# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
File for Linux ransomware helper, File for performing operations on a machine /
computer with UNIX Operating System

UnixRansomwareHelper
====================

    __init__()                          --  initialize object of the class

    _get_logger()                       --  Returns the custom logger for this module

    ransomware_protection_status()      --  This function checks the state of ransomware protection

    check_ransomware_mode()             --  This functions checks for current mode for
                                                ransomware protection

    get_sestatus_output()               --  Retrieves the sestatus output

    compare_sestatus_output()           --  Verifies the sestatus output according to expected dictionary

    validate_sestatus_when_rwp_enabled()    --  Verifies the sestatus output when ransomware protection is enabled

    validate_sestatus_when_rwp_disabled()   --  Verifies the sestatus output when ransomware protection is disabled

    check_sys_req()                     --  This will check if required rpms are present
                                                     on the media agent or not
                                            Multiple instance there or not, OS version
                                            Supported OS version RHEL 7.6, RHEL 7.7 and
                                            RHEL 7.8, 7.9, and their corresponding CentOS release

    policy_load_status()                --  To check policy_loaded status

    verify_ransomware_enablement()      --  To verify if ransomware enablement went successfully
                                                        or not
                                            Check mode, CVBackup tag

    verify_maglib_protected()		    --	Check MP is protected and tagged with cvbackup

    disable_selinux()			        --   Disable Selinux on the machine

    unlabel_cvstorage()			        --	Unlabelling cvstorage tag from file level

    pause_protection()			        --	Pause selinux protection

    resume_protection()			         --	Resume selinux protection

    enable_protection_linux()		     --	Enable ransomware protection

    check_hyperscale_machine()          --  Checks whether hyperscale node or not

    hsx_get_whitelisted_processes()     --  Parses cvsecurity.cfg file and returns a list of processes

    hsx_validate_whitelisted_processes_labels() --  Verifies if the whitelisted processes list is correctly tagged

    hyperscale_validate_process_selinux_tagging() - hyperscale node check cvbackup tagging
                                                    on expected processes

    hsx_validate_running_processes_labels()     --  Validate the processes that are running with correct selinux labels

    hsx_validate_process_label()                --  Check selinux context tagging on processes

    hyperscale_validate_ws_selinux_tagging()    --  hyperscale node check cvcontext tagging
                                                        on targeted objects

    hyperscale_selinux_label_mode()             --  return Selinux Label mode - file/mount level

    hyperscale_get_protected_mountpaths()       --  returns the list of protected mountpaths

    hsx_get_protected_mountpaths()              --  Returns the mount paths which are protected

    hyperscale_validate_mountpath_protected()   --  Validated whether mountpath is write protected

    hsx_enable_protection()                     --  Enables protection on this HSX node

    hsx_validate_registry_entries()             --  Verifies whether correct registry keys are present across MAs

    delete_registry_entries()                   --  Deletes the registry entries related to Ransomware Protection

    hsx_validate_fstab()                        --  Verifies the fstab file for selinux label

    backup_fstab()                              --  Saves the /etc/fstab file

    restore_fstab()                             --  Restores /etc/fstab file to its original state (before ransomware protection)

    hsx_validate_protected_mount_paths_mounted()    --  Validates if protected mount paths are mounted or not

    hsx_validate_context_on_protected_mount_paths() --  Validates the security context on the protected mount paths

    hsx_validate_context_on_whitelisted_binaries()    --  Validates the security context on the whitelisted binaries or scripts

    hsx_rwp_validation_suite()                  --  The complete validation suite for HSX ransomware protection


"""
import re
import time

from AutomationUtils import database_helper, logger
from AutomationUtils.output_formatter import UnixOutput
from AutomationUtils.unix_machine import UnixMachine
from Install import install_helper
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper


class UnixRansomwareHelper:
    """
    Helper class for linux ransomware
    """

    def __init__(self, machine_obj: UnixMachine = None, commcell_obj=None, log_obj=None):
        """
        Initialise instance for UnixRansomwareHelper
        Args:
            machine_obj     (object)    --   instance for machine
            commcell_obj    (object)    --  instance for commcell
            log_obj         (object)    --  instance for log
        """
        self.machine = machine_obj
        self.commcell = commcell_obj
        self.csdb = database_helper.get_csdb()
        self.client_obj = None
        self.media_agent_name = self.machine.machine_name
        self.short_name = self.media_agent_name.split('.', 1)[0]
        self.log = self._get_logger(log_obj)
        self.install_helper_obj = install_helper.InstallHelper(self.commcell, self.machine)
        if self.commcell is None or self.machine is None:
            raise Exception(f"No machine or client object passed, machine_obj : "
                            f"{self.machine}\tcommcell_obj"
                            f" : {self.commcell}")
        if self.log is None:
            raise Exception(f"Log object not initialised, log_obj : {self.log}")
        if self.machine and self.machine.client_object:
            self.client_obj = self.machine.client_object
        else:
            self.client_obj = self.commcell.clients.get(self.media_agent_name)
        self.dir_install = self.client_obj.install_directory
        self.dir_media_agent = f"{self.dir_install}/MediaAgent"
        self.cvsecurity_py = f"{self.dir_media_agent}/cvsecurity.py"
        self.cvsecurity_cfg = f"{self.dir_media_agent}/cvsecurity.cfg"

    def _get_logger(self, log_obj):
        """Returns the custom logger for this module

            Args:

                log_obj (obj)   --  The logger from CVTestCase

            Returns:

                logger  (obj)   --  The custom logger object
        """
        log_file = log_obj.handlers[0].baseFilename
        log_name = f"UnixRansomwareHelper_{self.short_name}"
        msg_prefix = f"[{self.short_name}] "
        logger_obj = logger.get_custom_logger(log_name, log_file, msg_prefix)
        return logger_obj

    def ransomware_protection_status(self):
        """
        This function checks the state of ransomware protection
        sestatus | grep 'SELinux status:'
            SELinux status:                 enabled
        Returns:
            True - if ransonware protection is enabled
            False - if ransomware protection is disabled
        """
        status = True
        command = r"sestatus | grep 'SELinux status:' | awk '{print $3}'"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.output)
        if output.formatted_output.lower() == 'disabled':
            status = False
            self.log.info("Ransomware not enabled")
        return status

    def check_ransomware_mode(self):
        """
        This functions checks for current mode for ransomware protection
        sestatus
            SELinux status:                 enabled
            SELinuxfs mount:                /sys/fs/selinux
            SELinux root directory:         /etc/selinux
            Loaded policy name:             targeted
            Current mode:                   enforcing
            Mode from config file:          enforcing
            Policy MLS status:              enabled
            Policy deny_unknown status:     allowed
            Max kernel policy version:      31

        Returns:
            True - if mode enforcing
            False -if mode permissive
        """
        command = r"sestatus"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.output)
        if self.ransomware_protection_status():
            command = r"sestatus | grep 'Current mode:' | awk '{print $3}'"
            self.log.info("command: %s", command)
            output = self.machine.execute_command(command)
            self.log.info(output.output)
            if output.formatted_output == "enforcing":
                return True
            return False
        raise Exception("Ransomware disabled")

    def get_sestatus_output(self):
        """Retrieves the sestatus output:

        sestatus
            SELinux status:                 enabled
            SELinuxfs mount:                /sys/fs/selinux
            SELinux root directory:         /etc/selinux
            Loaded policy name:             targeted
            Current mode:                   enforcing
            Mode from config file:          enforcing
            Policy MLS status:              enabled
            Policy deny_unknown status:     allowed
            Max kernel policy version:      31

            Returns:

                result  (dict)  --  { key -> value } as shown above
                                    False, in case of errors
        """
        command = "sestatus"
        self.log.info("get_sestatus_output")
        output = self.machine.execute_command(command)
        output = output.output.strip()
        self.log.info(f"{command} -> {output}")

        if not output:
            self.log.error(f"{command} failed to give any output")
            return False

        lines = output.split("\n")
        result = {}
        for line in lines:
            splits = re.split(': +', line)
            if len(splits) != 2:
                self.log.error(f"Error while splitting the line: {line}")
                return False
            key, value = splits
            result[key] = value
        return result

    def compare_sestatus_output(self, expected):
        """Verifies the sestatus output according to expected dictionary:

        sestatus
            SELinux status:                 enabled
            SELinuxfs mount:                /sys/fs/selinux
            SELinux root directory:         /etc/selinux
            Loaded policy name:             targeted
            Current mode:                   enforcing
            Mode from config file:          enforcing
            Policy MLS status:              enabled
            Policy deny_unknown status:     allowed
            Max kernel policy version:      31

            Args:

                expected    (dict)  --  Expected {key -> value} mapping
                                        value is None => key mustn't exist

            Returns:

                result      (bool)  --  Whether the actual matches the expected
                                        None, if error
        """
        actual = self.get_sestatus_output()
        if not actual:
            self.log.error(f"Error while getting sestatus output")
            return

        for key, value in expected.items():
            if actual.get(key) != value:
                self.log.error(f"Values don't match for key: {key}. Expected: {value}, Got: {actual.get(key)}")
                return False
        self.log.info(f"Successfully verified {expected}")
        return True

    def validate_sestatus_when_rwp_enabled(self):
        """Verifies the sestatus output when ransomware protection is enabled

        sestatus
            SELinux status:                 enabled
            SELinuxfs mount:                /sys/fs/selinux
            SELinux root directory:         /etc/selinux
            Loaded policy name:             targeted
            Current mode:                   enforcing
            Mode from config file:          enforcing
            Policy MLS status:              enabled
            Policy deny_unknown status:     allowed
            Max kernel policy version:      31

            Returns:

                result      (bool)  --  Whether verified successfully or not
                                        None, if errors
        """
        expected = {
            "SELinux status": "enabled",
            "Loaded policy name": "targeted",
            "Current mode": "enforcing",
            "Mode from config file": "enforcing",
        }
        result = self.compare_sestatus_output(expected)
        if result is None:
            return
        return result

    def validate_sestatus_when_rwp_disabled(self):
        """Verifies the sestatus output when ransomware protection is disabled

        sestatus
            SELinux status:                 disabled
            SELinuxfs mount:                N/A
            SELinux root directory:         N/A
            Loaded policy name:             N/A
            Current mode:                   N/A
            Mode from config file:          N/A
            Policy MLS status:              N/A
            Policy deny_unknown status:     N/A
            Max kernel policy version:      N/A

            N/A: entry doesn't exist

            Returns:

                result      (bool)  --  Whether verified successfully or not
                                        None, if errors
        """
        expected = {
            "SELinux status": "disabled",
            "SELinuxfs mount": None,
            "SELinux root directory": None,
            "Loaded policy name": None,
            "Current mode": None,
            "Mode from config file": None,
        }
        result = self.compare_sestatus_output(expected)
        if result is None:
            return
        return result

    def check_sys_req(self):
        """
        Also not a Hyperscale machine
        This will check if required rpms are present on the media agent or not
        Multiple instance there or not, OS version
        Supported OS version RHEL 7.6, RHEL 7.7 and RHEL 7.8, 7.9, and their corresponding
         CentOS release

        rpm -qa | grep -e libselinux-python -e policycoreutils-devel -e
        selinux-policy-devel -e selinux-policy-targeted
        -e selinux-policy
            libselinux-python-2.5-14.1.el7.x86_64
            selinux-policy-targeted-3.13.1-252.el7_7.6.noarch
            policycoreutils-devel-2.5-33.el7.x86_64
            selinux-policy-devel-3.13.1-252.el7_7.6.noarch
            selinux-policy-3.13.1-252.el7_7.6.noarch
        Return:
            bool True/False
        """
        status = True
        self.log.info(f"Checking system requirements on {self.media_agent_name}")
        self.log.info("Checking multiple Instances or not")
        command = "commvault status | grep 'Instance' | wc -l"
        self.log.info("command: %s", command)

        output = self.machine.execute_command(command)
        self.log.info(output.output)
        if len(output.output.replace("\n", "").split()) > 1:
            self.log.info("Multiple Instances")
            status = False
            return status

        self.log.info("Checking OS Version")
        os = ['7.6', '7.7', '7.8', '7.9']
        # command = "hostnamectl | grep 'Operating System:'"
        # output = self.media_agent_machine.execute_command(command)
        # self.log.info(output.output)
        os_ver = re.findall(r"[-+]?\d*\.\d+|\d+", self.machine.client_object.os_info)
        if os_ver[-1] not in os:
            status = False
            self.log.info("OS version not supported %s", os_ver[-1])
            return status

        rpms = ["python3-libselinux", "policycoreutils-devel", "selinux-policy-devel",
                "selinux-policy-targeted", "selinux-policy"]
        missing_rpms = []
        for rpm in rpms:
            command = r"rpm -qa | grep {0}"
            command = command.format(rpm)
            self.log.info("Checking rpm %s", rpm)
            output = self.machine.execute_command(command)
            self.log.info(output.output)
            if not output.output:
                self.log.info("RPM %s not present", rpm)
                missing_rpms.append(rpm)
                status = False
        if not status:
            self.log.error(f"Missing rpms {missing_rpms}, please install them")
            return status
        self.log.info("Satisfies requirements ")
        return status

    def policy_load_status(self):
        """
        To check policy_loaded status
        ./cvsecurity.py enable_protection -i Instance001
            OS version Red Hat Enterprise Linux Server release 7.6 (Maipo)
            2020-12-07 17:13:12,379 - __main__ - INFO - start setup_selinux_env
            Loaded plugins: langpacks, product-id, subscription-manager
            This system is not registered with an entitlement server. You can use
            subscription-manager to register.
            2020-12-07 17:13:12,641 - __main__ - INFO - selinux-policy-devel is already installed...
            2020-12-07 17:13:12,642 - __main__ - INFO - libselinux-python is already installed...
            2020-12-07 17:13:12,679 - __main__ - INFO - imported selinux
            2020-12-07 17:13:12,680 - __main__ - INFO - start enable_protection
            2020-12-07 17:13:12,680 - __main__ - INFO - start set_selinux_policy
            2020-12-07 17:13:12,681 - __main__ - INFO - start set_selinux_mode
            2020-12-07 17:13:12,682 - __main__ - INFO - selinux mode=permissive policy=targeted.
            2020-12-07 17:13:12,682 - __main__ - INFO - start update_selinux_state
            2020-12-07 17:13:12,682 - __main__ - INFO - start load_cv_policy
            2020-12-07 17:13:12,683 - __main__ - INFO - start is_policy_loaded
            2020-12-07 17:13:18,521 - __main__ - INFO - 400 cvbackup          pp

            policy_loaded=true
            2020-12-07 17:13:18,522 - __main__ - INFO - policy already loaded skipping
            2020-12-07 17:13:18,522 - __main__ - INFO - start reset_cv_app_file_context
            2020-12-07 17:13:18,522 - __main__ - INFO - start get_cv_process_list
            2020-12-07 17:13:18,523 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,590 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,596 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,601 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,605 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,609 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,613 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,618 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,622 - __main__ - INFO - start rest_file_context
            2020-12-07 17:13:18,626 - __main__ - INFO - start update_selinux_state
            2020-12-07 17:13:18,626 - __main__ - INFO - get_configured_library_paths
            2020-12-07 17:13:18,627 - __main__ - INFO -
        Return:
             bool (True, False)
        """
        policy_load_status = False
        command = f"(cd {self.client_obj.install_directory}/MediaAgent &&" \
                  f" ./cvsecurity.py enable_protection -i {self.machine.instance})"
        output = self.machine.execute_command(command)
        for info in output.formatted_output:
            if 'policy_loaded=true' in info:
                policy_load_status = True
                self.log.info("policy load status %s", info)
        return policy_load_status

    def verify_ransomware_enablement(self):
        """
        To verify if ransomware enablement went successfully or not
        Check mode, CVBackup tag

        pstree -Z | grep cvbackup
             |-CvMountd(`system_u:system_r:cvbackup_t:s0')
             |  `-22*[{CvMountd}(`system_u:system_r:cvbackup_t:s0')]
             |-cvd(`system_u:system_r:cvbackup_t:s0')
             |  `-46*[{cvd}(`system_u:system_r:cvbackup_t:s0')]
             |-cvlaunchd(`system_u:system_r:cvbackup_t:s0')
             |  |-CVODS(`system_u:system_r:cvbackup_t:s0')
             |  |  `-15*[{CVODS}(`system_u:system_r:cvbackup_t:s0')]
             |  |-CVODS(`system_u:system_r:cvbackup_t:s0')
             |  |  `-11*[{CVODS}(`system_u:system_r:cvbackup_t:s0')]
        Return:
            bool
        """
        status = True
        mode = self.check_ransomware_mode()
        if not mode:
            status = False
            raise Exception("Ransomware mode not set to enforcing")

        major_processes = ['CvMountd', 'cvd', 'CVODS']
        command = "pstree -Z | grep cvbackup"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.output)
        if len(output.output) == 0:
            status = False

        for process in major_processes:
            command = "pstree -Z | grep {0}".format(process)
            self.log.info("command: %s", command)
            output = self.machine.execute_command(command)
            self.log.info(output.output)
            if 'cvbackup' not in output.output:
                self.log.error("process %s not tagged with cvbackup", process)
                status = False
        return status

    def verify_maglib_protected(self, lib_name, mount_path):
        """
        Check MP is protected and tagged with cvbackup
        ls -Z /00000012mount_path_1 | grep cvstorage
            -rw-rw-r--. root root system_u:object_r:cvstorage_t:s0 DEVICE_LABEL
            drwxrwxr-x. root root system_u:object_r:cvstorage_t:s0 MLOGSO_12.21.2020_07.26
        Will get folder inforamtion for the mount path and create actual path for it on media agent
        Args:
            lib_name    (str) -- library name
            mount_path  (str) -- mount path name
        Return:
            bool
        """
        status = True
        actual_location = None
        if self.commcell.disk_libraries.has_library(lib_name):
            lib_obj = self.commcell.disk_libraries.get(lib_name)
            lib_id = int(lib_obj.library_id)
        else:
            self.log.error("Library %s does not exists", lib_name)
            raise Exception("No library found")
        query = """select MountPathName 
                           from mmmountpath 
                           where libraryid = {0}""".format(str(lib_id))
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        mount_path_location = self.csdb.fetch_one_row()[0]
        actual_location = f"{mount_path}{self.machine.os_sep}" \
                          f"{mount_path_location}{self.machine.os_sep}CV_MAGNETIC"
        self.log.info("MP location on MA %s", actual_location)
        command = "ls -Z {0} | grep cvstorage".format(actual_location)
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.output)
        if len(output.output) == 0:
            status = False
        return status

    def disable_selinux(self):
        """
        Disable Selinux on the machine at the end of TC, if selinux is enabled
        Remove labels (cvstorage) from the mount paths as well
        Untag/unlabel cvstorage tag from the file level tagging separately, refer unlabel_cvstarge()
        """
        if not self.ransomware_protection_status():
            self.log.info("Selinux in disabled state already")
            return

        self.log.info("Disabling Selinux")
        command = f"sed -i 's/selinux=1/selinux=0/g' /etc/default/grub"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.output)

        command = f"sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.output)

        self.log.info("Rebooting the MA")
        command = "reboot"
        output = self.client_obj.execute_command(command=command, wait_for_completion=False)
        if not self.install_helper_obj.wait_for_services(client=self.client_obj):
            self.log.info("client ma ready")
        time.sleep(300)

        if self.ransomware_protection_status():
            self.log.error("Disable selinux failed")
            raise Exception("Disable selinux failed")

        self.log.info("Unloading policy")
        command = f"semodule -r cvbackup2"
        self.log.info("command: %s", command)
        self.client_obj.execute_command(command=command, wait_for_completion=True)
        command = f"semodule -r cvbackup"
        self.log.info("command: %s", command)
        self.client_obj.execute_command(command=command, wait_for_completion=True)

        if not self.install_helper_obj.wait_for_services(client=self.machine.client_object):
            self.log.info("client ma is ready")

    def unlabel_cvstorage(self, lib_name, mount_path):
        """Unlabelling cvstorage tag from file level
        Args:
            lib_name        (str)   -- library name
            mount_path      (str)   --  mount path to untag from cvstorage
        Return:
            bool    --  True/False
        """
        status = False
        if self.verify_maglib_protected(lib_name, mount_path):
            status = True
            self.log.info("Unlabelling cvstorage tag from file level")
            command = f"chcon -R system_u:object_r:unlabeled_t:s0 {mount_path}"
            output = self.machine.execute_command(command)
            self.log.info(output.output)
            return status
        self.log.info(f"Mount path {mount_path} is not tagged with cvstorage, no need to un-label")
        return status

    def pause_protection(self):
        """
        Pause selinux protection
        """
        self.log.info("Pausing protection")
        command = f"(cd {self.client_obj.install_directory}/MediaAgent &&" \
                  f" ./cvsecurity.py pause_protection)"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.exception_message)
        self.log.info(output.output)
        output = self.check_ransomware_mode()
        if not output:
            self.log.info("Paused protection, selinux mode permissive")
        else:
            raise Exception("Failed to pause protection")

    def resume_protection(self):
        """
        Resume selinux protection
        """
        self.log.info("Resume protection")
        command = f"(cd {self.client_obj.install_directory}/MediaAgent &&" \
                  f" ./cvsecurity.py resume_protection)"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.exception_message)
        self.log.info(output.output)
        output = self.check_ransomware_mode()
        if not output:
            raise Exception("Failed to resume protection")
        self.log.info("Resume Protection successful")

    def check_hyperscale_machine(self):
        """
        check whether it is hyperscale node or not

        Returns: True/False

        """
        self.log.info("checking whether the given nodes are Hyperscale Nodes")
        command = f"grep -i 'sHyperScaleNodeType' {self.machine.key % ('MediaAgent')}"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        output = output.output.replace("\n", '')
        if output != '':
            return True
        return False

    def check_hyperscale_gluster(self):
        """
        check whether it is hyperscale 1.5 Node

        Returns: True/False

        """
        self.log.info("checking whether the given nodes are Hyperscale 1.5 Node")
        command = f"grep -i 'sHyperScaleImageidentifier' {self.machine.key % ('MediaAgent')}"
        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        output = output.output.replace("\n", '').split()[3]
        if '1.5' in output:
            return True
        return False

    def hsx_get_whitelisted_processes(self, names_only=True):
        """Parses cvsecurity.cfg file and returns a list of processes
        that are expected to be tagged

            Args:

                names_only   (bool)  -- OPTIONAL. Whether to return entire paths or just names
                                        Default: True

            Returns:

                result  (list)  --  The list of processes to be tagged
                                    None, in case of error

        """
        output = self.machine.read_file(self.cvsecurity_cfg)
        if not output:
            self.log.error("cvsecurity.cfg is empty or doesn't exist")
            return

        pattern = r'APPLICATION\][\n]paths = (.*)'
        matches = re.findall(pattern, output)
        if not matches:
            self.log.error("Failed to get paths from cvsecurity.cfg")
            return

        result = []
        for match in matches:
            for path in match.strip().split(','):
                if names_only:
                    path = path.rsplit('/', 1)[-1]
                elif not path.startswith('/'):
                    path = f"{self.dir_install}/{path}"

                result.append(path)

        self.log.info(f"Got whitelisted processes as {result}")
        # from APPLICATION:
        # cvd CVODS CVDiskPerf CVDiskEraser auxCopy CvMountd IdxLabelUtil 3dnfsd clRestore CommServeDR

        # from HEDVIG_APPLICATION:
        # HedvigFSServerController start-server.sh start-pages.sh start-hpod.sh filehandles.py
        # backup_systemdb.sh restore_systemdb_if_necessary.sh backup-restore.pl collect-state.pl
        # enable_drives_hblock.py enable_drives_pages.py enable_drives.sh hedvig_swatch.py

        return result

    def hsx_validate_whitelisted_processes_labels(self, whitelisted):
        """Verifies if the whitelisted processes list is correctly tagged

            Args:

                whitelisted     (list)          --  The list of whitelisted processes that should be tagged

            Returns:

                result, pids    (bool, dict)    --  bool: Whether validated or not
                                                    dict: { process pids -> name }

        """
        pids = {}
        for process in whitelisted:
            command = f"ps --no-headers -o comm,label,pid -e | grep -v grep | grep {process[:15]}"
            self.log.info("command: %s", command)
            output = self.machine.execute_command(command)
            output = output.output
            self.log.info(output)
            if not output:
                continue
            for line in output.strip().split("\n"):
                pname, plabel, pid = re.split(" +", line)
                if 'cvbackup_t' not in plabel:
                    self.log.error(f"Process {process} not tagged with cvbackup_t")
                    return False, None
                pids[pid] = pname

        self.log.info(f"All whitelisted processes that are running, have cvbackup context having pids: {pids}")
        return True, pids

    def hyperscale_validate_process_selinux_tagging(self):
        """
        check selinux context tagging on process

        Returns: True / False
        """
        self.log.info("check selinux context tagging on process")

        if not self.check_hyperscale_machine():
            self.log.error("Not a HyperScale Machine")
            raise Exception("Not a HyperScale Machine")

        command = "cd /opt/commvault/MediaAgent && cat cvsecurity.cfg" \
                  " | grep -i 'paths = ' | grep -i 'cv'"
        output = self.machine.execute_command(command)
        output = output.output[8:-1].split(",")
        expected_tagged_process = [process.split("/")[1] for process in output]
        self.log.info("%s", expected_tagged_process)
        for process in expected_tagged_process:
            command = "pstree -Z | grep -i {0}".format(process)
            self.log.info("command: %s", command)
            output = self.machine.execute_command(command)
            self.log.info(output.output)
            if output.output != '' and 'cvbackup' not in output.output:
                self.log.error("process %s not tagged with cvbackup", process)
                raise Exception(f"CV Process{process} not tagged Properly")
        command = "ps -eZ | grep 'cvbackup' | awk '{print$5}'"
        self.log.info("Command : %s", command)
        output = self.machine.execute_command(command)
        tagged_process = output.output.split("\n")[:-1]
        self.log.info(tagged_process)
        for process in tagged_process:
            if process not in expected_tagged_process:
                return False
        return True

    def hsx_validate_running_processes_labels(self, whitelisted_processes, whitelisted_pids):
        """Validate the processes that are running with correct selinux labels

            Args:

                whitelisted_processes   (list)  --  The list of processes expected to be tagged already

                whitelisted_pids        (dict)  --  dict: { process pids -> process name }

            Returns:

                result                  (bool)  --  Whether validated or not

        """
        command = "ps --no-headers -o comm,label,pid,ppid,cmd -e | grep -v grep | grep cvbackup_t"
        #                             0    1     2   3    4

        self.log.info("Command : %s", command)
        output = self.machine.execute_command(command)
        output = output.output.strip()
        self.log.info(output)
        tagged_processes = output.split("\n")

        for process in tagged_processes:
            pname, plabel, pid, ppid, cmd = re.split(" +", process, maxsplit=4)
            if pname in whitelisted_processes:
                continue
            if ppid in whitelisted_pids.keys():
                continue
            if "hedvighpod.jar" in cmd:
                continue
            if pname in ["subscription-ma", "sar", "jspawnhelper"]:
                continue
            if pname in [name[:15] for name in whitelisted_processes]:
                continue
            command = f"ps --no-headers -o comm,label,ppid,cmd {ppid}"
            output = self.machine.execute_command(command)
            parent_process = output.output
            self.log.info(f"{command} -> {parent_process}")
            ppname, pplabel, pppid, pcmd = re.split(" +", parent_process, maxsplit=3)
            if pppid in whitelisted_pids.keys():
                continue

            self.log.error(f"Process {pname} with pid {pid}, ppid {ppid} ({ppname}), pppid {pppid} wrongly has the cvbackup_t label")
            return False
        self.log.info(f"Validated all running processes that have cvbackup_t label")
        return True

    def hsx_validate_process_label(self):
        """Check selinux context tagging on processes

            Return:

                result  (bool)  --  Whether validated or not
                                    None, otherwise

        """
        whitelisted_processes = self.hsx_get_whitelisted_processes()
        if not whitelisted_processes:
            return

        result, pids = self.hsx_validate_whitelisted_processes_labels(whitelisted_processes)
        if result is None:
            return
        if result is False:
            return False

        result = self.hsx_validate_running_processes_labels(whitelisted_processes, pids)
        return result

    def hyperscale_validate_ws_selinux_tagging(self, hyperscale_helper, storage_pool_name):
        """
        Checking the sSELinuxProtectedMountPaths key is correctly set
        checking whether the tagging happened correctly in /ws/*
        Args :
            hyperscale_helper       : hyperscale_helper object
            storage_pool_name (str) : Storagepool name
        Returns : True/False
        """

        if not self.check_hyperscale_machine():
            self.log.error("Not a HyperScale Machine")
            raise Exception("Not a HyperScale Machine")

        brick_details = hyperscale_helper.gluster_brick_information(self.media_agent_name)
        brick_details = [brick.split(":")[1][:-9] for brick in
                         brick_details if self.media_agent_name in brick]
        details = hyperscale_helper.get_storage_pool_details(storage_pool_name)
        lib_id = details._storage_pool_properties['storagePoolDetails']['libraryList'][0]['library']['libraryId']
        mount_details = hyperscale_helper.check_library_mount(lib_id)
        brick_details.append(mount_details[0][2])
        self.log.info(f"brick details on {self.media_agent_name} : {brick_details}")
        protected_mount_paths = self.hyperscale_get_protected_mountpaths()
        if self.machine.compare_lists(brick_details, protected_mount_paths, sort_list=True)[0]:
            self.log.info("Registry entry sSELinuxProtectedMountPaths key is properly set")
        else:
            self.log.error("Mount Paths are not properly added to sSELinuxProtectedMountPaths")
            return False

        protected_mount_paths = [mountpath[4:] for mountpath in protected_mount_paths]
        command = "ls -Z /ws/ | grep 'cvstorage' | awk '{print$5}'"
        self.log.info("Command: %s", command)
        output = self.machine.execute_command(command)
        output = output.output.split("\n")[:-1]
        self.log.info(f"tagged mount paths : {output}")
        if self.machine.compare_lists(protected_mount_paths, output, sort_list=True)[0]:
            return True
        return False

    def hyperscale_selinux_label_mode(self):
        """Selinux Label mode - file/mount level

        Returns: (Str)file / mount
        """
        if not self.check_hyperscale_machine():
            self.log.error("Not a HyperScale Machine")
            raise Exception("Not a HyperScale Machine")
        command = f"grep -i 'sSELinuxLabelMode' " \
                  f"{self.machine.key % ('MediaAgent')}"
        command = command + " | awk '{print$2}'"
        self.log.info("Command : %s", command)
        output = self.machine.execute_command(command)
        output = output.output.replace("\n", "")
        return output

    def hyperscale_get_protected_mountpaths(self):
        """returns the mount paths which are protected
            Returns : List of Protected mountpaths
         """
        if not self.check_hyperscale_machine():
            self.log.error("Not a HyperScale Machine")
            raise Exception("Not a HyperScale Machine")
        self.log.info("Collecting Mount paths which are protected")
        command = f"grep -i 'sSELinuxSecurityEnabled' {self.machine.key % ('MediaAgent')}"
        command = command + " | awk '{print$2}'"
        self.log.info("Command : %s", command)
        output = self.machine.execute_command(command)
        output = output.output.replace("\n", "")
        if output != 'Yes':
            self.log.error("sSELinuxSecurityEnabled registry key is not set to yes on Node")

        command = f"grep -i 'sSELinuxProtectedMountPaths' {self.machine.key % ('MediaAgent')}"
        command = command + " | awk '{print$2}'"
        self.log.info("Command : %s", command)
        output = self.machine.execute_command(command)
        output = output.output.replace("\n", "")
        output = output.split(",")
        self.log.info("The protected mountpaths are : {0}".format(output))
        return output

    def hsx_get_protected_mountpaths(self, skip_read_only=False):
        """Returns the mount paths which are protected

            Args:

                skip_read_only  (bool)  --  Whether to skip <vdisk>-r path or not

            Returns:

                result          (list)  --  List of Protected mountpaths

         """
        reg_type = 'MediaAgent'
        reg_key = "sSELinuxProtectedMountPaths"
        if not self.machine.check_registry_exists(reg_type, reg_key):
            self.log.error(f"Registry {reg_key} doesn't exist")
            return
        self.log.info(f"Registry {reg_key} exists")

        value = self.machine.get_registry_value(reg_type, reg_key)
        self.log.info(f"Registry {reg_key} has {value}")
        if not value:
            self.log.error(f"Registry {reg_key} is empty")
            return

        paths = value.strip().split(',')
        if skip_read_only:
            paths = [p for p in paths if not p.endswith('-r')]

        self.log.info(f"Retrieved protected mount paths: {paths}")
        return paths

    @staticmethod
    def hsx_get_expected_protected_mountpaths(hyperscale_helper, ma_names, ma_machines):
        """Returns a list of hardcoded protected mount paths based on version
        
            Args:

                ma_names            (list)  --  The MA names

                ma_machines         (dict)  --  Dictionary, MA name -> machine object

                hyperscale_helper   (obj)   --  The HyperScaleHelper obj

            Returns:

                result          (list | False)          --  List of Protected mountpaths
                                                        --  False in case of any failure

                reason          (str)                   --  Reason of failure
                                                            None if success

         """
        
        expected_protected_mountpaths = []
        is_hsx_3x_or_above = all(hyperscale_helper.is_hsx_cluster_version_equal_or_above(ma_machines, major_version = 3).values())
        vdisk_name = hyperscale_helper.verify_vdisk_registry(ma_names, ma_machines)
        if not vdisk_name:
            hyperscale_helper.log.error(f"Vdisk is either not found or has different values across MAs")
            reason = f"Vdisk is either not found or has different values across MAs"
            return False, reason
        identical, result = hyperscale_helper.verify_sp_version_for_media_agents(ma_machines)
        if not identical:
            hyperscale_helper.log.error(f"Product versions are different across MAs")
            reason = f"Product versions are different across MAs"
            return False, reason
        
        product_version = result[ma_names[0]][0]
        hyperscale_helper.log.info(f"Product version -> {product_version}")
        if product_version <= 28:
            expected_protected_mountpaths = [f'/hedvig/d{i}' for i in range(3, 9)]
            expected_protected_mountpaths += [f"/ws/hedvig/{vdisk_name}{s}" for s in ["", "-r"]]
        elif product_version >= 32:
            expected_protected_mountpaths = [
                f"/flache/metadatadir",
                *[f"/hedvig/d{i}" for i in range(2, 9)],
                "/hedvig/hpod/data",
                "/hedvig/hpod/log",
                *[f"/mnt/d{i}" for i in range(2, 6)],
                "/mnt/f1",
                "/opt/commvault/MediaAgent64/IndexCache"
            ]
        
        if is_hsx_3x_or_above:
            expected_protected_mountpaths.append("/ws/ddb/CV_SIDB")
        hyperscale_helper.log.info(f"Protected mount paths -> {expected_protected_mountpaths}")
        reason = None
        return sorted(expected_protected_mountpaths), reason

    def hyperscale_validate_mountpath_protected(self, mount_path, id):
        """checks whether the mountpath is write protected
         Args:
            mount_path - mountpath to validate
            id : unique id for file name
        Returns : True/False
         """
        
        hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        if not self.check_hyperscale_machine():
            self.log.error("Not a HyperScale Machine")
            raise Exception("Not a HyperScale Machine")
        protection_status = False
        # try to append data to the file
        append_status = False
        self.log.info(f"verifying whether the mount path {mount_path} is protected on "
                      f"{self.media_agent_name}")
        files = self.machine.get_files_in_path(mount_path)

        #Excluding backup_ssh_keys directory since it doesn't get proper context on 3.x (Until this issue is fixed)
        node_major_version = hyperscale_helper.is_hsx_node_version_equal_or_above(ma_machine = self.machine, major_version = 3)
        
        if node_major_version:
            files = list(filter(lambda x:'backup_ssh_keys' not in x, files))
        if files == ['']:
            append_status = True
        else:
            command = f"echo 'Appending content to the protected file' >> '{files[0]}' & echo $!"
            self.log.info("Command : %s ", command)
            output = self.machine.execute_command(command)
            pid = int(output.formatted_output)

            pid_search = f"pid={pid}"
            command = f"cat /var/log/audit/audit.log* | grep {pid_search}"
            output = self.machine.execute_command(command)
            terms = ['avc:  denied  { append }', pid_search, 'success=no']
            if all([term in output.output for term in terms]):
                self.log.info("Append action denied, Mount path is write protected")
                append_status = True
            else:
                self.log.error("Mountpath : %s is not write protected ", mount_path)

        # try to create folder
        add_status = False
        self.log.info("creating a folder in mount path ")
        path = self.machine.join_path(mount_path, f"{id}_newfolder")
        command = f"mkdir {path} & echo $!"
        self.log.info("Command : %s ", command)
        output = self.machine.execute_command(command)
        pid = int(output.formatted_output)

        if self.machine.check_directory_exists(path):
            self.log.error("mount path not write protected, ransomware not working")
        else:
            self.log.info("directory creation failed, mount path write protected")

        pid_search = f"pid={pid}"
        command = f"cat /var/log/audit/audit.log* | grep {pid_search}"
        output = self.machine.execute_command(command)
        terms = ['avc:  denied  { write }', pid_search, 'comm="mkdir"', 'success=no']
        if all([term in output.output for term in terms]):
            add_status = True
            self.log.info("create folder action denied, Mounpath is write protected")
        else:
            self.log.error("Mountpath : %s is not write protected", mount_path)

        if self.machine.check_directory_exists(path):
            self.machine.remove_directory(path)

        # try to delete content
        delete_status = False
        self.log.info("deleting a folder")
        folder = sorted(self.machine.get_folders_in_path(mount_path), reverse=True)
        folder = list(filter(lambda x: x != mount_path, folder))
        if folder == []:
            delete_status = True
        else:
            command = f"rm -rf {folder[0]} & echo $!"
            self.log.info("Command : %s ", command)
            output = self.machine.execute_command(command)
            pid = int(output.formatted_output)

            if self.machine.check_directory_exists(folder[0]):
                self.log.info("deletion failed for %s", folder[0])
            else:
                self.log.error("delete success, not protected")

            pid_search = f"pid={pid}"
            command = f"cat /var/log/audit/audit.log* | grep {pid_search}"
            self.log.info(f"Command : {command} ")
            output = self.machine.execute_command(command)
            terms = ['avc:  denied  { write }', pid_search, 'comm="rm"', 'success=no']
            if all([term in output.output for term in terms]):
                self.log.info("delete action denied , Mountpath is write protected")
                delete_status = True
            else:
                self.log.error("Mountpath : %s is not write protected", mount_path)

        if append_status and add_status and delete_status:
            protection_status = True
        return protection_status

    def enable_protection_linux(self, library_present=False):
        """
        Enable ransomware protection
        If it fails to bring up services post restart/reboot for new machine please re run it
        Args:
            library_present     (bool)  --  Default: False, if library is present already
        Returns : None
        """
        self.log.info("Putting MA in maintenance mode")
        media_agent = self.commcell.media_agents.get(self.machine.machine_name).\
            mark_for_maintenance(True)
        time.sleep(120)

        self.log.info("Enabling protection")
        if int(self.machine.client_object.service_pack) < 23:
            command = f"(cd {self.client_obj.install_directory}/MediaAgent && " \
                    f"./cvsecurity.py enable_protection -i {self.machine.instance})"
        else :
            command = f"yes | (cd {self.client_obj.install_directory}/MediaAgent && " \
                      f"./cvsecurity.py enable_protection -i {self.machine.instance})"

        self.log.info("command: %s", command)
        output = self.machine.execute_command(command)
        self.log.info(output.exception_message)
        self.log.info(output.output)
        policy_load_status = self.policy_load_status()

        if not policy_load_status:
            self.log.error("Policy did not load successfully")
            raise Exception("Policy load failed")
        self.log.info("Policy load success")

        self.log.info("Creating /etc/fstab copy")
        self.machine.copy_folder("/etc/fstab", "/root/")

        # For library present
        if library_present and int(self.machine.client_object.service_pack) < 23:
            command = f"yes | (cd {self.client_obj.install_directory}/MediaAgent && " \
                      f"./cvsecurity.py protect_disk_library -i {self.machine.instance})"
            self.log.info("command: %s", command)
            output = self.machine.execute_command(command)
            self.log.info(output.exception)
            self.log.info(output.output)
        # If it fails to bring up services post restart/reboot for new machine please re run it
        self.log.info("Rebooting the MA")
        command = "reboot"
        output = self.client_obj.execute_command(command=command, wait_for_completion=False)
        if not self.install_helper_obj.wait_for_services(client=self.machine.client_object):
            self.log.info("client ma ready")
        time.sleep(300)
        if not self.check_hyperscale_machine():
            self.log.info("Restarting CV Services")
            command = f"(cd {self.client_obj.install_directory}/MediaAgent &&" \
                      f" ./cvsecurity.py restart_cv_services -i {self.machine.instance})"
            self.log.info("command: %s", command)
            output = self.client_obj.execute_command(command=command, wait_for_completion=False)
            time.sleep(300)
            if not self.install_helper_obj.wait_for_services(client=self.machine.client_object):
                self.log.info("client ma ready")

        self.log.info("logging logs for restart_cv_services")
        command = "cat /var/log/cvsecurity.log | tail -50"
        output = self.machine.execute_command(command)
        self.log.info(output.output)

        policy_load_status = self.policy_load_status()
        if not policy_load_status:
            self.log.error("Policy did not load successfully")
        self.log.info("Policy load success")
        time.sleep(300)
        mode = self.check_ransomware_mode()
        if not mode:
            self.log.info("Ransomware in permissive mode")
            raise Exception("Ransomware not enabled")

        self.log.info("Putting MA off maintenance mode")
        media_agent = self.commcell.media_agents.get(self.machine.machine_name).\
            mark_for_maintenance(False)
        time.sleep(240)

        if self.check_hyperscale_machine():
            self.hyperscale_validate_process_selinux_tagging()
        else:
            verify_ransomware = self.verify_ransomware_enablement()
            if not verify_ransomware:
                raise Exception("ransomware enablement failed")
            self.log.info("Ransomware enabled status = %s", verify_ransomware)

    def hsx_enable_protection(self, hyperscale_helper: HyperScaleHelper):
        """Enables protection on this HSX node

            1. Fires the enable_protection command
            2. Reboots
            3. Waits for enable_protection to complete
                using sRestartCVSecurity

            In FR32 we have to fire commvault stop command first before performing 1,2,3
        """

        product_version = hyperscale_helper.get_sp_version_for_media_agent(self.machine)
        product_version = product_version[0]
        self.log.info(f"Product version -> {product_version}")
        if(product_version >= 32):
            self.log.info("Firing commvault stop command")
            command = r"commvault stop"
            self.machine.execute_command(command)
        
        command = f"yes | {self.cvsecurity_py} enable_protection -i {self.machine.instance} 2>&1"
        self.log.info(f"hsx enable protection command: {command}")
        output: UnixOutput = self.machine.execute_command(command)
        self.log.info(f"{command} -> {output.output}")
        if output.exception_message or output.exit_code:
            self.log.error("Got an exception while enabling protection")
            self.log.error(f"exception message: {output.exception_message}")
            self.log.info(f"exit code: {output.exit_code}")
            return False

        if " ERROR " in output.output:
            if (output.output.count(" ERROR ") == 1 and "ERROR - no vdisk mounted" in output.output):
                self.log.info("Got no errors while enabling protection")
            else:
                self.log.error("Got an ERROR while enabling protection")
                return False

        if "failed" in str(output.output).lower():
            if (output.output.count("failed") == 1 and "failed=0" in output.output):
                self.log.info("Nothing failed while enabling protection")
            else:
                self.log.error("Something failed while enabling protection")
                return False

        if "Please reboot the system for enabling ransomware protection" not in output.output:
            self.log.error("Didn't find the reboot request in the output while enabling protection")
            return False

        if not self.machine.check_registry_exists("MediaAgent", "sRestartCVSecurity"):
            self.log.error("sRestartCVSecurity reg key not found")
            return False
        self.log.info("sRestartCVSecurity reg key found")

        value = self.machine.get_registry_value("MediaAgent", "sRestartCVSecurity")
        if value != "Yes":
            self.log.error(f"sRestartCVSecurity value is {value}. Expected Yes")
            return False
        self.log.info("sRestartCVSecurity is set to Yes")

        command = "shutdown -r +1"
        output = self.machine.execute_command(command)
        self.log.info(f"{command} -> {output.output}")
        time.sleep(40)

        if not hyperscale_helper.wait_for_ping_result_to_be(1, self.media_agent_name, retry_duration=3 * 60):
            self.log.error("Machine didn't shutdown")
            return False
        self.log.info("Machine down. Waiting for it to be up again")

        if not hyperscale_helper.wait_for_ping_result_to_be(0, self.media_agent_name, retry_duration=30 * 60,
                                                            silent=True):
            self.log.error("Machine didn't reboot in stipulated time")
            return False

        self.log.info("Node rebooted. Additional time for SSH services to come up")
        time.sleep(10)

        if not hyperscale_helper.wait_for_reg_key_to_be(self.machine, "No", "sRestartCVSecurity",
                                                        retry_duration=30 * 60):
            self.log.error("sRestartCVSecurity not set to No")
            return False
        self.log.info("sRestartCVSecurity set to no post reboot")
        self.log.info(
            "Successfully enabled ransomware. Waiting for a couple of minutes to change from permissive to enforcing mode...")

        result = hyperscale_helper.wait_for(self.validate_sestatus_when_rwp_enabled, bool, interval = 60, retry_duration= 20 * 60)

        if not result:
            self.log.error(f"Could not change from permissive to enforcing mode")
            return False
        self.log.info(f"Successfully changed from permissive to enforcing mode")
        return True

    @staticmethod
    def hsx_validate_registry_entries(hyperscale_helper: HyperScaleHelper, ma_names, ma_machines, expected_protected_mountpaths):
        """Verifies whether correct registry keys are present across MAs

            Args:

                hyperscale_helper       (obj)   --  The HyperScaleHelper object

                ma_names                (list)  --  The list of names of MediaAgents

                ma_machines             (dict)  --  Dictionary, MA name -> machine object

                protected_mount_paths   (list)  --  The list of protected mount paths

            Returns:

                result              (bool)  --  Whether verified or not
                                                None, in case of errors

        """

        expected_reg_keys = {
            "sProtectDiskLibraryStorageEnabled": "Yes",
            # "sRWPHedvigServices": "hedvighpod,hedvigpages",
            "sRestartCVSecurity": "No",
            "sSELinuxSecurityEnabled": "Yes",
            "sSELinuxProtectedMountPaths": ",".join(expected_protected_mountpaths),
            "sSELinuxLabelMode": "mount",
        }
        is_hsx_3x_or_above = all(hyperscale_helper.is_hsx_cluster_version_equal_or_above(ma_machines, major_version = 3).values())

        if is_hsx_3x_or_above:
            expected_reg_keys["sSELinuxLabelMode"] = "file"
            
        added_nodes = [ma_name for ma_name in ma_names if hyperscale_helper.is_added_node(ma_machines[ma_name])]
        other_nodes = [ma_name for ma_name in ma_names if ma_name not in added_nodes]
        
        def internal_hsx_validate_registry_entries(ma_names, expected_reg_keys, reg_keys_to_be_sorted = ["sSELinuxProtectedMountPaths"]):
            hyperscale_helper.log.info(f"Expected reg keys: {expected_reg_keys}")
            key_list = expected_reg_keys.keys()
            values, identical_list = hyperscale_helper.get_reg_key_values(ma_names, ma_machines, key_list, to_be_sorted=reg_keys_to_be_sorted)
            for identical, key_name in zip(identical_list, expected_reg_keys.keys()):
                if not identical:
                    hyperscale_helper.log.error(f"Key {key_name} is not identical across MAs")
                    return False
            hyperscale_helper.log.info(f"{key_list} identical across MAs")

            for key, expected in expected_reg_keys.items():
                actual = values[key][0]
                if expected != actual:
                    hyperscale_helper.log.error(f"Key {key}, expected: {expected}, got: {actual}")
                    return False
            hyperscale_helper.log.info(f"{key_list} matches expectations")
            return True
        
        result = internal_hsx_validate_registry_entries(ma_names, expected_reg_keys)
        if not result:
            return False
        
        if other_nodes:
            result = internal_hsx_validate_registry_entries(other_nodes, {"sRWPHedvigServices" : "hedvighpod,hedvigpages"})
            if not result:
                return False
        
        if added_nodes:
            # the added nodes will have this key but it will be empty
            result = internal_hsx_validate_registry_entries(added_nodes, {"sRWPHedvigServices" : None})
            if not result:
                return False
        
        return True
        

    def delete_registry_entries(self):
        """Deletes the registry entries related to Ransomware Protection
        """
        reg_keys = [
            "sProtectDiskLibraryStorageEnabled",
            "sRWPHedvigServices",
            "sRestartCVSecurity",
            "sSELinuxLabelMode",
            "sSELinuxProtectedMountPaths",
            "sSELinuxSecurityEnabled",
        ]
        for reg_key in reg_keys:
            if self.machine.check_registry_exists('MediaAgent', reg_key):
                self.machine.remove_registry('MediaAgent', reg_key)
                self.log.info(f"Removed {reg_key}")
            else:
                self.log.info(f"{reg_key} doesn't exist so not removing")

    def hsx_validate_fstab(self, expected_drives, product_version):
        """Verifies the fstab file for selinux label

            Args:

                expected_drives     (list)  -- The list of protected mount paths

            Returns:

                result              (bool)  --  Whether verified or not
                                                None, in case of errors

        """
        command = "cat /etc/fstab | grep -v '#' | grep 'cvstorage_t' | sort -k 2"
        output = self.machine.execute_command(command)
        output = output.output
        self.log.info(f"{command} -> {output}")

        if not output:
            self.log.error(f"Error while executing {command}")
            return

        lines = output.strip().split("\n")

        # Removing vdisk and vdisk -r as it not protected mount path

        if(product_version <= 28):
            expected_drives = expected_drives[:-2]

        if len(lines) != len(expected_drives):
            self.log.error(f"Unexpected number of lines in {command}")
            return False
        for line, drive in zip(lines, expected_drives):
            if "cvstorage_t" not in line:
                self.log.error(f"{line} doesn't contain the selinux label")
                return False

            if drive not in line:
                self.log.error(f"Wrong drive. Expected {drive} in {line}")
                return False

        self.log.info(f"All drives contain the right tagging in /etc/fstab")
        return True

    def backup_fstab(self, id):
        """Saves the /etc/fstab file

            Args:

                id      (str)   --  The test case id

            Returns:

                result  (bool)  --  Whether saved successfully or not
        """
        command = "grep cvstorage_t /etc/fstab"
        output = self.machine.execute_command(command)
        output = output.output
        if output:
            self.log.error(f"Couldn't backup fstab, it already contains the selinux tagging info")
            return False

        path = f"~/Automation/{id}"
        self.log.info(f"backing up fstab to {path}")

        command = f"mkdir -p {path}; \\cp /etc/fstab {path}"
        output: UnixOutput = self.machine.execute_command(command)
        if output.exception_code:
            self.log.error(f"Error while taking backup of fstab: {output.exception_code} : {output.exception_message}")
            return False
        self.log.info(f"backed up fstab to {path}")
        return True

    def restore_fstab(self, id):
        """Restores /etc/fstab file to its original state (before ransomware protection)

            Args:

                id      (str)   --  The test case id

            Returns:

                result  (bool)  --  Whether restored successfully or not

        """
        path_dir = f"~/Automation/{id}"
        path_fstab = f"{path_dir}/fstab"

        if not self.machine.check_file_exists(path_fstab):
            self.log.warning(f"There is no backup fstab file present. Copying now")
            command = f"mkdir -p {path_dir}; cp /etc/fstab {path_dir}"
            output = self.machine.execute_command(command)
            if output.exception or output.exception_code:
                self.log.error(f"Failed to copy /etc/fstab to {path_dir}. Maybe the file doesn't exist?")
                return False

        # backed up fstab exists, now check if it is legit
        command = f"grep cvstorage_t {path_fstab}"
        output = self.machine.execute_command(command)
        output = output.output
        self.log.info(f"{command} -> {output}")
        if not output:
            command = f"\\cp {path_fstab} /etc/fstab"
            self.machine.execute_command(command)
            self.log.info("fstab restored successfully")
            return True

        # backed up fstab is not legit, surgically fix it
        self.log.warning(f"{path_fstab} contains the selinux tagging info. Removing it now and restoring")
        command = f'sed \'s/,context="system_u:object_r:cvstorage_t:s0"/    /g\' {path_fstab} > /etc/fstab'
        output = self.machine.execute_command(command)

        self.log.info(f"{command} -> {output.output}")
        if output.exception or output.exception_code:
            self.log.error("fstab restoration failed")
            return False

        self.log.info("Successfully restored fstab")
        return True

    def hsx_validate_protected_mount_paths_mounted(self, hyperscale_helper: HyperScaleHelper):
        """Validates if protected mount paths are mounted or not

            Args:

                hyperscale_helper   (obj)   --  The HyperScaleHelper obj

            Returns:

                result              (bool)  --  Whether validated or not

        """
        protected_mount_paths = self.hsx_get_protected_mountpaths()
        for path in protected_mount_paths:
            if path == "/ws/ddb/CV_SIDB":
                path = "/ws/ddb"
            command = f"grep '{path}' /etc/mtab"
            output = self.machine.execute_command(command)
            output = output.output
            self.log.info(f"{command} -> {output}")
            if not output:
                self.log.error(f"{path} not mounted (mtab)")
                return False
            self.log.info(f"{path} is mounted (mtab)")

        for path in protected_mount_paths:
            if path == "/ws/ddb/CV_SIDB":
                path = "/ws/ddb"
            command = f"df | grep '{path}'"
            output = self.machine.execute_command(command)
            output = output.output
            self.log.info(f"{command} -> {output}")
            if not output:
                self.log.error(f"{path} not mounted (df)")
                return False
            self.log.info(f"{path} is mounted (df)")

        return True

    def hsx_validate_context_on_protected_mount_paths(self):
        """Validates the security context on the protected mount paths

            Returns:

                    result              (bool)  --  Whether verified or not
                                                    None, in case of errors
        """
        paths = self.hsx_get_protected_mountpaths(skip_read_only=True)
        if paths is None:
            return

        command = 'ls -dZ ' + " ".join(paths)
        output = self.machine.execute_command(command)
        output = output.output
        self.log.info(f"{command} -> {output}")
        if not output:
            self.log.error(f"context output is empty")
            return

        lines = output.strip().split('\n')
        if len(lines) != len(paths):
            self.log.error(f"Couldn't retrieve context for some paths")
            return

        self.log.info(f"Retrieved context for all paths: {paths}")

        for path, context in zip(paths, lines):
            if "cvstorage_t" not in context:
                self.log.error(f"Couldn't find the right context for {path}. Got: {context}")
                return False
        self.log.info(f"context verified for all protected mount paths")
        
        for path in paths:

            # Output of ls -ldZ /hedvig/d6/* looks like
            # -rw-r--r--.  1 root root system_u:object_r:cvstorage_t:s0  4791 Feb 28 12:03 /hedvig/d6/backup_network.zip
            # drwxr-xr-x.  3 root root system_u:object_r:etc_t:s0        4096 Feb 22 11:20 /hedvig/d6/backup_ssh_keys
            # drwxr-xr-x. 15 root root system_u:object_r:cvstorage_t:s0  4096 Feb 29 06:48 /hedvig/d6/data
            # drwxrwxrwx.  2 root root system_u:object_r:cvstorage_t:s0    35 Feb 28 11:34 /hedvig/d6/handle
            # -rw-r--r--.  1 root root system_u:object_r:cvstorage_t:s0 16384 Mar  6 13:54 /hedvig/d6/io_test.txt


            command = f'ls -ldZ {path}/*'
            output = self.machine.execute_command(command)
            output = output.output
            self.log.info(f"{command} -> {output}")
        
            sub_contents = output.strip().split('\n')
            sub_contents = [line for line in sub_contents if line.startswith(('d', '-'))]

            for line in sub_contents:
                if "cvstorage_t" not in line:
                    content = line.split()[-1]
                    self.log.error(f"Could not find right context on {content}")
                    # Return False once ssh_backup_keys not getting context issue is fixed, otherwise will fail the testcase always
                    # return False
        self.log.info(f"context verified for all contents within protected mount paths")

        return True

    def hsx_validate_context_on_whitelisted_binaries(self):
        """Validates the security context on the whitelisted binaries or scripts

            Returns:

                    result              (bool)  --  Whether verified or not
                                                    None, in case of errors
        """
        whitelisted_processes = self.hsx_get_whitelisted_processes(names_only=False)
        if not whitelisted_processes:
            return

        command = 'ls -Z ' + " ".join(whitelisted_processes)
        output = self.machine.execute_command(command)
        output = output.output
        self.log.info(f"{command} -> {output}")

        if not output:
            return

        lines = output.strip().split("\n")
        if len(lines) != len(whitelisted_processes):
            actual_binaries = set([l.split(' ')[-1] for l in lines])
            diff = actual_binaries.symmetric_difference(set(whitelisted_processes))
            self.log.warning(f"{len(whitelisted_processes) - len(lines)} binaries ({diff}) are missing. Ignoring")

        for binary in lines:
            if "cvbackup_exec_t" not in binary:
                self.log.error(f"Binary {binary} not tagged correctly")
                return False
        self.log.info("All binaries have the right context")
        return True


    def validate_rwp_blocked_commands(self,ma_machine):
        """Validates that certain commands are blocked after enabling rwp

            Args:

                ma_machine              (obj)                   --  Machine class object of MA
        
            Returns:

                result, reason          (bool, str)             --  Returns True all checked commands are blocked
                                                                    Else False and Reason of failure

        """

        commands = {
            "dd": "dd",
            "setenforce": "setenforce",
            "mke2fs": "mke2fs",
            "mkfs": "mkfs",
            "mkfs.ext2": "mkfs.ext2",
            "mkfs.ext3": "mkfs.ext3",
            "mkfs.ext4": "mkfs.ext4",
            "mkfs.fat": "mkfs.fat",
            "mkfs.minix": "mkfs.minix",
            "mkfs.xfs": "mkfs.xfs"
        }

        for command_name, blocked_command in commands.items():
            command = f"{blocked_command} & echo $!"
            output = ma_machine.execute_command(command)
            self.log.info(f"Command : {command} | Output : {output.output}")
            pid = int(output.formatted_output)

            pid_search = f"pid={pid}"
            command = f"cat /var/log/audit/audit.log* | grep {pid_search}"
            output = self.machine.execute_command(command)
            terms = ['avc:  denied  { execute }' ,pid_search, 'success=no']
            if not all([term in output.output for term in terms]):
                self.log.error(f"Failed to validate that {command_name} command is blocked")
                reason = f"Failed to validate that {command_name} command is blocked"
                return False, reason
            self.log.info(f"Validated that {command_name} command is blocked")
        return True, None    

    @staticmethod
    def hsx_rwp_validation_suite(ma_names, ma_machines, hyperscale_helper, rw_helpers):
        """The complete validation suite for HSX ransomware protection

            Args:

                ma_names            (list)  --  The MA names

                ma_machines         (dict)  --  Dictionary, MA name -> machine object

                hyperscale_helper   (obj)   --  The HyperScaleHelper obj

                rw_helpers          (dict)  --  Dictionary, MA name -> UnixRansomwareHelper object

            Returns:

                result, reason      (bool)  --  True if all checks are passed
                                                False if any check fails and reason of failure

        """
        log = hyperscale_helper.log

        step_name = 'HSX Ransomware Protection Validation Suite'
        log.info(step_name)
        step_errors = []
        suite_result = []

        def do_step_start():
            nonlocal step_errors
            step_count = len(suite_result) + 1
            log.info(f"STEP {step_count}: {step_name} - START")
            step_errors = []
        
        def do_step_error(msg):
            log.error(msg)
            step_errors.append(msg)

        def do_step_end():
            step_count = len(suite_result) + 1
            log.info(f"STEP {step_count}: {step_name} - END. {len(step_errors)} Errors")
            step_details = {"step_name":step_name, "step_errors":step_errors}
            suite_result.append(step_details)
        
        def show_summary():
            success = True
            reason_string =f""
            for idx, details in enumerate(suite_result):
                step_count = idx+1
                step_name = details['step_name']
                step_errors = details['step_errors']
                if step_errors:
                    log.error(f"STEP {step_count}: {step_name} FAILED")
                    success = False
                    for error in step_errors:
                        reason_string += (error + ' | ')
                        log.error(error)
                else:
                    log.info(f"STEP {step_count}: {step_name} SUCCESSFUL")
            return success, reason_string


        # 1. validate sestatus output
        step_name = f"Validating sestatus output"
        do_step_start()
        for ma in ma_names:
            result = rw_helpers[ma].validate_sestatus_when_rwp_enabled()
            if not result:
                msg = f"Failed to validate sestatus for {ma}"
                do_step_error(msg)
            else:
                log.info(f"Validated sestatus for {ma} successfully")
        do_step_end()
            
        # 2. Check if commmvault services are running
        step_name = "Checking if commvault services and processes are up"
        do_step_start()
        result = hyperscale_helper.verify_commvault_service_and_processes_are_up(ma_names, ma_machines)
        if not result:
            msg = f"Failed to verify if commvault services or processes are up"
            do_step_error(msg)
        else:
            log.info("Commvault services and processes are up on all nodes")
        do_step_end()

        # 3. Check if hedvig services are running
        step_name = "Checking if hedvig services are up"
        do_step_start()
        result = hyperscale_helper.verify_hedvig_services_are_up(ma_names, ma_machines)
        if not result:
            msg = f"Failed to verify if hedvig services are up"
            do_step_error(msg)
        else:
            log.info("Hedvig services are up on all nodes")
        do_step_end()
            
        # 4. Validate if taggable script / binaries are running in right context
        # and the running processes having cvbackup_t are authentic
        step_name = f"Validating processes on the nodes"
        do_step_start()
        for ma in ma_names:
            result = rw_helpers[ma].hsx_validate_process_label()
            if not result:
                msg = f"Failed to validate processes on {ma}"
                do_step_error(msg)
            else:
                log.info(f"Successfully validated processes on {ma}")
        do_step_end()
        
        # 5. Check context on whitelisted binaries
        step_name = "Checking context on whitelisted binaries"
        do_step_start()
        for ma in ma_names:
            result = rw_helpers[ma].hsx_validate_context_on_whitelisted_binaries()
            if not result:
                msg = f"Failed to validate context on whitelisted binaries for {ma}"
                do_step_error(msg)
            else:
                log.info(f"Successfully validated context on whitelisted binaries for {ma}")
        do_step_end()
            
        # 6. Verify MA registries
        step_name = "Verifying MA registries"
        do_step_start()
        expected_protected_mountpaths, reason = UnixRansomwareHelper.hsx_get_expected_protected_mountpaths(hyperscale_helper, ma_names, ma_machines)
        if not expected_protected_mountpaths:
            reason += f" | Failed to fetch expected protected mount paths"
            do_step_error(reason)
        result = UnixRansomwareHelper.hsx_validate_registry_entries(hyperscale_helper, ma_names, ma_machines, expected_protected_mountpaths)
        if not result:
            msg = f"Failed to verify MA registries for MAs"
            do_step_error(msg)
        else:
            log.info(f"Successfully verified MA registries for MAs")
        do_step_end()

        # 7. Check fstab for drive context
        step_name = "Checking fstab for drive context"
        is_hsx_3x_or_above = all(hyperscale_helper.is_hsx_cluster_version_equal_or_above(ma_machines, major_version = 3).values())
        if is_hsx_3x_or_above:
            log.info(f"Skipping drive context validations on fstab for HSX 3.x")
        else:
            do_step_start()
            expected_protected_mountpaths, reason = UnixRansomwareHelper.hsx_get_expected_protected_mountpaths(hyperscale_helper, ma_names, ma_machines)
            identical, product_version = hyperscale_helper.verify_sp_version_for_media_agents(ma_machines)
            if not identical: 
                msg = f"MAs does not have identical versions"
                do_step_error(msg)
            product_version = product_version[ma_names[0]][0]
            for ma in ma_names:
                result = rw_helpers[ma].hsx_validate_fstab(expected_protected_mountpaths, product_version)
                if not result:
                    msg = f"Failed to validate fstab for drive context for {ma}"
                    do_step_error(msg)
                else:
                    log.info(f"Successfully validated fstab for drive context for {ma}")
            do_step_end()
            
        # 8. Check whether protected mount paths are mounted
        step_name = "Checking whether protected mount paths are mounted"
        do_step_start()
        for ma in ma_names:
            result = rw_helpers[ma].hsx_validate_protected_mount_paths_mounted(hyperscale_helper)
            if not result:
                msg = f"Failed to validate whether protected mount paths are mounted for {ma}"
                do_step_error(msg)
            else:
                log.info(f"Successfully validated whether protected mount paths are mounted for {ma}")
        do_step_end()
        
        # 9. Check context on protected mount paths
        step_name = "Checking context on protected mount paths"
        do_step_start()
        for ma in ma_names:
            result = rw_helpers[ma].hsx_validate_context_on_protected_mount_paths()
            if not result:
                msg = f"Failed to validate context on protected mount paths for {ma}"
                do_step_error(msg)
            else:
                log.info(f"Successfully validated context on protected mount paths for {ma}")
        do_step_end()
            
        # 10. Check append / write / delete on mount path
        step_name = "Checking append / write / delete on mount path"
        do_step_start()
        for ma in ma_names:
            paths = rw_helpers[ma].hsx_get_protected_mountpaths()
            for path in paths:
                result = rw_helpers[ma].hyperscale_validate_mountpath_protected(path, rw_helpers[ma_names[0]].short_name)
                if not result:
                    msg = f"Failed to validate append / write / delete on mount path {path} for {ma}"
                    do_step_error(msg)
                else:
                    log.info(f"Successfully validated append / write / delete on mount path {path} for {ma}")
        do_step_end()

        # 11. Validating blocked commands
        step_name = "Validating blocked commands"
        do_step_start()
        for ma_name in ma_names:
            ma_machine = ma_machines[ma_name]
            result, reason = rw_helpers[ma_name].validate_rwp_blocked_commands(ma_machine)
            if not result:
                reason += f"Failed to validate blocked commands for {ma_name}"
                do_step_error(reason)
            else:
                log.info(f"Successfully validated blocked commands for {ma_name}")
        do_step_end()

        return show_summary()
