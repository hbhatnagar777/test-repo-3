# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from AutomationUtils import constants, machine
from cvpysdk.client import Client
import re
from time import sleep


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of CVC VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA CVC Snap backup Browse, find and Restore operation'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION,
                                                          tcinputs={
                                                              "user": None}
                                                          )
        self.vm_name = None
        self.vm_obj = None
        self.vm_machine = None
        self.fbr_obj = None
        self.dir_level = 2
        self.full_data_path = ''

    def set_additional_keys(self):
        """
        Setting up additional keys on the CS, FREL and the backup vm/client
        """
        try:
            decorative_log("Setting up Additional Keys")
            # adding key on CS
            self.log.info("Setting up additional key on CS")
            self.commcell.add_additional_setting("CommServDB.GxGlobalParam",
                                                 "EnforceUnixUserPermissionsOnRestore",
                                                 "INTEGER", "1")
            # adding key on the client
            if len(self.tc_utils.sub_client_obj.hvobj.VMs) != 1:
                raise Exception("This testcase is just for one vm")
            self.vm_name = self.tc_utils.sub_client_obj.vm_list[0]
            self.log.info("Setting up additional key on client {}".format(self.vm_name))
            self.vm_obj = Client(self.commcell, self.vm_name)
            self.vm_obj.add_additional_setting('CommvaultSDKForPython', 'nAgentType', 'Integer', "2")
            self.vm_machine = machine.Machine(self.vm_name, self.commcell)

            # adding key on FREL
            fbr_ma = self.tc_utils.sub_client_obj.auto_vsainstance.fbr_ma
            self.log.info("Setting up additional key on FREL {}".format(fbr_ma))
            self.fbr_obj = Client(self.commcell, fbr_ma)
            self.fbr_obj.add_additional_setting('FileSystemAgent', 'nCollectSIDInfoOnUnix', 'Boolean', "1")
            decorative_log("Additional Keys Set up complete")
        except Exception as exp:
            self.log.exception("Error in setting up reg key:{}".format(exp))
            raise Exception("Error in setting up reg key:{}".format(exp))

    def test_data_generation(self):
        """
        Generates the testdata for the testcase

        """
        try:
            decorative_log("testdata generation")
            test_path = '/testcase_cvc'
            subclient_content = self.vm_machine.join_path(test_path, self.tcinputs['SubclientName'])
            if self.vm_machine.check_directory_exists(subclient_content):
                self.vm_machine.remove_directory(subclient_content)
            run_path = self.vm_machine.join_path(subclient_content, str(self.tcTID))

            self.full_data_path = self.vm_machine.join_path(run_path, 'Full')
            self.vm_machine.create_directory(self.full_data_path)
            self.dir_structure(self.full_data_path, 0, 1, 1, self.dir_level)
        except Exception as exp:
            self.log.exception("Error in testdata generation:{}".format(exp))
            raise Exception("Error in testdata generation:{}".format(exp))

    def testcase_validations(self, operation, copy_precedence=1):
        """
        Runs the operation and the validations
        Args:

            operation               (string):   Operation type

            copy_precedence         (integer):  Copy precedence for the operation

        """
        try:
            decorative_log(f'{operation} operation and validation with copy precedence {copy_precedence}')
            user_name = self.tcinputs['user']
            backupset_name = self.tcinputs['BackupsetName']
            restore_path = self.full_data_path + "/restore "
            change_perm = "mkdir " + restore_path + " | chmod 707 " + restore_path
            change_return = self.vm_machine.execute(change_perm)
            if change_return != 0:
                tmp_path = "/tmp"
            else:
                tmp_path = restore_path
            self.validation(self.full_data_path, 0, self.dir_level, operation,
                            tmp_path, user_name, self.vm_name, backupset_name, copy_precedence)
        except Exception as exp:
            self.log.exception("Error in testcase validation:{}".format(exp))
            raise Exception("Error in testcase validation:{}".format(exp))

    def dir_structure(self, root_dir, level, ancestor_r,
                      ancestor_x, dir_level):
        """This method creates data as root and provides permissions
                like 700,701,704,705
                At each level 4 directories and 4 files are created
            Args:
                root_dir        (string):   Base path under which test data has to be generated

                level           (integer):  current level

                ancestor_r      (String):   Ancestor having Read permission

                ancestor_x      (String):   Ancestor having execute permission

                dir_level       (integer):  depth
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
            self.vm_machine.execute(mkdir_cmd)
            chmod_cmd = "chmod " + tmp_permission + " " + dir_path
            self.vm_machine.execute(chmod_cmd)

            for permission2 in lst_permission:
                tmp_permission = "70" + str(permission2)
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
                self.vm_machine.execute(touch_cmd)
                chmod_cmd = "chmod " + tmp_permission + " " + final_file_name
                self.vm_machine.execute(chmod_cmd)

            self.dir_structure(dir_path, level + 1, r_perm,
                               x_perm, dir_level)
        return 0

    def dir_structure_validation(self, source_path, level, dir_level, ancestor_r,
                                 ancestor_x, cmd, operation):
        """This method validates for

           browse, find and restore operations

           Ancestors having execute permission and browse path having

           Read permission should show in browse

           Ancestors having execute permission and browse path having

           Read and Execute should show for find

           Ancestors having execute permission and browse path having

           Read and Files having Read permission should be able to restore.

        Args:
            source_path     (String):   path on which operation to be performed

            level           (integer):  current level

            ancestor_r      (String):   Ancestor having Read permission

            ancestor_x      (String):   Ancestor having execute permission

            dir_level       (integer):  depth

            cmd             (String):   command to run from cvc

            operation       (String):   browse/find/restore

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
                output_cvc = self.vm_machine.execute(command1)
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
                                _tmp = command1.split()
                                _dest_path = self.vm_machine.join_path(_tmp[-3], _tmp[-1].split("/")[-1])
                                if self.vm_machine.number_of_items_in_folder(_dest_path) > 1:
                                    raise Exception("restore job {0} expected to restore 0 files "
                                                    "but it restored the files successfully".format(job.job_id))
                            else:
                                if job.status == "Pending" or job.status == "Failed":
                                    job.kill(wait_for_job_to_kill=True)
                                    run = False

            self.dir_structure_validation(dir_path, level + 1, dir_level,
                                          r_perm, x_perm, cmd, operation)
        return 0

    def cvc_cmd(self, user_name, operation, backupset_name,
                subclient_name, client_name, dest_path, copy_precedence):
        """   This method generated the cvc command for performing browse, find and restore operations

            Args:
                user_name       (string):   user to perform operation

                operation       (string):   browse/find/restore

                backupset_name  (string):   backup backupset name

                subclient_name  (string):   backup subclient name

                client_name     (string):   backup client name

                dest_path       (string):   path to which files to be restored

                copy_precedence (Integer):  copy precedence
            Returns:
                command             : command to be run

        """
        # Get the base path to run cvc commnds
        try:
            reg_value_dict = self.vm_machine.get_registry_dict()
            if 'dBASEHOME' not in reg_value_dict:
                raise Exception('fail to get client machine_ base folder, ' +
                                'we need simpana product installed before ' +
                                'run this test case, please check setup ' +
                                'and re-run again')
            base_folder = reg_value_dict['dBASEHOME']
            self.log.info(base_folder)
            self.log.info("Login as {0}".format(user_name))
            command = "sudo -u " + user_name + " " + base_folder + "/cvc login"
            self.log.info(command)
            cmd = self.vm_machine.execute(command)

            self.log.info("Login command:{0}".format(command))
            self.log.info("Login output: {0}".format(cmd.formatted_output))
            if cmd.exit_code != 0:
                self.log.info("Failed to login")
                raise Exception("Login failed. Please check logs {0}"
                                "".format(cmd.formatted_output))

            if operation == "browse":
                command = f'sudo -u {user_name} {base_folder}/cvc browse -c {client_name} ' \
                          f'-bk {backupset_name} -sc {subclient_name} -p '

            elif operation == "find":
                command = f'sudo -u {user_name} {base_folder}/cvc find -c {client_name} ' \
                          f'-bk {backupset_name} -sc {subclient_name} -f "*" -path '

            elif operation == "restore":
                command = f'sudo -u {user_name} {base_folder}/cvc restore -c {client_name} ' \
                          f'-bk {backupset_name} -sc {subclient_name} -dp {dest_path} -path '

            if copy_precedence != 0:
                split_command = command.split('-')
                split_command.insert(-1, f'cp{copy_precedence} ')
                command = '-'.join(split_command)

            return command
        except Exception as exp:
            self.log.exception('Exception during setting up cvc command: {}'.format(exp))
            raise Exception('Exception during setting up cvc command: {}'.format(exp))

    def validation(self, source_path, level, dir_level, operation, dest_path, user_name, client_name, backupset_name,
                   copy_precedence=0, subclient_name='default'):
        """ This method calls the other functions to perform
                validation of the operations

            Args:
                 source_path        (string):   Source data path

                 level              (integer):  Start of the validation level

                 dir_level          (integer):  depth

                 operation          (String):   browse/find/restore

                 dest_path          (string):   path where data to be restored

                 user_name          (string):   User to perform operations

                 client_name        (string):   backed up client

                 backupset_name     (string):   backed up backupset name

                 copy_precedence    (integer):  Copy precedence for the validation

                 subclient_name     (string): backed up subclient name

                """

        cmd = self.cvc_cmd(user_name, operation, backupset_name,
                           subclient_name, client_name, dest_path, copy_precedence)

        self.dir_structure_validation(source_path, level, dir_level,
                                      1, 1, cmd, operation)

    def run_backup(self):
        """
        Runs backup job

        """
        try:
            decorative_log('Running snap backup and backup copy')
            _backup_jobs = self.tc_utils.sub_client_obj.subclient.backup(self,
                                                                         advanced_options={
                                                                             'create_backup_copy_immediately': True,
                                                                             'backup_copy_type': 'USING_LATEST_CYLE'})
            if not (isinstance(_backup_jobs, list)):
                _backup_jobs = [_backup_jobs]
            for _backup_job in _backup_jobs:
                backup_job = _backup_job
            self.log.info("Submitted '{0}' backup Job : {1}".format('Full', backup_job.job_id))
            if not _backup_job.wait_for_completion():
                raise Exception("Failed to run backup with error: {0}"
                                .format(_backup_job.delay_reason))
            if _backup_job.status.lower() != 'completed':
                raise Exception("Job {} did not complete successfully. Error: {}"
                                .format(_backup_job.job_id, _backup_job.delay_reason))
            self.log.info("Backup Job {0} completed successfully".format(_backup_job.job_id))
            retry = 0
            common_utils = CommonUtils(self.tc_utils.sub_client_obj.auto_commcell.commcell)
            while retry < 5:
                try:
                    sleep(10)
                    backupcopy_job_id = common_utils.get_backup_copy_job_id(backup_job.job_id)
                    commcell_obj = self.commcell
                    job_controller_obj = commcell_obj.job_controller
                    backupcopy_job = job_controller_obj.get(backupcopy_job_id)
                    self.log.info("Backup Copy Job ID : {0}".format(backupcopy_job_id))
                    break
                except Exception:
                    sleep(10)
                    retry = retry + 1
            if not backupcopy_job.wait_for_completion():
                raise Exception("Failed to run backup copy job with error:{0} "
                                .format(backupcopy_job.details['jobDetail']['clientStatusInfo']
                                        ['vmStatus'][0]['FailureReason']))
            if backupcopy_job.status.lower() != 'completed':
                raise Exception("Job {} did not complete successfully. Error: {}"
                                .format(backupcopy_job.job_id, backupcopy_job.delay_reason))
        except Exception as exp:
            self.log.exception('Exception during Backup job due to: {}'.format(exp))
            raise Exception('Exception during Backup job due to: {}'.format(exp))

    def validate_file_indexing_job(self):
        """
        Validates the file indexing job has been run
        """
        try:
            decorative_log('Validating File indexing job')
            file_indexing_job_id = self.tc_utils.sub_client_obj.get_in_line_file_indexing_job()
            self.log.info("Validating File indexing job status")
            self.tc_utils.sub_client_obj.check_status_file_indexing(file_indexing_job_id)
        except Exception as exp:
            self.log.exception('Exception during file indexing job due to: {}'.format(exp))
            raise Exception('Exception during file indexing job due to: {}'.format(exp))

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            if self.tc_utils.sub_client_obj.subclient.properties.get('indexingInfo', {}).get('indexingStatus') != 1:
                raise Exception("this testcase needs file indexing to be enabled")
            self.set_additional_keys()
            self.test_data_generation()
            self.run_backup()
            self.validate_file_indexing_job()
            self.testcase_validations('browse')
            self.testcase_validations('restore')
            self.log.info("Waiting 12 minutes for the snaps to unmount")
            sleep(1200)
            self.testcase_validations('browse', 2)
            self.testcase_validations('find', 2)
            self.testcase_validations('restore', 2)
            decorative_log("Testcase was successful")

        except Exception as exp:
            self.log.exception("Testcase failed for reason:{}".format(exp))
            self.ind_status = False
            self.failure_msg += exp

        finally:
            try:
                decorative_log('Removing additioanl keys')
                self.commcell.delete_additional_setting("CommServDB.GxGlobalParam",
                                                        "EnforceUnixUserPermissionsOnRestore")
                self.vm_obj.delete_additional_setting('CommvaultSDKForPython', 'nAgentType')
                self.fbr_obj.delete_additional_setting('FileSystemAgent', 'nCollectSIDInfoOnUnix')
            except Exception:
                self.log.warning("Additional key deletion was not successful")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
