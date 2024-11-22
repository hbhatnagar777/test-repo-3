# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done on the VM groups page.


Classes:

    VMGroups() ---> _Navigator() ---> AdminConsoleBase() ---> object()


VMGroups  --  This class contains all the methods for action in VM groups page and is inherited
                  by other classes to perform VSA related actions

Functions:

    select_vm_group()			--	Opens the VM group with the given name

    add_vm_group()          	--  Creates a VM group for the given hypervisor

    action_backup_vm_groups()   --  Backs up the given VM group

    action_delete_vm_groups()   --  Deletes the given VM groups

    action_restore_vm_group()   --  Restores the given VM group

    action_jobs_vm_group()      --  Opens the jobs page of the VM group

    select_vm_group_hypervisor()--  Opens the hypervisor client of the VM group

    list_vm_groups()            --  Lists all the VM groups

    set_vm_group_content()      -- Sets the given VM group content

    select_content_type()       --Selects the content type from list

    action_list_snapshots()     -- list the snaps of particular vm group at VMgroups level

"""
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type, HypervisorDisplayName
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.manage_content import ManageContent
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException


class VMGroups:
    """
    Class for the VM groups page
    """

    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.

        Args:
            driver      (object)   :  the browser object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__hyp_det_obj = HypervisorDetails(admin_console)
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__panel_info_obj = PanelInfo(admin_console)
        self.__rpanel_info_obj = RPanelInfo(admin_console)
        self.__rdropdown_panel_obj = RDropDown(admin_console)
        self.__table = Rtable(admin_console)
        self.__wizard_obj = Wizard(admin_console)
        self.__rmodal_obj = RModalDialog(admin_console)
        self.__manage_content_obj = ManageContent(self.__admin_console)
        self.__page_container_obj = None

    @PageService()
    def select_vm_group(self, vm_group_name):
        """
        Opens the VM group with the given name

        Args:
            vm_group_name (str) :  the name of the VM group to open

        """
        self.__admin_console.wait_for_completion()
        self.__table.access_link(vm_group_name)

    @PageService()
    def add_vm_group(self, vm_group_name, vm_content, hypervisor_name=None, plan=None, vendor=None, is_metallic=False, **kwargs):
        """
        Adds a new VM group

        Args:
            hypervisor_name (str)     : the hypervisor whose VMs should be grouped

            vm_group_name (str)       : the name of the vm group to create

            vm_content      (dict)    :   the content to be added to the subclient
            

                Sample value:   {'Datastores and datastore clusters':[ds1,ds2],
                                 'Hosts and clusters':[h1,h2],
                                 'Tags and categories':[tag1,category1],
                                 'VMs and templates':[vm1,vm2],
                                 'Storage':[strg1, strg2]
                                }
                AWS:            {'Instances':{'By Zone':{us-east-1a:['c','d']}}}
                                {'Instances':{'By region':{'us-east-1':['a',b]}}}
            plan            (str)    :   the plan to be associated with the subclient

            vendor          (str)   : name of the vendor

            is_metallic     (bool)  : true, if creating vmgroup in metallic dashboard

        """
        if hypervisor_name is not None:
            self.__page_container_obj = PageContainer(self.__admin_console)
            self.__page_container_obj.access_page_action(name=self.__admin_console.props['action.addVMGroup'])
            if is_metallic:
                self.__wizard_obj.select_radio_card(vendor)
                self.__wizard_obj.click_next()
                self.__admin_console.wait_for_completion()
                self.__wizard_obj.click_next()
                self.__admin_console.wait_for_completion()
            self.__wizard_obj.select_drop_down_values(id='Hypervisor', values=[hypervisor_name])
            self.__wizard_obj.click_next()
            self.__admin_console.wait_for_completion()
            self.__wizard_obj.select_plan(plan)
            self.__wizard_obj.click_next()
            self.__admin_console.wait_for_completion()
        self.__wizard_obj.fill_text_in_field(id="name", text=vm_group_name)
        self.set_vm_group_content(vendor, vm_content, **kwargs)
        if hypervisor_name is None:
            self.__wizard_obj.select_drop_down_values(id='plan', values=[plan])
            self.__wizard_obj.click_next()
            self.__admin_console.wait_for_completion()
        else:
            self.__wizard_obj.click_button(self.__admin_console.props['action.submit'])
            self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def set_vm_group_content(self, vendor, vm_content, remove_existing_content=False, vm_group=None, **kwargs):
        """
        Sets the vm group content

        vendor                  (str)   -Vendor name

        vm_content              (str)   -content to be set

        remove_existing_content (bool)  -clears the list of content

        vm_group                (str)   -name of vmgroup
        

        Returns None
        """
        if vm_group is not None:
            self.select_vm_group(vm_group)
            self.__admin_console.select_content_tab()
            self.__manage_content_obj.vsa_sc_obj.manage_content()
        if remove_existing_content:
            self.__table.select_all_rows()
            self.__rmodal_obj.click_button_on_dialog(self.__admin_console.props['label.delete'])
        if vendor in [HypervisorDisplayName.AMAZON_AWS.value, HypervisorDisplayName.MICROSOFT_AZURE.value,
                      hypervisor_type.MS_VIRTUAL_SERVER.value, HypervisorDisplayName.VIRTUAL_CENTER.value,
                      HypervisorDisplayName.Nutanix.value, HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value,
                      HypervisorDisplayName.Vcloud.value, HypervisorDisplayName.Google_Cloud.value]:
            if type(vm_content) == list:
                self.__search_and_set_content(vm_content, **kwargs)
            else:
                for _key, _value in vm_content.items():
                    if _key == "Content":
                        self.__set_content_for_vmgroup(_key, vm_content)
                    else:
                        self.__set_rules_for_vmgroup(_key, vm_content)
            if remove_existing_content:
                self.__rmodal_obj.click_submit()
                self.__admin_console.wait_for_completion()
        else:
            self.__wizard_obj.click_button(self.__admin_console.props['label.addVirtualMachine'])
            self.__hyp_det_obj.select_vm_from_browse_tree(vm_content)

    def __search_and_set_content(self, vm_content, **kwargs):
        """
        Searches for the given VMs and sets the content

        vm_content  (list)  --Content to be set
        
        Returns None
        """
        for vm in vm_content:
            self.select_content_type("Content")
            __add_content_modal = RModalDialog(self.__admin_console, title='Add content')
            self.__admin_console.wait_for_completion()
            self.__hyp_det_obj.select_content_from_browse_tree([vm], **kwargs)
            __add_content_modal.click_button_on_dialog(self.__admin_console.props['label.save'])

    def __set_content_for_vmgroup(self, key, vm_content):
        """
        Sets the Content by browse

        vm_content  (list)  --Content to be set

        Returns None
        """
        self.select_content_type(key)
        count = -1
        __add_content_modal = RModalDialog(self.__admin_console, title='Add content')
        for content in vm_content[key]:
            for _browse_type, _values in content.items():
                count += 1
                if count > 0:
                    self.select_content_type(key)
                self.__select_browse_type(_browse_type)
                for _category_name, _vms in _values.items():
                    if _browse_type == "By region":
                        self.__hyp_det_obj.select_content_from_browse_tree(_vms, region=_category_name)
                    elif _browse_type == "By zone":
                        self.__hyp_det_obj.select_content_from_browse_tree(_vms, zone=_category_name)
                    elif _browse_type == "Regions":
                        self.__hyp_det_obj.select_content_from_browse_tree(_vms, region=_category_name)
                    elif _browse_type == "Resource Groups":
                        self.__hyp_det_obj.select_content_from_browse_tree(_vms, resource_group=_category_name)
                    elif _browse_type == "Instance View":
                        self.__hyp_det_obj.select_content_from_browse_tree(_vms, compartment=_category_name)
                    else:
                        self.__hyp_det_obj.select_content_from_browse_tree(_vms)
                __add_content_modal.click_button_on_dialog(self.__admin_console.props['label.save'])

    def __set_rules_for_vmgroup(self, key, vm_content):
        """
        Sets the vm group content rules

        Returns None
        """
        count = -1
        self.select_content_type(key)
        __rule_modal = RModalDialog(self.__admin_console, title='Add rule')
        for _rules in vm_content[key]:
            count += 1
            for _rule_type, _values in _rules.items():
                _rule_exp = list(_values.keys())[0]
                _rule_name = list(_values.values())[0]
                if count > 0:
                    __rule_modal.click_button_on_dialog(text='Add')
                self.__manage_content_obj.add_rule(_rule_type, _rule_exp, _rule_name, count)
        __rule_modal.click_submit()

    @PageService()
    def action_backup_vm_groups(self, vm_group_name, backup_type):
        """
        Starts a backup of the given type for the specified collection

        Args:
           vm_group_name (str)  : the name of the VM group to backup
           backup_type (BackupType)    : the type of backup to run, among the type in Backup.BackupType enum

        Returns:
            the backup job ID
        """
        self.__table.access_action_item(vm_group_name, self.__admin_console.props['action.commonAction.backup'])
        backup = Backup(self.__admin_console)
        return backup.submit_backup(backup_type)

    @PageService()
    def action_delete_vm_groups(self, vm_group_name):
        """
        Deletes a vm group with the given name

        Args:
            vm_group_name (str) : the VM group to delete
        """
        if self.has_vm_group(vm_group_name):
            self.__table.access_action_item(vm_group_name, self.__admin_console.props['action.delete'])
            self.__admin_console.click_button(self.__admin_console.props['button.delete.yes'])
            self.__admin_console.wait_for_completion()
        else:
            return

        # Validate whether vmgroup got deleted or not.
        self.__admin_console.log.info("checking for deleted vmgroup")
        self.__admin_console.navigator.navigate_to_vm_groups()
        if not self.has_vm_group(vm_group_name):
            self.__admin_console.log.info("VM group doesnt exist")
            pass
        else:
            self.__admin_console.log.error("VM group not deleted")
            raise Exception

    @PageService()
    def action_restore_vm_groups(self, vm_group_name):
        """
        Opens the restore page of the vm group from the server details page

        Args:
            vm_group_name (str):  the VM group to restore

        """
        self.__table.access_action_item(vm_group_name, self.__admin_console.props['action.commonAction.restore'])

    @PageService()
    def action_jobs_vm_groups(self, vm_group_name):
        """
        Lists all the jobs of the specific subclient

        Args:
            vm_group_name (str): the VM group whose jobs should be opened
        """
        self.__table.access_action_item(vm_group_name, self.__admin_console.props['action.commonAction.jobs'])

    @PageService()
    def select_vm_group_hypervisor(self, vm_group_name):
        """
        Opens the hypervisor of the VM group provided

        Args:
            vm_group_name (str): name of the VM group whose hypervisor to open
        """
        vmgroups = self.__table.get_column_data("Name")
        hypersiors = self.__table.get_column_data("Hypervisor")
        index = vmgroups.index(vm_group_name)
        self.__admin_console.select_hyperlink(hypersiors[index])

    @PageService()
    def list_vm_groups(self):
        """
        Lists all the VM groups

        Returns:
            list of all VM groups
        """
        return self.__table.get_column_data("Name")

    @PageService()
    def has_vm_group(self, vm_group):
        """
        Check if vm group exists
        Args:
            vm_group               (str):   vm group name
        Returns                    (bool): True if vm group exists or False otherwise
        """
        if not self.__table.is_entity_present_in_column(self.__admin_console.props['label.name'], vm_group):
            return False
        return True

    @PageService()
    def get_details_by_vm_group(self, vm_group):
        """
        Get table content filtered by vm group
        Args:
            vm_group               (str):  vm group name
        Returns:                   (Dict): table content of specified vm group
        """
        if self.has_vm_group(vm_group):
            self.__table.search_for(vm_group)
            return self.__table.get_table_data()
        raise CVWebAutomationException("VM group [%s] not found in vm groups page" % vm_group)

    @PageService()
    def search_vmgroup(self, search_param):
        """
        Get table content filtered by vm group
        Args:
            search_param               (str):  Specify a search parameter
        Returns:                       (Dict): table content after searching the specified search parameter
        """
        self.__table.search_for(search_param)
        table_details = self.__table.get_table_data()
        if table_details:
            return table_details
        else:
            raise CVWebAutomationException("No records found after search with parameter [%s] " % search_param)

    @WebAction()
    def select_content_type(self, content_type):
        """
        Selects the content type from drop down

        content_type    (str)- content type, rule or content

        returns None
        """
        try:
            self.__wizard_obj.click_button(self.__admin_console.props['label.add'])
        except Exception as exp:
            self.__rmodal_obj.click_button_on_dialog(self.__admin_console.props['label.add'])
        self.__admin_console.click_by_xpath("//li[contains(text(), '" + content_type + "')]")

    @WebAction()
    def __select_browse_type(self, browse_type):
        """
        Sets the browse type in AWS add content screen

        browse_type (str)   - browse by zone or region or tags

        returns None
        """
        self.__wizard_obj.select_drop_down_values(id='vmBrowseView', values=[browse_type])

    @WebAction()
    def setup_disk_filters(self, disk_filter_obj={}):
        """
        Setup disk filters for a VM Group.
        """
        self.__manage_content_obj.disk_filters(disk_filter_obj)

    @PageService()
    def action_list_snapshots(self, vm_group_name):
        """
        list the snaps of particular vm group at VMgroups level
        Args:
            vm_group_name  (str):  the name of the Particular VMgroup for list of snapshots
        """
        self.__table.access_action_item(vm_group_name, "List snapshots")

    @WebAction()
    def clear_vm_filters(self):
        """
        Clear VM filters for a VM Group.
        """
        manage_content_dialog = RModalDialog(self.__admin_console, title="Manage content")
        manage_content_dialog.disable_toggle(label="Define filters")
        manage_content_dialog.click_save_button()
        self.__admin_console.wait_for_completion()
