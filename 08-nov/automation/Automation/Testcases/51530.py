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

    get_validate_key_dict()    --  Forms the dictionary to be passed during validation of the
                                    identity server app

    tear down()     --  Clears all the entities created
"""
import random
import string
import base64
from Web.Common.cvbrowser import BrowserFactory, Browser
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance of SAML test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SAML adminconsole acceptance case"
        self.browser = None
        self.webconsole_url = None
        self.smtp_address = None
        self.saml_obj = None
        self.new_saml_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            "OKTA IDP Metadata Path": None,
            "idp metadata location": None,
            "jks file path": None,
            "Keystore Alias name": None,
            "Key password": None,
            "Keystore password": None
        }

    @test_step
    def init_tc(self):
        """function to initialize the variables"""

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator_obj = self.admin_console.navigator

        self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
        self.new_saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)

        self.saml_obj.app_name = "test_51530"
        self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
        self.smtp_address = self.saml_obj.app_name[0] + "." + ''.join(
            random.choices(string.ascii_lowercase, k=3))
        self.saml_obj.redirect_rule = {"test_51530": self.smtp_address}

    @test_step
    def add_saml_app(self):
        """ Adds SAML app """
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['OKTA IDP Metadata Path'],
                                      self.smtp_address,
                                      self.webconsole_url,
                                      False,
                                      None,
                                      jks_file_path=None,
                                      alias_name=None,
                                      keystore_password=None, key_password=None,
                                      auto_generate_key=True)

    @test_step
    def modify_redirectrule_and_validate(self):
        """ Modify the redirect rule and validate it """
        modified_redirect_rule = {"modified": "check.loc"}
        self.saml_obj.edit_saml_rule_or_mappings(self.saml_obj.app_name,
                                                 redirect_rule=modified_redirect_rule)
        validate_key_dict = {"Redirect rule": modified_redirect_rule}
        self.saml_obj.validate_saml_app(validate_key_dict)

    @test_step
    def modify_attribute_mappings_and_validate(self):
        """ Modify the Attribute mappings and validate it """
        mappings = {"modified_mapping": "test"}
        self.saml_obj.edit_saml_rule_or_mappings(self.saml_obj.app_name, mappings=mappings)
        validate_key_dict = {"Attribute mapping": mappings}
        self.saml_obj.validate_saml_app(validate_key_dict)

    @test_step
    def add_samlapp_with_substring_of_existing_app(self):
        """ Create SAML app with a substring of the already created app """
        self.navigator_obj.navigate_to_identity_servers()
        self.new_saml_obj.app_name = self.saml_obj.app_name[0]
        self.new_saml_obj.create_saml_app(self.tcinputs['OKTA IDP Metadata Path'],
                                          self.saml_obj.app_name[0] + "." + ''.join(
                                              random.choices(string.ascii_lowercase, k=3)),
                                          self.webconsole_url,
                                          False, None,
                                          jks_file_path=None, alias_name=None,
                                          keystore_password=None, key_password=None,
                                          auto_generate_key=True)

    @test_step
    def get_validate_key_dict(self):
        """
        Forms the dictionary to be passed during validation of the
                                    identity server app

        returns:

         validate_key_dict  (dict)   :dictionary of identity server attributes
        """
        _query = "select appKey from App_ThirdPartyApp where appname = '{0}' and " \
                 "appType = 2".format(self.saml_obj.app_name)
        self.csdb.execute(_query)
        app_key = self.csdb.fetch_one_row()
        if app_key:
            saml_app_key = base64.b64encode(bytes(app_key[0], 'utf-8'))
        else:
            raise Exception("No such app exists")

        sso_url = self.webconsole_url + "/samlAcsIdpInitCallback.do?samlAppKey=" + \
            str(saml_app_key.decode("utf-8"))

        validate_key_dict = {"AppName": self.saml_obj.app_name,
                             "Auto user create flag": True,
                             "Default user group": 'Not set',
                             "Company name": None,
                             "SP entity ID": self.webconsole_url,
                             "SSO URL": sso_url,
                             "Associations": None,
                             "Redirect rule": self.saml_obj.redirect_rule,
                             "Attribute mapping": self.saml_obj.attribute_mapping}
        return validate_key_dict

    def run(self):
        """Executes test case"""
        try:
            self.init_tc()
            self.add_saml_app()
            self.saml_obj.validate_saml_app(self.get_validate_key_dict())
            self.modify_redirectrule_and_validate()
            self.modify_attribute_mappings_and_validate()

            self.saml_obj.edit_saml_idp(self.saml_obj.app_name,
                                        idp_meta_path=self.tcinputs['idp metadata location'],
                                        web_console_url=self.webconsole_url,
                                        jks_file_path=self.tcinputs['jks file path'],
                                        alias_name=self.tcinputs['Keystore Alias name'],
                                        keystore_password=self.tcinputs['Keystore password'],
                                        key_password=self.tcinputs['Key password'])

            self.add_samlapp_with_substring_of_existing_app()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:

            self.saml_obj.delete_app()
            self.new_saml_obj.delete_app()

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)