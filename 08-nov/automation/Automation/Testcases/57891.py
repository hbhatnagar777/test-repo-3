# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for creating a new library, SP, backupset and subclient and run backups"""
import random
import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Hyperscale test class for creating and deleting storage pools"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for creating 3*Node Storage Pool, and health check"
        self.show_to_user = True
        self.result_string = ""
        self.backupset = None
        self.subclient_obj = None
        self.job_obj = None
        self.library = None
        self.username = None
        self.password = None
        self.client = None
        self.subclient = None
        self.storage_policy = None
        self.mediaagent = None
        self.control_nodes = {}
        self.ma1 = None
        self.ma2 = None
        self.ma3 = None
        self.ma4 = None
        self.ma5 = None
        self.ma6 = None
        self.mas = []
        self.storage_pool_name = None
        self.sql_sq_password = None
        self.sql_login = None
        self.policy_name = None
        self.policy = None
        self.hyperscale_helper = None
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
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        time.sleep(30)
        self.log.info("Deleting policy and sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)

    def run(self):
        try:

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
            # Get disk uuids for all nodes
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
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
            self.log.info("Additional time for the MAs to populate the CSDB with brick health and block device health "
                          "info ")

            time.sleep(300)
            all_nodes = self.hyperscale_helper.get_all_nodes(self.storage_pool_name)
            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            if not gluster_brick_status:
                self.log.error("Gluster brick status bad")
            gluster_mount_status = True
            for node in rows:
                gluster_mount_status = gluster_mount_status & self.hyperscale_helper.gluster_mount(node[0])

            if not gluster_brick_status & gluster_mount_status:
                self.log.error("Gluster status bad")

            # Getting node and disks of for health check by daemon down
            self.log.info("getting disks to bring down its daemon")
            sub_vol = self.hyperscale_helper.get_subvolume_for_pool(self.storage_pool_name)
            sub_vol_replace = sub_vol[0][0]
            bricks = self.hyperscale_helper.get_all_bricks_for_subvolume(sub_vol_replace)
            # Getting a random brick of subvolume
            replace_bricks = random.sample(bricks, 1)
            brick1 = replace_bricks[0]
            node_id1 = str(brick1[4])
            node1 = self.hyperscale_helper.get_hostname(node_id1)
            device_os_path1 = str(brick1[3])
            self.log.info("Node is node1 %s, hostid %s", node1, node_id1)
            self.log.info("device_os_path1: %s ", device_os_path1)
            disk_id1 = brick1[6]
            self.log.info("Disk id %s for brick %s ", disk_id1, device_os_path1)
            # Check flag status
            flag1 = self.hyperscale_helper.brick_flag_status(hostid=node_id1, device_os=device_os_path1)

            # Brick daemon down and Un Mounting disk1
            self.log.info("Brick daemon down and Un mounting disk %s to make it offline and bad", device_os_path1)
            self.hyperscale_helper.unmount_brick(node1, device_os_path1, self.storage_pool_name)
            flag1 = self.hyperscale_helper.brick_flag_status(hostid=node_id1, device_os=device_os_path1)
            count = 20
            while not flag1 & 16 and count >= 0:
                self.log.info("waiting to reflect offline for disk %s", device_os_path1)
                flag1 = self.hyperscale_helper.brick_flag_status(node_id1, device_os_path1)
                count -= 1
                time.sleep(120)
            self.log.info("Disk %s offline", device_os_path1)
            self.hyperscale_helper.gluster_healthy_brick_status(node_id1, device_os_path1)

            # Restart gluster service
            self.hyperscale_helper.mount_brick(node1, device_os_path1, self.storage_pool_name)

            # Wait to populate
            self.log.info("Checiking brick status again")
            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            if not gluster_brick_status:
                self.log.error("Gluster brick status bad")

            # Running backup job before replacement
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
            self.log.info("running Backup before replacement")
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
            self.log.info("Backup job status %s", self.job_obj.status)
            if not self.job_obj.wait_for_completion():
                self.log.info("Backup status %s", self.job_obj.status)
                raise Exception(self.job_obj.status)
            self.log.info("Backup status %s", self.job_obj.status)
            self.log.info("*" * 80)

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
