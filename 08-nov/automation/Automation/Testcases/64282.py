"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    tear_down()                 --  tear down method for testcase

    create_app()                --  Method to create a new Salesforce app in commcell

    backup_full()               --  Method to run full backup and wait for job completion

    validate_dashboard_data()   --  Method to compared and validate data between dashboard and report

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs.

    "testCases": {
        "64282": {
            "ClientName": "",
            "DestinationClient": "",
            "salesforce_options": {
                "login_url": "https://login.salesforce.com",
                "salesforce_user_name": "",
                "salesforce_user_password": "",
                "salesforce_user_token": "",
                "consumer_id": "",
                "consumer_secret": "",
                "sandbox": false
            },
            "infrastructure_options": {
                "access_node": "",
                "cache_path": "/tmp",
                "db_type": "POSTGRESQL",
                "db_host_name": "",
                "db_user_name": "postgres",
                "db_password": ""
            },
            "profile": "Admin",
            "plan": "",
            "resource_pool": "",
            "storage_policy": "",
            "sf_object": "Contact",
            "fields": ["FirstName", "LastName", "Email", "Phone"]
        }
    }
"""
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.dashboard import SalesforceDashboard
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Reports.report import Report
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType
from AutomationUtils.machine import Machine
from time import sleep
import os
import glob
DATABASE = 'tc_64282'
APP_NAME = f"TC_64282_{datetime.now().strftime('%d_%B_%H_%M')}"

""" Check data. Then create new org. Then run backup. Then check data again."""


class TestCase(CVTestCase):
    """Class for validating data from Salesforce Dashboard """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Dashboard"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.report = None
        self.manager_report = None
        self.machine = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
        self.download_dir = None
        self.dashboard = None
        self.dict_list = None
        self.file_name = None

    def setup(self):
        """Method to set up test variables"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.download_dir = self.browser.get_downloads_dir()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_database(DATABASE)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceOrganizations(self.admin_console, self.commcell)
        self.sf_app_details = SalesforceOverview(self.admin_console, self.commcell)
        self.dashboard = SalesforceDashboard(self.admin_console, self.commcell)
        self.report = Report(self.admin_console)
        self.manager_report = ManageReport(self.admin_console)
        self.machine = Machine()
        self.dict_list = [None] * 5

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE, db_type=DbType.POSTGRESQL)
            self.sf_apps.add_org(
                org_name=APP_NAME,
                plan=self.sf_helper.plan,
                oauth=False,
                **self.sf_helper.salesforce_options.__dict__,
                **infra_options.__dict__
            )
        except Exception as exp:
            raise CVTestStepFailure from exp

    def __retrieve_data_from_csv(self):
        """
            Function used to retrieve data from downloaded report
        """
        self.report.save_as_csv()
        sleep(10)
        path = self.download_dir+"\\*.csv"
        self.file_name = max(glob.glob(path), key=os.path.getctime)
        return self.machine.read_csv_file(self.file_name)

    @test_step
    def backup_full(self):
        """Method to run full backup and wait for job completion"""
        try:
            self.sf_app_details.backup(backup_type="full")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_dashboard_data(self, dict_list):
        """
                Function used to compare data between dashboard and report by validating the difference of the
                statistics before and after creating an org
                Args:
                    dict_list (list) : List of dictionaries and lists carrying data from Dashboard and Report before and
                    after backup of an org respectively
        """
        try:
            flag = True
            id_list = [self.admin_console.props["label.dashboard.backupHealth.entities.backedUp"],
                       self.admin_console.props["label.dashboard.backupHealth.entities.notBackedUp"],
                       self.admin_console.props["label.dashboard.backupHealth.entities.neverBackedUp"]]

            for i in range(0, 3):
                if (dict_list[2][id_list[i]] - dict_list[0][id_list[i]] !=
                        int(dict_list[3][2*i+4]['Salesforce Backup Health']) -
                        int(dict_list[1][2*i+4]['Salesforce Backup Health'])):
                    flag = False
                    break

            if not flag:
                raise Exception("Data from the Dashboard doesn't matches with the Report")

        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """
                Main function for test case execution
        """
        try:

            # storing dashboard data in dictionary before backup
            self.dict_list[0] = self.dashboard.get_Backup_health()

            self.navigator.navigate_to_reports()

            self.manager_report.access_report("Salesforce Backup Health")

            csv_data = self.__retrieve_data_from_csv()

            # storing report data in list before backup
            self.dict_list[1] = list(csv_data)

            self.navigator.navigate_to_salesforce()

            self.create_app()

            self.backup_full()

            self.navigator.navigate_to_salesforce()

            # storing dashboard data in dictionary after backup
            self.dict_list[2] = self.dashboard.get_Backup_health()

            self.navigator.navigate_to_reports()

            self.manager_report.access_report("Salesforce Backup Health")

            csv_data = self.__retrieve_data_from_csv()

            # storing report data in list after backup
            self.dict_list[3] = list(csv_data)

            self.validate_dashboard_data(self.dict_list)

            # Delete Salesforce App
            if "ClientName" not in self.tcinputs:
                self.delete()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def delete(self):
        """Deletes Salesforce app and Connected App credentials from Commcell"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp
