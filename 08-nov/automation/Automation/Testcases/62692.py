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
    __init__()           --  Initializes test case class object

    setup()              --  Setup function of this test case

    cleanup_resources()  -- Removes the created resources of this testcase

    testcase_based_lib() -- Create library here according to the mount path need in the testcase

    create_resources()   -- Create the required objects / resources for the testcase

    get_directories()    -- Return Paths to directories inside the Test Location
                            required for folder manipulations in the TC

    verify_path_protection()               -- Check if the path is being protected

    is_driver_loaded_and_path_protected()  --  Check if the cvdlp driver is loaded in MA and
                                               if the Path is being properly protected (writes disabled)

    run_backup_job()                       --  Run a backup job of specified type and wait till it is completed

    check_ransomware_protection_enabled()  --  Validate if the ransomware protection is enabled properly or not.
                                               Initial check should be successful.

    get_mountpath_info()  --  Get the MountPath Id, Name from LibraryId

    run()                 --  Run function of this test case

    tear_down()           --  deletes all items of the testcase

prerequisites:
try to keep CS and MA machine separate
noticed instances of driver not being unloaded if CS and MA are on same machine.

TcInputs to be passed in JSON File:
        "62692": {
            "ClientName": "Name of Client",
            "AgentName": "File System",
            "MediaAgentName": "Name of Media Agent",  // resources(MP/DDB) will be create initially here
            "NewMAName": "Name of new Machine",       // MA will be installed on it and resources will be Moved
            "username": "required input",             // Access credentials for accessing the new machine
            "password": "required input"
        }
Steps:

1.  Check Ransomware is enabled by Default on the existing MA

** CASE 1 **
2.  Create Resources with MP hosted on existing MA

3.  Install MA Package on the New Machine provided

4.  Run Move MountPath Job to the new MA

5.  Verify that Ransomware is enabled and MP is protected on new MA after Move Operation

6.  CleanUp: Delete the SP, Library and Uninstall the New MA

** CASE 2 **
7.  Create Resources with DDB hosted on existing MA

8. Install MA Package on the New Machine provided

9:  Run Move DDB Partition Job to the new MA

10: Verify that Ransomware is enabled and DDB Path is protected on new MA after Move Operation

11: CleanUp: Delete the SP, Library and Uninstall the New MA
"""

import time
from base64 import b64encode
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures

from MediaAgents.MAUtils import mahelper
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = """Ransomware protection feature testcase for MoveMP and MoveDDB to new MA"""
        self.tcinputs = {
            "MediaAgentName": None,
            "NewMAName": None,
            "username": None,
            "password": None
        }
        self.content_path = None
        self.library_prefix = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_policy_prefix = None
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

        self.library_prefix = str(self.id) + "_lib"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.storage_policy_prefix = str(self.id) + "_SP"

        self.client_machine = machine.Machine(self.client)
        self.media_agent_machine1 = machine.Machine(self.tcinputs.get("MediaAgentName"), self.commcell)
        self.media_agent_machine2 = machine.Machine(self.tcinputs.get("NewMAName"), self.commcell,
                                                    self.tcinputs.get('username'), self.tcinputs.get('password'))

        self.media_agent_obj1 = self.commcell.media_agents.get(self.tcinputs.get("MediaAgentName"))

        # get the drive path with required free space
        drive_path_client = self.opt_selector.get_drive(self.client_machine)
        self.testcase_path_client = self.client_machine.join_path(drive_path_client, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine1)
        self.testcase_path_media_agent = self.media_agent_machine1.join_path(drive_path_media_agent, f'test_{self.id}')

        drive_path_new_ma = self.opt_selector.get_drive(self.media_agent_machine2)
        self.testcase_path_new_ma = self.media_agent_machine2.join_path(drive_path_new_ma, f'test_{self.id}')

        self.error_flag = []

        self.mm_helper = mahelper.MMHelper(self)
        self.dedup_helper = mahelper.DedupeHelper(self)

    def cleanup_resources(self):
        """Removes the created resources of this testcase
        Removes -- (if exist)
                - Content directory
                - BackupSet, Storage Policies, Libraries
        """
        self.log.info("************** Clean up Resources ***************")
        try:
            self.log.info("Deleting Content directory if exist.")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            self.log.info("Deleting BackupSet, SPs, Libraries If Exists")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("BackupSet[%s] deleted", self.backupset_name)

            for sp_suffix in range(1, 3):
                if self.commcell.storage_policies.has_policy(f'{self.storage_policy_prefix}{sp_suffix}'):
                    self.commcell.storage_policies.delete(f'{self.storage_policy_prefix}{sp_suffix}')
                    self.log.info("Storage Policy[%s] deleted", f'{self.storage_policy_prefix}{sp_suffix}')

            for lib_suffix in range(1, 3):
                if self.commcell.disk_libraries.has_library(f'{self.library_prefix}{lib_suffix}'):
                    self.commcell.disk_libraries.delete(f'{self.library_prefix}{lib_suffix}')
                    self.log.info("Library[%s] deleted", f'{self.library_prefix}{lib_suffix}')
            self.log.info("************** Clean up Successful **************")
        except Exception as exp:
            self.log.error("************** Cleanup Failed with issue: %s **************", exp)

    def install_new_ma(self):
        """Installs CV on new machine with MA package

        Returns:
            (Client, MediaAgent): Client, MediaAgent objects for new MA
        """
        self.log.info('Installing new MA on [%s]', self.tcinputs.get("NewMAName"))
        job = self.commcell.install_software(client_computers=[self.tcinputs.get("NewMAName")],
                                             windows_features=[WindowsDownloadFeatures.MEDIA_AGENT.value],
                                             username=self.tcinputs.get('username'),
                                             password=b64encode(self.tcinputs.get('password').encode()).decode())
        self.log.info("Install Job(Id: %s)", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Install Job(Id: {job.job_id}) Failed[JPR: {job.delay_reason}]")
        self.log.info("Install Job(Id: %s) Completed", job.job_id)
        self.commcell.refresh()
        if not self.commcell.clients.has_client(self.tcinputs.get("NewMAName")):
            raise Exception("Install Job Completed but no client is present")
        self.log.info("Verified that Client is present after Install Job")

        new_client = self.commcell.clients.get(self.tcinputs.get("NewMAName"))
        return new_client, self.commcell.media_agents.get(new_client.client_name)

    def clean_uninstall_ma(self, client):
        """Uninstall MA and Retire Client

        Args:
            client    (Client):  Object of client which needs to be retired
        """
        self.log.info('Re-Associating the subclient and deleting the SP, Library if Exists')
        if self.storage_policy is not None:
            self.storage_policy.reassociate_all_subclients()
            self.commcell.storage_policies.delete(self.storage_policy.storage_policy_name)
        if self.library is not None:
            self.commcell.disk_libraries.delete(self.library.library_name)

        self.log.info('Retiring the client: %s', client.client_name)
        job = client.retire()
        self.log.info("Uninstall Job(Id: %s)", job.job_id)
        if not job.wait_for_completion():
            raise Exception(f"Uninstall Job(Id: {job.job_id}) Failed[JPR: {job.delay_reason}]")
        self.log.info("Uninstall Job(Id: %s) Completed", job.job_id)
        self.commcell.refresh()
        if self.commcell.clients.has_client(self.tcinputs.get("NewMAName")):
            raise Exception("Uninstall Job Completed but client is present")
        self.log.info("Verified that Client is Deleted after Uninstall Job")

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
        # create library
        if unc_path:
            library = self.mm_helper.configure_disk_library(
                lib_name,
                media_agent,
                mount_path,
                self.tcinputs.get("username"),
                self.tcinputs.get("password"))
        else:
            library = self.mm_helper.configure_disk_library(
                lib_name, media_agent, mount_path)
        return library

    def create_resources(self, initial=False, create_count=None):
        """Create the required objects / resources for the testcase

        Args:
            initial     (bool): if the create_resources function has been
                                called the first time in the testcase

            create_count(str):  an additional variable used in the naming of
                                the resources created for clarity every time
                                create_resources function is called.
        """
        self.log.info("*** Creating required resources for the case. MA:[%s] ***",
                      self.media_agent_machine1.machine_name)
        # create Library
        self.mount_path = self.media_agent_machine1.join_path(self.testcase_path_media_agent,
                                                              f"mount_path_{create_count}")
        if not self.media_agent_machine1.check_directory_exists(self.mount_path):
            self.media_agent_machine1.create_directory(self.mount_path)
        self.library = self.testcase_based_lib(f"{self.library_prefix}{create_count}",
                                               self.media_agent_machine1.machine_name, self.mount_path, unc_path=False)

        # create SP
        dedup_store_path = self.media_agent_machine1.join_path(self.testcase_path_media_agent,
                                                               f"dedup_store_path_{create_count}")
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            storage_policy_name=f"{self.storage_policy_prefix}{create_count}",
            library_name=f"{self.library_prefix}{create_count}", ma_name=self.media_agent_machine1.machine_name,
            ddb_path=dedup_store_path, ddb_ma_name=self.media_agent_machine1.machine_name)

        if initial:
            self.opt_selector.create_uncompressable_data(self.client.client_name, self.content_path,
                                                         size=1, num_of_folders=1, delete_existing=True)
            self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name, self.subclient_name, f"{self.storage_policy_prefix}{create_count}",
                self.content_path, self.agent)
        else:
            # point the existing subclient to newly created storage policy
            self.subclient.storage_policy = f"{self.storage_policy_prefix}{create_count}"
            self.log.info("storage policy of subclient %s changed to %s",
                          self.subclient_name, f"{self.storage_policy_prefix}{create_count}")

    def get_directories(self, test_location):
        """Return Paths to directories inside the Test Location required for folder manipulations in the TC

        Args:
            test_location   (str):  path to main mount path folder
        Returns:
            (str, str, str): (lvl1_child_dir, lvl2_child_dir, lvl3_child_dir)
        """
        # get the mount path/CV_SIDB folder
        lvl1_child_dir = self.media_agent_machine2.get_folders_in_path(test_location, recurse=False)[0]
        self.log.info("location of mount path/CV_SIDB is [%s]", lvl1_child_dir)
        # get cv_magnetic folder/2 folder
        lvl2_child_dir = self.media_agent_machine2.get_folders_in_path(lvl1_child_dir, recurse=False)[0]
        self.log.info("Location of CV_MAGNETIC/2 folder is [%s]", lvl2_child_dir)
        # get volume/sidb store folder
        lvl3_child_dir = self.media_agent_machine2.get_folders_in_path(lvl2_child_dir, recurse=False)[0]
        self.log.info("Location of Volumes/Store Folder is [%s]", lvl3_child_dir)

        return lvl1_child_dir, lvl2_child_dir, lvl3_child_dir

    def verify_path_protection(self, test_location, validation_type):
        """Check if the path is being protected.
        Will attempt to write a file in the Path location and then delete it.

        Args:
            test_location   (str):  path to the main folder of the mount path

            validation_type (int):  (1/2)-(MP/DDB) Validation
        Returns:
             (bool):  bool - protection working or not
        """
        self.log.info("*** Fetching Path Details and verifying if it protected or not ***")
        lvl1_child_dir, lvl2_child_dir, lvl3_child_dir = self.get_directories(test_location)

        protection_working = False
        manipulation_failed = {"test_location": test_location}  # used for error summarizing

        self.log.info("Attempting alterations from new MA[%s]", self.media_agent_machine2.machine_name)
        try:
            if validation_type == 1:
                # remove delete deny ace for existing folder(volumes) in MP
                self.media_agent_machine2.modify_ace('Everyone', lvl3_child_dir,
                                                     'DeleteSubdirectoriesAndFiles', 'Deny',
                                                     remove=True, folder=True)
                self.media_agent_machine2.modify_ace('Everyone', lvl3_child_dir, 'Delete',
                                                     'Deny', remove=True, folder=True)
                self.log.info("Deny delete permission removed from %s", lvl3_child_dir)
            # try to delete an existing folder in the Path
            self.media_agent_machine2.remove_directory(lvl3_child_dir)
            # below code path should not be touched ideally as remove directory should fail
            manipulation_failed["existing_folder_removal"] = "existing folder was removed" \
                                                             " - ransomware protection NOT properly working"
            self.log.error("existing folder was removed inside mount path")
        except Exception as exp:
            if "cannot remove item" in str(exp).lower() and "write protected" in str(exp).lower():
                protection_working = True
                self.log.info("existing folder removal failed as expected for %s", lvl3_child_dir)
            else:
                manipulation_failed["existing_folder_removal"] = str(exp)

        try:
            # try to create a new directory with overwriting existing folder option enabled
            new_directory_path = self.media_agent_machine2.join_path(
                lvl2_child_dir, f"z_{self.id}_test_direc_{str(time.time()).replace('.', '-')}")

            self.log.info("create new directory %s in path", new_directory_path)
            self.media_agent_machine2.create_directory(new_directory_path, force_create=True)

            # below code path should not be touched ideally as create directory should fail
            # validate if creation of directory was successful
            if self.media_agent_machine2.check_directory_exists(new_directory_path):
                self.log.error("creation of directory was successful - this should not"
                               " have occurred - create directory problem")

            manipulation_failed["creating_new_directory"] = "new directory creation was successful " \
                                                            "- ransomware protection not working properly"
            protection_working = protection_working and False
        except Exception as exp:
            if "new-item : the media is write protected" in str(exp).lower():
                self.log.info("creation of new directory %s inside mount path location failed", new_directory_path)
                protection_working = protection_working and True
            else:
                manipulation_failed["creating_new_directory"] = str(exp)
                protection_working = protection_working and False

        self.log.info("Is protection working? : %s", protection_working)
        if not protection_working:
            self.log.error("Error Summary [%s]: ", manipulation_failed)
        return protection_working

    def is_driver_loaded_and_path_protected(self, test_location, validation_type):
        """Check if the cvdlp driver is loaded in MA and if the Path is being properly protected (writes disabled)

        Args:
            test_location   (str):  path to the main folder of the MP/DDB

            validation_type (int):  (1/2)-(MP/DDB) Validation
        """
        self.log.info("***** Check if driver is loaded on MA[%s] and Path[%s] is protected *****",
                      self.media_agent_obj2.media_agent_name, test_location)
        # check if driver is loaded
        driver_loaded = self.mm_helper.ransomware_driver_loaded(
            self.commcell.clients.get(self.media_agent_obj2.media_agent_name))
        # check if path is protected
        mount_path_protected = self.verify_path_protection(test_location, validation_type)

        if driver_loaded and mount_path_protected:
            self.log.info(
                "the driver is loaded and the location is being properly protected by ransomware protection")
        elif not mount_path_protected:
            self.log.error("the location is not being protected properly: %s", test_location)
            self.error_flag += [f'directory manipulation was allowed for path {test_location}']
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
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Job {0} Failed with JPR: {1}".format(job.job_id, job.delay_reason))
        self.log.info("Job %s completed", job.job_id)
        return job

    def check_ransomware_protection_enabled(self, media_agent, testcase_initial_check=False):
        """Validate if the ransomware protection is enabled properly or not. Initial check should be successful.

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

    def get_mountpath_info(self, library_id):
        """Get the MountPath Id, Name from LibraryId

        Args:
            library_id (int):   Library Id
        Returns:
            (int, str):  MountPath Id, MountPath Name Tuple for the given Library id
        """
        query = """ SELECT	MM.MountPathId, MM.MountPathName
                    FROM	MMMountPath MM
                    WHERE	MM.LibraryId = {0}""".format(library_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", result[0])
        if result[0] != ['']:
            return int(result[0]), result[1]

    def run(self):
        """Run function of this test case"""
        try:
            # remove pre-created resources if any
            self.cleanup_resources()
            # uninstall ma if not cleaned from older run
            if self.commcell.clients.has_client(self.tcinputs.get("NewMAName")):
                self.clean_uninstall_ma(self.commcell.clients.get(self.tcinputs.get("NewMAName")))
            # treating initial check as soft failure because automation setups alter it frequently
            self.check_ransomware_protection_enabled(self.media_agent_obj1, testcase_initial_check=True)
            # set the interval minutes between disk space updates to 5 minutes
            self.log.info("setting interval minutes between disk space updates to 5 minutes")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)

            self.log.info("**************** CASE 1: Move MP to New MA ****************")

            self.create_resources(initial=True, create_count='1')
            self.run_backup_job('FULL')

            self.log.info("Install new MA, get MA Object, MP details for Move MP Job")
            new_client, self.media_agent_obj2 = self.install_new_ma()
            mp_id, mp_name = self.get_mountpath_info(self.library.library_id)
            self.log.info("Initiating MoveMP Job")
            job = self.library.move_mountpath(mp_id, self.media_agent_machine1.join_path(self.mount_path, mp_name),
                                              int(self.media_agent_obj1.media_agent_id),
                                              self.media_agent_machine2.join_path(self.testcase_path_new_ma, 'MovedMP'),
                                              int(self.media_agent_obj2.media_agent_id))
            self.log.info("Move Mount Path Job(Id: %s)", job.job_id)
            if not job.wait_for_completion():
                raise Exception(f"Move Mount Path Job(Id: {job.job_id}) Failed[JPR: {job.delay_reason}]")
            self.log.info("Move Mount Path Job(Id: %s) Completed", job.job_id)

            self.log.info("waiting for 360 seconds...[as we set the mmconfig to 5 min]")
            time.sleep(360)
            self.check_ransomware_protection_enabled(self.media_agent_obj2, testcase_initial_check=False)
            self.is_driver_loaded_and_path_protected(
                self.media_agent_machine2.join_path(self.testcase_path_new_ma, 'MovedMP'), 1)

            self.log.info('***** Validations Completed for Case 1. Cleaning Up *****')

            # uninstall MA and retire client
            self.clean_uninstall_ma(new_client)

            self.log.info("**************** CASE 2: Move DDB to New MA ****************")

            self.create_resources(initial=False, create_count='2')
            self.run_backup_job('FULL')

            self.log.info("Install new MA, get MA object, Store object, dest. DDB path details for Move DDB Operation")
            new_client, self.media_agent_obj2 = self.install_new_ma()

            engine = self.commcell.deduplication_engines.get(f'{self.storage_policy_prefix}2', 'Primary')
            store = engine.get(engine.all_stores[0][0])
            # move DDB to new MA
            if not self.media_agent_machine2.check_directory_exists(
                    self.media_agent_machine2.join_path(self.testcase_path_new_ma, 'MovedDDB')):
                self.media_agent_machine2.create_directory(
                    self.media_agent_machine2.join_path(self.testcase_path_new_ma, 'MovedDDB'), force_create=True)
            job = store.move_partition(
                substoreid=store.all_substores[0][0],
                dest_path=self.media_agent_machine2.join_path(self.testcase_path_new_ma, 'MovedDDB'),
                dest_ma_name=self.media_agent_obj2)
            self.log.info("Move DDB Job(Id: %s)", job.job_id)
            if not job.wait_for_completion():
                raise Exception(f"Move DDB Job(Id: {job.job_id}) Failed[JPR: {job.delay_reason}]")
            self.log.info("Move DDB Job(Id: %s) Completed", job.job_id)

            self.log.info("waiting for 360 seconds...[as we set the mmconfig to 5 min]")
            time.sleep(360)
            self.check_ransomware_protection_enabled(self.media_agent_obj2, testcase_initial_check=False)
            self.log.info("Restarting the media mount manager service...")
            new_client.restart_service(service_name="GxMMM(Instance001)")
            self.log.info("Sleeping for 120 seconds to gie MMM Service time to restart")
            time.sleep(120)
            self.log.info("Media mount manager service restarted")

            self.is_driver_loaded_and_path_protected(
                self.media_agent_machine2.join_path(self.testcase_path_new_ma, 'MovedDDB'), 2)

            self.log.info('***** Validations Completed for Case 2. Cleaning Up *****')

            # uninstall MA and retire client
            self.clean_uninstall_ma(new_client)

            if self.error_flag:
                # if the list is not empty then error was there, fail testcase
                self.log.error(self.error_flag)
                raise Exception(f"testcase failed: [{self.error_flag}]")
            self.log.info("Finished TC Operations")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status != constants.FAILED:
            # for all the testcase resources created in this run
            self.cleanup_resources()
        else:
            self.log.warning('******* TestCase Failed. Not CleaningUp the entities *******')
