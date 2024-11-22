# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Rtable,CVTable
from Web.AdminConsole.Components.panel import ModalPanel, RDropDown,RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
import datetime
import time


class NetworkStore:
    """Class for network stores page"""

    def __init__(self, admin_console):

        """
        Args:
        admin_console(AdminConsole): adminconsole
        object
        """

        self._admin_console = admin_console
        self._driver = admin_console.driver

        # Components required
        self.__table = Rtable(self._admin_console)
        self.__cv_table = CVTable(self._admin_console)
        self.__panel = ModalPanel(self._admin_console)
        self.__dropdown = RDropDown(self._admin_console)
        self.__dialog = RModalDialog(self._admin_console)

    @PageService()
    def add_network_store(self, network_store_name, nfs_server, plan=None, protocol="SMB", cache_path=None, idx_path=None):
        """Method to add network store"""

        self.__table.access_toolbar_menu("Add")
        self._admin_console.fill_form_by_id("storeName", network_store_name)
        self.__dropdown.select_drop_down_values(drop_down_id="protocol", values=protocol)
        self.__dropdown.select_drop_down_values(drop_down_id="nfsServerDropdown", values=nfs_server)
        

        if plan:
            self.__dropdown.select_drop_down_values(drop_down_id="planListDropdown_nogroups", values=plan)
        
        if cache_path :
            self._admin_console.fill_form_by_id(
                "physicalPathFolder", cache_path)
        if idx_path :
            self._admin_console.fill_form_by_id(
                "physicalIndexCachePathFolder", idx_path)

        self._admin_console.click_button("Save")

    @PageService()
    def delete_network_store(self, network_store_name):
        """Method to delete a network store"""

        self.__table.access_action_item(network_store_name, "Delete")
        self._admin_console.click_button("Yes")

    @PageService()
    def edit_general_settings(self,general_settings):
        """This function is used to edit the general tile info for the HFS client

        Args:
            general_settings (dict): the key value pair for the props you want to change
        Usage:
            general_settings = {'file_server':"hfsserver","allowed_network":"1.1.1.1,1.1.1.1",      # for multiple allowed clients
                                    "access_type":["Read Only"],"squash_type":["No Root Squash"]}
        """
        RPanelInfo(self._admin_console, 'General').edit_tile()

        if general_settings.get('file_server', None):
            self.__dropdown.select_drop_down_values(drop_down_id="nfsServerDropdown",values=[general_settings['file_server']])

        if self.__get_supported_protocol() == "NFS":

            if general_settings.get('allowed_network', None):
                self._admin_console.fill_form_by_id("networkClients",general_settings['allowed_network'])
            
            if general_settings.get('access_type',None):
                self.__dropdown.select_drop_down_values(drop_down_id="accessTypeField",values=general_settings['access_type'])
                if "Read Only" in general_settings['access_type'][0]:
                    self.__dialog.click_submit()
            
            if general_settings.get('squash_type',None):
                self.__dropdown.select_drop_down_values(drop_down_id="squashType",values=general_settings['squash_type'])
        
        self._admin_console.submit_form()
        self._admin_console.check_error_message()

    @PageService()
    def edit_retention_settings(self,retention_settings):
        """This function is used to edit retention tile info for the HFS client

        Args:
            retention_settings (dict): the key value pair for the props you want to change
        Usage:
            retention_settings = {'retention_deleted':{'val':10,'period':"Week"},
            'version':"ON","retention_versions":{'val':10,'period':"Week"},
            "no_of_version":31,"version_interval":42}
        """
        panel_info = RPanelInfo(self._admin_console, 'Retention')
        panel_info.edit_tile()
        if retention_settings.get('retention_deleted',None):
            self._admin_console.fill_form_by_id("retentionInDays",retention_settings['retention_deleted']['val'])
            self.__dropdown.select_drop_down_values(drop_down_id="retentionPeriod",values=retention_settings['retention_deleted']['period'])

        if retention_settings.get('version',None):
            if retention_settings['version'] != "OFF":
                self._admin_console.enable_toggle(index=0,cv_toggle=False)
            else:
                self._admin_console.disable_toggle(index=0,cv_toggle=False)
        
        if retention_settings.get('retention_versions',None):
            self._admin_console.fill_form_by_id("versionsRetentionInDays",retention_settings['retention_versions']['val'])
            self._admin_console.select_value_from_dropdown(select_id="olderVersionRetentionPeriodValue",value=retention_settings['retention_versions']['period'])
        
        if retention_settings.get('no_of_version',None):
            self._admin_console.fill_form_by_id("minNoOfVersions",retention_settings['no_of_version'])
        
        if retention_settings.get('version_interval',None):
            self._admin_console.fill_form_by_id("versionInterval",retention_settings['version_interval'])
        
        self._admin_console.wait_for_completion()
        self._admin_console.click_button_using_id("configureNetworkStoreProperties_button_#6704")
        self._admin_console.check_error_message()
    
    @PageService()
    def add_pit_view(self,date_time,name=None,allowed_network_client=None):
        """Function to add PIT view on the HFS share

        Args:
            date_time (date): date and for which we need to create PIT
            name ([type], optional): [description]. Defaults to None.
            allowed_network_client ([type], optional): [description]. Defaults to None.
        """
        self._admin_console.select_hyperlink('Create point in time view')#(self._admin_console.props['title.createPITViews'])
        self.__select_date_time(date_time)
        if name:
            self._admin_console.fill_form_by_id("SnapName",name)
        if allowed_network_client:
            self._admin_console.fill_form_by_id("NFSClient",allowed_network_client)

        self._admin_console.click_button_using_id("configureNetworkStoreProperties_button_#6703")
        self._admin_console.check_error_message()
        time.sleep(60) #wait for PIT to get exported
        self._driver.refresh()
        self._admin_console.wait_for_completion()

    @PageService()
    def delete_pit_view(self,pit_name):
        """To delete PIT view of the share"""
        self.__cv_table.access_action_item(pit_name, "delete")
        self._admin_console.click_button("Yes")

    @WebAction()
    def __select_date_time(self,date_time):
        """To select date and time from calender 

        Args:
            date_time (time): time object. time.time()
                    {'year':"2021",'month':'december','date':31,'hours':9,'mins':19,'session':'AM'}
        """
        curr_time = time.time()
        if date_time > curr_time:
            raise Exception("Time should not be greater than current time")
        year, month, date, hrs, mins, session = datetime.datetime.fromtimestamp(date_time).strftime(
            '%y_%B_%d_%I_%M_%p').split('_')
        year_now, month_now, date_now, hrs_now, mins_now, session_now = datetime.datetime.fromtimestamp(curr_time).strftime(
            '%y_%B_%d_%I_%M_%p').split('_')
        time_dict = {'year': year, 'month': month.lower(), 'date': int(date)}

        if year_now == year_now and month == month_now and date == date_now :  # in this case the hrs and mins inputs are disabled by default
            # to tackle this issue we have to click down the hrs button
            # at 12 AM this won't work as we are disabling the down button too.
            time_dict['hfs_pit'] = True

        if session == session_now:
            time_dict['session'] = session
        
        time_dict['hours'] = int(hrs) 
        time_dict['mins'] = int(mins)
        self._admin_console.click_button_using_id(value="networStoreProperties_button_#8961") #calender button
        self._admin_console.date_picker(time_value=time_dict)
        self._admin_console.click_button("Close")

    @WebAction()
    def __get_supported_protocol(self):
        """To Get supported solution """
        return self._admin_console.get_element_by_xpath("//span[@class='pageDetailColumn' and text()='Supported protocols']/../span[2]").text

    @PageService()
    def access_hfs(self,name):
        """To open hybrid file store

        Args:
            name (str): name of HFS
        """
        self.__table.access_link(name)
