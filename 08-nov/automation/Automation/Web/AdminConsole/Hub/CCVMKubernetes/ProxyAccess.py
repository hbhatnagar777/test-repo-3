# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Backup Gateway Tab on Metallic

"""
from selenium.common.exceptions import NoSuchElementException

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from selenium.webdriver.common.by import By
from Web.Common.page_object import (
    PageService,
    WebAction
)
from Web.Common.exceptions import (
    CVWebAutomationException
)
import time
from Install.install_custom_package import InstallCustomPackage
from Web.AdminConsole.Hub.utils import Utils
from AutomationUtils.machine import Machine
from AutomationUtils import constants

class ProxyAccess:
    """
    Class for configure Hyper-v Proxy Access Page
    """
    def __init__(self, wizard, admin_console, metallic_options,commcell_info=None):

        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__commcell = commcell_info['commcell']
        self.__commcell_info = commcell_info
        self.__base_xpath = "//bc-app-config"
        self.metallic_components = VSAMetallicHelper.getInstance(admin_console, metallic_options,commcell_info)
        self.utils = Utils(admin_console)
        self.log = self.__admin_console.log
        self.__wizard = wizard
        self.__dialog = RModalDialog(admin_console)
        self.metallic_options = metallic_options
        self.config()

    def config(self):

        self.configure_proxy_access()

    @PageService()
    def existing_proxy_access(self, dropdown_id=None, proxy=None):
        """
        selects the existing backup gateway provided in the options
        Returns:    None

        """
        proxy_name = self.metallic_options.proxy_client_name
        gateway_dropdown_id = 'accessNodes'
        if proxy:
            proxy_name = proxy
        if dropdown_id:
            gateway_dropdown_id = dropdown_id
        self.log.info(f"selecting existing backup gateway named {proxy_name}")
        time.sleep(30)
        self.__wizard.click_refresh_icon(1)
        self.__wizard.select_drop_down_values(id=gateway_dropdown_id, values=[proxy_name])
        time.sleep(30)

    @PageService()
    def configure_proxy_access(self):
        """
        configure new proxy-access
        Returns:    None

        """
        self.__download_proxy_exe()
        proxy_machine = {
            'remote_clientname': self.metallic_options.hyp_host_name,
            'remote_username': self.metallic_options.proxy_remote_username,
            'remote_userpassword': self.metallic_options.proxy_remote_userpassword
        }
        install_helper = InstallCustomPackage(self.__commcell, proxy_machine)
        if self.metallic_options.install_through_authcode:
            install_helper.install_custom_package(
                full_package_path=self.download_path, authcode=self.metallic_components.organization.auth_code)
        else:
            install_helper.install_custom_package(
                self.download_path, self.__commcell_info['user'],
                self.__commcell_info['password'])

        try:
            self.existing_proxy_access()
            self.log.info("Successfully installed and registered the Virtual Server Software on the proxy.")
        except NoSuchElementException as exp:
            self.log.exception("Failed to register backup gateway with commcell")
            raise CVWebAutomationException(exp)
        finally:
            self.controller_machine.delete_file(self.download_path)

        self.__wizard.click_button('Discover nodes')
        self.__admin_console.wait_for_completion()
        self.__wizard.select_drop_down_values(id="accessNodes",
                                              values=[self.metallic_options.proxy_client_name.upper()])

    @WebAction()
    def __download_proxy_exe(self):
        """
        method to download proxy access software
        """
        import socket
        self.controller_machine = Machine(socket.gethostname())
        self.download_path = self.controller_machine.join_path(constants.TEMP_DIR, self.metallic_options.app_type.split()[0],"WindowsVirtualServer64.exe")
        try:
            self.controller_machine.delete_file(self.download_path)
        except:
            pass

        text = 'Metallic VSA package'
        link_xpath =  f"//*[contains(text(),'{text}')]"
        self.__driver.find_element(By.XPATH, link_xpath).click()
        time_taken = 0
        time.sleep(120)
        time_taken = time_taken + 2
        while not self.controller_machine.check_file_exists(self.download_path):
            if time_taken > 15:
                raise CVWebAutomationException("time out during the gateway package download")
            time.sleep(120)
            time_taken = time_taken + 2
        self.log.info("gateway exe file coped successfully")
