# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This file contains _NewCloudDBInstance class which inherits from Modal Panel.
This is specific to cloud DBs and implements private methods to set the common inputs like
vendor name, DB engine, cloud account, backup plan when creating a cloud database instance
for DynamoDB, Redshift, RDS, DocumentDB.
This file will also contain classes specific to each cloud DB type which
implements methods to add cloud DB instances.

Perform the following steps when trying to add support for a new cloud database:
    1. Create a class for the new agent and inherit from _NewCloudDBInstance
    2. Implement the vendor_name() and cloud_db_engine() in the class
        to return the values specific to the agent
    3. Define a method in the class to create instance for the specific agent

---------------------------------------------------------------------------

_NewCloudDBInstance:
-------------------

    vendor_name()       --  Abstract method to set the cloud vendor name

    cloud_db_engine()   --  Abstract method to set the cloud database engine

    select_cloud_regions()  --  Selects cloud regions from cloud browse

    select_items_under_regions()  --   Selects one or more items under cloud regions

    add_aws_cloud_account()     --  Method to add AWS cloud account


DynamoDBInstance:
----------------
    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates Amazon DynamoDB Engine

AmazonRDSInstance:
-----------------
    vendor_name()       -- Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates Amazon RDS Engine

CosmosDBSQLInstance:
-------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates new Azure CosmosDB SQL API Instance

CosmosDBCassandraInstance
-------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates new Azure CosmosDB SQL API Instance

GoogleCloudPlatformDBInstance:
------------------------------
    vendor_name()       --  Returns vendor for database engine

    _add_gcp_cloud_account()   --  Method to add GCP cloud account

    create_instance()   --  Creates GCP Instance

GoogleCloudPlatformPostgreSQLInstance:
--------------------------------------
    cloud_db_engine()   --  Returns the database engine name


GoogleCloudPlatformMySQLInstance:
--------------------------------------
    cloud_db_engine()   --  Returns the database engine name

GoogleCloudPlatformAlloydbInstance:
--------------------------------------
    cloud_db_engine()   --  Returns the database engine name

AlibabaCloudDBInstance:
--------------------------------------
    vendor_name()       --  Returns vendor for database engine

    _add_alibaba_cloud_account() -- Method to create Alibaba cloud account

    create_instance()   --  Creates Alibaba DB Instance

AlibabaPostgreSQLInstance:
--------------------------------------
    cloud_db_engine()   --  Returns the database engine name

AlibabaMySQLInstance:
--------------------------------------
    cloud_db_engine()   --  Returns the database engine name

AmazonRDSPostgreSQLInstance:
--------------------------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    database_engine()   --  Returns engine database type

    create_instance()   --  Creates Amazon RDS postgresql Instance

AmazonRDSMySQLInstance:
--------------------------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    database_engine()   --  Returns engine database type

    create_instance()   --  Creates Amazon RDS mysql Instance

AzurePostgreSQLInstance:
--------------------------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

AzureCloudDBInstance:
--------------------------------------
    create_instance()   --  Creates Azure Database Instance

AzureMySQLInstance:
--------------------------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

GoogleCloudPlatformSpannerInstance:
--------------------------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates GCP Spanner Instance

AWSInstance:
------------
    vendor_name()               --  Returns vendor for database engine

    select_authentication()     --  Select the Authentication method

    add_aws_cloud_account()     --  Method to add AWS cloud account

    select_backup_content_aws() --  Selects specific content to backup

RedshiftInstance:
----------------

    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates Amazon Redshift Engine

DocumentDBInstance:
------------------

    cloud_db_engine()   --  Returns the database engine name

    create_instance()   --  Creates Amazon DocDB Engine

AzurePostgreSQLInstance: Class for creating Microsoft Azure PostgreSQL instance with react page
-------------------------
    _configure_instance()   -- Method to configure instance details

    create_instance()       --  Creates Microsoft Azure PostgreSQL instance

RAzureSQLServerInstance: Class for creating Microsoft Azure SQL Server instance with react page
------------------------
    vendor_name()       --  Returns vendor for database engine

    cloud_db_engine()   --  Returns the database engine name

    _configure_instance()   --  Method to configure instance details

    _create_credentials()   --  Method to create SQL server credentials

    create_instance()   --  Creates Microsoft Azure SQL Server instance

"""
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from abc import abstractmethod
from Web.Common.page_object import (
    PageService,
    WebAction
)
from Web.AdminConsole.Components.panel import ModalPanel, RModalPanel
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.dialog import RModalDialog
from AutomationUtils.config import get_config

_CONFIG_DATA = get_config()


class _NewCloudDBInstance(Wizard):
    """Class to set common options while creating cloud DB instances"""

    def __init__(self, admin_console):
        """ Initialize the class

        Args:
            admin_console: instance of AdminConsoleBase

        """
        super(_NewCloudDBInstance, self).__init__(admin_console)
        self._admin_console = admin_console
        self._driver = self._admin_console.driver
        self._tree = TreeView(self._admin_console)
        self.dialog = RModalDialog(self._admin_console)
        self.content_browse = RContentBrowse(self._admin_console)

    @property
    @abstractmethod
    def vendor_name(self):
        """Override this method and implement it as a variable
        whose value needs to be set for vendor name"""
        raise NotImplementedError

    @property
    def database_engine(self):
        """Override this method and implement it as a variable
                whose value needs to be set for Cloud DB engine"""
        raise NotImplementedError

    @WebAction()
    def _select_vendor(self):
        """Selects vendor"""
        self.select_radio_button(self.vendor_name)
        self.click_next()

    @property
    @abstractmethod
    def cloud_db_engine(self):
        """Override this method and implement it as a variable
                whose value needs to be set for Cloud DB engine"""
        raise NotImplementedError

    @WebAction()
    def _set_database_engine(self):
        """Selects the cloud database engine"""
        self.select_radio_button(self.cloud_db_engine)
        self.click_next()

    @WebAction()
    def _set_backup_method(self):
        """
        Sets the backup method
        """
        self._driver.find_element(By.XPATH,
                                  "//input[@data-ng-model='addCloudDB.backupMethod' and @value=1]"
                                  ).click()

    @WebAction()
    def _set_database_type(self):
        """
        Sets the database service type
        Args:
            database_engine    (str)   :   The type of database engine
        """
        self.select_radio_button(self.database_engine)
        self.click_next()

    @WebAction()
    def _set_cloud_account(self, cloud_account):
        """
        Sets the cloud account
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance
        """
        try:
            self.select_drop_down_values(id='cloudAccount', values=[cloud_account])
        except NoSuchElementException:
            self.select_drop_down_values(id='Hypervisor', values=[cloud_account])
        self.click_next()

    @WebAction()
    def _set_access_node(self, access_node):
        """
        Sets the access node
        Args:
            access_node   (str) : The access node used for running CosmosDB operations
        """
        self.drop_down.select_drop_down_values(
            values=[access_node],
            drop_down_id='accessNodes')

    @WebAction()
    def _set_plan(self, name):
        """
        Sets the plan
        Args:
            name    (str)  :    The name of the plan
        """
        self.select_plan(name)
        self.click_next()

    @WebAction()
    def _set_instance(self, instance_name):
        """
        Sets the instance
        Args:
            instance_name    (str)  :    The name of the instance
        """
        self.select_drop_down_values(
            values=[instance_name],
            id='cloudInstanceDropdown')

    @WebAction()
    def _click_edit(self):
        """click edit"""
        self._driver.find_element(By.XPATH,
                                  "//button[contains(@class, 'MuiButton-root')]//div[text()='Edit']"
                                  ).click()

    @WebAction()
    def _click_clear_all(self):
        """clear all"""
        self._driver.find_element(By.XPATH,
                                  "//a[@ng-click='cappsBC.clearAll()']").click()

    @WebAction()
    def _click_select_all(self):
        """select all"""
        self._driver.find_element(By.XPATH,
                                  "//a[@ng-click='cappsBC.selectAll()']").click()

    @WebAction()
    def _click_on_cloud_region(self, region):
        """Clicks on the region to add cloud content
        Args:
            region (str):  Name of the region to be selected

                           Example: Asia Pacific (Mumbai) (ap-south-1)
        """
        self._driver.find_element(By.XPATH,
                                  f"//span[text()='{region}']").click()

    @WebAction()
    def _expand_cloud_region(self, region):
        """Expands the cloud region by clicking on the arrow near region
        Args:
            region  (str):  Full nmae of the cloud region

                            Example: Asia Pacific (Mumbai) (ap-south-1)
        """
        self.content_browse.expand_folder_path(folder=region)

    @WebAction()
    def _click_on_items_inside_region(self, region, items_list):
        """Clicks on the items inside the cloud regions
        Args:
            region  (str):  Full nmae of the cloud region

                            Example: Asia Pacific (Mumbai) (ap-south-1)

            items_list  (list)  : List of items to be selected under region
        """
        for each_item in items_list:
            self._driver.find_element(By.XPATH,
                                      f"//span[@title='{region}']//parent::div//following-sibling::div"
                                      f"//span[text()='{each_item}']").click()

    @PageService()
    def select_cloud_regions(self, region_list):
        """Clicks on the region to add cloud content
        Args:
            region_list (list):  list of names of the regions to be selected

                                   Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']
        """
        for region in region_list:
            self._click_on_cloud_region(region)

    @PageService()
    def select_items_under_regions(self, mapping_dict):
        """Selects one or more items (like tables, clusters) under cloud regions
        Args:
            mapping_dict (dict) : The dictionary containing the full region names as keys
                                and LIST of items to be selected under them as value
                                Example --
                                mapping_dict={
                                'full region-1 name':['table1','table2','table3']
                                'full region-2 name':['item1','item2','item3']
                                }
        """
        for key, value in mapping_dict.items():
            self._expand_cloud_region(key)
            self.content_browse.select_content(value)

    @WebAction()
    def _click_add_hypervisor(self):
        """
            Clicks the + button infront of cloud account
        """
        xp = f"//*[contains(text(), 'Cloud account')]/..//span[contains(@data-ng-click,'addCloudDB.addHypervisorDialog()')]"
        self._admin_console.scroll_into_view(xp)
        self._driver.find_element(By.XPATH, xp).click()

    @PageService(react_frame=False)
    def add_aws_cloud_account(self, cloud_account, access_node_name, credential_name=None,
                              region=None, auth_type="ACCESS_KEY"):
        """Method to add AWS cloud account
        Args:
            cloud_account   (str) : The name of the cloud account that will be created

            access_node_name    (str)   :   Name of the access node used to make connection to AWS

            credential_name     (str)   :   Credential name for the cloud account
                default:    None

            region              (str)   :   Region Name
                default: None

            auth_type           (str) : Authentication type
                Possible values: IAM/ACCESS_KEY/STS

        """
        self.click_add_icon()

        self._admin_console.fill_form_by_id("name", cloud_account)
        if region:
            self._admin_console.fill_form_by_id("region", region)
        auth_type_id = "useIamRole"
        if auth_type == 'STS':
            auth_type_id = "RoleARN"
        elif auth_type == 'ACCESS_KEY':
            auth_type_id = "IamGroup"
        self.dialog.select_radio_by_id(auth_type_id)
        if auth_type in ['STS', 'ACCESS_KEY']:
            self.select_drop_down_values(
                values=[credential_name],
                id='credentials')
        self.select_drop_down_values(
            values=[access_node_name],
            id='accessNodes')
        self.dialog.click_submit()
        self.click_next()


class AmazonRDSInstance(_NewCloudDBInstance):
    """Class for creating Amazon RDS instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.aws']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['label.rdsSnap']

    @PageService()
    def create_rds_instance(self, cloud_account, plan, content='default'):
        """
        Creates Amazon RDS instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                        configuring instance

            plan            (str):  The name of the plan

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                    'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one more tables under regions as content:
                            provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                            Example:
                            {
                            'US East (Ohio) (us-east-2)':['table1','table2','table3']
                            'US East (Virginia) (us-east-1)':['tableA','tableB'']
                            }

                            Default value is 'default', default content set in UI will be used
                """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self._set_cloud_account(cloud_account)
        if content != 'default':
            self._click_edit()
            self._admin_console.wait_for_completion()
            self.dialog.click_button_on_dialog(id="AddContent")
            self._admin_console.wait_for_completion()
            if isinstance(content, dict):
                self.select_items_under_regions(content)
            elif isinstance(content, list):
                self.select_cloud_regions(content)
            else:
                raise Exception("Did not find the content in expected format, "
                                "Expected dict or list")
            content_dialog = RModalDialog(self._admin_console, title="Browse backup content")
            content_dialog.click_save_button()
            self.dialog.click_save_button()
        self._admin_console.wait_for_completion()
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()
        self._admin_console.wait_for_completion()




class CosmosDBSQLInstance(_NewCloudDBInstance):
    """class for creating azure CosmosDB SQL API instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.azure_v2']

    @property
    def cloud_db_engine(self):
        """returns the database engine or service type"""
        return self._admin_console.props['label.cosmosDB']

    @WebAction()
    def _expand_cosmosdb_database(self, account_name, database_name):
        """Expands the given database under the cosmosdb account
        Args:
            account_name    (str)   --   CosmosDB account name

            database_name   (str)   --  CosmosDB database name
        """
        self._driver.find_element(By.XPATH,
                                  f"//span[text()='{account_name}']/following::div"
                                  f"//span[text()='{database_name}']/preceding::input[1]/../../span"
                                  f"/span[contains(@class, 'k-i-caret-alt-right')]"
                                  ).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _select_containers(self, container_list):
        """Selects on one or more containers under given account and database
        Args:

            container_list  (list)  --  List of containers to be selected

        """
        self._tree.select_items(container_list)

    @WebAction()
    def _set_database_api(self, api_type):
        """Selects the API type for the CosmosDB instance
        Args:
            api_type    (str)   --  Type of API for the instance: SQL API, TABLE API
        """
        self.select_drop_down_values(
            id='apiSelection',
            values=[api_type],
            wait_for_content_load=True
        )

    @PageService()
    def create_instance(self, cloud_account, access_node, plan, content='default'):
        """Creates new Azure CosmosDB SQL API instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            access_node     (str) : The access node used for running CosmosDB operations

            plan            (str):  The name of the plan

            content         (List or nested dict):  The content to be selected
                Default value is 'default', default content set in UI will be used

                            1. To set complete CosmosDB account as content:

                            Provide a list of strings of account names
                                Example: ['cosmos-account-1', cosmos-account-2]

                            2. To set one more databases and containers under database as content:

                            Provide a nested dictionary containing the account names as keys
                            and value as another dictionary whose keys are the database names
                            and values is a LIST of containers under the database
                                Example:
                                {
                                'cosmos-account-1': {
                                'database1':['container1', 'container2'],
                                'database2':['container3', 'container4']
                                        }
                                'cosmos-account-2':{
                                'database3': ['container5', 'container6'],
                                'database4': ['container7', 'container8']
                                        }
                                }

                            3. To set complete database as content:

                            Provide the nested dictionary same as above #2 but
                            in the nested dictionary, provide an empty LIST as value
                            instead of list of containers
                                Example:
                                    {
                                'cosmos-account-1': {
                                'database1':[],
                                        }
                                'cosmos-account-2':{
                                'database2': [],
                                'database3': []
                                        }
                                }
        """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self._set_database_api('NoSQL API')
        self._set_cloud_account(cloud_account)
        self._admin_console.fill_form_by_name('instanceName', cloud_account)
        self.click_next()
        if content != 'default':
            self._click_edit()
            self._admin_console.wait_for_completion()
            self._admin_console.click_by_xpath(
                "//button[contains(@class, 'MuiButtonBase-root') and contains(@id, 'AddContent')]"
            )
            self._admin_console.wait_for_completion()
            if isinstance(content, list):
                self.select_cloud_regions(content)
            elif isinstance(content, dict):
                for account, details in content.items():
                    self._expand_cloud_region(account)
                    for database, container_list in details.items():
                        if not container_list:
                            self._click_on_items_inside_region(account, [database])
                        else:
                            self._expand_cosmosdb_database(account, database)
                            self._select_containers(container_list)
        self._admin_console.click_button(id='Save')
        self._admin_console.wait_for_completion()
        self._admin_console.click_button(id='Submit')
        self._admin_console.wait_for_completion()
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()


class CosmosDBCassandraInstance(_NewCloudDBInstance):
    """class for creating azure CosmosDB Cassandra API instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.azure_v2']

    @property
    def cloud_db_engine(self):
        """returns the database engine or service type"""
        return self._admin_console.props['label.cosmosDB']

    @PageService()
    def create_instance(
            self,
            regions,
            instance_name,
            cloud_account,
            access_nodes,
            plan,
            content=[],
            **kwargs):
        """Creates new Azure CosmosDB SQL API instance
        Args:
            regions         (str) : list of region
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            access_node     (str) : list of access nodes used for running CosmosDB operations

            plan            (str):  The name of the plan

            content         (List):  The list of content path to be selected, eg, /account1/keyspace1/table1

            kwargs      (dict)  -- dict of keyword arguments as follows
                subscription_id         (str)       --  azure subscription id
                credential_name         (str)       --  credential name for azure cloud account
                tenant_id               (str)       --  tenant id for azure cloud account
                application_id          (str)       --  application id of azure cloud account
                application_secret      (str)       --  application secret of azure cloud account
        """
        self.wizard.select_radio_button(label="Microsoft Azure")
        self.wizard.click_next()

        self.wizard.select_radio_button(label="Cosmos DB")
        self.wizard.click_next()

        self.wizard.select_plan(plan)
        self.wizard.click_next()

        self.wizard.select_drop_down_values(
            id='apiSelection', values=["CASSANDRA API"])
        existcloudaccounts = self._rdropdown.get_values_of_drop_down(
            drop_down_id='cloudAccount')
        if cloud_account not in existcloudaccounts:
            self.wizard.click_add_icon(index=0)
            self.dialog.fill_text_in_field(
                element_id='name', text=cloud_account)
            self.dialog.fill_text_in_field(
                element_id='subscriptionId', text=kwargs.get(
                    'subscription_id', ""))
            existcredentials = self._rdropdown.get_values_of_drop_down(
                drop_down_id='credentials')
            if kwargs.get('credential_name', "") not in existcredentials:
                self.dialog.click_button_on_dialog(aria_label="Create new")
                self._admin_console.scroll_into_view("tenantId")
                addcreddialog = RModalDialog(
                    self._admin_console,
                    title=self._admin_console.props['label.addCredential'])
                self._admin_console.fill_form_by_xpath(
                    xpath="//label[contains(text(),'Credential name')]/../div/input[@id='name']",
                    value=kwargs.get(
                        'credential_name',
                        ""))
                addcreddialog.fill_text_in_field(
                    element_id='tenantId', text=kwargs.get(
                        'tenant_id', ""))
                self._admin_console.scroll_into_view("applicationId")
                addcreddialog.fill_text_in_field(
                    element_id='applicationId', text=kwargs.get(
                        'application_id', ""))
                self._admin_console.scroll_into_view("applicationSecret")
                addcreddialog.fill_text_in_field(
                    element_id='applicationSecret', text=kwargs.get(
                        'application_secret', ""))
                self._admin_console.scroll_into_view("Save")
                addcreddialog.click_submit()

            self.dialog.select_dropdown_values(drop_down_id='credentials', values=[
                kwargs.get('credential_name', "")])
            self.dialog.select_dropdown_values(
                drop_down_id='accessNodeDropdown',
                values=access_nodes,
                partial_selection=True)
            self.dialog.click_submit()
        self.wizard.select_drop_down_values(
            id='cloudAccount', values=[cloud_account])
        self.wizard.click_next()

        self.wizard.fill_text_in_field(id='instanceName', text=instance_name)
        self.wizard.click_next()

        if content:
            self.wizard.click_button(name='Edit')
            for path in content:
                self.content_browse.select_path(path)
            self._admin_console.click_button(value='Save')
        self.wizard.click_next()
        self.wizard.click_finish()

class GoogleCloudPlatformDBInstance(_NewCloudDBInstance):
    """Class for creating Google Cloud DB instance"""
    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.googleCloud']

    @PageService()
    def _add_gcp_cloud_account(self, cloud_account, access_node_name, credential_name=None):
        """Method to add GCP cloud account
                Args:
                    cloud_account   (str) : The name of the cloud account that will be created

                    access_node_name    (str)   :   Name of the access node used to make connection to AWS

                    credential_name     (str)   :   Credential name for the cloud account
                        default:    None
        """
        self.click_add_icon()
        self._admin_console.fill_form_by_id("name", cloud_account)
        self.select_drop_down_values(
            values=[credential_name],
            id='credentials')
        self.select_drop_down_values(
            values=[access_node_name],
            id='accessNodeDropdown',
            partial_selection=True)
        self.dialog.click_submit()
        self.click_next()


    @PageService()
    def create_instance(self, cloud_account, plan, instance_name,
                        database_user, password, access_node, credential_name, endpoint=None):
        """
            Creates GCP instance
            Args:
                cloud_account   (str): The cloud account that needs to be used for
                                            configuring instance

                plan             (str):  The name of the plan

                instance_name    (str):  The instance to be selected

                database_user       (str):  The username of User

                password        (str):  The password of User

                access_node     (str):  The name of access node to be used

                credential_name (str):  The name of credential to be created

                endpoint        (str): The endpoint of database server on GCP
            """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self._add_gcp_cloud_account(cloud_account, access_node_name=access_node, credential_name=credential_name)
        self._set_instance(instance_name)
        self._admin_console.fill_form_by_name('databaseUser', database_user)
        self._admin_console.fill_form_by_name('password', password)
        self._admin_console.fill_form_by_name('confirmPassword', password)
        if endpoint:
            self._admin_console.fill_form_by_name('endPoint', endpoint)
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()

class GoogleCloudPlatformPostgreSQLInstance(GoogleCloudPlatformDBInstance):
    """Class for creating Google Cloud PostgreSQL instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.postgresql']


class GoogleCloudPlatformMySQLInstance(GoogleCloudPlatformDBInstance):
    """Class for creating Google Cloud MySQL instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.mysql']

class GoogleCloudPlatformAlloydbInstance(GoogleCloudPlatformDBInstance):
    """Class for creating Google Cloud Alloydb instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['label.alloydbpostgreSQL']

class AlibabaCloudDBInstance(_NewCloudDBInstance):
    """Class for creating Alibaba database instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.alibaba_cloud']

    @PageService()
    def _add_alibaba_cloud_account(self, cloud_account, access_node):
        """Method to create Alibaba cloud account"""
        self._admin_console.wait_for_completion()
        self.click_add_icon()
        self._admin_console.wait_for_completion()
        self.dialog.fill_text_in_field(element_id="name", text=cloud_account)
        self.dialog.fill_text_in_field(element_id="accessKey", text=_CONFIG_DATA.alibaba_access_creds.access_key)
        self.dialog.fill_text_in_field(element_id="secretkey", text=_CONFIG_DATA.alibaba_access_creds.secret_key)
        if self._admin_console.check_if_entity_exists('id', 'accessNodeDropdown'):
            self.dialog.select_dropdown_values("accessNodeDropdown",
                                               [access_node], partial_selection=True)
        self._admin_console.click_button('Save')
        self._admin_console.wait_for_completion()
        self.click_next()

    @PageService()
    def create_instance(self, cloud_account, plan, instance_name, database_user, password, access_node, endpoint):
        """
            Creates Alibaba DB instance
            Args:
                cloud_account   (str) : The cloud account that needs to be used for
                                            configuring instance

                plan            (str):  The name of the plan

                instance_name   (str):  The DB instance to be selected

                database_user   (str):  The username of DB User

                password        (str):  The password of DB User

                access_node     (str):  The name of access node to be used

                endpoint        (str):  The <IP:PORT> of the alibaba database instance
            """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self._add_alibaba_cloud_account(cloud_account=cloud_account,
                                        access_node=access_node)
        self._set_instance(instance_name)
        self._admin_console.fill_form_by_name('databaseUser', database_user)
        self._admin_console.fill_form_by_name('password', password)
        self._admin_console.fill_form_by_name('confirmPassword', password)
        if endpoint:
            self._admin_console.fill_form_by_name('endPoint', endpoint)
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()

class AlibabaPostgreSQLInstance(AlibabaCloudDBInstance):
    """Class for creating Alibaba PostgreSQL instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.postgresql']

class AlibabaMySQLInstance(AlibabaCloudDBInstance):
    """Class for creating Alibaba MySQL instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.mysql']

class AmazonRDSPostgreSQLInstance(_NewCloudDBInstance):
    """Class for creating Amazon RDS PostgreSQL instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.aws']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['label.rdsStreaming']

    @property
    def database_engine(self):
        """returns database engine"""
        return self._admin_console.props['label.postgreSQL']

    @PageService()
    def create_instance(self, cloud_account, plan, instance_name,
                        database_user, password, access_node, credential_name):
        """
            Creates Amazon RDS PostgreSQL instance
            Args:
                cloud_account   (str) : The cloud account that needs to be used for
                                            configuring instance

                plan            (str):  The name of the plan

                instance_name   (str):  The PostgreSQL instance to be selected

                database_user   (str):  The username of PostreSQL User

                password        (str):  The password of PostgreSQL User

                access_node     (str):  The name of access node to be used

                credential_name (str):  The name of credential to be created
            """
        self._select_vendor()
        self._set_database_engine()
        self._set_database_type()
        self._set_plan(plan)
        self.add_aws_cloud_account(cloud_account, access_node, credential_name)
        self._set_instance(instance_name)
        self.fill_text_in_field(id='databaseUser', text=database_user)
        self.fill_text_in_field(id='password', text=password)
        self.fill_text_in_field(id='confirmPassword', text=password)

        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()


class AmazonRDSMySQLInstance(_NewCloudDBInstance):
    """Class for creating Amazon RDS MySQL instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.aws']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['label.rdsStreaming']

    @property
    def database_engine(self):
        """returns database engine"""
        return self._admin_console.props['label.mySql']

    @PageService()
    def create_instance(self, cloud_account, plan, instance_name,
                        database_user, password, access_node, credential_name):
        """
            Creates Amazon RDS MySQL instance
            Args:
                cloud_account   (str) : The cloud account that needs to be used for
                                            configuring instance

                plan            (str):  The name of the plan

                instance_name   (str):  The MySQL instance to be selected

                database_user   (str):  The username of MySQL User

                password        (str):  The password of MySQL User

                access_node     (str):  The name of access node to be used

                credential_name (str):  The name of credential to be created
            """
        self._select_vendor()
        self._set_database_engine()
        self._set_database_type()
        self._set_plan(plan)
        self.add_aws_cloud_account(cloud_account, access_node, credential_name)
        self._set_instance(instance_name)
        self.fill_text_in_field(id='databaseUser', text=database_user)
        self.fill_text_in_field(id='password', text=password)
        self.fill_text_in_field(id='confirmPassword', text=password)

        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()


class AzureCloudDBInstance(_NewCloudDBInstance):
    """Class for creating Microsoft Azure database instance"""

    @property
    @abstractmethod
    def vendor_name(self):
        """Override this method and implement it as a variable
        whose value needs to be set for vendor name"""
        raise NotImplementedError

    @PageService()
    def _create_azure_app_credentials(self, credential_name):
        """
        Method to create Azure App credential
        Args:
            credential_name     (str):  Name of the Azure app credential
        """
        dialog = RModalDialog(admin_console=self._admin_console, title=self._admin_console.props['label.addCredential'])
        dialog.fill_text_in_field(element_id="name", text=credential_name)
        dialog.fill_text_in_field(element_id="tenantId", text=_CONFIG_DATA.Azure.Tenant)
        dialog.fill_text_in_field(element_id="applicationId", text=_CONFIG_DATA.Azure.App.ApplicationID)
        dialog.fill_text_in_field(element_id="applicationSecret", text=_CONFIG_DATA.Azure.App.ApplicationSecret)
        dialog.click_submit()

    @PageService()
    def _create_azure_cloud_account(self, cloud_account, access_node, app_credential=None):
        """
        Method to create cloud account
        Args:
            cloud_account      (str):  Name of the cloud account
            access_node        (str): Name of the access node
            app_credential     (str):  Name of the credential if Authentication is App based

        """
        self._admin_console.wait_for_completion()
        self.click_add_icon()
        self._admin_console.fill_form_by_id("name", cloud_account)
        self._admin_console.fill_form_by_id("subscriptionId", _CONFIG_DATA.Azure.Subscription)
        if app_credential is not None:
            self.dialog.disable_toggle(label=self._admin_console.props['label.managedSvcIdentity'])
            self.dialog.click_button_on_dialog(aria_label="Create new")
            self._create_azure_app_credentials(app_credential)
        else:
            self.dialog.enable_toggle(label=self._admin_console.props['label.managedSvcIdentity'])
        if self._admin_console.check_if_entity_exists('id', 'accessNodeDropdown'):
            self.dialog.select_dropdown_values("accessNodeDropdown", [access_node], partial_selection=True)
        self.dialog.click_button_on_dialog(text='Save')
        self._admin_console.wait_for_completion()
        self._admin_console.click_button('Save')
        self._admin_console.wait_for_completion()

    @PageService()
    def create_instance(self, **kwargs):
        """
            Creates Microsoft Azure MySQL instance
            Keyword Args:
                cloud_account   (str): The cloud account that needs to be used for
                                            configuring instance

                plan             (str):  The name of the plan

                instance_name    (str):  The MySQL instance to be selected

                database_user       (str):  The username of database User

                password        (str):  The password of database User

                access_node     (str): access node name

                app_credential  (str): credential name if a app based authentication is used

                maintenance_db  (str): if postgres db , name of the maintenance db

                ssl             (bool): True, if ssl option is to be enabled

                ssl_ca          (str): Location of ssl_ca certificate in the access node

                ad_auth         (bool): False if ad_auth has to be disabled for DB instance
            """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(kwargs.get("plan"))
        self._create_azure_cloud_account(kwargs.get("cloud_account"), kwargs.get("access_node"),
                                         kwargs.get("app_credential"))
        self._set_cloud_account(kwargs.get("cloud_account"))
        self._set_instance(kwargs.get("instance_name"))
        self.fill_text_in_field(id='databaseUser', text=kwargs.get("database_user"))
        if kwargs.get("ad_auth", False):
            self.enable_toggle(label=self._admin_console.props['label.useADAuthentication'])
        else:
            self.fill_text_in_field(id='password', text=kwargs.get("password"))
            self.fill_text_in_field(id='confirmPassword', text=kwargs.get("password"))
        if kwargs.get("maintenance_db", None):
            self.fill_text_in_field(id='MaintainenceDB', text=kwargs.get("maintenance_db", "postgres"))
        if kwargs.get("ssl", False):
            self.enable_toggle(label=self._admin_console.props['label.useSSLOption'])
            if kwargs.get("ssl_ca", None):
                self.fill_text_in_field(id="sslCa", text=kwargs.get("ssl_ca", None))
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_finish()


class AzureMySQLInstance(AzureCloudDBInstance):
    """Class for creating Microsoft Azure MySQL instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.azure_v2']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.mysql']


class GoogleCloudPlatformSpannerInstance(_NewCloudDBInstance):
    """Class for creating Google Cloud Spanner instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.googleCloud']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return "Cloud spanner"

    @PageService()
    def create_instance(
            self,
            cloud_account,
            instance_name,
            plan,
            **kwargs
    ):
        """
            Creates Cloud Spanner instance
            Args:
                cloud_account (str): The cloud account to use for configuring instance

                instance_name (str):  Name of the Cloud Spanner Instance

                plan (str):  The name of the plan


            Keyword Args:
                spanner_account_id  (str): Email address of the Google cloud account

                spanner_key_json (str): File path to the Cloud Spanner key JSON file

                client_name (str): Name to give new Cloud Account if Cloud Account not given

                access_node (str): Name of access node to associate if creating new Cloud Account

            """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self._set_cloud_account(cloud_account)

        self.select_drop_down_values(
            id="cloudInstanceDropdown",
            values=[instance_name],
            wait_for_content_load=True
        )
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_button(self._admin_console.props['Finish'])


class AWSInstance(_NewCloudDBInstance):
    """Common class for creating AWS instances"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.aws']

    @WebAction()
    def _confirm_iam_stack_created(self):
        """This select the checkbox creating MetallicRole stack"""
        self._admin_console.click_by_xpath("//span[contains(text(),'I confirm that the IAM')]")

    @PageService()
    def select_authentication(self, auth_type):
        """Select the Authentication method
            Args:
                auth_type(str) : Type of authentication
                Accepted values:
                    "IAM ROLE"
                    "ACCESS_KEY"
                    "STS"
        """
        authentication_type = "IAM ROLE"
        if "ACCESS_KEY" in auth_type:
            authentication_type = "Access and Secret Key"
        if "STS" in auth_type:
            authentication_type = "STS assume role with IAM policy"
        self.select_drop_down_values(id='authenticationMethod', values=[authentication_type])
        # iam_stack_url = self._get_iam_stack_url()
        # self.s3_helper.create_stack(stack_name='MetallicRole', stack_url=iam_stack_url,
        #                             capabilities=['CAPABILITY_NAMED_IAM'])
        self._confirm_iam_stack_created()
        self.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def add_aws_cloud_account(
            self, name, access_node_name, authentication_type="IAM", credential_name=None):
        """Method to add AWS cloud account
        Args:
            name                (str) : Name of the coud account

            access_node_name     (str)   :   access node name

            authentication_type (str)   : Authentication type to be used
                default:    "IAM ROLE"

                Accepted values:
                        "IAM"
                        "ACCESS_KEY"
                        "STS"

            credential_name     (str)   :   Credential name
                default:    None

        """
        self.click_add_icon()
        self.dialog.fill_text_in_field('name', name)
        auth_type_id_map = {
            "IAM": "useIamRole",
            "ACCESS_KEY": "IamGroup",
            "STS": "RoleARN"
        }
        self.dialog.select_radio_by_id(auth_type_id_map[authentication_type])
        if "IAM ROLE" not in authentication_type and credential_name:
            self.dialog.select_dropdown_values("credentials", [credential_name])
        self.dialog.select_dropdown_values("accessNodes", [access_node_name])
        self.dialog.click_button_on_dialog(text='Save')
        self._admin_console.wait_for_completion()

    @PageService()
    def select_backup_content_aws(self, content):
        """
        Selects specific content to back up
        args:
            content (list of str)   :   "Content to be selected"
        """
        if content is not None:
            self.click_button("Edit")
            self._admin_console.wait_for_completion()
            self.dialog.click_button_on_dialog(id="AddContent")
            self._admin_console.wait_for_completion()
            self.select_items_under_regions(mapping_dict=content)
            content_dialog = RModalDialog(self._admin_console, title="Browse backup content")
            content_dialog.click_save_button()
            self._admin_console.wait_for_completion()
            self.dialog.click_button_on_dialog(text='Save')
            self._admin_console.wait_for_completion()
        self._admin_console.click_button(value="Next")


class RedshiftInstance(AWSInstance):
    """Class for creating RedShift instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.redshift']

    @PageService()
    def create_instance(
            self, cloud_account, plan, content='default',
            auth_type="IAM", access_node=None, credential_name=None):
        """
        Creates Redshift instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            plan            (str):  The name of the plan

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }

                            Default value is 'default', default content set in UI will be used

            auth_type           (str) : Authentication type
                Possible values: IAM/ACCESS_KEY/STS

            access_node_name    (str)   :   Name of the access node

            credential_name     (str)   :   Credential name
                default:    None
        """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self.add_aws_cloud_account(cloud_account, access_node, auth_type, credential_name)
        self.click_next()
        self.select_backup_content_aws(content)
        self._admin_console.wait_for_completion()
        self.click_button(self._admin_console.props['Finish'])


class DocumentDBInstance(AWSInstance):
    """Class for creating DOCDB instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.documentdb']

    @PageService()
    def create_instance(
            self, cloud_account, plan, content='default',
            auth_type="IAM", access_node=None, credential_name=None):
        """
        Creates DocumentDB instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            plan            (str):  The name of the plan

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }

                            Default value is 'default', default content set in UI will be used

            auth_type           (str) : Authentication type
                Possible values: IAM/ACCESS_KEY/STS

            access_node_name    (str)   :   Name of the access node

            credential_name     (str)   :   Credential name
                default:    None
        """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self.add_aws_cloud_account(cloud_account, access_node, auth_type, credential_name)
        self.click_next()
        self.select_backup_content_aws(content)
        self._admin_console.wait_for_completion()
        self.click_button(self._admin_console.props['Finish'])


class DynamoDBInstance(AWSInstance):
    """Class for creating DynamoDB instance"""

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['label.dynamodb']

    @PageService()
    def create_instance(self, cloud_account, plan, adjust_read_capacity, content=None):
        """
        Creates DynamoDB instance
        Args:
            cloud_account   (str) : The cloud account that needs to be used for
                                    configuring instance

            plan            (str):  The name of the plan

            adjust_read_capacity(int):  The value that needs to be set for
                                        adjust read capacity parameter
                                        Converted into string to call other methods

            content         (dict or list):  The content to be selected

                            1. To set complete regions as content:
                            Provide list of strings of region names
                            Example: ['Asia Pacific (Mumbai) (ap-south-1)',
                                   'Asia Pacific (Singapore) (ap-southeast-1)']


                            2. To set one more tables under regions as content:
                            Provide a dictionary containing the full region names as keys
                            and LIST of strings with items to be selected under them as value
                                Example:
                                {
                                'US East (Ohio) (us-east-2)':['table1','table2','table3']
                                'US East (Virginia) (us-east-1)':['tableA','tableB'']
                                }
        """
        self._select_vendor()
        self.click_next()
        self._set_database_engine()
        self._set_plan(plan)
        self._set_cloud_account(cloud_account)
        if adjust_read_capacity != 0:
            self.enable_toggle(label='Adjust read capacity')
            adjust_read_capacity = str(adjust_read_capacity)
            self.fill_text_in_field(id='readCapacityUnits', text=adjust_read_capacity)
        self.click_next()
        self.select_backup_content_aws(content)
        self.click_button(self._admin_console.props['Finish'])


class AzurePostgreSQLInstance(AzureCloudDBInstance):
    """Class for creating Microsoft Azure PostgreSQL instance with react page"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.azure_v2']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['viewname.dbInstancesTable.postgresql']


class AzureMariaDBInstance(AzureCloudDBInstance):
    """Class for creating Microsoft Azure MariaDB instance"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.azure_v2']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['agentType.mariaDB']


class RAzureSQLServerInstance(_NewCloudDBInstance):
    """Class for creating Microsoft Azure SQL Server instance with react page"""

    @property
    def vendor_name(self):
        """returns the vendor"""
        return self._admin_console.props['label.vendor.azure_v2']

    @property
    def cloud_db_engine(self):
        """returns the database engine type"""
        return self._admin_console.props['label.azureSqlDatabaseService']

    @PageService()
    def _configure_instance(self, instance_name, storage_connection_string, **kwargs):
        """
            method to configure instance details
            Args:
                instance_name       (str):  Name of the instance

                storage_connection_string   (str):  Storage connection string for the Azure storage account

            Keyword Args:
                credentials         (str or dict):  Name of existing credentials to use or
                Dictionary of credentials to create

                username                (str):  The username for new credentials creation

                password                (str):  The password for new credentials creation

                description             (str):  The description for new credentials
        """
        self._admin_console.driver.refresh()
        self.select_drop_down_values(id='cloudInstanceDropdown', values=[instance_name])
        self.fill_text_in_field(id='azureStorageConnectionString', text=storage_connection_string)

        credentials = kwargs.get('credentials')
        if isinstance(credentials, dict):
            credential_name = credentials.get('name')
            username = credentials.get('username')
            password = credentials.get('password')
            description = credentials.get('description')
            if credential_name and username and password:
                self.click_add_icon()
                self._create_credentials(credential_name, username, password, description)
        else:
            self.select_drop_down_values(id='connectionString', values=[credentials])
        self.click_next()

    @PageService()
    def _create_credentials(self, credential_name, username, password, description=None):
        """
            method to create SQL server credentials
            Args:
                credential_name     (str):  Name of credentials to create

                username            (str):  Name of the user

                password            (str):  Password for user

                description         (str, Optional):    Description of the credentials. Default is None
        """
        self._admin_console.fill_form_by_id('credentialName', credential_name)
        self._admin_console.fill_form_by_id('userName', username)
        self._admin_console.fill_form_by_id('password', password)

        if description:
            self._admin_console.fill_form_by_id('description', description)

    @PageService()
    def create_instance(self, cloud_account, plan, instance_name, storage_connection_string, **kwargs):
        """
            Creates Microsoft Azure SQL Server instance
            Args:
                cloud_account   (str) : The cloud account that needs to be used for configuring the instance

                plan            (str):  The name of the plan

                instance_name   (str):  The Azure SQL instance to be selected

                storage_connection_string   (str):  Storage connection string for the Azure storage account

            """
        self._select_vendor()
        self._set_database_engine()
        self._set_plan(plan)
        self._set_cloud_account(cloud_account)
        self._configure_instance(
            instance_name,
            storage_connection_string,
            **kwargs
        )
        self.click_next()
        self._admin_console.wait_for_completion()
        self.click_button(self._admin_console.props['Finish'])
