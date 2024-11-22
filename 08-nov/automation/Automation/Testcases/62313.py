# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    _run_backup()       --  initiates backup job

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Wild Card content for Subclient Content and Filter"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "NAS NDMP - Data having Alternate data streams"
        self._nas_helper = NASHelper()
        self.tcinputs = {
            "AgentName": None,
            "BackupsetName": None,
            "CIFSSharePassword": None,
            "CIFSShareUser": None,
            "ClientName": None,
            "FilerRestoreLocation": None,
            "SubclientContent": None,
            "SubclientName": None
        }

    def ads_count(self, job, MAMachine):
        line1 = MAMachine.get_logs_for_job_from_file(job.job_id, "NasBackup.log", "CV_ADS=")
        l1 = line1.split("CV_ADS=")
        return int(l1[-1])

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            options_selector = OptionsSelector(self.commcell)
            self.log.info("Get NAS client object")
            nas_client = self._nas_helper.get_nas_client(self.client, self.agent, is_cluster=self.tcinputs.get("is_cluster", False))
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )
            self.log.info(f"Will run below test case on: {self.subclient} subclient")

            if self.subclient.is_intelli_snap_enabled:
                self.log.info("Disabling Intellisnap on subclient.")
                self.subclient.disable_intelli_snap()

            # run full backup
            job = self._nas_helper.run_backup(self.subclient, "FULL")
            maclient = self.commcell.clients.get(self.subclient.storage_ma)
            mamachine = Machine(maclient)
            ads_count = self.ads_count(job, mamachine)
            if ads_count == 0:
                raise Exception(
                    "Backup data doesn't contain Alternate Data Streams, please add and rerun")
            else:
                self.log.info("Alternate data streams are present in backup data")
                self.log.info(f"No.of ADS present are {ads_count}")
            for content in self.subclient.content:
                volume_path, _ = nas_client.get_path_from_content(content)
                self._nas_helper.copy_test_data(nas_client, volume_path)

            self._nas_helper.run_backup(self.subclient, "INCREMENTAL")

            for content in self.subclient.content:
                volume_path, _ = nas_client.get_path_from_content(content)
                self._nas_helper.copy_test_data(nas_client, volume_path)

            self._nas_helper.run_backup(self.subclient, "DIFFERENTIAL")
            size = nas_client.get_content_size(self.subclient.content)
            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            self.log.info("*" * 10 + " Run out of place restore to windows client" + "*" * 10)

            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name, windows_restore_location, self.subclient.content
            )
            self.log.info("Started Restore out of place with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + job.delay_reason
                )

            self.log.info("Successfully finished restore out of place")

            self._nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, windows_restore_location, self.subclient.content
            )
            self.log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
            filer_restore_location = str(self.tcinputs['FilerRestoreLocation'])

            job = self.subclient.restore_out_of_place(
                self._client.client_name,
                filer_restore_location,
                self.subclient.content)

            self.log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                )

            self.log.info("Successfully finished Restore out of place to Filer")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                self.subclient.content, filer_restore_location
            )

            # check if intellisnap is enabled at client level
            if not self.client.is_intelli_snap_enabled:
                self.log.info("Intelli Snap is not enabled for client, enabling it.")
                self.client.enable_intelli_snap()

            self.log.info("Intelli Snap for client is enabled.")

            # Check if intellisnap is enabled at subclient level
            if not self.subclient.is_intelli_snap_enabled:
                self.log.info("Intelli snap is not enabled at subclient level, enabling it.")
                self.subclient.enable_intelli_snap("NetApp")

            self.log.info("Intelli Snap for subclient is enabled.")

            job = self._nas_helper.run_backup(self.subclient, "FULL")

            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            self.log.info("*" * 10 + " Run out of place restore to windows client" + "*" * 10)

            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name, windows_restore_location, self.subclient.content
            )
            self.log.info("Started Restore out of place with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + job.delay_reason
                )

            self.log.info("Successfully finished restore out of place")
            self._nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, windows_restore_location, self.subclient.content
            )

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
