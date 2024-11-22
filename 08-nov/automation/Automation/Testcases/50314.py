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

    run()           --  Executes test case

    get_validate_key_dict()    --  Forms the dictionary to be passed during validation of the
                                    identity server app

    tear down()     --  Clears all the entities created

"""

import base64
import random
import string
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.Common.cvbrowser import BrowserFactory,Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance of SAML test case"""
    test_step = TestStep()

    def __init__(self):
        """
            Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "SAML Login/ Logout"
        self.browser = None
        self.saml_obj = None
        self.utils = None
        self.admin_console = None
        self.smtp_address = None
        self.webconsole_url = None
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
                         "Company name": None,
                         "idp metadata location": None,
                         "AD machine IP": None,
                         "AD machine name": None,
                         "AD administrator": None,
                         "AD admin password": None,
                         "SAML user": None,
                         "SAML password": None,
                         "Redirect rule": None
                         }

    def init_tc(self):
        """Function to initialize the variables"""

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

        self.navigator_obj = self.admin_console.navigator
        self.saml_obj = IdentityServersMain(self.admin_console, self.commcell, self.csdb)
        self.saml_obj.app_name = "test_50314"
        self.webconsole_url = "https://" + self.commcell.webconsole_hostname + ":443/webconsole"
        self.saml_obj.redirect_rule = self.tcinputs['Redirect rule']
        self.adfs_app_name = "ADFS_check"
        self.web_url = "https://" + self.commcell.webconsole_hostname + "/webconsole"
        self.smtp_address = self.saml_obj.app_name[0] + "." + ''.join(
            random.choices(string.ascii_lowercase, k=3))

    @test_step
    def add_saml_app(self):
        """ Adds SAML app """
        self.navigator_obj.navigate_to_identity_servers()
        self.saml_obj.create_saml_app(self.tcinputs['idp metadata location'],
                                      self.smtp_address,
                                      self.webconsole_url,
                                      True,
                                      self.tcinputs['Company name'],
                                      jks_file_path=None,
                                      alias_name=None,
                                      keystore_password=None, key_password=None,
                                      auto_generate_key=True)
        self.file_path = self.saml_obj.download_spmetadata(download_dir=self.utils.get_temp_dir())

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

        company_name = self.tcinputs['Company name']

        if self.saml_obj.redirect_rule is None:

            _query = "select attrVal from UMDSProviderProp where componentNameId =" \
                     "(select id from UMDSProviders where domainName = '{0}')and " \
                     "attrName = 'Email Domain'".format(self.tcinputs['Company name'])
            self.csdb.execute(_query)
            smtp = self.csdb.fetch_one_row()[0]
            redirect_rule = {company_name: smtp,
                             self.saml_obj.app_name: self.smtp_address}
        else:
            redirect_rule = self.saml_obj.redirect_rule

        validate_key_dict = {"AppName": self.saml_obj.app_name,
                             "Auto user create flag": True,
                             "Default user group": company_name + r"\Tenant Users",
                             "Company name": self.tcinputs['Company name'],
                             "SP entity ID": self.webconsole_url,
                             "SSO URL": sso_url,
                             "Associations": None,
                             "Redirect rule": redirect_rule,
                             "Attribute mapping": self.saml_obj.attribute_mapping}
        return validate_key_dict

    def run(self):
        """Executes test case"""
        try:
            self.init_tc()
            self.add_saml_app()
            self.saml_obj.validate_saml_app(self.get_validate_key_dict())
            self.saml_obj.edit_trust_party_adfs(self.saml_obj.app_name,
                                                self.tcinputs['AD machine IP'],
                                                self.tcinputs['AD administrator'],
                                                self.tcinputs['AD admin password'],
                                                self.file_path)
            self.admin_console.logout()

            self.saml_obj.initiate_saml_login(False, self.tcinputs['AD machine name'],
                                              self.web_url, self.adfs_app_name,
                                              self.tcinputs['SAML user'],
                                              self.tcinputs['SAML password'],
                                              tab_off_approach=True,
                                              verify_sso=False)

            self.saml_obj.initiate_saml_logout(False, self.tcinputs['AD machine name'],
                                               self.web_url,
                                               verify_single_logout=False)

            self.saml_obj.initiate_saml_login(False, self.tcinputs['AD machine name'],
                                              self.web_url, self.adfs_app_name,
                                              self.tcinputs['SAML user'],
                                              self.tcinputs['SAML password'],
                                              tab_off_approach=False,
                                              verify_sso=False)

            self.saml_obj.initiate_saml_logout(False, self.tcinputs['AD machine name'],
                                               self.web_url,
                                               verify_single_logout=False)

            self.saml_obj.initiate_saml_login(True, self.tcinputs['AD machine name'],
                                              self.web_url, self.adfs_app_name,
                                              self.tcinputs['SAML user'],
                                              self.tcinputs['SAML password'],
                                              tab_off_approach=False,
                                              verify_sso=True)

            self.saml_obj.initiate_saml_logout(True, self.tcinputs['AD machine name'],
                                               self.web_url,
                                               verify_single_logout=True)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.saml_obj.edit_trust_party_adfs(self.saml_obj.app_name,
                                                self.tcinputs['AD machine IP'],
                                                self.tcinputs['AD administrator'],
                                                self.tcinputs['AD admin password'],
                                                operation="Delete")
            self.saml_obj.delete_app()


        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)