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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    Input Example:
        "testCases":{
            "59435":
            {
            "masterHostname": "<Master hostname>",
            "port": "<port number of mongos/mongod>",
            "clientName": "<master node client name>",
            "pseudo_client_name": "<pseudo client name>",
            "dbUser": "<MongoDB user>"  (optional, use if mongodb user is configured),
            "dbPassword": "<MongoDB password>"  (optional, use if mongodb password is configured),
            "replSet": "<replica set name>"  (optional, use if running the tc for replica set),
            "osName": "<OS username>"   (optional, used for pseudo client creation),
            "binPath": "<MongoDB binary path>" (optional),
            "plan": "<plan name>"   (optional, required for client creation),
            "engine_name": "<Snap engine>"  (optional, default:Native),
            "validate_discovery": "<true/false>" (optional, cross checks with csdb),
            }
        }
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
        self.name = "MongoDB IDA Command Center - ACCT1 In Place Granular Restore Without Overwrite"
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
        self.tcinputs = {
            'masterHostname': None,
            'port': None,
            'clientName': None,
            'pseudo_client_name': None
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_big_data()
        self.instances = Instances(self.admin_console)
        self.overview = Overview(self.admin_console)
        self.restore_obj = Restores(self.admin_console)
        database_helper.set_csdb(CommServDatabase(self.commcell))
        self.port = int(self.tcinputs.get('port'))
        self.masterhostname = self.tcinputs['masterHostname']
        self.mongo = MongoDBHelper(self.commcell, self.masterhostname,
                                   self.port, self.tcinputs.get('dbUser') or '',
                                   self.tcinputs.get('dbPassword') or '',
                                   replset=self.tcinputs.get('replSet'),
                                   bin_path=self.tcinputs.get('binPath'))
        self.mongo.delete_test_data()

    def _wait_for_job_completion(self, job_id, restore=False):
        """wait till job gets completed/fails"""
        job_obj = self.commcell.job_controller.get(job_id)
        self.log.info("Wait for [%s] job to complete", str(job_obj.job_type))
        if restore:
            self.log.info("Verification for negative case : Overwrite disabled")
            self.log.info("Job should be failed")
        if job_obj.wait_for_completion():
            if restore:
                self.log.info("[%s] job completed with job id:[%s]", job_obj.job_type, job_id)
                err_str = "%s job:%s shouldn't be completed" % (job_obj.job_type, job_id)
                raise CVTestStepFailure(err_str)
            else:
                self.log.info("[%s] job completed with job id:[%s]", job_obj.job_type, job_id)
        else:
            if restore:
                self.log.info("Success: [%s] job failed with job id:[%s]", job_obj.job_type, job_id)
            else:
                self.log.info("[%s] job failed with job id:[%s]", job_obj.job_type, job_id)
                err_str = "%s job failed with job id:%s" % (job_obj.job_type, job_id)
                raise CVTestStepFailure(err_str)

    def _backup(self):
        """starts full backup"""
        cutils = CommonUtils(self.commcell)
        self.admin_console.click_button("OK")
        self.log.info("Start snap backup")
        snap_job_id = self.admin_console.get_jobid_from_popup()
        self._wait_for_job_completion(snap_job_id)
        self.log.info("Done with Snap backup")
        time.sleep(5)
        self.log.info("Running inline backup copy")
        backupcopy_job_id = cutils.get_backup_copy_job_id(snap_job_id)
        self._wait_for_job_completion(backupcopy_job_id)
        self.log.info("Done with Backup copy")

    def _restore(self):
        """starts a restore"""
        self.log.info("start restore in place")
        self.restore_obj.restore_in_place(overwrite=False)
        restore_job_id = self.admin_console.get_jobid_from_popup()
        self._wait_for_job_completion(restore_job_id, restore=True)
        self.log.info("Done with restore in place")

    @test_step
    def access_or_create_client(self):
        """Access client if exists else creates new one"""
        if self.instances.is_instance_exists(self.tcinputs['pseudo_client_name']):
            self.log.info(f"Using the existing pseudo client: "
                          f"{self.tcinputs['pseudo_client_name']} to run the testcase")
            self.instances.access_instance(self.tcinputs['pseudo_client_name'])
        else:
            self.log.info("creating pseudo client")
            if not self.tcinputs.get('plan'):
                raise CVTestCaseInitFailure("Plan is required for creating new instance")
            self.instances.create_mongodb_instance(master_node=self.tcinputs['clientName'],
                                                   name=self.tcinputs['pseudo_client_name'],
                                                   os_name=self.tcinputs.get('osName'),
                                                   db_user=self.tcinputs.get('dbUser'),
                                                   db_pwd=self.tcinputs.get('dbPassword'),
                                                   plan=self.tcinputs['plan'],
                                                   bin_path=self.tcinputs.get('binPath'),
                                                   port_number=self.port)
            self.log.info("successfully created pseudo client")

    @test_step
    def discover_and_backup(self):
        """Discover nodes, generates data and run backup"""
        conf = self.overview.access_configuration()
        time.sleep(5)
        conf.discover_nodes()
        time.sleep(10)
        self.log.info("Discovered nodes successfully")
        if self.tcinputs.get('validate_discovery'):
            nodetable = Table(self.admin_console)
            clientlist = nodetable.get_column_data('Name')
            portlist = nodetable.get_column_data('Port number')
            servertypelist = nodetable.get_column_data('Server type')
            self.log.info("Discovery validation from csdb")
            mongodb_server_name = self.tcinputs['pseudo_client_name']
            if self.mongo.validate_discovery_of_nodes(
                    mongodb_server_name, portlist, clientlist, servertypelist):
                self.log.info("Discovery validation is successful")
            else:
                self.log.info("Discovery validation failed")
                raise CVTestStepFailure("Discovery validation failed")
        if self.tcinputs.get("engine_name"):
            self.log.info("Editing engine")
            conf.edit_snapshot_engine(self.tcinputs["engine_name"])
            self.log.info("Successfully edited")
        self.generated_data = self.mongo.generate_test_data()
        self.log.info("Generated data...")
        conf.access_backup()
        self._backup()

    @test_step
    def restore_and_validate(self, onlycolls=False):
        """Restores databases/collections and validates(negative case)"""
        conf = self.overview.access_configuration()
        conf.access_restore()
        browse = Browse(self.admin_console)
        browse.switch_to_collections_view()
        if onlycolls:
            database = next(iter(self.generated_data))
            browse.access_folder(database)
            self.log.info("Restoring at collection level for db: %s", database)
        self.overview.restore_all()
        self._restore()

    def run(self):
        """
        Run function of this test case
        Create MongoDB instance if required
        access configuration and discover nodes
        In configuration page:
            Generate data, Discover nodes and start backup
        After backup,
            Navigate to restore(browse) page
        In restore page:
            Select restore at database/collection level
            start in place restore with overwrite option disabled
        After restore,
            validate that restore job is failing
        After validation,
            Delete generated data
        """
        try:
            self.access_or_create_client()
            self.discover_and_backup()
            self.restore_and_validate(onlycolls=False)
            self.admin_console.select_breadcrumb_link_using_text(
                self.tcinputs['pseudo_client_name'])
            self.restore_and_validate(onlycolls=True)
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.mongo.delete_test_data()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
