'''
    To login to Vcenter and clone a VM from an OVF template from a local path

    get_file_size()     -   Determine the size of a file inside the tarball.
                            If the object has a size attribute, use that. Otherwise seek to the end
                            and report that.

    VmwareSession:

        Class for Keeping the session for vmware active

    VM_from_OVF:

        login_Vcenter()         -   login to Vcenter
        GetResourcePools()      -   Obtain the ESXi host that the resource pool belongs to
        clone_vm()              -   clone VM from an OVF template
        get_dc()                -   Get a datacenter by its name
        get_rp()                -   Get a resource pool in the datacenter by its names
        get_largest_free_rp()   -   Get the resource pool with the largest unreserved memory for VMs
        get_ds()                -   Pick a datastore by its name
        get_largest_free_ds()   -   Pick the datastore that is accessible with the largest free space

    OvfHandler:

        keep_lease_alive()      -   Keeps the lease alive while POSTing the VMDK
        get_descriptor()        -   Getter function to get the descriptor value
        set_spec()              -   The import spec is needed for later matching disks keys with
                                    file names
        get_disk()              -   Does translation for disk key to file name, returning a file handle
        get_device_url()        -   Getter function to get device url
        upload_disks()          -   Uploads all the disks, with a progress keep-alive
        upload_disk()           -   Upload an individual disk. Passes the file handle of the
                                    disk directly to the urlopen request

    Reconfigure_VM:

        get_obj()               -   Get vm object from virtual machine details
        get_obj_nic()           -   Get vm object from network details
        count_hard_disk()       -   Count the number of hard disks in the virtual machine
        add_disk()              -   To add a virtual hard disk to a VM
        edit_nic()              -   To edit the Network Adapter of VM
        get_hdd_prefix_label()  -   To get hard disk prefix label depending on the language used
        delete_disk()           -   Deletes virtual Disk based on disk number
        edit_disk()             -   Change the disk mode on a virtual hard disk
'''

import atexit
import os
import os.path
import ssl
import time
import logging
import sys
import threading
from threading import Thread
import winrm
import paramiko
from six.moves.urllib.request import Request, urlopen
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl
# from Test.machine import Machine

si = None
rp = None
dc = None
log = None
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename="VM_from_OVF.log",
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger()


def get_file_size(file):
    '''
        Determine the size of a file inside the tarball.
        If the object has a size attribute, use that. Otherwise seek to the end
        and report that.
    '''

    if hasattr(file, 'size'):
        return file.size
    size = file.seek(0, 2)
    file.seek(0, 0)
    return size


class VmwareSession(object):
    '''
        Class for Keeping the session for vmware active
    '''

    def __init__(self, connected_session, log, update_interval=120):
        '''
            Create daemon thread to keep connection alive
            Create the thread
            Args:
                connected_session               (object):   connection object
                log                             (object):   object for logging
                update_interval                 (int):      Interval between which thread keep the session active
        '''

        super().__init__()
        self._testcase_running = True
        self.connected_session = connected_session
        self.update_interval = update_interval
        self.log = log
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def stop(self):
        self._testcase_running = False

    def run(self):
        while self._testcase_running:
            self.log.info('Keeping the session {} alive'.format(
                self.connected_session.content.sessionManager.currentSession.key))
            time.sleep(self.update_interval)


class VM_from_OVF:

    def __init__(self, server_host_name, user_name, password,
                 datacenter_name, ovf_path, resource_pool,
                 datastore_name, VM_Name, **kwargs):
        '''
            Initialize VM_from_template class properties

            Args:
                    server_host_name        (str):      Hostname of the Vcenter
                    user_name               (str):      Username of the Vcenter
                    password                (str):      Password of the Vcenter
                    datacenter_name         (str):      Name of datacenter to search on
                                                        Defaults to first
                    ovf_path                (str):      Path of the OVF template
                    resource_pool           (str):      Name of resource pool to use
                                                        Defaults to largest memory free
                    datastore_name          (str):      Name of datastore to use
                                                        Defaults to largest free space in datacenter
                    **kwargs                (dict):     Optional arguments
        '''

        self.server_host_name = server_host_name
        self.user_name = user_name
        self.password = password
        self.datacenter_name = datacenter_name
        self.ovf_path = ovf_path
        self.resource_pool = resource_pool
        self.datastore_name = datastore_name
        self.VM_Name = VM_Name

    def login_Vcenter(self):
        '''
            login to vCenter
        '''

        try:
            global si
            from pyVim.connect import SmartConnect
            si = SmartConnect(host=self.server_host_name,
                                           user=self.user_name,
                                           pwd=self.password, disableSslCertValidation=True)

        except TypeError:
            from pyVim.connect import SmartConnectNoSSL
            si = SmartConnectNoSSL(host=self.server_host_name,
                                                user=self.user_name,
                                                pwd=self.password)
            atexit.register(Disconnect, si)
            VmwareSession(si, log, 600)
            log.info("Connected to %s" % self.server_host_name)
        except:
            log.info("Unable to connect to %s" % self.server_host_name)
            print("Unable to connect to %s" % self.server_host_name)
            return 1

    def GetResourcePools(self, entity):
        '''
            Obtain the ESXi host that the resource pool belongs to
        '''

        pools = []
        for pool in entity.resourcePool:
            pools += self.GetResourcePools(pool)
        pools.append(entity)
        return pools

    def clone_vm(self):
        '''
            clone VM from an OVF template
        '''

        global si
        global rp
        global dc

        log.info("Choosing a datacenter")
        if self.datacenter_name != "None":
            dc = self.get_dc(self.datacenter_name)
        else:
            dc = si.content.rootFolder.childEntity[0]
        log.info("Chose {} as the datacenter".format(dc.name))

        log.info("Choosing a resource pool")
        if self.resource_pool != "None":
            rp = self.get_rp(dc, self.resource_pool)
        else:
            rp = self.get_largest_free_rp(dc)
        log.info("Chose {} as the resource pool".format(rp.name))

        # identifying the host that the resource pool belongs to
        log.info("Identifying the host that the resource pool belongs to")
        host = None
        for i in range(0, len(dc.hostFolder.childEntity)):
            pools = self.GetResourcePools(dc.hostFolder.childEntity[i].resourcePool)
            for pool in pools:
                if pool.name == rp.name:
                    host = dc.hostFolder.childEntity[i]
                    break
        log.info("The Resource Pool belongs to {}".format(host.name))

        log.info("Choosing a datastore")
        if self.datastore_name != "None":
            ds = self.get_ds(dc, self.datastore_name)
        else:
            ds = self.get_largest_free_ds(dc, host)
        log.info("Chose {} as the datastore".format(ds.name))

        ovf_handle = OvfHandler(self.ovf_path)

        ovfManager = si.content.ovfManager
        # CreateImportSpecParams can specify many useful things such as
        # diskProvisioning (thin/thick/sparse/etc)
        # networkMapping (to map to networks)
        # propertyMapping (descriptor specific properties)
        cisp = vim.OvfManager.CreateImportSpecParams(entityName=self.VM_Name, diskProvisioning="thin")
        cisr = ovfManager.CreateImportSpec(ovf_handle.get_descriptor(),
                                           rp, ds, cisp)

        # These errors might be handleable by supporting the parameters in
        # CreateImportSpecParams
        if len(cisr.error):
            log.info("The following errors will prevent import of this OVA:")
            print("The following errors will prevent import of this OVA:")
            for error in cisr.error:
                log.info("%s" % error)
                print("%s" % error)
            return 1

        ovf_handle.set_spec(cisr)

        lease = rp.ImportVApp(cisr.importSpec, dc.vmFolder)
        while lease.state == vim.HttpNfcLease.State.initializing:
            log.info("Waiting for lease to be ready...")
            print("Waiting for lease to be ready...")
            time.sleep(1)

        if lease.state == vim.HttpNfcLease.State.error:
            log.info("Lease error: %s" % lease.error)
            print("Lease error: %s" % lease.error)
            exit(1)
        if lease.state == vim.HttpNfcLease.State.done:
            return 0

        log.info("Starting deploy...")
        print("Starting deploy...")
        return ovf_handle.upload_disks(lease, self.server_host_name)

    def get_dc(self, name):
        '''
            Get a datacenter by its name.
        '''

        global si
        for dc in si.content.rootFolder.childEntity:
            if dc.name == name:
                log.info("Got a datacenter by its name")
                return dc
        log.info('Failed to find datacenter named %s' % name)
        raise Exception('Failed to find datacenter named %s' % name)

    def get_rp(self, dc, name):
        '''
            Get a resource pool in the datacenter by its names.
        '''

        global si
        viewManager = si.content.viewManager
        containerView = viewManager.CreateContainerView(dc, [vim.ResourcePool],
                                                        True)
        try:
            for rp in containerView.view:
                if rp.name == name:
                    log.info("Get a resource pool in the datacenter by its name")
                    return rp
        finally:
            containerView.Destroy()
        log.info("Failed to find resource pool %s in datacenter %s" %
                 (name, dc.name))
        raise Exception("Failed to find resource pool %s in datacenter %s" %
                        (name, dc.name))

    def get_largest_free_rp(self, dc):
        '''
            Get the resource pool with the largest unreserved memory for VMs.
        '''

        global si
        viewManager = si.content.viewManager
        containerView = viewManager.CreateContainerView(dc, [vim.ResourcePool],
                                                        True)
        largestRp = None
        unreservedForVm = 0
        try:
            for rp in containerView.view:
                if rp.runtime.memory.unreservedForVm > unreservedForVm:
                    largestRp = rp
                    unreservedForVm = rp.runtime.memory.unreservedForVm
        finally:
            containerView.Destroy()
        if largestRp is None:
            log.info("Failed to find a resource pool in dc %s" % dc.name)
            raise Exception("Failed to find a resource pool in dc %s" % dc.name)
        log.info("Get the resource pool with the largest unreserved memory for VMs")
        return largestRp

    def get_ds(self, dc, name):
        '''
            Pick a datastore by its name.
        '''

        for ds in dc.datastore:
            try:
                if ds.name == name:
                    log.info("Picked a datastore by its name")
                    return ds
            except:  # Ignore datastores that have issues
                pass
        log.info("Failed to find %s on datacenter %s" % (name, dc.name))
        raise Exception("Failed to find %s on datacenter %s" % (name, dc.name))

    def get_largest_free_ds(self, dc, host):
        '''
            Pick the datastore that is accessible with the largest free space.
        '''

        global rp
        largest = None
        largestFree = 0
        for ds in dc.datastore:
            try:
                freeSpace = ds.summary.freeSpace
                if freeSpace > largestFree and ds.summary.accessible and ds in host.datastore:
                    largestFree = freeSpace
                    largest = ds
            except:  # Ignore datastores that have issues
                pass
        if largest is None:
            log.info("Failed to find any free datastores on %s" % dc.name)
            raise Exception('Failed to find any free datastores on %s' % dc.name)
        log.info("Picked the datastore that is accessible with the largest free space")
        return largest


class Reconfigure_VM():
    '''
        To Reconfigure CPU, Memory, Hard disk, Network Adapter, VM Name
    '''

    def __init__(self=None, vm_name=None):

        global si
        self.content = si.RetrieveContent()
        self.vm = self.get_obj([vim.VirtualMachine], vm_name, rp)
        self.unit_number = None

    def get_obj(self, vimtype, name, rp):
        '''
            Get vm object from virtual machine details
        '''

        log.info("Getting VM object from virtual machine details")
        obj = None
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, vimtype, True)
        for c in container.view:
            r = None
            if c.resourcePool != None:
                r = c.resourcePool.name
            if c.name == name and r == rp.name:
                obj = c
                break
        return obj

    def get_obj_nic(self, vimtype, name):
        '''
            Get vm object from network details
        '''

        log.info("Getting VM object from network details")
        obj = None
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj

    def count_hard_disk(self):
        '''
            Count the number of hard disks in the virtual machine
        '''

        log.info("Counting the number of hard disks in the virtual machine")
        for dev in self.vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                self.unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if self.unit_number == 7:
                    self.unit_number += 1
                if self.unit_number >= 16:
                    log.info("we don't support this many disks")
                    print("we don't support this many disks")
        log.info("There are {} hard disks in this VM".format(self.unit_number))
        return self.unit_number

    def add_disk(self, disk_size, spec, disk_type):
        '''
            To add a virtual hard disk to a VM
        '''

        dev_changes = []
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if disk_type == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = self.unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        for dev in self.vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)
        spec.deviceChange = dev_changes
        self.vm.ReconfigVM_Task(spec=spec)

    def edit_nic(self, network_name):
        '''
            To edit the Network Adapter of VM
        '''

        device_change = []
        for device in self.vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec = vim.vm.device.VirtualDeviceSpec()
                nicspec.operation = \
                    vim.vm.device.VirtualDeviceSpec.Operation.edit
                nicspec.device = device
                nicspec.device.wakeOnLanEnabled = True

                nicspec.device.backing = \
                    vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                nicspec.device.backing.network = \
                    self.get_obj_nic([vim.Network], network_name)
                nicspec.device.backing.deviceName = network_name

                nicspec.device.connectable = \
                    vim.vm.device.VirtualDevice.ConnectInfo()
                nicspec.device.connectable.startConnected = True
                nicspec.device.connectable.allowGuestControl = True
                device_change.append(nicspec)
                break

        config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
        self.vm.ReconfigVM_Task(config_spec)
        return True

    def get_hdd_prefix_label(self, language):
        '''
            To get hard disk prefix label depending on the language used
        '''

        log.info("Getting hard disk prefix label depending on the language used")
        language_prefix_label_mapper = {
            'English': 'Hard disk '
        }
        return language_prefix_label_mapper.get(language)

    def delete_disk(self, disk_number, language):
        '''
            Deletes virtual Disk based on disk number
        '''

        # deleting disk
        try:
            global si
            global dc

            diskManager = si.content.virtualDiskManager
            name = None

            for dev in self.vm.config.hardware.device:
                if hasattr(dev.backing, 'fileName'):
                    name = dev.backing.fileName

            task = diskManager.DeleteVirtualDisk_Task(name=name, datacenter=dc)

            while task.info.state in [vim.TaskInfo.State.queued, vim.TaskInfo.State.running]:
                print('.', end='')
            print('Deleted Excess Disks')

        except vmodl.MethodFault as error:
            print('Caught vmodl fault : ', error.msg)
            return -1

        # removing disk
        hdd_prefix_label = self.get_hdd_prefix_label(language)
        if not hdd_prefix_label:
            raise RuntimeError('Hdd prefix label could not be found')

        hdd_label = hdd_prefix_label + str(disk_number)
        virtual_hdd_device = None
        for dev in self.vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) \
                    and dev.deviceInfo.label == hdd_label:
                virtual_hdd_device = dev
        if not virtual_hdd_device:
            raise RuntimeError('Virtual {} could not '
                               'be found.'.format(virtual_hdd_device))

        virtual_hdd_spec = vim.vm.device.VirtualDeviceSpec()
        virtual_hdd_spec.operation = \
            vim.vm.device.VirtualDeviceSpec.Operation.remove
        virtual_hdd_spec.device = virtual_hdd_device

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [virtual_hdd_spec]
        self.vm.ReconfigVM_Task(spec=spec)
        return True

    def edit_disk(self, disk_number, Capacity, idx,
                  disk_prefix_label='Hard disk '):
        '''
            Change the disk mode on a virtual hard disk
        '''

        disk_label = disk_prefix_label + str(disk_number)
        virtual_disk_device = None

        # Find the disk device
        for dev in self.vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk) \
                    and dev.deviceInfo.label == disk_label:
                virtual_disk_device = dev
        if not virtual_disk_device:
            raise RuntimeError('Virtual {} could not be found'.format(disk_label))

        virtual_disk_spec = vim.vm.device.VirtualDeviceSpec()

        if (int(Capacity) * 1024 * 1024) < virtual_disk_device.capacityInKB:
            log.info("Hard disk capacity mentioned for VM {}, Hard disk {} is less than the existing capacity of {} KB"
                     .format(idx, disk_number, virtual_disk_device.capacityInKB))
            sys.exit(1)

        virtual_disk_spec.operation = \
            vim.vm.device.VirtualDeviceSpec.Operation.edit
        virtual_disk_spec.device = virtual_disk_device
        new_disk_kb = int(Capacity) * 1024 * 1024
        virtual_disk_spec.device.capacityInKB = new_disk_kb

        dev_changes = []
        dev_changes.append(virtual_disk_spec)
        spec = vim.vm.ConfigSpec()
        spec.deviceChange = dev_changes
        self.vm.ReconfigVM_Task(spec=spec)
        return True


class OvfHandler(object):
    '''
        OvfHandler handles most of the OVF operations.
        It processes the tarfile, matches disk keys to files and
        uploads the disks, while keeping the progress up to date for the lease.
    '''

    def __init__(self, ovffolder):
        '''
            Performs necessary initialization, opening the OVF folder,
            processing the files and reading the embedded ovf file.
        '''

        log.info("Performs necessary initialization, opening the OVF folder,"
                 " processing the files and reading the embedded ovf file.")
        self.ovffolder = ovffolder
        for file in os.listdir(ovffolder):
            if file.endswith('.ovf'):
                ovffile = os.path.join(ovffolder, file)
        ovffile = open(str(ovffile), 'rb')
        self.descriptor = ovffile.read().decode()

    def keep_lease_alive(self, lease):
        '''
            Keeps the lease alive while POSTing the VMDK.
        '''

        while (True):
            time.sleep(5)
            try:
                # Choosing arbitrary percentage to keep the lease alive.
                lease.HttpNfcLeaseProgress(50)
                if (lease.state == vim.HttpNfcLease.State.done):
                    return
                # If the lease is released, we get an exception.
                # Returning to kill the thread.
            except:
                return

    def get_descriptor(self):

        return self.descriptor

    def set_spec(self, spec):
        '''
            The import spec is needed for later matching disks keys with
            file names.
        '''

        self.spec = spec

    def get_disk(self, fileItem, lease):
        '''
            Does translation for disk key to file name, returning a file handle.
        '''

        log.info("Translating for disk key to file name and returning a file handle.")
        ovffilename = list(filter(lambda x: x == fileItem.path,
                                  os.listdir(self.ovffolder)))[0]
        return os.path.join(self.ovffolder, ovffilename)

    def get_device_url(self, fileItem, lease):

        for deviceUrl in lease.info.deviceUrl:
            if deviceUrl.importKey == fileItem.deviceId:
                return deviceUrl
        log.info("Failed to find deviceUrl for file %s" % fileItem.path)
        raise Exception("Failed to find deviceUrl for file %s" % fileItem.path)

    def upload_disks(self, lease, host):
        '''
            Uploads all the disks, with a progress keep-alive.
        '''

        log.info("Uploading all the disks, with a progress keep-alive")
        self.lease = lease
        try:
            for fileItem in self.spec.fileItem:
                self.upload_disk(fileItem, lease, host)
            log.info("Finished deploy successfully")
            print("Finished deploy successfully.")
            return 0
        except vmodl.MethodFault as e:
            log.info("Hit an error in upload: %s" % e)
            print("Hit an error in upload: %s" % e)
            lease.Abort(e)
        except Exception as e:
            log.info("Lease: %s" % lease.info)
            print("Lease: %s" % lease.info)
            log.info("Hit an error in upload: %s" % e)
            print("Hit an error in upload: %s" % e)
            lease.Abort(vmodl.fault.SystemError(reason=str(e)))
            raise
        return 1

    def upload_disk(self, fileItem, lease, host):
        '''
            Upload an individual disk. Passes the file handle of the
            disk directly to the urlopen request.
        '''

        log.info("Uploading an individual disk. Passes the file handle of the"
                 " disk directly to the urlopen request.")
        while (True):
            if (lease.state == vim.HttpNfcLease.State.ready):

                keepalive_thread = Thread(target=self.keep_lease_alive, args=(lease,))
                keepalive_thread.start()

                ovffile = open(self.get_disk(fileItem, lease), 'rb')
                deviceUrl = self.get_device_url(fileItem, lease)
                url = deviceUrl.url.replace('*', host)
                headers = {'Content-length': get_file_size(ovffile)}
                if hasattr(ssl, '_create_unverified_context'):
                    sslContext = ssl._create_unverified_context()
                else:
                    sslContext = None
                req = Request(url, ovffile, headers)
                urlopen(req, context=sslContext)

                lease.HttpNfcLeaseComplete()
                keepalive_thread.join()
                return 0
            elif (lease.state == vim.HttpNfcLease.State.error):
                print("Lease error: " + lease.state.error)
                exit(1)


class main():

    def __init__(self, destination, file, VM_Name, CPU, Cores, Memory, Hard_Disk, Network, Hard_Disk_Cap, Op_Type, idx,
                 isBackupVM, VM_Curr, host, user, password, datacenter_name, resource_pool_name, datastore_name,
                 commserver_host_name, commserver_name, commcell_user_name, commcell_password):

        log.info("Reached VM_from_OVF.py")
        self.destination = destination
        self.file = file
        self.VM_Name = VM_Name
        self.CPU = CPU
        self.Cores = Cores
        self.Memory = Memory
        self.Hard_Disk = Hard_Disk
        self.Network = Network
        self.Hard_Disk_Cap = Hard_Disk_Cap
        self.Op_Type = Op_Type
        self.VM_Number = idx
        self.isBackupVM = isBackupVM
        self.VM_Curr = VM_Curr
        self.host = host
        self.user = user
        self.password = password
        self.datacenter_name = datacenter_name
        self.resource_pool_name = resource_pool_name
        self.datastore_name = datastore_name
        self.commserver_host_name = commserver_host_name
        self.commserver_name = commserver_name
        self.commcell_user_name = commcell_user_name
        self.commcell_password = commcell_password

    def start(self):

        # create an instance of VM_from_OVA class
        VM_from_OVF_obj = VM_from_OVF(self.host, self.user, self.password,
                                      self.datacenter_name, os.path.join(self.destination, self.file.split(".")[0]),
                                      self.resource_pool_name, self.datastore_name, self.VM_Name)

        # login to Vcenter
        log.info("--------------------------Logging into Vcenter---------------------------")
        VM_from_OVF_obj.login_Vcenter()

        # clone the VM from OVF template
        log.info("-------------------Starting to clone VM from OVF template----------------")
        VM_from_OVF_obj.clone_vm()

        # reconfiguring
        log.info("------------------Reconfiguring VM Hardware according to json------------")
        Reconfigure_VM_obj = Reconfigure_VM(self.VM_Name)
        vm = Reconfigure_VM_obj.vm
        cspec = vim.vm.ConfigSpec()

        # reconfiguring CPU
        log.info("Reconfiguring CPU")
        cspec.numCPUs = int(self.CPU)

        # reconfiguring CPU cores
        if self.Cores != "None":
            log.info("Reconfiguring CPU")
            k = []
            for i in range(1, int(self.Cores) + 1):
                if int(self.Cores) % i == 0:
                    k.append(i)
            if int(self.Cores) in k:
                cspec.numCoresPerSocket = int(self.Cores)
            else:
                log.info("Not possible to set the specified number of cores. Proceeding with default")

        # reconfiguring Memory
        log.info("Reconfiguring Memory")
        cspec.memoryMB = int(self.Memory) * 1024

        vm.Reconfigure(cspec)

        # reconfiguring Network Adapter 1
        log.info("Reconfiguring Network Adapter 1")
        Reconfigure_VM_obj.edit_nic(self.Network)

        # reconfiguring hard disks
        log.info("Reconfiguring Hard disk")
        number_disks = Reconfigure_VM_obj.count_hard_disk()

        if number_disks >= int(self.Hard_Disk):

            if number_disks > int(self.Hard_Disk):
                log.info("Deleting excess Hard disks according to requirement")
                for i in range(1, number_disks - int(self.Hard_Disk) + 1):
                    Reconfigure_VM_obj.delete_disk(number_disks, 'English')
                log.info("Deleted excess Hard disks according to requirement")
            log.info("Editing Hard disk Capacity according to requirement")

            for i in range(1, int(self.Hard_Disk) + 1):
                Reconfigure_VM_obj.edit_disk(i, int(self.Hard_Disk_Cap), self.VM_Number)
            log.info("Edited Hard disk Capacity according to requirement")

        elif number_disks < int(self.Hard_Disk):

            log.info("Adding excess Hard disks according to requirement")
            for i in range(1, int(self.Hard_Disk) - number_disks + 1):
                Reconfigure_VM_obj.add_disk(int(self.Hard_Disk_Cap), cspec, 'thin')
            log.info("Added excess Hard disks according to requirement")
            log.info("Editing Hard disk Capacity according to requirement")

            for i in range(1, int(number_disks) + 1):
                Reconfigure_VM_obj.edit_disk(i, int(self.Hard_Disk_Cap), self.VM_Number)
            log.info("Edited Hard disk Capacity according to requirement")

        '''
        # check if the machine has been created successfully 
        log.info("check if the machine has been created successfully")
        if self.Op_Type == "Linux":

            log.info("Powering on the Linux Backup VM to check if machine object is created")
            vm.PowerOn()
            log.info("Sleeping for 3 minutes to wait for the machine to switch on")
            time.sleep(180)
            try:
                host = vm.summary.guest.ipAddress
                Machine(host, username= "user", password = "password")
            except Exception as e:
                log.info('Backup Linux VM creation failed')
                exit(1)
        '''

        CSHost = self.commserver_host_name
        CSName = self.commserver_name
        CCName = self.commcell_user_name
        CCpwd = self.commcell_password

        # install Commvault software in Windows Controller Machine
        if self.isBackupVM == "False" and self.Op_Type == "Windows":

            Host_Name = self.VM_Curr['HostName']
            Domain_Name = self.VM_Curr['DomainName']
            Domain_UName = self.VM_Curr['DomainUserName']
            Domain_Pwd = self.VM_Curr['DomainPassword']

            # Default user name and password of the template machines
            user = 'Administrator'
            password = 'password'

            tries01 = 2

            while tries01:
                try:

                    log.info("Powering on the Controller VM")
                    vm.PowerOn()
                    log.info("Sleeping for 3 minutes to wait for the machine to switch on")
                    time.sleep(180)
                    host = vm.summary.guest.ipAddress
                    session = winrm.Session(host, auth=(user, password))
                    log.info("Obtaining the IP address {}".format(host))

                    # remove from domain
                    log.info("Removing the machine from the domain")
                    result = session.run_cmd("wmic computersystem where name='%computername%' call "
                                             "unjoindomainorworkgroup funjoinoptions=0")
                    log.info(result.std_out)
                    print(result.std_out)

                    # rename computer name
                    log.info("Renaming the machine's computer name")
                    result = session.run_cmd("wmic computersystem where name='%computername%' "
                                             "call rename name={}".format(Host_Name))
                    log.info(result.std_out)
                    print(result.std_out)

                    # restart VM
                    log.info("Restarting the VM to observe changes")
                    session.run_cmd("shutdown/r")
                    log.info("Sleeping for 5 minutes to wait for the machine to reboot")
                    time.sleep(300)

                    # add to a domain
                    log.info("Adding the machine to a domain")

                    tries02 = 5
                    while tries02:
                        log.info("Try {}".format(5 - tries02 + 1))
                        host = vm.summary.guest.ipAddress
                        session = winrm.Session(host, auth=(user, password))
                        result = session.run_cmd("wmic computersystem where name='%computername%' call "
                                                 "joindomainorworkgroup fjoinoptions=3 "
                                                 "name={} username={} password={}".format(Domain_Name, Domain_UName,
                                                                                          Domain_Pwd))
                        log.info(result.std_out)
                        print(result.std_out)
                        tries02 -= 1

                    # restart VM
                    log.info("Restarting the VM to observe changes")
                    session.run_cmd("shutdown/r")
                    log.info("Sleeping for 5 minutes to wait for the machine to reboot")
                    time.sleep(300)

                    # register client and commserver
                    log.info("Registering the client to a commserver muliptle times since the details"
                             "are not present in the registry the first time")
                    tries03 = 3
                    while tries03:
                        log.info("Try {}".format(3 - tries03 + 1))
                        host = vm.summary.guest.ipAddress
                        session = winrm.Session(host, auth=(user, password))
                        result = session.run_cmd('cd C:\\Program Files\\Commvault\\ContentStore\\Base && '
                                                 'SIMCallWrapper.exe -OpType {} -CSHost {} -CSName {} '
                                                 '-clientName {} -clientHostName {} -output {} -user {} '
                                                 '-password {}'.format(1000, CSHost, CSName, Host_Name,
                                                                       Host_Name + '.' + Domain_Name,
                                                                       'C:\\output.xml', CCName, CCpwd))
                        log.info(result.std_out)
                        print(result.std_out)
                        tries03 -= 1

                    log.info("Powering off the Controller VM")
                    vm.PowerOff()
                    break

                except Exception as e:

                    log.info("Error occurred: {}".format(str(e)))
                    print("Error occurred: {}".format(str(e)))

                    if tries01 == 2:
                        log.info("Giving another try to connect to the VM created")
                        log.info("Switching off VM")
                        vm.PowerOff()
                        log.info("Sleeping for 3 minutes to wait for the machine to power Off")
                        time.sleep(180)
                        tries01 -= 1

                    else:
                        log.info("------------------------------------------------------------------------------------")

        # install Commvault software in Linux Controller Machine
        if self.isBackupVM == "False" and self.Op_Type == "Linux":

            tries01 = 2

            while tries01:
                try:
                    log.info("Powering on the Controller VM")
                    vm.PowerOn()
                    log.info("Sleeping for 3 minutes to wait for the machine to switch on")
                    time.sleep(180)
                    host = vm.summary.guest.ipAddress

                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(host, username='root', password='password')
                    print(self.VM_Name)
                    client.exec_command('hostnamectl set-hostname {}'.format(self.VM_Name))
                    log.info("Changed hostname")

                    log.info("Details: ")
                    stdin, stdout, stderr = client.exec_command('hostnamectl')

                    for line in stdout:
                        log.info(line.strip('\n'))
                        print(line.strip('\n'))

                    # restart VM
                    log.info("Restarting the VM to observe changes")
                    client.exec_command('reboot')
                    log.info("Sleeping for 5 minutes to wait for the machine to reboot")
                    time.sleep(300)

                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    client.connect(host, username='root', password='password')

                    log.info("Registering client to commserver")
                    stdin, stdout, stderr = client.exec_command('cd /opt/commvault/Base && '
                                                                './SIMCallWrapper -OpType {} -CSHost {} -CSName {} '
                                                                '-clientName {} -clientHostName {} -output {} -user {} '
                                                                '-password {} -restartServices'.format(1000, CSHost,
                                                                                                       CSName,
                                                                                                       self.VM_Name,
                                                                                                       self.VM_Name,
                                                                                                       '/output.xml',
                                                                                                       CCName, CCpwd))

                    for line in stdout:
                        log.info(line.strip('\n'))
                        print(line.strip('\n'))

                    log.info("Registered successfully")

                    client.close()

                    log.info("Powering off the Controller VM")
                    vm.PowerOff()
                    break

                except Exception as e:

                    log.info("Error occurred: {}".format(str(e)))
                    print("Error occurred: {}".format(str(e)))

                    if tries01 == 2:
                        log.info("Giving another try to connect to the VM created")
                        log.info("Switching off VM")
                        vm.PowerOff()
                        log.info("Sleeping for 3 minutes to wait for the machine to power Off")
                        time.sleep(180)
                        tries01 -= 1

                    else:
                        log.info("------------------------------------------------------------------------------------")
