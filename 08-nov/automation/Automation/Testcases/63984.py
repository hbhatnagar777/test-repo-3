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
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Office365Pages import constants
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Office 365 New Tier Licensing
    Basic Validation for Office 365 tier licensing for all agents
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_New_Tier_Licensing"
        self._create_agent_table_query = "CREATE TABLE AgentCapacityUsage(AgentName varchar(255), ApplicationSize varchar(255));"
        self._create_licenses_usage_query = "CREATE TABLE LicensesUsage(Username varchar(255), EmailAddress varchar(255), AgentName varchar(255), LicenseType varchar(255));"
        self._create_tenant_user_query = "CREATE TABLE TenantUser(TenantUserName varchar(255);"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.mailboxes = None
        self.users = None
        self.sites = None
        self.teams = None
        self.app_name = None
        self.exmbclient_object = None
        self.service_catalogue = None
        self.dat_file = None
        self.agents_capacity = list()
        self.utils = TestCaseUtils(self)
        self.sqlite_helper = None
        self.dat_file_folder_path = os.path.join(AUTOMATION_DIRECTORY, "Temp")
        self.dat_file_name = "Office365LicenseUsage.dat"

    @TestStep
    def create_client_for_agent(self, app_type):
        """Create clients for agent to verify License Usage"""
        if app_type == O365AppTypes.exchange:
            self.log.info("------------------------------------"
                          "Creating Exchange Online Application"
                          "------------------------------------")
            self.office365_obj.app_type = O365AppTypes.exchange
            self.office365_obj.constants = constants.ExchangeOnline
            self.app_name = f'ExchangeOnline{self.tcinputs["Name"]}'
            self.mailboxes = self.tcinputs["ExchangeOnlineUsers"].split(',')
        elif app_type == O365AppTypes.onedrive:
            self.log.info("-----------------------------"
                          "Creating OneDrive Application"
                          "-----------------------------")
            self.office365_obj.app_type = O365AppTypes.onedrive
            self.office365_obj.constants = constants.OneDrive
            self.app_name = f'OneDrive{self.tcinputs["Name"]}'
            self.users = self.tcinputs["OneDriveUsers"].split(',')
        elif app_type == O365AppTypes.sharepoint:
            self.log.info("-------------------------------"
                          "Creating SharePoint Application"
                          "-------------------------------")
            self.office365_obj.app_type = O365AppTypes.sharepoint
            self.office365_obj.constants = constants.SharePointOnline
            self.app_name = f'SharePoint{self.tcinputs["Name"]}'
            self.sites = dict(zip(self.tcinputs['Sites'].split(","), self.tcinputs['SitesTitle'].split(",")))
        elif app_type == O365AppTypes.teams:
            self.log.info("--------------------------"
                          "Creating Teams Application"
                          "--------------------------")
            self.office365_obj.app_type = O365AppTypes.teams
            self.office365_obj.constants = constants.Teams
            self.app_name = f'Teams{self.tcinputs["Name"]}'
            self.teams = self.tcinputs["Teams"].split(',')
        self.office365_obj.create_office365_app(name=self.app_name,
                                                global_admin=self.tcinputs['GlobalAdmin'],
                                                password=self.tcinputs['Password'])
        self.app_name = self.office365_obj.get_app_name()

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
                                                 query=self._create_licenses_usage_query)
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name,
                                                 query=self._create_tenant_user_query)

    @TestStep
    def close_dat_file(self):
        """Closes the dat file after insertion of records"""
        self.dat_file.close()

    @TestStep
    def get_application_size(self):
        """Gets the backup stats for the client"""
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        backup_stats = self.office365_obj.fetch_backup_stats_for_client()
        backup_size = backup_stats["Backup size"]
        value, unit = backup_size.split()
        if unit == "GB":
            value = float(value)/1024
        elif unit == "MB":
            value = float(value)/(1024*1024)
        elif unit == "KB":
            value = float(value)/(1024*1024*1024)
        value = f'{value:.6f}' # round the number upto 6 decimal places
        return value

    @TestStep
    def store_application_sizes(self, application_size):
        """Stores application sizes respect to agent"""
        agent_capacity = {
            "AgentName": self.office365_obj.app_type.value,
            "ApplicationSize": application_size
        }
        insert_query = f"Insert into AgentCapacityUsage values('{agent_capacity['AgentName']}', '{agent_capacity['ApplicationSize']}');"
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name,
                                                 query=insert_query, is_read_only=False)

    @TestStep
    def store_licensed_users(self, licensed_users):
        """Stores licensed users respect to agent"""
        for user in licensed_users:
            insert_query = f"Insert into LicensesUsage values('{user['User Name']}'," \
                           f"'{user['Email Address']}'," \
                           f"'{user['Agent Name']}'," \
                           f"'{user['License Type']}');"
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
    def verify_office365_capacity_usages(self):
        """Verify the capacity usages for office 365"""
        self.navigator.navigate_to_office365_licensing_usage()
        capacity_usage = self.office365_obj.fetch_capacity_usage_report()
        self.log.info("Verifying the capacity usage report parameters")
        calculated_capacity_usage = str(round(25*50/1024, 6))+" TB"
        if capacity_usage["Purchased"] == calculated_capacity_usage:
            self.log.info("-----------------------------------------"
                          "Verified the purchased storage value"
                          "-----------------------------------------")
        else:
            raise Exception("Purchased and calculated storage values are not matching")
        select_query = "SELECT round(sum(ApplicationSize),5) from AgentCapacityUsage;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)
        value, unit = capacity_usage["Total Capacity Usage"].split()
        if float(value) <= result[0][0]:
            self.log.info("-----------------------------------------"
                          "Verified the total capacity usage value"
                          "-----------------------------------------")
        else:
            raise Exception("Total Capacity usage is not equal to all agent's capacity usage")
        select_query = "Select * from AgentCapacityUsage;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)
        if float(result[0][1]) >= float(capacity_usage["Monthly Usage"][O365AppTypes.exchange.value].split()[0])\
                and float(result[1][1]) >= float(capacity_usage["Monthly Usage"][O365AppTypes.onedrive.value].split()[0])\
                and float(result[2][1]) >= float(capacity_usage["Monthly Usage"][O365AppTypes.sharepoint.value].split()[0])\
                and float(result[3][1]) >= float(capacity_usage["Monthly Usage"][O365AppTypes.teams.value].split()[0]):
            self.log.info("-----------------------------------------"
                          "Verified the agents total capacity value"
                          "-----------------------------------------")
        else:
            raise Exception("Total Capacity value is not verified. Please check")

    @TestStep
    def verify_office365_license_usages(self):
        """Verify license usages for office 365"""
        self.navigator.navigate_to_office365_licensing_usage()
        license_usages = self.office365_obj.fetch_license_usage_report()
        value, unit = license_usages["Purchased"].split()
        if value == "25":
            self.log.info("-----------------------------------------"
                          "Verified the purchased user count"
                          "-----------------------------------------")
        else:
            raise Exception("Purchased user count is not matching. Please check")
        select_query = "select EmailAddress, AgentName from LicensesUsage where LicenseType=='Licensed';"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)
        for user in result:
            email = user[0]
            agent = user[1]
            if license_usages[email][agent]:
                self.log.info("Verified {} is a licensed user for agent {}.".format(email,agent))
            else:
                raise Exception("User {} is licensed according to client but not included in Office 365 Capacity Usage Table.".format(email))
        self.log.info("-----------------------------------------"
                      "Verified the licensed usage for all the users"
                      "-----------------------------------------")

    @TestStep
    def delete_dat_file(self):
        """Delete the dat file"""
        pass

    def open_browser(self):
        """Open browser"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name, self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.office365

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('Office365-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@exchange{current_timestamp}.com')

    def setup(self):
        self.sqlite_helper = SQLiteHelper(self, use_proxy=False)
        if not os.path.exists(os.path.join(self.dat_file_folder_path, self.dat_file_name)):
            self.create_dat_file_and_tables()
            self.create_tenant()
            self.store_tenant_user()
            self.open_browser()
            self.app_type = O365AppTypes.exchange
            self.hub_dashboard = Dashboard(self.admin_console, self.service, self.app_type)
            self.hub_dashboard.click_get_started()
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_continue()
            self.hub_dashboard.click_new_configuration()
            self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
            self.service_catalogue.start_office365_trial()
            self.navigator = self.admin_console.navigator
            self.log.info("Creating an object for office365 helper")
            self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)
            self.office365_obj.o365_plan = "{}-{}".format(self.tenant_name, "enterprise-metallic-o365-plan")
        else:
            self.tenant_user_name = self.get_tenant_user()
            self.open_browser()
            self.hub_dashboard = Dashboard(self.admin_console, self.service)
            self.hub_dashboard.go_to_admin_console()

    def run(self):
        """Main function for test case execution"""
        try:
            if not os.path.exists(os.path.join(self.dat_file_folder_path, self.dat_file_name)):
                self.create_client_for_agent(O365AppTypes.exchange)
                self.office365_obj.add_user(self.mailboxes)
                self.office365_obj.run_backup()
                exchange_application_size = self.get_application_size()
                self.store_application_sizes(exchange_application_size)
                exchange_licensed_users = self.office365_obj.fetch_licensed_users_for_client()
                self.store_licensed_users(exchange_licensed_users)
                self.navigator.navigate_to_office365()
                self.create_client_for_agent(O365AppTypes.onedrive)
                self.office365_obj.add_user(self.users)
                self.office365_obj.run_backup()
                onedrive_application_size = self.get_application_size()
                self.store_application_sizes(onedrive_application_size)
                onedrive_licensed_users = self.office365_obj.fetch_licensed_users_for_client()
                self.store_licensed_users(onedrive_licensed_users)
                self.navigator.navigate_to_office365()
                self.create_client_for_agent(O365AppTypes.sharepoint)
                self.office365_obj.add_user(self.sites)
                self.office365_obj.run_backup()
                sharepoint_application_size = self.get_application_size()
                self.store_application_sizes(sharepoint_application_size)
                self.navigator.navigate_to_office365()
                self.create_client_for_agent(O365AppTypes.teams)
                self.office365_obj.add_user(self.teams)
                self.office365_obj.run_backup()
                teams_application_size = self.get_application_size()
                self.store_application_sizes(teams_application_size)
                self.close_dat_file()
            else:
                self.verify_office365_capacity_usages()
                self.verify_office365_license_usages()
                self.delete_dat_file()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.hub_utils.deactivate_tenant(self.tenant_name)
        self.hub_utils.delete_tenant(self.tenant_name)

