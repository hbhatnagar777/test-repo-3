# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for data source Create/Edit/Update Schema/Import data operations

    DataSourceHelper:

        __init__()                              --      initialize the DataSourceHelper class

        check_content_for_solr_docs             --      checks whether content field is populated or not in solr

        populate_test_data                      --      populates basic test data text files on client

        file_crawl_after_folder_modify_delete   --      runs crawl job after modify & deleting all files in folder

        file_crawl_after_random_folder_add      --      runs crawl job after adding new folders

        file_crawl_after_random_file_modify_delete-     runs crawl job after modifying/deleting few random files

        monitor_crawl_job()                     --      Monitors the crawl job for the input job id

        create_open_data_source                 --      Creates open data source

        create_file_data_source                 --      Creates file system data source

        form_file_data_source_properties        --      forms the properties needed for file system data source

        form_data_source_properties             --      forms the data source dynamic properties

        update_data_source_schema               --      Updates the schema for the data source

        import_random_data                      --      imports random data into data source

        validate_data_from_handler_response     --      validate whether handler response matches or not

        form_entity_extraction_config           --      forms the entity config properties needed for the data source

        get_data_source_starting_with_string    --      Returns the first data source name which starts with a string

        get_running_job_id                      --      Returns the running crawl job ID of a datacube datasource

        prune_orphan_datasources                --      Calls an API to prune the orphan datasources

        check_datasource_exists()               --      Checks if a datasource is present with the given name

        get_datasource_collection_name()        --      Gets the collection and datasource full name for
                                                        a given datasource name

        wait_for_job()                          --      Waits for crawl job to complete on a given ediscovery
                                                        data source

        get_doc_count_for_client()              --      Returns the total document count present in the backup
                                                        of given client name

        validate_adm_datasources_with_config()  --      Verifies the datasource information present in config data
                                                        to that of the actual data in commcell

        get_doc_counts_from_solr()              --      get total doc counts from SOLR

        Get data from solr()                    --      Get data from solr

        validate_csv_data_with_solr()           --      Validates the data in csv with response received from SOLR

"""
import json
import os
import time
import pandas as pd
import numpy as np
import random
from cvpysdk.activate import Activate
from cvpysdk.client import Client
from cvpysdk.constants import AppIDAType
from cvpysdk.activateapps.ediscovery_utils import EdiscoveryDatasource
from datetime import datetime
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils import logger
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.utils.activateutils import ActivateUtils


class DataSourceHelper():
    """Helper class for data source operations"""

    def __init__(self, commcell_object):
        """Initialize the DataSourceHelper object"""
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.cvpysdk_object = self.commcell._cvpysdk_object
        self.mark_file = self.commcell._services['DATASOURCE_ACTIONS']
        self.activate_utils = ActivateUtils()
        self.activate = Activate(self.commcell)
        self.fso_servers = self.activate.file_storage_optimization()

    def check_content_for_solr_docs(self, solr_response, file_list=None, content_present=True, check_all=True):
        """checks whether content field is populated with value in solr or not

                Args:

                    solr_response       (dict)      --      Solr response JSON

                    file_list           (list)      --      list of files which needs to be checked against in solr
                                                                Example : [r"c:\doc\test.txt",r"d:\dco\testing1.doc"]

                    content_present     (bool)      --      bool to specify whether content has to be present or
                                                                                not for given file list

                    check_all           (bool)      --      bool to specify whether to check content for all docs or
                                                                                only provided file list

                Returns:
                    None

                Raises:
                    Exception:

                            if input is not valid

                            if content is not present for any solr doc

        """
        if not isinstance(solr_response, dict):
            raise Exception("Input data is not valid")
        file_list_count = 0
        if file_list is not None:
            file_list_count = len(file_list)
        self.log.info(f"Validate solr data for content field populated : {content_present}")
        solr_doc_count = 0
        for solr_doc in solr_response['response']['docs']:
            self.log.info(f"Analyzing Solr Document : {solr_doc[dynamic_constants.FIELD_URL]}")
            if content_present:
                if dynamic_constants.FIELD_CONTENT in solr_doc:
                    if solr_doc[dynamic_constants.FIELD_CONTENT] is None \
                            or solr_doc[dynamic_constants.FIELD_CONTENT] == '':
                        if check_all:
                            raise Exception(
                                f"Content field is not populated for document: {solr_doc[dynamic_constants.FIELD_URL]}")
                        self.log.info(
                            f"Content field is not populated for document: {solr_doc[dynamic_constants.FIELD_URL]}")
                    if file_list is not None and solr_doc[dynamic_constants.FIELD_URL] in file_list:
                        self.log.info(
                            f"Content is populated for specified files:{solr_doc[dynamic_constants.FIELD_URL]}")
                        solr_doc_count = solr_doc_count + 1
                    else:
                        self.log.info(f"Content is populated for files:{solr_doc[dynamic_constants.FIELD_URL]}")
            else:
                if dynamic_constants.FIELD_CONTENT in solr_doc:
                    if check_all:
                        raise Exception(
                            f"Content field is populated for document:{solr_doc[dynamic_constants.FIELD_URL]}")
                    self.log.info(f"Content field is populated for document:{solr_doc[dynamic_constants.FIELD_URL]}")
                if file_list is not None and solr_doc[dynamic_constants.FIELD_URL] in file_list:
                    self.log.info(
                        f"Content is not populated for specified files:{solr_doc[dynamic_constants.FIELD_URL]}")
                    solr_doc_count = solr_doc_count + 1
                else:
                    self.log.info(f"Content is not populated for files:{solr_doc[dynamic_constants.FIELD_URL]}")

        if solr_doc_count != file_list_count:
            raise Exception(f"Specified file list count & solr doc verification count not matches"
                            f"File list count : {file_list_count} Solr doc count : {solr_doc_count}")
        self.log.info(f"Validation Passed with content [{content_present}] With All docs criteria [{check_all}]")

    def file_crawl_after_random_file_modify_delete(
            self,
            data_source_obj,
            machine_obj,
            index_server_helper,
            test_data_path,
            file_count_to_alter,
            root_folder_count=0):
        """ runs crawl job after modifying & deleting few random files in given test data path

                Args:

                    data_source_obj         (obj)       --  data source class object

                    machine_obj             (obj)       --  machine class object

                    index_server_helper     (obj)       --  index server helper class object

                    test_data_path          (str)       --  root folder path where data resides

                    file_count_to_alter     (int)       --  Specifies number of files to be modified/deleted

                    root_folder_count       (int)       --  folder count present in root share path string
                                                                Default =0 *** Applicable only for content crawl***
                                                                    Example :
                                                                        Share path : c:\Test
                                                                        count = 2

                Returns:

                    None

                Raises:

                    Exception:

                        if failed to perform File modify/delete

                        if failed to validate result on index server

        """
        if not isinstance(test_data_path, str) or not isinstance(file_count_to_alter, int):
            raise Exception("Input data is not valid")
        file_list = machine_obj.get_files_in_path(folder_path=test_data_path)
        file_list = [x.lower() for x in file_list]
        self.log.info(f"File list from dataset : {file_list}")
        # use random.sample to get unique files from list
        modify_file_list = random.sample(file_list, k=file_count_to_alter)
        self.log.info(f"Modify files list : {modify_file_list}")
        # remove modify file list from original list so that it wont intersect with delete operation
        for modify_file in modify_file_list:
            self.log.info(f"Going to modify file by appending content to : {modify_file}")
            machine_obj.append_to_file(file_path=modify_file, content="CVModifiedNow")
            file_list.remove(modify_file)
        delete_file_list = random.sample(file_list, k=file_count_to_alter)
        self.log.info(f"Delete files list : {delete_file_list}")
        for delete_file in delete_file_list:
            self.log.info(f"Going to delete the file : {delete_file}")
            machine_obj.delete_file(file_path=delete_file)

        self.log.info("Going to start INCREMENTAL crawl job")
        incr_job_id = data_source_obj.start_job()
        self.monitor_crawl_job(job_id=incr_job_id)
        self.log.info("Going to verify modified & deleted data count on solr")
        file_query_criteria = {dynamic_constants.FIELD_JOB_ID: int(incr_job_id)}
        index_server_helper.validate_data_in_core(data_source_obj=data_source_obj,
                                                  file_count=(file_count_to_alter * 2),
                                                  folder_count=root_folder_count + len(machine_obj.get_folders_in_path(
                                                      folder_path=test_data_path)),
                                                  file_criteria=file_query_criteria)
        self.log.info("Validate file names matches with modified/deleted file list")
        file_query_criteria.update(dynamic_constants.QUERY_FILE_CRITERIA)
        self.log.info(f"Query formed : {file_query_criteria}")
        resp = index_server_helper.index_server_obj.execute_solr_query(core_name=data_source_obj.computed_core_name,
                                                                       select_dict=file_query_criteria,
                                                                       attr_list={dynamic_constants.FIELD_URL})
        for solr_doc in resp['response']['docs']:
            self.log.info(f"Analyzing Solr Document : {solr_doc}")
            if solr_doc[dynamic_constants.FIELD_URL] in modify_file_list:
                self.log.info(f"Document present in modify file list")
            elif solr_doc[dynamic_constants.FIELD_URL] in delete_file_list:
                self.log.info(f"Document present in Delete file list")
            else:
                raise Exception(
                    f"Document {solr_doc[dynamic_constants.FIELD_URL]} is neither "
                    f"present in modify/Delete list. Please check")

    def file_crawl_after_random_folder_add(
            self,
            data_source_obj,
            machine_obj,
            index_server_helper,
            test_data_path,
            folder_name,
            existing_folder,
            file_count,
            root_folder_count=0):
        """runs crawl job after adding new folders and new files

                Args:

                    data_source_obj     (obj)       --      data source class object

                    machine_obj         (obj)       --      machine class object

                    index_server_helper (obj)       --      index server helper class object

                    test_data_path      (str)       --      root folder path where data resides

                    folder_name         (str)       --      prefix for new random folder name

                    existing_folder     (str)       --      Existing folder name where new files to be added

                    file_count          (int)       --      number of files to be generated in each folder

                    root_folder_count   (int)       --      folder count present in root share path string
                                                                Default =0 *** Applicable only for content crawl***
                                                                    Example :
                                                                        Share path : c:\Test
                                                                        count = 2

                Returns:

                    None

                Raises:

                    Exception:

                        if failed to perform folder/File add

                        if failed to validate result on index server
        """
        if not isinstance(test_data_path, str) \
                or not isinstance(folder_name, str) \
                or not isinstance(existing_folder, str) \
                or not isinstance(file_count, int):
            raise Exception("Input data is not valid")
        self.populate_test_data(machine_obj=machine_obj, test_data_path=test_data_path,
                                folder_name=f"{folder_name}_1", file_count=file_count, file_name="firstincr.txt")
        self.populate_test_data(machine_obj=machine_obj, test_data_path=test_data_path,
                                folder_name=f"{folder_name}_2", file_count=file_count, file_name="secondincr.txt")
        self.populate_test_data(machine_obj=machine_obj, test_data_path=test_data_path,
                                folder_name=existing_folder, file_count=file_count,
                                file_name="FileInsideFull.txt")

        self.log.info("Going to start INCREMENTAL crawl job")
        incr_job_id = data_source_obj.start_job()
        self.monitor_crawl_job(job_id=incr_job_id)
        self.log.info("Going to verify pushed file data count on solr")
        index_server_helper.validate_data_in_core(
            data_source_obj=data_source_obj,
            file_count=len(machine_obj.get_files_in_path(folder_path=test_data_path)),
            folder_count=root_folder_count + len(machine_obj.get_folders_in_path(folder_path=test_data_path)))

    def file_crawl_after_folder_modify_delete(
            self,
            data_source_obj,
            index_server_helper,
            machine_obj,
            test_data_path,
            modify_folder_name,
            delete_folder_name,
            root_folder_count=0):
        """runs crawl job after modify & deleting all files in folder

                Args:

                    data_source_obj         (obj)       --  data source class object

                    index_server_helper     (obj)       --  Index server helper class object

                    machine_obj             (obj)       --  machine object

                    test_data_path          (str)       --  root folder path where data resides

                    modify_folder_name      (str)       --  folder name where files needs to be modified

                    delete_folder_name      (str)       --  folder name where files needs to be deleted

                    root_folder_count       (int)       --  folder count present in root share path string
                                                                Default =0 *** Applicable only for content crawl***
                                                                    Example :
                                                                        Share path : c:\Test
                                                                        count = 2

                Returns:

                    None

                Raises:

                    Exception:

                        if input is not valid

                        if failed to perform modify/delete

                        if failed to validate result on index server

        """
        if not isinstance(modify_folder_name, str) or not isinstance(delete_folder_name, str):
            raise Exception("Input data is not valid")

        self.log.info(f"Going to modify all files in folder : {modify_folder_name}")
        modify_file_path = os.path.join(test_data_path, modify_folder_name)
        start_time = datetime.utcnow()
        modify_start_time = start_time.strftime(dynamic_constants.SOLR_DATE_STRING)
        self.log.info("Wait for 2 mins before starting modifying the data")
        time.sleep(120)
        machine_obj.modify_test_data(data_path=modify_file_path, modify=True)
        self.log.info("Wait for 2 mins before Ending modifying the data")
        time.sleep(120)
        end_time = datetime.utcnow()
        modify_end_time = end_time.strftime(dynamic_constants.SOLR_DATE_STRING)
        modify_count = len(machine_obj.get_files_in_path(folder_path=modify_file_path))
        self.log.info(f"Total files modified : {modify_count}")
        self.log.info(f"Going to delete the folder : {delete_folder_name}")
        delete_file_path = os.path.join(test_data_path, delete_folder_name)
        delete_file_count = len(machine_obj.get_files_in_path(folder_path=delete_file_path))
        delete_folder_count = len(machine_obj.get_folders_in_path(folder_path=delete_file_path))
        delete_folder_count = delete_folder_count + 1  # add root folder as we are deleting that also
        machine_obj.remove_directory(directory_name=delete_file_path)
        self.log.info(f"Total files Deleted : {delete_file_count}")
        self.log.info(f"Total folders Deleted: {delete_folder_count}")
        self.log.info("Going to start INCREMENTAL crawl job")
        incr_job_id = data_source_obj.start_job()
        self.monitor_crawl_job(job_id=incr_job_id)
        folder_count = len(machine_obj.get_folders_in_path(folder_path=test_data_path))
        self.log.info(f"Total folders : {folder_count}")
        self.log.info("Going to verify Modified file data count on solr")
        solr_date_query = [f"[{modify_start_time} TO {modify_end_time}]"]
        self.log.info(f"Solr modified time query : {solr_date_query}")
        file_query_criteria = {dynamic_constants.FIELD_JOB_ID: int(incr_job_id)}
        file_query_criteria.update(dynamic_constants.QUERY_CISTATE_SUCCESS)
        file_query_criteria.update({dynamic_constants.FIELD_MODIFIED_TIME: solr_date_query})
        index_server_helper.validate_data_in_core(data_source_obj=data_source_obj,
                                                  file_count=modify_count,
                                                  folder_count=folder_count + root_folder_count,
                                                  file_criteria=file_query_criteria)

        self.log.info("Going to verify deleted file data count on solr")
        file_query_criteria = {dynamic_constants.FIELD_JOB_ID: int(incr_job_id)}
        file_query_criteria.update(dynamic_constants.QUERY_CISTATE_DELETE)
        # deleting the folder is marking those folder as files so add those deleted folder count to file count
        index_server_helper.validate_data_in_core(data_source_obj=data_source_obj,
                                                  file_count=delete_file_count + delete_folder_count,
                                                  folder_count=folder_count + root_folder_count,
                                                  file_criteria=file_query_criteria)

    def populate_test_data(self, machine_obj, test_data_path, folder_name, file_count, file_name, file_size=20):
        """creates the test data text files on client

                Args:

                    machine_obj         (obj)       --      machine class object for the client

                    test_data_path      (str)       --      root folder path where data will be generated

                    folder_name         (str)       --      folder name where text files has to be generated

                    file_count          (int)       --      number of files to be generated in each folder

                    file_name           (str)       --      custom file name used to name file created

                    file_size           (int)       --      size of file to be created in KB.
                                                                Default : 20KB

                Returns:

                    None

                Raises:

                    Exception:

                        if input is not valid

                        if failed to populate test data set

        """
        if not isinstance(test_data_path, str) \
                or not isinstance(folder_name, str) \
                or not isinstance(file_name, str) \
                or not isinstance(file_count, int):
            raise Exception("Input data is not valid")
        self.log.info(f"Going to populate test data on access node client : {machine_obj.machine_name}")
        folder_name = os.path.join(test_data_path, folder_name)
        self.log.info(f"Going to populate {file_count} files on file path {folder_name}")
        if not machine_obj.generate_test_data(file_path=folder_name, dirs=0, files=file_count, zero_size_file=False,
                                              custom_file_name=file_name, ascii_data_file=True, file_size=file_size):
            raise Exception(f"Unable to generate test data on access node : {machine_obj.machine_name}")

    def monitor_crawl_job(self, job_id, job_state='completed', time_limit=60, retry_interval=300, **kwargs):
        """Method to monitor the crawl job on a data source

            Args:

                job_id    (str)   --  job id of the crawl job

                job_state (str)   --  job state to finish for. Default : completed

                time_limit(int)   -- Time limit after which job status check shall be
                                                aborted if the job does not reach the desired
                                                 state. Default (in minutes) = 30

                retry_interval(int) --  Retry interval after which job status will be
                                        checked again Default (in seconds) = 300

            kwargs Args:

                raise_exception (bool)    -- Specifies whether to raise exception or not

            Returns:
                None

            Raises:
                Exception:

                    if crawl job failed.
        """
        self.log.info(f"Going to Monitor Job started with id {job_id}")
        job_manager = JobManager(_job=job_id, commcell=self.commcell)
        try:
            if job_manager.wait_for_state(
                    job_state,
                    retry_interval=retry_interval,
                    time_limit=time_limit,
                    hardcheck=True):
                self.log.info(f"Crawl job finished with Expected job state : {job_state}")
                return
        except Exception as ep:
            if kwargs.get('raise_exception', True):
                raise Exception(f"Crawl job got into unexpected job state : {job_manager.job.status} "
                                f"Expected job state : {job_state}")
        self.log.info(f"Crawl job got into unexpected job state : {job_manager.job.status} "
                      f"Expected job state : {job_state}")

    def form_data_source_properties(self, prop_name, prop_value):
        """ Returns the list of dynamic datasource properties based on input property list

                    Args:

                       prop_name        (list)      --  list containing the properties name

                                    Example : ['iscaenabled','caclientid']

                       prop_value       (list)      --  list containing the properties values

                                    Example : ['true','1020']

                    Returns:

                        list      --  Data Source properties values formed

                    Raises:

                        Exception:

                                if input is not valid

        """
        if not isinstance(prop_name, list) or not isinstance(prop_value, list):
            raise Exception("Input data type is not valid")
        data_source_properties = [{"propertyName": prop_name[x],
                                   "propertyValue": prop_value[x]}
                                  for x in range(0, len(prop_name))]
        self.log.info("Dynamic Properties formed : %s", data_source_properties)
        return data_source_properties

    def form_file_data_source_properties(self, prop_values):
        """ Returns the list of file system properties based on input dictionary

            Args:

                prop_values     (dict)      -- dict containing values for file system property fields

                    Example : {
                                "includedirectoriespath":"",
                                "username":"",
                                "password":"",
                                "accessnodeclientid":""
                            }

            Returns:

                list      --  file system properties values formed

            Raises:

                Exception:

                        if input is not valid

        """
        if not isinstance(prop_values, dict):
            raise Exception("Input data type is not valid")
        output = []
        file_properties = None
        ca_config = None
        i = 0
        for prop in dynamic_constants.FILE_DS_DYNAMIC_PROPERTY:
            if prop in prop_values:
                output.append(prop_values[prop])
            else:
                output.append(dynamic_constants.FILE_DS_DYNAMIC_PROPERTY_VALUES[i])
            i = i + 1
        if dynamic_constants.ENTITY_EXTRACTION_ENABLED in prop_values and \
                prop_values[dynamic_constants.ENTITY_EXTRACTION_ENABLED].lower() == "true":
            self.log.info("Entity extraction config found. Going to form it")
            ca_config = self.form_data_source_properties(
                prop_name=dynamic_constants.ENTITY_EXTRACTION_PROPERTY,
                prop_value=[prop_values[dynamic_constants.ENTITY_EXTRACTION_ENABLED],
                            prop_values[dynamic_constants.ENTITY_EXTRACTION_CONFIG],
                            prop_values[dynamic_constants.ENTITY_EXTRACTION_CLOUDID]])
            self.log.info(f"EE config Formed : {ca_config}")
        self.log.info("File system properties Formed : %s", output)
        file_properties = [{"propertyName": dynamic_constants.FILE_DS_DYNAMIC_PROPERTY[property],
                            "propertyValue": output[property]}
                           for property in range(0, len(dynamic_constants.FILE_DS_DYNAMIC_PROPERTY))]
        if ca_config is not None:
            file_properties = file_properties + ca_config
        self.log.info("Properties Json : %s", file_properties)
        return file_properties

    def create_open_data_source(self, data_source_name, index_server_name, ds_properties=None):
        """ Creates open data source on commcell

            Args:

                data_source_name        (str)       --  Name of the data source

                index_server_name       (str)       --  Index server cloud name

                ds_properties           (list)      --  Open data source properties
                            Format Example :[
                                        {
                                            "propertyName": x,
                                            "propertyValue": y
                                        },
                                         {
                                            "propertyName": x,
                                            "propertyValue": y
                                        }
                                        ]

            Returns:

                object      --  Instance of datasource object

            Raises:

                Exception:

                        if input is not valid

                        if failed to create data source
        """
        if not (isinstance(data_source_name, str) or isinstance(index_server_name, str) or
                isinstance(ds_properties, list)):
            raise Exception("Input data type is not valid")
        if ds_properties is None:
            self.log.info("Using Default open data source properties")
            ds_properties = dynamic_constants.OPEN_DS_PROPERTIES
        else:
            self.log.info("Using custom defined open data source properties")
            ds_properties = ds_properties + dynamic_constants.OPEN_DS_PROPERTIES
        self.log.info("Data Source Properties Formed : %s", ds_properties)
        self.commcell.datacube.datasources.add(
            data_source_name,
            index_server_name,
            dynamic_constants.OPEN_DATASOURCE_DSTYPE, ds_properties)
        self.log.info("Open datasource created successfully")
        data_source_obj = self.commcell.datacube.datasources.get(
            data_source_name)
        return data_source_obj

    def create_file_data_source(self, data_source_name, index_server_name, fs_properties):
        """ Creates File system data source on commcell

            Args:

                data_source_name        (str)       --  Name of the data source

                index_server_name       (str)       --  Index server cloud name

                fs_properties           (dict)      --  File system properties
                    ***output of form_file_data_source_properties function***

                            Format Example :
                                        {
                                        "propertyName": x,
                                        "propertyValue": y
                                        }


            Returns:

                object      --  Instance of datasource object

            Raises:

                Exception:

                        if input is not valid

                        if failed to create data source
        """
        if not (isinstance(fs_properties, dict) or
                isinstance(data_source_name, str) or
                isinstance(index_server_name, str)):
            raise Exception("Input data type is not valid")

        self.commcell.datacube.datasources.add(
            data_source_name,
            index_server_name,
            dynamic_constants.FILE_SYSTEM_DSTYPE,
            fs_properties)
        self.log.info("File system datasource created successfully")
        data_source_obj = self.commcell.datacube.datasources.get(
            data_source_name)
        return data_source_obj

    def update_data_source_schema(self, data_source_name, field_name, field_type, schema_field):
        """updates schema for the specified data source

            Args:

                data_source_name        (str)       --  Name of the data source

                field_name              (list)      --  list of Field names whose schema has to be updated

                field_type              (list)      --  list of field types

                schema_field            (dict)      --  dict containing schema fields type values
                        Example :
                                    {
                                        "indexed": True,
                                        "stored": True,
                                        "multiValued": False,
                                        "searchDefault": True,
                                        "autocomplete": False
                                    }
            Returns:

                None

            Raises:

                Exception:

                        if input is not valid

                        if failed to update schema
        """
        if not (isinstance(data_source_name, str) or isinstance(field_name, list) or
                isinstance(schema_field, dict) or isinstance(field_type, list)):
            raise Exception("Input data type is not valid. Please check")
        data_source_obj = self.commcell.datacube.datasources.get(data_source_name)
        schema = []
        i = 0
        for field in field_name:
            schema_field['fieldName'] = field
            schema_field['type'] = field_type[i]
            schema.append((schema_field))
            self.log.info("Schema formed : %s", str(schema))
            self.log.info("Calling update schema API to create column : %s", str(field))
            data_source_obj.update_datasource_schema(schema)
            schema.clear()
            i = i + 1

    def import_random_data(self, data_source_name, field_name, field_type, rows=10):
        """ imports random data into data source based on field types

            Args:

                data_source_name        (str)       --  Name of the data source

                field_name              (list)      --  list of field names

                field_type              (list)      --  list of field types

                rows                    (int)       --  number of rows to be generated for importing data

            Returns:

                int         --      total number of data rows imported

            Raises:

                Exception:

                        if input is not valid

                        if failed to import data
        """
        if not (isinstance(data_source_name, str) or
                isinstance(field_name, list) or
                isinstance(field_type, list)):
            raise Exception("Input data type is not valid. Please check")

        data_source_obj = self.commcell.datacube.datasources.get(data_source_name)
        self.log.info("Generating random data")
        input_data = []
        total_crawl_count = 0
        for row in range(rows):
            field_list = dict()
            i = 0
            for field in field_name:
                if field_type[i].lower() in ['int', 'long']:
                    field_list[field] = int(random.random())
                elif field_type[i].lower() in ['float', 'double']:
                    field_list[field] = random.random()
                elif field_type[i].lower() in ['date']:
                    now = datetime.now()
                    date_string = now.strftime(dynamic_constants.SOLR_DATE_STRING)
                    field_list[field] = f"{date_string}"
                else:
                    field_list[field] = str(f"{row}_Random_Generated_Data_{random.random()}")
                i = i + 1
            total_crawl_count = total_crawl_count + 1
            input_data.append((field_list))
        self.log.info("Import Data formed : %s", str(input_data))
        data_source_obj.import_data(input_data)
        self.log.info("Import Data done successfully")
        return total_crawl_count

    def validate_data_from_handler_response(self, source_data, dest_data):
        """ validates whether handler data matches or not

            Args:

                source_data             (dict)      --  Data source Handler response dictionary

                dest_data               (dict)      --  Data source Handler response dictionary to compare with source

            Returns:

                True    -- if data matches
                False   -- if data not matching

            Raises:
                None

        """
        if source_data['numFound'] != dest_data['numFound']:
            msg = f"Document count not matched. Expected : {source_data['numFound']} Actual : {dest_data['numFound']}"
            self.log.info(msg)
            return False
        self.log.info("Total document count matched : %s", dest_data['numFound'])
        self.log.info("Start comparing document by document")
        for doc in source_data['docs']:
            if doc not in dest_data['docs']:
                msg = f"Document missing in destination handler data. Missing document : {doc}"
                self.log.info(msg)
                return False
            self.log.info("Document Matched : %s", doc)
        return True

    def form_entity_extraction_config(self, entities, entity_fields):
        """ Forms the entity extraction configuration properties for data source

                Args:

                    entities        (dict)      --  dict containing entity details

                    entity_fields   (list)      -- field name to extract entity from

                        Example : {
                                        "RER":"Email,Ip",
                                        "NER": "Name",
                                        "DE": "PersonId"
                                  }

                Returns:

                    list      --  file system properties values formed

                Raises:

                    Exception:

                        if input is not valid

        """
        if not (isinstance(entities, dict) or isinstance(entity_fields, list)):
            raise Exception("Input data type is not valid")
        entities_to_extract_rer = []
        entities_to_extract_ner = []
        entities_to_extract_de = []
        if 'RER' in entities:
            entities_to_extract_rer = entities['RER'].split(",")
            self.log.info("Going to get entity id details for RER : %s", entities_to_extract_rer)
            self.log.info("Entity input is of type : %s", type(entities_to_extract_rer))
            entities_to_extract_rer = self.commcell.activate.entity_manager().get_entity_ids(entities_to_extract_rer)
            self.log.info("Entity id's got for RER : %s", entities_to_extract_rer)
        elif 'NER' in entities:
            entities_to_extract_ner = entities['NER'].split(",")
            self.log.info("Going to get entity id details for NER: %s", entities_to_extract_ner)
            self.log.info("Entity input is of type : %s", type(entities_to_extract_ner))
            entities_to_extract_ner = self.commcell.activate.entity_manager().get_entity_ids(entities_to_extract_ner)
            self.log.info("Entity id's got for NER : %s", entities_to_extract_ner)
        elif 'DE' in entities:
            entities_to_extract_de = entities['DE'].split(",")
            self.log.info("Going to get entity id details for DE: %s", entities_to_extract_de)
            self.log.info("Entity input is of type : %s", type(entities_to_extract_de))
            entities_to_extract_ner = self.commcell.activate.entity_manager().get_entity_ids(entities_to_extract_de)
            self.log.info("Entity id's got for DE : %s", entities_to_extract_de)

        entity_extraction_json_value = [entities_to_extract_rer, entities_to_extract_ner, entities_to_extract_de,
                                        entity_fields]
        caconfig = [{"task": dynamic_constants.ENTITY_EXTRACTION_JSON_PROP[x],
                     "arguments": entity_extraction_json_value[x]} for x in range
                    (0, len(dynamic_constants.ENTITY_EXTRACTION_JSON_PROP))]
        caconfig = json.dumps(caconfig)
        self.log.info("Generated Entity config Json : %s", caconfig)
        return caconfig

    def get_data_source_starting_with_string(self, start_string, pseudo_client=False):
        """Returns the first data source name which starts with a string

            Args:
                start_string    (str)   -   String phrase to be used

                pseudo_client   (bool)  -   if pseudo client is created for the data source

            Returns:
                String  -   data source/ pseudo client name starting with the start_string phrase
                None    -   if no such data source name found

        """
        if pseudo_client:
            self.commcell.clients.refresh()
            for ds_name in self.commcell.clients.all_clients:
                if str(ds_name).startswith(start_string):
                    self.log.info(f"Found a potential client with name {ds_name}")
                    return ds_name
            return None
        self.commcell.datacube.datasources.refresh()
        for ds_name in self.commcell.datacube.datasources._get_all_datasources():
            if str(ds_name).startswith(start_string):
                self.log.info(f"Found a potential data source with name {ds_name}")
                return ds_name
        return None

    def get_running_job_id(self, data_source_name):
        """Returns the running crawl job ID of a datacube datasource

            Args:
                data_source_name    (str)   -   datasource name

            Returns:
                String  -   running crawl job ID
                None    -   if no job ID was found

        """
        if not isinstance(data_source_name, str):
            raise Exception("Input data type is not valid")
        ds_obj = self.commcell.datacube.datasources.get(data_source_name)
        if 'jobId' in ds_obj.get_status()['status']:
            return ds_obj.get_status()['status']['jobId']
        return None

    def datasource_file_actions(self, operation_type, files_data):
        """Calls an API to mark files for actions

            Args:
                operation_type (enum)       -   type of operation ( file_actions() enum class )
                files_data     (list)       -   files data containing details of the files to be marked for an action

            Returns:
                None

            Raises:
                Response not success

                Invalid response

        """
        if not isinstance(files_data, list) or operation_type not in dynamic_constants.SOLR_FILE_OPERATIONS_MAP:
            raise Exception('Invalid operation type')
        solr_operation_payload = {
            dynamic_constants.MARK_FILE_JSON_OPERATION_KEY: dynamic_constants.SOLR_FILE_OPERATIONS_MAP[operation_type],
            dynamic_constants.MARK_FILE_JSON_FILES_KEY: []}
        for file_data in files_data:
            data = {
                dynamic_constants.PAYLOAD_DATA_SOURCE_ID_PARAM: int(file_data[dynamic_constants.DATA_SOURCE_ID_PARAM]),
                dynamic_constants.PAYLOAD_CONTENT_ID_PARAM: file_data[dynamic_constants.CONTENT_ID_PARAM]}
            if operation_type != dynamic_constants.file_actions.SOLR_FILE_DELETE_OPERATION:
                data[dynamic_constants.PAYLOAD_CATEGORY_TAG_PARAM] = \
                    dynamic_constants.PAYLOAD_CATEGORY_TAG_VALUE_MAP[operation_type]
            solr_operation_payload[dynamic_constants.MARK_FILE_JSON_FILES_KEY].append(data)
        solr_operation_payload[dynamic_constants.MARK_FILE_JSON_FILES_KEY] = \
            str(solr_operation_payload[dynamic_constants.MARK_FILE_JSON_FILES_KEY])
        flag, response = self.cvpysdk_object.make_request(method='POST', url=self.mark_file,
                                                          payload=solr_operation_payload)
        if flag:
            if response.json():
                if response.json()['errorCode'] == 0:
                    return
                raise Exception(f"Exception : Error message {response.json()['errorMsg']}")
            raise Exception('Invalid response')
        raise Exception('Response not success')

    def prune_orphan_datasources(self):
        """
        Calls an API to prune the orphan datasources
            Returns:
                None
        """
        self.log.info("Making API call to prune orphan datasource")
        self.commcell.index_servers.prune_orphan_datasources()
        self.log.info("Datasource Pruning API call complete")

    def check_datasource_exists(self, datasource_name):
        """
        Checks if a datasource is present with the given name
            Args:
                datasource_name(str)    -- Starting part name of the datasource

            Returns:
                bool                    -- boolean value representing the presence of the datasource
        """
        self.log.info(f'Trying to find the datasource starting with name [{datasource_name}]')
        data_source_name = self.get_data_source_starting_with_string(
            start_string=datasource_name)
        if data_source_name is not None:
            self.log.info(f'Datasource name obtained is: [{data_source_name}]')
            return True
        self.log.info(f'Failed to obtain actual datasource name for : [{datasource_name}]')
        return False

    def get_datasource_collection_name(self, datasource_name):
        """
        Gets the collection and datasource full name for a given datasource name
            Args:
                datasource_name(str)    -- Name of the datasource for which collection and
                                            datasource name is to be obtained
            Returns:
                str, str                -- collection name and datasource name
        """

        self.log.info(f"Trying to get full name for : {datasource_name}")
        datasource_actual_name = self.get_data_source_starting_with_string(
            start_string=datasource_name)
        self.log.info(f"Trying to get collection name for : {datasource_actual_name}")
        ds_obj = self.commcell.datacube.datasources.get(datasource_actual_name)
        self.log.info(f"Collection name obtained is : {ds_obj.computed_core_name}")
        return ds_obj.computed_core_name, datasource_actual_name

    def wait_for_job(self, datasource_object):
        """
        Waits for crawl job to complete on a given ediscovery data source
            Args:
                datasource_object(object)  -- Ediscovery datasource object on which the job is running
            Raises:
                When invalid datasource object is passed
                When online crawl job is not invoked
        """
        if not isinstance(datasource_object, EdiscoveryDatasource):
            raise Exception("Pass valid EdiscoveryDatasource object")
        jobs = datasource_object.get_active_jobs()
        if not jobs:
            self.log.info("Active job list returns zero list. so checking for job history")
            jobs = datasource_object.get_job_history()
            if not jobs:
                raise Exception("Online crawl job didn't get invoked for FSO server added")
        self.log.info(f"Job History details got - {jobs}")
        job_id = list(jobs.keys())
        job_id = [int(i) for i in job_id]
        job_id.sort(reverse=True)
        job_id = job_id[0]
        self.log.info(f"Online crawl job invoked with id - {job_id}. Going to wait till it completes")
        self.monitor_crawl_job(job_id=job_id)
        self.log.info(f"Crawl job - {job_id} completed")

    def get_doc_count_for_client(self, client_name):
        """Returns the total document count present in the backup of given client name

            Args:
                client_name (str)   --  Client name

            Returns:
                int --  Integer value denoting the count of documents present in the backup

        """
        total_doc_count = 0
        client_obj: Client = self.commcell.clients.get(client_name)
        all_agents = client_obj.agents.all_agents
        fs_agent = None
        for agent in all_agents:
            if int(all_agents[agent]) in [AppIDAType.WINDOWS_FILE_SYSTEM, AppIDAType.LINUX_FILE_SYSTEM]:
                fs_agent = client_obj.agents.get(agent)
        if not fs_agent:
            raise Exception("File system IDA not found for given client")
        bksets = fs_agent.backupsets.all_backupsets
        for bkset in bksets:
            bkset_obj = fs_agent.backupsets.get(bkset)
            file_count_bkset, file_information_dict = bkset_obj.find()
            total_doc_count += len(file_count_bkset)
        return total_doc_count

    def validate_adm_datasources_with_config(self, validation_data: dict, cleanup=False):
        """Verifies the datasource information present in config data to that of the actual data in commcell

            Args:
                cleanup         (boolean)   -       Whether to clean the datasource after validation or not
                validation_data (dict)      -       Dictionary consisting the fso server/ds information for validation
                                                    Example :
                                                        {
                                                            "LiveCrawlSources": [
                                                                server_name: {
                                                                    "Share Path": path,
                                                                    "Data Source Name": ds_name,
                                                                    "documentCount": doc_count
                                                                },..
                                                            ],
                                                            "BackedupSources": [
                                                                server_name: {
                                                                    "Data Source Name": ds_name
                                                                },...
                                                            ]
                                                        }

            Raises:
                "Latest crawl job failed exception"     --  if the latest crawl job is not completed without any errors
                "Document count mismatch exception"     --  If actual document count is not same as expected
                "Invalid crawl type exception"          --  if the crawl type of datasource does not match with the
                                                            expected crawl type

            Returns:
                None

        """
        self.fso_servers.refresh()
        ds_list_to_clean = {}
        for crawl_type_based_ds in validation_data:
            expected_crawl_type = [
                dynamic_constants.LIVE_CRAWL_TYPE,
                dynamic_constants.FROM_BACKUP_CRAWL_TYPE][
                crawl_type_based_ds == dynamic_constants.BACKEDUP_DS]
            for server_name in validation_data.get(crawl_type_based_ds):
                if self.fso_servers.has_server(server_name):
                    fso_server = self.fso_servers.get(server_name)
                    data_sources = fso_server.data_sources
                    for ds_entry in validation_data.get(crawl_type_based_ds).get(server_name):
                        ds_name = ds_entry.get(dynamic_constants.CSV_DATA_SOURCE_NAME)
                        if expected_crawl_type == dynamic_constants.BACKEDUP_DS:
                            expected_file_count = self.get_doc_count_for_client(server_name)
                        else:
                            expected_file_count = ds_entry.get(dynamic_constants.FSO_DATA_SOURCE_DOCUMENT_COUNT)
                        self.log.info(f"Validating Datasource: {ds_name} now")
                        if data_sources.has_data_source(ds_name):
                            self.log.info(f"Datasource {ds_name} found in the environment, checking further")
                            data_source = data_sources.get(ds_name)
                            ds_list_to_clean.update({ds_name: data_sources})
                            actual_doc_count = data_source.total_documents
                            actual_crawl_type = data_source.crawl_type
                            job_history: dict = data_source.get_job_history()
                            latest_job = sorted(job_history.keys())[-1]
                            latest_job_status = job_history[latest_job][dynamic_constants.FIELD_STATUS].lower()
                            if latest_job_status != dynamic_constants.JOB_COMPLETE.lower():
                                raise Exception(f"Latest crawl job is not completed for the ds {ds_name}.\n "
                                                f"Job Status found : {latest_job_status}")
                            if actual_crawl_type != expected_crawl_type:
                                raise Exception(f"Invalid crawl type ({actual_crawl_type}) assigned to the "
                                                f"datasource: {ds_name}, expected was {expected_crawl_type}")
                            if actual_doc_count != expected_file_count:
                                raise Exception(f"Total document count ({actual_doc_count}) mismatch with the"
                                                f"expected one ({expected_file_count} for datasource: {ds_name}")
                        self.log.info(f"Datasource {ds_name} has been validated successfully")
        if cleanup:
            self.log.info("Starting to cleaning up the datasources")
            for ds_name in ds_list_to_clean:
                self.log.info(f"Deleting Datasource : {ds_name} now")
                ds_list_to_clean[ds_name].delete(ds_name)
                self.log.info(f"Datasource : {ds_name} deleted successfully")

    def get_doc_counts_from_solr(self, client_name, datasource_name):
        """
        get total doc counts from SOLR

        Args:
            client_name         (str):      name of the client on which datasource is added
            datasource_name     (str):      name of the datasource
        """

        datasource_object = self.commcell.activate.file_storage_optimization().get(client_name).data_sources.get(
            datasource_name)
        core_name = datasource_object.computed_core_name
        index_server_object = self.commcell.index_servers.get(datasource_object.cloud_id)

        response = index_server_object.execute_solr_query(core_name, op_params=dynamic_constants.QUERY_ZERO_ROWS)
        return response["response"]['numFound']

    def get_data_from_solr(self, client_name, datasource_name, attributes, op_params, document_type="FILES",
                           is_backedup=False):
        """
        Get data from solr
        Args:
            client_name         (str):      name of the client on which datasource is added
            datasource_name     (str):      name of the datasource
            attributes          (list):     List of fields to get from SOLR index
            op_params           (dict):     Other params and values for solr query. Example : {"rows": 0}
            document_type      (str):       defines what all document types are expected! Example: "FILES", "FOLDERS"
            is_backedup         (bool):     defines if the current datasource is backed up or normal
        Returns:
            content of the response
        Raises:
            SDKException:
                if unable to send request
                if response is not success
        """
        datasource_object = self.commcell.activate.file_storage_optimization().get(client_name).data_sources.get(
            datasource_name)
        core_name = datasource_object.computed_core_name
        index_server_object = self.commcell.index_servers.get(datasource_object.cloud_id)
        select_dict = dict()
        if document_type.upper() == "FILES":
            select_dict.update(dynamic_constants.QUERY_FILE_CRITERIA)
        elif document_type.upper() == "FOLDERS":
            select_dict.update(dynamic_constants.QUERY_FOLDER_CRITERIA)
        else:
            pass
        if is_backedup:
            datasource_id = datasource_object.data_source_id
            select_dict.update({dynamic_constants.DATA_SOURCE_ID_PARAM: datasource_id})
        response = index_server_object.execute_solr_query(core_name, select_dict=select_dict,
                                                          attr_list=attributes, op_params=op_params)
        response = response[dynamic_constants.RESPONSE_PARAM]
        for doc_dict in response[dynamic_constants.DOCS_PARAM]:
            for attribute in attributes:
                if attribute not in doc_dict:
                    doc_dict[attribute] = np.nan
        return response

    def validate_csv_data_with_solr(self, csv_path, solr_response_json,
                                    dashboard=dynamic_constants.SIZE_DISTRIBUTION_DASHBOARD, **kwargs):
        """
        Validates the data in csv with response received from SOLR
        Args:
            csv_path    (list/str):      path to the csv file
            solr_response_json  (dict):     solr response in json format modified as python dictionary
            dashboard   (str):      name of the dashboard to validate the data
        Raises:
            CSV data doesn't match Exception:   when CSV data doesn't match with SOLR data
        """
        self.log.info("Validating csv data with SOLR data")
        csv_dataset = None
        if type(csv_path) == str:
            csv_dataset = pd.read_csv(csv_path)
        elif type(csv_path) == list:
            data_frames = []
            for path in csv_path:
                data_frames.append(pd.read_csv(path))
            csv_dataset = pd.concat(data_frames)
        else:
            raise Exception("CSV path looks to be wrong or badly formatted")

        solr_response_dict = {}
        key_modifier = dynamic_constants.DASHBOARDS_CSV_FIELDS[dashboard]

        for doc_dict in solr_response_json[dynamic_constants.DOCS_PARAM]:
            solr_response_dict[doc_dict['Url']] = doc_dict

        if dashboard == dynamic_constants.SIZE_DISTRIBUTION_DASHBOARD or dashboard == dynamic_constants.FILE_SECURITY_DASHBOARD:
            try:
                csv_dataset[key_modifier['AllowFullControlUsername']] = [item[1:-1].split(', ') for item in
                                                                         csv_dataset[
                                                                             key_modifier['AllowFullControlUsername']]]
                csv_dataset[key_modifier['AllowModifyUsername']] = [item[1:-1].split(', ') for item in
                                                                    csv_dataset[key_modifier['AllowModifyUsername']]]
                csv_dataset[key_modifier['AllowWriteUsername']] = [item[1:-1].split(', ') for item in
                                                                   csv_dataset[key_modifier['AllowWriteUsername']]]
                csv_dataset[key_modifier['AllowListUsername']] = [item[1:-1].split(', ') for item in
                                                                  csv_dataset[key_modifier['AllowListUsername']]]
            except Exception as err:
                self.log.info(err)

        if dashboard == dynamic_constants.TREE_SIZE_DASHBOARD:
            for index in range(len(csv_dataset)):
                csv_dict = dict(csv_dataset.iloc[index])
                solr_dict = solr_response_dict[csv_dict['Path']]

                if solr_dict['DocumentType'] == 1:
                    solr_response_dict[csv_dict['Path']]['DocumentType'] = 'File'

                else:
                    solr_response_dict[csv_dict['Path']]['DocumentType'] = 'Folder'
                    folder_size_unit = csv_dict['Folder Size'][-2:]
                    folder_size = solr_response_dict[csv_dict['Path']]['FolderSize_lv']
                    if folder_size_unit == "GB":
                        solr_response_dict[csv_dict['Path']]['FolderSize_lv'] = round(
                            folder_size / (1024 * 1024 * 1024), 2)
                    elif folder_size_unit == "MB":
                        solr_response_dict[csv_dict['Path']]['FolderSize_lv'] = round(folder_size / (1024 * 1024), 2)
                    else:
                        solr_response_dict[csv_dict['Path']]['FolderSize_lv'] = round(folder_size / 1024, 2)

            csv_dataset['Folder Size'] = [float(item[:-2]) if item == item else item for item in
                                          csv_dataset['Folder Size']]

        if dashboard == dynamic_constants.DUPLICATES_DASHBOARD:
            ui_duplicate_count = kwargs['duplicate_files']
            csv_duplicate_count = len(csv_dataset) - len(csv_dataset['File Name'].drop_duplicates())

            if ui_duplicate_count != csv_duplicate_count:
                raise Exception("Validation failed: Duplicate count is not matching!")

        if dashboard == dynamic_constants.DUPLICATES_DASHBOARD or (
                dashboard == dynamic_constants.FILE_SECURITY_DASHBOARD and key_modifier['Size'] in csv_dataset):
            for index in range(len(csv_dataset)):
                csv_dict = dict(csv_dataset.iloc[index])

                folder_size_unit = csv_dict[key_modifier['Size']][-2:]
                folder_size = solr_response_dict[csv_dict[key_modifier['Url']]]['Size']
                if folder_size_unit == "GB":
                    solr_response_dict[csv_dict[key_modifier['Url']]]['Size'] = round(
                        folder_size / (1024 * 1024 * 1024), 2)
                elif folder_size_unit == "MB":
                    solr_response_dict[csv_dict[key_modifier['Url']]]['Size'] = round(folder_size / (1024 * 1024), 2)
                else:
                    solr_response_dict[csv_dict[key_modifier['Url']]]['Size'] = round(folder_size / 1024, 2)

            csv_dataset[key_modifier['Size']] = [float(item[:-2]) if item == item else item for item in
                                                 csv_dataset[key_modifier['Size']]]

        csv_to_solr_modifier = dict(zip(key_modifier.values(), key_modifier.keys()))
        for index in range(len(csv_dataset)):
            csv_dict = dict(csv_dataset.iloc[index])
            solr_dict = solr_response_dict[csv_dict[key_modifier['Url']]]

            for key in csv_dict:
                if csv_to_solr_modifier[key] not in solr_dict:
                    raise Exception(f"Column {key} not available in solr response")
                if type(csv_dict[key]) == list:
                    solr_dict[csv_to_solr_modifier[key]].sort()
                    csv_dict[key].sort()
                if str(csv_dict[key]) != 'nan' and csv_dict[key] != solr_dict[csv_to_solr_modifier[key]]:
                    raise Exception("CSV data doesn't match with SOLR data")
        self.log.info("Successfully Validated csv data with SOLR data")
