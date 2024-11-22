# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that log restore from primary and secondary copy scenario works as expected

TestCase:
    __init__()                      --  Initializes the TestCase class

    setup()                         --  All testcase objects are initializes in this method

    run()                           --  Contains the core testcase logic and it is the one executed

    get_default_ma()                --  Gets the default primary copy MA of storage policy

    restart_mas()                   --  restarts cv services on MA's

    delete_specific_db_logs()       --  deletes index db , logs specified by instruction

    check_by_deleting()             --  deletes db,logs. validates find and restore operations


"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that log restore from primary and secondary copy scenario works as expected

        Steps:
        1) Create backupset and subclient
        2) Run FULL -> INC -> INC -> INC -> INC
        3) Assign a storage policy which has multiple datapaths.
        4) Before every backup switch default datapath.
        3) Delete all index logs
        4) Delete DB, stop/kill indexserver and log manager services.
        5) Do browse and verify if log restore is triggered for all missing jobs and DB is up to date.
        6) Delete alternate index logs
        7) Repeat #5
        8) Delete last few jobs index logs
        9) Repeat #5
        10) Start a new cycle by running SFULL
        11) Repeat #5

        - Verify index logs are restored for all the jobs and DB gets up to date.
        - Verify presence of index logs from index cache.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Indexing - Index logs restore"
        self.tcinputs = {
            'StoragePolicy': None,
        }
        self.storage_policy = None
        self.storage_policy_obj = None
        self.idx_tc = None
        self.cl_machine = None
        self.idx_db = None
        self.primary_copy = None
        self.jobs_ran = []
        self.mas_used = []
        self.idx_help = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)  # Used by IndexingTestcase class

        self.storage_policy = self.tcinputs['StoragePolicy']
        self.storage_policy_obj = self.commcell.storage_policies.get(self.storage_policy)
        self.primary_copy = self.storage_policy_obj.get_primary_copy()

        self.idx_tc = IndexingTestcase(self)

        self.backupset = self.idx_tc.create_backupset(name='index_logs_restore', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='index_logs_restore_sub',
            backupset_obj=self.backupset,
            storage_policy=self.storage_policy
        )
        self.idx_help = IndexingHelpers(self.commcell)

    def run(self):
        """Contains the core testcase logic"""

        self.mas_used.append(self.get_default_ma())

        self.log.info('+++ Using [%s] for Full backup +++', self.mas_used[-1])

        full_job = self.idx_tc.run_backup_sequence(self.subclient, ['New', 'Full'])
        self.jobs_ran.extend(full_job)

        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        self.idx_db = index_db.get(self.subclient if indexing_level == 'subclient' else self.backupset)

        for i in range(3):
            self.idx_tc.rotate_default_data_path(self.primary_copy)
            self.mas_used.append(self.get_default_ma())

            if self.mas_used[-2] == self.mas_used[-1]:
                self.log.error('MA not changed after rotating default data path')
                self.log.error(
                    'Same MA [%s] is used for previous job [%s]',
                    self.mas_used[-1],
                    self.jobs_ran[-1].job_id
                )
                raise Exception('Default MA [%s] remained same after rotating default path', self.mas_used[-1])

            self.log.info('+++ Using [%s] for Incremental [%s] backup +++', self.mas_used[-1], i)
            inc = self.idx_tc.run_backup_sequence(self.subclient, ['Edit', 'Incremental'])

            self.jobs_ran.extend(inc)

        self.log.info('*** Starting Sequential deletion of logs, validation of browse and restore ***')
        self.check_by_deleting('all')
        self.check_by_deleting('alternate')
        self.check_by_deleting('last_few')

        self.idx_tc.rotate_default_data_path(self.primary_copy)
        self.mas_used.append(self.get_default_ma())

        if self.mas_used[-2] == self.mas_used[-1]:
            self.log.error('MA not changed after rotating default data path')
            self.log.error(
                'Same MA [%s] is used for previous job [%s]',
                self.mas_used[-1],
                self.jobs_ran[-1].job_id
            )
            raise Exception(f'Default MA {self.mas_used[-1]} remained same after rotating default path')

        self.log.info('+++ Using [%s] for Synthetic full backup +++', self.mas_used[-1])
        s_full = self.idx_tc.run_backup_sequence(self.subclient, ['Synthetic_full'])
        self.jobs_ran.extend(s_full)

        self.log.info('*** Starting Sequential deletion of logs, validation of browse & restore After SFULL ***')
        self.check_by_deleting('all')
        self.check_by_deleting('alternate')
        self.check_by_deleting('last_few')

    def get_default_ma(self):
        """Gets the default primary copy MA of storage policy

            Returns:
                string      -    Name of the primary copy MA

        """
        self.primary_copy.refresh()
        ma_name = self.primary_copy.media_agent
        self.log.info('Current default MA is [%s]', ma_name)
        return ma_name

    def restart_mas(self):
        """Restarts the services on all ma's used so far"""

        for ma in set(self.mas_used):
            self.log.info('*** Restarting [%s] services****', ma)
            self.commcell.clients.get(ma).restart_services()

    def delete_specific_db_logs(self, instruction='all'):
        """Deletes the Index db and Index logs specified by instruction

            Args:
                instruction     (str)       --  specifies which logs to delete

        """
        self.log.info('*** List of jobs [%s] ***', self.jobs_ran)
        self.log.info('*** Deleting [%s] logs ***', instruction)
        self.idx_db.delete_db()

        if instruction == 'alternate':
            cnt = 0
            for job in self.jobs_ran:
                if cnt % 2 == 0:
                    job_id = 'J' + str(job.job_id)
                    self.idx_db.delete_logs(job_id)
                cnt += 1

        elif instruction == 'last_few':
            cnt = int(len(self.jobs_ran)/2)
            for job in reversed(self.jobs_ran):
                if cnt > 0:
                    job_id = 'J' + str(job.job_id)
                    self.idx_db.delete_logs(job_id)
                    cnt -= 1
                else:
                    break
        else:
            self.idx_db.delete_logs('all')

    def check_by_deleting(self, instruction='all'):
        """ Restarts all mas,
            deletes the logs specified by instruction,
            performs a browse restore validation

            Args:
                instruction     (str)       --  specifies which logs to delete

            Raises:
                  Exception, if browse restore validation failed

        """

        self.delete_specific_db_logs(instruction)

        self.log.info('*** Restarting all MAs to check by deleting [%s] logs ***', instruction)
        self.restart_mas()

        self.log.info('+++ Waiting 60 seconds after deleting the logs +++')
        time.sleep(60)

        self.log.info('*** Validating browse restore after deleting [%s] logs ***', instruction)
        ret_code = self.backupset.idx.validate_browse_restore({
            'operation': 'find',
            'restore': {
                'do': True
            }
        })

        if ret_code != 0:
            raise Exception(f'Validation of find restore Failed for after deleting {instruction} logs')

        self.log.info('*** Validation of find restore was successful after deleting [%s] logs ***', instruction)
