# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for node refresh
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup_admin_console()       --  Logs in to the command center and initializes the storage helper

    setup()                     --  setup function of this test case

    setup_vm_automation()       --  Initializes the VM automation helpers

    tear_down()                 --  tear down function of this test case

    fail_test_case()            --  Prints failure reason, sets the result string

    check_registry_exists_and_has_value()   --  Checks if a MA registry exists and has a given value

    get_sp_version_from_cs()    --  Returns SP version as indicated by CS from client name

    get_os_version_from_cs()    --  Returns OS version as indicated by CS from client name.

    is_remote_cache_present()   --  Returns whether remote cache present or not

    get_or_create_policy()      --  Gets or creates the storage policy from name

    check_gluster_shows_no_volumes_for_preserve_node()  --  Checks if gluster reports no volumes for preserve node

    run_upgrade_job_till_completion()   -- Runs the upgrade job on the client. Blocks until completes 

    run_until_success()         --  Runs a command untill it succeeds or retry attempts are exhausted

    get_rc_value_after()        --  Checks the return code log line (with retry attempts) from a particular line number and returns it.

    get_command_rc()            --  Checks the command (with retry attempts) and returns the return code in a log file.

    get_line_number_of_log()    --  Searches for a log line (with retry attempts) and returns it's line number.

    check_refresh_logs()        --  Checks if the logs related to the refresh operation are good

    refresh_preserve_node()     --  Clicks on the refresh button via admin console

    get_log_lines()             --  Returns list of log lines for a given Windows MA and log file name.

    find_substring_in_string_list()         --  Returns the first index where substring matches a string from a list

    validate_refresh_logs_on_mm()           --  Validates the refresh logs present on CS in MediaManager.log

    validate_initial_refresh_logs_on_mm()   --  Validates the initial refresh logs present on CS in MediaManager.log

    validate_final_refresh_logs_on_mm()     --  Validates the final refresh logs present on CS in MediaManager.log

    get_client_id()             --  Returns the client id from the client name

    check_identical_output()    --  Runs same command across multiple MAs for equality.

    check_identical_values()    --  Runs same operation across multiple MAs for output equality.

    get_client_test_data_folder()   --  Returns the folder name which will be backed up

    create_test_data()          --  Creates the test data with content_gb size

    get_client_restore_path()   --  Returns the path where restore happens

    cleanup_test_data()         --  Clears the test data directory

    is_node_down_from_gluster() --  Checks if preserve node is down from gluster's perspective

    verify_initial_request_logs()   --  Verifies the initial request logs in MM

    verify_final_mm_logs()      --  Verifies the final refresh logs in MM

    fire_basic_setup_commands() --  Sets up the node by executing basic commands

    restore_network_and_register_to_cs()    --  Performs network restore and runs setupsds

    run_ddb_verification()      --  Runs DDB Verification

    run()                       --  run function of this test case


Sample input json
"54888": {
            "ControlNodes": {
              "MA1": "name1",
              "MA2": "name2",
              "MA3": "name3"
            },
            "ContentGb1": 5,    (OPTIONAL)
            "ContentGb2": 20,   (OPTIONAL)
            "ContentGb3": 10,   (OPTIONAL)
            "PreserveNode": {
              "name": "name2",
              "username": "username",
              "password": "password"
            }
         }
"""
# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = '''
"HyperScale": {
    ...,
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
'''

from HyperScale.HyperScaleUtils.esx_vm_io import EsxVmIo
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.screen_matcher import ScreenMatcher
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.adminconsole import AdminConsole
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from Install.softwarecache_helper import SoftwareCache
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from AutomationUtils.vmoperations import VmOperations
from AutomationUtils.output_formatter import UnixOutput
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils import constants, commonutils
import time
import re
from datetime import datetime
import atexit
from pyVim import connect


class TestCase(CVTestCase):
    """Hyperscale test class for node refresh"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for node refresh"
        self.result_string = ""
        self.backupset = ""
        self.subclient_obj = ""
        self.job_obj = ""
        self.library = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient_name = ""
        self.storage_policy = ""
        self.client_name = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.storage_policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.tcinputs = {
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
            },
            # these are optional 
            # "ContentGb1": None,
            # "ContentGb2": None,
            # "ContentGb3": None,
            "PreserveNode": {
                "name": None,
                "username": None,
                "password": None,
            }
        }
        self.successful = False

    def setup_admin_console(self):
        """
        Logs in to the command center
        and initializes the storage helper
        """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.driver = self.admin_console.driver
            self.admin_console.login(self.username,
                                     self.password)
            self.storage_helper = StorageMain(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Initializes test case variables"""
        self.log.info(f"setup {self.id}")
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)

        # Preserve node (node to be refreshed) setup
        self.preserve_node = self.tcinputs["PreserveNode"]["name"]
        self.preserve_node_sds = f'{self.preserve_node}sds'
        self.preserve_node_username = self.tcinputs["PreserveNode"]["username"]
        self.preserve_node_password = self.tcinputs["PreserveNode"]["password"]

        # MA setup
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        for node in self.control_nodes:
            ma_name = self.control_nodes[node]
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            self.mas.append(ma_name)
        self.other_mas = [ma for ma in self.mas if ma != self.preserve_node]
        self.other_mas_sds = [f'{ma}sds' for ma in self.other_mas]
        
        # saving this now because when the commvault services are down
        # these values aren't correct / are None
        preserve_node_client = self.commcell.clients.get(self.preserve_node)
        self.preserve_node_log_directory = preserve_node_client.log_directory
        self.preserve_node_job_results_directory = preserve_node_client.job_results_directory
        self.preserve_node_install_directory = preserve_node_client.install_directory
        if (not self.preserve_node_log_directory) or (not self.preserve_node_job_results_directory):
            message = f"Please check if {self.preserve_node} is up including Commvault services."
            message += f" log directory = {self.preserve_node_log_directory}."
            message += f" job results directory = {self.preserve_node_job_results_directory}."
            raise Exception(message)

        # CSDB
        self.config = get_config()
        self.sql_sq_password = commonutils.get_cvadmin_password(self.commcell)
        if not hasattr(self.config.SQL, 'Username'):
            raise Exception(f"Please add default 'Username' to SQL in config.json file")
        self.sql_login = self.config.SQL.Username

        # Subclient & Storage setup
        self.storage_pool_name = f"{self.id}StoragePool"
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset_name = "defaultBackupSet"
        self.backupset = self.agent.backupsets.get(self.backupset_name)
        self.subclient_name = f"{self.id}_subclient"
        self.storage_policy_name = f"{self.id}_policy"
        # before node kill, small, 5gb
        self.content_gb1 = int(self.tcinputs.get('ContentGb1', 5))
        # after node kill, large 20gb
        self.content_gb2 = int(self.tcinputs.get('ContentGb2', 20))
        # after node refresh, medium 10gb
        self.content_gb3 = int(self.tcinputs.get('ContentGb3', 10))
        self.mmhelper_obj = MMHelper(self)
        self.total_content_gb = self.content_gb1 + self.content_gb2 + self.content_gb3
        self.options_selector = OptionsSelector(self.commcell)
        self.drive = self.options_selector.get_drive(self.client_machine, self.total_content_gb*2*1024)
        self.test_case_path = self.client_machine.join_path(self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(self.test_case_path, "Testdata")
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')

        self.hyperscale_helper = HyperScaleHelper(
            self.commcell, self.csdb, self.log)

        # VM setup + VM automation
        if not hasattr(self.config.HyperScale, 'VMConfig'):
            raise(f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}")
        self.hs_vm_config = self.config.HyperScale.VMConfig
        self.setup_vm_automation()

        self.idautils = CommonUtils(self)
        self.PRESERVE_KEY = 'sHyperScalePreserve'
        self.MEDIA_MANAGER_LOG = "MediaManager.log"

        # populated from setup_admin_console
        self.storage_helper = None

        # mm logs on CS
        self.mm_logs_before_refresh = []
        self.enforce_mm_logs = True

    def setup_vm_automation(self):
        """Initializes the VM automation helpers"""
        server_type = VmIo.SERVER_TYPE_ESX
        server_host_name = self.hs_vm_config.ServerHostName
        username =  self.hs_vm_config.Username
        password = self.hs_vm_config.Password
        vm_config = {
            'server_type': server_type,
            'server_host_name': server_host_name,
            'username': username,
            'password': password
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io: EsxVmIo = VmIo(
            self.preserve_node, server_type, server_host_name, username, password)
        self.vm = self.esx.get_vm_object(self.preserve_node)
        self.matcher = ScreenMatcher(self.vm_io)
    
    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        self.log.info(f"tear_down {self.id}")
        if self.successful:
            self.log.info("Test case successful. Cleaning up storage pool")
            self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                         self.sql_login, self.sql_sq_password)
            self.log.info("Storage pool cleaned up")
            self.cleanup_test_data()
        else:
            self.status = constants.FAILED
    
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:
                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

    def check_registry_exists_and_has_value(self, client_name, reg_key, value):
        """Checks if a MA registry exists and has a given value.

            Args:
                client_name     (str)   --  client name

                reg_key         (str)   --  name of the registry

                value           (str)   --  the value of the key   

            Returns:
                bool    - True when registry exists and set to value
                        - False, otherwise
        """
        client_machine = Machine(
            client_name, username=self.preserve_node_username, password=self.preserve_node_password)
        result = client_machine.check_registry_exists('MediaAgent', reg_key)
        if not result:
            self.log.error(f"reg key {reg_key} doesn't exist")
            return False

        result = client_machine.get_registry_value('MediaAgent', reg_key)
        if result != value:
            self.log.error(f"reg key {reg_key} expected {value}, got {result}")
            return False
        return True

    def get_sp_version_from_cs(self, client_name):
        """Returns SP version as indicated by CS from client name.

            Args:
                client_name     (str)  --  client name

            Returns:
                sp_version   - the SP version

        """
        client = self.commcell.clients.get(client_name)
        return client.service_pack
    
    def get_os_version_from_cs(self, client_name):
        """Returns OS version as indicated by CS from client name.

            Args:
                client_name     (str)  --  client name

            Returns:
                os_version   - the OS version

        """
        client = self.commcell.clients.get(client_name)
        return client.os_info

    def is_remote_cache_present(self, client_name):
        """
            Returns whether remote cache present or not

            Args:
                client_name     (str)  --   client name

            Returns:
                present or not  (bool) --   remote cache present for the client

            Raises Exception if:
                - Failed to execute the api

                - Response is incorrect/empty

        """
        rc_helper = self.commcell.get_remote_cache(client_name)
        path = rc_helper.get_remote_cache_path()
        return bool(path)

    def get_or_create_policy(self, policy_name):
        """
            Gets or creates the storage policy from name

            Args:
                policy_name(str) -- storage policy name

            Returns:
                New/updated storage policy
        """
        storage_pool_obj = self.hyperscale_helper.get_storage_pool_details(
            self.storage_pool_name)
        storage_pool_details = storage_pool_obj.storage_pool_properties['storagePoolDetails']

        library_details = storage_pool_details['libraryList'][0]
        library_name = library_details['library']['libraryName']

        gdsp = storage_pool_obj.storage_pool_id
        gdsp_details = self.hyperscale_helper.get_policy_details(gdsp)
        gdsp_name = gdsp_details[2]

        if not self.commcell.storage_policies.has_policy(policy_name):
            self.log.info("Policy not exists, Creating %s", policy_name)
            policy = self.commcell.storage_policies.add(
                policy_name, library_name, self.other_mas[0], global_policy_name=gdsp_name)
            self.log.info("Created Policy %s", policy_name)
        else:
            self.log.info("Policy exists")
            policy = self.commcell.storage_policies.get(policy_name)
        return policy

    def check_gluster_shows_no_volumes_for_preserve_node(self):
        """
            Checks if gluster reports no volumes for preserve node

            Returns:
                result(bool) - whether it shows no volumes or not
        """
        ma_machine = Machine(
            self.preserve_node, username=self.preserve_node_username, password=self.preserve_node_password)
        output: UnixOutput = ma_machine.execute_command("gluster v info")
        if output.exception and output.exception_message.strip() == 'No volumes present':
            return True
        else:
            self.log.info(f"info output: {output.output}")
            return False

    def run_upgrade_job_till_completion(self, client_name):
        """Runs the upgrade job on the client. Blocks until completes

            Args:
                client_name     (str)       --  The command to run

            Returns:
                True   - The job ran till completion
                None   - Otherwise
            
        """
        client = self.commcell.clients.get(client_name)
        job_obj = client.push_servicepack_and_hotfix()
        if job_obj.wait_for_completion():
            return True
        return False

    def run_until_success(self, machine, command, retry_attempts=10, interval=5):
        """Runs a command untill it succeeds or retry attempts are exhausted.

            Args:
                machine         (Machine)   --  The machine object on which command will run

                command         (str)       --  The command to run

                retry_attempts  (int)       --  The max number of iterations to run the command

                interval        (int)       --  The number of seconds to wait between iterations

            Returns:
                command         (str)       -- The output of the command, if successful
                None                        -- Otherwise
            
        """
        self.log.info(
            f"Running untill success |{command}| for {retry_attempts} retry attempts, spaced every {interval}s")
        for _ in range(retry_attempts):
            output = machine.execute_command(command)
            output = output.output
            if not output:
                time.sleep(interval)
                continue
            return output

    def get_rc_value_after(self, machine, log_file, line_no):
        """Checks the return code log line (with retry attempts) from a particular line number and returns it.

            Args:
                machine     (Machine)   --  The machine object on which command will run

                log_file    (str)       --  The log file name to search for

                line_no     (int)       --  The line number from where to search

            Returns either:
                (True,  rc)             -- If log line was found, rc has return code
                (False, None)           -- Otherwise
            
        """
        command = f"tail -n +{line_no} '{log_file}' | grep -oE 'Command completed with rc=[[:digit:]]+' | head -1"
        output = self.run_until_success(machine, command)
        if not output:
            return False, None
        rc = output.split('rc=')[1]
        rc = int(rc)
        return True, rc

    def get_command_rc(self, machine, command, log_file):
        """Checks the command (with retry attempts) and returns the return code in a log file.

            Args:
                machine     (Machine)   --  The machine object on which command will run

                log_file    (str)       --  The log file name to search for

            Returns either:
                (True,  rc)             -- If log line was found, rc has return code
                (False, msg)            -- Otherwise, msg has error message
            
        """
        no = self.get_line_number_of_log(machine, log_file, command)
        if not no:
            return False, f"|{command}| not found in logs"
        result, rc = self.get_rc_value_after(machine, log_file, no)
        if not result:
            return False, f"rc value for |{command}| not found in logs"
        return True, rc

    def get_line_number_of_log(self, machine, log_file, log_line):
        # TODO: add from line as well here, merge with get_rc_value_after
        """Searches for a log line (with retry attempts) and returns it's line number.

        Args:
            machine     (Machine)   --  The machine object which has the log file

            log_file    (str)       --  The log file name to search for

            log_line    (int)       --  The log line to search

        Returns:
            no          (int)       -- The line number

        """
        command = f"grep -n '{log_line}' '{log_file}' | head -1"
        output = self.run_until_success(machine, command)
        if not output:
            return False
        no, line = output.split(':', 1)
        return no

    def check_refresh_logs(self, ma_name):
        """Checks if the logs related to the refresh operation are good

        Args:
            ma_name    (str)       --  The MA name on which the logs are to be checked

        Returns:
            result          (bool)       -- Whether logs are good or bad

        """
        ma_machine = Machine(ma_name, self.commcell)
        hostid = self.get_client_id(ma_name)
        pool_name = self.storage_pool_name

        CVMA_FILE = ma_machine.join_path(ma_machine.client_object.log_directory, 'CVMA.log')
        job_results_directory = self.preserve_node_job_results_directory
        install_dir = self.preserve_node_install_directory
        
        log_config_sequence = [
            ("Received CVMA_SCALEOUT_REFRESH_NODE_REQ", False),
            (f"cd /&&tar  -xzf  {job_results_directory}/ScaleOut/gls_metadata_node_{hostid}.tar.gz", True),
            ("service glusterd stop", True),
            ("cp -f /tmp/glusterd.info /var/lib/glusterd", True),
            ("service glusterd start", True),
            (f"{install_dir}/MediaAgent/cvavahi.py fix_gluster_volsize", True),
            (f"gluster volume heal {pool_name}", True),
            ("mount /ws/glus", True),
            ("Successfully mounted gluster volume", False),
            ("Successfully set regkey sHyperScalePreserve to False", False),
        ]
        for config in log_config_sequence:
            command, check_rc = config
            if check_rc:
                result, rc_or_error = self.get_command_rc(
                    ma_machine, command, CVMA_FILE)
                if not result:
                    self.log.error(rc_or_error)
                    return False
                rc = rc_or_error
                self.log.info(f"|{command}| returned {rc}")
                if rc != 0:
                    self.log.error(f"rc != 0. Aborting")
                    return False
            else:
                result = self.get_line_number_of_log(
                    ma_machine, CVMA_FILE, command)
                if not result:
                    self.log.error(f"Couldn't find |{command}| in logs")
                    return False
                self.log.info(f"|{command}| is at line no. {result}")

        return True

    def refresh_preserve_node(self):
        """Clicks on the refresh button via admin console
        """
        self.setup_admin_console()
        self.storage_helper.hyperscale_refresh_node(
            self.storage_pool_name, self.preserve_node)

    def get_log_lines(self, ma_machine, log_file_name):
        """Returns list of log lines for a given Windows MA and log file name.

            Args:
                ma_name         (str)       --  The name of Windows MA

                log_file_name   (str)       --  The log file name

            Returns:
                log_lines       (list[str]) -- The log lines

        """
        logs = ma_machine.get_log_file(log_file_name)
        lines = [l.strip() for l in logs.split('\n')]
        return lines

    def find_substring_in_string_list(self, substring, string_list):
        """Returns the first index where substring matches a string from a list

            Args:
                substring       (str)   --  The string to search

                string_list     (str)   --  The list to search in

            Returns:
                index           (int)   -- The index where match was found, -1, otherwise

        """
        for i, line in enumerate(string_list):
            if substring in line:
                return i
        return -1

    def validate_refresh_logs_on_mm(self, log_lines, logs_to_check):
        """Validates the refresh logs present on CS in MediaManager.log

            Args:
                log_lines       (list)   --  Actual logs to search in

                logs_to_check   (list)   --  Reference logs to search for

            Returns:
                result          (bool)   --  Whether the logs were present or not

        """
        for line in logs_to_check:
            res = self.find_substring_in_string_list(line, log_lines)
            if res == -1:
                self.log.error(f"Didn't find |{line}| in the MM logs")
                return False
            else:
                self.log.info(f"{log_lines[res]} validated")
        return True

    def validate_initial_refresh_logs_on_mm(self, log_lines):
        """Validates the initial refresh logs present on CS in MediaManager.log

            Args:
                log_lines       (list)   --  Actual logs to search in

            Returns:
                result          (bool)   --  Whether the logs were present or not

        """
        host_id = self.get_client_id(self.preserve_node)
        logs_to_check = [
            "Received Request to configure storage pool. RequestType[3]",
            f"Going to retrieve metadata info for hostId = [{host_id}] to location",
            f"START GLUSTER METADATA COPY to Host [{self.preserve_node}, {host_id}]",
        ]
        return self.validate_refresh_logs_on_mm(log_lines, logs_to_check)

    def validate_final_refresh_logs_on_mm(self, log_lines):
        """Validates the final refresh logs present on CS in MediaManager.log

            Args:
                log_lines       (list)   --  Actual logs to search in

            Returns:
                result          (bool)   --  Whether the logs were present or not

        """
        logs_to_check = [
            "Successfully completed refresh node action"
        ]
        return self.validate_refresh_logs_on_mm(log_lines, logs_to_check)

    def get_client_id(self, client_name):
        """Returns the client id from the client name

            Args:
                client_name     (str)   --  The client name

            Returns:
                id              (int)   -- The client id for the client name
            
            Raises:
                Exception, if client_name not found within Commcell

        """
        if self.commcell.clients.has_client(client_name):
            return self.commcell.clients[client_name.lower()]['id']
        raise Exception("Client {client_name} doesn't exist within the Commcell")

    def check_identical_output(self, ma_list, command):
        """Runs same command across multiple MAs for equality.

            Args:
                ma_list     (list)  --  list of MA names

                command (str)   --  the command to run

            Returns:
                (bool, result) - bool indicates if outputs are equal
                    result is {ma_name: command_output}, where
                    ma_name belongs to ma_list and
                    command_output is output of command for ma_name

            Note:
                The output must be single line
        """
        outputs = set()
        result = {}
        identical = True
        for ma in ma_list:
            ma_machine = Machine(ma, self.commcell)
            output = ma_machine.execute_command(command)
            output = output.formatted_output
            outputs.add(output)
            result[ma] = output
        if len(outputs) > 1:
            identical = False
        return identical, result

    def check_identical_values(self, ma_list, operation):
        """Runs same operation across multiple MAs for output equality.

            Args:
                ma_list             (list)      --  list of MA names

                operation       (method)    --  the operation to run
                    should accept ma_name and return output

            Returns:
                (bool, result) - bool indicates if outputs are equal
                    result is {ma_name: command_output}, where
                    ma_name belongs to ma_list and
                    command_output is output of command for ma_name

        """
        outputs = set()
        result = {}
        identical = True
        for ma in ma_list:
            output = operation(ma)
            outputs.add(output)
            result[ma] = output
        if len(outputs) > 1:
            identical = False
        return identical, result

    def get_client_test_data_folder(self, prefix, content_gb):
        """Returns the folder name which will be backed up

            Args:
                prefix      (str)   -- The string to add in folder name

                content_gb  (int)   -- The size of the data (used in name)

            Returns:
                name        (str)   -- The folder name
        """
        folder = f"Data{prefix}-{content_gb}Gb"
        return folder

    def create_test_data(self, prefix, content_gb):
        """Creates the test data with content_gb size

            Args:
                prefix      (str)   -- The string to add in folder name

                content_gb  (int)   -- The size of the data in gb

            Returns:
                path        (str)   -- The path where data will be created

        """
        folder = self.get_client_test_data_folder(prefix, content_gb)
        path = self.client_machine.join_path(self.test_data_path, folder)
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
        self.client_machine.create_directory(path)
        result = self.mmhelper_obj.create_uncompressable_data(self.client_name, path, content_gb)
        if not result:
            return False

        # looks like C:\\Automation\\54888\\Testdata\\Data1-1Gb
        return path
    
    def get_client_restore_path(self, prefix, content_gb):
        """Returns the path where restore happens

            Args:
                prefix      (str)   -- The string to add in folder name

                content_gb  (int)   -- The size of the data in gb

            Returns:
                path        (str)   -- The path where data will be restored

        """
        folder = self.get_client_test_data_folder(prefix, content_gb)
        path = self.client_machine.join_path(self.restore_data_path, folder)
        return path
    
    def cleanup_test_data(self):
        """Clears the test data directory
        """
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

    def is_node_down_from_gluster(self):
        """Checks if preserve node is down from gluster's perspective

            Returns:
                True, None          --  Node is down
                False, reason       --  Node is not down, failure reason

        """
        peer_status = self.hyperscale_helper.get_gluster_peer_status(self.other_mas[0])
        if len(peer_status) != len(self.other_mas):
            reason = f"Invalid number of peers {len(peer_status)} while validating"
            return False, reason
        for status in peer_status:
            ma, connected = status
            if not connected and ma == self.preserve_node_sds:
                continue
            if connected and ma in self.other_mas_sds:
                continue
            reason = f"Node {ma} connection status is {connected}, but should have been {not connected}"
            return False, reason
        self.log.info(
            f"gluster peer status connected for {self.other_mas} and disconnected for {self.preserve_node}")
        return True, None

    def verify_initial_request_logs(self):
        """Verifies the initial request logs in MM

            Returns:
                True, None          --  logs verified / logs rolled

                False, reason       --  failed to verify logs, failure reason

        """
        mm_logs_after_refresh = self.get_log_lines(self.client_machine, self.MEDIA_MANAGER_LOG)
        prev_mm_logs_len = len(self.mm_logs_before_refresh)
        if len(mm_logs_after_refresh) < prev_mm_logs_len:
            self.log.info(
                f"MM logs on server have rolled. Can't guarantee log integrity. Skipping log checking")
            logs = '\n'.join(mm_logs_after_refresh)
            self.log.info(f"{logs}")
            self.enforce_mm_logs = False
            return True, None
            
        self.enforce_mm_logs = True
        mm_refresh_logs = mm_logs_after_refresh[prev_mm_logs_len-1:]
        result = self.validate_initial_refresh_logs_on_mm(
            mm_refresh_logs)
        if not result:
            logs = '\n'.join(mm_refresh_logs)
            self.log.info(f"{logs}")
            reason = f"Initial MM logs couldn't be verified. Node refresh has failed"
            return False, reason

        self.log.info(f"Initial MM logs verified")
        return True, None

    def verify_final_mm_logs(self):
        """Verifies the final refresh logs in MM

            Returns:
                True, None          --  logs verified / logs rolled

                False, reason       --  failed to verify logs, failure reason

        """
        mm_logs_final = self.get_log_lines(self.client_machine, self.MEDIA_MANAGER_LOG)
        prev_mm_logs_len = len(self.mm_logs_before_refresh)
        if len(mm_logs_final) < prev_mm_logs_len:
            self.log.info(
                f"MM logs on server have rolled. Can't guarantee log integrity. Skipping final log checking")
            return True, None

        mm_refresh_logs = mm_logs_final[prev_mm_logs_len-1:]
        result = self.validate_final_refresh_logs_on_mm(mm_refresh_logs)
        if not result:
            logs = '\n'.join(mm_refresh_logs)
            self.log.info(f"{logs}")
            reason = f"Final MM logs couldn't be verified. Node refresh has failed"
            return False, reason

        self.log.info(f"Final MM logs verified")
        return True, None

    def fire_basic_setup_commands(self):
        """Sets up the node by executing basic commands
        """
        machine = Machine(self.preserve_node, username=self.preserve_node_username,
                          password=self.preserve_node_password)
        self.log.info("Changing time")
        command = 'mv /etc/localtime /etc/localtime.backup; ln -s /usr/share/zoneinfo/Asia/Calcutta /etc/localtime'
        machine.execute_command(command)

        self.log.info("Changing hostname")
        command = f'hostname {self.preserve_node}'
        machine.execute_command(command)

        log_directory = self.preserve_node_log_directory
        job_results_directory = self.preserve_node_job_results_directory

        command = f'echo "export cvma={log_directory}/CVMA.log" >> ~/.bashrc'
        machine.execute_command(command)
        command = f'echo "export logs={log_directory}" >> ~/.bashrc'
        machine.execute_command(command)
        command = f'echo "export sout={job_results_directory}/ScaleOut" >> ~/.bashrc'
        machine.execute_command(command)
        command = 'echo "TMOUT=0;export TMOUT" >> ~/.bashrc'
        machine.execute_command(command)

    def restore_network_and_register_to_cs(self):
        """Performs these manual steps automatically:

        +-------------------------------MANUAL STEPS TO BE PERFORMED------------------------------------+
        | Please power on preserve_node and reimage with preserve option. Perform these steps:          |
        | cd /opt/commvault/MediaAgent                                                                  |
        | ./cvavahi.py restore_network True /ws/disk1                                                   |
        | systemctl restart network                                                                     |
        | ./setupsds                                                                                    |
        +-----------------------------------------------------------------------------------------------+

            Returns:
                result (bool) - Whether successful or not

        """
        result = self.esx.vm_power_control_with_retry_attempts(self.preserve_node, 'off')
        if not result:
            self.log.error(f"Failed to power off {self.preserve_node}")
            return False
        time.sleep(2)

        result = self.esx.vm_power_control_with_retry_attempts(self.preserve_node, 'on')
        if not result:
            self.log.error(f"Failed to power on {self.preserve_node}")
            return False
        time.sleep(2)

        result = self.matcher.wait_till_screen(
            ScreenMatcher.BOOT_SCREEN_PRESS_ENTER, attempts=5)
        if not result:
            self.log.warning(f"Skipping BOOT_SCREEN_PRESS_ENTER after 5 attempts")
        else:
            self.log.info(f"Pressing enter to continue boot.")
            self.vm_io.send_key('enter')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.REIMAGE_SCREEN_INITIAL)
        if not result:
            self.log.error(f"Error waiting for REIMAGE_SCREEN_INITIAL")
            return False
        self.log.info(
            f"Navigating from REIMAGE_SCREEN_INITIAL to next screen...")
        self.vm_io.send_down_arrow()
        self.vm_io.send_down_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.REIMAGE_SCREEN_PRESERVE)
        if not result:
            self.log.error(f"Error waiting for REIMAGE_SCREEN_PRESERVE")
            return False
        self.log.info(
            f"Navigating from REIMAGE_SCREEN_PRESERVE to next screen...")
        self.vm_io.send_down_arrow()
        self.vm_io.send_down_arrow()
        self.vm_io.send_down_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_SYSTEM_DRIVE)
        if not result:
            self.log.error(f"Error waiting for INSTALL_SCREEN_SYSTEM_DRIVE")
            return False
        self.log.info(
            f"Navigating from INSTALL_SCREEN_SYSTEM_DRIVE to next screen...")
        self.vm_io.send_key('space')
        self.vm_io.send_down_arrow()
        self.vm_io.send_right_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_SUMMARY)
        if not result:
            self.log.error(f"Error waiting for INSTALL_SCREEN_SUMMARY")
            return False
        self.log.info(
            f"Navigating from INSTALL_SCREEN_SUMMARY to next screen...")
        self.vm_io.send_down_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_FINISHED, attempts=60, interval=5)
        if not result:
            self.log.error(f"Error waiting for INSTALL_SCREEN_FINISHED")
            return False
        self.log.info(f"Navigating from INSTALL_SCREEN_FINISHED for reboot")
        self.vm_io.send_key('space')

        self.log.info("Waiting 10 seconds for reboot countdown")
        time.sleep(10)

        self.log.info("Waiting 10 seconds for reboot")
        time.sleep(10)

        result = self.matcher.wait_till_screen(ScreenMatcher.LOGIN_SCREEN)
        if not result:
            self.log.error(f"Error waiting for LOGIN_SCREEN")
            return False
        self.log.info(f"Now logging in")
        self.vm_io.send_command(self.preserve_node_username)
        self.vm_io.send_command(self.preserve_node_password)
        time.sleep(2)

        path = f'{self.preserve_node_install_directory}/MediaAgent'
        self.log.info(f"Navigating to {path}")
        self.vm_io.send_command(f"cd {path}")

        command = './cvavahi.py restore_network True /ws/disk1'
        self.log.info(f"Firing {command}")
        self.vm_io.send_command(command)
        time.sleep(1)

        command = 'systemctl restart network'
        self.log.info(f"Firing {command}")
        self.vm_io.send_command(command)
        self.log.info("Waiting 30 seconds for network restart")
        time.sleep(30)
        
        self.fire_basic_setup_commands()
        self.log.info(f"Basic setup done for {self.preserve_node}")

        self.log.info(f"Running setupsds")
        self.vm_io.send_command("clear")
        self.vm_io.send_command("./setupsds")

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_INITIAL)
        if not result:
            self.log.error(f"Error waiting for SETUP_SCREEN_INITIAL")
            return False
        self.log.info(f"Navigating SETUP_SCREEN_INITIAL")
        self.vm_io.send_down_arrow()
        self.vm_io.send_text(self.preserve_node_password)
        self.vm_io.send_down_arrow()
        self.vm_io.send_text(self.preserve_node_password)
        self.vm_io.send_down_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_NETWORK)
        if not result:
            self.log.error(f"Error waiting for SETUP_SCREEN_NETWORK")
            return False
        self.log.info(f"Navigating from SETUP_SCREEN_NETWORK")
        self.vm_io.send_right_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_CS_INFO)
        if not result:
            self.log.error(f"Error waiting for SETUP_SCREEN_CS_INFO")
            return False
        self.log.info(f"Navigating SETUP_SCREEN_CS_INFO")
        self.vm_io.send_text(self.commcell.webconsole_hostname)
        self.vm_io.send_down_arrow()
        self.vm_io.send_text(self.username)
        self.vm_io.send_down_arrow()
        self.vm_io.send_text(self.password)
        self.vm_io.send_down_arrow()
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_SUCCESS)
        if not result:
            self.log.error(f"Error waiting for SETUP_SCREEN_SUCCESS")
            return False
        self.log.info(
            f"MA {self.preserve_node} registered with CS successfully. Waiting for restart to complete")
        time.sleep(30)
        return True

    def run_ddb_verification(self):
        """Runs DDB Verification
        
        Returns:
            result (bool)   --  Whether the job was successful or not

        """
        self.log.info("Now starting DDB verification")
        job = self.policy.run_ddb_verification('Primary', 'Full', 'DDB_VERIFICATION')
        if job.wait_for_completion():
            self.log.info("Successfully ran DDB Verification")
            return True
        else:
            return False

    def run(self):
        """Run function for this test case"""
        try:
            
            # 2. Check if nodes are available: flags=0
            for ma in self.mas:
                host_id = self.get_client_id(ma)
                available = self.hyperscale_helper.check_brick_available_status(host_id)
                if not available:
                    reason = f"Node {ma} doesn't have all the bricks available"
                    return self.fail_test_case(reason)
            self.log.info(f"All bricks available for {self.mas}")

            # 3. Check if nodes are on same commvault version
            result, outputs = self.check_identical_values(
                self.mas, self.get_sp_version_from_cs)
            if not result:
                reason = f"Commvault version mismatch between MAs: {outputs}"
                return self.fail_test_case(reason)
            self.log.info(f"All nodes running Commvault version {outputs}")

            # 4. Check if nodes are on same gluster version
            result, outputs = self.check_identical_output(
                self.mas, "gluster --version")
            if not result:
                reason = f"Gluster version mismatch between MAs: {outputs}"
                return self.fail_test_case(reason)
            self.log.info(f"All nodes running Gluster version {outputs}")

            # 5. Check if nodes are on same OS version
            result, outputs = self.check_identical_values(
                self.mas, self.get_os_version_from_cs)
            if not result:
                self.log.warning(f"OS version mismatch between MAs: {outputs}")
            else:
                self.log.info(f"All nodes running OS version {outputs}")

            # 6. Create HS storage pool & validate it
            self.log.info(f"Creating storage pool {self.storage_pool_name}")
            status, response = self.hyperscale_helper.create_storage_pool(
                self.storage_pool_name, *self.mas)
            self.log.info(
                f"Created storage pool with status: {status} and response: {response}")
            if not status:
                reason = "Storage pool creation failed"
                return self.fail_test_case(reason)

            result = self.hyperscale_helper.validate_storage(
                self.storage_pool_name)
            if not result:
                reason = f"Storage pool {self.storage_pool_name} couldn't be validated"
                return self.fail_test_case(reason)

            # 7. Create a storage policy
            self.policy = self.get_or_create_policy(self.storage_policy_name)
            
            # create data
            path1 = self.create_test_data("1", self.content_gb1)
            # Creating sub client
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[path1])

            # 8. Create a backupset and subclient and take the backup, restore, verify
            self.log.info("Starting Backup (small)")
            self.job_obj = self.subclient_obj.backup("FULL")
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            else:
                return self.fail_test_case("Backup (small) job failed")

            # 8b. Perform restore here
            self.log.info("Performing Restore (small)")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [path1])
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            else:
                return self.fail_test_case("Restore (small) job failed")
            
            # 8c. Now verify the restored data
            restore_path_1 = self.get_client_restore_path("1", self.content_gb1)
            self.hyperscale_helper.verify_restored_data(self.client_machine, path1, restore_path_1)

            # 9. Power off node2
            result = self.esx.vm_power_control_with_retry_attempts(self.preserve_node, 'off')
            if not result:
                reason = f"Failed to power off {self.preserve_node}"
                return self.fail_test_case(reason)

            # 10. Check readiness for node1,node2,node3 (node2 would fail)
            result = self.idautils.check_client_readiness(
                self.other_mas, False)  # False won't throw the exception
            if not result:
                reason = f"Checking readiness failed for {self.other_mas}"
                return self.fail_test_case(reason)
            self.log.info(f"Checking readiness succeeded for {self.other_mas}")

            result = self.idautils.check_client_readiness(
                [self.preserve_node], False)
            if result:
                reason = f"Node {self.preserve_node} shouldn't be ready. Was it turned off properly?"
                return self.fail_test_case(reason)
            self.log.info(f"{self.preserve_node} is offline as reported by CS")

            # 11. perform more checks to confirm that the node is really down
            # gluster peer status (node2 will be disconnected)
            # gluster v status (brick daemons will be missing)
            result, reason = self.is_node_down_from_gluster()
            if not result:
                return self.fail_test_case(reason)

            # 12. take large(20) GB backup, split into different subclients. Restore and verify
            path2 = self.create_test_data("2", self.content_gb2)
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[path1, path2])
            self.log.info("Starting Backup (large)")
            self.job_obj = self.subclient_obj.backup("FULL")
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            else:
                return self.fail_test_case("Backup (large) job failed")

            # 12b. Perform restore here
            self.log.info("Performing Restore (large)")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [path2])
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            else:
                return self.fail_test_case("Restore (large) job failed")
            
            # 12c. Now verify the restored data
            restore_path_2 = self.get_client_restore_path("2", self.content_gb2)
            self.hyperscale_helper.verify_restored_data(self.client_machine, path2, restore_path_2)
            
            # 13. Manual step automation
            result = self.restore_network_and_register_to_cs()
            if not result:
                reason = "Failed to run the manual steps automatically"
                return self.fail_test_case(reason)
            self.log.info("Successfully ran the manual steps automatically")

            # 14. check if gluster is running and shows no volumes
            result = self.check_gluster_shows_no_volumes_for_preserve_node()
            if not result:
                self.log.warning(
                    f"Gluster shows some volume. Either glusterd is not running or re-imaging failed for {self.preserve_node}. Continuing.")
            else:
                self.log.info(
                    f"Gluster is running and shows no volumes for {self.preserve_node}.")

            # 15. check if software remote cache is not located on node2 (can be placed above also)
            result = self.is_remote_cache_present(self.preserve_node)
            if result:
                reason = f"Remote cache present on the node {self.preserve_node} which has to be refreshed. Can't proceed further."
                # TODO: change the cache location and re-populate 
                return self.fail_test_case(reason)
            self.log.info(
                f"Remote cache not located on {self.preserve_node}. It can be refreshed.")

            # 16. check sHyperScalePreserve set to True
            result = self.check_registry_exists_and_has_value(
                self.preserve_node, self.PRESERVE_KEY, 'True')
            if not result:
                reason = f"{self.PRESERVE_KEY} is either absent or not set to True. Re-imaging with preserve option has failed."
                return self.fail_test_case(reason)
            self.log.info(f"{self.PRESERVE_KEY} is True")

            # 17a. check commvault version of preserve node as report by CS
            result = self.get_sp_version_from_cs(self.preserve_node)
            if not result:
                reason = f"Couldn't get SP version from CS for {self.preserve_node}"
                return self.fail_test_case(reason)
            sp_from_cs = int(result)

            # 17b. Attempt upgrade
            if sp_from_cs == 15:
                self.log.info(f"Running upgrade job for {self.preserve_node}")
                result = self.run_upgrade_job_till_completion(
                    self.preserve_node)
                if not result:
                    reason = f"Couldn't run the upgrade job for {self.preserve_node}"
                    return self.fail_test_case(reason)
                self.log.info(
                    f"Upgrade job completed for {self.preserve_node}")
            else:
                self.log.info(
                    f"Node is upto date, not running the upgrade job")

            # 18a. Check if CS contains the metadata, if not, show a warning
            result = None
            try:
                result = self.hyperscale_helper.check_gluster_metadata(self.storage_pool_name)
            except Exception as e:
                if str(e) != "Glustermeta data not present":
                    raise e
            if not result:
                self.log.warning(
                    f"Gluster metadata not present for {self.storage_pool_name}. Proceeding.")
            else:
                self.log.info(
                    f"Gluster metadata present for {self.storage_pool_name}")

            # 18b. Check if CSDB contains the metadata, if not, show a warning
            self.log.info(
                f"Checking for gluster metadata in CSDB for {self.preserve_node}")
            result = self.hyperscale_helper.is_gluster_metadata_present_in_csdb(
                self.preserve_node)
            if result:
                self.log.info(
                    f"Gluster metadata present in CSDB for {self.preserve_node}")
            else:
                self.log.warning(
                    f"Gluster metadata not present in CSDB for {self.preserve_node}. Proceeding.")

            # 18.5 Save MM logs so that log roll over can be detected
            self.mm_logs_before_refresh = self.get_log_lines(self.client_machine, self.MEDIA_MANAGER_LOG)

            # 19. Refresh the node using the command center GUI
            self.refresh_preserve_node()
            self.log.info(f"Node {self.preserve_node} refreshed")

            # TODO: check for node status messages begin, middle, end

            # 20a. Initial request logs on MM
            result, reason = self.verify_initial_request_logs()
            if not result:
                return self.fail_test_case(reason)

            # 20b. CVMA logs on the node
            result = self.check_refresh_logs(self.preserve_node)
            if not result:
                reason = f"Couldn't verify refresh logs"
                return self.fail_test_case(reason)
            self.log.info(f"Refresh logs verified and okay.")

            # 20c. Final MM logs on CS
            if self.enforce_mm_logs:
                result, reason = self.verify_final_mm_logs()
                if not result:
                    return self.fail_test_case(reason)

            # 21. check sHyperScalePreserve again set to false
            result = self.check_registry_exists_and_has_value(
                self.preserve_node, self.PRESERVE_KEY, 'False')
            if not result:
                reason = f"{self.PRESERVE_KEY} is either absent or not set to False"
                return self.fail_test_case(reason)
            self.log.info(f"{self.PRESERVE_KEY} changed back to False")

            # 22. compare capacity with step 8
            # TODO: capacity/used space with respect to command center along with df output

            # 23. wait for healing to complete
            # TODO: try via command center (status message is data is being recovered for this node)
            result = self.hyperscale_helper.gluster_heal_entries(
                self.preserve_node, self.storage_pool_name)
            if not result:
                reason = f"There was an error in the healing process for pool {self.storage_pool_name} @ {self.preserve_node}"
                return self.fail_test_case(reason)
            self.log.info(
                f"Successfully healed entries for {self.preserve_node}")

            # pre capacity check
            # 24. run commvault restart (to sync with CS, we are healed)
            # post capacity check
            self.log.info(
                f"restarting commvault services on {self.preserve_node}")
            self.hyperscale_helper.restart_services(self.preserve_node)

            # 25. Run a full backup job with node2 as the media agent. Restore and verify
            path3 = self.create_test_data("3", self.content_gb3)
            subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[path1, path2, path3])
            self.log.info(f"Running final backup through {self.preserve_node}")
            self.job_obj = subclient_obj.backup('FULL', advanced_options={'media_agent_name': self.preserve_node})
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            else:
                reason = f"The final job {self.job_obj.job_id} failed to complete through MA {self.preserve_node}"
                return self.fail_test_case(reason)
            
            # 25b. Perform restore here
            self.log.info("Performing Restore (final)")
            self.job_obj = subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [path3])
            if self.job_obj.wait_for_completion():
                self.log.info("Job status %s", self.job_obj.status)
            else:
                return self.fail_test_case("The final restore job failed")
            
            # 25c. Now verify the restored data
            restore_path_3 = self.get_client_restore_path("3", self.content_gb3)
            self.hyperscale_helper.verify_restored_data(self.client_machine, path3, restore_path_3)
            
            # 26. Also run DDB Verification Job
            result = self.run_ddb_verification()
            if not result:
                reason = "DDB Verification failed"
                self.fail_test_case(reason)

            self.successful = True
            # '''

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
