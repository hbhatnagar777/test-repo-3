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

    setup()         --  setup function of this test case

    cleanup_resources() -- common function to remove the created resources of this testcase

    create_resources()   -- function to create the required objects /  resources for the testcase

    get_mp_directories()     --  It will return various mount path related directories
            required for folder manipulations in the testcase

    mount_path_protected_verify()   -- This will check if the mountpaths are being protected.
                                        Will attempt to write a file in the path location
                                        and then delete it.

    print_reasoning()  --  This function gets the output in a correct format

    is_driver_loaded_and_mountpath_protected()  --  this function checks if the cvdlp driver is
                                                loaded in MA and if the mount path is being
                                                properly protected (writes disabled)

    run_backup_job()   --  running a backup job depending on argument

    validation_per_mount_path()  --  This function will run validation and checks for the mount
                                    paths of this testcase.

    check_ransomware_protection_enabled()  --  this function validates if
            the ransomware protection is enabled properly or not initial
             check should be successful

    disable_ransomware_protection_validations()  --  disable the
    ransomware protection and do the validations

    directory_creation_check()  -- This function tries to create directory inside mount path
            when ransomware protection is turned off

    run()  --  Run function of this test case

    tear_down()  --  deletes all items of the testcase

basic idea of the test case:
Automate RansomWare Protection Feature Testcases for Mountpaths

validations used:
cases to be covered as mentioned in design doc.
1. NEW MOUNT PATH CREATION - make sure when mountpath is created that driver is loaded and
protecting that path.

2. RANSOMWARE DISABLE + DRIVER UNLOAD - confirm that disabling ‘ransomware protection’ from
GUI unloads the driver successfully.

3. RANSOMWARE ENABLE + DRIVER LOAD - Confirm that enabling ‘ransomware protection’ from GUI
loads the driver successfully and protects the path.

3.1 check for UNC path too(both type)

3.2 ransomware working verification will involve ->
 3.2.1 check if driver loads
 3.2.2 check if the registry is updated
 3.2.3 try writing a new file in the protected path – it should fail

prerequisites:
try to keep CS and MA machine separate
noticed instances of driver not being unloaded if CS and MA are on same machine.

input json file arguments required:
                            "ClientName": "required input"
                            "AgentName": "required input"
                            "MediaAgentName": "required input"
                            "base_path_ma": "optional"  -- needed to have a different path
                             for mount path location

Design steps:
1.	Remove pre – created resources if any.
2.	Check if ransomware protection on MA enabled – if not enabled then fail the
    testcase we expect it to be enabled by default on sp20 and sp20+.
    Get the registry values for the mount path currently protected.
3.	set the interval minutes between disk space updates to 5 minutes.
4.	Create resources - including multiple mount paths
5.	Check_driver_loaded_and_mountpath_protected (multiple mount paths without any content present),
    check if new mount paths added in registry.
6.	Create one more mount path.
7.	Check_driver_loaded_and_mountpath_protected (multiple mount paths after running small backups),
    check if new mount paths added in registry.
8.	Disable ransomware protection on MA. Check whether driver unloaded.
    Check in database if ransomware protection disabled.
9.	Try to create a new directory inside mount path location when protection was disabled.
10.	Create a new mount path while protection was disabled.
11.	Enable ransomware protection on MA. Check whether driver loaded.
    Check in database if ransomware protection enabled.
12.	Verify on existing mount path, verify on newly created mount path.
    -- end case here --- UNC path checks not included for now.
13.	Create mount path using UNC path (both types) and run the
 Check_driver_loaded_and_mountpath_protected checks
Run these checks once again on the existing mount paths added earlier.
14.	Delete all the resources of testcase in cleanup
 function + leave ransomware protection enabled in cleanup.
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

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = """Ransomware protection feature testcase for Mountpath"""
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.storage_policy_name = None
        self.storage_pool_name = None
        self.storage_pool = None
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
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.media_agent_anomaly = None
        self.job = None
        self.error_flag = None
        self.storage_entities = None
        self.media_agent_obj = None

    def setup(self):
        """
        assign values to variables for testcase
        check what sort of configuration should the testcase run for
        """
        # in linux, stop the testcase if ddb path is not provided

        self.storage_policy_name = str(self.id) + "_SP"
        self.storage_pool_name = str(self.id) + "_POOL"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.client)
        self.media_agent_machine = machine.Machine(
            self.tcinputs.get("MediaAgentName"), self.commcell)
        self.media_agent_obj = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName"))
        self.error_flag = []
        self.storage_entities = [[self.id+'_pool1', self.id+'_pool2',
                                  self.id+'_pool3', self.id+'_pool4'],
                                 [self.id+'_SP1', self.id+'_SP2',
                                  self.id+'_SP3', self.id+'_SP4']]

    def cleanup_resources(self):
        """
        Common function to remove the created resources of this testcase
        Removes -- (if exist)
                - Content directory
                - storage policy
                - backupset
                - Pool

        Args:
            None

        Returns:
            None
        """
        self.log.info("**************clean up resources***************")
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

            for sp_name in self.storage_entities[1]:
                if self.commcell.storage_policies.has_policy(
                        sp_name):
                    self.commcell.storage_policies.delete(sp_name)
                    self.log.info("storage policy deleted %s", sp_name)
                else:
                    self.log.info("storage policy does not exist %s", sp_name)

            for pool_name in self.storage_entities[0]:
                if self.commcell.storage_pools.has_storage_pool(pool_name):
                    self.commcell.storage_pools.delete(pool_name)
                    self.log.info("Storage Pool deleted %s", pool_name)
                else:
                    self.log.info("Storage Pool does not exist %s", pool_name)
            self.storage_entities = [[], []]
            # entities cleaned up

            self.log.info("clean up successful")

        except Exception as exp:
            self.log.error("cleanup failed with issue: %s", exp)

    def create_resources(
            self,
            initial=False,
            create_count=None):
        """
        function to create the required objects /  resources for the testcase
        Args:
            initial(bool)               --      if the create_resources function has been
                                                called the first time in the testcase

            create_count(str)           --      an additional variable used in the naming of
                                                the resources created for clarity every time
                                                create_resources function is called.

        Returns:
            None

        """

        if initial:
            # get the drive path with required free space
            drive_path_client = self.opt_selector.get_drive(
                self.client_machine)

            # base path ma option
            if self.tcinputs.get("base_path_ma"):
                drive_path_media_agent = self.tcinputs.get("base_path_ma")
            else:
                drive_path_media_agent = self.opt_selector.get_drive(
                    self.media_agent_machine)

            # creating testcase directory, mount path, content path, dedup
            # store path
            self.testcase_path_client = f"{drive_path_client}{self.id}"
            self.testcase_path_media_agent = f"{drive_path_media_agent}{self.id}"

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
                    self.client.client_name, self.content_path, 1, 1):
                self.log.info(
                    "generated content for subclient %s",
                    self.subclient_name)

        self.mount_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "mount_path_" + create_count)
        self.dedup_store_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "dedup_store_path_" + create_count)

        # create storage pool with mountpath as needed according to the testcase
        self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name + create_count, self.mount_path,
                                                            self.tcinputs.get("MediaAgentName"),
                                                            self.tcinputs.get("MediaAgentName"),
                                                            self.dedup_store_path)
        self.storage_entities[0].append(self.storage_pool_name + create_count)

        # create dependent SP
        self.storage_policy = self.commcell.storage_policies.add(
            storage_policy_name=self.storage_policy_name + create_count,
            global_policy_name=self.storage_pool_name + create_count)
        self.storage_entities[1].append(self.storage_policy_name + create_count)

        # point the existing subclient to newly created storage policy
        if initial:
            # create subclient and add subclient content
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name + create_count,
                self.content_path,
                self.agent)
        else:
            self.subclient.storage_policy = self.storage_policy_name + create_count
            self.log.info("storage policy of subclient %s changed to %s",
                          self.subclient_name,
                          self.storage_policy_name)

    def get_mp_directories(self, check_for_lib, path_to_location):
        """
        It will return various mount path related directories
        required for folder manipulations in the testcase.

        Args:
            check_for_lib(str)          --  name of the library

            path_to_location(str)       --  path to main mount path folder

        Returns:
            mount_path_location, physical_path, existing_folder

        """
        # get the physical mount path location from csdb
        query = f"""select      MountPathName
                    from        mmmountpath MM, MMLibrary ML
                    where       MM.LibraryId=ML.LibraryId
                    and         ML.AliasName='{check_for_lib}'"""
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        mount_path_location = self.csdb.fetch_one_row()[0]
        mount_path_location = self.media_agent_machine.join_path(
            path_to_location, mount_path_location)
        self.log.info("location of mount path is %s", mount_path_location)
        # going to cv_magnetic folder inside mount path where volumes are kept
        time.sleep(10)
        physical_path = self.media_agent_machine.get_folders_in_path(mount_path_location,
                                                                     recurse=False)[0]
        # physical_path = self.media_agent_machine.join_path(mount_path_location, "CV_MAGNETIC")
        self.log.info("path to contents of mount path is %s", physical_path)
        existing_folder = self.media_agent_machine.get_folders_in_path(physical_path,
                                                                       recurse=False)
        self.log.info("path to existing folder is %s", existing_folder)
        return mount_path_location, physical_path, existing_folder

    def mount_path_protected_verify(self, check_for_lib, path_to_location, service_restart_needed):
        """
        This will check if the mountpaths are being protected.
        Will attempt to write a file in the path location
        and then delete it.

        Args:
            check_for_lib(str)              --      name of the library for whose mount
                                                    path we are verifying

            path_to_location(str)           --      path to the main folder of the mount path

            service_restart_needed(bool)    --      in case of testing, when you don't
                                                    want to wait for whole disk
                                                    space update interval, then you
                                                    can set it to TRUE to fasten the process
                                                    of getting the setting change
                                                    in effect.

        Returns:
             protection working or not [bool]

             dictionary with reasoning if not working
                dictionary with only mount path location if working as intended
        """

        mount_path_location, physical_path, existing_folder = self.get_mp_directories(
            check_for_lib, path_to_location)

        # service restart
        # replace later with wait time
        # single instanced machine
        # restart part kept for testing / debugging purposes
        if service_restart_needed:
            self.log.info("Restarting the media mount manager service...")
            self.client.restart_service(service_name="GxMMM(Instance001)")
            time.sleep(5)
            self.log.info("Media mount manager service restarted")

        protection_working = False
        manipulation_failed = {"mount_path_location": physical_path}

        # making sure existing folder is not being removed
        # in case backups not written to the mount path - existing_folder will be empty
        if len(existing_folder) != 0:
            try:
                # try to delete an existing folder inside CV_magnetic
                # in mount path
                self.media_agent_machine.modify_ace('Everyone', existing_folder[0], 'Delete',
                                                    'Deny', remove=True, folder=True)
                self.log.info("Deny delete permission removed from %s", existing_folder[0])
                self.media_agent_machine.remove_directory(existing_folder[0])
                manipulation_failed["existing_folder_removal"] = "existing folder was removed" \
                                                                 " from inside mount path" \
                                                                 " - ransomware protection NOT " \
                                                                 "properly working"
                self.log.error("existing folder was removed inside mount path")
            except Exception as exp:
                if "cannot remove item" in str(exp).lower() and "write protected" in str(exp):
                    protection_working = True
                    self.log.info("existing folder removal failed as "
                                  "expected for %s", existing_folder[0])
                else:
                    manipulation_failed["existing_folder_removal"] = str(exp)

        try:
            # try to create a new folder there with overwriting existing folder option enabled
            # when ransomware protection working properly, new folder should
            # not be created
            temp_direc = self.media_agent_machine.join_path(
                physical_path, f"z_{self.id}_test_direc_{str(time.time()).replace('.', '-')}")
            # time stamp
            if self.media_agent_machine.check_directory_exists(temp_direc):
                self.log.info("%s directory exists in %s", temp_direc, physical_path)
                self.media_agent_machine.modify_ace('Everyone', temp_direc, 'Delete', 'Deny',
                                                    remove=True, folder=True)
                self.log.info("Deny delete permission removed from %s", temp_direc)
            self.log.info("create new directory %s in mount path", temp_direc)
            self.media_agent_machine.create_directory(temp_direc, force_create=True)
            #
            # validate if creation of directory was successful
            if self.media_agent_machine.check_directory_exists(temp_direc):
                self.log.error(
                    "creation of directory was successful - this should not"
                    " have occurred - create directory problem")

            # from future runs keep a note if this part is
            # skipped due to improper working of automation
            # function - meaning create_directory and remove_directory
            # both skip and dont raise
            # any exception - it will appear as if this case
            # was passing but nothing was created.

            # try to delete the newly added directory
            self.media_agent_machine.remove_directory(temp_direc)
            manipulation_failed["creating_new_directory"] = "new directory creation and" \
                                                            " removal inside mount path folder" \
                                                            " was successful " \
                                                            "- ransomware protection " \
                                                            "not working properly"
            protection_working = protection_working and False
            self.log.info("new directory creation and removal"
                          " inside mount path folder was successful")

        except Exception as exp:
            # we are only looking at the creation part
            # directory removal checked above
            # creation should not be possible
            if "New-Item : The media is write protected" in str(exp):
                self.log.info("creation of new directory %s inside "
                              "mount path location failed",
                              temp_direc)
                if len(existing_folder) == 0:
                    protection_working = True
                else:
                    protection_working = protection_working and True
            else:
                manipulation_failed["creating_new_directory"] = str(exp)
                protection_working = protection_working and False

        self.log.info("protection working is %s", protection_working)
        return protection_working, manipulation_failed

    def print_reasoning(self, reasoning):
        """
        This function gets the output in a correct format.
        Args:
            Reasoning - dictionary - contains key, value pairs depicting the
                                     problems encountered if any during the
                                     protection validation checks above.

        Returns:
             A string with the reasoning behind mount path
             ransomware protection check failure.
        """
        usable_key_set = [key for key in reasoning.keys() if key != "mount_path_location"]
        self.log.info("Reasoning is -")
        for key in usable_key_set:
            self.log.info("%s -- %s", key, reasoning[key])

    def is_driver_loaded_and_mountpath_protected(self,
                                                 check_for_lib,
                                                 path_to_location,
                                                 service_restart_needed,
                                                 repeat_check):
        """
            This function checks if the cvdlp driver is
            loaded in MA and if the mount path is being
            properly protected (writes disabled)

        Args:
            check_for_lib(str)              --      name of the library for whose
                                                    mount path we are verifying

            path_to_location(str)           --      path to the main folder of
                                                    the mount path

            service_restart_needed(bool)    --      in case of testing, when you don't want
                                                    to wait for whole disk space update
                                                    interval, then you can set it to TRUE to
                                                    fasten the process of getting the
                                                    setting change in effect.

            repeat_check(bool)              --      to mark the logging for
                                                    "in the repeated check after
                                                     enabling ransomware protection"

        Returns:
                None
        """

        # call machine class driver loaded function from here
        # name differing --> check_driver_working
        # call mount path protected verify function here
        driver_loaded = self.mm_helper.ransomware_driver_loaded(
            self.commcell.clients.get(self.tcinputs.get("MediaAgentName")))
        mount_path_protected, reasoning = self.mount_path_protected_verify(
            check_for_lib, path_to_location, service_restart_needed)
        if driver_loaded and mount_path_protected:
            self.log.info(
                "the driver is loaded and the mount path in library %s is being properly "
                "protected by ransomware protection", check_for_lib)
            self.log.info("mount path: %s", reasoning["mount_path_location"])
            self.log.info("------------------------------------------------")
        elif not mount_path_protected:
            self.log.error(
                "the mount path is not being protected properly: %s",
                reasoning["mount_path_location"])
            self.print_reasoning(reasoning)
            if repeat_check:
                self.error_flag += [
                    f'directory manipulation was allowed for'
                    f' mount path {reasoning["mount_path_location"]}'
                    f'in the repeated check after enabling ransomware protection']
            else:
                self.error_flag += [
                    f'directory manipulation was allowed for'
                    f' mount path {reasoning["mount_path_location"]}']
        elif not driver_loaded:
            self.log.error("CVDLP driver is not loaded")
            self.error_flag += ["CVDLP driver not loaded"]

    def run_backup_job(self, job_type):
        """
        running a backup job depending on argument

        Args:
            job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)

        Returns:
            job object

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
            backup_job=True,
            service_restart_needed=False,
            repeat_check=False):
        """
        This function will run validation and checks for the mount paths
        of this testcase.
        Will involve -
                    1. FULL backup job run on mount path
                    2. Check_driver_loaded_and_mountpath_protected

        Args:
            check_for_lib(str)              --      name of the library for whose mount
                                                    path we are verifying

            path_to_location(str)           --      path to the main folder of
                                                    the mount path

            backup_job(bool)                --      True    if backup job needs to be run
                                                            when this function is called.

                                                    False   if backup job is NOT NEEDED to
                                                            be run when this function
                                                            is called.
                                                    default - True

            service_restart_needed(bool)    --      in case of testing, when you don't
                                                    want to wait for whole disk
                                                    space update interval, then you can
                                                    set it to TRUE to fasten the process
                                                    of getting the setting change
                                                    in effect.
                                                    default - False

            repeat_check(bool)              --      to mark the logging for
                                                    "in the repeated check after
                                                     enabling ransomware protection"
                                                    default - False

        Returns:
            None

        """
        if backup_job:
            self.run_backup_job("FULL")
        self.is_driver_loaded_and_mountpath_protected(
            check_for_lib, path_to_location, service_restart_needed, repeat_check)

    def check_ransomware_protection_enabled(self, testcase_initial_check=False):
        """
        This function validates if the ransomware protection is enabled properly or not
        initial check should be successful.

        Args:
            testcase_initial_check(bool)    --      True if the function is doing the
                                                    check first time in the testcase, we
                                                    are expecting the ransomware protection
                                                    to be 'ON' by default in the initial check.
                                                    This option helps to give clearer logging.
                                                    default - False
        Returns:
            None
        """
        protection_enabled = self.mm_helper.ransomware_protection_status(
            self.commcell.clients.get(self.tcinputs.get("MediaAgentName")).client_id)
        driver_loaded = self.mm_helper.ransomware_driver_loaded(
            self.commcell.clients.get(self.tcinputs.get("MediaAgentName")))
        if protection_enabled and driver_loaded:
            self.log.info("Ransomware protection is enabled and driver loaded")
        elif (not driver_loaded) and protection_enabled:
            self.log.error(
                "Anomalous Behaviour: Ransomware protection is enabled "
                "but the driver is not loaded")
            raise Exception(
                "In csDB ransomware protection is enabled but cvdlp"
                "driver is not loaded: Please check "
                "the driver manually")
        elif testcase_initial_check:
            self.log.info("Ransomware protection is not enabled")
            self.log.error(
                "Ransomware protection is expected to be enabled by default in"
                " sp20 and sp20+ versions on windows. Treating it as soft failure")
        else:
            self.log.error("ransomware protection not Enabled correctly")
            self.error_flag += ['ransomware protection not Enabled properly']

    def disable_ransomware_protection_validations(self):
        """
        Disable the ransomware protection and do the validations

        Args:
            None

        Returns:
            None
        """
        protection_enabled = self.mm_helper.ransomware_protection_status(
            self.commcell.clients.get(self.tcinputs.get("MediaAgentName")).client_id)
        driver_loaded = self.mm_helper.ransomware_driver_loaded(
            self.commcell.clients.get(self.tcinputs.get("MediaAgentName")))
        if (not protection_enabled) and (not driver_loaded):
            self.log.info("Driver was unloaded")
            self.log.info(
                "In csDB, entry was updated to denote disabled state")
            self.log.info("Working as expected")
        elif driver_loaded and not protection_enabled:
            self.log.info("protection was disabled in DB")
            self.log.info("the driver is still loaded")
            self.error_flag += [
                'the cvdlp driver was not unloaded in MA even when the protection was disabled']
        else:
            self.log.error(
                "Anomalous behaviour :in csdb the protection is still enabled")
            self.error_flag += ['disabling of ransomware protection is not working correctly']

    def directory_creation_check(self, check_for_lib, path_to_location):
        """
        This function tries to create directory inside mount path
         when ransomware protection is turned off.

        Args:
            check_for_lib(str)              --      name of the library for whose mount path we are
                                                    verifying

            path_to_location(str)           --      path to the main folder of the mount path

        Returns:
            None

        """

        try:
            mount_path_location, physical_path, existing_folder = self.get_mp_directories(
                check_for_lib,
                path_to_location)

            temp_direc = self.media_agent_machine.join_path(
                physical_path, f"create_test_{self.id}_{str(time.time()).replace('.', '-')}")
            self.media_agent_machine.create_directory(temp_direc)
            if self.media_agent_machine.check_directory_exists(temp_direc):
                self.log.info("A temporary directory was successfully created.")
                self.log.info("Verified - protection was disabled.")
            else:
                raise Exception("directory creation did not occur")
        except Exception as exp:
            self.error_flag += ['directory creation while protection disabled was not successful.']
            self.log.error("the directory was not created even though protection was off: %s", exp)

    def run(self):
        """Run function of this test case"""
        try:
            # remove pre-created resources if any
            self.cleanup_resources()

            # enable RWP as previous TCs may have disabled it
            if self.media_agent_machine.os_info.lower() == 'windows':
                self.log.info('Enabling Ransomware protection on MA')
                self.commcell.media_agents.get(
                    self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
                self.log.info("Successfully enabled Ransomware protection on MA")
            self.log.info("sleeping 30 secs to allow RWP to get enabled")
            time.sleep(30)

            self.check_ransomware_protection_enabled(testcase_initial_check=True)

            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
            self.log.info("interval minutes between disk space updates set to 5 minutes")

            self.log.info('***** Case 1: Validating without any backup content present on mount path *****')
            # 1 mount - 1 library - 1 storage policy (association to be followed)
            # maintain single subclient with same content throughout
            # only change the storage policy to run backup on a different mount path
            self.create_resources(initial=True, create_count="1")
            self.log.info('Sleeping for 60 seconds...')
            time.sleep(60)

            first_mount_path = self.mount_path
            self.validation_per_mount_path(backup_job=False,
                                           check_for_lib=self.storage_pool_name + "1",
                                           path_to_location=self.mount_path)

            self.log.info("--------------------------------------------------------")
            self.log.info("***** Case 2: Validating with backup content present on mount path *****")
            # new mount path, library, storage policy created - associated to existing subclient
            self.create_resources(create_count="2")
            self.log.info('Sleeping for 60 seconds...')
            time.sleep(60)
            self.validation_per_mount_path(check_for_lib=self.storage_pool_name + "2",
                                           path_to_location=self.mount_path)
            second_path = self.mount_path

            self.log.info("--------------------------------------------------------")
            self.log.info("***** Case 3: Disable ransomware protection and do validations *****")
            self.media_agent_obj.set_ransomware_protection(False)
            self.log.info("ransomware protection disabled intentionally")
            self.log.info("waiting for 10 mins...")
            time.sleep(10 * 60)
            self.disable_ransomware_protection_validations()
            # create directory and check
            self.directory_creation_check(check_for_lib=self.storage_pool_name + "1",
                                          path_to_location=first_mount_path)

            self.log.info("--------------------------------------------------------")
            # add new library - mount path - 3
            self.log.info("***** Case 4: Create a new mount path while ransomware protection is off *****")
            self.create_resources(create_count="3")
            # storage policy of subclient also shifted to the one with 3rd mount path

            self.log.info("run a backup job on while protection is off")
            self.run_backup_job('FULL')

            self.log.info("--------------------------------------------------------")
            self.log.info("turning ransomware protection back on")
            self.media_agent_obj.set_ransomware_protection(True)
            self.log.info("disk space update interval was set to 5 minutes earlier")
            self.log.info("wait for 10 min...")
            time.sleep(10*60)
            self.check_ransomware_protection_enabled()
            self.log.info("checking ransomware protection validations on"
                          " existing mount path again after enabling protection")
            self.validation_per_mount_path(check_for_lib=self.storage_pool_name + "2",
                                           path_to_location=second_path, backup_job=False,
                                           # service_restart_needed=True,
                                           repeat_check=True)
            self.log.info(" checking ransomware protection for existing mount path "
                          "added while protection was disabled")
            self.validation_per_mount_path(check_for_lib=self.storage_pool_name + "3",
                                           path_to_location=self.mount_path,
                                           # service_restart_needed=True,
                                           repeat_check=False)

            if self.error_flag:
                # if the list is not empty then error was there, fail testcase
                self.log.error(self.error_flag)
                raise Exception("testcase failed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """deletes all items of the testcase"""
        self.log.info("*********************************************")
        self.log.info("Restoring defaults")
        # enable the ransomware protection on MA
        try:
            if not self.mm_helper.ransomware_protection_status(self.commcell.clients.get(
                    self.tcinputs.get("MediaAgentName")).client_id):
                self.media_agent_obj.set_ransomware_protection(True)

            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 30)
            self.log.info("interval minutes between disk space updates set to 30 minutes")

        except Exception as exp:
            self.log.info("Error in restoring the default state")
            self.log.error("ERROR: %s", exp)

        # for all the testcase resources created in this run
        self.cleanup_resources()
