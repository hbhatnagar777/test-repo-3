# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

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
    """Class for executing Basic acceptance Test of VSA Snap backup and File level Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Full Snap Backup and File level Restore for Windows Special configuration" \
                    "for v2 Indexing"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''
        self.tcinputs = {
            'path_to_million_files': None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            VirtualServerUtils.decorative_log("Checking the Details of the VM")
            auto_subclient.validate_inputs("", "", "windows")
            special_vm_drive, problematic_vm_drive = auto_subclient.validate_special_vm(advanced_config=True,
                                                                                        path_to_million_files=
                                                                                        self.tcinputs[
                                                                                            'path_to_million_files'])

            self.tc_utils.run_backup(self,
                                     advance_options={
                                         'create_backup_copy_immediately': True,
                                         'big_data_size': (2000000, 2500000)},
                                     backup_method='SNAP', special_vm_drive=special_vm_drive,
                                     problematic_vm_drive=problematic_vm_drive,
                                     skip_min_proxy_os=True,
                                     skip_ma_os=True,
                                     skip_min_vm_count=True,
                                     skip_min_vm_os=True,
                                     skip_min_disks_count=True
                                     )

            VirtualServerUtils.decorative_log("Guest file restores from snap from VM level")
            for vm in auto_subclient.vm_list:
                self.tc_utils.run_guest_file_restore(self,
                                                     browse_from_snap=True, special_vm_drive=special_vm_drive,
                                                     problematic_vm_drive=problematic_vm_drive, discovered_client=vm,
                                                     million_files_path=self.tcinputs['path_to_million_files']
                                                     )

            VirtualServerUtils.decorative_log("Guest file restore from backup copy VM level")
            for vm in auto_subclient.vm_list:
                self.tc_utils.run_guest_file_restore(self,
                                                     browse_from_snap=False, browse_from_backup_copy=True,
                                                     special_vm_drive=special_vm_drive,
                                                     problematic_vm_drive=problematic_vm_drive,
                                                     discovered_client=vm,
                                                     million_files_path=self.tcinputs['path_to_million_files']
                                                     )
        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            try:
                cleanup_options = {"special_vm_drive": special_vm_drive, "problematic_vm_drive": problematic_vm_drive}
                auto_subclient.cleanup_testdata(self.tc_utils.backup_options, extra_options=cleanup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
