# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate basic features of Indexing like browse, find, versions, synthetic full
and restores

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    run_combinations()          --  Executes the browse/find/restore combinations one by one

    combination_thread()        --  The thread which is spawn to execute every combination.

    generate_combinations()     --  Prepares a list of browse/find/versions/restore combinations

    get_timerange()             --  Gets a random timerange from the backups

    get_versions_file()         --  Gets a random file to do view all versions

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback
import time
import itertools
import random

from queue import Queue
from threading import Thread

from AutomationUtils import constants, commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Browse, find, versions and restore'

        self.tcinputs = {
            'StoragePolicyName': None,
            'TestDataPath': None,
            'RestorePath': None
            # 'Threads': None
        }

        self.backupset = None
        self.subclients = {}

        self.cv_entities = None
        self.cv_ops = None
        self.idx = None
        self.cl_machine = None
        self.cl_delim = None

        self.job_end_times = {}
        self.manual_testdata = {}
        self.combinations_failed = []

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:
            self.client_name = self.tcinputs.get('ClientName')
            self.backupset_name = self.tcinputs.get('Backupset', 'browse_find_restore')
            self.storagepolicy_name = self.tcinputs.get('StoragePolicyName')
            self.subclients_count = int(self.tcinputs.get('SubclientsToCreate', 1))
            self.restore_path = self.tcinputs.get('RestorePath')

            self.cl_machine = Machine(self.client_name, self.commcell)
            self.cl_delim = self.cl_machine.os_sep

            self.idx_tc = IndexingTestcase(self)

            self.backupset = self.idx_tc.create_backupset(self.backupset_name, for_validation=True)

            for i in range(self.subclients_count):
                name = f'subclient_{i}'
                sc_obj = self.idx_tc.create_subclient(
                    name=name,
                    backupset_obj=self.backupset,
                    storage_policy=self.storagepolicy_name
                )

                self.subclients[name] = sc_obj
                self.job_end_times[name] = []
                self.manual_testdata[name] = {}

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            backup_cycle = self.tcinputs.get('BackupCycle', 'NEW; FULL; EDIT; INC; EDIT; SYNTHETIC_FULL')
            backup_cycle = backup_cycle.split(';')
            backup_cycle = [step.strip() for step in backup_cycle]

            for sc_name in self.subclients:
                self.log.info('Running backups [{0}] for subclient {1}'.format(backup_cycle, sc_name))
                sc_obj = self.subclients[sc_name]
                jobs = self.idx_tc.run_backup_sequence(sc_obj, steps=backup_cycle)

                if not jobs:
                    raise Exception('No backups ran for the subclient')

                for job in jobs:
                    end_timestamp = commonutils.convert_to_timestamp(job.end_time)
                    self.job_end_times[sc_name].append(end_timestamp)

            self.log.info('Running browse/find/version combinations')
            self.run_combination()

            if self.combinations_failed:
                self.log.error('Some combinations of browse, find, versions and restore failed')
                self.log.error(self.combinations_failed)
                self.log.error('Setting testcase as failed')
                self.status = constants.FAILED
            else:
                self.log.info('All combinations of browse, find, versions and restore passed')
                self.log.info('Test case passed')
                self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Test case failed with error')
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def combination_thread(self, queue):
        """The thread which is spawn to execute every combination"""

        while True:
            combination = queue.get()

            random_sleep = random.randint(5, 30)
            self.log.info('Running next combination test in [{0}] seconds'.format(random_sleep))
            time.sleep(random_sleep)

            # Extracting to variables - [id, levels, operations, types, show_deleted, restore, filters]
            id = combination[0]
            level = combination[1]
            op_type = combination[2]
            op_range = combination[3]
            show_deleted = combination[4]
            restore = combination[5]
            filters = combination[6]

            self.log.info('Executing combination #{0} - {1}'.format(id, combination))

            the_subclient = None
            the_subclient_obj = None
            versions_check_file = None
            from_time = 0
            to_time = 0

            options = dict()
            options['restore'] = dict()
            options['operation'] = op_type
            options['show_deleted'] = show_deleted

            # LEVEL of browse
            if level == 'subclient':
                sc_list = list(self.subclients.keys())
                the_subclient = random.choice(sc_list)
                the_subclient_obj = self.subclients[the_subclient]
                options['subclient'] = the_subclient
            else:
                options['subclient'] = None

            # FROM, TO time
            from_time, to_time = self.get_timerange(op_range, the_subclient)
            options['from_time'] = from_time
            options['to_time'] = to_time

            # OPERATION type
            if op_type == 'browse':
                options['path'] = self.cl_delim

            elif op_type == 'find':
                options['path'] = '|**|*'.replace('|', self.cl_delim)

            elif op_type == 'versions':
                versions_check_file = self.get_versions_file(the_subclient, from_time, to_time)
                options['path'] = versions_check_file

            # FILTERS
            if filters:
                filter_name = random.choice(['*.txt', 'e*'])
                options['filters'] = [('FileName', filter_name)]
                options['compute_folder_size'] = True

            # RESTORE options
            if restore:
                options['restore']['do'] = True
                options['restore']['dest_path'] = self.restore_path

                if op_type == 'browse' and level == 'subclient':
                    options['restore']['source_items'] = the_subclient_obj.content

                if op_type == 'versions':
                    options['restore']['source_items'] = [versions_check_file]
                    options['restore']['select_version'] = 'all'

            ret_code = self.backupset.idx.validate_browse_restore(options)

            if ret_code == -1:
                self.combinations_failed.append(id)
                self.log.info('Adding to failed list')
                self.log.error('Combination finished. Result [FAILED] - #{0}\n'.format(id))
            else:
                self.log.info('Combination finished. Result [PASSED] - #{0}\n'.format(id))

            queue.task_done()

    def run_combination(self):
        """Executes the browse/find/restore combinations one by one"""

        try:
            self.log.info('Generating combinations')
            combinations = self.generate_combinations()
            for combination in combinations:
                self.log.info(combination)

            self.log.info('Creating threads')

            q = Queue()
            num_threads = int(self.tcinputs.get('Threads', 5))

            for i in range(num_threads):
                worker = Thread(target=self.combination_thread, args=(q,))
                worker.setDaemon(True)
                worker.start()

            for combination in combinations:
                q.put(combination)

            q.join()

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    @staticmethod
    def generate_combinations():
        """Prepares a list of browse/find/versions/restore combinations"""

        levels = ['backupset', 'subclient']
        operations = ['browse', 'find', 'versions']
        types = ['latest', 'timerange', 'point_in_time']
        show_deleted = [True, False]
        restore = [True]
        filters = [None]

        combinations = itertools.product(levels, operations, types, show_deleted, restore, filters)
        comb_list = list(combinations)

        # Adding manual list to the combination to include filters
        comb_list.append(['backupset', 'browse', 'timerange', True, True, True])
        comb_list.append(['subclient', 'browse', 'latest', True, True, True])
        comb_list.append(['subclient', 'find', 'latest', True, True, True])
        comb_list.append(['backupset', 'browse', 'latest', False, True, True])
        comb_list.append(['backupset', 'find', 'latest', True, True, True])

        comb_list_count = len(comb_list)
        combs = []

        # Appending ID to every combination
        for i in range(comb_list_count):
            comb = list(comb_list[i])
            comb.insert(0, i+1)
            combs.append(comb)

        return combs

    def get_timerange(self, type, subclient=None):
        """Gets a random timerange from the backups"""

        # Get all the timestamps from all the subclients, else from particular subclient
        if subclient is None:
            all_times = self.job_end_times.values()
            timestamps = list(itertools.chain.from_iterable(all_times))
        else:
            timestamps = self.job_end_times[subclient]

        timestamps = [commonutils.get_int(t) for t in timestamps]

        if len(timestamps) == 0:
            raise Exception('No backup jobs seems to have run because timestamps list is empty')

        t_count = len(timestamps)
        timestamps.sort()

        if type == 'timerange':
            etime_idx = random.randint(0, t_count-1)

            # If got the first item, then generate a dummy start time 1hr behind
            if etime_idx == 0:
                return timestamps[etime_idx]-3600, timestamps[etime_idx]

            # Get a start time index lesser than the end time index
            stime_idx = random.randint(0, etime_idx-1)

            # Adding 5 secs to from time because, we save job endtime in validation DB and taking
            # jobendtime as it is in timerange will cause problem since validation will
            # include that job but Indexing will not include the job

            return timestamps[stime_idx]+10, timestamps[etime_idx]

        if type == 'point_in_time':
            etime_idx = random.randint(0, t_count - 1)
            return 0, timestamps[etime_idx]

        if type == 'latest':
            return 0, 0

    def get_versions_file(self, subclient=None, from_time=0, to_time=0):
        """Gets a random file to do view all versions"""

        if to_time == 0:
            to_time = int(time.time())

        query = ("select path from indexing where jobendtime between {0} and {1} {2} and "
                 "type = 'file' and status in ('modified', 'new') and name like '%.txt' "
                 "order by jobid desc limit 1")

        sc_query = " and subclient = '{0}'".format(subclient) if subclient is not None else ''
        query = query.format(from_time, to_time, sc_query)

        response = self.backupset.idx.db.execute(query)

        random_file = ''
        if response.rowcount != 0:
            random_file = response.rows[0][0]

        return random_file

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        if self.status == constants.PASSED:
            self.backupset.idx.cleanup()
