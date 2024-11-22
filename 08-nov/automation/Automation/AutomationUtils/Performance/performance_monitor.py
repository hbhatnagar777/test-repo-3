# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""This file contains functions for monitoring performance stats of process/client for the given job

    PerformanceMonitor:

        __init__()                          --  Initialize the PerformanceMonitor class object

        start_monitor()                     --  starts the performance monitor for the given job id and configurations

        push_configurations()               --  pushes the required configuration files to clients

        cleanup_configurations()            --  clean ups the configuration files on clients

        get_config_file_path()              --  forms the config file path for the given counters

        monitor_thread()                    --  Thread which is used to monitor the commvault process on client
                                                                                        for performance

        get_thread_name()                   --  forms the thread name based on config data

        kill_thread_and_get_stats()         --  kills the monitor process on client machine and get output stats file

        push_stats_thread()                 --  pushes the performance stats csv file data to the open data source

        check_and_kill_threads()            --  Kills all the child threads invoked for monitoring process

        create_performance_data_source()    --  creates the pre-defined data sources for pushing performance stats

        get_data_from_csv()                 --  converts csv performance file output to list of key value pairs(dict)

        push_hwinfo_to_data_source()        --  pushes the machine hardware details to the open data source

        fetch_job_details()                 --  fetches the job details for the given job object

        push_jobinfo_to_data_source         --  pushes job details to the open data source

        check_and_log_exception()           --  cross check exception and logs accordingly

        check_alive_threads()               --  checks the live threads running for monitoring the performance and
                                                                removes non-alive threads

        run_cmd_timer()                     --  executes the command provided on remote client with specified time

        push_netstat_to_data_source()       --  pushes netstat output of process/machine to the open data source

        get_valid_datetime()                --  returns the valid datetime format to push into data source

"""
import time
import os
import copy
import threading
import datetime
import json
from queue import Queue
from cvpysdk.job import Job
from cvpysdk.datacube.sedstype import SEDS_TYPE_DICT

from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils import constants as dynamic_constants
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils.config import get_config
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from AutomationUtils.Performance.Utils.constants import CounterTypes
from AutomationUtils.Performance.Utils.constants import Platforms
from AutomationUtils.Performance.Utils.constants import TimerIntervals
from AutomationUtils.Performance.Utils.constants import JobStatus
from AutomationUtils.Performance.Utils.constants import JobTypes
from AutomationUtils.Performance.Utils.constants import Binary
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from AutomationUtils.Performance.Utils.performance_helper import AutomationCache


_CONFIG_DATA = get_config().DynamicIndex.PerformanceStats


class PerformanceMonitor():
    """ contains functions for monitoring cv process performance stats for the given job configurations"""

    def __init__(self, commcell_object, build_id):
        """ Initialize the PerformanceMonitor class

            Args:

                commcell_object         (obj)       --      commcell object

                build_id                (str)       --      build id for this run

        """
        self.job_id = None
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.build_id = build_id
        self.stop_threads = False
        # for storing thread object of each monitor threads
        self.threads = []
        # for storing timer tasks last execution time
        self.timer_task = {}
        self.queue = Queue()
        self.counter_queue = Queue()
        self.error = False
        self.error_msg = None
        self.perf_helper = PerformanceHelper(self.commcell)
        self.cache_obj = AutomationCache()
        # folder paths
        self.reports_path = os.path.join(
            GeneralConstants.CONTROLLER_FOLDER_PATH,
            self.build_id,
            GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME)
        if not os.path.exists(self.reports_path):
            os.makedirs(self.reports_path)
        self.machine_config_file_path = os.path.join(
            self.reports_path, GeneralConstants.CONTROLLER_MACHINE_CONFIG_JSON_FILE_NAME)
        self.job_config_file_path = os.path.join(self.reports_path,
                                                 GeneralConstants.CONTROLLER_PERFORMANCE_CONFIG_JSON_FILE_NAME)
        self.job_details_file_path = os.path.join(self.reports_path,
                                                  GeneralConstants.CONTROLLER_PERFORMANCE_JOB_DETAILS_JSON_FILE_NAME)

    def get_valid_datetime(self, input):
        """returns the valid datetime format to push into data source

            Args:

                input           (str)           --  Date time string
                                            Example: 10/14/2020 18:05:12.019
                                            Pattern: dd/mm/yy hh:mm:ss.SSS

            Returns:

                str - DateTime format of pattern 'YYYY-MM-dd HH:MM:SS'

        """
        return datetime.datetime.strptime(input, '%m/%d/%Y %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')

    def push_netstat_to_data_source(self, machine_obj, client_name, binary, process_id, push_to_data_source):
        """

        Args:

            machine_obj          (obj)       --      Machine class object

            client_name          (str)       --      client name

            process_id           (list)      --      Process id

            binary               (str)       --      Process binary name

            push_to_data_source  (bool)      --      bool to specify whether to push this stats to data source or not

        Returns:

            None

        """
        try:
            stats = []
            default_param = {
                GeneralConstants.COLUMN_BUILD_ID: self.build_id,
                GeneralConstants.COLUMN_COMMSERV_VERSION: self.commcell.version,
                GeneralConstants.COLUMN_MACHINE_NAME: client_name
            }
            ds_obj = None
            # Process level netstat
            if len(process_id) > 0:
                process_dict = copy.deepcopy(default_param)
                if push_to_data_source:
                    ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Process_Data_Source_Name)
                for process in process_id:
                    process_dict[GeneralConstants.COLUMN_BINARY] = binary
                    process_dict[GeneralConstants.COLUMN_PROCESS_ID] = process
                    netstat = machine_obj.get_port_usage(process_id=process)
                    self.log.info(f"Port usage for binary : {binary} , Process id : {process} "
                                  f"in client : {client_name} = {netstat}")
                    # Modify field value to _i at end so that it get pushed as integer to solr
                    netstat = {
                        f"{key}{GeneralConstants.SOLR_INTEGER_FIELD_SUFFIX}": val for key,
                        val in netstat.items()}
                    netstat.update(process_dict)
                    stats.append(netstat)
            # machine level netstat
            else:
                if push_to_data_source:
                    ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Machine_Data_Source_Name)
                netstat = machine_obj.get_port_usage()
                # Modify field value to _i at end so that it get pushed as integer to solr
                netstat = {f"{key}{GeneralConstants.SOLR_INTEGER_FIELD_SUFFIX}": val for key, val in netstat.items()}
                self.log.info(f"Port usage for Machine : {client_name} = {netstat}")
                netstat.update(default_param)
                stats.append(netstat)

            if push_to_data_source and ds_obj is not None:
                ds_obj.import_data(data=stats)
                self.log.info(f"Netstats pushed to data source successfully for client : {client_name} "
                              f"& binary : {binary}")

        except Exception as exp:
            self.check_and_log_exception(exp=exp)

    def run_cmd_timer(self, machine_obj, cmd):
        """ runs command on machine and comes out without waiting for output

        Args:

            machine_obj                 (obj)       --      Machine class object

            cmd                         (str)       --      command which needs to be executed

        Returns:

            None

        """
        machine_obj.execute_command(command=cmd)

    def check_alive_threads(self, threads):
        """ prints the alive threads in logs and removes dead one from list
        Args:

            threads         (list)      --  list of thread objects

        Returns:

            None

        """
        total_count = len(threads)
        if len(threads) > 0:
            for _thread in threads:
                if not _thread.is_alive():
                    self.log.info(f"Thread [{_thread.getName()}] is not alive")
                    threads.remove(_thread)
                    self.log.info(f"Removed Thread from stack : {_thread.getName()}")
            self.log.info(f"Expected Threads running count : {total_count}"
                          f" Current Running Thread count - {len(threads)}"
                          f" Running thread names : {threads}")

    def check_and_log_exception(self, exp, ignore_list=None):
        """cross check exception and logs accordingly

        Args:

                exp         (obj)       --      exception object

                ignore_list (list)      --      list of additional errors which can be ignored specifically

        Returns:

                None

        """
        log_error = True
        # ignore if it is remote connection related errors
        for ignore_err in GeneralConstants.IGNORE_REMOTE_ERRORS:
            if ignore_err in repr(exp):
                self.log.error(GeneralConstants.IGNORE_EXCEPTION)
                log_error = False
        # check for any specific error conditions which need to be ignored
        if ignore_list is not None:
            for specific_error in ignore_list:
                if specific_error in repr(exp):
                    self.log.error(f"{GeneralConstants.IGNORE_SPECIFIC_EXCEPTIONS}{specific_error}")
                    log_error = False

        if log_error:
            self.log.exception(exp)
            time.sleep(30)

    def push_jobinfo_to_data_source(self):
        """pushes job details to the open data source

        Args:
            None

        Returns:

            None

        Raises:

            Exceptions:

                if failed to fetch job/Data Source details

                if failed to push to open data source

        """
        if not os.path.exists(self.job_details_file_path):
            raise Exception(f"Job details Json file not found @ {self.job_details_file_path}")
        job_details = self.perf_helper.read_json_file(json_file=self.job_details_file_path)
        self.log.info(f"Loaded job details JSON file in memory")
        self.log.info(f"Job Details JSON : {job_details}")
        # handle json to string here for pushing into solr
        if GeneralConstants.COLUMN_JOB_EVENTS in job_details:
            self.log.info(f"Stringify the job events before pushing to open data source")
            job_details[GeneralConstants.COLUMN_JOB_EVENTS] = str(job_details[GeneralConstants.COLUMN_JOB_EVENTS])
        if GeneralConstants.COLUMN_JOB_CONFIG in job_details:
            self.log.info(f"Stringify the job config before pushing to open data source")
            job_details[GeneralConstants.COLUMN_JOB_CONFIG] = str(job_details[GeneralConstants.COLUMN_JOB_CONFIG])
        if dynamic_constants.FIELD_EXTRACT_DURATION in job_details:
            self.log.info(f"Stringify the Extract Duration before pushing to open data source")
            job_details[dynamic_constants.FIELD_EXTRACT_DURATION] = str(
                job_details[dynamic_constants.FIELD_EXTRACT_DURATION])
        job_ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Job_Details_Data_Source_Name)
        final_data = [job_details]
        job_ds_obj.import_data(data=final_data)
        self.log.info(f"Job details successfully pushed into open Data Source")

    def fetch_job_details(self, job_obj, job_type, **kwargs):
        """ fetches the job details for the given job object and job type

        Args:

            job_obj             (obj)       --  object of Job class

            job_type            (int)       --      type of job
                                            Example : defined in JobTypes in constants.py

                    **kwargs    --  optional params

                    DataSourceName  --  Name of the data source used in crawl job

                    ClientId        --  client id of data which got analysed in crawl job

                    SourceName_s    --  Name of the source data

                    SourceSize_s    --  Size of the source data


        Returns:

            dict        --  containing details about job

        Raises:

            Exception:

                    if input is not valid

        """
        if not isinstance(job_obj, Job):
            raise Exception("Input data type is not valid")
        task_done = False
        output = {}
        on_error = 0
        while not task_done:
            try:
                self.log.info(f"Going to fetch job details for the job id : {job_obj.job_id}")
                start = datetime.datetime.fromtimestamp(job_obj.start_timestamp)
                end = datetime.datetime.fromtimestamp(job_obj.end_timestamp)
                output = {
                    GeneralConstants.COLUMN_JOB_ID: int(job_obj.job_id),
                    GeneralConstants.COLUMN_JOB_STATUS: job_obj.status,
                    GeneralConstants.COLUMN_JOB_START: job_obj.start_timestamp,
                    GeneralConstants.COLUMN_JOB_END: job_obj.end_timestamp,
                    GeneralConstants.COLUMN_JOB_TYPE: job_obj.job_type,
                    GeneralConstants.COLUMN_JOB_EVENTS: job_obj.get_events(),
                    GeneralConstants.COLUMN_JOB_DURATION: int(float((end - start).total_seconds() / 60)),
                    GeneralConstants.COLUMN_COMMSERV_VERSION: self.commcell.version,
                    GeneralConstants.COLUMN_BUILD_ID: self.build_id,
                    GeneralConstants.COLUMN_JOB_CONFIG: str(self.perf_helper.read_json_file(
                        json_file=self.job_config_file_path))
                }
                task_done = True
            except Exception as exp:
                self.check_and_log_exception(exp=exp)
                on_error = on_error + 1
                if on_error > GeneralConstants.JOB_DETAILS_FETCH_THRESHOLD:
                    raise Exception(GeneralConstants.ERROR_JOB_DETAILS_FETCH_FAILED)
                continue
            # check whether input job type has associated data source or not. if so, collect data source details
            if job_type in JobTypes.DATA_SOURCE_SUPPORTED_JOB_TYPES:
                self.log.info(f"Data Source associated job. Proceed to get the data source stats")
                if not kwargs.get(GeneralConstants.DATA_SOURCE_NAME_PARAM):
                    raise Exception(f"DataSource name not found in Param")
                client_id = None
                if kwargs.get(GeneralConstants.COLUMN_CLIENT_ID):
                    client_id = kwargs.get(GeneralConstants.COLUMN_CLIENT_ID)
                ds_details = self.perf_helper.fetch_data_source_crawl_stats(
                    data_source_name=kwargs.get(GeneralConstants.DATA_SOURCE_NAME_PARAM),
                    client_id=client_id)
                ds_details[GeneralConstants.DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE] = job_type
                ds_details[GeneralConstants.COLUMN_DS_NAME] = kwargs.get(GeneralConstants.DATA_SOURCE_NAME_PARAM)
                if kwargs.get(GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME):
                    ds_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME] = kwargs.get(
                        GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME)
                else:
                    ds_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME] = "Default Source"
                if kwargs.get(GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE):
                    ds_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE] = kwargs.get(
                        GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE)
                else:
                    ds_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE] = 0
                ds_obj = self.commcell.datacube.datasources.get(kwargs.get(GeneralConstants.DATA_SOURCE_NAME_PARAM))
                self.log.info(f"DataSource Type : {ds_obj.data_source_type}")
                if str(ds_obj.data_source_type) == SEDS_TYPE_DICT[int(dynamic_constants.FILE_SYSTEM_DSTYPE)] and \
                        job_type in JobTypes.CONTENT_CRAWLS:
                    self.log.info(f"File system data source with content analysed found for stats analysis")
                    stats = self.perf_helper.find_fs_extract_duration_stats(
                        data_source_name=kwargs.get(GeneralConstants.DATA_SOURCE_NAME_PARAM))
                    ds_details[dynamic_constants.FIELD_EXTRACT_DURATION] = stats
                # append all data source details to above job details dict
                output.update(ds_details)
        return output

    def push_hwinfo_to_data_source(self, config_json_file):
        """pushes the machine hardware details to the open data source from input JSON file

        Args:

            config_json_file            (str)       --  JSON file containing machine hardware details

        Returns:

            None

        Raises:

            Exceptions:

                    if config json file doesn't exists

                    if failed to push data to open data source

        """
        self.log.info(f"Going to push machine configuration/Hardware details to the open data source")
        if not os.path.exists(config_json_file):
            raise Exception(f"Machine config file doesn't exists - {config_json_file}")
        with open(config_json_file) as file_json:
            json_data = json.load(file_json)
        self.log.info(f"Successfully fetched machine config details from Json file")
        push_list = []
        for client in json_data:
            # Remove GB letter from RAM size
            json_data[client][GeneralConstants.COLUMN_BUILD_ID] = self.build_id
            json_data[client][GeneralConstants.COLUMN_COMMSERV_VERSION] = self.commcell.version
            if GeneralConstants.COLUMN_RAM_SIZE in json_data[client]:
                json_data[client][GeneralConstants.COLUMN_RAM_SIZE] = \
                    int(float(json_data[client][GeneralConstants.COLUMN_RAM_SIZE].replace("GB", "")))
            if GeneralConstants.COLUMN_STORAGE in json_data[client]:
                json_data[client][GeneralConstants.COLUMN_STORAGE] = str(
                    json_data[client][GeneralConstants.COLUMN_STORAGE])
            push_list.append(json_data[client])
            self.log.info(f"Client-{client} Hardware config - {json_data[client]}")
        # push it to machine config open data source
        ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Machine_Config_Data_Source_Name)
        ds_obj.import_data(data=push_list)

    def get_data_from_csv(self, push_json):
        """converts the csv performance file output to list of key value pairs(dict)

        Args:

            push_json       (dict)  --  containing information about performance config of process

                                            Example : {
                                                        "binary":"ifind.exe",
                                                        "countertype" :"Process",
                                                        "binaryprocessids":['123'],
                                                        "statsfile":"c:\test.csv",
                                                        "counters" [r'\Process(cvd*)\Handle Count'],
                                                        "client":"xyz",
                                                        "platform" : "Windows"
                                                        }

        Returns:

            list        --  list of dict containing key-value pairs which needs to be pushed to data source
        """
        import csv
        output_list = []
        client_name = push_json[GeneralConstants.CLIENT_PARAM]
        counter_type = push_json[GeneralConstants.COUNTER_TYPE_PARAM]
        platform = push_json[GeneralConstants.PLATFORM_PARAM]
        stats_csv_file = push_json[GeneralConstants.STATS_FILE_PARAM]
        counters = push_json[GeneralConstants.COUNTERS_PARAM]
        csv_file = open(stats_csv_file, GeneralConstants.FILE_READ_MODE)
        csv_reader = csv.reader(csv_file)
        headers = next(csv_reader)
        header_length = len(headers)
        # counter to solr field mappings
        map_fields = []
        for column in headers:
            if column.startswith(GeneralConstants.TYPEPERF_TIME_STAMP_HEADER):
                map_fields.append(
                    GeneralConstants.COUNTERS_FIELD_MAPPING[GeneralConstants.TYPEPERF_TIME_STAMP_HEADER])
            elif column.startswith(GeneralConstants.BASH_TIME_STAMP_HEADER):
                map_fields.append(
                    GeneralConstants.COUNTERS_FIELD_MAPPING[GeneralConstants.BASH_TIME_STAMP_HEADER])
            else:
                header_name = column
                if platform == Platforms.Windows:
                    header_name = column.split("\\")[-1]  # windows counters
                else:
                    if counter_type == CounterTypes.PROCESS_COUNTER:
                        header_name = column.split("_")[-2]  # linux counters
                if GeneralConstants.COUNTERS_FIELD_MAPPING[header_name] not in map_fields:
                    map_fields.append(GeneralConstants.COUNTERS_FIELD_MAPPING[header_name])
        self.log.info(f"Mapped Solr fields for file : {stats_csv_file} is : {map_fields}")
        if counter_type == CounterTypes.PROCESS_COUNTER:
            self.log.info(f"Got Process level stats for pushing into data source")
            binary_name = push_json[GeneralConstants.BINARY_PARAM]
            # find type of output CSV file. single/multi process output csv
            if len(counters) + 1 == header_length:  # CSV file will have time column as extra at front
                # for single process file, read all column and rows directly.
                self.log.info(f"Single Process performance stats file {stats_csv_file} with total "
                              f"columns : {header_length}. Read and push directly")
                skipped_rows = 0
                for row in csv_reader:
                    row_data = {}
                    zero_skip = False
                    row_data[GeneralConstants.COLUMN_BUILD_ID] = self.build_id
                    row_data[GeneralConstants.COLUMN_BINARY] = binary_name
                    row_data[GeneralConstants.COLUMN_COMMSERV_VERSION] = self.commcell.version
                    row_data[GeneralConstants.COLUMN_PLATFORM] = platform.lower()
                    row_data[GeneralConstants.COLUMN_MACHINE_NAME] = client_name
                    index = 0
                    for field in map_fields:
                        # add time field always
                        if field == GeneralConstants.COLUMN_TIME:
                            if platform.lower() == Platforms.Windows.lower():
                                value = self.get_valid_datetime(input=row[index])
                            else:
                                value = row[index]
                        elif row[index].strip() != '' and row[index] is not None and float(row[index]) != 0:
                            value = row[index]
                        else:
                            # sometimes counter value can come as zero. so add logic to skip those
                            value = "0"
                            zero_skip = GeneralConstants.ZERO_VALUE_ROWS_SKIP
                        row_data[field] = value
                        index = index + 1
                    if not zero_skip:
                        output_list.append(row_data)
                    else:
                        skipped_rows = skipped_rows + 1
                self.log.info(f"Total skipped rows of Zero condition - {skipped_rows}")
            else:
                # minus the time header column from header length
                process_count = int((header_length - 1) / len(counters))
                # for multiple process stats output file from windows, drop the ones which is not needed based on pid
                # Time,Handle count,Handle Count,Threads count,Threads count,pid,pid
                # t1,453,345,12,45,43456,23765
                # t2,453,545,12,55,43456,23765
                self.log.info(
                    f"Multiple Process performance stats file {stats_csv_file} with total "
                    f"columns : {header_length}. Read and push accordingly assuming total process as : {process_count}")
                is_skipped = False
                unknown_pids = set()
                skipped_rows = 0
                for row in csv_reader:
                    for process_index in range(1, process_count + 1):
                        row_data = {}
                        zero_skip = False
                        row_data[GeneralConstants.COLUMN_BUILD_ID] = self.build_id
                        row_data[GeneralConstants.COLUMN_BINARY] = binary_name
                        row_data[GeneralConstants.COLUMN_COMMSERV_VERSION] = self.commcell.version
                        row_data[GeneralConstants.COLUMN_PLATFORM] = platform.lower()
                        row_data[GeneralConstants.COLUMN_MACHINE_NAME] = client_name
                        index = 0
                        for field in map_fields:
                            # add time field always
                            if field == GeneralConstants.COLUMN_TIME:
                                if platform.lower() == Platforms.Windows.lower():
                                    value = self.get_valid_datetime(input=row[index])
                                else:
                                    value = row[index]
                            elif row[index].strip() != '' and row[index] is not None and float(row[index]) != 0:
                                value = row[index]
                            else:
                                # sometimes counter value can come as zero. so add logic to skip those
                                value = "0"
                                zero_skip = GeneralConstants.ZERO_VALUE_ROWS_SKIP
                            row_data[field] = value
                            if index == 0:
                                index = index + process_index
                            else:
                                index = index + process_count
                        # check whether this process id is the one which we monitored. if not, drop this
                        if row_data[GeneralConstants.COLUMN_PROCESS_ID] in push_json[GeneralConstants.BINARY_PID_PARAM]:
                            if not zero_skip:
                                output_list.append(row_data)
                            else:
                                skipped_rows = skipped_rows + 1
                        else:
                            # Multiple instance of same binary running on client. Drop the ones which are not
                            # related to this configurations and print it for logging purpose
                            is_skipped = True
                            unknown_pids.add(row_data[GeneralConstants.COLUMN_PROCESS_ID])
                if is_skipped:
                    self.log.info(
                        f"DataSource Push -> Dropping this Unwanted PID {unknown_pids} "
                        f"from binary : {binary_name}"
                        f" for the client : {client_name}. Data will not be pushed to open data source")
                self.log.info(f"Total skipped rows of Zero condition - {skipped_rows}")
        else:
            self.log.info(f"Got Machine level stats for pushing into data source")
            skipped_rows = 0
            for row in csv_reader:
                row_data = {}
                zero_skip = False
                row_data[GeneralConstants.COLUMN_BUILD_ID] = self.build_id
                row_data[GeneralConstants.COLUMN_MACHINE_NAME] = client_name
                row_data[GeneralConstants.COLUMN_COMMSERV_VERSION] = self.commcell.version
                row_data[GeneralConstants.COLUMN_PLATFORM] = platform.lower()
                index = 0
                for field in map_fields:
                    # add time field always
                    if field == GeneralConstants.COLUMN_TIME:
                        if platform.lower() == Platforms.Windows.lower():
                            row_data[field] = self.get_valid_datetime(input=row[index])
                        else:
                            row_data[field] = row[index]
                    elif row[index].strip() != '' and row[index] is not None and float(row[index]) != 0:
                        row_data[field] = row[index]
                    else:
                        # sometimes counter value can come as zero. so add logic to skip those
                        row_data[field] = "0"
                        zero_skip = GeneralConstants.ZERO_VALUE_ROWS_SKIP
                    index = index + 1
                if not zero_skip:
                    output_list.append(row_data)
                else:
                    skipped_rows = skipped_rows + 1
            self.log.info(f"Total skipped rows of Zero condition - {skipped_rows}")
        return output_list

    def create_performance_data_source(self):
        """ creates the pre-defined data sources for pushing performance stats
        Args:

            None

        Returns:

            None

        """
        # check whether index server has DS role enabled. if not, enable and then proceed creating open data source
        self.log.info(f"Index Server to be used for pushing performance stats : {_CONFIG_DATA.Index_Server}")
        if not self.commcell.datacube.datasources.has_datasource(GeneralConstants.Process_Data_Source_Name) or not \
                self.commcell.datacube.datasources.has_datasource(GeneralConstants.Machine_Data_Source_Name) or not\
                self.commcell.datacube.datasources.has_datasource(GeneralConstants.Machine_Config_Data_Source_Name) or\
                not self.commcell.datacube.datasources.has_datasource(GeneralConstants.Job_Details_Data_Source_Name):
            index_server_helper = IndexServerHelper(self.commcell, _CONFIG_DATA.Index_Server)
            ds_helper = DataSourceHelper(self.commcell)
            self.log.info("Index server/Data Source helper initialised")
            index_server_helper.update_roles(index_server_roles=[GeneralConstants.ROLE_DATA_ANALYTICS])
            if not self.commcell.datacube.datasources.has_datasource(GeneralConstants.Process_Data_Source_Name):
                self.log.info(
                    f"Going to create Process level - Open DataSource : {GeneralConstants.Process_Data_Source_Name}")
                ds_helper.create_open_data_source(
                    data_source_name=GeneralConstants.Process_Data_Source_Name,
                    index_server_name=_CONFIG_DATA.Index_Server)
                ds_helper.update_data_source_schema(data_source_name=GeneralConstants.Process_Data_Source_Name,
                                                    field_name=GeneralConstants.PROCESS_DATA_SOURCE_COLUMN,
                                                    field_type=GeneralConstants.PROCESS_DATA_SOURCE_COLUMN_TYPES,
                                                    schema_field=dynamic_constants.SCHEMA_FIELDS)
                self.log.info(f"Process level - Open DataSource created successfully")

            if not self.commcell.datacube.datasources.has_datasource(GeneralConstants.Machine_Data_Source_Name):
                self.log.info(
                    f"Going to create Machine level - Open DataSource : {GeneralConstants.Machine_Data_Source_Name}")
                ds_helper.create_open_data_source(
                    data_source_name=GeneralConstants.Machine_Data_Source_Name,
                    index_server_name=_CONFIG_DATA.Index_Server)
                ds_helper.update_data_source_schema(data_source_name=GeneralConstants.Machine_Data_Source_Name,
                                                    field_name=GeneralConstants.MACHINE_DATA_SOURCE_COLUMN,
                                                    field_type=GeneralConstants.MACHINE_DATA_SOURCE_COLUMN_TYPES,
                                                    schema_field=dynamic_constants.SCHEMA_FIELDS)
                self.log.info(f"Machine level - Open DataSource created successfully")

            if not self.commcell.datacube.datasources.has_datasource(GeneralConstants.Machine_Config_Data_Source_Name):
                self.log.info(
                    f"Going to create Machine Config level - Open DataSource : "
                    f"{GeneralConstants.Machine_Config_Data_Source_Name}")
                ds_helper.create_open_data_source(
                    data_source_name=GeneralConstants.Machine_Config_Data_Source_Name,
                    index_server_name=_CONFIG_DATA.Index_Server)
                ds_helper.update_data_source_schema(data_source_name=GeneralConstants.Machine_Config_Data_Source_Name,
                                                    field_name=GeneralConstants.MACHINE_CONFIG_DATA_SOURCE_COLUMN,
                                                    field_type=GeneralConstants.MACHINE_CONFIG_DATA_SOURCE_COLUMN_TYPES,
                                                    schema_field=dynamic_constants.SCHEMA_FIELDS)
                self.log.info(f"Machine Config level - Open DataSource created successfully")

            if not self.commcell.datacube.datasources.has_datasource(GeneralConstants.Job_Details_Data_Source_Name):
                self.log.info(
                    f"Going to create Job Details - Open DataSource : {GeneralConstants.Job_Details_Data_Source_Name}")
                ds_helper.create_open_data_source(
                    data_source_name=GeneralConstants.Job_Details_Data_Source_Name,
                    index_server_name=_CONFIG_DATA.Index_Server)
                ds_helper.update_data_source_schema(data_source_name=GeneralConstants.Job_Details_Data_Source_Name,
                                                    field_name=GeneralConstants.JOB_DETAILS_DATA_SOURCE_COLUMN,
                                                    field_type=GeneralConstants.JOB_DETAILS_DATA_SOURCE_COLUMN_TYPES,
                                                    schema_field=dynamic_constants.SCHEMA_FIELDS)
                self.log.info(f"Job Details - Open DataSource created successfully")

        self.log.info("Open DataSource setup completed successfully")

    def check_and_kill_threads(self, threads):
        """Checks whether thread object exists in given list and then Kills the threads

            Args:

                threads     (list)      --  list of thread objects to be killed

            Returns:

                None

        """
        if len(threads) > 0:
            self.log.info(f"Killing all child threads running - {len(threads)}")
            self.check_alive_threads(threads=threads)
            # set stop flag to true so that all child threads will be notified
            self.stop_threads = True
            self.log.info(f"Setting Stop flag to : {self.stop_threads}")
            for _thread in threads:
                # join and wait for graceful exit of child thread
                self.log.info("Executing Join for thread : %s", _thread)
                _thread.join()
                self.log.info(f"{_thread.getName()} stopped gracefully")
                # thread came down gracefully. remove thread object from the list
                threads.remove(_thread)
                self.log.info(f"Removed Thread from stack : {_thread.getName()}")
            while len(threads) > 0:
                self.check_alive_threads(threads=threads)
                self.log.info("Waiting for all threads to go down!!!")
                time.sleep(30)
            # reset stop flag
            self.stop_threads = False
            self.log.info(f"Reset stop flag to : {self.stop_threads}")
            self.log.info(f"All child threads went down")
        else:
            self.log.info(f"No child threads are running")

    def get_config_file_path(self, config, separator, folder_only=False):
        """forms the config file path for the given counters

        Args:

            config     (dict)      --  dict containing performance monitor config data for a process/Machine

                    Example : {
                    'client': 'xyz',
                    'binary': {'Windows': 'IFind.exe'},
                    'counters': ['$5', '$7'],
                    'platform': 'UNIX',
                    'statsfolder': '/Users/root/commvault_automation/Automation_Performance_Data'}
                                }

            separator   (str)   --  OS specific Separator

            folder_only (bool)  --  returns only the folder level path for the given config

        Returns:

            str     --  Config file path

        """
        binary_name = config[GeneralConstants.BINARY_PARAM]
        if separator == "\\" and isinstance(binary_name, dict) and Platforms.Windows in binary_name:
            binary_name = binary_name[Platforms.Windows].replace(".", "_")
        elif isinstance(binary_name, dict) and Platforms.Unix in binary_name:
            binary_name = binary_name[Platforms.Unix].replace(".", "_")
        else:
            binary_name = binary_name.replace(".", "_")
        folder_path = f"{config[GeneralConstants.STATS_FOLDER_PARAM]}{separator}{self.build_id}{separator}{binary_name}"
        client_name = config[GeneralConstants.CLIENT_PARAM]

        if folder_only:
            return f"{folder_path}"
        if separator == "\\":  # return windows config file
            return f"{folder_path}{separator}{client_name}_{binary_name}{GeneralConstants.COUNTERS_TEXT_FILE}"

        # returns unix bash file
        return f"{folder_path}{separator}{client_name}_{binary_name}{GeneralConstants.COUNTERS_BASH_FILE}"

    def cleanup_configurations(self, config_data):
        """ cleanups the configurations files on client machines based on given config

        Args:

            config_data     (dict)      --  performance Monitor config data

            Example : {
                        'Live Scan': {
                                        '1': {
                                                'client': 'xyz',
                                                'binary': {'Windows': 'IFind.exe'},
                                                'counters': ['\\Process(%s*)\\Handle Count'],
                                                'platform': 'UNIX',
                                                'statsfolder': '/Users/root/Automation_Performance_Data'
                                            }
                                    },
                        'Content Push': {
                                        '1': {
                                                'client': 'xyz',
                                                'binary': {'Windows': 'CLBackup.exe'},
                                                'counters': ['1', '5'],
                                                'platform': 'UNIX',
                                                'statsfolder': '/Users/Automation_Performance_Data'}
                                        }
                    }

        Returns:

            None

        Raises:

                Exception:

                        if failed to delete configurations


        """
        try:
            clean_up_clients = []
            for phase_dict in config_data:
                self.log.info(f"Going to cleanup configurations for phase : {phase_dict}")
                self.log.info(f"Phase Configuration got : {config_data[phase_dict]}")
                # check for duplicate configurations
                current_phase_config = self.perf_helper.remove_dup_configs(config=config_data[phase_dict])
                for config_no in range(1, len(current_phase_config) +
                                       1):  # length of dict + 1 as we starting with index 1
                    config_to_process = str(config_no)
                    config = current_phase_config[config_to_process]
                    self.perf_helper.print_config(config_data=config)
                    if not config:
                        self.log.info(f"Empty Dict @ config no - {config_no}. Proceed further")
                        continue
                    client_name = config[GeneralConstants.CLIENT_PARAM]
                    if client_name in clean_up_clients:
                        self.log.info(f"Already cleaned up for this client : {client_name}. Nothing to do")
                        continue
                    machine_obj = None
                    is_cvlt_client = False
                    if self.commcell.clients.has_client(client_name):
                        is_cvlt_client = True
                    client_key = f"{client_name}{GeneralConstants.MACHINE_OBJ_CACHE}"
                    if self.cache_obj.is_exists(key=client_key):
                        machine_obj = self.cache_obj.get_key(key=client_key)
                    else:
                        if is_cvlt_client:
                            self.log.info(f"It is a commvault client - {client_name}")
                            machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell)
                        else:
                            self.log.info(f"It is a Non-commvault client - {client_name}")
                            machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell,
                                                  username=config[GeneralConstants.USERNAME_PARAM],
                                                  password=config[GeneralConstants.PASSWORD_PARAM])
                        self.log.info(f"Initialised Machine object for client : {client_name}")
                        self.cache_obj.put_key(key=client_key, value=machine_obj)
                    folder_path = f"{config[GeneralConstants.STATS_FOLDER_PARAM]}{machine_obj.os_sep}" \
                                  f"{self.build_id}"
                    self.log.info(f"Going to delete folder path : {folder_path} on client : {client_name}")
                    machine_obj.remove_directory(directory_name=folder_path)
                    self.log.info(f"Deleted the folder!!!")
                    clean_up_clients.append(client_name)
            self.log.info(f"Going to cleanup stats folder - {GeneralConstants.CONTROLLER_FOLDER_PATH} on controller.")
            machine_obj = Machine()
            folder_list = machine_obj.get_folders_in_path(folder_path=GeneralConstants.CONTROLLER_FOLDER_PATH)
            for folder in folder_list:
                machine_obj.remove_directory(directory_name=folder,
                                             days=GeneralConstants.STATS_FILE_DELETE_DAYS)
            self.log.info(f"Deletion on controller finished!!!")
        except Exception as exp:
            self.check_and_log_exception(exp=exp)

    def push_configurations(self, config_data):
        """ Pushes the required configurations files to client machines based on given config

        Args:

            config_data     (dict)      --  performance Monitor config data

            Example : {
                        'Live Scan': {
                                        '1': {
                                                'client': 'xyz',
                                                'binary': {'Windows': 'IFind.exe'},
                                                'counters': ['\\Process(%s*)\\Handle Count'],
                                                'platform': 'UNIX',
                                                'statsfolder': '/Users/root/Automation_Performance_Data'
                                            }
                                    },
                        'Content Push': {
                                        '1': {
                                                'client': 'xyz',
                                                'binary': {'Windows': 'CLBackup.exe'},
                                                'counters': ['1', '5'],
                                                'platform': 'UNIX',
                                                'statsfolder': '/Users/Automation_Performance_Data'}
                                        }
                    }

        Returns:

            None

        Raises:

                Exception:

                        if failed to push configurations


        """
        push_finish = False
        attempt = 0
        clients_config = {}
        while not push_finish:
            try:
                for phase_dict in config_data:
                    self.log.info(f"Going to push configurations for phase : {phase_dict}")
                    self.log.info(f"Phase Configuration got : {config_data[phase_dict]}")
                    for config_no in range(1, len(config_data[phase_dict]) +
                                           1):  # length of dict + 1 as we starting with index 1
                        config_to_process = str(config_no)
                        config = config_data[phase_dict][config_to_process]
                        self.perf_helper.print_config(config_data=config)
                        if not config:
                            self.log.info(f"Empty Dict @ config no - {config_no}. Proceed further")
                            continue
                        client_name = config[GeneralConstants.CLIENT_PARAM]
                        binary_name = config[GeneralConstants.BINARY_PARAM]
                        counters = config[GeneralConstants.COUNTERS_PARAM]
                        platform = config[GeneralConstants.PLATFORM_PARAM]
                        machine_obj = None
                        client_key = f"{client_name}{GeneralConstants.MACHINE_OBJ_CACHE}"
                        is_cvlt_client = False
                        if self.commcell.clients.has_client(client_name):
                            is_cvlt_client = True
                        if self.cache_obj.is_exists(key=client_key):
                            machine_obj = self.cache_obj.get_key(key=client_key)
                        else:
                            if is_cvlt_client:
                                self.log.info(f"It is a commvault client - {client_name}")
                                machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell)
                            else:
                                self.log.info(f"It is a Non-commvault client - {client_name}")
                                machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell,
                                                      username=config[GeneralConstants.USERNAME_PARAM],
                                                      password=config[GeneralConstants.PASSWORD_PARAM])
                            self.log.info(f"Initialised Machine object for client : {client_name}")
                            self.cache_obj.put_key(key=client_key, value=machine_obj)
                        if client_name.lower() not in clients_config:
                            # fetch hardware details for this client
                            self.log.info(f"Now going to fetch hardware details for client : {client_name.lower()}")
                            hardware_details = machine_obj.get_hardware_info()
                            hardware_details[GeneralConstants.COLUMN_CLIENT_NAME] = client_name.lower()
                            drives_list = []
                            storage_details = machine_obj.get_storage_details()
                            for storage_detail in storage_details:
                                if isinstance(storage_details[storage_detail], dict):
                                    to_be_added = f"{storage_detail}:\\"
                                    if machine_obj.os_info.lower() == dynamic_constants.UNIX.lower():
                                        to_be_added = storage_details[storage_detail]['mountpoint']
                                    drives_list.append(to_be_added)
                            read_perf = []
                            write_perf = []
                            delete_perf = []
                            for drive in drives_list:
                                self.log.info(f"Getting CV disk performance reports for disk : "
                                              f"{drive} of {client_name.lower()}")
                                try:
                                    disk_perf_details = machine_obj.run_cvdiskperf(drive, stat=False)
                                    read_perf.append(f"{drive}  "
                                                     f"{disk_perf_details[GeneralConstants.KEY_THROUGHPUT_READ]} GB/hr")
                                    write_perf.append(f"{drive}  "
                                                      f"{disk_perf_details[GeneralConstants.KEY_THROUGHPUT_WRITE]} "
                                                      f"GB/hr")
                                    delete_perf.append(f"{drive}  "
                                                       f"{disk_perf_details[GeneralConstants.KEY_THROUGHPUT_DELETE]} "
                                                       f"GB/hr")
                                except Exception as e:
                                    self.log.info(f"CV disk perf failed for drive {drive}")
                                    self.log.info(e)
                            hardware_details[GeneralConstants.DYNAMIC_COLUMN_THROUGH_PUT_READ] = ",".join(read_perf)
                            hardware_details[GeneralConstants.DYNAMIC_COLUMN_THROUGH_PUT_WRITE] = ",".join(write_perf)
                            hardware_details[GeneralConstants.DYNAMIC_COLUMN_THROUGH_PUT_DELETE] = ",".join(delete_perf)
                            clients_config[client_name.lower()] = hardware_details
                            self.log.info(f"Fetched hardware details for the client - {client_name} successfully")
                        else:
                            self.log.info(
                                f"Hardware details for this client present already. client name - {client_name}")
                        folder_path = f"{config[GeneralConstants.STATS_FOLDER_PARAM]}{machine_obj.os_sep}" \
                                      f"{self.build_id}"

                        if not machine_obj.check_directory_exists(directory_path=folder_path):
                            self.log.info(f"Creating Folder - {folder_path}  on client - {client_name}")
                            machine_obj.create_directory(directory_name=folder_path)
                        config_file_path = self.get_config_file_path(config=config, separator=machine_obj.os_sep)
                        # For windows clients
                        if platform.lower() == Platforms.Windows.lower():
                            if isinstance(binary_name, dict):
                                binary_name = binary_name[Platforms.Windows]
                            self.log.info(f"Client is windows machine. Create typeperf config files on : {client_name}")
                            file_text = ''
                            for counter in counters:
                                if binary_name != CounterTypes.MACHINE_COUNTER:
                                    counter = counter.format(pname=str(binary_name))
                                counter = counter.replace(
                                    ".exe", "")  # Counter file don't need extension on process name
                                file_text = f"{file_text}{counter}{GeneralConstants.WINDOWS_NEW_LINE}"
                            file_text = file_text.rstrip(GeneralConstants.WINDOWS_NEW_LINE)
                            # create typeperf config file on destination remote client
                            machine_obj.create_file(file_path=config_file_path, content=file_text)
                            self.log.info(f"Config file got created successfully on windows client - {client_name}")
                            # update typeperf structure to print pid in header column
                            machine_obj.create_registry(key=GeneralConstants.PERFMON_REGISTRY,
                                                        value=GeneralConstants.PERFMON_HEADER_PID_REG_KEY,
                                                        data=GeneralConstants.PERFMON_HEADER_WITH_PID_ON,
                                                        reg_type=GeneralConstants.REGISTRY_DWORD)
                            self.log.info(f"Updated the PerfMon output header registry key to value : 2")
                        else:
                            if isinstance(binary_name, dict):
                                binary_name = binary_name[Platforms.Unix]
                            self.log.info(f"Client is Linux machine. Copy the bash script to client  : {client_name}")
                            config_folder = self.get_config_file_path(
                                config=config, separator=machine_obj.os_sep, folder_only=True)
                            if binary_name != CounterTypes.MACHINE_COUNTER:
                                self.log.info(f"Process level counter matched. "
                                              f"Bash local path : {GeneralConstants.UNIX_PROCESS_BASH_SCRIPT} "
                                              f"Bash remote File path : {config_file_path}")
                                dir = f"{folder_path}{machine_obj.os_sep}{binary_name}"
                                dir = dir.replace(".", "_")  # in case of process name with . in it
                                if not machine_obj.check_directory_exists(directory_path=dir):
                                    machine_obj.create_directory(directory_name=dir)
                                # copy Process bash script to remote client
                                machine_obj.copy_from_local(local_path=GeneralConstants.UNIX_PROCESS_BASH_SCRIPT,
                                                            remote_path=config_folder)
                                time.sleep(180)
                                machine_obj.rename_file_or_folder(
                                    old_name=f"{config_folder}{machine_obj.os_sep}"
                                             f"{GeneralConstants.UNIX_PROCESS_BASH_FILE_NAME}",
                                    new_name=f"{config_file_path}")

                                self.log.info("Process level Bash script created successfully on the client")
                            else:
                                self.log.info(f"Machine level counter matched. "
                                              f"Bash local path : {GeneralConstants.UNIX_MACHINE_BASH_SCRIPT}"
                                              f"Bash remote File path : {config_file_path}")
                                dir = f"{folder_path}{machine_obj.os_sep}{binary_name}"
                                if not machine_obj.check_directory_exists(directory_path=dir):
                                    machine_obj.create_directory(
                                        directory_name=dir)
                                # copy machine bash script to remote client
                                machine_obj.copy_from_local(local_path=GeneralConstants.UNIX_MACHINE_BASH_SCRIPT,
                                                            remote_path=config_folder)
                                time.sleep(180)
                                machine_obj.rename_file_or_folder(
                                    old_name=f"{config_folder}{machine_obj.os_sep}"
                                             f"{GeneralConstants.UNIX_MACHINE_BASH_FILE_NAME}",
                                    new_name=f"{config_file_path}")

                                self.log.info("Machine level Bash script created successfully on the client")
                push_finish = True
            except Exception as exp:
                push_finish = False
                self.check_and_log_exception(exp=exp)
                attempt = attempt + 1
                # after few attempts, fail the monitor process by raising exceptions
                if attempt > TimerIntervals.PUSH_CONFIG_FAIL_RETRY:
                    raise Exception("Push configurations fail retry threshold exceeded.Fail the Performance collection")

        self.log.info("All Configurations got pushed to respective clients")
        # dump machine config and job config to the file
        self.log.info(f"Dumping Machine configs into file")
        self.perf_helper.dump_json_to_file(json_data=clients_config, out_file=self.machine_config_file_path)
        self.log.info(f"Dumping Job configs into file")
        self.perf_helper.dump_json_to_file(json_data=config_data, out_file=self.job_config_file_path)

    def get_thread_name(self, config):
        """forms the thread name based on config data

        Args:

            config      (dict)      --  dict containing performance monitor config data

        Returns:

            str     --  name of the thread

        """

        binary_name = config[GeneralConstants.BINARY_PARAM]
        if isinstance(binary_name, dict):
            platform = config[GeneralConstants.PLATFORM_PARAM]
            self.log.info(f"Forming Thread name with Platform as : {platform}")
            binary_name = binary_name[platform]
        client_name = config[GeneralConstants.CLIENT_PARAM]
        if binary_name == Binary.CONTENT_EXTRACTOR[Platforms.Unix]:
            binary_name = "ContentExtractor"
        thread_name = f"{client_name}_{binary_name}_Thread"
        self.log.info(f"Formed Thread Name for config : {thread_name}")
        return thread_name

    def kill_thread_and_get_stats(self, machine_obj, cmd_line, remote_file, file_path):
        """kills the monitor process on the client machine and get stats file to the controller

        Args:

            machine_obj         (obj)       --  Machine class object

            cmd_line            (str)       --  command line param to look for in process

            remote_file         (str)       --  remote csv file path which contains the performance stats collected

            file_path           (str)       --  file path in controller where stats needs to be copied over

        Returns:

            None

        """
        job_done = False
        on_error = 0
        pending_file_move = False
        while not job_done:
            try:
                monitor_pid = None
                # get pid of the monitored process
                if machine_obj.os_info.lower() == Platforms.Windows.lower():
                    monitor_pid = machine_obj.get_process_id(process_name=GeneralConstants.TYPEPERF_EXE,
                                                             command_line_keyword=cmd_line)
                else:
                    monitor_pid = machine_obj.get_process_id(process_name=GeneralConstants.BASH_EXE,
                                                             command_line_keyword=cmd_line)
                try:
                    # sometimes remote file fetch fails. so we are separating the monitor process kill and remote file
                    # fetch separately
                    if len(monitor_pid) == 0:  # no monitor process running.
                        # check whether remote file fetch is still pending
                        if not pending_file_move:
                            self.log.info(f"Process Instances to be killed is - 0. Skip getting the remote stats file")
                            break
                        else:
                            self.log.info(
                                f"Process instance already killed or not running. "
                                f"Try to get remote stats file - {remote_file}")
                    else:
                        self.log.info(
                            f"Going to Kill older Monitor Instance on client ip : {machine_obj.ip_address} "
                            f"with pid : {monitor_pid}")
                        # for unix bash scripts, multiple process may be running as child to bash script. Kill all such
                        for pid in monitor_pid:
                            self.log.info(f"Killing Process id : {pid}")
                            machine_obj.kill_process(process_id=pid)
                        self.log.info(
                            f"Killed the older Monitor Instance. Proceed with getting output stats "
                            f"from client IP : {machine_obj.ip_address}")
                except Exception as exp:
                    # sometimes for unix machine, child process of script may not exists. so
                    # avoid printing that exception
                    self.check_and_log_exception(exp=exp, ignore_list=[GeneralConstants.NO_VALID_PROCESS])
                # CSV performance stats remote file fetch
                self.log.info(f"Trying to access remote file path : {remote_file} on client : {machine_obj.ip_address}")
                try:
                    content = machine_obj.read_file(file_path=remote_file)
                    file = open(file_path, GeneralConstants.FILE_WRITE_MODE, newline=GeneralConstants.PYTHON_NEW_LINE)
                    file.write(content)
                    file.close()
                    dest_size = os.stat(file_path).st_size
                    source_size = machine_obj.get_file_size(file_path=remote_file, in_bytes=True)
                    self.log.info(
                        f"State file size details. Destination file size in bytes - [{dest_size}] "
                        f"Source file size in bytes - [{source_size}]")
                    # check for csv file delimiter , & file sizes
                    if "," not in content and int(dest_size) != int(source_size):
                        raise Exception(f"Something went wrong with remote stats file. Please check - {remote_file}")
                    self.log.info(f"File - {remote_file} fetched successfully from remote client to the controller")
                    # mark task as done
                    job_done = True
                    pending_file_move = False
                except Exception as exp:
                    pending_file_move = True
                    if GeneralConstants.FILE_NOT_EXISTS in repr(exp):
                        self.log.error(f"Error -> Remote stats file not found. File name : {remote_file} "
                                       f"on client : {machine_obj.ip_address}")
                    else:
                        self.check_and_log_exception(exp=exp)
            except Exception as exp:
                self.check_and_log_exception(exp=exp)
                on_error = on_error + 1
                # after few attempts, fail the monitor by raising exception
                if on_error > GeneralConstants.FILE_DOWNLOAD_ERROR_THRESHOLD:
                    self.log.error("Stats File thread crossed the failure threshold. Fail the collection")
                    self.error = True
                    break

    def push_stats_thread(self, stop):
        """Pushes the performance stats to the open data source

        Args:

            stop                    (bool)      --  boolean value to denote whether to stop the thread or not at runtime

        Returns:

            None

        Raises:

            Exception:

                    if failed to push data to open data source
        """
        thread_name = threading.currentThread().name
        on_error = 0
        queue_count = 0
        init_data_source = False
        process_data_source_obj = None
        machine_data_source_obj = None
        while True:
            # initialise data source only once for entire run
            monitor_counts = len(self.threads)
            if monitor_counts == 1:
                self.log.info(f"No monitor threads are running.")
            else:
                self.log.info(f"Total Threads : {monitor_counts} | "
                              f"Monitor threads running : {monitor_counts-1}")  # minus the push thread
            if not init_data_source:
                try:
                    self.create_performance_data_source()
                    process_data_source_obj = self.commcell.datacube.datasources.get(
                        GeneralConstants.Process_Data_Source_Name)
                    machine_data_source_obj = self.commcell.datacube.datasources.get(
                        GeneralConstants.Machine_Data_Source_Name)
                    # push the machine configurations to the open data source
                    self.push_hwinfo_to_data_source(config_json_file=self.machine_config_file_path)
                    self.log.info(f"Setting open DataSource setup as completed with True flag")
                    init_data_source = True
                except Exception as exp:
                    self.check_and_log_exception(exp=exp)
                    on_error = on_error + 1
                    if on_error > GeneralConstants.PUSH_ERROR_THRESHOLD:
                        self.log.info("Failed to create open data source to store performance stats")
                        self.error_msg = "Failed to create open data source to store performance stats"
                        self.error = True
            # check quit flag for thread
            if stop():
                self.log.info(f"Quit flag set. Stopping the Thread : {thread_name}")
                # come out if queue is empty or failure crossed threshold or no monitor threads are running
                self.check_alive_threads(threads=self.threads)
                if (self.queue.empty() and len(self.threads) == 1) or on_error > GeneralConstants.PUSH_ERROR_THRESHOLD:
                    break
                else:
                    count = self.queue.qsize()
                    # wait for queue to empty before going down
                    self.log.info(
                        f"{thread_name} waiting for queue to be empty before going down. Current Queue size : {count}")
                    if count not in (0, queue_count):
                        self.log.info(f"{thread_name} Setting Remaining queue count as : {count}")
                        queue_count = count
                    else:
                        # if queue size is not decreasing due to some data source push issue, then consider it as fail
                        self.log.info(f"{thread_name} queue is not decreasing. Current Queue Size : {count}")
                        on_error = on_error + 1
                        if on_error > GeneralConstants.PUSH_ERROR_THRESHOLD:
                            self.log.info("DataSource Push Queue is not decreasing. Fail the collection")
                            self.error_msg = "DataSource Push Queue is not decreasing. Fail the collection"
                            self.error = True

            try:
                while not self.queue.empty():
                    # get data from queue
                    self.log.info(f"Get data from Push queue. Current Queue size : {self.queue.qsize()}")
                    push_json = self.queue.get_nowait()  # lets not block the thread by calling get()
                    try:
                        self.log.info(f"Push stats configuration got from monitor thread")
                        self.perf_helper.print_config(config_data=push_json)
                        if push_json is not None:
                            post_data = self.get_data_from_csv(push_json=push_json)
                            counter_type = push_json[GeneralConstants.COUNTER_TYPE_PARAM]
                            stats_csv_file = push_json[GeneralConstants.STATS_FILE_PARAM]
                            if counter_type == CounterTypes.PROCESS_COUNTER:
                                self.log.info(f"Going to use Process level Performance DataSource for pushing stats")
                                process_data_source_obj.import_data(data=post_data)
                                self.log.info(
                                    f"Data got pushed for performance stats file : {stats_csv_file} in Process "
                                    f"DataSource. Total rows : {len(post_data)}")
                            else:
                                self.log.info(f"Going to use Machine level Performance DataSource for pushing stats")
                                machine_data_source_obj.import_data(data=post_data)
                                self.log.info(
                                    f"Data got pushed for performance stats file : {stats_csv_file} in Machine "
                                    f"DataSource. Total rows : {len(post_data)}")
                    except Exception as exp:
                        self.check_and_log_exception(exp=exp)
                        self.log.error(f"Pushed back the json to queue as something went wrong")
                        self.queue.put_nowait(push_json)
                        on_error = on_error + 1
                        if on_error > GeneralConstants.PUSH_ERROR_THRESHOLD:
                            self.log.error("Push thread crossed the failure threshold. Fail the collection")
                            self.error_msg = "Push thread crossed the failure threshold. Fail the collection"
                            self.error = True
                            break
                if stop() and len(self.threads) == 1:  # push thread alone running and all other monitor went down
                    self.log.info(f"Quit flag set. Stopping the Thread : {thread_name} completely")
                    break
                self.log.info(
                    f"{thread_name} is up and running. Sleeping for {TimerIntervals.PUSH_THREAD_SLEEP_IN_MINS} Mins")
                time.sleep(TimerIntervals.PUSH_THREAD_SLEEP_IN_MINS * 60)
            except Exception as exp:
                self.check_and_log_exception(exp=exp)
        self.log.info(f"{thread_name} going down gracefully")

    def monitor_thread(self, job_id, config, push_to_data_source, stop):
        """Thread which is used to monitor the commvault process on client for performance data

        Args:

            job_id              (str)       --  job id

            push_to_data_source (bool)      --  boolean to specify whether to push stats to open data source or not

            config              (dict)      --  dict containing performance monitor config

                                Example : {
                                            "client": "xuz",
                                            "binary": "cvd.exe",
                                            "counters": [
                                                            "\\Process({pname}*)\\Handle Count",
                                                            "\\Process({pname}*)\\Thread Count"
                                                        ],
                                            "platform": "Windows",
                                            "statsfolder": "C:\\Automation_Data",
                                            "cmdlineparams":"Instance002"
                                        }

            stop                (bool)      --  boolean value to denote whether to stop the thread or not at runtime

        Returns:

            None

        """
        machine_obj = None
        client_obj = None
        is_cvlt_client = False
        port_usage_stats = False
        if GeneralConstants.PORT_USAGE_PARAM in config and config[GeneralConstants.PORT_USAGE_PARAM]:
            port_usage_stats = True
        platform = config[GeneralConstants.PLATFORM_PARAM]
        thread_name = threading.currentThread().name
        self.log.info(f"{thread_name} - Starting")
        binary_name = config[GeneralConstants.BINARY_PARAM]
        counters = config[GeneralConstants.COUNTERS_PARAM]
        if isinstance(binary_name, dict):
            binary_name = binary_name[platform]
        client_name = config[GeneralConstants.CLIENT_PARAM]
        cmd_line = config[GeneralConstants.COMMAND_LINE_PARAM]
        if self.commcell.clients.has_client(client_name):
            is_cvlt_client = True
        # check whether command line param is job related, if so include job id
        if cmd_line in (GeneralConstants.JOB_ID_CMD_LINE_PARAM, GeneralConstants.JOB_ID_CMD_LINE_PARAM_OTHER,
                        GeneralConstants.JOB_TOKEN_CMD_LINE_PARAM):
            cmd_line = f"{cmd_line}{job_id}"
            self.log.info(f"Adding job id to the command line param. Final cmd line : {cmd_line}")
        init_done = False
        on_error = 0
        # initialise the machine object
        while not init_done:
            try:
                client_obj = None
                # check cache. if found reuse it or else initialise machine obj again
                if is_cvlt_client:
                    cache_key = f"{client_name}{GeneralConstants.CLIENT_OBJ_CACHE}"
                    if self.cache_obj.is_exists(key=cache_key):
                        client_obj = self.cache_obj.get_key(key=cache_key)
                    else:
                        client_obj = self.commcell.clients.get(client_name)
                        self.cache_obj.put_key(key=cache_key, value=client_obj)
                cache_key = f"{client_name}{GeneralConstants.MACHINE_OBJ_CACHE}"
                if self.cache_obj.is_exists(key=cache_key):
                    machine_obj = self.cache_obj.get_key(key=cache_key)
                else:
                    if is_cvlt_client:
                        self.log.info(f"It is a commvault client - {client_name}")
                        client_obj = self.commcell.clients.get(client_name)
                        machine_obj = Machine(machine_name=client_obj, commcell_object=self.commcell)
                    else:
                        self.log.info(f"It is a Non-commvault client - {client_name}")
                        machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell,
                                              username=config[GeneralConstants.USERNAME_PARAM],
                                              password=config[GeneralConstants.PASSWORD_PARAM])
                    self.log.info(f"Initialised Machine object for client : {client_name}")
                    self.cache_obj.put_key(key=cache_key, value=machine_obj)

                init_done = True
            except Exception as exp:
                on_error = on_error + 1
                if on_error > GeneralConstants.MONITOR_THREAD_ERROR_THRESHOLD:
                    self.log.error(GeneralConstants.ERROR_MONITOR_THREAD_INIT_FAIL)
                    self.error_msg = GeneralConstants.ERROR_MONITOR_THREAD_INIT_FAIL
                    self.error = True
                    break

        config_file = self.get_config_file_path(config=config, separator=machine_obj.os_sep)
        self.log.info(f"Config file path for this config : {config_file}")
        controller_folder = os.path.join(
            GeneralConstants.CONTROLLER_FOLDER_PATH,
            self.build_id,
            client_name,
            binary_name.replace(".", "_"))
        if not os.path.exists(controller_folder):
            os.makedirs(controller_folder, exist_ok=True)
            self.log.info(f"Created folder on controller : {controller_folder}")
        stats_file_count = 1
        stats_collected = False
        binary_process_ids = []
        remote_path = ''
        local_path = ''
        path = ''
        file_name = ''
        is_machine_counter = False
        on_error = 0
        while True:
            # check if quit flag is set
            if stop():
                self.log.info(f"Quit flag set. Stopping the Thread : {thread_name}")
                break
            try:
                pid_list = []
                if binary_name != CounterTypes.MACHINE_COUNTER:
                    pid_list = machine_obj.get_process_id(process_name=binary_name, command_line_keyword=cmd_line)
                    # add all monitored process pid to list to track
                    for process_id in pid_list:
                        if process_id not in binary_process_ids:
                            binary_process_ids.append(process_id)
                else:
                    is_machine_counter = True
                if len(pid_list) > 0 or is_machine_counter:
                    if port_usage_stats:
                        port_key = f"{thread_name}{GeneralConstants.PORT_USAGE_STATS}"
                        collect_stats = False
                        if port_key not in self.timer_task:
                            collect_stats = True
                        elif port_key in self.timer_task:
                            last_time = int(self.timer_task[port_key])
                            now_time = int(time.time())
                            time_limit = int(TimerIntervals.PORT_USAGE_CAPTURE_TIME_INTERVAL_IN_MINS * 60)
                            if now_time > last_time + time_limit:
                                collect_stats = True
                        if collect_stats:
                            custom_thread = threading.Thread(target=self.push_netstat_to_data_source, args=(
                                machine_obj, client_name, binary_name, pid_list, push_to_data_source), daemon=True)
                            custom_thread.start()
                            now_time = int(time.time())
                            self.log.info(f"{thread_name} -> Updating port usage last execution time as : {now_time}")
                            self.timer_task[port_key] = now_time
                        else:
                            self.log.info(f"Not collecting port usage as criteria is not met")
                    if is_machine_counter:
                        # machine performance stats collection
                        self.log.info(f"Machine level stats collection enabled. Proceeding further")
                    else:
                        # process performance stats collection
                        self.log.info(f"Expected binary process {binary_name} is running with PID : {pid_list}")
                    if platform == Platforms.Windows:
                        # for windows client, start the typeperf command
                        remote_path = config_file.replace(GeneralConstants.COUNTERS_TEXT_FILE, "")
                        remote_path = f"{remote_path}_{stats_file_count}{GeneralConstants.STATS_OUTPUT_TEXT_FILE}"
                        path, file_name = os.path.split(remote_path)
                        local_path = os.path.join(controller_folder, file_name)
                        self.log.info(f"Starting the typperf command with stats file count : {stats_file_count}")
                        cmd = f"{GeneralConstants.TYPEPERF_EXE} -cf {config_file} " \
                              f"-si {TimerIntervals.PERFORMANCE_STATS_INTERVAL_IN_SECS} -y -f CSV -o {remote_path}"
                        self.log.info(f"Typeperf command formed : {cmd}")
                        stats_started = False
                        on_stat_error = 0
                        while not stats_started:
                            try:
                                if is_cvlt_client:
                                    client_obj.execute_command(command=cmd, wait_for_completion=False)
                                else:
                                    # for some reason, subprocess call from powershell is blocking parent process too
                                    # so implementing this as thread with timeout for non commvault client
                                    try:
                                        cmd_thread = threading.Thread(target=self.run_cmd_timer,
                                                                      args=(machine_obj, cmd))
                                        cmd_thread.start()
                                        cmd_thread.join(
                                            timeout=TimerIntervals.NON_COMMVAULT_CLIENT_REMOTE_COMMAND_EXECUTE_WAIT_IN_SECS)
                                    except Exception as exp:
                                        self.check_and_log_exception(exp=exp)
                                stats_started = True
                            except Exception as exp:
                                self.check_and_log_exception(exp=exp)
                                on_stat_error = on_stat_error + 1
                                if on_stat_error > GeneralConstants.REMOTE_CLIENT_PROCESS_START_THRESHOLD:
                                    raise Exception(GeneralConstants.ERROR_MONITOR_THREAD_PROCESS_START)

                        self.log.info(f"Typeperf started on client : {client_name} @ time : {datetime.datetime.now()}")
                    elif platform == Platforms.Unix:
                        self.log.info(f"Starting the Bash script with stats file count : {stats_file_count}")
                        process = ','.join([str(pid) for pid in pid_list])
                        remote_path = config_file.replace(GeneralConstants.COUNTERS_BASH_FILE, "")
                        remote_path = f"{remote_path}_{stats_file_count}{GeneralConstants.STATS_OUTPUT_TEXT_FILE}"
                        # this get passed as command line args in order to kill this instance of bash
                        file_name = remote_path
                        # append file name to the controller folder to get full path
                        local_path = os.path.join(controller_folder, file_name.split("/")[-1])
                        header = GeneralConstants.COLUMN_TIME  # first column is time always
                        for each_counter in counters:
                            header = f"{header},{GeneralConstants.COUNTERS_FIELD_MAPPING[each_counter]}"
                        counter_type = CounterTypes.PROCESS_COUNTER if binary_name != CounterTypes.MACHINE_COUNTER \
                            else CounterTypes.MACHINE_COUNTER
                        if counter_type == CounterTypes.PROCESS_COUNTER:
                            self.log.info("Process level counters found for this configuration")
                            # process counters starts with $. so remove those
                            counter = ','.join([str(c)[1:] for c in counters])
                            cmd = f"{GeneralConstants.BASH_EXE} '{config_file}' '{process}' '{remote_path}' " \
                                  f"'{header}' '{counter}' {TimerIntervals.PERFORMANCE_STATS_INTERVAL_IN_SECS}"
                            self.log.info(f"Process Bash cmd formed : {cmd}")
                            stats_started = False
                            on_stat_error = 0
                            while not stats_started:
                                try:
                                    if is_cvlt_client:
                                        client_obj.execute_command(command=cmd, wait_for_completion=False)
                                    else:
                                        # for some reason, subprocess call from powershell is blocking parent process too
                                        # so implementing this as thread with timeout for non commvault client
                                        try:
                                            cmd_thread = threading.Thread(target=self.run_cmd_timer,
                                                                          args=(machine_obj, cmd))
                                            cmd_thread.start()
                                            cmd_thread.join(
                                                timeout=TimerIntervals.NON_COMMVAULT_CLIENT_REMOTE_COMMAND_EXECUTE_WAIT_IN_SECS)
                                        except Exception as exp:
                                            self.check_and_log_exception(exp=exp)
                                    stats_started = True
                                except Exception as exp:
                                    self.check_and_log_exception(exp=exp)
                                    on_stat_error = on_stat_error + 1
                                    if on_stat_error > GeneralConstants.REMOTE_CLIENT_PROCESS_START_THRESHOLD:
                                        raise Exception(GeneralConstants.ERROR_MONITOR_THREAD_PROCESS_START)

                            self.log.info(
                                f"Process Bash started on client : {client_name} @ time : {datetime.datetime.now()}")
                        else:
                            self.log.info("Machine level counters found for this configuration")
                            # process counters starts with $$. so remove those
                            counter = ','.join([str(c)[2:] for c in counters])
                            cmd = f"{GeneralConstants.BASH_EXE} '{config_file}' '{remote_path}' '{header}' " \
                                  f"'{counter}' {TimerIntervals.PERFORMANCE_STATS_INTERVAL_IN_SECS}"
                            self.log.info(f"Machine Bash cmd formed : {cmd}")
                            try:
                                if is_cvlt_client:
                                    client_obj.execute_command(command=cmd, wait_for_completion=False)
                                else:
                                    # for some reason, subprocess call from powershell is blocking parent process too
                                    # so implementing this as thread with timeout for non commvault client
                                    try:
                                        cmd_thread = threading.Thread(target=self.run_cmd_timer,
                                                                      args=(machine_obj, cmd))
                                        cmd_thread.start()
                                        cmd_thread.join(
                                            timeout=TimerIntervals.NON_COMMVAULT_CLIENT_REMOTE_COMMAND_EXECUTE_WAIT_IN_SECS)
                                    except Exception as exp:
                                        self.check_and_log_exception(exp=exp)
                            except Exception as exp:
                                self.check_and_log_exception(exp=exp)
                            self.log.info(
                                f"Machine Bash started on client : {client_name} @ time : {datetime.datetime.now()}")
                    stats_collected = True
                    current_time = time.time()
                    time_limit = current_time + (TimerIntervals.MONITOR_THREAD_RESTART_INTERVAL_IN_MINS * 60)
                    # wait for predefined time before restarting the performance collection threads
                    while current_time < time_limit:
                        self.log.info(
                            f"{thread_name} is up and running. "
                            f"Sleeping for {TimerIntervals.MONITOR_THREAD_SLEEP_IN_MINS} Mins")
                        time.sleep(TimerIntervals.MONITOR_THREAD_SLEEP_IN_MINS * 60)
                        current_time = time.time()
                        # check for quit flag
                        if stop():
                            self.log.info(f"Quit flag set. Stopping the Monitor Process : {thread_name}")
                            self.kill_thread_and_get_stats(machine_obj=machine_obj,
                                                           cmd_line=file_name,
                                                           remote_file=remote_path,
                                                           file_path=local_path)
                            self.log.info(f"{thread_name} killed all instances of process. Will go down!!!")
                            break
                    if not stop():
                        self.log.info(f"Restart the monitor process as it reached the time limit")
                    # predefined time limit reached. Stop remote scripts and get output csv files
                    self.kill_thread_and_get_stats(machine_obj=machine_obj,
                                                   cmd_line=file_name,
                                                   remote_file=remote_path,
                                                   file_path=local_path)
                    self.log.info(
                        f"Successfully moved stats file : {remote_path} from client : {client_name} "
                        f"to controller : {local_path}")
                    stats_file_count = stats_file_count + 1
                    # put the stats into queue for pushing into data source
                    if push_to_data_source:
                        push_json = {
                            GeneralConstants.BINARY_PARAM: binary_name,
                            GeneralConstants.CLIENT_PARAM: client_name,
                            GeneralConstants.COUNTER_TYPE_PARAM: CounterTypes.PROCESS_COUNTER if binary_name != CounterTypes.MACHINE_COUNTER else CounterTypes.MACHINE_COUNTER,
                            GeneralConstants.COUNTERS_PARAM: config[GeneralConstants.COUNTERS_PARAM],
                            GeneralConstants.BINARY_PID_PARAM: pid_list,
                            GeneralConstants.STATS_FILE_PARAM: local_path,
                            GeneralConstants.PLATFORM_PARAM: platform}
                        # quit flag set because of error from any thread, then don't push further stats to data source
                        if stop() and self.error:
                            self.log.info(
                                f"Quit signal set because of Error. Don't push any request to queue. "
                                f"Dropping request : {push_json}")
                        else:
                            if os.path.exists(local_path):
                                self.queue.put_nowait(push_json)
                                self.log.info(f"{thread_name} -> Queue push was success for Json - {push_json}")
                            else:
                                self.log.error(f"File not Found. Skip adding stats file to queue : {local_path}")

                else:
                    self.log.info(f"Expected binary process {binary_name} is not running on client : {client_name}")

            except Exception as exp:
                self.check_and_log_exception(exp=exp)
                on_error = on_error + 1
                if on_error > GeneralConstants.MONITOR_THREAD_ERROR_THRESHOLD:
                    self.log.error(GeneralConstants.ERROR_MONITOR_THREAD_FAIL)
                    self.error_msg = GeneralConstants.ERROR_MONITOR_THREAD_FAIL
                    self.error = True
                    break

        self.log.info(f"{thread_name} is going down gracefully")
        # if stats was not collected even once, then it is failure. Raise exception
        if not stats_collected:
            self.log.info(f"{thread_name} -> Stats not collected properly for this configurations - {config}")
            self.error = True
            self.error_msg = GeneralConstants.ERROR_STATS_NOT_COLLECTED_ONCE

    def start_monitor(self, job_id, job_type, config, push_to_data_source=True, **kwargs):
        """ starts the performance monitor for the given job id

        Args:

            job_id              (int/str)   --      job id which needs to be monitored for performance

                In case of non-job based monitoring, this value will be considered as timeout in Mins

            job_type            (int)       --      type of job
                                                Example : defined in JobTypes in constants.py

            push_to_data_source (bool)      --      boolean to specify whether to push stats to open data source or not
                                                        Default -True

            config              (dict)      --      dict containing inputs for performance collection

                        Example : {
                                    "Recover": {
                                                "1": {
                                                        "client": "xyz",
                                                        "binary": "cvd.exe",
                                                        "counters": [
                                                                            "\\Process({pname}*)\\Handle Count",
                                                                            "\\Process({pname}*)\\Thread Count"
                                                                    ],
                                                        "platform": "Windows",
                                                        "statsfolder": "C:\\Automation_Data",
                                                        "cmdlineparams":"Instance002"
                                                    }
                                                }
                                }

                        -- Recover is the job phase
                        -- For time based collection, job phase is : TimerPhase

                        Example : {
                                    "TimerPhase": {
                                                "1": {
                                                        "client": "xyz",
                                                        "binary": "cvd.exe",
                                                        "counters": [
                                                                            "\\Process({pname}*)\\Handle Count",
                                                                            "\\Process({pname}*)\\Thread Count"
                                                                    ],
                                                        "platform": "Windows",
                                                        "statsfolder": "C:\\Automation_Data",
                                                        "cmdlineparams":""
                                                    }
                                                }
                                }


                     **kwargs    --  optional params

                    DataSourceName  --  Name of the data source used in crawl job

                    SourceName_s    --  Name of the source data

                    SourceSize_s    --  Size of the source data


        Returns:

            bool        --  True: if performance stats was collected properly
                            False: if performance stats collection ended in some error or failed to collect

        Raises:

            Exception:

                    if input data type is not valid

                    if failed to monitor performance stats for the job

        """
        if isinstance(job_id, str):
            job_id = int(job_id)
        if not isinstance(config, dict) or not isinstance(job_id, int):
            raise Exception("Input data type is not valid")
        job_obj = None
        current_time = None
        time_limit = None
        if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
            self.log.info(f"Job based Monitoring")
            job_obj = self.commcell.job_controller.get(job_id)
        else:
            self.log.info(f"Time based Monitoring")
            current_time = time.time()
            time_limit = current_time + (job_id * 60)
            self.log.info(f"Timeout set as : {job_id} Mins")
        old_phase = ''
        current_status = ''
        current_phase = ''
        job_done = False
        job_pause = False
        job_status_fail_count = 0
        monitor_phase_count = 0
        self.log.info(f"Counters field mapping loaded : {GeneralConstants.COUNTERS_FIELD_MAPPING}")
        try:
            if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
                job_done = job_obj.is_finished
        except Exception as exp:
            self.check_and_log_exception(exp=exp)
        # loop till job is finished
        while not job_done:
            try:
                if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
                    job_done = job_obj.is_finished
                else:
                    current_time = time.time()
                    if current_time > time_limit:
                        self.log.info(f"Time limit reached")
                        job_done = True
                # if job done, then stop all threads and go down
                if job_done:
                    self.log.info(f"Monitored job completed. Stopping the threads")
                    self.check_and_kill_threads(threads=self.threads)
                    break
                if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
                    current_status = job_obj.status
                # check job status. if it goes pending/waiting, then stop all collection threads and wait for resume
                if job_type != JobTypes.TIME_BASED_JOB_MONITORING and current_status.lower(
                ) in [JobStatus.PENDING, JobStatus.WAITING, JobStatus.SUSPENDED]:
                    self.log.info(f"Job is in Pending/Suspend or Waiting state. Current state : {current_status}."
                                  f" Pausing the peformance monitor")
                    self.check_and_kill_threads(threads=self.threads)
                    job_pause = True
                    old_phase = current_status  # we need it to restart all threads once job gets resumed
                elif job_type == JobTypes.TIME_BASED_JOB_MONITORING:
                    self.log.info(f"Timer is running. Remaining Mins - {int(time_limit - current_time)/60}")
                else:
                    self.log.info(f"Monitored Job is in Running state")
                    job_pause = False
            except Exception as exp:
                job_status_fail_count = job_status_fail_count + 1
                self.check_and_log_exception(exp=exp)
                if job_status_fail_count > TimerIntervals.JOB_STATUS_FAIL_RETRY:
                    self.log.error("Main thread job status check threshold reached. Going down")
                    self.check_and_kill_threads(threads=self.threads)
                    raise Exception("Main thread job status check threshold reached. Please check logs")
                continue  # continue trying to get job status
            # one of the thread reported error status, stop the collection
            if self.error:
                self.log.info(f"Error flag set. Going down")
                self.check_and_kill_threads(threads=self.threads)
                raise Exception(self.error_msg)
            try:
                if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
                    current_phase = job_obj.phase
                else:
                    current_phase = GeneralConstants.TIMER_PHASE
            except Exception as exp:
                self.check_and_log_exception(exp=exp)
            # current phase is different from old monitored phase, then kill older threads and start new collection for
            # current job phase
            if old_phase != current_phase and not job_pause:
                self.log.info(f"Phase change detected. Old Phase : {old_phase}  Current Phase : {current_phase}")
                self.check_and_kill_threads(threads=self.threads)
                self.log.info(f"Job is ready for Monitoring performance stats with phase : {current_phase}")
                old_phase = current_phase
                # check if current phase is in config which user needs to be monitored
                if current_phase in config:
                    self.log.info(f"Current Phase present in performance monitor. Going to start off the thread")
                    monitor_phase_count = monitor_phase_count + 1
                    current_phase_config = config[current_phase]
                    # check for duplicate configurations
                    current_phase_config = self.perf_helper.remove_dup_configs(config=current_phase_config)
                    for config_no in range(1, len(current_phase_config) +
                                           1):  # length of dict + 1 as we starting with index 1
                        config_to_process = str(config_no)
                        self.log.info(
                            f"{config_to_process} --> Configuration : {current_phase_config[config_to_process]}")
                        if current_phase_config[config_to_process] is None or \
                                current_phase_config[config_to_process] == {}:
                            self.log.info("Empty Configurations. Ignore")
                            continue
                        monitor_thread = threading.Thread(target=self.monitor_thread,
                                                          args=(job_id, current_phase_config[config_to_process],
                                                                push_to_data_source,
                                                                lambda: self.stop_threads, ))
                        monitor_thread.name = self.get_thread_name(config=current_phase_config[config_to_process])
                        monitor_thread.start()
                        # append the thread details to thread array
                        self.threads.append(monitor_thread)
                        self.log.info(f"Started thread with name : {monitor_thread.name}")
                    self.log.info(f"Total Threads invoked for Phase : {current_phase} = {len(self.threads)}")
                    if push_to_data_source:  # Pushing stats to open data source
                        self.log.info(f"Starting the performance stats open data source push thread")
                        push_thread = threading.Thread(
                            target=self.push_stats_thread, args=(
                                lambda: self.stop_threads, ))
                        push_thread.name = GeneralConstants.PUSH_THREAD_NAME
                        push_thread.start()
                        # append the thread details to thread array
                        self.threads.append(push_thread)
                        self.log.info(f"Started thread with name : {push_thread.name}")

                else:
                    self.log.info(f"Current Phase : {current_phase} is not present in Config. No need to Monitor")
            else:
                if not job_pause:
                    self.log.info(f"No change in Job phase. Continue Monitoring in phase : {current_phase}")
                    self.check_alive_threads(threads=self.threads)
            # sleep for some predefined time and then wake up to check further on job progress
            self.log.info(f"Main Monitor sleeping for {TimerIntervals.MAIN_THREAD_SLEEP_IN_MINS} Mins")
            time.sleep(TimerIntervals.MAIN_THREAD_SLEEP_IN_MINS * 60)
            self.log.info(f"Main Monitor Wake up")
        # job is finished. fetch job details and store it in JSON file
        self.check_and_kill_threads(threads=self.threads)
        if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
            self.log.info(f"Job finished with status : {job_obj.status}")
            job_details = self.fetch_job_details(job_obj=job_obj, job_type=job_type, **kwargs)
            self.perf_helper.dump_json_to_file(json_data=job_details, out_file=self.job_details_file_path)
        # push job details to the open data source
        if push_to_data_source and job_type != JobTypes.TIME_BASED_JOB_MONITORING:
            self.log.info("Calling job details push to data source")
            self.push_jobinfo_to_data_source()
        if self.error:
            raise Exception(self.error_msg)
        # if total monitored phase in config is not equal to actually one monitored, then we missed few job phase.
        if monitor_phase_count != len(config):
            self.log.info(f"Total phases in configurations : {len(config)} "
                          f"but monitored phase count : {monitor_phase_count}")
            raise Exception(GeneralConstants.ERROR_MISSING_PERFORMANCE_STATS_FOR_PHASE)
        self.log.info(f"Performance collection done successfully")
        self.cleanup_configurations(config_data=config)
