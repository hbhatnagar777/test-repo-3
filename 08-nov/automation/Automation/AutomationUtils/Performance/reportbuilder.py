# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""This file contains helper functions for creating html reports for the given performance monitored job id

    ReportBuilder:

        __init__()                          --  Initialize the ReportBuilder class object

        form_commserv_details()             --  forms the commserv part of the html report

        form_job_details()                  --  forms the job details part of the html report

        form_machine_details()              --  forms the machine config details part of the html report

        form_monitor_details()              --  forms the monitored process/machine details of the html report

        add_line_breaks()                   --  adds the line breaks to the html report

        add_html_heading()                  --  adds the side h3 headings to the html report

        add_html_sub_heading()              --  adds the side h4 headings to the html report

        generate_report()                   --  generates the html report file and send mail(optional)

        create_table()                      --  creates table and adds to the html report

        remove_heading_suffix()             --  removes the heading suffix for the data source dynamic fields

        add_para()                          --  adds the input string as para to the html report

        add_unorder_list()                  --  adds the list to the html report as unordered

        export_graph_for_config()           --  exports the performance stats graph for the given config

        import_report()                     --  import default report and assign performance data source as dataset

        share_folder()                      --  shares the performance stats output folder on controller

        form_api_details()                  --  forms the API details part of the html report


"""

import os
import datetime
import xml.etree.cElementTree as ETree
import xml.sax.saxutils as saxutils
from AutomationUtils import logger
from AutomationUtils.mailer import Mailer
from AutomationUtils.machine import Machine
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from AutomationUtils.Performance.Utils.constants import JobTypes
from AutomationUtils.Performance.Utils.constants import JobPhases
from AutomationUtils.Performance.Utils.constants import CounterTypes
from AutomationUtils.Performance.Utils.constants import WindowsProcessCounters
from AutomationUtils.Performance.Utils.constants import UnixProcessCounters
from AutomationUtils.Performance.Utils.performance_helper import PerformanceHelper
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.utils import constants as dynamic_constants
from Web.API.Core.CommandCenter.reports import Reports
from Web.API import customreports
from Web.Common.exceptions import CVNotFound


class ReportBuilder():
    """contains helper functions related to html report generation for the monitored performance job"""

    def share_folder(self):
        """ shares the output performance stats folder on controller

        Args:

            None

        Returns:

            None

        """
        machine_obj = Machine()
        share_list = machine_obj.list_shares_on_network_path(network_path='',
                                                             username='',
                                                             password='')
        self.log.info(f"Share list - {share_list}")
        if GeneralConstants.FOLDER_NAME not in share_list:
            self.log.info(f"Sharing the folder - {GeneralConstants.FOLDER_NAME} to everyone")
            machine_obj.share_directory(share_name=GeneralConstants.FOLDER_NAME,
                                        directory=GeneralConstants.CONTROLLER_FOLDER_PATH)
            self.log.info(f"Sharing done successfully")
        else:
            self.log.info(f"Share already exists with that name - {GeneralConstants.FOLDER_NAME}. Nothing to do")

    def import_report(self):
        """ imports the default report xml and will assign open datasource as dataset to that report

        Args:

           None

        Returns:

            None

        """
        report_name = GeneralConstants.Automation_performance_Report_Name
        report_xml_path = GeneralConstants.REPORT_XML
        self.log.info(f"Report core API class initialised")
        try:
            self.api.get_report_definition_by_name(
                report_name=report_name, suppress=False)
            self.log.info(f"{report_name} - custom reports exists already.")
        except CVNotFound:
            self.log.info(f"Performance Report doesn't exists on this commcell. "
                          f"Going to import Report using xml file : {report_xml_path}")
            ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Machine_Data_Source_Name)
            handler_obj = ds_obj.ds_handlers.get(GeneralConstants.HANDLER_NAME)
            handler_id = handler_obj.handler_id
            ds_id = ds_obj.datasource_id
            self.log.info(f"Fetched Machine DataSource id - {ds_id} & Handler ID - {handler_id}")
            xml_tree = ETree.parse(report_xml_path)
            root = xml_tree.getroot()
            for page in root.iter(GeneralConstants.XML_REPORT_PAGE):
                ds_name = None
                page_name = page.find(GeneralConstants.XML_REPORT_PAGE_NAME).text
                self.log.info(f"Going to update Report's Page : {page_name}")
                if page_name == GeneralConstants.MACHINE_REPORT_PAGE:
                    ds_name = GeneralConstants.Machine_Data_Source_Name
                else:
                    ds_name = GeneralConstants.Process_Data_Source_Name
                ds_obj = self.commcell.datacube.datasources.get(ds_name)
                handler_obj = ds_obj.ds_handlers.get(GeneralConstants.HANDLER_NAME)
                handler_id = handler_obj.handler_id
                ds_id = ds_obj.datasource_id
                self.log.info(f"Fetched DataSource id - {ds_id} & Handler ID - {handler_id} for Page : {page_name}")
                ds_node = page.findall(GeneralConstants.DATA_SOURCE_ID_XML_FIND)
                ds_node[0].text = str(ds_id)
                handler_node = page.findall(GeneralConstants.HANDLER_ID_XML_FIND)
                handler_node[0].text = str(handler_id)
            xml_tree.write(report_xml_path)
            self.log.info(f"Xml updated correctly")
            self.rpt_api.import_custom_report_xml(rpt_path=report_xml_path)
            self.log.info(
                f"Import successful for Report xml : {report_xml_path}")

    def export_graph_for_config(self, config):
        """exports the performance stats graph for the given performance config param

        Args:

            config          (dict)      --  Client/Process monitor stats param

                        Example : {

                                    "client": "xyz",
                                    "binary": "Machine",
                                    "counters": ["\\Processor(_Total)\\% Processor Time"],
                                    "platform": "Windows",
                                    "statsfolder": "C:\\Automation_Performance_Data",
                                    "cmdlineparams": "",
                                    "countertype": "Machine"
                                }

        Returns:

            str     --  exported html file path

        """
        client_name = config[GeneralConstants.CLIENT_PARAM]
        binary = config[GeneralConstants.BINARY_PARAM]
        counter_type = config[GeneralConstants.COUNTER_TYPE_PARAM]
        self.log.info(f"Going to export report for the config - {config}")
        filters = None
        # Report name can be passed as report id. it will work
        report_id = GeneralConstants.Automation_performance_Report_Name
        self.log.info(f"Report core API class initialised")
        if binary == CounterTypes.MACHINE_COUNTER or counter_type == CounterTypes.MACHINE_COUNTER:
            self.log.info(
                f"Machine level counter. Using DataSource : {GeneralConstants.Machine_Data_Source_Name} "
                f"with report id : {report_id}")
            # forming filters which needs to applied on reports
            filters = f"pageName={GeneralConstants.MACHINE_REPORT_PAGE}" \
                      f"&" \
                      f"{GeneralConstants.MACHINE_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_COMMSERV_VERSION}-0=" \
                      f"{self.commcell.version}" \
                      f"&" \
                      f"{GeneralConstants.MACHINE_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_BUILD_ID}-0=" \
                      f"{self.build_id}" \
                      f"&" \
                      f"{GeneralConstants.MACHINE_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_MACHINE_NAME}-0=" \
                      f"{client_name}"
        else:
            self.log.info(
                f"Process level counter. Using DataSource : {GeneralConstants.Process_Data_Source_Name} "
                f"with report id : {report_id}")
            filters = f"pageName={GeneralConstants.PROCESS_REPORT_PAGE}" \
                      f"&" \
                      f"{GeneralConstants.PROCESS_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_COMMSERV_VERSION}-0=" \
                      f"{self.commcell.version}" \
                      f"&" \
                      f"{GeneralConstants.PROCESS_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_BUILD_ID}-0=" \
                      f"{self.build_id}" \
                      f"&" \
                      f"{GeneralConstants.PROCESS_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_MACHINE_NAME}-0=" \
                      f"{client_name}" \
                      f"&" \
                      f"{GeneralConstants.PROCESS_FILTER_ATTRIBUTE}{GeneralConstants.COLUMN_BINARY}-0=" \
                      f"{binary}"
        report_name = f"{client_name}_{binary}_{self.job_id}_{self.build_id}"
        report_file = self.rpt_api.export_report(
            report_id,
            GeneralConstants.REPORT_EXPORT_TYPE,
            self.export_html_folder_path,
            report_name,
            filters)
        report_name = f"{report_name}.{GeneralConstants.REPORT_EXPORT_TYPE}"
        path, file = os.path.split(report_file)
        file_path = os.path.join(path, report_name)
        if file_path != report_file and os.path.exists(file_path):
            os.remove(file_path)
            self.log.info(f"Removing older reports with same name as : {report_name}")
        os.rename(report_file, file_path)
        self.log.info(f"Successfully renamed report file as - {report_name}")
        return report_name

    def add_unorder_list(self, input_list):
        """ adds the given list as unordered list to the html report

        Args:

            input_list      (list)      --  items which needs to be added for unordered list on html report

        Returns:

            None
        """
        order = ETree.SubElement(self.body_element, self._ul_tag)
        for item in input_list:
            order_item = ETree.SubElement(order, self._li_tag)
            order_item.text = item

    def add_para(self, input, color):
        """ adds input string to para tag on the html report

        Args:

            input       (str)       --  Input para content

            color       (dict)      --  color

        Returns:

            None

        """
        para = ETree.SubElement(self.body_element, self._p_tag, color)
        para.text = input

    def remove_heading_suffix(self, heading):
        """removes the heading suffix which got added for solr dynamic fields if any

        Args:

            heading         (str)       --  Name of the header

        Returns:

            str     --  converted heading name

        """
        return heading.replace('_i', '').replace('_l', '').replace('_s', '')

    def create_table(self, header, values, is_horizontal):
        """ creates html table on the body

        Args:

            header          (list)      --  Table Header

            values          (dict/list) --  Table cell/row values

            is_horizontal   (bool)      --  specifies whether table is of horizontal or vertical
                                                if True, table will be formed n*2 where n= rows

        Returns:

            None

        """
        table = ETree.SubElement(self.body_element, self._table_tag, border="6")
        table_row = ETree.SubElement(table, self._tr_tag, bgcolor="#C1A8D0")
        for heading in header:
            table_header = ETree.SubElement(table_row, self._th_tag)
            table_header.text = self.remove_heading_suffix(heading=heading)
        if isinstance(values, dict):
            if is_horizontal:
                for key, value in values.items():
                    table_row = ETree.SubElement(table, self._tr_tag)
                    key_col = ETree.SubElement(table_row, self._td_tag)
                    key_col.text = str(key)
                    val_col = ETree.SubElement(table_row, self._td_tag)
                    val_col.text = str(value)
            else:
                table_row = ETree.SubElement(table, self._tr_tag)
                for heading in header:
                    val_col = ETree.SubElement(table_row, self._td_tag)
                    val_col.text = str(values[heading])
        elif isinstance(values, list):
            for value in values:
                table_row = ETree.SubElement(table, self._tr_tag)
                for heading in header:
                    # if value itself dict, then single cell split into multiple rows
                    if isinstance(value[heading], dict):
                        temp_dict = value[heading]
                        val_col = ETree.SubElement(table_row, self._td_tag)
                        gui_list = ETree.SubElement(val_col, self._ul_tag)
                        for element in temp_dict:
                            temp_value = f"{element} - {temp_dict[element]}"
                            list_element = ETree.SubElement(gui_list, self._li_tag)
                            list_element.text = temp_value

                    elif isinstance(value[heading], list):
                        temp_list = value[heading]
                        val_col = ETree.SubElement(table_row, self._td_tag)
                        gui_list = ETree.SubElement(val_col, self._ul_tag)
                        for element in temp_list:
                            list_element = ETree.SubElement(gui_list, self._li_tag)
                            list_element.text = element
                    else:
                        val_col = ETree.SubElement(table_row, self._td_tag)
                        if str(value[heading]).startswith(self._dummy_href):
                            modified_value = str(value[heading]).replace(self._dummy_href, "")
                            href = ETree.SubElement(val_col, self._href_tag, href=f"file:{modified_value}")
                            href.text = "Click Here to Open"
                        else:
                            val_col.text = str(value[heading])

    def add_html_heading(self, name, color):
        """adds the given name as h3 heading on the side in the html

        Args:
            name        (str)       --  Heading name

            color       (dict)      --  tag with color


        Returns:
            None

        """
        heading = ETree.SubElement(self.body_element, "h3", color)
        heading.text = name

    def add_html_sub_heading(self, name, color):
        """adds the given name as h4 heading on the side in the html

        Args:
            name        (str)       --  Heading name

            color       (dict)      --  tag with color


        Returns:
            None

        """
        heading = ETree.SubElement(self.body_element, "h4", color)
        heading.text = name

    def add_line_breaks(self, times):
        """adds the line breaks to the html report based on times specified

        Args:

            times       (int)   --  number of line breaks to be added

        Returns:

            None

        """
        for i in range(times):
            ETree.SubElement(self.body_element, self._br_tag)

    def __init__(self, commcell_object, job_id, job_type, build_id, use_data_source):
        """ initialise the ReportBuilder class

        Args:

            commcell_object             (obj)       --  commcell class object

            job_id                      (str)       --  performance monitored job id

            job_type                    (int)       --  job type
                                                            Example : defined in JobTypes in constants.py

            build_id                    (str)       --  build id for this automation run

            use_data_source             (bool)      --  whether to use data source or not during report generation

        """
        self.option_obj = OptionsSelector(commcell_object)
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.job_id = job_id
        self.job_type = job_type
        if job_type == JobTypes.TIME_BASED_JOB_MONITORING:
            self.job_id = GeneralConstants.TIMER_BASED_MONITOR
        self.build_id = build_id
        self.is_data_source = use_data_source
        # html elements
        self._table_tag = 'table'
        self._th_tag = 'th'
        self._p_tag = 'p'
        self._hr_tag = 'hr'
        self._img_tag = 'img'
        self._tr_tag = 'tr'
        self._br_tag = 'br'
        self._td_tag = 'td'
        self._ul_tag = 'ul'
        self._li_tag = 'li'
        self._href_tag = 'a'
        self._dummy_href = "DummyHref"
        # align tags
        self._center_align = {'align': 'center'}
        # color tags
        self._blue_color = {'style': "color:blue;"}
        self._black_color = {'style': "color:black;"}
        self._green_color = {'style': "color:green;"}
        self._dred_color = {'style': "color:darkred;"}
        self._red_color = {'style': "color:red;"}
        # report folder paths
        self.share_folder()
        self.reports_folder_path = os.path.join(
            GeneralConstants.CONTROLLER_FOLDER_PATH,
            self.build_id,
            GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME)
        self.export_html_folder_path = os.path.join(
            GeneralConstants.CONTROLLER_FOLDER_PATH,
            self.build_id,
            GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME,
            GeneralConstants.CONTROLLER_EXPORT_HTML_FOLDER_NAME)
        self.stats_share_folder_path = os.path.join(GeneralConstants.CONTROLLER_SHARE_FOLDER_PATH, self.build_id)
        self.export_html_share_folder_path = os.path.join(
            GeneralConstants.CONTROLLER_SHARE_FOLDER_PATH,
            self.build_id,
            GeneralConstants.CONTROLLER_REPORTS_FOLDER_NAME,
            GeneralConstants.CONTROLLER_EXPORT_HTML_FOLDER_NAME)
        if use_data_source and not os.path.exists(self.export_html_folder_path):
            os.makedirs(self.export_html_folder_path)
        if use_data_source and not os.path.exists(self.reports_folder_path):
            os.makedirs(self.reports_folder_path)
        self.machine_config_file_path = os.path.join(
            self.reports_folder_path,
            GeneralConstants.CONTROLLER_MACHINE_CONFIG_JSON_FILE_NAME)
        self.job_config_file_path = os.path.join(self.reports_folder_path,
                                                 GeneralConstants.CONTROLLER_PERFORMANCE_CONFIG_JSON_FILE_NAME)
        self.job_details_file_path = os.path.join(self.reports_folder_path,
                                                  GeneralConstants.CONTROLLER_PERFORMANCE_JOB_DETAILS_JSON_FILE_NAME)
        # html report headers
        self.root_element = ETree.Element("html")
        head = ETree.SubElement(self.root_element, "head")
        style = ETree.SubElement(head, "style")
        style.text = f"table, th, td {{border: 1px solid black;border-collapse: collapse;}}th, td {{padding: 5px;}}"
        self.body_element = ETree.SubElement(self.root_element, "body")
        # add logo
        if os.path.exists(GeneralConstants.LOGO_FILE):
            self.log.info(f"Adding Logo to the report")
            ETree.SubElement(self.body_element, self._img_tag, width="250", height="50",
                             style="float:left", src=f"{GeneralConstants.LOGO_FILE}")
        h1 = ETree.SubElement(self.body_element, "h1", self._center_align)
        if job_type != JobTypes.TIME_BASED_JOB_MONITORING:
            h1.text = f"Performance Report for Job Id - {self.job_id} & Build Id - {self.build_id}"
        else:
            h1.text = f"Performance Report for {self.job_id} & Build Id - {self.build_id}"
        # add straight line
        ETree.SubElement(self.body_element, self._hr_tag)
        self.perf_helper = PerformanceHelper(self.commcell)
        self.api = customreports.CustomReportsAPI(self.commcell.webconsole_hostname)
        self.rpt_api = Reports(self.api.cv_session)

    def form_commserv_details(self):
        """Forms the default commserv details header for the performance job on report

            Args:
                None

            Returns:
                None

        """
        self.add_line_breaks(2)
        self.add_html_heading(name=GeneralConstants.HEADING_COMMSERV_DETAILS, color=self._blue_color)
        commserv_details = {
            GeneralConstants.COLUMN_COMMSERV_NAME: self.commcell.commserv_name,
            GeneralConstants.COLUMN_COMMSERV_VERSION_REPORT: self.commcell.version,
            GeneralConstants.COLUMN_MONITOR_TYPE: "Job" if self.job_type != JobTypes.TIME_BASED_JOB_MONITORING else "Timer"}
        self.create_table(header=['Parameter', 'Values'], values=commserv_details, is_horizontal=True)

    def form_machine_details(self):
        """Forms the default machine details header for the performance job on the report

            Args:
                None

            Returns:
                None

        """
        self.add_line_breaks(2)
        self.add_html_heading(name=GeneralConstants.HEADING_MACHINE_CONFIG, color=self._blue_color)
        if not os.path.exists(self.machine_config_file_path):
            raise Exception(f"Machine Details Json file not found @ {self.machine_config_file_path}")
        config_details = self.perf_helper.read_json_file(json_file=self.machine_config_file_path)
        self.log.info(f"Loaded machine config details JSON file in memory")
        client_details = []
        # machine details will be key-value pair. Remove the key - client name as it is not needed
        for key, value in config_details.items():
            client_details.append(value)
        machine_header = [
            GeneralConstants.COLUMN_CLIENT_NAME,
            GeneralConstants.COLUMN_MACHINE_NAME,
            GeneralConstants.COLUMN_CPU_MODEL,
            GeneralConstants.COLUMN_MAX_CLOCK_SPEED,
            GeneralConstants.COLUMN_NO_OF_CORES,
            GeneralConstants.COLUMN_LOGICAL_PROCESSORS,
            GeneralConstants.COLUMN_RAM_SIZE,
            GeneralConstants.KEY_THROUGHPUT_READ,
            GeneralConstants.KEY_THROUGHPUT_WRITE,
            GeneralConstants.KEY_THROUGHPUT_DELETE,
            GeneralConstants.COLUMN_OS,
            GeneralConstants.COLUMN_OS_BIT
        ]
        machine_values = []
        for machine_details in client_details:
            values = {
                GeneralConstants.COLUMN_CLIENT_NAME: machine_details[GeneralConstants.COLUMN_CLIENT_NAME],
                GeneralConstants.COLUMN_MACHINE_NAME: machine_details[GeneralConstants.COLUMN_MACHINE_NAME],
                GeneralConstants.COLUMN_CPU_MODEL: machine_details[GeneralConstants.COLUMN_CPU_MODEL],
                GeneralConstants.COLUMN_MAX_CLOCK_SPEED:
                    str(machine_details[GeneralConstants.COLUMN_MAX_CLOCK_SPEED]),
                GeneralConstants.COLUMN_NO_OF_CORES:
                    str(machine_details[GeneralConstants.COLUMN_NO_OF_CORES]),
                GeneralConstants.COLUMN_LOGICAL_PROCESSORS:
                    str(machine_details[GeneralConstants.COLUMN_LOGICAL_PROCESSORS]),
                GeneralConstants.COLUMN_RAM_SIZE: machine_details[GeneralConstants.COLUMN_RAM_SIZE],
                GeneralConstants.COLUMN_OS: machine_details[GeneralConstants.COLUMN_OS],
                GeneralConstants.COLUMN_OS_BIT: f"{machine_details[GeneralConstants.COLUMN_OS_BIT]} bit",
                GeneralConstants.KEY_THROUGHPUT_READ:
                    machine_details[GeneralConstants.DYNAMIC_COLUMN_THROUGH_PUT_READ].split(','),
                GeneralConstants.KEY_THROUGHPUT_WRITE:
                    machine_details[GeneralConstants.DYNAMIC_COLUMN_THROUGH_PUT_WRITE].split(','),
                GeneralConstants.KEY_THROUGHPUT_DELETE:
                    machine_details[GeneralConstants.DYNAMIC_COLUMN_THROUGH_PUT_DELETE].split(','),
            }
            machine_values.append(values)
        self.log.info(f"Machine config details Json : {machine_values}")
        self.create_table(header=machine_header, values=machine_values, is_horizontal=False)

    def form_monitor_details(self):
        """Forms the monitored performance details header for the performance job on the report

            Args:
                None

            Returns:
                None

        """
        if not os.path.exists(self.job_config_file_path):
            raise Exception(f"Job Configs Json file not found @ {self.job_config_file_path}")
        job_configs = self.perf_helper.read_json_file(json_file=self.job_config_file_path)
        self.log.info(f"Loaded job configs JSON file in memory")
        self.log.info(f"Job Configs JSON : {job_configs}")
        self.add_line_breaks(2)
        self.add_html_heading(name=GeneralConstants.HEADING_MONITORED_CONFIG, color=self._blue_color)
        job_phase_obj = JobPhases()
        monitored_phases = []
        for phase in job_configs:
            monitored_phases.append(phase)
        self.add_html_sub_heading(
            name=f"Available Job Phases - {job_phase_obj.get_job_phase(job_type=self.job_type)}",
            color=self._green_color)
        self.add_html_sub_heading(name=f"Monitored Job Phases - {monitored_phases}", color=self._dred_color)
        config_header = [
            GeneralConstants.PHASE_NAME_PARAM,
            GeneralConstants.CONFIGURATIONS_NAME_PARAM,
            GeneralConstants.COLUMN_COUNTERS]
        if self.is_data_source:
            config_header.append(GeneralConstants.MIN_MAX_PARAM)
            config_header.append(GeneralConstants.COLUMN_NET_STATS)
            config_header.append(GeneralConstants.EXPORT_REPORT_PARAM)
        else:
            config_header.append(GeneralConstants.CSV_REPORT_PARAM)
        config_values = []
        for phase in job_configs:
            # check for duplicate configurations
            phase_json = self.perf_helper.remove_dup_configs(config=job_configs[phase])
            self.log.info(f"Total configurations for this phase : {phase} - {len(phase_json)}")
            for config_no in range(1, len(phase_json) + 1):  # length of dict + 1 as we starting with index 1
                config_to_process = str(config_no)
                config_json = phase_json[config_to_process]
                self.log.info(
                    f"{config_to_process} --> Configuration : {config_json}")
                if config_json is None or len(config_json) == 0:
                    self.log.info("Empty config. Ignore")
                    continue
                temp_counters = config_json[GeneralConstants.COUNTERS_PARAM]
                counters = []
                for counter in temp_counters:
                    if counter in (WindowsProcessCounters.PROCESS_PID, UnixProcessCounters.PROCESS_PID):
                        continue
                    counter = counter.split("\\")[-1]
                    counters.append(GeneralConstants.COUNTERS_FIELD_MAPPING[counter])
                phase_dict = {
                    GeneralConstants.PHASE_NAME_PARAM: phase,
                    GeneralConstants.COLUMN_COUNTERS: counters,
                    GeneralConstants.CONFIGURATIONS_NAME_PARAM: f"{config_json[GeneralConstants.CLIENT_PARAM]}"
                                                                f" - {config_json[GeneralConstants.BINARY_PARAM]}"

                }
                if self.is_data_source:
                    if GeneralConstants.PORT_USAGE_PARAM in config_json and\
                            config_json[GeneralConstants.PORT_USAGE_PARAM]:
                        # associate netstat details
                        self.log.info(f"Going to collect netstat min/max results")
                        net_stat = self.perf_helper.find_min_max_for_netstat(config=config_json,
                                                                             build_id=self.build_id)
                        phase_dict[GeneralConstants.COLUMN_NET_STATS] = net_stat
                    # associate min/max details
                    self.log.info(f"Going to collect counters min/max results")
                    min_max_stats = self.perf_helper.find_min_max_for_counters(
                        config=config_json, build_id=self.build_id)
                    # send it as dict itself so that table cell will be split into multiple cells
                    phase_dict[GeneralConstants.MIN_MAX_PARAM] = min_max_stats
                    # Export the report and associate it as href
                    export_file_name = self.export_graph_for_config(config=config_json)
                    phase_dict[GeneralConstants.EXPORT_REPORT_PARAM] = f"{self._dummy_href}" \
                                                                       f"{self.export_html_share_folder_path}" \
                                                                       f"{os.sep}{export_file_name}"
                else:
                    # put output CSV file location as use data source key is False
                    client_name = config_json[GeneralConstants.CLIENT_PARAM]
                    binary = config_json[GeneralConstants.BINARY_PARAM]
                    if binary != CounterTypes.MACHINE_COUNTER:
                        binary = binary.replace(".", "_")
                    phase_dict[GeneralConstants.CSV_REPORT_PARAM] = f"{self._dummy_href}" \
                                                                    f"{self.stats_share_folder_path}{os.sep}" \
                                                                    f"{client_name}{os.sep}{binary}"
                config_values.append(phase_dict)

        self.log.info(f"Monitor configurations json formed : {config_values}")
        self.create_table(header=config_header, values=config_values, is_horizontal=False)

    def form_job_details(self):
        """Forms the default job details header for the performance job on the report

            Args:
                None

            Returns:
                None

        """
        self.add_line_breaks(2)
        self.add_html_heading(name=GeneralConstants.HEADING_JOB_DETAILS, color=self._blue_color)
        if not os.path.exists(self.job_details_file_path):
            raise Exception(f"Job details Json file not found @ {self.job_details_file_path}")
        job_details = self.perf_helper.read_json_file(json_file=self.job_details_file_path)
        self.log.info(f"Loaded job details JSON file in memory")
        self.log.info(f"Job Details JSON : {job_details}")
        job_header = [
            GeneralConstants.COLUMN_JOB_ID,
            GeneralConstants.COLUMN_JOB_TYPE,
            GeneralConstants.DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE,
            GeneralConstants.COLUMN_JOB_STATUS,
            GeneralConstants.COLUMN_JOB_START,
            GeneralConstants.COLUMN_JOB_END,
            GeneralConstants.COLUMN_JOB_DURATION
        ]
        job_values = {
            GeneralConstants.COLUMN_JOB_ID: str(job_details[GeneralConstants.COLUMN_JOB_ID]),
            GeneralConstants.COLUMN_JOB_TYPE: job_details[GeneralConstants.COLUMN_JOB_TYPE],
            GeneralConstants.DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE:
                str(job_details[GeneralConstants.DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE]),
            GeneralConstants.COLUMN_JOB_STATUS: job_details[GeneralConstants.COLUMN_JOB_STATUS],
            GeneralConstants.COLUMN_JOB_START:
                datetime.datetime.fromtimestamp(int(
                    job_details[GeneralConstants.COLUMN_JOB_START])).strftime('%Y-%m-%d %H:%M:%S'),
            GeneralConstants.COLUMN_JOB_END:
                datetime.datetime.fromtimestamp(int(
                    job_details[GeneralConstants.COLUMN_JOB_END])).strftime('%Y-%m-%d %H:%M:%S'),
            GeneralConstants.COLUMN_JOB_DURATION:
                str(job_details[GeneralConstants.COLUMN_JOB_DURATION])
        }
        self.create_table(header=job_header, values=job_values, is_horizontal=False)
        self.add_line_breaks(1)
        self.add_html_sub_heading(name=GeneralConstants.HEADING_JOB_EVENTS, color=self._green_color)
        job_events = []
        for event in job_details[GeneralConstants.COLUMN_JOB_EVENTS]:
            if 'description' in event:
                job_events.append(event['description'])
        self.add_unorder_list(input_list=job_events)

        # Job specific data source details
        if self.job_type in JobTypes.DATA_SOURCE_SUPPORTED_JOB_TYPES:
            self.log.info(f"Populate the data source details on report as job is related to data source")
            ds_header = [
                GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME,
                GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE,
                GeneralConstants.COLUMN_DS_NAME,
                GeneralConstants.DYNAMIC_COLUMN_TOTAL_DOCS,
                GeneralConstants.DYNAMIC_COLUMN_SUCCESS_DOCS,
                GeneralConstants.DYNAMIC_COLUMN_FAILED_DOCS,
                GeneralConstants.DYNAMIC_COLUMN_SKIPPED_DOCS,
                GeneralConstants.COLUMN_INDEXING_SPEED
            ]
            ds_values = {GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME: job_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME],
                         GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE: job_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE],
                         GeneralConstants.COLUMN_DS_NAME: job_details[GeneralConstants.COLUMN_DS_NAME],
                         GeneralConstants.DYNAMIC_COLUMN_TOTAL_DOCS: str(job_details[GeneralConstants.DYNAMIC_COLUMN_TOTAL_DOCS]),
                         GeneralConstants.DYNAMIC_COLUMN_SUCCESS_DOCS: str(job_details[GeneralConstants.DYNAMIC_COLUMN_SUCCESS_DOCS]),
                         GeneralConstants.DYNAMIC_COLUMN_FAILED_DOCS: str(job_details[GeneralConstants.DYNAMIC_COLUMN_FAILED_DOCS]),
                         GeneralConstants.DYNAMIC_COLUMN_SKIPPED_DOCS: str(job_details[GeneralConstants.DYNAMIC_COLUMN_SKIPPED_DOCS]),
                         GeneralConstants.COLUMN_INDEXING_SPEED: str(self.option_obj.convert_no(int(job_details[GeneralConstants.DYNAMIC_COLUMN_SUCCESS_DOCS] / job_details[GeneralConstants.COLUMN_JOB_DURATION]) * 60))}
            if self.job_type in JobTypes.DATA_SOURCE_ENTITY_EXTRACT_JOB_TYPES:
                ds_header.append(GeneralConstants.DYNAMIC_COLUMN_CA_SUCCESS_DOCS)
                ds_header.append(GeneralConstants.DYNAMIC_COLUMN_CA_FAILED_DOCS)
                ds_values[GeneralConstants.DYNAMIC_COLUMN_CA_SUCCESS_DOCS] = str(
                    job_details[GeneralConstants.DYNAMIC_COLUMN_CA_SUCCESS_DOCS])
                ds_values[GeneralConstants.DYNAMIC_COLUMN_CA_FAILED_DOCS] = str(
                    job_details[GeneralConstants.DYNAMIC_COLUMN_CA_FAILED_DOCS])
            self.add_line_breaks(1)
            self.add_html_sub_heading(name=GeneralConstants.HEADING_DATA_SOURCE_DETAILS, color=self._green_color)
            self.create_table(header=ds_header, values=ds_values, is_horizontal=False)
            if dynamic_constants.FIELD_EXTRACT_DURATION in job_details:
                self.add_line_breaks(1)
                self.add_html_sub_heading(
                    name=GeneralConstants.HEADING_EXTRACT_DURATION_DETAILS,
                    color=self._green_color)
                ds_values = job_details[dynamic_constants.FIELD_EXTRACT_DURATION]
                self.create_table(
                    header=[
                        GeneralConstants.COLUMN_FILE_TYPE,
                        GeneralConstants.COLUMN_EXTRACT_DURATION_STATS],
                    values=ds_values,
                    is_horizontal=True)

        # past job history using open data source
        if self.is_data_source:
            self.add_line_breaks(1)
            self.log.info(f"Use DataSource key set. Try to find past similar job history")
            self.add_html_sub_heading(name=GeneralConstants.HEADING_PAST_JOB_HISTORY, color=self._green_color)
            ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.Job_Details_Data_Source_Name)
            index_server_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
            self.log.info(f"DataSource/Index Server Object initialised")
            past_job_header = [
                GeneralConstants.COLUMN_COMMSERV_VERSION,
                GeneralConstants.COLUMN_BUILD_ID,
                GeneralConstants.COLUMN_JOB_ID,
                GeneralConstants.COLUMN_JOB_STATUS,
                GeneralConstants.COLUMN_JOB_DURATION]
            if self.job_type in JobTypes.DATA_SOURCE_SUPPORTED_JOB_TYPES:
                self.log.info("DataSource job type. Fetch the data source dynamic fields from job details data source")
                past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_TOTAL_DOCS)
                past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_SUCCESS_DOCS)
                past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_FAILED_DOCS)
                past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME)
                past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_SOURCE_SIZE)
                if self.job_type in JobTypes.DATA_SOURCE_ENTITY_EXTRACT_JOB_TYPES:
                    past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_CA_SUCCESS_DOCS)
                    past_job_header.append(GeneralConstants.DYNAMIC_COLUMN_CA_FAILED_DOCS)
            past_job_values = []
            query = {
                GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME:
                    f"\"{job_details[GeneralConstants.DYNAMIC_COLUMN_SOURCE_NAME]}\"",
                GeneralConstants.DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE: job_details[
                    GeneralConstants.DYNAMIC_COLUMN_AUTOMATION_JOB_TYPE],
                f"!{GeneralConstants.COLUMN_JOB_ID}": self.job_id}
            resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                       select_dict=query,
                                                       attr_list=set(past_job_header),
                                                       op_params=dynamic_constants.QUERY_100_ROWS)
            hits = resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]
            if hits == 0:
                self.add_para(input="No Past job history found for same source/job type", color=self._red_color)
            else:
                for solr_doc in resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.DOCS_PARAM]:
                    past_job_values.append(solr_doc)
                self.log.info(f"Past Job history : {past_job_values}")
                self.create_table(header=past_job_header, values=past_job_values, is_horizontal=False)
        else:
            self.log.info(f"Use DataSource key not set.")
            self.add_html_sub_heading(
                name="Past Job History - Not Available. Please set use_data_source while calling report if applicable",
                color=self._red_color)

    def form_api_details(self, api_count=15):
        """Forms the API details part of the html report

            Args:
                api_count   (int)   -   number of top time consuming APIs to be listed in the report

        """
        api_detail_values = []
        api_table_header = [
            GeneralConstants.HAR_START_TIME_COLUMN,
            GeneralConstants.HAR_REQUEST_TYPE_COLUMN,
            GeneralConstants.HAR_URL_COLUMN,
            GeneralConstants.HAR_TOTAL_TIME_COLUMN,
            GeneralConstants.HAR_WAIT_TIME_COLUMN,
            GeneralConstants.HAR_RESPONSE_CODE_COLUMN
        ]
        self.commcell.datacube.datasources.refresh()
        if not self.commcell.datacube.datasources.has_datasource(GeneralConstants.HAR_DS_NAME):
            self.log.info(f"No HAR data source found. Skip it")
            return
        ds_obj = self.commcell.datacube.datasources.get(GeneralConstants.HAR_DS_NAME)
        index_server_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
        self.log.info(f"DataSource/Index Server Object initialised")
        query = {
            GeneralConstants.HAR_DS_BUILD_ID: self.build_id,
            GeneralConstants.HAR_URL_COLUMN: '*.do*'
        }
        resp = index_server_obj.execute_solr_query(core_name=ds_obj.computed_core_name,
                                                   select_dict=query,
                                                   attr_list=api_table_header,
                                                   op_params={
                                                       "sort": f"{GeneralConstants.HAR_TOTAL_TIME_COLUMN} desc",
                                                       "rows": api_count
                                                   })
        hits = resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.NUM_FOUND_PARAM]
        if hits == 0:
            self.log.info("No HAR result was found with the given Build id, Skipping")
        else:
            self.add_line_breaks(2)
            self.add_html_sub_heading(GeneralConstants.HAR_API_DETAILS_HEADING % api_count, color=self._green_color)
            for solr_doc in resp[dynamic_constants.RESPONSE_PARAM][dynamic_constants.DOCS_PARAM]:
                api_detail_values.append(solr_doc)
            self.log.info(f"API details retrieved : {api_detail_values}")
            self.create_table(header=api_table_header, values=api_detail_values, is_horizontal=False)

    def generate_report(self, send_mail=False, receivers=None, api_count=15):
        """Generates the html report for the job monitored and sends mail to given receivers mail ids

            Args:

                send_mail       (bool)      -- specifies whether generated report has to be sent or not

                                    Default : False

                receivers       (str)       --  receivers mail Id [comma separated email id's]

                api_count       (int)   -   number of top time consuming APIs to be listed in the report

                                    Default : 15

            Returns:

                str     --  generated report file path
        """
        if send_mail and receivers is None:
            raise Exception("Receiver email is not given. Please check")
        self.import_report()
        self.log.info(f"Custom report setup finished")
        self.form_commserv_details()
        self.log.info("Formed Commserv Details on report")
        if self.job_type != JobTypes.TIME_BASED_JOB_MONITORING:
            self.form_job_details()
            self.log.info("Formed Job Details on report")
        self.form_machine_details()
        self.log.info("Formed Machine details on report")
        self.form_monitor_details()
        self.log.info("Formed Monitor details on report")
        self.form_api_details(api_count=api_count)
        self.log.info("Formed time consuming API details(if any) on report")
        # Report Generation code from xml to html. Use saxutils to unescape characters accordingly
        html_string = saxutils.unescape(ETree.tostring(self.root_element, encoding='unicode', method='html'))
        report_file = os.path.join(
            self.reports_folder_path,
            f"{GeneralConstants.REPORTS_FILE_NAME}_{self.build_id}_{self.job_id}.html")
        out_file = open(report_file, GeneralConstants.FILE_WRITE_MODE)
        out_file.write(html_string)
        out_file.close()
        self.log.info(f"Successfully generated report @ {report_file}")
        if send_mail:
            mail_obj = Mailer({'receiver': receivers}, self.commcell)
            mail_obj.mail(
                subject=f"{GeneralConstants.EMAIL_SUBJECT} for BuildId : {self.build_id} and Job id : {self.job_id}",
                body=html_string)
        return report_file
