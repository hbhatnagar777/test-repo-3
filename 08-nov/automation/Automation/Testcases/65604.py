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

    backup_incremental()        --  Method to run incremental backup and wait for job completion

    create_alert()              --  Method to create an anomaly alert based on the given parameters

    validate_alert()            --  Method used to validate the triggered alert

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs.

    "testCases": {
        "65604": {
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
from Web.AdminConsole.Salesforce.configuration import SalesforceConfiguration
from Web.AdminConsole.Salesforce.monitoring import SalesforceAnomalyAlerts
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType
from time import sleep

DATABASE = 'tc_65604'
APP_NAME = f"TC_65604_{datetime.now().strftime('%d_%B_%H_%M')}"

""" Create alert. Run an incremental job. Then validate the triggered alert"""


class TestCase(CVTestCase):
    """Class for triggering and validating alerts on a Salesforce org """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Anomaly Alerts"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.list_of_parameters = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
        self.monitor = None
        self.sf_config = None

    def setup(self):
        """Method to set up test variables"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceOrganizations(self.admin_console, self.commcell)
        self.sf_app_details = SalesforceOverview(self.admin_console, self.commcell)
        self.monitor = SalesforceAnomalyAlerts(self.admin_console, self.commcell)
        self.sf_config = SalesforceConfiguration(self.admin_console)
        self.list_of_parameters = [["Contact"], ["Added"], 'Number', ["Greater than"], "10"]

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

    @test_step
    def backup_full(self):
        """Method to run full backup and wait for job completion"""
        try:
            return self.sf_app_details.backup(backup_type="full")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for job completion"""
        try:
            return self.monitor.backup(self.org_name)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_alert(self):
        """
                Function used to create an anomaly alert for an organization based on the parameters provided
        """
        try:
            self.sf_app_details.access_configuration_tab()
            self.sf_config.check_alert_status()
            self.sf_config.access_monitoring_tab()
            objects = self.list_of_parameters[0]
            criterias = self.list_of_parameters[1]
            parameter_type = self.list_of_parameters[2]
            condition = self.list_of_parameters[3]
            value = self.list_of_parameters[4]
            self.monitor.create_alert(objects, criterias, parameter_type, condition, value)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_alert(self, job_id):
        """
                Function used to validate the triggered alert by comparing the alert's configurations with the
                parameters provided
        """
        try:

            self.monitor.access_history_page()
            list_of_values = self.monitor.get_alert_info(job_id)

            for item1, item2 in zip(self.list_of_parameters, list_of_values):
                if item1 != item2:
                    raise Exception(f"Verification of Alert has failed."
                                    f"\nActual Parameters:{self.list_of_parameters}"
                                    f"\nRetrieved Parameters:{list_of_values}")

        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """
                Main function for test case execution
        """
        try:

            # Create new Salesforce App in Command Center
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()

            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)

            self.backup_full()

            self.create_alert()

            sleep(20)

            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields,
                                                      rec_count=20)

            job_id = self.backup_incremental()

            self.validate_alert(job_id[0])

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
            self.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp
