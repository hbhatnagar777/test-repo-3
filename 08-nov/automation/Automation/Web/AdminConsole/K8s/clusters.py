# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods to perform actions on k8s clusters.

Clusters  --  This class contains methods to perform actions on k8s clusters like
              opening a cluster, restore, view jobs, Retire etc.

    Functions:

    add_cluster()               --  add clusters

    open_cluster()              --  Opens cluster with the given name

    action_retire()             --  Retire the k8s cluster

    action_view_jobs()          --  Displays all the jobs of the given cluster

    action_restore()            --  Restores the given cluster

    action_change_company()     --  Change company

    run_validate_backup()       --  Runs backup validation job

    add_k8s_cluster(self)       --  Add kubernetes clusters

    is_cluster_exists()         --  Check if cluster exists

    delete_cluster_name()       --  Delete clusters

    access_cluster_tab()        --  Access cluster tab

    access_application_group_tab()    --  Access application groups tab

    access_application_tab()    --  Access cluster tab

    access_application_group_tab()    --  Access  kubernetes application group tab

AddK8sCluster:

    set_hostname()              -- set api server endpoint

    set_servername()            --  set server name

    set_authentication()        --  set authentication type

    set_service_account()       -- set service account

    set_service_token()         -- set service token

    set_access_nodes()          -- select access nodes

    save()                      -- click save button on add cluster screen

    next()                      -- Click next button

    cancel()                    -- Click on Cancel button

"""

from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService


class K8sClusters:
    """
     This class contains methods to perform actions on k8s clusters like restore,
     view jobs, Retire...
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._admin_console.load_properties(self, unique=True)
        self.__table = Rtable(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__alert = Alert(admin_console)

    @PageService()
    def add_cluster(self):
        """
        Selects Add Cluster
        """
        # local message only have "Add clusters"
        if self.__page_container.check_if_page_action_item_exists(
                self._admin_console.props['K8sClusters']['pageHeader.addHypervisor']
        ):
            self.__page_container.access_page_action(
                self._admin_console.props['K8sClusters']['pageHeader.addHypervisor']
            )

    @PageService()
    def open_cluster(self, cluster_name):
        """
        Opens clusters with the given name

        Args:
            cluster_name     (str):   name of the cluster to open

        """
        if self.is_cluster_exists(cluster_name):
            self.__table.access_link(cluster_name)
        else:
            raise CVWebAutomationException(f"Cluster with name [{cluster_name}] does not exist")

    @PageService()
    def action_view_jobs(self, cluster_name):
        """
        Displays all the jobs of the given cluster

        Args:
            cluster_name  (str):  the name of the cluster whose jobs to open

        """
        self.__table.access_action_item(cluster_name, self._admin_console.props['action.jobs'])

    @PageService()
    def action_restore(self, cluster_name):
        """
        Restores the given cluster

        Args:
            cluster_name  (str):  the name of the cluster to restore

        """
        self.__table.access_action_item(cluster_name, self._admin_console.props['label.restore'])

    @PageService()
    def action_change_company(self, cluster_name):
        """
        Restores the given cluster

        Args:
            cluster_name  (str):  the name of the cluster to restore

        """
        self.__table.access_action_item(cluster_name, self._admin_console.props['action.commonAction.changeCompany'])

    @PageService()
    def add_k8s_cluster(self):
        """Add kubernetes cluster"""
        self.add_cluster()
        return AddK8sCluster(self._admin_console)

    @PageService()
    def is_cluster_exists(self, server_name):
        """Check if cluster exists"""
        self.__table.reload_data()
        return self.__table.is_entity_present_in_column(self._admin_console.props['label.name'], server_name)

    @PageService()
    def delete_cluster_name(self, cluster_name):
        """Delete clusters
        Args:
            cluster_name     (String)       --     cluster name
        """
        if not self.is_cluster_exists(cluster_name):
            raise CVWebAutomationException(f"Cluster with name [{cluster_name}] does not exists to delete")
        try:
            self.__table.access_action_item(cluster_name, self._admin_console.props['action.retire'])
            prop_txt = 'action.retire'
        except Exception:
            self.__table.access_action_item(cluster_name, self._admin_console.props['action.delete'])
            prop_txt = 'action.delete'
        self._admin_console.fill_form_by_id("confirmText", self._admin_console.props[prop_txt].upper())
        self._admin_console.click_button_using_text(self._admin_console.props[prop_txt])
        self._admin_console.wait_for_completion()
        self.__alert.close_popup()

        if self.is_cluster_exists(cluster_name):
            self.__table.access_action_item(cluster_name, self._admin_console.props['action.delete'])
            self._admin_console.fill_form_by_id("confirmText", self._admin_console.props['action.delete'].upper())
            self._admin_console.click_button_using_text(self._admin_console.props['action.delete'])
            self._admin_console.wait_for_completion()
            self.__alert.close_popup()

    @PageService()
    def access_cluster_tab(self):
        """
        Access cluster tab
        """
        self.__page_container.select_tab(self._admin_console.props['label.nav.clusters'])

    @PageService()
    def access_application_group_tab(self):
        """
        Access application group tab
        """
        self.__page_container.select_tab(self._admin_console.props['label.nav.applicationGroups'])

    @PageService()
    def access_applications_tab(self):
        """
        Access applications tab
        """
        self.__page_container.select_tab(self._admin_console.props['label.nav.applications'])


class AddK8sCluster:
    """Add k8s cluster"""

    def __init__(self, admin_console):
        self.__wizard = Wizard(admin_console)
        self._admin_console = admin_console

    @PageService(react_frame=True)
    def set_hostname(self, api_server_endpoint):
        """
        Set api server endpoint
        Args:
            api_server_endpoint   (String)      -- Set API server endpoint (hostname)
        """
        self.__wizard.fill_text_in_field(id='clusterEndPoint', text=api_server_endpoint)

    @PageService()
    def set_servername(self, server_name):
        """
        Set server name
        Args:
            server_name        (String)      -- Set k8s cluster server name
        """
        self.__wizard.fill_text_in_field(id='name', text=server_name)

    @PageService()
    def select_authentication(self, authentication_type):
        """Select Authentication type
        Args:
            authentication_type      (String)       -- Set Authentication type
        """
        self.__wizard.select_drop_down_values(
            id="authType",
            values=[authentication_type]
        )

    @PageService()
    def set_service_account(self, serviceaccount):
        """Set service account
        Args:
            serviceaccount             (String)         --     service account
        """
        self.__wizard.fill_text_in_field(id='authKey', text=serviceaccount)

    @PageService()
    def set_service_token(self, servicetoken):
        """Set service token
        Args:
            servicetoken            (String)         --     service token
        """
        self.__wizard.fill_text_in_field(id='authValue', text=servicetoken)

    @PageService()
    def select_access_nodes(self, access_node):
        """Select access node
        Args:
            access_node      (String)       -- Set access nodes
        """
        if type(access_node) is str:
            access_node = [access_node]
        self.__wizard.select_drop_down_values(
            id="accessNodeDropdown",
            values=access_node
        )

    @PageService()
    def save(self):
        """Click save"""
        self.__wizard.click_button(self._admin_console.props['action.save'])
        self._admin_console.wait_for_completion()

    @PageService()
    def next(self):
        """Click next"""
        self.__wizard.click_next()
        self._admin_console.wait_for_completion()

    @PageService()
    def cancel(self):
        """Click cancel"""
        self.__wizard.click_cancel()
        self._admin_console.wait_for_completion()
