"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase:   Class for validating associations of SAML app

Input Example:

    "testCases": {
            "62592": {
                    "idpmetadata_xml_path": string,
                    "domain_name": string,
                    "netbios_name": string,
                    "ADAdmin": string,
                    "ADAdminPass": string,
                    "ADUserEmail": user email present in AD, with username equal to prefix of its email
                    "ADUser2Email": second user email present in AD, with username equal to prefix of its email
                }
"""
import time

from AutomationUtils import constants
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.samlhelper import SamlHelperMain


class TestCase(CVTestCase):
    """ Testcase to validate associations of SAML app"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "SAML associations validation"
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

        self.samlhelper = None
        self.orghelper = None
        self.grouphelper = None
        self.userhelper = None

        self.email_suffix = None
        self.email_suffix2 = None
        self.company_name = None
        self.saml_appname = None
        self.local_group = None
        self.local_user_email = None
        self.company_user_email = None
        self.AD_user_email = None
        self.local_user2_email = None
        self.local_user11_email = None
        self.company_user2_email = None
        self.AD_user2_email = None
        self.local_user22_email = None

        self.tcinputs = {
            "idpmetadata_xml_path": None,
            "domain_name": None,
            "netbios_name": None,
            "ADAdmin": None,
            "ADAdminPass": None,
            "ADUserEmail": None,
            "ADUser2Email": None

        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:

            self.samlhelper = SamlHelperMain(self.commcell)
            self.orghelper = OrganizationHelper(self.commcell)
            self.grouphelper = UsergroupHelper(self.commcell)
            self.userhelper = UserHelper(self.commcell)

            self.email_suffix = 'suffix1' + str(datetime.today().microsecond) + '.in'
            self.email_suffix2 = 'suffix2' + str(datetime.today().microsecond) + '.org'
            self.company_name = 'company' + str(datetime.today().microsecond)
            self.saml_appname = 'samlapp' + str(datetime.today().microsecond)
            self.local_group = 'group' + str(datetime.today().microsecond)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_saml_app(self):
        """Create a Commcell SAML app"""
        self.samlhelper.create_saml_app(self.saml_appname, self.name,
                                        self.tcinputs['idpmetadata_xml_path'],
                                        True,
                                        [self.email_suffix])
    @test_step
    def create_company(self):
        """Create a company"""
        self.orghelper.create(self.company_name, company_alias=self.company_name)

    @test_step
    def create_AD(self):
        """Create a Commcell AD"""
        self.commcell.domains.add(self.tcinputs['domain_name'],
                                  self.tcinputs['netbios_name'],
                                  self.tcinputs['ADAdmin'],
                                  self.tcinputs['ADAdminPass'],
                                  enable_sso=False,
                                  company_id=0)
    @test_step
    def create_usergroup(self):
        """Create a Commcell User Group"""
        self.grouphelper.create_usergroup(self.local_group)

    @test_step
    def create_users(self):
        """Create Company user, AD user, local user for user group, local user with smtp of saml app"""
        # create company user

        self.company_user_email = 'user' + str(datetime.today().microsecond) + '@' \
                                  + str(datetime.today().microsecond) + '.com'
        self.userhelper.create_user(self.company_name + '\\' + self.company_user_email.split('@')[0],
                                    email=self.company_user_email,
                                    password=self.userhelper.password_generator(3, 12))

        # create external / AD user
        self.AD_user_email = self.tcinputs['ADUserEmail']
        self.userhelper.create_user(self.AD_user_email.split('@')[0],
                                    email=self.AD_user_email,
                                    domain=self.tcinputs['netbios_name'])

        # create a local user and Add him to local user group
        self.local_user_email = 'user' + str(datetime.today().microsecond) + '@' \
                                + str(datetime.today().microsecond) + '.com'
        self.userhelper.create_user(self.local_user_email.split('@')[0],
                                    email=self.local_user_email,
                                    password=self.userhelper.password_generator(3, 12),
                                    local_usergroups=[self.local_group])

        # create a local user with matching smtp
        self.local_user2_email = 'user' + str(datetime.today().microsecond) + '@' + self.email_suffix
        self.userhelper.create_user(self.local_user2_email.split('@')[0],
                                    email=self.local_user2_email,
                                    password=self.userhelper.password_generator(3, 12))
    @test_step
    def verify_auth_id(self, users):
        """Verify auth id of given users"""
        for user in users:
            if user[1] == 0:
                try:
                    self.samlhelper.validate_authid(user[0])
                    raise Exception("Invalid Authid")
                except Exception as e:
                    if str(e) == "Invalid Authid":
                        raise Exception("Unexpected Authid for this user, raising exception")

            else:
                self.samlhelper.validate_authid(user[0])

    @test_step
    def add_associations(self):
        """Add email, company, AD and user group association to saml app"""
        self.samlhelper.modify_associations('emailSuffixes', self.email_suffix2, True)
        time.sleep(5)
        self.samlhelper.modify_associations('companies', self.company_name, True)
        time.sleep(5)
        self.samlhelper.modify_associations('domains', self.tcinputs['netbios_name'], True)
        time.sleep(5)
        self.samlhelper.modify_associations('userGroups', self.local_group, True)
        time.sleep(5)

    @test_step
    def create_users2(self):
        """Create Company user, AD user, local user for user group, local user with new smtp of saml app"""
        # create company user
        self.company_user2_email = 'user' + str(datetime.today().microsecond) + '@' \
                                   + str(datetime.today().microsecond) + '.com'
        self.userhelper.create_user(self.company_name + '\\' + self.company_user2_email.split('@')[0],
                                    email=self.company_user2_email,
                                    password=self.userhelper.password_generator(3, 12))

        # create external / AD user
        self.AD_user2_email = self.tcinputs['ADUser2Email']
        self.userhelper.create_user(self.AD_user2_email.split('@')[0],
                                    email=self.AD_user2_email,
                                    domain=self.tcinputs['netbios_name'])

        # create a local user and Add him to local user group
        self.local_user11_email = 'user' + str(datetime.today().microsecond) + '@' \
                                  + str(datetime.today().microsecond) + '.com'
        self.userhelper.create_user(self.local_user11_email.split('@')[0],
                                    email=self.local_user11_email,
                                    password=self.userhelper.password_generator(3, 12),
                                    local_usergroups=[self.local_group])

        # create a local user with matching smtp
        self.local_user22_email = 'user' + str(datetime.today().microsecond) + '@' + self.email_suffix2
        self.userhelper.create_user(self.local_user22_email.split('@')[0],
                                    email=self.local_user22_email,
                                    password=self.userhelper.password_generator(3, 12))

    @test_step
    def validate_redirect_url(self, users):
        """Validate redirect url of all 8 users"""
        for user in users:
            self.log.info('VAlidate redirect url of user [%s]', user[0])
            redirecturl = self.samlhelper.samluser_redirect_url(user[0])
            if user[1] == 0:
                if redirecturl is not None:
                    raise Exception("Invalid redirect url, user [%s], redirect url [%s]", user[0], redirecturl)
            elif redirecturl != self.samlhelper.samlapp_redirect_url():
                raise Exception("Invalid redirect url, user [%s], redirect url [%s]", user[0], redirecturl)
            self.log.info('valid redirect url')

    @test_step
    def remove_associations(self):
        """Remove email, compnay, AD and user group association from saml app"""
        self.samlhelper.modify_associations('emailSuffixes', self.email_suffix, False)
        time.sleep(5)
        self.samlhelper.modify_associations('emailSuffixes', self.email_suffix2, False)
        time.sleep(5)
        self.samlhelper.modify_associations('companies', self.company_name, False)
        time.sleep(5)
        self.samlhelper.modify_associations('domains', self.tcinputs['netbios_name'], False)
        time.sleep(5)
        self.samlhelper.modify_associations('userGroups', self.local_group, False)
        time.sleep(5)

    def run(self):
        self.init_tc()
        try:
            self.create_saml_app()
            self.create_company()
            self.create_AD()
            self.create_usergroup()
            self.create_users()

            self.verify_auth_id([
                [self.company_user_email, 0],
                [self.AD_user_email, 0],
                [self.local_user_email, 0],
                [self.local_user2_email, 1]
            ])

            self.add_associations()
            self.create_users2()

            self.verify_auth_id([
                [self.company_user_email, 1],
                [self.AD_user_email, 1],
                [self.local_user_email, 1],
                [self.local_user2_email, 1],
                [self.company_user2_email, 1],
                [self.AD_user2_email, 1],
                [self.local_user11_email, 1],
                [self.local_user22_email, 1]
            ])

            self.validate_redirect_url([
                [self.company_user_email, 1],
                [self.AD_user_email, 1],
                [self.local_user_email, 1],
                [self.local_user2_email, 1],
                [self.company_user2_email, 1],
                [self.AD_user2_email, 1],
                [self.local_user11_email, 1],
                [self.local_user22_email, 1]
            ])
            self.remove_associations()

            self.verify_auth_id([
                [self.company_user_email, 0],
                [self.AD_user_email, 0],
                [self.local_user_email, 0],
                [self.local_user2_email, 0],
                [self.company_user2_email, 0],
                [self.AD_user2_email, 0],
                [self.local_user11_email, 0],
                [self.local_user22_email, 0]
            ])
        except Exception as e:
            self.log.info('Failed with error %s', str(e))
            self.result_string = str(e)
            self.status = constants.FAILED

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.samlhelper.delete_saml_app()
            self.commcell.domains.delete(self.tcinputs['netbios_name'])
            self.commcell.organizations.delete(self.company_name)
            time.sleep(5)
            self.grouphelper.delete_usergroup(self.local_group,
                                              new_user=self.inputJSONnode['commcell']['commcellUsername'])
            users = [self.local_user_email, self.local_user2_email, self.local_user11_email, self.local_user22_email]
            for user in users:
                self.userhelper.delete_user(user.split('@')[0], new_user=self.inputJSONnode['commcell']['commcellUsername'])

        finally:
            pass
