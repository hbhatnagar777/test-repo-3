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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils, OptionsHelper
from AutomationUtils import constants, machine
import re
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of FBR MA cleanup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA VMWARE FBR cleanup test'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.cvods_pid = None
        self.mount_ids = []
        self.fbr_ma = None
        self.fbr_obj = None

    def pre_requisite(self):
        """
        Checking the prerequisite before running the testcase

        """
        self.fbr_ma = self.tc_utils.sub_client_obj.auto_vsainstance.fbr_ma
        self.fbr_obj = machine.Machine(self.fbr_ma, self.tc_utils.sub_client_obj.auto_commcell.commcell)
        if len(self.tc_utils.sub_client_obj.hvobj.VMs) == 2:
            for vm in self.tc_utils.sub_client_obj.hvobj.VMs:
                if self.tc_utils.sub_client_obj.hvobj.VMs[vm].guest_os.lower() != 'windows':
                    continue
                self.ind_status = False
                self.failure_msg += '<br> This testcase requires all vm to be unix <br>'
                raise Exception("This testcase requires all vm to be unix")
        else:
            self.ind_status = False
            self.failure_msg += '<br> This testcase works with 2 vms <br>'
            raise Exception("This testcase works with 2 vms")

    def check_output(self, output_, log_):
        if output_.exit_code != 0:
            self.ind_status = False
            raise Exception("{}: {}".format(log_, self.fbr_ma))

    def killing_cvods(self):
        """
        Killing the cvods on the FBR MA

        """
        try:
            decorative_log(f"Trying to kill CVODS on {self.fbr_ma}")
            command = "ss -tnlp | grep -i 'cvods'"
            output = self.fbr_obj.execute_command(command)
            self.check_output(output, "CVODS is not running in the FBR")
            self.cvods_pid = int(re.split("pid=", (re.findall("pid=[0-9]+", output.output))[0])[1])
            command = "mount | grep -i 'cvblk_mounts'"
            output = self.fbr_obj.execute_command(command)
            self.check_output(output, "Mount has not been done on the FBR")
            for _mounts in output.formatted_output:
                self.mount_ids.append(int(re.search("[0-9]+", _mounts[2]).group()))
            self.mount_ids = [*set(self.mount_ids)]
            command = f'kill -9 {self.cvods_pid}'
            output = self.fbr_obj.execute_command(command)
            self.check_output(output, "CVODS not killed")
            decorative_log("CVODS is killed")
        except Exception:
            self.failure_msg += '<br> Exception in killing of cvods <br>'
            raise Exception("Exception in killing cvods")

    def cvods_cleanup(self):
        """
        Verify that on respawning of cvods, older mounts are cleaned up

        """
        try:
            decorative_log(f"Verifying is CVODS has started and previous mount points are cleaned up on {self.fbr_ma}")
            command = "ss -tnlp | grep -i 'cvods'"
            output = self.fbr_obj.execute_command(command)
            self.check_output(output, "CVODS is not running in the FBR")
            _new_cvods_pid = int(re.split("pid=", (re.findall("pid=[0-9]+", output.output))[0])[1])
            if _new_cvods_pid == self.cvods_pid:
                self.ind_status = False
                raise Exception("Pid of CVODS is same as before")
            command = "mount | grep -i 'cvblk_mounts'"
            output = self.fbr_obj.execute_command(command)
            self.check_output(output, "Mount has not been done on the FBR after killing CVODS")
            new_mount_ids = []
            for _mounts in output.formatted_output:
                new_mount_ids.append(int(re.search("[0-9]+", _mounts[2]).group()))
            new_mount_ids = [*set(new_mount_ids)]
            if set(new_mount_ids).issubset(set(self.mount_ids)):
                self.ind_status = False
                raise Exception("Older mount points are still not pruned")
            decorative_log("cvods services has resumed after killing it previously")
        except Exception:
            self.failure_msg += '<br> Exception in cleanup of cvods <br>'
            raise Exception("Exception in cleanup of cvods")

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            self.pre_requisite()

            self.tc_utils.run_backup(self, backup_type='INCREMENTAL',
                                     msg='Streaming Full Backup')
            vm_count = 0
            try:
                for vm in self.tc_utils.sub_client_obj.hvobj.VMs:
                    vm_count += 1
                    _temp_vm, _temp_vmid = self.tc_utils.sub_client_obj.subclient.\
                        _get_vm_ids_and_names_dict_from_browse()
                    _ = self.tc_utils.sub_client_obj.subclient.guest_files_browse(
                        _temp_vmid[vm],
                        media_agent=self.tcinputs.get(
                            'browse_ma',
                            self.tc_utils.sub_client_obj.browse_ma[
                                0]))
                    if vm_count == 1:
                        self.killing_cvods()
                        continue
                    else:
                        self.cvods_cleanup()
                        fs_restore_options = OptionsHelper.FileLevelRestoreOptions(self.tc_utils.sub_client_obj)
                        flr_options, _, _ = self.tc_utils.sub_client_obj. \
                            file_level_path(fs_restore_options,
                                            vm,
                                            self.tc_utils.sub_client_obj.hvobj.VMs[
                                                vm].drive_list)
                        dest_client = machine.Machine(fs_restore_options.destination_client,
                                                      self.tc_utils.sub_client_obj.auto_commcell.commcell)
                        flr_options['dest_machine'] = dest_client
                        self.tc_utils.sub_client_obj.fs_restore_dest = self.tc_utils.sub_client_obj.restore_path(
                            fs_restore_options, vm)
                        fs_restore_job = self.tc_utils.sub_client_obj.subclient. \
                            guest_file_restore(vm_name=vm,
                                               folder_to_restore=flr_options['_fs_path_to_browse_list'],
                                               destination_client=fs_restore_options.destination_client,
                                               destination_path=self.tc_utils.sub_client_obj.fs_restore_dest,
                                               copy_precedence=fs_restore_options.copy_precedence,
                                               preserve_level=flr_options['_preserve_level'],
                                               unconditional_overwrite=fs_restore_options.unconditional_overwrite,
                                               browse_ma=flr_options['browse_ma'],
                                               fbr_ma=self.fbr_ma,
                                               agentless="")
                        self.log.info(" Running restore Job {0} :".format(fs_restore_job))
                        if not fs_restore_job.wait_for_completion():
                            raise Exception(
                                "Failed to run file level restore job {0} with error:{1}".format(
                                    fs_restore_job.job_id, fs_restore_job.delay_reason))
                        self.log.info("file level restore Job got complete JOb Id:{0}".format(
                            fs_restore_job.job_id))
                        self.tc_utils.sub_client_obj.file_level_validation(flr_options,
                                                                           self.tc_utils.sub_client_obj.hvobj.VMs[
                                                                               vm].drive_list,
                                                                           job_time_end=fs_restore_job.end_timestamp)

            except Exception:
                self.ind_status = False
                self.failure_msg += '<br> ' \
                                    'exception in killing or cleanup of cvods or guest file restore in the testcase' \
                                    '<br>'
                raise Exception("Exception in killing or cleanup of cvods or guest file restore in the testcase")

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
