from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
configure live sync replication group page of the AdminConsole

"""

from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.Components.panel import PanelInfo


class ConfigureVSAReplicationGroup:
    """Class for Configure VSA Replication Group Page"""

    def __init__(self, admin_console):
        """ """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver

    @WebAction()
    def __get_vms(self):
        """Gets all VMs of VMGroup
            Returns: All VM elements
        """
        return self.__driver.find_elements(By.XPATH, 
            "//*[@id='selectContentForm']/div[4]/div/div/isteven-multi-select/"
            "span/div/div[2]/div[1]/div/label/span")

    @WebAction()
    def __set_suffix(self):
        """Enters restore suffix"""
        self.__driver.find_element(By.XPATH, '//*[@id="restoreOptionsOCIForm"]/div'
                                            '/div/div/div/cv-display-name-azure'
                                            '/div[1]/div[2]'
                                            '/input').send_keys("_DeleteMeAC")

    @WebAction()
    def __get_subnet(self):
        """Finds available subnets
        Returns: Available subnets
        """
        return self.__driver.find_elements(By.XPATH, "//*[@id='subnet']/span/div")[0].text

    @WebAction()
    def __expand_advanced_options(self):
        """Expands Advanced options"""
        self.__driver.find_element(By.XPATH, 
            '//*[@id="restoreOptionsOCIForm"]/div/div/div/cv-oci-compartments-settings/div[6]'
            '/uib-accordion/div/div/div[1]/span[1]').click()

    @WebAction()
    def __override_options(self):
        """Get override options for the selected vm"""
        self.__driver.find_element(By.XPATH, '//*[@id="vmSelections"]/span/button').click()

    @WebAction()
    def __select_subnet(self, subnet_name):
        """Select subnet with given subnet ID"""
        _xp = '//*[@id="cloudNetwork"]/span/div/div[2]/div[1]/div/label/span'
        ind = 2
        while self.__admin_console.check_if_entity_exists("xpath", _xp):
            vcn_name = self.__driver.find_element(By.XPATH, _xp).get_attribute("innerHTML")
            self.__admin_console.cv_single_select("Virtual cloud network", vcn_name)
            self.__admin_console.wait_for_completion()
            subnet_path = f'//*[@id="subnet"]/span/div/div[2]/div[@title="{subnet_name}"]'
            if self.__admin_console.check_if_entity_exists("xpath", subnet_path):
                self.__admin_console.cv_single_select("Subnet", subnet_name)
                self.__admin_console.wait_for_completion()
                self.__driver.find_element(By.XPATH, '//*[@id="subnet"]').click()
                break
            self.__admin_console.cv_single_select("Virtual cloud network", "")
            self.__admin_console.wait_for_completion()
            _xp = f'//*[@id="cloudNetwork"]/span/div/div[2]/div[{ind}]/div/label/span'
            ind += 1

    @PageService()
    def configure_vsa_replication_group(self, dict_vals):
        """Configures Live Sync VSA replication group

            Args:
                dict_vals: Dictionary object containing hypervisor, replication_group_name,
                vm_backupgroup, replication_target, proxy, compartment, datastore, vcn and shape

            Sample dict_vals:
            dict_vals = {
            'hypervisor': '',
            'replication_group_name': '',
            'vm_backupgroup': '',
            'replication_target': '',
            'proxy': '',
            'compartment': '',
            'datastore': '',
            'vcn': '',
            'shape': '',
            'vm_name': '',
            'subnet_name": ''
            }

        """
        self.__admin_console.cv_single_select("Hypervisors", dict_vals['hypervisor'])
        self.__admin_console.fill_form_by_id("name", dict_vals['replication_group_name'])
        self.__admin_console.cv_single_select("Select VM group", dict_vals['vm_backupgroup'])
        self.__admin_console.wait_for_completion()
        vms = self.__get_vms()
        for _vm in vms:
            self.__admin_console.cv_single_select("Select VMs", _vm.text)
        self.__admin_console.button_next()
        self.__admin_console.select_hyperlink("Create new")
        self.__admin_console.cv_single_select("Select vendor", 'Oracle Cloud Infrastructure')
        self.__admin_console.fill_form_by_id("replicationTargetName",
                                             dict_vals['replication_target'])
        self.__admin_console.cv_single_select("Destination hypervisor", dict_vals['hypervisor'])
        self.__admin_console.cv_single_select("Access node", dict_vals['proxy'])
        self.__set_suffix()
        self.__admin_console.cv_single_select("Compartment", dict_vals['compartment'])
        self.__admin_console.cv_single_select("Availability domain", dict_vals['datastore'])
        # self.__admin_console.cv_single_select("Virtual cloud network", dict_vals['vcn'])
        self.__select_subnet(dict_vals['subnet_name'])
        self.__admin_console.cv_single_select("Shape", dict_vals['shape'])
        self.__admin_console.cv_single_select("Access node", dict_vals['proxy'])
        self.__admin_console.submit_form()
        self.__admin_console.button_next()
        self.__admin_console.click_button('Yes')
        self.__admin_console.cv_single_select("Virtual machine", dict_vals['vm_name'])
        self.__override_options()
        self.__admin_console.wait_for_completion()
        self.__admin_console.button_next()
        self.__admin_console.click_button("Finish")

    @PageService()
    def configure_vsa_replication_group_azure(self, dict_vals):
        """Configures Live Sync VSA replication group for azure

            Args:
                dict_vals: Dictionary object containing hypervisor, replication_group_name,
                vm_backupgroup, replication_target, proxy, compartment, datastore, vcn and shape

            Sample dict_vals:
            dict_vals = {
            'hypervisor': '',
            'replication_group_name': '',
            'vm_backupgroup': '',
            'vms':[],
            'replication_target': '',
            'proxy': '',
            'resource_group': '',
            'region': '',
            'storage_account': '',
            'storage_copy': '',
            'dvdf': True/False
            }

        """
        try:
            self.__admin_console.cv_single_select("Hypervisors", dict_vals['hypervisor'])
        except:
            self.__admin_console.log.info("Hypervisor is not already selected")
        self.__admin_console.fill_form_by_id("name", dict_vals['replication_group_name'])
        try:
            self.__admin_console.cv_single_select("Select VM group", dict_vals['vm_backupgroup'])
        except:
            self.__admin_console.log.info("VM group is already selected")
        self.__admin_console.wait_for_completion()
        for _vm in dict_vals['vms']:
            self.__admin_console.cv_single_select("Select VMs", _vm)
        self.__admin_console.button_next()

        self.__admin_console.wait_for_completion()
        self.__admin_console.select_hyperlink("Create new")
        self.__admin_console.cv_single_select("Select vendor", 'Microsoft Azure')
        self.__admin_console.fill_form_by_id("replicationTargetName", dict_vals['replication_target'])
        self.__admin_console.cv_single_select("Azure hypervisor", dict_vals['hypervisor'])
        self.__admin_console.cv_single_select("Access node", dict_vals['proxy'])
        self.__admin_console.driver.find_element(By.XPATH, 
            '//*[@id="replicationTargetForm"]//cv-display-name-azure/div[1]/div[2]/input').clear()
        self.__admin_console.driver.find_element(By.XPATH, '//*[@id="replicationTargetForm"]//cv-display-name-azure'
                                                          '/div[1]/div[2]/input').send_keys('RGDelete')
        self.__admin_console.select_value_from_dropdown("azureContainer", dict_vals['resource_group'])
        self.__admin_console.select_value_from_dropdown("azureRegion", dict_vals['region'])
        self.__admin_console.select_value_from_dropdown("azureAvailabilityZone", 'Auto')
        self.__admin_console.cv_single_select("Storage account", dict_vals['storage_account'])
        self.__admin_console.click_button('Add')

        if dict_vals['dvdf']:
            self.__admin_console.enable_toggle(index=1, cv_toggle=True)
        else:
            self.__admin_console.disable_toggle(index=1, cv_toggle=True)
        if 'storage_copy' in dict_vals:
            self.__admin_console.select_value_from_dropdown("copyPrecedence", dict_vals['storage_copy'])
        self.__admin_console.button_next()

        self.__admin_console.click_button('No')
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button("Finish")
        self.__admin_console.log.info("Replication Group = %s created successfully")
