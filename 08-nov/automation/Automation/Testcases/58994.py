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
        self.name = "[Negative Case] :  Enable DR backup to cv cloud with no access"
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
            "CloudUserName": None,
            "CloudPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.tc = ServerTestCases(self)
        self.dr_helper = DRHelper(self.commcell)
        self.machine = self.dr_helper.client_machine
        self.dr_manager = self.dr_helper.management

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Creating required prerequisites")
            dr_entities = self.dr_helper.dr_prerequisites()

            self.directory = self.dr_helper.generate_path(self.machine,
                                                          alias='local_path',
                                                          create_path=True)
            self.existing_dr_policy = self.dr_manager.dr_storage_policy
            self.dr_manager.dr_storage_policy = dr_entities['storagepolicy']
            self.dr_manager.set_local_dr_path(path=self.directory)
            self.log.info("Setting up DR cloud")
            self.dr_manager.upload_metdata_to_commvault_cloud(flag=True,
                                                              username=self.tcinputs["CloudUserName"],
                                                              password=self.tcinputs["CloudPassword"])
            self.log.info("Turning on firewall")
            self.machine.start_firewall(block_connections=True)
            self.dr_helper.kill_running_drjobs()
            try:
                self.dr_helper.trigger_dr_backup()
                raise Exception("Backup completed successfully, "
                                "expected to be completed with errors, validation failed")
            except Exception as excp:
                self.log.info("Validation successful, error message as expected [%s]", str(excp))

        except Exception as exp:
            self.tc.fail(exp)

        finally:
            self.log.info("Turning off firewall")
            self.machine.stop_firewall()
            self.dr_manager.dr_storage_policy = self.existing_dr_policy
            self.dr_helper.dr_prerequisites_cleanup()
            if self.machine.check_directory_exists(self.directory):
                self.machine.remove_directory(self.directory)
            self.dr_helper.kill_running_drjobs()
