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

from Application.Exchange.ExchangeMailbox import utils
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """
    Class for executing the check whether Archive Index Phase and Finalize phase ran after
    killing the job in Archive Phase
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = 'Check whether Archive Index and Finalise phase are run after killing the job'
        self.exchange_mailbox = None
        self.proxy_machine = None
        self.new_association_mailboxes = None

        self.backup_stats_query = 'select phase from JMBkpAtmptStats where jobId=%d'
        self._utility = None
        self.smtp_list = list()
        self.mailboxes_list: list = list()
        self.job = None
        self.job_results_dir = None
        self.proxy_name = None
        self.testdata: TestData = None
        self.exmbclient_object: ExchangeMailbox = None

        self.tcinputs = {
            'ProxyServers': None,
            'Office365Plan': None
        }

    @test_step
    def set_new_associations_for_backup(self):
        """Set new associations to the client for backup"""

        subclient_content = {
            'mailboxNames': self.mailboxes_list,
            'plan_name': self.tcinputs['Office365Plan']
        }

        self.log.info('Associating %d new mailboxes', len(self.mailboxes_list))
        self.subclient.set_user_assocaition(subclient_content, use_policies=False)

    @test_step
    def backup_new_association_mailboxes(self):

        """Backup newly associated mailboxes of the client"""

        self.log.info('Starting backup Job..')
        self.job = self.subclient.backup()

        self.log.info('Job Id: %d', int(self.job.job_id))

    @test_step
    def wait_till_one_mailbox_gets_processed(self):
        """Wait till at least one mailbox gets processed"""
        initial_folders = len(self.proxy_machine.get_folders_in_path(self.job_results_dir))
        self.log.info('Initial number of folders in job results dir: %d', initial_folders)

        for _ in range(60):
            time.sleep(10)

            current_folders = len(self.proxy_machine.get_folders_in_path(self.job_results_dir))
            self.log.info("Current number of folders in Job results dir: %d", current_folders)

            if current_folders - initial_folders >= 2:
                break

    @test_step
    def kill_job(self):
        """Kill the job"""
        self.log.info('Trying to kill the job...')

        self.job.kill(wait_for_job_to_kill=True)
        self.log.info('Job Status after attempting to Kill: %s' % self.job.status.lower())
        if self.job.status.lower() not in ('completed w/ one or more errors', 'committed'):
            raise CVTestStepFailure('Failed to kill the job. Job might be completed before killing it.')

        self.log.info('Job successful killed. Current status: %s', self.job.status)
        time.sleep(5)  # wait for csdb to get updated

    @test_step
    def perform_required_checks(self):
        """Check whether Archive Index Phase and Finalize check ran"""
        job_id = int(self.job.job_id)

        self.backup_stats_query = self.backup_stats_query % job_id
        phases_ran = set(self._utility.exec_commserv_query(self.backup_stats_query)[0])

        if '10' not in phases_ran:
            raise CVTestStepFailure('Archive Index Phase did not run after killing the job: %d'
                                    % job_id)
        self.log.info('Archive Index Phase ran after killing the job: %d', job_id)

        if '15' not in phases_ran:
            raise CVTestStepFailure('Finalize Phase did not run after killing the job: %d' % job_id)
        self.log.info('Finalize Phase ran after killing the job: %d', job_id)

    def setup(self):
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info('Creating TestData using PowerShell')
        self.testdata = TestData(self.exmbclient_object)

        utils.create_test_mailboxes(self, count=4)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Exchange Client has been created")

        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info("Exchange Sub Client is created")

        self.exmbclient_object.cvoperations.modify_backup_streams(stream_count=1)
        self.log.info("Modified Backup stream to 1")

        self.proxy_name = self.tcinputs.get('ProxyServers', None)[0]
        self.proxy_machine = Machine(
            self.proxy_name, self.commcell
        )
        self.log.info('Initialized Proxy Machine Object')

        self._utility = OptionsSelector(self.commcell)

        self.job_results_dir = self.exmbclient_object.get_job_results_dir
        self.log.info('Job results dir: %s', self.job_results_dir)

    def run(self):
        try:
            self.set_new_associations_for_backup()
            self.backup_new_association_mailboxes()
            self.wait_till_one_mailbox_gets_processed()
            self.kill_job()
            self.perform_required_checks()
        except Exception as ex:
            handle_testcase_exception(self, ex)

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        self.testdata.delete_online_mailboxes(mailboxes_list=self.smtp_list)
        # Cleanup Operation: Cleaning Up the mailboxes created
