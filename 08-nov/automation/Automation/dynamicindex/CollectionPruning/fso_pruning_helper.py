# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for FSO collection Pruning related operations

    FSOPruningHelper:

        __init__()                          --  Initialize the FSO Pruning Helper object

        initialize_fso()                    --  Initializes FSO entities such as plan and inventory

        add_content()                       --  Creates a new backupset and adds content to a FS client

        add_fso_server()                    --  Creates a new FSO server

        validate_fso_server()               --  Validates the data crawled in the FSO server

        switch_default_backupset()          --  Sets default backupset for the agent

        delete_backupset()                  --  Deletes the backupset associated with FSO backed up crawl datasource

        delete_unc_backupset()              --  Deletes the backupset created for FSO live crawl

        get_collection_info_for_pruning()   --  Gets the collection info needed for pruning

        check_if_collection_pruned()        --  Validates if the files in a collection is pruned

        cleanup()                           --  Cleans up the FSO entities such as Plan and inventory

        validate_audit_pruning()            --  Validates the audit trail logs for pruning

"""

import time
from AutomationUtils.machine import Machine
from cvpysdk.activateapps.constants import TargetApps
from cvpysdk.activateapps.constants import EdiscoveryConstants as edisconstant
from dynamicindex.CollectionPruning.collection_pruning_helper import CollectionPruningHelper
from dynamicindex.Datacube.data_source_helper import DataSourceHelper


class FSOPruningHelper(CollectionPruningHelper):
    """ contains helper class for FSO collection Pruning related operations"""

    def __init__(self, commcell):
        """
        Initialize the FSO Pruning Helper object
        """
        super().__init__(commcell)
        self.commcell = commcell
        self.ds_helper = DataSourceHelper(self.commcell)
        self.plans_obj = self.commcell.plans
        self.invs_obj = self.commcell.activate.inventory_manager()
        self.fso_obj = self.commcell.activate.file_storage_optimization()
        self.backupset_name = "FSO_backupset"
        self.file_count = 5
        self.plan_obj = None
        self.inv_obj = None
        self.fso_client = None
        self.fso_client_obj = None
        self.all_ds_obj = None
        self.ds_obj = None
        self.agent = None
        self.collection_name = None
        self.is_node_name = None
        self.query = None
        self.machine_obj = None
        self.path = None
        self.ds_name = None

    def initialize_fso(self, plan_name, inv_name, index_server, **kwargs):
        """ Initializes FSO entities such as plan and inventory
            Args:
                plan_name  (str)    --  Name of the plan to be created

                inv_name (str)      --  Name of the inventory to be created

                index_server (str)  --  Name of the index server that will be used by plan and inventory

                kwargs (dict)       --  Dictionary of optional parameters
                    fso_client(str)         --  Name of the FSO server
                    ds_name(str)            --  Name of the datasource

            Returns:
                None:
        """
        self.fso_client = kwargs.get("fso_client", None)
        self.ds_name = kwargs.get("ds_name", None)
        if self.fso_client is None or self.ds_name is None:
            raise Exception("FSO Client or datasource name inputs are missing. Pass valid inputs and try again")
        if self.fso_obj.has_server(self.fso_client):
            self.log.info("FSO Server exists with data sources already. Rechecking for any older run entities exists")
            server_obj = self.fso_obj.get(self.fso_client)
            ds_obj = server_obj.data_sources
            if ds_obj.has_data_source(self.ds_name):
                self.log.info(f"Datasource({self.ds_name}) exists already. Deleting it")
                ds_obj.delete(self.ds_name)
                self.fso_obj.refresh()  # As it is new client, refreshing it again
        if self.plans_obj.has_plan(plan_name):
            self.log.info(f"Deleting plan as it exists before - {plan_name}")
            self.plans_obj.delete(plan_name)
        if self.invs_obj.has_inventory(inv_name):
            self.log.info(f"Deleting inventory as it exists before - {inv_name}")
            self.invs_obj.delete(inv_name)
        self.log.info(f"Going to create FSO Plan - {plan_name}")
        self.plan_obj = self.plans_obj.add_data_classification_plan(
            plan_name=plan_name,
            index_server=index_server,
            target_app=TargetApps.FSO)
        self.log.info("Plan got created")
        self.log.info(f"Going to create Inventory - {inv_name}")
        self.inv_obj = self.invs_obj.add(inv_name, index_server)
        self.log.info("Inventory got created. Inventory crawl job got completed")

    def add_content(self, client_obj, server_plan, default_backupset, content):
        """ Creates a new backupset and adds content to a FS client
            Args:
                client_obj  (str)       --  Client Object on which the content is to be added

                server_plan (str)       --  Name of the Server plan

                default_backupset (str) --  Name of backupset to be set as default

                content (list)          --  List of paths to be added as content to subclient

            Returns:
                None:

            Raises:
                Exception:
                    If backup job for added content fails
        """
        self.path = content
        self.machine_obj = Machine(client_obj)
        self.log.info(f"Going to generate Test data on path - {content}")
        self.machine_obj.generate_test_data(
            file_path=f"{self.path[0]}{self.machine_obj.os_sep}Folder_{int(time.time())}",
            ascii_data_file=True,
            dirs=1,
            files=self.file_count, custom_file_name=f"Integration_File({int(time.time())}).txt")
        self.log.info("Test data generated successfully")
        self.agent = client_obj.agents.get("File System")
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.switch_default_backupset(default_backupset)
            self.agent.backupsets.delete(self.backupset_name)
        backup_set_obj = self.agent.backupsets.add(self.backupset_name)
        backup_set_obj.set_default_backupset()
        subclient_obj = backup_set_obj.subclients.get("default")
        subclient_obj.system_state_option = False
        subclient_obj.storage_policy = server_plan
        self.log.info(f"Going to add content to [{client_obj.client_name}]")
        subclient_obj.content = content
        self.log.info("Content added successfully. Starting backup job")
        job_obj = subclient_obj.backup("Full")
        self.log.info("Invoked the FS backup job with id : %s", job_obj.job_id)
        self.log.info("Going to Monitor this backup job for completion")
        if not job_obj.wait_for_completion(timeout=90):
            self.log.info("Backup job failed on storage policy. Please check logs")
            raise Exception("Backup job failed on storage policy")
        self.log.info("Backup job is finished")

    def add_fso_server(self, source=edisconstant.SourceType.BACKUP, path=""):
        """ Creates a new FSO server
            Args:
                source (enum)       -- Source type for crawl (Live source or Backedup)
                                                            Refer EdiscoveryConstants.SourceType

                path (str)          -- Path to be analyzed

            Returns:
                str                 -- actual name of the datasource

        """
        self.log.info("Going to add FSO data source")
        if source == edisconstant.SourceType.BACKUP:
            self.fso_client_obj = self.fso_obj.add_file_server(
                server_name=self.fso_client,
                data_source_name=self.ds_name,
                inventory_name=self.inv_obj.inventory_name,
                plan_name=self.plan_obj.plan_name,
                source_type=edisconstant.SourceType.BACKUP
            )
        else:
            self.path = path
            client = self.commcell.clients.get(self.fso_client)
            self.machine_obj = Machine(client)
            self.machine_obj.generate_test_data(
                file_path=f"{self.path[0]}{self.machine_obj.os_sep}Folder_{int(time.time())}",
                ascii_data_file=True,
                dirs=1,
                files=self.file_count, custom_file_name=f"Integration_File({int(time.time())}).txt")
            self.fso_client_obj = self.fso_obj.add_file_server(
                server_name=self.fso_client,
                data_source_name=self.ds_name,
                inventory_name=self.inv_obj.inventory_name,
                plan_name=self.plan_obj.plan_name,
                source_type=edisconstant.SourceType.SOURCE,
                crawl_path=path)
        self.log.info("FSO data source added successfully")
        self.all_ds_obj = self.fso_client_obj.data_sources
        self.ds_obj = self.all_ds_obj.get(self.ds_name)
        self.ds_helper.wait_for_job(self.ds_obj)
        return self.ds_obj.name

    def validate_fso_server(self, source=edisconstant.SourceType.BACKUP, path=""):
        """ Validates the FSO server added to commcell
            Args:
                source (enum)   -- Source type for crawl (Live source or Backedup)
                                                            Refer EdiscoveryConstants.SourceType

                path(str)       -- Crawl Path to be validated

            Returns:
                None:

            Raises:
                Exception:
                    If document count in server is not matching with the datasource
        """
        ds_name = self.ds_obj.data_source_name
        total_doc_in_src = 0
        if not self.all_ds_obj.has_data_source(ds_name):
            raise Exception(f"DataSource ({ds_name}) doesn't exists in FSO server")
        if source == edisconstant.SourceType.BACKUP:
            if not self.ds_obj.crawl_type != edisconstant.CrawlType.BACKUP.value:
                raise Exception(f"Crawl type is not of BACKUP")
            all_sets = self.agent.backupsets.all_backupsets
            for backup_set, _ in all_sets.items():
                if backup_set == self.backupset_name.lower():
                    self.log.info(f"Analyzing backupset - [{backup_set}] for backup files count")
                    backupset_obj = self.agent.backupsets.get(backup_set)
                    current_set_count = backupset_obj.backed_up_files_count()
                    self.log.info(f"Backup Set ({backup_set}) has [{current_set_count}] files")
                    total_doc_in_src = total_doc_in_src + current_set_count
        else:
            machine_obj = Machine(machine_name=self.fso_client, commcell_object=self.commcell)
            for src_path in path:
                files = len(machine_obj.get_files_in_path(folder_path=src_path))
                self.log.info(f"File count for path ({src_path}) is {files}")
                total_doc_in_src = total_doc_in_src + files
        self.log.info(f"Total document at source client  - {total_doc_in_src}")
        self.all_ds_obj.refresh()
        doc_in_dst = self.all_ds_obj.get_datasource_document_count(data_source=ds_name)
        if doc_in_dst != total_doc_in_src:
            raise Exception(f"Document count mismatched. Expected - {total_doc_in_src} but Actual : {doc_in_dst}")
        self.log.info("Document count validation - Success")

    def switch_default_backupset(self, default_backupset):
        """ Sets default backupset for the agent
            Args:

                default_backupset(str)  --  Name of backupset to be set as default

            Returns:
                None:
        """
        self.log.info(f"Checking if agent has backupset named [{default_backupset}]")
        if not self.agent.backupsets.has_backupset(default_backupset):
            raise Exception(f"Default backupset [{default_backupset}] not found. Please pass default backupset object")

        self.log.info(f"Backupset [{default_backupset}] is present")
        default_backupset_obj = self.agent.backupsets.get(default_backupset)
        self.log.info(f"Making backupset named [{default_backupset}] as default")
        default_backupset_obj.set_default_backupset()
        self.log.info(f"Backupset [{default_backupset}] set as default")

    def delete_backupset(self, default_backupset):
        """ Deletes the backupset associated with FSO backed up crawl datasource
            Args:

                default_backupset(str)  --  Name of backupset to be set as default

            Returns:
                None:
        """
        self.log.info(f"Trying to delete backupset [{self.backupset_name}]")
        self.log.info(f"Switching the default backupset from [{self.backupset_name}] to [{default_backupset}]")
        self.switch_default_backupset(default_backupset)
        self.log.info("Switched default backupset successfully")
        if not self.agent.backupsets.has_backupset(self.backupset_name):
            raise Exception(f"Backupset [{self.backupset_name}] is not found for deletion")
        self.agent.backupsets.delete(self.backupset_name)
        self.log.info(f"Deleted backupset [{self.backupset_name}] successfully")

    def delete_unc_backupset(self, client_obj):
        """ Deletes the backupset associated with FSO backed up crawl datasource
            Args:

                client_obj(object)  --  Client Object on which the backpset would be deleted

            Returns:
                None:
        """
        self.agent = client_obj.agents.get("File SYstem")
        backupset_name = f"{self.ds_obj.name}"
        self.log.info(f"Trying to delete backupset [{backupset_name}]")
        all_bs = self.agent.backupsets.all_backupsets
        did_delete_bs = False
        for bs in all_bs:
            self.log.info(f"Inside for loop for all backupset - \n "
                          f"Current backupset [{bs}]. Backupset to be deleted - [{backupset_name}]")
            if backupset_name.lower() in bs.lower():
                self.log.info("Backupset name matches. We are going to delete the backupset")
                self.agent.backupsets.delete(bs)
                self.log.info("Backupset deleted successfully")
                did_delete_bs = True
        if not did_delete_bs:
            raise Exception(f"Backupset [{backupset_name}] is not found for deletion")
        self.log.info(f"Deleted backupset [{backupset_name}] successfully")

    def get_collection_info_for_pruning(self):
        """ Gets the collection info needed for pruning
            Returns:
                str, str, str - collection name,
                                name of index server node,
                                query to fetch the files count on the collection,
        """
        collection_client_id = self.ds_obj.index_server_node_client_id
        is_node_client_obj = self.commcell.clients.get(collection_client_id)
        ds_id = self.ds_obj.data_source_id
        self.collection_name = self.ds_obj.computed_core_name
        self.is_node_name = is_node_client_obj.client_name
        self.query = {"data_source": ds_id, "wt": "json"}
        return self.collection_name, self.is_node_name, self.query

    def check_if_collection_pruned(self, index_server):
        """ Validates if the files in a collection is pruned
            Args:
                index_server    -- Name of the index server on which the collection exist
            Returns:
                bool            -- boolean output based on the documents presence in collection

            Raises:
                Exception:
                    If collection docs are not pruned

        """
        index_server_obj = self.commcell.index_servers.get(index_server)
        result = index_server_obj.execute_solr_query(self.collection_name,
                                                     self.is_node_name, self.query)
        self.log.info("Sending request to find the number of documents for the datasource in collection")
        if result["response"]["numFound"] > 0:
            raise Exception("Collection files still exist")
        self.log.info("Documents pruned successfully")
        return True

    def validate_audit_pruning(self):
        """ Validates the audit trail logs for pruning
                Returns:
                    None

                Raises:
                    Exception:
                        If audit trail logs for datasource pruning is missing
        """
        self.log.info(f"Validating audit trail. Datasource name: {self.ds_obj.name},"
                      f"Core Name: {self.ds_obj.computed_core_name}")
        if not self.is_pruning_audited(self.ds_obj.name, self.ds_obj.computed_core_name):
            raise Exception("Audit for datasource pruning failed")
        self.log.info("Audit info is logged properly")

    def cleanup(self):
        """ Cleans up the FSO entities such as Plan and inventory

                Returns:
                    None

                Raises:
                    Exception:
                        If plan deletion fails

                        If inventory deletion fails
        """
        self.log.info("Deleting inventory")
        self.invs_obj.delete(self.inv_obj.inventory_name)
        self.log.info("Deleting DC Plan")
        self.plans_obj.delete(self.plan_obj.plan_name)
        if self.plans_obj.has_plan(self.plan_obj.plan_name):
            raise Exception(f"DC Plan({self.plan_obj.plan_name}) didn't get deleted properly. Please check")
        if self.invs_obj.has_inventory(self.inv_obj.inventory_name):
            raise Exception(f"Inventory({self.inv_obj.inventory_name}) didn't get deleted properly. Please check")
        self.log.info("Plan and inventory deleted successfully")
        self.log.info(f"Deleting directory in path [{self.path[0]}]")
        if not self.machine_obj.remove_directory(self.path[0]):
            raise Exception(f"Directory ({self.path[0]}) didn't get deleted properly. Please check")
        self.log.info(f"Directory in path [{self.path[0]}] deleted successfully")
