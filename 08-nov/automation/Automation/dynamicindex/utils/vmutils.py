# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


import re

from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.hyperv

SNAP_TYPES = {'standard': 5,
              'production': 3,
              'productiononly': 4}


def load(user: str = None, passw: str = None, domain: str = None, host: str = None,
         proto: str = None, sync_interval: str = None, ssh_port: str = None):
    """
    Read config file and command line to create the configuration.

    Args:
        user: User passed as command line option.
        passw: Password passed as command line option.
        domain: Domain passed as command line option.
        host: Host passed as command line option.
        proto: Protocol passed as command line option.
        sync_interval: Sync interval passed as command line option
        ssh_port: SSH port number passed as command line option
    """

    try:
        configuration = {}
        if user is not None:
            configuration['user'] = user
        if passw is not None:
            configuration['pass'] = passw
        if domain is not None:
            configuration['domain'] = domain
        if host is not None:
            configuration['host'] = host
        if proto is not None:
            configuration['protocol'] = proto
        if ssh_port is not None:
            configuration['ssh_port'] = ssh_port
        if sync_interval is not None:
            configuration['sync_interval'] = sync_interval

        if (user or passw or domain or host) is None:
            credentials = _CONFIG.credentials
            configuration = {'user': credentials.user,
                             'pass': credentials.password,
                             'domain': credentials.domain,
                             'host': credentials.host}

        if (proto or ssh_port or sync_interval) is None:
            options = _CONFIG.options
            configuration['sync_interval'] = options.sync_interval
            configuration['protocol'] = options.protocol
            configuration['ssh_port'] = options.ssh_port

        return configuration
    except KeyError:
        print("Check your config file for hyperv information")
        exit(1)


config = load()


def get_vm(vm_name: str = None):
    """
    Retrieve vm information from hyper-v.

    Args:
        vm_name: Name of the vm. Using * in the vm's name can retrieve info
            of one or more machines. If the vm_name is None, * will be used
            instead, gathering information about all vms in the host which can
            be slow depending on the number of vms.
    Returns:
        Info obtained from remote hyper-v host.
    """
    if vm_name is None:
        vm_name = '*'
    ps_script = 'Get-VM -Name "{}" | Select Name,Id,State,Uptime,ParentSnapshotName | sort Name | \
ConvertTo-Json'.format(vm_name)
    rs = run_ps(ps_script)
    return rs


def list_vm_snaps(vm_name: str):
    """
    List vm snapshots.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Get-VMSnapshot -VMName "{}" | Select Name,ParentSnapshotName,CreationTime,\
ParentSnapshotId,Id | ConvertTo-Json'.format(vm_name)

    rs = run_ps(ps_script)
    return rs


def restore_vm_snap(vm_name: str, snap_name: str):
    """
    Restore virtual machine snapshot.

    Args:
        vm_name: The virtual machine name.
        snap_name: The name of the checkpoint to be restored.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Restore-VMSnapshot -Name "{}" -VMName "{}" -Confirm:$false'.format(snap_name,
                                                                                    vm_name)

    rs = run_ps(ps_script)
    return rs


def remove_vm_snapshot(vm_name: str, snap_name: str,
                       recursive: bool = False):
    """
    Deletes a virtual machine checkpoint.

    Args:
        vm_name: The virtual machine name.
        snap_name: The name of the checkpoint to be deleted.
        recursive: Specifies that the checkpoint’s children
            are to be deleted along with the checkpoint.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Remove-VMSnapshot -VMName "{}" -Name "{}"'.format(vm_name,
                                                                   snap_name)
    if recursive:
        ps_script += " -IncludeAllChildSnapshots"
    ps_script += " -Confirm:$false"

    rs = run_ps(ps_script)
    return rs


def get_snapsshot_type(vm_name: str):
    """
    Get snapshot type from vm.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Get-VM -VMName "{}" | Select CheckpointType | ConvertTo-Json'.format(vm_name)

    rs = run_ps(ps_script)
    return rs


def set_snapshot_type(vm_name: str, snap_type: str):
    """
    Set snapshot type to be created in this vm.

    Args:
        vm_name: The virtual machine name.
        snap_type: The type of the checkpoint to be created.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Set-VM -VMName "{}" -CheckpointType {}'.format(vm_name, snap_type)

    rs = run_ps(ps_script)
    return rs


def create_vm_snapshot(vm_name: str, snap_name: str):
    """
    Create a new snapshot with vm's current state.

    Args:
        vm_name: The virtual machine name.
        snap_name: The name of the checkpoint to be created.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Checkpoint-VM -Name "{}" -SnapshotName "{}" -Confirm:$false'.format(vm_name,
                                                                                     snap_name)

    rs = run_ps(ps_script)
    return rs


def stop_vm(vm_name: str, force: bool = False):
    """
    Stop virtual machine.

    Args:
        vm_name: The virtual machine name.
        force: Whether should force shutdown or not.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Stop-VM -Name "{}"'.format(vm_name)
    if force:
        ps_script += " -Force"

    rs = run_ps(ps_script)
    return rs


def resume_vm(vm_name: str):
    """
    Resume (paused) virtual machine.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Resume-VM -Name "{}"'.format(vm_name)

    rs = run_ps(ps_script)
    return rs


def save_vm(vm_name: str):
    """
    Save (Hibernate) virtual machine state.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Save-VM -Name "{}"'.format(vm_name)

    rs = run_ps(ps_script)
    return rs


def pause_vm(vm_name: str):
    """
    Pause virtual machine.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Suspend-VM -Name "{}"'.format(vm_name)

    rs = run_ps(ps_script)
    return rs


def start_vm(vm_name: str):
    """
    Start virtual machine.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Start-VM -Name "{}"'.format(vm_name)
    rs = run_ps(ps_script)

    return rs


def list_switches():
    """
    List virtual network switches from server.

    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = "Get-VMSwitch | Select Name | ConvertTo-Json"
    rs = run_ps(ps_script)

    return rs


def get_switch(vm_name: str):
    """
    Get current virtual network switch from mv.

    Args:
        vm_name: The virtual machine name.
    Returns:
        Info obtained from remote hyper-v host.
    """
    ps_script = 'Get-VMNetworkAdapter -VMName "{}" | Select VMName, SwitchName | ConvertTo-Json' \
        .format(vm_name)
    rs = run_ps(ps_script)

    return rs


def set_switch(vm_name: str, switch_name: str):
    """
    Set virtual machine's virtual network switch.

    Args:
        vm_name: The virtual machine name.
        switch_name: Switch name as retrieved by get_switch.
    Returns:
        Info about the command execution.
    """
    ps_script = 'Connect-VMNetworkAdapter -VMName "{}" -SwitchName "{}"'.format(vm_name,
                                                                                switch_name)
    rs = run_ps(ps_script)

    return rs


def allow_remote_connection(vm_name: str, username: str, password: str):
    """
    Allows remote connection on the VM present in the target machine
    Args:
        vm_name: The virtual machine name.
        username: username for the login
        password: password to login.
    Returns:
        Info about the command execution.
    """
    ps_script = f"$username = '{vm_name}\\{username}' \n" \
                f"$password = ConvertTo-SecureString '{password}' -AsPlainText -Force \n" \
                "$cred = New-Object System.Management.Automation.PSCredential($username, $password) \n" \
                f"$vmName = '{vm_name}' \n" \
                "$vm = Get-VM -Name $vmName \n" \
                "Invoke-Command -VMName $vm.Name -ScriptBlock { \n" \
                "reg add 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server' " \
                "/v fDenyTSConnections /t REG_DWORD /d 0 /f \n" \
                "reg add 'HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\WinStations\RDP-Tcp' " \
                "/v UserAuthentication /t REG_DWORD /d 0 /f \n" \
                "netsh advfirewall firewall add rule name='Allow RDP' dir=in action=allow protocol=TCP " \
                "localport=3389 \n" \
                "netsh advfirewall firewall add rule name='ICMP Allow incoming V4 echo request' protocol=icmpv4:8," \
                "any dir=in action=allow \n" \
                "netsh advfirewall firewall add rule name='Windows Remote Management' dir=in action=allow " \
                "protocol=TCP localport=5985 \n" \
                "netsh advfirewall firewall set rule group='File and Printer Sharing' new enable=Yes \n" \
                "Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False \n" \
                "winrm quickconfig /quiet \n" \
                "} -credential $cred | convertTo-JSON"
    rs = run_ps(ps_script)
    return rs


def get_ip_address(vm_name: str):
    """
    Gets the IP address for a given VM
    Args:
        vm_name: The virtual machine name.
    Returns:
        dict -  IP address and machine name
    """
    ps_script = f" Get-VM '{vm_name}' | Get-VMNetworkAdapter |" \
                "Select-Object VMName, @{N='IPv4Address';E={$_.IPAddresses -match '\d+\.\d+\.\d+\.\d+'}}|" \
                "ConvertTo-Json"
    rs = run_ps(ps_script)
    return rs


def get_up_time(vm_name: str):
    """
    Gets the total uptime of a given VM in minutes
    Args:
        vm_name(str)    -   Name of the VM
    Returns:
        Info about the command execution
    """
    ps_script = f"(Get-VM {vm_name}).Uptime.TotalMinutes"
    rs = run_ps(ps_script)
    return rs


def vm_reachable(ip_address: str):
    """
    Checks whether the VM is reachable
    Args:
        ip_address(str)    -   IPAddress of the VM
    Returns:
        Info about the command execution
    """
    ps_script = f"Test-Connection -ComputerName {ip_address} -Count 1"
    rs = run_ps(ps_script)
    return rs


def run_ps(ps: str):
    """
    Run powershell script on target machine.

    Args:
        ps: Powershell script to run.
    Returns:
        Response object
    Raises:
        Exception,
            When command execution fails
            When machine os info is not windows
    """
    vm_host = Machine(config['host'], None, config['user'], config['pass'])
    if vm_host.os_info.lower() == "windows":
        command_op = vm_host.execute_command(ps)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '', command_op.exception_message))
        if command_op.exception:
            raise Exception(command_op.exception_code, re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '',
                                                              command_op.exception))
        if isinstance(command_op.formatted_output, str):
            result = command_op.formatted_output.strip()
            result = re.sub(r'\033\[(?:[0-9]{1,3}(?:;[0-9]{1,3})*)?[m|K]', '', result)
        else:
            result = command_op.output.strip()
        return result
    raise Exception("Unsupported Host type detected")
