# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for Collection Pruning related operations

    CollectionPruningHelper:

        __init__()                              --  Initialize the CollectionPruningHelper object

        prune_orphan_datasources()              --  Prunes datasources for which the client or backupset no longer exist

        is_pruning_audited()                    --  Checks if a given datasource is audited in audit trail logs

        prune_migrated_index_datasource()       --  Performs pruning of stale index datasources associated to clients

        delete_collection_folder()              --  Deletes a collection folder from index server
                                                    for a given exchange datasource name

        delete_pruning_registry()               --  Deletes the pruning registry [AppPruneDataSourcesMinutes] set
                                                    in EventManager

"""

import time
from AutomationUtils import logger
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils import constants as cs


class CollectionPruningHelper:
    """ contains helper class for Collection Pruning related operations"""

    def __init__(self, commcell):
        """
        Initialize the CollectionPruningHelper object
        """
        self.commcell = commcell
        self.csdb = CommServDatabase(self.commcell)
        self.ds_helper = DataSourceHelper(self.commcell)
        self.log = logger.get_log()
        self.retry = 0
        self.max_attempt = 15
        self.wait_time = 60
        self.log.info("Deleting pruning registry as it may cause pruning of datasources "
                      "even before it is called from helper")
        self.delete_pruning_registry()

    def prune_orphan_datasources(self, datasource_name, use_api=False):
        """
        Prunes datasources for which the client or backupset no longer exist
            Args:
                datasource_name(str)    -- Name of the datasource to be pruned
                use_api(bool)           -- Represents whether pruning should be via API or registry
            Returns:
                Bool                    -- Boolean value representing whether the given datasource is pruned or not
        """
        if use_api is True:
            self.log.info(f'Calling datasource pruning API for datasource [{datasource_name}]')
            self.log.info('Pruning API is being called for pruning')
            self.ds_helper.prune_orphan_datasources()
            self.log.info('Pruning API call completed successfully')
        else:
            self.log.info('Going with timer based registry for pruning to start')
            cs_client = self.commcell.commserv_client
            cs_machine = Machine(cs_client)
            prune_time = 5
            if cs_machine.check_registry_exists(cs.EVENT_MANAGER_REG, cs.PRUNE_REGISTRY_MINS):
                self.log.info(f'Registry is already set [{cs.EVENT_MANAGER_REG}]. '
                              f'Updating the prune timer to [{prune_time}] minutes')
                cs_machine.update_registry(cs.EVENT_MANAGER_REG, cs.PRUNE_REGISTRY_MINS, prune_time, "DWORD")
                self.log.info(f'Registry timer [{cs.EVENT_MANAGER_REG}] updated successfully')
            else:
                self.log.info(f'Registry [{cs.EVENT_MANAGER_REG}] is not present.')
                cs_machine.create_registry(cs.EVENT_MANAGER_REG, cs.PRUNE_REGISTRY_MINS, prune_time, "DWORD")
                self.log.info(f'Created new registry [{cs.EVENT_MANAGER_REG}] with time [{prune_time}] minutes.')
            self.log.info(f'Restarting service - [{cs.EVENT_MANAGER_SERVICE}]')
            cs_client.restart_service(cs.EVENT_MANAGER_SERVICE)
            self.log.info(f'Restarted service - [{cs.EVENT_MANAGER_SERVICE}]. '
                          f'waiting for [{self.wait_time}] for restart to complete')
            time.sleep(self.wait_time)
            self.log.info(f'Wait complete. Waiting for [{prune_time}] minutes for automatic pruning to be triggered')
            time.sleep(prune_time * 60)
            self.log.info('Wait complete')
        while self.ds_helper.check_datasource_exists(datasource_name):
            self.log.info(f'Sleeping for [{self.wait_time}] seconds for pruning thread to complete')
            self.retry += 1
            if self.retry == self.max_attempt:
                self.log.info('Max retry attempt exceeded. Datasource not pruned')
                self.retry = 0
                return False
            time.sleep(self.wait_time)
        self.log.info('Datasource pruned successfully')
        return True

    def is_pruning_audited(self, datasource_name, core_name):
        """
        Checks if a given datasource is audited in audit trail logs
            Args:
                datasource_name(str)    -- Name of the datasource to be audited

                core_name(str)          -- Name of the core to be audited

            Returns:
                bool                    -- boolean value representing if the pruning information is audited

            Raises:
                Exception:
                    If audit trail logs are missing

                    if audit trail query fails in execution
        """
        try:
            query = "select top 1 messageTxt from (" \
                    "select top 100 ISNULL(DBO.fn_EvFormatEventMsgText(a.id, 0, a.messageId, 1, 2), '') as messageTxt " \
                    "from evmsg a WITH (NOLOCK)" \
                    "   left join EvGuiAuditOperation b  WITH (NOLOCK) on a.id = b.evMsgId and b.id = 76941" \
                    "   left join EvGuiAuditParameter c  WITH (NOLOCK) on a.id = c.evMsgId " \
                    "order by a.id desc) evmsg " \
                    f"where messageTxt like '%{datasource_name}%' and messageTxt like '%{core_name}%' " \
                    "and messageTxt like '%data source was deleted%'"
            self.log.info(f"Audit Query generated is: {query} ")
            self.csdb.execute(query)
            audit_message = self.csdb.fetch_one_row()
            while len(audit_message) == 0:
                self.log.info(f"Audit results not yet available in DB. Sleeping for [{self.wait_time}] seconds")
                time.sleep(self.wait_time)
                self.retry += 1
                if self.retry == self.max_attempt:
                    self.retry = 0
                    raise Exception("audit trail logs are missing")
                self.csdb.execute(query)
                audit_message = self.csdb.fetch_one_row()
            self.log.info(f"Audit trail obtained successfully. Audit message: {audit_message[0]}")
            self.log.info("Pruning messages are audited successfully")
            return True
        except Exception as exception:
            self.log.exception(
                "Exception occurred while fetching audit information")
            raise exception

    def prune_migrated_index_datasource(self, old_datasource_name, new_datasource_name):
        """
        Performs pruning of stale index datasources associated to clients
            Args:
                old_datasource_name(str)    -- Name of the stale datasource to be pruned

                new_datasource_name(str)    -- Name of the active datasource associated to the client

            Returns:
                None:

            Raises:
                Exception:
                    If new and old datasource name are the same

                    If old index datasource is not pruned
        """
        self.log.info(f"Pruning old index datasource : [{old_datasource_name}].")
        self.prune_orphan_datasources(old_datasource_name)
        self.log.info(f"Call to prune old datasource completed successfully")
        _, new_ds_actual_name = self.ds_helper.get_datasource_collection_name(new_datasource_name)
        self.log.info(f"New index datasource : [{new_ds_actual_name}].")
        if old_datasource_name.lower() == new_ds_actual_name.lower():
            raise Exception(f"Old and new datasource names are the same. Index server switch was not successful")
        if self.ds_helper.check_datasource_exists(old_datasource_name):
            raise Exception(f"Old index datasource [{old_datasource_name}] not pruned")
        self.log.info("Idle orphan index datasource pruned successfully")

    def delete_collection_folder(self, datasource_name):
        """
        Deletes a collection folder from index server for a given exchange datasource name
            Args:
                datasource_name --  Name of the datasource for which the collection folder is to be deleted

            Returns:
                None:

            Raises:
                Exception:
                    If the provided datasource is not of type Exchange

                    If index confHome directory deletion fails

                    If index collection directory deletion fails
        """
        self.log.info(f"Going to delete the collection belonging to datasource [{datasource_name}] from index server")
        ds_obj = self.commcell.datacube.datasources.get(datasource_name)
        if not ds_obj.data_source_type.lower() == "exchange":
            raise Exception("Exchange datasource is the only type supported")
        is_obj = self.commcell.index_servers.get(ds_obj.index_server_cloud_id)
        is_node_obj = is_obj.get_index_node(is_obj.client_name[0])
        index_node_client = is_node_obj.index_node_client
        machine = Machine(index_node_client)
        collection_dir = ds_obj.computed_core_name.replace(cs.MULTI_NODE, "")
        self.log.info(f"Obtained collection directory name - [{collection_dir}]")
        index_dir = is_node_obj.index_location
        index_conf_dir = index_dir+"\\"+cs.CONF_HOME+"\\"+collection_dir+"*"
        index_collection_dir = index_dir+"\\"+collection_dir+"*"
        self.log.info(f"Stopping [{cs.ANALYTICS_SERVICE_NAME}] service before index directory deletion")
        index_node_client.stop_service(cs.ANALYTICS_SERVICE_NAME)
        self.log.info(f"Going to delete index confHome directory - [{index_conf_dir}] - "
                      f"present in index server [{index_node_client.client_name}]")
        if not machine.remove_directory(index_conf_dir):
            raise Exception("Failed to delete index confHome Directory")
        self.log.info("Deleted index confHome directory successfully")
        self.log.info(f"Going to delete index collection directory - [{index_collection_dir}] - "
                      f"present in index server [{index_node_client.client_name}]")
        if not machine.remove_directory(index_collection_dir):
            raise Exception("Failed to delete index collection directory")
        self.log.info("Deleted index collection directory successfully")
        index_node_client.start_service(cs.ANALYTICS_SERVICE_NAME)
        self.log.info(f"Started [{cs.ANALYTICS_SERVICE_NAME}] service successfully")

    def delete_pruning_registry(self, wait_time=5):
        """
        Deletes the pruning registry [AppPruneDataSourcesMinutes] set in EventManager
        Args:
                wait_time --  wait time in minutes post deleting pruning registry
        """
        cs_client = self.commcell.commserv_client
        cs_machine = Machine(cs_client)
        if cs_machine.check_registry_exists(cs.EVENT_MANAGER_REG, cs.PRUNE_REGISTRY_MINS):
            self.log.info(f'Registry is already exist [{cs.EVENT_MANAGER_REG}]-> [{cs.PRUNE_REGISTRY_MINS}]. '
                          'Removing the registry')
            cs_machine.remove_registry(cs.EVENT_MANAGER_REG, cs.PRUNE_REGISTRY_MINS)
            self.log.info(f"Registry [{cs.PRUNE_REGISTRY_MINS}] removed successfully")
            cs_client.restart_service(cs.EVENT_MANAGER_SERVICE)
        else:
            self.log.info(f"Registry [{cs.PRUNE_REGISTRY_MINS}] doesn't exist")
        self.log.info(f'Restarted service - [{cs.EVENT_MANAGER_SERVICE}]. '
                      f'waiting for [{self.wait_time * wait_time}] for restart to complete')
        time.sleep(self.wait_time * wait_time)
        self.log.info(f'Restarted service [{cs.EVENT_MANAGER_SERVICE}] successfully')
