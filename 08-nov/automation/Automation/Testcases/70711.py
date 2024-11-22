# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Login/Logout for local user, SAML user, admin user, tenant admin user, ad user

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    commandcenter_login()        --  Login verification for admin console

    run()                       --  Contains the core testcase logic, and it is the one executed

    tear_down()                 --  Clean up entities

"""

import time
from datetime import datetime
from urllib.parse import quote
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Security.samlhelper import SamlHelperMain
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper
from Web.Common.exceptions import CVWebAutomationException, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Testcase json example:

            "70711":
                {
            "domain_name": None,
            "netbios_name": None,
            "domain_username": None,
            "domain_password": None,
            "ad_user": None,
            "ad_password": None,
            "ad_email": None
            "IDP URL": None,
            "idp_metadata_xml_path": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "SAML user email": None,
            "SAML user pwd": None,
                }

        """

        super(TestCase, self).__init__()

        self.name = "Login/Logout for local user, SAML user, admin user, tenant admin user, ad user"
        self.result_string = "Successful"
        self.organization_helper = None
        self.user_helper = None
        self.identity_server_helper = None
        self.saml_helper = None
        self.saml_appname = None
        self.local_user_email = None
        self.company_name = None
        self.tenant_admin_user =None
        self.machine = None
        self.download_directory = None
        self.cert = None

        self.tcinputs = {
            "domain_name": None,
            "netbios_name": None,
            "domain_username": None,
            "domain_password": None,
            "ad_user": None,
            "ad_password": None,
            "ad_email": None,
            "IDP URL": None,
            "idp_metadata_xml_path": None,
            "IDP admin username": None,
            "IDP admin password": None,
            "appname": None,
            "SAML user email": None,
            "SAML user pwd": None,
        }

    def setup(self):
        """Initializes pre-requisites for test case"""

        self.user_helper = UserHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)
        self.saml_helper = SamlHelperMain(self.commcell)
        self.saml_appname = 'saml_app' + str(datetime.today().microsecond)
        self.local_user_name = 'local_user' + str(datetime.today().microsecond)
        self.local_user_email = self.local_user_name + '@commvault.com'
        self.company_name = 'company70711' + str(datetime.today().microsecond)
        self.tenant_admin_user = 'tenant_admin_user' + str(datetime.today().microsecond)

    @test_step
    def commandcenter_login(self, username, password):
        """*********Command Center Login*********"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        try:
            login_obj = AdminConsole(browser, self.commcell.webconsole_hostname)
            login_obj.login(username, password)
            login_obj.check_error_message()
            self.log.info("Successfully logged in Command Center")
            login_obj.navigator.navigate_to_dashboard()
            login_obj.wait_for_completion()
            login_obj.navigator.navigate_to_virtualization()
            login_obj.wait_for_completion()
            AdminConsole.logout(login_obj)
        except CVWebAutomationException as exp:
            Browser.close_silently(browser)
            raise Exception(exp)
        Browser.close_silently(browser)

    @test_step
    def download_certificate(self, admin_console):
        """Download certificate from Command Center

        Args:
            admin_console (object)  --  AdminConsole class object

        Raises:
            CVTestStepFailure:  If certificate download fails
        """
        encoded = quote(self.saml_appname)
        download_url = "https://" + self.commcell.webconsole_hostname + \
                       "/commandcenter/downloadSPCertificate.do?appName=" + encoded
        parent_handle = admin_console.driver.current_url
        admin_console.driver.execute_script("window.open('" + download_url + "');")
        filename = self.saml_appname + ".cer"
        self.cert = self.download_directory + "\\" + filename
        time.sleep(5)
        if not self.machine.check_file_exists(self.cert):
            raise CVTestStepFailure("Certificate download failed")
        self.log.info("Certificate downloaded successfully")
        admin_console.browser.switch_to_tab(parent_handle)

    @test_step
    def saml_login(self):
        """Login to Command Center using SAML"""
        browser = BrowserFactory().create_browser_object()
        self.machine = Machine()
        self.download_directory = self.machine.join_path(constants.TEMP_DIR, str(self.id))
        self.machine.create_directory(self.download_directory, force_create=True)
        self.log.info("Setting Download directory to {0}".format(self.download_directory))
        browser.set_downloads_dir(self.download_directory)
        browser.open()
        try:
            admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
            command_center_url = "https://" + self.commcell.webconsole_hostname + "/commandcenter"

            admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                self.inputJSONnode['commcell']['commcellPassword'])
            self.identity_server_helper = IdentityServersMain(admin_console, self.commcell, self.csdb)
            self.download_certificate(admin_console)

            admin_console.logout()

            self.log.info("*********Login to Okta and edit general settings*********")
            (self.identity_server_helper.
             login_to_okta_and_edit_general_settings(okta_url=self.tcinputs['IDP URL'],
                                                     username=self.tcinputs['IDP admin username'],
                                                     pwd=self.tcinputs['IDP admin password'],
                                                     app_name=self.tcinputs['appname'],
                                                     sso_url=self.saml_helper.spmetadata['singleSignOnUrl'],
                                                     sp_entity_id=self.saml_helper.spmetadata['entityId'],
                                                     slo=True,
                                                     single_logout_url=self.saml_helper.spmetadata['singleLogoutUrl'],
                                                     sp_issuer=self.saml_helper.spmetadata['entityId'],
                                                     certificate=self.cert
                                                     )
             )
            time.sleep(2)
            self.identity_server_helper.logout_from_okta()
            self.log.info("*********Initiating SAML login*********")
            status = self.identity_server_helper.initiate_saml_login_with_okta(command_center_url,
                                                                               hostname=self.commcell.webconsole_hostname,
                                                                               okta_url=self.tcinputs['IDP URL'],
                                                                               username=self.tcinputs['SAML user email'],
                                                                               pwd=self.tcinputs['SAML user pwd'],
                                                                               app_name=self.tcinputs['appname'],
                                                                               is_idp_initiated=False)
            if not status:
                raise Exception("SAML login failed")
            self.log.info("Successfully logged in Command Center")
            admin_console.navigator.navigate_to_dashboard()
            admin_console.wait_for_completion()
            admin_console.navigator.navigate_to_virtualization()
            admin_console.wait_for_completion()
            AdminConsole.logout(admin_console)

        except Exception as exp:
            raise Exception(exp)
        finally:
            Browser.close_silently(browser)

    def run(self):

        try:
            self.log.info("*********Creating local user*********")
            password = self.user_helper.password_generator(complexity_level=3, min_length=12)
            self.user_helper.create_user(user_name=self.local_user_name, email=self.local_user_email,
                                         full_name='local_user', password=password)
            self.log.info("*********Creating Company and Tenant Admin user*********")
            self.organization_helper.create(name=self.company_name, company_alias=self.company_name)
            self.organization_helper = OrganizationHelper(self.commcell, company=self.company_name)
            self.organization_helper.add_new_company_user_and_make_tenant_admin(self.tenant_admin_user, password)
            self.log.info("*********Creating Active Directory and Ad User*********")
            self.commcell.domains.add(domain_name=self.tcinputs['domain_name'],
                                      netbios_name=self.tcinputs['netbios_name'],
                                      user_name=self.tcinputs['domain_username'],
                                      password=self.tcinputs['domain_password'],
                                      company_id=0)
            self.user_helper.create_user(user_name=self.tcinputs['ad_user'], email=self.tcinputs['ad_email'],
                                         domain=self.tcinputs['netbios_name'],
                                         local_usergroups=['master'])
            self.log.info("*********Creating SAML App*********")
            self.saml_helper.create_saml_app(appname=self.saml_appname,
                                             description="Login/Logout for SAML user",
                                             idpmetadata_xml_path=self.tcinputs['idp_metadata_xml_path'],
                                             auto_generate_sp_metadata=True,
                                             email_suffixes=[self.tcinputs['email_suffix']])

            self.commandcenter_login('admin', self.inputJSONnode['commcell']["commcellPassword"])
            self.commandcenter_login(self.local_user_name, password)
            self.commandcenter_login(self.company_name + '\\' + self.tenant_admin_user, password)
            self.commandcenter_login(self.tcinputs['netbios_name']+'\\'+self.tcinputs['ad_user'],
                                     self.tcinputs['ad_password'])
            self.saml_login()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To clean up the test case environment created"""
        self.user_helper.cleanup_users(self.local_user_name)
        self.organization_helper.cleanup_orgs(self.company_name)
        if self.commcell.domains.has_domain(self.tcinputs['netbios_name']):
            self.commcell.domains.delete(self.tcinputs['netbios_name'])
        if self.cert:
            self.machine.delete_file(self.cert)
        self.saml_helper.delete_saml_app()
        self.user_helper.delete_user(self.tcinputs['SAML user email'],
                                     new_user=self.inputJSONnode['commcell']['commcellUsername'])
