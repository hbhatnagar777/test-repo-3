# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
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
    """Class for executing CBT Tests of Hyper-V backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Hyper-V Migrate and Backup Cases with CBT Checks"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            log.info(
                "-------------------Initialize helper objects------------------------------------"
                )
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                                                        auto_client, self.agent, self.instance)
            # auto_instance.FBRMA = "fbrhv"
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            log.info("Set CBT status on the subclient")
            value = auto_subclient.subclient.cbtvalue
            if not value:
                auto_subclient.subclient.cbtvalue = 1
            auto_subclient.check_migrate_vm()
            log.info(
                "----------------------------------------Backup-----------------------------------"
            )
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)

            # """
            log.info(
                "----------------------------------------Perform CBT checks-----------------------------------"
            )
            cbtstat_folder = auto_instance.cbt_checks()
            auto_commcell.check_cbt_status(backup_options.backup_type, self.subclient)
            auto_subclient.create_ini_files()
            auto_subclient.get_changeid_from_metadata(backup_options.backup_type)

            for i in range(31):
                auto_subclient.check_migrate_vm()
                # """
                log.info(
                    "----------------------------------------Backup-----------------------------------"
                    )
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)

                #"""
                log.info(
                    "----------------------------------------Perform CBT checks-----------------------------------"
                )
                cbtstat_folder = auto_instance.cbt_checks()
                auto_commcell.check_cbt_status(backup_options.backup_type, self.subclient)
                auto_subclient.parse_diskcbt_stats(cbtstat_folder, backup_options.backup_type)
                status = auto_subclient.verify_changeid_used(backup_options.backup_type)
                if not status:
                    raise Exception("ChangeID validation failed")
                auto_subclient.get_changeid_from_metadata(backup_options.backup_type)

                log.info(
                    "----------------------------------------File Level restores----------------------"
                     )
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.metadata_collected = backup_options.collect_metadata
                if "FBRMA" in self.tcinputs:
                    fs_restore_options.fbr_ma = self.tcinputs["FBRMA"]
                if "Browse_MA" in self.tcinputs:
                    fs_restore_options.fbr_ma = self.tcinputs["Browse_MA"]
                auto_subclient.guest_file_restore(fs_restore_options)

            # """
            log.info(
                "----------------------------------------Backup-----------------------------------"
            )
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "DIFFERENTIAL"
            auto_subclient.backup(backup_options)

            # """
            log.info(
                "----------------------------------------Perform CBT checks-----------------------------------"
            )
            #cbtstat_folder = auto_instance.cbt_checks()
            auto_commcell.check_cbt_status(backup_options.backup_type, self.subclient)
            auto_subclient.parse_diskcbt_stats(cbtstat_folder, backup_options.backup_type)
            status = auto_subclient.verify_changeid_used(backup_options.backup_type)
            if not status:
                self.log.info("ChangeID validation failed as FULL changeiD got overwritten")
            auto_subclient.get_changeid_from_metadata(backup_options.backup_type)

            log.info(
                "----------------------------------------File Level restores----------------------"
            )
            fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
            fs_restore_options.metadata_collected = backup_options.collect_metadata
            if "Browse_MA" in self.tcinputs:
                fs_restore_options.fbr_ma = self.tcinputs["Browse_MA"]
            if "FBRMA" in self.tcinputs:
                fs_restore_options.fbr_ma = self.tcinputs["FBRMA"]
            auto_subclient.guest_file_restore(fs_restore_options)
            # """

            log.info(
                "----------------------------------------Disk restores----------------------------"
                )
            disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
            auto_subclient.disk_restore(disk_restore_options)

            # """
            # """
            log.info(
                "----------------------------------------FULL VM out of Place restores------------"
                )
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.unconditional_overwrite = True
            auto_subclient.virtual_machine_restore(vm_restore_options)

            # """

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
