# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

Sample Input
"testCases": {
                "47047":{
                    "deconfiguredSubclient": "AIT ePO Servers",
                    "drSubClient": "DR Subclient",
                    "drClient": "wilson64_DN	",
                    "ddbSubClient": "DDBBackup",
                    "indexSubClient": "default",
                    "indexClient": "wilson64-dedup_IndexServer"
                    "storage_policy": "sp"

                }
            }
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure)
from Web.Common.page_object import TestStep
from Reports.Custom.sql_utils import SQLQueries
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.home import ReportsHomePage
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator

from Web.WebConsole.Reports.Metrics.chargeback import (
    GlobalPrice,
    Chargeback,
    ManageBillingTags,
    Tag,
    ChargebackTrends
)


class TestCase(CVTestCase):
    """ChargeBack Report"""
    test_step = TestStep()
    GLOBALPRICE = {
        "Backup": "100",
        "Archive": "90",
        "Primary Application": "80",
        "Protected Application": "70",
        "Data on Media": "60",
        "Total Protected Application": "50",
        "Total Data on Media": "40",
        "Per Client": "30",
        "Per SubClient": "20",
        "Discount Percentage": "10",
        "Discount Size": "5",
        "Discount Entity": "Client",
        "Discount Selection": True
    }

    def __init__(self):
        super(TestCase, self).__init__()
        self.utils = None
        self.db_connection = None
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.chargeback = None
        self.name = "ChargeBack Report Validation"

        self.tcinputs = {
                "deconfiguredSubclient": None,
                "drSubClient": None,
                "drClient": None,
                'ddbClient': None,
                "ddbSubClient": None,
                "indexSubClient": None,
                "indexClient": None,
                "storage_policy": None
            }

    def init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()

            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)

            self.webconsole.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                  self.inputJSONnode["commcell"]["commcellPassword"])

            self.utils = TestCaseUtils(self, self.inputJSONnode["commcell"]["commcellUsername"],
                                       self.inputJSONnode["commcell"]["commcellPassword"])
            self.navigator = Navigator(self.webconsole)
            self.webconsole.goto_reports()
            report_home_page = ReportsHomePage(self.webconsole)
            report_home_page.goto_report("Chargeback")
            self.chargeback = Chargeback(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_global_prices(self):
        """Verifies the Global Prices being saved"""
        global_price = GlobalPrice()
        self.chargeback.add_global_price(global_price)
        global_price.set_front_end_cost(TestCase.GLOBALPRICE['Backup'],
                                        TestCase.GLOBALPRICE['Archive'])
        global_price.set_current_month_or_week_cost(TestCase.GLOBALPRICE['Primary Application'],
                                                    TestCase.GLOBALPRICE['Protected Application'],
                                                    TestCase.GLOBALPRICE['Data on Media'])
        global_price.set_lifetime_cost(TestCase.GLOBALPRICE['Total Protected Application'],
                                       TestCase.GLOBALPRICE['Total Data on Media'])
        global_price.set_additional_cost(
            TestCase.GLOBALPRICE['Per Client'], TestCase.GLOBALPRICE['Per SubClient'])
        global_price.discount(True,
                              TestCase.GLOBALPRICE['Discount Percentage'],
                              TestCase.GLOBALPRICE['Discount Size'],
                              TestCase.GLOBALPRICE['Discount Entity'])
        global_price.save_and_recalculate()
        self.chargeback.open_global_price()
        SQLQueries.validate_equality(TestCase.GLOBALPRICE, global_price.get_price_details())
        global_price.close()

    @test_step
    def verify_billing_tags(self):
        """Verify creation association and deletion of billing tags"""
        self.chargeback.access_billing_tags()
        manage = ManageBillingTags(self.webconsole)
        tag_name = 'TC47047'
        # Deletion
        if manage.has_billing_tag(tag_name):
            manage.delete_billing_tag(tag_name)

        # Creation
        tag = Tag()
        manage.add_new_billing_tag(tag)
        tag.add_name(tag_name)
        tag.add_size_type()
        tag.add_price()
        tag.add_additional_price_details(price_level="Client", value="10")
        tag.add_discount(discount_level="Subclient", size="5", percentage="25")
        tag.save()

        # Association
        manage.add_associate_billing_tag(tag_name, self.commcell.commserv_name)
        manage.delete_associate_billing_tags(tag_name)
        sp = self.commcell.storage_policies.get(self.tcinputs["storage_policy"])
        copy_name = list(sp.copies.keys())[0]
        manage.add_storage_policy_copy_association_for_tag(
            tag_name, self.commcell.commserv_name,self.tcinputs["storage_policy"], copy_name)
        manage.delete_storage_policy_copy_association_for_tags(tag_name)

        manage.add_agent_association_for_tag(tag_name)
        manage.delete_agent_association_for_tags(tag_name)
        self.navigator.goto_page_via_breadcrumb("Chargeback")

    @test_step
    def verify_grouping(self):
        """Verifies proper grouping of Chargeback report"""
        entities = ["Tenants", "CommCells", "Client Groups", "Clients",
                    "SubClients", "SubClient per Copy", "Billing Tags"]
        report = MetricsReport(self.webconsole)
        for entity in entities:
            self.chargeback.generate_report(entity)
            table_titles = [table.get_table_title() for table in report.get_tables()]
            if [entity] != table_titles:
                raise CVTestStepFailure(
                    f"Generate Report with Group By {entity} contains {table_titles} in report")

    @test_step
    def verify_trending_report(self):
        """Verifies proper loading of trending report"""
        page_title = "Daily Chargeback Trends - By {}"
        self.chargeback.open_chargeback_trends()
        report = MetricsReport(self.webconsole)
        report.verify_page_load()
        chargeback_trends = ChargebackTrends(self.webconsole)

        chargeback_trends.view_commcell_details()
        if report.get_page_title() != page_title.format("CommCells"):
            raise CVTestStepFailure(
                f"{report.get_page_title()} is seen instead of {page_title.format('CommCells')}")
        self.navigator.goto_page_via_breadcrumb("Chargeback Trends")

        chargeback_trends.view_client_details()
        if report.get_page_title() != page_title.format("Clients"):
            raise CVTestStepFailure(
                f"{report.get_page_title()} is seen instead of {page_title.format('Clients')}")
        self.navigator.goto_page_via_breadcrumb("Chargeback Trends")

        chargeback_trends.view_agents_details()
        if report.get_page_title() != page_title.format("Agents"):
            raise CVTestStepFailure(
                f"{report.get_page_title()} is seen instead of {page_title.format('Agents')}")
        self.navigator.goto_page_via_breadcrumb("Chargeback Trends")

        chargeback_trends.view_storage_policies_details()
        if report.get_page_title() != page_title.format("Storage Policies"):
            raise CVTestStepFailure(f"{report.get_page_title()} is seen instead of"
                                    f" {page_title.format('Storage Policies')}")

    @test_step
    def verify_deconfigured_subclient(self):
        """
        Verify that deconfigured subclient are excluded"""
        deconfigured_subclient_vals = []
        report = MetricsReport(self.webconsole)
        self.chargeback.generate_report("SubClients", exclude_deconfigured_subclients=True)
        table = report.get_table('SubClients')
        table.set_filter("Client", self.tcinputs["ddbClient"])
        deconfigured_subclient_vals = table.get_data_from_column("Subclient")

        if self.tcinputs["deconfiguredSubclient"] in deconfigured_subclient_vals:
            raise CVTestStepFailure(
                f"Deconfigured subclient [{self.tcinputs['deconfiguredSubclient']}] isn't excluded"
                )
        else:
            self.log.info("Deconfigured subclients are not included")

    @test_step
    def verify_ddr(self):
        """
        Verify that our own DDR, DDB, Index Subclients show up when the include box is checked
        """
        report = MetricsReport(self.webconsole)
        self.chargeback.generate_report("SubClients", include_dr_subclients=True)
        for table in report.get_tables():
            table.set_filter("Client", self.tcinputs["ddbClient"])
            client_vals = table.get_data_from_column("Client")
            if len(client_vals) > 0:
                self.log.info("DDB is working properly")
            else:
                raise CVTestStepFailure("DDB subclient (DDBackup) is not showing up")

            table.set_filter("Subclient", self.tcinputs["indexSubClient"])
            table.set_filter("Client", self.tcinputs["indexClient"])
            client_vals = table.get_data_from_column("Client")
            if len(client_vals) > 0:
                self.log.info("index is working properly")
            else:
                raise CVTestStepFailure("index (default) is not showing up")

            # enable after DR subclients are collected
            """
            table.set_filter("Subclient", self.tcinputs["drSubclient"])
            table.set_filter("Client", self.tcinputs["drClient"])
            client_vals = table.get_data_from_column("Client")
            if len(client_vals) > 0:
                self.log.info("DR is working properly")
            else:
                raise CVTestStepFailure("DR subclient (DR Subclient) is not showing up")
            """

    @test_step
    def verify_fet(self):
        """Verify that display FET checkbox works"""
        report = MetricsReport(self.webconsole)
        self.chargeback.generate_report(
            "SubClients", size_unit='GB', display_fet=True, time_interval='Daily')
        for table in report.get_tables():
            table.set_filter("Client", self.tcinputs["fetClient"])
            table.set_filter("Agent", "Virtual Center")
            client_vals = table.get_data_from_column("Front End Backup Size")
            if not client_vals:
                raise CVTestStepFailure(
                    f'FET Client {self.tcinputs["fetClient"]} doesnt have Front End Backup Size')
            if float(client_vals[0]) > 0:
                self.log.info("FET is working properly")
            else:
                raise CVTestStepFailure(f'FET of VM {self.tcinputs["fetClient"]} is still 0')

    def run(self):
        try:
            self.init_tc()
            self.verify_global_prices()
            self.verify_billing_tags()
            self.verify_grouping()
            self.verify_deconfigured_subclient()
            self.verify_ddr()
            self.verify_fet()
            self.verify_trending_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
