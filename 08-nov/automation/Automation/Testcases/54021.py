# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Changing the Display Name for Non-CommServer Client -
from Client Properties

"""
import re
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.NameChange.name_change_helper import NameChangeHelper


class TestCase(CVTestCase):
    """Class for executing verification of non-commserver client's display name change"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Changing the Display Name for Non-CommServer Client - " \
                    "from Client Properties"
        self.retval = 0
        self.tcinputs = {
            "ClientName": None
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

            self.log.info(
                "Finding the current display name of the given client")
            self.client_object = self._commcell.clients.get(
                self.tcinputs["ClientName"])
            old_disp_name = self.client_object.display_name

            self.log.info(
                "Current display name of the client: %s",
                old_disp_name)

            if bool(re.search("updated", old_disp_name)):
                new_name = old_disp_name.split('_updated')[0]
            else:
                new_name = old_disp_name + "_updated"

            self.log.info(
                "New client display name should be: %s",
                str(new_name))
            self.name_change_helper_object.change_client_display_name(
                self.tcinputs["ClientName"], new_name)
            self.log.info("Client display name updated successfully")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
