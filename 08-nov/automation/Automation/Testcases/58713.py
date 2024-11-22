# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "O365 auto discovery configuration"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.exmbclient_object = None
        self.archive_policy = None
        self.cleanup_policy = None
        self.retention_policy = None
        self.subclient = None
        self.navigator = None
        self.content_dict = {
            0: "All mailboxes",
            1: 'All O365 group mailboxes',
            2: 'All Public Folders'
        }

    def setup(self):
        self.log.info("Creating exchange mailbox client object")
        self.exmbclient_object = ExchangeMailbox(self)
        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self.subclient = self.exmbclient_object.cvoperations.subclient

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console,
                                           is_react=True)

    def fetch_all_o365_groups(self):
        """Fetch O365 groups from the DAT file"""
        query = "select * from MBInfo where msExchRecipientTypeDetails!=1 and msExchRecipientTypeDetails!=4"
        job_results_directory = self.exmbclient_object.get_job_results_dir
        sqlite_helper = SQLiteHelper(self)
        result = sqlite_helper.execute_dat_file_query(job_results_directory,"cvmailboxstore9.dat",query)
        return result

    def run(self):
        """Main function for test case execution"""

        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)

            for i in range(2):

                self.office365_obj.select_content(self.content_dict[i])  # Select All Users association
                self.subclient.refresh()
                if i == 0:
                    content_list = self.subclient.discover_users
                else:
                    content_list = self.fetch_all_o365_groups()
                self.office365_obj.verify_content_association(content_list)
                self.office365_obj.deselect_content(self.content_dict[i])
                self.office365_obj.verify_content_deassociation()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.exmbclient_object.client_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

