# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for OS Upgrade
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
      
    is_remote_cache_present()       -- Returns whether remote cache present or not
      
    populate_remote_cache()         -- Populates the remote cache with Unix RPMs
      
    run_until_success()             -- Runs a command untill it succeeds or tries are exhausted.
      
    grep_after_line()               -- Finds text in a log file with offset and tries
      
    monitor_pre_upgrade_logs_to_set_upgrade_sequence()  -- Parses the logs to figure out the node sequence used for upgrade
      
    should_upgrade_proceed()        -- Checks if the upgrade proceeds or not.
      
    monitor_os_upgrade_begin_logs() -- Verifies the pre-upgrade logs
      
    verify_yum_logs()               -- Verifies the yum logs on the MA machine           
      
    verify_logs_for_node()          -- Verifies the logs for the node being upgraded 
      
    check_identical_output()        -- Runs same command across multiple MAs for equality.
      
    check_identical_values()        -- Runs same operation across multiple MAs for output equality.
      
    monitor_remote_cache_logs()     -- Verifies the logs for the remote cache node
      
    fail_test_case()                -- Prints failure reason, sets the result string
      
    get_or_create_policy()          -- Gets or creates the storage policy from name
      
    get_client_content_folder()     -- Returns the folder path which will be backed up or restored to
      
    create_test_data()              -- Creates the test data with content_gb size
      
    cleanup_test_data()             -- Clears the test data directory
      
    run()                           --  run function of this test case
      

Sample input json
"54394": {
            "ControlNodes": {
              "MA1": "name",
              "MA2": "name",
              "MA3": "name"
            },
            "CacheNode": {
              "name": "name",
              "username": "username",
              "password": "password"
            },
            SqlLogin: login,        (OPTIONAL)
            SqlPassword: password   (OPTIONAL)
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

import time
import atexit
from cvpysdk.deployment.deploymentconstants import DownloadOptions, DownloadPackages
from pyVim import connect
from pyVim.task import WaitForTask
from pyVmomi import vim

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Hyperscale test class for OS Upgrade"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HS1.5 OS Upgrade"
        self.result_string = ""
        self.backupset = ""
        self.subclient_obj = ""
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
            # "VMMANames": [] (OPTIONAL)
            "CacheNode": {
                "name": None,
                "username": None,
                "password": None,
                # "vmname": None, (OPTIONAL)
            },
            # SqlLogin: None,       (OPTIONAL)
            # SqlPassword: None     (OPTIONAL)
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)

        # Cache node setup
        self.cache_node = self.tcinputs["CacheNode"]["name"]
        if not self.commcell.clients.has_client(self.cache_node):
            raise Exception(f"{self.cache_node} MA doesn't exist")
        self.cache_node_vm = self.tcinputs["CacheNode"].get("vmname", self.cache_node)
        self.cache_node_sds = self.cache_node.split('.',1)[0] + 'sds'
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]

        # MA setup
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        self.ma_machines = {}
        for node in self.control_nodes:
            ma_name = self.control_nodes[node]
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            self.mas.append(ma_name)
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.cache_node_username, password=self.cache_node_password)
            self.ma_machines[ma_name] = machine
        self.vm_ma_names = self.tcinputs.get('VMMANames', [name.split('.', 1)[0] for name in self.mas])
        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]
        self.other_mas_sds = [ma.split('.', 1)[0] + 'sds' for ma in self.other_mas]

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get('SqlLogin')
        tcinputs_sql_password = self.tcinputs.get('SqlPassword')

        if tcinputs_sql_login is None:
            # go for default credentials
            if not hasattr(self.config.SQL, 'Username'):
                raise Exception(f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs")
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, 'Password'):
                raise Exception(f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            if tcinputs_sql_password is None:
                raise Exception(f"Please provide SqlPassword in TC inputs or remove SqlLogin to fetch credentials from config.json")
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

        # Subclient & Storage setup
        self.storage_pool_name = f"{self.id}StoragePool"
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset_name = "defaultBackupSet"
        self.backupset = self.agent.backupsets.get(self.backupset_name)
        self.subclient_name = self.id + "_subclient"
        self.storage_policy_name = self.id + "_policy"
        self.mmhelper_obj = MMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.drive = self.options_selector.get_drive(self.client_machine, 2*1024)
        
        # Backup and restore paths
        self.test_case_path = self.client_machine.join_path(self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(self.test_case_path, "Testdata")
        self.content_gb = 1
        self.content_path = self.get_client_content_folder('1', self.content_gb, self.test_data_path)
        # looks like C:\\Automation\\54394\\Testdata\\Data1-1Gb
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')
        self.restore_path = self.get_client_content_folder('1', self.content_gb, self.restore_data_path)

        self.hyperscale_helper = HyperScaleHelper(
            self.commcell, self.csdb, self.log)

        # VM setup
        if not hasattr(self.config.HyperScale, 'VMConfig'):
            raise(f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}")
        self.hs_vm_config = self.tcinputs.get('VMConfig', self.config.HyperScale.VMConfig)
        self.setup_vm_automation()

        self.CVUPGRADEOS_LOG = "cvupgradeos.log"
        cache_node_obj = self.commcell.clients.get(self.cache_node)
        log_directory = cache_node_obj.log_directory
        self.cache_node_install_directory = cache_node_obj.install_directory
        self.CVUPGRADEOS_LOG_PATH = f"{log_directory}/{self.CVUPGRADEOS_LOG}"

        self.YUM_OUT_LOG = "yum.out.log"
        self.YUM_OUT_LOG_PATH = f"{log_directory}/hsupgradedbg/{self.YUM_OUT_LOG}"

    def setup_vm_automation(self):
        """Initializes the VM automation helpers"""
        server_type = VmIo.SERVER_TYPE_ESX
        server_host_name = self.hs_vm_config['ServerHostName'] if 'ServerHostName' in self.hs_vm_config else self.hs_vm_config.ServerHostName
        username =  self.hs_vm_config['Username'] if 'Username' in self.hs_vm_config else self.hs_vm_config.Username
        password = self.hs_vm_config['Password'] if 'Password' in self.hs_vm_config else self.hs_vm_config.Password
        vm_config = {
            'server_type': server_type,
            'server_host_name': server_host_name,
            'username': username,
            'password': password
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io = VmIo(
            self.cache_node_vm, server_type, server_host_name, username, password, self.esx)

    def cleanup(self):
        """Cleans up the test case resources and directories"""
        if self.backupset.subclients.has_subclient(self.subclient_name):
            self.backupset.subclients.delete(self.subclient_name)
            self.log.info(f"{self.subclient_name} deleted")
        
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            policy_obj = self.commcell.storage_policies.get(self.storage_policy_name)
            policy_obj.reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.storage_policy_name)
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                            self.sql_login, self.sql_sq_password)
        self.log.info("Storage pool cleaned up")
        

        self.cleanup_test_data()
        
        for ma in self.mas:
            ma_obj = self.commcell.media_agents.get(ma)
            ma_obj.mark_for_maintenance(False)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info("Test case successful. Cleaning up storage pool")
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

            Returns:

                present or not (bool) - remote cache present for the client

            Raises:

                SDKException:

                - Failed to execute the api

                - Response is incorrect/empty

        """
        rc_helper = self.commcell.get_remote_cache(client_name)
        path = rc_helper.get_remote_cache_path()
        self.log.info(f"Found remote cache at {path}")
        return bool(path)

    def populate_remote_cache(self):
        """Populates the remote cache with Unix RPMs

            Args:

                None

            Returns:

                True, None      - If jobs succeeded

                False, message  - If jobs failed with failure message

        """
        job_obj = self.commcell.download_software(options=DownloadOptions.LATEST_HOTFIXES.value, os_list=[DownloadPackages.UNIX_LINUX64], sync_cache=True, sync_cache_list=[self.cache_node])
        self.log.info(f"Started the download software job [{job_obj.job_id}]")
        if not job_obj.wait_for_completion():
            self.log.info("Download software job failed")
            return False, job_obj.status
        return True, None

    def run_until_success(self, machine, command, retry_attempts=None, interval=None):
        """Runs a command untill it succeeds or retry_attempts are exhausted.

            Args:

                machine     (Machine)   --  The machine object on which command will run

                command     (str)       --  The command to run

                retry_attempts  (int)   --  The max number of iterations to run the command
                                            Default: 100

                interval    (int)       --  The number of seconds to wait between iterations
                                            Default: 5

            Returns:

                command (str)   - The output of the command, if successful

                None            - Otherwise

        """
        if retry_attempts is None:
            retry_attempts = 100
        if interval is None:
            interval = 5
        self.log.info(
            f"Running untill success |{command}| for {retry_attempts} tries, spaced every {interval}s")
        for _ in range(retry_attempts):
            output = machine.execute_command(command)
            output = output.output
            if not output:
                time.sleep(interval)
                continue
            return output

    def grep_after_line(self, machine, log_file_path, text, from_line=1, last=False, retry_attempts=100, interval=5, fixed_string=True):
        """Finds text in a log file with offset and retry attempts

            Args:

                machine         (Machine)   --  The machine object on where the log file resides

                log_file_path   (str)       --  The path to the log file that we are grepping

                text            (str)       --  The text to grep for

                from_line       (int)       --  The line from which to search

                last            (bool)      --  Grep for last match

                retry_attempts  (int)       --  The max number of iterations to run the command

                interval        (int)       --  The number of seconds to wait between iterations
                
                fixed_string    (bool)      --  Use fixed string (-F) for grep search

            Returns:

                (no, line)
                    no          (int)       -- The line number on which the match was found

                    line        (str)       -- The complete line that was matched

        """
        get_text_from_line = f"tail -n +{from_line} '{log_file_path}'"
        
        _F = 'F' if fixed_string else ''
        get_line_no = f"grep -n{_F} '{text}'"
        command = f"{get_text_from_line} | {get_line_no}"
        if last:
            command += f" | tail -1"
        time_start = time.time()
        output = self.run_until_success(machine, command, retry_attempts=retry_attempts, interval=interval)
        duration = int(round(time.time()-time_start))
        if not output:
            self.log.error(f"Couldn't grep for {text} from line {from_line} even after {duration}s")
            return False, None
        no, line = output.split(':', 1)
        no = int(no) + from_line - 1
        line = line.strip()
        self.log.info(f"Found |{text}| at {no} after {duration}s")
        self.log.info(line)
        return no, line

    def monitor_pre_upgrade_logs_to_set_upgrade_sequence(self, from_line):
        """Parses the logs to figure out the node sequence used for upgrade

            Args:

                from_line       (int)       --  The line from which to search

            Returns:

                (result, num)
                    result      (bool)      -- Whether the parse was successful or not

                    num         (int)       -- The line number that was matched

        """
        machine = self.ma_machines[self.cache_node]
        text = "Following nodes will be upgraded:"
        line_no, _ = self.grep_after_line(machine, self.CVUPGRADEOS_LOG_PATH, text, from_line)
        if not line_no:
            return False, None
        self.log.info(f"|{text}| is present at {line_no}")

        node_line_tuple = []
        for ma in self.mas:
            n, _ = self.grep_after_line(machine, self.CVUPGRADEOS_LOG_PATH, ma, line_no)
            if not n:
                return False, None
            node_line_tuple.append((n, ma))
        upgrade_seq = [t[1] for t in sorted(node_line_tuple)]
        self.log.info(f"Node upgrade order: {upgrade_seq}")
        self.upgrade_seq = upgrade_seq
        return True, line_no

    def should_upgrade_proceed(self, from_line):
        """Checks if the upgrade proceeds or not. It can't proceed if either it is already
        up to date or if we didn't match any log lines after sufficient tries

            Args:

                from_line   (int)   --  The line number from which logs need to be checked

            Returns:

                (num, result)
                    num     (int)   --  The line number on which the match was found.
                                        None, if no match was found

                    result  (bool)  --  Should proceed or not

        """
        logs_to_check = [
            ("Created cvrepo successfully", True),
            ("Repository [/ws/ddb/upgos/cvrepo] is not present, it appears there are no packges available for upgrade. Nothing to be done.", False)
        ]
        # cache_machine = Machine(self.cache_node, username=self.cache_node_username, password=self.cache_node_password)
        cache_machine = self.ma_machines[self.cache_node]
        interval = 5
        retry_attempts = 100
        self.log.info(f"Checking if upgrade should proceed with {retry_attempts} tries spaced every {interval} s")
        for _ in range(retry_attempts):
            for log, return_value in logs_to_check:
                result_line, _ = self.grep_after_line(
                    cache_machine, self.CVUPGRADEOS_LOG_PATH, log, from_line=from_line, retry_attempts=1)
                if result_line:
                    return result_line, return_value
            time.sleep(interval)
        self.log.error(f"Couldn't determine if upgrade should proceed after {retry_attempts} tries spaced every {interval} s")
        return None, False

    def monitor_os_upgrade_begin_logs(self, from_line, upgrade_seq):
        """Verifies the pre-upgrade logs

            Args:

                from_line   (int)   --  The line number from which logs need to be checked

                upgrade_seq (list)  --  The upgrade sequence of nodes

            Returns:

                (num, result)
                    num     (int)   --  The line number on which the match was found.
                                        None, if no match was found

                    result  (bool)  --  Should proceed or not

        """
        logs_to_check = [
            "Restarted glusterd ...",
            "Volume stopped"
        ]

        for ma in upgrade_seq[:-1]:
            log = f"Stopping services on remote node: {ma}"
            logs_to_check.append(log)

        logs_to_check += [
            # "Disabled commvault services...", # log line changed
            "Stopped gluster processes....",
        ]
        cache_machine = self.ma_machines[self.cache_node]
        for log in logs_to_check:
            from_line, _ = self.grep_after_line(
                cache_machine, self.CVUPGRADEOS_LOG_PATH, log, from_line=from_line)
            if not from_line:
                self.log.error(f"Couldn't find {log}")
                return False
        return True

    def verify_yum_logs(self, machine_ma):
        """Verifies the yum logs on the MA machine

            Args:

                machine_ma      (Machine)   --  The machine object of the MA

            Returns:

                result          (bool)      --  Logs verified or not

        """
        logs = [
            "Resolving Dependencies",
            "Dependencies Resolved",
            "Running transaction",
            "Complete!",
        ]
        for log in logs:
            line_no, _ = self.grep_after_line(machine_ma, self.YUM_OUT_LOG_PATH, log, retry_attempts=int(20*60/5), interval=5)
            if not line_no:
                self.log.error(f"Couldn't find the line {log} in {self.YUM_OUT_LOG}")
                return False
        return True

    def verify_logs_for_node(self, ma, from_line):
        """Verifies the logs for the node being upgraded

            Args:

                ma              (str)       --  The MA whose logs are to be verified

                from_line       (int)       --  The line number from where to start log verification

            Returns:

                result          (bool)      --  Logs verified or not

        """
        machine_ma = self.ma_machines[ma]
        machine_cache = self.ma_machines[self.cache_node]
        text = f"Starting to upgrade node... {ma}"
        line_cache, _ = self.grep_after_line(machine_cache, self.CVUPGRADEOS_LOG_PATH, text, from_line=from_line)
        if not line_cache:
            return False, None
        
        text = "Starting to upgrade the machine"
        line_cvupgradeos, _ = self.grep_after_line(machine_ma, self.CVUPGRADEOS_LOG_PATH, text, last=True)
        if not line_cvupgradeos:
            self.log.error(f"OS Upgrade didn't start on {ma}")
            return False, None
        
        text = "Running command [yum repolist]"
        line_cvupgradeos, _ = self.grep_after_line(machine_ma, self.CVUPGRADEOS_LOG_PATH, text, from_line=line_cvupgradeos)
        if not line_cvupgradeos:
            self.log.error(f"yum repolist command not found in logs")
            return False, None

        #regex = "(Installing|Updating|Cleanup|Erasing).*[[:digit:]]+/[[:digit:]]+"
        result = self.verify_yum_logs(machine_ma)
        if not result:
            self.log.error(f"Failed to verify yum logs for {ma}")
            return False, None
        self.log.info(f"Verified yum logs for {ma}")
        
        text = "Successfully installed required RPMs"
        line_cache, _ = self.grep_after_line(machine_cache, self.CVUPGRADEOS_LOG_PATH, text, from_line=line_cache, retry_attempts=15*60, interval=1)
        if not line_cache:
            self.log.error(f"Couldn't find {text} in {self.cache_node}:{self.CVUPGRADEOS_LOG} for {ma}")
            return False, None
        self.log.info(f"Now waiting for the node {ma} to come back up")

        logs = [
            "Remote host is up and running",
            "Running postupgrade tasks on remote node",
            f"Upgrade completed successfully for node...{ma}"
        ]
        for log in logs:
            line_cache, _ = self.grep_after_line(machine_cache, self.CVUPGRADEOS_LOG_PATH, log, from_line=line_cache, retry_attempts=300, interval=1)
            if not line_cache:
                self.log.error(f"Couldn't find the line {log} in {self.cache_node}:{self.CVUPGRADEOS_LOG} for {ma}")
                return False, None
        return True, line_cache
        
    def check_identical_output(self, ma_list, command):
        """Runs same command across multiple MAs for equality.

            Args:
                ma_list (list)  --  list of MA names

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
            ma_machine = self.ma_machines[ma]
            output = ma_machine.execute_command(command)
            output = output.output.strip()
            self.log.info(f"{ma}# {command}  ->  {output}")
            outputs.add(output)
            result[ma] = output
        if len(outputs) > 1:
            identical = False
        return identical, result

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

    def monitor_remote_cache_logs(self, line_cache):
        """Verifies the logs for the remote cache node

            Args:

                line_cache  (int)   --  The line after which the logs are to be verified

            Returns:

                result      (bool)  --  If verified or not

        """
        machine_cache = self.ma_machines[self.cache_node]
        logs_to_check = [
            [f"Starting to upgrade node... {self.cache_node}", None, None],
            ["Running command [yum repolist]", None, None],
            ["yum command [yum repolist] successful", None, None],
            ["Running command [yum -y update]", None, None],
            ["yum command [yum -y update] successful", 15*60, 2],
            # ["Installed selinux rpms successfully", 10*60, 1],
            [f"Upgrade completed successfully for node...{self.cache_node}", None, 1]
        ]
        for log, interval, tries in logs_to_check:
            line_cache, _ = self.grep_after_line(machine_cache, self.CVUPGRADEOS_LOG_PATH, log, from_line=line_cache, retry_attempts=tries, interval=interval)
            if not line_cache:
                self.log.error(f"Couldn't find the line {log} in {self.cache_node}:{self.CVUPGRADEOS_LOG} for {self.cache_node}")
                return False
        self.log.info("Now waiting 5 minutes to complete reboot")

        time.sleep(5*60)
        
        text = "Upgrade completed successfully on all nodes"
        line_cache, _ = self.grep_after_line(machine_cache, self.CVUPGRADEOS_LOG_PATH, text, from_line=line_cache, retry_attempts=1, interval=1)
        if not line_cache:
            self.log.error(f"Couldn't find the line {log} in {self.cache_node}:{self.CVUPGRADEOS_LOG} for {self.cache_node}")
            return False
        self.log.info("Upgrade successful")
        return True

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

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
        result = self.mmhelper_obj.create_uncompressable_data(self.client_name, path, content_gb)
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


    def run(self):
        """ run function of this test case"""
        try:
            self.log.info("Running cleanup before run")
            self.cleanup()

            # 1. Power down the nodes
            self.log.info("Powering down the nodes")
            for ma in self.vm_ma_names:
                result = self.esx.vm_power_control_with_retry_attempts(ma, 'off')
                if not result:
                    reason = f"Couldn't power off {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} have been powered down")

            # 2. Disable CD-ROMs, so that it boots from hard drive
            self.log.info("Disabling CDROM for all nodes")
            for ma in self.vm_ma_names:
                self.esx.vm_set_cd_rom_enabled(ma, False)
            self.log.info(f"All nodes {self.mas} have their CD-ROMs disabled")

            # 3. Power on the machines
            self.log.info("Powering up the nodes")
            for ma in self.vm_ma_names:
                result = self.esx.vm_power_control_with_retry_attempts(ma, 'on')
                if not result:
                    reason = f"Couldn't power on {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} have been powered on. Waiting for boot to complete")
            time.sleep(3*60)
            self.log.info(f"Proceeding after waiting.")

            # 4a. Check gluster shows no volumes
            self.log.info("Making sure that gluster reports no volume")
            result, outputs = self.check_identical_output(
                self.mas, "gluster v info 2>&1 | head -1")
            if not result:
                reason  = f"Gluster info output mismatch between MAs: {outputs}"
                return self.fail_test_case(reason)
            output = outputs[self.mas[0]]
            if output.strip() != 'No volumes present':
                reason = f"Gluster info output reports some volume: {output}"
                return self.fail_test_case(reason)
            self.log.info(f"Gluster reports {output} for {self.mas}")

            # 4b. Detach peers forcefully if exists
            self.log.info("Detaching peers forcefully")
            for ma_sds in self.other_mas_sds:
                cache_machine = self.ma_machines[self.cache_node]
                command = f"yes | gluster peer detach {ma_sds} force"
                output = cache_machine.execute_command(command)
                output = output.output
                self.log.info(f"command = |{command}|")
                self.log.info(f"output = |{output}|")

            # 4c. Check gluster peers shows no peers
            self.log.info("Making sure that gluster peer status is empty")
            result, outputs = self.check_identical_output(
                self.mas, "gluster peer status")
            if not result:
                self.log.warning("Gluster shows no volumes but has peers? Please force remove the peers: # gluster peer detach <peer> force")
                reason = f"Gluster peer status output mismatch between MAs: {outputs}"
                return self.fail_test_case(reason)
            output = outputs[self.mas[0]]
            if output.strip() != 'Number of Peers: 0':
                reason = f"Gluster peer status reports some peers: {output}"
                return self.fail_test_case(reason)
            self.log.info(f"Gluster reports {output} for {self.mas}")

            # 10. Create a storage pool
            self.log.info(f"Creating storage pool {self.storage_pool_name}")
            status, response = self.hyperscale_helper.create_storage_pool(
                self.storage_pool_name, *self.mas)
            self.log.info(
                f"Created storage pool with status: {status} and response: {response}")
            if not status:
                reason = "Storage pool creation failed"
                return self.fail_test_case(reason)

            # 5. Check if remote cache is present on cache_node
            self.log.info(f"Checking if remote cache is present on {self.cache_node}")
            result = self.is_remote_cache_present(self.cache_node)
            if not result:
                reason = f"Cache node {self.cache_node} doesn't have the remote cache setup."
                return self.fail_test_case(reason)
            self.log.info(f"Cache node {self.cache_node} has the remote cache")

            # 6 sync the cache so that nodes can be updated to latest SP
            self.log.info("syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")
            
            # 7. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)
            
            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 8. Check SP Version
            self.log.info("Checking SP version for all nodes")
            result, outputs = self.check_identical_values(self.mas, self.get_sp_version_from_cs)
            if not result:
                self.log.error(f"Nodes have version mismatch {outputs}. Proceeding")
            self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")
            
            # 9a. Save current gluster version
            self.log.info("Saving pre gluster version")
            result, outputs = self.check_identical_output(self.mas, "gluster --version")
            if not result:
                self.log.warning(f"Nodes running different gluster version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running gluster version {outputs[self.mas[0]]}")
            pre_gluster_version = outputs

            # 9b. Save current gluster rpm version
            self.log.info("Saving pre gluster rpm version")
            result, outputs = self.check_identical_output(self.mas, "rpm -qa | grep glusterfs-server")
            if not result:
                self.log.warning(f"Nodes running different gluster rpm version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running gluster rpm version {outputs[self.mas[0]]}")
            pre_gluster_rpm_version = outputs
            
            # 9c. Save current OS Version
            self.log.info("Saving pre os version")
            result, outputs = self.check_identical_output(self.mas, "cat /etc/redhat-release")
            if not result:
                self.log.warning(f"Nodes running different OS version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running OS version {outputs}")
            pre_os_version = outputs

            # 9d. Save current kernel Version
            self.log.info("Saving pre kernel version")
            result, outputs = self.check_identical_output(self.mas, "uname -r")
            if not result:
                self.log.warning(f"Nodes running different kernel version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running kernel version {outputs}")
            pre_kernel_version = outputs

            

            # 11. populate the remote cache with Unix software
            self.log.info(f"Populating remote cache {self.cache_node} with Unix RPMs")
            result, message = self.populate_remote_cache()
            if not result:
                reason = message
                return self.fail_test_case(reason)
            self.log.info(f"Successfully populated remote cache {self.cache_node} with Unix RPMs")

            # 12. Take a backup here
            self.log.info("Proceeding to take backup before OS upgrade")
            
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")

            self.policy = self.get_or_create_policy(self.storage_policy_name)
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            # 13. Mark MAs in maintenance mode
            self.log.info("Marking media agents in maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(True)
            self.log.info(f"Marked MAs in maintenance mode")

            # 14. Get no. of lines in cvupgradeos.log
            self.log.info(f"Getting number of lines in {self.CVUPGRADEOS_LOG}")
            command = f"cat {self.CVUPGRADEOS_LOG_PATH} | wc -l"
            output = self.ma_machines[self.cache_node].execute_command(command)
            lines_before_os_upgrade = int(output.output)
            self.log.info(f"Number of lines in cvupgradeos.log: {lines_before_os_upgrade}")

            # 15. doing it once more as the session times out after 900 seconds
            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation()

            # 16. Login via console
            self.log.info(f"Logging in to the remote cache node {self.cache_node} via console")
            self.vm_io.send_command(self.cache_node_username)
            self.vm_io.send_command(self.cache_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)

            # 17. Run upgrade script
            self.log.info("Running the upgrade script")
            self.vm_io.send_command(f"cd {self.cache_node_install_directory}/MediaAgent")
            self.vm_io.send_command("./cvupgradeos.py")

            # 18. Finding upgrade sequence
            self.log.info("Finding the upgrade sequence...")
            result, line_no = self.monitor_pre_upgrade_logs_to_set_upgrade_sequence(
                lines_before_os_upgrade)
            if not result:
                reason = f"Failed to find the upgrade sequence"
                return self.fail_test_case(reason)
            self.log.info(f"Upgade sequence: {self.upgrade_seq}")

            self.log.info(f"Now proceeding for OS Upgrade. Sending 'y'")
            self.vm_io.send_command('y')
            
            # 19. Do we need the upgrade?
            self.log.info("Checking if upgrade will proceed or bail out")
            line_no, result = self.should_upgrade_proceed(line_no)
            if line_no is None:
                reason = "Failed to determine if upgrade should proceed or not"
                return self.fail_test_case(reason)
            if not result:
                self.log.info("No upgrade required at this point. Returning")
                self.successful = True
                return
            self.log.info("Proceeding with upgrade")

            # 20. Monitoring pre upgrade logs
            self.log.info("Monitoring pre upgrade logs on the remote cache node")
            result = self.monitor_os_upgrade_begin_logs(
                line_no, self.upgrade_seq)
            if not result:
                reason = f"Failed to verify pre upgrade logs"
                return self.fail_test_case(reason)
            self.log.info(
                f"Verified pre upgrade logs. Proceeding with node wise log checking")
            
            # 21. Node wise logs
            for ma in self.upgrade_seq[:-1]:
                self.log.info(f"Now verifying logs on {ma}")
                result, line_no = self.verify_logs_for_node(ma, line_no)
                if not result:
                    reason = f"Couldn't verify logs for node {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully verified logs for node {ma}")
            
            # 22. Final node
            self.log.info(f"Now proceeding with self upgrade of {self.cache_node}")
            result = self.monitor_remote_cache_logs(line_no)
            if not result:
                reason = f"Couldn't verify logs for node {self.cache_node}"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified logs for node {self.cache_node}")

            # 23. Mark MAs out of maintenance mode
            self.log.info("Marking media agents out of maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(False)
            self.log.info(f"Marked MAs out of maintenance mode")

            # 24. Perform restore here
            self.log.info("Performing Restore")
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)
            
            # 25. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

            # 26a. Compare current gluster version
            result, outputs = self.check_identical_output(self.mas, "gluster --version")
            if not result:
                self.log.warning(f"Nodes running different gluster version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running gluster version {outputs[self.mas[0]]}")
            self.log.info(f"Previous: {pre_gluster_version}")

            # 26b. compare current gluster rpm version
            result, outputs = self.check_identical_output(self.mas, "rpm -qa | grep glusterfs-server")
            if not result:
                self.log.warning(f"Nodes running different gluster rpm version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running gluster rpm version {outputs[self.mas[0]]}")
            self.log.info(f"Previous: {pre_gluster_rpm_version}")
            
            # 26c. Compare current OS Version
            result, outputs = self.check_identical_output(self.mas, "cat /etc/redhat-release")
            if not result:
                self.log.warning(f"Nodes running different OS version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running OS version {outputs}")
            self.log.info(f"Previous: {pre_os_version}")

            # 26d. Compare current kernel Version
            result, outputs = self.check_identical_output(self.mas, "uname -r")
            if not result:
                self.log.warning(f"Nodes running different kernel version {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes running kernel version {outputs}")
            post_kernel_version = outputs
            self.log.info(f"Kernel version post upgrade: {post_kernel_version}")

            # 26e. Compare current kernel version with the expected kernel version
            self.log.info(f"Comparing current kernel version with expected kernel version")
            result, outputs = self.hyperscale_helper.validate_cluster_kernel_versions(self.ma_machines)
            if not result:
                failed_nodes = [ma_name for ma_name, status in outputs.items() if not status]
                reason = f"Current kernel version doesn't match the expected kernel version on these nodes -> {failed_nodes}"
                self.fail_test_case(reason)
            self.log.info(f"Current kernel version matches the expected kernel versions on all nodes")

            self.successful = True
            self.log.info(f"Successfully upgraded the OS. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
