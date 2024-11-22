# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for HAR related operations

    HarHelper:

        __init__()                      --      initialize the HarHelper class

        refresh()                       --      refreshes the properties associated with
                                                HarHelper class

        upload_har_report()             --      uploads the HAR csv file to open data source

        export_har()                    --      dumps browser HAR content to json and csv files

        json_csv()                      --      parser to parse HAR json to csv file

        analyze_all_request()           --      exports and upload HAR report of a Browser object

"""

import json
import csv
import datetime
import os
from AutomationUtils.config import get_config
from AutomationUtils import constants as automation_constants
from AutomationUtils import logger
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from cvpysdk.datacube.constants import IndexServerConstants
from AutomationUtils.Performance.Utils.constants import GeneralConstants
from dynamicindex.index_server_helper import IndexServerHelper


_CONFIG = get_config().DynamicIndex.PerformanceStats


class HarHelper():
    """HarHelper class for HAR related operations"""

    FIELD_NAMES = GeneralConstants.HAR_DS_FIELD_NAMES
    FIELD_TYPES = GeneralConstants.HAR_DS_FIELD_TYPES
    FIELD_SCHEMA = GeneralConstants.HAR_DS_FIELD_SCHEMA

    def __init__(self, commcell_object):
        """Initializes the HarHelper object"""
        self.log = logger.get_log()
        self.commcell = commcell_object
        self.open_data_source_name = GeneralConstants.HAR_DS_NAME
        self.data_source_helper = None
        self.index_server_name = _CONFIG.Index_Server
        self.data_cube = None
        self.data_sources = None
        self.refresh()

    def refresh(self):
        """refreshes the properties associated with HarHelper class"""
        self.commcell.refresh()
        self.data_source_helper = DataSourceHelper(commcell_object=self.commcell)
        self.data_cube = self.commcell.datacube
        self.data_sources = self.data_cube.datasources

    def upload_har_report(self, csv_file, index_server_name=None):
        """Method to upload the HAR csv file to open data source

            Args:

                csv_file            (str)       --  HAR csv file location to be uploaded

                index_server_name   (str)       --  Index server name to be used a
                                                    create an Open Data Source
                                                        Default=None

            Returns:

                None

            Raises:

                Exception:

                    if index_server_name is not passed to create new Open data source

                    if failed to upload csv file

        """
        if self.data_sources.has_datasource(self.open_data_source_name):
            har_ds = self.data_sources.get(self.open_data_source_name)
        else:
            if index_server_name is None:
                if self.index_server_name == "":
                    self.log.error("Index server name is required to create new open data source")
                    raise Exception("Please specify index server name in the config.json")
                else:
                    index_server_name = self.index_server_name
            self.log.info(f"Using {index_server_name} index server to creating open data source")
            is_helper = IndexServerHelper(self.commcell, index_server_name)
            is_helper.update_roles(index_server_roles=[IndexServerConstants.ROLE_DATA_ANALYTICS])
            har_ds = self.data_source_helper.create_open_data_source(
                self.open_data_source_name, index_server_name
            )
            self.data_source_helper.update_data_source_schema(
                self.open_data_source_name, self.FIELD_NAMES, self.FIELD_TYPES, self.FIELD_SCHEMA
            )
        report_post_url = self.commcell._services['DATACUBE_IMPORT_DATA'] % ("csv", har_ds.datasource_id)
        with open(csv_file, 'r') as f:
            csv_data = f.read()
        build_id = csv_data.split("\n")[1].split(",")[0]
        report_view_url = f"http://{self.commcell.webconsole_hostname}/webconsole/dcube.do?type=blank&dn=" \
                          f"harReportDataSource&id={har_ds.datasource_id}&cn={har_ds.datasource_id}&" \
                          f"action=rv&fv=1&input.dsId={har_ds.datasource_id}&input.dsType=blank&" \
                          f"Filter.filter.include.BuildId={build_id}"
        csv_data = "".join(csv_data)
        flag, response = self.commcell._cvpysdk_object.make_request(
            'POST', report_post_url, csv_data
        )
        if flag:
            if response.json():
                if "errorCode" in response.json():
                    if int(response.json()['errorCode']) == 0:
                        self.log.info("HAR report uploaded")
                        self.log.info(f"HAR report URL :\n{report_view_url}")
                        self.refresh()
                        return
        raise Exception("Problem occurred while uploading HAR report.")

    def export_har(self, cvbrowser, build_id=None, return_json=False):
        """Method to dump browser HAR content to json and csv files

            Args:

                cvbrowser           (obj)       --      cvbrowser class instance

                build_id            (str)       --      unique build id string
                                                        Default=None

                return_json         (bool)      --      whether to return the json value or not

            Returns:

                str/dict     --      location of parsed csv file with HAR entries/ JSON formatted HAR records

            Raises:

                Exception:

                    if Browser Mob Proxy not initialized

                    if csv file does not exist

        """
        if not cvbrowser.bmp_proxy_server:
            raise Exception("Browser Mob Proxy not initialized")
        if not build_id:
            build_id = str(datetime.datetime.now().timestamp())
        dump_folder = os.path.join(automation_constants.AUTOMATION_DIRECTORY,
                                   GeneralConstants.HAR_PERF_FOLDER_NAME)
        dump_file_name = os.path.join(automation_constants.AUTOMATION_DIRECTORY,
                                      GeneralConstants.HAR_PERF_FOLDER_NAME, f"{build_id}.json")
        if not os.path.exists(dump_folder):
            os.mkdir(os.path.join(dump_folder))
        with open(dump_file_name, "w") as f:
            json.dump(cvbrowser.bmp_proxy_server.har, f)
        if return_json:
            return cvbrowser.bmp_proxy_server.har
        return self.json_to_csv(dump_file_name, build_id)

    def json_to_csv(self, filename, build_id=None):
        """Parser to parse HAR json to csv file

            Args:

                filename        (str)       --      HAR json file location

                build_id        (str)       --      unique build id string
                                                    Default=None

            Returns:

                str     --      location of parsed csv file

            Raises:

                Exception:

                    if csv file does not exist

        """
        if not build_id:
            build_id = str(datetime.datetime.now().timestamp())
        with open(filename, 'r') as f:
            json_data = json.load(f)
        url_entries = json_data['log']['entries']
        csv_headers = self.FIELD_NAMES
        csv_data = [csv_headers]
        for entry in url_entries:
            if '+' in entry['startedDateTime']:
                entry['startedDateTime'] = f"{entry['startedDateTime'].split('+')[0]}Z"
            request_detail = entry['request']
            base_url = f"{self.commcell.webconsole_hostname}"
            http_url = f"http://{base_url}"
            https_url = f"https://{base_url}"
            if request_detail['url'].startswith('http://'):
                request_detail['url'] = request_detail['url'][len(http_url)::]
            else:
                request_detail['url'] = request_detail['url'][len(https_url)::]
            response_detail = entry['response']
            timings = entry['timings']
            csv_row = [build_id, entry['serverIPAddress'], entry['pageref'], request_detail['url'],
                       request_detail['method'], response_detail['status'], entry['startedDateTime'],
                       timings['wait'], entry['time']]
            csv_data.append(csv_row)
        out_file = filename.replace('.json', '.csv')
        with open(out_file, 'w', newline='') as f:
            csv_writer = csv.writer(f)
            for csv_row in csv_data:
                csv_writer.writerow(csv_row)
        return out_file

    def analyze_all_request(self, cvbrowser, build_id=None, index_server_name=None):
        """Method to analyze all the network requests and push to open data source

        Args:
            cvbrowser           (Browser)   -   cvBrowser object to be used for HAR details

            build_id            (str)       -   custom build id to be set

            index_server_name   (str)   -   index server name where to upload the open data source

        """
        self.upload_har_report(self.export_har(cvbrowser=cvbrowser, build_id=build_id), index_server_name)
