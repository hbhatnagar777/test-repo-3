# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Input Example:

    "testCases":
            {
                "48635":
                 {
                    "addCommcellNames" : "CommCell1,CommCell2",
                    "editCommcellNames" : "CommCell",
                    "password": "******"
                    }
            }
"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Reports.commcells import Commcell
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.commcell_groups import CommcellGroup
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Reports.utils import TestCaseUtils

from cvpysdk.security.user import Users
from cvpysdk.security.usergroup import UserGroups
from time import sleep


_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics CommCell Group create, edit and Share options"
        self.browser: Browser = None
        self.admin_console: AdminConsole = None
        self.commcell_group: CommcellGroup = None
        self.user: Users = None
        self.usergroup: UserGroups = None
        self.tcinputs = {"addCommcellNames": None,
                         "editCommcellNames": None
                        }
        self.add_commcells = []
        self.edit_commcells = []
        self.COMMCELL_GROUP_NAME = 'Automated_commcellGroup_' + '48635'
        self.USER_NAME = 'Automated_User_48635'
        self.USER_GROUP_USER_NAME = 'Automated_User2_48635'
        self.USER_GROUP_NAME = 'Automated_User_Group_48635'
        self.USER_EMAIL1 = 'AutomatedUser148635@cvtest.com'
        self.USER_EMAIL2 = 'AutomatedUser248635@cvtest.com'
        self.utils: TestCaseUtils = None

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.commcell_group = CommcellGroup(self.admin_console)
            self.metrics_commcell = Commcell(self.admin_console)
            self.navigator = self.admin_console.navigator
            self.manage_reports = ManageReport(self.admin_console)
            self.navigator.navigate_to_metrics()
            self.manage_reports.access_commcell_group()
            self.user = Users(self.commcell)
            self.usergroup = UserGroups(self.commcell)
            self.add_commcells = self.tcinputs["addCommcellNames"].split(',')
            self.edit_commcells = self.tcinputs["editCommcellNames"].split(',')
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def cleanup(self):
        """clean up the commcellgroup and users if already existing"""
        if self.commcell_group.is_group_exist(self.COMMCELL_GROUP_NAME):
            self.commcell_group.delete(self.COMMCELL_GROUP_NAME)
        if self.user.has_user(self.USER_NAME):
            self.user.delete(self.USER_NAME, 'admin')
        if self.user.has_user(self.USER_GROUP_USER_NAME):
            self.user.delete(self.USER_GROUP_USER_NAME, 'admin')
        if self.usergroup.has_user_group(self.USER_GROUP_NAME):
            self.usergroup.delete(self.USER_GROUP_NAME, None, 'master')
        sleep(5)

    def create_users(self):
        """create new user group and users"""
        self.user.add(self.USER_NAME, self.USER_EMAIL1, self.USER_NAME, None,
                      self._tcinputs["password"])
        self.user.add(self.USER_GROUP_USER_NAME, self.USER_EMAIL2, self.USER_GROUP_USER_NAME,
                      None, self._tcinputs["password"])
        self.usergroup.add(self.USER_GROUP_NAME, None, [self.USER_GROUP_USER_NAME])

    @test_step
    def create_commcell_group(self):
        """Creation of new commcell group"""
        self.commcell_group.create(self.COMMCELL_GROUP_NAME, self.add_commcells)
        if self.commcell_group.is_group_exist(self.COMMCELL_GROUP_NAME):
            self.log.info("Creation of the commcell group %s is successful"
                          % self.COMMCELL_GROUP_NAME)
        else:
            raise CVTestStepFailure("Commcell group %s created now doesn't exist in "
                                    "Commcell groups listing page" % self.COMMCELL_GROUP_NAME)

    @test_step
    def edit_commcell_group(self):
        """Adding new commcell to the commcell group"""
        self.commcell_group.edit(self.COMMCELL_GROUP_NAME)
        self.commcell_group.add_commcells(self.edit_commcells)
        self.commcell_group.save()
        commcell_count = int(self.commcell_group.commcell_count_of_group(self.COMMCELL_GROUP_NAME))
        input_commcell_count = len(self.add_commcells) + len(self.edit_commcells)
        if commcell_count != input_commcell_count:
            raise CVTestStepFailure("commcell group %s has %d commcells instead of %d commcells,"
                                    " Edit group failed"
                                    % (self.COMMCELL_GROUP_NAME, commcell_count, input_commcell_count))

    def get_group_listing_page_details(self):
        """"get group details from listing page"""
        table_data = self.commcell_group.get_commcell_group_details(self.COMMCELL_GROUP_NAME)
        for key, value in table_data.items():
            self.log.info("key [%s] value [%s]" % (key, value))
        return table_data

    def verify_commcell_count(self, commcell_count, listingpage_commcell_count):
        """verify commcell count values"""
        if commcell_count != listingpage_commcell_count:
            raise CVTestStepFailure(
                "Commcell Count from Group listing page is [%d], commcell listing page is [%d],"
                "both values are not matching "
                "for commcell group %s" % (commcell_count,
                                           listingpage_commcell_count,
                                           self.COMMCELL_GROUP_NAME))
        else:
            self.log.info("Verified Commcell Count for group %s" % self.COMMCELL_GROUP_NAME)

    def verify_active_clients_count(self, active_clients_count, listingpage_active_clients_count):
        """verify active clients count values"""
        if active_clients_count != listingpage_active_clients_count:
            raise CVTestStepFailure(
                "Commcell Count from Group listing page is [%d] and commcell listing page is [%d]"
                "both values are not matching "
                "for commcell group %s" % (listingpage_active_clients_count,
                                           active_clients_count,
                                           self.COMMCELL_GROUP_NAME))
        else:
            self.log.info("Verified Active Clients Count value for commcell group %s"
                          % self.COMMCELL_GROUP_NAME)

    @test_step
    def validate_group_listing_page(self):
        """validate group for Number of Commcells, Active Clients values
         in groups listing page with dashboard and commcells listing page of the group """
        listing_values = self.get_group_listing_page_details()
        self.commcell_group.access_commcell_group(self.COMMCELL_GROUP_NAME)
        self.metrics_commcell.goto_commcell_tab()
        commcell_details = self.commcell_group.get_details_of_commcells_in_commcell_group()
        self.verify_commcell_count(len(commcell_details['CommCell Name']),
                                   int(listing_values['Number of CommCells'][0]))
        self.verify_active_clients_count(sum(map(int,commcell_details['Active Servers'])) +
                                         sum(map(int,commcell_details['Active VMs'])),
                                         int(listing_values['Active Clients'][0]))

    def validate_user(self, user_name):
        """Opens new browser and validates if user can view the commcell group"""
        browser2 = BrowserFactory().create_browser_object()
        browser2.open()
        user_admin_console = AdminConsole(browser2, self.commcell.webconsole_hostname)
        user_admin_console.login(user_name, self._tcinputs["password"])
        navigator2 = user_admin_console.navigator
        navigator2.navigate_to_metrics()
        manage_reports = ManageReport(user_admin_console)
        manage_reports.access_commcell_group()
        commcell_group2 = CommcellGroup(user_admin_console)
        ret = commcell_group2.is_group_exist(self.COMMCELL_GROUP_NAME)
        if ret is False:
            raise CVTestStepFailure("Commcell group %s is not visible to the user %s. "
                                    "User association to the Commcell group failed"
                                    % (self.COMMCELL_GROUP_NAME, user_name))
        else:
            self.log.info("User associaton to the Commcell group is successful")
        AdminConsole.logout_silently(user_admin_console)
        Browser.close_silently(browser2)

    @test_step
    def validate_user_association(self):
        """validate user association to the commcell group"""
        self.manage_reports.access_commcell_group()
        self.commcell_group.associate_user(self.COMMCELL_GROUP_NAME, self.USER_NAME)
        self.log.info("Assigned User %s to the commcell group %s" %
                      (self.USER_NAME, self.COMMCELL_GROUP_NAME))
        self.validate_user(self.USER_NAME)
        self.user.delete(self.USER_NAME, 'admin')

    @test_step
    def validate_user_group_association(self):
        """validate user group association to the commcell group"""
        self.manage_reports.access_commcell_group()
        self.commcell_group.associate_user(self.COMMCELL_GROUP_NAME, self.USER_GROUP_NAME)
        self.log.info("Assigned User Group %s to the commcell group %s" %
                      (self.USER_GROUP_NAME, self.COMMCELL_GROUP_NAME))
        self.validate_user(self.USER_GROUP_USER_NAME)

    @test_step
    def delete_commcell_group(self):
        """deletion of the commcell group"""
        self.manage_reports.access_commcell_group()
        self.commcell_group.delete(self.COMMCELL_GROUP_NAME)

    def run(self):
        try:
            self.init_tc()
            self.cleanup()
            self.create_users()
            self.create_commcell_group()
            self.edit_commcell_group()
            self.validate_group_listing_page()
            self.validate_user_association()
            self.validate_user_group_association()
            self.commcell_group.delete(self.COMMCELL_GROUP_NAME)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
