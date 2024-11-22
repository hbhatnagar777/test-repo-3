# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Backup Gateway Tab on Metallic

"""
import os
import time
from urllib.parse import urlparse, parse_qs

from AutomationUtils import constants, config
from AutomationUtils.machine import Machine
from VirtualServer.Deployment.deployment_helper import DeploymentHelper
from Install.install_custom_package import InstallCustomPackage
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from Web.AdminConsole.Hub.utils import Utils
from selenium.common.exceptions import NoSuchElementException
from Web.Common.exceptions import (
    CVWebAutomationException
)
from Web.Common.page_object import (
    PageService,
    WebAction
)


class BackupGateway:
    """
    Class for configure Backup GateWay Page
    """

    def __init__(self, wizard, admin_console, metallic_options, commcell_info=None):

        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__commcell = commcell_info.get('commcell', None) if commcell_info else None
        self.__commcell_info = commcell_info
        self.metallic_helper = VSAMetallicHelper.getInstance(admin_console, metallic_options, commcell_info)
        self.utils = Utils(admin_console)
        self.log = self.__admin_console.log
        self.metallic_options = metallic_options
        self.__wizard = wizard
        self.__dialog = RModalDialog(admin_console)
        self.auth_code = None
        self.download_path = None
        self.config_data = config.get_config()
        self.config()

    def config(self):

        if self.metallic_options.backup_gateway:
            self.existing_backup_gateway()
        else:
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
                self.configure_gateway()
            elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.oci.lower():
                self.configure_gateway()
            else:
                self.configure_new_gateway()
        self.__wizard.click_next()
        self.__admin_console.check_error_message()

    def configure_gateway(self):
        """
        function to configure oci gateway for metallic
        Returns:
            None
        """
        platforms = ['Windows', 'Linux']
        gateway = None
        dialog = None
        for platform in platforms:
            retry = 2
            while retry > 0:
                try:
                    self.__wizard.click_add_icon()
                    dialog = RModalDialog(admin_console=self.__admin_console, title='Add a new backup gateway')
                    dialog.select_dropdown_values(drop_down_id='platform', values=[platform])
                    dialog.select_dropdown_values(drop_down_id='storageRegion', values=[self.metallic_options.region])
                    self.log.info("wait for the generate link buttons")
                    time.sleep(15)
                    dialog.click_button_on_dialog(text='Generate link')
                    self.__admin_console.wait_for_completion()
                    retry = 0
                except Exception as exp:
                    self.log.exception(exp)
                    retry = retry - 1
                    if dialog:
                        dialog.click_close()
                    self.log.info("retrying this step again after 1 min")
                    time.sleep(60)

            self.log.info("waiting for 15 secs for the link generation")
            time.sleep(15)
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
                try:
                    stack_url = dialog.get_anchor_element_on_dialog(text='CloudFormation').get_attribute('href')
                except Exception:
                    self.log.info("waiting for 15 secs for the link generation")
                    time.sleep(15)
                    stack_url = dialog.get_anchor_element_on_dialog(text='CloudFormation').get_attribute('href')
                stack_output = self.execute_aws_gateway_stack(stack_url)
                if not stack_output:
                    raise Exception("Stack creation failed , please check the details on AWS Console")
                gateway = stack_output[0]['OutputValue'].split('.')[0] + ".testlab.commvault.com"
            elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.oci.lower():
                stack_url = dialog.get_anchor_element_on_dialog(text='Oracle Cloud Resource Stack').get_attribute('href')
                stack_output = self.execute_oci_gateway_stack(stack_url)
                for resource in stack_output['resources']:
                    if resource['type'] == 'oci_core_instance':
                        gateway = resource['instances'][0]['attributes']['display_name']
                        break
                gateway = 'BackupGateway-' + gateway
            dialog.click_button_on_dialog(text='OK')
            time.sleep(60)
            self.metallic_helper.update_gateway(gateway)
        if not gateway:
            self.log.warning("gateway is empty")
            raise Exception("gateway is empty after running stack")
        self.existing_backup_gateway(gateway=gateway)
        self.metallic_options.backup_gateway = gateway

    def execute_oci_gateway_stack(self, stack_url):
        """
        function to setup and execute oci stack for gateway creation
        Args:
            stack_url:

        Returns:
        """
        hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
        stack_params = parse_qs(urlparse(stack_url).query)
        zipUrl = stack_params['zipUrl'][0]
        import base64
        import requests
        encoded_file = base64.b64encode(requests.get(zipUrl).content).decode('ascii')
        stack_creation_data = dict()
        stack_creation_data['encoded_file'] = encoded_file
        if 'WindowsBackupGateway' in zipUrl:
            stack_creation_data['display_name'] = 'metallic automation windows backup gateway stack'
        else:
            stack_creation_data['display_name'] = 'metallic automation linux backup gateway stack'
        stack_creation_data['description'] = "backupgateway for oci automation for metallic onboarding test"
        stack_creation_data['compartment_id'] = self.metallic_options.oci_policy_compartment

        variables = dict()
        variables["tenancy_ocid"] = self.config_data.Virtualization.oci.tenancy
        variables["compartment_ocid"] = self.metallic_options.oci_policy_compartment
        variables["region"] = stack_params['region'][0]
        variables["data_size"] = '25TB'
        variables["authcode"] = self.metallic_helper.get_company_organization().auth_code
        variables["instance_compartment_ocid"] = self.metallic_options.oci_policy_compartment
        variables["nsg_compartment_ocid"] = self.config_data.Virtualization.oci.tenancy
        variables["availability_domain"] = self.config_data.Virtualization.oci.availability_domain
        variables["vcn_ocid"] = self.config_data.Virtualization.oci.vcn
        variables["subnet_ocid"] = self.config_data.Virtualization.oci.subnet
        if self.metallic_options.gateway_os_platform == 'Linux':
            text_file = open(self.config_data.Virtualization.oci.linux_gateway_pub_key, "r")
            data = text_file.read()
            text_file.close()
            variables["ssh_public_key"] = data
        stack_creation_data['variables'] = variables
        stack_info = hypervisor_helper.create_stack(stack_creation_data, delete_previous_existing=True)
        self.metallic_helper.stacks_created.append(stack_info.id)
        plan_job = hypervisor_helper.run_plan_job_for_stack(stack_id=stack_info.id)
        apply_job = hypervisor_helper.run_apply_job_for_stack(stack_id=stack_info.id, plan_job_id=plan_job.id)
        job_output = hypervisor_helper.get_stack_apply_job_output(apply_job.id)
        return job_output

    @WebAction()
    def execute_aws_gateway_stack(self, stack_url):
        """
        create required info to execute the statck on aws console
        Returns:
            stack output which contains hostname of the instance created
        """
        hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
        stack_params = parse_qs(urlparse(stack_url).fragment)
        templateUrl = stack_params['/stacks/quickcreate?templateURL'][0]
        stackName = stack_params['stackName'][0] + 'Auto'
        authCode = stack_params['param_AuthCode'][0]
        backup_gateway_package = stack_params['param_BackupGatewayPackage'][0]
        param_authentication = stack_params['param_Authentication'][0]

        capability = ['CAPABILITY_NAMED_IAM']
        parameters = []
        key_pair_name = \
            {
                'ParameterKey': 'KeyName',
                'ParameterValue': self.metallic_helper.config.Virtualization.aws_login_creds.key_pair_name
            }
        parameters.append(key_pair_name)
        vpc_id = \
            {
                'ParameterKey': 'VpcId',
                'ParameterValue': self.metallic_options.aws_vpc_id
            }
        parameters.append(vpc_id)
        AuthCode = \
            {
                'ParameterKey': 'AuthCode',
                'ParameterValue': authCode
            }
        parameters.append(AuthCode)
        aws_subnet_id = \
            {
                'ParameterKey': 'SubnetId',
                'ParameterValue': self.metallic_options.aws_subnet_id
            }
        parameters.append(aws_subnet_id)
        backup_gateway = \
            {
                'ParameterKey': 'BackupGatewayPackage',
                'ParameterValue': backup_gateway_package
            }
        parameters.append(backup_gateway)
        authentication_method = \
            {
                'ParameterKey': 'Authentication',
                'ParameterValue': param_authentication
            }
        parameters.append(authentication_method)
        stack_inputs = dict()
        stack_inputs['StackName'] = stackName
        stack_inputs['TemplateURL'] = templateUrl
        stack_inputs['Capabilities'] = capability
        stack_inputs['parameters'] = parameters
        stack_output = hypervisor_helper.create_stack(stack_inputs, delete_previous_existing=True)
        self.metallic_helper.stacks_created.append(stack_inputs['StackName'])
        return stack_output

    @PageService()
    def existing_backup_gateway(self, dropdown_id=None, gateway=None):
        """
        selects the existing backup gateway provided in the options
        Returns:    None

        """
        backup_gateway_name = self.metallic_options.backup_gateway
        gateway_dropdown_id = 'accessNodeDropdown'
        if gateway:
            backup_gateway_name = gateway
        if dropdown_id:
            gateway_dropdown_id = dropdown_id
        self.log.info(f"selecting existing backup gateway named {backup_gateway_name}")
        time.sleep(30)
        self.__wizard.click_refresh_icon()
        if self.metallic_options.app_type.lower() in [CCVMKubernetesTypes.vmware.lower(),
                                                      CCVMKubernetesTypes.nutanix.lower()] and \
                self.metallic_options.access_node_os != 'unix':
            backup_gateway_name = backup_gateway_name.split('.')[0]
        self.__wizard.select_drop_down_values(id=gateway_dropdown_id, values=[backup_gateway_name],
                                              partial_selection=True)
        time.sleep(30)

    @PageService()
    def configure_new_gateway(self):
        """
        configure new backup-gateway
        Returns:    None

        """
        self.log.info("Creating a new backup gateway")
        self.__download_gateway_exe()
        self.auth_code = self.metallic_helper.organization.auth_code
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.vmware.lower() and \
                self.metallic_options.access_node_os == 'unix':
            self.metallic_options.deploy_helper = DeploymentHelper(self.metallic_options.testcase,
                                                                   ova_path=self.download_path,
                                                                   is_metallic=True,
                                                                   auth_code=self.auth_code,
                                                                   services=['cvd', 'cvlaunchd', 'cvfwd', 'ClMgrS',
                                                                             'CvMountd'])
            self.metallic_options.deploy_helper.deploy()
            gateway_machine = {'remote_clientname': self.metallic_options.backup_gatewayname}
        else:
            gateway_machine = {
                'remote_clientname': self.metallic_options.backup_gatewayname,
                'remote_username': self.metallic_options.remote_username,
                'remote_userpassword': self.metallic_options.remote_userpassword
            }
            install_helper = InstallCustomPackage(self.__commcell, gateway_machine)
            if self.metallic_options.install_through_authcode:
                install_helper.install_custom_package(
                    full_package_path=self.download_path, authcode=self.auth_code)
            else:
                install_helper.install_custom_package(
                    self.download_path, self.__commcell_info['user'],
                    self.__commcell_info['password'])
        self.log.info("sleeping for 2 mins for the newly deployed gateway to be available")
        time.sleep(120)
        try:
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.hyper_v.lower():
                self.existing_backup_gateway(dropdown_id='mediaAgent',
                                             gateway=self.metallic_options.storage_backup_gateway)
            else:
                self.existing_backup_gateway(gateway=gateway_machine['remote_clientname'])
        except NoSuchElementException as exp:
            self.log.exception("Failed to register backup gateway with commcell")
            raise CVWebAutomationException(exp)
        finally:
            self.log.info("Successfully installed and registered the Backup Gateway.")
            try:
                self.controller_machine.delete_file(self.download_path)
            except Exception:
                self.log.warning('File not present')


    @WebAction()
    def __download_gateway_exe(self):
        """
         download the backup gateway software
         Returns:
               None
        """
        import socket
        self.controller_machine = Machine(socket.gethostname())
        local_temp = self.controller_machine.join_path(constants.TEMP_DIR, self.metallic_options.app_type.split()[0])
        if not os.path.exists(local_temp):
            os.makedirs(local_temp)
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.vmware.lower() and \
                self.metallic_options.access_node_os == 'unix':
            self.download_path = self.controller_machine.join_path(local_temp, "LinuxOnpremBackupGateway.ova")
        else:
            self.download_path = self.controller_machine.join_path(local_temp, "BackupGateway64.exe")
        try:
            self.controller_machine.delete_file(self.download_path)
        except Exception as exp:
            self.log.info("no path exists to delete with the given name {}".format(self.download_path))

        self.__wizard.click_add_icon()
        if self.metallic_options.app_type.lower() in [CCVMKubernetesTypes.vmware.lower(),
                                                      CCVMKubernetesTypes.nutanix.lower()]:
            if self.metallic_options.access_node_os == 'unix':
                self.__dialog.select_link_on_dialog(text="Linux (64-bit)")
            else:
                self.__dialog.select_link_on_dialog(text="Windows (64-bit)")
        else:
            self.__dialog.select_link_on_dialog(text="Download")
        time_taken = 0
        time.sleep(120)
        time_taken = time_taken + 2
        while not self.controller_machine.check_file_exists(self.download_path):
            if time_taken > 30:
                raise CVWebAutomationException("time out during the gateway package download")
            self.log.info(
                "-- Downloading the gateway since {} minutes. Sleeping for another 2 minutes --".format(time_taken))
            time.sleep(120)
            time_taken = time_taken + 2
        self.__dialog.click_close()
        self.log.info("gateway file downloaded successfully")
