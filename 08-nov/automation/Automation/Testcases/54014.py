# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Update CommServe hostname on CommServe and Remote Clients -
from Name Change Wizard

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from Server.NameChange.name_change_helper import NameChangeHelper

import ast

class TestCase(CVTestCase):
    """Class for executing verification of a commserver hostname change on commserver and
    remote clients"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Update CommServe hostname on CommServe and Remote Clients - " \
            "from Name Change Wizard"

        self.retval = 0
        self.tcinputs = {
            "ResolvableCommserverHostnames": None,  # 2 resolvable commserver hostnames(FQDN,short)
            "ClientsList": None  # Client for which commserver hostname has to be changed
        }
        self.name_change_helper_object = None
        self.server = None
        self.optionselector = OptionsSelector(self._commcell)

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.log.info("creating Name Change helper instance")
        self.name_change_helper_object = NameChangeHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Finding the commserver hostname")
            old_commserver_name = self._commcell.commserv_hostname
            self.log.info(
                "Current commserver hostname is: %s",
                old_commserver_name)
            commserver_hostnames = [x for x in ast.literal_eval(
                self.tcinputs["ResolvableCommserverHostnames"])]

            if old_commserver_name.lower() == commserver_hostnames[0].lower():
                new_hostname = commserver_hostnames[1]
            if old_commserver_name.lower() == commserver_hostnames[1].lower():
                new_hostname = commserver_hostnames[0]

            self.name_change_helper_object.change_commserver_hostname_remote_clients(
                new_hostname, ast.literal_eval(self.tcinputs["ClientsList"]))

            self.log.info(
                "Commserver hostname has been updated on commserver and remote clients")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
