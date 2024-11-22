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

    setup()             --  setup function of this test case

    run()               --  run function of this test case
	
	_run_backup()       --  Run backup type function
"""

import random
import string

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class to verify NAS NDMP Deduplication"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Testcase to verify NAS NDMP Deduplication"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "SubclientName": None,
            "BackupsetName": None,
            "AgentName": None,
            "SubclientContent": None,
            "CIFSShareUser": None,
            "CIFSSharePassword":None,
            "FilerRestoreLocation": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self._log = logger.get_log()
        self.commserver_name = self.commcell.commserv_name
        self._nas_helper = NASHelper()

		
    def _run_backup(self, backup_type):
        """Starts backup job"""
        
        job = self._subclient.backup(backup_type)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )
        return job	
		
    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing %s testcase", self.id)

            # check the data readers count
            self._log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self._log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                self._log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            self._log.info("Get Nas client object")
            options_selector = OptionsSelector(self.commcell)

            nas_client = self._nas_helper.get_nas_client(self.client, self.agent)

            self._log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            # run full backup
            self._log.info("*" * 10 + " Starting Subclient FULL Backup " + "*" * 10)
            job = self._run_backup("FULL")
            self._log.info("*" * 10 + " Starting Subclient FULL Backup to compute dedupe ratio " + "*" * 10)
            job = self._run_backup("FULL")
						
            query = "SELECT SUM(ISNULL(S.sizeOnMedia, 0)) FROM JMJobDataStats S WHERE S.commCellId = 2 AND S.jobId =" + job.job_id + " AND S.auxCopyJobId = 0" 
            self.csdb.execute(query)
            sizeOnMedia = self.csdb.fetch_one_row()
        
            query1 = "SELECT totalUncompBytes FROM JMBkpStats WHERE jobId = "+ job.job_id + "AND commCellId = 2"
            self.csdb.execute(query1)
            unCompBytes = self.csdb.fetch_one_row()
            self._log.info(sizeOnMedia[0])
            self._log.info(unCompBytes[0])
            if (int(unCompBytes[0]) > int(sizeOnMedia[0])):
                dedupeRatio = ((int(unCompBytes[0]) - int(sizeOnMedia[0]))/(int(unCompBytes[0]) * 1.0)) * 100
                self._log.info("Dedupe ratio is %s", dedupeRatio)
                if (dedupeRatio < 80):
                    self._log.info("The test case will FAIL as the Dedup Savings percentage is :%s" , dedupeRatio)
                    return 1
                else:	
                    self._log.info(" ###################### TC PASSED ###################### ")            
                    return 0
            else:
                raise Exception(
                    "Testcase failed as the dedupe ratio is low"                        
                )			
            
        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
