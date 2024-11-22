# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
	__init__()             --  Initialize TestCase class

	  run()                  --  run function of this test case
	  dir_structure()        --  Generates the data
	  dir_structure_validation()  -- Validates the operations performed
	  cvc_cmd   -- generates the cvc cmd to run
	  validation() -- method which calls other methods for validation

"""
import re
from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper

class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental, for backup and CVC browse, find, restore
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
        Step2, For each of the allowed scan type
                do the following on the backupset
            Step2.1,  Create subclient for the scan type if it doesn't exist.
                Step2.2, Add full data for the current run.
                Step2.3, Run a full backup for the subclient
                            and verify it completes without failures.
                Step2.4, As user run browse
                Step2.5, Validate the files and directories based on permission are shown correctly
                Step2.6, As  user run find
                Step2.7, Validate the files and directories based on permission are shown correctly
                Step2.8, As user run restore
                Step2.9, Validate correct directories and files are restorable.
                Step2.10, Run incremental job
                Step2.11, Run Synthetic Full job
                Step 2.12, Run browse and validate the files/directories
                Step 2.13, Run find and validate the files/directories
                Step 2.14, Run restore and validate the files/directories
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance for CVC browse, " \
                    "find and restore"
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "UserName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.acls = None
        self.should_wait = None

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)
            test_path = self.test_path
            client_name = self.client.client_name
            user_name = self.tcinputs.get('UserName')
            slash_format = self.slash_format
            helper = self.helper

            machine = self.client_machine
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy
            dir_level = 2
            self.log.info("Setting global param "
                          "EnforceUnixUserPermissionsOnRestore")
            self.commcell.add_additional_setting("CommServDB.GxGlobalParam",
                                                 "EnforceUnixUserPermissionsOnRestore",
                                                 "INTEGER", "1")
            self.log.info("Step1, Create backupset for "
                          "this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            helper.create_backupset(backupset_name)

            self.log.info("Step2, Executing steps for all the allowed scan type")
            scan_type = ScanType.RECURSIVE
            self.log.info("**STARTING RUN FOR {0} SCAN**".format(str(scan_type.name)))

            self.log.info("Step2.1, Create subclient for the scan type {0} "
                          "if it doesnt exists".format(str(scan_type.name)))

            subclient_name = ("subclient_{0}_"
                              "{1}".format(str(self.id), str(scan_type.name)))
            subclient_content = []
            subclient_content.append(test_path
                                     + slash_format
                                     + subclient_name)
            tmp_path = (test_path + slash_format + 'cvauto_tmp'
                        + slash_format + subclient_name + slash_format)

            run_path = (subclient_content[0]
                        + slash_format
                        + str(self.runid))

            full_data_path = "{0}{1}full".format(run_path, slash_format)

            helper.create_subclient(name=subclient_name,
                                    storage_policy=storage_policy,
                                    content=subclient_content,
                                    scan_type=scan_type,
                                    catalog_acl=True)
            self.log.info("Step 2.2 Adding data under path: "
                          "{0}".format(full_data_path))
            # Data creation script expects the parent path to be present
            if machine.check_directory_exists(full_data_path):
                self.log.info("Data path exists. Using the same")
            else:
                self.log.info("Data Path doesnt exist. "
                              "Creating the parent Full "
                              "path.{0}".format(full_data_path))
                machine.create_directory(full_data_path)

            self.dir_structure(full_data_path, 0, 1, 1, dir_level, machine)

            self.log.info("Step2.3,  Run a full backup for the subclient "
                          "and verify it completes without failures.")
            helper.run_backup_verify(scan_type, "Full")[0]
            # Creating restore path and setting permission for others so
            # that user can restore the data
            restore_path = full_data_path + "/restore "
            change_perm = "mkdir " + restore_path + " | chmod 707 " + restore_path
            change_return = machine.execute(change_perm)
            if change_return != 0:
                tmp_path = "/tmp"
            else:
                tmp_path = restore_path
            self.log.info("Step2.4 Validate browse operation using cvc command")
            self.validation(full_data_path, 0, dir_level, machine, "browse",
                            backupset_name, subclient_name, client_name,
                            tmp_path, user_name)
            self.log.info("Step2.5 Validate find operation using cvc command")
            self.validation(full_data_path, 0, dir_level, machine, "find",
                            backupset_name, subclient_name, client_name,
                            tmp_path, user_name)
            self.log.info("Step2.6 Validate restore operation using cvc command")
            self.validation(full_data_path, 0, dir_level, machine, "restore",
                            backupset_name, subclient_name,
                            client_name, tmp_path, user_name)
            self.log.info("Step2.7 Run incremental job")

            helper.run_backup_verify(scan_type, "Incremental")[0]
            self.log.info("Step2.8 Run Synthetic Full job")
            helper.run_backup_verify(scan_type, "Synthetic_full")

            self.log.info("Step2.9 Validate browse operation using cvc command")
            self.validation(full_data_path, 0, dir_level, machine, "browse",
                            backupset_name, subclient_name, client_name,
                            tmp_path, user_name)

            self.log.info("Step2.10 Validate find operation using cvc command")
            self.validation(full_data_path, 0, dir_level, machine, "find",
                            backupset_name, subclient_name, client_name,
                            tmp_path, user_name)

            self.log.info("Step2.11 Validate restore operation using cvc command")
            self.validation(full_data_path, 0, dir_level, machine, "restore",
                            backupset_name, subclient_name,
                            client_name, tmp_path, user_name)
            self.log.info("Cleaning up the data path")
            machine.remove_directory(test_path)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: {0}'.format(str(excp)))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        self.log.info("Removing additional setting "
                      "EnforceUnixUserPermissionsOnRestore")
        self.commcell.delete_additional_setting("CommServDB.GxGlobalParam",
                                                "EnforceUnixUserPermissionsOnRestore")


    def dir_structure(self, root_dir, level, ancestor_r,
                      ancestor_x, dir_level, machine):
        """This method creates data as root and provides permissions
                like 700,701,704,705
                At each level 4 directories and 4 files are created
                root_dir: Base path under which test data has to be generated

                level: (int) curent level

                ancestor_r: (Str) Ancestor having Read permission

                ancestor_x: (Str) Ancestor having execute permission

                dir_level: (int) depth

                machine: machine Object
                """
        # List of permissions with which directories and files are generated

        lst_permission = [0, 1, 4, 5]
        file_name = "File"
        if level > dir_level:
            return 0
        dir_name = root_dir + "/Dir"
        for permission in lst_permission:
            tmp_permission = "70" + str(permission)
            dir_path = dir_name + "_" + str(level) + "_" + tmp_permission
            current_r = current_x = 0
            if permission == 1 or permission == 5:
                current_x = 1
            if permission == 4 or permission == 5:
                current_r = 1

            r_perm = current_r & ancestor_r
            x_perm = current_x & ancestor_x
            mkdir_cmd = "mkdir " + dir_path
            machine.execute(mkdir_cmd)
            chmod_cmd = "chmod " + tmp_permission + " " + dir_path
            machine.execute(chmod_cmd)

            for permission in lst_permission:
                tmp_permission = "70" + str(permission)
                final_file_name = file_name + "_" + tmp_permission
                final_file_name = dir_path + "/" + final_file_name

                if ancestor_x and current_r:
                    final_file_name += "_showInBrowse"
                else:
                    final_file_name += "_DontShowInBrowse"
                if ancestor_x and current_r and current_x:
                    final_file_name += "_showInFind"
                else:
                    final_file_name += "_DontShowInFind"
                touch_cmd = "touch " + final_file_name
                machine.execute(touch_cmd)
                chmod_cmd = "chmod " + tmp_permission + " " + final_file_name
                machine.execute(chmod_cmd)

            self.dir_structure(dir_path, level + 1, r_perm,
                               x_perm, dir_level, machine)
        return 0

    def dir_structure_validation(self, source_path, level, dir_level, ancestor_r,
                                 ancestor_x, machine, cmd, operation):
        """This method validates for

           browse, find and restore operations

           Ancestors having execute permission and browse path having

           Read permission should show in browse

           Ancestors having execute permission and browse path having

           Read and Execute should show for find

           Ancestors having execute permission and browse path having

           Read and Files having Read permission should be restorable.

        Args:
        Source path     : (Str)  path on which operation to be performed

        level           : (int) curent level

        ancestor_r       : (Str) Ancestor having Read permission

        ancestor_x       : (Str) Ancestor having execute permission

        dir_level        : (int) depth

        machine         : (Obj) machine

        cmd             : (Str) command to run from cvc

        Operation       : (Str) browse/find/restore

        """

        lst_permission = [0, 1, 4, 5]
        if level > dir_level:
            return 0
        dir_name = source_path + "/Dir"

        for permission in lst_permission:
            tmp_permission = "70" + str(permission)
            dir_path = dir_name + "_" + str(level) + "_" + tmp_permission

            current_r = current_x = 0
            if permission == 1 or permission == 5:
                current_x = 1
            if permission == 4 or permission == 5:
                current_r = 1

            r_perm = current_r & ancestor_r
            x_perm = current_x & ancestor_x
            if level != 0 and ancestor_x and current_r:
                command1 = cmd + dir_path
                self.log.info("CVC command run: {0}".format(command1))
                output_cvc = machine.execute(command1)
                self.log.info(output_cvc)

                command_list = []
                for list_iter in output_cvc.formatted_output:
                    command_list.append("".join(list_iter))
                command_output = "".join(command_list)
                self.log.info("CVC Command output: {0}".format(command_output))

                # Validate paths for find and browse
                if operation == "browse":
                    if ancestor_x and current_r:
                        if command_output.count("showInBrowse") != 4:
                            raise Exception("browse operation failed to "
                                            "show correct number of files")
                    else:
                        if command_output.count("DontShowInBrowse") > 0:
                            raise Exception("browse operation showed "
                                            "incorrect number of files")
                elif operation == "find":
                    if ancestor_x and current_r and current_x:
                        if command_output.count("showInFind") < 4:
                            raise Exception("Find operation failed to "
                                            "show correct number of files")
                    else:
                        if command_output.count("DontShowInFind") > 0:
                            raise Exception("Find operation showed incorrect "
                                            "files")
                else:
                    self.log.info("Restore:{0}".format(output_cvc.formatted_output))
                    # Get the job id from the submitted request
                    xml = []
                    for list_iter in output_cvc.formatted_output:
                        xml.append(" ".join(list_iter))
                    string_xml = "".join(xml)
                    self.log.info("%s", string_xml)
                    job_id_list = re.findall('jobIds val=\"(\d+)\"', string_xml)
                    self.log.info("job id list: %s", job_id_list)
                    job_id = job_id_list[0]
                    # Create job object
                    commcell_obj = self.commcell
                    job_controller_obj = commcell_obj.job_controller
                    job = job_controller_obj.get(job_id)
                    self.log.info("waiting for completion of %s", job.job_id)
                    # Expected paths to succeed
                    job_should_succeed = ancestor_x and current_r and current_x
                    self.log.info(job_should_succeed)
                    if job_should_succeed:
                        if not job.wait_for_completion():
                            raise Exception(
                                "Failed to run restore job {0} with error: {1}".format(
                                    job.job_id, job.delay_reason)
                            )
                        if job.status != 'Completed':
                            raise Exception(
                                "job: {0} is completed with errors, Reason: {1}".format(
                                    job.job_id, job.delay_reason)
                            )
                        self.log.info("Successfully finished restore Job :%s", job.job_id)

                    else:
                        # Negative cases where the files are not expected to be restored
                        run = True
                        while run:
                            # Job is expected to fail.
                            # Job will be automatically resumed by JobManager
                            # wait_for_completion wait till all the attempts are exhausted
                            # So, keep polling for job status every 30 seconds and once
                            # the job goes pending, kill the job
                            sleep(30)
                            if job.status == "Completed":
                                run = False
                                if job.num_of_files_transferred > 1:
                                    raise Exception("restore job {0} expected to fail but "
                                                    "completed successfully".format(job.job_id))
                            else:
                                if job.status == "Pending" or job.status == "Failed":
                                    job.kill(wait_for_job_to_kill=True)
                                    run = False

            self.dir_structure_validation(dir_path, level + 1, dir_level,
                                          r_perm, x_perm, machine, cmd, operation)
        return 0

    def cvc_cmd(self, user_name, operation, machine, backupset_name,
                subclient_name, client_name, dest_path):
        """   This method generated the cvc command for performing

                browse, find and restore operations

                Args:
                        user_name       : (Str) user to perform operation

                        operation       : (Str) browse/find/restore

                        machine         : (Obj) machine

                        backupset_name  : (Str) backup backupset

                        subclient_name  : (Str) backup subclient

                        client_name     : (Str) backup client

                        dest_path       : (Str)  path to which files to be restored
                returns:
                        command             : command to be run


                        """
        # Get the base path to run cvc commnds
        reg_value_dict = machine.get_registry_dict()
        if 'dBASEHOME' not in reg_value_dict:
            raise Exception('fail to get client machine base folder, ' +
                            'we need simpana product installed before ' +
                            'run this test case, please check setup ' +
                            'and re-run again')
        base_folder = reg_value_dict['dBASEHOME']
        self.log.info(base_folder)
        self.log.info("Login as {0}".format(user_name))
        command = "sudo -u " + user_name + " " + base_folder + "/cvc login"
        self.log.info(command)
        cmd = machine.execute(command)

        self.log.info("Login command:{0}".format(command))
        self.log.info("Login output: {0}".format(cmd.formatted_output))
        if cmd.exit_code != 0:
            self.log.info("Failed to login")
            raise Exception("Login failed. Please check logs {0}"
                            "".format(cmd.formatted_output))

        if operation == "browse":
            command = "sudo -u " + user_name + " " + base_folder + "/cvc browse -c "\
                      + client_name + " -bk " + backupset_name + \
                      " -sc " + subclient_name + " -p "

        elif operation == "find":
            command = "sudo -u " + user_name + " " + base_folder + "/cvc find -c " \
                      + client_name + " -bk " + backupset_name + \
                      " -sc " + subclient_name + " -f \"*\" " + " -path "

        elif operation == "restore":
            command = "sudo -u " + user_name + " " + base_folder + "/cvc restore -c " \
                      + client_name + " -bk " + backupset_name + \
                      " -sc " + subclient_name + " -dp "\
                      + dest_path + " -path "

        return command

    def validation(self, source_path, level, dir_level, machine, operation, backupset_name,
                   subclient_name, client_name, dest_path, user_name):
        """ This method calls the other functions to perform
                validation of the operations

                Args:
                         source_path: (Str) Source data path

                         level:  (int) Start of the validation level

                         dir_level: (int) depth

                         machine:  (obj) machine

                         operation: (Str) browse/find/restore

                         backupset_name: backed up backupset

                         subclient_name: backed up subclient

                         client_name: backed up client

                         dest_path: path where data to be restored

                         user_name: User to perform operations

                """

        cmd = self.cvc_cmd(user_name, operation, machine, backupset_name,
                           subclient_name, client_name, dest_path)

        self.dir_structure_validation(source_path, level, dir_level,
                                      1, 1, machine, cmd, operation)
