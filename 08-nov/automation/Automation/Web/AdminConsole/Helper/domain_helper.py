from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on identity servers page for domains and domain details page.

DomainHelper : This class provides methods for Domains related operations

navigate_to_domain_details_page()     -- Navigates to domains details page
all_domains_info()                    -- Returns info of all domains displayed
                                         on the identity servers page
check_domain_exists()                 -- Checks if the domain exists
add_domain()                          -- Adds a domain
edit_domain()                         -- Edits a domain
delete_domain()                       -- Deletes a domain
input_value_dict()                    -- Returns a dict of all the getter values
validate_domain()                     -- Validates the getter values against displayed values

"""

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.identity_servers import Domains, IdentityServers
from Web.AdminConsole.AdminConsolePages.domain_details import DomainDetails


class DomainHelper(object):

    def __init__(self, admin_console):

        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__driver = admin_console.driver

        self.log = logger.get_log()

        self._all_domains = None
        self._netbios_name = None
        self._domain_name = None
        self._domain_username = None
        self._domain_password = None
        self._skip_ownership_transfer = True
        self._transfer_owner = None
        self._company = None
        self._type = "Active directory"
        self._domain_dict = None
        self._proxy_client = None
        self._proxy_client_value = None
        self._secure_ldap = None
        self._user_group = None
        self._local_group = None
        self._quota_enabled = False
        self._quota_limit = 100
        self.domains = Domains(self.__admin_console)
        self.identity_servers = IdentityServers(self.__admin_console)
        self.domain_details_page = DomainDetails(self.__admin_console)

    @property
    def netbios_name(self):
        """Get value for netbios name"""
        return self._netbios_name

    @netbios_name.setter
    def netbios_name(self, value):
        """Set value for netbios name"""
        self._netbios_name = value

    @property
    def domain_name(self):
        """Get value for domain name"""
        return self._domain_name

    @domain_name.setter
    def domain_name(self, value):
        """Set domain name value"""
        self._domain_name = value

    @property
    def domain_username(self):
        """Get domain username value"""
        return self._domain_username

    @domain_username.setter
    def domain_username(self, value):
        """Set the value for domain username"""
        self._domain_username = value

    @property
    def domain_password(self):
        """Get the value for domain password"""
        return self._domain_password

    @domain_password.setter
    def domain_password(self, value):
        """Set the value for domain password"""
        self._domain_password = value

    @property
    def domain_company(self):
        """Get value for domain company"""
        return self._company

    @domain_company.setter
    def domain_company(self, value):
        """Set value for netbios domain company"""
        self._company = value

    @property
    def skip_ownership_transfer(self):
        """Get skip ownership transfer, used while deleting a domain"""
        return self._skip_ownership_transfer

    @skip_ownership_transfer.setter
    def skip_ownership_transfer(self, value):
        """Get skip ownership transfer value"""
        self._skip_ownership_transfer = value

    @property
    def transfer_owner(self):
        """Get the transfer owner value"""
        return self._transfer_owner

    @transfer_owner.setter
    def transfer_owner(self, value):
        """Sets the transfer owner value"""
        self._transfer_owner = value

    @property
    def domain_dict(self):
        """Get domain_dict value"""
        return self._domain_dict

    @domain_dict.setter
    def domain_dict(self, value):
        """Sets domain_dictvalue"""
        self._domain_dict = value

    @property
    def proxy_client(self):
        """Get the proxy client"""
        return self._proxy_client

    @proxy_client.setter
    def proxy_client(self, value):
        """Sets the proxy client """
        self._proxy_client = value

    @property
    def proxy_client_value(self):
        """Get the proxy client"""
        return self._proxy_client_value

    @proxy_client_value.setter
    def proxy_client_value(self, value):
        """Sets the proxy client """
        self._proxy_client_value = value

    @property
    def secure_ldap(self):
        """Get the secure ldap value"""
        return self._secure_ldap

    @secure_ldap.setter
    def secure_ldap(self, value):
        """Sets the secure ldap value"""
        self._secure_ldap = value

    @property
    def user_group(self):
        """Get the User group"""
        return self._user_group

    @user_group.setter
    def user_group(self, value):
        """Sets the User group"""
        self._user_group = value

    @property
    def local_group(self):
        """Get the local group"""
        return self._local_group

    @local_group.setter
    def local_group(self, value):
        """Sets the local group"""
        self._local_group = value

    @property
    def quota_enabled(self):
        """Get the quota enabled value"""
        return self._quota_enabled

    @quota_enabled.setter
    def quota_enabled(self, value):
        """Sets the quota enabled value"""
        self._quota_enabled = value

    @property
    def quota_limit(self):
        """Get the quota limit value"""
        return self._quota_limit

    @quota_limit.setter
    def quota_limit(self, value):
        """Sets the quota limit value"""
        self._quota_limit = value

    def navigate_to_domain_details_page(self, netbios_name):
        """Navigates to domains details page"""

        self.__navigator.navigate_to_identity_servers()
        if netbios_name:

            base = self.__driver.find_element(By.XPATH,
                                              f"//a[contains(text(),'{netbios_name}')]/../../..")
            if base.find_element(By.XPATH, ".//td[2]/span").text == "AD":
                base.find_element(By.XPATH, ".//td[1]/span/a").click()

            self.__admin_console.wait_for_completion()
        else:
            raise Exception("Please check the netbios name passed"
                            "as argument or domain does not exist")

    def all_domains_info(self):
        """
        Lists the information of all the domains in the commcell

        Returns:
            List of all domains
        """

        all_domains_info = []
        domains_displayed = self.domains.domains_list()

        for name in domains_displayed:
            self.navigate_to_domain_details_page(name)
            domain_info = self.domain_details_page.extract_domain_info()
            all_domains_info.append(domain_info)
            self.__admin_console.select_hyperlink("Identity servers")

        return all_domains_info

    def check_domain_exists(self):
        """Checks if a domain with the set netbios name exists"""

        if self.__admin_console.check_if_entity_exists("link", self.netbios_name):
            return True
        else:
            return False

    def add_domain(self, negative_case=False):
        """
        Adds a domain with the set parameters - netbios name, username, password, domain name

        Args:
            negative_case   (bool)  -   if True, will test negative scenario also
        """
        self.__navigator.navigate_to_identity_servers()
        self.domains.add_domain(domain_name=self.domain_name,
                                netbios_name=self.netbios_name,
                                username=self.domain_username,
                                password=self.domain_password,
                                secure_ldap=self.secure_ldap,
                                proxy_client=self.proxy_client,
                                proxy_client_value=self.proxy_client_value,
                                user_group=self.user_group,
                                local_group=self.local_group)
        if negative_case:
            self.log.info("Validating negative case - duplicate AD creation")
            self.__navigator.navigate_to_identity_servers()
            try:
                self.domains.add_domain(domain_name=self.domain_name,
                                        netbios_name=self.netbios_name,
                                        username=self.domain_username,
                                        password=self.domain_password,
                                        secure_ldap=self.secure_ldap,
                                        proxy_client=self.proxy_client,
                                        proxy_client_value=self.proxy_client_value,
                                        user_group=self.user_group,
                                        local_group=self.local_group)
                raise Exception("Expected error for AD being present already, but got no error")
            except Exception as exp:
                if ((self.domain_name.lower() in str(exp).lower() or
                     self.netbios_name.lower() in str(exp).lower())
                        and 'already exist' in str(exp).lower()):
                    self.log.info("Verified error message for AD already exist")
                else:
                    self.log.error(f"Got different error: {str(exp)}")
                    raise exp

            self.log.info("Validating negative case - incorrect AD creation")
            self.__navigator.navigate_to_identity_servers()
            try:
                self.domains.add_domain(domain_name="incorrect.domain",
                                        netbios_name="INCORRECT",
                                        username="wrong_username",
                                        password="wrong_password")
                raise Exception("Expected error for AD details wrong, but got no error")
            except Exception as exp:
                if 'could not be verified' in str(exp).lower():
                    self.log.info("Verified error message for AD could not be verified")
                else:
                    self.log.error(f"Got different error: {str(exp)}")
                    raise exp

    def edit_domain(self, negative_case=False):
        """
        Edits a domain with the set parameters

        Args:
            negative_case   (bool)  -   if True, will test negative scenario also
        """
        self.__navigator.navigate_to_identity_servers()
        if self.check_domain_exists():
            self.identity_servers.select_identity_server(self.netbios_name)
            domain_dict = {}
            if self.domain_username:
                domain_dict['name'] = self.domain_name
            if self.domain_username:
                domain_dict['username'] = self.domain_username
            if self.domain_password:
                domain_dict['password'] = self.domain_password
            if self.proxy_client:
                domain_dict['proxy_client'] = self.proxy_client
            if self.proxy_client_value:
                domain_dict['proxy_client_value'] = self.proxy_client_value

            if negative_case:
                self.log.info("Validating negative case with wrong creds updated")
                try:
                    # edit AD with wrong password and make sure no proxy client, otherwise error is not expected
                    self.domain_details_page.modify_domain(
                        domain_dict | {'password': 'incorrect_pwd', 'proxy_client': False} 
                    )
                    raise Exception("Expected error for invalid creds, but got no error")
                except Exception as exp:
                    if 'could not be verified' in str(exp).lower():
                        self.log.info("Verified error message for AD could not be verified")
                    else:
                        self.log.error(f"Got different error: {str(exp)}")
                        raise exp
                self.log.info("Successfully validated negative case with wrong creds updation")
                self.__admin_console.refresh_page()
                self.__navigator.navigate_to_identity_servers()
                self.identity_servers.select_identity_server(self.netbios_name)

            self.domain_details_page.modify_domain(domain_dict)
            self.log.info("Domain successfully edited")
        else:
            raise Exception("Could not edit domain. Domain does not exist.")

    def delete_domain(self):
        """Deletes a domain which has the set netbios name"""

        self.__navigator.navigate_to_identity_servers()
        self.__admin_console.wait_for_completion()
        if self.check_domain_exists():
            self.domains.delete_domain(self.netbios_name,
                                       self.skip_ownership_transfer,
                                       self.transfer_owner)
        else:
            raise Exception("Could not delete domain. Domain does not exist.")

        if not self.check_domain_exists():
            self.log.info("Domain deleted successfully")
        else:
            raise Exception("Domain was not deleted")

    def input_value_dict(self):
        """Creates a dictionary of the provided domain values"""
        input_dict = dict()
        input_dict["Directory type"] = self._type
        input_dict["Name"] = self.domain_name
        input_dict["Credentials"] = self.domain_username
        if self.domain_company is None:
            input_dict["Company"] = "Commcell"
        else:
            input_dict["Company"] = self.domain_company

        return input_dict

    def validate_domain(self):
        """Validates the provided domain details against the adminconsole domain details """
        input_dict = self.input_value_dict()
        self.__navigator.navigate_to_identity_servers()
        self.identity_servers.select_identity_server(self.netbios_name)
        displayed_val = self.domain_details_page.get_domain_details()

        for key, value in input_dict.items():
            if str(input_dict[key]).lower() == str(displayed_val[key]).lower():
                self.log.info("Input Value {0} matches with displayed value {1}".format(
                    input_dict[key], displayed_val[key]))
            else:
                raise Exception(
                    f"Provided domain details are not valid, failed match for {key}: "
                    f"expected {input_dict[key]} but got {displayed_val[key]}"
                )
