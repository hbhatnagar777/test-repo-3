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

    wait_for_job_completion()   --  Waits for completion of job and gets the
    object once job completes

    navigate_to_backupset()     --  navigates to specified backupset page of the instance

    get_point_in_time()         --  Gets the end time of the job

    run_backup()                --  Run backup operation

    run_restore                 --  Run restore operation

    add_instance()              --  creates a new instance of specified type
                                    with specified name and details

    backup_operations()         --  Running backup and create data for each backup

    restore_operations()        -- Restore operations for DB and validate metadata after restore

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "65635":
                        {
                          "Client":"hana1_ABC",
                          "AgentName":"SAP HANA",
                          "InstanceName":"ABC",
                          "PlanName":"planName",
                          "HostName":"hana1",
                          "DBUser":"abcd",
                          "DBPassword":"abcd"
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
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Databases.backupset import Backupset
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.Instances.restore_panels import SAPHANARestorePanel
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Database.SAPHANAUtils.hana_helper import HANAHelper


class TestCase(CVTestCase):
    """ Class for executing SAP HANA Command Center Point in Time Restore """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAP HANA Command Center Point in Time Restore"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.db_instance_details = None
        self.backupset_page = None
        self.restore_panel = None
        self.subclient_page = None
        self.hana_helper = None
        self.tcinputs = {
            "Client": None,
            "AgentName": None,
            "InstanceName": None,
            "PlanName": None,
            "HostName": None,
            "DBUser": None,
            "DBPassword": None
        }
        self.system_bkp = {}
        self.tenant_bkp = {}
        self.restore_metadata = {}
        self.page_container = None
        self.rtable = None
        self.job_details = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("**** Initialize browser objects ****")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.change_language("English", self.admin_console)
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.backupset_page = DBInstanceDetails(self.admin_console)
        self.restore_panel = SAPHANARestorePanel(self.admin_console)
        self.subclient_page = SubClient(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.job_details = JobDetails(self.admin_console)
        self.log.info("#### SAP HANA Instance Operations ####")
        self.navigator.navigate_to_db_instances()
        self.admin_console.wait_for_completion()
        self.log.info("____ Checking if instance exists ____")
        if self.database_instances.is_instance_exists(DBInstances.Types.SAP_HANA,
                                                      self.tcinputs["InstanceName"],
                                                      self.tcinputs["Client"]):
            self.log.info("####  Instance Found  ####")
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
        self.hana_helper.cleanup_test_data()
        self.hana_helper.cleanup_test_data(tenant_connection=True)
        self.log.info("#### cleanup done ####")

    @test_step
    def create_helper_object(self):
        """  Creates HANA helper object

        """
        self.hana_helper = HANAHelper(commcell=self.commcell, client_name=self.tcinputs['Client'],
                                      instance_name=self.tcinputs['InstanceName'],
                                      backupset_name=self.tcinputs['InstanceName'], subclient_name='default')

    @test_step
    def wait_for_job_completion(self, jobid):
        """ Waits for completion of job and gets the object once job completes
            Args:
                jobid   (int) : Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise CVTestStepFailure(
                f"Failed to run job:{jobid} with error: {job_obj.delay_reason}"
            )
        self.log.info("Successfully finished %s job", jobid)

    @test_step
    def navigate_to_backupset(self, backupset_name="SYSTEMDB"):
        """ navigates to specified backupset page of the instance

        Args:
            backupset_name (str) : backupset name

                default = "SYSTEMDB"

        """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.SAP_HANA,
            self.tcinputs['InstanceName'], self.tcinputs['Client'])
        self.db_instance_details.click_on_entity(backupset_name)

    @test_step
    def get_point_in_time(self, job_id):
        """
        Gets the end time of the job
        Args:
            job_id (int): job id
        Returns:
            end time of the job
        """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.SAP_HANA,
            self.tcinputs['InstanceName'], self.tcinputs['Client'])
        self.page_container.select_tab("Jobs")
        self.rtable.access_link(job_id)
        return self.job_details.get_progress_details()["End time"]

    @test_step
    def run_backup(self, backup_type, backupset_name="SYSTEMDB", get_pit=False):
        """ Method to run HANA DB backup
            Args:
                backup_type (backup_type): FULL/INCR/DIFF

                backupset_name (str): backupset name
                    default = "SYSTEMDB"
                get_pit (bool): return end time of job.
                    default = False
            returns:
                end time of job if get_pit is True

        """
        self.log.info(
            "#### Running SapHana %s backup for database %s ####", format(backup_type.name), backupset_name)
        job_id = self.subclient_page.backup(backup_type)
        self.wait_for_job_completion(job_id)
        self.log.info(
            "#### SapHana %s Backup is completed for database %s ####", format(backup_type.name), backupset_name)
        return self.get_point_in_time(job_id) if get_pit else None

    @test_step
    def run_restore(self, backupset_name="SYSTEMDB", point_in_time=None):
        """ method to run HANA DB restore
            Args:
                backupset_name (str) : backupset name
                    default = "SYSTEMDB"
                point_in_time (str) : backup prefix
                    default = None
        """
        self.backupset_page.access_restore()
        self.log.info("#### Running SapHana %s most recent In_place Restore ####", backupset_name)
        job_id = self.restore_panel.in_place_restore(point_in_time=point_in_time, advanced_options={"InitializeLogArea": True})
        self.wait_for_job_completion(job_id)
        self.log.info("#### SapHana %s most recent In_place restore is completed ####", backupset_name)

    @test_step
    def add_instance(self):
        """Adding new HANA instance
        """
        self.log.info(" Inside Instance creation call ")
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

    @test_step
    def backup_operations(self, tenant_connection=False, backupset_name="SYSTEMDB"):
        """
            backup operations for DB and metadata creation

            Args:
                Args:
                tenant_connection  (boolean) : HANA DB connection, True will connect to tenant DB,
                                                                                False will connect to SYSTEMDB'
                    default : False

                backupset_name (str) : backupset name
                    default : "SYSTEMDB"

            returns:
            tuple : (dict, str)
                dictionary (dict) : collected metadata after backup
                point_in_time (str) : end time of backup job
        """
        self.navigate_to_backupset(backupset_name=backupset_name)
        backupset_page = Backupset(self.admin_console)
        backupset_page.access_subclient('default')

        self.log.info("#### Creating test data before FULL Backup ####")
        self.hana_helper.create_test_tables(tenant_connection=tenant_connection)
        self.log.info("#### Tables are created successfully ####")
        point_in_time = self.run_backup(RBackup.BackupType.FULL, backupset_name=backupset_name, get_pit=True)
        meta_data = self.hana_helper.get_meta_data(_tenant_connection=tenant_connection)

        self.navigate_to_backupset(backupset_name=backupset_name)
        backupset_page = Backupset(self.admin_console)
        backupset_page.access_subclient('default')

        self.hana_helper.create_test_tables(tenant_connection=tenant_connection)
        self.log.info("#### Tables are created successfully ####")
        self.run_backup(RBackup.BackupType.FULL, backupset_name=backupset_name)

        return meta_data, point_in_time

    @test_step
    def restore_operations(self, backup_map, tenant_connection=False, backupset_name="SYSTEMDB", point_in_time=None):
        """
        Restore operations for DB and validate metadata after restore

            Args:
                Args:

                backup_map (dict)   : Metadata collected before restore

                tenant_connection  (boolean) : HANA DB connection, True will connect to tenant DB,
                                                                                False will connect to SYSTEMDB'
                    default = False

                backupset_name (str)    :  backupset name
                    default = "SYSTEMDB"

        """
        if backupset_name == "SYSTEMDB":
            self.log.info("#### Cleaning up metadata on database before running Restore ####")
            self.hana_helper.cleanup_test_data()
            self.hana_helper.cleanup_test_data(tenant_connection=True)

        self.navigate_to_backupset(backupset_name=backupset_name)
        self.run_restore(backupset_name=backupset_name, point_in_time=point_in_time)

        self.log.info("#### Get the %s metadata after restore ####", backupset_name)
        restore_metadata = self.hana_helper.get_meta_data(_tenant_connection=tenant_connection)
        self.hana_helper.validate_db_info(backup_map, restore_metadata)

    def run(self):
        """ Main function for test case execution """
        try:
            #### Tenant DB backup ####
            self.tenant_bkp, point_in_time = self.backup_operations(True, self.tcinputs['InstanceName'])
            self.log.info("#### Database %s backup operations completed and metadata collected ####",
                          self.tcinputs['InstanceName'])
            #### TenantDB Restore ####
            self.restore_operations(self.tenant_bkp, True, self.tcinputs['InstanceName'], point_in_time=point_in_time)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)