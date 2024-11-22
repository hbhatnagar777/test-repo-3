# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing storage related operations in Metallic Ring

    StorageRingHelper:

        __init__()                          --  Initializes Storage Ring Helper

        start_task                          --  Starts the storage related tasks for metallic ring

        add_credentials                     --  adds credentials for creating cloud storage

        add_cloud_storage_pool              --  Adds new storage pool with provided name to the commcell

        add_storage_pool                    --  dds new storage pool with provided name to the commcell

        add_plan                            --  Adds new server plan with provided name to the commcell

        associate_dr_to_storage_policy      --  Associates DR backup to the given policy name

        set_local_dr_path                   --  Sets the local DR path for the commcell

"""

from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from cvpysdk.storage_pool import StoragePools

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class StorageRingHelper(BaseRingHelper):
    """ helper class for performing storage related operations in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.media_agents = self.commcell.media_agents
        self.sp_helper = StoragePools(self.commcell)
        self.dr_manager = self.commcell.disasterrecovery.disaster_recovery_management

    def start_task(self):
        """Starts the storage related tasks for metallic ring"""
        try:
            self.log.info("Starting Storage helper task")
            storage_info = _CONFIG.storage
            if not self.commcell.storage_pools.has_storage_pool(cs.LOCAL_STORAGE_POOL_NAME):
                self.log.info(f"Given storage pool - [{cs.LOCAL_STORAGE_POOL_NAME}] doesn't exist. Creating a new one")
                ma_clients = []
                ddb_paths = []
                mount_paths = []
                for media_agent in _CONFIG.media_agents:
                    ma_clients.append(media_agent.client_name)
                    platform = self.commcell.media_agents.get(media_agent.client_name).platform.lower()
                    if platform == cs.OSType.WINDOWS.name.lower():
                        ddb_paths.append(media_agent.ddb_path)
                        mount_paths.append(media_agent.mount_path)
                    else:
                        ddb_paths.append(media_agent.ddb_path_unix)
                        mount_paths.append(media_agent.mount_path_unix)
                self.add_storage_pool(cs.LOCAL_STORAGE_POOL_NAME, mount_paths[0], ma_clients[0],
                                            ddb_paths[0])
                self.log.info(f"Storage pool [{cs.LOCAL_STORAGE_POOL_NAME}] created successfully")
            else:
                self.log.info(f"Storage pool - [{cs.LOCAL_STORAGE_POOL_NAME}] already exists. Skip creating it")

            if not self.commcell.plans.has_plan(cs.LOCAL_SERVER_PLAN_NAME):
                self.log.info(f"Given plan with name [{cs.LOCAL_SERVER_PLAN_NAME}] doesn't exist. Creating a new one")
                self.add_plan(cs.LOCAL_SERVER_PLAN_NAME, cs.LOCAL_STORAGE_POOL_NAME)
                self.log.info(f"Plan with name [{cs.LOCAL_SERVER_PLAN_NAME}] created")
            else:
                self.log.info(f"plan - [{cs.LOCAL_SERVER_PLAN_NAME}] already exists. Skip creating it")

            self.log.info("Associating DR backup to storage policy")
            self.associate_dr_to_storage_policy(cs.LOCAL_SERVER_PLAN_NAME)
            self.log.info(f"DR backup associated to SP [{cs.LOCAL_SERVER_PLAN_NAME}]. Assigning local DR backup path")
            if self.is_linux_cs:
                self.set_local_dr_path(storage_info.local_dr_path_unix)
            else:
                self.set_local_dr_path(storage_info.local_dr_path)
            self.log.info(f"Local DR path set to [{storage_info.local_dr_path}]")
            self.log.info("Completed storage helper task. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute storage helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def add_credentials(self, cred_name, account_name, access_key, **kwargs):
        """
        adds credentials for creating cloud storage
        Args:
            cred_name(str)              -   name of the credential to be stored
            account_name(str)           -   name of the azure storage account
            access_key(str)             -   access key for storage
            ** kwargs(dict)             -   Key value pairs for supported arguments
            Supported argument values:
                owner(str)                  -   owner of the credentials
                is_user(bool)               -   Represents whether owner passed is a user or user group
                                                is_user=1 for user, is_user=0 for usergroup
                description(str)            -   description of the credentials
        """
        self.log.info(f"Request received to add credentials [{cred_name}]")
        self.commcell.credentials.add_azure_cloud_creds(cred_name, account_name, access_key, **kwargs)
        self.log.info("Credential added successfully")

    def add_cloud_storage_pool(self, storage_pool_name, container_name, media_agents, dedup_paths, **kwargs):
        """ Adds new storage pool with provided name to the commcell
                Args:
                    storage_pool_name (str)     --  name of the storage pool to be created

                    container_name (str)        --  container name to be used with storage pool

                    media_agents (list)         --  list of media agent names to be used for storage pool

                    dedup_paths (list)          --  list of paths for storing deduplication data

                    **kwargs (dict)             --  dict of keyword arguments as follows
                        username        (str)   --  azure storage credential username
                        password        (str)   --  azure storage credential password
                        credential_name (str)   --  Credential name to be used

                Returns:
                    None:

                Raises:
                    Exception:
                        If Storage Pool with given name already exist

        """
        self.log.info(f"Received request to add new storage pool : [{storage_pool_name}]")
        self.sp_helper.add_azure_storage_pool(storage_pool_name, container_name, media_agents, dedup_paths, **kwargs)
        self.log.info(f"Storage pool - [{storage_pool_name}] using azure cloud storage container created successfully")

    def add_storage_pool(self, storage_pool_name, mount_path, media_agent, dedup_path):
        """ Adds new storage pool with provided name to the commcell
                Args:
                    storage_pool_name (str) --  name of the storage pool to be created

                    mount_path (str)        --  mount path to be used with storage pool

                    media_agent (str)       --  media agent to be used for storage pool

                    dedup_path (str)        -- path for storing deduplication data

                Returns:
                    None:

                Raises:
                    Exception:
                        If Storage Pool with given name already exist

        """
        self.log.info(f"Received request to add new storage pool : [{storage_pool_name}]")
        storage_pools = self.commcell.storage_pools
        if storage_pools.has_storage_pool(storage_pool_name):
            raise Exception(f"Storage Pool with name: [{storage_pool_name}] already exist")
        self.log.info(f"Storage Pool  with name: [{storage_pool_name}] doesn't exist. Creating a new storage Pool")
        storage_pools.add(storage_pool_name, mount_path, media_agent, media_agent, dedup_path)
        self.log.info(f"Storage pool with name: [{storage_pool_name}] created successfully")

    def add_plan(self, plan_name, storage_pool_name):
        """ Adds new server plan with provided name to the commcell
                Args:
                    plan_name  (str)        --  Name of the Plan to be created

                    storage_pool_name (str) --  name of the storage pool to be used for the plan

                Returns:
                    None:

                Raises:
                    Exception:
                        If plan with given name already exist

                        If storage pool with given name does not exist

        """
        self.log.info(f"Received request to add new plan : [{plan_name}]")
        plans = self.commcell.plans
        if plans.has_plan(plan_name):
            raise Exception(f"Plan with name: [{plan_name}] already exist")
        self.commcell.storage_pools.refresh()
        if not self.commcell.storage_pools.has_storage_pool(storage_pool_name):
            raise Exception(f"Storage Pool with name: [{storage_pool_name}] does not exist")
        self.log.info(f"Plan with name: [{plan_name}] doesn't exist. Creating a new plan")
        plans.add(plan_name, cs.SERVER, storage_pool_name, sla_in_minutes=10080)
        self.log.info(f"Plan with name: [{plan_name}] created successfully")

    def associate_dr_to_storage_policy(self, policy_name):
        """
        Associates DR backup to the given policy name
        Args:
            policy_name(str)        -   Name of the policy
        """
        self.log.info(f"Associating dr backup to storage policy [{policy_name}]")
        if not self.commcell.storage_policies.has_policy(policy_name):
            raise Exception("Policy with given name doesn't exist")
        sp_object = self.commcell.storage_policies.get(policy_name)
        self.dr_manager.dr_storage_policy = sp_object
        self.log.info(f"Associated dr backup to storage policy [{policy_name}] successfully")

    def set_local_dr_path(self, path):
        """
        Sets the local DR path for the commcell
        Args:
            path(str)           -   Path for storing DR database dump
        """
        self.log.info(f"setting local DR path to [{path}]")
        if not self.dr_manager.backup_metadata_folder.lower() == path.lower():
            cs_mac_obj = Machine(self.commcell.commserv_client)
            if not cs_mac_obj.check_directory_exists(path):
                cs_mac_obj.create_directory(path)
            self.dr_manager.set_local_dr_path(path)
        self.log.info(f"DR Path set to [{path}]")


class CustomStorageRingHelper(StorageRingHelper):
    """ helper class for performing custom storage related operations in Metallic Ring"""

    def associate_dr_to_storage_policy(self, policy_name):
        pass

    def set_local_dr_path(self, path):
        pass
