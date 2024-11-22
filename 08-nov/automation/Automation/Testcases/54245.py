# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  Initialize TestCase class.

    setup()     --  Initializes pre-requisites for this test case.

    run()       --  Executes the test case steps.

    teardown()  --  Performs final clean up after test case execution.

"""

import re
from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.winfshelper import WinFSHelper


class TestCase(CVTestCase):
    """Class for executing

    File System Extent Level Restore - Restore Restartability on Windows
    This test case will verify basic restartability cases for extent level restores on Windows.
    This test case does the following.

    01. Enable feature by setting bEnableFileExtentBackup (DWORD,1) under FileSystemAgent on client.
    02. Lower threshold by setting mszFileExtentSlabs (REG_MULTI_SZ,101-1024=100) under FileSystemAgent on client.
    03. Create a new backupset.

    SCENARIO 1 BEGINS
    4.01. Create a new subclient.
    4.02. Create a few files with Read Only, Hidden attributes set for extent level backup.
    4.03. Run a full backup and let it complete.
    4.04. Restore the data using multiple streams out of place and verify.

    4.05. Restore the data using multiple streams out of place and verify.
          Suspend when the restore is in progress at least twice.
          Verify that the files were restored correctly and the statistics are correct.

    4.06. Restore the data using multiple streams out of place and verify.
          Kill the restore process clRestore.exe when the restore is in progress at least twice.
          Verify that the files were restored correctly and the statistics are correct.

    4.07. Creating one very large file.

    4.08. Run an Incremental backup and let it complete.

    4.09. Restore the large file using multiple streams out of place and verify.
          Suspend restore twice, verify metadata, checksum and stats match up with backed up data.

    4.10. Restore the large file using multiple streams out of place and verify.
          Kill clRestore twice, verify metadata, checksum and stats match up with backed up data.
    SCENARIO 1 ENDS

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Extent Level Restore - Restore Restartability on Windows"
        self.show_to_user = True
        self.tcinputs = {"TestPath": None, "StoragePolicyName": None}
        self.helper = None
        self.storage_policy = None
        self.slash_format = None
        self.test_path = None
        self.runid = None
        self.id = None
        self.client_machine = None
        self.bset_name = None
        self.sc_name = None
        self.content = None
        self.run_path = None
        self.num_files = None
        self.file_sizes = {}
        self.tmp_path = None
        self.fsa = None
        self.enable = None
        self.slab = None
        self.slab_val = None
        self.threshold = None
        self.log_line = None
        self.current_attmept = None
        self.cleanup_run = None
        self.RETAIN_DAYS = None
        self.common_args = None
        self.data_args = None
        self.large_file = None
        self.rst_args = None
        self.wait_interval = None
        self.no_of_streams = None
        self.max_attempts = None
        self.attr_path = None
        self.reg_path = None
        self.large_path = None
        self.small_path = None
        self.data_path_leaf = None
        self.fclRestoreCount = None
        self.killedPids = None

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.helper = WinFSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.bset_name = '_'.join(("backupset", str(self.id)))
        self.runid = str(self.runid)

        self.num_files = int(self.tcinputs.get("NumFiles", 2))
        self.file_sizes['regular'] = int(self.tcinputs.get("FileSizeInKB", 1048576))
        self.file_sizes['small'] = int(self.tcinputs.get("SmallFileSizeInKB", 102400))
        self.file_sizes['large'] = int(self.tcinputs.get("LargeFileSizeInKB", 10485760))

        self.no_of_streams = int(self.tcinputs.get("NumStreams", 2))
        self.wait_interval = int(self.tcinputs.get("WaitInterval", 5))
        self.max_attempts = 3
        self.log_line = ""
        self.fclRestoreCount = 0
        self.killedPids = set()

        self.fsa = "FileSystemAgent"
        self.enable = "bEnableFileExtentBackup"
        self.slab = "mszFileExtentSlabs"
        self.slab_val = str(self.tcinputs.get("Slab", "101-10240=100"))
        self.threshold = int(self.slab_val.split("-", maxsplit=1)[0]) * 1048576

        self.sc_name = '_'.join(("subclient", str(self.id)))
        self.content = [self.slash_format.join((self.test_path, self.sc_name))]
        self.run_path = self.slash_format.join((self.content[0], self.runid))

        self.attr_path = self.slash_format.join((self.run_path, "extent_files", "attr_files"))
        self.reg_path = self.slash_format.join((self.run_path, "extent_files", "regular_files"))
        self.large_path = self.slash_format.join((self.run_path, "extent_files", "large_files"))
        self.small_path = self.slash_format.join((self.run_path, "non_extent_files", "small_files"))
        self.tmp_path = self.slash_format.join((self.test_path, "cvauto_tmp", self.sc_name, self.runid))

        self.common_args = {'name': self.sc_name, 'content': self.content, 'storage_policy': self.storage_policy}
        self.data_args = {'dirs': 0, 'files': self.num_files}
        self.large_file = {'file_path': self.large_path, 'file_size': self.file_sizes['large'], 'dirs': 0, 'files': 1}

        # USED BY self.helper.restore_out_of_place
        self.rst_args = {'paths': [self.run_path], 'destination_path': self.tmp_path, 'no_of_streams': self.no_of_streams, 'wait_to_complete': False}

    def interrupt_restore(self, rst, interrupt_type, run_path=None, data_path_leaf=""):
        """
        Interrupts the restore by either killing it or suspending it.
        Whole point of this method was to reduce the number of lines in the test case.

        Args:
            rst             (obj)   --  Job object for the restore job.

            interrupt_type  (str)   --  Scenario number.

            run_path        (str)   --  Optionally provide run path to compare metadata and checksum against.

            data_path_leaf  (str)   --  The data path leaf, to help during comparison of metadata and checksums.
        Returns:
            None

        Raises:
            None

        """

        def _kill(self, atmpt, rst, continue_running_tc):

            self.log.info(f"clRestore.exe will be killed after {self.wait_interval} seconds.")
            sleep(self.wait_interval)

            pid_lines = self.helper.get_logs_for_job_from_file(rst.job_id, "clRestore.log", clrestore_search_term).split("\r\n")

            self.fclRestoreCount = len(pid_lines)

            pid_list = []

            for s in pid_lines:
                pid = re.search(r"(?P<pid>\d+)?.*", s).group(1)

                # Do not try to kill PID if it was killed in prev attempt
                if pid and not pid in self.killedPids:
                    pid_list.append(pid)
                    self.log.info(f"PID Added {pid}")
            
            killcount = 0
            pid_list.reverse()

            for pid in pid_list:
                self.log.info(f"Attempting to kill {pid}")
                output = self.client_machine.kill_process(process_id=str(pid))

                if str(output.output):
                    #This is not an issue as long as killcount doesn't end up being 0
                    self.log.info(f"Attempt to kill PID {pid} gave output {output.output} ") 
                    self.log.info(f"Could not kill {pid}")
                else:
                    self.killedPids.add(pid)
                    self.log.info(f"Successfully killed {pid}")
                    killcount += 1
            
            # Indicates that no instance of clRestore was killed
            if killcount == 0:
                self.log.info(f"Unable to kill any instances of clRestore. Couldn't reach maximum number of attempts, which was set at {self.max_attempts}.")
                self.log.info(f"STATUS OF job = {rst.status.upper()}")
                continue_running_tc = False
                self.log.info(f" continue_running_tc set = {continue_running_tc}")
            else:
                self.log.info(f"Waiting for {self.wait_interval} seconds before resuming the restore")
                sleep(self.wait_interval)
                self.log.info(f"STATUS OF JOB IS: {rst.status.upper()}, now resuming the job")
                atmpt += 1
                rst.resume()
            return atmpt, continue_running_tc

        def _suspend(self, atmpt, rst, continue_running_tc):
            self.log.info(f"Restore will be suspended after {self.wait_interval} seconds.")
            sleep(self.wait_interval)
            try:
                self.fclRestoreCount = len(self.helper.get_logs_for_job_from_file(rst.job_id, "clRestore.log", clrestore_search_term).split("\r\n"))
                rst.pause(wait_for_job_to_pause=True)
                self.log.info(f"STATUS OF JOB IS: {rst.status.upper()}")
            except:
                if "COMPLETED" in rst.status.upper():
                    continue_running_tc = False
                    return atmpt, continue_running_tc
            atmpt += 1
            rst.resume()
            return atmpt, continue_running_tc

        run_path = self.run_path if not run_path else run_path
        continue_running_tc = True
        atmpt = 1

        if interrupt_type == "suspend":
            interrupt = _suspend
        elif interrupt_type == "kill":
            interrupt = _kill

        # STARTING THE INTERRUPT PROCESS
        self.log.info("STARTING THE INTERRUPT PROCESS")
        while atmpt < self.max_attempts:
            while True:
                # WAIT TILL RESTORE PHASE BEGINS AND ITS STATUS IS RUNNING
                self.log.info("WAIT TILL RESTORE PHASE BEGINS AND ITS STATUS IS RUNNING")
                if "COMPLETED" in rst.status.upper() or atmpt == self.max_attempts:
                    atmpt = 999
                    continue_running_tc = False
                    break
                elif rst.status.upper() == "RUNNING":
                    self.log.info("JOB IS NOW RUNNING PROCEEDING FURTHER")
                    break

            # GET THE PROCESS ID FOR CURRENT ATTEMPT OF clRestore.
            self.log.info("VERIFY THE CURRENT ATTEMPT from StartClientRestore.log.")
            search_term = f"-jt {rst.job_id}:2:{atmpt}"
            while True and continue_running_tc:
                log_line = self.helper.get_logs_for_job_from_file(rst.job_id, "StartClientRestore.log", search_term)
                if log_line:
                    self.log.info(f"Current attempt of the restore job within StartClientRestore.log is indicated by {log_line}")
                    break
                elif "COMPLETED" in rst.status.upper() or atmpt == self.max_attempts:
                    atmpt = 999
                    continue_running_tc = False
                    break
            
            # Search Term within clRestore.log to get attempt info
            clrestore_search_term = "FclRestorePrivate::ParseExtendedRestoreOption"
            while True and continue_running_tc:
                log_lines = self.helper.get_logs_for_job_from_file(rst.job_id, "clRestore.log", clrestore_search_term)
                if log_lines and len(log_lines.split("\r\n")) > self.fclRestoreCount+1:
                    log_lines_list = log_lines.split("\r\n")
                    pid = re.search(r"(?P<pid>\d+)?.*", log_lines_list[self.fclRestoreCount ]).group(1)
                    break
                elif "COMPLETED" in rst.status.upper() or atmpt == self.max_attempts:
                    atmpt = 999
                    continue_running_tc = False
                    break

            # WAIT UNTIL AFILE IS OPENED IN THE CURRENT ATTEMPT
            self.log.info("WAIT UNTIL AFILE OPENED IN CURRENT ATTEMPT")
            search_term = f"CVArchive::ReadBuffer() - PL_FS_OPEN_AFILE"
            quit_flag = 0
            while True and continue_running_tc:
                log_lines = self.helper.get_logs_for_job_from_file(rst.job_id, "clRestore.log", search_term)
                if log_lines:
                    for log_line in log_lines.split("\r\n"):
                        if log_line.find(pid) != -1:
                            self.log.info(f"Archive file Open In Current Attempt is {log_line}")
                            quit_flag = 1
                            break
                elif "COMPLETED" in rst.status.upper() or atmpt == self.max_attempts:
                    atmpt = 999
                    continue_running_tc = False
                    break
                if quit_flag == 1:
                    break

            if continue_running_tc:
                self.log.info("INTERRUPTING THE JOB")
                atmpt, continue_running_tc = interrupt(self, atmpt, rst, continue_running_tc)
                self.log.info(f"atmpt = {atmpt} continue_running_tc = {continue_running_tc}")
                if atmpt == self.max_attempts or not continue_running_tc:
                    break

        self.fclRestoreCount = 0
        if continue_running_tc:
            rst.resume()
        if not "COMPLETED" in rst.status.upper():
            rst.wait_for_completion()

        self.log.info(f"Comparing [{run_path}] with [{self.slash_format.join((self.tmp_path, data_path_leaf))}]")
        # META DATA COMPARISON
        res, diff_op = self.client_machine.compare_meta_data(run_path, self.slash_format.join((self.tmp_path, data_path_leaf)))
        if res:
            self.log.info("Meta data comparison successful")
        else:
            self.log.error("Meta data comparison failed")
            self.log.info(f"Diff output: \n{diff_op}")

        # CHECKSUM COMPARISON
        res, diff_op = self.client_machine.compare_checksum(run_path, self.slash_format.join((self.tmp_path, data_path_leaf)))
        if res:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info(f"Diff output: \n{diff_op}")

    def run(self):
        """Main function for test case execution"""
        try:
            machine = self.client_machine

            self.log.info(self.__doc__)

            self.log.info(f"01. Enable feature by setting {self.enable} under {self.fsa} on client.\n")
            machine.create_registry(self.fsa, self.enable, 1, "DWord")

            self.log.info(f"02. Lowering threshold by setting {self.slab} under {self.fsa} on client.\n")
            machine.create_registry(self.fsa, self.slab, self.slab_val, "MultiString")

            self.log.info("03. Create a new backupset")
            self.helper.create_backupset(self.bset_name)

            # *****************
            # SCENARIO 1 BEGINS
            # *****************
            self.log.info("*****************")
            self.log.info("SCENARIO 1 BEGINS")

            self.log.info("4.01. Create a new subclient.\n")
            self.helper.create_subclient(**self.common_args)

            self.log.info("4.02. Create large files with attributes, large files without attributes and small files.\n")
            machine.generate_test_data(file_path=self.attr_path, file_size=self.file_sizes['regular'], attribute_files='H', **self.data_args)
            machine.generate_test_data(file_path=self.attr_path, file_size=self.file_sizes['regular'], attribute_files='R', **self.data_args)
            machine.generate_test_data(file_path=self.reg_path, file_size=self.file_sizes['regular'], **self.data_args)
            machine.generate_test_data(file_path=self.small_path, file_size=self.file_sizes['small'], **self.data_args)

            self.log.info("4.03. Run a Full backup and let it complete.\n")
            full_bkp = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("4.04. Restore the data using multiple streams out of place and verify.\n")
            self.helper.run_restore_verify(self.slash_format, self.run_path, self.tmp_path, self.runid, full_bkp)

            self.log.info("4.05. Restore the data using multiple streams out of place and verify.")
            self.log.info("Suspend restore twice, verify metadata, checksum and stats match up with backed up data.\n")
            rst = self.helper.restore_out_of_place(**self.rst_args)
            self.interrupt_restore(rst, "suspend", data_path_leaf=self.runid)

            self.log.info("4.06. Restore the data using multiple streams out of place and verify.")
            self.log.info("Kill clRestore twice, verify metadata, checksum and stats match up with backed up data.\n")
            rst = self.helper.restore_out_of_place(**self.rst_args)
            self.interrupt_restore(rst, "kill", data_path_leaf=self.runid)

            self.log.info("4.07. Creating one very large file.\n")
            machine.generate_test_data(**self.large_file)

            self.log.info("4.08. Run an Incremental backup and let it complete.\n")
            inc = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("4.09. Restore the large file using multiple streams out of place and verify.")
            self.log.info("Suspend restore twice, verify metadata, checksum and stats match up with backed up data.\n")
            self.rst_args['paths'] = [self.large_path]
            rst = self.helper.restore_out_of_place(from_time=inc.start_time, to_time=inc.end_time, **self.rst_args)
            self.interrupt_restore(rst, "suspend", run_path=self.large_path, data_path_leaf="large_files")

            self.log.info("4.10. Restore the large file using multiple streams out of place and verify.")
            self.log.info("Kill clRestore twice, verify metadata, checksum and stats match up with backed up data.\n")
            rst = self.helper.restore_out_of_place(from_time=inc.start_time, to_time=inc.end_time, **self.rst_args)
            self.interrupt_restore(rst, "kill", run_path=self.large_path, data_path_leaf="large_files")

            self.log.info("END OF SCENARIO 1")
            self.log.info("*****************")
            # ***************
            # SCENARIO 1 ENDS
            # ***************

        except Exception as excp:
            error_message = f"Failed with error: {str(excp)}"
            self.log.error(error_message)
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        if self.cleanup_run:
            self.client_machine.remove_directory(self.tmp_path)
            self.instance.backupsets.delete(self.bset_name)
            if self.client_machine.os_info == "WINDOWS":
                remove_msg = f"Removing registry entries {self.enable} and {self.slab} under {self.fsa}"
                self.log.info(remove_msg)
                self.client_machine.remove_registry(self.fsa, self.enable)
                self.client_machine.remove_registry(self.fsa, self.slab)
