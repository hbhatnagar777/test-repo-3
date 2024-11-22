from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Comm vault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Classes defined in this file
    Restores : class used for performing a restore operation.
    __init__: Initialize the Restores class
    _set_data_files: Choose data file
    _edit_primary: Edit primary node in a shard/replica set
    _add_secondary: Add secondary node to be restored
    _set_destination_replicaset: Set destination replica set /shard name
    _set_destination_client: Set destination client
    _set_destination_dbpath: Set destination dbPath
    _set_destination_port: Set destination port
    restore_in_place: Starts a restore in place job
    restore_out_of_place: Starts a restore out of place job
    restore_to_disk: Starts a restore to disk job
"""

from Web.AdminConsole.Components.panel import DropDown
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Table

class Restores:
    """Class  for performing restore operations"""
    def __init__(self, admin_console):
        """ Initialize the Restores class

        Args:
            admin_console: instance of AdminConsoleBase

        """
        self._admin_console = admin_console
        self.__drop_down = DropDown(admin_console)

    @PageService()
    def _set_data_files(self, data_file_name):
        """Choose data file
         Args:
            data_file_name                (String)        --      Choose data file name
        """
        self._admin_console.select_hyperlink(data_file_name)

    @WebAction()
    def _edit_primary(self, shardname):
        """edit primary shard
         Args:
            shardname                (String)        --      Shard name
        """
        self._admin_console.driver.find_element(By.XPATH, 
            "//span[text()='"+shardname+"']/"
            "ancestor::td[contains(@id,'srcShardName')]"
            "/following-sibling::td[contains(@id,'actions')]"
            "/descendant::a[contains(@cv-toggle-content,"
            " 'Edit primary')]").click()

    @WebAction()
    def _add_secondary(self, shardname):
        """add secondary shard node
                 Args:
                    shardname                (String)        --      Shard name
                """
        self._admin_console.driver.find_element(By.XPATH, 
            "//span[text()='"
            "" + shardname + "']/ancestor::td[contains(@id,'srcShardName')]/"
            "following-sibling::td[contains(@id,'actions')]"
            "/descendant::a[contains(@cv-toggle-content,"
            " 'Add secondary')]").click()

    def _set_destination_replicaset(self, des_shardname):
        """set destination shard name
        args:
        des_shardname                (String)        --      destination shard name"""
        if des_shardname is not None:
            self._admin_console.fill_form_by_id('destShardName', des_shardname)

    def _set_destination_client(self, des_client):
        """set destination client
        args:
        des_client                (String)        --      destination client name"""
        self.__drop_down.select_drop_down_values(
            drop_down_id='configureNode_isteven-multi-select_#9384'
            , values=[des_client])

    def _set_destination_dbpath(self, des_dbpath):
        """Set destination dbPath
         Args:
            des_dbpath                (String)        --      set destination dbPath
        """
        if des_dbpath is not None:
            self._admin_console.fill_form_by_name('destDataDir', des_dbpath)

    def _set_destination_port(self, des_port):
        """Set port number
        Args:
            des_port                          (String)         --     Set port number
        """
        if des_port is not None:
            self._admin_console.fill_form_by_id('destPortNumber', des_port)

    @PageService()
    def save(self):
        """Click save"""
        self._admin_console.click_button('Save')

    @PageService()
    def restore_in_place(self, staging_path=None, overwrite=False, shutdown=False):
        """Starts a restore in place job
        Args:
            staging_path                (String)        --      Staging path location
            overwrite                   (bool)          --      unconditionally overwrites
            shutdown                    (bool)          --      autoshutdown option
                (overwrite option only available in case of collection based restores)
        """
        self._admin_console.select_hyperlink('In place')
        if staging_path is not None:
            self._admin_console.fill_form_by_id("stagingPathLogRestore", staging_path)
        if self._admin_console.check_if_entity_exists('xpath', "//*[@id = 'overwrite']"):
            if overwrite:
                self._admin_console.checkbox_select('overwrite')
            else:
                self._admin_console.checkbox_deselect('overwrite')
        if self._admin_console.check_if_entity_exists('xpath'
                                                      , "//*[@id = 'shutdownRemoveExistingData']"):
            if shutdown:
                self._admin_console.checkbox_select('shutdownRemoveExistingData')
            else:
                self._admin_console.checkbox_deselect('shutdownRemoveExistingData')
        self._admin_console.click_button(self._admin_console.props['action.submit'])
        self._admin_console.click_button(self._admin_console.props['label.yes'])

    @PageService()
    def restore_out_of_place(self, des_cluster, overwrite=False, des_rename=False, shutdown=False,
                             data_files=None, staging_path=None
                             , des_instance=None, des_shardlist=None):
        """
        Module for restore Out of Place
        Args:
            des_cluster                 (String)        --      name of destination cluster
            overwrite                   (bool)          --      unconditionally overwrites
              (overwrite option only available in case of collection view based restores)
            des_rename                  (bool)          --      renames databases/collections
            (add '_restore' suffix in dest, only available for collection view based restores)
            shutdown                     (bool)         --       shutdown MongoDB
            services and cleanup dbpath
            data_files                  (dict)          --      details dictionary
            data_file- {shard_name:{'Hostname': hostname,'Data Directory': dir,'Port Number': port}}
            staging_path                (String)        --      Staging path location
            des_instance                (String)        --      Instance of Client
            des_shardlist                (dict)         --       destination shard list
            {shard_name:{'P':[Hostname, port, dbPath], 'S1':[Hostname, port, dbPath]}
        """
        self.__drop_down.select_drop_down_values(0, [des_cluster])
        if des_instance is not None:
            self.__drop_down.select_drop_down_values(1, des_instance)
        if staging_path is not None:
            self._admin_console.fill_form_by_id("stagingPathLogRestore", staging_path)
        if data_files is not None:
            for file in data_files.keys():
                self._edit_primary(file)
                self._set_destination_client(data_files[file]['Hostname'])
                self._set_destination_port(data_files[file]['Port Number'])
                self.save()
        if self._admin_console.check_if_entity_exists('id', 'overwrite'):
            if overwrite:
                self._admin_console.checkbox_select('overwrite')
            else:
                self._admin_console.checkbox_deselect('overwrite')
        if self._admin_console.check_if_entity_exists('xpath'
                                                      , "//*[@id = 'shutdownRemoveExistingData']"):
            if shutdown:
                self._admin_console.checkbox_select('shutdownRemoveExistingData')
            else:
                self._admin_console.checkbox_deselect('shutdownRemoveExistingData')
        if des_rename:
            num = 0
            id = f'mongoDBRestore{num}'
            while self._admin_console.check_if_entity_exists('id', id):
                value = self._admin_console.driver.find_element(By.ID, id).get_attribute('name')
                self._admin_console.fill_form_by_id(id, f'{value}_restore')
                num += 1
                id = f'mongoDBRestore{num}'
        if des_shardlist is not None:
            table = Table(self._admin_console)
            number_of_shards = int(table.get_total_rows_count())
            if number_of_shards == len(des_shardlist):

                for shard in des_shardlist.keys():
                    if des_shardlist[shard]["P"] is not None:
                        self._edit_primary(shard)
                        self._set_destination_client(des_shardlist[shard]["P"][0])
                        self._set_destination_port(des_shardlist[shard]["P"][1])
                        self._set_destination_dbpath(des_shardlist[shard]["P"][2])
                        self.save()
                    for node, nodelist in des_shardlist[shard].items():
                        if node.startswith('S'):
                            self._add_secondary(shard)
                            self._set_destination_client(nodelist[0])
                            self._set_destination_port(nodelist[1])
                            self._set_destination_dbpath(nodelist[2])
                            self.save()
        self._admin_console.click_button(self._admin_console.props['action.submit'])
        self._admin_console.click_button(self._admin_console.props['label.yes'])

    @PageService()
    def restore_to_disk(self, des_cluster, disk_path, data_files=None
                        , shutdown=False, des_shardlist=None):
        """
        Module for restore to disk
        Args:
            des_cluster  :  name of destination cluster (str)
            disk_path                (String)        --      Disk path
            data_files   :   details dictionary of the form -
            { shard_name: {'Hostname': hostname,
            'Data Directory': dir,'Port Number': port} }
            shutdown   (bool)         --       shutdown MongoDB services and cleanup dbpath
            des_shardlist                (dict)         --       destination shard list
            {shard_name:{'P':[Hostname, port, dbPath], 'S1':[Hostname, port, dbPath]}
        """
        self._admin_console.select_hyperlink('Restore to disk')
        self.__drop_down.select_drop_down_values(0, [des_cluster])
        self._admin_console.fill_form_by_name('restoreToDiskPath', disk_path)
        if data_files is not None:
            for file in data_files.keys():
                self._edit_primary(file)
                self._set_destination_client(data_files[file]['Hostname'])
                self._set_destination_port(data_files[file]['Port Number'])
                self.save()
        if self._admin_console.check_if_entity_exists('xpath'
                                                      , "//*[@id = 'shutdownRemoveExistingData']"):
            if shutdown:
                self._admin_console.checkbox_select('shutdownRemoveExistingData')
            else:
                self._admin_console.checkbox_deselect('shutdownRemoveExistingData')
        if des_shardlist is not None:
            table = Table(self._admin_console)
            number_of_shards = int(table.get_total_rows_count())
            if number_of_shards == len(des_shardlist):

                for shard in des_shardlist.keys():
                    if des_shardlist[shard]["P"] is not None:
                        self._edit_primary(shard)
                        self._set_destination_client(des_shardlist[shard]["P"][0])
                        self._set_destination_port(des_shardlist[shard]["P"][1])
                        self._set_destination_dbpath(des_shardlist[shard]["P"][2])
                        self.save()
                    for node, nodelist in des_shardlist[shard].items():
                        if node.startswith('S'):
                            self._add_secondary(shard)
                            self._set_destination_client(nodelist[0])
                            self._set_destination_port(nodelist[1])
                            self._set_destination_dbpath(nodelist[2])
                            self.save()
        self._admin_console.click_button(self._admin_console.props['action.submit'])
        self._admin_console.click_button(self._admin_console.props['label.yes'])
