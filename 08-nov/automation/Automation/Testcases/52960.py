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

    create_helper_object()      -- Create HANA helper object

    backup()                    --  method to run backup for HANA DB

    set_pit()                   --  method to set pit of a backup

    restore()                   --  restore operation for the client

    job_restore()               --  Restore from a specific job

    navigate_to_backupset()     --  navigates to specified backupset page of the instance

    wait_for_latest_job()       --  waits for the latest job of a client to finish

    run()                       --  Main function for test case execution

    tear_down()                 --  tear down method for testcase, delete automation created test data

Input Example:

    "testCases":
            {
            "52960": {
                "ClientName":"Client name for source client",
                "InstanceName":"Instance name for source",
                "source_database":"Source db na,e",
                "destination_client": "Client name for destination client",
                "destination_instance": "Instance name for destination",
                "destination_database": "Destination db name"
                }
            }

"""

from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Databases.subclient import SubClient
from Web.AdminConsole.Databases.Instances.restore_panels import SAPHANARestorePanel
from Database.dbhelper import DbHelper
from Database.SAPHANAUtils.hana_helper import HANAHelper


class TestCase(CVTestCase):
    """Class for executing testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAP HANA 2.0 MDC - Database Copy to Cross Tenant DB"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance_details = None
        self.database_instances = None
        self.backupset_page = None
        self.restore_panel = None
        self.job = None
        self.subclient_page = None
        self.hana_helper = None
        self.tcinputs = {
            "ClientName": None,
            "InstanceName": None,
            "source_database": None,
            "destination_client": None,
            "destination_instance": None,
            'destination_database': None,
        }
        self.dbhelper_object = None
        self.restore_job_id = None
        self.point_in_time = None
        self.last_job_id = None
        self.full_backup = None
        self.incr_backup = None
        self.log_backup = None
        self.diff_backup = None
        self.db_map = dict()

    def setup(self):
        """Method to setup test variables"""
        self.log.info("Started executing %s testcase", self.id)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.job = Jobs(self.admin_console)
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.restore_panel = SAPHANARestorePanel(self.admin_console)
        self.backupset_page = DBInstanceDetails(self.admin_console)
        self.dbhelper_object = DbHelper(self.commcell)
        self.subclient_page = SubClient(self.admin_console)
        self.full_backup = RBackup.BackupType.FULL
        self.incr_backup = RBackup.BackupType.INCR
        self.log_backup = RBackup.BackupType.TRANSAC
        self.diff_backup = RBackup.BackupType.DIFF

    @test_step
    def create_helper_object(self):
        """Creates HANA helper object for doing all related operations to HANA database"""
        self.hana_helper = HANAHelper(commcell=self.commcell, client_name=self.tcinputs['ClientName'],
                                      instance_name=self.tcinputs['InstanceName'],
                                      backupset_name=self.tcinputs['InstanceName'], subclient_name='default')

    @test_step
    def backup(self, backup_type):
        """
        Method to run backup for HANA DB
        Args:
            backup_type (backup_type) : FULL/INCR/DIFF/LOG
        """
        self.navigate_to_backupset()
        self.db_instance_details.click_on_entity(self.tcinputs["InstanceName"])
        self.db_instance_details.click_on_entity('default')
        self.log.info("#### Running SapHana Backup ####")
        job_id = self.subclient_page.backup(backup_type)
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.last_job_id = job_id
        self.log.info("#### SapHana backup is completed ####")

    def set_pit(self, operation):
        """
        Sets the Point In Time (PIT) to the current time.
        Args:
            operation (str) : opeation to set pit for (command_line, command_center)
        """
        current_time = datetime.now()
        formatted_time = ''
        if operation == 'command_center':
            formatted_time = current_time.strftime("%m/%d/%Y %H:%M:%S")
        elif operation == 'command_line':
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        self.point_in_time = formatted_time
        self.log.info(f"Set PIT to {formatted_time}")

    @test_step
    def restore(self, point_in_time=None, backup_prefix=None, internal_backup_id=None):
        """
        Method to run restore for HANA DB
        Args:
            point_in_time (str) : Point in time for restore
                default : None
            backup_prefix (str) : Backup prefix for restore
                default : None
            internal_backup_id (int) : Internal backup id for restore
                default : None
        """
        self.navigate_to_backupset()
        self.db_instance_details.click_on_entity(self.tcinputs['source_database'])
        self.backupset_page.access_restore()
        self.log.info("#### Running SapHana Restore ####")
        job_id = self.restore_panel.out_of_place_restore(
            destination_client=self.tcinputs['destination_client'],
            destination_instance=self.tcinputs['destination_instance'],
            point_in_time=point_in_time,
            backup_prefix=backup_prefix,
            internal_backup_id=internal_backup_id,
        )
        self.dbhelper_object.wait_for_job_completion(job_id)
        self.log.info("#### SapHana restore is completed ####")

    def job_restore(self, job_id):
        """
        Restores a job to the specified destination.
        Args:
           job_id (str): ID of the job to be restored.
        """
        self.navigate_to_backupset()
        self.backupset_page.list_backup_history()
        self.log.info(f"#### Running job {job_id} SapHana Restore ####")
        self.job.job_restore(job_id)
        restore_job = self.restore_panel.out_of_place_restore(
            destination_client=self.tcinputs['destination_client'],
            destination_instance=self.tcinputs['destination_instance'])
        self.dbhelper_object.wait_for_job_completion(restore_job)
        self.log.info(f"#### SapHana job {job_id} restore is completed ####")

    @test_step
    def navigate_to_backupset(self):
        """navigates to specified backupset page of the instance"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.SAP_HANA,
            self.tcinputs['InstanceName'], self.tcinputs['ClientName'])

    def wait_for_latest_job(self):
        """wait for the latest job of a client to complete"""
        latest_job = None
        while latest_job is None:
            jobs = self.commcell.job_controller.all_jobs(client_name=self.tcinputs['ClientName'])
            latest_job = (job_id for job_id, details in jobs.items() if "Application Command Line"
                          in details['operation'] and details['job_start_time'] > self.hana_helper._job_start)
            self.dbhelper_object.wait_for_job_completion(latest_job)
        self.log.info(f"waiting for job {latest_job} to complete")

    def run(self):
        """Main function for test case execution"""
        try:
            self.create_helper_object()
            self.hana_helper.create_test_tables()
            self.backup(self.full_backup)
            self.db_map['pit_backup'] = self.hana_helper.get_metadata()
            self.set_pit(operation='command_center')
            self.hana_helper.create_test_tables()
            self.backup(self.incr_backup)
            self.restore_job_id = self.last_job_id
            self.db_map['job_backup'] = self.hana_helper.get_metadata()
            self.hana_helper.create_test_tables()
            self.backup(self.diff_backup)
            self.db_map['recent_backup'] = self.hana_helper.get_metadata()
            self.restore()
            self.db_map['recent_restore'] = self.hana_helper.get_metadata()
            self.hana_helper.validate_db_info(self.db_map['recent_restore'], self.db_map['recent_backup'])
            self.restore(point_in_time=self.point_in_time)
            self.db_map['pit_restore'] = self.hana_helper.get_metadata()
            self.hana_helper.validate_db_info(self.db_map['pit_restore'], self.db_map['pit_backup'])
            self.job_restore(self.restore_job_id)
            self.db_map['job_restore'] = self.hana_helper.get_metadata()
            self.hana_helper.validate_db_info(self.db_map['job_restore'], self.db_map['job_backup'])
            self.hana_helper.run_hdbsql_command(operation='backup', database='SYSTEMDB')
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='backup', database='SYSTEMDB', backup_type='incr')
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='backup', database='SYSTEMDB', backup_type='diff')
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='backup', database=self.tcinputs["source_database"])
            self.wait_for_latest_job()
            self.set_pit(operation='command_line')
            self.hana_helper.run_hdbsql_command(operation='backup', database=self.tcinputs["source_database"],
                                                backup_type='incr')
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='backup', database=self.tcinputs["source_database"],
                                                backup_type='diff')
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='restore', database="SYSTEMDB",
                                                source_database=self.tcinputs['source_database'],
                                                pit=False, destination_databse=self.tcinputs['destination_database'])
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='restore', database='SYSTEMDB',
                                                source_database=self.tcinputs['source_database'], pit=self.point_in_time
                                                , destination_database=self.tcinputs['destination_database'])
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='restore', database='SYSTEMDB',
                                                source_database=self.tcinputs['source_database'],
                                                using_backint=self.hana_helper.last_backup_backint,
                                                destination_databse=self.tcinputs['destination_database'])
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='restore', database=self.tcinputs["source_database"],
                                                source_database=self.tcinputs['source_database'],
                                                pit=False, destination_database=self.tcinputs['destination_database'])
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='restore', atabase=self.tcinputs["source_database"],
                                                pit=self.point_in_time, source_database=self.tcinputs['source_database']
                                                , destination_database=self.tcinputs['destination_database'])
            self.wait_for_latest_job()
            self.hana_helper.run_hdbsql_command(operation='restore', atabase=self.tcinputs["source_database"],
                                                source_database=self.tcinputs['source_database'],
                                                using_backint=self.hana_helper.last_backup_backint,
                                                destination_databse=self.tcinputs['destination_database'])
            self.wait_for_latest_job()

        except Exception:
            raise CVWebAutomationException

        finally:
            self.hana_helper.cleanup_test_data()

    def tear_down(self):
        """Tear Down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
