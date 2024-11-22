# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright © Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import atexit
import gzip
from math import ceil
import tarfile
from lxml import etree
import threading
import time
import socket
from pathlib import Path
import re
import requests
import yaml
import base64
from typing import Tuple
import json
import sys
import paramiko
import urllib.parse
import psutil
from paramiko.ssh_exception import BadAuthenticationType

from selenium.webdriver.support.wait import WebDriverWait
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.config import get_config

from Server.JobManager.jobmanager_helper import JobManager

from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from AutomationUtils import logger
from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException

from pyVim import connect
from pyVim.task import WaitForTask
from pyVmomi import vim

from HyperScale.HyperScaleUtils.esx_console import EsxConsole
from HyperScale.HyperScaleUtils.esx_vm_io import EsxVmIo
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.screen_matcher import ScreenMatcher
from Web.Common.cvbrowser import BrowserFactory


class HyperscaleSetup:
    """
    This class has all the functions needed to create a
    Hyperscale setup.

    No instance need to be created. Just use the functions
    after supplying appropriate parameters

    _get_esx()                          --  Utility method to instantiate the ESX object

    _get_vm_io()                        --  Utility method to instantiate the VmIo object

    _get_esx_vm_io()                    --  Utility method to instantiate the ESX and VmIo object

    _get_log()                          --  Utility method to get the logger object

    _search_for_obj()                   --  Utility method to search the managed object for the name and type specified

    _get_hyperscale_default_creds()     --  Get default hyperscale username and password

    _get_hyperscale_scripts_path()      --  Get the Hyperscale scripts path

    _get_commcell()                     --  Get the commcell object

    get_self_ip()                       --  Utility method to get the IP of this controller

    get_vm_ip()                         --  Gets the IP address of the VM

    find_device()                       --  Finds a particular device_type for a VM

    vm_set_boot_from_cd()               --  Sets the boot from CD option

    clone_vm()                          --  Clones the template into a VM

    _hs_install_vm_reboot()             --  Reboots the VM, optionally can set the boot from CD option

    _hs_install_boot_screen_press_enter()           --  Navigates the BOOT_SCREEN_PRESS_ENTER screen

    _hs_install_reimage_screen_initial_preserve()   --  Navigates the REIMAGE_SCREEN_INITIAL screen

    _hs_install_screen_initial_hsx()    --  Navigates the INSTALL_SCREEN_INITIAL screen

    _is_vm_datastore_ssd()              --  Returns True if vm is on an SSD, false if not on SSD

    _hs_install_screen_finished()       --  Navigates the INSTALL_SCREEN_FINISHED screen

    start_hyperscale_install()          --  1.5 ISO installation

    basic_network_config()              --  1.5 ISO basic network config

    run_setupsds()                      --  1.5 ISO running setupsds

    run_update()                        --  Update the nodes' CV software

    vm_change_cd_rom_iso()              --  Changes the ISO on VM, optionally shuts down the VM

    start_hyperscale_x_install()        --  ISO installation for HSX

    hsx_login()                         --  Navigates the initial shell prompt banner screen

    hsx_bond_creation()                 --  Performs bond creation for HSX

    hsx_block_config()                  --  Performs block configuration for HSX

    hsx_machine_setup()                 --  Copies the helper shell scripts

    hsx_network_config()                --  Performs network configuration for HSX

    hsx_html_installer()                --  HSX HTML installer

    create_vm_config_spec()             --  Creates the config spec for creating new VM

    create_vm()                         --  Create a vm on particular datacenter based on specs

    find_free_ide_controller()          --  Find the next free_ide_controller

    add_disks()                         --  Create disks for the VM with sizes specified

    add_scsi()                          --  Add SCSI controller for the VM

    add_cdrom()                         --  Adds CDROM to this VM with ISO pointed by iso_path

    add_nic()                           --  Adds NICs to this VM with network_name

    get_iso_path()                      --  Returns the ISO path from key

    use_new_installer()                 --  Returns True if the ISO uses the new ElectronJS installer

    is_3x()                             --  Returns True if 3.x ISO is used

    setup_vm()                          --  Create a vm from scratch without template

    hsx_fix_vdisk_creation_error()      --  Fix vdisk not found issue

    delete_bs_for_policy()              --  Deletes the backupset for the given policy

    kill_jobs_for_policy()              --  Kill jobs for the policy

    partition()                         --  Partition of sequence based on predicate output value

    delete_for_ma()                     --  Cleanup of ma from cs side

    cleanup_media_agents_from_cs()      --  Cluster cleanup

    install_fix_media()                 --  Installation of fix media specific for HS2.1

    hsx_ejs_installer_quit()            --  Exit from the new installer

    hsx_ejs_installer()                 --  HSX new installer network configs

    generate_storage_pool_name()        --  To create a storagepool_name

    track_cvmanager_task()              --  Tracks cvmanager task by polling it

    run_cluster_install_task()          --  Create storagepool from cvmanager

    cvmanager_add_node_task()           --  Add Node from cvmanager task

    get_snapshot_details()              --  Get snapshot details based on key

    does_snapshot_exist()               --  Check whether snapshot exist for a given vm

    create_snapshot()                   --  Creates snapshot for the VMs

    revert_snapshot()                   --  Reverts snapshot for the VMs

    cvmanager_validateCluster()         --  Validate preinstall for the Cluster

    cvmanager_validateCommServe()       --  Validate preinstall for the Commserve

    set_root_access_on_cluster()        --  Enable root login access for the Cluster

    start_hsx_setup()                   --  Abstraction of the entire hsx automation setup

    extract_and_send_repo_checksum()    --  Sends the checksum from eng filer to controller machine

    """

    def _get_esx(host, user, password) -> EsxManagement:
        """Utility method to instantiate the ESX object

            Args:

                host            (str)           --  The hostname of ESX server

                user            (str)           --  The username of the ESX server

                password        (str)           --  The password of the ESX server

            Returns:

                result          (EsxManagement) --  The EsxManagement object

        """
        vm_config = {
            'server_type': 'vCenter',
            'server_host_name': host,
            'username': user,
            'password': password
        }
        esx: EsxManagement = VmOperations.create_vmoperations_object(
            vm_config)
        atexit.register(connect.Disconnect, esx.si)
        return esx

    def _get_vm_io(host, user, password, esx, vm_name):
        """Utility method to instantiate the VmIo object

            Args:

                host            (str)           --  The hostname of ESX server

                user            (str)           --  The username of the ESX server

                password        (str)           --  The password of the ESX server

                esx             (EsxManagement) --  The EsxManagement object

                vm_name         (str)           --  The name of the VM in the ESX server

            Returns:

                result          (VmIo)          --  The VmIo object

        """
        vm_io = VmIo(vm_name, 'vCenter', host, user, password, esx)
        if vm_io._vm_obj:
            return vm_io
        raise Exception(
            f"Couldn't find the VM with name: {vm_name} under esx {host}")

    def _get_esx_vm_io(host, user, password, vm_name) -> Tuple[EsxManagement, EsxVmIo]:
        """Utility method to instantiate the ESX and VmIo object

            Args:

                host            (str)                   --  The hostname of ESX server

                user            (str)                   --  The username of the ESX server

                password        (str)                   --  The password of the ESX server

                vm_name         (str)                   --  The name of the VM in the ESX server

            Returns:

                result          (EsxManagement, VmIo)   --  The tuple (EsxManagement, VmIo)

        """
        esx = HyperscaleSetup._get_esx(host, user, password)
        vm_io = HyperscaleSetup._get_vm_io(host, user, password, esx, vm_name)
        return (esx, vm_io)

    @staticmethod
    def _get_log():
        """Utility method to get the logger object

            Returns:

                result          (Logger)   --  The Logger object

        """
        log = logger.get_log()
        return log

    def _search_for_obj(content, vim_type, name, folder=None, recurse=True):
        """Utility method to search the managed object for the name and type specified

            Sample Usage:
            _search_for_obj(content, [vim.Datastore], "Datastore Name")

            Args:

                content         (obj)       --  The content of ESX server

                vim_type        (list)      --  The list of datatypes to search

                name            (str)       --  The name of obj to search in ESX

                folder          (str)       --  The folder from where to search
                                                default will take root folder

                recurse         (bool)       --  Should search in subfolders or not

            Returns:

                result          (obj)       --  The searched object

        """
        if folder is None:
            folder = content.rootFolder

        obj = None
        container = content.viewManager.CreateContainerView(
            folder, vim_type, recurse)

        for managed_object_ref in container.view:
            if managed_object_ref.name == name:
                obj = managed_object_ref
                break
        container.Destroy()
        return obj

    def _get_hyperscale_default_creds():
        """Get the default Hyperscale credentials

            Returns:

                result      (str,str)   --  The username and passwrod

        """
        config = get_config()
        username = config.HyperScale.Credentials.User
        if not username or ' ' in username:
            raise Exception(
                "Please fill default username in Config->Hyperscale->Credentials->User")
        password = config.HyperScale.Credentials.Password
        if not password:
            raise Exception(
                "Please fill default password in Config->Hyperscale->Credentials->Password")
        return username, password
    
    def _get_hyperscale_scripts_path():
        """Get the Hyperscale scripts path

            Returns:

                result      (str)   --  The scripts path

        """
        config = get_config()
        path = config.HyperScale.VMConfig.ScriptsPath
        if not path:
            raise Exception(
                "Please fill scripts path in Config->Hyperscale->VMConfig->ScriptsPath")
        
        return path

    def _get_commcell(cs_host, cs_user, cs_password):
        """Get the Commcell object

            Args:

                cs_host         (str)       --  The hostname of CS

                cs_user         (str)       --  The username of the CS

                cs_password     (str)       --  The password of the CS


            Returns:

                result      (obj)   --  The commcell object

        """
        commcell = Commcell(cs_host, cs_user, cs_password, verify_ssl=False)
        return commcell

    def get_self_ip():
        """Utility method to get the IP of this controller

            Returns:

                result      (str)   --  The IP address

        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def get_vm_ip(vm_name, console: EsxConsole, matcher: ScreenMatcher):
        """Gets the IP address of the VM. It creates a server on this controller
            and then sends a packet from the VM to this server. Once the packet
            is received, the IP address is extracted from it and returned

            Args:

                vm_name     (str)   --  The name of the VM in the ESX server

                console     (obj)   --  The EsxConsole object

                matcher     (obj)   --  The ScreenMatcher object


            Returns:

                result      (str)   --  The IP address of the VM

        """
        log = HyperscaleSetup._get_log()
        local_ip = HyperscaleSetup.get_self_ip()
        local_port = 21052
        buffer_size = 1024

        udp_socket = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)
        udp_socket.bind((local_ip, local_port))

        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        console.send_command(def_username)
        console.send_command(def_password)
        tries = 0
        while True:
            tries += 1
            console.send_command("clear")
            console.send_command("dhclient ens192")
            time.sleep(60)
            result = matcher.wait_till_screen(
                ScreenMatcher.DHCLIENT_SCREEN_SUCCESS, attempts=1)
            if result:
                log.info(
                    f"Fired dhclient successfully after {tries} tries on {vm_name}")
                break
            if tries >= 5:
                log.error(
                    f"Unable to fire dhclient successfully even after {tries} tries")
                udp_socket.close()
                return False
        # don't know why but the IP address received is sometimes wrong
        time.sleep(60)
        # console.send_command('systemctl restart network')
        time.sleep(60)
        console.send_command(f"echo -n 'msg' | nc -u {local_ip} {local_port}")

        msg, address = udp_socket.recvfrom(buffer_size)
        udp_socket.close()
        log.info(f"vm: {vm_name} msg: {msg}, address: {address}")
        return address[0]

    def find_device(vm, device_type):
        """Finds a particular device_type for a VM

            Args:

                vm          (obj)  -- VM object

                device_type (type) -- The type of device to search

            Returns:

                result      (list) -- List of devices
        """
        result = []
        for dev in vm.config.hardware.device:
            if isinstance(dev, device_type):
                result.append(dev)
        return result

    def vm_set_boot_from_cd(vm):
        """Sets the boot from CD option

            Args:

                vm          (obj)  -- VM object

            Returns:

                None
        """
        log = HyperscaleSetup._get_log()
        log.info(f"Now setting boot from CD on {vm.config.name}")
        vmconf = vim.vm.ConfigSpec()
        vmconf.bootOptions = vim.vm.BootOptions(
            bootOrder=[vim.vm.BootOptions.BootableCdromDevice()])
        WaitForTask(vm.ReconfigVM_Task(vmconf))
        log.info(
            f"Successfully configured to boot from CD on {vm.config.name}")

    def clone_vm(host=None, user=None, password=None, vm_name=None, template_name=None, esx_name=None):
        """Clones the template into a VM

            Args:

                host            (str)   --  The hostname of ESX server

                user            (str)   --  The username of the ESX server

                password        (str)   --  The password of the ESX server

                vm_name         (str)   --  The name of the VM in the ESX server

                template_name   (str)   --  The name of the template to be cloned

                esx_name        (str)   -- The compute resource in which the VM will be cloned

            Returns:

                result          (bool, reason)   --  success and failure reason, if any

        """
        esx = HyperscaleSetup._get_esx(host, user, password)
        log = HyperscaleSetup._get_log()

        vm_exists_already = esx.get_vm_object(vm_name)
        if vm_exists_already:
            reason = f"Couldn't clone as the vm_name already exists"
            log.error(reason)
            return False, reason

        vm_template = esx.get_vm_object(template_name)
        if not vm_template:
            reason = f"Couldn't find the template {template_name}"
            log.error(reason)
            return False, reason

        cluster = HyperscaleSetup._search_for_obj(esx.si.RetrieveContent(), [
            vim.ComputeResource], esx_name)
        if not cluster:
            reason = f"Couldn't find cluster {esx_name}"
            log.error(reason)
            return False, reason
        log.info(f"Cluster obj {cluster} for {esx_name}")

        datastore = vm_template.datastore[0]
        assert (isinstance(datastore, vim.Datastore))
        log.info(
            f"{template_name} present in datastore: {datastore.name}")

        datacenter = datastore
        log.info(f"Finding datacenter from datastore: {datastore.name}")
        while not isinstance(datacenter, vim.Datacenter):
            datacenter = datacenter.parent
        assert (isinstance(datacenter, vim.Datacenter))
        log.info(
            f"{template_name} present in datacenter: {datacenter.name}")

        dest_folder = datacenter.vmFolder
        log.info(f"Vm folder: {dest_folder}({dest_folder.name})")

        relospec = vim.vm.RelocateSpec()
        relospec.datastore = datastore
        relospec.pool = cluster.resourcePool

        clonespec = vim.vm.CloneSpec()
        clonespec.location = relospec
        clonespec.powerOn = False

        log.info(f"Cloning VM {vm_name}")
        start_time = time.time()
        task = vm_template.Clone(
            folder=dest_folder, name=vm_name, spec=clonespec)
        WaitForTask(task)
        dur = int(round(time.time() - start_time))
        log.info(f"Cloning finished in {dur} seconds")
        return True, None

    def _hs_install_vm_reboot(esx: EsxManagement, vm, vm_name, setup_cdrom=True):
        """Reboots the VM, optionally can set the boot from CD option

            Args:

                esx             (obj)           --  The EsxManagement object

                vm              (obj)           --  The VM object

                vm_name         (str)           --  The name of the VM in the ESX server

                setup_cdrom     (str)           --  Whether to boot from CD or not

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()

        result = esx.vm_power_control_with_retry_attempts(vm_name, 'off')
        if not result:
            reason = f"Failed to power off {vm_name}"
            log.error(reason)
            return False, reason
        time.sleep(2)

        if setup_cdrom:
            esx.vm_set_cd_rom_enabled(vm_name, True, vm)
            HyperscaleSetup.vm_set_boot_from_cd(vm)

        result = esx.vm_power_control_with_retry_attempts(vm_name, 'on')
        if not result:
            reason = f"Failed to power on {vm_name}"
            log.error(reason)
            return False, reason
        time.sleep(6)
        return True, None

    def _hs_install_boot_screen_press_enter(vm_io: VmIo, matcher: ScreenMatcher):
        """Navigates the BOOT_SCREEN_PRESS_ENTER screen

            Args:

                vm_io           (obj)           --  The VmIo object

                matcher         (obj)           --  The ScreenMatcher object

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()

        result = matcher.wait_till_screen(
            ScreenMatcher.BOOT_SCREEN_PRESS_ENTER, attempts=5, interval=1)
        if not result:
            log.warning(
                "We might have missed pressing enter and the setup is already started. Continuing...")
        else:
            log.info(f"Pressing enter to continue boot.")
            vm_io.send_key('enter')
        time.sleep(25)
        return True, None

    def _hs_install_reimage_screen_initial_preserve(vm_io: VmIo, matcher: ScreenMatcher, is_hsx3: bool):
        """Navigates the REIMAGE_SCREEN_INITIAL screen

            Args:

                vm_io           (obj)           --  The VmIo object

                matcher         (obj)           --  The ScreenMatcher object

                is_hsx3         (bool)          --  True if hsx3, false if not

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()

        result = matcher.wait_till_screen(
            ScreenMatcher.REIMAGE_SCREEN_INITIAL, attempts=None)
        if not result:
            reason = f"Error waiting for REIMAGE_SCREEN_INITIAL"
            log.error(reason)
            return False, reason
        log.info(
            f"Navigating from REIMAGE_SCREEN_INITIAL to next screen...")
        vm_io.send_down_arrow()
        vm_io.send_down_arrow()  # adding this to be safe
        vm_io.send_down_arrow()  # adding this for hsx
        vm_io.send_key('space')

        result = matcher.wait_till_screen(
            ScreenMatcher.REIMAGE_SCREEN_PRESERVE)
        if not result:
            reason = f"Error waiting for REIMAGE_SCREEN_PRESERVE"
            log.error(reason)
            return False, reason
        log.info(
            f"Navigating from REIMAGE_SCREEN_PRESERVE to next screen...")
        # reinitialize drives
        vm_io.send_down_arrow()
        vm_io.send_key('space')
        # next or goes to text prompt
        vm_io.send_down_arrow()
        if is_hsx3:
            # hsx3 text prompt
            vm_io.send_text('Erase data and reuse server')
        # on ssd this goes to 'next' option for Drives
        vm_io.send_down_arrow()

        # this is an accomodation for hsx2,3,ssd,non ssd
        # some may be noops
        vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')
        return True, None
    
    def _hs_install_screen_initial_hsx(vm_io: VmIo, matcher: ScreenMatcher, is_datastore_ssd: bool):
        """Navigates the INSTALL_SCREEN_INITIAL screen

            Args:

                vm_io           (obj)           --  The VmIo object

                matcher         (obj)           --  The ScreenMatcher object

                is_datastore_ssd (bool)         --  True if vm is on ssd datastore
                                                    false if on disk

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()

        vm_io.send_down_arrow()
        vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')
        log.info(
            f"Navigating from INSTALL_SCREEN_INITIAL to next screen...")

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_SYSTEM_DRIVE)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_SYSTEM_DRIVE"
            log.error(reason)
            return False, reason
        vm_io.send_key('space')  # select first drive
        
        # accomodates both 2.x and 3.x
        for _ in range(9):
            vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')
        log.info(
            f"Navigating from INSTALL_SCREEN_SYSTEM_DRIVE to next screen...")
        # difference is from here, on non-ssd click two metadata and go to next
        # on ssd, uncheck all except first two
        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_METADATA_DRIVE_HSX)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_METADATA_DRIVE_HSX"
            log.error(reason)
            return False, reason

        if is_datastore_ssd:
            vm_io.send_down_arrow()
            vm_io.send_down_arrow()  # skip first two
            for _ in range(4):
                vm_io.send_key('space')  # deselect drive
                vm_io.send_down_arrow()  # goto next drive
            vm_io.send_key('space')  # Next
            for _ in range(2):
                vm_io.send_key('space')  # deselect drive
                vm_io.send_down_arrow()  # goto next drive
            vm_io.send_down_arrow()  # Next
            vm_io.send_key('space')
        else:    
            vm_io.send_key('space') # select first 2 drives
            vm_io.send_down_arrow()
            vm_io.send_key('space')
            vm_io.send_down_arrow()

            for _ in range(7):
                vm_io.send_down_arrow()
            vm_io.send_right_arrow()
            vm_io.send_key('space')

        log.info(
            f"Navigating from INSTALL_SCREEN_METADATA_DRIVE_HSX to next screen...")

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_DATA_DRIVE)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_DATA_DRIVE"
            log.error(reason)
            return False, reason
        for _ in range(6):
            vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')
        log.info(
            f"Navigating from INSTALL_SCREEN_DATA_DRIVE to next screen...")

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_SUMMARY_HSX)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_SUMMARY"
            log.error(reason)
            return False, reason
        vm_io.send_down_arrow()
        vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')
        log.info(
            f"Navigating from INSTALL_SCREEN_SUMMARY to next screen...")
        return True, None
    
    def _hs_install_screen_finished(vm_io: VmIo, matcher: ScreenMatcher):
        """Navigates the INSTALL_SCREEN_FINISHED screen

            Args:

                vm_io           (obj)           --  The VmIo object

                matcher         (obj)           --  The ScreenMatcher object

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_FINISHED, attempts=None)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_FINISHED"
            log.error(reason)
            return False, reason
        log.info(f"Navigating from INSTALL_SCREEN_FINISHED for reboot")
        vm_io.send_key('space')
        log.info(f"Waiting 2 mins for reboot")
        time.sleep(120)
        return True, None

    def _is_vm_datastore_ssd(vm):
        """Returns True if vm is on an SSD, false if not on SSD

            Args:

                vm              (obj)           --  The vm object

            Returns:

                result          (bool)          --  success and failure reason, if any

        """
        
        log = HyperscaleSetup._get_log()
        if vm.config.template:
            raise Exception(f"{vm.name} is a Template, not a VM")
        vmdatastore = vm.datastore[0]
        if vmdatastore.tag and 'SSD-Backed' in str(vmdatastore.tag):
            log.info("Using SSD Datastore")
            return True
        log.info("Using Disk Datastore")
        return False

    def start_hyperscale_install(host=None, user=None, password=None, vm_name=None, reimage=False):
        """1.5 ISO installation

            Args:

                host            (str)   --  The hostname of ESX server

                user            (str)   --  The username of the ESX server

                password        (str)   --  The password of the ESX server

                vm_name         (str)   --  The name of the VM in the ESX server

                reimage         (bool)   --  Whether to reimage or not

            Returns:

                result          (bool, reason)   --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()
        esx, vm_io = HyperscaleSetup._get_esx_vm_io(
            host, user, password, vm_name)
        vm = vm_io._vm_obj

        matcher = ScreenMatcher(vm_io)

        result, reason = HyperscaleSetup._hs_install_vm_reboot(
            esx, vm, vm_name)
        if not result:
            return False, reason

        result, reason = HyperscaleSetup._hs_install_boot_screen_press_enter(
            vm_io, matcher)
        if not result:
            return False, reason

        screen_keys = [ScreenMatcher.REIMAGE_SCREEN_INITIAL,
                       ScreenMatcher.INSTALL_SCREEN_INITIAL]
        result = matcher.wait_till_either_screen(screen_keys)
        if not result:
            raise Exception(
                f"Not able to figure out the screen from {screen_keys}")
        if result == ScreenMatcher.REIMAGE_SCREEN_INITIAL:
            result, reason = HyperscaleSetup._hs_install_reimage_screen_initial_preserve(
                vm_io, matcher)
            if not result:
                return False, reason

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_INITIAL)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_INITIAL"
            log.error(reason)
            return False, reason
        log.info(f"Pressing down x 4, space")
        for _ in range(4):
            vm_io.send_down_arrow()
        # go right? only if reimaging
        vm_io.send_right_arrow()
        vm_io.send_key('space')

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_SYSTEM_DRIVE)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_SYSTEM_DRIVE"
            log.error(reason)
            return False, reason
        log.info(f"Selecting 1st disk as OS disk")
        vm_io.send_key('space')
        for _ in range(4):
            vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_METADATA_DRIVE)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_METADATA_DRIVE"
            log.error(reason)
            return False, reason
        log.info(f"Selecting 3rd disk as DDB disk")
        for _ in range(2):
            vm_io.send_down_arrow()
        vm_io.send_key('space')
        vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_DATA_DRIVE)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_DATA_DRIVE"
            log.error(reason)
            return False, reason
        log.info(f"Selecting all disks as data drives")
        for _ in range(2):
            vm_io.send_down_arrow()
        vm_io.send_right_arrow()
        vm_io.send_key('space')

        result = matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_SUMMARY)
        if not result:
            reason = f"Error waiting for INSTALL_SCREEN_SUMMARY"
            log.error(reason)
            return False, reason
        log.info(f"Navigating from Summary screen")
        vm_io.send_down_arrow()
        vm_io.send_key('space')

        result, reason = HyperscaleSetup._hs_install_screen_finished(
            vm_io, matcher)
        if not result:
            return False, reason

        time.sleep(20)
        esx.vm_set_cd_rom_enabled(vm_name, False, vm)

        return True, None

    def basic_network_config(host=None, user=None, password=None, vm_names=None, vm_ips=None, cs_host=None,
                             cs_user=None, cs_password=None):
        """1.5 ISO basic network config

            Args:

                host            (str)       --  The hostname of ESX server

                user            (str)       --  The username of the ESX server

                password        (str)       --  The password of the ESX server

                vm_names        (list[str]) --  The list of VM names

                vm_ips          (list[str]) --  The list of VM IP addresses

                cs_host         (str)       --  The hostname of CS

                cs_user         (str)       --  The username of the CS

                cs_password     (str)       --  The password of the CS

            Returns:

                result          (bool, str) --  success and failure reason, if any

        """
        esx = HyperscaleSetup._get_esx(host, user, password)
        log = HyperscaleSetup._get_log()

        local_ips_hosts = "\n".join(
            [f"{i} {v}sds" for i, v in zip(vm_ips, vm_names)])

        public_ips = []
        for vm_name in vm_names:
            vm = esx.get_vm_object(vm_name)
            console: EsxConsole = EsxConsole(vm)
            vm_io = HyperscaleSetup._get_vm_io(
                host, user, password, esx, vm_name)
            matcher: ScreenMatcher = ScreenMatcher(vm_io)
            public_ip = HyperscaleSetup.get_vm_ip(vm_name, console, matcher)
            if not public_ip:
                vm_io.send_command(
                    "mv /etc/sysconfig/network-scripts/ifcfg-ens192 ~")
                vm_io.send_command(
                    "mv /var/lib/dhclient/dhclient--ens192.lease ~")
                vm_io.send_command("mv /var/lib/dhclient/dhclient.leases ~")
                vm_io.send_command("systemctl restart network")
                time.sleep(20)
                vm_io.send_command("dhclient -r")
                public_ip = HyperscaleSetup.get_vm_ip(
                    vm_name, console, matcher)
                vm_io.send_command(
                    "mv ~/ifcfg-ens192 /etc/sysconfig/network-scripts/ifcfg-ens192")
                if not public_ip:
                    raise Exception(
                        "Couldn't get DHCP ip even after the workaround")
            public_ips.append(public_ip)
        log.info(f"public_ips: {public_ips}")
        public_ips_hosts = "\n".join(
            [f"{ip} {name}" for ip, name in zip(public_ips, vm_names)])

        peers_variable = f"\n{public_ips_hosts}\n{local_ips_hosts}\n"

        scripts_path = HyperscaleSetup._get_hyperscale_scripts_path()
        local_path = Path(scripts_path)

        node_setup_path = local_path / 'node-setup.sh'
        log.info(f"node-setup exists: {node_setup_path.exists()}")

        with open(str(node_setup_path)) as f:
            content = f.read()
        content = re.sub(
            r"EOM.*?EOM", f"EOM{peers_variable}EOM", content, flags=re.DOTALL)
        with open(str(node_setup_path), 'w', newline='\n') as f:
            f.write(content.replace('\r', ''))

        ssh_files_paths = local_path.glob("*.sh")

        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        machine = UnixMachine(
            public_ips[0], username=def_username, password=def_password)
        for file in ssh_files_paths:
            machine.copy_from_local(str(file), "/root")

        machine.execute_command("chmod +x /root/*.sh")

        vm = esx.get_vm_object(vm_names[0])
        console = EsxConsole(vm)
        console.send_command(def_username)
        console.send_command(def_password)
        console.send_command("cd ~")
        vm_names_str = " ".join(vm_names)
        console.send_command(f"./node-setup-all.sh {vm_names_str}")

        commcell = HyperscaleSetup._get_commcell(cs_host, cs_user, cs_password)
        machine = Machine(commcell.commserv_name, commcell)
        for vm_host, vm_ip in zip(vm_names, public_ips):
            machine.add_host_file_entry(vm_host, vm_ip)

        # machine.execute_command("rm -rf ~/.ssh")

        time.sleep(60)
        return True, None

    def run_setupsds(host=None, user=None, password=None, vm_name=None, cs_host=None, cs_user=None, cs_password=None):
        """1.5 ISO running setupsds

            Args:

                host            (str)       --  The hostname of ESX server

                user            (str)       --  The username of the ESX server

                password        (str)       --  The password of the ESX server

                vm_name        (str)        --  The VM name

                cs_host         (str)       --  The hostname of CS

                cs_user         (str)       --  The username of the CS

                cs_password     (str)       --  The password of the CS

            Returns:

                result          (bool)      --  success

        """
        esx = HyperscaleSetup._get_esx(host, user, password)
        log = HyperscaleSetup._get_log()
        vm = esx.get_vm_object(vm_name)
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()

        interval = 5
        console = EsxConsole(vm)
        console.send_command(def_username)
        time.sleep(interval)
        console.send_command(def_password)
        time.sleep(interval)
        console.send_command('cd /opt/commvault/MediaAgent')
        console.send_command('clear')
        console.send_command('./setupsds')

        time.sleep(interval)
        log.info(f"Navigating SETUP_SCREEN_INITIAL")
        console.send_down_arrow()
        console.send_text(def_password)
        console.send_down_arrow()
        console.send_text(def_password)
        console.send_down_arrow()
        console.send_key('space')

        time.sleep(interval)
        log.info(f"Navigating from SETUP_SCREEN_NETWORK")
        console.send_right_arrow()
        console.send_key('space')

        time.sleep(interval)
        log.info(f"Navigating SETUP_SCREEN_CS_INFO")
        console.send_text(cs_host)
        console.send_down_arrow()
        console.send_text(cs_user)
        console.send_down_arrow()
        console.send_text(cs_password)
        console.send_down_arrow()
        console.send_key('space')

        time.sleep(30)
        return True

    def run_update(vm_hostnames=None, cs_host=None, cs_user=None, cs_password=None):
        """Update the nodes' CV software

            Args:

                vm_hostnames    (list[str]) --  The hostnames of the nodes

                cs_host         (str)       --  The hostname of CS

                cs_user         (str)       --  The username of the CS

                cs_password     (str)       --  The password of the CS

            Returns:

                result          (bool, str) --  success and failure reason, if any

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

        commcell = HyperscaleSetup._get_commcell(cs_host, cs_user, cs_password)
        log = HyperscaleSetup._get_log()
        hyperscale_helper = HyperScaleHelper(commcell, None, log)
        rc_node = hyperscale_helper.determine_remote_caches(vm_hostnames)
        if len(rc_node) == 1:
            rc_node = rc_node[0]
            rc_client = commcell.clients.get(rc_node)
            job_obj = rc_client.push_servicepack_and_hotfix()
            log.info(f"Update job for {job_obj} for {rc_node}")
            if not job_obj.wait_for_completion():
                reason = f"RC node job {job_obj.job_id} failed to complete"
                log.error(reason)
                return False, reason
        else:
            log.warning("RC node not found. This could be HS 1.5 cluster")
            rc_node = ''
        jobs = []
        for vm_name in vm_hostnames:
            if vm_name == rc_node:
                continue
            client = commcell.clients.get(vm_name)
            job_obj = client.push_servicepack_and_hotfix()
            log.info(f"Update job for {job_obj} for {vm_name}")
            jobs.append(job_obj)
            time.sleep(60)
        for job in jobs:
            if not job.wait_for_completion():
                return False, f"Job {job.job_id} failed to complete"
        return True, None

    def vm_change_cd_rom_iso(esx: EsxManagement, vm, vm_name, iso_key, iso_datastore, shutdown=False, iso_path=None):
        """Changes the ISO on VM, optionally shuts down the VM

            Args:

                esx             (obj)           --  The EsxManagement object

                vm              (obj)           --  The VM object

                vm_name         (str)           --  The name of the VM in the ESX server

                iso_key         (str)           --  The key for ISO to change to

                iso_datastore   (str)           --  The ESX datastore where the ISO resides

                shutdown        (bool)           --  Whether to shutdown the VM or not

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()

        if iso_path is None:
            iso_path = HyperscaleSetup.get_iso_path(iso_datastore, iso_key)

        if shutdown:
            result = esx.vm_power_control_with_retry_attempts(vm_name, 'off')
            if not result:
                reason = f"Failed to power off {vm_name}"
                log.error(reason)
                return False, reason
            time.sleep(2)

        cdroms = HyperscaleSetup.find_device(vm, vim.vm.device.VirtualCdrom)
        for cdrom in cdroms:
            backing = cdrom.backing
            datastore_name = backing.datastore.name
            old_path = backing.fileName
            backing.fileName = iso_path
            cdrom.connectable.startConnected = True
            cdrom.connectable.connected = True

            device_spec = vim.vm.device.VirtualDeviceSpec()
            device_spec.device = cdrom
            device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit

            config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
            WaitForTask(vm.Reconfigure(config_spec))
            log.info(f"CD-ROM path {old_path} -> {iso_path} for {vm_name}")

    def start_hyperscale_x_install(host=None, user=None, password=None, vm_name=None, iso_datastore=None,
                                   iso_key=None):
        """ISO installation for HSX

            Args:

                host            (str)       --  The hostname of ESX server

                user            (str)       --  The username of the ESX server

                password        (str)       --  The password of the ESX server

                vm_name         (str)       --  The VM name

                iso_datastore   (str)       --  The ESX datastore where the ISO resides

                iso_key         (str)       --  The key for ISO to change to

            Returns:

                result          (bool, str) --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()
        esx, vm_io = HyperscaleSetup._get_esx_vm_io(
            host, user, password, vm_name)
        vm = vm_io._vm_obj
        is_datastore_ssd = HyperscaleSetup._is_vm_datastore_ssd(vm)
        matcher = ScreenMatcher(vm_io)

        if iso_datastore and iso_key:
            HyperscaleSetup.vm_change_cd_rom_iso(
                esx, vm, vm_name, iso_key, iso_datastore, shutdown=True)

        is_hsx3 = HyperscaleSetup.is_3x(iso_key)

        result, reason = HyperscaleSetup._hs_install_vm_reboot(
                esx, vm, vm_name) 
        if not result:
            return False, reason

        result, reason = HyperscaleSetup._hs_install_boot_screen_press_enter(
            vm_io, matcher)
        if not result:
            return False, reason

        # 3 possible initial screens
        # 1) reimage screen, (reinit or preserve drives, additionally for 3x there is a text prompt)
        # 2) initial install screen (drive selections)
        # 3) in case of a smart config, it will directly skip to installation
        screen_keys = [ScreenMatcher.REIMAGE_SCREEN_INITIAL, ScreenMatcher.INSTALL_SCREEN_INITIAL_HSX,
                       ScreenMatcher.INSTALL_SCREEN_FINISHED]
        result = matcher.wait_till_either_screen(screen_keys, attempts=None)
        if not result:
            raise Exception(
                f"Not able to figure out the screen from {screen_keys}")
        if result == ScreenMatcher.REIMAGE_SCREEN_INITIAL:
            result, reason = HyperscaleSetup._hs_install_reimage_screen_initial_preserve(
                vm_io, matcher, is_hsx3)
            if not result:
                return False, reason
                
        screen_keys = [ScreenMatcher.INSTALL_SCREEN_INITIAL_HSX,
                       ScreenMatcher.INSTALL_SCREEN_FINISHED]
        result = matcher.wait_till_either_screen(screen_keys, attempts=None)
        if not result:
            raise Exception(
                f"Not able to figure out the screen from {screen_keys}")
        if result == ScreenMatcher.INSTALL_SCREEN_INITIAL_HSX:
            result, reason = HyperscaleSetup._hs_install_screen_initial_hsx(
                vm_io, matcher, is_datastore_ssd)
        if not result:
            return False, reason

        result, reason = HyperscaleSetup._hs_install_screen_finished(
            vm_io, matcher)
        if not result:
            return False, reason

        time.sleep(20)
        esx.vm_set_cd_rom_enabled(vm_name, False, vm)

        return True, None

    def hsx_login(vm_io: VmIo, vm_password=None):
        """Navigates the initial shell prompt banner screen

            Args:

                vm_io           (obj)           --  The VmIo object

                vm_password     (str)           --  The VM password

            Returns:

                None

        """
        username, password = HyperscaleSetup._get_hyperscale_default_creds()
        if vm_password:
            password = vm_password
        screen_matcher = ScreenMatcher(vm_io)
        screen_matcher.get_image_and_text('hsx_login_before_f2')
        vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
        time.sleep(20)
        screen_matcher.get_image_and_text('hsx_login_before_username')
        vm_io.send_command(username)
        time.sleep(10)
        screen_matcher.get_image_and_text('hsx_login_before_password')
        vm_io.send_command(password)
        time.sleep(10)
        screen_matcher.get_image_and_text('hsx_login_after_password')

    def hsx_bond_creation(esx, vm_name, dp_ip, dp_nm, gateway, dnss, dp_ifs, sp_ip, sp_nm, sp_ifs):
        """Performs bond creation for HSX

            Args:

                esx             (obj)           --  The EsxManagement object

                vm_name         (str)           --  The name of the VM in the ESX server

                dp_ip           (str)           --  The data protection IP of this node

                dp_nm           (str)           --  The data protection netmask of this node

                gateway         (str)           --  The gateway IP of this node

                dnss            ([str])         --  List of DNS IPs

                dp_ifs          ([str])         --  List of interfaces for data protection

                sp_ip           (str)           --  The storage pool IP of this node

                sp_nm           (str)           --  The storage pool netmask of this node

                sp_ifs          ([str])         --  List of interfaces for storage pool network

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()
        vm_io = HyperscaleSetup._get_vm_io(None, None, None, esx, vm_name)
        vm = esx.get_vm_object(vm_name)
        console = EsxConsole(vm)

        matcher = ScreenMatcher(vm_io)
        result = matcher.wait_till_either_screen(
            [ScreenMatcher.OS_LOGIN_SCREEN_HSX3,
             ScreenMatcher.OS_LOGIN_SCREEN], attempts = 20, interval=10)
        HyperscaleSetup.hsx_login(vm_io)

        console.send_command("cd /opt/commvault/MediaAgent")
        command = f"./cvnwlacpbond.py -c -m active-backup -t dp -i {dp_ip} -n {dp_nm} -g {gateway} -d {dnss[0]} {dnss[1]} -f {dp_ifs[0]} {dp_ifs[1]}"
        log.info(f"Now firing {command} for {vm_name}")
        console.send_command(command)
        time.sleep(120)
        vm_io.take_screenshot(f"{vm_name}-dp")

        command = f"./cvnwlacpbond.py -c -m active-backup -t sp -i {sp_ip} -n {sp_nm} -f {sp_ifs[0]} {sp_ifs[1]}"
        log.info(f"Now firing {command} on {vm_name}")
        console.send_command(command)
        time.sleep(120)
        vm_io.take_screenshot(f"{vm_name}-sp")
        return True, None

    def hsx_block_config(vm_names, block_name, vm_hostnames=[]):
        """Performs block configuration for HSX

            Args:

                vm_names        ([str])         --  The name of the VM in the ESX server

                block_name      (str)           --  The block name to use

                vm_hostnames    ([str])         --  The hostnames of the vm_names

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        block_ids = []
        if not vm_hostnames:
            vm_hostnames = vm_names
        for vm_name, vm_hostname in zip(vm_names, vm_hostnames):
            machine = Machine(
                vm_hostname, username=def_username, password=def_password)
            command = "dmidecode -t system | grep Serial | sed 's/ //g'"
            output = machine.execute_command(command)
            output = output.output.strip()
            id = output.split(':')[1]
            log.info(f"{vm_name} -> {id}")
            block_ids.append(id)

            command = "systemctl restart avahi-daemon.service"
            output = machine.execute_command(command)
            output = output.output.strip()
            log.info(f"{command} -> {output}")

        time.sleep(60)
        block_id_str = " ".join(block_ids)
        command = f"/opt/commvault/MediaAgent/cvavahi.py set_blkid {block_name} {block_id_str}"
        output = machine.execute_command(command)
        output = output.output.strip()
        log.info(f"{command} -> {output}")
        if "Could not locate avahi node with serial number" in output:
            raise Exception("Error while setting block id")
        return True, None

    def hsx_machine_setup(vm_hostnames, tz=None):
        """Copies the helper shell scripts

            Args:

                vm_hostnames    ([str])         --  The hostnames of the vm_names

                tz              (str)           --  The time zone to set

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """
        log = HyperscaleSetup._get_log()
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        local_path = Path(r'HyperScale/HyperScaleUtils/Scripts')

        node_setup_path = local_path / 'node-setup.sh'
        log.info(f"node-setup exists: {node_setup_path.exists()}")
        node_hsx_setup_path = local_path / 'node-hsx-setup.sh'
        with open(str(node_setup_path)) as f:
            content = f.read()
        
        content = re.sub(r".*# HSX.*?\n", f"", content, flags=re.DOTALL) # removing all network config commands for hsx in node-setup.sh
        if tz is not None:  # US/Eastern
            content = content.replace("Asia/Calcutta", tz)
        with open(str(node_hsx_setup_path), 'w', newline='\n') as f:    
            f.write(content.replace('\r', ''))

        ssh_access_path = local_path / 'ssh-access.sh'                  # replacing '<<DEFAULT_PASSWORD>>' with default password
        with open(str(ssh_access_path)) as f:
            content = f.read().replace('<<DEFAULT_PASSWORD>>', def_password)
        with open(str(ssh_access_path), 'w', newline='\n') as f:
            f.write(content)

        ssh_files_paths = list(local_path.glob("*.sh"))
        
        for vm_hostname in vm_hostnames:
            
            machine = UnixMachine(
                vm_hostname, username=def_username, password=def_password)
            for file in ssh_files_paths:
                machine.copy_from_local(str(file), "/root")

            machine.execute_command("chmod +x /root/*.sh")
            machine.execute_command("./node-hsx-setup.sh")
        
        return True, None

    def hsx_network_config(host, user, password, vm_names, sp_ips, dp_ips, gateway, dnss, dp_ifs, sp_ifs, dp_nm, sp_nm,
                           block_name, vm_hostnames=[], tz=None, iso_key=None):
        """Performs network configuration for HSX

            Args:

                host            (str)           --  The hostname of ESX server

                user            (str)           --  The username of the ESX server

                password        (str)           --  The password of the ESX server

                vm_names        ([str])         --  The names of the VMs in the ESX server

                sp_ips          ([str])         --  The storage pool IP of this cluster

                dp_ips          ([str])         --  The data protection IP of this cluster

                gateway         (str)           --  The gateway IP of this cluster

                dnss            ([str])         --  List of DNS IPs

                dp_ifs          ([str])         --  List of interfaces for data protection

                sp_ifs          ([str])         --  List of interfaces for storage pool network

                dp_nm           (str)           --  The data protection netmask of this cluster

                sp_nm           (str)           --  The storage pool netmask of this cluster

                block_name      (str)           --  The block name to use

                vm_hostnames    ([str])         --  The hostnames of the vm_names

                tz              (str)           --  The time zone to set

                iso_key         (str)           --  The key for ISO to change to

            Returns:

                result          (bool, reason)  --  success and failure reason, if any

        """

        esx = HyperscaleSetup._get_esx(host, user, password)
        log = HyperscaleSetup._get_log()

        threads = []
        for vm_name, dp_ip, sp_ip in zip(vm_names, dp_ips, sp_ips):
            def worker(vm_name, dp_ip, sp_ip):
                log.info(f"Configuring bonds for {vm_name}...")
                HyperscaleSetup.hsx_bond_creation(
                    esx, vm_name, dp_ip, dp_nm, gateway, dnss, dp_ifs, sp_ip, sp_nm, sp_ifs
                )
                log.info(f"Bonds for {vm_name} configured")
            thread = threading.Thread(target=worker, args=(vm_name, dp_ip, sp_ip))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        
        time.sleep(60)
        result, reason = HyperscaleSetup.hsx_machine_setup(vm_hostnames, tz=tz)
        if not result:
            log.error(f"HSX machine setup failed {reason}")
            return False, reason

        if HyperscaleSetup.use_new_installer(iso_key):
            for vm_name in vm_names:
                log.info(f"Now running new installer for {vm_name}")
                vm_io = HyperscaleSetup._get_vm_io(
                    host, user, password, esx, vm_name)
                HyperscaleSetup.hsx_ejs_installer(vm_io)
                log.info(f"Successfully ran installer for {vm_name}")
        else:
            result, reason = HyperscaleSetup.hsx_block_config(
                vm_names, block_name, vm_hostnames=vm_hostnames)
            if not result:
                log.error(f"Block config failed. {reason}")
                return False, reason

        return True, None

    def hsx_html_installer(vm_hostnames, cs_hostname, cs_user, cs_password):
        """HSX HTML installer

            Args:

                vm_hostnames    (list[str]) --  The hostnames of the nodes

                cs_hostname     (str)       --  The hostname of CS

                cs_user         (str)       --  The username of the CS

                cs_password     (str)       --  The password of the CS

            Returns:

                None

        """
        browser = BrowserFactory().create_browser_object()
        browser.open()
        browser.driver.implicitly_wait(60)
        driver = browser.driver
        log = HyperscaleSetup._get_log()

        def find_xpath(xpath, wait_till_displayed=True):
            """Finds the element from the xpath"""
            time.sleep(1)
            element = driver.find_element_by_xpath(xpath)
            while wait_till_displayed and not element.is_displayed():
                time.sleep(1)
            return element

        def send_to_xpath(xpath, text):
            """Sends the text to the given xpath"""
            element = find_xpath(xpath)
            element.send_keys(text)
            log.info(f"sent {text}")

        def click_xpath(xpath):
            """Clicks the xpath"""
            element = find_xpath(xpath)
            element.click()
            log.info(f"clicked {xpath}")

        def assert_text(xpath, text):
            """Verifies whether the text matches the xpath"""
            element = find_xpath(xpath)
            element_text = element.get_attribute('textContent')
            if element_text != text:
                raise Exception(
                    f"{text} doesn't match with elements's {element_text}")

        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()

        url = f"http://{vm_hostnames[0]}"
        log.info(f"url: {url}")

        driver.get(url)
        log.info(f"get url: {url}")

        xpath = '//*[@id="username"]'
        send_to_xpath(xpath, def_username)

        xpath = '//*[@id="password"]'
        send_to_xpath(xpath, def_password)

        xpath = '//*[@id="login_submit"]'
        click_xpath(xpath)

        time.sleep(10)

        xpath = '//*[@id="root_pwd"]'
        send_to_xpath(xpath, def_password)

        xpath = '//*[@id="root_confirm_pwd"]'
        send_to_xpath(xpath, def_password)

        xpath = '//*[@id="submit_step"]'
        click_xpath(xpath)

        time.sleep(40)

        log.info(f"testing for network information")
        xpath = '//*[@id="setupForm"]/div[2]/div[2]/h2'
        assert_text(xpath, "Provide Network information")

        xpath = '//*[@id="submit_step"]'
        click_xpath(xpath)

        xpath = '//*[@id="hostname"]'
        send_to_xpath(xpath, cs_hostname)

        xpath = '//*[@id="username"]'
        send_to_xpath(xpath, cs_user)

        xpath = '//*[@id="pwd"]'
        send_to_xpath(xpath, cs_password)

        xpath = '//*[@id="submit_step"]'
        click_xpath(xpath)
        log.info("clicked submit")

        time.sleep(20 * 60)
        log.info("Slept for 20 mins")

        xpath = '//*[@id="summary-dialog"]/div/div/div[1]/div[2]/div'
        text = 'HyperScale configuration completed successfully!'
        waiter = WebDriverWait(
            driver=driver, timeout=40 * 60, poll_frequency=3 * 60)
        waiter.until(lambda drv: drv.find_element_by_xpath(
            xpath).get_attribute('textContent') == text)

        # self.browser.driver.close()
        # self.browser.driver.quit()
        # input("waiting...")
        log.info("Looks like HTML installation was successful")

    def create_vm_config_spec(datastore_name, name, memory=24, guest="rhel7_64Guest",
                              cpus=8):
        """Creates the config spec for creating new VM
            default values correspond to HSX - if no template option

            Args:

                datastore_name  (str)   --  The ESX datastore where the VM is to be created

                name            (str)   --  The name of VM to create

                memory          (int)   --  The memory of VM in GB

                guest           (str)   --  The VM template

                cpus            (int)   --  The no. of virtual CPUs

            Returns:

                result          (obj)   --  ConfigSpec object

        """
        config = vim.vm.ConfigSpec()
        config.annotation = f"automation-{name}"
        config.memoryMB = int(memory * 1024)
        config.guestId = guest
        config.name = name
        config.numCPUs = cpus
        files = vim.vm.FileInfo()
        files.vmPathName = "[" + datastore_name + "]"
        config.files = files
        return config

    def create_vm(si, vm_name, datacenter_name, host_ip, datastore_name=None, cpus=None, memory=None):
        """Create a vm on particular datacenter based on specs

            Args:

                si              (obj)   --  ESX si object

                vm_name         (str)   --  The name of VM to create

                datacenter_name (str)   --  The datacenter where VM is to be created

                host_ip         (str)   --  The IP/FQDN of the datacenter

                datastore_name  (str)   --  The ESX datastore where the VM is to be created

                cpus            (int)   --  The no. of virtual CPUs

                memory          (int)   --  The memory of VM in GB

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        content = si.RetrieveContent()
        destination_host = HyperscaleSetup._search_for_obj(
            content, [vim.HostSystem], host_ip)
        source_pool = destination_host.parent.resourcePool
        if datastore_name is None:
            datastore_name = destination_host.datastore[0].name

        config = HyperscaleSetup.create_vm_config_spec(datastore_name=datastore_name, name=vm_name, cpus=cpus,
                                                       memory=memory)
        for child in content.rootFolder.childEntity:
            if child.name == datacenter_name:
                vm_folder = child.vmFolder  # child is a datacenter
                break
        else:
            log.error("Datacenter %s not found!" % datacenter_name)
            sys.exit(1)

        try:
            WaitForTask(vm_folder.CreateVm(
                config, pool=source_pool, host=destination_host))
            log.info("VM created: %s" % vm_name)
        except vim.fault.DuplicateName:
            log.error("VM duplicate name: %s" % vm_name, file=sys.stderr)
        except vim.fault.AlreadyExists:
            log.error("VM name %s already exists." % vm_name, file=sys.stderr)

    def find_free_ide_controller(vm):
        """Find the next free_ide_controller

            Args:

                vm      (obj)   --  VM object

            Returns:

                result  (obj)   --  IDE controller

        """
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualIDEController):
                # If there are less than 2 devices attached, we can use it.
                if len(dev.device) < 2:
                    return dev
        return None

    def add_disks(esx, vm, datastore, size_gbs=[]):
        """Create disks for the VM with sizes specified

            Args:

                esx         (EsxManagement) --  The EsxManagement object

                vm          (obj)           -- VM object

                datastore   (str)           --  The ESX datastore where the disks are to be created

                size_gbs    (list[int])     --  The list of disk sizes

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        unit_number = 0
        controller = None
        for device in vm.config.hardware.device:
            if hasattr(device.backing, 'fileName'):
                unit_number = int(device.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    raise Exception("we don't support this many disks")
            if isinstance(device, vim.vm.device.VirtualSCSIController):
                controller = device
        if controller is None:
            raise Exception("Disk SCSI controller not found!")
        # add disk here
        path_on_ds = f"[{datastore}] {vm.config.name}"
        content = esx.si.RetrieveContent()

        try:
            content.fileManager.MakeDirectory(path_on_ds)
        except vim.fault.FileAlreadyExists as e:
            pass

        datastore_obj = HyperscaleSetup._search_for_obj(
            content, [vim.Datastore], datastore)
        if not datastore_obj:
            raise Exception(f"Couldn't find {datastore}")

        dev_changes = []
        for i in range(len(size_gbs)):
            size_gb = size_gbs[i]

            new_disk_kb = int(size_gb) * 1024 * 1024
            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.fileOperation = "create"
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            disk_spec.device = vim.vm.device.VirtualDisk()
            disk_spec.device.backing = \
                vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
            disk_spec.device.backing.thinProvisioned = True
            disk_spec.device.backing.diskMode = 'persistent'

            if unit_number == 0:
                suffix = ''
            else:
                suffix = f'_{unit_number}'
            disk_spec.device.backing.fileName = f"[{datastore}] {vm.config.name}/{vm.config.name}{suffix}.vmdk"
            disk_spec.device.backing.datastore = datastore_obj

            disk_spec.device.unitNumber = unit_number
            disk_spec.device.capacityInKB = new_disk_kb
            disk_spec.device.controllerKey = controller.key
            disk_spec.device.key = unit_number
            dev_changes.append(disk_spec)
            log.info(f"{size_gb} GB disk request appended to {vm.config.name}")
            unit_number += 1
            if unit_number == 7:
                unit_number = 8
        spec.deviceChange = dev_changes
        task = vm.ReconfigVM_Task(spec=spec)
        WaitForTask(task)
        log.info(f"All {len(size_gbs)} disks added")

    def add_scsi(vm):
        """Add SCSI controller for the VM

            Args:

                vm              (obj)           --  The VM object

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        spec = vim.vm.ConfigSpec()
        dev_spec = vim.vm.device.VirtualDeviceSpec()
        dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        dev_spec.device = vim.vm.device.ParaVirtualSCSIController()
        dev_spec.device.busNumber = 0
        dev_spec.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
        spec.deviceChange = [dev_spec]
        task = vm.ReconfigVM_Task(spec=spec)
        WaitForTask(task)
        log.info(f"scsi controller added to {vm.config.name}")

    def add_cdrom(vm, iso_path):
        """Adds CDROM to this VM with ISO pointed by iso_path

            Args:

                vm              (obj)           --  The VM object

                iso_path        (str)           --  The ISO path

            Returns:

                None

        """
        controller = HyperscaleSetup.find_free_ide_controller(vm)
        backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso_path)

        connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        connectable.allowGuestControl = True
        connectable.startConnected = True  # so that I remember to tick mark the NICs
        connectable.connected = True  # no effect

        cdrom = vim.vm.device.VirtualCdrom()
        cdrom.controllerKey = controller.key
        cdrom.key = -1
        cdrom.connectable = connectable
        cdrom.backing = backing

        device_spec = vim.vm.device.VirtualDeviceSpec()
        device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        device_spec.device = cdrom

        config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
        task = vm.Reconfigure(config_spec)
        WaitForTask(task)

    def add_nic(esx, vm, network_name):
        """Adds NICs to this VM with network_name

            Args:

                esx             (obj)           --  The EsxManagement object

                vm              (obj)           --  The VM object

                network_name    (str)           --  The name of network to set for the NICs

            Returns:

                None

        """
        spec = vim.vm.ConfigSpec()
        nic_changes = []

        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

        nic_spec.device = vim.vm.device.VirtualVmxnet3()
        # nic_spec.device = vim.vm.device.VirtualE1000()

        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.summary = 'nic added via automation'

        content = esx.si.RetrieveContent()
        network = HyperscaleSetup._search_for_obj(
            content, [vim.Network], network_name)
        if isinstance(network, vim.OpaqueNetwork):
            nic_spec.device.backing = \
                vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
            nic_spec.device.backing.opaqueNetworkType = \
                network.summary.opaqueNetworkType
            nic_spec.device.backing.opaqueNetworkId = \
                network.summary.opaqueNetworkId
        else:
            nic_spec.device.backing = \
                vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.useAutoDetect = False
            nic_spec.device.backing.deviceName = network_name
            # nic_spec.device.backing.inPassthroughMode = True

        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True
        # nic_spec.device.connectable.connected = True
        # nic_spec.device.connectable.status = 'untried'
        nic_spec.device.wakeOnLanEnabled = True
        # nic_spec.device.addressType = 'assigned'

        nic_changes.append(nic_spec)
        spec.deviceChange = nic_changes
        task = vm.ReconfigVM_Task(spec=spec)
        WaitForTask(task)
        print("NIC CARD ADDED")

    def get_iso_path(datastore, iso, prefix="ISO"):
        """Returns the ISO path from key

            Args:

                datastore   (str)   --  The datastore for the path

                iso         (str)   --  The ISO key

                prefix      (str)   --  The prefix for the path

            Returns:

                result      (str)   --  ISO path

        """
        iso_name_mapping = {
            '1.5': 'hsrefdvd_1.5.1.iso',
            '2.1': 'dvd_12122020_124341.iso',
            '2.2': 'dvd_08072021_132913.iso',
            '2.3': 'dvd_10072022_113351.iso',
            '2.2212': 'dvd_12162022_081946.iso',
            '3.2312': 'dvd_12122023_204828.iso',
            '3.2408': 'dvd_09092024_015417.iso',
            'fixmedia': 'HSHotfixMedia-2.1.iso',
            'test': 'dvd_11282022_053415.iso'
        }
        if iso not in iso_name_mapping:
            raise Exception("Wrong key")
        return f"[{datastore}] {prefix}/{iso_name_mapping[iso]}"

    def use_new_installer(iso_key):
        """Returns True if the ISO uses the new ElectronJS installer

            Args:

                iso_key     (str)   --  The key for ISO to change to

            Returns:

                result      (bool)  --  If ISO uses new installer or not

        """
        if iso_key == "2.3" or re.match("[23][.][0-9]{4}", iso_key):
            return True
        return False
    
    def is_3x(iso_key):
        """Returns True if 3.x ISO is used

            Args:

                iso_key     (str)   --  The key for ISO

            Returns:

                result      (bool)  --  If ISO is for 3.x or not

        """
        if re.match("3[.][0-9]{4}", iso_key):
            return True
        return False

    def setup_vm(host=None, user=None, password=None, vm_names=None, datacenter_name=None, host_ip=None,
                 vm_datastore=None, iso_datastore=None, iso_ver=None, iso_path=None, network_name=None):
        """Create a vm from scratch without template

            Args:

                host            (str)       --  The hostname of ESX server

                user            (str)       --  The username of the ESX server

                password        (str)       --  The password of the ESX server

                vm_names        (list[str]) --  The list of VM names

                datacenter_name (str)       --  The datacenter where VM is to be created

                host_ip         (str)       --  The IP/FQDN of the datacenter

                vm_datastore    (str)       --  The ESX datastore where the VM is to be created

                iso_datastore   (str)       --  The ESX datastore where the ISO exists

                iso_ver         (str)       --  The key for ISO to change to

                iso_path        (str)       --  The ISO path

                network_name    (str)       --  The name of network to set for the NICs

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        esx = HyperscaleSetup._get_esx(host, user, password)
        if iso_path is None:
            iso_path = HyperscaleSetup.get_iso_path(iso_datastore, iso_ver)

        if "1.5.1" in iso_path:
            disks = [40, 50, 50, 100]
            nics_count = 2
            cpus = 4
            memory = 8
        else:
            disks = [100, 120, 120] + [128] * 6
            nics_count = 4
            cpus = 8
            memory = 24

        for vm_name in vm_names:
            log.info(f"{vm_name} creation in progress")
            HyperscaleSetup.create_vm(esx.si, vm_name=vm_name, datacenter_name=datacenter_name, host_ip=host_ip,
                                      datastore_name=vm_datastore, cpus=cpus, memory=memory)
            vm = esx.get_vm_object(vm_name)
            HyperscaleSetup.add_scsi(vm)
            HyperscaleSetup.add_disks(esx, vm, vm_datastore, disks)
            HyperscaleSetup.add_cdrom(vm, iso_path)

            for i in range(nics_count):
                if isinstance(network_name, str):
                    net_name = network_name
                elif isinstance(network_name, list):
                    net_name = network_name[i]
                else:
                    raise Exception(f"Invalid network name: {network_name}")

                log.info(f"adding nic {i}")
                HyperscaleSetup.add_nic(esx, vm, net_name)
            log.info(f"{vm_name} successfully created")
            time.sleep(10)

    def hsx_fix_vdisk_creation_error(vm_hostnames=None, cs_host=None, cs_user=None, cs_password=None):
        """Fix vdisk not found issue

            Args:

                vm_hostnames    (list[str]) --  The hostnames of the nodes

                cs_host         (str)       --  The hostname of CS

                cs_user         (str)       --  The username of the CS

                cs_password     (str)       --  The password of the CS

            Returns:

                None

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

        log = HyperscaleSetup._get_log()
        commcell = HyperscaleSetup._get_commcell(cs_host, cs_user, cs_password)
        machines = [Machine(hostname, commcell) for hostname in vm_hostnames]
        hyperscale_helper = HyperScaleHelper(commcell, None, log)
        machine_cluster_name_outputs = []
        for machine in machines:
            output = hyperscale_helper.get_hedvig_cluster_name(machine)
            if output:
                machine_cluster_name_outputs.append((machine, output))
        len_outputs = len(machine_cluster_name_outputs)
        if len_outputs == len(vm_hostnames):
            log.info("Nothing to be done to fix vdisk creation error")
            return
        if len_outputs != 1:
            log.error("Unknown error")
            return
        machine, cluster_name = machine_cluster_name_outputs[0]
        log.info(f"Proceeding to fix the error on {machine.machine_name}")
        env_prefix = f"HV_CLUSTER_NAME={cluster_name} HV_PUBKEY=1"
        command = f"{env_prefix} /usr/local/hedvig/scripts/collect_state.pl --backup"
        output = machine.execute_command(command)
        log.info(output.output)
        command = f"{env_prefix} HV_PREMADE=0 /usr/local/hedvig/scripts/update_cluster_status_wrap.pl"
        output = machine.execute_command(command)
        log.info(output.output)

    def delete_bs_for_policy(commcell, csdb_obj, policy_id, policy_name, skip_sc_deletion=False):
        """Deletes the backupset for the given policy

            Args:

                commcell            (obj)   --  The Commcell object

                csdb_obj            (obj)   --  The CSDB object

                policy_id           (str)   --  The policy id

                policy_name         (str)   --  The policy name

                skip_sc_deletion    (str)   --  Whether to delete the subclient or not

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()

        query = f'''
        select cl.name, app.subclientName, bs.name, agent.displayName
        from APP_Application app inner join APP_Client cl on app.clientId=cl.id inner join APP_BackupSetName bs on app.backupSet=bs.id inner join APP_iDAType agent on app.appTypeId=agent.type
        where app.dataArchGrpID={policy_id}
        '''
        csdb_obj.execute(query)
        result = csdb_obj.fetch_one_row()
        log.info(result)
        if not result or not result[0]:
            log.info(f"no backupset found for {policy_name}")

            policy_obj = commcell.storage_policies.get(policy_name)
            log.info(f"reassociating all subclients for {policy_name}...")
            policy_obj.reassociate_all_subclients()
            log.info(f"reassociated all subclients for {policy_name}")

            return
        cl, sc, bs, ag = result
        agent = commcell.clients.get(cl).agents.get(ag)
        backupset = agent.backupsets.get(bs)
        if backupset.name.lower() != 'defaultbackupset':
            agent.backupsets.delete(bs)
            log.info(f"deleted backupset {backupset.name}.")

        policy_obj = commcell.storage_policies.get(policy_name)
        log.info(f"reassociating all subclients for {policy_name}...")
        policy_obj.reassociate_all_subclients()
        log.info(f"reassociated all subclients for {policy_name}")

        if not agent.backupsets.has_backupset(bs):
            log.info("returning as backupset is deleted")
            return

        if sc in ["DDBBackup", "default"]:
            return

        if skip_sc_deletion:
            log.info(f"Not deleting {sc}. Returning")
            return

        backupset.subclients.delete(sc)
        log.info("deleted subclient")

    def kill_jobs_for_policy(commcell, csdb_obj, policy_id, policy_name):
        """Kill jobs for the policy

            Args:

                commcell            (obj)   --  The Commcell object

                csdb_obj            (obj)   --  The CSDB object

                policy_id           (str)   --  The policy id

                policy_name         (str)   --  The policy name

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()

        query = f'''
        select jobId from JMBkpJobInfo where currentPolicy={policy_id}
        '''
        csdb_obj.execute(query)
        result_jobs = csdb_obj.fetch_all_rows()
        if not result_jobs or not result_jobs[0] or not result_jobs[0][0]:
            log.info(f"no jobs running for {policy_name}")
            return
        log.info(f"Jobs running for {policy_name}")
        for [job_id] in result_jobs:
            jm = JobManager(job_id, commcell)
            jm.modify_job('kill')
            log.info(f"Killed job {job_id}")

    def partition(pred, iterable):
        """Partition of sequence based on predicate output value

            Args:

                pred        (func)          --  The predicate that partitions

                iterable    (list)          --  The list to partition

            Returns:

                result      (list, list)    --  The true and false lists respectively

        """
        trues = []
        falses = []
        for item in iterable:
            if pred(item):
                trues.append(item)
            else:
                falses.append(item)
        return trues, falses

    def delete_for_ma(commcell, csdb_obj, ma_name, skip_sc_deletion=False):
        """Cleanup of ma from cs side

            Args:

                commcell            (obj)   --  The Commcell object

                csdb_obj            (obj)   --  The CSDB object

                ma_name             (str)   --  The name of the Media Agent

                skip_sc_deletion    (str)   --  Whether to delete the subclient or not

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()

        ma_id = commcell.clients[ma_name.lower()]['id']
        query = f'''
        select 
            distinct(ag.id), 
            ag.name, 
            sign((ag.flags&256)|(ag.flags&8388608)) isGDSP,
            sign(ag.flags&536870912) isPlan
        from archGroup ag inner join archGroupCopy agc on ag.id = agc.archGroupId
        where agc.id in (select CopyId
        from MMDataPath
        where HostClientId={ma_id})
        '''
        csdb_obj.execute(query)
        result_policy = csdb_obj.fetch_all_rows()
        if not result_policy or not result_policy[0] or not result_policy[0][0]:
            log.info(f"nothing to be done for {ma_name}")
            return

        plans, _ = HyperscaleSetup.partition(
            lambda p: int(p[3]), result_policy)

        for plan in plans:
            id, name = plan[:2]
            plan_policy = commcell.storage_policies.get(name)

            log.info(f"reassociating all subclients for {name}...")
            plan_policy.reassociate_all_subclients()
            log.info(f"reassociated all subclients for {name}")

            plan_obj = commcell.plans.get(name)
            if plan_obj._associated_entities:
                plan_obj.edit_association(plan_obj._associated_entities)

            log.info(f"deleting plan: {name}")
            commcell.plans.delete(name)
            log.info(f"deleted plan: {name}")

        pools, policies = HyperscaleSetup.partition(
            lambda p: int(p[2]), result_policy)
        
        for pool in pools:
            id, name = pool[:2]
            policy = commcell.storage_policies.get(name)
            policy.seal_ddb("Primary")

        for policy in policies:
            id, name = policy[:2]
            HyperscaleSetup.kill_jobs_for_policy(commcell, csdb_obj, id, name)
            HyperscaleSetup.delete_bs_for_policy(
                commcell, csdb_obj, id, name, skip_sc_deletion)
            commcell.storage_policies.delete(name)
            log.info(f"deleted {name}")

        for pool in pools:
            id, name = pool[:2]
            commcell.storage_pools.delete(name)
            if commcell.client_groups.has_clientgroup(name):
                commcell.client_groups.delete(name)
            log.info(f"deleted {name}")
    
    def  cleanup_media_agents_from_cs(cs_host=None, cs_user=None, cs_password=None, ma_list=None, skip_ma_deletion=False,
                                     skip_sc_deletion=False):
        """Cluster cleanup

            Args:

                cs_host             (str)       --  The hostname of CS

                cs_user             (str)       --  The username of the CS

                cs_password         (str)       --  The password of the CS

                ma_list             ([str])     --  The list of Media Agents to remove

                skip_ma_deletion    (str)   --  Whether to delete the Media Agent or not

                skip_sc_deletion    (str)   --  Whether to delete the subclient or not

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()

        commcell = HyperscaleSetup._get_commcell(cs_host, cs_user, cs_password)
        csdb_obj = CommServDatabase(commcell)

        for client_name in ma_list:
            log.info(f"{client_name}:")
            if not commcell.clients.has_client(client_name):
                log.info("skipping")
                continue

            HyperscaleSetup.delete_for_ma(
                commcell, csdb_obj, client_name, skip_sc_deletion)

            if skip_ma_deletion:
                continue

            log.info(f"deleting ma {client_name}...")
            try:
                commcell.media_agents.delete(client_name, force=True)
                log.info(f"ma deleted {client_name}")
            except SDKException as e:
                if "No Mediaagent exists with name: " in str(e):
                    log.info(f"Media agent {client_name} already deleted")
                else:
                    raise

            client = commcell.clients.get(client_name)
            log.info(client.consumed_licenses)
            if False and "sp29" in cs_host:
                job = client.retire()
                job.wait_for_completion()
            else:
                client.release_license()
                log.info(f"license released {client_name}")

                commcell.clients.delete(client_name)
                log.info(f"{client_name} deleted")
    
    def  metallic_cleanup_media_agents_from_cs(cs_host=None, cvautoexec_user=None, cvautoexec_password=None, tenant_admin=None, tenant_password=None, ma_list=None, skip_ma_deletion=False,
                                     skip_sc_deletion=False):
        """Cluster cleanup

            Args:

                cs_host             (str)       --  The hostname of CS

                cvautoexec_user             (str)       --  The username of the CS cvautoexec user

                cvautoexec_password         (str)       --  The password of the CS cvautoexec user

                tenant_admin_user           (str)       --  The username of the tenant admin user

                tenant_admin_password       (str)       --  The password of the tenant admin user

                ma_list             ([str])     --  The list of Media Agents to remove

                skip_ma_deletion    (str)   --  Whether to delete the Media Agent or not

                skip_sc_deletion    (str)   --  Whether to delete the subclient or not

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()

        cvautoexec_commcell = HyperscaleSetup._get_commcell(cs_host, cvautoexec_user, cvautoexec_password)
        csdb_obj = CommServDatabase(cvautoexec_commcell)

        tenant_commcell = HyperscaleSetup._get_commcell(cs_host, tenant_admin, tenant_password)

        for client_name in ma_list:
            log.info(f"{client_name}:")
            if not tenant_commcell.clients.has_client(client_name):
                log.info("skipping")
                continue

            HyperscaleSetup.delete_for_ma(
                tenant_commcell, csdb_obj, client_name, skip_sc_deletion)

            if skip_ma_deletion:
                continue

            log.info(f"deleting ma {client_name}...")
            try:
                tenant_commcell.media_agents.delete(client_name, force=True)
                log.info(f"ma deleted {client_name}")
            except SDKException as e:
                if "No Mediaagent exists with name: " in str(e):
                    log.info(f"Media agent {client_name} already deleted")
                else:
                    raise

            client = tenant_commcell.clients.get(client_name)
            log.info(client.consumed_licenses)
            if False and "sp29" in cs_host:
                job = client.retire()
                job.wait_for_completion()
            else:
                client.release_license()
                log.info(f"license released {client_name}")

                tenant_commcell.clients.delete(client_name)
                log.info(f"{client_name} deleted")

    def install_fix_media(host, user, password, vm_names, iso_datastore):
        """Installation of fix media specific for HS2.1

            Args:

                host            (str)       --  The hostname of ESX server

                user            (str)       --  The username of the ESX server

                password        (str)       --  The password of the ESX server

                vm_names        (list[str]) --  The list of VM names

                iso_datastore   (str)       --  The ESX datastore where the ISO exists

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        esx = HyperscaleSetup._get_esx(host, user, password)
        vm_ios = []
        for vm_name in vm_names:
            vm_io: EsxVmIo = HyperscaleSetup._get_vm_io(
                host, user, password, esx, vm_name)
            vm_ios.append(vm_io)
            vm = vm_io._vm_obj
            HyperscaleSetup.hsx_login(vm_io)
            vm_io.send_command("eject cdrom")
            HyperscaleSetup.vm_change_cd_rom_iso(
                esx, vm, vm_name, 'fixmedia', iso_datastore)

            vm_io.send_command("mkdir /UpdateMediaFolder")
            vm_io.send_command("mount /dev/sr0 /UpdateMediaFolder")
            vm_io.send_command("cd /UpdateMediaFolder")
            log.info(f"Triggered hotfix media install for {vm_name}")
            vm_io.send_command("./HSHotfixMediaInstall")

        log.info("waiting for fixmedia installation to complete...")
        time.sleep(10 * 60)

        for vm_io in vm_ios:
            vm_io.send_command('y')

        log.info("waiting for reboot...")
        time.sleep(3 * 60)
        log.info("fixmedia installation done")

    def hsx_ejs_installer_quit(vm_io: EsxVmIo):
        """Exit from the new installer

            Args:

                vm_io           (obj)           --  The VmIo object

            Returns:

                None

        """
        vm_io.send_key("LEFTALT")
        vm_io.send_key("SPACE")
        vm_io.send_key("TAB")
        vm_io.send_key("TAB")
        vm_io.send_key("SPACE")

    def hsx_ejs_installer(vm_io: EsxVmIo, exit_after_nw_config=True):
        """HSX new installer network configs

            Args:

                vm_io                   (obj)   --  The VmIo object

                exit_after_nw_config    (bool)  --  Whether to exit after network

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        log.info(f"Logging in the HSX machine: {vm_io.vm_name}")
        HyperscaleSetup.hsx_login(vm_io)
        vm_io.send_command("hsxsetup")
        log.info(f"Launched hsxsetup: {vm_io.vm_name}")

        matcher = ScreenMatcher(vm_io)

        screen_keys = [ScreenMatcher.HSX_INSTALLER_SCREEN_VERSION_2212,
                       ScreenMatcher.HSX_INSTALLER_SCREEN_VERSION_3_2312,
                       ScreenMatcher.HSX_INSTALLER_SCREEN_VERSION_3_2408,
                       ScreenMatcher.HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION]
        result = matcher.wait_till_either_screen(screen_keys)
        if not result:
            raise Exception(
                f"Not able to figure out the screen from {screen_keys}")
        if result != ScreenMatcher.HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION:
            vm_io.send_key('TAB')
            vm_io.send_key('SPACE')

        result = matcher.wait_till_screen(
            ScreenMatcher.HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION, attempts=20)
        if not result:
            raise Exception(
                "Error waiting for HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION")

        vm_io.send_key('TAB')
        vm_io.send_keys(['MOD_LSHIFT', 'TAB'])
        vm_io.send_key('SPACE')

        result = matcher.wait_till_screen(
            ScreenMatcher.HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION_SUMMARY, attempts=30)
        if not result:
            raise Exception(
                "Error waiting for HSX_INSTALLER_SCREEN_NETWORK_CONFIGURATION_SUMMARY")

        vm_io.send_key('TAB')
        vm_io.send_key('TAB')
        vm_io.send_key('SPACE')

        if exit_after_nw_config:
            vm_io.send_key('TAB')
            vm_io.send_key('SPACE')
            return
        vm_io.send_key('TAB')
        vm_io.send_key('TAB')
        vm_io.send_key('SPACE')

    def generate_storage_pool_name(nodes):
        """To create a storagepool_name

            Args:

                nodes           ([str]) --  The cluster nodes

            Returns:

                result          (str)   --  The storage pool name generated

        """

        def get_same_chars_count(string_list):
            """Returns the size of common prefix"""
            same_chars = 0
            for chars in list(zip(*string_list)):
                if all([c == chars[0] for c in chars]):
                    same_chars += 1
                else:
                    break
            return same_chars

        nodes = [re.sub('[-]', '', node) for node in nodes]
        same_chars_end = get_same_chars_count([node[::-1] for node in nodes])
        nodes_end_removed = [node[:-1 * same_chars_end] for node in nodes]

        same_chars_begin = get_same_chars_count(nodes_end_removed)
        prefix = nodes_end_removed[0][:same_chars_begin]
        leftover = "".join([n[same_chars_begin:] for n in nodes_end_removed])
        pool_name = f"{prefix}{leftover}Pool"
        return pool_name

    class InstallTaskYaml(yaml.YAMLObject):
        """Generate yaml object for install task"""
        yaml_tag = "!Task"

        def __init__(self, cluster_nodes, cs_hostname, cs_username, cs_password, cvbackupadmin_password=None, os_password=None,
                     storage_pool_name=None, timezone=None):
            if os_password is None:
                os_password = cs_password

            if storage_pool_name is None:
                storage_pool_name = HyperscaleSetup.generate_storage_pool_name(
                    cluster_nodes)

            if timezone is None:
                timezone = "Asia/Kolkata"

            if cvbackupadmin_password is None:
                cvbackupadmin_password = cs_password

            self.kwargs = {
                "cluster_nodes": cluster_nodes,
                "cs_registration": {
                    "registration_cs": cs_hostname,
                    "registration_password": cs_password,
                    "registration_username": cs_username
                },
                "cvbackupadmin_password":cvbackupadmin_password,
                "os_password": os_password,
                "storagepool_name": storage_pool_name,
                "timezone": timezone
            }
            self.type = 'Install'

    def run_cluster_install_task(host=None, user=None, password=None, cs_host=None, cs_user=None, cs_password=None,
                                 vm_names=None, vm_hostnames=None, storage_pool_name=None, cvbackupadmin_password=None):
        """Create storagepool from cvmanager

            Args:

                host                (str)       --  The hostname of ESX server

                user                (str)       --  The username of the ESX server

                password            (str)       --  The password of the ESX server

                cs_host             (str)       --  The hostname of CS

                cs_user             (str)       --  The username of the CS

                cs_password         (str)       --  The password of the CS

                vm_names            (list[str]) --  The list of VM names

                vm_hostnames        (list[str]) --  The hostnames of the nodes

                storage_pool_name   (str)       --  The name of the storage pool

            Returns:

                result              (bool)      --  Whether successful or not

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
        
        log = HyperscaleSetup._get_log()

        if vm_hostnames is None:
            vm_hostnames = vm_names

        yaml_file_name = "automation_install_task.yml"
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        machine = UnixMachine(
            vm_hostnames[0], username=def_username, password=def_password)
        install_task_obj = HyperscaleSetup.InstallTaskYaml(
            vm_hostnames, cs_host, cs_user, cs_password, cvbackupadmin_password, storage_pool_name=storage_pool_name)
        task_yaml = yaml.dump({"tasks": [install_task_obj]})
        machine.create_file(f'{task_manager_dir}/{yaml_file_name}', task_yaml)

        esx, vm_io = HyperscaleSetup._get_esx_vm_io(
            host, user, password, vm_names[0])
        HyperscaleSetup.hsx_login(vm_io)
        vm_io.send_command(f"cd {task_manager_dir}")
        vm_io.send_command(f"./cvmanager.py {yaml_file_name}")
        time.sleep(60)

        task_name = install_task_obj.type
        commcell = HyperscaleSetup._get_commcell(cs_host, cs_user, cs_password)
        hyperscale_helper = HyperScaleHelper(commcell, None, log)
        if not hyperscale_helper.track_cvmanager_task(machine, cs_password, task_name, max_time_mins=4*60+15):
            return False
        return True

    def get_snapshot_details(key):
        """Get snapshot details based on key

            Args:

                key         (str)       --  The ISO key

            Returns:

                result          [str, str] --  Name and description of snapshot

        """
        snapshot_mapping = {
            "1.5": ["HS 1.5.1", "Snapshot created just before CS registration"],
            "2.1": ["HSX 2.1", "Snapshot created just after fix media installation"],
            "2.2": ["HSX 2.2", "Snapshot created just before HTML installer"],
            "2.2212": ["HSX 2.2212", "Snapshot created just after hsxsetup -> don't proceed"],
            "3.2312": ["HSX 3.2312", "Snapshot created after network config -> don't proceed"],
            "3.2408": ["HSX 3.2408", "Snapshot created just after hsxsetup -> don't proceed"]
        }
        return snapshot_mapping[key]
    
    def does_snapshot_exist(vm_obj, snapshot_name, snapshot_description):
        """Checks if a snapshot with a certain name exists for a given VM
        If snapshot exists with specified details, ignore snapshot creation.

         Args:

                vm_obj                  (obj)       --  The vm object

                snapshot_name           (str)       --  Name of the snapshot

                snapshot_description    (str)       --  Description of the snapshot

        Returns:

                result                  (bool)      --  True if snapshot exists on VM
                                                        False if it doesnt

        """
        log = HyperscaleSetup._get_log()

        if not vm_obj.snapshot:
            log.info(f"VM has no snapshots")
            return False
        for snapshot in vm_obj.snapshot.rootSnapshotList:
            if snapshot.name == snapshot_name and snapshot.description == snapshot_description:
                log.info(f"Snapshot found")
                return True
        return False

    def create_snapshot(host=None, user=None, password=None, vm_names=None, snapshot_name=None,
                        snapshot_description=None, snapshot_key=None):
        """Creates snapshot for the VMs

            Args:

                host                    (str)       --  The hostname of ESX server

                user                    (str)       --  The username of the ESX server

                password                (str)       --  The password of the ESX server

                vm_names                ([str])     --  The VM names

                spanshot_name           (str)       --  The name of snapshot

                snapshot_description    (str)       --  The description for snapshot

                snapshot_key            (str)       --  The ISO key, if given name and description
                                                        are auto populated

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        esx = HyperscaleSetup._get_esx(host, user, password)

        if snapshot_key is not None:
            snapshot_name, snapshot_description = HyperscaleSetup.get_snapshot_details(
                snapshot_key)

        for vm_name in vm_names:
            vm_obj = esx.get_vm_object(vm_name)
            snapshot_exists = HyperscaleSetup.does_snapshot_exist(vm_obj, snapshot_name, snapshot_description)
            if snapshot_exists:
                log.info(f"Snapshot {snapshot_name} already exists for {vm_name}")  # skip snapshot creation if already exists
                continue

            esx.vm_power_control_with_retry_attempts(vm_name, 'off')

            if not esx.save_snapshot(vm_name, snapshot_name, snapshot_description):
                log.error(f"Failed to create snapshot for {vm_name}")
                continue
            log.info(f"Created snapshot for {vm_name}")

            esx.vm_power_control_with_retry_attempts(vm_name, 'on')

    def revert_snapshot(host=None, user=None, password=None, vm_names=None, snapshot_name=None, snapshot_key=None):
        """Reverts snapshot for the VMs

            Args:

                host                    (str)       --  The hostname of ESX server

                user                    (str)       --  The username of the ESX server

                password                (str)       --  The password of the ESX server

                vm_names                ([str])     --  The VM names

                spanshot_name           (str)       --  The name of snapshot

                snapshot_key            (str)       --  The ISO key, if given name is auto populated

            Returns:

                success, reason         (bool, str) --  Whether reverted or not and reason if any

        """
        log = HyperscaleSetup._get_log()
        esx = HyperscaleSetup._get_esx(host, user, password)

        if snapshot_key is not None:
            snapshot_name, _ = HyperscaleSetup.get_snapshot_details(
                snapshot_key)
        
        for vm_name in vm_names:
            try:
                esx.get_snapshot_object(vm_name, snapshot_name)
            except Exception as e:
                reason = f"Failed to get snapshot info for VM: {vm_name}, snapshot: {snapshot_name}"
                return False, reason
            log.info(f"VM {vm_name} has snapshot {snapshot_name}")

        for vm_name in vm_names:
            esx.vm_power_control_with_retry_attempts(vm_name, 'off')

            if not esx.revert_snapshot(vm_name, snapshot_name):
                reason = f"Failed to revert for {vm_name}"
                return False, reason
            log.info(f"Successfully reverted snapshot {snapshot_name} for VM {vm_name}")

            esx.vm_power_control_with_retry_attempts(vm_name, 'on')
        
        return True, None

    class ValidateYamlBase(yaml.YAMLObject):
        """Parent class for ValidateCommServeYaml and ValidateClusterYaml"""
        yaml_tag = "!Task"
        
        def __init__(self, list_of_imaged_nodes, cs_password, os_password=None, cvbackupadmin_password=None):
            
            if os_password is None:
                os_password = cs_password

            if cvbackupadmin_password is None:
                cvbackupadmin_password = os_password

            self.kwargs = {
                "cluster_nodes": list_of_imaged_nodes,
                "mgmt_nw": False,
                "os_password": os_password,
                "cvbackupadmin_password": cvbackupadmin_password
            }
            self.type = "ValidatePreInstall"

    class ValidateCommServeYaml(ValidateYamlBase):
        """Generate YAML Object for running ValidateCommServe (ValidatePreInstall) cvmanager task"""
        
        yaml_tag = "!Task"
        def __init__(self, list_of_imaged_nodes, cs_hostname, cs_username, 
                    cs_password, os_password=None, cvbackupadmin_password=None):
            super().__init__(list_of_imaged_nodes, cs_password, os_password, cvbackupadmin_password)
            
            self.kwargs["cs_registration"] = {
            "registration_cs": cs_hostname,
            "registration_password": cs_password,
            "registration_username": cs_username
            }
            self.type = "ValidatePreInstall"

    class ValidateClusterYaml(ValidateYamlBase):
        """Generate YAML Object for running ValidateCluster (ValidatePreInstall) cvmanager task"""

        yaml_tag = "!Task"

        def __init__(self, list_of_imaged_nodes, 
                    cs_password, os_password=None, cvbackupadmin_password=None, timezone=None, storage_pool_name=None):
            super().__init__(list_of_imaged_nodes, cs_password, os_password, cvbackupadmin_password)

            if storage_pool_name is None:
                storage_pool_name = HyperscaleSetup.generate_storage_pool_name(list_of_imaged_nodes)

            if timezone is None:
                timezone = "Asia/Kolkata"
                
            self.kwargs["storagepool_name"] = storage_pool_name
            self.kwargs["timezone"] = timezone
            self.type = "ValidatePreInstall"

    class MetallicValidateCommServeYaml(ValidateYamlBase):
        """Generate YAML Object for running ValidateCommServe (ValidatePreInstall) cvmanager task"""
        
        yaml_tag = "!Task"
        def __init__(self, list_of_imaged_nodes, backup_gateway_host, cs_username, 
                    cs_password, backup_gateway_port, os_password=None, cvbackupadmin_password=None):
            super().__init__(list_of_imaged_nodes, cs_password, os_password, cvbackupadmin_password)
            
            self.kwargs["cs_registration"] = {
            "backup_gateway_host": backup_gateway_host,
            "backup_gateway_port": backup_gateway_port,
            "registration_username": cs_username,
            "registration_password": cs_password
            }
            self.type = "ValidatePreInstall"
    
    class MetallicInstallTaskYaml(yaml.YAMLObject):
        """Generate yaml object for install task"""
        yaml_tag = "!Task"

        def __init__(self, cluster_nodes, backup_gateway_host, cs_username, cs_password, backup_gateway_port, cvbackupadmin_password=None, os_password=None,
                     storage_pool_name=None, timezone=None):
            if os_password is None:
                os_password = cs_password

            if storage_pool_name is None:
                storage_pool_name = HyperscaleSetup.generate_storage_pool_name(
                    cluster_nodes)

            if timezone is None:
                timezone = "Asia/Kolkata"

            if cvbackupadmin_password is None:
                cvbackupadmin_password = cs_password

            self.kwargs = {
                "cluster_nodes": cluster_nodes,
                "cs_registration": {
                    "backup_gateway_host": backup_gateway_host,
                    "backup_gateway_port": backup_gateway_port,
                    "registration_password": cs_password,
                    "registration_username": cs_username
                },
                "cvbackupadmin_password":cvbackupadmin_password,
                "os_password": os_password,
                "storagepool_name": storage_pool_name,
                "timezone": timezone
            }
            self.type = 'Install'
    
    def run_metallic_cluster_install_task(host=None, user=None, password=None, backup_gateway_host=None, cs_host=None, cs_user=None, cs_password=None,
                                 backup_gateway_port=None, vm_names=None, vm_hostnames=None, storage_pool_name=None, cvbackupadmin_password=None):
        """Create storagepool from cvmanager

            Args:

                host                (str)       --  The hostname of ESX server

                user                (str)       --  The username of the ESX server

                password            (str)       --  The password of the ESX server

                backup_gateway_host (str)       --  The hostname of CS

                cs_user             (str)       --  The username of the CS

                cs_password         (str)       --  The password of the CS

                backup_gateway_port (int)       --  The port number for the CS 

                vm_names            (list[str]) --  The list of VM names

                vm_hostnames        (list[str]) --  The hostnames of the nodes

                storage_pool_name   (str)       --  The name of the storage pool

            Returns:

                result              (bool)      --  Whether successful or not

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
        
        log = HyperscaleSetup._get_log()

        if vm_hostnames is None:
            vm_hostnames = vm_names

        yaml_file_name = "automation_install_task.yml"
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        machine = UnixMachine(
            vm_hostnames[0], username=def_username, password=def_password)
        install_task_obj = HyperscaleSetup.MetallicInstallTaskYaml(
            vm_hostnames, backup_gateway_host, cs_user, cs_password, backup_gateway_port, cvbackupadmin_password, storage_pool_name=storage_pool_name)
        task_yaml = yaml.dump({"tasks": [install_task_obj]})
        machine.create_file(f'{task_manager_dir}/{yaml_file_name}', task_yaml)

        esx, vm_io = HyperscaleSetup._get_esx_vm_io(
            host, user, password, vm_names[0])
        HyperscaleSetup.hsx_login(vm_io)
        vm_io.send_command(f"cd {task_manager_dir}")
        vm_io.send_command(f"./cvmanager.py {yaml_file_name}")
        time.sleep(60)

        task_name = install_task_obj.type
        commcell = Commcell(cs_host, cs_user, cs_password)
        hyperscale_helper = HyperScaleHelper(commcell, None, log)
        if not hyperscale_helper.track_cvmanager_task(machine, cs_password, task_name, 4*60+15):
            return False
        return True
 
    def cvmanager_validatePreInstall(server_host_name=None, server_user_name=None, server_password=None,
                                           host=None, user=None, password=None, vm_names=None,
                                           cs_hostname=None, cs_username=None, cs_password=None, preinstall_task_obj=None,
                                           yaml_filename=None,
                                           ):
        """Validate preinstall Tasks

        
            Args:

                server_host_name        (str)   --  The hostname of ESX server

                server_user_name        (str)   --  The username of the ESX server

                server_password         (str)   --  The password of the ESX server

                host                    (str)   --  The hostname of VM

                user                    (str)   --  The username to login to the VM

                password                (str)   --  The password of the VM

                vm_hostnames            (list)  --  Hostnames of Imaged Nodes to verify

                vm_names                (list)  --  List of vm names

                cs_hostname             (str)   --  The hostname of CS

                cs_username             (str)   --  The username of the CS

                cs_password             (str)   --  The password of the CS

                preinstall_task_obj     (obj)   --  Yaml Object of relevant task

                yaml_filename           (str)   --  Name for Yaml file

            Returns:

                Result                  (Bool)  --  Whether the task is executed successfull or not

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

        log = HyperscaleSetup._get_log()
        if user == None or password == None:
            user, password = HyperscaleSetup._get_hyperscale_default_creds()
        machine = UnixMachine(machine_name=host, username=user, password=password)
        task_manager_dir = "/opt/commvault/MediaAgent/task_manager"
        task_yaml = yaml.dump({"tasks":[preinstall_task_obj]})
        esx, vm_io = HyperscaleSetup._get_esx_vm_io(server_host_name, server_user_name, server_password,
                                                    vm_names[0])
        HyperscaleSetup.hsx_login(vm_io)    # may or may not be necessary
        machine.create_file(f'{task_manager_dir}/{yaml_filename}', task_yaml)

        log.info(f"Created yaml file at {task_manager_dir}/{yaml_filename}")
        commcell = HyperscaleSetup._get_commcell(cs_hostname, cs_username, cs_password)
        hyperscale_helper = HyperScaleHelper(commcell, None, log)
        vm_io.send_command(f"cd {task_manager_dir}")
        vm_io.send_command(f"./cvmanager.py {yaml_filename}")
        task_name = preinstall_task_obj.type
        if not hyperscale_helper.track_cvmanager_task(machine, cs_password, task_name, max_time_mins=40):
            return False
        return True
 
    def set_root_access_on_cluster(vm_names=None, vm_hostnames = None, cs_hostname=None, cs_username=None, cs_password=None,
                    storage_pool_name=None, root_access=None):
        """Set root login access for the Cluster

        
            Args:

                vm_hostnames            (list)  --  List of hostnames of nodes to enable root

                cs_hostname             (str)   --  Hostname of the CS

                cs_username             (str)   --  Username of the CS

                cs_password             (str)   --  Password of the CS

                storage_pool_name       (str)   --  Name of the storage Pool

                root_access             (bool)  --  To enable/disable root access


            Returns:

                Result                  (Bool)  --  Whether the task is executed successfull or not

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

        log = HyperscaleSetup._get_log()
        commcell = HyperscaleSetup._get_commcell(cs_hostname, cs_username, cs_password)
        hyperscale_helper = HyperScaleHelper(commcell, None, log)

        if not storage_pool_name:
            storage_pool_name = HyperscaleSetup.generate_storage_pool_name(vm_hostnames)
            log.info(f"Using Generated Storage Pool Name: {storage_pool_name}")
        for vm_hostname in vm_hostnames:
            log.info(f"Setting root on {vm_hostname}")
            result = hyperscale_helper.set_root_access(storage_pool_name, vm_hostname, root_access)
            if not result:
                log.error(f"Root not set on {vm_hostname}")
                return False
        return True
    
    def firewall_add_icmp_rule(host, user, password, vm_names, vm_hostnames, root_password):
        """Adds firewall rule to enable ICMP traffic

        
            Args:

                host                (str)       --  The hostname of ESX server

                user                (str)       --  The username of the ESX server

                password            (str)       --  The password of the ESX server

                vm_names            (list)      --  Names of the VMs as seen on ESX server

                vm_hostnames        (list)      --  Hostnames of the VMs 

                root_password       (str)       --  Password for root user


            Returns:

                Result                  (Bool)  --  Whether the task is executed successfull or not

        """
        log = HyperscaleSetup._get_log()
        esx = HyperscaleSetup._get_esx(host, user, password)
        def_username, def_password = HyperscaleSetup._get_hyperscale_default_creds()
        for i in range(len(vm_names)):
            try:
                vm_io = HyperscaleSetup._get_vm_io(host, user, password, esx, vm_names[i])
            except Exception as e:
                log.error(f"Unable to get vm_io on vm {vm_names[i]}")
                return False
            log.info(f"Got vm_io for vm {vm_names[i]}")

            HyperscaleSetup.hsx_login(vm_io, root_password)

            add_rich_rule = f'--add-rich-rule=\'rule family="ipv4" protocol value="icmp" accept\''
            
            vm_io.send_command(f"firewall-cmd  {add_rich_rule} --zone=block")
            vm_io.send_command(f"firewall-cmd  --permanent {add_rich_rule} --zone=block")
            vm_io.send_command(f"firewall-cmd  --reload")
            time.sleep(30)
            machine = UnixMachine(vm_hostnames[0], username=def_username, password=root_password)
            log.info(f"Machine Object created successfully")
        return True

    def start_hsx_setup(host, user, password, vm_names, add_node_names, vm_hostnames, add_node_hostnames, iso_key, iso_datastore,
                        sp_ips, dp_ips, gateway, dnss, dp_ifs, sp_ifs, dp_nm, sp_nm, block_name, cluster_name,
                        cs_host, cs_user, cs_password, cvbackupadmin_password, revert_snapshots=False, create_snapshots=True,
                        cleanup_from_cs=True):
        """The main function for creating any HSX setup

        
            Args:

                host                (str)       --  The hostname of ESX server

                user                (str)       --  The username of the ESX server

                password            (str)       --  The password of the ESX server

                vm_names            (list)      --  Names of the VMs as seen on ESX server to create cluster

                add_node_names      (list)      --  Names of the VMs as seen on ESX server that will be used for add node

                vm_hostnames        (list)      --  Hostnames of the VMs to create cluster

                add_node_hostnames  (list)      --  Hostnames of the VMs to that will be used for add node

                iso_key             (str)       --  The ISO key (e.g. "2.2212"). Refer get_iso_path for all keys

                iso_datastore       (str)       --  The name of the datastore where the ISO exists

                sp_ips              (list[str]) --  The storage pool IP addresses for the VMs
                
                dp_ips              (list[str]) --  The data protection IP addresses for the VMs

                gateway             (str)       --  The IP of the gateway server

                dnss                (list[str]) --  The list of DNS servers

                dp_ifs              (list[str]) --  The names of dp interfaces (e.g. ["enpsf1","enpsf3"])

                sp_ifs              (list[str]) --  The names of sp interfaces (e.g. ["enpsf2","enpsf4"])

                dp_nm               (str)       --  The dp netmask (e.g. "255.255.240.0")

                sp_nm               (str)       --  The sp netmask (e.g. "255.255.255.0")

                block_name          (str)       --  Block name used for legacy 2.N ISO (Deprecated)

                cluster_name        (str)       --  The name of the storage pool

                cs_host             (str)       --  The hostname of CS

                cs_user             (str)       --  The username of the CS

                cs_password         (str)       --  The password of the CS

                cvbackupadmin_password  (str)   --  Password for cvbackupadmin user for newer ISOs

                revert_snapshot     (bool)      --  Whether to skip network config by reverting to a snapshot

                create_snapshot     (bool)      --  Whether to create a snapshot after network phase

                cleanup_from_cs     (bool)      --  Whether to cleanup the MediaAgents from CS prior to new cluster creation


            Returns:

                Result                  (bool)  --  Whether the task executed successfully or not

        """
        log = HyperscaleSetup._get_log()
        if cleanup_from_cs:
            start_time = time.time()
            ma_list = vm_hostnames + add_node_hostnames
            HyperscaleSetup.cleanup_media_agents_from_cs(
                cs_host=cs_host,
                cs_user=cs_user,
                cs_password=cs_password,
                ma_list=ma_list, 
                skip_ma_deletion=False, 
                skip_sc_deletion=False
            )
            log.info(f"Took {round(time.time()-start_time)} seconds to cleanup from CS")

        if revert_snapshots:
            ma_names = vm_names + add_node_names
            result, reason = HyperscaleSetup.revert_snapshot(host, user, password, ma_names, snapshot_key=iso_key)
            if not result:
                log.error(f"Unable to revert snapshot: {reason}")
                return False
            log.info("Sleeping for 2 mins")
            time.sleep(8*60)
            

        log.info("Performing HyperscaleX install")
        
        task_threads = []
        if not revert_snapshots:
            start_time = time.time()
            ma_names = vm_names + add_node_names
            for vm_name in ma_names:
                args = (host, user, password, vm_name, iso_datastore, iso_key)
                t = threading.Thread(target=HyperscaleSetup.start_hyperscale_x_install, args=args)
                t.start()
                task_threads.append(t)
                # t.join() # debug (sequential install)
            for i,t in enumerate(task_threads):
                t.join()
                log.info(f"HyperscaleX install finished for {ma_names[i]}")
            log.info(f"Took {round(time.time()-start_time)} seconds to Install HSX on the nodes")

            log.info("Performing HSX Network Config")
            ma_hostnames = vm_hostnames + add_node_hostnames
            ma_names = vm_names + add_node_names
            start_time = time.time()
            args = (host, user, password, ma_names, sp_ips, dp_ips, gateway, dnss, dp_ifs, sp_ifs, dp_nm, sp_nm, block_name, ma_hostnames, None, iso_key)
            result, reason = HyperscaleSetup.hsx_network_config(*args)

            if not result:
                log.info(f"Network config failed. {reason}")
                return False
            log.info(f"HSX Network Config finished")
            log.info(f"Took {round(time.time()-start_time)} seconds to setup Network")
        if iso_key and "2.1" in iso_key:
            HyperscaleSetup.install_fix_media(
                host=host, 
                user=user, 
                password=password, 
                vm_names=vm_names,
                iso_datastore=iso_datastore
            )

        if create_snapshots:
            ma_names = vm_names + add_node_names
            HyperscaleSetup.create_snapshot(host, user, password, ma_names, snapshot_key=iso_key)
        
        log.info(f"Performing Pre Install Verifications")

        start_time = time.time()
        # validatePreInstallCommServe
        validate_cs_task_obj = HyperscaleSetup.ValidateCommServeYaml(vm_hostnames, cs_host, cs_user, cs_password)
        validate_cs_filename = "validate_cs_task.yml"
        args =(host, user, password, vm_hostnames[0], None, None, vm_names, cs_host, cs_user, cs_password, validate_cs_task_obj, validate_cs_filename)
        result = HyperscaleSetup.cvmanager_validatePreInstall(*args)
        if not result:
            log.info(f"Pre Install Verifications Failed (validatePreInstallCommServe)")
            return False
        log.info("Successfully ran validatePreInstallCommServe task")

        # validatePreInstallCluster
        validate_cluster_task_obj = HyperscaleSetup.ValidateClusterYaml(vm_hostnames, cs_password)
        validate_cluster_filename = "validate_cluster_task.yml"
        args =(host, user, password, vm_hostnames[0], None, None, vm_names, cs_host, cs_user, cs_password, validate_cluster_task_obj, validate_cluster_filename)
        result = HyperscaleSetup.cvmanager_validatePreInstall(*args)
        if not result:
            log.info(f"Pre Install Verifications Failed (validatePreInstallCluster)")
            return False
        log.info("Successfully ran validatePreInstallCluster task")

        log.info(f"Pre Install validations successful")
        log.info(f"Took {round(time.time()-start_time)} seconds to run Pre-Install Validations")

        log.info(f"Running Install Task")
        start_time = time.time()
        args =(host, user, password, cs_host, cs_user, cs_password, vm_names, vm_hostnames, cluster_name, cvbackupadmin_password)
        HyperscaleSetup.run_cluster_install_task(*args)
        log.info(f"Install Task finished successfully")
        log.info(f"Took {round(time.time()-start_time)} seconds to run Install Task")
        
        if int(iso_key[0]) >= 3: 

            time.sleep(5*60)
            log.info(f"Enabling root access on vms: {vm_names}")
            result = HyperscaleSetup.set_root_access_on_cluster(
                vm_names=vm_names, 
                vm_hostnames=vm_hostnames, 
                cs_hostname=cs_host, 
                cs_username=cs_user, 
                cs_password=cs_password,
                storage_pool_name=None, 
                root_access=True)
            if not result:
                log.error("Failed to enable root")
                return False
            log.info("Successfully enabled root access")

            time.sleep(5*60)

            # add firewall commands to let icmp traffic go through
            result = HyperscaleSetup.firewall_add_icmp_rule(
                host=host,
                user=user,
                password=password,
                vm_names=vm_names,
                vm_hostnames=vm_hostnames,
                root_password=cvbackupadmin_password)
            if not result:
                return False
            log.info("Successfully enabled ICMP traffic")
        
        if not (iso_key and "2.1" in iso_key):
            log.info("Performing update job")
            result, reason = HyperscaleSetup.run_update(vm_hostnames=vm_hostnames, cs_host=cs_host, cs_user=cs_user, cs_password=cs_password)
            if not result:
                log.error(f"Update failed job failed: {reason}")
                return False
            log.info(f"Successfully performed update")

        log.info("Running vdisk fix")
        HyperscaleSetup.hsx_fix_vdisk_creation_error(vm_hostnames=vm_hostnames, cs_host=cs_host, cs_user=cs_user, cs_password=cs_password)

        log.info("Hyperscale setup completed successfully")
        return True

    def metallic_start_hsx_setup(host, user, password, vm_names, add_node_names, vm_hostnames, add_node_hostnames, iso_key, iso_datastore,
                        sp_ips, dp_ips, gateway, dnss, dp_ifs, sp_ifs, dp_nm, sp_nm, block_name, 
                        cluster_name, cs_host, cvautoexec_user, cvautoexec_password, tenant_admin, tenant_password, backup_gateway_host, backup_gateway_port, cvbackupadmin_password, revert_snapshots=False, create_snapshots=True,
                        cleanup_from_cs=True):
        """The main function for creating any HSX setup

        
            Args:

                host                (str)       --  The hostname of ESX server

                user                (str)       --  The username of the ESX server

                password            (str)       --  The password of the ESX server

                vm_names            (list)      --  Names of the VMs as seen on ESX server to create cluster

                add_node_names      (list)      --  Names of the VMs as seen on ESX server that will be used for add node

                vm_hostnames        (list)      --  Hostnames of the VMs to create cluster

                add_node_hostnames  (list)      --  Hostnames of the VMs to that will be used for add node

                iso_key             (str)       --  The ISO key (e.g. "2.2212"). Refer get_iso_path for all keys

                iso_datastore       (str)       --  The name of the datastore where the ISO exists

                sp_ips              (list[str]) --  The storage pool IP addresses for the VMs
                
                dp_ips              (list[str]) --  The data protection IP addresses for the VMs

                gateway             (str)       --  The IP of the gateway server

                dnss                (list[str]) --  The list of DNS servers

                dp_ifs              (list[str]) --  The names of dp interfaces (e.g. ["enpsf1","enpsf3"])

                sp_ifs              (list[str]) --  The names of sp interfaces (e.g. ["enpsf2","enpsf4"])

                dp_nm               (str)       --  The dp netmask (e.g. "255.255.240.0")

                sp_nm               (str)       --  The sp netmask (e.g. "255.255.255.0")

                block_name          (str)       --  Block name used for legacy 2.N ISO (Deprecated)

                cluster_name        (str)       --  The name of the storage pool

                cs_host             (str)       --  The hostname of CS

                cs_user             (str)       --  The username of the CS

                cs_password         (str)       --  The password of the CS

                cvbackupadmin_password  (str)   --  Password for cvbackupadmin user for newer ISOs

                revert_snapshot     (bool)      --  Whether to skip network config by reverting to a snapshot

                create_snapshot     (bool)      --  Whether to create a snapshot after network phase

                cleanup_from_cs     (bool)      --  Whether to cleanup the MediaAgents from CS prior to new cluster creation


            Returns:

                Result                  (bool)  --  Whether the task executed successfully or not

        """
        log = HyperscaleSetup._get_log()
        if cleanup_from_cs:
            start_time = time.time()
            ma_list = vm_hostnames + add_node_hostnames
            HyperscaleSetup.metallic_cleanup_media_agents_from_cs(
                cs_host=cs_host,
                cvautoexec_user=cvautoexec_user,
                cvautoexec_password=cvautoexec_password,
                tenant_admin=tenant_admin,
                tenant_password=tenant_password,
                ma_list=ma_list, 
                skip_ma_deletion=False, 
                skip_sc_deletion=False
            )
            log.info(f"Took {round(time.time()-start_time)} seconds to cleanup from CS")

        if revert_snapshots:
            ma_names = vm_names + add_node_names 
            result, reason = HyperscaleSetup.revert_snapshot(host, user, password, ma_names, snapshot_key=iso_key)
            if not result:
                log.error(f"Unable to revert snapshot: {reason}")
                return False
            log.info("Sleeping for 6 mins")
            time.sleep(6*60)

        #Todo : to include if node is up functionality 

        log.info("Performing HyperscaleX install")
        
        task_threads = []
        if not revert_snapshots:
            start_time = time.time()
            ma_names = vm_names + add_node_names
            ma_hostnames = vm_hostnames + add_node_hostnames
            for vm_name in ma_names:
                args = (host, user, password, vm_name, iso_datastore, iso_key)
                t = threading.Thread(target=HyperscaleSetup.start_hyperscale_x_install, args=args)
                t.start()
                task_threads.append(t)
                # t.join() # debug (sequential install)
            for i,t in enumerate(task_threads):
                t.join()
                log.info(f"HyperscaleX install finished for {ma_names[i]}")
            log.info(f"Took {round(time.time()-start_time)} seconds to Install HSX on the nodes")

            log.info("Performing HSX Network Config")
            start_time = time.time()
            args = (host, user, password, ma_names, sp_ips, dp_ips, gateway, dnss, dp_ifs, sp_ifs, dp_nm, sp_nm, block_name, ma_hostnames, iso_datastore, iso_key)
            result, reason = HyperscaleSetup.hsx_network_config(*args)

            if not result:
                log.info(f"Network config failed. {reason}")
                return False
            log.info(f"HSX Network Config finished")
            log.info(f"Took {round(time.time()-start_time)} seconds to setup Network")
        if iso_key and "2.1" in iso_key:
            HyperscaleSetup.install_fix_media(
                host=host, 
                user=user, 
                password=password, 
                vm_names=vm_names,
                iso_datastore=iso_datastore
            )

        if create_snapshots:
            ma_names = vm_names + add_node_names
            HyperscaleSetup.create_snapshot(host, user, password, ma_names, snapshot_key=iso_key)
        
        log.info(f"Performing Pre Install Verifications")

        start_time = time.time()

        # validatePreInstallCommServe
        validate_cs_task_obj = HyperscaleSetup.MetallicValidateCommServeYaml(vm_hostnames, backup_gateway_host, tenant_admin, tenant_password, backup_gateway_port)
        validate_cs_filename = "validate_cs_task.yml"
        args =(host, user, password, vm_hostnames[0], None, None, vm_names, cs_host, tenant_admin, tenant_password, validate_cs_task_obj, validate_cs_filename)
        result = HyperscaleSetup.cvmanager_validatePreInstall(*args)
        if not result:
            log.info(f"Pre Install Verifications Failed (validatePreInstallCommServe)")
            return False
        log.info("Successfully ran validatePreInstallCommServe task")

        # validatePreInstallCluster
        validate_cluster_task_obj = HyperscaleSetup.ValidateClusterYaml(vm_hostnames, tenant_password)
        validate_cluster_filename = "validate_cluster_task.yml"
        args =(host, user, password, vm_hostnames[0], None, None, vm_names, cs_host, tenant_admin, tenant_password, validate_cluster_task_obj, validate_cluster_filename)
        result = HyperscaleSetup.cvmanager_validatePreInstall(*args)
        if not result:
            log.info(f"Pre Install Verifications Failed (validatePreInstallCluster)")
            return False
        log.info("Successfully ran validatePreInstallCluster task")

        log.info(f"Pre Install validations successful")
        log.info(f"Took {round(time.time()-start_time)} seconds to run Pre-Install Validations")

        # Running install task 
        log.info(f"Running Install Task")
        start_time = time.time()
        args =(host, user, password, backup_gateway_host, cs_host, tenant_admin, tenant_password, backup_gateway_port, vm_names, vm_hostnames, cluster_name, cvbackupadmin_password)
        HyperscaleSetup.run_metallic_cluster_install_task(*args)
        log.info(f"Install Task finished successfully")
        log.info(f"Took {round(time.time()-start_time)} seconds to run Install Task")

        if int(iso_key[0]) >= 3:
            time.sleep(5*60)
            log.info(f"Enabling root access on vms: {vm_names}")
            result = HyperscaleSetup.set_root_access_on_cluster(
                vm_names=vm_names, 
                vm_hostnames=vm_hostnames, 
                cs_hostname=cs_host, 
                cs_username=tenant_admin, 
                cs_password=tenant_password,
                storage_pool_name=None, 
                root_access=True)
            if not result:
                log.error("Failed to enable root")
                return False
            log.info("Successfully enabled root access")

            time.sleep(5*60)

            # add firewall commands to let icmp traffic go through
            result = HyperscaleSetup.firewall_add_icmp_rule(
                host=host,
                user=user,
                password=password,
                vm_names=vm_names,
                vm_hostnames=vm_hostnames,
                root_password=cvbackupadmin_password)
            if not result:
                return False
            log.info("Successfully enabled ICMP traffic")
            

        # add check to get check readiness here and if needed add retries 
        time.sleep(3*60)
    
        log.info("Running vdisk fix")
        HyperscaleSetup.hsx_fix_vdisk_creation_error(vm_hostnames=vm_hostnames, cs_host=cs_host, cs_user=tenant_admin, cs_password=tenant_password)

        log.info("Hyperscale setup completed successfully")
        return True
    
    def ensure_root_access(cs_hostname=None, cs_username=None, cs_password=None, commcell=None, node_hostnames=None, node_root_password=None):
        """This ensures that root is enabled on the node_hostnames

        
            Args:

                cs_hostname            (str)        --  The hostname of CS

                cs_username            (str)        --  The username of the CS

                cs_password             (str)       --  The password of the CS

                commcell                (obj)       --  If given, the above 3 arguments can be skipped

                node_hostnames          (list)      --  Hostnames of the nodes

                node_root_password      (str)       --  The root password for the nodes

            Returns:

                Result, reason          (bool,str)  --  Whether the root was enabled or not. 
                                                        If not, then a reason is returned

        """
        from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

        log = HyperscaleSetup._get_log()
        
        if commcell is None:
            commcell = HyperscaleSetup._get_commcell(cs_hostname, cs_username, cs_password)
        
        csdb = CommServDatabase(commcell)
        hyperscale_helper = HyperScaleHelper(commcell, csdb, log)
        storage_pool_name = hyperscale_helper.get_storage_pool_from_media_agents(node_hostnames)
        if not storage_pool_name:
            reason = "Either no storage pool exists or values are inconsistent"
            return False, reason
        
        for node_hostname in node_hostnames:
            machine = Machine(node_hostname, commcell)
            command = "grep 'PermitRootLogin yes' /etc/ssh/sshd_config"
            output = machine.execute_command(command)
            log.info(f"{command} -> {output.output} on {node_hostname}")
            
            if output.output:
                continue
            
            result = hyperscale_helper.set_root_access(storage_pool_name, node_hostname, True)
            if not result:
                return False, f"Failed to set_root_access on {node_hostname}"
        
        time.sleep(10)
        
        for node_hostname in node_hostnames:
            duration = 5*60
            interval = 1*60
            tries = int(ceil(duration / interval))
            for iteration in range(1, tries+1):
                log.info(f"Try {iteration}. Connecting via SSH to {node_hostname}")
                try:
                    ssh_client = paramiko.SSHClient()
                    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh_client.connect(node_hostname, username='root', password=node_root_password)
                    log.info(f"Successfully connected via SSH to {node_hostname}")
                    break
                except BadAuthenticationType as e:
                    log.info(f"Unable to connect. {e}")
                    if iteration == tries:
                        return False, f"Failed to connect using SSH to {node_hostname} after enabling root access even after {tries} tries."

        return True, None
                
            
    
  
    def extract_and_send_repo_checksum_7zip(eng_repodata_tar, zip_exe_path, destination_path):
        """Before running any platform upgrade automation case, we need to get the cv-hedvig repo RPM checksums from trusted eng filer
        and use those values for validation purposes in our untrusted controller. This method helps in bringing the needed info
        from eng to the controller and hence need to run prior

            Args:

                eng_repodata_tar            (str)        --  The path to repodata*.tar file in eng filer

                zip_exe_path            (str)        --  The binary used to manipulate tar and gz file. Mostly 7 zip

                destination_path             (str)       --  The path on the controller to copy the checksums

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        machine = Machine()
        is_mixed = 'mixed.tar' in eng_repodata_tar
        dest_dir = str(Path('.').resolve())
        if is_mixed:
            input_tar_file = eng_repodata_tar
        else:
            command = fr'&"{zip_exe_path}" e {eng_repodata_tar} -o{dest_dir} -aoa'
            output = machine.execute_command(command)
            log.info(output.output)
            log.info(output.exception)
            input_tar_file = 'repodata.tar'
        result = machine.execute_command(f'&"{zip_exe_path}" l {input_tar_file}')
        output = result.output
        
        lines = [l for l in output.split('\r\n')]
        lines_hedvig = list(filter(lambda x : 'cv-hedvig' in x and '-primary.xml' in x, lines))
        primary_gz_xml_file_paths = [l.rsplit(' ', 1)[-1] for l in lines_hedvig]
        log.info(primary_gz_xml_file_paths)
        for gz_xml_file in primary_gz_xml_file_paths:
            if is_mixed:
                repo_type = gz_xml_file.split("\\")[0]
            else:
                repo_type = Path(eng_repodata_tar).stem.split('_', 1)[-1]
            log.info(f"repo type: {repo_type}")
            dest_file_name = f"{repo_type}.csv"
            command = fr'&"{zip_exe_path}" e {input_tar_file} -o{dest_dir} -aoa {gz_xml_file}'
            log.info(command)
            output = machine.execute_command(command)
            log.info(output.output)
            log.info(output.exception)

            gz_file = Path(gz_xml_file).name
            command = fr'&"{zip_exe_path}" e {gz_file} -o{dest_dir} -aoa'
            log.info(command)
            output = machine.execute_command(command)
            log.info(output.output)
            log.info(output.exception)

            xml_file = Path(gz_xml_file).stem

            tree = etree.parse(xml_file)
        
            root = tree.getroot()
            checksum_values = [x.text for x in root.findall(".//checksum", root.nsmap)]
            rpm_names = [x.get('href').rsplit('/',1)[-1] for x in root.findall(".//location", root.nsmap)]
            with open(dest_file_name, 'w') as f:
                lines = [f"{name},{sha}" for name,sha in zip(rpm_names,checksum_values)]
                content = "\n".join(lines)
                log.info(content)
                f.write(content)
            Path(gz_file).unlink()
            Path(xml_file).unlink()
            machine.execute_command(f'cp {dest_file_name} {destination_path}')
        if eng_repodata_tar != input_tar_file:
            Path(input_tar_file).unlink()

    def extract_and_send_repo_checksum(eng_repodata_tar, destination_path):
        """Before running any platform upgrade automation case, we need to get the cv-hedvig repo RPM checksums from trusted eng filer
        and use those values for validation purposes in our untrusted controller. This method helps in bringing the needed info
        from eng to the controller and hence need to run prior

            Args:

                eng_repodata_tar            (str)        --  The path to repodata*.tar file in eng filer

                destination_path             (str)       --  The path on the controller to copy the checksums

            Returns:

                None

        """
        log = HyperscaleSetup._get_log()
        machine = Machine()
        is_mixed = 'mixed.tar' in eng_repodata_tar
        dest_dir = str(Path('.').resolve())
        if is_mixed:
            tar_mode = 'r'
        else:
            tar_mode = 'r:gz'
        tarfile_obj = tarfile.open(name=eng_repodata_tar, mode=tar_mode)
        xml_hedvig_infos = [tarfile_obj.getmember(l) for l in tarfile_obj.getnames() if "cv-hedvig" in l and "-primary.xml" in l]
        for info in xml_hedvig_infos:
            if is_mixed:
                repo_type = info.name.split("/")[0]
            else:
                repo_type = Path(eng_repodata_tar).stem.split('_', 1)[-1]
            log.info(f"repo type: {repo_type}")
            dest_file_name = f"{repo_type}.csv"
            info.name = Path(info.name).name # skip directories while extracting the file
            result = tarfile_obj.extractall(members=[info])
            gz_xml_file = gzip.open(info.name)
            content = gz_xml_file.read()

            root = etree.fromstring(content)
            checksum_values = [x.text for x in root.findall(".//checksum", root.nsmap)]
            rpm_names = [x.get('href').rsplit('/',1)[-1] for x in root.findall(".//location", root.nsmap)]
            with open(dest_file_name, 'w') as f:
                lines = [f"{name},{sha}" for name,sha in zip(rpm_names,checksum_values)]
                content = "\n".join(lines)
                log.info(content)
                f.write(content)
            gz_xml_file.close()
            Path(info.name).unlink()
            machine.execute_command(f'cp {dest_file_name} {destination_path}')

    def get_url_to_get_url():
        '''
        Reverse engineered this from cloud.commvault.com
        But the idea is to fire this API and it will redirect
        to the metadata.tar file link
        '''
        
        log = HyperscaleSetup._get_log()

        payload = {
            "id": 24179,
            "packageId": 24179,
            "guid": "",
            "platforms": [
                {
                    "id": 4,
                    "name": "Linux",
                    "pkgPlatformMapId": 74909,
                    "pkgRepository": {
                        "repositoryId": 2,
                        "serverType": 2
                    },
                    "downloadType": {
                        "name": "Native Installer"
                    }
                }
            ]
        }
        json_str = json.dumps(payload)
        encoded = urllib.parse.quote(json_str)
        url = f"https://cloud.commvault.com/webconsole/softwarestore/store-download-package.do?isStore=false&packageData={encoded}"
        log.info(f"Got URL: {url}")
        return url
    
    def get_url_to_download_metadata_tar(url):
        '''
        This GETs the url and returns the returned redirected url
        which is where the metadata.tar file is
        '''
        log = HyperscaleSetup._get_log()

        response = requests.get(url, allow_redirects=False)
        log.info(f"Response: {response}")
        redirected_url = response.headers.get('Location')
        log.info(f"Redirected URL: {redirected_url}")
        return redirected_url

    def download_large_file(url, destination):
        '''
        Primarily used to download 500 MB+ metadata.tar
        file from the cloud for offline upgrade case
        '''
        log = HyperscaleSetup._get_log()

        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        log.info("File downloaded successfully!")
    
    def ensure_tmux_installed(machine):
        '''
        This returns the path to tmux executable
        For 1.5, it first installs tmux
        '''
        log = HyperscaleSetup._get_log()

        command = 'commvault reg | grep "Commvault HyperScale 1.5.1"'
        result = machine.execute_command(command)
        is_151 = bool(result.output)

        if not is_151:
            # we will always find tmux here for hedvig case
            return "/usr/local/hedvig/scripts/tmux"
        
        command = 'rpm -qa | grep -i tmux'
        result = machine.execute_command(command)
        if result.output:
            return "tmux"
        
        # install tmux here
        log.info("Installing tmux...")
        tmux_rpm_file_name = "tmux-1.8-4.el7.x86_64.rpm"
        rpm_path = Path.cwd() / "HyperScale" / "HyperScaleUtils" / tmux_rpm_file_name
        machine.copy_from_local(str(rpm_path), "/root/")

        command = f'yum -y --disablerepo=* localinstall {tmux_rpm_file_name}'
        log.info(f"Now firing {command}")
        result = machine.execute_command(command)
        log.info(result.output)
        log.info(result.exception)
        log.info(result.exception_message)

        command = 'rpm -qa | grep -i tmux'
        result = machine.execute_command(command)
        if result.output:
            return "tmux"
        raise Exception(f"Failed to install tmux")

    
    def spawn_process_and_wait(machine: UnixMachine, input_command, send_yes=False, time_out_hrs=1, poll_interval_mins=2):
        """
        For 2.x and later we use tmux which is available under hedvig folder
        However for 1.x, since hedvig is not used, we don't have tmux, but we do have screen
        This code automatically spawns the process using the right multiplexer and waits for it to exit
        Sometimes you have to give a 'y' prompt after firing the command, which is handled as follows:
        screen: send 'y' at the time of sending the actual command
        tmux: send the 'y' and 'enter' key to the session afterwards
        """
        log = HyperscaleSetup._get_log()

        tmux_path = HyperscaleSetup.ensure_tmux_installed(machine)

        session_name = 'offline_upgrade'
        tmux_command = f'{tmux_path} new-session -d -s {session_name}'
        
        command = f"{tmux_command} '{input_command}'"
        investigate_command = f"{tmux_path} attach-session -t {session_name}"

        log.info(f"Now firing: {command}")

        result = machine.execute_command(command)
        log.info(result.output)
        log.info(result.exception)
        log.info(result.exception_message)

        if result.exception or result.exception_message:
            log.error("Encountered exception while spawning process")
            return False

        if send_yes:
            machine.execute_command(f"{tmux_path} send-keys 'y' 'Enter'")

        # TODO: when performing OS upgrade, the machine may reboot and the below line will throw an error - handle it
        result = machine.wait_for_process_to_exit(f"'{input_command}'", 
                                                  time_out=time_out_hrs*60*60, poll_interval=poll_interval_mins*60)
        if not result:
            log.error(f"The process is still running. Manually investigate by firing |{investigate_command}|")
            return False
        
        return True
        

    def create_upgrpms_file(cache_node, cache_username, cache_password):
        '''
        fires the get_list_of_rpms command after copying metadata.tar file
        '''
        log = HyperscaleSetup._get_log()

        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)

        get_rpms_command = '/opt/commvault/MediaAgent/cv_offline_upgrade.py get_list_of_rpms /root/metadata.tar'

        result = HyperscaleSetup.spawn_process_and_wait(cache_machine, get_rpms_command, time_out_hrs=1, poll_interval_mins=2)
        if not result:
            return False
        
        upgrpms_file_path = '/ws/ddb/upgos/upgrpms.xml'
        content = cache_machine.read_file(upgrpms_file_path)
        with open(Path(upgrpms_file_path).name, 'w', newline='\n') as f:
            f.write(content)
        lines_count = len(content.split("\n"))
        log.info(f"Successfully created upgrpms.xml file with {lines_count} lines")
        return True

    def generate_rpm_bundle(installer_path, log_file_path):
        '''
        Here installer_path is Setup.exe path after extracting
        Commvault_Media_11_32.exe

        The log_file_path is where this installer writes
        typically C:\ProgramData\C*\G*\L*\Install.log
        '''
        log = HyperscaleSetup._get_log()
        
        dest_path = Path('.').resolve()
        command = f'& "{installer_path}" /wait /s /installupdates /s /downloadunixospatches upgrpms.xml /outputpath "{dest_path}"'
        machine = Machine()
        with open(log_file_path, errors='ignore') as log_file:
            prevContent = log_file.read()
        # prevContent = prevContent[0:prevContent.rfind("Installation STARTED")-100]
        # TODO: could have rehydrator here to store the prevContent

        log.info(f"firing: {command}")
        result = machine.execute_command(command)
        log.info(result.output)
        log.info(result.exception)
        log.info(result.exception_message)
        
        duration = 2*60
        interval = 10
        tries = duration // interval
        pid = None
        log.info(f"Now trying to find the PID of the installer process from {log_file_path}")
        for i in range(1, tries+1):
            log.info(f"Try {i}")
            with open(log_file_path, errors='ignore') as log_file:
                content = log_file.read()
            content = content.replace(prevContent, '')
            match_obj = re.search(r"^(\d+).*?Installation STARTED", content, re.M)
            if match_obj:
                pid = int(match_obj[1])
                break
            time.sleep(interval)
        if pid is None:
            log.error(f"Couldn't find the pid. Refer {log_file_path}")
            return
        log.info(f"Pid found {pid}")
        proc = psutil.Process(pid)
        log.info(f"Process: {proc}")

        duration = 20*60
        final_time = time.time() + duration
        success = False
        log.info("Now waiting for process to finish")
        while time.time() < final_time:
            if not proc.is_running():
                success = True
                log.info("Process finished executing")
                break
            time.sleep(interval)
        if not success:
            log.error("Error waiting for process to finish")
            return
        return Path(dest_path) / Path('CVAppliance_Unix.tar')
    
    def install_rpm_bundle(cache_node, cache_username, cache_password, upgrade_flags, send_yes=False):
        '''
        fires the upgrade command after copying CVAppliance_Unix.tar file
        handles hedvig and OS variants with an optional yes too
        '''
        log = HyperscaleSetup._get_log()
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)

        install_rpms_command = '/opt/commvault/MediaAgent/cv_offline_upgrade.py upgrade /ws/ddb/CVAppliance_Unix.tar'

        result = HyperscaleSetup.spawn_process_and_wait(cache_machine, f"{install_rpms_command} {upgrade_flags}", send_yes=send_yes, time_out_hrs=2, poll_interval_mins=2)
        if not result:
            return False
        return True
    
    def cvoffline_main(installer_path, log_file_path, cache_node, cache_username, cache_password):
        '''
        This is the main function which needs to be run from fastpass-common machine

        Here installer_path is Setup.exe path after extracting
        Commvault_Media_11_32.exe

        The log_file_path is where this installer writes
        typically C:\ProgramData\C*\G*\L*\Install.log

        '''
        log = HyperscaleSetup._get_log()

        log.info(f"Starting offline upgrade procedure from {cache_node}")

        # 1. Download metadata.tar file from cloud
        store_url = HyperscaleSetup.get_url_to_get_url()
        file_url = HyperscaleSetup.get_url_to_download_metadata_tar(store_url)
        HyperscaleSetup.download_large_file(file_url, 'metadata.tar')
        log.info("Successfully downloaded metadata.tar file to the controller")

        # 2. Copy metadata.tar to the node
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)
        result = cache_machine.copy_from_local('metadata.tar', '/root/')
        if not result:
            log.error("Failed to copy metadata.tar")
            return
        log.info("Successfully copied metadata.tar file to the node")

        # 3. Run query and get RPM list
        result = HyperscaleSetup.create_upgrpms_file(cache_node, cache_username, cache_password)
        if not result:
            log.error("Failed to create upgrpms.xml file on the controller")
            return
        log.info("Successfully created upgrpms.xml file on the controller")

        # 4. Generate CVAppliance_Unix.tar file
        result = HyperscaleSetup.generate_rpm_bundle(installer_path, log_file_path)
        if not result:
            log.error("Failed to generate RPM bundle")
        log.info("Successfully generated RPM bundle")

        # 5. Copy CVAppliance_Unix.tar file back to the node
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)
        result = cache_machine.copy_from_local('CVAppliance_Unix.tar', '/ws/ddb')
        if not result:
            log.error("Failed to copy CVAppliance_Unix.tar")
            return
        log.info("Successfully copied CVAppliance_Unix.tar file to the node")

        # 6a. Log pre-upgrade hedvig-cluster RPM version
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)
        result = cache_machine.execute_command("rpm -qa | grep hedvig-cluster")
        log.info(f"Pre upgrade hedvig version: {result.output}")

        # 6b. Install hedvig RPMs
        result = HyperscaleSetup.install_rpm_bundle(cache_node, cache_username, cache_password, '-upgrade_hedvig_only')
        if not result:
            log.error("Failed to install RPM bundle -upgrade_hedvig_only")
            return
        log.info("Successfully installed RPM bundle -upgrade_hedvig_only")

        # 6c. Log post-upgrade hedvig-cluster RPM version
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)
        result = cache_machine.execute_command("rpm -qa | grep hedvig-cluster")
        log.info(f"Post upgrade hedvig version: {result.output}")

        # 7a. Log pre-upgrade kernel version
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)
        result = cache_machine.execute_command("uname -r")
        log.info(f"Pre upgrade kernel version: {result.output}")

        # 7b. Install OS RPMs
        result = HyperscaleSetup.install_rpm_bundle(cache_node, cache_username, cache_password, '-upgrade_os_only', send_yes=True)
        if not result:
            log.error("Failed to install RPM bundle -upgrade_os_only")
            return
        log.info("Successfully installed RPM bundle -upgrade_os_only")

        # 7c. Log post-upgrade kernel version
        cache_machine = UnixMachine(cache_node, username=cache_username, password=cache_password)
        result = cache_machine.execute_command("uname -r")
        log.info(f"Post upgrade kernel version: {result.output}")
        
        return True