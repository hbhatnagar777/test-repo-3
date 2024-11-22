# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Name change - Update Commserver Display Name from Name Change Wizard

"""
import re
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.NameChange.name_change_helper import NameChangeHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing verification of commserver client's display name change"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Name change - Update Commserver Display Name from Name Change Wizard"
        self.retval = 0
        self.tcinputs = {  # This testcase needs no input
        }
        self.name_change_helper_object = None
        self.server = None
        self.options = OptionsSelector(self._commcell)

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")

        self.log.info("creating Name Change helper instance")
        self.name_change_helper_object = NameChangeHelper(self)
        self._commserv = self.commcell

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Finding the current display name of commcell")
            old_disp_name = self._commserv.clients.get(self._commserv.commserv_hostname).\
                display_name

            self.log.info("Current display name: %s", old_disp_name)

            if bool(re.search("updated", old_disp_name)):
                new_name = old_disp_name.split('_updated')[0]
            else:
                new_name = old_disp_name + "_updated"

            self.name_change_helper_object.change_commserve_display_name(
                new_name)
            self.log.info("Commserver display name updated successfully")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
