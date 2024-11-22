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
    """Class for executing Basic acceptance test of Lotus Notes backup Template File test case"""

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
        self.name = "Basic acceptance test of Lotus Notes backup Template File test case"
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
        #pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        try:
            self.log.info(self.subclient.content)
            dbs_in_subclient = []
            doc_properties_beforebackup = []
            doc_properties_afterrestore = []
            for lndbcontent in self.subclient.content:
                if 'ntf' not in lndbcontent['lotusNotesDBContent']['relativePath']:
                    self.log.error(
                        "{} not a template.".format(
                            lndbcontent['lotusNotesDBContent']['relativePath']))
                else:
                    dbs_in_subclient.append(lndbcontent['lotusNotesDBContent']['relativePath'])

            if dbs_in_subclient:
                for database in dbs_in_subclient:
                    self.log.info('Database: ' + database)
                test_steps = {'IN PLACE RESTORE',
                              'OUT PLACE RESTORE'}
                count = 0
                for step in test_steps:
                    self.log.info('**************************************************************')
                    self.log.info(step)
                    self.log.info('*******************COLLECT*DOC*PROPERTIES*********************')
                    for database in dbs_in_subclient:
                        response = self.helper.return_result_json(
                            self, 'get document properties', param=[database])
                        self.log.info(response)
                        doc_properties_beforebackup.append(response.get('documents'))
                    self.helper.run_backup(testcase=self, level='FULL', sc=None)
                    if 'IN' in step:
                        self.helper.delete_db_and_validate(
                            testcase=self, dbsinsubclient=dbs_in_subclient)
                        self.helper.run_restore(testcase=self)
                    else:
                        temp_dbs_in_subclient = []
                        for database in dbs_in_subclient:
                            temp_dbs_in_subclient.append('OOPRestore_auto-' + str(database))
                        self.helper.delete_db_and_validate(
                            testcase=self, dbsinsubclient=temp_dbs_in_subclient)
                        self.helper.run_restore(testcase=self, type_of_restore='out')
                        self.log.info('****************COLLECT*DOC*PROPERTIES********************')
                    for database in dbs_in_subclient:
                        if 'IN' in step:
                            response = self.helper.return_result_json(
                                self, 'get document properties', param=[database])
                        else:
                            temp = 'OOPRestore_auto-' + str(database)
                            response = self.helper.return_result_json(
                                self, 'get document properties', param=[temp])
                        self.log.info(response)
                        doc_properties_afterrestore.append(response.get('documents'))
                        self.log.info('*****************COLLECT*DOC*PROPERTIES*******************')
                    answer = []
                    if doc_properties_beforebackup != doc_properties_afterrestore:
                        self.log.error('Document properties do not match')
                        self.log.error('Test scenario {} has failed'.format(step))
                        self.log.error(answer)
                        raise Exception('Document properties do not match')
                    else:
                        self.log.info('Document properties match')
                        self.log.info('Test scenario {} has passed'.format(step))
                        count = count + 1
                if count < 2:
                    raise Exception("Only {} test scenario(s) passed".format(count))
                else:
                    self.status = constants.PASSED
            else:
                self.log.error("Subclient does not contain any template file.")
                raise Exception("Subclient does not contain any template file.")
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(type(ex).__name__,
                                                                  sys.exc_info()[-1].tb_lineno,
                                                                  ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
    #     # delete subclient here
    #     # delete docs folder, label dict folder and message property folder
