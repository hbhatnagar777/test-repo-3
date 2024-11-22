# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for data source crawl job

    CrawlJobHelper:

        __init__()                      --      initialize the CrawlJobHelper class

        monitor_crawl_job()             --      starts a crawl job and monitor till end
                                                for a given data source name

        get_data_source_stats()         --      returns the data source solr core stats

        get_crawl_docs_count()          --      returns the number of documents crawled

        get_docs_count()                --      returns the count of documents that can
                                                be crawled in given folder path on given machine

        validate_crawl_files_count()    --      Validates whether crawled documents count is
                                                same as the actual documents count
                                                present on the data source

        monitor_job()                   --      Monitors the job for given time and
                                                return true if job completes without any errors else return false

        validate_folder_stats()         --      Verifies if all the folder related data is pushed to solr
                                                and matches with the records in DB

        create_subclients()             --      Creates test data and uses that as content to create the required number
                                                of subclients in defaultBackupSet for File System IDA for a given client

        is_index_import_job()           --      Checks whether the Job was an index import job

        create_files_with_content()     --      Creates files with given file count and content

"""

import time
import calendar
from dateutil import parser
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.JobManager.jobmanager_helper import JobManager
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import *
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper


class CrawlJobHelper():
    """Helper class for data source crawl job monitoring"""

    def __init__(self, tc_object):
        """Initialize the class with testcase object"""
        self.commcell = tc_object.commcell
        self.log = tc_object.log
        self.solr_helper = SolrHelper(tc_object)

    def create_files_with_content(self, client_names, count, content, folder=None):
        """Creates files with given count and content

                Args:

                    client_names        (list)     --  Name of the client

                    count              (int)       --  Number of files to create

                    content             (str)      --  content to be written on files

                    folder              (str)      --  Folder path where files will be created

                Returns:

                    list(str)     --  Folder path where files got generated

                Raises:

                    Exception:

                            if failed to create file
        """
        folder_list = []
        self.log.info(f"Going to create [{count}] files on clients [{client_names}] with content [{content}]")
        for client in client_names:
            machine_obj = Machine(machine_name=client, commcell_object=self.commcell)
            if folder is None:
                options_obj = OptionsSelector(self.commcell)
                drive = options_obj.get_drive(machine_obj)
                folder = f"{drive}RuntimeCreatedby_{options_obj.get_custom_str()}"
            if not machine_obj.check_directory_exists(folder):
                machine_obj.create_directory(directory_name=folder, force_create=True)
            self.log.info(f"Folder name to create files : {folder}")
            cmd = f"1..{count} | foreach {{new-item -path {folder}\\Testdata$_.txt -ItemType File -Value \"{content}\"}}"
            machine_obj.execute_command(command=cmd)
            folder_list.append(folder)
        return folder_list

    def monitor_crawl_job(self, data_source_name, interval_time=10, job_time_limit=75):
        """Method to start and monitor the crawl job on a data source

            Args:

                data_source_name    (str)   --  data source name on which
                crawl job will start and be monitored

                interval_time       (int)   -- Interval (in seconds) after which job state
                                                    will be checked in a loop. Default = 10

                job_time_limit      (int)   --  Time limit for which the crawl job
                has to be monitored

            Returns:
                None

            Raises:
                Exception:

                    if crawl job failed.
                    if data source not found.
        """
        data_source_obj = self.commcell.datacube.\
            datasources.get(data_source_name)
        self.log.info("Starting crawl job on datasource : %s",
                      data_source_name)
        job_id = data_source_obj.start_job()
        if job_id is None:
            raise Exception("Something went wrong with datasource start job")
        self.log.info("Job started with id %s",
                      job_id)
        if self.monitor_job(commcell_object=self.commcell, job=job_id,
                            interval_time=interval_time, job_time_limit=job_time_limit):
            self.log.info("Crawl job completed successfully")
            return
        self.log.error("Crawl job failed.")
        raise Exception("Crawl job failed.")

    def get_data_source_stats(self, data_source_name, client_name):
        """Returns the data source solr core stats

            Args:

                data_source_name    (str)   --  data source name
                client_name         (str)   --  node name of the index server

            Returns:

                core_stats          (dict)  --  details of the data source
                solr statistics
        """
        data_source_obj = self.commcell.datacube. \
            datasources.get(data_source_name)
        dcube_id = data_source_obj.datasource_id
        core_id = self.solr_helper.get_coreid_datasource(dcube_id)
        base_url = self.solr_helper.get_solr_baseurl(client_name, 1)
        data_source_core_name = "{0}{1}_{2}".format(
            FILE_DS_PREFIX,
            data_source_name,
            core_id
        )
        dcube_core_stats = self.solr_helper.get_corestats(
            baseurl=base_url, corename=data_source_core_name
        )
        return dcube_core_stats

    def get_docs_count(self, folder_path,
                       machine_name,
                       username=None, password=None,
                       include_folders=True):
        """Returns the count of files and folders in given folder path

            Args:

                folder_path     (str)   --  network or local path
                machine_name    (str)   --  if commcell client
                                                then client name
                                            else ip address or machine name
                                            for the machine containing the folder
                username        (str)   --  username for machine
                password        (str)   --  corresponding password for user
                include_folders (bool)  --  true to count files and folders in the given folder path
                                            false to count only the files in the given folder path

            Returns:

                count           (int)   --  number of documents present in the folder path

        """
        machine_obj = Machine(
            machine_name=machine_name,
            commcell_object=self.commcell,
            username=username,
            password=password
        )
        count = len(machine_obj.get_files_in_path(
            folder_path
        ))
        if include_folders:
            count += len(machine_obj.get_folders_in_path(
                folder_path
            ))
        return count

    def get_crawl_docs_count(self, data_source_name, client_name):
        """Returns the count of documents crawled from the data source

            Args:

                data_source_name    (str)   --  data source name
                client_name         (str)   --  node name of the index server

            Returns:

                count       (int)   --  total number of documents crawled from
                the data source
        """
        core_stats = self.get_data_source_stats(
            data_source_name=data_source_name, client_name=client_name)
        return core_stats.get('index', 0).get('numDocs', 0)

    def validate_crawl_files_count(self, data_source_name, include_directories_path,
                                   access_node_name, index_server_name):
        """Validates whether crawled documents count is same as the actual documents count
        present on the data source

        Args:
            data_source_name            (str)   -   file data source name

            include_directories_path    (str)   -   (,) separated directory paths
                                                    of the file data source

            access_node_name            (str)   -   access node client name of given
                                                    file data source

            index_server_name           (str)   -   index server name which is assigned
                                                    to the given ile data source

        Returns:
            None

        Raises:

            if input data is not valid

            If number of documents crawled is not same as the actual count

        """
        if not (isinstance(data_source_name, str) and
                isinstance(include_directories_path, str) and
                isinstance(access_node_name, str) and
                isinstance(index_server_name, str)):
            raise Exception("Input data is not of valid datatype")
        crawl_dir_paths = include_directories_path.split(',')
        total_files_count = 0
        for dir_path in crawl_dir_paths:
            total_files_count += self.get_docs_count(
                folder_path=dir_path,
                machine_name=access_node_name,
                include_folders=True
            )
        self.log.info("Number of files present in crawl directories : %s", total_files_count)
        crawled_files_count = self.get_crawl_docs_count(
            data_source_name=data_source_name,
            client_name=self.commcell.index_servers.get(index_server_name).client_name[0]
        )
        self.log.info(
            "Number of documents crawled : %s",
            crawled_files_count)
        if int(crawled_files_count) != int(total_files_count):
            self.log.error(
                "Number of crawled documents are invalid\nExpected: %s\tActual: %s",
                total_files_count,
                crawled_files_count)
            raise Exception("Number of documents crawled were incorrect")
        self.log.info("All the documents were crawled successfully")

    @staticmethod
    def monitor_job(commcell_object, job, interval_time=10, job_time_limit=75):
        """Monitors the job for given time and return true if job completes without any errors else return false

            Args:
                commcell_object     (object)        -   Commcell object
                job                 (int/object)    -   Job ID/ Job object of the job to be monitored
                interval_time       (int)           -   Interval time in minutes
                job_time_limit      (int)           -   Time limit in minutes till which Job needs to be monitored

            Return:
                True    -   if Job completes without any errors
                False   -   if Job fails to complete

        """
        try:
            job_manager = JobManager(_job=job, commcell=commcell_object)
            return job_manager.wait_for_state('completed', interval_time, job_time_limit)
        except Exception:
            return False

    @staticmethod
    def validate_folder_stats(commcell_object, db_path, data_source_name, index_server_name):
        """Verifies if all the folder related data is pushed to solr and matches with the records in DB

        Args:
            commcell_object         (object)    --  commcell object
            db_path                 (str)       --  database file path
            data_source_name        (str)       --  datacube datasource name
            index_server_name       (str)       --  index server name where folder stats are pushed

        Return:
            True if data is valid and matches with the DB value
            False if data is not valid

        """
        log = logger.get_log()
        data_source_obj = commcell_object.datacube.datasources.get(data_source_name)
        core_name = data_source_obj.computed_core_name
        index_server_obj = commcell_object.index_servers.get(index_server_name)
        total_rows = ActivateUtils.db_get_folder_stats_count(db_path)
        solr_response = int(index_server_obj.execute_solr_query(core_name=core_name,
                                                                select_dict=QUERY_FOLDER_CRITERIA)
                            [RESPONSE_PARAM][NUM_FOUND_PARAM])
        if total_rows != solr_response:
            log.info("Folders count in DB and Solr are not a match")
            return False
        log.info("Folders count in DB and Solr are matched successfully")
        attr_list = [URL_PARAM, DOCUMENT_TYPE_PARAM, FOLDER_SIZE_PARAM, FILES_COUNT_PARAM,
                     FOLDERS_COUNT_PARAM, ACCESS_TIME_PARAM]
        op_params = {ROWS_PARAM: solr_response}
        solr_response = index_server_obj.execute_solr_query(
            core_name=core_name,
            attr_list=set(attr_list),
            select_dict=QUERY_FOLDER_CRITERIA,
            op_params=op_params
        )[RESPONSE_PARAM][DOCS_PARAM]
        for solr_item in solr_response:
            try:
                folder_url = solr_item[URL_PARAM]
                folders_count = int(solr_item[FOLDERS_COUNT_PARAM])
                files_count = int(solr_item[FILES_COUNT_PARAM])
                folder_size = solr_item[FOLDER_SIZE_PARAM]
                access_time = solr_item[ACCESS_TIME_PARAM]
                log.info(f"Checking entities for folder : {folder_url}")
                folders_count_db = ActivateUtils.db_get_folders_count(folder_url, db_path)
                files_count_db = ActivateUtils.db_get_files_count(folder_url, db_path)
                folder_size_db = ActivateUtils.db_get_folder_size(folder_url, db_path)
                access_time_db = ActivateUtils.db_get_access_time(folder_url, db_path)
                access_time_db_object = parser.isoparse(access_time_db)
                access_time_object = parser.isoparse(access_time)
                delay_in_seconds = abs((access_time_object - access_time_db_object).total_seconds())
                if folders_count != folders_count_db or files_count != files_count_db \
                        or folder_size != folder_size_db or delay_in_seconds >= 2:
                    log.info(f"Some entities failed to match for folder :{folder_url}")
                    log.info(f"Entities in Solr :\nFolder Count : {folders_count}\nFolder Size : {folder_size}"
                             f"\nFile Count : {files_count}\nAccess Time : {access_time}")
                    log.info(f"Entities in DB :\nFolder Count : {folders_count_db}"
                             f"\nFolder Size : {folder_size_db}\nFile Count : {files_count_db}"
                             f"\nAccess Time : {access_time_db}")
                    return False
            except KeyError:
                return False
        return True

    def create_subclients(self, client_name, number_of_subclients, number_of_files_per_subclient, storage_policy_name,
                          delete_generated_data=True):
        """Creates test data and uses that as content to create the required number of subclients in defaultBackupSet
         for File System IDA for a given client

         Args -
            client_name                    (str) : The name of the client where the subclients have to be created.
            number_of_subclients           (int) : The number of subclients to be created
            number_of_files_per_subclient  (int) : The number of files to be generated as content for each subclient.
            storage_policy_name            (str) : The storage policy name to be associated with the subclient(s).
            delete_generated_data          (Bool): Deletes the dummy data generated in the function.
                                                    Default : True

        Returns -
                subclients_list (List)   : List of names of all the subclients created
                backupset_obj   (Object) : The object of the default backupset.
         """

        client_obj = self.commcell.clients.get(client_name)
        agent_obj = client_obj.agents.get("File System")
        backupset_obj = agent_obj.backupsets.get("defaultBackupSet")

        machine_obj = Machine(client_name, self.commcell)
        delimiter = "\\"
        if machine_obj.os_info.lower() == UNIX:
            delimiter = "/"
        options_obj = OptionsSelector(self.commcell)
        drive = options_obj.get_drive(machine_obj)
        data_paths = []
        timestamp = calendar.timegm(time.gmtime())
        data_source_helper_obj = DataSourceHelper(self.commcell)
        subclients_list = []
        job_list = []

        for subclient_num in range(number_of_subclients):
            subclient_name = f"subclient_{timestamp}_{subclient_num}"
            subclients_list.append(subclient_name)
            data_path = f"{drive}{timestamp}{delimiter}{subclient_num}"
            data_paths.append(data_path)
            self.log.info(f"Creating dummy data for {subclient_name} at location {data_path}")
            machine_obj.generate_test_data(file_path=data_path, dirs=1, files=number_of_files_per_subclient)

            subclient_obj = backupset_obj.subclients.add(subclient_name=subclient_name,
                                                         storage_policy=storage_policy_name)
            subclient_obj.content = [data_path]
            job_obj = subclient_obj.backup("Full")
            job_list.append(job_obj.job_id)

        for job_id in job_list:
            data_source_helper_obj.monitor_crawl_job(job_id)

        if delete_generated_data:
            self.log.info("Deleting the generated data")
            for data_path in data_paths:
                machine_obj.remove_directory(data_path)

        return subclients_list, backupset_obj

    @staticmethod
    def is_index_import_job(commcell_object, job_id):
        """Checks whether the Job was an index import job

            Args:
                commcell_object     (object)    -   commcell class object
                job_id              (int)   -   Job ID of the job to be checked

        """
        job_details = commcell_object.job_controller.get(job_id)
        return job_details.job_type == INDEX_IMPORT_JOB_TYPE
