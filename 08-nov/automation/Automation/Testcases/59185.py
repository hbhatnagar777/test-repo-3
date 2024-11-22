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

    run()           --  run function of this test case
"""


from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.sevice_commcell_helper import ServiceCommcellMain
from Web.AdminConsole.Helper.UserGroupHelper import UserGroupMain

from Reports.utils import TestCaseUtils
from urllib.parse import urlparse


class TestCase(CVTestCase):
    """Class for executing UI check for Jupiter"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Multicommcell: UI Registration and Switch to Service commcell"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.service_commcell_obj = None
        self.user_group_obj = None
        self.navigator = None
        self.tcinputs = {
            'hostname': None,
            'username': None,
            'password': None,
            'master': None,
            'child': None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator

            self.service_commcell_obj = ServiceCommcellMain(self.admin_console, self.csdb, self.commcell)
            self.user_group_obj = UserGroupMain(self.admin_console)
            self.service_commcell_obj.host_name = self.tcinputs['hostname']
            self.service_commcell_obj.user_name = self.tcinputs['username']
            self.service_commcell_obj.password = self.tcinputs['password']
            self.service_commcell_obj.configure_as_IdP = 'True'
            self.service_commcell_obj.create_service_commcell()
            self.service_commcell_obj.validate_service_commcell()
            self.navigator.switch_service_commcell(commcell_name=self.tcinputs['child'])
            if not urlparse(self.admin_console.current_url()).netloc == self.tcinputs['hostname']:
                raise Exception("Redirection Failed")
            self.user_group_obj.add_new_user_group()
            self.log.info("User group creation completed. validating User group...")
            self.user_group_obj.validate_user_group()
            self.log.info("Initial User group validation completed. Editing Details")
            self.user_group_obj.delete_user_group()
            self.navigator.switch_service_commcell(commcell_name=self.tcinputs['master'])
            self.service_commcell_obj.delete_service_commcell()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To logout from Adminconsole """

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
