# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" helper class for Creating, configuring VMs and installing Metallic software on a Metallic Ring

    VMProvisioningHelper:

        __init__()                      --  Initializes User Ring Helper

        start_task                      --  Starts the VM provisioning related tasks for metallic ring

        clone_template_disks             --  Clones the given template VHD to a given specified path

        create_vms                      --  Creates the required VMs

        allow_remote_connection         --  Allows RDP and other permissions to VM for management

        change_hostname                 --  Changes hostname of a VM

        add_to_domain                   --  Adds the VM to a domain

"""
import json
import os
import re
import shutil
import socket
import time
from time import sleep

import hcl2

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.windows_machine import Machine, WindowsMachine
from Install import installer_utils
from Install.install_helper import InstallHelper
from Install.install_validator import InstallValidator
from MetallicRing.Helpers.admin_helper import AdminRingMaintenanceHelper
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Helpers.terraform_helper import TerraformHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils
from cvpysdk.commcell import Commcell
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages, UnixDownloadFeatures, \
    WindowsDownloadFeatures
from dynamicindex.utils import vmutils as vm_host

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class VirtualMachine:

    def __init__(self, vm_name, username, password):
        """
        Initializes the virtual machine class
        """
        self.log = logger.get_log()
        self.username = username
        self.password = password
        self.vm_name = vm_name
        self.host_name = self.get_ip_address()
        self.reach_attempt = 0
        self.log.info("Initializing Virtual machine object")
        while not self.is_vm_reachable():
            if self.reach_attempt > 5:
                raise Exception(f"VM is not reachable on the given hostname/IP - [{self.host_name}]."
                                f"Please check the connection to the VM [{self.vm_name}] and try again")
            self.reach_attempt += 1
            self.log.info(f"Retry Attempt - [{self.reach_attempt}]."
                          f"VM - [{self.vm_name}] is not reachable on the obtained IP [{self.host_name}]. "
                          f"Will sleep and retry in three minutes")
            sleep(180)
            self.host_name = self.get_ip_address()
        self.mach = Machine(self.host_name, commcell_object=None, username=self.username,
                            password=self.password)
        self.reboot_attempt = 0
        self.log.info("Virtual machine initialized successfully")

    def change_hostname(self, new_hostname, domain_name=None):
        """
        changes the hostname of the given machine
        """
        self.log.info(f"Request received to change hostname - {new_hostname}, domain = {domain_name}")
        if self.mach.os_flavour == "Linux":
            self.log.info("This is linux machine. Removing hostfile entry and updating with correct ones")
            self.mach.remove_host_file_entry("localhost")
            self.mach.add_host_file_entry(f"{new_hostname}\t{new_hostname}.{domain_name}\t{new_hostname}.localdomain",
                                          "127.0.0.1")
            self.mach.add_host_file_entry(f"{new_hostname}\t{new_hostname}.{domain_name}\t{new_hostname}.localdomain",
                                          "::1")
            new_hostname = f"{new_hostname}.{domain_name}"
            self.log.info(f"Hostfile entries added successfully. New hostname is {new_hostname}")
        old_hostname = self.mach.get_hostname()
        self.log.info(f"Old Name - [{old_hostname}], New Name - [{new_hostname}]. ")
        if new_hostname == old_hostname or new_hostname in old_hostname:
            self.log.info("Old Name is same as New Name. Hostname change is not required")
            return
        self.mach.change_hostname(new_hostname)
        self.log.info("Hostname changed successfully. Restarting client")
        self.reboot_client()
        self.log.info("Client reboot successful. Sleeping for 2 minutes")
        time.sleep(60 * 2)
        self.log.info("Sleep complete. Hostname change operation complete")

    def add_to_domain(self, domain_name, domain_username, domain_password):
        """
        Adds a VM to a given domain
        Args:
            domain_name(str)    -   name of the domain
            domain_username(str)    -   Username for the VM
            domain_password(str)    -   Password for the VM
        """
        try:
            self.log.info(f"Request received to add machine to domain - {domain_name}")
            if self.mach.os_flavour == "Linux":
                self.log.info("This is unix machine. Removing the old file entry for domain controller")
                self.mach.remove_host_file_entry(domain_name)
                ip_address = socket.gethostbyname(domain_name)
                self.mach.add_host_file_entry(domain_name, ip_address)
                self.log.info(f"Successfully added new host file entry for the DC - [{domain_name}] [{ip_address}]")
            self.mach.add_to_domain(domain_name, domain_username, domain_password)
            self.log.info("Added machine to domain. Restarting the machine")
            self.reboot_client()
            self.log.info("Restart complete. Sleeping for 2 minutes")
            time.sleep(60 * 2)
            self.log.info("Sleep complete")
        except Exception as exp:
            self.log.info(str(exp))
            if cs.WIN_EXP_DOMAIN_ADDED == str(exp) or cs.UNIX_EXP_DOMAIN_ADDED in str(exp):
                self.log.info("Already part of domain. Skipping this step")
                return
            raise exp

    def reboot_client(self):
        """
        Reboots the virtual machine client
        """
        try:
            self.log.info("Request received to reboot client")
            self.mach.reboot_client()
            self.log.info("Machine reboot successful")
        except Exception as exp:
            self.log.info(f"Exception occurred during client reboot - [{exp}]")
            exp_msg = str(exp)
            if cs.EXP_WINRM_REBOOT_ERROR in exp_msg or cs.EXP_WSM_REBOOT_ERROR in exp_msg:
                self.log.info("This is WinRM/WSM exception while executing reboot command which can be safely ignored."
                              "Sleeping for 2 mins post reboot to get the machine initialized")
                sleep(60 * 2)
                self.log.info("Sleep complete")
                return
            up_time = self.get_up_time()
            if up_time > 2:
                raise exp
            self.log.info(f"Machine was rebooted successfully. uptime - {up_time}."
                          f"Ignoring the exception caused. - {exp}")

    def install_software(self, client_name, host_name=None, commcell_obj=None, package=cs.Infra.CS, **kwargs):
        """
        Installs software on a given machine
        Args:
            client_name(str)    -   Name of the client
            host_name(str)      -   Name of the host
            commcell_obj(object)-   Object of commcell class
            package(int)        -   Type of package to be installed
            **kwargs(dict)      -   Dictionary of support arguments
            Supported   -
                webconsole_inputs(dict) -   web console dictionary containing the information for install
                Ex: webconsole_inputs = {
                                            "webServerClientId": "wes01155c1us02"
                                        }
        """
        self.log.info("Install software job started")
        if host_name is None:
            host_name = self.host_name
        machine = Machine(
            machine_name=host_name,
            username=self.username,
            password=self.password)
        install_helper = InstallHelper(commcell_obj, machine_obj=machine)
        service_pack = _CONFIG.install_options.ServicePack
        _cs_password = _CONFIG.commserv.encrypted_password
        install_inputs = {
            "csClientName": commcell_obj.commserv_name if commcell_obj is not None else client_name,
            "csHostname": commcell_obj.commserv_hostname if commcell_obj is not None else client_name,
            "commservePassword": _cs_password,
            "instance": "Instance001",
            "oem_id": kwargs.get("oem_id", 119)
        }
        self.log.info(f"Install Inputs - [{install_inputs}]")
        if package == cs.Infra.CS:
            self.log.info("This is CS install")
            if machine.check_registry_exists(cs.REG_SECTION_SESSION, cs.REG_KEY_CVD_PORT):
                install_helper.uninstall_client(delete_client=False)
            self.log.info("Determining Media Path for Installation")
            _service_pack = service_pack
            self.log.info(f"Starting CS Installation. Install inputs - [{install_inputs}]")
            install_helper.install_commserve(install_inputs=install_inputs, feature_release=_service_pack)
            self.log.info("Installation complete. Will perform login post 5 mins")
            time.sleep(60 * 5)
        elif package == cs.Infra.MA:
            self.log.info("This MA install request")
            job_obj = install_helper.install_software([host_name], features=["MEDIA_AGENT"],
                                                      username=self.username, password=self.password, **kwargs)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Install Software Job Successful")
            else:
                self.log.error("Install job failed")
        elif package == cs.Infra.WS:
            self.log.info("This web server install request")
            install_helper.silent_install(
                client_name=client_name,
                tcinputs=install_inputs, feature_release=service_pack, packages=['WEB_SERVER'])
        elif package == cs.Infra.WC:
            self.log.info("This webconsole install request")
            job_obj = install_helper.install_software([host_name], features=["WEB_CONSOLE"],
                                                      username=self.username, password=self.password, **kwargs)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Install Software Job Successful")
            else:
                self.log.error("Install job failed")
        elif package == cs.Infra.IS:
            self.log.info("This is Index server install request")
            job_obj = install_helper.install_software([host_name], features=["INDEX_STORE"],
                                                      username=self.username, password=self.password, **kwargs)
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Install Software Job Successful")
            else:
                self.log.error("Install job failed")
        elif package == cs.Infra.NWP:
            self.log.info("This Network proxy install request")
            media_path = _CONFIG.install_options.MediaPath
            if "{sp_to_install}" in media_path:
                _service_pack = service_pack.split('_')[0] if '_' in service_pack else service_pack
                _service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
                media_path = media_path.replace("{sp_to_install}", _service_pack_to_install)
            install_inputs["mediaPath"] = media_path
            install_helper.silent_install(
                client_name=client_name,
                tcinputs=install_inputs, feature_release=service_pack, packages=["FILE_SYSTEM"])
            self.log.info("Network proxy install complete")

    def get_ip_address(self):
        """
        Gets the IP address for a given VM
        """
        self.log.info(f"Trying to get IP address for VM [{self.vm_name}]")
        resp = vm_host.get_ip_address(self.vm_name)
        json_data = json.loads(resp)
        ip_address = json_data.get("IPv4Address", None)
        if ip_address is None:
            raise Exception("IP address is empty. Please make sure the VM has proper IP address assigned")
        self.log.info(f"IPV4 address response acquired is [{ip_address}]")
        return ip_address

    def get_up_time(self):
        """
        Gets the Uptime for a given VM
        """
        self.log.info(f"Request received to get the up time of the VM [{self.vm_name}]")
        resp = vm_host.get_up_time(self.vm_name)
        if resp.status_code != 0:
            raise Exception(f"Failed to obtain IP address for VM [{self.vm_name}]. [{resp.std_err}]")
        self.log.info("IPV4 address response successful")
        string = resp.std_out.decode().strip()
        uptime = int(float(string))
        self.log.info(f"Total uptime of VM in minutes = [{uptime}]")
        return uptime

    def is_vm_reachable(self):
        """
        Checks whether the given VM is reachable
        """
        self.log.info(f"Checking if VM [{self.vm_name}] is reachable. [{self.host_name}]")
        vm_host.vm_reachable(self.host_name)
        self.log.info(f"VM - [{self.vm_name}] is reachable. IP obtained is - [{self.host_name}]")
        return True


class VMProvisioningHelper(BaseRingHelper):
    """ helper class for Creating, configuring VMs and installing Metallic software on a Metallic Ring"""

    def __init__(self, cs_installed=False, host_type=cs.VMHost.HYPERV):
        """
        Initializes VM provisioning helper
        """
        super().__init__(ring_commcell=None)
        self.log.info("Initializing VM provisioning Helper")
        self.host_type = host_type
        if self.host_type == cs.VMHost.HYPERV:
            self._HOST_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.hyperv
        windows_cred = self._HOST_CONFIG.disk_images.windows_os.credentials
        linux_cred = self._HOST_CONFIG.disk_images.RHEL_os.credentials
        self.win_username = windows_cred.username
        self.unix_username = linux_cred.username
        self.win_pwd = windows_cred.password
        self.unix_pwd = linux_cred.password
        self.host = self._HOST_CONFIG.credentials.host
        self.username = self._HOST_CONFIG.credentials.user
        self.password = self._HOST_CONFIG.credentials.password
        self.domain = self._HOST_CONFIG.credentials.domain
        self.ring_id = RingUtils.get_ring_string(_CONFIG.id)
        self.region = _CONFIG.region
        self.local_machine = Machine()
        ring_suffix_name = f"{self.ring_id}{self.region}"
        self.cs_01_name = f"cms01{ring_suffix_name}"
        self.ws_01_name = f"wes01{ring_suffix_name}"
        self.wc_01_name = f"wec01{ring_suffix_name}"
        self.np_01_name = f"nwp01{ring_suffix_name}"
        self.ma_01_name = f"mas01{ring_suffix_name}"
        self.cs_hostname = f"{self.cs_01_name}.{_CONFIG.domain.name}"
        self.ma_hostname = f"{self.ma_01_name}.{_CONFIG.domain.name}"
        self.ws_hostname = f"{self.ws_01_name}.{_CONFIG.domain.name}"
        self.wc_hostname = f"{self.wc_01_name}.{_CONFIG.domain.name}"
        self.np_hostname = f"{self.np_01_name}.{_CONFIG.domain.name}"
        self.commcell = None
        if cs_installed:
            self.commcell = Commcell(self.cs_hostname, commcell_username=_CONFIG.commserv.username,
                                     commcell_password=_CONFIG.commserv.password)
        self.vm_host_mach = WindowsMachine(self.host, commcell_object=None, username=self.username,
                                           password=self.password)
        vm_host.config = vm_host.load(self.username, self.password, self.domain, self.host)
        self.hyperv_config_path = cs.HYPERV_CONFIG_FILE_PATH % self.ring_id
        self.terraform_helper = TerraformHelper(self.hyperv_config_path, self.host_type, self.username, self.password)
        tf_dir = os.path.dirname(self.hyperv_config_path)
        if not os.path.exists(tf_dir):
            os.makedirs(tf_dir)
        self.cs_machine = None
        self.ma_machine = None
        self.ws_machine = None
        self.wc_machine = None
        self.np_machine = None
        self.terraform_init_attempt = 0
        self.max_attempt = 5
        self.log.info("VM provisioning helper initialized")

    def start_task(self):
        """
        Starts the user related tasks for metallic ring
        """
        try:
            self.log.info("Starting metallic VM provisioning tasks")
            self.allow_terraform_provider()
            self.create_terraform_vms()
            self.configure_VMs()
            self.install_CS_software()
            self.install_MA_software()
            self.install_WS_software()
            self.install_WC_software()
            self.install_NP_software()
            self.status = cs.PASSED

        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def install_CS_software(self):
        """Installs the required software in the Ring VMs"""
        try:
            self.log.info("Request received to install Commserve Software. Initializing CS machine")
            self.cs_machine = VirtualMachine(self.cs_01_name, username=self.win_username, password=self.win_pwd)
            self.log.info("Starting CS install")
            self.cs_machine.install_software(self.cs_01_name, self.cs_hostname, commcell_obj=None, package=cs.Infra.CS)
            self.log.info("Login to Commcell after CS Installation")
            try:
                self.log.info("Trying to login to CS")
                self.commcell = Commcell(self.cs_hostname, commcell_username=_CONFIG.commserv.username,
                                         commcell_password=_CONFIG.commserv.password)
            except Exception:
                self.log.info("CS login failed. Sleeping for 20 minutes")
                time.sleep(1200)
                self.commcell = Commcell(self.cs_hostname, commcell_username=_CONFIG.commserv.username,
                                         commcell_password=_CONFIG.commserv.password)
                self.log.info("Commcell object initialized")
            self.log.info("Checking Readiness of the CS machine")
            commserv_client = self.commcell.commserv_client
            if commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")
            admin_helper = AdminRingMaintenanceHelper(self.commcell)
            admin_helper.update_download_settings()
            self.log.info("Starting download software job")
            job_obj = self.commcell.download_software(
                options=DownloadOptions.LATEST_HOTFIXES.value,
                os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                self.log.error("Download job failed")
            self.log.info("Starting Install Validation")
            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]
            install_validation = InstallValidator(commserv_client.client_hostname, commcell_object=self.commcell,
                                                  machine_object=self.cs_machine.mach, package_list=package_list,
                                                  oem_id=119)
            install_validation.validate_install()
            self.log.info("Install validation successful. CS install is complete")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def install_MA_software(self):
        """Installs the required software in the Ring VMs"""
        try:
            self.log.info("Request received to install media agent Software. Initializing MA machine")
            self.ma_machine = VirtualMachine(self.ma_01_name, username=self.win_username, password=self.win_pwd)
            self.log.info("VM initialized. Starting install")
            self.ma_machine.install_software(self.ma_01_name, self.ma_hostname, commcell_obj=self.commcell,
                                             package=cs.Infra.MA)
            self.log.info("Install complete")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def install_WS_software(self):
        """Installs the required software in the Ring VMs"""
        try:
            self.log.info("Request received to install Web server Software. Initializing web server machine")
            self.ws_machine = VirtualMachine(self.ws_01_name, username=self.win_username, password=self.win_pwd)
            self.log.info("Web server initialized")
            self.ws_machine.install_software(self.ws_01_name, self.ws_hostname, commcell_obj=self.commcell,
                                             package=cs.Infra.WS)
            self.log.info("Web server software installed successfully")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def install_WC_software(self):
        """Installs the required software in the Ring VMs"""
        try:
            self.log.info("Request received to install webconsole Software. Initializing WC machine")
            webconsole_inputs = {"webServerClientId": self.ws_01_name}
            self.wc_machine = VirtualMachine(self.wc_01_name, username=self.win_username, password=self.win_pwd)
            self.log.info(f"Webconsole machine initialized. Starting install. Webserver - {webconsole_inputs}[]")
            self.wc_machine.install_software(self.wc_01_name, self.wc_hostname, commcell_obj=self.commcell,
                                             package=cs.Infra.WC, webconsole_inputs=webconsole_inputs)
            self.log.info("Web console install complete")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def install_NP_software(self):
        """Installs the required software in the Ring VMs"""
        try:
            self.log.info("Request received to install network proxy Software. Initializing network proxy machine")
            self.np_machine = VirtualMachine(self.np_01_name, username=self.unix_username, password=self.unix_pwd)
            self.log.info("VM initialized. Starting install softeare")
            self.np_machine.install_software(self.np_01_name, self.np_hostname, commcell_obj=self.commcell,
                                             package=cs.Infra.NWP)
            self.log.info("Install software complete. Updating network proxy settings")
            np = self.commcell.clients.get(self.np_01_name)
            np_nw = np.network
            np_nw.configure_network_settings = True
            np_nw.tunnel_connection_port = 443
            np_nw.proxy = True
            self.log.info("Network proxy settings complete")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def allow_terraform_provider(self):
        """
        Enables remote execution of terraform commands in a Hyperv machine
        """
        """Performs configurations in the hyperv host to allow uploading shell script"""
        cmd = "Enable-WindowsOptionalFeature -Online -FeatureName:Microsoft-Hyper-V -All -NoRestart;" \
              "Enable-PSRemoting -SkipNetworkProfileCheck -Force;" \
              "winrm set winrm/config/service/auth '@{Basic=\"true\"}';"\
              "Set-WSManInstance WinRM/Config/WinRS -ValueSet @{MaxMemoryPerShellMB = 1024};" \
              "Set-WSManInstance WinRM/Config -ValueSet @{MaxTimeoutms=1800000};" \
              "Set-WSManInstance WinRM/Config/Client -ValueSet @{TrustedHosts='*'};" \
              "Set-WSManInstance WinRM/Config/Service/Auth -ValueSet @{Negotiate = $true};" \
              "$PubNets = Get-NetConnectionProfile -NetworkCategory Public -ErrorAction SilentlyContinue;" \
              "foreach ($PubNet in $PubNets) {" \
              "Set-NetConnectionProfile -InterfaceIndex $PubNet.InterfaceIndex -NetworkCategory Private" \
              "};" \
              "Set-WSManInstance WinRM/Config/Service -ValueSet @{AllowUnencrypted = $true};" \
              "foreach ($PubNet in $PubNets) {" \
              "Set-NetConnectionProfile -InterfaceIndex $PubNet.InterfaceIndex -NetworkCategory Public" \
              "};" \
              "Get-ChildItem wsman:\\localhost\\Listener\\ | Where-Object -Property Keys -eq " \
              "'Transport=HTTP' | Remove-Item -Recurse;" \
              "New-Item -Path WSMan:\\localhost\\Listener -Transport HTTP -Address * -Force -Verbose;" \
              "Restart-Service WinRM -Verbose;" \
              "New-NetFirewallRule -DisplayName 'Windows Remote Management (HTTP-In)' -Name 'WinRMHTTPIn' " \
              "-Profile Any -LocalPort 5985 -Protocol TCP -Verbose;"
        command_op = self.vm_host_mach.execute_command(cmd)
        if command_op.exception_message:
            raise Exception(command_op.exception_code,
                            command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)

    def configure_VMs(self):
        """
        Configures the VMs for the ring
        """
        try:
            self.log.info("Request received to configure VMs")
            self.configure_VM(self.cs_01_name, self.win_username, self.win_pwd,
                              domain=_CONFIG.domain.name, d_username=_CONFIG.domain.username,
                              d_password=_CONFIG.domain.password)
            self.configure_VM(self.ma_01_name, self.win_username, self.win_pwd,
                              domain=_CONFIG.domain.name, d_username=_CONFIG.domain.username,
                              d_password=_CONFIG.domain.password)
            self.configure_VM(self.ws_01_name, self.win_username, self.win_pwd,
                              domain=_CONFIG.domain.name, d_username=_CONFIG.domain.username,
                              d_password=_CONFIG.domain.password)
            self.configure_VM(self.wc_01_name, self.win_username, self.win_pwd,
                              domain=_CONFIG.domain.name, d_username=_CONFIG.domain.username,
                              d_password=_CONFIG.domain.password)
            self.configure_VM(self.np_01_name, self.unix_username, self.unix_pwd,
                              domain=_CONFIG.domain.name, d_username=_CONFIG.domain.username,
                              d_password=_CONFIG.domain.password, os_type=cs.OSType.LINUX)
            self.log.info("VMs configured successfully")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def create_terraform_vms(self):
        """
        Creates a VM with a given name
        """
        try:
            self.terraform_helper.cleanup_terraform_config()
            self.allow_terraform_provider()
            self.log.info("Request received to create VMs")
            if self.host_type == cs.VMHost.HYPERV:
                self.log.info("Host type is Hyperv")
                with open(cs.HYPERV_CONFIG_TEMPLATE_FILE_PATH, "r") as template_config_file:
                    hcl_config = hcl2.load(template_config_file)
                for provider in hcl_config.get("provider", []):
                    hyperv = provider.get("hyperv", {})
                    hyperv["host"] = self.host
                for resource in hcl_config.get("resource", []):
                    resource_instance = resource["hyperv_machine_instance"]
                    commserv01 = resource_instance.get("commserver01")
                    if commserv01 is not None:
                        self.update_resource_info(commserv01, self.cs_01_name)
                        continue
                    media_agent01 = resource_instance.get("mediaagent01")
                    if media_agent01 is not None:
                        self.update_resource_info(media_agent01, self.ma_01_name)
                        continue
                    web_server01 = resource_instance.get("webserver01")
                    if web_server01 is not None:
                        self.update_resource_info(web_server01, self.ws_01_name)
                        continue
                    command_center01 = resource_instance.get("commandcenter01")
                    if command_center01 is not None:
                        self.update_resource_info(command_center01, self.wc_01_name)
                        continue
                    network_proxy01 = resource_instance.get("networkproxy01")
                    if network_proxy01 is not None:
                        self.update_resource_info(network_proxy01, self.np_01_name, cs.OSType.LINUX)
                        continue
                with open(self.hyperv_config_path, "wb") as config_file:
                    data_bytes = json.dumps(hcl_config).encode()
                    config_file.write(data_bytes)
                    self.log.info("Updated the config file")
                self.log.info("Executing terraform configuration")
                self.execute_terraform_config()
                self.log.info("Terraform VMs created successfully")
                self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute VM Provisioning helper. Exception - [{exp}]"
            self.log.info(self.message)
            self.status = cs.FAILED
        return self.status, self.message

    def execute_terraform_config(self):
        """
        Executes the given terraform config file
        """
        self.terraform_helper.execute_terraform_config()

    def update_resource_info(self, resource, name, os_type=cs.OSType.WINDOWS):
        """
        Updates a given resource dictionary with the name and path provided
        """
        self.log.info("Request received to update terraform resources")
        path = f"{self._HOST_CONFIG.cloned_disk_path}\\{self.ring_id}\\{name}\\template.vhdx"
        resource["name"] = name
        for hard_disk in resource.get("hard_disk_drives", []):
            hard_disk["path"] = path
        self.log.info("Resource updated successfully. Cloning disks")
        if os_type == cs.OSType.WINDOWS:
            self.clone_template_disks(self._HOST_CONFIG.disk_images.windows_os.template, path)
        elif os_type == cs.OSType.LINUX:
            self.clone_template_disks(self._HOST_CONFIG.disk_images.RHEL_os.template, path)
        self.log.info("Resource info updated")

    def clone_template_disks(self, source, destination):
        """
        Clones the given template VHD to a given specified path
        Args:
            source(str)         --  Path to where the template VHD is present in the VM host
            destination(str)    --  Path to where the template VHD has to be copied in the VM host
        """
        self.log.info(f"Copying template disk from  [{source}] to [{destination}]")
        self.vm_host_mach.copy_file_locally(source, destination)
        self.log.info("Copy disk complete")

    def configure_VM(self, vm_name, username, password, **kwargs):
        """
        Configures a VM by changing the hostname and adding it to domain
        """
        self.log.info(f"Configure VM request. VM name - [{vm_name}]")
        os_type = kwargs.get("os_type", cs.OSType.WINDOWS)
        hostname = kwargs.get("new_hostname", vm_name)
        domain_name = kwargs.get("domain", None)
        domain_username = kwargs.get("d_username", None)
        domain_password = kwargs.get("d_password", None)
        if os_type != cs.OSType.LINUX:
            self.log.info("Allowing remote connection on VM")
            self.allow_remote_connection(vm_name, username, password)
            self.log.info("Remote connection allowed successfully")
        machine = VirtualMachine(vm_name, username=username, password=password)
        machine.change_hostname(hostname, domain_name)
        self.log.info("Hostanme changed successfully. Attempting to change domain name")
        machine = VirtualMachine(vm_name, username=username, password=password)
        machine.add_to_domain(domain_name=domain_name, domain_username=domain_username,
                              domain_password=domain_password)
        self.log.info("Domain name updated successfully")

    def allow_remote_connection(self, vm_name, username, password):
        """
        Allows remote connection on a given VM
        """
        self.log.info(f"Attempting to allow remote connection on VM - [{vm_name}]")
        vm_host.allow_remote_connection(vm_name, username, password)
        self.log.info(f"Remote connection for VM [{vm_name}] allowed successfully")

