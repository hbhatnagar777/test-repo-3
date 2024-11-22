# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the NAS_File_Servers page for Nutanix Files.

NutanixFiles        --  Class for Nutanix Files.

add_nutanix_files() --  Method to add Nutanix Files client.

NutanixFiles Instance Attributes:
=================================

    **current_add_button_index**    --  Returns the index value of the current Add button in focus.

    **current_edit_button_index**   --  Returns the index value of the current Edit button in focus.

"""

from Web.AdminConsole.Components.panel import DropDown
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.FileServerPages.network_share import NFS, CIFS
from Web.AdminConsole.NAS.nas_file_servers import NutanixFilesArray


class NutanixFiles:

    def __init__(self, admin_console, array_details):
        """
        Method to initialize NutanixFiles class.

        Args:
            admin_console   (object)    :   Instance of AdminConsole.

            array_details   (dict)      :   The dictionary of array details.
            Dictionary contains the keys array_name, control_host, username and password.

                array_name      (str)    :   Name of the array.

                control_host    (str)    :   Control host name if applicable to the array.

                username        (str)    :   Username for the array, defined in CoreUtils\\config.json.

                password        (str)    :   Password for the array, defined in CoreUtils\\config.json.

        """
        self.admin_console = admin_console
        self.array_details = array_details
        self.__drop_down = DropDown(self.admin_console)
        self._current_add_button_index = 0
        self._current_edit_button_index = 0

    @property
    def current_add_button_index(self):
        """
        Returns the current index of the Add button on the Add NAS Server page.
        """
        return self._current_add_button_index

    @current_add_button_index.setter
    def current_add_button_index(self, value):
        """
        Updates the current index of the Add button on the Add NAS Server page.
        """
        self._current_add_button_index = value

    @property
    def current_edit_button_index(self):
        """
        Returns the current index of the Edit button on the Add NAS Server page.
        """
        return self._current_edit_button_index

    @current_edit_button_index.setter
    def current_edit_button_index(self, value):
        """
        Updates the current index of the Edit button on the Add NAS Server page.
        """
        self._current_edit_button_index = value

    @PageService()
    def add_nutanix_files(self, name, plan, **kwargs):
        """
        Adds a new Nutanix Files Client with the Chosen iDAs and Access Nodes.

        Args:
            name    (str)   :   The  name of the NAS/Network Share client to be created.

            plan    (str)   :   The name of the plan that needs to be associated to the client.

            kwargs  (str)   :   Optional arguments.

                cifs            (dict)  :   The dictionary of CIFS Agent details.
                Dictionary contains the keys access_nodes, impersonate_user and content.

                    access_nodes        (list)  :   List of access node names, access node names are strings.

                    impersonate_user    (dict)  :   The dictionary of impersonation account details.
                    Dictionary contains the keys username and password.

                        username    (str)    :   Username of the account, defined in CoreUtils\config.json.

                        password    (str)    :   Password of the account, defined in CoreUtils\config.json.

                    content             (list)  :   List of content paths, content paths are strings.

                nfs            (dict)  :   The dictionary of NFS Agent details.
                Dictionary contains the keys access_nodes, impersonate_user and content.

                    access_nodes        (list)  :   List of access node names, access node names are strings.

                    content             (list)  :   List of content paths, content paths are strings.
        """
        self.admin_console.click_by_id("addFileServer")
        self.admin_console.access_sub_menu("Nutanix Files")
        self.admin_console.fill_form_by_id("clientName", name)

        if kwargs['array_details']['array_name'] not in self.__drop_down.get_values_of_drop_down('nutanix-create-array'):
            self.admin_console.select_hyperlink('Add', self.current_add_button_index)
            array = NutanixFilesArray(self.admin_console, kwargs.get('array_details', None))
            array.fill_array_details(kwargs['array_details'])
            self.admin_console.submit_form()
        else:
            self.__drop_down.select_drop_down_values(values=[kwargs['array_details']['array_name']], drop_down_id='nutanix-create-array')

        # SELECT PLAN
        self.__drop_down.select_drop_down_values(values=[plan], drop_down_id='planSummaryDropdown')

        # IF CIFS IS SELECTED, FILL IN ALL RELEVANT DETAILS
        if kwargs.get('cifs', None):
            self.admin_console.enable_toggle(0)
            kwargs.update({'ida': 'cifs'})
            cifs = CIFS(self.admin_console, kwargs['cifs'])

            # ADD ACCESS NODES
            self.current_add_button_index += 1
            self.admin_console.select_hyperlink('Add', self.current_add_button_index)
            cifs.add_access_nodes()

            # EDIT IMPERSONATE USER
            self.current_edit_button_index += 1
            self.admin_console.select_hyperlink('Edit', self.current_edit_button_index)
            cifs.edit_impersonate_user()

            # EDIT CONTENT
            self.current_edit_button_index += 1
            self.admin_console.select_hyperlink('Edit', self.current_edit_button_index)
            cifs.edit_content()

        # IF NFS IS SELECTED, FILL IN ALL RELEVANT DETAILS
        if kwargs.get('nfs', None):
            self.admin_console.enable_toggle(1)
            kwargs.update({'ida': 'nfs'})
            nfs = NFS(self.admin_console, kwargs['nfs'])

            # ADD ACCESS NODES
            self.current_add_button_index += 1
            self.admin_console.select_hyperlink('Add', self.current_add_button_index)
            nfs.add_access_nodes()

            # EDIT CONTENT
            self.current_edit_button_index += 1
            if kwargs.get('cifs', None):
                self.current_edit_button_index += 1
            self.admin_console.select_hyperlink('Edit', self.current_edit_button_index)
            nfs.edit_content()

        self.admin_console.submit_form()
