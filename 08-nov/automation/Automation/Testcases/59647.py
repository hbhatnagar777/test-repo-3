# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"59647": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "InstanceName": "db2inst1",
            "BackupsetName": "SAMPLE",
            "db2_username": "db2inst1",
            "db2_user_password": "test",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    refresh_commcell()                          --  Refreshes commcell properties and get updated client's properties

    edit_instance_property()                    --  Editing instance properties to add username and password

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    navigate_db2_instance_details_page()        --  Navigates to instance details page

    run_backup()                                --  Runs a backup

    run_restore()                               --  Runs a restore

    verify_backup_history()                     --  Verifies if backup job exists in backup history page

    verify_restore_history()                    --  Verifies if restore job exists in restore history page

    tear_down()                                 --  Tear down method to cleanup the entities
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Database.DB2Utils.db2helper import DB2
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """ Command center: Backup and Restore History Check. """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "DB2 Backup and Restore History Check Test"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.dbtype = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.client_displayname = None
        self.jobs_page = None
        self.tcinputs = {
            "instance_name": None,
            "database_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "plan": None,
            "credential_name": None
        }

    def setup(self):
        """ Must needed setups for test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])

            self.navigator = self.admin_console.navigator
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.db_backupset = DB2Backupset(admin_console=self.admin_console)
            self.db_subclient = DB2Subclient(admin_console=self.admin_console)
            self.dbtype = DBInstances.Types.DB2
            self.jobs_page = Jobs(admin_console=self.admin_console)
            self.client_displayname = self.client.display_name
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case """

        self.prerequisite_setup_test_case()

        self.discover_database()

        self.refresh_commcell()
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs['database_name'])

        self.update_db2_client_machine_property()

        self.page_container.select_entities_tab()
        backup_job_id = self.run_backup()
        self.admin_console.refresh_page()
        self.page_container.select_overview_tab()
        restore_job_id = self.run_restore()

        self.navigate_db2_instance_details_page()

        self.verify_backup_history(backup_job_id)
        self.verify_restore_history(restore_job_id)
        self.cleanup()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.cleanup()
        self.db_instance.react_instances_table.reload_data()
        self.discover_instance()
        self.db_instance.react_instances_table.reload_data()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)

        self.db_instance_details.get_instance_details()
        if "windows" in self.client.os_info.lower():
            self.tcinputs["db2_username"] = self.client.display_name + "\\" + self.tcinputs["db2_username"]

        self.edit_instance_property()
        self.admin_console.refresh_page()

    @test_step
    def refresh_commcell(self):
        """ Refreshing Commcell object to refresh the properties after adding new properties. """
        self.commcell.refresh()

    @test_step
    def discover_instance(self):
        """
        Discover Instances
        """
        self.db_instance.discover_instances(database_engine=self.dbtype,
                                            server_name=self.client_displayname)
        self.refresh_commcell()
        self.admin_console.refresh_page()
        self.db_instance.react_instances_table.reload_data()

    @test_step
    def discover_database(self):
        """
        Discover database
        """
        if self.tcinputs["database_name"] not in self.db_instance_details.get_instance_entities():
            self.db_instance_details.discover_databases()
            self.admin_console.refresh_page()

    @test_step
    def edit_instance_property(self):
        """
        Changes DB2 instance properties.
        """
        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"],
                                                              credential_name=self.tcinputs["credential_name"])

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""

        instance = self.agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['database_name'])
        subclient = backupset.subclients.get('default')
        subclient.storage_policy = self.tcinputs["plan"]
        self.refresh_commcell()
        self.admin_console.refresh_page()

        db2_helper = DB2(commcell=self.commcell,
                         client=self.client,
                         instance=instance,
                         backupset=backupset)
        db2_helper.update_db2_database_configuration1()
        if "unix" in self.client.os_info.lower():
            db2_helper.db2_cold_backup(cold_backup_path="/dev/null",
                                       db_name=backupset.name)
        else:
            install_loc = self.client.install_directory
            db2_helper.db2_cold_backup(cold_backup_path="%s\\Base\\Temp" % install_loc,
                                       db_name=backupset.name)

    @test_step
    def navigate_db2_instance_details_page(self):
        """
        Navigates to instance details page
        """
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs['instance_name'],
                                         client_name=self.client_displayname)

    @test_step
    def run_backup(self):
        """Runs backup
            Raises:
                Exception:
                    If backup job fails
        """
        full_backup_job_id = self.db_backupset.db2_backup(subclient_name="default", backup_type="full")
        job = self.commcell.job_controller.get(full_backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Number: %s)", full_backup_job_id)
        job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2 with error: %s!" % job.delay_reason)

        common_utils = CommonUtils(self.commcell)
        common_utils.backup_validation(full_backup_job_id, "Full")

        return full_backup_job_id

    @test_step
    def run_restore(self):
        """Runs restore
            Raises:
                Exception:
                    If restore job fails
        """
        self.db_backupset.access_restore()
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.in_place_restore(endlogs=True)
        job = self.commcell.job_controller.get(restore_job_id)

        self.log.info("Waiting for Restore Job to Complete (Job Number: %s)", restore_job_id)
        job_status = job.wait_for_completion()

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client_displayname)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.log.info("Waiting for Jobs to Complete (Job Id: %s)", job_id)
            job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")
        return restore_job_id

    @test_step
    def verify_backup_history(self, backup_job_id):
        """Verifies backup job id on Backup History Page
            Args:
                backup_job_id               (int)               -- Backup Job Id

            Raises:
                Exception:
                    If backup job does not exist
        """
        self.db_instance_details.list_backup_history_of_entity(self.tcinputs['database_name'])
        job_exists = self.jobs_page.if_job_exists(backup_job_id)

        if job_exists:
            self.log.info("Backup Job Exists.")
            self.navigate_db2_instance_details_page()
        else:
            raise CVTestStepFailure("Backup Job does not exist.")

    @test_step
    def verify_restore_history(self, restore_job_id):
        """Verifies restore job id on Restore History Page
            Args:
                restore_job_id               (int)               -- Restore Job Id

            Raises:
                Exception:
                    If restore job does not exist
        """
        self.db_instance_details.list_restore_history_of_entity(self.tcinputs['database_name'])
        job_exists = self.jobs_page.if_job_exists(restore_job_id)

        if job_exists:
            self.log.info("Restore Job Exists.")
        else:
            raise CVTestStepFailure("Restore Job does not exist.")

    @test_step
    def delete_instance(self):
        """Deletes instance"""
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client_displayname):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)
            self.db_instance_details.delete_instance()
        else:
            self.log.info("Instance does not exists.")

    @test_step
    def cleanup(self):
        """Cleanup method for test case"""
        self.navigator.navigate_to_db_instances()
        self.delete_instance()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """

        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
