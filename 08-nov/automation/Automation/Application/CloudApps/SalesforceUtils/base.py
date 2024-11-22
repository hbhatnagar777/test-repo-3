# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Base file for handling config/testcase inputs for all Salesforce helper classes

SalesforceBase is the only class defined in this file

SalesforceBase: Base class for all Salesforce helper classes

SalesforceBase:
    __init__()                          --  initializes SalesforceBase object

    updated_salesforce_options()        --  Returns updated values in salesforce_options using parameters passed

    updated_infrastructure_options()    --  Returns updated values in salesforce_options using parameters passed

    decode_input()                      --  Parses testcase input dictionary and converts values to python objects if
    they are passed as string

    cleanup()                           --  Method to clean up entities from previous TC run

    Properties:
        **salesforce_options**          --  Salesforce options from config updated with any values in testcase inputs

        **infrastructure_options**      --  Infrastructure options from config updated with any values in testcase inputs
"""
import os
import json
from json.decoder import JSONDecodeError
from types import SimpleNamespace
from enum import Enum
from AutomationUtils.config import get_config
from AutomationUtils import logger
from .constants import DbType

_CONFIG_DATA = get_config().Salesforce


class SalesforceBase:
    """Base class for SalesforceHelper classes"""

    def __init__(self, tcinputs=None, commcell=None):
        """
        Constructor for the class. Pass commcell object to use CvConnector object. If tcinputs is not passed, then
        inputs will be read from config file.

        Args:
            commcell (Commcell): commcell object
            tcinputs (dict): testcase inputs

        Returns:
            None:
        """
        if not commcell:
            raise Exception("Commcell parameter is required but not passed")
        self._log = logger.get_log()
        self._tcinputs = self.decode_input(tcinputs or dict())
        self._commcell = commcell
        self.__infrastructure_options = \
            _CONFIG_DATA.infrastructure_options._asdict() | self._tcinputs.get('infrastructure_options', dict())
        self.__sqlserver_options = \
            _CONFIG_DATA.sqlserver_options._asdict() | self._tcinputs.get('sqlserver_options', dict())
        self.__postgresql_options = \
            _CONFIG_DATA.postgresql_options._asdict() | self._tcinputs.get('postgresql_options', dict())
        if self.__infrastructure_options.get('db_type', None) == DbType.SQLSERVER.value:
            self.__infrastructure_options |= self.__sqlserver_options
        else:
            self.__infrastructure_options |= self.__postgresql_options
        self.__salesforce_options = \
            _CONFIG_DATA.salesforce_options._asdict() | self._tcinputs.get('salesforce_options', dict())

    @property
    def infrastructure_options(self):
        """
        Returns infrastructure options dict as SimpleNamespace

        Returns:
            SimpleNamespace: infrastructure_options
        """
        return SimpleNamespace(**self.__infrastructure_options)

    @property
    def salesforce_options(self):
        """
        Returns salesforce options dict as SimpleNamespace

        Returns:
            SimpleNamespace: salesforce_options
        """
        return SimpleNamespace(**self.__salesforce_options)

    @property
    def postgresql_options(self):
        """
        Returns PostgreSQL options dict as SimpleNamespace

        Returns:
            SimpleNamespace: postgresql_options
        """
        return SimpleNamespace(**self.__postgresql_options)

    @property
    def sqlserver_options(self):
        """
        Returns SQLServer options dict as SimpleNamespace

        Returns:
            SimpleNamespace: sqlserver_options
        """
        return SimpleNamespace(**self.__sqlserver_options)

    def updated_salesforce_options(self, **update_dict):
        """
        Updates values in salesforce_options using parameters passed and returns as SimpleNamespace. Use this method to
        construct dictionaries for passing as input to Command Center methods/cvpysdk if some parameters need to be
        different from defaults in tcinputs/config.

        Args:
            update_dict: Keyword arguments to override tcinputs/config options

        Returns:
            SimpleNamespace: salesforce_options
        """
        update_dict = {key: val.value if isinstance(val, Enum) else val for key, val in update_dict.items()}
        return SimpleNamespace(**(self.__salesforce_options | update_dict))

    def updated_infrastructure_options(self, **update_dict):
        """
        Updates values in infrastructure_options using parameters passed and returns as SimpleNamespaces. Use this
        method to construct dictionaries for passing as input to Command Center methods/cvpysdk if some parameters need
        to be different from defaults in tcinputs/config.

        Args:
            update_dict: Keyword arguments to override tcinputs/config options

        Returns:
            SimpleNamespace: infrastructure_options
        """
        update_dict = {key: val.value if isinstance(val, Enum) else val for key, val in update_dict.items()}
        return SimpleNamespace(**(self.__infrastructure_options | update_dict))

    def __getattr__(self, item):
        """
        Allows for accessing values set in config file from testcase as attributes of helper object

        Args:
            item (str): Attribute name

        Returns:
            Config value
        """
        try:
            return self._tcinputs[item]
        except KeyError:
            return getattr(_CONFIG_DATA, item)

    @staticmethod
    def decode_input(tcinputs):
        """
        Parses testcase input dictionary and converts values to python objects if they are passed as string

        Args:
            tcinputs (dict): Testcase inputs

        Returns:
            dict: Decoded testcase inputs
        """
        for key, val in tcinputs.items():
            try:
                tcinputs[key] = json.loads(val)
            except (JSONDecodeError, TypeError):
                pass
        return tcinputs

    def cleanup(self, tc_file_path):
        """
        Method to clean up entities from previous run

        Args:
            tc_file_path (str): path to the test case file

        """
        tc_number = os.path.splitext(os.path.basename(tc_file_path))[0]
        for client in self._commcell.clients.all_clients:
            if (tc_number in client) and (client not in (self._tcinputs.get("ClientName", "").lower(),
                                                         self._tcinputs.get("DestinationClientName", "").lower())):
                try:
                    self._log.info(f"Deleting existing Pseudo-Client {client}")
                    self._commcell.clients.delete(client)
                except Exception as exp:
                    self._log.error(f"Unable to delete client {client}. {exp}")
