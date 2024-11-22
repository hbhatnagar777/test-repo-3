# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on SNMP Configuration page.

Classes:

    SNMPConfigurationMain

Functions:

    create_configuration       --  Add a configuration to the SNMP Configuration page

    modify_configuration       --  Modifies/Edits the Added configuration

    del_configuration          --  Method to delete the SNMP Configuration

    validate_SNMPConfiguration --  Validates the Configuration added by create_configuration method
"""

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.SNMPConfiguration import SNMPConfiguration


class SNMPConfigurationMain:
    """
    Helper file to provide arguments and handle function call to main file
    """
    encryption_algorithms = [
        "HMAC_MD5", "HMAC_SHA", "HMAC128_SHA224",
        "HMAC192_SHA256", "HMAC256_SHA384", "HMAC384_SHA512"
    ]
    privacy_algorithms = [
        "CBC_DES", "CFB128_AES128", "CBC_AES128"
    ]

    def __init__(self, admin_console):
        """
        Initialize method for SNMPConfigurationMain
        """
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__snmp_config = SNMPConfiguration(self.__admin_console)

        self.log = logger.get_log()
        self._config_name = None
        self._username = "Tester A"
        self._password = "########"
        self._privacy_password = "########"
        self._old_config_name = None
        self._encryption_algorithm = None
        self._privacy_algorithm = None
        self.edit_config = 0

    @property
    def config_name(self):
        """ Get Configuration name"""
        return self._config_name

    @config_name.setter
    def config_name(self, value):
        """ Set Configuration name"""
        self._config_name = value
        if self._old_config_name is None:
            self._old_config_name = value

    @property
    def username(self):
        """ Get username"""
        return self._username

    @username.setter
    def username(self, value):
        """ Set username"""
        self._username = value

    @property
    def password(self):
        """ Get password"""
        return self._password

    @password.setter
    def password(self, value):
        """ Set password"""
        self._password = value

    @property
    def privacy_password(self):
        """ Get private password"""
        return self._privacy_password

    @privacy_password.setter
    def privacy_password(self, value):
        """ Set private password"""
        self._privacy_password = value

    @property
    def privacy_algorithm(self):
        """ Get private password"""
        return self._privacy_algorithm

    @privacy_algorithm.setter
    def privacy_algorithm(self, value):
        """ Set private password"""
        self._privacy_algorithm = value

    @property
    def encryption_algorithm(self):
        """ Get private password"""
        return self._encryption_algorithm

    @encryption_algorithm.setter
    def encryption_algorithm(self, value):
        """ Set private password"""
        self._encryption_algorithm = value

    def create_configuration(self):
        """Calls the function to create Configuration"""

        self.__navigator.navigate_to_snmp()
        self.__snmp_config.add_configuration(
            self.config_name,
            self.encryption_algorithm,
            self.username,
            self.password,
            self.privacy_algorithm,
            self.privacy_password)
        self._encryption_algorithm = [self.encryption_algorithm]
        self._privacy_algorithm = [self.privacy_algorithm]

    def modify_configuration(self):
        """Calls the function to modify Configuration"""

        self.__navigator.navigate_to_snmp()
        for value_encrypt in self.encryption_algorithm:
            for value_private in self.privacy_algorithm:
                self.edit_config += 1
                if self.edit_config == 1:
                    self.__snmp_config.edit_configuration(
                        self._old_config_name,
                        self.config_name,
                        value_encrypt,
                        self.username,
                        self.password,
                        value_private,
                        self.privacy_password)
                else:
                    self.__snmp_config.edit_configuration(
                        self.config_name,
                        self.config_name,
                        value_encrypt,
                        self.username,
                        self.password,
                        value_private,
                        self.privacy_password)

    def del_configuration(self):
        """Calls the function to delete Configuration"""

        self.__navigator.navigate_to_snmp()
        self.__snmp_config.delete_configuration(self.config_name)

    def validate_snmp_configuration(self):
        """ Validates SNMP configuration for the values, if retained correctly or not """

        self.__navigator.navigate_to_snmp()
        details = self.__snmp_config.configuration_details(self.config_name)

        if not details['Host name'] == [self.config_name]:
            exp = "Config name given %s does not match with %s displayed" \
                  % ([self.config_name], details['Host name'])
            self.log.exception(exp)
            raise Exception(exp)
        self.log.info("Config name given %s matched with %s displayed"
                      % ([self.config_name], details['Host name']))

        if not details['User name'] == [self.username]:
            exp = "User name given %s does not match with %s displayed" \
                  % ([self.username], details['User name'])
            self.log.exception(exp)
            raise Exception(exp)
        self.log.info("User name given %s matched with %s displayed"
                      % ([self.username], details['User name']))

        if self.encryption_algorithm:
            if not details['Authentication algorithm'] == self.encryption_algorithm:
                exp = "encryption algorithm given %s does not match with %s displayed" \
                      % (self.encryption_algorithm, details['Authentication algorithm'])
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("encryption algorithm given %s matched with %s displayed"
                          % (self.encryption_algorithm, details['Authentication algorithm']))

        if self.privacy_algorithm:
            if not details['Privacy algorithm'] == self.privacy_algorithm:
                exp = "privacy algorithm given %s does not match with %s displayed" \
                      % (self.privacy_algorithm, details['Privacy algorithm'])
                self.log.exception(exp)
                raise Exception(exp)
            self.log.info("privacy algorithm given %s matched with %s displayed"
                          % (self.privacy_algorithm, details['Privacy algorithm']))

        self.log.info("Configuration validated successfully, all values are correctly retained")
