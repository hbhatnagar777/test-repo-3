# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on companies or subscriptions page.

Class:

    CompanyMain()

Functions:

    add_new_company()               :   Calls method add_company from companies class

    delete_existing_company()       :   Calls methods to de-associate plans and delete company
                                        from CompanyDetails & Company class

    validate_company()               :   Validates the values displayed for company against
                                        values provided as input

    __set_default_values_if_none()  :   provides defaults for values provided to compare
                                        with values displayed

    edit_company_details()          :   Edits company tiles from company details page

    edit_plans()                    :   Method to edit plans associated to the company

    add_test_user()                 :   Method to add users to given company

Class

    MSPHelper()

Functions:

    assert_comparison()             -- Performs a comparison of the value with the expected value

    parse_email_reset()             -- Parse Email and resets password

    login_as_tenant()               -- Login as a tenant admin

    validate_template()             -- Validate the email template used against the received email

    __get_company_usergroup()       -- Returns user groups related to a company

    __get_company_users()           -- Returns user groups related to a company

    validate_usergroup()            -- Validates if usergroup set in UI and backend are same

    validate_users()                -- Validates if users shown in UI and backend are same

    validate_security_associations()-- Validates the security associations of company

    validate_operators()            -- Validates if the operator shown in admin console and backend are same

    validate_general_tile()         -- Validate is the properties shown in general tile in UI and the backend are same

    validate_plans()                -- Validates if plans shown in UI and backend are same

    validate_contacts()             -- Validates if contacts shown in UI and backend are same

    validate_email_settings()       -- Validates if emails shown in UI and backend are same

    validate_external_auth()        -- Validates if external authentication shown in UI and backend are same

    validate_file_exception()       -- Validates if file exceptions shown in UI and backend are same

    validate_client_groups()        -- Validates if client groups shown in UI and backend are same

    validate_alerts()               -- Validates if alerts associated to company shown in Alerts page and backend are same

    validate_navigation_preferences()-- Validates the navigation preferences

    __get_company_details()         -- Sets company details

    validate_default_configurations()-- Method to validate if the default config are set correctly

    validate_supported_solutions()  -- Method to validate the functionality for supported solutions on company page

    validate_infrastructure_type()  -- Method to validate the functionality for infrastructure type on company page

    validate_plan_functionality()   -- Method to validate the functionality for Plan on company page

    validate_security_functionality() -- Method to validate the functionality for Security tile on company page

    validate_operator_functionality() -- Method to validate the functionality for Operator tile on company page

    validate_allow_owner_data_encryption() -- Method to validate the functionality for
                                              allow owners to enable data encryption

    company_entities()              -- Method to return basic entities associated to a company
"""

import datetime
import time
from bs4 import BeautifulSoup
import copy
import collections

from selenium.webdriver.common.by import By

from AutomationUtils.config import get_config
from AutomationUtils import logger
from Server.Security.userhelper import UserHelper
from Server.organizationhelper import OrganizationHelper
from Web.AdminConsole.AdminConsolePages.AlertDefinitions import AlertDefinitions
from Web.AdminConsole.AdminConsolePages.Alerts import Alerts
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.EmailTemplates import EmailTemplates
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import SubclientOverview
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from cvpysdk.organization import Organization
from AutomationUtils.mail_box import EmailSearchFilter
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.Setup.core_setup import Setup
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Components.panel import PanelInfo
from Web.Common.exceptions import CVWebAutomationException


company_tile = [
            'usergroup',
            'users',
            'security_associations',
            'operators',
            'email_settings',
            'general_tile',
            'client_groups',
            'alerts',
            'file_exception',
            'plans',
            'contacts',
            'plans',
            'navigation_preferences'
        ]


class CompanyMain:
    """
        Helper for companies/subscriptions page
    """

    def __init__(self, admin_console, csdb=None):
        """
            Initializes the company helper module

            Args:
                admin_console  (object)   --  AdminConsole class object

                csdb        (Object)   --  CommServe database object
        """

        self.csdb = csdb
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__companies = Companies(self.__admin_console)
        self.__company_details = CompanyDetails(self.__admin_console)
        self.__users = Users(self.__admin_console)
        self.__table = Table(self.__admin_console)

        self.log = logger.get_log()
        self._company_name = "TestCompany"+" "+str(datetime.datetime.today())
        self._email = "xyz@commvault.com"
        self._contact_name = "xyz"
        self._enable_custom_domain = True
        self._plans = None
        self._company_alias = self._company_name.translate({ord(c): None for c in ":,-.' '"})
        self._smtp = "commvault.com"
        self._tfa = {'default':'OFF'}
        self._user_name = ""
        self._primary_site = self._company_name+"."+self._smtp
        self._mail_template = None
        self._edited = False
        self._secondary_sites = "defgh.com, ghijk.com"
        self._sender_name = 'abc'
        self._sender_email = 'abc@commvault.com'
        self._general_settings = {'company_alias': 'Test Alias',
                                  'smtp': 'comm.com',
                                  'authcode': 'ON',
                                  'UPN': 'ON',
                                  '2-factor': 'ON',
                                  'reseller_mode': 'ON',
                                  'data_encryption': 'ON',
                                  'auto_discover_applications': 'ON',
                                  'infra_type': 'Own storage',
                                  'supported_solutions': ['File server',
                                                          'Archiving',
                                                          'Cloud apps',
                                                          'Sharepoint',
                                                          'Active directory',
                                                          'Office 365']}
        self._server_default_plan = None
        self._laptop_default_plan = None
        self._operators = {'add': {self._company_alias+r'\Tenant Operator': 'Tenant Operator'},
                           'remove': None}
        self._file_exceptions = {'windows_path': [r'C:\TestFolder', r'C:\TestFolder1'],
                                 'unix_path': ['root/TestFolder', 'root/TestFolder1']}
        self._active_directory = None
        self._job_start_time = 'System default'
        self._company_filters = 'ON'
        self._supported_solutions = ['File server',
                                     'Virtualization',
                                     'Laptop',
                                     'Databases',
                                     'Exchange',
                                     'Office 365']

    @property
    def company_name(self):
        """ Get Company name"""
        return self._company_name

    @company_name.setter
    def company_name(self, value):
        """ Set Company name"""
        self._company_name = value

    @property
    def email(self):
        """ Get Company email"""
        return self._email

    @email.setter
    def email(self, value):
        """ Set Company name"""
        self._email = value

    @property
    def contact_name(self):
        """ Get Company contact name"""
        return self._contact_name

    @contact_name.setter
    def contact_name(self, value):
        """ Set Company contact name"""
        self._contact_name = value

    @property
    def plans(self):
        """ Get plans"""
        return self._plans

    @plans.setter
    def plans(self, value):
        """ Set plans"""
        self._plans = value

    @property
    def company_alias(self):
        """ Get Company alias"""
        return self._company_alias

    @company_alias.setter
    def company_alias(self, value):
        """ Set Company alias"""
        self._company_alias = value

    @property
    def smtp(self):
        """ Get SMTP"""
        return self._smtp

    @smtp.setter
    def smtp(self, value):
        """ Set SMTP"""
        self._smtp = value

    @property
    def primary_site(self):
        """ Get primary domain"""
        return self._primary_site

    @primary_site.setter
    def primary_site(self, value):
        """ Set primary domain"""
        self._primary_site = value

    @property
    def mail_template(self):
        """ Get primary domain"""
        return self._mail_template

    @mail_template.setter
    def mail_template(self, value):
        """ Set primary domain"""
        self._mail_template = value

    @property
    def enable_custom_domain(self):
        """ Get flag for custom domain"""
        return self._enable_custom_domain

    @enable_custom_domain.setter
    def enable_custom_domain(self, value):
        """ Set flag for custom domain"""
        self._enable_custom_domain = value

    @property
    def secondary_sites(self):
        """ Get values for secondary domains"""
        return self._secondary_sites

    @secondary_sites.setter
    def secondary_sites(self, value):
        """ Set values for secondary domains"""
        self._secondary_sites = value

    @property
    def sender_name(self):
        """ Get value for sender name"""
        return self._sender_name

    @sender_name.setter
    def sender_name(self, value):
        """ Set value for sender name"""
        self._sender_name = value

    @property
    def sender_email(self):
        """ Get value for sender name"""
        return self._sender_email

    @sender_email.setter
    def sender_email(self, value):
        """ Set value for sender name"""
        self._sender_email = value

    @property
    def general_settings(self):
        """ Get values for general settings"""
        return self._general_settings

    @general_settings.setter
    def general_settings(self, value):
        """ Set values for general settings"""
        self._general_settings = value

    @property
    def server_default_plan(self):
        """ Get value for default server plan for company"""
        return self._server_default_plan

    @server_default_plan.setter
    def server_default_plan(self, value):
        """ Set value for default server plan for company"""
        self._server_default_plan = value

    @property
    def laptop_default_plan(self):
        """ Get value for default laptop plan for company"""
        return self._laptop_default_plan

    @laptop_default_plan.setter
    def laptop_default_plan(self, value):
        """ Set value for default laptop plan for company"""
        self._laptop_default_plan = value

    @property
    def operators(self):
        """ Get operators for company"""
        return self._operators

    @operators.setter
    def operators(self, value):
        """ Set operators for company"""
        self._operators = value

    @property
    def file_exceptions(self):
        """ Get file_exceptions for company"""
        return self._file_exceptions

    @file_exceptions.setter
    def file_exceptions(self, value):
        """ Set file_exceptions for company"""
        self._file_exceptions = value

    @property
    def active_directory(self):
        """ Get active_directory values for company"""
        return self._active_directory

    @active_directory.setter
    def active_directory(self, value):
        """ Set active_directory values for company"""
        self._active_directory = value

    @property
    def company_filters(self):
        """ Get company_filters for file exceptions"""
        return self._company_filters

    @company_filters.setter
    def company_filters(self, value):
        """ Set company_filters for file exceptions"""
        self._company_filters = value

    @property
    def job_start_time(self):
        """ Get job_start_time value"""
        return self._job_start_time

    @job_start_time.setter
    def job_start_time(self, value):
        """ Set job_start_time value"""
        self._job_start_time = value

    @property
    def supported_solutions(self):
        """ Get supported_solutions value"""
        return self._supported_solutions

    @supported_solutions.setter
    def supported_solutions(self, value):
        """ Set supported_solutions value"""
        self._supported_solutions = value

    def add_new_company(self,
                        company_name=None,
                        email=None,
                        contact_name=None,
                        plans=None,
                        company_alias=None,
                        smtp=None,
                        mail_template=None,
                        primary_site=None):
        """ Method to call base methods to navigate and create a company """

        self.__navigator.navigate_to_companies()
        if company_name:
            self.company_name = company_name

        if email:
            self.email = email

        if contact_name:
            self.contact_name = contact_name

        if plans:
            self.plans = plans

        if company_alias:
            self.company_alias = company_alias

        if smtp:
            self.smtp = smtp

        if mail_template:
            self.mail_template = mail_template

        if primary_site:
            self.primary_site = primary_site

        self.__companies.add_company(self.company_name,
                                     self.email,
                                     self.contact_name,
                                     self.plans,
                                     self.company_alias,
                                     self.smtp,
                                     self.mail_template,
                                     self.primary_site)

    def delete_existing_company(self):
        """ Method to call base methods to perform delete operation for given company """
        self.__navigator.navigate_to_companies()
        self.__companies.deactivate_and_delete_company(self.company_name)

    def validate_company(self):
        """ Method to validate displayed values against given input values """
        self.__navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        displayed_val = self.__company_details.company_info()

        if self._edited:
            validation_dict = self.__set_default_values_if_none("Post-edit")
        else:
            validation_dict = self.__set_default_values_if_none("Pre-edit")

        for key, value in validation_dict.items():
            if isinstance(value, list):
                self.log.info('Entity given val %s', value)
                if (key == 'Plans' and
                        displayed_val[key] != "None" and
                        validation_dict[key] != "None"):
                    count = 0
                    validation_dict[key] = sorted(validation_dict[key])
                    max_val = max(len(displayed_val[key]), len(validation_dict[key]))
                    for plan in sorted(displayed_val[key]):
                        if count < max_val:
                            plan_name, sep, rest = plan.partition('Default')
                            if str(plan_name).strip() == validation_dict[key][count]:
                                self.log.info("{0} displayed for {1} matches"
                                              .format(plan, key))
                            else:
                                exp = "{0} displayed for {1} does not match \
                                with {2}".format(key, plan, validation_dict[key][count])
                                self.log.exception(exp)
                                raise Exception(exp)
                        else:
                            break
                        count += 1
                elif (key == 'Operators'and
                      displayed_val[key] != "None" and
                      validation_dict[key] != "None"):
                    count = 0
                    validation_dict[key] = sorted(validation_dict[key])
                    max_val = max(len(displayed_val[key]), len(validation_dict[key]))
                    for operator in sorted(displayed_val[key]):
                        if count < max_val:
                            if '(' in operator:
                                operator = operator.rsplit('(', 1)[1].rsplit(')', 1)[0]

                            if str(operator).strip() == validation_dict[key][count]:
                                self.log.info("{0} displayed for {1} matches"
                                              .format(operator, key))
                            else:
                                exp = "{0} displayed for {1} does not match with {2}"\
                                    .format(key, operator, validation_dict[key][count])
                                self.log.exception(exp)
                                raise Exception(exp)
                        else:
                            break
                        count += 1
                else:
                    if set(displayed_val[key]) == set(validation_dict[key]):
                        self.log.info("{0} displayed for {1} matches with {2} given"
                                      .format(displayed_val[key], key, validation_dict[key]))
                    else:
                        exp = "{0} displayed for {1} does not match with {2} given".format(
                            displayed_val[key], key, validation_dict[key])
                        self.log.exception(exp)
                        raise Exception(exp)

            elif isinstance(value, str):
                if displayed_val[key] == validation_dict[key]:
                    self.log.info("{0} displayed for {1} matches with {2} given"
                                  .format(displayed_val[key], key, validation_dict[key]))
                else:
                    exp = "{0} displayed for {1} does not match with {2} given ".format(
                        displayed_val[key], key, validation_dict[key])
                    self.log.exception(exp)
                    raise Exception(exp)

            else:
                self.log.info('Entity given val :{0}'.format(value))
                for item, value_dict in value.items():
                    d_val = displayed_val[key][item]
                    key_val = validation_dict[key][item]
                    if d_val == key_val:
                        self.log.info("{0} values match" .format(item))
                    else:
                        exp = "{0} displayed for {1} does not match with {2} given".format(
                            d_val, item, key_val)
                        self.log.exception(exp)
                        raise Exception(exp)

    def __set_default_values_if_none(self, get_validation_dict):
        """ Method to create dictionary with given inputs for comparison with displayed values """

        default_comp_values = {"Requires authcode for installation": "OFF",
                               "Use UPN instead of e-mail": "OFF",
                               "Enable two factor authentication": "OFF",
                               "Secondary domain name": "Not set",
                               "Navigation preferences": ['Navigation customization'],
                               "Email settings": [],
                               "External authentication": [],
                               "data_encryption": "ON",
                               "infra_type": "Rented storage",
                               "file_exceptions": []}

        _query = "select attrVal from App_CompanyProp where componentNameId=\
            (select id from UMDSProviders where serviceType=5 and domainName=\
            '{0}') and attrName='Creation Time'".format(self.company_alias)
        self.csdb.execute(_query)
        unix_company_time = self.csdb.fetch_one_row()
        creation_time = datetime.datetime.fromtimestamp(int(unix_company_time[0]))
        comp_creation_time = creation_time.strftime('%b %#d, %#I:%M:%S %p')

        file_exception_windows = ""
        file_exception_unix = ""
        i = 0
        for exception in self.file_exceptions['windows_path']:
            i += 1
            if i == 1:
                file_exception_windows = file_exception_windows + str(exception)
            else:
                file_exception_windows = file_exception_windows + '\n' + str(exception)

        i = 0
        for exception in self.file_exceptions['unix_path']:
            i += 1
            if i == 1:
                file_exception_unix = file_exception_unix + str(exception)
            else:
                file_exception_unix = file_exception_unix + '\n' + str(exception)

        if self.primary_site:
            primary_site = self.primary_site
        else:
            primary_site = 'Not set'

        if self.secondary_sites:
            secondary_sites = self.secondary_sites
        else:
            secondary_sites = 'Not set'

        if get_validation_dict == "Pre-edit":
            validation_dict = {
                'CompanyName': str(self.company_name),
                'Contacts': {'Contact name': str(self.contact_name)},
                'Plans': self.plans,
                'Email settings': default_comp_values["Email settings"],
                'General': {'Company created on': comp_creation_time,
                            'Company alias': self.company_alias,
                            'Associated SMTP': self.smtp,
                            'Requires authcode for installation':
                                default_comp_values["Requires authcode for installation"],
                            'Use UPN instead of e-mail': default_comp_values["Use UPN instead of e-mail"],
                            'Enable two factor authentication':
                                default_comp_values["Enable two factor authentication"],
                            'Allow owners to enable data encryption': default_comp_values['data_encryption'],
                            'Infrastructure type': default_comp_values['infra_type'],
                            'Supported solutions': self.supported_solutions},
                'Navigation preferences': default_comp_values["Navigation preferences"],
                'Sites': {'Primary site name': primary_site,
                          'Secondary site name': default_comp_values['Secondary domain name']},
                'Operators': self.operators['add'],
                'External authentication': default_comp_values['External authentication'],
                'File exceptions': default_comp_values['file_exceptions']
            }
        else:
            validation_dict = {
                'CompanyName': self.company_name,
                'Contacts': {'Contact name': self.contact_name},
                'Plans': self.plans,
                'Email settings': {'Sender name': self.sender_name,
                                   'Sender email': self.sender_email},
                'General': {'Company created on': comp_creation_time,
                            'Company alias': self.company_alias,
                            'Associated SMTP': self.general_settings['smtp'],
                            'Requires authcode for installation': self.general_settings['authcode'],
                            'Use UPN instead of e-mail': self.general_settings['UPN'],
                            'Enable two factor authentication': self.general_settings['2-factor'],
                            'Allow owners to enable data encryption': self.general_settings['data_encryption'],
                            'Infrastructure type': self.general_settings['infra_type'],
                            'Supported solutions': self.general_settings['supported_solutions']},
                'Navigation preferences': default_comp_values["Navigation preferences"],
                'Sites': {'Primary site name': primary_site,
                          'Secondary site name': secondary_sites},
                'Operators': self.operators['add'],
                'External authentication': [self.active_directory['netbios_name']],
                'File exceptions': {'Use company filters on all subclients': self.company_filters,
                                    'Windows': file_exception_windows,
                                    'Unix': file_exception_unix}
            }
        return validation_dict

    def edit_company_details(self):
        """ Method to call base methods for editing company properties from company details page """

        secondary_sites = self.secondary_sites.split(',')
        contact_names = self.contact_name.split(',')
        self.add_test_user()
        self.__navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_details.edit_general_settings(self.general_settings)
        self.__company_details.edit_contacts(contact_names)
        self.__company_details.edit_sender_email(self.sender_name, self.sender_email)
        self.__company_details.edit_external_authentication(self.active_directory['netbios_name'],
                                                            self.active_directory['username'],
                                                            self.active_directory['password'],
                                                            self.active_directory['domain_name'],
                                                            self.active_directory['proxy_client'])
        self.__company_details.edit_sites(self.primary_site, secondary_sites)
        self.__company_details.edit_company_plans(self.plans,
                                                  self.server_default_plan,
                                                  self.laptop_default_plan)
        self.__company_details.edit_company_file_exceptions(self.file_exceptions)
        self.__company_details.edit_company_operators(self.operators)
        self._edited = True

    def edit_plans(self):
        """Method to edit plans associated to a company from company details page"""

        self.__navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_details.edit_company_plans(self.plans,
                                                  self.server_default_plan,
                                                  self.laptop_default_plan)
        self._edited = True

    def add_test_user(self):
        """Method to add test user for verification"""

        self.__navigator.navigate_to_users()
        contacts = [str(i) for i in self.contact_name.split(',')]
        for contact in contacts:
            self.__users.add_local_user(email=contact+'@commvault.com',
                                        groups=[self.company_alias + r'\Tenant Admin'],
                                        username=contact,
                                        name=contact,
                                        password="######")


class MSPHelper(CompanyMain):
    """
        Helper function for MSP pages
    """

    def __init__(self, admin_console, commcell, mail_box=None, csdb=None):
        """
            Initializes the MSP helper module

        Args:
            admin_console (object): Admin console object

            commcell (object): A commcell object

            mail_box (object): mail_box for getting the mail
        """

        super(MSPHelper, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.csdb = csdb
        self.__navigator = admin_console.navigator
        self.__companies = Companies(self.__admin_console)
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__panel = PanelInfo(self.__admin_console)
        self.__template_helper = EmailTemplates(self.__admin_console)
        self.__users = Users(self.__admin_console)
        self.__comcell = commcell
        self.__mail_box = mail_box
        self.__subclient = SubclientOverview(self.__admin_console)
        self.__setup = Setup(self.__admin_console)
        self.__company_details = CompanyDetails(self.__admin_console)
        self.__user = Users(self.__admin_console)
        self._is_MSP_admin = self.__is_msp_admin()
        self.__company_helper = CompanyDetails(self.__admin_console)
        self._company_details = None
        self.__organization = None
        self._company_name = None
        self.__config = get_config().MSPCompany
        self.fssubclient = Subclient(self.__admin_console)
        self.org_helper = None
        self.user_helper = UserHelper(commcell)

    @property
    def company_details(self):
        """Returns company details property"""
        if not self._company_details:
            self.__get_company_details()

        return self._company_details

    @company_details.setter
    def company_details(self, value):
        """Sets company details property"""
        self._company_details = value

    @property
    def organization(self):
        """Returns organization object"""
        if not self.__organization:
            self.__organization = Organization(self.__comcell, self._company_name)

        return self.__organization

    @property
    def company_details(self):
        """Returns company details property"""
        if not self._company_details:
            self.__get_company_details()

        return self._company_details

    @company_details.setter
    def company_details(self, value):
        """Sets company details property"""
        self._company_details = value

    @property
    def organization(self):
        """Returns organization object"""
        if not self.__organization:
            self.__organization = Organization(self.__comcell, self._company_name)

        return self.__organization

    def __is_msp_admin(self):
        logged_user = self.__comcell.users.get(self.__comcell._user)
        user_group = logged_user.associated_usergroups or logged_user.associated_external_usergroups
        if 'Tenant Admin' in user_group:
            return False

        return True

    @staticmethod
    def assert_comparison(value, expected):
        """Performs a comparison of the value with the expected value"""
        if collections.Counter(value) != collections.Counter(expected):
            raise CVTestStepFailure(
                f"The value: {value} does not match the expected value {expected}")

    def parse_email_reset(self, password, username, l_user_password):
        """ Parse Email and resets password """

        # Reset password via email won't work now since CAPTCHA is added we don't have any way of exposing the correct
        # response. So we are using a hack to directly changing the password from pysdk

        self.__comcell.users.get(username).update_user_password(password, l_user_password)

        # search_query = EmailSearchFilter(f"Your {self.company_name} account is available")
        # links = self.__mail_box.get_mail_links(search_query)
        # self.__admin_console.driver.get(links["here"])
        # self.__admin_console.fill_form_by_id("pwd", password)
        # self.__admin_console.fill_form_by_id("confirmPassword", password)
        # self.__admin_console.click_button("Set password")
        # self.__admin_console.wait_for_completion()

    def login_as_tenant(self, username, password):
        """Login as a tenant admin"""
        self.__admin_console.login(username, password)

    def validate_template(self):
        """Validate the email template used against the received email"""
        self.__navigator.navigate_to_email_templates()
        self.__template_helper.open_mail_template('Add company')
        editor_contents = self.__template_helper.get_editor_contents()
        editor_contents['subject'] = "Subject : " + editor_contents['subject']
        editor_contents['subject'] = \
            editor_contents['subject'].replace("$TENANT_COMPANY_NAME$", self._company_name)

        body_token_list = ['$EMAIL_HEADER$', '$RECIPIENT_NAME$', '$TENANT_COMPANY_NAME$',
                           '$USERNAME$', '$CHANGE_PASSWORD_LINK_EXPIRATION$',
                           '$ADMINISTRATOR_NAME$', '$EMAIL_FOOTER$']
        token_replacement_list = ['', self.contact_name, self.company_name,
                                  self.email, '30 minutes', 'Administrator', '']

        for token, string in zip(body_token_list, token_replacement_list):
            editor_contents['body'] = editor_contents['body'].replace(token, string)

        search_query = EmailSearchFilter(f"Your {self._company_name} account is available")
        mail = self.__mail_box.get_mail(search_query)

        body_html = mail['Body'][0].decode('utf-8').replace('<br><br>', '  ')
        soup = BeautifulSoup(body_html, "html.parser")
        body = soup.body.text
        mail_dict = {'subject': 'Subject : ' + mail['Subject'],
                     'body': ' ' + body}
        self.assert_comparison(editor_contents, mail_dict)

    @staticmethod
    def __convert_infrastructure_to_id(infra_id):
        """ Convert id to infrastructure name

        Args:
            infra_id (int) : id for a infrastructure type

        Returns:
            infrastructure (string) : Infrastructure name
        """
        infra_map = {
            0: "Rented storage",
            1: "Own storage",
            2: "Rented and own storage"
        }
        return infra_map[infra_id]

    @staticmethod
    def __convert_job_start_time(job_start_time):
        """Convert job start time to readable format"""
        time = ""
        if type(job_start_time) == int:
            hour = str((int(job_start_time / 3600) % 12))
            if len(hour) == 1:
                hour = '0' + hour

            time += hour
            time += ":"
            min = str(int((job_start_time % 3600) / 60))
            if len(min) == 1:
                min = '0' + min

            time += min
            if job_start_time / (60 * 12 * 60) > 1:
                time += ' PM'
            else:
                time += ' AM'

            if job_start_time == 0:
                return "12:00 AM"

            return time

        return job_start_time

    @staticmethod
    def __convert_solution_list_to_id(soln_id, list=True):
        """ Converts solutions id to list of supported solutions

        Args:
            soln_id (int) : solution id from API

        Returns:
            supported_solns (list) : list of supported solutions
        """
        solution_dict = {
            1: "File server",
            2: "Virtualization",
            4: "Laptop",
            8: "Databases",
            16: "Exchange",
            32: "Archiving",
            64: "Cloud apps",
            512: "Sharepoint",
            1024: "Activate",
            2048: "Active_directory",
            4096: "Office 365",
            8192: "Bigdata apps",
            32769: "G Suite",
            65536: "Salesforce",
            131072: "Replication",
            262144: "Kubernetes",
            524288: "Object storage",
            1048576: "Epic EHR systems",
            2097152: "Dynamics 365"
        }

        supported_soln = []
        for key in solution_dict:
            if key & soln_id == key:
                supported_soln.append(solution_dict[key])

        if not list:
            supported_sln_str = ""
            for sln in supported_soln:
                supported_sln_str += f"{sln}, "

            return supported_sln_str[:-2]

        return supported_soln

    def __get_company_usergroup(self):
        """ Returns user groups related to a company """
        self.__navigator.navigate_to_user_groups()
        userg_table = Rtable(self.__admin_console, "User groups")
        if self._is_MSP_admin:
            userg_table.select_company(self.company_name)

        return userg_table.get_column_data("Group name", True)

    def __get_company_users(self):
        """ Returns user groups related to a company """
        self.__navigator.navigate_to_users()
        userg_table = Rtable(self.__admin_console, "Users")
        if self._is_MSP_admin:
            userg_table.select_company(self.company_name)

        return userg_table.get_column_data("User name", True)
    
    def __get_company_server_groups(self):
        """ Returns server groups related to a company"""
        self.__navigator.navigate_to_server_groups()
        severgrp_table = Rtable(self.__admin_console, "Server groups")
        if self._is_MSP_admin:
            severgrp_table.select_company(self.company_name)

        return severgrp_table.get_column_data("Name", True)

    def __get_company_alerts(self):
        """ Returns alerts related to a company"""
        self.__navigator.navigate_to_alerts()
        Alerts(self.__admin_console).select_alert_definitions()
        alert_def_obj = AlertDefinitions(self.__admin_console)
        if self._is_MSP_admin:
            return alert_def_obj.get_alert_definitions_for_company(self.company_name)
        else:
            return alert_def_obj.get_alert_definitions()

    def validate_usergroup(self):
        """ Validates if usergroup set in UI and backend are same """
        self.log.info('Validating usergroup...')
        userg_api = self.organization.user_groups
        userg_ui = self.__get_company_usergroup()
        self.assert_comparison(userg_ui, userg_api)

    def validate_users(self):
        """ Validates if users shown in UI and backend are same """
        self.log.info('Validating users...')
        user_api = self.organization.contacts
        user_ui = self.__get_company_users()
        self.assert_comparison(user_ui, user_api)

    def validate_security_associations(self, is_edited=False):
        """ Validates the security associations of company"""
        self.log.info('Validating security associations..')
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        security_assoc_api = self.organization.get_security_associations()
        security_assoc_ui = self.company_details.get('Security')
        security_assoc_ui.pop('User/Group')
        for key in security_assoc_ui.keys():
            if isinstance(security_assoc_ui[key], str):
                security_assoc_ui[key] = [security_assoc_ui[key]]

        self.assert_comparison(security_assoc_ui, security_assoc_api)

    def validate_operators(self, is_edited=False):
        """ Validates if the operator shown in admin console and backend are same """
        self.log.info('Validating Operators..')
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        operator_api = self.organization.tenant_operator
        operator_api_val = list(operator_api.values())
        operator_api_list = []
        for elem in operator_api_val:
            operator_api_list = operator_api_list + elem
        operator_ui = self.company_details['Operators']

        if 'User/Group' in operator_ui:
            operator_ui.pop('User/Group')
            operator_ui_list = list(operator_ui.keys())
        else:
            operator_ui_list = operator_ui
        self.assert_comparison(operator_ui_list, operator_api_list)

    def validate_general_tile(self, is_edited=False):
        """ Validate is the properties shown in general tile in UI and the backend are same """
        self.log.info('Validating General Tile..')
        if is_edited:
            self.__get_company_details()
        general_tile_ui = self.company_details.get('General')
        general_tile_ui.pop('Time zone')
        general_tile_ui.pop('Workload region')

        org = self.organization
        old_org = copy.copy(org)
        org.refresh()
        self.org_helper = OrganizationHelper(self.__comcell, self._company_name)
        general_tile_api = self.org_helper.get_company_properties()
        if 'Supported solutions' in general_tile_api:
            general_tile_api['Supported solutions'] = \
                self.__convert_solution_list_to_id(general_tile_api['Supported solutions'], list=False)

        general_tile_api['Infrastructure type'] = \
            self.__convert_infrastructure_to_id(general_tile_api['Infrastructure type'])
        general_tile_api['User session timeout value'] = \
            self.__timeout_value(general_tile_api['User session timeout value'])
        general_tile_api['Job start time'] = self.__convert_job_start_time(general_tile_api['Job start time'])

        if is_edited:
            edited_general_tile = {
                "Company created on": org.organization_created_on,
                "Company alias": self._company_alias,
                "Associated email suffixes": self._smtp,
                "Requires authcode for installation": org.is_auth_code_enabled,
                "Enable two factor authentication": org.is_tfa_enabled,
                "Enable reseller mode": org.reseller_enabled,
                "Allow owners to enable data encryption": org.is_auto_discover_enabled,
                "Enable auto discover": org.is_auto_discover_enabled,
                "Infrastructure type": self.__convert_infrastructure_to_id(org.infrastructure_type),
                "Supported solutions": self.__convert_solution_list_to_id(org.supported_solutions, list=False),
                "Job start time": self.__convert_job_start_time(self.job_start_time),
                "Password ages in": self.__password_age(org.password_age_days),
                "Download software from internet": org.is_download_software_from_internet_enabled,
                "User session timeout value": self.__timeout_value(org.user_session_timeout)
            }
            self.assert_comparison(general_tile_ui, edited_general_tile)
            self.assert_comparison(edited_general_tile, general_tile_api)
            if old_org.domain_name != org.domain_name:
                self._validate_company_alias()
        
        if not self._is_MSP_admin:
            general_tile_api.pop('Supported solutions')

        self.assert_comparison(general_tile_api, general_tile_ui)

    def validate_plans(self, is_edited=False):
        """ Validates if plans shown in UI and backend are same """
        self.log.info('Validating plans...')
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        plans_api = self.organization.plans
        plans = self.company_details['Plans']
        plans_ui = [plan.lower() for plan in plans]
        if is_edited:
            edited_plans = self._plans
            if not edited_plans == plans_api == plans_ui:
                raise Exception("All the values don't match")
        else:
            self.assert_comparison(plans_ui, plans_api)

    def validate_contacts(self, is_edited=False):
        """ Validates if contacts shown in UI and backend are same """
        self.log.info('Validating contacts...')
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        contacts_list = self.organization.contacts_fullname
        contacts_ui = self.company_details['Contacts'].get('Contact name', []).split(', ')
        self.assert_comparison(contacts_ui, contacts_list)

        if is_edited:
            contacts_list = self.organization.contacts_fullname
            contacts = [self.contact_name] if type(self.contact_name) == str else self.contact_name
            if not contacts == contacts_list:
                raise Exception("All the values don't match")

    def validate_email_settings(self, is_edited=False):
        """ Validates if emails shown in UI and backend are same """
        self.log.info('Validating email settings..')
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        sender_name = self.organization.sender_name
        email_info_api = [sender_name, self.__organization.sender_email] if sender_name else []
        email_ui = (self.company_details.get("Email settings"))
        email_info_ui = []
        if email_ui:
            email_info_ui = list(email_ui.values())
        self.assert_comparison(email_info_api, email_info_ui)

        if is_edited:
            sender_name = self.organization.sender_name
            email_info_api = [sender_name, self.organization.sender_email] if sender_name else []
            email_settings = [self.sender_name, self.sender_email]
            self.assert_comparison(email_info_api, email_settings)

    def validate_external_auth(self):
        """ Validates if external authentication shown in UI and backend are same """
        pass

    def validate_file_exception(self, is_edited=False):
        """ Validates if file exceptions shown in UI and backend are same """
        self.log.info('Validating file exceptions..')
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        excep = self.organization.file_exceptions
        file_ex_present = False
        file_exceptions_dict = {}
        for patterns in excep.values():
            if patterns:
                file_ex_present = True
        if file_ex_present:
            file_exceptions_dict = {"Use company filters on all subclients":
                                        'ON' if self.organization.is_global_file_exceptions_enabled else 'OFF'}
            for os_type in self.organization.file_exceptions.keys():
                ex = self.organization.file_exceptions[os_type]
                ex_string = "\n".join(map(str, ex))
                if ex_string:
                    file_exceptions_dict[os_type] = ex_string

        file_exceptions_ui = self.company_details['File exceptions']
        self.assert_comparison(file_exceptions_dict, file_exceptions_ui)

        if is_edited:
            new_excep = self.organization.file_exceptions
            edited_vals = self.file_exceptions
            file_exceptions = {}
            for key in edited_vals:
                if key == "windows_path":
                    file_exceptions['Windows'] = edited_vals[key]
                elif key == "unix_path":
                    file_exceptions["Unix"] = edited_vals[key]

            self.assert_comparison(file_exceptions, new_excep)

    def validate_client_groups(self):
        """ Validates if client groups shown in UI and backend are same """
        self.log.info('Validating server groups...')
        self.org_helper = OrganizationHelper(self.__comcell, self.organization.name)
        smart_client_group = self.org_helper.company_smart_client_group_object.name
        client_group_api = list(self.organization.client_groups.keys())
        client_group_api.remove(smart_client_group.lower())
        client_group_ui = [client_name.lower() for client_name in self.__get_company_server_groups()]
        self.assert_comparison(client_group_ui, client_group_api)

    def validate_alerts(self):
        """ Validates if alerts associated with a company shown in Alerts page and backend are same """
        self.log.info('Validating alerts...')
        alert_api = sorted(self.organization.get_alerts())
        alert_ui = sorted(self.__get_company_alerts())
        self.assert_comparison(alert_ui, alert_api)

    def validate_navigation_preferences(self):
        """ Validates the navigation preferences """
        self.log.info('Validating navigation preferences...')
        # This is just a basic check
        if self._is_MSP_admin:
            self.__navigator.navigate_to_company()
            self.__table.access_link(self.company_name)
            self.__admin_console.close_popup() # sometimes pop up appears after auto page refresh
            self.__admin_console.select_main_bar_tab_item(link_text= 'Overview')
            self.__panel.open_hyperlink_on_tile("Navigation customization")
            table_headers = self.__admin_console.driver.find_elements(By.XPATH, 
                "//span[contains(@class, 'ui-grid-header-cell-label')]")
            nav_headers = []
            for elem in table_headers:
                nav_headers.append(elem.text)
            expected_column_headers = ["Tenant admin", "Tenant user"]
            self.assert_comparison(nav_headers[1:], expected_column_headers)

    def __get_company_details(self):
        """ Sets company details """
        if not self._is_MSP_admin:
            self.__navigator.navigate_to_company()
            self.company_details = self.__company_helper.company_info()
        else:
            self.__navigator.navigate_to_companies()
            self.__table.access_link(self._company_name)
            self.__admin_console.close_popup() # sometimes pop up appears after auto page refresh
            self.__admin_console.select_overview_tab()
            self.company_details = self.__company_helper.company_info()


    def validate_default_configurations(self):
        """ Method to validate if the default config are set correctly """
        self.__get_company_details()
        for func_name in company_tile:
            getattr(self, 'validate_' + func_name)()

    def validate_supported_solutions(self, parent_username, parent_password, tenant_username, password, is_edited=False):
        """ Method to validate the functionality for supported solutions on company page"""
        if is_edited:
            self.refresh_company_details()

        details = self.company_details
        supported_solns = details['General']['Supported solutions']
        self.__admin_console.logout()
        self.__admin_console.login(tenant_username, password)
        supported_solns_ta = self.__setup.supported_solutions()
        self.assert_comparison(supported_solns, supported_solns_ta)
        self.__admin_console.logout()
        self.__admin_console.login(parent_username, parent_password)

    def validate_infrastructure_type(self, parent_username, parent_password, tenant_username, password, is_edited=False):
        """ Method to validate the functionality for infrastructure type on company page"""
        if is_edited:
            self.organization.refresh()
            self.refresh_company_details()

        details = self.company_details
        infrastructure_type = details['General']['Infrastructure type']
        self.__admin_console.logout()
        self.__admin_console.login(tenant_username, password)
        self.__navigator.navigate_to_getting_started()
        infrastructure_type_ta = 'Own storage' if self.__setup.has_owned_storage() is True \
            else 'Rented storage'
        self.assert_comparison(infrastructure_type_ta, infrastructure_type)
        self.__admin_console.logout()
        self.__admin_console.login(parent_username, parent_password)

    def validate_plan_functionality(self, user_details, plan_details):
        """ Method to validate the functionality for Plan on company page"""
        self.__navigator.navigate_to_plan()

        plan_name = plan_details['plan_name']
        derived_plan_name = plan_details['derived_plan_name']
        storage = plan_details['storage']
        allow_override = plan_details['allow_override']
        backup_data = plan_details['backup_data']

        tenant_username = user_details['tenant_username']
        password = user_details['tenant_password']

        plan = Plans(self.__admin_console)
        plan.create_server_plan(plan_name=plan_name, storage=storage, allow_override=allow_override)

        self.__navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_helper.edit_company_plans([plan_name])

        self.__admin_console.logout()
        self.__admin_console.login(tenant_username, password)

        self.__navigator.navigate_to_plan()
        self.__table.access_link(plan_name)
        plan.click_create_derived_plan_button()
        plan.create_laptop_derived_plan(derived_plan=derived_plan_name, backup_data=backup_data)

        self.__navigator.navigate_to_plan()
        plan.delete_plan(plan_name=derived_plan_name)

        self.__admin_console.logout()
        self.__admin_console.login(user_details['parent_username'], user_details['parent_password'])

        self.__navigator.navigate_to_plan()
        plan.delete_plan(plan_name=plan_name)

    def validate_security_functionality(self, user_details, password, client_details):
        """ Method to validate the functionality for Security tile on company page"""
        # already have a client associated to your company
        client_name = client_details['client']
        subclient = client_details['subclient']
        loc = client_details['loc']
        os = client_details['OS']
        self.__navigator.switch_company_as_operator(self.company_name)
        self.__navigator.navigate_to_users()
        self.__users.add_local_user(email=user_details["user1"]['email'],
                                    groups=[self.company_alias + "\\Tenant Admin"],
                                    password=password,
                                    upn="")

        self.__navigator.switch_company_as_operator("Reset")
        self.__navigator.navigate_to_users()
        self.__users.add_local_user(email=user_details["user2"]['email'],
                                    username=user_details["user2"]['username'],
                                    password=password, upn="")

        self.__navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_helper.edit_company_operators(
            {
                user_details["user2"]['username']: ['Tenant Operator']
            })

        self.__admin_console.logout()
        self.__admin_console.login(user_details["user1"]['username'], password)
        self.__navigator.navigate_to_file_servers()
        FileServers(self.__admin_console).access_server(client_name)

        self.__admin_console.access_tab("Subclients")
        self.fssubclient.access_subclient(subclient, 'defaultBackupSet')
        self.__subclient.edit_content(browse=True, add_content=loc, del_content=loc)

        self.__admin_console.logout()
        self.__admin_console.login(user_details["user2"]['username'], password)
        self.__admin_console.click_button("OK")
        self.__navigator.switch_company_as_operator(self.company_name)
        self.__navigator.navigate_to_file_servers()
        FileServers(self.__admin_console).access_server(client_name)
        try:
            self.__admin_console.access_tab("Subclients")
            self.fssubclient.access_subclient(subclient, 'defaultBackupSet')
            self.__subclient.edit_content(browse=True, add_content=loc, del_content=loc)

            raise CVTestStepFailure("Tenant operators should not be able to browse data")
        except Exception:
            self.log.info(Exception)

    def validate_operator_functionality(self, user_details, password, client_details):
        """ Method to validate the functionality for Operator tile on company page"""
        client_name = client_details['client']
        subclient = client_details['subclient']
        loc = client_details['loc']
        os = client_details['OS']
        self.__navigator.navigate_to_users()
        self.__users.add_local_user(email=user_details["user1"]['email'],
                                    username=user_details["user1"]['username'],
                                    password=password, upn="")
        self.__navigator.navigate_to_users()
        self.__users.add_local_user(email=user_details["user2"]['email'],
                                    username=user_details["user2"]['username'],
                                    password=password, upn="")

        self.__navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_helper.edit_company_operators(
            {
                    user_details["user1"]['username']: ['Tenant Operator'],
                    user_details["user2"]['username']: ['Plan Subscription Role']
            })

        self.__admin_console.logout()
        self.__admin_console.login(user_details["user1"]['username'], password)
        self.__admin_console.click_button("OK")
        self.__navigator.switch_company_as_operator(self.company_name)

        self.__navigator.navigate_to_file_servers()
        FileServers(self.__admin_console).access_server(client_name)
        try:
            self.__admin_console.access_tab("Subclients")
            self.fssubclient.access_subclient(subclient, 'defaultBackupSet')
            self.__subclient.edit_content(browse=True, add_content=loc, del_content=loc)
            raise CVTestStepFailure("Tenant operators should not be able to browse data")
        except Exception:
            self.log.info(Exception)

        self.__admin_console.logout()
        self.__admin_console.login(user_details["user2"]['username'], password)
        self.__admin_console.click_button("OK")
        self.__navigator.switch_company_as_operator(self.company_name)
        self.__navigator.navigate_to_file_servers()
        servers = self.__table.get_column_data("Name")
        if servers:
            raise CVTestStepFailure("Error: No server associated to the user")

    def validate_allow_owner_data_encryption(self, owner_details):
        """ Method to validate the functionality for allow owners to enable data encryption in General tile
            on company page

        Args:
            owner_details (dict): Dict containing info about the client with owner
                eg: owner_details = {
                                        "client": "TestClient"
                                        "username": "Test User",
                                        "password": "#####"
                                    }
        """
        self.__admin_console.logout()
        self.__admin_console.login(owner_details['username'], owner_details['password'])
        self.__navigator.navigate_to_my_data()
        if not self.__company_helper.check_data_encryption_tile(client_name=owner_details['client']):
            CVTestStepFailure("Error: No data encryption tile found in computer settings page")

    def company_entities(self):
        """Method to return basic entities associated to a company"""
        entities = {}
        self.__navigator.navigate_to_users()
        self.__rtable.search_for(self.company_alias)
        users = self.__rtable.get_column_data('User name')
        if users:
            entities['Users'] = users

        self.__navigator.navigate_to_user_groups()
        self.__rtable.search_for(self.company_alias)
        user_groups = self.__rtable.get_column_data('Group name')
        if user_groups:
            entities['Users Groups'] = user_groups

        self.__navigator.navigate_to_server_groups()
        server_groups = self.__table.get_column_data('Name')
        if self.company_name in server_groups:
            entities['Server Groups'] = self.company_name

        self.__navigator.navigate_to_alerts()
        Alerts(self.__admin_console).select_alert_definitions()
        self.__table.search_for(self.company_name)
        alerts = self.__table.get_column_data('Name')
        if alerts:
            entities['Alerts'] = alerts

        return entities

    def edit_company_general_settings(self, **kwargs):
        """This function is used for validation of details in General tile after editing
        Usage:
            edit_company_general_settings(smtp='gmail.com',two_factor={'default':'add','user_groups':['company_alias\\tenant_admin']},company_alias=True)
        """
        self.__navigator.navigate_to_company()
        self.__companies.access_company(self._company_name)
        edit_general_settings = {}
        if 'smtp' in kwargs:
            self._smtp = kwargs['smtp']
            edit_general_settings['smtp'] = self._smtp
        if 'company_alias' in kwargs :
            self._company_alias = kwargs['company_alias']
            edit_general_settings['company_alias'] = self._company_alias
        if 'two_factor' in kwargs:
            self._tfa = kwargs['two_factor']
            edit_general_settings['2-factor'] = self._tfa

        self.__organization = Organization(self.__comcell, self._company_name)
        self.__company_details.edit_general_settings(
            general_settings=edit_general_settings)

        self.__comcell.refresh()
        

    def _validate_company_alias(self):
        """for vaildating company alias """
        self.__navigator.navigate_to_user_groups()
        self.__rtable.search_for(self._company_alias)  # use __rtable for SP 25
        lst = self.__rtable.get_column_data(column_name="Group name")
        if not lst:
            CVWebAutomationException("Company alias not changed in User Group")
        else:
            self.log.info("Validated company alias")

        
    def validate_tfa_login(self, user_name,password, tfa_enabled_group):
        """
        To validate that the given login is done by TFA or not
        Args:
            user_name (str): username to be used
            password (str): password for the given username
            tfa_enabled_group (bool): is tfa enabled for a user group
        """
        self.__admin_console.is_tfa_login = False
        if tfa_enabled_group:
            self.__admin_console.login(password=password,
                                       username=user_name,
                                       pin_generator=lambda: self.user_helper.get_tfa_otp(user_name))
        else:
            self.__admin_console.login(password=password,
                                   username=user_name)

        if self.__admin_console.is_tfa_login ^ tfa_enabled_group:
            error_message = "TFA is " + "enabled" if tfa_enabled_group else "disabled" + " for company but user " + \
                user_name + " loggedin " + "with" if self.__admin_console.is_tfa_login else "without" + "TFA login."
            raise CVWebAutomationException(error_message)
        self.__admin_console.logout()

    def refresh_company_details(self):
        """Reload the company details from UI"""
        self.__get_company_details()

    def validate_active_company_list(self):
        """Get all the company names from DB"""
        self.__navigator.navigate_to_companies()
        company_list = self.__companies.get_active_companies()
        query = 'select hostName from UMDSProviders where serviceType=5 and enabled=1 and flags=0'
        self.csdb.execute(query)
        company_list_db = self.csdb.fetch_all_rows()
        self.log.info("Comparing companies listed in UI with companies listed in DB")
        self.assert_comparison(company_list, self.parse_and_clean_data(company_list_db))

    def parse_and_clean_data(self, data):
        """Method to restructure data coming from DB"""
        clean_data = []
        for item in data:
            if item[0]:
                clean_data.append(item[0])

        clean_data.sort()
        return clean_data

    def validate_deleted_company_list(self):
        """Validate if all deleted companies are listed"""
        time.sleep(300) # select the value that you have under appMaintenaceMinutes
        self.__navigator.navigate_to_users()
        self.__navigator.navigate_to_companies()
        company_list = self.__companies.get_deleted_companies()
        query = 'select hostName from UMDSProviders where serviceType=5 and enabled=0'
        self.csdb.execute(query)
        company_list_db = self.csdb.fetch_all_rows()
        self.log.info("Comparing companies listed in UI with companies listed in DB")
        self.assert_comparison(company_list, self.parse_and_clean_data(company_list_db))

    def validate_deactivated_company_list(self):
        """Validate if all deactivated companies are listed"""
        self.__navigator.navigate_to_companies()
        company_list = self.__companies.get_deactivated_companies()
        query = 'select hostName from UMDSProviders where serviceType=5 and enabled=1 and flags=16'
        self.csdb.execute(query)
        company_list_db = self.csdb.fetch_all_rows()
        self.log.info("Comparing companies listed in UI with companies listed in DB")
        self.assert_comparison(company_list, self.parse_and_clean_data(company_list_db))

    def delete_deactivated_company(self, company_name):
        """method to delete deactivated company"""
        self.__navigator.navigate_to_companies()
        self.__table.view_by_title("Deactivated")
        self.__companies.delete_company(company_name)

    def __password_age(self, password_age_days):
        """Formats password age"""
        if password_age_days == 0:
            return "Password age not set"
        else:
            return f"{password_age_days} days"

    def __timeout_value(self, user_session_timeout):
        """Formats user session timeout value"""
        if user_session_timeout == 0:
            return "Not configured"
        else:
            return f"{user_session_timeout} minutes"