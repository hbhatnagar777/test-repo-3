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

    validate_records()          --  Validate records for each change - Added, Deleted, Modified, Total_first,
                                    Total_second

    validate_compare_data()     --  Method to validate compare data

    get_compare_data()          --  Method to fetch data from Compare page

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "60616": {
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
from Web.AdminConsole.Salesforce.SalesforceCompare import SalesforceCompare, SFCompare
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType
from enum import Enum

DATABASE = 'tc_60616'
APP_NAME = f"TC_60616_{datetime.now().strftime('%d_%B_%H_%M')}"


class ValidationLevel(Enum):
    """Constants for compare validation level"""
    ONLY_NUMBERS = 1
    ONLY_RECORDS = -1
    BOTH = 0


def convert_to_id_map(data, id_required=True):
    id_map = {}

    for record in data:
        id_field = record.get("Id") or record.get("id")
        id_map[id_field] = {key.lower(): value for key, value in record.items()
                            if id_required or not key.lower() == "id"}

    return id_map


def find_difference(data1, data2):
    id_map_data1 = convert_to_id_map(data1)
    id_map_data2 = convert_to_id_map(data2)

    added_records = [id_map_data2[id] for id in id_map_data2.keys() - id_map_data1.keys()]
    deleted_records = [id_map_data1[id] for id in id_map_data1.keys() - id_map_data2.keys()]

    common_ids = id_map_data1.keys() & id_map_data2.keys()
    old_records = []

    for id in common_ids:
        if id_map_data1[id] != id_map_data2[id]:
            old_record = id_map_data1[id].copy()
            old_record["id"] = f"{id} - Old"
            old_records.append(old_record)

    modified_records = [id_map_data2[id] for id in common_ids if id_map_data1[id] != id_map_data2[id]]

    return added_records, deleted_records, old_records, modified_records


def update_records(data1, data2, data3) -> list[dict]:
    """
    Update the data for deleted records

    """
    data_map1 = convert_to_id_map(data1.copy())
    data_map2 = convert_to_id_map(data2)
    data_map3 = convert_to_id_map(data3)

    for id in [id_del for id_del in data_map1.keys() if id_del not in data_map3.keys() and id_del in data_map2.keys()]:
        data_map1[id] = data_map2[id]
    return [rec for rec in data_map1.values()]


class TestCase(CVTestCase):
    """Class for executing object compare test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Object Compare"
        self.browser = None
        self.admin_console = None
        self.data1 = None
        self.data2 = None
        self.data3 = None
        self.sf_object = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.org_name = APP_NAME
        self.sf_compare = None
        self.added_records = None
        self.deleted_records = None
        self.old_records = None
        self.modified_records = None

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
            self.data3 = [{key: val for key, val in row.items() if key != 'Id'} for row in self.data3]
            self.sf_helper.delete_custom_object(self.sf_object.fullName, self.data3)
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

    def validate_records(self, expected_records, compare_records, compare_num, title, old_records=None,
                         validation_level=ValidationLevel.BOTH):
        """
        Validate records for each change - Added, Deleted, Modified, Total_first, Total_second

        Args:
            expected_records (list[dict]): List of expected records at compare page
            compare_records (list[dict]): List of records fetched from compare page
            compare_num (int): Number of records mentioned on object summary
            title (CompareChangeType): Column title on compare
            old_records (list[dict]): List of records before modifying
            validation_level (ValidationLevel): Validation level - records only, compare numbers only, both

        Returns:
            None:

        Raises:
            CVTestStepFailure: If records don't match
        """
        self.log.info(f"Validating {title.value} records")

        if validation_level in (ValidationLevel.ONLY_NUMBERS, ValidationLevel.BOTH):
            if not compare_num == len(expected_records):
                raise Exception(f"{title.value} Records do not match. "
                                f"{compare_num} {title.value} Records from compare "
                                f"do not match actual number {len(expected_records)}")

        if ((validation_level in (ValidationLevel.ONLY_RECORDS, ValidationLevel.BOTH)) and
                (title != CompareChangeType.TOTAL_FIRST and title != CompareChangeType.TOTAL_SECOND)):
            if not title == CompareChangeType.MODIFIED:
                for record in expected_records:
                    if not any(all(value == comp_rec[key.lower()] for key, value in record.items()) for
                               comp_rec in compare_records):
                        raise Exception(
                            f"Validation for {title.value} records on {self.sf_object.fullName} failed."
                            f" Record {record} not found.")
            else:
                old_rec_map = convert_to_id_map(old_records, False)
                compare_org_rec = {key: rec for key, rec in convert_to_id_map(compare_records, False).items() if
                                   ("- Old" in key)}
                compare_mod_rec = {key: rec for key, rec in convert_to_id_map(compare_records, False).items() if
                                   not ("- Old" in key)}
                modified_expected_map = convert_to_id_map(expected_records, False)

                for mod_key, record in modified_expected_map.items():
                    if not (all(v == compare_mod_rec[mod_key][k] for k, v in record.items()) and
                            all(v == compare_org_rec.get(mod_key, compare_org_rec.get(f"{mod_key} - Old"))[k] for
                                k, v in old_rec_map.get(mod_key, old_rec_map.get(f"{mod_key} - Old")).items())):
                        raise Exception(
                            f"Validation for {title.value} records on {self.sf_object.fullName} failed."
                            f" Record {record} not found.")

        self.log.info(f"{title.value} records validation successful")

    @test_step
    def validate_compare_data(self, compare_data, data1, data2, validation_level=ValidationLevel.BOTH):
        """
        Method to validate compare data

        Args:
            compare_data (SFCompare): Object to hold compare data
            data1 (list[dict]): List of records in Salesforce backed up in first job
            data2 (list[dict]): List of records in Salesforce backed up in second job
            validation_level (ValidationLevel): Validation level - records only, compare numbers only, both

        Returns:
            None:
        """
        try:
            self.added_records, self.deleted_records, self.old_records, self.modified_records = find_difference(data1,
                                                                                                                data2)
            self.log.info(f"Validating compare for {self.sf_object.fullName} object")

            for itr, expected_records, title in [
                    (compare_data.added, self.added_records, CompareChangeType.ADDED),
                    (compare_data.deleted, self.deleted_records, CompareChangeType.DELETED),
                    (compare_data.modified, self.modified_records, CompareChangeType.MODIFIED),
                    (compare_data.total_first, data1, CompareChangeType.TOTAL_FIRST),
                    (compare_data.total_sec, data2, CompareChangeType.TOTAL_SECOND)]:

                self.validate_records(expected_records, itr.records, itr.nums, title, self.old_records,
                                      validation_level)

            self.log.info(f"Validating successful for {self.sf_object.fullName} object")
        except Exception as exp:
            raise CVTestStepFailure from exp

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
            job1 = self.commcell.job_controller.get(job1)
            job1_timestamp = datetime.fromtimestamp(job1.end_timestamp)
            job2 = self.commcell.job_controller.get(job2)
            job2_timestamp = datetime.fromtimestamp(job2.end_timestamp)
            self.sf_app_details.access_compare_tab()
            compare_data = self.sf_compare.object_compare(job1_timestamp, job2_timestamp, [self.sf_object.fullName],
                                                          fields=[field.lower() for field in self.data1[0].keys()])[0]
            self.sf_compare.access_overview_tab()
            return compare_data
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
            # Create custom object and records
            self.sf_object, self.data1 = self.sf_helper.create_test_object(APP_NAME, self.sf_helper.fields)

            # Run full backup
            job1 = self.backup_full()[0]
            # Modify records in Salesforce object
            self.data2 = self.sf_helper.create_incremental_data(self.sf_object.fullName, data=self.data1.copy(),
                                                                rec_count=10)
            # Run incremental backup
            job2 = self.backup_incremental()[0]
            # Retrieve & compare data for first and second job
            compare_data = self.get_compare_data(job1, job2)
            self.validate_compare_data(compare_data, self.data1, self.data2)
            # Modify records in Salesforce object
            self.data3 = self.sf_helper.create_incremental_data(self.sf_object.fullName, data=self.data2.copy(),
                                                                add=8, modify=4, delete=8)
            # Run incremental backup
            job3 = self.backup_incremental()[0]
            # Retrieve & compare data for second and third job
            compare_data = self.get_compare_data(job2, job3)
            self.validate_compare_data(compare_data, self.data2, self.data3)

            compare_data = self.get_compare_data(job1, job3)
            self.validate_compare_data(compare_data, update_records(self.data1, self.data2, self.data3), self.data3,
                                       ValidationLevel.ONLY_RECORDS)

            # Deleting salesforce app
            if "ClientName" not in self.tcinputs:
                self.delete()

        except CVTestStepFailure as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
