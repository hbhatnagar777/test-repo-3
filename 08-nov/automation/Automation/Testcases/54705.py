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
        self.name = "Test case for Resiliency un-mounting disks"
        self.show_to_user = True
        self.result_string = ""
        self.policy = None
        self.policy_name = None
        self.subclient_obj = None
        self.job_obj = None
        self.username = None
        self.password = None
        self.client = None
        self.media_agent = None
        self.storage_pool_name = None
        self.sql_sq_password = None
        self.sql_login = None
        self.control_nodes = {}
        self.ma1 = None
        self.ma2 = None
        self.ma3 = None
        self.mas = []
        self.node1 = None
        self.node2 = None
        self.node3 = None
        self.brick1 = None
        self.brick2 = None
        self.brick3 = None
        self.device_os_path1 = None
        self.new_device_os_path1 = None
        self.device_os_path2 = None
        self.device_os_path3 = None
        self.new_device_os_path2 = None
        self.new_device_os_path3 = None
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
        }
        self.disk_id1 = 0
        self.disk_id2 = 0
        self.node_id1 = None
        self.node_id2 = None
        self.node_id3 = None
        self.sub_vol = None
        self.sub_vol_replace = None
        self.hyperscale_helper = None
        self.time_diff = 0

    def setup(self):
        """
        Setup function of this test case
        Initializes test case variables
        """
        self.username = self.tcinputs["username"]
        self.password = self.tcinputs["password"]
        self.media_agent = self.commcell.commserv_name
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        for node in self.control_nodes:
            self.mas.append(self.control_nodes[node])
        self.storage_pool_name = self.tcinputs["Storage_Pool_Name"]
        self.sql_sq_password = self.tcinputs["SqlSaPassword"]
        self.sql_login = self.tcinputs["SqlLogin"]
        self.client = self.commcell.clients.get(self.media_agent)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset = self.agent.backupsets.get("defaultBackupSet")
        self.subclient = self.id + "_subclient"
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        self.time_diff = 1200

    def run(self):
        """Run function of this test case
            Replacing healthy Disk
        """
        try:
            self.log.info("*************Resiliency Un-Mounting disk test**************")
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
            # Get disk uuids for all node
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            status, response = self.hyperscale_helper.create_storage_pool(self.storage_pool_name,
                                                                          self.ma1, self.ma2, self.ma3)
            self.log.info(status)
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

            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the current storage pool = %s", str(len(rows)))
            self.log.info("Current storage pool contains the following nodes: ")
            for row in rows:
                self.log.info(row[0])

            # Checking sp present and sp state
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

            # Getting node and disks of same sub volume 
            self.log.info("getting disks of same sub volume ")
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

            # Checking node part of storage pool or not ( handle it api doen't handle it, would disturb other node)
            if int(self.node_id1) and int(self.node_id2) and int(self.node_id3) not in nodes:
                self.log.error("Node %s or %s not part of Pool %s", self.node1, self.node2,
                               self.storage_pool_name)
                raise Exception("Node not part of Storage Pool")
            self.log.info("Nodes %s, %s and %s part of Pool %s", self.node1, self.node2, self.node3,
                          self.storage_pool_name)

            # NO NEED TO CHECK -----(checking brick part of node)----ALREADY PART OF POOL FROM SUB VOLUME
            self.log.info("device_os_path1: %s and device_os_path2: %s and self.device_os_path3: %s",
                          self.device_os_path1, self.device_os_path2, self.device_os_path3)
            self.disk_id1, self.disk_id2, disk_id3 = self.brick1[6], self.brick2[6], self.brick3[6]
            self.log.info("\nDisk id %s for brick %s\nDisk id %s for brick %s\nDisk id %s for brick %s ",
                          self.disk_id1, self.device_os_path1,
                          self.disk_id2, self.device_os_path2,
                          disk_id3, self.device_os_path3)

            # --------checking brick part of pool and gluster and
            # Checking brick health of brick being replaced-------
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

            # ---------------------------TRIGGERING A BACKUP JOB BEFORE Un-Mounting------------------------
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
            self.log.info("**************RUNNING BACKUP JOB ******************")
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(
                                                                     library_id)[2],
                                                                 self.node1, global_policy_name=
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

            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)
            while True:
                if self.job_obj.phase == 'Backup':
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
                    break
                self.log.info("Job status %s", self.job_obj.status)
                time.sleep(120)
                if self.job_obj.status == "Completed":
                    break
                if self.job_obj.status == "Failed":
                    break
            self.log.info("Job status %s", self.job_obj.status)
            time.sleep(300)
            self.log.info("Job status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
                self.log.info("Job completed after unmounting 2 disks")

            # Hitting resiliency
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)

            while True:
                if self.job_obj.phase == "Backup":
                    # Un Mounting disk
                    self.log.info("Un mounting to hit resiliency")
                    self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path3)
                    self.hyperscale_helper.unmount_brick(self.node3, self.device_os_path3, self.storage_pool_name)
                    flag3 = self.hyperscale_helper.brick_flag_status(hostid=self.node_id3,
                                                                     device_os=self.device_os_path3)
                    count = 20
                    while not flag3 & 16 and count >= 20:
                        self.log.info("waiting to reflect offline for disk %s", self.device_os_path3)
                        flag3 = self.hyperscale_helper.brick_flag_status(self.node_id3, self.device_os_path3)
                        count -= 1
                        time.sleep(120)
                    self.log.info("Disk %s offline", self.device_os_path3)
                    self.hyperscale_helper.gluster_healthy_brick_status(self.node_id3, self.device_os_path3)
                    break
                self.log.info("Job status %s", self.job_obj.status)
                time.sleep(120)
                if self.job_obj.status == "Completed":
                    break
                if self.job_obj.status == "Failed":
                    break
            self.log.info("Job status %s", self.job_obj.status)
            self.log.info("Additional time to verify job status")
            time.sleep(400)
            self.log.info("Job status %s", self.job_obj.status)
            self.log.info("Re mounting disk back to bring to resiliency and waiting for 20 mins")
            time.sleep(self.time_diff)
            self.hyperscale_helper.mount_brick(self.node3, self.device_os_path3, self.storage_pool_name)
            self.log.info("Aditional time after re mounting of disk")
            time.sleep(120)

            self.log.info("Job status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
                self.log.info("Job completed after hitting back to resiliency ")

            self.log.info("Re mounting all the disks back")
            self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
            self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
            self.log.info("Waiting after remounting of disks")
            time.sleep(200)

            self.log.info("Un mounting all the disks from a node while backup is running")
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Started backup job, status %s", self.job_obj.status)

            while True:

                if self.job_obj.phase == 'Backup':
                    self.log.info("Getting bricks for node %s", self.ma1)
                    ma_id = self.hyperscale_helper.get_host_id(self.ma1)
                    bricks = self.hyperscale_helper.get_all_bricks_for_hostid(ma_id)
                    for brick in bricks:
                        device_os_path = str(brick[3])
                        self.hyperscale_helper.unmount_brick(self.ma1, device_os_path, self.storage_pool_name)
                        flag = self.hyperscale_helper.brick_flag_status(hostid=ma_id, device_os=device_os_path)
                        count = 20
                        while not flag & 16 and count >= 20:
                            self.log.info("waiting to reflect offline for disk %s", )
                            flag = self.hyperscale_helper.brick_flag_status(ma_id, device_os_path)
                            time.sleep(120)
                        self.log.info("Disk %s offline", device_os_path)
                        self.hyperscale_helper.gluster_healthy_brick_status(ma_id, device_os_path)
                    break
                self.log.info("Started backup job, status %s", self.job_obj.status)
                time.sleep(120)
                if self.job_obj.status == "Completed":
                    break
                if self.job_obj.status == "Failed":
                    break
            self.log.info("Job status %s", self.job_obj.status)
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
                self.log.info("Job completed")

            self.log.info("Re mounting all the disks back")
            for brick in bricks:
                device_os_path = str(brick[3])
                self.hyperscale_helper.mount_brick(self.ma1, device_os_path, self.storage_pool_name)

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("Re mounting all the disks back")
        if self.device_os_path1 is not None:
            self.hyperscale_helper.mount_brick(self.node1, self.device_os_path1, self.storage_pool_name)
        if self.device_os_path1 is not None:
            self.hyperscale_helper.mount_brick(self.node2, self.device_os_path2, self.storage_pool_name)
        if self.device_os_path1 is not None:
            self.hyperscale_helper.mount_brick(self.node3, self.device_os_path3, self.storage_pool_name)
        self.log.info("Re mounting all the disks back")
        self.log.info("Getting bricks for node %s", self.ma1)
        ma_id = self.hyperscale_helper.get_host_id(self.ma1)
        bricks = self.hyperscale_helper.get_all_bricks_for_hostid(ma_id)
        for brick in bricks:
            device_os_path = str(brick[3])
            self.hyperscale_helper.mount_brick(self.ma1, device_os_path, self.storage_pool_name)
        self.log.info("Deleting policy and sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)