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
•	Diff snap backup with skip catalog
•	Restore to filer and validate
•	Restore to windows and validate
•	Inplace restore and validate
•	Backup copy
•	Restore to filer from backupcopy and validate
•	Restore to windows from backupcopy and validate
•	Inplace restore from backupcopy and validate
•	Deferred cataloging on Storage policy
•	Restore to filer from catalog and validate
•   Mount snap & validate
•   Unmount snap & validate
•   Revert snap & validate
•	Delete snap & validate

Steps for Replication Template:
    
1. Create replica copy.
2. Run Full, Incremental and Differential Snap Backup.
3. Run Aux Copy.
4. Mount snap from Replica and validation.
5. UnMount snap from Replica and validation.
6. Run out of place restore to Filer from Replica snap
7. Run out of place restore to Windows Client from Replica Copy.
8. Update Replica copy as source for backup copy and snapshot catalog.
9. Run backup copy.
10. Run out of place restore to Filer from backupcopy
11. Run out of place restore to Windows Client from backupcopy.
12.  Run Restore in place from backup copy.
13. Run deferred cataloging on the storage policy.
14. Run out of place restore to Filer from deferred catalog.
15. Delete snap from Replica and validation.
16. Delete Replica Copy.

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


class CIFSSnapBasicAcceptance(SnapBasicAcceptance):
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
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("FULL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("INCREMENTAL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("DIFFERENTIAL")
        self.snapjob = job
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
            self.nas_client, windows_restore_client, windows_restore_location, \
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
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )
        storage_policy_copy = "Primary"

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
            self._subclient.storage_policy, storage_policy_copy
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
            self.nas_client, windows_restore_client, windows_restore_location, \
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
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run deferred cataloging on the storage policy  " + "*" * 10)
        self.snapshot_cataloging()

        self._log.info("*" * 10 + "Run out of place restore to Filer from deferred catalog" + "*" * 10)
        storage_policy_copy = "Primary Snap"
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, storage_policy_copy
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
        mounthost = self._inputs.get('mounthost', None)
        mounthostobj = Machine(mounthost, self._commcell)
        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)
        self.mount_snap(job.job_id, snap_copy_name, destclient=mounthost)
        self.mount_validation(job.job_id, snap_copy_name, destclient=mounthostobj)
        self.unmount_snap(job.job_id, snap_copy_name)
        self.unmount_validation(job.job_id, snap_copy_name)

        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        time.sleep(30)
        self.revert_snap(job.job_id, snap_copy_name)
        self.revert_validation(job.job_id, snap_copy_name, destclient=mounthostobj)
        time.sleep(30)
        self.delete_snap(self.snapjob.job_id, snap_copy_name)
        self.delete_validation(self.snapjob.job_id, snap_copy_name)
        self.cleanup()
        self._nas_helper.delete_nre_destinations(windows_restore_client, windows_restore_location)

    def replication_template(self, replica_type):
        """Executes Intellisnap basic acceptance test for Replication"""
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

        self.delete_replica_copy()
        replica_copy = self.create_replica_copy(replica_type)

        self.sccontent = self._inputs['SubclientContent'].split(",")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        full_job = self._run_backup("FULL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        inc_job = self._run_backup("INCREMENTAL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        diff_job = self._run_backup("DIFFERENTIAL")
        time.sleep(30)

        self.run_aux_copy()
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, replica_copy
        )

        self.mount_snap(full_job.job_id, replica_copy, destclient=self.mounthost)
        self.mount_validation(full_job.job_id, replica_copy, destclient=self.mounthostobj)
        self.unmount_snap(full_job.job_id, replica_copy)
        self.unmount_validation(full_job.job_id, replica_copy)

        fs_options = {'impersonate_user' : self.impersonate_user,\
		               'impersonate_password' : self.impersonate_password}
        self.sc_content_for_restore = []
        for x in range(len(self.sccontent)):
            self.sc_content_for_restore += [x]
            self.sc_content_for_restore[x] = ((self.sccontent[x]).replace("\\\\", "\\\\UNC-NT_"))
        self._log.info("*" * 10 + " Run out of place restore to Filer from Replica snap" + "*" * 10)
        job = self._subclient.restore_out_of_place(
            self.proxy,
            filer_restore_location,
            self.sc_content_for_restore,
            copy_precedence=int(copy_precedence),
            fs_options=fs_options)
        self._log.info(
            "Started Restore out of place to filer job with Job ID: %s", job.job_id
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
        windows_restore_client, windows_restore_location = \
            options_selector.get_windows_restore_client()
        self._log.info("*" * 10 + " Run out of place restore to Windows Client from Replica Copy " + "*" * 10)
        job = self._subclient.restore_out_of_place(windows_restore_client.machine_name,
                                                   windows_restore_location,
                                                   self.sc_content_for_restore,
                                                   restore_data_and_acl=False,
                                                   copy_precedence=int(copy_precedence))

        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: %s", job.job_id
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

        self._log.info("*" * 10 + "Updating replica copy as source for backup copy & snapshot catalog" + "*" * 10)
        options = {
            'enable_backup_copy': True,
            'source_copy_for_snap_to_tape': replica_copy,
            'enable_snapshot_catalog': True,
            'source_copy_for_snapshot_catalog': replica_copy,
            'is_ocum': None,
            'disassociate_sc_from_backup_copy': None
        }
        self._storage_policy.update_snapshot_options(**options)

        self._log.info("*" * 10 + "Running backup copy from Replica Copy" + "*" * 10)
        self.run_backup_copy()

        self._log.info("*" * 10 + "Run out of place restore to Filer from backupcopy" + "*" * 10)
        backup_copy_name = self.execute_query(self.get_backup_copy, self._storage_policy.storage_policy_id)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )
        job = self._subclient.restore_out_of_place(self.proxy,
                                                   filer_restore_location,
                                                   self.sc_content_for_restore,
                                                   copy_precedence=int(copy_precedence),
                                                   fs_options=fs_options)
        self._log.info(
            "Started Restore out of place to filer job with Job ID: %s", job.job_id
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
                                                   restore_data_and_acl=False,
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
            self.nas_client, windows_restore_client, windows_restore_location, \
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
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run deferred cataloging using Replica snap " + "*" * 10)
        self.snapshot_cataloging()

        self._log.info("*" * 10 + "Run out of place restore to Filer from deferred catalog" + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, replica_copy
        )
        job = self._subclient.restore_out_of_place(self.proxy,
                                                   filer_restore_location,
                                                   self.sc_content_for_restore,
                                                   copy_precedence=int(copy_precedence),
                                                   fs_options=fs_options)
        self._log.info(
            "Started Restore out of place to filer job with Job ID: %s", job.job_id
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )
        self._log.info("Successfully finished Restore out of place to Filer from catalog")
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )

        self.delete_snap(full_job.job_id, replica_copy)
        self.delete_snap(inc_job.job_id, replica_copy)
        self.delete_snap(diff_job.job_id, replica_copy)
        self.delete_validation(diff_job.job_id, replica_copy)
        self.delete_replica_copy(replica_copy)

    def runext1(self):
        """Executes Intellisnap Extent Base Feature Test case for NAS Client"""
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
        self.sccontent = self._inputs['SubclientContent'].split(",")
        self.client_machine = Machine(self._commserver_name, self._commcell)
        self._snaphelper = SNAPHelper
        self._snapconstants = SNAPConstants
        fsa = "FileSystemAgent"
        enable = "bEnableFileExtentBackup"
        slab = "mszFileExtentSlabs"
        slab_val = str(self._inputs.get("Slab", "10-1024=5"))
        self._log.info("01 : Enable feature by setting {} under {} on client."
                       .format(enable, fsa))
        self.client_machine.create_registry(fsa, enable, 1, 1)
        self._log.info(
            "02 : Lowering threshold by setting {} under {} on client.".format(
                slab, fsa))
        self.client_machine.create_registry(fsa, slab, slab_val, 1)
        job = self._run_backup("FULL")
        for x in range(len(self.sccontent)):
            self._nas_helper.copy_test_data(self.nas_client, self.sccontent[x])
        job = self._run_backup("INCREMENTAL")
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
        self._get_scid1 = "select jobResultDir from APP_client where name like '{a}' "
        self._csdb.execute(self._get_scid1)
        output1 = self._snapconstants.execute_query(self, self._get_scid1,
                                                    {'a': self.proxy})
        newout = output1[0]
        SCID = self._subclient.subclient_id
        SPPath1 = newout[0] + '\\CV_JobResults\\iDataAgent\\FileSystemAgent\\2'  +  '\\'+ SCID  + '\\SubClientProperties.cvf'
        result = self.client_machine.read_file(SPPath1).find("fileAsExtentsBackupEnabled=\"1\"")
        if result != -1:
            self._log.info("File extent is enabled on the client")
            self._log.info("Snap backup validation passed")
        else:
            self._log.info("Snap backup validation failed")
        remove_msg = "Removing registry entries {} and {} under {}".format(enable, slab, fsa)
        self._log.info(remove_msg)
        self.client_machine.remove_registry(fsa, enable)
        self.client_machine.remove_registry(fsa, slab)
        self._log.info(
            "Snap Backup and backup copy with Extent Base Feature Test case for NAS completed Successfully")
