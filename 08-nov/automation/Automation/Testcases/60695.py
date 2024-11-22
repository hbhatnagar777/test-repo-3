# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate index DB inline backup with fulls and synthetic fulls for Subclient level index

TestCase:
    __init__()                         --  Initializes the TestCase class

    setup()                            --  All testcase objects are initializes in this method

    run()                              --  Contains the core testcase logic and it is the one executed

    get_index_checkpoints()            --  Checks for the presence of the index logs

    inline_backup_status()             --  Checks for the presence of the index logs

    verify_latest_checkpoint_restore() -- To verify the restore of latest checkpoint from latest cycle full/sfull

    tear_down()                        -- Disables the inline index backup option at commcell level after the run finishes

"""

import time
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Verify index DB inline backup with fulls and synthetic fulls for subclient level index"""

    def __init__(self):
        """Initializes the TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Indexing - Index DB inline index backup with Fulls and Synthetic fulls"
        self.tcinputs = {
            'StoragePolicy': None,
        }

        self.storage_policy = None
        self.sp_primary_copy = None
        self.idx_help = None
        self.cl_machine = None
        self.idx_tc = None
        self.backupset = None
        self.subclient = None
        self.indexing_level = None
        self.indexing_version = None
        self.inline_idx_bkp_option = None
        self.bkp_jobs = None
        self.backupset_guid = None
        self.subclient_guid = None
        self.full_jobs_list = None
        self.full_jobs_index_afiles_list = None
        self.index_afiles_list = None
        self.index_db_backups_list = None
        self.idx_db = None
        self.inline_idx_bkp_option_flag = 0

    def setup(self):
        """All testcase objects are initializes in this method"""

        self.cl_machine = Machine(self.client)
        storage_policy_name = self.tcinputs.get('StoragePolicy')
        self.log.info("Storage policy is: %s", self.storage_policy)
        self.storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        self.sp_primary_copy = self.storage_policy.get_primary_copy()
        self.idx_help = IndexingHelpers(self.commcell)
        self.idx_tc = IndexingTestcase(self)

        self.log.info("Creating backupset and subclient..")
        self.backupset = self.idx_tc.create_backupset(
            name='60695_inline_idx_bkp',
            for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name="inline_idx_bkp_sc",
            backupset_obj=self.backupset,
            storage_policy=storage_policy_name,
            register_idx=True)

        self.log.info("Subclient content is: %s", self.subclient.content)

        self.log.info('Changing the index retention to 2 cycles')
        self.subclient.index_pruning_type = 'cycles_based'
        self.subclient.index_pruning_cycles_retention = 2

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Check if inline backup setting is enabled
            2 - Run 2 cycles of jobs
            3 - Keep the index server and backup MA different
            4 - Verify that with each Full/SFull, index is checkpointed
            5 - Also verify with Inc and Diff, index is not checkpointed
            6 - Run 2 more cycles of jobs
            7 - Run data aging
            8 - Verify that checkpoints created with the fulls/sfulls of first two cycles are aged

        """
        try:
            # Starting the testcase
            self.log.info("Started executing %s testcase ", self.id)

            # Checking client's Indexing version (v1 or v2)
            self.log.info("Checking client's Indexing version v1 or v2")
            self.indexing_version = self.idx_help.get_agent_indexing_version(
                self.client,
                agent_short_name=None
            )
            self.log.info("Indexing Version is: %s", self.indexing_version)
            if self.indexing_version == 'v1':
                raise Exception("This is V1 client")

            # Checking if it is backupset level index or subclient level index
            self.log.info("Checking if it is backupset level index or subclient level index")
            self.indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
            self.log.info("Agent Index Level is: %s", self.indexing_level)
            if self.indexing_level != 'subclient':
                raise Exception("This is not subclient level Index ")

            self.log.info('Enabling the Inline Index backup option')
            self.commcell._set_gxglobalparam_value(
                request_json={
                    'name': 'BackupIndexWithFull',
                    'value': '1'
                }
            )
            self.inline_idx_bkp_option_flag = 1

            self.full_jobs_list = []
            self.full_jobs_index_afiles_list = []

            self.log.info('************* Running 2 cycles of backup jobs *************')
            self.bkp_jobs = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Differential', 'Edit',
                       'Incremental'])
            sfull_job = self.idx_tc.cv_ops.subclient_backup(
                self.subclient,
                backup_type="Synthetic_full",
                wait=False,
                advanced_options={
                    'use_multi_stream': False
                }
            )

            jm_obj = JobManager(sfull_job, self.commcell)
            jm_obj.wait_for_phase(phase='Synthetic Full Backup', total_attempts=120, check_frequency=1)
            self.log.info('Job is at backup phase, suspending job in [5] seconds')
            time.sleep(5)
            self.log.info('Suspending job')
            sfull_job.pause(wait_for_job_to_pause=True)
            self.log.info('Job suspended')

            self.log.info('Fetching the backup media agent for the synthetic full job: %s', sfull_job.job_id)
            get_backup_ma = f""" 
                        select mediaAgentName from JMBkpJobInfo where jobid = {sfull_job.job_id} 
                        """
            self.csdb.execute(get_backup_ma)
            backup_ma_hostname = self.csdb.fetch_all_rows()[0][0]
            self.log.info('The Backup MA host name is %s', backup_ma_hostname)
            if '.' in backup_ma_hostname:
                backup_ma = backup_ma_hostname.split('.')[0]
            else:
                backup_ma = backup_ma_hostname

            if not backup_ma:
                raise Exception('There are no media agent details for the job: %s', sfull_job.job_id)
            self.log.info('The backup media agent for the synthetic full job is %s', backup_ma)

            self.log.info('Job is suspended, resuming it in [1] minutes')
            time.sleep(60)
            self.log.info('Resuming job')
            sfull_job.resume(wait_for_job_to_resume=True)
            self.log.info('Job resumed')

            self.log.info('Fetching all datapaths MAs of the primary copy of the subclient storage policy')
            get_all_datapath_mas = f"""   
                                select name from app_client where id in (select HostClientId from 
                                MMdatapath where copyid = {self.sp_primary_copy.get_copy_id()})
                                    """
            self.csdb.execute(get_all_datapath_mas)
            datapath_mas = self.csdb.fetch_all_rows()
            if len(datapath_mas) < 2:
                raise Exception('There are no two datapath media agents for the SP copy')
            self.log.info('The list of datapath media agents for the SP copy are %s', datapath_mas)

            self.idx_db = index_db.get(self.subclient)
            is_name = self.idx_db.index_server.name
            self.log.info('Current index server is %s', is_name)
            new_is = None
            if is_name.lower() == backup_ma.lower():
                self.log.info('Index server and backup MA are same, so changing the index server')
                for ma in datapath_mas:
                    if ma[0] != backup_ma:
                        new_is = ma[0]
                new_is_cl = self.commcell.clients.get(new_is)
                self.subclient.index_server = new_is_cl
                self.subclient.refresh()
                self.idx_db = index_db.get(self.subclient)
                new_is_name = self.idx_db.index_server.name
                self.log.info('Index server after change is %s', new_is_name)

            self.log.info("Checking GUIDs for backupset and subclient")

            self.backupset_guid = self.idx_db.backupset_guid
            self.subclient_guid = self.idx_db.db_guid
            self.log.info("Backupset GUID is: %s", self.backupset_guid)
            self.log.info("Subclient GUID is: %s", self.subclient_guid)

            self.log.info("Initial full Backup jobs list: %s", self.full_jobs_list)
            self.log.info("Initial full Backup jobs Index afiles list: %s", self.full_jobs_index_afiles_list)

            for job in self.bkp_jobs:
                self.inline_backup_status(job)

            self.log.info("Final full Backup jobs list: %s", self.full_jobs_list)
            self.log.info("Final full Backup jobs Index afiles list: %s", self.full_jobs_index_afiles_list)

            #Run few more backup jobs job
            self.bkp_jobs.extend(self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['Edit', 'Incremental', 'Synthetic_full', 'Edit', 'Incremental', 'Synthetic_full']))

            #Compact the DB
            self.log.info('Running index backup job to compact the index')
            attempt = 1
            while attempt < 3:
                if self.idx_db.compact_db():
                    self.log.info('Compaction of the index completed successfully')
                    break
                attempt = attempt + 1
            if attempt == 3:
                raise Exception('Failed to compact the DB')

            self.log.info('Perform time range browse from cycles 1 and 2 to restore latest checkpoint')
            self.idx_tc.verify_browse_restore(self.backupset, {
                'operation': 'browse',
                'from_time': self.bkp_jobs[0].start_timestamp,
                'to_time': self.bkp_jobs[3].end_timestamp,
                'show_deleted': True,
                'restore': {
                    'do': True
                }
            })
            self.log.info('Verify restore of latest checkpoint from latest job after browse from old cycles')
            self.verify_latest_checkpoint_restore()

            #Run Data aging job
            self.log.info('Verifying the aging of checkpoints from older cycle jobs')
            self.commcell.run_data_aging('Primary', self.storage_policy.name)
            self.index_afiles_list = self.get_index_checkpoints(self.subclient_guid)

            self.log.info("List of index checkpoints made for the database %s", self.index_afiles_list)

            for afile in self.full_jobs_index_afiles_list:
                if afile in self.index_afiles_list:
                    raise Exception("Index checkpoint not aged")
            self.log.info("All the checkpoints associated with the aged jobs are aged as expected")

            self.log.info("End of the testcase")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def inline_backup_status(self, job):
        """Checks for the presence of the index logs
          Args:
              job    (obj) --  backup job for which we need to check inline index backup

          Returns:
              returns afile id if index backedup inline, else returns 0

          Raises:
              Exception:
                  if failed to check inline index backup status for any given backup job id
          """

        jobid = job.job_id
        self.log.info('Verifying the inline index backup status for job: %s', jobid)
        flag = self.idx_help.verify_checkpoint(jobid, self.subclient_guid)

        if flag:
            self.log.info("DB has been checkpointed by job:%s", jobid)
        else:
            self.log.info(f"DB has not been checkpointed by job:%s", jobid)

        self.csdb.execute(f"""
                   select bkplevel from JMBkpStats where jobid in ({jobid})
                     """)
        backup_job_type = int(self.csdb.fetch_one_row()[0])
        self.log.info('The backup job type is %s', backup_job_type)

        if backup_job_type in (1, 64):
            self.full_jobs_list.append(jobid)
            self.log.info("Current jobs list: %s", self.full_jobs_list)

        flag1 = 1
        if (backup_job_type == 1) or (backup_job_type == 64):
            if flag == 1:
                self.log.info("This is a full/sfull backup job and Index DB has been checkpointed")
            else:
                raise Exception('Index DB not checkpointed with full/sfull job')
        else:
            if flag == 1:
                raise Exception('Index DB checkpointed with non full/sfull job')
            else:
                self.log.info("This is not a full/sfull job and Index DB has not been checkpointed")
                flag1 = 0

        if flag1:
            self.csdb.execute(f"""
                   select id from archfile where jobid={jobid} and name like '%checkpoint%' and 
                   isvalid =1
            """)

            inline_backup_afile = int(self.csdb.fetch_one_row()[0])
            if not inline_backup_afile:
                raise Exception(f'Index backup with backup job: {jobid} has no afiles')
            self.log.info('The inline backup afile is %s', inline_backup_afile)

            self.log.info(f"""Index has been backed up with the given backup job: {jobid} "
                              and index afile id is: {inline_backup_afile} """)
            self.full_jobs_index_afiles_list.append(inline_backup_afile)

    def get_index_checkpoints(self, sc_guid):
        """Checks for the presence of the index logs
          Args:
              sc_guid   (str) --  subclient GUID

          Returns:
              returns list of checkpoint afiles for the given subclient

          Raises:
              Exception:
                  if failed to get the list of checkpoints for the given subclient
          """

        self.csdb.execute(f"""
               select id from archfile where name like '%{sc_guid}'
                 """)
        list_of_checkpoints = self.csdb.fetch_all_rows(named_columns=False)
        if not list_of_checkpoints:
            raise Exception(f'There are no checkpoints for Subclient with guid {sc_guid}')
        self.log.info('List of checkpoints is %s', list_of_checkpoints)

        return list_of_checkpoints

    def verify_latest_checkpoint_restore(self):
        """ To verify the restore of latest checkpoint from latest cycle full/sfull """

        get_latest_checkpoint_afile = (f"""
                     select id from archfile where jobid={self.bkp_jobs[-1].job_id} and name like '%checkpoint%' and 
                    isvalid =1
                         """)

        self.csdb.execute(get_latest_checkpoint_afile)
        checkpoint_afile_id = int(self.csdb.fetch_one_row()[0])
        self.log.info('The afile id of the latest checkpoint that needs to be restored is %s', checkpoint_afile_id)
        get_latest_checkpoint_timestamps = f""" 
                    select * from App_IndexCheckpointInfo where dbname = '{self.idx_db.db_guid}' and 
                    flags = 1 and afileid = {checkpoint_afile_id} order by afileid asc
                    """
        self.csdb.execute(get_latest_checkpoint_timestamps)
        self.log.info('Expected checkpoint to be restored is %s', self.csdb.fetch_all_rows()[0])
        checkpoint_start_time = self.csdb.fetch_all_rows()[0][4]
        checkpoint_end_time = self.csdb.fetch_all_rows()[0][5]
        indexes_list = self.idx_db.isc_machine.get_folders_in_path(folder_path=self.idx_db.backupset_path,
                                                                   recurse=False)
        restored_checkpoint = None
        self.log.info('The indexes in the index cache after checkpoint restore are %s', indexes_list)
        for each_index in indexes_list:
            db_folder_name = each_index.split('\\')[-1]
            if checkpoint_start_time in db_folder_name and checkpoint_end_time in db_folder_name:
                restored_checkpoint = each_index

        if restored_checkpoint:
            self.log.info('The restored checkpoint is at %s', restored_checkpoint)
        else:
            raise Exception('Expected checkpoint not restored')

    def tear_down(self):
        """ To disable the inline index backup option"""
        if self.inline_idx_bkp_option_flag:
            self.log.info('Disabling inline index backup option')
            self.commcell._set_gxglobalparam_value({
                'name': 'BackupIndexWithFull',
                'value': '0'
            })
