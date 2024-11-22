# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case
	TestCase to perform Data Server IP Cases.
	TestCase is the only class defined in this file.
	TestCase: Class for executing this test case
	TestCase:
	    __init__()                  --  initialize TestCase class
	    get_source_media_agent_id_of_aux_copy_job(job_id)
	                                --  function to get source media agent id of aux copy job
	    get_media_agent_id_of_media_agent_ip(library_name, access_type)
	                                --  function to get media agent id of the IP media agent
	    run_backup(backup_type, subclient_obj)
	                                --  function to run backup
	    get_space_update_time_value_from_mmconfigs()
	                                --  function to get space update time from MMConfigs table
	    parse_ma_logs()
	                                --  function to parse log files in media agents
	    reg_check_for_mountpath()   --  checks for mountpath set in registry
	    main_activity(storage_policy_name)
	                                --  function to carry out data protection operations
	    setup()                     --  setup function of this test case
	    run()                       --  run function of this test case
	    tear_down()                 --  teardown function of this test case
"""
import random
import time
from cvpysdk import (storage, policy, job)
from cvpysdk.backupset import Backupsets
from cvpysdk.subclient import Subclients
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object
                    Properties to be initialized:
                        name            (str)       --  name of this test case
                        tcinputs        (dict)      --  test case inputs with input name as dict
                                                        key and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Data Server IP Testing"
        self.tcinputs = {
            "AgentName": None,
            "MediaAgentRegular": None,
            "MediaAgentIP": None,
            "AccessType": None
        }
        self.random_number = None
        self.media_agent_regular = None
        self.media_agent_ip = None
        self.media_agent_regular_machine = None
        self.media_agent_ip_machine = None
        self.automation_folder = None
        self.automation_folder_location = None
        self.disk_library_mountpath_name = None
        self.disk_library_mountpath = None
        self.aux_copy_library_mountpath = None
        self.dedup_path = None
        self.restore_primary_location = None
        self.restore_secondary_location = None
        self.subclient_content_folder = None
        self.subclient_content = None
        self.disk_library_name = None
        self.aux_copy_name = None
        self.aux_copy_library_name = None
        self.storage_policy_obj = None
        self.nondedup_storage_policy = None
        self.dedup_storage_policy = None
        self.dedup_helper = None
        self.mm_helper = None
        self.access_type = None
        self.agent_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.media_agent_regular_obj = None
        self.media_agent_ip_obj = None
        self.agent_obj = None
        self.backupsets_all = None
        self.backupset_obj = None
        self.subclients_all = None
        self.subclient_obj = None
    
    def get_media_agent_id_of_media_agent_ip(self, library_name, access_type):
        """
        Get id of the ip media agent used for the aux copy job
        Args:
            library_name (str) -- name of the library which has the shared mount path
            access_type (int) -- access type for Data Server IP
        Return:
            (int) -- id of the ip media agent
        """
        query = """ select clientid from MMDeviceController MMDC WITH (NOLOCK)
                       join
                       MMMountPathToStorageDevice MPTSD WITH (NOLOCK)
                       on MPTSD.DeviceId = MMDC.DeviceId 
                       join 
                       MMMountPath MMMP WITH (NOLOCK)
                       on MPTSD.mountpathid = MMMP.mountpathid
                       join
                       MMLibrary MML WITH (NOLOCK) 
                       on MML.LibraryId = MMMP.libraryid
                       where MML.AliasName like '{0}' and
                       MMDC.deviceaccesstype={1}
               """.format(library_name, int(access_type))
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        media_agent_id = int(self.csdb.fetch_one_row()[0])
        return media_agent_id

    def run_backup(self, backup_type, subclient_obj):
        """
        Run backup
        Args:
            backup_type (str) -- type of the backup operation
            subclient_obj (object) -- object of the subclient to take backup of
        Return:
            (object) -- object of the Job class
        """
        self.log.info("Starting %s backup", backup_type)
        job = subclient_obj.backup(backup_type)
        self.log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job

    def get_space_update_time_value_from_mmconfigs(self):
        """
        Get id of the ip media agent used for the aux copy job
        Args:
            none
        Return:
            (int) -- space update time from MMConfigs
        """
        query = """ select value
                    from MMConfigs WITH (NOLOCK)
                    where name like 'MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN'
                    """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        interval = int(self.csdb.fetch_one_row()[0])
        return interval

    def parse_ma_logs(self):
        """
        Parse media agent logs
        Args:
            (str) -- shared mount path of the disk library
        Return:
            (bool) -- True, if the parsing and comparison is successful. False, otherwise
        """
        matched_lines, matched_strings = self.dedup_helper.parse_log(
            client=self.media_agent_ip,
            log_file='NFSTransport.log',
            regex='exported successfully as'
        )
        nfst_final_list = []
        to_find = self.disk_library_mountpath_name
        for line in matched_lines:
            index = line.find(to_find)
            if index > -1:
                self.log.info(line)
                nfst_final_list.append(line)
        all_3dnfs_request = []
        all_3dnfs_success = []
        matched_lines, matched_strings = self.dedup_helper.parse_log(
            client=self.media_agent_regular,
            log_file='3dnfs.log',
            regex='Request to mount'
        )
        to_find = self.disk_library_mountpath_name
        for line in matched_lines:
            index = line.find(to_find)
            if index > -1:
                self.log.info(line)
                all_3dnfs_request.append(line)
        matched_lines, matched_strings = self.dedup_helper.parse_log(
            client=self.media_agent_regular,
            log_file='3dnfs.log',
            regex='Successfully added mount point'
        )
        to_find = self.disk_library_mountpath_name
        for line in matched_lines:
            index = line.find(to_find)
            if index > -1:
                self.log.info(line)
                all_3dnfs_success.append(line)
        nfst_count = len(nfst_final_list)
        _3dnfs_request_count = len(all_3dnfs_request)
        _3dnfs_success_count = len(all_3dnfs_success)
        if nfst_count == 0 or _3dnfs_success_count == 0 or _3dnfs_request_count == 0:
            self.log.error("Parsing failed as there are no matching log lines...")
            return False
        if _3dnfs_request_count + _3dnfs_success_count == nfst_count * 2:
            self.log.info("Parsing and comparison is successful...")
            return True
        self.log.error("Parsing and comparison is not successful...")
        return False

    def reg_check_for_mountpath(self):
        """
        Waits and check whether mountpath is set in registry
        Args:
            None
        Return:
            None
        """
        space_update_time = self.get_space_update_time_value_from_mmconfigs()
        t_end = time.time() + 60 * space_update_time
        pos = -1
        while time.time() < t_end:
            foldervalue = 0
            while foldervalue < 100:
                try:
                    instance_value = self.media_agent_ip_machine.instance
                    regkeyvalue = self.media_agent_ip_machine.get_registry_value(
                        win_key=r"HKLM:\\SOFTWARE\\Commvault Systems\\Galaxy\\" + instance_value
                        + "\\MediaAgent\\" + str(foldervalue), value="Path")
                except Exception:
                    continue
                pos = regkeyvalue.find(self.disk_library_mountpath)
                if pos > 0:
                    break
                foldervalue = foldervalue + 1
            if pos > 0:
                break

    def main_activity(self, storage_policy_name):
        """
        Data protection operations are carried out using this function
        Args:
            storage_policy_name (str) -- name of the storage policy
        Return:
            None
        """
        self.log.info("Adding storage policy." + storage_policy_name)
        if storage_policy_name == self.dedup_storage_policy:
            self.storage_policy_obj = self.commcell.storage_policies.add(
                storage_policy_name=storage_policy_name,
                library=self.disk_library_name,
                media_agent=self.media_agent_regular,
                dedup_path=self.dedup_path,
                dedup_media_agent=self.media_agent_regular
            )
        elif storage_policy_name == self.nondedup_storage_policy:
            self.storage_policy_obj = self.commcell.storage_policies.add(
                storage_policy_name=storage_policy_name,
                library=self.disk_library_name,
                media_agent=self.media_agent_regular
            )
        self.log.info("Added storage policy." + storage_policy_name)
        self.log.info("Setting Retention: 0-days and 1-cycle on Primary Copy.")
        sp_primary_obj = self.storage_policy_obj.get_copy("Primary")
        retention = (0, 1, -1)
        sp_primary_obj.copy_retention = retention
        self.log.info("Set Retention: 0-days and 1-cycle on Primary Copy.")
        self.log.info("Creating secondary copy for storage policy."
                      + storage_policy_name)
        self.storage_policy_obj.create_secondary_copy(
            copy_name=self.aux_copy_name,
            library_name=self.aux_copy_library_name,
            media_agent_name=self.media_agent_ip
        )
        self.log.info("Created secondary copy for storage policy."
                      + storage_policy_name)
        self.log.info("Setting Retention: 0-days and 1-cycle on Aux Copy.")
        sp_aux_obj = self.storage_policy_obj.get_copy(self.aux_copy_name)
        retention = (0, 1, -1)
        sp_aux_obj.copy_retention = retention
        self.log.info("Set Retention: 0-days and 1-cycle on Aux Copy.")
        self.log.info("Removing association with system created "
                      "autocopy schedule on above created copy.")
        if self.commcell.schedule_policies.has_policy('System Created Autocopy schedule'):
            auxcopy_schedule_policy = self.commcell.schedule_policies.get('System Created '
                                                                          'Autocopy schedule')
            association = [{'storagePolicyName': storage_policy_name,
                            'copyName': self.aux_copy_name}]
            auxcopy_schedule_policy.update_associations(association, 'exclude')
        self.log.info("Removed association with system created "
                      "autocopy schedule on above created copy.")
        self.log.info("Adding subclient and setting content." + self.subclient_name)
        if self.subclients_all.has_subclient(self.subclient_name):
            self.subclients_all.delete(self.subclient_name)
        self.subclient_obj = self.subclients_all.add(
            self.subclient_name, storage_policy_name)
        self.subclient_obj.content = [self.subclient_content]
        self.log.info("Added subclient and set content." + self.subclient_name)
        job_type_list = ['FULL', 'INCREMENTAL', 'INCREMENTAL', 'SYNTHETIC_FULL']
        for job_type in job_type_list:
            if not job_type == 'SYNTHETIC_FULL':
                if not self.media_agent_regular_machine.generate_test_data(
                        file_path=self.subclient_content,
                        file_size=5000):
                    self.log.error("Failed to generate test data.")
                    raise Exception("Failed to generate test data.")
                self.log.info("Test data generated successfully.")
                self.run_backup(job_type, self.subclient_obj)
                time.sleep(5)
            else:
                self.run_backup(job_type, self.subclient_obj)
                time.sleep(5)
        self.reg_check_for_mountpath()
        self.log.info("Starting aux copy job.")
        aux_copy_obj = self.storage_policy_obj.run_aux_copy(self.aux_copy_name)
        if not aux_copy_obj.wait_for_completion():
            raise Exception("Failed to run aux copy job with error: {0}".format(
                aux_copy_obj.delay_reason))
        self.log.info("Successfully finished aux copy job.")
        source_ma_id_list = self.mm_helper.get_source_ma_id_for_auxcopy(int(aux_copy_obj.job_id))
        if len(source_ma_id_list) > 1:
            raise Exception(f"More than 1 source media agent used in aux copy job: {aux_copy_obj.job_id}, Media Agents: {source_ma_id_list}")
        source_ma_id = source_ma_id_list[0]
        dest_ma_id = self.get_media_agent_id_of_media_agent_ip(
            self.disk_library_name,
            self.access_type)
        self.log.info("Source media agent id used for aux copy job: %d", source_ma_id)
        self.log.info("Destination media agent id used for aux copy job: %d", dest_ma_id)
        if source_ma_id == dest_ma_id:
            self.log.info(
                "Source media agent and the destination media agent is the IP Media Agent.")
        else:
            self.log.error(
                "Source media agent or the destination media agent is not the IP Media Agent.")
            self.status = constants.FAILED
        log_file_validation = self.parse_ma_logs()
        if log_file_validation:
            self.log.info("Log file validation is successful.")
        else:
            self.log.error("Log file validation failed.")
            self.status = constants.FAILED
        self.log.info("Deleting restore locations if exists, and then creating restore locations.")
        if self.media_agent_regular_machine.check_directory_exists(
                self.restore_primary_location):
            self.media_agent_regular_machine.remove_directory(self.restore_primary_location)
        self.media_agent_regular_machine.create_directory(self.restore_primary_location)
        if self.media_agent_regular_machine.check_directory_exists(
                self.restore_secondary_location):
            self.media_agent_regular_machine.remove_directory(self.restore_secondary_location)
        self.media_agent_regular_machine.create_directory(self.restore_secondary_location)
        self.log.info("Created restore locations.")
        restore_from_primary_copy_job_obj = self.subclient_obj.restore_out_of_place(
            client=self.media_agent_regular,
            destination_path=self.restore_primary_location,
            paths=self.subclient_obj.content,
            fs_options={
                "media_agent": self.media_agent_ip
            })
        self.log.info(
            "Started restore job from Primary Copy with id {0}".format(
                restore_from_primary_copy_job_obj.job_id))
        if not restore_from_primary_copy_job_obj.wait_for_completion():
            raise Exception(
                "Failed to run restore job {0} with error: {1}".format(
                    restore_from_primary_copy_job_obj.job_id,
                    restore_from_primary_copy_job_obj.delay_reason
                )
            )
        self.log.info(
            "Completed restore job from Primary Copy with id {0}".format(
                restore_from_primary_copy_job_obj.job_id))
        self.log.info("Validating contents after restore from primary copy.")
        restore_location_primary = self.media_agent_regular_machine.join_path(
            self.restore_primary_location,
            self.subclient_content_folder)
        ret = self.media_agent_regular_machine.compare_folders(
            self.media_agent_regular_machine,
            self.subclient_content, restore_location_primary)
        if len(ret) == 0:
            self.log.info("Validation of data after restore from Primary copy is successful.")
        else:
            self.log.error("Validation of data after restore from Primary copy has failed.")
            self.status = constants.FAILED
        restore_from_secondary_job_obj = self.subclient_obj.restore_out_of_place(
            client=self.media_agent_regular,
            destination_path=self.restore_secondary_location,
            paths=self.subclient_obj.content,
            fs_options={
                "media_agent": self.media_agent_ip
            },
            copy_precedence=2,
            overwrite=True)
        self.log.info(
            "Started restore job from Aux Copy with id {0}".format(
                restore_from_secondary_job_obj.job_id))
        if not restore_from_secondary_job_obj.wait_for_completion():
            raise Exception(
                "Failed to run restore job {0} with error: {1}".format(
                    restore_from_secondary_job_obj.job_id,
                    restore_from_secondary_job_obj.delay_reason
                )
            )
        self.log.info(
            "Completed restore job from Aux Copy with id {0}".format(
                restore_from_secondary_job_obj.job_id))
        self.log.info("Validating contents after restore from aux copy.")
        restore_location_secondary = self.media_agent_regular_machine.join_path(
            self.restore_secondary_location,
            self.subclient_content_folder)
        ret = self.media_agent_regular_machine.compare_folders(
            self.media_agent_regular_machine,
            self.subclient_content, restore_location_secondary)
        if len(ret) == 0:
            self.log.info("Validation of data after restore from Aux copy is successful.")
        else:
            self.log.error("Validation of data after restore from Aux copy has failed.")
            self.status = constants.FAILED

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.random_number = str(random.randint(100, 999999))
        self.media_agent_regular = self.tcinputs["MediaAgentRegular"]
        self.media_agent_ip = self.tcinputs["MediaAgentIP"]
        self.media_agent_regular_machine = Machine(
            machine_name=self.media_agent_regular,
            commcell_object=self.commcell
        )
        self.media_agent_ip_machine = Machine(
            machine_name=self.media_agent_ip,
            commcell_object=self.commcell
        )
        ma_regular_drive = options_selector.get_drive(self.media_agent_regular_machine, 1024 * 5)
        if ma_regular_drive is None:
            raise Exception("No free space...")
        ma_ip_drive = options_selector.get_drive(self.media_agent_ip_machine, 1024 * 5)
        if ma_ip_drive is None:
            raise Exception("No free space...")
        self.automation_folder = 'Automation' + self.random_number
        self.automation_folder_location = self.media_agent_regular_machine.join_path(
            ma_regular_drive, self.automation_folder)
        if self.media_agent_regular_machine.check_directory_exists(self.automation_folder_location):
            self.media_agent_regular_machine.remove_directory(self.automation_folder_location)
        self.media_agent_regular_machine.create_directory(self.automation_folder_location)
        self.disk_library_mountpath_name = 'DiskLibraryMountPath' + self.random_number
        self.disk_library_mountpath = self.media_agent_regular_machine.join_path(
            ma_regular_drive, self.automation_folder, 'DiskLibraryMountPath' + self.random_number)
        if self.media_agent_regular_machine.check_directory_exists(self.disk_library_mountpath):
            self.media_agent_regular_machine.remove_directory(self.disk_library_mountpath)
        self.media_agent_regular_machine.create_directory(self.disk_library_mountpath)
        self.aux_copy_library_mountpath = self.media_agent_ip_machine.join_path(
            ma_ip_drive, self.automation_folder, 'AuxCopyLibraryMountPath' + self.random_number)
        if self.media_agent_ip_machine.check_directory_exists(self.aux_copy_library_mountpath):
            self.media_agent_ip_machine.remove_directory(self.aux_copy_library_mountpath)
        self.media_agent_ip_machine.create_directory(self.aux_copy_library_mountpath)
        self.dedup_path = self.media_agent_regular_machine.join_path(
            ma_regular_drive, self.automation_folder, 'DedupPath' + self.random_number)
        if self.media_agent_regular_machine.check_directory_exists(self.dedup_path):
            self.media_agent_regular_machine.remove_directory(self.dedup_path)
        self.media_agent_regular_machine.create_directory(self.dedup_path)
        self.restore_primary_location = self.media_agent_regular_machine.join_path(
            ma_regular_drive, self.automation_folder, 'RestorePrimary' + self.random_number)
        self.restore_secondary_location = self.media_agent_regular_machine.join_path(
            ma_regular_drive, self.automation_folder, 'RestoreSecondary' + self.random_number)
        self.subclient_content_folder = 'BackupContent' + self.random_number
        self.subclient_content = self.media_agent_regular_machine.join_path(
            ma_regular_drive, self.automation_folder, 'BackupContent' + self.random_number)
        if self.media_agent_regular_machine.check_directory_exists(self.subclient_content):
            self.media_agent_regular_machine.remove_directory(self.subclient_content)
        self.media_agent_regular_machine.create_directory(self.subclient_content)
        self.disk_library_name = 'DiskLibrary' + self.random_number
        self.aux_copy_name = 'AuxCopy' + self.random_number
        self.aux_copy_library_name = 'AuxCopyLibrary' + self.random_number
        self.nondedup_storage_policy = 'NonDedupStoragePolicy' + self.random_number
        self.dedup_storage_policy = 'DedupStoragePolicy' + self.random_number
        self.dedup_helper = DedupeHelper(self)
        self.mm_helper = MMHelper(self)
        self.access_type = int(self.tcinputs["AccessType"])
        self.agent_name = self.tcinputs["AgentName"]
        self.backupset_name = 'BackupSet' + self.random_number
        self.subclient_name = 'Subclient' + self.random_number
        self.media_agent_regular_obj = self.commcell.clients.get(self.media_agent_regular)
        self.media_agent_ip_obj = self.commcell.clients.get(self.media_agent_ip)
        self.agent_obj = self.media_agent_regular_obj.agents.get(self.agent_name)
        self.backupsets_all = Backupsets(self.agent_obj)
        self.backupset_obj = self.backupsets_all.add(self.backupset_name)
        self.subclients_all = Subclients(self.backupset_obj)
        self.subclient_obj = None

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info('Adding disk library.' + self.disk_library_name)
            self.commcell.disk_libraries.add(
                library_name=self.disk_library_name,
                media_agent=self.media_agent_regular,
                mount_path=self.disk_library_mountpath
            )
            self.log.info('Added disk library.' + self.disk_library_name)
            self.log.info("Adding aux copy library." + self.aux_copy_library_name)
            self.commcell.disk_libraries.add(
                library_name=self.aux_copy_library_name,
                media_agent=self.media_agent_ip,
                mount_path=self.aux_copy_library_mountpath
            )
            self.log.info("Added aux copy library." + self.aux_copy_library_name)
            self.log.info('Sharing mount path.' + self.disk_library_mountpath)
            library_details = {
                "mountPath": self.disk_library_mountpath,
                "mediaAgentName": self.media_agent_regular
            }
            storage.DiskLibrary(
                self.commcell,
                self.disk_library_name,
                library_details=library_details).share_mount_path(
                    media_agent=self.media_agent_regular,
                    library_name=self.disk_library_name,
                    mount_path=self.disk_library_mountpath,
                    new_media_agent=self.media_agent_ip,
                    access_type=self.access_type,
                    new_mount_path=self.disk_library_mountpath
                )
            self.log.info('Shared mount path.' + self.disk_library_mountpath)
            self.log.info("***** DEDUP CASE *****")
            self.main_activity(self.dedup_storage_policy)
            self.log.info("****** NON-DEDUP CASE *****")
            self.main_activity(self.nondedup_storage_policy)
        except Exception as excp:
            self.log.error('Exception raised while executing testcase: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("***** CLEANING UP *****")
        time.sleep(10)
        job_obj = job.JobController(self.commcell)
        jobs = job_obj.active_jobs()
        current_dataaging_job_id = -1
        for job_id, job_details in jobs.items():
            for key, value in job_details.items():
                if key.lower() == "operation" and value.lower() == "data aging":
                    current_dataaging_job_id = job_id
        if current_dataaging_job_id != -1:
            running_job_obj = job.Job(self.commcell, current_dataaging_job_id)
            if not running_job_obj.wait_for_completion():
                raise Exception(
                    "Failed to run data aging job."
                )        
        data_aging_job = self.commcell.run_data_aging(
            storage_policy_name=self.dedup_storage_policy, 
            is_granular=True,
            include_all_clients=True)
        self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error("Data Aging job [%s] has failed with %s.", data_aging_job.job_id,
                           data_aging_job.delay_reason)
            raise Exception(
                "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                   data_aging_job.delay_reason))
        self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)
        data_aging_job = self.commcell.run_data_aging(
            storage_policy_name=self.nondedup_storage_policy,
            is_granular=True,
            include_all_clients=True)
        self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
        if not data_aging_job.wait_for_completion():
            self.log.error("Data Aging job [%s] has failed with %s.", data_aging_job.job_id,
                           data_aging_job.delay_reason)
            raise Exception(
                "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                   data_aging_job.delay_reason))
        self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)
        self.log.info("Removing subclient if exists...")
        if Subclients(self.backupset_obj).has_subclient(self.subclient_name):
            Subclients(self.backupset_obj).delete(self.subclient_name)
            self.log.info("Removed subclient..." + self.subclient_name)
        self.log.info("Removing backupset if exists...")
        if Backupsets(self.agent_obj).has_backupset(self.backupset_name):
            Backupsets(self.agent_obj).delete(self.backupset_name)
            self.log.info("Removed backupset..." + self.backupset_name)
        backupsetobj = Backupsets(self.agent_obj).get('defaultBackupSet')
        if Subclients(backupsetobj).has_subclient('DDBBackup'):
            Subclients(backupsetobj).delete('DDBBackup')
        self.log.info("Removing non-dedup storage policy if exists...")
        if policy.StoragePolicies(self.commcell).has_policy(self.nondedup_storage_policy):
            policy.StoragePolicies(self.commcell).delete(self.nondedup_storage_policy)
            self.log.info("Removed non-dedup storage policy..." + self.nondedup_storage_policy)
        self.log.info("Removing dedup storage policy if exists...")
        if policy.StoragePolicies(self.commcell).has_policy(self.dedup_storage_policy):
            policy.StoragePolicies(self.commcell).delete(self.dedup_storage_policy)
            self.log.info("Removed dedup storage policy..." + self.dedup_storage_policy)
        self.log.info("Removing disk library if exists...")
        if storage.DiskLibraries(self.commcell).has_library(self.disk_library_name):
            storage.DiskLibraries(self.commcell).delete(self.disk_library_name)
            self.log.info("Removed disk library..." + self.disk_library_name)
        self.log.info("Removing aux copy library if exists...")
        if storage.DiskLibraries(self.commcell).has_library(self.aux_copy_library_name):
            storage.DiskLibraries(self.commcell).delete(self.aux_copy_library_name)
            self.log.info("Removed aux copy library..." + self.aux_copy_library_name)
        if self.media_agent_regular_machine.check_directory_exists(self.subclient_content):
            self.media_agent_regular_machine.remove_directory(self.subclient_content)
            self.log.info('Removed directory...' + self.subclient_content)
        if self.media_agent_regular_machine.check_directory_exists(self.restore_primary_location):
            self.media_agent_regular_machine.remove_directory(self.restore_primary_location)
            self.log.info('Removed directory...' + self.restore_primary_location)
        if self.media_agent_regular_machine.check_directory_exists(self.restore_secondary_location):
            self.media_agent_regular_machine.remove_directory(self.restore_secondary_location)
            self.log.info('Removed directory...' + self.restore_secondary_location)
        if self.media_agent_ip_machine.check_directory_exists(self.aux_copy_library_mountpath):
            self.media_agent_ip_machine.remove_directory(self.aux_copy_library_mountpath)
            self.log.info('Removed directory...' + self.aux_copy_library_mountpath)
        if self.media_agent_regular_machine.check_directory_exists(self.disk_library_mountpath):
            self.media_agent_regular_machine.remove_directory(self.disk_library_mountpath)
            self.log.info('Removed directory...' + self.disk_library_mountpath)
        if self.media_agent_regular_machine.check_directory_exists(self.dedup_path):
            self.media_agent_regular_machine.remove_directory(self.dedup_path)
            self.log.info('Removed directory...' + self.dedup_path)
        if self.media_agent_regular_machine.check_directory_exists(self.automation_folder_location):
            self.media_agent_regular_machine.remove_directory(self.automation_folder_location)
            self.log.info('Removed directory...' + self.automation_folder_location)
        if self.media_agent_ip_machine.check_directory_exists(self.automation_folder_location):
            self.media_agent_ip_machine.remove_directory(self.automation_folder_location)
            self.log.info('Removed directory...' + self.automation_folder_location)
