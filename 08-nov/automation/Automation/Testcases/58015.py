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

    wait_for_job_completion()   --  Waits for completion of job and gets the
                                    object once job completes

    add_instance()              --  adds db2 instance

    delete_db2_instance()       --  deletes db2 instance if already exists

    discover_databases()        --  discovers databases under given instance

    trigger_backup_at_instance()    --  triggers backup for default subclient

    navigate_to_backupset()     --  method to navigate cursor to backupset page

    run_restore_validate()      --  method to run restore and validate test data

    run()                       --  run function of this test case

Input Example:

    "testCases":
            {
                "58015":
                        {
                            "ClientName": "client_name",
                            "InstanceName": "db2_instance_name",
                            "Backupset": "database_name",
                            "StoragePolicyName": "plan_name",
                            "DB2User": "db2_instance_user",
                            "DB2UserPassword": "db2_user_password",
                            "DB2HomePath": "instance_home_path",
                            "credential_name": "cred_name"
                        }
            }

"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure
from Database.DB2Utils.db2helper import DB2
from Web.AdminConsole.Components.dialog import RBackup
import time

class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for DB2 backup and restore using adminconsole """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Db2 ACCT1 automation case for command center "
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db2_helper = None
        self.machine_obj = None
        self.db2_user = None
        self.db2_password = None
        self.db2_instance = None
        self.db2_home = None
        self.db2_dbname = None
        self.storagepolicy = None
        self.credential_name = None
        self.storage_plan = None
        self.table_name = None
        self.tablespace_name = None
        self.os_info = None
        self.datafile = None
        self.database_type = None
        self.database_instances = None
        self.db_instance_details = None
        self.backupset_page = None
        self.tcinputs = {
            'Instance': None,
            'Backupset': None,
            'Subclient': None,
            'StoragePolicyName': None,
            'DB2User': None,
            'DB2UserPassword': None,
            'DB2HomePath': None,
            "credential_name": None
        }

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.browse = RBrowse(self.admin_console)
        self.client = self.commcell.clients.get(self.tcinputs['ClientName'])
        self.navigator.navigate_to_db_instances()
        self.database_instances = DBInstances(self.admin_console)
        self.db_instance_details = Db2InstanceDetails(self.admin_console)
        self.machine_obj = Machine(self.client)
        self.db2_user = self.tcinputs["DB2User"]
        self.db2_password = self.tcinputs['DB2UserPassword']
        self.db2_instance = self.tcinputs['Instance']
        self.db2_home = self.tcinputs['DB2HomePath']
        self.db2_dbname = self.tcinputs['Backupset']
        self.subclient = self.tcinputs['Subclient']
        self.storagepolicy = self.tcinputs['StoragePolicyName']
        self.storage_plan = self.tcinputs['StoragePolicyName']
        self.credential_name = self.tcinputs['credential_name']
        self.table_name = "T52802"
        self.tablespace_name = "TS52802"
        self.os_info = self.client.os_info
        if "windows" in self.os_info.lower():
            self.db2_user = self.client.display_name + '\\' + self.db2_user
        self.database_type = DBInstances.Types.DB2

    @test_step
    def wait_for_job_completion(self, jobid):
        """Waits for completion of job and gets the object once job completes
        Args:
            jobid   (int): Jobid
        """
        job_obj = self.commcell.job_controller.get(jobid)
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed to run job:%s with error: %s" % (jobid, job_obj.delay_reason)
            )
        self.log.info("Successfully finished %s job", jobid)
        return True

    @test_step
    def add_instance(self):
        """add new db2 instance"""
        self.navigator.navigate_to_db_instances()

        self.database_instances.add_db2_instance(
            self.tcinputs['ClientName'],
            self.db2_instance,
            self.storage_plan,
            self.db2_home,
            self.db2_user,
            self.db2_password,
            credential_name=self.credential_name)

    @test_step
    def delete_db2_instance(self):
        """
        method to delete the db2 instance

        Args:
            db2_instance (str):   name of the db2 instance to be deleted

        """
        self.navigator.navigate_to_db_instances()
        self.database_instances = DBInstances(self.admin_console)
        try:
            self.database_instances.select_instance(
                self.database_type, self.db2_instance, self.tcinputs['ClientName'])
            db_instance_details = DBInstanceDetails(self.admin_console)
            db_instance_details.delete_instance()
            self.log.info(" *****existing instance deleted successfully*****")
        except Exception as exp:
            self.log.info(" given db2 instance does not exists ")

    @test_step
    def discover_databases(self):
        """discover db2 databases/backupsets"""
        self.navigator.navigate_to_db_instances()
        self.database_instances.react_instances_table.reload_data()
        self.database_instances.select_instance(
            self.database_type, self.db2_instance, self.tcinputs['ClientName'])

        self.admin_console.access_tab("Databases")
        self.admin_console.click_button("Discover databases", "discoverDB")

        time.sleep(60) #Let all the database get discovered. Due to huge number takes some time.
        self.admin_console.refresh_page()

    @test_step
    def trigger_backup_at_instance(self):
        """trigger backup on backupset actions in db2 instance level page"""

        self.navigator.navigate_to_db_instances()
        self.database_instances = DBInstances(self.admin_console)
        self.database_instances.select_instance(
            self.database_type, self.db2_instance, self.tcinputs['ClientName'])
        self.db_instance_details = DBInstanceDetails(self.admin_console)
        self.db_instance_details.click_on_entity(self.tcinputs['Backupset'])
        backupset_page = DB2Backupset(self.admin_console)
        backupset_page.access_subclient('default')
        subclient_page = DB2Subclient(self.admin_console)

        db2_instance_options_windows = {"domain_name": self.client.client_name,
                                        "password": self.db2_password,
                                        "user_name": self.db2_user,
                                        "instance_name": self.db2_instance,
                                        "home_directory": self.db2_home,
                                        "data_storage_policy": self.storagepolicy,
                                        "log_storage_policy": self.storagepolicy,
                                        "command_storage_policy": self.storagepolicy,
                                        "storage_policy": self.storagepolicy}

        db2_instance_options = {"password": self.db2_password,
                                "user_name": self.db2_user,
                                "instance_name": self.db2_instance,
                                "home_directory": self.db2_home,
                                "data_storage_policy": self.storagepolicy,
                                "log_storage_policy": self.storagepolicy,
                                "command_storage_policy": self.storagepolicy,
                                "storage_policy": self.storagepolicy}

        db2_backupset_options = {"backupset_name": self.db2_dbname,
                                 "storage_policy_name": self.storagepolicy}

        try:
            self.instance = self.agent.instances.get(
                db2_instance_options['instance_name'])

            try:
                self.log.info(
                    "If backupset already exists, it will be deleted and recreated ")
                self.backupset = self.instance.backupsets.get(
                    db2_backupset_options['backupset_name'])
            except BaseException:
                self.log.info("get backupset props failed")

        except Exception as exp:
            self.log.error('get instance details failed: %s exp ', exp)

        self.log.info("######### loading db2helper ##########")
        self.db2_helper = DB2(
            self.commcell,
            self.client,
            self.instance,
            self.backupset)
        self.datafile = self.db2_helper.get_datafile_location()
        self.log.info("#####Get Version#######")
        version = self.db2_helper.get_db2_version()
        self.log.info("Version: %s", version)
        self.log.info("#####Update Db2 Config#######")
        self.db2_helper.update_db2_database_configuration1()
        self.log.info("Running FULL Backup.")
        job_id = subclient_page.backup(backup_type=RBackup.BackupType.FULL)
        self.wait_for_job_completion(job_id)
        self.log.info("FULL backup is completed")
        self.log.info("Running INCR backup.")
        job_id = subclient_page.backup(backup_type=RBackup.BackupType.INCR)
        self.wait_for_job_completion(job_id)
        self.log.info("Incremental backup completed")
        self.log.info("Running delta backup ")
        job_id = subclient_page.backup(backup_type=RBackup.BackupType.DIFF)
        self.wait_for_job_completion(job_id)
        self.log.info("Delta backup complete successfully")

    @test_step
    def navigate_to_backupset(self, db2_dbname):
        """ navigates to specified backupset page of the instance

        Args:
            db2_dbname  (str)   --  backupset name

                db2_dbname = "Backupset"

        """
        self.navigator.navigate_to_db_instances()
        self.database_instances.select_instance(
            DBInstances.Types.DB2,
            self.tcinputs['Instance'], self.tcinputs['ClientName'])
        self.db_instance_details.click_on_entity(db2_dbname)

    @test_step
    def run_restore_validate(
            self, backupset_page, db2_dbname):
        """ method to run restore and validate test data

        Args:

            backupset_page      (obj)   --  backupset page object

            db2_dbname          (str)   --  backupset name

        """
        self.navigate_to_backupset(db2_dbname)
        self.log.info(
            "#" * (10) + "  Running " + db2_dbname + " Restore  " + "#" * (10))





        backupset_page.access_restore()
        self.browse.show_latest_backups(database=True)
        restore_panel = None

        restore_panel = backupset_page.restore_folders(
            database_type=DBInstances.Types.DB2, all_files=True)
        self.db2_helper.disconnect_applications(
            self.backupset.backupset_name)
        job_id = restore_panel.in_place_restore(endlogs=True)
        self.log.info("restore job is %s", job_id)
        job_status = self.wait_for_job_completion(job_id)

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client.display_name)
        for key, _ in all_jobs.items():
            if 'application' in all_jobs[key]['operation'].lower() and \
                    'restore' in all_jobs[key]['operation'].lower():
                job = self.commcell.job_controller.get(key)
                self.log.info("Waiting for Jobs to Complete (Job Id: %s)", key)
                job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")
        self.log.info("Restore completed")
        self.db2_helper.reconnect()

    def run(self):
        """ Main function for test case execution """
        try:
            self.delete_db2_instance()
            self.add_instance()
            self.discover_databases()
            self.trigger_backup_at_instance()
            backupset_page = DB2Backupset(self.admin_console)
            self.run_restore_validate(backupset_page, self.db2_dbname)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
