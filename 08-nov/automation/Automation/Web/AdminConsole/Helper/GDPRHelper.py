# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run GDPR
AdminConsole Automation test cases.

Class:

    GDPR()

Functions:

    create_sqlite_db_connection()    --   Establishes connection to the
                                        SQLite Database at the given file path
    testdata_path(self)    --    Returns the testdata path
    testdata_path()    --    Sets the testdata path for file server data source
    entities_list()    --    Returns the entities list
    entities_list()    --    Sets the entities list
    entities_replace_dict()    --    Returns the entities dict which are replaced in
                                        key value pair/s
    entities_replace_dict()    --    Sets the entities dict which are replaced in key value pair/s
    disable_entities_list()    --    Returns the entities list to be disabled
    disable_entities_list()    --    Sets the disentities_list with the entities list to be disabled
    data_source_name()    --    Returns the testdata path
    data_source_name()    --    Sets the testdata path for file server data source
    db_get_total_files_count()    --    Returns the total no.of files
                                            specific to the test data directory path
    db_get_all_entities()    --    Returns all the entities present in the db
    modified_entities_list()    --    Returns list of modified entities; unique items of
                                    (entities_list - old entity + new entity - disabled entities)
    db_get_sensitive_files_count()    --    Returns the total no.of sensitive files
                                                specific to the test data dir path
    db_get_custom_entity_parameters()    --    Returns a dictionary with custom entity parameters
                                                    associated to a given entity name
    db_get_custom_entity_list()    --    Returns list of custom entities in sqlite DB
    db_get_sensitive_file_paths()    --    Returns all sensitive file paths
                                                specific to the test data dir path
    db_get_entities()    --    Returns a dictionary with entity names/values
                                    associated to a given file path
    verify_data_source_name()    --    Verify data source name of the current page
    verify_data_source_discover()    --    Verify contents on data source discover page
    verify_sensitivity()    --    Verify sensitivity for a given file path
    verify_data_source_review()    --    Verify contents on data source review page
    cleanup()    --    Cleanup test case created things
    get_schedule_datetime()     -- Returns the schedule options based on current time
    verify_last_collection_time()    -- Verifies the last collection time for inventory asset scan
    validate_request_operations() -- validates whether DELETE/EXPORT request made from Request Manages
    compare_entities()  -- Compares DB Entites with Review Page Entities
    monitor_classifier_training()   --    Monitors the classifier training progress
    valid_row_list()                -- Get valid SQLIte DB rows for Advance Search
    inventory_exists()              -- Verify if a inventory with given name is present
    plan_exists()                   -- Verify if a plan with given name is present
    project_exists()                -- Verify if a project with given name is present
    validate_review_request()       -- Validates the review request (both review and approve)
    apply_time_filters()            --  applies time filters on data
    apply_filter_on_db()            --  Applies filter on db
    get_random_filters()            --  Creates randomized filters dict with filter names and values
    generate_filters()              --  Generates filters to be applied on request review page
    verify_review_operation_from_db()   -- Verify if the review operation worked properly
    fetch_latest_gdpr_wrkflow_job_id()  --  Returns latest workflow GDPR task approval job id
    get_latest_job_by_operation()       --  Returns the latest or last run data curation job details
    find_job_by_operation()             --  Finds the latest job by operation from a dictionary
    risk_analysis_cleanup()             --  Deletes the Risk Analysis project and plan
"""

import os
import random
import re
import time
from datetime import datetime, timedelta

from requests import request

from Web.AdminConsole.AdminConsolePages.Jobs import Jobs

import dynamicindex.utils.constants as cs
from AutomationUtils import logger
from AutomationUtils.database_helper import SQLite
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.table import Rtable, Table
from Web.AdminConsole.GovernanceAppsPages.DataSourceDiscover import DataSourceDiscover
from Web.AdminConsole.GovernanceAppsPages.DataSourceReview import DataSourceReview
from Web.AdminConsole.GovernanceAppsPages.FileServerLookup import FileServerLookup
from Web.AdminConsole.GovernanceAppsPages.InventoryManagerDetails import InventoryManagerDetails
from Web.AdminConsole.GovernanceAppsPages.RequestManager import RequestManager
from Web.AdminConsole.GovernanceAppsPages.ReviewRequest import ReviewRequest
from Web.AdminConsole.GovernanceAppsPages.entity_manager import ClassifierManager, EntityManager
from Web.Common.page_object import PageService
from dynamicindex.utils.activateutils import ActivateUtils
from cvpysdk.job import Job


class GDPR:
    """ GDPR helper """

    def __init__(self, admin_console=None, commcell=None, csdb=None):
        """ A class that represents GDPR functions that can be performed
            for AdminConsole Automation
        :param admin_console: the admin console class object
        :param commcell: the commcell object
        :param csdb: the commcell database object
        """
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver

        self.log = logger.get_log()
        self.csdb = csdb
        self._login_obj = None

        self.commcell = commcell
        self._subclient = None
        self.user_name = None
        self.password = None
        self.sqlitedb = None
        self._testdata_path = None
        self._entities_list = None
        self._entities_list_map = None
        self._entities_dict = None
        self._entities_replace_dict = None
        self._data_source_name = None
        self._disable_entities_list = None
        self._advance_entity_names = list()
        self._advance_column_names = list()
        self._queries_per_entity = 1

        self.activate_utils = ActivateUtils(self.commcell)
        self.inventory_details_obj = InventoryManagerDetails(
            self.__admin_console)
        self.plans_obj = Plans(self.__admin_console)
        self.file_server_lookup_obj = FileServerLookup(self.__admin_console)
        self.data_source_discover_obj = DataSourceDiscover(
            self.__admin_console)
        self.data_source_review_obj = DataSourceReview(self.__admin_console)
        self.entity_manager_obj = EntityManager(self.__admin_console)
        self.classifier_obj = ClassifierManager(self.__admin_console)
        self.request_manager = RequestManager(self.__admin_console)
        self.credential_manager = CredentialManager(self.__admin_console)
        self.review = ReviewRequest(self.__admin_console)
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)

    def create_sqlite_db_connection(self, sqlite_database_file_path):
        """Establishes connection to the SQLite Database at the given file path.

            Args:
                sqlite_database_file_path     (str)   --  path of the sqlite db file

        """
        self.sqlitedb = SQLite(sqlite_database_file_path)

    @property
    def advance_entity_names(self):
        """
        Returns Entity list used for Advance search validation
        in SDG
        Example:
            ['Email','IP address']
        :return: advance_entity_names (list) UI Entity names for Advance search
        """
        return self._advance_entity_names

    @advance_entity_names.setter
    def advance_entity_names(self, value):
        """
        Sets Entity names list  for Advance search validation
        in SDG
        Example:
            ['Email','IP address']
        :param value: (list) UI Entity names for Advance search
        """
        self._advance_entity_names = value

    @property
    def queries_per_entity(self):
        """
        Returns the number of queries per entity
        Returns
            (int):- Count of queries per entity
        """
        return self._queries_per_entity

    @queries_per_entity.setter
    def queries_per_entity(self, value):
        """
        Sets queries count per entity
        :param value: (int) Count of queries per entity
        """
        self._queries_per_entity = value

    @property
    def advance_column_names(self):
        """
        Returns Columns list used for Advance search validation
        in SDG
        Example:
            ['File name','File Path']
        :return: advance_column_names (list) UI Column names for Advance search
        """
        return self._advance_column_names

    @advance_column_names.setter
    def advance_column_names(self, value):
        """
        Sets Column names list  for Advance search validation
        in SDG
        Example:
            ['File name','File Path']
        :param value: (list) UI Column names for Advance search
        """
        self._advance_column_names = value

    @property
    def testdata_path(self):
        """
        Returns the testdata path
        :return: testdata_path  (str)  --   test data path location of file server
                                            data source
        """
        return self._testdata_path

    @testdata_path.setter
    def testdata_path(self, value):
        """
        Sets the testdata path for file server data source
        :param value    (str)   --  test data location for file server data source
        """
        self._testdata_path = value

    @property
    def entities_list(self):
        """
        Returns the entities list
        :return: entities_list  (list)  --   entities list
        """
        return self._entities_list

    @entities_list.setter
    def entities_list(self, value):
        """
        Sets the entities list
        :param value    (list)   --  entities list
        """
        self._entities_list = value

    @property
    def entities_list_map(self):
        """
        Returns the entities list map
        :return: entities_list_map  (list)  --   entities list map
        """
        return self._entities_list_map

    @entities_list_map.setter
    def entities_list_map(self, value):
        """
        Sets the entities list map
        :param value    (list)   --  entities list map
        """
        self._entities_list_map = value

    @property
    def entities_replace_dict(self):
        """
        Returns the entities dict which are replaced in key value pair/s
        :return: entities_dict  (dict)  --   entities replace dict
        """
        return self._entities_replace_dict

    @entities_replace_dict.setter
    def entities_replace_dict(self, value):
        """
        Sets the entities dict which are replaced in key value pair/s
        :param value    (dict)   --  entities replace dict
        """
        self._entities_replace_dict = value

    @property
    def disable_entities_list(self):
        """
        Returns the entities list to be disabled
        :return: entities_list  (list)  --   entities disable list
        """
        return self._disable_entities_list

    @disable_entities_list.setter
    def disable_entities_list(self, value):
        """
        Sets the disentities_list with the entities list to be disabled
        :return: entities_list  (list)  --   entities disable list
        """
        self._disable_entities_list = value

    @property
    def data_source_name(self):
        """
        Returns the testdata path
        :return: data_source_name  (str)  --   name of the data source
        """
        return self._data_source_name

    @data_source_name.setter
    def data_source_name(self, value):
        """
        Sets the testdata path for file server data source
        :param value    (str)   --  name of the data source
        """
        self._data_source_name = value

    def db_get_total_files_count(self):
        """
        Returns the total no.of files specific to the test data directory path
        """
        query = 'select count(*) from files where filepath like "%{0}%"'.format(
            self.testdata_path)
        self.log.info("Query being executed is: {0}".format(query))
        result = self.sqlitedb.execute(query)
        total_files = result.rows[0][0]
        self.log.info("Total Files found are: %s" % total_files)
        return total_files

    def db_get_all_entities(self, valid_entities=True):
        """
        Returns all the entities present in the db

            Args:
                valid_entities (Bool) -- If True, entities which are null or blank
                                        are removed

        """
        query = 'select * from files where filepath like "%{0}%"'.format(
            self.testdata_path)
        self.log.info("Query being executed is: {0}".format(query))
        result = self.sqlitedb.execute(query)
        db_entities_list = result.columns
        remove_columns = []
        if valid_entities:
            values = result.rows[0]
            for index, value in enumerate(values):
                if value is None or value == '':
                    remove_columns.append(db_entities_list[index])
        remove_columns = remove_columns + db_entities_list[:2]
        for column in remove_columns:
            db_entities_list.remove(column)
        return db_entities_list

    def modified_entities_list(self):
        """
        Returns list of modified entities; unique items of
        (entities_list - old entity + new entity - disabled entities)
        """
        entities_list_modified = list(
            self.entities_list)  # this is to keep self.entities_list intact
        if self.entities_replace_dict is not None:
            for old_entity in self.entities_replace_dict.keys():
                entities_list_modified.remove(old_entity)
                entities_list_modified.append(
                    self.entities_replace_dict[old_entity])  # adding new_entity to the list
        # converting to set and back to list to remove duplicates from the list
        entities_list_modified = list(set(entities_list_modified))
        self.log.info(
            "entities_list_modified is: '{0}'".format(entities_list_modified))
        if self.disable_entities_list is not None:
            self.log.info(
                "self.disable_entities_list is: '{0}'".format(
                    self.disable_entities_list))
            for entity in self.disable_entities_list:
                entities_list_modified.remove(entity)
        return entities_list_modified

    def db_get_sensitive_files_count(self):
        """
        Returns the total no.of sensitive files specific to the test data dir path
        """
        entities_list_modified = self.modified_entities_list()
        """getting modified entities list if applicable; i.e., unique items of
        (entities_list - old entity + new entity - disabled entities)"""

        query = '''
            SELECT count(*) FROM files where filepath like "%{0}%" and (
            not "{1}" is null
        '''.format(self.testdata_path, entities_list_modified[0])
        for entity in entities_list_modified[1:]:
            query = query + ' or not "{0}" is null'.format(entity)
        query = query + ')'
        self.log.info("Query being executed is: '{0}'".format(query))
        result = self.sqlitedb.execute(query)
        sensitive_files = result.rows[0][0]
        self.log.info("Sensitive Files found are: %s" % sensitive_files)
        return sensitive_files

    def db_get_custom_entity_parameters(self, entity_name):
        """
        Returns a dictionary with custom entity parameters associated to a given entity name
             Args:
                entity_name (str) -- Custom entity name
        """
        entity_parameters_dict = {}
        self.log.info(
            "Selecting entity parameters for custom entity: %s" %
            entity_name)
        query = '''SELECT EntityName,Sensitivity,Regex,ParentEntity,
                keywords FROM CustomEntities where EntityName = "{0}"'''.format(entity_name)
        result = self.sqlitedb.execute(query)
        entity_parameters_dict["entity_name"] = result.rows[0][0]
        entity_parameters_dict["sensitivity"] = result.rows[0][1]
        entity_parameters_dict["python_regex"] = result.rows[0][2]
        entity_parameters_dict["parent_entity"] = result.rows[0][3]
        keywords = result.rows[0][4]
        if keywords:
            keywords = keywords.split(',')
            self.log.info("Keywords are: '{0}'".format(keywords))
            entity_parameters_dict["keywords"] = keywords

        self.log.info(
            "Parameters Dictionary obtained is: '{0}'".format(entity_parameters_dict))
        return entity_parameters_dict

    def db_get_custom_entity_list(self):
        """
        Returns list of custom entities in sqlite DB

        """
        entity_list = []
        query = 'SELECT EntityName FROM CustomEntities'
        result = self.sqlitedb.execute(query)
        for entity_name in result.rows:
            entity_list.append(entity_name[0])

        self.log.info(
            "Entities list obtained is: '{0}'".format(entity_list))
        return entity_list

    def db_get_sensitive_file_paths(self):
        """
        Returns all sensitive file paths specific to the test data dir path
        """
        entities_list_modified = self.modified_entities_list()
        # getting modified entities list if applicable; i.e., unique items of
        # (entities_list - old entity + new entity - disabled entities)

        query = '''
            SELECT filepath FROM files where filepath like "%{0}%" and (
            not "{1}" is null
        '''.format(self.testdata_path, entities_list_modified[0])
        for entity in entities_list_modified[1:]:
            query = query + ' or not "{0}" is null'.format(entity)
        query = query + ')'
        self.log.info("Query being executed is: '{0}'".format(query))
        result = self.sqlitedb.execute(query)
        sensitive_file_paths_list = result.rows
        sensitive_file_paths_list = [file_path[0]
                                     for file_path in sensitive_file_paths_list]
        sensitive_file_paths_list = (
            sorted(sensitive_file_paths_list, key=str.lower))
        self.log.info("Sensitive file paths found are: %s" %
                      sensitive_file_paths_list)
        return sensitive_file_paths_list

    def db_get_entities(self, file_path, unique=True):
        """
        Returns a dictionary with entity names/values associated to a given file path

            Args:
                file_path (str) -- Full file path
                unique (Bool) -- Returns only the unique entity values if True

        """

        entities_list_modified = self.modified_entities_list()

        entities_dict = {}
        query = 'SELECT'

        for entity in entities_list_modified:
            query = query + ' "{0}"'.format(entity)
            if entities_list_modified.index(
                    entity) + 1 < len(entities_list_modified):
                query = query + ','

        query = query + ' FROM Files where FilePath = "{0}"'.format(file_path)
        self.log.info("Query being executed is: '{0}'".format(query))
        result = self.sqlitedb.execute(query)
        columns_list = result.rows[0]
        for index, column in enumerate(columns_list):
            entity_values_list = column
            if entity_values_list is not None:
                entity_values_list = entity_values_list.split(',:;')
                if unique:
                    entity_values_list = list(set(entity_values_list))
                entity_values_list = sorted(entity_values_list, key=str.lower)
                entities_dict[entities_list_modified[index].lower()] = entity_values_list

        self.log.info(
            "Entities Dictionary obtained is: '{0}'".format(entities_dict))
        return entities_dict

    def verify_data_source_name(self):
        """
        Verify data source name of the current page

        Exception:
                    if there is a mismatch
        """
        self.log.info(
            "Verifying the data source name on the admin console page")
        data_source_name_on_page = self.data_source_discover_obj.get_data_source_name()
        if re.search(self.data_source_name, data_source_name_on_page):
            self.log.info("Data Source name matched")
        else:
            raise Exception("Data Source name mismatch")

    def verify_data_source_discover(self, skip_total_files=False):
        """
        Verify contents on data source discover page

            Args:
                skip_total_files (Bool) -- If True, skips total files validation

        Exception:
                    if any of the validation fails
        """
        self.verify_data_source_name()
        if not skip_total_files:
            self.log.info("Verifying the total files count")
            if self.data_source_discover_obj.get_total_files() != self.db_get_total_files_count():
                raise Exception("Total Files Mismatch")
            self.log.info("Total files matched")

        self.log.info("Verifying the sensitive files count")
        if self.data_source_discover_obj.get_sensitive_files(
        ) != self.db_get_sensitive_files_count():
            raise Exception("Total Files Mismatch")
        self.log.info("Total files matched")

    def verify_sensitivity(
            self,
            file_path,
            folder_path=False,
            unique=True,
            edit_system_entity=False):
        """
        Verify sensitivity for a given file path

            Args:
                file_path (str) -- Name of the file path to verify the sensitivity for
                folder_path (str) -- Folder path to be replaced with the folder path
                                    to match in the sql db file. Provide this in case
                                    of live crawl or backed up client case
                unique (Bool) --     Fetch unique entities from DB.
        Exception:
                    if any of the validation fails
        """
        file_name_expected = os.path.split(file_path)[-1]
        self.log.info("File Name expected is: %s" % file_name_expected)
        file_name_obtained = self.data_source_review_obj.get_file_name()
        self.log.info("File Name obtained is: %s" % file_name_obtained)
        if file_name_expected != file_name_obtained:
            raise Exception("File Name Mismatch")
        self.log.info('File Names matched')

        if folder_path:
            file_path = file_path.replace(folder_path, self.testdata_path, 1)

        self.log.info(
            "Obtaining Dict of entities and values for a given file path from Sqlite DB")
        # Dict of entities and values in a given file path
        db_entities_dict = self.db_get_entities(file_path, unique)

        self.log.info(
            "db_entities_dict obtained is : '{0}'".format(db_entities_dict))

        if self.entities_replace_dict is not None:
            db_entities_dict_temp = {}
            self.log.info(
                "Entities Edit case: Appending old_entiy name and new_entity \
                    values to the list of entities and values obtained from SQlite DB")
            for new_entity in db_entities_dict.keys():
                for old_entity, value in self.entities_replace_dict.items():
                    if new_entity == value.lower(
                    ):
                        self.log.info(
                            "self.entities_replace_dict[old_entity] is : '{0}'".format(
                                self.entities_replace_dict[old_entity].lower()))
                        new_entity_values_list = db_entities_dict[new_entity]
                        db_entities_dict_temp[old_entity.lower(
                        )] = new_entity_values_list
            if edit_system_entity:
                db_entities_dict.clear()
            db_entities_dict.update(db_entities_dict_temp)
            self.log.info(
                "db_entities_dict modified to : '{0}'".format(db_entities_dict))

        entities_dict = self.data_source_review_obj.get_entities()

        if db_entities_dict != entities_dict:
            for db_key in db_entities_dict:
                if db_key in entities_dict:
                    if db_entities_dict[db_key] != entities_dict[db_key]:
                        self.log.error(f"Entity values are not matching for {db_key}")
                        self.log.error(f"DB values for {db_key} : {db_entities_dict[db_key]}")
                        self.log.error(f"UI values for {db_key} : {entities_dict[db_key]}")
                else:
                    self.log.error(f"DB key {db_key} is missing from UI")
            raise Exception("Entity Values mismatched")
        self.log.info('Entity Values matched')

    def compare_entities(self, row_data, data_source_type):
        """
        Compare Sensitive Entities between UI and Test DB
        for given row data and Data Source Type in review page.
        Args:
            row_data: Row Data To Compare
            data_source_type: Data source Type

        Returns:
            status(bool): True/False depending on comparison
        """
        status = True
        search_str = row_data
        if data_source_type == cs.ONE_DRIVE:
            search_str = row_data.replace(':', '_')
            search_str = search_str.replace('\\', '_')
        elif data_source_type == cs.SHAREPOINT:
            search_str = row_data.split('\\')[-1]
        self.data_source_review_obj.search_file(
            search_str, data_source_type=data_source_type)
        self.log.info(f"Verifying Sensitivity for Data {search_str}")
        db_entities_dict = self.activate_utils.db_get_sensitive_entities(
            data_source_type,
            row_data,
            self.entities_list,
            cs.DB_ENTITY_DELIMITER,
            self.sqlitedb.database_file_path
        )
        if data_source_type == cs.DATABASE or data_source_type == cs.GOOGLE_DRIVE:
            self.__table.select_rows([''])
        else:
            self.data_source_review_obj.select_file(search_str)
        self.log.info(f"Database Entities Dictionary for Data {search_str} is  {db_entities_dict}")
        temp_dict = self.data_source_review_obj.get_entities(data_source_type)
        entities_dict = dict()
        for key, value in temp_dict.items():
            for key1, value1 in self.entities_list_map.items():
                if str(key).lower() == str(key1).lower():
                    entities_dict[value1.lower()] = value
                    break
        if db_entities_dict != entities_dict:
            self.log.info(f"Entities Value Mismatched For Data {search_str}")
            status = False
        else:
            self.log.info(f'Entity Values matched for Data {search_str}')
        if data_source_type != cs.DATABASE and data_source_type != cs.GOOGLE_DRIVE:
            self.data_source_review_obj.close_file_preview()
        return status

    def validate_request_operations(self, data_source_type, sensitive_file, project_name, review_column,
                                    subclient_obj=None, backup_flag=False):
        """
        Validate post request approval operations
        Args:
            data_source_type (str): Data Source Type To Be Reviewed
            sensitive_file (str): Name of Sensitive file on which operation to be done
            project_name (str): name of project to which file belongs to
            review_column (str): Column in review pages to check if action was successfull
            subclient_obj (obj): subclient object to run backup job
            backup_flag (bool): flag set to true if backup to be run else false

        Returns: status(True/False) whether request validation passed or failed

        """
        status = True
        self.__admin_console.navigator.navigate_to_jobs()
        job = self.review.fetch_request_job()
        __current__url = self.__admin_console.driver.current_url
        __interaction_id = self.activate_utils.get_workflow_interaction(
            self.commcell, job[0])
        __approve_url = "https://{0}/{1}&id={2}&interactionId=0&actionName=Approve".format(
            self.commcell.webconsole_hostname, self.request_manager.constants.approval_url_suffix,
            __interaction_id)
        self.log.info("Approval URL [%s]", __approve_url)
        self.__admin_console.driver.get(__approve_url)
        time.sleep(180)
        self.__admin_console.driver.get(__current__url)
        time.sleep(180)
        self.commcell.job_controller.get(job[0]).wait_for_completion()
        if backup_flag:
            self.activate_utils.run_backup(subclient_obj)
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.inventory_details_obj.select_sensitive_data_analysis()
        self.file_server_lookup_obj.search_for_project(project_name)
        self.data_source_discover_obj.navigate_to_project_details(project_name)
        self.file_server_lookup_obj.select_data_source(self.data_source_name)
        self.log.info("Starting a re-crawl of the datasource [%s]",
                      self.data_source_name)
        self.data_source_discover_obj.select_details()
        self.data_source_discover_obj.start_data_collection_job()
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.inventory_details_obj.select_sensitive_data_analysis()
        self.file_server_lookup_obj.navigate_to_project_details(
            project_name)
        if not self.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.data_source_name):
            raise Exception("Could not complete Data Source Scan")
        self.log.info("Sleeping for: '[%s]' seconds", str(180))
        time.sleep(120)
        self.file_server_lookup_obj.select_data_source(
            self.data_source_name)
        self.data_source_discover_obj.select_review()
        self.data_source_review_obj.search_file(
            sensitive_file, data_source_type=data_source_type
        )
        temp_column_list = self.__table.get_column_data(review_column)
        if not len(temp_column_list) == 0:
            self.log.info("Selected file [%s] not deleted ", sensitive_file)
            status = False
        else:
            self.log.info(
                "File [%s] deleted successfully", sensitive_file)
        return status

    def verify_data_source_review(
            self,
            folder_path=False,
            unique=True,
            edit_system_entity=False):
        """
        Verify contents on data source review page

            Args:
                folder_path (str) -- Folder path to be replaced with the folder path
                                    present in the sql db file. Provide this in case
                                    of live crawl or backed up client case
                unique (Bool) --     Fetch unique entities from DB.

        Exception:
                    if any of the validation fails
        """
        self.verify_data_source_name()
        db_sensitive_file_paths_list = self.db_get_sensitive_file_paths()
        if folder_path:
            db_sensitive_file_paths_list = [
                file_path.replace(
                    self.testdata_path, folder_path, 1
                ) for file_path in db_sensitive_file_paths_list
            ]
        self.log.info(
            "Verifying Sensitive Data for each file according to the test data")
        for file_path in db_sensitive_file_paths_list:
            folder_name = os.path.split(file_path)[0]
            file_name = os.path.split(file_path)[1]
            self.data_source_review_obj.search_file(
                file_name, repr(folder_name))
            self.data_source_review_obj.select_file(file_name)
            self.log.info(
                "Validating Sensitivity for File Path: %s" %
                file_path)
            self.verify_sensitivity(
                file_path, folder_path, unique, edit_system_entity)
            self.data_source_review_obj.close_file_preview()

    def cleanup(self, project_name=None, inventory_name=None, plan_name=None, delete_backupset_for_client=False,
                backupset_names_list=None, pseudo_client_name=None, classifier_name=None, review_request=None,
                credential_name=None):
        """
        Cleanup test case created things

            Args:
                project_name (str) -- Name of the project to be deleted
                inventory_name (str) -- Name of the inventory to be deleted
                plan_name (str) -- Name of the plan to be deleted
                delete_backupset_for_client (str) -- Name of the client whose
                                                    backupsets to be deleted whose
                                                    names matches with project name
                backupset_names_list (list) -- List of Backupset names to be deleted
                If none provided, it would search for names related to project_name
                classifier_name (list)   --  Name of classifier to be deleted
                review_request  (list)  --  Names of review requests to be deleted
                pseudo_client_name (str): Name of pseudo client to delete from Commcell
                credential_name (str)   :  Name of the credential to be deleted

        """
        if classifier_name is not None:
            self.__admin_console.navigator.navigate_to_governance_apps()
            self.inventory_details_obj.select_entity_manager(sub_type=1)
            for classifier in classifier_name:
                if self.__table.is_entity_present_in_column('Name', classifier):
                    self.classifier_obj.delete_classifier(name=classifier)
        if review_request is not None:
            for request_name in review_request:
                self.__admin_console.navigator.navigate_to_governance_apps()
                self.data_source_review_obj.select_request_manager()
                if self.request_manager.search_for_request(request_name):
                    self.request_manager.delete.delete_request(request_name)
        if project_name is not None:
            self.__admin_console.navigator.navigate_to_governance_apps()
            self.inventory_details_obj.select_sensitive_data_analysis()
            if self.file_server_lookup_obj.search_for_project(project_name):
                self.file_server_lookup_obj.delete_project(project_name)
        if inventory_name is not None:
            self.__admin_console.navigator.navigate_to_governance_apps()
            self.inventory_details_obj.select_inventory_manager()
            if self.inventory_details_obj.search_for_inventory(inventory_name):
                self.inventory_details_obj.delete_inventory(inventory_name)
        if plan_name is not None:
            self.__admin_console.navigator.navigate_to_governance_apps()
            self.__admin_console.navigator.navigate_to_plan()
            if self.__rtable.is_entity_present_in_column('Plan name', plan_name):
                self.plans_obj.action_delete_plan(plan_name)

        if project_name is not None:
            if pseudo_client_name is None:
                pseudo_client_name = project_name[:]
            all_clients_names = self.commcell.clients.all_clients.keys()
            for client_name in all_clients_names:
                if re.search(pseudo_client_name, client_name, re.IGNORECASE):
                    self.log.info('Deleting client: %s' % client_name)
                    try:
                        self.commcell.clients.delete(client_name)
                    except Exception as excp:
                        self.log.info('Unable to delete client: "%s" with \
                        reason: "%s". Continuing anyway.' % (client_name, excp))

            if delete_backupset_for_client:
                client_obj = self.commcell.clients.get(
                    delete_backupset_for_client)
                all_agents_names = client_obj.agents.all_agents.keys()
                for agent_name in all_agents_names:
                    agent_obj = client_obj.agents.get(agent_name)
                    all_backupset_names_list = agent_obj.backupsets.all_backupsets.keys()
                    for backupset_name in all_backupset_names_list:
                        matched = False
                        if not backupset_names_list:
                            if re.search(
                                    pseudo_client_name,
                                    backupset_name,
                                    re.IGNORECASE):
                                matched = True
                        else:
                            if backupset_name in backupset_names_list:
                                matched = True
                        if matched:
                            self.log.info(
                                'Deleting backupset: %s' %
                                backupset_name)
                            try:
                                agent_obj.backupsets.delete(backupset_name)
                            except Exception as excp:
                                self.log.info(
                                    'Unable to delete backupset: "%s" with \
                                reason: "%s". Continuing anyway.' %
                                    (backupset_name, excp))

        if credential_name is not None:
            self.__admin_console.navigator.navigate_to_credential_manager()
            if self.__rtable.is_entity_present_in_column(
                    self.__admin_console.props['label.credentialName'], credential_name):
                self.credential_manager.action_remove_credential(credential_name)

    def risk_analysis_cleanup(self, project_name=None, plan_name=None):
        """
        Deletes the Risk Analysis project and plan
        Args:
            project_name(str)       -- Name of the RA Project
            plan_name(str)          -- Name of the RA SDG Plan
        """
        if project_name is not None:
            self.log.info("Project name is passed. Deleting Project")
            self.__admin_console.navigator.navigate_to_risk_analysis()
            self.__admin_console.navigator.switch_risk_analysis_tabs(cs.RATab.PROJECTS)
            if self.file_server_lookup_obj.search_for_project(project_name):
                self.log.info("Project name is returned by search")
                self.file_server_lookup_obj.delete_project(project_name)
                self.log.info("Project deleted successfully")

        if plan_name is not None:
            self.log.info("Plan name is passed. Deleting Project")
            self.__admin_console.navigator.navigate_to_plan()
            if self.__rtable.is_entity_present_in_column('Plan name', plan_name):
                self.log.info("Plan name is returned by search")
                self.plans_obj.action_delete_plan(plan_name)
                self.log.info("Plan deleted successfully")

    @staticmethod
    def get_schedule_datetime(frequency=None, exceptions=False, custom_time=None):
        '''
        Returns the schedule options based on current time
            Args:
            frequency (Str) -- For Schedule Frequency
                Valid Values:
                    "One time"
                    "Daily"
                    "Weekly"
                    "Montyly"
            custom_time (datetime)  --  Using a custom time for schedule
            exceptions (Bool)  -- For Exceptions
        '''
        schedule_options = {}
        now = datetime.now()
        if custom_time is not None:
            now = custom_time
        if frequency is not None:
            schedule_options['schedule_time'] = now
            schedule_options['hours'] = now.strftime("%I")
            schedule_options['mins'] = now.strftime("%M")
            schedule_options['session'] = now.strftime("%p")
            schedule_options['repeat'] = str(int(now.strftime("%m")))
            schedule_options['date'] = now.strftime("%d")
        if frequency == 'One time':
            schedule_options['year'] = now.strftime("%Y")
            schedule_options['month'] = now.strftime("%B")
            schedule_options['date'] = now.strftime("%d")
        elif frequency == 'Weekly':
            schedule_options['days'] = [now.strftime("%A")]
        elif frequency == 'Monthly':
            schedule_options['onday'] = str(int(now.strftime("%d")))
        if exceptions:
            next_day = now + timedelta(days=1)
            schedule_options['exceptiondays'] = [str(int(next_day.strftime("%d")))]
        return schedule_options

    def verify_last_collection_time(self, last_collection_time, schedule_options):
        '''
        Verifies the last collection time for inventory asset scan
            Args:
            last_collection_time (str) -- Last collection time
            schedule_options (dict)  -- schedule options to compare the collection time with
        '''
        last_collection_time = datetime.strptime(
            last_collection_time, "%b %d, %I:%M %p").replace(year=datetime.today().year)
        schedule_time = schedule_options['schedule_time']
        if last_collection_time >= schedule_time:
            self.log.info('Last collection time is greater than or equal to scheduled time')
        else:
            raise Exception("Last collection time is less than scheduled time")

    def monitor_classifier_training(self, status, time_out=20):
        """Monitors the classifier training job
            Args:

                time_out            (int)   --  Threshold wait time in mins
                                                    Default : 20

                status              (str)   --  Status of classifier to wait for
        """
        start_time = int(time.time())
        current_time = start_time
        completion_time = start_time + time_out * 60
        while completion_time > current_time:
            current_status = self.classifier_obj.get_training_status()
            self.log.info("Current classifier status : %s", current_status)
            if re.search(status, current_status, re.IGNORECASE):
                self.log.info("Expected status reached : %s", current_status)
                return
            time.sleep(30)
            current_time = int(time.time())
        raise Exception("Timeout at classifier training")

    def valid_row_list(self, db_path, data_source=cs.FILE_SYSTEM):
        """
        Returns list of valid row items for Advance Search SDG
        Args:
            db_path (str): Path to GDPR DB
            data_source (str): SDG DataSource Type Ex:- (File system/Exchange)
        Return:
                List of Valid Row Items, for Advance Search SDG
        """
        flag = 0
        valid_row_items = list()
        if data_source in (cs.DATABASE, cs.EXCHANGE):
            flag = 1
        temp_db_entites = []
        for item in self.advance_entity_names:
            temp_db_entites.append(
                cs.DB_COLUMN_NAMES[cs.ADVANCE_SEARCH_FIELDS.index(item)].strip()
            )
        valid_row_items = self.activate_utils.db_get_sensitive_columns_list(
            data_source,
            temp_db_entites,
            db_path,
            flag
        )
        # For FileSystem,OneDrive,GDrive,Database validity is only dependent on file content
        # For Exchange If Attachment has sensitive content and body doesn`t it will count.
        if data_source == cs.EXCHANGE:
            # Get Valid Attachment Files
            valid_item = '(\'' + '\',\''.join(valid_row_items) + '\')'
            fetch_attachments_query = f"""
            Select FileName from {cs.ENTITY_TABLE_NAME} where {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[cs.EXCHANGE]}
            IN {valid_item}
            """
            valid_attachments = self.activate_utils.query_database(
                db_path, fetch_attachments_query)['result']
            valid_attachments = [item.get('FileName') for item in valid_attachments]
            valid_attachments = '(\'' + '\',\''.join(valid_attachments) + '\')'
            additional_rows_query = f"""
            Select {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[cs.EXCHANGE]}  from {cs.METADATA_TABLE_NAME} where
            {cs.EXCHANGE_ATTACHMENT_FIELD} IN {valid_attachments}
            """
            valid_attachments = self.activate_utils.query_database(
                db_path, additional_rows_query)['result']
            valid_attachments = [
                item.get(cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[cs.EXCHANGE]) for item in valid_attachments]
            # Select attachment items not selected earlier
            valid_row_items = valid_row_items + list(set(valid_attachments) - set(valid_row_items))

        return valid_row_items

    def verify_advance_search(self, db_path, data_source=cs.FILE_SYSTEM):
        """
        Verify advance search functionality for SDG/FSO
        Args:
            db_path (str): Path to GDPR DB
            data_source (str): SDG DataSource Name
        Return:
            status (bool) True/False whether verification is passed or failed
        """
        status = True
        or_count = 2
        query_dict = dict()
        db_data_entity = list()
        db_data_metadata = list()
        performed_query_list = list()
        error_list = []
        flag = 0
        if data_source in (cs.DATABASE, cs.EXCHANGE):
            flag = 1
        valid_row_items = self.valid_row_list(db_path, data_source)
        valid_row_items = '(\'' + '\',\''.join(valid_row_items) + '\')'
        db_data_entity = self.activate_utils.query_database(
            db_path,
            f"""select * from {cs.ENTITY_TABLE_NAME} where 
            {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]} IN {valid_row_items}"""
        )['result']

        if data_source != cs.FILE_SYSTEM:
            db_data_metadata = self.activate_utils.query_database(
                db_path,
                f"""select * from {cs.METADATA_TABLE_NAME} where 
                {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]} IN {valid_row_items}"""
            )['result']
            advance_selector_ui = {
                i: self._queries_per_entity for i in self._advance_entity_names}
        else:
            advance_selector_ui = \
                {i: self._queries_per_entity for i in self._advance_entity_names + self._advance_column_names}

        for rows in db_data_entity:
            pending_selectors = [k.strip() for (
                k, v) in advance_selector_ui.items() if v > 0]
            non_empty_columns = [k.strip()
                                 for (k, v) in rows.items() if v is not None]
            for col in pending_selectors:
                db_label = cs.DB_COLUMN_NAMES[cs.ADVANCE_SEARCH_FIELDS.index(col)].strip()
                if db_label in non_empty_columns and rows['Flag'] == flag:
                    advance_selector_ui[col] = advance_selector_ui[col] - 1
                    test_value = rows[db_label].split(cs.DB_ENTITY_DELIMITER)[0].strip()
                    ui_test_value = test_value
                    if db_label == cs.DB_SEARCH_TEXT_FIELD:
                        ui_test_value = f"\"{ui_test_value}\""
                    self.__admin_console.driver.refresh()
                    self.__admin_console.wait_for_completion()
                    self.data_source_discover_obj.select_review()
                    ui_output_value, adv_query = \
                        self.data_source_review_obj.do_advanced_search(
                            selector_list=[col],
                            value_list=[ui_test_value],
                            data_source=data_source)

                    query = f"""select [{cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]}],ID from 
                    {cs.ENTITY_TABLE_NAME} where [{db_label}] like '%{test_value}%' AND 
                    {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]} IN {valid_row_items}"""
                    db_data_temp = self.activate_utils.query_database(
                        db_path, query)['result']
                    db_output_value = []
                    for rows_temp in db_data_temp:
                        if data_source != cs.FILE_SYSTEM:
                            mquery = f"""select [{cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]}],
                            [{cs.EXCHANGE_MAILBOX_DB_FIELD}],[{cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD}] 
                            from {cs.METADATA_TABLE_NAME} where Eid = {rows_temp['ID']}"""
                            mdata = self.activate_utils.query_database(
                                db_path, mquery)['result']
                            rows_temp = mdata[0]
                            if data_source == cs.EXCHANGE:
                                for i in range(len(
                                        rows_temp[cs.EXCHANGE_MAILBOX_DB_FIELD].split(cs.DB_ENTITY_DELIMITER))):
                                    db_output_value.append(
                                        rows_temp[cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]])
                                if rows_temp[cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD]:
                                    for item in rows_temp[cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD].split("\n"):
                                        item = item.strip()[1:-1].split(",")
                                        for i in item[1].strip().split(cs.DB_ENTITY_DELIMITER):
                                            db_output_value.append(item[0].strip())
                        else:
                            db_output_value.append(
                                rows_temp[cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]])
                    self.log.info("Performing Query:- {}".format(adv_query))
                    performed_query_list.append(adv_query)
                    db_output_value = sorted([" ".join(item.split()) for item in db_output_value])
                    ui_output_value = sorted(ui_output_value)
                    if len(ui_output_value) == 0 or db_output_value != ui_output_value:
                        error_list.append(adv_query)
                        status = False
                        self.log.info(
                            "Advance search output Mismatched DB:%s , UI: %s" % (
                                db_output_value, ui_output_value))
                    else:
                        self.log.info(
                            "Advance search output Matched DB:%s , UI: %s" % (
                                db_output_value, ui_output_value))

            if or_count != 0:
                for col in self._advance_entity_names:
                    db_label = cs.DB_COLUMN_NAMES[
                        cs.ADVANCE_SEARCH_FIELDS.index(col)].strip()
                    if db_label in non_empty_columns and rows['Flag'] == flag:
                        selector_value = rows[db_label].split(cs.DB_ENTITY_DELIMITER)[0]
                        query = f"""
                        select [{cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]}],ID from  
                        {cs.ENTITY_TABLE_NAME} where [{db_label}] like '%{selector_value}%' AND 
                        {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]} IN {valid_row_items}"""
                        db_data_temp = self.activate_utils.query_database(
                            db_path, query)['result']
                        db_output_value = []
                        for rows_temp in db_data_temp:
                            if data_source != cs.FILE_SYSTEM:
                                mquery = f"""select [{cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]}],
                                [{cs.EXCHANGE_MAILBOX_DB_FIELD}],[{cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD}] from 
                                {cs.METADATA_TABLE_NAME} where Eid = {rows_temp['ID']}"""
                                mdata = self.activate_utils.query_database(
                                    db_path, mquery)['result']
                                rows_temp = mdata[0]
                                if data_source == cs.EXCHANGE:
                                    for i in range(len(
                                            rows_temp[cs.EXCHANGE_MAILBOX_DB_FIELD].split(cs.DB_ENTITY_DELIMITER))):
                                        db_output_value.append(
                                            rows_temp[cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]])
                                    if rows_temp[cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD]:
                                        for item in rows_temp[cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD].split("\n"):
                                            item = item.strip()[1:-1].split(",")
                                            for i in item[1].strip().split(cs.DB_ENTITY_DELIMITER):
                                                db_output_value.append(item[0].strip())
                            else:
                                db_output_value.append(
                                    rows_temp[cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]])
                        query_dict[col] = \
                            [selector_value, [" ".join(item.split()) for item in db_output_value]]
                        or_count = or_count - 1
                        self._advance_entity_names.remove(col)
                        break
            if or_count == 0 and len(pending_selectors) == 0:
                break

        advance_selector_ui = {
            i: self._queries_per_entity for i in self._advance_column_names}
        for rows in db_data_metadata:
            pending_selectors = [k.strip() for (k, v) in advance_selector_ui.items() if v > 0]
            non_empty_columns = [k.strip() for (k, v) in rows.items() if v is not None]
            for col in pending_selectors:
                table_name = cs.METADATA_TABLE_NAME
                db_label = cs.DB_COLUMN_NAMES[
                    cs.ADVANCE_SEARCH_FIELDS.index(col)].strip()
                if db_label in non_empty_columns:
                    advance_selector_ui[col] = advance_selector_ui[col] - 1
                    test_value = rows[db_label].split(cs.DB_ENTITY_DELIMITER)[0].strip()
                    ui_test_value = test_value
                    if db_label == cs.DB_SEARCH_TEXT_FIELD:
                        ui_test_value = f"\"{ui_test_value}\""
                    self.__admin_console.driver.refresh()
                    self.__admin_console.wait_for_completion()
                    self.data_source_discover_obj.select_review()
                    ui_output_value, adv_query = \
                        self.data_source_review_obj.do_advanced_search(
                            selector_list=[col],
                            value_list=[ui_test_value],
                            data_source=data_source)

                    query = f"""select [{cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]}],
                    [{cs.EXCHANGE_MAILBOX_DB_FIELD}],[{cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD}] 
                    from {table_name} where [{db_label}] like '%{test_value}%' AND 
                    {cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]} IN {valid_row_items}"""
                    db_data_temp = self.activate_utils.query_database(
                        db_path, query)['result']
                    db_output_value = []
                    for rows_temp in db_data_temp:
                        if data_source == cs.EXCHANGE:
                            for i in range(len(rows_temp[cs.EXCHANGE_MAILBOX_DB_FIELD].split(cs.DB_ENTITY_DELIMITER))):
                                db_output_value.append(
                                    rows_temp[cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]])
                            if rows_temp[cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD] and \
                                    db_label == cs.DB_SEARCH_TEXT_FIELD:
                                for item in rows_temp[cs.EXCHANGE_ATTACHMENT_MAILBOXES_FIELD].split("\n"):
                                    item = item.strip()[1:-1].split(",")
                                    for i in item[1].strip().split(cs.DB_ENTITY_DELIMITER):
                                        db_output_value.append(item[0].strip())
                        else:
                            db_output_value.append(
                                rows_temp[cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source]])
                    self.log.info("Performing Query:- {}".format(adv_query))
                    performed_query_list.append(adv_query)
                    ui_output_value = sorted(ui_output_value)
                    db_output_value = sorted([" ".join(item.split()) for item in db_output_value])
                    if len(ui_output_value) == 0 or db_output_value != ui_output_value:
                        error_list.append(adv_query)
                        status = False
                        self.log.info(
                            "Advance search output Mismatched DB:{0} , UI: {1}".format(
                                db_output_value, ui_output_value))
                    else:
                        self.log.info(
                            "Advance search output Matched DB: %s , UI: %s" % (
                                db_output_value, ui_output_value))

        # OR Query
        if or_count == 0:
            test_value_list = [selector_value[0] for selector_value in query_dict.values()]
            db_output_value_list = []
            for output_value in query_dict.values():
                del_items = set(db_output_value_list).intersection(set(output_value[1]))
                temp_output_list = output_value[1]
                for item in del_items:
                    if item in temp_output_list:
                        for i in range(temp_output_list.count(item)):
                            temp_output_list.remove(item)

                db_output_value_list = db_output_value_list + temp_output_list
            ui_selector_list = list(query_dict.keys())
            self.__admin_console.driver.refresh()
            self.__admin_console.wait_for_completion()
            self.data_source_discover_obj.select_review()
            ui_output_value, adv_query = \
                self.data_source_review_obj.do_advanced_search(
                    selector_list=ui_selector_list,
                    value_list=test_value_list,
                    data_source=data_source)
            self.log.info("Performing OR Query:- {}".format(adv_query))
            performed_query_list.append(adv_query)
            db_output_value_list = sorted([" ".join(item.split()) for item in db_output_value_list])
            ui_output_value = sorted(ui_output_value)
            if len(ui_output_value) == 0 or db_output_value_list != ui_output_value:
                error_list.append(adv_query)
                status = False
                self.log.info(
                    "Advance search output Mismatched DB: %s , UI: %s" % (
                        db_output_value_list, ui_output_value))
            else:
                self.log.info(
                    "Advance search output Matched DB:%s , UI: %s" % (
                        db_output_value_list, ui_output_value
                    ))
        else:
            self.log.info(
                "Please Provide more data or Entity fields for OR Query to be formed")

        # Perform AND Query for advance search
        if len(query_dict) > 0:
            selector_ui = list(query_dict.keys())[0]
            input_query = "({0}:{1}) AND ({2}:{3})".format(
                cs.DB_COLUMN_TO_KEY[
                    cs.ADVANCE_SEARCH_FIELDS.index(selector_ui)],
                query_dict[selector_ui][0],
                cs.DB_COLUMN_TO_KEY[
                    cs.DB_COLUMN_NAMES.index(cs.ADVANCE_SEARCH_DB_OUTPUT_FIELD[data_source])],
                query_dict[selector_ui][1][0]
            )
            db_output_list = []
            for output_value in range(query_dict[selector_ui][1].count(query_dict[selector_ui][1][0])):
                db_output_list.append(query_dict[selector_ui][1][0])
            self.__admin_console.driver.refresh()
            self.__admin_console.wait_for_completion()
            self.data_source_discover_obj.select_review()
            self.log.info(
                "Performing AND operation query:- %s" % input_query)
            performed_query_list.append(input_query)
            and_ui_output, adv_query = self.data_source_review_obj.do_advanced_search(
                input_query=input_query,
                data_source=data_source
            )
            db_output_list = sorted([" ".join(item.split()) for item in db_output_list])
            and_ui_output = sorted(and_ui_output)
            if len(and_ui_output) == 0 or db_output_list != and_ui_output:
                error_list.append(adv_query)
                self.log.info("Advance search output Mismatched DB:%s , UI: %s" % (
                    db_output_list, and_ui_output))
                status = False
            else:
                self.log.info("Advance search output Matched DB:%s , UI: %s" % (
                    db_output_list, and_ui_output))
        if not status:
            self.log.info("****************Advance Search Failed for below queries*******************")
            for k in error_list:
                self.log.info(" Failed Query:- %s" % k)
        self.log.info("\n\n")
        for q in performed_query_list:
            if q in error_list:
                self.log.info("Status:- FAILED | Query Used  %s" % q)
            else:
                self.log.info("Status:- PASSED | Query Used  %s" % q)

        self.log.info("\n\n\nTotal Queries Performed = [%s] | PASSED = [%s] | FAILED = [%s] \n\n\n" %
                      (len(performed_query_list), len(performed_query_list) - len(error_list), len(error_list)))
        return status

    @PageService()
    def inventory_exists(self, inventory_name):
        """
        Verify if a inventory with given name is present
        Args:
            inventory_name (str): Name of the inventory
        Return:
            exist (bool) True/False based on presence of the inventory
        Raises:
            Exception:
                If inventory name is not supplied
        """
        if inventory_name is not None:
            self.log.info(f"Checking if the given Inventory with name [{inventory_name}] exist")
            if self.inventory_details_obj.search_for_inventory(inventory_name):
                self.log.info(f"Inventory with given name [{inventory_name}] exist")
                return True
            self.log.info(f"Inventory with given name [{inventory_name}] does not exist")
            return False
        raise Exception("Inventory name is not supplied")

    @PageService()
    def plan_exists(self, plan_name):
        """
        Verify if a plan with given name is present
        Args:
            plan_name (str): Name of the Plan
        Return:
            exist (bool) True/False based on presence of the plan
        Raises:
            Exception:
                If plan name is not supplied
        """
        if plan_name is not None:
            self.log.info(f"Checking if the given Plan with name [{plan_name}] exist")
            if self.__table.is_entity_present_in_column('Plan name', plan_name):
                self.log.info(f"Plan with given name [{plan_name}] exist")
                return True
            self.log.info(f"Plan with given name [{plan_name}] does not exist")
            return False
        raise Exception("Plan name is not supplied")

    @PageService()
    def project_exists(self, project_name):
        """
        Verify if a project with given name is present
        Args:
            project_name (str): Name of the project
        Return:
            exist (bool) True/False based on existence of the project
        Raises:
            Exception:
                If project name is not supplied
        """
        if project_name is not None:
            self.log.info(f"Checking if the given project with name [{project_name}] exist")
            if self.file_server_lookup_obj.search_for_project(project_name):
                self.log.info(f"Project with given name [{project_name}] exist")
                return True
            self.log.info(f"Project with given name [{project_name}] does not exist")
            return False
        raise Exception("Project name is not supplied")

    @PageService()
    def validate_review_request(self, request_name, reviewer, reviewer_password, owner_user, owner_password,
                                approver, approver_password, files=None, is_fso=False, filters=None, db_count=None):
        """
        Validates the review request (both review and approve)
        Args:
            owner_user         (str)   -- username of request creator
            owner_password     (str)   -- Password of request owner
            reviewer           (str)   -- Reviewer to review the request
            reviewer_password  (str)   -- Password for the reviewer user
            request_name       (str)   -- Name of the review request
            approver           (str)   -- Approver of the review request
            approver_password  (str)   -- Password for the approver user
            files              (list)  -- List of files to be reviewed (SDG)
            is_fso             (bool)  -- True if FSO else False
            filters            (dict)  -- Filters to be applied before accepting the documents
            db_count           (int)   -- number of files after applying filters on db
        """
        self.__admin_console.logout()
        # Review Request
        self.__admin_console.login(username=reviewer, password=reviewer_password)
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.data_source_review_obj.select_request_manager()
        self.review.review_approve_request(request_name, files=files, is_fso=is_fso, filters=filters, db_count=db_count)
        self.__admin_console.logout()
        # Request Approval
        self.__admin_console.login(username=owner_user, password=owner_password)
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.data_source_review_obj.select_request_manager()
        self.request_manager.select_request_by_name(request_name=request_name)
        self.review.request_approval()
        self.__admin_console.logout()
        # Approve the Request
        self.__admin_console.login(username=approver, password=approver_password)
        self.__admin_console.navigator.navigate_to_governance_apps()
        self.data_source_review_obj.select_request_manager()
        self.review.approve_request(request_name)
        self.__admin_console.logout()
        self.__admin_console.login(username=owner_user, password=owner_password)

    def apply_time_filters(self, filter_values, data, operation_type):
        """
        applies time filters on data if the time filters are lying in the range of lower bound & upper bound
        Args:
            filter_values   (list):             List of filter values
            data            (list):       Data on which filters are to be applied
            operation_type  (int):              1 for Access, 2 for Modified, 3 for Created time respectively
        returns data after applying the filters on it
        """
        result = []
        for row in data:
            for value in filter_values:
                lower_bound, upper_bound = cs.TIME_RANGE_VALUES[value]
                if lower_bound < row[operation_type] < upper_bound:
                    result.append(row)
        return result

    def apply_filter_on_db(self, filters):
        """
        Applies filter on db and return the info of filtered documents as a list of list
        Args:
            filters (dict): filters to be applied on DB
            Example:
                {'Size': {'1MB to 50MB', '0KB to 1MB'},
                'FileExtension': {'Archives', 'Others'},
                'ModifiedTime': {'4 to 5 Years', '3 to 4 Years', '1 to 2 Years'},
                'CreatedTime': {'4 to 5 Years'}}
        Return documents info in list of list format
        """
        base_query = "SELECT PATH, ACCESS_TIME, MODIFIED_TIME, CREATED_TIME FROM fso_metadata"
        size_conditions = []
        extension_conditions = []
        if cs.FILTER_SIZE in filters:
            size_filters = filters[cs.FILTER_SIZE]
            for value in size_filters:
                lower_bound, upper_bound = cs.SIZE_RANGE_VALUES[value]
                if lower_bound == 0:
                    lower_bound = -1
                size_conditions.append(f"FILE_SIZE > {lower_bound} AND FILE_SIZE <= {upper_bound}")
        if cs.FILTER_EXTENSION in filters:
            extension_filters = filters[cs.FILTER_EXTENSION]
            for value in extension_filters:
                extension_list = cs.EXTENSION_GROUP_VALUES[value]
                if value == cs.EXTENSION_TYPE_OTHERS:
                    extension_conditions.append(f"File_Type NOT IN {extension_list}")
                else:
                    extension_conditions.append(f"File_Type IN {extension_list}")
        extension_conditions = ' or '.join(extension_conditions)
        size_conditions = ' or '.join(size_conditions)
        if size_conditions and extension_conditions:
            query = f'{base_query} WHERE ({size_conditions}) AND ({extension_conditions})'
        elif size_conditions and not extension_conditions:
            query = f'{base_query} WHERE ({size_conditions})'
        elif not size_conditions and extension_conditions:
            query = f'{base_query} WHERE ({extension_conditions})'
        else:
            query = f'{base_query}'
        self.log.info(f"Query being executed is: {query}")
        result = self.sqlitedb.execute(query)
        final_result = []
        for row in result.rows:
            curr_row = [row[0]]
            for index in range(1, 4):
                curr_row.append(int(datetime.now().timestamp())
                                - datetime.strptime(row[index], '%B %d, %Y %I:%M:%S %p').timestamp())
            final_result.append(curr_row)
        if cs.FILTER_ACCESS_TIME in filters:
            access_time_filters = filters[cs.FILTER_ACCESS_TIME]
            final_result = self.apply_time_filters(access_time_filters, final_result, 1)
        if cs.FILTER_MODIFIED_TIME in filters:
            modified_time_filters = filters[cs.FILTER_MODIFIED_TIME]
            final_result = self.apply_time_filters(modified_time_filters, final_result, 2)
        if cs.FILTER_CREATED_TIME in filters:
            created_time_filters = filters[cs.FILTER_CREATED_TIME]
            final_result = self.apply_time_filters(created_time_filters, final_result, 3)
        return final_result

    def get_random_filters(self, filters_count):
        """
        Creates randomized filters dict with filter names and values to be applied on review page
        Args:
            filters_count       (int):  Number of filters to be generated randomly

        Returns the dict of filters with key as filter name and value as filter value.
        """
        filters = {}
        for _ in range(filters_count):
            filter_name = random.choice(cs.FACET_FILTERS)
            if filter_name == cs.FILTER_SIZE:
                filter_value = random.choice(list(cs.SIZE_RANGE_VALUES.keys()))
            elif filter_name == cs.FILTER_EXTENSION:
                filter_value = random.choice(list(cs.EXTENSION_GROUP_VALUES.keys()))
            else:
                filter_value = random.choice(list(cs.TIME_RANGE_VALUES.keys()))
            if filter_name in filters:
                filters[filter_name].add(filter_value)
            else:
                filters[filter_name] = {filter_value}
        return filters

    def generate_filters(self):
        """ Generates filters to be applied on request review page """
        count = 0
        filter_dict = {}
        retry_count = 10
        while count <= 0 and retry_count > 0:
            filter_dict = self.get_random_filters(2)
            count = len(self.apply_filter_on_db(filter_dict))
            retry_count -= 1
        return filter_dict

    def verify_review_operation_from_db(self, documents_info):
        """
        Verify if the review operation worked properly by verifying that documents are not present in re-created db.
        Args:
            documents_info  (list[list]):   info of documents on which the operation is performed
        """
        directory_path = []
        self.log.info('Creating Path list to match entries from DB')
        for item in documents_info:
            directory_path.append(item[0])
        directory_path = tuple(directory_path)
        query = f'SELECT COUNT(*) FROM fso_metadata WHERE PATH IN {directory_path}'
        query = query.replace('\\\\', '\\')
        result = self.sqlitedb.execute(query)
        if result.rows[0][0] != 0:
            self.log.info("Review Action doesn't work properly. Files are still present in the directory")
            raise Exception("Review Action doesn't work properly. Files are still present in the directory")
        self.log.info('Review Action Verified Successfully')

    def fetch_latest_gdpr_wrkflow_job_id(self, lookup_time=1):
        """Returns the latest workflow job ID for GDPR task approval

                Args:

                    lookup_time     (int)       --  get all the jobs executed within the number of hours
                                                        (Default - 1hr)

                Returns:

                    str --  job id of workflow job
        """
        job = self.commcell.job_controller.all_jobs(lookup_time=lookup_time, job_filter='90')
        # filter out other non gdpr jobs
        for each_job in job.copy():
            if job[each_job]['job_type'] != 'GDPR task approval':
                del job[each_job]
        latest_job_id = list(job.keys())[0]
        if len(job) > 1:
            self.log.info("Found Multiple workflow job ids. Fetching latest one")
            latest_job_id = max(job.keys())
        return latest_job_id
    
    def get_latest_job_by_operation(self, operation, client_name=None):
        """
        Returns the latest or last run data curation job details
             Args:
                operation_type (str)  - job operation name
             Optional Args:
                client_name    (str)  - name of the client

            Returns job details
        """
        details_dict = {}
        job_controller = self.commcell.job_controller
        try:
         time.sleep(10)
         self.log.info(job_controller.active_jobs())
         all_active_jobs = job_controller.active_jobs(client_name=client_name)
         self.log.info(all_active_jobs)
         (running_job_id, details_dict) = self.find_job_by_operation(
             all_active_jobs, operation)
        except:
            self.log.info("Exception occurred while getting active jobs")
            return None
        if running_job_id > 0:
         job_object = Job(self.commcell, running_job_id)
         self.log.info(f"Waiting for the job {running_job_id} to complete")
         job_object.wait_for_completion()
         self.log.info(f"Job id is {job_object.job_id}")
         details_dict.update({"Id": running_job_id})
         # change the key name from status to Status
         details_dict[cs.STATUS] = details_dict.pop("status")
         self.log.info(f"Job status is {job_object.status}")

        else:
         try:
             finished_jobs = job_controller.finished_jobs(
                 client_name=client_name)
             (running_job_id, details_dict) = self.find_job_by_operation(
                 finished_jobs, operation)
             job_object = Job(self.commcell, running_job_id)
             job_object.wait_for_completion()
             self.log.info(f"Job id is {job_object.job_id}")
             self.log.info(f"Job status is {job_object.status}")
             # change the key name from status to Status
             details_dict[cs.STATUS] = details_dict.pop("status")
             details_dict.update({"Id": running_job_id})

         except:
             self.log.info("Exception occurred while getting finished jobs")
             return None
        return details_dict


    def find_job_by_operation(self, jobs_dict, operation):
        """
        Finds the latest job by operation from a dictionary 
             Args:
                job_dict  (dict)  - jobs details dictionary
                operation (str)   - operation type to find

            Returns 
                    tuple  --  job id, latest job details matching the operation

        """
        job_id = 0
        details_dict = {}
        for id in jobs_dict:
            if jobs_dict.get(id).get('operation') == operation:
                self.log.info("Found a job")
                job_id = id
                details_dict = jobs_dict.get(id)
                break
        return (job_id, details_dict)