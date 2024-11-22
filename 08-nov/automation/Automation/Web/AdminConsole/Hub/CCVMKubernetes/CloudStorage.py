# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Cloud Storage Tab on Metallic

"""
import time
from selenium.common.exceptions import NoSuchElementException
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.AdminConsole.Hub.constants import CCVMKubernetesTypes
from cvpysdk.policies.storage_policies import StoragePolicies, StoragePolicy, StoragePolicyCopy
from Web.Common.page_object import (
    PageService
)


class CloudStorage:
    """
    Class For Cloud Storage Page
    """

    def __init__(self, wizard, admin_console, metallic_options):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.metallic_helper = VSAMetallicHelper.getInstance(admin_console)
        self.log = self.__admin_console.log
        self.__wizard = wizard
        self.modal_dialog = None
        self.metallic_options = metallic_options
        self.commcell = self.metallic_helper.get_commcell()
        self.config()
        time.sleep(30)
        try:
            self.disable_compliance_for_mrr_storage()
        except Exception as exp:
            self.log.exception(exp)

    def disable_compliance_for_mrr_storage(self):
        if 'Air Gap Protect' in self.metallic_options.cloud_storage_account:
            storage_policies = StoragePolicies(self.commcell)
            all_policies = storage_policies.all_storage_policies
            policy_name = list(all_policies.keys())[0]
            storage_policy = StoragePolicy(self.commcell, policy_name)
            copy_name = list(storage_policy.copies.keys())[0]
            copy = StoragePolicyCopy(self.commcell, policy_name, copy_name)
            copy.disable_compliance_lock()

    def __get_metallic_option_value(self, name):
        """Get the value of the property from metallic options"""

        return eval(f"self.metallic_options.{name}")

    def __start_trial(self):
        """Start Trial for Metallic Recovery Reserve"""
        try:
            self.modal_dialog.click_button_on_dialog(text='Start trial')
        except (NoSuchElementException, IndexError) as e:
            return
        self.__admin_console.wait_for_completion()
        trial_dialog = RModalDialog(self.__admin_console, "Successfully created a trial subscription")
        trial_dialog.click_button_on_dialog(text="Close")

    def config(self):
        if self.metallic_options.existing_storage_cloud:
            self.select_previously_configured_cloud_storage()
        elif not self.metallic_options.keep_only_on_premise:
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
                self.configure_aws_storage()
            else:
                self.configure_new_cloud_storage()
        else:
            self.keep_only_on_premise()
        if self.metallic_options.secondary_storage_cloud:
            self.select_secondary_copy_cloud_storage()
        self.__wizard.click_next()

    @PageService()
    def configure_aws_storage(self):
        """
        method to configure aws storage in the hub
        Returns:
            None
        """
        retry = 2
        modal_dialog = None
        while retry > 0:
            try:
                self.__wizard.click_icon_button_by_title(title='Add')
                self.__admin_console.wait_for_completion(wait_time=600)
                modal_dialog = RModalDialog(self.__admin_console, title='Add cloud storage')
                modal_dialog.select_dropdown_values(drop_down_id='cloudType',
                                                    values=[self.metallic_options.cloud_storage_account])
                modal_dialog.fill_text_in_field(element_id='cloudStorageName', text=self.metallic_options.cloud_storage_name)
                modal_dialog.select_dropdown_values(drop_down_id='storageClass',
                                                    values=[self.metallic_options.aws_storage_class])
                modal_dialog.select_dropdown_values(drop_down_id='region', values=[self.metallic_options.region])
                modal_dialog.select_dropdown_values(drop_down_id='authentication',
                                                    values=[self.metallic_options.aws_authentication_type],
                                                    case_insensitive=True)
                retry = 0
            except Exception as exp:
                self.log.exception(exp)
                retry = retry - 1
                if modal_dialog:
                    modal_dialog.click_close()
                self.log.info("retrying the cloud storage creation again after 30 sec")
                time.sleep(30)

        if not self.metallic_options.aws_role_arn:
            hypervisor_helper = self.metallic_helper.create_hypervisor_helper()
            self.metallic_options.aws_role_arn = hypervisor_helper.get_role('MetallicRole').arn
        if not self.metallic_options.BYOS:
            self.select_existing_credential()
        else:
            modal_dialog.click_button_on_dialog(aria_label='Create new')
            data_dict = {
                'credential_name': "vsa aws admin creds auto" + self.metallic_options.unique_param,
                'description': "credentials crated via automation for aws",
                'role_arn': self.metallic_options.aws_role_arn
            }
            self.metallic_helper.create_credential_object(data_dict)
        modal_dialog.fill_text_in_field(element_id='mountPath', text=self.metallic_options.bucket_container)
        modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.retry_cloud_storage_submission(modal_dialog=modal_dialog)
        self.metallic_options.existing_storage_cloud = self.metallic_options.cloud_storage_name

    @PageService()
    def select_previously_configured_cloud_storage(self, primary_copy=True):
        """
        Select the previously existing storage option
        """
        cloud_storage_name = self.metallic_options.existing_storage_cloud
        dropdown_id = "metallicCloudStorageDropdown"
        if not primary_copy:
            cloud_storage_name = self.metallic_options.existing_secondary_cloud
            dropdown_id = "secondaryMetallicCloudStorageDropdown"
        self.log.info(f"Selecting existing cloud storage named {self.metallic_options.existing_storage_cloud}")
        self.__wizard.select_drop_down_values(
            id=dropdown_id, values=[cloud_storage_name]
        )

    @PageService()
    def configure_new_cloud_storage(self, primary_copy=True):
        """

        Args:
            primary_copy    (bool)  :  Configure options for primary copy or secondary copy

        Returns:
            None
        """

        prefix = ""
        if not primary_copy:
            prefix = "secondary_"
        retry = 2
        while retry > 0:
            try:
                self.log.info("Configuring new cloud storage")
                self.__wizard.click_add_icon(index=0 if primary_copy else 1)
                self.modal_dialog = RModalDialog(self.__admin_console, title='Add cloud storage')
                try:
                    self.modal_dialog.select_dropdown_values(
                        drop_down_id='cloudType', values=[self.__get_metallic_option_value(prefix + "cloud_storage_account")]
                    )
                except Exception:
                    self.__driver.switch_to.default_content()
                    self.__driver.switch_to.frame("cc-iframe")
                    self.modal_dialog.select_dropdown_values(
                        drop_down_id='cloudType', values=[self.__get_metallic_option_value(prefix + "cloud_storage_account")]
                    )
                retry = 0
            except Exception as exp:
                self.log.exception(exp)
                retry = retry - 1
                self.log.info("retrying the cloud storage dialog options after 30 sec")
                time.sleep(30)
                if self.modal_dialog:
                    self.modal_dialog.click_close()
        if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.hyper_v.value.lower():
            self.__start_trial()
            self.modal_dialog.select_dropdown_values(
                drop_down_id='offering', values=[self.__get_metallic_option_value(prefix + "cloud_storage_provider")]
            )
            self.modal_dialog.select_dropdown_values(
                drop_down_id='storageClass', values=[self.__get_metallic_option_value(prefix + "cloud_storage_tier")]
            )
            self.__start_trial()
            self.modal_dialog.select_dropdown_values(
                drop_down_id='region', values=[self.__get_metallic_option_value(prefix + "cloud_storage_region")]
            )
        elif 'Air Gap Protect' in self.__get_metallic_option_value(prefix + "cloud_storage_account"):
            if self.metallic_options.app_type.lower() != CCVMKubernetesTypes.vmware.value.lower():
                self.__start_trial()
            self.modal_dialog.select_dropdown_values(
                drop_down_id='offering', values=[self.__get_metallic_option_value(prefix + "cloud_storage_provider")]
            )
            self.modal_dialog.select_dropdown_values(
                drop_down_id='storageClass', values=[self.__get_metallic_option_value(prefix + "cloud_storage_tier")]
            )
            self.modal_dialog.select_dropdown_values(
                drop_down_id='region', values=[self.__get_metallic_option_value(prefix + "cloud_storage_region")]
            )
            if self.metallic_options.app_type.lower() in [CCVMKubernetesTypes.vmware.value.lower(),
                                                          CCVMKubernetesTypes.nutanix.value.lower()]:
                self.__start_trial()
        else:
            self.modal_dialog.fill_text_in_field(
                element_id='cloudStorageName', text=self.__get_metallic_option_value(prefix + "cloud_storage_name")
            )
            if self.metallic_options.app_type.lower() == CCVMKubernetesTypes.oci.lower():
                compartment = self.metallic_helper.hypervisor_helper_obj. \
                    get_compartment_details(compartment_id=self.metallic_options.oci_policy_compartment)
                self.modal_dialog.fill_text_in_field('configureCloudLibrary.CompartmentName', compartment.name)
                self.modal_dialog.fill_text_in_field('mountPath', self.metallic_options.bucket_container)
            elif self.metallic_options.app_type.lower() == CCVMKubernetesTypes.amazon.lower():
                self.__wizard.select_dropdown_values(id='region', values=[self.metallic_options.region])
                self.__wizard.select_dropdown_values(id='authentication',
                                                     text=self.metallic_options.aws_authentication_type)
                self.__wizard.select_dropdown_values(id='arnRole', text=self.metallic_options.aws_role_arn)
                self.__wizard.select_dropdown_values(id='mountPath', text=self.metallic_options.bucket_container)
                self.__wizard.select_dropdown_values(id='storageClass',
                                                     values=[self.metallic_options.aws_storage_class])
            else:
                self.__wizard.click_icon_button_by_label('Create new')
                self.__wizard.fill_text_in_field(
                    id='credentialName', text=self.__get_metallic_option_value(prefix + "storage_credential_name")
                )
                self.__wizard.fill_text_in_field(
                    id='userName', text=self.__get_metallic_option_value(prefix + "storage_credential_account")
                )
                self.__wizard.fill_text_in_field(
                    id='password', text=self.__get_metallic_option_value(prefix + "storage_credential_password")
                )
        self.modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.retry_cloud_storage_submission(modal_dialog=self.modal_dialog)

    @PageService()
    def select_secondary_copy_cloud_storage(self):
        """Configure secondary copy for cloud storage location
        """
        if self.metallic_options.existing_secondary_cloud:
            self.select_previously_configured_cloud_storage(primary_copy=False)
        else:
            self.configure_new_cloud_storage(primary_copy=False)

    @PageService()
    def select_existing_credential(self):
        """
        select the previously existing credential
        """
        dialog = RModalDialog(self.__admin_console)
        dialog.select_dropdown_values(drop_down_id='savedCredential', values=[self.metallic_options.hyp_credential_name])

    def retry_cloud_storage_submission(self, modal_dialog):
        """
        retry submitting the cloud storage
        """
        try:
            title = modal_dialog.title()
            if title == 'Add cloud storage':
                self.log.info('sleeping for 2 min and retry storage submission')
                time.sleep(120)
                modal_dialog.click_submit()
                self.__admin_console.check_error_message()
        except Exception as exp:
            self.log.info("this is a soft error")
            self.log.warning(exp)

    @PageService()
    def keep_only_on_premise(self):
        """
        select keep only on on-premise option
        Returns:
            None
        """
        self.log.info("Selection to keep only on premise option")
        self.__wizard.enable_toggle(label=self.__admin_console.props["label.onlyOnPremiseStorageEnabled"])
