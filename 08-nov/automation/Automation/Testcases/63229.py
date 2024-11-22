# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test Case for HSX Node Refresh
Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()                      --  initialize TestCase class
    setup()                         --  setup function of this test case
    setup_vm_automation()           --  Initializes the VM automation helpers
    cleanup()                       --  Cleans up the test case resources and directories
    tear_down()                     --  Tear down function of this test case

    get_sp_version_from_cs()        -- Returns SP version as indicated by CS from client name

    is_remote_cache_present()   --  Returns whether remote cache present or not

    parse_which_commit_output()     -- Parses the ./whichCommit.sh output
    get_which_commit_output()       -- Retrieves the ./whichCommit.sh output for all MAs
    verify_output_changed_post_upgrade() -- Verifies that the output is different post upgrade
    parse_cluster_details()         -- Parses the cluster details output

    check_identical_values()        -- Runs same operation across multiple MAs for output equality.

    fail_test_case()                -- Prints failure reason, sets the result string

    get_client_content_folder()     -- Returns the folder path which will be backed up or restored to

    create_test_data()              -- Creates the test data with content_gb size

    cleanup_test_data()             -- Clears the test data directory

    get_log_lines()                 -- Returns list of log lines for a given Windows MA and log file name.

    setup_admin_console()           -- Logs in to the command center and initializes the storage helper

    get_client_id()                 -- Returns the client id from the client name

    get_rc_value_after()            -- Checks the return code log line (with retry attempts) from a particular line number and returns it.

    get_line_number_of_log()        -- Searches for a log line (with retry attempts) and returns it's line number.

    get_command_rc()                -- Checks the command (with retry attempts) and returns the return code in a log file.

    run_until_success()             -- Runs a command untill it succeeds or retry attempts are exhausted.

    check_refresh_logs()            -- Checks if the logs related to the refresh operation are good

    reimage_with_preserve()         -- Reimage with preserve option

    get_client_restore_path()       -- Returns the path where restore happens

    run_ddb_verification()          -- Runs DDB Verification

    check_registry_exists_and_has_value() -- Checks if a MA registry exists and has a given value.

    run()                           --  run function of this test case

    Sample input json
    "tc_id": {
            "VMNames": [
                None,
                None,
                None
            ],
            "ControlNodes": [
                None,
                None,
                None
            ],
            "CacheNode": {
                "name": None,
                "vmName": None,
                "username": None,
                "password": None,
            },
            "PreserveNode": {
                "name": None,
                "vmName": None,
                "username": None,
                "password": None
            },
            "StoragePoolName": None,
            # SqlLogin: None,       (OPTIONAL)
            # SqlPassword: None     (OPTIONAL)
        }
"""
# The following keys must be present under HyperScale key
# in config.json file
from pyVim import connect
from AutomationUtils import constants, commonutils
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from Server.JobManager.jobmanager_helper import JobManager
from MediaAgents.MAUtils.screen_matcher import ScreenMatcher
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.exceptions import CVTestCaseInitFailure
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.output_formatter import UnixOutput
from HyperScale.HyperScaleUtils.vm_io import VmIo
from HyperScale.HyperScaleUtils.esx_vm_io import EsxVmIo
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from AutomationUtils.vmoperations import VmOperations
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
import yaml
import atexit
import re
import time
import random

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


class TestCase(CVTestCase):
    """Hyperscale test class for HSX Node Refresh"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX Node Refresh"
        self.result_string = ""
        self.backupset = ""
        self.backupset_name = ""
        self.subclient_obj = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient_name = ""
        self.storage_policy = ""
        self.client_name = ""
        self.client_machine = ""
        self.cache_node = ""
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
        self.ma_machines = ""
        self.other_mas = ""
        self.other_mas_sds = ""
        self.config = ""
        self.mmhelper_obj = ""
        self.options_selector = ""
        self.content_gb = ""
        self.drive = ""
        self.test_case_path = ""
        self.test_data_path = ""
        self.content_path = ""
        self.restore_data_path = ""
        self.restore_path = ""
        self.hs_vm_config = ""
        self.vm_io = ""
        self.esx = ""
        self.tcinputs = {
            "VMNames": [
                None,
                None,
                None
            ],
            "ControlNodes": [
                None,
                None,
                None
            ],
            "CacheNode": {
                "name": None,
                "vmName": None,
                "username": None,
                "password": None,
            },
            "PreserveNode": {
                "name": None,
                "vmName": None,
                "username": None,
                "password": None
            },
            "StoragePoolName": None,
            # SqlLogin: None,       (OPTIONAL)
            # SqlPassword: None     (OPTIONAL)
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.cs_hostname = self.inputJSONnode['commcell']['webconsoleHostname']
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)

        # Cache node setup
        self.cache_node = self.tcinputs["CacheNode"]["name"]
        if not self.commcell.clients.has_client(self.cache_node):
            raise Exception(f"{self.cache_node} MA doesn't exist")
        self.cache_node_vm_name = self.tcinputs["CacheNode"].get("vmName", self.cache_node)
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]

        # Preserve node (node to be refreshed) setup
        self.preserve_node = self.tcinputs["PreserveNode"]["name"]
        self.preserve_node_vm_name = self.tcinputs["PreserveNode"].get("vmName", self.preserve_node)
        self.preserve_node_username = self.tcinputs["PreserveNode"]["username"]
        self.preserve_node_password = self.tcinputs["PreserveNode"]["password"]

        skip_preserve_node_machine_object = False # only for debugging purposes

        # MA setup
        self.mas = self.tcinputs["ControlNodes"]
        self.vm_names = self.tcinputs.get("VMNames", self.mas)
        self.ma_machines = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            
            if ma_name == self.preserve_node and skip_preserve_node_machine_object:
                continue
            self.log.info(f"Creating machine object for: {ma_name}")

            try:
                machine = Machine(
                    ma_name, username=self.cache_node_username, password=self.cache_node_password)
            except Exception as e:
                if "Authentication Failed." in str(e) and ma_name == self.preserve_node:
                    self.log.warning(
                        "Using default credentials for preserve node")
                    machine = Machine(
                        ma_name, username=self.preserve_node_username, password=self.preserve_node_password)
                else:
                    raise

            self.ma_machines[ma_name] = machine
        if self.cache_node == self.preserve_node and skip_preserve_node_machine_object:
            pass
        else:
            self.cache_machine = self.ma_machines[self.cache_node]
        self.other_mas = [ma for ma in self.mas if ma != self.preserve_node]
        self.other_mas_sds = [f'{ma}sds' for ma in self.other_mas]

        # Node which will run the newer refresh task
        task_node_index = random.randint(0, len(self.other_mas)-1)
        self.task_node = self.other_mas[task_node_index]
        self.task_node_vm_name = self.vm_names[self.mas.index(self.task_node)]
        self.log.info(f"Task node: {self.task_node}")

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get('SqlLogin')
        tcinputs_sql_password = self.tcinputs.get('SqlPassword')
        if tcinputs_sql_login is None:
            # go for default credentials
            if not hasattr(self.config.SQL, 'Username'):
                raise Exception(
                    f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs")
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, 'Password'):
                raise Exception(
                    f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

        # saving this now because when the commvault services are down
        # these values aren't correct / are None
        preserve_node_client = self.commcell.clients.get(self.preserve_node)
        self.preserve_node_log_directory = preserve_node_client.log_directory
        self.preserve_node_log_directory = "/var/log/commvault/Log_Files"
        self.preserve_node_job_results_directory = preserve_node_client.job_results_directory
        self.preserve_node_install_directory = preserve_node_client.install_directory
        if (not self.preserve_node_log_directory) or (not self.preserve_node_job_results_directory):
            message = f"Please check if {self.preserve_node} is up including Commvault services."
            message += f" log directory = {self.preserve_node_log_directory}."
            message += f" job results directory = {self.preserve_node_job_results_directory}."
            raise Exception(message)

        # Subclient & Storage setup
        self.storage_pool_name = self.tcinputs.get('StoragePoolName')
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset_name = "defaultBackupSet"
        self.backupset = self.agent.backupsets.get(self.backupset_name)
        self.subclient_name = f"{self.id}_subclient"
        self.storage_policy_name = f"{self.id}_policy"
        self.mmhelper_obj = MMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.content_gb = 1
        self.drive = self.options_selector.get_drive(
            self.client_machine, 2 * self.content_gb * 1024)

        # Backup and restore paths
        self.test_case_path = self.client_machine.join_path(
            self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(
            self.test_case_path, "Testdata")
        self.content_path = self.get_client_content_folder(
            '1', self.content_gb, self.test_data_path)
        self.restore_data_path = self.client_machine.join_path(
            self.test_case_path, 'Restore')
        self.restore_path = self.get_client_content_folder(
            '1', self.content_gb, self.restore_data_path)
        self.hyperscale_helper = HyperScaleHelper(
            self.commcell, self.csdb, self.log)

        self.hsx3_or_above = self.hyperscale_helper.is_hsx_node_version_equal_or_above(
            self.ma_machines[self.other_mas[0]], 3
        )

        # VM setup
        if not hasattr(self.config.HyperScale, 'VMConfig'):
            raise Exception(
                f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}")
        self.hs_vm_config = self.config.HyperScale.VMConfig
        self.setup_vm_automation(self.preserve_node_vm_name)
        
        self.PRESERVE_KEY = 'sHyperScalePreserve'

    def setup_vm_automation(self, vm_name):
        """Initializes the VM automation helpers"""
        server_type = VmIo.SERVER_TYPE_ESX
        self.server_hostname = self.hs_vm_config.ServerHostName
        self.server_username = self.hs_vm_config.Username
        self.server_password = self.hs_vm_config.Password
        vm_config = {
            'server_type': server_type,
            'server_host_name': self.server_hostname,
            'username': self.server_username,
            'password': self.server_password
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(
            vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io = VmIo(
            vm_name, server_type, self.server_hostname, self.server_username, self.server_password, self.esx)
        self.vm = self.vm_io._vm_obj
        self.matcher = ScreenMatcher(self.vm_io)

    def cleanup(self):
        """Cleans up the test case resources and directories"""

        policy_exists = self.commcell.storage_policies.has_policy(
            self.storage_policy_name)
        if policy_exists:
            policy_obj = self.commcell.storage_policies.get(
                self.storage_policy_name)
            # TODO: kill all jobs related to the subclient before doing this
            policy_obj.reassociate_all_subclients()
            self.log.info(
                f"Reassociated all {self.storage_policy_name} subclients")
        if self.backupset.subclients.has_subclient(self.subclient_name):
            self.backupset.subclients.delete(self.subclient_name)
            self.log.info(f"{self.subclient_name} deleted")
        if policy_exists:
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info(f"{self.storage_policy_name} deleted")
        self.cleanup_test_data()

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(
                f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})")
            self.cleanup()
        else:
            self.log.warning("Not cleaning up as the run was not successful")
            self.status = constants.FAILED

    def get_sp_version_from_cs(self, client_name):
        """Returns SP version as indicated by CS from client name.
            Args:
                client_name     (str)  --  client name
            Returns:
                sp_version   - the SP version
        """
        client = self.commcell.clients.get(client_name)
        return client.service_pack

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

    def parse_which_commit_output(self, output):
        """Parses the ./whichCommit.sh output
            Args:
                output   (str)   --  The output from ./whichCommit.sh script
            Returns:
                result  (dict)  --  The parsed output. {CommitId: '', Branch: ''}
        """
        output = output.replace("\n ", "")
        regex = r'(CommitId|Branch): (.*)'
        matches = re.findall(regex, output)
        if not matches:
            return None
        parsed = {tag: value for tag, value in matches}
        return parsed

    def get_which_commit_output(self):
        """Retrieves the ./whichCommit.sh output for all MAs
        output: {ma1: value1, ma2: value2, ma3: value3}
            Args:
                output   (str)   --  The output from ./whichCommit.sh script
            Returns:
                result  (dict)  --  The parsed output. {CommitId: output, Branch: output}
        """
        command = "/usr/local/hedvig/scripts/whichCommit.sh"
        identical, result = self.hyperscale_helper.check_identical_output(
            self.mas, self.ma_machines, command)
        if not identical:
            self.log.warning(f"./whichCommit.sh outputs differ. Proceeding")
        else:
            self.log.info("./whichCommit.sh outputs match")
        which_commit_outputs = {}
        for ma_name, output in result.items():
            parsed = self.parse_which_commit_output(output)
            if not parsed:
                self.log.error(f"./whichCommit.sh parse failed for {ma_name}")
                return None
            for key in sorted(parsed.keys()):
                value = which_commit_outputs.get(key, {})
                value[ma_name] = parsed[key]
                which_commit_outputs[key] = value
        return which_commit_outputs

    def verify_output_changed_post_upgrade(self, pre_output, post_output):
        """Verifies that the output is different post upgrade
        output: {ma1: value1, ma2: value2, ma3: value3}
            Args:
                pre_output  (output)    --  The output before upgrade
                post_output (output)    --  The output after upgrade
            Returns:
                result      (bool)      --  If the output is different or not
        """
        for ma in self.mas:
            pre = pre_output[ma]
            post = post_output[ma]
            if pre == post:
                self.log.error(f"{ma} has same {pre} post upgrade")
                return False
            self.log.info(f"{ma} output changed from {pre} to {post}")
        return True

    def parse_cluster_details(self):
        """Parses the cluster details output
            Returns:
                result (bool)   -- Whether parsed or not
        """
        machine = self.ma_machines[self.mas[0]]
        cluster_name = self.hyperscale_helper.get_hedvig_cluster_name(machine)
        if not cluster_name:
            self.log.error("Couldn't get the cluster name")
            return False
        path = '/opt/hedvig/bin/hv_deploy'
        command = f'su -l -c "env HV_PUBKEY=1 {path} --check_cluster_status_detail --cluster_name {cluster_name}" admin'
        identical, result = self.hyperscale_helper.check_identical_output(
            self.mas, self.ma_machines, command)
        if not result:
            self.log.error(f"Unable to get cluster details")
            return False
        self.log.info("Cluster details were parsed")
        return True

    def check_identical_values(self, ma_list, operation):
        """Runs same operation across multiple MAs for output equality.
            Args:
                ma_list         (list)      --  list of MA names
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

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string
            Args:
                reason         (str)   --  Failure reason
        """
        self.log.error(reason)
        self.result_string = reason
        self.status = constants.FAILED

    def get_client_content_folder(self, prefix, content_gb, parent=None):
        """Returns the folder path which will be backed up or restored to
            Args:
                prefix      (str)   -- The string to add in folder name
                content_gb  (int)   -- The size of the data (used in name)
                parent      (str)   -- The parent path to join to (optional)
            Returns:
                name        (str)   -- The folder name
        """
        folder = f"Data{prefix}-{content_gb}Gb"
        if parent:
            folder = self.client_machine.join_path(self.test_data_path, folder)
        return folder

    def create_test_data(self, path, content_gb):
        """Creates the test data with content_gb size at given path
            Args:
                path        (str)   -- The path where data is to be created
                content_gb  (int)   -- The size of the data in gb
            Returns:
                result      (bool)  -- If data got created
        """
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
        self.client_machine.create_directory(path)
        result = self.mmhelper_obj.create_uncompressable_data(
            self.client_name, path, content_gb)
        if not result:
            return False
        return True

    def cleanup_test_data(self):
        """Clears the test data directory
        """
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

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
        raise Exception(
            "Client {client_name} doesn't exist within the Commcell")

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

    def get_line_number_of_log(self, machine, log_file, log_line):
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

    def get_command_rc(self, machine, command, log_file):
        """Checks the command (with retry attempts) and returns the return code in a log file.

            Args:
                machine     (Machine)   --  The machine object on which command will run

                log_file    (str)       --  The log file name to search for

                command     (str)       --  The command we are getting rc for

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

        CVMA_FILE = ma_machine.join_path(
            ma_machine.client_object.log_directory, 'CVMA.log')
        job_results_directory = self.preserve_node_job_results_directory
        install_dir = self.preserve_node_install_directory

        log_config_sequence = [
            ("Received CVMA_SCALEOUT_REFRESH_NODE_REQ", False),
            (f"Node : {ma_name} is restored successfully", False),
            (f"{install_dir}/cvavahi.py delete_noderefresh_key", True)
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

    def reimage_with_preserve(self):
        """Reimages the node to be refreshed with "Preserve drives" option

            Returns:
                result (bool) - Whether successful or not

        """
        result = self.esx.vm_power_control_with_retry_attempts(
            self.preserve_node_vm_name, 'off', retry_attempts=10)
        if not result:
            self.log.error(f"Failed to power off {self.preserve_node_vm_name}")
            return False
        time.sleep(2)

        self.esx.vm_set_cd_rom_enabled(self.preserve_node_vm_name, True)

        result = self.esx.vm_power_control_with_retry_attempts(
            self.preserve_node_vm_name, 'on')
        if not result:
            self.log.error(f"Failed to power on {self.preserve_node_vm_name}")
            return False
        time.sleep(2)

        result = self.matcher.wait_till_screen(
            ScreenMatcher.BOOT_SCREEN_PRESS_ENTER, attempts=5)
        if not result:
            self.log.warning(
                f"Skipping BOOT_SCREEN_PRESS_ENTER after 5 attempts")
        else:
            self.log.info(f"Pressing enter to continue boot.")
            self.vm_io.send_key('enter')
        time.sleep(60)
        result = self.matcher.wait_till_screen(
            ScreenMatcher.REIMAGE_SCREEN_INITIAL, attempts=40)
        if not result:
            self.log.error(f"Error waiting for REIMAGE_SCREEN_INITIAL")
            return False
        self.log.info(
            f"Navigating from REIMAGE_SCREEN_INITIAL to next screen...")
        self.vm_io.send_down_arrow()
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
        self.vm_io.send_down_arrow() # extra down arrow for 3.x
        self.vm_io.send_key('space')

        result = self.matcher.wait_till_either_screen(
            [ScreenMatcher.INSTALL_SCREEN_FINISHED, ScreenMatcher.INSTALL_SCREEN_SYSTEM_DRIVE], attempts=150, interval=5)
        if not result:
            self.log.error(f"Error waiting for INSTALL_SCREEN_FINISHED / INSTALL_SCREEN_SYSTEM_DRIVE")
            return False
        if result == ScreenMatcher.INSTALL_SCREEN_SYSTEM_DRIVE:
            self.vm_io.send_key('space') # select the OS drive
            self.vm_io.send_down_arrow() # goes to back
            self.vm_io.send_right_arrow() # goes to next
            self.vm_io.send_key('space') # next
            
        result = self.matcher.wait_till_either_screen(
            [ScreenMatcher.INSTALL_SCREEN_FINISHED, ScreenMatcher.INSTALL_SCREEN_SUMMARY_HSX], attempts=150, interval=5)
        if not result:
            self.log.error(f"Error waiting for INSTALL_SCREEN_FINISHED / INSTALL_SCREEN_SUMMARY_HSX")
            return False
        if result == ScreenMatcher.INSTALL_SCREEN_SUMMARY_HSX:
            self.vm_io.send_down_arrow() # goes to apply
            self.vm_io.send_key('space') # apply
        
        result = self.matcher.wait_till_screen(
            ScreenMatcher.INSTALL_SCREEN_FINISHED, attempts=150, interval=5)
        if not result:
            self.log.error(f"Error waiting for INSTALL_SCREEN_FINISHED")
            return False
            
        self.log.info(f"Navigating from INSTALL_SCREEN_FINISHED for reboot")
        self.vm_io.send_key('space')

        self.log.info("Waiting 10 seconds for reboot countdown")
        time.sleep(10)

        self.log.info("Waiting 10 seconds for reboot")
        time.sleep(10)

        return True

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

    def run_ddb_verification(self):
        """Runs DDB Verification

        Returns:
            result (bool)   --  Whether the job was successful or not

        """
        self.log.info("Now starting DDB verification")
        job = self.policy.run_ddb_verification(
            'Primary', 'Full', 'DDB_VERIFICATION')
        if job.wait_for_completion():
            self.log.info("Successfully ran DDB Verification")
            return True
        else:
            return False

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
        client_machine = self.ma_machines[client_name]
        result = client_machine.check_registry_exists('MediaAgent', reg_key)
        if not result:
            self.log.error(f"reg key {reg_key} doesn't exist")
            return False

        result = client_machine.get_registry_value('MediaAgent', reg_key)
        if result != value:
            self.log.error(f"reg key {reg_key} expected {value}, got {result}")
            return False

        return True

    def restore_node_fr28(self):
        """Runs the restore node command (legacy)

            Returns:

                bool, str    - whether successful or not and reason if any

        """
        path = f'/opt/commvault/MediaAgent'
        self.log.info(f"Navigating to {path}")
        self.vm_io.send_command(f"cd {path}")

        command = './cvavahi.py restore_node'
        self.log.info(f"Firing {command}")
        self.vm_io.send_command(command)
        time.sleep(5)

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_ROOT_PASSWORD)
        if not result:
            reason = f"Error waiting for SETUP_SCREEN_ROOT_PASSWORD"
            return False, reason
        self.log.info(
            f"sending root password for preserve node : {self.preserve_node}")
        self.vm_io.send_text(self.cache_node_password)
        self.vm_io.send_key('enter')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_COMMSERVE_FQDN)
        if not result:
            reason = f"Error waiting for SETUP_SCREEN_COMMSERVE_FQDN"
            return False, reason
        self.log.info(f"sending commserve : {self.client_name} FQDN")
        self.vm_io.send_text(self.commcell.webconsole_hostname)
        self.vm_io.send_key('enter')

        self.log.info(f"sending commserve : {self.client_name} creds")
        self.vm_io.send_text(self.username)
        self.vm_io.send_key('enter')
        self.vm_io.send_text(self.password)
        self.vm_io.send_key('enter')

        result = self.matcher.wait_till_screen(
            ScreenMatcher.SETUP_SCREEN_REGISTRATION_SUCCESS)
        if not result:
            reason = f"Error waiting for SETUP_SCREEN_REGISTRATION_SUCCESS"
            return False, reason

        return True, None

    def restore_node_latest(self):
        """Runs the restore node command (latest)

            Returns:
                bool, str    - whether successful or not and reason if any
        """
        args = (self.server_hostname, self.server_username, self.server_password,
                self.cs_hostname, self.username, self.password, 
                self.task_node, self.task_node_vm_name, self.cache_node_username, self.cache_node_password, 
                self.preserve_node, self.storage_pool_name)
        result = self.hyperscale_helper.cvmanager_refresh_node_task(*args)
        if not result:
            return False, "Failure in running the refresh node task"
        return True, None

    def is_legacy_refresh_operation(self):
        """Returns whether we are refreshing using a legacy operation

            Returns:
                bool    -   Whether legacy or not
        """
        _, major, _ = self.commcell.version.split('.')
        return int(major) <= 28

    def run(self):
        """ run function of this test case"""
        try:
            # Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()

            # This introduces a bug wherein all the cluster nodes become offline
            # refer: "check readiness failure for hsx cluster 24 hours after add node"
            # 1. Disable CD-ROM on available nodes
            # result, reason = self.hyperscale_helper.reboot_and_disable_cd_rom(self.esx, self.vm_names, self.mas) 
            # if not result:
            #     return self.fail_test_case(reason)
            
            remote_cache_client = self.commcell.clients.get(self.cache_node)

            # self.log.info("Setting up VM automation again to avoid timeouts")
            # self.setup_vm_automation(self.cache_node_vm_name)
            # # Login via console
            # self.vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
            # time.sleep(10)
            # self.vm_io.send_command(self.cache_node_username)
            # self.vm_io.send_command(self.cache_node_password)
            # time.sleep(2)

            # 4. Check if remote cache is present on cache_node
            self.log.info(
                f"Checking if remote cache is present on {self.cache_node}")
            result = self.hyperscale_helper.is_remote_cache_present(
                self.cache_node)
            if not result:
                reason = f"Cache node {self.cache_node} doesn't have the remote cache setup."
                return self.fail_test_case(reason)
            self.log.info(f"Cache node {self.cache_node} has the remote cache")

            # 5. Sync the cache so that nodes can be updated to latest SP
            self.log.info(
                "syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(
                f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(
                f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 6. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(
                    f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 7. Check SP Version
            self.log.info("Checking SP version for all nodes")
            result, outputs = self.check_identical_values(
                self.mas, self.get_sp_version_from_cs)
            if not result:
                self.log.error(
                    f"Nodes have version mismatch {outputs}. Proceeding")
            self.log.info(
                f"All nodes have same version {outputs[self.mas[0]]}")

            # 8. Create a storage pool, if not already there
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(
                    f"Creating storage pool {self.storage_pool_name}")
                status, response = self.hyperscale_helper.create_storage_pool(
                    self.storage_pool_name, *self.mas)
                self.log.info(
                    f"Created storage pool with status: {status} and response: {response}")
                if not status:
                    reason = "Storage pool creation failed"
                    return self.fail_test_case(reason)
            else:
                self.log.info(
                    f"Skipping storage pool creation as {self.storage_pool_name} already exists")

            # 9a. Parse --check_cluster_status_detail output
            self.log.info("--check_cluster_status_detail")
            if not self.parse_cluster_details():
                reason = "Failed to parse check_cluster_status_detail"
                return self.fail_test_case(reason)
            self.log.info("Parsed check_cluster_status_detail output")
            # 9b. Verify nfsstat -m output
            self.log.info("Verifying nfsstat -m output")
            if not self.hyperscale_helper.verify_nfsstat_output(self.mas, self.ma_machines):
                reason = "Failed to verify nfsstat"
                # return self.fail_test_case(reason) # the newly added node doesn't have the same params so it fails here
            self.log.info("Verified nfsstat -m output")
            # 9c. Verify df -kht nfs4 output
            self.log.info("Verifying df -kht nfs4 output")
            if not self.hyperscale_helper.verify_df_kht_nfs4_output(self.mas, self.ma_machines):
                reason = "Failed to verify df -kht nfs4"
                return self.fail_test_case(reason)
            self.log.info("Verified df -kht nfs4 output")
            # 9d. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(
                self.mas[:3], self.ma_machines)
            if len(self.mas)>3: # for newly added nodes, check for only hpod
                result = result and self.hyperscale_helper.verify_hedvig_services_are_up(
                self.mas[3:], self.ma_machines, services=['hedvighblock'])
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info(
                "Successfully verified hedvig services are up and running")

            # 10. Check if commvault service and processes are up
            self.log.info(
                "Verify if commvault service and processes are up post hedvig upgrade")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(
                self.mas, self.ma_machines)
            
            if not result:
                reason = "Failed to verify if commvault service and processes are up post hedvig upgrade"
                return self.fail_test_case(reason)
            self.log.info(
                f"Successfully verified commvault service and processes are up post hedvig upgrade")

            # 12a. Backup: create test data
            self.log.info("Proceeding to take backup before Refresh node")
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")

            # 12b. Backup: take full backup
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0],
                                                                      self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(
                content_path=[self.content_path])
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation(self.preserve_node_vm_name)
            time.sleep(2)
            
            # Take a backup of Log files
            log_files_path = '/var/log/commvault/Log_Files'
            log_files_tarball = f"Log_Files_"+time.strftime("%Y-%m-%d_%H-%M-%S")+".tar.gz"
            self.ma_machines[self.preserve_node].execute(f"tar -czvf ~/{log_files_tarball} {log_files_path}")
            self.ma_machines[self.preserve_node].execute(f"scp -o StrictHostKeyChecking=no ~/{log_files_tarball} root@{self.other_mas[0]}:")

            # 13. Manual step automation
            result = self.reimage_with_preserve()
            if not result:
                reason = "Failed to reimage with preserve option"
                return self.fail_test_case(reason)
            self.log.info("Successfully reimaged with preserve option")

            # 14. check whether the node is online
            result = self.hyperscale_helper.wait_for_ping_result_to_be(
                0, self.preserve_node)
            if not result:
                reason = f"Failure while waiting for power on to complete for {self.preserve_node}"
                return self.fail_test_case(reason)
            self.log.info(f"{self.preserve_node} is back online")
            time.sleep(10)

            self.ma_machines[self.preserve_node] = Machine(
                self.preserve_node, username=self.preserve_node_username, password=self.preserve_node_password)

            # 15. verify hosts file on Preserve node
            command = "cat /etc/hosts | sort"
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, command)
            if not identical:
                reason = f"/etc/hosts file is inconsistent on {self.preserve_node} after reimage"
                return self.fail_test_case(reason)
            self.log.info(
                f"Hosts file is consistent on {self.preserve_node} after reimage ")

            # 16. restore_node and register to cs
            if self.is_legacy_refresh_operation():
                result, reason = self.restore_node_fr28()
            else:
                result, reason = self.restore_node_latest()
            if not result:
                return self.fail_test_case(reason)
            self.log.info("Successfully fired the restore node command")

            # 16.5
            # better to sync the RC node otherwise the upgrade job will fail saying that the RC doesn't have packages
            self.log.info(
                "syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(
                f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(
                f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 17. upgrade refreshed to latest SP
            client = self.commcell.clients.get(self.preserve_node)
            job_obj = client.push_servicepack_and_hotfix()
            self.log.info(
                f"Started update job ({job_obj.job_id}) for {self.preserve_node}")
            if not job_obj.wait_for_completion():
                reason = f"{self.preserve_node} update job {job_obj.job_id} failed to complete"
                return self.fail_test_case(reason)
            self.log.info(
                f"Refreshed node {self.preserve_node} updated to the latest SP")
            
            if self.hsx3_or_above:
                result, reason = HyperscaleSetup.ensure_root_access(
                    commcell=self.commcell, node_hostnames=[self.preserve_node], node_root_password=self.cache_node_password)
                if not result:
                    return self.fail_test_case(reason)
                self.log.info("Successfully enabled root on the refreshed node")
                
                result = HyperscaleSetup.firewall_add_icmp_rule(
                    host=self.hs_vm_config.ServerHostName,
                    user=self.hs_vm_config.Username,
                    password=self.hs_vm_config.Password,
                    vm_names=[self.preserve_node_vm_name],
                    vm_hostnames=[self.preserve_node],
                    root_password=self.cache_node_password)
                if not result:
                    reason = f"Failed to add icmp rule"
                    return self.fail_test_case(reason)
                self.log.info("Successfully enabled ICMP traffic")
                
            self.ma_machines[self.preserve_node] = Machine(
                self.preserve_node, username=self.cache_node_username, password=self.cache_node_password)

            if self.is_legacy_refresh_operation():
                # 18. check if software remote cache is not located on node2 (can be placed above also)
                result = self.is_remote_cache_present(self.preserve_node)
                if result:
                    reason = f"Remote cache present on the node {self.preserve_node} which has to be refreshed. Can't proceed further."
                    return self.fail_test_case(reason)
                self.log.info(
                    f"Remote cache not located on {self.preserve_node}. It can be refreshed.")
                # 19. check sHyperScalePreserve set to True
                result = self.check_registry_exists_and_has_value(
                    self.preserve_node, self.PRESERVE_KEY, 'True')
                if not result:
                    reason = f"{self.PRESERVE_KEY} is either absent or not set to True. Re-imaging with preserve option has failed."
                    return self.fail_test_case(reason)
                self.log.info(f"{self.PRESERVE_KEY} is True")

                # 20.a Refresh the node using the API
                self.hyperscale_helper.trigger_node_refresh(
                    self.storage_pool_name, self.preserve_node)
                self.log.info(f"Node {self.preserve_node} refreshed")

                # 20b. CVMA logs on the node
                result = self.check_refresh_logs(self.preserve_node)
                if not result:
                    reason = f"Couldn't verify refresh logs"
                    return self.fail_test_case(reason)
                self.log.info(f"Refresh logs verified and okay.")

            # 21. check sHyperScalePreserve again set to false
            result = self.check_registry_exists_and_has_value(
                self.preserve_node, self.PRESERVE_KEY, 'False')
            if not result:
                reason = f"{self.PRESERVE_KEY} is either absent or not set to False"
                return self.fail_test_case(reason)
            self.log.info(f"{self.PRESERVE_KEY} changed back to False")

            # 22. Perform restore here
            self.log.info("Performing Restore")
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0],
                                                                      self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(
                content_path=[self.content_path])
            job_obj = self.subclient_obj.restore_out_of_place(
                self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s",
                          job_obj.status)

            # 23. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(
                self.client_machine, self.content_path, self.restore_path)

            # 26. Also run DDB Verification Job
            result = self.run_ddb_verification()
            if not result:
                reason = "DDB Verification failed"
                self.fail_test_case(reason)

            self.successful = True

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
