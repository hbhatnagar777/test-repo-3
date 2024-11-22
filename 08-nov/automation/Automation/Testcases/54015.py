# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Update CommServe for Client (After DR Restore Usage) - from Name Change
Wizard

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.NameChange.name_change_helper import NameChangeHelper

import ast

class TestCase(CVTestCase):
    """Class for executing verification of a commserver hostname change on the clients, after
        DR restore
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Update CommServe for Client (After DR Restore Usage) - " \
                    "from Name Change Wizard"

        self.retval = 0
        self.tcinputs = {
            "ResolvableCommserverHostnames": None,  # 2 resolvable commserver hostnames(FQDN,short)
            "ClientsList": None  # List of clients for which namechange has to be verified
        }
        self.name_change_helper_object = None
        self.server = None
        self.found = 0
        self.hostname_position = 0

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.log.info("creating Name Change helper instance")
        self.name_change_helper_object = NameChangeHelper(self)


    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Finding the commserver hostname")
            current_cs_hostname = self._commcell.commserv_hostname
            self.log.info(
                "Current commserver hostname is: %s",
                current_cs_hostname)
            commserver_hostnames = [x for x in ast.literal_eval(
				                                    self.tcinputs["ResolvableCommserverHostnames"])]
            # Checking if the current hostname is present in the provided
            # ResolvableCommserverHostnames list
            for hostname in commserver_hostnames:
                if hostname.lower() == current_cs_hostname.lower():
                    self.found = 1
                    break  # break the loop if found
                else:
                    self.hostname_position += 1

            if self.hostname_position == 0:
                new_temp_cs_hostname = commserver_hostnames[1]
            elif self.hostname_position == 1:
                new_temp_cs_hostname = commserver_hostnames[0]
            self.log.info(
                "The temporary commserver hostname in the clients should be: %s",
                new_temp_cs_hostname)

            if self.found == 1:
                self.log.info(
                    "Found the current hostname in the provided hostnames list. Procceding")
                client_list = [x for x in ast.literal_eval(self.tcinputs["ClientsList"])]
                for client in client_list:
                    self.log.info(
                        "Finding the current commserver hostname for the client: %s", client)
                    client_object = self._commcell.clients.get(client)
                    current_cs_hostname_on_client = client_object.commcell_name

                    # If the commserver client's hostname and client's commserver hostname are
                    # same, we are changing the client's commserver hostname to the
                    # other resolvable hostname
                    if current_cs_hostname.lower() == current_cs_hostname_on_client.lower():
                        self.log.info(
                            "Running temporary commserver hostname change on client : %s", client)
                        self.name_change_helper_object.change_commserver_hostname_for_client(
                            client, new_temp_cs_hostname)
                        self.log.info(
                            "Commserver hostname for the client '%s' has been updated", client)

                    # If the commserver client's hostname and client's commserver hostname are
                    # different, there is no need to change the client's commserver# hostname
                    elif new_temp_cs_hostname.lower() == current_cs_hostname_on_client.lower():
                        self.log.info(
                            "This client, '%s' doesn't need temporary hostname change", client)

                # Once temporary commserver hostname change is dont for all the required clients,
                # we are changing the temporary commserver hostname in the
                # clients to the current commserver hostname
                self.log.info(
                    "Proceeding to 'Update CommServe for Client (After DR Restore Usage)'")
                self.name_change_helper_object.change_commserver_hostname_after_dr(
                    current_cs_hostname, new_temp_cs_hostname, ast.literal_eval(self.tcinputs["ClientsList"]))
            else:
                raise Exception(
                    "Current commserver hostname not found in given commserver hostname list.")

            self.log.info(
                "Commserver hostname has been updated on the clients")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
