from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
CofigIAMRole Tab on Metallic

"""
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from Web.AdminConsole.Hub.utils import Utils
from Web.Common.page_object import (
    PageService,
    WebAction
)
import time
from urllib.parse import urlparse, parse_qs
from AutomationUtils import config


class ConfigIAMRole:
    """
    class of the CofigIAMRole Page
    """
    def __init__(self, wizard, admin_console, metallic_options, commcell_info=None):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__commcell = commcell_info['commcell']
        self.__commcell_info = commcell_info
        self.metallic_helper = VSAMetallicHelper.getInstance(admin_console, metallic_options, commcell_info)
        self.utils = Utils(admin_console)
        self.log = self.__admin_console.log
        self.__wizard = wizard
        self.metallic_options = metallic_options
        self.config_options = config.get_config()
        self.config()

    def config(self):
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
            if not self.metallic_options.BYOS:
                self.metallic_helper.hypervisor_helper_obj.switch_to_admin_access()
                self.__aws_hosted_infra_configuration()
            else:
                self.__aws_cross_account_configuration()
                self.confirm_configuration()
        else:
            self.__configure_oci_role()
            self.__create_credential_object()
        self.__click_next()
        self.__admin_console.wait_for_completion()

    @PageService()
    def __click_next(self):
        """
        click next on the page
        """
        self.__wizard.click_next()

    def __create_credential_object(self):
        """
        create a new credential object
        :return:
        """
        private_key_path = self.config_options.Virtualization.oci.private_key_file
        self.__wizard.click_icon_button_by_title("Create new")
        data_dict = dict()
        data_dict['credential_name'] = "oci Automation Creds" + self.metallic_options.unique_param
        data_dict['tenancy_ocid'] = self.config_options.Virtualization.oci.tenancy
        data_dict['user_ocid'] = self.api_key_data.user_id
        data_dict['fingerprint'] = self.api_key_data.fingerprint
        data_dict['private_key_path'] = private_key_path
        data_dict['description'] = "oci creds object for automation testing"
        data_dict['private_key_password'] = self.config_options.Virtualization.oci.oci_private_key_password
        time.sleep(30)
        self.metallic_helper.create_credential_object(data_dict)

    def __configure_oci_role(self):
        """
        method to collect the stack information to execute on oci
        :return:
        stack ino
        """
        public_key_path = self.config_options.Virtualization.oci.public_key_file
        path = "//a[contains(text(),'Launch Oracle Cloud Stack Template')]"
        stack_url = self.__driver.find_element(By.XPATH, path).get_attribute('href')
        stack_params = parse_qs(urlparse(stack_url).query)
        stack_params['region'] = stack_params['zipUrl'][0].split('.')[1]
        zipUrl = stack_params['zipUrl'][0]
        import base64,requests
        encoded_file = base64.b64encode(requests.get(zipUrl).content).decode('ascii')
        stack_creation_data = dict()
        stack_creation_data['encoded_file'] = encoded_file
        stack_creation_data['display_name'] = 'metallication automation Role'
        stack_creation_data['description'] = "role with the permissions required"
        stack_creation_data['compartment_id'] = self.metallic_options.oci_policy_compartment
        variables = dict()
        variables['tenancy_ocid'] = self.config_options.Virtualization.oci.tenancy
        variables['region'] = stack_params['region']
        variables['user_email'] = "abc@abc.com"
        variables['policy_compartment_ocid'] = self.metallic_options.oci_policy_compartment
        stack_creation_data['variables'] = variables
        hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
        stack_info = hypervisor_helper.create_stack(stack_creation_data=stack_creation_data,
                                                    delete_previous_existing=True)
        self.metallic_helper.stacks_created.append(stack_info.id)
        plan_job = hypervisor_helper.run_plan_job_for_stack(stack_id= stack_info.id)
        apply_job = hypervisor_helper.run_apply_job_for_stack(stack_id=stack_info.id, plan_job_id=plan_job.id)
        job_output = hypervisor_helper.get_stack_apply_job_output(apply_job.id)
        username = job_output['outputs']['metallic_user']['value']
        self.user_details = hypervisor_helper.oci_user_details(username=username)
        self.api_key_data = hypervisor_helper.upload_api_key(self.user_details, public_key_path=public_key_path)

    @PageService()
    def select_authentication_method(self):
        """
        method to select authenticatio nmethod for aws
        Returns:
            None
        """
        self.log.info(f"selecting the authentication method : {self.metallic_options.aws_authentication_type}")
        self.__wizard.select_drop_down_values(id='authenticationMethod',
                                              values=[self.metallic_options.aws_authentication_type])

    @WebAction()
    def confirm_configuration(self):
        """
        confirm the configuration for the aws authentication method
        """
        xpath = "//div[contains(@class,'teer-checkbox')]"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __get_stack_url(self):
        """
        get the stack url on the page
        Returns:
            (str) stack url
        """
        path = "//a[contains(text(),'Launch the CloudFormation Stack')]"
        return self.__driver.find_element(By.XPATH, path).get_attribute('href')

    @PageService()
    def __create_aws_metallic_role(self):
        """
        method to execute the stack on the aws cloud platform
        Returns:
            None
        """
        stack_url = self.__get_stack_url()
        stack_params = parse_qs(urlparse(stack_url).fragment)
        templateUrl = stack_params['/stacks/quickcreate?templateURL'][0]
        capability = ['CAPABILITY_NAMED_IAM']
        hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
        stack_inputs = dict()
        stack_inputs['StackName'] = stack_params['stackName'][0]
        stack_inputs['TemplateURL'] = templateUrl
        stack_inputs['Capabilities'] = capability
        stack_inputs['parameters'] = []
        if 'ExternalId' in stack_url:
            external_id_info = {
                'ParameterKey' : 'ExternalId',
                'ParameterValue' : stack_params['param_ExternalId'][0]
            }
            stack_inputs['parameters'].append(external_id_info)
        if 'MetallicARN' in stack_url:
            arn_info = {
                'ParameterKey': 'MetallicARN',
                'ParameterValue': stack_params['param_MetallicARN'][0]
            }
            stack_inputs['parameters'].append(arn_info)
        if hypervisor_helper.create_stack(stack_inputs):
            self.metallic_helper.stacks_created.append(stack_inputs['StackName'])

    @PageService()
    def __aws_hosted_infra_configuration(self):
        """
        configure stacks for aws hosted infra configuration
        """
        hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
        hypervisor_helper.switch_to_admin_access()
        self.__create_aws_metallic_role()
        stack_details = hypervisor_helper.get_stack_details('MetallicTenantRole')
        for output_value in stack_details:
            if output_value['OutputKey'] == 'ExternalId':
                self.metallic_options.aws_external_id = output_value['OutputValue']
            if output_value['OutputKey'] == 'IAMRole':
                self.metallic_options.aws_role_arn = output_value['OutputValue']
        self.metallic_options.hyp_credential_name = 'Metallic hosted infra creds'
        self.metallic_options.hyp_credential_name = self.metallic_options.hyp_credential_name + \
                                                    self.metallic_options.unique_param
        data_dict = {
            'credential_name': self.metallic_options.hyp_credential_name,
            'description': "credentials created via automation for aws hosted infra",
            'role_arn': self.metallic_options.aws_role_arn,
            'external_id': self.metallic_options.aws_external_id
        }
        self.__wizard.click_icon_button_by_title("Create new")
        self.metallic_helper.create_credential_object(data_dict)

    @PageService()
    def __aws_cross_account_configuration(self):
        """
        configure stacks for cross account configuration
        Returns:
            None
        """
        hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
        if not self.metallic_options.aws_admin_account_configured:
            hypervisor_helper.switch_to_admin_access()
            self.metallic_options.aws_authentication_type = "IAM Role"
            self.select_authentication_method()
            self.__create_aws_metallic_role()
            self.metallic_options.aws_authentication_type = "STS assume role with IAM policy"
            self.select_authentication_method()
            self.__create_aws_metallic_role()
            self.metallic_options.aws_admin_role_arn = hypervisor_helper.get_role('MetallicAdminRole').arn
        else:
            if not self.metallic_options.aws_admin_role_arn:
                hypervisor_helper.switch_to_admin_access()
                self.metallic_options.aws_admin_role_arn = hypervisor_helper.get_role('MetallicAdminRole').arn
            hypervisor_helper.switch_to_tenant_access()
            self.metallic_options.aws_authentication_type = 'IAM Role'
            self.select_authentication_method()
            self.__create_aws_metallic_role()
            self.metallic_options.aws_authentication_type = "STS assume role with IAM policy"
            self.select_authentication_method()
        self.metallic_options.aws_role_arn = hypervisor_helper.get_role('MetallicRole').arn
        hypervisor_helper.add_arn_to_role(role_name='MetallicRole', role_arn=self.metallic_options.aws_admin_role_arn)