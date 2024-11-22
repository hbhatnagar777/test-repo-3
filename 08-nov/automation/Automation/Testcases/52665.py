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

    _run_backup()       --  Run backup type function
"""

import random
import string

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class to verify NAS NDMP Deduplication for Huawei"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to verify NAS NDMP Deduplication for Huawei"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.nas_helper = NASHelper()
        self.tcinputs = {
            "ClientName": None,
            "SubclientName": None,
            "BackupsetName": None,
            "AgentName": None,
            "SubclientContent": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def _run_backup(self, backup_type):
        """Starts backup job"""
        job = self._subclient.backup(backup_type)
        self.log.info(f"Started {backup_type} backup with Job ID: {job.job_id}")
        if not job.wait_for_completion():
            raise Exception(
                f"Failed to run {backup_type} backup job with error: {job.delay_reason}"
            )
        return job

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info(f"Started executing {self.id} testcase")

            # check the data readers count
            self.log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self.log.info(f"Number of data readers:{self.subclient.data_readers}")
            if self.subclient.data_readers != 3:
                self.log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            self.log.info("Get Nas client object")
            options_selector = OptionsSelector(self.commcell)
            nas_client = self.nas_helper.get_nas_client(self.client, self.agent)

            self.log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            # run full backup
            self.log.info("*" * 10 + " Starting Subclient FULL Backup " + "*" * 10)
            job = self._run_backup("FULL")
            self.log.info("*" * 10 + " Starting Subclient FULL Backup to compute dedupe ratio " + "*" * 10)
            job = self._run_backup("FULL")
            dedupeRatio = self.nas_helper.calculate_deduperatio(job)
            if (dedupeRatio < 80):
                self.log.info(f"The test case will FAIL as the Dedup Savings percentage is :{dedupeRatio}")
                raise Exception("Testcase failed as the dedupe ratio is low")
            else:
                self.log.info(" ###################### TC PASSED ###################### ")
                return 0

        except Exception as exp:
            self.log.error(f"Failed with error:{exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED
