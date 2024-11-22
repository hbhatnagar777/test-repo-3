# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on hypervsor

    Methods:
        get_all_vms_in_hypervisor()    - abstract -get all the VMs in that hypervisor

        compute_free_resources()    - compute teh free resource for perfoming restores

"""

import socket
from abc import ABCMeta, abstractmethod
from AutomationUtils import logger
from . import VMHelper, VirtualServerConstants, VirtualServerUtils
from AutomationUtils import machine
from importlib import import_module
from inspect import getmembers, isclass, isabstract


class Hypervisor(object):
    __metaclass__ = ABCMeta
    """
    Base class for performing all Hypervisor operations

    Methods:
         get_all_vms_in_hypervisor()    - abstract -get all the VMs in HYper-V Host

        compute_free_resources()        - compute the hyperv host and destiantion path
                                                    for perfoming restores

    """

    def __new__(cls, server_host_name,
                user_name,
                password,
                instance_type,
                commcell,
                host_machine=None,
                **kwargs):
        """
        Initialize the object based in intstance_type

        server_name (list)  - hypervisor name eg: vcenter name or Hyperv host

        host_machine    (str)  - client of cs where we will execute all hypervisor operations


        """

        instance_helper = VirtualServerConstants.instance_helper(instance_type)
        hh_module = import_module("VirtualServer.VSAUtils.HypervisorHelpers.{}".format(instance_helper))
        classes = getmembers(hh_module, lambda m: isclass(m) and not isabstract(m))
        for name, _class in classes:
            if issubclass(_class, Hypervisor) and _class.__module__.rsplit(".", 1)[-1] == instance_helper:
                return object.__new__(_class)

    def __init__(self,
                 server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):
        """
        Initialize common variables for hypervior
        """
        self.commcell = commcell
        self.instance_type = instance_type
        self.server_list = server_host_name
        self.server_host_name = server_host_name[0] if server_host_name else None
        self.host_machine = host_machine
        self.user_name = user_name
        self.password = password
        self.instance_type = instance_type
        self._VMs = {}
        self.log = logger.get_log()
        self.utils_path = VirtualServerUtils.UTILS_PATH
        self._machine = None
        self.timestamp = None
        """set it to false, if you don't want to power off proxies after use"""
        self.power_off_proxies_flag = True
        self.controller = machine.Machine(socket.gethostbyname_ex(socket.gethostname())[2][0],
                                          self.commcell)

    @property
    def vm_user_name(self):
        """gets the user name of the Vm . it si read only attribute"""

        return self._user_name

    @vm_user_name.setter
    def vm_user_name(self, value):
        """sets the user name of the VM if it is differnt form default"""
        self._user_name = value

    @property
    def vm_password(self):
        """gets the user name of the Vm . it si read only attribute"""

        return self._password

    @vm_password.setter
    def vm_password(self, value):
        """sets the user name of the VM if it is differnt form default"""
        self._password = value

    @property
    def machine(self):
        """
        Gets the machine object for the host machine and sets it in the class
        Returns the host machine object"""
        if not self._machine:
            self._machine = machine.Machine(self.host_machine, self.commcell)
        return self._machine

    @machine.setter
    def machine(self, machine_obj):
        """
        Sets the host machine object for the host machine
        Args:
            machine_obj: machine object of the host machine
        """
        if not isinstance(machine_obj, machine.Machine):
            self._machine = machine.Machine(machine_obj, self.commcell)
        else:
            self._machine = machine_obj

    @property
    def aws_region(self):
        """returns region for aws instance"""
        return self._aws_region

    @aws_region.setter
    def aws_region(self, region):
        """
        sets region for aws instance
        Args:
            region - region of the amazon instance
        """
        self._aws_region = region

    @property
    def VMs(self):
        """Returns List of VMs. It is read onlyt attribute"""
        return self._VMs

    @VMs.setter
    def VMs(self, vm_list):
        """creates VMObject for list of VM passed
        Args:
            vmList    (list) - list of VMs for creating VM object
        """

        try:
            if isinstance(vm_list, list):
                for each_vm in vm_list:
                    self._VMs[each_vm] = VMHelper.HypervisorVM(self, each_vm)

            else:
                self._VMs[vm_list] = VMHelper.HypervisorVM(self, vm_list)
                self.log.info("VMs are %s" % self._VMs)

        except Exception as err:
            self.log.exception(
                "An exception occurred in creating object %s" % err)
            raise Exception(err)

    def to_vm_object(self, vm):
        return VMHelper.HypervisorVM(self, vm)

    @abstractmethod
    def power_on_proxies(self, proxy_ips):
        """
        power on the proxies
        Args:
                proxy_ips  (dict)   - contains the hostname and ips of the proxies
        Returns:
                None
        """
        self.log.info("power on the proxies")

    @abstractmethod
    def power_off_proxies(self, proxy_ips):
        """
        power off the proxies
        Args:
                proxy_ips  (dict)   - contains the hostname and ips of the proxies
        Returns:
                None
        """
        self.log.info("power off the proxies")

    @abstractmethod
    def get_all_vms_in_hypervisor(self, server="", pattern="", c_type=""):
        """
        get all the Vms in Hypervisor

        Args:
                server    (str)    - specific hypervisor Host for which all Vms has to be fetched

                pattern    (str)   - Pattern to fetch the vms

                c_type            (str):  Type of content

        Return:
                Vmlist    (list)    - List of Vms in  in host of Pseudoclient
        """
        self.log.info("get all the VMs in hypervisor class")

    @abstractmethod
    def compute_free_resources(self, proxy_list, vm_list):
        """
        compute the free hosting hypervisor and free space for disk in hypervisor

        Args:
            proxy_list  - list of servers from which best has to be chosen

            vm_list     - list of Vm to be restored

        Return:
                host         (str)    - hypervisor host where vm is to be restored
                                            like esx, resourcegroup,region,hyperv host

                datastore    (str)    - diskspace where vm needs to be restored
                                            like destinationpath,datastore,bucket
        """
        self.log.info(
            "computes the free ESXHost and Datastore in case of VMware")

    def copy_test_data_to_each_volume(self, vm_name, _drive, backup_folder, _test_data_path):
        """
        Copy testdata to each volume in the vm provided

        Args:
            vm_name             (str):  vm to which test data has to be copied

            _drive              (str):  Drive letter where data needs to be copied

            backup_folder       (str):  name of the folder to be backed up

            _test_data_path     (str):  path where testdata needs to be generated

        Raises:
            Exception:
                if it fails to generate testdata or if fails to copy testdata

        """

        try:
            if vm_name not in self.VMs:
                self.VMs = vm_name
            self.VMs[vm_name].copy_test_data_to_each_volume(_drive, backup_folder, _test_data_path)
        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying test data to Vm  ")
            raise err

    def copy_content_indexing_data(self, vm_name, _drive, backup_folder):
        """
        copy testdata to each volume in the vm provided for content indexing


        Args:
                vm_name     (str):   vm to which test data has to be copied

                _drive      (str):   Drive letter where data needs to be copied

                backup_folder(str):  name of the folder to be backed up

        Exception:
                if fails to copy testdata

        """
        try:
            self.VMs[vm_name].copy_content_indexing_data(_drive, backup_folder)
        except Exception as err:
            self.log.exception(
                "An error occurred in  Copying content indexing data to Vm  ")
            raise err

    def update_hosts(self):
        """
        update the Information of Host
        """
        self.log.info("Host Is updated")
