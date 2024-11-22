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
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Hyper-V backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Hyper-V VM filter Full backup"
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            filter_string = self.subclient.vm_filter
            if not ((filter_string == "") or (filter_string is None)):
                self.log.info("VM filter is applied , the filter string is {0}".format(filter_string))
            else:
                self.log.info("No VM filter is applied, please add vm filter and rerun the TC")
                raise Exception("No VM filter applied")

            #Take backup of the subclient
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options, msg="Backup")

            VirtualServerUtils.decorative_log("Verify if VM filters are working properly")
            auto_subclient.verify_vmfilter_backedup_vms()

            if "Restore_check" in self.tcinputs and self.tcinputs["Restore_Check"]:
                try:
                    #File level restore
                    fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                    if "FBRMA" in self.tcinputs:
                        fs_restore_options.fbr_ma = self.tcinputs["FBRMA"]
                    if "Browse_MA" in self.tcinputs:
                        fs_restore_options.browse_ma = self.tcinputs["Browse_MA"]
                    auto_subclient.guest_file_restore(fs_restore_options, msg="Files restores")
                except Exception as exp:
                    self.test_individual_status = False
                    self.test_individual_failure_message = str(exp)

                try:
                    #Disk level restore
                    disk_restore_options = OptionsHelper.DiskRestoreOptions(auto_subclient)
                    auto_subclient.disk_restore(disk_restore_options, msg="Disk restores")
                except Exception as exp:
                    self.test_individual_status = False
                    self.test_individual_failure_message = str(exp)

                try:
                    #Full vm Out of Place restore
                    vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                    vm_restore_options.unconditional_overwrite = True
                    auto_subclient.virtual_machine_restore(vm_restore_options, msg="FULL VM out of Place restores")
                except Exception as exp:
                    self.test_individual_status = False
                    self.test_individual_failure_message = str(exp)

            try:
                #Full vm in Place restore
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.in_place_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options, msg="FULL VM in Place restores")
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
