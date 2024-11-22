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

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants
import time


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware Full Snap backup and Backup copy. Agentless Restore.
    Linux MA, Windows backup vm without metadata collection.
    Configuration: Requires Windows Guest VM with NTFS file system and subclient with Linux Proxy. Can set Different
    destination client or browse MA through input JSON"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Agentless Restore from Snap Backup and Backup Copy"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "destination_client": None,  # Can be Windows or Linux VSA Agent
            "browse_ma": None
        }
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Snap Backup with immediate Backup Copy")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.advance_options = {"create_backup_copy_immediately": True}
            backup_options.backup_method = "SNAP"
            VirtualServerUtils.set_inputs(self.tcinputs, backup_options)
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("Agentless file restore from Snap Backup")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_from_snap = True
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.agentless_file_restore(file_restore_options)
            except Exception as exp:
                self.log.error("sleeping 12 minutes for cleanup of mounted snaps")
                time.sleep(720)
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Agentless file restore from Backup copy")
                file_restore_options.browse_from_snap = False
                file_restore_options.browse_from_backup_copy = True
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.agentless_file_restore(file_restore_options)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)


        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
