# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that automatic synthetic full schedule starts every x days

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    synthetic_full_started()    --  Checks if a SFULL job has started or not

    move_system_days()          --  Changes the system time in days

"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.commonutils import get_int

from Server.JobManager.jobmanager_helper import JobManager

from cvpysdk.policies.schedule_policies import OperationType
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This testcase verifies that automatic synthetic full schedule starts every x days"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Automatic synthetic full - Every x days"
        self.tcinputs = {
            "StoragePolicyName": None,
            "SchedulePolicyName": None,
            "EveryXDays": None
        }

        self.commserv_machine = None
        self.commserve_client = None
        self.cl_machine = None
        self.idx_tc = None
        self.total_time_changed = 0
        self.jobs = []
        self.every_x_days = None
        self.sfull_started = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        backupset_name = 'Automatic_SFULL_everyxdays'
        subclient_name = 'automatic_sfull_sc1'

        self.cl_machine = Machine(self.client, self.commcell)
        self.idx_tc = IndexingTestcase(self)

        self.commserve_client = self.commcell.clients.get(self.commcell.commserv_hostname)
        self.commserv_machine = Machine(self.commserve_client, self.commcell)

        self.backupset = self.idx_tc.create_backupset(backupset_name, for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name=subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicyName')
        )

        self.log.info('********** Creating schedule policy **********')
        if not self.commcell.schedule_policies.has_policy(self.tcinputs.get('SchedulePolicyName')):
            self.log.info('********** Creating schedule, does not exist**********')
            self.schedule_policy = self.commcell.schedule_policies.add(
                name=self.tcinputs.get('SchedulePolicyName'),
                policy_type='Data Protection',
                associations=[],
                schedules=[{
                   'pattern': {
                       "freq_type": "automatic",
                       "run_synthetic_full": "every_x_days",
                       "days_between_synthetic_full": int(self.tcinputs.get('EveryXDays'))
                   },
                   'options': {
                       "backupLevel": "Synthetic_full"
                   }
               }]
            )
        else:
            self.log.info('********** Schedule policy already exists **********')
            self.schedule_policy = self.commcell.schedule_policies.get(self.tcinputs.get('SchedulePolicyName'))

        self.log.info('********** Associating the subclient with the schedule policy **********')
        self.schedule_policy.update_associations(
            associations=[{
                'clientName': self.client.client_name,
                'appName': 'File System',
                'backupsetName': backupset_name,
                'subclientName': subclient_name
            }],
            operation_type=OperationType.INCLUDE
        )

    def run(self):
        """Contains the core testcase logic and it is the one executed

                Steps:
                    1) Create a schedule policy with automatic synthetic full with "every X days" set already/manually.
                    2) Create a new backupset, subclient
                    3) Run FULL --> INC backups.
                    4) Move system time to some time before x days
                    5) Verify no SFULL has run.
                    6) Move system time to every x days.
                    7) Verify if SFULL has started.
                    8) Run one more new INC backup
                    9) Verify if SFULl starts the second time.

        """
        try:

            self.jobs = self.idx_tc.run_backup_sequence(self.subclient, [
                'new', 'full', 'edit', 'incremental'
            ])

            self.log.info('********** Getting scheduled interval days **********')
            schedule_id = self.schedule_policy.all_schedules[0]['schedule_id']
            schedule_details = self.schedule_policy.get_schedule(schedule_id)
            self.every_x_days = schedule_details['options']['backupOpts']['dataOpt']['daysBetweenSyntheticBackup']
            self.log.info(f'Interval: [{self.every_x_days}]')

            early_days = 5
            self.move_system_days(self.every_x_days - early_days)

            self.log.info('********** #1 - Checking if SFULL starts prematurely **********')
            if self.synthetic_full_started(self.jobs[-1]):
                raise Exception('Job started early than the scheduled x days.')
            else:
                self.log.info('********** #1 - Job did not run prematurely **********')

            self.log.info('********** #2 - Checking if SFULL starts when time is met **********')
            self.move_system_days(early_days + 1)

            if self.synthetic_full_started(self.jobs[-1]):
                self.log.info('********** #2 - Synthetic full job ran as per schedule **********')
            else:
                raise Exception('Synthetic full job did not start/complete as per schedule')

            self.log.info('********** Running few backup jobs and seeing if SFULL starts 2nd time **********')
            self.jobs.extend(self.idx_tc.run_backup_sequence(self.subclient, [
                'edit', 'incremental'
            ]))

            self.log.info('********** #3 - Checking if SFULL starts 2nd time **********')
            self.move_system_days(self.every_x_days)

            if self.synthetic_full_started(self.jobs[-1]):
                self.log.info('********** #3 - Synthetic full job ran 2nd time as per schedule **********')
            else:
                raise Exception('Synthetic full job did not start/complete as per schedule')

            self.log.info('********** #4 - Checking if SFULL starts without INC **********')
            self.move_system_days(self.every_x_days)

            if self.synthetic_full_started(self.sfull_started):
                raise Exception('Synthetic full job started without INC from automatic schedule.')
            else:
                self.log.info('********** #4 - Synthetic full did not run without INC **********')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

        finally:
            if self.total_time_changed:
                self.log.info(f'Resetting system time as earlier [-{self.total_time_changed}]')
                try:
                    self.commserv_machine.toggle_time_service(stop=False)
                    self.move_system_days(-self.total_time_changed)
                except Exception as exp:
                    self.log.exception(exp)
                    self.log.error('Failed to reset system time')
                try:
                    self.log.info('Trying to start windows time service')
                    self.commserv_machine.toggle_time_service(stop=False)
                except Exception as exp:
                    self.log.exception(exp)

    def synthetic_full_started(self, current_last_job):
        """Checks if a SFULL job has started or not

            Args:
                current_last_job    (obj)   --  The latest ran job of the subclient

            Returns:
                bool    --      True if SFULL started, False otherwise

        """

        total_attempts = get_int(self.tcinputs.get('TotalAttempts', 10), 10)
        attempt = 1

        self.log.info(f'********** Current last job of the subclient [{current_last_job.job_id}] **********')

        while attempt <= total_attempts:
            self.log.info('Waiting for 1 minute before checking for new job. Attempt [{0}/{1}]'.format(
                attempt, total_attempts
            ))
            time.sleep(60)

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
                        self.sfull_started = new_last_job
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

        self.log.info('Emptying run time table')
        self.idx_tc.options_help.update_commserve_db('delete from TM_RunTime')

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
