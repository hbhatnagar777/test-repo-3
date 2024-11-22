# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import json
import sys
import requests
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from NotesDatabase.cvrest_helper import CVRestHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Lotus Notes
     'Disable Replication'  option test case"""

    # pylint: disable=too-many-instance-attributes
    # Sixteen is reasonable in this case.

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name                    (str)           --  name of this test case

                applicable_os           (str)           --  applicable os for this test case

                    Ex: self.os_list.WINDOWS

                product                 (str)           --  applicable product for this test case

                    Ex: self.products_list.FILESYSTEM

                features                (str)           --  qcconstants feature_list item

                    Ex: self.features_list.DATAPROTECTION

                show_to_user            (bool)          --  test case flag to determine if the test case is
                to be shown to user or not

                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

                tcinputs                (dict)          --  dict of test case inputs with input name as dict key
                and value as input type

                    Ex: {
                         "MY_INPUT_NAME": None
                    }

                common_optons_dict      (dict)          --  common options for this testcase

                lndb_restore_options    (dict)          --  options particular for notes database restore

                domino_data_path        (str)           --  path to the domino data directory

                helper                  (CVRestHelper)  --  Object of cvrest helper

                rest_ops                (dict)          --  dictionary of rest services enabled on domino server

                log                     (object)        --  Object of the logger module
        """
        super(TestCase, self).__init__()
        self.name = "Basic acceptance test of Lotus Notes 'Disable Replication' option"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LOTUSNOTESDB
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

        self.tcinputs = {
            "ClientName": None,
            "SubclientName": None,
            "DominoServerHostName": None,
            "DominoNotesUser": None,
            "DominoNotesPassword": None,
            "AgentName": "Notes Database",
            "InstanceName": None,
            "BackupsetName": "defaultbackupset"
        }
        self.common_options_dict = {}
        self.lndb_restore_options = {}
        self.domino_data_path = None
        self.helper = None
        self.rest_ops = None

    def setup(self):
        """Setup function of this test case"""
        self.helper = CVRestHelper()
        try:
            self.log.info('Checking if server is up...')
            response = requests.get('http://' + self.tcinputs.get("DominoServerHostName"))
            self.log.info(response.status_code)
            self.log.info('Checking if cvrest api exists...')
            response = requests.get(
            	'http:///api'.format(self.tcinputs.get("DominoServerHostName")))
            self.log.info(response.status_code)
            self.rest_ops = json.loads(response.text)
            self.rest_ops = self.rest_ops.get('services')
            if not any(d['name'] == 'CVRestApi' for d in self.rest_ops):
                raise Exception('CVRestAPI not present on this domino server')
            else:
                if not any(d['name'] == 'CVRestApi' and d['enabled']
                           for d in self.rest_ops):
                    raise Exception('CVRestAPI not enabled on this domino server')
            self.rest_ops = self.helper.get_all_apis(self)
            self.log.info('List of rest services:')
            for i in self.rest_ops:
                self.log.info(self.rest_ops[i])
            response = self.helper.return_result_json(
                self, 'notes setting', param=['Directory'])
            self.domino_data_path = response['Directory']
            self.log.info('Domino Data Directory is located at {}'.format(self.domino_data_path))
        except requests.ConnectionError:
            self.log.error("Either the domino server or http services on domino server are down")
            self.result_string = str(
                "Either the domino server or http services on domino server are down")
            self.status = constants.FAILED
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(self.subclient.content)
            dbs_in_subclient = []
            for lndbcontent in self.subclient.content:
                dbs_in_subclient.append(lndbcontent['lotusNotesDBContent']['databaseTitle'])
            for database in dbs_in_subclient:
                self.log.info('Database: ' + database)
            count = 0
            #####
            # Step 1
            #####
            self.log.info('*****************************REGULAR*SETUP****************************')
            test_steps = {'IN PLACE RESTORE': 'in',
                          'OUT PLACE RESTORE': 'out'}
            replication_info_before = []
            self.log.info('********************ENABLE*REPLICATION********************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'set replication info', param=[database, 'false'])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['ReplicationInfo']))
                self.helper.return_result_json(self, 'console commands', param=['dbcache flush'])
            self.log.info('**********************GET*REPLICATION*INFO****************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'replication info', param=[database])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['property']))
                replication_info_before.append(response['property'])
            self.helper.run_backup(self)
            self.lndb_restore_options = {"disableReplication": True}
            for step in test_steps:
                replication_info_after = []
                self.common_options_dict = {'unconditionalOverwrite': True}
                self.helper.run_restore(self, test_steps[step])
                self.log.info('********************GET*REPLICATION*INFO**************************')
                for database in dbs_in_subclient:
                    if 'in' in test_steps[step]:
                        response = self.helper.return_result_json(
                            self, 'replication info', param=[database])
                    else:
                        temp = 'OOPRestore_auto-' + str(database)
                        response = self.helper.return_result_json(
                            self, 'replication info', param=[temp])
                    self.log.info(
                        'Replication status for {} is {}'.format(
                            database, response['property']))
                    replication_info_after.append(response['property'])
                self.log.info('*******************COMPARE*REPLICATION*INFO***********************')
                chk = 0
                for value in replication_info_after:
                    if 'disabled' in value:
                        chk = chk + 1
                if chk < len(dbs_in_subclient):
                    self.log.info("Test scenario {} failed".format(step))
                else:
                    self.log.info("Test scenario {} passed".format(step))
                    count = count + 1
            #####
            # Step 2
            #####
            self.log.info('*******************LOGS*GETTING*REPLAYED***************************')
            replication_info_before = []
            replication_info_after = []
            doc_count_before = []
            doc_count_after = []
            self.log.info('****************************ENABLE*TR*LOGGING***********************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'change transactional logging', param=[database, 'true'])
                self.helper.return_result_json(self, 'console commands', param=['dbcache flush'])
                self.log.info(
                    'Transactional Logging for {} is {}'.format(
                        database, response['TRLogInfo']))
            self.log.info('************************ENABLE*REPLICATION**************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'set replication info', param=[database, 'false'])
                self.helper.return_result_json(self, 'console commands', param=['dbcache flush'])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['ReplicationInfo']))
                self.log.info('********************GET*REPLICATION*INFO**************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'replication info', param=[database])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['property']))
                replication_info_before.append(response['property'])
            self.helper.run_backup(self)
            self.log.info('**********************CREATE*DOCUMENTS*******************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'add documents', param=[database, "10"])
                self.log.info('Total docs for {} is {}'.format(database, response['docCount']))
                doc_count_before.append(response['docCount'])
            trlogsubclient = self.backupset.subclients.get('transaction logs')
            self.log.info('*******************BACKUP*TR*LOG*SUBCLIENT***************************')
            self.helper.run_backup(self, level='INCREMENTAL', sc=trlogsubclient)
            self.log.info('***************************DELETE************************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'delete database', param=[database])
                if 'removed' in response.get('status'):
                    self.log.info('{} removal successful'.format(database))
                else:
                    self.log.info('{} removal unsuccessful'.format(database))
            self.lndb_restore_options = {"disableReplication": True}
            self.common_options_dict = {}
            self.helper.run_restore(self, type_of_restore='in')
            self.log.info('********************GET*REPLICATION*INFO**************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'replication info', param=[database])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['property']))
                replication_info_after.append(response['property'])
            self.log.info('************************COLLECT*DOC*PROPERTIES************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[database])
                self.log.info(response)
                doc_count_after.append(len(response['documents']))
            self.log.info('***************************COMPARE************************************')
            if doc_count_before == doc_count_after:
                self.log.info('Number of documents is the same. {}'.format(doc_count_before))
                self.log.info('Test scenario PASSED')
                count = count + 1
            else:
                self.log.error('Number of documents is not right. '
                               'DocCount before backup: {} DocCount after restore: {}'
                               .format(doc_count_before, doc_count_after))
                self.log.info('Test scenario FAILED')
            self.log.info('************************TR*LOGS*NOT*REPLAYED*************************')
            self.common_options_dict = {"doNotReplayTransactLogs": True}
            doc_count_after = []
            self.log.info('***************************DELETE************************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'delete database', param=[database])
                if 'removed' in response.get('status'):
                    self.log.info('{} removal successful'.format(database))
                else:
                    self.log.info('{} removal unsuccessful'.format(database))
            self.lndb_restore_options = {"disableReplication": True}
            self.common_options_dict = {"doNotReplayTransactLogs": True}
            self.helper.run_restore(self, type_of_restore='in')
            self.log.info('********************GET*REPLICATION*INFO**************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'replication info', param=[database])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['property']))
                replication_info_after.append(response['property'])
                self.log.info('************************COLLECT*DOC*PROPERTIES************************')
            for database in dbs_in_subclient:
                temp = 'OOPRestore_auto-' + str(database)
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[temp])
                self.log.info(response)
                doc_count_after.append(len(response['documents']))
                self.log.info('***************************COMPARE************************************')
            if doc_count_before != doc_count_after:
                self.log.info(
                    'Number of documents is not same. {} {}'.format(
                        doc_count_before, doc_count_after))
                self.log.info('Test scenario PASSED')
                count = count + 1
            else:
                self.log.error('Number of documents is not right. '
                               'DocCount before backup: {} DocCount after restore: {}'
                               .format(doc_count_before, doc_count_after))
                self.log.info('Test scenario FAILED')
            #####
            # Step 3
            #####
            replica_dbs = []
            doc_count_before = []
            doc_count_after = []
            doc_properties_before = []
            doc_properties_after = []
            self.common_options_dict = {}
            self.log.info('****************************ENABLE*TR*LOGGING*************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'change transactional logging', param=[database, 'true'])
                self.helper.return_result_json(self, 'console commands', param=['dbcache flush'])
                self.log.info(
                    'Transactional Logging for {} is {}'.format(
                        database, response['TRLogInfo']))
            self.log.info('****************ENABLE*REPLICATION************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'set replication info', param=[database, 'false'])
                self.helper.return_result_json(self, 'console commands', param=['dbcache flush'])
                self.log.info(
                    'Replication status for {} is {}'.format(
                        database, response['ReplicationInfo']))
            self.log.info('**********************CREATE*REPLICA*********************')
            for database in dbs_in_subclient:
                try:
                    response = self.helper.return_result_json(
                        self, 'create replica', param=[database])
                    self.log.info(
                        'Replication status for {} is {}'.format(
                            database, response['status']))
                    replica_dbs.append(response['replica name'].replace("\\", "-"))
                except Exception:
                    self.log.info('Replication is disabled for this database')
            self.helper.run_backup(self)
            self.log.info('**********************CREATE*DOCUMENTS*********************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'add documents', param=[database, "10"])
                self.log.info('Total docs for {} is {}'.format(database, response['docCount']))
                doc_count_before.append(response['docCount'])
            trlogsubclient = self.backupset.subclients.get('transaction logs')
            self.log.info('**********************BACKUP*TR*LOG*SUBCLIENT**********************')
            self.helper.run_backup(self, level='INCREMENTAL', sc=trlogsubclient)
            self.log.info('***************************DELETE************************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'delete database', param=[database])
                if 'removed' in response.get('status'):
                    self.log.info('{} removal successful'.format(database))
                else:
                    self.log.info('{} removal unsuccessful'.format(database))
            self.lndb_restore_options = {"disableReplication": True}
            self.helper.run_restore(self, type_of_restore='in')
            self.log.info('**********************CREATE*DOCUMENTS*IN*REPLICTED*DB****************')
            for database in replica_dbs:
                response = self.helper.return_result_json(self, 'add documents',
                                                          param=[database.replace('.nsf', ''),
                                                                 "10"])
                self.log.info('Total docs for {} is {}'.format(database, response['docCount']))
                doc_count_after.append(response['docCount'])
                self.log.info('*********************COLLECT*DOC*PROPERTIES*********************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[database])
                self.log.info(response)
                doc_properties_before.append(response.get('documents'))
            self.log.info('*********************RUN*REPLICATION******************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(self, 'replicate', param=[database])
                self.log.info(response)
            self.log.info('*******************COLLECT*REPLICA*PROPERTIES*****************')
            for database in replica_dbs:
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[
                        database.replace(
                            '.nsf', '')])
                self.log.info(response)
                doc_properties_after.append(response.get('documents'))
            self.log.info('********************COMPARE*DOC*PROPERTIES********************')
            if doc_properties_before != doc_properties_after:
                self.log.info('Document properties do not match. Hence no replication has occured')
                self.log.info('Test scenario {} has passed'.format('Replication Across Servers'))
                count = count + 1
            else:
                self.log.info('Document properties match. Replication occured')
                self.log.info('Test scenario has failed')

            if count < 5:
                raise Exception("Only {} out of 5 test scenario(s) passed".format(count))
            else:
                self.status = constants.PASSED
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
    #     # delete subclient here
    #     # delete docs folder, label dict folder and message property folder
        self.common_options_dict = {'unconditionalOverwrite': True}
        self.lndb_restore_options = {"disableReplication": False}
        self.helper.run_restore(self, type_of_restore='in')
