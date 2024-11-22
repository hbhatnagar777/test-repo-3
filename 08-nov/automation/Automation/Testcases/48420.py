# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This test verifies acceptance testcase for the list media feature.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    run_backup()                --  Runs backup with start new media option set and records the media used by the job

    verify_list_media()         --  Verifies the list media results

    get_media_job()             --  Queries the actual media used by the job

    media_name()                --  Prepares an internal name for the media using subclient ID and CV media ID

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This test verifies acceptance testcase for the list media feature.

        Steps:
            1) Assign a storage policy with tape media to a subclient
            2) Run FULL, INC
            3) Make a note of the tape media used by these jobs
            4) Do list media for the subclient.
            5) Verify if list media returns media of FULL and INC.
            6) Run index checkpoint and checkpoint the index DB
            7) Make a note of the media used for the checkpoint job
            8) Verify if list media returns the media of FULL, INC, checkpoint job
            9) Run INC2
            10) Verify if list media returns the media of FULL, INC, checkpoint job, INC2

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - List Media'

        self.tcinputs = {
            'StoragePolicy': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None
        self.media = {}
        self.media_index = []
        self.isc_subclient = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('list_media_auto', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_list_media',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        # Assumption, there is only one subclient in the backupset
        self.log.info('Getting IndexServer backup client objects')
        index_server_client = self.idx_help.get_index_backup_clients(self.subclient)
        isc = self.commcell.clients.get(index_server_client[0])
        isc_agent = isc.agents.get('Big Data Apps')
        isc_backupset = isc_agent.backupsets.get('defaultBackupSet')
        self.isc_subclient = isc_backupset.subclients.get('default')

        self.log.info(
            'IndexServer client [%s], subclient [%s]',
            isc.client_name,
            self.isc_subclient.subclient_name
        )

    def run(self):
        """Contains the core testcase logic"""

        # Flags for type of data in media - Refer mediaPredictionTypes.h#22 for more details.
        in_lib = 1
        index_media = 2
        data_media = 8

        self.log.info(' => Running cycle: FULL1 -> INC1 -> CHECKPOINT -> INC2 -> SFULL1 -> INC3 -> SFULL2')
        self.log.info(
            ' => Flags meaning: In library [%s] Index media [%s] Data media [%s]',
            in_lib, index_media, data_media
        )

        self.log.info('***** Running FULL 1, INC 1 *****')
        self.idx_tc.new_testdata(self.subclient.content, count=1)
        self.run_backup('full', 'full1')

        self.idx_tc.edit_testdata(self.subclient.content)
        self.run_backup('incremental', 'inc1')

        self.verify_list_media(
            options={},
            expected_media={
                'full1': in_lib + index_media + data_media,
                'inc1': in_lib + index_media + data_media
            }
        )

        self.log.info('***** Running index checkpoint *****')
        self.run_index_checkpoint()

        self.log.info('***** Running INC 2 *****')
        self.idx_tc.edit_testdata(self.subclient.content)
        self.run_backup('incremental', 'inc2')

        self.verify_list_media(
            options={},
            expected_media={
                'full1': in_lib + data_media,
                'inc1': in_lib + data_media,
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + data_media + index_media,
            }
        )

        self.log.info('***** Running Synthetic full 1 *****')
        self.idx_tc.edit_testdata(self.subclient.content)
        self.run_backup('synthetic_full', 'sfull1')

        self.verify_list_media(
            options={},
            expected_media={
                'inc2': in_lib + index_media,
                'sfull1': in_lib + data_media + index_media,
                'checkpoint': in_lib + index_media
            }
        )

        self.log.info('***** Running INC 3 *****')
        self.idx_tc.edit_testdata(self.subclient.content)
        self.run_backup('incremental', 'inc3')

        self.verify_list_media(
            options={},
            expected_media={
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + index_media,
                'sfull1': in_lib + data_media + index_media,
                'inc3': in_lib + data_media + index_media
            }
        )

        self.log.info('***** Verifying job based list media (INC 1 job) *****')
        inc1_job = self.media['inc1']['job']
        self.verify_list_media(
            options={
                'from_time': inc1_job.start_timestamp,
                'to_time': inc1_job.end_timestamp
            },
            expected_media={
                'inc1': in_lib + data_media,
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + index_media,
                'sfull1': in_lib + index_media,
                'inc3': in_lib + index_media,
            }
        )

        self.log.info('***** Verifying list media from BACKUPSET level (timerange between FULL and INC 2) *****')
        self.verify_list_media(
            options={
                'from_time': self.media['full1']['job'].start_timestamp,
                'to_time': self.media['inc2']['job'].end_timestamp
            },
            expected_media={
                'full1': in_lib + data_media,
                'inc1': in_lib + data_media,
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + index_media + data_media,
                'sfull1': in_lib + index_media,
                'inc3': in_lib + index_media
            },
            level='backupset'
        )

        self.log.info('***** Verifying list media with COPY PRECEDENCE set (full1 job) *****')
        self.verify_list_media(
            options={
                'from_time': self.media['full1']['job'].start_timestamp,
                'to_time': self.media['full1']['job'].end_timestamp,
                'copy_precedence': 1
            },
            expected_media={
                'full1': in_lib + data_media,
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + index_media,
                'sfull1': in_lib + index_media,
                'inc3': in_lib + index_media
            }
        )

        self.log.info('***** Verifying list media with PATH set *****')
        self.verify_list_media(
            options={
                'path': self.subclient.content[0]
            },
            expected_media={
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + index_media,
                'sfull1': in_lib + data_media + index_media,
                'inc3': in_lib + data_media + index_media
            }
        )

        self.log.info('***** Running Synthetic full 2 *****')
        self.idx_tc.edit_testdata(self.subclient.content)
        self.run_backup('synthetic_full', 'sfull2')

        self.log.info('***** Verifying list media after SFULL 2 *****')
        self.verify_list_media(
            options={},
            expected_media={
                'checkpoint': in_lib + index_media,
                'inc2': in_lib + index_media,
                'sfull1': in_lib + index_media,
                'inc3': in_lib + index_media,
                'sfull2': in_lib + index_media + data_media,
            }
        )

    def run_backup(self, level, name):
        """Runs backup with start new media option set and records the media used by the job

            Args:
                level       (str)       --      The backup level of the job

                name        (str)       --      A friendly name for the job used during verifying list media

        """

        job_obj = self.idx_tc.run_backup(self.subclient, level, verify_backup=False, advanced_options={
            'start_new_media': False if level.lower() == 'synthetic_full' else True
        })

        media_id = self.get_media_job(job_obj.job_id)

        self.media[name] = {
            'job': job_obj,
            'media_id': media_id,
            'subclient_id': self.subclient.subclient_id
        }

        self.log.info('Current status of data tapes [%s]', self.media)

    def run_index_checkpoint(self):
        """Runs the index checkpoint job and makes a note of the media used by the job"""

        index_backup_job = self.idx_help.run_index_backup(self.isc_subclient)

        query = f"""
            select id, isValid from archFile where
            name like 'IdxCheckPoint_{self.backupset.guid}:%'
            and jobid = '{index_backup_job.job_id}'
        """

        self.csdb.execute(query)
        rows = self.csdb.fetch_one_row()
        if not rows or rows[1] != '1':
            raise Exception('Index DB was not checkpointed by the job [%s] [%s]', index_backup_job.job_id, rows)

        self.log.info('Index DB is checkpointed. Afile ID [%s]', rows[0])

        media_id = self.get_media_job(index_backup_job.job_id, rows[0])
        self.media_index.append({
            'job': index_backup_job,
            'media_id': media_id,
            'subclient_id': self.isc_subclient.subclient_id
        })

    def verify_list_media(self, options, expected_media, level='subclient'):
        """Verifies the list media results

            Args:
                options         (dict)      --      The options to pass to list media

                expected_media  (dict)      --      A dictionary of tapes expected from the jobs and media flags

                level           (str)       --      The level to do list media from

        """

        self.log.info(
            '***** Verifying list media for options [%s], expected media %s *****', options, expected_media
        )

        entity = self.subclient if level == 'subclient' else self.backupset
        media_out, size_out = entity.list_media(options)

        self.log.info('List media response [%s], Total size [%s]', media_out, size_out)
        if not media_out:
            raise Exception('List media returned no media for the given request')

        actual_media_list = {}
        for media_data in media_out:
            flags = media_data['physicalMedia']['flags']
            media_name = self.media_name(
                media_data['physicalMedia']['subclient']['subclientId'],
                media_data['physicalMedia']['uniqueId']
            )

            self.log.info(' => Media in actual list [%s] flags [%s]', media_name, flags)
            actual_media_list[media_name] = flags

        self.log.info('Actual media list %s', actual_media_list)

        expected_media_list = {}
        for job_name, flags in expected_media.items():
            if job_name == 'checkpoint':
                if self.media_index:
                    recent_checkpoint = self.media_index[-1]
                    media_name = self.media_name(
                        recent_checkpoint['subclient_id'],
                        recent_checkpoint['media_id']
                    )
                else:
                    continue
            else:
                media_name = self.media_name(
                    self.media[job_name]['subclient_id'],
                    self.media[job_name]['media_id']
                )

            self.log.info(' => Media in expected list [%s] flags [%s]', media_name, flags)
            expected_media_list[media_name] = flags

        self.log.info('Expected media list %s', expected_media_list)

        if expected_media_list != actual_media_list:
            raise Exception(
                f'Mismatch in actual and expected results. '
                f'Actual [{actual_media_list}] Expected [{expected_media_list}]'
            )

        self.log.info('***** Successfully verified list media *****')

    def get_media_job(self, job_id, afile_id=None):
        """Queries the actual media used by the job

            Args:
                job_id          (str)       --      The job ID to get media for

                afile_id        (str)       --      The afile ID in specific to get media for

            Returns:
                (str)   --  The unique media ID of the media

        """

        query = f"""
            select distinct mm.UniqueId from archfile af
            join archChunkMapping acm on acm.archFileId = af.id
            join archChunk ac on ac.id = acm.archChunkId
            join MMVolume mv on mv.VolumeId = ac.volumeId
            join MMMedia mm on mm.MediaId = mv.MediaId
            where af.jobid = '{job_id}'
        """

        if afile_id:
            query += f" and af.id='{afile_id}'"

        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()

        self.log.info('Media used by job [%s] is %s', job_id, rows)

        if not rows or not rows[0]:
            raise Exception(f'No media found for the given job [{job_id}]')

        return rows[0][0]  # Assumption - Jobs always take only one media

    @staticmethod
    def media_name(subclient_id, media_id):
        """Prepares an internal name for the media using subclient ID and CV media ID"""
        return f'{subclient_id}_{media_id}'
