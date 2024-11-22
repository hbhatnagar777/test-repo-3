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
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import random
import base64
from datetime import datetime, timezone
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing-
    Exchange Journaling: Verification of basic search filter for email metadata ,
     in Advanced search of Compliance Search from admin console"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange Journaling: Verification of basic search filter for" \
                    " email metadata, in Advanced search of Compliance Search from admin console"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.accessnodes = None
        self.globaladmin = None
        self.password = None
        self.show_to_user = False
        self.tcinputs = {
            "IndexServer": None,
            "SearchKeyword": None
        }
        # Test Case constants
        self.indexservercloud = None
        self.search_keyword = None
        self.email_address_list = None
        self.subject_list = None
        self.has_attach_list = None
        self.attachment_name_list = None
        self.receivedtime_list = None
        self.folders_list = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solrquery_params = None
        self.solr_helper_obj = None
        self.advanced_search_results = -1
        self.count_solr = -1
        self.test_case_error = None
        self.baseurl = None
        self.encoded_pwd = None
        self.q_string = None
        self.mssql = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            # Test Case constants
            self.indexservercloud = self.tcinputs['IndexServer']
            self.search_keyword = self.tcinputs['SearchKeyword']
            self.email_address_list = self.tcinputs['EmailAddress']
            self.from_address_list = self.tcinputs['FromAddress']
            self.to_address_list = self.tcinputs['ToAddress']
            self.cc_address_list = self.tcinputs['CCAddress']
            self.bcc_address_list = self.tcinputs['BCCAddress']
            self.subject_list = self.tcinputs['Subject']
            self.has_attach_list = self.tcinputs['HasAttachment']
            self.attachment_name_list = self.tcinputs['AttachmentName']
            self.receivedtime_range_list = self.tcinputs['ReceivedTimeRange']
            self.folders_list = self.tcinputs['Folder']
            self.baseurl = self.commcell._web_service
            if self.baseurl[-1] == '/':
                self.baseurl = self.baseurl[:-1]
            admin_pwd = self.inputJSONnode['commcell']['loginPassword']
            encodedBytes_pwd = base64.b64encode(admin_pwd.encode("utf-8"))
            self.encoded_pwd = str(encodedBytes_pwd, "utf-8")
            self.ex_object = ExchangeMailbox(self)
            self.solr_search_obj = SolrSearchHelper(self)
            self.solrquery_params = {'start': 0, 'rows': 50}
            server_name = self.tcinputs['SQLServerName']
            user = self.tcinputs['SQLUsername']
            password = self.tcinputs['SQLPassword']
            self.mssql = MSSQL(
                server_name,
                user,
                password,
                'CommServ',
                as_dict=False,
                use_pyodbc=False)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def query_indexserver_get_results(self):
        """
            Query IndexServer for given keyword and filter criteria
        """
        self.log.info("Getting search results count from Index Server")
        params = {'start': 0, 'rows': 50}
        search_base_url = self.solr_search_obj.construct_virtual_index_query(
            "Journal Index", self.inputJSONnode['commcell']['loginUsername'], self.mssql,
            self.indexservercloud, isadvancedsearch=True, datatypes_search=[
                "journalmailbox", "smtpmailbox"])
        self.solr_helper_obj = SolrHelper(self.ex_object, search_base_url)
        solr_results = self.solr_search_obj.create_url_with_debug_query_and_get_response(
            self.solr_helper_obj, {'keyword': self.q_string}, op_params=params)
        self.count_solr = self.solr_helper_obj.get_count_from_json(
            solr_results.content)
        if self.count_solr == -1:
            raise CVTestStepFailure(f"Error getting results from Solr")
        self.log.info("Solr Query returns %s items", self.count_solr)

    @test_step
    def advanced_search_emailaddress_from_to_cc_subject_default_operators(
            self):
        """
            Perform AdvancedSearch for Keywords and filters through REST API call
            Filters: From, To, CC, Email Address, Subject, with default operators
        """
        email_filters = {}
        emailaddress_list = random.sample(self.email_address_list, 2)
        str1 = ';'.join(emailaddress_list)
        emailaddress_str = "OR;" + str1
        email_filters['EMAIL_RECIPIENTLIST'] = emailaddress_str

        fromaddress_list = random.sample(self.from_address_list, 2)
        str1 = ';'.join(fromaddress_list)
        fromaddress_str = "OR;" + str1
        email_filters['EMAIL_FROM'] = fromaddress_str

        subject_list = random.sample(self.subject_list, 2)
        str1 = ';'.join(subject_list)
        subject_str = "OR;" + str1
        email_filters['EMAIL_SUBJECT'] = subject_str

        toaddress_list = random.sample(self.to_address_list, 2)
        str1 = ';'.join(toaddress_list)
        toaddress_str = "OR;" + str1
        email_filters['EMAIL_TO'] = toaddress_str

        ccaddress_list = random.sample(self.cc_address_list, 2)
        str1 = ';'.join(ccaddress_list)
        ccaddress_str = "OR;" + str1
        email_filters['EMAIL_CC'] = ccaddress_str

        email_filters["usermailbox"] = 0
        email_filters["journalmailbox"] = 1
        email_filters["smtpmailbox"] = 1

        self.advanced_search_results = self.solr_search_obj.\
            submit_advanced_search_api_request(self.baseurl,
                                               self.inputJSONnode['commcell']['loginUsername'],
                                               self.encoded_pwd, self.indexservercloud,
                                               self.search_keyword, "AND", email_filters)
        self.log.info(
            "Advanced Search API returns %s items",
            self.advanced_search_results)
        if self.advanced_search_results == -1:
            raise CVTestStepFailure(f"Error getting Advanced Search results")

        self.q_string = ""

        emailadd_q_search_string = "(rclst:" + emailaddress_list[0] \
            + " OR " + "rclst:" + emailaddress_list[1] + ")"
        self.q_string = self.q_string + emailadd_q_search_string + " AND "

        from_q_search_string = "(fromdisp:" + fromaddress_list[0] \
            + " OR " + "fromdisp:" + fromaddress_list[1] + ")"
        self.q_string = self.q_string + from_q_search_string + " AND "

        to_q_search_string = "(todisp:" + toaddress_list[0] \
            + " OR " + "todisp:" + toaddress_list[1] + ")"
        self.q_string = self.q_string + to_q_search_string + " AND "

        subject_q_search_string = "(conv:" + subject_list[0] \
            + " OR " + "conv:" + subject_list[1] + ")"
        self.q_string = self.q_string + subject_q_search_string + " AND "

        cc_q_search_string = "(ccdisp:" + ccaddress_list[0] \
            + " OR " + "ccdisp:" + ccaddress_list[1] + ")"
        self.q_string = self.q_string + cc_q_search_string + \
            " AND (" + self.search_keyword + ")"

    @test_step
    def advanced_search_emailaddress_from_to_cc_subject_non_default_operators(
            self):
        """
            Perform AdvancedSearch for Keywords and filters through REST API call
            Filters: From, To, CC, Email Address, Subject, with non default operators
        """
        email_filters = {}
        emailaddress_list = random.sample(self.email_address_list, 2)
        str1 = ';'.join(emailaddress_list)
        emailaddress_str = "AND;" + str1
        email_filters['EMAIL_RECIPIENTLIST'] = emailaddress_str

        fromaddress_list = random.sample(self.from_address_list, 2)
        str1 = ';'.join(fromaddress_list)
        fromaddress_str = "NOT;" + str1
        email_filters['EMAIL_FROM'] = fromaddress_str

        subject_list = random.sample(self.subject_list, 2)
        str1 = ';'.join(subject_list)
        subject_str = "AND;" + str1
        email_filters['EMAIL_SUBJECT'] = subject_str

        toaddress_list = random.sample(self.to_address_list, 2)
        str1 = ';'.join(toaddress_list)
        toaddress_str = "AND;" + str1
        email_filters['EMAIL_TO'] = toaddress_str

        ccaddress_list = random.sample(self.cc_address_list, 2)
        str1 = ';'.join(ccaddress_list)
        ccaddress_str = "AND;" + str1
        email_filters['EMAIL_CC'] = ccaddress_str

        email_filters["usermailbox"] = 0
        email_filters["journalmailbox"] = 1
        email_filters["smtpmailbox"] = 1

        self.advanced_search_results = self.solr_search_obj. \
            submit_advanced_search_api_request(self.baseurl,
                                               self.inputJSONnode['commcell']['loginUsername'],
                                               self.encoded_pwd, self.indexservercloud,
                                               self.search_keyword, "OR", email_filters)
        self.log.info(
            "Advanced Search API returns %s items",
            self.advanced_search_results)
        if self.advanced_search_results == -1:
            raise CVTestStepFailure(f"Error getting Advanced Search results")

        self.q_string = ""

        emailadd_q_search_string = "((rclst:" + emailaddress_list[0] \
                                   + " AND " + "rclst:" + emailaddress_list[1] + ")"
        self.q_string = self.q_string + emailadd_q_search_string + " OR "

        to_q_search_string = "(todisp:" + toaddress_list[0] \
                             + " AND " + "todisp:" + toaddress_list[1] + ")"
        self.q_string = self.q_string + to_q_search_string + " OR "

        cc_q_search_string = "(ccdisp:" + ccaddress_list[0] \
                             + " AND " + "ccdisp:" + ccaddress_list[1] + ")"
        self.q_string = self.q_string + cc_q_search_string + " OR "

        subject_q_search_string = "(conv:" + subject_list[0] \
                                  + " AND " + "conv:" + subject_list[1] + "))"
        self.q_string = self.q_string + subject_q_search_string

        from_q_search_string = "NOT((fromdisp:" + fromaddress_list[0] \
                               + " OR " + "fromdisp:" + fromaddress_list[1] + "))"
        self.q_string = self.q_string + from_q_search_string + \
            " AND (" + self.search_keyword + ")"

    def get_epochtime(self, time_list):
        """
        Converts date to unix epoch timestamp
        :param time_list: List of dates in the format of string
        :return: List of dates in unix epoch time format
        """
        epoch_t = []
        for t in time_list:
            date_obj = datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
            unix_time = int(date_obj.replace(tzinfo=timezone.utc).timestamp())
            epoch_t.append(str(unix_time))
        return epoch_t

    @test_step
    def advanced_search_folder_receivedtime_att_bcc_default_operators(self):
        """
            Perform AdvancedSearch for Keywords and filters through REST API call
            Filters: folder name ,Received time, has attachment,
             attachment name, with non default operators
        """
        email_filters = {}
        email_filters["FOLDER"] = "OR;" + self.folders_list[0]

        receivedtime_unix_list = self.get_epochtime(
            self.receivedtime_range_list)
        str1 = ';'.join(receivedtime_unix_list)
        time_str = "RANGE;" + str1
        email_filters['EMAIL_RECEIVED_TIME'] = time_str

        hasattach = random.choice(self.has_attach_list)
        hasattach_str = "NONE;" + hasattach
        email_filters['HAS_ATTACHMENT'] = hasattach_str

        att_list = random.sample(self.attachment_name_list, 2)
        str1 = ';'.join(att_list)
        att_str = "OR;" + str1
        email_filters['EMAIL_ATTACHMENTNAME'] = att_str

        bccaddress_list = random.sample(self.bcc_address_list, 2)
        str1 = ';'.join(bccaddress_list)
        bccaddress_str = "OR;" + str1
        email_filters['EMAIL_BCC_ADMIN'] = bccaddress_str

        email_filters["usermailbox"] = 0
        email_filters["journalmailbox"] = 1
        email_filters["smtpmailbox"] = 1

        self.advanced_search_results = self.solr_search_obj. \
            submit_advanced_search_api_request(self.baseurl,
                                               self.inputJSONnode['commcell']['loginUsername'],
                                               self.encoded_pwd, self.indexservercloud,
                                               self.search_keyword, "AND", email_filters)
        self.log.info(
            "Advanced Search API returns %s items",
            self.advanced_search_results)
        if self.advanced_search_results == -1:
            raise CVTestStepFailure(f"Error getting Advanced Search results")

        solr_date_range = "[" + self.receivedtime_range_list[0] +\
                          " TO " + self.receivedtime_range_list[1] + "]"

        self.q_string = ""

        folder_q_search_string = "(folder:\"" + \
            self.folders_list[0] + "\")"
        self.q_string = self.q_string + folder_q_search_string + " AND "

        receivedtime_q_search_string = "(mtm:" + solr_date_range + ")"
        self.q_string = self.q_string + receivedtime_q_search_string + " AND "

        hasattach_q_search_string = "(hasattach:" + hasattach + ")"
        self.q_string = self.q_string + hasattach_q_search_string + " AND "

        attnames_q_search_string = "((attname:" + att_list[0] \
            + " OR " + "attname:" + att_list[1] + "))"
        self.q_string = self.q_string + attnames_q_search_string + " AND "

        bcc_q_search_string = "(bccdisp:" + bccaddress_list[0] \
                              + " OR " + "bccdisp:" + bccaddress_list[1] + ") OR (bccdisp_admin:" + bccaddress_list[0] \
                              + " OR " + "bccdisp_admin:" + bccaddress_list[1] + ")"
        self.q_string = self.q_string + bcc_q_search_string + " OR "
        self.q_string = self.q_string + bcc_q_search_string + \
                        " AND (" + self.search_keyword + ")"

        self.q_string = self.q_string + bcc_q_search_string + \
            " AND (" + self.search_keyword + ")"

    @test_step
    def validate_search_results(self):
        """
           Check if the items count from AdvancedSearch and Indexserver match
        """
        self.log.info(
            "Advanced Search API Returned [%s], IndexServer Solr Query Returned [%s]",
            self.advanced_search_results,
            self.count_solr)
        if int(self.advanced_search_results) != int(self.count_solr):
            self.test_case_error = (
                "Advanced Search Returned [%s], "
                "IndexServer Solr Query Returned [%s]. ",
                self.advanced_search_results,
                self.count_solr)
            raise CVTestStepFailure(self.test_case_error)

    def run(self):
        try:
            self.init_tc()
            self.advanced_search_emailaddress_from_to_cc_subject_default_operators()
            self.query_indexserver_get_results()
            self.validate_search_results()
            self.advanced_search_emailaddress_from_to_cc_subject_non_default_operators()
            self.query_indexserver_get_results()
            self.validate_search_results()
            self.advanced_search_folder_receivedtime_att_bcc_default_operators()
            self.query_indexserver_get_results()
            self.validate_search_results()
        except Exception as err:
            handle_testcase_exception(self, err)
