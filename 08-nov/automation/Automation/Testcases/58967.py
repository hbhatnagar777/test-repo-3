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
from datetime import datetime
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
        self.name = "[Negative Case] : Update DR backup path"
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

            self.directory = self.dr_helper.generate_path(self.dr_helper.client_machine, alias='local_path')
            self.log.info("Creating local directory")
            self.dr_helper.client_machine.create_directory(directory_name=self.directory)
            self.dr_manager.set_local_dr_path(path=self.directory)
            self.log.info("Removing local directory before job is triggered")
            self.dr_helper.client_machine.remove_directory(directory_name=self.directory)
            self.dr_helper.kill_running_drjobs()
            self.dr_helper.trigger_dr_backup()
            self.log.info("DR Backup job was successful, deleting the backed up dumps")
            self.dr_helper.client_machine.remove_directory(directory_name=self.directory)

            self.log.info("Creating and sharing the directory")
            share_path = self.dr_helper.generate_path(self.machine, alias='share', create_path=True)
            share_name = share_path.split("\\")[-1]
            self.machine.share_directory(share_name=share_name, directory=share_path)
            network_path = "\\\\{0}\\{1}".format(self.machine.machine_name, share_name)

            self.log.info("Setting network path {0} as destination path".format(network_path))
            self.dr_manager.set_network_dr_path(path=network_path, username=self.tcinputs["UncUser"],
                                                password=self.tcinputs["UncPassword"])
            self.log.info("Unsharing it before job is triggered")
            self.machine.unshare_directory(share_name=share_name)
            self.dr_helper.kill_running_drjobs()
            try:
                self.dr_helper.trigger_dr_backup()
                raise Exception("Backup completed successfully, "
                                "expected to be completed with errors, validation failed")
            except Exception as excp:
                delay_reason = "One or more databases couldn't be backed up to one or more destination."
                if self.dr_helper.job_manager.job.delay_reason:
                    if delay_reason not in self.dr_helper.job_manager.job.delay_reason:
                        raise Exception("Delay reason not as expected, the delay reason is {0}"
                                        .format(self.dr_helper.job_manager.job.delay_reason))
                self.log.info("Validation successful, error message as expected [%s]", str(excp))

        except Exception as exp:
            self.tc.fail(exp)

        finally:
            self.dr_manager.dr_storage_policy = self.existing_dr_policy
            self.dr_helper.dr_prerequisites_cleanup()
            self.dr_helper.kill_running_drjobs()
