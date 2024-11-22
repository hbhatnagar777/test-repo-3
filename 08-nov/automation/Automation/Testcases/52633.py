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
        self.validator = None
        self.cv_cloud_creds = None
        self.name = "Validate upload to cvcloud scenario"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = True
        self.tcinputs = {
            "UncPath": None,
            "UncUser": None,
            "UncPassword": None,
            "CloudCS": None,
            "CloudUserName": None,
            "CloudPassword": None,
            "CompanyName": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()
        self.cv_cloud_creds = {
            "CloudCS": self.tcinputs.get('CloudCS'),
            "CloudUserName": self.tcinputs.get('CloudUserName'),
            "CloudPassword": self.tcinputs.get('CloudPassword'),
            "CompanyName": self.tcinputs.get('CompanyName'),
            "DestinationPath": self.tcinputs.get('DestinationPath')
        }
        self.validator = DRValidator(self,
                                     cvcloud_cs=self.cv_cloud_creds.get('CloudCS'),
                                     cvcloud_username=self.cv_cloud_creds.get('CloudUserName'),
                                     cvcloud_password=self.cv_cloud_creds.get('CloudPassword'))

    def run(self):
        """Execution method for this test case"""
        tc = ServerTestCases(self)
        try:
            self.validator.validate(feature="dr_backup_metadata",
                                    backup_type='full',
                                    upload_to_cvcloud=self.cv_cloud_creds)
        except Exception as excep:
            tc.fail(excep)

    def tear_down(self):
        self.validator.management.upload_metdata_to_cloud_library(flag=False)
