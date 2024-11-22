# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to onboarding page in AdminConsole
StorageOnboarding : This class provides methods for storage related operations on onboarding pages

StorageOnboarding:

    select_backup_gateway()   --  Select gateway nodes

    click_next()         --  Click the next button

    backup_to_cloud_storage_only() --  Method to enable backup to cloud only on onboarding pages

    use_on_premises_storage_only() --  Method to enable use on premises storage only on onboarding pages

    enable_secondary_copy()        --   Method to enable toggle to allow creation of secondary copy

    select_local_storage()          --  select existing local storage

    add_local_storage()             --  configure new local storage

    select_cloud_storage()          --  select existing cloud storage

    add_cloud_storage()             --  configure new cloud storage

    select_plan()                   --  select  plan

    add_new_plan()                  --  add a new plan

"""

from Web.AdminConsole.Components.wizard import Wizard
import time
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService


class StorageOnboardingSaaS:

    def __init__(self, admin_console):
        """
        Args:

        admin_console(AdminConsole): adminconsole object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._admin_console.load_properties(self)
        self.__rdropdown = RDropDown(self._admin_console)
        self.__wizard = Wizard(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__rtable = Rtable(admin_console)
        self.__props = self._admin_console.props

    def __is_storage_selected(self, storage_name, drop_down_id):
        """
        Checks if the storage given is selected or not.

        Args :
            storage_name(list) : Storage names

            drop_down_id(str) : Drop down id to fetch values
        """
        selected_values = self.__rdropdown.get_selected_values(drop_down_id=drop_down_id, expand=False)
        if sorted(storage_name) == sorted(selected_values):
            return True
        else:
            return False

    @PageService()
    def select_backup_gateway(self, backup_gateways):
        """
        Select backup gateway.

        Args:
            backup_gateways (list of str): List of  backup gateway names
        """
        for backup_gateway in backup_gateways:
            self.__wizard.select_drop_down_values(id='accessNodeDropdown', values=[backup_gateway])

    @PageService()
    def click_next(self):
        """
        Click the next button
        """
        self.__wizard.click_next()

    @PageService()
    def backup_to_cloud_storage_only(self):
        """
        Method to enable backup to cloud only on onboarding pages
        """
        self.__wizard.enable_toggle(self.__props['label.onlyCloudBackupEnabled'], 1)

    @PageService()
    def use_on_premises_storage_only(self):
        """
        Method to enable use on premises storage only on onboarding pages
        """
        self.__wizard.enable_toggle(self.__props['label.onlyOnPremiseStorageEnabled'], 1)

    @PageService()
    def enable_secondary_copy(self):
        """
        Method to enable toggle to allow creation of secondary copy.
        """
        self.__wizard.enable_toggle(self.__props['label.secondaryCopy'], 1)

    @PageService()
    def select_local_storage(self, local_storage_name):
        """
        Select an existing local storage.

            Args:
                local_storage_name(str)     :   Local storage name to select
        """
        storage_names = [local_storage_name]
        drop_down_id = 'metallicLocalStorageDropdown'
        self.__wizard.select_drop_down_values(id=drop_down_id, values=storage_names)
        if not self.__is_storage_selected(storage_name=storage_names, drop_down_id=drop_down_id):
            raise Exception("Given storage is not selected:", local_storage_name)

    @PageService()
    def add_local_storage(self, local_storage_name, backup_location):
        """
        Configure new local storage
            Args:
                local_storage_name (str)    :    local storage name

                backup_location (dict)      :    Details of the backup location

                   Format: {'backup_gateway': 'sample_backup_gateway_name',
                            'backup_location': 'sample_backup_location',
                            'username': 'sample_username',
                            'password': 'sample_password'}

                    'backup_gateway' (str)         :    gateway machine name
                    'backup_location' (str)        :    local disk library path
                    'username' (str)               :    username for UNC storage path
                    'password' (str)               :    password for UNC storage path
        """
        media_agents = [backup_location['backup_gateway']]
        self.__wizard.click_add_icon()
        self.__dialog.fill_text_in_field(
            element_id='name', text=local_storage_name)
        self._admin_console.select_hyperlink(self.__props['action.add'])
        time.sleep(15)
        backup_location_dialog = RModalDialog(admin_console=self._admin_console,
                                              title=self._admin_console.props['Add_Path'])
        backup_location_dialog.select_dropdown_values(drop_down_id='mediaAgent', values=media_agents)
        if 'username' in backup_location and 'password' in backup_location:
            backup_location_dialog.select_radio_by_id(radio_id='networkRadioDisk')
            backup_location_dialog.fill_text_in_field(
                element_id='credential.userName', text=backup_location['username'])
            backup_location_dialog.fill_text_in_field(
                element_id='credential.password', text=backup_location['password'])
        backup_location_dialog.fill_text_in_field(element_id='path', text=backup_location['backup_location'])
        backup_location_dialog.click_button_on_dialog(text=self.__props['action.add'])
        time.sleep(30)
        self._admin_console.click_button(self.__props['action.save'])
        time.sleep(60)
        self._admin_console.check_error_message()

    @PageService()
    def select_cloud_storage(self, cloud_storage_name, addingSecondCloudStorage=False):
        """
        Select an existing cloud storage.
         Args:
                cloud_storage_name (str)    :    Name of the cloud storage to select

                addingSecondCloudStorage (bool)   :    False if selecting first cloud storage on Cloud Storage page
                                                       True if selecting second cloud storage on Cloud Storage page
        """
        storage_names = [cloud_storage_name]
        dropdown_id = 'metallicCloudStorageDropdown' if not addingSecondCloudStorage \
                        else 'secondaryMetallicCloudStorageDropdown'
        self.__wizard.select_drop_down_values(id=dropdown_id, values=storage_names)
        if not self.__is_storage_selected(storage_name=storage_names, drop_down_id=dropdown_id):
            raise Exception("Given storage is not selected:", cloud_storage_name)

    @PageService()
    def add_cloud_storage(self, cloud_storage_details, cloud_storage_name=None, addingSecondCloudStorage=0):
        """
        Add cloud storage configuration based on the cloud type.

        Args:
             cloud_storage_name (str): The name of the cloud storage.

             cloud_storage_details (dict):  Details required for configuration.
                                            Dictionary inputs change according to cloud_type.
                Format :   {'cloud_type': 'sample_cloud_type',
                            'storage_provider': 'sample_storage_provider',
                            'storage_class': 'sample_storage_class',
                            'region': 'sample_region'}

                Above is example dictionary for Air Gap Protect, secondary storage. Check UI for more information about
                required inputs for specific storage type.

                storage_provider (str): Storage provider name.

                cloud_type (str): Storage account name.

                region (str): Storage region.

                storage_class (str): Storage class.

                server_host (str): Server host address.

                authentication (str): Authentication type.

                saved_credential_name (str): Name of saved credentials.

                container (str): Container name.

            addingSecondCloudStorage (bool)   :    False if creating first cloud storage on Cloud Storage page
                                                    True if creating second cloud storage on Cloud Storage page

        """
        required_keys_mapping = {
            'Air Gap Protect': ['cloud_type', 'storage_provider', 'storage_class', 'region'],
            'Oracle Cloud Infrastructure Object Storage': ['cloud_type', 'storage_class', 'region',
                                                           'saved_credentials', 'bucket'],
            'Microsoft Azure Storage': ['cloud_type', 'storage_class', 'region', 'saved_credentials',
                                        'container'],
            'Amazon S3': ['cloud_type', 'storage_class', 'region', 'saved_credentials', 'bucket']
        }
        cloud_type = cloud_storage_details.get('cloud_type')
        if not cloud_type:
            raise ValueError("Missing 'cloud_type' in cloud storage details")
        index = 1 if addingSecondCloudStorage else 0
        required_keys = required_keys_mapping.get(cloud_type)

        if not required_keys:
            raise ValueError(f"Unsupported cloud_type: {cloud_type}")

        missing_keys = [key for key in required_keys if key not in cloud_storage_details]

        if missing_keys:
            raise ValueError(f"Missing required cloud storage details for {cloud_type}: {', '.join(missing_keys)}")
        if cloud_type == 'Air Gap Protect':
            self.__wizard.click_add_icon(index)
            self.__dialog.select_dropdown_values(drop_down_id='cloudType', values=[cloud_storage_details['cloud_type']])
            self.__dialog.select_dropdown_values(drop_down_id='offering',
                                                 values=[cloud_storage_details['storage_provider']])
            self.__dialog.select_dropdown_values(drop_down_id='storageClass',
                                                 values=[cloud_storage_details['storage_class']])
            try:
                self._admin_console.click_button_using_text("Start trial")
                self._admin_console.check_error_message()
                self._admin_console.click_button_using_text(value="Close")
            except BaseException:
                pass
            time.sleep(120)
            self.__dialog.select_dropdown_values(drop_down_id='region', values=[cloud_storage_details['region']])
            self._admin_console.click_button(self.__props['action.save'])
            time.sleep(120)
        else:
            self.__wizard.click_add_icon(index)
            self.__dialog.select_dropdown_values(drop_down_id='cloudType', values=[cloud_type])
            self.__dialog.fill_text_in_field("cloudStorageName", cloud_storage_name)
            self.__dialog.select_dropdown_values("storageClass", values=[cloud_storage_details['storage_class']])
            self.__dialog.select_dropdown_values("region", values=[cloud_storage_details['region']])
            if 'service_host' in cloud_storage_details:
                self.__dialog.fill_text_in_field("serviceHost", cloud_storage_details['service_host'])
            if 'authentication' in cloud_storage_details:
                self.__dialog.select_dropdown_values("authentication", values=[cloud_storage_details['authentication']])
            self.__dialog.select_dropdown_values('savedCredential',
                                                     values=[cloud_storage_details['saved_credentials']])
            if 'container' in cloud_storage_details:
                self.__dialog.fill_text_in_field("mountPath", cloud_storage_details['container'])
            else:
                self.__dialog.fill_text_in_field("mountPath", cloud_storage_details['bucket'])
            self.__dialog.click_submit()
            self._admin_console.check_error_message()

    @PageService()
    def select_plan(self, plan_name):
        """Select plan

            Args:

                plan_name (string): new plan name
        """
        self.__wizard.fill_text_in_field(id="searchPlanName", text=plan_name)
        self.__wizard.select_plan(plan_name)

    @PageService()
    def add_new_plan(self, plan_name, retention=None):
        """Add a new plan

            Args:

                plan_name (str)      :   plan name

                retention (dict) : Dict containing retention and backup frequency

                    Eg:    retention = { 'pri_ret_period': None,
                                         'pri_ret_unit': None,
                                         'sec_ret_period': None,
                                         'sec_ret_unit': None,
                                         'backup_frequency': None,
                                         'backup_frequency_unit': None}

                    For pri_ret_unit , sec_ret_unit allowed values are Day(s), Week(s), Month(s), Year(s), Infinite
        """
        self.__wizard.click_add_icon()
        self.__dialog.fill_text_in_field(
            element_id="planNameInputFld", text=plan_name)
        if retention:
            self.__dialog.enable_toggle(toggle_element_id='custom')
            if len(retention['pri_ret_period'].strip()):
                self.__dialog.fill_text_in_field(
                    element_id='retentionPeriod',
                    text=retention['pri_ret_period'])
                self.__dialog.select_dropdown_values(
                    drop_down_id='retentionPeriodUnit', values=[
                        retention['pri_ret_unit']])
            if len(retention['sec_ret_period'].strip()):
                self.__dialog.fill_text_in_field(
                    element_id='secondaryRetentionPeriod',
                    text=retention['sec_ret_period'])
                self.__dialog.select_dropdown_values(
                    drop_down_id='secondaryRetentionPeriodUnit', values=[
                        retention['sec_ret_unit']])
            if len(retention['backup_frequency'].strip()):
                self.__dialog.fill_text_in_field(
                    element_id='backupFrequency',
                    text=retention['backup_frequency'])
                self.__dialog.select_dropdown_values(
                    drop_down_id='backupFrequencyUnit', values=[
                        retention['backup_frequency_unit']])

        self.__dialog.fill_text_in_field(
            element_id="planNameInputFld", text=plan_name
        )
        self._admin_console.click_button(id=self.__props['action.save'])
        time.sleep(60)

    def current_onboarding_wizard_step(self):
        """
        Returns current active wizard step on onboarding pages
        """
        wizard = Wizard(adminconsole=self._admin_console)
        wizard_step = wizard.get_active_step()
        return wizard_step
