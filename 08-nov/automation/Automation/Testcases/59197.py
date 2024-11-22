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

    mount_paths()       --  Mounts the given path to client machine

    check_backup_failures()    --  Checks if any file is failed to backup using Failures.cvf file

    is_backup_successful()      --  Checks if data is backed up successfully

"""

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
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Multi-Node backup - File Lock and backup"
        self.helper = None
        self.client_machine = None
        self.data_access_nodes = None
        self.config_reader = None
        self.drive_letter = None
        self.operation_selector = None
        self.restore_directory = None
        self.client_node = None
        self.is_client_network_share = True
        self.username = None
        self.password = None
        self.tcinputs = {
            "Content": None,
            "LockContent": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        self.data_access_nodes = self.subclient.backup_nodes
        if self.data_access_nodes:
            temp_client = self.commcell.clients.get(self.data_access_nodes[0]["clientName"])
            self.client_machine = Machine(temp_client)
            self.client_node = self.data_access_nodes[0]["clientName"]
        else:
            raise Exception("Backup Nodes for subclient is Empty")

        self.config_reader = ConfigReader()
        self.config_reader = self.config_reader.get_config()
        self.username = self.config_reader.Network[0]
        self.password = self.config_reader.Network[1]
        self.operation_selector = OptionsSelector(self.commcell)
        self.drive_letter = self.operation_selector.get_drive(self.client_machine)
        self.restore_directory = self.client_machine.join_path(self.drive_letter, 'RestorePath')
        if not self.client_machine.check_directory_exists(self.restore_directory):
            self.client_machine.create_directory(directory_name=self.restore_directory)
            self.log.info("Created Restore Directory [%s]", self.restore_directory)

    def update_subclient(self):
        """
            Updates Subclient content and Impersonate User properties
        """
        if isinstance(self.tcinputs.get("Content"), list):
            self.subclient.content = self.tcinputs.get("Content")
        else:
            self.subclient.content = [self.tcinputs.get("Content")]
        subclient_properties = self.subclient.properties
        subclient_properties["impersonateUser"]["userName"] = self.username
        subclient_properties["impersonateUser"]["password"] = b64encode(self.password.encode()).decode()
        self.subclient.update_properties(subclient_properties)

    def mount_paths(self, paths):
        """
            mounts the given paths to client machine
            Args:
                paths (list) - list of paths to mount
        """
        for path in paths:
            if not self.client_machine.check_directory_exists(path):
                self.client_machine.mount_network_path(network_path=path,
                                                       username=self.username,
                                                       password=self.password)
                if not self.client_machine.check_directory_exists(path):
                    raise Exception(f"Error in mounting path [{path}]")

    def check_backup_failures(self):
        """
            Checks if any file is failed to backup using Failures.cvf file
            Returns:
                (bool) - True/False if (failed/not failed)
        """
        remaining_path = "CV_JobResults\\iDataAgent\\FileSystemAgent\\2"
        client_instance = self.client_machine.machine_name
        job_results_directory = self.commcell.clients.get(client_instance).job_results_directory
        subclient_directory = self.client_machine.join_path(job_results_directory,
                                                            remaining_path,
                                                            self.subclient.subclient_id)

        failure_file_path = self.client_machine.join_path(subclient_directory, "Failures.cvf")
        file_content = self.client_machine.read_file(file_path=failure_file_path)
        if len(file_content) > 0:
            failed_contents = "Failed Contents:\n"
            lines = file_content.split("\r\n")
            for line in lines[:-1]:
                tokens = line.split("|")
                failed_contents += tokens[0] + "\n"

            self.log.info(failed_contents)
            return True

        return False

    def is_backup_successful(self, content_paths):
        """
            Checks if data is backed up successfully
            Args:
                content_paths (list) - Paths to be verified

            Returns:
                bool - True/False denoting (success/failure)
        """
        paths = []
        for path in content_paths:
            if "\\\\" in path:
                paths.append(path.replace("\\\\", "UNC-NT_"))
            else:
                paths.append(path)

        # checking that back up ran successfully.
        self.helper.restore_out_of_place(destination_path=self.restore_directory,
                                         paths=paths)

        self.log.info("Comparing Checksum")
        return self.client_machine.compare_checksum(source_path=content_paths,
                                                    destination_path=self.restore_directory)

    def run(self):
        """Run function of this test case"""
        try:
            # setting content and updating credentials.
            self.update_subclient()

            # mounting subclient contents in order to make the contents accessible
            # using lock_file() functions
            if isinstance(self.tcinputs.get("Content"), list):
                self.mount_paths(paths=self.tcinputs.get("Content"))
            else:
                self.mount_paths(paths=[self.tcinputs.get("Content")])

            # Locking LockContent file
            self.log.info("Locking files [%s] for [%s] seconds", self.tcinputs.get("LockContent"), 1200)
            pid = self.client_machine.lock_file(file=self.tcinputs.get("LockContent"), interval=1200)

            # Run FULL backup
            self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup(backup_level="Full")
            self.log.info("Backup job: %s completed successfully", job[0].job_id)

            # checking if any file failed
            if not self.check_backup_failures():
                self.log.info("No files found in Failure.cvf")
                if self.is_backup_successful(self.subclient.content):
                    self.log.info("No files failed, Either files are not locked properly OR "
                                  "files do not belongs to Subclient content\n"
                                  "Terminating run() function")
                    return

            # unlocking content
            self.client_machine.kill_process(process_id=str(pid))

            # Run INCR backup
            self.log.info("Running Incremental backup job on subclient %s", self.subclient.subclient_name)
            job = self.helper.run_backup()
            self.log.info("Backup job: %s completed successfully", job[0].job_id)

            locked_contents = []
            if isinstance(self.tcinputs.get("LockContent"), list):
                locked_contents = self.tcinputs.get("LockContent")
            else:
                locked_contents = [self.tcinputs.get("LockContent")]

            if self.is_backup_successful(locked_contents):
                self.log.info("Checksum matched, Contents backed up successfully")
            else:
                raise Exception(
                    "Checksum not matched, Contents are not backed up successfully"
                )

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
