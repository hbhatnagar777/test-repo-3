# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies the restore of backup with copy precedence set during browse and restore.

TestCase:
    __init__()                      --  Initializes the TestCase class

    setup()                         --  All testcase objects are initializes in this method

    run()                           --  Contains the core testcase logic and it is the one executed

    prepare_storage_policy_info()   -- finds the name of secondary copy, default MA's of primary and secondary copies

    restart_mas()                   -- restarts cv services of default MA's of primary, secondary copies

    check_for_index_db_logs()       -- checks for presence of index db , index logs in given ma

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies the restore of backup with copy precedence set during browse and restore.

        Steps:
            1. Create backupset/subclient
            2. Assign a storage policy which has multiple copies (each copy with different MA)
            3. Run FULL, INC1, S FULL
            4. Run aux copy job
            5. Run INC2
            (Right now jobs FULL, INC1, S FULL are present in both primary and 2nd copy and INC2 only in primary copy)
            6. Delete the Index db, logs for this backupset from the index cache in IndexServer MA.
            7. Do browse from the secondary copy (i.e with copy precedence set)
            8. Verify if browse request went to the secondary copy MA  and was served from secondary copy MA and
            not from index server MA
            a. from cs browse log
            b. Presence of the index db, logs in 2nd copy ma’s index cache and not in index server ma’s index cache.
            9. Stop services on IndexServer MA
            10. Do restore from 2nd copy and confirm if data is restored and correct as expected (I.e data till SFULL)

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Copy precedence browse and log restore cases'
        self.cl_machine = None
        self.storage_policy = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None

        self.tcinputs = {
            'StoragePolicy': None,
            # Optional 'WaitForLogsDelete': None,
        }

        self.ma1 = None
        self.ma2 = None
        self.secondary_copy = None
        self.secondary_copy_precedence = None
        self.primary_copy_precedence = None

    def setup(self):
        """All testcase objects are initialized in this method"""
        self.storage_policy = self.tcinputs['StoragePolicy']

        self.cl_machine = Machine(self.client)
        self.prepare_storage_policy_info()
        self.idx_tc = IndexingTestcase(self)

        self.backupset = self.idx_tc.create_backupset(name='copy_precedence_auto', for_validation=True)
        self.subclient = self.idx_tc.create_subclient(
            name='copy_precedence_auto_sub',
            backupset_obj=self.backupset,
            storage_policy=self.storage_policy
        )

        self.idx_help = IndexingHelpers(self.commcell)

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.run_backup_sequence(self.subclient, ['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full'])
        self.idx_tc.cv_ops.aux_copy(
            storage_policy=self.storage_policy,
            sp_copy=self.secondary_copy,
            media_agent=self.ma1.name
        )
        self.backupset.idx.do_after_aux_copy(self.storage_policy, self.secondary_copy_precedence)
        self.idx_tc.run_backup_sequence(self.subclient, ['Edit', 'Incremental', 'Edit', 'Incremental'])

        wait_for_logs_delete = self.tcinputs.get('WaitForLogsDelete', 180)
        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        self.idx_db = index_db.get(self.subclient if indexing_level == 'subclient' else self.backupset)

        self.log.info('*** VALIDATION - 1 (from copy precedence 0) ***')
        self.restart_mas()
        self.idx_db.delete_db()
        self.idx_db.delete_logs()
        self.log.info('+++ Waiting %s seconds after deleting the logs +++', str(wait_for_logs_delete))
        time.sleep(wait_for_logs_delete)

        self.log.info('*** Validating browse from copy precedence 0 ***')

        ret_code = self.backupset.idx.validate_browse_restore({
            'operation': 'find',
            'copy_precedence': 0,
            'restore': {
                'do': True
            }
        })
        if ret_code != 0:
            raise Exception('Browse restore Validation Failed with copy precedence 0')
        self.log.info('Browse Restore validation was successful with copy precedence 0')

        if not self.idx_db.db_exists:
            raise Exception('Browse was successful, but index is not present in primary copy MA')
        self.log.info('*** Index restored after req went to primary copy ma ***')

        self.log.info('*** VALIDATION - 2 (from copy precedence [%s]) ***', self.primary_copy_precedence)
        self.restart_mas()
        self.idx_db.delete_db()
        self.idx_db.delete_logs()
        self.log.info('+++ Waiting %s seconds after deleting the logs +++', str(wait_for_logs_delete))
        time.sleep(wait_for_logs_delete)

        self.log.info('*** Validating browse from primary copy - precedence [%s] ***', self.primary_copy_precedence)
        ret_code = self.backupset.idx.validate_browse_restore({
            'operation': 'find',
            'copy_precedence': self.primary_copy_precedence,
            'restore': {
                'do': True,
            }
        })

        if ret_code != 0:
            raise Exception('Browse restore Validation Failed with copy precedence [%s]', self.primary_copy_precedence)
        self.log.info('Browse, restore validated with copy precedence [%s]', self.primary_copy_precedence)

        if not self.idx_db.db_exists:
            raise Exception('Browse was successful, but index is not present in primary copy MA')
        self.log.info('*** Index restored after req went to primary copy ma ***')

        self.log.info('*** VALIDATION - 3 (from copy precedence [%s]) ***', self.secondary_copy_precedence)
        self.restart_mas()
        self.idx_db.delete_db()
        self.idx_db.delete_logs()
        self.log.info('+++ Waiting %s seconds after deleting the logs+++',str(wait_for_logs_delete))
        time.sleep(wait_for_logs_delete)

        self.log.info(
            '*** Validating browse restore from secondary copy - precedence = [%s] ***',
            self.secondary_copy_precedence
        )

        ret_code = self.backupset.idx.validate_browse_restore({
            'operation': 'find',
            'copy_precedence': self.secondary_copy_precedence,
            'restore': {
                'do': True,
            }
        })
        if ret_code != 0:
            raise Exception(f'Browse restore Validation Failed with copy precedence {self.secondary_copy_precedence}')
        self.log.info(f'Browse Restore validation was successful with copy precedence {self.secondary_copy_precedence}')

        if self.idx_db.db_exists:
            raise Exception(f'Index restored on primary copy ma,but browse copy precedence is set to secondary copy')

        if not self.check_for_index_db_logs(self.ma2):
            raise Exception('Index not present on secondary copy ma - req is not served by secondary copy ma')

        self.log.info('Index not restored on primary copy ma, request went to second copy')
        self.log.info('Index restored on secondary copy ma')
        self.log.info('Testcase ran successfully')

    def prepare_storage_policy_info(self):
        """Uses storage policy properties to find primary and secondary MAs and their copy precedence"""

        sp_obj = self.commcell.storage_policies.get(self.storage_policy)
        primary_copy = sp_obj.get_primary_copy()
        ma1_name = primary_copy.media_agent
        self.primary_copy_precedence = primary_copy.copy_precedence

        secondary_copies = sp_obj.get_secondary_copies()
        if not secondary_copies:
            raise Exception('There are no secondary copies in this storage policy')

        secondary_copy = secondary_copies[0]  # Pick the first secondary copy MA for this testcase
        ma2_name = secondary_copy.media_agent
        self.secondary_copy = secondary_copy.copy_name
        self.secondary_copy_precedence = secondary_copy.copy_precedence

        self.ma1 = self.commcell.clients.get(ma1_name)
        self.ma2 = self.commcell.clients.get(ma2_name)

        self.log.info('=> Primary copy MA [%s] - Precedence [%s]', ma1_name, self.primary_copy_precedence)
        self.log.info('=> Secondary copy MA [%s] - Precedence [%s]', ma2_name, self.secondary_copy_precedence)

    def restart_mas(self):
        """Uses ma1 , ma2 client objects to restart services"""

        self.log.info('*** Restarting ma1 - [%s] services ***', self.ma1.name)
        self.ma1.restart_services()
        self.log.info('*** Restarting ma2 - [%s] services ***', self.ma2.name)
        self.ma2.restart_services()

        self.log.info('=> Current IndexServer [%s]', self.idx_db.index_server.client_name)

    def check_for_index_db_logs(self, ma_client):
        """Checks if index db and logs are present on given MA

            Args:
                ma_client       (obj)   --      pySDK client object

            Returns:
                boolean -   True if backupset Index logs or db present in given MA else False

        """

        ma_machine = Machine(ma_client)
        index_path = self.commcell.media_agents.get(ma_client.name).index_cache_path
        logs_path = ma_machine.join_path(index_path, 'CvIdxLogs', '2', self.backupset.guid)
        db_path = ma_machine.join_path(index_path, 'CvIdxDB', self.backupset.guid)
        self.log.info('DB Path [%s]', db_path)
        self.log.info('Logs Path [%s]', logs_path)
        return ma_machine.check_directory_exists(logs_path) or ma_machine.check_directory_exists(db_path)
