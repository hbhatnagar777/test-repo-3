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
from VirtualServer.VSAUtils import VsaTestCaseUtils, VirtualServerUtils
from AutomationUtils import constants
import time


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware Full Snap backup and Backup copy. Agentbased Restore.
    Linux MA, Windows backup vm without metadata collection.
    Configuration: Requires Windows Guest VM with NTFS file system and subclient with Linux Proxy. Can set Different
    destination client or browse MA through input JSON"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA VMWARE Agentbased Restore from Snap Backup and Backup Copy'
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
            auto_subclient = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self,
                                          advance_options={
                                              'create_backup_copy_immediately': True,
                                              'backup_copy_type': 'USING_LATEST_CYLE'},
                                          backup_method='SNAP')

            try:
                VirtualServerUtils.decorative_log("Agentbased file restore from Snap")
                self.tc_utils.run_guest_file_restore(self,
                                                     browse_from_snap=True)
            except Exception as exp:
                self.log.error("sleeping 12 minutes for cleanup of mounted snaps")
                time.sleep(720)
                self.ind_status = False
                self.failure_msg = str(exp)

            try:
                VirtualServerUtils.decorative_log("Agentbased file restore from Backup Copy")
                self.tc_utils.run_guest_file_restore(self,
                                                     browse_from_snap=False,
                                                     browse_from_backup_copy=True)
            except Exception as exp:
                self.ind_status = False
                self.failure_msg = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(self.backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
