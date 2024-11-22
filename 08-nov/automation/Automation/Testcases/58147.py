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

Input Example :
    "testCases":
            {
                "58078":
                        {
                                "ArrayVendor": Dell EMC Unity,
                                "ServerName": ,
                                "ArrayUser": ,
                                "ArrayPassword": "",
                                "ControlHost": None,
                                "Controllers": None

                        }

            }


    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case


"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.nas_helper import Nashelper



class TestCase(CVTestCase):

    """Class for executing Acceptance test case for Add/Delete NAS server in the Array Management for
       Dell EMC Unity from Command Center"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Add/Delete NAS Array in the Array Management for NAS Server : Dell EMC Unity from Command center"
        self.admin_console = None
        self.fs_server_obj = None
        self.array_obj = None
        self.nashelper_obj = None
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            "ServerName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "ControlHost": None,
            "Controllers": None}

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.nashelper_obj = Nashelper(self.admin_console)
        self.nashelper_obj.array_vendor = 'Dell EMC Unity'
        self.nashelper_obj.server_name = self.tcinputs['ServerName']
        self.nashelper_obj.array_name = self.tcinputs['ServerName']
        self.nashelper_obj.array_user = self.tcinputs['ArrayUser']
        self.nashelper_obj.array_password = self.tcinputs['ArrayPassword']
        self.nashelper_obj.control_host = self.tcinputs['ControlHost']
        self.nashelper_obj.controllers = self.tcinputs['Controllers']



    def run(self):
        """Main function for test case execution"""

        try:
            self.nashelper_obj.add_engine()
            self.nashelper_obj.update_client(self.nashelper_obj.server_name)
            self.nashelper_obj.reconfigure_server()
            self.nashelper_obj.action_delete_array(self.tcinputs['ServerName'])
            # self.nashelper_obj.delete_client(self.nashelper_obj.server_name)
            self.nashelper_obj.retire_server(self.nashelper_obj.server_name)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)


        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
