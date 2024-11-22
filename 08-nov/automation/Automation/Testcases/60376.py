# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies that multistream synthetic full job handles scenarios where one of the MA used for
synthetic full is down

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    switch_data_path()          --  Switches the default datapath and adds it to the list

    change_index_server()       --  Changes the IndexServer MA for the backupset/subclient

    start_ma_services()         --  Starts the MA services

"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Server.JobManager.jobmanager_helper import JobManager

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies that multistream synthetic full job handles scenarios where one of the MA used for
    synthetic full is down

        Steps:
            1) Create backupset and subclient
            2) Have a storage policy which has multiple datapaths.
            3) Run FULL - INC - INC
            4) Before each job rotate default datapath so that each job picks a different MA for backup.
            5) Stop the services of one of the MA and keep other MA up.
            6) Now run multistream SFULL
            7) Multi stream SFULL should go pending/wait for the MA to come up to backup the items from that MA.
            8) Bring back the MA and job should complete successfully.

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Synthetic full - Stream MA is down'

        self.tcinputs = {
            'TestDataPath': None,
            'RestoreLocation': None,
            'CopyData': None,
            'StoragePolicy': None,
            'IndexServer': None,
            'MAInfo': None
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.idx_db = None
        self.storage_policy = None
        self.primary_copy = None
        self.mas_used = []
        self.ma_client = None
        self.ma_machine = None
        self.ma_service_down = False

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        self.primary_copy = self.storage_policy.get_primary_copy()

        self.backupset = self.idx_tc.create_backupset(f'{self.id}_sfull_ma_down', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name=f'sc1_{self.id}',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        ma_info = self.tcinputs.get('MAInfo')
        if not ma_info.get('name') or not ma_info.get('username') or not ma_info.get('password'):
            input_format = {
                'name': '<ma name>',
                'username': '<ma username>',
                'password': '<ma password>'
            }
            raise Exception(f'MAInfo does not have all the inputs. Format: [{input_format}]')

        self.ma_client = self.commcell.clients.get(ma_info.get('name'))
        self.log.info('Initializing MA object with hostname [%s]', self.ma_client.client_hostname)

        self.ma_machine = Machine(
            machine_name=self.ma_client.client_hostname,
            username=ma_info.get('username'),
            password=ma_info.get('password')
        )
        self.log.info('MA to stop services is [%s]', self.ma_client.client_name)

    def run(self):
        """Contains the core testcase logic"""
        try:
            self.idx_tc.run_backup_sequence(self.subclient, ['new', 'copy', 'full'], verify_backup=True)

            self.switch_data_path()
            self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

            #self.switch_data_path()
            #self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

            #self.switch_data_path()
            #self.idx_tc.run_backup_sequence(self.subclient, ['edit', 'incremental'], verify_backup=True)

            self.log.info('***** Changing IndexServer *****')
            self.change_index_server()

            self.log.info(
                '***** Stopping the services on MA [%s] before starting synthetic full job *****',
                self.ma_client.client_name
            )

            self.ma_client.stop_service(service_name='GxCVD(Instance001)')
            self.ma_service_down = True
            self.log.info('Stopped services on MA')

            self.log.info('Waiting 5 mins for IndexSever services to go down')
            time.sleep(300)

            job = self.idx_tc.cv_ops.subclient_backup(
                self.subclient,
                backup_type='Synthetic_full',
                wait=False
            )
            jm_obj = JobManager(job, self.commcell)
            time.sleep(20)

            max_jpr_checks = 0
            while job.delay_reason is None and max_jpr_checks < 10:
                self.log.info('Job delay reason is [%s]', job.delay_reason)
                max_jpr_checks += 1
                time.sleep(20)
            self.log.info('Job delay reason is [%s]', job.delay_reason)

            expected_jpr = self.tcinputs.get('ErrorJPRString', 'Unable to allocate resources')
            if expected_jpr in job.delay_reason and job.state.lower() in ['pending', 'waiting']:
                self.log.info('Job is pending with JPR [%s] State [%s]', job.delay_reason, job.state)
                self.log.info('Job went pending with expected JPR [%s]', expected_jpr)
            else:
                raise Exception('Job did not go to pending/waiting state when MA is down')

            time.sleep(10)
            self.start_ma_services()
            time.sleep(10)

            try:
                if not job.is_finished:
                    self.log.info('Resuming the job')
                    job.resume(wait_for_job_to_resume=True)
            except Exception as e:
                self.log.error('Unable to resume the job [%s]', e)

            jm_obj.wait_for_state('completed')
            self.log.info('Job completed successfully')

            self.backupset.idx.record_job(job)

            self.idx_tc.verify_synthetic_full_job(job, self.subclient)

        except Exception as exp:
            self.log.exception('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if self.ma_service_down:
                self.start_ma_services()

    def switch_data_path(self):
        """Switches the default datapath and adds it to the used MA list"""

        new_ma = self.idx_tc.rotate_default_data_path(self.primary_copy)
        if new_ma not in self.mas_used:
            self.mas_used.append(new_ma.lower())

    def change_index_server(self):
        """Changes the IndexServer MA for the backupset/subclient"""

        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)

        entity_obj = self.subclient if indexing_level == 'subclient' else self.backupset
        entity_obj.refresh()
        self.log.info('Current IndexServer MA is [%s]', entity_obj.index_server.client_name)

        self.log.info('Changing IndexServer to [%s]', self.tcinputs.get('IndexServer'))
        entity_obj.index_server = self.commcell.clients.get(self.tcinputs.get('IndexServer'))

        time.sleep(5)
        entity_obj.refresh()
        self.log.info('IndexServer is changed to [%s]', entity_obj.index_server.client_name)

    def start_ma_services(self):
        """Starts the MA services"""
        try:
            self.log.info('Starting services on the MA [%s]', self.ma_client.client_name)
            self.ma_machine.start_all_cv_services()
            self.ma_service_down = False
        except Exception as e:
            self.log.error('Failed to start services on MA [%s]', e)
