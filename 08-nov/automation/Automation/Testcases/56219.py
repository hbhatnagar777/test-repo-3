# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for MetadataDrive Replacement"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Hyperscale test class for MetadataDrive Replacement"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for MetaData Drive Replacement"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.result_string = ""
        self.subclient_obj = ""
        self.job_obj = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient = ""
        self.mediaagent = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.clear_information = None
        self.metadata_disk_name = ""
        self.vm_server_name = ""
        self.server_username = ""
        self.server_password = ""
        self.tcinputs = {
            "Storage_Pool_Name": None,
            "username": None,
            "password": None,
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
            },
            "SqlSaPassword": None,
            "SqlLogin": None,
            "MetaData_Disk": None,
            "VM_Server": None,
            "Server_username": None,
            "Server_password": None,
        }

    def setup(self):
        """Initializes test case variables"""
        self.username = self.tcinputs["username"]
        self.password = self.tcinputs["password"]
        self.mediaagent = self.commcell.commserv_name
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        for node in self.control_nodes:
            self.mas.append(self.control_nodes[node])
        self.storage_pool_name = self.tcinputs["Storage_Pool_Name"]
        self.sql_sq_password = self.tcinputs["SqlSaPassword"]
        self.sql_login = self.tcinputs["SqlLogin"]
        self.client = self.commcell.clients.get(self.mediaagent)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset = self.agent.backupsets.get("defaultBackupSet")
        self.subclient = self.id + "_subclient"
        self.policy_name = self.id + "_Policy1"
        self.metadata_disk_name = self.tcinputs["MetaData_Disk"]
        self.vm_server_name = self.tcinputs["VM_Server"]
        self.server_username = self.tcinputs["Server_username"]
        self.server_password = self.tcinputs["Server_password"]
        self.metadata_disk_name = self.tcinputs["MetaData_Disk"]
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        time.sleep(30)
        self.log.info("Deleting policy and sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)

    def run(self):
        try:
            self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
            self.log.info("\n\t\t************************** \n\t\t%s\n\t\t ************************** ", self.name)
            status = self.hyperscale_helper.check_if_storage_pool_is_present(self.storage_pool_name)
            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)

            self.log.info("Number of nodes in the current storage pool = %s", str(len(rows)))

            if status is True:
                self.log.info("Storage pool : %s already present, attempting deletion", self.storage_pool_name)
                self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                             self.sql_login, self.sql_sq_password)
                time.sleep(30)
            else:
                self.log.info(
                    "Storage pool : %s is not present", self.storage_pool_name)
            # Create a fresh storage pool
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            status, response = self.hyperscale_helper.create_storage_pool(self.storage_pool_name,
                                                                          self.ma1, self.ma2, self.ma3)

            self.log.info("storage pool %s not valid with status %s ", self.storage_pool_name, status)
            self.log.info(response)

            if status is False:
                raise Exception("Storage Pool creation failed")
            self.log.info("Storage Pool creation Successful")

            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)

            self.log.info("Number of nodes in the current storage pool = %s ", str(len(rows)))
            self.log.info("Current storage pool contains the following nodes: ")
            for row in rows:
                self.log.info(row[0])
            self.log.info("\nMetaData Drive replacement would be carried on %s\n", self.ma1)

            glus_info_before = self.hyperscale_helper.gluster_vol_info(self.ma1)
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
            self.log.info("**************RUNNING BACKUP JOB ******************")
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(library_id)[
                                                                     2],
                                                                 self.ma1, global_policy_name=
                                                                 self.hyperscale_helper.get_policy_details(gdsp)[2])
                self.log.info("Created Policy %s", self.policy_name)
            else:
                self.log.info("Policy exists")
                self.policy = self.commcell.storage_policies.get(self.policy_name)
            # Creating sub client
            self.log.info("Creating sub client %s if not exists", self.subclient)
            if not self.backupset.subclients.has_subclient(self.subclient):
                self.log.info("Subclient not exists, Creating %s", self.subclient)
                self.subclient_obj = self.backupset.subclients.add(self.subclient,
                                                                   self.policy.storage_policy_name)
                self.log.info("Created sub client %s", self.subclient)
                # Content
                self.subclient_obj.content = [self.tcinputs["Content"]]
            else:
                self.log.info("Sub Client exists")
                self.subclient_obj = self.backupset.subclients.get(self.subclient)
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)

            self.log.info("Job status %s", self.job_obj.status)
            job_id = self.job_obj.job_id
            row1 = self.hyperscale_helper.bkp_job_details(job_id)
            row2 = self.hyperscale_helper.admin_job_details(job_id)
            self.log.info(row1)
            self.log.info(row2)
            self.log.info("Getting ddb information from node %s for metadata drive replacement", self.ma1)
            ma = Machine(self.ma1, self.commcell)
            commands = ["ls -l /ws/ddb", "lsblk | grep 'lvm'",
                        "vgdisplay", "lvdisplay metadatavg"]
            for command in commands:
                self.log.info(command)
                output = ma.execute_command(command)
                if output.exception:
                    self.log.error("Check ddb structure for node %s", self.ma1)
                    raise Exception("DDB structure not proper check")
                self.log.info(output.output)
            jobs_running = 0
            for media_agent in rows:
                jobs_running += len(self.commcell.job_controller.active_jobs(media_agent[0]))
            jobs_running += len(self.commcell.job_controller.active_jobs(self.mediaagent))
            if jobs_running > 0:
                raise Exception("Jobs are running on nodes, make sure no active jobs are running on Storage")
            self.log.info("No jobs running on Storage and MA")
            self.log.info("Identifying disks available for node %s", self.ma1)
            disk_before = []
            disk_before += self.hyperscale_helper.disk_for_vertical_scaleout(self.ma1, self.storage_pool_name)
            for disk in disk_before:
                self.log.info(disk)
            vm = self.hyperscale_helper.get_vm_object(self.vm_server_name, self.server_username, self.server_password,
                                                      self.ma1)
            disk_size = 0
            for device in vm.vm_obj.config.hardware.device:
                if type(device).__name__ == 'vim.vm.device.VirtualDisk' and \
                        device.deviceInfo.label == self.metadata_disk_name:
                    disk_size = int(device.deviceInfo.summary.lower().replace("kb", '')
                                    .replace(" ", '').replace(",", "")) // (1024 * 1024)
            self.log.info("Size for MetaData disk %s is %s", self.metadata_disk_name, disk_size)
            self.log.info("Powering off the Vm %s", self.ma1)
            vm.vm_obj.PowerOff()
            time.sleep(120)
            self.log.info("Removing the meta data disk %s from vm %s", self.metadata_disk_name, self.ma1)
            vm.delete_disks(self.metadata_disk_name)
            time.sleep(120)
            self.log.info("Adding disk for replacement")
            vm.add_disks(disk_size)
            time.sleep(120)
            self.log.info("Powering on and restarting vm")
            vm.vm_obj.PowerOn()
            time.sleep(300)
            ma_session = Machine(self.ma1, self.commcell)
            mount = r"df -h | grep '/ws/ddb' | awk '{print $1}'"
            mount_output = ma_session.execute_command(mount)
            if not mount_output.output:
                self.log.error("No mount path for /ws/ddb over %s ", self.ma1)

            commands = ["ls -l /ws/ddb", "lsblk | grep 'lvm'",
                        "vgdisplay", "lvdisplay metadatavg"]
            for command in commands:
                self.log.info(command)
                output = ma.execute_command(command)
                if output.exception:
                    self.log.error("Check ddb structure for node %s", self.ma1)
                self.log.info(output.output)
            disk_after = []
            disk_after += self.hyperscale_helper.disk_for_vertical_scaleout(self.ma1, self.storage_pool_name)
            for disk in disk_after:
                self.log.info(disk)
            metadata_replace_disk = []
            for disk in disk_after:
                if disk not in disk_before:
                    metadata_replace_disk += disk
                    break
            command = "lsblk | grep '{0}'".format(metadata_replace_disk[0].replace('/dev/', ''))
            self.log.info(command)
            output = ma_session.execute_command(command)
            self.log.info(output)
            add_disk_size = output.formatted_output.split()[3]
            add_disk_size = int(''.join(list(value for value in add_disk_size if value.isdigit())))
            if add_disk_size != disk_size:
                self.log.error("Added disk size not same %s != %s", disk_size, add_disk_size)
                raise Exception("Added disk size not same")
            self.log.info("Size of added disk is same %s = %s", disk_size, add_disk_size)
            self.log.info("Triggering metadata replace")
            command = "echo \"y\" | (cd /opt/commvault/Base && ./CVSDS -m -l {0})".format(metadata_replace_disk[0])
            ma_session = Machine(self.ma1, self.commcell)
            self.log.info(command)
            output = ma_session.execute_command(command)
            self.log.info(output.output)
            time.sleep(120)
            self.log.info("Cehecking mount status for the metadata drive on node %s", self.ma1)
            if not ma_session.is_path_mounted("/ws/ddb"):
                raise Exception("Check CVWebScale.log for metadata drive replace mount failure")
            mount = r"df -h | grep '/ws/ddb' | awk '{print $1}'"
            mount_output = ma_session.execute_command(mount)
            if not mount_output.output:
                self.log.error("No mount path for /ws/ddb over %s ", self.ma1)

            commands = ["ls -l /ws/ddb", "lsblk | grep 'lvm'",
                        "vgdisplay", "lvdisplay metadatavg"]
            for command in commands:
                self.log.info(command)
                output = ma.execute_command(command)
                if output.exception:
                    self.log.error("Check ddb structure for node %s", self.ma1)
                self.log.info(output.output)
            self.log.info("Partition status")
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            partition = storage_pool_details._storage_pool_properties['storagePoolDetails']['dedupDBDetailsList'][
                0]['reserveField7']
            self.log.info(partition)
            self.log.info("Marking partions for recovery")
            dedup_engine = self.commcell.deduplication_engines.get(self.storage_pool_name, 'primary')
            all_stores = dedup_engine.all_stores
            for store in all_stores:
                sub_store = dedup_engine.get(int(store[0]))
                partition_store = sub_store.all_substores
                for partition in partition_store:
                    part = sub_store.get(int(partition[0]))
                    self.log.info("Marking for recovery %s", part)
                    part.mark_for_recovery()
            self.log.info("waiting 30 mins for DDB reconstruction to be triggered, with checking in interval of 5min")
            count = 7
            status = False
            job = []
            while count >= 0:
                status, job = self.hyperscale_helper.get_ddb_reconstruction_job(self.storage_pool_name)
                if status:
                    if int(job[1]) == 2:
                        raise Exception("Reconstruction job Failed, check ScalableDDBRecovery.log/DDBRecovery.log logs")
                    if int(job[1]) == 1:
                        self.log.info("Reconstruction job completed successfully")
                        break
                count -= 1
                time.sleep(300)
            if status is False:
                raise Exception("Recon job Not triggered/ failed due to some reason,"
                                " check ScalableDDBRecovery.log/DDBRecovery.log logs")
            if status:
                self.log.info("Reconstruction job completed successfully")
                job = self.commcell.job_controller.get(int(job[0]))
                self.log.info(job.summary)
            glus_info_after = self.hyperscale_helper.gluster_vol_info(self.ma1)
            glus_size_staus = self.hyperscale_helper.verify_replace_gluster_size(glus_info_before, glus_info_after)
            if not glus_size_staus:
                self.log.info("Gluster size not same after replacement")

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
