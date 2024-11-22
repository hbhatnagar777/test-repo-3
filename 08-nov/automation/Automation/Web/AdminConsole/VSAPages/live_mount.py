# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for submitting Live Mount for VMware

Classes:

    LiveMount() --- > _Navigator() ---> AdminConsoleBase() ---> Object()

LiveMount --  This class contains methods for submitting Live Mount.

Functions:

    submit_LiveMount()       --  Submits a VMware Live Mount

"""

from Web.AdminConsole.Components.panel import RDropDown, ModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import (
    WebAction,
    PageService
)


class LiveMount:
    """
    This class contains methods for submitting Live Mount.
    """

    def __init__(self, admin_console):
        """ Init for LiveMount class"""
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__rdropdown_obj = RDropDown(admin_console)
        self.__modalpanel = ModalPanel(admin_console)

    @WebAction()
    def __select_live_mount_policy(self, live_mount_policy_name):
        """
        Args:
            live_mount_policy_name:  (str) name of the live mount policy to be selected
        """
        self.__rdropdown_obj.select_drop_down_values(values=[live_mount_policy_name], drop_down_id='recoveryTarget')
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_network(self, network):
        """
        Args:
            network : (str) name of the network
        """
        self.__rdropdown_obj.select_drop_down_values(values=[network], drop_down_id='vmNetworks')
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_copy_precedence(self, copy_precedence):
        """
        Args:
            copy_precedence : (str) copy precedence to be selected
        """
        self.__rdropdown_obj.select_drop_down_values(values=[copy_precedence], drop_down_id='copyPrecedence',
                                                     case_insensitive_selection=True)
        self.__admin_console.wait_for_completion()

    @PageService()
    def submit_live_mount(self,
                          live_mount_policy_name,
                          network,
                          copy_precedence,
                          passkey=None):
        """
        Args:
            live_mount_policy_name: (str) name of the live mount policy

            network :              (str) name of the network

            copy_precedence:        (str) copy precedence to be selected

            passkey:                (str) passkey for restores
        raises:
            Exception if error in submitting live mount
        """
        try:
            self.__select_live_mount_policy(live_mount_policy_name)
            self.__admin_console.wait_for_completion()
            self.__select_network(network)
            self.__select_copy_precedence(copy_precedence)
            self.__admin_console.click_submit(wait=False)

            if passkey:
                passkey_dialog = RModalDialog(self.__admin_console, title='Authorize for restore')
                passkey_dialog.fill_text_in_field('passkey', passkey)
                passkey_dialog.click_submit()
                self.__admin_console.check_error_message()
                self.__admin_console.click_submit(wait=False)

            self.__admin_console.log.info('Live mount job submitted successfully')
            live_mount_job_id = self.__admin_console.get_jobid_from_popup()
            return live_mount_job_id
        except Exception as exp:
            self.__admin_console.log.info('Failed with error: ' + str(exp))
