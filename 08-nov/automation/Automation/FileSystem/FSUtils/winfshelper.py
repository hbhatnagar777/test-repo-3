# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Windows File System operations

WinFSHelper is the only class defined in this file.

WinFSHelper: Helper class to perform file system operations

WinFSHelper:
============

    remote_login()                              --  Establishes remote desktop connection with the client.

    get_log_file()                              --  Reads and returns the contents of a log file as a string.

    get_logs_for_job_from_file()                --  From a log file object only return those
    log lines for a particular job ID.

    get_current_extent_level_pass()             --  It retrieves the current pass number for
    the extent level backup job.

    get_copyid_for_extent_backup()              --  It retrieves the copy ID for the extent level backup.

    is_copyid_persistent()                      --  Checks if given copy ID is persistent.

    multi_stream_restore_validation()           --  Checks whether the restore job used multiple streams.


    get_failed_items_in_jr()                    --  Returns a dictionary containing entries from
    Failures.cvf and FailedFileRetryCollect.cvf in the form of a dictionary.

    get_extent_backup_stream_count()            --  Returns number of streams used by an extent level backup from logs.

    get_restore_stream_count()                  --  Returns number of streams used by a restore job from logs.

    bmr_verify_vmware()                         --  Checks whether the machine booed up properly post 1-touch to vmware

    bmr_verify_hyperv()                         --  Checks whether the machine booed up properly post 1-touch to hyper-v

    get_no_of_qualified_objects_from_filescan() --  Returns number of objects qualified for backup from FileScan.log.

    get_volume_guid()                           --  Returns the volume guid for given drive letter.


WinFSHelper Instance Attributes:
================================

    **log_files_dir**   --  Returns the Commvault log file directory for the client machine instance.

"""

# TODO START USING CONSTANTS FOR FILE NAMES LIKE Failures.cvf & FailedFileRetryCollect.cvf & SOME REGEX PATTERNS

import subprocess
import time
import re
from AutomationUtils import machine
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils.constants import BMR_VERIFY_VMWARE,BMR_VERIFY_HYPERV


class WinFSHelper(FSHelper):
    """Helper class to perform file system operations"""

    def __init__(self, testcase):
        """Initialize instance of the WinFSHelper class."""
        super(WinFSHelper, self).__init__(testcase)
        self._log_files_dir = None

    @property
    def log_files_dir(self):
        """Returns the log file directory for the given client."""
        return self.testcase.client_machine.get_registry_value("EventManager", "dEVLOGDIR")

    @staticmethod
    def populate_tc_inputs(cv_testcase):
        """Initializes all the test case inputs after validation

        Args:
            cv_testcase    (obj)    --    Object of CVTestCase

        Returns:
            None

        Raises:
            None

        """

        FSHelper.populate_tc_inputs(cv_testcase)

    def remote_login(self):
        """Establishes remote desktop connection with the client.

            Raises:
                Exception - If remote login is not successful
        """
        try:
            stopped = 0
            machine_name = self.testcase.client.client_hostname
            client_name = self.testcase.tcinputs['ClientName']
            client_admin_username = self.testcase.tcinputs['ClientAdminUsername']
            client_admin_password = self.testcase.tcinputs['ClientAdminPassword']
            machine_instance = machine.Machine(
                machine_name, username=client_admin_username, password=client_admin_password
            )

            # Remote desktop connection for non-admin account
            username = self.testcase.tcinputs['ClientNonAdminUsername']
            local_file_path = "C:\\test"
            backup_content = self.testcase.tcinputs['TestPath']
            subprocess.Popen("mstsc /v:" + client_name, shell=True)
            self.log.info("Waiting for 90 seconds before checking for the status of RDP session")
            time.sleep(90)
            # Check if the RDP was launched
            session_output = machine_instance.execute_command("query session")
            if session_output.exception_message is None:
                session_info = session_output.formatted_output
                username_t = username
                if '\\' in username_t:
                    username_t = username_t[username_t.index("\\") + 1:]
                username_index = session_info.find(username_t)
                if username_index != -1:
                    entry = session_info[
                        username_index:
                        username_index + session_info[
                            username_index:
                            len(session_info)
                        ].index("\n")
                    ]
                    if entry.find("Active") == -1:
                        raise Exception("Failed to launch RDP session for the user. "
                                        "Ensure no other sessions are running for the user and try again")
                    else:
                        self.log.info("RDP was launched successfully")
                else:
                    raise Exception("No session entry for the user was found")
            else:
                raise Exception("Failed to get session information")
            self.log.info("Stopping services on remote client before creating backup content")
            installation_path = self.testcase.client.install_directory
            if not installation_path:
                raise Exception("Failed to get installation path of client")

            command_output = machine_instance.execute_command(
                machine_instance.join_path(installation_path.replace(" ", "' '"),
                                           "Base\\gxadmin -consoleMode -stopsvcgrp All")
            )

            if command_output.exception_message is None:
                stopped = 1
                self.log.info("Copying content to remote client")
                command_output = machine_instance.copy_from_local(
                    local_file_path,
                    backup_content
                )
                if command_output[0][0] is False:
                    raise Exception("Could not copy content to remote machine")
            else:
                raise Exception(command_output.exception_message)
        finally:
            if stopped:
                self.log.info("Starting services on remote client")
                command_output = machine_instance.execute_command(
                    machine_instance.join_path(
                        installation_path.replace(" ", "' '"),
                        "Base\\gxadmin -consoleMode -startsvcgrp All"
                    )
                )
                if command_output.exception_message is not None:
                    raise Exception("Count not start services. %s" % (command_output.exception_message))

    def get_log_file(self, log_file_name, all_versions=False):
        """Returns the contents of a log file.

        Args:
            log_file_name   (str)   --  Name of the log file.

            all_versions    (bool)  --  Whether to parse all the older versions of the log file as well.
            If it's false, it will only read and return the contents of the most recent version of the file.

            **support not yet implemented.**
            **This argument will be ignored and not used till it is implemented**

        Returns:
            str     -   \r\n separated string containing the requested log lines.

        Raises:
            None

        """

        return self.testcase.client_machine.get_log_file(log_file_name,  all_versions=False)

    def get_logs_for_job_from_file(self, job_id=None, log_file_name=None, search_term=None):
        """Return all log lines for a particular job ID or only those containing the search term if one is provided.

        Args:
            job_id          (str)   --  Job ID for which log lines need to be fetched.

            log_file_name   (bool)  --  Name of the log file.

            search_term     (str)   --  Only capture those log lines containing the search term.

        Returns:
            str     -   \r\n separated string containing the requested log lines.

            None    -   If no log lines were found for the given job ID or containing the given search term.

        Raises:
            None

        """

        # GET ONLY LOG LINES FOR A PARTICULAR JOB ID
        return self.testcase.client_machine.get_logs_for_job_from_file(job_id, log_file_name, search_term)

    # EXTENT LEVEL BACKUP SPECIFIC FUNCTION
    def get_current_extent_level_pass(self, job, return_log_line=True):
        """It retrieves the current pass number for the extent level backup job.

        Args:
            job             (obj)   --  Job object for which log lines need to be fetched.

            return_log_line (bool)  --  Log line indicating the current pass.

        Returns:

            int -   Value of the current pass.

            str -   The log line indicating the current pass number.

        Raises:
            None

        """

        pass_num, pass_log_line = 0, ""
        log_file = self.get_logs_for_job_from_file(job.job_id, "clBackup.log", "CurrentExtentPass =")
        if log_file is not None:
            for line in log_file.split("\r\n"):
                re_search = re.search(r"CurrentExtentPass = \[(\d)\]", line)
                if re_search is not None:
                    cur_pass_num = int((re_search).groups()[0])
                    if cur_pass_num > pass_num:
                        pass_num, pass_log_line = cur_pass_num, line

        if return_log_line:
            return pass_num, pass_log_line
        return pass_num

    # EXTENT LEVEL BACKUP SPECIFIC FUNCTION
    def get_copyid_for_extent_backup(self, job, return_log_line=True, exit_on_vss_snap_failure=True):
        """Retrieves the CopyId of VSS snap for the extent level job.

        Args:
            job                         (obj)   --  Job object for which log lines need to be fetched.

            return_log_line             (bool)  --  Log line indicating the CopyId.

            exit_on_vss_snap_failure    (bool)  --  Indicates whether to raise an exception if snap creation failed.

        Returns:

            str -   CopyId of the VSS snap.

            str -   The log line indicating the CopyId.

        Raises:
            Exception:
                If creation of the persistent VSS snap failed.
                We can disable this behavior by setting exit_on_vss_snap_failure to False.

        """

        # ENSURE SNAP CREATION DID NOT FAIL
        snap_failure_term = "Failed to create persistent volume snapshot for file extent eligible volumes"
        log_file = self.get_logs_for_job_from_file(job.job_id, "clBackup.log", snap_failure_term)
        if log_file is not None:
            for line in log_file.split("\r\n"):
                if line.find(snap_failure_term) != -1:
                    self.log.info(f"VSS snap creation failed indicated by below log line \n {line}.")
            if exit_on_vss_snap_failure:
                raise Exception("Persistent VSS snap creation failed.")

        # CHECK IF SNAP ID EXISTS
        copyid, copyid_line = None, None
        search_term = "CVSSClientShadow::GetShadowDeviceObjects() - SSID"
        log_file = self.get_logs_for_job_from_file(job.job_id, "clBackup.log", search_term)
        if log_file is not None:
            for line in log_file.split("\r\n"):
                re_search = re.search(r"CVSSClientShadow::GetShadowDeviceObjects\(\).*CopyId\[([\d\w-]+)\]", line)
                if re_search is not None:
                    copyid, copyid_line = str((re_search).groups()[0]), line

        if return_log_line:
            return copyid, copyid_line
        return copyid

    # EXTENT LEVEL BACKUP SPECIFIC FUNCTION
    def is_copyid_persistent(self, copyid):
        """Checks if given CopyId is persistent.

        Args:
            copyid      (str)   --  The CopyId.

        Returns:
            bool    -   True if the CopyId is persistent else False

        Raises:
            None

        """

        res = False
        self.log.info(f"Checking if CopyId {copyid} is persistent")
        cmd = "Get-WMIObject Win32_ShadowCopy | WHERE {{$_.ID -eq '{{{}}}'}} | FT -Property @{{e={{$_.Persistent}}}}"
        cmd_op = self.testcase.client_machine.execute_command(cmd.format(copyid)).formatted_output

        if cmd_op[0][0] == "True":
            self.log.info("CopyId is persistent")
            res = True
        else:
            self.log.info("CopyId is NOT persistent")
        return res

    def get_extent_backup_stream_count(self, job, log_dir=None):
        """Returns number of streams used by an extent level job from logs.

        Args:
            job     (object)    --  Instance of restore job.

            log_dir (str)       --  Path of the log directory.
                default:None

        Returns:

            int     -   Number of streams used by the backup job.

        Raises:
            None

        """
        if log_dir is None:
            # This will be ignored for now, and will be implemented with cross restore support
            log_dir = self._log_files_dir
        search_term = "CBackupBase::DoBackup"
        tids = set()
        log_lines = ""
        log_file = self.get_logs_for_job_from_file(job.job_id, "clBackup.log", search_term)
        ptrn = re.compile(r"(?P<pid>\d+)\s*(?P<tid>[\d\w]+)\s.*")
        for line in log_file.split("\r\n"):
            re_search = re.search(ptrn, line)
            if re_search is not None:
                tids.add(re_search.group("tid"))
                log_lines = "".join((log_lines, line, "\r\n"))

        if tids:
            self.log.info("Log lines indicating that job %s used multiple streams \n %s",
                          str(job.job_id), str(log_lines))
        return len(tids)

    def get_restore_stream_count(self, job, log_dir=None):
        """Returns number of streams used by a restore job from logs.

        Args:
            job     (object)    --  Instance of restore job.

            log_dir (str)       --  Path of the log directory.

        Returns:

            int     -   Number of streams used by the restore job.

        Raises:
            None

        """
        if log_dir is None:
            # This will be ignored for now, and will be implemented with cross restore support
            log_dir = self._log_files_dir
        search_term = "finishing worker thread"
        tids = set()
        log_lines = ""
        log_file = self.get_logs_for_job_from_file(job.job_id, "startClientRestore.log", search_term)

        for line in log_file.split("\r\n"):
            re_search = re.search(r"(?P<pid>\d+)\s*(?P<tid>[\d\w]+)\s.*", line)
            if re_search is not None:
                tids.add(re_search.group("tid"))
                log_lines = "".join((log_lines, line, "\r\n"))

        if len(tids) > 1:
            self.log.info("Log lines indicating that job %s used multiple streams \n %s",
                          str(job.job_id), str(log_lines))
        return len(tids)



    def get_failed_items_in_jr(self, return_only_paths=True):
        """Read entries from Failures.cvf and FailedFileRetryCollect.cvf if they exist.

            Args:

                return_only_paths   --  Extracts the path name from the entries. Simplifies comparison
                against the output of a "dir" command or a list of path names for verification purposes.

            Returns:

                dict    -   A dictionary containing entries from Failures.cvf and FailedFileRetryCollect.cvf.
                The names of the collect files are the keys and the entries in those files are the values.

            Raises:
                None

        """

        failures, ffr = "Failures.cvf",  "FailedFileRetryCollect.cvf"
        output = {failures:[], ffr:[]}

        failures_path = self.testcase.client_machine.os_sep.join((list(self.subclient_job_results_directory.values())[0], failures))
        ffr_path = self.testcase.client_machine.os_sep.join((list(self.subclient_job_results_directory.values())[0], ffr))

        cvf_ptrn = re.compile(r"[?*]{3}(?P<path_name>.*?)\|.*") if return_only_paths else None

        if self.testcase.client_machine.check_file_exists(failures_path):
            for entry in self.testcase.client_machine.read_file(failures_path).split("\r\n"):
                match = re.match(cvf_ptrn, entry)
                if match:
                    output[failures].append(match.group('path_name'))

        if self.testcase.client_machine.check_file_exists(ffr_path):
            for entry in self.testcase.client_machine.read_file(ffr_path).split("\r\n"):
                match = re.match(cvf_ptrn, entry)
                if match:
                    output[ffr].append(match.group('path_name'))

        return output

    def bmr_verify_vmware(self, esxservername, esxusername, esxpassword, vmname, mach_username, mach_password):
        """Returns the number of streams used by a restore job.

        Args:
            esxservername       (str)       --  Name of the ESX server.

            esxusername         (str)       --  Username of the ESX server

            esxpassword         (str)       --  Password of the ESX server.

            vmname              (str)       --  Name of the VM on which script is to be invoked.

            mach_username       (str)       --  username of the guest OS.

            mach_password       (str)       --  Password of the guest OS.


        Returns:

            None

        Raises:
            Exception:
                If the script returns anything other than true

        """
        script_arguments = {
            'esxservername': esxservername,
            'esxusername': esxusername,
            'esxpassword': esxpassword,
            'vmname': vmname,
            'mach_username': mach_username,
            'mach_password': mach_password
        }

        self.log.info("Invoking Powershell script")
        attempts = 1
        while attempts <= 5:
            self.log.info("Attempt number: %s", attempts)
            output = self.testcase.controller_machine.execute_script(BMR_VERIFY_VMWARE, script_arguments)
            self.log.info("Script output is : %s", output.formatted_output)
            if output.formatted_output.lower() == "true":
                self.log.info("The machine is up and running")
                break
            else:
                time.sleep(300)
                attempts = attempts+1

        if output.formatted_output.lower() != "true":
            raise Exception("The machine did not come up post restore")

    def bmr_verify_hyperv(self, vmname, mach_username, mach_password):
        """Returns the number of streams used by a restore job.
        Args:
            vmname              (str)       --  Name of the VM on which script is to be invoked.
            mach_username       (str)       --  username of the guest OS.
            mach_password       (str)       --  Password of the guest OS.
        Returns:
            None
        Raises:
            Exception:
                If the script returns anything other than true
        """
        script_arguments = {
            'vmname': vmname,
            'mach_username': mach_username,
            'mach_password': mach_password
        }

        self.log.info("Invoking Powershell script")
        attempts = 1
        while attempts <= 5:
            self.log.info("Attempt number: %s", attempts)
            output = self.testcase.hypervhost_machine.execute_script(BMR_VERIFY_HYPERV, script_arguments)
            self.log.info("Script output is : %s", output.formatted_output)
            if output.formatted_output.lower() == "true":
                self.log.info("The machine is up and running")
                break
            else:
                time.sleep(300)
                attempts = attempts+1

        if output.formatted_output.lower() != "true":
            raise Exception("The machine did not come up post restore")

    def get_no_of_qualified_objects_from_filescan(self, job):
        """Returns the number of objects identified by the given backup job from FileScan.log.

        Args:
            job (obj)   --  Instance of a Backup job.

        Returns:
            dict --  Returns the number of qualified files and folders.

        Raises:
            None

        """

        qualified_objects_count = {}
        log_file = self.get_logs_for_job_from_file(job.job_id, "FileScan.log", "Found")
        if log_file is not None:
            for line in log_file.split("\r\n"):
                sch = re.search(r"Found (?P<files>\d+) files and (?P<folders>\d+) folders \((?P<total>\d+) total items\) to back up", line)
                if sch is not None:
                    qualified_objects_count['files'] = sch.group('files')
                    qualified_objects_count['folders'] = sch.group('folders')
                    qualified_objects_count['total'] = sch.group('total')

        return qualified_objects_count

    def get_volume_guid(self, drive_letter):
        """Returns Db path for given volume.

            Args:
                drive_letter     (str)   --  Volume Letter without Colon
                                            (E for E: volume)

            Returns:
                str    -   guid Id for given drive letter on client machine
                None   -   If drive letter is not valid or not able to extract guid from output

            """
        command = f"Get-Volume -DriveLetter {drive_letter} | FT Path"
        output = self.testcase.client_machine.execute_command(command)
        result = re.search(r'\{.*\}', output.output)
        if not result:
            return None

        return result[0]
