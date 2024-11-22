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
    __init__()            --  Initializes test case class object

    setup()               --  Setup function of this test case

    cleanup_resources()   -- Removes the created resources of this testcase

    testcase_based_lib()  -- Create library here according to the mount path need in the testcase

    create_resources()    -- Create the required objects / resources for the testcase

    get_mp_directories()  --  Return Paths to directories inside the MP Location
                              required for folder manipulations in the TC

    mount_path_protected_verify()               -- Check if the Mount Path is being protected

    is_driver_loaded_and_mountpath_protected()  -- Check if the cvdlp driver is loaded in MA and
                                                   if the MP is being properly protected (writes disabled)

    run_backup_job()                       -- Run a backup job of specified type and wait till it is completed

    validation_per_mount_path()            --  Run Checks and do validations for the mount paths of this testcase.

    check_ransomware_protection_enabled()  --  Validate if the ransomware protection is enabled properly or not.

    disable_ransomware_protection_validations()  --  Disable the ransomware protection and do the validations

    directory_creation_check()  -- Validate directory creation in MP when it is not protected

    run()                       --  Run function of this test case

    tear_down()                 --  Tear Down Function of this Case

prerequisites:
try to keep CS and MA machine separate
noticed instances of driver not being unloaded if CS and MA are on same machine.

TcInputs to be passed in JSON File:
        "62693": {
            "ClientName": "Name of Client",
            "AgentName": "File System",
            "MediaAgent1Name": "Name of Media Agent 1",  // We use the physical location on this Machine for creating MP
            "MediaAgent2Name": "Name of Media Agent 2",  // We try to access the MP from this machine via UNC Share
            "username": "required input",                // Access credentials for accessing the UNC Shares
            "password": "required input"
        }
Steps:

1.  Check Ransomware is enabled by Default on the MAs

** CASE 1 **
2.  Create Resources: Library (MA: machine2, MP: \\\\machine1\\mp1), SP, SubClient

3.  Run Backup Job

4. Validate ransomware protection. Do Operations from machine2 via UNC Path
    -   Ransomware turned on and driver loaded
    -   delete existing directory & create new directory should fail

5. Disable Ransomware protection and do validations. Do Operations from machine2 via UNC Path
    -   Ransomware turned off and driver unloaded
    -   create new directory should succeed

6. Create Resources: Library (MA: machine2, MP: \\\\machine1\\mp2), SP, re-associate the SC

7.  Run Backup Job

8.  Enable Ransomware protection and do validations.  Do Operations from machine2 via UNC Path
    -   Ransomware turned on and driver loaded
    -   delete existing directory & create new directory should fail

** CASE 2 **
9.  Create Resources: Library (MA: machine1, MP: C:\\mp3), SP, re-associate the SC. Share the MP Location via UNC

10. Validate ransomware protection. Do Operations from machine2 via UNC Path
    -   delete existing directory & create new directory should succeed

11. Share the MountPath to machine2 and do validations. Do Operations from machine2 via UNC Path
    -   Ransomware turned on and driver loaded
    -   delete existing directory & create new directory should fail

12. CleanUp the Entities.
"""

import time

from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = """Ransomware protection feature testcase for UNC Mountpath"""
        self.tcinputs = {
            "MediaAgent1Name": None,
            "MediaAgent2Name": None,
            "username": None,
            "password": None
        }
        self.mount_location = None
        self.content_path = None
        self.restore_path = None
        self.dedup_store_path = None
        self.library_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_policy_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine1 = None
        self.media_agent_machine2 = None
        self.opt_selector = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.subclient = None
        self.backup_set = None
        self.storage_policy = None
        self.error_flag = None
        self.storage_entities = None
        self.media_agent_obj1 = None
        self.media_agent_obj2 = None

    def setup(self):
        """Setup function of this test case"""
        self.opt_selector = OptionsSelector(self.commcell)
        self.library_name = str(self.id) + "_Lib"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.storage_policy_name = str(self.id) + "_SP"

        self.client_machine = machine.Machine(self.client, self.commcell)
        self.media_agent_obj1 = self.commcell.media_agents.get(self.tcinputs.get("MediaAgent1Name"))
        self.media_agent_obj2 = self.commcell.media_agents.get(self.tcinputs.get("MediaAgent2Name"))
        self.media_agent_machine1 = machine.Machine(self.tcinputs.get("MediaAgent1Name"), self.commcell)
        self.media_agent_machine2 = machine.Machine(self.tcinputs.get("MediaAgent2Name"), self.commcell)

        drive_path_client = self.opt_selector.get_drive(self.client_machine)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        self.error_flag = []
        # for older entities cleanup
        self.storage_entities = [[f"{self.library_name}1", f"{self.library_name}2", f"{self.library_name}3"],
                                 [f"{self.storage_policy_name}1", f"{self.storage_policy_name}2",
                                  f"{self.storage_policy_name}3"],
                                 [f'share_{self.id}_1', f'share_{self.id}_2', f'share_{self.id}_3']]
        self.mm_helper = mahelper.MMHelper(self)
        self.dedup_helper = mahelper.DedupeHelper(self)

    def cleanup_resources(self):
        """Removes the created resources of this testcase
        Removes -- (if exist)
                - Content directory
                - BackupSet, Storage Policies, Libraries
                - un-share the shared paths
        """
        self.log.info("************** CleanUp Resources ***************")
        try:
            self.log.info("Deleting Content If Exists")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            self.log.info("Deleting BackupSet, SPs, Libraries If Exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("BackupSet[%s] deleted", self.backupset_name)
            for sp_name in self.storage_entities[1]:
                if self.commcell.storage_policies.has_policy(sp_name):
                    self.commcell.storage_policies.delete(sp_name)
                    self.log.info("Storage Policy[%s] deleted", sp_name)
            for lib_name in self.storage_entities[0]:
                if self.commcell.disk_libraries.has_library(lib_name):
                    self.commcell.disk_libraries.delete(lib_name)
                    self.log.info("Library[%s] deleted", lib_name)
            self.log.info("wait for 120 secs for data in mp to be removed after library deletion")
            time.sleep(120)
            self.log.info('UnSharing the Shared Directories')
            for share_name in self.storage_entities[2]:
                try:
                    self.media_agent_machine1.unshare_directory(share_name)
                except Exception as exe:
                    self.log.error("UnShare failed: %s %s", share_name, str(exe))
            self.storage_entities = [[], [], []]

            self.log.info("************** CleanUp successful **************")
        except Exception as exp:
            self.log.error("************** CleanUp failed with issue: %s **************", exp)

    def testcase_based_lib(self, lib_name, media_agent, mount_path, unc_path):
        """Create library here according to the mount path need in the testcase

        Args:
            lib_name    (str):  name of the library to be created

            media_agent (str):  name of the MA to be used for library creation

            mount_path  (str):  mount path to be used for library

            unc_path    (bool): True if we are creating a UNC path based library
                                False if we are not creating a UNC path based library
        Returns:
            Library object after creation of the library
        """
        self.log.info("Creating Lib with MA[%s] MP[%s]", media_agent, mount_path)
        if unc_path:
            library = self.mm_helper.configure_disk_library(
                lib_name, media_agent, mount_path,
                self.tcinputs.get("username"), self.tcinputs.get("password"))
        else:
            library = self.mm_helper.configure_disk_library(lib_name, media_agent, mount_path)
        return library

    def create_resources(self, host_machine, media_agent_machine, initial=False, create_count=None):
        """Create the required objects / resources for the testcase

        Args:
            initial             (bool)   :  if the create_resources function has been
                                            called the first time in the testcase

            host_machine        (Machine):  Machine Object for the MP Host

            media_agent_machine (Machine):  Machine Object for the MediaAgent

            create_count        (str)    :  an additional variable used in the naming of
                                            the resources created for clarity every time
                                            create_resources function is called.
        """
        self.log.info("*** Creating required resources for the case. MA:[%s], Host:[%s] ***",
                      media_agent_machine.machine_name, host_machine.machine_name)
        drive_path_host_machine = self.opt_selector.get_drive(host_machine)
        drive_path_media_agent = self.opt_selector.get_drive(media_agent_machine)

        self.testcase_path_host_machine = host_machine.join_path(drive_path_host_machine, f'test_{self.id}')
        self.testcase_path_media_agent = media_agent_machine.join_path(drive_path_media_agent, f'test_{self.id}')

        self.host_path = host_machine.join_path(self.testcase_path_host_machine, f"mount_path_{create_count}")
        if not host_machine.check_directory_exists(self.host_path):
            host_machine.create_directory(self.host_path)
        host_machine.share_directory(f'share_{self.id}_{create_count}',
                                     self.host_path, user=self.tcinputs.get("username"))
        self.storage_entities[2].append(f'share_{self.id}_{create_count}')
        self.mount_location = f"\\\\{host_machine.machine_name}\\share_{self.id}_{create_count}"

        if host_machine.machine_name != media_agent_machine.machine_name:
            # for case 1: library with unc MP
            self.library = self.testcase_based_lib(f"{self.library_name}{create_count}",
                                                   media_agent_machine.machine_name, self.mount_location, unc_path=True)
        else:
            # for case 2: library with local MP
            self.library = self.testcase_based_lib(f"{self.library_name}{create_count}",
                                                   media_agent_machine.machine_name, self.host_path, unc_path=False)
        self.storage_entities[0].append(f"{self.library_name}{create_count}")

        # create SP
        self.dedup_store_path = media_agent_machine.join_path(self.testcase_path_media_agent,
                                                              f"dedup_store_path_{create_count}")
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            storage_policy_name=f"{self.storage_policy_name}{create_count}",
            library_name=f"{self.library_name}{create_count}", ma_name=media_agent_machine.machine_name,
            ddb_path=self.dedup_store_path,  ddb_ma_name=media_agent_machine.machine_name)
        self.storage_entities[1].append(f"{self.storage_policy_name}{create_count}")

        if initial:
            self.opt_selector.create_uncompressable_data(self.client.client_name, self.content_path, size=1,
                                                         num_of_folders=1, delete_existing=True)
            self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name, self.subclient_name, f"{self.storage_policy_name}{create_count}",
                self.content_path, self.agent)
        else:
            # point the existing subclient to newly created storage policy
            self.subclient.storage_policy = f"{self.storage_policy_name}{create_count}"
            self.log.info("storage policy of subclient %s changed to %s", self.subclient_name, self.storage_policy_name)

    def get_mp_directories(self, library_name, host_location, mount_location):
        """Return Paths to directories inside the MP Location required for folder manipulations in the TC

        Args:
            library_name    (str):    name of the library

            host_location   (str):    host path to the MP

            mount_location  (str):    unc path to the MP
        Returns:
            (str, str, str):    mount_path_location, physical_path, existing_folder
        """
        # get the physical mount path location from CS DB
        query = f"""select      MountPathName
                    from        mmmountpath MM, MMLibrary ML
                    where       MM.LibraryId=ML.LibraryId
                    and         ML.AliasName='{library_name}'"""
        self.log.info("EXECUTING QUERY: %s", query)
        self.csdb.execute(query)
        mount_path_name = self.csdb.fetch_one_row()[0]
        unc_mp_location = self.media_agent_machine2.join_path(mount_location, mount_path_name)
        host_mp_location = self.media_agent_machine1.join_path(host_location, mount_path_name)
        self.log.info("location of mount path is %s %s", unc_mp_location, host_mp_location)
        # going to cv_magnetic folder inside mount path where volumes are kept
        host_mag_path = self.media_agent_machine1.get_folders_in_path(host_mp_location,
                                                                      recurse=False)[0]
        unc_mag_path = self.media_agent_machine2.join_path(
            unc_mp_location, host_mag_path.split(host_mp_location+self.media_agent_machine1.os_sep)[1])
        self.log.info("path to contents of mount path is %s %s", host_mag_path, unc_mag_path)

        existing_folder = self.media_agent_machine1.get_folders_in_path(host_mag_path, recurse=False)
        if existing_folder:
            existing_folder = existing_folder[0]
            existing_unc_folder = self.media_agent_machine2.join_path(
                unc_mag_path, existing_folder.split(host_mag_path+self.media_agent_machine1.os_sep)[1])
        else:
            existing_folder, existing_unc_folder = '', ''

        self.log.info("path to existing folder is %s %s", existing_folder, existing_unc_folder)
        return (host_mp_location, unc_mp_location), (host_mag_path, unc_mag_path),\
               (existing_folder, existing_unc_folder)

    def mount_path_protected_verify(self, library_name, host_location, mount_location):
        """Check if the Mount Path is being protected.
        Will attempt to write a file in the Path location and then delete it.

        Args:
            library_name    (str):    name of the library

            host_location   (str):    host path to the MP

            mount_location  (str):    unc path to the MP
        Returns:
             (bool) :  protection working or not
        """
        self.log.info("*** Fetching MP Details and verifying if it protected or not ***")
        mp_location, mag_path, existing_folder = self.get_mp_directories(
            library_name, host_location, mount_location)

        protection_working = False
        manipulation_failed = {"mount_path_location": mag_path[0]}  # used for error summarizing

        self.log.info("Attempting alterations via [%s]", self.media_agent_machine2.machine_name)
        # making sure existing folder is not being removed
        try:
            self.log.info("try to delete an existing folder inside CV_magnetic in mount path")
            self.media_agent_machine1.modify_ace('Everyone', existing_folder[0],
                                                 'DeleteSubdirectoriesAndFiles', 'Deny',
                                                 remove=True, folder=True)
            self.media_agent_machine1.modify_ace('Everyone', existing_folder[0], 'Delete',
                                                 'Deny', remove=True, folder=True)
            self.log.info("Deny delete permission removed from %s", existing_folder[0])
            self.media_agent_machine2.remove_directory(existing_folder[1],
                                                       username=self.tcinputs.get("username"),
                                                       password=self.tcinputs.get("password"))

            # below code path should not be touched ideally as remove directory should fail
            manipulation_failed["existing_folder_removal"] = "existing folder was removed" \
                                                             " from inside mount path" \
                                                             " - ransomware protection NOT " \
                                                             "properly working"
            self.log.error("existing folder was removed inside mount path")
        except Exception as exp:
            if "cannot remove item" in str(exp).lower() and "write protected" in str(exp).lower():
                protection_working = True
                self.log.info("existing folder removal failed as expected for %s", existing_folder[1])
            else:
                manipulation_failed["existing_folder_removal"] = str(exp)

        try:
            new_directory_path_unc = self.media_agent_machine2.join_path(
                mag_path[1], f"z_{self.id}_test_direc_{str(time.time()).replace('.', '-')}")

            self.log.info("create new directory %s in mount path", new_directory_path_unc)
            self.media_agent_machine2.create_directory(new_directory_path_unc, force_create=True,
                                                       username=self.tcinputs.get("username"),
                                                       password=self.tcinputs.get("password"))

            # below code path should not be touched ideally as create directory should fail
            new_directory_path = self.media_agent_machine1.join_path(
                mag_path[0], new_directory_path_unc.split(mag_path[1])[1])
            if self.media_agent_machine1.check_directory_exists(new_directory_path):
                self.log.error("creation of directory was successful - this should not"
                               " have occurred - create directory problem")

            manipulation_failed["creating_new_directory"] = "new directory creation was successful " \
                                                            "- ransomware protection  not working properly"
            protection_working = protection_working and False
        except Exception as exp:
            if "new-item : the media is write protected" in str(exp).lower():
                self.log.info("creation of new dir [%s] inside MP location failed as expected", new_directory_path_unc)
                protection_working = protection_working and True
            else:
                manipulation_failed["creating_new_directory"] = str(exp)
                protection_working = protection_working and False

        self.log.info("Is protection working? : %s", protection_working)
        if not protection_working:
            self.log.error("Error Summary [%s]: ", manipulation_failed)
        return protection_working

    def is_driver_loaded_and_mountpath_protected(self,
                                                 library_name,
                                                 host_location,
                                                 mount_location):
        """Check if the cvdlp driver is loaded in MA and if the MP is being properly protected (writes disabled)

        Args:
            library_name    (str):    name of the library

            host_location   (str):    host path to the MP

            mount_location  (str):    unc path to the MP
        """
        self.log.info("***** Check if driver is loaded on MA[%s] and MP[%s] is protected *****",
                      self.media_agent_machine2.machine_name, mount_location)
        driver_loaded = self.mm_helper.ransomware_driver_loaded(
            self.commcell.clients.get(self.media_agent_machine2.machine_name))
        # check if path is protected
        mount_path_protected = self.mount_path_protected_verify(library_name, host_location, mount_location)

        if driver_loaded and mount_path_protected:
            self.log.info(
                "the driver is loaded and the MP is being properly protected by ransomware protection")
        elif not mount_path_protected:
            self.log.error("the mount path is not being protected properly: %s", mount_location)
            self.error_flag += [f'directory manipulation was allowed for mount path {mount_location}']
        elif not driver_loaded:
            self.log.error("CVDLP driver is not loaded")
            self.error_flag += ["CVDLP driver not loaded"]

    def run_backup_job(self, job_type):
        """Run a backup job of specified type and wait till it is completed

        Args:
            job_type (str):  type of backup job
        Returns:
            (Job):  job object
        """
        self.log.info("Starting backup job type: %s", job_type)
        job = self.subclient.backup(job_type)
        self.log.info("Backup job: %s. Job Type: %s", job.job_id, job_type)
        if not job.wait_for_completion():
            raise Exception("Job {0} Failed with JPR: {1}".format(job.job_id, job.delay_reason))
        self.log.info("Job %s complete", job.job_id)
        return job

    def validation_per_mount_path(self, library_name, host_location, mount_location, backup_job=True):
        """Run Checks and do validations for the mount paths of this testcase.

        Will involve -
                    1. FULL backup job run on mount path
                    2. Check_driver_loaded_and_mountpath_protected

        Args:
            library_name    (str):    name of the library

            host_location   (str):    host path to the MP

            mount_location  (str):    unc path to the MP

            backup_job      (bool):   True/False (Run Backup)
        """
        if backup_job:
            self.run_backup_job("FULL")
        self.is_driver_loaded_and_mountpath_protected(library_name, host_location, mount_location)

    def check_ransomware_protection_enabled(self, media_agent, testcase_initial_check=False):
        """Validate if the ransomware protection is enabled properly or not.

        Args:
            media_agent             (MediaAgent):   MediaAgent Object

            testcase_initial_check  (bool):         True if the function is doing the
                                                    check first time in the testcase, we
                                                    are expecting the ransomware protection
                                                    to be 'ON' by default in the initial check.
                                                    This option helps to give clearer logging.
                                                    default - False
        """
        self.log.info("Checking protection status for MA: [%s]", media_agent.media_agent_name)
        protection_enabled = self.mm_helper.ransomware_protection_status(media_agent.media_agent_id)
        driver_loaded = self.mm_helper.ransomware_driver_loaded(media_agent.media_agent_name)
        if protection_enabled and driver_loaded:
            self.log.info("Ransomware protection is enabled and driver loaded")
        elif (not driver_loaded) and protection_enabled:
            self.log.error("Anomalous Behaviour: Ransomware protection is enabled but the driver is not loaded")
            raise Exception("Anomalous Behaviour: Ransomware protection is enabled but the driver is not loaded")
        elif testcase_initial_check:
            self.log.error("Ransomware protection is not enabled by default. Treating as soft error")
        else:
            self.log.error("ransomware protection not Enabled correctly")
            self.error_flag += ['ransomware protection not Enabled properly']

    def disable_ransomware_protection_validations(self, media_agent):
        """Disable the ransomware protection and do the validations

        Args:
            media_agent             (MediaAgent):   MediaAgent Object
        """
        self.log.info("disabling ransomware protection intentionally on MA: [%s]", media_agent.media_agent_name)
        media_agent.set_ransomware_protection(False)
        self.log.info("waiting for 360 seconds...")
        time.sleep(360)

        self.log.info("Checking protection status for MA: [%s]", media_agent.media_agent_name)
        protection_enabled = self.mm_helper.ransomware_protection_status(media_agent.media_agent_id)
        driver_loaded = self.mm_helper.ransomware_driver_loaded(media_agent.media_agent_name)

        if (not protection_enabled) and (not driver_loaded):
            self.log.info("In csDB, entry was updated to denote disabled state")
            self.log.info("Driver was unloaded. Working as expected")
        elif driver_loaded and not protection_enabled:
            self.log.info("protection was disabled in DB.But the driver is still loaded")
            self.error_flag += [
                'the cvdlp driver was not unloaded in MA even when the protection was disabled']
        else:
            self.log.error("Anomalous behaviour :in csdb the protection is still enabled")
            self.error_flag += ['disabling of ransomware protection is not working correctly']

    def directory_creation_check(self, library_name, host_location, mount_location):
        """Validate directory creation in MP when it is not protected

        Args:
            library_name    (str):    name of the library

            host_location   (str):    host path to the MP

            mount_location  (str):    unc path to the MP
        """
        self.log.info("*** validate directory creation in MP when it is not protected ***")
        try:
            mp_location, mag_path, existing_folder = self.get_mp_directories(
                library_name, host_location, mount_location)

            new_directory_path_unc = self.media_agent_machine2.join_path(
                mag_path[1], f"z_{self.id}_test_direc_{str(time.time()).replace('.', '-')}")

            self.log.info("create new directory %s in mount path", new_directory_path_unc)
            self.media_agent_machine2.create_directory(new_directory_path_unc, force_create=True,
                                                       username=self.tcinputs.get("username"),
                                                       password=self.tcinputs.get("password"))
            # validate if creation of directory was successful
            new_directory_path = self.media_agent_machine1.join_path(
                mag_path[0], new_directory_path_unc.split(mag_path[1] + self.media_agent_machine2.os_sep)[1])
            if self.media_agent_machine1.check_directory_exists(new_directory_path):
                self.log.info("A temporary directory was successfully created.")
                self.log.info("Verified - protection was disabled.")
            else:
                raise Exception("directory creation did not occur")
        except Exception as exp:
            self.error_flag += ['directory creation was not successful when MP is not protected.']
            self.log.error("directory creation was not successful when MP is not protected.: %s", str(exp))

    def run(self):
        """Run function of this test case"""
        try:
            # remove pre-created resources if any
            self.cleanup_resources()

            # treating initial check as soft failure because automation setups alter it frequently
            self.check_ransomware_protection_enabled(self.media_agent_obj1, testcase_initial_check=True)
            self.check_ransomware_protection_enabled(self.media_agent_obj2, testcase_initial_check=True)
            self.log.info("turning on ransomware protection on MA's if not already enabled")
            self.media_agent_obj1.set_ransomware_protection(True)
            self.media_agent_obj2.set_ransomware_protection(True)

            self.log.info("setting interval minutes between disk space updates to 5 minutes")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
            self.log.info('wait for 360 seconds...')
            time.sleep(360)

            self.log.info('********* CASE 1: Protection against UNC Access on UNC MP *********')

            # create content, library with UNC MP, storage policy, subclient
            self.create_resources(host_machine=self.media_agent_machine1,
                                  media_agent_machine=self.media_agent_machine2,
                                  initial=True, create_count="1")

            self.validation_per_mount_path(library_name=f"{self.library_name}1",
                                           host_location=self.host_path, mount_location=self.mount_location,
                                           backup_job=True)

            self.log.info("--------------------------------------------------------")
            self.log.info("***** Disable ransomware protection and do validations *****")
            self.disable_ransomware_protection_validations(self.media_agent_obj2)
            # create directory and check. should be created as ransomware is off
            self.directory_creation_check(library_name=f"{self.library_name}1",
                                          host_location=self.host_path, mount_location=self.mount_location)

            # add new library - mount path - 2
            self.log.info("create a new mount path while ransomware protection is off")
            self.create_resources(host_machine=self.media_agent_machine1,
                                  media_agent_machine=self.media_agent_machine2, create_count="2")

            self.log.info("run a backup job on while protection is off")
            self.run_backup_job('FULL')

            self.log.info("--------------------------------------------------------")
            self.log.info("turning on ransomware protection back on MA: [%s]", self.media_agent_obj2.media_agent_name)
            self.media_agent_obj2.set_ransomware_protection(True)

            self.log.info("waiting for 360 seconds...")
            time.sleep(360)
            self.check_ransomware_protection_enabled(self.media_agent_obj2)
            self.log.info("checking ransomware protection validations on"
                          " existing mount path again after enabling protection")
            self.validation_per_mount_path(backup_job=False, library_name=f"{self.library_name}2",
                                           host_location=self.host_path, mount_location=self.mount_location)

            self.log.info('********* CASE 1 Completed *********')

            self.log.info('********* CASE 2: Protection against UNC Access on LocalMP *********')

            # Create the resources
            self.create_resources(host_machine=self.media_agent_machine1,
                                  media_agent_machine=self.media_agent_machine1,
                                  initial=False, create_count="3")
            # create directory and check. should be created as local mp is not protected against unc access
            self.directory_creation_check(library_name=f"{self.library_name}3",
                                          host_location=self.host_path, mount_location=self.mount_location)

            self.log.info("Sharing the MP with new MA[%s], mount Location [%s]",
                          self.media_agent_obj2.media_agent_name, self.mount_location)
            self.library.share_mount_path(new_media_agent=self.media_agent_obj2.media_agent_name,
                                          new_mount_path=self.mount_location,
                                          media_agent=self.media_agent_obj1.media_agent_name,
                                          mount_path=self.host_path, access_type=6,
                                          username=self.tcinputs.get('username'),
                                          password=self.tcinputs.get('password'))
            self.log.info("wait for 360 secs...")
            time.sleep(360)
            # now we expect the path to be protected as MP sharing is done
            self.validation_per_mount_path(backup_job=True, library_name=f"{self.library_name}3",
                                           host_location=self.host_path, mount_location=self.mount_location)

            self.log.info('********* CASE 2 Completed *********')
            if self.error_flag:
                # if the list is not empty then error was there, fail testcase
                self.log.error(self.error_flag)
                raise Exception(f"testcase failed: [{self.error_flag}]")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("Restoring defaults")
        if self.status != constants.FAILED:
            self.log.info("Enabling Ransomware Protection on both MAs")
            try:
                if not self.mm_helper.ransomware_protection_status(self.media_agent_obj1.media_agent_id):
                    self.media_agent_obj1.set_ransomware_protection(True)
                if not self.mm_helper.ransomware_protection_status(self.media_agent_obj2.media_agent_id):
                    self.media_agent_obj2.set_ransomware_protection(True)
            except Exception as exp:
                self.log.error("ERROR: %s", str(exp))
            # for all the testcase resources created in this run
            self.cleanup_resources()
        else:
            self.log.warning('******* TestCase Failed. Not CleaningUp the entities *******')
