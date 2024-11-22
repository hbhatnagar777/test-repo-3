# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()              --  Initializes test case class object

    init_cloud()            --  Initializes Cloud Store URL

    get_sub_category()      --  Returns the sub-category available in workflow category

    download_workflow()     --  Downloads the workflow

    access_file()           --  Access the downloaded workflow xml

    close_cloud()           --  Ends the Cloud Store URL

    init_local_web()        --  Initializes the local webserver URL

    init_db()               --  Initializes the Database for updating details

    install_workflow()      --  Installs the workflow through local webserver

    run()                   --  Main function for testcase execution

"""
# Test Suite Imports
import os
from datetime import datetime
from xml.etree import ElementTree as ET

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.mailer import Mailer
from Reports.Custom.utils import CustomReportUtils
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.API.webconsole import Store
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for valiating this testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW -  [Software Store] Validation of Download, Install all " \
                    "workflows available in Software Store"
        self.browser = None
        self.webconsole = None
        self.store = None
        self.mssql = None
        self.store_dict = {}
        self.category_wf_mapping = {}
        self.download_location = None
        self.failure_count = None
        self.html = None
        self.testcaseutils = None
        self.retry = None
        self.error_list = {}
        self.tcinputs = {
            'SQLUserName': None,
            'SQLPassword': None,
            'DownloadLocation': None,
            'EmailId': None
        }

    def check_report_exists(self):
        """Check whether Status Report Exists"""
        utils = CustomReportUtils(self)
        report = utils.cre_api.get_report_definition_by_name('Cloud Workflow Status', suppress=True)
        if not report:
            self.log.info("Report with name [Cloud Workflow Status] is not available")
            raise Exception("Report [Cloud Workflow Status] is unavailable. Please deploy the "
                            "workflow 'Cloud Workflow Status' "
                            "from /Automation/Server/Workflow/Reports/CloudWorkflowStatus.xml")

    def init_cloud(self):
        """Initialising Cloud Store URL"""
        try:
            self.testcaseutils = TestCaseUtils(self)
            username = _STORE_CONFIG.Cloud.username
            password = _STORE_CONFIG.Cloud.password
            cloud_url = _STORE_CONFIG.Reports.PUBLIC_CLOUD
            self.download_location = self.tcinputs['DownloadLocation']
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update "\
                                "the username and password details under "\
                                "<Automation_Path>/CoreUtils/Templates/template-config.json")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.download_location)
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                cloud_url,
                enable_ssl=True
            )
            self.webconsole.login(
                username, password)
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(direct=False)

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def get_sub_category(self):
        """Returns the subcategory"""
        sub_ctg = self.store.get_sub_category(category='Workflows')
        self.log.info("Subcategories available %s", sub_ctg)
        return sub_ctg

    @test_step
    def get_wf_of_subcategory(self, sub_category):
        """Returns the workflows available in subcategory"""
        storeapi = Store(port=443, protocol="https",
                         machine=self.inputJSONnode['commcell']['webconsoleHostname'],
                         wc_uname=self.inputJSONnode['commcell']['commcellUsername'],
                         wc_pass=self.inputJSONnode['commcell']['commcellPassword'],
                         store_uname=_STORE_CONFIG.Cloud.username,
                         store_pass=_STORE_CONFIG.Cloud.password)
        return storeapi.get_packages(category_name='Workflows', sub_category=sub_category)

    @test_step
    def download_workflow(self, workflow):
        """Downloads the store workflow"""
        self._process_download_path()
        self.store.download_workflow(workflow, escape_package_name=True)

    def _process_download_path(self, return_file_name=False):
        """Deletes the existing file in download location"""
        for root, dirs, files in os.walk(self.download_location):
            self.log.info("Processing file %s on directory [%s]", files, dirs)
            if return_file_name:
                return files[0]
            for file in files:
                self.log.info("Deleting file [%s]", os.path.join(root, file))
                os.remove(os.path.join(root, file))

    @test_step
    def access_file(self, workflow):
        """Accesss the downloaded workflow file content"""
        file_name = self._process_download_path(return_file_name=True)
        file_path = "{0}\\{1}".format(self.download_location, file_name)
        self.log.info("Accessing File Path %s", file_path)
        wf_name = self._read_download_file(file_path)
        self.store_dict[workflow] = wf_name
        self.log.info("Updated Store dict %s", self.store_dict)

    def _read_download_file(self, file_path):
        if '.zip' in file_path:
            self.log.info("Zip File Path %s", file_path)
            from zipfile import ZipFile
            archive = ZipFile(file_path).namelist()
            self.log.info("Files in the zipped file are [%s]", archive)
            for arch in archive:
                if arch.endswith('.xml'):
                    with ZipFile(file_path, 'r') as zip_file:
                        content = zip_file.read(arch)
        else:
            with open(file_path, 'rb') as file:
                content = file.read()
        root = ET.fromstring(content)
        if 'name' in root.attrib:
            return root.attrib['name']
        element = root.find('./workflow')
        return element.attrib['name']

    @test_step
    def close_cloud(self):
        """Ends the browser session of Cloud URL"""
        WebConsole.logout_silently(self.webconsole)
        Browser.close_silently(self.browser)

    @test_step
    def init_local_web(self):
        """Initializes the browser session of Local webserver URL"""
        try:
            self.testcaseutils = TestCaseUtils(self)
            username = _STORE_CONFIG.Cloud.username
            password = _STORE_CONFIG.Cloud.password
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(
                username=username, password=password)

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def init_db(self):
        """Initialises the DB for updating details"""
        db_server = "{0}{1}".format(self.commcell.commserv_hostname, "\\Commvault")
        self.log.info("Initiating the DB Server")
        self.mssql = MSSQL(db_server, self.tcinputs['SQLUserName'], self.tcinputs['SQLPassword'], 'WFEngine')
        query = "if not exists (" \
                "select 1 from sysobjects where name='{0}') BEGIN " \
                "CREATE TABLE CloudWorkflowStatus " \
                "(WorkflowName nvarchar(250), StoreWorkflowName nvarchar(250)," \
                "Category nvarchar(250), status nvarchar(50)," \
                "FailureMessage nvarchar(500), modifiedTime datetime" \
                ")END".format('CloudWorkflowStatus')
        self.mssql.execute(query)

    def _delete_workflow(self, workflow_list):
        """Delete the list of workflows"""
        for workflow in workflow_list:
            self.log.info("Delete Workflow %s", workflow)
            self.commcell.workflows.delete_workflow(workflow)
            self.log.info("Deleted workflow [%s] successfully", workflow)

    @test_step
    def install_workflow(self):
        """Installs the workflow using local webserver"""
        parent_wf_mapping = _STORE_CONFIG.CloudWorkflow.EmbeddedWorkflow.ParentWorkflow
        self.log.info("Dependent Mapping [%s]", parent_wf_mapping)
        counter = 0
        for sub_ctg, store_wf_list in self.category_wf_mapping.items():
            self.log.info("Subcategory considered for processing %s", sub_ctg)
            for store_wf in store_wf_list:
                if counter >= 10:
                    self.close_cloud()
                    self.init_local_web()
                    counter = 0
                try:
                    del_wf_list = []
                    workflow = self.store_dict.get(store_wf)
                    self.log.info("Processing for Workflow with store name [%s] and actual name [%s]", store_wf, workflow)
                    if workflow in parent_wf_mapping:
                        dependent_wf = _STORE_CONFIG.CloudWorkflow.EmbeddedWorkflow.ChildWorkflow
                        actual_wf_name = self.store_dict.get(dependent_wf)
                        self.log.info("Processing for Dependent Workflow with store name [%s] and actual name[%s] ",
                                      dependent_wf, actual_wf_name)
                        del_wf_list.append(actual_wf_name)
                        dependent_pkg_status = self.store.get_package_status(
                            package_name=dependent_wf, category='Workflows', refresh=True, escape_package_name=True)
                        self.log.info("Package Status of dependent workflow is %s", dependent_pkg_status)
                        try:
                            self._process_install_request(dependent_pkg_status, actual_wf_name, dependent_wf,
                                                          sub_ctg, dependent=True)
                        except Exception as excp:
                            self._update_db(workflow, store_wf, sub_ctg, 'Failed', str(excp),
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            self.failure_count += 1
                            temp_html = '<tr><td>{0}</td><td>{1}</td></tr>'.format(store_wf, format(str(excp)))
                            self.html = '{0}{1}'.format(self.html, temp_html)
                            continue
                    del_wf_list.append(workflow)
                    wf_pkg_status = self.store.get_package_status(
                        package_name=store_wf, category='Workflows', refresh=True, escape_package_name=True
                    )
                    self.log.info("Package Status of workflow is %s", wf_pkg_status)
                    self._process_install_request(wf_pkg_status, workflow, store_wf, sub_ctg)
                    counter += 1
                    self.log.info("Initiating Delete workflow request for Store Workflow [%s] with name as %s",
                                  store_wf, workflow)
                    self.log.info("Workflow(s) to delete %s", del_wf_list)
                    self._delete_workflow(del_wf_list)
                    self.log.info("Workflow deleted successfully")
                except Exception as exp:
                    self.log.error("Error in installing workflow [%s]", store_wf)
                    self.log.error("The error is [%s]", str(exp))
                    if sub_ctg in self.error_list:
                        if store_wf not in self.error_list.get(sub_ctg):
                            self.error_list.setdefault(sub_ctg, []).append(store_wf)
                            if self.retry:
                                self.failure_count += 1
                                temp_html = '<tr><td>{0}</td><td>{1}</td></tr>'.format(store_wf, "Selenium issue")
                                self.html = '{0}{1}'.format(self.html, temp_html)
                                workflow = self.store_dict.get(store_wf)
                                self._update_db(workflow, store_wf, sub_ctg, "Failed", "Selenium issue",
                                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    else:
                        self.error_list.setdefault(sub_ctg, []).append(store_wf)
                        if self.retry:
                            self.failure_count += 1
                            temp_html = '<tr><td>{0}</td><td>{1}</td></tr>'.format(store_wf, "Selenium issue")
                            self.html = '{0}{1}'.format(self.html, temp_html)
                            workflow = self.store_dict.get(store_wf)
                            self._update_db(workflow, store_wf, sub_ctg, "Failed", "Selenium issue",
                                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    self.log.info("Updated error list %s", self.error_list)
                    self.log.info("Refreshing page")
                    self.browser.driver.refresh()

    def _process_install_request(self, pkg_status, workflow, store_wf, sub_ctg, dependent=False):
        if pkg_status == 'Install':
            self._install(workflow, store_wf, sub_ctg, dependent=dependent)
            self.log.info("Workflow [%s] is installed successfully", workflow)
        elif pkg_status == 'Update':
            self._update(workflow, store_wf, sub_ctg, dependent=dependent)
            self.log.info("Workflow [%s] is updated successfully", workflow)
        elif not dependent:
            self.log.info("Workflow [%s] is already installed. Status is Open", workflow)
            self._update_db(workflow, store_wf, sub_ctg, 'Success', '', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def _install(self, workflow, store_workflow, category, dependent=False):
        try:
            self.log.info("Initiating Install workflow for Store Workflow [%s] with name as %s",
                          store_workflow, workflow)
            self.store.install_workflow(store_workflow, escape_package_name=True)
            if not dependent:
                self._update_db(workflow, store_workflow, category, 'Success', '',
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        except Exception as excp:
            if dependent:
                raise Exception("Failed to install the dependent workflow [{0}] with excp {1}".
                                format(workflow, str(excp)))
            notifications = self.webconsole.get_all_unread_notifications(
                expected_count=2
            )
            self.log.info("Install Workflow [%s] failed with notification as %s",
                          store_workflow, str(notifications[0]))
            self._update_db(workflow, store_workflow, category, 'Failed', str(notifications[0]),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.failure_count += 1
            temp_html = '<tr><td>{0}</td><td>{1}</td></tr>'.format(store_workflow, str(notifications[0]))
            self.html = '{0}{1}'.format(self.html, temp_html)

    def _update_db(self, workflow, store_workflow, category, status, status_msg, modified_time):
        """Updates the status of workflow install/update in db"""
        update_query = "if exists(select 1 from CloudWorkflowStatus where " \
                       "workflowName='{0}') " \
                       "update CloudWorkflowStatus set StoreWorkflowName='{1}', Category='{2}', status='{3}', " \
                       "FailureMessage='{4}', " \
                       "modifiedTime='{5}' where workflowName='{0}'" \
                       "else " \
                       "insert CloudWorkflowStatus values ('{0}','{1}','{2}','{3}','{4}', '{5}')".format(
                           workflow, store_workflow, category, status, status_msg, modified_time)
        self.mssql.execute(update_query)
        self.log.info("Successfully updated the DB details")

    def _update(self, workflow, store_workflow, category, dependent=False):
        """Clicks the Update on the workflow"""
        try:
            self.log.info("Initiating Update Workflow for Store Workflow [%s] with name as %s",
                          store_workflow, workflow)
            self.store.update_workflow(store_workflow, escape_package_name=True)
            if not dependent:
                self._update_db(workflow, store_workflow, category, 'Success', '',
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        except Exception as excp:
            if dependent:
                raise Exception("Failed to install the dependent workflow [{0}] with excp {1}".
                                format(workflow, str(excp)))
            notifications = self.webconsole.get_all_unread_notifications(
                expected_count=2
            )
            self.log.info("Update Workflow [%s] failed with notiication as %s", store_workflow, str(notifications[0]))
            self._update_db(workflow, store_workflow, category, 'Failed', str(notifications[0]),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.failure_count += 1
            temp_html = '<tr><td>{0}</td><td>{1}</td></tr>'.format(store_workflow, format(str(notifications[0])))
            self.html = '{0}{1}'.format(self.html, temp_html)

    @test_step
    def failed_download(self, wf_list):
        """Method for retrying failed workflows"""
        self.init_cloud()
        self.error_list = {}
        self.store_dict = {}
        self.category_wf_mapping = wf_list
        for subcategory in self.category_wf_mapping:
            for workflow in self.category_wf_mapping[subcategory]:
                try:
                    self.log.info("Processing for workflow [%s] ", workflow)
                    self.download_workflow(workflow)
                    self.log.info("Download workflow successfully")
                    self.access_file(workflow)
                    self.log.info("Access file is completed")
                except Exception as exp:
                    self.log.error("Error in downloading the workflow [%s]", workflow)
                    self.log.error("The error is [%s]", str(exp))
                    self.error_list.setdefault(subcategory, []).append(workflow)
                    self.failure_count += 1
                    temp_html = '<tr><td>{0}</td><td>{1}</td></tr>'.format(workflow, "Selenium issue")
                    self.html = '{0}{1}'.format(self.html, temp_html)
                    self._update_db(workflow, workflow, subcategory, "Failed", "Selenium issue",
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    self.log.info("Updated download error list %s", self.error_list)
                    self.log.info("Refreshing page")
                    self.browser.driver.refresh()
        self.close_cloud()
        self.init_local_web()
        self.init_db()
        self.install_workflow()
        self.log.info("Error list after retry %s", self.error_list)

    @test_step
    def send_mail(self):
        """Sends the status mail with report link"""
        report_link = '{0}{1}'.format(
            self.webconsole.base_url, 'reportsplus/reportViewer.jsp?reportId=CloudWorkflowAutomationStatus')
        self.log.info("Status Report Link %s", report_link)
        header_html = '<html><body><div id="wrap"><br><p>Report Link <a href="{0}">click here</a></p>'.\
            format(report_link)
        if self.failure_count > 0:
            email_subject = '[FAILED] - Cloud Workflow Automation'
            table_html = '<h2 style="text-align: justify;">Summary</h2><table ' \
                         'style="border-collapse: collapse !important;border-spacing: 5px;' \
                         'table-layout: fixed;width: 75%"><tr style="font-size: 20px;' \
                         'background-color: #e0ebeb;text-align: left;">' \
                         '<th style="padding: 5px;">Workflow</th><th style="padding: 5px;">Failure Reason</th></tr>'
            email_content = '{0}{1}{2}{3}'.format(header_html, table_html, self.html, '</table></div></body></html>')
        else:
            email_subject = '[PASSED] - Cloud Workflow Automation'
            email_content = '{0}{1}'.format(header_html, '</div></body></html>')
        mailer = Mailer({"receivers": self.tcinputs['EmailId']}, self.commcell)
        mailer.mail(email_subject, email_content)

    def run(self):
        """Main function for testcase execution"""
        try:
            self.html = ''
            self.retry = False
            self.check_report_exists()
            self.init_cloud()
            sub_categories = self.get_sub_category()
            for sub_category in sub_categories:
                wf_list = self.get_wf_of_subcategory(sub_category=sub_category)
                self.log.info("Workflows available in sub_category [%s] are %s", sub_category, wf_list)
                self.category_wf_mapping[sub_category] = wf_list
                self.log.info("SubCategory and workflow mapping %s", self.category_wf_mapping)
                for workflow in wf_list:
                    try:
                        self.log.info("Processing for workflow [%s] in category %s", workflow, sub_category)
                        self.download_workflow(workflow)
                        self.log.info("Download workflow successfully")
                        self.access_file(workflow)
                        self.log.info("Access file is completed")
                    except Exception as exp:
                        self.log.error("Error in downloading the workflow [%s]", workflow)
                        self.log.error("The error is [%s]", str(exp))
                        self.error_list.setdefault(sub_category, []).append(workflow)
                        self.log.info("Updated error list %s", self.error_list)
                        self.log.info("Refreshing page")
                        self.browser.driver.refresh()
                self.store.clear_search_field()
            self.close_cloud()
            self.init_local_web()
            self.init_db()
            self.failure_count = 0
            self.install_workflow()
            self.close_cloud()
            self.log.info("Error list %s", self.error_list)
            self.log.info("Retrying failed ones")
            self.retry = True
            self.failed_download(self.error_list)
            self.log.info(self.html)
            self.send_mail()

        except Exception as err:
            self.testcaseutils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
