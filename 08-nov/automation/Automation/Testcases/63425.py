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

    run()               --  run function of this test case
"""

import time

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from cvpysdk.job import Job

class TestCase(CVTestCase):
    """Class for executing Restartable backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Isilon -Backupcopy- NDMP Single Path Multi-stream restartability (some paths are restarted)"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self._nas_helper = NASHelper()
        self.tcinputs = {
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            # check the data readers count
            self.log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self.log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                self.log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            self.log.info("Get Nas client object")
            options_selector = OptionsSelector(self.commcell)

            nas_client = self._nas_helper.get_nas_client(self.client, self.agent)

            self.log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            # run full backup
            self.log.info("*" * 10 + " Starting Subclient FULL Backup " + "*" * 10)
            job = self.subclient.backup("FULL")
            self.log.info("Started FULL backup with Job ID: " + str(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run full snap backup job with error: {0}".format(job.delay_reason))
            storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
            storage_policy_copy = "Primary"
            self.log.info("*" * 10 + "Running backup copy now" + "*" * 10)
            storage_policy.run_backup_copy()
            time.sleep(10)
            job = self._nas_helper.get_bkpcpyjob_from_snapjob(job)
            self.log.info(job[0])
            job = Job(self._commcell, int(job[0]))
            self.log.info(job)
            # Run restartable backup case
            self._nas_helper.run_restartable_backup(job)
            self.log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
            filer_restore_location = str(self.tcinputs['FilerRestoreLocation'])

            job = self._subclient.restore_out_of_place(
                self._client.client_name,
                filer_restore_location,
                self._subclient.content)

            self.log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
                )

            self.log.info("Successfully finished Restore out of place to Filer")

            self._nas_helper.validate_filer_to_filer_restored_content(
                nas_client, self._subclient.content, filer_restore_location
            )

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
