# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

import time
import random
import string
import xml.etree.ElementTree as ET

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing Restartable backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "MultiStream NDMP - NetApp C mode Cluster as client - Single volume content - Restartabilty case"
        self.tcinputs = {
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def _get_restart_string(self, job_id):
        """Returns the restart string for specified job"""
        query = "SELECT restartString FROM JMJobInfo WHERE jobid='{0}'".format(job_id)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        if cur and cur[0]:
            xml = str(cur[0]).split("|")[0]
            return int(
                self._get_attribute_value_from_xml(xml, "ValidRestartString", "restartByteOffset")
            )
        else:
            return 0

    def _get_chunks_count(self, job_id):
        """Returns the chunks count for specified job"""
        query = "SELECT COUNT(*) FROM archChunkMapping WHERE jobId = '{0}'".format(job_id)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        if cur:
            return int(cur[0])
        else:
            raise Exception("Failed to get chunks count")

    def _wait_for_restartable_point(self, job):
        """Pauses the test case till it finds restartable point"""
        try:
            while True:
                restart_string = self._get_restart_string(int(job.job_id))
                if restart_string > 0:
                    return restart_string

                self._log.info("Waiting for Restart String to set")
                time.sleep(5)

                if job.is_finished:
                    self._log.info("Job finished skip restart string job")
                    return 0
        except Exception as exp:
            self._log.error("Failed to wait till restart point:" + str(exp))
            raise Exception("Failed to wait till restart point:" + str(exp))

    def _get_attribute_value_from_xml(self, input_xml, element, attribute):
        """Returns the attribute value from specified xml"""
        xml = ET.fromstring(input_xml)
        elem = xml.find(element)
        return elem.get(attribute)

    def _resume_job(self, job):
        """Resumes the specified job"""
        job.resume()

        while str(job.status).lower() != "running":
            self._log.info("Waiting for job status to change to running")
            time.sleep(20)

        self._log.info("Resumed job")

    def _kill_nasbackup_exe(self):
        """Terminates the NASBackup.exe"""
        commserv_machine = Machine(self.commserver_name, self.commcell)

        cmd = 'taskkill /s {0} /F /FI "IMAGENAME eq NasBackup.exe"'.format(self.commserver_name)

        commserv_machine.execute_command(cmd)
        time.sleep(10)
        self._log.info("Successfully killed the NasBackup.exe process")

    def _check_restart_offset(self, job_id, restart_offset):
        """"Validates the restart offset value"""
        new_restart_offset = self._get_restart_string(job_id)
        self._log.info("Restart offset before resuming: " + str(restart_offset))
        self._log.info("Restart offset after resuming: " + str(new_restart_offset))
        if new_restart_offset != restart_offset:
            raise Exception("Restart String was reset to: " + str(new_restart_offset))
        time.sleep(5)

    def _run_restartable_backup(self, job):
        """Executes the restartable backup case"""
        self._log.info("Check for Restartable String. Will wait till the flag is set.")
        restart_offset = self._wait_for_restartable_point(job)

        if job.is_finished:
            return

        self._log.info("restartable point flag is set")

        self._log.info("Pause the job")
        job.pause()
        time.sleep(20)

        self._log.info("Check if job status is suspended")
        if job.is_finished:
            self._log.info("Job finished skip the case")
            return

        while str(job.status).lower() != "suspended":
            self._log.info("Waiting for job status to change to suspended")
            time.sleep(20)

        time.sleep(5)
        self._log.info(str(job.delay_reason))

        chunks_count = self._get_chunks_count(int(job.job_id))

        self._resume_job(job)

        self._check_restart_offset(int(job.job_id), restart_offset)

        # Wait for 2 more chunks to create
        self._log.info("Number of chunks created before resume: " + str(chunks_count))
        self._log.info("Wait for 2 more chunks to be created")
        while True:
            new_chunks_count = self._get_chunks_count(int(job.job_id))
            self._log.info(
                "Waiting for chunks count to be equal or more than: %d, current chunk count: \
                   %d ", (chunks_count + 2), new_chunks_count
            )

            if new_chunks_count >= (chunks_count + 2):
                break
            time.sleep(5)

        if job.is_finished:
            self._log.info("Job finished skip the case")
            return

        self._kill_nasbackup_exe()

        restart_offset = self._get_restart_string(int(job.job_id))

        # check if job status is pending for 2 minutes
        count = 0
        status_pending = False
        while count <= 300:
            if str(job.status.lower()) == 'pending':
                status_pending = True
                break
            count = count + 10
            time.sleep(10)

        if not status_pending:
            raise Exception("Job {0} Status is not changed to Pending. It is still: {1}".format(
                str(job.job_id), str(job.status)))

        self._log.info("Job status is: " + str(job.status))

        if job.is_finished:
            self._log.info("Job finished skip the case")
            return

        self._resume_job(job)
        self._check_restart_offset(int(job.job_id), restart_offset)

        if job.is_finished:
            self._log.info("Job finished skip the case")
            return

        self._log.info("Wait for job completion")
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished backup job")

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self._log = logger.get_log()
        self.commserver_name = self.commcell.commserv_name
        self._nas_helper = NASHelper()

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

            nas_client = self._nas_helper.get_nas_client(self.client, self.agent, is_cluster=True)

            self._log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            # run full backup
            self._log.info("*" * 10 + " Starting Subclient FULL Backup " + "*" * 10)
            job = self.subclient.backup("FULL")
            self._log.info("Started FULL backup with Job ID: " + str(job.job_id))
            # Run restartable backup case
            self._run_restartable_backup(job)
            size = nas_client.get_content_size(self.subclient.content)

            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            self._log.info("*" * 10 + " Run out of place restore " + "*" * 10)
            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name,
                windows_restore_location, self.subclient.content)
            self._log.info("Started restore out of place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + str(job.delay_reason)
                )

            self._log.info("Successfully finished restore out of place")

            self._nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                self.subclient.content)

            self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)

            job = self.subclient.restore_in_place([self.subclient.content[0]])

            self._log.info("Started restore in place jb with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: " + str(job.delay_reason)
                )

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                [self.subclient.content[0]]
            )
        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
