# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for Resiliency Performance Test"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils import constants
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Hyperscale test class for creating and deleting storage pools"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for resiliency performance test"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.result_string = ""
        self.subclient_obj = None
        self.job_obj = None
        self.policy = None
        self.policy_name = None
        self.username = None
        self.password = None
        self.client = None
        self.media_agent = None
        self.backup_content = None
        self.restore_path = None
        self.control_nodes = {}
        self.ma1 = None
        self.ma2 = None
        self.ma3 = None
        self.storage_pool_name = None
        self.sql_sq_password = None
        self.sql_login = None
        self.hyperscale_helper = None
        self.library_name = None
        self.mount_path = None
        self.copy_policy = None
        self.copy_policy_obj = None
        self.mas = []
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
        self.library_name = "dummy_library_" + self.id
        self.mount_path = self.client.install_directory + self.id
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        time.sleep(30)
        cs_machine = Machine(self.commcell.commserv_name, self.commcell)
        self.log.info("Deleting sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.log.info("Deleting secondary copy")
        if self.policy.has_copy(self.copy_policy):
            self.policy.delete_secondary_copy(self.copy_policy)
        self.log.info("Deleting policy created for backup job")
        self.hyperscale_helper.reassociate_all_associated_subclients(self.storage_pool_name,
                                                                     self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
        self.log.info("Deleting dummy library")
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.commcell.disk_libraries.delete(self.library_name)
        self.log.info("removing mount path directory")
        if cs_machine.check_directory_exists(self.mount_path):
            cs_machine.remove_directory(self.mount_path)
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
            else:
                self.log.info("Storage Pool creation Successful")

            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the current storage pool = %s", str(len(rows)))
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

            self.log.info("\nBACKUP ON DISK LIBRARY, AUX COPY OVER POOL\n")
            self.log.info("Creating dummy Disk library")
            self.log.info("Library %s and mount path %s", self.library_name, self.mount_path)
            self.log.info("Check if library exists")
            cs_machine = Machine(self.commcell.commserv_name, self.commcell)
            if not self.commcell.disk_libraries.has_library(self.library_name):
                if not cs_machine.check_directory_exists(self.mount_path):
                    cs_machine.create_directory(self.mount_path)
                disk_library = self.commcell.disk_libraries.add(self.library_name, self.commcell.commserv_name,
                                                                self.mount_path)
            else:
                self.log.info("library already present")
                disk_library = self.commcell.disk_libraries.get(self.library_name)

            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.library_name,
                                                                 self.commcell.commserv_name)
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
            job_id1 = self.job_obj.job_id
            if self.job_obj.wait_for_completion():
                self.log.info("Backup status %s", self.job_obj.status)

            self.log.info("Running aux copy job over pool")
            self.log.info("Creating secondary copy policy for %s", self.policy.storage_policy_name)
            self.copy_policy = self.policy.storage_policy_name + "copy"
            if not self.policy.has_copy(self.copy_policy):
                self.copy_policy_obj = self.policy.create_secondary_copy(
                    self.copy_policy,
                    self.hyperscale_helper.get_library_details(library_id)[2],
                    self.ma1)
            else:
                self.log.info("Copy policy exists")
                self.copy_policy_obj = self.policy.get_copy(self.copy_policy)
            copy_job = self.policy.run_aux_copy(self.copy_policy, self.commcell.commserv_name)
            job_id2 = copy_job.job_id
            if copy_job.wait_for_completion():
                self.log.info("Aux copy job status %s", self.job_obj.status)
            self.hyperscale_helper.bkp_job_details(job_id1)
            self.hyperscale_helper.admin_job_details(job_id2)
            # Deleting created objects for backup
            time.sleep(30)
            self.log.info("Deleting sub clients created for backup job")
            self.backupset.subclients.delete(self.subclient)
            self.log.info("Deleting secondary copy")
            self.policy.delete_secondary_copy(self.copy_policy)
            self.log.info("Deleting policy created for backup job")
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
            self.log.info("Deleting dummy library")
            self.commcell.disk_libraries.delete(self.library_name)
            self.log.info("removing mount path directory")
            cs_machine.remove_directory(self.mount_path)

            self.log.info("\nBACKUP ON POOL, AUX COPY OVER DISK\n")

            self.log.info("Creating dummy Disk library")
            self.log.info("Library %s and mount path %s", self.library_name, self.mount_path)
            self.log.info("Check if library exists")
            if not self.commcell.disk_libraries.has_library(self.library_name):
                cs_machine = Machine(self.commcell.commserv_name, self.commcell)
                if not cs_machine.check_directory_exists(self.mount_path):
                    cs_machine.create_directory(self.mount_path)
                disk_library = self.commcell.disk_libraries.add(self.library_name,
                                                                self.commcell.commserv_name, self.mount_path)
                self.log.info("Created library")
            else:
                self.log.info("library already present")
                disk_library = self.commcell.disk_libraries.get(self.library_name)
            # Running backup
            # Creating Plan
            self.commcell.storage_pools.refresh()
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(
                                                                     library_id)[2],
                                                                 self.ma1, global_policy_name=
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
                self.log.info("Sub Client created")
            else:
                self.log.info("Sub Client exists")
                self.subclient_obj = self.backupset.subclients.get(self.subclient)
            # Starting backup
            self.log.info("Starting Backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            job_id3 = self.job_obj.job_id
            if self.job_obj.wait_for_completion():
                self.log.info("Backup status %s", self.job_obj.status)

            self.log.info("Running aux copy job over pool")
            self.log.info("Creating secondary copy policy for %s", self.policy.storage_policy_name)
            self.copy_policy = self.policy.storage_policy_name + "_copy"
            self.commcell.refresh()
            if not self.policy.has_copy(self.copy_policy):
                self.copy_policy_obj = self.policy.create_secondary_copy(
                    self.copy_policy,
                    self.library_name,
                    self.commcell.commserv_name)
            else:
                self.log.info("Copy policy exists")
                self.copy_policy_obj = self.policy.get_copy(self.copy_policy)
            copy_job = self.policy.run_aux_copy(self.copy_policy, self.ma1)
            job_id4 = copy_job.job_id
            if copy_job.wait_for_completion():
                self.log.info("Aux copy job status %s", self.job_obj.status)

            self.hyperscale_helper.bkp_job_details(job_id3)
            self.hyperscale_helper.admin_job_details(job_id4)
            # Deleting created objects for backup
            time.sleep(30)
            self.log.info("Deleting sub clients created for backup job")
            self.backupset.subclients.delete(self.subclient)
            self.log.info("Deleting secondary copy")
            self.policy.delete_secondary_copy(self.copy_policy)
            self.log.info("Deleting policy created for backup job")
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
            self.log.info("Deleting dummy library")
            self.commcell.disk_libraries.delete(self.library_name)
            self.log.info("removing mount path directory")
            cs_machine.remove_directory(self.mount_path)

            self.log.info("\nBACKUP OVER POOL, AUX COPY OVER POOL\n")

            # Running backup
            # Creating Plan
            self.commcell.storage_pools.refresh()
            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(
                                                                     library_id)[2],
                                                                 self.ma1, global_policy_name=
                                                                 self.hyperscale_helper.get_policy_details(gdsp)[2])
            else:
                self.log.info("Policy exists")
                # self.commcell.storage_policies.delete(self.policy_name)
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
            job_id5 = self.job_obj.job_id
            if self.job_obj.wait_for_completion():
                self.log.info("Backup status %s", self.job_obj.status)

            self.log.info("Running aux copy job over pool")
            self.log.info("Creating secondary copy policy for %s", self.policy.storage_policy_name)
            self.copy_policy = self.policy.storage_policy_name + "_copy"
            self.commcell.refresh()
            if not self.policy.has_copy(self.copy_policy):
                self.copy_policy_obj = self.policy.create_secondary_copy(
                    self.copy_policy,
                    str(self.hyperscale_helper.get_library_details(library_id)[2]),
                    self.ma1)
            else:
                self.log.info("Copy policy exists")
                self.copy_policy_obj = self.policy.get_copy(self.copy_policy)
            copy_job = self.policy.run_aux_copy(self.copy_policy, self.ma1)
            job_id6 = copy_job.job_id
            if copy_job.wait_for_completion():
                self.log.info("Aux copy job status %s", self.job_obj.status)

            self.hyperscale_helper.bkp_job_details(job_id5)
            self.hyperscale_helper.admin_job_details(job_id6)
            # Deleting created objects for backup
            time.sleep(30)
            self.log.info("Deleting sub clients created for backup job")
            self.backupset.subclients.delete(self.subclient)
            self.log.info("Deleting secondary copy")
            self.policy.delete_secondary_copy(self.copy_policy)
            self.log.info("Deleting policy created for backup job")
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
