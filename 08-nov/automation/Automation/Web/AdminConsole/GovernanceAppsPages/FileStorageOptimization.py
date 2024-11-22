from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
This module provides all the methods that can be done of the File storage
optimization and FSO Server Group page.

FileStorageOptimization  --  This class contains all the methods for action in
    File Storage Optimization page and is inherited by other classes to
    ...

    Functions:

    add_client()                            -- Adds an FSO client
    select_client()                         -- Select fso client or associated data source
    toggle_client()                         -- Toggle client in FSO landing page
    select_details_action()                 -- Select details action for a row
    check_if_client_exists()                -- Check if client exists on FSO landing page
    select_client_datasource()              -- select data source from FSO landing page
    get_fso_datasource_list ()              -- Get data source list in expanded view
    select_fso_grid_tab ()                  -- Select a tab from FSO Grid
    add_fso_server_group()                  -- Select Add FSO Server Group tile
    view_datasources()                      -- Selects Data sources on FSO landing page

FileStorageOptimizationClientDetails -- This class contains all the methods
    for Web action/page service in client details page
    ...

    Functions:
    select_datasource()                     -- select fso data source
    select_details_action()                 -- select data source details action
    select_delete_action()                  -- select delete action
    check_if_datasource_exists()            -- Searches for FSO data source in client details page
    delete_fso_datasource()                 -- Delete given FSO data source


FsoDataSourceDiscover -- This class contains all the methods
    for Web action/page service in FSO Data source discover page.

    ...

    Functions:

    get_duplicate_file_count()              -- Get Duplicate file count from FSO duplicate dashboard
    get_duplicate_file_size()               -- Get Duplicate File size from FSO duplicate dashboard
    fso_dashboard_entity_count()            -- get fso dashboard entity count
    select_fso_dashboard()                  -- Select given FSO dashboard
    get_file_security_dashboard_user_count()-- Get User count for a given permission in
                                                FSO security dashboard

    load_fso_dashboard()                    --  Load FSO dashboards
    select_fso_review_tab()                 -- Select review tab in FSO review page

FsoDataSourceReview  -- This class contains all the methods for Web action/page service in FSO
     Data source review page.
    ...

    Functions:

    select_review_page_filter()             -- Click passed review page filter
    get_fso_time_info()                     -- Get FSO time info from UI
    get_fso_time_dict()                     -- Get fso time dict for passed filter


FsoDataSourceDetails -- This class contains all the methods for Web actions/page service in FSO
    Data source details page

    Functions:

    Need to be added


FsoServerGroupDetails -- This class contains all the methods for Web actions/page service for
    FSO Server Group Details Page

    Functions:
        select_server_details_action()          -- select server details action
        check_if_client_exists()                -- Searches for FSO client in server group details page


FSOMonitoringReport --  This class contains all the methods for the Web actions / Page Services in FSO
    File Monitoring Report page.

    Functions:
        __get_search_bar()                      -- Gets the search bar input field
        select_hyperlink_using_text()           -- Selects Hyper link using text
        open_monitoring_report_page()           -- Open File Monitoring Report Page
        sort_monitoring_table()                 -- Sorts the File monitoring report table using a column link text
        access_monitoring_report_searchbar()             -- Access Search bar using id and enter text on it


FSODataSourceManagement --  Class contains all the methods for the Web actions / Page services in FSO
    Activate datasource management page

    Functions:
        __add_entry()                       --  Adds a new datasource entry to the datasource property table
        __upload_csv()                      --  Uploads csv file to data source management
        __enter_credentials()               --  Enters the username and password require for the data source
        __click_row_action()                --  Clicks the row action save or cancel for the given row entry on table
        select_data_source()                --  Selects a data source from table
        add_multiple_data_sources()         --  Adds multiple data source to FSO

"""
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.Common.page_object import WebAction, PageService
from Web.Common.exceptions import CVWebAutomationException
from time import sleep
from dynamicindex.utils.constants import FSO_DASHBOARDS_TO_VERIFY, FSO_DASHBOARD_TABS_TO_VERIFY, FSO_DASHBOARD_FILTERS_ID
import dynamicindex.utils.constants as di_constants


class FileStorageOptimization(GovernanceApps):
    """
     This class contains all the methods for action in File Storage Optimization landing page
    """

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__subGridPaginationValue = "100"
        self.__fso_Grid_Id = "FSOGrid"
        self.__fso_SubGrid_ID = 'DataSourcesSubGrid-'
        self.__rtable = Rtable(self.__admin_console, id=self.__fso_Grid_Id)
        self.__rSubTable = Rtable(self.__admin_console, id=self.__fso_SubGrid_ID)
        self.__admin_console.load_properties(self)

    @PageService()
    def add_client(self, inventory_name, plan_name, storage_type="File system"):
        """
        Adds a client
            Args:
                plan_name (str)  - Plan name to be selected
                inventory_name (str)  - Inventory name to be selected
                storage_type (str) - Storage Type "File system" or "Object storage"
        """
        self.__rtable.access_toolbar_menu(self.__admin_console.props['client.add'])
        if storage_type == "File system":
            self.__rtable.access_menu_from_dropdown(self.__admin_console.props['label.filesystem'])
        elif storage_type == "Object storage":
            self.__rtable.access_menu_from_dropdown(self.__admin_console.props['label.objectStorage'])
        else:
            raise CVWebAutomationException("Invalid Storage Type selected!!")
        # Setting the value of class variables of parent class GovernanceApps so that it can be used later
        # in add_file_server(FileServerLookup.py)
        GovernanceApps.inventory_name = inventory_name
        GovernanceApps.plan_name = plan_name

    @PageService()
    def select_fso_grid_tab(self, entity_name="Server group"):
        """
        Select passed Tab from FSO Grid
        Args:
            entity_name (str) : FSO Grid Tab Name
            Ex : Object storage,File system,Server group
        """
        self.__rtable.view_by_title(entity_name)

    @PageService()
    def add_fso_server_group(self, inventory_name, plan_name):
        """Select add server group tile in FSO Server group landing page"""
        self.select_fso_grid_tab()
        self.__rtable.access_toolbar_menu(self.__admin_console.props['clientGroup.add'])
        # Setting the value of class variables of parent class GovernanceApps so that it can be used later
        # in add_file_server(FileServerLookup.py)
        GovernanceApps.inventory_name = inventory_name
        GovernanceApps.plan_name = plan_name

    @PageService()
    def check_if_client_exists(self, client_name):
        """
        Searches for a client
            Args:
                client_name (str)  - Client name to be searched for
            Returns:
                 (bool) True/False based on the presence of the Client
        """
        return self.__rtable.is_entity_present_in_column(
            self.__admin_console.props['label.name'],
            client_name)

    @PageService()
    def select_client(self, client_name):
        """
        Selects FSO Client or associated datasource
            Args:
                client_name (str)  - Client name to be selected
        """
        self.__rtable.access_link(client_name)

    @PageService()
    def select_client_datasource(self, data_source_name):
        """
        Selects a data source from expanded view in FSO Client page
        Args:
            data_source_name (str): Name of DataSource to be selected
        """
        self.__rSubTable.set_pagination(self.__subGridPaginationValue)
        self.__rSubTable.access_link(data_source_name)

    @PageService()
    def toggle_client(self, row_entity_name, expand=True):
        """
        Expand or Collapse client in FSO landing page
        Args:
            row_entity_name (str) : Entity name belonging to target row
            expand (bool) : Whether to expand or collapse
        """
        self.__rtable.expand_row(row_entity_name, expand)

    @PageService()
    def select_details_action(self, entity_name):
        """
        Select details action for given FSO Client/DataSource
            Args:
                entity_name (str):- FSO client name/FSO Data source name
        """
        self.__rtable.access_action_item(
            entity_name,
            self.__admin_console.props['label.configuration'])

    @PageService()
    def get_fso_datasource_list(self):
        """
        Get list of FSO data sources present in FSO client
        after expanding client row
        """
        if self.__rSubTable.has_next_page():
            self.__rSubTable.set_pagination(self.__subGridPaginationValue)
        return self.__rSubTable.get_column_data(self.__admin_console.props['label.datasource.name'])

    @PageService()
    def view_datasources(self):
        """Selects Data sources on FSO landing page"""
        self.__admin_console.access_tab('Data sources')


class FileStorageOptimizationClientDetails:
    """
     This class contains all the methods for Web action/page service in client details page
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__modal_dialog = RModalDialog(self.__admin_console)
        self.__table = Rtable(self.__admin_console)
        self.__admin_console.load_properties(self)

    @PageService()
    def select_datasource(self, datasource_name):
        """
        Selects FSO data source
            Args:
                datasource_name (str)  - Client name to be selected
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        self.__table.access_link(datasource_name)

    @PageService()
    def select_details_action(self, entity_name):
        """
        Select details action for given FSO DataSource
        (Override parent method as page is in angular)
            Args:
                entity_name (str):- FSO client name/FSO Data source name
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        self.__table.access_action_item(entity_name, self.__admin_console.props['label.configuration'])

    @WebAction()
    def check_if_datasource_exists(self, datasource_name):
        """
        Searches for FSO data source in client details page
            Args:
                datasource_name (str): Name of FSO data source
            Returns:
                (bool) True/False based on presence of data source
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        return self.__table.is_entity_present_in_column(
            self.__admin_console.props['label.datasource'],
            datasource_name)

    @WebAction()
    def select_delete_action(self, entity_name):
        """
        Select delete action for given FSO Client / FSO Data source name
            Args:
                entity_name (str):- FSO client name/ FSO Data source name
        """
        self.__table.access_action_item(
            entity_name,
            self.__admin_console.props['label.delete'])

    @PageService()
    def delete_fso_datasource(self, data_source_name):
        """
        Delete given FSO data source
        Args:
            data_source_name (str): Name of FSO data source
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.datasource.title'])
        self.select_delete_action(data_source_name)
        self.__modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()


class FsoDataSourceDiscover:
    """
     This class contains all the methods for Web action/page service in FSO
     Datasource discover page.
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)

    @WebAction()
    def get_duplicate_file_count(self):
        """
        Get duplicate file count from FSO duplicate dashboard
        Returns:
            (int): Duplicate file count
        """
        xpath = '//div[@id="component_Hits1602273571012"]//h5'
        return self.__admin_console.driver.find_element(By.XPATH, xpath).text

    @WebAction()
    def get_duplicate_file_size(self):
        """
        Get Duplicate file size from FSO Duplicate dashboard
        Returns:
            (str): Duplicate file size in format ('10 KB')
        """
        xpath = '//div[@id="component_Hits1602261899734"]//h5'
        return self.__admin_console.driver.find_element(By.XPATH, xpath).text

    @WebAction()
    def fso_dashboard_entity_count(self, entity_name):
        """
        Get FSO Dashboard entity count
        Args:
            entity_name (str): Entity name whose count to be fetched
        Returns:
            (str) Count of Entity in FSO dashboard
        """
        return self.__admin_console.driver.find_element(By.XPATH,
                                                        f'//h4[text()="{entity_name}"]/following-sibling::h5').text

    @WebAction()
    def get_file_security_dashboard_user_count(self, permission_type):
        """
        Get the user count for a particular permissions in FSO
        Security dashboard
        Args:
            permission_type (str): Type of permission
        Return:
            (int) -- no of user having mentioned permission
        """
        base_xp = f"//div[contains(@ id,'Panel_{permission_type}')]//h3"
        count = self.__admin_console.driver.find_elements(By.XPATH, base_xp)[0].text.split('(')[1].strip(')')
        if str(count).__eq__(''):
            count = '0'
        return int(count)

    @WebAction()
    def __click_dashboard_dropdown(self):
        """
        Click dashboard drop down in FSO report page
        """
        x_path = "//div[@id='customDatasourceReport']//a[@data-toggle='dropdown']"
        elem = self.__admin_console.driver.find_element(By.XPATH, x_path)
        if elem.get_attribute('aria-expanded').__eq__('false'):
            elem.click()

    @PageService()
    def select_fso_dashboard(self, dashboard_name):
        """
        Select passed dashboard for FSO client
        Args:
             dashboard_name (str): Name of FSO Dashboard
        """
        self.__admin_console.access_tab(dashboard_name)
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_for_react_errors()

    @PageService()
    def load_fso_dashboard(self, cloud_app_type=None):
        """
        Load FSO Dashboards
        Args:
            cloud_app_type  (str)   :   Type of the cloud app ( AZURE / AWS / GCP ) for selectively
                                        validating dashboards
        """

        if cloud_app_type and cloud_app_type in FSO_DASHBOARDS_TO_VERIFY.keys():
            dashboards_to_check = FSO_DASHBOARDS_TO_VERIFY[cloud_app_type]
        else:
            dashboards_to_check = FSO_DASHBOARDS_TO_VERIFY['ALL']

        for dashboard_name in dashboards_to_check:
            self.select_fso_dashboard(self.__admin_console.props[dashboard_name])
            self.__admin_console.check_error_message()

    @PageService()
    def select_fso_review_tab(self):
        """
        Select Review tab in FSO review page
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.review'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def download_csv_from_report_actions(self):
        """
        Download csv from report actions
        """
        self.__admin_console.access_page_action_menu_by_class("popup")
        save_element = self.__admin_console.driver.find_element('xpath', '//*[text()="Save as"]')
        save_element.click()
        csv_element = self.__admin_console.driver.find_element('xpath', '//*[text()="CSV"]')
        csv_element.click()
        self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()

    @PageService()
    def download_csv_treesize_dashboard(self, all_data=True):
        """
        Download csv from treesize dashboard
        """
        self.__admin_console.click_button_using_text("Export to CSV")
        if all_data:
            self.__admin_console.click_button_using_text("All data")
        else:
            self.__admin_console.click_button_using_text("Folders")


class FsoDataSourceReview:
    """
     This class contains all the methods for Web action/page service in FSO
     Datasource review page.
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__fso_discover = FsoDataSourceDiscover(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__dropdown = RDropDown(self.__admin_console)
        self.time_dict = {
            1: "0 to 1 Year",
            2: "1 to 2 Years",
            3: "2 to 3 Years",
            4: "3 to 4 Years",
            5: "4 to 5 Years",
            6: "5 Years+"
        }

    @WebAction()
    def get_review_page_filter_time_data(self, filter_id):
        """
        Select filter dropdown
            Args:
                filter_id (str): ID of filter
        """
        facet_elem = self.__dropdown.get_values_of_drop_down(drop_down_id=filter_id)
        temp_dict = {}
        for elem in facet_elem:
            time_range = elem.split(' (')[0]
            data = elem.split('(')[1].strip(')')

            for key, value in self.time_dict.items():
                if time_range == value:
                    temp_dict[key] = data
        return temp_dict

    @WebAction()
    def get_fso_time_dict(self, filter_name):
        """
        Get (Access/Created/Modified) Time data for FSO data source
            Args:
                filter_name (str): Access Time/Modified Time/Created Time
            Returns: temp_dict (dict)  {
                            1:"66 k",2:"5 k",3:"11 k",4:"452 k",5:"56 k",6:"12 k"
                            }
        """
        facet_elem = self.__admin_console.driver.find_element(By.XPATH,
                                                              f"//cvfilterandsearch//label[text()= '{filter_name}']/ancestor::cvfacet"
                                                              )
        temp_dict = {}
        for key, value in self.time_dict.items():
            temp_dict[key] = facet_elem.find_element(By.XPATH,
                                                     f"//cvfacet//span[text() = '{value}']/following::span[1]"
                                                     ).text.strip()[1:-1]
        return temp_dict

    @PageService()
    def get_fso_time_info(self, cloud_app_type=None):
        """
        Get CreatedTime/AccessTime/Modified Time data for FSO datsource
            Args:
                cloud_app_type (str): Optional String argument containing the Type of Cloud App ( AZURE, AWS, GCP )


            Returns: temp_dict (dict) {
                                "CreatedTime": {1:"66 k",2:"5 k",3:"11 k",4:"452 k",5:"56 k",6:"12 k"},
                                "AccessTime": {1:"66 k",2:"5 k",3:"11 k",4:"452 k",5:"56 k",6:"12 k"},
                                ModifiedTime: {1:"66 k",2:"5 k",3:"11 k",4:"452 k",5:"56 k",6:"12 k"}
                            }
        """
        temp_dict = {}
        tabs_to_check = []
        if cloud_app_type:
            if cloud_app_type in FSO_DASHBOARD_TABS_TO_VERIFY.keys():
                tabs_to_check = FSO_DASHBOARD_TABS_TO_VERIFY[cloud_app_type]
            else:
                CVWebAutomationException(f"{cloud_app_type} is not present in {str(FSO_DASHBOARD_TABS_TO_VERIFY)}")
        else:
            tabs_to_check = FSO_DASHBOARD_TABS_TO_VERIFY['ALL']
        self.__fso_discover.select_fso_dashboard(self.__admin_console.props['reports.sizeDistribution'])
        self.__admin_console.check_error_message()
        self.__fso_discover.select_fso_review_tab()
        for tab_name in tabs_to_check:
            # self.select_review_page_filter(tab_name)
            tab_id = FSO_DASHBOARD_FILTERS_ID[tab_name]
            temp_dict[tab_name] = self.get_review_page_filter_time_data(tab_id)
        return temp_dict


class FsoDataSourceDetails:
    """
     This class contains all the methods for Web action/page service in FSO
     data source details  page.
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)


class FsoServerGroupDetails:
    """
     This class contains all the methods for Web action/page service in FSO
     server group details page.
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__admin_console.load_properties(self)

    @PageService()
    def check_if_client_exists(self, client_name):
        """
        Searches for a client in FSO Server group details page
            Args:
                client_name (str)  - Client name to be searched for
            Returns:
                 (bool) True/False based on the presence of the Client
        """
        return self.__table.is_entity_present_in_column(
            self.__admin_console.props['label.name'],
            client_name)

    @PageService()
    def select_server_details_action(self, entity_name):
        """
        Select details action for given FSO Client
            Args:
                entity_name (str):- FSO client name/FSO Data source name
        """
        self.__table.access_action_item(
            entity_name,
            self.__admin_console.props['label.configuration'])


class FSOMonitoringReport:
    """
        This class contains all the methods for the Web actions / Page Services in FSO File Monitoring Report page.
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console

    @WebAction()
    def __get_search_bar(self, searchbar_id):
        """
        Gets the search bar input field
        Args:
            searchbar_id    (str):  id of search bar
        """
        search_bar = self.__admin_console.driver.find_element(By.ID, searchbar_id)
        search_bar_input = search_bar.find_element(By.TAG_NAME, 'input')
        return search_bar_input

    @WebAction()
    def __select_hyperlink_using_text(self, hyperlink_text, wait_for_load=True):
        """
        Selects Hyper link using text
        Args:
            hyperlink_text (str)    :   Hyperlink Text
            wait_for_load   (bool)  :   True if user wants to wait for page to load false otherwise
        """
        self.__admin_console.select_hyperlink(hyperlink_text, wait_for_load=wait_for_load)

    @PageService()
    def open_monitoring_report_page(self):
        """
        Opens the File Monitoring Report Page
        """
        self.__select_hyperlink_using_text(self.__admin_console.props["label.datasource.FileMonitoringReport"])

    @PageService()
    def sort_monitoring_table(self, column_hyperlink_text, wait_for_load=True):
        """
        Sorts the File monitoring report table using a column link text
        Args:
            column_hyperlink_text   (str)   Hyperlink text for the column we are sorting
            wait_for_load   (bool)          True if user wants to wait for page to load false otherwise
        """
        self.__select_hyperlink_using_text(column_hyperlink_text, wait_for_load)

    @PageService()
    def access_monitoring_report_searchbar(self, search_text):
        """
        Access File Monitoring Report Search bar using id and enter text on it
        Args:
            search_text     (str):  text which user want to enter on search bar
        """
        search_bar = self.__get_search_bar("SearchBar1582903448847")
        search_bar.clear()
        search_bar.send_keys(search_text)


class FSODataSourceManagement:
    """Class contains all the methods for the Web actions / Page services in FSO Activate datasource management page"""

    def __init__(self, admin_console):
        """Init method of FSODataSourceManagement class
            Args:
                admin_console   (object)    -   Instance of AdminConsole class
        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.__ds_management_ID = 'dataSources'
        self.__dstable = Rtable(self.__admin_console, id=self.__ds_management_ID)
        self.__wizard = Wizard(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__add_manually_table_ID = 'AddDataSourceManually'
        self.__amtable = Rtable(self.__admin_console, id=self.__add_manually_table_ID)

    @WebAction()
    def __add_entry(self, entry_dict):
        """Adds a new datasource entry to the datasource property table
            Args:
                entry_dict      (dict)  -   Single FS Data source properties dictionary
                    example :
                        { "Server Host Name" : host_name,
                          "Data Source Name" : datasource_name,
                          "Country" : country_name,
                          "User Name" : user_name,
                          "Password" : password,
                          "DC Plan" : dc_plan_name,
                          "Access Node" : access_node_name,
                          "Share Path" : data_directory
                          }
        """
        self.__amtable.access_menu_from_dropdown(self.__admin_console.props['label.action.single'])
        self.__rdropdown.select_drop_down_values(values=[
            entry_dict[di_constants.CSV_HEADER_HOST_NAME].upper()], index=-4)
        self.__rdropdown.select_drop_down_values(values=[
            entry_dict[di_constants.CSV_HEADER_DC_PLAN]], index=-3)
        self.__rdropdown.select_drop_down_values(values=[
            entry_dict[di_constants.CSV_HEADER_COUNTRY]], index=-1)
        self.__rtable.type_input_for_row(-1, entry_dict[di_constants.CSV_UNC_SHARE_PATH], 'input')
        self.__rtable.type_input_for_row(-2, entry_dict[di_constants.CSV_DATA_SOURCE_NAME])
        if di_constants.CSV_HEADER_ACCESS_NODE in entry_dict:
            self.__enter_credentials(
                entry_dict[di_constants.CSV_HEADER_USERNAME], entry_dict[di_constants.CSV_HEADER_PASSWORD])
            self.__rdropdown.select_drop_down_values(values=[
                entry_dict[di_constants.CSV_HEADER_ACCESS_NODE]], index=-2)
        self.__click_row_action()

    @WebAction()
    def __upload_csv(self, csv_path):
        """Uploads csv file to data source management
            Args:
                csv_path       (str)   :   csv file path
        """
        upload = self.__driver.find_element(By.XPATH, "//input[contains(@data-testid,'input-file')]")
        upload.send_keys(csv_path)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __enter_credentials(self, username, password):
        """Enters the username and password require for the data source with Agent not installed server host
            Args:
                username    (str)       -   Username for the UNC path
                password    (str)       -   Password for given user
        """
        self.__rtable.type_input_for_row(-1, username)
        self.__rtable.click_forward_arrow(-1)
        self.__rtable.type_input_for_row(-1, password, 'password')

    @WebAction()
    def __click_row_action(self, action='save', row_number=0):
        """Clicks the row action save or cancel for the given row entry on table
            Args:
                action      (str)   -   Action string to be performed ('save'/'cancel')
                row_number  (int)   -   Row number on which the action has to perform
                                        (default : 0 (last row))
        """
        self.__rtable.select_row_action(row_number - 1, action)

    @PageService()
    def select_data_source(self, data_source_name):
        """Selects a data source from table
            Args:
                data_source_name    (str)   -   Data source name to be selected
        """
        self.__dstable.access_link_by_column(data_source_name, data_source_name)

    @PageService()
    def add_multiple_data_sources(self, inventory_name, manual_entry_dict=None, import_csv=False, csv_file_path=None):
        """Adds multiple data source to FSO with the help of csv file or by manually entering values
            Args:
                inventory_name      (str)   -   Inventory name to be used for data source creation
                manual_entry_dict   (dict)  -   Datasource configuration details
                import_csv          (bool)  -   Whether to add data sources from csv or not
                csv_file_path       (str)   -   csv file location using which we will add data sources
        """
        self.__dstable.access_menu_from_dropdown([self.__admin_console.props['addManually'],
                                                  self.__admin_console.props['addFromCSV']][import_csv])
        sleep(120)
        self.__rdropdown.select_drop_down_values(index=0, values=[inventory_name])
        if import_csv:
            self.__upload_csv(csv_path=csv_file_path)
            self.__wizard.click_next()
            sleep(300)
            self.__wizard.click_button('Create')
            self.__admin_console.wait_for_completion()
        else:
            self.__click_row_action('cancel')
            for entry in manual_entry_dict:
                self.__add_entry(entry)
            self.__wizard.click_button('Submit')
