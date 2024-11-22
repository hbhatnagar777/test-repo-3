# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file that executes the  Intellisnap basic acceptance test cases for nas client

Intellisnap BasicAcceptance is the only class defined in this file

This class include below cases:
•   Full snap backup with skip catalog
•   Add data
•   Inc snap backup with skip catalog
•   Add data
•   Diff snap backup with skip catalog
•   Restore to filer and validate
•   Restore to windows and validate
•   Inplace restore and validate
•   Backup copy
•   Restore to filer from backupcopy and validate
•   Restore to windows from backupcopy and validate
•   Inplace restore from backupcopy and validate
•   Deferred cataloging on Storage policy
•   Restore to filer from catalog and validate
•   Mount snap & validate
•   Unmount snap & validate
•   Revert snap & validate
•   Delete snap & validate


BasicAcceptance:
     run()                   --  runs the basic acceptance test case
"""
import time
from base64 import b64encode
from AutomationUtils.options_selector import OptionsSelector
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance
from AutomationUtils.machine import Machine



class HNASCIFSSnapBasicAcceptance(SnapBasicAcceptance):
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
        self.impersonate_user = self._inputs['CIFSShareUser']
        self.impersonate_password = b64encode(self._inputs['CIFSSharePassword'].encode()).decode()
        self.proxy = self._inputs['ProxyClient']
        filer_restore_location = (str(self._inputs['FilerRestoreLocation']))
        self.sccontent = self._inputs['SubclientContent'].split(",")

        job = self._run_backup("FULL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("INCREMENTAL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("DIFFERENTIAL")

        fs_options = {'impersonate_user' : self.impersonate_user,\
                      'impersonate_password' : self.impersonate_password}
        self.sc_content_for_restore = []
        for x in range(len(self.sccontent)):
            self.sc_content_for_restore += [x]
            self.sc_content_for_restore[x] = ((self.sccontent[x]).replace("\\\\", "\\\\UNC-NT_"))
        self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
        job = self._subclient.restore_out_of_place(
            self.proxy,
            filer_restore_location,
            self.sc_content_for_restore,
            fs_options=fs_options)
        self._log.info(
            "Started Restore out of place to filer job with Job ID: %d", job.job_id
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to Filer")
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )

        options_selector = OptionsSelector(self._commcell)
        if self._inputs.get("WindowsDestination"):
            windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
            windows_restore_client, windows_restore_location = self._nas_helper.restore_to_selected_machine(
                options_selector, windows_client=windows_client
            )
        else:
            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client()
        self._log.info("*" * 10 + " Run out of place restore to Windows Client " + "*" * 10)
        job = self._subclient.restore_out_of_place(windows_restore_client.machine_name,
                                                   windows_restore_location,
                                                   self.sc_content_for_restore)

        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: " + str(job.job_id)
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to windows client")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,\
            self._subclient.content
        )

        self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        job = self._subclient.restore_in_place(self.sc_content_for_restore,
                                               fs_options=fs_options,
                                               proxy_client=self.proxy)
        self._log.info("Started restore in place job with Job ID: %s", format(str(job.job_id)))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(job.delay_reason)
            )
        self._log.info("Successfully finished restore in place job")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,\
            self._subclient.content
        )
        backup_copy_name = self.execute_query(self.get_backup_copy, self._storage_policy.storage_policy_id)

        self._log.info("*" * 10 + "Running backup copy now" + "*" * 10)

        job = self._storage_policy.run_backup_copy()
        self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup copy job with error: " + str(job.delay_reason)
            )
        self._log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))

        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, \
                    Reason: {1}".format(job.job_id, job.delay_reason)
            )

        self._log.info("*" * 10 + "Run out of place restore to Filer from backupcopy" + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )
        job = self._subclient.restore_out_of_place(self.proxy,
                                                   filer_restore_location,
                                                   self.sc_content_for_restore,
                                                   copy_precedence=int(copy_precedence),
                                                   fs_options=fs_options)
        self._log.info(
            "Started Restore out of place to filer job with Job ID: %d", job.job_id
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to Filer from backup copy")
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )

        options_selector = OptionsSelector(self._commcell)
        windows_restore_client, windows_restore_location = \
            options_selector.get_windows_restore_client()
        self._log.info("*" * 10 + "Run out of place restore to windows client from backupcopy"
                       + "*" * 10)
        job = self._subclient.restore_out_of_place(windows_restore_client.machine_name,
                                                   windows_restore_location,
                                                   self.sc_content_for_restore,
                                                   copy_precedence=int(copy_precedence))

        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: " + str(job.job_id)
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to windows client"\
                       "from Backupcopy")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,\
            self._subclient.content
        )

        self._log.info("*" * 10 + " Run Restore in place from backup copy " + "*" * 10)
        job = self._subclient.restore_in_place(self.sc_content_for_restore,
                                               copy_precedence=int(copy_precedence),
                                               fs_options=fs_options,
                                               proxy_client=self.proxy)
        self._log.info("Started restore in place job with Job ID: %s", format(str(job.job_id)))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(job.delay_reason)
            )
        self._log.info("Successfully finished restore in place job")
        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,\
            self._subclient.content
        )

        self._log.info("*" * 10 + " Run deferred cataloging on the storage policy  " + "*" * 10)
        self.snapshot_cataloging()

        self._log.info("*" * 10 + "Run out of place restore to Filer from deferred catalog" +
                       "*" * 10)
        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, snap_copy_name
        )
        job = self._subclient.restore_out_of_place(self.proxy,
                                                   filer_restore_location,
                                                   self.sc_content_for_restore,
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

        self._log.info("Running snap operations")
        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)
        self.mount_snap(job.job_id, snap_copy_name, destclient=self.mounthost)
        self.mount_validation(job.job_id, snap_copy_name, destclient=self.mounthostobj)
        self.unmount_snap(job.job_id, snap_copy_name)
        self.unmount_validation(job.job_id, snap_copy_name)

        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        time.sleep(30)
        self.revert_snap(job.job_id, snap_copy_name)
        self.revert_validation(job.job_id, snap_copy_name)
        time.sleep(60)
        self.delete_snap(job.job_id, snap_copy_name)
        self.delete_validation(job.job_id, snap_copy_name)
        self.cleanup()
        self._nas_helper.delete_nre_destinations(windows_restore_client, windows_restore_location)

    def snapop_validation(self, jobid, mount=False, revert=False, delete=False, unmount=False):
        """ Common Method for Snap Operation Validations
            Args:
                jobid : snap backup jobid
        """

        self._log.info("validating snap operation")
        if mount or revert:
            self.mountpath_val = str(self.execute_query(self.get_mount_path, jobid))
            self.compare(
                self.client_machine, self.client_machine, self.mountpath_val, str(self._inputs['SubclientContent']))
            self._log.info("comparing files/folders was successful")

        elif delete:
            self._log.info("Checking if the snapshot of JobId: %s exists in the DB", format(jobid))
            self._log.info(
                "smvolumeid from DB is: %s", format(self.execute_query_all_rows(self.get_volume_id, jobid)))
            if format(self.execute_query_all_rows(self.get_volume_id, jobid)) == format([['']]):
                self._log.info("Snapshot is successfully deleted")
            else:
                raise Exception(
                    "Snapshot of jobid: {0} is not deleted yet, please check the CVMA logs".format(
                        jobid)
                )
            self._log.info("Successfully verified Snapshot cleanup")

        else:
            self.mountpath_val = str(self.execute_query(self.get_mount_path, jobid))
            if self.client_machine.check_directory_exists(self.mountpath_val):
                raise Exception("MountPath folder still exists under {0}".format(
                    self.mountpath_val))
            else:
                self._log.info("MountPath folder does not exists ")
