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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.array_helper import ArrayHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Acceptance test case for Add/Edit/Delete Array in the Array Management for
        Oracle ZFS Intellisnap from Command Center"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Intellisnap Feature: Array management operations - Oracle ZFS"
        self.admin_console = None
        self.arrayhelper_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "ArrayVendor": None,
            "ArrayName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "ControlHost": None,
            "Controllers": None,
            "Storage Device Group": None,
            "Mount Retry Count": None,
            "Remote SnapMA": None,
            "Mount retry interval(in seconds)": None,
            "Snap Operation Retry Interval (in seconds)": None,
            "Server Port": None,
            "Mount Datastore": None
        }

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.arrayhelper_obj = ArrayHelper(self.admin_console, self.csdb)
        self.arrayhelper_obj.array_vendor = self.tcinputs['ArrayVendor']
        self.arrayhelper_obj.array_name = self.tcinputs['ArrayName']
        self.arrayhelper_obj.array_user = self.tcinputs['ArrayUser']
        self.arrayhelper_obj.array_password = self.tcinputs['ArrayPassword']
        self.arrayhelper_obj.control_host = self.tcinputs['ControlHost']
        self.arrayhelper_obj.controllers = self.tcinputs['Controllers']
        self.arrayhelper_obj.storage_device_group = self.tcinputs['Storage Device Group']
        self.arrayhelper_obj.mount_retry_count = self.tcinputs['Mount Retry Count']
        self.arrayhelper_obj.remote_snap_ma = self.tcinputs['Remote SnapMA']
        self.arrayhelper_obj.mount_retry_interval = self.tcinputs['Mount retry interval(in seconds)']
        self.arrayhelper_obj.snap_operation_retry_interval = self.tcinputs['Snap Operation Retry Interval (in seconds)']
        self.arrayhelper_obj.server_port = self.tcinputs['Server Port']
        self.arrayhelper_obj.mount_datastore = self.tcinputs['Mount Datastore']


    def run(self):
        """Main function for test case execution"""

        try:
            self.arrayhelper_obj.add_array()
            

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        try:
            self.arrayhelper_obj.action_delete_array()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
