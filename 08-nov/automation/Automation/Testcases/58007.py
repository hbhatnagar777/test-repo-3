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
        self.name = "[Negative Case] : Validate Local to UNC path with invalid creds" \
                    " and UNC Path to UNC path with invalid creds"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = True
        self.tcinputs = {
            "UncPath": None,
            "UncUser": None,
            "UncPassword": None,
            "UncPath2": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        tc = ServerTestCases(self)
        try:
            validator = DRValidator(self)
            local_path = validator.dr_helper.generate_path(validator.dr_helper.client_machine,
                                                           alias='local_path',
                                                           create_path=True)
            self._log.info('Setting local path {0} as destination path'.format(local_path))
            validator.management.set_local_dr_path(path=local_path)
            self._log.info('Setting unc path {0} as destination'
                           ' with invalid credentails'.format(self.tcinputs.get('UncPath')))
            try:
                validator.management.set_network_dr_path(path=self.tcinputs.get('UncPath'),
                                                         username=self.tcinputs.get('UncUser'),
                                                         password='dummypassword')
            except Exception as excp:
                self._log.info('ERROR : {0}'.format(excp))
            self._log.info('Setting unc path {0} as destination'
                           ' with valid credentails'.format(self.tcinputs.get('UncPath')))
            validator.set_destination_path()
            self._log.info('Setting unc path {0} as destination'
                           ' with invalid credentails'.format(self.tcinputs.get('UncPath')))
            try:
                validator.management.set_network_dr_path(path=self.tcinputs.get('UncPath2'),
                                                         username=self.tcinputs.get('UncUser'),
                                                         password='dummypassword')
            except Exception as excp:
                self._log.info('ERROR : {0}'.format(excp))
            self._log.info('Negative Scenario validated successfully')
        except Exception as excp:
            tc.fail(excp)
