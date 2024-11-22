# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This class contains all the utility methods needed for activate automation

Classes:

    ActivateUtils()                         Constructor : object()
    set_dm2_settings()                      Sets dm2 settings on webserver client
    create_new_directory()                  Creates a child Directory.
    query_database()                        Query the test validation database
    db_get_entities_dict_from_sqllite()     Returns all the entities present in the db
    get_workflow_interaction()              Get workflow interaction detail
    sensitive_data_generation()             Generate sensitive data with PII
    read_config_file()                      Read the content of the config file
    write_config_file()                     Write in the config file
    encrypt_data()                          Encrypts data in the file path
    create_new_directory()                  Creates new Directory
    delete_old_directory()                  Deletes an old Directory
    delete_old_data()                       Deletes old generated data
    run_backup()                            Run Backup JOB
    get_sensitive_content_details()         Get Sensitive content with linked entity value for for creating
                                            GDPR (DELETE/EXPORT) request.
    db_get_sensitive_columns_list()         Get Sensitive Files From SQL DB for Matching Entities
    db_get_sensitive_entities()             Get Sensitive Entities for Row which matches column data
    execute_query()                         Executes a DB query on the given DB
    db_get_folder_stats_count()             Returns the count of rows present in folderStatsTable DB table
    db_get_folder_size()                    Returns the size of the given folder path from database
    db_get_folders_count()                  Returns the count of all the folders present inside the given folder path
    db_get_files_count()                    Returns the count of all the files present inside the given folder path
    db_get_access_time()                    Returns the access time of the given folder path from database
    run_data_generator()                    Run Data Generator Utility TO Populate Endpoint.
    mail_generate_and_send()                Generate Random Mails And Send
    run_backup_mailbox_job()                Run mailbox Backup JOB from Commcell
    get_user_to_sid_mapping()               Get Username to SID mapping dictionary for given user list
    get_user_info()                         Get File Owner for given file path
    set_file_time_info()                    Set Access Time, Creation Time, Modified Time randomly for
                                            given file (TimeZone Set GMT standard time)
    change_file_owner()                     Make the ownership of a given NTFS file/directories to  given sid
    convert_readable_format()               Convert ACL to readable permission
    get_readable_permission()               Get Access Control List for given file or directory
    read_formatted_acl_from_database()      Query ACL database for file, folder or root details
    get_access_control_list()               Get Access Control List for given file or directory
    fetch_acl()                             Fetch access list details for files/directories
    create_fso_metadata_db()                Create fso metadata database5
    create_fso_data()                       Create SQL Database to store FSO entities for Admin Console Review
    get_random_files_for_actions()          Selects a random number of files for actions
    validate_files_marked_for_actions()     Verifies if the files are marked for delete or not
    activate_cleanup()                      Performs activate related cleanup operations
    create_fs_subclient_for_clients()           Create File System subclient objects
    do_operation_on_file()                  Perform an operation on a randomly chosen file
    generate_fso_datasource_config()        Generates a csv config file which can be imported on FSO landing page
    create_share_and_generate_data()        Creates a new share one the machine and generates data on the share
    db_get_total_files_count()              Returns the total count of files present in the given table
    create_commcell_entities()              Creates all the required entities for the subclient object
    get_date_time_dict_calendarview()       Returns the date or time dict for CalendarView class
    get_random_file_from_path               Gets a random file from the path
    apply_new_permissions()                 Applies new permissions on given folder
    eicar_data_generation()                 Generate anti-malware test file 

"""
import configparser
import csv
import json
import math
import mimetypes
import os
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta
from random import random, randrange
from subprocess import PIPE, Popen

import dynamicindex.utils.constants as cs
import ntsecuritycon as con
import win32api
import win32file
import win32security
from AutomationUtils import config, logger
from AutomationUtils.constants import AUTOMATION_BIN_PATH, AUTOMATION_DIRECTORY
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from AutomationUtils.Performance.Utils.performance_helper import \
    AutomationCache
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils.constants import (RANDOM_INT_LOWER_LIMIT,
                                          RANDOM_INT_UPPER_LIMIT)
from Server.JobManager.jobmanager_helper import JobManager

from cvpysdk.storage import MediaAgent

_CONFIG = config.get_config()
_ACTIVATE_CONSTANTS = _CONFIG.DynamicIndex


class ActivateUtils:
    """
         This class contains all the utility methods needed for activate automation
    """
    def __init__(self, commcell=None):
        """
        Initializes ActivateUtils object
        """
        self.log = logger.get_log()
        self._commcell = commcell
        self._automation_cache = AutomationCache()
        self._data_source_management_constants = _ACTIVATE_CONSTANTS.DataSourceManagement

    def set_dm2_settings(self, webserver, setting_name, setting_value):
        """Sets dm2 settings on given webserver dm2 db

            Args:

                webserver       (str)       --  Webserver client name

                setting_name    (str)       --  Setting name to insert

                setting_value   (str)       --  Setting value

            Returns:
                None
        """
        _qscript_dm2 = f"qoperation execscript -dbn DM2 -c '{webserver}' -sn UpdateSettingValue -si '{setting_name}' -si '{setting_value}'"
        self.log.info(
            f"Setting dm2settings - {setting_name} with value : {setting_value}")
        self._commcell._qoperation_execscript(_qscript_dm2)

    @staticmethod
    def query_database(target_database, query):
        """
        Query database
        :param target_database: target database to query
        :param query: query to be fired
        :return result
        """
        connection = None
        column_names = []
        return_list = []
        result = {}
        try:
            connection = sqlite3.connect(target_database)
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            result_from_database = cursor.execute(query)
            for row in result_from_database.description:
                column_names.append(row[0])
            result_from_database = result_from_database.fetchall()
            for res in range(len(result_from_database)):
                temp_dict = {}
                for col in range(len(column_names)):
                    temp_dict.update({column_names[col]: result_from_database[res][col]})
                return_list.append(temp_dict)
            result = {'result': return_list}

        except Exception as ex:
            ActivateUtils().log.error("Error {0}".format(ex))

        finally:
            if connection is not None:
                connection.close()
        return result

    @staticmethod
    def db_get_entities_dict_from_sqllite(sqllite_db_path):
        """
        Returns all the entities present in the db

            Args:
                sqllite_db_path -- If True, entities which are null or blank
                                        are removed
                :return result

        """
        result = {}
        query = 'select * from entity'
        result = ActivateUtils.query_database(sqllite_db_path, query)
        return result

    @staticmethod
    def get_workflow_interaction(commcell, workflow_id):
        """
        Get workflow interaction detail
        :param commcell: commcell object
        :param workflow_id: workflow job
        :return: interactionid
        """
        query = """select interactionGuid from WF_Interaction where jobId ={}""".format(
            workflow_id)
        csdb = CommServDatabase(commcell)
        csdb.execute(query)
        cur = csdb.fetch_one_row()
        value = cur.pop(0)
        if value is "":
            raise Exception("Could not find interaction details")
        return value
    
    def eicar_data_generation(self, local_path, machine = None, remote_machine = None, number_files=1):
        """
        Generate anti-malware test file 
        :param self:
        :param path: path to create a file at
        :param machine: controller machine object
        :param remote_machine: remote machine object
        :param number_files: number of files to generate
        :return: 
                list of filenames created
        """
        try:
         filenames = []
         if not machine:
            path = local_path
         else:
            temp_path = AUTOMATION_BIN_PATH + os.sep + cs.THREAT_SCAN_FOLDER
            machine.remove_directory(temp_path)
            dir_created = machine.create_directory(temp_path)
            if not dir_created:
             self.log.info("Couldn't create temp directory")
             return
            path = temp_path

         while number_files > 0:
          suffix = randrange(cs.RANDOM_INT_LOWER_LIMIT,
                             cs.RANDOM_INT_UPPER_LIMIT)
          filename = "eicar_sample_"+str(suffix)+".txt"
          file = open(path + f"\\{filename}", "w")
          content = "X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
          file.write(content)
          file.close()
          self.log.info(f"Created an EICAR file {filename} at {path}")
          number_files = number_files-1
          filenames.append(filename)
         if remote_machine:
            self.log.info("Copy eicar files from the temp dir to the unc path")
            remote_machine.copy_from_local(temp_path, local_path)
         return filenames
        except Exception as exp:
            self.log.info(f"Exception occurred {exp}")
            raise Exception("Failed generating EICAR data")

    def sensitive_data_generation(self, database_path, number_files=5, encrypt=False, corrupt=False):
        """
        Generate sensitive data with PII
        :param self:
        :param database_path: dump database path
        :param number_files: number of files to generate
        :param encrypt: whether to encrypt
        :param corrupt: whether to corrupt
        :return:
        """
        javahome = os.environ.get('JAVA_HOME')
        if javahome is None:
            self.log.error("Java_Home is not set")
            return 2
        filename = AUTOMATION_BIN_PATH
        self.log.info(filename)
        self.log.info(f"Database path is {database_path}")
        self.delete_old_data(database_path)
        config_file = f'{filename}\\Properties\\Config.properties'
        original_values_dict = {}
        if encrypt or corrupt:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.rstrip()  # removes trailing whitespace and '\n' chars
                    if "=" not in line:
                        continue  # skips blanks and comments w/o =
                    if line.startswith("#"):
                        continue  # skips comments which contain =
                    k, v = line.split("=", 1)
                    original_values_dict[k] = v
                if encrypt:
                    self.log.info("Enabling encryption temporarily")
                    self.write_in_config_file(
                        config_file, cs.ENCRYPTION_KEY, "true")
                if corrupt:
                    self.log.info("Enabling corruption temporarily")
                    self.write_in_config_file(
                        config_file, cs.CORRUPTION_KEY, "true")

        # Form the command to run
        runcommand = r'"{0}\bin\java.exe" ' \
                     r'-jar "{1}\GDPR.jar" -NUM {2} -PATH {3}'.format(javahome, filename,
                                                                      number_files, database_path)
        self.log.info("Running [%s]." % (str(runcommand)))
        process = Popen(runcommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
                        cwd=filename)
        stdout, stderr = process.communicate()
        self.log.info(stderr)
        self.log.info(stdout)
        process.wait()
        if encrypt or corrupt:
            self.log.info("Reverting the properties file")
            self.write_in_config_file(
                file_path=config_file, key_value_dict=original_values_dict, remove_property=True)

    def read_config_file(self, file_path, section_name):
        """
        Reads the content of config file
        Args:
            file_path    (str): config file path
            section_name (str): dummy section name
        Returns:
            ConfigParser object
        """
        config = configparser.ConfigParser(strict=False)
        config.optionxform = str
        self.log.info(f'Reading the properties file {file_path}')
        with open(file_path, 'r') as f:
            default_values_dict = f.read()
            config_string = '[' + section_name + ']\n' + default_values_dict
        config.read_string(config_string)
        return config

    def write_in_config_file(self, file_path, key=None, value=None, **kwargs):
        """
        Writes in the config file
        Args:
            file_path      (str) : config file path
            key            (str) : key to write
            value          (str) : value to write
            kwargs         (dict): optional arguments

            Available kwargs options
                    key_value_dict (dict): key value dictionary
                    remove_property (bool): whether to remove the property
            
        """
        config = self.read_config_file(file_path, cs.DUMMY_CONFIG_FILE_SECTION)
        if not kwargs.get("remove_property", False) and (key and value):
            self.log.info(f"Writing the key {key} with value {value}")
            config.set(cs.DUMMY_CONFIG_FILE_SECTION, key, value)
        elif kwargs.get("remove_property", False) and key:
            config.remove_option(cs.DUMMY_CONFIG_FILE_SECTION, key)
            self.log.info(f"Removing key{key} in Dummy section")
        elif kwargs.get("remove_property", False):
            config.remove_section(cs.DUMMY_CONFIG_FILE_SECTION)
            self.log.info("Removing Dummy section and recreating empty one")
            config.add_section(cs.DUMMY_CONFIG_FILE_SECTION)

        if "key_value_dict" in kwargs:
            for key in kwargs.get('key_value_dict'):
                config.set(cs.DUMMY_CONFIG_FILE_SECTION, key, kwargs.get('key_value_dict')[key])

        with open(file_path, 'w') as configfile:
            config.write(configfile)

        # remove section and rewrite it
        with open(file_path, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(file_path, 'w') as fout:
            fout.writelines(data[1:])

    def encrypt_data(self, path, filename=None):
        """
        Encrypts the data in the path
        :param self:
        :param path: directory path
        :param filename: file to encrypt
        :return:
        """
        exepath = AUTOMATION_BIN_PATH
        self.log.info(f"Expecting Commvault ransomeware exe at {exepath}")
        # Form the command to run
        if filename:
         runcommand = r'{0}\CVRansomwareSimulator.exe "{1}" -names "{2}"'.format(exepath,
                                                                                 path, filename)
        else:
          runcommand = r'{0}\CVRansomwareSimulator.exe "{1}" -r'.format(exepath,
                                                                     path)
        self.log.info("Running [%s]." % (str(runcommand)))
        process = Popen(runcommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False,
                        cwd=filename)
        stdout, stderr = process.communicate()
        self.log.info(stderr)
        self.log.info(stdout)

    def create_new_directory(self, directory_name):
        """
        Creates new Directory
        Args:
            directory_name (str): Name of Directory to be created
        """
        try:
            os.mkdir(directory_name)
        except OSError as error:
            self.log.info(error)

    @staticmethod
    def delete_old_directory(_directory):
        """
        :param _directory: directory to be deleted
        """
        shutil.rmtree(_directory, ignore_errors=True)

    def delete_old_data(self, _directory):
        """
        :param _directory:
        """
        try:
            if len(os.listdir(_directory)) == 0:
                self.log.info("Directory [%s] is empty", _directory)
            else:
                self.log.info(
                    "Directory [%s] is not empty, deleting..", _directory)
                self.delete_old_directory(_directory)
        except Exception as exception:
            self.log.error(exception)

    def create_fs_subclient_for_clients(self, tcid, client_list, subclient_content_list,
                                        storage_policy, subclient_prop={}):
        """
        Create File System Subclients
        Args:
             tcid (int) : Testcase Id
             client_list (list) : List of Clients to create subclients for.
             subclient_content_list (list) : Subclient content list
             storage_policy (str) : Name of Storage Policy to associate with subclient
             subclient_prop (dict) : Subclient Properties dictionary
        Returns :
            (list) : Subclient Object list
        """
        subclient_object_list = list()
        for index, client_name in enumerate(client_list):
            self.log.info(f"Client Name : [{client_name}]")
            backupset_name = f"{tcid}_{client_name}_backupset"
            subclient_name = f"{tcid}_{client_name}_subclient"
            self.log.info(f"Backupset Name : [{backupset_name}]")
            self.log.info(f"Subclient Name : [{subclient_name}]")
            if self._commcell.clients.has_client(client_name):
                client_object = self._commcell.clients.get(client_name)
                agent_object = client_object.agents.get("File system")

                if agent_object.backupsets.has_backupset(backupset_name):
                    self.log.info(f"Backup set [{backupset_name}] already exists!! Deleting!!")
                    agent_object.backupsets.delete(backupset_name)

                backupset_obj = agent_object.backupsets.add(backupset_name)
                self.log.info(f"Added New backupset [{backupset_name}]")

                subclient_obj = backupset_obj.subclients.add(
                    subclient_name, storage_policy)
                self.log.info(f"Successfully created subclient: [{subclient_name}]")

                subclient_obj.content = [subclient_content_list[index]]
                if len(subclient_prop) > 0:
                    subclient_obj.update_properties(subclient_prop)
                subclient_object_list.append(subclient_obj)
            else:
                raise Exception(f"Client not found in commcell: {client_name} ")
        return subclient_object_list

    def run_backup(self, subclient_obj, backup_level='Incremental',
                   expected_state='completed'):
        """
        Run Backup JOB for passed subclient or list of subclients
        Args    :
            subclient_obj (Object/List) :  Subclient Object/List To Run Backup

            backup_level   (str)         :  level of backup the user wish to run
                                            Full / Incremental / Differential / Synthetic_full
                                            default: Incremental

            expected_state    (str/list) :  Expected job id state. Default = completed.
                                            suspended/killed/running/completed etc..
                                            Can be a string OR list of job states
                                            e.g
                                            completed
                                            ['waiting', 'running']
        """
        job_manager = JobManager(commcell=self._commcell)
        if not isinstance(subclient_obj, list):
            subclient_obj = [subclient_obj]
        if isinstance(expected_state, str):
            expected_state = [expected_state]
        for obj in subclient_obj:
            self.log.info(f"Starting {backup_level} backup for subclient : [{obj.subclient_name}]")
            job_manager.job = obj.backup(backup_level=backup_level)
            job_manager.wait_for_state(expected_state, time_limit=180)
            time.sleep(5)

    @staticmethod
    def get_sensitive_content_details(data_source_type, entity_type,
                                      db_path, entity_separator):
        """
        Get Sensitive content with linked entity value for for creating
        GDPR (DELETE/EXPORT) request.
        Args:
            data_source_type (str): Type of Data Source
            entity_type (str): Entity Type to paired with sensitive file name
            entity_separator: Separator between Entities
            db_path: Path of DB to use
        Returns:
            Tuple containing sensitive (file_name, entity_value)
        """
        __entity = ""
        __file = ""
        entities_list = list()
        entities_list.append(entity_type)
        __sensitive_files = ActivateUtils.db_get_sensitive_columns_list(
            data_source_type,
            entities_list,
            db_path
        )
        for filepath in __sensitive_files:
            __file = filepath
            db_entities_dict = ActivateUtils.db_get_sensitive_entities(
                data_source_type,
                filepath,
                entities_list,
                entity_separator,
                db_path
            )
            if entity_type.lower() in db_entities_dict.keys():
                __entity = db_entities_dict[entity_type.lower()].pop(0)
                break
        return __file, __entity

    @staticmethod
    def db_get_sensitive_columns_list(data_source, entities_list, db_path, flag=0):
        """
        Get Sensitive Files From SQL DB for Matching Entities
        Args:
            data_source: Data Source Type
            entities_list: List of Entities
            db_path: Path to Database Object
            flag: Value of FLag Column in Database

        Returns: List of Sensitive Columns
        """
        column_dict = {
            cs.EXCHANGE: "Subject",
            cs.ONE_DRIVE: "FilePath",
            cs.DATABASE: "Subject",
            cs.GOOGLE_DRIVE: "FilePath",
            cs.SHAREPOINT: "FilePath",
            cs.FILE_SYSTEM: "FilePath"
        }
        if data_source == cs.EXCHANGE or data_source == cs.DATABASE:
            flag = 1
        column_name = column_dict[data_source]
        sensitive_columns_list = []
        db_table = ActivateUtils.db_get_entities_dict_from_sqllite(db_path)
        for rows in db_table['result']:
            for entity in entities_list:
                if rows[entity] is not None and rows['Flag'] == flag:
                    sensitive_columns_list.append(rows[column_name])
                    break
        return sensitive_columns_list

    @staticmethod
    def db_get_sensitive_entities(
            data_source, column_data,
            entities_list, entity_separator, db_path):
        """
        Get Sensitive Entities for Row which matches column data
        Args:
            data_source: Data Source Type
            column_data: Column Data for filtering
            entities_list: List of Entities to return
            entity_separator: Separator between Entities
            db_path: Path of DB to use

        Returns: Entites Dictionary for matching column_data

        """
        columns_dict = {
            cs.EXCHANGE: "Subject",
            cs.ONE_DRIVE: "FilePath",
            cs.DATABASE: "Subject",
            cs.GOOGLE_DRIVE: "FilePath",
            cs.SHAREPOINT: "FilePath",
            cs.FILE_SYSTEM: "FilePath"
        }
        column_name = columns_dict[data_source]
        db_entities_dict = {}
        db_table = ActivateUtils.db_get_entities_dict_from_sqllite(db_path)
        for row in db_table['result']:
            if column_data == row[column_name]:
                for entity in entities_list:
                    if row[entity] is not None:
                        db_entities_dict[entity.lower()] = \
                            sorted(
                                [item.strip() for item in row[entity].split(entity_separator)],
                                key=str.lower
                            )
                break
        return db_entities_dict

    @staticmethod
    def execute_query(db_path, query, is_update=False):
        """Executes a DB query on the given DB

            Args:
                db_path     (str)   --  database file path
                query       (str)   --  DB query to be executed
                is_update   (bool)  --  specify whether given query is update query (Default:false)

            Returns:
                Dictionary with the result of the DB query

        """
        connection = sqlite3.connect(db_path)
        dict1 = None
        if is_update:
            connection.execute(query)
            connection.commit()
            dict1 = {'result': []}
        else:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            try:
                column_names = []
                return_list = []
                result = cursor.execute(query)
                for row in result.description:
                    column_names.append(row[0])
                result = result.fetchall()
                for res in range(len(result)):
                    temp_dict = {}
                    for col in range(len(column_names)):
                        temp_dict.update({column_names[col]: result[res][col]})
                    return_list.append(temp_dict)
                dict1 = {'result': return_list}

            except Exception as ex:
                raise Exception("Error {0}".format(ex))

        connection.close()
        return dict1

    @staticmethod
    def db_get_folder_stats_count(db_path):
        """Returns the count of rows present in folderStatsTable DB table

            Args:
                db_path     (str)   --  database file path

            Returns:
                int     --  number of rows

        """
        return int(ActivateUtils.execute_query(db_path=db_path, query="select count(*) from "
                                                                      "folderStatsTable")['result'][0]['count(*)'])

    @staticmethod
    def db_get_folder_size(folder_path, db_path):
        """Returns the size of the given folder path from database

            Args:
                folder_path     (str)   --  folder path
                db_path         (str)   --  database file path

            Returns:
                str     --  folderSize present in the DB for the given folder path

        """
        return ActivateUtils.execute_query(db_path=db_path,
                                           query=f'select folderSize from folderStatsTable where folderPath='
                                                 f'"{folder_path}"')['result'][0]['folderSize']

    @staticmethod
    def db_get_folders_count(folder_path, db_path):
        """Returns the count of all the folders present inside the given folder path

            Args:
                folder_path     (str)   --  folder path
                db_path         (str)   --  database file path

            Returns:
                int     --  count of all the folders present inside the given folder path

        """
        return int(ActivateUtils.execute_query(db_path=db_path,
                                               query=f'select count(*) from folderStatsTable where folderPath '
                                                     f'like "{folder_path}%"')['result'][0]['count(*)']) - 1

    @staticmethod
    def db_get_files_count(folder_path, db_path):
        """Returns the count of all the files present inside the given folder path

                    Args:
                        folder_path     (str)   --  folder path
                        db_path         (str)   --  database file path

                    Returns:
                        int     --  count of all the files present inside the given folder path

                """
        return int(ActivateUtils.execute_query(db_path=db_path,
                                               query=f'select sum(totalFiles) from folderStatsTable where folderPath '
                                                     f'like "{folder_path}%"')['result'][0]['sum(totalFiles)'])

    @staticmethod
    def db_get_access_time(folder_path, db_path):
        """Returns the access time of the given folder path from database

            Args:
                folder_path     (str)   --  folder path
                db_path         (str)   --  database file path

            Returns:
                str     --  accessTime present in the DB for the given folder path

        """
        return ActivateUtils.execute_query(db_path=db_path,
                                           query=f'select max(accessTime) from folderStatsTable where '
                                                 f'folderPath like "{folder_path}%"')['result'][0]['max(accessTime)']

    def run_data_generator(self, data_api_path, data_endpoint, db_path=None):
        """
        Run Data Generator Utility TO Populate Endpoint.
        Args:
            data_api_path: Full Path To Utility
            data_endpoint: Data Endpoint Like Exchange,OneDrive,Database
            db_path:       Database file path

        Returns: Boolean response to JOB Success ot Failure

        """
        self.log.info(
            f"Log File for Data Generation Utility {os.path.join(data_api_path, f'DataGenerator_{data_endpoint}.log')}")
        if db_path is not None:
            data_gen = \
                os.path.join(data_api_path,
                             f'DataGenerator.exe "{data_endpoint}" "{db_path}"') + f' 1> "DataGenerator_{data_endpoint}.log" 2>&1'
        else:
            data_gen = \
                os.path.join(data_api_path,
                             f'DataGenerator.exe "{data_endpoint}" ') + f' 1> "DataGenerator_{data_endpoint}.log" 2>&1'
        status = Popen(data_gen, cwd=data_api_path,
                       stdout=PIPE, stderr=PIPE, shell=True)
        if status.wait() != 0:
            raise Exception("Data Generation JOB Failed .Please Check LOG")
        self.log.info("Completed Data Generation Succesfully!!")
        return True

    def mail_generate_and_send(self, recepients, mail_api_path):
        """
        Generate Random Mails And Send
        Args:
            recepients: List of Reciepients
            mail_api_path: Path of Mail API root Dir

        Returns:

        """
        mailboxes = recepients.strip().replace(",", ";")
        params_file = os.path.join(mail_api_path, "params.json")
        self.log.info(f"Updating {params_file} with {mailboxes} ")
        if not os.path.exists(params_file):
            raise Exception(f"File Not Found {params_file}")

        data = {}
        with open(params_file, "r") as file:
            data = file.read()
            data = json.loads(data)
            data[cs.EXCHANGE]["recepients"] = mailboxes
            file.close()
        with open(params_file, "w") as file:
            json.dump(data, file)
            file.close()
        if self.run_data_generator(mail_api_path, cs.EXCHANGE):
            self.log.info("Mailing Completed Successfull!!")

    def run_backup_mailbox_job(self, subclient_obj, backupset_obj,
                               subclient_name, exchange_mailbox_alias):
        """
        Run Backup JOB from Commcell
        Args:
            subclient_obj: Subclient Object
            backupset_obj: BackupSet Object
            subclient_name: Name of Subclient
            exchange_mailbox_alias: Mailbox Aliases

        Returns: SMTP of Mailboxes

        """
        associated_users = [elem["alias_name"] for elem in subclient_obj.users]

        input_users = str(exchange_mailbox_alias).split(",")

        mailboxes = []
        if str(exchange_mailbox_alias).lower() == "all mailboxes":
            mailboxes = ["all mailboxes"]
        else:
            new_user_mailbox = list(
                set(input_users).difference(set(associated_users)))
            self.log.info(
                '*' * 5 + f"Selected Mailboxes for Association {new_user_mailbox}" + '*' * 5)
            if len(new_user_mailbox) > 0:
                subclient_obj.set_user_assocaition(
                    {
                        'mailboxNames': new_user_mailbox,
                        'archive_policy': "Archving Policy",
                        'cleanup_policy': "cleanup_policy",
                        'retention_policy': "retention_policy"
                    }
                )
            subclient_obj = backupset_obj.subclients.get(subclient_name)
            mailboxes = [item["smtp_address"] for mail in input_users for item in
                         subclient_obj.users if
                         item["alias_name"] == mail]

        self.log.info(
            '*' * 5 + "Starting Backup JOB for Associated Mailboxes" + '*' * 5)
        job_obj = subclient_obj.backup()
        if not job_obj.wait_for_completion():
            raise Exception("Backup JOB of Associated Subclients Could\
            not be Complted . JOB Status is " + str(job_obj.status))
        self.log.info("Job Completed Successfully!!")
        return mailboxes

    @staticmethod
    def get_user_to_sid_mapping(user_list, target_machine_name=None):
        """
        Get Username to SID mapping dictionary for given user list
        Args:
            user_list (list): List of users
            target_machine_name (str): Host name of remote machine, None for local
        Returns:
            {"username": "sid"} (dictionary)
        """
        user_to_sid = {}
        for user in user_list:
            user_to_sid[user] = win32security.LookupAccountName(
                target_machine_name, user)[0]
        return user_to_sid

    @staticmethod
    def get_user_info(file_path, target_machine_name=None):
        """
        Get File Owner for given file path
        Args:
            file_path (str): Path of file
            target_machine_name (str): Hostname of target machine.
                                        None implies current machine
        Returns:
            "DOMAIN\\OWNER" (str)
        """
        try:
            sd = win32security.GetFileSecurity(
                file_path, win32security.OWNER_SECURITY_INFORMATION)
            owner_sid = sd.GetSecurityDescriptorOwner()
            username = "ORPHAN"
            domain = "ORPHAN"
            if not win32security.ConvertSidToStringSid(owner_sid).__eq__('S-1-0-0-0'):
                username, domain, user_type = win32security.LookupAccountSid(
                    target_machine_name, owner_sid
                )
        except win32security.error as e:
            ActivateUtils().log.info(e)
        return f"{domain}\\{username}"

    @staticmethod
    def set_file_time_info(file_path):
        """
        Set Access Time, Creation Time, Modified Time randomly for
        given file (TimeZone Set GMT standard time)
            Args:
                file_path (str): Full path of file
        """
        create_time_offset = random.randint(3, 8) * 367
        access_time_offset = random.randint(1, 2) * 365
        modified_time_offset = random.randint(1, 2) * 365
        fh = win32file.CreateFile(
            file_path, win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None,
            win32file.OPEN_EXISTING, 0, 0)
        old_create_time, old_access_time, old_modify_time = win32file.GetFileTime(
            fh)
        new_create_time = old_create_time - timedelta(create_time_offset)
        new_access_time = new_create_time + timedelta(access_time_offset)
        new_modified_time = new_create_time + timedelta(modified_time_offset)
        win32file.SetFileTime(fh, new_create_time,
                              new_access_time, new_modified_time)
        win32file.CloseHandle(fh)

    @staticmethod
    def change_file_owner(file_path_list, owner_sid=None,
                          target_machine_name=None, force=True):
        """
        Make the ownership of a given NTFS file/directories to  given sid
            Args:
                file_path_list (list): List of files to make orphan
                owner_sid (PySID): Change ownership of file to this sid.
                                If None is passed makes files orphan
                target_machine_name (str): Hostname of machine on which files reside.
                                        None for local Machine
                force (bool):
        """
        if owner_sid is None:
            owner = win32security.ConvertStringSidToSid('S-1-0-0-0')
        else:
            owner = owner_sid
        try:
            htoken = win32security.OpenThreadToken(
                win32api.GetCurrentThread(),
                win32security.TOKEN_ALL_ACCESS, True)
        except win32security.error:
            htoken = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_ALL_ACCESS)
        prev_state = ()
        if force:
            new_state = [(
                win32security.LookupPrivilegeValue(target_machine_name, name),
                win32security.SE_PRIVILEGE_ENABLED
            ) for name in (win32security.SE_TAKE_OWNERSHIP_NAME, win32security.SE_RESTORE_NAME)]
            prev_state = win32security.AdjustTokenPrivileges(
                htoken, False, new_state)
        file_path = ""
        try:
            sd = win32security.SECURITY_DESCRIPTOR()
            sd.SetSecurityDescriptorOwner(owner, False)
            for file_path in file_path_list:
                win32security.SetFileSecurity(
                    file_path, win32security.OWNER_SECURITY_INFORMATION, sd)
        except win32security.error as e:
            raise OSError(
                'Cannot take ownership of file: {0}. {1}.'.format(file_path, e))
        finally:
            if prev_state:
                win32security.AdjustTokenPrivileges(htoken, False, prev_state)

    @staticmethod
    def convert_readable_format(permission):
        """
        Convert ACL to readable permission
        :param permission: ACL default permission
        :return readable format
        """
        if cs.PERMISSION_DENY in permission:
            permission = cs.PERMISSION_NO_ACCESS_FORMATTED
        elif cs.PERMISSION_EXECUTE in permission and cs.PERMISSION_WRITE in permission:
            permission = cs.PERMISSION_EXECUTE_WRITE_FORMATTED
        elif cs.PERMISSION_EXECUTE in permission:
            permission = cs.PERMISSION_EXECUTE_FORMATTED
        elif cs.PERMISSION_FULL_CONTROL in permission:
            permission = cs.PERMISSION_FULL_CONTROL_FORMATTED
        elif cs.PERMISSION_MODIFY in permission:
            permission = cs.PERMISSION_MODIFY_FORMATTED
        elif cs.PERMISSION_DELETE in permission:
            permission = cs.PERMISSION_DELETE_FORMATTED
        elif cs.PERMISSION_READ in permission and cs.PERMISSION_WRITE in permission:
            permission = cs.PERMISSION_READ_WRITE_FORMATTED
        elif cs.PERMISSION_WRITE in permission:
            permission = cs.PERMISSION_WRITE_FORMATTED
        elif cs.PERMISSION_READ in permission:
            permission = cs.PERMISSION_READ_FORMATTED
        elif cs.PERMISSION_NO_ACCESS in permission:
            permission = cs.PERMISSION_NO_ACCESS_FORMATTED

        return permission

    def get_readable_permission(self, path, target_machine_name=None):
        """
        Get Access Control List for given file or directory
        Args:
            path (str): Path to file or folder
            target_machine_name (str): Name of target machine
        Return:
            {"username": set(permissions)} dict: Return permissions dictionary
        """
        permission_dict = {}
        for line in os.popen("icacls \"%s\"" % path).read().splitlines()[:-1]:
            if not line.__eq__(""):
                line = line.strip()
                if len(line.split(path)) > 1:
                    line = line.split(path)[1].strip()
                user = line.split(":")[0]
                if user.startswith('S-1'):
                    try:
                        user, domain, user_type = win32security.LookupAccountSid(
                            target_machine_name,
                            win32security.ConvertStringSidToSid(user)
                        )
                        user = f"{domain}\\{user}"
                    except Exception as e:
                        self.log.warn(
                            "User to SID lookup failed for user {} due to {}".format(user, e))

                permission = set(line.split(":")[1][1:-1].replace(')(', ',').split(','))
                formatted_permission = ActivateUtils.convert_readable_format(permission)
                permission_dict[user] = formatted_permission
        return json.dumps(permission_dict)

    def read_formatted_acl_from_database(self, full_file_path, database_path):
        """
        Query ACL database for file, folder or root details
        full_file_path - Absolute path of file
        database_path - Location of metadata database
        :return permission list
        """
        full_file_path = full_file_path.replace("'", "''")
        if "\\" in full_file_path:
            query = "SELECT FILE_PERMISSION_READABLE from fso_metadata " \
                    "where PATH LIKE '\\\\{}' OR NAME LIKE '{}'". \
                format(full_file_path, full_file_path[full_file_path.rindex("\\") + 1:])
        else:
            query = "SELECT FILE_PERMISSION_READABLE from fso_metadata " \
                    "where NAME LIKE '{}'".format(full_file_path)
        # self.log.info(query)
        permissions_source = self.query_database(
            database_path, query)
        return permissions_source

    def get_access_control_list(self, path, target_machine_name=None):
        """
        Get Access Control List for given file or directory
        Args:
            path (str): Path to file or folder
            target_machine_name (str): Name of target machine
        Return:
            {"username": set(permissions)} dict: Return permissions dictionary
        """
        permission_dict = {}
        for line in os.popen("icacls \"%s\"" % path).read().splitlines()[:-1]:
            if not line.__eq__(""):
                line = line.strip()
                if len(line.split(path)) > 1:
                    line = line.split(path)[1].strip()
                user = line.split(":")[0]
                if user.startswith('S-1'):
                    try:
                        user, domain, user_type = win32security.LookupAccountSid(
                            target_machine_name,
                            win32security.ConvertStringSidToSid(user)
                        )
                        user = f"{domain}\\{user}"
                    except Exception as e:
                        self.log.warn(
                            "User to SID lookup failed for user {} due to {}".format(user, e))

                permission = set(line.split(":")[1][1:-1].replace(')(', ',').split(','))
                if user in permission_dict.keys():
                    permission_dict[user] = permission_dict[user] | permission
                else:
                    permission_dict[user] = permission
        return permission_dict

    def fetch_acl(self, root, current, is_dir, meta_data, target_machine_name):
        """
               Fetch access list details for files/directories
               Args:
                   root(str) : root directory
                   current (str): current file/directory
                   is_dir (int) : 1 - directory, 0 - file
                   meta_data (list) : current meta_data list
                   target_machine_name (str): Host name of target machine, None for local
                Returns:
                    access control list


               """
        file_os_obj = os.stat(os.path.join(root, current))
        m_timestamp = datetime.fromtimestamp(file_os_obj.st_mtime)
        c_timestamp = datetime.fromtimestamp(file_os_obj.st_ctime)
        a_timestamp = datetime.fromtimestamp(file_os_obj.st_atime)
        file_base_name = os.path.basename(os.path.join(root, current))
        filename, file_type = os.path.splitext(file_base_name)
        if file_type:
            file_type = file_type.replace('.', '')

        temp_dict = {
            cs.FSO_METADATA_FIELD_PARENT_DIR: os.path.join(root, current)[0:os.path.join(root, current).rindex('\\')],
            cs.FSO_METADATA_FIELD_NAME: current,
            cs.FSO_METADATA_FIELD_PATH: os.path.join(root, current),
            cs.FSO_METADATA_FIELD_FILE_SIZE: file_os_obj.st_size,
            cs.FSO_METADATA_FIELD_MIME_TYPE: mimetypes.guess_type(os.path.join(root, current))[0],
            cs.FSO_METADATA_FIELD_MODIFIED_TIME: f"{m_timestamp.date().strftime('%B %d, %Y')} {m_timestamp.time().strftime('%r')}",
            cs.FSO_METADATA_FIELD_CREATED_TIME: f"{c_timestamp.date().strftime('%B %d, %Y')} {c_timestamp.time().strftime('%r')}",
            cs.FSO_METADATA_FIELD_ACCESS_TIME: f"{a_timestamp.date().strftime('%B %d, %Y')} {a_timestamp.time().strftime('%r')}",
            cs.FSO_METADATA_FIELD_FILE_OWNER: ActivateUtils.get_user_info(os.path.join(root, current), target_machine_name),
            cs.FSO_METADATA_FIELD_PARENT_DIR_PERMISSION: str(self.get_access_control_list(
                         os.path.join(root, current)[0:os.path.join(root, current).rindex('\\')],
                         target_machine_name=target_machine_name)),
            cs.FSO_METADATA_FIELD_FILE_PERMISSION: str(self.get_access_control_list(
                os.path.join(root, current),
                target_machine_name=target_machine_name)),
            cs.FSO_METADATA_FIELD_FILE_PERMISSION_READABLE: str(self.get_readable_permission(
                os.path.join(root, current),
                target_machine_name=target_machine_name)),
            cs.FSO_METADATA_FIELD_IS_DIR: is_dir,
            cs.FSO_METADATA_FIELD_FILE_TYPE: file_type
        }

        meta_data.append(temp_dict)
        return meta_data

    def create_fso_metadata_db(self, target_data_path, target_data_db,
                               target_machine_name=None, track_dir_stats=False, meta_data=None, cloud_apps_dir_count=1):
        """
        Create fso metadata database5
        Args:
            target_data_path (str): Fso data path
            target_data_db (str): Target data path
            target_machine_name (str): Host name of target machine, None for local
            track_dir_stats (bool): True to track directories
            -- Only required for cloud apps validation --
            meta_data (list): For cloud_apps, pass meta_data as an argument
            cloud_apps_dir_count (int): For cloud apps, this parameter denotes the number of containers crawled,
                                        it is checked against the dir count parameter
        """

        if os.path.exists(target_data_db):
            os.remove(target_data_db)
        dir_list = list()
        is_file = 0
        is_dir = 1
        cloud_apps = False
        if not meta_data:
            meta_data = list()
            for root, dirs, files in os.walk(target_data_path):
                for name in files:
                    meta_data = self.fetch_acl(root, name, is_file, meta_data, target_machine_name)

                for name in dirs:
                    dir_list.append(os.path.join(root, name))
                    if track_dir_stats:
                        meta_data = self.fetch_acl(root, name, is_dir, meta_data, target_machine_name)
        else:
            cloud_apps = True
            cloud_apps_dir_count = 1  # For cloud apps in Activate, dir_cnt is replaced by container count

        total_dir_count = len(dir_list) if not cloud_apps else cloud_apps_dir_count

        connection = sqlite3.connect(target_data_db)
        create_table_query = '''
        CREATE TABLE fso_metadata (
        ID INTEGER  PRIMARY KEY AUTOINCREMENT,
        PARENT_DIR TEXT NOT NULL,
        NAME TEXT NOT NULL,
        PATH TEXT NOT NULL,
        FILE_SIZE BIGINT NOT NULL,
        MIME_TYPE TEXT NOT NULL,
        MODIFIED_TIME VARCHAR(30) NOT NULL,
        CREATED_TIME VARCHAR(30) NOT NULL,
        ACCESS_TIME VARCHAR(30) NOT  NULL,
        FILE_OWNER VARCHAR(50) NOT NULL,
        TOTAL_DIR_COUNT INT NOT NULL,
        PARENT_DIR_PERMISSION TEXT NOT NULL,
        FILE_PERMISSION TEXT NOT NULL,
        FILE_PERMISSION_READABLE TEXT NOT NULL,
        IS_DIR INT NOT NULL,
        FILE_TYPE VARCHAR(50) NOT NULL
        );
        '''
        connection.execute(create_table_query)
        for data_row in meta_data:
            insert_query = f'''
            INSERT INTO fso_metadata 
            (PARENT_DIR, NAME, PATH, FILE_SIZE,MIME_TYPE,
            MODIFIED_TIME, CREATED_TIME, ACCESS_TIME, 
            FILE_OWNER, TOTAL_DIR_COUNT,
            PARENT_DIR_PERMISSION, FILE_PERMISSION, FILE_PERMISSION_READABLE, IS_DIR, FILE_TYPE) VALUES(
            "{data_row[cs.FSO_METADATA_FIELD_PARENT_DIR]}",
            "{data_row[cs.FSO_METADATA_FIELD_NAME]}",
            "{data_row[cs.FSO_METADATA_FIELD_PATH]}",
            "{data_row[cs.FSO_METADATA_FIELD_FILE_SIZE]}",
            "{data_row[cs.FSO_METADATA_FIELD_MIME_TYPE]}",
            "{data_row[cs.FSO_METADATA_FIELD_MODIFIED_TIME]}",
            "{data_row[cs.FSO_METADATA_FIELD_CREATED_TIME]}",
            "{data_row[cs.FSO_METADATA_FIELD_ACCESS_TIME]}",
            "{data_row[cs.FSO_METADATA_FIELD_FILE_OWNER]}",
            "{total_dir_count}",
            "{data_row[cs.FSO_METADATA_FIELD_PARENT_DIR_PERMISSION]}",
            "{data_row[cs.FSO_METADATA_FIELD_FILE_PERMISSION]}",
            '{data_row[cs.FSO_METADATA_FIELD_FILE_PERMISSION_READABLE]}',
            "{data_row[cs.FSO_METADATA_FIELD_IS_DIR]}",
            "{data_row[cs.FSO_METADATA_FIELD_FILE_TYPE]}"
            );
            '''
            connection.execute(insert_query)
        connection.commit()
        connection.close()

    def create_fso_data(self, target_data_path, file_count,
                        target_machine_name=None):
        """
        Create SQL Database to store FSO entities for Admin Console
        Review
        Args:
            target_data_path (str): Target UNC or local path to dump data
            file_count (atr): Total no of files to be generated
            target_machine_name (str): Hostname of target machine, None for local
        """
        temp_file_count = file_count
        if os.path.exists(target_data_path):
            self.delete_old_data(target_data_path)
        if not target_data_path.startswith("\\") and not os.path.exists(target_data_path):
            os.mkdir(target_data_path)
        duplicate_files_count = 0
        orphan_files_count = 0
        files_path_list = list()
        if 2 < file_count < 5:
            duplicate_files_count = 1
            orphan_files_count = 1
        if file_count >= 5:
            duplicate_files_count = int(
                (random.randint(20, 25) / 100) * file_count)
            orphan_files_count = int(
                (random.randint(20, 25) / 100) * file_count)
        file_count = file_count - duplicate_files_count
        self.log.info(
            "Total File Count %d Duplicate file count %d orphan files count %d"
            % (file_count, duplicate_files_count, orphan_files_count)
        )
        file_per_folder = file_count
        if file_count > 200:
            file_per_folder = int((random.randint(5, 10) / 100) * file_count)
        self.log.info("Generating %d Files per Folder" % file_per_folder)
        while file_count != 0:
            path = os.path.join(target_data_path, f"fso_data_{str(int(time.time()))}")
            os.mkdir(path)
            self.log.info("%s created successfully" % path)
            self.log.info("Generating %d files at %s" %
                          (min(file_count, file_per_folder), path))
            self.sensitive_data_generation(
                path, min(file_count, file_per_folder))
            if file_count < file_per_folder:
                file_count = 0
            else:
                file_count = file_count - file_per_folder

        duplicate_list = []
        orphan_list = []
        dir_list = []
        self.log.info("Crawling %s" % target_data_path)
        for root, dirs, files in os.walk(target_data_path):
            for file in files:
                files_path_list.append(os.path.join(root, file))
            for d in dirs:
                dir_list.append(os.path.join(root, d))
        duplicate_file_path = os.path.join(target_data_path, 'Duplicate_Files')
        if duplicate_files_count > 0:
            self.log.info("Generating Duplicate Files")
            duplicate_list = files_path_list[:duplicate_files_count]
            os.mkdir(duplicate_file_path)
            if os.path.exists(duplicate_file_path):
                self.log.info(f"{duplicate_file_path} created successfully")
            for file in duplicate_list:
                shutil.copy2(file, duplicate_file_path)
        if orphan_files_count > 0:
            self.log.info("Generating Orphan Files")
            orphan_list = files_path_list[file_count - orphan_files_count:]
            ActivateUtils.change_file_owner(
                orphan_list, target_machine_name=target_machine_name)
        duplicate_list_temp = list()
        for i in range(len(duplicate_list)):
            duplicate_list_temp.append(duplicate_list[i])
            temp = duplicate_list[i].rindex("\\")
            duplicate_list[i] = os.path.join(
                duplicate_file_path,
                duplicate_list[i][temp + 1:]
            )
            duplicate_list_temp.append(duplicate_list[i])
        dir_list.append(duplicate_file_path)
        user_list = ['system', 'administrator', 'administrators', 'everyone']
        user_sid_dict = ActivateUtils.get_user_to_sid_mapping(
            user_list, target_machine_name=target_machine_name)
        files_path_list = files_path_list + duplicate_list
        temp_list = list(set(files_path_list) - set(orphan_list))
        i = 0
        while i < len(temp_list):
            for username in user_list[:-1]:
                if i < len(temp_list):
                    self.change_file_owner(
                        [temp_list[i]], owner_sid=user_sid_dict[username],
                        target_machine_name=target_machine_name
                    )
                i = i + 1
        for d in dir_list:
            owner_name = ActivateUtils.get_user_info(
                d, target_machine_name).split("\\")[-1].lower()
            owner_sid = user_sid_dict[owner_name]
            sd = win32security.GetFileSecurity(
                d, win32security.DACL_SECURITY_INFORMATION)
            dacl = win32security.ACL()
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION, con.FILE_ALL_ACCESS, owner_sid)
            d_user_list = list(set(user_list[:-1]) - {owner_name})
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE | con.FILE_GENERIC_EXECUTE,
                user_sid_dict[d_user_list[0]])
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_GENERIC_WRITE,
                user_sid_dict[d_user_list[1]])
            everyone_sid = user_sid_dict["everyone"]
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_GENERIC_READ | con.FILE_LIST_DIRECTORY,
                everyone_sid)
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                d, win32security.DACL_SECURITY_INFORMATION, sd)
        for file in files_path_list:
            owner_name = ActivateUtils.get_user_info(
                file, target_machine_name).split("\\")[-1].lower()
            if owner_name.__eq__("orphan"):
                owner_name = 'administrators'
            owner_sid = user_sid_dict[owner_name]
            sd = win32security.GetFileSecurity(
                file, win32security.DACL_SECURITY_INFORMATION)
            dacl = win32security.ACL()
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION, con.FILE_ALL_ACCESS, owner_sid)
            f_user_list = list(set(user_list[:-1]) - {owner_name})
            dacl.AddAccessAllowedAce(win32security.ACL_REVISION,
                                     con.FILE_GENERIC_READ | con.FILE_GENERIC_WRITE | con.FILE_GENERIC_EXECUTE,
                                     user_sid_dict[f_user_list[0]])
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_GENERIC_WRITE,
                user_sid_dict[f_user_list[1]])
            everyone_sid = user_sid_dict['everyone']
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_GENERIC_READ, everyone_sid)
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                file, win32security.DACL_SECURITY_INFORMATION, sd)
            if file not in duplicate_list_temp:
                ActivateUtils.set_file_time_info(file)
        self.log.info(f"Generated {temp_file_count} files at  {target_data_path}")

    @staticmethod
    def get_random_files_for_actions(commcell_object, ds_name, select_max=False):
        """Selects a random number of files for actions

            Args:
                commcell_object (object) : commcell object
                ds_name         (str)    : data source name
                select_max      (bool)   : whether to select max number of files

            Returns:
                dictionary with all the files details

        """
        log = logger.get_log()
        ds_object = commcell_object.datacube.datasources.get(ds_name)
        is_object = commcell_object.index_servers.get(ds_object.index_server_cloud_id)
        core_name = ds_object.computed_core_name
        total_files = int(is_object.execute_solr_query(
            core_name=core_name,
            select_dict=cs.QUERY_FILE_CRITERIA,
            op_params=cs.QUERY_ZERO_ROWS)[cs.RESPONSE_PARAM][cs.NUM_FOUND_PARAM])
        """ Selects the number of files for each action depending on the given input
         Criteria of selection :
            select_max is True -> selects the min of total_files/3 and Max files allowed to mark (constant)
            select_max is False -> selects a random number between 1 and total_files/3
                                    selects the min of the random number and Max files allowed to mark (constant)
        """
        files_in_each_part = min([random.randint(1, total_files // 3), total_files // 3][select_max],
                                 cs.MAX_FILES_TO_MARK)
        log.info(f"Going to select {files_in_each_part} for each action")
        custom_rows_param = {'start': 0, 'rows': files_in_each_part}
        selected_files_to_delete = is_object.execute_solr_query(
            core_name=core_name,
            select_dict=cs.QUERY_FILE_CRITERIA,
            op_params=custom_rows_param)[cs.RESPONSE_PARAM][cs.DOCS_PARAM]
        custom_rows_param['start'] = files_in_each_part
        selected_files_to_defer = is_object.execute_solr_query(
            core_name=core_name,
            select_dict=cs.QUERY_FILE_CRITERIA,
            op_params=custom_rows_param)[cs.RESPONSE_PARAM][cs.DOCS_PARAM]
        custom_rows_param['start'] = files_in_each_part * 2
        selected_files_to_keep = is_object.execute_solr_query(
            core_name=core_name,
            select_dict=cs.QUERY_FILE_CRITERIA,
            op_params=custom_rows_param)[cs.RESPONSE_PARAM][cs.DOCS_PARAM]
        return {cs.file_actions.SOLR_FILE_DELETE_OPERATION: selected_files_to_delete,
                cs.file_actions.SOLR_FILE_KEEP_OPERATION: selected_files_to_keep,
                cs.file_actions.SOLR_FILE_DEFER_OPERATION: selected_files_to_defer}

    @staticmethod
    def validate_files_marked_for_actions(commcell_obj, files_list, ds_name, action_name):
        """Verifies if the files are marked for delete or not

            Args:
                commcell_obj    (object)    -   commcell object
                files_list      (list)      -   files data list
                ds_name         (str)       -   data source name
                action_name     (enum)      -   type of action ( file_actions() enum class )

            Returns:
                None

        """
        log = logger.get_log()
        ds_object = commcell_obj.datacube.datasources.get(ds_name)
        is_object = commcell_obj.index_servers.get(ds_object.index_server_cloud_id)
        core_name = ds_object.computed_core_name
        select_dict = {cs.CONTENT_ID_PARAM: []}
        custom_rows_param = {'rows': len(files_list)}
        log.info("Creating Solr Query")
        for file_info in files_list:
            select_dict[cs.CONTENT_ID_PARAM].append(file_info[cs.CONTENT_ID_PARAM])
        solr_response = is_object.execute_solr_query(
            core_name=core_name,
            select_dict=select_dict,
            op_params=custom_rows_param)[cs.RESPONSE_PARAM][cs.DOCS_PARAM]
        for doc in solr_response:
            flag = False
            log.info(f"Checking attributes for file {doc[cs.URL_PARAM]}")
            for key in cs.OPERATION_ATTRIBUTES_SOLR_MAP[action_name]:
                if key not in doc:
                    flag = True
                    log.info(f"{key} is not present for {cs.CONTENT_ID_PARAM} : {doc[cs.CONTENT_ID_PARAM]}")
            if action_name != cs.file_actions.SOLR_FILE_DELETE_OPERATION:
                if doc[cs.IGNORE_FROM_DELETE_USER_CATEGORY_SV] != cs.PAYLOAD_CATEGORY_TAG_VALUE_MAP[action_name]:
                    log.info(f"Category value mismatched for {cs.CONTENT_ID_PARAM} : {doc[cs.CONTENT_ID_PARAM]}")
                    log.info(f"Expected value : {cs.PAYLOAD_CATEGORY_TAG_VALUE_MAP[action_name]}")
                    log.info(f"Actual value : {doc[cs.IGNORE_FROM_DELETE_USER_CATEGORY_SV]}")
                    flag = True
            if flag:
                raise Exception(f"Validation failed for file with {cs.CONTENT_ID_PARAM} : {doc[cs.CONTENT_ID_PARAM]}")
            log.info(f"{doc[cs.URL_PARAM]} is marked for {action_name} successfully")
        log.info("All the files are validated successfully")

    def activate_cleanup(self, commcell_obj, exchange_mailbox_client=None, storage_policy_name=None,
                         ci_policy_name=None, library_name=None, index_server_name=None, client_name=None,
                         backupset_name=None):
        """Performs cleanup operation

            Args:
                commcell_obj                (object)    -   commcell object
                exchange_mailbox_client     (str)       -   exchange pseudo client name to be deleted
                storage_policy_name         (str)       -   storage policy name to be deleted
                ci_policy_name              (str)       -   File content indexing policy name to be deleted
                library_name                (str)       -   Library's name which need to be removed from environment
                index_server_name           (str)       -   index server's name which needs to be deleted
                client_name                 (str)       -   commcell client's name of which backupset has to be deleted
                backupset_name              (str)       -   name of the backupset of client_name to be deleted

            Returns:
                None

        """
        if backupset_name and client_name:
            if commcell_obj.clients.has_client(client_name):
                agent = commcell_obj.clients.get(client_name).agents.get(cs.FILE_SYSTEM_IDA)
                if agent.backupsets.has_backupset(backupset_name):
                    self.log.info(f"Backupset {backupset_name} already present. Deleting it")
                    agent.backupsets.delete(backupset_name)
                    self.log.info(f"Backupset {backupset_name} deleted")
        if exchange_mailbox_client:
            if commcell_obj.clients.has_client(exchange_mailbox_client):
                self.log.info(f"Exchange client {exchange_mailbox_client} already present. Deleting it")
                commcell_obj.clients.delete(exchange_mailbox_client)
                self.log.info(f"Exchange client {exchange_mailbox_client} deleted")
        if storage_policy_name:
            if commcell_obj.storage_policies.has_policy(storage_policy_name):
                self.log.info(f"Storage policy {storage_policy_name} already present. Deleting it")
                commcell_obj.storage_policies.delete(storage_policy_name)
                self.log.info(f"Storage policy {storage_policy_name} deleted")
        if ci_policy_name:
            if commcell_obj.policies.configuration_policies.has_policy(ci_policy_name):
                self.log.info(f"CI policy {ci_policy_name} already exists. Deleting it")
                commcell_obj.policies.configuration_policies.delete(ci_policy_name)
                self.log.info(f"CI policy {ci_policy_name} deleted")
        if library_name:
            if commcell_obj.disk_libraries.has_library(library_name):
                self.log.info(f"Library {library_name} already present. Deleting it")
                commcell_obj.disk_libraries.delete(library_name)
                self.log.info(f"Library {library_name} deleted")
        if index_server_name:
            if commcell_obj.index_servers.has(index_server_name):
                self.log.info(f"Index Server {index_server_name} already present. Deleting it")
                IndexServerHelper(commcell_obj, index_server_name).delete_index_server()
                self.log.info(f"Index Server {index_server_name} deleted")
        commcell_obj.run_data_aging()

    def do_operation_on_file(self, target_data_path, operation, username=None, password=None):
        """
        Perform an operation on a randomly chosen file
            Args:
                target_data_path (str): Target UNC or local path to dump data
                operation (str): Operation to be performed.
                username(str): Domain user accessing the target UNC
                password(str): Password to access the target UNC
        """
        machine_obj = Machine()
        machine_ip = machine_obj.ip_address
        drive_letter = "Z"
        if username:
            machine_obj.execute_command(f"net use {drive_letter}: {target_data_path} /user:{username} {password}")
        time.sleep(30)
        if operation == "Modified":
            file_path = random.choice(
                machine_obj.get_files_in_path(f"{drive_letter}:{machine_obj.os_sep}Text{machine_obj.os_sep}"))
        else:
            file_path = random.choice(machine_obj.get_files_in_path(f"{drive_letter}:{machine_obj.os_sep}"))
        file_name = [file_path.split(f'{machine_obj.os_sep}')[-1]]
        if file_path.split('.')[1] != 'txt':
            raise Exception(f"The file {file_name} at {file_path} is not a text file")
        self.log.info(f"Performing {operation} on File : {file_name[0]}")
        operation_time = 0
        if operation == "Modified":
            operation = ["Modified", "Accessed"]
            file_append = open(file_path, "a")
            file_append.write("Now the file has more content!")
            file_append.close()
            operation_time = os.path.getmtime(file_path)
        if operation == "Deleted":
            operation = ["Deleted", "Accessed"]
            os.remove(file_path)
            parent_folder_path = f'{machine_obj.os_sep}'.join(file_path.split(f'{machine_obj.os_sep}')[:-1])
            operation_time = os.path.getmtime(parent_folder_path)
        if operation == "Accessed":
            operation = ["Accessed"]
            read_file = open(file_path, "rb")
            read_file.readline()
            read_file.close()
            operation_time = os.path.getatime(file_path)
        if operation == "Renamed":
            operation = ["Renamed"]
            if '.' not in file_path:
                file_path_renamed = file_path + "_" + str(int(time.time()))
            else:
                file_path_renamed = file_path.split('.')
                file_path_renamed[-2] = file_path_renamed[-2] + "_" + str(int(time.time()))
                file_path_renamed = '.'.join(file_path_renamed)
            file_name.append(file_name[0].split('.')[0] + "_" + str(int(time.time())) + '.' + file_name[0].split('.')[1])
            os.rename(file_path, file_path_renamed)
            parent_folder_path = f'{machine_obj.os_sep}'.join(file_path.split(f'{machine_obj.os_sep}')[:-1])
            operation_time = os.path.getmtime(parent_folder_path)
        machine_obj.execute_command(f"net use /delete {drive_letter}:")
        return username, operation, file_name, operation_time, file_path, machine_ip

    @staticmethod
    def db_get_total_files_count(db_path, table_name="entity"):
        """Returns the count of files present in the given table

                    Args:
                        db_path         (str)   --  database file path
                        table_name      (str)   --  Name of the table
                    Returns:
                        int                     --  total count of files present in the table

                """
        return int(ActivateUtils.execute_query(db_path=db_path,
                                               query='select count(FilePath) as '
                                                     f'TotalFiles from  {table_name} ')['result'][0]['TotalFiles'])

    def create_share_and_generate_data(self, machine_name, share_name, file_count, user_name=None, password = None):
        """Creates a new share one the machine and generates data on the machine

            Args:
                machine_name    (str)       --  Machine name of the remote machine
                share_name      (str)       --  Share name to be given for the new UNC path
                file_count      (int)       --  Number of files to be created on share
                user_name       (str)       --  Username for the remote machine
                password        (str)       --  password for given user on remote machine

            Returns:
                (str)                       --  Local path of the dataset folder
                (str)                       --  UNC path or share path of the dataset folder

        """
        cache_machine_key = f"{machine_name}{GeneralConstants.MACHINE_OBJ_CACHE}"
        if self._automation_cache.is_exists(cache_machine_key):
            machine_obj = self._automation_cache.get_key(key=cache_machine_key)
        else:
            machine_obj = Machine(machine_name=machine_name, commcell_object=self._commcell,
                                  username=user_name, password=password)
            self._automation_cache.put_key(key=cache_machine_key, value=machine_obj)
        option_selector = OptionsSelector(self._commcell)
        drive_name = option_selector.get_drive(machine_obj)
        share_path = drive_name + share_name
        unc_path = machine_obj.get_unc_path(share_path)
        machine_obj.create_directory(directory_name=share_path)
        machine_obj.share_directory(share_name=share_name, directory=share_path)
        self.create_fso_data(target_data_path=unc_path, file_count=file_count)
        return share_path, unc_path

    def generate_fso_datasource_config(self, csv_file_path=AUTOMATION_DIRECTORY, file_count=cs.DEFAULT_FILE_COUNT):
        """Generates a csv config file which can be imported on FSO landing page to add more than one datasource
            Args:
                csv_file_path           :   (str)   path to the folder where csv file has to be created
                file_count              :   (int)   number of files to be generated for each live crawl datasource

            Returns:
                list    :   list of dictionaries containing the config of all data sources
                str     :   file path string where ADM csv file has been exported to
                dict    :   dictionary consisting of validation details clubbed together on basis of hostnames

        """
        config_data = []
        validation_data = {
            cs.ONLINE_CRAWL_DS: {},
            cs.BACKEDUP_DS: {}
        }
        csv_file = os.path.join(csv_file_path, cs.DEFAULT_CSV_NAME % str(datetime.now().timestamp()))
        number_of_unc_ds = self._data_source_management_constants.UNCPathDS
        number_of_local_ds = self._data_source_management_constants.LocalPathDS
        number_of_backedup_ds = self._data_source_management_constants.BackedupDS

        for data_source in range(number_of_unc_ds):
            nas_client = random.choice(self._data_source_management_constants.NASClients)
            nas_host_name = nas_client.hostname
            nas_user_name = nas_client.username
            nas_password = nas_client.password
            data_source_name = f"UNC_DS_{nas_host_name}_{data_source}"
            cache_machine_key = f"{nas_host_name}{GeneralConstants.MACHINE_OBJ_CACHE}"
            if self._automation_cache.is_exists(cache_machine_key):
                nas_machine_obj = self._automation_cache.get_key(key=cache_machine_key)
            else:
                nas_machine_obj = Machine(machine_name=nas_host_name,
                                          username=nas_user_name,
                                          password=nas_password,
                                          commcell_object=self._commcell)
                self._automation_cache.put_key(key=cache_machine_key, value=nas_machine_obj)
            local_path, unc_path = self.create_share_and_generate_data(
                machine_name=nas_host_name,
                password=nas_password,
                user_name=nas_user_name,
                share_name=data_source_name,
                file_count=file_count
            )
            config_data.append({
                cs.CSV_HEADER_HOST_NAME: nas_host_name,
                cs.CSV_HEADER_CRAWL_TYPE: cs.LIVE_CRAWL_TYPE,
                cs.CSV_HEADER_FROM_BACKUP: cs.DEFAULT_BACKUP_STATUS,
                cs.CSV_HEADER_COUNTRY: self._data_source_management_constants.Country,
                cs.CSV_HEADER_USERNAME: nas_user_name,
                cs.CSV_HEADER_PASSWORD: nas_password,
                cs.CSV_HEADER_DC_PLAN: self._data_source_management_constants.PlanName,
                cs.CSV_HEADER_ACCESS_NODE: random.choice(self._data_source_management_constants.AccessNode),
                cs.CSV_UNC_SHARE_PATH: unc_path,
                cs.CSV_DATA_SOURCE_NAME: data_source_name})
            if nas_host_name not in validation_data.get(cs.ONLINE_CRAWL_DS):
                validation_data.get(cs.ONLINE_CRAWL_DS).update({nas_host_name: []})
            validation_data.get(cs.ONLINE_CRAWL_DS).get(nas_host_name).append({
                cs.CSV_UNC_SHARE_PATH: unc_path,
                cs.CSV_DATA_SOURCE_NAME: data_source_name,
                cs.FSO_DATA_SOURCE_DOCUMENT_COUNT: nas_machine_obj.get_files_in_path(unc_path)
            })

        for data_source in range(number_of_local_ds):
            commcell_client = random.choice(self._data_source_management_constants.CommcellClients)
            data_source_name = f"Local_DS_{commcell_client}_{data_source}"
            cache_machine_key = f"{commcell_client}_{GeneralConstants.MACHINE_OBJ_CACHE}"
            if self._automation_cache.is_exists(cache_machine_key):
                client_machine_obj = self._automation_cache.get_key(key=cache_machine_key)
            else:
                client_machine_obj = Machine(machine_name=commcell_client)
                self._automation_cache.put_key(key=cache_machine_key, value=client_machine_obj)
            local_path, unc_path = self.create_share_and_generate_data(
                machine_name=commcell_client,
                share_name=data_source_name,
                file_count=file_count
            )
            config_data.append({
                cs.CSV_HEADER_HOST_NAME: commcell_client,
                cs.CSV_HEADER_CRAWL_TYPE: cs.LIVE_CRAWL_TYPE,
                cs.CSV_HEADER_FROM_BACKUP: cs.DEFAULT_BACKUP_STATUS,
                cs.CSV_HEADER_COUNTRY: self._data_source_management_constants.Country,
                cs.CSV_HEADER_DC_PLAN: self._data_source_management_constants.PlanName,
                cs.CSV_UNC_SHARE_PATH: local_path,
                cs.CSV_DATA_SOURCE_NAME: data_source_name})
            if commcell_client not in validation_data.get(cs.ONLINE_CRAWL_DS):
                validation_data.get(cs.ONLINE_CRAWL_DS).update({commcell_client: []})
            validation_data.get(cs.ONLINE_CRAWL_DS).get(commcell_client).append({
                cs.CSV_UNC_SHARE_PATH: local_path,
                cs.CSV_DATA_SOURCE_NAME: data_source_name,
                cs.FSO_DATA_SOURCE_DOCUMENT_COUNT: client_machine_obj.get_files_in_path(local_path)
            })

        backedup_choices = list(self._data_source_management_constants.BackedupClients).copy()
        if number_of_backedup_ds > len(backedup_choices):
            raise Exception("Insufficient backedup clients available for scale testing")
        for data_source in range(number_of_backedup_ds):
            backedup_client = random.choice(backedup_choices)
            backedup_choices.remove(backedup_client)
            data_source_name = f"Backedup_DS_{backedup_client}_{data_source}"
            config_data.append({
                cs.CSV_HEADER_HOST_NAME: backedup_client,
                cs.CSV_HEADER_CRAWL_TYPE: cs.FROM_BACKUP_CRAWL_TYPE,
                cs.CSV_HEADER_FROM_BACKUP: cs.FROM_BACKUP_STATUS,
                cs.CSV_HEADER_COUNTRY: self._data_source_management_constants.Country,
                cs.CSV_HEADER_DC_PLAN: self._data_source_management_constants.PlanName,
                cs.CSV_DATA_SOURCE_NAME: data_source_name})
            validation_data.get(cs.BACKEDUP_DS).update({backedup_client: [{
                cs.CSV_DATA_SOURCE_NAME: data_source_name
            }]})

        with open(csv_file, 'w') as f:
            csv_writer = csv.DictWriter(f, fieldnames=cs.CSV_HEADERS)
            csv_writer.writeheader()
            for row in config_data:
                csv_writer.writerow(row)
        return config_data, csv_file, validation_data

    def create_commcell_entities(self, commcell, media_agent_name, client, path, **kwargs):
        """Creates all the required entities and returns V2 subclient object

            Args:
                commcell (object)       -- An instance of the Commcell class

                media_agent_name (str)  -- Name of the media agent

                client (object)         -- An instance of the Client class

                path (str)              -- Path to add to the subclient

                **kwargs  (dict)        -- Optional arguments

                Available kwargs options:

                    id (str)                   --  Id of the testcase

                    enable_ci  (bool)          --  Whether or not to enable CI

                    index_server_name  (str)   --  Index server name

                    accesss_node_name  (str)   --  Access node name

            Returns:
                subclient_obj(dict)     -- The subclient object

            Raises:
                SDKException:
                   If backupset fails to get created

                   If type of the client name arg is not a string or int

                   If no client exists with the given name

                   If subclient fails to get created for any reason

        """
        if "id" in kwargs:
            id = kwargs["id"]
        else:
            id = random.randrange(cs.RANDOM_INT_LOWER_LIMIT,
                                  cs.RANDOM_INT_UPPER_LIMIT)
        ma_machine = Machine(machine_name=media_agent_name,
                             commcell_object=commcell)
        media_agent_object = MediaAgent(commcell, media_agent_name)
        subclient_name = f"{id}_subclient"
        library_name = f"{id}_library"
        storage_policy_name = f"{id}_storagepolicy"
        backupset_name = f"{id}_backupset"
        file_policy_name = f"{id}_filepolicy"
        self.log.info(f"Commcell object is {commcell}")
        self.log.info(f"Media agent name is {media_agent_name}")
        drive_letter = OptionsSelector(commcell).get_drive(ma_machine)
        mount_path = f"{drive_letter}library_{id}"
        self.log.info(client.properties.get('client'))
        fs_agent_object = client.agents.get(cs.FILE_SYSTEM_IDA)
        self.log.info(f"Creating new Library {library_name}")
        commcell.disk_libraries.add(
            library_name, media_agent_object, mount_path)
        self.log.info(f"Library {library_name} created")
        self.log.info(
            f"Creating new storage policy {storage_policy_name}")
        commcell.storage_policies.add(storage_policy_name=storage_policy_name,
                                      library=library_name, media_agent=media_agent_object)
        self.log.info(f"Storage policy {storage_policy_name} created")

        self.log.info(f"Creating new backupset {backupset_name}")
        fs_agent_object.backupsets.add(backupset_name)
        self.log.info(f"Backupset {backupset_name} created")
        self.log.info(
            f"Adding new subclient {subclient_name} to backupset {backupset_name}")
        subclient_obj = fs_agent_object.backupsets.get(
            backupset_name).subclients.add(subclient_name, storage_policy_name)
        self.log.info(f"Subclient {subclient_name} added")
        self.log.info("Adding content to subclient")
        subclient_obj.content = [path]
        self.log.info(f"Content added to subclient {path}")
        if "enable_ci" in kwargs and kwargs.get("enable_ci"):
         self.log.info(f"Creating new CI policy {file_policy_name}")
         policy_object = commcell.policies.configuration_policies.\
             get_policy_object('ContentIndexing', file_policy_name)

         if "index_server_name" in kwargs and "access_node" in kwargs:
          policy_object.index_server_name = kwargs.get('index_server_name')
          policy_object.data_access_node = kwargs.get('access_node')
         else:
          raise Exception(
              "Either index server name or access node is not specified")

         self.log.info(f"Policy object is {policy_object}")
         file_policy_object = commcell.policies.configuration_policies.add_policy(
             policy_object)
         self.log.info(f"File policy object is {file_policy_object}")
         subclient_obj.enable_content_indexing(
             file_policy_object.configuration_policy_id)
         self.log.info(
             f"Subclient marked for content indexing with policy {file_policy_name}")
        return subclient_obj

    def get_date_time_dict_calendarview(self, date_object):
        """
        Returns the date or time dict for CalendarView class
        Args:
                date_object (str)  - Datetime string

        Returns:
                dict  - dictionary of date and time strings
        """
        month = date_object.strftime('%B')
        date = {'year': date_object.year, 'month': month,
                'day': date_object.day
                }
        session = "PM" if date_object.hour > 12 else "AM"
        hour = date_object.hour if date_object.hour < 12 else date_object.hour-12
        time = {'hour': hour, 'minute': date_object.minute,
                'session': session}

        return {'date': date, 'time': time}
    
    def get_random_file_from_path(self, machine, path):
        """
        Gets a random file from the path
            Args:
               machine --  Machine class object
               path    --  File path
            
            Returns:
               str   - file name from the path
        """
        files = machine.get_files_in_path(path)
        index = random()
        index = math.ceil(index*len(files))
        file = files[index]
        file = os.path.basename(file)
        self.log.info(f"Random file chosen is {file}")
        return file

    def apply_new_permissions(self, machine_name, user, path, access_permissions=None, grant=True):
        """Applies new permissions on given folder
            Args:
                machine_name        (str)   -   Machine name
                user                (str)   -   Username on which permissions to apply
                path                (str)   -   Folder/File path
                access_permissions  (set)   -   Set of new basic access permissions
                grant               (bool)  -   Whether to accept or deny the given permission
        """
        if access_permissions is None:
            raise Exception("Please provide at least one permission on file/folder")
        user_sid = str(self.get_user_to_sid_mapping(user_list=[user],
                                                    target_machine_name=machine_name)[user]).split(":")[1]
        access = ['deny', 'grant'][grant]
        machine_obj = Machine(machine_name=machine_name, commcell_object=self._commcell)
        if not machine_obj.check_directory_exists(path):
            raise Exception(f"Provided folder : {path} is not present on machine : {machine_name}")
        machine_obj.execute_command(f"icacls {path} /{access} *{user_sid}:\"({','.join(access_permissions)})\"")
