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
from Server.DisasterRecovery.drvalidator import DRValidator


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Validate DR backup client logs."
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = True
        self.tcinputs = {
            "UncPath": None,
            "UncUser": None,
            "UncPassword": None,
            "comma_sep_client_list": None,
            "comma_sep_log_file_names": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            tc = ServerTestCases(self)
            validator = DRValidator(self)
            validator.validate(feature="dr_backup_metadata", backup_type='full',
                               client_list=self.tcinputs.get('comma_sep_client_list').split(','),
                               log_names=self.tcinputs.get('comma_sep_log_file_names').split(','))
        except Exception as excep:
            tc.fail(excep)




