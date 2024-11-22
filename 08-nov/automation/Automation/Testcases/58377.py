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
import time

class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Commcell level two factor auth for internal and external users"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "Commcell": None,
            "Company": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        tc = None
        try:
            tc = ServerTestCases(self)
            validator = LoginValidator(self)
            self.commcell.enable_tfa()
            validator.validate_multiusergroup_tfa()
            validator.validate(feature='user_login')
        except Exception as excep:
            tc.fail(excep)
        finally:
            self.commcell.disable_tfa()
            time.sleep(5)
            companies = self.commcell.organizations
            for company in companies.all_organizations:
                try:
                    self.commcell.organizations.get(company).disable_tfa()
                except Exception as e:
                    self.log.info(f"failed disable TFA for {company} because of exception: {e}")
                time.sleep(2)
