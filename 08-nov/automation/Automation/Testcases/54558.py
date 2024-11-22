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
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
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
        self.name = "Test case for Simultaneously replace two bricks on a " \
                    "separate sub-volume while a few backups are running"
        self.result_string = ""
        self.policy = ""
        self.policy_name = ""
        self.subclient_obj = ""
        self.job_obj = ""
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
        self.brick1 = ""
        self.brick2 = ""
        self.device_os_path1 = ""
        self.new_device_os_path1 = ""
        self.device_os_path2 = ""
        self.new_device_os_path2 = ""
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
        }
        self.disk_id1 = 0
        self.disk_id2 = 0
        self.node_id1 = ""
        self.node_id2 = ""
        self.sub_vol = ""
        self.sub_vol_replace1 = ""
        self.sub_vol_replace2 = ""
        self.hyperscale_helper = None
        self.restore_path = ""
        self.sd_name1 = ""
        self.sd_name2 = ""

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
        # Backup objects
        self.client = self.commcell.clients.get(self.media_agent)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset = self.agent.backupsets.get("defaultBackupSet")
        self.subclient = self.id + "_subclient"
        self.policy_name = self.id + "_Policy1"
        self.restore_path = self.tcinputs["Content"] + self.id + "_restore"
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
     
    def run(self):
        """Run function of this test case
            Replacing healthy Disk
        """
        try:
            self.log.info("*************Simultaneously replace two bricks on a separate "
                          "sub-volume while a few backups are running**************")
            status_fstab = False
            status = self.hyperscale_helper.check_if_storage_pool_is_present(self.storage_pool_name)
            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the current storage pool = %s", str(len(rows)))

            if status is True:
                self.log.info("Storage pool : %s already present, attempting deletion", self.storage_pool_name)
                self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                             self.sql_login,
                                                             self.sql_sq_password)
                time.sleep(30)
            else:
                self.log.info(
                    "Storage pool : %s is not present", self.storage_pool_name)
            # Create a fresh storage pool
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            status, response = self.hyperscale_helper.create_storage_pool(self.storage_pool_name,
                                                                          self.ma1, self.ma2, self.ma3)
            # Validating storage pool after creation
            status = self.hyperscale_helper.validate_storage(self.storage_pool_name)
            self.log.info("storage pool %s not valid with status %s ", self.storage_pool_name, status)
            self.log.info(response)

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
            # # Checking sp present and sp state
            storage_pool_status = self.hyperscale_helper.check_if_storage_pool_is_present(self.storage_pool_name)
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            storage_pool_properties = storage_pool_details._storage_pool_properties
            status = storage_pool_properties["storagePoolDetails"]['statusCode']
            if not storage_pool_status:
                self.log.error("Pool %s not present", self.storage_pool_name)
                raise Exception("Pool not present")
            if int(status) != 300:
                self.log.error("Pool %s, not healthy with status %s", self.storage_pool_name,
                               status)
                raise Exception("Pool status Failure or pending, pool not healthy")
            self.log.info("Pool %s healthy and details %s ", self.storage_pool_name,
                          storage_pool_details)

            nodes = self.hyperscale_helper.get_all_nodes_hostids(self.storage_pool_name)
            self.log.info("All node ids associated with pool are %s", nodes)

            # Getting node and disks of different sub volume for simultaneous replacement
            self.log.info("getting disks of separate sub volume for simultaneous replacement")
            # self.node_id = self.hyperscale_helper.get_host_id(self.node)
            self.sub_vol = self.hyperscale_helper.get_subvolume_for_pool(self.storage_pool_name)
            subvol = random.sample(self.sub_vol, 2)
            self.sub_vol_replace1 = subvol[0][0]
            self.sub_vol_replace2 = subvol[1][0]
            self.log.info("Sub volume for disk replacement are %s and %s", self.sub_vol_replace1,
                          self.sub_vol_replace2)
            self.log.info("Bricks for sub vol1 %s ", self.sub_vol_replace1)
            bricks1 = self.hyperscale_helper.get_all_bricks_for_subvolume(self.sub_vol_replace1)

            # Getting 1 random brick of subvolume
            replace_bricks1 = random.sample(bricks1, 1)
            self.brick1 = replace_bricks1[0]
            self.log.info("Bricks for sub vol2 %s ", self.sub_vol_replace2)
            bricks2 = self.hyperscale_helper.get_all_bricks_for_subvolume(self.sub_vol_replace2)

            # Getting 1 random brick of subvolume
            replace_bricks2 = random.sample(bricks2, 1)
            self.brick2 = replace_bricks2[1]
            self.log.info("Bricks of sub volume %s for replacement are %s ", self.sub_vol_replace1, self.brick1)
            self.log.info("Bricks of sub volume %s for replacement are %s ", self.sub_vol_replace2, self.brick2)
            self.node_id1, self.node_id2 = str(self.brick1[4]), str(self.brick2[4])
            self.node1, self.node2 = self.hyperscale_helper.get_hostname(self.node_id1),\
                                     self.hyperscale_helper.get_hostname(self.node_id2)
            self.device_os_path1, self.device_os_path2 = str(self.brick1[3]), str(self.brick2[3])
            self.log.info("Nodes are node1 %s, hostid %s and node2 %s, hostid %s ", self.node1, self.node_id1,
                          self.node2, self.node_id2)

            # Checking node part of storage pool or not ( handle it api doen't handle it, would disturb other node)
            if int(self.node_id1) and int(self.node_id2) not in nodes:
                self.log.error("Node %s or %s not part of Pool %s", self.node1, self.node2,
                               self.storage_pool_name)
                raise Exception("Node not part of Storage Pool")
            self.log.info("Nodes %s and %s part of Pool %s", self.node1, self.node2,
                          self.storage_pool_name)

            # NO NEED TO CHECK -----(checking brick part of node)----ALREADY PART OF POOL FROM SUB VOLUME
            self.log.info("device_os_path1: %s and device_os_path2: %s", self.device_os_path1,
                          self.device_os_path2)
            # brick_info = self.hyperscale_helper.node_brick_info(self.node_id, self.device_os_path1)
            self.disk_id1, self.disk_id2 = self.brick1[6], self.brick2[6]
            self.log.info("\nDisk id %s for brick %s\nDisk id %s for brick %s ", self.disk_id1,
                          self.device_os_path1,
                          self.disk_id2, self.device_os_path2)

            self.log.info("--------checking bricks part of pool and glusters and "
                          "Checking brick health of bricks being replaced-------")
            self.hyperscale_helper.check_gluster_brick_online(self.node1, self.storage_pool_name,
                                                              self.device_os_path1)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id1, self.device_os_path1)

            self.hyperscale_helper.check_gluster_brick_online(self.node2, self.storage_pool_name,
                                                              self.device_os_path2)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id2, self.device_os_path2)

            # Getting gluster size info before triggering replace
            glus_info_before = self.hyperscale_helper.gluster_vol_info(self.node1)

            # Running backup job before replacement
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
                self.log.info("Starting Backup")
                self.job_obj = self.subclient_obj.backup("FULL")
                self.log.info("Job status %s", self.job_obj.status)

            self.log.info("-----------------------REPLACING DISKS on Same SUB VOLUME, "
                          "while backup runs ---------------------------")
            # Check flag status, to CONFIRM NO REPLACEMENT ALREADY SUBMITTED
            flag1 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id1,
                                                             device_os=self.device_os_path1)
            flag2 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id2,
                                                             device_os=self.device_os_path2)
            # Trigger disk replacement, check fstab entry
            entry_old1 = self.hyperscale_helper.check_fstab_entry(self.node1, self.device_os_path1)
            entry_old2 = self.hyperscale_helper.check_fstab_entry(self.node2, self.device_os_path2)
            if not entry_old1:
                self.log.error("No entry in fstab for %s", self.device_os_path1)
                if not entry_old2:
                    self.log.error("No entry in fstab for %s", self.device_os_path2)
                raise Exception("No entry in fstab check disk")

            # -----------------------REPLACING DISKS ---------------------------
            if not flag1 & 4 and not flag2 & 4:

                # Check flag status
                self.log.info("flag status before replace")
                flag1 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id1,
                                                                 device_os=self.device_os_path1)
                flag2 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id2,
                                                                 device_os=self.device_os_path2)
                self.log.info("Getting sd name for the disk1 %s", self.device_os_path1)
                self.sd_name1 = self.hyperscale_helper.sd_name_for_disk(self.node1, self.device_os_path1)
                self.log.info("Getting sd name for the disk2 %s", self.device_os_path2)
                self.sd_name2 = self.hyperscale_helper.sd_name_for_disk(self.node2, self.device_os_path2)

                while True:
                    if self.job_obj.phase == "Backup":
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

                        # ----- Replace request for brick1------
                        self.log.info("Replace request for brick1 %s ", self.brick1)
                        flag, response = self.hyperscale_helper.replace_brick(media_agent=self.node1,
                                                                              brick_id=self.disk_id1,
                                                                              pool=self.storage_pool_name)
                        replace_flag = self.hyperscale_helper.brick_flag_status(self.node_id1,
                                                                                self.device_os_path1)
                        self.log.info("Replace Flag status %s", replace_flag)

                        # Checking new disk availability
                        disk_available_stauts = self.hyperscale_helper.replace_brick_available(self.node1)
                        if not disk_available_stauts:
                            self.log.error("No disk available for replacement")
                            raise Exception("No disk available")

                        # Replace success failure logs
                        status, response_log = self.hyperscale_helper.replace_log_status(self.node1)
                        self.log.info("Status of Replace %s", status)
                        for log in response_log:
                            self.log.info(log)
                        # Repalce failure re mounting the disk again
                        if not status:
                            self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
                            self.log.error('Replacement failed')
                            raise Exception(response_log)
                            # raise Exception(response_log)
                        else:
                            self.hyperscale_helper.formatting_replaced_disk(self.node1, self.sd_name1)
                            status_reset = self.hyperscale_helper.verify_reset_brick(self.node1,
                                                                                     self.storage_pool_name,
                                                                                     self.device_os_path1)

                        # ----- Replace request for brick2------
                        # Un Mounting disk
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

                        self.log.info("Replace request for brick2 %s ", self.brick2)
                        flag, response = self.hyperscale_helper.replace_brick(media_agent=self.node2,
                                                                              brick_id=self.disk_id2,
                                                                              pool=self.storage_pool_name)
                        replace_flag = self.hyperscale_helper.brick_flag_status(self.node_id2, self.device_os_path2)
                        self.log.info("Replace Flag status %s", replace_flag)

                        # Checking new disk availability
                        disk_available_stauts = self.hyperscale_helper.replace_brick_available(self.node2)
                        if not disk_available_stauts:
                            self.log.error("No disk available for replacement")
                            raise Exception("No disk available")

                        # Replace success failure logs
                        status, response_log = self.hyperscale_helper.replace_log_status(self.node2)
                        self.log.info("Status of Replace %s", status)
                        for log in response_log:
                            self.log.info(log)
                        # Repalce failure re mounting the disk again
                        if not status:
                            self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2,
                                                               self.storage_pool_name)
                            self.log.error('Replacement failed')
                            raise Exception(response_log)
                        else:
                            self.hyperscale_helper.formatting_replaced_disk(self.node2, self.sd_name2)
                            status_reset = self.hyperscale_helper.verify_reset_brick(self.node2,
                                                                                     self.storage_pool_name,
                                                                                     self.device_os_path2)
                            break
                    else:
                        self.log.info("Job status %s", self.job_obj.status)
                        time.sleep(120)
                    if self.job_obj.status == "Completed":
                        break
                    if self.job_obj.status == "Killed":
                        break
            else:
                status_fstab = True
                self.log.info("Replace request cannot be submitted as previous request in progress")

            # for replace
            # New disk information
            new_brick_info1 = self.hyperscale_helper.get_disk_by_disk_id(self.disk_id1)
            new_brick_info2 = self.hyperscale_helper.get_disk_by_disk_id(self.disk_id2)
            self.new_device_os_path1, self.new_device_os_path2 = str(new_brick_info1[3]), str(new_brick_info2[3])

            self.log.info("\nFor brick1 %s old device path %s and new device path %s "
                          "\nFor brick2 %s old device path %s and new device path %s",
                          self.brick1, self.device_os_path1, self.new_device_os_path1,
                          self.brick2, self.device_os_path2, self.new_device_os_path2)
            # -----Checking flag status for new bricks----
            self.log.info("Flag status for new brick1 %s ", new_brick_info1)
            flag1 = self.hyperscale_helper.brick_flag_status(self.node_id1, self.new_device_os_path1)
            self.log.info("Flag status for new brick2 %s ", new_brick_info2)
            flag2 = self.hyperscale_helper.brick_flag_status(self.node_id2, self.new_device_os_path2)

            # Check gluster  entries for heal on any node
            if not self.hyperscale_helper.gluster_heal_entries(self.node1, self.storage_pool_name):
                self.log.info("Entries not zero yet")
            else:
                self.log.info("heal success and entries 0 now")

            # Checking new disk health
            self.log.info("\nChecking disk health for brick1 %s", self.brick1)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id1, self.new_device_os_path1)
            self.log.info("\nChecking disk health for brick2 %s", self.brick2)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id2, self.new_device_os_path2)

            # for replace submitted checking flags
            self.log.info("Flag status for %s ", self.new_device_os_path1)
            flag1 = self.hyperscale_helper.brick_flag_status(self.node_id1, self.new_device_os_path1)
            self.log.info("Flag status for %s ", self.new_device_os_path2)
            flag2 = self.hyperscale_helper.brick_flag_status(self.node_id2, self.new_device_os_path2)
            # check fstab entries for replace
            entry_new1 = self.hyperscale_helper.check_fstab_entry(self.node1, self.new_device_os_path1)
            entry_new2 = self.hyperscale_helper.check_fstab_entry(self.node2, self.new_device_os_path2)
            if not entry_new1:
                self.log.error("No entry in fstab for %s", self.new_device_os_path1)
                if not entry_new2:
                    self.log.error("No entry in fstab for %s", self.new_device_os_path2)

            if status_fstab is False:
                status_fstab1, res = self.hyperscale_helper.replace_fstab_entry(self.node1, entry_old1, entry_new1)
                status_fstab2, res = self.hyperscale_helper.replace_fstab_entry(self.node2, entry_old2, entry_new2)
                status_fstab = True
                if status_fstab1 is False or status_fstab2 is False:
                    self.log.error(res)
                    raise Exception(res)

            status_heal1 = False
            status_heal2 = False
            while status_heal1 & status_heal2 is not True and int(flag1) != 1 and int(flag2) != 1 \
                    and status_fstab is True:
                if status_heal1 is False:
                    status_heal1 = self.hyperscale_helper.heal_disk_entry(self.node1, self.new_device_os_path1)
                if int(flag1) != 1:
                    flag1 = self.hyperscale_helper.brick_flag_status(self.node_id1, self.new_device_os_path1)
                if status_heal2 is False:
                    status_heal2 = self.hyperscale_helper.heal_disk_entry(self.node2, self.new_device_os_path2)
                if int(flag2) != 1:
                    flag2 = self.hyperscale_helper.brick_flag_status(self.node_id2, self.new_device_os_path2)

                time.sleep(300)

            self.log.info("----------------REPLACE DISK OVER------------")

            # Checking new bricks part of gluster or not
            self.log.info("--------checking new bricks part of glusters -------")
            self.hyperscale_helper.check_gluster_brick_online(self.node1, self.storage_pool_name,
                                                              self.new_device_os_path1)
            self.hyperscale_helper.check_gluster_brick_online(self.node2, self.storage_pool_name,
                                                              self.new_device_os_path2)
            # Checking gluster size after replacement
            glus_info_after = self.hyperscale_helper.gluster_vol_info(self.node1)
            glus_size_staus = self.hyperscale_helper.verify_replace_gluster_size(glus_info_before, glus_info_after)
            if not glus_size_staus:
                self.log.info("Gluster size not same after replacement")

            self.log.info("CHECKING JOB COMPLETION")
            if self.job_obj.wait_for_completion():
                self.log.info("Backup job status %s", self.job_obj.status)

            # Running JOBS over pool
            # Restore Job
            self.log.info("Starting Restore")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_path,
                                                                   self.subclient_obj.content, True, True)
            if self.job_obj.wait_for_completion():
                self.log.info("Restore job status %s", self.job_obj.status)
            # Verifying Restore Data, Path for single folder
            path = self.tcinputs["Content"].split("\\")
            path = path[-1]
            restore_veri = self.restore_path + "\\" + path
            difference = self.hyperscale_helper.check_restore_folders(self.media_agent,
                                                                      self.tcinputs["Content"],
                                                                      restore_veri)
            if not difference:
                self.log.info("Restore data not same as backed up, Different Data %s", difference)
            else:
                self.log.info("Restore data same as Backed up, after Replacement data intact")

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Remounting the disk back")
        self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
        self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
        self.log.info("Deleting policy and sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)

