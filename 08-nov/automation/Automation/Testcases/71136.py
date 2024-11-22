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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.msgraph_helper import CVEXMBGraphOps
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Verification of email deletion on the Exchange browse page"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verification of email deletion on the Exchange browse page"
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


    def setup(self):
        """Setup function for testcase execution"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.testdata = TestData(self.exmbclient_object)
        self.msgraph_helper=CVEXMBGraphOps(self.exmbclient_object)
        self.mailboxes_list = self.testdata.create_online_mailbox(use_json=False,count=6)
        self.smtp_list = []
        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)
        self.log.info("Mailboxes are created successfully")
        self.exmbclient_object.exchange_lib.send_email(
            mailbox_list=self.smtp_list)
        self.log.info("Mailbox List: %s" % self.mailboxes_list)
        self.log.info("SMTP List: %s" % self.smtp_list)
        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self.subclient = self.exmbclient_object.cvoperations.subclient
        self.exmbclient_object.users = self.smtp_list
        self.filter_value = self.tcinputs['filter_value']

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

    def run(self):
        """Main function for test case execution"""

        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            self.office365_obj.add_user(self.smtp_list)
            self.office365_obj.run_backup()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            count=int(self.office365_obj.get_browse_count(filter_value=self.filter_value)[0])
            mail_to_delete=count//2
            if mail_to_delete>=15:
                mail_to_delete=15
            self.office365_obj.delete_message_in_browse(count=mail_to_delete)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            delete_count=int(self.office365_obj.get_browse_count(filter_value=self.filter_value)[0])
            if delete_count!=(count-mail_to_delete):
                raise Exception("Message count are not correct after deletion")
            self.log.info("Message count is verified")
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            self.office365_obj.apply_sort_in_mailbox_table(column_name="Active items backed up",sort_order=False)
            mailbox_data=self.office365_obj.get_mailbox_tab_table_data()
            self.office365_obj.delete_backup_data(entity=mailbox_data["Name"][0])
            self.filter_value["Mailbox"]=mailbox_data["Name"][0]
            if int(self.office365_obj.get_browse_count(filter_value=self.filter_value)[0]):
                raise Exception("Message count are not correct after deletion")
            self.log.info("Message count is verified")
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            audit_table_data=self.office365_obj.get_audit_trail_data(app_name=self.exmbclient_object.client_name,user_name=self.inputJSONnode['commcell']['commcellUsername'],filter_value="Files/Emails deleted")
            if "Files/Emails deleted" not in audit_table_data["Operation"]:
                raise Exception("Deleted operation not in Audit trail report")
            self.log.info("Deleted operation is in Audit trail report")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.exmbclient_object.client_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

