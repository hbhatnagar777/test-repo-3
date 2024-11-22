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
"59645": {
            "client_hostname": 	"172.16.xx.xxx",
            "client_username": "root",
            "client_password": "password",
            "instance_name": "db2inst1",
            "db2_username": "db2inst1",
            "db2_user_password": "Commvault",
            "database_name": "SAMPLE",
            "plan": "DB2TestPlan",
            "unix_group": "db2iadm1",
            "logs_path": "/opt",
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down method to cleanup the entities

    navigate_db2_backupset_page()               --  Navigates to backupset details page

    discover_instance()                         --  Discovers all the instances for client machine

    refresh_commcell()                          --  Refreshes commcell properties and get updated client's properties

    verify_db2_agent_installation()             --  Verifies if db2 agent was installed properly

    client_properties_verify()                  --  Verifies installation of db2 in client properties

    client_machine_verify()                     --  Verifies installation on client machine.

    edit_instance_property()                    --  Editing instance properties to add username and password

    update_db2_client_machine_property()        --  Updating DB2 logging properties on client

    run_backup()                                --  Runs a backup

    run_restore()                               --  Runs a restore

    cleanup()                                   -- Uninstalls the DB2 agent from client
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from Database.DB2Utils.db2helper import DB2
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ Command center: Installing DB2 agent on client machine. """

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "DB2 Agent Installation Test"
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
        self.client = None
        self.client_displayname = None
        self.servers = None
        self.tcinputs = {
            "client_hostname": None,
            "client_username": None,
            "client_password": None,
            "instance_name": None,
            "db2_username": None,
            "db2_user_password": None,
            "database_name": None,
            "plan": None,
            "unix_group": None,
            "logs_path": None
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

            self.servers = Servers(self.admin_console)

            self.prerequisite_setup_test_case()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case
            Raises:
                Exception:
                    If agent installation is unsuccessful
        """
        self.commcell.refresh()

        self.client_machine = Machine(machine_name=self.tcinputs["client_hostname"],
                                      commcell_object=self.commcell,
                                      username=self.tcinputs["client_username"],
                                      password=self.tcinputs["client_password"])
        if self.client_machine.os_info.lower() == "windows":
            self.tcinputs["db2_username"] = self.client_machine.ip_address + "/" + self.tcinputs["db2_username"]
            self.tcinputs["client_username"] = self.client_machine.ip_address + "\\" + self.tcinputs["client_username"]

        self.navigator.navigate_to_db_instances()

        add_server_job = self.db_instance.add_server(database_type=self.dbtype,
                                                     server_name=self.tcinputs["client_hostname"],
                                                     username=self.tcinputs["client_username"],
                                                     password=self.tcinputs["client_password"],
                                                     plan=self.tcinputs["plan"],
                                                     unix_group=self.tcinputs["unix_group"],
                                                     db2_log_path=self.tcinputs["logs_path"],
                                                     os_type=self.client_machine.os_info.lower())

        job = self.commcell.job_controller.get(add_server_job)
        self.log.info("Waiting for Agent Installation to Complete (Job Id: %s)", add_server_job)
        job_status = job.wait_for_completion()
        if job_status:
            self.commcell.refresh()
            self.client = self.commcell.clients.get(self.tcinputs['client_hostname'])
            self.client_displayname = self.client.display_name
            self.admin_console.refresh_page()

            if self.db_instance.is_instance_exists(database_type=self.dbtype,
                                                   instance_name=self.tcinputs["instance_name"],
                                                   client_name=self.client_displayname):
                self.db_instance.select_instance(database_type=self.dbtype,
                                                 instance_name=self.tcinputs["instance_name"],
                                                 client_name=self.client_displayname)
            else:
                self.discover_instance()
                self.refresh_commcell()
                self.admin_console.refresh_page()
                self.db_instance.select_instance(database_type=self.dbtype,
                                                 instance_name=self.tcinputs["instance_name"],
                                                 client_name=self.client_displayname)

            self.admin_console.wait_for_completion()
            self.edit_instance_property()

            self.admin_console.refresh_page()

            if self.tcinputs["database_name"] not in self.db_instance_details.get_instance_entities():
                self.db_instance_details.add_db2_database(database_name=self.tcinputs["database_name"],
                                                          plan=self.tcinputs["plan"])
                self.admin_console.refresh_page()

            self.refresh_commcell()

            self.verify_db2_agent_installation()
            self.update_db2_client_machine_property()

            self.navigate_db2_backupset_page()
            self.run_backup()

            self.navigator.navigate_to_db_instances()
            self.db_instance.select_instance(database_type=self.dbtype,
                                             instance_name=self.tcinputs["instance_name"],
                                             client_name=self.client_displayname)
            self.navigate_db2_backupset_page()

            self.run_restore()

        else:
            raise CVTestStepFailure("Agent installation job did not complete.")

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        all_clients = self.commcell.clients
        if all_clients.has_client(self.tcinputs["client_hostname"]):
            self.client_displayname = all_clients.get(self.tcinputs["client_hostname"]).display_name
            self.uninstall_client()

    @test_step
    def navigate_db2_backupset_page(self):
        """
        Takes to Backupset details page
        """
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])

    @test_step
    def discover_instance(self):
        """
        Discover Instances
        """
        self.db_instance.discover_instances(database_engine=self.dbtype,
                                            server_name=self.client_displayname)

    @test_step
    def verify_db2_agent_installation(self):
        """ This function is used for verification of agent installation.
            Raises:
                Exception:
                    If agent installation is not verified
        """
        if self.client_properties_verify() and self.client_machine_verify():
            pass
        else:
            raise CVTestStepFailure("Agent Installation could not be verified")

    @test_step
    def refresh_commcell(self):
        """ Refreshing Commcell object to refresh the properties"""
        self.commcell.refresh()
        self.client.refresh()

    @test_step
    def client_properties_verify(self):
        """ This function verifies the Client API to look for newly added client

                Returns:
                    bool - Boolean that represents whether client properties API verified or not
                    True - DB2 entry is present in client property
                    False - DB2 entry is not present in client property
        """
        ida_list = self.client.properties["client"]["idaList"]

        for ida in ida_list:
            if ida['idaEntity']['appName'] == 'DB2':
                return True
        return False

    @test_step
    def client_machine_verify(self):
        """
        This function verifies Client machine by running command and going through output.

        Returns:
            bool - Boolean that represents whether client machine verified the installation or not
            True - DB2 entry is present in client machine status
            False - DB2 entry is not present in client machine status
        Raises:
            Exception:
                If login is unsuccessful

        """
        if self.client_machine.os_info.lower() == "windows":
            qlogin = self.client_machine.execute_command("qlogin -cs %s -u %s -clp %s"
                                                         % (self.inputJSONnode['commcell']['webconsoleHostname'],
                                                            self.inputJSONnode['commcell']["commcellUsername"],
                                                            self.inputJSONnode['commcell']["commcellPassword"]))

            if "successfully" not in qlogin.output.lower():
                raise CVTestStepFailure(qlogin.output)
            command_op = self.client_machine.execute_command("qlist dataagent -c %s" % self.client_displayname)

        else:
            command_op = self.client_machine.execute_command("commvault status")

        if "db2" in command_op.output.lower():
            return True
        return False

    @test_step
    def edit_instance_property(self):
        """
        Changes DB2 instance properties.
        """
        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"])

    @test_step
    def update_db2_client_machine_property(self):
        """Edit db2 parameters on client to make them ready for backup"""

        agent = self.client.agents.get("DB2")
        instance = agent.instances.get(self.tcinputs['instance_name'])
        backupset = instance.backupsets.get(self.tcinputs['database_name'])

        db2_helper = DB2(commcell=self.commcell,
                         client=self.client,
                         instance=instance,
                         backupset=backupset)
        db2cmd = ""
        db2_helper.update_db2_database_configuration1()
        if "unix" in self.client.os_info.lower():
            db2_helper.db2_cold_backup(cold_backup_path="/dev/null",
                                       db_name=self.tcinputs["database_name"])
        else:
            db2cmd = " set-item -path env:DB2CLP -value **$$** ;"
            install_loc = self.client.install_directory
            db2_helper.db2_cold_backup(cold_backup_path="%s\\Base\\Temp" % install_loc,
                                       db_name=self.tcinputs["database_name"])
        db2_helper.third_party_command(cmd=f"{db2cmd} db2 deactivate db {self.tcinputs['database_name']}")
        db2_helper.third_party_command(cmd=f"{db2cmd} db2 activate db {self.tcinputs['database_name']}")

    @test_step
    def run_backup(self):
        """Runs backup
            Raises:
                Exception:
                    If backup job fails
        """
        self.db_backupset.access_subclient(subclient_name="default")
        full_backup_job_id = self.db_subclient.backup(backup_type=RBackup.BackupType.FULL)
        job = self.commcell.job_controller.get(full_backup_job_id)
        self.log.info("Waiting for Backup to Complete (Job Id: %s)", full_backup_job_id)
        job_status = job.wait_for_completion()

        if not job_status:
            raise CVTestStepFailure("Backup Job Failed for DB2!")
        common_utils = CommonUtils(self.commcell)
        common_utils.backup_validation(full_backup_job_id, "Full")

    @test_step
    def run_restore(self):
        """Runs restore
            Raises:
                Exception:
                    If restore job fails
        """
        self.db_subclient.access_restore()
        restore_job = self.db_subclient.restore_folders(database_type=self.dbtype, all_files=True)
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
    def uninstall_client(self):
        """
        Uninstalls client
             Raises:
                Exception:
                    If retire server job fails
        """
        self.navigator.navigate_to_servers()
        all_clients = self.commcell.clients
        if self.servers.is_client_exists(server_name=self.client_displayname, select_from_all_server=True):
            if not all_clients.get(self.tcinputs["client_hostname"]).properties['clientProps']['IsDeletedClient']:
                retire_server_job = self.servers.retire_server(server_name=self.client_displayname)
                job = self.commcell.job_controller.get(retire_server_job)
                self.log.info("Waiting for Retire Server to Complete (Job Id: %s)", retire_server_job)
                job_status = job.wait_for_completion()
                if not job_status:
                    raise CVTestStepFailure("Server Retire job did not complete.")
            self.admin_console.refresh_page()
            if self.servers.is_client_exists(server_name=self.client_displayname, select_from_all_server=True):
                self.servers.delete_server(server_name=self.client_displayname, select_from_all_server=True)

    def tear_down(self):
        """ Logout from all the objects and close the browser. """
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
