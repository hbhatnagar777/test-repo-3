# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from AutomationUtils import logger, config
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep, handle_testcase_exception
from Server.mongodb_helper import MongoDBHelper
from Server.organizationhelper import OrganizationHelper
from AutomationUtils.options_selector import OptionsSelector
from Server.Security.userhelper import UserHelper
from datetime import datetime
from cvpysdk.security.user import User
from cvpysdk.organization import Organizations


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "MSP admin and TA login using username and email"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.mongodbhelper = None
        self.users_login_details = []
        self.utility = None
        self.userhelper = None
        self.organizations = None
        self.config_json = None
        self.result_string = "Successful"

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()
        self.mongodbhelper = MongoDBHelper(self._commcell, self._commcell.commserv_client.client_hostname)
        self.utility = OptionsSelector(self._commcell)
        self.userhelper = UserHelper(self._commcell)
        self.organizations = Organizations(self._commcell)
        self.config_json = config.get_config()

    @test_step
    def _users_to_be_validated(self, username, password, email=None, domain=None):
        """Adding users to be validated"""
        user_template = {
            "username": username,
            "password": password,
            "email": email,
            "domain": domain
        }
        self.users_login_details.append(user_template)

    @test_step
    def user_login(self, login_with='username'):
        """Login with email/username"""
        failed_login_counter = 0
        failed_users_list = []
        for user in self.users_login_details:
            redundant_emails_found = False
            try:
                if login_with.lower() == 'username':
                    username = ((user.get('domain') + "\\" + user.get('username'))
                                if user.get('domain') else user.get('username'))
                elif login_with.lower() == 'email':
                    username = user.get('email')
                    record = self.utility.exec_commserv_query(query="select count(email) as count from umusers"
                                                                    " where email='{0}' and enabled=1"
                                                                    " group by email".format(username))
                    redundant_emails_found = int(record[0][0]) > 1
                else:
                    raise Exception('please pass validate param')
                # Rest API Login
                self.userhelper.gui_login(self._commcell.commserv_hostname, username, user.get('password'))

            except Exception as exp:
                # if login fails for one user, catch the exception and continue login validations for other users
                if str(exp) in ("Invalid Username or Password", "User has no credentials on this CommServe",
                                "Response was not success") and not redundant_emails_found:
                    failed_login_counter = failed_login_counter + 1
                    failed_users_list.append(username)
                else:
                    raise Exception(exp)
        if failed_login_counter:
            raise Exception('Login failed for {0} users, users List = {1} please check logs'
                            ' for more info'.format(failed_login_counter, failed_users_list))

    def run(self):
        """Execution method for this test case"""
        try:
            self._users_to_be_validated(username=self.inputJSONnode['commcell']["commcellUsername"],
                                        password=self.inputJSONnode['commcell']["commcellPassword"],
                                        email=User(self._commcell,
                                                   self.inputJSONnode['commcell']["commcellUsername"]).email)
            # create company/organization
            timestamp = datetime.strftime(datetime.now(), '%H%M%S')
            company_name = 'company{0}'.format(timestamp)
            company_email = company_name + "@company.com"
            self.log.info("creating company {0}".format(company_name))
            company_object = self.organizations.add(
                name=company_name, email=company_email, contact_name=company_name, company_alias=company_name)
            self.log.info("company {0} got created successfully".format(company_name))
            organization_helper = OrganizationHelper(self._commcell, company_name)
            tenant_admin_name = company_name + "\\" + company_name + "2"
            new_password = self.config_json.ADMIN_PASSWORD
            organization_helper.add_new_company_user_and_make_tenant_admin(tenant_admin_name, new_password)
            user_obj = User(self._commcell, user_name=tenant_admin_name)
            self._users_to_be_validated(username=company_name+"2",
                                        password=new_password,
                                        email=user_obj.email,
                                        domain=company_name)
            if self.mongodbhelper.validate_service_status():
                self.user_login()
                self.user_login(login_with='email')
            else:
                raise Exception('Mongo Service is not up')
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.log.info('Cleaning up entities...')
            if company_object:
                # deleting company, will delete company associated entities like directories, groups etc
                self.log.info('deactivating and deleting company {0}'.format(company_object.name))
                self.organizations.delete(company_object.name)