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

import os
from AutomationUtils import constants
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Office365Pages import constants
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Office 365 All Versions and Latest Version Licensing for all agents
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_All_Versions_and_Latest_Version_Licensing_Case"
        self._create_agent_table_query = "CREATE TABLE AgentCapacityUsage(AgentName varchar(255), " \
                                         "ApplicationSize varchar(255), " \
                                         "InactiveApplicationSize varchar(255), TotalApplicationSize varchar(255)" \
                                         ");"
        self._create_licenses_usage_query = "CREATE TABLE LicensesUsage(Username varchar(255), " \
                                            "EmailAddress varchar(255)" \
                                            ", AgentName varchar(255), LicenseType varchar(255));"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.app_type = None
        self.mailboxes = None
        self.users = None
        self.sites = None
        self.teams_client = None
        self.onedrive_client = None
        self.exchange_client = None
        self.sharepoint_client = None
        self.company = None
        self.dat_file_path = None
        self.teams = None
        self.app_name = None
        self.exmbclient_object = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)
        self.sqlite_helper = None
        self.dat_file = None
        self.dat_file_folder_path = os.path.join(AUTOMATION_DIRECTORY, "Temp")
        self.dat_file_name = "Office365AllVersionLicenseUsage.dat"

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['TenantUsername'],
                                 self.tcinputs['TenantPassword'])
        self.sqlite_helper = SQLiteHelper(self, use_proxy=False)
        self.dat_file_path = os.path.join(self.dat_file_folder_path, self.dat_file_name)
        if not os.path.exists(os.path.join(self.dat_file_folder_path, self.dat_file_name)):
            self.create_dat_file_and_tables()
        self.navigator = self.admin_console.navigator
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)
        self.app_name = self.tcinputs['Name']
        self.teams_client = self.tcinputs['Teams Client']
        self.onedrive_client = self.tcinputs['Onedrive Client']
        self.sharepoint_client = self.tcinputs['Sharepoint Client']
        self.exchange_client = self.tcinputs['Exchange Client']
        self.log.info("Creating an object for office365 helper")

    @TestStep
    def get_application_size(self, app_type):
        """Gets the backup stats for the client
        Args:
            app_type (enum) : App type of the client
        """
        backup_size = self.office365_obj.fetch_active_inactive_capacity_for_agent(app_type)
        for key, size in backup_size.items():
            value, unit = size.split()
            if unit == "GB":
                backup_size[key] = float(value) / 1024
            elif unit == "MB":
                backup_size[key] = float(value) / (1024 * 1024)
            elif unit == "KB":
                backup_size[key] = float(value) / (1024 * 1024 * 1024)
            elif unit == "B":
                backup_size[key] = float(value) / (1024 * 1024 * 1024 * 1024)
        return backup_size

    @TestStep
    def store_application_sizes(self, application_size):
        """Stores application sizes respect to agent
        Application_size (dict) : Dictionary of the active, inactive and total application size"""
        agent_capacity = {
            "AgentName": self.app_type.value,
            "ApplicationSize": application_size['Active'],
            "InactiveApplicationSize": application_size['Inactive'],
            "TotalApplicationSize": application_size['Total']
        }
        insert_query = f"Insert into AgentCapacityUsage values('{agent_capacity['AgentName']}', " \
                       f"'{agent_capacity['ApplicationSize']}', " \
                       f"'{agent_capacity['InactiveApplicationSize']}', " \
                       f"'{agent_capacity['TotalApplicationSize']}');"
        self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                 file_name=self.dat_file_name,
                                                 query=insert_query, is_read_only=False)

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

    @TestStep
    def verify_office365_capacity_usages(self):
        """Verify the capacity usages for Office 365"""
        self.navigator.navigate_to_office365_licensing_usage()
        capacity_usage = self.office365_obj.fetch_capacity_usage_report()
        select_query = "SELECT round(sum(ApplicationSize),4) from AgentCapacityUsage;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)
        value = capacity_usage["Total Active Capacity Usage"].split()
        if round(float(value[0]),4) <= round((result[0][0]), 4):
            self.log.info("-----------------------------------------"
                          "Verified the active capacity usage value"
                          "-----------------------------------------")
        else:
            raise Exception("Total Active Capacity usage is not equal to all agents' active capacity usage")
        select_query = "SELECT round(sum(InactiveApplicationSize),4) from AgentCapacityUsage;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)
        value = capacity_usage["Total Inactive Capacity Usage"].split()
        if round(float(value[0]),4) <= round((result[0][0]), 4):
            self.log.info("-----------------------------------------"
                          "Verified the inactive capacity usage value"
                          "-----------------------------------------")
        else:
            raise Exception("Total inactive Capacity usage is not equal to all agents' inactive capacity usage")
        select_query = "SELECT round(sum(TotalApplicationSize),4) from AgentCapacityUsage;"
        result = self.sqlite_helper.execute_query_locally(source_folder=self.dat_file_folder_path,
                                                          file_name=self.dat_file_name,
                                                          query=select_query)

        value = capacity_usage["Total Capacity Usage"].split()
        if round(float(value[0]), 4) <= round((result[0][0]), 4):
            self.log.info("-----------------------------------------"
                          "Verified the total capacity usage value"
                          "-----------------------------------------")
        else:
            raise Exception("Total Capacity usage is not equal to all agents' total capacity usage")

    @TestStep
    def delete_dat_file(self):
        """Delete the dat file"""
        os.remove(self.dat_file_folder_path + "\\" + self.dat_file_name)

    def run(self):
        """Main function for test case execution"""
        self.app_type = O365AppTypes.teams
        self.navigator.navigate_to_office365()
        teams_backup_size = self.get_application_size(self.app_type)
        self.store_application_sizes(teams_backup_size)

        self.app_type = O365AppTypes.exchange
        self.navigator.navigate_to_office365()
        exchange_backup_size = self.get_application_size(self.app_type)
        self.store_application_sizes(exchange_backup_size)

        self.app_type = O365AppTypes.onedrive
        self.navigator.navigate_to_office365()
        onedrive_backup_size = self.get_application_size(self.app_type)
        self.store_application_sizes(onedrive_backup_size)

        self.app_type = O365AppTypes.sharepoint
        self.navigator.navigate_to_office365()
        sharepoint_backup_size = self.get_application_size(self.app_type)
        self.store_application_sizes(sharepoint_backup_size)

        self.verify_office365_capacity_usages()

        self.office365_obj.change_capacity_usage()

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Testcase completed successfully!")
        if self.status == constants.PASSED:
            self.delete_dat_file()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

