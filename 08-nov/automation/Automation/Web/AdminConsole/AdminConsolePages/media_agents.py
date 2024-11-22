# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to media agents page

==============

    access_media_agent()        --    selects the media agent with the given name

    delete_media_agent()        --    deletes the media agent with the given name

    reload_data()               --    Reloads the table data

    is_media_agent_exists()     --    check media agent entry existence from media agents page

    retire_media_agent()         --    Retires the media agent with the given name

    install_media_agent()        --    This installs MediaAgent on the given clients and returns the job id of the installation job

"""

from Web.AdminConsole.Components.table import CVTable, Rtable
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.Common.page_object import PageService, WebAction

class MediaAgents:
    """
    Class for media agents page in Admin console

    """

    def __init__(self, admin_console):
        """ Initialize the MediaAgents obj

        Args:
            admin_console (AdminConsole): AdminConsole object

        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__table = CVTable(self.__admin_console)
        self.__rtable = Rtable(admin_console)
        self.__rdiag = RModalDialog(self.__admin_console)
        self.__props = self.__admin_console.props

    @PageService()
    def access_media_agent(self, media_agent):
        """
        selects the media agent with the given name

        Args:
            media agent    (str)   -- Name of the media agent to be opened
        """
        self.__rtable.access_link(media_agent)

    @PageService()
    def delete_media_agent(self, media_agent):
        """
        Deletes the media agent with the given name

        Args:
            media_agent (str) - name of the media agent to be deleted
        """
        self.__table.access_action_item(media_agent, self.__props['action.delete'])
        diag = ModalDialog(self.__admin_console)
        diag.type_text_and_delete('confirm')
        self.__admin_console.check_error_message()

    @PageService()
    def reload_data(self):
        """
        Reloads the table data
        """
        self.__rtable.reload_data()

    @PageService()
    def is_media_agent_exists(self, media_agent):
        """ check media agent entry existence from media agents page
        Args:
            media_agent    (str)   -- name of the media agent to be checked

        returns: boolean
            True: if media agent exists
            false: if media agent does not exists
        """
        status = self.__rtable.is_entity_present_in_column(column_name='MediaAgent',
                                                           entity_name=media_agent)
        return status

    @PageService()
    def retire_media_agent(self, media_agent):
        """
        Retires the media agent with the given name

        Args:
            media_agent (str) - name of the media agent to be retired
        """
        self.__rtable.access_action_item(
            media_agent, self.__props['action.commonAction.retire'])
        self.__rdiag.type_text_and_delete(
            "Reviewed the impact report and carried out the recommendations",
            button_name='Retire')
        self.__admin_console.check_error_message()

    @WebAction()
    def _add_hostnames(self,r_modal_dialog, hostnames):
        """
        Types all the provided hostnames in the hostname field of the modal dialog (Add MA Dialog)
        
        Args:
            r_modal_dialog (RModalDialog)  --  RModalDialog object of the Add MA Dialog
            hostnames (list(str))            --  hostnames of the media agent machine
        """

        all_hostnames = ""

        for hostname in hostnames:
        # \ue007 is the unicode for enter key
            all_hostnames += hostname + u'\ue007'
        
        r_modal_dialog.fill_text_in_field("hostname",all_hostnames)
    
    @WebAction()
    def _fill_ma_details_and_submit(self,r_modal_dialog: RModalDialog,hostnames,os_type,username,password,saved_credential_name,**kwargs):
        """
        Acts as a helper function for Adding MA and fills the ma_details and submits the given Add/Install MA dialog
        
        Args:
            r_modal_dialog (RModalDialog)  --  RModalDialog object of the Add/Install MA Dialog

            hostnames (list(str))  --  hostnames of the media agent machine

            username (str | None)       --  username of the media agent machine

            password (str | None)       --  password of the media agent machine

            os_type (str)        --  os type of the media agent machine , values can be "windows","linux","unix"

            saved_credential_name (str | None) --  saved credential name , default is None

            Available kwargs Options:

                software_cache (str) --  software cache client name , default is None

                port_number (int)    --  port number , default is 22

                install_location (str)    --  installation location

                reboot_if_required (bool) --  reboot if required , default is False
        """

        software_cache = kwargs.get("software_cache",None)
        port_number = kwargs.get("port_number",22)
        install_location = kwargs.get("install_location",None)
        reboot_if_required = kwargs.get("reboot_if_required",False)

        self._add_hostnames(r_modal_dialog,hostnames)

        if os_type != "windows":
            r_modal_dialog.select_radio_by_id("unix")
            r_modal_dialog.fill_text_in_field("sshPortNumber",port_number)

        if software_cache:
            r_modal_dialog.select_dropdown_values('remoteCacheClientDropdown', values=[software_cache])
            
        if saved_credential_name:
            r_modal_dialog.enable_toggle("savedCredentials")
            r_modal_dialog.select_dropdown_values('credentials', values=[saved_credential_name])
        elif username and password:
            r_modal_dialog.fill_text_in_field("username",username)
            r_modal_dialog.fill_text_in_field("password",password)
            r_modal_dialog.fill_text_in_field("confirm_password",password)
        else:
            raise Exception("Either saved credentials or username and password should be provided")
        
        if install_location:
            r_modal_dialog.fill_text_in_field("installation_location",install_location)

        if reboot_if_required:
            r_modal_dialog.enable_toggle("reboot")

        r_modal_dialog.click_button_on_dialog(self.__props["label.install"])
        self.__admin_console.check_error_message()

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def install_media_agent(self,hostnames,os_type,username = None,password = None,saved_credential_name = None,**kwargs):
        """
        This installs MediaAgent on the given clients and returns the job id of the installation job
         
        Opens the Add MA dialog in Media Agent Page and then fills the details and submits it

        Args:
            hostnames (list(str))  --  hostnames of the media agent machine

            username (str | None)       --  username of the media agent machine , default is None

            password (str | None)       --  password of the media agent machine , default is None

            os_type (str)        --  os type of the media agent machine , values can be "windows","linux","unix"

            saved_credential_name (str | None) --  saved credential name , default is None

            Available kwargs Options:

                software_cache (str) --  software cache client name , default is None

                port_number (int)    --  port number , default is 22

                install_location (str)    --  installation location

                reboot_if_required (bool) --  reboot if required , default is False

        Returns: 
            job id of the installation job
        """

        self.__rtable.access_toolbar_menu(self.__props["title.addMediaAgent"])
        r_modal_dialog = RModalDialog(self.__admin_console,title = self.__props["title.addMediaAgent"])

        return self._fill_ma_details_and_submit(r_modal_dialog,hostnames,os_type,username,password,saved_credential_name,**kwargs)