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


import time
import json
import sys
import requests
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from NotesDatabase.cvrest_helper import CVRestHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Lotus Notes backup and Restore test case"""

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

                machine                 (MAchine)       --  Object of machine class

                rest_ops                (dict)          --  dictionary of rest services enabled on domino server

                log                     (object)        --  Object of the logger module
        """
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Lotus Notes backup and restore"
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
        self.machine = None
        self.rest_ops = None

    def setup(self):
        """Setup function of this test case"""

        self.helper = CVRestHelper()
        self.machine = Machine(machine_name=self.client.client_name, commcell_object=self.commcell)
        try:
            self.log.info('Checking if server is up...')
            response = requests.get('http://' + self.tcinputs.get("DominoServerHostName"))
            self.log.info(response.status_code)
            self.log.info('Checking if cvrest api exists...')
            response = requests.get('http://{}/api'.format(self.tcinputs.get(
            	"DominoServerHostName")))
            self.log.info(response.status_code)
            self.rest_ops = json.loads(response.text)
            self.rest_ops = self.rest_ops.get('services')
            if not any(d['name'] == 'CVRestApi' for d in self.rest_ops):
                raise Exception('CVRestAPI not present on this domino server')
            else:
                if not any(d['name'] == 'CVRestApi' and d['enabled']
                           for d in self.rest_ops):
                    raise Exception('CVRestAPI not enabled on this domino server')
            self.rest_ops = self.helper.get_all_apis(testcase=self)
            self.log.info('List of rest services:')
            for i in self.rest_ops:
                self.log.info(self.rest_ops[i])
            response = self.helper.return_result_json(
            	testcase=self,
            	operation='notes setting',
            	param=['Directory']
            )
            self.domino_data_path = response['Directory']
            self.log.info('Domino Data Directory is located at {}'.format(self.domino_data_path))
        except requests.ConnectionError:
            self.log.error("Either the domino server or " +
            	"http services on domino server are down")
            self.result_string = str("Either the domino server or " +
            	"http services on domino server are down")
            self.status = constants.FAILED
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
            	type(ex).__name__,
                sys.exc_info()[-1].tb_lineno,
                ex))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(self.subclient.content)
            dbs_in_subclient = []
            browse_paths_dictionary = {}
            for lndbcontent in self.subclient.content:
                dbs_in_subclient.append(lndbcontent['lotusNotesDBContent']['databaseTitle'])
            for database in dbs_in_subclient:
                self.log.info('Database: ' + database)
            test_steps = {'IN PLACE RESTORE', 'OUT PLACE RESTORE'}
            count = 0
            for step in test_steps:
                doc_properties_beforebackup = []
                doc_properties_afterrestore = []
                self.log.info('******************************************************************')
                self.log.info(step)
                self.log.info('*********************COLLECT*DOC*PROPERTIES***********************')
                for database in dbs_in_subclient:
                    response = self.helper.return_result_json(
                    	testcase=self,
                        operation='get document properties',
                        param=[database]
                    )
                    self.log.info(response)
                    doc_properties_beforebackup.append(response.get('documents'))
                self.helper.run_backup(testcase=self, level='FULL', sc=None)
                if 'IN' in step:
                    self.helper.delete_db_and_validate(
                    	testcase=self,
                        dbsinsubclient=dbs_in_subclient
                    )
                    self.helper.run_restore(testcase=self)
                else:
                    temp_dbs_in_subclient = []
                    for database in dbs_in_subclient:
                        temp_dbs_in_subclient.append('OOPRestore_auto-' + str(database))
                    self.helper.delete_db_and_validate(
                    	testcase=self,
                        dbsinsubclient=temp_dbs_in_subclient
                    )
                    self.helper.run_restore(testcase=self,
                                            type_of_restore='out')
                    self.log.info('*******************COLLECT*DOC*PROPERTIES*********************')
                browse_paths_dictionary = self.helper.recursive_browse(sc=self.subclient,
                                                                       log=self.log)
                for database in dbs_in_subclient:
                    if 'IN' in step:
                        for browse_path in browse_paths_dictionary[database]:
                            browse_path = browse_path.replace('\\', '-')
                            response = self.helper.return_result_json(
                            	testcase=self,
                                operation='get document properties',
                                param=[browse_path]
                            )
                    else:
                        for browse_path in browse_paths_dictionary[database]:
                            browse_path = browse_path.replace('\\', '-')
                            browse_path = 'OOPRestore_auto-' + str(browse_path)
                            response = self.helper.return_result_json(
                            	testcase=self,
                                operation='get document properties',
                                param=[browse_path]
                            )
                    self.log.info(response)
                    doc_properties_afterrestore.append(response.get('documents'))
                    self.log.info('*******************COMPARE*DOC*PROPERTIES*********************')
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
        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}. trace:{}'.format(type(ex).__name__,
                                                                            sys.exc_info()
                                                                            [-1].tb_lineno,
                                                                            ex,
                                                                            sys.exc_info()[0]))
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
    #     # delete subclient here
    #     # delete docs folder, label dict folder and message property folder
        self.log.info('***********************CLEAN*UP*OOP*FOLDER********************************')
        try:
            self.helper.return_result_json(self,
                                           operation='console commands',
                                           param=['exit'])
            time.sleep(40)
            if 'WINDOWS' in self.machine.os_info:
                self.machine.execute_command('taskkill /f /im n*')
                self.log.info('Killed Domino')
                time.sleep(60)
                if self.machine.check_directory_exists(self.domino_data_path +
                                                       '\\OOPRestore_auto'):
                    self.machine.remove_directory(self.domino_data_path +
                                                  '\\OOPRestore_auto')
                    self.log.info('Deleted OOPRestore folder')
                self.machine.execute_command('nserver.exe')
            else:
                self.machine.execute_command("ps -aef| "
                                             "grep notes | "
                                             "awk '{print $2}' | "
                                             "xargs kill -9")
                time.sleep(60)
                if self.machine.check_directory_exists(self.domino_data_path +
                                                       '/OOPRestore_auto'):
                    self.machine.remove_directory(self.domino_data_path +
                                                  '/OOPRestore_auto')
                    self.log.info('Deleted OOPRestore folder')
                cmd = self.domino_data_path + '/DomShrct.sh'
                self.machine.execute_command(cmd)
        except Exception as ex:
            self.log.info('Clean-up failed. Testcase PASSED. Exception {}'.format(ex))
        for _ in range(4):
            time.sleep(60)
            try:
                self.log.info('Checking if server is up...')
                response = requests.get('http://' + self.tcinputs.get("DominoServerHostName"))
                if response.status_code == 200:
                    self.log.info('Domino is up successfully')
                    break
                else:
                    self.log.info('Error in Domino recovery')
            except requests.ConnectionError:
                self.log.info('Domino shut down. Please start Domino before continuing')
