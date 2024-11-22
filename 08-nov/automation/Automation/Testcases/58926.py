
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                 -- initialize TestCase class
    setup()                    -- setup method for test case
    tear_down()                -- tear down method for test case
    run()                      -- run function of this test case
    navigate_to_subclient()    -- Navigates to details page for default subclient
    create_ifx_helper_object() -- Creates informix helper class object
    add_data_get_metadata()    -- Adds data for incremental backup & collect backup metadata
    wait_for_job_completion()  -- Wait for completion of job and check job status
    run_backup()               -- Submit backup and validate backup job type
    aux_copy()                 -- Run aux copy for backups and get copy precedence of the copy
    restore_and_validate()     -- Submit restore and validate data restored
    verify_copy_used()         -- From IFXXBSA.log confirm right copy was used for restore

Input Example:
    "testCases":
        {
            "58926":
                    {
					    "ClientName": "meeratrad_3",
					    "AgentName": "informix",
					    "InstanceName": "ol_informix1210",
					    "BackupsetName": "default",
					    "SubclientName": "default",
					    "InformixPassword": "#####",
					    "InformixServiceName": "13601",
					    "TestDataSize": [2, 10, 100]
                    }
        }
Provide port to which informix server listens using ipv4 address in InformixServiceName
TestDataSize should be list in order: [database_count, tables_count, row_count]
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import InformixSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper

class TestCase(CVTestCase):
    """Class for executing restore from aux copy for informix from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Informix restore from secondary copy using command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'InformixPassword': None,
            'InformixServiceName': None,
            'TestDataSize': []
            }
        self.subclient_page = None
        self.informix_helper_object = None
        self.bkp_jobid = 0
        self.db_instance = None
        self.db_instance_details = None
        self.page_container = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.db_instance = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.subclient_page = InformixSubclient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created databases")
        if self.informix_helper_object:
            self.informix_helper_object.delete_test_data()

    @test_step
    def navigate_to_subclient(self):
        """Opens details page for default subclient"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        db_instance = DBInstances(self.admin_console)
        db_instance.select_instance(DBInstances.Types.INFORMIX,
                                    self.tcinputs["InstanceName"],
                                    self.tcinputs["ClientName"])
        self.db_instance_details.click_on_entity('default')

    @test_step
    def create_ifx_helper_object(self, refresh=False):
        """Creates object of informix helper class
        Args:
            refresh (bool) -- Skips informix test data population and
                              creates informix helper object only if True
                              Default is false
        """
        self.informix_helper_object = InformixHelper(
            self.commcell,
            self.instance,
            self.subclient,
            self.client.client_hostname,
            self.instance.instance_name,
            self.instance.informix_user,
            self.tcinputs['InformixPassword'],
            self.tcinputs['InformixServiceName']
        )
        if not refresh:
            self.log.info("Populate the informix server with "
                          "test data size=%s", self.tcinputs['TestDataSize'])
            self.informix_helper_object.populate_data(scale=self.tcinputs['TestDataSize'])

    @test_step
    def add_data_get_metadata(self):
        """Adds more rows to tab1 and collect metadata"""
        self.informix_helper_object.insert_rows(
            "tab1",
            database="auto1",
            scale=2)
        self.log.info("Collect metadata from server")
        metadata_backup = self.informix_helper_object.collect_meta_data()
        return metadata_backup

    @test_step
    def wait_for_job_completion(self, jobid):
        """Wait for completion of job and check job status
        Args:
            jobid (int) -- job id for the submitted operation
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def run_backup(self, backup_type=RBackup.BackupType.INCR):
        """Submit backup and validate backup job type
        Args:
            backup_type (str) -- Backup operation can be Full or Incremental
                                 default is Incremental
            Accepted values    : RBackup.BackupType.INCR for incremental,
                                 RBackup.BackupType.FULL
        """
        self.bkp_jobid = self.subclient_page.backup(backup_type)
        self.wait_for_job_completion(self.bkp_jobid)
        job_type = 'Incremental'
        if backup_type == RBackup.BackupType.FULL:
            job_type = 'Full'
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(self.bkp_jobid, job_type)

    @test_step
    def aux_copy(self):
        """ Perform aux copy for data and log storage policies
        A copy named automation_copy is created for the SPs, if not present already
        Returns:
            data_cp (int) -- copy precedence of aux copy for data SP
            log_cp (int)  -- copy precedence of aux copy for log SP
        """
        dbhelper_object = dbhelper.DbHelper(self.commcell)
        data_cp = dbhelper_object.prepare_aux_copy_restore(self.subclient.storage_policy)
        if self.instance.log_storage_policy_name == self.subclient.storage_policy:
            log_cp = data_cp
        else:
            log_cp = dbhelper_object.prepare_aux_copy_restore(self.instance.log_storage_policy_name)
        return data_cp, log_cp

    @test_step
    def restore_and_validate(self, metadata_backup, data_cp, log_cp):
        """ Submit restore from aux copy, verify correct copy is used and validate data restored
        Args:
            metadata_backup (str)--  metadata collected during backup
            data_cp         (int)--  copy precedence of aux copy for data SP
            log_cp          (int)--  copy precedence of aux copy for log SP
        """
        self.log.info("Delete test generated data")
        self.informix_helper_object.delete_test_data()
        self.log.info("Stop informix server to perform entire instance restore from aux copy")
        self.informix_helper_object.stop_informix_server()
        self.page_container.click_breadcrumb(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        self.log.info("Perform physical restore including restore of config files")
        restore_panel = self.subclient_page.restore_folders(DBInstances.Types.INFORMIX,
                                                            all_files=True, copy="automation_copy")
        job_id = restore_panel.informix_restore('EntireInstance', logical=False,
                                                config_files=True)
        self.wait_for_job_completion(job_id)
        time.sleep(20)
        self.log.info("Verify copy used for data restore is with cp =%s", data_cp)
        self.verify_copy_used(job_id, data_cp, "1")
        self.log.info("Perform logical only restore")
        restore_panel = self.subclient_page.restore_folders(DBInstances.Types.INFORMIX,
                                                            all_files=True, copy='automation_copy')
        job_id = restore_panel.informix_restore('EntireInstance', physical=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Making server online and validating data")
        self.informix_helper_object.bring_server_online()
        self.log.info("Verify copy used for log restore is with cp =%s", log_cp)
        self.verify_copy_used(job_id, log_cp, "4")
        self.log.info("Metadata collected during backup=%s", metadata_backup)
        self.create_ifx_helper_object(refresh=True)
        metadata_restore = self.informix_helper_object.collect_meta_data()
        self.log.info("Metadata collected after restore=%s", metadata_restore)
        if metadata_backup == metadata_restore:
            self.log.info("Restored data is validated")
        else:
            raise Exception("Data validation failed")

    @test_step
    def verify_copy_used(self, restore_jobid, aux_copy_cp, file_type):
        """ Verify copy precedence in IFXXBSA.log is correct for any one afile restored
                Args:
                    restore_jobid (int)-- job id of restore operation
                    aux_copy_cp (int)  -- copy precedence of the copy selected to perform restore
                    file_type (int)    -- file_type of the data restored. 1 for data and 4 for log
                Raises:
                    Exception:
                        If copy precedence value in IFXXBSA.log is different from expected.
        """
        afile_id = self.informix_helper_object.get_afileid(self.bkp_jobid, file_type)
        self.log.info("The afileID is {0}".format(afile_id))
        machine_object = machine.Machine(self.client, self.commcell)
        output = machine_object.get_logs_for_job_from_file(
            job_id=restore_jobid, log_file_name="IFXXBSA.log", search_term=str(afile_id))
        if f"copy = {aux_copy_cp}" not in output:
            raise Exception("Restore did not use correct copy. Output is {0}".format(output))

    def run(self):
        """ Main function for test case execution """
        try:
            self.create_ifx_helper_object()
            self.navigate_to_subclient()
            self.subclient_page.edit_content('EntireInstance')
            self.run_backup(backup_type=RBackup.BackupType.FULL)
            metadata_backup = self.add_data_get_metadata()
            self.run_backup()
            data_cp, log_cp = self.aux_copy()
            self.restore_and_validate(metadata_backup, data_cp, log_cp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
