# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
details file has the functions to operate on instance page where we can backup and restore the
instances in Big data.

Overview:

    access_backup_history              --      Accesses backup history

    access_restore                     --      Accesses restore page

    access_instance_restore            --      Access restore of the instance

    access_restore_history             --      Access restore history

    backup_now                         --      Initiates backup

    log_backup                         --      Initiates log backup

    restore_all                        --      restore all clients with default options

    set_restore_content                --      set paths to be restored from backup

    access_hdfs                        --      Access HDFS page

    is_backupset_exists                --      Check if backup exists

    access_backupset                   --      Access backupset page or hadoop app page

    add_hadoop_app                     --      Add hadoop app

    add_hadoop_apps                    --      Add hadoop apps based on app list input

Nodes:

     discover_nodes                    --        Discover nodes in MongoDB instance from nodes tab

     backup                            --        Access backup from nodes tab

Restore:

    select_do_not_recover              --     selects do not recover

    set_staging_location               --     sets staging location

    select_out_of_place_restore        --     select out of place restore

    select_in_place_restore            --     select in place restore

    select_recover                     --     select recover

    set_number_of_streams              --     sets number of streams

    use_sstableloader_tool             --     enable sstableloader tool toggle

    set_staging_location               --     set staging location

    select_stage_free_restore          --     select stage free restore

    use_sstableloader_tool             --     selects use sstableloader tool option

    select_overwrite_option            --     Selects unconditional overwrite option

    ok                                 --     click on ok

    set_destination_client             --     set the destination client

    set_destination_path               --     set the destination paths

    set_overwrite                      --     Enables overwrite option in restore page

    restore_in_place                   --     Starts a restore in place job

    restore_out_of_place               --     Starts a restore out of place job

    select_destination_instance        --     Selects destination instance during couchbase out of place restore

    set_destination_bucket_names       --     Selects destination bucket names during couchbase out of place restore

    set_destination_db_names           --     Selects destination database names during yugabyte out of place restore


CouchbaseOperations:

    backup                             --     clicks backup button on the top menu bar and submits backup job

    access_restore                     --     Access restore of specified instance

    restore_all                        --     Selects all files and initiates restore

    submit_restore                     --     Submits restore job
"""

from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.browse import Browse, RBrowse
from Web.AdminConsole.Components.panel import Backup, ModalPanel, DropDown, PanelInfo, RDropDown, RPanelInfo, RModalPanel
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction


class Overview:
    """
    Functions to operate on backup and restore
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)
        self.__rtable = Rtable(admin_console)
        self.__browse = Browse(admin_console)
        self.__backup = Backup(admin_console)
        self.__panel = RModalPanel(admin_console)
        self.__hadoop_app_map = {"hdfs": "HDFS", "hbase": "HBase", "kudu": "Kudu"}
        self.__pagecontainer = PageContainer(admin_console)
        self.__rbrowse = RBrowse(admin_console)

    @WebAction()
    def __click_hadoop_app(self, app_index=0):
        """
        Click on the Hadoop App

            Args:
                app_index       (int)   -- 0 for HDFS, 1 for HBASE

        """
        xp = '//a[contains(@href,"bigDataBackupsetDetails")]'
        self._admin_console.driver.find_elements(By.XPATH, xp)[app_index].click()
        self._admin_console.wait_for_completion()

    @PageService()
    def restore_all(self, view=None):
        """
        Initiate restore
         Args:
            view   (String)     --  for cassandra restore,can be either "Cluster view" or "Keyspace view"
        """
        if view is not None:
            self.__browse.select_keyspace_view(view)
        self.__browse.select_for_restore(all_files=True)
        self.__browse.submit_for_restore()
        return Restore(self._admin_console)

    @PageService()
    def set_restore_content(self, paths=None, folder=None):
        """set paths to be restored from backup
        Args:
            paths       (list)   --  paths to be selected for restore
            folder      (str)    --  folder to be accessed before selecting paths
        Returns:
            Restore object for performing restore operations post restore content selection
        """
        if folder is not None:
            self.__browse.access_folder(folder)
        if paths is None:
            self.__browse.select_for_restore(all_files=True)
        else:
            self.__browse.select_for_restore(paths)
        self.__browse.submit_for_restore()
        return Restore(self._admin_console)

    @PageService()
    def select_restore_content(self, paths=None, folder=None, view=None):
        """set paths to be restored from backup
        Args:
            paths       (list)   --  paths to be selected for restore
            folder      (str)    --  folder to be accessed before selecting paths
        Returns:
            Restore object for performing restore operations post restore content selection
        """
        if view is not None:
            self.__browse.select_keyspace_view(view)
        if folder is not None:
            # self.__rbrowse.access_folder(folder)
            self.__rtable.access_link_by_column(
                entity_name="Name", link_text=folder)
        if paths is None:
            self.__rbrowse.select_files(select_all=True)
        else:
            self.__rbrowse.select_files(file_folders=paths)
        self.__rbrowse.submit_for_restore()
        return Restore(self._admin_console)

    @PageService()
    def backup_now(self, name='default', backup_level=Backup.BackupType.FULL):
        """
        Initiate backup
        Args:
            name                         (String)       --    Instance name
            backup_level                 (String)       --    Specify backup level from constant
                                                              present in OverView class
        """
        self.__table.access_action_item(
            name, self._admin_console.props['label.globalActions.backup'])
        _job_id = self.__backup.submit_backup(backup_level)
        return _job_id

    @PageService()
    def log_backup(self, name='default', backup_level=Backup.BackupType.INCR):
        """
        Initiate log backup
        Args:
            name                         (String)       --    Instance name
            backup_level                 (String)       --    Specify backup level from constant
                                                              present in OverView class
        """
        self.__table.access_action_item(
            name, self._admin_console.props['label.globalActions.backup'])
        _job_id = self.__backup.submit_backup(backup_level, log=True)
        return _job_id

    @PageService()
    def access_backup_history(self, instance=None):
        """
        Access backup history
        Args:
            instance                       (String)       --     Instance name
                    default - None, access from top menu else from instance menu
        """
        if instance is None:
            self._admin_console.access_menu("Backup history")
        else:
            self.__table.access_action_item(instance, 'Backup history')

    @PageService()
    def access_restore_history(self, instance=None):
        """Access restore history
        Args:
            instance                       (String)       --     Instance name
                    default - None, access from top sub menu else from instance level
        """
        if instance is None:
            self._admin_console.access_menu_from_dropdown("Restore history")
        else:
            self.__table.access_action_item(instance, 'Restore history')

    @PageService()
    def access_restore(self, name):
        """Access restore of specified instance
        Args:
            name                   (String)          --     Instance name
        """
        self.__table.access_action_item(name, 'Restore')

    @PageService()
    def access_instance_restore(self):
        """Access restore of specified instance"""
        self._admin_console.tile_select_hyperlink('Recovery points', 'Restore')

    @PageService()
    def access_configuration(self):
        """Access configuration page"""
        self._admin_console.select_configuration_tab()
        return Configuration(self._admin_console)

    @PageService()
    def access_tablegroups(self):
        """Access configuration page"""
        self._admin_console.access_tab("Table groups")

    @PageService()
    def access_namespacegroups(self):
        """Access namespace groups tab"""
        self._admin_console.access_tab("Namespace groups")

    @PageService()
    def access_datacenter(self):
        """Access configuration page"""
        self._admin_console.access_tab("Data center")

    @PageService()
    def access_nodes(self):
        """Access nodes page"""
        self.__pagecontainer.select_tab("Nodes")
        return Nodes(self._admin_console)

    @PageService()
    def access_hdfs(self):
        """Access HDFS page"""
        self.__click_hadoop_app(app_index=0)

    @PageService()
    def is_backupset_exists(self, backupset):
        """Check if backup exists
        Args:
            backupset        (str)   -- name of the backupset
        """
        return self.__table.is_entity_present_in_column('Name', backupset)

    @PageService()
    def access_backupset(self, backupset="default"):
        """Access backupset page or hadoop app page
        Args:
            backupset        (str)   -- name of the backupset
        Returns:
            Backupset object of hadoop app or generic one
        """
        self.__table.access_link(backupset)
        from Web.AdminConsole.Bigdata.backupset import Backupset
        return Backupset(self._admin_console, backupset)

    @PageService()
    def add_hadoop_app(self, app_name, staging, user=None):
        """Add hadoop app
        Args:
            app_name        (str)   -- name of the app(HBase/Kudu)
            staging         (str)   -- staging path for the app
            user            (str)   -- user of the app(Default - same as app name)
        """
        app_name = app_name.lower()
        self._admin_console.access_tile('addHadoopApps')
        rdropdown = RDropDown(self._admin_console)
        rdropdown.select_drop_down_values(drop_down_id="hadoopApps", values=[self.__hadoop_app_map[app_name]])
        self._admin_console.fill_form_by_id('name', user or app_name)
        self._admin_console.fill_form_by_id('stagingLocation', staging)
        self._admin_console.submit_form()
        self._admin_console.check_error_message()

    @PageService()
    def add_hadoop_apps(self, apps=None):
        """Add hadoop apps based on app list
        Args:
            apps            (dict)  -- Apps to be added
                apps - {"app_name": {"user":"", "staging":""}}
        """
        apps = apps or {}
        for app in apps:
            if not self.is_backupset_exists(app):
                self.add_hadoop_app(app_name=app, staging=app.get("staging"), user=app.get("user"))


class Configuration:
    """Operations on configuration page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)

    @PageService()
    def access_backup(self):
        """clicks backup button on the top menu bar"""
        self._admin_console.access_menu(self._admin_console.props['label.globalActions.backup'])

    @PageService()
    def access_restore(self):
        """clicks restore button on the top menu bar"""
        self._admin_console.access_menu(self._admin_console.props['action.restore'])

    @PageService()
    def is_nodes_exists(self):
        """Check if nodes exists"""
        xpath = '"//*[@title="Nodes"]/../..//*[@class="info-place-holder"]'
        if self._admin_console.is_element_present(xpath):
            return False
        return True

    @PageService()
    def discover_nodes(self):
        """Discovers nodes"""
        self._admin_console.select_hyperlink('Discover nodes')
        discover_text = self._admin_console.get_notification().lower()
        if not discover_text:
            raise CVWebAutomationException("No notification is popped up to extract text")
        if "success" not in discover_text:
            raise CVWebAutomationException("Failed to discover nodes")
        self._admin_console.driver.refresh()

    @PageService()
    def get_replica_set_list(self):
        """Fetches replica set information in case of mongoDB"""
        port_list = self.__table.get_column_data('Port number')
        shard_list = self.__table.get_column_data("Replica set")
        hostname_list = self.__table.get_column_data("Host name")
        replicaset_list = {}
        for shard, hostname, port in zip(shard_list, hostname_list, port_list):
            if shard == '':
                continue
            if shard not in replicaset_list:
                replicaset_list[shard] = [hostname + "_" + port]
            else:
                replicaset_list[shard].append(hostname + "_" + port)
        return replicaset_list

    @PageService()
    def access_overview(self):
        """Access overview page"""
        self._admin_console.select_overview_tab()
        return Overview(self._admin_console)


    @PageService()
    def edit_snapshot_engine(self, engine="native"):
        """
        Edits the snapshot engine
        Args:
            engine  (str)       --      Engine name
        """
        rpanel_info = RPanelInfo(self._admin_console, 'Snapshot management')
        toggle_element = rpanel_info.get_toggle_element('Enable hardware snapshot')
        if rpanel_info.is_toggle_enabled(toggle_element):
            rpanel_info.edit_tile()
        else:
            rpanel_info.enable_toggle('Enable hardware snapshot')
        drop_down = RDropDown(self._admin_console)
        drop_down.select_drop_down_values(drop_down_id='enginesDropdown', values=[engine])
        self._admin_console.click_button("Save")

    @PageService()
    def edit_mongosnapshot_engine(self, engine="native"):
        """
        Edits the snapshot engine
        Args:
            engine  (str)       --      Engine name
        """
        rpanel_info = RPanelInfo(self._admin_console, 'Snapshot management')
        toggle_element = rpanel_info.get_toggle_element('Enable snap backup')
        if rpanel_info.is_toggle_enabled(toggle_element):
            rpanel_info.edit_tile()
        else:
            rpanel_info.enable_toggle('Enable snap backup')
        drop_down = RDropDown(self._admin_console)
        drop_down.select_drop_down_values(drop_down_id='enginesDropdown', values=[engine])
        self._admin_console.click_button("Save")

    @PageService()
    def discover_cassandra_node(self):
        """Discovery cassandra nodes"""
        self._admin_console.click_button(value='Discover nodes')
        num_of_column = self.__table.get_number_of_columns()
        if num_of_column != 6:
            raise CVWebAutomationException("Failed to discover cassandra nodes")

    @PageService()
    def edit_cassandra_node(self, configpath, datapath, javapath=None):
        """Edit cassandra nodes"""

        ip_address = self.__table.get_column_data('IP address')
        for i in ip_address:
            self.__table.search_for(i)
            self.__table.select_all_rows()
            self._admin_console.click_by_id("EDIT_NODE")
            if javapath is not None:
                self._admin_console.fill_form_by_id('javaHome', javapath)
            if configpath is not None:
                self._admin_console.fill_form_by_id('configFile', configpath)
            self._admin_console.fill_form_by_id('dataDir', datapath)
            self._admin_console.click_button('Save')
            self._admin_console.wait_for_completion()

    @PageService()
    def set_archive_properties(self, archive_path, archive_command):
        """enables commitlogs toggle and configures archive path and archive command"""
        panel = PanelInfo(self._admin_console, title='General')
        panel.enable_toggle("Commit log backups")
        self._admin_console.fill_form_by_id('archiveLogPath', archive_path)
        self._admin_console.fill_form_by_id('archiveCommand', archive_command)
        self._admin_console.click_button("Save")
        self._admin_console.wait_for_completion()

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
        self._admin_console.click_button_using_text('Yes')


class DataCenter:
    """Operations on Data center page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)
        self.__backup = Backup(admin_console)

    @PageService()
    def backup(self, name='default', backup_level=Backup.BackupType.INCR):
        """initial backup job"""
        self.__table.access_action_item(name, "Back up")
        self._admin_console.select_radio(id=backup_level.value)
        self._admin_console.click_button("Submit")
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def backup_log(self, name='default', backup_level=Backup.BackupType.INCR):
        """initial backup job"""
        self.__table.access_action_item(name, "Back up")
        self._admin_console.select_radio(id=backup_level.value)
        self._admin_console.checkbox_select(checkbox_id='logCheckbox')
        self._admin_console.click_button("Submit")
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def access_nodes(self):
        """Access configuration page"""
        self._admin_console.access_tab("Nodes")
        return Nodes(self._admin_console)

    @PageService()
    def access_restore(self, name='default'):
        """Access configuration page"""
        self.__table.access_action_item(name, "Restore")


class TableGroups:
    """Operations on table groups page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)

    @PageService()
    def access_backup(self, tablegroup="default"):
        """clicks backup button on the top menu bar"""
        self.__table.access_action_item(tablegroup, 'Back up')

    @PageService()
    def access_restore(self, tablegroup="default"):
        """clicks restore button on the top menu bar"""
        self.__table.access_action_item(tablegroup, 'Restore')

    @PageService()
    def access_tablegroup(self, tablegroup="default"):
        """
        Access instance
        """
        self.__table.access_link(tablegroup)

    @PageService()
    def backup_now(self, tablegroup='default'):
        """
        Initiate backup
        Args:
            name                         (String)       --    Instance name
            backup_level                 (String)       --    Specify backup level from constant
                                                              present in OverView class
        """
        self.access_backup(tablegroup)
        self._admin_console.select_radio(id="INCREMENTAL")
        self._admin_console.click_button("Submit")
        _job_id = self._admin_console.get_jobid_from_popup()
        return _job_id


class NamespaceGroups:
    """Operations on table groups page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Rtable(admin_console)

    @PageService()
    def access_backup(self, namespacegroup="default"):
        """clicks backup button on the top menu bar"""
        self.__table.access_action_item(namespacegroup, 'Back up')

    @PageService()
    def access_restore(self, namespacegroup="default"):
        """clicks restore button on the top menu bar"""
        self.__table.access_action_item(namespacegroup, 'Restore')

    @PageService()
    def access_namespacegroup(self, namespacegroup="default"):
        """
        Access instance
        """
        self.__table.access_link(namespacegroup)

    @PageService()
    def backup_now(self, namespacegroup='default'):
        """
        Initiate backup
        Args:
            name                         (String)       --    Instance name
            backup_level                 (String)       --    Specify backup level from constant
                                                              present in OverView class
        """
        self.access_backup(namespacegroup)
        self._admin_console.select_radio(id="INCREMENTAL")
        self._admin_console.click_button("Submit")
        _job_id = self._admin_console.get_jobid_from_popup()
        return _job_id


class Nodes:
    """Operations on nodes page"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__pagecontainer = PageContainer(admin_console)
        self.__table = Rtable(self._admin_console)

    @PageService()
    def discover_nodes(self):
        """Discovers nodes"""
        self._admin_console.click_button_using_text('Discover nodes')
        discover_text = self._admin_console.get_notification().lower()
        if not discover_text:
            raise CVWebAutomationException("No notification is popped up to extract text")
        if "success" not in discover_text:
            raise CVWebAutomationException("Failed to discover nodes")
        self._admin_console.refresh_page()

    @PageService()
    def is_nodes_exists(self):
        """Check if nodes exists"""
        nodenames = self.__table.get_column_data(column_name='Name')
        if len(nodenames):
            return True
        else:
            return False

    @PageService()
    def backup(self):
        """clicks backup button on the top menu bar"""
        self.__pagecontainer.access_page_action("Backup")
        self._admin_console.select_radio(id='FULL')
        self._admin_console.click_button_using_text('Submit')

class CouchbaseOperations:
    """Operations on couchbase react page"""
    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__backup = Backup(admin_console)
        self.__panel = RModalPanel(admin_console)
        self.__browse = Browse(admin_console)
        self.__pagecontainer = PageContainer(admin_console)
        self.__rbrowse = RBrowse(admin_console)

    @PageService()
    def backup(self, backup_type, name='default'):
        """clicks backup button on the top menu bar and submits backup job"""
        self.__pagecontainer.access_page_action("Backup")
        if backup_type == "FULL":
            self._admin_console.select_radio(id='FULL')
        elif backup_type == "INCR":
            self._admin_console.select_radio(id='INCREMENTAL')
        else:
            self._admin_console.log.info("invalid backup type")
        self._admin_console.click_button("Submit")
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def restore_all(self):
        """
        Initiate restore
        """
        self.__rbrowse.select_files(select_all=True)
        self.__rbrowse.submit_for_restore()
        return Restore(self._admin_console)

    @PageService()
    def access_restore(self):
        """Access restore of specified instance"""
        self.__pagecontainer.access_page_action("Restore")

    @PageService()
    def submit_restore(self):
        """submits restore job"""
        self._admin_console.click_button_using_id('Save')
        self._admin_console.click_button_using_text('Yes')


class Restore:
    """Restore operations"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__panel = RModalPanel(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__rtable = Rtable(admin_console)

    @PageService()
    def select_out_of_place_restore(self):
        """Select out of place restore checkbox"""
        self.__panel.access_tab('Out of place')

    @PageService()
    def use_sstableloader_tool(self):
        """Enable SSTableLoader tool toggle"""
        self._admin_console.select_radio(id='sSTableLoader')

    @PageService()
    def set_staging_location(self, location):
        """Set staging location"""
        self._admin_console.fill_form_by_id(
            element_id='stagingLocation', value=location)

    @PageService()
    def select_overwrite_option(self):
        """check unconditional overwrite option"""
        self._admin_console.checkbox_select('unconditionalOverwrite')

    @PageService()
    def select_destination_instance(self, destination_instance):
        """selects destination instance during out of place restore"""
        self.__rdropdown.select_drop_down_values(
            drop_down_id='destinationClusterServer',
            values=[destination_instance])

    @PageService()
    def set_destination_bucket_names(self):
        """sets destination bucket names during out of place restore"""
        rows = int(self.__rtable.get_total_rows_count() / 2)
        for i in range(1, rows + 1):
            self.__rtable.type_input_for_row(i, '_oopauto')

    @PageService()
    def set_kms_config(self, kms_config):
        """sets kms configuration"""
        self.__rdropdown.select_drop_down_values(
            drop_down_id='kmsConfiguration',
            values=[kms_config])

    @PageService()
    def set_destination_db_names(self, restoreoption):
        """sets destination db names during out of place restore"""
        rows = int(self.__rtable.get_total_rows_count() / 2)
        if restoreoption != 0 and restoreoption != 4:
            for i in range(1, rows + 1):
                self.__rtable.type_input_for_row(i, '_oopauto')

    @PageService()
    def set_number_of_streams(self, number):
        """Set number of streams"""
        self._admin_console.fill_form_by_id(
            element_id='noOfStreams', value=number)

    @PageService()
    def select_stage_free_restore(self):
        """Select run stage free restore"""
        self._admin_console.checkbox_select(checkbox_id='runStageFreeRestore')

    @PageService()
    def select_in_place_restore(self):
        """Select in place restore tab"""
        self.__panel.access_tab('In place')

    @PageService()
    def submit_restore(self):
        """submit restore job"""
        self.__panel.submit()
        self._admin_console.click_button_using_text('Yes')

    @PageService()
    def click_restore_and_confirm(self):
        """star restore job"""
        self.__panel.click_restore_button()
        self._admin_console.click_button_using_text('Yes')

    @PageService()
    def set_destination_client(self, des_client=None, dropdown_id=None):
        """set the destination client
        Args:
            des_client          (str)   --  name of destination client
                    default - uses prefilled value from cc
            dropdown_id         (str)  --  id xpath of the destination client
                    default - uses first dropdown present in the page
        """
        if des_client is not None:
            drop_down = DropDown(self._admin_console)
            if dropdown_id is None:
                drop_down.select_drop_down_values(0, [des_client])
            else:
                drop_down.select_drop_down_values(drop_down_id=dropdown_id, values=[des_client])

    @PageService()
    def set_destination_path(self, des_path, des_path_id="OOPPath"):
        """Set the destination path
        Args:
            des_path           (str)   --  path where data needs to be restored
            des_path_id        (str)   --  id xpath of the destination path
        """
        self._admin_console.fill_form_by_name(des_path_id, des_path)

    @PageService()
    def set_overwrite(self, overwrite=False):
        """Enables overwrite option in restore page
        Args:
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        """
        if self._admin_console.check_if_entity_exists('xpath', "//*[@id = 'overwrite']"):
            if overwrite:
                self._admin_console.checkbox_select('overwrite')
            else:
                self._admin_console.checkbox_deselect('overwrite')

    @PageService()
    def select_restore_logs(self):
        """"select commit log restore"""
        self._admin_console.checkbox_select(checkbox_id='restoreCommitLog')

    @PageService()
    def deselect_restore_logs(self):
        """"select commit log restore"""
        Checkbox(self._admin_console).uncheck(id='restoreCommitLog')

    @PageService()
    def restore_in_place(self, overwrite=False):
        """Starts a restore in place job
        Args:
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        Returns:
            job id as string
        """
        self.select_in_place_restore()
        self.set_overwrite(overwrite)
        self.submit_restore()
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def restore_out_of_place(self, destination_path, destination_client=None,
                             dest_path_id=None, dropdown_id=None, overwrite=False):
        """Starts a restore out of place job
        Args:
            destination_path    (str)   --  path where data needs to be restored
            destination_client  (str)   --  name of destination client
                    default - uses prefilled value from cc
            dest_path_id        (str)   --  id xpath of the destination path
                    default - "OOPPath" id xpath is used
            dropdown_id         (bool)  --  id xpath of the destination client
                    default - uses first dropdown present in the page
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        Returns:
            job id as string
        """
        self.select_out_of_place_restore()
        self.set_destination_client(destination_client, dropdown_id)
        self.set_destination_path(destination_path, dest_path_id)
        self.set_overwrite(overwrite)
        self.submit_restore()
        return self._admin_console.get_jobid_from_popup()
