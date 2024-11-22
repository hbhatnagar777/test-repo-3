# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for reading/updating the config files for Ring Automation

    ConfigReader:

        __init__()                                  --  Initializes the config reader helper
        read_and_update_config_files                --  Reads and updates the config files needed for ring automation
        read_controller_inputs_and_update_config    --  Reads controller input from config json
                                                        and updates the ring config file
        read_and_backup_config_file                 --  Moves/backs up the old ring config file to a new location
        get_updated_commcell_details                --  Gets and sets the required commcell details
        get_updated_ring_details                    --  Gets and sets the required ring details
        get_updated_config                          --  Gets and sets the required configuration required for the ring
        get_updated_strict_data                     --  Gets and sets the required config for strict guideline machines
        get_updated_virtualization_data             --  Gets and sets the required config for VM host based configuration
        get_updated_containers_data                 --  Gets and sets the required config for containers based provisioning
        get_updated_custom_data                     --  Gets and sets the required config for custom infrastructure
        get_ip_op_data                              --  Reads and returns the required JSON input and template config
                                                        file for ring provisioning
        start_func_app_exists_task                  --  Start the task to check if a function app exists for a given/available ring
        get_ring_name                               --  Gets the provided or available ring name
        get_ring_details                            --  Get the details of the ring
"""

import os
import re
import time

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from MetallicHub.Helpers.azure_resource_helper import app_exists
from MetallicHub.Utils.Constants import BIZ_FUNCTION_APP_NAME, CORE_FUNCTION_APP_NAME
from MetallicRing.Core.db_helper import DBQueryHelper
from cvpysdk.commcell import Commcell
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.DBQueries import Constants as db_cs
from MetallicRing.Utils.ring_utils import RingUtils


class ConfigReader:
    """Helper class to read and update config files"""

    def __init__(self):
        """
        Initializes the config reader helper
        """
        self.log = logger.get_log()
        self.db_obj = SQLiteDBQueryHelper()
        self.ring_id = None
        self.ring_id_str = None
        self.ring_name = None
        self.unique_id = None
        self.provision_type = str(cs.RingProvisionType.STRICT.value)
        self.commserv_name = None
        self.commcell_username = None
        self.commcell_password = None
        self.notification_email = None
        self.suffix = f"testlab.commvault.com"

    def read_and_update_config_files(self):
        """
        Reads and updates the config files needed for ring automation
        """
        try:
            self.log.info("Reading and backing up the config file")
            self.read_and_backup_config_file()
            self.log.info("Read and backup complete. Reading the input file from controller")
            self.read_controller_inputs_and_update_config()
            self.log.info("Updated the config file with controller inputs")
        except Exception as exp:
            from MetallicRing.Helpers.email_helper import EmailHelper
            emh = EmailHelper(self.ring_name, self.commserv_name)
            emh.send_init_failure_mail(str(exp), f"{self.ring_name}{cs.RING_FROM_EMAIL_SUFFIX}", self.notification_email)
            raise

    def read_controller_inputs_and_update_config(self):
        """
        Reads controller input from config json and updates the ring config file
        """
        # Read the JSON file
        ip_data, op_data = self.get_ip_op_data()
        # Extract the attribute values
        self.provision_type = ip_data.get("PROVISION TYPE", str(cs.RingProvisionType.STRICT.value))
        self.start_func_app_exists_task(ip_data)
        op_data = self.get_updated_ring_details(ip_data, op_data)
        op_data = self.get_updated_commcell_details(ip_data, op_data)
        op_data = self.get_updated_config(ip_data, op_data)
        op_data = op_data.replace('{{domain_suffix}}', self.suffix)
        # Write the output file with indentation
        self.log.info("All input files read successfully. Writing the info back to config file")
        RingUtils.write_to_file(cs.METALLIC_CONFIG_FILE_PATH, op_data)
        self.log.info("Write to config successful")
        from MetallicRing.Helpers.email_helper import EmailHelper
        emh = EmailHelper(self.ring_name, self.commserv_name)
        emh.send_welcome_mail()

    def start_func_app_exists_task(self, ip_data):
        """
        Start the task to check if a function app exists for a given/available ring
        Args:
            ip_data(dict)       --  JSON data having the required inputs
        """
        self.ring_name = self.get_ring_name(ip_data)
        task_type = db_cs.CHECK_FUNC_APP_EXIST_TASK
        query = db_cs.SELECT_RING_CONFIG_QUERY % (self.ring_name.lower(), task_type)
        result = self.db_obj.execute_query(query)
        self.log.info(f"Result of query execution - [{result}]")
        if len(result.rows) != 0:
            self.log.info(f"Check if Function App Exists task already complete for ring [{self.ring_name}]. "
                          "Not Starting it")
            return
        while app_exists(BIZ_FUNCTION_APP_NAME % self.ring_name) or app_exists(CORE_FUNCTION_APP_NAME % self.ring_name):
            self.db_obj.execute_query(db_cs.UPDATE_AVAILABLE_RING_STATUS % (db_cs.RING_TASK_COMPLETE,
                                                                            db_cs.NON_DEV_RING, self.ring_name))
            self.ring_name = self.get_ring_name(ip_data)
        self.log.info(f"Function App is available for use for ring [{self.ring_name}]")
        query = db_cs.INSERT_RING_CONFIG_QUERY_V2 % (db_cs.STATE_COMPLETE, '%s', '%s', self.ring_name.lower(), task_type)
        self.db_obj.execute_query(query)
        self.log.info(f"Check if Function App Exists task completed successfully. Available RIng is [{self.ring_name}]")

    def get_updated_commcell_details(self, ip_data, op_data):
        """
        Gets and sets the required commcell details
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced

        Returns:
            str                 --  String containing updated values in the placeholder
        """
        self.commserv_name = ip_data.get('COMMSERV NAME', None)
        if self.commserv_name is None:
            self.commserv_name = f"cms01{self.ring_id_str}c1us02"
        self.commcell_username = ip_data.get('COMMCELL USERNAME')
        self.commcell_password = ip_data.get('COMMCELL PASSWORD')
        self.notification_email = ip_data.get('EMAIL ID', f'{self.commcell_username}{cs.RING_EMAIL_SUFFIX}')
        op_data = op_data.replace('{{commcell_username}}', self.commcell_username)
        op_data = op_data.replace('{{commcell_password}}', self.commcell_password)
        op_data = op_data.replace('{{notification_email}}', self.notification_email)
        return op_data

    def get_ring_name(self, ip_data):
        """
        Gets the provided or available ring name
        Args:
            ip_data(dict)       --  JSON data having the required inputs
        Returns:
            str                 --  Name of the ring
        """
        if self.provision_type in (str(cs.RingProvisionType.STRICT.value),
                                   str(cs.RingProvisionType.VIRTUALIZATION.value)):
            return ip_data.get('RING NAME', None)
        elif self.provision_type in (str(cs.RingProvisionType.CONTAINERS.value),
                                     str(cs.RingProvisionType.CUSTOM.value)):
            result, _ = self.get_ring_details(ip_data)
            ring_name = result.rows[0][1]
            self.log.info(f"Ring name obtained is [{ring_name}]")
            return ring_name
        return None

    def get_updated_ring_details(self, ip_data, op_data):
        """
        Gets and sets the required ring details
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced

        Returns:
            str                 --  String containing updated values in the placeholder
        """
        if self.provision_type in (str(cs.RingProvisionType.STRICT.value),
                                   str(cs.RingProvisionType.VIRTUALIZATION.value)):
            self.ring_name = ip_data.get('RING NAME', None)
            self.ring_id = str(int(re.findall(r'\d+', self.ring_name)[-1]))
            self.ring_id_str = RingUtils.get_ring_string(self.ring_id)
            op_data = op_data.replace('{{unique_id}}', self.ring_name)
        elif self.provision_type in (str(cs.RingProvisionType.CONTAINERS.value),
                                     str(cs.RingProvisionType.CUSTOM.value)):
            result, unique_id = self.get_ring_details(ip_data)
            self.ring_id = result.rows[0][0]
            self.ring_name = result.rows[0][1]
            self.ring_id_str = RingUtils.get_ring_string(self.ring_id)
            op_data = op_data.replace('{{unique_id}}', unique_id)
        op_data = op_data.replace('{{ring_name}}', self.ring_name)
        op_data = op_data.replace('"{{ring_id}}"', f"{self.ring_id}")
        return op_data

    def get_ring_details(self, ip_data):
        """
        Get the details of the ring
        Args:
            ip_data(dict)       --  JSON data having the required inputs
        Returns:
            str, str            --  Name of the available ring, unique ID (username/cc hostname)
        Raises:
            Exception           --  When there are no available ring names to use
        """
        if self.provision_type == str(cs.RingProvisionType.CONTAINERS.value):
            unique_id = ip_data.get('RING USERNAME')
            unique_id = unique_id.replace("\\", "\\\\")
        else:
            unique_id = ip_data.get('COMMAND CENTER HOSTNAME', None)
        self.unique_id = unique_id
        result = self.db_obj.execute_query(db_cs.CHECK_USER_HAS_RING_QUERY % unique_id)
        if len(result.rows) > 0:
            self.ring_name = result.rows[0][1]
            status = result.rows[0][2]
            if status == db_cs.RING_TASK_COMPLETE:
                raise Exception("Given user/command center host has a ring configured. Request the "
                                "administrator for an additional ring")
            elif status == db_cs.RING_TASK_RUNNING:
                raise Exception("Given user has a ring that is in progress. Please wait till it completes")
        else:
            result = self.db_obj.execute_query(db_cs.GET_AVAILABLE_RING_QUERY)
            if len(result.rows) == 0:
                raise Exception("There are no free available rings to use. Contact administrator")
        return result, unique_id

    def get_updated_config(self, ip_data, op_data):
        """
        Gets and sets the required configuration required for the ring
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced

        Returns:
            str                 --  String containing updated values in the placeholder
        """
        if self.provision_type == str(cs.RingProvisionType.STRICT.value):
            op_data = self.get_updated_strict_data(ip_data, op_data)
        elif self.provision_type == str(cs.RingProvisionType.VIRTUALIZATION.value):
            op_data = self.get_updated_virtualization_data(ip_data, op_data)
        elif self.provision_type == str(cs.RingProvisionType.CONTAINERS.value):
            op_data = self.get_updated_containers_data(ip_data, op_data)
        elif self.provision_type == str(cs.RingProvisionType.CUSTOM.value):
            op_data = self.get_updated_custom_data(ip_data, op_data)
        op_data = op_data.replace('"{{provision_type}}"', self.provision_type)
        op_data = op_data.replace('{{ring_id}}', self.ring_id_str)
        return op_data

    def get_updated_strict_data(self, ip_data, op_data):
        """
        Gets and sets the required config for strict guideline machines
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced
        Returns:
            str                 --  String containing updated values in the placeholder
        """
        self.log.info("This is Non provision VM request. Inputs must contain the all VM/machine details")
        op_data = op_data.replace('"{{provision_vm}}"', "false")
        op_data = op_data.replace('"{{provision_containers}}"', "false")
        self.log.info("This is a request to provision ring with existing VMs")
        cs_hostname = ip_data['COMMSERV HOST NAME']
        ma_clientname = ip_data['MEDIA AGENT CLIENT NAME']
        ws_clientname = ip_data['WEB SERVER CLIENT NAME']
        wc_clientname = ip_data['WEBCONSOLE CLIENT NAME']
        wc_hostname = ip_data['WEBCONSOLE HOSTNAME']
        nwp_clientname = ip_data['NETWORK PROXY CLIENT NAME']
        op_data = op_data.replace('cms01{{ring_id}}c1us02.testlab.commvault.com', cs_hostname)
        op_data = op_data.replace('cms01{{ring_id}}c1us02', self.commserv_name)
        op_data = op_data.replace('mas01{{ring_id}}c1us02', ma_clientname)
        op_data = op_data.replace('wes01{{ring_id}}c1us02', ws_clientname)
        op_data = op_data.replace('wec01{{ring_id}}c1us02.testlab.commvault.com', wc_hostname)
        op_data = op_data.replace('wec01{{ring_id}}c1us02', wc_clientname)
        op_data = op_data.replace('nwp01{{ring_id}}c1us02', nwp_clientname)
        return op_data

    def get_updated_virtualization_data(self, ip_data, op_data):
        """
        Gets and sets the required config for VM host based configuration
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced
        Returns:
            str                 --  String containing updated values in the placeholder
        """
        self.log.info("This is provision VM request. Inputs must contain the hyperv host and required details")
        op_data = op_data.replace('"{{provision_vm}}"', "true")
        op_data = op_data.replace('"{{provision_containers}}"', "false")
        op_data = op_data.replace('{{ring_id}}', self.ring_id_str)
        vm_host_type = ip_data.get("VIRTUAL MACHINE HOST TYPE".upper(), None)
        if vm_host_type == "Hyperv":
            self.log.info("Given host is hyperv")
            self.log.info("Request received to provision ring by creating new VMs")
            v3_enc_password = ip_data['V3 ENCRYPTED COMMCELL PASSWORD']
            vm_host_fqdn = ip_data['VM HOST FQDN']
            vm_host_domain = ip_data['VM HOST DOMAIN']
            vm_host_username = ip_data['VM HOST USERNAME']
            vm_host_password = ip_data['VM HOST PASSWORD']
            win_template_path = ip_data['WINDOWS OS TEMPLATE FILE PATH']
            win_template_path = win_template_path.replace("\\", "\\\\")
            win_temp_username = ip_data['WINDOWS OS TEMPLATE USERNAME']
            win_temp_password = ip_data['WINDOWS OS TEMPLATE PASSWORD']
            unix_template_path = ip_data['LINUX OS TEMPLATE FILE PATH']
            unix_template_path = unix_template_path.replace("\\", "\\\\")
            unix_temp_username = ip_data['LINUX OS TEMPLATE USERNAME']
            unix_temp_password = ip_data['LINUX OS TEMPLATE PASSWORD']
            vm_disk_path = ip_data['PATH TO CREATE VMS']
            vm_disk_path = vm_disk_path.replace("\\", "\\\\")
            sp_info = ip_data['SERVICE PACK INFORMATION']
            unix_dvd_path = ip_data['UNIX INSTALLATION DVD PATH']
            unix_dvd_path = unix_dvd_path.replace("\\", "\\\\")
            op_data = op_data.replace('{{v3_commcell_encrypted_password}}', v3_enc_password)
            op_data = op_data.replace('{{hyper_host}}', vm_host_fqdn)
            op_data = op_data.replace('{{hyperv_domain}}', vm_host_domain)
            op_data = op_data.replace('{{hyperv_username}}', vm_host_username)
            op_data = op_data.replace('{{hyperv_password}}', vm_host_password)
            op_data = op_data.replace('{{windows_template_path}}', win_template_path)
            op_data = op_data.replace('{{windows_template_username}}', win_temp_username)
            op_data = op_data.replace('{{windows_template_password}}', win_temp_password)
            op_data = op_data.replace('{{unix_template_path}}', unix_template_path)
            op_data = op_data.replace('{{unix_template_username}}', unix_temp_username)
            op_data = op_data.replace('{{unix_template_password}}', unix_temp_password)
            op_data = op_data.replace('{{cloned_disk_path}}', vm_disk_path)
            op_data = op_data.replace('{{service_pack}}', sp_info)
            op_data = op_data.replace('{{media_path}}', unix_dvd_path)
        else:
            raise Exception(f"Provisioning of VM on [{vm_host_type}] host is not supported")
        return op_data

    def get_updated_containers_data(self, ip_data, op_data):
        """
        Gets and sets the required config for containers based provisioning
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced
        Returns:
            str                 --  String containing updated values in the placeholder
        """
        self.log.info("This is containers provision request")
        self.suffix = f"{self.ring_name}.devk8s.{self.suffix}"
        op_data = op_data.replace('"{{provision_containers}}"', "true")
        op_data = op_data.replace('"{{provision_vm}}"', "false")
        hostname_str = f"01{self.ring_id_str}c1us02.{self.suffix}"
        op_data = op_data.replace('cms01{{ring_id}}c1us02.testlab.commvault.com',
                                  f"cms{hostname_str}")
        op_data = op_data.replace('wec01{{ring_id}}c1us02.testlab.commvault.com',
                                  f"wec{hostname_str}")
        self.db_obj.execute_query(db_cs.UPDATE_AVAILABLE_RING_STATUS % (db_cs.RING_TASK_RUNNING,
                                                                        self.unique_id, self.ring_name))
        return op_data

    def get_updated_custom_data(self, ip_data, op_data):
        """
        Gets and sets the required config for custom infrastructure
        Args:
            ip_data(dict)       --  JSON data having the requireed inputs
            op_data(str)        --  Input string containing placeholder to be replaced
        Returns:
            str                 --  String containing updated values in the placeholder
        """
        wc_client, ws_obj = None, None
        unique_id = ip_data.get('COMMAND CENTER HOSTNAME', None)
        unique_id = unique_id.replace("\\", "\\\\")
        op_data = op_data.replace('{{unique_id}}', unique_id)
        self.log.info("This is custom setup. Inputs must contain the command center hostname")
        op_data = op_data.replace('"{{provision_vm}}"', "false")
        op_data = op_data.replace('"{{provision_containers}}"', "false")
        self.log.info("This is a request to provision ring with existing VMs")
        wc_hostname = ip_data['COMMAND CENTER HOSTNAME']
        cc = Commcell(wc_hostname, self.commcell_username, self.commcell_password)
        cs_hostname = cc.commserv_hostname
        self.log.info(f"Obtained commserve [{cs_hostname}] and command center host name [{wc_hostname}]")
        dbh = DBQueryHelper(cc)
        result = dbh.execute_select_query(db_cs.GET_CLIENT_CONTAINER_FLAG % cc.commcell_id)
        if result[0][0] == '1':
            self.log.info("This is container based deployment. Getting the updated cs hostname")
            cs_host_split = cs_hostname.split('.')
            wc_host_split = wc_hostname.split('.')
            wc_host_split[0] = f'{cs_host_split[0]}gateway'
            cs_hostname = '.'.join(wc_host_split)
            self.log.info(f"Updated CS hostname - [{cs_hostname}]")
        self.commserv_name = cc.commserv_name
        ma_clientname = None
        for media_agent in cc.media_agents.all_media_agents:
            try:
                ma_obj = cc.media_agents.get(media_agent)
                retry_attempt = 0
                if not ma_obj.is_online:
                    self.log.info(f"Media agent is not online - [{media_agent}]")
                    ma_client_obj = cc.clients.get(media_agent)
                    ma_mac_obj = Machine(ma_client_obj)
                    ma_mac_obj.start_all_cv_services()
                    ma_obj.refresh()
                    while not ma_obj.is_online and retry_attempt <= 6:
                        self.log.info("Sleeping for 10 seconds for services to come up")
                        time.sleep(10)
                        ma_obj.refresh()
                        retry_attempt += 1
                        self.log.info(f"Retry attempt [{retry_attempt}] complete")
                if ma_obj.is_online:
                    ma_clientname = media_agent
                    self.log.info(f"Media Agent with name [{media_agent}] is Online. WIll be used further")
                    break
                else:
                    self.log.info(f"Media Agent with name [{media_agent}] is offline")
            except Exception as exp:
                self.log.info(f"Exception occurred when accessing MA object [{exp}]")
        if ma_clientname is None:
            raise Exception("No Media agents which are online is found. Please check if the MA services "
                            "are up and try again")
        try:
            # If we cannot obtain the client name, then it means it's a endpoint and not command center hostname
            self.log.info(f"Trying to obtain command center object for host - [{wc_hostname}]")
            wc_client = cc.clients.get(wc_hostname)
            wc_clientname = wc_client.client_name
        except Exception as exp:
            self.log.info("Failed to obtain the client name. This is a endpoint and not command center hostname")
            for client in cc.clients.all_clients:
                self.log.info(f"Checking if client [{client}] has Web Server/Command Center Package installed")
                wc_client = cc.clients.get(client)
                if wc_client.is_command_center:
                    self.log.info(f"Command Center client object obtained [{client}]")
                    break
            if wc_client is None:
                raise Exception("No command center/web server client found")
            wc_clientname = wc_client.client_name
        wc_machine = Machine(wc_client)
        if wc_machine.check_registry_exists(cs.WEBCONSOLE_REG_SECTION, cs.WEBCONSOLE_WS_HOST_REG_KEY) is True:
            ws_hostname = wc_machine.get_registry_value(cs.WEBCONSOLE_REG_SECTION, cs.WEBCONSOLE_WS_HOST_REG_KEY)
            ws_obj = cc.clients.get(ws_hostname)
            ws_clientname = ws_obj.client_name
        else:
            raise Exception("Web Server info is missing in the Command Center Client")
        op_data = op_data.replace('cms01{{ring_id}}c1us02.testlab.commvault.com', cs_hostname)
        op_data = op_data.replace('cms01{{ring_id}}c1us02', self.commserv_name)
        op_data = op_data.replace('mas01{{ring_id}}c1us02', ma_clientname)
        op_data = op_data.replace('wes01{{ring_id}}c1us02', ws_clientname)
        op_data = op_data.replace('wec01{{ring_id}}c1us02.testlab.commvault.com', wc_hostname)
        op_data = op_data.replace('wec01{{ring_id}}c1us02', wc_clientname)
        op_data = op_data.replace('nwp01{{ring_id}}c1us02', "")  # Skipping network proxy part
        self.db_obj.execute_query(db_cs.UPDATE_AVAILABLE_RING_STATUS % (db_cs.RING_TASK_RUNNING,
                                                                        unique_id, self.ring_name))
        return op_data

    def get_ip_op_data(self):
        """
        Reads and returns the required JSON input and template config file for ring provisioning
        Returns:
            str. str            --  the JSON input and template config file for ring provisioning
        """
        self.log.info(f"Reading controller inputs. opening file [{cs.METALLIC_CONTROLLER_INPUT_CONFIG_FILE_PATH}]")
        ip_data = RingUtils.read_from_file(cs.METALLIC_CONTROLLER_INPUT_CONFIG_FILE_PATH, read_json=True)
        self.log.info(f"Read complete. Opening the deployment config file [{cs.METALLIC_DEPLOYMENT_CONFIG_FILE_PATH}]")
        op_data = RingUtils.read_from_file(cs.METALLIC_DEPLOYMENT_CONFIG_FILE_PATH)
        self.log.info("Read complete")
        return ip_data, op_data

    def read_and_backup_config_file(self):
        """
        Moves/backs up the old ring config file to a new location
        """
        # Read the input JSON file
        self.log.info("Checking if the old config file is already present")
        if os.path.exists(cs.METALLIC_CONFIG_FILE_PATH):
            self.log.info("Old config is present")
            data = RingUtils.read_from_file(cs.METALLIC_CONFIG_FILE_PATH, read_json=True)
            self.log.info("Completed reading the config file")
            # Extract the "ring name" attribute value
            ring_name = data['Metallic']['ring']['name']
            self.log.info(f"Ring name on old config - [{ring_name}]")
            # Create the output filename (with timestamp if file already exists)
            os.chdir(os.path.dirname(cs.METALLIC_CONFIG_FILE_PATH))
            os.chdir(cs.METALLIC_RUN_CONFIG_DIRECTORY_NAME)
            output_filename = f"metallic_config_{ring_name}.json"
            self.log.info(f"Moving the config file to the below name - [{output_filename}]")
            if os.path.exists(output_filename):
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_filename = f"metallic_config_{ring_name}_{timestamp}.json"
                print(f"Output file '{output_filename}' already exists. Appending timestamp...")
            # Write the JSON data to the output file with indentation
            RingUtils.write_to_file(output_filename, data, write_json=True)
            self.log.info(f"Old Data dumped to a different file - [{output_filename}]")
        else:
            self.log.info("No old config files present")
