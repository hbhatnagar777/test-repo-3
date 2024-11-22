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
    cleanup()                  -- deletes the subclient created by automation
    run()                      -- run function of this test case
    create_ifx_helper_object() -- Creates informix helper class object
    add_data_get_metadata()    -- Adds data for incremental backup & collect backup metadata
    create_subclient()         -- Create a new subclient with selective as content
    wait_for_job_completion()  -- Wait for completion of job and check job status
    run_backup()               -- Submit backup and validate backup job type
    confirm_job_content()      -- Verify no dbspace except cvauto1 is part of job in IFXXBSA.log
    restore_and_validate()     -- Submit restore and validate data restored

Input Example:
    "testCases":
        {
            "58928":
                    {
					    "ClientName": "meeratrad_3",
					    "AgentName": "informix",
					    "InstanceName": "ol_informix1210",
					    "BackupsetName": "default",
					    "SubclientName": "default",
					    "InformixPassword": "####",
					    "InformixServiceName": "13601",
					    "Plan": "Plan_Name",
                        "incr_Level": "2",
					    "TestDataSize": [1,10,100]
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
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import InformixSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.page_container import PageContainer
from Database.InformixUtils.informixhelper import InformixHelper

class TestCase(CVTestCase):
    """Class for executing partial restore for informix from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Informix partial dbspace level restore from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'InformixPassword': None,
            'InformixServiceName': None,
            'Plan': None,
            'incr_Level': None,
            'TestDataSize': []
            }
        self.db_instance = None
        self.db_instance_details = None
        self.subclient_page = None
        self.page_container = None
        self.informix_helper_object = None
        self.machine_object = None

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
        self.machine_object = machine.Machine(self.client, self.commcell)

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created data")
        if self.informix_helper_object:
            self.informix_helper_object.delete_test_data()

    @test_step
    def cleanup(self):
        """Deletes subclient created by automation"""
        if self.backupset.subclients.has_subclient('Select_58928'):
            self.page_container.click_breadcrumb(self.tcinputs['InstanceName'])
            self.db_instance_details.click_on_entity('Select_58928')
            self.subclient_page.delete_subclient()

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
    def create_subclient(self):
        """Create a new subclient with selective as content"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.db_instance.select_instance(DBInstances.Types.INFORMIX,
                                    self.instance.instance_name,
                                    self.client.client_name)
        self.db_instance_details.click_on_entity('default')
        self.log.info("Run full backup for default subclient for content refresh")
        job_id = self.subclient_page.backup(RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.page_container.click_breadcrumb(self.tcinputs['InstanceName'])
        if self.backupset.subclients.has_subclient('Select_58928'):
            self.log.info("Deleting existing subclient Select_58928")
            self.db_instance_details.click_on_entity('Select_58928')
            self.subclient_page.delete_subclient()
        subclient_object = self.db_instance_details.click_add_subclient(DBInstances.Types.INFORMIX)
        subclient_object.add_subclient(
            "Select_58928",
            self.tcinputs['Plan'],
            "Selective",
            self.tcinputs['incr_Level']
        )
        self.log.info("Subclient Select_58928 created successfully")

    @test_step
    def wait_for_job_completion(self, job_id):
        """Wait for completion of job and check job status"""
        job_obj = self.commcell.job_controller.get(job_id)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                "Failed to run job:%s with error: %s" % (job_id, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", job_id)

    @test_step
    def run_backup(self, backup_type=RBackup.BackupType.INCR):
        """Submit backup and validate backup job type
        Args:
            backup_type (str) -- Backup operation can be Full or Incremental
                                 default is Incremental
                Accepted values: RBackup.BackupType.INCR for incremental,
                                 Backup.BackupType.FULL
        """
        job_id = self.subclient_page.backup(backup_type)
        self.wait_for_job_completion(job_id)
        job_type = 'Incremental'
        if backup_type == RBackup.BackupType.FULL:
            job_type = 'Full'
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(job_id, job_type)
        self.confirm_job_content(job_id)

    @test_step
    def confirm_job_content(self, job_id):
        """ Verify no dbspace except cvauto1 is part of backup or restore job in IFXXBSA.log
                Args:
                    job_id (int)-- job id of backup or restore operation
                Raises:
                    CVTestStepFailure exception:
                        If IFXXBSA.log for job_id has rootdbs related logging for backup or restore
        """
        output = None
        output = self.machine_object.get_logs_for_job_from_file(
            job_id=job_id, log_file_name="IFXXBSA.log", search_term='rootdbs')
        if output is not None and "rootdbs" in output:
            raise CVTestStepFailure("Rootdbs dbspace was part of the job. Output is {0}".format(output))

    @test_step
    def restore_and_validate(self, metadata_backup):
        """ Submit partial restore and validate data restored
        Args:
            metadata_backup (str)--  metadata collected during backup
        """
        self.log.info("Prepare cvauto1 dbspace to perform partial restore")
        self.informix_helper_object.mark_disabled_dbspace_down()
        self.create_ifx_helper_object(refresh=True)
        self.page_container.click_breadcrumb(self.tcinputs['InstanceName'])
        self.db_instance_details.access_restore()
        browse = RBrowse(self.admin_console)
        browse.clear_all_selection()
        self.log.info("Perform physical restore of dbspace cvauto1")
        restore_panel = self.subclient_page.restore_folders(DBInstances.Types.INFORMIX,
                                                            items_to_restore=["cvauto1"])
        job_id = restore_panel.informix_restore(logical=False)
        self.wait_for_job_completion(job_id)
        self.confirm_job_content(job_id)
        time.sleep(20)
        self.log.info("Perform logical only restore of dbspace cvauto1")
        browse.clear_all_selection()
        restore_panel = self.subclient_page.restore_folders(DBInstances.Types.INFORMIX,
                                                            items_to_restore=["cvauto1"])
        job_id = restore_panel.informix_restore(physical=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Validating data.Metadata collected during backup=%s", metadata_backup)
        self.create_ifx_helper_object(refresh=True)
        metadata_restore = self.informix_helper_object.collect_meta_data()
        self.log.info("Metadata collected after restore=%s", metadata_restore)
        if metadata_backup == metadata_restore:
            self.log.info("Restored data is validated")
        else:
            raise CVTestStepFailure("Data validation failed")
        self.cleanup()

    def run(self):
        """ Main function for test case execution """
        try:
            self.create_ifx_helper_object()
            self.create_subclient()
            self.run_backup(backup_type=RBackup.BackupType.FULL)
            metadata_backup = self.add_data_get_metadata()
            self.run_backup()
            self.restore_and_validate(metadata_backup)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
