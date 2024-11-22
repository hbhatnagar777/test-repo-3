# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Helper file for performing precert and Registry operations

RegistryManager: Class for managing registry operations.

Methods:

    __init__(self, local_machine, build_helper, tcinputs, log) -- Initialize the RegistryManager class.

    _get_primary_data(self) -- Retrieves and validates the primary data from tcinputs.

    _create_or_update_registry(self, key, value, data) -- Creates or updates a registry entry.

    _handle_batch_mode(self) -- Handles the registry updates in batch mode.

    _handle_loose_mode(self) -- Handles the registry updates in loose mode.

    create_registry(self) -- Creates or updates the registry entries based on the current configuration and mode.
"""

from Install.installer_constants import (
    REG_INTEGRATION_VALUE, REG_INTEGRATION_VALUE_BATCH, REG_INTEGRATION_VALUE_LOOSE, REG_INTEGRATION_BATCH_MEDIA,
    AUTOMATION, PRIMARY, REG_INTEGRATION_VALUE_BATCH_MEDIA, REG_FRESH_INSTALL_REQUESTID
)


class RegistryManager:
    """Class for managing registry operations."""

    def __init__(self, local_machine, build_helper, primaryvalue, log):
        """
        Initialize the RegistryManager class.

        Args:
            local_machine (object): The local machine object.
            build_helper (object): The build helper object.
            primaryvalue (string): The primaryvalue input.
            log (object): The log object.
        """
        self.local_machine = local_machine
        self.build_helper = build_helper
        self.primaryvalue = primaryvalue
        self.log = log
        self.regkey = AUTOMATION
        self.regvalue = PRIMARY
        self._integration_mode = None
        self._primary = None
        self._integration_type = None
        self._fresh_install_requestid = None
        self.data = self._get_primary_data()

    @property
    def primary(self):
        """
        Returns the primary key value.
        """
        if self.local_machine.check_registry_exists(key=self.regkey, value=self.regvalue):
            self._primary = self.local_machine.get_registry_value(commvault_key=self.regkey, value=self.regvalue)
        return self._primary

    @property
    def integration_mode(self):
        """
        Returns the integration mode (Media mode or batch mode).
        """
        if self.local_machine.check_registry_exists(key=self.regkey, value=REG_INTEGRATION_BATCH_MEDIA):
            self._integration_mode = self.local_machine.get_registry_value(commvault_key=self.regkey, value=REG_INTEGRATION_BATCH_MEDIA)
        return self._integration_mode

    @property
    def integration_type(self):
        """
        Returns the integration type (Loose update type or batch update type).
        """
        if self.local_machine.check_registry_exists(key=self.regkey, value=REG_INTEGRATION_VALUE):
            self._integration_type = self.local_machine.get_registry_value(commvault_key=self.regkey, value=REG_INTEGRATION_VALUE)
        return self._integration_type
    
    @property
    def fresh_install_requestid(self):
        """
        Returns the freshinstall request id if it exists
        """
        if self.local_machine.check_registry_exists(key=self.regkey, value=REG_FRESH_INSTALL_REQUESTID):
            self._fresh_install_requestid = self.local_machine.get_registry_value(commvault_key=self.regkey, value=REG_FRESH_INSTALL_REQUESTID)
        return self._fresh_install_requestid

    @fresh_install_requestid.setter
    def fresh_install_requestid(self, value):
        """
        Sets the freshinstall request id.
        
        Args:
            value (str): The value to be set.
        """
        self._fresh_install_requestid = value
    
    
    def delete_fresh_install_requestid(self):
        """
        deletes the freshinstall request id if it exists
        """
        try:
            if self.local_machine.check_registry_exists(key=self.regkey, value=REG_FRESH_INSTALL_REQUESTID):
                self._fresh_install_requestid = self.local_machine.remove_registry(key=self.regkey, value=REG_FRESH_INSTALL_REQUESTID)
                self.log.info(f"Deleted the registry entry {REG_FRESH_INSTALL_REQUESTID}")
            else:
                self.log.info(f"Registry entry {REG_FRESH_INSTALL_REQUESTID} does not exist")
        except Exception as err:
            print(err)
            raise Exception(err)
        
    

    def _get_primary_data(self):
        """
        Retrieves and validates the primary data from tcinputs.

        Returns:
            int: The primary data value.

        Raises:
            ValueError: If the primary data is not 0 or 1.
        """
        try:
            data = int(self.primaryvalue)
            if data not in {0, 1}:
                raise ValueError(f"Invalid value for primary: {data}. It should be 0 or 1")
            return data
        except ValueError:
            raise ValueError(f"Invalid value for primary: {self.primaryvalue}. It should be 0 or 1")

    def _create_or_update_registry(self, key, value, data):
        """
        Creates or updates a registry entry.

        Args:
            key (str): The registry key.
            value (str): The registry value name.
            data (int): The data to be set.
        """
        if not self.local_machine.check_registry_exists(key=key, value=value):
            self.local_machine.create_registry(key=key, value=value, data=data)
            self.log.info(f"Created Registry {value} with value {data}")
        else:
            self.local_machine.update_registry(key=key, value=value, data=data)
            self.log.info(f"Registry exists. Updated Registry {value} with value {data}")

    def _handle_batch_mode(self):
        """
        Handles the registry updates in batch mode.
        """
        self.log.info(f"[BATCH UPDATE MODE] Mark the updates ['{REG_INTEGRATION_VALUE_BATCH}']")
        self._create_or_update_registry(self.regkey, REG_INTEGRATION_VALUE, REG_INTEGRATION_VALUE_BATCH)
    
    def _handle_media_mode(self):
        """
        Handles the registry updates in batch Media mode.
        """
        self.log.info(f"[BATCH Media MODE] Mark the updates ['{REG_INTEGRATION_BATCH_MEDIA}']")
        self._create_or_update_registry(self.regkey, REG_INTEGRATION_VALUE, REG_INTEGRATION_BATCH_MEDIA)

    def _handle_loose_mode(self):
        """
        Handles the registry updates in loose mode.
        """
        self.log.info(f"Precert Running in [LOOSE UPDATE\MEDIA MODE]. Mark the updates in ['{REG_INTEGRATION_VALUE_LOOSE}']")
        self._create_or_update_registry(self.regkey, REG_INTEGRATION_VALUE, REG_INTEGRATION_VALUE_LOOSE)

        if self.build_helper.is_batch_media_mode():
            self.log.info(f"Run precert in batchmedia mode. Setting key {REG_INTEGRATION_BATCH_MEDIA} : [{REG_INTEGRATION_VALUE_BATCH_MEDIA}]")
            self._create_or_update_registry(self.regkey, REG_INTEGRATION_BATCH_MEDIA, REG_INTEGRATION_VALUE_BATCH_MEDIA)

    def create_registry(self):
        """
        Creates or updates the registry entries based on the current configuration and mode.
        """
        self._create_or_update_registry(self.regkey, self.regvalue, self.data)

        if self.build_helper.is_batch_mode():
            self._handle_batch_mode()
        elif self.build_helper.is_batch_media_mode():
            self._handle_media_mode()
        else:
            self._handle_loose_mode()

        self.log.info(f"Primary node is set to {self.primary}")
        self.log.info(f"Running Precert in: {self.integration_type}")
        self.log.info(f"Running Precert in BatchMedia: {self.integration_mode}")
