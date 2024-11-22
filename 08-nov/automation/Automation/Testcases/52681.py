# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies the feature of backing up Index DBs using the new Index backup storage policy clients.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    run_data_aging()            --  Enables data aging on the client and runs data aging job on the commcell

    age_cycle_delete_jobs()     --  Changes storage policy retention and marks jobs are aged in the Index validation DB

"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import commonutils

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies the feature of backing up Index DBs using the new Index backup storage policy clients.

        Steps:
            1. Create 2 subclients with 2 different storage policies
            2. Run 2 cycles of backup for both
            3. Verification 1 - Start index checkpoint for both the storage policies
            4. Verify if DB has been checkpointed by both the storage policy clients
            5. Run 1 cycle of backup for both subclients
            5. Verification 2 - Retain 2 cycles and age the remaining cycles + randomly pick and delete one job
            from 2nd cycle for both the subclient storage policies.
            6. Run data aging
            7. Run compaction
            8. Verify if compaction has removed the aged afile.
            9. Verify timerange browse of latest 2 cycles, latest cycle, job based browse and restore.
            10. Run 1 cycle for backup for both subclients
            11. Verification 3 - Delete DB and restart index server services.
            12. Initiate index checkpoint restore and verify DB has been restored.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Backupset level index – Index checkpoint and compaction'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy1': None,
            'StoragePolicy2': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

        self.checkpoint_registry_keys = {
            'CHKPOINT_ITEMS_ADDED_MIN': 100,
            'CHKPOINT_MIN_DAYS': 0
        }

        self.compaction_registry_keys = {
            'CHKPOINT_AFILES_AGED_MIN': 1,
            'COMPACTION_ENFORCE_DAYS': 0,
            'FULL_COMPACTION_MIN_PERCENT_AFILE_AGED': 0
        }

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        if self.indexing_level != 'backupset':
            raise Exception('Client is not at backupset level')

        self.backupset = self.idx_tc.create_backupset('checkpoint_compaction_auto', for_validation=True)

        self.subclient1 = self.idx_tc.create_subclient(
            name='sc1_52681',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy1')
        )

        self.subclient2 = self.idx_tc.create_subclient(
            name='sc2_52681',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy2')
        )

    def run(self):
        """Contains the core testcase logic"""
        try:

            jobs = []

            self.log.info('***** Running cycle 1 and 2 of backup *****')
            self.log.info('***** Subclient 1 *****')
            jobs.extend(self.idx_tc.run_backup_sequence(
                self.subclient1,
                ['new', 'full', 'edit', 'incremental', 'synthetic_full', 'edit', 'incremental'],
                verify_backup=True
            ))

            self.log.info('***** Subclient 2 *****')
            jobs.extend(self.idx_tc.run_backup_sequence(
                self.subclient2,
                ['new', 'full', 'edit', 'incremental', 'synthetic_full', 'edit', 'incremental'],
                verify_backup=True
            ))

            self.idx_db = index_db.get(self.backupset)

            self.log.info('***** VERIFICATION 1 - Checkpoint of DB *****')
            if not self.idx_db.checkpoint_db(registry_keys=self.checkpoint_registry_keys):
                raise Exception('One or more index backup failed/verification failed')

            self.log.info('***** VERIFICATION 1 - CHECKPOINT - PASSED *****')

            self.log.info('***** Running cycle 3 of backup *****')

            self.log.info('***** Subclient 1 *****')
            jobs.extend(self.idx_tc.run_backup_sequence(
                self.subclient1,
                ['synthetic_full', 'edit', 'incremental']
            ))

            self.log.info('***** Subclient 2 *****')
            jobs.extend(self.idx_tc.run_backup_sequence(
                self.subclient2,
                ['synthetic_full', 'edit', 'incremental']
            ))

            self.log.info('***** VERIFICATION 2 - Compaction of DB *****')

            self.log.info('Reading archive file table before compaction in Index')
            afile_table = self.idx_db.get_table(table='archiveFileTable')
            afiles_before = afile_table.get_column('AfileNumber')
            self.log.info('Afiles before compaction [%s]', afiles_before)

            self.age_cycle_delete_jobs(cycles_to_retain=2, job_cycle_delete=2)

            self.idx_db.compact_db(registry_keys=self.compaction_registry_keys)

            self.log.info('Reading archive file table after compaction in Index')
            afile_table.refresh()
            afiles_after = afile_table.get_column('AfileNumber')
            self.log.info('Afiles after compaction [%s]', afiles_after)

            if afiles_before == afiles_after:
                raise Exception('Afiles are not removed from the Index after compaction operation')

            self.log.info('Afiles are aged in the index')

            self.log.info('***** Latest cycle browse *****')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient1.subclient_name,
                'operation': 'find',
                'path': "/**/*",
                'from_time': 0,
                'to_time': 0,
                'show_deleted': True,
                'restore': {'do': True}
            })

            self.log.info('***** Timerange browse of 1st and 2nd cycle *****')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient2.subclient_name,
                'operation': 'find',
                'path': "/**/*",
                'from_time': commonutils.convert_to_timestamp(jobs[0].start_time),  # SC 1 - First cycle, first job
                'to_time': commonutils.convert_to_timestamp(jobs[7].end_time),  # SC 2 - Second cycle, last job
                'show_deleted': True,
                'restore': {'do': True}
            })

            self.log.info('***** Job based browse [%s] *****', jobs[2].job_id)
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'browse',
                'path': "/",
                'job_id': jobs[2].job_id,  # SC 1 - Second cycle, first job
                'show_deleted': True,
                'restore': {'do': True}
            })

            self.log.info('***** Running cycle 4 of backup *****')
            self.log.info('***** Subclient 1 *****')
            jobs.extend(self.idx_tc.run_backup_sequence(self.subclient1, ['synthetic_full'], verify_backup=True))

            self.log.info('***** Subclient 2 *****')
            jobs.extend(self.idx_tc.run_backup_sequence(self.subclient2, ['synthetic_full'], verify_backup=True))

            self.log.info('***** VERIFICATION 2 - COMPACTION - PASSED *****')

            self.log.info('***** VERIFICATION 3 - RESTORE OF CHECKPOINT *****')

            old_creation_id = self.idx_db.get_db_info_prop('creationId')
            self.log.info('Creation ID [%s] - Before', old_creation_id)

            self.log.info('Deleting the DB [%s]', self.idx_db.db_path)
            self.idx_db.delete_db()

            try:
                self.log.info('Restarting Index Server [%s] services', self.idx_db.index_server.client_name)
                self.idx_db.index_server.restart_services(wait_for_service_restart=True)
                self.log.info('Restarted services')
                time.sleep(120)
            except Exception as e:
                self.log.error('Cannot restart services successfully [%s]', e)

            if self.idx_db.db_exists:
                raise Exception('Index DB exists even before doing checkpoint restore')

            self.log.info('Triggering index checkpoint restore')
            if not self.idx_db.is_upto_date:
                self.log.error('Index is not yet up to date')

            self.log.info('Index is up to date')
            time.sleep(30)

            new_creation_id = self.idx_db.get_db_info_prop('creationId')
            self.log.info('Creation ID [%s] - After checkpoint restore', new_creation_id)

            if old_creation_id != new_creation_id:
                raise Exception('Index checkpoint was not restored')

            self.log.info('***** VERIFICATION 3 - CHECKPOINT RESTORE - PASSED *****')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def run_data_aging(self):
        """Enables data aging on the client and runs data aging job on the commcell"""

        try:
            self.log.info('Enabling data aging on the client')
            self.client.enable_data_aging()
        except Exception as e:
            self.log.error('Issue with enabling data aging on the client [%s]', e)

        try:
            self.idx_tc.cv_ops.data_aging()
        except Exception as e:
            self.log.error('Data aging job did not complete as expected [%s]', e)

        self.log.info('***** Waiting for 60 seconds for data aging to send age request to IndexServer *****')
        time.sleep(60)

    def age_cycle_delete_jobs(self, cycles_to_retain=1, job_cycle_delete=2):
        """Changes storage policy retention and marks jobs are aged in the Index validation DB

            Args:
                cycles_to_retain    (int)   --      The number of cycles to retain in the storage policy

                job_cycle_delete    (int)   --      The cycle to delete an INC job from

            Returns:
                None

        """

        default_data = []
        subclients = [self.subclient1, self.subclient2]

        try:
            for subclient in subclients:
                self.log.info(
                    '********* AGING OLDEST CYCLE JOBS - SUBCLIENT [%s] - SP [%s] **********',
                    subclient.subclient_name,
                    subclient.storage_policy
                )

                self.csdb.execute(
                    f"""select retentionDays, fullCycles from archAgingRule where 
                    copyid = ( select defaultCopy from archGroup where name = '{subclient.storage_policy}' )"""
                )

                rows = self.csdb.fetch_all_rows()

                if not rows or not rows[0]:
                    self.log.error(rows)
                    raise Exception('Failed to get storage policy retention configuration')

                default_days = rows[0][0]
                default_cycles = rows[0][1]
                default_data.append({
                    'storage_policy': subclient.storage_policy,
                    'days': default_days,
                    'cycles': default_cycles
                })

                self.log.info('Default retention settings [%s days %s cycles]', default_days, default_cycles)
                self.log.info('Changing retention of the primary copy')

                self.idx_tc.options_help.update_commserve_db(
                    f"""update archAgingRule set retentionDays = '0', fullCycles = '{cycles_to_retain}' where 
                    copyid = ( select defaultCopy from archGroup where name = '{subclient.storage_policy}' )"""
                )

                self.log.info('***** Marking cycles are aged in validation DB *****')
                self.backupset.idx.do_age_jobs_storage_policy(
                    subclient.storage_policy,
                    copy=1,
                    retain_cycles=cycles_to_retain
                )

                self.log.info(
                    '********** AGING SINGLE JOB FROM CYCLE [%s] - SUBCLIENT [%s] **********',
                    job_cycle_delete,
                    subclient.subclient_name
                )

                self.csdb.execute(f"""select top 1 jobid from jmbkpstats 
                where appid = '{subclient.subclient_id}' and fullCycleNum = '{job_cycle_delete}' and bkpLevel = 2 
                order by jobId desc""")

                rows = self.csdb.fetch_all_rows()

                if not rows or not rows[0]:
                    self.log.error(rows)
                    raise Exception(f'Failed to get a job to age in cycle [{job_cycle_delete}]')

                manual_age_job = rows[0][0]
                self.log.info(f'Manually deleting the job [{manual_age_job}]')
                storage_policy_obj = self.commcell.storage_policies.get(subclient.storage_policy)
                sp_copy = storage_policy_obj.get_copy('primary')
                sp_copy.delete_job(manual_age_job)

                self.log.info(f'***** Marking job [{manual_age_job}] aged in the validation DB *****')
                self.backupset.idx.do_age_jobs([manual_age_job])

            self.run_data_aging()

        finally:
            for sp in default_data:
                try:
                    self.log.info('Resetting defaults for [%s]', sp)
                    self.idx_tc.options_help.update_commserve_db(
                        f"""update archAgingRule set retentionDays = '{sp["days"]}', fullCycles = '{sp["cycles"]}' 
                        where copyid = ( select defaultCopy from archGroup where name = '{sp["storage_policy"]}' )"""
                    )
                except Exception as e:
                    self.log.error('Exception while resetting storage policy retention defaults [%s]', e)
