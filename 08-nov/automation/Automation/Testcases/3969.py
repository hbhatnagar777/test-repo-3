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
    """Class for executing Basic acceptance test of Notes Database
    "no transaction logging" option"""

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
        self.name = "Basic acceptance test of Notes Database 'no transaction logging' option"
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
            self.log.error('Error {} on line {}. Error {}'.format(type(ex).__name__,
                                                                  sys.exc_info()[-1].tb_lineno,
                                                                  ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(self.subclient.content)
            dbs_in_subclient = []
            trlog_info_before = []
            trlog_info_after = []
            doc_count_before = []
            new_doc_count = []
            doc_count_after = []
            count = 0
            for lndbcontent in self.subclient.content:
                dbs_in_subclient.append(lndbcontent['lotusNotesDBContent']['databaseTitle'])
            for database in dbs_in_subclient:
                self.log.info('Database: ' + database)
            self.log.info('************************GET*TR*LOGGING*INFO***************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'transactional logging', param=[database])
                self.log.info(
                    'Transactional Logging for {} is {}'.format(
                        database, response['logging']))
                trlog_info_before.append(response['logging'])
            self.log.info('*********************CHANGE*TR*LOGGING*INFO***************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'change transactional logging', param=[database, 'false'])
                self.helper.return_result_json(self, 'console commands', param=['dbcache flush'])
                self.log.info(
                    'Transactional Logging for {} is {}'.format(
                        database, response['TRLogInfo']))
            self.log.info('************************GET*TR*LOGGING*INFO***************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'transactional logging', param=[database])
                self.log.info(
                    'Transactional Logging for {} is {}'.format(
                        database, response['logging']))
                trlog_info_after.append(response['logging'])
            self.helper.run_backup(self)
            self.log.info(self.subclient.content)
            self.common_options_dict = {'unconditionalOverwrite': True}
            self.helper.run_restore(self, 'in')
            self.log.info('***************************CREATE*DOCUMENTS***************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'add documents', param=[database, "10"])
                self.log.info('Total docs for {} is {}'.format(database, response['docCount']))
            self.log.info('************************COLLECT*DOC*PROPERTIES*************************')
            for database in dbs_in_subclient:
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[database])
                self.log.info(response)
                doc_count_before = len(response['documents'])
            trlogsubclient = self.backupset.subclients.get('transaction logs')
            self.log.info('*************************BACKUP*TR*LOG*SUBCLIENT**********************')
            self.helper.run_backup(self, level='INCREMENTAL', sc=trlogsubclient)
            self.log.info('***********************DELETE*IN*OUTPLACE*FOLDER**********************')
            for database in dbs_in_subclient:
                temp = 'OOPRestore_auto-' + str(database)
                response = self.helper.return_result_json(self, 'delete database', param=[temp])
                if 'removed' in response.get('status'):
                    self.log.info('{} removal successful'.format(database))
                elif 'not' in response.get('status'):
                    self.log.info('{} {}'.format(database, response.get('status')))
                else:
                    self.log.info('{} removal unsuccessful'.format(database))
            self.log.info('*************************VALIDATE**DELETE*****************************')
            for database in dbs_in_subclient:
                temp = 'OOPRestore_auto-' + str(database)
                response = self.helper.return_result_json(self, 'delete database', param=[temp])
                self.log.info('{} {}'.format(database, response.get('status')))

            self.helper.run_restore(self, 'out')
            self.log.info('************************COLLECT*DOC*PROPERTIES************************')
            for database in dbs_in_subclient:
                temp = 'OOPRestore_auto-' + str(database)
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[temp])
                self.log.info(response)
                new_doc_count = len(response['documents'])
            self.log.info('*****************************COMPARE**********************************')
            if doc_count_before == new_doc_count:
                self.log.error('Number of documents is the same. {}'.format(doc_count_before))
                self.log.info('Test scenario FAILED')
                raise Exception('Number of documents is the same. {}'.format(doc_count_before))
            elif doc_count_before > new_doc_count:
                self.log.info('Number of documents before tr log backup '
                              'is the greater than restored. {}'
                              .format(doc_count_before - new_doc_count))
                self.log.info('Test scenario PASSED')
                count = count + 1
            else:
                self.log.error('Number of documents is not right. '
                               'DocCount before backup: {} DocCount after restore: {}'
                               .format(doc_count_before, new_doc_count))
                self.log.info('Test scenario FAILED')
                raise Exception('Number of documents is not right.'
                                'DocCount before backup: {} DocCount after restore: {}'
                                .format(doc_count_before, new_doc_count))

            self.helper.run_backup(self, 'INCREMENTAL')
            self.helper.run_restore(self, 'out')
            self.log.info('************************COLLECT*DOC*PROPERTIES************************')
            for database in dbs_in_subclient:
                temp = 'OOPRestore_auto-' + str(database)
                response = self.helper.return_result_json(
                    self, 'get document properties', param=[temp])
                self.log.info(response)
                doc_count_after = len(response['documents'])
                self.log.info('***************************COMPARE********************************')
            if doc_count_before == doc_count_after:
                self.log.info('Number of documents is the same. {}'.format(doc_count_before))
                self.log.info('Test scenario PASSED')
                count = count + 1
            elif doc_count_before > doc_count_after:
                self.log.error(
                    'Number of documents is not right. '
                    'DocCount before backup: {} DocCount after restore: {}'
                    .format(doc_count_before, doc_count_after))
                self.log.info('Test scenario FAILED')
                raise Exception(
                    'Number of documents is not right.'
                    'DocCount before backup: {} DocCount after restore: {}'
                    .format(doc_count_before, doc_count_after))
            else:
                self.log.error(
                    'Number of documents is not right. '
                    'DocCount before backup: {} DocCount after restore: {}'.format(
                        doc_count_before,
                        doc_count_after))
                self.log.info('Test scenario FAILED')
                raise Exception(
                    'Number of documents is not right.'
                    'DocCount before backup: {} DocCount after restore: {}'
                    .format(doc_count_before, doc_count_after))
            if count == 2:
                self.result_string = str('Test case passed')
                self.status = constants.PASSED
            else:
                self.result_string = str('Only {} test scenarios passed'.format(count))
                self.status = constants.FAILED
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
    #     # delete subclient here
    #     # delete docs folder, label dict folder and message property folder
