from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Configure Hypervisor Tab on Metallic

"""

import time
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from Web.AdminConsole.Hub.CCVMKubernetes.ProxyAccess import ProxyAccess
from Web.AdminConsole.Hub.utils import Utils
from Web.Common.page_object import (
    WebAction,
    PageService
)


class ConfigureHypervisor:
    """
    Class for Configure Hypevisor Page
    """

    def __init__(self, wizard, admin_console, metallic_options, commcell_info=None):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__commcell = commcell_info['commcell']
        self.__commcell_info = commcell_info
        self.__base_xpath = "//bc-vm-app-config"
        self.metallic_helper = VSAMetallicHelper.getInstance(admin_console, metallic_options, commcell_info)
        self.utils = Utils(admin_console)
        self.__wizard = wizard
        self.log = self.__admin_console.log
        self.metallic_options = metallic_options
        self.config()

    def config(self):
        if self.metallic_options.existing_hypervisor:
            self.select_existing_hypervisor()
        else:
            self.create_hypervisor()
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @WebAction()
    def fill_form_by_xpath(self, xpath, value):
        """
            Fill the value in a text field with xpath of the element.

            Args:
                xpath (str) - xpath attribute value of the element
                value (str)      -- the value to be filled in the element

            Raises:
                Exception:
                    If there is no element with given xpath
        """
        element = self.__driver.find_element(By.XPATH, xpath)
        element.click()
        element.clear()
        element.send_keys(value)
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_hypervisor(self):
        """
        create new hypervisor
        Args:
            options:    (dict)  options for creationg new hypervisor

        Returns:
            None
        """
        self.log.info("creating new hypervisor")
        if self.__admin_console.check_if_entity_exists(entity_name='id', entity_value='addHypervisor'):
            self.__wizard.select_radio_button(id="addHypervisor")
        if not self.metallic_helper.hypervisor_creation_wizard.get_active_step().lower() == 'azure application':
            self.__wizard.fill_text_in_field(id='name', text=self.metallic_options.hyp_client_name)
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.azure_vm.lower() and \
                self.metallic_helper.hypervisor_creation_wizard.get_active_step().lower() == "azure application":
            self.__wizard.select_radio_button(id="useExistingAppRadio")
            self.__wizard.fill_text_in_field(id='subscriptionIdField', text=self.metallic_options.subscription_id)
            self.__wizard.click_icon_button_by_title(title='Create new')
            data_dict = dict()
            data_dict['credential_name'] = self.metallic_options.hyp_credential_name
            data_dict['tenant_id'] = self.metallic_options.tenant_id
            data_dict['application_id'] = self.metallic_options.hyp_user_name
            data_dict['application_password'] = self.metallic_options.hyp_pwd
            time.sleep(30)
            self.metallic_helper.create_credential_object(data_dict)
        elif self.metallic_options.app_type.lower() in (
                CCVMKubernetesTypes.hyper_v.lower(), CCVMKubernetesTypes.vmware.lower(), CCVMKubernetesTypes.nutanix.lower()):
            self.__wizard.click_icon_button_by_title('Create new')
            data_dict = dict()
            data_dict['credential_name'] = self.metallic_options.hyp_credential_name
            data_dict['userAccount'] = self.metallic_options.hyp_user_name
            data_dict['password'] = self.metallic_options.hyp_pwd
            time.sleep(30)
            self.metallic_helper.create_credential_object(data_dict)
            self.__admin_console.wait_for_completion()
            time.sleep(30)
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.hyper_v.lower():
                self.__wizard.fill_text_in_field(id='serverName', text=self.metallic_options.hyp_host_name)
                ProxyAccess(self.__wizard,
                            self.__admin_console, self.metallic_options,
                            self.__commcell_info)

            elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.nutanix.lower():
                self.__wizard.fill_text_in_field(id='hostName', text=self.metallic_options.hyp_host_name)

            else:
                self.__wizard.fill_text_in_field(id='vcenterHostName',
                                                 text=self.metallic_options.hyp_host_name)
        elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.oci.lower():
            # self.__wizard.fill_text_in_field
            pass
        elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
            if not self.metallic_options.BYOS:
                return
            if not self.metallic_options.aws_admin_account_configured:
                self.metallic_helper.hypervisor_helper_obj.switch_to_admin_access()
                self.metallic_options.hyp_credential_name = "vsa aws admin creds auto" + \
                                                            self.metallic_options.unique_param
                self.select_existing_credential()
            else:
                self.__wizard.click_icon_button_by_title(title='Create new')
                self.metallic_helper.hypervisor_helper_obj.switch_to_tenant_access()
                self.metallic_options.hyp_credential_name = "vsa aws tenant creds auto"
                self.metallic_options.content_list = self.metallic_options.tenant_content_list
                self.metallic_options.hyp_credential_name = self.metallic_options.hyp_credential_name + \
                                                            self.metallic_options.unique_param
                if not self.metallic_options.aws_role_arn:
                    self.metallic_options.aws_role_arn = self.metallic_helper.hypervisor_helper_obj.\
                        get_role('MetallicRole').arn
                data_dict = {
                    'credential_name': self.metallic_options.hyp_credential_name,
                    'description': "credentials crated via automation for aws",
                    'role_arn': self.metallic_options.aws_role_arn
                }
                self.metallic_helper.create_credential_object(data_dict)
            if not self.metallic_options.aws_admin_account_configured:
                self.metallic_options.hyp_client_name = self.metallic_options.hyp_client_name + '-Tenant'
            self.metallic_options.aws_admin_account_configured = True
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_existing_credential(self):
        """
        select an existing credential object
        """
        self.log.info("selecting existing credential")
        self.__wizard.select_drop_down_values(id='credentials', values=[self.metallic_options.hyp_credential_name])

    @PageService()
    def select_existing_hypervisor(self):
        """
        Select an existing hypervisor
        """
        self.log.info("selecting existing hypervisor")
        self.__wizard.select_radio_button(id="existingHypervisor")
        self.__wizard.select_drop_down_values(id='Hypervisor', values=[self.metallic_options.hyp_client_name])
