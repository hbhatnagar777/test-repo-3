# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "48201": {}
            }

"""
import os
import re
import time
from datetime import timedelta
from xml.etree.ElementTree import XML
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.metricsutils import MetricsServer
from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """Class for executing Test Case: Metrics - Frequency collection acceptance"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case


        """
        super(TestCase, self).__init__()
        self.files_in_archive = []
        self.commserv_client = None
        self.cs_machine = None
        self.simpana_path = None
        self.metrics_server = None
        self.schedule_info_xml_path = None
        self.compulsory_queries = None
        self.private_metrics = None
        self.name = "Metrics - Frequency collection acceptance"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.commserv_client = self.commcell.commserv_client
            self.cs_machine = Machine(self.commserv_client)
            self.simpana_path = self.commserv_client.install_directory
            self.schedule_info_xml_path = self.cs_machine.join_path(
                    self.simpana_path, "Reports", "CommservSurvey", "ScheduleInfo.xml")
            self.private_metrics = PrivateMetrics(self.commcell)
            self.metrics_server = MetricsServer(self.private_metrics.private_metrics_server_name,
                                                self.inputJSONnode['commcell']["commcellUsername"],
                                                self.inputJSONnode['commcell']["commcellPassword"])
            self.compulsory_queries = ["CommservSurveyQuery_2.sql", "CommservSurveyQuery_57.sql"]

            self.metrics_machine  = self.metrics_server.metrics_machine
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def if_schedule_info_xml_created(self):
        """Check if ScheduleInfo.xml is present"""
        end_time = time.time()+60*60
        while time.time() < end_time:
            if self.cs_machine.check_file_exists(self.schedule_info_xml_path):
                self.log.info("scheduleInfoXML found")
                return True
            time.sleep(300)
        raise CVTestStepFailure("ScheduleInfo.xml not found at [%s]" % self.schedule_info_xml_path)

    @test_step
    def get_query_ids_from_schedule_info(self):
        """Get query ids from ScheduleInfo.xml"""
        query_ids = []
        schedule_info_content = self.cs_machine.read_file(self.schedule_info_xml_path)
        self.log.info(schedule_info_content)
        root = XML(schedule_info_content)

        for file_list in root.findall('./fileList'):
            filename = file_list.attrib['fileName']
            query_ids.append(filename)
        return query_ids

    @test_step
    def get_timestamp_from_schedule_info(self):
        """Read timestamp from ScheduleInfo.xml"""
        query_file_name = 'CommservSurveyQuery_137.sql'
        schedule_info_content = self.cs_machine.read_file(self.schedule_info_xml_path)
        root = XML(schedule_info_content)
        for file_list in root.findall('./fileList'):
            if file_list.attrib['fileName'] == query_file_name:
                last_collection_time = file_list.attrib['lastCollectionTime']
                break
        else:
            raise CVTestStepFailure("ScheduleInfo.xml is not having specified query id")
        self.log.info("Last collection time from xml :" + last_collection_time)
        return int(last_collection_time)

    @test_step
    def check_timestamp(self, timestamp):
        """Check timestamp from ScheduleInfo.xml is within last 1 hour"""
        last_hour_date_time = self.cs_machine.current_time() - timedelta(hours=1)
        unix_secs = int(last_hour_date_time.timestamp())
        if not timestamp > unix_secs:
            raise CVTestStepFailure("ScheduleInfo.xml timestamp is not within last 1 hour")

    @test_step
    def get_xml_uploaded_file_name(self, query_id, timestamp):
        """Get uploaded xml filename"""
        filename = self.private_metrics.get_uploaded_filename(query_id=query_id, last_collection_time=timestamp)
        digits_to_replace = str(timestamp)[-3:]
        filename_pattern = re.sub(digits_to_replace, '\\\\d{3}', filename) + '$'
        archive_folder = self.metrics_server.get_upload_dir()
        archive_folder = self.metrics_machine.join_path(archive_folder, "Archive")
        if not self.files_in_archive:
            self.files_in_archive = self.metrics_machine.get_files_in_path(archive_folder)
        filename = [file for file in self.files_in_archive if re.search(filename_pattern, file)][0]
        self.log.info("uploaded filename: " + filename)
        return filename

    @test_step
    def get_query_ids_from_uploaded_xml(self, xml_file):
        """Get query ids present in uploaded xml file"""
        query_ids = self.metrics_server.get_queryids_from_uploaded_xml(xml_file)
        if not query_ids:
            raise CVTestStepFailure("Uploaded XML does not have any results")
        self.log.info("Query ids present in XML file:" + str(query_ids))
        return query_ids

    @test_step
    def check_queries_in_uploaded_xml(self, query_ids_from_schedule_info, timestamp):
        """Check if compulsory queries present in uploaded xml file"""
        for xml_query in query_ids_from_schedule_info:
            self.log.info("Checking upload results for: " + xml_query)
            query_id = int(re.split("[_.]", xml_query)[1])
            xml_file_name = self.get_xml_uploaded_file_name(query_id, timestamp)
            list_of_queries_not_found_in_xml = []
            query_ids = self.get_query_ids_from_uploaded_xml(xml_file_name)
            for query in self.compulsory_queries:
                if query not in query_ids:
                    self.log.error("QueryId:" + query + " results found in uploaded xml: " + xml_file_name)
                    list_of_queries_not_found_in_xml.append(query)

            if list_of_queries_not_found_in_xml:
                raise CVTestStepFailure(f"Results not found in uploaded xml for QueryIds "
                                        + str(list_of_queries_not_found_in_xml))
            self.log.info("Verified results for: " + xml_query)

    def run(self):
        """Run function of this test case"""
        try:

            self.init_tc()
            self.if_schedule_info_xml_created()
            query_ids_from_schedule_info = self.get_query_ids_from_schedule_info()
            self.log.info("Query ids from ScheduleInfo.xml are: " + str(query_ids_from_schedule_info))
            timestamp = self.get_timestamp_from_schedule_info()
            self.check_timestamp(timestamp)
            self.check_queries_in_uploaded_xml(query_ids_from_schedule_info, timestamp)
            self.log.info("Successfully verified that collection and upload are happening in every 60 minutes")

        except Exception as exp:
            handle_testcase_exception(self, exp)