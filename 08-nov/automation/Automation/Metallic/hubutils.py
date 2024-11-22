import json
import time
from cvpysdk.commcell import Commcell
from cvpysdk.organization import Organizations
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.config import get_config
from Server.RestAPI.restapihelper import RESTAPIHelper
from base64 import b64encode


class HubManagement(object):
    """
    This is class for All hub related util operations.
    Current methods:
        Create_tenant
        Reset User password

    Future Methods:
        Delete Tenant
    """
    def __init__(self, testcase_instance, commcell,
                 code=None):
        """
        This is the init method of the class.
        :param commcell:            (str)       Commcell name / url can either be metallic names like
                                                m6.metallic.io or m6 or the actual CS name.
        :param testcase_instance:   (object)    Instance of the testcase.
        :param code:                (str)       OPTIONAL. auth code for the metallic API.
        """
        self.commcell_object = None
        self.commcell_hostname = None
        self.workflow = None
        self.tenant_user_name = None
        self.tenant_name = None
        self.api_inputs = None
        self.code = code
        self.tenant_id = None
        self.tenant_domain = None
        self.qsdk_token = None
        self.tenant_ag_id = None
        self.tenant_ug_id = None
        self.cs_reachable = True
        self.ring_name = commcell
        self.tenant_properties = None
        # Start of temporary workaround because of m1/m6 ring name mix up in db
        self.original_ring_name = self.ring_name
        if self.ring_name.lower() in ("m6.metallic.io", "m6"):
            self.ring_name = "m1.metallic.io"
        # End of temp code

        if "." in self.ring_name:
            self.ring_short_name = self.ring_name.split(".")[0]
        else:
            self.ring_short_name = self.ring_name


        config = get_config()
        if self.code is None:
            self.code = config.Metallic.code
        self.cs_mapping = {item.split(":")[0].strip(): item.split(":")[1].strip()
                           for item in config.Metallic.cs_mapping.split(",")}
        self.hub_signup_url = config.Metallic.signup_url
        self.cs_suffix = config.Metallic.cs_suffix
        self.workflow_user = config.Metallic.workflow_user
        self.workflow_pass = config.Metallic.workflow_password
        self.tenant_password = config.Metallic.tenant_password
        self.reset_workflow_name = config.Metallic.reset_password_workflow
        self.delete_workflow_name = config.Metallic.manage_company_workflow
        self._testcase = testcase_instance
        self.log = self._testcase.log
        self.validate_cs_name(commcell)
        self.commcell_object = Commcell(self.ring_name, self.workflow_user, self.workflow_pass)
        # / Added as workaround untill the metallic case in handled
        self.commcell_object._is_linux_commserv = False
        self._testcase.commcell._is_linux_commserv = False
        # / end of workaround
        self._restapi = RESTAPIHelper()


    def create_tenant(self, company_name, email, first_name="test_fname", last_name="test_lname",
                      phone_number="0000000000", country="United States"):
        """
        This method is for creating a new tenant
        :param company_name:    (str) Name of the company
        :param email:           (str) Email of the user
        :param first_name:      (str) First name
        :param last_name:       (str) Last name
        :param phone_number:    (str) Phone number
        :param country:         (str) Country name for Azure . Optional
        :return:                (str) Username for the user
        """
        tenant_json = {
            "company": company_name,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "phone": phone_number,
            "country": country,
            'mKTOFormOptInCheckBox': 'false'
        }
        self.tenant_user_name = r"%s\%s" % (company_name, email.split("@")[0])
        self.tenant_name = company_name
        self.user_name = r"%s\%s" % (company_name, email.split("@")[0])
        self.tenant_domain = email.split("@")[1]

        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        if self.code in (None, ''):
            raise Exception('CS operation not supported.')
        response = self.commcell_object._cvpysdk_object.make_request("POST",
                                                                     url=self.hub_signup_url+"?code=" + self.code +
                                                                         "&commcell=" + self.commcell,
                                                                     payload=tenant_json,
                                                                     headers=headers
                                                                     )
        if not response[0]:
            self.log.error(response[1])
            raise Exception('Error executing signup api')

        if int(response[1].status_code) != 200:
            self.log.error(response[1])
            raise Exception('Error running user signup api')

        api_output = json.loads(str(response[1].text))
        if api_output["error_code"]:
            self.log.error(api_output['error_message'])
            raise Exception('Error executing signup api')
        self.log.info('Tenant successfully created: %s' % self.tenant_name)
        time.sleep(120)
        self.reset_user_password(self.tenant_user_name)
        self.log.info('Successfully reset password for the tenant user: %s' % self.tenant_user_name)
        if email.split("@")[0].lower() != 'uat':
            self.log.info('Creating UAT user')
            self.create_tenant_user('uat', 'Tenant Admin', 'uat@%s' % self.tenant_name)

        return self.tenant_user_name

    def reset_user_password(self, cs_user):
        """
        This method is used to Reset the password for a Metallic user
        :param cs_user:     (str)   Name of the user
        :return:            Nothing
        """
        self.workflow = WorkflowHelper(self._testcase, self.reset_workflow_name,
                                       deploy=False, commcell=self.commcell_object)
        self.workflow.execute(
                    {
                     "Username": cs_user
                     })
        self.validate_user_password(cs_user)

    def validate_cs_name(self, cs_name):
        """
        This method is used to convert metallic names to actual CS names
        m6 or m6.metallic.io will be converted to its CS hostname value
        :param cs_name:     (str)   Name of the CS
        :return:            (str)   Resolvable CS FQDN
        """
        if cs_name.lower().rstrip('.metallic.io') in list(self.cs_mapping.keys()):
            new_cs_name = self.cs_mapping[cs_name.lower().rstrip('.metallic.io')]
            self.log.info('Using the CS name %s for %s ' % (new_cs_name, cs_name))
            self.commcell = new_cs_name
            self.commcell_hostname = new_cs_name+self.cs_suffix
        else:
            self.commcell = cs_name
            self.commcell_hostname = cs_name

    def get_cs_hostname(self):
        """
        This method returns the resolvable CS name
        :return: (str)  CS name
        """
        return self.commcell_hostname

    def manage_tenant(self, operation):
        """
        This method is used to manage a tenant
        :param operation:     (str)   operation to be performed DeactivateCompany | DeleteCompany
        :return: Nothing
        """
        self.workflow = WorkflowHelper(self._testcase, self.delete_workflow_name,
                                       deploy=False, commcell=self.commcell_object)
        try:
            self.workflow.execute(
                {
                    "Operation": operation,
                    "companyName": self.tenant_name
                })
            self.log.info("%s successful: %s" % (operation, self.tenant_name))
        except Exception as err:
            self.log.error('Errors encountered while processing %s for tenant %s' % (operation, self.tenant_name))
            self.log.error(str(err))

    def deactivate_tenant(self, tenant_name=None):
        """
        This method is used to deactivate a tenant
        :param tenant_name:     (str)   Name of the tenant
        :return: Nothing
        """

        if tenant_name is not None:
            self.tenant_name = tenant_name

        if self.tenant_name in (None, '', 'None'):
            self.log.error('Tenant name not provided. %s skipped. %s' % ('Delete', self.tenant_name))
            return
        self.manage_tenant('DeactivateCompany')

    def cleanup_tenants(self, filter=None):
        """
        cleanup tenants based on the filter key provided
        :param filter:  (str)   filter key that should be present in tenant name
        """
        if filter is None:
            self.log.info("No Filter provided, no tenants are cleared")
            return
        orgs = Organizations(self.commcell_object)
        tenants = orgs.all_organizations
        for tenant in tenants:
            if filter.lower() in tenant:
                self.log.info(f"cleaning up tenant :{tenant}")
                self.deactivate_tenant(tenant)
                self.delete_tenant(tenant)

    def delete_tenant(self, tenant_name=None):
        """
        This method is used to deactivate a tenant
        :param tenant_name:     (str)   Name of the tenant
        :return: Nothing
        """
        if tenant_name is not None:
            self.tenant_name = tenant_name

        if self.tenant_name in (None, '', 'None'):
            self.log.error('Tenant name not provided. %s skipped. %s' % ('Delete', self.tenant_name))
            return
        self.manage_tenant('DeleteCompany')
        try:
            self.get_company_details()
            self.log.error("Unable to delete Tenant. "
                           "Please contact the MSP admin with the error. Company: %s" % self.tenant_name)
        except Exception as err:
            if 'Username/Password are incorrect' in str(err):
                self.log.info('Validated that company is deleted')
            else:
                self.log.warning(str(err))
                self.log.warning("Please contact the MSP admin with the above warning. Company: %s" % self.tenant_name)

    def login_user(self, user_name=None):
        """
        This method uses the tenant user or the user provided to do rest api login to the CS
        It uses password listed in the config for created tenant admin or the user provided
        :param user_name: Optional. Str -> username for login
        :return:            Nothing
        """
        if user_name is None:
            self.log.error('No user provided for login')
            raise Exception
        login_url = "https://%s/webconsole/api/Login" % self.original_ring_name
        base64pwd = b64encode(self.tenant_password.encode()).decode()
        login_body_json = {
            "mode": "webconsole",
            "domain": "",
            "username": user_name,
            "password": base64pwd,
            "commserver": ""
        }
        login_headers = {'Content-Type': 'application/json',
                         'Accept': 'application/json'}

        response = self.commcell_object._cvpysdk_object.make_request("POST",
                                                                     url=login_url,
                                                                     payload=login_body_json,
                                                                     headers=login_headers
                                                                     )
        if not response[0]:
            raise Exception('Error logging in with user: %s' % str(response[1]))

        if int(response[1].status_code) != 200:
            raise Exception('Error logging in with user: %s' % str(response[1]))

        if response[1].json()['errList']:
            if response[1].json()['errList'][0]['errorCode'] not in (0, '0'):
                raise Exception(response[1].json()['errList'][0]['errLogMessage'])

        self.log.info('User %s logged in successfully' % user_name)
        self.qsdk_token = response[1].json()['token']

    def logout_user(self, user_name):
        """
        This method logs out the logged in user. Uses the QSDK token that was set by login method.
        :return: Nothing
        """
        logout_url = "https://%s/webconsole/api/Logout" % self.original_ring_name
        logout_headers = {'Content-Type': 'application/json', 'Authtoken': self.qsdk_token, 'Accept': 'application/json'}

        response = self.commcell_object._cvpysdk_object.make_request("POST",
                                                                     url=logout_url,
                                                                     payload={},
                                                                     headers=logout_headers
                                                                     )
        if not response[0]:
            raise Exception('Error logging out with user: %s' % str(response[1]))
        if int(response[1].status_code) != 200:
            raise Exception('Error logging out with user: %s' % str(response[1]))
        if response[1].text == 'User logged out':
            self.log.info('User %s logged out successfully' % user_name)
        else:
            self.log.warning(response[1].text)
        try:
            if response[1].json()['errList']:
                if response[1].json()['errList'][0]['errorCode'] not in (0, '0'):
                    self.log.error(response[1].json()['errList'][0]['errLogMessage'])
        except:
            pass
        self.qsdk_token = None

    def validate_user_password(self, user_name=None):
        """
        This method validated the user/password combination by doing a REST api login
        :param user_name:   (str)   Username
        :return:    Nothing
        """
        if user_name is None:
            self.log.error('No user provided')
            raise Exception('Please provide valid username to verify')
        self.log.info('We will now validate the user %s against the new password %s'
                      % (user_name, self.tenant_password))
        self.login_user(user_name)
        self.logout_user(user_name)

    def create_user_token(self, user_name=None):
        """
        This method can be used to create user qsdk token for the tenant admin
        :param user_name:   (str)   Username (optional)
        :return: Nothing
        """
        if self.qsdk_token is None:
            self.login_user(user_name)

    def destroy_qsdk_token(self, user_name):
        """
        This method can be called to destroy existing user session
        :return:
        """
        if self.qsdk_token is not None:
            self.logout_user(user_name)

    def get_tenant_id(self):
        """
        This method is used to get the tenant id for the created tenant
        :return: Nothing
        """
        if self.tenant_id is None:
            self.create_user_token(self.tenant_user_name)
            get_company_list = "https://%s/webconsole/api/Organization" % self.original_ring_name

            headers = {'Authtoken': self.qsdk_token, 'Accept': 'application/json'}
            response = self.commcell_object._cvpysdk_object.make_request("GET",
                                                                         url=get_company_list,
                                                                         payload={},
                                                                         headers=headers
                                                                         )
            if not response[0]:
                self.log.error(response[1])
                raise Exception('Error getting tenant list')
            if int(response[1].status_code) != 200:
                self.log.error(response[1])
                raise Exception('Error with request for getting tenant list')
            try:
                if response[1].json()['errList']:
                    if response[1].json()['errList'][0]['errorCode'] not in (0, '0'):
                        self.log.error(response[1].json()['errList'][0]['errLogMessage'])
            except:
                pass
            self.tenant_id = response[1].json()['providers'][0]['shortName']['id']

    def get_company_details(self):
        self.create_user_token(self.tenant_user_name)
        get_company_details_url = "https://%s/webconsole/api/Organization/%d" % (self.original_ring_name, self.tenant_id)
        headers = {'Authtoken': self.qsdk_token, 'Accept': 'application/json'}
        response = self.commcell_object._cvpysdk_object.make_request("GET",
                                                                     url=get_company_details_url,
                                                                     payload={},
                                                                     headers=headers
                                                                     )
        if not response[0]:
            self.log.error(response[1])
            raise Exception('Error getting tenant list')
        if int(response[1].status_code) != 200:
            self.log.error(response[1])
            raise Exception('Error with request for getting tenant list')
        try:
            if response[1].json()['errList']:
                if response[1].json()['errList'][0]['errorCode'] not in (0, '0'):
                    self.log.error(response[1].json()['errList'][0]['errLogMessage'])
        except:
            pass
        self.tenant_properties = response[1].json()['organizationInfo']['organizationProperties']
        self.destroy_qsdk_token(self.tenant_user_name)

    def create_tenant_user(self, user_name, user_group='Tenant User', email=None, full_name=None):
        """
        This method is used to create a tenant user using the qsdk token of the tenant admin.
        :param user_name:   (str)   USERNAME
        :param user_group:  (str)   User group type ( "Tenant Admin" / "Tenant User" )
        :param email:       (str)   EMAIL OF THE USER   (optional)
        :param full_name:   (str)   Full name of user (Optional)
        :return:            (str)   Created company username
        """
        if email is None:
            email = user_name+'@'+self.tenant_domain
        if full_name is None:
            full_name = user_name
        self.create_user_token(self.tenant_user_name)
        self.get_tenant_id()
        self.get_user_groups()
        if user_group.lower() == 'tenant user':
            user_group_name = self.tenant_name + '\\Tenant Users'
            group_id = self.tenant_ug_id
        elif user_group.lower() == 'tenant admin':
            user_group_name = self.tenant_name + '\\Tenant Admin'
            group_id = self.tenant_ag_id
        else:
            self.log.error('Incorrect user type provided.')
            self.log.info(str(user_group))
            raise Exception

        create_user = "https://%s/webconsole/api/User" % self.original_ring_name
        create_user_headers = {'Authtoken': self.qsdk_token, 'Accept': 'application/json', 'Content-Type': 'application/json'}
        base64pwd = b64encode(self.tenant_password.encode()).decode()
        create_user_body = {
                  "users": [
                    {
                        "email": email,
                        "systemGeneratePassword": False,
                        "password": base64pwd,
                        "fullName": full_name,
                        "enableUser": True,
                        "associatedExternalUserGroups": [
                            {
                                "groupId": group_id,
                                "externalGroupName": user_group_name
                            }
                        ],
                        "userEntity": {
                            "userName": user_name
                          }
                    }
                  ]
                }
        response = self.commcell_object._cvpysdk_object.make_request("POST",
                                                                     url=create_user,
                                                                     payload=create_user_body,
                                                                     headers=create_user_headers
                                                                     )
        if not response[0]:
            self.log.error(response[1])
            raise Exception('Error executing create User method')
        if int(response[1].status_code) != 200:
            self.log.error(response[1])
            raise Exception('Create user method not successful')
        try:
            if response[1].json()['response'][0]['errorCode'] != 0:
                raise Exception
            created_user = response[1].json()['response'][0]['entity']['userName']
            self.log.info('Created user %s' % created_user)
            self.destroy_qsdk_token(self.tenant_user_name)
            self.validate_user_password(user_name=created_user)
            return created_user

        except:
            if response[1].json()['response'][0]['errorString']:
                self.log.error('Error creating user %s. Error: %s'
                               % (user_name, response[1].json()['response'][0]['errorString']))
            raise Exception('Error creating user %s' % user_name)

    def get_user_groups(self):
        """
        This method is used to query the ring to get tenant user groups and sets the admin and user group id variables
        :return: Nothing
        """
        if self.tenant_ag_id is None:
            self.create_user_token(self.tenant_user_name)
            get_user_group_list = "https://%s/webconsole/api/UserGroup" % self.original_ring_name

            headers = {'Authtoken': self.qsdk_token, 'Accept': 'application/json'}
            response = self.commcell_object._cvpysdk_object.make_request("GET",
                                                                         url=get_user_group_list,
                                                                         payload={
                                                                             "parentProvider/providerId": self.tenant_id
                                                                         },
                                                                         headers=headers
                                                                         )
            if not response[0]:
                self.log.error(response[1])
                raise Exception('Error getting User group list')
            if int(response[1].status_code) != 200:
                self.log.error(response[1])
                raise Exception('Error with request for getting user group list')
            try:
                if response[1].json()['errList']:
                    if response[1].json()['errList'][0]['errorCode'] not in (0, '0'):
                        self.log.error(response[1].json()['errList'][0]['errLogMessage'])
            except:
                pass
            group_count = len(response[1].json()['userGroups'])
            for i in range(0, group_count):
                if 'tenant admin' in response[1].json()['userGroups'][i]['userGroupEntity']['userGroupName'].lower():
                    self.tenant_ag_id = response[1].json()['userGroups'][i]['userGroupEntity']['userGroupId']
                elif 'tenant users' in response[1].json()['userGroups'][i]['userGroupEntity']['userGroupName'].lower():
                    self.tenant_ug_id = response[1].json()['userGroups'][i]['userGroupEntity']['userGroupId']

    def delete_companies_with_prefix(self, prefix):
        """Deletes the companies with given prefix
            Args:
                prefix(str):  prefix of the companies which need to be deleted.
        """
        companies_list = self.commcell_object.organizations.all_organizations
        companies_list_with_given_prefix = [key for key, value in companies_list.items() if
                                            key.startswith(prefix.lower())]
        if len(companies_list_with_given_prefix) == 0:
            self.log.info("No companies found with given prefix")
        for company in companies_list_with_given_prefix:
            organization = self.commcell_object.organizations.get(company)
            user_groups_in_company = organization.user_groups
            users_in_user_group = self.commcell_object.user_groups.get(user_groups_in_company[0]).users
            self.tenant_user_name = users_in_user_group[0]
            self.deactivate_tenant(company)
            self.delete_tenant(company)
        self.log.info('Companies deletion with given prefix is completed.')
