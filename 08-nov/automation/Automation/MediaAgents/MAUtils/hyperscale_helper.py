# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import json
from math import ceil
from pathlib import Path
import shutil
import sys
import tarfile
import time
import ipaddress
import re
from operator import itemgetter
from typing import List
import paramiko
from paramiko import ChannelException, SSHClient
from paramiko.ssh_exception import NoValidConnectionsError
import yaml
import py7zr
from lxml import etree
from datetime import datetime
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.pyping import ping
from AutomationUtils.unix_machine import UnixMachine
from cvpysdk.storage import MediaAgents
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from cvpysdk.deployment.install import Install
from cvpysdk.job import Job
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.mediaagentconstants import HYPERSCALE_CONSTANTS
from VirtualServer.VSAUtils import HypervisorHelper
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages, InstallUpdateOptions


class LogLine:
    """
    A class which stores information that is used in log verification
    """

    def __init__(self, text, interval=None, tries=None, fixed_string=None, last=None):
        """Creates a new instance of LogLine

            Args:

                text         (str)  -- The text in the log

                interval     (int)  -- The time to sleep between consecutive checks
                                       Use None for default

                tries        (int)  -- The number of retry attempts
                                       Use None for default

                fixed_string (bool) -- Used for verbatim search (True) or pattern search (False)
                                       Use None for default

                last         (bool) -- Whether to match the last occurrence from all matches
                                       Use None for default

        """
        self.text = text
        self.interval = interval
        self.tries = tries
        self.fixed_string = fixed_string
        self.last = last

    def __str__(self):
        """String representation
        """
        return self.text

    def __repr__(self):
        """Instance representation
        """
        return self.__str__(self)


class HyperScaleHelper:
    """

        Hyperscale helper library for DB based and REST based functionalities

        This file contains a class named hyperscale_helper that can be used to carry out
        all hyperscale related operations.

        The instance of this class can be used to perform various operations on a
        Hyperscale Storage Pool like:

        hyperscale_helper
        =================

        __init__()                  -- initialize object of the class

        execute_update_query()      -- Executes update query on CSDB

        get_storage_pool_details()  -- Gets StoragePool Details from the MMSDSStoragePool table

        get_all_bricks()            -- Gets flags, BrickHealth, BlockDeviceHealth and DeviceOsPath
            for all bricks associated with a storage pool for a particular MA

        get_all_bricks_for_hostid() -- Gets flags, BrickHealth, BlockDeviceHealth and DeviceOsPath
            for all bricks associated with a particular MA

        get_brick_daemon_for_brick()    -- Check if brick daemon is present for the hyperscale brick

        get_all_nodes()             -- Gets a list of MAs associated with a particular Storage Pool

        check_brick_health_status() -- Checks the flag, blockdevicehealth and brickhealth
        values for all bricks for a given MA

        get_host_id()               -- Returns the hostid of the MA

        wait_for_completion()       -- Check if hyperscale storage pool creation
        or expansion operation has completed or failed

        add_nodes()                 -- Add 3 more nodes to horizontally expand a setup by 1 block

        create_storage_pool()       -- Create a hyperscale storage pool containing 3 nodes

        delete_storage_pool()       -- Deletes a hyperscale storage pool

        get_associated_storage_policies()   -- Get a list of Storage Policies associated
        to a hyperscale Storage pool's GDSP

        check_if_storage_pool_is_present()  -- Check if s hyperscale storage pool is present or not

        get_associated_mas()        -- Get all MAs associated with a hyperscale storage pool

        clean_up_ma()               -- Cleans up all data disks and peer files from an MA

        reassociate_all_associated_subclients() -- Reassociates all subclients associated
        with a storage policy to none assigned

        clean_up_storage_pool()     -- Cleans up all entries left by a pre-existing storage pool

        check_brick_flag_status()   -- Check if the health status is proper for a particular
        MA's bricks or not

        is_gluster_metadata_present_in_csdb()   -- Checks if CSDB contains the gluster metadata entry for the MA.

        is_gluster_services_online()    -- to check gluster services are up and running

        gluster_volume_status()     -- to know the status of gluster volume

        check_peer_status()         -- to check the peer connectivity

        get_gluster_peer_status()   --  Returns gluster peer status for a MA

        restart_services()          --  Restarts Commvault services for a client

        verify_restored_data()      --  Performs the verification after restore

        run_until_success()         --  Runs command for specified number of times

        search_log_line()           --  Search text/pattern in a log file

        get_active_files_store()    --  Return active file store

        check_identical_operation_output()  --  Runs same operation across multiple MAs for equality.

        check_identical_output()    --  Runs same command across multiple MAs for equality.

        is_remote_cache_present()   --  Returns whether remote cache is present or not

        populate_remote_cache()     --  Populates the remote cache with Unix RPMs

        verify_log_lines()          -- Verifies the list of LogLine instances

        verify_logs()               -- Verifies the list of logs

        get_lines_in_log_file()     -- Finds number of lines in a log file present on given MA

        get_or_create_policy()      -- Gets or creates the storage policy from name

        check_if_service_is_running()   -- Checks if a service is in desired state or not across MediaAgents

        wait_for_ping_result_to_be()    -- Pings a host until the given result is obtained

        wait_for_reboot()           -- Waits for the media agent to reboot

        upgrade_hedvig_get_upgrade_sequence()   -- Parses the logs to figure out the node sequence used for upgrade

        upgrade_hedvig_monitor_initial_logs()   -- Verifies the hedvig pre-upgrade logs

        upgrade_hedvig_verify_action_recap()    -- Verifies the action recap failure count is zero

        upgrade_hedvig_monitor_upgrade_logs()   -- Verifies the hedvig upgrade logs

        upgrade_hedvig_monitor_final_logs()     -- Verifies the hedvig upgrade end logs

        upgrade_os_monitor_prereq_logs()        -- Verifies the prerequisites logs (before pressing enter)

        upgrade_os_monitor_initial_logs()       -- Verifies the pre-upgrade logs

        upgrade_os_should_proceed()     -- Checks if the upgrade proceeds or not

        upgrade_os_monitor_yum_logs()   -- Verifies the yum logs on the MA machine

        upgrade_os_monitor_node_logs()  -- Verifies the logs for the node being upgraded

        upgrade_os_monitor_remote_cache_logs()  -- Verifies the logs for the remote cache node

        get_hedvig_cluster_name()       -- Gets the hedvig cluster name

        verify_hedvig_services_are_up() -- Verifies if hedvig services are up

        verify_nfsstat_output()         -- Verifies nfsstat output

        verify_df_kht_nfs4_output()     -- Verifes df -kht nfs4 output

        get_killed_commvault_processes()        -- Retrieves the list of killed commvault processes for a media agent

        verify_commvault_service_and_processes_are_up() -- Verifies if commvault service and processes are up

        stop_commvault_services()       -- Stops the commvault services on the MAs

        determine_remote_caches()       -- From a list of MAs, returns remote cache nodes

        get_reg_key_values()            -- Gets the values for multiple reg keys for multiple MAs, also checks for equality

        wait_for()                      -- Runs till_condition_is_true(func()) with retry attempts

        wait_for_reg_key_to_be()        -- Waits until a particular reg key exists and equal to reg_value

        verify_vdisk_registry()         -- Verifies if sVDiskList is present and same across MediaAgents

        get_storage_pool_from_media_agent()     -- Gets the name of the storage pool from MA name

        get_storage_pool_from_media_agents()    -- Gets the name of the storage pool spanning the MAs

        trigger_node_refresh()          --  Triggers the node refresh API

        validate_ddb_expansion()        --  Validates DDB expansion

        get_storage_pool_size()         --  Gets the storage pool size

        reboot_and_disable_cd_rom()     --  Reboots the nodes while disabling CD rom

        verify_showmembers_output()     --  Verfies showmembers output based on the given inputs

        validate_passwordless_ssh()     --  Verifies passwordless SSH using ssh command on terminal

        validate_passwordless_ssh_using_cvhsx() --  Verifies passwordless SSH using cvmanager

        get_sp_version_for_client()     --  Gets the SP version for client as reported by CS

        verify_sp_version_for_clients() --  Verifies if the SP version is same for all clients

        get_sp_version_for_media_agent()    --  Gets the SP version for MA as reported by MA itself

        verify_sp_version_for_media_agents()    --  Verifies if the SP version is same for all clients

        track_cvmanager_task()          --  Tracks cvmanager task by polling it

        cvmanager_add_node_task()       --  Add Node from cvmanager task

        cvmanager_refresh_node_task()   --  Refresh Node from cvmanager task

        verify_repo_checksum()          --  Verifies repo checksum

   """

    def __init__(self, commcell_obj, csdb_obj, log_obj):
        """
            Initializes instance of the Machine class.
            Args:

            commcell_obj    (object)    --  instance of the Commcell
            csdb_obj        (object)    --  instance of the CSDB
            log_obj         (object)    --  instance of the Logger

        """
        self.commcell = commcell_obj
        self.csdb = csdb_obj
        self.log = log_obj
        self.user = self.commcell._user 
        is_tenant_commcell = self.user not in ('cvautoexec', 'admin')
        is_cvauto_commcell = self.user == 'cvautoexec'

        if not is_cvauto_commcell:
            self.storage_pool_obj = self.commcell.storage_pools
        else:
            self.storage_pool_obj = None

        self.dbobject = None
        self.commserve_instance = "\\commvault"
        if is_tenant_commcell or self.commcell.is_linux_commserv:
            self.commserve_instance = ""

    def connect(self, db_user, db_password):
        """
        Connection to db
        """
        try:
            self.dbobject = MSSQL(self.commcell.commserv_hostname + self.commserve_instance,
                                  db_user, db_password, "CommServ", False, True)
        except Exception as err:
            raise Exception("Exception raised {}, failed to connect to the Database with username {}".format(
                err, db_user))

    def execute_update_query(self, query, sql_login, db_password):
        """
        Executes update query on CSDB
        Args:
            query (str) -- update query that needs to be run on CSDB
            sql_login (str) --  Sql login user name
            db_password (str)   -- sa password for CSDB login
        Return:
            Response / exception
        """
        try:
            if self.dbobject is None:
                self.connect(sql_login, db_password)

            response = self.dbobject.execute(query)
            if response.rows is None:
                return bool(response.rowcount == 1)
            return response
        except Exception as err:
            raise Exception("failed to execute query {0}".format(err))

    def get_storage_pool_details(self, name):
        """
            Returns Storage Pool details as a list
            Args:
                name (str) -- Storage Pool Name
            Return:
                storage_pool_details / Exception
        """
        self.commcell.storage_pools.refresh()
        storage_pool_details = self.commcell.storage_pools.get(name)
        self.log.info("Storage Pool Details %s ", storage_pool_details)
        return storage_pool_details

    def get_all_bricks(self, name, host_id):
        """
            Gets flags, BrickHealth, BlockDeviceHealth and DeviceOsPath
            for all bricks associated with a storage pool for a particular MA
            Args:
               name(name) -- Storage Pool name
               host_id(name) -- Media agent id
            Return:
                rows -- List of bricks and their details
        """
        storage_pool_details = self.get_storage_pool_details(name)
        storage_pool_properties = storage_pool_details._storage_pool_properties
        storage_pool_node_detail_list = storage_pool_properties[
            "storagePoolDetails"]["storagePoolNodeDetailsList"]
        result = []
        for brick_details in storage_pool_node_detail_list:
            if brick_details["mediaAgent"]["mediaAgentId"] == host_id:
                result.append(brick_details)
        self.log.info("Bricks for host_id %s are %s", host_id, result)
        return result

    def get_all_bricks_for_hostid(self, hostid):
        """
            Gets flags, BrickHealth, BlockDeviceHealth and DeviceOsPath for all bricks associated with a particular MA
            Args:
                hostid (int/str) -- Host ID of the MA

            Return:
                rows -- List of bricks and their details
        """
        self.csdb.execute(
            "select flags,BrickHealth, BlockDeviceHealth, deviceospath, deviceId from mmdiskhwinfo where "
            "mountpathusagetype = 2 and hostid = " + str(hostid))
        rows = self.csdb.fetch_all_rows()
        return rows

    def get_brick_daemon_for_brick(self, media_agent, disk):
        """
           Check if brick daemon is present for the hyperscale brick
           Args:
               media_agent (str) -- Name of the MA where the daemon is to be checked
               disk (string) -- Name of the hyperscale brick

           Return:
                String -- Console output
        """

        # SSH to MA
        ma_session = Machine(media_agent, self.commcell)
        output = ma_session.execute_command("ps -ef | grep {0}".format(disk))
        self.log.info(output.output)
        return output.output

    def get_all_nodes(self, storage_pool_name):
        """
            Gets a list of MAs associated with a particular Storage Pool
            Args:
                storage_pool_name (str) -- Name of the Storage Pool
            Return:
                rows -- List of all MAs associated with the given Storage Pool
        """
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        storage_pool_properties = storage_pool_details._storage_pool_properties
        storage_pool_node_detail_list = storage_pool_properties[
            'storagePoolDetails']['storagePoolNodeDetailsList']
        node_list = []
        for details in storage_pool_node_detail_list:
            data = [details['mediaAgent']['mediaAgentId'],
                    details['mediaAgent']['mediaAgentName']]
            if data not in node_list:
                node_list.append(data)
        self.log.info("Node detils %s", node_list)
        return node_list

    def check_brick_health_status(self, hostid):
        """
            Checks the flag, blockdevicehealth and brickhealth values for all bricks for a given MA
            Args:
                hostid (int) -- host id for the given MA
            Return:
                True / Exception
        """
        bricks = self.get_all_bricks_for_hostid(hostid)

        for brick in bricks:
            self.log.info(brick[3])
            if int(brick[0]) != 1:
                raise Exception(
                    "{0} Brick does not have the flag set to 1".format(brick[3]))
            if int(brick[1]) != 23:
                raise Exception(
                    "{0} Brick does not have the BrickHealth set to 23".format(brick[3]))
            if int(brick[2]) != 15:
                raise Exception(
                    "{0} Brick does not have the BlockDeviceHealth set to 15".format(brick[3]))
            self.log.info(
                "Flags, brickHealth and BlockDeviceHealth correctly set for {0}".format(brick[3]))

        return True

    def get_host_id(self, ma_name):
        """
            Returns the hostid of the MA
            Args:
                ma_name (str) -- Name of the MA whose hostid is to be returned
            Return:
                hostid (int) -- host id for the given MA / Exception
        """
        ma_client = self.commcell.clients.get(ma_name)
        ma_id = ma_client.client_id
        self.log.info("Host id for ma: %s is %s", ma_name, ma_id)
        return ma_id

    def wait_for_completion(self, storage_pool_name):
        """
            Check if hyperscale storage pool creation or expansion operation has completed or failed

            Args:
                storage_pool_name (str) -- Name of the storage pool

            Return:
                 Boolean -- True or False based on whether the storage pool creation succeeded or failed
        """
        count = 0
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        storage_pool_properties = storage_pool_details._storage_pool_properties
        status = storage_pool_properties["storagePoolDetails"]['statusCode']

        while int(status) == 100 and count <= 20:
            storage_pool_details = self.get_storage_pool_details(
                storage_pool_name)
            storage_pool_properties = storage_pool_details._storage_pool_properties
            status = storage_pool_properties["storagePoolDetails"]['statusCode']
            self.log.info("status for pool %s is %s",
                          storage_pool_name, status)
            count += 1
            time.sleep(60)
        status = storage_pool_properties["storagePoolDetails"]['statusCode']
        self.log.info(status)
        if int(status) == 300:
            return True
        self.log.info("Storage Pool status %s not 300", status)
        return False

    def add_nodes(self, storage_pool_name, *args):
        """
        Add 3 more nodes to horizontally expand a setup by 1 block

        Args:
            storage_pool_name (str) -- Name of the storage pool
            *args: Media agent names
                    ma1_name (str) -- Name of the first MA
                    ma2_name (str) -- Name of the second MA
                    ma3_name (str) -- Name of the third MA

        Return:
            flag (int) -- Response code received from the Rest API call
            response (str) -- Response received from the Rest API
            status (boolean) -- True or False based on the success or failure of the operation
        """
        if len(args) <= 2:
            self.log.error("insufficient number of inputs %s" % str(args))
            raise Exception("insufficient number of inputs %s" % str(args))

        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        ma_values = [self.commcell.media_agents.get(value) for value in args]

        ma_ids = [self.get_host_id(ma_name) for ma_name in args]
        self.log.info("Check if hosts present and flags = 0 not configured")
        for ma_id in ma_ids:
            if not self.check_brick_available_status(ma_id):
                raise Exception("Brick status not available for creation")
        storage_pool_details.hyperscale_add_nodes(ma_values)

        self.log.info("Waiting CSDB to populate")
        time.sleep(900)

        status = self.wait_for_completion(storage_pool_name)
        response = self.get_storage_pool_details(storage_pool_name)
        self.log.info(response)
        return status, response

    def create_storage_pool(self, storage_pool_name, *args):
        """
            Create a hyperscale storage pool containing 3 nodes

            Args:
                storage_pool_name (str) -- Name of the storage pool
               *args: Media agent names
                    ma1_name (str) -- Name of the first MA
                    ma2_name (str) -- Name of the second MA
                    ma3_name (str) -- Name of the third MA

            Return:
                flag (int) -- Response code received from the Rest API call
                response (str) -- Response received from the Rest API
                status (boolean) -- True or False based on the success or failure of the operation
        """
        setup = "Standard"
        if len(args) <= 2:
            self.log.error("insufficient number of inputs %s" % str(args))
            raise Exception("insufficient number of inputs %s" % str(args))
        ma_values = [self.commcell.media_agents.get(value) for value in args]
        ma_ids = [self.get_host_id(ma_name) for ma_name in args]
        self.log.info("Check if hosts present and flags = 0 not configured")
        for ma_id in ma_ids:
            if not self.check_brick_available_status(ma_id):
                raise Exception("Brick status not available for creation")

        if not self.resiliency(ma_ids, setup):
            self.log.info("Resiliency not Correct")
            raise Exception(
                "Resiliency factor not correct or brick status not available")

        self.commcell.storage_pools.hyperscale_create_storage_pool(
            storage_pool_name, ma_values)

        status = self.wait_for_completion(storage_pool_name)
        self.log.info("Storage Pool status %s", status)
        response = self.get_storage_pool_details(storage_pool_name)
        self.log.info(response)

        return status, response
    

    def delete_storage_pool(self, storage_pool_name):
        """
        Deletes a hyperscale storage pool
        Args:
           storage_pool_name (str) -- name of the storage pool

        Return:
            flag (int) -- Response code received from the Rest API call
            response (str) -- Response received from the Rest API call
       """

        self.commcell.storage_pools.delete(storage_pool_name)

    def get_associated_storage_policies(self, storage_pool_name):
        """
           Get a list of Storage Policies associated to a hyperscale Storage pool's GDSP

           Args:
               storage_pool_name (str) -- Name of the storage pool

           Return:
               rows (list) -- List of associated storage policies
        """
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        gdsp = storage_pool_details.storage_pool_id
        query = """select name from archgroup where id in (select archgroupid from archgroupcopy where SIDBStoreId =  
                (select sidbstoreid from archGroupCopy where archgroupid  =  
                (select gdspid from MMSDSStoragePool where GDSPId = '{0}')))  
                and id <> (select gdspid from MMSDSStoragePool where GDSPId = '{0}')""".format(
            gdsp)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return rows

    def check_if_storage_pool_is_present(self, storage_pool_name):
        """
            Check if s hyperscale storage pool is present or not

            Args:
                storage_pool_name (str) -- Name of the storage pool

            Return:
                 Boolean -- True or False based on whether the storage pool is present or not
                """
        self.commcell.storage_pools.refresh()
        return self.commcell.storage_pools.has_storage_pool(storage_pool_name)

    def get_associated_mas(self, storage_pool_name):
        """
               Get all MAs associated with a hyperscale storage pool

               Args:
                   storage_pool_name (str) -- Name of the storage pool

               Return:
                    rows (list) -- List of associated MAs
               """
        if self.check_if_storage_pool_is_present(storage_pool_name):
            storage_pool_details = self.get_storage_pool_details(
                storage_pool_name)
            storage_pool_properties = storage_pool_details._storage_pool_properties
            storage_pool_node_detail_list = storage_pool_properties['storagePoolDetails'][
                'storagePoolNodeDetailsList']
            ma_list = []
            for details in storage_pool_node_detail_list:
                data = [details['mediaAgent']['mediaAgentName']]
                if data not in ma_list:
                    ma_list.append(data)
            self.log.info("Node detils %s", ma_list)
            return ma_list
        return []

    def clean_up_ma(self, ma1, storage_pool_name):
        """
            Cleans up all data disks and peer files from an MA
            Args:
                ma1 (str) -- Name of primary MA that is being cleaned up
                storage_pool_name(str) --> Storage Pool name
            Return:
                Exception
        """
        # SSH to MA1
        count = 5
        ma_session = None
        status = False
        while count >= 0:
            try:
                ma_session = Machine(ma1, self.commcell)
                status = True
            except Exception as exp:
                result = str(exp)
                self.log.exception(
                    "Exception occurred connecting to host %s ", result)
                count -= 1
                status = False
                self.log.info("Trying again")
                time.sleep(90)
                pass
            if status:
                break

        # Run echo "y" | gluster v stop storage_pool_name
        output = ma_session.execute_command(
            "echo \"y\" | gluster v stop " + storage_pool_name)
        self.log.info(output.output)

        # Run echo "y" | gluster v delete storage_pool_name
        output = ma_session.execute_command(
            "echo \"y\" | gluster v delete " + storage_pool_name)
        self.log.info(output.output)

        # Run for i in `lsblk | grep -i /ws/ | awk '{print $7}'` ; do rm -fr $i/* ; ls -l $i ; done
        self.log.info("Cleaning all /ws/disk drives")
        output = ma_session.execute_command(
            "for i in `lsblk | grep -i /ws/ | awk '{print $7}'` ; do rm -fr $i/* ; ls -l $i ; done")
        self.log.info(output.output)

        # gluster peer detach sds
        self.log.info("Detaching peers")
        peers = ma_session.execute_command(
            "gluster peer status | grep 'Hostname' | awk '{print $2}'")
        peers = peers.output.split("\n")
        peers = peers[:len(peers) - 1]
        for peer in peers:
            self.log.info("Peer %s", peer)
            output = ma_session.execute_command(
                "echo \"y\" | gluster peer detach " + peer)
            self.log.info(output.output)

        # cleaning fstab
        self.log.info("Cleaning fstab entry")
        ma_session = Machine(ma1, self.commcell)
        command = "sed -i '/{0}/d' /etc/fstab".format(storage_pool_name)
        self.log.info(command)
        ma_session.execute_command(command)

        # cleaning Replace brick file
        self.log.info("Cleaning ReplaceBrick file")
        file_path = f"{ma_session.client_object.job_results_directory}/Scaleout"
        self.log.info(file_path)
        ma_session.delete_file(file_path=file_path)

        # commvault restart
        self.log.info("Restarting MA services")
        try:
            output = ma_session.execute_command("commvault restart")
        except Exception as exp:
            self.log.info("Exception %s", exp)
            self.log.info("Restarted Services")
        time.sleep(60)

    def reassociate_all_associated_subclients(self, storage_pool_name, sql_login, sql_sq_password):
        """
            Reassociates all subclients associated with a storage policy to none assigned
            Args:
                storage_pool_name (str) -- Name of the Storage pool which is to be cleaned up
                sql_login       (str) -- SQL login name
                sql_sq_password (str) -- Password to log into the SQL server
            Return:
                Exception
        """

        # Find all associated storage policies with this GDSP
        sstorage_policy_list = self.get_associated_storage_policies(
            storage_pool_name)
        self.log.info("Associated storage policies: {0}".format(
            sstorage_policy_list))

        self.log.info(str(len((sstorage_policy_list[0])[0])))

        if not (sstorage_policy_list[0])[0]:
            return

        for storage_policy in sstorage_policy_list[0]:
            storage_policy_obj = self.commcell.storage_policies.get(
                storage_policy)

            # update archgroupid = 1 for all associated subclients to sp.
            query = """update app_application 
                            set dataArchGrpID = 1, logArchGrpID = 1 
                            where dataArchGrpID = {0}""".format(storage_policy_obj.storage_policy_id)
            # self.log.info("QUERY: %s", query)
            self.execute_update_query(query, sql_login, sql_sq_password)

            # Delete associated storage policies with this GDSP
            try:
                self.commcell.storage_policies.delete(storage_policy)
            except Exception as err:
                self.log.error("failed to delete SP %s" % err)

    def clean_up_storage_pool(self, storage_pool_name, sql_login, sql_sq_password):
        """
            Cleans up all entries left by a pre-existing storage pool
            Args:
                storage_pool_name (str) -- Name of the Storage pool which is to be cleaned up
                sql_login (str)       --  SQL login name
                sql_sq_password (str) -- Password to log into the SQL server
            Return:
                Exception
        """

        status = self.check_if_storage_pool_is_present(storage_pool_name)

        if status is False:
            self.log.info("Storage pool not present, aborting clean up")
            return
        gluster_name = self.gluster_name_for_storage_pool(storage_pool_name)
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        library_name = storage_pool_details._storage_pool_properties['storagePoolDetails'][
            'libraryList'][0]['library']['libraryName']
        mas = self.get_associated_mas(storage_pool_name)

        # Reassociate all associated subclients
        self.reassociate_all_associated_subclients(
            storage_pool_name, sql_login, sql_sq_password)

        # Delete Storage Pool
        self.delete_storage_pool(storage_pool_name)

        # Delete Storage Target
        try:
            self.commcell._disk_libraries = None
            self.commcell.disk_libraries.delete(library_name)
        except Exception as err:
            self.log.error("Failed to delete library %s" % err)

        # SSH to MA1
        for media_agent in mas:
            ma_session = Machine(media_agent[0], self.commcell)
            # Unmounting glus mount point and removing folder
            command = "df -h | grep '" + \
                str(gluster_name) + "'| awk '{print $6}'"
            self.log.info(command)
            output = ma_session.execute_command(command)
            self.log.info(output.formatted_output)
            command = "umount {0}".format(output.formatted_output)
            self.log.info(command)
            output = ma_session.execute_command(command)
            self.log.info(output)

            # removing /ws/glus_
            self.log.info("Removing glus directory")
            command = "for i in `ls /ws | grep -i glus | awk '{print $1}'` ; do rm -fr /ws/$i ; done"
            self.log.info(command)
            output = ma_session.execute_command(command)
            self.log.info(output.exception)

        for media_agent in mas:
            self.log.info("Cleaning up {0}".format(media_agent[0]))
            self.clean_up_ma(media_agent[0], gluster_name)

    def check_brick_flag_status(self, media_agent):
        """
            Check if the health status is proper for a particular MA's bricks or not
         Args:
            media_agent (str) -- Name of the MA

        Return:
            Boolean -- True if all daemons are active
            Exception if daemons are not active
        """
        hostid = self.get_host_id(media_agent)
        self.log.info(hostid)
        status = self.check_brick_health_status(int(hostid))
        if status is True:
            self.log.info(
                "All brick daemons for {0} are active".format(media_agent))
        else:
            raise Exception(
                "Not all brick daemons for {0} are active".format(media_agent))

    def reconfigure_storage_pool(self, storage_pool_name):
        """
                   Checks device accessibility before reconfigure and trigger reconfigure
                   after completion checks pool status and validates pool and accessibility of devices
                   validation of pool done while checking accessibility
                    Args:
                       storage_pool_name (name) -- storage pool name
                    Return:
                        True / False
                """
        self.log.info("Checking brick accessibility for pool %s ",
                      storage_pool_name)
        if self.brick_accessibility(storage_pool_name) is False:
            return False, "Brick Not Accessible"
        nodes_before = list(self.get_all_nodes_hostids(storage_pool_name))
        nodes_before.sort()
        self.log.info("Nodes use for pool creation %s ", nodes_before)

        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        storage_pool_details.hyperscale_reconfigure_storage_pool(
            storage_pool_name)
        self.log.info("Waiting")
        time.sleep(1700)

        status = self.wait_for_completion(storage_pool_name)
        response = self.get_storage_pool_details(storage_pool_name)
        self.log.info(response)
        sp_status = self.validate_storage(storage_pool_name)
        nodes_after = list(self.get_all_nodes_hostids(storage_pool_name))
        nodes_after.sort()
        self.log.info("Nodes after reconfigure pool %s are %s ",
                      storage_pool_name, nodes_after)
        nodes_status = False
        if nodes_before == nodes_after:
            nodes_status = True
        device_accessible_status = self.brick_accessibility(storage_pool_name)
        status = status & device_accessible_status & nodes_status & sp_status

        return status, response

    def check_brick_available_status(self, hostid):
        """
            Checks the flag values for all bricks for a given MA
            Args:
                hostid (int) -- host id for the given MA
            Return:
                True / Exception
        """
        time.sleep(10)
        not_configured = 0
        bricks = self.get_all_bricks_for_hostid(hostid)
        for brick in bricks:
            self.log.info("Brick %s status;", brick[3])
            if int(brick[0]) != not_configured:
                self.log.error(
                    f"{brick[3]} Brick does not have the flag set to 0 for hostid {hostid}")
                return False
            self.log.info(
                "Brick %s is available and flag status %s ", brick[3], brick[0])

        return True

    def false_hosts(self, ma1):
        """
            Update host file with false hosts to break connectivity between
            th host and commserve
            Args:
                ma1(name) --> Media Agent
            Return:
                Nothing
        """
        ma1_session = Machine(ma1, self.commcell)
        self.log.info("Updating hosts, Storage pool failure "
                      "Updating Hosts with wrong details at %s", ma1)
        ma1_session.execute_command(" mkdir /root/false_hosts")
        ma1_session.execute_command(" mkdir /root/true_hosts")
        ma1_session.execute_command("cp -f /etc/hosts /root/true_hosts/hosts")
        ma1_session.execute_command("cp -f /etc/hosts /root/false_hosts/hosts")
        ma1_session.execute_command(
            "sed -i -e 's/^/#/' /root/false_hosts/hosts")
        # Run cp -f /root/false_hosts/hosts /etc/hosts
        command = r"cp -f /root/false_hosts/hosts /etc/hosts"
        self.log.info(command)
        output = ma1_session.execute_command(command)
        self.log.info("Updated false host file")
        ma1_session.execute_command("rm -rf /root/false_hosts")
        self.log.info(output.output)

    def true_hosts(self, ma1):
        """
           Update host file with true hosts to bring up the connectivity b/w
           host and cs, which was broken by false host
           Args:
               ma1(name) --> Media Agent
           Return:
               Nothing
        """
        ma1_session = Machine(ma1, self.commcell)
        self.log.info("Updating Hosts with correct details at %s", ma1)

        command = r"cp -f /root/true_hosts/hosts /etc/hosts"
        # Run cp -f /root/true_hosts/hosts /etc/hosts
        self.log.info(command)
        output = ma1_session.execute_command(command)
        self.log.info(output.output)
        self.log.info("Updated correct host file")
        ma1_session.execute_command("rm -rf /root/true_hosts")

    def check_resolution_error(self, hostid):
        """
            Checks the flag, blockdevicehealth and brickhealth values for all bricks for a given MA
            Args:
                hostid (int) -- host id for the given MA
            Return:
                True / False
        """
        self.log.info("Checking Resolution error issue Flags,"
                      " brickHealth and BlockDeviceHealth set to 0 "
                      "after creation failure,resolution error")
        bricks = self.get_all_bricks_for_hostid(hostid)
        not_configured = 0
        for brick in bricks:
            self.log.info("Brick %s status;", brick[3])
            if int(brick[0]) != not_configured and int(brick[1]) != not_configured and int(brick[2]) != not_configured:
                self.log.info(
                    "Flags, brickHealth and BlockDeviceHealth are correctly set for {0}".format(brick[3]))
            else:
                self.log.info("For brick: %s  "
                              "Flag: %s, brickHealth: %s and "
                              "BlockDeviceHealth: %s", brick[3], brick[0], brick[1], brick[2])
                self.log.info("Resolution issue, Check hosts file")
                return True
        return False

    def get_device_controller_details(self, name):
        """
            Gets the all device details for the storage pool
            Args:
                name(name) --> storage pool name
            Return:
                devices details
        """
        if self.check_if_storage_pool_is_present(name):
            host_ids = self.get_all_nodes_hostids(name)
            bricks = self.get_all_bricks_for_hostid(host_ids[0])
            device_id = 0
            for brick in bricks:
                if len(brick[4]) != 0:
                    device_id = brick[4]
                    break
            self.log.info("Getting all devices for pool %s ", name)
            query = "select * from MMDeviceController where deviceId = {0}".format(
                device_id)
            self.log.info(query)
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            self.log.info(rows)
            return rows
        raise Exception("No device controller details for storage pool")

    def get_library_details(self, library_id):
        """
           Gets the library details for the given library id
           Args:
               library_id (int) -- library id for given library
           Return:
               library details
        """
        self.log.info("Getting library details for id %s ", library_id)
        query = "select * from MMLibrary as lib where lib.LibraryId = " + \
            str(library_id)
        self.log.info(query)
        self.csdb.execute(query)
        library_details = self.csdb.fetch_one_row()
        if not library_details[0]:
            raise Exception('No library with id %s', library_id)
        self.log.info("Library Details  %s", str(library_details))
        return library_details

    def check_library_mount(self, library_id):
        """
             Gets the library mount details, accessibility and controller
              for the given library id
             Args:
                 library_id (int) -- library id for given library
             Return:
                 library details
                 """
        self.log.info("Getting library mount details, accessibility and controller "
                      "for the given library id %s ", library_id)
        query = """select mmd.DeviceControllerEnabled, mmd.DeviceAccessible, mmd.Folder  
                from MMlibrary as lib, MMMountPath as mp, MMMountPathToStorageDevice as mps, 
                 MMDeviceController as mmd  
                where lib.LibraryId = mp.LibraryId and mp.MountPathId = mps.MountPathId and 
                 mps.DeviceId = mmd.DeviceId and lib.LibraryId = {0}""".format(str(library_id))
        self.log.info(query)
        self.csdb.execute(query)
        mount_details = self.csdb.fetch_all_rows()
        self.log.info("Mount Deatils %s", mount_details)
        return mount_details

    def get_policy_details(self, gdspid):
        """
            Gets the policy details for the given pool
            Args:
                gdspid (int) -- gdspid for the policy to be created
            Return:
                policy details
                    """
        self.log.info("Getting Policy details for gdspid %s ", gdspid)
        query = "select * from archGroup where id = " + str(gdspid)
        self.log.info(query)
        self.csdb.execute(query)
        policy_details = self.csdb.fetch_one_row()
        self.log.info("Policy Details " + str(policy_details))
        return policy_details

    def get_dedup_details(self, name):
        """
            Gets the dedup details for the given pool
                Args:
                    name --> storage pool name
                Return:
                    dedup details
        """
        self.log.info("Getting dedup store details for %s", name)
        details = self.get_storage_pool_details(name)
        storage_pool_details = details._storage_pool_properties['storagePoolDetails']
        storage_pool_dedup = storage_pool_details['dedupDBDetailsList']
        dedup_details = []
        for detail in storage_pool_dedup:
            dedup_details.append(detail['storeName'])

        self.log.info("Dedup Details %s", dedup_details)
        return dedup_details

    def validate_dedup_store(self, gdspid):
        """
           Validate dedup present on ma's or not
                Args:
                    gdspid (int) -- gdspid for the policy to be created
                Return:
                    dedup details
        """
        self.log.info("Checking ddb stores on ma\n")
        query = """select Distinct pt.IdxAccessPathId, pt.ClientId, pt.Path, client.name, pt.OfflineReason
                from APP_Client as client, IdxAccessPath as pt, IdxSIDBStore as idx, archGroup as arc,  
                MMSDSStoragePool as storage, archCopySIDBStore sidb, IdxSIDBSubStore as sub  
                where storage.GDSPId = arc.id and arc.defaultCopy = sidb.CopyId and  
                sidb.SIDBStoreId = sub.SIDBStoreId  and sub.IdxAccessPathId = pt.IdxAccessPathId
                and client.id = pt.ClientId
                and storage.GDSPId = {0}""".format(str(gdspid))
        self.log.info(query)
        self.csdb.execute(query)
        details = self.csdb.fetch_all_rows()
        self.log.info("Dedup Partition details %s ", details)
        ma_dict = {}
        status = True
        for row in details:
            if row[3] not in ma_dict:
                ma_dict[row[3]] = []
            ma_dict[row[3]].append(row)
        for media_agent in ma_dict:
            row = ma_dict[media_agent]
            ma_session = Machine(media_agent, self.commcell)
            # checking /ws/ddb mount on node or not
            mount = r"df -h | grep '/ws/ddb' | awk '{print $1}'"
            mount_output = ma_session.execute_command(mount)
            if not mount_output.output:
                self.log.error(
                    "No mount path for /ws/ddb over %s ", media_agent)
                raise Exception("No mount path /ws/ddb")
            self.log.info("/ws/ddb mount path %s ", mount_output.output)
            # Restart services to check ddb copy presence, idx file gets created then,
            # CS sends information and thread creates that
            restart = r"commvault restart"
            try:
                ma_session.execute_command(restart)
            except Exception as exp:
                self.log.info("Exception %s", exp)
                self.log.info("Restarted Services")
                pass
            time.sleep(120)
            for entry in row:
                command = r"cd "
                self.log.info(
                    "Checking presence of partition %s on ma %s ", entry[2], entry[3])
                output = ma_session.execute_command(command + str(entry[2]))
                if output.exception:
                    status = False
                    self.log.error(output.exception)
                    # raise Exception("Partition %s not present on ma", entry[2])
                else:
                    self.log.info("Present")
                self.log.info("Checking Offline status")
                if int(entry[4]) != 0:
                    self.log.error("DDB partition %s offline with code %s on node %s", entry[2],
                                   entry[4], entry[3])
                else:
                    self.log.info("Online")
        return status

    def validate_storage(self, name):
        """
                   Validates the pool against library and policy
                   if policy present will have a dedup engine else no
                   Args:
                       name (str) -- Storage pool name
                   Return:
                       True/False
               """
        status = True
        details = self.get_storage_pool_details(name)
        self.log.info("Checking library state for pool %s", name)
        lib_id = details._storage_pool_properties[
            'storagePoolDetails']['libraryList'][0]['library']['libraryId']
        # lib_id = details[2]
        gdspid = details.storage_pool_id
        library_details = self.get_library_details(lib_id)
        if int(library_details[3]) != 1 and int(library_details[34]) != 46003:
            self.log.info("library offline with error %s and creation incomplete for "
                          "pool %s", library_details[34], name)
            status = False
        mount_details = self.check_library_mount(lib_id)
        if not mount_details[0]:
            self.log.info("No Mount path details for library %s", lib_id)
            status = False
        else:
            for mount in mount_details:
                self.log.info("Mount details %s, Accessible %s, DeviceEnabled %s", mount[2], mount[1],
                              mount[0])

        policy_details = self.get_policy_details(gdspid)
        if not policy_details[0]:
            self.log.info("Policy is not present, pool %s creation failed",
                          name)
            status = False
        if policy_details[0] and int(policy_details[13]) & 256 != 256:
            self.log.info("Not Global Policy for pool %s", name)
            status = False
        else:
            self.log.info("policy %s is Global Policy for pool %s",
                          policy_details, name)
        dedup_details = self.get_dedup_details(name)
        if not dedup_details[0]:
            self.log.info("No dedup store present for %s ", name)
            status = False

        if not self.validate_dedup_store(gdspid):
            status = False

        if status is True:
            self.log.info("Library %s and Global policy %s and dedup store %s"
                          "up and present for pool %s ",
                          library_details, policy_details, dedup_details,
                          name)
            self.log.info("Storage pool %s created and up", name)
        return status

    def brick_accessibility(self, name):
        """
                   Check if bricks are accessible for pool creation
                   Args:
                       name (str) -- Storage pool name
                   Return:
                       library details
               """

        devices = self.get_device_controller_details(name)

        for device in devices:
            self.log.info("Node %s with Device id %s ", device[1], device[2])
            if int(device[11]) != 1:
                self.log.info("Node %s not accessible", device[1])
                return False
            self.log.info("Node %s accessible for creation", device[1])
        return True

    def resiliency(self, ma_list, setup):
        """
        Determine resiliency factor for the storage pool is correct or not at the time
        of creation
        Args:
            ma_list(list) --> List of media agent used
            setup(name) --> Type of setup (Standard/ Medium/ High)
        Return:
            True/False
        """
        self.log.info("Determining Resiliency")
        if setup.lower() == "standard":
            scale_out = 1
            self.log.info("Standard configuration, 3 nodes")
        elif setup.lower() == "medium":
            scale_out = 2
            self.log.info("Medium configuration, 6 nodes")
        elif setup.lower() == "high":
            scale_out = 3
            self.log.info("High configuration, 6 nodes")
        else:
            raise Exception("Setup configuration not present")

        count, min_used = 0, sys.maxsize
        node_bricks = {}
        for media_agent in ma_list:
            bricks = self.get_all_bricks_for_hostid(media_agent)
            node_bricks[media_agent] = len(bricks)
            req = int(len(bricks) // 2) * 2
            if req <= min_used:
                min_used = req
        node_bricks_sort = sorted(node_bricks.items(), key=lambda kv: kv[1])
        self.log.info("Bricks on nodes are %s", node_bricks_sort)
        if min_used == 0:
            self.log.error("Disk number not correct for node %s, minimum required are"
                           "%s ", node_bricks_sort[0][0], min_used)
            return False
        if node_bricks_sort[0][1] < min_used:
            self.log.error("Disk number not correct for node %s, minimum required are"
                           "%s ", node_bricks_sort[0][0], min_used)
            return False
        count += len(ma_list) * min_used
        if scale_out == 1 and count % 6 == 0:
            self.log.info("Standard for 3 Nodes, Disperse Factor 6, Redundancy Factor 2."
                          "Withstands loss of 2 drives or 1 node")
            return True
        if scale_out == 2 and count % 12 == 0:
            self.log.info("Medium for 6 Nodes, Disperse Factor 6, Redundancy Factor 2. "
                          "Withstands loss of 2 drives or 2 nodes")
            return True
        if scale_out == 3 and count % 12 == 0:
            self.log.info("High for 6 Nodes, Disperse Factor 12, Redundancy Factor 4."
                          " Withstands loss of 4 drives or 2 nodes")
            return True

        return False

    def get_all_nodes_hostids(self, storage_pool_name):
        """
            Gets a list of MA ids associated with a particular Storage Pool
            Args:
                storage_pool_name (str) -- Name of the Storage Pool
            Return:
                rows -- List of all MA ids associated with the given Storage Pool
        """
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        storage_pool_properties = storage_pool_details._storage_pool_properties
        storage_pool_node_detail_list = storage_pool_properties[
            'storagePoolDetails']['storagePoolNodeDetailsList']
        node_id_list = []
        for details in storage_pool_node_detail_list:
            data = details['mediaAgent']['mediaAgentId']
            if data not in node_id_list:
                node_id_list.append(data)
        self.log.info("host ids %s for pool %s ",
                      node_id_list, storage_pool_name)
        return node_id_list

    def get_disk_uuid(self, mas):
        """
        Get disk uuid information present on all the mas
        Args:
            mas(list) --> list of Media Agents
        Return:
            Dictionary of data
        """

        self.log.info("getting uuid information")
        command1 = r"lsblk | grep -i /ws/disk | awk '{print $1,$7}'"
        # sdb | awk '{print $2}'"
        ma_dict = {}
        for media_agent in mas:
            ma_session = Machine(media_agent, self.commcell)
            self.log.info("UUID's of disks for %s ", media_agent)
            self.log.info(command1)
            output1 = ma_session.execute_command(command1)
            disks = output1.output.split("\n")
            disks.remove("")
            self.log.info(disks)
            hostid = self.get_host_id(media_agent)
            for disk in disks:
                command2 = r"blkid | grep -i "
                data1, data2 = disk.split()
                command2 = command2 + data1 + " | awk '{print $2}'"
                # self.log.info("UUID for %s is", disk)
                output2 = ma_session.execute_command(command2)
                uuid = output2.output
                # self.log.info(output2.output)
                media_agent_split = media_agent.split('.', 1)
                if 2 == len(media_agent_split):
                    key = media_agent.split('.', 1)[0] + "sds." + media_agent.split('.', 1)[
                        1] + ":" + data2 + "/ws_brick"
                else:
                    key = media_agent.split(
                        '.', 1)[0] + "sds:" + data2 + "/ws_brick"
                ma_dict[key] = [media_agent, data1,
                                uuid.replace("\n", ""), data2, hostid]

        for key in ma_dict:
            self.log.info("%s %s", key, ma_dict[key])
        return ma_dict

    def gluster_brick_information(self, media_agent):
        """
        Get bricks for the gluster
        Args:
            media_agent(name)  --> Media Agent
        Return:
            list of bricks
        """
        self.log.info("getting disk information for gluster")
        ma_session = Machine(media_agent, self.commcell)
        command2 = r"gluster v info | grep -i 'sds' | awk '{print $2}'"
        self.log.info(command2)
        time.sleep(200)
        output1 = ma_session.execute_command(command2)
        self.log.info(output1.output)
        if output1.output == "":
            self.log.error("no gluster on node %s ", media_agent)
            raise Exception("No Gluster information present on ma")
        bricks = output1.output.split("\n")
        bricks = bricks[:len(bricks) - 2]
        return bricks

    def verify_gluster_disk_uuids(self, media_agent, ma_dict):
        """
        Verify if same disks were used for gluster creation or not,
        disks which were present on each node and bricks after gluster creation
        Args:
            media_agent(name) --> Media Agent (for gluster information)
            ma_dict(dictionary) --> output of get_disk_uuid ( before creation)
        Return:
            True/False
        """

        self.log.info("getting disk uuids for Gluster")
        ma_session = Machine(media_agent, self.commcell)
        command = r"gluster v info | grep -i 'auth.allow:' | awk '{print $2}'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        self.log.info(output.output)
        nodes = output.output.replace("\n", "").replace("sds", "").split(",")
        gluster_disk_ids = self.get_disk_uuid(nodes)
        bricks = self.gluster_brick_information(media_agent)
        status = True
        for brick in bricks:
            if gluster_disk_ids[brick][2] != ma_dict[brick][2] or gluster_disk_ids[brick][1] != ma_dict[brick][1]:
                self.log.info("For node %s, uuid are different %s != %s or disk name different %s != %s",
                              gluster_disk_ids[brick][0], gluster_disk_ids[brick][2],
                              ma_dict[brick][2], gluster_disk_ids[brick][3], ma_dict[brick][3])
                status = False
            self.log.info("Ids same for %s or %s, %s equals %s", gluster_disk_ids[brick][3],
                          gluster_disk_ids[brick][1],
                          gluster_disk_ids[brick][2], ma_dict[brick][2])
        self.log.info(
            "brick ids checked and are same for gluster and node disk used")
        return status

    def gluster_healthy_brick_status(self, host_id, device_os):
        """
        Check gluster brick healthy or not from brick information
        Args:
            host_id(name) --> Client id for Media Agent
            device_os(name) --> path for brick
        Return:
            True/False
        """
        brick = self.node_brick_info(host_id, device_os)
        if int(brick[0]) == 1 and (int(brick[1]) != 23 or int(brick[2]) != 15):
            err_msg = f"Brick configured, with bad BrickHealth {brick[1]} or BlockDeviceHealth {brick[2]}"
            self.log.error(err_msg)
            raise Exception(err_msg)
        if not int(brick[0]) & 1:
            self.log.error(
                "{0} Brick does not have the flag set to 1".format(brick[3]))
            return False
        if int(brick[1]) != 23:
            self.log.error(
                "{0} Brick does not have the BrickHealth set to 23".format(brick[3]))
            return False
        if int(brick[2]) != 15:
            self.log.error(
                "{0} Brick does not have the BlockDeviceHealth set to 15".format(brick[3]))
            return False
        self.log.info(
            "Flags, brickHealth and BlockDeviceHealth correctly set for {0}".format(brick[3]))
        return True

    def gluster_disk_health(self, mas, ma_dict):
        """
        Verify if all the bricks are healthy for the gluster
        or not.
        Args:
            mas(list) --> list of media agents
             ma_dict(dictionary) --> output of get_disk_uuid ( before creation)
        Return:
            True/False

        """
        bricks = self.gluster_brick_information(mas[0][1])
        for brick in bricks:
            host_id = ma_dict[brick][4]
            disk = ma_dict[brick][3]
            self.log.info("Host id %s and disk %s ", host_id, disk)
            if not self.gluster_healthy_brick_status(host_id, disk):
                self.log.error("Flags, brickHealth and BlockDeviceHealth bad for %s and %s",
                               host_id, disk)
                return False
        return True

    def update_storage_policy(self, name, rename, sql_login, sql_sa_password):
        """
        Updating storage policy name for the given storage pool
        Args:
            name(name) --> Storage Pool Name
            rename(name) --> New name for Storage Pool
            sql_login(name) --> SQL login username
            sql_sa_password(name) --> SQL login password
        Return:
            New name for Storage Pool Policy
        """
        self.log.info("Updating GDSP for %s", name)
        storage_pool_details = self.get_storage_pool_details(name)
        gdspid = storage_pool_details.storage_pool_id
        # rename = "rename " + name
        query = """update archGroup  
                set name = '{0}' 
                where id = {1}""".format(str(rename), str(gdspid))
        self.execute_update_query(query, sql_login, sql_sa_password)
        self.commcell.refresh()
        self.commcell.storage_pools.refresh()
        return rename

    def get_hostname(self, host_id):
        """
        Get hostname for the hostid
        Args:
            host_id (int) -- hostid
        Return:
            hostname
        """
        self.log.info("Getting hostname for id %s", host_id)
        query = " select net_hostname from App_Client where id = " + \
            str(host_id)
        self.log.info(query)
        self.csdb.execute(query)
        hostname = self.csdb.fetch_one_row()
        self.log.info("For id %s, hostname is %s", host_id, hostname[0])
        return hostname[0]

    def gluster_vol_info(self, media_agent):
        """
        Getting gluster volume information form node
        Args:
            media_agent (name) -- node
        Return:
            Volume information
        """
        self.log.info("getting volume information")
        ma_session = Machine(media_agent, self.commcell)
        command = "df -h | grep '/ws/glus'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        if output.output:
            glus_info = output.output.split("\n")[-2].split()
            self.log.info("Glus info %s", glus_info)
            return glus_info
        self.log.error("No gluster /ws/glus present on node %s", media_agent)
        return []

    def check_new_gluster_volume_size(self, media_agent):
        """
        Checking gluster volume permissible size
        Args:
            media_agent (name) -- host
        Return:
            True/False
        """
        glus_metadata_factor = 4  # percentage
        self.log.info("Verifying gluster volume size against glus_metadata_factor %s (percentage)",
                      glus_metadata_factor)
        glus_info = self.gluster_vol_info(media_agent)
        total_size = float(glus_info[1].lower().replace('g', ''))
        metadata_used = float(glus_info[2].lower().replace('g', ''))
        permissible_size = (total_size * glus_metadata_factor) / 100
        self.log.info("Total size of gluster %s and metadata used %s and permissible is %s",
                      total_size, metadata_used, permissible_size)
        if metadata_used <= permissible_size:
            self.log.info("Gluster size permissible for node %s", media_agent)
            return True
        self.log.error("Gluster size not permissible for node %s", media_agent)
        return False

    def node_brick_info(self, host_id, device_os):
        """
        Get information for the brick present on the node
        Args:
            host_id(name) --> Clint id for the Media Agent
            device_os(name) --> path for the brick
        Return:
            Brick information if present (list)
        """

        query = """select flags,BrickHealth, BlockDeviceHealth, deviceospath, diskId, deviceId from mmdiskhwinfo where 
                mountpathusagetype = 2 and hostid = {0} and deviceOSPath = '{1}'""".format(str(host_id), str(device_os))
        self.log.info(query)
        self.csdb.execute(query)
        brick = self.csdb.fetch_one_row()
        if not str(brick[0]):
            self.log.info("Brick %s not present on node %s",
                          device_os, host_id)
            raise Exception("Brick not present on node")
        self.log.info("Brick %s present on node %s ", brick, host_id)
        return brick

    def gluster_single_brick_info(self, media_agent, pool, brick):
        """
        Get brick information for the gluster if it is part of the gluster or not
        Args:
            media_agent(name) --> Media Agent
            pool(name) --> Storage Pool name
            brick(name) --> brick name
        Return:
            Brick information which is part of gluster (list)
        """

        self.log.info("Checing brick %s part of gluster or not", brick)
        pool = self.gluster_name_for_storage_pool(pool)
        ma_session = Machine(media_agent, self.commcell)
        search = media_agent.lower() + "sds:" + str(brick)
        command = "gluster v status " + \
            str(pool) + " | grep '" + search + "'| awk '{print $1,$2,$5,$6}'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        if output.exception:
            self.log.error("brick %s not part of gluster %s", brick, pool)
            # raise Exception("Brick not part of gluster")
            self.log.info(output.exception)
            return []
        brick_info = output.output.replace("\n", "").split()
        self.log.info(
            f"output: {output.output} exception: {output.exception}, exception_message: {output.exception_message}")
        self.log.info(
            f"brick_info: {brick_info}. len(brick_info): {len(brick_info)}")
        if len(brick_info) != 4:
            brick_info = []
            command = "gluster v status " + \
                str(pool) + " | grep '" + search + \
                "' -A 1 | awk '{print $1,$2,$4,$5}'"
            self.log.info(command)
            output = ma_session.execute_command(command)
            brick_output = output.output.replace("\n", "").split()
            self.log.info(
                f"brick_output: {brick_output}. len(brick_output): {len(brick_output)}")
            brick_output[1] = brick_output[1] + brick_output[2]
            brick_info.extend(
                [brick_output[0], brick_output[1], brick_output[4], brick_output[5]])
        self.log.info(
            "Brick part of gluster %s \nBrick information %s ", pool, brick_info)
        return brick_info

    def check_gluster_brick_online(self, media_agent, pool, brick):
        """
            Verify disk part of gluster or not and online or not
            Args:
                media_agent(name) --> Media Agent of pool
                pool(name) --> storage pool name
                brick(name) --> brick to be verified
            Return:
                 True/False
        """
        gluster_brick = self.gluster_single_brick_info(
            media_agent, pool, brick)
        if len(gluster_brick) != 0:
            if str(gluster_brick[2]) == "Y":
                self.log.info("Brick %s online %s for gluster %s ", brick,
                              gluster_brick[2], pool)
                return True
        self.log.error("Brick %s not online for gluster %s ", brick, pool)
        return False

    def brick_flag_status(self, hostid, device_os):
        """
        Get flag information for the brick and identify over the flag
       Args:
           hostid(name) --> Clint id for the Media Agent
           device_os(name) --> path for the brick
       Return:
          Flag value
               """
        self.log.info("Checking Flag status for brick")
        brick = self.node_brick_info(hostid, device_os)
        flag = int(brick[0])
        if flag & 0:
            self.log.info(
                "Flag %s Brick %s not configured for host %s ", flag, device_os, hostid)
            raise Exception("brick not configured")
        if flag & 1:
            self.log.info("Flag %s Brick %s configured for host %s ",
                          flag, device_os, hostid)
        if flag & 2:
            self.log.info(
                "Flag %s Replace initiated for\t Brick %s configured for host %s ", flag, device_os, hostid)
        if flag & 4:
            self.log.info(
                "Flag %s Replace submitted for\t Brick %s configured for host %s ", flag, device_os, hostid)
        if flag & 8:
            self.log.info(
                "Flag %s Replace Failed for \t Brick %s configured for host %s ", flag, device_os, hostid)
        if flag & 16:
            self.log.info("Flag %s Brick missing in health update, broken or offline for \t"
                          "Brick %s configured for host %s ", flag, device_os, hostid)
        self.log.info("Flag value %s", flag)
        return flag

    def replace_brick(self, media_agent, brick_id, pool):
        """
                Trigger disk replacement
                        Args:
                           pool (name) -- storage_pool_name
                           media_agent (name) -- media_agent
                           brick_id (int) -- diskId
                        Return:
                            status, response
        """
        self.log.info("Triggering Disk replacement over node %s"
                      "on brick %s", media_agent, brick_id)

        storage_details = self.get_storage_pool_details(pool)

        storage_details.hyperscale_replace_disk(brick_id, media_agent, pool)
        time.sleep(20)
        flag = self.get_disk_by_disk_id(brick_id)[0]
        self.commcell.storage_pools.refresh()
        response = self.get_storage_pool_details(pool)
        self.log.info(response)
        return flag, response

    def replace_log_status(self, media_agent, from_line=0):
        """
        Getting log details for replace brick
        flag = 0 no log lines,
        flag = 1 Replace Failure
        flag = 2 Replace Success

            Args:

                media_agent         (str)           --  The MA name

                from_line           (int)           --  The line number of CVMA.log after which to verify the logs

            Returns:

                status, response    (bool, list)    --  Whether verified or not, log lines
        """
        status = False
        flag = 0
        self.log.info(
            "Getting Replace status response from node %s", media_agent)
        ma_session = Machine(media_agent, self.commcell)
        client = self.commcell.clients.get(media_agent)

        client_log_directory = client.log_directory
        if not client_log_directory:
            message = f"Please check if {media_agent} is up including Commvault services."
            message += f" log directory = {client_log_directory}."
            raise Exception(message)
        client_cvma_log_path = f"{client_log_directory}/CVMA.log"

        version_info = int(client.version)
        service_pack = client.service_pack
        self.log.info(
            "Version information %s, Service Pack information %s", version_info, service_pack)
        sp_info = int(service_pack)
        self.log.info("Service Pack info %s", sp_info)
        command = "gluster v status | grep 'Status of volume:' | awk '{print $4}'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        gluster_name = output.output.replace("\n", "")
        gluster_flag = False
        command_fail = f'tail -n +{from_line} {client_cvma_log_path}' \
                       ' | grep "CVMAGlusStoragePool::ReplaceDisk" | tail -8'
        self.log.info("Waiting")
        time.sleep(120)
        self.log.info(command_fail)
        output = ma_session.execute_command(command_fail)
        log_line = output.output.split("\n")
        log_line = log_line[: len(log_line) - 1]
        for index in range(len(log_line)):
            log_line[index] = " ".join(log_line[index].split())
            if gluster_name in log_line[index]:
                gluster_flag = True
            if "Replace brick failure" in log_line[index]:
                status = False
                flag = 1
            elif "Reset brick failure" in log_line[index] and int(sp_info) >= 16:
                status = False
                flag = 1
        if flag == 1 and gluster_flag is True:
            return status, log_line
        time.sleep(30)
        command_success = f'tail -n +{from_line} {client_cvma_log_path}' \
                          ' | grep "CVMAGlusStoragePool::ReplaceDisk" | tail -7'
        self.log.info(command_success)
        self.log.info("Waiting")
        time.sleep(120)
        output = ma_session.execute_command(command_success)
        log_line = output.output.split("\n")
        log_line = log_line[: len(log_line) - 1]
        gluster_flag = False
        for index in range(len(log_line)):
            log_line[index] = " ".join(log_line[index].split())
            if gluster_name in log_line[index]:
                gluster_flag = True
            if "Replace Success" in log_line[index] and int(sp_info) < 16:
                status = True
                flag = 2
            elif "Reset Success" in log_line[index] and int(sp_info) >= 16:
                status = True
                flag = 2
        if flag == 2 and gluster_flag is True:
            return status, log_line
        self.log.info("Cannot grab success or failure status and logs")
        return status, []

    def replace_brick_available(self, media_agent):
        """
            Disk present for replace or not
            Args:
                media_agent(name) -- Node/media agent
            Return:
                True/False
        """
        status = True
        self.log.info("Checking raw disk availability or not ")
        time.sleep(120)
        ma_session = Machine(media_agent, self.commcell)
        command = r'bzgrep "CVMAGlusStoragePool::ReplaceDisk" ' \
                  r'/var/log/commvault/Log_Files/CVMA.log | tail -4 | ' \
                  r'grep " Replace brick failure, not able to find replacing brick"'
        self.log.info(command)
        output = ma_session.execute(command)
        if output.output:
            status = False
            log_line = output.output.split("\n")
            log_line = log_line[: len(log_line) - 1]
            for index in range(len(log_line)):
                log_line[index] = " ".join(log_line[index].split())
            self.log.info(log_line)
            return status
        self.log.info("Disk available for replacement")
        return status

    def get_disk_by_disk_id(self, disk_id):
        """
        Get disk information for the given disk Id
        Args:
            disk_id(name) --> Disk Id for the disk
        Return:
            disk information (list)
        """
        self.log.info("Getting brick information for diskId %s", disk_id)
        query = """select flags,BrickHealth, BlockDeviceHealth, deviceospath, hostId, deviceId from mmdiskhwinfo where  
                mountpathusagetype = 2 and diskId = {0}""".format(str(disk_id))
        self.log.info(query)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        self.log.info(row)
        return row

    def heal_disk_entry(self, media_agent, new_path):
        """
        Check if disk replaced is healed or not, entry present in the directory
        /opt/commvault/iDataAgent/jobResults/ScaleOut/ReplaceBricksFile
        Args:
            media_agent(name) --> media Agent on which replace carried out
            new_path(name) --> disk path
        Return:
            True/False
        """
        self.log.info("Checking entry %s for disk heal", new_path)
        status = False
        ma_session = Machine(media_agent, self.commcell)
        command = "bzgrep '" + \
            str(new_path) + \
            "' /opt/commvault/iDataAgent/jobResults/ScaleOut/ReplaceBricksFile"
        self.log.info(command)
        output = ma_session.execute_command(command)
        if output.output:
            status = False
            self.log.info("Gluster heal in progress for %s", new_path)
            self.log.info(output.output)
            return status

        status = True
        self.log.info("Gluster heal complete for %s ", new_path)
        self.log.info(output.output)
        return status

    def check_fstab_entry(self, media_agent, disk):
        """
            Checking entry in /etc/fstab for the disk on given ma
            Args:
                media_agent (name) -- MediaAgent
                disk (name) -- Brick/disk on Ma
            Return:
                list output of entry
        """
        self.log.info("Checking Fstab entry %s on node %s", disk, media_agent)
        ma_session = Machine(media_agent, self.commcell)
        command = "bzgrep '" + str(disk) + "' /etc/fstab"
        self.log.info(command)
        output = ma_session.execute_command(command)
        self.log.info(output.output)
        return output.output.replace("\n", "").split()

    def replace_fstab_entry(self, media_agent, old_entry, new_entry):
        """
        CHecks fstab entry being replaced or not after brick repalcement
        Args:
            media_agent(name) --> Media Agent
            old_entry(list) --> list input for old entry
            new_entry(list) --> list input for new entry
        Return:
            True/False
        """
        self.log.info(" Fstab entries for old disk %s and new disk %s", old_entry,
                      new_entry)

        fstab_replace_status = self.verify_fstab_replace_entry(
            media_agent, new_entry)
        if new_entry and fstab_replace_status:
            if old_entry[0] != new_entry[0]:
                res = "Disk Replacement success, Verified ids for new disk entry {0} " \
                      "\nRemoved old entry {1} and added new entry {2}".format(new_entry,
                                                                               old_entry, new_entry)
                self.log.info(res)
                return True, res
            if old_entry[0] == new_entry[0]:
                res = "old {0} " \
                      "same as new {1}. Verified the ids for the disk {2}".format(
                          old_entry, new_entry, new_entry)
                self.log.info(res)
                return True, res
        if old_entry[0] == new_entry[0]:
            res = "Old entry {0} not removed from fstab".format(old_entry)
            self.log.info(res)
            # raise Exception("Old entry not removed")
            return False, res
        if not fstab_replace_status:
            res = "Ids not same for the entry and sd name mounted as"
            self.log.info(res)
            return False, res

    def verify_fstab_replace_entry(self, media_agent, fstab_info):
        """
            Verify same disk ids, for entry in fstab and mounted on gluster
            Args:
                media_agent(name) -- MediaAgent
                fstab_info (name string) -- fstab entry of disk
        """
        self.log.info("Verifying uuid for entry %s", fstab_info)
        ma_session = Machine(media_agent, self.commcell)
        command = "df -h | grep " + str(fstab_info[1])
        self.log.info(command)
        output = ma_session.execute_command(command)
        self.log.info(output.output)
        sd_name = output.output.replace("\n", " ").split()
        self.log.info("For disk %s, mounted with sd name %s",
                      fstab_info[1], sd_name[0])
        self.log.info("Getting uuid for %s", sd_name[0])
        command2 = "blkid " + str(sd_name[0])
        self.log.info(command2)
        output_id = ma_session.execute_command(command2)
        self.log.info(output_id.output)
        id_info = output_id.output.replace("\n", " ").split()
        self.log.info(
            "Verifying ids same for %s which is mounted as %s", fstab_info[1], sd_name[0])
        if fstab_info[0] == id_info[1].replace('"', ""):
            self.log.info("Fstab entry for %s is same for mounted as %s with id as %s and %s", fstab_info[1],
                          sd_name[0], fstab_info[0], id_info[1])
            return True
        self.log.info("Fstab entry for %s is NOT same for mounted as %s with id as %s and %s", fstab_info[1],
                      sd_name[0], fstab_info[0], id_info[1])
        return False

    def gluster_heal_entries(self, media_agent, pool):
        """
            Checking Heal entries, value should reach 0 after heal process
            Args:
                media_agent(name) -- media Agent/ node
                pool(name) -- storage pool name
            Return:
                True/False
        """
        status = False
        self.log.info(
            "Checking heal entries and making sure they turn to 0 for heal process")
        pool = self.gluster_name_for_storage_pool(pool)
        ma_session = Machine(media_agent, self.commcell)
        command = r"gluster v heal " + \
            str(pool) + " info | grep 'Number of entries:'"
        while status is not True:
            self.log.info("Checking gluster heal entries: ")
            output = ma_session.execute(command)
            self.log.info(output.output)
            entries = output.output.replace("\n", " ").split()
            entry_sum = 0
            for entry in entries:
                if entry.isdigit():
                    entry_sum += entry_sum + int(entry)
            if entry_sum == 0:
                status = True
                break
            time.sleep(30)
        return status

    def verify_replace_gluster_size(self, before_replace, after_replace):
        """
                Checking gluster volume  size
                Args:
                    before_replace (list) -- gluster info before replace
                    after_replace (list) -- gluster info after replace
                Return:
                    True/False
                """
        self.log.info("Verifying Gluster size info before replacement request and after replacement request\n"
                      "Gluster size before replacement request %s \n Gluster size after replacement request %s", before_replace, after_replace)
        total_size_before = float(before_replace[1].lower().replace('g', ''))
        used_before = float(before_replace[2].lower().replace('g', ''))
        available_before = float(before_replace[3].lower().replace('g', ''))
        total_size_after = float(after_replace[1].lower().replace('g', ''))
        used_after = float(after_replace[2].lower().replace('g', ''))
        available_after = float(after_replace[3].lower().replace('g', ''))
        self.log.info("\nTotal gluster size before %s, used %s, available %s\n"
                      "Total gluster size after replace is %s, used %s, available %s\n", total_size_before,
                      used_before, available_before, total_size_after, used_after, available_after)

        if (total_size_before == total_size_after) and (used_before == used_after) and \
                (available_before == available_after):
            self.log.info("Gluster size same after replacement request ")
            return True
        self.log.info("Gluster size different after replace request")
        return False

    def get_subvolume_for_pool(self, storage_pool_name):
        """
            Getting subvolume names for the storage_pool
            Args:
                storage_pool_name (name) --> storage_pool_name
            Returns:
                sub_volume_name (list)
        """
        self.log.info("Getting subVolume names for SP %s", storage_pool_name)
        time.sleep(120)
        self.commcell.storage_pools.refresh()
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        host_ids = self.get_all_nodes_hostids(storage_pool_name)
        ids = ",".join(str(id) for id in host_ids)
        query = """ select distinct SubVolume 
                    from MMDiskHWInfo 
                    where hostId in ({0})""".format(str(ids))
        self.log.info(query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info("Sub Volumes for pool %s are %s",
                      storage_pool_name, rows)
        return rows

    def get_all_bricks_for_subvolume(self, sub_volume):
        """
            Get all bricks belonging to a sub volume
            Args:
                sub_volume(name) --> SubVolume
            Returns:
                bricks(list)
        """
        self.log.info(
            "Getting all bricks belonging to the sub volume %s", sub_volume)
        time.sleep(300)
        query = """select flags,BrickHealth, BlockDeviceHealth, deviceospath, hostId, deviceId, diskId 
                 from mmdiskhwinfo where  
                mountpathusagetype = 2 and SubVolume = '{0}'""".format(str(sub_volume))
        self.log.info(query)
        self.csdb.execute(query)
        bricks = self.csdb.fetch_all_rows()
        self.log.info("Bricks belonging to sub volume %s are %s",
                      sub_volume, bricks)
        return bricks

    def ma_service_down(self, media_agent):
        """
            Making MA services for node offline and not accessible
            Args:
                media_agent(name) --> Media Agent
            Return:
                Machine Object
        """
        self.log.info("Making media agent services down for %s", media_agent)
        client = self.commcell.clients.get(media_agent)
        self.log.info(
            "Bringing down Commvault Media Mount Manager MA services")
        client.execute_command("pkill CvMountd")
        self.log.info("Node %s Media Mount Manager  Down", media_agent)

    def ma_service_up(self, media_agent):
        """
            Making MA services for node online and accessible again
            Args:
                media_agent(name) --> Media Agent
        """
        self.log.info("Making media agent services up for %s", media_agent)
        ma_session = Machine(media_agent, self.commcell)
        client = self.commcell.clients.get(media_agent)
        self.log.info("Bringing up Commvault Media Mount Manager MA services")
        client.start_service("CvMountd")
        try:
            output = ma_session.execute_command("commvault restart")
        except Exception as exp:
            self.log.info("Exception %s", exp)
            self.log.info("Restarted Services")
            pass
        time.sleep(120)
        self.log.info("Node %s Commvault Media Mount Manager Up", media_agent)

    def check_restore_folders(self, media_agent, backup_path, restore_path):
        """
            Create machine object for media_agent and compare backup and restore
            Here source and destination machine are same
            Args:
                media_agent(name) -> Media_Agent
                backup_path(name) -> source destination of file
                restore_path(name) -> restore destination of file
            Return:
                Output(list)
        """
        self.log.info("Verifying Restore data")
        ma_session = Machine(media_agent, self.commcell)
        destination_ma = Machine(media_agent, self.commcell)
        output = ma_session.compare_files(
            destination_ma, backup_path, restore_path)
        self.log.info(output)
        return output

    def gluster_mount(self, media_agent):
        """
            Check /ws/glus mounted on ma or not
            Args:
                media_agent(name) --> media Agent
            Return:
                True/False
        """
        self.log.info("checking /ws/glus mount on %s", media_agent)
        ma_session = Machine(media_agent, self.commcell)
        # checking /ws/ddb mount on node or not
        mount = r"df -h | grep '/ws/glus' | awk '{print $1}'"
        mount_output = ma_session.execute_command(mount)
        if not mount_output.output:
            self.log.error("No mount path for /ws/glus over %s ", media_agent)
            return False
        self.log.info("/ws/glus is mounted")
        return True

    def unmount_brick(self, media_agent, disk, pool):
        """
            Un mounting brick from gluster
            Args:
                media_agent(name) --> node
                disk(name) --> brick to un mount
                pool(name) --> storage pool
        """
        self.log.info("Un Mounting %s from gluster on node %s ",
                      disk, media_agent)
        brick_info = self.gluster_single_brick_info(media_agent, pool, disk)
        pid = brick_info[-1]
        self.log.info("Pid to kill %s and un mount disk %s", pid, disk)
        ma_session = Machine(media_agent, self.commcell)
        if pid != "N/A":
            command = "kill -9 " + str(pid)
            self.log.info(command)
            output = ma_session.execute_command(command)
            self.log.info(output.output)
            ma_session.execute_command("umount " + str(disk))

        self.log.info("Checking gluster brick status")
        status = self.check_gluster_brick_online(media_agent, pool, disk)
        if not status:
            self.log.info("gluster disk %s not online", disk)
        try:
            output = ma_session.execute_command("commvault restart")
        except Exception as exp:
            self.log.info("Exception %s", exp)
            self.log.info("Restarted Services")
            pass
        time.sleep(120)
        self.log.info("gluster disk un mounted")

    def mount_brick(self, media_agent, disk, pool):
        """
            Mounting disk back to gluster
            Args:
                media_agent(name) --> node
                disk(name) --> brick to un mount
                pool(name) --> storage pool
        """
        self.log.info("Mounting %s back to gluster on node %s ",
                      disk, media_agent)
        gluster_name = self.gluster_name_for_storage_pool(pool)
        self.log.info("Checking gluster brick status")
        status = self.check_gluster_brick_online(media_agent, pool, disk)
        if not status:
            self.log.info("gluster disk %s not online", disk)
        ma_session = Machine(media_agent, self.commcell)
        command = "mount " + str(disk)
        ma_session.execute_command(command)
        self.log.info("Restarting gluster to get brick online")

        # Run echo "y" | gluster v stop storage_pool_name
        output = ma_session.execute_command(
            "echo \"y\" | gluster v stop " + str(gluster_name))
        self.log.info(output.output)
        # gluster v start storage_pool_name
        output = ma_session.execute_command("gluster v start " + str(gluster_name)
                                            + " force")
        self.log.info(output.output)
        self.log.info("Checking gluster brick status")
        status = self.check_gluster_brick_online(media_agent, pool, disk)
        if not status:
            self.log.info("gluster disk %s not online", disk)
        try:
            output = ma_session.execute_command("commvault restart")
        except Exception as exp:
            self.log.info("Exception %s", exp)
            self.log.info("Restarted Services")
            pass
        time.sleep(120)
        self.log.info("gluster disk mounted back")

    def verify_reset_brick(self, media_agent, pool, disk):
        """
            Verifying reset-brick used over SP16+
            Args:
                media_agent(name) --> Media Agent/ Node
                pool(name) --> Storage Pool name
                disk(name) --> Disk replaced
            Return:
                True/False
        """
        self.log.info("Verifying reset-brick used over SP16+")
        pool = self.gluster_name_for_storage_pool(pool)
        disk_name = str(media_agent) + "sds:" + str(disk) + "/ws_brick"
        regex = "reset-brick " + str(pool) + " " + str(disk_name)
        command = "bzgrep '" + \
            str(regex) + "' /var/log/commvault/Log_Files/CVMA.log | tail -2"
        ma_session = Machine(media_agent, self.commcell)
        client = self.commcell.clients.get(media_agent)
        version_info = int(client.version)
        service_pack = client.service_pack
        self.log.info(
            "Version information %s, Service Pack information %s", version_info, service_pack)
        sp_info = int(service_pack)
        output = ma_session.execute_command(command)
        log_info = output.output.split("\n")
        log_info = log_info[:len(log_info) - 1]
        if len(output.output) != 0:
            for log in log_info:
                self.log.info(log)
            if int(sp_info) >= 16:
                self.log.info(
                    "Service pack version %s higher than 16", sp_info)
                self.log.info("Reset command used")
                return True
            self.log.info("Service pack version %s lower than 16", sp_info)

        self.log.info("Reset command not used")
        return False

    def brick_data_being_written(self, media_agent, disk):
        """
            Get brick data written while backup is running
            Args:
                media_agent(name) --> Media Agent
                disk(name) --> brick of gluster
            Return:
                list of data and disk
        """
        self.log.info("Check disk %s is in use or not", disk)
        ma_session = Machine(media_agent, self.commcell)
        command = "du " + str(disk) + " | awk '{print $1,$2}'"
        output = ma_session.execute_command(command)
        res = output.output.split("\n")
        res = res[: len(res) - 1]
        check = res[-1].split()
        self.log.info("Data usage over %s is %s", disk, check)
        return check

    def check_brick_in_use(self, media_agent, disk):
        """
            Check if brick under use or not
            Args:
                media_agent(name) --> Media Agent
                disk(name) --> brick of gluster
            Return:
                True/False
        """
        old = self.brick_data_being_written(media_agent, disk)
        self.log.info("Wait some time")
        time.sleep(30)
        new = self.brick_data_being_written(media_agent, disk)
        if old[0] != new[0]:
            self.log.info(
                "Disk %s under usage, old %s and new %s", disk, old, new)
            return True
        return False

    def check_gluster_metadata(self, storage_pool_name):
        """
            Check gluster metadata present after pool expansion
            Args:
                storage_pool_name(name) --> Storage Pool Name
            Return:
                True/Exception
        """
        self.log.info("Checking gluster meta data over expansion")
        commserve = self.commcell.commserv_name
        ma_session = Machine(commserve, self.commcell)
        media_agents = self.get_associated_mas(storage_pool_name)
        client = self.commcell.clients.get(self.commcell.commserv_name)
        service_pack = client.service_pack
        sp_info = int(service_pack)
        regex = "C:\\temp\\glusterd__{0}.tar.gz"
        regex2 = client.job_results_directory + \
            "\\ScaleOut\\glusterd__{0}.tar.gz"
        for media_agent in media_agents:
            hostid = self.get_host_id(media_agent[0])
            self.log.info("Checking gluster metadata for hostid %s ", hostid)
            self.log.info("checking path %s or %s", regex2.format(
                hostid), regex2.format(hostid))
            if not ma_session.check_file_exists(regex.format(hostid)) and \
                    not ma_session.check_file_exists(regex2.format(hostid)) and sp_info < 20:
                self.log.error("%s not present for %s",
                               regex.format(hostid), media_agent[0])
                self.log.error("OR %s not present for %s",
                               regex2.format(hostid), media_agent[0])
                raise Exception("Glustermeta data not present")
        return True

    def is_gluster_metadata_present_in_csdb(self, ma_name):
        """Checks if CSDB contains the gluster metadata entry for the MA.

            Args:
                ma_name         (str)           --  MA name

            Returns:
                bool - Whether entry is present or not
        """
        if not self.commcell.clients.has_client(ma_name):
            raise Exception(
                f"Client {ma_name} doesn't exist within the Commcell")

        hostid = self.commcell.clients[ma_name.lower()]['id']
        query = f'select * from MMScaleOutMAInfo WITH (NOLOCK) where ClientId={hostid}'
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()[0]
        if not row:
            return False
        return True

    def get_ddb_hosts(self, storage_pool_name):
        """
        Get hosts, for the ddb partitions
        Args:
            storage_pool_name(name) --> Storage Pool Name
        Return:
            list of host ids
        """
        self.log.info(
            "Getting hosts for dedup partitions present for pool %s", storage_pool_name)
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        gdsp = storage_pool_details.storage_pool_id
        query = """
            select distinct substore.ClientId from 
            IdxSIDBSubStore as substore, IdxSIDBStore as idx, archGroup as arc, MMSDSStoragePool as storage, 
            archCopySIDBStore sidb 
            where storage.GDSPId = arc.id and
            arc.defaultCopy = sidb.CopyId and
            sidb.SIDBStoreId = idx.SIDBStoreId and 
            idx.SIDBStoreId = substore.SIDBStoreId and  
            storage.GDSPId = {0}
        """.format(gdsp)
        self.log.info(query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info("Hosts with ddb partitions present are %s", rows)
        return rows

    def check_control_node(self, media_agent):
        """
        Check controlnode or datanode for host
        Args:
            media_agent(name) --> Media Agent
        Return:
            True/False
        """
        self.log.info("Checking control node or not")
        ma_session = Machine(media_agent, self.commcell)
        command = "bzgrep 'HyperScaleNodeType' /etc/CommVaultRegistry/Galaxy/Instance001/MediaAgent/.properties |" \
                  " awk '{print $2}'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        formatted_output = output.output.replace("\n", "").lower()
        if formatted_output == 'control':
            self.log.info("Host %s is control node", media_agent)
            return True
        self.log.info("Host %s is data node", media_agent)
        return False

    def check_ddb_move_job(self, storage_pool_name):
        """
        Check job initiated and status for ddb move over expansion
        Args:
            storage_pool_name(name) --> Storage Pool Name
        Return:
            list of jobs
        """
        self.log.info("checking ddb move job over expansion")
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        gdsp = storage_pool_details.storage_pool_id
        query = """
        select jobId, status from JMAdminJobStatsTable where opType = 99 and archGrpID = {0}
        """.format(gdsp)
        self.log.info(query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        if len(rows[0][0]) > 0:
            self.log.info("DDB Move job initiated with jobs %s ", rows)
            for job in rows:
                status = job[1]
                if int(status) == 1:
                    self.log.info(
                        "Job %s is completed with status %s", job[0], job[1])
                else:
                    self.log.info("Job %s with status %s", job[0], job[1])
            return True
        self.log.info("DDB Move job not initiated")
        return False

    def check_sds_entry(self, entry, media_agent):
        """
        check sds entry populated over ma
        Args:
            entry(name) --> media agent entry to check
            media_agent(name) --> Media Agent on which to check
        Return:
            True/False
        """
        self.log.info("Checking %s sds entry on %s", entry, media_agent)
        regex = entry + "sds"
        ma_sessin = Machine(media_agent, self.commcell)
        command = "bzgrep '{0}' /etc/hosts".format(regex)
        self.log.info(command)
        output = ma_sessin.execute_command(command)
        if output.output:
            self.log.info("Entry %s sds present on host %s",
                          entry, media_agent)
            return True
        self.log.info("Entry %s sds not present on host %s",
                      entry, media_agent)
        return False

    def bkp_job_details(self, job_id):
        """
        Get Job details for the job id
        Args:
            job_id(name) --> Job Id
        Return:
            job details
        """
        self.log.info("Getting job details for job %s", job_id)
        job_id = int(job_id)
        job_obj = self.commcell.job_controller.get(job_id)
        details = job_obj._get_job_details()
        job_details = details['jobDetail']['generalInfo']
        for detail in job_details:
            self.log.info("Details: %s --> %s", detail, job_details[detail])

        return job_details

    def admin_job_details(self, job_id):
        """
        Get Job details for the job id
        Args:
            job_id(name) --> Job Id
        Return:
            job details
        """
        self.log.info("Getting job details for job %s", job_id)
        job_id = int(job_id)
        job_obj = self.commcell.job_controller.get(job_id)
        details = job_obj._get_job_summary()
        # job_details = details['jobDetail']['generalInfo']
        for detail in details:
            self.log.info("Details: %s --> %s", detail, details[detail])

        return details

    def kill_sds_network(self, media_agent, add_mas):
        """
        Kill sds network for media agent

        Args:
            media_agent(name) --> Media Agent
            add_mas (list) --> List of Additional nodes
        """

        ma_session = Machine(media_agent, self.commcell)
        ma_session.copy_folder("/etc/hosts", "/root/")
        command = "cat /etc/hosts | grep -m 1 'sds' | cut -d'.' -f3 "
        output = ma_session.execute_command(command)
        if output.output != '':
            output = output.output.split("\n")[0]
        else:
            raise Exception("sds ip's not present on node")
        sds_ip = "192.168." + output + ".240"
        sds_ip = ipaddress.IPv4Address(sds_ip)
        for ma in add_mas:
            sds_ip = sds_ip + 1
            ma = ma + 'sds'
            command = "sed -i '/ma/s/[0-9]\\{1,3\\}\\.[0-9]\\{1,3\\}\\.[0-9]\\{1,3\\}\\.[0-9]\\{1,3\\}/ip/g' /etc/hosts".replace(
                'ma', ma).replace('ip', str(sds_ip))
            output = ma_session.execute_command(command)
            self.log.info(output.output)

    def start_sds_network(self, media_agent):
        """
        Restore and start sds network back online again

        Args:
            media_agent(name) --> Media Agent
        """
        ma_session = Machine(media_agent, self.commcell)
        ma_session.copy_folder("/root/hosts", "/etc/")

    def fill_gluster_volume(self, media_agent):
        """
        Fill gluster volume with random generated data
        bs --> buffer size (1Gb = 1073741824)
        Args:
            media_agent(name) --> Media Agent
        Return:
            Response
        """
        self.log.info("Filling gluster with random data")
        glus_info = self.gluster_vol_info(media_agent)
        available_size = int(glus_info[3].lower().replace('g', ''))
        self.log.info("Gluster availble size is %s", available_size)
        reserve_space = 2
        fill_size = available_size - reserve_space
        self.log.info(
            "Filling gluster with size %s and leaving reserve space %s", fill_size, reserve_space)
        ma_session = Machine(media_agent, self.commcell)
        self.log.info("Creating dummy folder under /ws/glus")
        ma_session.execute_command("mkdir /ws/glus/dummy")
        for i in range(fill_size):
            command = "dd if=/dev/zero of=/ws/glus/dummy/file{0}.txt count=1 bs=1073741824".format(
                i)
            self.log.info(command)
            ma_session.execute_command(command)
        self.log.info("FIlled gluster with size %s", available_size)

    def gluster_name_for_storage_pool(self, name):
        """
        Get gluster name, for the storage pool
        Args:
            name(str) --> storage Pool
        Return:
            Gluster_name(str)
        """
        self.log.info("Gluster name for the pool %s", name)
        details = self.get_storage_pool_details(name)
        gdsp = details.storage_pool_id
        media_agents = self.get_associated_mas(name)
        media_agent = media_agents[0][0]
        count = 5
        ma_session = None
        while count >= 0:
            try:
                ma_session = Machine(media_agent, self.commcell)
                status = True
            except Exception as exp:
                result = str(exp)
                self.log.exception(
                    "Exception occurred connecting to host %s ", result)
                count -= 1
                status = False
                self.log.info("Trying again")
                time.sleep(90)
                pass
            if status:
                break
        command = "gluster v status | grep 'Status of volume:' | awk '{print $4}'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        gluster_name = output.output.replace("\n", "")
        return gluster_name

    def sd_name_for_disk(self, media_agent, disk):
        """
        Getting sd/scuzzy name for the disk
        Args:
            media_agent --> Media Agent
            disk --> disk to format
        """
        self.log.info("Getting sd_name or scuzzy name for the disk %s", disk)
        ma_session = Machine(media_agent, self.commcell)
        command = "lsblk | grep '{0}'".format(disk)
        self.log.info(command)
        output = ma_session.execute_command(command)
        sd_name = output.output.split("\n")[0].split()[0]
        self.log.info("sd name for disk %s is %s", disk, sd_name)
        return sd_name

    def formatting_replaced_disk(self, media_agent, scuzzy_name):
        """
        Formatting disk and removing all data and file system present over it
        Args:
            media_agent --> Media Agent
           scuzzy_name --> sd name for the disk to be formatted
        """
        self.log.info(
            "Formatting replaced disk %s as sd name on media agent %s", scuzzy_name, media_agent)
        ma_session = Machine(media_agent, self.commcell)
        command1 = "dd if=/dev/zero of=/dev/{0}  bs=512  count=1".format(
            scuzzy_name)
        self.log.info(command1)
        output = ma_session.execute_command(command1)
        self.log.info(output.output)

    def size_of_disk_used_in_storagepool(self, media_agent, storage_pool_name):
        """
        Getting disk size for /ws/disk on the node used in storage pool
        Args:
            media_agent --> Media agent
            storage_pool_name --> storage pool name
        Return:
            size of disk used in gluster (int)
        """
        self.log.info("Getting disk size for %s on node %s",
                      storage_pool_name, media_agent)
        ma_session = Machine(media_agent, self.commcell)
        command = "df -h | grep '/ws/disk'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        self.log.info(output.output)
        disks = output.formatted_output
        disks = sorted(disks, key=itemgetter(3))
        gluster_disk = []
        for disk in disks:
            gluster_disk_info = self.gluster_single_brick_info(
                media_agent, storage_pool_name, disk[5])
            if len(gluster_disk_info) != 0:
                gluster_disk = disk
                break
        disk_size = gluster_disk[3]
        self.log.info("/ws/disk size used in gluster %s is %s for gluster disk %s",
                      storage_pool_name, disk_size, gluster_disk)
        return disk_size

    def disk_for_vertical_scaleout(self, media_agent, storage_pool_name):
        """
           Identifying disks available on node for Vertical scale out
           Args:
               media_agent --> Media Agent
               storage_pool_name --> storage pool name
            Return:
                list of disks available(list)
        """
        self.log.info(
            "Disks available on node %s for vertical scale out", media_agent)
        ma_session = Machine(media_agent, self.commcell)
        command = "echo \"q\" | (cd /opt/commvault/Base && ./CVSDS -d)"
        self.log.info(command)
        output = ma_session.execute_command(command)
        self.log.info(output.output)
        disk_size_req = self.size_of_disk_used_in_storagepool(
            media_agent, storage_pool_name)
        disk_size_req = float(
            ''.join(list(value for value in disk_size_req if value.isdigit())))
        disk_available = []
        for data in output.formatted_output:
            if '/dev/sd' in ''.join(data) \
                    and float(''.join(list(value for value in data[1] if value.isdigit()))) >= disk_size_req:
                data.append(media_agent)
                disk_available.append(data)
        self.log.info(
            "disk available for vertical scale out are %s", disk_available)
        return disk_available

    def minimum_disks_for_vertical_scaleout(self, storage_pool_name):
        """
        Getting minimum number of disks required to be present on each node for
        vertical scale out
        Args:
            storage_pool_name --> storage pool name
        Return:
            dictionary of hosts with disks, min required for vertical scaleout
            0 --> False(no apt disks present for Vertical scaleout)
        """
        self.log.info(
            "Verifying nodes have minimum number of disks available for vertical scale out")
        media_agents = self.get_associated_mas(storage_pool_name)
        self.log.info("Associated media agents are %s", media_agents)
        for media_agent in media_agents:
            self.log.info(media_agent[0])
        vertical_scaleout_disks = {}
        host, min_used = 'media_agent', sys.maxsize
        for media_agent in media_agents:
            if media_agent[0] not in vertical_scaleout_disks:
                vertical_scaleout_disks[media_agent[0]] = []
            vertical_scaleout_disks[media_agent[0]] = self.disk_for_vertical_scaleout(media_agent[0],
                                                                                      storage_pool_name)
            req = len(vertical_scaleout_disks[media_agent[0]])
            req = (req // 2) * 2
            if req <= min_used:
                min_used = req
            if req == 0:
                host = media_agent[0]
        if min_used == 0:
            self.log.error("Not correct number of disks present on host %s for vertical scaleout, disk count", host,
                           len(vertical_scaleout_disks[host]))
            return vertical_scaleout_disks, min_used
        self.log.info(
            "Minimum number of disk required for vertical scaleout %s", min_used)
        return vertical_scaleout_disks, min_used

    def adding_disk_vertical_scaleout(self, media_agent, disk):
        """
        Adding disks for vertical scale out
        Args:
            media_agent --> Media agent
            disk --> disk to be added for VS (/dev/sdx)
        Return:
            True/False
        """
        self.log.info("Adding disk %s over media agent %s", disk, media_agent)
        ma_session = Machine(media_agent, self.commcell)
        command = "echo -e \"{0}\\nq\" | (cd /opt/commvault/Base && ./CVSDS -d)".format(
            disk)
        self.log.info(command)
        output = ma_session.execute_command(command)
        self.log.info(output.output)
        if (HYPERSCALE_CONSTANTS['vertical_scaleout_add_disk_success'] in ''.join(output.formatted_output[-1]).lower()) \
                and (disk in ''.join(output.formatted_output[-1]).lower()):
            self.log.info("Added disk, Configure status for disk %s is %s",
                          disk, output.formatted_output[-1])
            return True
        self.log.error(output.output)
        self.log.info("configure status False")
        return False

    def mount_details(self, media_agent, path):
        """
        Get mount details for the path, for linux ma
        Args:
            media_agent --> media agent
            path --> path (which is to be verified and mount details fetched)
        Return:
            True/False --> if path mounted
            details for mount path(list)
        """
        self.log.info(
            "Getting mount details for path %s on MA %s", path, media_agent)
        ma_session = Machine(media_agent, self.commcell)
        mount_status = ma_session.is_path_mounted(path)
        self.log.info("Path mount status for %s is %s", path, mount_status)
        if mount_status:
            command = "df -h | grep '{0}'".format(path)
            self.log.info(command)
            output = ma_session.execute_command(command)
            mount_details = output.formatted_output.split()
            self.log.info("Mount details for %s is %s", path, mount_details)
            return mount_status, mount_details
        self.log.info("Disk %s is not mounted on %s", path, media_agent)
        return mount_status, []

    def vertical_scaleout_log_status(self, media_agent):
        """
        Getting status for vertical scale out from logs on media agent
        Args:
            media_agent --> media agent
        Return:
            flag = 0 no log lines,
            flag = 2 Success
        """
        self.log.info(
            "Getting vertical scaleout status logs from MA %s", media_agent)
        flag = 0
        ma_session = Machine(media_agent, self.commcell)
        command = "gluster v status | grep 'Status of volume:' | awk '{print $4}'"
        self.log.info(command)
        output = ma_session.execute_command(command)
        gluster_name = output.output.replace("\n", "")
        regex = 'bzgrep "CvProcess::system() - gluster volume add-brick\\' \
                '|CVMAWorker::add_bricks_to_gluster_volume\\' \
                '|CVMAWorker::AddBricksToGlusterVolume" /var/log/commvault/Log_Files/CVMA.log | tail -5'
        self.log.info(regex)
        output = ma_session.execute_command(regex)
        if output.output:
            for log in output.formatted_output:
                if HYPERSCALE_CONSTANTS['Add_Bricks_Success'] in " ".join(log).lower() and \
                        gluster_name.lower() in " ".join(log).lower():
                    self.log.info("Add Bricks To Gluster Volume Success, %s",
                                  HYPERSCALE_CONSTANTS['Add_Bricks_Success'])
                    for log_data in output.formatted_output:
                        log_data = ' '.join(log_data)
                        self.log.info(log_data)
                    flag = 2
                    return flag

            if flag != 2:
                self.log.info("No logs found!!")
            return flag
        self.log.info("No logs found!!")
        return flag

    def get_vm_object(self, server, username, password, name):
        """
        Get VM object for the vm name, for the server
        Args:
            server --> server url
            username --> username
            password --> password
            name --> name of vm
        Return:
            vm object/ Exception
        """
        hv_obj = HypervisorHelper.Hypervisor(
            [server], username, password, "vmware", self.commcell)
        vm_help_obj = HypervisorHelper.VMHelper.HypervisorVM(hv_obj, name)
        return vm_help_obj

    def get_ddb_reconstruction_job(self, storage_pool_name):
        """
        Get ddb reconstruction job for storage pool
        Args:
            storage_pool_name(name) --> Storage Pool Name
        Return:
            list of jobs
        """
        self.log.info("Getting ddb reconstruction job")
        storage_pool_details = self.get_storage_pool_details(storage_pool_name)
        gdsp = storage_pool_details.storage_pool_id
        query = """
        select jobId, status from JMAdminJobInfoTable where servStart = 
        (select max(servStart) from JMAdminJobInfoTable where opType = 80) and archGrpID = {0}
        """.format(gdsp)
        self.log.info(query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        if len(rows[0][0]) <= 0:
            self.log.info("No ddb reconstruction job running at present")
        else:
            job = rows[0]
            self.log.info("Job %s with status %s", job[0], job[1])
            return True, job
        self.log.info("Checking ddb reconstruction job if completed")
        query = """
                select jobId, status from JMAdminJobStatsTable where servStart = 
                (select max(servStart) from JMAdminJobStatsTable where opType = 80) and archGrpID = {0}
                """.format(gdsp)
        self.log.info(query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        if len(rows[0][0]) <= 0:
            self.log.info("No ddb reconstruction jobs")
            return False, []
        job = rows[0]
        self.log.info("Job %s with status %s", job[0], job[1])
        status = job[1]
        if int(status) == 1:
            self.log.info("Job %s is completed with status %s", job[0], job[1])
        else:
            self.log.info("Job %s with status %s", job[0], job[1])
        return True, job

    def is_gluster_services_online(self, ma_session):
        """To check gluster service is online
           Args:
                ma_session - Machine Object of MA
           Return : True/ False
         """
        self.log.info("checking gluster is online")
        count = 0
        while count <= 1:
            command = "service glusterd status | grep 'Active:' | awk '{print$2}'"
            self.log.info("command : %s", command)
            output = ma_session.execute_command(command)
            output = output.output.replace("\n", "")
            if output == 'inactive':
                if count == 1:
                    return False
                self.log.error('gluster service is inactive (dead)')
                self.log.info('Restarting gluster services')
                command = "service glusterd restart"
                self.log.info("command : %s", command)
                output = ma_session.execute_command(command)
                count += 1
            elif output == 'active':
                return True

    def gluster_volume_status(self, ma_session):
        """returns the gluster volume status
           Args:
                ma_session - Machine Object of MA
           Return : True/ False
         """
        count = 0
        self.log.info("checking gluster volume status")
        while count <= 1:
            command = "gluster v info | grep 'Status' | awk '{print$2}'"
            self.log.info("command : %s", command)
            output = ma_session.execute_command(command)
            output = output.output.replace("\n", "")
            if output == 'Stopped':
                if count == 1:
                    return False
                self.log.error('gluster volume status is ofline')
                self.log.info('starting the volume ')
                command = "gluster v info | grep -i 'Volume Name' | awk '{print$3}'"
                self.log.info("command : %s", command)
                output = ma_session.execute_command(command)
                storage_pool_name = output.output.replace("\n", "")
                command = f"gluster v start {storage_pool_name}"
                self.log.info("command : %s", command)
                output = ma_session.execute_command(command)
                count += 1
            elif output == 'Started':
                return True
            else:
                return False

    def check_peer_status(self, ma_session):
        """ checks whether peers are connected or not -
            Args:
                ma_session - Machine Object of MA
            Return : True/ False
        """
        self.log.info("checking Peer Status of Nodes")
        command = "gluster peer status | grep 'Number of Peers' | awk '{print$4}'"
        self.log.info("command : %s", command)
        output = ma_session.execute_command(command)
        num_of_peers = int(output.output.replace("\n", ""))
        command1 = " gluster peer status | grep -i 'hostname' | awk '{print $2}'"
        command2 = " gluster peer status | grep -i 'State' | awk '{print $5}'"
        self.log.info("%s", command1)
        self.log.info("%s", command2)
        output = ma_session.execute_command(command1)
        peer_nodes = output.output.split('\n')[:-1]
        output = ma_session.execute_command(command2)
        state = output.output.split('\n')[:-1]
        peer_status = {peer_nodes[i]: state[i] for i in range(num_of_peers)}
        for peer in peer_status:
            if peer[1] == 'Disconnected':
                self.log.error("Peer  : %s ", peer)
                return False
        return True

    def get_gluster_peer_status(self, ma_name):
        """Returns gluster peer status for a MA.

            Args:
                ma_name     (str)  --  MA name

            Returns:
                [(host, status), ...] - list of peer connection status
                    host is the host name
                    status is either True/False (Connected/Disconnected)
        """
        ma_machine = Machine(ma_name, self.commcell)
        output = ma_machine.execute_command('gluster peer status')
        output = output.output
        hosts = re.findall(r'Hostname: (.*)', output)
        status = re.findall(r'State:.* \((.*)\)', output)
        status = [True if s == 'Connected' else False for s in status]
        return (list(zip(hosts, status)))

    def restart_services(self, client_name):
        """Restarts Commvault services for a client

        Args:
            client_name (str) --  The client whose services are to be restarted

        Returns:
            None

        Note:
            this takes approx 1.5 minutes

        """
        if not self.commcell.clients.has_client(client_name):
            message = f"Can't restart services on non-existent client: {client_name}"
            raise Exception(message)
        client_obj = self.commcell.clients.get(client_name)
        client_obj.restart_services()

    def verify_restored_data(self, machine, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                machine          (object)    --  Machine class object.

                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s",
                      src_path, dest_path)
        diff_output = machine.compare_folders(machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def run_until_success(self, machine, command, tries=None, interval=None, success_predicate=None):
        """Runs a command until it succeeds or tries are exhausted.

            Args:

                machine     (Machine)   --  The machine object on which command will run

                command     (str)       --  The command to run

                tries       (int)       --  The max number of iterations to run the command
                                            Default: 100

                interval    (int)       --  The number of seconds to wait between iterations
                                            Default: 5

                success_predicate   (func)  --  A predicate function which takes the output and
                                                returns true for success

            Returns:

                command (str)   - The output of the command, if successful

                None            - Otherwise

        """
        if tries is None:
            tries = 100
        if interval is None:
            interval = 5
        if success_predicate is None:
            success_predicate = lambda x : bool(x)
        self.log.info(
            f"Running untill success |{command}| for {tries} tries, spaced every {interval}s")
        for _ in range(tries):
            try:
                output = machine.execute_command(command)
            except ChannelException as e:
                self.log.warning("Got a channel exception. Sleeping")
                time.sleep(interval)
                continue
            output = output.output
            if not success_predicate(output):
                time.sleep(interval)
                continue
            return output

    def run_until_either_success(self, machine, command_list, tries=None, interval=None):
        """Runs a list of commands until any succeeds or tries are exhausted.

            Args:

                machine     (Machine)   --  The machine object on which command will run

                command     (str)       --  The command to run

                tries       (int)       --  The max number of iterations to run the command
                                            Default: 100

                interval    (int)       --  The number of seconds to wait between iterations
                                            Default: 5

            Returns:

                command (str)   - The output of the command, if successful

                None            - Otherwise

        """
        if tries is None:
            tries = 100
        if interval is None:
            interval = 5
        self.log.info(
            f"Running untill success |{command_list}| for {tries} tries, spaced every {interval}s")
        for _ in range(tries):
            for command in command_list:
                try:
                    output = machine.execute_command(command)
                except ChannelException as e:
                    self.log.warning("Got a channel exception. Sleeping")
                    continue
                output = output.output
                if not output:
                    continue
                return command, output
            time.sleep(interval)

    def search_log_line(self, machine, log_file_path, text, from_line=None, last=None, tries=None, interval=None,
                        fixed_string=None, retry_duration=None):
        """Finds text in a log file with offset and retry attempts

            Args:

                machine         (Machine)   --  The machine object on where the log file resides

                log_file_path   (str)       --  The path to the log file that we are searching

                text            (str)       --  The text to search for

                from_line       (int)       --  The line from which to search
                                                Default 1

                last            (bool)      --  Search for last match
                                                Default False

                tries           (int)       --  The max number of iterations to run the command. None for default

                interval        (int)       --  The number of seconds to wait between iterations. None for default

                fixed_string    (bool)      --  Use fixed string (-F) for grep search
                                                Default True
                                                
                retry_duration  (int)       --  Time in sec during which to search for log line
                                                auto calculates tries

            Returns:

                (no, line)
                    no          (int)       -- The line number on which the match was found

                    line        (str)       -- The complete line(s) that matched

        """
        if retry_duration is not None:
            tries = int(ceil(retry_duration / interval))            
        
        if from_line is None:
            from_line = 1

        if last is None:
            last = False

        if fixed_string is None:
            fixed_string = True

        get_text_from_line = f"tail -n +{from_line} '{log_file_path}'"

        _F = 'F' if fixed_string else ''
        get_line_no = f"grep -n{_F} -- '{text}'"
        command = f"{get_text_from_line} | {get_line_no}"
        if last:
            command += f" | tail -1"
        time_start = time.time()
        output = self.run_until_success(
            machine, command, tries=tries, interval=interval)
        duration = int(round(time.time() - time_start))
        if not output:
            self.log.error(
                f"Couldn't find {text} from line {from_line} even after {duration}s")
            return False, None
        no, line = output.split(':', 1)
        no = int(no) + from_line - 1
        line = line.strip()
        self.log.info(f"Found |{text}| at {no} after {duration}s")
        self.log.info(line.split('\n')[0])
        return no, line

    def search_either_log_line(self, machine, log_file_path, text_list, from_line=None, last=None, tries=None, interval=None,
                        fixed_string=None):
        """Finds text in a log file with offset and retry attempts

            Args:

                machine         (Machine)   --  The machine object on where the log file resides

                log_file_path   (str)       --  The path to the log file that we are searching

                text            (str)       --  The text to search for

                from_line       (int)       --  The line from which to search
                                                Default 1

                last            (bool)      --  Search for last match
                                                Default False

                tries           (int)       --  The max number of iterations to run the command. None for default

                interval        (int)       --  The number of seconds to wait between iterations. None for default

                fixed_string    (bool)      --  Use fixed string (-F) for grep search
                                                Default True

            Returns:

                (text, no, line)
                    text        (str)       -- The original text that was matched

                    no          (int)       -- The line number on which the match was found

                    line        (str)       -- The complete line(s) that matched

        """
        if from_line is None:
            from_line = 1

        if last is None:
            last = False

        if fixed_string is None:
            fixed_string = True

        get_text_from_line = f"tail -n +{from_line} '{log_file_path}'"

        _F = 'F' if fixed_string else ''
        time_start = time.time()
        commands = {}
        for text in text_list:
            get_line_no = f"grep -n{_F} -- '{text}'"
            command = f"{get_text_from_line} | {get_line_no}"
            if last:
                command += f" | tail -1"
            commands[command] = text
        output = self.run_until_either_success(
            machine, commands.keys(), tries=tries, interval=interval)
        duration = int(round(time.time() - time_start))
        if not output:
            self.log.error(
                f"Couldn't find {text_list} from line {from_line} even after {duration}s")
            return None, False, None
        command, output = output
        no, line = output.split(':', 1)
        no = int(no) + from_line - 1
        line = line.strip()
        text = commands[command]
        self.log.info(f"Found |{text}| at {no} after {duration}s")
        self.log.info(line.split('\n')[0])
        return text, no, line
    
    def get_active_files_store(self, storage_policy_name):
        """returns active store object for files iDA
            Args : storagepolicy name
            Returns : file_store
        """
        copy_name = 'primary'
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(
            storage_policy_name, copy_name)
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def check_identical_operation_output(self, ma_list, ma_operations):
        """Runs same operation across multiple MAs for equality.

            Args:

                ma_list         (list)  --  list of MA names

                ma_operations   (list)  --  list of operations

            Returns:

                (bool, result) - bool indicates if outputs are equal
                    result is {ma_name: command_output}, where
                    ma_name belongs to ma_list and
                    command_output is output of command for ma_name

        """
        outputs = set()
        result = {}
        identical = True
        for ma, operation in zip(ma_list, ma_operations):
            output = operation()
            self.log.info(f"{ma} -> {output}")
            outputs.add(output)
            result[ma] = output
        if len(outputs) > 1:
            identical = False
        if identical:
            self.log.info(f"Outputs match amongst the nodes")
        else:
            self.log.warning(f"Outputs do not match amongst the nodes")
        return identical, result

    def check_identical_output(self, ma_list, ma_machines, command):
        """Runs same command across multiple MAs for equality.

            Args:

                ma_list     (list)  --  list of MA names

                ma_machines (dict)  --  dictionary, MA name -> machine object

                command     (str)   --  the command to run

            Returns:

                (bool, result) - bool indicates if outputs are equal
                    result is {ma_name: command_output}, where
                    ma_name belongs to ma_list and
                    command_output is output of command for ma_name

        """
        operations = []
        for ma in ma_list:
            def lambda_generator(ma):
                def execute():
                    ma_machine = ma_machines[ma]
                    output = ma_machine.execute_command(command)
                    output = output.output.strip()
                    return output

                return execute

            operations.append(lambda_generator(ma))
        self.log.info(f"Checking for identical output for command: {command}")
        identical, result = self.check_identical_operation_output(
            ma_list, operations)
        return identical, result

    def is_remote_cache_present(self, client_name):
        """
            Returns whether remote cache is present or not

            Args:

                client_name (str) -- The name of the remote cache node

            Returns:

                result      (bool) -- Whether present or not

            Raises:

                SDKException:

                - Failed to execute the api

                - Response is incorrect/empty

        """
        rc_helper = self.commcell.get_remote_cache(client_name)
        path = rc_helper.get_remote_cache_path()
        self.log.info(f"Found remote cache at {path} for {client_name}")
        return bool(path)

    def populate_remote_cache(self, cache_node):
        """Populates the remote cache with Unix RPMs

            Args:

                cache_node  (str) -- The name of the remote cache node

            Returns:

                True, None        -- If job succeeded

                False, message    -- If job failed with failure message

        """
        job_obj = self.commcell.download_software(
            options=DownloadOptions.LATEST_HOTFIXES.value,
            os_list=[DownloadPackages.UNIX_LINUX64.value],
            sync_cache=True, sync_cache_list=[cache_node])
        self.log.info(f"Started the download software job [{job_obj.job_id}]")
        if not job_obj.wait_for_completion():
            self.log.info("Download software job failed")
            return False, job_obj.status
        return True, None

    def populate_remote_cache_v4(self, cache_node):
        """Populates the remote cache with Unix RPMs

            Args:

                cache_node  (str) -- The name of the remote cache node

            Returns:

                True, None        -- If job succeeded

                False, message    -- If job failed with failure message

        """
        request_json = {
            "downloadConfiguration": {
                "upgradeToLatestRelease": False,
                "latestFixesForCurrentRelease": True,
                "windowsDownloadOptions": None,
                "unixDownloadOptions": [
                    "LINUX_X86_64"
                ]
            },
            "notifyWhenJobCompletes": True,
            "entities": [
                {
                "type": "CLIENT_ENTITY",
                "name": cache_node,
                }
            ]
        }
        _cvpysdk_object = self.commcell._cvpysdk_object
        url = self.commcell._services.get('DOWNLOAD_SOFTWARE', 
                                          self.commcell._services['CREATE_RC'].replace("SoftwareCache", "DownloadSoftware"))
        flag, response = _cvpysdk_object.make_request(
            'PUT', url, request_json
        )
        
        if not flag:
            reason = f"Error while calling the API"
            self.log.error(reason)
            return False, reason
        
        if not response.json():
            reason = f"Couldn't convert to json"
            self.log.error(reason)
            return False, reason
        
        if "jobId" not in response.json():
            reason = f"json doesn't contain a job id"
            self.log.error(reason)
            return False, reason
        
        job_obj = Job(self.commcell, response.json()['jobId'])
        
        self.log.info(f"Started the download software job [{job_obj.job_id}]")
        if not job_obj.wait_for_completion():
            self.log.info("Download software job failed")
            return False, job_obj.status
        return True, None


    def verify_log_lines(self, machine, log_file_path, log_line_list: List[LogLine], from_line):
        """Verifies the list of LogLine instances

            Args:

                machine         (obj)   -- The Machine on which logs are to be verified

                log_file_path   (str)   -- The path to the log file used for verification

                log_line_list   (list)  -- The list of LogLine instances

                from_line       (int)   -- The line after which to verify the logs

            Returns:

                no              (int)   -- The line number on which the last match was found
                                           False if verification failed
        """
        for log in log_line_list:
            from_line, _ = self.search_log_line(machine, log_file_path, log.text, from_line=from_line, tries=log.tries,
                                                interval=log.interval, fixed_string=log.fixed_string)
            if not from_line:
                self.log.error(f"Failed to verify log: {log}")
                return False
        self.log.info(f"All {len(log_line_list)} logs verified")
        return from_line

    def verify_logs(self, machine, log_file_path, logs, from_line):
        """Verifies the list of logs

            Args:

                machine         (obj)   -- The Machine on which logs are to be verified

                log_file_path   (str)   -- The path to the log file used for verification

                logs            (list)  -- The list of logs

                from_line       (int)   -- The line after which to verify the logs

            Returns:

                no              (int)   -- The line number on which the last match was found
                                           False if verification failed
        """
        log_line_list = [LogLine(log) for log in logs]
        return self.verify_log_lines(machine, log_file_path, log_line_list, from_line=from_line)

    def get_lines_in_log_file(self, machine, log_file_path):
        """Finds number of lines in a log file present on given MA

            Args:

                machine         (obj)       --  The MA where the log file resides

                log_file_path   (str)       --  The path to the log file

            Returns:

                no              (int)       --  The number of lines in the log file

        """
        self.log.info(
            f"Getting number of lines in {machine.machine_name}:{log_file_path}")
        command = f"cat {log_file_path} | wc -l"
        output = machine.execute_command(command)
        lines = int(output.output)
        self.log.info(f"Got {lines} lines")
        return lines

    def get_or_create_policy(self, storage_pool_name, ma_name, policy_name):
        """Gets or creates the storage policy from name

            Args:

                storage_pool_name   (str) -- Storage pool name

                ma_name             (str) -- The name of MA to be associated with this policy

                policy_name         (str) -- Storage policy name

            Returns:

                policy              (obj) -- New/updated storage policy
        """
        storage_pool_obj = self.get_storage_pool_details(storage_pool_name)
        storage_pool_details = storage_pool_obj.storage_pool_properties['storagePoolDetails']

        library_details = storage_pool_details['libraryList'][0]
        library_name = library_details['library']['libraryName']

        gdsp = storage_pool_obj.storage_pool_id
        gdsp_details = self.get_policy_details(gdsp)
        gdsp_name = gdsp_details[2]

        if not self.commcell.storage_policies.has_policy(policy_name):
            self.log.info("Policy not exists, Creating %s", policy_name)
            policy = self.commcell.storage_policies.add(
                policy_name, library_name, ma_name, global_policy_name=gdsp_name)
            self.log.info("Created Policy %s", policy_name)
        else:
            self.log.info("Policy exists")
            policy = self.commcell.storage_policies.get(policy_name)
        return policy

    def check_if_service_is_running(self, ma_list, ma_machines, service, active_states=['active'],
                                    substates=['running']):
        """Checks if a service is in desired state or not across MediaAgents

            Args:

                ma_list         (list) -- List of MA names

                ma_machines     (dict) -- Dictionary, MA name -> machine object

                service         (str)  -- The name of the service

                active_states   (list) -- Desired list of active states for the service

                substates       (list) -- Desired list of substates for the service

            Returns:

                result          (bool) -- Whether service is in desired state or not
        """
        command = f"systemctl show -p ActiveState -p SubState {service}"
        _, result = self.check_identical_output(ma_list, ma_machines, command)

        for ma in ma_list:
            self.log.info(f"Now parsing service status for {service} on {ma}")
            output = result[ma]
            lines = output.split('\n')
            if len(lines) != 2:
                self.log.error(f"Unexpected lines in {command} output")
                return False
            active_state = lines[0].split('=')[-1]
            if active_state.lower() not in active_states:
                self.log.error(f"{service}: active state: {active_state}")
                return False

            substate = lines[1].split('=')[-1]
            if substate.lower() not in substates:
                self.log.error(f"{service}: substate: {substate}")
                return False
            self.log.info(
                f"{service} is running on {ma}: {active_state}, {substate}")

        return True

    def wait_for_ping_result_to_be(self, result, hostname, interval=2, retry_attempts=40, retry_duration=None,
                                   silent=False):
        """Pings a host until the given result is obtained

            Args:

                result          (int)       --  The desired result
                                                0 - alive, 1 - dead

                hostname        (str)       --  The host to ping

                interval        (int)       --  Seconds to wait between pings

                retry_attempts  (int)       --  The number of retries

                retry_duration  (int)       --  The total retry duration in seconds (instead of retry_attempts)

                silent          (bool)      --  Silently ping

            Returns:

                result          (bool)      --  Whether the desired ping result was achieved or not

        """

        def func():
            try:
                response = ping(hostname)
            except Exception as e:
                if "Host not reachable. Please check the Host name again" in str(e):
                    self.log.warning(f"Exception while pinging {hostname}: {e}")
                    return False
                raise
            ret_code = response.ret_code
            if ret_code == result:
                return True

        success = self.wait_for(func, bool, interval=interval, retry_attempts=retry_attempts,
                                retry_duration=retry_duration, silent=silent)
        if not success:
            self.log.error(
                f"Couldn't get the desired ping result {result} for {hostname}")
            return False

        self.log.info(f"Got the desired ping result {result} for {hostname}")
        return True

    def wait_for_reboot(self, ma, ignore_shutdown_failure=True):
        """Waits for the media agent to reboot

            Args:

                ma                      (str)   --  The media agent

                ignore_shutdown_failure (bool)  -- Ignore if we fail to determine if node was shutdown

            Returns:

                result                  (bool)  --  Whether the reboot was successful or not

        """
        result = self.wait_for_ping_result_to_be(
            1, ma, retry_attempts=5 * 60, interval=1)
        if not result:
            message = f"Something went wrong while waiting for the node {ma} to go down"
            if ignore_shutdown_failure:
                self.log.warning(message)
                return True
            self.log.error(message)
            return False
        self.log.info(f"Node {ma} is down")
        result = self.wait_for_ping_result_to_be(0, ma, retry_duration=10*60)
        if not result:
            self.log.error(
                f"Something went wrong while waiting for the node {ma} to come back up")
            return False
        self.log.info(f"Node {ma} has come up")
        return True

    def upgrade_hedvig_get_upgrade_sequence(self, cache_machine, log_path, from_line, ma_list):
        """Parses the logs to figure out the node sequence used for upgrade

            Args:
                cache_machine   (obj)   -- The Machine object of cache_node

                log_path        (str)   -- The path of the log file to parse

                from_line       (int)   -- The line from which to search

                ma_list         (list)  -- The upgrade sequence will be a permutation of this list

            Returns:

                seq, num        (list, int)   -- The sequence and the line number that was last matched
                                                 False, in case of any errors

        """
        text = "Upgrade Summary"
        line_cache, _ = self.search_log_line(
            cache_machine, log_path, text, from_line)
        if not line_cache:
            return False
        self.log.info(f"|{text}| is present at {line_cache}")

        node_line_tuple = []
        for ma in ma_list:
            n, _ = self.search_log_line(
                cache_machine, log_path, ma, line_cache)
            if not n:
                return False
            node_line_tuple.append((n, ma))
        sorted_node_line_tuple = sorted(node_line_tuple)
        upgrade_seq = [t[1] for t in sorted_node_line_tuple]
        self.log.info(f"Node upgrade order: {upgrade_seq}")
        max_line_no = sorted_node_line_tuple[-1][0]
        return upgrade_seq, max_line_no

    def upgrade_hedvig_monitor_initial_logs(self, cache_node, cache_machine, log_path, from_line, upgrade_seq, hv_deploy_log_path = None):
        """Verifies the hedvig pre-upgrade logs

            Args:

                cache_node      (str)   -- The remote cache node

                cache_machine   (obj)   -- The Machine object of cache_node

                log_path        (str)   -- The path of the log file to parse

                from_line       (int)   --  The line number from which logs need to be checked

                upgrade_seq     (list)  --  The upgrade sequence of nodes

            Returns:

                num             (int)   --  The line number upto which logs were matched
                                            False, otherwise

        """
        other_nodes = upgrade_seq[:-1]

        if cache_node != upgrade_seq[-1]:
            raise Exception(
                "The last node to be upgraded is not the cache node. This shouldn't have happened.")

        logs_to_check = [
            "It appears CS VM is not deployed on mediaagent nodes ... skipping VM management",
            # "Upgrading CDS rpms ...",
            "Command [exportfs -ra] successful ...",
            "Created cvrepo successfully ... ",
            # f"Need hedvig upgrade on node {cache_node}",
            # *[f"Need to upgrade hedvig rpms on remote node ... {node}" for node in other_nodes],
            *[f"Stopping services on remote node: {node}" for node in other_nodes],
            f"Stopping services on local node: {cache_node}",
            "Stopped commvault services...",
            *[f"Pausing SELinux protection on node: {node}" for node in other_nodes],
        ]
        from_line = self.verify_logs(
        cache_machine, log_path, logs_to_check, from_line)
        if not from_line:
            self.log.error(f"Hedvig upgrade begin logs verification failed")
            return False
        logs_to_check = [
            "/opt/hedvig/bin/hv_deploy --upgrade_hs_disruptive"
        ]
        sp_version = int(self.commcell.version.split('.')[1])
        if sp_version <= 28:
            from_line = self.verify_logs(
            cache_machine, log_path, logs_to_check, from_line)
            if not from_line:
                self.log.error(f"Hedvig upgrade begin logs verification failed")
                return False
        elif sp_version >= 32:
            line_no = self.verify_logs(
            cache_machine, hv_deploy_log_path, logs_to_check, 1)
            if not line_no:
                self.log.error(f"Hedvig upgrade begin logs verification failed")
                return False
        return from_line

    def upgrade_hedvig_verify_action_recap(self, machine, log_path, line_hvcmd):
        """Verifies the action recap failure count is zero

            Args:

                machine     (obj)   -- The Machine object

                log_path    (str)   -- The path of the log file to parse

                line_hvcmd  (int)   -- The line number from which logs need to be checked

            Returns:

                num         (int)   -- The line number upto which logs were matched
                                       False, otherwise

        """
        text = "ACTION RECAP"
        line_hvcmd, _ = self.search_log_line(
            machine, log_path, text, line_hvcmd)
        if not line_hvcmd:
            self.log.error(f"Failed to find {text} for {machine.machine_name}")
            return False

        command = f"tail -n +{line_hvcmd} {log_path} | grep '{text}' -C 5 -m1 | awk '{{print $1, $NF}}' | grep failed"
        result = machine.execute_command(command)
        output = result.output
        self.log.info(f"{text} output from line {line_hvcmd}: {output}")
        # output will look like:
        # hostname1.domain.com: failed=1
        # hostname2.domain.com: failed=0
        # hostname3.domain.com: failed=0
        # localhost failed=0

        regex = r'([^: \n]+).*?failed=(\d+)'
        matches = re.findall(regex, output)
        self.log.info(f"{text} failure matches: {matches}")
        if not matches:
            self.log.error(f"Couldn't parse {text} failures")
            return False
        for hostname, fail_count in matches:
            fail_count = int(fail_count)
            if fail_count:
                self.log.error(f"{hostname} reported {fail_count} failure(s)")
                return False

        self.log.info(f"No {text} failures reported")
        return line_hvcmd

    def upgrade_hedvig_monitor_upgrade_logs(self, cache_machine, log_path, line_hvcmd):
        """Verifies the hedvig upgrade logs

            Args:

                cache_machine   (obj) -- The Machine object of cache_node

                log_path        (str) -- The path of the log file to parse

                line_hvcmd      (int) -- The line number from which logs need to be checked

            Returns:

                num             (int) -- Line number upto which logs were matched
                                         False, otherwise

        """

        # Check these logs from cv_hv_deploy_debug.log instead of hvcmd.log in FR32

        logs_to_check = [
            "RUNNING: upgrade_hs_disruptive",
            "RUNNING PLAY 1 [collect deploy server facts]",
            "RUNNING PLAY 2 [install preliminary dependencies]",
            "RUNNING PLAY 3 [transfer hedvig infrastructure]",
            "RUNNING PLAY 4 [run upgrade tasks for cluster nodes]",
            "COMPLETED PLAY 4",
        ]
        logs_to_check = [LogLine(log, interval=30) for log in logs_to_check]

        line_hvcmd = self.verify_log_lines(
            cache_machine, log_path, logs_to_check, line_hvcmd)
        if not line_hvcmd:
            self.log.error(f"Couldn't verify hedvig upgrade logs")
            return False

        line_hvcmd = self.upgrade_hedvig_verify_action_recap(
            cache_machine, log_path, line_hvcmd)
        if not line_hvcmd:
            self.log.error(
                f"Failed to verify action recap failure count for hedvig upgrade")
            return False
        return line_hvcmd

    def upgrade_hedvig_monitor_final_logs(self, cache_machine, log_path, from_line, upgrade_seq):
        """Verifies the hedvig upgrade end logs

            Args:

                cache_machine   (obj)   --  The Machine object of cache_node

                log_path        (str)   --  The path of the log file to parse

                from_line       (int)   --  The line number from which logs need to be checked

                upgrade_seq     (list)  --  The upgrade sequence of nodes

            Returns:

                num             (int)   --  Line number upto which logs were matched
                                            False, otherwise

        """
        other_nodes = upgrade_seq[:-1]
        cache_node = upgrade_seq[-1]

        logs_to_check = [
            *[f"Resuming SELinux protection on node: {node}" for node in other_nodes],
            f"Starting services on local node: {cache_node}",
            "Started commvault services...",
            *[f"Starting services on remote node: {node}" for node in other_nodes],
            # "Successfully upgraded CDS rpms ...",
            "Stopping nfs-server.service",
        ]
        from_line = self.verify_logs(
            cache_machine, log_path, logs_to_check, from_line)
        if not from_line:
            self.log.error(f"Hedvig upgrade end logs verification failed")
            return False

        return from_line

    def upgrade_os_monitor_prereq_logs(self, cache_machine, log_path, from_line, upgrade_seq):
        """Verifies the prerequisites logs (before pressing enter)

            Args:

                cache_machine   (obj)   --  The Machine object of cache_node

                log_path        (str)   --  The path of the log file to parse

                from_line       (int)   --  The line number from which logs need to be checked

                upgrade_seq     (list)  --  The upgrade sequence of nodes

            Returns:

                num             (int)   --  Line number upto which logs were matched
                                            False, otherwise

        """
        logs_to_check = [
            "It appears CS VM is not deployed on mediaagent nodes ... skipping VM management",
            "New packages are present in SW cache ... going ahead with upgrading HyperScale cluster nodes ...",
            "Performing some pre-upgrade checks ... please wait...",
            "Following nodes will be upgraded:",
            *[node for node in upgrade_seq]
        ]
        from_line = self.verify_logs(
            cache_machine, log_path, logs_to_check, from_line)
        if not from_line:
            self.log.error(f"Prereq logs verification failed")
            return False
        return from_line

    def upgrade_os_monitor_initial_logs(self, cache_machine, log_path, from_line, upgrade_seq):
        """Verifies the pre-upgrade logs

            Args:

                cache_machine   (obj)   --  The Machine object of cache_node

                log_path        (str)   --  The path of the log file to parse

                from_line       (int)   --  The line number from which logs need to be checked

                upgrade_seq     (list)  --  The upgrade sequence of nodes

            Returns:

                num             (int)   --  The line number upto which logs were matched
                                            False, otherwise

        """
        other_nodes = upgrade_seq[:-1]
        cache_node = upgrade_seq[-1]
        logs_to_check = [
            "Proceeding with upgrade ...",
            "Creating rpm repository ...",
            *[f"node: {node}" for node in other_nodes],
            "Started nfs-server.service ...",
            "Command [exportfs -ra] successful ...",
        ]
        from_line = self.verify_logs(
            cache_machine, log_path, logs_to_check, from_line)
        if not from_line:
            self.log.error(f"OS upgrade begin logs verification failed")
            return False
        return from_line

    def upgrade_os_should_proceed(self, cache_machine, log_path, from_line):
        """Checks if the upgrade proceeds or not. It can't proceed if either it is already
        up to date or if we didn't match any log lines after sufficient tries

            Args:

                cache_machine   (obj)   --  The Machine object of cache_node

                log_path        (str)   --  The path of the log file to parse

                from_line   (int)   --  The line number from which logs need to be checked

            Returns:

                (result, num)
                    result  (bool)  --  Should proceed or not

                    num     (int)   --  The line number on which the match was found.
                                        None, if no match was found

        """
        logs_to_check = [
            ("Created cvrepo successfully", True),
            (
                "Repository [/ws/ddb/upgos/cvrepo] is not present, it appears there are no packges available for upgrade. Nothing to be done.",
                False)
        ]

        interval = 5
        retry_attempts = 100
        self.log.info(
            f"Checking if upgrade should proceed with {retry_attempts} tries spaced every {interval} s")
        for _ in range(retry_attempts):
            for log, return_value in logs_to_check:
                result_line, _ = self.search_log_line(
                    cache_machine, log_path, log, from_line=from_line, tries=1)
                if result_line:
                    return return_value, result_line
            time.sleep(interval)
        self.log.error(
            f"Couldn't determine if upgrade should proceed after {retry_attempts} tries spaced every {interval} s")
        return False, None

    def upgrade_os_monitor_yum_logs(self, machine_ma, log_path):
        """Verifies the yum logs on the MA machine

            Args:

                machine_ma      (Machine)   --  The machine object of the MA

                log_path        (str)       --  The path of the log file to parse

            Returns:

                result          (bool)      --  Logs verified or not

        """
        logs = [
            "Resolving Dependencies",
            "Dependencies Resolved",
            "Running transaction",
            # "Complete!",
        ]
        for log in logs:
            line_no, _ = self.search_log_line(
                machine_ma, log_path, log, tries=int(20 * 60 / 5), interval=5)
            if not line_no:
                self.log.error(f"Couldn't find the line {log} in yum.out.log")
                return False
        return True

    def upgrade_os_monitor_node_logs(self, machine_ma, log_path_cvupgos, log_path_hvcmd, cumulative_hvcmd, log_path_yum,
                                     machine_cache, line_cache, hv_deploy_log_path = None):
        """Verifies the logs for the node being upgraded

            Args:

                machine_ma          (obj)   --  The MA whose logs are to be verified

                log_path_cvupgos    (str)   --  The path of the cvupgradeos log file to parse

                log_path_hvcmd      (str)   --  The path of the hvcmd log file to parse

                cumulative_hvcmd    (bool)  --  Whether hvcmd log needs to be parsed cumulatively

                log_path_yum        (str)   --  The path of the yum.out log file to parse
                                                Use None to skip verification

                machine_cache       (obj)   --  The Machine object of cache_node

                line_cache          (int)   --  The line number from where to start log verification

            Returns:

                no                  (int)   --  Line number of last matched log

        """
        ma = machine_ma.machine_name
        text = f"Starting to upgrade node... {ma}"
        line_cache, _ = self.search_log_line(
            machine_cache, log_path_cvupgos, text, tries=500, from_line=line_cache)
        if not line_cache:
            return False

        text = "Starting to upgrade the machine"
        line_ma, _ = self.search_log_line(
            machine_ma, log_path_cvupgos, text, tries=500, last=True)
        if not line_ma:
            self.log.error(f"OS Upgrade didn't start on {ma}")
            return False

        logs_to_check = [
            "Copied repo file [cvrepo] to /etc/yum.repos.d ...",
            "cmd [multipath -F] successful...",
            "cmd [systemctl stop multipathd.service] successful...",
            "cmd [systemctl disable multipathd.service] successful...",
            "Stopping cv services ...",
            "Creating service control hook",
            "Stopped commvault services...",
            "Stopping all distributed storage services.",
        ]
        line_ma = self.verify_logs(
            machine_ma, log_path_cvupgos, logs_to_check, line_ma)
        if not line_ma:
            self.log.error(f"Verifying logs for {ma} has failed")
            return False
        logs_to_check = [
            f"--stop_node {ma}",
        ]
        sp_version = int(self.commcell.version.split('.')[1])
        result = None
        if sp_version <= 28:
            line_ma = self.verify_logs(
                machine_ma, log_path_cvupgos, logs_to_check, line_ma)
            result = line_ma
            
        elif sp_version >= 32:
            result = self.verify_logs(machine_ma, hv_deploy_log_path, logs_to_check, 1)
        
        if not result:
            self.log.error(f"Verifying logs for {ma} has failed")
            return False

        text = "RUNNING: stop_node"
        line_hvcmd, _ = self.search_log_line(
            machine_ma, log_path_hvcmd, text, tries=500, last=True)
        if not line_hvcmd:
            self.log.error(
                f"{text} not found on {ma}. Log verification failed")
            return False
        line_hvcmd = self.upgrade_hedvig_verify_action_recap(
            machine_ma, log_path_hvcmd, line_hvcmd)
        if not line_hvcmd:
            self.log.error(f"{text} action verification failed on {ma}")
            return False
        self.log.info(f"{text} was successful on {ma}")

        logs_to_check = [
            "Stopping Fujitsu services ...",
            "Stop and disable NetworkManager service ...",
            "yum command [yum repolist] successful ...",
            "Installing rpms...this will take several minutes...Please wait",
        ]

        line_ma = self.verify_logs(
            machine_ma, log_path_cvupgos, logs_to_check, line_ma)
        if not line_ma:
            self.log.error(f"Verifying logs for {ma} has failed")
            return False

        self.log.info(f"Verified beginning logs for node: {ma}")

        if log_path_yum:
            result = self.upgrade_os_monitor_yum_logs(machine_ma, log_path_yum)
            if not result:
                self.log.error(f"Failed to verify yum logs for {ma}")
                return False
            self.log.info(f"Verified yum logs for {ma}")
        else:
            self.log.info(f"Skipping yum logs verification")

        text = "Successfully installed required RPMs"
        line_cache, _ = self.search_log_line(machine_cache, log_path_cvupgos, text, from_line=line_cache, tries=15 * 60,
                                             interval=1)
        if not line_cache:
            self.log.error(
                f"Couldn't find {text} in {machine_cache.machine_name}:cvupgradeos.log for {ma}")
            return False
        self.log.info(f"Now waiting for the node {ma} to come back up")

        logs_to_check = [
            "Remote host is up and running",
            "Running postupgrade tasks on remote node",
        ]
        line_cache = self.verify_logs(
            machine_cache, log_path_cvupgos, logs_to_check, line_cache)
        if not line_cache:
            self.log.error(
                f"Verifying initial post upgrade logs for {ma} on remote cache has failed")
            return False
        self.log.info(
            f"Successfully verified initial post upgrade logs for {ma} on remote cache")

        logs_to_check = [
            "Running postupgrade tasks",
        ]
        line_ma = self.verify_logs(
            machine_ma, log_path_cvupgos, logs_to_check, line_ma)
        if not line_ma:
            self.log.error(
                f"Verifying initial post upgrade logs for {ma} on the node has failed")
            return False
        logs_to_check = [    
            f"--start_node {ma}",
        ]
        result = None
        if sp_version <= 28:    
            line_ma = self.verify_logs(
                machine_ma, log_path_cvupgos, logs_to_check, line_ma)
            result = line_ma
        elif sp_version >= 32:
            result = self.verify_logs(
                machine_ma, hv_deploy_log_path, logs_to_check, 1)
        if not result:
            self.log.error(
                f"Verifying initial post upgrade logs for {ma} on the node has failed")
            return False
        
        self.log.info(
            f"Successfully verified initial post upgrade logs for {ma} on the node")

        text = "RUNNING: start_node"
        if not cumulative_hvcmd:
            line_hvcmd = 1
        line_hvcmd, _ = self.search_log_line(
            machine_ma, log_path_hvcmd, text, tries=500, from_line=line_hvcmd)
        if not line_hvcmd:
            self.log.error(
                f"{text} not found on {ma}. Log verification failed")
            return False
        line_hvcmd = self.upgrade_hedvig_verify_action_recap(
            machine_ma, log_path_hvcmd, line_hvcmd)
        if not line_hvcmd:
            self.log.error(f"{text} action verification failed on {ma}")
            return False
        self.log.info(f"{text} was successful on {ma}")

        logs_to_check = [
            LogLine(
                f"Upgrade completed successfully for node...{ma}", interval=1, tries=10*60)
        ]
        line_cache = self.verify_log_lines(
            machine_cache, log_path_cvupgos, logs_to_check, line_cache)
        if not line_cache:
            self.log.error(f"Final log verification failed for node {ma}")
            return False
        return line_cache

    def upgrade_os_monitor_remote_cache_logs(self, machine_cache, log_path_cvupgos, line_cache, log_path_hvcmd,
                                             cumulative_hvcmd, hv_deploy_log_path = None):
        """Verifies the logs for the remote cache node

            Args:

                machine_cache       (obj)   --  The Machine object of cache_node

                log_path_cvupgos    (str)   --  The path of the cvupgradeos log file to parse

                line_cache          (int)   --  The line after which the logs are to be verified

                log_path_hvcmd      (str)   --  The path of the hvcmd log file to parse

                cumulative_hvcmd    (bool)  --  Whether hvcmd log needs to be parsed cumulatively

            Returns:

                result              (bool)  --  If verified or not

        """
        cache_node = machine_cache.machine_name

        logs_to_check = [
            "Stopped commvault services",
        ]
        line_cache = self.verify_logs(
            machine_cache, log_path_cvupgos, logs_to_check, line_cache)
        if not line_cache:
            self.log.error(
                f"Verifying begin upgrade logs for {cache_node} has failed")
            return False
        logs_to_check = [ 
            f"--stop_node {cache_node}"
        ]
        sp_version = int(self.commcell.version.split('.')[1])
        result = None
        if sp_version <= 28:
            line_cache = self.verify_logs(
                machine_cache, log_path_cvupgos, logs_to_check, line_cache)
            result = line_cache
            
        elif sp_version >= 32:
            result = self.verify_logs(machine_cache, hv_deploy_log_path, logs_to_check, 1)

        if not result:
                self.log.error(
                    f"Verifying begin upgrade logs for {cache_node} has failed")
                return False
        

        text = "RUNNING: stop_node"
        line_hvcmd, _ = self.search_log_line(
            machine_cache, log_path_hvcmd, text, last=True)
        if not line_hvcmd:
            self.log.error(
                f"{text} not found on {cache_node}. Log verification failed")
            return False
        line_hvcmd = self.upgrade_hedvig_verify_action_recap(
            machine_cache, log_path_hvcmd, line_hvcmd)
        if not line_hvcmd:
            self.log.error(
                f"{text} action verification failed on {cache_node}")
            return False
        self.log.info(f"{text} was successful on {cache_node}")

        logs_to_check = [
            LogLine(f"Starting to upgrade node... {cache_node}"),
            LogLine("Running command [yum repolist]"),
            LogLine("yum command [yum repolist] successful"),
            LogLine("Running command [yum -y update]"),
            LogLine("yum command [yum -y update] successful",
                    tries=15 * 60, interval=2),
            LogLine(
                f"Upgrade completed successfully for node...{cache_node}", interval=1)
        ]
        line_cache = self.verify_log_lines(
            machine_cache, log_path_cvupgos, logs_to_check, from_line=line_cache)
        if not line_cache:
            self.log.error(
                f"Failed to verify logs for remote cache before reboot")
            return False
        self.log.info(f"Pre-reboot logs verified for {cache_node}")

        if not cumulative_hvcmd:
            self.log.info(f"Now waiting for {cache_node} to complete reboot")
            result = self.wait_for_reboot(cache_node)
            if not result:
                self.log.error("Failed to reboot")
                return False
            self.log.info(f"{cache_node} has rebooted successfully")
        else:
            self.log.info(f"Skipping waiting for {cache_node} to reboot")

        # wait for SSH services to come up
        time.sleep(10)

        logs_to_check = [
            "Resuming upgrade after reboot",
            "Successfully completed hv_deploy --startup_cluster_check",
        ]
        line_cache = self.verify_logs(
            machine_cache, log_path_cvupgos, logs_to_check, line_cache)
        if not line_cache:
            self.log.error(
                f"Verifying --start_node upgrade logs for {cache_node} has failed")
            return False
        logs_to_check  = [
            f"--start_node {cache_node}",
        ]
        if sp_version <= 28:
            line_cache = self.verify_logs(
                machine_cache, log_path_cvupgos, logs_to_check, line_cache)
        elif sp_version >= 32:
            line_cache = self.verify_logs(
                machine_cache, hv_deploy_log_path, logs_to_check, 1)
        if not line_cache:
            self.log.error(
                f"Verifying upgrade logs for {cache_node} has failed")
            return False

        text = "RUNNING: start_node"
        if not cumulative_hvcmd:
            line_hvcmd = 1
        line_hvcmd, _ = self.search_log_line(
            machine_cache, log_path_hvcmd, text, from_line=line_hvcmd)
        if not line_hvcmd:
            self.log.error(
                f"{text} not found on {cache_node}. Log verification failed")
            return False
        line_hvcmd = self.upgrade_hedvig_verify_action_recap(
            machine_cache, log_path_hvcmd, line_hvcmd)
        if not line_hvcmd:
            self.log.error(
                f"{text} action verification failed on {cache_node}")
            return False
        self.log.info(f"{text} was successful on {cache_node}")

        text = "Upgrade completed successfully on all nodes"
        line_cache, _ = self.search_log_line(
            machine_cache, log_path_cvupgos, text, from_line=line_cache)
        if not line_cache:
            self.log.error(
                f"Couldn't find the line {text} in {cache_node}:cvupgradeos.log for {cache_node}")
            return False
        self.log.info("Upgrade successful")
        return True

    def get_hedvig_cluster_name(self, machine):
        """Gets the hedvig cluster name

            Args:

                machine (obj)   --  The Machine object

            Returns:

                name    (str)   --  The cluster name
                                    False, otherwise

        """
        if self.is_hsx_node_version_equal_or_above(machine, 3):
            fire_command_as = "root"
        else:
            fire_command_as = "admin"
        command = f'su -l -c "/opt/hedvig/bin/hv_deploy --show_all_clusters" {fire_command_as}'
        output = machine.execute_command(command)
        output = output.output
        match_obj = re.findall("(HV[0-9]+)", output)
        if not match_obj:
            self.log.error(
                "Unable to match the regex to parse the cluster name")
            return False
        cluster_name = match_obj[0]
        self.log.info(f"hedvig cluster name: {cluster_name}")
        return cluster_name

    def verify_hedvig_services_are_up(self, ma_names, ma_machines, services=None):
        """Verifies if hedvig services are up

            Args:

                ma_names    (list)  --  The MA names

                ma_machines (dict)  --  Dictionary, MA name -> machine object

                services    (list)  --  The list of hedvig services to check
                                        Use None to check all services

            Returns:

                result (bool)   -- Whether verified or not

        """
        added_nodes = [ma_name for ma_name in ma_names if self.is_added_node(ma_machines[ma_name])]
        other_nodes = [ma_name for ma_name in ma_names if ma_name not in added_nodes]
        added_node_services = ['hedvigfsc', 'hedvighblock']
        other_node_services = added_node_services + ['hedvighpod', 'hedvigpages']

        
        def verify_service_status(services, ma_names, ma_machines):
            for service in services:
                result = self.check_if_service_is_running(
                    ma_names, ma_machines, service)
                if not result:
                    return False
            return True

        if services:
            other_node_services = services
            skipped_services = [service for service in services if service not in added_node_services]
            added_node_services = [service for service in services if service in added_node_services]
        self.log.info(f"Checking for status of {other_node_services} on existing nodes in the cluster")
        result = verify_service_status(other_node_services, other_nodes, ma_machines)
        if not result:
            return False
        if added_nodes:
            if services and skipped_services:
                self.log.info(f"Skipping {skipped_services} since it is not expected to be present on added nodes")
            self.log.info(f"Checking for status of {added_node_services} on added nodes")
            result = verify_service_status(added_node_services, added_nodes, ma_machines)
        return result


    def verify_nfsstat_output(self, ma_names, ma_machines):
        """Verifies nfsstat output

            Args:

                ma_names    (list)  --  The MA names

                ma_machines (dict)  --  Dictionary, MA name -> machine object

            Returns:

                result (bool)   -- Whether verified or not

        """
        vdisk_name = self.verify_vdisk_registry(ma_names, ma_machines)
        if not vdisk_name:
            self.log.error("Error retrieving vdisk name")
            return False
        command = f"nfsstat -m | grep '{vdisk_name} ' -A 1 | head -n 2"
        identical, result = self.check_identical_output(
            ma_names, ma_machines, command)
        if not identical:
            return False
        lines = result[ma_names[0]].split('\n')
        if len(lines) != 2:
            self.log.error(f"Unexpected lines in {command} output")
            return False
        info_line = lines[0]
        mount_path, _, exports_path = info_line.split(" ")
        self.log.info(f"mount path: {mount_path} exports_path: {exports_path}")
        flag_line = lines[1]
        flags_string = flag_line.replace('Flags:\t', '').strip()
        flags = flags_string.split(',')
        if len(flags) <= 1:
            self.log.error(f"Unexpected flags in {command} output")
            return False
        self.log.info(f"Found {len(flags)} flags")
        return True

    def verify_df_kht_nfs4_output(self, ma_names, ma_machines):
        """Verifes df -kht nfs4 output

            Args:

                ma_names    (list)  --  The MA names

                ma_machines (dict)  --  Dictionary, MA name -> machine object

            Returns:

                result (bool)   -- Whether verified or not

        """
        command = "df -kht nfs4 | grep -v -- '-r' | grep -i CVLTBackup"
        identical, result = self.check_identical_output(
            ma_names, ma_machines, command)
        if not identical:
            self.log.error(f"Output not identical across MAs")
            return False
        output = result[ma_names[0]]

        # remove extra spaces
        info = ' '.join(output.split())
        values = info.split()
        if len(values) != 6:
            self.log.error(f"Unexpected no. of values in {command} output")
            return False
        exports_path = values[0]
        mount_path = values[-1]
        self.log.info(f"mount path: {mount_path} exports_path: {exports_path}")
        return True

    def get_killed_commvault_processes(self, machine):
        """Retrieves the list of killed commvault processes for a media agent

            Args:

                machine (obj)   --  The machine object of the media agent

            Returns:

                result  (list)  --  The list of killed commvault processes

        """
        command = r'commvault list | grep "N/A" | sed "s/|//g"'
        output = machine.execute_command(command)
        output = output.output.strip()
        if not output:
            return []
        lines = output.split('\n')
        lines = [line.strip() for line in lines]
        names = [line.split(' ')[0] for line in lines]
        return names

    def verify_commvault_service_and_processes_are_up(self, ma_names, ma_machines):
        """Verifies if commvault service is up as well as the commvault processes

            Args:

                ma_names    (list)  --  The MA names

                ma_machines (dict)  --  Dictionary, MA name -> machine object

            Returns:

                result      (bool)  --  Whether verified or not

        """
        result = self.check_if_service_is_running(
            ma_names, ma_machines, 'commvault')
        if not result:
            return False
        for ma_name in ma_names:
            processes = self.get_killed_commvault_processes(
                ma_machines[ma_name])
            if processes:
                self.log.error(f"{processes} killed for {ma_name}")
                return False
            self.log.info(f"All commvault processes running for {ma_name}")
        return True

    def stop_commvault_services(self, ma_names, ma_machines):
        """Stops the commvault services on the MAs

            Args:

                ma_names    (list)  --  The MA names

                ma_machines (dict)  --  Dictionary, MA name -> machine object

            Returns:

                result      (bool)  --  Whether stopped or not
        """
        identical, result = self.check_identical_output(
            ma_names, ma_machines, 'commvault stop')

        def operation():
            result = self.check_if_service_is_running(
                ma_names, ma_machines, 'commvault', ['inactive'], ['dead'])
            return result

        result = self.wait_for(operation, bool, interval=5, retry_duration=60)
        if result:
            self.log.info("Successfully stopped commvault services")
        else:
            self.log.error("Couldn't stop commvault services")
        return result

    def determine_remote_caches(self, ma_names):
        """From a list of MAs, returns remote cache nodes

            Args:

                ma_names    (list)  --  The MA names

            Returns:

                result      (list)  --  List of remote caches
        """
        remote_caches = []
        for ma in ma_names:
            if self.is_remote_cache_present(ma):
                remote_caches.append(ma)
        return remote_caches

    def get_reg_key_values(self, ma_names, ma_machines, reg_keys, reg_type='MediaAgent', to_be_sorted=[]):
        """Gets the values for multiple reg keys for multiple MAs, also checks for equality

            Args:

                ma_names        (list)          --  The MA names

                ma_machines     (dict)          --  Dictionary, MA name -> machine object

                reg_keys        (list)          --  The registry keys like nHyperScaleLastUpgradeTime

                reg_type        (str)           --  The type of registry like MediaAgent, Session, etc.

                to_be_sorted    (list)          --  List with the reg keys that needs to be sorted (comma-seperated)

            Returns:

                output  (dict, [bool])  --  dict:   { Reg key -> value list } for all MAs mapping
                                                    value is None, if reg key doesn't exist
                                            [bool]:   Whether for each reg key, the values match or not

        """
        result = {}
        identical = []
        for reg_key in reg_keys:
            values = []
            values_set = set()
            for ma in ma_names:
                machine: Machine = ma_machines[ma]
                if not machine.check_registry_exists(reg_type, reg_key):
                    value = None
                else:
                    value = machine.get_registry_value(reg_type, reg_key)
                    if reg_key in to_be_sorted:
                        value = ','.join(sorted(value.split(',')))
                values.append(value)
                values_set.add(value)
            result[reg_key] = values
            self.log.info(f"{reg_key} -> {values}")
            if len(values_set) > 1:
                self.log.info(f"{reg_key} has different values")
                identical.append(False)
            else:
                self.log.info(f"{reg_key} has same values")
                identical.append(True)
        return result, identical

    def wait_for(self, func, func_validator, interval=2, retry_attempts=40, retry_duration=None, silent=False):
        """Runs func till func_validator(func()) returns true with retry attempts

            Args:

                func            (func)      --  The function to wait for

                func_validator  (func)      --  Determines if func() should be called again or not.
                                                Accepts the output of func() as argument

                interval        (int)       --  Seconds to wait between calls to func()

                retry_attempts  (int)       --  The number of retries

                retry_duration  (int)       --  The total retry duration in seconds (instead of retry_attempts)

                silent          (bool)      --  If true, skips logging unsuccessful tries - minimal logging

            Returns:

                result          (bool)      --  Whether the desired result was achieved or not within the time

        """
        iter = 1
        start_time = time.time()
        if retry_duration:
            retry_attempts = None
            end_time = start_time + retry_duration

        while (retry_attempts and iter <= retry_attempts) or (retry_duration and time.time() <= end_time):
            response = func()

            if not silent:
                self.log.info(
                    f"iter: {iter}, duration: {round(time.time() - start_time)}, response received {response}")
            if func_validator(response):
                self.log.info(
                    f"Got the desired response {response} after {iter} tries and {round(time.time() - start_time)}s")
                return True
            iter += 1
            time.sleep(interval)
        duration = round(time.time() - start_time)
        self.log.error(
            f"Couldn't get the desired response even after {iter} tries and {duration}s")
        return False

    def wait_for_reg_key_to_be(self, machine: Machine, reg_value, reg_key, reg_type='MediaAgent',
                               retry_duration=15 * 60):
        """Waits until a particular reg key exists and equal to reg_value

            Args:

                machine         (dict)  --  Machine object where reg key will be probed

                reg_value       (list)  --  The desired value for the reg_key

                reg_key         (list)  --  The registry key like nHyperScaleLastUpgradeTime

                reg_type        (str)   --  The type of registry like MediaAgent, Session, etc.

                retry_duration  (int)   --  The total retry duration in seconds

            Returns:

                result          (bool)  --  Whether the reg key reflected the desired value or not

        """
        self.log.info(
            f"wait_for_reg_key_to_be on {machine.machine_name} {reg_type}:{reg_key} = {reg_value} for {retry_duration}s")

        def func():
            try:
                if machine.check_registry_exists(reg_type, reg_key) and machine.get_registry_value(reg_type,
                                                                                                   reg_key) == reg_value:
                    return True
            except ChannelException as e:
                self.log.warning("Ignoring Channel Exception")
            except NoValidConnectionsError as e:
                self.log.warning("Ignoring NoValidConnectionsError")
                self.log.error(e)
            return False

        return self.wait_for(func, bool, retry_duration=retry_duration, silent=True)

    def verify_vdisk_registry(self, ma_names, ma_machines):
        """Verifies if sVDiskList is present and same across MediaAgents

            Args:

                ma_names        (list)  --  The MA names

                ma_machines     (dict)  --  Dictionary, MA name -> machine object

            Returns:

                reg_value       (str)   --  The value for the sVDiskList reg key
                                            None in case of error
        """
        reg_name = "sVDiskList"
        reg_values, identical_values = self.get_reg_key_values(
            ma_names, ma_machines, [reg_name])
        values = reg_values[reg_name]

        if not identical_values[0]:
            self.log.error(f"{reg_name} has different values across MAs")
            return

        if not values[0]:
            self.log.error(f"{reg_name} doesn't exist across MAs or is empty")
            return

        self.log.info(f"{reg_name} verified across MAs")
        return values[0]

    def get_storage_pool_from_media_agent(self, ma_name):
        """Gets the name of the storage pool from MA name

            Args:

                ma_name (str)   -- Name of the Media Agent

            Returns:

                result  (str)   --  The name of the storage pool
                                    None if doesn't exist or error
        """
        hostid = self.get_host_id(ma_name)
        query = f'''
        SELECT
        DISTINCT
            (ag.id),
            ag.name
        FROM archGroup ag WITH (NOLOCK)
        INNER JOIN archGroupCopy agc WITH (NOLOCK)
            ON ag.id = agc.archGroupId
        WHERE agc.id IN (SELECT
            CopyId
        FROM MMDataPath WITH (NOLOCK)
        WHERE HostClientId = {hostid})
        AND SIGN((ag.flags & 256) | (ag.flags & 8388608)) = 1
        '''
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info(f"{ma_name} -> {rows}")
        if not rows or rows == [['']]:
            return
        if len(rows) > 1:
            self.log.error(f"Multiple storage pools for {ma_name}")
            return
        return rows[0][1]

    def get_storage_pool_from_media_agents(self, ma_list):
        """Gets the name of the storage pool spanning the MAs

            Args:

                ma_list (list)  -- Name of the Media Agents

            Returns:

                result  (str)   --  The name of the storage pool
                                    None if doesn't exist
        """
        operations = []
        for ma in ma_list:
            def lambda_creator(ma):
                return lambda: self.get_storage_pool_from_media_agent(ma)

            operations.append(lambda_creator(ma))
        identical, result = self.check_identical_operation_output(
            ma_list, operations)
        if not identical:
            self.log.error(
                "Inconsistent values for storage pools across nodes")
            return
        storage_pool_name = result[ma_list[0]]
        if not storage_pool_name:
            self.log.info(f"No storage pool exists for these nodes: {ma_list}")
            return
        self.log.info(
            f"Found {storage_pool_name} as the storage pool for nodes: {ma_list}")
        return storage_pool_name

    def trigger_node_refresh(self, storage_pool_name, media_agent):
        """Trigger node refresh action on the node

        Args:

            media_agent      (str|obj)  --  name of media agents(str)
                                            or instance of media agent's(object)

            Example: "ma"

        Raises Exception:

                    if refresh node action fails
        """
        fr_version = int(self.commcell.version.split('.')[0])
        if fr_version >= 32:
            raise Exception("This is a noop starting FR 32")

        mediagent_obj = None
        if isinstance(media_agent, MediaAgents):
            mediagent_obj = media_agent
        elif isinstance(media_agent, str):
            mediagent_obj = self.commcell.media_agents.get(media_agent)
        else:
            raise Exception('Invalid arguments')

        request_json = {
            "scaleoutOperationType": 3,
            "StoragePolicy": {
                "storagePolicyName": "{0}".format(storage_pool_name),
            },
            "storage": [
                {
                    "mediaAgent": {
                        "displayName": "{0}".format(mediagent_obj.media_agent_id),
                        "mediaAgentName": "{0}".format(mediagent_obj.media_agent_name)
                    }
                }
            ],
        }

        response = self.commcell.request(
            "POST", 'StoragePool?Action=edit', request_json)

        if response.json():
            error_code = response.json()['errorCode']

            if int(error_code) != 0:
                error_message = response.json()['errorMessage']
                o_str = 'Failed to trigger node refresh\nError: "{0}"'

                raise Exception(o_str.format(error_message))
        else:
            raise Exception("Failed to trigger node refresh")

    def validate_ddb_expansion(self, storage_pool_name, ma_name):
        """Validates DDB expansion

            Args:

                storage_pool_name (str) -- Name of the storage pool

                ma_name (str)           -- Name of the Media Agent

            Returns:

                result  (bool)           --  Whether valid or not
        """
        query = f"""
            SELECT COUNT(*)
            FROM MMSDSStoragePool msds, IdxSIDBStore idxstore, IdxSIDBSubStore idxsubstore, APP_Client ap
            WHERE msds.StoragePoolName = '{storage_pool_name}'
            AND idxstore.SIDBStoreName LIKE CONCAT(msds.StoragePoolName, '_%')
            AND idxstore.SIDBStoreId = idxsubstore.SIDBStoreId
            AND idxsubstore.ClientId = ap.id 
            AND ap.net_hostname = '{ma_name}'
            AND idxsubstore.Status = 0;
        """
        self.csdb.execute(query)
        rows = self.csdb.fetch_one_row()
        if not rows:
            return False
        return True

    def get_storage_pool_size(self, storage_pool_name):
        """Gets the size of storage pool

            Args:

                storage_pool_name (str) -- Name of the storage pool

            Returns:

                result  (int)           --  storage pool size
        """
        query = f"""SELECT mmside.TotalSpaceMB
                    FROM MMSDSStoragePool msds
                    JOIN MMLibrary mml ON msds.LibraryId = mml.LibraryId
                    JOIN MMMountPath mmp ON mml.LibraryId = mmp.LibraryId
                    JOIN MMMediaSide mmside ON mmp.MediaSideId = mmside.MediaSideId
                    WHERE msds.StoragePoolName = '{storage_pool_name}'
                 """

        self.log.info(query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_one_row()
        return int(rows[0])

    def reboot_and_disable_cd_rom(self, esx: EsxManagement, vm_names, host_names=None):
        """Reboots the node and disables CD-ROM

            Args:

                esx         (obj)   --  EsxManagement object

                vm_names    (list)  --  The names of the VMs

                host_names  (list)  --  The host names of the VMs
                                        defaults to vm_names

            Returns:

                result  (bool,str)           --  Whether successful or not and reason if failed
        """
        if host_names is None:
            host_names = vm_names
        # 1. Power down the nodes
        self.log.info("Powering down the nodes")
        for ma in vm_names:
            result = esx.vm_power_control_with_retry_attempts(ma, 'off')
            if not result:
                reason = f"Couldn't power off {ma}"
                return False, reason
            self.log.info(f"{ma} have been powered down")

        # 2. Disable CD-ROMs, so that it boots from hard drive
        self.log.info("Disabling CDROM for all nodes")
        for ma in vm_names:
            esx.vm_set_cd_rom_enabled(ma, False)
            self.log.info(f"{ma} have their CD-ROMs disabled")

        # 3a. Power on the machines
        self.log.info("Powering up the nodes")
        for ma in vm_names:
            result = esx.vm_power_control_with_retry_attempts(ma, 'on')
            if not result:
                reason = f"Couldn't power on {ma}"
                return False, reason
            self.log.info(
                f"{ma} have been powered on. Waiting for boot to complete")

        # 3b. Wait for power on to complete
        for ma in host_names:
            result = self.wait_for_ping_result_to_be(0, ma, retry_duration=60*10) # NJ ring is slow
            if not result:
                reason = f"Failure while waiting for power on to complete for {ma}"
                return False, reason
            self.log.info(f"{ma} is back online")
        time.sleep(10)
        self.log.info(f"Boot is completed on all the nodes")
        return True, None

    def verify_showmembers_output(self, output, count_live_members, count_unreachable_members):
        """Verfies showmembers output based on the given inputs

            Args:

                output                      (str)   --  The showmembers output

                count_live_members          (int)   --  The expected count of live members

                count_unreachable_members   (int)   --  The expected count of unreachable members

            Returns:

                result                      (bool)  --  Whether successful or not
        """
        if not output:
            self.log.error(f"No output to verify: |{output}|")
            return False

        def match_count(memberType, expected):
            """Verify whether the member count matches or not"""
            regex = f'{memberType} MEMBERS:(\\d+)'
            matched = re.findall(regex, output)
            if not matched or len(matched) != 1:
                self.log.error(
                    f"Could not match the regex for {memberType} members. Got |{matched}|")
                return False

            count = int(matched[0])
            if count != expected:
                self.log.error(
                    f"Count mismatch for {memberType} members. Expected {expected}. Got {count}")
                return False
            self.log.info(
                f"Count successfully matched for {memberType} members: {count}")
            return True

        if not match_count('LIVE', count_live_members):
            return False

        if not match_count('UNREACHABLE', count_unreachable_members):
            return False

        return True

    def validate_passwordless_ssh(self, ma_list, ma_machines):
        """Verfies whether passwordless SSH is working across the cluster or not

            Args:

                ma_list     (list)  --  The cluster nodes

                ma_machines (dict)  --  dictionary, MA name -> machine object

            Returns:

                result      (bool)  --  Whether successful or not
        """
        for source_ma in ma_list:
            for destination_ma in ma_list:
                command = f"ssh -q -o StrictHostKeyChecking=no {destination_ma} 'hostname'"
                result = ma_machines[source_ma].execute_command(command)
                output = result.output.strip()
                if output != destination_ma:
                    self.log.error(
                        f"Failed to get correct output from {source_ma} to {destination_ma}. Got {output}. Expected {destination_ma}")
                    return False
                self.log.info(f"Validated {source_ma} --> {destination_ma}")

        return True

    def validate_passwordless_ssh_using_cvhsx(self, ma_list, ma_machines):
        """Verfies whether passwordless SSH is working across the cluster or not
            Ed recommeded this approach, but not using it as on FR 24 (HSX 2.2212 ISO)
            the file cvhsx_cli.py is not present

            Args:

                ma_list     (list)  --  The cluster nodes

                ma_machines (dict)  --  dictionary, MA name -> machine object

            Returns:

                result      (bool)  --  Whether successful or not
        """
        command = "/opt/commvault/MediaAgent/cvhsx_cli.py cluster --get_serial_number"
        identical, result = self.check_identical_output(
            ma_list, ma_machines, command)
        if not identical:
            self.log.error(f"Different outputs received for command {command}")
            return False

        output = result[ma_list[0]]
        if not output:
            self.log.error(f"Empty output for command {command}")
            return False
        # parsing serial numbers from the output and matching
        for ma in ma_list:
            regex = fr'\[{ma}\].*\n(.+)'
            serial = re.findall(regex, output)
            if not serial:
                self.log.error(f"Failed to match serial for {ma}")
                return False
            if len(serial) != 1:
                self.log.error(
                    f"match length incorrect while parsing serial number for {ma}")
                return False
            serial_actual = serial[0]
            output = ma_machines[ma].execute_command(
                "dmidecode -s system-serial-number | tr -d ' ' | tr '[:upper:]' '[:lower:]'")
            serial_expected = output.output.strip()
            if serial_actual != serial_expected:
                self.log.error(
                    f"Failed to match the serial numbers. From hsx_cli {serial_actual}. From dmidecode command {serial_expected}")
                return False
            self.log.info(f"Successfully matched serial numbers for {ma}")
        return True

    def get_sp_version_for_client(self, client_name):
        """Gets the SP version for the client as reported by the CS

            Args:

                client_name (str)           --  The name of the client

            Returns:

                result      (major,minor)   --  The SP version
        """
        if not self.commcell.clients.has_client(client_name):
            raise Exception(f"{client_name} not part of commcell")
        client = self.commcell.clients.get(client_name)
        version_string = client.properties['client']['versionInfo']['version']
        match_obj = re.search(r'ServicePack:(\d+)[.](\d+)', version_string)
        major = int(match_obj.group(1))
        minor = int(match_obj.group(2))
        return major, minor

    def verify_sp_version_for_clients(self, client_names):
        """Verifies the SP version for all clients to be same

            Args:

                client_name     (str)  --  The name of the client

            Returns:

                result      (bool, version)  --  Whether identical or not and the version dictionary
        """
        operations = []
        for name in client_names:
            def lambda_creator(client):
                return lambda: self.get_sp_version_for_client(client)

            operations.append(lambda_creator(name))
        identical, result = self.check_identical_operation_output(
            client_names, operations)
        return identical, result

    def get_sp_version_for_media_agent(self, ma_machine):
        """Gets the SP version for the client as reported by the MA itself

            Args:

                client_name     (str)       --  The name of the client

            Returns:

                result          (int,int)   --  The SP version (major, minor)
        """
        reg_value = ma_machine.get_registry_value(
            "", "sProductVersion", commvault_key='')
        if not reg_value:
            raise Exception(
                f"Couldn't find SP version reg key for {ma_machine.machine_name}")
        _, major, minor = [int(v) for v in reg_value.split('.')]
        return (major, minor)

    def verify_sp_version_for_media_agents(self, client_names):
        """Verifies the SP version for all clients to be same

            Args:

                client_name     (str)       --  The name of the client

            Returns:

                result          (int,int    --  Whether identical or not and the version dictionary
        """
        operations = []
        for name in client_names.values():
            def lambda_creator(client):
                return lambda: self.get_sp_version_for_media_agent(client)

            operations.append(lambda_creator(name))
        identical, result = self.check_identical_operation_output(
            client_names, operations)
        return identical, result

    def track_cvmanager_task(self, machine, new_password, task_name, max_time_mins, tries_interval_mins=5):
        """Tracks cvmanager task by polling it

            Args:

                machine             (obj)   --  The machine object where task is running

                new_password        (str)   --  The new password for this node

                task_name           (str)   --  The name of the task to track

                max_time_mins       (int)   --  The maximum time to track this

                tries_interval_mins (int)   --  The interval between tries

            Returns:

                result              (bool)      --  Whether task successfully completed or not

        """
        log = HyperscaleSetup._get_log()
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        active_task_dir = "/ws/ddb/cvmanager/catalog/active_tasks"
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        def validator():
            try:
                ls = machine.get_items_list(active_task_dir)
                if len(ls)>1: 
                    return True
                return False
            except Exception as e:
                if "No such file or directory" in str(e):
                    log.info("trying again")
                    return False 
                raise
        if not self.wait_for(func=validator, func_validator=bool, interval=2, retry_attempts=None, retry_duration=1800):
            raise Exception("Failed in creating Task File")
        items = machine.get_items_list(active_task_dir)
        items.remove(active_task_dir)

        task_file = items[0].split('/')[-1]
        pid = task_file.split('____')[2].replace('.pid', '')
        pid = int(pid)
        # task_name = task_file.split('____', 1)[0]

        max_tries = max_time_mins//tries_interval_mins
        tries = 0
        success = False
        self.log.info(
            f"Polling status for pid {pid} every {tries_interval_mins} mins for {max_tries} tries spanning {max_time_mins} mins")
        while(tries <= max_tries):
            command = f"{task_manager_dir}/cvmanager_status_cli.py status --get_status task_name={task_name} pid={pid}"
            try:
                output = machine.execute_command(command)
            except Exception as e:
                if str(e) == "Authentication Failed. Invalid credentials provided.":
                    self.log.warning(
                        "Got an authentication exception. Updating machine object and counting it as a try and proceeding")
                    self.log.exception(e)
                    tries += 1
                    machine = UnixMachine(
                        machine.machine_name, username=def_username, password=new_password)
                    time.sleep(tries_interval_mins*60)
                    continue
                raise
            if output.exception:
                self.log.warning(
                    "Got an exception counting it as a try and proceeding")
                self.log.exception(output.exception)
                tries += 1
                time.sleep(tries_interval_mins*60)
                continue
            json_output = json.loads(output.output)
            if json_output['status'] == 'SUCCESS':
                self.log.info(
                    f"Successfully ran the {task_name} task in {tries} tries")
                success = True
                break
            if json_output['status'] == 'RUNNING':
                self.log.info(
                    f"pid {pid} is running. Tries {tries} <= {max_tries}")
            elif json_output['status'] == 'FAILED':
                self.log.error("Task has failed")
                break
            else:
                self.log.error(
                    f"Unknown status encountered: {json_output['status']}")
            tries += 1
            time.sleep(tries_interval_mins*60)

        return success

    class AddNodeYaml(yaml.YAMLObject):
        """Generate yaml object for add node task"""
        """"""
        yaml_tag = "!Task"

        def __init__(self, cs_hostname, cs_username, cs_password, existing_node_hostname, username, cid, nodes_to_add,
                     os_cid=None, cvbackupadmin_password=None
                     ):
            if os_cid is None:
                os_cid = cid

            self.kwargs = {
                "cs_registration": {
                    "registration_cs": cs_hostname,
                    "registration_password": cs_password,
                    "registration_username": cs_username
                },
                "existing_node": {
                    "cid": cid,
                    "hostname": existing_node_hostname,
                    "username": username
                },
                "nodes_to_add": nodes_to_add,
                "os_cid": os_cid,
            }
            if cvbackupadmin_password:
                self.kwargs['cvbackupadmin_password'] = cvbackupadmin_password
            self.type = 'Add_Node_To_Cluster'

    class MetallicAddNodeYaml(yaml.YAMLObject):
        """Generate yaml object for add node task"""
        """"""
        yaml_tag = "!Task"

        def __init__(self, backup_gateway_host, cs_username, cs_password, backup_gateway_port, existing_node_hostname, username, cid, nodes_to_add,
                     os_cid=None, cvbackupadmin_password=None
                     ):
            if os_cid is None:
                os_cid = cid
            self.kwargs = {
                "cs_registration": {
                    "backup_gateway_host": backup_gateway_host,
                    "backup_gateway_port": backup_gateway_port,
                    "registration_password": cs_password,
                    "registration_username": cs_username
                },
                "existing_node": {
                    "cid": cid,
                    "hostname": existing_node_hostname,
                    "username": username
                },
                "nodes_to_add": nodes_to_add,
                "os_cid": os_cid,
            }
            if cvbackupadmin_password:
                self.kwargs['cvbackupadmin_password'] = cvbackupadmin_password
            self.type = 'Add_Node_To_Cluster'

    def cvmanager_add_node_task(self, server_host_name=None, server_user_name=None, server_password=None, cs_host=None,
                                cs_user=None, cs_password=None, existing_node_hostname=None, existing_node_vm_name=None,
                                existing_node_username=None, existing_node_password=None, nodes_to_add=None, cvbackupadmin_password=None):
        """Add Node from cvmanager task

            Args:

                server_host_name        (str)   --  The hostname of ESX server

                server_user_name        (str)   --  The username of the ESX server

                server_password         (str)   --  The password of the ESX server

                cs_host                 (str)   --  The hostname of CS

                cs_user                 (str)   --  The username of the CS

                cs_password             (str)   --  The password of the CS

                existing_node_hostname  (str)   --  One of existing node in a cluster

                existing_node_username  (str)   --  The hostnames of the nodes

                existing_node_password  (str)   --  The name of the storage pool

                nodes_to_add            (str)   --  New node to add

                cvbackupadmin_password  (str)   --  Password for cvbackupadmin user

            Returns:

                None
        """
        add_node_task_obj = HyperScaleHelper.AddNodeYaml(cs_host, cs_user, cs_password, existing_node_hostname,
                                                         existing_node_username, existing_node_password, nodes_to_add, cvbackupadmin_password)
        machine = UnixMachine(
            existing_node_hostname, username=existing_node_username, password=existing_node_password)
        yaml_file_name = "add_node_task.yml"
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        task_yaml = yaml.dump({"tasks": [add_node_task_obj]})
        machine.create_file(f'{task_manager_dir}/{yaml_file_name}', task_yaml)
        esx, vm_io = HyperscaleSetup._get_esx_vm_io(server_host_name, server_user_name, server_password,
                                                    existing_node_vm_name)
        HyperscaleSetup.hsx_login(vm_io, existing_node_password)
        vm_io.send_command(f"cd {task_manager_dir}")
        vm_io.send_command(f"./cvmanager.py {yaml_file_name}")
        time.sleep(60)

        task_name = add_node_task_obj.type
        if not self.track_cvmanager_task(machine, cs_password, task_name, 200):
            return False
        return True

    def metallic_cvmanager_add_node_task(self, server_host_name=None, server_user_name=None, server_password=None, backup_gateway_host=None,
                                cs_user=None, cs_password=None, backup_gateway_port=None, existing_node_hostname=None, existing_node_vm_name=None,
                                existing_node_username=None, existing_node_password=None, nodes_to_add=None, cvbackupadmin_password=None):
        """Add Node from cvmanager task

            Args:

                server_host_name        (str)   --  The hostname of ESX server

                server_user_name        (str)   --  The username of the ESX server

                server_password         (str)   --  The password of the ESX server

                cs_host                 (str)   --  The hostname of CS

                cs_user                 (str)   --  The username of the CS

                cs_password             (str)   --  The password of the CS

                existing_node_hostname  (str)   --  One of existing node in a cluster

                existing_node_username  (str)   --  The hostnames of the nodes

                existing_node_password  (str)   --  The name of the storage pool

                nodes_to_add            (str)   --  New node to add

                cvbackupadmin_password  (str)   --  Password for cvbackupadmin user

            Returns:

                None
        """
        add_node_task_obj = HyperScaleHelper.MetallicAddNodeYaml(backup_gateway_host, cs_user, cs_password, backup_gateway_port,  existing_node_hostname,
                                                         existing_node_username, existing_node_password, nodes_to_add, cvbackupadmin_password)
        machine = UnixMachine(
            existing_node_hostname, username=existing_node_username, password=existing_node_password)
        yaml_file_name = "add_node_task.yml"
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        task_yaml = yaml.dump({"tasks": [add_node_task_obj]})
        machine.create_file(f'{task_manager_dir}/{yaml_file_name}', task_yaml)
        esx, vm_io = HyperscaleSetup._get_esx_vm_io(server_host_name, server_user_name, server_password,
                                                    existing_node_vm_name)
        HyperscaleSetup.hsx_login(vm_io, existing_node_password)
        vm_io.send_command(f"cd {task_manager_dir}")
        vm_io.send_command(f"./cvmanager.py {yaml_file_name}")
        time.sleep(60)

        task_name = add_node_task_obj.type
        if not self.track_cvmanager_task(machine, cs_password, task_name, 200):
            return False
        return True

    class RefreshTaskYaml(yaml.YAMLObject):
        """Generate yaml object for install task"""

        yaml_tag = "!Task"

        def __init__(self, cs_hostname, cs_username, cs_password, preserve_node, os_password,
                     storage_pool_name):
            self.kwargs = {
                "cs_registration": {
                    "registration_cs": cs_hostname,
                    "registration_password": cs_password,
                    "registration_username": cs_username
                },
                "nodes_to_restore": [preserve_node],
                "os_cid": os_password,
                "storage_pool_display_name": storage_pool_name
            }
            self.type = 'Restore_Node'

    def cvmanager_refresh_node_task(self, server_host_name, server_user_name, server_password, cs_host,
                                    cs_user, cs_password, existing_node_hostname, existing_node_vm_name,
                                    existing_node_username, existing_node_password, preserve_node,
                                    storage_pool_name):
        """Refresh Node from cvmanager task

            Args:

                server_host_name        (str)   --  The hostname of ESX server

                server_user_name        (str)   --  The username of the ESX server

                server_password         (str)   --  The password of the ESX server

                cs_host                 (str)   --  The hostname of CS

                cs_user                 (str)   --  The username of the CS

                cs_password             (str)   --  The password of the CS

                existing_node_hostname  (str)   --  One of exisiting node in a cluster

                existing_node_username  (str)   --  Existing node username

                existing_node_password  (str)   --  Existing node password

                preserve_node_hostname  (str)   --  Node to be refreshed

                storage_pool_name       (str)   --  Name of the storage pool

            Returns:

                result                  (bool)  --  Whether successful or not
        """
        refresh_node_task_obj = HyperScaleHelper.RefreshTaskYaml(cs_host, cs_user, cs_password, preserve_node,
                                                                 existing_node_password, storage_pool_name)
        machine = UnixMachine(
            existing_node_hostname, username=existing_node_username, password=existing_node_password)
        yaml_file_name = "refresh_node_task.yml"
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        task_yaml = yaml.dump({"tasks": [refresh_node_task_obj]})
        machine.create_file(f'{task_manager_dir}/{yaml_file_name}', task_yaml)
        esx, vm_io = HyperscaleSetup._get_esx_vm_io(server_host_name, server_user_name, server_password,
                                                    existing_node_vm_name)
        HyperscaleSetup.hsx_login(vm_io, existing_node_password)
        vm_io.send_command(f"cd {task_manager_dir}")
        vm_io.send_command(f"./cvmanager.py {yaml_file_name}")
        time.sleep(60)

        task_name = refresh_node_task_obj.type
        if not self.track_cvmanager_task(machine, existing_node_password, task_name, 200):
            return False
        return True
    
    def get_hyperscale_image_identifier(self, ma_machine):
            """Gets the hyperscale image identifier from the node

                Args:

                    ma_machine                      (str)       --  The name of the MA

                Returns:

                    (major_version,minor_version)   (tuple)     --  Major and minor version in int   
            """
            reg_value = ma_machine.get_registry_value(
                "MediaAgent", "sHyperScaleImageidentifier", commvault_key='')
            if not reg_value:
                raise Exception(
                    f"Couldn't find Hyperscale Image Identifier reg key for {ma_machine.machine_name}")
            result = re.search(r'\d+\.\d+', reg_value).group()
            major_version, minor_version = map(int, result.split('.'))
            return (major_version, minor_version)

    def verify_hyperscale_image_identifier(self, ma_machines):
        """Verifies the hyperscale image identifier for all nodes to be same or not

            Args:

                ma_machines     (dict)       --  The dictionary having ma_name as key and ma machine object as value

            Returns:

                result          (bool, dict)    --  Whether identical or not and a dict with MA name -> hyperscale image identifier
        """
        operations = []
        for name in ma_machines.values():
            def lambda_creator(ma):
                return lambda: self.get_hyperscale_image_identifier(ma)

            operations.append(lambda_creator(name))
        identical, result = self.check_identical_operation_output(
            ma_machines, operations)
        return identical, result
    
    def is_hsx_node_version_equal_or_above(self, ma_machine, major_version, minor_version=None, exact_match=False, or_below=False):
        """Verifies whether hyperscale node has version equal or above to given major and minor version

            Args:

                ma_machine      (obj)           --  Machine class object of MA

                major_version   (int)           --  Major version of Hyperscale node 
                                                    Like (2).x, (3).x 
            
                minor_version   (int)           --  Minor version of Hyperscale node
                                                    Like 2.(2212), 3.(2312)
               
                exact_match     (bool)          --  True if matching for exact version
                
                or_below        (bool)          --  True if need to check for a version below given version

            Returns:

                result          (bool)          --  Returns True if given nodes are having versions as expected
        """

        hsx_image_id = self.get_hyperscale_image_identifier(ma_machine)
        actual_major_version, actual_minor_version = hsx_image_id
        self.log.info(f"Hyperscale Image Identifier -> Commvault Hyperscale {actual_major_version}.{actual_minor_version}")
        def match_versions(v1, v2):
            if exact_match:
                return v1 == v2
            elif or_below:
                return v1 <= v2
            return v1 >= v2
        
        major_version_matches = match_versions(actual_major_version, major_version)
        if minor_version is None or actual_major_version != major_version:
            return major_version_matches
        return match_versions(actual_minor_version, minor_version)

    def is_hsx_cluster_version_equal_or_above(self, ma_machines, major_version, minor_version=None, exact_match=False, or_below=False):
        """Verifies whether hyperscale cluster has version equal or above to given major and minor version

            Args:

                ma_machines     (dict)       --  The dictionary having ma_name as key and ma machine object as value

                major_version   (int)           --  Major version of Hyperscale node 
                                                    Like (2).x, (3).x 
            
                minor_version   (int)           --  Minor version of Hyperscale node
                                                    Like 2.(2212), 3.(2312)
               
                exact_match     (bool)          --  True if matching for exact version
                
                or_below        (bool)          --  True if need to check for a version below given version

            Returns:

                result_list     (dict)          --  Dictionary with key as ma_name and value as boolean 
                                                    with True denoting version check is successful
        """

        result_list = {}
        for ma_name, ma_machine in ma_machines.items():
            result = self.is_hsx_node_version_equal_or_above(ma_machine, major_version, minor_version, exact_match, or_below)
            if not result:
                self.log.error(f"Version check failed for {ma_name}")
            else:
                self.log.info(f"Version check successful for {ma_name}")
            result_list[ma_name] = result
        return result_list

    def verify_repo_checksum(self, xml_path, machine, repo_path='Unix/rhel-7.9/cv-hedvig', ignore_orphan_rpms = True):
        """Verifies the repo checksum

            Args:

                xml_path            (str)   --  The folder path in which CVApplianceConfig_Unix.xml is present

                machine             (obj)   --  The machine object which has the RPMs

                repo_path           (str)   --  The path to the repo starting with <Platform>/<OS>

                ignore_orphan_rpms  (bool)  --  Ignores orphan RPMs - which are neither in cache and nor installed                 (str)   --  The hostname of CS

            Returns:

                result              (bool)  --  Whether successful or not
        """
        tree = etree.parse(f'{xml_path}/CVApplianceConfig_Unix.xml')
        root = tree.getroot()
        repo_xml_path_rpms = root.xpath(f"//patches[starts-with(@SourcePath, '{repo_path}')]")
        sha_values_expected = {e.attrib['Name']:e.attrib['CheckSum2'] for e in repo_xml_path_rpms}

        software_cache_path = '/opt/commvault/SoftwareCache'
        repo_path_rpms = f'{software_cache_path}/CVAppliance/{repo_path}/Packages'
        output = machine.execute_command(f"cd {repo_path_rpms}; sha256sum *.rpm")
        result = output.output.strip()
        rpms_list = [re.split(r'\s+', n) for n in result.split('\n')]
        sha_values_actual = {n[1]:n[0] for n in rpms_list}
        rpms_sha_mismatch = []
        rpms_orphan = []
        for rpm, sha in sha_values_expected.items():
            self.log.info("="*30)
            self.log.info(f"Checking for {rpm}")
            if rpm in sha_values_actual:
                if sha == sha_values_actual[rpm]:
                    self.log.info(f"sha matches")
                else:
                    self.log.warn(f"sha doesn't match")
                    self.log.info(f"sha cache folder: {sha_values_actual[rpm]}")
                    self.log.info(f"sha XML file: {sha}")
                    rpms_sha_mismatch.append(rpm)
                del sha_values_actual[rpm]
            else:
                result = machine.execute_command(f"rpm -qi {rpm[:-4]}")
                if result.exit_code == 0:
                    self.log.info(f"rpm not found in SW cache but is installed")
                else:
                    self.log.warn(f"Neither rpm was found in SW cache nor was it installed")
                    rpms_orphan.append(rpm)
        if ignore_orphan_rpms:
            rpms_orphan = []

        return len(rpms_sha_mismatch) == 0 & len(rpms_orphan) == 0
        
    def verify_repo_checksum_csv(self, csv_path, repo_type, machine, ignore_orphan_rpms = False):
        """Verifies the repo checksum

            Args:

                csv_path            (str)   --  The file path in which expected rpm,sha values are present

                repo_type           (str)   --  The OS of the repo like rhel-7.9

                machine             (obj)   --  The machine object which has the RPMs

                ignore_orphan_rpms  (bool)  --  Ignores orphan RPMs - which are neither in cache and nor installed

            Returns:

                result              (bool)  --  Whether successful or not
        """
        with open(csv_path, 'r') as csv_file:
            lines = csv_file.read().splitlines()
            sha_values_expected = dict([line.split(',') for line in lines])

        software_cache_path = '/opt/commvault/SoftwareCache'
        repo_path_rpms = f'{software_cache_path}/CVAppliance/Unix/{repo_type}/cv-hedvig/Packages'
        output = machine.execute_command(f"cd {repo_path_rpms}; sha256sum *.rpm")
        result = output.output.strip()
        rpms_list = [re.split(r'\s+', n) for n in result.split('\n')] if result else []
        sha_values_actual = {n[1]:n[0] for n in rpms_list}
        rpms_sha_mismatch = []
        rpms_orphan = []
        for rpm, sha in sha_values_expected.items():
            self.log.info("="*30)
            self.log.info(f"Checking for {rpm}")
            if rpm in sha_values_actual:
                if sha == sha_values_actual[rpm]:
                    self.log.info(f"sha matches")
                else:
                    self.log.warn(f"sha doesn't match")
                    self.log.info(f"sha cache folder: {sha_values_actual[rpm]}")
                    self.log.info(f"sha XML file: {sha}")
                    rpms_sha_mismatch.append(rpm)
                del sha_values_actual[rpm]
            else:
                result = machine.execute_command(f"rpm -qi {rpm[:-4]}")
                if result.exit_code == 0:
                    self.log.info(f"rpm not found in SW cache but is installed")
                else:
                    self.log.warn(f"Neither rpm was found in SW cache nor was it installed")
                    rpms_orphan.append(rpm)
        if ignore_orphan_rpms:
            rpms_orphan = []

        return len(rpms_sha_mismatch) == 0 & len(rpms_orphan) == 0
     

    def set_root_access(self, storage_pool_name, media_agent, root_access):
        """Enable/Disable root access

        Args:

            storage_pool_name   (str)      --   Name of the Storage Pool

            media_agent         (str|obj)  --   name of media agents(str)
                                                or instance of media agent's(object)

            root_access         (bool)     --   True to enable root, False 
                                                to disable root access


        Raises Exception:

                    if error or no response recieved from API request
        """

        mediagent_obj = None
        if isinstance(media_agent, MediaAgents):
            mediagent_obj = media_agent
        elif isinstance(media_agent, str):
            mediagent_obj = self.commcell.media_agents.get(media_agent)
        else:
            raise Exception('Invalid arguments')

        storage_pool_obj = self.commcell.storage_pools.get(storage_pool_name)
        request_json = {
            "StoragePolicy": {
                "storagePolicyId": int(storage_pool_obj.storage_pool_id),
                "storagePolicyName": "{0}".format(storage_pool_name),
            },
            "storage": [
                {
                    "mediaAgent": {
                        "mediaAgentId": int(mediagent_obj.media_agent_id),
                        "mediaAgentName": "{0}".format(mediagent_obj.media_agent_name)
                    }
                }
            ],
            "scaleoutOperationType": 5,
            "disableRootAccess": int(not root_access)
        }
        
        response = self.commcell.request(
            "POST", 'StoragePool?Action=edit', request_json) 
        if response.json():
            error_code = response.json()['errorCode']

            if int(error_code) != 0:
                error_message = response.json()['errorMessage']
                o_str = 'Failed to enable root access\nError: "{0}"'

                raise Exception(o_str.format(error_message))

        else:
            raise Exception("Failed to enable root access")
        return True
    
    def trigger_platform_update(self, server_group_name, non_disruptive=False, update_cvfs = False, update_os = False):
        """Triggers the platform update job on the CS

        Args:

            server_group_name   (str)      --   Name of the Storage Pool

            non_disruptive      (bool)  --  whether this update should happen non disruptively

            update_cvfs         (bool)  --  whether it should update CVFS or not

            update_os           (bool)  --  whether it should update CVFS or not

        Raises Exception:

                    if error or no response recieved from API request

        Returns:

                job             (obj)  --  The job which gets triggered
        """
        install = Install(self.commcell)
        options = 0
        if update_os:
            options = options | InstallUpdateOptions.UPDATE_INSTALL_HYPERSCALE_OS_UPDATES.value
        if self.commcell.commserv_version >= 36:
            if update_cvfs:
                options = options | InstallUpdateOptions.UPDATE_INSTALL_HSX_STORAGE_UPDATES.value
            if not non_disruptive:
                options = options | InstallUpdateOptions.UPDATE_INSTALL_HSX_STORAGE_UPDATES_DISRUPTIVE_MODE.value
        else:
            if update_cvfs:
                if non_disruptive:
                    options = options | InstallUpdateOptions.UPDATE_INSTALL_HSX_STORAGE_UPDATES.value
                else:
                    options = options | InstallUpdateOptions.UPDATE_INSTALL_HSX_STORAGE_UPDATES_DISRUPTIVE_MODE.value
                
        job = install.push_servicepack_and_hotfix(
            client_computer_groups=[server_group_name], 
            install_update_options=options
            )
        return job
    
    def trigger_platform_update_v4(self, server_group_name, non_disruptive=False, update_cvfs = False, update_os = False):
        """Triggers the platform update job on the CS

        Args:

            server_group_name   (str)      --   Name of the Storage Pool

            non_disruptive      (bool)  --  whether this update should happen non disruptively

            update_cvfs         (bool)  --  whether it should update CVFS or not

            update_os           (bool)  --  whether it should update CVFS or not

        Raises Exception:

                    if error or no response recieved from API request

        Returns:

                job             (obj)  --  The job which gets triggered
        """
        request_json = {
            "rebootIfRequired": False,
            "runDBMaintenance": False,
            "installDiagnosticUpdates": True,
            "notifyWhenJobCompletes": False,
            "installOSUpdates": update_os,
            "installStorageUpdates": update_cvfs,
            "hyperscalePlatformUpgradeMode": "NON_DISRUPTIVE" if non_disruptive else "DISRUPTIVE",
            "entities": [
                {
                "name": server_group_name,
                "type": "CLIENT_GROUP_ENTITY"
                }
            ]
        }
        _cvpysdk_object = self.commcell._cvpysdk_object
        url = self.commcell._services.get('UPGRADE_SOFTWARE', 
                                          self.commcell._services['CREATE_RC'].replace("SoftwareCache", "UpgradeSoftware"))
        flag, response = _cvpysdk_object.make_request(
            'PUT', url, request_json
        )
        if not flag:
            self.log.error(f"Error while calling the API")
            return
        if not response.json():
            self.log.error(f"Couldn't convert to json")
            return
        if "jobId" not in response.json():
            self.log.error(f"json doesn't contain a job id")
            return
        return Job(self.commcell, response.json()['jobId'])
    
    def fetch_node_platform_version_from_csdb(self, ma_name):
        """Method that fetches platform version from CSDB for a hyperscale node 

            Args:

                ma_name             (str)       --  Name of MA

            Returns:

                platform_version    (str)       --  Platform version of the MA provided from CSDB
                                                    False if couldn't find platform version from CSDB
        """

        query = f"""SELECT HardwareInformation.value('(/MediaManager_WSPlatformHwInfo/swInfo/@platformVersion)[1]', 'VARCHAR(255)') AS platformVersion
                  FROM App_Client INNER JOIN MMScaleOutMAInfo
                  ON App_Client.id = MMScaleOutMAInfo.ClientId 
                  WHERE App_Client.net_hostname = '{ma_name}'; """
        self.csdb.execute(query)
        platform_version = self.csdb.fetch_one_row()[0]
        if not platform_version:
            reason = f"Query didnt return any results from CSDB"
            self.log.error(reason)
            return False
        return platform_version
    
    def fetch_cluster_platform_version_from_csdb(self, ma_names):
        """Method that fetches platform version from CSDB for all nodes in hyperscale cluster

            Args:

                ma_names            (list)          --  List of names of MAs

            Returns:

                identical           (bool)          --  True if all nodes in cluster have same platform_version

                result              (dict)          --  ma_name -> platform_version
        """

        operations = []
        for ma_name in ma_names:
            def lambda_creator(ma_name):
                return lambda: self.fetch_node_platform_version_from_csdb(ma_name)

            operations.append(lambda_creator(ma_name))
        identical, result = self.check_identical_operation_output(
            ma_names, operations)
        return identical, result
    
    def fetch_node_platform_version_from_payload(self, ma_machine):
        """Fetches platform version of a hyperscale node from payload release date

            Args:

                ma_machine          (obj)   --  Machine object of the MA

            Returns:
                
                platform_version    (str)   --  platform version of the MA as reported from MA
                                                False if unable to find payload date
        """

        iso_major_version, _ = self.get_hyperscale_image_identifier(ma_machine)
        command = f"/opt/commvault/MediaAgent/cv_hs_version.py version -j"
        output = ma_machine.execute_command(command)
        json_output = json.loads(output.output)
        payload_date = json_output.get('date')
        if not payload_date:
            reason = f"Unable to find date from json"
            self.log.error(reason)
            return False
        self.log.info(f"Payload date -> {payload_date}")
        parsed_payload_date = datetime.strptime(payload_date, "%a %b %d %H:%M:%S %Y").strftime("%y%m")
        platform_version = str(iso_major_version) + '.' + parsed_payload_date
        return platform_version
    
    def fetch_cluster_platform_version_from_payload(self, ma_machines):
        """Fetches platform version of a hyperscale node from payload release date

            Args:

                ma_machines         (dict)   --  ma_name -> machine object

            Returns:
                
                identical           (bool)  --  True if all nodes in the cluster have the same platform version
                
                result              (dict)  --  ma_name -> platform_version/False   
        """

        operations = []
        for ma_machine in ma_machines.values():
            def lambda_creator(ma_machine):
                return lambda: self.fetch_node_platform_version_from_payload(ma_machine)

            operations.append(lambda_creator(ma_machine))
        identical, result = self.check_identical_operation_output(
            ma_machines, operations)
        return identical, result

    def validate_node_kernel_version(self, ma_machine):
        """ Validates kernel version to ensure kernel version is as expected on a hyperscale node

            Args:

                ma_machine          (obj)       --  Machine object of the MA

            Returns:

                result              (bool)      --  True if kernel versions from OS and json match    
        """

        command = f"uname -r"
        output = ma_machine.execute_command(command)
        # kernel version from OS looks like - 3.10.0-1160.118.1.el7.x86_64
        kernel_version_from_os = output.output
        self.log.info(f"Kernel version from OS -> {kernel_version_from_os}")
        command = f"/opt/commvault/MediaAgent/cv_hs_version.py version -j"
        output = ma_machine.execute_command(command)
        json_output = json.loads(output.output)
        # kernel version from json looks like - kernel-3.10.0-1160.118.1
        kernel_version_from_json = json_output.get('kernel_version')
        if not kernel_version_from_json:
            reason = f"Unable to find kernel version from json"
            self.log.error(reason)
            return False
        self.log.info(f"Kernel version from json -> {kernel_version_from_json}")
        # Parsed kernel version from json looks like - 3.10.0-1160.118.1
        parsed_kernel_version_from_json = re.sub(r'^kernel-',"",kernel_version_from_json)
        self.log.info(f"Parsed kernel version from json -> {parsed_kernel_version_from_json}")
        if parsed_kernel_version_from_json not in kernel_version_from_os:
            reason = f"Kernel versions from OS and json do not match"
            self.log.error(reason)
            return False
        self.log.info(f"Kernel versions from OS and json match")
        return True
    
    def validate_cluster_kernel_versions(self, ma_machines):
        """Validates kernel version to ensure kernel version is as expected on all hyperscale nodes

            Args:

                ma_machines         (dict)   --  ma_name -> machine object

            Returns:
                
                identical           (bool)  --  True if all nodes in the cluster have the same kernel version
                
                result              (dict)  --  ma_name -> True/False   
        """

        operations = []
        for ma_machine in ma_machines.values():
            def lambda_creator(ma_machine):
                return lambda: self.validate_node_kernel_version(ma_machine)

            operations.append(lambda_creator(ma_machine))
        identical, result = self.check_identical_operation_output(
            ma_machines, operations)
        return identical, result
    
    def hsx_create_storage_pool(self, storage_pool_name, mas):
        """
            Create a hyperscale storage pool containing 3 nodes

            Args:
                storage_pool_name (str) -- Name of the storage pool
               *args: Media agent names
                    ma1_name (str) -- Name of the first MA
                    ma2_name (str) -- Name of the second MA
                    ma3_name (str) -- Name of the third MA

            Return:
                flag (int) -- Response code received from the Rest API call
                response (str) -- Response received from the Rest API
                status (boolean) -- True or False based on the success or failure of the operation
        """
        ma_values = [self.commcell.media_agents.get(value) for value in mas]
        self.commcell.storage_pools.hyperscale_create_storage_pool(
            storage_pool_name, mas)

        status = self.wait_for_completion(storage_pool_name)
        self.log.info("Storage Pool status %s", status)
        response = self.get_storage_pool_details(storage_pool_name)
        self.log.info(response)

        return status, response

    def is_added_node(self,ma_machine):
        """ Checks whether given node is an added node

        Args:
            
            ma_machine  (obj)   --  Machine object of MA

        Return:

            result      (bool)  --  True if node is an added node
        """

        command = f"cat /etc/hedvig/role"
        self.log.info(f"Command -> {command}")
        output = ma_machine.execute_command(command)
        self.log.info(f"Services on node -> {output.output}")
        
        # Output looks like 
        # HV_ROLE=deploynode,cvm,hblock # BUILT (Added node)
        # HV_ROLE=deploynode,cvm,hpod,hblock,pages # BUILT (Existing node)
        hv_roles = output.output.split('=')[1].split('#')[0].strip().split(',')

        if 'hpod' not in hv_roles and 'pages' not in hv_roles:
            self.log.info("hpod and pages absent in HV_ROLE. This is an added node")
            return True
        self.log.info("hpod and pages present in HV_ROLE. This is not an added node")
        return False
        
    def is_refreshed_node(self, ma_machine):
        """ Checks whether given node was refreshed or not

        Args:
        
            ma_machine      (obj)   --  Machine object of MA

        Returns:
            
            result          (bool)  --  True if node was refreshed
        """
        if not ma_machine.check_registry_exists('MediaAgent', 'sHyperScalePreserve'):
            self.log.info(f"sHyperScalePreserve reg key absent on node. Not a refreshed node")
            return False
        self.log.info(f"sHyperScalePreserve reg key present on node. This is a refreshed node")
        return True

    def trigger_sendlogs(self, ma_name, local_path):
        """
        Here local_path is that of the CS
        """
        request_json = {
            "taskInfo": {
                "task": {
                "taskType": 1,
                "initiatedFrom": 1,
                "policyType": 0,
                "taskFlags": {
                    "disabled": False
                }
                },
                "subTasks": [
                {
                    "subTask": {
                    "subTaskType": 1,
                    "operationType": 5010
                    },
                    "options": {
                        "adminOpts": {
                            "sendLogFilesOption": {
                                "actionLogsEndJobId": 0,
                                "emailSelected": True,
                                "jobid": 0,
                                "tsDatabase": False,
                                "galaxyLogs": True,
                                "getLatestUpdates": False,
                                "actionLogsStartJobId": 0,
                                "computersSelected": True,
                                "csDatabase": False,
                                "otherDatabases": False,
                                "crashDump": False,
                                "isNetworkPath": False,
                                "saveToFolderSelected": True,
                                "notifyMe": True,
                                "includeJobResults": False,
                                "doNotIncludeLogs": True,
                                "machineInformation": True,
                                "scrubLogFiles": False,
                                "emailSubject": f"sendLogs automation for {ma_name}",
                                "osLogs": True,
                                "allUsersProfile": True,
                                "splitFileSizeMB": 512,
                                "actionLogs": False,
                                "includeIndex": False,
                                "databaseLogs": True,
                                "includeDCDB": False,
                                "collectHyperScale": True,
                                "logFragments": False,
                                "uploadLogsSelected": True,
                                "useDefaultUploadOption": True,
                                "enableChunking": True,
                                "saveToLogDir": local_path,
                                "collectRFC": False,
                                "collectUserAppLogs": False,
                                "impersonateUser": {
                                    "useImpersonation": False
                                },
                                "clients": [
                                    {
                                    "clientName": ma_name
                                    }
                                ],
                                "sendLogsOnJobCompletion": False
                            }
                        }
                    }
                }
                ]
            }
        }
        _cvpysdk_object = self.commcell._cvpysdk_object
        url = self.commcell._services['CREATE_TASK']
        flag, response = _cvpysdk_object.make_request(
            'POST', url, request_json
        )
        
        if not flag:
            reason = f"Error while calling the API"
            self.log.error(reason)
            return False, reason
        
        if not response.json():
            reason = f"Couldn't convert to json"
            self.log.error(reason)
            return False, reason
        
        if "jobIds" not in response.json():
            reason = f"json doesn't contain a job id"
            self.log.error(reason)
            return False, reason
        
        job_obj = Job(self.commcell, response.json()['jobIds'][0])
        
        self.log.info(f"Started the sendlogs job [{job_obj.job_id}]")
        if not job_obj.wait_for_completion():
            self.log.info("Sendlogs job failed")
            return False, job_obj.status
        self.log.info("Sendlogs job succeeded")
        return True, None
    
    def verify_sendlogs(self, path, hostname, username, password):
        '''
        Given the path under which send logs .7z file is present and creds for the machine
        this function runs a quick validation on it
        '''
        # 1. Check if the .7z file exists at path at hostname
        self.log.info(f"Checking if .7z file exists at {username}@{hostname}:{path}")
        machine = Machine(hostname, username=username, password=password)
        files = machine.get_items_list(path)
        if not files:
            raise Exception(f"No send logs file exists at {path}")
        sendlogs_7z_file = files[-1]
        if not sendlogs_7z_file.endswith('.7z'):
            raise Exception(f"Send logs file does't end with .7z")
        self.log.info(f"Found .7z file {sendlogs_7z_file}")
        
        # 2. Get the file to this machine so that we can process it
        # TODO: test this on a remote windows system as well
        parent_path = Path("sendlogs/")
        self.log.info(f"Trying to download {sendlogs_7z_file} locally to {parent_path}")
        remote_client = SSHClient()
        remote_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remote_client.connect(hostname=hostname, username=username, password=password)
        ftp_client = remote_client.open_sftp()
        
        if parent_path.is_dir():
            shutil.rmtree(parent_path)
            self.log.info(f"Deleting already existing {parent_path}")
        parent_path.mkdir()
        
        local_7z_file_name = parent_path / Path('sendlogs.7z')
        ftp_client.get(sendlogs_7z_file, str(local_7z_file_name))
        self.log.info(f"Successfully downloaded to {local_7z_file_name}")
        
        # 3. extract from the .7z file to get a .tar file
        self.log.info(f"Now processing {local_7z_file_name}")
        with py7zr.SevenZipFile(local_7z_file_name, mode='r') as z:
            z.extractall(path=parent_path)
        self.log.info(f"Successfully extracted the tar file")
            
        # 4. extract from the .tar file to get node .tar.gz file
        extracted_tar_file = parent_path / Path(sendlogs_7z_file).with_suffix('.tar').name
        self.log.info(f"Now processing {extracted_tar_file}")
        tarfile_obj = tarfile.open(name=extracted_tar_file, mode='r')
        node_tar_gz_file = [tarfile_obj.getmember(l) for l in tarfile_obj.getnames() if l.endswith('.tar.gz')]
        if not node_tar_gz_file:
            raise Exception("Couldn't find the .tar.gz file inside the .tar.7z file")
        node_tar_gz_info = node_tar_gz_file[0]
        node_tar_gz_info.name = parent_path / node_tar_gz_info.name
        tarfile_obj.extractall(members=[node_tar_gz_info])
        self.log.info(f"Successfully extracted {node_tar_gz_info.name}")
        
        # 5. extract from the node .tar.gz file to get sosreport.tar.xz
        self.log.info(f"Now processing {node_tar_gz_info.name}")
        tarfile_obj = tarfile.open(name=node_tar_gz_info.name, mode='r:gz')
        sosreport_file = [tarfile_obj.getmember(l) for l in tarfile_obj.getnames() if l.endswith('.tar.xz')]
        if not sosreport_file:
            raise Exception("Couldn't find the sos report file inside the node .tar.gz file")
        sosreport_info = sosreport_file[0]
        sosreport_info.name = parent_path / "sosreport.tar.xz"
        tarfile_obj.extractall(members=[sosreport_info])
        self.log.info(f"Successfully extracted {sosreport_info.name}")
        
        # 6. verify paths in sosreport.tar.xz
        tarfile_obj = tarfile.open(name=sosreport_info.name)
        self.log.info(tarfile_obj.getnames())
        
        
    