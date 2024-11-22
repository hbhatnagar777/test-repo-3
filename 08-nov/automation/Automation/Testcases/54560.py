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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
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
        self.name = "Test case for Replace Same Brick Being Healed"
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
        self.node = ""
        self.brick = ""
        self.device_os_path = ""
        self.new_device_os_path = ""
        self.tcinputs = {
            "username": None,
            "password": None,
            "MA": None,
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None
            },
            "Brick": None,
            "Storage_Pool_Name": None,
            "SqlLogin": None,
            "SqlSaPassword": None,
        }
        self.disk_id = 0
        self.node_id = ""
        self.restore_path = ""
        self.hyperscale_helper = None
        self.sd_name = ""
        self.replace_again = 0

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
        self.node = self.tcinputs["MA"]
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        for node in self.control_nodes:
            self.mas.append(self.control_nodes[node])
        self.brick = self.tcinputs["Brick"]
        # Backup objects
        self.client = self.commcell.clients.get(self.media_agent)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset = self.agent.backupsets.get("defaultBackupSet")
        self.subclient = self.id + "_subclient"
        self.policy_name = self.id + "_Policy1"
        self.device_os_path = '/ws/' + self.brick
        self.restore_path = self.tcinputs["Content"] + self.id + "_restore"
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        node_client = self.commcell.clients.get(self.node)
        self.node_log_directory = node_client.log_directory
        if not self.node_log_directory:
            message = f"Please check if {self.node} is up including Commvault services."
            message += f" log directory = {self.node_log_directory}."
            raise Exception(message)
        self.node_cvma_log_path = f"{self.node_log_directory}/CVMA.log"

        self.node_machine = Machine(self.node, self.commcell)

    def run(self):
        """Run function of this test case
            Replacing healthy Disk
        """
        try:
            self.log.info("*****************Replace Same Brick Being Healed******************")
            status_fstab = False
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
            # Validating storage pool after creation
            status = self.hyperscale_helper.validate_storage(self.storage_pool_name)
            self.log.info("storage pool %s not valid with status %s ", self.storage_pool_name, status)
            self.log.info(response)

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

            # Getting node and disk for replacement
            self.log.info("Getting node and disk for replacement")
            self.node_id = self.hyperscale_helper.get_host_id(self.node)
            self.log.info("Node %s, host_id is %s", self.node, self.node_id)

            # Checking node part of storage pool or not ( handle it api doen't handle it, would disturb other node)
            if int(self.node_id) not in nodes:
                self.log.error("Node %s not part of Pool %s", self.node,
                               self.storage_pool_name)
                raise Exception("Node not part of Storage Pool")
            self.log.info("Node %s part of Pool %s", self.node,
                          self.storage_pool_name)

            # checking brick part of node
            self.log.info("device_os_path: %s", self.device_os_path)
            brick_info = self.hyperscale_helper.node_brick_info(self.node_id, self.device_os_path)
            self.disk_id = str(brick_info[4])
            self.log.info("Disk id %s for brick %s ", self.disk_id, self.device_os_path)

            # checking brick part of pool and gluster
            gluster_brick = self.hyperscale_helper.check_gluster_brick_online(self.node,
                                                                              self.storage_pool_name,
                                                                              self.device_os_path)

            # Checking brick health of brick being replaced
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id,
                                                                self.device_os_path)

            # Getting gluster size info before triggering replace
            glus_info_before = self.hyperscale_helper.gluster_vol_info(self.node)

            # Running backup job before replacement
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
            self.log.info("**************RUNNING BACKUP JOB BEFORE REPLACEMENT******************")
            self.log.info("running Backup before replacement")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(
                                                                     library_id)[2],
                                                                 self.node, global_policy_name=
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
                self.log.info("Job status %s", self.job_obj.status)

            self.log.info("Job status %s", self.job_obj.status)
            self.log.info("***REPLACING DISK*******")
            # Check flag status
            flag = self.hyperscale_helper.brick_flag_status(hostid=self.node_id,
                                                            device_os=self.device_os_path)
            # Trigger disk replacement, check fstab entry
            entry_old = self.hyperscale_helper.check_fstab_entry(self.node, self.device_os_path)
            if not entry_old:
                self.log.error("No entry in fstab for %s", self.device_os_path)
                raise Exception("No entry in fstab check disk")
            while self.replace_again <= 1:
                if not flag & 4:
                    # Check flag status
                    self.log.info("flag status before replace")
                    self.hyperscale_helper.brick_flag_status(hostid=self.node_id,
                                                             device_os=self.device_os_path)
                    self.log.info("Getting sd name for the disk")
                    self.sd_name = self.hyperscale_helper.sd_name_for_disk(self.node, self.device_os_path)
                    # Un Mounting disk
                    self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path)
                    self.hyperscale_helper.unmount_brick(self.node, self.device_os_path,
                                                         self.storage_pool_name)
                    flag = self.hyperscale_helper.brick_flag_status(hostid=self.node_id,
                                                                    device_os=self.device_os_path)
                    count = 20
                    while not flag & 16 and count >= 20:
                        self.log.info("waiting to reflect offline for disk %s", self.device_os_path)
                        flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.device_os_path)
                        count -= 1
                        time.sleep(120)
                    self.log.info("Disk %s offline", self.device_os_path)
                    self.hyperscale_helper.gluster_healthy_brick_status(self.node_id, self.device_os_path)

                    lines_cvma = self.hyperscale_helper.get_lines_in_log_file(self.node_machine, self.node_cvma_log_path)

                    flag, response = self.hyperscale_helper.replace_brick(media_agent=self.node,
                                                                          brick_id=self.disk_id,
                                                                          pool=self.storage_pool_name)
                    replace_flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.device_os_path)
                    self.log.info("Replace Flag status %s", replace_flag)

                    # Checking new disk availability
                    disk_available_stauts = self.hyperscale_helper.replace_brick_available(self.node)
                    if not disk_available_stauts:
                        self.log.error("No disk available for replacement")
                        raise Exception("No disk available")

                    # Replace success failure logs
                    status, response_log = self.hyperscale_helper.replace_log_status(self.node, from_line=lines_cvma)
                    self.log.info("Status of Replace %s", status)
                    for log in response_log:
                        self.log.info(log)
                    # Repalce failure re mounting the disk again
                    if not status:
                        self.hyperscale_helper.mount_brick(self.node,
                                                           self.device_os_path,
                                                           self.storage_pool_name)
                        self.log.error('Replacement failed')
                        raise Exception(response_log)

                    else:
                        self.hyperscale_helper.formatting_replaced_disk(self.node, self.sd_name)
                        status_reset = self.hyperscale_helper.verify_reset_brick(self.node,
                                                                                 self.storage_pool_name,
                                                                                 self.device_os_path)
                else:
                    status_fstab = True
                    self.log.info("Replace request cannot be submitted as previous request in progress")

                # for replace submitted
                # New disk
                new_brick_info = self.hyperscale_helper.get_disk_by_disk_id(self.disk_id)
                self.new_device_os_path = str(new_brick_info[3])
                self.log.info("old device path %s and new device path %s", self.device_os_path,
                              self.new_device_os_path)
                flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.new_device_os_path)

                # Check entries for heal
                if not self.hyperscale_helper.gluster_heal_entries(self.node, self.storage_pool_name):
                    self.log.info("Entries not zero yet")
                else:
                    self.log.info("heal success and entries 0 now")

                # Checking new disk health
                self.hyperscale_helper.gluster_healthy_brick_status(self.node_id, self.new_device_os_path)

                # for replace submitted
                flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.new_device_os_path)
                # check fstab entries for replace
                entry_new = self.hyperscale_helper.check_fstab_entry(self.node, self.new_device_os_path)
                if not entry_new:
                    self.log.error("No entry in fstab for %s", self.new_device_os_path)
                if status_fstab is False:
                    status_fstab, res = self.hyperscale_helper.replace_fstab_entry(self.node, entry_old, entry_new)
                    if status_fstab is False:
                        self.log.info(res)
                        raise Exception(res)

                status_heal = False
                while status_heal is False and int(flag) != 1 and status_fstab is True:
                    if status_heal is False:
                        status_heal = self.hyperscale_helper.heal_disk_entry(self.node, self.new_device_os_path)
                    if int(flag) != 1:
                        flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.new_device_os_path)
                    if int(flag) & 4:
                        self.log.info("Previous replace request still in progress, can't place new request")
                    time.sleep(300)

                # Checking new brick part of gluster or not
                replaced_gluster_brick = self.hyperscale_helper.check_gluster_brick_online(self.node,
                                                                                           self.storage_pool_name,
                                                                                           self.new_device_os_path)

                # Checking gluster size after replacement
                glus_info_after = self.hyperscale_helper.gluster_vol_info(self.node)
                glus_size_staus = self.hyperscale_helper.verify_replace_gluster_size(glus_info_before, glus_info_after)
                if not glus_size_staus:
                    self.log.info("Gluster size not same after replacement")

                if not int(flag) & 4 and self.replace_again < 1:
                    self.replace_again += 1
                    self.device_os_path = self.new_device_os_path
                    self.new_device_os_path = ""
                    self.log.info("#############Replacing same Brick being healed again#############")
                    self.log.info("Replacing disk %s again", self.device_os_path)

            # Restoring and verifying
            self.log.info("Starting Restore")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_path,
                                                                   self.subclient_obj.content, True, True)
            self.log.info("Waiting")
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)

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
        self.hyperscale_helper.mount_brick(self.node, self.device_os_path, self.storage_pool_name)
        self.log.info("Deleting policy and sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
