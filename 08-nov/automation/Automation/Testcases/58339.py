# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.Security.user_login_validator import LoginValidator


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Login for User's [commcell user, AD user, LDAP user] with key DefaultADUserDomain"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "Commcell": None,
            "domain": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            tc = ServerTestCases(self)
            validator = LoginValidator(self)
            validator.validate(feature='domain_less_login', default_ad_user_domain=self.tcinputs['domain'], default_cs_domain="commcell")
        except Exception as excep:
            tc.fail(excep)
