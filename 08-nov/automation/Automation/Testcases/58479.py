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
    folder_list     --  return list of folders in specified path
"""
from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix AHV Clean up using NAS mode with Windows Proxy"
        self.test_individual_status = True
        self.tcinputs = {}

    def folder_list(self, lst):
        """
    
        Return the list of the folders in the specified path
    
        Args:
            
            lst (list) -- list of the folder in the specified path

        Returns:

            list - list of the folders in the specified path

        Raises:
    
            Exception - if failed to get the list of folder in specified path
    

        """

        try:
            folderlist = []
            if len(lst) == 0:
                return folderlist
            else:
                for each_path in lst:
                    folderlist.append(each_path.split("\\")[-1])
            return folderlist

        except Exception as err:
            self.log.error("Failed to get the folder list")
            raise Exception(err)

    def run(self):
        """Main function for test case execution"""
    
        try:
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            auto_subclient.validate_inputs("windows", "windows")

            try:
                VirtualServerUtils.decorative_log("Getting the proxy name used for the backup")
                self.proxy_name = auto_subclient.subclient.subclient_proxy
                self.log.info("VSA proxy machine name used for the backup job is %s", self.proxy_name[0])
            except Exception as err:
                self.log.error("Failed to get the proxy machine")
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Creating machine object for proxy machine")
                self.windows_machine = Machine(self.proxy_name[0], self.commcell)
                VirtualServerUtils.decorative_log("proxy machine connection object created successfully")
            except Exception as err:
                self.log.error("Failed to create proxy machine connection object %s", err)
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Checking if NFS path folder exists in proxy machine")
                self.client_obj = self.commcell.clients.get(self.proxy_name[0])
                _job_results = self.client_obj._job_results_directory
                self.nfs_path_ = self.windows_machine.join_path(_job_results.split("iDataAgent")[0], "ProductionData",
                                                                "VSCloudFS")
                self.path_exists = self.windows_machine.check_directory_exists(self.nfs_path_)
                self.log.info("NFS mount path on the proxy machine %s exits = %s", self.proxy_name[0], self.path_exists)
                _paths = self.windows_machine.get_folders_in_path(self.nfs_path_, False)

            except Exception as err:
                self.log.error("Failed to get the NFS path on proxy machine")
                raise Exception(err)

            #NFSMP folder is only created while backup is running so changing NFS path
            self.nfs_path = self.windows_machine.join_path(self.nfs_path_, "NFSMP")

            try:
                VirtualServerUtils.decorative_log("Getting the list of folders in NFS path before the backup job")
                before_folder_list = self.folder_list(_paths)
                self.log.info("Total number of folder's before the backup in the NFS path is %d", len(before_folder_list))
    
            except Exception as err:
                self.log.error("Failed to get the folders from NFS path")
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Getting guest VM Name")
                guest_vm = auto_subclient.hvobj.VMs
                source_vm = auto_subclient.vm_list
                self.log.info("Getting the name of the source vm = %s", source_vm)

            except Exception as err:
                self.log.error("Failed to get the guest VM name---")
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Collecting the container's UUID of the source VM")
                specific_vm = guest_vm[source_vm[0]]
                self.log.info("Getting the container UUID from the source VM %s", source_vm[0])
                container = guest_vm[source_vm[0]].disk_list
                container_uuid =[]
                for index in range(1, len(container)):
                    container_uuid.append((container[index]['containerUuid']))
                self.log.info("Total number of container associated to source VM %s = %d", source_vm[0],len(container_uuid))

                self.log.info("Container_UUID is %s", container_uuid)

            except Exception as err:
                self.log.error("Failed to get the container UUID of the guest VM")
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Getting the name of the container's of the source VM")
                containers = specific_vm.get_container_name(container_uuid)
                self.log.info("Conatiner's name for the source VM is =%s ", set(containers))

            except Exception as err:
                self.log.error("Failed to get the container name of the guest VM---")
                raise Exception(err)

            try:
                self.log.info("Getting the list of Snapshot's of a VM before backup job")
                data = specific_vm.get_snapshot()
                snapshot_before_backup = data['metadata']['total_matches']
                self.log.info("Total number of snapshot on a %s  VM is : %d ", source_vm[0], data['metadata']['total_matches'])

            except Exception as err:
                self.log.error("Failed to get the container name of the guest VM")
                raise Exception(err)

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
                self.log.error("Backup job Failed")
                raise Exception(err)

            try:

                log_file_name = ("vsbkp.log")
                search_term1 = "Saving Cleanup string"
                sleep(30)
                vsbkp_logline1 = self.windows_machine.get_logs_for_job_from_file(_backup_job.job_id, log_file_name, search_term1)
                sleep(60)
                if vsbkp_logline1 is not None:
                    self.log.info("Searched successfully for log lines Saving Cleanup string")
                self.log.info("Search_term1===>%s", vsbkp_logline1)
            except Exception as err:
                self.log.error("Failed to search the string in vsbkp.log")
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Getting the folders list in NFS path")
                paths = self.windows_machine.get_folders_in_path(self.nfs_path, False)
    
                self.log.info("Getting the list of the folders in NFSMP mount path after the containers are mounted %s", paths)
                folder_lst = self.folder_list(paths)
                self.log.info("After mounting the containers list of the folders are {}".format(folder_lst))
                folder_lst = len(paths)
                self.log.info("Total number of folders in NFS path is %d", folder_lst)

                if folder_lst >= len(before_folder_list):
                    self.log.info("Container's is mounted to NFSMP mount path.")
                else:
                    self.log.info("Container's is not mounted to NFS path")
            except Exception as err:
                self.log.error("Failed in getting the NFS folder list")
                raise Exception(err)

            try:
                self.log.info("Killing Backup Job")
                _backup_job.kill(True)
                sleep(10)
            except Exception as err:
                self.log.error("Failed to Kill the backup job")
                raise Exception(err)

            try:
                VirtualServerUtils.decorative_log("Checking for the string Removing Cleanup string in vsbkp.log")
                search_term2 = "Removing Cleanup string"
                vsbkp_logline2 = self.windows_machine.get_logs_for_job_from_file(_backup_job.job_id, log_file_name,search_term2)
                self.log.info("searched successfully for log lines for Saving Cleanup string")

                self.log.info("Search_term2===>%s", vsbkp_logline2)

            except Exception as exp:
                self.log.exception("Failed to search the text in vsbkp.log")
                raise Exception(exp)

            try:
                VirtualServerUtils.decorative_log("---Checking the NFS mount path after the backup job is killed---")
                self.paths = self.windows_machine.get_folders_in_path(self.nfs_path_, False)
                if len(self.paths) == 0:
                    self.log.info("NFS mount path is cleaned up successfully and no contianer's are mounted after killing backup job")
                else:
                    self.log.info("Cleanup of the disk's did not happen on proxy machine and container are still mounted")
            except Exception as exp:
                self.log.exception("Failed to get the NFS folder path-----")
                raise Exception(exp)

            try:
                VirtualServerUtils.decorative_log("Getting the list of Snapshot's of a VM after killing the backup job")
                data = specific_vm.get_snapshot()
                self.log.info("Total number of snapshot on a VM after killing the backup job is : {} "
                              .format(data['metadata']['total_matches']))
                snapshot_after_backup = data['metadata']['total_matches']
                if snapshot_before_backup == snapshot_after_backup:
                    self.log.info("Cleanup of the snapshot on a VM is successful")
                else:
                    self.log.info("Cleanup of the snapshot on a VM is not successful")
                    raise Exception("Cleanup of the snapshot is not successful")

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: {0}:'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
    