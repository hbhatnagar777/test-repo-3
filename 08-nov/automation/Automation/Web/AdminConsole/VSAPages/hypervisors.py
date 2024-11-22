from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done of the Hypervisors page.


Classes:

    Hypervisors() ---> _Navigator() ---> login_page --->
    AdminConsoleBase() ---> object()


Hypervisors  --  This class contains all the methods for action in Hypervisors page and is inherited
                  by other classes to perform VSA realted actions

Functions:

    select_hypervisor()          --  Opens the server with the given name

    add_hypervisor()             --  Adds a new server with the specified vendors and proxies

    action_jobs()                --  Opens the job details page for the chosen server

    action_delete()              --  delete a server with the specified name

    action_send_logs()           --   Send logs of a server with the specified name

    hypervisor_restore()        --  Restores a subclient from the hypervisor

    list_company_hypervisor()   --  Lists the hypervisor from the given company

    is_hypervisor_exists()      --  Method to check if hypervisor exists or not

    retire_hypervisor()         -- Retires the given hypervisor
    
    get_all_hypervisors()       -- Returns all the list of hypervisors present

"""
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails

from Web.Common.page_object import (
    WebAction,
    PageService
)
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type, HypervisorDisplayName


class Hypervisors:
    """
     This class contains all the methods for action in Hypervisors page
    """

    def __init__(self, admin_console):
        """
        Method to initiate Hypervisors class

        Args:
            admin_console   (Object) :   Admin Console Base Class object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__table_obj = Rtable(admin_console)
        self.__panel_dropdown_obj = RDropDown(admin_console)
        self.__panel_info_obj = RPanelInfo(admin_console)
        self.__vm_groups_obj = VMGroups(admin_console)
        self.__driver = admin_console.driver
        self.__navigator = admin_console.navigator
        self.__wizard_obj = Wizard(admin_console)
        self.__hypervisor_details_obj = HypervisorDetails(admin_console)
        self.__modal_dialog_obj = RModalDialog(admin_console)
        self.ssl_check = {}

    @WebAction()
    def __select_add_hypervisor(self):
        """
        Selects Add Hypervisor
        """
        self.__admin_console.click_button_using_text(self.__admin_console.props['label.addHypervisor'])

    @PageService()
    def select_add_hypervisor(self):
        """
        Selects Add Hypervisor
        """
        self.__select_add_hypervisor()

    @WebAction()
    def __set_hostname(self, hostname):
        """
        Sets Hostname
        """
        self.__admin_console.fill_form_by_id("hostName", hostname)

    @WebAction()
    def __set_oracle_manager(self, hostname):
        """
        Sets Oracle vm manager
        """
        self.__admin_console.fill_form_by_id("oracleVMManager", hostname)

    @WebAction()
    def __set_vcenter_hostname(self, hostname):
        """
        Sets vCenter Hostname
        """
        self.__admin_console.fill_form_by_id("vcenterHostName", hostname)

    @WebAction()
    def __set_servername(self, server_name):
        """
        Sets Servername
        """
        self.__admin_console.fill_form_by_id("name", server_name)

    @WebAction()
    def __set_credential(self, credential):
        """
        Sets the Credential
        """
        self.__wizard_obj.select_drop_down_values(id='credentials', values=[credential])

    @WebAction()
    def __set_access_nodes(self, proxy_list):
        """
        Sets the Access Nodes
        """
        self.__wizard_obj.select_drop_down_values(id='accessNodes', values=proxy_list)

    @WebAction()
    def __set_username(self, username):
        """
        Sets username
        """
        if self.__admin_console.check_if_entity_exists("id", "vsUserName"):
            self.__admin_console.fill_form_by_id("vsUserName ", username)
        else:
            self.__admin_console.fill_form_by_id("userName", username)

    @WebAction()
    def __populate_hostname(self, host_name):
        """
        Set hostname
        """
        self.__wizard_obj.fill_text_in_field(id="serverName", text=host_name)

    @WebAction()
    def __populate_clientname(self, server_name):
        """
        Set Hypervisor Client Name
        """
        self.__wizard_obj.fill_text_in_field(id="name", text=server_name)

    @WebAction()
    def __set_password(self, pwd):
        """
        Sets password
        """
        if self.__admin_console.check_if_entity_exists("id", "vsPassword"):
            self.__admin_console.fill_form_by_id("vsPassword", pwd)
        else:
            self.__admin_console.fill_form_by_id("password", pwd)

    @WebAction()
    def __set_domain(self, domain):
        """
        Sets domain
        """
        self.__admin_console.fill_form_by_id("domainName", domain)

    @WebAction()
    def __set_access_key(self, access_key):
        """
        Sets access key
        """
        self.__admin_console.fill_form_by_id("accessKey", access_key)

    @WebAction()
    def __set_secret_key(self, secret_key):
        """
        Sets secret key
        """
        self.__admin_console.fill_form_by_id("secretKey", secret_key)

    @WebAction()
    def __set_client_name(self, client_name):
        """
        Sets client name
        """
        self.__admin_console.fill_form_by_id("clientName", client_name)

    @WebAction()
    def __set_service_account_id(self, service_account_id):
        """
        Sets service account id
        """
        self.__admin_console.fill_form_by_id("serviceAccountID", service_account_id)

    @WebAction()
    def __set_p12_keyname(self, p12_keyname):
        """
        Sets p12 keyname
        """
        self.__admin_console.fill_form_by_id("p12KeyFileName", p12_keyname)

    @WebAction()
    def __set_private_key_password(self, pvt_key_pass):
        """
        Sets private key password
        """
        self.__admin_console.fill_form_by_id("privateKeysPassword", pvt_key_pass)

    @WebAction()
    def __set_subscription_id(self, subs_id):
        """
        Sets subscription id
        """
        self.__admin_console.fill_form_by_id("subscriptionId", subs_id)

    @WebAction()
    def __set_tenant_id(self, tenant_id):
        """
        Sets tenant id
        """
        self.__admin_console.fill_form_by_id("tenantId", tenant_id)

    @WebAction()
    def __set_app_id(self, app_id):
        """
        Sets app id
        """
        self.__admin_console.fill_form_by_id("applicationId", app_id)

    @WebAction()
    def __set_application_pwd(self, application_password):
        """
        Sets application pwd
        """
        self.__admin_console.fill_form_by_id("applicationPassword", application_password)

    @WebAction()
    def __skip_for_now(self):
        """
        Selects skip for now
        """
        if self.__driver.find_element(By.LINK_TEXT, self.__admin_console.props['action.skip']):
            self.__driver.find_element(By.LINK_TEXT, self.__admin_console.props['action.skip']).click()

    @WebAction()
    def __select_subclient(self, subclient):
        """
        Selects subclient
        """
        elems = self.__driver.find_elements(By.XPATH, "//ul[@class='ivh-treeview ng-scope']/li")
        for elem in elems:
            if elem.find_element(By.XPATH, ".//span/label").text == subclient:
                elem.find_element(By.XPATH, ".//span/label").click()

    @WebAction()
    def __select_vendor_type(self, vendor_name):
        """
        Selects vendor name

        vendor_name(str)    name of the vendor

        returns None
        """
        elems = self.__driver.find_elements(By.XPATH, "//span[contains(@class,'MuiCardHeader-title')]"
                                                      "//span[contains(@class,'MuiFormControlLabel-label')]")
        for elem in elems:
            if vendor_name in elem.text:
                elem.click()
                break

    def get_all_hypervisors(self):
        """
        Method to return the list of all hypervisors displayed in the UI

        Returns:
            List(str) : a list of hypervisor names
        """
        return self.__table_obj.get_column_data(self.__admin_console.props['Name'])

    @PageService()
    def select_hypervisor(self, server_name):
        """
        Opens the server with the given name

        Args:
            server_name  (str):  the name of the server to be opened

        Raises:
            Exception:
                if there is no server with the given name

        """
        self.__navigator.navigate_to_hypervisors()
        self.__table_obj.access_link(server_name)

    @PageService()
    def add_hypervisor(
            self,
            vendor,
            server_name,
            proxy_list=None,
            host_name=None,
            vs_password=None,
            vs_username=None,
            access_key=None,
            secret_key=None,
            auth_type="IAM",
            credential=None,
            regions=None,
            admin_hypervisor=None,
            vm_group_name=None,
            vm_content=None,
            plan=None,
            domain=None,
            project_id=None,
            service_account_id=None,
            p12_key=None,
            private_key_password=None,
            subscription_id=None,
            thumbprint=None,
            tenant_id=None,
            application_id=None,
            application_password=None,
            associated_vcenters=None,
            vcloud_organization=None,
            company=None,
            **kwargs):
        """
        Adds a new server with the specified vendors and proxies.

        Args:
            project_id           (str):  the project ID of Google cloud

            service_account_id   (str):  the service account ID of Google cloud

            p12_key              (str):  the P12 Key of Google Cloud

            private_key_password (str):  the private key password of Google Cloud

            subscription_id      (str):  the subscription ID of Azure account

            thumbprint           (str):  the thumbprint of the Azure account

            tenant_id            (str):  the tenant ID of the Azure account

            application_id       (str):  the application ID of the Azure account

            application_password (str):  the application password of the Azure account

            domain               (str):  the domain name of the openstack server

            access_key           (str):  the access key required for Amazon client

            secret_key           (str):  the secret key required for Amazon client

            regions             (str): list of comma separated regions for Amazon client

            auth_type            (str): authentication type for AWS client

            credential           (str):Name of the saved AWS credential

            admin_hypervisor    (str):admin AWS hypervisor client to be used

            vm_group_name       (str):  Name of the vm group

            vm_content          (list/dict): list of vms as content

            plan                (string): name of the plan

            vendor               (str):  the vendor type of server to be added

            server_name          (str):  the name of the server to be added

            host_name            (str):  the hostname of the server to be added

            vs_username          (str):  the username of the server to be added

            proxy_list           (list):        the list of proxies to be associated with server

            vs_password          (str):  the password of the server to be added

            associated_vcenters  (dict):    List of credentials for associated vCenters in vCloud

            vcloud_organization  (str):     Organization for tenant hypervisors in vCloud

            company              (str):     Company to which hypervisor is made part of

        Raises:
            Exception:
                if the hypervisor could not be created

        """
        self.__admin_console.log.info("Adding a %s server %s as %s", vendor, host_name, server_name)
        self.__navigator.navigate_to_hypervisors()
        self.__select_add_hypervisor()
        self.__select_vendor_type(vendor)
        self.__wizard_obj.click_next()
        if vendor in [HypervisorDisplayName.OPENSTACK.value, hypervisor_type.Oracle_Cloud_Classic.value,
                      HypervisorDisplayName.ORACLE_VM.value]:
            if vendor == HypervisorDisplayName.ORACLE_VM.value:
                self.__set_oracle_manager(host_name)
            else:
                self.__set_hostname(host_name)
            self.__set_servername(server_name)
            self.__set_username(vs_username)
            self.__set_password(vs_password)
            if vendor == HypervisorDisplayName.OPENSTACK.value and domain:
                self.__set_domain(domain)
            self.__set_access_nodes(proxy_list)
        elif vendor == HypervisorDisplayName.VIRTUAL_CENTER.value:
            self.__set_vcenter_hostname(host_name)
            self.__set_servername(server_name)
            self.__set_credential(credential, vs_username, vs_password)
            self.__set_access_nodes(proxy_list)
        elif vendor == hypervisor_type.MS_VIRTUAL_SERVER.value:
            self.__populate_hostname(host_name)
            self.__populate_clientname(server_name)
            self.__set_credential(credential, vs_username, vs_password)
            self.__wizard_obj.select_drop_down_values(id='accessNodes', values=["Automatic"])
            self.__wizard_obj.click_button(name=self.__admin_console.props['button.discover.nodes'])
            self.__wizard_obj.select_drop_down_values(id='accessNodes', values=[proxy.upper() for proxy in proxy_list])
        elif vendor == hypervisor_type.Nutanix.value:
            self.__select_vendor_type(vendor)
            self.__wizard_obj.click_next()
            self.__set_hostname(host_name)
            self.__set_servername(server_name)
            self.__set_username(vs_username)
            self.__set_password(vs_password)
            self.__wizard_obj.select_drop_down_values(id='accessNodes', values=proxy_list)
        elif vendor == HypervisorDisplayName.MS_VIRTUAL_SERVER.value:
            self.__set_hostname(host_name)
            self.__set_servername(server_name)
            self.__set_username(vs_username)
            self.__set_password(vs_password)
            self.__admin_console.click_button(self.__admin_console.props['button.discover.nodes'])
            # check if at all the discovery is successful.
            self.__admin_console.check_error_message()
            # select proxy from the discovered access node list
            self.__wizard_obj.select_drop_down_values(id='accessNodes',
                                                      values=[proxy.upper() for proxy in proxy_list])

            self.__wizard_obj.click_next()
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()
            self.__admin_console.log.info("Hypervisor created successfully")
            self.__vm_groups_obj.add_vm_group(vm_group_name, vm_content, plan=plan, vendor=vendor)

        elif vendor == HypervisorDisplayName.AMAZON_AWS.value:
            self.__set_servername(server_name)
            if regions is not None:
                self.__admin_console.fill_form_by_id("region", regions)
            self.__hypervisor_details_obj.set_aws_auth(auth_type, credential)
            if admin_hypervisor is not None:
                self.__hypervisor_details_obj.set_admin_hypervisor(admin_hypervisor)
            else:
                self.__wizard_obj.select_drop_down_values(id='accessNodes', values=proxy_list)
        elif vendor == HypervisorDisplayName.Alibaba_Cloud.value:
            self.__set_servername(server_name)
            self.__set_access_key(access_key)
            self.__set_secret_key(secret_key)
        elif vendor == HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value:
            self.__set_servername(server_name)
            self.__set_credential(credential, vs_username, vs_password)
            self.__set_access_nodes(proxy_list)
        elif vendor in [HypervisorDisplayName.MICROSOFT_AZURE.value, HypervisorDisplayName.Azure_Stack.value]:
            self.__set_servername(server_name)
            self.__set_subscription_id(subscription_id)
            self.__hypervisor_details_obj.set_azure_auth(auth_type, credential)
            self.__wizard_obj.select_drop_down_values(id='accessNodes', values=proxy_list)
        elif vendor == HypervisorDisplayName.Vcloud.value:
            if admin_hypervisor is not None:
                self.__set_admin_hypervisor(admin_hypervisor=admin_hypervisor, vendor=vendor, server_name=server_name)
                self.__wizard_obj.select_drop_down_values(id='organization', values=[vcloud_organization])
                self.__wizard_obj.select_drop_down_values(id='company', values=[company])
            else:
                self.__set_hostname(host_name)
                self.__set_servername(server_name)
                self.__set_credential(credential)
                self.__set_access_nodes(proxy_list)
                self.__wizard_obj.click_next()
                alert_messages = self.__admin_console.driver.find_elements(By.CLASS_NAME, 'MuiAlert-message')
                if alert_messages and ("skip SSL certificate validation" in alert_messages[1].text):
                    self.__wizard_obj.disable_toggle(label="Verify SSL certificate")
                    self.ssl_check[server_name] = False
                    self.__admin_console.log.info(f"SSL Validation has been disabled for {server_name}")
                    self.__wizard_obj.click_next()
                else:
                    self.ssl_check[server_name] = True
                    self.__admin_console.log.info(f"SSL Validation has been enabled for {server_name}")
                self.__admin_console.wait_for_completion()
                self._setup_associated_vcenters(associated_vcenters)


        elif vendor == HypervisorDisplayName.Google_Cloud.value:
            self.__set_servername(server_name)
            self.__set_credential(credential)
            self.__wizard_obj.select_drop_down_values(id='accessNodes', values=proxy_list)

        self.__wizard_obj.click_next()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        if vendor == HypervisorDisplayName.Google_Cloud.value:
            self.__vm_groups_obj.add_vm_group(vm_group_name, vm_content, plan=plan, vendor=vendor,
                                              project=kwargs.get('project'))
        else:
            self.__vm_groups_obj.add_vm_group(vm_group_name, vm_content, plan=plan, vendor=vendor)
        self.__admin_console.wait_for_completion()
        self.__wizard_obj.click_button(name=self.__admin_console.props['Finish'])
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        self.__admin_console.log.info("Successfully added hypervisor.")

    @WebAction()
    def __set_credential(self, credential, vs_username=None, vs_password=None):
        """
        Set a saved Windows Account credential if it already exists or create a new credential object

        credential (str) : Name of the saved credential
        vs_username (str) : credential username
        vs_password (str) : credential password

        """
        try:
            # Try to select existing saved credential
            self.__panel_dropdown_obj.wait_for_dropdown_load(drop_down_id="credentials")
            if credential in self.__panel_dropdown_obj.get_values_of_drop_down(drop_down_id="credentials",
                                                                               search=credential):
                self.__panel_dropdown_obj.select_drop_down_values(drop_down_id="credentials", values=[credential])
                self.__admin_console.log.info(f"Selected credential with given name {credential}")
            else:
                # Create a new credential, if existing credential with the same name is not present
                self.__admin_console.log.info(f"Credential with the given name {credential} does not exist."
                                              f"Creating a new credential object")
                if not vs_username or not vs_password:
                    raise Exception("Invalid username or password field")
                self.__wizard_obj.click_add_icon()
                self.__admin_console.wait_for_completion()
                self.__create_win_acc_credential(credential, vs_username, vs_password)
                self.__admin_console.wait_for_completion()
                self.__wizard_obj.click_refresh_icon()
                self.__panel_dropdown_obj.wait_for_dropdown_load(drop_down_id="credentials")
                self.__panel_dropdown_obj.select_drop_down_values(drop_down_id="credentials", values=[credential])
                self.__admin_console.log.info(f"Selecting credential with given name {credential}")

        except Exception as exp:
            raise Exception(f"Credential could not be created due to the following error: {exp}")

    @WebAction()
    def __create_win_acc_credential(self, credential, vs_username, vs_password):
        """
            Create new credential object

            credential (str): Name of the credential
            credential (str) : Name of the saved credential
            vs_username (str) : credential username
            vs_password (str) : credential password

            """
        try:
            if not credential:
                credential = "auto_generated_credential"

            self.__modal_dialog_obj.fill_input_by_xpath(element_id="name", text=credential)
            self.__modal_dialog_obj.fill_input_by_xpath(element_id="userAccount", text=vs_username)
            self.__modal_dialog_obj.fill_input_by_xpath(element_id="password", text=vs_password)
            description = "This is an auto generated credential"
            self.__modal_dialog_obj.fill_input_by_xpath(element_id="description", text=description)
            self.__modal_dialog_obj.click_submit()
            self.__admin_console.check_error_message()
            self.__admin_console.log.info(f"Successfully created a new credential with name {credential}")

        except Exception as exp:
            raise Exception(f"Could not create a new credential : {exp}")

    @WebAction()
    def _setup_associated_vcenters(self, associated_vcenters=None):
        """
        setup credentials for vcenters associated with vcloud setup

        Args:
            associated_vcenters     (dict)     -       Dictionary containing credentials for the associated vCenters
                                                       for the vCloud hypervisor in the form of
                                                       {
                                                            <vCenter Hostname> : <Saved Credential for vCenter>
                                                       }
        """
        for vcenter, credential in associated_vcenters.items():
            self.__table_obj.access_action_item(entity_name=vcenter, action_item='Edit')
            self.__panel_dropdown_obj.select_drop_down_values(drop_down_label='Credential', values=[credential])
            self.__panel_info_obj.click_button("Save")
        self.__wizard_obj.click_next()
        self.__admin_console.wait_for_completion()

        alert_message = self.__admin_console.driver.find_element(By.CSS_SELECTOR,
                                                                 '[aria-label*="valid SSL certificate"]')
        if alert_message and ("valid SSL certificate" in alert_message.text):
            vcenter_names = self.__table_obj.get_column_data("vCenter details", True)
            toggle_elements = self.__admin_console.driver.find_elements(By.ID, "enableSSLValidationToggle")
            if toggle_elements:
                for index, toggle_element in enumerate(toggle_elements):
                    self.__admin_console.driver.execute_script("arguments[0].scrollIntoView(true);", toggle_element)
                    if toggle_element.is_enabled():
                        toggle_element.click()
                        self.ssl_check[vcenter_names[index]] = False
                        self.__admin_console.log.info(f"SSL Validation has been disabled for {vcenter_names[index]}")
                    else:
                        self.ssl_check[vcenter_names[index]] = True
                        self.__admin_console.log.info(f"SSL Validation has been enabled for {vcenter_names[index]}")

    @WebAction()
    def __set_admin_hypervisor(self, admin_hypervisor=None, vendor=None, server_name=None):
        """
        Sets the admin hypervisor

        Args:
            admin_hypervisor (str)  -   admin hypervisor client name to set
            vendor           (str)  -   hypervisor vendor being used

        Returns:
            None
        """
        if vendor == HypervisorDisplayName.Vcloud.value:
            self.__wizard_obj.enable_toggle(label='Create organization account')
            self.__admin_console.fill_form_by_id("servername", server_name)
            self.__wizard_obj.select_drop_down_values(id='AdminAccount', values=[admin_hypervisor])
        else:
            self.__wizard_obj.enable_toggle(label='Use service account resources')
            self.__wizard_obj.select_drop_down_values(id='useServiceAccount', values=[admin_hypervisor])

    @PageService()
    def action_jobs(self, server_name):
        """
        Opens the job details page for the chosen server

        Args:
            server_name  (str):  name of the hypervisor whose jobs needs to be opened

        """
        self.__table_obj.access_action_item(server_name, self.__admin_console.props['action.jobs'])

    @PageService()
    def action_retire(self, server_name):
        """
        delete a server with the specified name

        Args:
            server_name  (str):  name of the hypervisor server to be deleted

        """
        self.__table_obj.access_action_item(server_name, self.__admin_console.props['action.commonAction.retire'])
        self.__admin_console.fill_form_by_id('confirmText', 'RETIRE')
        self.__admin_console.click_button("Retire")

    @PageService()
    def action_send_logs(self, server_name):
        """
        Send logs of a server with the specified name

        Args:
            server_name  (str):  name of the server whose logs needs to be sent

        """
        self.__table_obj.access_action_item(server_name, self.__admin_console.props['action.sendLogs'])

    @PageService()
    def hypervisor_restore(self, hypervisor_name, subclient_name=None):
        """
        Restores the given subclient in the hypervisor

        Args:
            hypervisor_name      (str):  the name of the hypervisor whose subclient is to
                                                be restored

            subclient_name       (str):  the name of the subclient to be restored

        Raises:
            Exception:
                if there is no subclient with the given name
                if restore could not be selected
                if the hypervisor was not backed up

        """
        self.__admin_console.log.info("Restoring subclient %s in hypervisor %s", subclient_name, hypervisor_name)
        self.__table_obj.access_link(hypervisor_name)
        url = self.__admin_console.current_url()
        self.__table_obj.access_action_item(subclient_name, self.__admin_console.props['pageTitle.restore'])
        if self.__admin_console.current_url() == url:
            self.__select_subclient(subclient_name)
            self.__admin_console.wait_for_completion()
            self.__admin_console.submit_form()
        else:
            self.__admin_console.log.info("There was only backed up subclient in the hypervisor")

    @PageService()
    def list_company_hypervisors(self, company_name):
        """
        Lists the companies whose hypervisors needs to be displayed

        Args:
            company_name (str):  the name of the company

        """
        self.__navigator.switch_company_as_operator(company_name)

    @PageService(hide_args=True)
    def is_hypervisor_exists(self, hyperv_name):
        """Checks if hypervisor exists

            Args:

                hyperv_name (str)  --  Hyperv name
        """
        self.__table_obj.search_for(hyperv_name)
        hyperv_data = self.__table_obj.get_column_data('Name')
        return hyperv_name in hyperv_data

    @PageService()
    def retire_hypervisor(self, server_name):
        """
        Performs retire action for the given server

        Args:
                server_name     (str) -- server name to retire
        """
        if self.is_hypervisor_exists(server_name):
            self.__table_obj.access_action_item(server_name, self.__admin_console.props['action.commonAction.retire'])
            self.__admin_console.fill_form_by_id("confirmText",
                                                 self.__admin_console.props['action.commonAction.retire'].upper())
            self.__admin_console.click_button_using_text(self.__admin_console.props['action.commonAction.retire'])
            self.__admin_console.wait_for_completion()
            self.__admin_console.check_error_message()
        else:
            return

        # Validate whether hypervisor deleted or not.
        if not self.is_hypervisor_exists(server_name):
            self.__admin_console.log.info("Hypervisor doesnt exist")
            pass
        else:
            self.__admin_console.log.error("Hypervisor not deleted")
            raise Exception
