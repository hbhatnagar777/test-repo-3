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
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase, delete automation created test data

    create_helper_object()      -- Create HANA helper object

    get_job_details()           --  Method to get job details

    run_backup()                --  method to run backup for HANA DB

    run_restore()               --  method to run restore for HANA DB

    backup_operations()         --  backup operations for DB and metadata creation

    restore_operations()        --  Restore operations for DB and validate test data after restore

    navigate_to_backupset()     --  navigates to specified backupset page of the instance

    add_instance()              --  Adding new HANA instance

    run()                       --  Main function for test case execution

Input Example:

    "testCases":
            {
                "53787": {
                    "Client":"abc",
                    "AgentName":"SAPHANA",
                    "InstanceName":"abc",
                    "PlanName":"backupPlan",
                    "DBUser":"sys",
                    "DBPassword":"***"
                }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.backupset import Backupset
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.Instances.restore_panels import SAPHANARestorePanel
from Database.dbhelper import DbHelper
from Database.SAPHANAUtils.hana_helper import HANAHelper
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails


class TestCase(CVTestCase):
    """ Class for executing SAP HANA Scale Out SNAP ACCT 1 test case for HANA 2 multi-tenant """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAP HANA Scale Out SNAP ACCT 1 test case for HANA 2 multi-tenant"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance_details = None
        self.database_instances = None
        self.backupset_page = None
        self.restore_panel = None
        self.subclient_page = None
        self.hana_helper = None
        self.page_container = None
        self.rtable = None
        self.job_details = None
        self.tcinputs = {
            "Client": None,
            "AgentName": None,
            "InstanceName": None,
            "PlanName": None,
            "DBUser": None,
            "DBPassword": None
        }
        self.snap_engine = self.tcinputs.get("SnapEngine") or "NetApp"
        self.snapshot_enabled = None
        self.dbhelper_object = None
        self.backup_prefix = None
        self.internal_backup_id = None
        self.point_in_time = None
        self.last_job_id = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*** Initialize browser objects ***")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.restore_panel = SAPHANARestorePanel(self.admin_console)
        self.backupset_page = DBInstanceDetails(self.admin_console)
        self.dbhelper_object = DbHelper(self.commcell)
        self.subclient_page = SubClient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.job_details = JobDetails(self.admin_console)
        self.log.info("#### SAP HANA Instance Operations ####")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("#### Checking if instance exists ####")
        if self.database_instances.is_instance_exists(DBInstances.Types.SAP_HANA,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["Client"]):
            self.log.info("#### Instance Found  ####")
        else:
            self.log.info("#### Instance not found. Creating new instance ####")
            self.add_instance()
            self.log.info("#### Instance successfully created ####")

        self.create_helper_object()
        self.log.info("#### Hana Helper Object created ####")

    def tear_down(self):
        """ tear down method for testcase """
        self.log.info("Deleting Automation Created test data")
        self.log.info("#### cleanUp test data ####")
        self.hana_helper.cleanup_test_data(tenant_connection=True)
        self.log.info("#### cleanup done ####")

    @test_step
    def create_helper_object(self):
        """  Creates HANA helper object for doing all related operations to HANA database
        """
        self.hana_helper = HANAHelper(commcell=self.commcell, client_name=self.tcinputs['Client'],
                                      instance_name=self.tcinputs['InstanceName'],
                                      backupset_name=self.tcinputs['InstanceName'], subclient_name='default')

    def get_job_details(self):
        """ Method to get job details """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.SAP_HANA,
            self.tcinputs['InstanceName'], self.tcinputs['Client'])
        self.page_container.select_tab("Jobs")
        self.rtable.access_link(self.last_job_id)
        association_details = self.job_details.get_association_details()
        self.backup_prefix = association_details[self.admin_console.props['label.backupPrefix']]
        self.internal_backup_id = association_details[self.admin_console.props['label.internalBackupId']]
        self.point_in_time = self.job_details.get_progress_details()["End time"]

    @test_step
    def run_backup(self, backup_type, backupset_name=None):
        """ method to run backup for HANA DB
            Args:
                backup_type (backup_type) : FULL/INCR/DIFF

                backupset_name (str) : backupset name
                    default : "SYSTEMDB"
        """
        self.log.info(
            "#### Running SapHana %s Backup for %s DB ####", format(backup_type.name), backupset_name)
        job_id = self.subclient_page.backup(backup_type)
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.last_job_id = job_id
        self.log.info(
            "#### SapHana %s backup is completed for %s DB ####", format(backup_type.name), backupset_name)

    @test_step
    def run_restore(self, advanced_options=None, point_in_time=None, backup_prefix=None, internal_backup_id=None):
        """ method to run restore for HANA DB
            Args:
                advanced_options (dict) : advanced options for restore
                    default : None
                point_in_time (str) : Point in time for restore
                    default : None
                backup_prefix (str) : Backup prefix for restore
                    default : None
                internal_backup_id (int) : Internal backup id for restore
                    default : None
        """
        self.backupset_page.access_restore()
        self.log.info("#### Running SapHana Snap In place Restore ####")
        job_id = self.restore_panel.in_place_restore(
            point_in_time=point_in_time,
            backup_prefix=backup_prefix,
            internal_backup_id=internal_backup_id,
            advanced_options=advanced_options
        )
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("#### SapHana Snap In place restore is completed ####")

    @test_step
    def backup_operations(self):
        """
            backup operations for DB and metadata creation
            returns:
                dictionary (dict) : collected metadata after backup
        """
        self.navigate_to_backupset(backupset_name=self.tcinputs['InstanceName'])
        backupset_page = Backupset(self.admin_console)
        backupset_page.access_subclient('default')

        self.log.info("#### Creating test data before FULL Backup ####")
        self.hana_helper.create_test_tables(tenant_connection=True)
        self.log.info("#### Tables are created successfully ####")
        self.run_backup(RBackup.BackupType.FULL, backupset_name=self.tcinputs['InstanceName'])
        self.log.info("#### Running Backup Copy ####")
        self.dbhelper_object.run_backup_copy(self.tcinputs["PlanName"])
        self.get_job_details()

        self.log.info("#### Collect the metadata for %s ####", self.tcinputs['InstanceName'])
        return self.hana_helper.get_meta_data(_tenant_connection=True)

    @test_step
    def restore_operations(self, backup_map, type=None, backup_copy=None, revert=False):
        """
        Restore operations for DB and validate test data after restore

            Args:
                backup_map (dict) : metadata collected after backup
                type (str) : Type of restore operation
                    default : None
                backup_copy (bool) : True if backup copy is used
                    default : None
                revert (bool) : True if revert is enabled
                    default : False
        """
        self.log.info("#### Cleaning up metadata on Snap DB before running Restore ####")
        self.hana_helper.cleanup_test_data(tenant_connection=True)

        self.navigate_to_backupset(backupset_name=self.tcinputs['InstanceName'])

        advanced_options = {}
        if backup_copy:
            advanced_options["copyPrecedence"] = "Primary"
        if revert:
            advanced_options["hardwareRevert"] = True

        match type:
            case "most recent":
                self.run_restore(advanced_options=advanced_options)
            case "pit":
                self.run_restore(point_in_time=self.point_in_time, advanced_options=advanced_options)
            case "backup prefix":
                self.run_restore(backup_prefix=self.backup_prefix, advanced_options=advanced_options)
            case "internal backup id":
                self.run_restore(internal_backup_id=self.internal_backup_id, advanced_options=advanced_options)

        self.log.info("#### Get the %s metadata after restore ####", self.tcinputs['InstanceName'])
        restore_metadata = self.hana_helper.get_meta_data(_tenant_connection=True)
        self.hana_helper.validate_db_info(backup_map, restore_metadata)

    @test_step
    def navigate_to_backupset(self, backupset_name="SYSTEMDB"):
        """ navigates to specified backupset page of the instance

        Args:
            backupset_name  (str) : backupset name
                default : "SYSTEMDB"

        """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.SAP_HANA,
            self.tcinputs['InstanceName'], self.tcinputs['Client'])
        self.db_instance_details.click_on_entity(backupset_name)

    @test_step
    def add_instance(self):
        """ Adding new HANA instance
        """
        self.log.info("Creating Instance...")
        self.database_instances.add_saphana_instance(system_name=self.tcinputs['Client'],
                                                     sid=self.tcinputs['InstanceName'],
                                                     plan=self.tcinputs['PlanName'],
                                                     host_list=[self.tcinputs['HostName']],
                                                     database_user=self.tcinputs['DBUser'],
                                                     database_password=self.tcinputs['DBPassword'],
                                                     add_new_system=True)

        self.database_instances.select_instance(DBInstances.Types.SAP_HANA,
                                                self.tcinputs["InstanceName"],
                                                self.tcinputs["Client"])

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("#### Full Snap Backup tenant DB ####")
            meta_data = self.backup_operations()

            self.log.info("#### In place Restore most recent from snap copy ####")
            self.restore_operations(meta_data, type="most recent")
            self.log.info("#### In place Restore most recent from backup copy ####")
            self.restore_operations(meta_data, type="most recent", backup_copy=True)
            self.log.info("#### In place Restore most recent from snap copy with revert ####")
            self.restore_operations(meta_data, type="most recent", revert=True)

            self.log.info("#### In place Restore PIT from snap copy ####")
            self.restore_operations(meta_data, type="pit")
            self.log.info("#### In place Restore PIT from backup copy ####")
            self.restore_operations(meta_data, type="pit", backup_copy=True)
            self.log.info("#### In place Restore PIT from snap copy with revert ####")
            self.restore_operations(meta_data, type="pit", revert=True)

            self.log.info("#### In place Restore Backup Prefix from snap copy ####")
            self.restore_operations(meta_data, type="backup prefix")
            self.log.info("#### In place Restore Backup Prefix from backup copy ####")
            self.restore_operations(meta_data, type="backup prefix", backup_copy=True)

            self.log.info("#### In place Restore Internal Backup ID from snap copy ####")
            self.restore_operations(meta_data, type="internal backup id")
            self.log.info("#### In place Restore Internal Backup ID from backup copy ####")
            self.restore_operations(meta_data, type="internal backup id", backup_copy=True)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
