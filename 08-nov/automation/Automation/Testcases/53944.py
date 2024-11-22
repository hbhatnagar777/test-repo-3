# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that automatic synthetic full schedule when estimated free space is greater
than 50%

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    synthetic_full_started()    --  Checks if a SFULL job has started or not

    move_system_days()          --  Changes the system time in days

    change_time_restart_services()  --  Changes the system time in days by keeping services off and turning
    it on afterwards

Inputs:
    StoragePolicyName       --      The name of the storage policy

    SchedulePolicyName      --      The name of the schedule policy

    CSUsername              --      The CS machine username

    CSPassword              --      The CS machine password

    TotalAttempts(optional) --      The total number of attempts to check if SFULL had started. Default 15

"""

import time

from cvpysdk.policies.schedule_policies import OperationType

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.commonutils import get_int

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers

from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """This testcase verifies that automatic synthetic full schedule when estimated free space is
    greater than 50%

        Steps:
            1) Create a subclient and associate automatic synthetic full for "space reclaim" option.
            2) Create huge testdata. Example: 2 GB
            3) Run Incremental job
            4) Run SFULL
            5) Run INC
            6) Move system time and verify if no synthetic full job is started un usually.
            7) Delete most of the files making sure we can get 50% free space. i.e retain only 2 MB of files and
            delete rest. So total application size is 1 GB+ but quota size is 2 MB and minimum reclaimed space is 1 GB+
            8) Run INC
            9) Change system time to 7 days forward and wait for the automatic synthfull job to run.
            10) Verify if SFULL job is started.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Automatic SFULL based on estimated free space'
        self.tcinputs = {
            'StoragePolicyName': None,
            'SchedulePolicyName': None,
            'CSUsername': None,
            'CSPassword': None
        }

        self.backupset = None
        self.subclient = None

        self.cl_machine = None
        self.cl_delim = None
        self.idx_tc = None
        self.idx_help = None

        self.total_time_changed = 0

    def setup(self):
        """All testcase objects are initializes in this method"""

        backupset_name = self.tcinputs.get('Backupset', 'auto_sfull_space_reclaim')
        subclient_name = self.tcinputs.get('Subclient', self.id)

        self.cl_machine = Machine(self.client, self.commcell)
        self.cl_delim = self.cl_machine.os_sep

        self.commserve_client = self.commcell.commserv_client
        self.commserv_machine = Machine(
            self.commserve_client.client_hostname,
            username=self.tcinputs.get('CSUsername'),
            password=self.tcinputs.get('CSPassword')
        )

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset(backupset_name, for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name=subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicyName')
        )

        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        schedule_policy_name = self.tcinputs.get('SchedulePolicyName')

        if not self.commcell.schedule_policies.has_policy(schedule_policy_name):
            raise Exception(f'No schedule policy exists with name [{schedule_policy_name}]')

        self.log.info('********** Associating the subclient with the schedule policy **********')
        schedule_policy = self.commcell.schedule_policies.get(schedule_policy_name)
        schedule_policy.update_associations(
            associations=[{
                'clientName': self.client.client_name,
                'appName': 'File System',
                'backupsetName': backupset_name,
                'subclientName': subclient_name
            }],
            operation_type=OperationType.INCLUDE
        )

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            sc_content = self.subclient.content

            self.idx_tc.new_testdata(sc_content)
            self.idx_tc.create_only_files(sc_content, base_dir='to_delete', count=6, size=(307200000, 409600000))
            self.idx_tc.create_only_files(sc_content, base_dir='to_keep', count=4, size=(307200000, 409600000))

            jobs = self.idx_tc.run_backup_sequence(self.subclient, [
                'full', 'edit', 'incremental', 'synthetic_full', 'edit', 'incremental'
            ])

            self.change_time_restart_services(8)

            if self.synthetic_full_started(jobs[-1]):
                raise Exception('Job started when there is no space reclaimed')
            else:
                self.log.info('SFULL did not start unexpectedly')

            self.log.info('********** Deleting large files directory ********')
            for path in sc_content:
                large_file_dir = self.cl_delim.join([path, 'to_delete'])
                self.cl_machine.remove_directory(large_file_dir)

            jobs = self.idx_tc.run_backup_sequence(self.subclient, [
                'edit', 'incremental'
            ])

            if self.indexing_level == 'backupset':
                quota_size = self.idx_help.get_quota_size(backupset_obj=self.backupset)
            else:
                quota_size = self.idx_help.get_quota_size(subclient_obj=self.subclient)

            self.log.info('********** Quota size [{0}] **********'.format(quota_size))

            application_size = self.idx_tc.get_application_size(subclient_obj=self.subclient, cycle_num=None)
            self.log.info('********** Application size [{0}] **********'.format(application_size))

            savings = ((application_size-quota_size)/application_size)*100
            self.log.info('********** Savings seen is [{0}%] **********'.format(savings))

            if savings > 50:
                self.log.info('Savings is more than 50%')
            else:
                raise Exception('Saving is not more than 50% after deleting data')

            self.log.info('Expecting synthetic full job to run automatically after 7 days')

            self.change_time_restart_services(8)

            if self.synthetic_full_started(jobs[-1]):
                self.log.info('********** Synthetic full job started and completed as per schedule **********')
            else:
                raise Exception('Synthetic full job did not start/complete as per schedule')

            self.log.info('********** Testcase completed successfully **********')

        except Exception as exp:
            self.log.error('Test case failed with error')
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

        finally:
            attempts = 0
            while self.total_time_changed != 0:
                attempts += 1
                self.log.info(f'Resetting system time as earlier [-{self.total_time_changed}]')

                if attempts == 3:
                    break

                try:
                    self.move_system_days(-self.total_time_changed)
                    self.commserv_machine.toggle_time_service(stop=False)
                except Exception as exp:
                    self.log.exception(exp)
                    self.log.error('Failed to reset system time.')
                    time.sleep(120)

    def synthetic_full_started(self, current_last_job):
        """Checks if a SFULL job has started or not

            Args:
                current_last_job    (obj)   --  The latest ran job of the subclient

            Returns:
                bool    --      True if SFULL started, False otherwise

        """

        total_attempts = get_int(self.tcinputs.get('TotalAttempts', 15), 15)
        attempt = 1

        self.log.info(f'********** Current last job of the subclient [{current_last_job.job_id}] **********')

        while attempt <= total_attempts:
            self.log.info('Waiting for 2 minutes before checking for new job. Attempt [{0}/{1}]'.format(
                attempt, total_attempts
            ))
            time.sleep(120)

            new_last_job = self.idx_tc.get_last_job(self.subclient)

            self.log.info(f'Last job of the subclient [{new_last_job.job_id}]')

            if new_last_job.job_id == current_last_job.job_id:
                self.log.info('No new job started for the subclient, checking again.')
                attempt += 1
                continue
            else:
                self.log.info(f'********** New job [{new_last_job.job_id}] started for the subclient **********')
                if new_last_job.job_type == 'Synthetic Full':

                    self.log.info('Waiting for the job to complete')
                    jm_obj = JobManager(new_last_job)

                    try:
                        jm_obj.wait_for_state('completed')
                        self.log.info('A synthetic full job has been started and it is complete')
                        return True
                    except Exception as exp:
                        self.log.exception(exp)
                        return False

                else:
                    self.log.error('A job other than synthetic full ran')
                    return False

        return False

    def move_system_days(self, days):
        """Changes the system time in days

            Args:
                days        (int)   --      The number of days to move

            Returns:
                None

            Raises:
                Exception if unable to change the system time

        """

        self.log.info(f'Moving system time by [{days}] days')

        current_time = self.commserv_machine.current_time()
        self.log.info(f'Current machine time [{current_time}]')

        total_attempts = 3
        attempt = 1

        self.commserv_machine.toggle_time_service(stop=True)

        while attempt <= total_attempts:
            self.log.info(f'Changing system time Attempt [{attempt}/{total_attempts}]')

            # Adding in exception block since sometimes webservice crashes/times out after changing system time
            try:
                self.commserv_machine.change_system_time(86400 * days)
            except Exception as exp:
                self.log.exception(exp)
                self.log.error('Exception while changing system time. Ignoring and proceeding further')

            time.sleep(30)

            try:
                changed_time = self.commserv_machine.current_time()
            except Exception as exp:
                self.log.exception(exp)
                self.log.error('Exception while getting system time. Waiting sometime and getting again')
                time.sleep(30)
                changed_time = self.commserv_machine.current_time()

            self.log.info(f'After change machine time [{changed_time}]')

            if current_time.date() == changed_time.date():
                self.log.error('System time has not changed. Changing again.')
                attempt += 1
                continue
            else:
                self.log.info('********** System time has changed **********')
                self.total_time_changed += days
                return

        raise Exception('Unable to change system time after multiple attempts')

    def change_time_restart_services(self, days):
        """Changes the system time in days by keeping services off and turning it on afterwards

            Args:
                days        (int)   --      The number of days to move

            Returns:
                None

            Raises:
                Exception if unable to change the system time

        """

        self.log.info('***** Stopping all services *****')
        self.commserve_client.stop_service(service_name='GxCVD(Instance001)')

        self.move_system_days(days)

        services_up = False
        attempt = 0

        while not services_up:
            self.log.info('***** Starting all services *****')
            self.commserv_machine.start_all_cv_services()

            self.log.info('Waiting for 5 minutes')
            time.sleep(300)

            self.log.info('Checking if API server is up and reachable.')
            try:
                attempt += 1
                self.commserve_client.refresh()
                self.log.info('API server is up.')
                services_up = True
            except Exception as e:
                self.log.error('Exception while checking API server after restart [%s]. Attempt [%s]', e, attempt)
                time.sleep(30)
                if attempt > 3:
                    break
