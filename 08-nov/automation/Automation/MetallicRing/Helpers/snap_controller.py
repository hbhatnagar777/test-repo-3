# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for managing the VMs used for Metallic Ring configuration

    RingSnapController:

        __init__()                              --  Initializes Ring snap controller

        start_task                              --  Starts the reports related tasks for metallic ring

        get_all_vms                             --  Gets all the VMs in the config file

        create_snap                             --  creates a snapshot on a given VM name

        check_snap_exists                       --  Checks if a given snapshot on a VM is present

        get_parent_snap                         --  Gets the first snap created on a VM

        list_snap                               --  Lists all the snap which are present in a VM

        restore_vm_snap                         --  Restores VM snap based on the snap name passed

        delete_snap                             --  Deletes the snapshot on a VM

        start_vm                                --  Starts a VM with a given name


    Snapshot:

        __init__()                              --  Initializes Snapshot class for a VM


"""

import json
from time import sleep

from datetime import datetime
from AutomationUtils import logger
from AutomationUtils.config import get_config
from dynamicindex.utils import vmutils as vm_helper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_SNAP_OPTION = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.snap_options


class RingSnapController:
    """ helper class for managing the VMs used for Metallic Ring configuration"""

    def __init__(self):
        self.log = logger.get_log()
        self.sleep_time = 20
        self.status = cs.FAILED

    def start_task(self):
        """Starts the tasks for managing the VMs for metallic ring"""
        self.log.info("Starting snap controller task")
        message = None
        try:
            self.log.info("Trying to get all the VMs in the Config file")
            client_list = self.get_all_vms()
            self.log.info(f"Virtual machine list obtained. VM client - [{client_list}]")
            if _SNAP_OPTION.rerun == 1:
                self.log.info("Option to rerun the automation is selected")
                for client_name in client_list:
                    self.log.info(f"Getting the parent checkpoint for VM [{client_name}]")
                    snap = self.get_parent_snap(client_name)
                    self.log.info(f"Parent snap shot obtained is [{snap.name}]. Restoring the VM to parent snap")
                    self.restore_vm_snap(client_name, snap.name)
                    self.log.info("Parent snap shot restored. Starting the VM")
                    self.start_vm(client_name)
                    self.log.info("VM started successfully. Please make sure all the services are up and running")
                sleep_time = self.sleep_time * 7
                self.log.info(f"sleeping for [{sleep_time}] seconds")
                sleep(sleep_time)
                self.log.info("sleep complete")
            else:
                self.log.info("Snap rerun option is disabled")
            if _SNAP_OPTION.take_snap == 1:
                self.log.info("Take snap option is set. Creating snaps for clients")
                for client_name in client_list:
                    self.log.info(f"Creating snap for client [{client_name}]")
                    self.create_snap(client_name, cs.SNAP_NAME % (client_name,
                                                                  datetime.now().strftime("%m/%d/%Y, %H:%M:%S")))
                    self.log.info(f"Snap Created for client - [{client_name}]")
            else:
                self.log.info("Create snap option is disabled by default")
            self.status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute snap controller. Exception - [{exp}]"
            self.log.info(message)
        return self.status, message

    def get_all_vms(self):
        """
        Gets all the virtual machines in the config file
        Returns:
            List of VM names in the present in the config file
        """
        self.log.info("Fetching all the VM clients")
        all_clients = []
        commserv = _CONFIG.commserv
        all_clients.append(commserv.client_name)

        mas = _CONFIG.media_agents
        for media_agent in mas:
            all_clients.append(media_agent.client_name)

        wcs = _CONFIG.web_consoles
        for web_console in wcs:
            all_clients.append(web_console.client_name)

        wss = _CONFIG.web_servers
        for web_server in wss:
            all_clients.append(web_server.client_name)

        nps = _CONFIG.network_proxies
        for network_proxy in nps:
            all_clients.append(network_proxy.client_name)

        iss = _CONFIG.index_servers
        for is_config in iss:
            nodes = is_config.nodes
            for node in nodes:
                all_clients.append(node)

        case_insensitive_clients = []
        for client_name in all_clients:
            case_insensitive_clients.append(client_name)
        unique_client_list = set(case_insensitive_clients)
        self.log.info(f"Client list obtained is [{unique_client_list}]")
        return unique_client_list

    def create_snap(self, vm_name, snap_name):
        """
        Creates a snapshot for a given VM
        Args:
            vm_name(str)        -   Name of the Virtual Machine
            snap_name(str)      -   Name of the snap to be created
        Raises:
            Exception:
                When snapshot creation fails
                When snapshot created doesn't exist
        """
        self.log.info(f"Creating snapshot for VM - [{vm_name}]. Snap - [{snap_name}]")
        vm_helper.create_vm_snapshot(vm_name, snap_name)
        sleep(self.sleep_time)
        if not self.check_snap_exists(vm_name, snap_name):
            raise Exception("Snapshot creation failed")
        self.log.info(f"Snapshot [{snap_name}] created successfully for VM [{vm_name}]")

    def check_snap_exists(self, vm_name, snap_name):
        """
        Checks if the snapshot exists for a given VM
        Args:
            vm_name(str)        -   Name of the Virtual Machine
            snap_name(str)      -   Name of the snap to be checked
        Returns:
            True if snapshot with given name is present
            False if snapshot with given name is not present
        """
        self.log.info(f"Checking if snapshot [{snap_name}] for VM - [{vm_name}] exists")
        snap_list = self.list_snap(vm_name)
        for snap in snap_list:
            if snap.name == snap_name:
                self.log.info("snapshot is found")
                return True
        self.log.info("Snapshot is not present")
        return False

    def get_parent_snap(self, vm_name):
        """
        Get the base snapshot of the VM
        Args:
            vm_name(str)        -   Name of the Virtual Machine
        Returns:
            Object of parent snapshot
        """
        self.log.info(f"Trying to fetch the parent snap information for vm - [{vm_name}]")
        snap_list = self.list_snap(vm_name)
        for snap in snap_list:
            if snap.is_parent:
                self.log.info(f"Parent snap found - [{snap.name}]")
                return snap
        self.log.info(f"No parent checkpoints found for this VM [{vm_name}]")

    def list_snap(self, vm_name):
        """
        List the snaps on a VM
        Args:
            vm_name(str)        -   Name of the Virtual Machine
        """
        self.log.info("Fetching the list of snapshots for a given client")
        snap_list_obj = vm_helper.list_vm_snaps(vm_name)
        snap_list_json = json.loads(snap_list_obj)
        snap_list = []
        if isinstance(snap_list_json, list):
            for snap in snap_list_json:
                snapshot = Snapshot(snap.get("Name"), snap.get("ParentSnapshotName"), snap.get("CreationTime"))
                snap_list.append(snapshot)
        else:
            snapshot = Snapshot(snap_list_json.get("Name"), snap_list_json.get("ParentSnapshotName"),
                                snap_list_json.get("CreationTime"))
            snap_list = [snapshot]
        self.log.info(f"List of snapshot obtained. Snap List [{snap_list}]")
        return snap_list

    def restore_vm_snap(self, vm_name, snap_name):
        """
        Restore the snapshot on a VM
        Args:
            vm_name(str)        -   Name of the Virtual Machine
            snap_name(str)      -   Name of the snap to be restored
        Raises:
            Exception:
                If snap restore fails
        """
        self.log.info(f"Trying to restore snapshot [{snap_name}] for VM - [{vm_name}]")
        vm_helper.restore_vm_snap(vm_name, snap_name)
        self.log.info("Snapshot restored successfully")

    def delete_snap(self, vm_name, snap_name):
        """
        Deletes the snapshot on a VM
        Args:
            vm_name(str)        -   Name of the Virtual Machine
            snap_name(str)      -   Name of the snap to be deleted
        Raises:
            Exception:
                If snap deletion fails
        """
        self.log.info(f"Trying to delete snapshot [{snap_name}] for VM - [{vm_name}]")
        vm_helper.remove_vm_snapshot(vm_name, snap_name)
        self.log.info("Snapshot deleted successfully")

    def start_vm(self, vm_name):
        """
        Starts a VM with a given name
        Args:
            vm_name(str)        -   Starts a VM with a given name
        Raises:
            Exception:
                If VM failed to start
        """
        self.log.info(f"Trying to start VM with name - [{vm_name}]")
        vm_helper.start_vm(vm_name)
        self.log.info("VM started successfully")


class Snapshot:
    """Class for holding the snapshot information"""
    def __init__(self, name, parent, creation_time):
        self.is_parent = False
        self.name = name
        self.parent = parent
        self.creation_time = creation_time
        if self.parent is None:
            self.is_parent = True
