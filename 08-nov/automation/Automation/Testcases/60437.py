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


class TestCase(CVTestCase):
    """Class for executing Windows VM - NTFS Live Browse and file level restore using Linux MA - Agentless
       Configuration: Requires Windows Guest VM with NTFS file system and subclient with Linux Proxy
       Can set Different destination client or browse MA through input JSON"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Agentless Restore from Streaming Full Backup"
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
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            VirtualServerUtils.set_inputs(self.tcinputs, backup_options)
            auto_subclient.backup(backup_options)
            VirtualServerUtils.decorative_log("Agentless file restores")
            file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
            VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
            auto_subclient.agentless_file_restore(file_restore_options)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
