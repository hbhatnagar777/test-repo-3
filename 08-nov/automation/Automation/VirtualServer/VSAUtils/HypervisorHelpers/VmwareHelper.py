# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Vmware

    VmwareHelper:

        get_all_vms_in_hypervisor()		        - abstract -get all the VMs in HYper-V Host

        compute_free_resources()		        - compute the Vmware host and Datastore
                                                    for performing restores

        _vmware_login()                         - Login to vcenter 6.5 and above

        _make_request()                         - Rest api calls to vcenter

        _vmware_get_vms()                       - Get list of qualified vms

        _get_vcenter_version()                  - get the vcenter version

        get_all_vms_in_hypervisor()             - Get complete list of vms in the vcenter

        compute_free_resources()                - Calculate free resources

        _get_datastore_dict()                   - Get list of datastore with free space

        _get_host_memory()                      - Get list of esx with free ram and cpu

        _get_required_resource_for_restore()    - Get restore vm ram and storage requirement

        _get_datastore_priority_list()          - Get list of datastore in descending
                                                    order as per free space

        _get_host_priority_list()               -  Get list of esx in descending oder
                                                    as per free ram

        _get_datastore_tree_list()              - get datastore hierarchy

        enable_maintenance_mode()               - Enable maintenance mode on specified the ESXi host

        disable_maintenance_mode()              - Disable maintenance mode on specified the ESXi host

        enter_standby_mode()                    - Enter standby mode on the specified ESXi host

        exit_standby_mode()                     - Exit standby mode on the specified ESXi host

        get_datastore_type()                    - Gets the type of datastore(NFS or VMFS)
"""
import copy
import socket
import re
import time
import os
import threading
import requests
from collections import OrderedDict
from cvpysdk.job import JobController
from cvpysdk.client import Client
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from pyVmomi import vim, vmodl, pbm, VmomiSupport, SoapStubAdapter
import ssl
import http.client
from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vapi.std_client import DynamicID

class VmwareHelper(Hypervisor):
    """
    Main class for performing all operations on Vmware Hypervisor
    """

    def __init__(self, server_host_name, user_name,
                 password, instance_type, auto_commcell,
                 host_machine=socket.gethostbyname_ex(socket.gethostname())[2][0],
                 **kwargs):
        """
        Initialize Vmware Helper class properties

        Args:
            server_host_name    (str):      Hostname of the Vcenter

            host_machine        (str):      Vcenter name

            user_name           (str):      Username of the Vcenter

            password            (str):      Password of the Vcenter

            instance_type       (str):      Instance type of the Vmware

            auto_commcell       (object):   Commcell object

            **kwargs            (dict):   Optional arguments
        """
        super(VmwareHelper, self).__init__(server_host_name,
                                           user_name, password, instance_type, auto_commcell, host_machine)
        self.operation_ps_file = "GetVmwareProps.ps1"
        self.vcenter_version = 0
        self.prop_dict = {
            "server_name": self.server_host_name,
            "user": self.user_name,
            "pwd": self.password,
            "vm_name": "$null",
            "extra_args": "$null"
        }
        self.disk_extension = [".vmdk"]
        self.connection = None
        self.vim = vim
        self.vmodl = vmodl
        self.keep_login = None
        self.pbm_content = None
        self.profile_manager = None
        self.vsphere_client = None
        self._vmware_login()

    class VmwareSession(object):
        """
        Class for Keeping the session for vmware active
        """

        def __init__(self, connected_session, log, update_interval=600):
            """Create daemon thread to keep connection alive
            Create the thread
            Args:
                connected_session             (object): connection object

                log                             (object): object for logging

                update_interval                 (int):      Interval between which thread keep the session active

            """
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

    def _vmware_login(self):
        """
        Login to vcenter 6.0 and above
        Raises:
            Exception:
                Failed to log in to vcenter server
        """
        try:
            try:
                from pyVim.connect import SmartConnect
                self.connection = SmartConnect(host=self.server_host_name,
                                               user=self.user_name,
                                               pwd=self.password, disableSslCertValidation=True)

            except TypeError:
                from pyVim.connect import SmartConnectNoSSL
                self.connection = SmartConnectNoSSL(host=self.server_host_name,
                                                    user=self.user_name,
                                                    pwd=self.password, disableSslCertValidation=True)
            if self.connection:
                self.keep_login = self.VmwareSession(self.connection, self.log, 600)
                self.log.info("Connection successful to VC: {}".format(self.server_host_name))
                self.vcenter_version = self.connection.content.about.version
                self.vcenter_version = float('.'.join(self.vcenter_version.split('.')[:-1]))
        except http.client.HTTPException as e:
            self.log.exception(e)
            raise Exception(str(e))
        except Exception as err:
            self.log.exception("An exception occurred while logging in to the vcenter")
            raise Exception(err)

    def get_content(self, vimtype):
        """
        Get content object
        Args:
            vimtype             (object): vim type

        Returns:
            obj                 (object):   object of the content of vimtype

        Raises:
            Exception:
                Failed to get content
        """

        _try = 0
        obj = {}
        while _try < 3:
            try:
                try:
                    container = self.connection.content.viewManager.CreateContainerView(
                        self.connection.content.rootFolder, vimtype, True)
                except self.vim.fault.NotAuthenticated as err:
                    self.log.info("Session timed out. Reconnecting")
                    self._vmware_login()
                    container = self.connection.content.viewManager.CreateContainerView(
                        self.connection.content.rootFolder, vimtype, True)
                for managed_object_ref in container.view:
                    obj.update({managed_object_ref: managed_object_ref.name})
                container.Destroy()
                return obj
            except Exception as err:
                self.log.info("Error:{} Attempt {}".format(err, _try))
                time.sleep(10)
                _try += 1
        self.log.exception("Not able to get content from VC: {}".format(self.server_host_name))

    def _vmware_get_vms(self):
        """
        Get all vms of the vcenter

        Returns:
             vmlist         (dict): list of vms in the Vcenter

        Raises:
            Exception:
                Not able to get the vms from vcenter
        """
        try:
            vmlist = []
            get_all_vms = self.get_content([self.vim.VirtualMachine])
            for vm in get_all_vms:
                try:
                    vmlist.append(vm.name)
                except (AttributeError, self.vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("Issue with vm: {}. Skipping it".format(vm))
                    continue
            return vmlist
        except Exception as err:
            self.log.exception("An exception occurred while getting list of vms from vcenter")
            raise Exception(err)

    def get_all_vms_in_hypervisor(self, server="", pattern="", c_type=""):
        """
        Get all the vms for vmware

        Args:
            server          (str):  Vcenter for which all the VMs has to be fetched

            pattern         (str):  Pattern to fetch the vms

            c_type            (str):  Type of content

        Returns:
            _all_vm_list    (str):  List of VMs in the host of the Vcenter

        Raises:
            Exception:
                Not able to get the vms from vcenter
        """
        try:
            _all_vm_list = []
            if not c_type:
                get_all_vms = self._vmware_get_vms()
            else:
                if not pattern:
                    self.log.error("No pattern received")
                else:
                    rep = {'type:server': ':runtime.host.name',
                           'type:datastore': ':datastore[0].name',
                           'type:datacenter': ':parent.parent.name',
                           'type:cluster': ' :runtime.host.parent.name',
                           'type:resource_pool': ':resourcePool.name',
                           'type:vmpowerstate': ':runtime.powerState',
                           'type:vmguestos': ':config.guestFullName',
                           'type:vmguesthostname': ':guest.hostName',
                           'type:tag': ':get-tag',
                           'type:tagcategory': ':get-tagcategory'}
                rep = dict((re.escape(k), v) for k, v in rep.items())
                _pattern = re.compile("|".join(rep.keys()))
                pattern = _pattern.sub(lambda m: rep[re.escape(m.group(0))], pattern)
                if re.search('get-tag', pattern):
                    _ps_path = os.path.join(
                        self.utils_path, self.operation_ps_file)
                    self.prop_dict["property"] = c_type
                    self.prop_dict["extra_args"] = pattern
                    output = self.controller._execute_script(_ps_path, self.prop_dict)
                    if not output.exception:
                        get_all_vms = output.output.rsplit("=", 1)[1].strip().split(",")
                    else:
                        self.log.error("Error in getting tags/category vms: {}".
                                       format(output.exception))
                        raise Exception
                else:
                    if 'id:' in pattern:
                        pattern = pattern.replace('name', '_moId')
                    get_all_vms = self._filter_vms(pattern)

            for vm in get_all_vms:
                if re.match("^[()\sA-Za-z0-9_-]*", vm):
                    _all_vm_list.append(vm)
            return _all_vm_list
        except Exception as err:
            self.log.exception("An exception occurred while getting all VMs from Vcenter")
            raise Exception(err)

    def _filter_vms(self, pattern):
        """
        Filters teh vms from the vm list
        Args:
            pattern             (string):   Patten to be looked for in vms

        Returns:
            vms                 (list):     List of vms matching the pattern

        """
        vms = []
        _prop = pattern.split('\n:')[1]
        _value = pattern.split('\n')[0].split(':')[1]
        all_vms = self.get_content([self.vim.VirtualMachine])
        _pat = re.compile(_value)
        for vm in all_vms:
            if vm.runtime.connectionState == 'connected':
                try:
                    if _pat.match(eval('vm.%s' % _prop)):
                        vms.append(vm.name)
                except (AttributeError, vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("vm {} is getting skipped. Please check".format(vm))
                    continue
        return vms

    def compute_free_resources(self, vm_list):
        """
        Compute the free Resource of the Vcenter based on free memory and cpu

        Args:
            vm_list         (list):  list of Vms to be restored

        Returns:
            Datastore	    (str):  The Datastore where restore can be performed

            ESX             (str):  ESX where restore has to be performed

            Cluster         (str):  Cluster where restore has to be performed

            Datacenter      (str):  DataCenter where restore has to be performed

            network         (str):  Netowrk which needs to be attached

        Raises:
            Exception:
                Not able to get Datastore or ESX or Cluster or Datacenter or all

        """
        try:
            _datastore_priority_dict = self._get_datastore_dict()
            _host_priority_dict = self._get_host_memory()
            network = None

            if vm_list:
                _total_vm_memory, _total_disk_space = self._get_required_resource_for_restore(vm_list)
            else:
                _total_vm_memory = 0
                _total_disk_space = 0

            for each_datastore in _datastore_priority_dict.items():
                try:
                    if (each_datastore[1][0]) > _total_disk_space:
                        datastore_name = each_datastore[0]
                        self.log.info("The Datastore {} has more than total"
                                      "disk space in VM".format(datastore_name))
                        _tree = self._get_datastore_tree_list(datastore_name)
                        if _tree['ESX'] in _host_priority_dict.keys():
                            if _host_priority_dict[_tree['ESX']][0] > _total_vm_memory:
                                for _vm in self.VMs:
                                    if _tree['ESX'] != self.VMs[_vm].esx_host:
                                        network = self._get_host_network(_tree['ESX'])
                                        if not network:
                                            break
                                if not network:
                                    continue
                                self.log.info(
                                    "the Host {} has higher "
                                    "memory than the total VMs".format(_tree['ESX']))
                                break
                    else:
                        continue
                except Exception:
                    self.log.warning("Issue with ds: {}. Skipping it".format(each_datastore))
                    continue
            return each_datastore[0], [_tree['ESX']], _tree['Cluster'], _tree['Datacenter'], network

        except Exception as err:
            self.log.exception("An exception occurred while getting "
                               "datastore or ESX or Cluster or Datacenter or all")
            raise Exception(err)

    def _get_datastore_dict(self, gx_backup=False):
        """
        Get the list of datastore in an ESX

        Args:
            gx_backup           (bool):  include gx_backup datastores

        Returns:
            _disk_size_dict     (dict): Datastores with name and free spaces

        Raises:
            Exception:
                Not able to get datastores from the Vcenter
        """
        try:
            _disk_size_dict = {}
            all_ds = self.get_content([self.vim.Datastore])
            for ds in all_ds:
                try:
                    if ds.summary.accessible:
                        free_space = int(ds.info.freeSpace / 1024 / 1024 / 1024)
                        _disk_size_dict.setdefault(ds.name, []).append(free_space)
                except (AttributeError, vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("datastore {} is getting skipped. Please check".format(ds))
                    continue

            _disk_size_dict = OrderedDict(sorted(
                _disk_size_dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True))
            if not gx_backup:
                _disk_size_dict = dict(
                    filter(lambda item: 'GX_BACKUP' not in item[0], _disk_size_dict.items()))
            return _disk_size_dict

        except Exception as err:
            self.log.exception("exception raised in _get_datastore_dict  ")
            raise err

    def _get_all_nics_in_host(self):
        """
        Get all the nics in the host

        Returns:
            nics_dict           (list):     list of nics in each esx host

        Raises:
            Exception:
                Not able to get nic cards from the Vcenter
        """
        try:
            _nics_dict = {}
            all_esx = self.get_content([self.vim.HostSystem])
            for esx in all_esx:
                try:
                    for network in esx.network:
                        try:
                            if isinstance(network.name, str):
                                _nics_dict[esx.name] = network.name
                        except (AttributeError, vmodl.fault.ManagedObjectNotFound):
                            self.log.warning("Issue with network: {}. Skipping it".format(network))
                            continue
                except (AttributeError, vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("Issue with ESX: {}. Skipping it".format(esx))
                    continue
            return _nics_dict
        except Exception as err:
            self.log.exception("exception raised in _get_all_nics_in_host  ")
            raise err

    def _get_host_memory(self):
        """
        Get the free memory in the ESX

        Returns:
            _esx_dict           (dict): Dictionary of ESX and its free space

        Raises:
            Exception:
                Raise exception when failed to get Memory of the ESX

        """
        try:
            _esx_dict = {}
            all_esx = self.get_content([self.vim.HostSystem])
            for host in all_esx:
                try:
                    if host.summary.runtime.connectionState == 'connected':
                        total_memory = host.summary.hardware.memorySize
                        used_memory = host.summary.quickStats.overallMemoryUsage
                        free_memory = int(total_memory / 1024 / 1024 / 1024) - int(used_memory / 1024)
                        _esx_dict.setdefault(host.name, []).append(free_memory)
                except (AttributeError, vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("Issue with host: {}. Skipping it".format(host))
                    continue
            _esx_dict = OrderedDict(sorted(
                _esx_dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True))
            return _esx_dict
        except Exception as err:
            self.log.exception("exception raised in GetMemory  ")
            raise err

    def _get_host_network(self, host):
        """
        Get the network in the ESX

        Args:
            host            (str):   the esx host whose network is to be obtained

        Returns:
            network         (str):   the network in the ESX host

        Raises:
            Exception:
                Raise exception when failed to get network of the ESX

        """
        try:
            import ipaddress
            vms = []
            network_count = {}
            all_vms = self.get_content([self.vim.VirtualMachine])
            for vm in all_vms:
                try:
                    if vm.runtime.host.name == host and vm.runtime.powerState == 'poweredOn':
                        vms.append(vm)
                except (AttributeError, self.vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("Issue with vm: {}. Skipping it".format(vm))
                    continue
            if len(vms) < 3:
                return None
            for vm in vms:
                _ip = vm.summary.guest.ipAddress
                if _ip and len(vm.network) > 0:
                    if ipaddress.ip_address(_ip) and not re.search('^169\.254', _ip):
                        if vm.network[0].name in network_count:
                            network_count[vm.network[0].name] += 1
                        else:
                            network_count[vm.network[0].name] = 1
            for net_name, count in network_count.items():
                if count > 5:
                    return net_name

        except Exception as err:
            self.log.exception("exception raised in GetNetwork")
            raise err

    def _get_required_resource_for_restore(self, vm_list):
        """
        sums up all the memory of needs to be restores(passed as VM list)

        Args:
            vm_list             (list):  list of vm to be restored

        Returns:
            _vm_total_memory    (int):  Total memory required for restoring

            _vm_total_space     (int):  Total disk space required for restoring

        Raises:
            Exception:
                Raise exception when failed to get space and ram of the source vm
        """
        try:
            copy_vm_list = vm_list
            _vm_total_memory = _vm_total_space = 0
            get_all_vms = self.get_content([self.vim.VirtualMachine])
            vms = dict(filter(lambda elem: elem[1] in copy_vm_list, get_all_vms.items()))
            for vm in vms:
                try:
                    space = 0
                    memory = int(vm.summary.config.memorySizeMB / 1024)
                    for _v in vm.storage.perDatastoreUsage:
                        space = space + int(_v.committed / 1024 / 1024 / 1024)
                    _vm_total_memory = _vm_total_memory + memory
                    _vm_total_space = _vm_total_space + space
                except (AttributeError, self.vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("Issue with vm: {}. Skipping it".format(vm))
                    continue
            return _vm_total_memory, _vm_total_space

        except Exception as err:
            self.log.exception(
                "An Error occurred in  _get_required_memory_for_restore ")
            raise err

    def _get_datastore_tree_list(self, datastore):
        """
        Get the free host memory in proxy and arrange them with ascending order

        Args:
            datastore           (str):  Datastore for which we need to find the hierarchy

        Returns:
            tree_list           (dict): Dict contains parent ESX, Cluster, Datacenter for the datastore

        Raises:
            Exception:
                Raise exception when failed to get tree structure for the datastore
        """
        try:
            all_ds = self.get_content([self.vim.Datastore])
            datastores = dict(filter(lambda elem: datastore == elem[1], all_ds.items()))
            for ds in datastores:
                try:
                    tree_list = {'ESX': ds.host[0].key.name,
                                 'Cluster': ds.host[0].key.parent.name,
                                 'Datacenter': ds.parent.parent.name}
                except (AttributeError, self.vmodl.fault.ManagedObjectNotFound, IndexError):
                    self.log.warning("Issue with ds: {}. Skipping it".format(ds))
                    continue
                return tree_list
            self.log.error("Failed to find datastore")

        except Exception as err:
            self.log.exception("An error occurred in  _get_datastore_tree_list ")
            raise err

    def deploy_ova(self, ova_path, vm_name, esx_host, datastore, network, vm_password):
        """
        Deploy the OVA in the vcenter ESX

        Args:
            ova_path        (str):   the path where the OVA file is present

            vm_name         (str):   the name with which the OVA needs to be deployed

            esx_host        (str):   the esx host where the VM is to be deployed

            datastore       (str):   datastore to store the VM

            network         (str):   network to attach the VM to

            vm_password     (str):   the password of the new VM

        Returns:

        """
        try:
            _ps_path = os.path.join(self.utils_path, "DeployOVA.ps1")
            prop_dict = {
                "server_name": self.server_host_name,
                "user": self.user_name,
                "pwd": self.password,
                "ova_path": ova_path,
                "vm_name": vm_name,
                "esx_host": esx_host,
                "datastore": datastore,
                "vm_network": network,
                "vm_pwd": vm_password
            }
            output = self.controller._execute_script(_ps_path, prop_dict)
            exception_list = ["Exception", "Cannot", "login"]
            if any(exp in output.formatted_output for exp in exception_list):
                raise Exception(output.formatted_output)
        except Exception as exp:
            self.log.exception("Something went wrong while deploying OVA. Please check logs.")
            raise Exception(exp)

    def find_vm(self, vm_name):
        """
            Finds the vm and returns its status, ESX and Datastore

            Args:
                vm_name             (str): Name of the VM to be searched

            Returns:
                vm_detail           (list): VM found status, ESX and DS

            Raises:
                Exception:
                    Raise exception when failed to get the status of the vm
            """
        try:
            get_all_vms = self.get_content([self.vim.VirtualMachine])
            vms = dict(filter(lambda elem: vm_name == elem[1], get_all_vms.items()))
            if len(vms) == 0:
                return False, None, None
            if len(vms) == 1:
                for vm in vms:
                    _ds = vm.config.files.logDirectory
                    _ds = _ds[_ds.find("[") + 1:_ds.find("]")]
                    return True, vm.runtime.host.name, _ds
            return 'Multiple', None, None

        except Exception as err:
            self.log.exception("exception raised in finding the vm details")
            raise err

    def find_esx_parent(self, vm_host):
        """
            Finds the parent of the ESX host

            Args:
               vm_host             (str): ESX host to be checked for

            Returns:
               vm_host_detail      (list): ParentId and Parent name

            Raises:
               Exception:
                   Raise exception when failed to get the parent of the vm
            """
        try:
            vm_host_detail = []
            all_esx = self.get_content([self.vim.HostSystem])
            esx_dict = dict(filter(lambda elem: vm_host == elem[1], all_esx.items()))
            for host in esx_dict.keys():
                vm_host_detail = [host.parent._moId, host.parent.name]
            return vm_host_detail
        except Exception as err:
            self.log.exception("exception raised in finding the vm details: {0}".format(err))
            raise err

    def wait_for_tasks(self, tasks):
        """
        Waits till a task if completed
        Args:
            tasks                   (object):   Task to be monitored

        """

        property_collector = self.connection.content.propertyCollector
        task_list = [str(task) for task in tasks]
        obj_specs = [self.vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                     for task in tasks]
        property_spec = self.vmodl.query.PropertyCollector.PropertySpec(type=self.vim.Task,
                                                                        pathSet=[],
                                                                        all=True)
        filter_spec = self.vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pc_filter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            while len(task_list):
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue
                            if not str(task) in task_list:
                                continue
                            if state == self.vim.TaskInfo.State.success:
                                task_list.remove(str(task))
                            elif state == self.vim.TaskInfo.State.error:
                                raise task.info.error
                version = update.version
        finally:
            if pc_filter:
                pc_filter.Destroy()

    def data_store_for_attach_disk_restore(self, host):
        """
        Find the datastore to be used for attach disk restore
        Args:
            host                (string):   ESX where datastore has to be searched

        Returns:
            datastore_name      (string):   Datastore name where restore will happen

        Raises:
               Exception:
                   Raise exception when failed to get the DS

        """
        try:
            datastore_priority_dict = self._get_datastore_dict()
            for each_datastore in datastore_priority_dict.items():
                datastore_name = each_datastore[0]
                tree = self._get_datastore_tree_list(datastore_name)
                if tree['ESX'] == host:
                    self.log.info("Disk is restoring to datastore: {}".format(datastore_name))
                    return datastore_name
            self.log.exception("No Datastore found")
        except Exception as err:
            self.log.exception("exception raised in finding DS: {0}".format(err))
            raise err

    def power_off_all_vms(self):
        """

        Power off all VMs in VMs dictionary

        Raise:
            Exception:
                Raise Exception when fails to power off

        """
        try:
            for vm_name in self.VMs:
                self.VMs[vm_name].power_off()
        except Exception as exp:
            self.log.exception(f"Exception raised in powering off VMs: {exp}")
            raise exp

    def power_on_all_vms(self):
        """

        Power on all VMs in VMs dictionary

        Raise:
            Exception:
                Raise Exception when fails to power on

        """
        try:
            for vm_name in self.VMs:
                self.VMs[vm_name].power_on()
        except Exception as exp:
            self.log.exception(f"Exception raised in powering off VMs: {exp}")
            raise exp

    def check_vms_exist(self, vm_list):
        """

        Check each VM in vm_list exists in Hypervisor VMs Dict

        Args:
            vm_list (list): List of VMs to check

        Returns:
            True (bool): If All VMs are present

            False (bool): If any VM is absent

        """
        if isinstance(vm_list, str):
            vm_list = [vm_list]
        present_vms = self.get_all_vms_in_hypervisor()
        present_vms = set(present_vms)
        if (set(vm_list) & set(present_vms)) == set(vm_list):
            return True
        else:
            return False

    def check_vms_absence(self, vm_list):
        """

        Check VMs in vm_list should not be present in Hypervisor VMs Dict

        Args:

            vm_list (list): If all VMs are not present

        Returns:
            True (bool): If All VMs are absent

            False (bool): If any VM is present

        """
        present_vms = self.get_all_vms_in_hypervisor()
        present_vms = set(present_vms)
        if (set(vm_list) & set(present_vms)) == set():
            return True
        else:
            return False

    def check_ds_exist(self, ds_list):
        """

        Check datastrores if present in the vcenter

        Args:

            ds_list                 (list): List of datastores to be checked in the vcenter

        Returns:
            True (bool): If any of the DS is present in the vcenter

            False (bool): If all DS are not present

        """
        try:
            all_ds = self.get_content([self.vim.Datastore])
            if dict(filter(lambda elem: elem[1] in ds_list, all_ds.items())):
                return True
            return False
        except Exception as err:
            self.log.exception("An error occurred in checking DS list")
            raise err

    def get_proxy_location(self, proxy_ip):
        """
                    Finds the proxy and returns its status, ESX and Datastore

                    Args:
                        proxy_ip             (str): Hostname / Ip of the proxy to be searched

                    Returns:
                        Proxy Status         (bool): Proxy found status

                        Host                 (str): ESX Host of the Proxy

                        Datastore            (str): Datastore of the Proxy

                    Raises:
                        Exception:
                            Raise exception when failed to get the status of the vm
                    """
        try:

            vm = None
            get_all_vms = self.get_content([self.vim.VirtualMachine])
            for elem in get_all_vms.items():
                try:
                    if proxy_ip == elem[0].guest.hostName:
                        vm = elem
                        break
                    elif proxy_ip == elem[0].guest.ipAddress:
                        vm = elem
                except (AttributeError, self.vmodl.fault.ManagedObjectNotFound):
                    self.log.warning("Issue with vm: {}. Skipping it".format(vm.name))
                    continue

            if vm:
                _ds = vm[0].config.files.logDirectory
                _ds = _ds[_ds.find("[") + 1:_ds.find("]")]
                return True, vm[0].runtime.host.name, _ds
            return False, None, None

        except Exception as err:
            self.log.exception("Exception raised in finding the Proxy details")
            raise err

    def get_pbm_connection(self):
        """
        Establish connection to the SPBM service endpoint of the vCenter

        Raises:
            Exception:
                If connection failed
        """
        try:
            vpxd_stub = self.connection._stub
            VmomiSupport.GetRequestContext()["vcSessionCookie"] = vpxd_stub.cookie.split('"')[1]
            hostname = vpxd_stub.host.split(":")[0]
            pbm_stub = SoapStubAdapter(
                host=hostname,
                version="pbm.version.version11",
                path="/pbm/sdk",
                poolSize=0,
                sslContext=ssl._create_unverified_context())
            pbm_si = pbm.ServiceInstance("ServiceInstance", pbm_stub)
            self.pbm_content = pbm_si.RetrieveContent()
            self.profile_manager = self.pbm_content.profileManager
        except Exception as err:
            self.log.exception('SPBM connection failed')
            raise err

    def check_vm_storage_policy_compliance(self, vm_storage_policy, datastore):
        """
        Checks whether the datastore is compatible with the storage policy
        Args:
            vm_storage_policy       (str): Storage Policy

            datastore               (str): Datastore

        Returns:
            True    (bool): If compatibility check passed

            False   (bool): If compatibility check failed

        Raises:
            Exception:
                If there is an exception in checking the storage policy compliance
        """
        # 'Datastore Default' is the default vCenter policy compatible with all the datastores
        if vm_storage_policy == 'Datastore Default':
            return True
        try:
            all_ds = self.get_content([self.vim.Datastore])
            ds = dict(filter(lambda elem: datastore == elem[1], all_ds.items()))
            if len(ds) == 0:
                raise Exception("Datastore not found")
            elif len(ds) == 1:
                # Create placement hub data object for the datastore that has to be checked for compatibility
                ds_obj = next(iter(ds))  # datastore managed object reference
                hub = pbm.placement.PlacementHub()
                hub.hubType = 'Datastore'
                hub.hubId = ds_obj._moId

                # Get the Storage Policy profile managed object reference
                storage_profile = None
                profile_ids = self.profile_manager.PbmQueryProfile(
                    resourceType=pbm.profile.ResourceType(resourceType="STORAGE"),
                    profileCategory="REQUIREMENT")
                if len(profile_ids) > 0:
                    profiles = self.profile_manager.PbmRetrieveContent(profileIds=profile_ids)
                    for profile in profiles:
                        if vm_storage_policy in profile.name:
                            storage_profile = profile

                if not storage_profile:
                    raise Exception('Profile not found')

                # Check the datastore compatibility with the Storage Profile
                compatibility_result = self.pbm_content.placementSolver. \
                    PbmCheckCompatibility(hubsToSearch=[hub], profile=storage_profile.profileId)
                if len(compatibility_result[0].error) == 0:
                    return True
                else:
                    return False
            else:
                raise Exception("Multiple datastores exist with the same name")
        except Exception as err:
            self.log.exception('Exception in storage policy compliance check')
            raise err

    def _validate_snapshot_pruning(self, live_sync_options, replication_group_name=None):
        """
        Validate Snapshot pruning validation

            live_sync_options       (object):   Live sync objects

            replication_group_name (string) :   name of the replication group

            Raises:
             Exception:
                If validation fails
        """
        try:
            auto_commcell_obj = live_sync_options.auto_subclient.auto_commcell
            commcell_obj = auto_commcell_obj.commcell
            vm_list = live_sync_options.auto_subclient.vm_list
            destination_client = live_sync_options.destination_client
            # get control host id of the configured storage array
            control_host_id = auto_commcell_obj.get_control_host_id(replication_group_name)

            # xml to get the snapshot list on the storage array
            deploy_xml = """<?xml version='1.0' encoding='UTF-8'?>
            <EVGui_GetVolumesOfSnapBackupReq jobId="0" copyId="0" clientId="0" controlHostId="{0}"/>""". \
                format(control_host_id)
            # executing qoperation by passing above xml
            snaphots_response = commcell_obj.qoperation_execute(deploy_xml)
            snapshot_jobids = set()
            for response_index in range(len(snaphots_response['listOfVolumes'])):
                snapshot_jobids.add(snaphots_response['listOfVolumes'][response_index]['jobId'])

            snapshot_retention = 3  # default value
            for _vm in vm_list:
                snap_backup_jobids = []

                job_controller_obj = JobController(commcell_obj)
                client_obj = Client(commcell_obj, _vm)
                client_id = int(client_obj.client_id)

                # getting finished job id's
                jobs_details = job_controller_obj.finished_jobs(client_name=destination_client,
                                                                lookup_time=48,
                                                                job_filter='snapbackup',
                                                                job_summary='full',
                                                                limit=100)
                # filtering jobs with client id
                for job_id in jobs_details.keys():
                    if jobs_details[job_id]['subclient']['clientId'] == client_id:
                        snap_backup_jobids.append(int(job_id))

                # getting backup job id's yet to replicate
                pending_backup_jobids = auto_commcell_obj.get_backup_pending_jobs_to_replicate(_vm)

                jobids_exist = []
                jobids_notexist = []

                # logic to get the list of job id's to be there and list of job id's not to be there
                snap_backup_jobids.sort(reverse=True)
                if pending_backup_jobids[0] != '':  # if we are having backup jobs yet to replicate
                    # converting job id's string to int
                    for jobid_index in range(len(pending_backup_jobids)):
                        pending_backup_jobids[jobid_index] = int(pending_backup_jobids[jobid_index])

                    # adding all backup job id's yet to replicate to
                    # the list of snapshot job id's to be present on the storage array
                    for jobid in pending_backup_jobids:
                        jobids_exist.append(jobid)
                        snapshot_retention = snapshot_retention - 1

                for jobid_index in range(len(snap_backup_jobids)):
                    if jobid_index < snapshot_retention:
                        jobids_exist.append(snap_backup_jobids[jobid_index])
                    else:
                        jobids_notexist.append(snap_backup_jobids[jobid_index])

                # validating snapshot job id's to be present on the storage array
                for jobid in jobids_exist:
                    if jobid not in snapshot_jobids:
                        raise Exception(f'snapshot corresponding to jobid:{jobid} is not found on array')
                # validating snapshot job id's not to be present on the storage array
                for jobid in jobids_notexist:
                    if jobid in snapshot_jobids:
                        raise Exception(
                            f'snapshot corresponding to jobid:{jobid} is found on array and should be pruned')
            return True
        except Exception as exp:
            self.log.error(exp)
            raise Exception("Failed to complete snapshot pruning validation.")

    def enable_maintenance_mode(self, esx_hostname):
        """
            Enable maintenance mode on the ESXi host

            Args:
               esx_hostname             (str): ESX host on which maintenance mode is to be disabled

            Raises:
               Exception:
                   Raise exception when failed to enable maintenance mode on the ESXi host
            """
        try:
            all_esx = self.get_content([self.vim.HostSystem])
            esx_dict = dict(filter(lambda elem: esx_hostname == elem[1], all_esx.items()))
            host_obj = list(esx_dict.keys())[0]
            if host_obj.name == esx_hostname:
                for vm_obj in host_obj.vm:
                    vm_obj.PowerOff()
                host_obj.EnterMaintenanceMode(300)
        except Exception as err:
            self.log.exception("exception raised while entering maintenance mode: {0}".format(err))
            raise err

    def disable_maintenance_mode(self, esx_hostname):
        """
            Disable maintenance mode on the ESXi host

            Args:
               esx_hostname             (str): ESX host on which maintenance mode is to be disabled

            Raises:
               Exception:
                   Raise exception when failed to disable maintenance mode on the ESXi host
            """
        try:
            all_esx = self.get_content([self.vim.HostSystem])
            esx_dict = dict(filter(lambda elem: esx_hostname == elem[1], all_esx.items()))
            host_obj = list(esx_dict.keys())[0]
            if host_obj.name == esx_hostname:
                host_obj.ExitMaintenanceMode(300)
        except Exception as err:
            self.log.exception("exception raised while exiting maintenance mode: {0}".format(err))
            raise err

    def enter_standby_mode(self, esx_hostname):
        """
            Enter standby mode on the ESXi host

            Args:
               esx_hostname             (str): ESX host on which standby mode is to be enabled

            Raises:
               Exception:
                   Raise exception when failed to enter standby mode on the ESXi host
            """
        try:
            all_esx = self.get_content([self.vim.HostSystem])
            esx_dict = dict(filter(lambda elem: esx_hostname == elem[1], all_esx.items()))
            host_obj = list(esx_dict.keys())[0]
            if host_obj.name == esx_hostname:
                for vm_obj in host_obj.vm:
                    vm_obj.PowerOff()
                host_obj.EnterStandbyMode(300)
        except Exception as err:
            self.log.exception("exception raised while entering standby mode: {0}".format(err))
            raise err

    def exit_standby_mode(self, esx_hostname):
        """
            Exit standby mode on the ESXi host

            Args:
               esx_hostname             (str): ESX host on which standby mode is to be disabled

            Raises:
               Exception:
                   Raise exception when failed to exit standby mode on the ESXi host
            """
        try:
            all_esx = self.get_content([self.vim.HostSystem])
            esx_dict = dict(filter(lambda elem: esx_hostname == elem[1], all_esx.items()))
            host_obj = list(esx_dict.keys())[0]
            if host_obj.name == esx_hostname:
                host_obj.ExitStandbyMode(300)
        except Exception as err:
            self.log.exception("exception raised while exiting standby mode: {0}".format(err))
            raise err

    def find_datastore_cluster(self, ds_cluster):
        """

        Check if the given datastore cluster is present in the vcenter

        Args:

            ds_cluster       (str): Datastore Cluster

        Returns:
            True/False      (bool):  True if the datastore cluster exists

            ds_list         (list): Datastores part of the Datastore cluster

        """
        try:
            all_ds = self.get_content([self.vim.StoragePod])
            ds_cluster_dict = dict(filter(lambda elem: elem[1] == ds_cluster, all_ds.items()))
            if len(ds_cluster_dict) == 0:
                return False, None
            elif len(ds_cluster_dict) == 1:
                ds_list = None
                for ds_cluster in ds_cluster_dict:
                    ds_list = [_ds.name for _ds in ds_cluster.childEntity]
                return True, ds_list
            return "Multiple", None
        except Exception as err:
            self.log.exception("An error occurred in finding DS cluster")
            raise err

    def find_esx_cluster(self, esx_cluster):
        """

        Check if the given esx cluster is present in the vcenter

        Args:

            esx_cluster      (str): ESX Cluster

        Returns:
            True/False      (bool):  True if the ESX cluster exists

            ds_list         (list): Hosts part of the ESX cluster

        """
        try:
            all_esx = self.get_content([self.vim.ClusterComputeResource])
            esx_cluster_dict = dict(filter(lambda elem: elem[1] == esx_cluster, all_esx.items()))
            if len(esx_cluster_dict) == 0:
                return False, None
            elif len(esx_cluster_dict) == 1:
                esx_list = None
                for esx_cluster in esx_cluster_dict:
                    esx_list = [_esx.name for _esx in esx_cluster.host]
                return True, esx_list
            return "Multiple", None
        except Exception as err:
            self.log.exception("An error occurred in finding ESX cluster")
            raise err

    def get_datastore_from_cluster(self, ds_cluster):
        """
            Gets the Datastore with the most amount of free space from the Datastore cluster
        Args:
            ds_cluster      (str): Datastore Cluster

        Returns:
            ds             (str): Name of the Datastore cluster

        Raises:
            Exception:
                If failed to get a datastore form the cluster
        """
        try:
            all_ds_dict = self._get_datastore_dict()
            ds_cluster_exists, ds_list = self.find_datastore_cluster(ds_cluster)
            if ds_cluster_exists:
                updated_ds_dict = copy.deepcopy(all_ds_dict)
                for _ds, _free_space in all_ds_dict.items():
                    if _ds not in ds_list:
                        del updated_ds_dict[_ds]
                ds = next(iter(updated_ds_dict))
                return ds
        except Exception as err:
            self.log.exception("An error occurred in getting a datastore from cluster")
            raise err

    def get_esx_from_cluster(self, esx_cluster):
        """
            Gets the ESX host with the most amount of free memory from the ESX cluster
        Args:
            esx_cluster      (str): ESX Cluster

        Returns:
            esx             (str): Name of the ESX host

        Raises:
            Exception:
                If failed to get a host form the cluster
        """
        try:
            all_esx_dict = self._get_host_memory()
            esx_cluster_exists, esx_list = self.find_esx_cluster(esx_cluster)
            if esx_cluster_exists:
                updated_esx_dict = copy.deepcopy(all_esx_dict)
                for _ds, _free_space in all_esx_dict.items():
                    if _ds not in esx_list:
                        del updated_esx_dict[_ds]
                esx = next(iter(updated_esx_dict))
                return esx
        except Exception as err:
            self.log.exception("An error occurred in getting an ESX from cluster")
            raise err

    def get_datastore_type(self, esx, ds_name):
        """
        Gets the type of datastore(NFS or VMFS)
        Args:
            esx                     (str):  esx of the datastore

            ds_name                 (str:   datastore name

        Returns:
            Type of datastore VMFS or NFS

        """
        try:
            _esx_objects = self.get_content([self.vim.HostSystem])
            _esx_obj = list(_esx_objects.keys())[list(_esx_objects.values()).index(esx)]
            _storage = _esx_obj.configManager.storageSystem
            sys_vol_mount_info = _storage.fileSystemVolumeInfo.mountInfo
            _ds_vol_type = None
            for vol in sys_vol_mount_info:
                if vol.volume.name == ds_name:
                    _ds_vol_type = vol.volume.type
            return _ds_vol_type
        except Exception as err:
            self.log.exception("An error occurred in getting the type of datastore")
            raise err

    def get_vsphere_client(self):
        """
        Return a vSphere client

        Returns:
            vsphere_client          (object):  vSphere client object
        
        Raises:
            Exception:
                If failed to create a vSphere client
        """
        if self.vsphere_client:
            return
        session = requests.session()
        session.verify = False
        try:
            self.vsphere_client = create_vsphere_client(server=self.server_host_name,
                                                   username=self.user_name,
                                                   password=self.password,
                                                   session=session)
        except Exception as err:
            self.log.exception("An error occurred in creating a vSphere client")
            raise err

    def get_tag_and_category_id(self, tag_name, category_name = None):
        """
        Gets the tag and category id of a given the tag -> category_name:tag_name if category_name is provided
        Else gets the tag id of the first tag with the given tag_name irrespective of the category
        Args:
            tag_name                (str):  Tag name

            category_name (Optional)  (str):  Category name
        
        Returns:
            tag_id                  (str):  Tag id

            category_id             (str):  Category id
        """
        self.get_vsphere_client()
        tags = self.vsphere_client.tagging.Tag.list()
        tag_id, category_id = None, None
        if not category_name:
            for tag_str in tags:
                tag = self.vsphere_client.tagging.Tag.get(tag_str)
                if tag.name == tag_name:
                    tag_id = tag.id
                    category_id = tag.category_id
                    break
            return tag_id, category_id
        for tag_str in tags:
            tag = self.vsphere_client.tagging.Tag.get(tag_str)
            if tag.name == tag_name and self.vsphere_client.tagging.Category.get(tag.category_id).name == category_name:
                tag_id = tag.id
                category_id = tag.category_id
                break
        return tag_id, category_id

    def assign_tag_to_vm(self, tag_name, category_name, moref):
        """
        Assigns the tag -> category_name:tag_name to the VM
        If the tag of the given category does not exist, it will use the create_tag() method to create the tag
        Args:
            tag_name                (str):  Tag name to be added

            category_name           (str):  Category name

            moref                   (str):  Moref of the VM

        Raises:
            Exception:
                If failed to add tag to the VM
        """
        self.get_vsphere_client()
        tag_id, category_id = self.get_tag_and_category_id(tag_name, category_name)
        if not tag_id or not category_id:
            self.log.info(f"Tag {tag_name}:{category_name} not found. Creating the tag")
            tag_id, category_id = self.create_tag(tag_name, category_name)
        dynamic_id = DynamicID(type='VirtualMachine', id=moref)
        try:
            self.vsphere_client.tagging.TagAssociation.attach(tag_id=tag_id, object_id=dynamic_id)
            for tag_str in self.vsphere_client.tagging.TagAssociation.list_attached_tags(dynamic_id):
                tag = self.vsphere_client.tagging.Tag.get(tag_str)
                if tag.id == tag_id:
                    return True
            raise Exception(f"Failed to add tag {tag_name} to VM {moref}")
        except Exception as err:
            raise Exception(f"Error occurred in adding tag {tag_name} to VM {moref}: {err}")
    
    def remove_tag_from_vm(self, tag_name, category_name, moref):
        """
        Removes the tag -> category_name:tag_name from the VM if it exists
        Args:
            tag_name                (str):  Tag name to be removed

            category_name           (str):  Category name

            moref                   (str):  Moref of the VM

        Raises:
            Exception:
                If failed to remove tag from the VM
        """
        self.get_vsphere_client()
        tag_id, category_id = self.get_tag_and_category_id(tag_name, category_name)
        if not tag_id or not category_id:
            self.log.info(f"Tag {tag_name}:{category_name} not found in the vCenter")
            return
        dynamic_id = DynamicID(type='VirtualMachine', id=moref)
        try:
            self.vsphere_client.tagging.TagAssociation.detach(tag_id=tag_id, object_id=dynamic_id)
            for tag_str in self.vsphere_client.tagging.TagAssociation.list_attached_tags(dynamic_id):
                tag = self.vsphere_client.tagging.Tag.get(tag_str)
                if tag.id == tag_id:
                    raise Exception(f"Failed to remove tag {tag_name} from VM {moref}")
            return True
        except Exception as err:
            raise Exception(f"Error occurred in removing tag {tag_name} from VM {moref}: {err}")
    
    def create_tag(self, tag_name, category_name, description = "Tag created via Automation"):
        """
        Creates a tag -> category_name:tag_name if it does not exist in the vCenter
        If the category does not exist, it will use the create_tag_category() method to create the category

        Args:
            tag_name                (str):  Tag name to be created

            category_name           (str):  Category name

        Returns:
            tag_id                  (str):  Tag id

            category_id             (str):  Category id
        
        Raises:
            Exception:
                If failed to create tag
        """
        self.get_vsphere_client()
        tag_id, category_id = self.get_tag_and_category_id(tag_name, category_name)
        if tag_id and category_id:
            self.log.info(f"Tag {tag_name}:{category_name} already exists in the vCenter")
            return tag_id, category_id
        category_id = self.create_tag_category(category_name)
        create_spec = self.vsphere_client.tagging.Tag.CreateSpec()
        create_spec.name = tag_name
        create_spec.category_id = category_id
        create_spec.description = description
        try:
            tag_id = self.vsphere_client.tagging.Tag.create(create_spec)
            self.log.info(f"Tag {tag_name}:{category_name} created in the vCenter")
            return tag_id, category_id
        except Exception as err:
            raise Exception(f"Failed to create tag {tag_name}:{category_name}: {err}")

    def delete_tag(self, tag_name, category_name):
        """
        Deletes a tag -> category_name:tag_name if it exists in the vCenter

        Args:
            tag_name                (str):  Tag name to be deleted

            category_name           (str):  Category name
        
        Raises:
            Exception:
                If failed to delete tag
        """
        self.get_vsphere_client()
        tag_id, category_id = self.get_tag_and_category_id(tag_name, category_name)
        if not tag_id or not category_id:
            self.log.info(f"Tag {tag_name}:{category_name} not found in the vCenter")
            return
        try:
            self.vsphere_client.tagging.Tag.delete(tag_id) 
            self.log.info(f"Tag {tag_name}:{category_name} deleted from the vCenter")
        except Exception as err:
            raise Exception(f"Failed to delete tag {tag_name}:{category_name}: {err}") 

    def create_tag_category(self, category_name, description = "Category created via Automation", cardinality = "SINGLE", associable_types = {"VirtualMachine"}):
        """
        Creates a category with name category_name if it does not exist in the vCenter

        Args:
            category_name           (str):  Category name

            description             (str):  Description of the category
            Default: "Category created via Automation"

            cardinality             (str):  Cardinality of the category
            Default: "SINGLE"

            associable_types        (set of strings): Set of associable types
            Default: {"VirtualMachine"}

        Returns:
            category_id             (str):  Category id
        
        Raises:
            Exception:
                If failed to create category
        """
        self.get_vsphere_client()
        for category_str in self.vsphere_client.tagging.Category.list():
            category = self.vsphere_client.tagging.Category.get(category_str)
            if category.name == category_name:
                self.log.info(f"Category {category_name} already exists")
                return category.id
        create_spec = self.vsphere_client.tagging.Category.CreateSpec()
        create_spec.name = category_name
        create_spec.description = description
        create_spec.cardinality = cardinality
        create_spec.associable_types = associable_types
        try:
            category_id = self.vsphere_client.tagging.Category.create(create_spec)
            self.log.info(f"Category {category_name} created in the vCenter")
            return category_id
        except Exception as err:
            raise Exception(f"Failed to create category {category_name}: {err}")

    def delete_tag_category(self, category_name):
        """
        Deletes the category with name category_name if it exists in the vCenter

        Args:
            category_name           (str):  Category name
        
        Raises:
            Exception:
                If failed to delete category
        """
        self.get_vsphere_client()
        category_id = None
        for category_str in self.vsphere_client.tagging.Category.list():
            category = self.vsphere_client.tagging.Category.get(category_str)
            if category.name == category_name:
                category_id = category.id
                break
        if not category_id:
            self.log.info(f"Category {category_name} not found in the vCenter")
            return
        try:
            self.vsphere_client.tagging.Category.delete(category_id)
            self.log.info(f"Category {category_name} deleted from the vCenter")
        except Exception as err:
            raise Exception(f"Failed to delete category {category_name}: {err}")