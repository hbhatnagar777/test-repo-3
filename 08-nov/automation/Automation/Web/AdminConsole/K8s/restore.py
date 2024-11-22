from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.wizard import Wizard

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This file has classes and functions to interact with Kubernetes restore pages

KubernetesRestore:

    enable_notify_via_email()           --      Enable the checkbox for notify via email

    enable_unconditional_overwrite()    --      Enable toggle for unconditional overwrite

    select_for_restore()                --      Select apps for restore

    select_restore()                    --      Click on the restore button in table header

    select_restore_destination_type()   --      Select inplace or out of place

    select_restore_type()               --      Select the restore type from screen

    submit_restore()                    --      Click on Restore button in dialog to submit restore

FullAppRestore:

    enter_application_name()            --      Enter the restore name application in input box

    enter_restore_namespace()           --      Select restore namespace from dropdown, or enter manually

    select_access_node()                --      Select access node for restore

    select_app_from_restore_list()      --      Select application from the restore list in restore panel

    select_destination_cluster()        --      Select destination cluster form dropdown

    select_storage_class()              --      Select storage class from dropdown

ManifestRestore:

    enter_destination_path()            --      Enter the destination path for restore

    select_destination_client()         --      Select the client as restore destination

NamespaceRestore:

    add_storage_class_mapping()         --      Add storage class mappings

FSDestinationRestore:

    access_fs_destination_tab()         --      Select the FS Destination tab in dialog

ApplicationFileRestore:

    browse_and_select()                 --      Browse the folder structure and select the folder or file

    enter_destination_path()            --      Enter the destination path in the input box

    enter_password()                    --      Enter password in impersonate user details

    enter_username()                    --      Enter username in impersonate user details

    select_access_node()                --      Select access nodes from the dropdown

    select_destination_cluster()        --      Select destination cluster from the dropdown

"""
from enum import Enum

from Web.AdminConsole.Components.browse import ContentBrowse, Browse, RBrowse, RContentBrowse
from Web.AdminConsole.Components.dialog import RModalDialog, ModalDialog
from Web.AdminConsole.Components.panel import ModalPanel, DropDown
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.K8s.RestoreScreens.Destination import Destination
from Web.AdminConsole.K8s.RestoreScreens.Applications import Applications
from Web.AdminConsole.K8s.RestoreScreens.RestoreOptions import RestoreOptions
from Web.AdminConsole.K8s.RestoreScreens.Summary import Summary
from Web.AdminConsole.K8s.RestoreScreens.Namespaces import Namespaces


class KubernetesRestore:
    """Restore operations"""

    class RestoreType(Enum):
        """ type of backup to submit """
        FULL_APPLICATION = "Full application"
        APPLICATION_MANIFEST = "Application manifests"
        APPLICATION_FILES = "Application files"
        NAMESPACE_LEVEL = "Namespace and cluster level"
        FILE_SYSTEM_DESTINATION = "Application files"

    def __init__(self, admin_console, restore_type):
        """Initialize class variables

            Args:

                admin_console       (obj)           --  Admin console object

                restore_type        (RestoreType)   --  Enum for restore type to initialize based on type
        """
        self.__restore_type = restore_type
        self.admin_console = admin_console
        self._panel = ModalPanel(admin_console)
        self._browse = RContentBrowse(admin_console)
        # self._restore_browse = Browse(admin_console)
        self._restore_browse = RBrowse(admin_console)
        self._dropdown = DropDown(admin_console)
        self._modal = RModalDialog(admin_console)
        self.admin_console.load_properties(self)

    @WebAction()
    def __click_restore_type(self):
        """
        Selects the Restore type"""

        restore_option_xp = (f"//h2[contains(text(),'{self.__restore_type.value}')]/ancestor::div[contains(@class, "
                             f"'tile-content-wrapper')]")
        if self.admin_console.check_if_entity_exists(entity_name="xpath", entity_value=restore_option_xp):
            self.admin_console.click_by_xpath(restore_option_xp)
        else:
            raise CVWebAutomationException(f"Restore type [{self.__restore_type.value}] is not available as option")

    @PageService()
    def _confirm_override_options(self):
        """Click on Yes for override options dialog box"""

        if self.admin_console.check_if_entity_exists(
                entity_name="xpath",
                entity_value="//div[contains(@class, 'modal-content')]/div[contains(@class, 'modal-header')]" +
                             f"/h4[contains(text(), '{self.admin_console.props['label.overrideOptions']}')]"
        ):
            self._modal.click_submit()

    @PageService()
    def select_restore_type(self):
        """Select the restore type"""
        self.__click_restore_type()

    @PageService()
    def get_application_list(self, column_name=None):
        """Fetches list of all applications available"""

        app_list = self._restore_browse.get_column_data(column_name=column_name)
        return app_list

    @PageService()
    def select_for_restore(self, path, selection=None, use_tree=True):
        """Select the table rows based on column values

            Args:

                path            (str)   --
                selection       (list)  --  List of values in rows to select from column
                                            Select all if None
                use_tree        (bool)  --  True conducts tree search
         """
        self._restore_browse.select_path_for_restore(path=path, file_folders=selection, use_tree=use_tree)

    @PageService()
    def select_restore(self):
        """Select the restore button from table header"""
        self._restore_browse.submit_for_restore()

    @PageService()
    def select_restore_destination_type(self, in_place=True):
        """Select in-place or out of place radio buttons

            Args:

                in_place        (bool)  --  Select in-place radio button, else out-of-place
        """
        if in_place:
            self.admin_console.select_radio(id='inPlaceRadio')
        else:
            self.admin_console.select_radio(id='outOfPlaceRadio')

    @PageService()
    def enable_unconditional_overwrite(self):
        """Check unconditional overwrite toggle"""
        self._modal.enable_toggle(self.admin_console.props['warning.overwrite'], preceding_label=True)
        self._modal.click_submit()

    @PageService()
    def submit_restore(self):
        """Click on submit button in modal"""
        self.admin_console.submit_form()

    @PageService()
    def enable_notify_via_email(self):
        """Enable checkbox for email notification"""
        # To be implemented
        pass


class FullAppRestore(KubernetesRestore):

    def __init__(self, admin_console, restore_type=KubernetesRestore.RestoreType.FULL_APPLICATION):
        """Initialize class variables"""
        super(FullAppRestore, self).__init__(admin_console, restore_type=restore_type)
        self.__wizard = Wizard(admin_console)

    @WebAction()
    def __click_li_item(self, link_text):
        """Click link in li item

            Args:

                link_text    (str)   --  Link text to select
        """
        ul_xpath = "//ul[contains(@class, 'vm-full-restore-list')]"
        link_xpath = ul_xpath + f"/li/a[contains(text(), '{link_text}')]"
        self.admin_console.click_by_xpath(link_xpath)

    @WebAction()
    def __toggle_namespace_if_present(self):
        """Enable toggle for namespace if it is present"""
        if self.admin_console.check_if_entity_exists(
                entity_name="id",
                entity_value="vmFullRestoreKubernetes_namespace"
        ):
            toggle_element = self.admin_console.driver.find_element(By.ID, "vmFullRestoreKubernetes_namespace")
            toggle_label = toggle_element.text
            self._modal.enable_toggle(toggle_label, preceding_label=True)

    @PageService()
    def select_destination(self, destination_cluster, access_node='Automatic', inplace=False):
        """
            Fills up fields of destination step of restore wizard
            1. Fills In Place/Out of place radio button
            2. Selects Destination cluster if applicable
            3. Selects Access Node

            args:

                access_node             (str)   --  Access nodes to select. If None, Automatic is selected

                destination_cluster     (str)   --  Destination cluster

                inplace                (bool)  --  ip/oop restore. Default in place

        """

        Destination(
            wizard=self.__wizard,
            inplace=inplace,
            destination_cluster=destination_cluster,
            access_node=access_node
        )

    @PageService()
    def confirm_applications(self, app_info, inplace=False, application_list=None):

        """
        Fills up fields of Application step of restore wizard

        Args:
            app_info            (dict)      dictionary of applications and associated modifications
                                            {app_name:{new_name: ...
                                                       new_namespace: ...
                                                       new_sc: ...
                                                      }
                                            }

            inplace         (bool)      ip/oop restore

            application_list    (list)      list of applications to restore


        """

        if not application_list:
            application_list = []

        Applications(
            wizard=self.__wizard,
            admin_console=self.admin_console,
            inplace=inplace,
            application_list=application_list,
            app_info=app_info
        )

    @PageService()
    def select_restore_options(
            self,
            inplace=False,
            unconditional_overwrite=False,
            source_modifier=True,
            modifier_list=None
    ):

        """
        Fills up fields in restore options section of restore wizard

        Args:

            inplace         (bool)      ip/oop restore
            unconditional_overwrite     (bool)      choose to overwrite app at destination
            source_modifier         (bool)          choose to use source modifiers
            modifier_list           (list)          list of modifiers to apply
        """

        if not modifier_list:
            modifier_list = []

        RestoreOptions(
            wizard=self.__wizard,
            admin_console=self.admin_console,
            inplace=inplace,
            unconditional_overwrite=unconditional_overwrite,
            source_modifier=source_modifier,
            modifier_list=modifier_list
        )

    @PageService()
    def validate_summary(self):

        """
        Summary step
        """

        Summary(
            wizard=self.__wizard,
            admin_console=self.admin_console
        )


    @PageService()
    def select_access_node(self, access_node="Automatic"):
        """Select access node from dropdown

            Args:

                access_node     (str)   --  Access node to select
                                            If None, then Automatic is selected
        """
        self.admin_console.select_value_from_dropdown(select_id="destinationProxy", value=access_node)

    @PageService()
    def select_destination_cluster(self, cluster_name=None):
        """Select destination cluster from dropdown if name is passed

            Args:

                cluster_name        (str)   --  Name of the destination cluster
        """
        self.admin_console.select_value_from_dropdown(select_id="serverId", value=cluster_name)

    @PageService()
    def enter_application_name(self, name=None):
        """Input the application name in restore application name field

            Args:

                name        (str)   --  Name to enter
        """
        if name:
            self.admin_console.fill_form_by_id(element_id="displayName", value=name)

    @PageService()
    def enter_restore_namespace(self, namespace):
        """Select the target namespace

            Args:

                namespace       (str)   --  Select the target namespace for restore
        """

        if not namespace:
            self.admin_console.log.info("No restore namespace is provided, skipping selection from dropdown")
            return

        try:
            self.admin_console.select_value_from_dropdown(select_id="projects", value=namespace)
            self._confirm_override_options()
        except CVWebAutomationException as exp:
            self.admin_console.log.info(exp)
            self.__toggle_namespace_if_present()
            self._confirm_override_options()
            self.admin_console.fill_form_by_id(element_id="manualNamespaceInput", value=namespace)

    @PageService()
    def select_storage_class(self, storage_class=None):
        """Select storage class from dropdown"""

        if not storage_class:
            self.admin_console.log.info("No target storage class is provided, skipping selection from dropdown")
            return

        self.admin_console.select_value_from_dropdown(select_id="storageClass", value=storage_class)
        self._confirm_override_options()

    @PageService()
    def select_destination_modifiers(self):
        """Select the destination modifier checkbox"""

        self.admin_console.select_radio(value='1')

    @PageService()
    def select_advanced_options(self):
        """Expand the accordian"""

        self.admin_console.expand_cvaccordion(label='label.advanced.options')

    @PageService()
    def select_restore_modifiers(self, modifier_list=None, ):
        """Select the restore modifiers on cluster to use"""

        if not modifier_list:
            self.admin_console.log.info("NO restore modifier list provided, skipping selection from dropdown")
            return
        self._dropdown.select_drop_down_values(
            drop_down_id="modifiersToBeAppliedDropDown",
            values=modifier_list,
            partial_selection=True
        )

    @PageService()
    def select_app_from_restore_list(self, application_name):
        """Select application link from restore list

            Args:

                application_name        (str)   --  Name of the application to select
        """
        try:
            self.__click_li_item(link_text=application_name)
        except Exception:
            raise CVWebAutomationException(f"Application [{application_name}] not found in list")


class NamespaceRestore(FullAppRestore):

    def __init__(self, admin_console):
        super(NamespaceRestore, self).__init__(
            admin_console, restore_type=KubernetesRestore.RestoreType.NAMESPACE_LEVEL
        )
        self.__wizard = Wizard(admin_console)

    @WebAction()
    def __click_add_storage_class_map(self):
        """Click on Add hyperlink for storage class mapping"""
        self.admin_console.select_hyperlink(link_text=self.admin_console.props['label.add'])

    @PageService()
    def add_storage_class_mapping(self, storage_class_map):
        """Add mapping for storage class

            Args:

                storage_class_map       (dict)   -  Dictionary with storage class mappings
        """

        for source_sc, destination_sc in storage_class_map.items():
            self.__click_add_storage_class_map()
            self._dropdown.select_drop_down_values(
                drop_down_id="addStorageMappingsModal_isteven-multi-select_#0160", values=[source_sc]
            )
            self._dropdown.select_drop_down_values(
                drop_down_id="addStorageMappingsModal_isteven-multi-select_#9141", values=[destination_sc]
            )
            self._modal.click_submit()

    @PageService()
    def confirm_namespaces(self, namespace_list, namespace_info, inplace=False,):
        """
        Confirms namespaces, in case of OOP restore it also provides functionality
        to rename the application and add a storage class mapping

        Args:

            namespace_info  (dict)      dictionary of namespaces
                                            {namespace: {new_name:
                                            storage_class_mapping: {mapping}
                                            }
                                            }
            inplace:        (bool)      ip/oop restore
            namespace_list  (list)      list of namespaces to restore
            namespace_info  (dict)      dictionary of namespaces
                                            {namespace: {new_name:
                                            sc_mapping: {mapping}
                                            }
                                            }



        """

        Namespaces(
            wizard=self.__wizard,
            admin_console=self.admin_console,
            namespace_info=namespace_info,
            inplace=inplace,
            namespace_list=namespace_list
        )


class ApplicationFileRestore(KubernetesRestore):

    def __init__(self, admin_console, restore_type=KubernetesRestore.RestoreType.APPLICATION_FILES):
        super(ApplicationFileRestore, self).__init__(admin_console, restore_type=restore_type)

    @WebAction()
    def _click_browse_button(self):
        """Click browse button in restore panel"""
        self.admin_console.click_button_using_text(value=self.admin_console.props['label.browse'])

    @PageService()
    def browse_and_select(self, path):
        """Browse and select from browse panel

            Args:

                path        (str)   --  Path to select from browse panel
        """
        self._click_browse_button()

        browse_modal = RModalDialog(
            admin_console=self.admin_console,
            title='Select volume destination')
        self.admin_console.wait_for_completion()
        self._browse.select_path(path=path)
        browse_modal.click_button_on_dialog(text='Save')

    def browse_fs_for_restore_path(self, path):

        self._click_browse_button()
        browse_modal = RModalDialog(
            admin_console=self.admin_console,
            title='Select a path')
        self.admin_console.wait_for_completion()
        self._browse.select_path(path=path)
        browse_modal.click_button_on_dialog(text='Save')

    @PageService()
    def run_app_file_restore(self,
                             access_node,
                             destination_namespace,
                             destination_pvc,
                             unconditional_overwrite=False,
                             inplace=True,
                             destination_cluster=None,
                             path=None
                             ):

        """Fills up the modal for application file restore

            Args:

                unconditional_overwrite     (bool)      enable overwrite

                inplace                     (bool)      restore IP/OOP

                access_node                 (str)       access node to restore to

                destination_cluster         (str)       destination cluster to restore to

                path                        (str)       path relative to PVC mount point

                destination_namespace       (str)       where dest PVC exists

                destination_pvc             (Str)       name of dest pvc

        """

        restore_options_dialog = RModalDialog(title='Restore options', admin_console=self.admin_console)
        restore_options_dialog.select_radio_by_id(radio_id='volume-restore')
        restore_options_dialog.select_dropdown_values(drop_down_id='accessNodeDropdown', values=[access_node])
        if not inplace:
            restore_options_dialog.select_radio_by_id(radio_id='outOfPlaceRadio')
            restore_options_dialog.select_dropdown_values(
                drop_down_id='destinationServer',
                values=[destination_cluster]
            )
            self.browse_and_select(path=f"{destination_namespace}/{destination_pvc}")
            restore_options_dialog.fill_text_in_field(element_id='selectedPath', text=path)

        if unconditional_overwrite:
            restore_options_dialog.enable_toggle(toggle_element_id='overwrite')
            overwrite_dialog = RModalDialog(title='Confirm overwrite option', admin_console=self.admin_console)
            overwrite_dialog.click_button_on_dialog(text='Yes')
        restore_options_dialog.click_submit()


    @PageService()
    def select_access_node(self, client="Automatic"):
        """Select access node from dropdown

            Args:

                client     (str)   --  Destination client to restore to
        """
        self._dropdown.select_drop_down_values(drop_down_id="vmDiskRestore_isteven-multi-select_#4918", values=[client])

    @PageService()
    def enter_username(self, username):
        """Enter username in impersonate user input

            Args:

                username        (str)   --  Username to input
        """
        self.admin_console.fill_form_by_name(name="vmLoginName", value=username)

    @PageService()
    def enter_password(self, password):
        """Enter password in impersonate user input

            Args:

                password        (str)   --  Password to input
        """
        self.admin_console.fill_form_by_name(name="vmPassword", value=password)

    @PageService()
    def enter_destination_path(self, path, browse=False):
        """Enter destination path in Path input

            Args:

                path        (str)   --  Enter destination path in input

                browse      (bool)  --  Browse file system instead of directly entering text in input field
        """
        if not browse:
            self.admin_console.fill_form_by_name(name="path", value=path)
        else:
            self.browse_and_select(path=path)

    @PageService()
    def select_destination_cluster(self, cluster_name=None):
        """Select destination cluster from dropdown if name is passed

            Args:

                cluster_name        (str)   --  Name of the destination cluster
        """
        self._dropdown.select_drop_down_values(
            drop_down_id="vmDiskRestore_isteven-multi-select_#5406", values=[cluster_name]
        )


class ManifestRestore(ApplicationFileRestore):

    def __init__(self, admin_console):
        super(ManifestRestore, self).__init__(
            admin_console, restore_type=KubernetesRestore.RestoreType.APPLICATION_MANIFEST
        )

    @PageService()
    def fill_manifest_restore_modal(self, access_node, path, unconditional_overwrite):
        """
        Fills the Restore options modal for manifest restore

            Args:

                access_node     (str)       --  Destination access node
                path            (str)       --  path on access node
                unconditional_overwrite     (bool)      True=overwrite
        """

        restore_options_dialog = RModalDialog(admin_console=self.admin_console, title='Restore options')
        restore_options_dialog.select_dropdown_values(drop_down_id='restoreVMFilesDropdown', values=[access_node])
        restore_options_dialog.fill_text_in_field(element_id='destinationPath', text=path)
        if unconditional_overwrite:
            restore_options_dialog.enable_toggle(toggle_element_id='overwrite')
            overwrite_dialog = RModalDialog(admin_console=self.admin_console, title='Confirm overwrite option')
            overwrite_dialog.click_button_on_dialog(text='Yes')

        restore_options_dialog.click_submit()


    @PageService()
    def select_destination_client(self, destination_client):
        """Select destination client from dropdown

            Args:

                destination_client     (str)   --  Destination client to restore to
        """
        self._dropdown.select_drop_down_values(
            drop_down_id="vmFileRestore_isteven-multi-select_#2697", values=[destination_client]
        )

    @PageService()
    def enter_destination_path(self, path):
        """Enter destination path in Path input

            Args:

                path        (str)   --  Enter destination path in input
        """
        self.admin_console.fill_form_by_name(name="restorePath", value=path)


class FSDestinationRestore(ApplicationFileRestore):

    def __init__(self, admin_console):
        super(FSDestinationRestore, self).__init__(
            admin_console, restore_type=KubernetesRestore.RestoreType.FILE_SYSTEM_DESTINATION
        )

    def access_fs_destination_tab(self):
        """Click on File System destination tab"""
        self._panel.access_tab(self.admin_console.props['label.fsDestination'])

    def perform_fs_destination_restore(self, access_node: object, path: object, unconditional_overwrite: object) -> object:
        """
        Fills up FS destination restore modal
        """
        restore_options_dialog = RModalDialog(admin_console=self.admin_console, title='Restore options')
        restore_options_dialog.select_radio_by_id(radio_id='fs-destination-restore')
        restore_options_dialog.select_dropdown_values(drop_down_id='accessNodeDropdown', values=[access_node])
        self.browse_fs_for_restore_path(path=path)
        # restore_options_dialog.click_button_on_dialog(text='Browse')
        # browse_dialog = RModalDialog(admin_console=self.admin_console, title='Select a path')
        # tree_xpath = '//div[contains(@class,"mui-modal-dialog mui-modal-centered")]'
        # tree_view = TreeView(admin_console=self.admin_console, xpath=tree_xpath)
        # browse_dialog.wait_for_loader()
        # tree_view.expand_path(path=path.split('/'))
        # browse_dialog.click_submit()
        if unconditional_overwrite:
            restore_options_dialog.enable_toggle(toggle_element_id='overwrite')
            overwrite_dialog = RModalDialog(admin_console=self.admin_console, title='Confirm overwrite option')
            overwrite_dialog.click_button_on_dialog(text='Yes')
        restore_options_dialog.click_submit()







