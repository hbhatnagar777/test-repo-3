# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Helper for Notes Document automation operations

    LNDOCHelper:
        __init__(testcase)                          --  Initialize the lndochelper object

        verify_full_backup()                        --  Verifies full backup for a subclient

        verify_incremental_backup()                 --  Verifies incremnetal backup for subclient

        verify_differential_backup()                --  Verifies differential backup for subclient

        verify_synthetic_backup()                   --  Verifies synthetic backup for a subclient

        verify_restores()                           --  Verifies in-place/out-place restores

        verify_template_and_encrypted_db_backup()   --  Verifies data protection for template and
        encrypted databases


"""
from .cvrest_helper import CVRestHelper
from .csdbhelper import CSDBHelper
from .exception import LNException


class LNDOCHelper:
    """"Contains helper functions for LN Agent related automation tasks
    """

    def __init__(self, testcase):
        """"Initializes the LNDOC Helper class object

                Properties to be initialized:
                    tc      (object)    --  testcase object

                    cvhelp  (object)    --  object of CVRestHelper class

                    log     (object)    --  object of the logger class

        """
        self.tc = testcase
        self.cvhelp = CVRestHelper(testcase)
        self.dbhelp = CSDBHelper(testcase)
        self.log = testcase.log

    def verify_full_backup(self):
        """"Verifies full backup for a subclient.
        Requires the subclient to be already created

        """
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        self.cvhelp.run_backup(level='FULL')
        browse_paths_dictionary = self.cvhelp.recursive_browse(
            subclient=self.tc.subclient,
            machine=self.tc.machine
        )
        self.log.info('dbs_in_subclient:')
        self.log.info(self.tc.dbs_in_subclient)
        self.log.info('browse paths:')
        self.log.info(list(browse_paths_dictionary.keys()))
        if not set(browse_paths_dictionary.keys()) == set(self.tc.dbs_in_subclient):
            self.log.info('Browse failed')
            raise LNException('CVOperation', '101')
        else:
            self.log.info('Test Scenario PASSED')
            self.tc.pass_count += 1

    def verify_incremental_backup(self):
        """"Verifies incremental backup for a subclient.
        Requires the subclient to be already created

        """
        job_ini = self.cvhelp.run_backup(level='FULL')
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        number_of_databases = len(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            self.cvhelp.return_result_json('add documents', param=[database, "2"])
        self.log.info('1st incremental')
        job = self.cvhelp.run_backup(level='INCREMENTAL')
        for database in self.tc.dbs_in_subclient:
            response = self.cvhelp.return_result_json('get document properties', param=[database])
            self.log.info(f'Total docs for {database} is {len(response.get("documents"))}')
        backup_size = job.summary['sizeOfApplication']
        if backup_size == 0:
            raise LNException('CVOperation', '103')
        self.log.info(f'Application size is {backup_size} as expected')
        self.log.info('Data was backed up')
        self.log.info('2nd incremental')
        job = self.cvhelp.run_backup(level='INCREMENTAL')
        if not job.summary['totalNumOfFiles'] == (4 * number_of_databases):
            raise LNException('CVOperation', '103')
        self.log.info('Nothing was backed up because no new data was added')
        self.tc.pass_count += 1
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
        self.log.info('Test Scenario PASSED')

    def verify_differential_backup(self):
        """"Verifies incremental backup for a subclient.
        Requires the subclient to be already created

        """
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        self.log.info('SOURCE PROPERTIES FULL')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        src_properties_full = [tuple(_['documents']) for _ in response]
        src_properties_full = self.cvhelp.clean_properties_fetched(src_properties_full)
        job = self.cvhelp.run_backup(level='FULL')
        for database in self.tc.dbs_in_subclient:
            self.cvhelp.return_result_json('add documents', param=[database, "2"])
        self.log.info('1st incremental')
        self.cvhelp.run_backup(level='INCREMENTAL')
        for database in self.tc.dbs_in_subclient:
            self.cvhelp.return_result_json('add documents', param=[database, "2"])
        self.log.info('2nd incremental')
        self.cvhelp.run_backup(level='INCREMENTAL')
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        self.log.info('SOURCE PROPERTIES DIFFERENTIAL')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        src_properties_diff = [tuple(_['documents']) for _ in response]
        src_properties_diff = self.cvhelp.clean_properties_fetched(src_properties_diff)
        self.cvhelp.run_backup(level='DIFFERENTIAL')
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        self.cvhelp.run_restore(start_time=job.start_time, end_time=job.end_time)
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        self.log.info('CV PROPERTIES FULL')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        cv_properties_full = [tuple(_['documents']) for _ in response]
        cv_properties_full = self.cvhelp.clean_properties_fetched(cv_properties_full)
        if src_properties_full != cv_properties_full:
            raise LNException('DocProperties', '101', 'FULL BACKUP')
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        self.cvhelp.run_restore()
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        self.log.info('CV PROPERTIES DIFFERENTIAL')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        cv_properties_diff = [tuple(_['documents']) for _ in response]
        cv_properties_diff = self.cvhelp.clean_properties_fetched(cv_properties_diff)
        if src_properties_diff != cv_properties_diff:
            raise LNException('DocProperties', '101', 'DIFFERENTIAL BACKUP')
        self.tc.pass_count += 1
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        self.cvhelp.run_restore(start_time=job.start_time, end_time=job.end_time)
        self.log.info('Test Scenario PASSED')

    def verify_synthetic_backup(self):
        """"Verifies synthetic full backup for a subclient.
        Requires the subclient to be already created

        """
        test_scenarios = ['AFTER_SYNTH', 'BEFORE_SYNTH']
        job_ini = self.cvhelp.run_backup(level='FULL')
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        for step in test_scenarios:
            self.log.info('********************************************************************')
            self.log.info(f'***********************{step}*******************************')
            self.log.info('********************************************************************')
            for _ in range(3):
                for database in self.tc.dbs_in_subclient:
                    self.cvhelp.return_result_json('add documents', param=[database, "2"])
                self.log.info(f'{_+1} incremental')
                self.cvhelp.run_backup(level='INCREMENTAL')
            self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
            src_count = [len(_['documents']) for _ in response]
            if 'AFTER' in step:
                self.cvhelp.delete_indexcache(subclient=self.tc.subclient)
            job1 = self.cvhelp.run_backup(
                level='SYNTHETIC_FULL',
                incremental_backup=True,
                incremental_level=step
            )
            job_dict = self.tc.commcell.job_controller.all_jobs(
                lookup_time=0.01)
            job2 = self.tc.commcell.job_controller.get(list(job_dict.keys())[0])
            job2.wait_for_completion()
            self.log.info(job2)
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, 'OUT')
            if 'BEFORE' in step:
                job = job2
            else:
                job = job1
            self.log.info(f'Synthetic Job: {job}')
            self.cvhelp.run_restore(
                type_of_restore='OUT',
                start_time=job.start_time,
                end_time=job.end_time
            )
            self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient, 'OUT')
            cv_count = [len(_['documents']) for _ in response]
            if set(src_count) != set(cv_count):
                raise LNException(
                    'DocProperties',
                    '101',
                    f'SYNTHETIC BACKUP WITH INCREMENTAL {step}'
                )
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, 'OUT')
            self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
            self.log.info(f'Test Scenario {step} PASSED')
            del src_count, cv_count
        self.tc.pass_count += 1

    def verify_restores(self):
        """"Verifies in-place and out-place restores for a subclient.
            Requires the subclient to be already created

        """
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        job_ini = self.cvhelp.run_backup(level='FULL')
        test_scenarios = ['OUT PLACE RESTORE', 'IN PLACE RESTORE']
        for step in test_scenarios:
            self.log.info('********************************************************************')
            self.log.info(f'{step}')
            self.log.info('********************************************************************')
            self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
            src_properties = [tuple(_['documents']) for _ in response]
            src_properties = self.cvhelp.clean_properties_fetched(src_properties)
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, step)
            self.cvhelp.run_restore(type_of_restore=step)
            self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient, step)
            cv_properties = [tuple(_['documents']) for _ in response]
            cv_properties = self.cvhelp.clean_properties_fetched(cv_properties)
            self.log.info(src_properties)
            self.log.info(cv_properties)
            if src_properties != cv_properties:
                raise LNException('DocProperties', '101', f'{step}')
            self.log.info(f'Test Scenario {step} PASSED')
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, 'OUT')
            self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
            del src_properties, cv_properties
        self.tc.pass_count += 1

    def verify_template_and_encrypted_db_backup(self):
        """"Verifies data protection for template and encrypted databases.
        Requires a subclient to be created beforehand with the appropriate dbs

        """
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            self.log.info('Database: ' + database)
        test_steps = {'IN PLACE RESTORE',
                      'OUT PLACE RESTORE'}
        count = 0
        for step in test_steps:
            self.log.info(
                '**************************************************************')
            self.log.info(step)
            self.log.info(
                '**************************************************************')
            self.log.info(
                '**********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(
                self.tc.dbs_in_subclient)
            temp = [tuple(_['documents']) for _ in response]
            doc_properties_beforebackup = self.cvhelp.clean_properties_fetched(temp)
            del temp
            self.cvhelp.run_backup()
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, step)
            self.cvhelp.run_restore(type_of_restore=step)
            self.log.info(
                '****************COLLECT*DOC*PROPERTIES********************')
            response = self.cvhelp.collect_doc_properties(
                dbs_in_subclient=self.tc.dbs_in_subclient,
                type_of_restore_performed=step
            )
            temp = [tuple(_['documents']) for _ in response]
            doc_properties_afterrestore = self.cvhelp.clean_properties_fetched(temp)
            del temp
            self.log.info(
                '*****************COMPARE*DOC*PROPERTIES*******************')
            if doc_properties_beforebackup != doc_properties_afterrestore:
                self.log.error(f'Test scenario {step} has failed')
                raise LNException(
                    'DocProperties',
                    '101',
                    f'Before: {doc_properties_beforebackup} || '
                    f'After : {doc_properties_afterrestore}'
                )
            else:
                self.log.info('Document properties match')
                self.log.info(f'Test scenario {step} has passed')
                count = count + 1
        if count < 2:
            raise LNException('TestScenario', '101', f'{count}/2')
        else:
            self.tc.pass_count += 1

    def verify_data_docs_restore(self):
        """"Verifies overwrite data documents restore option
            Requires the subclient to be already created

        """
        src_prop, cv_prop = [], []
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        job_ini = self.cvhelp.run_backup(level='FULL')
        response = self.cvhelp.return_result_json(
            'add auto stub',
            param=["1"],
            jstring=[self.tc.dbs_in_subclient]
        )
        self.log.info("*********************ORIGINAL*PROPERTY******************************")
        self.log.info(response)
        try:
            for _ in response:
                src_prop.append(_['documents'][0]['CVAutoStub'])
        except Exception:
            src_prop.append(response['documents'][0]['CVAutoStub'])
        self.log.info(src_prop)
        self.cvhelp.run_backup(level='FULL')
        self.log.info("*********************CHANGE*PROPERTY******************************")
        self.cvhelp.return_result_json(
            'add auto stub',
            param=["0"],
            jstring=[self.tc.dbs_in_subclient]
        )
        self.tc.common_options_dict = {'overwriteDataDoc': True}
        self.cvhelp.run_restore()
        response = self.cvhelp.return_result_json(
            'view auto stub',
            jstring=[self.tc.dbs_in_subclient]
        )
        self.log.info(response)
        for database in self.tc.dbs_in_subclient:
            cv_prop.append(response[database])
        if set(src_prop) != set(cv_prop):
            raise LNException('DocProperties', '101')
        self.log.info(f'Test Scenario PASSED')
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
        del src_prop, cv_prop
        self.tc.pass_count += 1

    def deleted_subclient(self):
        """"Verifies data protection for a deleted subclient.
        Need to create the subclient manually again after this test scenario deletes it.

        """
        self.tc.subclient.refresh()
        self.tc.dbs_in_subclient = []
        doc_count_src, doc_count_cv = [], []
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        doc_count_src = doc_count_src.append(len(_['documents']) for _ in response)
        job = self.cvhelp.run_backup()
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, 'in')
        self.tc.subclient.delete()
        self.tc.backupset.restore(start_time=job.start_time, end_time=job.end_time)
        self.log.info('****************COLLECT*DOC*PROPERTIES********************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        doc_count_cv = doc_count_cv.append(len(_['documents']) for _ in response)
        if doc_count_src == doc_count_cv:
            self.tc.pass_count += 1
            self.log.info('Able to restore user defined subclient version')
        else:
            self.log.error('Unable to restore user defined subclient version')
            self.log.info(
                f'Source: {doc_count_src} CV: {doc_count_cv}')
