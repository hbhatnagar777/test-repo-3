# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - OpenStack - Disk Level - Full backup using Windows Proxy"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info(
                "-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)

            try:
                self.log.info(
                    "-" * 25 + " Files restores " + "-" * 25)
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                auto_subclient.guest_file_restore(file_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            # try:
                # log.info(
                #     "-" * 25 + " Disk restores " + "-" * 25)
                # disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
                # auto_subclient.disk_restore(disk_restore_options)
                #
            # except Exception as exp:
            #     self.test_individual_status = False
            #     self.test_individual_failure_message = str(exp)
            #
            try:
                self.log.info(
                    "-" * 15 + " FULL VM out of Place restores " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                self.log.info(
                    "-" * 15 + " FULL VM inPlace restores " + "-" * 15)
                # vm_restore_options.in_place_overwrite = True
                # auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
               self.result_string = self.test_individual_failure_message
               self.status = constants.FAILED