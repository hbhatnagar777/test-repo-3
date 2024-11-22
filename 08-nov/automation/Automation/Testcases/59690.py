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
"59689": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "InstanceName": "db2inst1",
            "BackupsetName": "SAMPLE",
            "plan": "BackupPlan",
            "ClientName" : "Client name",
            "AgentName": "database agent",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    refresh_commcell()                          --  Refreshes commcell properties and get updated client's properties

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    run_backup()                                --  Runs a backup

    verify_job_phases()                         --  Verifies backup job phases on DB2 machine

    tear_down()                                 --  Tear down method to cleanup the entities

    cleanup()                                   --  Deletes the subclient
"""

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
    """ Command center: Adding logs backup subclient in Backupset Details Page. """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "DB2 Add subclient Logs backup Test"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.client_displayname = None
        self.db2_helper = None
        self.dbtype = None
        self.tcinputs = {
            "instance_name": None,
            "database_name": None,
            "plan": None,
            "db2_username": None,
            "db2_user_password": None,
            "credential_name": None,
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
            self.client_displayname = self.client.display_name
            self.dbtype = DBInstances.Types.DB2
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case
            Raises:
                Exception:
                    If database is not present for that instance
        """
        self.prerequisite_setup_test_case()

        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])
        self.add_subclient()

        self.refresh_commcell()

        self.update_db2_client_machine_property()

        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])
        self.page_container.select_entities_tab()
        self.run_backup()

        self.cleanup()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.navigator.navigate_to_db_instances()

        self.delete_instance()

        self.discover_instance()

        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)

        if "windows" in self.client.os_info.lower():
            self.tcinputs["db2_username"] = self.client.display_name + "\\" + self.tcinputs["db2_username"]

        self.edit_instance_property()
        self.discover_database()

    @test_step
    def discover_instance(self):
        """
        Discover Instances if not exist already
        """
        if not self.db_instance.is_instance_exists(database_type=self.dbtype,
                                                   instance_name=self.tcinputs["instance_name"],
                                                   client_name=self.client_displayname):
            self.db_instance.discover_instances(database_engine=self.dbtype,
                                                server_name=self.client_displayname)
            self.refresh_commcell()
            self.admin_console.refresh_page()
            self.db_instance.react_instances_table.reload_data()

    @test_step
    def edit_instance_property(self):
        """
        Changes DB2 instance properties.
        """
        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"],
                                                              credential_name=self.tcinputs["credential_name"])
        self.refresh_commcell()
        self.admin_console.refresh_page()

    @test_step
    def discover_database(self):
        """
        Discover database if does not exist
        """
        self.db_instance_details.discover_databases()
        self.refresh_commcell()
        self.admin_console.refresh_page()

    @test_step
    def add_subclient(self):
        """
        Creates subclient if does not exist
        """
        if self.id not in self.db_backupset.list_subclients():
            self.db_backupset.add_db2_subclient(subclient_name=self.id,
                                                plan=self.tcinputs["plan"],
                                                data_backup=False,
                                                backup_logs=True)

    @test_step
    def refresh_commcell(self):
        """ Refreshing Commcell object to refresh the properties after adding new properties. """
        self.commcell.refresh()

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""

        instance = self.agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['database_name'])

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
    def run_backup(self):
        """Runs backup
            Raises:
                Exception:
                    If backup job fails
        """

        full_backup_job_id = self.db_backupset.db2_backup(subclient_name=self.id,
                                                          backup_type="full")

        job = self.commcell.job_controller.get(int(full_backup_job_id))
        self.log.info("Waiting for Backup to Complete (Job Id: %s)", full_backup_job_id)
        job_status = job.is_finished
        phases = []
        prev_phase = ""
        while not job_status:
            curr_phase = job.phase
            job_status = job.is_finished
            if curr_phase != prev_phase and curr_phase is not None:
                phases.append(curr_phase.split()[0].lower())
                prev_phase = curr_phase

        job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")
        self.verify_job_phases(job, phases)

    @test_step
    def verify_job_phases(self, job, phases):
        """Verifies backup job
            Args:
                job               (Job)               -- Object of Job class

                phases            (list)              -- List of phases in backup job

            Raises:
                Exception:
                    If Data backup phase exists
        """

        if "data" in phases:
            raise CVTestStepFailure("Data Backup Phase also exists!")

        commonutils = CommonUtils(self.commcell)
        commonutils.backup_validation(job.job_id, "Full")

    @test_step
    def delete_instance(self):
        """Deletes instance if exists"""
        if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                               instance_name=self.tcinputs["instance_name"],
                                               client_name=self.client_displayname):
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)
            self.admin_console.wait_for_completion()
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
