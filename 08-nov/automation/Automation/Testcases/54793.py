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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Agent less restore case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2: VSA VMWARE Agent less restore from streaming"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.ind_status = True
        self.failure_msg = ""
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            if not auto_subclient.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1'
                raise Exception(self.failure_msg)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            VirtualServerUtils.set_inputs(self.tcinputs, backup_options)
            auto_subclient.backup(backup_options)

            try:
                VirtualServerUtils.decorative_log("Agentless file restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                for vm in auto_subclient.vm_list:
                    auto_subclient.agentless_file_restore(file_restore_options, discovered_client=vm)
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