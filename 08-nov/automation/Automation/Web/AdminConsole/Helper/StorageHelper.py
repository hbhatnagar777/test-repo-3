# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Storage in AdminConsole
StorageMain : This class provides methods for storage related operations

StorageMain
===========

    add_disk_storage()              --     To add a new disk storage

    list_disk_storage               --     Get the of all the disk storage in the form of a list

    has_disk_storage()              --     Checks the existence of disk storage with the given name

    delete_disk_storage()           --     Deletes the disk storage with the given name

    disk_storage_info()             --     Returns the details of given disk storage

    add_disk_backup_location()      --     To add a new backup location to an existing disk storage

    delete_disk_backup_location()   --     Deletes the backup location on disk storage

    list_disk_backup_locations()    --     Get the of all the backup location disk storage in the form of a list

    add_media_agent_disk_storage()  --     Add media agent to backup location on disk storage

    encrypt_disk_storage()          --     To encrypt the disk storage on the selected

    decrypt_disk_storage()          --     To Decrypt the disk storage of passed disk argument

    disk_encryption_info()          --      Returns the details of given disk storage's encryption info

    list_disk_storage_associated_plans() -- Get all the associated plans to the disk storage in the form of a list

    list_disk_media_agent()          --     List media agents of a backup location on disk storage

    add_disk_media_agent()           --     Add media agents to a backup location on disk storage

    enable_disk_backup_location()    --     Enable a backup location on disk storage

    disable_disk_backup_location()    --     Disable a backup location on disk storage

    disable_disk_backup_location_for_future_backups   --   Disable a backup location for future backups on disk storage

    retire_disk_backup_location()    --     Retire a backup location  on disk storage

    delete_disk_access_path()        --     Delete access path  on certain backup location of disk storage

    disk_worm_storage_lock()              --     Enable WORM lock on disk storage

    disk_compliance_lock()                --     Enable compliance lock on disk storage

    add_cloud_storage()              --     To add a new cloud storage

    modify_retention_on_worm_cloud_storage -- Modifies retention on worm enabled cloud storage with the given name

    list_cloud_storage               --     Get all the cloud storage in the form of a list

    has_cloud_storage                --     Checks the existence of cloud storage with the given name

    delete_cloud_storage()           --     Deletes the cloud storage with the given name

    cloud_storage_info()             --     Returns the details of given cloud storage

    add_cloud_container()            --     To add a new container to an existing cloud storage

    delete_cloud_container()         --     Deletes the container on cloud storage

    list_cloud_containers()          --     Get all the container cloud storage in the form of a list

    add_media_agent_cloud_storage()  --     Add media agent to container on cloud storage

    encrypt_cloud_storage()          --     To encrypt the cloud storage on the selected

    cloud_worm_storage_lock()       --      To enable worm lock on cloud storage

    cloud_compliance_lock()         --      To enable compliance lock on cloud storage

    list_cloud_container_media_agent()  --  List media agents on a particular container

    enable_cloud_container()        --      Enable a container on cloud storage if disabled

    disable_cloud_container()       --      Disable a container on cloud storage if enabled

    disable_cloud_container_for_future_backups()    --    Disable a container for future backups on cloud storage

    retire_cloud_container()        --      Retire a container  on cloud storage

    delete_cloud_access_path()      --      Delete media agent  on certain container of cloud storage

    air_gap_protect_storage_status()            --  Retrieves the Status field value from air gap protect listing table
                                                    for air gap protect storage with the given name

    air_gap_protect_wait_for_online_status()    --  Waits until Air Gap Protect storage is fully configured;
                                                    i.e.; Status changes to 'Online'

    air_gap_protect_compliance_lock()           --  Enable compliance lock on AirGapProtect storage

    air_gap_protect_compliance_lock_enabled()   --  Checks if compliance lock is enabled on AirGapProtect storage

    has_air_gap_protect_storage()               --  Checks the existence of Air Gap Protect storage with the given name

    list_cloud_storage_associated_plans() -- Get all the associated plans to the cloud storage in the form of a list

    add_storage_onboarding_SaaS()  -- Create primary and optional secondary storage on onboarding pages

    hyperscale_add_storagepool()   -  To add a new hyperscale storagepool

    hyperscale_list_storagepool()  -  returns  all the HyperScale Storagepool in the form of a list

    hyperscale_delete_storagepool()-  Deletes the HyperScale Storagepool with the given name

    hyperscale_reconfigure_storagepool() - Reconfigure the HyperScale Storagepool with the given name

    hyperscale_storagepool_health_status() - Returns hyperscale storagepool status

    hyperscale_add_nodes()          -  To add nodes to an existing hyperscale storagepool

    hyperscale_reconfigure_add_nodes() - Reconfigure add nodes operation

    hyperscale_library_info()         -  To get the details of hyperscale storagepool

    hyperscale_refresh_node()         -   Node Refresh on hyperscale node

    hyperscale_list_nodes()           -   returns all the Nodes of  hyperscale storagepool in the form of a list

    hyperscale_node_health_status()   -    return status of a Node

    list_hyperscale_storagepool_associated_plans() - returns all the associated plans to the hyperscale storage in the
                                                    form of a list

    encrypt_hyperscale_storagepool()  -    To encrypt the Hyperscale storage pool

    hyperscale_node_disk_info()       -    To get the details of Node Bricks

    hyperscale_node_server_info()     -    To get the details of Node hardware usage

    hyperscale_replace_brick()        -    Replace brick action on a disk

    hyperscale_list_bricks()          -    returns all the bricks  of  hyperscale Node in the form of a list

    hyperscale_brick_health_status()   - 	returns brick status

"""

import time
from AutomationUtils import logger
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Storage.DiskStorage import DiskStorage
from Web.AdminConsole.Storage.DiskStorageDetails import DiskStorageDetails
from Web.AdminConsole.Storage.DiskBackupLocation import DiskBackupLocation
from Web.AdminConsole.Storage.CloudStorage import CloudStorage
from Web.AdminConsole.Storage.CloudStorageDetails import CloudStorageDetails
from Web.AdminConsole.Storage.CloudContainerDetails import CloudContainerDetails
from Web.AdminConsole.Storage.AirGapProtectStorage import AirGapProtectStorage
from Web.AdminConsole.Storage.AirGapProtectStorageDetails import AirGapProtectStorageDetails
from Web.AdminConsole.Storage.AirGapProtectContainer import AirGapProtectContainer
from Web.AdminConsole.Storage.HyperScaleStorage import HyperScaleStorage
from Web.AdminConsole.Storage.HyperScaleStorageDetails import HyperScaleStorageDetails
from Web.AdminConsole.Storage.HyperScaleNodeDetails import HyperScaleNodeDetails
from Web.AdminConsole.Storage.StorageOnboarding import StorageOnboardingSaaS
from Web.AdminConsole.Components.wizard import Wizard


class StorageMain:
    """ Admin console helper for Storage related pages """

    def __init__(self, admin_console):
        """
        Helper for storage related files

        Args:
            admin_console   (AdminConsole)    --  AdminConsole class object
        """
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__props = admin_console.props
        self.__disk = DiskStorage(self.__admin_console)
        self.__disk_details = DiskStorageDetails(self.__admin_console)
        self.__disk_backup_location = DiskBackupLocation(self.__admin_console)
        self.__cloud = CloudStorage(self.__admin_console)
        self.__cloud_details = CloudStorageDetails(self.__admin_console)
        self.__cloud_container = CloudContainerDetails(self.__admin_console)
        self.__air_gap_protect = AirGapProtectStorage(self.__admin_console)
        self.__air_gap_protect_details = AirGapProtectStorageDetails(self.__admin_console)
        self.__air_gap_protect_container = AirGapProtectContainer(self.__admin_console)
        self.__hyperscale_storage = HyperScaleStorage(self.__admin_console)
        self.__hyperscale_storage_details = HyperScaleStorageDetails(self.__admin_console)
        self.__hyperscale_node_details = HyperScaleNodeDetails(self.__admin_console)
        self.__table = Rtable(self.__admin_console)
        self.log = logger.get_log()
        self.__storage_onb_helper = StorageOnboardingSaaS(self.__admin_console)
        self.__wizard = Wizard(admin_console)

    def add_disk_storage(self, disk_storage_name, media_agent, backup_location, saved_credential_name=None,
                         username=None, password=None, deduplication_db_location=None):
        """
        To add a new disk storage

        Args:
            disk_storage_name (str)     -- Name of the disk storage to be created

            media_agent     (str)       -- Media agent to create storage on

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            backup_location (str)       -- local/network path for the backup

            deduplication_db_location (str | list[str]) -- local path(s) for the deduplication db

        **Note** MediaAgent should be installed prior, for creating a new backup location for storage.
                To use saved credentials for network path it should be created prior using credential manager,
        """
        self.__navigator.navigate_to_disk_storage()
        if saved_credential_name:
            backup_location_details = [{'media_agent': media_agent,
                                        'backup_location': backup_location,
                                        'saved_credential_name': saved_credential_name,
                                        }]
        elif username and password:
            backup_location_details = [{'media_agent': media_agent,
                                        'backup_location': backup_location,
                                        'username': username,
                                        'password': password}]
        else:
            backup_location_details = [{'media_agent': media_agent,
                                        'backup_location': backup_location,
                                        }]

        if deduplication_db_location:
            if isinstance(deduplication_db_location, str):
                deduplication_db_location_details = [{'media_agent': media_agent,
                                                      'deduplication_db_location': deduplication_db_location}]
            elif isinstance(deduplication_db_location, list):
                deduplication_db_location_details = [{'media_agent': media_agent,
                                                      'deduplication_db_location': db_location}
                                                     for db_location in deduplication_db_location
                                                     ]
            else:
                deduplication_db_location_details = None
        else:
            deduplication_db_location_details = None

        self.__disk.add_disk_storage(disk_storage_name, backup_location_details, deduplication_db_location_details)
        self.log.info('Successfully added disk storage: %s', disk_storage_name)

    def add_disk_storage_with_multiple_locations(self, disk_storage_name, backup_location_details,
                                                 deduplication_db_location_details=None):
        """
        To add a new disk storage with multiple locations

        disk_storage_name(str) : Name of the disk storage to be created

         backup_location_details (list): List of dictionaries containing backup location details to add multiple backup
                                         locations.
                E.g. - backup_location_details = [{'media_agent': "sample_media_agent1",
                                                    'backup_location': "sample_backup_location",
                                                    'saved_credential_name': "sample_saved_credential"},
                                                    {'media_agent': "sample_media_agent1",
                                                     'backup_location': "sample_backup_location",
                                                     'username': "sample_username",
                                                     'password': "sample_password}]

        deduplication_db_location_details (list): List of dictionaries containing DDB location details to add
                                                  multiple deduplication db locations.
                E.g. - deduplication_db_location_details = [{'media_agent': "sample_media_agent",
                                                            'deduplication_db_location': "sample_ddb_location"}]
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.add_disk_storage(disk_storage_name, backup_location_details, deduplication_db_location_details)
        self.log.info('Successfully added disk storage: %s', disk_storage_name)

    def list_disk_storage(self, fetch_all=False):
        """Get the of all the disk storage in the form of a list

            Returns:
                disk_storage_list    (list)  --  all disk storage
        """
        self.__navigator.navigate_to_disk_storage()
        return self.__disk.list_disk_storage(fetch_all=fetch_all)

    def has_disk_storage(self, disk_storage):
        """Checks the existence of disk storage with the given name

            Args:
                disk_storage (str) -- name of the disk storage

            Returns (bool):
                True if disk storage exist, else False

        """

        self.__navigator.navigate_to_disk_storage()
        res = self.__table.is_entity_present_in_column(column_name="Name", entity_name=disk_storage)
        self.__table.clear_search()
        return res

    def delete_disk_storage(self, disk_storage):
        """
        Deletes the disk storage with the given name

        Args:
            disk_storage (str) -- name of the disk storage to be removed
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.delete_disk_storage(disk_storage)
        self.log.info('Successfully deleted disk storage: %s', disk_storage)

    def disk_storage_info(self, disk_storage):
        """
        Returns the details of given disk storage

            Args:
                disk_storage    (str)       -- Name of the disk storage to get details
            Returns:
                info    (dict)  -- details of disk storage
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        return self.__disk_details.storage_info()

    def add_disk_backup_location(self, disk_storage, media_agent, backup_location, saved_credential_name=None,
                                 username=None, password=None):
        """
        To add a new backup location to an existing disk storage

        Args:
            disk_storage    (str)       -- Name of the disk storage to add new backup location

            media_agent     (str)       -- Media agent to create storage on

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            backup_location (str)       -- local/network path for the backup

        **Note** MediaAgent should be installed prior, for creating a backup location for storage.
                To use saved credentials for network path it should be created prior using credential manager,
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.add_backup_location(media_agent, backup_location, saved_credential_name, username, password)
        self.log.info('Successfully added backup location: %s', backup_location)

    def delete_disk_backup_location(self, disk_storage, mount_path):
        """
        Deletes the backup location on disk storage

        Args:
            disk_storage    (str)  --   name of the disk storage to delete backup location

            mount_path (str)   --  name of the backup location to delete
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.delete_mount_path(mount_path)
        self.log.info('Successfully deleted backup location: %s', mount_path)

    def list_disk_backup_locations(self, disk_storage):
        """
        Get the of all the backup location disk storage in the form of a list

            Args:
                disk_storage    (str)       -- Name of the disk storage to get all the backup location
            Returns:
                    backup_location_list    (list)  --  all backup locations on disk
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        return self.__disk_details.list_mount_paths()

    def add_media_agent_disk_storage(self, disk_storage, mount_path, media_agent_list,
                                     use_option_from="DiskStorageDetails"):
        """
        Add media agent to backup location on disk storage

            Args:
                disk_storage       (str)  --  name of the disk storage to add media agent

                mount_path   (str)   --  backup location on which given media agent will be added

                media_agent_list  (list)  --  list of media agents to be added

                use_option_from(str)     -- add media agent from disk storage page/backup location page
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        if use_option_from == "DiskStorageDetails":
            self.__disk_details.add_media_agent(mount_path, media_agent_list)
        else:
            self.__disk_details.access_mount_path(mount_path)
            self.__disk_backup_location.add_media_agent(media_agent_list)
        self.log.info('Successfully added media agents: %s', media_agent_list)

    def list_disk_storage_associated_plans(self, disk_storage):
        """
        Get all the associated plans to the disk storage in the form of a list

            Args:
                disk_storage    (str)       -- Name of the disk storage to get all the associated plans
            Returns:
                    associated_plan_list (list)  --  all backup locations on disk
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        return self.__disk_details.list_associated_plans

    def encrypt_disk_storage(self, disk_storage, cipher=None, key_length=None, key_management_server=None):
        """
        To encrypt the disk storage on the selected

        Args:
            disk_storage   (str)   -- Name of the disk storage to be encrypted

            cipher      (str)   -- Encryption method to be used

            key_length  (str)   -- Key length for the chosen cipher

            key_management_server   (str)   --  Key management server for the storage pool
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.encrypt_storage(cipher, key_length, key_management_server)
        self.log.info('Successfully encrypted the disk storage: %s', disk_storage)

    def decrypt_disk_storage(self, disk_storage):
        """
            To decrypt the disk storage on the selected

            Args:
                disk_storage   (str)   -- Name of the disk storage to be decrypted

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.decrypt_storage()
        self.log.info('Successfully decrypted the disk storage: %s', disk_storage)


    def disk_encryption_info(self, disk_storage):
        """
        Returns the details of given disk storage's encryption info

            Args:
                disk_storage    (str)   -- Name of the disk storage to get details

            Returns:
                info            (dict)  -- Details of disk storage
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        return self.__disk_details.storage_encryption_info()

    def worm_disk_storage_lock(self, disk_storage, retention_period):
        """
        Enable WORM lock on disk storage

            Args:
                disk_storage        (str)   -- Name of the disk storage

                retention_period           (dict):     How long the retention is to be set
                    Format: {'period': 'day(s)','value': '365'}
                        'period' (str):Retention time period unit
                            Allowed values: 'day(s)' , 'month(s)', 'year(s)'
                    'value' (str):      Retain for that many number of time period

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.worm_storage_lock(retention_period)

    def disk_compliance_lock(self, disk_storage):
        """
        Enable compliance lock on disk storage

            Args:
                disk_storage        (str)   -- Name of the disk storage
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.compliance_lock()

    def list_disk_media_agent(self, disk_storage, mount_path):
        """
        List media agents of a backup location on disk storage

            Args:
                disk_storage       (str)  --  name of the disk storage to list media agents

                mount_path   (str)   --  backup location on which media agents need to be listed
        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.access_mount_path(mount_path)
        return self.__disk_backup_location.list_media_agent()

    def enable_disk_backup_location(self, disk_storage, mount_path, use_option_from="DiskStorageDetails"):
        """
        Enable a backup location on disk storage

            Args:
               disk_storage       (str)  --  name of the disk storage with backup location

               mount_path   (str)   --  backup location which needs to be enabled

               use_option_from (str)   -- add media agent from disk storage page/backup location page

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        if use_option_from == "DiskStorageDetails":
            self.__disk_details.enable_mount_path(mount_path)
        else:
            self.__disk_details.access_mount_path(mount_path)
            self.__disk_backup_location.enable_backup_location()

    def disable_disk_backup_location(self, disk_storage, mount_path, use_option_from="DiskStorageDetails"):
        """
        Disable a backup location on disk storage

            Args:
               disk_storage       (str)  --  name of the disk storage with backup location

               mount_path   (str)   --  backup location which needs to be disabled

               use_option_from -- add media agent from disk storage page/backup location page

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        if use_option_from == "DiskStorageDetails":
            self.__disk_details.disable_mount_path(mount_path)
        else:
            self.__disk_details.access_mount_path(mount_path)
            self.__disk_backup_location.disable_backup_location()

    def enable_disk_backup_location_for_future_backups(self, disk_storage, mount_path):
        """
        Enable a backup location for future backups on disk storage

            Args:
               disk_storage       (str)  --  name of the disk storage with backup location

               mount_path   (str)   --  backup location that is to be disabled

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.access_mount_path(mount_path)
        self.__disk_backup_location.enable_backup_location_for_future_backups()

    def disable_disk_backup_location_for_future_backups(self, disk_storage, mount_path):
        """
        Disable a backup location for future backups on disk storage

            Args:
               disk_storage       (str)  --  name of the disk storage with backup location

              mount_path   (str)   --  mount_path that is to be disabled

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.access_mount_path(mount_path)
        self.__disk_backup_location.disable_backup_location_for_future_backups()

    def enable_retire_disk_backup_location(self, disk_storage, mount_path):
        """
        Enable retire a backup location  on disk storage

            Args:
               disk_storage       (str)  --  name of the disk storage with backup location

               mount_path   (str)   --  backup location that needs to be retired

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.access_mount_path(mount_path)
        self.__disk_backup_location.enable_retire_backup_location()

    def disable_retire_disk_backup_location(self, disk_storage, mount_path):
        """
        Disable retire a backup location  on disk storage

            Args:
               disk_storage       (str)  --  name of the disk storage with backup location

               mount_path   (str)   --  backup location that needs to be retired

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.access_mount_path(mount_path)
        self.__disk_backup_location.disable_retire_backup_location()

    def delete_disk_access_path(self, disk_storage, mount_path, media_agent):
        """
        Delete media agent  on certain backup location of disk storage

           Args:
               disk_storage       (str)  --  name of the disk storage

               mount_path   (str)   --  backup location on which given access path will be deleted

               media_agent      (list)  --  media agents that needs to be deleted

        """
        self.__navigator.navigate_to_disk_storage()
        self.__disk.access_disk_storage(disk_storage)
        self.__disk_details.access_mount_path(mount_path)
        self.__disk_backup_location.delete_access_path(media_agent)

    def add_cloud_storage(self, cloud_storage_name, media_agent, cloud_type, server_host, container, storage_class=None,
                          saved_credential_name=None, username=None, password=None, deduplication_db_location=None,
                          region=None, auth_type=None, cred_details=None):
        """
        To add a new cloud storage

        Args:
            cloud_storage_name (str)    -- Name of the cloud storage to be created

            media_agent     (str)       -- Media agent to create storage on

            cloud_type      (str)       -- type of the cloud storage server

            server_host     (str)       -- cloud server host name

            container       (str)       -- container to be associated with the storage

            storage_class   (str)       --  storage class to be associated with the container

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            deduplication_db_location (str) -- local path for the deduplication db

            region          (str)       -- region of the cloud storage

            auth_type       (str)       -- type of authentication

            cred_details (dict) -- Dictionary containing attributes for saving creds as per auth_type
                Eg. - {'accountName':xyz, 'accessKeyId': xyz}

        **Note** MediaAgent should be installed prior, for creating a new storage,
                To use saved credentials it should be created prior using credential manager.
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.add_cloud_storage(cloud_storage_name, media_agent, cloud_type, server_host, container,
                                       storage_class, saved_credential_name, username, password,
                                       deduplication_db_location, region, auth_type, cred_details)
        self.log.info('Successfully added cloud storage: %s', cloud_storage_name)

    def modify_retention_on_worm_cloud_storage(self, cloud_storage, ret_number, ret_unit):
        """Modifies retention on worm enabled cloud storage with the given name

            Args:
                cloud_storage (str) - name of the storage

                ret_number (int)    :   number of days/months, etc. to retain

                ret_unit (str)    :   Unit to use (Day(s), Month(s), etc.

        **Note** Worm lock should be enabled to modify retention

        """

        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        notification_text = self.__cloud.modify_retention_on_worm_cloud_storage(ret_unit=ret_unit,
                                                                                ret_number=ret_number)
        return notification_text

    def list_cloud_storage(self, fetch_all=False):
        """Get the of all the cloud storage in the form of a list

            Returns:
                cloud_storage_list    (list)  --  all cloud storage
        """
        self.__navigator.navigate_to_cloud_storage()
        return self.__cloud.list_cloud_storage(fetch_all=fetch_all)

    def has_cloud_storage(self, cloud_storage):
        """Checks the existence of cloud storage with the given name

            Args:
                cloud_storage (str) -- name of the cloud storage

            Returns (bool):
                True if cloud storage exist, else False

        """

        self.__navigator.navigate_to_cloud_storage()
        res = self.__table.is_entity_present_in_column(column_name="Name", entity_name=cloud_storage)
        self.__table.clear_search()
        return res

    def delete_cloud_storage(self, cloud_storage):
        """
        Deletes the cloud storage with the given name

        Args:
            cloud_storage (str) -- name of the cloud storage to be removed
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.action_delete(cloud_storage)
        self.log.info('Successfully deleted cloud storage: %s', cloud_storage)

    def cloud_storage_info(self, cloud_storage):
        """
        Returns the details of given cloud storage

            Args:
                cloud_storage    (str)       -- Name of the cloud storage to get details
            Returns:
                info    (dict)  -- details of cloud storage
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        return self.__cloud_details.storage_info()

    def add_cloud_container(self, cloud_storage, media_agent, server_host, container, storage_class=None,
                            saved_credential_name=None, username=None, password=None, auth_type=None):
        """
        To add a new container to an existing cloud storage

        Args:
            cloud_storage       (str)  --  name of the cloud storage to add container

            media_agent     (str)       -- Media agent to create storage on

            server_host     (str)       -- cloud server host name

            container       (str)       -- container to be associated with the storage

            storage_class   (str)       --  storage class to be associated with the container

            saved_credential_name (str) -- saved credential name created using credential manager

            username        (str)       -- username for the network path

            password        (str)       -- password for the network path

            auth_type       (str)       -- type of authentication

        **Note** MediaAgent should be installed prior, for creating a storage,
                To use saved credentials it should be created prior using credential manager.
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.add_container(media_agent, server_host, container, storage_class, saved_credential_name,
                                           username, password, auth_type)
        self.log.info('Successfully added container: %s', container)

    def delete_cloud_container(self, cloud_storage, mount_path):
        """
        Deletes the container on cloud storage

        Args:
            cloud_storage    (str)  --   name of the cloud storage to delete container

            mount_path (str)   --  name of the container to delete
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.delete_mount_path(mount_path)
        self.log.info('Successfully deleted container: %s', mount_path)

    def list_cloud_containers(self, cloud_storage):
        """
        Get the of all the container cloud storage in the form of a list

            Args:
                cloud_storage    (str)       -- Name of the cloud storage to get all the container
            Returns:
                    container_list    (list)  --  all containers on cloud
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        return self.__cloud_details.list_mount_paths()

    def add_media_agent_cloud_storage(self, cloud_storage, mount_path, media_agent_list,
                                      use_option_from="CloudStorageDetails"):
        """
        Add media agent to container on cloud storage

            Args:
                cloud_storage       (str)  --  name of the cloud storage to add media agent

                mount_path   (str)   --  container on which given media agent will be added

                media_agent_list  (list)  --  list of media agents to be added

                use_option_from   (str)        -- add media agent from cloud storage/container page
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        if use_option_from == "CloudStorageDetails":
            self.__cloud_details.add_media_agent(mount_path, media_agent_list)
        else:
            self.__cloud_details.access_mount_path(mount_path)
            self.__cloud_container.add_media_agent(media_agent_list)
        self.log.info('Successfully added media agents: %s', media_agent_list)

    def list_cloud_storage_associated_plans(self, cloud_storage):
        """
        Get all the associated plans to the cloud storage in the form of a list

            Args:
                cloud_storage    (str)       -- Name of the cloud storage to get all the associated plans
            Returns:
                associated_plan_list (list)  --  all plans associated with cloud storage
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        return self.__cloud_details.list_associated_plans()

    def encrypt_cloud_storage(self, cloud_storage, cipher=None, key_length=None, key_management_server=None):
        """
        To encrypt the cloud storage on the selected

        Args:
            cloud_storage   (str)   -- Name of the cloud storage to be encrypted

            cipher      (str)   -- Encryption method to be used

            key_length  (str)   -- Key length for the chosen cipher

            key_management_server   (str)   --  Key management server for the storage
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.encrypt_storage(cipher, key_length, key_management_server)
        self.log.info('Successfully encrypted the cloud storage: %s', cloud_storage)

    def cloud_encryption_info(self, cloud_storage):
        """
        Returns the details of given cloud storage's encryption info

            Args:
                cloud_storage    (str)   -- Name of the cloud storage to get details

            Returns:
                info            (dict)  -- Details of cloud storage encryption
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        return self.__cloud_details.storage_encryption_info()

    def cloud_worm_storage_lock(self, cloud_storage, retention_period):
        """
        To enable worm lock on cloud storage

        Args:
            cloud_storage   (str)   -- Name of the cloud storage to be encrypted

            retention_period           (dict):     How long the retention is to be set
                Format: {'period': 'day(s)','value': '365'}
                    'period' (str):Retention time period unit
                        Allowed values: 'day(s)' , 'month(s)', 'year(s)'
                'value' (str):      Retain for that many number of time period

        """

        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.worm_storage_lock(retention_period)

    def cloud_compliance_lock(self, cloud_storage):
        """
        To enable compliance lock on cloud storage

        Args:
            cloud_storage   (str)   -- Name of the cloud storage to be encrypted
        """

        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.compliance_lock()

    def list_cloud_container_media_agent(self, cloud_storage, mount_path):
        """
        List media agents on a particular container

            Args:
               cloud_storage       (str)  --  name of the cloud storage with container

               mount_path   (str)   --  container that is to be accessed

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.access_mount_path(mount_path)
        self.__cloud_container.list_media_agent()

    def enable_cloud_container(self, cloud_storage, mount_path, use_option_from="CloudStorageDetails"):
        """
        Enable a container on cloud storage if disabled

            Args:
               cloud_storage       (str)  --  name of the cloud storage with container

               mount_path   (str)   --  container that is to be enabled

               use_option_from (str)   -- enable media agent from cloud storage page/container page
        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        if not use_option_from == "CloudStorageDetails":
            self.__cloud_details.enable_mount_path(mount_path)
        else:
            self.__cloud_details.access_mount_path(mount_path)
            self.__cloud_container.enable_container()

    def disable_cloud_container(self, cloud_storage, mount_path, use_option_from="CloudStorageDetails"):
        """
        Disable a container on cloud storage if enabled

            Args:
               cloud_storage       (str)  --  name of the cloud storage with container

               mount_path   (str)   --  container that is to be disabled

               use_option_from    -- add media agent from cloud storage page/container page

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        if not use_option_from == "CloudStorageDetails":
            self.__cloud_details.disable_mount_path(mount_path)
        else:
            self.__cloud_details.access_mount_path(mount_path)
            self.__cloud_container.disable_container()

    def enable_cloud_container_for_future_backups(self, cloud_storage, mount_path):
        """
        Enable a container for future backups on cloud storage

            Args:
               cloud_storage       (str)  --  name of the cloud storage with container

               mount_path   (str)   --  container that is to be enabled

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.access_mount_path(mount_path)
        self.__cloud_container.enable_container_for_future_backups()

    def disable_cloud_container_for_future_backups(self, cloud_storage, mount_path):
        """
        Disable a container for future backups on cloud storage

            Args:
               cloud_storage       (str)  --  name of the cloud storage with container

               mount_path   (str)   --  container that is to be disabled

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.access_mount_path(mount_path)
        self.__cloud_container.disable_container_for_future_backups()

    def enable_retire_cloud_container(self, cloud_storage, mount_path):
        """
        Enable retire a container  on cloud storage

            Args:
                cloud_storage       (str)  --  name of the  cloud_storage with container

               mount_path   (str)   --  container that needs to be retired

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.access_mount_path(mount_path)
        self.__cloud_container.enable_retire_container()

    def disable_retire_cloud_container(self, cloud_storage, mount_path):
        """
        Disable retirement of a container  on cloud storage

            Args:
                cloud_storage       (str)  --  name of the  cloud_storage with container

               mount_path   (str)   --  container to perform disable retire operation

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.access_mount_path(mount_path)
        self.__cloud_container.disable_retire_container()

    def delete_cloud_access_path(self, cloud_storage, mount_path, media_agent):
        """
        Delete media agent  on certain container of cloud storage

           Args:
               cloud_storage       (str)  --  name of the cloud storage

               mount_path   (str)   --  container on which given access path will be deleted

               media_agent      (list)  --  media agents that needs to be deleted

        """
        self.__navigator.navigate_to_cloud_storage()
        self.__cloud.select_cloud_storage(cloud_storage)
        self.__cloud_details.access_mount_path(mount_path)
        self.__cloud_container.delete_access_path(media_agent)

    def add_air_gap_protect_storage(self, air_gap_protect_storage_name, media_agent,
                                    region, storage_type=None, storage_class=None,
                                    deduplication_db_location=None):
        """
        To add a new air gap protect storage

        Args:
            air_gap_protect_storage_name (str)     -- Name of the air gap protect storage
                                                                to be created

            media_agent     (str)       -- Media agent to create storage on

            region (str)                -- Region / Location of storage

            storage_type     (str)      -- Cloud vendor type (eg- Microsoft Azure Storage)

            storage_class       (str)   -- storage class associated with the storage

            deduplication_db_location (str) -- local path for the deduplication db

        **Note** MediaAgent should be installed prior for storage.
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.add_air_gap_protect_storage(air_gap_protect_storage_name,
                                                           media_agent, region, storage_type,
                                                           storage_class, deduplication_db_location)
        self.log.info('Successfully added metallic recovery reserve storage: %s', air_gap_protect_storage_name)

    def list_air_gap_protect_storage(self):
        """Get  all air gap protect storage in the form of a list

            Returns:
                air_gap_protect_list    (list)  --  all air gap protect storage
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        return self.__air_gap_protect.list_air_gap_protect_storage()

    def delete_air_gap_protect_storage(self, air_gap_protect_storage):
        """
        Deletes the air gap protect storage with the given name

        Args:
            air_gap_protect_storage (str) -- name of the air gap protect storage to be removed
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.delete_air_gap_protect_storage(air_gap_protect_storage)
        self.log.info('Successfully deleted metallic recovery reserve storage: %s', air_gap_protect_storage)

    def air_gap_protect_info(self, air_gap_protect_storage):
        """
        Returns the details of given air gap protect storage

            Args:
                air_gap_protect_storage    (str)       -- Name of the air gap protect storage to get details
            Returns:
                info    (dict)  -- details of air gap protect storage
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        return self.__air_gap_protect_details.storage_info()

    def air_gap_protect_storage_status(self, air_gap_protect_storage, navigate_to=True):
        """Retrieves the Status field value from air gap protect listing table for air gap protect storage with
            the given name

            Args:
                air_gap_protect_storage (str)   -   name of the storage

                navigate_to             (bool)  -   if True (default) navigates to Air Gap Protect storage page
                                                    if False avoids redundant navigation operation

            Returns:
                string                          -   Status of air gap protect storage
        """
        self.log.info('Getting Air Gap Protect storage status for %s' % air_gap_protect_storage)
        if navigate_to:
            self.__navigator.navigate_to_air_gap_protect_storage()
        status = self.__air_gap_protect.air_gap_protect_storage_status(air_gap_protect_storage)
        self.log.info('Air Gap Protect storage status [%s]' % status)
        return status

    def air_gap_protect_wait_for_online_status(self, air_gap_protect_storage, wait_time=3, total_attempts=10):
        """Waits until Air Gap Protect storage is fully configured; i.e.; Status changes to 'Online'

            Args:
                air_gap_protect_storage (str)   - Name of air gap protect storage
                wait_time               (int)   - Number of minutes to wait before next attempt

                total_attempts          (int)   - Total number of attempts before raising error

            Raises:
                CVTestStepFailure   - If timed out
        """
        online = self.__props['label.online']

        status = self.air_gap_protect_storage_status(air_gap_protect_storage)
        self.log.info('Air Gap Protect Storage %s, status: %s' % (air_gap_protect_storage, status))
        is_online = online in status

        for attempt in range(0, total_attempts):
            if is_online:
                break

            self.log.info('Attempt: [%s/%s]; Waiting for %s minutes' % (attempt + 1, total_attempts, wait_time))
            time.sleep(60 * wait_time)

            status = self.air_gap_protect_storage_status(air_gap_protect_storage, navigate_to=False)
            self.log.info('Air Gap Protect Storage %s, status: %s' % (air_gap_protect_storage, status))
            is_online = online in status
        else:
            raise Exception('Failed to validate status after %s attempts' % total_attempts)

        self.log.info('Air Gap Protect storage is online [took: %s attempt(s)]' % attempt)

    def air_gap_protect_compliance_lock(self, air_gap_protect_storage):
        """Enable compliance lock on AirGapProtect storage

            Args:
                air_gap_protect_storage (str)   -   name of the storage
        """
        self.log.info('Enabling compliance lock on Air Gap Protect storage %s' % air_gap_protect_storage)
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.compliance_lock()
        self.log.info('Successfully enabled compliance lock on Air Gap protect storage %s' % air_gap_protect_storage)

    def air_gap_protect_is_compliance_lock_enabled(self, air_gap_protect_storage):
        """Checks if compliance lock is enabled on AirGapProtect storage

            Args:
                air_gap_protect_storage (str)   -   name of the storage

            Returns:
                bool                            - True if compliance lock is enabled
                                                  False if compliance lock is not enabled
        """
        self.log.info('Checking status of Compliance Lock on Air Gap Protect storage %s' % air_gap_protect_storage)
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        is_enabled = self.__air_gap_protect_details.is_compliance_lock_enabled()
        if is_enabled:
            self.log.info('Compliance Lock is enabled on Air Gap Protect storage %s' % air_gap_protect_storage)
        else:
            self.log.info('Compliance Lock is disabled on Air Gap Protect storage %s' % air_gap_protect_storage)
        return is_enabled

    def add_air_gap_protect_container(self, air_gap_protect_storage, media_agent, location, license=None,
                                      storage_class=None, replication=None):
        """
        To add a new container to an existing air gap protect storage

        Args:
            air_gap_protect_storage (str)   -- Name of the air gap protect storage to add container

            media_agent     (str)       -- Media agent used to add container

            license         (str)       -- Type of license used to add container

            location        (str)       -- Location of container

            storage_class   (str)       --  storage class to be associated with the container

            replication       (str)       -- replication associated with container

        **Note** MediaAgent should be installed prior
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.add_container(media_agent, location, license,
                                                     storage_class, replication)

    def delete_air_gap_protect_container(self, air_gap_protect_storage, mount_path):
        """
        Deletes the container on air gap protect storage

        Args:
            air_gap_protect_storage    (str)  --   name of the air gap protect storage to delete container

            mount_path (str)   --  name of the container to delete
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.delete_mount_path(mount_path)
        self.log.info('Successfully deleted container: %s', mount_path)

    def list_air_gap_protect_containers(self, air_gap_protect_storage):
        """
        Get  all the containers on air gap protect storage in the form of a list

            Args:
                air_gap_protect_storage    (str)       -- Name of the air gap protect storage to get all the container
            Returns:
                    container_list    (list)  --  all containers on air gap protect
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        return self.__air_gap_protect_details.list_mount_paths()

    def add_media_agent_air_gap_protect_storage(self, air_gap_protect_storage, mount_path, media_agent_list,
                                                use_option_from="AirGapProtectStorageDetails"):
        """
        Add media agent to container on air gap protect storage

            Args:
                air_gap_protect_storage       (str)  --  name of the air gap protect storage to add media agent

                mount_path   (str)   --  container on which given media agent will be added

                media_agent_list  (list)  --  list of media agents to be added

                use_option_from   (str)        -- add media agent from air gap protect storage/container page
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        if use_option_from == "AirGapProtectStorageDetails":
            self.__air_gap_protect_details.add_media_agent(mount_path, media_agent_list)
        else:
            self.__air_gap_protect_details.access_mount_path(mount_path)
            self.__air_gap_protect_container.add_media_agent(media_agent_list)
        self.log.info('Successfully added media agents: %s', media_agent_list)

    def list_air_gap_protect_storage_associated_plans(self, air_gap_protect_storage):
        """
        Get all the associated plans to the air gap protect storage in the form of a list

            Args:
                air_gap_protect_storage    (str)       -- Name of the air gap protect storage to get all the associated
                                                          plans
            Returns:
                associated_plan_list (list)  --  all plans associated with  air gap protect storage
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        return self.__air_gap_protect_details.list_associated_plans()

    def encrypt_air_gap_protect_storage(self, air_gap_protect_storage, cipher=None, key_length=None,
                                        key_management_server=None):
        """
        To encrypt the air gap protect storage on the selected

        Args:
            air_gap_protect_storage   (str)   -- Name of the air gap protect storage to be encrypted

            cipher      (str)   -- Encryption method to be used

            key_length  (str)   -- Key length for the chosen cipher

            key_management_server   (str)   --  Key management server for the storage
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.encrypt_storage(cipher, key_length, key_management_server)
        self.log.info('Successfully encrypted the air gap protect storage: %s', air_gap_protect_storage)

    def air_gap_protect_encryption_info(self, air_gap_protect_storage):
        """
        Returns the details of given air gap protect storage's encryption info

            Args:
                air_gap_protect_storage    (str)   -- Name of the air gap protect storage to get details

            Returns:
                info            (dict)  -- Details of air gap protect storage encryption
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        return self.__air_gap_protect_details.storage_encryption_info()

    def list_air_gap_protect_container_media_agent(self, air_gap_protect_storage, mount_path):
        """
        List media agents on a particular container

            Args:
               air_gap_protect_storage       (str)  --  name of the air gap protect storage with container

               mount_path   (str)   --  container that is to be accessed
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.access_mount_path(mount_path)
        self.__air_gap_protect_container.list_media_agent()

    def enable_air_gap_protect_container(self, air_gap_protect_storage, mount_path,
                                         use_option_from="AirGapProtectStorageDetails"):
        """
       Enable a container on air gap protect storage if disabled

           Args:
              air_gap_protect_storage       (str)  --  name of the air gap protect storage with container

              mount_path   (str)   --  container that is to be enabled

              use_option_from (str)   -- enable media agent from air gap protect storage page/container page
       """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        if not use_option_from == "AirGapProtectStorageDetails":
            self.__air_gap_protect_details.enable_mount_path(mount_path)
        else:
            self.__air_gap_protect_details.access_mount_path(mount_path)
            self.__air_gap_protect_container.enable_container()

    def disable_air_gap_protect_container(self, air_gap_protect_storage, mount_path,
                                          use_option_from="AirGapProtectStorageDetails"):
        """
           Disable a container on air gap protect storage if disabled

               Args:
                  air_gap_protect_storage       (str)  --  name of the air gap protect storage with container

                  mount_path   (str)   --  container that is to be enabled

                  use_option_from (str)   -- disable media agent from air gap protect storage page/container page
        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        if not use_option_from == "AirGapProtectStorageDetails":
            self.__air_gap_protect_details.disable_mount_path(mount_path)
        else:
            self.__air_gap_protect_details.access_mount_path(mount_path)
            self.__air_gap_protect_container.disable_container()

    def enable_air_gap_protect_container_for_future_backups(self, air_gap_protect_storage, mount_path):
        """
        Enable a container for future backups on air gap protect storage

            Args:
               air_gap_protect_storage       (str)  --  name of the air gap protect storage with container

               mount_path   (str)   --  container that is to be enabled

        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.access_mount_path(mount_path)
        self.__air_gap_protect_container.enable_container_for_future_backups()

    def disable_air_gap_protect_container_for_future_backups(self, air_gap_protect_storage, mount_path):
        """
        Disable a container for future backups on air gap protect storage

            Args:
               air_gap_protect_storage       (str)  --  name of the air gap protect storage with container

               mount_path   (str)   --  container that is to be disabled

        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.access_mount_path(mount_path)
        self.__air_gap_protect_container.disable_container_for_future_backups()

    def enable_retire_air_gap_protect_container(self, air_gap_protect_storage, mount_path):
        """
        Enable retire a container  on air gap protect storage

            Args:
                air_gap_protect_storage       (str)  --  name of the air gap protect with container

               mount_path   (str)   --  container that needs to be retired

        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.access_mount_path(mount_path)
        self.__air_gap_protect_container.enable_retire_container()

    def disable_retire_air_gap_protect_container(self, air_gap_protect_storage, mount_path):
        """
        Disable retire a container  on air gap protect storage

            Args:
                air_gap_protect_storage       (str)  --  name of the air gap protect with container

               mount_path   (str)   --  container to perform disable retire operation

        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.access_mount_path(mount_path)
        self.__air_gap_protect_container.disable_retire_container()

    def delete_air_gap_protect_access_path(self, air_gap_protect_storage, mount_path, media_agent):
        """
        Delete media agent  on certain container of air gap protect storage

           Args:
               air_gap_protect_storage       (str)  --  name of the air gap protect storage

               mount_path   (str)   --  container on which given access path will be deleted

               media_agent      (list)  --  media agents that needs to be deleted

        """
        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__air_gap_protect.access_air_gap_protect_storage(air_gap_protect_storage)
        self.__air_gap_protect_details.access_mount_path(mount_path)
        self.__air_gap_protect_container.delete_access_path(media_agent)

    def has_air_gap_protect_storage(self, air_gap_protect_storage):
        """Checks the existence of Air Gap Protect storage with the given name

            Args:
                air_gap_protect_storage (str) -- name of the AGP storage

            Returns (bool):
                True if AGP storage exist, else False

        """

        self.__navigator.navigate_to_air_gap_protect_storage()
        res = self.__table.is_entity_present_in_column(column_name="Name", entity_name=air_gap_protect_storage)
        self.__table.clear_search()
        return res

    def add_storage_onboarding_SaaS(self,
                                    primary_storage,
                                    secondary_storage=None,
                                    use_only_on_premises_storage=False):
        """
        Create primary and optional secondary storage.
        Provide inputs of primary and secondary storage through dict based on cloud_type.

        Args:
            primary_storage(dict)   -- Details required to configure/select primary storage

            secondary_storage(dict) -- Details required to configure/select secondary storage

            use_only_on_premises_storage(bool)  --  True if use only on premises storage
                                                    if not False(default)

                Format for above dict's: {'type'(str) : 'storage_type',
                                         'name'(str) : 'storage_name',
                                         'details'(dict) : 'storage_details'}

                Eg for disk : {'type' : 'disk',
                               'name' : 'sample_name'
                               'details' : {'gateway_name': 'sample_backup_gateway_name',
                                            'backup_location': 'sample_backup_location',
                                            'username': 'sample_username',
                                            'password': 'sample_password'}}

                    The above is for creation of local storage with network path. We don't
                     pass username and password for local path

                Eg for cloud(Air Gap Protect) : {'type' : 'cloud',
                                                'name' : None,
                                                'details' : {'cloud_type': 'sample_cloud_type',
                                                             'storage_provider': 'sample_storage_provider',
                                                             'storage_class': 'sample_storage_class',
                                                             'region': 'sample_region'}}

            Note:
                1. Format for primary_storage and secondary_storage is similar based on storage type.

                2. Required information to pass based on cloud type.
                    'Air Gap Protect': ['cloud_type', 'storage_provider', 'storage_class', 'region'],
                    'Oracle Cloud Infrastructure Object Storage': ['cloud_type', 'storage_class', 'region',
                                                           'saved_credentials', 'bucket'],
                    'Microsoft Azure Storage': ['cloud_type', 'storage_class', 'region', 'saved_credentials',
                                        'container'],
                    'Amazon S3': ['cloud_type', 'storage_class', 'region', 'saved_credentials', 'bucket']
        """
        wizard_step = self.__storage_onb_helper.current_onboarding_wizard_step()
        if wizard_step == 'Local Storage':
            self.log.info('Current Wizard Step: Local Storage')
            if primary_storage['type'] == 'disk':
                if 'details' in primary_storage:
                    self.log.info('Creating new local storage : %s', primary_storage['name'])
                    self.__storage_onb_helper.add_local_storage(primary_storage['name'], primary_storage['details'])
                    self.log.info('Successfully created new local storage : %s', primary_storage['name'])
                else:
                    self.log.info("Selecting local storage :%s", primary_storage['name'])
                    self.__storage_onb_helper.select_local_storage(primary_storage['name'])
                    self.log.info("Local storage is selected,name:%s", primary_storage['name'])
                self.__storage_onb_helper.click_next()
                self.__admin_console.check_error_message()
                if not use_only_on_premises_storage:
                    if 'details' in secondary_storage:
                        if secondary_storage['details']['cloud_type'] == 'Air Gap Protect':
                            self.log.info('Creating Air Gap Protect secondary cloud storage')
                            self.__storage_onb_helper.add_cloud_storage(cloud_storage_details=
                                                                        secondary_storage['details'],
                                                                        addingSecondCloudStorage=False)
                            self.log.info('Successfully created Air Gap Protect cloud storage as secondary storage')
                        else:
                            self.log.info('Creating %s secondary cloud storage: %s',
                                          secondary_storage['details']['cloud_type'],
                                          secondary_storage['name'])
                            self.__storage_onb_helper.add_cloud_storage(cloud_storage_name=secondary_storage['name'],
                                                                        cloud_storage_details=
                                                                        secondary_storage['details'],
                                                                        addingSecondCloudStorage=False)
                            self.log.info('Successfully created new %s secondary cloud storage, name: %s',
                                          secondary_storage['details']['cloud_type'],
                                          secondary_storage['name'])
                    else:
                        self.log.info('Selecting secondary cloud storage : %s', secondary_storage['name'])
                        self.__storage_onb_helper.select_cloud_storage(secondary_storage['name'],
                                                                       addingSecondCloudStorage=False)
                        self.log.info('Secondary cloud storage is selected,name: %s', secondary_storage['name'])
                    self.__storage_onb_helper.click_next()
                    self.__admin_console.check_error_message()
                else:
                    self.__storage_onb_helper.use_on_premises_storage_only()
                    self.__storage_onb_helper.click_next()
                    self.__admin_console.check_error_message()

            if primary_storage['type'] == 'cloud':
                self.__storage_onb_helper.backup_to_cloud_storage_only()
                self.__storage_onb_helper.click_next()
                if 'details' in primary_storage:
                    if primary_storage['details']['cloud_type'] == 'Air Gap Protect':
                        self.log.info('Creating Air Gap Protect primary cloud storage')
                        self.__storage_onb_helper.add_cloud_storage(cloud_storage_details=primary_storage['details'],
                                                                    addingSecondCloudStorage=False)
                        self.log.info('Successfully created Air Gap Protect cloud storage as primary storage')
                    else:
                        self.log.info('Creating %s primary cloud storage : %s',
                                      primary_storage['details']['cloud_type'],
                                      primary_storage['name'])
                        self.__storage_onb_helper.add_cloud_storage(cloud_storage_name=primary_storage['name'],
                                                                    cloud_storage_details=primary_storage['details'],
                                                                    addingSecondCloudStorage=False)
                        self.log.info('Successfully created new %s primary cloud storage,name : %s',
                                      primary_storage['details']['cloud_type'],
                                      primary_storage['name'])
                else:
                    self.log.info('Selecting primary cloud storage : %s', primary_storage['name'])
                    self.__storage_onb_helper.select_cloud_storage(primary_storage['name'],
                                                                   addingSecondCloudStorage=False)
                    self.log.info('Primary cloud storage is selected,name: %s', primary_storage['name'])

                if secondary_storage is not None:
                    if secondary_storage['type'] == 'cloud':
                        self.__storage_onb_helper.enable_secondary_copy()
                        if 'details' in secondary_storage:
                            if secondary_storage['details']['cloud_type'] == 'Air Gap Protect':
                                self.log.info('Creating Air Gap Protect secondary cloud storage')
                                self.__storage_onb_helper.add_cloud_storage(cloud_storage_details=
                                                                            secondary_storage['details'],
                                                                            addingSecondCloudStorage=True)
                                self.log.info('Successfully created Air Gap Protect cloud storage as secondary storage')
                            else:
                                self.log.info('Creating %s secondary cloud storage: %s',
                                              secondary_storage['details']['cloud_type'],
                                              secondary_storage['name'])
                                self.__storage_onb_helper.add_cloud_storage(cloud_storage_name=
                                                                            secondary_storage['name'],
                                                                            cloud_storage_details=
                                                                            secondary_storage['details'],
                                                                            addingSecondCloudStorage=True)
                                self.log.info('Successfully created new %s secondary cloud storage, name: %s',
                                              secondary_storage['details']['cloud_type'],
                                              secondary_storage['name'],
                                              addingSecondCloudStorage=True)
                        else:
                            self.log.info('Selecting secondary cloud storage : %s', secondary_storage['name'])
                            self.__storage_onb_helper.select_cloud_storage(secondary_storage['name'],
                                                                           addingSecondCloudStorage=True)
                            self.log.info('Secondary cloud storage is selected,name: %s', secondary_storage['name'])
                self.__storage_onb_helper.click_next()
                self.__admin_console.check_error_message()

        elif wizard_step == 'Cloud Storage':
            self.log.info('Current Wizard Step: Cloud Storage')
            if primary_storage['type'] == 'cloud':
                if 'details' in primary_storage:
                    if primary_storage['details']['cloud_type'] == 'Air Gap Protect':
                        self.log.info('Creating Air Gap Protect primary cloud storage')
                        self.__storage_onb_helper.add_cloud_storage(cloud_storage_details=primary_storage['details'],
                                                                    addingSecondCloudStorage=False)
                        self.log.info('Successfully created Air Gap Protect cloud storage as primary storage')
                    else:
                        self.log.info('Creating %s primary cloud storage : %s',
                                      primary_storage['details']['cloud_type'],
                                      primary_storage['name'])
                        self.__storage_onb_helper.add_cloud_storage(cloud_storage_name=primary_storage['name'],
                                                                    cloud_storage_details=primary_storage['details'],
                                                                    addingSecondCloudStorage=False)
                        self.log.info('Successfully created new %s primary cloud storage,name : %s',
                                      primary_storage['details']['cloud_type'],
                                      primary_storage['name'])
                else:
                    self.log.info('Selecting primary cloud storage : %s', primary_storage['name'])
                    self.__storage_onb_helper.select_cloud_storage(primary_storage['name'],
                                                                   addingSecondCloudStorage=False)
                    self.log.info('Primary cloud storage is selected,name: %s', primary_storage['name'])
                if secondary_storage is not None:
                    if secondary_storage['type'] == 'cloud':
                        self.__storage_onb_helper.enable_secondary_copy()
                        if 'details' in secondary_storage:
                            if secondary_storage['details']['cloud_type'] == 'Air Gap Protect':
                                self.log.info('Creating Air Gap Protect secondary cloud storage')
                                self.__storage_onb_helper.add_cloud_storage(cloud_storage_details=
                                                                            secondary_storage['details'],
                                                                            addingSecondCloudStorage=True)
                                self.log.info('Successfully created Air Gap Protect cloud storage as secondary storage')
                            else:
                                self.log.info('Creating %s secondary cloud storage: %s',
                                              secondary_storage['details']['cloud_type'],
                                              secondary_storage['name'])
                                self.__storage_onb_helper.add_cloud_storage(cloud_storage_name=
                                                                            secondary_storage['name'],
                                                                            cloud_storage_details=
                                                                            secondary_storage['details'],
                                                                            addingSecondCloudStorage=True)
                                self.log.info('Successfully created new %s secondary cloud storage, name: %s',
                                              secondary_storage['details']['cloud_type'],
                                              secondary_storage['name'])
                        else:
                            self.log.info('Selecting secondary cloud storage : %s', secondary_storage['name'])
                            self.__storage_onb_helper.select_cloud_storage(secondary_storage['name'],
                                                                           addingSecondCloudStorage=True)
                            self.log.info('Secondary cloud storage is selected,name: %s', secondary_storage['name'])
                self.__storage_onb_helper.click_next()
                self.__admin_console.check_error_message()
            else:
               raise Exception('Unsupported storage type')

        else:
            raise Exception('Unsupported wizard Step, supported wizard steps are Local Storage and Cloud Storage.')

    def hyperscale_add_storagepool(self, hyperscale_storagepool_name, media_agents):
        """
        To add a new hyperscale storagepool

        Args:
            hyperscale_storagepool_name (str)     -- Name of the disk storage to be created

            media_agents  (str)       -- Media agent to create storage on

        ** Note : Atleast three media Agent should present,
         MediaAgent should be available for pool creation
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.add_hyperscale_storagepool(hyperscale_storagepool_name, media_agents)
        self.log.info("Successfully added Hyperscale Storage pool")

    def hyperscale_list_storagepool(self):
        """
        Get  all the HyperScale Storagepools in the form of a list

        Returns: list --  all HyperScale Storagepools
        """
        self.__navigator.navigate_to_hyperscale_storage()
        return self.__hyperscale_storage.list_hyperscale_storagepool()

    def hyperscale_delete_storagepool(self, hyperscale_storagepool_name):
        """
         Deletes the HyperScale Storagepool with the given name
         Args:
         hyperscale_storagepool_name (str) - name of the storagepool to be removed
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.delete_hyperscale_storagepool(hyperscale_storagepool_name)
        self.log.info(f"Successfully deleted the storagepool {hyperscale_storagepool_name}")

    def hyperscale_reconfigure_storagepool(self, hyperscale_storagepool_name):
        """
                Reconfigure the HyperScale Storagepool with the given name

                Args:
                    hyperscale_storagepool_name (str) - name of the storagepool to get reconfigured
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.reconfigure_hyperscale_storagepool(hyperscale_storagepool_name)
        self.log.info(f"Successfully reconfigured the storagepool {hyperscale_storagepool_name}")

    def hyperscale_storagepool_health_status(self, hyperscale_storagepool_name):
        """Checks storagepool is present iff present

        Args:
            hyperscale_storagepool_name (str) - name of the storagepool

        Return (str) : Status - online/offline
        """
        self.__navigator.navigate_to_hyperscale_storage()
        return self.__hyperscale_storage.storagepool_health_status(hyperscale_storagepool_name)

    def hyperscale_add_nodes(self, hyperscale_storagepool_name, hyperscale_nodes):
        """
        To add nodes to an existing hyperscale storagepool

        Args:
            hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
            hyperscale_nodes     (List)            -- List of nodes for scaleout

        **Note** Nodes we are adding should be available to join to the StoragePool,
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.add_nodes(hyperscale_nodes)
        self.log.info(f'Successfully added nodes to the storagepool : {hyperscale_storagepool_name}')

    def hyperscale_reconfigure_add_nodes(self, hyperscale_storagepool_name):
        """
            Reconfigure add nodes operation
            Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.reconfigure_add_nodes()
        self.log.info(f'Successfully triggered reconfigure storagepool at add nodes :'
                      f' {hyperscale_storagepool_name}')

    def hyperscale_library_info(self, hyperscale_storagepool_name):
        """
        To get the details of hyperscale storagepool
        Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
        Returns:
                info    (dict)  -- details of Disk Library
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        return self.__hyperscale_storage_details.library_info(hyperscale_storagepool_name)

    def hyperscale_refresh_node(self, hyperscale_storagepool_name, hyperscale_node):
        """
        Node Refresh on hyperscale node

            Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
                hyperscale_node (str)   --  name of the node to refresh
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.refresh_node(hyperscale_node)
        self.log.info(f'Successfully triggered refresh node on : {hyperscale_node}')

    def hyperscale_list_nodes(self, hyperscale_storagepool_name):
        """
        Get all the Nodes of  hyperscale storagepool in the form of a list
        Args :
            hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool

        Returns:
                Nodes    (list)  --  all Nodes of a storagepool
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        return self.__hyperscale_storage_details.list_nodes()

    def hyperscale_node_health_status(self, hyperscale_storagepool_name, hyperscale_node):
        """Checks nodes is present iff present return status : online/offline
        Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
                hyperscale_node (str)   --  name of the node
         Return (str) : Status - online/offline
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        return self.__hyperscale_storage_details.nodes_health_status(hyperscale_node)

    def list_hyperscale_storagepool_associated_plans(self, hyperscale_storagepool_name):
        """
        Get all the associated plans to the hyperscale storage in the form of a list

            Args:
                hyperscale_storagepool_name   (str)       -- Name of the hyperscale storagepool to get all the
                                                            associated plans
            Returns:
                    associated_plan_list (list)  --  associated plans list
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        return self.__hyperscale_storage_details.list_associated_plans()

    def encrypt_hyperscale_storagepool(self, hyperscale_storagepool_name, cipher=None, key_length=None,
                                       key_management_server=None):
        """
        To encrypt the Hyperscale storage pool

        Args:
            hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool to be encrypted

            cipher      (str)   -- Encryption method to be used

            key_length  (str)   -- Key length for the chosen cipher

            key_management_server   (str)   --  Key management server for the storage pool
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.encrypt_storage(cipher, key_length, key_management_server)
        self.log.info(f'Successfully encrypted the hyperscale storagepool: {hyperscale_storagepool_name}')

    def hyperscale_node_disks_info(self, hyperscale_storagepool_name, hyperscale_node):
        """
        To get the details of Node Bricks
        Args:
            hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
            hyperscale_node               (str)   -- Name of the Hyperscale Node

        Returns:
                info    (dict)  -- details of Node Disks
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.access_hyperscale_node(hyperscale_node)
        return self.__hyperscale_node_details.node_disk_info()

    def hyperscale_node_server_info(self, hyperscale_storagepool_name, hyperscale_node):
        """
        To get the details of Node hardware usage
        Args:
            hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
            hyperscale_node               (str)   -- Name of the Hyperscale Node
        Returns:
                info    (dict)  -- details of Node hardware usage
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.access_hyperscale_node(hyperscale_node)
        return self.__hyperscale_node_details.node_server_info()

    def hyperscale_replace_brick(self, hyperscale_storagepool_name, hyperscale_node, brick):
        """
        Replace brick action on a disk

            Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
                hyperscale_node               (str)   -- Name of the Hyperscale Node
                brick (str)   --  name of the brick to replace
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.access_hyperscale_node(hyperscale_node)
        self.__hyperscale_node_details.replace_brick(brick)
        self.log.info(f'Successfully triggered replace brick action on : {brick}')

    def hyperscale_list_bricks(self, hyperscale_storagepool_name, hyperscale_node):
        """
        Get all the bricks  of  hyperscale Node in the form of a list
            Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
                hyperscale_node               (str)   -- Name of the Hyperscale Node
            Returns:
                    Nodes    (list)  --  all Bricks of a Node
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.access_hyperscale_node(hyperscale_node)
        return self.__hyperscale_node_details.list_bricks()

    def hyperscale_brick_health_status(self, hyperscale_storagepool_name, hyperscale_node, brick):
        """Checks brick is present iff present return status
            Args:
                hyperscale_storagepool_name   (str)   -- Name of the hyperscale_storagepool
                hyperscale_node               (str)   -- Name of the Hyperscale Node
                brick (str)   --  name of the brcik to replace
           Return (str) : Status of a brick
        """
        self.__navigator.navigate_to_hyperscale_storage()
        self.__hyperscale_storage.access_hyperscale_storagepool(hyperscale_storagepool_name)
        self.__hyperscale_storage_details.access_hyperscale_node(hyperscale_node)
        return self.__hyperscale_node_details.brick_health_status(brick)
