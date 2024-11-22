# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify vmware replication group creation and its primary copy job completion

Sample input:
"60413": {
            "rpstore_mediagent":"RP store media agent name"
            "rpstore_mediagent2":"RP store second media agent name"
            "lib_location":"Library location path"
       }
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from VirtualServer.VSAUtils import VirtualServerHelper
from Web.AdminConsole.DR.rp_store import RpstoreOperations
import re


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)

        self.name = "RPStore CRUD Test"
        self.tcinputs = {
            "rpstore_mediagent": None,
            "rpstore_mediagent2": None,
            "lib_location": None
        }
        self.lib_location = None
        self.rpstore = None
        self.rpstorename = None
        self.rpstore_mediagent = None
        self.rpstore_mediagent2 = None
        self.max_size_1 = "80"
        self.path_1 = "Local Path"
        self.peak_interval_1 = {'Monday': [6]}
        self.peak_interval_2 = {"Sunday": [1]}
        self.day_1 = "Sunday"
        self.day_2 = "Monday"
        self.rpstoremaxspace_1 = "79"
        self.rptotalcapacity_1 = "80.00 GB"
        self.time_1 = "6am-7am"
        self.time_2 = "1am-2am"

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.rpstore_mediagent = self.tcinputs["rpstore_mediagent"]
        self.rpstore_mediagent2 = self.tcinputs["rpstore_mediagent2"]
        self.lib_location = self.tcinputs["lib_location"]

    def login(self):
        """Logs in to admin console"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
            self.replication_group = ReplicationGroup(self.admin_console)
            self.replication_details = ReplicationDetails(self.admin_console)
            self.rpstore = RpstoreOperations(self.admin_console)

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def rpstore_name(self):
        """
        Generates rpstore name
        """
        self.rpstorename = f'Rpstore_TC_{self.id}'

    @test_step
    def create_rpstore(self):
        """
        Creates an rp store
        """
        self.rpstore.create_recovery_store(self.rpstorename, self.rpstore_mediagent, self.max_size_1, self.lib_location,
                                           self.path_1, self.peak_interval_1)

    @test_step
    def verify_general_details(self, rpstorename, rpstore_mediagent, rpstoremaxspace, rptotalcapacity, peakenabled,
                               peakintervaltime, peakintervalday):
        """Verifies the General Summary tab of an RP store"""
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.goto_rpstore(rpstorename)
        panel_details = self.rpstore.get_rpstorepanel_info()
        self.log.info("Panel detail:%s", panel_details)
        self.utils.assert_comparison(panel_details['Storage name'], rpstorename)
        self.utils.assert_comparison(panel_details['Associated MediaAgents'], rpstore_mediagent)
        self.utils.assert_comparison(panel_details['Maximum size (GB)'], rpstoremaxspace)
        self.utils.assert_comparison(panel_details['Total capacity'], rptotalcapacity)
        if peakenabled == 0:
            self.utils.assert_comparison(panel_details['Peak interval'], "Not enabled")
        else:
            actual_day = re.search("^\w+", panel_details['Peak interval']).group()
            self.utils.assert_comparison(actual_day, peakintervalday)
            actual_time = re.search("\d[a|p]m-\d[a|p]m", panel_details['Peak interval']).group()
            self.utils.assert_comparison(actual_time, peakintervaltime)
        self.log.info("Successfully verified general summary panel on RP store page")

    @test_step
    def validate_locations_details(self, rpstore_mediagent, lib_location):
        """Verifies the Backup Location tab of an RP store"""
        actual_location = self.rpstore.get_column_data("Name")
        actual_status = self.rpstore.get_column_data("Status")

        self.utils.assert_comparison(actual_location, "[" + rpstore_mediagent + "] " + lib_location)
        self.utils.assert_comparison(actual_status, "Ready")

        self.log.info("Successfully Locations values on RP store page")

    @test_step
    def edit_and_verify_storage(self, name, rpstoremaxspace, rp_interval):
        """Change the edit storage options and verify disabled field """
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.goto_rpstore(self.rpstorename)
        self.rpstore.edit_general_details()
        self.rpstore.edit_storage(name, rpstoremaxspace, rp_interval)
        self.rpstore.edit_general_details()
        result = self.rpstore.verify_disabled_fields(self.rpstore_mediagent2)
        self.admin_console.click_button('Save')
        if result:
            self.log.info("Verified the media agent field is disabled as expected")
        else:
            raise CVTestStepFailure("The media agent field is enabled as expected")

    @test_step
    def verify_deletion(self, rpstore_name):
        """
        Verify the deltion of RP store
        Args:
             rpstore_name: Specify name of the rpstore deleted
        """
        self.admin_console.navigator.navigate_to_rpstore()
        rpstore_list = self.rpstore.get_all_rpstores()
        if rpstore_name not in rpstore_list:
            self.log.info("Successfully verified Rpstore %s with name deleted" % rpstore_name)
        else:
            raise CVTestStepFailure(f"Rpstore {rpstore_name} not deleted")

    @test_step
    def clear_intervals(self, rpstore_name):
        """Clears the intervals set on a rpstore"""
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.goto_rpstore(rpstore_name)
        self.rpstore.edit_general_details()
        self.rpstore.clear_intervals()

    @test_step
    def add_mediagent(self, media_agent_name, rpstore_name):
        """
        Clears the intervals set on a rpstore
        """
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.goto_rpstore(rpstore_name)
        self.rpstore.add_mediagent(media_agent_name)

    @test_step
    def delete_rpstore(self, rpstore_name):
        """
        delete the rp store
        """
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.delete_rpstore(rpstore_name)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_rpstore(self.rpstorename)
            self.verify_deletion(self.rpstorename)
            self.create_rpstore()
            self.verify_general_details(self.rpstorename, self.rpstore_mediagent,
                                        self.rpstoremaxspace_1, self.rptotalcapacity_1,
                                        0, self.time_1, self.day_2)
            self.validate_locations_details(self.rpstore_mediagent, self.lib_location)
            self.edit_and_verify_storage(self.rpstorename + "renamed", self.max_size_1, self.peak_interval_2)
            self.verify_general_details(self.rpstorename + "renamed", self.rpstore_mediagent,
                                        self.rpstoremaxspace_1, self.rptotalcapacity_1,
                                        1, self.time_2, self.day_1)
            self.edit_and_verify_storage(self.rpstorename, self.max_size_1, self.peak_interval_2)
            self.clear_intervals(self.rpstorename)
            self.verify_general_details(self.rpstorename, self.rpstore_mediagent,
                                        self.rpstoremaxspace_1, self.rptotalcapacity_1,
                                        0, None, None)
            self.add_mediagent([self.rpstore_mediagent2], self.rpstorename)
            self.verify_general_details(self.rpstorename, self.rpstore_mediagent + "," + self.rpstore_mediagent2,
                                        self.rpstoremaxspace_1, self.rptotalcapacity_1,
                                        0, None, None)
            self.delete_rpstore(self.rpstorename)
            self.verify_deletion(self.rpstorename)

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
