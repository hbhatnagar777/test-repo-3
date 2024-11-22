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


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Full Backup and File level Restore for Unix Special configuration " \
                    "for v2 Indexing"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Checking the Details of the VM")
            auto_subclient.validate_inputs("", "", "unix")
            special_vm_drive = auto_subclient.validate_special_vm()

            self.tc_utils.run_backup(self, msg='Streaming Full Backup',
                                     special_vm_drive=special_vm_drive,
                                     testdata_size=(25000, 35000))

            VirtualServerUtils.decorative_log("Guest file restores from vm level")
            for vm in auto_subclient.vm_list:
                self.tc_utils.run_guest_file_restore(self, special_vm_drive=special_vm_drive,
                                                     discovered_client=vm)

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options, special_vm_drive)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
