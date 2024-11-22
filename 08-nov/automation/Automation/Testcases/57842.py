# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

Inputs:

    client_group_name      -- name of the client group to install updates
"""



from cvpysdk.clientgroup import ClientGroup
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from Install.install_helper import InstallHelper
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.AdminConsolePages.maintenance import Maintenance
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper


class TestCase(CVTestCase):
    """Runs install updates job for the given client/ client group"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Install- Admin Console - Verify Install update Schedules"
        self.factory = None
        self.browser = None
        self.driver = None
        self.admin_console = None
        self.schedule_helper = None
        self.machine_objects = None
        self.deployment_helper = None
        self.maintenance = None
        self.tcinputs = {
            "client_group_name" : None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.admin_console = AdminConsole(self.browser,
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.maintenance = Maintenance(self.admin_console)
        self.admin_console.navigator.navigate_to_maintenance()
        install_helper = InstallHelper(self.commcell)
        self.machine_objects = install_helper.get_machine_objects()
        self.schedule_helper = ScheduleCreationHelper(self.commcell)
        self.deployment_helper = DeploymentHelper(self, self.admin_console)
        self.config_json = config.get_config()

    def run(self):
        """main function for executing testcase"""
        try:
            for machine in self.machine_objects:
                self.install_helper = InstallHelper(self.commcell, machine)
                if not self.commcell.clients.has_client(self.install_helper.client_host):
                    self.log.info("Creating {0} client".format(machine.os_info))
                    job = self.install_helper.install_software()
                    if not job.wait_for_completion():
                        raise Exception("{0} Client installation Failed".format(machine.os_info))
            self.commcell.clients.refresh()

            windows_client_obj = self.commcell.clients.get(
                self.config_json.Install.windows_client.machine_host)
            # creating new client group or add client to existing client group
            self.log.info("Creating client group")
            if not self.commcell.client_groups.has_clientgroup(clientgroup_name=self.tcinputs.get('client_group_name')):
                self.commcell.client_groups.add(
                    clientgroup_name=self.tcinputs.get('client_group_name'), clients=[
                        windows_client_obj.client_name])
            else:
                client_group = ClientGroup(self.commcell, clientgroup_name=self.tcinputs.get('client_group_name'))
                if windows_client_obj.client_name not in client_group.associated_clients:
                    client_group.add_clients(clients=[windows_client_obj.client_name])

            jobid = self.maintenance.run_install_updates(
                clients=[
                    self.commcell.clients.get(
                        self.install_helper.client_host).client_name], client_groups=[
                    self.tcinputs.get('client_group_name')])
            self.log.info("Job %s is started for update software", jobid)

            # To Check the Job status
            self.deployment_helper.check_job_status(jobid)
            self.log.info("install updates job completed successfully")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
