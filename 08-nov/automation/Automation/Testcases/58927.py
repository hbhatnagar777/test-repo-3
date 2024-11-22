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
    __init__()                          -- initialize TestCase class
    setup()                             -- setup method for test case
    tear_down()                         -- tear down method for test case
    run()                               -- run function of this test case
    navigate_to_source_subclient()      -- Navigates to source subclient details page
    create_source_ifx_helper_obj()      -- Creates informix helper object for source instance
    create_destination_ifx_helper_obj() -- Creates informix helper object for destination instance
    add_data_get_metadata()             -- Add data for incremental backup & collect backup metadata
    wait_for_job_completion()           -- Wait for completion of job and check job status
    run_backup()                        -- Submit backup and validate backup job type
    restore_and_validate()              -- Submit restore and validate data restored

Input Example:
    "testCases":
        {
            "58927":
                    {
                        "ClientName":"meeratrad",
                        "InstanceName":"ol_informix1210",
                        "SourceInformixServiceName": "13601",
                        "SourceInformixDBPassword": "####",
                        "TestDataSize": [1,1,1],
                        "DestinationClientName": "meerasnap",
                        "DestinationInstanceName": "ol_informix1210",
                        "DestinationInformixServiceName": "7653",
                        "DestinationInformixDBPassword": "####"
                    }
        }
Provide port to which informix server listens using ipv4 address in InformixServiceName
TestDataSize should be list in order: [database_count, tables_count, row_count]
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.subclient import InformixSubclient
from Web.AdminConsole.Components.dialog import RBackup
from Database.InformixUtils.informixhelper import InformixHelper

class TestCase(CVTestCase):
    """Class for executing cross machine restore for Informix iDA using command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Cross machine restore test for Informix iDA from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'ClientName': None,
            'InstanceName': None,
            'SourceInformixServiceName': None,
            'SourceInformixDBPassword': None,
            'TestDataSize': [],
            'DestinationClientName': None,
            'DestinationInstanceName': None,
            'DestinationInformixServiceName': None,
            'DestinationInformixDBPassword': None
            }
        self.db_instance = None
        self.db_instance_details = None
        self.subclient_page = None
        self.source_informix_helper_obj = None
        self.destination_informix_helper_obj = None

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

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created databases")
        if self.source_informix_helper_obj:
            self.source_informix_helper_obj.delete_test_data()
        if self.destination_informix_helper_obj:
            self.destination_informix_helper_obj.delete_test_data()

    @test_step
    def navigate_to_source_subclient(self):
        """Opens details page for default subclient of source instance"""
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        db_instance = DBInstances(self.admin_console)
        db_instance.select_instance(DBInstances.Types.INFORMIX,
                                    self.tcinputs['InstanceName'],
                                    self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity('default')

    @test_step
    def create_source_ifx_helper_obj(self, refresh=False):
        """Creates object of informix helper class for source instance
        and does test data generation
        Args:
            refresh (bool) -- Creates informix helper object and
                              skips test data generation if True
                              Default is false
        """
        source_agent = self.client.agents.get('informix')
        source_instance = source_agent.instances.get(self.tcinputs['InstanceName'])
        self.source_informix_helper_obj = InformixHelper(
            self.commcell,
            source_instance,
            'default',
            self.client.client_hostname,
            self.tcinputs['InstanceName'],
            source_instance.informix_user,
            self.tcinputs['SourceInformixDBPassword'],
            self.tcinputs['SourceInformixServiceName']
        )
        if not refresh:
            self.log.info("Populate the informix server with "
                          "test data size=%s", self.tcinputs['TestDataSize'])
            self.source_informix_helper_obj.populate_data(scale=self.tcinputs['TestDataSize'])

    @test_step
    def create_destination_ifx_helper_obj(self, refresh=False):
        """Creates object of informix helper class for destination instance
        and creates the automation test dbspace cvauto1
        Args:
            refresh (bool) -- Creates helper object and skips dbspace creation if True
                              Default is false
        """
        destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientName"])
        destination_agent = destination_client.agents.get('informix')
        destination_instance = destination_agent.instances.get(
            self.tcinputs["DestinationInstanceName"])
        self.destination_informix_helper_obj = InformixHelper(
            self.commcell,
            destination_instance,
            'default',
            destination_client.client_hostname,
            self.tcinputs["DestinationInstanceName"],
            destination_instance.informix_user,
            self.tcinputs['DestinationInformixDBPassword'],
            self.tcinputs['DestinationInformixServiceName']
        )
        if not refresh:
            self.destination_informix_helper_obj.delete_test_data()
            self.destination_informix_helper_obj.create_dbspace()

    @test_step
    def add_data_get_metadata(self):
        """Adds more rows to tab1 and collect metadata"""
        self.source_informix_helper_obj.insert_rows(
            "tab1",
            database="auto1",
            scale=2)
        self.log.info("Collect metadata from server")
        metadata_backup = self.source_informix_helper_obj.collect_meta_data()
        return metadata_backup

    @test_step
    def wait_for_job_completion(self, jobid):
        """Wait for completion of job and check job status"""
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def run_backup(self, backup_type=RBackup.BackupType.INCR):
        """Submit backup and validate RBackup job type
        Args:
            backup_type (str) -- Backup operation can be Full or Incremental
                                 default is Incremental
                Accepted values: RBackup.BackupType.INCR for incremental,
                                 RBackup.BackupType.FULL
        """
        job_id = self.subclient_page.backup(backup_type)
        self.wait_for_job_completion(job_id)
        job_type = 'Incremental'
        if backup_type == RBackup.BackupType.FULL:
            job_type = 'Full'
        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(job_id, job_type)

    @test_step
    def restore_and_validate(self, metadata_backup, restore_type):
        """ Submit restore and validate data restored
        Args:
            metadata_backup (str)--  metadata collected during backup
            restore_type   (str) -- 'Entireinstance' for Entire Instance restore and
                                    'Wholesystem' for Whole System restore
        """
        self.create_destination_ifx_helper_obj()
        self.log.info("Stop informix server to perform %s restore", restore_type)
        self.destination_informix_helper_obj.stop_informix_server()
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(
            DBInstances.Types.INFORMIX,
            self.tcinputs["InstanceName"],
            self.tcinputs["ClientName"])
        self.db_instance_details.access_restore()
        self.log.info("Perform physical restore including restore of config files")
        restore_panel = self.subclient_page.restore_folders(DBInstances.Types.INFORMIX,
                                                            all_files=True)
        job_id = restore_panel.informix_restore(
            restore_type,
            destination_client=self.tcinputs["DestinationClientName"],
            destination_instance=self.tcinputs["DestinationInstanceName"],
            logical=False, config_files=True)
        self.wait_for_job_completion(job_id)
        self.log.info("Perform logical only restore")
        restore_panel = self.subclient_page.restore_folders(DBInstances.Types.INFORMIX,
                                                            all_files=True)
        job_id = restore_panel.informix_restore(
            restore_type,
            destination_client=self.tcinputs["DestinationClientName"],
            destination_instance=self.tcinputs["DestinationInstanceName"],
            physical=False)
        self.wait_for_job_completion(job_id)
        self.log.info("Making server online and validating data")
        self.destination_informix_helper_obj.bring_server_online()
        self.log.info("Metadata collected during backup=%s", metadata_backup)
        self.create_destination_ifx_helper_obj(refresh=True)
        metadata_restore = self.destination_informix_helper_obj.collect_meta_data()
        self.log.info("Metadata collected after restore=%s", metadata_restore)
        if metadata_backup == metadata_restore:
            self.log.info("Restored data is validated")
        else:
            raise Exception("Data validation failed")

    def run(self):
        """ Main function for test case execution """
        try:
            self.create_source_ifx_helper_obj()
            self.navigate_to_source_subclient()
            self.subclient_page.edit_content('EntireInstance')
            self.run_backup(backup_type=RBackup.BackupType.FULL)
            metadata_backup = self.add_data_get_metadata()
            self.run_backup()
            self.restore_and_validate(metadata_backup, restore_type='EntireInstance')
            self.navigate_to_source_subclient()
            self.subclient_page.edit_content('WholeSystem')
            self.run_backup(backup_type=RBackup.BackupType.FULL)
            metadata_backup = self.add_data_get_metadata()
            self.run_backup()
            self.restore_and_validate(metadata_backup, restore_type='WholeSystem')

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
