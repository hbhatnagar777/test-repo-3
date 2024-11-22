# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file that executes the  Intellisnap basic acceptance test cases for nas client

Intellisnap BasicAcceptance is the only class defined in this file

This class include below cases:
•	Full snap backup with skip catalog
•	Add data
•	Inc snap backup with skip catalog
•	Add data
•	Restore to filer and validate
•	Restore to windows and validate
•	Inplace restore and validate
•	Backup copy
•	Restore to filer from backupcopy and validate
•	Restore to windows from backupcopy and validate
•	Inplace restore from backupcopy and validate




BasicAcceptance:
     run()                   --  runs the basic acceptance test case
"""

import time
from base64 import b64encode
from AutomationUtils.options_selector import OptionsSelector
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance
from AutomationUtils.machine import Machine
from FileSystem.SNAPUtils.snaphelper import SNAPHelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants


class NutanixAcceptance(SnapBasicAcceptance):
    """Helper class to run Intellisnap basic acceptance test case for nas client"""

    def run(self):
        """Executes Intellisnap basic acceptance test case"""
        self._log.info(
            "Will run below test case on: %s subclient",
            format(str(self._inputs["SubclientName"])),
        )
        self._log.info("Number of data readers: " + str(self._subclient.data_readers))
        if self._subclient.data_readers != 3:
            self._log.info("Setting the data readers count to 3")
            self._subclient.data_readers = 3
        self._log.info("Get NAS Client object")
        self.nas_client = self._nas_helper.get_nas_client(
            self._client, self._agent, is_cluster=self._is_cluster
        )
        self._log.info("Make a CIFS Share connection")
        self.nas_client.connect_to_cifs_share(
            str(self._inputs["CIFSShareUser"]), str(self._inputs["CIFSSharePassword"])
        )
        self.impersonate_user = self._inputs["CIFSShareUser"]
        self.impersonate_password = b64encode(
            self._inputs["CIFSSharePassword"].encode()
        ).decode()
        self.proxy = self._inputs["ProxyClient"]
        filer_restore_location = str(self._inputs["FilerRestoreLocation"])
        self.sccontent = self._inputs["SubclientContent"].split(",")
        job = self._run_backup("FULL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("INCREMENTAL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("FULL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("INCREMENTAL")
        self.snapjob = job

        fs_options = {
            "impersonate_user": self.impersonate_user,
            "impersonate_password": self.impersonate_password,
        }
        self.sc_content_for_restore = []
        for x in range(len(self.sccontent)):
            self.sc_content_for_restore += [x]
            self.sc_content_for_restore[x] = (self.sccontent[x]).replace(
                "\\\\", "\\\\UNC-NT_"
            )
        self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
        job = self._subclient.restore_out_of_place(
            self.proxy,
            filer_restore_location,
            self.sc_content_for_restore,
            fs_options=fs_options,
        )
        self._log.info(
            f"Started Restore out of place to filer job with Job ID: {job.job_id}"
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info("Successfully finished Restore out of place to Filer")
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )
        # Restoe happense from snapshot (before baclup copy) so its live browse + add logs to say the same
        options_selector = OptionsSelector(self._commcell)
        (
            windows_restore_client,
            windows_restore_location,
        ) = options_selector.get_windows_restore_client()
        self._log.info(
            "*" * 10 + " Run out of place restore to Windows Client " + "*" * 10
        )
        job = self._subclient.restore_out_of_place(
            windows_restore_client.machine_name,
            windows_restore_location,
            self.sc_content_for_restore,
        )

        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: "
            + str(job.job_id)
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: "
                + str(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to windows client")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client,
            windows_restore_client,
            windows_restore_location,
            self._subclient.content,
        )

        self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        job = self._subclient.restore_in_place(
            self.sc_content_for_restore, fs_options=fs_options, proxy_client=self.proxy
        )
        self._log.info(
            "Started restore in place job with Job ID: %s", format(str(job.job_id))
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info("Successfully finished restore in place job")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client,
            windows_restore_client,
            windows_restore_location,
            self._subclient.content,
        )

        storage_policy_copy = "Primary"

        self._log.info("*" * 10 + "Running backup copy now" + "*" * 10)

        job = self._storage_policy.run_backup_copy()
        self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup copy job with error: " + str(job.delay_reason)
            )
        self._log.info(
            "Successfully finished backup copy workflow Job :%s", format(job.job_id)
        )

        if job.status != "Completed":
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, \
                    Reason: {1}".format(
                    job.job_id, job.delay_reason
                )
            )

        self._log.info(
            "*" * 10 + "Run out of place restore to Filer from backupcopy" + "*" * 10
        )
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, storage_policy_copy
        )
        job = self._subclient.restore_out_of_place(
            self.proxy,
            filer_restore_location,
            self.sc_content_for_restore,
            copy_precedence=int(copy_precedence),
            fs_options=fs_options,
        )
        self._log.info(
            f"Started Restore out of place to filer job with Job ID: {job.job_id}"
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info(
            "Successfully finished Restore out of place to Filer from backup copy"
        )
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )

        options_selector = OptionsSelector(self._commcell)
        (
            windows_restore_client,
            windows_restore_location,
        ) = options_selector.get_windows_restore_client()
        self._log.info(
            "*" * 10
            + "Run out of place restore to windows client from backupcopy"
            + "*" * 10
        )
        job = self._subclient.restore_out_of_place(
            windows_restore_client.machine_name,
            windows_restore_location,
            self.sc_content_for_restore,
            copy_precedence=int(copy_precedence),
        )

        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: "
            + str(job.job_id)
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: "
                + str(job.delay_reason)
            )
        self._log.info(
            "Successfully finished Restore out of place to windows client"
            "from Backupcopy"
        )
        self._nas_helper.validate_windows_restored_content(
            self.nas_client,
            windows_restore_client,
            windows_restore_location,
            self._subclient.content,
        )

        self._log.info("*" * 10 + " Run Restore in place from backup copy " + "*" * 10)
        job = self._subclient.restore_in_place(
            self.sc_content_for_restore,
            copy_precedence=int(copy_precedence),
            fs_options=fs_options,
            proxy_client=self.proxy,
        )
        self._log.info(
            "Started restore in place job with Job ID: %s", format(str(job.job_id))
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info("Successfully finished restore in place job")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client,
            windows_restore_client,
            windows_restore_location,
            self._subclient.content,
        )

        # Validating Snapshot content by comparing with subclient content
        job = self._run_backup("FULL")
        self._log.info("Running snap operations")
        self.mount_snap(job.job_id)
        query = f"SELECT MountPath FROM SMVolume WHERE JobId = {job.job_id}"
        self._csdb.execute(query)
        rest_loc = self._csdb.fetch_all_rows()[0]
        self._nas_helper.validate_filer_to_filer_restored_content(
            nas_client=self.nas_client,
            subclient_content=self._subclient.content[0],
            filer_restore_location=rest_loc,
            filter_content=[".snapshot"],
        )
