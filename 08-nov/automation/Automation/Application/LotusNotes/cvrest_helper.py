# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for LN Agents

    CVRestHelper:
        __init__(testcase)          --  Initialize the cvresthelper object

        check_for_api()             --  Checks for CVRestAPI on the Domino Server and
        populates rest_ops and domino_data_path accordingly

        get_all_apis()              --  Returns a list of all REST API extensions
        active on Domino Server

        return_result_json()        --  Calls the API and returns a dictionary
        of the response received

        delete_db_and_validate()    --  Deletes LN databases and validates their
        successful/unsuccessful delete

        run_backup()                --  Runs backup operation on an LNDB Subclient

        run_restore()               --  Runs restore operation on an LNDB Subclient

        browse_processor()          --  Helps in processing recursive browse for LNDBSubclient

        recursive_browse()          --  Performs browse recursively and returns a dict of paths

        clean_up_OOP_folder()       --  Cleans up Out Of Place Restore folder

        remove_restored_dbs()       --  Removes restored databses

        collect_doc_properties()    --  Returns a list of database properties

        edit_notes_ini()            --  Edits the notes.ini configuration file

        rename_logdir()             --  Rename logdir folder on the client machine

        start_domino()              --  Start Domino server

        check_if_domino_up()        --  Checks if the Domino server is up and running

        delete_indexcache()         --  Remove indexcache from media agent

        add_database_to_subclient() --  Create new database(s) and add it to a subclient

        fetch_noteid_dict()         --  Collects note ids from a list of databases

        parse_find()                --  Parses find() result into a dictionary with list of
        note ids with their corresponding databases as keys

        clean_properties_fetched()  --  Parses collect properties result into a list of tuples
        note ids and embedded object details

        remove_extension()          --  Parses collect properties result into a list of tuples
        note ids and embedded object details

"""
import json
import os
import re
import sys
import time
from queue import Queue
from threading import Thread

import requests
from requests.auth import HTTPBasicAuth

from AutomationUtils.machine import Machine
from . import constants
from .exception import LNException


class CVRestHelper:
    """Contains helper functions for interaction with Domino REST API for LN Agents
    """

    def __init__(self, testcase):
        """"Initializes the CVRest Helper class object

            Properties to be initialized:
                tc      (object)    --  testcase object

                log     (object)    --  object of the logger class

        """

        self.tc = testcase
        self.log = testcase.log

    def check_for_api(self):
        """"Checks for CVRestAPI on the Domino Server and
        populates rest_ops and domino_data_path accordingly

            Raises:
                LNException:
                    if Domino Server does not have CVRestAPI
                    if Domino Server has not enabled CVRestAPI

        """
        self.log.info('Checking if cvrest api exists...')
        response = requests.get(constants.API_URL % self.tc.tcinputs.get("DominoServerHostName"))
        self.log.info(response.status_code)
        self.tc.rest_ops = json.loads(response.text)
        self.tc.rest_ops = self.tc.rest_ops.get('services')
        if not any(d['name'] == 'CVRestApi' for d in self.tc.rest_ops):
            raise LNException('DominoOperations', '102')
        else:
            if not any(d['name'] == 'CVRestApi' and d['enabled']
                       for d in self.tc.rest_ops):
                raise LNException('DominoOperations', '103')
        self.tc.rest_ops = self.get_all_apis()
        self.log.info('List of rest services:')
        for i in self.tc.rest_ops:
            self.log.info(self.tc.rest_ops[i])
        response = self.return_result_json('notes setting', param=['Directory'])
        self.tc.domino_data_path = response['Directory']
        self.log.info(f'Domino Data Directory: {self.tc.domino_data_path}')

    def get_all_apis(self):
        """Returns a list of all REST API extensions active on Domino Server

            Returns:
                list    -  list of services
        """

        url = constants.CVREST_URL % self.tc.tcinputs.get("DominoServerHostName")
        self.log.info('URL formed: %s', url)
        response = requests.get(url)
        self.log.info(f'Response status code: {response.status_code}')
        data = json.loads(response.text)
        services = {}
        data = data['cv rest services']
        for item in data:
            key_temp = href_temp = type_temp = None
            for i in item:
                if i == 'href':
                    href_temp = url + item[i]
                elif i == 'type':
                    type_temp = item[i]
                else:
                    key_temp = i
            services[key_temp] = dict({'href': href_temp, 'type': type_temp})

        return services

    def return_result_json(self, operation, param=None, jstring=None):
        """Calls the API and returns a dictionary of the response received

            Args:
                operation       (str)       --  API functionality called

                param           (str)       --  parameters to be passed to the API for GET requests
                    default: None

                jstring         (str)       --  parameters to be passed to the API for POST request
                    default: None


            Returns:
                dictionary  --  dictionary of the json received
        """

        result = {}
        try:
            response = None
            if operation in self.tc.rest_ops:
                temp = self.tc.rest_ops[operation]
                url = temp['href']
                num_of_parameters = 0
                while '{' in url:
                    url = url.replace(url[url.index('{'):url.index('}') + 1],
                                      param[num_of_parameters])
                    num_of_parameters = num_of_parameters + 1
                if temp['type'] == 'get':
                    response = requests.get(url, auth=HTTPBasicAuth(
                        self.tc.tcinputs.get("DominoNotesUser"),
                        self.tc.tcinputs.get("DominoNotesPassword")))
                else:
                    response = requests.post(url, json=jstring, auth=HTTPBasicAuth(
                        self.tc.tcinputs.get("DominoNotesUser"),
                        self.tc.tcinputs.get("DominoNotesPassword")))
            data = json.loads(response.text)
            for i in data:
                try:
                    result = eval(' '.join(str(x) for x in data[i]))
                except Exception:
                    result = data[i]
            return result
        except Exception as ex:
            self.log.error(
                f'Error {type(ex).__name__} on '
                f'line {sys.exc_info()[-1].tb_lineno}. '
                f'Error {ex}')
            raise Exception(f'{ex}. Result:{result}')

    def delete_db_and_validate(self, dbsinsubclient):
        """"Deletes LN databases and validates their successful/unsuccessful delete

            Args:
                dbsinsubclient  (list)      --  databases to be removed

        """
        self.log.info(
            '***************************************DELETE****************************************')
        for database in dbsinsubclient:
            response = self.return_result_json('delete database', param=[database])
            if 'removed' in response.get('status'):
                self.log.info(f'{database} removal successful')
            else:
                self.log.info(f'{database} removal unsuccessful')
        self.log.info(
            '*****************************VALIDATE**DELETE****************************************')
        for database in dbsinsubclient:
            response = self.return_result_json('delete database', param=[database])
            self.log.info(f'{database} {response.get("status")}')

    def run_backup(
            self,
            level='FULL',
            subclient=None,
            schedule_pattern=None,
            incremental_backup=False,
            incremental_level='BEFORE_SYNTH'):
        """"Runs backup operation on an LNDB Subclient

            Args:
                level               (str)       --  type of backup

                    default: 'FULL'

                subclient           (object)    --  instance of the subclient to perform backup on

                    default: None

                schedule_pattern    (dict)      --  schedule pattern for setting schedule

                    default: None

                incremental_backup  (bool)      --  run incremental backup
                        only applicable in case of Synthetic_full backup

                    default: False

                incremental_level   (str)       --  run incremental backup before/after
                synthetic full
                        BEFORE_SYNTH / AFTER_SYNTH

                        only applicable in case of Synthetic_full backup

                    default: BEFORE_SYNTH

            Returns:
                object - instance of the Job class for this backup job

        """
        try:
            if subclient is None:
                subclient = self.tc.subclient
            self.log.info(
                '**********************************BACKUP***************************')
            self.log.info(f'Running {level} backup for {subclient}')
            time.sleep(30)
            job = subclient.backup(
                backup_level=level,
                schedule_pattern=schedule_pattern,
                incremental_backup=incremental_backup,
                incremental_level=incremental_level
            )
            self.log.info(job)
            if schedule_pattern is None:
                job.wait_for_completion()
            return job
        except Exception as ex:
            self.log.error(
                f'Error {type(ex).__name__} on '
                f'line {sys.exc_info()[-1].tb_lineno}. '
                f'Error {ex}'
            )
            self.tc.result_string = str(ex)
            raise Exception(ex)

    def run_restore(
            self,
            type_of_restore='IN',
            subclient=None,
            interrupt=False,
            start_time=None,
            end_time=None):
        """"Runs restore operation on an LNDB Subclient

            Args:
                type_of_restore (str)       --  type of restore

                    default: 'IN'

                subclient       (object)    --  instance of the subclient to perform backup on

                    default: None

                interrupt       (bool)      --  boolean specifying whether to interrupt and
                return the job or wait for the job to complete

                    default: False

                start_time      (str)       --  time to retore the contents after
                        format: YYYY-MM-DD HH:MM:SS

                    default: None

                end_time        (str)       --  time to restore the contents before
                        format: YYYY-MM-DD HH:MM:SS

                    default: None

             Returns:
                object - instance of the Job class for this restore job if its an immediate Job
                         instance of the Schedule class for this restore job if its a scheduled Job
        """
        lndb_restore_options = None
        try:
            if subclient is None:
                subclient = self.tc.subclient
            if self.tc.common_options_dict == {}:
                self.tc.common_options_dict = None
            try:
                lndb_restore_options = self.tc.lndb_restore_options
            except Exception:
                pass
            self.log.info(
                f"common_options_dict: {self.tc.common_options_dict}")
            self.log.info(
                f"lndb_restore_options: {lndb_restore_options}")
            if 'OUT' in type_of_restore:
                self.log.info(
                    '***************************OUT*RESTORE*****************************')
                path, di = subclient.browse()
                if not path:
                    path = self.tc.machine.os_sep
                dest_path = self.tc.machine.join_path(
                    self.tc.domino_data_path, constants.OUT_PLACE_FOLDER_PATH)
                self.log.info(f'Out of place restore path: {dest_path}')
                time.sleep(30)
                job = subclient.restore_out_of_place(
                    self.tc.tcinputs.get('ClientName'),
                    paths=path,
                    destination_path=dest_path,
                    from_time=start_time,
                    to_time=end_time,
                    lndb_restore_options=lndb_restore_options,
                    common_options_dict=self.tc.common_options_dict
                )
            else:
                self.log.info(
                    '*******************************IN*RESTORE*****************************')
                path, di = subclient.browse()
                if not path:
                    path = self.tc.machine.os_sep
                job = subclient.restore_in_place(
                    paths=path,
                    from_time=start_time,
                    to_time=end_time,
                    lndb_restore_options=lndb_restore_options,
                    common_options_dict=self.tc.common_options_dict
                )
            self.log.info(job)
            if not interrupt:
                job.wait_for_completion()
            return job
        except Exception as ex:
            self.log.error(f'Error {type(ex).__name__} on line '
                           f'{sys.exc_info()[-1].tb_lineno}. Error {ex}')
            self.tc.result_string = str(ex)
            raise Exception(ex)

    def browse_processor(self, subclient, queue, dictionary, machine):
        """"Helps in processing recursive browse for LNDBSubclient

                    Args:
                        subclient    (object)     --  instance of the subclient to perform browse on

                        queue       (object)     --  queue object storing paths found through browse

                        dictionary  (dict)       --  dict mapping backed up database to its path

                        machine     (object)     --  instance of machine class

         """
        while True:
            element = None
            try:
                element = queue.get()
                t_path, t_dict = subclient.browse(path=element)
                for path in t_path:
                    regex = re.compile('(.*nsf*)|(.*ntf*)|(.*mail/.+)|(.*mail\\\\.+)')
                    if re.match(regex, path):
                        abspath = os.path.splitext(path)[0]
                        self.log.info(f'Path found:{abspath}')
                        sep = machine.os_sep
                        name = abspath.rsplit(sep, 1)[1]
                        if name in dictionary:
                            dictionary[name].append(
                                abspath.replace(
                                    f'{sep}DATABASES{sep}', ''))
                        else:
                            dictionary[name] = [
                                abspath.replace(f'{sep}DATABASES{sep}', '')
                            ]
                    else:
                        queue.put(path)
            except Exception:
                pass
            finally:
                queue.task_done()

    def recursive_browse(self, subclient, machine):
        """"Performs browse recursively for an LNDBSubclient

            Args:
                subclient          (object)    --  instance of the subclient to perform browse on

                machine     (object)    --  instance of machine class

            Returns:
                dictionary  - dictionary of paths

        """
        q = Queue()
        dictionary = dict()
        for _ in range(5):
            try:
                t = Thread(
                    target=self.browse_processor,
                    args=(subclient, q, dictionary, machine)
                )
                t.setDaemon(True)
                t.start()
            except Exception as ex:
                self.log.info(ex)
                continue
        q.put(machine.os_sep)
        q.join()
        self.log.info('Browse operation completed')
        return dictionary

    def clean_up_OOP_folder(self):
        """"Cleans up Out Of Place Restore folder

        """
        self.log.info(
            '***********************CLEAN*UP*OOP*FOLDER****************************')
        try:
            self.return_result_json('console commands', param=['restart server'])
            time.sleep(10)
            self.log.info('Killed Domino')
            oopf_path = self.tc.machine.join_path(
                self.tc.domino_data_path,
                constants.OUT_PLACE_FOLDER_PATH
            )
            if self.tc.machine.check_directory_exists(oopf_path):
                self.tc.machine.remove_directory(oopf_path)
            self.log.info('Deleted OOPRestore folder')
            self.check_if_domino_up()
        except Exception as ex:
            self.log.info(f'Clean-up failed. Exception {ex}')
            self.check_if_domino_up()

    def remove_restored_dbs(
            self,
            dbs_in_subclient,
            type_of_restore_performed='IN'):
        """"Removes restored databses

            Args:
                dbs_in_subclient            (list)      --  list of databases to be removed

                type_of_restore_performed   (str)       --  in-place / out-place

                    default: 'IN'

        """
        if 'OUT' in type_of_restore_performed:
            for database in dbs_in_subclient:
                temp = f'{constants.OUT_PLACE_FOLDER_PATH}-{str(database)}'
                temp = temp.replace(self.tc.machine.os_sep, '-')
                response = self.return_result_json(
                    'delete database',
                    param=[temp.replace('.nsf', '')])
                self.log.info(f'{database} {response.get("status")}')
        else:
            for database in dbs_in_subclient:
                database = database.replace(self.tc.machine.os_sep, '-')
                response = self.return_result_json(
                    'delete database',
                    param=[database.replace('.nsf', '')]
                )
                self.log.info(f'{database} {response.get("status")}')

    def collect_doc_properties(
            self,
            dbs_in_subclient,
            type_of_restore_performed='IN',
            browse_paths_dictionary=None):
        """"Collect database properties

            Args:
                dbs_in_subclient            (list)          --  list of databases

                type_of_restore_performed   (string)        --  in-place / out-place

                    default: 'IN'

                browse_paths_dictionary     (dictionary)    --  dictionary of paths

           Returns:
                list    -  list of properties

        """
        return_list = []
        if browse_paths_dictionary is None:
            if 'OUT' in type_of_restore_performed:
                for database in dbs_in_subclient:
                    temp = f'{constants.OUT_PLACE_FOLDER_PATH}-{str(database)}'
                    temp = temp.replace(self.tc.machine.os_sep, '-')
                    response = self.return_result_json(
                        'get document properties',
                        param=[temp.replace('.nsf', '')]
                    )
                    self.log.debug(response)
                    if 'error' not in response:
                        return_list.append(response)
            else:
                for database in dbs_in_subclient:
                    database = database.replace(self.tc.machine.os_sep, '-')
                    response = self.return_result_json(
                        'get document properties',
                        param=[database.replace('.nsf', '')]
                    )
                    self.log.debug(response)
                    if 'error' not in response:
                        return_list.append(response)
        else:
            if 'OUT' in type_of_restore_performed:
                for database in dbs_in_subclient:
                    for browse_path in browse_paths_dictionary[database]:
                        temp = f'{constants.OUT_PLACE_FOLDER_PATH}-{str(browse_path)}'
                        temp = temp.replace(self.tc.machine.os_sep, '-')
                        response = self.return_result_json(
                            'get document properties',
                            param=[temp.replace('.nsf', '')]
                        )
                        self.log.debug(response)
                        if 'error' not in response:
                            return_list.append(response)
            else:
                for database in dbs_in_subclient:
                    for browse_path in browse_paths_dictionary[database]:
                        browse_path = browse_path.replace(self.tc.machine.os_sep, '-')
                        response = self.return_result_json(
                            'get document properties',
                            param=[browse_path.replace('.nsf', '')]
                        )
                        self.log.debug(response)
                        if 'error' not in response:
                            return_list.append(response)
        return return_list

    def edit_notes_ini(self, value):
        """"Edit the notes.ini configuration file

            Args:
                value   (str)    --  configuration setting in notes.ini

        """
        command = f"Set Configuration {value}"
        response = self.return_result_json('console commands', param=[command])
        self.log.info(response)
        self.log.info('*************SHUT*DOWN*DOMINO*SERVER**********************')
        response = self.return_result_json('console commands', param=['exit'])
        time.sleep(40)
        self.log.info(response)

    def rename_logdir(self):
        """"Rename logdir folder on the client machine

        """
        logdir_path = self.tc.machine.join_path(
            self.tc.domino_data_path, 'logdir')
        rlogdir_path = self.tc.machine.join_path(
            self.tc.domino_data_path, 'logdir_')
        if self.tc.machine.check_directory_exists(rlogdir_path):
            self.tc.machine.remove_directory(rlogdir_path)
        self.tc.machine.rename_file_or_folder(logdir_path, rlogdir_path)
        self.log.info(self.tc.machine.check_directory_exists(rlogdir_path))

    def start_domino(self):
        """"Start Domino server

        """
        if self.check_if_domino_up(False):
            return
        else:
            if 'WINDOWS' in self.tc.machine.os_info:
                self.tc.machine.execute_command('nserver.exe')
            else:
                cmd = self.tc.domino_data_path + '/DomShrct.sh'
                self.tc.machine.execute_command(cmd)
            self.check_if_domino_up()

    def check_if_domino_up(self, exception_flag=True):
        """"Checks if the Domino server is up and running

            Args:
                exception_flag      (bool)      --  boolean to decide whether to return
                exception or continue

                    default: True

            Returns:
                int     - 1, if server is  up
                          0, if not

            Raises:
                LNException:
                    if Domino Server did not start up

        """
        for _ in range(4):
            time.sleep(60)
            try:
                self.log.info('Checking if server is up...')
                response = requests.get(
                    constants.BASE_URL % self.tc.tcinputs.get("DominoServerHostName")
                )
                if response.status_code == 200:
                    self.log.info('Domino is up successfully')
                    return 1
                else:
                    self.log.info('Error in Domino recovery')
                    continue
            except requests.ConnectionError:
                self.log.info('Domino shut down')
                continue
        if exception_flag:
            raise LNException('DominoOperations', '101')
        else:
            return 0

    def delete_indexcache(self, subclient):
        """"Remove indexcache from media agent

            Args:
                subclient  (object)     --  instance of subclient

        """
        self.log.info(
            f'MediaAgent for storage policy {subclient.storage_policy} for '
            f'subclient {subclient.subclient_name}:')
        self.log.info(subclient.storage_ma)
        self.log.info('Subclient ID:')
        self.log.info(subclient.subclient_id)
        ma_machine = Machine(subclient.storage_ma, self.tc.commcell)
        indexcache = ma_machine.get_registry_value(
            ma_machine.join_path('Machines', subclient.storage_ma),
            'dFSINDEXCACHE')
        self.log.info('IndexCache: ' + indexcache)
        self.log.info('Removing index cache:')
        self.log.info(
            ma_machine.remove_directory(
                ma_machine.join_path(
                    indexcache,
                    'CV_Index',
                    '2',
                    subclient.subclient_id)))
        self.log.info('Check to see if indexcache exists after deletion:')
        self.log.info(
            ma_machine.check_directory_exists(
                ma_machine.join_path(
                    indexcache,
                    'CV_Index',
                    '2',
                    subclient.subclient_id)))

    def add_database_to_subclient(
            self,
            subclient,
            num_db,
            num_doc,
            num_logs="null",
            prefix="CVAuto"):
        """"Create new database(s) and add it to a subclient

            Args:
                subclient          (object)      --  instance of subclient

                num_db      (str)         --  number of databases to be created

                num_doc     (str)         --  number of documents to be added

                num_logs    (str)         --  number of logs to be filled

                    default: 'null'

                prefix      (str)         --  prefix for database name

                    default: 'CVAuto'

            Returns:
                list    -   list of database names added
        """
        self.log.info(subclient)
        jstring = {
            "key":
                [{
                    "template": "notebook9.ntf",
                    "numdb": num_db,
                    "numdocs": num_doc,
                    "numlogs": num_logs,
                    "dbname": prefix,
                    "trlog": "true",
                    "del": "false",
                    "incremental": "true"
                }]
        }
        self.log.info(jstring)
        response = self.return_result_json('data populator', jstring=jstring)
        if isinstance(response, list):
            db_names = [_['name'] for _ in response]
        else:
            db_names = [response.get('name')]
        for db_name in db_names:
            subclient_content = [{
                'dbiid1': 1,
                'dbiid2': 1,
                'dbiid3': 1,
                'dbiid4': 1,
                'relativePath': db_name,
                'databaseTitle': db_name.replace('.nsf', '')
            }]
            subclient.content += subclient_content
            self.log.info(f'New database added: {db_name}')
        db_names = [w.replace('.nsf', '') for w in db_names]
        self.log.info(db_names)
        return db_names

    def fetch_noteid_dict(self, dbs_in_subclient):
        """"Collects note ids

            Args:
                dbs_in_subclient    (list)  --  list of databases

           Returns:
                dict    -  dictionary of list of note ids with their corresponding dbs as keys

        """
        result = {}
        for database in dbs_in_subclient:
            response = self.return_result_json(
                'get document properties',
                param=[database.replace('.nsf', '')]
            )
            docprop = response['documents']
            for _ in docprop:
                if database in result:
                    result[database].append(_['node id'].strip())
                else:
                    result[database] = [_['node id'].strip()]
        return result

    def parse_find(self, to_parse, num_db, dbs_in_subclient):
        """"Parses find() result into a dictionary with list of note ids
        with their corresponding databases as keys

            Args:
                to_parse            (tuple)     --  result of find() operation

                num_db              (int)       --  number of databases

                dbs_in_subclient    (list)      --  list of databases

           Returns:
                dict    -  dictionary of list of note ids with their corresponding dbs as keys

        """
        result = {}

        temp_list, temp_dict = to_parse
        t_noteid_list = temp_list[(4 * num_db):]
        for database in dbs_in_subclient:
            for _ in t_noteid_list:
                if database in _:
                    noteid = _.split('\\')[-1].strip('0').upper().strip()
                    if database in result:
                        result[database].append(noteid)
                    else:
                        result[database] = [noteid]
        return result

    def clean_properties_fetched(self, properties):
        """"Parses collect properties result into a list of tuples note ids
        and embedded object details

            Args:
                properties      (list)  --  document properties

           Returns:
                list    -  list of tuples of note ids and embedded object details

        """
        for item_db in properties:
            for item_doc in item_db:
                item_doc.pop('created', item_doc['created'])
                item_doc.pop('universal id', item_doc['universal id'])
        return properties

    def remove_extension(self, database_list, machine_os):
        """"Parses collect properties result into a list of tuples note ids
        and embedded object details

            Args:
                database_list      (list)   --  list of databases in subclient

                machine_os         (str)    --  operating system of the machine

           Returns:
                list    -  list of databases present in subclient

        """
        new_list = []
        for lndbcontent in database_list:
            database = lndbcontent['lotusNotesDBContent']['relativePath']
            if 'ntf' in database:
                self.log.info(f'{database} is a template.')
            if 'WINDOWS' in machine_os:
                new_list.append(database.replace('.nsf', ''))
            else:
                new_list.append(
                    database.replace('.nsf', '').replace('/', '')
                )
        self.log.info(new_list)
        return new_list
