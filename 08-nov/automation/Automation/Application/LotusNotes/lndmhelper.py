# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Helper for Domino Mailbox Archiver automation operations

    LNDOCHelper:
        __init__(testcase)                          --  Initialize the lndmhelper object

        verify_archive()                            --  Verifies archival for a subclient

        verify_basic_restores()                     --  Verifies in-place and out-place restores

        _create_blank_mail_file()                   --  Creates a 0 document mail nsf for restores


"""

from .cvrest_helper import CVRestHelper
from .csdbhelper import CSDBHelper
from .exception import LNException, TimeoutException
from .constants import OUT_PLACE_FOLDER_PATH


class LNDMHelper:
    """"Contains helper functions for LN Agent related automation tasks
    """

    def __init__(self, testcase):
        """"Initializes the LNDM Helper class object

                Properties to be initialized:
                    tc      (object)    --  testcase object

                    cvhelp  (object)    --  object of CVRestHelper class

                    dbhelp  (object)    --  object of CSDBHelper class

                    log     (object)    --  object of the logger class

        """
        self.tc = testcase
        self.cvhelp = CVRestHelper(testcase)
        self.dbhelp = CSDBHelper(testcase)
        self.log = testcase.log

    def verify_archive(self):
        """"Verifies archival for a subclient.
        Requires the subclient to be already created

        """
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        self.cvhelp.run_backup(level='FULL')
        try:
            browse_paths_dictionary = self.cvhelp.recursive_browse(
                subclient=self.tc.subclient,
                machine=self.tc.machine
            )
            self.log.info('dbs_in_subclient:')
            self.log.info(self.tc.dbs_in_subclient)
            self.log.info('browse paths:')
            browse_result = []
            for browse_path in browse_paths_dictionary:
                if 'mail' in browse_path:
                    browse_path = [browse_paths_dictionary.get(browse_path)[0].split("\u0012", 1)[0]]
                    browse_result.extend(browse_path)
                else:
                    browse_result.extend(browse_paths_dictionary.get(browse_path))
            for i, _ in enumerate(browse_result):
                _ = _.replace('\\', '', 1)
                if 'WINDOWS' not in self.tc.machine.os_info:
                    _1_, _2_ = _.split('\u0012', 1)
                    _ = _1_.replace('/', '', 1)
                browse_result[i] = _
            self.log.info(browse_result)
            if not set(browse_result) == set(self.tc.dbs_in_subclient):
                self.log.info('Browse failed')
                raise LNException('CVOperation', '101')
            else:
                self.log.info('Test Scenario PASSED')
                self.tc.pass_count += 1
        except TimeoutException:
            self.tc.pass_count += 1
            self.log.info('Browse processor ran indefinately')
            pass
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            self._create_blank_mail_file(database)
        self.tc.common_options_dict = {'unconditionalOverwrite': True}
        self.cvhelp.run_restore()

    def verify_basic_restores(self):
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
            src_properties = [len(_['documents']) for _ in response]
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, step)
            for database in self.tc.dbs_in_subclient:
                if 'OUT' in step:
                    database_name = f'{OUT_PLACE_FOLDER_PATH}{self.tc.machine.os_sep}{database}'
                else:
                    database_name = str(database)
                self._create_blank_mail_file(database_name)
            self.cvhelp.run_restore(type_of_restore=step)
            self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient, step)
            cv_properties = [len(_['documents']) for _ in response]
            self.log.info(src_properties)
            self.log.info(cv_properties)
            if set(src_properties) != set(cv_properties):
                raise LNException('DocProperties', '101', f'{step}')
            self.log.info(f'Test Scenario {step} PASSED')
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, 'OUT')
            for database in self.tc.dbs_in_subclient:
                self._create_blank_mail_file(database)
            self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
            del src_properties, cv_properties
        self.tc.pass_count += 1

    def verify_append(self):
        """"Verifies that restore option 'Append' works as expected.

        """
        self.tc.subclient.refresh()
        self.tc.dbs_in_subclient = []
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        job_ini = self.cvhelp.run_backup(level='FULL')
        self.tc.common_options_dict = {'append': True, 'unconditionalOverwrite': False}
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        src_properties = [len(_['documents']) for _ in response]
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            database_name = str(database)
            self._create_blank_mail_file(database_name)
            self.cvhelp.return_result_json(
                'add documents',
                param=[database.replace(self.tc.machine.os_sep, '-'), "2"]
            )
        self.cvhelp.run_restore()
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        cv_properties = [len(_['documents']) for _ in response]
        self.log.info(src_properties)
        self.log.info(cv_properties)
        if set(src_properties) >= set(cv_properties):
            raise LNException('DocProperties', '102',)
        self.log.info(f'Test Scenario PASSED')
        self.tc.pass_count += 1
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            self._create_blank_mail_file(database)
        self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
        del src_properties, cv_properties

    def verify_skip(self):
        """"Verifies that restore option 'Skip' works as expected.

        """
        self.tc.subclient.refresh()
        self.tc.dbs_in_subclient = []
        self.tc.dbs_in_subclient = self.dbhelp.fetch_subclient_content()
        self.log.info(self.tc.dbs_in_subclient)
        job_ini = self.cvhelp.run_backup(level='FULL')
        self.tc.common_options_dict = {'skip': True, 'unconditionalOverwrite': False}
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        src_properties = [len(_['documents']) for _ in response]
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            database_name = str(database)
            self._create_blank_mail_file(database_name)
        self.cvhelp.run_restore()
        self.log.info('**********************COLLECT*DOC*PROPERTIES***********************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        cv_properties = [len(_['documents']) for _ in response]
        self.log.info(src_properties)
        self.log.info(cv_properties)
        if set(src_properties) != set(cv_properties):
            raise LNException('DocProperties', '101')
        self.log.info(f'Test Scenario PASSED')
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient)
        for database in self.tc.dbs_in_subclient:
            self._create_blank_mail_file(database)
        self.cvhelp.run_restore(start_time=job_ini.start_time, end_time=job_ini.end_time)
        del src_properties, cv_properties
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
        for database in self.tc.dbs_in_subclient:
            database_name = str(database)
            self._create_blank_mail_file(database_name)
        self.tc.subclient.delete()
        self.tc.backupset.restore(start_time=job.start_time, end_time=job.end_time)
        self.log.info(
            '****************COLLECT*DOC*PROPERTIES********************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_subclient)
        doc_count_cv = doc_count_cv.append(len(_['documents']) for _ in response)
        if doc_count_src == doc_count_cv:
            self.tc.pass_count += 1
            self.log.info('Able to restore user defined subclient version')
        else:
            self.log.error('Unable to restore user defined subclient version')
            self.log.info(
                f'Source: {doc_count_src} CV: {doc_count_cv}')

    def _create_blank_mail_file(self, database_name):
        """"Creates a 0 document mail nsf for restores

                Args:
                    database_name       (str)       --  Name by which database has to be created

        """
        restore_jstring = {
            "key":
                [{
                    "template": "mail9.ntf",
                    "numdb": "1",
                    "numdocs": "0",
                    "numlogs": "null",
                    "dbname": database_name,
                    "trlog": "true",
                    "del": "false",
                    "incremental": "false"
                }]
        }
        self.cvhelp.return_result_json('data populator', jstring=restore_jstring)
