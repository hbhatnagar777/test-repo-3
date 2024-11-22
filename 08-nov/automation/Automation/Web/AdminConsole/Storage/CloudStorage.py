# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to cloud storage page in AdminConsole
CloudStorage : This class provides methods for cloud storage related operations

CloudStorage:

    add_cloud_storage()      --  adds a new cloud storage

    list_cloud_storage()     --  returns a list of all cloud storage

    select_cloud_storage()   --  opens a cloud storage

    action_delete()         --  removes a cloud storage

"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService, WebAction


class CloudStorage:
    """
    This class provides the function or operations that can be
    performed on the Cloud Storage Page of the Admin Console
    """

    def __init__(self, admin_console):
        """
        Initialization method for CloudStorage Class

            Args:
                admin_console (AdminConsole): AdminConsole object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = self.__admin_console.driver
        self.__props = self.__admin_console.props
        self.__table = Rtable(self.__admin_console)
        self.__dropdown = RDropDown(self.__admin_console)

    @PageService()
    def add_cloud_storage(self, cloud_storage_name, media_agent, cloud_type, server_host,
                          container, storage_class=None, saved_credential_name=None, username=None,
                          password=None, deduplication_db_location=None, region=None, auth_type=None, cred_details=None):
        """
        To add a new cloud storage

        Args:
            cloud_storage_name (str)    -- Name of the cloud storage to be created

            media_agent     (str)       -- Media agent to create storage on

            cloud_type      (str)       -- type of the cloud storage server

            server_host     (str)       -- cloud server host name

            container       (str)       -- container to be associated with the storage

            storage_class   (str)       --  storage class to be associated with the container

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            deduplication_db_location (str) -- local path for the deduplication db

            region          (str)       -- region of the cloud storage

            auth_type       (str)       -- type of authentication

            cred_details (dict) -- Dictionary containing attributes for saving creds as per auth_type
                Eg. - {'accountName':xyz, 'accessKeyId': xyz}

        **Note** MediaAgent should be installed prior, for creating a new storage,
                To use saved credentials it should be created prior using credential manager.
        """
        credentials_needed = True
        self.__table.access_toolbar_menu(self.__props['action.add'])
        self.__dropdown.select_drop_down_values(drop_down_id="cloudType", values=[cloud_type])
        self.__admin_console.fill_form_by_name("cloudStorageName", cloud_storage_name)
        self.__dropdown.select_drop_down_values(drop_down_id='mediaAgent', values=[media_agent])
        if storage_class:
            self.__dropdown.select_drop_down_values(drop_down_id="storageClass", values=[storage_class])
        if region:
            self.__dropdown.select_drop_down_values(drop_down_id="region", values=[region])
        if server_host:
            self.__admin_console.fill_form_by_id("serviceHost", server_host)
        if auth_type:
            self.__dropdown.select_drop_down_values(drop_down_id="authentication", values=[auth_type])

        if cloud_type == 'HPE Catalyst Storage':
            self.__admin_console.fill_form_by_id("loginName", username)
            self.__admin_console.fill_form_by_id("password", password)
            credentials_needed = False

        if cloud_type == "Microsoft Azure Storage" and auth_type == "IAM AD application":
            self.__admin_console.fill_form_by_id(element_id="loginName", value=cred_details.get("accountName"))

        if cloud_type == "Microsoft Azure Storage" and auth_type == "IAM VM role":
            credentials_needed = False
            self.__admin_console.fill_form_by_id(element_id="loginName", value=cred_details.get("accountName"))

        if credentials_needed:
            list_of_credentials = self.__dropdown.get_values_of_drop_down(drop_down_id='savedCredential')
            if saved_credential_name not in list_of_credentials:
                credential_div = "//label[contains(text(), 'Credentials')]/ancestor::div[3]"
                self.__admin_console.click_by_xpath(
                    f"{credential_div}//div[contains(@aria-label,'Create new')]//button")
                add_credential_dialog = RModalDialog(self.__admin_console, title='Add credential')
                add_credential_dialog.fill_text_in_field(element_id='name', text=saved_credential_name)

                if cloud_type == "Microsoft Azure Storage":
                    if auth_type == "Access key and Account name":
                        add_credential_dialog.fill_text_in_field(element_id='accountName',
                                                                 text=cred_details.get("accountName"))
                        add_credential_dialog.fill_text_in_field(element_id="accessKeyId",
                                                                 text=cred_details.get("accessKeyId"))
                        add_credential_dialog.click_submit()

                    elif auth_type == "IAM AD application":
                        add_credential_dialog.fill_text_in_field(element_id='tenantId', text=cred_details.get("tenantId"))
                        add_credential_dialog.fill_text_in_field(element_id='applicationId',
                                                                 text=cred_details.get("applicationId"))
                        add_credential_dialog.fill_text_in_field(element_id='applicationSecret',
                                                                 text=cred_details.get("applicationSecret"))
                        add_credential_dialog.click_submit()
            self.__dropdown.select_drop_down_values(drop_down_id='savedCredential', values=[saved_credential_name])

        self.__add_container_to_cloud_storage(container_name=container)

        if deduplication_db_location:
            self.__admin_console.select_hyperlink(self.__props['action.add'])

            # Use DDB specific RModalDialogs
            select_ddb_dialog = RModalDialog(self.__admin_console, title=self.__props['label.ddbPartitionPath'])
            select_ddb_dialog.select_dropdown_values(values=[media_agent], drop_down_id='mediaAgent')
            available_ddb_locations = self.__dropdown.get_values_of_drop_down(drop_down_id='ddbPartitionPath')
            if deduplication_db_location not in available_ddb_locations:
                select_ddb_dialog.click_button_on_dialog(aria_label='Create new', button_index=1)
                add_ddb_dialog = RModalDialog(self.__admin_console, title=self.__props['action.addPartition'])
                add_ddb_dialog.fill_text_in_field('ddbDiskPartitionPath', deduplication_db_location)
                add_ddb_dialog.click_submit()
            select_ddb_dialog.select_dropdown_values(values=[deduplication_db_location],
                                                     drop_down_id='ddbPartitionPath')

            self.__admin_console.click_button('Add')
        elif cloud_type != 'HPE Catalyst Storage':
            self.__admin_console.click_by_xpath("//span[contains(text(), 'Use deduplication')]")
        self.__admin_console.click_button(self.__props['action.save'])
        self.__admin_console.check_error_message()

    @PageService()
    def list_cloud_storage(self, fetch_all=False):
        """
        Get all the cloud storage in the form of a list

            Returns:
               list --  all cloud storage
        """
        try:
            return self.__table.get_column_data(self.__props['Name'], fetch_all=fetch_all)
        except ValueError:
            return []

    @PageService()
    def select_cloud_storage(self, cloud_storage):
        """
        selects the cloud storage with the given name

        Args:
            cloud_storage    (str)   -- Name of the cloud storage to be opened
        """
        self.__table.access_link(cloud_storage)

    @PageService()
    def action_delete(self, cloud_storage):
        """
        Deletes the cloud storage with the given name

        Args:
            cloud_storage (str) - name of the storage to be removed
        """
        self.__table.access_action_item(cloud_storage, self.__props['label.globalActions.delete'])
        self.__admin_console.click_button(self.__props['label.yes'])
        self.__admin_console.check_error_message()
        self.__table.clear_search()

    def modify_retention_on_worm_cloud_storage(self, ret_number, ret_unit):
        """Modifies retention on worm enabled cloud storage with the given name

            Args:
                ret_number (int)    :   number of days/months, etc. to retain

                ret_unit (str)    :   Unit to use (Day(s), Month(s), etc.

        """

        self.__admin_console.access_tab(self.__props['label.scaleOutConfiguration'])
        panel_info = RPanelInfo(self.__admin_console, self.__props['label.WORM'])
        panel_info.edit_tile_entity("Retention period")
        self.__admin_console.fill_form_by_id("retainBackupDataForDays", ret_number)
        self.__dropdown.select_drop_down_values(drop_down_id="retainBackupDataForDaysUnit", values=[ret_unit])
        self.__admin_console.click_button('Submit')
        notification_text = self.__admin_console.get_notification()
        return notification_text

    @WebAction()
    def __add_container_to_cloud_storage(self, container_name):
        """
            Method to fill in the container name and click on  add "<container>" while adding new cloud storage

            Args:
                container_name (str)    :   Name of the container

        """
        self.__admin_console.fill_form_by_id("mountPath", container_name)
        wait = WebDriverWait(self.__driver, 30)
        add_container_locator = (By.ID, 'mountPath-option-0')
        # wait at most 30 sec to locate the add "<container>" element
        add_container_element = wait.until(ec.visibility_of_element_located(add_container_locator))
        add_container_element.click()



