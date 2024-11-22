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
        self.name = "Test Case for creating 3*Node Storage Pool"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.result_string = ""
        self.backupset = ""
        self.subclient_obj = ""
        self.job_obj = ""
        self.library = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient = ""
        self.storage_policy = ""
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
        self.sql_sq_password = ""
        self.sql_login = ""
        self.policy_name = ""
        self.policy = ""
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
        self.hyperscale_helper.reassociate_all_associated_subclients(self.storage_pool_name,
                                                                     self.sql_login, self.sql_sq_password)
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
                self.log.info(
                    "Storage pool : %s is not present", self.storage_pool_name)
            # Create a fresh storage pool
            # Get disk uuids for all nodes
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
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

            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)

            self.log.info("Number of nodes in the current storage pool = %s ", str(len(rows)))
            self.log.info("Current storage pool contains the following nodes: ")
            for row in rows:
                self.log.info(row[0])
            self.log.info("Additional time for the MAs to populate the CSDB with brick health and blcok device health "
                          "info ")

            time.sleep(400)
            all_nodes = self.hyperscale_helper.get_all_nodes(self.storage_pool_name)
            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            if not gluster_brick_status:
                self.log.error("Gluster brick status bad")
            gluster_mount_status = True
            for node in rows:
                gluster_mount_status = gluster_mount_status & self.hyperscale_helper.gluster_mount(node[0])

            if not gluster_brick_status & gluster_mount_status:
                self.log.error("Gluster brick status bad")
                raise Exception("Gluster brick status bad")
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
            if self.status == constants.FAILED:
                self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                             self.sql_login, self.sql_sq_password)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
