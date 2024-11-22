# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Helper class for Sharepoint collection pruning related operations

    SharepointPruningHelper:

        __init__()                              --  Initialize the Sharepoint Pruning Helper object

        create_sharepoint_o365()                --  Creates Sharepoint Online V2 client

        sharepoint_run_backup                   --  Runs backup on a sharepoint client

        sharepoint_delete_client                --  Deletes the client associated to a sharepoint client

        sharepoint_delete_backupset             --  Deletes the backupset associated to a Sharepoint client

        sharepoint_switch_index_server          --  Changes the index server associated to the sharepoint client

"""
from copy import deepcopy
from dynamicindex.CollectionPruning.collection_pruning_helper import CollectionPruningHelper
from dynamicindex.utils import constants as cs


class SharepointPruningHelper(CollectionPruningHelper):
    """ contains helper class for Sharepoint collection pruning related operations"""

    def __init__(self, commcell, sp_online_object, o365_plan, site_url):
        """
        Initialize the Sharepoint Pruning Helper object
            Args:
                commcell(object)            -- instance of commcell class
                sp_online_object(object)    -- instance of sharepoint online class
                o365_plan(str)              -- Name of office365 plan
                site_url(str)               -- Site that has to be backed up
        """
        super().__init__(commcell)
        self.sp_client_object = sp_online_object
        self.log.info('Initializing sharepoint pruning helper object')
        self.sp_client_object.initialize_sp_v2_client_attributes()
        self.sp_client_object.office_365_plan = [(o365_plan,
                                                  int(self.sp_client_object.cvoperations.get_plan_obj
                                                      (o365_plan).plan_id))]
        self.sp_client_object.site_url = site_url
        self.log.info('sharepoint pruning helper object initialized')

    def create_sharepoint_o365(self):
        """
        Creates Sharepoint Online V2 client
            Returns:
                Object  -- An instance of Sharepoint Client
        """
        self.log.info('Adding new SharePoint client')
        self.sp_client_object.cvoperations.add_share_point_pseudo_client()
        self.log.info('Initiating sharepoint discover to later associate the discovered sites as content')
        self.sp_client_object.cvoperations.browse_for_sp_sites()
        self.log.info('SharePoint client object created.')
        return self.sp_client_object

    def sharepoint_run_backup(self):
        """
        Runs backup on a sharepoint client
        """
        self.log.info('Associating the content for sharepoint backup')
        self.sp_client_object.cvoperations.associate_content_for_backup(
            self.sp_client_object.office_365_plan[0][1])
        self.log.info('Content associated. Starting the backup')
        self.sp_client_object.cvoperations.run_backup()
        self.log.info(f'Backup completed successfully')

    def sharepoint_delete_client(self):
        """
        Deletes the client associated to a sharepoint client
        """
        self.log.info(f"Trying to delete sharepoint client: [{self.sp_client_object.pseudo_client_name}]")
        self.sp_client_object.cvoperations.delete_share_point_pseudo_client(self.sp_client_object.pseudo_client_name)
        self.log.info(f"Sharepoint client [{self.sp_client_object.pseudo_client_name}] deleted successfully")

    def sharepoint_delete_backupset(self):
        """
        Deletes the backupset associated to a Sharepoint client
        """
        self.log.info(f"Trying to delete sharepoint backupset")
        self.sp_client_object.cvoperations.delete_backupset()
        self.log.info(f"Sharepoint backupset deleted successfully")

    def sharepoint_switch_index_server(self, new_index_server):
        """
        Changes the index server associated to the sharepoint client
        Args:
            new_index_server  (str)    --  Name of the new index server to be associated with sharepoint client
        """
        self.log.info(f"Switching the index server to : [{new_index_server}]")
        sp_client = self.commcell.clients.get(self.sp_client_object.pseudo_client_name)
        index_server_obj = self.commcell.index_servers.get(new_index_server)
        request_json = deepcopy(cs.SP_PROPS_UPDATE_JSON)
        request_json["pseudoClientInfo"]["clientType"] = sp_client.client_type
        index_server_json = request_json["pseudoClientInfo"]["sharepointPseudoClientProperties"]["indexServer"]
        index_server_json["mediaAgentId"] = index_server_obj.index_server_client_id
        index_server_json["mediaAgentName"] = new_index_server
        sp_client.update_properties(request_json)
        self.log.info(f"Request for Index server switch to : [{new_index_server}] completed successfully")
        self.sp_client_object.index_server = new_index_server
        self.log.info(f"Switched the index server for sp client object")
