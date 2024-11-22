# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------
"""

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.theme_helper import CustomizeThemeMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ basic acceptance test case for customize theme page """

    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Admin console - Customization page Acceptance"
        self.factory = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.customize_theme_obj = None

        self.tcinputs = {
            'logo_file_path': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.factory = BrowserFactory()
            self.browser = self.factory.create_browser_object()
            self.browser.open()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def run(self):
        """Method to execute the test case operations """
        try:
            primary_color = '#841a1a'
            header_color = '#31b7a5'
            header_text_color = '#b61c61'
            navigation_color = '#d6d8e9'
            link_color = '#152a0f'

            new_primary_color = '#1a8428'
            new_header_color = '#ac5ca6'
            new_header_text_color = '#223c0b'
            new_navigation_color = '#cfc3d8'
            new_link_color = '#d83ba7'

            self.log.info("Creating the self.login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.customize_theme_obj = CustomizeThemeMain(self.admin_console)
            self.customize_theme_obj.logo_file_path = self.tcinputs['logo_file_path']
            self.customize_theme_obj.add_theme_customization(primary_color=primary_color,
                                                             header_color=header_color,
                                                             header_text_color=header_text_color,
                                                             navigation_color=navigation_color,
                                                             link_color=link_color)
            self.log.info("Theme customization was set successfully in the commcell")

            self.customize_theme_obj.validate_theme_logo(self.customize_theme_obj.logo_file_path)
            self.log.info("Logo validation was performed successfully")

            self.customize_theme_obj.validate_theme_customization(primary_color=primary_color,
                                                                  header_color=header_color,
                                                                  header_text_color=header_text_color,
                                                                  navigation_color=navigation_color,
                                                                  link_color=link_color)
            self.log.info("successfully validated the color settings")

            self.admin_console.logout()
            self.log.info("successfully logged out from admin console")

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.customize_theme_obj.edit_theme_customization(new_primary_color=new_primary_color,
                                                              new_header_color=new_header_color,
                                                              new_header_text_color=new_header_text_color,
                                                              new_navigation_color=new_navigation_color,
                                                              new_link_color=new_link_color)
            self.log.info("Theme customization options were modified successfully")

            self.customize_theme_obj.validate_theme_customization(primary_color=new_primary_color,
                                                                  header_color=new_header_color,
                                                                  header_text_color=new_header_text_color,
                                                                  navigation_color=new_navigation_color,
                                                                  link_color=new_link_color)
            self.log.info("successfully validated the color settings")

            self.admin_console.logout()
            self.log.info("successfully logged out from admin console")

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                    self.inputJSONnode['commcell']['commcellPassword'])

            self.customize_theme_obj.remove_theme_customization()
            self.log.info("Theme customization was reset with default values successfully")

            self.customize_theme_obj.validate_theme_customization()
            self.log.info("successfully validated the default color settings")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean-up the test case environment created"""
        try:
            Browser.close_silently(self.browser)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
