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
"71201": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "instance_name": "db2inst1",
            "db2_username": "db2inst1",
            "db2_user_password": "test",
            "database_name": "SAMPLE",
            "plan": "BackupPlan",
            "home_path": "/home/db2inst1",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
     __init__()                                 --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    refresh_commcell()                          --  Refreshes commcell properties and get updated client's properties

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    run_backup()                                --  Runs a backup

    run_restore()                               --  Runs a restore

    verify_backup_job_client_machine()          --  Verifies backup job on client machine

    tear_down()                                 --  Tear down method to cleanup the entities

    cleanup()                                   --  Deletes backupset and instance
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Database.DB2Utils.db2helper import DB2
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """ Command center: Add/Delete Instance and Backupset """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "DB2 Command Center verify backup and restore for password-less setups"
        self.dbtype = None
        self.browser = None
        self.browser_driver = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.client_machine = None
        self.db2_helper = None
        self.client_displayname = None
        self.page_container = None
        self.servers = None
        self.tcinputs = {
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "database_name": None,
            "plan": None,
            "home_path": None,
            "credential_name": None
        }

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.browser_driver = self.browser.driver
            self.admin_console = AdminConsole(self.browser,
                                              self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])

            self.navigator = self.admin_console.navigator
            self.dbtype = DBInstances.Types.DB2
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.db_backupset = DB2Backupset(admin_console=self.admin_console)
            self.db_subclient = DB2Subclient(admin_console=self.admin_console)
            self.client_displayname = self.client.display_name
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case """
        self.prerequisite_setup_test_case()
        self.add_instance()
        self.delete_database()
        self.add_backupset()
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])
        self.refresh_commcell()
        self.update_db2_client_machine_property()

        self.run_backup()
        self.admin_console.refresh_page()
        time.sleep(10)
        self.page_container.select_overview_tab()
        self.run_restore()

        self.permit_empty_passwords()
        self.delete_password_for_instance()
        self.edit_credential()
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])

        self.run_backup()
        self.admin_console.refresh_page()
        time.sleep(10)
        self.page_container.select_overview_tab()
        self.run_restore()

        self.cleanup()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.navigator.navigate_to_db_instances()
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client_displayname):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)
            self.admin_console.wait_for_completion()
            self.delete_instance()

    @test_step
    def permit_empty_passwords(self):
        """ Modifies the sshd_config file to Permit Empty Passwords """
        self.reset_empty_password_permissions()
        append_cmd = "echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config"
        self.db2_helper.machine_object.execute_command(append_cmd)

    @test_step
    def reset_empty_password_permissions(self):
        """ Resets the sshd_config file """
        reset_cmd = ("grep -v -x 'PermitEmptyPasswords yes' /etc/ssh/sshd_config > temp_config && mv -f temp_config "
                     "/etc/ssh/sshd_config")
        self.db2_helper.machine_object.execute_command(reset_cmd)

    @test_step
    def delete_password_for_instance(self):
        """Deletes the password of instance (DB2 Instance Password-Less configuration)"""
        if "windows" in self.client.os_info.lower():
            raise Exception("Password-Less configuration is only supported for linux clients")
        else:
            command = f"passwd -d {self.tcinputs['instance_name']}"
            self.db2_helper.machine_object.execute(command)

    @test_step
    def add_instance(self):
        """ Adding instance """

        self.db_instance.add_db2_instance(server_name=self.client_displayname,
                                          plan=self.tcinputs["plan"],
                                          instance_name=self.tcinputs["instance_name"],
                                          db2_home=self.tcinputs["home_path"],
                                          db2_username=self.tcinputs["db2_username"],
                                          db2_user_password=self.tcinputs["db2_user_password"],
                                          credential_name=self.tcinputs["credential_name"])
        self.refresh_commcell()
        self.admin_console.refresh_page()

    @test_step
    def add_backupset(self):
        """ Adding database """
        self.refresh_commcell()
        self.admin_console.refresh_page()
        if self.tcinputs["database_name"] not in self.db_instance_details.get_instance_entities():
            self.db_instance_details.add_db2_database(database_name=self.tcinputs["database_name"],
                                                      plan=self.tcinputs["plan"])

    @test_step
    def edit_credential(self):
        """Edits the credential from instance page"""
        self.navigator.navigate_to_db_instances()
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client_displayname):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)

        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password="",
                                                              plan=self.tcinputs["plan"],
                                                              credential_name=self.tcinputs["credential_name"])

    @test_step
    def refresh_commcell(self):
        """ Refreshing Commcell object to refresh the properties"""
        self.commcell.refresh()

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""
        self.initialize_db2helper_object()
        self.db2_helper.update_db2_database_configuration1()
        if "unix" in self.client.os_info.lower():
            self.db2_helper.db2_cold_backup(cold_backup_path="/dev/null",
                                            db_name=self.tcinputs["database_name"])
        else:
            install_loc = self.client.install_directory
            self.db2_helper.db2_cold_backup(cold_backup_path="%s\\Base\\Temp" % install_loc,
                                            db_name=self.tcinputs["database_name"])

    @test_step
    def initialize_db2helper_object(self):
        """Initializes the DB2 Helper Object"""
        instance = self.agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['database_name'])

        self.db2_helper = DB2(commcell=self.commcell,
                              client=self.client,
                              instance=instance,
                              backupset=backupset)

    @test_step
    def run_backup(self, backup_type="Full"):
        """Runs backup
            Args:
                backup_type               (str)               -- Type of backup default: Full

            Raises:
                Exception:
                    If backup job fails
        """
        self.page_container.select_entities_tab()
        self.admin_console.wait_for_completion()
        backup_job_id = self.db_backupset.db2_backup(subclient_name="default", backup_type=backup_type.lower())
        job = self.commcell.job_controller.get(backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Id: %s)", backup_job_id)
        job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")
        self.initialize_db2helper_object()
        self.verify_backup_job_client_machine(job, backup_type)

    @test_step
    def verify_backup_job_client_machine(self, job, backup_type):
        """Verifies backup job
            Args:
                job                     (Job)               -- Object of Job class

                backup_type            (str)                -- Type of backup job

            Raises:
                Exception:
                    If Data backup job of backup type expected is not present
        """
        timestamp = self.db2_helper.get_backup_time_stamp_and_streams(job.job_id)[0]
        cmd = "db2 list backup since {} for db {}".format(timestamp, self.tcinputs['database_name'])
        if "unix" in self.client.os_info.lower():
            backup_history = self.db2_helper.third_party_command(cmd)
        else:
            cmd = "set-item -path env:DB2CLP -value **$$** ; {}".format(cmd)
            backup_history = self.db2_helper.third_party_command(cmd)

        output = " ".join([output for line in backup_history for output in line]).lower()
        output = ' ' + ' '.join(output.split())

        key = " n "
        if backup_type.lower() == "incremental":
            key = " o "
        elif backup_type.lower() == "differential":
            key = " e "

        if " b " not in output and \
                key not in output and \
                "backup {} online".format(self.tcinputs['database_name'].lower()) not in output:
            raise CVTestStepFailure("Backup Job was not {}!".format(backup_type.lower()))

        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(job.job_id, backup_type)

    @test_step
    def run_restore(self):
        """Runs restore
            Raises:
                Exception:
                    If Restore Job Fails
        """
        self.db2_helper.disconnect_applications()
        self.db_backupset.access_restore()
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        restore_job_id = restore_job.in_place_restore(endlogs=True)
        job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Waiting for Restore Job to Complete (Job Id: %s)", restore_job_id)
        job_status = job.wait_for_completion()

        all_jobs = self.commcell.job_controller.active_jobs(client_name=self.client_displayname)
        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)
            self.log.info("Waiting for Jobs to Complete (Job Id: %s)", job_id)
            job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")

    @test_step
    def delete_database(self):
        """
        Deletes database if it exists
        """
        self.refresh_commcell()
        self.admin_console.refresh_page()
        if self.tcinputs["database_name"] in self.db_instance_details.get_instance_entities():
            self.db_instance_details.delete_entity(self.tcinputs["database_name"])

    @test_step
    def delete_instance(self):
        """Deletes instance"""
        self.db_instance_details.delete_instance()

    @test_step
    def cleanup(self):
        """Cleanup method for test case"""
        self.db2_helper.modify_db2_instance_password(self.tcinputs["db2_user_password"])
        self.db2_helper.reset_empty_password_permissions()
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs['instance_name'],
                                         client_name=self.client_displayname)
        self.delete_database()
        self.delete_instance()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """

        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
