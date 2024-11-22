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
import Application.Exchange.ExchangeMailbox.constants as Exchangeconstants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.contentstore_helper import ContentStore
from Application.Exchange.ExchangeMailbox.contentstore_helper import XMLWriter
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from AutomationUtils import machine
import time
import glob


class TestCase(CVTestCase):
    """SMTP_Automation: Verification of message delivery and email metadata for Contentstore Mailbox"""

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
        self.name = "SMTP_Automation: Verification of message delivery and email metadata for Contentstore Mailbox"
        self.show_to_user = True
        self.exmbclient_object = None
        self.user_emailcount = 0
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
        self.log = self.exmbclient_object.log
        self.smtp_auto_user = self.exmbclient_object.contact
        self.smtp_contact_id = self.exmbclient_object.contactid
        self.testcase_id = str(self.exmbclient_object.tc_object.id)
        self.smtp_machine = machine.Machine(self.exmbclient_object.server_name, self.exmbclient_object.commcell)
        self.testdata = TestData(self.exmbclient_object)
        self.exmbclient_object.users = [self.smtp_auto_user]
        self.svcstopped = 0

    def run(self):
        """Run function of this test case"""
        try:
            cs_object = ContentStore(self.exmbclient_object)

            self.svcstopped = 0

            self.log.info("--------------------------PERFORMING CLEANUP OPERATION-----------------------------------")

            # cleanup : SMTPCache, AutomationTemp folder
            cs_object.cleanup_SMTPCache()

            cs_object.cleanup_AutomationTemp()

            # Sending ten sample emails
            self.log.info("--------------------------SENDING TEN TEST EMAILS-----------------------------------")

            cs_object.send_email(10)

            # Sleep for 2 min, for emails to reach
            time.sleep(120)

            cs_object.get_emailproperties_from_smtpcache()

            # Stop SMTP Service
            self.log.info("--------------------------STOP SMTP SERVICE---------------------")
            self.smtp_machine.client_object.stop_service("GxImapServer(Instance001)")
            self.svcstopped = 1

            # Sending ten sample emails
            self.log.info("---------SENDING TEN TEST EMAILS AFTER STOPPING SERVICE-----------------------")

            cs_object.send_email(10)

            # Start SMTP Service
            self.log.info("--------------------------START SMTP SERVICE-----------------------------------")
            self.smtp_machine.client_object.start_service("GxImapServer(Instance001)")

            # Sleep for 20 min
            time.sleep(int(Exchangeconstants.EXCHANGE_QUEUE_TIMEOUT))

            # Verify that all emails are received
            self.log.info("-----------------VERIFYING SMTPCACHE FOLDER FOR EMAILS ----------------------")

            self.user_emailcount = cs_object.get_email_count_cache()
            mailcount_after_start_svc = self.user_emailcount

            if mailcount_after_start_svc != 20:
                self.log.info("SMTP Cache has %s number of emails. Expected 20.", mailcount_after_start_svc)
                raise Exception("Expected 20 mails and Actual is " + str(mailcount_after_start_svc) + " mails")

            self.log.info("Email count matches. Opening each EML and retrieving the metadata..")

            cs_object.get_emailproperties_from_smtpcache()

            self.log.info("Comparing the Metadata of files before and after reaching SMTPCache")
            automationdir_smtpcache = "{}\\{}".format(Exchangeconstants.LOCAL_WORKING_DIR,
                                                      Exchangeconstants.CSSendEmailHelper.SMTPCACHEEMAILSDIR)
            automationdir_O365 = "{}\\{}".format(Exchangeconstants.LOCAL_WORKING_DIR,
                                                 Exchangeconstants.CSSendEmailHelper.O365EMAILSDIR)
            xml = XMLWriter()
            for xml_O365 in glob.glob(automationdir_O365 + "\\*"):
                uniqueid_indx = xml_O365.rfind('\\') + 1
                uniqueid_file = xml_O365[uniqueid_indx:]
                xml_smtp = automationdir_smtpcache + "\\" + uniqueid_file
                diff = xml.comparexmlfiles(xml_O365, xml_smtp)
                if diff:
                    self.log.info("----------TEST CASE FAILED----------There is a difference in metadata fields: %s",
                                  diff['root'])
                    raise Exception("There is a difference in metadata fields. Please check file:", xml_smtp)

            self.log.info("There is no difference in metadata. Testcase successful")
            self.log.info("-----TEST CASE PASSED----------All the emails are received after starting SMTP Service-----")

        except Exception as ex:
            if self.svcstopped == 1:
                self.log.info("------START SMTP SERVICE AS TEST CASE FAILED AND SERVICE IS IN STOPPED STATE----------")
                self.smtp_machine.client_object.start_service("GxImapServer(Instance001)")
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
