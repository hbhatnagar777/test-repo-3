# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Helper file for performing cvc operations

    CvcOps:

    get_cvc_base()              -- Get the cvc path

    login()                     -- Login to CVC session non-interactively method

    browse()                    -- validate browse operation

    find()                      -- validate find operation

    restore()                   -- validate restore operation

    data_creation()             -- Create test data as root with various permissions


"""

import re
from time import sleep
from AutomationUtils import logger
from AutomationUtils.machine import Machine


class Cvchelper():
    """ Helper class for CVC operations
    Initialize instance of cvcHelper class.
        Args:

                    ClientName  (str)       --  client on which cvc operations are performed

                    testcase    (object)     --  instance of the CVTestCase class

    """

    def __init__(self, client_name, commcell, client_obj):
        self.log = logger.get_log()
        self.cvc_machine_obj = Machine(
            client_name, commcell)
        self.client_obj = client_obj
        self.commcell_obj = commcell
        self._username = None

    @property
    def username(self):
        """Returns the Client display name"""
        return self._username

    @username.setter
    def username(self, username):
        """setter to set the display name of the client

        Args:
            username    (str)   -- Us

        """
        self._username = username

    def get_cvc_base(self):
        """
        Function to get the cvc path to run the CVC commands non interactively

        Args: None

        return:
            CVC path
        """
        # Get the path to run cvc commands non interactively
        base_folder = ("{0}/Base".format(self.client_obj.install_directory))
        return base_folder

    def login(self):
        """
        Function to login to CVC session non interactively

        Args:
            None

        """
        # Get the CVC path
        base_folder = self.get_cvc_base()
        self.log.info(base_folder)
        self.log.info("Login as {0}".format(self._username))
        command = ("sudo -u {0} {1}/cvc login".format(self._username, base_folder))
        self.log.info(command)
        cmd = self.cvc_machine_obj.execute(command)
        self.log.info("Login command:{0}".format(command))
        if cmd.exit_code != 0:
            self.log.info("Failed to login")
            raise Exception("Login failed. Please check logs {0}"
                            "".format(cmd.formatted_output))
        self.log.info("Login output: {0}".format(cmd.formatted_output))

    def browse(self, client_name, backupset_name,
               subclient_name, source_path, level, dir_level, ancestor_r, ancestor_x):
        """
        Funtion verifies browse operation

        Args:

            client_name: (str) Client on which cvc browse performed

            backupset_name: (str) source backupset name

            subclient_name: (str) source subclient name

            source_path: (str)  source path for restore

            dir_level: (int) depth

            level: (int) curent level

            ancestor_r: (Str) Ancestor having Read permission

            ancestor_x: (Str) Ancestor having execute permission

        """
        base_folder = self.get_cvc_base()
        cmd = ("sudo -u {0} {1}/cvc browse -c {2} -bk {3} -sc {4} -p ".format(self._username,
                                                                              base_folder, client_name,
                                                                              backupset_name, subclient_name))
        lst_permission = [0, 1, 4, 5]
        if level > dir_level:
            return 0
        dir_name = source_path + "/Dir"

        for permission in lst_permission:
            tmp_permission = ("70{0}".format(permission))
            dir_path = ("{0}_{1}_{2}".format(dir_name, level, tmp_permission))

            current_r = current_x = 0
            if permission == 1 or permission == 5:
                current_x = 1
            if permission == 4 or permission == 5:
                current_r = 1

            r_perm = current_r & ancestor_r
            x_perm = current_x & ancestor_x
            if level != 0 and ancestor_x and current_r:
                command1 = ("{0}{1}".format(cmd, dir_path))
                self.log.info("CVC command run: {0}".format(command1))
                output_cvc = self.cvc_machine_obj.execute(command1)
                self.log.info(output_cvc)

                command_list = []
                for list_iter in output_cvc.formatted_output:
                    command_list.append("".join(list_iter))
                command_output = "".join(command_list)
                self.log.info("CVC Command output: {0}".format(command_output))

                # Validate paths for find and browse
                if ancestor_x and current_r:
                    if command_output.count("showInBrowse") != 4:
                        raise Exception("browse operation failed to "
                                        "show correct number of files")
                    else:
                        if command_output.count("DontShowInBrowse") > 0:
                            raise Exception("browse operation showed "
                                            "incorrect number of files")
        self.browse(client_name, backupset_name, subclient_name,
                    dir_path, level + 1, dir_level, r_perm, x_perm)
        return 0

    def find(self, client_name, backupset_name, subclient_name,
             source_path, level, dir_level, ancestor_r,
             ancestor_x):
        """
        Funtion to create find command

        Args:

            client_name: (str) Client on which cvc browse performed

            backupset_name: (str) source backupset name

            subclient_name: (str) source subclient name

            source_path: (str)  source path for restore

            dir_level: (int) depth

            level: (int) curent level

            ancestor_r: (Str) Ancestor having Read permission

            ancestor_x: (Str) Ancestor having execute permission

        """
        base_folder = self.get_cvc_base()

        cmd = ("sudo -u {0} {1}/cvc find -c {2} -bk {3} -sc {4} -f \"*\""
               " -path  ".format(self._username, base_folder,
                                 client_name, backupset_name, subclient_name))
        lst_permission = [0, 1, 4, 5]
        if level > dir_level:
            return 0
        dir_name = source_path + "/Dir"

        for permission in lst_permission:
            tmp_permission = ("70{0}".format(permission))
            dir_path = ("{0}_{1}_{2}".format(dir_name, level, tmp_permission))
            current_r = current_x = 0
            if permission == 1 or permission == 5:
                current_x = 1
            if permission == 4 or permission == 5:
                current_r = 1

            r_perm = current_r & ancestor_r
            x_perm = current_x & ancestor_x
            if level != 0 and ancestor_x and current_r:
                command1 = ("{0}{1}".format(cmd, dir_path))
                self.log.info("CVC command run: {0}".format(command1))
                output_cvc = self.cvc_machine_obj.execute(command1)
                self.log.info(output_cvc)

                command_list = []
                for list_iter in output_cvc.formatted_output:
                    command_list.append("".join(list_iter))
                command_output = "".join(command_list)
                self.log.info("CVC Command output: {0}".format(command_output))

                if ancestor_x and current_r and current_x:
                    if command_output.count("showInFind") < 4:
                        raise Exception("Find operation failed to "
                                        "show correct number of files")
                    else:
                        if command_output.count("DontShowInFind") > 0:
                            raise Exception("Find operation showed incorrect "
                                            "files")
        self.find(client_name, backupset_name, subclient_name,
                  dir_path, level + 1, dir_level, r_perm, x_perm)
        return 0

    def restore(self, client_name, backupset_name, subclient_name, source_path,
                level, dir_level, ancestor_r,
                ancestor_x, oop=None
                ):
        """
        Function to verify restore operation

        Args:

            client_name: (str) Client on which cvc browse performed

            backupset_name: (str) source backupset name

            subclient_name: (str) source subclient name

            source_path: (str)  source path for restore

            dir_level: (int) depth

            level: (int) curent level

            ancestor_r: (Str) Ancestor having Read permission

            ancestor_x: (Str) Ancestor having execute permission

            oop: (str) out of place restore path
        """
        base_folder = self.get_cvc_base()

        if oop is None:
            command = ("sudo -u {0} {1}/cvc restore -c {2} -bk {3} "
                       "-sc {4} -path  ".format(self._username, base_folder,
                                                client_name, backupset_name,
                                                subclient_name))
        else:
            dest_path = oop
            command = ("sudo -u {0} {1}/cvc restore -c {2} -bk {3} -sc {4} "
                       "-dp {5} -path  ".format(self._username, base_folder, client_name,
                    backupset_name, subclient_name, dest_path))

        lst_permission = [0, 1, 4, 5]
        if level > dir_level:
            return 0
        dir_name = source_path + "/Dir"

        for permission in lst_permission:
            tmp_permission = ("70{0}".format(permission))
            dir_path = ("{0}_{1}_{2}".format(dir_name, level, tmp_permission))
            current_r = current_x = 0
            if permission == 1 or permission == 5:
                current_x = 1
            if permission == 4 or permission == 5:
                current_r = 1

            r_perm = current_r & ancestor_r
            x_perm = current_x & ancestor_x
            if level != 0 and ancestor_x and current_r:
                command1 = ("{0}{1}".format(command, dir_path))
                self.log.info("CVC command run: {0}".format(command1))
                output_cvc = self.cvc_machine_obj.execute(command1)
                self.log.info(output_cvc)

                command_list = []
                for list_iter in output_cvc.formatted_output:
                    command_list.append("".join(list_iter))
                command_output = "".join(command_list)
                self.log.info("CVC Command output: {0}".format(command_output))

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
                job_controller_obj = self.commcell_obj.job_controller
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
                        sleep(300)
                        if job.status == "Completed":
                            run = False
                            if job.num_of_files_transferred > 1:
                                raise Exception("restore job {0} expected to fail but "
                                                "completed successfully".format(job.job_id))
                        else:
                            if job.status == "Pending" or job.status == "Failed":
                                job.kill(wait_for_job_to_kill = True)
                                run = False

            self.restore(client_name, backupset_name, subclient_name,
                         dir_path, level + 1, dir_level,
                         r_perm, x_perm, oop)
        return 0

    def data_creation(self, root_dir, level, ancestor_r,
                      ancestor_x, dir_level):
        """This method creates data as root and provides permissions
                like 700,701,704,705
                At each level 4 directories and 4 files are created
                root_dir: Base path under which test data has to be generated

                level: (int) curent level

                ancestor_r: (Str) Ancestor having Read permission

                ancestor_x: (Str) Ancestor having execute permission

                dir_level: (int) depth

        """
        # List of permissions with which directories and files are generated

        lst_permission = [0, 1, 4, 5]
        file_name = "File"
        if level > dir_level:
            return 0
        dir_name = ("{0}/Dir".format(root_dir))
        for permission in lst_permission:
            tmp_permission = "70" + str(permission)
            dir_path = ("{0}_{1}_{2}".format(dir_name, level, tmp_permission))
            current_r = current_x = 0
            if permission == 1 or permission == 5:
                current_x = 1
            if permission == 4 or permission == 5:
                current_r = 1

            r_perm = current_r & ancestor_r
            x_perm = current_x & ancestor_x
            mkdir_cmd = ("mkdir {0}".format(dir_path))
            self.cvc_machine_obj.execute(mkdir_cmd)
            chmod_cmd = ("chmod {0} {1}".format(tmp_permission, dir_path))
            self.cvc_machine_obj.execute(chmod_cmd)

            for permission in lst_permission:
                tmp_permission = ("70{0}".format(permission))
                final_file_name = ("{0}_{1}".format(file_name,tmp_permission))
                final_file_name = ("{0}/{1}".format(dir_path, final_file_name))

                if ancestor_x and current_r:
                    final_file_name += "_showInBrowse"
                else:
                    final_file_name += "_DontShowInBrowse"
                if ancestor_x and current_r and current_x:
                    final_file_name += "_showInFind"
                else:
                    final_file_name += "_DontShowInFind"
                touch_cmd = "touch " + final_file_name
                self.cvc_machine_obj.execute(touch_cmd)
                chmod_cmd = "chmod " + tmp_permission + " " + final_file_name
                self.cvc_machine_obj.execute(chmod_cmd)

            self.data_creation(dir_path, level + 1, r_perm,
                               x_perm, dir_level)
        return 0
