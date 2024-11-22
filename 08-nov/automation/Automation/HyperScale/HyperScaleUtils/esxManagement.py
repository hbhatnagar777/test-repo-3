# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2018 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import ssl
import tarfile
import time
from sys import exit
import os.path
from threading import Thread
from multiprocessing import Queue
import requests as req2
from AutomationUtils import logger
from pyVim import connect
from pyVmomi import vim
import shutil
from pyVim.task import WaitForTask

"""
Requirements: pyvmomi package

>> pip install pyvmomi

This module provides all the common methods that are needed for esx related functions for 
Hyperscale testing


    Functions:

    __init__()                      --  initialize an instance of the esxManagement class

    tear_down()                     -- Disconnects the object from the ESX server

    deploy_ovf()                     -- Can be used to remotely deploy an OVF to create a new 
                                        ESX machine for CS/Client

    keep_lease_alive()              -- This function provides a way to keep the lease to the ESX 
                                            host alive for the duration fo the operation
                                             being performed.

    get_all_vms_info()               -- Can be used to get the list of ALL vm's on the esx host 
                                            along with the details of their disk location and 
                                            IP address

    get_specific_vm_info()          -- Can be used to get details of a specific VM hosted on 
                                            the esx host

    get_vm_disk_path()              -- Can be used to get the location of the VM disk on the 
                                        datacenter/store on the esx

    get_vm_ip()                     -- Can be used to get the IP address of the VM disk on the 
                                            esx.

    get_vm_object()                 -- This method gives you back the object for the VM on the 
                                        esx to be used further

    vm_power_control()              -- This method can be used to turn ON/OFF/Reset a VM

    vm_power_control_with_retry_attempts()   -- This method can be used to turn ON/OFF/Reset a VM with retry attempts

    get_vm_power_state()            -- This method can be used to get teh current power state of 
                                        a VM      

    destroy_vm()                    -- This method can be used to destroy a VM using its name

    export_vm()                     -- This method can be used to export a Vm by name in OVF format

    create_ova()                     -- This methoda can be used to convert the OVF format 
                                        exported machine into an OVA
    
    find_devices_in_vm()             -- Finds devices of a particular type for a VM

    vm_set_cd_rom_enabled()          -- Disables/Enables the 'Connect At Power On' property for VM

    There are other specific methods in this class which are mainly used by the ones listed above.
"""


class EsxManagement(object):

    def __init__(self, esx_host, esx_user, esx_password, port=443):
        """
        Initializes the esxManagement class
        :param esx_host: (str) hostname of the esx server
        :param esx_user: (str) username of the esx server for connection
        :param esx_password: (str) password of the esx server for connection
        :param port: (int) port number of the esx server for connection. Default: 443
        """

        self.log = logger.get_log()
        self.esx_host = esx_host
        self.esx_user = esx_user
        self.esx_password = esx_password
        self.port = port
        self.ovf_path = None
        self.vmdk_path = None
        self.datastore_name = None
        self.datacenter_name = None
        self.cluster_name = None
        self.lease = None
        self.workdir = None
        self.ovfd = None
        context = None
        if hasattr(ssl, '_create_unverified_context'):
            context = ssl._create_unverified_context()
        try:
            self.si = connect.SmartConnect(host=self.esx_host, user=self.esx_user,
                                           pwd=self.esx_password, port=self.port,
                                           sslContext=context)
        except Exception as err:
            self.log.error('Unable to connect to host')
            self.log.error(str(err))
            raise Exception

    def tear_down(self):
        """Tear down function of test case"""
        connect.Disconnect(self.si)

    def deploy_ovf(self, datacenter_name, datastore_name, cluster_name, vmdk_path, ovf_path):
        """
        This method is used to deploy an ovf file along with the disk
        :param datacenter_name: (str) (Required) Data center name where it needs to be hosted
        :param datastore_name: (str) (Required) DataStore name where it needs to be hosted.
        :param cluster_name: (str) Name of the clulster on the host. If nothing is provided,
                default is used from host
        :param vmdk_path: (str) (Required) Location of the path to the vmdk file on the
                                local machine
        :param ovf_path: (str) (Required) Location of the path to the ovf file on the
                                local machine
        :return:
        """
        self.ovf_path = ovf_path
        self.vmdk_path = vmdk_path
        self.datastore_name = datastore_name
        self.datacenter_name = datacenter_name
        self.cluster_name = cluster_name
        exit_flag = Queue()
        try:
            self.get_ovf_descriptor()
            objs = self.get_objects()
            manager = self.si.content.ovfManager
            spec_params = vim.OvfManager.CreateImportSpecParams()
            import_spec = manager.CreateImportSpec(self.ovfd, objs["resource pool"], objs["datastore"]
                                                   , spec_params)
            self.lease = objs["resource pool"].ImportVApp(import_spec.importSpec,
                                                          objs["datacenter"].vmFolder)
            while True:
                if self.lease.state == vim.HttpNfcLease.State.ready:
                    url = self.lease.info.deviceUrl[0].url.replace('*', self.esx_host)
                    keepalive_thread = Thread(target=self.keep_lease_alive, args=(exit_flag,))
                    keepalive_thread.start()
                    '''
                    headers = {'Content-length': self.get_tarfile_size(),
                               'Content-Type': 'application/x-vnd.vmware-streamVmdk'} }
                    '''
                    self.log.info('Uploading VM disk now...')
                    start_time = time.time()
                    with open(self.vmdk_path, 'rb') as f:
                        req2.post(url, data=f, verify=False)
                    end_time = time.time()
                    self.log.info('VM disk has been uploaded in %d minutes'
                                  % int(((end_time - start_time)/60)))
                    exit_flag.put(1)
                    time.sleep(10)
                    self.lease.HttpNfcLeaseComplete()
                    return 0
                elif self.lease.state == vim.HttpNfcLease.State.error:
                    self.log.error("Lease error: " + self.lease.state.error)
                    try:
                        self.log.error(str(self.lease.error.msg))
                    except Exception as err:
                        self.log.warning(str(err))
                    return 1
        except Exception as err:
            self.log.error(str(err))
            return 1

    def get_ovf_descriptor(self):
        """
        Read in the OVF descriptor.
        This is used for deploying of OVF.
        """

        if os.path.exists(self.ovf_path):
            with open(self.ovf_path, 'r') as ovf_object:
                try:
                    self.ovfd = ovf_object.read()
                    ovf_object.close()
                except Exception as err:
                    self.log.error("Could not read file: %s" % self.ovf_path)
                    self.log.error(str(err))
                    exit(1)

    def get_obj_in_list(self, obj_name, obj_list):
        """
        Gets an object out of a list (obj_list) whos name matches obj_name.
        This is used for deploying of OVF.
        """
        for item in obj_list:
            if item.name == obj_name:
                return item
        self.log.info("Unable to find object by the name of %s in list %s"
                      % (obj_name, str(obj_list)))
        exit(1)

    def get_objects(self):
        """
        Return a dict containing the necessary objects for deployment.
        This is used for deploying of OVF.
        """
        # Get datacenter object.
        datacenter_list = self.si.content.rootFolder.childEntity
        if self.datacenter_name:
            datacenter_obj = self.get_obj_in_list(self.datacenter_name, datacenter_list)
        else:
            datacenter_obj = datacenter_list[0]

        # Get datastore object.
        datastore_list = datacenter_obj.datastoreFolder.childEntity
        if self.datastore_name:
            datastore_obj = self.get_obj_in_list(self.datastore_name, datastore_list)
        elif len(datastore_list) > 0:
            datastore_obj = datastore_list[0]
        else:
            self.log.error("No datastores found in DC (%s)." % datacenter_obj.name)
            return None

        # Get cluster object.
        cluster_list = datacenter_obj.hostFolder.childEntity
        if self.cluster_name:
            cluster_obj = self.get_obj_in_list(self.cluster_name, cluster_list)
        elif len(cluster_list) > 0:
            cluster_obj = cluster_list[0]
        else:
            self.log.error("No clusters found in DC (%s)." % datacenter_obj.name)
            return None
        # Generate resource pool.
        resource_pool_obj = cluster_obj.resourcePool
        return {"datacenter": datacenter_obj,
                "datastore": datastore_obj,
                "resource pool": resource_pool_obj}

    def keep_lease_alive(self, exit_flag):
        """
        Keeps the lease alive while POSTing the VMDK.
        This is used for deploying of OVF.
        """
        while True:
            try:
                exit_flag_val = exit_flag.get_nowait()
                if exit_flag_val == 1:
                    return
            except Exception as err:
                pass

            time.sleep(5)

            try:
                # Choosing arbitrary percentage to keep the lease alive.
                self.lease.HttpNfcLeaseProgress(50)
                if self.lease.state == vim.HttpNfcLease.State.done:
                    return
                # If the lease is released, we get an exception.
                # Returning to kill the thread.
            except Exception as err:
                self.log.error('Lease error %s' % str(err))
                self.log.error(str(vim.HttpNfcLease.error))
                return

    def get_tarfile_size(self):
        """
        Determine the size of a file inside the tarball.
        If the object has a size attribute, use that. Otherwise seek to the end
        and report that.
        This is used for deploying of OVF.
        """
        if hasattr(self.vmdk_path, 'size'):
            return self.vmdk_path.size
        size = os.path.getsize(self.vmdk_path)
        return size

    def get_disk(self, file_item):
        """
        Does translation for disk key to file name, returning a file handle.
        This is used for deploying of OVF.
        """
        ovffilename = list(filter(lambda x: x == file_item.path, tarfile.getnames()))[0]
        return tarfile.extractfile(ovffilename)

    def get_all_vms_info(self, depth=1):
        """
        Get VM info of ALL the machines on the host
        :param depth:
        :return: LIST of DICT (list of all machines )
        """

        content = self.si.RetrieveContent()
        full_vm_list = []
        for child in content.rootFolder.childEntity:
            if hasattr(child, 'vmFolder'):
                datacenter = child
                vm_folder = datacenter.vmFolder
                vm_list = vm_folder.childEntity
                for vm in vm_list:
                    maxdepth = 10
                    if hasattr(vm, 'childEntity'):
                        if depth > maxdepth:
                            return
                        vm_list = vm.childEntity
                        for vm_instance in vm_list:
                            self.get_all_vms_info(vm_instance, depth + 1)
                        return

                    if isinstance(vm, vim.VirtualApp):
                        vm_list = vm.vm
                        for vm_instance in vm_list:
                            self.get_all_vms_info(vm_instance, depth + 1)
                        return
                    summary = vm.summary
                    vm_info= {'Name': '', 'Path': '', 'IP': ''}
                    vm_info['Name'] = summary.config.name
                    vm_info['Path'] = summary.config.vmPathName
                    vm_info['IP'] = summary.guest.ipAddress
                    full_vm_list.append(vm_info)
                    if summary.runtime.question is not None:
                        self.log.warning("Question  : ", summary.runtime.question.text)
        return full_vm_list

    def get_specific_vm_info(self, vm_name):
        """

        :param vm_name: (str) This is the name of the VM on the host
        :return: (dict) of Name/disk path and IP address of the VM name specified.
        """
        for item in self.get_all_vms_info():
            if item['Name'] == vm_name:
                return item

    def get_vm_disk_path(self, vm_name):
        """

        :param vm_name: (str) This is the name of the VM on the host
        :return: Disk location of the VM  in string format
        """
        return self.get_specific_vm_info(vm_name)['Path']

    def get_vm_ip(self, vm_name):
        """

        :param vm_name:  (str) This is the name of the VM on the host
        :return:  IP address of the VM if resolvable in string format
        """
        return self.get_specific_vm_info(vm_name)['IP']

    def get_vm_object(self, vm_name):
        """

        :param vm_name: (str) This is the name of the VM on the host
        :return: return the VM object
        """
        vm = None
        try:
            entity_stack = self.si.content.rootFolder.childEntity
            while entity_stack:
                entity = entity_stack.pop()

                if entity.name == vm_name:
                    vm = entity
                    del entity_stack[0:len(entity_stack)]
                elif hasattr(entity, 'childEntity'):
                    entity_stack.extend(entity.childEntity)
                elif isinstance(entity, vim.Datacenter):
                    entity_stack.append(entity.vmFolder)
            if not isinstance(vm, vim.VirtualMachine):
                self.log.error('Could not find the virtual machine named %s' % vm_name)
        except Exception as err:
            self.log.error(err)
        finally:
            return vm

    def vm_power_control(self, vm_name, operation='on', vmware_tools_installed=True):
        """
        :param vm_name: (str) This is the name of the VM on the host
        :param operation: (str) on | off | shutdown. This is the desired operation
        shutdown
        :param vmware_tools_installed: True | False
                It helps to correctly check if the machine is up or not .
                if it is not installed, pass False
        :return: True if successful and False if not
        """
        try:
            vm = self.get_vm_object(vm_name)
            if vm is not None:
                if operation.lower() != self.get_vm_power_state(vm_name):
                    if operation.lower() == 'off':
                        try:
                            task = vm.ShutdownGuest()
                        except:
                            self.log.info('Could not shutdown via vmtools. Will power off now')
                            task = vm.PowerOff()

                        if task in (None, 'None'):
                            task = vm.PowerOff()
                    elif operation.lower() == 'on':
                        task = vm.PowerOn()
                    elif operation.lower() == 'shutdown':
                        task = vm.ShutdownGuest()
                    else:
                        self.log.error('Incorrect operation type provided."%s"' % operation)
                        return None
                    # answers = {}
                    while task.info.state not in [vim.TaskInfo.State.success,
                                                  vim.TaskInfo.State.error]:

                        self.log.info('Please wait while machine is powered %s'
                                      % operation.lower())
                        time.sleep(10)
                    if task.info.state == vim.TaskInfo.State.error:
                        self.log.error("error type: %s" % task.info.error.__class__.__name__)
                        self.log.error("found cause: %s" % task.info.error.faultCause)
                        for fault_msg in task.info.error.faultMessage:
                            self.log.error(fault_msg.key)
                            self.log.error(fault_msg.message)
                        self.log.error('Unable to power %s the machine' % operation.lower())
                        return False
                    self.log.info('Machine has been powered %s' % operation.lower())
                    if vmware_tools_installed and operation == 'on':
                        time_counter = 0
                        while True:
                            if vm.guest.toolsStatus == vim.vm.GuestInfo.ToolsStatus.toolsOk:
                                self.log.info('Machine OS has been booted up')
                                break
                            elif vim.vm.GuestInfo.ToolsStatus == vim.vm.GuestInfo.ToolsStatus.toolsNotRunning:
                                self.log.info('Vmware tools installed but not running. Bring up the tools service and continue')
                                time.sleep(15)
                                time_counter += 1
                                if time_counter >= 60:
                                    self.log.info('Waited 15 minutes for tool to start. Exiting')
                                    break
                            elif vim.vm.GuestInfo.ToolsStatus == vim.vm.GuestInfo.ToolsStatus.toolsNotInstalled:
                                self.log.info('VM tools not installed. cannot check for machine to be up')
                                time.sleep(300)
                                break
                            elif time_counter >= 120:
                                self.log.warning('Waited about 30 minutes for machine to boot '
                                                 'without confirmation. Exiting wait now')
                                break
                            else:
                                self.log.info('Waiting for OS to finish booting')
                                self.log.info('vmToolStatus: %s' % str(vm.guest.toolsStatus))
                                time.sleep(15)
                                time_counter += 1

                    return True
                else:
                    self.log.info('Machine is already powered %s' % operation.lower())
                    return True
            else:
                self.log.error('There was an error getting the Vm object. '
                               'Please check the logs for more info')
                self.log.error('Please make sure machine has been deployed')
                return False
        except Exception as err:
            self.log.error(str(err))
            self.log.error('Please make sure machine has been deployed')
            return False
    
    def vm_power_control_with_retry_attempts(self, vm_name, operation, vmware_tools_installed=False, retry_attempts=5):
        """
        Changes the power state of the VM (with retry attempts).

            Args:
                vm_name                 (str)   --  VM name

                operation               (str)   --  'on' or 'off'

                vmware_tools_installed  (bool)  --  It helps to correctly check if the machine is up or not .
                                                    if it is installed, pass True (Default False)

                retry_attempts          (int)   --  number of retry attempts   

            Returns:
                bool - Whether the state was changed.
                    returns True even when there is no need to change state
        """
        for attempt in range(retry_attempts):
            result = self.vm_power_control(vm_name, operation, vmware_tools_installed)
            if not result:
                self.log.warning(
                    f"Machine {vm_name} couldn't be powered {operation} in iteration {attempt+1}")
                time.sleep(5)
                continue
            self.log.info(
                f"Machine {vm_name} powered {operation} in iteration {attempt+1}")
            return True
        self.log.error(f"Machine {vm_name} couldn't be powered {operation}")
        return False

    def get_vm_power_state(self, vm_name):
        """

        :param vm_name: (str) Name of the VM whose current power state is required.
        :return: 'off' | 'on' | None (if error is encountered)
        """
        try:
            vm = self.get_vm_object(vm_name)
            if vm is not None:
                if vm.runtime.powerState == 'poweredOff':
                    self.log.info('%s - Machine is currently OFF' % vm_name)
                    return 'off'
                elif vm.runtime.powerState == 'poweredOn':
                    self.log.info('%s - Machine is currently ON' % vm_name)
                    return 'on'
                else:
                    self.log.warning('%s - Machine is currently in a weird state. %s '
                                     % (vm_name, vm.runtime.powerState))
                    return 'stuck'
            else:
                self.log.error('There was an error getting the Vm object. '
                               'Please check the logs for more info')
                return None
        except Exception as err:
            self.log.error(str(err))
            self.log.error('Please make sure machine has been deployed')
            return None

    def get_vmtools_status(self, vm_name):
        """
        This is a WIP
        This method will find out if the VM has vmtools installed or not.
        :param vm_name:
        :return: True | False . True being installed.
        """
        vm = self.get_vm_object(vm_name)
        states = ['toolsNotInstalled','toolsNotRunning','toolsOk','toolsOld']
        return vm.guest.toolsStatus

        # WIP

    def destroy_vm(self, vm_name):
        """

        :param vm_name: (str) Name of the VM that needs to be deleted.
        :return: True if successful and False if not
        """
        try:
            vm = self.get_vm_object(vm_name)
            if vm is not None:
                self.vm_power_control(vm_name, 'off')
                time.sleep(10)
                vm.Destroy()
                self.log.info('%s has been successfully deleted' % vm_name)
                return True
            else:
                self.log.error('There was an error getting the Vm object. '
                               'Please check the logs for more info')
                return False
        except Exception as err:
            self.log.error(str(err))
            return False

    def break_down_cookie(self, cookie):
        """ Breaks down vSphere SOAP cookie
        :param cookie: vSphere SOAP cookie
        :type cookie: str
        :return: Dictionary with cookie_name: cookie_value
        """
        cookie_a = cookie.split(';')
        cookie_name = cookie_a[0].split('=')[0]
        cookie_text = ' {0}; ${1}'.format(cookie_a[0].split('=')[1],
                                          cookie_a[1].lstrip())
        return {cookie_name: cookie_text}

    def download_device(self, headers, cookies, temp_target_disk, device_url,
                        total_bytes_written, total_bytes_to_write):
        """
        Download disk device of HttpNfcLease.info.deviceUrl list of devices
        :param headers: Request headers
        :type cookies: dict
        :param cookies: Request cookies (session)
        :type cookies: dict
        :param temp_target_disk: file name to write
        :type temp_target_disk: str
        :param device_url: deviceUrl.url
        :type device_url: str

        Following will be used in future

        :param total_bytes_written: Bytes written so far
        :type total_bytes_to_write: long
        :param total_bytes_to_write: VM unshared storage
        :type total_bytes_to_write: long
        :return: current_bytes_written
        """
        with open(temp_target_disk, 'wb') as handle:
            response = req2.get(device_url, stream=True, headers=headers, cookies=cookies,
                                verify=False)
            # response other than 200
            if not response.ok:
                response.raise_for_status()
            # keeping track of progress
            current_bytes_written = 0
            for block in response.iter_content(chunk_size=2048):
                # filter out keep-alive new chunks
                if block:
                    handle.write(block)
                    handle.flush()
                    os.fsync(handle.fileno())
                # getting right progress
                current_bytes_written += len(block)

        return current_bytes_written

    def export_vm(self, vm_name, destination_dir):
        """
        This method can be used to export a VM from a vmware ESX
        :param vm_name: (str) Name of the VM that needs to be exported
        :param destination_dir: (srt) Location path where the VM can be exported
        :return: (str) Location of the path where the exported files are located.
                        This will typically be a subfolder of the desitantion_dir variable.
        """
        self.workdir = destination_dir
        exit_flag = Queue()

        # VM must be powered off to export
        if self.get_vm_power_state(vm_name) != 'off':
            self.log.info('Shutting down VM %s for export' % vm_name)
            self.vm_power_control(vm_name, 'off')
        vm_obj = self.get_vm_object(vm_name)
        # Breaking down SOAP Cookie &
        # creating Header
        soap_cookie = self.si._stub.cookie
        cookies = self.break_down_cookie(soap_cookie)
        headers = {'Accept': 'application/x-vnd.vmware-streamVmdk'}  # not required
        self.log.info('Working dir: {} '.format(self.workdir))
        if not os.path.isdir(self.workdir):
            self.log.info('Creating working directory {}'.format(self.workdir))
            os.mkdir(self.workdir)
        # actual target directory for VM
        target_directory = os.path.join(self.workdir, vm_obj.config.instanceUuid)
        self.log.info('Target dir: {}'.format(target_directory))
        if not os.path.isdir(target_directory):
            self.log.info('Creating target dir {}'.format(target_directory))
            os.mkdir(target_directory)

        # Getting HTTP NFC Lease
        self.lease = vm_obj.ExportVm()
        keepalive_thread = Thread(target=self.keep_lease_alive, args=(exit_flag,))
        keepalive_thread.start()

        # Creating list for ovf files which will be value of
        ovf_files = list()
        total_bytes_written = 0
        total_bytes_to_write = vm_obj.summary.storage.unshared
        temp_target_disk = None
        try:
            while True:
                if self.lease.state == vim.HttpNfcLease.State.ready:
                    self.log.info('HTTP NFC Lease Ready')
                    for deviceUrl in self.lease.info.deviceUrl:
                        self.log.info(deviceUrl.url)
                        deviceUrl.url = deviceUrl.url.replace("*", self.esx_host)
                        if not deviceUrl.targetId:
                            self.log.error("No targetId found for url: {}.".format(deviceUrl.url))
                            self.log.error("Device is not eligible for export")
                            self.log.warning("Skipping...")
                            continue
                        temp_target_disk = os.path.join(target_directory,
                                                        deviceUrl.targetId)
                        self.log.info('Downloading {} to {}'.format(deviceUrl.url,
                                                                    temp_target_disk))

                        current_bytes_written = self.download_device(
                            headers=headers, cookies=cookies,
                            temp_target_disk=temp_target_disk,
                            device_url=deviceUrl.url,
                            total_bytes_written=total_bytes_written,
                            total_bytes_to_write=total_bytes_to_write)
                        # Adding up file written bytes to total
                        total_bytes_written += current_bytes_written
                        self.log.info('Creating OVF file for {}'.format(temp_target_disk))
                        # Adding Disk to OVF Files list
                        ovf_file = vim.OvfManager.OvfFile()
                        ovf_file.deviceId = deviceUrl.key
                        ovf_file.path = deviceUrl.targetId
                        ovf_file.size = current_bytes_written
                        ovf_files.append(ovf_file)
                    break
                elif self.lease.state == vim.HttpNfcLease.State.initializing:
                    self.log.info('HTTP NFC Lease Initializing.')
                elif self.lease.state == vim.HttpNfcLease.State.error:
                    self.log.info("HTTP NFC Lease error: {}".format(self.lease.state.error))
                    exit(1)
                time.sleep(2)
            self.log.info('Getting OVF Manager')
            ovf_manager = self.si.content.ovfManager
            self.log.info('Creating OVF Descriptor')
            vm_descriptor_name = vm_name if vm_name else vm_obj.name
            ovf_parameters = vim.OvfManager.CreateDescriptorParams()
            ovf_parameters.name = vm_descriptor_name
            ovf_parameters.ovfFiles = ovf_files
            vm_descriptor_result = ovf_manager.CreateDescriptor(obj=vm_obj,
                                                                cdp=ovf_parameters)
            if vm_descriptor_result.error:
                raise vm_descriptor_result.error[0].fault
            else:
                self.log.info(str(vm_descriptor_result))
                vm_descriptor = vm_descriptor_result.ovfDescriptor
                self.log.info(str(vm_descriptor))
                target_ovf_descriptor_path = os.path.join(target_directory,
                                                          vm_descriptor_name +
                                                          '.ovf')
                self.log.info('Writing OVF Descriptor {}'.format(target_ovf_descriptor_path))
                with open(target_ovf_descriptor_path, 'w') as handle:
                    handle.write(vm_descriptor)
                # ending lease
                exit_flag.put(1)
                time.sleep(5)
                self.lease.HttpNfcLeaseProgress(100)
                self.lease.HttpNfcLeaseComplete()
                exit_flag.put(1)
        except Exception as err:
            self.log.error(str(err))
        finally:
            return target_directory

    def create_ova(self, destination_filepath, source_folderpath, cleanup_source = True):
        """
        This function ca be used to convert an OVF export to an OVA
        :param destination_filepath: (str) This is the path to the ova that needs to be created.
                                    For Example: "C\\temp\test.ova"
        :param source_folderpath:  (str) This is a folder path where the ovf and disk files are
                                    present
        :return:
        """
        curr_dir = os.getcwd()
        self.log.info('Creating OVA')
        try:
            os.chdir(source_folderpath)

            with tarfile.open(destination_filepath, "w") as tar_handle:
                for file in (os.listdir(os.curdir)):
                    self.log.info('Adding %s to the archive' % str(file))
                    tar_handle.add(file)

            self.log.info('OVA creation finished')
            tar_handle.close()
            os.chdir(curr_dir)
            if cleanup_source:
                shutil.rmtree(source_folderpath)
                self.log.info('Cleaned up source ovf directory %s '
                              'since ova is successfully generated' % str(source_folderpath))
        except Exception as err:
            self.log.error(str(err))
            raise err
        finally:
            os.chdir(curr_dir)

    def delete_network_card(self, vm_name, nic_number):
        """ Deletes virtual NIC based on nic number
        :param vm_name: Virtual Machine name
        :param nic_number: Unit Number usuallt is 1/2/3 and so on
        :return: True if success
        """
        vm_obj = self.get_vm_object(vm_name)
        nic_prefix_label = 'Network adapter '
        nic_label = nic_prefix_label + str(nic_number)
        virtual_nic_device = None
        for dev in vm_obj.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard) \
                    and dev.deviceInfo.label == nic_label:
                virtual_nic_device = dev

        if not virtual_nic_device:
            raise RuntimeError('Virtual {} could not be found.'.format(nic_label))
        self.vm_power_control(vm_name, 'off')
        virtual_nic_spec = vim.vm.device.VirtualDeviceSpec()
        virtual_nic_spec.operation = \
            vim.vm.device.VirtualDeviceSpec.Operation.remove
        virtual_nic_spec.device = virtual_nic_device

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [virtual_nic_spec]
        task = vm_obj.ReconfigVM_Task(spec=spec)
        self.log.info(task)
        self.log.info('Removed %s ' % nic_label)
        time.sleep(15)
        return True

    def delete_all_nics(self, vm_name):
        """
        This method basically tries to remove the default nic one by one
        :param vm_name: name of the VM whose nic's are to be removed
        :return: nothing
        """
        try:
            for i in range(1, 5):
                self.delete_network_card(vm_name, i)
            self.log.info('Removed all network adapters')
        except Exception as err:
            self.log.warning(err)

    def get_snapshots(self, vm_name):
        """
        This method gets list of all snapshots with their names along with their snapshot objects

        :param vm_name: name of the VM whose snapshots are needed
        :return: list of dictionary in format
        op_dict = {"snapshot_name": '', "snapshot_obj": ''}
        """
        vm_object = self.get_vm_object(vm_name)
        op_dict = {"snapshot_name": '', "snapshot_obj": ''}
        op = []
        for i in vm_object.snapshot.rootSnapshotList:
            op_dict["snapshot_name"] = i.name
            op_dict["snapshot_obj"] = i.snapshot
            op.append(op_dict)
            op += self.snapshot_info(i)
        return op

    def snapshot_info(self, snapshot_list, depth=1):
        """
        This method is used internally to get child snapshots of each snapshot
        :param snapshot_list: internal
        :param depth:
        :return: list of dict of name object of snaps
        """
        max_depth = 100
        op_dict = {"snapshot_name": '', "snapshot_obj": ''}
        op = []
        if depth <= max_depth:
            if len(snapshot_list.childSnapshotList) > 0:
                for i in snapshot_list.childSnapshotList:
                    op_dict["snapshot_name"] = i.name
                    op_dict["snapshot_obj"] = i.snapshot
                    op.append(op_dict)
                    if hasattr(i, "childSnapshotList"):
                        op += self.snapshot_info(i, depth + 1)
        return op

    def get_snapshot_object(self, vm_name, snapshot_name):
        """
        This method helps to get snapshot object from the outptu of get all snapshots by name
        :param vm_name: Vm whos snapshot object is reqd
        :param snapshot_name: snapshot name whose object is reqd
        :return: snapshot object
        """
        for item in self.get_snapshots(vm_name):
            if item["snapshot_name"] == snapshot_name.strip():
                return item["snapshot_obj"]

    def revert_snapshot(self, vm_name, snapshot_name):
        """
        This method is to be able to revet to a snapshot of a vm by name
        :param vm_name: VM name
        :param snapshot_name: snapshot name
        :return: Returns True when success | False when it could not find snapshot
        """
        vm_snapshots = self.get_snapshots(vm_name)
        for snapshot in vm_snapshots:
            if snapshot_name == snapshot["snapshot_name"]:
                snap_obj = snapshot["snapshot_obj"]
                self.log.info("Reverting snapshot to %s " % str(snapshot["snapshot_name"]))
                task = snap_obj.RevertToSnapshot_Task()
                WaitForTask(task)
                self.log.info('Snapshot has been reverted')
                return True
        return False

    def reconfigure(self):
        pass # WIP

    def save_snapshot(self, vm_name, snapshot_name, description="Test snapshot"):
        """
        This method is used to create a snapshot of a vm
        :param vm_name: VM name
        :param snapshot_name: desired name of snapshot
        :param description: Description to add to snapshot
        :return: True if no error
        """
        vm_object = self.get_vm_object(vm_name)
        dump_memory = False
        quiesce = False
        self.log.info("Creating snapshot %s for virtual machine %s" % (
            snapshot_name, vm_name))
        WaitForTask(vm_object.CreateSnapshot(snapshot_name, description, dump_memory, quiesce))
        return True

    def delete_snapshot(self, vm_name, snapshot_name):
        """
        This method can be used to delete a particular snapshot

        :param vm_name: name of the VM
        :param snapshot_name: name of the snapshot to be deleted
        :return: True is success | False if not
        """
        vm_snapshots = self.get_snapshots(vm_name)
        for snapshot in vm_snapshots:
            if snapshot_name == snapshot["snapshot_name"]:
                snap_obj = snapshot["snapshot_obj"]
                self.log.info("Removing snapshot %s" % snapshot_name)
                WaitForTask(snap_obj.RemoveSnapshot_Task(True))
                return True
        return False

    def find_devices_in_vm(self, vm, device_type):
        """
        Finds devices of a particular type for a VM

            Args:
                vm                 (vim.VirtualMachine)   --  VM 

                device_type               (class)   --  The type of device to search for

            Returns:
                list - The list of devices for the VM matching the device_type
        """
        result = []
        for dev in vm.config.hardware.device:
            if isinstance(dev, device_type):
                result.append(dev)
        return result
    
    def vm_set_cd_rom_enabled(self, vm_name, enabled, vm=None):
        """Disables/Enables the 'Connect At Power On' property for VM

            Args:

                vm_name (str)                   --  VM name

                enabled (bool)                  --  To enable or disable

                vm      (vim.VirtualMachine)    --  The VM object (optional)

            Returns:

                None
        """
        if not vm:
            vm = self.get_vm_object(vm_name)
        cd_roms = self.find_devices_in_vm(vm, vim.vm.device.VirtualCdrom)
        for cd_rom in cd_roms:
            if cd_rom.connectable.startConnected == enabled:
                self.log.info(
                    f"Skipping CD-ROM for {vm_name} as it is in desired state already")
                continue
            self.log.info(f"Now setting CD-ROM for {vm_name} state as {enabled}")
            cd_rom.connectable.startConnected = enabled
            cd_rom.connectable.connected = enabled

            device_spec = vim.vm.device.VirtualDeviceSpec()
            device_spec.device = cd_rom
            device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit

            config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
            WaitForTask(vm.Reconfigure(config_spec))
            self.log.info(f"CD-ROM state changed for {vm_name} to {enabled}")
