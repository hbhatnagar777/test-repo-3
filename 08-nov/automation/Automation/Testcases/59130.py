# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
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
from VirtualServer.VSAUtils import OptionsHelper, VMHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper
from AutomationUtils import constants
from AutomationUtils.windows_machine import WindowsMachine
from time import sleep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix Cleaning up snapshot after the backup job is suspended in HotAdd mode"
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.tcinputs = {}


    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            auto_subclient.validate_inputs("windows", "windows")
            try:
                VirtualServerUtils.decorative_log("Getting the name of the proxy machine")
                proxy_name = auto_subclient.auto_vsainstance.co_ordinator
                self.log.info("VSA proxy machine is {}".format(proxy_name))
                auto_subclient.hvobj.VMs = proxy_name
                proxy_vm = auto_subclient.hvobj.VMs[proxy_name]
                before_backup_num_disks = len(proxy_vm.disk_list)
                self.log.info("Number of the disk's attached to proxy machine before the backup job is trigger :{}".format(
                    before_backup_num_disks))
            except Exception as err:
                self.log.error("---Getting name of the proxy machine failed---")
                raise Exception

            VirtualServerUtils.decorative_log("Creating machine object for proxy machine")
            try:
                self.windows_machine = WindowsMachine(proxy_name, self.commcell)
                self.log.info("-----proxy machine connection object created successfully-----")
            except Exception as err:
                self.log.error("-----Failed to create proxy machine connection object-----" + str(err))
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Getting the list of Snapshot's of a VM before backup job")
                source_vm = auto_subclient.vm_list
                auto_subclient.hvobj.VMs = source_vm
                guest_vm = auto_subclient.hvobj.VMs
                specific_vm = guest_vm[source_vm[0]]
                data = specific_vm.get_snapshot()
                snapshot_before_backup = data['metadata']['total_matches']
                self.log.info("Total number of snapshot on a {} VM is : {} ".format(source_vm[0], data['metadata']['total_matches']))
            except Exception as err:
                self.log.error(
                    "---Failed to get the list of snapshot of a vm before the backup---")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Getting the number of disks of a source VM")
                source_vm_num_of_disks = []
                for index in source_vm:
                    source_vm_num_of_disks.append(len(guest_vm[index].disk_list))
                    self.log.info("Number of the disk's guest VM {} have is : {}".format(index, source_vm_num_of_disks))
            except Exception as err:
                self.log.error(
                    "Failed to get the number of disk's of the guest VM:")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Calculating total disk's of the source VM")
                total_guest_disk = sum(source_vm_num_of_disks)
                self.log.info("Total number of disk's of the source/guest VM's is {}".format(total_guest_disk))
            except Exception as err:
                self.log.error(
                    "Failed to get the total number of the disk's of the source VM")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Calculating total disk's will be attach to proxy using Hot Add mode")
                total_proxy_disk = before_backup_num_disks + total_guest_disk
                self.log.info("Total number of disk's will be attach to proxy machine is : {} ".format(total_proxy_disk))
            except Exception as err:
                self.log.error(
                    "Error in calculating total disk's attach to proxy")
                raise Exception

            try:
                self.log.info(
                    "-" * 15 + " FULL  Backup" + "-" * 15)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "FULL"
                auto_subclient.vsa_discovery(backup_options, dict())
                self.log.info("----------Starting Backup Job----------")
                _backup_job = self.subclient.backup(backup_options.backup_type,
                                                    backup_options.run_incr_before_synth,
                                                    backup_options.incr_level,
                                                    backup_options.collect_metadata,
                                                    backup_options.advance_options)

                sleep(30)
                self.log.info("Back Up Job ID = {}".format(_backup_job.job_id))
            except Exception as err:
                self.log.error(
                    "Backup job Failed")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Creating machine object for proxy machine")
                log_file_name = ("vsbkp.log")
                search_term1 = "Saving Cleanup string"
                vsbkp_logline1 = self.windows_machine.get_logs_for_job_from_file(_backup_job.job_id, log_file_name, search_term1)
                self.log.info("-----searched successfully for log lines for Saving Cleanup string -----")
                self.log.info("Search_term1===>{}".format(vsbkp_logline1))
            except Exception as err:
                self.log.error(
                    "-----Failed to search the Saving Cleanup string in vsbkp.log-----")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Checking the disks attach to proxy in Hot Add mode while backup is running")
                index = 0
                while index < 100:
                    sleep(1)
                    proxy_vm.get_disk_config(force_update=True)
                    num_of_disks_proxy_machine = len(proxy_vm.disk_list)
                    self.log.info("Number of disks attached to proxy machine is {}".format(num_of_disks_proxy_machine))
                    if num_of_disks_proxy_machine == total_proxy_disk:
                        self.log.info("All the disk's are attached to proxy machine {}".format(proxy_name))
                        break
                    index += 1
            except Exception as err:
                self.log.error(
                    "-----Failed to get list of the disk attach to proxy-----")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Suspending Backup Job")
                self.log.info("Suspending the backup jobs {}".format(_backup_job.job_id))
                _backup_job.pause(True)
                sleep(10)
            except Exception as err:
                self.log.error(
                    "-----Failed to Kill the backup job-----")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Creating machine object for proxy machine")

                search_term2 = "Removing Cleanup string"
                vsbkp_logline2 = self.windows_machine.get_logs_for_job_from_file(_backup_job.job_id, log_file_name,
                                                                                 search_term2)
                self.log.info("-----searched successfully for log lines for Saving Cleanup string -----")
                sleep(10)
                self.log.info("Search_term2===>{}".format(vsbkp_logline2))

            except Exception as err:
                self.log.exception(
                    "---Failed to search Removing Cleanup string in vsbkp.log---")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Getting the list of the disk's attach to proxy machine after killing the backup job")
                proxy_vm.get_disk_config(force_update=True)
                after_backup_num_disks = len(proxy_vm.disk_list)
                self.log.info("Number of disk's attached to proxy machine after suspending the backup job is {}".format(
                    after_backup_num_disks))

            except Exception as err:
                self.log.exception(
                    "---Failed to get the disk's attached to proxy---")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Checking number of disk's on proxy machine after the killing backup")
                if after_backup_num_disks == before_backup_num_disks:
                    self.log.info("Cleanup of the disk's on proxy machine is successful.")
                else:
                    self.log.info("Cleanup of the disk's did not happen on proxy machine successfully")
            except Exception as err:
                self.log.exception(
                    "---Failed to cleanup the disk's attach to proxy---")
                raise Exception

            try:
                VirtualServerUtils.decorative_log("Getting the list of Snapshot's of a VM after killing the backup job")
                data = specific_vm.get_snapshot()
                self.log.info("Total number of snapshot on a VM after suspending the backup job is : {} ".format(
                    data['metadata']['total_matches']))
                snapshot_after_backup = data['metadata']['total_matches']
                if snapshot_before_backup == snapshot_after_backup:
                    self.log.info("Cleanup of the snapshot on a VM is successful")
                else:
                    self.log.info("Cleanup of the snapshot on a VM is not successful")
                    raise Exception("Cleanup of the snapshot is not successful")
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            
            try:
                self.log.info("killing the suspended backup job")
                _backup_job.kill(True)
                
            except Exception as err:
                self.log.error(
                    "-----Failed to Kill the backup job-----")
                raise Exception

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