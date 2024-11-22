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

    restore()                   --  Method to restore data from database to salesforce and wait for job completion

    delete()                    --  Deletes Salesforce app from Commcell

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" parameter to run this testcase on an existing
    Salesforce pseudoclient. If not provided, a new pseudoclient will be created.

    "testCases": {
        "70530": {
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
                "db_type": "POSTGRESQL"
            },
            "postgresql_options": {
                "db_host_name": "",
                "db_user_name": "postgres",
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
import copy
import time
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from Web.AdminConsole.Salesforce.compliance_manager import ComplianceManager
from Web.AdminConsole.Salesforce.constants import GDPRRequestType
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper

DATABASE = 'tc_70530'
APP_NAME = f"TC_70530_{datetime.now().strftime('%d_%B_%H_%M')}"


def update_records(data, records):
    """Method to update GDPR MOD records from data"""
    data_cpy = []
    for li in data:
        d2 = copy.deepcopy(li)
        data_cpy.append(d2)

    for data_rec in data_cpy:
        for record in records:
            if data_rec["Id"] == record["Id"]:
                data_rec.update(record)
    return data_cpy


class TestCase(CVTestCase):
    """Class for executing testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.third_full_data = None
        self.name = "Salesforce: GDPR modify test"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.sf_CM = None
        self.gdpr_mod_records = None
        self.gdpr_mod_records_2 = None
        self.app_name = APP_NAME

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        if "ClientName" in self.tcinputs:
            self.app_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_database(DATABASE)
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
        self.sf_CM = ComplianceManager(self.admin_console, self.commcell)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.third_full_data]
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            if "ClientName" not in self.tcinputs:
                self.sf_helper.delete_database(DATABASE)

    @test_step
    def create_app(self):
        """Method to create a new Salesforce app in commcell"""
        try:
            infra_options = self.sf_helper.updated_infrastructure_options(db_name=DATABASE)
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
            job = self.sf_app_details.backup(backup_type="full")[-1]
            return job
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for job completion"""
        try:
            job = self.sf_app_details.backup()[-1]
            return job
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def create_gdpr_mod_request(self, object_name, records):
        """Method to create GDPR MOD request"""
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            self.sf_app_details.access_compliance_manager()
            self.sf_CM.create_request(f"{APP_NAME}_mod", GDPRRequestType.MODIFICATION,
                                      [{"name": object_name,
                                        "options": [{"id": record['Id'],
                                                     "fieldValues": [
                                                         {"name": field, "value": value} for
                                                         field, value in
                                                         record.items() if field != "Id"]} for
                                                    record in records]}])
            cm_job = self.sf_helper.get_latest_job(job_filter='198')
            self.log.info(f"Waiting for CM job {cm_job} to complete")
            if self.commcell.job_controller.get(cm_job).wait_for_completion():
                self.log.info(
                    f"CM job {cm_job} completed with status {self.commcell.job_controller.get(cm_job).status}")
            self.sf_CM.access_overview_tab()

        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def restore(self, backup_job_id):
        """Method to restore data from database to salesforce and wait for job completion"""
        try:
            backup_job = self.commcell.job_controller.get(backup_job_id)
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.access_organization(self.app_name)
            self.sf_app_details.select_time_for_restore(datetime.fromtimestamp(backup_job.start_timestamp))
            job_id = RSalesforceRestore(self.admin_console).object_level_restore(
                path='/Objects/',
                file_folders=[self.sf_helper.sf_object]
            )
            job = self.commcell.job_controller.get(job_id)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run job {job_id} with error: {job.delay_reason}")
            self.log.info(f"Successfully finished job {job_id}")
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
            # Create new records in Salesforce object
            first_full_data = self.sf_helper.create_records(self.sf_helper.sf_object,
                                                            fields=self.sf_helper.fields)
            # Run full backup
            first_full = self.backup_full()
            # Modify records in Salesforce object
            second_full_data = self.sf_helper.create_incremental_data(self.sf_helper.sf_object,
                                                                      first_full_data.copy())
            # Run second full backup
            second_full = self.backup_full()
            # Create incremental data change
            second_full_incr_1_data = self.sf_helper.create_incremental_data(self.sf_helper.sf_object,
                                                                             second_full_data.copy())
            # Modify few records that will also be modified with GDPR
            self.gdpr_mod_records = second_full_incr_1_data[:2]
            self.gdpr_mod_records = self.sf_helper.modify_records(self.sf_helper.sf_object, self.gdpr_mod_records)
            # Run incremental backup
            second_full_incr_2 = self.backup_incremental()
            # Create GDPR MOD req for Modified records
            self.create_gdpr_mod_request(self.sf_helper.sf_object, self.gdpr_mod_records)
            # Again modify GDPR data on Salesforce
            self.gdpr_mod_records_2 = self.sf_helper.modify_records(self.sf_helper.sf_object, self.gdpr_mod_records)
            # Run Incremental backup
            second_full_incr_3 = self.backup_incremental()
            self.third_full_data = update_records(second_full_incr_1_data, self.gdpr_mod_records_2)
            # Run Full backup
            third_full = self.backup_full()
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.third_full_data)
            # Run restore to Salesforce from previous cycle and validate
            self.restore(first_full)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object,
                                                              update_records(first_full_data,
                                                                             self.gdpr_mod_records))
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object)
            # Run restore to Salesforce from previous cycle and validate
            self.restore(second_full_incr_3)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object,
                                                              update_records(second_full_incr_1_data,
                                                                             self.gdpr_mod_records_2))
            # Delete records in Salesforce object
            self.sf_helper.delete_object_data(self.sf_helper.sf_object)
            # Run restore to Salesforce from latest cycle and validate
            self.restore(third_full)
            self.sf_helper.validate_object_data_in_salesforce(self.sf_helper.sf_object,
                                                              self.third_full_data)

            # Delete Salesforce App
            if "ClientName" not in self.tcinputs:
                self.delete()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
