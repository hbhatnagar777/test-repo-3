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
import os
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.DisasterRecovery.drhelper import DRHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.share_path = None
        self.name = "[Negative Case] : Partial upload of DRBackup dumps "
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = True
        self.tc = None
        self.machine = None
        self.directory = None
        self.dr_manager = None
        self.existing_dr_policy = None
        self.dr_helper = None
        self.tcinputs = {
            "hostname": None,
            "UncUser": None,
            "UncPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.tc = ServerTestCases(self)
        self.machine = Machine(machine_name=self.tcinputs["hostname"],
                               username=self.tcinputs["UncUser"],
                               password=self.tcinputs["UncPassword"])
        self.dr_helper = DRHelper(self.commcell)
        self.dr_manager = self.dr_helper.management

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Creating required prerequisites")
            dr_entities = self.dr_helper.dr_prerequisites()
            self.existing_dr_policy = self.dr_manager.dr_storage_policy
            self.dr_manager.dr_storage_policy = dr_entities['storagepolicy']

            self.log.info("Creating and sharing the directory")
            self.share_path = self.dr_helper.generate_path(self.machine, alias='share', create_path=True)
            share_name = self.share_path.split("\\")[-1]
            self.machine.share_directory(share_name=share_name, directory=self.share_path)
            network_path = "\\\\{0}\\{1}".format(self.machine.machine_name, share_name)

            self.log.info("Setting network path {0} as destination path".format(network_path))
            self.dr_manager.set_network_dr_path(path=network_path, username=self.tcinputs["UncUser"],
                                                password=self.tcinputs["UncPassword"])

            self.dr_helper.kill_running_drjobs()
            self.dr_helper.trigger_dr_backup(wait_for_completion=False)
            set_folder = False
            while not set_folder:
                self.log.info("Checking if set folder is created")
                folder_list = self.machine.get_folders_in_path(self.share_path)
                if folder_list:
                    for folder in folder_list:
                        if 'SET' in folder:
                            set_folder = True
                            break
            self.machine.unshare_directory(share_name=share_name)
            self.log.info("Unshared the folder to simulate breakage in connectivity")
            self.dr_helper.job_manager.wait_for_state(
                expected_state=['completed w/ one or more errors'],
                retry_interval=120, time_limit=300, hardcheck=True)
            delay_reason = "One or more databases couldn't be backed up to one or more destination."
            if self.dr_helper.job_manager.job.delay_reason:
                if delay_reason not in self.dr_helper.job_manager.job.delay_reason:
                    raise Exception("Delay reason not as expected, the delay reason is {0}"
                                    .format(self.dr_helper.job_manager.job.delay_reason))
            self.log.info("Validation Successful")

        except Exception as exp:
            self.tc.fail(exp)

        finally:
            self.dr_manager.dr_storage_policy = self.existing_dr_policy
            self.dr_helper.dr_prerequisites_cleanup()
            self.dr_helper.kill_running_drjobs()
