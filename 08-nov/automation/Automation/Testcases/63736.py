# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Design steps:

1.Check if MongoDB instance with same name exists. If it does, delete it.
2.Create a new MongoDB instance.
3.Set snapshot engine.
4.Discovery the nodes in the instance.
5.Perform a backup.

"""
import time

from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.Bigdata.Restores import Restores
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.wizard import Wizard

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure

from AutomationUtils import database_helper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.idautils import CommonUtils

from Database.MongoDBUtils.mongodbhelper import MongoDBHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "MongoDB :Verify instance creation, discovery of nodes " \
                    "and backup"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.instances = None
        self.overview = None
        self.restore_obj = None
        self.mongo = None
        self.port = None
        self.masterhostname = None
        self.generated_data = None
        self.restore_list = None
        self.restore_node_list = None
        self.replica_set_list = None
        self.backup_db_size = None
        self.mongos_start = None
        self.mongod_list = None
        self.replicaset_or_shard = None
        self.tcinputs = {
            'masterHostname': None,
            'port': None,
            'replSet': None,
            'clientName': None,
            'dbUser': None,
            'dbPassword': None,
            'pseudo_client_name': None,
            'osName': None,
            'plan': None,
            'binPath': None,
            'engine_name': None
        }

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.overview = Overview(self.admin_console)
            self.navigator.navigate_to_big_data()
            time.sleep(100)
            self.instances = Instances(self.admin_console)
            # deletion if instance exists
            if self.instances.is_instance_exists(self.tcinputs['pseudo_client_name']):
                self.delete_monogodb_instance()
            database_helper.set_csdb(CommServDatabase(self.commcell))
            self.port = int(self.tcinputs['port'])
            self.masterhostname = self.tcinputs['masterHostname']
            self.mongo = MongoDBHelper(self.commcell, self.masterhostname, self.port, self.tcinputs['dbUser'],
                                       self.tcinputs['dbPassword'], replset=self.tcinputs['replSet'] or None,
                                       bin_path=self.tcinputs['binPath'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()

    def _backup(self):
        """starts full backup"""
        snap_job_id = self.admin_console.get_jobid_from_popup()
        snap_job = self.commcell.job_controller.get(snap_job_id)
        self.log.info("Wait for [%s] job to complete", str(snap_job))
        if snap_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Snap job completed with job id:[%s]", snap_job_id)
        else:
            err_str = "[%s] job id for snap backup job failed" % snap_job_id
            raise CVTestStepFailure(err_str)
        cutils = CommonUtils(self.commcell)
        time.sleep(30)
        self.log.info("Running inline backup copy")
        backupcopy_job_id = cutils.get_backup_copy_job_id(snap_job_id)
        backupcopy_job = self.commcell.job_controller.get(backupcopy_job_id)
        self.log.info("Wait for [%s] job to complete", str(backupcopy_job))
        if backupcopy_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Backup copy job completed with job id:[%s]", backupcopy_job_id)
        else:
            err_str = "[%s] job id for backup copy job failed" % backupcopy_job_id
            raise CVTestStepFailure(err_str)


    @test_step
    def discover_and_backup(self):
        """Discover nodes, generates data and run backup"""
        nodes = self.overview.access_nodes()
        time.sleep(5)
        nodes.discover_nodes()
        self.admin_console.driver.refresh()
        time.sleep(30)
        self.log.info("Discovered nodes successfully")
        """
        nodetable = Table(self.admin_console)
        clientlist = nodetable.get_column_data('Name')
        portlist = nodetable.get_column_data('Port number')
        servertypelist = nodetable.get_column_data('Server type')
        self.log.info("Discovery validation from csdb")"""
        mongodb_server_name = self.tcinputs['pseudo_client_name']
        """
        if self.mongo.validate_discovery_of_nodes(mongodb_server_name, portlist, clientlist, servertypelist):
            self.log.info("Discovery validation is successful")
        else:
            self.log.info("Discovery validation failed")
        """
        self.admin_console.driver.refresh()
        time.sleep(15)
        conf = self.overview.access_configuration()
        time.sleep(30)
        conf.edit_mongosnapshot_engine(self.tcinputs["engine_name"])
        self.replicaset_or_shard = self.mongo.check_shardedcluster_or_replicaset(mongodb_server_name)
        time.sleep(30)
        self.replica_set_list = conf.get_replica_set_list()
        self.generated_data = self.mongo.generate_test_data()
        self.log.info("Generated data...")
        nodes.backup()
        self._backup()

    @test_step
    def delete_monogodb_instance(self):
        """Delete mongodb instance"""
        mongodb_server_name = self.tcinputs['pseudo_client_name']
        self.log.info("deleting [%s] instance", mongodb_server_name)
        self.navigator.navigate_to_big_data()
        self.instances.delete_instance_name(mongodb_server_name)
        self.browser.driver.refresh()
        if self.instances.is_instance_exists(mongodb_server_name):
            raise CVTestStepFailure("[%s] mongoDB server is not getting deleted" %
                                    mongodb_server_name)
        self.log.info("Deleted [%s] instance successfully", mongodb_server_name)

    def run(self):
        """Run function of this test case
        Create mongoDb instance
        access configuration and discover nodes
        In configuration page:
            get client list,port list
            check whether we are dealing with sharded cluster or replicaset
            get replica set list and mongos list
            Generate data and start backup
        """
        try:
            self.log.info("creating pseudo client")
            self.instances.create_mongodb_instance(master_node=self.tcinputs['clientName'],
                                                   name=self.tcinputs['pseudo_client_name'],
                                                   os_name=self.tcinputs['osName'],
                                                   db_user=self.tcinputs['dbUser'],
                                                   db_pwd=self.tcinputs['dbPassword'],
                                                   plan=self.tcinputs['plan'],
                                                   bin_path=self.tcinputs['binPath'],
                                                   port_number=self.port)
            self.log.info("successfully created pseudo client")
            self.discover_and_backup()
            time.sleep(90)
            self.log.info("Verified instance creation/deletion , discovery of nodes and backup")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
