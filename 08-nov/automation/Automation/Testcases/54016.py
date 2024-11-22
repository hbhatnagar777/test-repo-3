# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Update Client Domain Name Change from Name Change Wizard

"""
import re
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from Server.NameChange.name_change_helper import NameChangeHelper

import ast

class TestCase(CVTestCase):
    """Class for executing verification of a client domain name change"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Update Client Domain Name Change from Name Change Wizard"

        self.retval = 0
        self.tcinputs = {
            "ResolvableClientDomainNames": None,  # 2 resolvable client domain names
            "ClientsList": None  # List of clients for which namechange has to be verified
        }
        self.name_change_helper_object = None
        self.server = None
        self.optionselector = OptionsSelector(self._commcell)
        self.found = 0
        self._commserv = self.commcell

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.log.info("creating Name Change helper instance")
        self.name_change_helper_object = NameChangeHelper(self)


    def run(self):
        """Main function for test case execution"""
        try:
            client_list = [x for x in ast.literal_eval(self.tcinputs["ClientsList"])]
            domain_names = []
            for client in client_list:
                client_object = self._commcell.clients.get(client)
                old_client_hostname = client_object.client_hostname
                self.log.info(
                    "Current client hostname is: %s",
                    old_client_hostname)
                current_domain_name = re.findall(r"\.(.*)", old_client_hostname)
                domain_names.append(current_domain_name[0])

            # checking if the domain names of the given clients are the same
            if domain_names.count(domain_names[0]) == len(domain_names):
                self.log.info(
                    "The domain names of the given clients match. Proceeding..")
            else:
                raise Exception(
                    "Domain names of the clients given don't match. Please make sure the given "
                    "clients' domain names match before execution")

            client_domain_names = [
                x for x in ast.literal_eval(self.tcinputs["ResolvableClientDomainNames"])]
            if domain_names[0] == client_domain_names[0]:
                new_domain_name = client_domain_names[1]
            elif domain_names[0] == client_domain_names[1]:
                new_domain_name = client_domain_names[0]
            self.name_change_helper_object.change_client_domain_name(
                ast.literal_eval(self.tcinputs["ClientsList"]),
                current_domain_name, new_domain_name)

            self.log.info(
                "Domain name updated successfully for all the given clients")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
