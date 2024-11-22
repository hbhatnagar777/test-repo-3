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
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from AutomationUtils import machine
import time
import glob


class TestCase(CVTestCase):
    """SMTP_Automation: Verification of large email delivery for Contentstore Mailbox"""

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
        self.name = "SMTP_Automation: Verification of large email delivery for Contentstore Mailbox"
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
        self.log = self.exmbclient_object.log
        self.smtp_auto_user = self.exmbclient_object.contact
        self.smtp_contact_id = self.exmbclient_object.contactid
        self.testcase_id = str(self.exmbclient_object.tc_object.id)
        self.smtp_machine = machine.Machine(self.exmbclient_object.server_name, self.exmbclient_object.commcell)
        self.testdata = TestData(self.exmbclient_object)
        self.exmbclient_object.users = [self.smtp_auto_user]

    def run(self):
        """Run function of this test case"""
        try:
            cs_object = ContentStore(self.exmbclient_object)
            self.log.info("--------------------------PERFORMING CLEANUP OPERATION-----------------------------------")
            cs_object.cleanup_SMTPCache()
            cs_object.cleanup_AutomationTemp()
            # ################ Verification of Large email delivery
            self.log.info("-------------- SENDING LARGE EMAIL WITH SIZE 40 MB ------------------------")
            cs_object.send_email(1, Exchangeconstants.CSSendEmailHelper.LARGE)
            time.sleep(120)
            cs_object.get_emailproperties_from_smtpcache()
            self.log.info("Comparing the Metadata of files before and after reaching SMTPCache")
            smtpcache_dir = "{}\\{}".format(Exchangeconstants.LOCAL_WORKING_DIR,
                                            Exchangeconstants.CSSendEmailHelper.SMTPCACHEEMAILSDIR)
            o365emails_dir = "{}\\{}".format(Exchangeconstants.LOCAL_WORKING_DIR,
                                             Exchangeconstants.CSSendEmailHelper.O365EMAILSDIR)
            for xml_O365 in glob.glob(o365emails_dir + "\\*"):
                unique_id_index = xml_O365.rfind('\\') + 1
                unique_id_file = xml_O365[unique_id_index:]
                xml_smtp = smtpcache_dir + "\\" + unique_id_file
                diff = []
                with open(xml_O365, encoding="utf-8") as b:
                    blines = set(b)
                with open(xml_smtp, encoding="utf-8") as a:
                    for line in a:
                        if line not in blines:
                            diff.append(line)
                if len(diff) != 0:
                    self.log.info("----------TEST CASE FAILED----------There is a difference in metadata fields")
                    raise Exception("There is a difference in metadata fields of large email. Please check file:",
                                    xml_smtp)
            self.log.info("There is no difference in metadata. Testcase to verify large email delivery is successful")
        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
