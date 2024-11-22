# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Initializes pre-requisites for this test case

    run()           --  run function of this test case

Input Example:

   "testCases": {
        "63405": {
            "ContentGroups":[]
        }
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Tags import EntityTags
from Web.AdminConsole.Archiving.ContentGroups import ContentGroups
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """
    Class for executing acceptance test case for AaaS - analyze then archive
    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Metallic Archiving: manage, view, filter, delete tags"
        self.config = get_config()
        self.browser = None
        self.hub_dashboard = None
        self.admin_console = None
        self.contentgroups = None
        self.tagnames = None
        self.tcinputs = {
            "ContentGroups": []
        }

    def init_pre_req(self):
        """ Initialize test case inputs"""
        if len(self.tcinputs["ContentGroups"]):
            self.contentgroupnames = self.tcinputs["ContentGroups"]
        else:
            raise CVTestStepFailure(
                "Multipath_Content is empty. please provide test content group names")

        self.tagnames = {'AutomationTag1': 'automationtag1',
                         'AutomationTag2': 'automationtag2',
                         'AutomationTag3': 'automationtag3',
                         'AutomationTag4': ''}

    @test_step
    def remove_all_tags(self):
        """remove all existing tags for the content groups to be tested"""
        for groupname in self.contentgroupnames:
            self.contentgroups.remove_tags(groupname)
        self.admin_console.refresh_page()

    def cleanup_test_data(self):
        """ cleanup test data"""
        self.remove_all_tags()
        self.tags = EntityTags(self.admin_console)
        self.admin_console.navigator.navigate_to_tags(True)
        for tagname in [*(self.tagnames)]:
            if self.tags.is_tag_name_exists(tagname):
                self.tags.action_delete_entity_tag(tagname)

    @test_step
    def verify_add_tags(self):
        """verify add tags to content groups"""
        for groupname in self.contentgroupnames:
            self.contentgroups.add_tag(groupname, self.tagnames)
        self.admin_console.refresh_page()
        for groupname in self.contentgroupnames:
            tagnames = self.contentgroups.get_tag_name_value_dict(groupname)
            if tagnames != self.tagnames:
                raise CVTestStepFailure(
                    "content group %s does not have correct tags", groupname)

    @test_step
    def verify_filter_tags(self):
        """verify filter content groups with tags"""
        for tagname in [*(self.tagnames)]:
            groupnames = self.contentgroups.filter_with_tagname(tagname)
            if groupnames.sort() != self.contentgroupnames.sort():
                raise CVTestStepFailure(
                    "filter with tags, does not show correct content groups")
            if tagname == "AutomationTag1":
                tag_strings = self.contentgroups.get_tags_column_value(
                    tag_name=tagname)
                expected_tag = tagname + " : " + self.tagnames[tagname]
                if tag_strings[0] != expected_tag:
                    raise CVTestStepFailure(
                        "filter with tag name %s show wrong tags", tagname)

    @test_step
    def verify_view_tags(self):
        """verify view tags from content group page"""
        for groupname in self.contentgroupnames:
            view_tag_dict = self.contentgroups.view_tags(groupname)
            if self.tagnames != view_tag_dict:
                raise CVTestStepFailure(
                    "view tags show wrong tag names/values")

    def setup(self):
        """ Pre-requisites for this testcase """
        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

    def run(self):
        """Main function for test case execution"""
        _desc = """
        1)    remove existing tags for test content groups
        2)    verify add tags
        3)    verify filter with tag names
        4)    verify clicking tags and view the tag list
        5)    test data clean up
        """
        try:
            try:
                self.service = HubServices.file_archiving
                self.hub_dashboard = Dashboard(
                    self.admin_console, self.service)
                self.hub_dashboard.choose_service_from_dashboard()
                self.admin_console.click_button(value='Acknowledge')
            except BaseException:
                pass
            self.admin_console.navigator.navigate_to_archivingv2()
            self.admin_console.access_tab("Content groups")
            self.contentgroups = ContentGroups(self.admin_console)
            self.init_pre_req()
            self.remove_all_tags()
            self.verify_add_tags()
            self.verify_filter_tags()
            # self.verify_view_tags()
            self.cleanup_test_data()

        except Exception as excp:
            handle_testcase_exception(self, excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
