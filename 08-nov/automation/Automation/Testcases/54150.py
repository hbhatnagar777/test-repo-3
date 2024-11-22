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
from AutomationUtils import config
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):

    def __init__(self):

        super(TestCase, self).__init__()
        self.name = "Oracle Cloud Infrastructure : Linux proxy SYNTH backup with in-place FULL vm restore"
        self.show_to_user = True
        self.esx_object = None
        self.status = constants.PASSED
        self.result_string = constants.NO_REASON
        self.automation_dir = os.getcwd()
        self.machine_obj = None
        self.user_name = ''
        self.password = ''
        self.clean_up = True
        self.config = config.get_config()
        self.tcinputs = {
            "webconsoleHostname": None,
            "commcellUsername": None,
            "commcellPassword": None,
            "InstanceName": None,
            "key_file_path": None,
            "key_file_password": None
        }

    def setup(self):
        """Setup function of this test case"""
        pass

    def run(self):

        """Run function of this test case"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance, self._tcinputs)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            self.log.info("----------------------------------------Backup-----------------------------------")
            backup_obj = OptionsHelper.BackupOptions(auto_subclient)
            backup_obj.run_incr_before_synth = False
            backup_obj.backup_type = 'SYNTHETIC_FULL'
            self.log.info('Running %s backup' % backup_obj.backup_type)
            auto_subclient.backup(backup_obj)
            # Running inc manually since synthfull flags for running inc are not working for OCI
            backup_obj = OptionsHelper.BackupOptions(auto_subclient)
            backup_obj.backup_type = 'INCREMENTAL'
            self.log.info('Running %s backup' % backup_obj.backup_type)
            auto_subclient.backup(backup_obj)

            self.log.info("----------------------------------------Restore-----------------------------------")
            vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
            vm_restore_options.in_place = True
            vm_restore_options.power_on_after_restore = True
            vm_restore_options.source_vm_details = \
                auto_instance.hvobj.get_vm_details(vm_restore_options.auto_subclient.vm_list[0])
            self.log.info('In place VM Restore starting')
            auto_subclient.virtual_machine_restore(vm_restore_options, indexing_v2=False)
            self.log.info('In place VM Restore finished')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            pass

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info('End of test case')
