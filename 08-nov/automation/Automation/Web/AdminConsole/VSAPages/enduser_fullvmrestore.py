# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods for submitting full vm restore for all hypervisors

Classes:

    EndUserFullVMRestore() --- > _Navigator() ---> AdminConsoleBase() ---> Object()

FullVMRestore --  This class contains methods for submitting full vm restore.

Functions:

    enduser_full_vm_restore       --  Submits a VMware full VM restore as end user
    #end user               -- User having permissions only at the VM level


"""

from Web.AdminConsole.Components.panel import RPanelInfo as PanelInfo
from Web.Common.page_object import PageService
from Web.AdminConsole.VSAPages.full_vm_restore import FullVMRestore


class EndUserFullVMRestore:
    """
    This class contains methods for submitting full vm restore.
    """

    def __init__(self, admin_console):
        """ Init for FullVMRestore class"""
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__panel_info_obj = PanelInfo(admin_console)
        self._full_vm_restore = FullVMRestore(admin_console)

    @PageService()
    def enduser_full_vm_restore(
            self,
            vm_to_restore,
            inplace=False,
            power_on=True,
            over_write=True,
            restore_prefix=""
    ):
        """
        Submits full VM restore as vm end user

        Args:

            vm_to_restore:                   --  VM thats need to be restored

            inplace                  (bool)  --  if the VM needs to be restored in place

            power_on                 (bool)  --  if the restored VM needs to be powered on

            over_write               (bool)  --  if the restored VM needs to be overwritten

            restore_prefix:                  --  prefix word to keep before the restored VM


        Returns:
            job_id      (str)   --  the restore job ID

        """
        self.__admin_console.wait_for_completion()
        self.__admin_console.log.info("performing end user Full VM restore")
        from VirtualServer.VSAUtils.OptionsHelper import VMwareWebRestoreOptions
        vmware_options = VMwareWebRestoreOptions()
        vmware_options.vm_info = {
            vm_to_restore: {
                'name': vm_to_restore
            }
        }
        vmware_options.end_user = True
        if inplace:
            vmware_options.restore_type = 'In place'
        else:
            vmware_options.restore_type = 'Out of place'
            vmware_options.prefix = restore_prefix

        vmware_options.power_on_after_restore = power_on
        vmware_options.unconditional_overwrite = over_write

        restore_job_id = self._full_vm_restore.submit_restore_from_react_screen(restore_options=vmware_options)
        return restore_job_id
