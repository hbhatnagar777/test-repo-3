# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import os
import time
import filecmp
import traceback

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase

from Indexing.tools import idxcli
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase

from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = 'Indexing - RFC Upload/Download'

        self._debug = False

        self.job = None
        self.idxcli = None
        self.idx_tc = None
        self.idx_db = None
        self.idx_helpers = None
        self.isc_machine = None
        self.temp_dir = None
        self.cl_machine = None
        self.storage_policy = None
        self.index_cache_path = None

        self.tcinputs = {
            'AgentName': None,
            'ClientName': None,
            'StoragePolicy': None,
        }


    # Setup function of this test case
    def setup(self):
        try:
            self.log.info('Started setup %s testcase', self.id)
            self.storage_policy = self.commcell.storage_policies.get(
                self.tcinputs.get('StoragePolicy'))
            self.cl_machine = Machine(self.tcinputs.get('ClientName'), self.commcell)
            self.idx_tc = IndexingTestcase(self)
            self.idx_helpers = IndexingHelpers(self.commcell)

            # Create test backupset/subclient/content
            self.log.info("Creating RFC Backupset")
            if self._debug:
                self.backupset = self.agent.backupsets.get('rfc_test_56563')
            else:
                self.backupset = self.idx_tc.create_backupset('rfc_test_56563',
                                                              for_validation=False)

            self.log.info("Creating RFC Subclient and Content")

            if self._debug:
                self.subclient = self.backupset.subclients.get('56563')
            else:
                self.subclient = self.idx_tc.create_subclient(
                    name="56563",
                    backupset_obj=self.backupset,
                    storage_policy=self.storage_policy.name
                )
                self.idx_tc.new_testdata(self.subclient.content, dirs=5, files=25, file_size=20480)

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception(exp)


    # Run function of this test case
    def run(self):
        try:
            self.log.info('Started executing %s testcase', self.id)

            # Start full backup
            self.log.info("Starting full backup for RFC Subclient")
            self.job = self.idx_tc.run_backup(self.subclient, "Full")

            self.idx_db = index_db.get(self.subclient)
            self.log.info('Index DB: %s', self.idx_db.index_server.name)
            self.idxcli = idxcli.IdxCLI(self.idx_db.index_server)

            # Create RFC Test Files
            self.isc_machine = self.idx_db.isc_machine
            self.index_cache_path = self.idx_helpers.get_index_cache(self.idx_db.index_server)
            self.log.info("Index Cache: %s", self.index_cache_path)

            self.temp_dir = self.isc_machine.join_path(self.index_cache_path, 'Temp')
            self.log.info("Temp Dir: %s", self.temp_dir)

            self.log.info("Creating RFC Test Files")
            if not self.isc_machine.check_directory_exists(self.temp_dir + "\\rfc_test_56563"):
                self.isc_machine.create_directory(self.temp_dir + "\\rfc_test_56563")

            self.b_file = self.isc_machine.join_path(self.temp_dir, "rfc_test_56563", "b.txt")
            self.c_file = self.isc_machine.join_path(self.temp_dir, "rfc_test_56563", "c.txt")

            self.isc_machine.create_file(self.b_file, "1")
            self.isc_machine.create_file(self.c_file, "2")

            # Upload to RFC
            self.job = self.subclient.backup("Full")
            job_manager = JobManager(self.job, self.commcell)
            job_manager.wait_for_phase(phase='backup')
            time.sleep(30)
            self.log.info("Upload test files to RFC for Job ID %s", self.job.job_id)
            self.idxcli.do_rfc_upload(self.job.job_id, "", self.b_file)
            self.idxcli.do_rfc_upload(self.job.job_id, "", self.c_file, "Y")
            self.idxcli.do_rfc_upload(self.job.job_id, "subfolder", self.b_file)
            self.idxcli.do_rfc_upload(self.job.job_id, "subfolder", self.c_file, "Y")

            self.download_and_compare()
            self.job.wait_for_completion()

            # Check RFC files are backed up
            self.log.info("Verify RFC Files in CS DB")
            query = "SELECT * FROM archFile WHERE name = 'RFC_AFILE' AND isValid = 1 AND jobId =" + self.job.job_id
            self.csdb.execute(query)
            row = self.csdb.fetch_one_row()
            if not row[0]:
                raise Exception("Job ID '%s' did not contain RFC_AFILE", self.job.job_id)

            self.log.info("Downloading RFC Files after job has completed")
            self.download_and_compare()

            # TODO: Synthentic Full Backup, validate RFC Files move forward
            # self.log.info("Starting Synthetic Full Backup")
            # self.sf_job = self.subclient.backup("Synthetic Full")
            # job_manager = JobManager(self.sf_job, self.commcell)
            # job_manager.wait_for_phase(phase='completed')

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise Exception(exp)


    def download_and_compare(self):
            # Download from RFC
            self.log.info("Download from RFC for Job ID %s", self.job.job_id)            

            self.restore = self.isc_machine.join_path(self.temp_dir, "rfc_test_56563", 'restore')
            self.restore_sub = self.isc_machine.join_path(self.temp_dir, "rfc_test_56563", 'restore', 'subfolder')

            # Check and delete Restore directory if exists
            if not self.isc_machine.check_directory_exists(self.restore):
                self.log.info("Restore directory exists, deleting")
                self.isc_machine.remove_directory(self.restore)

            self.idxcli.do_rfc_download(self.job.job_id, "", self.restore)
            self.idxcli.do_rfc_download(self.job.job_id, "subfolder", self.restore_sub)

            # Verify file is the same
            self.log.info("Verify files are valid")
            if not self.isc_machine.compare_files(self.isc_machine, self.b_file, self.restore + self.isc_machine.os_sep + "b.txt"):
                self.log.error('B.txt failed verification')
                raise Exception('File Verification Failed')
            if not self.isc_machine.compare_files(self.isc_machine, self.c_file, self.restore + self.isc_machine.os_sep + "c.txt"):
                self.log.error('C.txt compressed failed verification')
                raise Exception('File Verification Failed')
            if not self.isc_machine.compare_files(self.isc_machine, self.b_file, self.restore_sub + self.isc_machine.os_sep + "b.txt"):
                self.log.error('B.txt subfolder failed verification')
                raise Exception('File Verification Failed')
            if not self.isc_machine.compare_files(self.isc_machine, self.c_file, self.restore_sub + self.isc_machine.os_sep + "c.txt"):
                self.log.error('C.txt compressed subfolder failed verification')
                raise Exception('File Verification Failed')

    # Tear down function of this test case
    def tear_down(self):
        # Delete temp RFC Directory
        self.isc_machine.remove_directory(self.temp_dir + "rfc_test_56563")
