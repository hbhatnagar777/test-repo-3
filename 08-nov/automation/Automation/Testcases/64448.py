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

    delete()                    --  Deletes Salesforce app from Commcell

    cleanup_old_downloads()     --  Method to clean up old download files

    read_file()                 --  Method to clean up old download files

    download()                  --  Method to download from file/object/metadata browse

    validate_file_data()        --  validates downloaded file data with expected

    validate_object_data()      --  validates downloaded object data with salesforce

    validate_metadata_object()  --  validates downloaded metadata file is not empty

    run()                       --  run function of this test case

Input Example:

    There are no required inputs to this testcase. The values set in config.json can be overridden by providing any of
    the following variables in testcase inputs. Pass the "ClientName" and "DestinationClientName" parameters to run this
    testcase on existing Salesforce pseudoclients. If not provided, new pseudoclients will be created.

    "testCases": {
        "64448": {
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
import os
import time
from base64 import b64encode
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import PASSED
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Salesforce.restore import RSalesforceRestore
from Web.AdminConsole.Salesforce.organizations import SalesforceOrganizations
from Web.AdminConsole.Salesforce.overview import SalesforceOverview
from Application.CloudApps.SalesforceUtils.salesforce_helper import SalesforceHelper
from Application.CloudApps.SalesforceUtils.constants import DbType,CONTENT_DOCUMENT
from Application.CloudApps.SalesforceUtils.cv_connector import convert_csv_string_to_data_dict

DATABASE = 'tc_64448'
APP_NAME = f"TC_64448_{datetime.now().strftime('%d_%B_%H_%M')}"
CONTENT_VERSION_PATH = '/Files/ContentVersion'
OBJECT_PATH = '/Objects'
METADATA_OBJECT_BROWSE_PATH = '/Metadata/unpackaged/objects'
METADATA_OBJECT_PATH = 'objects'


class TestCase(CVTestCase):
    """Class for executing basic acceptance test for Salesforce on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Salesforce: Download"
        self.browser = None
        self.admin_console = None
        self.data = None
        self.sf_helper = None
        self.sf_apps = None
        self.sf_app_details = None
        self.content_document = None
        self.content_version = None
        self.download_dir = None
        self.machine = Machine()
        self.org_name = APP_NAME
        self.validate = {
            CONTENT_VERSION_PATH: self.validate_file_data,
            OBJECT_PATH: self.validate_object_data,
            METADATA_OBJECT_PATH: self.validate_metadata_object
        }

    def setup(self):
        """Method to setup test variables"""
        self.sf_helper = SalesforceHelper(self.tcinputs, self.commcell)
        self.sf_helper.cleanup(__file__)
        self.cleanup_old_downloads()
        if "ClientName" in self.tcinputs:
            self.org_name = self.sf_helper.ClientName
        else:
            self.sf_helper.create_new_postgresql_database(DATABASE)

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
        self.admin_console.navigator.navigate_to_salesforce()
        self.sf_apps = SalesforceOrganizations(self.admin_console, self.commcell)
        self.sf_app_details = SalesforceOverview(self.admin_console, self.commcell)
        self.machine.clear_folder_content(self.download_dir)

    def tear_down(self):
        """Tear down method for testcase"""
        if self.status == PASSED:
            self.data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.data]
            self.sf_helper.delete_object_data(self.sf_helper.sf_object, self.data)
            delete_data = [{key: val for key, val in row.items() if key != 'Id'} for row in self.content_document]
            self.sf_helper.delete_object_data(CONTENT_DOCUMENT, delete_data)
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
            self.sf_app_details.backup(backup_type="full")
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def backup_incremental(self):
        """Method to run incremental backup and wait for job completion"""
        try:
            self.sf_app_details.backup()
        except Exception as exp:
            raise CVTestStepFailure from exp

    def cleanup_old_downloads(self):
        """Method to clean up old download files"""
        self.machine.clear_folder_content(self.download_dir)

    def read_file(self, file_name, wait=600):
        """
        read a file from download dir

        Args:
            file_name: file to be read from download dir
            wait (default 300): wait in seconds for the file to download
        """
        t = 0

        while t < wait:
            if self.machine.check_file_exists(os.path.join(self.download_dir, file_name)):
                return self.machine.read_file(os.path.join(self.download_dir, file_name))

            elif self.machine.check_file_exists(os.path.join(self.download_dir, f"{file_name}.zip")):
                self.machine.unzip_zip_file(os.path.join(self.download_dir, f"{file_name}.zip"), self.download_dir)
                download_job = self.sf_helper.get_latest_job(self.org_name)
                return self.machine.read_file(
                    os.path.join(os.path.join(self.download_dir, download_job), f"{file_name}.csv"))
            time.sleep(10)
            t += 10
        raise Exception(f'File {file_name} did not download in {wait} seconds')

    @test_step
    def download(self, path, file, metadata=False):
        """Download from file/object/metadata browse"""
        self.log.info(f"Downloading {file}{' Metadata' if metadata else ''} from {path}")
        try:
            self.admin_console.navigator.navigate_to_salesforce()
            self.sf_apps.click_on_restore(self.org_name)
            if metadata:
                file = f'{file}.object'
                RSalesforceRestore(self.admin_console).metadata_restore(
                    path=path,
                    file_folders=[file],
                    download=True
                )
            else:
                RSalesforceRestore(self.admin_console).object_level_restore(
                    path=path,
                    file_folders=[file],
                    download=True
                )
            return self.read_file(file)
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

    def validate_file_data(self, file_read, expected_doc):
        """validates downloaded file data with expected"""
        expected_version = self.content_version[expected_doc['LatestPublishedVersionId']]
        expected_data = expected_version['VersionData']
        if b64encode(file_read.strip().encode()).decode() != expected_data:
            raise Exception(f"Local version of {expected_doc['Title']} does not match version on Salesforce")
        self._log.info(f"{expected_doc['Title']} validated successfully")

    def validate_object_data(self, file_read):
        """validates downloaded object data with salesforce"""
        downloaded_data = convert_csv_string_to_data_dict(file_read)
        try:
            self.sf_helper.validate_object_data(self.data, downloaded_data)
        except Exception as exp:
            self._log.error("Validation failed")
            self._log.error(f"Downloaded records were {downloaded_data}")
            self._log.error(f"Records created on Salesforce are {self.data}")
            raise exp
        self._log.info(f"validated downloaded {self.sf_helper.sf_object} CSV successfully")

    def validate_metadata_object(self, file_read):
        """validates downloaded metadata data with salesforce"""
        zipped_data = self.sf_helper.download_metadata_zip(package={'CustomObject': [self.sf_helper.sf_object]})
        contact_object_xml = zipped_data.read(f'{METADATA_OBJECT_PATH}/{self.sf_helper.sf_object}.object').decode()
        if file_read.replace("\r", "").replace("\n", "") != contact_object_xml.replace("\r", "").replace("\n", ""):
            raise Exception(
                f'Validation Failed for Metadata \n Local file {file_read}\n Salesforce file {contact_object_xml}')
        self._log.info(f"validated Downloaded {self.sf_helper.sf_object} Metadata File successfully")

    def run(self):
        """Main function for test case execution"""
        try:
            # Create new Salesforce App in Command Center
            if "ClientName" in self.tcinputs:
                self.sf_apps.access_organization(self.sf_helper.ClientName)
            else:
                self.create_app()
            self.sf_app_details.content = ['All files', 'All metadata']
            # Create new records and files in Salesforce object
            self.data = self.sf_helper.create_records(self.sf_helper.sf_object, fields=self.sf_helper.fields)
            self.content_version, self.content_document = self.sf_helper.create_files(rec_count=5)
            # Run full backup
            self.backup_full()
            # Modify records in Salesforce object
            self.data = self.sf_helper.create_incremental_data(self.sf_helper.sf_object, self.data)
            # Run incremental backup
            self.backup_incremental()
            # Download ContentVersion File
            file = self.download(
                CONTENT_VERSION_PATH,
                self.content_version[self.content_document[0]['LatestPublishedVersionId']]['PathOnClient'])
            # Validating Downloaded ContentVersion File
            self.validate[CONTENT_VERSION_PATH](file, self.content_document[0])
            # Download Object CSV File
            file = self.download(
                OBJECT_PATH,
                self.sf_helper.sf_object)
            # Validating Downloaded Object CSV
            self.validate[OBJECT_PATH](file)
            # Download object Metadata File
            file = self.download(
                METADATA_OBJECT_BROWSE_PATH,
                self.sf_helper.sf_object,
                metadata=True)
            # Validating Downloaded Metadata File
            self.validate[METADATA_OBJECT_PATH](file)

            # Delete Salesforce App
            if "ClientName" not in self.tcinputs:
                self.delete()
                pass
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
