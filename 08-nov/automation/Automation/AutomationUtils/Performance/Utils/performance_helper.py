# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""This file contains helper functions for monitoring cv process performance stats

Classes defined in this file:

    PerformanceHelper       --  helper functions related to performance monitoring configurations

    AutomationCache         --  class for caching mechanism


    PerformanceHelper:

        __init__()                          --  Initialize the PerformanceHelper class object

        form_sdg_fs_monitor_param()         --  forms performance monitor param for FS data Source crawl job in SDG

        form_client_monitor_param()         --  forms client performance monitor param based on input provided

        remove_invalid_counters()           --  removes invalid counters for the client based on OS flavor

        dump_json_to_file()                 --  dumps json(dict) to the output file

        read_json_file()                    --  reads the json file and returns the dict

        fetch_data_source_crawl_stats()     --  fetches the crawl stats for the given data source name

        find_min_max_for_counters()         --  finds min/max values for the each performance counters of given config

        find_min_max_for_netstat()          --  finds min/max values for netstat of process/Machine of given config

        print_config()                      --  logs the client config

        find_fs_extract_duration_stats()    --  fetches the file system extract duration stats for each file type

        form_fso_monitor_param()            --  forms performance monitor param for FS data Source crawl job in FSO

        remove_dup_configs()                --  removes duplicate configs from dict for job phase


    AutomationCache

        __init__()                          --  Initialize the AutomationCache class object

        is_exists()                         --  checks whether given key exists in cache or not

        get_key()                           --  gets value from cache for given key

        put_key()                           --  inserts key into cache


"""
import copy
import json
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.Performance.Utils.constants import JobTypes
from AutomationUtils.Performance.Utils.constants import CounterTypes
from AutomationUtils.Performance.Utils.constants import Binary
from AutomationUtils.Performance.Utils.constants import JobPhaseNames
from AutomationUtils.Performance.Utils.constants import WindowsProcessCounters
from AutomationUtils.Performance.Utils.constants import WindowsMachineCounters
from AutomationUtils.Performance.Utils.constants import UnixProcessCounters
from AutomationUtils.Performance.Utils.constants import UnixMachineCounters
from AutomationUtils.Performance.Utils.constants import CustomCounters
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from AutomationUtils.Performance.Utils.constants import Platforms
from dynamicindex.utils import constants as dynamic_constants


class AutomationCache():
    """contains caching mechanism related functions"""

    def __init__(self):
        self.log = logger.get_log()
        # cache implementation
        self.cache = {}

    def is_exists(self, key):
        """ checks whether given key exists in cache or not

        Args:

            key             --      key to look for in cache

        Returns:

            bool        -- True if key is found else False

        """
        if key.lower() in self.cache:
            return True
        return False

    def get_key(self, key):
        """ gets the value for the given key from cache

                Args:

                    key             --      key to look for in cache

                Returns:

                    value from the cache for the given key

        """
        key = key.lower()
        self.log.info(f"Retrieved value : {self.cache[key]} from cache for key : {key}")
        return self.cache[key]

    def put_key(self, key, value):
        """ sets the value for the given key in cache

                Args:

                    key             --      key to insert in cache

                    value           --      value of the key

                Returns:

                    None

        """
        key = key.lower()
        self.cache[key] = value
        self.log.info(f"Caching key : {key}  value : {value}")


class PerformanceHelper():
    """contains helper functions related to performance monitoring of jobs or process on client"""

    def __init__(self, commcell_object):
        """ Initialize the PerformanceHelper class

                   Args:

                       commcell_object         (obj)       --      commcell object

        """
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.cache_obj = AutomationCache()

    def remove_dup_configs(self, config):
        """removes duplicate configs from dict for job phase

        Args:

            config          (dict)          --  configuration for job phase

        Returns:

                dict    --  after removing duplicates

        """
        monitor = []
        index = 1
        output = {}
        for config_no in range(1, len(config) +
                               1):  # length of dict + 1 as we starting with index 1
            config_to_process = str(config_no)
            current_param = config[config_to_process]
            if current_param is None or current_param == {}:
                continue
            client = current_param[GeneralConstants.CLIENT_PARAM]
            binary = current_param[GeneralConstants.BINARY_PARAM]
            cmd = current_param[GeneralConstants.COMMAND_LINE_PARAM]
            key = f"{client}_{binary}_{cmd}".lower()
            if key not in monitor:
                monitor.append(key)
                output[str(index)] = current_param
                index = index + 1
            else:
                self.log.info(f"Removing the Duplicated configs : {current_param}")

        return output

    def form_fso_monitor_param(self, index_server, job_type, counters=None, search_engine=None, access_node=None):
        """forms performance monitor param for FS data Source crawl job in FSO

        Args:

            index_server                (str)       --      name of the index server

            job_type                    (int)       --      type of job
                                                                Example : defined in JobTypes in constants.py

            counters                    (dict)      --      Windows/Unix counters

                                    Example : {
                                                'Process' : [Memory,Handle]
                                                'Machine' : [Memory,CPU]
                                             }
                    if None, then all counters will be selected for monitoring

            search_engine               (list)      --      list of search engine client names

            access_node                 (str)       --      Access node client name

        Returns:

            dict        --  containing monitoring configurations for clients

            Example : {
                'Live Scan': {
                                '1': {
                                        'client': 'dez',
                                        'binary': {'Windows': 'IFind.exe'},
                                        'counters': ['\\Process(%s*)\\Handle Count', '\\Process(%s*)\\Thread Count'],
                                        'platform': 'UNIX',
                                        'statsfolder': '/Users/root/commvault_automation/Automation_Performance_Data'}
                                        'cmdlineparams': "-j ",
                                        'portusagestats' : True,
                                        # below fields are applicable for non-commvault client alone
                                        'client_username':<username>,
                                        'client_password':<password>
                                    }
                            }
                }

        Raises

            Exception:

                    if input data type is not valid

        """
        if not isinstance(index_server, str):
            raise Exception("Input data type is not valid")
        if counters is None:
            counters = {
                CounterTypes.MACHINE_COUNTER:
                    WindowsMachineCounters.COUNTER_VALUES + UnixMachineCounters.COUNTER_VALUES,
                CounterTypes.PROCESS_COUNTER:
                    WindowsProcessCounters.COUNTER_VALUES + UnixProcessCounters.COUNTER_VALUES}
            self.log.info(f"No input for counters so Adding All counters by Default - {counters}")
        self.log.info("Going to form file system monitor params based on user inputs")
        index_server_obj = self.commcell.index_servers.get(index_server)
        index_server_client_list = copy.deepcopy(index_server_obj.client_name)
        self.log.info(f"Index server Initialised. Total index server nodes : {len(index_server_client_list)}")
        monitor_param = {}
        index_server_machine_param = []
        index_server_param = []
        for node in index_server_client_list:
            index_server_machine_param.append(self.form_client_monitor_param(
                client_name=node, phase_name=JobPhaseNames.DUMMY_EMPTY,
                counters=counters[CounterTypes.MACHINE_COUNTER]))
            index_server_param.append(self.form_client_monitor_param(
                client_name=node,
                phase_name=JobPhaseNames.DUMMY_DATA_CUBE,
                counters=counters[CounterTypes.PROCESS_COUNTER]))
        self.log.info("Index server configuration formed")
        if job_type == JobTypes.FSO_BACKUP_QUICK_SCAN:
            cvci_param = []
            self.log.info(f"Quick scan job. Forming cvcianalytics param")
            for node in index_server_client_list:
                cvci_param.append(self.form_client_monitor_param(
                    client_name=node,
                    phase_name=JobPhaseNames.DUMMY_CVCI_ANALYTICS,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
            index = 1
            monitor_param[JobPhaseNames.ANALYSIS] = {}
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.ANALYSIS][str(index)] = index_server_machine_param[i]
                index = index + 1
                monitor_param[JobPhaseNames.ANALYSIS][str(index)] = index_server_param[i]
                index = index + 1
                monitor_param[JobPhaseNames.ANALYSIS][str(index)] = cvci_param[i]
                index = index + 1
        elif job_type == JobTypes.FSO_BACKUP_FULL_SCAN_SOURCE_CI:
            self.log.info(f"Full scan job for CI'ed Client. Forming analyticsmgr param")
            mgr_service_param = self.form_client_monitor_param(client_name=self.commcell.commserv_client.name,
                                                               phase_name=JobPhaseNames.DUMMY_CVODS,
                                                               counters=counters[CounterTypes.PROCESS_COUNTER],
                                                               **{GeneralConstants.CVODS_APP_NAME:
                                                                  GeneralConstants.ANALYTICS_MGR_SERVICE_NAME})
            self.log.info(f"Analytics Mgr Service - CVODS param formed")
            index = 1
            monitor_param[JobPhaseNames.IMPORT_INDEX] = {}
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = index_server_machine_param[i]
                index = index + 1
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = index_server_param[i]
                index = index + 1
            monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = mgr_service_param
            index = len(monitor_param[JobPhaseNames.IMPORT_INDEX]) + 1
            for node in search_engine:
                self.log.info(f"Forming search engine param for search node : {node}")
                # process counters
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = self.form_client_monitor_param(
                    client_name=node, phase_name=JobPhaseNames.DUMMY_SEARCH_ENGINE,
                    counters=counters[CounterTypes.PROCESS_COUNTER])
                index = index + 1
                # Machine counters
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = self.form_client_monitor_param(
                    client_name=node, phase_name=JobPhaseNames.DUMMY_EMPTY,
                    counters=counters[CounterTypes.MACHINE_COUNTER])
                index = index + 1
        elif job_type == JobTypes.FSO_BACKUP_FULL_SCAN:
            self.log.info(f"Full scan job for backup client.")
            index = 1
            monitor_param[JobPhaseNames.INDEX_EXTRACTION] = {}
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = index_server_machine_param[i]
                index = index + 1
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = index_server_param[i]
                index = index + 1
                cv_distributor_param = self.form_client_monitor_param(client_name=index_server_client_list[i],
                                                                      phase_name=JobPhaseNames.INDEX_EXTRACTION,
                                                                      counters=counters[CounterTypes.PROCESS_COUNTER])
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = cv_distributor_param
                index = index + 1
                cvods_param = self.form_client_monitor_param(client_name=index_server_client_list[i],
                                                             phase_name=JobPhaseNames.DUMMY_CVODS,
                                                             counters=counters[CounterTypes.PROCESS_COUNTER],
                                                             **{GeneralConstants.CVODS_APP_NAME:
                                                                GeneralConstants.INDEX_SERVER_SERVICE_NAME})
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = cvods_param
                index = index + 1
                clrestore_param = self.form_client_monitor_param(client_name=index_server_client_list[i],
                                                                 phase_name=JobPhaseNames.DUMMY_CLRESTORE,
                                                                 counters=counters[CounterTypes.PROCESS_COUNTER])
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = clrestore_param
                index = index + 1
                gateway_param = self.form_client_monitor_param(client_name=index_server_client_list[i],
                                                               phase_name=JobPhaseNames.DUMMY_INDEX_GATEWAY,
                                                               counters=counters[CounterTypes.PROCESS_COUNTER])
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = gateway_param
        elif job_type == JobTypes.FSO_LIVE_CRAWL:
            self.log.info(f"Live crawl for client using access node")
            index = 1
            monitor_param[JobPhaseNames.LIVE_SCAN] = {}
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.LIVE_SCAN][str(index)] = index_server_machine_param[i]
                index = index + 1
                monitor_param[JobPhaseNames.LIVE_SCAN][str(index)] = index_server_param[i]
                index = index + 1
            if access_node is None:
                raise Exception("Access node is empty")
            access_node_param = self.form_client_monitor_param(client_name=access_node,
                                                               phase_name=JobPhaseNames.LIVE_SCAN,
                                                               counters=counters[CounterTypes.PROCESS_COUNTER])
            monitor_param[JobPhaseNames.LIVE_SCAN][str(index)] = access_node_param
            index = index + 1
            access_node_machine_param = self.form_client_monitor_param(
                client_name=access_node, phase_name=JobPhaseNames.DUMMY_EMPTY,
                counters=counters[CounterTypes.MACHINE_COUNTER])
            monitor_param[JobPhaseNames.LIVE_SCAN][str(index)] = access_node_machine_param

        self.log.info(f"Final configurations formed : {monitor_param}")

        return monitor_param

    def find_fs_extract_duration_stats(self, data_source_name):
        """fetches the file system extract duration stats for each file type

        Args:

            data_source_name            (str)       --  name of the data source

        Returns:

            dict        --      containing extract duration stats for each file type

        Raises

            Exception:

                    if failed to fetch extract duration stats

        """
        ds_obj = self.commcell.datacube.datasources.get(data_source_name)
        index_server_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
        self.log.info(f"Index server object initialised for cloud id : {ds_obj.index_server_cloud_id}")
        file_type_query = {
            dynamic_constants.FACET_PARAM: 'true',
            dynamic_constants.FACET_FIELD_SET_PARAM: dynamic_constants.FIELD_FILE_EXTENSION,
            dynamic_constants.ROWS_PARAM: 0
        }
        resp = index_server_obj.execute_solr_query(
            core_name=ds_obj.computed_core_name,
            select_dict={
                GeneralConstants.COLUMN_DATA_SOURCE_NAME: f"\"{data_source_name}\""},
            op_params=file_type_query)
        file_type_list = \
            resp[dynamic_constants.FACET_COUNTS_PARAM][dynamic_constants.FACET_FIELDS_PARAM][dynamic_constants.FIELD_FILE_EXTENSION]
        del file_type_list[1::2]  # drop all even index
        self.log.info(f"Total file types found for stats analysis : {len(file_type_list)}")
        output = {}
        for file_type in file_type_list:
            if file_type is None or file_type == '':
                continue
            self.log.info(f"Going to get stats for File Extension : {file_type}")
            stats_query = {
                dynamic_constants.STATS_PARAM: 'true',
                dynamic_constants.STATS_FIELD_SET_PARAM: dynamic_constants.FIELD_EXTRACT_DURATION,
                dynamic_constants.ROWS_PARAM: 0
            }
            resp = index_server_obj.execute_solr_query(
                core_name=ds_obj.computed_core_name, select_dict={
                    dynamic_constants.FIELD_FILE_EXTENSION: f"\"{file_type}\"",
                    GeneralConstants.COLUMN_DATA_SOURCE_NAME: f"\"{data_source_name}\""}, op_params=stats_query)
            min_value = \
                resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][dynamic_constants.FIELD_EXTRACT_DURATION][
                    dynamic_constants.MIN_PARAM]
            max_value = \
                resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][dynamic_constants.FIELD_EXTRACT_DURATION][
                    dynamic_constants.MAX_PARAM]
            mean_value = \
                resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][dynamic_constants.FIELD_EXTRACT_DURATION][
                    dynamic_constants.MEAN_PARAM]
            count_value = \
                resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][
                    dynamic_constants.FIELD_EXTRACT_DURATION][dynamic_constants.COUNT_PARAM]
            if int(count_value) != 0:
                output[file_type] = {
                    f"Total Doc {dynamic_constants.COUNT_PARAM}": f"{count_value}",
                    dynamic_constants.MIN_PARAM: f"{min_value} Ms",
                    dynamic_constants.MAX_PARAM: f"{max_value} Ms",
                    dynamic_constants.MEAN_PARAM: f"{mean_value} Ms"
                }
                self.log.info(f"Stats got for this file type : {file_type}")
                self.print_config(config_data=output[file_type])
            else:
                output[file_type] = "Unsupported file type for extraction"
                self.log.info(f"Unsupported file extension for SearchText Extraction : {file_type}")

        return output

    def find_min_max_for_netstat(self, config, build_id):
        """finds min/max values for the netstat of given config and build id

        Args:

            config              (dict)      --  monitor client/process config dict

                        Example : {

                                    "client": "xyz",
                                    "binary": "Machine",
                                    "platform": "Windows",
                                    "countertype": "Machine"
                                }

            build_id            (str)       --  Automation run's build id

        Returns:

            dict        --  containing min/max values for netstat

        """
        counter_type = config[GeneralConstants.COUNTER_TYPE_PARAM]
        platform = config[GeneralConstants.PLATFORM_PARAM]
        binary = config[GeneralConstants.BINARY_PARAM]
        client_name = config[GeneralConstants.CLIENT_PARAM]
        output = {}
        ds_obj = None
        states = []
        if platform.lower() == Platforms.Unix.lower():
            states = GeneralConstants.NETSTAT_STATE_LIST_UNIX
        else:
            states = GeneralConstants.NETSTAT_STATE_LIST_WINDOWS
        self.log.info(f"Netstat States - {states}")
        criteria_query = {
            GeneralConstants.COLUMN_BUILD_ID: f"\"{build_id}\"",
            GeneralConstants.COLUMN_MACHINE_NAME: f"\"{client_name}\"",
            GeneralConstants.COLUMN_COMMSERV_VERSION: f"\"{self.commcell.version}\""
        }
        if counter_type == CounterTypes.MACHINE_COUNTER:
            self.log.info(f"Machine NetStat detected for Min/Max Calculation")
            ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Machine_Data_Source_Name)

        else:
            self.log.info(f"Process NetStat detected for Min/Max Calculation")
            ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Process_Data_Source_Name)
            criteria_query[GeneralConstants.COLUMN_BINARY] = f"\"{binary}\""
        index_server_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
        self.log.info(f"DataSource/Index Server class initialised")
        for state in states:
            self.log.info(f"Going to find Min/Max for state : {state}")
            stats_query = {
                dynamic_constants.STATS_PARAM: 'true',
                dynamic_constants.STATS_FIELD_SET_PARAM: state,
                dynamic_constants.ROWS_PARAM: 0
            }
            criteria_query[f"-{state}"] = 0  # add not query to leave all zero values
            resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                       select_dict=criteria_query,
                                                       op_params=stats_query)
            criteria_query.pop(f"-{state}")  # remove the counter
            min_value = \
                resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][state][
                    dynamic_constants.MIN_PARAM]
            max_value = resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][state][
                dynamic_constants.MAX_PARAM]
            mean_value = resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][state][
                dynamic_constants.MEAN_PARAM]

            if (min_value is None or min_value == 0) and (max_value is None or max_value == 0):
                self.log.info(f"Skip adding for state : {state}")
            else:
                output[state] = {
                    dynamic_constants.MIN_PARAM: f"{min_value}",
                    dynamic_constants.MAX_PARAM: f"{max_value}",
                    dynamic_constants.MEAN_PARAM: f"{int(mean_value)}"
                }
                self.log.info(f"Min/Max NetStat results")
                self.print_config(config_data=output[state])

        return output

    def find_min_max_for_counters(self, config, build_id):
        """finds min/max values for the each performance counters of given config and build id

        Args:

            config              (dict)      --  monitor client/process config dict

                        Example : {

                                    "client": "xyz",
                                    "binary": "Machine",
                                    "counters": ["\\Processor(_Total)\\% Processor Time"],
                                    "platform": "Windows",
                                    "countertype": "Machine"
                                }

            build_id            (str)       --  Automation run's build id

        Returns:

            dict        --  containing min/max values for each counters in the config

        """
        counter_type = config[GeneralConstants.COUNTER_TYPE_PARAM]
        platform = config[GeneralConstants.PLATFORM_PARAM]
        counters = config[GeneralConstants.COUNTERS_PARAM]
        binary = config[GeneralConstants.BINARY_PARAM]
        client_name = config[GeneralConstants.CLIENT_PARAM]
        ds_obj = None
        output = {}
        criteria_query = {
            GeneralConstants.COLUMN_BUILD_ID: f"\"{build_id}\"",
            GeneralConstants.COLUMN_MACHINE_NAME: f"\"{client_name}\"",
            GeneralConstants.COLUMN_COMMSERV_VERSION: f"\"{self.commcell.version}\""
        }
        if counter_type == CounterTypes.MACHINE_COUNTER:
            self.log.info(f"Machine counter detected for Min/Max Calculation")
            ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Machine_Data_Source_Name)

        else:
            self.log.info(f"Process counter detected for Min/Max Calculation")
            ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Process_Data_Source_Name)
            criteria_query[GeneralConstants.COLUMN_BINARY] = f"\"{binary}\""
        index_server_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
        self.log.info(f"DataSource/Index Server class initialised")
        for counter in counters:
            convert = False
            unit = ''
            if counter in (WindowsProcessCounters.PROCESS_PID, UnixProcessCounters.PROCESS_PID):
                continue
            if counter_type == CounterTypes.PROCESS_COUNTER:
                if counter not in (
                        WindowsProcessCounters.PROCESS_THREAD_COUNT,
                        WindowsProcessCounters.PROCESS_HANDLE_COUNT,
                        WindowsProcessCounters.PROCESS_CPU,
                        UnixProcessCounters.PROCESS_HANDLE_COUNT,
                        UnixProcessCounters.PROCESS_THREAD_COUNT,
                        UnixProcessCounters.PROCESS_CPU):
                    convert = True
                    unit = 'MB'
            else:
                if counter in (WindowsMachineCounters.MACHINE_AVAILABLE_MEMORY_IN_MB,
                               UnixMachineCounters.MACHINE_AVAILABLE_MEMORY_IN_MB):
                    unit = 'MB'
            if platform.lower() == Platforms.Windows.lower():
                counter = counter.split("\\")[-1]
            solr_field = GeneralConstants.COUNTERS_FIELD_MAPPING[counter]
            self.log.info(f"Going to find Min/Max for solr field : {solr_field}")

            stats_query = {
                dynamic_constants.STATS_PARAM: 'true',
                dynamic_constants.STATS_FIELD_SET_PARAM: solr_field,
                dynamic_constants.ROWS_PARAM: 0
            }
            criteria_query[f"-{solr_field}"] = 0  # add not query to leave all zero values
            resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                       select_dict=criteria_query,
                                                       op_params=stats_query)
            criteria_query.pop(f"-{solr_field}")  # remove the counter
            min_value = \
                resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][solr_field][dynamic_constants.MIN_PARAM]
            max_value = resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][solr_field][
                dynamic_constants.MAX_PARAM]
            mean_value = resp[dynamic_constants.STATS_PARAM][dynamic_constants.STATS_FIELD_PARAM][solr_field][
                dynamic_constants.MEAN_PARAM]

            # convert it to MB in report
            if convert:
                if min_value is not None:
                    min_value = int(min_value / 1048576)
                if max_value is not None:
                    max_value = int(max_value / 1048576)
                if mean_value is not None and not isinstance(mean_value, str):
                    mean_value = int(mean_value / 1048576)

            # round it off to 2 decimals
            if min_value is not None and isinstance(min_value, float):
                min_value = round(min_value, 2)
            if max_value is not None and isinstance(max_value, float):
                max_value = round(max_value, 2)
            if mean_value is not None and isinstance(mean_value, float):
                mean_value = round(mean_value, 2)

            output[solr_field] = {
                dynamic_constants.MIN_PARAM: f"{min_value}{unit}",
                dynamic_constants.MAX_PARAM: f"{max_value}{unit}",
                dynamic_constants.MEAN_PARAM: f"{mean_value}{unit}"
            }
            self.log.info(f"Min/Max counters results")
            self.print_config(config_data=output[solr_field])
        return output

    def fetch_data_source_crawl_stats(self, data_source_name, client_id=None):
        """ fetches the crawl stats for the given data source name

        Args:

            data_source_name        (str)       --  name of the data source

            client_id               (str)       --  client id which needs to applied as filter

        Returns:

            dict    --  containing crawl job stats info

        Raises

            Exception:

                    if input data type is not valid

        """
        if not isinstance(data_source_name, str):
            raise Exception("Input data type is not valid")
        select_dict = {GeneralConstants.COLUMN_DATA_SOURCE_NAME: f"\"{data_source_name}\""}
        if client_id:
            select_dict = {GeneralConstants.COLUMN_CLIENT_ID: f"\"{client_id}\""}
        success_dict = {** select_dict, **dynamic_constants.QUERY_CISTATE_ITEMSTATE_SUCCESS}
        skip_dict = {** select_dict, **dynamic_constants.QUERY_CISTATE_SKIPPED}
        ca_success_dict = {**select_dict, **dynamic_constants.QUERY_CASTATE_SUCCESS}
        ds_obj = self.commcell.datacube.datasources.get(data_source_name)
        index_server_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
        self.log.info(f"Index server object initialised for cloud id : {ds_obj.index_server_cloud_id}")
        resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                   select_dict=select_dict,
                                                   op_params=dynamic_constants.QUERY_ZERO_ROWS)
        total_docs = int(resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM])
        self.log.info(f"Total docs for this Data Source : {total_docs}")
        resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                   select_dict=success_dict,
                                                   op_params=dynamic_constants.QUERY_ZERO_ROWS)
        ci_success = int(resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM])

        resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                   select_dict=skip_dict,
                                                   op_params=dynamic_constants.QUERY_ZERO_ROWS)
        ci_skipped = int(resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM])

        ci_failed = total_docs - ci_success - ci_skipped
        self.log.info(f"Success docs for CI : {ci_success}. Failed docs for CI : {ci_failed}"
                      f" Skipped docs for CI : {ci_skipped}")
        resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                   select_dict=ca_success_dict,
                                                   op_params=dynamic_constants.QUERY_ZERO_ROWS)
        ca_success = int(resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM])
        ca_failed = total_docs - ca_success
        self.log.info(f"Success docs for CA : {ca_success}. Failed docs for CA : {ca_failed}")
        output = {
            GeneralConstants.DYNAMIC_COLUMN_TOTAL_DOCS: total_docs,
            GeneralConstants.DYNAMIC_COLUMN_SUCCESS_DOCS: ci_success,
            GeneralConstants.DYNAMIC_COLUMN_FAILED_DOCS: ci_failed,
            GeneralConstants.DYNAMIC_COLUMN_SKIPPED_DOCS: ci_skipped,
            GeneralConstants.DYNAMIC_COLUMN_CA_SUCCESS_DOCS: ca_success,
            GeneralConstants.DYNAMIC_COLUMN_CA_FAILED_DOCS: ca_failed
        }
        return output

    def read_json_file(self, json_file):
        """ Opens the json file and loads into dict

        Args:

            json_file           (str)       --  json file path

        Returns:

            dict  -- JSON data from the file

        Raises:

            Exception:

                    if failed to read the file

        """
        with open(json_file) as in_file:
            return json.load(in_file)

    def dump_json_to_file(self, json_data, out_file):
        """ dumps the given JSON dict to the output file given

        Args:

            json_data       (dict)      --  Data to be dumped to the file

            out_file        (str)       --  Output file path

        Returns:

            None

        """
        self.log.info(f"Dumping Json data in to the file : {out_file}")
        with open(out_file, GeneralConstants.FILE_WRITE_MODE) as outfile:
            json.dump(json_data, outfile)
        self.log.info(f"Json Data saved successfully to Json file - {out_file}")

    def remove_invalid_counters(self, counters, platform, counter_type):
        """removes invalid counters for the client based on the platform type provided

        Args:

            counters            (list)      --  list of counters

            platform            (str)       --  platform type of client

            counter_type        (str)       --  type of counter

        Returns:

            list        --  valid counters for the client and platform provided

        """

        class_name = None
        if Platforms.Windows.lower() == platform.lower():
            if counter_type == CounterTypes.PROCESS_COUNTER:
                class_name = GeneralConstants.WINDOWS_PROCESS_COUNTER
            else:
                class_name = GeneralConstants.WINDOWS_MACHINE_COUNTER
        else:
            if counter_type == CounterTypes.PROCESS_COUNTER:
                class_name = GeneralConstants.UNIX_PROCESS_COUNTER
            else:
                class_name = GeneralConstants.UNIX_MACHINE_COUNTER
        class_dict = {
            GeneralConstants.WINDOWS_PROCESS_COUNTER: WindowsProcessCounters,
            GeneralConstants.WINDOWS_MACHINE_COUNTER: WindowsMachineCounters,
            GeneralConstants.UNIX_PROCESS_COUNTER: UnixProcessCounters,
            GeneralConstants.UNIX_MACHINE_COUNTER: UnixMachineCounters
        }
        class_obj = class_dict[class_name]
        remove_counter = []
        for counter in counters:
            if counter not in class_obj.COUNTER_VALUES:
                remove_counter.append(counter)
        set_difference = set(counters) - set(remove_counter)
        counters = list(set_difference)
        self.log.info(f"Removed invalid counters - {remove_counter}")
        self.log.info(f"Final valid counters returned : {counters}")
        return counters

    def form_client_monitor_param(self, client_name, phase_name, counters=None, **kwargs):
        """ forms the client monitor performance config based on inputs

        Args:

            client_name             (str)       --  name of the client

            phase_name              (str)       --  Job phase name

            Note : set this to JobphaseNames.DUMMY_EMPTY in case if we want to form performance counter for machine

            counters                (list)      --  list containing performance counters which needs to be monitored

                                                if none, default counters are selected

            kwargs                              --  optional argument

                    appname         --  cvods process appname command line param

                    username        --  username to connect to machine in case of non-commvault client

                    password        --  password used to connect to machine in case of non-commvault client

        Returns:

            dict    --  containing performance config needed to monitor stats for a client/Process

                Example : {
                            'client': 'xyz',
                            'binary': {'Windows': 'IFind.exe'},
                            'counters': ['\\Process(%s*)\\Handle Count', '\\Process(%s*)\\Thread Count'],
                            'platform': 'UNIX',
                            'statsfolder': '/Users/root/commvault_automation/Automation_Performance_Data'},
                            'cmdlineparams':'-j ',
                            'portusagestats' : True,
                            # below fields are applicable for non-commvault client alone
                            'client_username':<username>,
                            'client_password':<password>

                        }

        """
        if not isinstance(client_name, str):
            raise Exception("Input data type is not valid")
        if counters is None:
            if phase_name == JobPhaseNames.DUMMY_EMPTY:
                # Machine counters
                counters = WindowsMachineCounters.COUNTER_VALUES + UnixMachineCounters.COUNTER_VALUES
            else:
                # process counters
                counters = WindowsProcessCounters.COUNTER_VALUES + UnixProcessCounters.COUNTER_VALUES
            self.log.info(f"No input for counters so Adding All counters by Default - {counters}")
        local_counters = copy.deepcopy(counters)
        client_obj = None
        machine_obj = None
        is_cvlt_client = False
        instance = None
        install_dir = None
        if self.commcell.clients.has_client(client_name):
            is_cvlt_client = True
        machine_cache_key = f"{client_name}{GeneralConstants.MACHINE_OBJ_CACHE}"
        if self.cache_obj.is_exists(key=machine_cache_key):
            machine_obj = self.cache_obj.get_key(key=machine_cache_key)
            # if commvault client, find instance and install dir
            if is_cvlt_client:
                client_obj = self.commcell.clients.get(client_name)
                instance = client_obj.instance
                install_dir = client_obj.install_directory
        else:
            # key not present in cache. Create it
            if is_cvlt_client:
                self.log.info(f"It is a commvault client - {client_name}")
                client_obj = self.commcell.clients.get(client_name)
                machine_obj = Machine(machine_name=client_obj, commcell_object=self.commcell)
                instance = client_obj.instance
                install_dir = client_obj.install_directory
            else:
                self.log.info(f"It is a Non-commvault client - {client_name}")
                machine_obj = Machine(machine_name=client_name, commcell_object=self.commcell,
                                      username=kwargs.get(GeneralConstants.USERNAME_PARAM),
                                      password=kwargs.get(GeneralConstants.PASSWORD_PARAM))
            self.cache_obj.put_key(key=machine_cache_key, value=machine_obj)
        binary_name = None
        cmd_line = ""
        counter_type = CounterTypes.PROCESS_COUNTER
        if phase_name == JobPhaseNames.LIVE_SCAN:
            binary_name = Binary.I_FIND
            cmd_line = GeneralConstants.JOB_ID_CMD_LINE_PARAM
        elif phase_name == JobPhaseNames.CONTENT_PUSH:
            binary_name = Binary.CL_BACKUP
            cmd_line = GeneralConstants.JOB_ID_CMD_LINE_PARAM
        elif phase_name == JobPhaseNames.INDEX_EXTRACTION:
            binary_name = Binary.CV_DISTRIBUTOR
            cmd_line = GeneralConstants.JOB_ID_CMD_LINE_PARAM
        elif phase_name == JobPhaseNames.DUMMY_DATA_CUBE:
            binary_name = Binary.DATA_CUBE
            cmd_line = instance
        elif phase_name == JobPhaseNames.DUMMY_CONTENT_EXTRACTOR:
            binary_name = Binary.CONTENT_EXTRACTOR
            cmd_line = instance
        elif phase_name == JobPhaseNames.DUMMY_MESSAGE_QUEUE:
            binary_name = Binary.MESSAGE_QUEUE
            cmd_line = instance
        elif phase_name == JobPhaseNames.DUMMY_EXPORTER:
            binary_name = Binary.EXPORTER
            cmd_line = instance
        elif phase_name == JobPhaseNames.DUMMY_PYTHON:
            binary_name = Binary.PYTHON
            if machine_obj.os_info.lower() == Platforms.Windows.lower():
                cmd_line = 'anaconda'
            else:
                cmd_line = install_dir
        elif phase_name == JobPhaseNames.DUMMY_SEARCH_ENGINE:
            binary_name = Binary.SEARCH_ENGINE
            cmd_line = f"{GeneralConstants.CI_SERVER_SERVICE}{instance}"
        elif phase_name == JobPhaseNames.DUMMY_CVCI_ANALYTICS:
            binary_name = Binary.CVCI_ANALYTICS
            cmd_line = GeneralConstants.JOB_ID_CMD_LINE_PARAM
        elif phase_name == JobPhaseNames.DUMMY_CVD:
            binary_name = Binary.CVD
            cmd_line = f"{install_dir}{machine_obj.os_sep}{GeneralConstants.BASE_FOLDER}"
        elif phase_name == JobPhaseNames.DUMMY_AUX_COPY:
            binary_name = Binary.AUX_COPY
            cmd_line = GeneralConstants.JOB_ID_CMD_LINE_PARAM_OTHER
        elif phase_name == JobPhaseNames.DUMMY_AUX_COPY_MGR:
            binary_name = Binary.AUX_COPY_MGR
            cmd_line = GeneralConstants.JOB_ID_CMD_LINE_PARAM
        elif phase_name == JobPhaseNames.DUMMY_CVODS:
            binary_name = Binary.CVODS
            cmd_line = f"-{GeneralConstants.CVODS_APP_NAME} {kwargs.get(GeneralConstants.CVODS_APP_NAME)}"
        elif phase_name == JobPhaseNames.DUMMY_EMPTY:
            # performance stats is for machine level so binary name is Machine
            binary_name = CounterTypes.MACHINE_COUNTER
            counter_type = CounterTypes.MACHINE_COUNTER
        elif phase_name == JobPhaseNames.DUMMY_CLRESTORE:
            binary_name = Binary.CL_RESTORE
            cmd_line = GeneralConstants.JOB_TOKEN_CMD_LINE_PARAM
        elif phase_name == JobPhaseNames.DUMMY_INDEX_GATEWAY:
            binary_name = Binary.INDEX_GATEWAY
            cmd_line = GeneralConstants.INDEX_GATEWAY_COMMAND_LINE_KEYWORD
        drive_cache_lookup = f"{client_name}{GeneralConstants.DRIVE_CACHE}"
        drive = None
        if self.cache_obj.is_exists(key=drive_cache_lookup):
            drive = self.cache_obj.get_key(key=drive_cache_lookup)
        else:
            option_obj = OptionsSelector(self.commcell)
            drive = f"{option_obj.get_drive(machine=machine_obj)}{GeneralConstants.FOLDER_NAME}{machine_obj.os_sep}" \
                    f"{client_name}"
            self.cache_obj.put_key(key=drive_cache_lookup, value=drive)

        platform = None
        if machine_obj.os_info.lower() == Platforms.Windows.lower():
            platform = Platforms.Windows
            if binary_name != CounterTypes.MACHINE_COUNTER:
                # Add PID as default counters to all request. we need PID so that we drop unwanted process stats from
                # pushing into open data source in multi instancing setup
                if WindowsProcessCounters.PROCESS_PID not in local_counters:
                    local_counters.append(WindowsProcessCounters.PROCESS_PID)
                # remove non windows counters from the list
                local_counters = self.remove_invalid_counters(counters=local_counters,
                                                              counter_type=CounterTypes.PROCESS_COUNTER,
                                                              platform=platform)
            else:
                local_counters = self.remove_invalid_counters(counters=local_counters,
                                                              counter_type=CounterTypes.MACHINE_COUNTER,
                                                              platform=platform)
        else:
            platform = Platforms.Unix
            if binary_name != CounterTypes.MACHINE_COUNTER:
                # Add PID as default counters to all request. we need PID so that we drop unwanted process stats from
                # pushing into open data source in multi instancing setup
                if UnixProcessCounters.PROCESS_PID not in local_counters:
                    local_counters.append(UnixProcessCounters.PROCESS_PID)
                # remove windows counters from the list
                local_counters = self.remove_invalid_counters(counters=local_counters,
                                                              counter_type=CounterTypes.PROCESS_COUNTER,
                                                              platform=platform)
            else:
                local_counters = self.remove_invalid_counters(counters=local_counters,
                                                              counter_type=CounterTypes.MACHINE_COUNTER,
                                                              platform=platform)
        param = {
            GeneralConstants.CLIENT_PARAM: client_name,
            GeneralConstants.BINARY_PARAM: binary_name[platform] if binary_name != CounterTypes.MACHINE_COUNTER else binary_name,
            GeneralConstants.COUNTERS_PARAM: local_counters,
            GeneralConstants.PLATFORM_PARAM: platform,
            GeneralConstants.STATS_FOLDER_PARAM: f"{drive}",
            GeneralConstants.COMMAND_LINE_PARAM: cmd_line,
            GeneralConstants.COUNTER_TYPE_PARAM: counter_type,
            GeneralConstants.PORT_USAGE_PARAM: CustomCounters.CAPTURE_NETWORK_PORT_USAGE}
        if not is_cvlt_client:
            param[GeneralConstants.USERNAME_PARAM] = kwargs.get(GeneralConstants.USERNAME_PARAM)
            param[GeneralConstants.PASSWORD_PARAM] = kwargs.get(GeneralConstants.PASSWORD_PARAM)
        self.log.info(f"Client Param Formed ")
        self.print_config(config_data=param)
        return param

    def print_config(self, config_data):
        """  prints the config data on log

        Args:

            config_data         (dict)      --      config data which needs to be logged

        Returns:

            None

        """
        self.log.info(f"*********************************************************************************************")
        for param in config_data:
            self.log.info(f"{param} - {config_data[param]}")
        self.log.info(f"*********************************************************************************************")

    def form_sdg_fs_monitor_param(
            self,
            job_type,
            counters=None,
            index_server=None,
            access_node=None,
            content_analyzer=None,
            search_engine=None,
            media_agent=None,
            is_tika=True):
        """ forms performance monitor config required for FS data source crawl job in SDG activate

        Args:

            job_type                    (int)       --      type of job
                                                                Example : defined in JobTypes in constants.py

            index_server                (str)       --      Index server name

            access_node                 (str)       --      Access node client name

            content_analyzer            (str/list)   --      Content Analyzer client name/s

            counters                    (dict)      --      Windows/Unix counters

                                    Example : {
                                                'Process' : [Memory,Handle]
                                                'Machine' : [Memory,CPU]
                                             }

                    if None, then all counters will be selected for monitoring

            search_engine               (list)      --      list of search engine client names

            media_agent                 (str)       --      Media agent client name

            is_tika                     (bool)      --      specifies whether it is tika or stellant based extraction

        Returns:

            dict    --  containing attributes needed for performance monitoring

    Example : {
                'Live Scan': {
                                '1': {
                                        'client': 'dez',
                                        'binary': {'Windows': 'IFind.exe'},
                                        'counters': ['\\Process(%s*)\\Handle Count', '\\Process(%s*)\\Thread Count'],
                                        'platform': 'UNIX',
                                        'statsfolder': '/Users/root/commvault_automation/Automation_Performance_Data'}
                                        'cmdlineparams': "-j ",
                                        'portusagestats' : True,
                                        # below fields are applicable for non-commvault client alone
                                        'client_username':<username>,
                                        'client_password':<password>
                                    }
                'Content Push': {
                                '1': {
                                        'client': 'tyr',
                                        'binary': {'Windows': 'CLBackup.exe'},
                                        'counters': ['\\Process(%s*)\\Handle Count', '\\Process(%s*)\\Thread Count'],
                                        'platform': 'UNIX',
                                        'statsfolder': '/Users/root/commvault_automation/Automation_Performance_Data'},
                                        'cmdlineparams':"-j ",
                                        'portusagestats' : True,
                                        # below fields are applicable for non-commvault client alone
                                        'client_username':<username>,
                                        'client_password':<password>

                                    }
                }
            }

        """

        if not isinstance(index_server, str):
            raise Exception("Input data type is not valid")
        if isinstance(content_analyzer, str):
            content_analyzer = [content_analyzer]
        if counters is None:
            counters = {
                CounterTypes.MACHINE_COUNTER:
                    WindowsMachineCounters.COUNTER_VALUES + UnixMachineCounters.COUNTER_VALUES,
                CounterTypes.PROCESS_COUNTER:
                    WindowsProcessCounters.COUNTER_VALUES + UnixProcessCounters.COUNTER_VALUES}
            self.log.info(f"No input for counters so Adding All counters by Default - {counters}")
        self.log.info("Going to form file system monitor params based on user inputs")
        index_server_obj = self.commcell.index_servers.get(index_server)
        index_server_client_list = copy.deepcopy(index_server_obj.client_name)
        self.log.info(f"Index server Initialised. Total index server nodes : {len(index_server_client_list)}")
        monitor_param = {}
        # Add Machine counters
        self.log.info("Forming performance params for machine counters")
        access_node_machine_param = None
        if job_type in JobTypes.ONLINE_CRAWL_JOB:
            access_node_machine_param = self.form_client_monitor_param(client_name=access_node,
                                                                       phase_name=JobPhaseNames.DUMMY_EMPTY,
                                                                       counters=counters[CounterTypes.MACHINE_COUNTER])
            self.log.info("Access node machine configuration formed")
        index_server_machine_param = []
        if job_type in JobTypes.DATA_SOURCE_SUPPORTED_JOB_TYPES:
            for node in index_server_client_list:
                index_server_machine_param.append(self.form_client_monitor_param(
                    client_name=node, phase_name=JobPhaseNames.DUMMY_EMPTY,
                    counters=counters[CounterTypes.MACHINE_COUNTER]))
            self.log.info("Index server machine configuration formed")

        content_analyzer_machine_params = []
        amq_params = []
        ca_params = []
        exporter_params = []
        python_params = []
        cv_distributor_params = []
        cvods_params = []
        clrestore_params = []
        gateway_params = []

        if content_analyzer is not None:
            for ca_node in content_analyzer:
                if ca_node not in index_server_client_list:
                    self.log.info("Index server and Content Analyzer are different machines. "
                                  "Forming separate machine counters")
                    content_analyzer_machine_params.append(self.form_client_monitor_param(
                        client_name=ca_node,
                        phase_name=JobPhaseNames.DUMMY_EMPTY,
                        counters=counters[
                            CounterTypes.MACHINE_COUNTER]))

        # Add common Process counters
        index_server_param = []
        for node in index_server_client_list:
            index_server_param.append(self.form_client_monitor_param(
                client_name=node,
                phase_name=JobPhaseNames.DUMMY_DATA_CUBE,
                counters=counters[CounterTypes.PROCESS_COUNTER]))
        live_scan_param = None
        if job_type in JobTypes.ONLINE_CRAWL_JOB:
            live_scan_param = self.form_client_monitor_param(
                client_name=access_node,
                phase_name=JobPhaseNames.LIVE_SCAN,
                counters=counters[CounterTypes.PROCESS_COUNTER])
        if job_type in (JobTypes.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT,
                        JobTypes.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT_WITH_EE):
            self.log.info(f"Forming basic performance params for FS DataSource with content Crawl")
            cl_backup_param = self.form_client_monitor_param(
                client_name=access_node,
                phase_name=JobPhaseNames.CONTENT_PUSH,
                counters=counters[CounterTypes.PROCESS_COUNTER])
            # content push alone online job
            if content_analyzer is None and job_type == JobTypes.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_CONTENT:
                # this case is for datacube crawl. Always use first node of index server
                if len(index_server_client_list) > 1:
                    raise Exception("Not a supported configurations for this job type")
                ca_params.append(self.form_client_monitor_param(
                    client_name=index_server_client_list[0],
                    phase_name=JobPhaseNames.DUMMY_CONTENT_EXTRACTOR,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                if not is_tika:
                    exporter_params.append(self.form_client_monitor_param(
                        client_name=index_server_client_list[0],
                        phase_name=JobPhaseNames.DUMMY_EXPORTER,
                        counters=counters[CounterTypes.PROCESS_COUNTER]))
                    amq_params.append(self.form_client_monitor_param(
                        client_name=index_server_client_list[0],
                        phase_name=JobPhaseNames.DUMMY_MESSAGE_QUEUE,
                        counters=counters[CounterTypes.PROCESS_COUNTER]))
            else:
                self.log.info(f"FS DataSource with Entity Extraction Enabled. Forming CA attributes")
                if content_analyzer is None:
                    raise Exception("CA can't be NULL for this type of JOB with Entity Extraction Enabled")
                for ca_node in content_analyzer:
                    amq_params.append(self.form_client_monitor_param(
                        client_name=ca_node,
                        phase_name=JobPhaseNames.DUMMY_MESSAGE_QUEUE,
                        counters=counters[CounterTypes.PROCESS_COUNTER]))
                    ca_params.append(self.form_client_monitor_param(
                        client_name=ca_node,
                        phase_name=JobPhaseNames.DUMMY_CONTENT_EXTRACTOR,
                        counters=counters[CounterTypes.PROCESS_COUNTER]))
                    if not is_tika:
                        exporter_params.append(self.form_client_monitor_param(
                            client_name=ca_node,
                            phase_name=JobPhaseNames.DUMMY_EXPORTER,
                            counters=counters[CounterTypes.PROCESS_COUNTER]))
                    python_params.append(self.form_client_monitor_param(
                        client_name=ca_node,
                        phase_name=JobPhaseNames.DUMMY_PYTHON,
                        counters=counters[CounterTypes.PROCESS_COUNTER]))

            monitor_param = {
                JobPhaseNames.LIVE_SCAN: {
                    '1': live_scan_param,
                    '2': access_node_machine_param},
                JobPhaseNames.CONTENT_PUSH: {
                    '1': cl_backup_param,
                    '2': access_node_machine_param if access_node_machine_param is not None else {},
                }}
            index = len(monitor_param[JobPhaseNames.CONTENT_PUSH]) + 1
            for ca_param in ca_params:
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index)] = ca_param
                index += 1
            for content_analyzer_machine_param in content_analyzer_machine_params:
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index)] = content_analyzer_machine_param
                index += 1
            for exporter_param in exporter_params:
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index)] = exporter_param
                index += 1
            for python_param in python_params:
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index)] = python_param
                index += 1
            for amq_param in amq_params:
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index)] = amq_param
                index += 1
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index)] = index_server_machine_param[i]
                monitor_param[JobPhaseNames.CONTENT_PUSH][str(index+1)] = index_server_param[i]
                index += + 2
        elif job_type == JobTypes.FILE_SYSTEM_ONLINE_CRAWL_JOB_WITH_METADATA_ONLY:
            self.log.info("Metadata only Crawl")
            monitor_param = {
                JobPhaseNames.LIVE_SCAN: {
                    '1': live_scan_param,
                    '2': access_node_machine_param
                }
            }
            index = len(monitor_param[JobPhaseNames.LIVE_SCAN]) + 1
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.LIVE_SCAN][str(index)] = index_server_machine_param[i]
                index = index + 1
                monitor_param[JobPhaseNames.LIVE_SCAN][str(index)] = index_server_param[i]
                index = index + 1
        elif job_type == JobTypes.FILE_SYSTEM_BACKUP_INDEX_EXTRACTION:
            self.log.info(f"Index Extraction job")
            for ca_node in content_analyzer:
                amq_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_MESSAGE_QUEUE,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                if not is_tika:
                    exporter_params.append(self.form_client_monitor_param(
                        client_name=ca_node,
                        phase_name=JobPhaseNames.DUMMY_EXPORTER,
                        counters=counters[CounterTypes.PROCESS_COUNTER]))
                self.log.info(f"Exporter param formed")
                ca_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_CONTENT_EXTRACTOR,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                self.log.info(f"Content Extractor param formed")
                cv_distributor_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.INDEX_EXTRACTION,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                cvods_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_CVODS,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                clrestore_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_CLRESTORE,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                gateway_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_INDEX_GATEWAY,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                python_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_PYTHON,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                self.log.info(f"Content Analyser  - Python  param formed")
            index_server_cvd_param = []
            for node in index_server_client_list:
                index_server_cvd_param.append(self.form_client_monitor_param(
                    client_name=node, phase_name=JobPhaseNames.DUMMY_CVD,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
            self.log.info(f"Index server CVD param formed")
            ma_machine_param = self.form_client_monitor_param(client_name=media_agent,
                                                              phase_name=JobPhaseNames.DUMMY_EMPTY,
                                                              counters=counters[
                                                                  CounterTypes.MACHINE_COUNTER])
            self.log.info(f"MA Machine param formed")
            monitor_param = {
                JobPhaseNames.INDEX_EXTRACTION: {
                    '1': ma_machine_param if ma_machine_param is not None else {},
                }
            }
            index = len(monitor_param[JobPhaseNames.INDEX_EXTRACTION]) + 1
            for i in range(len(content_analyzer)):
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = ca_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+1)] = content_analyzer_machine_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+2)] = python_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+3)] = amq_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+4)] = cv_distributor_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+5)] = cvods_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+6)] = clrestore_params[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+7)] = gateway_params[i]
                index += 8
                if not is_tika:
                    monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = exporter_params[i]
                    index += 1
            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index)] = index_server_machine_param[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+1)] = index_server_param[i]
                monitor_param[JobPhaseNames.INDEX_EXTRACTION][str(index+2)] = index_server_cvd_param[i]
                index += 3
        elif job_type == JobTypes.FILE_SYSTEM_BACKUP_IMPORT_INDEX:
            self.log.info(f"Import index job from Search engine")
            if content_analyzer is None or search_engine is None:
                raise Exception("CA/Search engine is empty. Please check")
            for ca_node in content_analyzer:
                amq_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_MESSAGE_QUEUE,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                ca_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_CONTENT_EXTRACTOR,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                self.log.info(f"Content Extractor param formed")
                python_params.append(self.form_client_monitor_param(
                    client_name=ca_node,
                    phase_name=JobPhaseNames.DUMMY_PYTHON,
                    counters=counters[CounterTypes.PROCESS_COUNTER]))
                self.log.info(f"Content Analyser  - Python  param formed")

            mgr_service_param = self.form_client_monitor_param(
                client_name=self.commcell.commserv_client.name,
                phase_name=JobPhaseNames.DUMMY_CVODS,
                counters=counters[CounterTypes.PROCESS_COUNTER],
                **{GeneralConstants.CVODS_APP_NAME:
                                                                      GeneralConstants.ANALYTICS_MGR_SERVICE_NAME})
            self.log.info(f"Analytics Mgr Service - CVODS param formed")

            monitor_param = {
                JobPhaseNames.IMPORT_INDEX: {
                    '1': mgr_service_param if mgr_service_param is not None else {},
                }
            }
            index = len(monitor_param[JobPhaseNames.IMPORT_INDEX]) + 1

            for i in range(len(content_analyzer)):
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = ca_params[i]
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index+1)] = content_analyzer_machine_params[i]
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index+2)] = python_params[i]
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index+3)] = amq_params[i]
                index += 4

            for node in search_engine:
                self.log.info(f"Forming search engine param for search node : {node}")
                # process counters
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = self.form_client_monitor_param(
                    client_name=node, phase_name=JobPhaseNames.DUMMY_SEARCH_ENGINE,
                    counters=counters[CounterTypes.PROCESS_COUNTER])
                # Machine counters
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index+1)] = self.form_client_monitor_param(
                    client_name=node, phase_name=JobPhaseNames.DUMMY_EMPTY,
                    counters=counters[CounterTypes.MACHINE_COUNTER])
                index += 2

            for i in range(len(index_server_client_list)):
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index)] = index_server_machine_param[i]
                monitor_param[JobPhaseNames.IMPORT_INDEX][str(index+1)] = index_server_param[i]
                index += 2
        self.log.info(f"Final Performance attributes : {monitor_param}")
        return monitor_param
