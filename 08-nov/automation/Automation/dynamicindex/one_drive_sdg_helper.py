# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for OneDrive sensitive data governance related operations

    OneDriveSDGHelper:

        __init__()                              --  Initialize the OneDriveSDGHelper object

        generate_sensitive_files()              --  Performs data generation and upload of sensitive files
                                                    to onedrive online user

        create_client()                         --  Creates OneDrive client

        init_od_client_entities()               --  Initializes the onedrive client entities

        add_users()                             --  Adds a list of users to OneDrive client for backup

        run_backup()                            --  Runs backup on the OncDrive client

        perform_and_validate_restore()          --  Performs restore of the files backed up to media and validates the
                                                    restored files

        delete_client()                         --  Deletes the given onedrive client

        validate_index_reuse()                  --  Checks whether the index server is being reused as
                                                    part of data governance job

"""
import copy
import time
from Application.CloudApps import constants as cloud_apps_constants
from AutomationUtils import logger
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.utils import constants as cs
from dynamicindex.utils.activateutils import ActivateUtils

_ONEDRIVE_CONFIG_DATA = get_config().DynamicIndex.Activate.OneDrive


class OneDriveSDGHelper:
    """ contains helper class for OneDrive sensitive data governance related operations"""

    def __init__(self, commcell, client_name=None):
        """
        Initialize the OneDriveSDGHelper object
        Args:
            commcell    -   Instance of commcell class
            client_name -   Name of onedrive client
        """
        self.commcell = commcell
        self.cvcloud_object = None
        self.agent = None
        self.instance = None
        self.backupset = None
        self.client = None
        if client_name is not None:
            self.client = self.commcell.get(client_name)
            self.init_od_client_entities()
        self.ds_helper = DataSourceHelper(self.commcell)
        self.activate_utils = ActivateUtils()
        self.log = logger.get_log()

    def generate_sensitive_files(self, db_path=None):
        """
        Performs generation and upload of sensitive files to onedrive online user
        Args:
            db_path:       Database file path
        """
        self.log.info(f'Starting the data generator tool for OneDrive Online')
        self.activate_utils.run_data_generator(_ONEDRIVE_CONFIG_DATA.OneDriveAPI, cs.ONE_DRIVE, db_path)
        self.log.info(f'Data generation completed successfully')

    def create_client(self, client_name, server_plan, **kwargs):
        """
        Creates OneDrive client
        Args:
            client_name(str)        --  Name of the client to be created
            server_plan(str)        --  Name of the Server plan to be used
        **kwargs(dict)      --  Dictionary of other parameters to be used
            azure_directory_id(str) --  Azure directory id to be used for connecting to onedrive cloud
            azure_app_id(str)       --  Azure Application id to be used for connecting to onedrive cloud
            azure_app_key_id(str)   --  Azure Application Key to be used for connecting to onedrive cloud
            index_server(str)       --  Name of the index server to be used
            access_nodes_list(list) --  List of access nodes to be used
        Returns:
            Client(object)          --  Instance of client class that was created
        """
        self.log.info(f'Creating a new client with name [{client_name}]')
        self.commcell.clients.\
            add_onedrive_for_business_client(client_name=client_name,
                                   server_plan=server_plan,
                                   azure_directory_id=kwargs.get('azure_directory_id'),
                                   azure_app_id=kwargs.get('azure_app_id'),
                                   azure_app_key_id=kwargs.get('azure_app_key_id'),
                                   index_server=kwargs.get('index_server'),
                                   access_nodes_list=kwargs.get('access_nodes_list'))
        self.client = self.commcell.clients.get(client_name)

        self.log.info(f'New client Created - [{client_name}]')
        self.init_od_client_entities()
        return self.client

    def init_od_client_entities(self):
        """
        Initializes the onedrive client entities
        """
        if self.agent is None:
            self.log.info(f'Initializing onedrive agent - [{cloud_apps_constants.ONEDRIVE_AGENT}]')
            self.agent = self.client.agents.get(cloud_apps_constants.ONEDRIVE_AGENT)
        if self.instance is None:
            self.log.info(f'Initializing onedrive instance - [{cloud_apps_constants.ONEDRIVE_INSTANCE}]')
            self.instance = self.agent.instances.get(cloud_apps_constants.ONEDRIVE_INSTANCE)
        if self.backupset is None:
            self.log.info(f'Initializing onedrive backupset - [{cloud_apps_constants.ONEDRIVE_BACKUPSET}]')
            self.backupset = self.instance.backupsets.get(cloud_apps_constants.ONEDRIVE_BACKUPSET)
        self.log.info(f'All onedrive entities initialize')

    def add_users(self, users, o365_plan, cloud_connector):
        """
        Adds a list of users to OneDrive client for backup
        Args:
            users(list)             --  list of users to be added for backup
            o365_plan(str)          --  Name of Office365 plan to be used
            cloud_connector(object) --  Instance of Cloud Connector class
        """
        self.log.info(f'Request received to add the following users for backup [{users}]')
        self.cvcloud_object = cloud_connector
        self.log.info('Waiting for discovery to complete')
        self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()
        self.log.info(f'Discovery complete. Trying to add the following users for backup - [{users}]')
        self.init_od_client_entities()
        subclient = self.backupset.subclients.get(cloud_apps_constants.ONEDRIVE_SUBCLIENT)
        subclient.add_users_onedrive_for_business_client(users, o365_plan)
        self.log.info(f'Users added successfully - [{users}]')

    def run_backup(self, admin_commcell=None):
        """
        Runs backup on the oncdrive client
        Args:
            admin_commcell(object)    --    Admin Commcell object to perform solr query check for playback completion
        Returns:
            job_id      --  ID of the completed backup job
        """
        job = self.run_backup_only()
        self.log.info(f'Backup job completed - [{str(job.job_id)}]. Checking for playback completion')
        if admin_commcell is not None:
            self.cvcloud_object.cvoperations.commcell = admin_commcell
        self.cvcloud_object.cvoperations.check_playback_completion(job.job_id)
        self.log.info('Playback completed successfully')
        if admin_commcell is not None:
            self.cvcloud_object.cvoperations.commcell = self.commcell
        return job.job_id

    def run_backup_only(self):
        """
                Runs only backup on the oncdrive client
                Returns:
                    job     --  job object of the completed backup job
                """
        self.log.info('Request received to run backup')
        backup_level = constants.backup_level.INCREMENTAL.value
        self.log.info(f'Setting backup level to incremental [{backup_level}]')
        job = self.client.backup_all_users_in_client()
        self.log.info(f'Backup job submitted - [{str(job.job_id)}]')
        self.cvcloud_object.cvoperations.check_job_status(job=job, backup_level_tc=backup_level)
        self.log.info(f'Backup job completed - [{str(job.job_id)}].')
        return job

    def perform_and_validate_restore(self, users, proxy_client, file_count=5):
        """
        Performs restore of the files backed up to media and validates the restored files
        Args:
            users(list)             --  list of users to be restored
            proxy_client(str)       --  Access node to which the files will be restored
            file_count(int)         --  Count of files to be validated against restored files
        """
        self.log.info(f'Request received to run disk restore for user: {users} to client : [{proxy_client}]')
        restore_dir = f'{_ONEDRIVE_CONFIG_DATA.RESTORE_DIR}_{str(int(time.time()))}'
        disk_restore = self.client.disk_restore(users,
                                                proxy_client,
                                                restore_dir)
        self.log.info('Restore job submitted. Waiting for restore to complete')
        self.cvcloud_object.cvoperations.check_job_status(job=disk_restore, backup_level_tc=cs.RESTORE_LEVEL)
        self.log.info('Restore complete. Validating the restored files')
        machine = Machine(self.commcell.clients.get(proxy_client))
        file_list = machine.get_files_in_path(restore_dir)
        if len(file_list) >= file_count:
            self.log.info("Count of files restored is greater than or equal to the actual files uploaded. "
                          f"Restored count: [{len(file_list)}]. Upload file count: [{file_count}]")
        else:
            self.log.info("Count of files restored is not equal to the actual files uploaded. "
                          f"Restored count: [{len(file_list)}]. Upload file count: [{file_count}]")
            raise Exception("Restore validation failed")
        machine.remove_directory(restore_dir)
        self.log.info(f'Successfully removed the restore directory [{restore_dir}]')

    def delete_client(self, client_name):
        """
        Deletes the given onedrive client
        Args:
            client_name(str)        --  Name of the client
        """
        self.log.info(f'Request received to remove client - [{client_name}]')
        if self.commcell.clients.has_client(client_name):
            self.commcell.clients.delete(client_name)
        self.log.info(f"Successfully deleted client - [{client_name}]")

    def validate_index_reuse(self, index_server, job_id):
        """
        Checks whether the index server is being reused as part of data governance job
        Args:
            index_server(str)       --  Name of the index server
            job_id(int)             --  Backup job ID
        Returns:
            Bool                    -- Boolean value whether or not the index server is reused
        """
        self.init_od_client_entities()
        self.log.info('Request received to validate index reuse for OneDrive data governance operation')
        backupset_guid = self.backupset.properties.get("backupSetEntity", {}).get("backupsetGUID", "")
        ds_name = f"{cs.ONEDRIVE_INDEX}{backupset_guid}"
        collection_name, _ = self.ds_helper.get_datasource_collection_name(ds_name)
        select_query = copy.deepcopy(cs.DOCUMENT_CI_EE_SUCCESS)
        select_query[cs.FIELD_JOB_ID] = job_id
        op_query = cs.DOCUMENT_CI_EE_STATUS
        is_obj = self.commcell.index_servers.get(index_server)
        self.log.info(f'Got the needed information for validating index reuse. Collection Name - [{collection_name}], '
                      f'Select Query - [{select_query}], Optional Query - [{op_query}]')
        resp = is_obj.execute_solr_query(collection_name, select_dict=select_query, op_params=op_query)
        self.log.info(f'Response received for the query is - [{resp}]')
        document_count = resp[cs.RESPONSE_PARAM][cs.NUM_FOUND_PARAM]
        document_count_db = ActivateUtils.db_get_total_files_count(_ONEDRIVE_CONFIG_DATA.TestDataSQLiteDBPath)
        if document_count != document_count_db:
            self.log.info('Number of documents in index and test db doesnt match -'
                          f' DB count [{document_count_db}], Document Count - [{document_count}]')
            return False
        self.log.info('Number of documents in index and test db matched -'
                      f' DB count [{document_count_db}], Document Count - [{document_count}]')
        ci_state = resp[cs.FACET_COUNTS_PARAM][cs.FACET_FIELDS_PARAM][cs.CONTENT_INDEXING_STATUS]
        self.log.info(f'CI state response - [{ci_state}]')
        if int(ci_state[0]) != 1 or int(ci_state[1]) != document_count:
            self.log.info('Number of documents CIed is not same as the documents that are backed up')
            return False
        self.log.info('Number of documents CIed is same as the documents that are backed up')
        ca_state = resp[cs.FACET_COUNTS_PARAM][cs.FACET_FIELDS_PARAM][cs.CA_STATE]
        self.log.info(f'CA state response - [{ca_state}]')
        if int(ca_state[0]) != 1 or int(ca_state[1]) != document_count:
            self.log.info('Number of documents analyzed is not same as the documents that are backed up')
            return False
        self.log.info('Number of documents analyzed is same as the documents that are backed up. Validation successful')
        return True
