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

    restore()                   --  Method to restore data from database to salesforce and wait for job completion

    validate_records_on_record_level_page() -- Validates records on record level restore page

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" parameter to run this testcase on an existing
    Salesforce pseudoclient. If not provided, a new pseudoclient will be created.

    "testCases": {
        "62173": {
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
                "db_type": "SQLSERVER"
            },
            "sqlserver_options": {
                "db_host_name": "",
                "db_instance": "MSSQLSERVER",
                "db_port": 1433,
                "db_user_name": "",
                "db_password": ""
            }
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
from Application.CloudApps.SalesforceUtils.constants import DbType
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Web.AdminConsole.Salesforce.constants import RecordLevelVersion
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper

DATABASE = 'tc_62173'
APP_NAME = f"TC_62173_{datetime.now().strftime('%d_%B_%H_%M')}"


class TestCase(CVTestCase):
    """Class for executing testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Record Level Restore (SQL Server)"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.sf_restore = None
        self.app_name = APP_NAME

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.app_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_sqlserver_database(DATABASE)
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
        self.sf_restore = RSalesforceRestore(self.admin_console)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.data]
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_sqlserver_database(DATABASE)

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(
                db_name=DATABASE,
                db_type=DbType.SQLSERVER,
                **self.sf_helper.sqlserver_options.__dict__
            )
            self.sf_apps.add_org(
                org_name=self.app_name,
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
            return self.sf_app_details.backup(backup_type="full")[-1]
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for job completion"""
        try:
            return self.sf_app_details.backup()[-1]
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def restore(self, backup_job_id=None):
        """Method to run record level restore to salesforce and wait for job completion"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            if backup_job_id:
                backup_job = self.commcell.job_controller.get(backup_job_id)
                self.sf_app_details.select_time_for_restore(datetime.fromtimestamp(backup_job.start_timestamp))
            else:
                self.sf_app_details.click_on_restore()
            job_id = self.sf_restore.record_level_restore(
                sf_object=self.sf_helper.sf_object,
                record_ids=[record['Id'] for record in self.data]
            )
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_records_on_record_level_page(self, latest_records, all_records, deleted_records):
        """
        Validates records on restore page

        Args:
            latest_records (list[dict]): list of records that should show up in latest records
            all_records (list[dict]: list of records that should show up in all records
            deleted_records (list[dict]): list of records that should show up in deleted records

        Returns:
            None:

        Raises:
            CVTestStepFailure: if records don't match
        """
        try:
            for saved_data, version in zip(
                    [latest_records, all_records, deleted_records],
                    [RecordLevelVersion.LATEST, RecordLevelVersion.ALL, RecordLevelVersion.DELETED]
            ):
                self.admin_console.navigator.navigate_to_salesforce()
                self.sf_apps.access_organization(self.app_name)
                self.sf_app_details.click_on_restore()
                restore_data = self.sf_restore.get_rows_from_record_level_restore(
                    sf_object=self.sf_helper.sf_object,
                    record_ids=[record['Id'] for record in self.data],
                    version=version,
                    fields=list(self.data[0].keys())
                )
                if len(restore_data) != len(saved_data):
                    raise Exception(
                        f"Validation failed for {version}. Number of records should be {len(saved_data)} but is"
                        f" {len(restore_data)}"
                    )
                for saved_record in saved_data:
                    if not (any(
                            all(value == restore_record[key] for key, value in saved_record.items())
                            for restore_record in restore_data
                    )):
                        raise Exception(
                            f"Validation failed for {version}. Record {saved_record} not found."
                        )
                self.log.info(f"Record level validation successful for {version}")
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def delete(self):
        """Deletes Salesforce app from Commcell"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            self.sf_app_details.delete()
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
            # Create new record in Salesforce object
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, self.sf_helper.fields, 5)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, self.data)
            # Run full backup
            self.backup_full()
            # Modify record in Salesforce object
            modified_data = self.sf_helper.modify_records(self.sf_helper.sf_object, self.data)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, modified_data)
            # Run incremental backup
            job_id = self.backup_incremental()
            # Validate records on record level restore page
            self.validate_records_on_record_level_page(modified_data, [*self.data, *modified_data], [])
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, modified_data, hard_delete=False)
            # Run incremental backup
            self.backup_incremental()
            # Validate records on record level restore page
            self.validate_records_on_record_level_page([], [], modified_data)
            # Run restore to Salesforce and validate
            self.restore(job_id)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object, modified_data)
            if "ClientName" not in self.tcinputs:
                self.delete()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
