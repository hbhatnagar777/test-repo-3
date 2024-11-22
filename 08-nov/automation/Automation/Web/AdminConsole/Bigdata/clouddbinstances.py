from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Cloud DB (MongoDB Atlas cluster) operations.

Classes defined in this file
     CloudDBInstances : Class which performs MongoDB Atlas cluster related operations

         __int__ :Constructor for CloudDBInstances class,
          initializes objects required for MongoDB Atlas cluster related operations

         is_mongodb_atlas_cloud_account_exists: check if MongoDB Atlas cluster exists with that name

         delete_mongodb_atlas_cluster_cloud_account: Delete MongoDB Atlas cluster and cloud account

         delete_mongodb_atlas_cluster_only: Delete MongoDB Atlas cluster only

         __get_drop_down_by_id: Get drop down using id

         __expand_drop_down: Exapand drop down

         __add_cloud_db: Add instance and select cloud DB instance

         __add_cloud_db_mongodb_atlas_cluster: Add instance

         __select_mongodb_atlas_cluster_option: Select MongoDB Atlas option

         __add_new_credential: Create new credential

         __add_cloud_account: Add cloud account during MongoDB Atlas cluster creation

         create_mongodb_atlas_cluster: Create MongoDB Atlas cluster

     MongoDBAtlasInstances: Class which performs operation on MongoDB Atlas cluster instance

          __int__ :Constructor for MongoDBAtlasInstances class,
          initializes objects required for MongoDB Atlas cluster instance related operations

          __click_add_backup_content: Click on add backup content

          __click_add_cluster: Click on add cluster

          select_add_backup_content: Select and add backup content

          __expand_project: Expand project

          __select_cluster: Select DB cluster content

          add_cluster_to_backup_content: Select and add DB cluster to the subclient content

          access_backup: Perform backup

          access_restore: Perform restore

          in_place_restore_mongodb_atlas_cluster: Perform in place restore of MongoDB Atlas cluster

"""
import time
from enum import Enum

from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Components.dialog import RModalDialog, ModalDialog
from Web.AdminConsole.Components.panel import DropDown, RDropDown
from Web.AdminConsole.Components.table import Table, Rtable

from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import PageService, WebAction


class CloudDBInstances:
    """This class provides the function or operations that can be performed on the Cloud DB Instances like
    MongoDB Atlas cluster in AdminConsole
    """

    class Types(Enum):
        """Available cloud database types supported"""
        MongoDBAtlas = "MongoDB Atlas"

    def __init__(self, admin_console: AdminConsole):
        """Class constructor

            Args:
                admin_console   (obj)   --  The admin console class object

        """
        self.admin_console = admin_console
        self.cloudinstances_table = Table(self.admin_console)
        self.cloudinstances_rtable = Rtable(self.admin_console)
        self.__dropdown = DropDown(self.admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__rmodaldialog = RModalDialog(admin_console)
        self.__modaldialog = ModalDialog(admin_console)
        self.admin_console.load_properties(self)
        self.props = self.admin_console.props
        self.navigator = None

    @PageService()
    def is_mongodb_atlas_cloud_account_exists(self, instance_name):
        """Check if instance exists

            Args:

                instance_name            (str)  --  Name of the cloud DB instance

        """
        self.admin_console.refresh_page()
        self.__rdropdown.select_drop_down_values(drop_down_id='Type', values=["Cloud DB"])
        return self.cloudinstances_rtable.is_entity_present_in_column('Server', instance_name)

    @PageService()
    def delete_mongodb_atlas_cluster_cloud_account(self, cloud_account_instance):
        """Delete MongoDB Atlas cluster instance and cloud account

                    Args:

                        cloud_account_instance           (str)  --  cloud account name

        """
        self.cloudinstances_table.access_link_by_column(cloud_account_instance, cloud_account_instance)
        self.admin_console.access_menu('Retire')
        self.admin_console.wait_for_completion()
        self.__modaldialog.type_text_and_delete('Retire', button_name='Retire')
        self.admin_console.wait_for_completion()
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_db_instances()
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()
        self.cloudinstances_rtable.reload_data()
        self.admin_console.wait_for_completion()
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()
        if self.cloudinstances_rtable.is_entity_present_in_column('Server', cloud_account_instance):
            self.__rdropdown.select_drop_down_values(drop_down_id='Type', values=["Cloud DB"])
            self.cloudinstances_table.access_link_by_column(cloud_account_instance, cloud_account_instance)
            self.admin_console.access_menu_from_dropdown('Delete')
            self.admin_console.wait_for_completion()
            self.__modaldialog.type_text_and_delete('Delete', button_name='Delete')
            self.admin_console.wait_for_completion()
            self.navigator.navigate_to_db_instances()
            self.admin_console.refresh_page()
            self.admin_console.wait_for_completion()
            self.cloudinstances_rtable.reload_data()
            self.admin_console.wait_for_completion()

    @PageService()
    def delete_mongodb_atlas_cluster_only(self, cloud_account_instance):
        """Delete MongoDB Atlas cluster instance only

                    Args:

                        cloud_account_instance            (str)  --  cloud account instance name

        """
        self.cloudinstances_table.access_link_by_column(cloud_account_instance, 'MongoDB Atlas')
        self.admin_console.access_menu_from_dropdown('Delete')
        self.admin_console.wait_for_completion()
        self.__rmodaldialog.type_text_and_delete('Delete', button_name='Delete')
        self.admin_console.wait_for_completion()

    @WebAction()
    def __get_drop_down_by_id(self, drop_down_id):
        """ Method to get drop down based on id provided as input

            Args:

                        drop_down_id            (str)  --  dropdown id

        """
        drop_down = None
        if self.admin_console.check_if_entity_exists("xpath", f"//isteven-multi-select[@id='{drop_down_id}']"):
            drop_down = self.admin_console.driver.find_element(By.XPATH, f"//isteven-multi-select[@id='{drop_down_id}']")
        else:
            drop_down = self.admin_console.\
                driver.find_element(By.XPATH, f"//isteven-multi-select[@directive-id='{drop_down_id}']")
        return drop_down

    @WebAction()
    def __expand_drop_down(self, drop_down):
        """ Expand drop down
            Args:

                                drop_down            (str)  --  drop down object
        """
        drop_down.click()

    @WebAction()
    def __add_cloud_db(self):
        """Add cloud db """

        xp = "//div[contains(@class, 'page-actions')]/" \
             "/button[contains(@aria-label, 'Add instance')]//*[contains(text(), 'Add instance')]"
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.wait_for_completion()
        xp = '//div[contains(text(),"Cloud DB")]'
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def __add_cloud_db_mongodb_atlas_cluster(self):
        """Add MongoDB atlas cluster instance """

        xp = "//div[contains(@class, 'page-actions')]" \
             "//button[contains(@aria-label, 'Add instance')]//*[contains(text(), 'Add instance')]"
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def __select_mongodb_atlas_cluster_option(self):
        """Select MongoDB as Atlas cluster type option"""

        xp = "//div[@class='checkBoxContainer']//label/span[contains(text(),'MongoDB')]/ancestor::label"
        self.admin_console.driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def __add_new_credential(self, credential_name, username, password):
        """Add new credentials during MongoDB Atlas cluster instance creation

                            Args:

                                credential_name     (str)  --  credential name

                                username            (str)  --  user name

                                password            (str)  --  password
        """

        xp='//isteven-multi-select[@directive-id="selectId"]//following-sibling::span/span[contains(@title,"Add")]'
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.fill_form_by_id('credentialName', credential_name)
        self.admin_console.fill_form_by_id('userName', username)
        self.admin_console.fill_form_by_id('password', password)
        self.admin_console.click_button("Save")
        self.admin_console.wait_for_completion()

    @WebAction()
    def __add_cloud_account(self, cloud_account_name, cloud_access_node, credential_name, plan_name,
                            create_new_credential=1, username='', password=''):
        """Add a new cloud account during MongoDB Atlas cluster creation

                            Args:

                                cloud_account_name            (str)  --  Database type

                                cloud_access_node            (str)  --  Instance Name

                                credential_name              (str)  --  Client Name

                                plan_name                    (str)  --  Plan name

                                create_new_credential        (int)  -- Create new credential-1
                                                                        Use existing credential-0

                                username                      (str)

                                password                      (str)
                        """
        xp = '//isteven-multi-select[@directive-id="accountName"]' \
             '//following-sibling::span/span[contains(@data-ng-click,"addCloudDB")]'
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.wait_for_completion()
        self.admin_console.fill_form_by_id('serverName', cloud_account_name)
        self.__dropdown.select_drop_down_values(drop_down_id='cappsAccessNodes_isteven-multi-select_#8659'
                                                , values=[cloud_access_node])
        if create_new_credential == 0:
            self.__dropdown.select_drop_down_values(drop_down_id='selectId', values=[credential_name])
        else:
            self.__add_new_credential(credential_name, username, password)
        self.admin_console.click_button("Save")
        self.admin_console.wait_for_completion()

    @PageService()
    def create_mongodb_atlas_cluster(self, cloud_account_instance, cloud_access_node, credential_name, plan_name,
                                     create_new_cloud_account=1, create_new_credential=1, username='', password=''):
        """Create MongoDB Atlas cluster

                            Args:

                                cloud_account_instance       (str)  --  cloud account instance name

                                cloud_access_node            (str)  --  cloud access node

                                credential_name              (str)  --  credential name

                                plan_name                    (str)  --  plan name

                                create_new_cloud_account     (int)  - 0 - use existing cloud account
                                                                      1 - create new cloud account

                                create_new_credential        (int) - 0 - use existing credentials
                                                                     1 - create new credentials

                                username                     (str)  --  username

                                password                     (str)  --  password

        """
        self.__add_cloud_db()
        MongoDB_dropdown = self.__get_drop_down_by_id('vendorType')
        self.__expand_drop_down(MongoDB_dropdown)
        self.__select_mongodb_atlas_cluster_option()
        self.admin_console.wait_for_completion()
        self.__dropdown.select_drop_down_values(drop_down_id='databaseService', values=["Atlas"])
        if int(create_new_cloud_account) == 0:
            self.__dropdown.select_drop_down_values(drop_down_id='accountName', values=[cloud_account_instance])
        else:
            self.__add_cloud_account(cloud_account_instance, cloud_access_node, credential_name, plan_name,
                                     create_new_credential, username, password)
        self.__dropdown.select_drop_down_values(drop_down_id='planSummaryDropdown', values=[plan_name])
        self.admin_console.click_button("Add")
        self.admin_console.wait_for_completion()


class MongoDBAtlasInstances:
    """This class provides the function or operations that can be performed on the MongoDB Atlas cluster Instance
    page in AdminConsole
    """

    def __init__(self, admin_console: AdminConsole):
        """Class constructor

            Args:
                admin_console   (obj)   --  The admin console class object

        """
        self.admin_console = admin_console
        self.mongodbcloudinstances_table = Table(self.admin_console)
        self.__dropdown = DropDown(self.admin_console)
        self.__rmodaldialog = RModalDialog(admin_console)
        self.admin_console.load_properties(self)
        self.props = self.admin_console.props
        self.overview = Overview(admin_console)

    @WebAction()
    def __click_add_backup_content(self, subclient_name='default'):
        """Add subclient backup content

                            Args:

                                subclient_name            (str)  --  subclient name

        """

        time.sleep(20)
        xp = f"//div[contains(@id,'dbInstanceSubclientTable')]//table/descendant::tr/td" \
             f"//a[contains(text(),'default')]/ancestor::td/following-sibling::td/a[contains(@cv-toggle-content,'Add')]"
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.wait_for_completion()

    @WebAction()
    def __click_add_cluster(self):
        """Click add cluster option"""

        xp = '//div/a[contains(text(),"Add clusters")]'
        self.admin_console.driver.find_element(By.XPATH, xp).click()
        self.admin_console.wait_for_completion()

    @PageService()
    def select_add_backup_content(self, subclient_name='default'):
        """Add backup content in subclient

                            Args:

                                subclient_name            (str)  --  subclient name

        """

        self.mongodbcloudinstances_table.search_for(subclient_name)
        self.admin_console.wait_for_completion()
        self.__click_add_backup_content(subclient_name)
        self.admin_console.wait_for_completion()
        self.__click_add_cluster()

    @WebAction()
    def __expand_project(self, project_name):
        """Expand the project

                            Args:

                                project_name            (str)  --  Project name

        """

        self.admin_console.click_by_xpath('//button[contains(@id,"cv-capps-browse-content_button_#9981")]')
        self.admin_console.wait_for_completion()
        self.admin_console.click_by_xpath(
            '//span[text()="'+project_name+'"]//ancestor::div/button['
                                           'contains(@id,"cv-capps-browse-content_button_#9981")]')

        self.admin_console.wait_for_completion()

    @WebAction()
    def __select_cluster(self, cluster_name):
        """Select the cluster to be backed up

                            Args:

                                cluster_name            (str)  --  cluster name

        """
        self.admin_console.click_by_xpath('//span[contains(text(),'
                                          '"' + cluster_name + '") and contains(text(),"DB Cluster")]')
        self.admin_console.wait_for_completion()

    @PageService()
    def add_cluster_to_backup_content(self, project_name, cluster_name):
        """Add MongoDB Atlas DB cluster to subclient content

                            Args:

                                project_name            (str)  --  Project name

                                cluster_name            (str)  --  cluster name

        """

        self.__expand_project(project_name)
        self.__select_cluster(cluster_name)
        self.admin_console.click_button("OK")
        self.admin_console.click_button("Save")

    @PageService()
    def access_backup(self, subclient_name):
        """Access backup

                            Args:

                                subclient_name            (str)  --  subclient name

        """

        self.mongodbcloudinstances_table.access_action_item(subclient_name, "Back up")
        self.admin_console.wait_for_completion()
        self.admin_console.click_button("OK")
        self.admin_console.wait_for_completion()

    @PageService()
    def access_restore(self, subclient_name):
        """access restore

                            Args:

                                subclient_name            (str)  --  subclient name

        """

        self.mongodbcloudinstances_table.access_action_item(subclient_name, "Restore")
        self.admin_console.wait_for_completion()

    @PageService()
    def in_place_restore_mongodb_atlas_cluster(self):
        """In place restore of MongoDB Atlas cluster"""

        self.admin_console.select_hyperlink('In place')
        self.admin_console.click_button(self.admin_console.props['action.submit'])
        self.admin_console.click_button(self.admin_console.props['label.yes'])
