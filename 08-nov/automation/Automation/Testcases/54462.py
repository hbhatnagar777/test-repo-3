# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" verify worldwide dashboard osos ppt export """
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "verify worldwide dashboard osos ppt export"
        self.browser = None
        self.webconsole = None
        self.export = None
        self.admin_user_name = None
        self.admin_password = None
        self.non_admin_user_name = "non_admin_user_54462"
        self.non_admin_password = "######"
        self.utils = TestCaseUtils(self)

    def create_non_admin_user(self):
        """create non admin user """
        if self.commcell.users.has_user(self.non_admin_user_name):
            self.log.info("non admin user[%s] already exists", self.non_admin_user_name)
            return
        role_name = "Report_Management_54462"

        #  add role if it does not exists
        if not self.commcell.roles.has_role(role_name):
            self.commcell.roles.add(rolename=role_name, permission_list=["Report Management"])

        #  add user
        self.commcell.users.add(user_name=self.non_admin_user_name,
                                password=self.non_admin_password,
                                email="AutomatedUser@cvtest.com")

        #  update the user properties with created role
        entity_dictionary = {
            'assoc1': {
                'commCellName': [self.commcell.commserv_name],
                'role': [role_name]
            }
        }
        non_admin_user = self.commcell.users.get(self.non_admin_user_name)
        non_admin_user.update_security_associations(entity_dictionary=entity_dictionary,
                                                    request_type='UPDATE')
        self.log.info("Non admin user is created [%s] with commcell level "
                      "report management capability ", self.non_admin_user_name)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.utils.reset_temp_dir()
            self.create_non_admin_user()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def init_webconsole(self, user_name, passowrd):
        """Initialize webconsole with specified username and passwprd"""
        try:
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(user_name, passowrd)
            self.webconsole.goto_commcell_dashboard()
            navigator = Navigator(self.webconsole)
            navigator.goto_worldwide_dashboard(public_cloud=True)
            report = MetricsReport(self.webconsole)
            self.export = report.export_handler()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_admin_dashboard_osos_export(self):
        """
        Verify osos export on commcell dashboard
        """
        try:
            self.init_webconsole(self.inputJSONnode['commcell']["commcellUsername"],
                                 self.inputJSONnode['commcell']["commcellPassword"])
            self.export.to_osos_ppt()
            self.utils.wait_for_file_to_download('pptx')
            self.utils.validate_tmp_files("pptx")
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

    @test_step
    def verify_non_admin_user_visiblity(self):
        """Verify for non authorized user osos export is not visible"""
        try:
            self.init_webconsole(self.non_admin_user_name, self.non_admin_password)
            if 'OSOS PPT' in self.export.get_available_export_types():
                raise CVTestStepFailure("'OSOS export is visible to non authorized user[%s]"
                                        " in setup [%s]" % (self.non_admin_user_name,
                                                            self.commcell.webconsole_hostname))
            self.log.info("Verified OSOS export is not visible to non admin user")

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            # pass

    def run(self):
        try:
            self.init_tc()
            self.verify_non_admin_user_visiblity()
            self.verify_admin_dashboard_osos_export()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
