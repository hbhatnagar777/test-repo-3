# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Helper for Notes Database automation operations

    LNDBHelper:
        __init__(testcase)                  --  Initialize the lndbhelper object

        backup_template_and_encrypted_db()  --  Verifies data protection for template and
        encrypted databases

        deleted_subclient()                 --  Verifies data protection for a deleted subclient

        mark_job_bad()                      --  Verifies restore from a backup job that has been
        marked as bad

        unconditional_overwrite()           --  Verifies that restore option 'Unconditional
        Overwrite' works as expected

        database_replica_id()               --  Verifies that restore option 'Change Replica ID'
        works as expected

        database_instance_id()              --  Verifies that restore option 'Change Database
        Instance ID' works as expected

        do_not_replay_transact_logs()       --  Verifies that restore option 'Do Not Replay
        Transactional Logs' works as expected

        disable_replication()               --  Verifies that restore option 'Disable Replication'
        works as expected

        full_data_protection()              --  Verifies full backup for a subclient.

        inc_data_protection()               --  Verifies incremental backups for a subclient

        restores()                          --  Verifies in-place and put-place restores for
        a subclient

        defsubclient_autodiscovery()        --  Verifies auto-discovery feature of the
        default subclient

        disaster_recovery()                 --  Verifies disaster recovery scenario

        tr_log_backup_with_indexing()       --  Verifies tr log backup job with indexing

        backup_many_tr_logs()               --  Verifies data protection with a large number
        of tr logs

        backup_many_databases()             --  Verifies data protection with a large number
        of databases

        osc_schedule_backup()               --  Verifies osc scheduler triggered backups

"""
import time

from . import constants
from .cvrest_helper import CVRestHelper
from .exception import LNException, TimeoutException, BrowseException, InvalidJobException


class LNDBHelper:
    """"Contains helper functions for LN Agent related automation tasks
    """

    def __init__(self, testcase):
        """"Initializes the LNDB Helper class object

                Properties to be initialized:
                    tc      (object)    --  testcase object

                    cvhelp  (object)    --  object of CVRestHelper class

                    log     (object)    --  object of the logger class

        """
        self.tc = testcase
        self.cvhelp = CVRestHelper(testcase)
        self.log = testcase.log

    def backup_template_and_encrypted_db(self):
        """"Verifies data protection for template and encrypted databases.
        Requires a subclient to be created beforehand with the appropriate dbs

        """
        self.log.info(self.tc.subclient.content)
        self.tc.dbs_in_subclient = []
        self.tc.dbs_in_subclient = self.cvhelp.remove_extension(
            self.tc.subclient.content,
            self.tc.machine.os_info
        )
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
            doc_properties_beforebackup = [_['documents'] for _ in response]
            self.cvhelp.run_backup()
            self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, step)
            self.cvhelp.run_restore(type_of_restore=step)
            self.log.info(
                '****************COLLECT*DOC*PROPERTIES********************')
            response = self.cvhelp.collect_doc_properties(
                dbs_in_subclient=self.tc.dbs_in_subclient,
                type_of_restore_performed=step
            )
            doc_properties_afterrestore = [_['documents'] for _ in response]
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

    def deleted_subclient(self):
        """"Verifies data protection for a deleted subclient.

        """
        self.tc.dbs_in_subclient = []
        self.tc.dbs_in_def_subclient = []
        count = 0
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.newsubclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        dbname = self.cvhelp.add_database_to_subclient(
            self.tc.newsubclient, "1", "1")
        response = self.cvhelp.collect_doc_properties(dbname)
        doc_count_1 = [len(_['documents']) for _ in response]
        self.cvhelp.run_backup(subclient=self.tc.newsubclient)
        self.cvhelp.remove_restored_dbs(dbname, 'in')
        self.cvhelp.run_restore(subclient=self.tc.newsubclient)
        self.log.info(
            '****************COLLECT*DOC*PROPERTIES********************')
        response = self.cvhelp.collect_doc_properties(dbname)
        doc_count_3 = [len(_['documents']) for _ in response]
        if doc_count_1 == doc_count_3:
            count += 1
            self.log.info('Able to restore user defined subclient version')
        else:
            self.log.error('Unable to restore user defined subclient version')
            self.log.info(
                f'doc_count_1 {doc_count_1} doc_count_3 {doc_count_3}')
        for database in dbname:
            response = self.cvhelp.return_result_json('add documents', param=[database, "10"])
            doc_count_2 = [response['docCount']]
            self.log.info(f'Total docs for {database} is {doc_count_2}')
        self.tc.default_subclient.refresh()
        self.cvhelp.run_backup(
            level='incremental',
            subclient=self.tc.default_subclient)
        self.tc.default_subclient.refresh()
        for lndbcontent in self.tc.default_subclient.content:
            self.tc.dbs_in_def_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
        self.cvhelp.run_restore(subclient=self.tc.default_subclient)
        self.log.info(
            '****************COLLECT*DOC*PROPERTIES********************')
        response = self.cvhelp.collect_doc_properties(dbname)
        doc_count_4 = [len(_['documents']) for _ in response]
        if doc_count_2 == doc_count_4:
            count += 1
            self.log.info('Able to restore default subclient version')
        else:
            self.log.error('Unable to restore default subclient version')
            self.log.info(
                f'doc_count_2 {doc_count_2} doc_count_4 {doc_count_4}')
        if count == 2:
            self.tc.pass_count += 1
        self.cvhelp.remove_restored_dbs(dbname, 'IN')

    def mark_job_bad(self):
        """"Verifies restore from a backup job that has been marked as bad.

        """
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.newsubclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        dbname = self.cvhelp.add_database_to_subclient(
            self.tc.newsubclient, "1", "1")[0]
        job = self.cvhelp.run_backup('full', self.tc.newsubclient)
        qscript = (f"-sn 'MarkJobsOnCopy' -si '{self.tc.tcinputs['StoragePolicy']}' -si 'Primary' "
                   f"-si '{'markJobsBad'}' -si '{job.job_id}'")
        self.log.info(f'Qscript generated: {qscript}')
        response = self.tc.commcell._qoperation_execscript(qscript)
        self.log.info('Response:')
        self.log.info(response)
        browse_paths_dictionary = self.cvhelp.recursive_browse(
            subclient=self.tc.newsubclient, machine=self.tc.machine)
        self.log.info('dbs_in_subclient:')
        self.log.info([dbname])
        self.log.info('browse paths:')
        self.log.info(list(browse_paths_dictionary.keys()))
        if not set(browse_paths_dictionary.keys()) == set([dbname]):
            raise LNException('CVOperations', '101')
        self.log.info('Browse works as expected')
        job = self.cvhelp.run_restore('IN', self.tc.newsubclient)
        self.log.info('Restore Job Status: ' + job.status)
        if job.status == 'Completed':
            self.log.info('Test case PASSED')
            self.tc.pass_count += 1
        self.cvhelp.remove_restored_dbs([dbname], 'in')

    def unconditional_overwrite(self):
        """"Verifies that restore option 'Unconditional Overwrite' works as expected.

        """
        self.log.info(
            '***********************RESTORE*OPTION*1**********************************')
        self.log.info(
            '*****************UNCONDITIONAL*OVERWRITE*********************************')
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(
            subclient=self.tc.subclient,
            num_db="1",
            num_doc="10")
        for lndbcontent in self.tc.subclient.content:
            db_name = lndbcontent['lotusNotesDBContent']['databaseTitle']
        response = self.cvhelp.collect_doc_properties([db_name])
        creation_initial = response[0]['documents'][0]['created']
        self.log.info(
            f'Original creation date is {creation_initial} for database {db_name}')
        self.cvhelp.run_backup(level='FULL', subclient=self.tc.subclient)
        self.cvhelp.return_result_json('delete database', [db_name])
        self.tc.common_options_dict = {'unconditionalOverwrite': True}
        self.cvhelp.run_restore(subclient=self.tc.subclient)
        response = self.cvhelp.collect_doc_properties([db_name])
        creation_final = response[0]['documents'][0]['created']
        self.log.info(
            f'Restored creation date is {creation_final} for database {db_name}')
        if creation_final == creation_initial:
            self.log.info('Creation date is the same. Test scenario PASSED')
            self.tc.pass_count += 1
        else:
            self.log.info(f'Doc count before: {creation_initial} and '
                          f'doc count after : {creation_final} are not same.')
            self.log.info('Test sceanrio FAILED')
        self.cvhelp.remove_restored_dbs([db_name], 'IN')

    def database_replica_id(self):
        """"Verifies that restore option 'Change Replica ID' works as expected.

        """
        self.log.info(
            '***********************RESTORE*OPTION*2********************************')
        self.log.info(
            '*****************CHANGE*REPLICA*ID*************************************')
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(
            subclient=self.tc.subclient,
            num_db="1",
            num_doc="10")
        replication_info_before = []
        for lndbcontent in self.tc.subclient.content:
            self.tc.dbs_in_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
        for database in self.tc.dbs_in_subclient:
            self.log.info(f'Database: {database}')
        self.log.info(
            '****************************GET*REPLICATION*INFO********************************')
        for database in self.tc.dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'replication info', param=[database])
            self.log.info(
                f'Replica ID for {database} is {response["replicaID"]}')
            replication_info_before.append(response['replicaID'])
        test_steps = ['SAME REPLICA ID', 'CHANGE REPLICA ID']
        count = 0
        for step in test_steps:
            self.log.info(
                '****************************************************************************')
            self.log.info(step)
            replication_info_after = []
            if step == test_steps[1]:
                self.tc.common_options_dict = {'recoverZapReplica': True}
            self.log.info(
                '*****************************BACKUP*******************************')
            self.cvhelp.run_backup()
            self.cvhelp.delete_db_and_validate(
                dbsinsubclient=self.tc.dbs_in_subclient)
            self.cvhelp.run_restore()
            time.sleep(60)
            self.log.info(
                '**************************GET*REPLICATION*INFO******************************')
            for database in self.tc.dbs_in_subclient:
                response = self.cvhelp.return_result_json(
                    operation='replication info', param=[database])
                self.log.info(
                    f'Replica ID for {database} is {response["replicaID"]}')
                replication_info_after.append(response['replicaID'])
            self.log.info(
                '************************COMPARE*REPLICATION*INFO****************************')
            if replication_info_before == replication_info_after:
                self.log.info('For databases, the replica ID is the same')
                match = True
            else:
                self.log.error(
                    'For databases, the replication info is not the same')
                match = False

            if (match and step == test_steps[0]) or \
                    (not match and step == test_steps[1]):
                self.log.info(f'Test scenario {step} passed')
                count = count + 1
            else:
                self.log.info(f'Test scenario {step} failed')
        if count < 2:
            raise LNException('TestScenario', '101', f'{count}/2')
        else:
            self.tc.pass_count += 1
        self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, 'in')

    def database_instance_id(self):
        # Under development
        """"Verifies that restore option 'Change Database Instance ID' works as expected.

        """
        self.log.info(
            '**********************RESTORE*OPTION*3*********************************')
        self.log.info(
            '****************CHANGE*DATABASE*INSTANCE*ID****************************')
        dbiid_before = []
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(
            subclient=self.tc.subclient,
            num_db="1",
            num_doc="10"
        )
        for lndbcontent in self.tc.subclient.content:
            self.tc.dbs_in_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
            dbiid_before.append([lndbcontent['lotusNotesDBContent']['dbiid1'],
                                 lndbcontent['lotusNotesDBContent']['dbiid2'],
                                 lndbcontent['lotusNotesDBContent']['dbiid3'],
                                 lndbcontent['lotusNotesDBContent']['dbiid4']])
        for database in self.tc.dbs_in_subclient:
            self.log.info('Database: ' + database)
        self.log.info('DBIID before:')
        self.log.info(dbiid_before)
        test_steps = ['SAME INSTANCE ID', 'CHANGE INSTANCE ID']
        count = 0
        for step in test_steps:
            self.log.info(
                '****************************************************************************')
            self.log.info(step)
            if step == test_steps[1]:
                self.tc.common_options_dict = {'recoverZap': True}
            self.log.info(
                '*****************************BACKUP*******************************')
            self.cvhelp.run_backup()
            self.cvhelp.delete_db_and_validate(
                dbsinsubclient=self.tc.dbs_in_subclient)
            self.cvhelp.run_restore()
            time.sleep(60)
            self.tc.subclient.refresh()
            dbiid_after = []
            for lndbcontent in self.tc.subclient.content:
                dbiid_after.append([lndbcontent['lotusNotesDBContent']['dbiid1'],
                                    lndbcontent['lotusNotesDBContent']['dbiid2'],
                                    lndbcontent['lotusNotesDBContent']['dbiid3'],
                                    lndbcontent['lotusNotesDBContent']['dbiid4']])
            self.log.info('DBIID after:')
            self.log.info(dbiid_after)
            self.log.info(
                '************************COMPARE*INSTANCE*ID*INFO****************************')
            if dbiid_before == dbiid_after:
                self.log.info('For databases, the instance ID is the same')
                match = True
            else:
                self.log.error(
                    'For databases, the instance ID is not the same')
                match = False

            if (match and step == test_steps[0]) or \
                    (not match and step == test_steps[1]):
                self.log.info(f'Test scenario {step} passed')
                count = count + 1
            else:
                self.log.info(f'Test scenario {step} failed')
        if count < 2:
            self.log.info("Test scenario FAILED")
        else:
            self.tc.pass_count += 1

    def do_not_replay_transact_logs(self):
        """"Verifies that restore option 'Do Not Replay Transactional Logs' works as expected.

        """
        self.log.info(
            '***********************RESTORE*OPTION*4**********************************')
        self.log.info(
            '****************DO*NOT*REPLAY*TRANSACTIONAL*LOGS*************************')
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(self.tc.subclient, "1", "10")
        for lndbcontent in self.tc.subclient.content:
            db_name = lndbcontent['lotusNotesDBContent']['databaseTitle']
        response = self.cvhelp.collect_doc_properties([db_name])
        doc_prop_before = len(response[0]['documents'])
        self.log.info(
            f'Original doc count is {doc_prop_before} for database {db_name}')
        self.cvhelp.run_backup()
        self.log.info(
            '************************ADDING*NEW*DOCUMENTS*****************************')
        response = self.cvhelp.return_result_json(
            'add documents', param=[db_name, "10"])
        self.log.info(
            f'New doc count is {response["docCount"]} for database {db_name}')
        self.cvhelp.run_backup('incremental', self.tc.trlogsubclient)
        self.cvhelp.return_result_json('delete database', [db_name])
        response = self.cvhelp.return_result_json(
            'console commands', param=['restart server'])
        time.sleep(120)
        self.cvhelp.check_if_domino_up()
        self.tc.common_options_dict = {'doNotReplayTransactLogs': True}
        self.cvhelp.run_restore()
        response = self.cvhelp.collect_doc_properties([db_name])
        doc_prop_after = len(response[0]['documents'])
        self.log.info(
            f'Restored doc count is {doc_prop_after} for database {db_name}')
        if doc_prop_before == doc_prop_after:
            self.log.info('Test scenario PASSED')
            self.tc.pass_count += 1
        else:
            self.log.info(f'Doc count before: {doc_prop_before} and '
                          f'doc count after : {doc_prop_after} are not same.')
            self.log.info('Test sceanrio FAILED')

    def disable_replication(self):
        """"Verifies that restore option 'Disable Replication' works as expected.

        """
        self.log.info(
            '**************************RESTORE*OPTION*5*******************************')
        self.log.info(
            '***********************DISABLE*REPLICATION*******************************')
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName'])
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(
            subclient=self.tc.subclient,
            num_db="1",
            num_doc="10")
        self.log.info(self.tc.subclient.content)
        dbs_in_subclient = []
        for lndbcontent in self.tc.subclient.content:
            dbs_in_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
        for database in dbs_in_subclient:
            self.log.info('Database: ' + database)
        count = 0
        #####
        # Step 1
        #####
        self.log.info(
            '*****************************REGULAR*SETUP****************************')
        test_steps = ['IN PLACE RESTORE', 'OUT PLACE RESTORE']
        replication_info_before = []
        self.log.info(
            '********************ENABLE*REPLICATION********************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'set replication info', param=[database, 'false'])
            self.log.info(
                f'Replication status for {database} is {response["ReplicationInfo"]}')
            self.cvhelp.return_result_json(
                'console commands', param=['dbcache flush'])
        self.log.info(
            '**********************GET*REPLICATION*INFO****************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'replication info', param=[database])
            self.log.info(
                f'Replication status for {database} is {response["property"]}')
            replication_info_before.append(response['property'])
        self.log.info(
            '*****************************BACKUP*******************************')
        self.cvhelp.run_backup(level='full', subclient=self.tc.subclient)
        self.tc.lndb_restore_options = {"disableReplication": True}
        for step in test_steps:
            replication_info_after = []
            self.tc.common_options_dict = {'unconditionalOverwrite': True}
            self.cvhelp.run_restore(step)
            self.log.info(
                '********************GET*REPLICATION*INFO**************************')
            for database in dbs_in_subclient:
                if 'IN' in step:
                    response = self.cvhelp.return_result_json(
                        'replication info', param=[database])
                else:
                    out_path_database = f'{constants.OUT_PLACE_FOLDER_PATH}-{str(database)}'
                    response = self.cvhelp.return_result_json(
                        'replication info', param=[out_path_database])
                self.log.info(
                    f'Replication status for {database} is {response["property"]}')
                replication_info_after.append(response['property'])
            self.log.info(
                '*******************COMPARE*REPLICATION*INFO***********************')
            chk = 0
            for value in replication_info_after:
                if 'disabled' in value:
                    chk = chk + 1
            if chk < len(dbs_in_subclient):
                self.log.info(f"Test scenario {step} failed")
            else:
                self.log.info(f"Test scenario {step} passed")
                count = count + 1
        #####
        # Step 2
        #####
        self.log.info(
            '*******************LOGS*GETTING*REPLAYED***************************')
        replication_info_before = []
        replication_info_after = []
        doc_count_before = []
        doc_count_after = []
        self.log.info(
            '****************************ENABLE*TR*LOGGING***********************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'change transactional logging', param=[database, 'true'])
            self.cvhelp.return_result_json(
                'console commands', param=['dbcache flush'])
            self.log.info(
                f'Transactional Logging for {database} is {response["TRLogInfo"]}')
        self.log.info(
            '************************ENABLE*REPLICATION**************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'set replication info', param=[database, 'false'])
            self.cvhelp.return_result_json(
                'console commands', param=['dbcache flush'])
            self.log.info(
                f'Replication status for {database} is {response["ReplicationInfo"]}')
            self.log.info(
                '********************GET*REPLICATION*INFO**************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'replication info', param=[database])
            self.log.info(
                f'Replication status for {database} is {response["property"]}')
            replication_info_before.append(response['property'])
        self.cvhelp.run_backup()
        self.log.info(
            '**********************CREATE*DOCUMENTS*******************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'add documents', param=[database, "10"])
            self.log.info(
                f'Total docs for {database} is {response["docCount"]}')
            doc_count_before.append(response['docCount'])
        self.log.info(
            '*******************BACKUP*TR*LOG*SUBCLIENT***************************')
        self.cvhelp.run_backup(
            level='INCREMENTAL',
            subclient=self.tc.trlogsubclient)
        self.log.info(
            '***************************DELETE************************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'delete database', param=[database])
            if 'removed' in response.get('status'):
                self.log.info(f'{database} removal successful')
            else:
                self.log.info(f'{database} removal unsuccessful')
        self.tc.lndb_restore_options = {"disableReplication": True}
        self.tc.common_options_dict = {}
        self.cvhelp.run_restore(type_of_restore='IN')
        self.log.info(
            '********************GET*REPLICATION*INFO**************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'replication info', param=[database])
            self.log.info(
                f'Replication status for {database} is {response["property"]}')
            replication_info_after.append(response['property'])
        self.log.info(
            '************************COLLECT*DOC*PROPERTIES************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'get document properties', param=[database])
            self.log.info(response)
            doc_count_after.append(len(response['documents']))
        self.log.info(
            '***************************COMPARE************************************')
        if doc_count_before == doc_count_after:
            self.log.info(
                f'Number of documents is the same. {doc_count_before}')
            self.log.info('Test scenario PASSED')
            count = count + 1
        else:
            self.log.error(
                'Number of documents is not right. '
                f'Before backup: {doc_count_before} After restore: {doc_count_after}')
            self.log.info('Test scenario FAILED')
        self.log.info(
            '************************TR*LOGS*NOT*REPLAYED*************************')
        self.tc.common_options_dict = {"doNotReplayTransactLogs": True}
        doc_count_after = []
        self.log.info(
            '***************************DELETE************************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'delete database', param=[database])
            if 'removed' in response.get('status'):
                self.log.info(f'{database} removal successful')
            else:
                self.log.info(f'{database} removal unsuccessful')
        self.tc.lndb_restore_options = {"disableReplication": True}
        self.tc.common_options_dict = {"doNotReplayTransactLogs": True}
        self.cvhelp.run_restore(type_of_restore='IN')
        self.log.info(
            '********************GET*REPLICATION*INFO**************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'replication info', param=[database])
            self.log.info(
                f'Replication status for {database} is {response["property"]}')
            replication_info_after.append(response['property'])
            self.log.info(
                '************************COLLECT*DOC*PROPERTIES************************')
        for database in dbs_in_subclient:
            temp = 'OOPRestore_auto-' + str(database)
            response = self.cvhelp.return_result_json(
                'get document properties', param=[temp])
            self.log.info(response)
            doc_count_after.append(len(response['documents']))
            self.log.info(
                '***************************COMPARE************************************')
        if doc_count_before != doc_count_after:
            self.log.info(
                f'Number of documents is not same. {doc_count_before} {doc_count_after}')
            self.log.info('Test scenario PASSED')
            count = count + 1
        else:
            self.log.error(
                'Number of documents is not right. '
                f'Before backup: {doc_count_before} After restore: {doc_count_after}')
            self.log.info('Test scenario FAILED')
        #####
        # Step 3
        #####
        replica_dbs = []
        doc_count_before = []
        doc_count_after = []
        self.tc.common_options_dict = {}
        self.log.info(
            '****************************ENABLE*TR*LOGGING*************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'change transactional logging', param=[database, 'true'])
            self.cvhelp.return_result_json(
                'console commands', param=['dbcache flush'])
            self.log.info(
                f'Transactional Logging for {database} is {response["TRLogInfo"]}')
        self.log.info(
            '****************ENABLE*REPLICATION************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'set replication info', param=[database, 'false'])
            self.cvhelp.return_result_json(
                'console commands', param=['dbcache flush'])
            self.log.info(
                f'Replication status for {database} is {response["ReplicationInfo"]}')
        self.log.info(
            '**********************CREATE*REPLICA*********************')
        for database in dbs_in_subclient:
            try:
                response = self.cvhelp.return_result_json(
                    'create replica', param=[database])
                self.log.info(
                    f'Replication status for {database} is {response["status"]}')
                replica_dbs.append(response['replica name'].replace(self.tc.machine.os_sep, "-"))
            except Exception:
                self.log.info('Replication is disabled for this database')
        self.log.info(
            '*****************************BACKUP*******************************')
        self.cvhelp.run_backup(subclient=self.tc.subclient, level='FULL')
        self.log.info(
            '**********************CREATE*DOCUMENTS*********************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'add documents', param=[database, "10"])
            self.log.info(
                f'Total docs for {database} is {response["docCount"]}')
            doc_count_before.append(response['docCount'])
        self.log.info(
            '**********************BACKUP*TR*LOG*SUBCLIENT**********************')
        self.cvhelp.run_backup(
            level='INCREMENTAL',
            subclient=self.tc.trlogsubclient)
        self.log.info(
            '***************************DELETE************************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'delete database', param=[database])
            if 'removed' in response.get('status'):
                self.log.info(f'{database} removal successful')
            else:
                self.log.info(f'{database} removal unsuccessful')
        self.tc.lndb_restore_options = {"disableReplication": True}
        self.cvhelp.run_restore(type_of_restore='IN')
        self.log.info(
            '**********************CREATE*DOCUMENTS*IN*REPLICTED*DB****************')
        for database in replica_dbs:
            response = self.cvhelp.return_result_json(
                'add documents', param=[database.replace('.nsf', ''), "10"])
            self.log.info(
                f'Total docs for {database} is {response["docCount"]}')
            doc_count_after.append(response['docCount'])
        self.log.info(
            '*********************COLLECT*DOC*PROPERTIES*********************')
        response = self.cvhelp.collect_doc_properties(dbs_in_subclient)
        doc_properties_before = [_['documents'] for _ in response]
        self.log.info(
            '*********************RUN*REPLICATION******************************')
        for database in dbs_in_subclient:
            response = self.cvhelp.return_result_json(
                'replicate', param=[database])
            self.log.info(response)
        self.log.info(
            '*******************COLLECT*REPLICA*PROPERTIES*****************')
        for i, database in enumerate(replica_dbs):
            replica_dbs[i] = database.replace('.nsf', '')
        response = self.cvhelp.collect_doc_properties(replica_dbs)
        doc_properties_after = [_['documents'] for _ in response]
        self.log.info(
            '********************COMPARE*DOC*PROPERTIES********************')
        if doc_properties_before != doc_properties_after:
            self.log.info(
                'Document properties do not match. Hence no replication has occured')
            self.log.info(
                f'Test scenario {"Replication Across Servers"} has passed')
            count = count + 1
        else:
            self.log.info('Document properties match. Replication occured')
            self.log.info('Test scenario has failed')

        if count < 5:
            raise LNException('TestScenario', '101', f'{count}/5')
        else:
            self.tc.pass_count += 1

    def full_data_protection(self):
        """"Verifies full backup for a subclient.

        """
        if self.tc.backupset.subclients.has_subclient(self.tc.tcinputs['SubclientName']):
            self.log.info(self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName']))
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(self.tc.subclient, "1", "10")
        for lndbcontent in self.tc.subclient.content:
            self.tc.dbs_in_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
        self.cvhelp.run_backup(level='FULL')

        browse_paths_dictionary = self.cvhelp.recursive_browse(
            subclient=self.tc.subclient, machine=self.tc.machine)
        self.log.info('dbs_in_subclient:')
        self.log.info(self.tc.dbs_in_subclient)
        self.log.info('browse paths:')
        self.log.info(list(browse_paths_dictionary.keys()))
        if not set(browse_paths_dictionary.keys()) == set(self.tc.dbs_in_subclient):
            self.log.info('Browse failed')
            raise LNException('CVOperation', '101')
        else:
            self.tc.pass_count += 1

    def inc_data_protection(self):
        """"Verifies incremental backups for a subclient

        """
        self.log.info(
            "***********DELETING*PREVIOUS*SUBCLIENT*AND*CREATING*A*NEW*ONE************")
        self.log.info(self.tc.backupset.subclients.delete(self.tc.tcinputs['SubclientName']))
        self.tc.subclient = self.tc.backupset.subclients.add(
            self.tc.tcinputs['SubclientName'], self.tc.tcinputs['StoragePolicy'])
        self.cvhelp.add_database_to_subclient(self.tc.subclient, "2", "10")
        self.log.info('1st Incremental')
        job = self.cvhelp.run_backup(
            subclient=self.tc.subclient,
            level='INCREMENTAL')
        if not job.backup_level == 'Full':
            raise LNException('CVOperation', '102')
        self.log.info('Job converted to FULL as expected')
        self.log.info('2nd Incremental')
        job = self.cvhelp.run_backup(
            subclient=self.tc.subclient,
            level='INCREMENTAL')

        if not job.summary['sizeOfApplication'] == 0:
            raise LNException('CVOperation', '103')
        if job.backup_level == 'Full':
            raise LNException('CVOperation', '104', '(2nd Incremental)')
        self.log.info('Application size is 0 as expected')
        self.log.info('Job not converted to FULL as expected')

        self.tc.dbs_in_subclient = []
        for lndbcontent in self.tc.subclient.content:
            self.tc.dbs_in_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
        self.cvhelp.delete_indexcache(subclient=self.tc.subclient)
        try:
            browse_paths_dictionary = self.cvhelp.recursive_browse(
                subclient=self.tc.subclient, machine=self.tc.machine)
            self.log.info('dbs_in_subclient:')
            self.log.info(self.tc.dbs_in_subclient)
            self.log.info('browse paths:')
            self.log.info(list(browse_paths_dictionary.keys()))
            if not set(browse_paths_dictionary.keys()) == set(self.tc.dbs_in_subclient):
                raise LNException('CVOperation', '101')
            self.log.info(
                'Browse works after IndexCache is deleted as expected')
        except TimeoutException:
            pass

        for database in self.tc.dbs_in_subclient:
            response = self.cvhelp.return_result_json('add documents', param=[database, "10"])
            self.log.info(f'Total docs for {database} is {response["docCount"]}')
        self.log.info('3rd Incremental')
        job = self.cvhelp.run_backup(
            subclient=self.tc.subclient,
            level='INCREMENTAL')
        if job.backup_level == 'Full':
            raise LNException('CVOperation', '104', '(3rd Incremental)')
        self.log.info(
            'Job not converted to FULL after Indexcache deletion as expected')

        self.log.info('4th Incremental')
        job = self.cvhelp.run_backup(
            subclient=self.tc.subclient,
            level='INCREMENTAL')
        if not job.summary['sizeOfApplication'] == 0:
            raise LNException('CVOperation', '103')
        if job.backup_level == 'Full':
            raise LNException('CVOperation', '104', '(4th Incremental)')
        self.log.info('Application size is 0 as expected')
        self.log.info('Job not converted to FULL as expected')

        self.tc.pass_count += 1

    def restores(self):
        """"Verifies in-place and put-place restores for a subclient.
        Requires a subclient to be created beforehand with the appropriate dbs

        """
        self.tc.dbs_in_subclient = []
        for lndbcontent in self.tc.subclient.content:
            self.tc.dbs_in_subclient.append(
                lndbcontent['lotusNotesDBContent']['databaseTitle'])
        test_steps = {'IN PLACE RESTORE', 'OUT PLACE RESTORE'}
        for step in test_steps:
            doc_properties_beforebackup = []
            self.log.info(
                '******************************************************************')
            self.log.info(step)
            self.log.info(
                '*********************COLLECT*DOC*PROPERTIES***********************')
            for database in self.tc.dbs_in_subclient:
                response = self.cvhelp.return_result_json(
                    operation='get document properties',
                    param=[database]
                )
                self.log.info(response)
                doc_properties_beforebackup.append(response.get('documents'))
            self.log.info(
                '***************************BACKUP*******************************')
            self.cvhelp.run_backup()
            self.tc.subclient.backup()
            if 'IN' in step:
                self.cvhelp.delete_db_and_validate(
                    dbsinsubclient=self.tc.dbs_in_subclient)
            else:
                self.cvhelp.remove_restored_dbs(self.tc.dbs_in_subclient, step)
            self.cvhelp.run_restore(step)
            self.log.info(
                '*******************COLLECT*DOC*PROPERTIES*********************')
            browse_paths_dictionary = self.cvhelp.recursive_browse(
                subclient=self.tc.subclient, machine=self.tc.machine)
            for database in self.tc.dbs_in_subclient:
                for browse_path in browse_paths_dictionary[database]:
                    browse_path.replace(self.tc.machine.os_sep, '-')
            response = self.cvhelp.collect_doc_properties(
                self.tc.dbs_in_subclient,
                step,
                browse_paths_dictionary
            )
            doc_properties_afterrestore = [_['documents'] for _ in response]
            self.log.info(
                '*******************COMPARE*DOC*PROPERTIES*********************')
            if doc_properties_beforebackup != doc_properties_afterrestore:
                raise LNException(
                    'DocProperties',
                    '101',
                    f'Before:{doc_properties_beforebackup} | After :{doc_properties_afterrestore}'
                )
            self.log.info('Document properties match')
            self.log.info(f'Test scenario {step} has passed')
            self.tc.pass_count += 1

    def defsubclient_autodiscovery(self):
        """"Verifies auto-discovery feature of the default subclient.
        Requires the subclient to be initialized beforehand

        """
        count = 0
        self.log.info(
            '***********************RUN*BACKUP*DEFAULT*SUBCLIENT*****************************')
        self.cvhelp.run_backup(
            level='FULL',
            subclient=self.tc.default_subclient
        )
        self.log.info(
            '*******************************DATABASES*DEFAULT*SUBCLIENT**********************')
        self.tc.default_subclient.refresh()
        self.tc.dbs_in_default_before = self.cvhelp.remove_extension(
            self.tc.default_subclient.content,
            self.tc.machine.os_info
        )
        self.log.info(f'TOTAL DATABASES IN DEFAULT SUBCLIENT:{len(self.tc.dbs_in_default_before)}')
        self.log.info(
            '***********************************CREATE*NEW*DATABASES*************************')
        jstring = {
            "key":
                [{
                    "template": "notebook9.ntf",
                    "numdb": "2",
                    "numdocs": "10",
                    "numlogs": "null",
                    "dbname": "36903",
                    "trlog": "null",
                    "del": "false"
                }]
        }
        response = self.cvhelp.return_result_json('data populator', jstring=jstring)
        for value in response:
            self.tc.new_dbs_added.append(value.get('name').replace('.nsf', ''))
        self.log.info(response)
        self.tc.default_subclient.refresh()
        self.cvhelp.run_backup(
            level='FULL',
            subclient=self.tc.default_subclient)
        self.log.info(
            '*******************************DATABASES*DEFAULT*SUBCLIENT**********************')
        self.tc.default_subclient.refresh()
        self.tc.dbs_in_default_after = self.cvhelp.remove_extension(
            self.tc.default_subclient.content,
            self.tc.machine.os_info
        )
        self.log.info(f'TOTAL DATABASES IN DEFAULT SUBCLIENT:{len(self.tc.dbs_in_default_after)}')
        if len(self.tc.dbs_in_default_after) > len(self.tc.dbs_in_default_before):
            self.log.info(f"dbs_before: {self.tc. dbs_in_default_before}")
            self.log.info(f"dbs_after: {self.tc.dbs_in_default_after}")
            self.log.info(f'new_dbs_added: {self.tc.new_dbs_added}')
            if not (set(self.tc.dbs_in_default_after) -
                    set(self.tc.dbs_in_default_before)) - set(self.tc.new_dbs_added):
                self.log.info("New databases found by default subclient")
            else:
                self.log.error("New databases not found by default subclient")
        else:
            self.log.error(
                "Number of databases in default subclient after are not more than before")

        self.cvhelp.run_backup(
            subclient=self.tc.default_subclient,
            level="INCREMENTAL")
        self.log.info(
            '*************************************CREATE*DOCUMENTS***************************')
        self.log.info(self.tc.new_dbs_added)
        for database in self.tc.new_dbs_added:
            response = self.cvhelp.return_result_json(
                'add documents',
                param=[database, "10"]
            )
            self.log.info(
                f'Total docs for {database} is {response["docCount"]}')
        self.log.info(
            '***************************BACKUP*TR*LOG*SUBCLIENT******************************')
        self.cvhelp.run_backup(
            level='INCREMENTAL',
            subclient=self.tc.trlogsubclient
        )
        test_steps = ['IN PLACE RESTORE', 'OUT PLACE RESTORE']
        doc_properties_beforebackup = []
        doc_name_beforebackup = []
        for i, database in enumerate(self.tc.dbs_in_default_after):
            self.tc.dbs_in_default_after[i] = database.replace('/', '-')
        self.log.info(
            '*********************COLLECT*DOC*PROPERTIES***********************')
        response = self.cvhelp.collect_doc_properties(
            self.tc.dbs_in_default_after)
        for _ in response:
            if 'error' not in _:
                doc_properties_beforebackup.append(_.get('documents'))
                doc_name_beforebackup.append(_.get('name'))
        for step in test_steps:
            doc_properties_afterrestore = []
            doc_name_afterrestore = []
            self.log.info(
                '******************************************************************')
            self.log.info(step)
            if 'OUT' in step:
                self.cvhelp.remove_restored_dbs(
                    self.tc.dbs_in_default_after, step)

            self.cvhelp.run_restore(
                type_of_restore=step,
                subclient=self.tc.default_subclient)
            self.log.info(
                '*********************COLLECT*DOC*PROPERTIES***********************')
            response = self.cvhelp.collect_doc_properties(
                self.tc.dbs_in_default_after, step)
            for _ in response:
                if 'error' not in _:
                    doc_properties_afterrestore.append(_.get('documents'))
                    doc_name_afterrestore.append(_.get('name'))
            self.log.info(
                '*****************COMPARE*DOC*PROPERTIES*******************')
            print(doc_properties_beforebackup)
            self.log.info(f"before backup: {doc_name_beforebackup}")
            print(doc_properties_afterrestore)
            self.log.info(f"after restore:{doc_name_afterrestore}")
            if doc_properties_beforebackup != doc_properties_afterrestore:
                self.log.error('Document properties do not match')
                self.log.error(f'Test scenario {step} has failed')
            else:
                self.log.info('Document properties match')
                self.log.info(f'Test scenario {step} has passed')
                count += 1

        self.log.info('count:' + str(count))
        if count == 2:
            self.tc.pass_count += 1

    def disaster_recovery(self):
        """"Verifies disaster recovery scenario

        """
        doc_properties_beforebackup = []
        doc_name_beforebackup = []
        doc_properties_afterrestore = []
        doc_name_afterrestore = []
        self.log.info(
            '**************************DISASTER*RECOVERY*SCENARIO****************************')
        self.cvhelp.run_backup(
            level='FULL',
            subclient=self.tc.default_subclient
        )
        self.tc.default_subclient.refresh()
        self.log.info(
            '*******************************CREATE*DOCUMENTS*********************************')
        self.log.info(self.tc.new_dbs_added)
        for database in self.tc.new_dbs_added:
            response = self.cvhelp.return_result_json('add documents', param=[database, "10"])
            self.log.info(f'Total docs for {database} is {response["docCount"]}')
        self.log.info(
            '****************************BACKUP*TR*LOG*SUBCLIENT*****************************')
        self.cvhelp.run_backup('incremental', self.tc.trlogsubclient)
        self.log.info(
            '***********************COLLECT*DOC*PROPERTIES*************************')
        response = self.cvhelp.collect_doc_properties(
            self.tc.dbs_in_default_after)
        for _ in response:
            if 'error' not in _:
                doc_properties_beforebackup.append(_.get('documents'))
                doc_name_beforebackup.append(_.get('name'))
        self.cvhelp.remove_restored_dbs(self.tc.new_dbs_added)
        self.log.info(
            '********************************CHANGE*NOTES.INI*******************************')
        self.cvhelp.edit_notes_ini('TRANSLOG_RECREATE_LOGCTRL=1')
        time.sleep(30)
        self.log.info(
            '**************************************RENAME*LOGDIR*****************************')
        self.cvhelp.rename_logdir()
        self.log.info(
            '*************************************DR*RESTORE*********************************')
        self.tc.common_options_dict = {
            'disasterRecovery': True,
            'unconditionalOverwrite': True
        }
        job = self.cvhelp.run_restore(subclient=self.tc.default_subclient, interrupt=True)
        while job.status == 'Running':
            continue
        if job.status == 'Pending':
            time.sleep(300)
            job.kill()
        self.log.info(
            '**********************************BRINGING*UP*DOMINO****************************')
        self.cvhelp.start_domino()
        self.log.info('Wait for 2 mins before further processing')
        time.sleep(120)
        self.log.info(
            '***********************COLLECT*DOC*PROPERTIES*************************')
        response = self.cvhelp.collect_doc_properties(self.tc.dbs_in_default_after)
        for _ in response:
            if 'error' not in _:
                doc_properties_afterrestore.append(_.get('documents'))
                doc_name_afterrestore.append(_.get('name'))
        self.log.info(
            '***********************COMPARE*DOC*PROPERTIES*************************')
        self.log.debug(doc_properties_beforebackup)
        self.log.debug(f"before backup: {doc_name_beforebackup}")
        self.log.debug(doc_properties_afterrestore)
        self.log.debug(f"after restore:{doc_name_afterrestore}")
        if doc_properties_beforebackup != doc_properties_afterrestore:
            self.log.error('Document properties do not match')
            self.log.error(f'Test scenario DISASTER RECOVERY has failed')
        else:
            self.log.info('Document properties match')
            self.tc.pass_count += 1
            self.log.info(f'Test scenario DISASTER RECOVERY has passed')

    def tr_log_backup_with_indexing(self):
        """"Verifies tr log backup job with indexing
        Requires the subclient to be initialized beforehand

        """
        self.log.info(
            '***********************BACKUP*TR*LOG*SUBCLIENT************************')
        job = self.tc.trlogsubclient.backup('FULL')
        self.log.info(job)
        self.log.info(
            '***************SUSPEND*TR*LOG*BACKUP*JOB******************************')
        job.pause()
        time.sleep(15)
        self.log.info(job.status)
        self.log.info("Will pause job for 30 secs")
        time.sleep(30)
        self.log.info(
            '************RESUME*TR*LOG*BACKUP*JOB**********************************')
        job.resume(True)
        self.log.info(job.status)
        time.sleep(30)
        self.log.info(
            '***************SUSPEND*TR*LOG*BACKUP*JOB******************************')
        if job.status == 'Completed':
            job = self.tc.trlogsubclient.backup()
        job.pause()
        time.sleep(15)
        self.log.info(job.status)
        self.log.info("Will pause job for 30 secs")
        time.sleep(30)
        self.log.info(
            '***********************RESET*SERVICES*ON*CLIENT***********************')
        self.tc.client.restart_services()
        self.log.info('Services restarted successfully')
        self.log.info(
            '************RESUME*TR*LOG*BACKUP*JOB**********************************')
        job.resume(True)
        self.log.info(job.status)
        job.wait_for_completion()
        try:
            path, dictionary = self.tc.trlogsubclient.browse()
        except BrowseException:
            path = self.tc.machine.os_sep
        try:
            job = self.tc.trlogsubclient.restore_in_place(
                paths=path,
                lndb_restore_options=self.tc.lndb_restore_options,
                common_options_dict=self.tc.common_options_dict)
            time.sleep(60)
        except InvalidJobException:
            self.log.info("TR log jobs cannot be restored independently")
            self.log.info("Test scenario PASSED")
            job.kill()
            self.tc.pass_count += 1
        if 'Pending' in job.status:
            self.log.info("TR log jobs cannot be restored independently")
            self.log.info("Test scenario PASSED")
            job.kill()
            self.tc.pass_count += 1
        else:
            self.log.info(
                "Tried to restore TR logs individually. Test scenario FAILED")
            raise LNException('CVOperations', '105')

    def backup_many_tr_logs(self):
        """"Verifies data protection with a large number of tr logs.


        """
        self.cvhelp.run_backup()
        dbname = self.cvhelp.add_database_to_subclient(
            self.tc.subclient, "2", "1000", "null", "auto_50919"
        )
        dbname = dbname[0]
        self.cvhelp.run_backup()
        response = self.cvhelp.return_result_json('add documents', param=[dbname, "10"])
        self.log.info(response)
        self.log.info(f'Total docs for {dbname} is {response.get("docCount")}')
        doc_count_before = response.get("docCount")
        self.log.info(
            '**********************BACKUP*TR*LOG*SUBCLIENT*************************')
        self.cvhelp.run_backup(subclient=self.tc.trlogsubclient)
        self.log.info(
            '************************CLEAN*UP*TR*LOG*FOLDER************************')
        self.cvhelp.return_result_json(operation='console commands',
                                       param=['restart server'])
        time.sleep(120)
        self.cvhelp.check_if_domino_up()
        self.cvhelp.delete_db_and_validate(dbsinsubclient=[dbname])
        self.cvhelp.run_restore()
        response = self.cvhelp.return_result_json(
            'get document properties', param=[dbname])
        self.log.info(
            f'Total docs for {dbname} is {len(response.get("documents"))}')
        doc_count_after = len(response.get('documents'))
        if doc_count_before == doc_count_after:
            self.log.info('Test scenario PASSED')
            self.tc.pass_count += 1
        else:
            raise LNException(
                'DocProperties',
                '101',
                f'Before: {doc_count_before} || After : {doc_count_after}'
            )

    def backup_many_databases(self):
        """"Verifies data protection with a large number of databases.

        """
        self.cvhelp.run_backup(
            level='FULL',
            subclient=self.tc.default_subclient)
        self.tc.default_subclient.refresh()
        new_dbs_added = []
        dbs_in_default_before = []
        doc_count_before = []
        self.log.info(
            '********************CREATE*1000*DATABASES*****************************')
        jstring = {
            "key":
                [{
                    "template": "notebook9.ntf",
                    "numdb": "1000",
                    "numdocs": "1",
                    "numlogs": "null",
                    "dbname": "50919",
                    "trlog": "true",
                    "del": "false",
                    "incremental": "true"
                }]
        }
        response = self.cvhelp.return_result_json('data populator', jstring=jstring)
        for value in response:
            new_dbs_added.append(value.get('name').replace('.nsf', ''))
        self.log.info(response)
        self.log.info(
            f"TOTAL DATABASES IN DEFAULT SUBCLIENT BEFORE: {len(dbs_in_default_before)}")
        self.log.info(
            '*******************RUN*BACKUP*DEFAULT*SUBCLIENT***********************')
        self.cvhelp.run_backup(subclient=self.tc.default_subclient)
        self.log.info(
            '********************DATABASES*DEFAULT*SUBCLIENT***********************')
        self.tc.default_subclient.refresh()
        for lndbcontent in self.tc.default_subclient.content:
            database = lndbcontent['lotusNotesDBContent']['databaseTitle']
            dbs_in_default_before.append(database)
        self.log.info(
            f"TOTAL DATABASES IN DEFAULT SUBCLIENT AFTER: {len(dbs_in_default_before)}")
        if set(new_dbs_added).issubset(set(dbs_in_default_before)):
            self.log.info('New databases found by the default subclient')
        else:
            raise LNException('CVOperation', '106')
        for database in new_dbs_added:
            response = self.cvhelp.return_result_json('add documents', param=[database, "10"])
            self.log.info(
                f'Total docs for {database} is {response["docCount"]}')
            doc_count_before.append(response['docCount'])
        self.log.info(
            '*******************BACKUP*TR*LOG*SUBCLIENT****************************')
        self.cvhelp.run_backup('INCREMENTAL', self.tc.trlogsubclient)
        self.log.info(
            '*********************CLEAN*UP*TR*LOG*FOLDER***************************')
        self.cvhelp.return_result_json('console commands', param=['restart server'])
        time.sleep(120)
        self.cvhelp.check_if_domino_up()
        self.cvhelp.delete_db_and_validate(dbsinsubclient=new_dbs_added)
        self.cvhelp.run_restore(subclient=self.tc.default_subclient)
        self.log.info(
            '*********************COLLECT*DOC*PROPERTIES***************************')
        response = self.cvhelp.collect_doc_properties(new_dbs_added)
        doc_count_after = [len(_['documents']) for _ in response]
        if doc_count_before == doc_count_after:
            self.log.info('Test scenario PASSED')
            self.tc.pass_count += 1
        else:
            raise LNException(
                'DocProperties',
                '101',
                f'Before: {doc_count_before} || After : {doc_count_after}'
            )
        self.log.info(
            '****************CLEAN*UP*EXTRA*DATABASES*CREATED**********************')
        self.cvhelp.delete_db_and_validate(dbsinsubclient=new_dbs_added)

    def osc_schedule_backup(self):
        """"Verifies osc scheduler triggered backups.

        """
        schedule_pattern = {
            "schedule_name": "osc_test_automation",
            "freq_type": "automatic",
            "min_interval_hours": constants.OSC_MIN_HOURS,
            "min_interval_minutes": constants.OSC_MIN_MINS,
            "max_interval_hours": constants.OSC_MAX_HOURS,
            "max_interval_minutes": constants.OSC_MAX_MINS
        }
        self.log.info(
            '***********************BACKUP*TR*LOG*SUBCLIENT************************')
        self.cvhelp.run_backup(
            level='INCREMENTAL',
            subclient=self.tc.trlogsubclient,
            schedule_pattern=schedule_pattern
        )
        time.sleep(10)
        self.tc.trlogsubclient.refresh()
        if not self.tc.trlogsubclient.schedules.has_schedule(
                "osc_test_automation"):
            raise LNException('CVoperation', '107')
        else:
            self.log.info('Schedule creation successful')
        self.tc.client.restart_services()
        time.sleep(constants.OSC_MAX_MINS * 60)
        job_dict = self.tc.commcell.job_controller.all_jobs(
            lookup_time=constants.OSC_MAX_MINS / 60)
        if job_dict:
            job = self.tc.commcell.job_controller.get(list(job_dict.keys())[0])
            if job.details['jobDetail']['generalInfo']['jobStartedFrom'] == 'Scheduled':
                self.log.info('Job ran successfully')
                self.log.info('Test Scenario PASSED')
                self.tc.pass_count += 1
                self.tc.trlogsubclient.refresh()
                self.tc.trlogsubclient.schedules.delete("osc_test_automation")
            else:
                self.tc.trlogsubclient.refresh()
                self.tc.trlogsubclient.schedules.delete("osc_test_automation")
                raise LNException('CVOperation', '108')
        else:
            self.tc.trlogsubclient.refresh()
            self.tc.trlogsubclient.delete("osc_test_automation")
            raise LNException('CVOperation', '109')
