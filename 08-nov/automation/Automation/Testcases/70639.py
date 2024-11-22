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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report

from Web.AdminConsole.AD.ad import ADClientsPage, CvAd, ADPage
from Web.AdminConsole.AD.azuread import AzureADPage
from Web.AdminConsole.AD.page_ops import check_element, check_dchildren
import time
from Web.AdminConsole.Components.table import Table, Rtable
from selenium.webdriver.common.by import By

class TestCase(CVTestCase):
    """" Class for executing AD/Azure AD Health  Report Validataion"""

    def __init__(self):
        """Initial the class"""
        super().__init__()
        self.name = "AD/Azure AD Health  Report Validataion"
        self.tcinputs = {}

        self.browser = None
        self.driver = None
        self.adminconsole = None
        self.adclientspage = None
        self.adpage = None
        self.azureadpage = None
        self.adclientsinfo = {}
        self.aadclientsinfo = {}
        self.mspuser = None
        self.msppassword = None
        self.tenantuser = None
        self.tenantname = None
        self.reports = None
        self.table = None
        self.adhealthreport = {}
        self.aadhealthreport = {}
        self.cvad = None

        self.tcinputs = {
            "MspUser": None,
            "MspUserPassword": None,
            "TenantName" : None
        }

    def switch_company(self, company="Reset"):
        """Switch company"""
        company_element = check_element(self.driver,"id", "header-company-dropdown-wrapper")
        company_element.click()
        time.sleep(5)
        copmany_search = check_element(self.driver, "id", "header-company-dropdownSearchInput")
        copmany_search.send_keys(company)
        time.sleep(5)
        avail_objs = check_dchildren(check_dchildren(company_element,pc=1),pc=2)
        self.log.debug(f"found the companies: {avail_objs.text}")
        for _ in check_dchildren(avail_objs):
            if company in _.text:
                self.log.debug(f"found the company: {company}")
                _.click()
                self.adminconsole.wait_for_completion()
                break
        self.log.debug(f"switch to company: {company}")


    @TestStep()
    def collect_ad_aad_info(self):
        """Collect AD/AAD information from clients list page"""
#        self.adminconsole.navigator.switch_company_as_operator(self.tenantname)
        self.switch_company(self.tenantname)   
        self.log.debug("switch view to tenant view")
        self.adclientspage = ADClientsPage(self.adminconsole)
        self.adpage = ADPage(self.adminconsole, self._commcell)
        self.cvad = CvAd(self.adpage,self.tcinputs, ADconnect=False, adclientspage=self.adclientspage)
        adinfo = self.adclientspage.get_ad_clients(details=True) 
        self.adclientsinfo, self.aadclientsinfo = self.cvad.adinfo_process(adinfo)
        self.log.debug('remove company filter')
#        self.adminconsole.navigator.switch_company_as_operator("Reset")
        self.switch_company()
        self.log.debug("switch view to MSP view")


    @TestStep()
    def check_health_report(self, reportname="Active Directory Backup Health"):
        """Check Health Report"""
#        self.adminconsole.navigator.navigate_to_health_reports()
        self.adminconsole.navigator.search_nav_by_id(nav="Reports", nav_id="navigationItem_reports")
        self.adminconsole.wait_for_completion()
        self.reports = Report(self.adminconsole)
        for _ in self.reports.get_all_reports():
            if _['name'] == "Active Directory Backup Health":
                self.driver.get(_['href'])
                self.log.debug(f"found the report: {self.driver.current_url}")
                self.adminconsole.wait_for_completion()
                break
        self.switch_company(self.tenantname)
        self.log.info(f"filter the report with company: {self.tenantname}")

    @TestStep()
    def check_ad_health_report(self):
        """Check AD Health Report"""
        self.adminconsole.click_by_id("Active Directory")
        self.adminconsole.wait_for_completion()
        self.log.debug("go to AD reprot page")
        self.adhealthreport['health_status'], self.adhealthreport['health_info'] = self.cvad.health_content()
        self.log.debug(f"health report: {self.adhealthreport}")

    @TestStep()
    def check_azure_ad_health_report(self):
        """Check Azure AD Health Report"""
        self.adminconsole.click_by_id("Azure Active Directory")
        self.log.debug("go to Azure AD reprot page")
        self.adminconsole.wait_for_completion() 
        self.aadhealthreport['health_status'], self.aadhealthreport['health_info'] = self.cvad.health_content()
        self.log.debug(f"health report: {self.aadhealthreport}")

    @TestStep()
    def compare_health_report(self):
        """Compare the health report information"""
        self.cvad.health_info_comparre(self.adclientsinfo, self.adhealthreport, mutliplesubclients=True)
        self.cvad.health_info_comparre(self.aadclientsinfo, self.aadhealthreport)

    def setup(self):
        """Setup the variables for running the test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.log.info("open the browser")
        self.log.info(f"self.commcell: {self.commcell}, {dir(self.commcell)}")
        self.driver = self.browser.driver
        self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)

        self.mspuser = self.tcinputs['MspUser']
        self.msppassword = self.tcinputs['MspUserPassword']
        self.tenantname = self.tcinputs['TenantName']

        self.adminconsole.login(self.mspuser, self.msppassword)
        self.log.info("Logged into Admin Console")
        self.adminconsole.wait_for_completion()

        self.adminconsole.navigator.navigate_to_activedirectory()
        self.adminconsole.wait_for_completion()

    def run(self):
        """Run the test case"""
        # collect ad/aad clients information
        self.collect_ad_aad_info()
        # go to health report to check 
        self.check_health_report()
        # start to collec information from health report
        self.check_ad_health_report()
        self.check_azure_ad_health_report()
        # compare the information
        self.compare_health_report()

    def teardown(self):
        """Tear down the things created for running the test case"""
        self.browser.close()
        self.log.info("close the browser")
        self.log.info("Test case execution completed")        