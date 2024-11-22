# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

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
from Server.Security.userhelper import UserHelper
from Server.Security.userconstants import WebConstants


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """User's [commcell user, AD user, LDAP user] login with email
        from [adminconsole, webconsole, gui] with key nAllowUserWithoutRightToLogin"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.userhelper = None
        self.result_string = "Successful"
        self.tcinputs = {
            "Commcell": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()
        self.userhelper = UserHelper(self.commcell)

    def run(self):
        """Execution method for this test case"""
        try:
            tc = ServerTestCases(self)
            validator = LoginValidator(self)
            validator.associations = False
            validator.prerequisites()
            validator.validate_association_less_login(login_with="email")
            validator.validate_user_login(login_with="email",
                                          additional_setting={"category": "CommServDB.GxGlobalParam",
                                                            "key_name": "nAllowUserWithoutRightToLogin",
                                                            "data_type": "INTEGER",
                                                            "value": "1"})
        except Exception as excep:
            tc.fail(excep)

        finally:
            validator.cleanup()
