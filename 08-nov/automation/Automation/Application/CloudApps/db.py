# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module for performing JSON read/write operations for Google data.

DbOperations is the only class is defined in this file.

DbOperations: Performs database (CRUD) operations using TinyDB.
             Uses JSON storage by default

DbOperations:
        __init__(cloud_object)  --  Initializes the DbOperation object by creating a JSON db

        save_into_table()   --  Method to create and table and save the data into it

        search_label()  --  Method to search whether a label exists in the labels table

        get_length()    --  Method to check the length of a table of database

        get_content()   --  Method to fetch all the content of a table

        get_message_id_list()   --  Method to get the ids of all messages from
        message property table

        check_db_length()   --  Method to check whether both the tables contain
        same number of documents

        get_folder_cvid()   --  Method to get the folder CVID of the
        already uploaded folder to GDrive

        search_md5checksum()    --  Method to search whether a label exists in the labels table

"""
from tinydb import TinyDB, Query
from . import constants
from .exception import CVCloudException
import sqlite3
from AutomationUtils.machine import Machine


class DbOperations:
    """Class for performing database operations on TinyDB"""

    def __init__(self, cc_object):
        """Initializes the DbOperation object by creating a JSON db

                Args:

                    cc_object (object)  --  Instance of CloudConnector class

                Returns:

                    object  --  Instance of DbOperations class

        """
        self.tc_object = cc_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.log.info('Initializing db object')

        if self.tc_object.instance.ca_instance_type == 'GMAIL':
            self.log.info('This is GMail backup. Initializing db object for GMail.')
            db_name = constants.GMAIL_DB_NAME

        elif self.tc_object.instance.ca_instance_type == 'GDRIVE':
            self.log.info('This is GDrive backup. Initializing db object for GDrive.')
            db_name = constants.GDRIVE_DB_NAME

        elif self.tc_object.instance.ca_instance_type == 'ONEDRIVE':
            self.log.info('This is OneDrive backup. Initializing db object for OneDrive')
            db_name = constants.ONEDRIVE_DB_NAME

        self.dbo = TinyDB(db_name, sort_keys=True, indent=4, separators=(',', ': '))
        self.log.info('Purging existing tables to clear the db')
        self.dbo.purge_tables()

    def save_into_table(self, user_id, data, data_type):
        """Method to create and table and save the data into it.

                Args:

                    user_id  (str)  -- SMTP address of the user

                    data        (list or dict)  --  data to write into the table

                                In case of list, it should be list of dicts

                    data_type  (str)  --  Type of the data to insert/update db

                        Valid Values:

                            messages  --  If the data parameter contains message properties

                            labels  -- If data parameter contains label properties

                            files  --  If the data contains GDrive file information

                            list  --  If the data contains job related info

        """
        if not isinstance(data, list) and not isinstance(data, dict):
            raise CVCloudException(self.app_name, '101')

        tbl = self.dbo.table(name=user_id + data_type)

        self.log.info('inserting data into the db: %s', tbl.name)

        if isinstance(data, list):
            for element in data:
                if isinstance(element, dict):
                    if 'id' in element:
                        if tbl.contains(Query().id == element['id']):
                            tbl.remove(Query().id == element['id'])
                tbl.insert(element)
        else:
            if 'id' in data:
                if tbl.contains(Query().id == data['id']):
                    tbl.remove(Query().id == data['id'])
            tbl.insert(data)

    def delete_table(self, name):
        """Method to delete a table with given name

            Args:

                name    (str)   --  Name of the table to be deleted

        """
        self.dbo.purge_table(name)
        self.log.info(f'Deleted table: {name}')

    def search_label(self, value, user_id):
        """Method to search whether a label exists in the labels table

                Args:

                    value  (str)  --  Name of the label to search in the table

                    user_id  (str)  --  smtp address of the user. This is prefixed in the table name

                Returns:

                    True  --  If the value exists in the table

                    False --  If the value doesn't exist in the table

        """

        table_name = f'{user_id}_labels'

        table = self.dbo.table(table_name)
        self.log.info('searching in the table %s', table_name)
        self.log.info('value to search for: %s', value)
        ret = table.contains(
            (Query().name == value) | (
                    Query().name == value.lower()) | (
                    Query().name == value.upper()))
        self.log.info('match result: %s', ret)
        ret_value = table.search(
            (Query().name == value) | (
                    Query().name == value.lower()) | (
                    Query().name == value.upper()))
        self.log.info('ret value: %s', ret_value)
        total_messages = 0
        if ret:
            total_messages = ret_value[0]['messagesTotal']
        return ret, total_messages

    def get_length(self, table_name):
        """Method to check the length of a table of database.

                Args:

                    table_name  (str)  --  Name of the table or database

                Returns:

                    length  (int)  --  Number of documents in a table or database

        """
        table = self.dbo.table(table_name)

        return len(table)

    def get_content(self, table_name):
        """Method to fetch all the content of a table.

                Args:

                    table_name  (str)  --  Name of the table or database

                Returns:

                    content  (list or Dict)  --  content of the table

        """

        table = self.dbo.table(table_name)

        return table.all()

    def get_message_id_list(self, user_id):
        """Method to get the ids of all messages from message property table

                Args:

                    user_id  (str)  --  SMTP address of the user

                Returns:

                    List  (list)  --  List of the messages ids

        """

        table = self.dbo.table(f'{user_id}{constants.MESSAGES_TABLE}')
        idlist = []

        for item in table:
            idlist.append(item['msg_id'])

        return idlist

    def check_db_length(self, user_id):
        """Method to check whether both the tables contain same number of documents.
            This method will be used to check the number of document in the table before backup
            and the table after restore.

                Args:

                    user_id  (str)  --  SMTP address of the user

                Returns:

                    boolean

        """

        table1 = self.dbo.table(f'{user_id}{constants.MESSAGES_TABLE}')

        table2 = self.dbo.table(f'{user_id}{constants.MESSAGES_AFTER_RES_TABLE}')

        if len(table1) == len(table2):
            return True
        return False

    def get_folder_cvid(self, user_id):
        """Method to get the folder CVID of the already uploaded folder to GDrive

                Args:

                    user_id  (str)  --  SMTP address of the user

                Returns:

                    Id of the folder (str)

        """
        try:
            table = self.dbo.table(f'{user_id}{constants.GDRIVE_TABLE}')

            folder_id = table.search(Query().folder_id.exists())[0]['folder_id']
            return folder_id
        except Exception:
            self.log.info('folder id could not be retrieved')
            return None

    def search_md5checksum(self, value, user_id):
        """Method to search whether a label exists in the labels table

                Args:

                    value  (str)  --  Name of the label to search in the table

                    user_id  (str)  --  smtp address of the user. This is prefixed in the table name

                Returns:

                    True  --  If the value exists in the table

                    False --  If the value doesn't exist in the table

        """
        table_name = f'{user_id}_files'

        table = self.dbo.table(table_name)
        self.log.info('searching in the table %s', table_name)
        self.log.info('value to search for: %s', value)
        ret = table.contains(Query().md5Checksum == value)
        self.log.info('match result: %s', ret)
        return ret


class SQLiteOperations:
    """Class for performing database operations with SQLite DB Browser"""

    def __init__(self, cc_object):
        """Initializes the SQLiteOperations object

                Args:

                    cc_object (object)  --  Instance of CloudConnector class

                Returns:

                    object  --  Instance of SQLiteOperations class

        """
        self.tc_object = cc_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.log.info('Initializing SQLite object')

        if not getattr(self.tc_object, "is_tenant", False):
            self.machine = Machine(machine_name=cc_object.tc_object.instance.proxy_client,
                                   commcell_object=cc_object.tc_object.commcell)

    def get_failed_files_local_db(self):
        """Method to get the list of failed files present in FailedItems table from local DB
            table from the local DB

                Returns:
                    failed files present in the FailedItems table (list)

        """
        try:
            files_list = []
            path = self.machine.get_registry_value(f'{constants.REG_KEY_BASE}', f'{constants.PATH_KEY}')
            sc_content = self.tc_object.subclient.content
            user_id = None
            for content in sc_content:
                user_id = content.get('SMTPAddress')
            sqlite_file = (
                f'{path}'
                f'{constants.ONEDRIVE_JOB_DIRECTORY_PATH.format(self.tc_object.subclient.subclient_id, user_id)}'
            )
            query = 'SELECT Path FROM FailedItems'
            output = self.excute_query(sqlite_file, query)

            if output:
                for path in output:
                    for file in path:
                        file_str = file.rsplit('/', 1)[1]
                        files_list.append(file_str)
                return files_list

        except Exception:
            self.log.info("failed to get the data from local DB")
            raise CVCloudException(self.app_name, '101')

    def get_discover_users_local_db(self):
        """Method to get the users of OneDrive client from the local DB

              Returns:
                    All Users present in the client (list)

        """
        try:
            users_list = []
            path = self.machine.get_registry_value(f'{constants.REG_KEY_BASE}', f'{constants.PATH_KEY}')
            sqlite_file = (
                f'{path}'
                f'{constants.ONEDRIVE_DISCOVER_PATH.format(self.tc_object.client.client_id, self.tc_object.client.client_name)}')

            query = 'SELECT Email FROM {tn}'.format(tn=f'Users')
            output = self.excute_query(sqlite_file, query)

            if output:
                for item in output:
                    for user in item:
                        user_str = user.split(';', 1)[0]
                        users_list.append(user_str)
                return users_list
        except Exception:
            self.log.info("failed to get the data from local DB")
            raise CVCloudException(self.app_name, '101')

    def get_last_cache_update_time(self, is_group=False):
        """
        Method to retrieve the last cache update time from local db
        Returns:
            the last cache update time in epoch format
        """
        try:
            temp_path = self.machine.get_registry_value(f'{constants.REG_KEY_BASE}', f'{constants.PATH_KEY}')
            path = f'\\\\{self.machine.ip_address}\\{temp_path[0]}${temp_path[2:]}'
            if is_group:
                sqlite_file = (f'{path}'
                               f'{constants.ONEDRIVE_V2_GROUP_DISCOVER_PATH.format(self.tc_object.client.client_id, self.tc_object.client.client_name)}')
            else:
                sqlite_file = (f'{path}'
                               f'{constants.ONEDRIVE_V2_USER_DISCOVER_PATH.format(self.tc_object.client.client_id, self.tc_object.client.client_name)}')
            query = 'select LastCheckTime from JobInfo'
            self.log.info(f'sqlite_file: {sqlite_file}')
            self.log.info(f'query: {query}')
            output = self.excute_query(sqlite_file, query)[0][0]
            return output
        except Exception:
            self.log.info("failed to get the data from local DB")
            raise CVCloudException(self.app_name, '101')

    def get_job_info_local_db(self, job_id):
        """Method to get the job info(JobId, Status, NextLink4OneDriveChangeList, LastOneNoteModificationTime) from
            JobHistory table in local DB for a particular job id

                Returns:
                    list contains JobId, Status, NextLink4OneDriveChangeList, LastOneNoteModificationTime (list)

        """
        try:
            path = self.machine.get_registry_value(f'{constants.REG_KEY_BASE}', f'{constants.PATH_KEY}')
            sc_content = self.tc_object.subclient.content
            user_id = None
            for content in sc_content:
                user_id = content.get('SMTPAddress')

            sqlite_file = (
                f'{path}'
                f'{constants.ONEDRIVE_JOB_DIRECTORY_PATH.format(self.tc_object.subclient.subclient_id, user_id)}'
            )

            query = 'SELECT * FROM JobHistory WHERE JobId = {id}'.format(id=job_id)
            output = self.excute_query(sqlite_file, query)
            return output
        except Exception:
            self.log.exception("failed to get the data from local DB")
            raise CVCloudException(self.app_name, '101')

    def excute_query(self, file_path, query):
        """
        Method to execute the query

                Args:

                    file_path (str)    (str)   --  Local path to the db file

                    query (str)  --  Query to be executed

                returns:

                    Result of the SQLite Query

        """
        connection = sqlite3.connect(file_path)

        cursor = connection.cursor()
        cursor.execute(query)

        output = cursor.fetchall()
        connection.close()

        return output
