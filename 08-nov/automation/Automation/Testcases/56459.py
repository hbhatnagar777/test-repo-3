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

import time

from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for Verification of configuring definitions with multiple filter criteria"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Verification of configuring definitions with multiple filter criteria'
        self.data_type = 'Exchange journaling'
        self.index_server_email_num = 0
        self.case_name = None
        self.def_name = None
        self.custodians = None
        self.def_custodians = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.jobs = None
        self.index_copy_job_id = None
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "CaseCustodians": None,
            "CaseKeyword": None,
            "DefinitionName": None,
            "DefinitionCustodians": None,
            "DefinitionKeyword": None,
            "Filters": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None
        }
        self.mssql = None
        self.table = None
        self.custodians_num = None
        self.emails_num = None
        self.ex_object = None
        self.solr_search_obj = None
        self.solr_helper_obj = None

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['loginUsername'],
                self.inputJSONnode['commcell']['loginPassword'])

            self.activate = GovernanceApps(self.admin_console)
            self.case_manager = CaseManager(self.admin_console)
            self.jobs = Jobs(self.admin_console)
            self.ex_object = ExchangeMailbox(self)
            self.solr_search_obj = SolrSearchHelper(self)
            self.table = Table(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()

            self.case_name = self.tcinputs['CaseName'] + str(int(time.time()))
            self.def_name = self.tcinputs['DefinitionName'] + \
                str(int(time.time()))
            self.custodians = self.tcinputs['CaseCustodians']
            self.def_custodians = self.tcinputs['DefinitionCustodians']

            server_name = self.tcinputs['SQLServerName']
            user = self.tcinputs['SQLUsername']
            password = self.tcinputs['SQLPassword']
            self.mssql = MSSQL(
                server_name,
                user,
                password,
                'CommServ',
                as_dict=False)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_case_manager_client(self):
        """Enter basic details, custodians, keyword and save it"""
        try:
            self.case_manager.select_add_case()
            self.case_manager.enter_case_details(
                self.case_name,
                self.data_type,
                'Continuous',
                self.custodians,
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['CaseKeyword']
            )
            self.log.info('Case Added')
        except Exception:
            raise CVTestStepFailure("Error creating case")

    @test_step
    def trigger_collection_job(self):
        """Triggers collection job and waits for it to complete"""
        try:
            self.case_manager.submit_collection_job()
            self.index_copy_job_id = str(
                self.case_manager.get_index_copy_job_id())

            self.jobs.job_completion(self.index_copy_job_id)
        except BaseException:
            raise CVTestStepFailure("Error triggering collection job")

    @test_step
    def add_definition(self):
        """Creates another definition for the case"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            if self.table.is_entity_present_in_column('Name', self.case_name):
                self.case_manager.select_case(self.case_name)
                self.case_manager.select_add_definition()
                self.case_manager.create_definition(
                    self.def_name,
                    self.data_type,
                    'One time only',
                    self.def_custodians,
                    self.tcinputs['DefinitionKeyword'],
                    self.tcinputs['Filters'],
                )
                self.log.info('Definition Added')
            else:
                raise CVTestStepFailure('Error finding case')
        except BaseException:
            raise CVTestStepFailure('Error adding definition')

    @test_step
    def get_no_of_custodians_and_emails(self):
        """Getting the number of custodians and emails from admin console"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()

            if self.table.is_entity_present_in_column('Name', self.case_name):
                self.case_manager.select_case(self.case_name)
                self.custodians_num = int(self.case_manager.get_custodian_count(self.case_name))
                self.log.info(
                    'Identified number of custodians as %s',
                    self.custodians_num)

                self.case_manager.open_search_tab()
                self.case_manager.click_search_button()
                try:
                    self.emails_num = int(self.table.get_total_rows_count())
                except IndexError:
                    self.emails_num = 0

            self.log.info('Identified number of emails as %s', self.emails_num)
        except Exception:
            raise CVTestStepFailure(
                "Error getting the number of custodians and emails")

    def construct_argument_for_solr_query(self, def_name, server_type, schema_version):
        """To create the dictionary which is passed as argument to create solr query"""
        filters = self.tcinputs['Filters']
        filters_dict = dict()
        if def_name == self.def_name:
            if server_type == '1' and (schema_version == '0' or schema_version == '1'):
                if filters.get('Email address') is not None:
                    params = ('fmsmtp', 'tosmtp', 'ccsmtp', 'bcsmtp_admin')
                    filters_dict[params] = filters.get('Email address')
                if filters.get('From') is not None:
                    if 'fmsmtp' in filters_dict:
                        filters_dict['fmsmtp'].append(filters.get('From'))
                    else:
                        filters_dict['fmsmtp'] = filters.get('From')
                if filters.get('To') is not None:
                    if 'tosmtp' in filters_dict:
                        filters_dict['tosmtp'].append(filters.get('To'))
                    else:
                        filters_dict['tosmtp'] = [filters.get('To')]
                if filters.get('CC') is not None:
                    if 'ccsmtp' in filters_dict:
                        filters_dict['ccsmtp'].append(filters.get('CC'))
                    else:
                        filters_dict['ccsmtp'] = [filters.get('CC')]
                if filters.get('BCC') is not None:
                    if 'bcc_admin' in filters_dict:
                        filters_dict['bcc_admin'].append(filters.get('BCC'))
                    else:
                        filters_dict['bcc_admin'] = [filters.get('BCC')]
                if filters.get('Has attachment') is not None:
                    filters_dict['hasattach'] = filters.get('Has attachment')
                if filters.get('Attachment name') is not None:
                    filters_dict['attname'] = [filters.get('Attachment name')]
                if filters.get('Subject') is not None:
                    filters_dict['conv'] = filters.get('Subject')
                if filters.get('Folder') is not None:
                    if filters.get('Folder')[1] in [
                        'Match exact folder path',
                            'Folder path contains pattern']:
                        filters_dict['folder'] = filters.get('Folder')[0]
                    elif filters.get('Folder')[1] == 'Folder path contains term':
                        filters_dict['folder'] = '*' + \
                            filters.get('Folder')[0] + '*'
                if filters.get('Received time') is not None:
                    rcv_time = []
                    for i in range(2):
                        r_time = filters.get('Received time')[i]
                        if r_time['Time'] == 'PM':
                            r_time['Hours'] = str(int(r_time['Hours']) + 12)
                        rcv_time.append(
                            r_time['Year'] + '-' +
                            r_time['Month'] + '-' +
                            r_time['Day'] + 'T' +
                            r_time['Hours'] + ':' +
                            r_time['Minutes'] + ':00Z')
                    filters_dict['mtm'] = '[' + rcv_time[0] + \
                                          ' TO ' + rcv_time[1] + ']'
            elif server_type == '5' or (server_type == '1' and schema_version == '2'):
                if filters.get('Email address') is not None:
                    params = ('FromSMTP', 'ToSMTP', 'CCSMTP', 'BccComplianceSMTP')
                    filters_dict[params] = filters.get('Email address')
                if filters.get('From') is not None:
                    if 'FromSMTP' in filters_dict:
                        filters_dict['FromSMTP'].append(filters.get('From'))
                    else:
                        filters_dict['FromSMTP'] = filters.get('From')
                if filters.get('To') is not None:
                    if 'ToSMTP' in filters_dict:
                        filters_dict['ToSMTP'].append(filters.get('To'))
                    else:
                        filters_dict['ToSMTP'] = [filters.get('To')]
                if filters.get('CC') is not None:
                    if 'CCSMTP' in filters_dict:
                        filters_dict['CCSMTP'].append(filters.get('CC'))
                    else:
                        filters_dict['CCSMTP'] = [filters.get('CC')]
                if filters.get('BCC') is not None:
                    if 'BccComplianceSMTP' in filters_dict:
                        filters_dict['BccComplianceSMTP'].append(filters.get('BCC'))
                    else:
                        filters_dict['BccComplianceSMTP'] = [filters.get('BCC')]
                if filters.get('Has attachment') is not None:
                    filters_dict['HasAttachment'] = filters.get('Has attachment')
                if filters.get('Attachment name') is not None:
                    filters_dict['Attachment'] = [filters.get('Attachment name')]
                if filters.get('Subject') is not None:
                    filters_dict['Subject'] = filters.get('Subject')
                if filters.get('Folder') is not None:
                    if filters.get('Folder')[1] in [
                        'Match exact folder path',
                            'Folder path contains pattern']:
                        filters_dict['Folder'] = filters.get('Folder')[0]
                    elif filters.get('Folder')[1] == 'Folder path contains term':
                        filters_dict['Folder'] = '*' + \
                            filters.get('Folder')[0] + '*'
                if filters.get('Received time') is not None:
                    rcv_time = []
                    for i in range(2):
                        r_time = filters.get('Received time')[i]
                        if r_time['Time'] == 'PM':
                            r_time['Hours'] = str(int(r_time['Hours']) + 12)
                        rcv_time.append(
                            r_time['Year'] + '-' +
                            r_time['Month'] + '-' +
                            r_time['Day'] + 'T' +
                            r_time['Hours'] + ':' +
                            r_time['Minutes'] + ':00Z')
                    filters_dict['ReceivedTime'] = '[' + rcv_time[0] + \
                        ' TO ' + rcv_time[1] + ']'
        return filters_dict

    def get_emails_num(self, def_name, keyword):
        """To query the number of emails from index server"""
        email_num = 0
        app_id = '(' + ','.join(self.solr_search_obj.get_app_id(
            def_name, 'source', self.inputJSONnode['commcell']['loginUsername'], self.mssql
        )) + ')'
        details_list, distinct_cid = self.solr_search_obj.get_ci_server_url(
            self.mssql, app_id)
        cloud_name = dict()
        for cloud_id in distinct_cid:
            cloud_name[cloud_id] = self.solr_search_obj.get_index_server_name(
                cloud_id)
        for item in details_list:
            self.ex_object.index_server = cloud_name[item['cloudId']]
            server_type = item['serverType']
            schema_version = item['schemaVersion']
            query_url = item['ciServer'] + '/select?'
            self.solr_helper_obj = SolrHelper(self.ex_object, query_url)
            custodian_list = []
            if def_name == self.def_name:
                for custodian in self.def_custodians:
                    custodian_list.append(custodian)
            else:
                for custodian in self.custodians:
                    custodian_list.append(custodian)
            filters = self.construct_argument_for_solr_query(def_name, server_type, schema_version)
            recipient_list = tuple()
            if item['serverType'] == '5' or (item['serverType'] == '1' and item['schemaVersion'] == '2'):
                recipient_list = ('FromSMTP', 'ToSMTP', 'CCSMTP', 'BccComplianceSMTP')
            elif (item['serverType'] == '1' and
                  (item['schemaVersion'] == '0' or item['schemaVersion'] == '1')):
                recipient_list = ('fmsmtp', 'tosmtp', 'ccsmtp', 'bcc_admin')
            filters[recipient_list] = custodian_list
            filters['keyword'] = keyword
            solr_results = self.solr_helper_obj.create_url_and_get_response(
                filters)
            email_num += self.solr_helper_obj.get_count_from_json(
                solr_results.content)
        return email_num

    @test_step
    def verify_custodian_count(self):
        """Verify the count of custodians"""
        if self.custodians_num != (
                len(self.custodians) + len(self.def_custodians)):
            raise CVTestStepFailure('CUSTODIAN COUNT MISMATCH')

    @test_step
    def verify_email_count(self):
        """Verify the count of emails"""
        try:
            self.index_server_email_num += self.get_emails_num(
                self.case_name + '-definition',
                self.tcinputs['CaseKeyword']
            )
            self.index_server_email_num += self.get_emails_num(
                self.def_name,
                self.tcinputs['DefinitionKeyword']
            )
            self.log.info('No of emails obtained from Solr Query is %s',
                          self.index_server_email_num)
            if self.index_server_email_num != self.emails_num:
                raise CVTestStepFailure('EMAIL COUNT MISMATCH')
        except Exception:
            raise CVTestStepFailure(f'Error Querying the index server')

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.trigger_collection_job()
            self.add_definition()
            self.trigger_collection_job()
            self.get_no_of_custodians_and_emails()
            self.verify_custodian_count()
            self.verify_email_count()
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_manager.delete_case(self.case_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
