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

    setup()         --  Setup function to initialize the variables

    run()           --  Executes test case

    tear down()     --  Clears all the entities created

"""


from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory,Browser
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance of SAML test case"""
    test_step = TestStep()

    def __init__(self):
        """
            Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "SAML- login with username"
        self.browser = None
        self.utils = None
        self.saml_obj = None
        self.webconsole_url = None
        self.smtp_address = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            "idp metadata location": None,
            "AD machine IP": None,
            "AD machine name": None,
            "AD administrator": None,
            "AD admin password": None,
            "Existing SAML user": None,
            "Existing SAML user password": None,
            "New SAML User": None,
            "New SAML password": None
        }

    @test_step
    def init_tc(self):
        """ Initial configuration for the test case. """

        factory = BrowserFactory()

        try:
            machine = Machine(self.client)
            download_directory = self.utils.get_temp_dir()
            machine.create_directory(download_directory)
        except Exception as exp:
            if str(exp == "Directory already exists"):
                self.log.info("Directory already exists")

        self.browser = factory.create_browser_object()
        self.browser.set_downloads_dir(download_directory)
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
        self.navigator_obj = self.admin_console.navigator
        self.saml_obj.app_name = "test_50949"
        self.saml_obj.idp_metadata_path = self.tcinputs['idp metadata location']
        self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
        self.smtp_address = self.tcinputs['New SAML User'].split('@')[1]
        self.saml_obj.redirect_rule = {"Commcell": self.smtp_address}
        self.adfs_app_name = "ADFS_check"
        self.web_url = "https://" + self.commcell.webconsole_hostname + "/webconsole"

    @test_step
    def add_saml_app(self):
        """ Adds SAML application and download SP metadata """
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['idp metadata location'],
                                      self.smtp_address,
                                      self.webconsole_url,
                                      False,
                                      None,
                                      jks_file_path=None,
                                      alias_name=None,
                                      keystore_password=None, key_password=None,
                                      auto_generate_key=True)
        self.file_path = self.saml_obj.download_spmetadata(download_dir=self.utils.get_temp_dir())

    @test_step
    def add_saml_app_in_AD_machine(self):
        """ Adds trust party app in ADFS machine """
        self.saml_obj.edit_trust_party_adfs(self.saml_obj.app_name,
                                            self.tcinputs['AD machine IP'],
                                            self.tcinputs['AD administrator'],
                                            self.tcinputs['AD admin password'],
                                            self.file_path)

    @test_step
    def disable_saml_app(self):
        """ Disable SAML app at CS and attempt login """
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.open_saml_app(self.saml_obj.app_name)
        self.saml_obj.modify_saml_general_settings(self.saml_obj.app_name,
                                                   modify_app_state=True,
                                                   enable_app=False)
        self.admin_console.logout()

    def run(self):
        """Executes the testcase"""
        try:
            self.init_tc()
            self.add_saml_app()
            self.admin_console.logout()
            self.add_saml_app_in_AD_machine()

            self.saml_obj.initiate_saml_login(False, self.tcinputs['AD machine name'],
                                              self.web_url, self.adfs_app_name,
                                              self.tcinputs['New SAML User'],
                                              self.tcinputs['New SAML password'],
                                              tab_off_approach=True,
                                              verify_sso=False)

            self.saml_obj.initiate_saml_logout(False, self.tcinputs['AD machine name'],
                                               self.web_url,
                                               verify_single_logout=True)

            self.saml_obj.add_associations_on_saml_app(self.tcinputs['Existing SAML user'])

            self.saml_obj.initiate_saml_login(True, self.tcinputs['AD machine name'],
                                              self.web_url, self.adfs_app_name,
                                              self.tcinputs['Existing SAML user'],
                                              self.tcinputs['Existing SAML user password'],
                                              tab_off_approach=False,
                                              verify_sso=False)

            self.saml_obj.initiate_saml_logout(False, self.tcinputs['AD machine name'],
                                               self.web_url,
                                               verify_single_logout=True)

            self.disable_saml_app()

            status = self.saml_obj.initiate_saml_login(True, self.tcinputs['AD machine name'],
                                                       self.web_url, self.adfs_app_name,
                                                       self.tcinputs['New SAML User'],
                                                       self.tcinputs['New SAML password'],
                                                       tab_off_approach=False,
                                                       verify_sso=False)
            if not status:
                self.log.info("On disabling SAML app login fails, TC completed successfully")
            else:
                raise Exception("On disabling SAML app login succeeded")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.saml_obj.delete_app()

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

