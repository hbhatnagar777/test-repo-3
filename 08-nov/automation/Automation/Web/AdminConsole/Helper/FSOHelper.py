# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run FSO
AdminConsole Automation test cases.

Class:

    FSO()

Functions:

    create_sqlite_db_connection()    --   Establishes connection to the
                                        SQLite Database at the given file path
    close_existing_connections()    --  Close existing SQLite DB Connections
    db_get_orphan_files_count()     -- Get the count of orphan files from FSO db.
    get_fso_file_count_db()         -- Get Total file count from FSO db
    get_fso_dir_count_db()          -- Get Total dir count frm FSO db
    get_fso_data_size_db()          -- Get total file size from FSO db
    get_file_types_db()             -- Get count of distinct file types from FSO db.
    get_owner_count_db()            -- Get count of distinct owners from FSO db
    duplicate_dashboard_data_db()   -- Get duplicate dashboard data from FSO db
    get_db_column_data()            -- Get data for a particular column from FSO db
    get_file_security_dashboard_info() -- Get files security dashboard info from FSO db
    review_size_distribution_dashboard() -- Review size distribution dashboard in FSO
    review_file_duplicates_dashboard()  -- Review file duplicates dashboard in fso
    review_fso_file_ownership_dashboard() -- Review file ownership dashboard in FSO
    review_fso_file_security_dashboard() -- Review file security dashboard in FSO
    fetch_fso_files_db()                -- Fetch given number filepath values from FSO db
    fso_cleanup()                       -- Delete FSO data source
    analyze_client_details()            -- Analyze Client Details Page
    analyze_client_expanded_view()      -- Analyze Expanded view for client
    verify_fso_time_data                -- Verify FSO time info
    get_fso_time_metadata               -- Get fso time info from DB
    fso_file_count_formatting           -- Perform FSO dashboard file count formatting
    track_job()                         -- Tracks a job based on the job operation or job id
    do_file_operation()                 -- Do mentioned operation on a randomly chosen file from target data path
    verify_file_monitoring()            -- Verify File Monitoring Report
    navigate_to_datasource_details()    -- Navigates to datasource details page
    get_csv_file_from_machine()         -- Returns the file path to csv file after extracting the zip file

Class:
    FSOServerGroupHelper(FSO)

Functions:
    add_client_group()                  -- Add Client group
    remove_client_group()               -- Remove Client Group
    analyze_server_group_details()      -- Analyze Server group details page


"""

import ast
import calendar
import re
import sqlite3
import time
import zipfile
from datetime import datetime, timedelta

from AutomationUtils import logger, config
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.AdminConsole.Components.table import Table, Rtable, Rfilter
from Web.AdminConsole.GovernanceAppsPages.FileServerLookup import FileServerLookup
from Web.AdminConsole.GovernanceAppsPages.FileStorageOptimization import \
    FileStorageOptimization, FileStorageOptimizationClientDetails, \
    FsoDataSourceDiscover, FsoDataSourceReview, FsoDataSourceDetails, FsoServerGroupDetails, FSOMonitoringReport
from Web.AdminConsole.GovernanceAppsPages.InventoryManagerDetails import InventoryManagerDetails
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Reports.Custom import viewer
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import FSO_DASHBOARD_TABS_TO_VERIFY, FILE_MONITORING_OPERATIONS, FSO_DASHBOARD_FILTERS_ID

_SERVER_GROUP_CONSTANTS = config.get_config().DynamicIndex.FSOServerGroupDetails


class FSO:
    """FSO Helper Class"""

    def __init__(self, admin_console, commcell=None, csdb=None):
        """
        FSO helper class provides functions to perform DB operations
        to FSO test DB and perform verify operations on FSO
        Args:
            admin_console : Admin Console Object
            commcell : Commcell Object
            csdb : CSDB Object
        """
        self.__admin_console = admin_console
        self.log = logger.get_log()
        self.commcell = commcell
        self.csdb = csdb
        self.sqlitedb = None
        self.fso_obj = FileStorageOptimization(self.__admin_console)
        self.fso_client_details = FileStorageOptimizationClientDetails(self.__admin_console)
        self.fso_data_source_discover = FsoDataSourceDiscover(self.__admin_console)
        self.fso_data_source_review = FsoDataSourceReview(self.__admin_console)
        self.fso_data_source_details = FsoDataSourceDetails(self.__admin_console)
        self.fso_server_group_details = FsoServerGroupDetails(self.__admin_console)
        self.fso_monitoring_report_details = FSOMonitoringReport(self.__admin_console)
        self.file_server_lookup = FileServerLookup(self.__admin_console)
        self.credential_manager = CredentialManager(self.__admin_console)
        self.activate_utils = ActivateUtils()
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__rtable_job = Rtable(admin_console, id="activeJobsTable")
        self._data_source_name = None
        self.backup_file_path = None
        self.__inventory_manager_details = InventoryManagerDetails(
            self.__admin_console)
        self.data_size_mapping = {
            'KB': 1, 'MB': 2, 'GB': 3, 'TB': 4
        }
        self.data_size_mapper_filter = {
            'KB': 1, 'MB': 2, 'GB': 3, 'TB': 4
        }
        self.data_count_filter = {
            ' ': 0, 'K': 1, 'M': 2, 'B': 3, 'T': 4
        }

    @property
    def data_source_name(self):
        """
        Returns the data source name
        Return:
            (str): Name of FSO data source
        """
        return self._data_source_name

    @data_source_name.setter
    def data_source_name(self, value):
        """
        Sets the  data source name for FSO client
        Args:
            value (str): Name of FSO data source
        """
        self._data_source_name = value

    def create_sqlite_db_connection(self, sql_database_path):
        """
        Connect to given sql database path
        Args:
            sql_database_path (str): path to database
        """
        self.sqlitedb = sqlite3.connect(sql_database_path)
        self.sqlitedb.row_factory = sqlite3.Row

    def close_existing_connections(self):
        """
        Closes existing SqliteDB connection
        """
        if self.sqlitedb is not None:
            self.sqlitedb.close()

    def db_get_orphan_files_count(self):
        """
        Get Orphan file count from database
        Returns:
            (int): Count of orphan files from the database
        """
        query = '''
        select COUNT(*) as ORPHAN_COUNT from fso_metadata where FILE_OWNER = 'ORPHAN\\ORPHAN'
        '''
        return self.sqlitedb.execute(query).fetchall()[0]['ORPHAN_COUNT']

    def get_fso_time_metadata(self):
        """
        Get AccessTime, CreateTime, Modified Time info
        for fso data source
            Return:
                (list) [sqlite3.Row,sqlite3.Row]
        """
        query = '''select PATH,CREATED_TIME AS "Created Time",ACCESS_TIME AS "Access Time", MODIFIED_TIME AS 
        "Modified Time", FILE_SIZE from fso_metadata '''
        return self.sqlitedb.execute(query).fetchall()

    def get_fso_file_count_db(self):
        """
        Get number of files count from FSO DB
        Returns:
            (int): No of files in FSO DB
        """
        get_file_count_query = '''
        SELECT COUNT(DISTINCT(PATH)) as File_Count from fso_metadata
        '''
        return \
            self.sqlitedb.execute(
                get_file_count_query).fetchall()[0]['File_Count']

    def get_fso_dir_count_db(self):
        """
        Get no of directory in FSO db
        Return:
            (int): No of directory in FSO DB
        """
        get_dir_count_query = '''
        SELECT DISTINCT(TOTAL_DIR_COUNT) as Dir_Count from fso_metadata
        '''
        return \
            self.sqlitedb.execute(
                get_dir_count_query).fetchall()[0]['Dir_Count']

    def get_fso_data_size_db(self):
        """
        Get the sum of file size in bytes
        Returns:
            (int) : Sum of all files size
        """
        get_file_size = '''
        SELECT SUM(FILE_SIZE) as File_Size from fso_metadata
        '''
        return \
            self.sqlitedb.execute(
                get_file_size).fetchall()[0]['File_Size']

    def get_file_types_db(self):
        """
        Get the count of no of file types
        Return:
            (int) :  Count of number of file types
        """
        get__file_types_count = '''
        SELECT COUNT(DISTINCT(MIME_TYPE)) as Mime_Type_Count from fso_metadata
        '''
        return \
            self.sqlitedb.execute(
                get__file_types_count).fetchall()[0]['Mime_Type_Count']

    def get_owner_count_db(self, crawl_type='Live'):
        """
        Get total no of owners count
        Args:
            crawl_type (str): FSO Crawl type Live/Backup
        Returns:
            (int): Count of owner related to fso file data
        """
        if crawl_type.lower() == 'backup':
            get_owner_count = "SELECT COUNT(DISTINCT(FILE_OWNER)) as Owner_Count from\
             fso_metadata where FILE_OWNER NOT LIKE 'ORPHAN\\ORPHAN'"
        else:
            get_owner_count = '''
            SELECT COUNT(DISTINCT(FILE_OWNER)) as Owner_Count from fso_metadata
            '''
        return \
            self.sqlitedb.execute(get_owner_count).fetchall()[0]['Owner_Count']

    def duplicate_dashboard_data_db(self):
        """
        Get ['NAME', 'MODIFIED_TIME', 'FILE_SIZE', 'File_Count', 'Total_Size']
        information for duplicate files in fso db
        Returns:
            [{},{},....]: List of dictionary in the below format
            [{Entity}:Value,....]
        """
        duplicate_dashboard_query = '''
        Select NAME,MODIFIED_TIME,FILE_SIZE,
        COUNT(NAME) as File_Count,sum(FILE_SIZE) as Total_Size
        from fso_metadata GROUP BY NAME,MODIFIED_TIME,FILE_SIZE HAVING COUNT(*) > 1
        '''
        data = self.sqlitedb.execute(duplicate_dashboard_query).fetchall()
        return [dict(item) for item in data]

    def get_db_column_data(self, column_name, columns_alias=None):
        """
        Get the list of items present in mentioned db field
        Args:
            columns_alias (str): Alias for Column name
            column_name (str): Name of column to fetch
        Returns:
            (list): List of column data
        """
        query = f'''
        SELECT {column_name} from fso_metadata
        '''
        if not column_name:
            column_name = columns_alias
        data = self.sqlitedb.execute(query).fetchall()
        return [item[column_name] for item in data]

    def get_file_security_dashboard_info(self):
        """ security dasboard info
        Get FSO File
        """
        permission_dict = {
            'Full Control': set(),
            'Modify Access': set(),
            'Write Access': set(),
            'List Access': set()
        }

        query = '''
        Select PARENT_DIR_PERMISSION, FILE_PERMISSION from fso_metadata
        '''
        data = self.sqlitedb.execute(query).fetchall()
        for item in data:
            dir_perm = ast.literal_eval(item['PARENT_DIR_PERMISSION'])
            file_perm = ast.literal_eval(item['FILE_PERMISSION'])
            for key, val in dir_perm.items():
                if val.__contains__('F'):
                    permission_dict['Full Control'].add(key)
                if val.__contains__('M'):
                    permission_dict['Modify Access'].add(key)
                if len(val.intersection({'W', 'GW', 'GA'})) > 0:
                    permission_dict['Write Access'].add(key)
                if len(val.intersection({'R', 'GR', 'GA', 'RD', 'RX', 'Rc'})) > 0:
                    permission_dict['List Access'].add(key)
            for key, val in file_perm.items():
                if val.__contains__('F'):
                    permission_dict['Full Control'].add(key)
                if val.__contains__('M'):
                    permission_dict['Modify Access'].add(key)
                if len(val.intersection({'W', 'GW', 'GA'})) > 0:
                    permission_dict['Write Access'].add(key)

        permission_dict['Modify Access'] = \
            permission_dict['Full Control'] | permission_dict['Modify Access']
        permission_dict['Write Access'] = \
            permission_dict['Write Access'] | permission_dict['Modify Access']
        permission_dict['List Access'] = \
            permission_dict['List Access'] | permission_dict['Full Control'] | permission_dict[
                'Modify Access']
        return permission_dict

    def fso_file_count_formatting(self, ui_count, db_count):
        """
        Perform FSO dashboards file count formatting
            Args:
                ui_count (str): Count from FSO dashboard
                db_count (int): Count from DB
            Return: Tuple (ui_count, db_count): Formatted UI and DB count
        """
        ui_count = ui_count.replace(',', '')
        temp_list = ui_count.split()
        if len(temp_list) == 2:
            db_count = round(
                db_count / pow(1000, self.data_size_mapper_filter[temp_list[1]]), 2)
            ui_count = temp_list[0]
        return float(ui_count), float(db_count)

    def review_size_distribution_dashboard(self, crawl_type='Live', cloud_apps=False):
        """
        Review FSO Size distribution dashboard
        Args:
            crawl_type (str): Type of FSO crawl Live/Backup

            cloud_apps (bool):  True if running validation for cloud apps
        """
        error_list = list()
        folder_count_offset = 0
        if crawl_type == 'Backup' and self.backup_file_path is not None:
            folder_count_offset = len(self.backup_file_path.split('\\'))
        self.fso_data_source_discover.select_fso_dashboard("Size distribution")
        ui_count = self.fso_data_source_discover.fso_dashboard_entity_count("Files")
        db_count = self.get_fso_file_count_db()
        ui_count, db_count = self.fso_file_count_formatting(ui_count, db_count)
        if ui_count != db_count:
            error_list.append(
                'FILES_COUNT_MISMATCH: {DB: %s,UI: %s}' % (db_count, ui_count))

        folder_element_name = "Folders" if not cloud_apps else "Containers"
        ui_count = self.fso_data_source_discover.fso_dashboard_entity_count(folder_element_name)
        db_count = self.get_fso_dir_count_db()
        ui_count, db_count = self.fso_file_count_formatting(ui_count, db_count)
        if ui_count != (db_count + folder_count_offset):
            error_list.append("FOLDER_COUNT_MISMATCH: {DB: %s,UI: %s}"
                              % (db_count + folder_count_offset, ui_count))
        data_size_ui = self.fso_data_source_discover.fso_dashboard_entity_count(
            "Size").split(' ')
        data_size_db = self.get_fso_data_size_db()
        data_size_db = round(data_size_db / pow(1024, self.data_size_mapping.get(
            data_size_ui[1]
        )), 2)
        if data_size_db != float(data_size_ui[0]):
            error_list.append(
                "FILE_SIZE_MISMATCH: {DB: %s,UI: %s}" % (data_size_db, float(data_size_ui[0])))

        ui_count = int(self.fso_data_source_discover.fso_dashboard_entity_count('File Types'))
        db_count = self.get_file_types_db()

        if db_count != ui_count:
            error_list.append(
                'FILE_TYPE_COUNT_MISMATCH: {DB: %s, UI: %s}' % (db_count, ui_count))

        owner_count = self.get_owner_count_db(crawl_type=crawl_type)
        if cloud_apps:
            owner_count_ui = 1
        else:
            owner_count_ui = int(self.fso_data_source_discover.fso_dashboard_entity_count('Owners'))
        if owner_count != owner_count_ui:
            error_list.append(
                'FILE_OWNERS_COUNT_MISMATCH: {DB: %s,UI: %s}' % (owner_count, owner_count_ui))
        if len(error_list) != 0:
            raise Exception(
                f"Following Errors Occurred in Size distribution dashboard page: {error_list} "
            )

    def review_file_duplicates_dashboard(self):
        """
        Review File duplicates dashboard in FSO
        """
        self.fso_data_source_discover.select_fso_dashboard("File duplicates")
        error_list = []
        ui_count = self.fso_data_source_discover.fso_dashboard_entity_count("Total Files")
        db_count = self.get_fso_file_count_db()
        ui_count, db_count = self.fso_file_count_formatting(ui_count, db_count)
        if ui_count != db_count:
            error_list.append(
                'FILES_COUNT_MISMATCH: {DB: %s,UI: %s}' % (db_count, ui_count))
        data_size_ui = self.fso_data_source_discover.fso_dashboard_entity_count(
            "Size of Files"
        ).split(' ')
        data_size_db = self.get_fso_data_size_db()
        data_size_db = round(data_size_db / pow(1024, self.data_size_mapping.get(
            data_size_ui[1], 2
        )), 2)
        if data_size_db != float(data_size_ui[0]):
            error_list.append(
                "FILE_SIZE_MISMATCH: {DB: %s, UI: %s}" % (data_size_db, float(data_size_ui[0])))
        duplicate_dashboard_data = self.duplicate_dashboard_data_db()
        duplicate_files_count = self.fso_data_source_discover.get_duplicate_file_count().replace('N/A', '0 KB')
        db_duplicate_files_count = len(duplicate_dashboard_data)
        duplicate_files_count, db_duplicate_files_count = self.fso_file_count_formatting(
            duplicate_files_count, db_duplicate_files_count
        )
        duplicate_file_size_db = 0
        for items in duplicate_dashboard_data:
            duplicate_file_size_db = duplicate_file_size_db + items['FILE_SIZE']
        duplicate_file_size_ui = self.fso_data_source_discover.get_duplicate_file_size().replace('N/A', '0 KB').split()
        duplicate_file_size_db = round(duplicate_file_size_db / pow(
            1024, self.data_size_mapping.get(duplicate_file_size_ui[1])
        ), 2)
        if duplicate_files_count != db_duplicate_files_count:
            error_list.append("DUPLICATE_FILES_COUNT_MISMATCH: {DB: %s,UI: %s}"
                              % (db_duplicate_files_count, duplicate_files_count))
        if float(duplicate_file_size_ui[0]) != duplicate_file_size_db:
            error_list.append("DUPLICATE_FILE_SIZE_MISMATCH: {DB: %s,UI: %s}" %
                              (duplicate_file_size_db, float(duplicate_file_size_ui[0])))
        if len(error_list) != 0:
            raise Exception(
                f"Following Errors Occurred in FSO duplicates dashboard page: {error_list} "
            )

    def review_fso_file_ownership_dashboard(self, crawl_type="Live"):
        """
        Review File Ownership dashboard
        Args:
            crawl_type (str): FSO crawl Type
        """
        self.fso_data_source_discover.select_fso_dashboard("File ownership")
        error_list = []
        ui_count = self.fso_data_source_discover.fso_dashboard_entity_count("Files")
        db_count = self.get_fso_file_count_db()
        ui_count, db_count = self.fso_file_count_formatting(ui_count, db_count)
        if ui_count != db_count:
            error_list.append(
                'FILES_COUNT_MISMATCH: {DB: %s, UI: %s}' % (db_count, ui_count))
        data_size_ui = self.fso_data_source_discover.fso_dashboard_entity_count(
            "Size").split(' ')
        data_size_db = self.get_fso_data_size_db()
        data_size_db = round(data_size_db / pow(1024, self.data_size_mapping.get(
            data_size_ui[1]
        )), 2)
        if data_size_db != float(data_size_ui[0]):
            error_list.append("FILE_SIZE_MISMATCH: {DB: %s,UI: %s}"
                              % (data_size_db, float(data_size_ui[0])))

        ui_count = int(self.fso_data_source_discover.fso_dashboard_entity_count('Owners'))
        db_count = self.get_owner_count_db(crawl_type=crawl_type)
        if db_count != ui_count:
            error_list.append(
                'FILE_OWNERS_COUNT_MISMATCH: {DB: %s, UI: %s}' % (db_count, ui_count))

        ui_count = self.fso_data_source_discover.fso_dashboard_entity_count("Orphan Files")
        db_count = self.db_get_orphan_files_count()
        ui_count, db_count = self.fso_file_count_formatting(ui_count, db_count)
        if db_count != ui_count:
            error_list.append(
                "ORPHAN_FILES_COUNT_MISMATCH:{DB: %s,UI: %s}" % (db_count, ui_count))
        if len(error_list) != 0:
            raise Exception(
                f"Following Errors Occurred in FSO Ownership dashboard page: {error_list} "
            )

    def review_fso_file_security_dashboard(self):
        """
        Review file security dashboard

        """
        error_list = []
        self.fso_data_source_discover.select_fso_dashboard("File security")
        db_permission_dict = self.get_file_security_dashboard_info()
        db_count = len(db_permission_dict['Full Control'])
        ui_count = self.fso_data_source_discover.get_file_security_dashboard_user_count(
            'Full Control')
        if db_count != ui_count:
            error_list.append(
                "FULL_ACCESS_USER_COUNT_DOESNT_MATCH: {DB: %s,UI: %s}" % (db_count, ui_count))
        db_count = len(db_permission_dict['Modify Access'])
        ui_count = self.fso_data_source_discover.get_file_security_dashboard_user_count(
            'Modify Access')
        if db_count != ui_count:
            error_list.append(
                "MODIFY_ACCESS_USER_COUNT_DOESNT_MATCH: {DB: %s,UI: %s}" % (db_count, ui_count))
        db_count = len(db_permission_dict['Write Access'])
        ui_count = self.fso_data_source_discover.get_file_security_dashboard_user_count(
            'Write Access')
        if db_count != ui_count:
            error_list.append(
                "WRITE_ACCESS_USER_COUNT_DOESNT_MATCH: {DB: %s,UI: %s}" % (db_count, ui_count))
        db_count = len(db_permission_dict['List Access'])
        ui_count = self.fso_data_source_discover.get_file_security_dashboard_user_count(
            'List Access')
        if db_count != ui_count:
            error_list.append(
                "LIST_ACCESS_USER_COUNT_MISMATCH: {DB: %s,UI: %s}" % (db_count, ui_count))
        if len(error_list) > 0:
            raise Exception(
                f"Following error occurred in File Security Dashboard: {str(error_list)}"
            )

    def fetch_fso_files_db(self, count):
        """
        Get given number of files from FSO database
        Args:
            count  (int): Count of no of files to fetch
        Returns:
            (list): List of filepaths
        """
        query = f"""
        Select PATH from fso_metadata LIMIT {count} 
        """
        data = self.sqlitedb.execute(query).fetchall()
        return [item['PATH'] for item in data]

    def get_duplicate_file_count_db(self, file_name):
        """
        Get file count for a given file
        Args:
            file_name (str): Name of file
        Returns (int): Count of occurrences for a file
        """
        data = self.duplicate_dashboard_data_db()
        count = 1
        for item in data:
            if item['NAME'].__eq__(file_name):
                count = item['File_Count']
                break
        return count

    def fso_cleanup(self, client_name, datasource_name, dir_path=None,
                    pseudo_client_name=None, cloud_apps=False, credential_name=None, review_request=None):
        """
        Delete FSO data source
        Args:
            client_name (Str): Name of FSO client
            datasource_name (str): Name of FSO data source
            dir_path (str): UNC path of dir to delete its contents
            pseudo_client_name (str): Name of pseudo client to delete from Commcell
            cloud_apps (bool)   : True for cloud apps
            credential_name (str)   :  Name of the credential to be deleted
            review_request  (list)  --  Names of review requests to be deleted
        """
        request_manager = RequestManager(self.__admin_console)
        if review_request is not None:
            for request_name in review_request:
                self.__admin_console.navigator.navigate_to_governance_apps()
                self.fso_obj.select_request_manager()
                if request_manager.search_for_request(request_name):
                    request_manager.delete.delete_request(request_name)
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.__inventory_manager_details.select_file_storage_optimization()
        if cloud_apps:
            self.fso_obj.select_fso_grid_tab(self.__admin_console.props['label.objectStorage'])
        if self.fso_obj.check_if_client_exists(client_name):
            self.fso_obj.select_details_action(client_name)
            if self.fso_client_details.check_if_datasource_exists(datasource_name):
                self.fso_client_details.delete_fso_datasource(datasource_name)
        if dir_path is not None:
            self.activate_utils.delete_old_data(dir_path)
        if pseudo_client_name is not None:
            all_clients_names = self.commcell.clients.all_clients.keys()
            for c_name in all_clients_names:
                if re.search(pseudo_client_name, c_name, re.IGNORECASE):
                    self.log.info('Deleting client: %s' % c_name)
                    try:
                        self.commcell.clients.delete(c_name)
                    except Exception as excp:
                        self.log.info('Unable to delete client: "%s" with '
                                      'reason: "%s". Continuing anyway.' % (c_name, excp))
        if credential_name is not None:
            self.__admin_console.navigator.navigate_to_credential_manager()
            if self.__rtable.is_entity_present_in_column(
                    self.__admin_console.props['label.credentialName'], credential_name):
                self.credential_manager.action_remove_credential(credential_name)

    def analyze_client_details(self, client_name, data_source_name,
                               docs_count, plan_name, is_backed_up=False, server_group_client=False):
        """
        Analyze details page for a FSO client
        Args:
             client_name (str): Name of FSO client
             data_source_name (str): FSO client data source name
             docs_count (int): Count of docs present for FSO data source
             plan_name (str): Associated plan name for FSO client
             is_backed_up (bool): Is associated DS backed up or live
             server_group_client (bool) : Is a server group client
        """
        error_list = []
        if server_group_client:
            if self.fso_server_group_details.check_if_client_exists(client_name):
                self.fso_server_group_details.select_server_details_action(client_name)
        else:
            if self.fso_obj.check_if_client_exists(client_name):
                self.fso_obj.select_details_action(client_name)
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        table_data = self.__table.get_table_data()
        docs_dict = dict(zip(table_data["Data source"], table_data["Documents"]))
        crawl_type_dict = dict(
            zip(table_data["Data source"], table_data["Type"]))
        ui_count, db_count = self.fso_file_count_formatting(
            docs_dict[data_source_name], docs_count)

        plan_dict = dict(zip(table_data["Data source"], table_data["Plan"]))
        if docs_dict.__contains__(data_source_name):
            if ui_count != db_count:
                error_list.append("Docs count in details page does not match:{DB: %s, UI:%s}"
                                  % (db_count, ui_count))
            if not plan_name.__eq__(plan_dict[data_source_name]):
                error_list.append(
                    'Plan name does not match on details page or missing')
            if is_backed_up:
                if not str(crawl_type_dict[data_source_name]). \
                        __eq__("Backup"):
                    error_list.append(
                        "Data Source Type for FSO client is not backup as expected")
            else:
                if not (str(crawl_type_dict[data_source_name])). \
                        __eq__("Source"):
                    error_list.append(
                        "Data source type for FSO client is not Source as Expected")
        else:
            raise Exception(
                "%s not found in details page for %s " % (data_source_name, client_name))
        if len(error_list) > 0:
            raise Exception(str(error_list))
        self.log.info(
            "Verified details page without exceptions for FSO client %s" % client_name)

    def analyze_client_expanded_view(self, client_name):
        """
        Analyze expanded view for FSO client
        Args:
            client_name (str) : Name of FSO client
        """
        if self.fso_obj.check_if_client_exists(client_name):
            self.fso_obj.toggle_client(client_name, expand=True)
        else:
            raise Exception(f"fso client {client_name} not found")
        if self.data_source_name not in self.fso_obj.get_fso_datasource_list():
            raise Exception("Data Source not found in FSO client quick view")

    def verify_fso_time_data(self, cloud_app_type=None, crawl_type= 'Live'):
        """
        Verify Access Time, Create Time, Modified Time for FSO data source
            Args:
                cloud_app_type  (str)   :   Type of the cloud app ( AZURE / AWS / GCP ) for selectively
                                            validating dashboards
                crawl_type (str)        :   FSO crawl Type
            Returns (True/False)        : Depending on whether time info is correct
        """
        tabs_to_check = []
        if cloud_app_type:
            if cloud_app_type in FSO_DASHBOARD_TABS_TO_VERIFY.keys():
                tabs_to_check = FSO_DASHBOARD_TABS_TO_VERIFY[cloud_app_type]
            else:
                CVWebAutomationException(f"{cloud_app_type} is not present in {str(FSO_DASHBOARD_TABS_TO_VERIFY)}")
        else:
            tabs_to_check = FSO_DASHBOARD_TABS_TO_VERIFY['ALL']
        time_ui_dict = self.fso_data_source_review.get_fso_time_info(cloud_app_type)
        temp_list = self.get_fso_time_metadata()
        db_dict = dict()
        for tab_name in tabs_to_check:
            db_dict[tab_name] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        now_time = datetime.now()
        current_year = now_time.year
        leap_timestamp = datetime.strptime(f'28/02/{current_year} 00:00:00', '%d/%m/%Y %H:%M:%S')
        current_year_offset = timedelta()
        if now_time > leap_timestamp and calendar.isleap(current_year):
            if now_time.day == 29 and now_time.month == 2:
                current_year_offset = now_time - leap_timestamp
            else:
                current_year_offset = timedelta(days=1)

        # Get timedelta difference due to leap years between passed year and current year

        def timedelta_offset(year):
            return current_year_offset if year == current_year else \
                (timedelta(days=1) if calendar.isleap(year)
                 else timedelta()) + timedelta_offset(year + 1)

        # Get timedelta object for i number of years in the past from current year
        def tdl_value(i):
            return now_time - timedelta(365 * i) - \
                   timedelta_offset(current_year - i)

        tdl_dict = {
            1: tdl_value(1),
            2: tdl_value(2),
            3: tdl_value(3),
            4: tdl_value(4),
            5: tdl_value(5),
        }

        # Map passed time object to correct year span i.e between
        # {0-1 years:1, 1-2 years:2, 2-3 years:3, 3-4 years:4, 4-5 years:5, 5+ years:6]

        def year_mapper(tdl):
            return 1 if tdl_dict[1] < tdl <= now_time else \
                2 if tdl_dict[2] < tdl <= tdl_dict[1] else \
                    3 if tdl_dict[3] < tdl <= tdl_dict[2] else \
                        4 if tdl_dict[4] < tdl <= tdl_dict[3] else \
                            5 if tdl_dict[5] < tdl <= tdl_dict[4] else 6

        format_time = '%B %d, %Y %I:%M:%S %p'
        for item in temp_list:
            for tab_name in tabs_to_check:
                time_key = year_mapper(datetime.strptime(
                    item[tab_name], format_time))
                db_dict[tab_name][time_key] = db_dict[tab_name][time_key] + 1

        def data_size_mapper(fl, y):
            return self.data_size_mapper_filter[
                time_ui_dict[fl][y].split()[1]]

        def data_count_mapper(fl, y):
            return self.data_count_filter[time_ui_dict[fl][y].split()[1]] if len(time_ui_dict[fl][y].split()) > 1 \
                else self.data_count_filter[' ']

        for key, value in time_ui_dict.items():
            for key1, value1 in value.items():
                if value1.__ne__('0'):
                    temp = 1
                    temp = data_count_mapper(key, key1)
                    time_ui_dict[key][key1] = round(float(value1.split()[0]) * pow(1000, temp), 2)
                else:
                    time_ui_dict[key][key1] = float('0')
        self.log.info('DB Time Dict %s' % str(db_dict))
        self.log.info('UI Time Dict %s' % str(time_ui_dict))

        if crawl_type =='Backup':
            del db_dict['Access Time']
            del time_ui_dict['Access Time']

        if db_dict != time_ui_dict:
            raise Exception('Access/Modified/Created Time does not match for DB and UI')

        return db_dict == time_ui_dict


    def verify_permission(self, actual, expected):
        """
        Verify entitlement manager per file
        :param actual permissions
        :param expected permissions
        :return True/False
        """
        if expected is not None or actual is not None:
            for key in actual.keys():
                user = key
                if user != "NT AUTHORITY\\Authenticated Users":
                    if expected[user] is not None:
                        if actual[user].lower() != expected[user].lower():
                            self.log.error("User permission mismatched for [{}]".format(user))

                            self.log.error(
                                "User permission mismatched for [{}]".format(user))

                            self.log.error(
                                "Actual [{}] Excepted [{}]".format(actual[key], expected[key]))
                            return False
        return True

    def get_permissions(self, elements, file_name):
        """
        Get permission for a file
        :param elements: permission list for all files/folders
        :param file_name: file name
        :return all permissions for a file
        """
        permissions = {}
        for current in elements:
            if file_name.lower() in current["file_name"].lower():
                permissions = current
                break
        return permissions

    def detect_file_permission_change(self, old_permissions_list, new_permissions_list, file_name):
        """
        Detect file permission change
        :param old_permissions_list: old permissions list
        :param new_permissions_list: new permissions list
        :param file_name: file name
        :return True/False
        """
        old_permissions = self.get_permissions(old_permissions_list, file_name)
        new_permissions = self.get_permissions(new_permissions_list, file_name)
        if old_permissions == new_permissions:
            return False

        for key in new_permissions:
            if key not in old_permissions:
                self.log.info("New user [{}]".format(key))
                return True

        self.log.info("No change permission detected.")
        return False

    def track_job(self, job_operation=None, job_id=None, expected_status="Completed"):
        """
         Tracks a job based on the job operation or job id
         Args:
         job_operation     (str)    --  Job operation type
         job_id            (int)    --  Job id of the job to track
         Returns:
         bool  - Returns true or false based on the job status

        """
        jobs = Jobs(self.__admin_console)
        self.__admin_console.navigator.navigate_to_jobs()
        jobs.access_active_jobs()
        if job_id is None and job_operation:
            self.__rtable_job.apply_filter_over_column_selection(
                self.__admin_console.props['label.taskDetail.operation'],
                job_operation,
                criteria=Rfilter.equals
            )
            job_id = self.__rtable_job.get_column_data("Job Id")[0]
        job_details = jobs.job_completion(job_id=job_id)
        if job_details[self.__admin_console.props['label.status']] == expected_status:
            return True
        return False

    def do_file_operation(self, target_data_path, operation, username=None, password=None):
        """
        Do mentioned operation on a randomly chosen file from target data path
        Args:
            target_data_path    (str):  target data path from where the file should be chosen
            operation   (str):          operation which we have to perform
            username(str): Domain user accessing the target UNC
            password(str): Password to access the target UNC
        """
        return self.activate_utils.do_operation_on_file(target_data_path=target_data_path, operation=operation,
                                                        username=username, password=password)

    def verify_file_monitoring(self, file_server_directory_path, username, password):
        """
        Verify File Monitoring
        Args:
                file_server_directory_path  (str):  target data path from where the file should be choosen
                username                    (str):  Domain user accessing the target path
                password                    (str):  Password to access the target path
        """
        self.fso_monitoring_report_details.open_monitoring_report_page()
        viewer_obj = viewer.CustomReportViewer(self.__admin_console)
        self.log.info("Creating an object for File Monitoring Report Table")
        table_obj = viewer.DataTable("File Information")
        viewer_obj.associate_component(table_obj)
        self.log.info("Sorting the table based on Event Time Column in Descending Order")
        self.fso_monitoring_report_details.sort_monitoring_table("Event Time", wait_for_load=False)
        self.fso_monitoring_report_details.sort_monitoring_table("Event Time", wait_for_load=False)
        operations = FILE_MONITORING_OPERATIONS
        for operation in operations:
            self.log.info("Performing Operation on the target data path")
            data_from_operation = self.do_file_operation(target_data_path=file_server_directory_path,
                                                         operation=operation,
                                                         username=username,
                                                         password=password)
            self.__admin_console.refresh_page()
            self.fso_monitoring_report_details.access_monitoring_report_searchbar(data_from_operation[2][0])
            self.log.info("Sleeping for 15 seconds")
            time.sleep(15)
            self.log.info("Getting Data Reported from File Monitoring Table")
            monitoring_report_data = table_obj.get_rows_from_table_data()
            monitoring_counter = 0
            verified_operations = []
            self.log.info("Verifying if the Monitoring Data matches with the manually performed operation data")
            for row in monitoring_report_data:
                if datetime.strptime(row[3], '%b %d, %Y %I:%M:%S %p').timestamp() < data_from_operation[3] - 5:
                    self.log.info(f"Skipping an old entry for same file: {row}")
                    continue
                if row[1] in data_from_operation[1]:
                    monitoring_counter += 1
                    if row[0].lower() == data_from_operation[0].lower():
                        monitoring_counter += 1
                    if row[2] in data_from_operation[2]:
                        monitoring_counter += 1
                    if abs(data_from_operation[3] - datetime.strptime(row[3], '%b %d, %Y %I:%M:%S %p').timestamp()) < 5:
                        monitoring_counter += 1
                    if row[6] == data_from_operation[5]:
                        monitoring_counter += 1
                    if monitoring_counter != 5:
                        self.log.info(
                            f"Operation {operation} monitoring data does not match the manual operation performed data")
                        raise Exception(f"Operation {operation} monitoring data does not "
                                        f"match the manual operation performed data")
                    else:
                        verified_operations.append(row[1])
                monitoring_counter = 0
            if sorted(verified_operations) == sorted(data_from_operation[1]):
                self.log.info(f"Operation {operation} Verified from File Monitoring Report Table Data")
            else:
                self.log.info(
                    f"Operation {operation} monitoring data does not match the manual operation performed data")
                raise Exception(f"Operation {operation} monitoring data does not "
                                f"match the manual operation performed data")

    def navigate_to_datasource_details(self, client_name, datasource_name):
        """
        Navigates to datasource details page
        Args:
            client_name         (str):      name of the client on which datasource is added
            datasource_name     (str):      name of the datasource
        """
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.__inventory_manager_details.select_file_storage_optimization()
        self.fso_obj.select_details_action(client_name)
        self.fso_client_details.select_details_action(datasource_name)

    def get_csv_file_from_machine(self, zip_directory_path):
        """
        Returns the file path to csv file after extracting the zip file
        Args:
            zip_directory_path  (str):      path to the directory where csv zip_file exist
        Returns:
            the file path to csv file after extracting the zip file
        """
        machine_object = Machine()
        zip_path = machine_object.get_files_in_path(zip_directory_path)[0]
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            self.log.info("Extracting all files inside zip")
            zip_ref.extractall(zip_directory_path)
        all_files = machine_object.get_files_in_path(zip_directory_path)
        csv_path = [csv_file for csv_file in all_files if csv_file.endswith("csv")]
        return csv_path


class FSOServerGroupHelper(FSO):
    """FSO Server Helper Class"""

    def __init__(self, admin_console, commcell, csdb):
        """
        FSO Server helper class provides functions to perform DB operations
        on FSO server group test DB and perform verify operations on FSO
        Args:
            admin_console : Admin Console Object
            commcell (Object) : Commcell Object
            csdb (Object) : CSDB Object
        """
        super().__init__(admin_console, commcell, csdb)
        self.fso_server_group_config = _SERVER_GROUP_CONSTANTS
        self.clientgroup = self.commcell.client_groups
        self.__table = Table(admin_console)
        self.config_mapping = {
            "CLIENT_LIST": self.fso_server_group_config.ClientList,
            "SUBCLIENT_CONTENT_LIST": self.fso_server_group_config.SubclientContentList,
            "SQLITE_DB_LIST": self.fso_server_group_config.SqliteDBPaths
        }

    def add_client_group(self, client_group_name, client_list=[]):
        """
        Add Client group to Commcell
        Args:
            client_group_name (str) -- Name of Client group to add
            client_list (list)   -- List of clients to be associated
        """
        self.clientgroup.add(client_group_name, client_list)

    def remove_client_group(self, client_group_name):
        """
        Removes Existing client group from commcell
        Args:
             client_group_name (str) -- Name of client group to be removed
        """
        if self.clientgroup.has_clientgroup(client_group_name):
            self.clientgroup.delete(client_group_name)
        else:
            self.log.info(f"Unable to delete {client_group_name}. Client group not found")

    def analyze_server_group_details(self, server_group_name):
        """
        Verify If server group listing in details page is correct
        Args:
            server_group_name (str) : Name of server group to verify
        Returns:
             (bool) : True / False
        """
        if self.fso_obj.check_if_client_exists(server_group_name):
            self.fso_obj.select_details_action(server_group_name)
            table_data = self.__table.get_table_data()
            ui_client_list = sorted(table_data["Name"])
            db_client_list = sorted(self.fso_server_group_config.ClientList)
            if ui_client_list == db_client_list:
                self.log.info("FSO Server group client list matched.")
            else:
                raise Exception(f"Client List Mismatch DB:{db_client_list}  UI:{ui_client_list}")
        else:
            raise Exception(f"{server_group_name} not found.")
        self.log.info("Verified Server Group details page Successfully")
