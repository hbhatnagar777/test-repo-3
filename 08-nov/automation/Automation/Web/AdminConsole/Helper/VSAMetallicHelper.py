# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be used as utility
 for Metallic Pages

"""
import time
import threading
from cvpysdk.organization import Organization
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.Common.exceptions import (
    CVWebAutomationException
)
from .LoadModule import load_module
from selenium.webdriver.common.by import By
from AutomationUtils import constants
from AutomationUtils import logger
from AutomationUtils import config
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils.OptionsHelper import VSAMetallicOptions
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from Web.AdminConsole.Hub.constants import HubServices, CCVMKubernetesTypes
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components import page_container, wizard
from Web.AdminConsole.Hub.utils import Utils
from urllib.parse import urlparse, parse_qs
import base64

from ..Components.dialog import RModalDialog
from Install.install_helper import InstallHelper


class VSAMetallicHelper:
    """
    class for all the common methods that can be used in
    """
    _thread_local = threading.local()

    @staticmethod
    def getInstance(admin_console, tcinputs=None, commcell_info=None, company=None):
        """ Static access method. """
        if not hasattr(VSAMetallicHelper._thread_local, 'instance'):
            VSAMetallicHelper(admin_console, tcinputs, commcell_info=commcell_info, company=company)
        return VSAMetallicHelper._thread_local.instance

    @staticmethod
    def resetInstance():
        """ Reset the singleton instance to None. """
        del VSAMetallicHelper._thread_local.instance

    def __init__(self, admin_console, tcinputs=None, commcell_info=None, company=None):

        if hasattr(VSAMetallicHelper._thread_local, 'instance'):
            raise CVWebAutomationException("it is a singleton class, use getInstance class method")
        else:
            self.__admin_console = admin_console
            self.__driver = admin_console.driver
            self.__commcell = commcell_info.get('commcell', None) if commcell_info else None
            self.__commcell_info = commcell_info
            self.log = logger.get_log()
            self.metallic_options = VSAMetallicOptions(tcinputs)
            self.service = HubServices.vm_kubernetes
            self.app_type = None
            self.hub = None
            self.hub_dashboard = None
            self.config = config.get_config()
            self.utils = Utils(self.__admin_console)
            self.stacks_created = []
            self.hypervisor_helper_obj = None
            self.company = company
            self.organization = None
            self.hypervisor_creation_wizard = None
            VSAMetallicHelper._thread_local.instance = self

    def get_commcell(self):
        return self.__commcell

    @PageService()
    def configure_metallic(self):
        """
        method that starts the metallic configuration for VSA
        Returns:
            None
        """
        for app_type in CCVMKubernetesTypes:
            if self.metallic_options.app_type.lower() == app_type.value.lower():
                self.app_type = app_type
                break

        self.hub_dashboard = Dashboard(self.__admin_console, self.service, self.app_type)
        hypervisor_wizard = wizard.Wizard(adminconsole=self.__admin_console, title='Configure Hypervisor')
        self.hub_dashboard.click_get_started()
        self.hub_dashboard.choose_service_from_dashboard()

        if self.hub:
            self.hub_dashboard.click_new_configuration()
            self.hub_dashboard.request_to_trial()
            self.close_popup_out_side_react_frame()
        else:
            self.navigator = self.__admin_console.navigator
            virtualization_page_object = page_container.PageContainer(admin_console=self.__admin_console)
            virtualization_page_object.access_page_action(name='Add hypervisor')
            hypervisor_wizard.select_radio_card(text=self.app_type.value)
            hypervisor_wizard.click_next()
        hypervisor_wizard = wizard.Wizard(adminconsole=self.__admin_console)
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
            if not self.metallic_options.BYOS:
                hypervisor_wizard.select_radio_card(text='Back up using Commvault Cloud Infrastructure')
            else:
                hypervisor_wizard.select_radio_card(text='Back up using the gateway(s)')
        if "Express configuration" in hypervisor_wizard.get_tile_content() and \
                self.metallic_options.app_type.lower() == CCVMKubernetesTypes.azure_vm.lower():
            hypervisor_wizard.click_next()
            hypervisor_wizard.select_radio_card(text="Custom configuration")
        hypervisor_wizard.click_next()
        self.auto_config()

    @PageService()
    def configure_metallic_vm_group(self):
        """
        configure vm-group for a hypervisor
        """
        for app_type in CCVMKubernetesTypes:
            if self.metallic_options.app_type.lower() == app_type.value.lower():
                self.app_type = app_type
                break

        self.hub_dashboard = Dashboard(self.__admin_console, self.service, self.app_type)
        virtualization_page_object = page_container.PageContainer(admin_console=self.__admin_console)
        virtualization_page_object.access_page_action(name='Add VM group')
        vm_group_wizard = wizard.Wizard(adminconsole=self.__admin_console, title='Add VM Group')
        vm_group_wizard.select_radio_card(text=self.app_type.value)
        vm_group_wizard.click_next()
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
            if not self.metallic_options.BYOS:
                vm_group_wizard.select_radio_card(text='Back up using Metallic Infrastructure')
            else:
                vm_group_wizard.select_radio_card(text='Back up using the gateway(s)')
        vm_group_wizard.click_next()
        self.auto_config()

    @PageService(react_frame=False)
    def close_popup_out_side_react_frame(self):
        """
        close popup outside react frame and switch back to react frame
        """
        if self.__admin_console.check_if_entity_exists("xpath", "//button[contains(@aria-label,'Close')]"):
            try:
                self.__driver.find_element(By.XPATH, "//button[contains(@aria-label,'Close')]").click()
                self.__admin_console.wait_for_completion()
            except Exception as exp:
                self.log.warning(exp)
                self.log.warning("Nothing to close")
        self.switch_to_react_frame()

    @PageService()
    def switch_to_react_frame(self):
        """
        method to switch to react frame
        """
        self.log.info("switch to react frame")

    def auto_config(self):
        """
        method to help intiate classes automatically based on the page currently it is working on
        Returns:

        """
        self.hypervisor_creation_wizard = wizard.Wizard(adminconsole=self.__admin_console)
        self.hypervisor_helper_obj = self.create_hypervisor_helper()
        self.files_path = '\\Web\\AdminConsole\\Hub\\CCVMKubernetes'
        move_forward = True
        prev_step = None
        while move_forward:
            current_step = self.hypervisor_creation_wizard.get_active_step()
            if prev_step == current_step:
                self.log.exception(f"executing same tab again : {current_step}")
                raise Exception(f"executing same tab multiple times : {current_step}")
            else:
                prev_step = current_step
            # self.filter_html_source()
            if current_step.lower() == "backup gateway":
                self.navigate_to_backup_gateway()
            elif current_step.lower() == 'region':
                self.navigate_to_region_selection()
            elif current_step.lower() in ['configure iam permission', 'configure permissions', 'iam role']:
                self.navigate_to_config_access_permission()
            elif current_step.lower() == 'hyper-v proxy access':
                self.navigate_to_hyperv_proxy_access()
            elif current_step.lower() in ['hypervisor connection', 'cloud account', 'hypervisor', 'azure application']:
                self.navigate_to_hypervisor_connection()
            elif current_step.lower() in ('select vm content', 'add vm group'):
                self.navigate_to_vm_content()
            elif current_step.lower() == "local storage":
                self.navigate_to_local_storage()
            elif current_step.lower() == "cloud storage":
                self.navigate_to_cloud_storage()
            elif current_step.lower() == "plan":
                self.navigate_to_select_plan()
            elif current_step.lower() == "summary":
                self.navigate_to_summary()
                move_forward = False
            else:
                raise CVWebAutomationException("Incorrect Tab")
        self.log.info("Configuration finished successfully")

    def navigate_to_backup_gateway(self):
        backup_gateway = load_module(
            'BackupGateway',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        backup_gateway.BackupGateway(self.hypervisor_creation_wizard, self.__admin_console,
                                     self.metallic_options, self.__commcell_info)

    def navigate_to_region_selection(self):
        region_selection = load_module(
            'RegionSelection',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        region_selection.RegionSelection(self.hypervisor_creation_wizard,
                                         self.__admin_console, self.metallic_options)

    def navigate_to_config_access_permission(self):
        config_permission = load_module(
            'ConfigureIAMRole',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        config_permission.ConfigIAMRole(self.hypervisor_creation_wizard,
                                        self.__admin_console, self.metallic_options,
                                        self.__commcell_info)

    def navigate_to_hyperv_proxy_access(self):
        hyperv_proxy_access = load_module(
            'ProxyAccess',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        hyperv_proxy_access.ProxyAccess(self.hypervisor_creation_wizard,
                                        self.__admin_console, self.metallic_options,
                                        self.__commcell_info)

    def navigate_to_hypervisor_connection(self):
        hypervisor_connection = load_module(
            'ConfigureHypervisor',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        hypervisor_connection.ConfigureHypervisor(self.hypervisor_creation_wizard,
                                                  self.__admin_console, self.metallic_options,
                                                  self.__commcell_info)

    def navigate_to_vm_content(self):
        vm_content = load_module(
            'VMContentSelection',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        vm_content.VMContentSelection(self.hypervisor_creation_wizard,
                                      self.__admin_console, self.metallic_options)

    def navigate_to_local_storage(self):
        local_storage = load_module(
            'LocalStorage',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        local_storage.LocalStorage(self.hypervisor_creation_wizard,
                                   self.__admin_console, self.metallic_options)

    def navigate_to_cloud_storage(self):
        if not self.metallic_options.skip_cloud_storage:
            cloud_storage = load_module(
                'CloudStorage',
                constants.AUTOMATION_DIRECTORY +
                self.files_path
            )
            cloud_storage.CloudStorage(self.hypervisor_creation_wizard,
                                       self.__admin_console, self.metallic_options)

        else:
            self.hypervisor_creation_wizard.enable_toggle('Only use on-premises storage')
            self.hypervisor_creation_wizard.click_next()

    def navigate_to_select_plan(self):
        storage_plan = load_module(
            'StoragePlan',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        storage_plan.StoragePlan(self.hypervisor_creation_wizard,
                                 self.__admin_console, self.metallic_options)

    def navigate_to_summary(self):
        summary = load_module(
            'Summary',
            constants.AUTOMATION_DIRECTORY +
            self.files_path
        )
        summary.Summary(self.hypervisor_creation_wizard,
                        self.__admin_console, self.metallic_options)

    @PageService()
    def create_credential_object(self, data_dict):
        """

        Args:
            data_dict:

        Returns:

        """
        dialog = RModalDialog(self.__admin_console, title='Add credential')
        dialog.fill_text_in_field(element_id='name',
                                  text=data_dict.get('credential_name', 'auto_cred_obj'))
        if data_dict.get('tenancy_ocid'):
            dialog.fill_text_in_field(element_id='tenancyOCID', text=data_dict.get('tenancy_ocid'))
        if data_dict.get("user_ocid"):
            dialog.fill_text_in_field(element_id='userOCID', text=data_dict.get('user_ocid'))
        if data_dict.get("username"):
            dialog.fill_text_in_field(element_id='userName', text=data_dict.get('username'))
        if data_dict.get("userAccount"):
            dialog.fill_text_in_field(element_id='userAccount', text=data_dict.get('userAccount'))
        if data_dict.get("fingerprint"):
            dialog.fill_text_in_field(element_id='fingerprint', text=data_dict.get('fingerprint'))
        if data_dict.get("password"):
            dialog.fill_text_in_field(element_id='password', text=data_dict.get('password'))
        if data_dict.get("private_key_path"):
            dialog.submit_file(element_xpath="//input[@name='fileInput']",
                               file_location=data_dict.get('private_key_path'))
        if data_dict.get('tenant_id'):
            dialog.fill_text_in_field(element_id='tenantId', text=data_dict.get('tenant_id'))
        if data_dict.get('application_id'):
            dialog.fill_text_in_field(element_id='applicationId', text=data_dict.get('application_id'))
        if data_dict.get('application_password'):
            dialog.fill_text_in_field(element_id='applicationSecret', text=data_dict.get('application_password'))
        if data_dict.get("private_key_password"):
            dialog.fill_text_in_field(element_id='privateKeysPassword', text=data_dict.get('private_key_password'))
        if data_dict.get("role_arn"):
            dialog.fill_text_in_field(element_id='roleArn', text=data_dict.get('role_arn'))
        if data_dict.get("external_id"):
            dialog.fill_text_in_field(element_id='externalId', text=data_dict.get('external_id'))
        dialog.fill_text_in_field(element_id='description',
                                  text=data_dict.get('description', 'creds created through automation'))
        dialog.click_submit()
        time.sleep(30)
        self.log.info("sleeping for 30 sec after submitting")

    @WebAction()
    def wait_for_spinners(self):
        """
        wait for to load the spinners on the page
        Returns:
            None
        """
        li = self.__driver.find_elements(By.XPATH, "//mdb-spinner[@class='ng-star-inserted']")
        while len(li) != 0:
            time.sleep(10)
            li = self.__driver.find_elements(By.XPATH, "//mdb-spinner[@class='ng-star-inserted']")
        return

    @PageService()
    def wait_for_client_job_completion(self, client):
        """
        method to wait till the any job running for the given client completes
        Args:
            client:     (str)   name of the client
        """
        admin_page = self.__admin_console.navigator
        admin_page.navigate_to_hypervisors()
        self.__driver.refresh()
        hyp_obj = Hypervisors(self.__admin_console)
        hyp_obj.action_jobs(client)
        job_object = Jobs(self.__admin_console)
        job_object.access_active_jobs()
        jobs = job_object.get_job_ids(active_jobs=True)
        if len(jobs) > 0:
            self.log.info("waiting for the completion of current running job " + str(jobs[0]))
            job_object.job_completion(job_id=jobs[0])
        else:
            self.log.info("no jobs is running currently for the hypervisor")

    @WebAction()
    def click_next(self):
        """
        click next button on the page
        Returns:

        """
        self.wait_for_spinners()
        self.__admin_console.click_button("Next")
        self.wait_for_spinners()

    @WebAction()
    def click_cancel(self):
        """
        click cancel button on the page
        Returns:

        """
        self.__admin_console.click_button("Cancel")

    def filter_html_source(self):
        """
        checks the page source for the do not see company

        Returns:
            html source which contains the values mentioned above
        """
        page_source = self.__driver.page_source
        import re
        pattern = re.compile('([^\s]*(donotsee)[^\s]*)')
        li = re.findall(pattern=pattern, string=page_source)
        try:
            if len(li) != 0:
                raise Exception
        except Exception as exp:
            self.log.info("found donotsee values")
            self.log.info(li)
            self.log.exception(exp)

    @staticmethod
    def encode_zip_file(zip_file_path):
        with open(zip_file_path, 'rb') as file:
            file_content = file.read()
        encoded_file = base64.b64encode(file_content).decode('ascii')
        return encoded_file

    def cleanup_stacks(self):
        """
        clean up the stack created during metallic automation
        """
        for stack in self.stacks_created:
            if not self.hypervisor_helper_obj:
                self.hypervisor_helper_obj = self.create_hypervisor_helper()
            try:
                self.hypervisor_helper_obj.delete_stack(stack)
                self.log.info(f"successfully deleted the stack : {stack}")
            except Exception as exp:
                self.log.info(f"failed to delete the stacks : {stack}")
                self.log.warning(exp)

    def get_company_organization(self):
        if not self.organization:
            self.organization = Organization(self.__commcell, self.company)
        return self.organization

    def create_hypervisor_helper(self):
        """
        connection_details : dict() containing the information required to Log in to the hypervisor
        return: (obj) Hypervisor Helper object
        """
        if self.hypervisor_helper_obj:
            return self.hypervisor_helper_obj
        else:
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.oci.value.lower():
                oci_config = {
                    "oci_user_id": self.config.Virtualization.oci.user,
                    "oci_private_file_name": self.config.Virtualization.oci.key_file,
                    "oci_finger_print": self.config.Virtualization.oci.fingerprint,
                    "oci_tenancy_id": self.config.Virtualization.oci.tenancy,
                    "oci_region_name": self.config.Virtualization.oci.region,
                    "oci_private_key_password": self.config.Virtualization.oci.oci_private_key_password
                }
                self.hypervisor_helper_obj = Hypervisor(server_host_name=None, user_name=oci_config,
                                                        password=oci_config,
                                                        instance_type=hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.
                                                        value.lower(),
                                                        commcell=self.__commcell,
                                                        host_machine=None)
            elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.value.lower():
                self.hypervisor_helper_obj = Hypervisor(server_host_name=None, user_name=None, password=None,
                                                        instance_type=hypervisor_type.AMAZON_AWS.value.lower(),
                                                        commcell=self.__commcell, host_machine=None,
                                                        **{'is_metallic': True})
            return self.hypervisor_helper_obj

    def cleanup_metallic_instance_on_client(self, machine_details):
        """
        clients_info : dict()
        format
        {
            name : (str),
            username : (str),
            password : (str),   (for windows machine)
            key_filename: (str) (for linux machine)
            instance_name : (str) (optional, by default it will be 'Instance001')
        }
        """
        machine_object = Machine(machine_name=machine_details.get('name'),
                                 commcell_object=self.__commcell,
                                 username=machine_details.get('username'),
                                 password=machine_details.get('password', None),
                                 key_filename=machine_details.get('key_filename', None))
        try:
            install_helper = InstallHelper(commcell=self.__commcell, machine_obj=machine_object)
            install_helper.uninstall_client()
            self.log.info("Cleaned up instance")
        except Exception as exp:
            self.log.warning("failed to uninstall client with the below exception")
            self.log.exception(exp)

    def update_gateway(self, gateway_name):
        """
        update the backup gateway to the latest sp
        Args:
            gateway_name: name of the gateway
        """
        try:
            self.__commcell.refresh()
            client = self.__commcell.clients.get(gateway_name)
        except Exception as exp:
            self.log.warning(exp)
            self.log.info("Retrying after 2 mins")
            time.sleep(120)
            self.__commcell.refresh()
            client = self.__commcell.clients.get(gateway_name)
        update_job_object = client.push_servicepack_and_hotfix(reboot_client=True)
        self.log.info(f'update job for the client : {gateway_name} : {update_job_object.job_id} is in progress')
        self.log.info("waiting for the job completion")
        update_job_object.wait_for_completion()
        time.sleep(60)
