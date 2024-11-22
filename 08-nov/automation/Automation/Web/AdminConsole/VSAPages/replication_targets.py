from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done on the Replication
targets page.


Classes:

    Replicationtargets() ---> _Navigator() ---> LoginPage --->
    AdminConsoleBase() ---> object()


Replicationtargets  --  This class contains all the methods for action in
                        Replication targets page and is inherited by other
                        classes to perform VSA realted actions

    Functions:

    add_replication_target()          --  Adds a new replication target with
                                          the specified inputs and proxy.
    select_replication_target()       --  Opens the replication target with the
                                          given name
    action_delete()                   --  delete a replication target with the
                                          specified name
"""
from Web.AdminConsole.Components.table import Rtable as Table
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.panel import PanelInfo


class ReplicationTargets:
    """
     This class contains all the methods for action in replication targets page
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__table = Table(admin_console)
        self.__panel = PanelInfo(admin_console, self.__admin_console.props['pageTitle.replication.summary'])

    @WebAction()
    def add_replication_target(
            self,
            vendor_type,
            rep_target_name,
            destination_hypervisor,
            proxy,
            vm_display_name,
            destination_host,
            resource_pool,
            datastore,
            destination_network,
            prefix=False,
            test_failover_options=False,
            expiration_hours=True,
            expiration_time_hours=1,
            expiration_days=False,
            expiration_time_days=2,
            configure_isolated_network=False,
            gateway_template=None,
            migrate_vms=False):
        """
        Adds a new replication target with the specified inputs and proxy.

        Args:
            vendor_type             (str)   --  name of the vendor (vmware, amazon etc.)

            rep_target_name         (str)   --  name the user gives to the
                                                        replication target

            destination_hypervisor  (str)   --  client with the hypervisor.

            proxy                   (str)   --  proxy given by the user.

            vm_display_name         (str)   --  allows the user to give the prefix or
                                                        suffix in the name

            destination_host        (str)   --  name of esx host

            datastore               (str)   --  specify a datastore from the dropdown

            resource_pool           (str)   --  specify the resource pool from the dropdown

            destination_network     (str)   --  specify the destination network from the dropdown

            prefix                  (bool)  --  if prefix has to be added in vm display name

            test_failover_options   (bool)  --  to test failover options after replication

            expiration_hours        (bool)  --  if the replicated VM has to be up for hours

            expiration_time_hours   (int)   --  the no of hours the replicated VMs need to be up

            expiration_days         (bool)  --  if the replicated VM has to be up for days

            expiration_time_days    (int)   --  the no of days the replicated VMs need to be up

            configure_isolated_network  (bool)  --  if the replicated VMs need to be placed in
                                                    a isolated network

            gateway_template        (str)   --  the name of the gateway template to use for
                                                        isolated network

            migrate_vms             (bool)  --  if the replicated VMs need to be migrated

        Raises:
            Exception:
                if there is no option to add a replication target because the logged in user did
                    not have sufficient permissions or
                if there an error while creating replication targets

        """
        self.__driver.execute_script("window.scrollTo(0,0)")

        self.__admin_console.select_hyperlink("Add replication target")

        self.__admin_console.select_value_from_dropdown("vendorTypes", vendor_type)
        self.__admin_console.fill_form_by_id('replicationTargetName', rep_target_name)

        if prefix:
            self.__admin_console.select_radio("azureDisplayNamePrefix")

        # self.fill_form_by_id("displayNamePrefixSuffix", vm_display_name)
        self.__driver.find_element(By.XPATH, "//div/input[@name='displayNamePrefixSuffix']"
                                            ).send_keys(vm_display_name)

        if vendor_type == 'VMware':
            self.__driver.find_element(By.XPATH, "//cv-select-hypervisors[@vendor='VMW']").click()
            self.__driver.find_element(By.XPATH, "//cv-select-hypervisors//div[@class="
                                                "'line-search']/input"
                                                ).send_keys(destination_hypervisor)
            elements = self.__driver.find_elements(By.XPATH, "//cv-select-hypervisors//div["
                                                            "@class='checkBoxContainer']/div")
            for element in elements:
                if element.find_element(By.XPATH, "./div/label/span").text == " " \
                        + destination_hypervisor:
                    element.find_element(By.XPATH, "./div/label/span").click()
            self.__driver.find_element(By.XPATH, "//cv-select-proxy[@vendor='VMW']").click()
            self.__driver.find_element(By.XPATH, "//cv-select-proxy//div[@class='line-search']"
                                                "/input").send_keys(proxy)
            elements = self.__driver.find_elements(By.XPATH, "//cv-select-proxy//div[@class="
                                                            "'checkBoxContainer']/div")
            for element in elements:
                if element.find_element(By.XPATH, "./div/label/span").text == " " + proxy:
                    element.find_element(By.XPATH, "./div/label/span").click()
            self.__admin_console.wait_for_completion()

            # Browsing and selecting the destination host
            self.__driver.find_element(By.XPATH, '//span[@class="input-group-btn"]/'
                                                'button').click()
            self.__admin_console.wait_for_completion()

            self.__admin_console.select_destination_host(destination_host)
            self.__admin_console.submit_form()

            self.__admin_console.select_value_from_dropdown("dataStore", datastore, True, False)
            self.__admin_console.select_value_from_dropdown("resourcePool", resource_pool, False, False)
            self.__admin_console.select_value_from_dropdown("networkSettingsDestination", destination_network)

            if test_failover_options:
                self.__admin_console.checkbox_select("showVirtualLab")
                if expiration_hours:
                    self.__admin_console.fill_form_by_id("expirationTimeInHours", expiration_time_hours)
                if expiration_days:
                    self.__admin_console.select_radio("Day(s)")
                    self.__admin_console.fill_form_by_id("expirationTimeInDays", expiration_time_days)
                if configure_isolated_network:
                    self.__admin_console.checkbox_select("createIsolatedNetwork")
                    self.__admin_console.select_destination_host(gateway_template)
                    self.__admin_console.submit_form()
                if migrate_vms:
                    self.__admin_console.checkbox_select("migrateVMs")
            self.__admin_console.submit_form()

    @PageService()
    def select_replication_target(self, rep_target_name):
        """
        Opens the replication target with the given name

        Args:
            rep_target_name     (str)   --  name of replication target

        Raises:
            Exception:
                if there is no replication target with the given name

        """
        self.__table.access_link(rep_target_name)

    @PageService()
    def action_delete(self, rep_target_name):
        """
        delete a replication target with the specified name

        Args:
            rep_target_name     (str)   --  name of replication target

        """
        self.__table.access_context_action_item(rep_target_name, self.__admin_console.props['label.delete'])
        self.__admin_console.click_button(self.__admin_console.props['button.yes'])

    @PageService()
    def get_destination_hypervisor(self, rep_target_name=None):
        """
        Get Destination Hypervisor from page summary

         Args:
            rep_target_name                   (str)    : name of recovery target

        Returns:
            panel_details.get_details()        (dict)   : info about the recovery target
        """
        if rep_target_name:
            self.select_replication_target(rep_target_name)
        dest_hv = self.__panel.get_details()[self.__admin_console.props['header.destinationHypervisor']]
        return dest_hv
