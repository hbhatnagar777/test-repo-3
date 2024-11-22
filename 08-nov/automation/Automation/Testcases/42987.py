# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    _run_backup()       --  initiates backup job

    _run_snap_backup()  --  initiates snap backup job

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing Advanced backup option- Snapshot to backup (Netapp) test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Advanced backup option- Snapshot to backup (Netapp)"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def _run_backup(self, backup_type):
        """Initiates the backup job and waits till completion"""
        self._log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self.subclient.backup(backup_type)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason))

        self._log.info("Successfully finished %s backup", backup_type)

        return job

    def _run_snap_backup(self, backup_type, snap_name):
        """Initiates the snap backup job and waits till completeion"""
        self._log.info(
            "*" * 10 + " Starting Subclient {0} Snap Backup ".format(backup_type) + "*" * 10
        )
        self._log.info("Running backup with snap: " + snap_name)
        job = self.subclient.backup(backup_type, snap_name=snap_name)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason))
        self._log.info("Succesfully finished %s backup", backup_type)

        return job

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing %s testcase", self.id)
            inputs = self.tcinputs

            self._log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            nas_helper = NASHelper()
            options_selector = OptionsSelector(self.commcell)

            # check if intellisnap is enabled at client level
            if not self.client.is_intelli_snap_enabled:
                self._log.info("Intelli Snap is not enabled for client, enabling it.")
                self.client.enable_intelli_snap()

            self._log.info("Intelli Snap for client is enabled.")

            # Check if intellisnap is enabled at subclient level
            if not self.subclient.is_intelli_snap_enabled:
                self._log.info("Intelli snap is not enabled at subclient level, enabling it.")
                self.subclient.enable_intelli_snap("NetApp")

            self._log.info("Intelli Snap for subclient is enabled.")

            self._log.info(
                "Will run below test case on: %s subclient", str(inputs['SubclientName'])
            )

            self._log.info("Get NAS Client object")
            nas_client = nas_helper.get_nas_client(self.client, self.agent)
            self._log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(inputs['CIFSShareUser']), str(inputs['CIFSSharePassword'])
            )

            job = self._run_backup("FULL")

            full_snap_name = nas_helper.get_snap_name_from_job(str(job.job_id))
            self._log.info("Full Snap name: " + full_snap_name)

            volume_path, _ = nas_client.get_path_from_content(self.subclient.content[0])
            nas_helper.copy_test_data(nas_client, volume_path)

            job = self._run_backup("INCREMENTAL")

            inc_snap_name = nas_helper.get_snap_name_from_job(str(job.job_id))
            self._log.info("Incremental Snap name: " + inc_snap_name)

            volume_path, _ = nas_client.get_path_from_content(self.subclient.content[0])
            nas_helper.copy_test_data(nas_client, volume_path)

            job = self._run_backup("DIFFERENTIAL")

            diff_snap_name = nas_helper.get_snap_name_from_job(str(job.job_id))
            self._log.info("Differential Snap name: " + diff_snap_name)

            self._log.info("Disabling Intellisnap on subclient.")
            self.subclient.disable_intelli_snap()

            self._run_snap_backup("FULL", snap_name=full_snap_name)

            self._run_snap_backup("INCREMENTAL", snap_name=inc_snap_name)

            self._run_snap_backup("DIFFERENTIAL", snap_name=diff_snap_name)

            size = nas_client.get_content_size(self.subclient.content)

            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            self._log.info("*" * 10 + " Run out of place restore to Windows Client" + "*" * 10)
            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name,
                windows_restore_location,
                self.subclient.content)

            self._log.info(
                "Started Restore out of place restore with job id: %s", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + job.delay_reason
                )

            nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                self.subclient.content)

            self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            job = self.subclient.restore_in_place([self.subclient.content[0]])

            self._log.info("Started Restore in place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: " + job.delay_reason
                )

            self._log.info("Successfuly finished restore in place job")

            nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                [self.subclient.content[0]]
            )

        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
