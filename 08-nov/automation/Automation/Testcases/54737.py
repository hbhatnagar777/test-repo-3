# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Basic acceptance test case for Email templates in AdminConsole

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.email_template_helper import EmailTemplateHelper
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test Case for Email templates in AdminConsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.email_templates_helper_obj = None
        self.tcinputs = {
                "template_sub": None,
                "new_template_name": None
        }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.email_templates_helper_obj = EmailTemplateHelper(self.admin_console)

    def run(self):
        """
        Test Case
        1) Creates Email header and footer
        2) Add an email template, set it as default, send test mail
        3) Modify email template
        4) Delete email template

        """
        try:

            self.log.info("****** Creating email header and footer ******")
            self.email_templates_helper_obj.modify_email_header_footer()

            self.log.info("****** Adding an email template ******")
            self.email_templates_helper_obj.add_email_template()

            self.log.info("****** Setting email template as default ******")
            self.email_templates_helper_obj.set_template_as_default()
            self.email_templates_helper_obj.verify_email_template_contents()

            self.log.info("****** Sending test mail for the template ******")
            self.email_templates_helper_obj.template_send_test_mail()

            self.email_templates_helper_obj.new_template_name = self.tcinputs['new_template_name']
            self.email_templates_helper_obj.template_subject = self.tcinputs['template_sub']

            self.log.info("****** Modifying email template ******")
            self.email_templates_helper_obj.modify_email_template()
            self.email_templates_helper_obj.verify_email_template_contents()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:

            self.email_templates_helper_obj.delete_email_template()
            AdminConsole.logout_silently(self.admin_console)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            Browser.close_silently(self.browser)
