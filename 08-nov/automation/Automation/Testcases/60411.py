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
    __init__()      --  initialize TestCase classuit
    qqq

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Windows VM - NTFS Live Browse and file level restore using Linux MA - Agent Based
       Configuration: Requires Windows Guest VM with NTFS file system and subclient with Linux Proxy
       Can set Different proxy or browse MA through input JSON"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA VMWARE Agentbased Restore from Streaming Full/Incremental/Synthetic Full Backups'
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "destination_client": None, # Can be Windows or Linux VSA Agent
            "browse_ma": None #
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
            VirtualServerUtils.decorative_log("Full Backup")
            self.tc_utils.run_backup(self, msg='Streaming Full Backup')
            VirtualServerUtils.decorative_log("Agentbased file restore from Full")
            self.tc_utils.run_guest_file_restore(self)
            self.tc_utils.run_backup(self, msg='Streaming Incremental Backup',
                                                      backup_type="incremental")
            VirtualServerUtils.decorative_log("Agentbased file restore from Incremental")
            self.tc_utils.run_guest_file_restore(self)
            self.tc_utils.run_backup(self, msg='Streaming Synthetic Full Backup',
                                                      backup_type="SYNTHETIC_FULL")
            VirtualServerUtils.decorative_log("Agentbased file restore from Synthetic Full")
            self.tc_utils.run_guest_file_restore(self)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options)
            except Exception as exp:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                self.log.error(exp)
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
