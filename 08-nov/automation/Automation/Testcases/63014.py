# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                            --  initialize TestCase class

    setup()                                               --  setup function of this test case

    _backup()                                             --  backup of the instance with single node replica set

    _restore()                                            --  Restore of a single node replica set cluster

    discover_and_backup                                   --  Discover the cluster and backup

    autoshutdown_servers_and_restore                      --  Prepare server for restore and run restore

    validation_post_restore                               --  Validation post restore operation

    shutdown_and_restart_servers                          --  Shutdown and start original server

    delete_monogodb_instance                              --  Delete MongoDB instance

    run()                                                 --  run function of this test case

    tear_down()                                           --  tear down function of this test case

"""
import time

from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.Bigdata.Restores import Restores
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.adminconsole import AdminConsole

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
        self.name = "Command Center: Verify in place restore for MongoDB single node replica set cluster"
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
        self.dbprefix = "as" + str(int(time.time()))
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
            self.navigator.navigate_to_big_data()
            self.port = int(self.tcinputs['port'])
            self.masterhostname = self.tcinputs['masterHostname']
            self.mongo = MongoDBHelper(self.commcell, self.masterhostname,
                                       self.port, self.tcinputs['dbUser'],
                                       self.tcinputs['dbPassword'],
                                       replset=self.tcinputs['replSet'] or None,
                                       bin_path=self.tcinputs['binPath'])
            if self.mongo.check_if_sharded_cluster() == 0:
                raise CVTestStepFailure("This cluster is a sharded cluster and not a single node replica set")
            if not self.mongo.check_if_replica_set():
                raise CVTestStepFailure("This cluster is not a replica set")
            if not self.mongo.check_single_node_replica_set():
                raise CVTestStepFailure("This cluster is not a single node replica set")
            self.instances = Instances(self.admin_console)
            # deletion if instance exists
            if self.instances.is_instance_exists(self.tcinputs['pseudo_client_name']):
                self.delete_monogodb_instance()
            self.overview = Overview(self.admin_console)
            self.restore_obj = Restores(self.admin_console)
            database_helper.set_csdb(CommServDatabase(self.commcell))

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()

    def _backup(self):
        """starts full backup"""
        cutils = CommonUtils(self.commcell)
        time.sleep(5)
        self.admin_console.click_button("OK")
        snap_job_id = self.admin_console.get_jobid_from_popup()
        snap_job = self.commcell.job_controller.get(snap_job_id)
        self.log.info("Wait for [%s] job to complete", str(snap_job))
        if snap_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Snap job completed with job id:[%s]", snap_job_id)
        else:
            err_str = "[%s] job id for snap backup job failed" % snap_job_id
            raise CVTestStepFailure(err_str)
        time.sleep(5)
        self.log.info("Running inline backup copy")
        backupcopy_job_id = cutils.get_backup_copy_job_id(snap_job_id)
        backupcopy_job = self.commcell.job_controller.get(backupcopy_job_id)
        self.log.info("Wait for [%s] job to complete", str(backupcopy_job))
        if backupcopy_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("Backup copy job completed with job id:[%s]", backupcopy_job_id)
        else:
            err_str = "[%s] job id for backup copy job failed" % backupcopy_job_id
            raise CVTestStepFailure(err_str)

    def _restore(self):
        """starts a restore"""
        self.log.info("start restore in place")
        self.overview.restore_all()
        time.sleep(10)
        self.restore_obj.restore_in_place(shutdown=True)
        restore_job_id = self.admin_console.get_jobid_from_popup()
        restore_job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Wait for [%s] job to complete", str(restore_job))
        if restore_job.wait_for_completion(300):  # wait for max 5 minutes
            self.log.info("restore job completed with job id:[%s]", restore_job)
        else:
            err_str = "[%s] job id for restore job failed" % restore_job
            raise CVTestStepFailure(err_str)
        self.log.info("Done with restore in place")

    @test_step
    def discover_and_backup(self):
        """Discover nodes, generates data and run backup"""
        conf = self.overview.access_configuration()
        time.sleep(5)
        conf.discover_nodes()
        self.admin_console.driver.refresh()
        time.sleep(30)
        self.log.info("Discovered nodes successfully")
        mongodb_server_name = self.tcinputs['pseudo_client_name']
        #if not self.mongo.check_if_single_node_replicaset_from_DB(mongodb_server_name):
        #    raise CVTestStepFailure("Server Type corresponding to this instance is not set to 4")
        nodetable = Table(self.admin_console)
        clientlist = nodetable.get_column_data('Name')
        portlist = nodetable.get_column_data('Port number')
        servertypelist = nodetable.get_column_data('Server type')
        self.log.info("Discovery validation from csdb")
        if self.mongo.validate_discovery_of_nodes(mongodb_server_name,
                                                  portlist, clientlist, servertypelist):
            self.log.info("Discovery validation is successful")
        else:
            self.log.info("Discovery validation failed")
        self.admin_console.driver.refresh()
        time.sleep(35)
        conf.edit_snapshot_engine(self.tcinputs["engine_name"])
        self.replicaset_or_shard = \
            self.mongo.check_shardedcluster_or_replicaset(mongodb_server_name)
        self.replica_set_list = conf.get_replica_set_list()
        self.generated_data = self.mongo.generate_test_data(database_prefix=self.dbprefix,
                                                            num_dbs=5, num_col=2, num_docs=5)
        self.log.info("Generated data...")
        conf.access_backup()
        self._backup()

    @test_step
    def autoshutdown_servers_and_restore(self):
        """get start commands and start restore with auto shutdown option enabled"""
        conf = self.overview.access_configuration()
        self.backup_db_size = self.mongo.get_db_server_size()
        self.mongod_list = self.mongo.get_mongod_start_command_from_csdb()
        conf.access_overview()
        self.overview.access_instance_restore()
        browse = Browse(self.admin_console)
        self.log.info("Dropping the test data generated with database prefix " + self.dbprefix)
        self.mongo.delete_test_data(prefix=self.dbprefix)
        # Nodes the data is being restored to
        time.sleep(20)
        self._restore()

    @test_step
    def validation_post_restore(self):
        """Restore database validation based on size and count"""

        new_mongo = MongoDBHelper(self.commcell, self.masterhostname, self.port, '',
                                  '', replset=self.tcinputs['replSet']
                                  , bin_path=self.tcinputs['binPath'])
        if not new_mongo.check_single_node_replica_set():
            raise CVTestStepFailure("This cluster is not a single node replica set")
        restore_db_size = new_mongo.get_db_server_size()
        if self.backup_db_size == restore_db_size:
            self.log.info("Validation of db server size is successful")
        else:
            self.log.info("Restore db size is not equal to backed up db server size")
        if self.mongo.validate_restore(self.generated_data, self.masterhostname, self.port):
            self.log.info("Validation of restored data is successful")
        else:
            self.log.info("Validation failed")

    @test_step
    def shutdown_and_restart_servers(self):
        """shutting down restored servers and starting original servers"""
        self.log.info("Shutting down the restored nodes")
        self.mongo.shutdown_server_using_kill_command()
        self.log.info("Restored nodes are offline")
        time.sleep(60)
        self.log.info("Starting replica set nodes")
        self.mongo.start_mongod_services(self.mongod_list)


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
            check weather we are dealing with sharded cluster or replicaset
            get replica set list and mongos list
            Generate data and start backup
        After backup,
            Get mongo start commands for replica set and sharded cluster
        Navigate to restore(browse) page
        In restore page:
            start in place restore with autoshutdown option
        After restore,
            For sharded cluster, disable authentication and start mongos to validate restored data
            For replica set, validate restored data
        After validation,
            shutdown the restored nodes
            start replicaset nodes and initiate replica set
            For sharded cluster, shutdown mongos and start mongos(with authentication)
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
            self.autoshutdown_servers_and_restore()
            self.validation_post_restore()
            self.shutdown_and_restart_servers()
            self.delete_monogodb_instance()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
