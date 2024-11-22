# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file that executes the  Intellisnap basic acceptance test cases for nas client

Intellisnap BasicAcceptance is the only class defined in this file

This class include below cases:
    1.  FULL backup job

    2.  INCREMENTAL backup job after adding test data

    3.  DIFFERENTIAL backup job after adding test data

    4.  Restore out of place to Windows client

    5.  Restore out of place to Unix client

    6.  Restore in place job

    7.  Restore out of place to filer job

    8.  Running backup copy job

    9. Restore in place from backup copy job

    10. Restore in place in incremental job time frame

BasicAcceptance:
    __init__()              --  initializes basicacceptance object

    _get_copy_precedence()  --  returns the copy precedence value

    _run_backup()           --  starts the backup job

    run()                   --  runs the basic acceptance test case
"""


import time

from NAS.NASUtils.nasclient import NetAPPClient, HNASClient
from AutomationUtils.options_selector import OptionsSelector
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance
from AutomationUtils.machine import Machine


class HNASSnapBasicAcceptance(SnapBasicAcceptance):
    """Helper class to run Intellisnap basic acceptance test case for nas client"""

    def run(self):
        """Executes Intellisnap basic acceptance test case"""
        self._log.info(
            "Will run below test case on: %s subclient", format(str(self._inputs['SubclientName']))
        )

        self._log.info("Number of data readers: " + str(self._subclient.data_readers))
        if self._subclient.data_readers != 3:
            self._log.info("Setting the data readers count to 3")
            self._subclient.data_readers = 3

        self._log.info("Get NAS Client object")
        self.nas_client = self._nas_helper.get_nas_client(self._client, self._agent,
                                                          is_cluster=self._is_cluster)

        self._log.info("Make a CIFS Share connection")
        self.nas_client.connect_to_cifs_share(
            str(self._inputs['CIFSShareUser']), str(self._inputs['CIFSSharePassword'])
        )

        job = self._run_backup("FULL")
        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)

        job = self._run_backup("INCREMENTAL")

        inc_job_start_time = str(job.start_time)
        inc_job_end_time = str(job.end_time)
        mounthost = self._inputs.get('mounthost', None)
        mounthostobj = Machine(mounthost, self._commcell)
        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)

        self.mount_snap(job.job_id, snap_copy_name, destclient=mounthost)
        self.mount_validation(job.job_id, snap_copy_name, destclient=mounthostobj)
        self.unmount_snap(job.job_id, snap_copy_name)
        self.unmount_validation(job.job_id, snap_copy_name)

        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)

        job = self._run_backup("DIFFERENTIAL")

        options_selector = OptionsSelector(self._commcell)

        size = self.nas_client.get_content_size(self._subclient.content)
        if self._inputs.get("WindowsDestination"):
            windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
            windows_restore_client, windows_restore_location = self._nas_helper.restore_to_selected_machine(
                options_selector, windows_client=windows_client, size=size
            )
        else:
            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

        if self._inputs.get('liveBrowse'):
            if self._inputs['liveBrowse'].upper() == 'TRUE':
                fs_options = {'live_browse': True}

        self._log.info("*" * 10 + " Run out of place restore to Windows Client " + "*" * 10)

        job = self._subclient.restore_out_of_place(
            windows_restore_client.machine_name, windows_restore_location, self._subclient.content, fs_options=fs_options
        )
        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: " + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to windows client")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run out of place restore to Linux Client" + "*" * 10)
        if self._inputs.get("LinuxDestination"):
            linux_client = Machine(self._inputs["LinuxDestination"], self._commcell)
            linux_restore_client, linux_restore_location = self._nas_helper.restore_to_selected_machine(
                options_selector, linux_client=linux_client, size=size
            )
        else:
            linux_restore_client, linux_restore_location = \
                options_selector.get_linux_restore_client(size=size)

        job = self._subclient.restore_out_of_place(
            linux_restore_client.machine_name, linux_restore_location, self._subclient.content, fs_options=fs_options
        )
        self._log.info(
            "Started restore out of place to linux client job with Job ID: " + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to linux client")

        out = []
        out = windows_restore_client.compare_folders(
            linux_restore_client, windows_restore_location,
            linux_restore_location, ignore_files=self._nas_helper.ignore_files_list)
        if out != []:
            self._log.error(
                "Restore validation failed. List of different files \n%s", format(str(out))
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self._log.info("Successfully validated restored content")


        self._log.info("*" * 10 + " Run in place restore in incremental jobtime frame " + "*" * 10)
        job = self._subclient.restore_in_place(
            self._subclient.content,
            from_time=inc_job_start_time,
            to_time=inc_job_end_time, fs_options=fs_options)

        self._log.info(
            "Started restore in place in incremental jobtime frame job with Job ID: %s", format(
                job.job_id
            )
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in incremental time frame with error: {0}".format(
                    job.delay_reason
                )
            )

        self._log.info("Successfully finished Restore in place in incremental time frame")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)

        job = self._subclient.restore_in_place(self._subclient.content, fs_options=fs_options)
        self._log.info("Started restore in place job with Job ID: %s", format(str(job.job_id)))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished restore in place job")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
        filer_restore_location = str(self._inputs['FilerRestoreLocation'])

        job = self._subclient.restore_out_of_place(
            self._client.client_name,
            filer_restore_location,
            self._subclient.content, fs_options=fs_options)

        self._log.info(
            "Started Restore out of place to filer job with Job ID: %s}", format(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to Filer")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,
            self._subclient.content, filer_restore_location
        )

        backup_copy_name = self.execute_query(self.get_backup_copy, self._storage_policy.storage_policy_id)

        self._log.info("*" * 10 + "Running backup copy now" + "*" * 10)

        job = self._storage_policy.run_backup_copy()
        self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )
        self._log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))

        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, \
                    Reason: {1}".format(job.job_id, job.delay_reason)
            )

        self._log.info("*" * 10 + " Run in place restore from backup copy " + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )
        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self.nas_client.remove_folder(volume_path)

        job = self._subclient.restore_in_place(
            self._subclient.content, copy_precedence=int(copy_precedence)
        )

        self._log.info(
            "Started restore in place from backup copy job with Job ID: %s", format(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to restore from backup copy with error: {0}".format(str(job.delay_reason))
            )

        self._log.info("Successfully finished Restore in place from backup copy")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run deferred cataloging on the storage policy  " + "*" * 10)
        self.snapshot_cataloging()

        self._log.info("*" * 10 + "Run out of place restore to Filer from deferred catalog" +
                       "*" * 10)

        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, snap_copy_name
        )
        job = self._subclient.restore_out_of_place(self._client.client_name,
                                                   filer_restore_location,
                                                   self._subclient.content,
                                                   copy_precedence=int(copy_precedence),
                                                   fs_options=fs_options)
        self._log.info(
            "Started Restore out of place to filer job with Job ID: %d", job.job_id
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to Filer from catalog")
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )
        job = self._run_backup("FULL")

        if isinstance(self.nas_client, NetAPPClient) or isinstance(self.nas_client, HNASClient):
            volume_path, _ = self.nas_client.get_path_from_content(self._subclient.content[0])
            self._nas_helper.copy_test_data(self.nas_client, volume_path)
            self.revert_snap(job.job_id, snap_copy_name)
            self.revert_validation(job.job_id, snap_copy_name)
        time.sleep(60)
        self.delete_snap(job.job_id, snap_copy_name)
        self.delete_validation(job.job_id, snap_copy_name)

        self.cleanup()
        self._nas_helper.delete_nre_destinations(windows_restore_client, windows_restore_location)
        self._nas_helper.delete_nre_destinations(linux_restore_client, linux_restore_location)
