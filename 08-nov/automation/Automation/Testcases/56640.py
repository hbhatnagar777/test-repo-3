# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase is the only class defined in this file.
"""

import time
import xml.etree.ElementTree as ET

from Application.Exchange.ExchangeMailbox import utils
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """
    Class for executing check for Finalize phase with job suspend and resume
    and killing CVMailBackup process
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = 'Finalize phase check with job suspend and resume and process kill'
        self.proxy_machine = None
        self.sqlite_helper = None
        self.exchange_mailbox = None
        self.new_mailbox_associations = None
        self.guids_of_new_mailbox_associations = None

        self.job_status_query = "select data from JMMisc where jobId=%d and itemType=28"
        self.dat_file_query = "select indexingGUID, prevArchiveJobID, nextIncrementalRefTime," \
                              "curJobID, jobToken, curStatus from ArchiveResults"
        self._utility = None
        self.job = None
        self.job_results_dir = None
        self.proxy_name = None
        self.smtp_list = list()
        self.mailboxes_list: list = list()
        self.testdata: TestData = None
        self.exmbclient_object: ExchangeMailbox = None

        self.tcinputs = {
            "ProxyServers": None,
            'Office365Plan': None
        }

    @staticmethod
    def get_mailboxes_for_association(discovered_users, associated_users, count=4):
        """
        Get mailbox alias names and guids for new association
        Args:
            discovered_users(list): All discovered user of the subclient
            associated_users(list): Already associated users fo the subclient
            count(int): Number of required new mailboxes
        Returns:
            mailboxes_for_backup(list): List of alias names of mailboxes for new association
            guids_of_backup_mailboxes(list): List of guids of above mailboxes
        """
        associated_alias_names = set(user['alias_name'] for user in associated_users)
        mailboxes_for_backup = []
        guids_of_backup_mailboxes = set()

        for user in discovered_users:
            if count == 0:
                break

            if user['aliasName'] not in associated_alias_names:
                if user['msExchRecipientTypeDetails'] in (3, 36):  # group or shared mailboxes
                    mailboxes_for_backup.append(user['aliasName'])
                    guids_of_backup_mailboxes.add(user['user']['userGUID'])
                    count -= 1

        return mailboxes_for_backup, guids_of_backup_mailboxes

    def get_failed_or_skipped_mailboxes(self, job_id):
        """
        Get failed or skipped mailboxes for a backup job
        Args:
            job_id(int): Backup job id
        Returns:
            failed_or_skipped_mailboxes(list): List of dicts of failed or skipped mailbox details
            mailbox details - {
                "GUID": GUID of the mailbox,
                "SMTP": SMTP of the mailbox
            }
        """
        self.job_status_query = self.job_status_query % job_id

        xml_data = self._utility.exec_commserv_query(self.job_status_query)[0][0]
        xml = ET.fromstring(xml_data)

        failed_or_skipped_mailboxes = []
        for element in xml.iter('SourceMailboxStats'):
            failed_or_skipped_mailboxes.append({
                'GUID': element.attrib['GUID'],
                'SMTP': element.attrib['SMTP']
            })

        self.log.info('Failed or skipped mailboxes count: %d', len(failed_or_skipped_mailboxes))
        if len(failed_or_skipped_mailboxes) > 0:
            self.log.info('SMTPs of failed or skipped mailboxes: %s',
                          [element['SMTP'] for element in failed_or_skipped_mailboxes])

        return failed_or_skipped_mailboxes

    @staticmethod
    def wait_for_status(status, job):
        """
        Waits for the job status
        Args:
            status(str): Status to wait for
            job(Job): Instance of the job
        Returns:
            bool - True if status is achieved in 150 secs else False
        """
        start_time = time.time()

        while job.status.lower() != status.lower():
            if (job.is_finished is True) or (time.time() - start_time > 150):
                return False

            time.sleep(3)

        return True

    @test_step
    def set_new_associations_for_backup(self):
        """Set new associations to the client for backup"""
        subclient_content = {
            'mailboxNames': self.mailboxes_list,
            'plan_name': self.tcinputs['Office365Plan']
        }

        self.log.info('Associating %d new mailboxes', len(self.mailboxes_list))
        self.subclient.set_user_assocaition(subclient_content, use_policies=False)

        self.guids_of_new_mailbox_associations = self.get_mailboxes_guids(self.mailboxes_list)

    @test_step
    def get_mailboxes_guids(self, mailbox_list: list[str]) -> list[str]:
        """
            Get the GUID for the list of mailboxes
        """
        _guids_dict = self.exmbclient_object.csdb_helper.get_mailbox_guid(mailbox_list)

        _guids_list = list(_guids_dict.values())
        return _guids_list

    @test_step
    def backup_new_association_mailboxes(self):
        """Backup newly associated mailboxes of the client"""
        self.log.info('Starting backup Job..')
        self.job = self.subclient.backup()

        self.log.info('Job Id: %d', int(self.job.job_id))
        self.log.info('Job start time(Unix): %s', str(self.job.start_timestamp))

    @test_step
    def wait_for_one_mailbox_to_get_processed(self):
        """Wait for at least one mailbox to get processed"""
        initial_folders = len(self.proxy_machine.get_folders_in_path(self.job_results_dir))
        self.log.info('Initial number of folders in job results dir: %d', initial_folders)

        for _ in range(60):
            time.sleep(10)

            current_folders = len(self.proxy_machine.get_folders_in_path(self.job_results_dir))
            self.log.info("Current number of folders in Job results dir: %d", current_folders)

            if current_folders - initial_folders >= 2:
                break

    @test_step
    def suspend_job(self):
        """Suspend the job"""
        self.log.info('Trying to suspend the job..')

        self.job.pause(wait_for_job_to_pause=True)
        if self.job.status.lower() != 'suspended':
            raise CVTestStepFailure('Failed to Suspend the Job')

        self.log.info('Job Successfully Suspended')
        time.sleep(10)

    @test_step
    def resume_job(self):
        """Resume the job"""
        self.log.info('Trying to resume the job..')

        self.job.resume(wait_for_job_to_resume=True)
        if self.job.status.lower() != 'running':
            raise CVTestStepFailure('Failed to resume the Job')

        self.log.info('Job Successfully Resumed')
        time.sleep(5)

    @test_step
    def kill_the_backup_process(self):
        """Kill CVMailBackup process in proxy server"""
        self.log.info('Trying to kill CVMailBackup process..')
        self.proxy_machine.kill_process(process_name='CVMailBackup')
        while self.wait_for_status('Kill pending', self.job):
            time.sleep(15)
        if self.wait_for_status('Completed w/ one or more errors', self.job):
            self.log.info('Successfully killed CVMailBackup Process')
        else:
            raise Exception('Job did not achieve pending state after killing CVMailBackup process')

    @test_step
    def wait_for_job_completion(self):
        """Wait for backup job to complete"""
        while not self.job.is_finished:
            time.sleep(15)
            self.log.info('Backup job still running. Current Phase : %s', self.job.phase)

        if 'completed' not in self.job.status.lower():
            raise Exception('Backup job failed with status %s' % self.job.status)

        self.log.info('Backup job completed with status: %s', self.job.status)

    @test_step
    def perform_required_checks(self):
        """Perform required checks to verify finalize phase"""
        job_id = int(self.job.job_id)
        job_start_time = int(self.job.start_timestamp)

        failed_or_skipped_mailboxes = self.get_failed_or_skipped_mailboxes(job_id)
        failed_or_skipped_guids = set(
            element['GUID'] for element in failed_or_skipped_mailboxes
        )

        dat_file_content = self.sqlite_helper.execute_dat_file_query(
            self.job_results_dir, 'ExMBJobInfo.dat', self.dat_file_query
        )

        for row in dat_file_content:
            if row[0] in failed_or_skipped_guids:
                self.log.info("Checking GUID [%s] Failed", row[0])
                if row[1]==0:
                    self.log.info("Previous Archive job ID has not moved: PASSED")
                else:
                    raise CVTestStepFailure("Mailbox check failed as the PrevArchiveJobID is greater than 0")
                if row[2] < job_start_time:
                    self.log.info("Reference time has not moved for the failed/skipped mailbox:PASSED")
                else:
                    raise CVTestStepFailure("Mailbox check failed as the ref time has shifted for the failed mailbox")
            else:
                self.log.info("Checking GUID [%s] Successful/To Be Processed",row[0])
                if row[1] == job_id and row[2] == job_start_time:
                    self.log.info("Job ID, nextIncrementRefTime and nextAgeRuleRefTime is shifted: mailbox is successful")
                elif row[1] != job_id and row[2] < job_start_time:
                    self.log.info("Job ID, nextIncrementRefTime and nextAgeRuleRefTime is shifted: mailbox is To Processed")
                else:
                    raise CVTestStepFailure("Mailbox Check Failed as one of the parameters has given unexpected value")

    def setup(self):
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info('Creating TestData using PowerShell')
        self.testdata = TestData(self.exmbclient_object)

        utils.create_test_mailboxes(self, count=8)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Exchange Client has been created")

        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info("Exchange Subclient is created")

        self.exmbclient_object.cvoperations.modify_backup_streams(stream_count=1)
        self.log.info("Modified Backup stream to 1")

        self.proxy_name = self.tcinputs.get('ProxyServers', None)[0]
        self.proxy_machine = Machine(
            self.proxy_name, self.commcell
        )
        self.log.info('Initialized Proxy Machine Object')

        self.sqlite_helper = SQLiteHelper(self)
        self.log.info('Initialized SQLiteHelper Object')

        self._utility = OptionsSelector(self.commcell)

        self.job_results_dir = self.exmbclient_object.get_job_results_dir
        self.log.info('Job results dir: %s', self.job_results_dir)

    def run(self):
        try:
            self.set_new_associations_for_backup()
            self.backup_new_association_mailboxes()
            self.wait_for_one_mailbox_to_get_processed()
            self.suspend_job()
            self.resume_job()
            self.kill_the_backup_process()
            self.wait_for_job_completion()
            self.perform_required_checks()
        except Exception as ex:
            handle_testcase_exception(self, ex)

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        # Cleanup Operation: Cleaning Up the mailboxes created
        self.testdata.delete_online_mailboxes(mailboxes_list=self.smtp_list)
        self.commcell.clients.delete(self.client.client_name)
        self.log.info('Deleted the Client')
