# -*- coding: utf-8 -*-

#  --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
#  --------------------------------------------------------------------------

""""helper class for vm related operations in hyperv

    VmManager:


        check_client_revert_snap()       --  Checks whether client exists in commcell and then revert snap on hyperv
                                                     if client exists, then delete it from commcell

        vm_shutdown()                    --  Shutsdown the specified vm in the hyper-v server

        populate_vm_ips_on_client()      --  Populates the vm ip address on given client list and vice versa

"""
import time
from AutomationUtils.machine import Machine
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from Install.install_helper import InstallHelper


class VmManager():
    """ contains helper class for vm related operations on Hyperv"""

    def __init__(self, tc_object):
        self.commcell = tc_object.commcell
        self.log = tc_object.log

    def populate_vm_ips_on_client(self, config_data, clients):
        """Populates vm ip on clients and vice versa

            Args:

                config_data        (tuple)      --      config data containing hyperv details

                                                            Example :
                                                                        "HyperVName": "fr.dd.v",
                                                                        "HyperVUsername": "gb\\admin",
                                                                        "HyperVPassword": "xxxx!12",
                                                                        "VmName": "yy",
                                                                        "VmUsername": "yy\\administrator",
                                                                        "VmPassword": "xxxx!12"


                clients             (list)      --      client name list where vm's ip address needs to be added

            Returns:

                None

            Raises:

                Exception:

                        if input data type is not valid

                        if failed to insert host entry
        """
        if not isinstance(clients, list) or not isinstance(config_data, tuple):
            raise Exception("Input data type is not valid")
        self.log.info(f"Client list got for Ipv4 population : {clients}")
        self.log.info(f"Going to find ip address for vm name : {config_data.VmName}")
        if not config_data.HyperVUsername and not config_data.HyperVPassword:
            hyperv_machine = Machine(machine_name=config_data.HyperVName, commcell_object=self.commcell)
        else:
            hyperv_machine = Machine(machine_name=config_data.HyperVName,
                                     username=config_data.HyperVUsername,
                                     password=config_data.HyperVPassword)
        self.log.info(f"Machine object initialised for hyperv : {config_data.HyperVName}")
        vm_ip = None
        try:
            vm_ip = hyperv_machine.get_vm_ip(vm_name=config_data.VmName)
            if vm_ip is None:
                raise Exception("Initiate Wait exception")
        except Exception:
            self.log.info(f"Waiting for 5Mins and then will retry")
            time.sleep(300)
            vm_ip = hyperv_machine.get_vm_ip(vm_name=config_data.VmName)
        if vm_ip is None:
            raise Exception("Failed to get ip address for the vm")
        # got vm ip. Populate it in controller too
        local_machine = Machine()
        local_machine.remove_host_file_entry(hostname=config_data.VmName)
        local_machine.add_host_file_entry(hostname=config_data.VmName, ip_addr=vm_ip)
        self.log.info("Successfully added Vm's new IP in controller")
        vm_machine_obj = Machine(machine_name=config_data.VmName,
                                 username=config_data.VmUsername, password=config_data.VmPassword)
        for client in clients:
            self.log.info(f"Analysing IP configuration for client - {client}")
            client_obj = self.commcell.clients.get(client)
            client_machine_obj = Machine(machine_name=client_obj, commcell_object=self.commcell)
            client_ip = client_machine_obj.ip_address
            self.log.info(f"Client ipv4 address - {client_ip}")
            self.log.info(f"VM ipv4 address : {vm_ip}")
            self.log.info(f"Client hostname - {client_obj.client_hostname}")
            self.log.info(f"VM hostname - {config_data.VmName}")
            self.log.info(f"Client name - {client_obj.client_name}")
            self.log.info(f"VM name - {config_data.VmName}")
            self.log.info(f"Removing the exisitng ip configuration from hosts file for both client & VM")
            client_machine_obj.remove_host_file_entry(hostname=config_data.VmName)
            vm_machine_obj.remove_host_file_entry(hostname=client_obj.client_name)
            vm_machine_obj.remove_host_file_entry(hostname=client_obj.client_hostname)
            self.log.info(f"Adding the new Ip configuration on hosts file for both client & VM")
            client_machine_obj.add_host_file_entry(hostname=config_data.VmName, ip_addr=vm_ip)
            vm_machine_obj.add_host_file_entry(hostname=client_obj.client_name, ip_addr=client_ip)
            vm_machine_obj.add_host_file_entry(hostname=client_obj.client_hostname, ip_addr=client_ip)
        self.log.info(f"Successfully added vm ips on all clients")

    def check_client_revert_snap(self, hyperv_name, hyperv_user_name, hyperv_user_password, vm_name, snap_name="fresh"):
        """ Checks whether client exists in commcell and then revert snap on hyperv
                                                        if client exists, then delete
                Args:
                    hyperv_name          (str)    --  Hostname of the hyperv machine

                    hyperv_user_name     (str)    -- username to connect to hyperv machine

                    hyperv_user_password (str)    -- password to connect to hyperv machine

                    vm_name              (str)    -- Vm name on which snap has to be reverted

                    snap_name            (str)    -- Name of the snap

                Return:
                    None:

                Exception:
                    if unable to delete client

                    if unable to revert snap

                    if unable to power on VM
        """
        self.log.info("Check whether client name exists in commcell or not")
        cloud_name = vm_name + "_ContentAnalyzer"
        content_analyzer = False
        if self.commcell.clients.has_client(cloud_name):
            content_analyzer = True
            self.log.info("Cloud PseudoClient exists in commcell. Going to delete it")
            self.commcell.clients.delete(cloud_name)
            self.log.info("Cloud PseudoClient delete was success")
        if self.commcell.clients.has_client(vm_name):
            self.log.info("Client exists in commcell. Going to delete it")
            self.log.info("Checking if Content Analyzer is installed on client or not (To decide deletion API)")
            if content_analyzer:
                self.commcell.clients.delete(vm_name)
            else:
                client_obj = self.commcell.clients.get(vm_name)
                job_obj = client_obj.retire()
                job_obj.wait_for_completion()
            self.log.info("Client delete was success")
        self.log.info("Hyperv server : %s", hyperv_name)
        install_obj = InstallHelper(self.commcell)
        self.log.info("Going to revert snap of machine : %s", vm_name)
        install_obj.revert_snap(
            server_name=hyperv_name, username=hyperv_user_name,
            password=hyperv_user_password, vm_name=vm_name, snap_name=snap_name)

    def vm_shutdown(self, hyperv_name, hyperv_user_name, hyperv_user_password, vm_name):
        """ Shutdown the vm on the hyper-v server

            Args:
                hyperv_name          (str)    --  Hostname of the hyperv machine

                hyperv_user_name     (str)    -- username to connect to hyperv machine

                hyperv_user_password (str)    -- password to connect to hyperv machine

                vm_name              (str)    -- Vm name to power off

            Return:
                None:

            Exception:

                if unable to power Off VM
        """
        if not hyperv_user_name and not hyperv_user_password:
            machine = Machine(machine_name=hyperv_name, commcell_object=self.commcell)
        else:
            machine = Machine(hyperv_name, username=hyperv_user_name, password=hyperv_user_password)
        command = {
            "server_name": hyperv_name,
            "vm_name": vm_name,
            "operation": "PowerOff",
            "extra_args": vm_name,
            "vhd_name": "$null"
        }

        script_path = machine.join_path(
            AUTOMATION_DIRECTORY,
            "VirtualServer",
            "VSAUtils",
            "HyperVOperation.ps1"
        )
        output = machine.execute_script(script_path, command)
        if '0' in output.formatted_output:
            self.log.info('Successfully power off VM : %s', vm_name)
        else:
            raise Exception("Unable to Power off the vm")
