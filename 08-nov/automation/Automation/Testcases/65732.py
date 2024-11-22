# -*-coding:utf-8-*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems,Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Honeypot simulation by deleting a trap file and validating alert mail

"""
import random
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.mail_box import MailBox, EmailSearchFilter
from AutomationUtils import logger
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for executing this testcase"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.filtered_users = None
        self.users_list = None
        self.alert_mail = None
        self.search_query = None
        self.client_machine = None
        self.name = "Honeypot ransomware check validation"
        self.log = logger.get_log()
        self.tcinputs = {
            "ClientName": None
        }
        self.commcell = None
        self.trapFiles_list = []
        self.utils = TestCaseUtils(self)
        self.mailbox = None
        self.folder_path = None

    def setup(self):
        """Setup function of this testcase"""
        try:
            # self.events = Events(self.cc)
            self.client_machine = Machine(machine_name=self.tcinputs['ClientName'], commcell_object=self.commcell)
            self.log.info(self.client_machine)
            self.get_trapfile_list()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def get_trapfile_list(self):
        """Simulates honeypot alert by encrypting or modifying trapfiles in clientmachine"""
        try:
            self.users_list = self.client_machine.get_folders_in_path("C:\\Users", recurse=False)
            self.filtered_users = [user for user in self.users_list if user != "C:\\Users\\Public"]
            self.folder_path = random.choice(self.filtered_users) + "\\Documents"
            self.log.info(self.folder_path)
            self.trapFiles_list = self.client_machine.get_files_in_path(self.folder_path, recurse=False,
                                                                        only_hidden=True)

        except:
            self.log.error(f"No trap files found in specified path:{self.folder_path}")
            raise Exception("No trap files found")

    def simulate_honeypot_by_trapfile_deletion(self):
        """Simulates honeypot alert by deleting or modifying trapfiles in clientmachine"""
        try:
            if len(self.trapFiles_list) > 0:
                self.client_machine.delete_file(self.trapFiles_list[1])
                self.log.info("one of the trap file deleted")
        except Exception as err:
            self.log.error(f"An error occurred:{err}")
            self.utils.handle_testcase_exception(err)

    def simulate_honeypot_by_aes_encryption(self):
        """Simulates honeypot alert by encrypting or modifying trapfiles in clientmachine"""
        try:
            if len(self.trapFiles_list) > 0:
                self.log.info("executing simulation of honeypot through aes encryption case")
                self.log.info(self.trapFiles_list[2])
                self.client_machine.modify_test_data(data_path=self.trapFiles_list[2], encrypt_file_with_aes=True)
                self.log.info("one of the trap file is encrypted")
        except Exception as err:
            self.log.error(f"An error occurred:{err}")
            self.utils.handle_testcase_exception(err)

    def is_honeypot_alert_sent(self):
        """Checks mailbox for alert mail"""
        try:
            # Define the search filter using EmailSearchFilter
            self.search_query = EmailSearchFilter("Alert: Threat Indicator")
            # Searches for latest unread alert mail
            self.alert_mail = self.mailbox.get_mail(search_query=self.search_query)

            if self.alert_mail:
                self.log.info("Alert mail sent successfully")
                return True
            else:
                self.log.info("Alert mail is not sent")
                return False

        except Exception as e:
            self.log.error(f"An error occurred:{e}")
            self.utils.handle_testcase_exception(e)
            return False

        finally:
            # Always make sure to disconnect from the mailserver in case of an exception
            if self.mailbox:
                self.mailbox.disconnect()

    def mail_validation(self):
        """validates alert mail"""
        self.log.info("alert mail validation started")
        try:
            self.mailbox = MailBox()
            self.mailbox.connect()
            if self.is_honeypot_alert_sent():
                self.log.info("honeypot ransomware detection is successful")
            else:
                self.log.error("honeypot ransomware detection is unsuccessful")
        except Exception as e:
            self.log.error(f"An error occurred:{e}")
            self.log.error(f"honeypot ransomware detection failed due to an error {e}")

    def run(self):
        """run function of this testcase"""
        try:
            self.log.info("honeypot simulation by trapfile deletion started")
            self.simulate_honeypot_by_trapfile_deletion()
            time.sleep(1000)

            self.mail_validation()

            self.log.info("pausing to avoid cooling period for sending ransomware alert")
            time.sleep(300)

            self.log.info("honeypot simulation by trapfile encryption started")
            self.simulate_honeypot_by_aes_encryption()
            time.sleep(1000)

            self.mail_validation()

        except Exception as err:
            self.log.error(f"An error occurred:{err}")
            self.utils.handle_testcase_exception(err)