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

    6.  Restore Out of place to filer job

    7.  Restore in place job

    8.  Restore in place from copy job

    9.  Restore in place from differential job time frame

BasicAcceptance:
    __init__()              --  initializes basicacceptance object

    _get_copy_precedence()  --  returns the copy precedence value

    _run_backup()           --  starts the backup job

    run()                   --  runs the basic acceptance test case
"""

import random
import string

from NAS.NASUtils.basicacceptance import BasicAcceptance

class HuaweiBasicAcceptance(BasicAcceptance):
    """Helper class to run basic acceptance test case for Huawei client"""

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

        self._run_backup("FULL")
        for content in self._subclient.content:
            volume_path, _ = nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(nas_client, volume_path)

        self._run_backup("INCREMENTAL")
        for content in self._subclient.content:
            volume_path, _ = nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(nas_client, volume_path)

        job = self._run_backup("DIFFERENTIAL")
        diff_job_start_time = str(job.start_time)
        diff_job_end_time = str(job.end_time)
        # create a random string
        random_string = "".join([random.choice(string.ascii_letters) for _ in range(4)])

        storage_policy = self._commcell.storage_policies.get(self._subclient.storage_policy)
        storage_policy_copy = "SPCopy_" + random_string

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

        self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
        filer_restore_location = (str(self._inputs['FilerRestoreLocation']))
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

        self._nas_helper.validate_filer_to_filer_restored_content(
            nas_client, self._subclient.content, filer_restore_location
        )

        self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        job = self._subclient.restore_in_place(self._subclient.content)
        self._log.info("Started restore in place job with Job ID: %s", str(job.job_id))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished restore in place job")

        self._nas_helper.validate_filer_to_filer_restored_content(
            nas_client, self._subclient.content, filer_restore_location
        )

        self._log.info("*" * 10 + " Run in place restore from copy " + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, storage_policy_copy
        )

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

        self._nas_helper.validate_filer_to_filer_restored_content(
            nas_client, self._subclient.content, filer_restore_location
        )

        self._log.info("Deleting Secondary copy")
        storage_policy.delete_secondary_copy(storage_policy_copy)
        self._log.info("Successfully deleted secondary copy")

        self._log.info(("*" * 10 + " Run in place restore from differential jobtime frame " + "*" *
                        10))
        job = self._subclient.restore_in_place(
            self._subclient.content,
            from_time=diff_job_start_time,
            to_time=diff_job_end_time)

        self._log.info(
            "Started restore in place from differential jobtime frame job with Job ID:"
            "%d", job.job_id
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore from differential time frame with error: {0}".format(
                    job.delay_reason
                )
            )

        self._log.info("Successfully finished Restore in place in differential time frame")

        self._nas_helper.validate_filer_to_filer_restored_content(
            nas_client, self._subclient.content, filer_restore_location
        )