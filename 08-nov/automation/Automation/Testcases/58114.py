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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import sys
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.msgraph_helper import CVEXMBGraphOps
from Web.AdminConsole.Office365Pages.constants import ExchangeOnline
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure
from collections import defaultdict

class TestCase(CVTestCase):
    """Class for adding mailboxes and groups to clients and verifying user details after changes in the Azure portal"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not
                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user
                    default: False

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type
                        Ex: {
                             "MY_INPUT_NAME": None
                        }
        """
        super(TestCase, self).__init__()
        self.name = "Creation of Office365 client with modern authentication enabled"
        self.show_to_user = True
        self.mailboxes_list = []
        self.smtp_list = []
        self.exmbclient_object = None
        self.testdata=None
        self.msgraph_helper=None
        self.group=defaultdict(list)
        self.smtp_data = defaultdict(str)


    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.testdata = TestData(self.exmbclient_object)
        self.msgraph_helper=CVEXMBGraphOps(self.exmbclient_object)
        self.mailboxes_list = self.testdata.create_online_mailbox(use_json=False,count=6)
        self.smtp_list = []
        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)
            self.smtp_data[mailbox]=smtp
        self.log.info("Mailboxes are created successfully")
        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self.subclient = self.exmbclient_object.cvoperations.subclient
        self.exmbclient_object.users = self.smtp_list

        for i in range(1,3):
            start_index=0
            end_index=2
            self.group[f"{self.exmbclient_object.tc_object.id}_{i}"].extend(self.smtp_list[start_index:end_index])
            del self.smtp_list[start_index:end_index]
            del self.mailboxes_list[start_index:end_index]

        self.group=dict(self.group)
        for group_name in self.group:
            self.msgraph_helper.create_group(group_name=group_name)
            time.sleep(10)
            self.msgraph_helper.add_group_members(group_name=group_name, members=self.group[group_name])
        self.log.info("Groups are created and members are associated to the group")

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.users = self.smtp_list
        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console,
                                           is_react=True)

    def run(self):
        """Run function of this test case"""
        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            self.office365_obj.add_user(users=self.users)
            self.office365_obj.add_AD_Group(groups=[group_names for group_names in self.group])

            time.sleep(60)
            display_name=self.msgraph_helper.update_user(user_upn=self.smtp_data[self.mailboxes_list[0]],properrty="DISPLAY-NAME")
            self.smtp_data[display_name]=self.smtp_data[self.mailboxes_list[0]]
            del self.smtp_data[self.mailboxes_list[0]]
            self.log.info("Display Name for User is modified")

            for i in self.group:
                new_display_name=self.msgraph_helper.update_user(user_upn=self.group[i][0],properrty="DISPLAY-NAME")
                self.smtp_data[new_display_name]=self.group[i][0]
                del self.smtp_data[self.group[i][0].split("@")[0]]
                time.sleep(5)
            self.log.info("Display Name for User in group is modified")

            new_smtp="modified"+self.smtp_data[self.mailboxes_list[1]]
            self.msgraph_helper.update_user_smtp(user_upn=self.smtp_data[self.mailboxes_list[1]],
                                                           new_mail_address=new_smtp)
            self.smtp_data[self.mailboxes_list[1]]=new_smtp
            self.log.info("SMTP for User is modified")

            for i in self.group:
                new_smtp="modified"+self.group[i][1]
                self.msgraph_helper.update_user_smtp(user_upn=self.group[i][1],new_mail_address=new_smtp)
                self.smtp_data[self.group[i][1].split("@")[0]]=new_smtp
                time.sleep(5)
            self.log.info("SMTP for User in group is modified")

            self.log.info(
                "--------------------------RUNNING AdMailboxMonitor"
                "-----------------------------------"
            )
            self.exmbclient_object.cvoperations.run_admailbox_monitor()
            self.admin_console.refresh_page()
            self.admin_console.access_tab(ExchangeOnline.ACCOUNT_TAB.value)
            mailbox_data=self.office365_obj.get_mailbox_tab_table_data()
            self.log.info("Verification of user details in mailbox tab")
            for user_name in self.smtp_data:
                if mailbox_data['Email address'][mailbox_data['Name'].index(user_name)]!=self.smtp_data[user_name]:
                    raise Exception(f"Value is mismatched for user {user_name}")
            self.log.info("Mailbox tab is table verified after changing the user details in Azure portal")

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.navigator.navigate_to_office365()
        for emails in self.smtp_data:
            self.msgraph_helper.delete_azure_ad_user(user_upn=self.smtp_data[emails])
        for group_name in self.group:
            self.msgraph_helper.delete_azure_ad_group(group_name=group_name)
        self.office365_obj.delete_office365_app(self.exmbclient_object.client_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
