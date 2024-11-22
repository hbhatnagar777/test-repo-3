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
"60623": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "Instance_Name": "dummy_inst",
            "Backupset_Name": "SAMPLE",
            "db2_username": "dummy_user",
            "db2_user_password": "test_passwd",
            "home_path": "/home/dummy_inst",
            "plan_name": "plan name",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down method to cleanup the entities

    prerequisite_setup_test_case()              --  Deleting already created instance and setup entities for test case

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    run_full_backup()                           --  Runs a full backup

    run_aux_copy()                              --  Runs an aux copy job

    run_restore()                               --  Runs a restore

    stop_primary_ma_services()                  -- Stops Media Agent services

    start_primary_ma_services()                 -- Starts Media Agent services

    verify_logs()                               --  Verifies copyPrecedence from DB2SBT logs on client

    delete_instance()                           --  Deletes instance

    cleanup()                                   -- Uninstalls the DB2 agent from client
"""


import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Database.DB2Utils.db2helper import DB2
from cvpysdk.policies.storage_policies import StoragePolicies
from Web.AdminConsole.Components.page_container import PageContainer

class TestCase(CVTestCase):
    """ Command center: Verifying Copy Precedence for restores. """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "DB2 restore Copy Precedence check."
        self.dbtype = None
        self.browser = None
        self.browser_driver = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.client_displayname = None
        self.client_conn = None
        self.primary_copy = None
        self.secondary_copy = None
        self.storage_policy = None
        self.media_agent = None
        self.media_agent_client = None
        self.media_agent_client_conn = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "Instance_Name": None,
            "Backupset_Name": None,
            "db2_username": None,
            "db2_user_password": None,
            "home_path": None,
            "plan_name": None,
            "credential_name": None
        }

    def setup(self):
        """ Initial configuration for the test case.

            Raises:
                Exception:
                    If test case initialization is failed.
        """

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

            storage_policies = StoragePolicies(self.commcell)
            self.storage_policy = storage_policies.get(self.tcinputs["plan_name"])
            self.client_displayname = self.client.display_name

            self.client_conn = Machine(machine_name=self.client)
            copies = [copy for copy in list(self.storage_policy.copies.keys()) if "snap" not in copy.lower()]
            self.primary_copy = copies[0]
            self.secondary_copy = copies[1]
            self.media_agent = self.storage_policy.get_copy(self.primary_copy).media_agent
            self.media_agent_client = self.commcell.clients.get(self.media_agent)
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case """
        try:
            self.prerequisite_setup_test_case()

            self.add_instance()
            self.commcell.refresh()
            self.admin_console.refresh_page()
            self.discover_database()

            self.commcell.refresh()

            self.update_db2_client_machine_property()

            backup_job_id = self.run_full_backup()

            self.log.info("Waiting for Aux copy Job to run as scheduled.")
            self.run_aux_copy(backup_job_id)

            self.stop_primary_ma_services()

            self.admin_console.refresh_page()

            self.page_container.select_overview_tab()
            self.run_restore()

            self.cleanup()
        
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.start_primary_ma_services()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.media_agent_client_conn = Machine(machine_name=self.media_agent_client.client_hostname,
                                               commcell_object=self.commcell)
        self.start_primary_ma_services()
        self.navigator.navigate_to_db_instances()
        self.delete_instance()
        self.db_instance.react_instances_table.reload_data()
        self.log.info("OS: %s" % self.client.os_info.lower())
        if "windows" in self.client.os_info.lower():
            self.tcinputs["db2_username"] = self.client.display_name + "\\" + self.tcinputs["db2_username"]

    @test_step
    def add_instance(self):
        """ Adding instance """

        self.db_instance.add_db2_instance(server_name=self.client_displayname,
                                          plan=self.tcinputs["plan_name"],
                                          instance_name=self.tcinputs["Instance_Name"],
                                          db2_home=self.tcinputs["home_path"],
                                          db2_username=self.tcinputs["db2_username"],
                                          db2_user_password=self.tcinputs["db2_user_password"],
                                          credential_name=self.tcinputs["credential_name"])

    @test_step
    def discover_database(self):
        """ Discover database """

        self.db_instance_details.discover_databases()
        self.commcell.refresh()
        self.admin_console.refresh_page()

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""

        instance = self.agent.instances.get(self.tcinputs['Instance_Name'])
        backupset = instance.backupsets.get(self.tcinputs['Backupset_Name'])

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
    def run_full_backup(self):
        """ Runs full backup
            Returns:
                (str) -- Backup Job Id

            Raises:
                Exception:
                    If full backup is unsuccessful
         """

        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["Backupset_Name"])
        self.page_container.select_entities_tab()
        backup_job_id = self.db_backupset.db2_backup(subclient_name="default", backup_type="full")
        job = self.commcell.job_controller.get(backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Id: %s)", backup_job_id)
        job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")
        return backup_job_id

    @test_step
    def run_aux_copy(self, backup_job_id):
        """ Running aux copy scheduled job
            Args:
            backup_job_id (str):   Full Backup Job ID

            Raises:
                Exception:
                    If aux copy is unsuccessful
        """

        plan_aux_job = 0
        attempts = 0
        while (not plan_aux_job) and (attempts <= 10):
            time.sleep(3 * 60)
            aux_copy_jobs = self.commcell.job_controller.all_jobs(lookup_time=0.05,
                                                                  job_filter="104")
            for aux_job in aux_copy_jobs:
                if int(aux_job) > int(backup_job_id):
                    job = self.commcell.job_controller.get(aux_job)
                    job_details = job.details["jobDetail"]

                    if job_details["generalInfo"]["storagePolicy"]["storagePolicyName"] == self.tcinputs["plan_name"]:
                        plan_aux_job = job
                        break

            attempts += 1

        if not plan_aux_job:
            plan_aux_job = self.storage_policy.run_aux_copy(storage_policy_copy_name=self.secondary_copy,
                                                            all_copies=False)

        self.log.info("Waiting for Aux Copy Job %s to finish.", plan_aux_job.job_id)

        job_status = plan_aux_job.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure("Aux Copy Job %s Failed!." % plan_aux_job.job_id)

    @test_step
    def stop_primary_ma_services(self):
        """Stop Primary MA services"""
        if "windows" in self.media_agent_client.os_info.lower():
            client_instance = self.media_agent_client.instance
            service_name = 'GxMMM({})'.format(client_instance)
            self.commcell.clients.get(self.media_agent).stop_service(service_name)
        else:
            self.media_agent_client_conn.kill_process(
                process_id=self.media_agent_client_conn.get_process_id(
                    process_name=f'{self.media_agent_client.install_directory}/MediaAgent/CvMountd')[0])

    @test_step
    def start_primary_ma_services(self):
        """Start Primary MA services"""
        if "windows" in self.media_agent_client.os_info.lower():
            client_instance = self.media_agent_client.instance
            service_name = 'GxMMM({})'.format(client_instance)
            self.commcell.clients.get(self.media_agent).start_service(service_name)
        else:
            self.media_agent_client_conn.start_all_cv_services()

    @test_step
    def run_restore(self):
        """ Run restore

            Raises:
                Exception:
                    If restore is unsuccessful
        """
        self.db_backupset.access_restore()
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype,
                                                        all_files=True,
                                                        copy=self.secondary_copy)
        restore_job_id = restore_job.in_place_restore(endlogs=True)
        job = self.commcell.job_controller.get(restore_job_id)
        self.log.info("Waiting for Restore Job to Complete (Job Id: %s)", restore_job_id)
        job_status = job.wait_for_completion()

        all_jobs = self.commcell.job_controller.all_jobs(client_name=self.client_displayname)

        for job_id in all_jobs:
            job = self.commcell.job_controller.get(job_id)

            if job.status.lower() != "completed":
                self.log.info("Waiting for Jobs to Complete (Job Id: %s)", str(job_id))
                job_status = job.wait_for_completion()
            if job_status:
                if "application" in all_jobs[job_id]["operation"].lower() and \
                        "restore" in all_jobs[job_id]["operation"].lower():
                    self.log.info("Verifying Copy Precedence for Job %s", str(job_id))
                    self.verify_logs(str(job_id))

        if not job_status:
            raise CVTestStepFailure("Restore Job Failed for DB2!")

    @test_step
    def verify_logs(self, job_id):
        """Verify copy precedence in logs
            job_id  (str): Command Line Restore Job ID.

            Raises:
                Exception:
                    If expected copy precedence is not found in logs.
        """
        copy_precedence = self.storage_policy.get_copy_precedence(self.secondary_copy)

        log_lines = self.client_conn.get_logs_for_job_from_file(job_id=job_id,
                                                                log_file_name="DB2SBT.log",
                                                                search_term="copyPrec="+str(copy_precedence))

        if len(log_lines.strip()) == 0:
            raise CVTestStepFailure("Cannot Verify Copy Precedence.")

    @test_step
    def delete_instance(self):
        """Deletes instance"""
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["Instance_Name"],
                                               client_name=self.client_displayname):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["Instance_Name"],
                                             client_name=self.client_displayname)
            self.db_instance_details.delete_instance()
        else:
            self.log.info("Instance does not exists.")

    @test_step
    def cleanup(self):
        """ Cleanup method for test case """
        self.navigator.navigate_to_databases()
        self.delete_instance()

        self.start_primary_ma_services()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
