# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This Test Case performs the Sanity Checks for Identity Provider Commcell.
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Server.routercommcell import RouterCommcell
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Class for executing Multicommcell Registration and sync """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Multicommcell Registration and Sync"
        self.log = None
        self._user_helper = None
        self.show_to_user = False
        self.tcinputs = {
            "ServiceCommcellName": None,
            "ServiceCommcellAdminUserName": None,
            "ServiceCommcellAdminUserPassword": None
        }
    def setup(self):
        """Setup function of this test case"""
        self.router_commcell = RouterCommcell(self.commcell)
        self.utility = OptionsSelector(self.commcell)

    def run(self):
        """Main function for test case execution"""

        try:
            self.router_commcell.register_service_commcell(service_commcell_host_name=self.tcinputs["ServiceCommcellName"],
                                                           service_user_name=self.tcinputs["ServiceCommcellAdminUserName"],
                                                           service_password=self.tcinputs["ServiceCommcellAdminUserPassword"],
                                                           registered_for_idp="True")
            self.utility.sleep_time(10)
            self.router_commcell.get_service_commcell(self.tcinputs["ServiceCommcellName"],
                                                      self.tcinputs["ServiceCommcellAdminUserName"],
                                                      self.tcinputs["ServiceCommcellAdminUserPassword"])
            self.router_commcell.check_registration()
            self.router_commcell.validate_sync()
            self.router_commcell.validate_commcells_idp(self.commcell)
            self.router_commcell.unregister_service_commcell()

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
