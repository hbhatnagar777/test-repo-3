# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for Vertical Scale-out of Storage Pool"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Hyperscale test class for Vertical Scale out of storage Pool"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for Vertical Scale out"
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
        self.log.info("Clearing out SP %s", self.storage_pool_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
        self.log.info("Clearing out all the added disks")
        for media_agent in self.clear_information.keys():
            disks = self.clear_information[media_agent]
            query = "delete  from MMDiskHWInfo where hostid = {0}"
            ma_session = Machine(media_agent, self.commcell)
            self.log.info("Clearing and Un mounting disks for %s", media_agent)
            client_id = self.commcell.clients.get(media_agent).client_id
            for disk in disks:
                command = "umount {0}".format(disk[0])
                self.log.info(command)
                ma_session.execute_command(command)
                self.log.info("Formatting disk %s as sd name on media agent %s", disk[0], media_agent)
                command1 = "dd if=/dev/zero of={0}  bs=512  count=1".format(disk[0])
                self.log.info(command1)
                output = ma_session.execute_command(command1)
                self.log.info(output.output)
                self.log.info("clearing fstab entry")
                command = "sed -i '/{0}/d' /etc/fstab".format(disk[4].replace('/ws/', ''))
                self.log.info(command)
                ma_session.execute_command(command)
                self.log.info("Clearing /ws folder ")
                command = "rm -rf {0}".format(disk[4])
                self.log.info(command)
                ma_session.execute_command(command)
            self.log.info("Clearing CSDB entries for MA %s with id %s", media_agent, client_id)
            query = query.format(client_id)
            self.log.info(query)
            self.hyperscale_helper.execute_update_query(query, self.sql_login, self.sql_sq_password)

        for media_agent in self.clear_information.keys():
            self.log.info("Restarting services for host %s", media_agent)
            ma_session = Machine(media_agent, self.commcell)
            restart = r"commvault restart"
            try:
                ma_session.execute_command(restart)
            except Exception as exp:
                self.log.info("Exception %s", exp)
                self.log.info("Restarted Services")
                pass
            time.sleep(120)

    def run(self):
        try:
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
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            status, response = self.hyperscale_helper.create_storage_pool(self.storage_pool_name,
                                                                          self.ma1, self.ma2, self.ma3)
            # Validating storage pool after creation
            status = self.hyperscale_helper.validate_storage(self.storage_pool_name)
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
            glus_info_before = self.hyperscale_helper.gluster_vol_info(self.ma1)
            gluster_brick_before = self.hyperscale_helper.gluster_brick_information(self.ma1)
            self.log.info("Gluster bricks before Vertical Expandion %s", len(gluster_brick_before))
            self.log.info("Getting sub vol information for %s", self.storage_pool_name)
            sub_vol_before = self.hyperscale_helper.get_subvolume_for_pool(self.storage_pool_name)

            self.log.info("Identifying disks available for vertical scale out on each node")
            vertical_disks = []
            for media_agent in rows:
                vertical_disks += self.hyperscale_helper.disk_for_vertical_scaleout(media_agent[0],
                                                                                    self.storage_pool_name)
            self.log.info("Vertical scale out disks are")
            for disk in vertical_disks:
                self.log.info(disk)
            vertical_scaleout_disk, min_req = self.\
                hyperscale_helper.minimum_disks_for_vertical_scaleout(self.storage_pool_name)
            if min_req == 0:
                raise Exception("Not proper number of disks present for Vertical scale out")

            for key in vertical_scaleout_disk.keys():
                self.log.info("MA %s and disks are %s", key, vertical_scaleout_disk[key])

            self.log.info("\nAdding disks for vertical scale out of pool %s", self.storage_pool_name)
            restart = r"commvault restart"
            self.clear_information = vertical_scaleout_disk
            for media_agent in vertical_scaleout_disk.keys():
                count = 0
                disks = vertical_scaleout_disk[media_agent]
                self.log.info("Disks for media agent %s that can be added for vertical scaleout are %s",
                              media_agent, disks)
                for disk in disks:
                    if disk[2] == 'false':
                        status = self.hyperscale_helper.adding_disk_vertical_scaleout(media_agent, disk[0])
                        disk[2] = status
                        if status:
                            count += 1
                    elif disk[2] == 'true':
                        disk[2] = True
                        count += 1

                    self.log.info("Checking disk %s being mounted on %s", disk[0], media_agent)
                    mount_status, mount_details = self.hyperscale_helper.mount_details(media_agent, disk[0])
                    if mount_status:
                        self.log.info("Disk %s is mounted as %s on %s", disk[0], mount_details[5], media_agent)
                        disk.append(mount_details[5])
                    if count == min_req:
                        self.log.info("Added minimum required disks for vertical scaleout")
                        break

                if count != min_req:
                    raise Exception("Unable to add minimum required disks,"
                                    " please verify minimum disk present on nodes")
            self.clear_information = vertical_scaleout_disk

            self.log.info("Verifying Vertical Scaleout, Log info!!")
            for media_agent in vertical_scaleout_disk.keys():
                trys = 20
                while trys > 0:
                    status = self.hyperscale_helper.vertical_scaleout_log_status(media_agent)
                    trys -= 1
                    if status in (1, 2):
                        break
                    time.sleep(300)
                if status != 0:
                    break
            if not status:
                self.log.error("Unable to fetch logs from all MA's")

            self.log.info("Additional time for csdb to populate ")
            time.sleep(400)
            self.log.info("Getting disk information for the disks added")
            for media_agent in vertical_scaleout_disk.keys():
                disks = vertical_scaleout_disk[media_agent]
                hostid = self.commcell.clients.get(media_agent).client_id
                for disk in disks:
                    self.hyperscale_helper.node_brick_info(hostid, disk[4])
            self.log.info("Getting sub volume information after Vertical expansion")
            sub_vol_after = self.hyperscale_helper.get_subvolume_for_pool(self.storage_pool_name)
            new_sub_vol = []
            for sub_vol in sub_vol_after:
                if sub_vol not in sub_vol_before:
                    self.log.info("New sub volume created %s", sub_vol)
                    new_sub_vol.append(sub_vol)
            self.log.info("Getting all new bricks added to the gluster pool %s", self.storage_pool_name)
            if len(new_sub_vol) != 0:
                for sub_vol in new_sub_vol:
                    bricks = self.hyperscale_helper.get_all_bricks_for_subvolume(sub_vol[0])
                    self.log.info("New bricks added to %s are %s", self.storage_pool_name, bricks)
                    self.log.info("Checking gluster brick health status for these bricks")
                    for brick in bricks:
                        status = self.hyperscale_helper.gluster_healthy_brick_status(brick[4], brick[3])
                        if not status:
                            raise Exception("Brick not healthy after scale out!")
                    self.log.info("Checking bricks part of gluster or not")
                    for brick in bricks:
                        hostname = self.hyperscale_helper.get_hostname(brick[4])
                        brick_info = self.hyperscale_helper.gluster_single_brick_info(hostname,
                                                                                      self.storage_pool_name,
                                                                                      brick[3])
                        if brick_info[3] == 'N/A':
                            raise Exception("No PID for brick")
                        self.log.info("PID for brick %s is %s", brick[3], brick_info[3])
                        if len(brick_info) == 0:
                            raise Exception("Brick not part of gluster")
                        fstab_entry = self.hyperscale_helper.check_fstab_entry(hostname, brick[3])
                        status = self.hyperscale_helper.verify_fstab_replace_entry(hostname, fstab_entry)
                        if not status:
                            raise Exception("UUID not same")

            self.log.info("Gluster bricks for %s", self.storage_pool_name)
            gluster_brick_after = self.hyperscale_helper.gluster_brick_information(self.ma1)
            self.log.info("Gluster bricks after Vertical Expandion are %s before expansion were %s",
                          len(gluster_brick_after), len(gluster_brick_before))
            glus_info_after = self.hyperscale_helper.gluster_vol_info(self.ma1)
            glus_size_staus = self.hyperscale_helper.verify_replace_gluster_size(glus_info_before, glus_info_after)
            if not glus_size_staus:
                self.log.info("Gluster size not same after replacement")

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

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
