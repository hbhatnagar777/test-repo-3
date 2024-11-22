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
    """Class for executing company user email login test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Company User's[local user, AD user, AD as Generic LDAP user, Redhat as Generic LDAP user, openldap
         user, oracle directory user] login with email from [adminconsole, Rest api, qlogin]"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.result_string = "Successful"
        self.tcinputs = {
            "Company": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            tc = ServerTestCases(self)
            validator = LoginValidator(self)
            validator.validate(feature='user_login', login_with="email")
        except Exception as excep:
            tc.fail(excep)
        finally:
            da_job = self.commcell.run_data_aging(include_all_clients=True)
            self.log.info("Started Data Aging: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job job with error: %s", da_job.delay_reason
                )
            self.log.info("Data aging job completed!")
