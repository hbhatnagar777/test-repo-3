# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Arrays Details Page on the Alert page of AdminConsole

Class:

    ArrayDetails()

Functions:

array_info()                    --  Displays all the information about the array
delete_array()                  --  Deletes the array
edit_snap_configuration()       --  Editing the snap configuration of the array
click_list_snapshots()          --  Click on list snapshot button at array details page
"""

from Web.AdminConsole.Components.panel import PanelInfo ,ModalPanel , DropDown , RPanelInfo , RDropDown
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.AdminConsolePages.Arrays import _Snap_config
from Web.AdminConsole.Components.dialog import RModalDialog
from AutomationUtils.database_helper import get_csdb


class ArrayDetails():
    """
    this class provides the function or operations that can be performed on the Arrays Details Page
    """
    def __init__(self, admin_console):

        """Method to initiate Array Details Class
                Args:
                        admin_console   (Object) :   Admin Console Class object"""

        self.__driver = admin_console.driver
        self.__panel_info = None
        self.__admin_console = admin_console
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__navigator = admin_console.navigator
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__csdb = get_csdb()
        self.snap_config_obj = _Snap_config(self.__admin_console, self.__csdb)
        self.__dropdown = DropDown(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)


    @PageService()
    def array_info(self):
        """
        Displays all the information about the array
        :return array_info  (dict)  --  info about the array
        """
        panel_details = PanelInfo(self)
        return panel_details.get_details()

    @PageService()
    def delete_array(self):
        """
        Deletes the array
        """

        self.__admin_console.click_button_using_text('Delete')
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button_using_text('Yes')

    @PageService()
    def edit_snap_configuration(self,
                                array_vendor,
                                array_name,
                                snap_config=None):
        """
                Editing the snap configuration of the array
                Args:

                    snap_vendor                  (str)   --  the name of the vendor
                    array_name                   (str)   --  the name of the array to be added
                    snap_config                  (str)   --  snap configurations to be edited
        """

        self.__rtable.access_link(array_name)
        self.__admin_console.access_tab("Configuration")
        RPanelInfo(self.__admin_console, 'Snap configurations').edit_tile()
        self.__admin_console.wait_for_completion()
        self.snap_config_obj.add_snapconfig(snap_config, array_vendor)
        self.__admin_console.click_button("Submit")
        self.__admin_console.wait_for_completion()

    @PageService()
    def edit_general(self,
                     array_name , region):
        """

        Args:
            array_name: name of the array
            region: region

        """


        self.__rtable.access_link(array_name)
        PanelInfo(self.__admin_console, 'General').edit_tile()
        self.__admin_console.wait_for_completion()
        self.__admin_console.cvselect_from_dropdown("Region", region)
        self.__admin_console.click_button("Save")
        self.__admin_console.wait_for_completion()



    @PageService()
    def edit_array_access_node(self,
                               array_name, controllers):
        """

        Args:
            array_name: name of the array
            controllers: controllers

        """

        self.__rtable.access_link(array_name)
        self.__admin_console.access_tab("Configuration")
        RPanelInfo(self.__admin_console, 'Array access nodes').edit_tile()
        self.__admin_console.wait_for_completion()
        self.__rdropdown.select_drop_down_values(values=[controllers], drop_down_id='availableMediaAgents')
        rmd=RModalDialog(self.__admin_console,title="Edit array access nodes")
        rmd.click_submit()
        self.__admin_console.wait_for_completion()


    def clear_access_node(self, array_name):
        """Clears all access nodes set on the array

            args:
                array_name : String : Name of array

        """
        self.__rtable.access_link(array_name)
        self.__admin_console.access_tab("Configuration")
        RPanelInfo(self.__admin_console, 'Array access nodes').edit_tile()
        self.__admin_console.wait_for_completion()
        node_list = self.__rdropdown.get_selected_values(drop_down_id='availableMediaAgents')
        self.__rdropdown.deselect_drop_down_values(values=node_list,drop_down_id='availableMediaAgents')
        rmd = RModalDialog(self.__admin_console, title="Edit array access nodes")
        rmd.click_submit()
        self.__admin_console.wait_for_completion()

    def disable_pruning(self, array_name):
        """Disables pruning on all array nodes

            args:
                array_name : String : Name of array
        """
        self.__rtable.access_link(array_name)
        self.__admin_console.access_tab("Configuration")
        RPanelInfo(self.__admin_console, 'Array access nodes').edit_tile()
        self.__admin_console.wait_for_completion()
        node_list = self.__rdropdown.get_selected_values(drop_down_id='availableMediaAgents')
        rmd = RModalDialog(self.__admin_console, title="Edit array access nodes")
        ma_list = rmd._get_elements(".//input[@type='checkbox']")
        for ma in ma_list:
            ma.click()

        rmd.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def click_list_snapshots(self):
        """
        Click on list snapshot button at array details page

        """
        self.__admin_console.refresh_page()
        self.__admin_console.click_button_using_text(self.__admin_console.props['action.listSnaps'])


