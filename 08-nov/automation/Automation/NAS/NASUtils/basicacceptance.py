# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file that executes the  basic acceptance test cases for nas client

BasicAcceptance is the only class defined in this file

This class include below cases:
    1.  FULL backup job

    2.  INCREMENTAL backup job after adding test data

    3.  DIFFERENTIAL backup job after adding test data

    4.  Storage Policy copy creation

    5.  Running Aux copy job

    6.  Restore out of place to Windows client

    7.  Restore out of place to Unix client

    8.  Restore in place job

    9.  Restore out of place to filer job

    10. Restore in place from copy job

    11. Restore in place in incremental job time frame

BasicAcceptance:
    __init__()              --  initializes basicacceptance object

    _get_copy_precedence()  --  returns the copy precedence value

    _run_backup()           --  starts the backup job

    run()                   --  runs the basic acceptance test case
"""


from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class BasicAcceptance(object):
    """Helper class to run basic acceptance test case for nas client"""

    def __init__(self, test_case_obj, is_cluster=False, is_vdm=False, **kwargs):
        """Initializes basicacceptance object

            Args:
                test_case_obj   (object)    --  test case class object

                is_cluster      (bool)      --  flag to determine if the specified client
                                                    is cluster / vserver / filer
				  is_vdm          (bool)      --  flag to determine if client is vdm

            kwargs:

                 c2c             (bool)      -- flag to run c2c steps
                
        """

        c2c = kwargs.get('c2c', False)
        self._inputs = test_case_obj.tcinputs
        self._commcell = test_case_obj.commcell
        self._log = logger.get_log()
        self._subclient = test_case_obj.subclient
        self._commserver_name = self._commcell.commserv_name
        self._csdb = test_case_obj.csdb
        self._nas_helper = NASHelper()
        self._client = test_case_obj.client
        self._is_cluster = is_cluster
        self._agent = test_case_obj.agent
        self.is_vdm = is_vdm
        self.is_c2c = c2c
        self.max_incs = hasattr(test_case_obj, "max_incs")
        self.get_vendor_id = "SELECT Id FROM SMVendor WHERE Name = '{a}'"
        self.get_controlhost_id = "SELECT RefId FROM SMHostAlias WHERE AliasName = '{a}'"
        self.dip_ip = self._inputs.get("dip_ip", None)

    def execute_query(self, query, my_options=None, fetch_rows=True):
        """ Executes SQL Queries
            Args:
                query           (str)   -- sql query to execute

                my_options      (dict)  -- options in the query
                default: None

                fetch_rows      (bool)   -- By default return all rows, if false return one row
            Return:
                    list : first column  or all rows of the sql output

        """
        if my_options is None:
            self._csdb.execute(query)
        elif isinstance(my_options, dict):
            self._csdb.execute(query.format(**my_options))

        if fetch_rows:
            return self._csdb.fetch_all_rows()
        return self._csdb.fetch_one_row()[0]			

    def _run_backup(self, backup_type):
        """Starts backup job"""
        self._log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self._subclient.backup(backup_type)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        return job

    def _get_copy_precedence(self, storage_policy, storage_policy_copy):
        """Returns the copy precedence value"""
        self._csdb.execute(
            "select copy from archGroupCopy where archGroupId in (select id from archGroup where \
            name = '{0}') and name = '{1}'".format(storage_policy, storage_policy_copy))
        cur = self._csdb.fetch_one_row()
        return cur[0]

    def run(self):
        """Executes basic acceptance test case"""
        self._log.info(
            "Will run below test case on: %s subclient", str(self._inputs['SubclientName'])
        )

        self._log.info("Number of data readers: " + str(self._subclient.data_readers))
        if self._subclient.data_readers != 3:
            self._log.info("Setting the data readers count to 3")
            self._subclient.data_readers = 3

        self._log.info("Get NAS Client object")
        nas_client = self._nas_helper.get_nas_client(self._client, self._agent,
                                                     is_cluster=self._is_cluster)

        self._log.info("Make a CIFS Share connection")
        nas_client.connect_to_cifs_share(
            str(self._inputs['CIFSShareUser']), str(self._inputs['CIFSSharePassword'])
        )

        job = self._run_backup("FULL")
        if self.dip_ip:
            self._log.info(f"IP address from inputs is {self.dip_ip}")
            MAClient = self._commcell.clients.get(self._subclient.storage_ma)
            MAMachine = Machine(MAClient)
            ip_used = self._nas_helper.get_data_connect_ip(job, MAMachine)
            if self.dip_ip in ip_used:
                self._log.info("DIP IP is used correctly")
            else:
                raise Exception(
                    "DIP IP is not used, hence failing TC "
                )

        for content in self._subclient.content:
            volume_path, _ = nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(nas_client, volume_path)

        if self.max_incs:
            self._nas_helper.run_max_incs(self._subclient)
        else:
            self._run_backup("INCREMENTAL")
        for content in self._subclient.content:
            volume_path, _ = nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(nas_client, volume_path)
            test_data_path = self._nas_helper.generate_and_copy_files(nas_client, volume_path)

        job = self._run_backup("DIFFERENTIAL")
        diff_job_start_time = str(job.start_time)
        diff_job_end_time = str(job.end_time)
        options_selector = OptionsSelector(self._commcell)

        storage_policy = self._commcell.storage_policies.get(self._subclient.storage_policy)

        if self.is_c2c:
            self._log.info("*" * 20 + "Running Snapshot catalog on the SP" + "*" * 20)
            job = storage_policy.run_snapshot_cataloging()
            self._log.info("Started catalog job with Job ID: %s", str(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run {0} snapshot catalog job with error: {1}".format(
                        job.job_id, job.delay_reason
                    )
                )
            self._log.info("*" * 20 + "Successfully completed Snapshot catalog" + "*" * 20)

            storage_policy_copy = options_selector.get_custom_str(presubstr="C2C_Target_")
            is_mirror_copy = False
            is_snap_copy = True
            library_name = str(self._inputs['AuxCopyLibrary'])
            media_agent_name = self._inputs['AuxCopyMediaAgent']
            source_copy = "Primary Snap"
            self._log.info("*" * 20 + "Creating Copies for PV_Replica_C2C Configuration" + "*" * 20)
            storage_policy.create_snap_copy(
                storage_policy_copy, is_mirror_copy, is_snap_copy, library_name,
                media_agent_name, source_copy, is_replica_copy=True, is_c2c_target=True)
            self._log.info("Successfully created Cloud Target Replica copy")
            self._log.info("*" * 20 + "Adding Cloud Target Mappings" + "*" * 20)
            spcopy = storage_policy.get_copy(storage_policy_copy)
            self._log.info("Adding SVM association")
            target_vendor = self._inputs.get('C2CTargetVendorName', None)
            tgt_vendor_id = self.execute_query(self.get_vendor_id,
                                        {'a': target_vendor}, fetch_rows=False)
            source_array = self._inputs['ArrayName']
            target_array = self._inputs['ArrayName2']
            src_array_id = self.execute_query(self.get_controlhost_id,
                                              {'a': source_array}, fetch_rows=False)
            tgt_array_id = self.execute_query(self.get_controlhost_id,
                                              {'a': target_array}, fetch_rows=False)
            kwargs = {
                'target_vendor' : target_vendor,
                'tgt_vendor_id' : tgt_vendor_id
                }
            spcopy.add_svm_association(src_array_id, source_array, tgt_array_id, target_array,
                                       **kwargs)
            self._log.info("Successfully added SVM association to copy : {0}".format(storage_policy_copy))
        else:
            storage_policy_copy = options_selector.get_custom_str(presubstr="SPCopy_")
            self._log.info(
                "Creating Storage Policy Copy %s ", storage_policy_copy
            )
            storage_policy.create_secondary_copy(
                storage_policy_copy, str(self._inputs['AuxCopyLibrary']),
                str(self._inputs['AuxCopyMediaAgent'])
            )
            self._log.info("Successfully created secondary copy")

        self._log.info("*" * 10 + " Run Aux Copy job " + "*" * 10)
        job = storage_policy.run_aux_copy(
            storage_policy_copy, str(self._inputs['AuxCopyMediaAgent'])
        )
        self._log.info("Started Aux Copy job with Job ID: " + str(job.job_id))

        if not job.wait_for_completion():
            raise Exception("Failed to run aux copy job with error: " + str(job.delay_reason))

        self._log.info("Successfully finished Aux Copy Job") 

        
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, storage_policy_copy
        )

        if not self.is_c2c:

            size = nas_client.get_content_size(self._subclient.content)

            if self._inputs.get("WindowsDestination"):
                windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
                try:
                    drive = options_selector.get_drive(windows_client, size)
                except OSError:
                    self._log.info("No drive found")
                dir_path = drive + options_selector._get_restore_dir_name()
                windows_client.create_directory(dir_path)

                self._log.info(
                    "Windows Restore Client obtained: %s", windows_client.machine_name
                )
                self._log.info("Windows Restore location: %s", dir_path)
                windows_restore_client = windows_client
                windows_restore_location = dir_path

            else:
                windows_restore_client, windows_restore_location = \
                    options_selector.get_windows_restore_client(size=size)

            self._log.info("*" * 10 + " Run out of place restore to Windows Client " + "*" * 10)

            job = self._subclient.restore_out_of_place(
                windows_restore_client.machine_name, windows_restore_location, self._subclient.content
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
                nas_client, windows_restore_client, windows_restore_location, self._subclient.content
            )

            self._log.info("*" * 10 + " Run out of place restore to Linux Client" + "*" * 10)

            if self._inputs.get("LinuxDestination"):
                linux_client = Machine(self._inputs["LinuxDestination"], self._commcell)

                try:
                    mount_path = options_selector.get_drive(linux_client, size)
                except OSError:
                    self._log.info("No drive found")

                dir_path = mount_path + options_selector._get_restore_dir_name()
                linux_client.create_directory(dir_path)

                self._log.info(
                    "Linux Restore Client obtained: %s", linux_client.machine_name
                )
                self._log.info("Linux Restore location: %s", dir_path)
                linux_restore_client = linux_client
                linux_restore_location = dir_path

            else:
                linux_restore_client, linux_restore_location = \
                    options_selector.get_linux_restore_client(size=size)

            job = self._subclient.restore_out_of_place(
                linux_restore_client.machine_name, linux_restore_location, self._subclient.content
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
                    "Restore validation failed. List of different files \n%s", str(out)
                )
                raise Exception(
                    "Restore validation failed. Please check logs for more details."
                )

            self._log.info("Successfully validated restored content")

            self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            job = self._subclient.restore_in_place(self._subclient.content)
            self._log.info("Started restore in place job with Job ID: %s", str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: {0}".format(job.delay_reason)
                )

            self._log.info("Successfully finished restore in place job")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location, self._subclient.content
            )

            self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
            filer_restore_location = str(self._inputs['FilerRestoreLocation'])

            job = self._subclient.restore_out_of_place(
                self._client.client_name,
                filer_restore_location,
                self._subclient.content)

            self._log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                )

            self._log.info("Successfully finished Restore out of place to Filer")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                self._subclient.content, filer_restore_location
            )

            self._log.info("*" * 10 + " Run in place restore to filer from secondary copy " + "*" * 10)

            job = self._subclient.restore_in_place(
                self._subclient.content, copy_precedence=int(copy_precedence)
            )

            self._log.info(
                "Started restore in place from copy job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore from copy with error: {0}".format(str(job.delay_reason))
                )

            self._log.info("Successfully finished Restore in place from copy")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location, self._subclient.content
            )

            self._log.info("*" * 10 + " Run in place restore from differential jobtime frame " + "*" *\
                           10)
            job = self._subclient.restore_in_place(
                self._subclient.content,
                from_time=diff_job_start_time,
                to_time=diff_job_end_time)

            self._log.info(
                "Started restore in place from differential jobtime frame job with Job ID: %d",\
                    job.job_id
                )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore from differential time frame with error: {0}".format(
                        job.delay_reason
                    )
                )

            self._log.info("Successfully finished Restore in place in differential time frame")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location, self._subclient.content
            )

        if self.is_c2c:
            file_path1 = f"{self._inputs['SubclientContent']}/{test_data_path}/textfile1.txt"
            file_path2 = f"{self._inputs['SubclientContent']}/{test_data_path}/textfile2.txt"
            paths = [file_path1, file_path2]

            self._log.info("*" * 10 + " Run out of place restore to different SVM from Cloud copy" + "*" * 10)
            filer_restore_location = str(self._inputs['FilerRestoreLocation'])

            job = self._subclient.restore_out_of_place(
                self._client.client_name,
                filer_restore_location,
                paths,
                copy_precedence=int(copy_precedence))

            self._log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                )

            self._log.info("Successfully finished Restore out of place to Filer")
            path = [f"{self._inputs['SubclientContent']}/{test_data_path}"]

            self._nas_helper.validate_filer_to_filer_restored_content(
                nas_client, path, filer_restore_location, verify_files=True
            )

            self._log.info("*" * 10 + " Run out of place restore to Same SVM from Cloud copy" + "*" * 10)
            filer_restore_location = str(self._inputs['FilerRestoreLocation1'])

            job = self._subclient.restore_out_of_place(
                self._client.client_name,
                filer_restore_location,
                paths,
                copy_precedence=int(copy_precedence))

            self._log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                )

            self._log.info("Successfully finished Restore out of place to Same SVM from Cloud copy")
            path = [f"{self._inputs['SubclientContent']}/{test_data_path}"]

            self._nas_helper.validate_filer_to_filer_restored_content(
                nas_client, path, filer_restore_location, verify_files=True
            )

            self._log.info("*" * 10 + " Run in place restore to filer from Cloud copy " + "*" * 10)

            job = self._subclient.restore_in_place(paths, copy_precedence=int(copy_precedence))

            self._log.info(
                "Started restore in place from copy job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore from copy with error: {0}".format(str(job.delay_reason))
                )

            self._log.info("Successfully finished Restore in place from Cloud copy")

            self._nas_helper.validate_filer_to_filer_restored_content(
                nas_client, path, filer_restore_location, verify_files=True
            )

        self._log.info("Deleting Secondary copy")
        storage_policy.delete_secondary_copy(storage_policy_copy)
        self._log.info("Successfully deleted secondary copy")
        self._nas_helper.delete_nre_destinations(windows_restore_client, windows_restore_location)
        self._nas_helper.delete_nre_destinations(linux_restore_client, linux_restore_location)
