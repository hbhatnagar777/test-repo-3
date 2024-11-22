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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from collections import defaultdict

class TestCase(CVTestCase):
    """Class for verification of restore job using AD group restore option"""

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
        self.name = "Verification of restore job using AD group restore option"
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
        self.mailboxes_list = self.tcinputs["Users"].split(",")
        self.smtp_list = []
        for mailbox in self.mailboxes_list:
            smtp = mailbox + "@" + self.tcinputs['DomainName']
            self.smtp_list.append(smtp)
            self.smtp_data[mailbox]=smtp
        self.log.info("Mailboxes are created successfully")
        self.exmbclient_object.exchange_lib.send_email(mailbox_list=self.smtp_list)
        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self.subclient = self.exmbclient_object.cvoperations.subclient
        self.exmbclient_object.users = self.smtp_list

        for i in range(1,3):
            start_index=0
            end_index=2
            self.group[f"{self.exmbclient_object.tc_object.id}_{i}"].extend(self.smtp_list[start_index:end_index])
            del self.smtp_list[start_index:end_index]

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
            self.office365_obj.add_user(users=list(self.smtp_data.values())[1:])
            self.office365_obj.run_backup()
            for emails in self.group:
                self.exmbclient_object.exchange_lib.cleanup_mailboxes(mailbox_list=self.group[emails])
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            restore_job_details=self.office365_obj.run_restore(ad_group_restore=list(self.group.keys()))

            if int(restore_job_details["Successful mailboxes"])!=3 or int(restore_job_details["Successful messages"])==0 or int(restore_job_details["Skipped messages"])!=0:
                self.log.info("AD Group restore job failed")
            self.log.info("AD Group restore job completed successfully")

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.navigator.navigate_to_office365()
        for group_name in self.group:
            self.msgraph_helper.delete_azure_ad_group(group_name=group_name)
        self.office365_obj.delete_office365_app(self.exmbclient_object.client_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)