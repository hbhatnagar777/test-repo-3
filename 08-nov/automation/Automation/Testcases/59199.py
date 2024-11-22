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

    update_subclient()   --  Updates the content and impersonation details

    is_jr_dir_updated_in_all_nodes()    --  Verifies that JR Dir is updated in all nodes using DCTot.cvf

    check_if_all_node_participated_in_backup()  --  Verifies that all nodes participated in backup

    update_jr_directory_in_client()   -- Updates the JR Dir of client

"""

import time
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import ConfigReader
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Multi-node backup -- JR Dir update"
        self.helper = None
        self.config_reader = None
        self.client_machine = None
        self.option_selector = None
        self.drive_letter = None
        self.all_machines = {}
        self.prev_jr_dir = None
        self.master_node = None
        self.tcinputs = {
            "Content": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        if self.subclient.backup_nodes:
            temp_client = self.commcell.clients.get(self.subclient.backup_nodes[0]["clientName"])
            self.client_machine = Machine(temp_client)
        else:
            raise Exception("Backup Nodes for subclient is Empty")

        for backup_node in self.subclient.backup_nodes:
            machine = Machine(backup_node["clientName"], commcell_object=self.commcell)
            self.all_machines[backup_node["clientName"]] = machine

        self.config_reader = ConfigReader()
        self.config_reader = self.config_reader.get_config()
        self.option_selector = OptionsSelector(self.commcell)
        self.drive_letter = self.option_selector.get_drive(machine=self.client_machine, size=500)

    def update_subclient(self):
        """
            Updates Subclient content and Impersonate User properties
        """
        if isinstance(self.tcinputs.get("Content"), list):
            self.subclient.content = self.tcinputs.get("Content")
        else:
            self.subclient.content = [self.tcinputs['Content']]
        subclient_properties = self.subclient.properties
        subclient_properties["impersonateUser"]["userName"] = self.config_reader.Network[0]
        password = self.config_reader.Network[1].encode()
        subclient_properties["impersonateUser"]["password"] = b64encode(password).decode()
        self.subclient.update_properties(subclient_properties)

    def subclient_dir_path(self, machine_instance):
        """
            Function to return subclient Dir of the client
        """
        sc_jr_items = None
        path_items = (machine_instance.client_object.job_results_directory,
                      str(self.commcell.commcell_id),
                      str(self.subclient.subclient_id))

        if machine_instance.os_info == "WINDOWS":
            sc_jr_items = path_items[:1] + ("CV_JobResults",
                                            "iDataAgent", "FileSystemAgent") + path_items[1:]

        elif machine_instance.os_info == "UNIX":
            sc_jr_items = path_items

        return machine_instance.join_path(*sc_jr_items)

    def is_jr_dir_updated_in_all_nodes(self):
        """
            Checks if JR directory is updated for all nodes using clBackup.log

            Returns:
                True/False - if JR updated/JR not updated
        """
        if len(self.all_machines) < 2:
            return True

        all_nodes = list(self.all_machines.keys())
        first_node = all_nodes[0]
        first_node_sc_dir = self.subclient_dir_path(self.all_machines[first_node])
        first_node_dc_file_path = self.all_machines[first_node].join_path(first_node_sc_dir, "DCTot.cvf")
        first_node_checksum_list = self.all_machines[first_node].get_checksum_list(first_node_dc_file_path)
        for node in all_nodes[1:]:
            curr_node_sc_dir = self.subclient_dir_path(self.all_machines[node])
            curr_node_dc_file_path = self.all_machines[first_node].join_path(curr_node_sc_dir, "DCTot.cvf")
            curr_node_checksum_list = self.all_machines[node].get_checksum_list(curr_node_dc_file_path)
            if not self.helper.compare_lists(first_node_checksum_list, curr_node_checksum_list):
                return False

        return True

    def check_if_all_node_participated_in_backup(self, job):
        """
            Checks if all node participated in backup
            Args:
                job (Job Instance) - job for this need to be verified

            Returns:
                True/False - if all participated/Not participated
        """
        for node in self.all_machines:

            machine = self.all_machines[node]

            logs = machine.get_logs_for_job_from_file(job_id=job.job_id,
                                                      log_file_name="clBackup.log",
                                                      search_term="STARTING Controller")

            if not logs:
                self.log.info("[%s] Node not participated in Backup", node)
                return False

        return True

    def update_jr_directory_in_client(self, client_name, new_jr_directory):
        """
            Updates JR directory for given client by updating client's properties:
            Args:
                client_name(str) - Name of the client

                new_jr_directory(str) - Full Path of New JR directory

            Returns:
                prev_directory(str) - returns the full path of previous directory
        """
        self.log.info("Updating Job Result directory for client [%s]", client_name)
        client = self.commcell.clients.get(client_name)
        properties = client.properties
        prev_directory = properties['client']['jobResulsDir']['path']
        properties['client']['jobResulsDir']['path'] = new_jr_directory
        client.update_properties(properties)
        self.log.info("JR directory updated to [%s]", client.properties['client']['jobResulsDir']['path'])

        return prev_directory

    def run(self):
        """Run function of this test case"""
        try:
            # setting content(if required) and updating credentials.
            self.update_subclient()

            # Run FULL backup
            self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup(backup_level="Full")
            self.log.info("Backup job: %s completed successfully", job[0].job_id)

            # verify if the JR dir is updated in all backup nodes
            self.log.info("Verifying that JR is updated for all nodes")
            if not self.is_jr_dir_updated_in_all_nodes():
                raise Exception("Job Result Directory is not Updated in all backup nodes")

            self.log.info("JR updated for all nodes.")

            # Checking if all node participated in backup
            self.log.info("Checking that all node participated in Backup")
            if not self.check_if_all_node_participated_in_backup(job[0]):
                raise Exception("All not participated in Backup")

            self.log.info("All Node Participated in Backup")

            # update default JR directory to given NewJobResultDir in TC_INPUT for master node
            self.master_node = self.helper.identify_master(job[0], self.all_machines)
            if self.master_node is None:
                raise Exception("Master Node not detected")

            new_jr_dir = self.client_machine.join_path(self.drive_letter, "JR")
            if not self.client_machine.check_directory_exists(new_jr_dir):
                self.client_machine.create_directory(new_jr_dir)

            self.prev_jr_dir = self.update_jr_directory_in_client(client_name=self.master_node,
                                                                  new_jr_directory=new_jr_dir)
            time.sleep(10)

            # Run Full backup
            self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup(backup_level="Full")
            self.log.info("Backup job: %s completed successfully", job[0].job_id)

            # Checking if all node participated in backup
            self.log.info("Checking that all node participated in Backup")
            if not self.check_if_all_node_participated_in_backup(job[0]):
                raise Exception("All not participated in Backup")

            self.log.info("All Node Participated in Backup")

            # verify if the JR dir is updated in all backup nodes
            if not self.is_jr_dir_updated_in_all_nodes():
                raise Exception("Job Result Directory is not Updated in all backup nodes")

            self.update_jr_directory_in_client(client_name=self.master_node,
                                               new_jr_directory=self.prev_jr_dir)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """JR Update of master node to prev. state"""
        if self.prev_jr_dir:
            self.update_jr_directory_in_client(client_name=self.master_node,
                                               new_jr_directory=self.prev_jr_dir)
