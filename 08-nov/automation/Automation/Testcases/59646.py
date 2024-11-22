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
"59646": {
            "ClientName": "test_client",
            "AgentName": "DB2",
            "instance_name": "db2inst1",
            "db2_username": "db2inst1",
            "db2_user_password": "Commvault",
            "database_name": "SAMPLE",
            "plan": "DB2TestPlan",
            "credential_name": "cred_name"
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down method to cleanup the entities

    refresh_commcell()                          --  Refreshes commcell properties and get updated client's properties

    edit_instance_property()                    --  Editing instance properties to add username and password

    verify_database_tab()                       --  Verifies if database present on databases tab

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    run_backup()                                --  Runs a backup

    cleanup()                                   --  Deletes the backupset
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Database.DB2Utils.db2helper import DB2
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """ Command center: Adding database in DB2 instance. """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "DB2 Add Database Test"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.client_displayname = None
        self.dbtype = None
        self.tcinputs = {
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "database_name": None,
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
            self.client_displayname = self.client.display_name
            self.dbtype = DBInstances.Types.DB2
            self.page_container = PageContainer(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case """

        self.prerequisite_setup_test_case()

        self.add_database()

        self.navigator.navigate_to_db_instances()

        self.verify_database_tab()

        self.db_instance.select_database_from_databases_tab(database_type=self.dbtype,
                                                            database_name=self.tcinputs['database_name'],
                                                            client_name=self.client_displayname)

        self.refresh_commcell()
        self.update_db2_client_machine_property()
        self.page_container.select_entities_tab()
        self.run_backup()

        self.cleanup()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.navigator.navigate_to_db_instances()
        self.delete_instance()

        self.db_instance.react_instances_table.reload_data()

        self.discover_instance()
        self.admin_console.refresh_page()

        self.db_instance.react_instances_table.reload_data()

        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["instance_name"],
                                         client_name=self.client_displayname)
        if "windows" in self.client.os_info.lower():
            self.tcinputs["db2_username"] = self.client.display_name + "\\" + self.tcinputs["db2_username"]

        self.edit_instance_property()
        self.admin_console.refresh_page()
        self.delete_database()

    @test_step
    def add_database(self):
        """
        Adds database if does not exist
        """

        try:
            self.admin_console.refresh_page()
            if self.tcinputs["database_name"] not in self.db_instance_details.get_instance_entities():
                self.db_instance_details.add_db2_database(database_name=self.tcinputs["database_name"],
                                                          plan=self.tcinputs["plan"])
                self.admin_console.refresh_page()
        except Exception as exp:
            self.log.info("Backupset exists")

    @test_step
    def delete_database(self):
        """
        Deletes database if it exists
        """
        self.refresh_commcell()
        self.admin_console.refresh_page()
        if self.tcinputs["database_name"] in self.db_instance_details.get_instance_entities():
            self.db_instance_details.delete_entity(self.tcinputs["database_name"])
        self.admin_console.refresh_page()
        self.refresh_commcell()

    @test_step
    def refresh_commcell(self):
        """ Refreshing Commcell object to refresh the properties after adding the server. """
        self.commcell.refresh()

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

    @test_step
    def edit_instance_property(self):
        """
        Changes DB2 instance configurations.
        """

        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"],
                                                              credential_name=self.tcinputs["credential_name"])

    @test_step
    def verify_database_tab(self):
        """
        Verifies database in database tab using client name and instance name
        Raises:
            Exception:
                If database is not listed in database tab
        """
        self.db_instance.access_databases_tab()
        if not self.db_instance.is_database_exists(database_type=self.dbtype,
                                                   client_name=self.client_displayname,
                                                   database_name=self.tcinputs['database_name']):
            raise CVTestStepFailure("Database not available in Database Tab")

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
        full_backup_job_id = self.db_backupset.db2_backup(subclient_name="default", backup_type="full")
        job = self.commcell.job_controller.get(full_backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Number: %s)", full_backup_job_id)
        job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")

        common_utils = CommonUtils(self.commcell)
        common_utils.backup_validation(full_backup_job_id, "Full")

    @test_step
    def delete_instance(self):
        """Deletes instance if exists"""
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
        self.db_backupset.delete_backupset()
        self.navigator.navigate_to_db_instances()
        self.delete_instance()

    def tear_down(self):
        """ Logout from all the objects and close the browser. """

        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
