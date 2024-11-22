from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for all the actions that can be done of the Hypervisors Details page.


Classes:

    HypervisorDetails() ---> _Navigator() --->  AdminConsoleBase() ---> object()


HypervisorDetails  --  This class contains all the methods for action in a particular server's page

Functions:

    open_hypervisor_alert()         --  Opens the given raised alert of the hypervisor

    edit_proxy()                    -- Adds / Removes a proxy to the given server

    reorder_proxy()                 -- Reorders the proxies for the server

    proxy_info()                    -- Lists all the proxy of the server

    action_backup()                 -- Starts a backup of the given type for the specified
                                            collection

    add_subclient()                 --  Adds a new subclient with the given VMs as content

    select_vm_from_browse_tree()    -- browse_and_select_vms can take one these 1.Group by host
                                        2.VMs 3.Group by datastore

    action_delete_subclient()       -- Deletes a subclient with the given name

    delete_server()                 -- Deletes the entire server with the given name

    data_management()               -- Enables and disables the data backup capability
                                        of the server

    data_recovery()                 -- Enables and disables the data restore capability of
                                        the server

    jobs()                          --  Opens the jobs page with all the running jobs for
                                        the server

    select_overview_tab()            -- Selects the overview tab

    select_configuration_tab()      -- Selects the configurations tab

    select_vmgroup_tab()            -- Selects the vm groups tab

    select_content_tab()            -- Selects the content tab
    
    select_vm_tab()                 --  Selects the virtual machines tab

    open_subclient()                --  Opens a subclient with the given name

    edit_hypervisor_details()       -- This definition edits the server credentials

    select_total_vm_graph()         -- Opens the VM details page with all the VMs present
                                        in the server

    select_protected_vm_graph()     -- Opens the VM details page with all the protected VMs
                                        present in the server

    select_non_protected_vm_graph() -- Opens the VM details page with all the unprotected VMs
                                        present in the server

    select_backedup_with_error_vm_graph() -- Opens the VM details page with all the VMs that were
                                                backed up with errors

    action_subclient_restore()      -- Opens the restore page of the subclient from the
                                        server details page

    action_subclient_jobs()         -- Lists all the jobs of the specific subclient

    server_settings()               --  Sets properties like FBR and vCloud

    server_analytics()              --  Enables / Disables analytics on the server

    hyperv_monitor()                --  Enables / Disables the hyper-v monitor

    open_vm_provisioning_settings() -- Opens Vm provisioning settings

    enable_auto_scale()             --  Enables auto scale on client

    disable_auto_scale()            -- Disables auto scale on client

    configure_azure_vm_provisioning() -- Configures VMProvisioning settings on azure client

    fetch_aws_hypervisor_details()    -- Fetches the AWS hypervisor details

    hypervisor_name()                  -- Gets the current hypervisor name

     set_aws_auth()                  -- Sets authentication on AWS hypervisor
     
     action_list_snapshots()        -- list the snaps of particular vm group or VM at Hypervisor level

"""
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common import StaleElementReferenceException, NoSuchElementException
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName, hypervisor_type
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.panel import RPanelInfo, PanelInfo
from Web.AdminConsole.Components.panel import DropDown, RDropDown
from Web.AdminConsole.Components.core import TreeView, Toggle, Checkbox
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.Components.browse import CVAdvancedTree
from Web.AdminConsole.Components.dialog import RModalDialog


class HypervisorDetails:
    """
    This class contains all the methods for action in a particular server's page
    """

    def __init__(self, admin_console):
        """ """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__navigator = admin_console.navigator
        self.__table_obj = Table(admin_console)
        self.__wizard_obj = Wizard(admin_console)
        self.__rtable_obj = Rtable(admin_console)
        self.__panel_obj = RPanelInfo(admin_console)
        self.__modal_dialog_obj = RModalDialog(admin_console)
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__panel_rdropdown_obj = RDropDown(admin_console)
        self.cv_advanced_tree_browser = CVAdvancedTree(admin_console)
        self.__treeview_obj = TreeView(admin_console)
        self.__toggle_obj = None
        self.__page_container_obj = None
        self.hyp_ssl_check = {}

    @PageService()
    def open_hypervisor_alert(self, alert_name):
        """
        Opens the alert with the given name
        Args:
            alert_name  (str):   the name of the alert to open

        """
        self.__admin_console.select_configuration_tab()
        panel_info = PanelInfo(self.__admin_console, self.__admin_console.props['label.alerts.text'])
        panel_info.open_hyperlink_on_tile(alert_name)

    @PageService()
    def edit_proxy(self, proxies, remove_existing_proxies=False):
        """
        Adds / Removes a proxy to the given server

        Args:
            proxies   (dict or list):    dictionary with proxy groups and proxies to be selected OR
                                        list of proxies to be selected
                                        Examples :   [proxy1, proxy2]
                                                    {'proxyGroup' : [proxy_group1,proxy_group2],
                                                    'proxy' : [proxy3,proxy4]}

            remove_existing_proxies (bool): Remove existing proxies set on the hypervisor

        Raises:
            Exception:
                if the proxy list could not be edited

        """
        self.select_configuration_tab()
        proxy_panel_obj = RPanelInfo(self.__admin_console, title=self.__admin_console.props['heading.proxyNodes'])
        proxy_panel_obj.click_action_item('Edit')
        edit_access_nodes_modal = RModalDialog(self.__admin_console, title='Edit access nodes')

        if remove_existing_proxies:
            self.__treeview_obj.clear_all_selected()

        if isinstance(proxies, list):
            self.__treeview_obj.select_items(proxies)
        else:
            if proxies.get('proxy'):
                self.__treeview_obj.select_items(proxies['proxy'])
            if proxies.get('proxyGroup'):
                proxy_groups = [item + " (group)" for item in proxies['proxyGroup']]
                self.__treeview_obj.select_items(proxy_groups)
        edit_access_nodes_modal.click_submit()

    @PageService()
    def reorder_proxy(self, proxy_order):
        """
        Reorders the proxies for the server

        Args:
            proxy_order  (dict):    the order in which the proxies have to be arranged
                Sample value:   {'proxy1': 3, 'proxy2': 1, 'proxy3': 2}

        Raises:
            Exception:
                if the proxies could not be re-ordered

        """
        self.__admin_console.select_configuration_tab()
        panel_info = PanelInfo(self.__admin_console, title=self.__admin_console.props['header.vmAgent'])
        # panel_info.edit_tile()
        if self.__admin_console.check_if_entity_exists("link", "Reorder"):
            proxies = self.__driver.find_elements(By.XPATH,
                                                  "//div[@id='scroll-box']/ul/li")
            index = 1
            old_proxy_order = {}
            for proxy in proxies:
                old_proxy_order[proxy.find_element(By.XPATH, "./span/span").text] = index
                index += 1
            self.__driver.find_element(By.LINK_TEXT, "Reorder").click()
            for key in proxy_order.keys():
                source = self.__driver.find_element(By.XPATH, "//span[contains(text(),'" + key +
                                                    "')]")
                destination = self.__driver.find_element(By.XPATH, "//div[@id='scroll-box']/ul/li"
                                                                   "[" + str(proxy_order[key]) +
                                                         "]/span/span")
                ActionChains(self.__driver).drag_and_drop(source, destination).perform()
                self.__admin_console.wait_for_completion()
            # self.submit_form()
            panel_info.open_hyperlink_on_tile("Save")
            self.__admin_console.wait_for_completion()
            index = 1
            old_proxy_order = {}
            proxies = self.__driver.find_elements(By.XPATH,
                                                  "//div[@id='scroll-box']/ul/li")
            for proxy in proxies:
                old_proxy_order[proxy.find_element(By.XPATH, "./span/span").text] = index
                index += 1
            if old_proxy_order == proxy_order:
                self.__admin_console.log.info("Proxy reorder was successful")
            else:
                self.__admin_console.log.info("The proxy was not reordered properly.")

    @PageService()
    def get_service_account_proxies(self, tenant_account_name):
        """
        Fetches proxies from Admin Account

        Returns:
            proxy               (list): list of all proxies assigned to Admin Account
            tenant_account_name (str): name of the tenant account

        """
        self.__admin_console.select_overview_tab()

        general_panel = RPanelInfo(self.__admin_console, 'General')
        general_panel_details = general_panel.get_details()
        service_account_hypervisor_value = general_panel_details.get('Service account hypervisor')
        general_panel.open_hyperlink_on_tile(service_account_hypervisor_value)
        self.__admin_console.wait_for_completion()

        self.__admin_console.select_configuration_tab()

        service_account_proxies = self.proxy_info()
        self.__admin_console.wait_for_completion()

        tenant_account_xpath = '//div[@id="hypervisors-configuration-tenants-aws"]//a'
        self.__driver.find_element(By.XPATH, tenant_account_xpath).click()
        self.__admin_console.wait_for_completion()

        self.__admin_console.select_configuration_tab()
        return service_account_proxies

    @PageService()
    def proxy_info(self):
        """
        Lists all the proxies of the server

        Returns:
            proxy   (list): list of all proxies that has been assigned to server

        """
        self.__admin_console.select_configuration_tab()
        panel = RPanelInfo(self.__admin_console, title='Access nodes')
        proxylist = panel.get_list()

        if not proxylist:
            labels = panel.get_label()
            if any("This hypervisor is configured to use resources from service account." in label for label in labels):
                tenant_account_name = self.__driver.find_element(By.XPATH,
                                                                 "//span[contains(@class,'title-display')]").text
                proxylist = self.get_service_account_proxies(tenant_account_name)
        else:
            formatted_proxylist = [proxy.split('\n') for proxy in proxylist if "Auto scale" not in proxy]
            proxylist = [proxy for sublist in formatted_proxylist for proxy in sublist]

        return proxylist
    
    @PageService()
    def get_verify_ssl_cert_status(self):
        """
        Returns the status of the toggle of verify ssl certificate

        Returns:
            status   (boolean): the status of the toggle of verify ssl certificate

        """
        self.__admin_console.select_configuration_tab()
        panel = RPanelInfo(self.__admin_console, title='Options')
        return panel.checkbox.is_checked(id='enableSSLValidationToggle')
    
    @PageService()
    def action_backup(self, bkp_type, subclient):
        """
        Starts a backup of the given type for the specified collection

        Args:
            bkp_type    (BackupType):    the backup level, among the type in Backup.BackupType enum

            subclient   (str):   the name of the subclient to be backed up

        Returns:
            job_id  (int):  the backup job ID

        """
        self.__admin_console.select_overview_tab()
        self.__table_obj.access_action_item(subclient, self.__admin_console.props['action.commonAction.backup'])
        backup = Backup(self.__admin_console)
        return backup.submit_backup(bkp_type)

    @PageService()
    def add_subclient(
            self,
            subclient_name,
            vm_content,
            plan=None
    ):
        """
        Adds a new subclient with the given VMs as content

        Args:
            subclient_name  (str)    :   the name of the subclient to be created

            vm_content      (dict)          :   the content to be added to the subclient

                Sample value:   {'Datastores and datastore clusters':[ds1,ds2],
                                 'Hosts and clusters':[h1,h2],
                                 'Tags and categories':[tag1,category1],
                                 'VMs and templates':[vm1,vm2],
                                 'Storage':[strg1, strg2]
                                }

            plan            (str)    :   the plan to be associated with the subclient

        """
        self.__admin_console.select_overview_tab()
        self.__admin_console.access_menu(self.__admin_console.props['action.showAddVMGroup'])
        self.__admin_console.fill_form_by_id("name", subclient_name)
        self.select_vm_from_browse_tree(vm_content)
        self.__panel_dropdown_obj.select_drop_down_values(2, [plan])
        self.__admin_console.submit_form()
        self.__admin_console.check_error_message()

    @PageService()
    def select_vm_from_browse_tree(self, vm_content):
        """
        Select content for subclient from the browse tree

        Args:
            vm_content  (dict):     the content to be selected
                Sample value:   {'Datastores and datastore clusters':[ds1,ds2],
                                 'Hosts and clusters':[h1,h2],
                                 'Tags and categories':[tag1,category1],
                                 'VMs and templates':[vm1,vm2],
                                 'Storage':[strg1, strg2],
                                 'By region': [region1, region2],
                                 'By zone': [zone1, zone2]
                                }

        Raises:
            Exception:
                if the content could not be selected properly

        """
        selected = []
        all_content = []
        for key, value in vm_content.items():
            all_content += value
            self.__panel_dropdown_obj.select_drop_down_values(0, [key])
            for _vm in value:
                self.__admin_console.search_vm(_vm)
                selected.append(_vm)
            difference = list(set(all_content) - set(selected))
            if difference:
                raise Exception("Exception during selection of content. Some of the content "
                                "could not be selected")

    @PageService()
    def select_content_from_browse_tree(self, vm_name_list, region=None, zone=None, resource_group=None, project=None, compartment=None):
        """
        Select content for subclient from the browse tree

        Args:
            vm_name_list (list)   : name of the instances to be selected from a region or zone

            region  (str)          : Region name

            zone    (str)           :Zone name

            resource_group  (str)   : Azure resource group name

            project (str)           : GCP project name

            compartment (str) : Compartment path of the VM starting from the root compartment to the compartment the VM is in seperated by '/'
                                Ex: If instacnce is in compartment X then the path is root/A/B/X 
        Raises:
            Exception:
                if the content could not be selected properly

        """
        self.__treeview_obj = TreeView(self.__admin_console)
        for _vm in vm_name_list:
            if "|" in _vm:
                # instance id is passed with the vm name
                self.__toggle_obj = Toggle(self.__admin_console)
                self.__toggle_obj.enable(label="Show instance ID")
            if region is not None:
                self.__treeview_obj.expand_node(region, partial_selection=True)
                self.__treeview_obj.select_item_by_label(_vm)
            elif zone is not None:
                region = zone[:-1]
                self.__treeview_obj.expand_node(region, partial_selection=True)
                self.__treeview_obj.expand_node(zone, partial_selection=True)
                self.__treeview_obj.select_item_by_label(_vm)
            elif resource_group is not None:
                self.__treeview_obj.expand_node(resource_group, partial_selection=True)
                self.__treeview_obj.select_item_by_label(_vm)
            elif project is not None:
                self.__treeview_obj.expand_node(project, partial_selection=True)
                self.__treeview_obj.select_item_by_label(_vm)
            elif compartment is not None:
                compartment_path = compartment.split('/')
                compartment_path.append(_vm)
                self.__treeview_obj.expand_path(compartment_path, partial_selection=True)
            else:
                if "/" in _vm:
                    # VM inventory path is passed with "/" as separator
                    _vm_path = _vm.strip("/").split("/")
                    self.__treeview_obj.expand_path(_vm_path)
                else:
                    self.__treeview_obj.select_items([_vm])

    @PageService()
    def action_delete_subclient(self, subclient):
        """
        Deletes a subclient with the given name

        Args:
            subclient    (str):  the name of the subclient to be deleted

        """
        self.__admin_console.select_overview_tab()
        self.__table_obj.access_action_item(subclient, self.__admin_console.props['action.delete'])
        self.__admin_console.click_button(self.__admin_console.props['button.yes'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def delete_server(self):
        """
        Deletes the entire server with the given name
        """
        self.__admin_console.access_menu_from_dropdown(self.__admin_console.props['action.commonAction.retire'])
        self.__admin_console.click_button(self.__admin_console.props['action.commonAction.retire'])

    @PageService()
    def data_backup(self, enabled=True):
        """
        Enables and disables the data backup capability of the server

        Args:
            enabled    (bool):  the enabled state [True / False] for data backup

        """
        self.__admin_console.select_configuration_tab()
        panel_info = PanelInfo(self.__admin_console, self.__admin_console.props['heading.clientActivityControl'])
        if enabled:
            panel_info.enable_toggle(self.__admin_console.props['label.dataBackup'])
        else:
            panel_info.disable_toggle(self.__admin_console.props['label.dataBackup'])

    @PageService()
    def data_restore(self, enabled=True):
        """
        Enables and disables the data restore capability of the server

        Args:
            enabled     (bool): the enabled state [True / False] for data restore
        """
        self.__admin_console.select_configuration_tab()
        panel_info = PanelInfo(self.__admin_console, title=self.__admin_console.props['heading.clientActivityControl'])
        if enabled:
            panel_info.enable_toggle(self.__admin_console.props['Data_Restore'])
        else:
            panel_info.disable_toggle(self.__admin_console.props['Data_Restore'])

    @PageService()
    def jobs(self):
        """
        Opens the jobs page with all the running jobs for the server

        Raises:
            Exception:
                if the jobs page could not be opened

        """
        self.__admin_console.access_menu(self.__admin_console.props['action.commonAction.jobs'])

    @PageService()
    def select_overview_tab(self):
        """
        Selects the overview tab

        Raises:
            NoSuchElementException:
                if the Overview tab is not present
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.tab.overview'])

    @PageService()
    def select_configuration_tab(self):
        """
        Selects the configuration tab

        Raises:
            NoSuchElementException:
                if the configuration tab is not present
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.nav.configuration'])

    @PageService()
    def select_vmgroup_tab(self):
        """
        Selects the vmgroup tab

        Raises:
            NoSuchElementException:
                if the vm group tab is not present
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.nav.vmGroups'])

    @PageService()
    def select_content_tab(self):
        """
        Selects the content tab

        Raises:
            NoSuchElementException:
                if the content tab is not present
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.content'])

    @PageService()
    def select_vm_tab(self):
        """
        Selects the virtual machines tab
        Raises:
            NoSuchElementException:
                if the vm tab is not present
        """
        self.__admin_console.access_tab(self.__admin_console.props['label.nav.vms'])

    @PageService()
    def open_subclient(self, subclient_name, backupset_name="defaultBackupSet"):
        """
        Opens a subclient with the given name

        Args:
            subclient_name  (str):   the name of the subclient to be opened

        Raises:
            Exception:
                if the subclient is not found

        """
        self.select_vmgroup_tab()
        if self.__panel_rdropdown_obj.is_dropdown_exists(drop_down_id="Backup sets"):
            self.__rtable_obj.set_default_filter(filter_id="Backup sets", filter_value=backupset_name)
        self.__rtable_obj.access_link(subclient_name)
        self.__admin_console.wait_for_completion()

    @PageService()
    # Written only for VMWare,AWS,Azure hypervisor,OCI, GCP
    def edit_hypervisor_details(self, vs_hostname=None, vs_username=None, vs_password=None,
                                vs_old_password=None, vendor=None, auth_type=None, credential=None,
                                admin_hypervisor=None, subscription_id=None, proxy_list=None,
                                frel= None,tag_name=None, service_account_id=None,
                                description=None, json_path=None):
        """
        This definition edits the server credentials only for VMWare, AWS hypervisor,OCI

        Args:
            vs_hostname          (str):  the hostname of the server

            vs_username          (str):  the username / access key of the server

            vs_password          (str):  the password / secret key of the server

            vs_old_password      (str):  the old password of the server

            vendor                (str): Vendor type

            auth_type             (str): authentication type

            credential             (str): credential

            admin_hypervisor        (str): admin hypervisor for tenant account

            subscription_id         (str): azure subscription id

            proxy_list               (str): proxy list

            frel                     (str): file_recovery_enabler

            tag_name                 (str): tag_name
            
            description             (str): Description of the credential

            service_account_id      (str):  Name of the service account to be used

            json_path               (str): Absolute path of the service account json file

        Raises:
            Exception:
                if the hypervisor details could not be edited

        """
        try:
            self.__admin_console.select_overview_tab()
            if vendor == HypervisorDisplayName.VIRTUAL_CENTER.value:
                if vs_username or vs_password or vs_hostname or credential:
                    account_panel_obj = RPanelInfo(self.__admin_console,
                                                   title=self.__admin_console.props['header.account'])
                    account_panel_obj.edit_tile()
                    account_details_modal = RModalDialog(self.__admin_console, title='Edit hypervisor details')
                    if vs_hostname:
                        if self.__admin_console.check_if_entity_exists("id", "vcenterHostName"):
                            self.__admin_console.fill_form_by_id("vcenterHostName", vs_hostname)
                    if credential:
                        account_details_modal.checkbox.check(id='toggleFetchCredentials')
                        account_details_modal.select_dropdown_values('credentials', [credential])
                    if vs_username and vs_password:
                        account_details_modal.checkbox.uncheck(id='toggleFetchCredentials')
                    if vs_username:
                        if self.__admin_console.check_if_entity_exists("id", "userName"):
                            self.__admin_console.fill_form_by_id("userName", vs_username)
                    if vs_password:
                        if self.__admin_console.check_if_entity_exists("id", "password"):
                            self.__admin_console.fill_form_by_id("password", vs_password)
                    account_details_modal.click_submit()
                    self.__admin_console.check_error_message()
            else:
                panel_info = RPanelInfo(self.__admin_console, self.__admin_console.props['heading.clientGeneral'])
                panel_info.edit_tile()
                if vs_hostname:
                    self.__admin_console.fill_form_by_name("serverName", vs_hostname)

                checkbox_obj = Checkbox(self.__admin_console)
                checkbox_label = "Use credential manager"
                if checkbox_obj.is_exists(label=checkbox_label) and \
                        checkbox_obj.is_checked(checkbox_label):
                    self.__edit_credential(credential=credential, vs_username=vs_username,
                                           vs_password=vs_password, description=description,
                                           service_account_id=service_account_id, json_path=json_path)
                else:
                    if vs_username:
                        if self.__admin_console.check_if_entity_exists("id", "uname"):
                            self.__admin_console.fill_form_by_id("uname", vs_username)
                        elif self.__admin_console.check_if_entity_exists("name", "vsAccessKey"):
                            self.__admin_console.fill_form_by_id("vsAccessKey", vs_username)

                    if vs_old_password:
                        if self.__admin_console.check_if_entity_exists("id", "vsCurrPassword"):
                            self.__admin_console.fill_form_by_id("vsCurrPassword", vs_old_password)

                    if vs_password:
                        self.__admin_console.fill_form_by_id("pass", vs_password)
                        if self.__admin_console.check_if_entity_exists("id", "confirmServerPassword"):
                            self.__admin_console.fill_form_by_id("confirmServerPassword", vs_password)

                if vendor == HypervisorDisplayName.AMAZON_AWS.value:
                    if admin_hypervisor is not None:
                        self.set_admin_hypervisor(admin_hypervisor)
                    if auth_type is not None:
                        self.set_aws_auth(auth_type, credential)

                if vendor == HypervisorDisplayName.MICROSOFT_AZURE.value:
                    self.edit_azure_auth(auth_type, credential, subscription_id)

                if vendor == HypervisorDisplayName.Vcloud.value:
                    self.set_vcloud_auth(saved_credentials=credential)

                if vendor == HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value:
                    if credential:
                        general_details_modal = RModalDialog(self.__admin_console, title='Edit hypervisor details')
                        general_details_modal.select_dropdown_values('credentials', [credential])
                        self.__admin_console.cancel_form()
                    if proxy_list:
                        self.proxy_obj = VsaSubclientDetails(self.__admin_console)
                        self.proxy_obj.update_access_node(proxy_list)
                    if frel:
                        self.recovery_obj = VsaSubclientDetails(self.__admin_console)
                        self.recovery_obj.update_frel(frel)
                    if tag_name:
                        self.tab_obj = VsaSubclientDetails(self.__admin_console)
                        self.tab_obj.update_tag_name(tag_name)

                self.__admin_console.submit_form()
                self.__admin_console.check_error_message()
        except Exception as exp:
            raise Exception(f"Failed to edit hypervisor : {exp}")

    @PageService()
    def action_subclient_restore(self, subclient_name):
        """
        Opens the restore page of the subclient from the server details page

        Args:
            subclient_name  (str):   the name of the subclient to be restored

        """
        self.__admin_console.select_overview_tab()
        self.__table_obj.access_action_item(subclient_name, self.__admin_console.props['action.commonAction.restore'])

    @PageService()
    def action_subclient_jobs(self, subclient_name):
        """
        Lists all the jobs of the specific subclient

        Args:
            subclient_name  (str):   the subclient whose jobs need to be opened

        """
        self.__admin_console.select_overview_tab()
        self.__table_obj.access_action_item(subclient_name, self.__admin_console.props['action.commonAction.jobs'])

    @PageService()
    def server_settings(self, fbr=None, vcloud_hostname=None,
                        vcloud_username=None, vcloud_password=None):
        """
        Sets the FBR MA and other settings like vCloud

        Args:
            fbr                  (str):  the name of the FBR MA to be set

            vcloud_hostname      (str):  the host name of the vcloud director

            vcloud_username      (str):  the vcloud username

            vcloud_password      (str):  the vcloud password

        """
        self.__admin_console.select_configuration_tab()
        panel_info = PanelInfo(self.__admin_console, title=self.__admin_console.props['label.nav.settings'])
        if fbr:
            panel_info.edit_tile_entity(self.__admin_console.props['label.fbrUnixMA'])
            self.__panel_dropdown_obj.select_drop_down_values(0, [fbr])
            self.__admin_console.submit_form()

        if vcloud_hostname:
            panel_info.edit_tile_entity(self.__admin_console.props['label.vCloudHostName'])
            self.__admin_console.fill_form_by_id("vcloudHostName", vcloud_hostname)
            self.__admin_console.fill_form_by_id("vcloudUserName", vcloud_username)
            self.__admin_console.fill_form_by_id("vcloudPassword", vcloud_password)
            self.__admin_console.fill_form_by_id("confirmVcloudPassword", vcloud_password)
            self.__admin_console.submit_form()

    @PageService()
    def open_vm_provisioning_settings(self):
        """
        Opens vm provisioning settings
        """
        panel = RPanelInfo(self.__admin_console, self.__admin_console.props['label.accessNodes'])
        panel.open_hyperlink_on_tile(
                                  self.__admin_console.props["label.vmProvisioningSettings"])
        self.__admin_console.wait_for_completion()

    @PageService()
    def reset_vm_provisioning_settings(self):
        """
        Resets VM Provisioning setting at Hypervisor
        """
        panel = RPanelInfo(self.__admin_console, self.__admin_console.props['label.accessNodes'])
        panel.open_hyperlink_on_tile(
            self.__admin_console.props["label.reset"])
        confirm_reset_dialog = RModalDialog(self.__admin_console,
                                            title=self.__admin_console.props['label.confirmReset'])
        confirm_reset_dialog.click_yes_button()

    def enable_auto_scale(self):
        """
        Enables auto scale toggle
        """
        panel = RPanelInfo(self.__admin_console, self.__admin_console.props['label.accessNodes'])
        panel.enable_toggle(self.__admin_console.props['label.autoScaleOut'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def disable_auto_scale(self):
        """
        Disables auto scale toggle
        """
        panel = RPanelInfo(self.__admin_console, self.__admin_console.props['label.accessNodes'])
        panel.disable_toggle(self.__admin_console.props['label.autoScaleOut'])


    @PageService()
    def configure_vm_provisioning(self, options, reset=True, is_autoscale=False):
        """
        Configures vm provisioning for azure/aws

         Args:
             options(dict): configurations
                example:{"server group": "AZ",
                        "resource group": "RG",
                        "region specific info": [{'region name': 'East US 2',
                        'network name': 'NSG', 'subnet name': 'default'}],
                        'public Ip' : True,
                        "advanced settings" : "{}"}

             reset(bool) : Resets the configurations before setting it to provided values
        """
        self.__admin_console.select_configuration_tab()
        panel = RPanelInfo(self.__admin_console, title='Access nodes')
        proxylist = panel.get_list()

        if not proxylist:
            labels = panel.get_label()
            if any("This hypervisor is configured to use resources from service account." in label for label in labels):
                self.__admin_console.select_overview_tab()

                tenant_account_general_panel = RPanelInfo(self.__admin_console, 'General')
                general_panel_details = tenant_account_general_panel.get_details()
                service_account_hypervisor_value = general_panel_details.get('Service account hypervisor')
                tenant_account_general_panel.open_hyperlink_on_tile(service_account_hypervisor_value)

                self.__admin_console.select_configuration_tab()
                self.__admin_console.wait_for_completion()
                self.disable_auto_scale()

        if reset:
            if self.__admin_console.check_if_entity_exists('xpath','//div[contains(@class,"tile-row-label")]//a['
                                                                   'contains(text(), "Reset")]'):
                self.reset_vm_provisioning_settings()

        if is_autoscale:
            self.enable_auto_scale()
        else:
            self.open_vm_provisioning_settings()
            self.__admin_console.wait_for_completion()

        provisioning_setting_dialog = RModalDialog(self.__admin_console, "VM provisioning settings")

        if options.get("AssociateExistingProvisioningPolicy", None):
            provisioning_setting_dialog.enable_toggle(toggle_element_id="vmProvisioning")

            provisioning_setting_dialog.select_dropdown_values(drop_down_id="hypervisorsDropdownInput",
                                                               values=[options["AssociateExistingProvisioningPolicy"]])

        else:
            provisioning_setting_dialog.disable_toggle(toggle_element_id="vmProvisioning")

        provisioning_setting_dialog.click_submit()

        from Web.AdminConsole.VSAPages.configure_vm_provisioning_settings import ConfigureVMProvisioningSetting

        vm_provisioning_wizard = ConfigureVMProvisioningSetting(self.__admin_console, vm_provisioning_options=options)
        vm_provisioning_wizard.configure_settings()

    @PageService()
    def get_tenant_accounts(self):
        """
        Gets organizational accounts linked to an admin vCloud hypervisor

        Returns:
            tenant_accounts     (list)  -   list of children tenant accounts for the hypervisor
        """
        self.__admin_console.log.info("Fetching hypervisor details")
        self.select_configuration_tab()
        org_accounts = RPanelInfo(self.__admin_console, title=self.__admin_console.props['label.tenants'])
        tenant_accounts = org_accounts.get_list()
        return tenant_accounts

    @PageService()
    def get_associated_vcenters(self):
        """
        Gets associated vCenters for the vCloud hypervisor

        Returns:
            vcenters (list) - list of associated vCenters
        """
        self.__admin_console.log.info("Fetching associated vCenters")
        self.select_configuration_tab()
        return self._fetch_associated_vcenters()

    @WebAction()
    def _fetch_associated_vcenters(self):
        """
        Fetches associated vCenters by performing web actions on the UI.

        Returns:
            vcenter_names (list) - list of vCenter names fetched from the UI
        """
        xpath = "//div[@id='vcenterList']//ul/li//a"
        list_elements = self.__driver.find_elements(By.XPATH, xpath)
        vcenter_names = []
        for element in list_elements:
            if element.is_displayed():
                vcenter_names.append(element.text)
        return vcenter_names

    @PageService()
    def get_credential_info(self):
        """
        Gets the credential info from general tab

        Returns credential value
        """
        credential_detail = {}
        credential_detail['credential'] = self.__admin_console.get_element_value_by_id("credentials")
        credential_detail['regions'] =  self.__admin_console.get_element_value_by_id("regionName")
        return credential_detail

    def validate_ssl_check(self, hypervisor=None, ssl_check=False):
        """
        Validate the SSL certificate verification status for a hypervisor.

        hypervisor_name (str) : Name of the hypervisor to check
        ssl_check (bool) : Expected SSL certificate verification status (True for enabled, False for disabled)

        Returns True if the SSL check status matches the expected value, otherwise logs an error.
        """
        self.__navigator.navigate_to_virtualization()
        self.__navigator.navigate_to_hypervisors()
        self.__rtable_obj.access_link(hypervisor)
        self.hyp_ssl_check[hypervisor] = self.get_verify_ssl_cert_status()
        if self.hyp_ssl_check[hypervisor] == ssl_check:
            return True
        else:
            raise Exception("SSL check mismatch")

    @PageService()
    def fetch_hypervisor_details(self, vendor=None):
        """
        Fetches the hypervisor detail

        Args:
            vendor  (str)   :   Name of the vendor

        Returns dict of Hypervisor details
        """
        self.__admin_console.log.info("Fetching hypervisor name and auth details")
        self.select_overview_tab()
        general_panel_obj = RPanelInfo(self.__admin_console, title=self.__admin_console.props['heading.clientGeneral'])
        general_info = general_panel_obj.get_details()
        admin_hypervisor = access_nodes = None
        if 'Service account hypervisor' in general_info.keys():
            admin_hypervisor = general_info['Service account hypervisor']
        else:
            access_nodes = self.proxy_info()
        hypervisor_name = self.hypervisor_name()
        self.select_vmgroup_tab()
        vm_group = self.__rtable_obj.get_column_data(column_name=self.__admin_console.props['label.name'])[0]
        plan = self.__rtable_obj.get_column_data(column_name="Plan")[0]
        hypervisor_detail = {"vendor": general_info['Vendor'],
                             "server_name": hypervisor_name,
                             "proxy_list": access_nodes,
                             "vm_group_name": vm_group,
                             "plan": plan}
        if vendor == HypervisorDisplayName.AMAZON_AWS.value:
            credential = self.__get_credential_info(general_info)
            hypervisor_detail.update({"regions": general_info['Regions'],
                                      "auth_type": general_info['Authentication Type'],
                                      "credential": credential,
                                      "admin_hypervisor": admin_hypervisor
                                      })
        elif vendor == HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value:
            self.select_overview_tab()
            general_panel_obj.edit_tile()
            credential_detail = self.get_credential_info()
            self.__admin_console.cancel_form()
            self.obj = VsaSubclientDetails(self.__admin_console)
            FREL_detail = self.obj.get_frel_info()
            tag_name_detail = self.obj.get_tag_name_info()
            hypervisor_detail.update ({ "credential": credential_detail['credential'],
                                        "regions": credential_detail['regions'],
                                        "frel":FREL_detail['frel'],
                                        "tag_name":tag_name_detail['tag_name']})
        elif vendor == HypervisorDisplayName.MICROSOFT_AZURE.value:
            self.select_overview_tab()
            general_panel_obj.edit_tile()
            cred_detail = self.__get_azure_credential_info()
            self.__admin_console.cancel_form()
            hypervisor_detail.update({"auth_type": cred_detail['auth_type'],
                                      "subscription_id": cred_detail['subscription_id'],
                                      "credential": cred_detail['credential']
                                      })
        elif hypervisor_type.MS_VIRTUAL_SERVER.value in vendor:
            self.select_overview_tab()
            general_panel_obj.edit_tile()
            cred_name = self.__get_credential_name()
            hypervisor_detail.update({"vendor": hypervisor_type.MS_VIRTUAL_SERVER.value,
                                      "credential": cred_name,
                                      "username": general_info['User name'],
                                      "hostname": general_info['Hostname']
                                      })
        elif vendor == hypervisor_type.Nutanix.value:
            hypervisor_detail.update({"vs_username": general_info['User name'],
                                      "host_name": general_info['Hostname']})
        elif vendor == HypervisorDisplayName.ORACLE_VM.value:
            hypervisor_detail.update({"vs_username": general_info['User name']})
        elif vendor == HypervisorDisplayName.VIRTUAL_CENTER.value:
            self.select_overview_tab()
            account_panel_obj = RPanelInfo(self.__admin_console, title=self.__admin_console.props['header.account'])
            account_panel_obj.edit_tile()
            account_details_modal = RModalDialog(self.__admin_console, title='Edit hypervisor details')
            credential = None
            username = None
            if account_details_modal.checkbox.is_checked(id='toggleFetchCredentials'):
                self.__panel_rdropdown_obj.wait_for_dropdown_load(drop_down_id="credentials")
                credential = self.__get_account_credential()
            else:
                try:
                    self.__panel_rdropdown_obj.wait_for_dropdown_load(drop_down_id="credentials")
                except (StaleElementReferenceException, NoSuchElementException):
                    pass
                username = self.__get_account_username()
            account_details_modal.click_cancel()
            hypervisor_detail.update({"username": username, "credential": credential})
        elif vendor == HypervisorDisplayName.Vcloud.value:
            if 'Organization' in general_info.keys():
                hypervisor_detail['vcloud_organization'] = general_info['Organization']
                hypervisor_detail['company'] = general_info['Company']
            else:
                hypervisor_detail['tenant_accounts'] = self.get_tenant_accounts()

                self.select_configuration_tab()
                proxy_panel_obj = RPanelInfo(self.__admin_console, title=self.__admin_console.props['heading.proxyNodes'])
                hypervisor_detail['proxy_list'] = proxy_panel_obj.get_list()
                hypervisor_detail['host_name'] = general_info['Hostname']
                hypervisor_detail['associated_vcenters'] = self.get_associated_vcenters()
                hypervisor_detail['ssl_check'] = self.hyp_ssl_check

                self.select_overview_tab()
                general_panel_obj.edit_tile()
                self.__admin_console.wait_for_completion()
                vcloud_creds = self.__admin_console.driver.find_element(By.ID, "credentials").text
                self.__admin_console.cancel_form()
                hypervisor_detail['credential'] = vcloud_creds


        elif vendor == HypervisorDisplayName.Google_Cloud.value:
            self.select_overview_tab()
            general_panel_obj.edit_tile()
            account_details_modal = RModalDialog(self.__admin_console, title='Edit hypervisor details')
            cred_obj = self.__get_gcp_credential_details()
            hypervisor_detail.update(cred_obj)
            account_details_modal.click_cancel()
        return hypervisor_detail


    def __get_gcp_credential_details(self):
        cred_name = None
        checkbox_obj = Checkbox(self.__admin_console)
        if checkbox_obj.is_checked(self.__admin_console.props['label.globalActions.savedCredentials']):
            cred_name = self.__panel_rdropdown_obj.get_selected_values('credentials', expand=False)
            self.__admin_console.click_by_xpath("//div[contains(@class, 'Dropdown-field')]"
                                                "//button[@aria-label='Edit']")
            credential_dialog = RModalDialog(self.__admin_console, title='Edit credential')

            service_account_id = credential_dialog.get_input_details(input_id="userAccount")
            credential_dialog.click_close()
            return {
                "credential": cred_name[0],
                "service_account_id": service_account_id
            }

        return {}
    def __get_credential_info(self, general_info):
        """
        Gets the credential info from general tab dict

        general_info    (dict)--dict of values in general tile of the AWS hypervisor

        Returns credential value
        """
        if "Role ARN" in general_info.keys():
            return general_info['Role ARN']
        if "Access key" in general_info.keys():
            return general_info['Access key']
        return None

    def __get_azure_credential_info(self):
        """
        Fetches the Azure credential detail

        returns dict of credential details
        """
        cred_detail = {'subscription_id': self.__driver.find_element(By.ID, "subscriptionId").get_attribute("value"),
                       'auth_type': "MSI", 'credential': None}
        if self.__admin_console.check_if_entity_exists("id", "credentialsInput"):
            cred_detail['auth_type'] = "Non-MSI"
            if self.__admin_console.check_if_entity_exists("path", "//div[@id='credentials']/li/p"):
                cred_detail['credential'] = self.__driver.find_element(By.XPATH, "//div[@id='credentials']/li/p").text
        return cred_detail

    def __get_credential_name(self):
        """
        returns saved credential name

        """
        cred_name = None
        checkbox_obj = Checkbox(self.__admin_console)
        if checkbox_obj.is_checked(self.__admin_console.props['label.useCredentialManager']):
            cred_name = self.__panel_rdropdown_obj.get_selected_values('credentials', expand=False)
        self.__admin_console.cancel_form()
        return cred_name[0]

    def __edit_credential(self, credential=None, vs_username=None, vs_password=None, description=None,
                          service_account_id=None, json_path=None):

        """
        Edit the credential details in credential object
        args:
            credential          (str) - New credential Name
            vs_username         (str) - New username
            vs_password         (str) - New Password
            description         (str) - description (if any)

        raise:
            Exception:
                If edit credential fails
        """
        try:
            self.__admin_console.click_by_xpath("//div[contains(@class, 'Dropdown-field')]"
                                                "//button[@aria-label='Edit']")

            self.__admin_console.wait_for_completion()
            if credential:
                self.__modal_dialog_obj.fill_input_by_xpath(element_id="name", text=credential)

            if vs_username:
                self.__modal_dialog_obj.fill_input_by_xpath(element_id="userAccount", text=vs_username)

            if vs_password:
                self.__modal_dialog_obj.fill_input_by_xpath(element_id="password", text=vs_password)

            if description:
                self.__modal_dialog_obj.fill_input_by_xpath(element_id="description", text=description)

            if service_account_id:
                self.__modal_dialog_obj.fill_input_by_xpath(element_id="userAccount", text=service_account_id)

            if json_path:
                self.__modal_dialog_obj.upload_file(label="JSON file path", absolute_path=json_path)

            self.__admin_console.click_by_xpath("//*[contains(@class, 'modal-footer')]"
                                                "//button[contains(@aria-label, 'Save')]")
            self.__admin_console.check_error_message()
            self.__admin_console.log.info(f"Successfully edited the credential")

        except Exception as exp:
            raise Exception(f"Failed to edit credential : {exp}")

    @WebAction()
    def hypervisor_name(self):
        """
        Gets the current hypervisor name

        returns (str)   name of the hypervisor
        """
        self.__page_container_obj = PageContainer(self.__admin_console)
        return self.__page_container_obj.fetch_title()

    @PageService(react_frame=True)
    def open_create_access_node_dialog(self):
        """
        Opens Create access node dialog from Hypervisor Page

        """
        self.__admin_console.select_configuration_tab()
        access_node_panel = RPanelInfo(self.__admin_console, 'Access nodes')
        access_node_panel.click_action_item("Create access node")

    @WebAction()
    def set_aws_auth(self, auth_type, aws_credential):
        """
        sets the authentication type for the AWS client

        auth_type:  (str)   :auth type, IAM or STS or Access and secret

        aws_credential  (str): name of the saved credential

        returns None
        """
        if auth_type == "IAM role":
            self.__admin_console.click_by_id(id="useIamRole")
            return
        elif auth_type == "STS assume role with IAM policy":
            self.__admin_console.click_by_id(id="RoleARN")
        else:
            self.__admin_console.click_by_id(id="IamGroup")
        self.__wizard_obj.select_drop_down_values(id='credentials', values=[aws_credential])

    @WebAction()
    def set_azure_auth(self, auth_type, credential):
        """
        Sets the authentication details for the Azure client.

        Args:
            auth_type           (str):  type of azure client
            credential          (str):  credential of azure client

        Returns none
        """
        if auth_type == "MSI":
            self.__admin_console.checkbox_select(checkbox_name='useManagedIdentity')
            return
        self.__wizard_obj.select_drop_down_values(id='credentials', values=[credential])

    @WebAction
    def set_vcloud_auth(self, saved_credentials):
        """
        Set/edit vCloud hypervisor auth

        Args:
            saved_credentials        (str)   =       Name of the saved credential

        Returns:
            None
        """
        if saved_credentials:
            if self.__wizard_obj.checkbox.is_exists("Saved credentials", "toggleFetchCredentials"):
                self.__wizard_obj.checkbox.check("Saved credentials", "toggleFetchCredentials")

            self.__wizard_obj.select_drop_down_values("credentials", [saved_credentials])
            self.__admin_console.submit_form()

    @WebAction()
    def edit_azure_auth(self, auth_type, credential=None, subscription_id=None):
        """
        Edit the authentication details for the Azure client.

        Args:
            auth_type           (str):  type of azure client
            credential          (str):  credential of azure client
            subscription_id     (str): azure subscription id

        Returns None
        """
        if subscription_id:
            self.__admin_console.fill_form_by_id("subscriptionId", subscription_id)
        if auth_type == "MSI":
            self.__admin_console.checkbox_select(checkbox_name='useManagedIdentity')
            return
        if credential:
            self.set_azure_auth(auth_type, credential)

    @WebAction()
    def set_admin_hypervisor(self, admin_hypervisor):
        """
        Sets the admin hypervisor

        admin_hypervisor (str)  -admin hypervisor client name to set

        Returns None
        """
        self.__toggle_obj = Toggle(self.__admin_console)
        self.__toggle_obj.enable(label="Use service account resources")
        self.__wizard_obj.select_drop_down_values(id='useServiceAccount', values=[admin_hypervisor])

    @PageService()
    def set_workload_region(self, region):
        """
        method to set workload region for a hypervisor

        Args:
            region(str) = name of the region to assign
        """
        self.__panel_obj.edit_tile_entity('Workload region')
        self.__panel_rdropdown_obj.select_drop_down_values(drop_down_id="regionDropdown_", values=[region])
        self.__panel_obj.click_button("Save")

    @PageService()
    def get_region(self):
        """ Method used to get the assigned region for the cloud hypervisor

        returns:
            workload region assigned to the entity
        """
        return RPanelInfo(self.__admin_console, "General").get_details()['Workload region']

    @WebAction()
    def __get_account_credential(self):
        """
        Gets the Hypervisor Account Credential

        Returns:
            (str) : Credential
        """
        return self.__driver.find_element(By.XPATH, "//div[@id='credentials']/li/p").text

    @WebAction()
    def __get_account_username(self):
        """
        Gets the Hypervisor Account Username

        Returns:
            (str) : Username
        """
        return self.__driver.find_element(By.XPATH, "//input[@id='userName']").get_attribute('value')

    @PageService()
    def action_list_snapshots(self, entity):
        """
        list the snaps of particular vm group or VM at Hypervisor level
        Args:
            entity  (str):  the name of the VMgroup or VM for list of snapshots
            ex: entity : "Virtual machine" (VM as entity) or
                entity : "VMgroup" (VMgroup as entity)
        """
        self.__rtable_obj.access_action_item(entity, "List snapshots")

    @PageService()
    def manage_filters(self):
        """
        Open Manage Filters Dialog from Hypervisor Details Page

        Raises:
            Exception:
                if there is no link to Manage the Filters

        """
        self.__page_container_obj = PageContainer(self.__admin_console)
        self.__page_container_obj.access_page_action_from_dropdown("Manage filters")
        self.__admin_console.wait_for_completion()