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
        self.name = "Test case for reconfigure storage pool hyperscale"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.result_string = ""
        self.subclient_obj = ""
        self.job_obj = ""
        self.policy = ""
        self.policy_name = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.media_agent = ""
        self.backup_content = ""
        self.restore_path = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.ma4 = ""
        self.ma5 = ""
        self.ma6 = ""
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.hyperscale_helper = None
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

    def run(self):
        """Run function of this test case"""
        try:

            status = self.hyperscale_helper.check_if_storage_pool_is_present(self.storage_pool_name)
            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the expanded storage pool = %s ", str(len(rows)))
          
            if status is True:
                self.log.info("Storage pool : %s already present, attempting deletion", self.storage_pool_name)
                self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                             self.sql_login, self.sql_sq_password)
                time.sleep(30)
            else:
                self.log.info(
                    "Storage pool : %s is not present", self.storage_pool_name)

            # Create a fresh storage pool
            time.sleep(30)
            # Get disk uuids for all nodes
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
            self.log.info("Wait for hosts to get available for SP creation\t"
                          "Get host ids for the MAs")
            all_ma_ids = {}
            for media_agent in self.control_nodes:
                all_ma_ids[self.control_nodes[media_agent]] = self.hyperscale_helper.get_host_id(
                    self.control_nodes[media_agent])
            self.log.info("All ma and ids %s", all_ma_ids)
            ma_ids = all_ma_ids.values()
            self.log.info("Host ids are %s", ma_ids)
            self.log.info("creating storage pool: %s", self.storage_pool_name)

            # Failing pool creation
            self.log.info("Failing pool creation %s", self.storage_pool_name)
            self.hyperscale_helper.false_hosts(self.ma2)

            # Creating storage pool
            status, response = self.hyperscale_helper.create_storage_pool(self.storage_pool_name,
                                                                          self.ma1, self.ma2,
                                                                          self.ma3)
            status = self.hyperscale_helper.validate_storage(self.storage_pool_name)

            self.log.info("Storage Pool creation failed status %s", status)
            self.log.info(response)

            storage_pool_details = self.hyperscale_helper.get_storage_pool_details(self.storage_pool_name)
            library_id = storage_pool_details._storage_pool_properties['storagePoolDetails']['libraryList'][0][
                'library']['libraryId']
            gdsp = storage_pool_details.storage_pool_id

            # Updating hosts for reconfigure storage pool
            self.log.info("Updating hosts for reconfigure storage pool %s", self.storage_pool_name)
            self.hyperscale_helper.true_hosts(self.ma2)

            # Checking resolution error, verifying bricks still not used due to some error
            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Reconfiguring Storage pool %s ", self.storage_pool_name)
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
            self.commcell.refresh()
            self.log.info("Waiting to populate")
            time.sleep(300)
            disk_same_status = self.hyperscale_helper.verify_gluster_disk_uuids(self.ma1, disk_uuids)
            if disk_same_status:
                self.log.info("disks used are same")
            else:
                self.log.info("disks used are not same")

            # Checking bricks health status of gluster
            self.log.info("Checking brick health status for %s ", self.storage_pool_name)
            self.hyperscale_helper.get_all_nodes_hostids(self.storage_pool_name)
            all_nodes = self.hyperscale_helper.get_all_nodes(self.storage_pool_name)
            self.log.info("Waiting CSDB to populate")
            time.sleep(400)
            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            if not gluster_brick_status:
                self.log.error("Gluster brick status bad")

            # Checking gluster vol information
            vol_status = True
            pool_nodes = self.hyperscale_helper.get_all_nodes_hostids(self.storage_pool_name)
            for node_id in pool_nodes:
                hostname = self.hyperscale_helper.get_hostname(node_id)
                if not self.hyperscale_helper.check_new_gluster_volume_size(hostname):
                    vol_status = False
                    break
            if not vol_status:
                self.log.error('Gluster vol size available is not permissible')
            self.log.info("gluster volume size is good and permissible")

            status = False
            trys = 5
            while status is False and trys != 0:
                status = self.hyperscale_helper.check_if_storage_pool_is_present(self.storage_pool_name)
                if status is False:
                    self.log.info("Storage pool %s not present, waiting to add again",
                                  self.storage_pool_name)
                time.sleep(30)
                trys -= 1

            if status is False:
                raise Exception("Storage Pool %s creation failed",
                                self.storage_pool_name)
            self.log.info("Storage Pool %s creation Successful", self.storage_pool_name)
            self.log.info("MAs %s are associated with Storage Pool %s ",
                          all_nodes, self.storage_pool_name)

            # Running backup
            # Creating Plan
            self.log.info("running Backup")
            self.log.info("Creating Policy")
            self.policy_name = self.id + "_Policy1"
            if not self.commcell.storage_policies.has_policy(self.policy_name):
                self.log.info("Policy not exists, Creating %s", self.policy_name)
                self.policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.hyperscale_helper.get_library_details(library_id)[2],
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
            self.log.info("Updating hosts because of failure")
            self.hyperscale_helper.true_hosts(self.ma2)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)

    def tear_down(self):
        """Tear down function of this test case"""
        # Deleting created objects for backup
        time.sleep(30)
        self.log.info("Deleting policy and sub clients created for backup job")
        if self.backupset.subclients.has_subclient(self.subclient):
            self.backupset.subclients.delete(self.subclient)
        self.hyperscale_helper.reassociate_all_associated_subclients(self.storage_pool_name,
                                                                     self.sql_login, self.sql_sq_password)
        if self.commcell.storage_policies.has_policy(self.policy_name):
            self.commcell.storage_policies.delete(self.policy.storage_policy_name)
