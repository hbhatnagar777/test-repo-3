# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name Change - Changing Commserver Hostname for Non-CommServer Client -
from Client Properties

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from Server.NameChange.name_change_helper import NameChangeHelper

import ast

class TestCase(CVTestCase):
    """Class for executing verification of commserver hostname change for non-commserver clients"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name Change - Changing Commserver Hostname for Non-CommServer Client - " \
                    "from Client Properties"
        self.retval = 0
        self.tcinputs = {
            "ClientName": None,  # Client for which commserver hostname has to be changed
            # 2 resolvable commserver hostnames.(FQDN,short)
            "ResolvableCommserverHostnames": None
        }
        self.name_change_helper_object = None
        self.server = None
        self.options = OptionsSelector(self._commcell)

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.log.info("creating Name Change helper instance")
        self.name_change_helper_object = NameChangeHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            client_object = self._commcell.clients.get(self.tcinputs["ClientName"])
            self.log.info(
                "Finding the current commserver hostname for the given client")
            old_cs_hostname = client_object.commcell_name

            self.log.info(
                "Current commserver hostname of the client is: %s",
                old_cs_hostname)

            commserver_hostnames = [x for x in ast.literal_eval(
					                                  self.tcinputs["ResolvableCommserverHostnames"])]

            if old_cs_hostname.lower() == commserver_hostnames[0].lower():
                new_hostname = commserver_hostnames[1]
            if old_cs_hostname.lower() == commserver_hostnames[1].lower():
                new_hostname = commserver_hostnames[0]

            self.name_change_helper_object.change_commserver_hostname_for_client(
                self.tcinputs["ClientName"], new_hostname)

            self.log.info(
                "Commserver hostname for the client has been updated")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
