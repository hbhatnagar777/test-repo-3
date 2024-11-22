# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This is a protected module which has classes to implement migration to cloud feature.

Importing this module directly to the Test case file is strictly prohibited.

Please refer to the corresponding instance class in db_instances.py file which makes use of this module"""

from abc import abstractmethod

from Web.AdminConsole.Components.panel import ModalPanel, DropDown
from Web.AdminConsole.Components.table import CVTable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import PageService


class MigrateToCloud(ModalPanel):

    @abstractmethod
    def __init__(self, admin_console):
        super().__init__(admin_console)
        vendor = DropDown(admin_console)
        vendor.select_drop_down_values(0, [self.cloud_type])

    @property
    @abstractmethod
    def cloud_type(self):
        raise NotImplementedError


class _ComputeNodeConfigurationAzure(ModalPanel):

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self._admin_console = admin_console
        self.name1 = "Compute node configuration"
        self.drop_down = DropDown(self._admin_console)

    @PageService()
    def set_vm_name(self, vm_name):
        """Sets VM Name

        Args:
            vm_name (str):  Name of the VM

        """
        self._expand_accordion_if_not_visible("newVmName", self.name1)
        self._admin_console.fill_form_by_id("newVmName", vm_name)

    @PageService()
    def set_username(self, username):
        """Sets username

        Args:
            username (str): Name of the user

        """
        self._expand_accordion_if_not_visible("username", self.name1)
        self._admin_console.fill_form_by_id("username", username)

    @PageService()
    def set_password(self, password):
        """Sets  password

        Args:
            password (str):  password value

        """
        self._expand_accordion_if_not_visible("password", self.name1)
        self._admin_console.fill_form_by_id("password", password)

    @PageService()
    def set_confirm_password(self, password):
        """Sets confirm password

        Args:
            password (str):  password value

        """
        self._expand_accordion_if_not_visible("confirmPassword", self.name1)
        self._admin_console.fill_form_by_id("confirmPassword", password)

    @PageService()
    def set_recovery_target(self, recovery_target_name):
        """Sets the recovery target

        Args:
            recovery_target_name (str): Name of the recovery target

        """
        self._expand_accordion_if_not_visible("AllocPolicyId", self.name1)
        self.drop_down.select_drop_down_values(1, [recovery_target_name])

    @PageService()
    def set_template(self, template_name):
        """Sets the VM Template

        Args:
            template_name (str):  Name of the template

        """
        self._expand_accordion_if_not_visible("amiName", self.name1)
        self.drop_down.select_drop_down_values(2, [template_name])

    @PageService()
    def set_size(self, size):
        """Sets the VM Size

        Args:
            size (str): Name of the VM size

        """
        self._expand_accordion_if_not_visible("instanceType", self.name1)
        template = DropDown(self._admin_console)
        template.select_drop_down_values(3, [size])


class _NetworkRouteConfigurationAzure(ModalPanel):

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self._admin_console = admin_console
        self.name2 = "Network route configuration"

    @PageService()
    def set_proxy(self, client_name):
        """Sets the proxy

        Args:
            client_name (str): Name of the proxy client

        """
        self._expand_accordion_if_not_visible("enableFirewall", self.name2)
        self._admin_console.select_radio("throughProxy")
        self._admin_console.select_value_from_dropdown(
            'proxyClient', client_name, check_sort=False)


class _ContentSelection(ModalPanel):

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self._admin_console = admin_console
        self.db_list = None
        self.name3 = "Content selection"

    def select_databases(self, databases):
        self.db_list = CVTable(self._admin_console)
        self.db_list.de_select_all_values_from_table()
        self.db_list.select_values_from_table(databases)


class _MigrateToAzure(MigrateToCloud, _ComputeNodeConfigurationAzure, _NetworkRouteConfigurationAzure):

    def __init__(self, admin_console: AdminConsole):
        super().__init__(admin_console)
        _ComputeNodeConfigurationAzure.__init__(self, admin_console)
        _NetworkRouteConfigurationAzure.__init__(self, admin_console)

    @property
    def cloud_type(self):
        return "Azure"


class MigrateSQLToAzure(_MigrateToAzure, _ContentSelection):
    pass


class MigrateOracleToAzure(_MigrateToAzure):
    pass
