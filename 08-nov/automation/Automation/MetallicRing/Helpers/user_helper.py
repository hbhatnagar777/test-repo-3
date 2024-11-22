# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for User related operations in Metallic Ring

    UserRingHelper:

        __init__()                      --  Initializes User Ring Helper

        start_task                      --  Starts the user related tasks for metallic ring

        update_user_properties          --  Updates the user's properties(username and password)

"""

from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Helpers.network_helper import NetworkRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class UserRingHelper(BaseRingHelper):
    """ helper class for User related operations in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)

    def start_task(self):
        """
        Starts the user related tasks for metallic ring
        """
        try:
            nrh = NetworkRingHelper(self.commcell)
            nrh.check_communication_with_cs()
            user_info = _CONFIG.commserv
            self.log.info("User helper task started")
            if user_info.new_username is None or user_info.new_password is None \
                    or not user_info.new_password or not user_info.new_username:
                raise Exception("New username and new password information is missing in the configuration file.")
            if not (user_info.username == user_info.new_username and user_info.password == user_info.new_password):
                self.log.info("Updating username and password")
                self.update_user_properties(user_info.username, user_info.password,
                                            user_info.new_username, user_info.new_password)
                self.log.info("updated username and password")
            self.log.info("User helper task complete. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute user helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def update_user_properties(self, username, password, new_username, new_password):
        """
        Updates the user's properties(username and password)
        Args:
            username(str)               -   name of the user to be updated
            password(str)               -   password for the user
            new_username(str)           -   new username for the user
            new_password(str)           -   new password to be updated for the user
        Raises:
            Exception:
                When username with given name doesn't exist
        """
        if not self.users.has_user(username):
            raise Exception(f"User with given name [{username}] doesn't exist")
        self.log.info("Received request to update user properties")
        user = self.users.get(username)
        self.log.info("Updating user password")
        user.update_user_password(new_password, password)
        self.log.info(f"User password updated successfully. Updating user name from [{username}] to [{new_username}]")
        user.user_name = new_username
        self.log.info("User name updated successfully")
        self.users.refresh()
