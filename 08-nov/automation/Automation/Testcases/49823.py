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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VsaTestCaseUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and CBT Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMware Full/Incremental Backup & CBT Restore"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self, skip_min_proxy_os=True)
            self.tc_utils.run_backup(self, backup_type="INCREMENTAL",
                                     skip_min_proxy_os=True)
            _test_data_path1 = self.tc_utils.sub_client_obj.testdata_path
            _timestamp1 = self.tc_utils.sub_client_obj.timestamp

            VirtualServerUtils.decorative_log("Copy Test Data after backup")
            # We're not running Differential backup, but we are copying a Folder called Differential.
            # After Restore, it should not exist in the VM.
            self.tc_utils.sub_client_obj.backup_option.backup_type = "DIFFERENTIAL"
            self.tc_utils.sub_client_obj.backup_folder_name = self.tc_utils.sub_client_obj.backup_option.backup_type
            self.tc_utils.sub_client_obj.backup_option.cleanup_testdata_before_backup = False
            self.tc_utils.sub_client_obj.vsa_discovery(self.tc_utils.sub_client_obj.backup_option, {})
            _test_data_path2 = self.tc_utils.sub_client_obj.testdata_path
            _timestamp2 = self.tc_utils.sub_client_obj.timestamp

            try:
                VirtualServerUtils.decorative_log("Inplace full vm restore")
                self.tc_utils.sub_client_obj.backup_folder_name = "INCREMENTAL"
                self.tc_utils.sub_client_obj.testdata_path = _test_data_path1
                self.tc_utils.sub_client_obj.timestamp = _timestamp1
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(self.tc_utils.sub_client_obj, self)
                if "browse_ma" in self.tcinputs:
                    VirtualServerUtils.set_inputs(self.tcinputs, vm_restore_options)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.in_place_overwrite = True
                self.tc_utils.sub_client_obj.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                raise Exception("Exception during Full VM In-place Restore")

            try:
                VirtualServerUtils.decorative_log("CBT Restore Validation")
                self.log.info("Restore Proxy: %s" % self.tc_utils.sub_client_obj.restore_proxy_client)
                self.tc_utils.sub_client_obj.verify_cbt_restore(vm_restore_options.restore_job.job_id,
                                                                self.tc_utils.sub_client_obj.restore_proxy_client)
                for _vm in self.tc_utils.sub_client_obj.vm_list:
                    self.tc_utils.sub_client_obj.verify_data_pruned(_vm)
            except Exception as exp:
                raise Exception("CBT Validation Failed")

            try:
                VirtualServerUtils.decorative_log("Checked if the data which should be present is present not")
                self.tc_utils.sub_client_obj.backup_folder_name = "DIFFERENTIAL"
                self.tc_utils.sub_client_obj.testdata_path = _test_data_path2
                self.tc_utils.sub_client_obj.timestamp = _timestamp2
                for _vm in self.tc_utils.sub_client_obj.vm_list:
                    drive_list = self.tc_utils.sub_client_obj.hvobj.VMs[_vm].drive_list
                    for drive in drive_list:
                        dest_location = self.tc_utils.sub_client_obj.hvobj.VMs[_vm].machine.join_path(
                            drive_list[drive],
                            self.tc_utils.sub_client_obj.backup_folder_name, "TestData",
                            self.tc_utils.sub_client_obj.timestamp)
                        if self.tc_utils.sub_client_obj.hvobj.VMs[_vm].machine.check_directory_exists(dest_location):
                            raise Exception("{} should not present in the vm".format(dest_location))
                self.log.info(
                    "{} is not present after inplace restore".format(self.tc_utils.sub_client_obj.backup_folder_name))
            except Exception as exp:
                raise Exception("exception on data not to present check")

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.sub_client_obj.backup_option)
                self.tc_utils.sub_client_obj.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
