# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase runs a big backup job and verifies if system resources like process memory, thread, handles are consumed
within limits with and without job interruption.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    prepare_thresholds()        --  Sets default value for the threshold to validate

    increase_thresholds()       --  Increases the threshold by the specific "increase" percentage configured

    get_index_process_id()      --  Finds out the process ID for the specific indexing process app

    fetch_process_ids()         --  Gets the process ID for both IndexServer and LogManager processes

    fetch_stats()               --  Fetches the stats for both IndexServer and LogManager processes, logs and returns.

    print_process_stats()       --  Prints the stats for the given process

    check_threshold()           --  Validates if the threshold is under limits for the given indexing process and stats

    validate_interrupted_process_stats()    --  Validates the stats of the process

    take_process_dump()         --  Takes the process dump for the given app

"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.commonutils import get_int, set_defaults

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase runs a big backup job and verifies if system resources like process memory, thread, handles are
    consumed within limits with and without job interruption.

        Steps:
            1) Create a new backupset (or use existing) and start a FULL job (run one job previous to it if needed)
            2) Suspend the job when it is as backup phase
            3) Fetch the process stats for IndexServer and LogManager and validate it against the thresholds.
            4) Increase threshold by a certain percentage.
            5) If the stats go beyond the accepted limit then fail the testcase/continue
            6) Resume the job.
            7) Repeat steps 2-6.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Scale test - Resource monitoring'

        self.tcinputs = {
            'TestData': None,
            'StoragePolicy': None,
            'TotalInterrupts': None,
            'Thresholds': None,
            'ExitOnFail': None,
            'InterruptInterval': None
            # Optional - JobQueryFrequency - default=60 secs
            # Optional - JobTimeLimit - default=300 mins
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.testdata = None
        self.idx_db = None

        self.full_job = None
        self.validation_failed = False
        self.thresholds = {}
        self.process_ids = {}
        self.attempt = 0

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.log.info('***** Thresholds *****')
        self.prepare_thresholds()
        self.log.info(self.thresholds)

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)
        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        if self._subclient is None:
            self.log.info('***** Creating backupset and subclient since not given as input ****')
            self.backupset = self.idx_tc.create_backupset('scale_test_res_mon', for_validation=False)

            self.subclient = self.idx_tc.create_subclient(
                name='sc1_scale',
                backupset_obj=self.backupset,
                storage_policy=self.tcinputs.get('StoragePolicy')
            )

            self.log.info('***** Running DUMMY FULL backup to set IndexServer *****')
            self.subclient.backup('Full')

            self.subclient.trueup_option = True
            self.subclient.scan_type = 2

        self.log.info('***** Setting huge dataset as testdata *****')
        self.testdata = self.tcinputs.get('TestData')
        self.subclient.content = self.testdata.split(';')

        if self.tcinputs.get('PreRunJob', None):
            self.log.info('***** Pre running backup job *****')
            self.idx_tc.run_backup(self.subclient, 'Full', verify_backup=False)
        else:
            self.log.info('***** Not pre-running FULL backup *****')

        self.log.info('***** Getting IndexServer for the backupset *****')
        self.idx_db = index_db.get(self.subclient if self.indexing_level == 'subclient' else self.backupset)
        self.log.info(f'IndexServer MA is [{self.idx_db.index_server.client_name}]')

    def run(self):
        """Contains the core testcase logic"""
        try:

            job_query_freq = get_int(self.tcinputs.get('JobQueryFrequency', 60), 60)  # Seconds
            job_time_limit = get_int(self.tcinputs.get('JobTimeLimit', 300), 300)  # Minutes

            self.log.info('***** Starting FULL backup *****')
            self.full_job = self.subclient.backup('Full')

            jm_obj = JobManager(self.full_job)
            jm_obj.wait_for_phase('backup', check_frequency=job_query_freq)
            self.log.info('***** Job is at backup phase now *****')

            self.log.info('***** Fetching process IDs *****')
            self.fetch_process_ids()

            self.log.info('***** Process stats at the start *****')
            self.fetch_stats()

            total_interrupts = get_int(self.tcinputs.get('TotalInterrupts'), 4)
            interrupt_interval = get_int(self.tcinputs.get('InterruptInterval'), 120)

            for self.attempt in range(total_interrupts):
                self.log.info(f'***** Attempt [{self.attempt+1}/{total_interrupts}] *****')
                self.log.info(f'Job status [{self.full_job.status}]. Waiting for [{interrupt_interval}] seconds.')
                time.sleep(interrupt_interval)

                if 'waiting' in self.full_job.status.lower():
                    self.full_job.resume(wait_for_job_to_resume=True)
                    self.log.info('Job is resumed')
                    time.sleep(30)

                if self.full_job.is_finished:
                    self.log.error('Job already completed ahead (before interruption)')
                    break

                self.log.info('Suspending the job')
                self.full_job.pause(wait_for_job_to_pause=True)
                time.sleep(30)

                self.increase_thresholds()
                self.validate_interrupted_process_stats()

                self.log.info('Resuming the job')
                self.full_job.resume(wait_for_job_to_resume=True)

            jm_obj.wait_for_state('completed', retry_interval=job_query_freq, time_limit=job_time_limit)

            self.log.info('***** Process stats at the end *****')
            self.fetch_stats()

            if self.validation_failed:
                self.log.error('Testcase completed, but certain process stats went beyond the thresholds.')
                self.status = constants.FAILED
            else:
                self.log.info('***** Job completed successfully within resource utilization conditions *****')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

        finally:
            if self.full_job and not self.full_job.is_finished:
                self.log.error('Killing job as testcase raised exception')
                self.full_job.kill(wait_for_job_to_kill=True)

    def prepare_thresholds(self):
        """Sets default value for the threshold to validate"""

        set_defaults(self.tcinputs['Thresholds'], {
            'IndexServer': {
                'HandleCount': {
                    'value': 400,
                    'AcceptedVariation': 5,
                    'Increase': 3
                },
                'ThreadCount': {
                    'value': 10,
                    'AcceptedVariation': 5,
                    'Increase': 3
                },
                'CPUUsage': {
                    'value': 0,
                    'AcceptedVariation': 0,
                    'Increase': 0
                },
                'Memory': {
                    'value': 600000000,  # bytes
                    'AcceptedVariation': 10,  # percentage
                    'Increase': 0  # percentage
                }
            },
            'LogManager': {
                'HandleCount': {
                    'value': 300,
                    'AcceptedVariation': 5,
                    'Increase': 3
                },
                'ThreadCount': {
                    'value': 25,
                    'AcceptedVariation': 5,
                    'Increase': 3
                },
                'CPUUsage': {
                    'value': 0,
                    'AcceptedVariation': 0,
                    'Increase': 3
                },
                'Memory': {
                    'value': 200000000,
                    'AcceptedVariation': 10,
                    'Increase': 3
                }
            }
        })

        self.thresholds = self.tcinputs['Thresholds']

    def increase_thresholds(self):
        """Increases the threshold by the specific "increase" percentage configured"""

        self.log.info('Increasing thresholds')
        for app, stats in self.thresholds.items():
            for stat, stat_value in stats.items():
                if stat_value['Increase']:
                    current_value = self.thresholds[app][stat]['value']
                    new_value = round(current_value + (current_value * (stat_value['Increase']/100)))
                    self.thresholds[app][stat]['value'] = new_value

    def get_index_process_id(self, app):
        """Finds out the process ID for the specific indexing process app

            Args:
                app     (str)   --      The name of the app. Example IndexServer, LogManager

            Returns:
                (str)      --      The ID of the process

        """

        return self.idx_db.isc_machine.get_process_id('CVODS.exe', app + '%%' + self.idx_db.index_server.instance)

    def fetch_process_ids(self):
        """Gets the process ID for both IndexServer and LogManager processes

            Returns:
                (dict)      --      App process name and it's ID

        """

        time.sleep(300)
        id_index_server = self.get_index_process_id('IndexServer')[0]
        id_log_manager = self.get_index_process_id('LogManager')[0]

        self.log.info(f'***** Process ID: IndexServer [{id_index_server}] *****')
        self.log.info(f'***** Process ID: LogManager [{id_log_manager}] *****')

        if not id_index_server or not id_log_manager:
            raise Exception('Unable to get IndexServer and LogManager process IDs')

        self.process_ids = {
            'IndexServer': id_index_server,
            'LogManager': id_log_manager
        }

    def fetch_stats(self):
        """Fetches the stats for both IndexServer and LogManager processes, logs and returns them

            Returns:
                (dict)      --      App name and it's stats

        """

        self.log.info('Fetching IndexServer process stats')
        index_server_stats = self.idx_db.isc_machine.get_process_stats(self.process_ids['IndexServer'])
        self.print_process_stats(index_server_stats, 'IndexServer')

        self.log.info('Fetching LogManager process stats')
        log_manager_stats = self.idx_db.isc_machine.get_process_stats(self.process_ids['LogManager'])
        self.print_process_stats(log_manager_stats, 'LogManager')

        return {
            'IndexServer': index_server_stats,
            'LogManager': log_manager_stats
        }

    def print_process_stats(self, stats, name):
        """Prints the stats for the given process

            Args:
                stats       (dict)       --      The dictionary of process stats

                name        (str)        --      The name of the process i.e IndexServer, LogManager

        """

        self.log.info(f'Process [{name}] stats at this point')
        for key, val in stats.items():
            self.log.info('    {0:<15}:{1:>15}'.format(key, val))

    def check_threshold(self, app, stats):
        """Validates if the threshold is under limits for the given indexing process and it's stats.

            Args:
                app         (str)       --      The name of the index process app IndexServer, LogManager

                stats       (dict)      --      The dictionary of process stats

            Raises:
                Exception if the stats are not within the threshold and variation percentage.

        """

        thresholds = self.thresholds[app]
        threshold_map = {
            'handle_count': 'HandleCount',
            'thread_count': 'ThreadCount',
            'cpu_usage': 'CPUUsage',
            'memory': 'Memory'
        }

        check_failed = False
        try:
            for stat, threshold_name in threshold_map.items():
                stat_value = stats[stat]
                threshold_value = thresholds[threshold_name]['value']
                accepted_variation = thresholds[threshold_name]['AcceptedVariation']

                self.log.info(f'App [{app}] Stat [{stat}] Value [{stat_value}] Threshold [{threshold_value}] '
                              f'Accepted variation [{accepted_variation}%]')

                if stat_value > threshold_value:
                    actual_variation = abs((stat_value - threshold_value) / threshold_value) * 100

                    if actual_variation < accepted_variation:
                        self.log.info(f' = PASS - Stat [{stat}] is under limits. Variation [{actual_variation:.2f}%]')
                    else:
                        msg = f' = FAIL - Process [{app}] stat [{stat}] has varied ' \
                              f'beyond the the limit. Actual [{actual_variation:.2f}%]'
                        self.log.error(msg)
                        check_failed = True

                        if self.tcinputs.get('ExitOnFail'):
                            raise Exception(msg)
                        else:
                            self.log.info('Continuing as testcase is configured to run on validation failure.')
                            self.validation_failed = True
                else:
                    self.log.info(f' = Stat [{stat}] is below the threshold and under control')
        finally:
            if check_failed:
                self.take_process_dump(app)

    def validate_interrupted_process_stats(self):
        """Validates the stats of the process"""

        stats = self.fetch_stats()
        index_server_stats = stats['IndexServer']
        log_manager_stats = stats['LogManager']

        self.check_threshold('IndexServer', index_server_stats)
        self.check_threshold('LogManager', log_manager_stats)

    def take_process_dump(self, app):
        """Takes the process dump for the given app

            Args:
                app         (str)       --      The name of the index process app IndexServer, LogManager

            Returns:
                None

        """

        attempt = self.attempt + 1
        file_name = f'{app}_{attempt}'
        process_id = self.process_ids[app]

        self.log.info('Taking process dump for [%s] Process ID [%s] Attempt [%s]', app, process_id, attempt)

        try:
            dump_path = self.idx_db.isc_machine.get_process_dump(process_id, file_name=file_name)
            self.log.info('Process dump taken at [%s]', dump_path)
        except Exception as e:
            self.log.error('Unable to take process dump [%s]', e)
