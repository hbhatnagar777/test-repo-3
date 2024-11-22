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

from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Application.Exchange.ExchangeMailbox.msgraph_helper import CVEXMBGraphOps
from Reports.utils import TestCaseUtils
from AutomationUtils.database_helper import MSSQL
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from collections import defaultdict, OrderedDict

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "O365 auto discovery configuration"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.exmbclient_object = None
        self.archive_policy = None
        self.cleanup_policy = None
        self.retention_policy = None
        self.subclient = None
        self.navigator = None

    def setup(self):
        """Setup function for testcase execution"""
        self.log.info("Creating exchange mailbox client object")
        self.exmbclient_object = ExchangeMailbox(self)
        self.solr_search_obj = SolrSearchHelper(self)
        self.msgraph_helper = CVEXMBGraphOps(self.exmbclient_object)
        self.user=self.tcinputs["Users"].split(",")
        self.filter_value=self.tcinputs['filter_value']
        self.mssql = MSSQL(
            self.tcinputs['SQLServerName'],
            self.tcinputs['SQLUsername'],
            self.tcinputs['SQLPassword'],
            'CommServ',
            as_dict=False)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Client creation successful")
        self.subclient = self.exmbclient_object.cvoperations.subclient

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console,
                                           is_react=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
            self.office365_obj.add_user(self.user)
            self.office365_obj.run_backup()
            for filters in self.filter_value:
                self.navigator.navigate_to_office365()
                self.office365_obj.access_office365_app(self.exmbclient_object.client_name)
                job_details=self.office365_obj.run_restore(mailbox=False,filter_value=filters)
                self.log.info(f"Restore was successful with filter {filters}")
                self.solr_helper = SolrHelper(self.exmbclient_object)
                self.new_solr_query=self.solr_helper.create_solr_q_filed_parameter(filter_value=filters)
                client_id = self.commcell.clients.get(self.exmbclient_object.client_name).client_id
                self.email_count=self.solr_helper.get_emails_from_index_server(solr_query=dict(self.new_solr_query),mssql=self.mssql,client_id=client_id,search_obj=self.solr_search_obj)
                if int(job_details['Skipped messages'])+int(job_details['Successful messages'])!=self.email_count:
                    raise Exception(f"Email count from solr {self.email_count} and restore job {int(job_details['Skipped messages'])+int(job_details['Successful messages'])} are mismatched")
                self.log.info(f"Email count from solr {self.email_count} and restore {int(job_details['Skipped messages'])+int(job_details['Successful messages'])} are verified")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.exmbclient_object.client_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
