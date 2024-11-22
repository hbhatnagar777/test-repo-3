# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for Resiliency data Test"""
import os
import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from MediaAgents.mediaagentconstants import DUMMY_DATA


class TestCase(CVTestCase):

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for resiliency data consistency test"
        self.show_to_user = True
        self.result_string = ""
        self.username = None
        self.password = None
        self.client = None
        self.media_agent = None
        self.control_nodes = {}
        self.ma1 = None
        self.ma2 = None
        self.ma3 = None
        self.storage_pool_name = None
        self.sql_sq_password = None
        self.sql_login = None
        self.hyperscale_helper = None
        self.test_data_file = None
        self.verify_data_file = None
        self.content = None
        self.script_content = ""
        self.script_path = ""
        self.script = ""
        self.script_name = ""
        self.dummy_data = None
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
        self.test_data_file = "/ws/glus/test.txt"
        self.verify_data_file = "/ws/glus/v1.txt"
        self.dummy_data = DUMMY_DATA['dummy_data']
        self.script_name = self.id + "_script.py"
        self.script = os.getcwd() + self.script_name
        self.script_path = os.path.abspath(self.script)
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        self.log.info("Bringing Up the down networks")
        self.hyperscale_helper.ma_service_up(self.ma1)
        self.hyperscale_helper.ma_service_up(self.ma2)
        self.hyperscale_helper.start_sds_network(self.ma1)
        self.hyperscale_helper.start_sds_network(self.ma2)
        self.log.info("deleting the paths")
        ma_session2 = Machine(self.ma2, self.commcell)
        ma_session3 = Machine(self.ma3, self.commcell)
        ma_session2.execute_command("rm -rf {0}".format(self.test_data_file))
        ma_session2.execute_command("rm -rf {0}".format(self.verify_data_file))
        ma_session2.execute_command("rm -rf /root/{0}".format(self.script_name))
        ma_session3.execute_command("rm -rf /root/{0}".format(self.script_name))
        if os.path.exists(self.script):
            os.remove(self.script)
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
            self.log.info("Additional time for the MAs to populate the CSDB with brick health and blcok device health "
                          "info ")

            time.sleep(300)
            all_nodes = self.hyperscale_helper.get_all_nodes(self.storage_pool_name)

            gluster_brick_status = self.hyperscale_helper.gluster_disk_health(all_nodes, disk_uuids)
            if not gluster_brick_status:
                self.log.error("Gluster brick status bad")

            self.log.info("Bringing down node %s ", self.ma1)
            self.hyperscale_helper.ma_service_down(self.ma1)
            self.hyperscale_helper.kill_sds_network(self.ma1)

            self.log.info("Creating local script to be executed on remote machine")
            self.script_content = """   
#!/usr/bin/python\n
import os\n
import random\n
dummy_data = "{0}"\n
test_data_file = "{1}"\n
verify_data_file = "{2}"\n
count = random.randint(20, 100)\n
while count > 0:\n
\tfile = open(test_data_file, "a")\n
\tfile.write(dummy_data)\n
\tos.fsync(file)\n
\tfile.close()\n
\tcount -= 1\n

file = open(test_data_file, "a")\n
pos = file.tell()\n
file.close()\n
file = open(test_data_file, "r")\n
file2 = open(verify_data_file, "w")\n
file2.write(file.read(pos))\n
os.fsync(file2)\n
file2.close()\n
file.close()\n
print(pos)\n""".format(self.dummy_data, self.test_data_file, self.verify_data_file)
            with open(self.script_path, "w+") as f:
                f.writelines(self.script_content)
            self.log.info("script is %s", self.script_content)
            # time.sleep(300)
            self.log.info("Creating machine for all nodes")
            ma_session1 = Machine(self.ma1, self.commcell)
            ma_session2 = Machine(self.ma2, self.commcell)
            ma_session3 = Machine(self.ma3, self.commcell)
            self.log.info("Copying script to remote host %s for execution", self.ma2)

            self.log.info("Script path %s", self.script_path)
            ma_session2.copy_from_local(self.script_path, "/root")
            self.log.info("Executing script over host %s ", self.ma2)
            command = "( cd /root && python ./{0} )".format(self.script_name)
            self.log.info(command)
            output = ma_session2.execute_command(command)
            offset_pos = output.output
            self.log.info("Offset till written is %s ", offset_pos)

            self.log.info("Copying script to remote host %s for execution", self.ma3)
            ma_session3.copy_from_local(self.script_path, "/root")
            self.log.info("Executing script over host %s ", self.ma3)
            command = "( cd /root && python ./{0} )".format(self.script_name)
            self.log.info(command)
            output = ma_session3.execute_command(command)
            offset_pos = output.output
            self.log.info("Offset till written is %s ", offset_pos)

            self.log.info("Bringing one more node down to hit resiliency, node %s", self.ma2)
            self.hyperscale_helper.ma_service_down(self.ma2)
            self.hyperscale_helper.kill_sds_network(self.ma2)
            self.log.info("Waiting 10 mins and than bringing all nodes up")
            time.sleep(600)

            self.hyperscale_helper.ma_service_up(self.ma1)
            self.hyperscale_helper.ma_service_up(self.ma2)
            self.hyperscale_helper.start_sds_network(self.ma1)
            self.hyperscale_helper.start_sds_network(self.ma2)

            self.log.info("waiting some time")
            time.sleep(300)

            self.log.info("Reading data till offset %s from node1 %s and verifying data consistency", offset_pos,
                          self.ma1)
            compare1 = ma_session1.compare_checksum(self.test_data_file, self.verify_data_file)
            if compare1[0]:
                self.log.info("data consistent till offset written, verified from host %s", self.ma1)

            self.log.info("Reading data till offset %s from node2 %s and verifying data consistency", offset_pos,
                          self.ma2)
            compare2 = ma_session2.compare_checksum(self.test_data_file, self.verify_data_file)
            if compare2[0]:
                self.log.info("data consistent till offset written, verified from host %s", self.ma2)

            self.log.info("Reading data till offset %s from node3 %s and verifying data consistency", offset_pos,
                          self.ma3)
            compare3 = ma_session3.compare_checksum(self.test_data_file, self.verify_data_file)
            if compare3[0]:
                self.log.info("data consistent till offset written, verified from host %s", self.ma3)

            if compare1[0] and compare2[0] and compare3[0]:
                self.log.info("Data consistent")
            else:
                self.log.info("Data not consistent")

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
