# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on hypervsor VM

classes defined:
    Base class:
        vmOperations- Act as base class for all hypervior operations

    Inherited class:
        HyperVOperations - Does all operations on Hyper-V Hypervisor

    HyperVOp:

        revert_snapshot()                        - Reverts the snapshot of a VM

"""

import time
from AutomationUtils import logger, config
from AutomationUtils.machine import Machine
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement


class VmOperations(object):
    """
    Base class for performing all Hypervisor operations

    """
    @staticmethod
    def create_vmoperations_object(inputs):

        """Returns the instance of one of the Subclasses HypervOperations / EsxManagement
        based on the server_type from inputs."""

        if inputs['server_type'] == 'HyperV':
            obj = HyperVOperations(inputs['server_host_name'], inputs['username'], inputs['password'])
        elif inputs['server_type'] == "vCenter":
            obj = EsxManagement(inputs['server_host_name'], inputs['username'], inputs['password'])

        return obj

    def __init__(self,
                 host_machine,
                 user_name,
                 password):
        """
        Initialize common variables for vmOperations
        """
        self.host_machine = host_machine
        self.user_name = user_name
        self.password = password
        self.log = logger.get_log()
        self.config = config.get_config()
        self.machine = Machine(self.host_machine, username=self.user_name, password=self.password)

    def revert_snapshot(self, vm_name, snap_name):
        """ Reverts a given snapshot for a given VM"""

        return self.revert_snapshot(vm_name, snap_name)


class HyperVOperations(VmOperations):
    """
    Main class for performing all operations on Hyperv Hyperviosr

    Methods:
            revert_snapshot()        - Reverts the given snapshot for a vm

            power_on_vm()            - Powers on the hyperV vm

            power_off_vm()           - Powers off the hyperV vm

    """

    def __init__(self,
                 host_machine,
                 user_name,
                 password):
        """
        Initialize Hyper-V Helper class properties
        """

        super(HyperVOperations, self).__init__(host_machine, user_name, password)
        self.machine = Machine(self.host_machine, username=self.user_name, password=self.password)

    def revert_snapshot(self, vm_name=None, snap_name='fresh'):
        """
        To revert the snap of a VM

        Args:

            vm_name         (str)   -- Name of the VM to revert snap

            snap_name       (str)   -- Snap name to revert the VM to
                                        default: 'fresh'

        """
        command = {
            "server_name": self.host_machine,
            "vm_name": vm_name,
            "operation": "RevertSnap",
            "extra_args": snap_name,
            "vhd_name": "$null"
        }

        script_path = self.machine.join_path(
            AUTOMATION_DIRECTORY,
            "VirtualServer",
            "VSAUtils",
            "HyperVOperation.ps1"
        )
        output = self.machine.execute_script(script_path, command)

        if (output.formatted_output == '0') or ("retrying for IP" in output.formatted_output):
            self.log.info('Successfully reverted VM %s to snap %s', vm_name, snap_name)

            # To wait for the machine to come up
            self.log.info('Sleeping for 1 minutes for the machine %s to be up', vm_name)
            time.sleep(60)
        else:
            self.log.error('Failed to Revert VM %s, please check the logs', vm_name)
            raise Exception(f'Failed to Revert VM {vm_name}, please check the logs')

    def power_on_vm(self, vm_name=None):
        """
        Powers on HyperV VM
        Args:
            vm_name         (str)   -- Name of the VM to power on
        """
        command = {
            "server_name": self.host_machine,
            "vm_name": vm_name,
            "operation": "PowerOn",
            "extra_args": "$null",
            "vhd_name": "$null"
        }

        script_path = self.machine.join_path(
            AUTOMATION_DIRECTORY,
            "VirtualServer",
            "VSAUtils",
            "HyperVOperation.ps1"
        )
        attempt = 0
        while attempt < 5:
            attempt = attempt + 1
            output = self.machine.execute_script(script_path, command)
            if "Success" in output.formatted_output:
                self.log.info('VM is powered on successfully')
                return True
            else:
                time.sleep(60)
                self.log.error(" Error occurred : %s" % output.formatted_output)
        raise Exception(f"Error in powering on vm {vm_name}")

    def power_off_vm(self, vm_name=None):
        """
        Powers off HyperV VM
        Args:
            vm_name         (str)   -- Name of the VM to power off
        """
        command = {
            "server_name": self.host_machine,
            "vm_name": vm_name,
            "operation": "PowerOff",
            "extra_args": "$null",
            "vhd_name": "$null"
        }

        script_path = self.machine.join_path(
            AUTOMATION_DIRECTORY,
            "VirtualServer",
            "VSAUtils",
            "HyperVOperation.ps1"
        )
        attempt = 0
        while attempt < 5:
            attempt = attempt + 1
            output = self.machine.execute_script(script_path, command)
            if "Success" in output.formatted_output:
                self.log.info('VM is powered off successfully')
                return True
            else:
                time.sleep(60)
                self.log.error(" Error occurred : %s" % output.formatted_output)
        raise Exception(f"Error in powering off vm {vm_name}")
