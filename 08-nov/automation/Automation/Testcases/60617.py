# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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

    delete()                    --  Deletes Salesforce app from Commcell

    validate_compare_data()     --  Method to validate compare data

    get_compare_data()          --  Method to fetch data from Compare page

    create_custom_field()       --  Method to create custom field on custom object

    delete_custom_object        --  Method to delete custom object

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "60617": {
            "ClientName": "",
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
                "cache_path": "/var/cache/commvault",
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
from Web.AdminConsole.Salesforce.constants import CompareChangeType
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Salesforce.SalesforceCompare import SalesforceCompare
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType
from enum import Enum

DATABASE = 'tc_60617'
APP_NAME = f"TC_60617_{datetime.now().strftime('%d_%B_%H_%M')}"
CUSTOM_FIELD = "Field1"


class ValidationLevel(Enum):
    """Constants for compare validation level"""
    ONLY_NUMBERS = 1
    ONLY_RECORDS = -1
    BOTH = 0


class TestCase(CVTestCase):
    """Class for executing metadata compare test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Metadata Compare"
        self.browser = None
        self.admin_console = None
        self.expected_data = [{"File name": f"{APP_NAME}__c.object"}]
        self.sf_object = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
        self.sf_compare = None

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_postgresql_database(DATABASE)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.admin_console.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceOrganizations(self.admin_console, self.commcell)
        self.sf_app_details = SalesforceOverview(self.admin_console, self.commcell)
        self.sf_compare = SalesforceCompare(self.admin_console)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_postgresql_database(DATABASE)

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
            return self.sf_app_details.backup()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete(self):
        """Deletes Salesforce app from Commcell"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(APP_NAME)
            self.sf_app_details.delete()
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_compare_data(self, expected_records, compare_records, compare_num, title,
                              validation_level=ValidationLevel.BOTH):
        """
        Method to validate metadata compare

        Args:
            expected_records (list[dict]): List of expected records at compare page
            compare_records (list[dict]): List of records fetched from compare page
            compare_num (int): Number of records mentioned on metadata summary
            title (CompareChangeType): Column title on compare
            validation_level (ValidationLevel): Validation level - records only, compare numbers only, both

        Returns:
            None:

        Raises:
            CVTestStepFailure: If records don't match
        """
        self.log.info(f"Validating {title.value} metadata")

        if validation_level in (ValidationLevel.ONLY_NUMBERS, ValidationLevel.BOTH):
            if not compare_num == len(expected_records):
                raise Exception(f"{title.value} metadata do not match. "
                                f"{compare_num} {title.value} metadata from compare "
                                f"do not match actual number {len(expected_records)}")

        if validation_level in (ValidationLevel.ONLY_RECORDS, ValidationLevel.BOTH):
            for record in expected_records:
                if not any(all(value == comp_rec[key] for key, value in record.items()) for
                           comp_rec in compare_records):
                    raise Exception(
                        f"Validation for {title.value} metadata on {self.sf_object.fullName} failed."
                        f" Metadata {record} not found.")

        self.log.info(f"{title.value} metadata validation successful")

    @test_step
    def get_compare_data(self, job1, job2):
        """
            Method to fetch data from Compare page

            Args:
                job1 (str): Job id for first job in compare
                job2 (str): Job id for second job in compare

            Returns:
                Object of SFCompare

                """
        try:
            self.sf_app_details.access_compare_tab()
            compare_data = self.sf_compare.metadata_compare(job1, job2, ["objects"], is_job_id=True)[0]
            self.sf_compare.access_overview_tab()
            return compare_data
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_custom_field(self):
        """Method to create custom field on custom object"""
        try:
            self.sf_helper.create_custom_field(self.sf_object, CUSTOM_FIELD)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete_custom_object(self):
        """Method to delete custom object"""
        try:
            self.sf_helper.delete_custom_object(self.sf_object.fullName)
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """Main function for test case execution"""
        try:
            # Create new Salesforce App in Command Center
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()
            # Enabling Metadata backups
            self.sf_app_details.content = [
                self.admin_console.props['label.allSfMetadata'],
                self.admin_console.props['label.allSfFiles']
            ]
            # Run full backup
            job1 = self.backup_full()[0]
            # Create custom object and records
            self.sf_object, _ = self.sf_helper.create_test_object(APP_NAME, self.sf_helper.fields)
            # Run Incremental backup
            job2 = self.backup_incremental()[0]
            # Retrieve & compare data for first and second job
            compare_data = self.get_compare_data(job1, job2)
            self.validate_compare_data(self.expected_data, compare_data.added.records, compare_data.added.nums,
                                       CompareChangeType.ADDED, ValidationLevel.BOTH)
            # Create custom field
            self.create_custom_field()
            # Run Incremental backup
            job3 = self.backup_incremental()[0]
            # Retrieve & compare data for first and second job
            compare_data = self.get_compare_data(job2, job3)
            self.validate_compare_data(self.expected_data, compare_data.modified.records, compare_data.modified.nums,
                                       CompareChangeType.MODIFIED, ValidationLevel.BOTH)
            # Delete custom object
            self.delete_custom_object()
            # Run Incremental backup
            job4 = self.backup_incremental()[0]
            # Retrieve & compare data for first and second job
            compare_data = self.get_compare_data(job3, job4)
            self.validate_compare_data(self.expected_data, compare_data.deleted.records, compare_data.deleted.nums,
                                       CompareChangeType.DELETED, ValidationLevel.BOTH)

            # Deleting salesforce app
            if "ClientName" not in self.tcinputs:
                self.delete()

        except CVTestStepFailure as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
