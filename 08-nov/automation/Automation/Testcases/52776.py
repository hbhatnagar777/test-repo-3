# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: Failover Group: Approval for DR Jobs testcase

TestCase: Class for executing this test case
Sample JSON: {
        "tenant_username": <username>,
        "tenant_password": <password>,
        'user_for_approval': "username",
        "failover_group_name": "group_1",
}
"""
from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.AdminConsole.DR.failover_groups import FailoverGroup
from AutomationUtils.mail_box import (MailBox, EmailSearchFilter)
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.LoginPage import LoginPage


class TestCase(CVTestCase):
    """This class is used to automate failover group Approval for DR Jobs Automation"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "Failover Group: Approval for DR Jobs testcase"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "user_for_approval": None,
            "failover_group_name": None
        }

        self.utils = None
        self.failover_group_name = None
        self.admin_console = None
        self.failover_group = None
        self.failover_group_obj = None
        self.config = None
        self.mailbox = None
        self.job_obj = None
        self.browser = None

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.failover_group = FailoverGroup(self.admin_console)
        self.failover_group_obj = self.commcell.failover_groups.get(self.failover_group_name)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.failover_group_name = self.tcinputs['failover_group_name']

            self.config = get_config()
            self.mailbox = MailBox(mail_server=self.config.email.server,
                                   username=self.config.email.username,
                                   password=self.config.email.password)

        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    def login_and_verfiy(self, links):
        """ login with email user and perform approval"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.browser.driver.get(links['here '])
        _admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'],
                                      self.config.email.username, self.config.email.password)
        LoginPage(_admin_console).login(self.config.email.username,
                                        self.config.email.password, stay_logged_in=True)
        _admin_console.wait_for_completion()
        _admin_console.select_radio(value="Yes")
        _admin_console.click_button(id='okButton')
        _admin_console.wait_for_completion()
        _admin_console.logout_silently(_admin_console)
        _admin_console.browser.close_silently(_admin_console.browser)

    @test_step
    def pre_validation(self):
        """ Validations before failover group approval"""
        self.login()

        self.log.info('check approval in group')
        if not self.failover_group_obj.is_approval_required:
            raise Exception("Approval is not set in failover group")

        self.log.info('check user in group')
        user_name = self.failover_group_obj.user_for_approval
        self.utils.assert_comparison(user_name, self.config.email.username)

        self.log.info('check vms sync status in group')
        vm_names = self.failover_group.get_column_details("Name", self.failover_group_name, navigate=True)
        sync_status = self.failover_group.get_column_details("Sync status", self.failover_group_name, navigate=False)
        for vm_index, vm_name in enumerate(vm_names):
            if sync_status[vm_index] not in ('In Sync', 'Sync Pending'):
                raise Exception(f"Sync Status expected : ['In Sync','Sync Pending']  not observed on VM {vm_name}"
                                f" with Sync status : {sync_status[vm_index]}")

    @test_step
    def perform_job(self):
        """Perform test boot job operation from failover group"""
        self.admin_console.refresh_page()
        self.log.info('Performing Test boot job')
        job_id = self.failover_group.run_testboot(self.failover_group_name)
        self.job_obj = self.commcell.job_controller.get(job_id)
        self.logout()

        sleep(5)
        self.log.info('check test boot job is running')
        self.utils.assert_comparison(self.job_obj.status, 'Running')

    @test_step
    def perform_approval_operation(self):
        """Performing  approval for the requested job"""
        sleep(30)
        self.mailbox.connect()
        search_query = EmailSearchFilter("Approval required for [Testboot]  operation")
        links = self.mailbox.get_mail_links(search_query)
        self.mailbox.disconnect()

        self.log.info("login with email user and perform approval")
        self.login_and_verfiy(links)

    @test_step
    def post_operation(self):
        """Perform post operation- check job completion"""
        self.log.info('Waiting for Job [%s] to complete', self.job_obj.job_id)
        self.job_obj.wait_for_completion()
        self.utils.assert_comparison(self.job_obj.status, 'Completed')
        self.log.info('Testboot job completed')

    def run(self):
        """Runs the testcase in order"""
        try:
            self.pre_validation()
            self.perform_job()
            self.perform_approval_operation()
            self.post_operation()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        try:
            self.logout()
        except Exception as _exception:
            self.log.error(_exception)
