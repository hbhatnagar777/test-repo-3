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

    base_path()     --  returns the base path for a given full path

    update_subclient()    --  Updates the content and impersonation details

    run_backup_suspend_resume()  --  Runs a backup job, suspends and resumes it.

"""

import time
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import ConfigReader
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Multi-node automation - Restartability"
        self.helper = None
        self.client_machine = None
        self.config_reader = None
        self.drive_letter = None
        self.option_selector = None
        self.restore_directory = None
        self.username = None
        self.password = None
        self.tcinputs = {
            "Content": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.helper = FSHelper(self)
        self.tcinputs['DataAccessNodes'] = [access_node["clientName"] for access_node in self.subclient.backup_nodes]
        FSHelper.populate_tc_inputs(self, mandatory=False)
        self.config_reader = ConfigReader()
        self.config_reader = self.config_reader.get_config()
        self.username = self.config_reader.Network[0]
        self.password = self.config_reader.Network[1]
        self.option_selector = OptionsSelector(self.commcell)
        self.drive_letter = self.option_selector.get_drive(self.client_machine)
        self.restore_directory = self.client_machine.join_path(self.drive_letter, 'RestorePath')
        if not self.client_machine.check_directory_exists(self.restore_directory):
            self.client_machine.create_directory(directory_name=self.restore_directory)
            self.log.info("Created Restore Directory [%s]", self.restore_directory)

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

    def run_backup_suspend_resume(self):
        """
            1. Performs a backup
            2. Suspends the backup in backup phase
            3. Resumes the backup again

            Returns:
                job (job instance of the backup job)
        """
        # Run FULL backup and wait until scan phase completed
        self.log.info("Running Full backup job on subclient %s", self.subclient.subclient_name)
        job = self.helper.run_backup(backup_level="Full", wait_to_complete=False)[0]

        while not job.phase.upper() == 'BACKUP':
            time.sleep(15)

        self.log.info("Scan Phase completed")
        if 'WaitTime' in self.tcinputs.keys():
            time.sleep(int(self.tcinputs.get('WaitTime')))
        else:
            time.sleep(15)

        # suspending the backup job
        self.log.info("Suspending Job %s", job.job_id)
        job.pause(wait_for_job_to_pause=True)
        self.log.info("Job Suspended Successfully")
        time.sleep(15)

        # resuming backup job
        self.log.info("Resuming Job %s", job.job_id)
        job.resume(wait_for_job_to_resume=True)
        self.log.info("Job Resumed Successfully")

        # waiting till backup completes
        self.log.info("Waiting for completion of Full backup with Job ID: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run FULL backup with error: {job.delay_reason}"
            )

        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job

    def run(self):
        """Run function of this test case"""
        try:
            # setting content and updating credentials.
            self.update_subclient()

            # running backup, suspending and resuming and waiting until it completes
            self.run_backup_suspend_resume()

            # verifying if the backup ran successfully
            paths = []
            for path in self.subclient.content:
                if "\\\\" in path:
                    paths.append(path.replace("\\\\", "UNC-NT_"))
                else:
                    paths.append(path)

            # checking that back up ran successfully.
            self.helper.restore_out_of_place(destination_path=self.restore_directory,
                                             paths=paths)

            self.log.info("Comparing Checksum")
            if not self.client_machine.compare_checksum(source_path=self.subclient.content,
                                                        destination_path=self.restore_directory):
                raise Exception("Checksum not matched, Contents are not backed up successfully")

            self.log.info("Checksum matched, Contents backed up successfully")
            self.client_machine.remove_directory(self.restore_directory)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.client_machine.remove_directory(self.restore_directory)
