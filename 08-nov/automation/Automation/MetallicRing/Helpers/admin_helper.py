# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing admin tasks in Metallic Ring

    AdminRingMaintenanceHelper:

        __init__()                              --  Initializes Admin Ring Maintenance Helper

        start_task                              --  Starts the administrative tasks for metallic ring

        update_download_settings                --  Updates the download settings of the ring commcell

        disable_schedules                       --  Disables the schedules in commcell

        download_software                       --  Performs download software operation in the commcell

        schedule_download                       --  Schedules download software job in the commcell

        sync_software                           --  Syncs software cache across all the clients in the commcell

        install_updates                         --  Installs latest updates in the commcell and the clients

        schedule_install_updates                --  Schedules install update software job in the commcell


    AdminRingSystemHelper:

        __init__()                              --  Initializes Admin Ring Helper

        start_task                              --  Starts the administrative tasks for metallic ring

        restart_wc_service                      --  Restart tomcat service on webconsole machine

        update_web_console_certificate          --  Updates web console certificate on the webconsole machines

        update_metallic_brand_registry          --  Updates metallic brand registry for the commcell

        set_ring_clients_display_name           --  sets the display name for all clients in the commcell ring
                                                    based on the information provided in the metallic configuration file

        update_client_dn                        --  Updates the display name for a given client based on the region,
                                                    ring name and infrastructure type

        add_web_domains                         --  Adds web domains on the commcell

        disable_ipv6_for_web_console            --  Disables IPV6 on the webconsole machines

        __set_client_dn                         --  Sets the display name for a given client name


    CustomAdminRingSystemHelper

        set_ring_clients_display_name           --  Changes only the commcell client's display name for uniformity
                                                    across all service commcells

        update_network_proxy_settings           --  Skips updating the network proxy settings

"""
import os.path
import time
import xml.etree.ElementTree as ET
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from Install.install_helper import InstallHelper
from MetallicRing.Core.db_helper import DBQueryHelper
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils
from cvpysdk.constants import OSType
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_METRICS_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.metrics_commcell


class AdminRingMaintenanceHelper(BaseRingHelper):
    """ contains helper class for performing administrative tasks in the ring commcell"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.job_management = self.commcell.job_management
        self.cs_client = self.commcell.commserv_client
        self.db_query_helper = DBQueryHelper(ring_commcell)
        self.install_helper = InstallHelper(self.commcell)

    def start_task(self):
        """Starts the administrative tasks for metallic ring"""
        try:
            self.log.info("Starting the admin task for metallic ring configuration")
            self.log.info("Updating download settings")
            self.update_download_settings()
            self.log.info("Updated download settings. Disabling system schedules")
            self.disable_schedules(cs.SCHEDULE_LIST)
            self.log.info("Disabled system schedules. Starting download software job")
            self.download_software()
            self.log.info("Download software job complete. Creating automatic schedules for download software job")
            self.schedule_download()
            self.log.info("Automatic schedules for download software created. Starting sync software job")
            self.sync_software()
            self.log.info("Sync software job completed. Starting to install updates")
            self.install_updates()
            self.log.info("Install updates job completed. Scheduling install updates")
            self.schedule_install_updates()
            self.log.info("Install updates job completed.")
            self.log.info("All Admin tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute admin helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def update_metallic_brand_registry(self):
        """
        Updates OEM ID of the Commcell to Metallic OEM
        """
        cs_machine = Machine(self.cs_client)
        if cs_machine.check_registry_exists("", cs.OEM_REGISTRY):
            self.log.info(f'Registry is already set [{cs.OEM_REGISTRY}]. '
                          f'Updating the value [{cs.METALLIC_OEM}]')
            cs_machine.update_registry("", cs.OEM_REGISTRY, cs.METALLIC_OEM, "DWORD")
            self.log.info(f'OEM set to [{cs.METALLIC_OEM}] successfully')
        else:
            self.log.info(f'Registry [{cs.OEM_REGISTRY}] is not present.')
            cs_machine.create_registry("", cs.OEM_REGISTRY, cs.METALLIC_OEM, "DWORD")
            self.log.info(f'Created new registry [{cs.OEM_REGISTRY}] with value [{cs.METALLIC_OEM}].')

    def update_download_settings(self):
        """
        Updates the download update software settings for a given commcell
        """
        self.log.info("Request received to update download software settings")
        for global_param in _CONFIG.global_param:
            value = global_param.value
            if global_param.key == cs.GP_VB_LEVEL_KEY:
                value = cs.VisibilityLevel.CLOUD.value if self.commcell.commserv_client.service_pack in ('3401', '3201') \
                    else cs.VisibilityLevel.SOFTWARE.value
            request_json = {
                "name": global_param.key,
                "value": str(value),
            }
            self.commcell._set_gxglobalparam_value(request_json)
        self.log.info("Download software settings updated successfully. Updating the visibility level")
        self.log.info("Visibility level updated successfully. Restarting commcell services")
        cc_obj = self.commcell.commserv_client
        cc_obj.restart_services()
        self.log.info("Restart of Commcell services complete. Updated download settings successfully")

    def disable_schedules(self, schedule_list):
        """
        Disables system created schedules
        Arguments:
            schedule_list       --      List of schedule names to be disabled
        """
        self.log.info(f'Request received to disable the following system schedules - [{schedule_list}]')
        for schedule in schedule_list:
            if self.commcell.schedules.has_schedule(schedule):
                schedule_obj = self.commcell.schedules.get(schedule)
                schedule_obj.disable()
                self.log.info(f"Schedule - [{schedule}] disabled successfully")
            else:
                self.log.info(f"Schedule - [{schedule}] is not present in the commcell")

    def download_software(self):
        """
        Downloads the latest hotfixes for the current service pack
        """
        if self.ring.container_provision is True:
            self.log.info("Skipping Downloading packages job for container provisioning")
            return
        job = self.commcell.download_software(options=DownloadOptions.LATEST_HOTFIXES.value,
                                              os_list=[DownloadPackages.UNIX_LINUX64.value,
                                                       DownloadPackages.WINDOWS_64.value])
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run download job with error: " + job.delay_reason
            )
        if job.status == "Completed w/ one or more errors":
            raise Exception("Job Completed with one or more errors please check the logs")
        self.log.info("Successfully finished Downloading packages")

    def schedule_download(self):
        """
        Schedules download software job on the commcell
        """
        sched_name = cs.SCHEDULE_DOWNLOAD_SOFTWARE_JSON["schedule_name"]
        if not self.commcell.schedules.has_schedule(sched_name):
            self.commcell.download_software(options=DownloadOptions.LATEST_HOTFIXES.value,
                                            os_list=[DownloadPackages.UNIX_LINUX64.value,
                                                     DownloadPackages.WINDOWS_64.value],
                                            schedule_pattern=cs.SCHEDULE_DOWNLOAD_SOFTWARE_JSON)
            self.log.info(f"Schedule with given name [{sched_name}] created successfully")
        else:
            self.log.info(f"Schedule with given name [{sched_name}] already exists")

    def sync_software(self):
        """
        Syncs remote software cache
        """
        if self.ring.container_provision is True:
            self.log.info("Skipping Sync packages job for container provisioning")
            return
        job_obj = self.commcell.sync_remote_cache()
        if not job_obj.wait_for_completion():
            self.log.info("Sync software job failed. Details: %s", job_obj.delay_reason)
        else:
            self.log.info("Sync software job completed successfully")

    def install_updates(self):
        """
        Installs updates on all the client computers in the commcell
        Raises:
            Exception:
                If install updates job fails with an error
        """
        if self.ring.container_provision is True:
            self.log.info("Skipping install updates for container provisioning")
            return
        job = self.commcell.push_servicepack_and_hotfix(
            all_client_computers=True,
            reboot_client=True,
            run_db_maintenance=False
        )
        self.log.info("Job %s started for Installing packages", job.job_id)
        try:
            job.wait_for_completion(timeout=180)
        except Exception:
            self.install_helper.wait_for_services()
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run Install job with error: " + job.delay_reason
            )
        if job.status == "Completed w/ one or more errors":
            raise Exception("Job Completed with one or more errors please check the logs")
        self.log.info("Successfully finished Installing packages")

    def schedule_install_updates(self):
        """
        Schedules install updates job in the commcell
        """
        sched_name = cs.SCHEDULE_INSTALL_UPDATES_JSON["schedule_name"]
        if not self.commcell.schedules.has_schedule(sched_name):
            self.commcell.push_servicepack_and_hotfix(
                all_client_computers=True,
                reboot_client=True,
                run_db_maintenance=False,
                schedule_pattern=cs.SCHEDULE_INSTALL_UPDATES_JSON
            )
            self.log.info(f"Schedule with given name [{sched_name}] created successfully")
        else:
            self.log.info(f"Schedule with given name [{sched_name}] already exists")


class AdminRingSystemHelper(BaseRingHelper):
    """ contains helper class for performing administrative system tasks in the ring commcell"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.job_management = self.commcell.job_management
        self.cs_client = self.commcell.commserv_client
        self.db_query_helper = DBQueryHelper(ring_commcell)
        self.install_helper = InstallHelper(self.commcell)

    def start_task(self):
        """Starts the administrative system tasks for metallic ring"""
        try:
            self.log.info("Starting the admin task for metallic ring configuration")
            self.log.info("Updating network proxy settings for the network proxy clients")
            self.update_network_proxy_settings()
            self.log.info("Network proxy settings updated susccessfully. "
                          "Proceeding with updating webconsole certificates")
            self.update_web_console_certificate()
            self.log.info("Webconsole certificate updated successfully"
                          "Proceeding with set display name for each client in the commcell")
            self.set_ring_clients_display_name()
            self.log.info("Set display name is complete. Updating web domain for the ring.")
            self.add_web_domains()
            self.log.info("Successfully added web domains. Disabling IPV6 for webconsole.")
            self.disable_ipv6_for_web_console()
            self.log.info("Disable IPv6 for webconsoles. Admin task for Metallic completed successfully")
            self.restart_wc_service()
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute admin helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def restart_wc_service(self):
        """
        Restarts the tomcat service on the webconsole machine
        """
        for wc in _CONFIG.web_consoles:
            self.log.info(f"Request received to restart service on webconsole [{wc.client_name}]")
            wc_obj = self.commcell.clients.get(wc.client_name)
            if wc_obj.os_type is OSType.WINDOWS:
                wc_obj.restart_service(cs.WEBCONSOLE_TOMCAT_SERVICE)
            else:
                wc_obj.restart_service(cs.WEBCONSOLE_UNIX_TOMCAT_SERVICE)
            self.log.info(f"Sent restart service request to webconsole [{wc.client_name}]")
        self.log.info("Waiting for service to be up. Sleeping for 3 minutes")
        time.sleep(5*60)
        self.log.info("Sleep complete")

    def update_web_console_certificate(self):
        """Update web console certificate"""
        if self.ring.container_provision is True:
            self.log.info("Skipping updaing webconsole certificate update for container provisioning")
            return
        for wc in _CONFIG.web_consoles:
            self.log.info(f"Request received to update web console certificate on [{wc.client_name}]")
            wc_obj = self.commcell.clients.get(wc.client_name)
            wc_mac = Machine(wc_obj)
            tomcat_dir = wc_mac.get_registry_value(cs.WEBCONSOLE_REG_SECTION, cs.WEBCONSOLE_TOMCAT_REG_KEY)
            conf_folder = f"{tomcat_dir}{wc_mac.os_sep}{cs.WEBCONSOLE_CONF_FOLDER}"
            orig_server_xml_file = f"{conf_folder}{wc_mac.os_sep}{cs.WEBCONSOLE_SERVER_XML_FILE}"
            timestamp = f"_{time.strftime('%Y%m%d-%H%M%S')}"
            dest_server_xml_file = f"{conf_folder}{wc_mac.os_sep}{cs.WEBCONSOLE_SERVER_DEST_XML_FILE % timestamp}"
            self.log.info(f"Directories initialized. Apache Configuration Folder [{conf_folder}]"
                          f"\n Server XML File - [{orig_server_xml_file}]."
                          f"\n XML file to be renamed = [{dest_server_xml_file}]")
            # Read XML file
            self.log.info("Reading XML file")
            cert_xml = wc_mac.read_file(orig_server_xml_file)
            tree = ET.ElementTree(ET.fromstring(cert_xml))
            root = tree.getroot()
            # Modify XML file
            self.log.info("Read complete. Updating the XML")
            for element in root.iter('Certificate'):
                element.set("certificateKeystoreFile", f"{cs.WEBCONSOLE_CONF_FOLDER}/{cs.WEBCONSOLE_CERT_NAME}")
                element.set("certificateKeystorePassword", _CONFIG.certificate.certificateKeystorePassword)

            # Write changes to XML file
            self.log.info("Writing changes")
            final_xml_bytes = ET.tostring(root, encoding='UTF-8', method='xml', xml_declaration=True)
            final_xml_str = str(final_xml_bytes, 'UTF-8')
            if isinstance(wc_mac, UnixMachine):
                final_xml_str = final_xml_str.replace('"', '\\"')
            self.log.info("Renaming the original XML file")
            wc_mac.move_file(orig_server_xml_file, dest_server_xml_file)
            self.log.info("Rename complete. Creating the new server XML file and pushing it to web console")
            wc_mac.create_file(orig_server_xml_file, final_xml_str)
            wc_mac.copy_from_local(cs.WEB_CONSOLE_CERTIFICATE_FILE_PATH, os.path.dirname(orig_server_xml_file))
            self.log.info("Server XML moved to webconsole successfully")

    def update_network_proxy_settings(self, port_no=443):
        """
        Allows remote connection on network proxy
        Args:
            port_no(int)    --  Port number to be used for proxy client
        """
        if self.ring.container_provision is True:
            self.log.info("Skipping update of network proxy settings for container provisioning")
            return
        for np in _CONFIG.network_proxies:
            self.log.info("Updating nwp settings")
            np = self.commcell.clients.get(np.client_name)
            np_nw = np.network
            self.log.info("Updating configure network settings.")
            np_nw.configure_network_settings = True
            self.log.info("Completed configure network settings.  Updating port for proxy")
            np_nw.tunnel_connection_port = 443
            self.log.info("Completed port update.  marking the client as proxy")
            np_nw.proxy = True
            self.log.info("Marked the client as proxy. Opening the required ports in the proxy")
            mac = Machine(np)
            if mac.os_flavour == "Linux":
                cmd_check_port = f"firewall-cmd --list-ports | grep {port_no}/tcp"
                self.log.info(f"Executing the following command -[{cmd_check_port}]")
                command_op = mac.execute_command(cmd_check_port)
                if cs.FIREWALL_NOT_RUNNING_ERROR.lower() in command_op.exception.lower() \
                        or cs.FIREWALL_NOT_RUNNING_ERROR.lower() in command_op.exception_message.lower():
                    self.log.info("Firewall is not running")
                else:
                    self.log.info(f"command output - [{command_op}]")
                    if not str(port_no) in command_op.formatted_output:
                        cmd = f"firewall-cmd --zone=public --add-port={port_no}/tcp --permanent; " \
                              "firewall-cmd --reload"
                        self.log.info(f"Port is not open. Opening the port - [{port_no}]")
                        command_op = mac.execute_command(cmd)
                        if command_op.exception_message:
                            raise Exception(command_op.exception_code,
                                            command_op.exception_message)
                        elif command_op.exception:
                            raise Exception(command_op.exception_code, command_op.exception)
                        self.log.info(f"Port - [{port_no}] opened on proxy client")

    def set_ring_clients_display_name(self):
        """Sets the display name for all clients in the commcell based on the information in the metallic ring config"""
        self.log.info("Request received to update display name")
        commserv = _CONFIG.commserv
        self.update_client_dn(commserv.client_name, cs.Infra.CS.name, commserv.region)

        mas = _CONFIG.media_agents

        for index, media_agent in enumerate(mas):
            index_str = f"0{index + 1}" if len(str(index)) <= 1 else index + 1
            self.update_client_dn(media_agent.client_name, cs.Infra.MA.name, media_agent.region, index=index_str)

        wcs = _CONFIG.web_consoles
        for index, web_console in enumerate(wcs):
            index_str = f"0{index + 1}" if len(str(index)) <= 1 else index + 1
            self.update_client_dn(web_console.client_name, cs.Infra.WC.name, web_console.region, index=index_str)

        wss = _CONFIG.web_servers
        for index, web_server in enumerate(wss):
            index_str = f"0{index + 1}" if len(str(index)) <= 1 else index + 1
            self.update_client_dn(web_server.client_name, cs.Infra.WS.name, web_server.region, index=index_str)

        nps = _CONFIG.network_proxies
        for index, network_proxy in enumerate(nps):
            index_str = f"0{index + 1}" if len(str(index)) <= 1 else index + 1
            self.update_client_dn(network_proxy.client_name, cs.Infra.NWP.name, network_proxy.region, index=index_str)
        self.log.info("Display name update for clients completed successfully")

    def update_client_dn(self, client_name, infra_type, region="c1us02", index="01"):
        """
        Updates the display name for a given client based on the region,
                                                    ring name and infrastructure type
        Args:
            client_name(str)        -   Name of the client
            infra_type(enum)        -   Type of the client
            region(str)             -   region of the client
            index(str)              -   represents the node number of the client
                                        Ex - 01 represents first node
                                             02 represents second node
        """
        self.log.info(f"Display name update request received for client [{client_name}]. "
                      f"Client Type: [{infra_type}]. Region: [{region}]. Node: [{index}]")
        ring_id = RingUtils.get_ring_string(_CONFIG.id)
        if infra_type == cs.Infra.CS.name:
            display_name = f"M{ring_id}"
        elif infra_type == cs.Infra.MA.name:
            display_name = f"mas{index}{ring_id}{region}"
        elif infra_type == cs.Infra.WS.name:
            display_name = f"wes{index}{ring_id}{region}"
        elif infra_type == cs.Infra.WC.name:
            display_name = f"wec{index}{ring_id}{region}"
        elif infra_type == cs.Infra.NWP.name:
            display_name = f"nwp{index}{ring_id}{region}"
        else:
            self.log.info(f"Given Client Type: [{infra_type}] is not supported for display name change.")
            return
        self.__set_client_dn(client_name, display_name)
        self.log.info(f"Display name [{display_name}] for client [{client_name}] updated successfully.")

    def add_web_domains(self, web_domain_urls=None):
        """
        Adds the web domains to a given commcell
        Args:
            web_domain_urls(list) -- List of web domain URLs to be added
        Raises:
            Exception:
                If setting web domain urls have failed
        Returns:
            None
        """
        self.log.info("Request received to add web domains")
        if web_domain_urls is None:
            web_domain_urls = [f"https://{_METRICS_CONFIG.url}:443"]
        request_json = {
            "name": "webDomainsWhiteList",
            "value": ", ".join(web_domain_urls)
        }
        self.log.info(f"Updating via set gx global param API - req [{request_json}]")
        resp = self.commcell._set_gxglobalparam_value(request_json)
        if resp.get("errorCode", 0) != 0:
            raise Exception(f"Failed to set web domains {web_domain_urls} - response - {resp}")
        self.log.info("Updated web domains successfully")

    def disable_ipv6_for_web_console(self, web_consoles=_CONFIG.web_consoles):
        """
        disable web console machines' IPV6 address
        Args:
            web_consoles(list)      -   List of web console machines
        """
        if self.ring.container_provision is True:
            self.log.info("Skip IPv6 for container provisioning")
            return
        self.log.info("Request received to disable IPV6")
        for web_console in web_consoles:
            self.log.info(f"Disabling for webconsole machine - [{web_console.client_name}]")
            mac = Machine(web_console.client_name, self.commcell)
            mac.disable_ipv6()
            self.log.info(f"Disabled IPV6 for webconsole machine - [{web_console.client_name}]")

    def __set_client_dn(self, client_name, display_name):
        """
        Sets the client display name in the commcell
        Args:
            client_name(str)    --  Name of the client
            display_name(str)   --  New display name for the client
        Raises:
            Exception:
                If given client name is not present
        """
        if self.commcell.clients.has_client(client_name):
            client_obj = self.commcell.clients.get(client_name)
            client_dn = client_obj.display_name
            self.log.info(f"Current Display name: [{client_dn}]. Display name to be updated [{display_name}]")
            if client_dn != display_name:
                client_obj.display_name = display_name
                self.log.info(f"New Display name: [{display_name}] updated successfully.")
            else:
                self.log.info("Display name update is not required")
        else:
            raise Exception(f"client with given name doesn't exist [{client_name}]")


class CustomAdminRingSystemHelper(AdminRingSystemHelper):
    """Overrides AdminRingSystemHelper to cater needs based on custom infrastructure"""

    def set_ring_clients_display_name(self):
        """Changes only the commcell client's display name for uniformity across all service commcells"""
        self.log.info("Request received to update CS display name")
        commserv = _CONFIG.commserv
        self.update_client_dn(commserv.client_name, cs.Infra.CS.name, commserv.region)

    def update_network_proxy_settings(self, port_no=443):
        """Skips updating the network proxy settings"""
        pass

    def disable_ipv6_for_web_console(self, web_consoles=_CONFIG.web_consoles):
        """Skips disabling the IPv6 address for custom infra"""
        try:
            super().disable_ipv6_for_web_console(web_consoles)
        except Exception as e:
            self.log.info(f"Disabling IPV6 failed. Disable it manually. Exception: [{e}]")


class CustomAdminRingMaintenanceHelper(AdminRingMaintenanceHelper):

    def sync_software(self):
        pass

    def download_software(self):
        pass

    def update_download_settings(self):
        pass

    def install_updates(self):
        pass
