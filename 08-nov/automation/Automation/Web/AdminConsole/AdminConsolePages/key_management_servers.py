# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to key management servers in AdminConsole
KeyManagementServers : This class provides methods for key management server related operations

KeyManagementServers:

    select_kms()        -- To select a key management server

    delete_kms()        -- To delete a key management server

    add_aws_kmsp()      -- To add a new AWS KMSP

    add_kmip()          -- To add a new KMIP

"""
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService, WebAction


class KeyManagementServers:
    """
    This class provides the function or operations that can be
    performed on key management servers Page of the Admin Console
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__props = self.__admin_console.props
        self.__table = Table(admin_console)
        self.driver = admin_console.driver

    @PageService()
    def select_kms(self, server_name):
        """
        To select a key management server

        Args:
        server_name     (str)       -- Name of the key management server to be selected

        """
        self.__table.access_link(server_name)

    @WebAction()
    def delete_kms(self, server_name):
        """
        To delete a key management server

        Args:
            server_name     (str)       -- Name of the key management server to be deleted

        """
        if self.__admin_console.check_if_entity_exists('id', 'search-field'):
            self.__table.access_action_item(server_name, 'Delete')
            self.driver.find_element(By.XPATH, "//button[text()='Yes'][@ng-click='yes()']").click()
            self.__admin_console.check_error_message()

    @PageService()
    def add_aws_kmsp(
            self,
            name=None,
            region=None,
            access_key=None,
            secret_access_key=None):
        """
        To add a new AWS KMSP

        Args:
            name        (str)   -- Name for the KMS

            region      (str)   -- Region to be selected for the KMS

            access_key  (str)   -- Access key for the KMS

            secret_access_key   (str)   -- Secret access key for the KMS

        """
        self.__admin_console.select_hyperlink(self.__props['action.add'])
        self.__admin_console.select_hyperlink(self.__props['label.awsKmsp'])
        self.__admin_console.fill_form_by_id('name', name)
        self.__admin_console.cv_single_select(self.__props['label.region'], region)
        self.__admin_console.fill_form_by_id('accessKey', access_key)
        self.__admin_console.fill_form_by_id('secretAccess', secret_access_key)
        self.__admin_console.submit_form()
        self.__admin_console.__admin_console.check_error_message()

    @PageService()
    def add_kmip(
            self,
            name=None,
            key_length=None,
            server=None,
            port=None,
            passphrase=None,
            certificate=None,
            certificate_key=None,
            ca_certificate=None):
        """
        To add a new KMIP

        Args:
            name        (str)   -- Name of the KMIP to be added

            key_length  (str)   -- Keylength for encryption

            server      (str)   -- Server for the KMIP

            port        (str)   -- Port for the KMIP

            passphrase  (str)   -- Passphrase for the KMIP

            certificate (str)   -- Certificate path for the KMIP

            certificate_key (str)   -- Certificate key path for the KMIP

            ca_certificate  (str)   -- CA Certificate path for the KMIP

        """
        self.__admin_console.select_hyperlink('Add')
        self.__admin_console.select_hyperlink('KMIP')
        self.__admin_console.fill_form_by_id('name', name)
        self.__admin_console.select_value_from_dropdown('keyLength', key_length)
        self.__admin_console.fill_form_by_id('server', server)
        self.__admin_console.fill_form_by_id('port', port)
        self.__admin_console.fill_form_by_id('passphrase', passphrase)
        self.__admin_console.fill_form_by_id('certificate', certificate)
        self.__admin_console.fill_form_by_id('certificateKey', certificate_key)
        self.__admin_console.fill_form_by_id('caCertificate', ca_certificate)
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()
