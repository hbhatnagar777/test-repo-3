# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Changing Client Hostname for Non-CommServer Client - from Client Properties

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.NameChange.name_change_helper import NameChangeHelper

import ast

class TestCase(CVTestCase):
    """Class for executing verification of a client hostname change for a non-commsevrer client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Changing Client Hostname for Non-CommServer Client - " \
                    "from Client Properties"
        self.retval = 0
        self.tcinputs = {
            "ClientName": None,  # Client for which hostname has to be changed
            "ResolvableClientHostnames": None  # 2 resolvable client hostnames.(ex.FQDN, short)
        }
        self.name_change_helper_object = None
        self.server = None

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.log.info("creating Name Change helper instance")
        self.name_change_helper_object = NameChangeHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            client_object = self._commcell.clients.get(self.tcinputs["ClientName"])
            self.log.info("Finding the current hostname for the given client")
            old_client_hostname = client_object.client_hostname
            self.log.info(
                "Current client hostname is: %s",
                old_client_hostname)

            client_hostnames = [x for x in ast.literal_eval(
				                                self.tcinputs["ResolvableClientHostnames"])]

            if old_client_hostname.lower() == client_hostnames[0].lower():
                new_hostname = client_hostnames[1]
            if old_client_hostname.lower() == client_hostnames[1].lower():
                new_hostname = client_hostnames[0]

            self.name_change_helper_object.change_client_hostname(
                self.tcinputs["ClientName"], new_hostname)

            self.log.info("Client hostname has been updated")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
