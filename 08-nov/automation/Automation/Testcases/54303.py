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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import time
import random
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Gluster/DDB Failure Scenarios for HyperScale"
        self.result_string = ""
        self.policy = ""
        self.policy_name = ""
        self.subclient_obj = ""
        self.job_obj = None
        self.username = ""
        self.password = ""
        self.client = ""
        self.media_agent = ""
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.node1 = ""
        self.node2 = ""
        self.node3 = ""
        self.brick1 = ""
        self.brick2 = ""
        self.brick3 = ""
        self.device_os_path1 = ""
        self.device_os_path2 = ""
        self.device_os_path3 = ""
        self.vm_server_name = ""
        self.server_username = ""
        self.server_password = ""
        self.tcinputs = {
            "username": None,
            "password": None,
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None
            },
            "Storage_Pool_Name": None,
            "SqlLogin": None,
            "SqlSaPassword": None,
            "VM_Server": None,
            "Server_username": None,
            "Server_password": None,
        }
        self.disk_id1 = 0
        self.disk_id2 = 0
        self.node_id1 = ""
        self.node_id2 = ""
        self.node_id3 = ""
        self.sub_vol = ""
        self.sub_vol_replace = ""
        self.hyperscale_helper = None
        self.restore_path = ""
        self.time_off = 30*60
        self.subclients = []
        self.subclients_obj = []
        self.jobs = []
        self.query_results = []
        self.volumes = set()
        self.lib_folder = ""
        self.ws_folder = ""

    def setup(self):
        """
        Setup function of this test case
        Initializes test case variables
        """
        self.username = self.tcinputs["username"]
        self.password = self.tcinputs["password"]
        self.media_agent = self.commcell.commserv_name
        self.storage_pool_name = self.tcinputs["Storage_Pool_Name"]
        self.sql_sq_password = self.tcinputs["SqlSaPassword"]
        self.sql_login = self.tcinputs["SqlLogin"]
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        for node in self.control_nodes:
            self.mas.append(self.control_nodes[node])
        self.vm_server_name = self.tcinputs["VM_Server"]
        self.server_username = self.tcinputs["Server_username"]
        self.server_password = self.tcinputs["Server_password"]
        # Backup objects
        self.client = self.commcell.clients.get(self.media_agent)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset = self.agent.backupsets.get("defaultBackupSet")
        self.subclient = self.id + "_subclient"
        for index in range(1, 10):
            sub = self.id + "subclient" + str(index)
            self.subclients.append(sub)
        self.policy_name = self.id + "_Policy1"
        self.restore_path = self.tcinputs["Content"] + self.id + "_restore"
        self.mmhelper_obj = MMHelper(self)
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def backup(self):
        for index in range(1, 10):
            self.mmhelper_obj.create_uncompressable_data(self.media_agent,
                                                         self.tcinputs["Content"] + str(index), 2)
        storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
        library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
            'library']['libraryId']
        gdsp = storage_pool_details.storage_pool_id
        self.log.info("**************RUNNING BACKUP JOB BEFORE REPLACEMENT******************")
        self.log.info("Creating Policy")
        self.policy_name = self.id + "_Policy1"
        if not self.commcell.storage_policies.has_policy(self.policy_name):
            self.log.info("Policy not exists, Creating %s", self.policy_name)
            self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                             self.hyperscale_helper.get_library_details(
                                                                 library_id)[2],
                                                             self.ma1, global_policy_name=
                                                             self.hyperscale_helper.get_policy_details(gdsp)[2])
            self.log.info("Created Policy %s", self.policy_name)
        else:
            self.log.info("Policy exists")
            self.policy = self.commcell.storage_policies.get(self.policy_name)
        # Creating sub client
        for index in range(1, 10):
            if not self.backupset.subclients.has_subclient(self.subclient + str(index)):
                self.log.info("Subclient not exists, Creating %s", self.subclient + str(index))
                self.subclients.append(self.subclient + str(index))
                subclient_obj = self.backupset.subclients.add(self.subclient + str(index),
                                                              self.policy.storage_policy_name)
                self.log.info("Created sub client %s", self.subclient + str(index))
                # Content
                subclient_obj.content = [self.tcinputs["Content"] + str(index)]
                self.subclients_obj.append(subclient_obj)
            else:
                self.log.info("Sub Client exists")
                subclient_obj = self.backupset.subclients.get(self.subclient + str(index))
                subclient_obj.content = [self.tcinputs["Content"] + str(index)]
                self.subclients_obj.append(subclient_obj)
        for index in range(0, 9):
            self.jobs.append(self.subclients_obj[index].backup())
            self.log.info("Backup Job(Id: %s) Started ", self.jobs[index].job_id)
        for index in range(0, 9):
            if not self.jobs[index].wait_for_completion():
                self.log.error("Job(Id: %s) failed ", self.jobs[index].job_id)
                raise Exception("Baclup Job Failed")
            self.log.info("Job(Id: %s) status %s ", self.jobs[index].job_id, self.jobs[index].status)

    def run(self):
        """Run function of this test case
            Replacing healthy Disk
        """
        try:
            self.log.info("\n*************Gluster/DDB Failure Scenarios for HyperScale**************\n")
            self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
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
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            status, response = self.hyperscale_helper.create_storage_pool(self.storage_pool_name,
                                                                          self.ma1, self.ma2, self.ma3)

            status = False
            attempts = 5
            while status is False and attempts != 0:
                status = self.hyperscale_helper.check_if_storage_pool_is_present(self.storage_pool_name)
                if status is False:
                    self.log.info("Storage pool not present, waiting for entry to be added")
                time.sleep(30)
                attempts = attempts - 1
            if status is False:
                raise Exception("Storage Pool creation failed")
            self.log.info("Storage Pool creation Successful")
            self.backup()

            nodes = self.hyperscale_helper.get_all_nodes_hostids(self.storage_pool_name)
            self.log.info("All node ids associated with pool are %s", nodes)
            self.log.info("\n\t*******************Disk Corruption case*****************\n\t")
            self.log.info("Getting volume information for the jobs in %s", self.jobs)
            self._log.info("Getting the List of Volumes")
            for index in range(0, 9):
                query = '''select
                            Folder,MMMountPath.MountPathName, MMVolume.VolumeName, archChunk.id
                        from
                            archFile,archChunkMapping, archChunk,MMVolume, MMMountPath,
                            MMMountPathToStorageDevice, MMDeviceController
                        where
                            archFile.jobId = {0}
                            and archFile.id = archChunkMapping.archFileId
                            and archChunkMapping.archChunkId = archChunk.id
                            and archChunk.volumeId = MMVolume.VolumeId
                            and MMVolume.CurrMountPathId = MMMountPath.MountPathId
                            and MMMountPath.MountPathId = MMMountPathToStorageDevice.MountPathId
                            and MMMountPathToStorageDevice.DeviceId = MMDeviceController.DeviceId
                        '''.format(self.jobs[index].job_id)
                self.csdb.execute(query)
                self.query_results.append(self.csdb.fetch_all_rows())
            self.lib_folder = self.query_results[0][0][1]
            self.log.info("Library folder %s", self.lib_folder)
            self.ws_folder = self.query_results[0][0][0]
            for query_data in self.query_results:
                query_out = query_data
                for data in query_out:
                    self.volumes.add(data[2])
            volume_list = list(self.volumes)
            for vol in volume_list:
                self.log.info("Volume Folder for job are %s ", vol)
            vm = self.hyperscale_helper.get_vm_object(self.vm_server_name, self.server_username, self.server_password,
                                                      self.ma1)
            self.log.info("Turning on/off vm %s to release any locks on V_ folders", self.ma1)
            self.log.info("Powering off the Vm %s", self.ma1)
            vm.vm_obj.PowerOff()
            time.sleep(120)
            self.log.info("Powering on and restarting vm")
            vm.vm_obj.PowerOn()
            time.sleep(300)
            ma_session = Machine(self.ma1, self.commcell)
            location = "/ws/disk1/ws_brick/" + self.lib_folder + "/CV_MAGNETIC/"
            for vol in volume_list:
                self.log.info("removing V_ folder %s from /ws/disk1 on ma %s", vol, self.ma1)
                command = "rm -rf " + location + vol
                self.log.info(command)
                ma_session.execute_command(command)
            self.log.info("Wait for healing to complete and recover lost Volume folders")
            count = 10
            status = True
            while count > 0:
                time.sleep(self.time_off)
                ma_session = Machine(self.ma1, self.commcell)
                command = "ls " + location + " | grep 'V_'"
                self.log.info(command)
                output = ma_session.execute_command(command)
                for volume in volume_list:
                    if [volume] not in output.formatted_output:
                        status = False
                count -= 1
                if not status:
                    self.log.info("All volume folders not recovered yet wait for healing to complete")
                else:
                    self.log.info("All volume folders recovered and healing complete")
                    break
            heal_entries = self.hyperscale_helper.gluster_heal_entries(self.ma1, self.storage_pool_name)
            if not heal_entries:
                self.log.error("Healing not complete after wait time, please check")
                raise Exception("Healing not complete after wait time, please check")
            self.log.info("Heal entries 0, healing complete, status %s", heal_entries)

            self.log.info("\n******************Kill Brick daemons under Resdundancy Factor*********************\n")
            # Getting node and disks of same sub volume for simultaneous replacement
            self.log.info("getting disks of sub volume to hit RF")
            self.sub_vol = self.hyperscale_helper.get_subvolume_for_pool(self.storage_pool_name)
            subvol = random.sample(self.sub_vol, 1)
            self.sub_vol_replace = subvol[0][0]
            self.log.info("Sub volume for disk replacement is %s", self.sub_vol_replace)
            bricks = self.hyperscale_helper.get_all_bricks_for_subvolume(self.sub_vol_replace)
            # Getting 2 random bricks of same subvolume
            replace_bricks = random.sample(bricks, 3)
            self.brick1 = replace_bricks[0]
            self.brick2 = replace_bricks[1]
            self.brick3 = replace_bricks[2]
            self.log.info("Bricks of sub volume %s for replacement are %s ", self.sub_vol_replace, replace_bricks)
            self.node_id1, self.node_id2, self.node_id3 = str(self.brick1[4]), str(self.brick2[4]), str(self.brick3[4])

            self.node1, self.node2, self.node3 = self.hyperscale_helper.get_hostname(self.node_id1), \
                                                 self.hyperscale_helper.get_hostname(self.node_id2), \
                                                 self.hyperscale_helper.get_hostname(self.node_id3)

            self.device_os_path1, self.device_os_path2, self.device_os_path3 = str(self.brick1[3]), \
                                                                               str(self.brick2[3]), \
                                                                               str(self.brick3[3])
            self.log.info("Nodes are node1 %s, hostid %s and node2 %s, hostid %s and self.node3 %s, hostid %s ",
                          self.node1, self.node_id1,
                          self.node2, self.node_id2,
                          self.node3, self.node_id3)

            # NO NEED TO CHECK -----(checking brick part of node)----ALREADY PART OF POOL FROM SUB VOLUME
            self.log.info("device_os_path1: %s and device_os_path2: %s and self.device_os_path3: %s",
                          self.device_os_path1, self.device_os_path2, self.device_os_path3)
            self.disk_id1, self.disk_id2, disk_id3 = self.brick1[6], self.brick2[6], self.brick3[6]
            self.log.info("\nDisk id %s for brick %s\nDisk id %s for brick %s\nDisk id %s for brick %s ",
                          self.disk_id1, self.device_os_path1,
                          self.disk_id2, self.device_os_path2,
                          disk_id3, self.device_os_path3)

            self.log.info("--------checking bricks part of pool and glusters and "
                          "Checking brick health of bricks being replaced-------")
            self.hyperscale_helper.check_gluster_brick_online(self.node1, self.storage_pool_name,
                                                              self.device_os_path1)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id1, self.device_os_path1)

            self.hyperscale_helper.check_gluster_brick_online(self.node2, self.storage_pool_name,
                                                              self.device_os_path2)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id2, self.device_os_path2)

            self.hyperscale_helper.check_gluster_brick_online(self.node3, self.storage_pool_name,
                                                              self.device_os_path3)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id3, self.device_os_path3)

            # Getting gluster size info before
            glus_info_before = self.hyperscale_helper.gluster_vol_info(self.node1)
            # Check flag status
            self.log.info("flag status before backup and un-mount")
            flag1 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id1, device_os=self.device_os_path1)
            flag2 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id2, device_os=self.device_os_path2)

            # Un Mounting disk
            self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path1)
            self.hyperscale_helper.unmount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
            flag1 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id1, device_os=self.device_os_path1)
            count = 20
            while not flag1 & 16 and count >= 0:
                self.log.info("waiting to reflect offline for disk %s", self.device_os_path1)
                flag1 = self.hyperscale_helper.brick_flag_status(self.node_id1, self.device_os_path1)
                count -= 1
                time.sleep(120)
            self.log.info("Disk %s offline", self.device_os_path1)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id1, self.device_os_path1)
            self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path2)
            self.hyperscale_helper.unmount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
            flag2 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id2,
                                                             device_os=self.device_os_path2)
            count = 20
            while not flag2 & 16 and count >= 0:
                self.log.info("waiting to reflect offline for disk %s", self.device_os_path2)
                flag2 = self.hyperscale_helper.brick_flag_status(self.node_id2, self.device_os_path2)
                count -= 1
                time.sleep(120)
            self.log.info("Disk %s offline", self.device_os_path2)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id2, self.device_os_path2)
            # Running backup
            self.log.info("---------------------------TRIGGERING A BACKUP JOB BEFORE ------------------------")
            # Running backup job before replacement
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
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
                self.subclient_obj.content = [self.tcinputs["Content"]]
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)

            self.log.info("Job status %s", self.job_obj.status)
            self.log.info("Re mounting all the disks back")
            self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
            self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
            self.log.info("Waiting after remounting of disks")
            time.sleep(200)
            # Check gluster  entries for heal on any node
            if not self.hyperscale_helper.gluster_heal_entries(self.node1, self.storage_pool_name):
                self.log.info("Entries not zero yet")
            else:
                self.log.info("heal success and entries 0 now")
            self.log.info("Running DV2 job")
            policy_obj = self.commcell.storage_policies.get(self.storage_pool_name)
            if policy_obj is not None:
                dv_job1 = policy_obj.run_ddb_verification("Primary", "Full", "DDB_VERIFICATION")
                if dv_job1.wait_for_completion():
                    self.log.info("Job status %s", self.job_obj.status)
            else:
                raise Exception("No policy object created for DV2 job")

            self.log.info("\n*************Bringing brick daemons down while backup***********\n")
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)
            while True:
                if self.job_obj.phase == 'Backup':
                    # Un Mounting disk
                    self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path1)
                    self.hyperscale_helper.unmount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
                    flag1 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id1,
                                                                     device_os=self.device_os_path1)
                    count = 20
                    while not flag1 & 16 and count >= 0:
                        self.log.info("waiting to reflect offline for disk %s", self.device_os_path1)
                        flag1 = self.hyperscale_helper.brick_flag_status(self.node_id1, self.device_os_path1)
                        count -= 1
                        time.sleep(120)
                    self.log.info("Disk %s offline", self.device_os_path1)
                    self.hyperscale_helper.gluster_healthy_brick_status(self.node_id1, self.device_os_path1)
                    time.sleep(120)
                    self.log.info("Re mounting disks %s back and observe healing", self.device_os_path1)
                    self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
                    # Check gluster  entries for heal on any node
                    if not self.hyperscale_helper.gluster_heal_entries(self.node1, self.storage_pool_name):
                        self.log.info("Entries not zero yet")
                    else:
                        self.log.info("heal success and entries 0 now")
                    self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path2)
                    self.hyperscale_helper.unmount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
                    flag2 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id2,
                                                                     device_os=self.device_os_path2)
                    count = 20
                    while not flag2 & 16 and count >= 0:
                        self.log.info("waiting to reflect offline for disk %s", self.device_os_path2)
                        flag2 = self.hyperscale_helper.brick_flag_status(self.node_id2, self.device_os_path2)
                        count -= 1
                        time.sleep(120)
                    self.log.info("Disk %s offline", self.device_os_path2)
                    self.hyperscale_helper.gluster_healthy_brick_status(self.node_id2, self.device_os_path2)
                    self.log.info("Re mounting disks %s back and observe healing", self.device_os_path2)
                    self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
                    # Check gluster  entries for heal on any node
                    if not self.hyperscale_helper.gluster_heal_entries(self.node2, self.storage_pool_name):
                        self.log.info("Entries not zero yet")
                    else:
                        self.log.info("heal success and entries 0 now")
                    break
                self.log.info("Job status %s", self.job_obj.status)
                time.sleep(120)
                if self.job_obj.status == "Completed":
                    break
                if self.job_obj.status == "Failed":
                    break
            self.log.info("Job status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            self.log.info("Running DV2 job")
            policy_obj = self.commcell.storage_policies.get(self.storage_pool_name)
            if policy_obj is not None:
                dv_job1 = policy_obj.run_ddb_verification("Primary", "Full", "DDB_VERIFICATION")
                if dv_job1.wait_for_completion():
                    self.log.info("Job status %s", self.job_obj.status)
            else:
                raise Exception("No policy object created for DV2 job")

            self.log.info("\n*************Bringing down 2 nodes to make Storage Pool Offline*************\n")
            self.hyperscale_helper.ma_service_down(self.ma1)
            self.hyperscale_helper.ma_service_down(self.ma2)
            self.log.info("Additional wait time to reflect offline")
            time.sleep(self.time_off)
            status = self.hyperscale_helper.wait_for_completion(self.storage_pool_name)
            if not status:
                self.log.info("storage pool %s is offline", self.storage_pool_name)
            self.log.info("Storage POOL %s Online", self.storage_pool_name)
            self.log.info("Validating ddb partitions")
            self.hyperscale_helper.validate_dedup_store(gdsp)
            self.log.info("Partition status")
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            partition = storage_pool_details._storage_pool_properties['storagePoolDetails']['dedupDBDetailsList'][
                0]['reserveField7']
            self.log.info(partition)
            self.hyperscale_helper.ma_service_up(self.ma1)
            self.hyperscale_helper.ma_service_up(self.ma2)
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)

            self.log.info("\n*****************Restarting gluster daemon while backup*****************\n")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)
            while True:
                if self.job_obj.phase == 'Backup':
                    self.log.info("Restarting gluster to get brick online")
                    ma_session = Machine(self.ma1, self.commcell)
                    gluster_name = self.hyperscale_helper.gluster_name_for_storage_pool(self.storage_pool_name)
                    # Run echo "y" | gluster v stop storage_pool_name
                    stop_command = "echo \"y\" | gluster v stop " + str(gluster_name)
                    self.log.info(stop_command)
                    output = ma_session.execute_command(stop_command)
                    self.log.info(output.output)
                    time.sleep(120)
                    self.log.info(" backup job, status %s", self.job_obj.status)
                    # gluster v start storage_pool_name
                    start_command = "gluster v start " + str(gluster_name) + " force"
                    self.log.info(start_command)
                    output = ma_session.execute_command(start_command)
                    self.log.info(output.output)
                    time.sleep(120)
                    self.log.info(" backup job, status %s", self.job_obj.status)
                if self.job_obj.status == "Completed":
                    break
                if self.job_obj.status == "Failed":
                    break
            self.log.info("Job status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)

            self.log.info("\n************Killing one MA and running backups and "
                          "perform DV2 after node online************\n")
            self.hyperscale_helper.ma_service_down(self.ma1)
            self.log.info("Additional wait time to reflect offline")
            time.sleep(self.time_off)
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            self.hyperscale_helper.ma_service_up(self.ma1)

            self.log.info("Wait for MA to be marked and DDB reconstruction job triggered")
            time.sleep(self.time_off)
            status, job = self.hyperscale_helper.get_ddb_reconstruction_job(self.storage_pool_name)
            if status:
                job_obj = self.commcell.job_controller.get(job[0])
                if job_obj.wait_for_completion():
                    self.log.info("Job status %s", job_obj.status)
            self.log.info("Running DV2 job")
            policy_obj = self.commcell.storage_policies.get(self.storage_pool_name)
            if policy_obj is not None:
                dv_job1 = policy_obj.run_ddb_verification("Primary", "Full", "DDB_VERIFICATION")
                if dv_job1.wait_for_completion():
                    self.log.info("Job status %s", self.job_obj.status)
            else:
                raise Exception("No policy object created for DV2 job")

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)

    def tear_down(self):
        """Tear down function of this test case"""
        self.hyperscale_helper.ma_service_up(self.ma1)
        self.hyperscale_helper.ma_service_up(self.ma2)
        self.log.info("Remounting the disk back")
        self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
        self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
        self.hyperscale_helper.mount_brick(self.node3, self.device_os_path3, self.storage_pool_name)
        self.log.info("Deleting data directory created")
        for index in range(1, 10):
            self.mmhelper_obj.remove_content( self.tcinputs["Content"] + str(index), self.commcell.commserv_name)
        self.log.info("Deleting policy and sub clients created for backup job")
        self.log.info("CHECKING JOB COMPLETION")
        if self.job_obj.wait_for_completion():
            self.log.info("Backup job status %s", self.job_obj.status)
        for index in range(1, 10):
            if not self.backupset.subclients.has_subclient(self.subclient + str(index)):
                self.backupset.subclients.delete(self.subclient + str(index))
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
