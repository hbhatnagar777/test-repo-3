# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File to add utils required for Metrics server functionality"""
from datetime import datetime, timedelta
import time
import requests
from time import sleep

from xml.etree.ElementTree import XML
from requests import get

from cvpysdk.commcell import Commcell, Clients

from AutomationUtils.machine import Machine
from AutomationUtils import logger, config

from Web.API.customreports import CustomReportsAPI

from Web.Common.exceptions import CVException

_CONSTANTS = config.get_config()


def get_troubleshooting_url_path(req_id, commcell_id):
    """Returns the URLs path of sendlogs remote troubleshooting XMLs"""

    file_name = f'SendLogsTask_{req_id}.xml'
    url1 = f'http://{_CONSTANTS.Reports.EDCNode1}/Downloads/SQLScripts/Troubleshooting/{commcell_id}/{file_name}'
    url2 = f'http://{_CONSTANTS.Reports.EDCNode2}/Downloads/SQLScripts/Troubleshooting/{commcell_id}/{file_name}'

    return [url1, url2]


class MetricsServer:
    """class for actions on Metrics Server"""

    def __init__(self, metrics_webconsole_name=None,
                 metrics_commcell_user=_CONSTANTS.ADMIN_USERNAME,
                 metrics_commcell_pwd=_CONSTANTS.ADMIN_PASSWORD):
        """

        Args:
            metrics_webconsole_name: name of the webconsole used for metrics server
            metrics_commcell_user: login user name
            metrics_commcell_pwd: login password
        """

        self._mcommcell = Commcell(metrics_webconsole_name, metrics_commcell_user,
                                   metrics_commcell_pwd, verify_ssl=False)
        self._log = logger.get_log()
        self._user = metrics_commcell_user
        self._pwd = metrics_commcell_pwd
        self.__METRICS_SERVER_API = None
        self.webserver_name = self._get_webserver_name()
        self.metrics_machine = Machine(self.webserver_name, self._mcommcell)
        self._m_webserver = self._mcommcell.clients.get(self.webserver_name)
        self._uploaddir = self.get_upload_dir()
        self._uploadedfilename = None

    @property
    def log_dir(self):
        return self._m_webserver.log_directory

    @property
    def metrics_server_api(self):
        """API to access metrics server DB"""
        if not self.__METRICS_SERVER_API:
            self.__METRICS_SERVER_API = CustomReportsAPI(
                self._mcommcell.webconsole_hostname,
                username=self._user,
                password=self._pwd
            )
        return self.__METRICS_SERVER_API

    @property
    def archive_dir(self):
        """returns xml Archive directory"""
        return self.metrics_machine.join_path(self._uploaddir, 'Archive')

    def _get_webserver_name(self):
        """returns the Webserver name of the metrics webconsole"""
        wc_client = Clients(self._mcommcell).get(self._mcommcell.webconsole_hostname)
        query = f"""
        SELECT name FROM app_client 
        WHERE id in (
            SELECT attrval FROM app_clientprop 
            WHERE componentnameid={wc_client.client_id} AND attrname LIKE 'WebServerClientId')
        """
        rows = self.metrics_server_api.execute_sql(query)
        return rows[0][0]

    def _is_file_parsed(self, upload_path, expected_filename):
        file_name_with_path = self.metrics_machine.join_path(upload_path, expected_filename)
        if self.metrics_machine.check_file_exists(file_name_with_path):
            file_size = self.metrics_machine.get_file_size(file_name_with_path)
            if file_size >= 0:
                self._uploadedfilename = file_name_with_path
                return True  # File parsed by driver
            else:
                raise Exception("Metrics uploaded file {0} size is {1} Bytes"
                                .format(expected_filename, file_size))
        self._log.error("File [%s] not found in archive folder" % file_name_with_path)
        return False

    def get_wia_troubleshoot_request_id(self, commcell_guid):
        """returns the latest WIA request id for the commcell"""
        query = """exec GetRemoteWIAStatusReq '%s'""" % commcell_guid
        request_id = self.metrics_server_api.execute_sql(query, database_name='CloudServices')
        self._log.info('Troubleshoot request id - %s' % str(request_id[0][2]))
        if not request_id:
            raise Exception('WIA Request id not found')
        return int(request_id[0][2])

    def get_troubleshoot_directory(self):
        """
        comm_cell : commcelll object
        Returns(str): its return path of  troubleshoot directory

        """
        return self.metrics_machine.join_path(_CONSTANTS.Reports.PUBLIC_CLOUD_DOWNLOAD_SCRIPTS, 'Troubleshooting')

    def check_troubleshooting_xml_exists(self, req_id, commcell_id):
        """
        Check if remote troubleshooting xmls exists
        Args:
            req_id (str): Request ID of the remote troubleshooting job
            commcell_id (str): CommcellID of the remote troubleshooting job

        Returns :
            list - list of urls path to check for troubleshooting xmls
        """
        paths = get_troubleshooting_url_path(req_id, commcell_id)
        for path in paths:
            response = requests.get(path)
            if response.status_code != 200:
                return [False, paths]
        return [True, paths]

    def get_troubleshoot_xml_name(self, req_id, commcell_id):
        """returns the latest WIA request XML name for the commcell"""
        file_name = 'SendLogsTask_%d.xml' % req_id
        xml_abs_path = self.metrics_machine.join_path(
            self.get_troubleshoot_directory(),
            commcell_id,
            file_name
        )
        self._log.info('Expected Troubleshooting xml name [%s]' % xml_abs_path)
        return xml_abs_path

    def is_wia_troubleshoot_xml_exist(self, commcell_id, commcell_guid):
        """Checks latest troubleshoot xml exist for given commcell"""
        req_id = self.get_wia_troubleshoot_request_id(commcell_guid)
        self._log.info(self.metrics_machine)
        return self.metrics_machine.check_file_exists(
            self.get_troubleshoot_xml_name(
                req_id,
                commcell_id
            )
        )

    def get_upload_dir(self):
        """gets the Upload directory in metrics server"""
        return self.metrics_machine.get_registry_value("Cloud", "nXMLPATH")

    def get_script_dir(self):
        """Gets the metrics download script directory"""
        self._install_dir = self._m_webserver.install_directory
        self._log.info('Script directory [%s]', self._install_dir)
        return self.metrics_machine.join_path(self._install_dir, 'Metrics', 'scripts')

    def is_file_in_archive(self, expected_filename):
        """
        Checks uploaded file is parsed successfully and present in archive folder in Metrics server

        Args:
            expected_filename (str): uploaded file name
                                    this is available from metricsreport api in SDK

        Returns: True/False
        """
        upload_path = self.metrics_machine.join_path(self._uploaddir, 'Archive')
        status = self._is_file_parsed(upload_path, expected_filename)
        if status:
            return True
        return False

    def is_file_blocked(self, expected_filename):
        """
        Checks uploaded file is blocked in parsing and present in blocked folder in Metrics server

        Args:
            expected_filename (str): uploaded file name
                                    this is available from metricsreport api in SDK

        Returns: True/False
        """
        upload_path = self.metrics_machine.join_path(self._uploaddir, 'Blocked')
        status = self._is_file_parsed(upload_path, expected_filename)
        if status:
            return True
        return False

    def is_file_failed(self, expected_filename):
        """
        Checks uploaded file failed in parsing and present in Failed folder in Metrics server

        Args:
           expected_filename (str): uploaded file name
                                    this is available from metricsreport api in SDK

        Returns: True/False
        """
        upload_path = self.metrics_machine.join_path(self._uploaddir, 'Failed')
        status = self._is_file_parsed(upload_path, expected_filename)
        if status:
            return True
        return False

    def _is_db_parsed(self, file_name):
        """
        Args:
            file_name (str): uploaded file names to check for DB parsing
            Returns: shred_status(int) : Processed status of the file
        """
        query = f"""SELECT ShredStatus FROM cf_CustomerFeedbackXmlFile WITH (Nolock)
                    WHERE filename like '%{file_name}%'"""
        shred_status = self.metrics_server_api.execute_sql(query, database_name='CVCloud',
                                                           connection_type="METRICS")
        return int(shred_status[0][0])

    def wait_for_xml_parsing(self, expected_filename):
        """
        Waits for uploaded xml to be parsed and moved to archive folder
        Args:
            expected_filename (str): uploaded file names
                                    this is available from metricsreport api in SDK

        Returns: True

        Raises: raises exception when xml is not found in archive folder after
                timeout period of 5 minutes

        """
        time_out = 300
        while not self.is_file_in_archive(expected_filename):
            if time_out < 0:
                raise TimeoutError(
                    f'Uploaded file ({expected_filename}) not present in Archive folder')
            sleep(30)
            time_out -= 30
        self._log.info('File (%s) present in Archive folder', self._uploadedfilename)
        return True

    def wait_for_xml_blocked(self, expected_filename):
        """
        wait for uploaded xml file to be present in blocked folder in Metrics server
        Args:
            expected_filename (str): uploaded file name
                                    this is available from metricsreport api in SDK
        Returns: True/False
        """
        time_out = 300
        while not self.is_file_blocked(expected_filename):
            if time_out < 0:
                raise TimeoutError(
                    f'Uploaded file ({expected_filename}) not present in Blocked folder')
            sleep(30)
            time_out -= 30
        self._log.info('File (%s) present in Blocked folder', self._uploadedfilename)
        return True

    def wait_for_xml_failed(self, expected_filename):
        """
        wait for uploaded xml file to be present in Failed folder in Metrics server
        Args:
           expected_filename (str): uploaded file name
                                    this is available from metricsreport api in SDK
        Returns: True/False
        """
        time_out = 300
        while not self.is_file_failed(expected_filename):
            if time_out < 0:
                raise TimeoutError(
                    f'Uploaded file ({expected_filename}) not present in Failed folder')
            sleep(30)
            time_out -= 30
        self._log.info('File (%s) present in Failed folder', self._uploadedfilename)
        return True

    def wait_for_db_parsing(self, expected_filename):
        """
        Waits for uploaded xml to be parsed in database
        Args:
            expected_filename (str): uploaded file name
        Returns: True

        Raises: raises exception when xml is not parsed in DB after timeout period of 5 minutes
        """
        time_out = 300
        while True:
            shred_status = self._is_db_parsed(expected_filename)
            if shred_status in [2, 3]:
                break
            if time_out < 0:
                raise TimeoutError('Uploaded file not present in DB')
            sleep(30)
            time_out -= 30
        if shred_status != 2:
            raise CVException(f"File {self._uploadedfilename} is not parsed in database")
        self._log.info('file (%s) parsed in database', self._uploadedfilename)
        return True

    def wait_for_parsing(self, expected_filename):
        """
        waits for xml to be parsed by metrics driver and in database
        Args:
            expected_filename (str): uploaded file name
                                    this is available from metricsreport api in SDK

        Returns:

        """
        self._log.info(f"Waiting for parsing of file {expected_filename}")
        self.wait_for_xml_parsing(expected_filename)
        self.wait_for_db_parsing(expected_filename)

    def get_queryids_from_uploaded_xml(self, file_path):
        """
        returns the queries from successfully parsed xml (xml in archive folder)
        Args:
            file_path (str): file name with path

        Returns: list of queries present in file
        """
        return self._get_queryids_from_xml(file_path)

    def _get_queryids_from_xml(self, file_path):
        """
        Returns: list of queries whose results are present in file
        """
        xml_content = self.metrics_machine.read_file(file_path, encoding="UTF8")
        root = XML(xml_content)
        return ["CommservSurveyQuery_" + str(i.attrib['QueryId']) + '.sql' for i in
                root.findall("./Rpt_CSSXMLDATA")]

    def get_offline_collect_file_names(self, dataset_name):
        """
        gets offline collection query name for the given report
        Args:
            dataset_name (str): offline dataset name

        Returns:
            list: query names

        """
        return self.metrics_server_api.execute_sql(
            f"""
            SELECT CollectScriptName
            FROM cf_CommservSurveyQueries
            WHERE Name LIKE '{dataset_name}'
            """,
            database_name="CVCloud", connection_type="METRICS"
        )

    def get_commcell_version(self, ccid):
        """
        returns the commcell version
        Args:
            ccid (str): hex value of commcell id for non eval versions

        Returns: CommServe version

        """
        if ccid == 'FFFFF':
            return 'FFFFF'
        ccid = int(ccid, 16)
        query = f"""
         SELECT  CommservVersion 
         FROM cf_commcellidnamemap WITH (NOLOCK) 
         WHERE commcellid = {ccid}
         """
        query_result = self.metrics_server_api.execute_sql(query, database_name="CVCloud")
        if query_result:
            return query_result[0][0]
        return 'N/A'

    def get_commcell_customername(self, ccid):
        """
        returns the commcell customer name
        Args:
            ccid (str): hex value of commcell id 

        Returns: Customer Name

        """
        ccid = int(ccid, 16)
        query = f"""
         SELECT  CustomerName 
         FROM cf_commcellidnamemap WITH (NOLOCK) 
         WHERE commcellid = {ccid}
         """
        self._log.info('query (%s) ', query)
        query_result = self.metrics_server_api.execute_sql(query, database_name="CVCloud",
                                                           connection_type="METRICS")
        if query_result:
            return query_result[0][0]
        return 'N/A'

    def get_commcell_upload_ip(self, ccid):
        """
        returns the commcell upload ip
        Args:
            ccid (str): hex value of commcell id

        Returns: Upload IP

        """
        ccid = int(ccid, 16)
        query = f"""
         SELECT  CommservIP
         FROM cf_commcellidnamemap WITH (NOLOCK) 
         WHERE commcellid = {ccid}
         """
        self._log.info('query (%s) ', query)
        query_result = self.metrics_server_api.execute_sql(query, database_name="CVCloud", connection_type="METRICS")
        if query_result:
            return query_result[0][0]
        return 'N/A'

    def get_metrics_report_name(self, query_id):
        """
            Get the metrics report from the table
            Args:
                query_id: report id

            Returns: report name
            """
        query = f"""
            SELECT Name 
            FROM cf_commservsurveyqueries WITH (NOLOCK) 
            WHERE QueryId= {query_id}
            """
        query_result = self.metrics_server_api.execute_sql(query, database_name="CVCloud")
        if query_result:
            return str(query_result[0][0])
        return 'N/A'

    def is_offline_query_exist(self, file_name):
        """Checks offline collection query exist"""
        query_url = f'https://{self._mcommcell.webconsole_hostname}/downloads/sqlscripts/CustomerScripts/{file_name}'
        response = get(query_url, verify=False)
        if response.status_code != 200:
            self._log.error(f'Expected collection query URL: [{query_url}]')
            return False
        return True

    def get_collect_file_content(self, dataset_name):
        """
        gets offline collection query content for the given report
        Args:
            dataset_name: offline dataset name

        Returns: collection query file_content and collection query URL

        Raises:
            CVException: if query not found in DB or when file not found in metrics script folder
        """
        try:

            collect_file_name = self.get_offline_collect_file_names(dataset_name)
            if not collect_file_name:
                raise CVException(
                    f'collection query entry not found in DB for dataset [{dataset_name}]'
                )
            collect_file_name = collect_file_name[0][0]
            if not self.is_offline_query_exist(collect_file_name):
                raise FileNotFoundError
            wc_name = self._mcommcell.webconsole_hostname
            collect_file_url = f'http://{wc_name}/downloads/sqlscripts/CustomerScripts/{collect_file_name}'
            collect_file_content = get(collect_file_url).text
            return collect_file_content, collect_file_url
        except FileNotFoundError:
            raise CVException(
                f'collection query [{collect_file_name}] not found in collection scripts directory'
            )

    def _get_failed_folder_contents(self):
        """
        Scans the Metrics failed folder contents

        Returns:
            list    -       List of items under the directory with each item being a
            dictionary of item properties
        """
        failed_folder = self.metrics_machine.join_path(self.get_upload_dir(), r'Failed')
        return self.metrics_machine.scan_directory(failed_folder)

    def _read_error_files(self, file_paths):
        """
        Reads the collection error files
        Args:
            file_paths (list) : file paths of output files

        Returns: Dictionary of commcell id, query id and error file, only unique errors are
            added to this.
        """
        unique_error_list = []
        collection_errors = []
        excluded_errors = 'with error [Query Output is not correct]]'
        for each_file in file_paths:
            error = self.metrics_machine.read_file(each_file)
            if error not in unique_error_list and excluded_errors not in error:
                unique_error_list.append(error)
                temp = {}
                file_name = each_file.split('\\')[-1]
                temp['ccid'] = file_name.split('_')[1]
                temp['queryid'] = file_name.split('.sql.output')[0].split('_')[-1]
                temp['report_name'] = self.get_metrics_report_name(temp['queryid'])
                temp['Version'] = self.get_commcell_version(temp['ccid'])
                temp['error'] = error
                collection_errors.append(temp)

        return collection_errors

    def get_collection_errors(self, days=1):
        """
        Gets Collection errors from failed folder
        Args:
            days (int): Error in last x days

        Returns :
            list - Dictionary of commcell id, query id and error file, only unique errors are
            added to this.

        """
        yesterday = datetime.now() - timedelta(days=days)
        yest_unix_time = int(time.mktime(yesterday.timetuple()))
        files = self._get_failed_folder_contents()
        out_files = [
            fobj['path'] for fobj in files
            if (fobj['type'] == 'file' and
                fobj['path'].split('.')[-1] == 'output' and
                int(fobj['mtime']) > yest_unix_time)
        ]
        if out_files:
            return self._read_error_files(out_files)
        return []

    def get_metrics_reports(self):
        """
        get the all the metrics reports from the report page
        """
        query = """
        SELECT Name FROM cf_WebConsoleReports WHERE DispFlag in (199,203,207,0,195)
        """
        result = self.metrics_server_api.execute_sql(query, database_name="CVCloud")
        temp = []
        for each_report in result:
            temp.append(each_report[0])
        return temp

    def check_files_in_failed(self, pattern):
        """
        Checks for file patterns in failed folder
        """
        failed_folder = self.metrics_machine.join_path(self.get_upload_dir(), r'Failed')
        no_of_files = self.metrics_machine. \
            number_of_items_in_folder(failed_folder, filter_name=pattern)
        return True if no_of_files > 0 else False
