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
details file has the functions to operate on instance page where we can backup and restore the
instances in Git apps.

Overview:

    backup_now                         --      Initiate backup for the repository group

    edit_general_properties            --      Modify general properties in the instance edit form

    restore_by_job                     --      Triggers restore from the given backup job

    restore_all                        --      Initiate restore by selecting all files/content

    backup_now                         --      Initiate backup for the repository group

    access_backup_history              --      Access backup history of instance/repository group

    access_restore_history             --      Access restore history of the instance

    access_restore                     --      Access restore of the repository group

    access_configuration               --      Access configuration page

    edit_repo_group_content            --      Edits repository group content

    edit_repo_group_azure_services     --      Edits repository group services

    is_repository_group_exists         --      Check if repository group exists

    access_repository_group            --      Access repository group

    add_repository_group               --      Adds repository group

    delete_repository_group            --      Deletes repository group

Configuration:

    access_overview                    --     Access overview page

    enable_backup                      --     Enable backup

    disable_backup                     --     Disable backup

    edit_access_nodes                  --     Method to edit access nodes details

Restore:

    restore_in_place                   --      Starts a restore in place job

    restore_out_of_place               --      Starts a restore out of place job

    restore_to_disk                    --      Starts a restore to disk job
"""
import time

from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.browse import ContentBrowse, Browse, RBrowse
from Web.AdminConsole.Components.panel import Backup, DropDown, RDropDown, PanelInfo, RPanelInfo
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs

from Web.Common.page_object import PageService
from Web.Common.exceptions import CVWebAutomationException
from selenium.common.exceptions import NoSuchElementException


class Overview:
    """
    Overview class has the functions to operate on overview page for a Git App.
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)
        self.__rtable = Rtable(admin_console)
        self.__dropdown = DropDown(admin_console)

    def _edit_app_name(self, app_name):
        """Edits name of app"""
        self._admin_console.fill_form_by_id('cloudStorageName', app_name)

    def _edit_token_name(self, token_name):
        """Edits name of token"""
        self._admin_console.fill_form_by_id('tokenName', token_name)

    def _edit_access_token(self, access_token):
        """Edits Access token"""
        self._admin_console.fill_form_by_id('accessToken', access_token)

    def _edit_staging_path(self, staging_path):
        """Edits Staging path"""
        self._admin_console.fill_form_by_id('stagingPath', staging_path)

    def _edit_impersonate_user(self, impersonate_user):
        """Edits impersonate user information"""
        if impersonate_user:
            username = impersonate_user.get('username')
            password = impersonate_user.get('password')
            if username is not None and password is not None:
                self._admin_console.enable_toggle(0, cv_toggle=True)
                self._admin_console.select_radio(value="MANUAL")
                self._admin_console.fill_form_by_name("loginName", username)
                self._admin_console.fill_form_by_name("password", password)
                self._admin_console.click_button_using_text('OK')

    def _edit_host_url(self, host_url):
        """Edits host url"""
        if host_url != "https://api.github.com":
            self._admin_console.fill_form_by_id('hostURL', host_url)

    def _edit_plan(self, plan):
        """Edits plan"""
        self.__dropdown.select_drop_down_values(drop_down_id="planSummaryDropdown", values=[plan])

    @PageService()
    def edit_general_properties(self, **kwargs):
        """
        Modify general properties in the instance edit form
        Kwargs:
            access_token            (str)   -- personal access token

            plan                    (str)   -- plan name to select

            app_name                (str)   -- name of instance/app

            token_name              (str)   -- token name

            host_url                (str)   -- host url of git server

            staging_path            (str)   -- staging path

            impersonate_user        (dict)  -- impersonation details
                Dictionary contains the keys username and password
                    username    (str)  --   username to be impersonated
                    password    (str)  --   password to be impersonated
                default - False is used for no impersonation
        """
        panel = PanelInfo(self._admin_console, title='General')
        panel.edit_tile()
        for prop in kwargs:
            if kwargs[prop] is not None:
                getattr(self, f"_edit_{prop}")(f"{kwargs[prop]}")
        self._admin_console.click_button('Save')
        self._admin_console.check_error_message()

    @PageService()
    def restore_by_job(self, job_id, repository_group=None):
        """Triggers restore from the given backup job
        Args:
            job_id                  (str)       --    Backup job to be restored
            repository_group        (str)       --    repository group name
                If repository_group is none, uses backup history at app level
        """
        jobs = Jobs(self._admin_console)
        self.access_backup_history(repository_group)
        if jobs.if_job_exists(job_id):
            jobs.access_job_by_id(job_id)
        else:
            jobs.access_active_jobs()
            if not jobs.if_job_exists(job_id):
                raise Exception(f"Job: {job_id} is not present in Active jobs or Job History")
        jobs.initiate_job_based_subclient_restore(job_id)

    @PageService()
    def restore_all(self, path=None):
        """
        Initiate restore by selecting all files/content
        Args:
            path        (str)       --      content path to be selected for restore
        """
        time.sleep(60)
        browse = Browse(self._admin_console)
        if path is None:
            browse.select_for_restore(all_files=True)
        else:
            parent_path, file_to_select = path.rsplit("\\", 1)
            browse.select_path_for_restore(parent_path, [file_to_select])
        browse.submit_for_restore()
        return Restore(self._admin_console)

    @PageService()
    def backup_now(self, repository_group=None, backup_level=Backup.BackupType.FULL):
        """
        Initiate backup for the repository group
        Args:
            repository_group        (str)       --    repository group name
                If repository_group is none, uses default repository group
            backup_level            (str)       --    specify backup level from constant
                                                      present in OverView class
        """
        backup = Backup(self._admin_console)
        self.__table.access_action_item(repository_group or 'default',
                                        self._admin_console.props['label.globalActions.backup'])
        _job_id = backup.submit_backup(backup_level)
        return _job_id

    @PageService()
    def access_backup_history(self, repository_group=None):
        """
        Access backup history of instance or specified repository group
        Args:
            repository_group        (str)       --     repository group name
        """
        if repository_group is None:
            self._admin_console.access_menu("Backup history")
        else:
            self.__table.access_action_item(repository_group, 'Backup history')

    @PageService()
    def access_restore_history(self):
        """Access restore history of the instance"""
        self._admin_console.access_menu_from_dropdown("Restore history")

    @PageService()
    def access_restore(self, repository_group=None):
        """Access restore of the repository group
        Args:
            repository_group        (str)      -- name of the repository group
                If repository_group is none, uses default repository group
        """
        self._admin_console.browser.driver.refresh()
        self._admin_console.wait_for_completion()
        self.__table.access_action_item(repository_group or 'default', 'Restore')

    @PageService()
    def access_configuration(self):
        """Access configuration page"""
        self._admin_console.select_configuration_tab()
        return Configuration(self._admin_console)

    @PageService()
    def access_repository_groups(self):
        """Access Repository groups page"""
        self._admin_console.click_by_id('devOpsDetailsRepoGroups')
        return RepositoryGroups(self._admin_console)

    @PageService()
    def disable_backup(self):
        """Disable backup from overview tab in repository group page"""
        panel = PanelInfo(self._admin_console, title='General')
        panel.disable_toggle("Enable backup")
        self._admin_console.click_button_using_text('Yes')

    def __select_content(self, content=None):
        """Selects given content"""
        if content is not None:
            cbrowse = ContentBrowse(self._admin_console)
            self._admin_console.select_radio(value="selectRepositories")
            add_content_error_xpath = "//*[@class='serverMessage error']"
            if self._admin_console.check_if_entity_exists('xpath', add_content_error_xpath):
                raise Exception(self._admin_console.driver.find_element(By.XPATH, add_content_error_xpath).text)
            all_content_xpath = "//div[@class='browse-item ng-scope'][*]"
            while self._admin_console.driver.find_elements(By.XPATH, all_content_xpath)[0].text.strip() == "Loading...":
                time.sleep(15)
            for item in content:
                cbrowse.select_path(item)
        else:
            self._admin_console.select_radio(value="allRepositories")

    def edit_repo_group_content(self, repository_group, content=None):
        """
        Edits repository group content
        Args:
            repository_group            (str)       --      Name of the repository group
            content                     (list)      --      Projects/Repositories list
                Default - selects all repositories (top level if specified)
        """
        self.access_repository_group(repository_group)
        panel = PanelInfo(self._admin_console, title='Repository')
        panel.edit_tile()
        self._admin_console.click_by_id('toolbar-menu_addRepository')
        self.__select_content(content)
        self._admin_console.click_button_using_text('Save')
        add_content_error_xpath = "//*[@class='serverMessage error']"
        if self._admin_console.check_if_entity_exists('xpath', add_content_error_xpath):
            raise Exception(self._admin_console.driver.find_element(By.XPATH, add_content_error_xpath).text)
        current_content = panel.get_details()
        return True if current_content == content else False

    def edit_repo_group_azure_services(self, repository_group, azure_services):
        """
        Edits repository group services
        Args:
            repository_group            (str)       --      Name of the repository group
            azure_services              (list)      --      list of services(only for azure app)
        """
        self.access_repository_group(repository_group)
        panel = PanelInfo(self._admin_console, title='Azure services')
        panel.edit_tile()
        self.__dropdown.deselect_drop_down_values(0, ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts'])
        self.__dropdown.select_drop_down_values(
            drop_down_id='azureservices_isteven-multi-select_#7659',
            values=azure_services, default_unselect=False)

    @PageService()
    def is_repository_group_exists(self, repository_group='default'):
        """Check if repository group exists
        Args:
            repository_group        (str)   -- name of the repository group
        """
        return self.__table.is_entity_present_in_column('Name', repository_group)

    @PageService()
    def access_repository_group(self, repository_group):
        """Access repository group
        Args:
            repository_group        (str)   -- name of the repository group
        """
        if not self.is_repository_group_exists(repository_group):
            raise Exception(f"Repository group doesn't exist:{repository_group}")
        self.__table.access_link(repository_group)

    @PageService()
    def add_repository_group(self, repository_group, organization_name, azure_services=None,
                             plan_name=None, account_type=None, content=None, fetch_org=False):
        """Adds repository group
        Args:
            repository_group        (str)   -- name of the repository group
            organization_name       (str)   -- name of the organization
            azure_services          (list)  -- list of azure services(only for azure app)
            plan_name               (str)   -- plan name to select
            account_type            (str)   -- account type(only for git app)
            content                 (list)  -- projects or repos to be selected
            fetch_org               (bool)  -- org fetch failure will raise exception
        """
        self._admin_console.select_hyperlink('Add repository group')
        self._admin_console.fill_form_by_id('repositoryGroupName', repository_group)
        dropdown_no = 1
        try:
            self.__dropdown.select_drop_down_values(drop_down_id='addCloudStorageContent_isteven-multi-select_#76360',
                                                    values=[organization_name])
        except Exception as excp:
            if not fetch_org:
                self._admin_console.fill_form_by_id('organizationName', organization_name)
                dropdown_no = 0
            else:
                raise CVWebAutomationException(f"Organization auto fetch failed with {excp}")
        dropdown_id = 'azureservices_isteven-multi-select_#7654'
        if self._admin_console.check_if_entity_exists('id', dropdown_id):
            if azure_services is None:
                azure_services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
            self.__dropdown.deselect_drop_down_values(dropdown_no,
                                                      ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts'])
            self.__dropdown.select_drop_down_values(drop_down_id=dropdown_id, values=azure_services,
                                                    default_unselect=False)
        dropdown_id = "addCloudStorageContent_isteven-multi-select_#6986"
        if self._admin_console.check_if_entity_exists('id', dropdown_id):
            account_type = account_type or "Business/Institution"
            self.__dropdown.select_drop_down_values(drop_down_id=dropdown_id,
                                                    values=[account_type])
        self.__select_content(content)
        if plan_name is not None:
            dropdown = DropDown(self._admin_console)
            dropdown.select_drop_down_values(drop_down_id="planSummaryDropdown",
                                             values=[plan_name])
        self._admin_console.click_button('Save')
        self._admin_console.check_error_message()
        if not self.is_repository_group_exists(repository_group):
            raise CVWebAutomationException(f"Repository group: {repository_group} creation failed")

    @PageService()
    def delete_repository_group(self, repository_group):
        """Deletes repository group
        Args:
            repository_group        (str)   -- name of the repository group
        """
        self._admin_console.browser.driver.refresh()
        self.__table.access_action_item(repository_group, 'Delete')
        self._admin_console.fill_form_by_id("deleteTypedConfirmation", "DELETE")
        self._admin_console.click_button('Delete')
        if self.is_repository_group_exists(repository_group):
            raise CVWebAutomationException(f"Repository group: {repository_group} deletion failed")


class Configuration:
    """
    Configuration class to operate on configuration page for a Git App.
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__dropdown = DropDown(admin_console)
        self.__rdropdown = RDropDown(admin_console)

    @PageService()
    def access_overview(self):
        """Access overview page"""
        self._admin_console.select_overview_tab()
        return Overview(self._admin_console)

    @PageService()
    def access_repository_groups(self):
        """Access Repository groups page"""
        self._admin_console.click_by_id('devOpsDetailsRepoGroups')
        return RepositoryGroups(self._admin_console)

    @PageService()
    def enable_backup(self):
        """Enable backup"""
        panel = PanelInfo(self._admin_console, title='Activity control')
        panel.enable_toggle("Data backup")

    @PageService()
    def disable_backup(self):
        """Disable backup"""
        panel = PanelInfo(self._admin_console, title='Activity control')
        panel.disable_toggle("Data backup")

    @PageService()
    def __get_all_current_access_nodes(self):
        """
        Get all the names of the access nodes present in the 'Access nodes' panel
        Returns : list of names of every access-node configured for the app

        """
        xpath = f"//span[contains(@class, 'MuiCardHeader-title') and normalize-space()='Access nodes']" \
                f"/ancestor::div[contains(@class, 'MuiCard-root')]" \
                "//div[@class='tile-row']//a"
        nodes_list = self._admin_console.driver.find_elements(By.XPATH, xpath)
        current_accessnodes = [tag.text for tag in nodes_list]
        return current_accessnodes

    @PageService()
    def edit_access_nodes(self, access_nodes=None, accessnodes_type=None,
                          staging_path=None, impersonate_user=None):
        """
        Method to edit access nodes, staging path or impersonate user details
        Args:
            access_nodes       (list)  -- list of access nodes to select
            accessnodes_type   (str)   -- type of access nodes to select
            staging_path       (str)   -- staging path
            impersonate_user   (False/dict)  -- impersonation details
                Dictionary contains the keys username and password
                    username   (str)   --   username to be impersonated
                    password   (str)   --   password to be impersonated
                False is passed for disabling impersonation
            None is used by default for not changing existing configuration
        """
        rpanel = RPanelInfo(self._admin_console, "Access nodes")
        current_accessnodes = self.__get_all_current_access_nodes()
        current_accessnodes.sort()
        if len(current_accessnodes) == 1:
            rpanel.edit_tile()
        else:
            rpanel.click_action_item("Edit")
        if access_nodes is not None:
            access_nodes.sort()
            if access_nodes != current_accessnodes:
                if accessnodes_type is not None:
                    if accessnodes_type.lower() == "unix":
                        self._admin_console.select_radio('INCREMENTAL')
                    else:
                        self._admin_console.select_radio('Windows')
                self.__rdropdown.deselect_drop_down_values(current_accessnodes, "accessNode")
                self._admin_console.wait_for_completion()
                self._admin_console.driver.find_element(By.ID, "accessNode").click()
                self.__rdropdown.select_drop_down_values(index=2,
                                                         drop_down_id='accessNode',
                                                         values=access_nodes)
        if staging_path is not None:
            self._admin_console.fill_form_by_id('stagingPath', staging_path)
        if impersonate_user is not None:
            if impersonate_user:
                username = impersonate_user.get('username')
                password = impersonate_user.get('password')
                self._admin_console.enable_toggle(0, cv_toggle=True)
                self._admin_console.fill_form_by_name("userName", username)
                self._admin_console.fill_form_by_name("password", password)
        self._admin_console.click_button('Save')
        if access_nodes is not None:
            if access_nodes != sorted(self.__get_all_current_access_nodes()):
                raise CVWebAutomationException(f"Editing Access nodes failed.")


class RepositoryGroups:
    """
        RepositoryGroups class to operate on Repository Groups page for a Git App.
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__rtable = Rtable(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__treeview = TreeView(admin_console)
        self._wizard = Wizard(admin_console)

    def _select_services(self, services=None):
        """selects the list of services provided in the argument from the dropdown"""
        if services is not None:
            if self._admin_console.check_if_entity_exists('id', 'services'):
                app_name_element = self._admin_console.driver.find_element(By.XPATH,
                                                                           "//label[@id='services-chip-label']")
                app_name = app_name_element.text.split()[0]
                all_services = []
                if 'Azure' in app_name:
                    all_services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
                elif 'GitLab' in app_name:
                    all_services = ['Deployments', 'Issues', 'Snippets', 'Wikis']
                deselect_values = [service for service in all_services if service not in services]
                self.__rdropdown.deselect_drop_down_values(
                    values=deselect_values,
                    drop_down_id="services")

    def _close_toast_alert(self):
        """closes the toast alert receiver after performing a backup"""
        self._admin_console.click_by_xpath(
            "//div[contains(@class, 'toast-wrapper')]//button[@type='button' and @aria-label='Close']")

    @PageService()
    def is_repository_group_exists(self, repository_group='default'):
        """Check if repository group exists
        Args:
            repository_group        (str)   -- name of the repository group
        """
        return self.__rtable.is_entity_present_in_column('Name', repository_group)

    def add_repository_group(self, plan_name, repo_group_name, organization_name, fetch_org=False, services=None,
                             select=None):
        """Adds a new repository group"""
        self.__rtable.select_row_action(0, 'Add repository group')

        self._wizard.select_plan(plan_name)

        self._wizard.click_next()

        self._admin_console.fill_form_by_id('repositoryGroupName', repo_group_name)

        self._wizard.click_next()

        self._select_services(services)

        try:
            self.__rdropdown.select_drop_down_values(drop_down_id='organizationName',
                                                     values=[organization_name])
        except Exception as excp:
            if not fetch_org:
                self._admin_console.fill_form_by_id('organizationName', organization_name)
            else:
                raise CVWebAutomationException(f"Organization auto fetch failed with {excp}")

        if select:
            self._admin_console.click_by_id("select")
            self._admin_console.click_by_xpath("//button[contains(@aria-label, 'Browse')]")
            self._admin_console.wait_for_completion()
            self.__treeview.select_items(select)
            self._admin_console.click_by_id("Save")

        self._wizard.click_submit()

    @PageService()
    def delete_repository_group(self, repository_group):
        """Deletes repository group
        Args:
            repository_group        (str)   -- name of the repository group
        """
        self.__rtable.access_action_item(repository_group, 'Delete')
        self._admin_console.fill_form_by_id("confirmText", "DELETE")
        self._admin_console.click_button('Delete')
        if self.is_repository_group_exists(repository_group):
            raise CVWebAutomationException(f"Repository group: {repository_group} deletion failed")

    def backup_now(self, repository_group='default'):
        self.__rtable.access_action_item(repository_group, 'Backup')
        self._admin_console.click_submit()

        job_id = self._admin_console.get_jobid_from_popup(wait_time=0)

        # self._close_toast_alert()

        return job_id

    @PageService()
    def open_restore_browse(self, repository_group=None):
        """Access restore of the repository group
        Args:
            repository_group        (str)      -- name of the repository group
                If repository_group is none, uses default repository group
        """
        self._admin_console.browser.driver.refresh()
        self._admin_console.wait_for_completion()
        self.__rtable.access_action_item(repository_group or 'default', 'Restore')

    @PageService()
    def restore_all(self, path=None):
        """
        Initiate restore by selecting all files/content
        """
        time.sleep(60)
        rbrowse = RBrowse(self._admin_console)
        if path:
            parent_path, file_to_select = path.rsplit("\\", 1)
            rbrowse.select_path_for_restore(parent_path, [file_to_select])
        else:
            rbrowse.select_files(select_all=True)
        rbrowse.submit_for_restore()
        return Restore(self._admin_console)


class Toolbar:
    """
        Toolbar class operates the three buttons : Backup, Backup history and the more options button
    """

    def __init__(self, admin_conslole):
        self._admin_console = admin_conslole
        self.__rtable = Rtable(admin_conslole)

    def _close_toast_alert(self):
        """closes the toast alert receiver after performing a backup"""
        self._admin_console.click_by_xpath("//div[contains(@class, 'toast-wrapper')]//button[@type='button' and @aria-label='Close']")

    def _is_multi_repo_groups_exists(self):
        """Check if there are multiple repo groups configured for this app in the backup panel"""
        try:
            self._admin_console.driver.find_element(By.ID, "devOpsSubclients")
            return True
        except NoSuchElementException:
            return False

    def backup_now(self, repository_groups=["default"]):

        """
            Performs backup of all the repository group passed in the function and returns the backup job ID
        """

        self._admin_console.click_by_xpath("//button[@id='BACKUP']")
        self._admin_console.wait_for_completion()
        if self._is_multi_repo_groups_exists():
            self.__rtable.select_rows(repository_groups)

        self._admin_console.click_submit()
        self._admin_console.wait_for_completion()

        job_id = self._admin_console.get_jobid_from_popup(wait_time=0)

        # self._close_toast_alert()

        return job_id

    def view_backup_history(self):
        """View the backup history page of a devops app"""
        self._admin_console.click_by_id("BACKUP_HISTORY")
        self._admin_console.wait_for_completion()

    def _click_more_options(self):
        """Clicks on the more option button to view the dropdown"""
        self._admin_console.click_by_xpath("//div[@aria-label='More' and contains(@class, 'anchor-btn')]")
        self._admin_console.wait_for_completion()

    def _click_delete(self):
        """
        Clicks through the delete process on the admin console interface.
        """
        self._click_more_options()
        self._admin_console.click_by_id("DELETE")
        self._admin_console.fill_form_by_id("confirmText", "DELETE")
        self._admin_console.click_by_xpath("//button[@id='Submit']")
        self._admin_console.wait_for_completion()

    def view_restore_history(self):
        """View the restore history page of a devops app"""
        self._click_more_options()
        self._admin_console.click_by_id("RESTORE_HISTORY")
        self._admin_console.wait_for_completion()

    def delete_app(self):
        """Deletes the devops instance"""
        self._click_delete()

    def delete_repository_group(self):
        """
        Clicks through the delete process on the admin console interface.
        """
        self._click_delete()


class Restore:
    """
    Restore class has the functions to start different restores for a Git App.
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__dropdown = DropDown(admin_console)
        self.__rdropdown = RDropDown(admin_console)

    def _select_services(self, services=None):
        """selects the list of services provided in the argument from the dropdown"""
        if services is not None:
            if self._admin_console.check_if_entity_exists('id', 'services'):
                app_name_element = self._admin_console.driver.find_element(By.XPATH,
                                                                           "//label[@id='services-chip-label']")
                app_name = app_name_element.text.split()[0]
                all_services = []
                if app_name == 'Azure':
                    all_services = ['Boards', 'Pipelines', 'Repos', 'Test Plans', 'Artifacts']
                elif app_name == 'GitLab':
                    all_services = ['Deployments', 'Issues', 'Snippets', 'Wikis']
                deselect_values = [service for service in all_services if service not in services]
                self.__rdropdown.deselect_drop_down_values(
                    values=deselect_values,
                    drop_down_id="services")

    @PageService()
    def restore_in_place(self, no_of_streams=None, services=None):
        """
        Starts a restore in place job
        Args:
            no_of_streams            (int)        --      number of streams
            services                 (list)       --      list of services(only for azure app)
        """
        self.__rdropdown.select_drop_down_values(drop_down_id='restoreType', values=['In place'])
        self._admin_console.wait_for_completion()
        self._select_services(services)
        if no_of_streams is not None:
            self._admin_console.wait_for_completion()
            self._admin_console.fill_form_by_id('noOfStreams', no_of_streams)
        self._admin_console.wait_for_completion()
        self._admin_console.click_submit()

    @PageService()
    def restore_out_of_place(self, des_app, organization_name, project_name,
                             account_type=None, no_of_streams=None, services=None):
        """
        Starts a restore out of place job
        Args:
            des_app                  (str)        --      name of destination instance
            organization_name        (str)        --      name of the organization
            project_name  (str)                   --      project name(azure)
            account_type (str)                    --      Type of account (GitHub, GitLab only)
            no_of_streams            (int)        --      number of streams
            services                 (list)       --      list of services(only for azure app)
        """
        self.__rdropdown.select_drop_down_values(drop_down_id='restoreType', values=['Out of place'])
        self.__rdropdown.select_drop_down_values(
            drop_down_id="destinationApp",
            values=[des_app])

        # For Gitlab and GitHub only
        if account_type and account_type in ["Business/Institution", "Personal", "Groups"]:
            self.__rdropdown.select_drop_down_values(
                drop_down_id="accountType",
                values=[account_type])

        # For Azure and GitLab only
        try:
            self._select_services(services)
            self._admin_console.fill_form_by_id('projectName', project_name)
        except NoSuchElementException:
            pass  # Gitlab will not have a projectName field and Github will not have a services field

        org_name_element = self._admin_console.driver.find_element(By.XPATH, "//input[@id='organizationName']")
        if 'disabled' not in org_name_element.get_attribute('outerHTML'):
            self._admin_console.fill_form_by_id("organizationName", organization_name)

        if no_of_streams is not None:
            self._admin_console.fill_form_by_id('noOfStreams', no_of_streams)
        self._admin_console.click_button_using_text(self._admin_console.props['action.submit'])

    @PageService()
    def restore_to_disk(self, des_server, des_path, overwrite=True, no_of_streams=None):
        """
        Starts a restore to disk job
        Args:
            des_server                  (str)        --      name of destination server
            des_path                    (str)        --      destination path
            overwrite                   (bool)       --      unconditional overwrite
            no_of_streams               (int)        --      number of streams
        """
        self.__rdropdown.select_drop_down_values(drop_down_id='restoreType', values=['Restore to disk'])
        self.__rdropdown.select_drop_down_values(
            drop_down_id="destinationServer",
            values=[des_server])
        self._admin_console.fill_form_by_id('destinationPath', des_path)
        if overwrite:
            self._admin_console.checkbox_select(checkbox_id='unconditionalOverwrite')
        if no_of_streams is not None:
            self._admin_console.fill_form_by_id("noOfStreams", no_of_streams)
        self._admin_console.click_submit()
