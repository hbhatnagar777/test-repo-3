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
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - OpenStack - Disk Level - Full backup using Windows Proxy with CBT checks"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""


    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            self.hvobj = auto_backupset.auto_vsainstance.hvobj
            #------ Set CBT status for the subclient ------
            VirtualServerUtils.decorative_log("Set CBT status on the subclient")
            value = auto_subclient.subclient.cbtvalue
            if not value:
                auto_subclient.subclient.cbtvalue = 1

            #-------- Backup for the subclient -------------
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            for _backup_type in ['FULL', 'INCREMENTAL']:
                backup_options.backup_type = _backup_type
                auto_subclient.backup(backup_options)
                try:
                    VirtualServerUtils.decorative_log(
                        "-" * 25 + " CBT validation for full/incr" + "-" * 25)
                    auto_subclient.verify_cbt_backup(backup_options.backup_type, backup_method='Streaming')
                    auto_subclient.create_ini_files()
                    auto_subclient.get_changeid_from_metadata(backup_options.backup_type)
                except Exception as exp:
                    self.test_individual_status = False
                    self.test_individual_failure_message = str(exp)
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Check if time & backup size taken to complete Incr backup is less than full with CBT " + "-" * 25)
            auto_subclient.check_cbt_backup_sizes(backup_options.backup_type)
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " FULL VM out of Place restores " + "-" * 25)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
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
