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

    get_job_details()           --  Method to get job details

    run_backup()                --  method to run backup for HANA DB

    run_restore()               --  method to run restore for HANA DB

    enable_snap_operations()    --  Method to enable snap backup operation

    backup_operations()         --  backup operations for DB and metadata creation

    backup_copy()               --  Method to run backup copy operation

    restore_operations()        --  Restore operations for DB and validate test data after restore

    navigate_to_backupset()     --  navigates to specified backupset page of the instance

    add_instance()              --  Adding new HANA instance

    run()                       --  Main function for test case execution

Input Example:

    "testCases":
            {
                "52957": {
                    "Client":"abc",
                    "DestinationClient":"def"
                    "AgentName":"SAPHANA",
                    "InstanceName":"abc",
                    "PlanName":"backupPlan",
                    "SourcreDB":"HDB1"
                    "DBUser":"sys",
                    "DBPassword":"***",
                    "DestinationDB":"HDB2",
                    "DestinationDBUser":"sys",
                    "DestinationDBPassword":"***",
                }
            }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
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
    """ Class for executing SAP HANA 2.0 MDC - Database Copy same SID different Tenant DB """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAP HANA 2.0 MDC - Database Copy same SID different Tenant DB"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance_details = None
        self.database_instances = None
        self.backupset_page = None
        self.restore_panel = None
        self.subclient_page = None
        self.hana_helper_src = None
        self.hana_helper_dst = None
        self.page_container = None
        self.rtable = None
        self.job_details = None
        self.tcinputs = {
            "Client": None,
            "DestinationClient": None,
            "AgentName": None,
            "InstanceName": None,
            "PlanName": None,
            "DBUser": None,
            "DBPassword": None,
            "DestinationDB": None,
            "DestinationDBUser": None,
            "DestinationDBPassword": None,
        }
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
        self.hana_helper_src.cleanup_test_data(tenant_connection=True)
        self.hana_helper_dst.cleanup_test_data(tenant_connection=True)
        self.log.info("#### cleanup done ####")

    @test_step
    def create_helper_object(self):
        """  Creates HANA helper object for doing all related operations to HANA database
        """
        self.hana_helper_src = HANAHelper(commcell=self.commcell, client_name=self.tcinputs['Client'],
                                      instance_name=self.tcinputs['InstanceName'],
                                      backupset_name=self.tcinputs['SourcreDB'], subclient_name='default')
        self.hana_helper_dst = HANAHelper(commcell=self.commcell, client_name=self.tcinputs['Client'],
                                          instance_name=self.tcinputs['InstanceName'],
                                          backupset_name=self.tcinputs['DestinationDB'], subclient_name='default')

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
    def run_restore(self, **kwargs):
        """ method to run restore for HANA DB
            Args:
                kwargs (dict) : keyword arguments for restore operation
        """
        self.log.info("#### Running SapHana Out of place Restore ####")
        job_id = self.restore_panel.out_of_place_restore(**kwargs)
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("#### SapHana Out of place restore is completed ####")

    @test_step
    def backup_operations(self, tenant_connection=False, backupset_name="SYSTEMDB", data_only=False):
        """
            backup operations for DB and metadata creation

            Args:
                Args:
                tenant_connection  (boolean) : HANA DB connection, True will connect to tenant DB,
                                                                                False will connect to SYSTEMDB'
                    default : False

                backupset_name (str) : backupset name
                    default : "SYSTEMDB"
                data_only (boolean) : True will get backup prefix and end time of job
                    default : False
            returns:
                dictionary (dict) : collected metadata after backup
        """
        self.navigate_to_backupset(backupset_name=backupset_name)
        backupset_page = Backupset(self.admin_console)
        backupset_page.access_subclient('default')

        self.log.info("#### Creating test data before FULL Backup ####")
        self.hana_helper_src.create_test_tables(tenant_connection=tenant_connection)
        self.log.info("#### Tables are created successfully ####")
        self.run_backup(RBackup.BackupType.FULL, backupset_name=backupset_name)

        if data_only:
            self.log.info("#### Collect Backup Prefix and End time of job ####")
            self.get_job_details()
        else:
            self.log.info("#### Creating test data before Inc Backup ####")
            self.hana_helper_src.create_test_tables(tenant_connection=tenant_connection)
            self.log.info("#### Tables are created successfully ####")
            self.run_backup(RBackup.BackupType.INCR, backupset_name=backupset_name)
            self.log.info("#### Creating test data before Diff Backup ####")
            self.hana_helper_src.create_test_tables(tenant_connection=tenant_connection)
            self.log.info("#### Tables are created successfully ####")
            self.run_backup(RBackup.BackupType.DIFF, backupset_name=backupset_name)

        self.log.info("#### Collect the metadata for %s ####", backupset_name)
        return self.hana_helper_src.get_meta_data(_tenant_connection=tenant_connection)

    @test_step
    def restore_operations(self, backup_map, tenant_connection=False, backupset_name="SYSTEMDB", restore_type=None):
        """
        Restore operations for DB and validate test data after restore

            Args:
                backup_map (dict) : metadata collected after backup
                tenant_connection  (boolean) : HANA DB connection, True will connect to tenant DB,
                                                                                False will connect to SYSTEMDB
                    default = False

                backupset_name (str) : backupset name
                    default : "SYSTEMDB"
                restore_type (str) : Type of restore operation
                    default : None
        """
        self.log.info("#### Cleaning up metadata on DB before running Restore ####")
        self.hana_helper_dst.cleanup_test_data(tenant_connection=tenant_connection)

        self.navigate_to_backupset(backupset_name=backupset_name)
        destination_database = self.tcinputs["DestinationDB"] if backupset_name != "SYSTEMDB" else "SYSTEMDB"
        args = {
            "destination_client": self.tcinputs["DestinationClient"],
            "destination_instance": self.tcinputs["InstaneName"],
            "destination_database": destination_database
        }
        match restore_type:
            case "most recent":
                self.run_restore(**args)
            case "pit":
                self.run_restore(**args, point_in_time=self.point_in_time)
            case "backup prefix":
                self.run_restore(**args, backup_prefix=self.backup_prefix)
            case "internal backup id":
                self.run_restore(**args, internal_backup_id=self.internal_backup_id)

        self.log.info("#### Get the %s metadata after restore ####", backupset_name)
        restore_metadata = self.hana_helper_dst.get_meta_data(_tenant_connection=tenant_connection)
        self.hana_helper_dst.validate_db_info(backup_map, restore_metadata)

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
            self.log.info("#### FULL Backup for System DB ####")
            bkp_metadata_1 = self.backup_operations(data_only=True)
            self.log.info("#### FULL, INC, DIFF Backup for System DB ####")
            bkp_metadata_2 = self.backup_operations()

            self.log.info("#### Most Recent Restore for SYSTEM DB ###")
            self.restore_operations(bkp_metadata_2, restore_type="most recent")
            self.log.info("#### PIT Restore for SYSTEM DB ###")
            self.restore_operations(bkp_metadata_1, restore_type="pit")
            self.log.info("#### Data Only Restore using Backup Prefix for SYSTEM DB ###")
            self.restore_operations(bkp_metadata_1, restore_type="backup prefix")
            self.log.info("#### Data Only Restore using Internal Backup ID for SYSTEM DB ###")
            self.restore_operations(bkp_metadata_1, restore_type="internal backup id")

            args = {
                "tenant_connection": True,
                "backupset_name": self.tcinputs["SourcreDB"]
            }

            self.log.info("#### FULL Backup for Tenant DB ####")
            bkp_metadata_3 = self.backup_operations(**args, data_only=True)
            self.log.info("#### FULL, INC, DIFF Backup for Tenant DB ####")
            bkp_metadata_4 = self.backup_operations(**args)

            self.navigator.navigate_to_db_instances()
            self.admin_console.wait_for_completion()

            self.log.info("#### Most Recent Restore for Tenant DB ###")
            self.restore_operations(bkp_metadata_4, **args, restore_type="most recent")
            self.log.info("#### PIT Restore for Tenant DB ###")
            self.restore_operations(bkp_metadata_3, **args, restore_type="pit")
            self.log.info("#### Data Only Restore using Backup Prefix for Tenant DB ###")
            self.restore_operations(bkp_metadata_3, **args, restore_type="backup prefix")
            self.log.info("#### Data Only Restore using Internal Backup ID for Tenant DB ###")
            self.restore_operations(bkp_metadata_3, **args, restore_type="internal backup id")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
