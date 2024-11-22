# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase is the only class defined in this file.
"""

from cvpysdk.subclients.exchange.usermailbox_subclient import UsermailboxSubclient

from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.windows_machine import WindowsMachine
from Application.Exchange.ExchangeMailbox.constants import CHECK_SERVICE_ACCOUNT_PERMISSIONS
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """
    Class for executing check for Office 365 app basic coverage
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = 'Exchange office365 APP basic coverage'
        self.admin_console = None
        self.browser = None
        self.navigator = None
        self.o365_apps = None
        self.windows_machine = None
        self.client = None
        self.client_name = None
        self.exchange_mailbox = None
        self.proxy_name = None

        # defaults for new clients
        self.agent_name = 'Exchange Mailbox'
        self.instance_name = 'defaultInstanceName'
        self.backupset_name = 'User Mailbox'
        self.subclient_name = 'usermailbox'
        self.ex_powershell = None
        self.tcinputs = {
            'ServerPlan': None,
            'IndexServer': None,
            'AccessNode': None,
            "ProxyServers": None,
            "ServiceAccountDetails": None
        }

    @staticmethod
    def format_output(data):
        """Function for formatting output from powershell"""
        data = data.replace('\r', '').splitlines()

        ex_result = data[-1]
        message = '\n'.join(data[:-1])

        return message, ex_result

    @test_step
    def create_office_365_app(self):
        """Create office 365 App with provided details"""
        self.navigator.navigate_to_office365()

        self.o365_apps.create_office365_app()
        self.log.info('Created Office 365 App: %s', self.client_name)

    @test_step
    def wait_for_ad_mailbox_monitor(self):
        """Wait for AdMailboxMonitor to complete in proxy server"""
        if not self.windows_machine.wait_for_process_to_exit('AdMailboxMonitor'):
            raise CVTestStepFailure('Process did not end within stipulated time')

    @test_step
    def init_objects_for_new_client(self):
        """Initialize Client, Agent, Instance, Backup set objects for new client"""
        self.commcell.clients.refresh()
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get(self.agent_name)
        self.instance = self.agent.instances.get(self.instance_name)
        self.backupset = self.instance.backupsets.get(self.backupset_name)

    @test_step
    def get_service_accounts(self):
        """Get auto created service accounts of the client"""
        service_accounts = []
        for account in self.agent.properties['onePassProperties']['onePassProp']['accounts']['adminAccounts']:
            if account['serviceType'] == 2:
                service_accounts.append(account['exchangeAdminSmtpAddress'])

        if len(service_accounts) < 1:
            raise CVTestStepFailure('Found only %d Service Accounts, Expected 1 Service Account(s)'
                                    % len(service_accounts))

        self.log.info("Found %d service accounts.", len(service_accounts))
        return service_accounts[0]

    @test_step
    def check_service_accounts_permissions(self, service_accounts):
        """Check permissions for the auto created service account"""

        powershell_output = self.ex_powershell.check_online_service_account_permissions(
            service_account=service_accounts)

        if powershell_output is True:
            self.log.info("Verified the Service Account roles")
        else:
            raise CVTestStepFailure('Expected Roles not found assigned with the service account')

    @test_step
    def run_discovery(self):
        """Run discovery on the new client created"""
        exchange_subclient = UsermailboxSubclient(self.backupset, self.subclient_name)
        self.log.info("Discovered mailboxes: %d", len(exchange_subclient.discover_users))

    @test_step
    def delete_client(self):
        """Delete the client"""
        self.client.retire()

    def setup(self):
        """Setup Function for the Test Case"""
        try:
            self.exchange_mailbox = ExchangeMailbox(self)

            self.tcinputs['GlobalAdmin'] = self.exchange_mailbox.service_account_user
            self.tcinputs['Password'] = self.exchange_mailbox.service_account_password
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            username = self.inputJSONnode['commcell']['commcellUsername']
            password = self.inputJSONnode['commcell']['commcellPassword']

            self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
            self.admin_console.login(username, password)

            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.o365_apps = Office365Apps(self.tcinputs, self.admin_console, is_react=True)

            self.client_name = self.exchange_mailbox.client_name
            self.proxy_name = self.tcinputs.get('ProxyServers', None)[0]
            self.windows_machine = WindowsMachine(self.proxy_name, self.commcell)

            self.ex_powershell = ExchangePowerShell(
                ex_object=self.exchange_mailbox,
                cas_server_name=None,
                exchange_server=None,
                exchange_adminname=self.tcinputs['GlobalAdmin'],
                exchange_adminpwd=self.tcinputs['Password'],
                server_name=self.exchange_mailbox.server_name)
        except Exception as ex:
            handle_testcase_exception(self, ex)

    def run(self):
        """Run Function for the Test Case"""
        try:
            self.create_office_365_app()
            self.wait_for_ad_mailbox_monitor()
            self.init_objects_for_new_client()
            self.run_discovery()
            self.delete_client()
        except Exception as ex:
            handle_testcase_exception(self, ex)

    def tear_down(self):
        """Tear down Function for the Test Case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
