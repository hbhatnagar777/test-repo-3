# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to Reports Tagging in AdminConsole
"""


from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)

from Web.AdminConsole.adminconsole import AdminConsole

from Web.AdminConsole.Reports.manage_reports import (
    ManageReport,
    Tag
)


from Reports import reportsutils

REPORTS_CONFIG = reportsutils.get_reports_config()


class TestCase(CVTestCase):
    """Testcase to verify Reports Tagging in AdminConsole"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Web Reports: Tagging of reports"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.navigator = None
        self.tag = None
        self.manage_rpt = None
        self.tag_name = 'Auto_TC48146'
        self.non_admin_user = "auto_non_admin_user_48146"
        self.non_admin_password = "######"
        self.report_name = REPORTS_CONFIG.REPORTS.CUSTOM[0]

    def init_adminconsole(self):
        """Initialize the application to the state required by the testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_rpt = ManageReport(self.admin_console)
            self.tag = Tag(self.admin_console)

        except Exception as msg:
            raise CVTestCaseInitFailure(msg) from msg

    @test_step
    def cleanup(self):
        """Clean up tags created by this testcase"""
        if self.tag_name in self.manage_rpt.get_tags():
            self.manage_rpt.tag_report(self.report_name)
            self.tag.delete_tag(self.tag_name)
            self.tag.apply_to_all()
            self.tag.save()

    def create_non_admin_user(self):
        """create non admin user """
        role_name = "Report_Management_48146"
        # If user exists no need to create user/role.
        if not self.commcell.users.has_user(self.non_admin_user):
            self.log.info("Creating user [%s]", self.non_admin_user)
            self.commcell.users.add(
                user_name=self.non_admin_user,
                email="AutomatedUsr48146@cvtest.com",
                password=self.non_admin_password
            )
        else:
            self.log.info("non admin user [%s] already exists", self.non_admin_user)
            return
        # Create role
        if not self.commcell.roles.has_role(role_name):
            self.commcell.roles.add(rolename=role_name, permission_list=["Report Management"])
        entity_dictionary = {
            'assoc1': {
                'clientName': [self.commcell.commserv_name],
                'role': [role_name]
            }
        }
        non_admin_user = self.commcell.users.get(self.non_admin_user)
        non_admin_user.update_security_associations(entity_dictionary=entity_dictionary,
                                                    request_type='UPDATE')
        self.log.info("Non admin user [%s] is created", self.non_admin_user)

    def validate_non_adminuser(self, tag_exist, tag_name=None):
        """check tag exist for non admin user
        Args:
            tag_exist (bool): True/False
            tag_name (str): tag name
        """
        na_browser = BrowserFactory().create_browser_object(name='nonAdmin')
        try:
            na_browser.open()
            na_admin_console = AdminConsole(na_browser, self.commcell.webconsole_hostname)
            na_admin_console.login(self.non_admin_user, self.non_admin_password)
            na_navigator = na_admin_console.navigator
            na_navigator.navigate_to_reports()
            manage_rpt = ManageReport(na_admin_console)
            tags = manage_rpt.get_tags()
            if tag_name is None:
                tag_name = self.tag_name
            if tag_exist:
                if tag_name not in tags:
                    raise CVTestStepFailure(
                        f"Tag [{tag_name}] doesn't exist in Report Page for user"
                        f" {self.non_admin_user}"
                    )
            else:
                if tag_name in tags:
                    raise CVTestStepFailure(
                        f"Global Tag [{tag_name}] exist in Report Page for user"
                        f" {self.non_admin_user}, it is not expected to be present"
                    )

        finally:
            Browser.close_silently(na_browser)

    @test_step
    def validate_private_tag(self):
        """Validate Private Tag"""
        self.manage_rpt.tag_report(self.report_name)
        self.tag.create_tag(self.tag_name)
        self.tag.click_tag(self.tag_name)
        tags_list = self.manage_rpt.get_tags()
        if self.tag_name not in tags_list:
            raise CVTestStepFailure(f"Private Tag [{self.tag_name}] doesn't exist in Report Page")
        if len(tags_list) != 1:
            raise CVTestStepFailure(f"Couldn't reach into the {self.tag_name} page")

        self.validate_non_adminuser(tag_exist=False)

    @test_step
    def validate_global_tag(self):
        """Validate Global Tag"""
        self.manage_rpt.tag_report(self.report_name)
        self.tag.apply_to_all()
        self.tag.save()
        self.validate_non_adminuser(tag_exist=True)

    @test_step
    def validate_delete_tag(self):
        """Validate delete tag"""
        self.manage_rpt.tag_report(self.report_name)
        self.tag.delete_tag(self.tag_name)
        self.tag.apply_to_all()
        self.tag.save()
        if self.tag_name in self.manage_rpt.get_tags():
            raise CVTestStepFailure(f"Deleted Tag [{self.tag_name}] still exist in Report Page")

    @test_step
    def edit_tag(self):
        """Validate edit tag name"""
        new_name = self.tag_name + '_new'
        self.manage_rpt.edit_tag(self.tag_name, new_name)
        self.browser.driver.refresh()
        self.navigator.wait_for_completion()
        if new_name not in self.manage_rpt.get_tags():
            raise CVTestStepFailure(f"Edited Tag [{new_name}] doesn't exist in Report Page")
        self.validate_non_adminuser(tag_exist=True, tag_name=new_name)
        self.tag_name = new_name

    def run(self):
        try:
            self.create_non_admin_user()
            self.init_adminconsole()
            self.cleanup()
            self.validate_private_tag()
            self.validate_global_tag()
            self.edit_tag()
            self.validate_delete_tag()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
