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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.contentstore_helper import ContentStore
from Application.Exchange.ExchangeMailbox.smtpdashboard_helper import SMTPDashboard
from Web.Common.cvbrowser import BrowserFactory
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from AutomationUtils import machine
import time
from AutomationUtils.config import get_config

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """SMTP_Automation: Behavioral Verification of whitelist feature for SMTP Gateway"""

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
                exmbclient_object      (object)    --  Object of ExchangeMailbox class
        """
        super(TestCase, self).__init__()
        self.name = "SMTP_Automation: Behavioral Verification of whitelist feature for SMTP Gateway"
        self.show_to_user = True
        self.exmbclient_object = None
        self.tcinputs = {
            "DomainName": None,
            "DomainUserName": None,
            "DomainUserPassword": None,
            "ExchangeServer": None,
            "ExchangeAdminUserName": None,
            "ExchangeAdminPassword": None,
            "ContentStoreServer": None,
            "ContactDisplayName": None,
            "ContactEmailID": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.smtp_auto_user = self.exmbclient_object.contact
        self.smtp_contact_id = self.exmbclient_object.contactid
        self.testcase_id = str(self.exmbclient_object.tc_object.id)
        self.log = self.exmbclient_object.log
        self.smtp_machine = machine.Machine(self.exmbclient_object.server_name, self.exmbclient_object.commcell)
        self.testdata = TestData(self.exmbclient_object)
        self.exmbclient_object.users = [self.smtp_auto_user]

    def run(self):
        """Run function of this test case"""
        try:
            total_count = 0
            count = 1
            user_emailcount = 0
            cs_object = ContentStore(self.exmbclient_object)
            self.log.info("--------------------------PERFORMING CLEANUP OPERATION-----------------------------------")
            # cleanup : SMTPCache, AutomationTemp folder
            cs_object.cleanup_SMTPCache()
            # send one test email
            cs_object.send_email(count)
            total_count += count
            # Sleep for 2 min, for email to reach
            time.sleep(120)
            # Check that SMTPCache has only one email
            user_emailcount = cs_object.get_email_count_cache()
            if user_emailcount == total_count:
                self.log.info("SMTPCache has only one email in it")
            self.log.info("------------- UNCHECK THE OPTION TO 'TRUST MS EXCHANGE ONLINE IP ADDRESSES' ---------------")
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            driver = browser.driver
            smtpdashboard_obj = SMTPDashboard(driver)
            # Login
            smtpdashboard_obj.dashboard_login(driver, self.exmbclient_object.server_name,
                                              self.exmbclient_object.smtpdashboard_port,
                                              self.exmbclient_object.smtpdashboard_username,
                                              self.exmbclient_object.smtpdashboard_password)
            smtpdashboard_obj.toggle_trustmsexchange_button()
            self.log.info("------------ SENDING EMAILS. THEY SHOULDN'T BE RECEIVED AS TRUST HAS BEEN REMOVED----------")
            count = 5
            cs_object.send_email(count)
            time.sleep(120)
            user_emailcount = cs_object.get_email_count_cache()
            if user_emailcount == total_count:
                self.log.info("SMTPCache has only one email in it. This is expected")
            else:
                excp = "SMTPCache folder has {} emails even after removing trust. " \
                       "This is not expected".format(user_emailcount)
                raise Exception(excp)
            smtpdashboard_obj.toggle_trustmsexchange_button()
            self.log.info("------------ SENDING EMAILS. THEY SHOULD BE RECEIVED AS TRUST HAS BEEN GRANTED -----------")
            cs_object.send_email(count)
            total_count += 2 * count
            time.sleep(120)
            user_emailcount = cs_object.get_email_count_cache()
            if user_emailcount == total_count:
                self.log.info("SMTPCache has 11 emails in it after granting trust. This is expected")
            else:
                excp = f'SMTPCache folder has {str(user_emailcount)} emails even after granting trust.' \
                       f' This is not expected'
                raise Exception(excp)
            self.log.info("------------TESTCASE SUCCESSFUL--------------")
            self.status = constants.PASSED
        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
            self.log.info("------------TESTCASE FAILED--------------")
