# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for creating a new library, SP, backupset and subclient and run backups"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Hyperscale test class for creating and deleting storage pools"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for expansion of pool failure and reconfigure it"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.result_string = ""
        self.backupset = ""
        self.subclient_obj = ""
        self.job_obj = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient = ""
        self.storage_policy = ""
        self.policy = ""
        self.mediaagent = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.ma4 = ""
        self.ma5 = ""
        self.ma6 = ""
        self.mas = []
        self.storage_pool_name = ""
        self.policy_name = ""
        self.sql_login = ""
        self.sql_sq_password = ""
        self.hyperscale_helper = None
        self.tcinputs = {
            "Storage_Pool_Name": None,
            "username": None,
            "password": None,
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
                "MA4": None,
                "MA5": None,
                "MA6": None,
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
        self.ma4 = self.control_nodes["MA4"]
        self.ma5 = self.control_nodes["MA5"]
        self.ma6 = self.control_nodes["MA6"]
        self.client = self.commcell.clients.get(self.mediaagent)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset = self.agent.backupsets.get("defaultBackupSet")
        self.subclient = self.id + "_subclient"
        self.policy_name = self.id + "_Policy1"
        for node in self.control_nodes:
            self.mas.append(self.control_nodes[node])
        self.storage_pool_name = self.tcinputs["Storage_Pool_Name"]
        self.sql_sq_password = self.tcinputs["SqlSaPassword"]
        self.sql_login = self.tcinputs["SqlLogin"]
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
                self.log.info("Storage pool : %s is not present", self.storage_pool_name)
            # Create a fresh storage pool
            # Get disk uuids for all nodes
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            all_ma_ids = {}
            for media_agent in self.control_nodes:
                all_ma_ids[self.control_nodes[media_agent]] = self.hyperscale_helper.get_host_id(
                    self.control_nodes[media_agent])
            self.log.info("All ma and ids %s", all_ma_ids)
            ma_ids = all_ma_ids.values()
            self.log.info("Host ids are %s", ma_ids)

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
            old_count = len(rows)
            self.log.info("Current storage pool contains the following nodes: ")
            for row in rows:
                self.log.info(row[0])
            self.log.info("Additional time for the MAs to populate the CSDB with brick health and blcok device health "
                          "info ")

            time.sleep(300)
            all_nodes = self.hyperscale_helper.get_all_nodes(self.storage_pool_name)
            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            if not gluster_brick_status:
                self.log.error("Gluster brick status bad")

            # Failing expansion
            self.log.info("Failing expansion %s", self.storage_pool_name)
            self.hyperscale_helper.kill_sds_network(self.ma5)

            self.log.info("Horizontally expanding setup")
            status, response = self.hyperscale_helper.add_nodes(self.storage_pool_name,
                                                                self.ma4, self.ma5, self.ma6)

            self.log.info(status)
            self.log.info(response)
            # validating storage pool after expansion
            time.sleep(60)
            status = self.hyperscale_helper.wait_for_completion(self.storage_pool_name)
            self.log.info("Storage Pool expansion failed status %s", status)
            if status is True:
                self.log.info("Storage Pool expansion Successful")
            else:
                self.log.error("Storage Expansion failed")

            time.sleep(60)
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id

            # Updating hosts for reconfigure storage pool
            self.log.info("Updating hosts for reconfigure storage pool %s", self.storage_pool_name)
            self.hyperscale_helper.start_sds_network(self.ma5)
            self.log.info("Reconfiguring Storage pool %s ", self.storage_pool_name)
            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            resolution_status = False
            for ma_id in ma_ids:
                host = self.hyperscale_helper.get_hostname(ma_id)
                if [host] in rows:
                    resolution_status = self.hyperscale_helper.check_resolution_error(ma_id)
                if resolution_status is True:
                    break
            self.log.info("Resolution Error in storage pool %s: %s",
                          self.storage_pool_name, resolution_status)

            # Reconfiguring SP
            reconfigure_try = 5
            if resolution_status is True:
                while status is False and reconfigure_try != 0:
                    status, response = self.hyperscale_helper.reconfigure_storage_pool(
                        self.storage_pool_name)
                    self.log.info("After triggering reconfigure on %s, Reconfigure status is %s",
                                  self.storage_pool_name, status)
                    if status is False:
                        self.log.info("Storage pool %s not reconfigured, waiting to reconfigure",
                                      self.storage_pool_name)
                    reconfigure_try -= 1
                self.log.info("Storage Pool %s reconfigured and created status %s",
                              self.storage_pool_name, status)

            # Verifying same disks used in gluster
            disk_same_status = self.hyperscale_helper.verify_gluster_disk_uuids(self.ma3, disk_uuids)
            if disk_same_status:
                self.log.info("disks used are same")
            else:
                self.log.info("disks used are not same")

            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the current storage pool = %s", str(len(rows)))
            new_count = len(rows)
            self.log.info("Current storage pool contains the following nodes: ")
            for row in rows:
                self.log.info(row[0])

            added_nodes = new_count - old_count

            if added_nodes == 3:
                self.log.info("Storage pool has been successfully expanded by 3 nodes")
            else:
                raise Exception("Storage pool expansion failed with incorrect number of nodes")

            self.log.info("Additional time for the MAs to populate the CSDB with brick health and blcok device health "
                          "info ")
            time.sleep(600)

            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            gluster_mount_status = True
            for node in rows:
                gluster_mount_status = gluster_mount_status & self.hyperscale_helper.gluster_mount(node[0])

            if not gluster_brick_status & gluster_mount_status:
                self.log.error("Gluster brick status bad")
            # Running backup
            # Creating Plan
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(library_id)[
                                                                     2],
                                                                 self.ma3, global_policy_name=
                                                                 self.hyperscale_helper.get_policy_details(gdsp)[2])
            else:
                self.log.info("Policy exists")
                self.policy = self.commcell.storage_policies.get(self.policy_name)
            # Creating sub client
            self.log.info("Creating sub client %s if not exists", self.subclient)
            if not self.backupset.subclients.has_subclient(self.subclient):
                self.log.info("Subclient not exists, Creating %s", self.subclient)
                self.subclient_obj = self.backupset.subclients.add(self.subclient,
                                                                   self.policy.storage_policy_name)
                # Content
                self.subclient_obj.content = [self.tcinputs["Content"]]
            else:
                self.log.info("Sub Client exists")
                self.subclient_obj = self.backupset.subclients.get(self.subclient)
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            if self.job_obj.wait_for_completion():
                self.log.info("Backup status %s", self.job_obj.status)

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.info("Updating hosts for failure of case of pool %s", self.storage_pool_name)
            self.hyperscale_helper.start_sds_network(self.ma1)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)