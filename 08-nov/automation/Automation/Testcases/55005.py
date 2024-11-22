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
       Intellisnap from Command Center"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Intellisnap Feature: Array management operations"

        self.admin_console = None
        self.arrayhelper_obj = None
        self.utils = TestCaseUtils(self)
        self.navigator = None
        self.tcinputs = {
            "ArrayVendor": None,
            "ArrayName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "ControlHost": None,
            "Controllers": None,

        }

    def setup(self):

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.arrayhelper_obj = ArrayHelper(self.admin_console, self.csdb)
        self.arrayhelper_obj.array_vendor = self.tcinputs['ArrayVendor']
        self.arrayhelper_obj.array_name = self.tcinputs['ArrayName']
        self.arrayhelper_obj.array_user = self.tcinputs['ArrayUser']
        self.arrayhelper_obj.array_password = self.tcinputs['ArrayPassword']
        self.arrayhelper_obj.control_host = self.tcinputs['ControlHost']
        self.arrayhelper_obj.controllers = self.tcinputs['Controllers']
        self.arrayhelper_obj.snap_config = self.tcinputs.get('SnapConfig', None)
        self.arrayhelper_obj.region = self.tcinputs.get('Region', None)
        self.arrayhelper_obj.multisite = self.tcinputs.get('Multisite', None)
        self.arrayhelper_obj.credential_name = self.tcinputs.get('Credential_name', None)


    def run(self):
        """Main function for test case execution"""

        try:
            self.navigator.navigate_to_arrays()
            self.arrayhelper_obj.add_engine()
            if self.tcinputs['ArrayVendor'] not in ('DataCore', 'Kubernetes CSI',
                                                    'NEC Storage', 'Oracle ZFS Storage',
                                                    'NetApp Cloud Target - Amazon S3',
                                                    'NetApp Cloud Target - Microsoft Azure Storage',
                                                    'NetApp Cloud Target - IBM Cloud Object Storage',
                                                    'NetApp Cloud Target - Alibaba Cloud Object Storage',
                                                    'NetApp Cloud Target - Google Cloud Storage',
                                                    'NetApp Cloud Target - NetApp ONTAP S3'):
                self.navigator.navigate_to_arrays()
                self.arrayhelper_obj.edit_snap_configuration()
            multisite = self.tcinputs.get('Multisite', None)
            if self.tcinputs['ArrayVendor'] == 'NetApp' and multisite is not None:
                self.navigator.navigate_to_arrays()
                self.arrayhelper_obj.edit_general()
            self.navigator.navigate_to_arrays()
            self.arrayhelper_obj.edit_array_access_node()
            if multisite is not None:
                if self.tcinputs.get('ArrayVendor_2', None):
                    self.arrayhelper_obj.array_vendor = self.tcinputs.get('ArrayVendor_2', None)
                    self.arrayhelper_obj.array_name = self.tcinputs.get('ArrayName_2', None)
                    self.arrayhelper_obj.array_user = self.tcinputs.get('ArrayUser_2', None)
                    self.arrayhelper_obj.array_password = self.tcinputs.get('ArrayPassword_2', None)
                    self.arrayhelper_obj.control_host = self.tcinputs.get('ControlHost_2', None)
                    self.arrayhelper_obj.controllers = self.tcinputs.get('Controllers_2', None)
                    self.arrayhelper_obj.snap_config = self.tcinputs.get('SnapConfig_2', None)
                    self.arrayhelper_obj.region = self.tcinputs.get('Region_2', None)

            if self.arrayhelper_obj.array_vendor == 'NetApp' and multisite is not None:
                self.navigator.navigate_to_arrays()
                self.arrayhelper_obj.add_engine()
                self.navigator.navigate_to_arrays()
                self.arrayhelper_obj.edit_snap_configuration()
                self.navigator.navigate_to_arrays()
                self.arrayhelper_obj.edit_general()


        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        try:
            self.navigator.navigate_to_arrays()
            self.arrayhelper_obj.action_delete_array()
            if self.tcinputs['ArrayVendor'] == 'NetApp' and self.tcinputs.get ('Multisite', None):
                self.array_name = self.tcinputs['ArrayName_2']
                self.navigator.navigate_to_arrays()
                self.arrayhelper_obj.action_delete_array()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
