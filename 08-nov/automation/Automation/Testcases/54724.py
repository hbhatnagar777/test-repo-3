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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
import smtplib


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SMTP Server Test"
        self.show_to_user = True
        self.tcinputs = {
            "SERVER": None,
            "PORT": None,
            "USER": None,
            "PASSWORD": None,
            "SENDER": None,
            "RECIPIENT": None,
            "CAPABILITY": None
        }


    def run(self):
        """Run function of this test case"""
        try:
            smtp = smtplib.SMTP(self.tcinputs["SERVER"], port=self.tcinputs["PORT"])

            if smtp:
                self.log.info("Successful connection to host")

                msg = smtp.ehlo()[1].decode("utf-8")
                if self.tcinputs["CAPABILITY"] in msg:
                    self.log.info("Expected capability supported")
                else:
                    self.log.info("Expected capability NOT supported")

                try:
                    smtp.login(self.tcinputs["USER"], self.tcinputs["PASSWORD"])
                    self.log.info("Authentication successful")
                except smtplib.SMTPAuthenticationError:
                    self.log.error("Authentication unsuccessful")

                try:
                    smtp.sendmail(self.tcinputs["SENDER"], self.tcinputs["RECIPIENT"], "test message")
                    self.log.info("Send mail OK")
                except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused):
                    self.log.error("Invalid Sender/Recipient")

        except OSError:
            self.log.error("Failed to connect to host")
            self.status = constants.FAILED