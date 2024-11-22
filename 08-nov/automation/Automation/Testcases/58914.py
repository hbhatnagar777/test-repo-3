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

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.DisasterRecovery.drmanagement_helper import DRManagementHelper
from Server.DisasterRecovery.drhelper import DRHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "[Negative Case] : Enable DR backup to UNC path"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = True
        self.tc = None
        self.dr_manager = None
        self.dr_helper = None
        self.machine = None
        self.existing_dr_policy = None
        self.tcinputs = {
            "UncPath": None,
            "UncUser": None,
            "UncPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.tc = ServerTestCases(self)
        self.dr_helper = DRHelper(self.commcell)
        self.machine = Machine()

    def validate(self, path, username, password, error_msg):
        """Method to validate the error response received"""
        dr_manager = DRManagementHelper(self.commcell)
        self.dr_helper.kill_running_drjobs()
        try:
            dr_manager.set_network_dr_path(path, username, password, validate=False)
            raise Exception('Path was set successfully, should have failed, Validation failed')

        except Exception as exp:
            if error_msg not in str(exp):
                raise Exception(str(exp))
            self.log.info('Error as expected : %s', format(str(exp)))
        self.log.info('Validation successful')

    def run(self):
        """Execution method for this test case"""
        try:
            custom_string = OptionsSelector(self.commcell).get_custom_str()
            path = self.tcinputs["UncPath"]
            password = self.tcinputs["UncPassword"]
            username = self.tcinputs["UncUser"] + '_' + custom_string
            self.log.info('Setting DR backup UNC path with incorrect user name [%s]', username)
            error_msg = ('Failed to set dr properties. Error: Failed to set [Backup Metadata Folder]'
                         ' for [DR Backup] with error [Create directory failed.].')

            self.validate(path, username, password, error_msg)
            username = self.tcinputs["UncUser"]
            password = self.tcinputs["UncPassword"] + '_' + custom_string
            self.log.info('Setting DR backup UNC path with incorrect password [%s]', password)

            self.validate(path, username, password, error_msg)
            password = self.tcinputs["UncPassword"]
            path = self.tcinputs["UncPath"] + '_' + custom_string
            self.log.info('Setting DR backup UNC path with path unavailable [%s]', path)

            self.validate(path, username, password, error_msg)
            path = self.tcinputs["UncPath"]
            self.log.info('Creating a set folder in the path')
            set_folder = path + '\\SET_58914'
            try:
                if set_folder.startswith('\\'):
                    # split machine hostname from destination path
                    hostname = set_folder.split('\\')[2]
                    self.log.info('Path is UNC path, hostname = {0}'.format(hostname))
                    machine_obj = Machine(hostname,
                                          username=self._tcinputs['UncUser'],
                                          password=self._tcinputs['UncPassword'])
                else:
                    machine_obj = self.machine
                machine_obj.create_directory(set_folder)

            except Exception as exp:
                self.log.info('Exception while creating folder: %s', format(str(exp)))

            self.log.info('Setting DR backup UNC path with path having data [%s]', path)
            error_msg = ('Failed to save Disaster Recovery Destination in CommServe database'
                         ' because folder [{0}] is already being used for '
                         'Disaster Recovery').format(path)
            try:
                dr_manager = DRManagementHelper(self.commcell)
                dr_manager.set_network_dr_path(path, username, password, validate=False)
                raise Exception('Path was set successfully, should have failed,'
                                ' Validation failed')
            except Exception as excp:
                if error_msg not in str(excp):
                    raise Exception(str(excp))
                self.log.info('Error as expected : %s', format(str(excp)))
                self.log.info('Validation successful')

        except Exception as exp:
            self.tc.fail(exp)
