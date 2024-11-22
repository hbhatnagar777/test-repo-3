# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Verify APSS Associate Storage Policy workflow """

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Reports.storeutils import StoreUtils
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.API.webconsole import Store
from Web.API import customreports
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Forms.forms import Forms


_CONFIG = get_config()


class TestCase(CVTestCase):
    """ Verify APSS Associate Storage Policy workflow """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.util = StoreUtils(self)
        self.workflow_name = 'APSS Associate Storage Policy'
        self.name = "Reports Workflow : Verify APSS Associate Storage Policy workflow"
        self.store_api = None
        self.table = None
        self.browser = None
        self.form = None
        self.client = None
        self.agent = None
        self.webconsole = None
        self.backupset = None
        self.utils = TestCaseUtils(self)
        self.custom_report_name = 'APSS - Subclients with No Storage Policy Associations'

    def login_to_store(self):
        """Login to store"""
        self.store_api = Store(
            machine=self.commcell.webconsole_hostname,
            wc_uname=self.inputJSONnode['commcell']["commcellUsername"],
            wc_pass=self.inputJSONnode['commcell']["commcellPassword"],
            store_uname=_CONFIG.email.username,
            store_pass=_CONFIG.email.password)

    def init_webconsole(self):
        """Initialize webconsole"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                              self.inputJSONnode['commcell']["commcellPassword"])
        navigator = Navigator(self.webconsole)
        self.webconsole.goto_reports()
        navigator.goto_worldwide_report(self.custom_report_name)
        _viewer = viewer.CustomReportViewer(self.webconsole)
        self.table = viewer.DataTable("Subclients with no Storage Policy associations")
        _viewer.associate_component(self.table)

    def create_backupset(self):
        """Create backupset"""
        # backup set will be created with the name: backupset_54384
        _backupset_name = "auto_backupset_" + str(self.id)
        self.log.info("Creating backupset [%s]", _backupset_name)
        default_client_obj = self.commcell.clients.get(self.commcell.commserv_name)
        self._agent = default_client_obj.agents.get("file system")
        if self._agent.backupsets.has_backupset(_backupset_name):
            self._agent.backupsets.delete(_backupset_name)
        self.backupset = self._agent.backupsets.add(_backupset_name)
        _subclient = self.backupset.subclients.get('default')
        _subclient.disable_backup()
        self.log.info("[%s]Backupset is created!", _backupset_name)

    def install_workflow(self):
        """Installs the workflow"""
        if self.commcell.workflows.has_workflow(self.workflow_name):
            self.log.info("Deleting workflow [%s] using API", self.workflow_name)
            self.commcell.workflows.delete_workflow(self.workflow_name)
        self.store_api.install_workflow(self.workflow_name)

    def install_report(self):
        """Install the required custom report"""
        custom_report_api = customreports.CustomReportsAPI(self.commcell.webconsole_hostname,
                                                           username=self.inputJSONnode['commcell']
                                                           ["commcellUsername"],
                                                           password=self.inputJSONnode['commcell']
                                                           ["commcellPassword"],
                                                           )
        reports = custom_report_api.get_all_installed_reports()
        if self.custom_report_name in reports:
            self.log.info("[%s] already installed in webconsole. "
                          "No need to install again.", self.custom_report_name)
        else:
            self.log.info(f"Installing [%s] custom report", self.custom_report_name)
            self.store_api.install_report(self.custom_report_name)

    @test_step
    def associate_storage_policy(self):
        """Associate storage policy"""
        self.table.set_filter(column_name='Backupset', filter_string=self.backupset.name)
        column_obj = viewer.DataTable.Column("Backupset")
        self.table.associate_column(column_obj)
        column_obj.open_hyperlink_on_cell("Associate Storage Policy")
        storage_policy = list(self.commcell.storage_policies.all_storage_policies.keys())[0]
        if 'commservedr' in storage_policy:  # commservdr sp will not be listed in form
            storage_policy = list(self.commcell.storage_policies.all_storage_policies.keys())[1]
        schedule_policy = list(self.commcell.schedule_policies.all_schedule_policies.keys())[0]
        _form = Forms(self.webconsole)
        _form.submit()
        self.webconsole.wait_till_load_complete()
        _form.select_dropdown('Storage Policy:', storage_policy)
        _form.submit()
        _form.select_dropdown('Schedule Policy:', schedule_policy)
        _form.submit()
        self.webconsole.wait_till_load_complete()
        _form.submit()  # click ok for information message
        self.webconsole.wait_till_load_complete()

    @test_step
    def verify_sp_associated(self):
        """Verify storage policy associated"""
        self.webconsole.browser.driver.refresh()
        self.webconsole.wait_till_load_complete()
        self.table.set_filter(column_name='Backupset', filter_string=self.backupset.name)
        data = self.table.get_table_data()
        for key, values in data.items():
            if values:
                raise CVTestStepFailure("Storage policy may not be associated for [%s] backupset, "
                                        "Please verify" % self.backupset.name)

    def cleanup_configuration(self):
        """Delete backup set """
        default_client_obj = self.commcell.clients.get(self.commcell.commserv_name)
        agent = default_client_obj.agents.get("file system")
        agent.backupsets.delete(self.backupset.name)

    def setup(self):
        """Test case Pre Configuration"""
        self.login_to_store()
        self.install_report()
        self.install_workflow()
        self.create_backupset()
        self.init_webconsole()

    def run(self):
        try:
            self.associate_storage_policy()
            self.verify_sp_associated()
            self.cleanup_configuration()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
