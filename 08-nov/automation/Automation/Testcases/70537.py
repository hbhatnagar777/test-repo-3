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
import datetime
import time,os

from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.cvtestcase import CVTestCase
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices,ADTypes
from Web.AdminConsole.AD.ad import ADClientsPage,ADPage
from Web.AdminConsole.Hub.ad import MetallicAD
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep
from Application.AD.adpowershell_helper import AADPowerShell
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
import re

class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Active Directory New Tier Licensing
    Basic Validation for Active Directory licensing
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Active Directory_New_Tier_Licensing"
        self._create_agent_table_query = "CREATE TABLE Agentusercount(AgentName varchar(255), Usercount varchar(255));"
        self._create_tenant_user_query = "CREATE TABLE TenantUser(TenantUserName varchar(255));"
        self.browser = None
        self.AzureAD_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.adclientspage=None
        self.teams = None
        self.app_name = None
        self.service_catalogue = None
        self.dat_file = None
        self.utils = TestCaseUtils(self)
        self.sqlite_helper = None
        self.tenant = None
        self.app_name=None
        self.adpage=None
        self.azure_power_helper = None
        self.dat_file_folder_path = os.path.join(AUTOMATION_DIRECTORY, "Temp")
        self.dat_file_name = "ADLicenseUsage.dat"
        self.user_count=None


    @TestStep
    def create_client_for_agent(self, app_type):
        """Create clients for agent to verify License Usage"""
        self.log.info("------------------------------------"
                          "Creating Azure AD Application"
                          "------------------------------------")
        self.adclientspage = ADClientsPage(self.admin_console)
        self.adclientspage.aad_creation_metallic_react(clientname=self.app_name,tcinputs=self.tcinputs)
        job_helper = Jobs(self.admin_console)
        self.navigator.navigate_to_jobs()
        job_helper.access_active_jobs()
        jobid = job_helper.get_job_ids()[0]
        job_details = job_helper.job_completion(jobid)

    @TestStep
    def create_dat_file_and_tables(self):
        """Creates the dat file to store the records"""
        self.log.info("Creating DAT File to store the data")
        dat_file_path = os.path.join(self.dat_file_folder_path, self.dat_file_name)
        if os.path.exists(dat_file_path):
            os.remove(dat_file_path)
        self.dat_file = open(dat_file_path, "w")
        self.log.info("Created DAT File")
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name,
                                                 query=self._create_agent_table_query)
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name,
                                                 query=self._create_tenant_user_query)

    @TestStep
    def close_dat_file(self):
        """Closes the dat file after insertion of records"""
        self.dat_file.close()

    @TestStep
    def verify_ad_license_usages(self):
        """Verify license usages for AD"""
        self.adpage = ADPage(self.admin_console, self.commcell)
        license_usages = self.adpage.fetch_user()
        value, unit = license_usages["Purchased"].split()
        if value == "25":
            self.log.info("-----------------------------------------"
                          "Verified the purchased user count"
                          "-----------------------------------------")
        else:
            raise Exception("Purchased user count is not matching. Please check")

        select_query = "select Usercount from Agentusercount;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)


        if int(result[0][0])==(max(int(license_usages["Total Active Directory Users"]),
                              int(license_usages["Total Azure AD Users"]))):
            self.log.info("Licensed Users are Verified")
        else:
            raise Exception("Licensed Users are not matching")

        self.log.info("-----------------------------------------"
                      "Verified the licensed usage for all the users"
                      "-----------------------------------------")

    @TestStep
    def get_licensed_user(self):
        """Gets the Licensed User from Azure AD"""
        self.user_count = self.azure_power_helper.user_ps_operation(op_type="COUNT_USER",group_object_id="",
                                                                    user_id="")
        user_count = re.findall(r'\d+', str(self.user_count.formatted_output))
        return int(user_count[-1])

    @TestStep
    def store_licensed_user(self,licensed_user):
        """Stores Licensed User Count"""
        agent_capacity = {
            "AgentName": "Azure AD",
            "Usercount": licensed_user
        }
        insert_query = f"Insert into Agentusercount values('{agent_capacity['AgentName']}', '{agent_capacity['Usercount']}');"
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name,
                                                 query=insert_query, is_read_only=False)

    @TestStep
    def store_tenant_user(self):
        """Stores tenant user in the dat file"""
        insert_query = f"Insert into TenantUser values('{self.tenant_user_name}');"
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name, query=insert_query,
                                                 is_read_only=False)

    @TestStep
    def get_tenant_user(self):
        """Get the tenant user stored from DAT file"""

        select_query = "select TenantUserName from TenantUser;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)
        return result[0][0]

    @TestStep
    def delete_dat_file(self):
        """Delete the dat file"""
        os.remove(self.dat_file_folder_path+"\\"+self.dat_file_name)

    def open_browser(self):
        """Open browser"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name, self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.service = HubServices.ad

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('AzureADAuto%d%b%H%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@azuread{current_timestamp}.com')

    def setup(self):
        self.sqlite_helper = SQLiteHelper(self, use_proxy=False)
        self.tenant = False
        self.azure_power_helper = AADPowerShell(self.log, self.tcinputs['AdminUser'], self.tcinputs['AdminPassword'])
        self.app_name=datetime.datetime.now().strftime('App_%d%b%H%M')
        if not os.path.exists(os.path.join(self.dat_file_folder_path, self.dat_file_name)):
            self.create_dat_file_and_tables()
            self.create_tenant()
            self.store_tenant_user()
            self.open_browser()
            self.app_type = ADTypes.aad
            self.navigator = self.admin_console.navigator
            self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
            self.navigator.navigate_to_service_catalogue()
            self.service_catalogue.start_azureAD_trial()
            self.log.info("Creating an object for Azure AD helper")
            self.AzureAD_obj = MetallicAD(self.admin_console)
            self.tenant=True

        else:
            self.tenant_user_name = self.get_tenant_user()
            self.open_browser()
            self.navigator.navigate_to_usage()

    def run(self):
        """Main function for test case execution"""
        try:
            if self.tenant==True:
                self.create_client_for_agent(self.app_type)
                licensed_user= self.get_licensed_user()
                self.store_licensed_user(licensed_user)
                self.close_dat_file()

            else:
                self.verify_ad_license_usages()
                self.delete_dat_file()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.tenant==False:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.hub_utils.deactivate_tenant(self.tenant_name)
            self.hub_utils.delete_tenant(self.tenant_name)
        else:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)