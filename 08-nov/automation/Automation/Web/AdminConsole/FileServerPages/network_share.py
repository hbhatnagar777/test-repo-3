#!/usr/bin/env python

"""
This module provides all the methods that can be done of the NAS_File_Servers page.


Classes:

    NetworkShare    --  Base Class for Network Share Agents CIFS and NFS.

    CIFS            --  Class for Network Share Agent CIFS.

    NFS             --  Class for Network Share Agent NFS.

"""

from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.content import AddContent


class __NetworkShare(AddContent):

    def __init__(self, admin_console, network_share):
        super().__init__(admin_console)
        self.access_nodes = network_share.get('access_nodes', [])
        self.content = network_share.get('content', None)
        self.drop_down = DropDown(self.admin_console)


class CIFS(__NetworkShare):
    """
    Class for CIFS Network Share agent.

    """

    def __init__(self, admin_console, network_share):
        super().__init__(admin_console, network_share)
        self.impersonate_user = network_share.get('impersonate_user')
        self.admin_console.enable_toggle(index=0)

    @PageService()
    def edit_impersonate_user(self):
        """
        Click on Edit and specify impersonation account details.
        """
        self.admin_console.click_by_xpath("//label[contains(text(),'CIFS credentials')]/..//a")
        self.admin_console.fill_form_by_name("loginName", self.impersonate_user['username'])
        self.admin_console.fill_form_by_name("password", self.impersonate_user['password'])
        self.admin_console.click_button_using_text('OK')

    @PageService()
    def add_access_nodes(self):
        """
        Click on Add and specify access nodes.
        """
        self.drop_down.select_drop_down_values(values=self.access_nodes,
                                               drop_down_id='CIFS-accessnode-selection-dropdown')

    @PageService()
    def edit_content(self):
        """Click and edit content."""
        self.admin_console.click_by_xpath("//li[.='All CIFS shares']/ancestor::div[@class='form-group ng-scope']//a")
        super().edit_content([self.content])
        self.admin_console.click_button_using_text('Save')


class NFS(__NetworkShare):
    """
    Class for NFS Network Share agent.

    """

    def __init__(self, admin_console, network_share):
        super().__init__(admin_console, network_share)
        self.admin_console.enable_toggle(index=1)

    @PageService()
    def add_access_nodes(self):
        """
        Click on Add and specify access nodes.
        """
        self.drop_down.select_drop_down_values(values=self.access_nodes,
                                               drop_down_id='NFS-accessnode-selection-dropdown')

    @PageService()
    def edit_content(self):
        """Click and edit content."""
        self.admin_console.click_by_xpath("//li[.='All NFS exports']/ancestor::div[@class='form-group ng-scope']//a")
        super().edit_content([self.content])
        self.admin_console.click_button_using_text('Save')


class NDMP(__NetworkShare):
    """
    Class for CIFS Network Share agent.

    """

    def __init__(self, admin_console, network_share):
        super().__init__(admin_console, network_share)
        self.impersonate_user = network_share.get('impersonate_user')

    @PageService()
    def edit_impersonate_user(self):
        """
        specify impersonation account details.
        """
        self.admin_console.fill_form_by_name("ndmpLogin", self.impersonate_user['username'])
        self.admin_console.fill_form_by_name("ndmpPassword", self.impersonate_user['password'])

    @PageService()
    def edit_content(self):
        """Click and edit content."""
        self.admin_console.click_by_xpath("//li[.='All Volumes']/ancestor::div[@class='form-group ng-scope']//a")
        super().edit_content([self.content])
        
    @PageService()
    def add_access_nodes(self):
        """
        Click on Add and specify access nodes.
        """
        self.drop_down.select_drop_down_values(values=self.access_nodes,
                                               drop_down_id='NDMP-accessnode-selection-dropdown')
