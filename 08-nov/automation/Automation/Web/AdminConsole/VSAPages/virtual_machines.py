from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods to perform actions on vm.


Classes:

    VMsOwned() ---> _Navigator() ---> login_page ---> AdminConsoleBase() ---> object()


Hypervisors  --  This class contains methods to perform actions on vm like opening a vm, opening a
                  server of vm, listing backup vms etc.

    Functions:

    open_vm()               --  Opens VM with the given name

    open_hypervisor_of_vm() --  Opens the server corresponding to the VM name

    list_backup_vms()       --  Lists all the backup VM details

    action_remove_vm()      --  Removes the VM from the list of backed up VMs

    action_vm_jobs()        --    Displays all the jobs of the given VM

    action_vm_backup()      -- Backups the given VM

    action_vm_restore()     -- Restores the given VM

    run_validate_backup()   --  Runs backup validation job
    
    action_list_snapshots() --  list the snaps of particular vm at VM's level

"""
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Rtable, CVTable
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.Common.page_object import PageService, WebAction


class VirtualMachines:
    """
     This class contains methods to perform actions on vm like opening a vm, opening a server of \
     vm, listing backup vms etc.
    """
    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__table = Rtable(admin_console)
        self.__cvtable = CVTable(admin_console)

    @PageService()
    def open_vm(self, vm_name):
        """
        Opens VM with the given name

        Args:
            vm_name     (str):   name of the VM to open

        """
        self.__table.access_link(vm_name)

    @PageService()
    def open_hypervisor_of_vm(self, vm_name):
        """Opens the hypervisor corresponding to the VM name

        Args:
            vm_name  (str):  the name of the VM whose hypervisor has to be opened

        """
        all_vm_names = self.__table.get_column_data("Name")
        all_hypervisor_names = self.__table.get_column_data("Hypervisor")
        index = all_vm_names.index(vm_name)
        self.__admin_console.select_hyperlink(all_hypervisor_names[index])

    @WebAction()
    def list_backup_vms(self):
        """
        Lists all the backup VM details

        Returns:
            vms     (list):     list of all VMs owned by the user

        """
        vms = {}
        while True:
            elements = self.__admin_console.driver.find_elements(By.XPATH, "//div[@class='ui-grid-canvas']/div")
            for elem in elements:
                vm_details = []
                key = elem.find_element(By.XPATH, "./div/div[1]/a").text
                for index in range(2, 10):
                    if index == 2:
                        vm_details.append(elem.find_element(By.XPATH, 
                            "./div/div["+str(index)+"]/a").text)
                        continue
                    elif index == 6:
                        vm_details.append(elem.find_element(By.XPATH, 
                            "./div/div["+str(index)+"]/div").text)
                        continue
                    vm_details.append(elem.find_element(By.XPATH, 
                        "./div/div["+str(index)+"]/span").text)
                vms[key] = vm_details
            if self.__admin_console.cv_table_next_button_exists():
                if self.__admin_console.driver.find_element(By.XPATH, 
                        "//button[@ng-disabled='cantPageForward()']").is_enabled():
                    self.__admin_console.cv_table_click_next_button()
                    self.__admin_console.wait_for_completion()
                    continue
                else:
                    break
            else:
                break
        self.__admin_console.log.info("The list of backed up VMs owned by the user is %s", str(vms))
        return vms

    @PageService()
    def action_remove_vm(self, vm_name):
        """
        Removes the VM from the list of backed up VMs

        Args:
            vm_name  (str):  the name of the VM to remove

        """
        self.__table.access_action_item(vm_name, "Do not back up")
        self.__admin_console.click_button('No')

    @PageService()
    def action_vm_jobs(self, vm_name):
        """
        Displays all the jobs of the given VM

        Args:
            vm_name  (str):  the name of the VM whose jobs to open

        """
        self.__table.access_action_item(vm_name, "View jobs")

    @PageService()
    def action_vm_backup(self, vm_name):
        """
        Backups the given VM

        Args:
            vm_name  (str):      the name of the VM to backup

        Returns:
            job_id  (int):  the backup job ID

        """
        self.__table.access_action_item(vm_name, "Back up")
        backup = Backup(self.__admin_console)
        return backup.submit_backup(backup.BackupType.INCR)

    @PageService()
    def action_vm_restore(self, vm_name):
        """
        Restores the given VM

        Args:
            vm_name  (str):  the name of the VM to restore

        """
        self.__table.access_action_item(vm_name, "Restore")

    @PageService()
    def action_list_mounts(self, vm_name):
        """
        Opens Active mounts page for vm

        Args:
            vm_name  (str):  the name of the VM to restore

        """
        self.__table.access_action_item(vm_name, "View active mounts")

    @PageService()
    def delete_active_live_mount(self, mount_name):
        """
        Deletes active live mount from Active Mounts Page
        Args:
             mount_name: (str) VM Mount Name to be deleted
        :returns
            bool: True/False

        """
        mounts = self.__table.get_column_data('Name')
        self.__admin_console.log.info(f"Active Mounts: {mounts}")
        for i in mounts:
            if mount_name in i:
                self.__table.access_action_item(i, 'Delete')
                my_dialog = ModalDialog(self.__admin_console)
                my_dialog.click_submit()
                self.__admin_console.wait_for_completion()
                self.__admin_console.log.info(f"Successfully deleted {i}")
                return True
        self.__admin_console.log.info("Unable to find active mount")
        return False

    @PageService()
    def action_list_snapshots(self, vm_name):
        """
        list the snaps of particular vm at VM's level
        Args:
            vm_name  (str):  the name of the Particular VM for list of snapshots

        """
        self.__table.access_action_item(vm_name, "List snapshots")



