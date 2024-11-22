# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that are common to Snap FS
"""

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RModalPanel, RPanelInfo, RDropDown


class SnapUtils:
    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.admin_console = admin_console

    @PageService()
    def mount_multiple_snap(self,
                            jobid: str,
                            mount_path: str,
                            copy_name: str,
                            plan_name: str,
                            clientname: str,
                            ) -> str:
        """
            Args:
                jobid (str) : jobid
                mount_path(str) : mount path
                copy_name(str) : copy name
                plan_name(str) : plan name
                clientname(str) : client name

            Returns:
                Mount_job_id : jobid of multiple mount snaps

            Note: Mounting multiple snaps at Subclient level with same jobid (if subclient has subclientcontent from Different volumes)
        """
        self.__rtable.search_for(jobid)
        if plan_name and copy_name:
            sp_copy = "{}/{}".format(plan_name, copy_name)
        else:
            sp_copy = ""
        self.__rtable.apply_filter_over_column(column_name="Plan/Copy", filter_term=sp_copy)
        self.__rtable.select_all_rows()
        self.__rtable.access_toolbar_menu("Mount")
        self.__rdropdown.select_drop_down_values(values=[clientname], drop_down_id='availableMediaAgents')
        self.admin_console.fill_form_by_id("destPath", mount_path)
        self.__rmodal_dialog.click_submit(wait=False)
        self.admin_console.click_button_using_text('Yes')
        mount_job_id = self.admin_console.get_jobid_from_popup()
        return mount_job_id

    def revert_snap(self, job_id: str) -> str:
        """
        Args:
            job_id(str) : job id of snap
        return:
            jobid: jobid of revert operation

        Note: if you have multiple volumes snap with same job id which occurs at subclient content has muliptle volumes
        locations then this revert will Reverts all the volumes.
        """
        self.__rtable.apply_filter_over_column(column_name="Job ID", filter_term=job_id)
        self.__rtable.select_all_rows()
        self.__rtable.access_toolbar_menu("Hardware revert")
        self.__rmodal_dialog.click_submit(wait=False)
        jobid = self.admin_console.get_jobid_from_popup()
        return jobid