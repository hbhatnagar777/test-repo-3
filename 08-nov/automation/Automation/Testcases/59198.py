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

    update_subclient()    --  Updates the content and impersonation details

    base_path()       --  returns the base path for a given full path

    tear_down()     --  tear down function of this test case

"""

import time
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.config import ConfigReader
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.winfshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Multi-node backup -- master services down during backup"
        self.helper = None
        self.client_machine = None
        self.data_access_nodes = None
        self.config_reader = None
        self.drive_letter = None
        self.option_selector = None
        self.restore_directory = None
        self.username = None
        self.password = None
        self.master_node_hostname = None
        self.master_node_install_path = None
        self.all_machines = {}
        self.tcinputs = {
            "Content": None,
            "master_username": None,
            "master_password": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        self.tcinputs['DataAccessNodes'] = [access_node["clientName"] for access_node in self.subclient.backup_nodes]
        FSHelper.populate_tc_inputs(self, mandatory=False)
        for backup_node in self.subclient.backup_nodes:
            machine = Machine(backup_node["clientName"], commcell_object=self.commcell)
            self.all_machines[backup_node["clientName"]] = machine
        self.config_reader = ConfigReader()
        self.config_reader = self.config_reader.get_config()
        self.username = self.config_reader.Network[0]
        self.password = self.config_reader.Network[1]
        self.option_selector = OptionsSelector(self.commcell)
        self.drive_letter = self.option_selector.get_drive(self.client_machine)

    def update_subclient(self):
        """
            Updates Subclient content and Impersonate User properties
        """
        if isinstance(self.tcinputs.get("Content"), list):
            self.subclient.content = self.tcinputs.get("Content")
        else:
            self.subclient.content = [self.tcinputs['Content']]
        subclient_properties = self.subclient.properties
        subclient_properties["impersonateUser"]["userName"] = self.username
        subclient_properties["impersonateUser"]["password"] = b64encode(self.password.encode()).decode()
        self.subclient.update_properties(subclient_properties)

    @staticmethod
    def base_path(full_path):
        """
            Returns leaf-data path/base path for a given full path

            Args:
                full_path (str) - path

            Returns:
                (str) - basename of the path
        """
        if "/" in full_path:
            return full_path.split("/")[-1]

        return full_path.split("\\")[-1]

    def run(self):
        """Run function of this test case"""
        try:
            # setting content and updating credentials.
            self.update_subclient()

            # Run FULL backup
            self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            while not job.phase.upper() == 'BACKUP':
                time.sleep(10)

            # wait until backup state is running
            while not job.status.upper() == "RUNNING":
                time.sleep(5)

            self.log.info("identifying Master node")
            master_node = self.helper.identify_master(job, self.all_machines)
            self.log.info("Master node identified [%s]", master_node)
            if master_node is None:
                raise Exception("Master Node not detected")

            master_node_client = self.commcell.clients.get(master_node)
            self.master_node_hostname = master_node_client.client_hostname
            self.master_node_install_path = master_node_client.install_directory
            self.log.info("Shutting down master node services")
            master_node_client.stop_service(f"GxCVD({master_node_client.instance})")

            while not job.status.upper() == "PENDING":
                time.sleep(30)

            self.log.info("Resuming Backup job")
            job.resume(wait_for_job_to_resume=True)

            # waiting till backup completes
            self.log.info("Waiting for completion of Full backup with Job ID: %s", str(job.job_id))
            if not job.wait_for_completion(timeout=300):
                raise Exception(f"Failed to run FULL backup with error: {job.delay_reason}")

            self.log.info("Backup job: %s completed successfully", job.job_id)

            paths = []
            for path in self.subclient.content:
                if "\\\\" in path:
                    paths.append(path.replace("\\\\", "UNC-NT_"))
                else:
                    paths.append(path)

            # checking that back up ran successfully.
            self.log.info("Verifying if Backup ran successfully")
            self.restore_directory = self.client_machine.join_path(self.drive_letter, 'RestorePath')
            if self.client_machine.check_directory_exists(self.restore_directory):
                self.client_machine.remove_directory(directory_name=self.restore_directory)

            self.client_machine.create_directory(directory_name=self.restore_directory)
            self.log.info("Created Restore Directory [%s]", self.restore_directory)
            self.helper.restore_out_of_place(destination_path=self.restore_directory,
                                             paths=paths)

            self.log.info("Comparing Checksum")
            if not self.client_machine.compare_checksum(source_path=self.subclient.content,
                                                        destination_path=self.restore_directory):
                raise Exception("Checksum not matched, Contents are not backed up successfully")

            self.log.info("Checksum matched, Contents backed up successfully")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Cleanup process"""
        self.client_machine.remove_directory(self.restore_directory)
        if self.master_node_hostname:
            self.log.info("Restarting Services of master Node")
            machine = Machine(machine_name=self.master_node_hostname,
                              username=self.tcinputs.get("master_username"),
                              password=self.tcinputs.get("master_password"))
            command = machine.join_path(self.master_node_install_path, "Base", "GxAdmin.exe") \
                      + " -console -startsvcgrp ALL"
            output = machine.execute_command(command)
            if output.exit_code != 0:
                raise Exception('failed to stop the services')
