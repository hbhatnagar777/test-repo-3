from selenium.webdriver.common.by import By

# !/usr/bin/env python

"""
This module provides all the methods that can be done of the NAS_File_Servers page.


Classes:

    NAS_File_Servers() ---> LoginPage --->
    AdminConsoleBase() ---> object()


NAS_File_Servers  --  This class contains all the methods for action in NAS_File_Servers page and
                  is inherited by other classes to perform NAS Client related actions

    Functions:

    select_nas_client()        		--  Opens the server with the given name
    action_jobs()                	--  Opens the job details page for the chosen NAS File Server
    action_add_software()			--	Allows user to select different iDAs under NAS Client
    action_release_license()        --  Allows user to Releases Licenses consumed by NAS Client
    action_send_logs()           	--  Sends logs of a server with the specified name
    action_backup()					--	Runs Backup of specified subClient of NAS File Server
    action_restore()				--	Runs Restore from defaultbackupSet of NAS File Server
    delete_client()                 --  Deletes NAS Client.
    add_nas_client()                --  Add a new NAS Client.

"""
from enum import Enum
import time
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import PanelInfo, DropDown, ModalPanel
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.page_object import PageService, WebAction
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.FSPages.RFsPages.network_share import NFS, CIFS, NDMP


class Vendor(Enum):
    """
    List of all Vendors.
    """
    DELL_EMC_ISILON = "Dell EMC Isilon"
    DELL_EMC_UNITY = "Dell EMC Unity"
    DELL_EMC_VNXCELERRA = "Dell EMC VNX/Celerra"
    HITACHI_NAS = "Hitachi NAS"
    HUAWEI = "Huawei"
    NETAPP = "NetApp"


class NASFileServers:
    """
    This class contains all the methods for action in NAS_File_Servers page
    """

    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = admin_console.driver
        self.admin_console.load_properties(self)
        self.__table = Table(self.admin_console)
        self.__drop_down = DropDown(self.admin_console)
        self.__panel = PanelInfo(self.admin_console)
        self.__modal_panel = ModalPanel(self.admin_console)
        self.__wizard = Wizard(self.admin_console)
        self.__toggle = Toggle(self.admin_console)
        self.__rdialog = RModalDialog(self.admin_console)
        self.__rdrop_down = RDropDown(self.admin_console)

    @staticmethod
    def _create_array(admin_console, vendor, array_details):
        """
        Creates and returns an instance of the array vendor.

        Args:

            admin_console   (obj)   --  Instance of admin_console object

            vendor          (enum)  --  Vendor name, values can be found under class Vendor.

            array_details   (dict)  :   The dictionary of array details.
            Dictionary contains the keys array_name, control_host, username and password.

                array_name      (str)    :   Name of the array.

                control_host    (str)    :   Control host name if applicable to the array.

                username        (str)    :   Username for the array, defined in config.json.

                password        (str)    :   Password for the array, defined in config.json.

        """
        if vendor != Vendor.NETAPP:
            return DellEMCIsilonArray(admin_console, array_details)
        return

    @WebAction()
    def __get_access_nodes(self, accessnode_ma):
        """Returns MA count and opt"""
        ma_cnt = 0
        opt = 0
        element = self.driver.find_element(By.ID, 'detectMa')
        for option in element.find_elements(By.TAG_NAME, 'option'):
            ma_cnt = ma_cnt + 1
            cmptxt = option.text
            cmptxt = cmptxt[17: len(cmptxt) - 14]
            if not accessnode_ma and str(cmptxt) == str(accessnode_ma):
                opt = ma_cnt
        return ma_cnt, opt

    @WebAction()
    def __get_text(self):
        """Gets text"""
        return self.driver.find_element(By.TAG_NAME, "html").text

    @WebAction()
    def __click_backup(self):
        """Clicks backup"""
        self.driver.find_element(By.LINK_TEXT, "Backup").click()

    @WebAction()
    def __click_subclient(self, subclient_name):
        """Clicks subclient"""
        self.driver.find_element(By.XPATH, "//label[text()='" + subclient_name + "']/../..//input").click()

    @WebAction()
    def __click_submit(self):
        """Clicks submit"""
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

    @WebAction
    def __click_restore(self):
        """Clicks restore"""
        self.driver.find_element(By.XPATH, "*//a[.='Restore']/..").click()

    @PageService()
    def select_nas_client(self, server_name):
        """
        Opens the NAS File Server with the given name

        Args:
            server_name  (str):  the name of the server to be opened

        """
        self.__table.access_link(server_name)

    @PageService()
    def add_nas_client(self, name, host_name, plan, vendor=None, **kwargs):
        """
        Adds a new NAS File Server with the Chosen iDAs and Access Nodes.

        Args:
            name        (str)    :   The  name of the NAS/Network Share client to be created.

            host_name   (str)    :   The host name of the NAS/Network Share client to be created.

            plan        (str)    :   The name of the plan that needs to be associated to the client.

            vendor      (Vendor(Enum))  :   The name of the vendor, supports following values.
                -   DELL_EMC_ISILON

            kwargs  (dict)              --  Optional arguments.

            Available kwargs Options:

                    array_details   (dict)  :   The dictionary of array details.
                     Dictionary contains the keys array_name, control_host, username and password.

                        array_name      (str)    :   Name of the array.

                        control_host    (str)    :   Control host name if applicable to the array.

                        username        (str)    :   Username for the array, defined in CoreUtils\config.json.

                        password        (str)    :   Password for the array, defined in CoreUtils\config.json.

                        access_nodes    (str)   :   access nodes for the array

                    cifs            (dict)  :   The dictionary of CIFS Agent details.
                    Dictionary contains the keys access_nodes, impersonate_user and content.

                        access_nodes        (list)  :   List of access node names, access node names are strings.

                        impersonate_user    (dict)  :   The dictionary of impersonation account details.
                        Dictionary contains the keys username and password.

                            username    (str)    :   Username of the account, defined in CoreUtils\config.json.

                            password    (str)    :   Password of the account, defined in CoreUtils\config.json.

                        client_level_content    (list)  :   List of content paths, content paths are strings.
                     ndmp            (dict)  :   The dictionary of NDMP Agent details.
                    Dictionary contains the keys access_nodes, impersonate_user and content.

                        access_nodes        (list)  :   List of access node names, access node names are strings.

                        impersonate_user    (dict)  :   The dictionary of impersonation account details.
                        Dictionary contains the keys username and password.

                            username    (str)    :   Username of the account, defined in CoreUtils\config.json.

                            password    (str)    :   Password of the account, defined in CoreUtils\config.json.

                            credential_manager (bool) : if credential manager cred passed in json set to True else False

                            credential_manager_name (str) : credential manager name

                           client_level_content  (list)  :   List of content paths, content paths are strings.
                     nfs            (dict)  :   The dictionary of CIFS Agent details.
                    Dictionary contains the keys access_nodes, impersonate_user and content.

                        access_nodes        (list)  :   List of access node names, access node names are strings.

                        client_level_content     (list)  :   List of content paths, content paths are strings.


        """

        self.admin_console.click_button('Add server')
        self.__wizard.select_radio_card('NAS')
        self.__wizard.click_next()

        self.__wizard.fill_text_in_field(id="displayName", text=name)
        self.__wizard.fill_text_in_field(id="hostName", text=len(name) * Keys.DELETE)
        self.__wizard.fill_text_in_field(id="hostName", text=host_name)
        self.__wizard.click_next()

        # select plan
        self.__wizard.select_plan(plan_name=plan)
        self.__wizard.click_next()

        # enable toggle for backup method
        if kwargs.get('cifs', None):
            self.__wizard.enable_toggle(label="CIFS")
        if kwargs.get('nfs', None):
            self.__wizard.enable_toggle(label="NFS")
        if kwargs.get('ndmp', None):
            self.__wizard.enable_toggle(label="NDMP")
        self.__wizard.click_next()

        # network share configuration
        if vendor and kwargs.get('array_details', None):
            self.__wizard.click_icon_button_by_title(title="Add array")
            self.__wizard.select_drop_down_values(id="vendorDropdown", values=[vendor.value])
            array = self._create_array(self.admin_console, vendor, kwargs.get('array_details', None))
            array.fill_array_details(kwargs['array_details'])
            if kwargs.get('array_details')['access_nodes']:
                self.__wizard.select_drop_down_values(id="arrayAccessNodeDropDown",
                                                      values=[kwargs.get('array_details')['access_nodes']])
            self.admin_console.click_button(id="Save")

        from Web.AdminConsole.FSPages.RFsPages.RFile_servers import AddWizard
        self.__raddwizard = AddWizard(self.admin_console)

        if kwargs.get('cifs', None):
            cifs = CIFS(self.admin_console, kwargs.get('cifs', None))
            cifs_values = kwargs.get('cifs')['impersonate_user']
            index = 2
            if cifs.access_nodes is not None:
                cifs.add_access_nodes(index=index)
            if cifs_values['username'] is not None and cifs_values['password'] is not None:
                self.__wizard.click_icon_button_by_title(title="Select credential.")
                self.__rdialog.deselect_checkbox(checkbox_id="toggleFetchCredentials")
                cifs.edit_impersonate_user()
            if kwargs.get('cifs')['client_level_content'] is not None:
                self.__wizard.disable_toggle(label="All CIFS shares")
                self.__raddwizard.set_backup_content_filters(contentpaths=kwargs.get('cifs')['client_level_content'],
                                                             contentfilters=kwargs.get('cifs').get('client_level_filters', []),
                                                             contentexceptions=kwargs.get('cifs').get('client_level_exceptions', []),
                                                             is_nas_subclient=True)

        if kwargs.get('nfs', None):
            nfs = NFS(self.admin_console, kwargs.get('nfs', None))
            index = 2
            if kwargs.get('cifs', None):
                index = 3
            if nfs.access_nodes is not None:
                time.sleep(10)
                nfs.add_access_nodes(index=index)
            if kwargs.get('nfs')['client_level_content'] is not None:
                self.__wizard.disable_toggle(label="All NFS exports")
                self.__raddwizard.set_backup_content_filters(contentpaths=kwargs.get('nfs')['client_level_content'],
                                                             contentfilters=kwargs.get('nfs').get('client_level_filters', []),
                                                             contentexceptions=kwargs.get('nfs').get('client_level_exceptions', []),
                                                             is_nas_subclient=True)

        if kwargs.get('cifs', None) or kwargs.get('nfs', None) or kwargs.get('ndmp', None):
            self.__wizard.click_next()

        if kwargs.get('ndmp', None):
            ndmp = NDMP(self.admin_console, kwargs.get('ndmp', None))
            ndmp_values = kwargs.get('ndmp')['impersonate_user']
            if ndmp.access_nodes is not None:
                ndmp.add_access_nodes()
            if (ndmp_values['username'] is not None and ndmp_values['password'] is not None) and \
                    (kwargs.get('ndmp')['credential_manager'] and kwargs.get('ndmp')['credential_manager_name']):
                self.__wizard.click_icon_button_by_title(title="Create new")
                self.admin_console.fill_form_by_name("name", kwargs.get('ndmp')['credential_manager_name'])
                self.admin_console.fill_form_by_name("userName", ndmp_values['username'])
                self.admin_console.fill_form_by_name("password", ndmp_values['password'])
                self.admin_console.click_button(id="Save")
            else:
                self.__wizard.select_radio_button(id="useSavedCredentials")
                ndmp.edit_impersonate_user()
            self.__wizard.click_next()

        self.__wizard.click_button(name="Add")
        self.admin_console.wait_for_completion()

    @PageService()
    def action_jobs(self, server_name):
        """
        Opens the job details page for the chosen server

        Args:
            server_name  (str):  the name of the server to be opened

        """
        self.__table.access_action_item(server_name, "Jobs")

    @PageService()
    def action_send_logs(self, server_name):
        """
        Send logs of a server with the specified name

        Args:
            server_name  (str):  the name of the server to be opened

        """
        self.__table.access_action_item(server_name, "Send logs")

    @PageService()
    def action_release_license(self, server_name):
        """"
        Release CIFS and NFS Licenses

        Args:
            server_name  (str):  the name of the server to be opened

        """
        self.__table.access_action_item(server_name, "Release license")
        if "Server File System - Linux File System" in self.__get_text():
            self.admin_console.heckbox_select("Server File System - Linux File System")
        if "Server File System - Windows File System" in self.__get_text():
            self.admin_console.checkbox_select("Server File System - Windows File System")
        if "NDMP - NDMP" in self.__get_text():
            self.admin_console.checkbox_select("NDMP - NDMP")
        self.admin_console.click_button("OK")
        # self.log.info("Release license successful on Client:" + server_name)

    @PageService()
    def action_backup(self, server_name, idataagent, subclient_name, backup_type):
        """"
        Running backup of subClients under defaultbackupset

        Args:
            server_name  (str):  the name of the server to be opened

            idataagent  (str):   the name of the iDA (NDMP or CIFS or NFS)

            subclient_name (str):    name of the subclient to be backed up
            backup_type (BackupType):   the backup type to be run, among the type in Backup.BackupType enum

        Returns (int) : the backup job ID
        """

        self.__table.search_for(server_name)
        self.__click_backup()
        self.admin_console.wait_for_completion()
        if idataagent == 'NDMP':
            # self.log.info("Finding for SubClient under NDMP Agent")
            self.__click_subclient(subclient_name)
            self.admin_console.wait_for_completion()
        elif idataagent == 'CIFS':
            # self.log.info("Finding for subClient under CIFS Agent")
            self.__click_subclient(subclient_name)
            self.admin_console.wait_for_completion()
        elif idataagent == 'NFS':
            # self.log.info("Finding for subClient under NFS Agent")
            self.__click_subclient(subclient_name)
            self.admin_console.wait_for_completion()
        else:
            raise Exception("Invalid iDA name passed")
        self.__click_submit()
        self.admin_console.wait_for_completion()
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @PageService()
    def action_restore(self, server_name, idataagent, subclient_name):
        """"
            Running Restore of Data backed up by SubClient under defaultbackupSet of NAS Client

            Args:
                server_name  (str):  the name of the server to be opened

                idataagent  (str):   the name of the iDA (NDMP or CIFS or NFS)

                subclient_name (str):    name of the subclient to be backed up

        """
        self.__table.search_for(server_name)
        self.__click_restore()
        self.admin_console.wait_for_completion()
        if "Backup content" in self.__get_text():
            self.admin_console.wait_for_completion()
        elif "Please select a subclient or instance to restore" in self.__get_text():
            if idataagent == 'NDMP':
                self.__click_subclient(subclient_name)
                self.admin_console.wait_for_completion()
            elif idataagent == 'Windows File System':
                self.__click_subclient(subclient_name)
                self.admin_console.wait_for_completion()
            elif idataagent == 'Linux File System':
                self.__click_subclient(subclient_name)
                self.admin_console.wait_for_completion()
            else:
                raise Exception("Invalid Agent Passed")
            self.admin_console.click_button("Select")
        else:
            return

    @PageService()
    def delete_client(self, server_name):
        """
            Deletes Deconfigured NAS NDMP Client

            Args:
                server_name  (str):  the name of the server to be opened

        """

        self.__table.access_action_item(server_name, "Delete")
        # self.log.info("Proceeding with Client Deletion")
        self.admin_console.click_button("Yes")


class __Array:
    """
    This class contains all the methods for action on the Add Array Page.
    """

    @PageService()
    def fill_array_details(self, array_details):
        """
        Fill in all the array details.
        Args:
            array_details   (dict)  :   Dictionary of array details, refer to add_nas_client() docstring.
        """
        self.admin_console.fill_form_by_id("arrayName", len(array_details['array_name']) * Keys.DELETE)
        self.admin_console.fill_form_by_id("arrayName", array_details['array_name'])
        self.admin_console.fill_form_by_id("username", array_details['username'])
        self.admin_console.fill_form_by_id("password", array_details['password'])


class DellEMCIsilonArray(__Array):
    """
    Class for Dell EMC Isilon Array Vendor.
    """

    def __init__(self, admin_console, array_details):
        """
            Method to initiate DellEMCIsilon Array class
            Args:
                admin_console   (Object) :   admin console object
                array_details   (Dict) :   contains array details DellEMCIsilion array
        """
        self.admin_console = admin_console
        self.array_details = array_details

    @PageService()
    def fill_array_details(self, array_details):
        """
        Fill in all the array details.

        Args:
            array_details   (dict)  :   Dictionary of array details, refer to add_nas_client() docstring.

        """
        super().fill_array_details(self.array_details)
        if self.array_details['control_host']:
            self.get_control_host_element(self.array_details['control_host'])

    @WebAction()
    def get_control_host_element(self, control_host_name):
        """
        Fill control host name in control host field.
        args:
            control_host_name(str)  : name of control host
        """
        self.admin_console.fill_form_by_id("controlHost", control_host_name)


class NutanixFilesArray(__Array):
    """
    Class for NutanixFiles Array Vendor.
    """
    def __init__(self, admin_console, array_details):
        """
            Method to initiate NutanixFiles Array class
            Args:
                admin_console   (Object) :   admin console object
                array_details   (Dict) :   contains array details NutanixFilesArray array
        """
        self.admin_console = admin_console
        self.array_details = array_details


class NetApp(__Array):
    """
    Class for NetApp Array Vendor.
    """
    def __init__(self, array_details, driver):
        """
            Method to initiate Netapp Array class
            Args:
                array_details  (Dict) : contains array details NutanixFilesArray array
                driver   (Object) :   driver object
        """
        raise NotImplementedError

