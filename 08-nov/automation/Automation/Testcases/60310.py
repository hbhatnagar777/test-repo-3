# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

This Testcase verifies that single stream synthetic full backup job is unsuccessful when chunks are missing and once
the missing chunks are retrieved, upon running a synthetic full again, the job finishes successfully.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    pick_local_chunk_file()                     --  To get the local file path of a random chunk associated with
                                                    a given job id

    chunk_path_conversion_to_unc()              --  To convert the local file path to UNC and change the chunk file
    permissions

"""

import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase

from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """This Testcase verifies that single stream synthetic full backup job is unsuccessful when chunks are missing and
    once the missing chunks are retrieved, upon running a synthetic full again, the job finishes successfully.

        Steps:
             1) Create backupset and subclient
             2) Create testdata and run FULL -> INC -> INC -> INC
             3) Identify a couple of chunks from a couple of these jobs.
             4) Rename/move the chunks somewhere else in the media.
             5) Run single stream SFULL
             6) SFULL should go pending/waiting state with correct JPR and should not complete.
             7) Restore the chunks back to normal.
             8) Run another SFULL and it should complete successful

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Chunk missing'
        self.tcinputs = {
            'StoragePolicy': None,
            'TestDataPath': None,
            'MediaAgentName': None,
            'UNCUserName': None,
            'UNCPassword': None,
        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_tc = None
        self.ma_machine = None

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_chunk_missing', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )
        self.ma_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""

        expected_jpr = self.tcinputs.get('ErrorJPRString', 'Error occurred in Disk Media')
        expected_second_jpr = self.tcinputs.get('ErrorJPRStringType2', 'Failed to open or read')

        jobs = self.idx_tc.run_backup_sequence(
            subclient_obj=self.subclient,
            steps=['New', 'Full', 'Edit', 'Incremental', 'Edit', 'Incremental'],
            verify_backup=True
        )

        if 'unix' in self.ma_machine.os_info.lower():
            path_chunk1 = self.pick_local_chunk_file_path(jobs[0])
            path_chunk2 = self.pick_local_chunk_file_path(jobs[1])

        elif 'windows' in self.ma_machine.os_info.lower():
            local_path_chunk1 = self.pick_local_chunk_file_path(jobs[0])
            local_path_chunk2 = self.pick_local_chunk_file_path(jobs[1])
            path_chunk1 = self.chunk_path_conversion_to_unc(local_path_chunk1)
            path_chunk2 = self.chunk_path_conversion_to_unc(local_path_chunk2)
            self.log.info(
                'Authentication for accessing network will be done using username: %s and password: %s',
                self.tcinputs['UNCUserName'],
                self.tcinputs['UNCPassword']
            )
            self.cl_machine.list_shares_on_network_path(
                f'\\\\{self.ma_machine.ip_address}', self.tcinputs['UNCUserName'], self.tcinputs['UNCPassword'])
        else:
            raise Exception('Failed to get chunk path - OS not identified')

        path_chunk1_new = path_chunk1 + 'new'
        path_chunk2_new = path_chunk2 + 'new'

        self.ma_machine.rename_file_or_folder(path_chunk1, path_chunk1_new)
        self.ma_machine.rename_file_or_folder(path_chunk2, path_chunk2_new)

        ss_syn_job = self.idx_tc.cv_ops.subclient_backup(
            self.subclient,
            backup_type='Synthetic_full',
            wait=False
        )

        jm_obj = JobManager(ss_syn_job, self.commcell)
        time.sleep(60)

        jm_obj.wait_for_state(expected_state='waiting', retry_interval=60)
        time.sleep(30)

        self.log.info('Job JPR [%s]', ss_syn_job.delay_reason)
        if expected_jpr in ss_syn_job.delay_reason or expected_second_jpr in ss_syn_job.delay_reason:
            self.log.info('JPR Verified')
        else:
            raise Exception('Job in waiting state due to a different JPR')

        ss_syn_job.pause(wait_for_job_to_pause=True)
        self.ma_machine.rename_file_or_folder(path_chunk1_new, path_chunk1)
        self.ma_machine.rename_file_or_folder(path_chunk2_new, path_chunk2)
        ss_syn_job.resume(wait_for_job_to_resume=True)

        jm_obj.wait_for_state(expected_state='completed', retry_interval=60)
        self.subclient.idx.record_job(ss_syn_job)

        self.idx_tc.verify_job_find_results(ss_syn_job, self.subclient.idx, restore=True)
        self.idx_tc.verify_synthetic_full_job(ss_syn_job, self.subclient)

    def pick_local_chunk_file_path(self, job_obj):
        """To get the file path of a random chunk associated with a given job id

               Args:
                   job_obj (obj) -- chunk that we pick up will belong to this job.

        """

        self.log.info('Finding the chunk for the job with job id: %s', job_obj.job_id)
        query_chunk_id = f"""
            select AC.volumeid, ACM.archchunkid from archchunk AC join archchunkmapping ACM on AC.id = ACM.archChunkid 
            where ACM.archfileid in (select top 1 id from archfile where jobid = '{job_obj.job_id}' and fileType= 1)
        """

        self.csdb.execute(query_chunk_id)
        volume_id, chunk_file_id = self.csdb.fetch_all_rows()[0]

        self.log.info('The volume id and chunk id are %s, %s respectively', volume_id, chunk_file_id)

        query_mount_path = f"""
                select top 1 MMV.volumename, MMV.volumeid, MMDC.folder, MNTPATH.MountPathName, CL.name
                from MMMountpath MNTPATH, MMDeviceController MMDC, MMMountPathToStorageDevice MMPS, MMVOLUME MMV , 
                App_Client CL where MMPS.MountPathId = MMV.CurrMountPathId and 
                MNTPATH.MountPathId = MMV.CurrMountPathId and CL.id = MMDC.clientid 
                 and MMDC.deviceid = MMPS.DeviceId and MMV.volumeid = '{volume_id}'
                """

        self.csdb.execute(query_mount_path)
        mount_path = self.csdb.fetch_all_rows()[0]
        self.log.info(mount_path)

        chunk_path_local = self.ma_machine.join_path(
            mount_path[2], mount_path[3], 'CV_MAGNETIC', mount_path[0], 'CHUNK_'+chunk_file_id
        )

        self.log.info('Path of the random chunk picked is %s', chunk_path_local)

        return chunk_path_local

    def chunk_path_conversion_to_unc(self, chunk_path_local):
        """To convert the local file path to UNC and change the chunk file permissions

              Args:
                   chunk_path_local (str) -- local file path of the chunk that we picked up

        """
        self.ma_machine.windows_operation(
            user='Everyone',
            path=chunk_path_local,
            action='Allow',
            modify_acl=True,
            inheritance='2',
            permission='FullControl'
        )

        chunk_path_unc = f'\\\\{self.ma_machine.ip_address}\\'+chunk_path_local.replace(':', '$')
        self.log.info('UNC path of the chunk file is %s', chunk_path_unc)

        return chunk_path_unc
