# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Changing Client Name for Non-CommServer - from Client Properties

"""
import re
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from Server.NameChange.name_change_helper import NameChangeHelper


class TestCase(CVTestCase):
    """Class for executing verification of a client name change for a non-commsevrer client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Changing Client Name for Non-CommServer - from Client Properties"

        self.retval = 0
        self.tcinputs = {
            "ClientNameToChange": None  # Client for which name has to be changed
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
            self.log.info(
                "Finding the current client name for the given client")

            dbquery = "select name from app_client where  name like '%" \
                      + str(self.tcinputs["ClientNameToChange"]) + "%'"
            result = self.options.exec_commserv_query(dbquery)
            old_client_name = str(result[0][0])

            self.log.info("Current client name is: %s", old_client_name)

            if bool(re.search("updated", old_client_name)):
                new_name = old_client_name.split('_updated')[0]
            else:
                new_name = old_client_name + "_updated"

            self.name_change_helper_object.change_client_name(
                old_client_name, new_name)

            self.log.info("Client name has been updated")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
