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


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Company User's [local user, AD user, LDAP user] login with username
        from [adminconsole, gui] with key nAllowUserWithoutRightToLogin"""
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
        tc = None
        validator = None
        try:
            tc = ServerTestCases(self)
            validator = LoginValidator(self)
            validator.associations = False
            validator.prerequisites()
            validator.validate_association_less_login()
            validator.validate_user_login(additional_setting={"category": "CommServDB.GxGlobalParam",
                                                              "key_name": "nAllowUserWithoutRightToLogin",
                                                              "data_type": "INTEGER",
                                                              "value": "1"})
        except Exception as excep:
            tc.fail(excep)
        finally:
            validator.cleanup()
            da_job = self.commcell.run_data_aging(include_all_clients=True)
            self.log.info("Started Data Aging: %s", da_job.job_id)
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job job with error: %s", da_job.delay_reason
                )
            self.log.info("Data aging job completed!")
