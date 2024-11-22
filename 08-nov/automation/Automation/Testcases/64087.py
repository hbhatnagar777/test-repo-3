# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper
from Web.Common.exceptions import CVWebAutomationException
from AutomationUtils.options_selector import CVEntities
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.jobs_helper import JobsHelper
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from datetime import datetime


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.clientcompany = None
        self.entity_props = None
        self.entities = None
        self.company = None
        self.userhelper = None
        self.orghelper = None
        self.reseller_helper = None
        self.name = "Activity Control UI: Job management rights on different levels"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.tcinputs = {
            'ClientName': None
        }

    def create_subclient(self, clientname, storagepolicy):
        """
        Create subclient with given client and storagepolicy.
        Returns subclient properties dict.
        """
        subclient_pattern = {
            'subclient':
                {
                    'client': clientname,
                    'storagepolicy': storagepolicy,
                    'backupset': 'defaultBackupSet',
                    'agent': "File system",
                    'instance': "defaultinstancename",
                }
        }
        try:
            return self.entities.create(subclient_pattern)['subclient']
        except Exception as e:
            self.log.info(e)

    def start_job(self):
        """ Starts a backup job"""
        bkp_job = self.subclient.backup("Full")
        bkp_job.pause(True)
        self.job = bkp_job.job_id
        self.log.info(f"Job {self.job} started on subclient {self.subclient.subclient_name}")

    @test_step
    def setup_company(self):
        """Creates a company and adds the given client to it."""
        self.company = 'Company' + datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.orghelper.create(self.company, company_alias=self.company)
        ta_name = f'tenantadmin'
        self.userhelper.create_user(f'{self.company}\\{ta_name}',
                                    email=f'{ta_name}@{self.company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.company + '\\Tenant Admin'])
        tu_name = f'tenantuser'
        sec_dict = {
                    'asso1': {
                        'clientName': [self.tcinputs['ClientName']],
                        'role': ['View']
                    }
                    }
        self.userhelper.create_user(f'{self.company}\\{tu_name}',
                                    email=f'{tu_name}@{self.company}.com',
                                    password=self.inputJSONnode['commcell']['commcellPassword'],
                                    local_usergroups=[self.company + '\\Tenant Users'],
                                    security_dict=sec_dict)
        self.client.change_company_for_client(self.company)
        self.log.info(f"Client {self.tcinputs['ClientName']} is migrated to {self.company}")

    def setup(self):
        """sets up all the required modules"""
        self.userhelper = UserHelper(self.commcell)
        self.orghelper = OrganizationHelper(self.commcell)
        self.clientcompany = self.client.company_name if self.client.company_name else "Commcell"
        self.setup_company()
        self.entities = CVEntities(self)
        self.entity_props = self.entities.create(["disklibrary", "storagepolicy"])
        self.subclient = self.create_subclient(self.tcinputs["ClientName"],
                                                self.entity_props["storagepolicy"]["name"])['object']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                 password=self.inputJSONnode['commcell']['commcellPassword'])
        self.file_servers = FileServers(self.admin_console)
        self.rpanelinfo = RPanelInfo(self.admin_console)
        self.rmodaldialog = RModalDialog(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.alert = Alert(self.admin_console)
        self.jobshelper = JobsHelper(self.admin_console)


    def toggle_button(self, operation, hasJobManagementRights):
        """operations can be Data_Backup or Data_Restore"""
        prev_state = "enable" if self.rpanelinfo.is_toggle_enabled(label=self.admin_console.props[operation]) else "disable"
        if prev_state == "enable":
            # if enabled now, disabling it
            self.rpanelinfo.disable_toggle(label=self.admin_console.props[operation])
            if operation == "Data_Backup":
                self.rmodaldialog.click_submit()
        else:
            # if disabled now, enabling it
            self.rpanelinfo.enable_toggle(label=self.admin_console.props[operation])

        error_raised = 0
        try:
            self.admin_console.check_error_message()
        except CVWebAutomationException as exp:
            if not hasJobManagementRights:
                if 'does not have required capability [Agent Management/Job Management] ' in exp.args[0] or \
                        'No permission to set activity control' in exp.args[0]:
                    error_raised = 1
                    self.log.info(f"User without job management rights is "
                                  f"getting an exception to disable {operation.replace('_',' ')}.")
                    self.log.info("Working as expected")

        if not hasJobManagementRights:
            if not error_raised:
                raise CVWebAutomationException("User without rights can modify the job, invalid behaviour")

        self.log.info(f"setting the {operation} to its previous state")
        if hasJobManagementRights:
            if prev_state == "disable":
                self.rpanelinfo.disable_toggle(label=self.admin_console.props[operation])
                if operation == "Data_Backup":
                    self.rmodaldialog.click_submit()
            else:
                self.rpanelinfo.enable_toggle(label=self.admin_console.props[operation])
    @test_step
    def start_test(self, hasJobManagementRights):
        """runs the testcase"""
        self.log.info("Validating toggle button at Servers page.")
        self.admin_console.navigator.navigate_to_servers()
        self.rtable.view_by_title("All")
        self.rtable.access_link(self.tcinputs["ClientName"])
        self.admin_console.select_configuration_tab()
        self.toggle_button("Data_Backup", hasJobManagementRights)
        self.log.info("Successfully validated toggle button at Servers page.")
        self.log.info("Validating toggle button at file servers agent page.")
        self.toggle_button("Data_Restore", hasJobManagementRights)
        self.admin_console.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")
        self.file_servers.access_server(self.tcinputs["ClientName"])
        self.admin_console.select_configuration_tab()
        self.toggle_button("Data_Backup", hasJobManagementRights)
        self.toggle_button("Data_Restore", hasJobManagementRights)
        self.log.info("Successfully validated toggle button at file servers agent page.")
        self.log.info("Validating toggle button at subclient details page.")
        self.admin_console.access_tab(self.admin_console.props['header.subclients'])
        self.rtable.access_link(self.subclient.name)
        self.alert.close_popup()
        self.toggle_button("Data_Backup", hasJobManagementRights)
        self.log.info("Successfully validated toggle button at subclient details page.")
        self.start_job()
        raised_exp = 0
        try:
            self.jobshelper.resume_and_validate(self.job)
        except Exception as exp:
            if not hasJobManagementRights:
                raised_exp = 1
                self.log.info(exp)
                self.log.info("Getting exception when the user doesnt have JM rights, working as expected.")
        if not hasJobManagementRights:
            if not raised_exp:
                raise CVWebAutomationException("User without rights can modify the job, invalid behaviour")
        self.commcell.job_controller.get(self.job).kill(True)

    def run(self):
        try:
            AdminConsole.logout_silently(self.admin_console)
            self.log.info(f"starting test step as tenantadmin@{self.company}.com")
            self.admin_console.login(f'tenantadmin@{self.company}.com',
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.start_test(hasJobManagementRights=True)
            AdminConsole.logout_silently(self.admin_console)
            self.log.info(f"starting test step as tenantuser@{self.company}.com")
            self.admin_console.login(f'tenantuser@{self.company}.com',
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.start_test(hasJobManagementRights=False)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.client.change_company_for_client(self.clientcompany)
            self.log.info(f"Client {self.tcinputs['ClientName']} is migrated back to  {self.clientcompany}")
            self.log.info('Deleting company {0}'.format(self.company))
            self.commcell.organizations.delete(self.company)
        finally:
            self.entities.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
