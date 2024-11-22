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
    __init__()                          --      initialize TestCase class

    setup()                             --      setup function of this test case

    cleanup_resources()                 --      common function to remove the created resources of this testcase

    clean_disk()                        --      Un mount and format the disks

    delete_resources()                  --      Deleted created libraries and policies

    testcase_based_lib()                --      create library here according to the mount path need in the testcase

    create_resources()                  --      function to create the required objects /  resources for the testcase

    check_hyperscale_machine()          --      verify for hyperscale machine

    check_library_present               --      check if there is are libraries already present on the media agent

    get_mountpath_folder                --      get folder inforamtion for the mount path and create actual path for it on media agent

    mount_path_protected_verify         --      check if the mountpaths are being protected

    run_backup_job                      --      running a backup job depending on argument

    validation_per_mount_path           --      function will run validation and checks for the mount paths of this testcase

    verify_ransomware_enablement        --      verify if ransomware enablement went successfully or not

    is_ready                            --      wait for client to become ready

    create_fstab_copy                   --      make a copy for /etc/fstab

    disable_selinux                     --      Disable Selinux on the machine

    create_denial_log                   --      clear content of  denial log file and create log file for the denial logs

    rotate_audit_log                    --      Rotate audit log

    log_denial_logs                     --      log audit denial logs after selinux enablement

    run()                               --      run function of this test case

    tear_down()                         --      tear down function of this test case

basic idea of the test case:
Automate RansomWare Protection Feature Testcases for Mountpaths on linux media agent

prerequisites:
-- Not for Hyperscale/Hedvig Machine
1. 2 free disks on machine
2. static ip for the media agent
3. snapshot of media agent before executing tc


input json file arguments required:
"59760":{
           "AgentName": "File System",
           "MediaAgentName": "machine_name",
           "Linux_File_System": "file_system_type",
           "Disk1": "disk_name1",
           "Disk2": "disk_name2"
           }

Design steps:
1. check ransomware enabled already or not
2. check all rpms present -->code done - OS check, check instance(multiple not supported)
3. check if library already present on the MA, if yes ./cvsecurity.py protect_disk_library -i InstanceID
4. if step 3, make copy of fstab, create fstab entry
5. Put MA in maintanence mode
7. From /opt/commvault/MediaAgent ,Run ./cvsecurity.py enable_protection -i InstanceID
8. if library already present on the MA, if yes ./cvsecurity.py protect_disk_library -i InstanceID
9. Reboot MA, (static ip)
10. After reboot ./cvsecurity.py restart_cv_services -i InstanceID
11. Turn off maintanence mode
12.Validation of ransomware enabled {enforcing} and pstree -Z | grep -i cv, ls -Z <direc>, validate fstab return
13. run some backup
14.Validate mount path, do operations delete and create
validation, shouldn ot be deleted, tail -f /var/log/audit/audit.log | grep -i cvstorage "Access denied" , grep rm -rf
15.create library and provide MP case 2( After enable )
16. run some backup
17. step 14 again

"""
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper
from Install import install_helper
from MediaAgents.MAUtils.unix_ransomware_helper import UnixRansomwareHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = """Ransomware protection feature testcase for Mountpath"""
        self.tcinputs = {
            "MediaAgentName": None,
            "Disk1": None,
            "Disk2": None
        }
        self.mount_path = None
        self.mount_path2 = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.media_agent_anomaly = None
        self.job = None
        self.error_flag = None
        self.unc_path = None
        self.disk1 = None
        self.disk2 = None
        self.file_system = None
        self.cv_instance = None
        self.disk_head = '/dev/'
        self.client_obj = None

    def setup(self):
        """
        assign values to variables for testcase
        check what sort of configuration should the testcase run for
        """
        # in linux, stop the testcase if ddb path is not provided

        self.library_name = f"{self.id}_lib"
        self.storage_policy_name = f"{self.id}_SP"
        self.library_name1 = f"{self.id}_lib2"
        self.storage_policy_name1 = f"{self.id}_SP2"
        self.backupset_name = f"{self.id}_BS"
        self.subclient_name = f"{self.id}_SC"
        self.client = self.commcell.clients.get(self.commcell.commserv_name)
        self.agent = self.client.agents.get(self.tcinputs.get("AgentName"))
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.commcell.commserv_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs.get("MediaAgentName"), self.commcell)
        self.disk1 = f'{self.disk_head}{self.tcinputs.get("Disk1")}'
        self.disk2 = f'{self.disk_head}{self.tcinputs.get("Disk2")}'
        self.mount_path = f"{self.media_agent_machine.os_sep}{self.id}mount_path_1"
        self.mount_path2 = f"{self.media_agent_machine.os_sep}{self.id}mount_path_2"
        self.file_system = self.tcinputs.get("Linux_File_System")
        self.client_obj = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))
        self.audit_denial_path = f'{self.client_obj.log_directory}/{self.id}_audit_denials.log'
        self.ransomware_helper = UnixRansomwareHelper(self.media_agent_machine, self.commcell, self.log)

    def cleanup_resources(self):
        """
        common function to remove the created resources of this testcase
        Removes -- (if exist)
                - Content directory
                - storage policy
                - backupset
                - Library
        """
        self.log.info("**************Clean up resources***************")
        try:
            # delete the generated content for this testcase if any
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            self.log.info("deleting backupset and SP of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            self.delete_resources(self.library_name, self.storage_policy_name)
            self.delete_resources(self.library_name1, self.storage_policy_name1)
            self.clean_disk(self.disk1)
            self.clean_disk(self.disk2)
            self.log.info("clean up successful")
        except Exception as exp:
            self.log.error("cleanup failed with issue: %s", exp)

    def clean_disk(self, disk):
        """
        Un mount and format the disks
        Un mounting the disk if it already mounted over(free disk input will be provided)
        1.Unmount disk
        2.Format disk using dd commnad
        3.Remove directory over which mount was done
        4.Deleting the fstab entry for the same

        Sample outputs for commands
         df -h
            Filesystem             Size  Used Avail Use% Mounted on
            /dev/mapper/rhel-root   50G   21G   30G  41% /
            devtmpfs               3.8G     0  3.8G   0% /dev

        Args:
            disk (str) -- disk name

        """
        self.log.info("Unmounting the disks %s", disk)
        storage_details = self.media_agent_machine.get_storage_details()
        if disk in storage_details:
            output = self.media_agent_machine.unmount_path(mount_path=storage_details.get(disk).get('mountpoint'))
            self.log.info(output)

            self.log.info("Formatting disks %s on media agent %s", disk, self.tcinputs.get("MediaAgentName"))
            temp = disk.replace('/dev/', '')
            output = self.media_agent_machine.fill_zero_disk(temp)
            self.log.info(output)

            self.log.info("Removing directory")
            output = self.media_agent_machine.remove_directory(storage_details.get(disk).get('mountpoint'))
            self.log.info("Directory remove: ", output)
            if not output:
                self.log.error("Directory remove: ", output)
                raise Exception("Directory removal failed, please check")

            self.log.info("Cleaning fstab entry")
            command = "sed -i '{0}/d' /etc/fstab".format(storage_details.get(disk).get('mountpoint'))
            self.log.info(command)
            self.media_agent_machine.execute_command(command)
        else:
            self.log.info("Disk %s is not mounted", disk)

    def delete_resources(self, lib_name, storage_policy_name):
        """Deleted created libraries and policies
        Args:
            lib_name (str) -- library name
            storage_policy_name (str) -- storage pool policy name
        """
        if self.commcell.storage_policies.has_policy(storage_policy_name):
            self.commcell.storage_policies.delete(storage_policy_name)
            self.log.info("storage policy deleted")
        else:
            self.log.info("storage policy does not exist.")

        if self.commcell.disk_libraries.has_library(lib_name):
            self.commcell.disk_libraries.delete(lib_name)
            self.log.info("Library deleted")
        else:
            self.log.info("Library does not exist.")

    def testcase_based_lib(self, lib_name, media_agent, mount_path):
        """create library here according to the mount path need in the testcase
        Args:
            lib_name (str) -- library name
            media_agent (str) -- Media agent name
            mount_path (str) -- mount path name
        """
        # create library
        self.log.info("creating library")
        self.library = self.commcell.disk_libraries.add(lib_name, media_agent, mount_path)

    def create_resources(
            self,
            mount_path,
            lib_name,
            storage_policy_name,
            disk,
            initial=False):
        """function to create the required objects /  resources for the testcase
        Args:
            mount_path (str) -- mount path name
            lib_name (str) -- library name
            storage_policy_name (str) -- storage policy name
            disk (str) -- disk name
            initial (bool) -- (False/True) default: False
        """
        self.log.info("############ Creating Resources ###############")
        self.log.info("Creating Mount Path directory")
        if not self.media_agent_machine.check_directory_exists(mount_path):
            output = self.media_agent_machine.create_directory(mount_path)
            self.log.info("creating directory status: ", output)

        self.log.info("Creating FileSystem and mounting to mount point")
        self.media_agent_machine.create_local_filesystem(self.file_system, disk)
        output = self.media_agent_machine.mount_local_path(disk, mount_path)
        self.log.info(output)

        if initial:
            drive_path_client = self.opt_selector.get_drive(
                self.client_machine)
            # creating testcase directory, mount path, content path
            self.testcase_path_client = f"{drive_path_client}{self.id}"

            self.content_path = self.client_machine.join_path(
                self.testcase_path_client, "content_path")
            if self.client_machine.check_directory_exists(self.content_path):
                self.log.info("content path directory already exists")
            else:
                self.client_machine.create_directory(self.content_path)
                self.log.info("content path created")
            # create backupset
            self.backup_set = self.mm_helper.configure_backupset(
                self.backupset_name, self.agent)

            # generate content for subclient
            # generating content once should suffice before running backups
            # we are pointing the subclient to a different storage policy
            if self.mm_helper.create_uncompressable_data(
                    self.commcell.commserv_name, self.content_path, 1, 1):
                self.log.info(
                    "generated content for subclient %s",
                    self.subclient_name)

        # create library with mount path as needed according to testcase
        self.testcase_based_lib(
            lib_name,
            self.tcinputs.get("MediaAgentName"),
            mount_path)

        self.log.info("adding entry for mount path in /etc/fstab")
        command = "cat /etc/fstab | grep {0}".format(mount_path)
        output = self.media_agent_machine.execute_command(command)
        if not output.output:
            command = 'echo "{0}                {1}                   {2}    defaults        0 0" >> /etc/fstab'.format(
                disk, mount_path, self.file_system)
            self.log.info("command:: %s", command)
            output = self.media_agent_machine.execute_command(command)
            self.log.info(output.output)
        else:
            self.log.error("entry already present for mount path %s", mount_path)

        # create SP
        self.log.info("creating storage policy")
        self.storage_policy = self.commcell.storage_policies.add(
            storage_policy_name,
            lib_name,
            self.tcinputs.get("MediaAgentName"))

        # point the existing subclient to newly created storage policy
        if initial:
            # create subclient and add subclient content
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                storage_policy_name,
                self.content_path,
                self.agent)
        else:
            self.subclient.storage_policy = storage_policy_name

    def check_hyperscale_machine(self):
        """
        This function will verify for hyperscale machine
        Raises:
            Exception(Exception_message):
            if hyperscale machine

        """
        self.log.info("checking for hyperscale machine")
        command = f"grep -i HyperScale {self.media_agent_machine.key % ('MediaAgent')}"
        output = self.media_agent_machine.execute_command(command)
        self.log.info(output.output)
        if output.output:
            raise Exception("Hyperscale MA not supported for this TC")
        self.log.info("Not a Hyperscale Machine")

    def check_library_present(self):
        """
        This will check if there is are libraries already present on the media agent
        Return:
            Bool True/False
        """
        self.log.info("checking library on ma")
        status = False
        disks = self.commcell.disk_libraries.all_disk_libraries
        disk_list = list(disks.keys())
        for disk in disk_list:
            disk_details = self.commcell.disk_libraries.get(disk)
            media_agents_associated = disk_details.media_agents_associated
            if self.tcinputs.get("MediaAgentName") in media_agents_associated:
                status = True
                self.log.info("Library %s already present on MA", disk)
                return status
        return status

    def get_mountpath_folder(self, lib_name, mount_path):
        """
        Will get folder inforamtion for the mount path and create actual path for it on media agent
        Args:
            lib_name (str) -- library name
            mount_path (str) -- mount path name
        Return:
            actual mount path(str)
        """
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
        actual_location = f"{mount_path}{self.media_agent_machine.os_sep}{mount_path_location}" \
                          f"{self.media_agent_machine.os_sep}CV_MAGNETIC"
        self.log.info("MP location on MA %s", actual_location)
        return actual_location

    def mount_path_protected_verify(self, lib_name, mount_path, disk):
        """
        This will check if the mountpaths are being protected.
        Will attempt to write a file in the path location
        and then delete it.
        ARgs:
            lib_name (str) -- library name
            mount_path (str) -- mount path name
            disk (str) -- disk
        Returns:
             protection working or not [bool]
        """
        # get the physical mount path location from csdb
        protection_status = False
        actual_location = self.get_mountpath_folder(lib_name, mount_path)

        # going to cv_magnetic folder inside mount path where volumes are kept
        existing_folder = self.media_agent_machine.get_folders_in_path(
            actual_location, recurse=False)

        # creating a new folder
        self.log.info("trying to write to the path %s", actual_location)
        check1, check2 = False, False
        temp = self.media_agent_machine.join_path(actual_location, f"{self.id}_temp")
        self.log.info(temp)
        command = "mkdir {0} & echo $!".format(temp)
        self.log.info("command: %s", command)
        output = self.media_agent_machine.execute_command(command)
        self.log.info("pid %s", output.output)
        self.log.info(output.exception)
        # check permission denied out
        if output.exception_message.lower() == 'permission denied':
            check1 = True
            self.log.info("mount path write protected, ransomware working as expected")
        if self.media_agent_machine.check_directory_exists(temp):
            self.log.error("mount path not write protected, ransomware not working")
        else:
            self.log.info("directory creation failed, mount path write protected")

        self.log.info("validating log")
        command = "bzgrep 'pid={0}' /var/log/audit/audit.log".format(output.formatted_output)
        self.log.info("command: %s", command)
        output = self.media_agent_machine.execute_command(command)
        self.log.info(output.output)
        if (('comm="mkdir"' in output.output) and ('dev="{0}"'.format(disk.replace('/dev/', '')) in output.output)
                and ('name="CV_MAGNETIC"' in output.output) and ('success=no' in output.output)
                and ('avc:  denied  { write }' in output.output) and ('cvstorage' in output.output)):
            check2 = True
            self.log.info("mount path write protected, ransomware working as expected")
        else:
            self.log.error("mount path not write protected")

        if check1 and check2:
            self.log.info("mount path write protected, ransomware working as expected")
        else:
            self.log.error("mount path not write protected")

        if self.media_agent_machine.check_directory_exists(temp):
            self.media_agent_machine.remove_directory(temp)

        # deleting from the mount path
        self.log.info("trying to delete V_ folder from %s", actual_location)
        check3, check4 = False, False
        command = "rm -rf {0} & echo $!".format(existing_folder[1])
        output1 = self.media_agent_machine.execute_command(command)
        self.log.info("pid %s", output1.output)
        self.log.info(output1.exception)
        if output1.exception_message.lower() == 'permission denied':
            check3 = True
            self.log.info("mount path write protected")
        if self.media_agent_machine.check_directory_exists(existing_folder[1]):
            self.log.info("deletion failed for %s", existing_folder[1])
        else:
            self.log.error("delete success, not protected")

        self.log.info("validating log")
        command = "bzgrep 'pid={0}' /var/log/audit/audit.log".format(output1.formatted_output)
        self.log.info("command: %s", command)
        output = self.media_agent_machine.execute_command(command)
        self.log.info(output.output)
        for info in output.formatted_output:
            if 'type=AVC' in info:
                string = " ".join(info)
                if (('comm="rm"' in string) and ('dev="{0}"'.format(disk.replace('/dev/', '')) in string)
                        and ('pid={0}'.format(output1.formatted_output) in string)
                        and ('avc: denied { write }' in string) and ('cvstorage' in string)):
                    check4 = True
                    self.log.info("mount path protected, ransomware working as expected")
                    break
        if check3 and check4:
            self.log.info("mount path protected, ransomware working as expected")
        else:
            self.log.error("mount path not write protected")

        # editing from the mount path
        self.log.info("trying to edit V_ folder from %s", actual_location)
        check5, check6 = False, False
        command = "touch {0} & echo $!".format(existing_folder[1])
        output1 = self.media_agent_machine.execute_command(command)
        self.log.info("pid %s", output1.output)
        self.log.info(output1.exception)
        if output1.exception_message.lower() == 'permission denied':
            check5 = True
            self.log.info("mount path write protected")
            self.log.info("edit failed for %s", existing_folder[1])
        else:
            self.log.error("edit success, not protected")

        self.log.info("validating log")
        command = "bzgrep 'pid={0}' /var/log/audit/audit.log".format(output1.formatted_output)
        self.log.info("command: %s", command)
        output = self.media_agent_machine.execute_command(command)
        self.log.info(output.output)
        for info in output.formatted_output:
            if 'type=AVC' in info:
                string = " ".join(info)
                if (('comm="touch"' in string) and ('dev="{0}"'.format(disk.replace('/dev/', '')) in string)
                        and ('pid={0}'.format(output1.formatted_output) in string)
                        and ('avc: denied { write }' in string) and ('cvstorage' in string)):
                    check6 = True
                    self.log.info("mount path protected, ransomware working as expected")
                    break
        if check5 and check6:
            self.log.info("mount path protected, ransomware working as expected")
        else:
            self.log.error("mount path not write protected")

        if check1 and check2 and check3 and check4 and check5 and check6:
            protection_status = True
        return protection_status

    def run_backup_job(self, job_type):
        """running a backup job depending on argument
            job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)
        """
        self.log.info("Starting backup job type: %s", job_type)
        job = self.subclient.backup(job_type)
        self.log.info("Backup job: %s", str(job.job_id))
        self.log.info("job type: %s", job_type)
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)
        return job

    def validation_per_mount_path(
            self,
            check_for_lib,
            path_to_location,
            disk,
            backup_job=True):
        """
        This function will run validation and checks for the mount paths of this testcase.
        Will involve -
                    1. FULL backup job run on mount path
                    2. Check mountpath_protected
        Returns:

        """
        self.log.info("validating mount path, by manipulation")
        if backup_job:
            self.run_backup_job("FULL")
        status = self.mount_path_protected_verify(check_for_lib, path_to_location, disk)
        return status

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
        status = self.ransomware_helper.verify_ransomware_enablement()
        if not status:
            raise Exception("cvbackup not tagged with processes")
        return status

    def is_ready(self):
        """
        wait for client to become ready
        Return:
            bool[True,False]
        """
        install_helper_obj = install_helper.InstallHelper(self.commcell, self.media_agent_machine)
        ready = False
        if install_helper_obj.wait_for_services():
            ready = True
        return ready

    def create_fstab_copy(self):
        """Create copy for /etc/fstab"""
        self.log.info("Creating /etc/fstab copy")
        self.media_agent_machine.copy_folder("/etc/fstab", "/root/")

    def disable_selinux(self):
        """
        Disable Selinux on the machine at the end of TC, if selinux is enabled
        Remove labels (cvstorage) from the mount paths as well
        """
        self.ransomware_helper.disable_selinux()
        self.ransomware_helper.unlabel_cvstorage(self.library_name1, self.mount_path2)
        self.log.info("Checking tags on mount paths")
        if self.ransomware_helper.verify_maglib_protected(self.library_name, self.mount_path) or \
                self.ransomware_helper.verify_maglib_protected(self.library_name1, self.mount_path2):
            self.log.error("Maglib still protected, disable failed")

    def create_denial_log(self):
        """
        clear content of  denial log file and create log file for the denial logs
        """
        output = self.media_agent_machine.check_file_exists(self.audit_denial_path)
        if not output:
            output = self.media_agent_machine.create_file(self.audit_denial_path, '')
            self.log.info(output)

        else:
            self.log.info("clear content of denial log file")
            command = f'echo > {self.audit_denial_path}'
            self.log.info("Command : %s ", command)
            output = self.media_agent_machine.execute_command(command)
            self.log.info(f"output {output.output} + {output.exception}")

    def rotate_audit_log(self):
        """Rotate audit log, to log logs for the TC"""
        command = "service auditd rotate"
        self.log.info(f"command : {command}")
        output = self.media_agent_machine.execute_command(command)
        self.log.info(f"output : {output.output}")
        if output.formatted_output != 'Rotating logs:':
            self.log.error(f"audit log not rotated, exception : {output.exception}")
            raise Exception(f"audit log not rotated, exception: {output.exception}")

    def log_denial_logs(self):
        """log audit denial logs after selinux enablement """
        self.log.info("writing to the denials file")
        command = f" bzgrep 'cvstorage \\| avc:  denied' /var/log/audit/audit.log >> {self.audit_denial_path}"
        self.log.info("Command : %s ", command)
        output = self.media_agent_machine.execute_command(command)

    def run(self):
        """Run function of this test case"""
        try:

            # remove pre-created resources if any
            self.cleanup_resources()
            ransomware_status = self.ransomware_helper.ransomware_protection_status()
            if ransomware_status:
                raise Exception("Ransomware already enabled")

            self.check_hyperscale_machine()
            prerequisite = self.ransomware_helper.check_sys_req()
            if not prerequisite:
                raise Exception("System requirements not met")

            self.create_fstab_copy()
            self.create_resources(mount_path=self.mount_path,
                                  lib_name=self.library_name,
                                  storage_policy_name=self.storage_policy_name,
                                  disk=self.disk1,
                                  initial=True)

            self.log.info("check library on MA")
            library_present = self.check_library_present()
            if not library_present:
                self.log.info("no library on MA")
            self.log.info("library present on MA")

            self.rotate_audit_log()
            self.create_denial_log()
            self.ransomware_helper.enable_protection_linux(library_present=library_present)

            # Create resources for content and subclient common accross
            # content, library, storage policy, subclient created
            maglib_protect = self.ransomware_helper.verify_maglib_protected(lib_name=self.library_name,
                                                                            mount_path=self.mount_path)
            if not maglib_protect:
                raise Exception("CVStorge is not tagged with Maglib")
            self.log.info("Maglib %s is protected", self.library_name)
            if library_present:
                self.log.info("checking cvstorage tag updation in /etc/fstab")
                tag = False
                command = "bzgrep 'cvstorage' /etc/fstab"
                output = self.media_agent_machine.execute_command(command)
                self.log.info(output.output)
                if isinstance(output.formatted_output, str):
                    if self.disk1 and self.mount_path and self.file_system in output.formatted_output:
                        tag = True

                if isinstance(output.formatted_output, list):
                    for info in output.formatted_output:
                        if self.disk1 and self.mount_path and self.file_system in info:
                            tag = True
                            break
                if not tag:
                    self.log.error("mount path not tagged with cvstorage for existing library")
                    raise Exception("mount path not tagged with cvstorage for existing library, check selinux")
                self.log.info("mount path tagged with cvstorage successfully")

            # new mount path, library, storage policy created - associated to same subclient
            self.create_resources(mount_path=self.mount_path2,
                                  lib_name=self.library_name1,
                                  storage_policy_name=self.storage_policy_name1,
                                  disk=self.disk2,
                                  initial=True)

            # do validations with backup content present on mount path
            if not self.validation_per_mount_path(backup_job=True,
                                                  check_for_lib=self.library_name1,
                                                  path_to_location=self.mount_path2,
                                                  disk=self.disk2):
                raise Exception("Selinux not working properly, not write protected")

            self.ransomware_helper.pause_protection()
            if not self.validation_per_mount_path(backup_job=False,
                                                  check_for_lib=self.library_name1,
                                                  path_to_location=self.mount_path2,
                                                  disk=self.disk2):
                self.log.info(f"Protection is paused, able to perform write operations")

            self.ransomware_helper.resume_protection()
            if not self.validation_per_mount_path(backup_job=False,
                                                  check_for_lib=self.library_name1,
                                                  path_to_location=self.mount_path2,
                                                  disk=self.disk2):
                raise Exception("Selinux not working properly, not write protected")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes all items of the testcase"""
        self.log.info("*********************************************")
        self.log.info("Restoring defaults")
        self.log_denial_logs()
        self.disable_selinux()
        self.cleanup_resources()
        self.log.info("Putting MA off maintenance mode")
        media_agent = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName")). \
            mark_for_maintenance(False)
