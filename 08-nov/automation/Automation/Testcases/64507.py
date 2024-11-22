# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

    This test case does the following:

    i. Create cloud Pool and validate flags.
        - Create cloud pool with MA1 using access key auth
        - Validate from DB:
                       - Max concurrent writers are set on device, Mountpath and storage all three levels
                       - Spill and Fill is enabled by defaults
                       - Micro pruning is ON
                       - Reserve space is used instead of do not consume more than ## GB
        - Validate the MA1 with a backup job that it can write.
        - Change the device access type from R/W to Read on MA1, and run a new backup and validate backup return a good JPR.
        - Update back to r/w from read, ensure job is completed

    ii. Validate for IAM Auth type
        - Add a new MA2 on MP1 with IAM auth Type (you will need to enable config param to support diff credential on diff controller)
        - check MA has read/write access with max writers
        - Run backup via MA2 and ensure it completes
        - Modify the credential used to a read only cred and run new backup again and it should fail with good JPR.

    iii. Restore using two MA if needed two jobs. ensure restore complete from MA2 and MA1 both

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    clean_up()      --  clean up function of this test case

    validate_storage_default_settings() --  validates if the defaults are set for the storage

    get_library_name()  -- returns the name of the library of the storage pool

    get_mountpath_id()  --  returns the id of the mountpath in the storage

    get_device_controller_id()  --  returns the id of the device controller for given media agent and mountpath id

    get_device_id()  --  returns the device id for the given mountpath id

    get_media_agent_id()  --  returns the id of the media agent for the given media agent name

    validate_max_writers_on_device_controller()  --  validates if the max writers are set on the device controller

    validate_device_controller_read_only_access()  --  validates if the device controller has read only access

    validate_device_controller_read_write_access()  --  validates if the device controller has read write access

    validate_device_controller_credentials() -- validates if the credentials used are same as expected credentials

    validate_ma_used_for_backup_job()  --  validates if the given media agent was used for the backup job

    validate_ma_used_for_restore_job()  --  validates if the given media agent was used for the restore job

    is_device_controller_read_write()  --  Tells if the device controller has read/write access or not

    restore_to_path_on_client()  -- restores to the given destination path on the client machine

Sample JSON:
    "64507": {
        "ClientName": "Client machine name",
        "AgentName": "File System",
        "MediaAgentName": "MA1 machine name",
        "MediaAgent2Name": "MA2 machine name",
        "CloudMountPath": "cloud mount path",
        "AccessKeyAuthTypeUsername": "username in the format <Service Host>//<Access Key ID>",
        "AccessKeyAuthTypeCredentialName": "Credential name for access key auth type",
        "IAMAuthTypeUsername": "username in the format <Service Host>//<Access Key ID>",
        "IAMAuthTypeCredentialName": "Credential name for IAM auth type",
        "IAMAuthTypeReadOnlyUsername": "username in the format <Service Host>//<Access Key ID>",
        "IAMAuthTypeReadOnlyCredentialName": "Credential name for IAM auth type having read-only access",
        "CloudVendorName": "microsoft azure storage"
    }
    Note: For 'CloudVendorName' refer the constants in mediaagentconstants.CLOUD_SERVER_TYPES
          For 'CloudMountPath' and for each auth type username format refer
          https://documentation.commvault.com/2023e/expert/cloud_libraries_vendor_specific_xml_parameters_01.html
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager
from MediaAgents import mediaagentconstants
import time

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Acceptance Cloud Storage Pool"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None,
            "MediaAgent2Name": None,
            "CloudMountPath": None,
            "AccessKeyAuthTypeUsername": None,
            "AccessKeyAuthTypeCredentialName": None,
            "IAMAuthTypeUsername": None,
            "IAMAuthTypeCredentialName": None,
            "IAMAuthTypeReadOnlyUsername": None,
            "IAMAuthTypeReadOnlyCredentialName": None,
            "CloudVendorName": None
        }
        self.cloud_storage_pool_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.partition_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.restore_dest_path2 = None
        self.common_util = None
        self.dedupehelper = None
        self.mmhelper = None
        self.job_manager = None
        self.ddb_path = None
        self.warning_list = None

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        self.common_util = CommonUtils(self)
        self.client_machine = Machine(self.client)
        self.ma_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)
        self.cloud_storage_pool_name = \
            f"cloud_storage_pool_{self.id}_{self.tcinputs['ClientName']}_{self.tcinputs['MediaAgentName']}"
        self.storage_policy_name =\
            f"storage_policy_{self.id}_{self.tcinputs['ClientName']}_{self.tcinputs['MediaAgentName']}"
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.backupset_name = f"Backupset_{self.id}_{self.tcinputs['ClientName']}"
        client_drive = options_selector.get_drive(self.client_machine, size=20 * 1024)
        if client_drive is None:
            raise Exception("No free space for content on client machine.")
        ma_drive = client_drive = options_selector.get_drive(self.ma_machine, size=10 * 1024)
        if ma_drive is None:
            raise Exception("No free space for ddb on MA1 machine")
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id),
                                                               'RestoreLocation')
        self.restore_dest_path2 = self.client_machine.join_path(client_drive, 'Automation', str(self.id),
                                                                'RestoreLocation2')
        self.ddb_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDBLocation')
        self.job_manager = JobManager()
        self.warning_list = []
        self.clean_up()

    def run(self):
        """Run function of this test case"""
        try:
            # constants
            read_only_device_access_type = 4
            read_write_device_access_type = 6

            # updating MMConfigs table param to update cloud library credential to selected device controller only
            self.mmhelper.update_mmconfig_param('MMS2_CONFIG_CLOUD_LIB_UPDATE_CREDENTIAL_TO_REQUESTED_DEVICE_CTRL',
                                                0, 1)

            # Creating cloud storage pool with saved credentials (Access key) for azure storage
            # Note: Same MA is being used for both datamover and DDB.
            self.commcell.storage_pools.add(self.cloud_storage_pool_name,
                                           self.tcinputs["CloudMountPath"],
                                           self.tcinputs["MediaAgentName"],
                                           self.tcinputs["MediaAgentName"],
                                           self.ddb_path,
                                           username=self.tcinputs["AccessKeyAuthTypeUsername"],
                                           password="",
                                           credential_name=self.tcinputs["AccessKeyAuthTypeCredentialName"],
                                           cloud_server_type=mediaagentconstants.CLOUD_SERVER_TYPES[self.tcinputs['CloudVendorName']])

            # getting disk library object
            library_name = self.get_library_name()
            disk_library = self.commcell.disk_libraries.get(library_name)
            disk_library.mount_path = self.tcinputs["CloudMountPath"]
            disk_library.mediaagent = self.tcinputs["MediaAgentName"]

            # ----------------- Validating defaults from DB -----------------------
            self.validate_storage_default_settings()

            # ------ Creating a storage policy, backup set, subclient and generating test data -------------
            # Creating storage policy
            self.dedupehelper.configure_dedupe_storage_policy(storage_policy_name=self.storage_policy_name,
                                                              storage_pool_name=self.cloud_storage_pool_name,
                                                              is_dedup_storage_pool=True
                                                              )

            # Creating backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # Creating subclient
            subclient_name = f"subclient_{self.id}"
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient_name,
                                                       self.storage_policy_name, self.content_path, self.agent)

            # Genrating test data
            self.log.info("Generating Data at %s", self.content_path)
            if not self.client_machine.generate_test_data(self.content_path, dirs=4, file_size=(10 * 1024),
                                                          files=5):
                self.log.error("unable to Generate Data at %s", self.content_path)
                raise Exception("unable to Generate Data at {0}".format(self.content_path))
            self.log.info("Generated Data at %s", self.content_path)

            # Run backup through MA1
            job = self.common_util.subclient_backup(sc_obj, "full")
            self.validate_ma_used_for_backup_job(job, self.tcinputs['MediaAgentName'])

            # Change MA1 to Read-only
            mountpath_id = self.get_mountpath_id()
            media_agent_id = self.get_media_agent_id(self.tcinputs['MediaAgentName'])
            device_controller_id = self.get_device_controller_id(self.tcinputs['MediaAgentName'], mountpath_id)
            disk_library.modify_cloud_access_type(mountpath_id, device_controller_id, read_only_device_access_type)

            # validating if ma is read only
            self.validate_device_controller_read_only_access(device_controller_id)

            # run backup keeping MA read only. Ensure good JPR
            job = self.common_util.subclient_backup(sc_obj, "full", wait=False)
            self.job_manager.job = job
            time_limit = time.time() + 1 * 60
            while not job.delay_reason:
                time.sleep(2)
                if time.time() >= time_limit:
                    raise Exception("Did not get delay reason when MA1 was read only, waited 60 seconds. exiting...")
            self.log.info(f"Job Delay Reason : {job.delay_reason}")
            if "MediaAgent does not have write access enabled for the mount path to this device" not in job.delay_reason:
                raise Exception("When MA was read-only, did not receive a valid JPR")

            # revert MA back to r/w. ensure job is completed.
            self.log.info("MA1 reverting back to r/w")
            disk_library.modify_cloud_access_type(mountpath_id, device_controller_id, read_write_device_access_type)
            self.validate_device_controller_read_write_access(device_controller_id)
            self.log.info("MA1 reverted to r/w")
            self.job_manager.wait_for_state("completed")
            self.validate_ma_used_for_backup_job(job, self.tcinputs['MediaAgentName'])

            # sharing mount path with MA2
            self.log.info("Sharing mount path with MA2")
            disk_library.share_mount_path(self.tcinputs["MediaAgent2Name"],
                                          self.tcinputs["CloudMountPath"],
                                          username=self.tcinputs["IAMAuthTypeUsername"],
                                          password="dummy",
                                          credential_name=self.tcinputs["IAMAuthTypeCredentialName"],
                                          access_type=14)

            # validating if correct credentials are used for MA2
            device_controller2_id = self.get_device_controller_id(self.tcinputs["MediaAgent2Name"], mountpath_id)
            self.validate_device_controller_credentials(device_controller2_id, self.tcinputs["IAMAuthTypeCredentialName"])

            # make sure MA2 has max writers and read/write access
            # validate max writers
            self.validate_max_writers_on_device_controller(self.tcinputs["MediaAgent2Name"])

            # validate read/write access
            self.validate_device_controller_read_write_access(device_controller2_id)

            # change MA1 to readonly to force backup using MA2
            self.log.info("Making MA1 readonly")
            disk_library.modify_cloud_access_type(mountpath_id, device_controller_id, read_only_device_access_type)
            self.validate_device_controller_read_only_access(device_controller_id)
            self.log.info("MA1 is now readonly")

            # Running backup job (through MA2)
            self.log.info("Running a backup job, keeping MA1 readonly")
            job = self.common_util.subclient_backup(sc_obj, "full")
            self.validate_ma_used_for_backup_job(job, self.tcinputs['MediaAgent2Name'])

            # Updating MA2 to use readonly credentials
            device_id = self.get_device_id(mountpath_id)
            media_agent2_id = self.get_media_agent_id(self.tcinputs['MediaAgent2Name'])
            self.log.info("Updating MA2 to use readonly IAM credentials")
            disk_library.update_device_controller(mountpath_id,
                                                  device_id,
                                                  device_controller2_id,
                                                  media_agent2_id,
                                                  read_write_device_access_type,
                                                  username=self.tcinputs["IAMAuthTypeReadOnlyUsername"],
                                                  password="dummy",
                                                  credential_name=self.tcinputs["IAMAuthTypeReadOnlyCredentialName"])

            # validating if correct credentials are used for MA2
            self.validate_device_controller_credentials(device_controller2_id,
                                                        self.tcinputs["IAMAuthTypeReadOnlyCredentialName"])

            # running a backup job
            job = self.common_util.subclient_backup(sc_obj, "full", wait=False)

            # waiting until job goes to pending state and validating if good JPR is received
            self.job_manager.job = job
            self.job_manager.wait_for_state("pending")
            self.log.info(f"Pending reason : {job.pending_reason}")
            if "The permission is bad" not in job.pending_reason:
                raise Exception("Did not receive a valid JPR when using read only creds")

            # reverting back to r/w creds and resuming the job
            self.log.info("MA2 reverting back to using r/w IAM creds")
            disk_library.update_device_controller(mountpath_id,
                                                  device_id,
                                                  device_controller2_id,
                                                  media_agent2_id,
                                                  read_write_device_access_type,
                                                  username=self.tcinputs["IAMAuthTypeUsername"],
                                                  password="dummy",
                                                  credential_name=self.tcinputs["IAMAuthTypeCredentialName"])

            # validating if correct credentials are used for MA2`
            self.validate_device_controller_credentials(device_controller2_id,
                                                        self.tcinputs["IAMAuthTypeCredentialName"])

            job.resume()
            self.job_manager.wait_for_state("completed")
            self.validate_ma_used_for_backup_job(job, self.tcinputs['MediaAgent2Name'])

            # -----------------Restoring----------------------
            # Disable MA1
            self.log.info("Disabling MA1 on mountpath")
            disk_library.update_device_controller(mountpath_id,
                                                  device_id,
                                                  device_controller_id,
                                                  media_agent_id,
                                                  read_write_device_access_type,
                                                  username=self.tcinputs['AccessKeyAuthTypeUsername'],
                                                  password="dummy",
                                                  credential_name=self.tcinputs['AccessKeyAuthTypeCredentialName'],
                                                  enabled=False)

            # Restore using MA2
            self.log.info("Running a restore job")
            restore_job = self.restore_to_path_on_client(sc_obj, self.restore_dest_path)
            self.validate_ma_used_for_restore_job(restore_job, self.tcinputs['MediaAgent2Name'])

            # Enable MA1 and Disable MA2
            self.log.info("Disabling MA2 and Enabling MA1 on mountpath")
            disk_library.update_device_controller(mountpath_id,
                                                  device_id,
                                                  device_controller_id,
                                                  media_agent_id,
                                                  read_write_device_access_type,
                                                  username=self.tcinputs['AccessKeyAuthTypeUsername'],
                                                  password="dummy",
                                                  credential_name=self.tcinputs['AccessKeyAuthTypeCredentialName'])
            disk_library.update_device_controller(mountpath_id,
                                                  device_id,
                                                  device_controller2_id,
                                                  media_agent2_id,
                                                  read_write_device_access_type,
                                                  username=self.tcinputs["IAMAuthTypeUsername"],
                                                  password="dummy",
                                                  credential_name=self.tcinputs["IAMAuthTypeCredentialName"],
                                                  enabled=False)

            # Restore using MA1
            self.log.info("Running a restore job")
            restore_job = self.restore_to_path_on_client(sc_obj, self.restore_dest_path2)
            self.validate_ma_used_for_restore_job(restore_job, self.tcinputs['MediaAgentName'])

            # Revert the mmconfig param
            self.mmhelper.update_mmconfig_param('MMS2_CONFIG_CLOUD_LIB_UPDATE_CREDENTIAL_TO_REQUESTED_DEVICE_CTRL',
                                                0, 0)

            if len(self.warning_list) > 0:
                warnings = '\n'.join(self.warning_list)
                self.warning_list = []
                raise Exception(warnings)

            self.log.info("*********************** Run completed *****************************")
        except Exception as exp:
            error = f'Failed to execute test case with error: {exp}'
            if len(self.warning_list) > 0:
                error = error + '\n'.join(self.warning_list)
            self.log.error(error)
            self.result_string = error
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # Delete generated test data on client
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("Cleaning up the test data on client %s", self.content_path)
            self.client_machine.remove_directory(self.content_path)
            self.log.info("Cleaned up the test data on client %s", self.content_path)

        # Delete restored data on client from restore location 1
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.log.info("Cleaning up the restore destination path %s", self.restore_dest_path)
            self.client_machine.remove_directory(self.restore_dest_path)
            self.log.info("Cleaned up the restore destination path %s", self.restore_dest_path)

        # Delete restored data on client from restore location 2
        if self.client_machine.check_directory_exists(self.restore_dest_path2):
            self.log.info("Cleaning up the restore destination path %s", self.restore_dest_path2)
            self.client_machine.remove_directory(self.restore_dest_path2)
            self.log.info("Cleaned up the restore destination path %s", self.restore_dest_path2)

        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self.clean_up()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")

        self.log.info("************* Teardown completed ***************")

    def clean_up(self):
        """ clean up function of this test case """
        try:
            # Delete backup set
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting Backup-set: %s ", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted Backup-set: %s", self.backupset_name)

            # Delete storage policy
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info(f"Deleting Storage Policy: {self.storage_policy_name}")
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info(f"Deleted Storage Policy: {self.storage_policy_name}")

            # Delete cloud storage pool
            if self.commcell.storage_pools.has_storage_pool(self.cloud_storage_pool_name):
                self.log.info(f"Deleting Storage Pool: {self.cloud_storage_pool_name}")
                self.commcell.storage_pools.delete(self.cloud_storage_pool_name)
                self.log.info(f"Deleted Storage Pool: {self.cloud_storage_pool_name}")

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))

        self.log.info("********** Clean up completed *************")

    def validate_storage_default_settings(self):
        """
            validates if the defaults are set for the storage
            returns: none
        """
        # --------------getting library props---------------------
        query = f"""select  lib.extendedattributes,
                            mpl.maxswitchforhost,
                            mp.maxconcurrentwriters,
                            mp.attribute,
                            mp.maxdatatowritemb,
                            dpl.maxdrivestoswitch
                    from    mmlibrary lib with (nolock),
                            app_client ac with (nolock), 
                            mmmountpath mp with (nolock),
                            mmmountpathtostoragedevice mpsd with (nolock), 
                            mmdevicecontroller dc with (nolock), 
                            mmmasterpool mpl with (nolock),
                            mmdrivepool dpl with (nolock), 
                            mmdatapath dp with (nolock), 
                            archgroupcopy agc with (nolock),
                            archgroup ag with (nolock)
                    where   ac.name = '{self.tcinputs['MediaAgentName']}'
                            and mp.libraryid = lib.libraryid
                            and mpsd.mountpathid = mp.mountpathid
                            and dc.deviceid = mpsd.deviceid 
                            and dc.clientid = ac.id
                            and mpl.libraryid = lib.libraryid
                            and dpl.MasterPoolId = mpl.masterpoolid 
                            and dpl.ClientId = ac.id
                            and dp.drivepoolid = dpl.drivepoolid
                            and agc.id = dp.CopyId
                            and ag.id = agc.archGroupId
                            and ag.name = '{self.cloud_storage_pool_name}'
                    """

        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        library_values = self.csdb.fetch_one_row()

        extendedattributes = int(library_values[0])
        maxswitchforhost = int(library_values[1])
        maxconcurrentwriters = int(library_values[2])
        attribute = int(library_values[3])
        maxdatatowritemb = int(library_values[4])
        maxdrivestoswitch = int(library_values[5])


        # max writers on mountpath level
        is_maxwriters_on_mountpath_set = (maxconcurrentwriters == 1000)
        if not is_maxwriters_on_mountpath_set:
            msg = f"Max writers are not set on mountpath. Max writers = {maxconcurrentwriters}"
            self.log.error(msg)
            self.warning_list.append(msg)
        else:
            self.log.info(f"Max writers are set on Mountpath")

        # max writers on device controller level
        is_maxwriter_on_device_controller_set = (maxdrivestoswitch == -1)
        if not is_maxwriter_on_device_controller_set:
            msg = f"Max writers are not set on devicecontroller. Max writers = {maxdrivestoswitch}"
            self.log.error(msg)
            self.warning_list.append(msg)
        else:
            self.log.info(f"Max writers are set on DeviceController")

        # max writers on library level
        is_maxwriters_on_library_set = (maxswitchforhost == -1)
        if not is_maxwriters_on_library_set:
            msg = f"Max writers are not set on library. Max writers = {maxswitchforhost}"
            self.log.error(msg)
            self.warning_list.append(msg)
        else:
            self.log.info(f"Max writers are set on Library")

        # spill and fill is enabled
        is_spill_and_fill_enabled = ((extendedattributes & 1) == 1)
        if not is_spill_and_fill_enabled:
            msg = f"Spill and fill is not enabled on library"
            self.log.error(msg)
            self.warning_list.append(msg)
        else:
            self.log.info(f"Spill and fill is enabled")

        # micro pruning is on
        is_micro_pruning_on = ((attribute & 32) == 32)
        if not is_micro_pruning_on:
            msg = f"Micro pruning is not enabled on mountpath"
            self.log.error(msg)
            self.warning_list.append(msg)
        else:
            self.log.info(f"Micro pruning is on")

        # no restriction is used instead of 'do not consume more than ## gb'
        is_no_restriction = (maxdatatowritemb == -1)
        if not is_no_restriction:
            msg = f"'Max data to write' is used instead of 'No restriction' on mountpath"
            self.log.error(msg)
            self.warning_list.append(msg)
        else:
            self.log.info(f"'No restriction' is used on mountpath")

    def get_library_name(self):
        """
            returns the name of the library of the storage pool
        """
        query = f"""select  distinct lib.aliasname
                    from    mmlibrary lib with (nolock),
                            mmmasterpool mpl with (nolock),
                            mmdrivepool dpl with (nolock), 
                            mmdatapath dp with (nolock), 
                            archgroupcopy agc with (nolock),
                            archgroup ag with (nolock)
                    where   mpl.libraryid = lib.libraryid
                            and dpl.MasterPoolId = mpl.masterpoolid 
                            and dp.drivepoolid = dpl.drivepoolid
                            and agc.id = dp.CopyId
                            and ag.id = agc.archGroupId
                            and ag.name = '{self.cloud_storage_pool_name}'
                """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        return self.csdb.fetch_one_row()[0]

    def get_mountpath_id(self):
        """
            Returns the id of the mountpath in the storage
        """

        query = f"""select  mp.mountpathid
                    from    app_client ac with (nolock), 
                            mmmountpath mp with (nolock),
                            mmmasterpool mpl with (nolock),
                            mmdrivepool dpl with (nolock), 
                            mmdatapath dp with (nolock), 
                            archgroupcopy agc with (nolock),
                            archgroup ag with (nolock)
                    where   ac.name = '{self.tcinputs['MediaAgentName']}'
                            and mp.libraryid = mpl.LibraryId
                            and dpl.MasterPoolId = mpl.masterpoolid 
                            and dpl.ClientId = ac.id
                            and dp.drivepoolid = dpl.drivepoolid
                            and agc.id = dp.CopyId
                            and ag.id = agc.archGroupId
                            and ag.name = '{self.cloud_storage_pool_name}'
                """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def get_device_controller_id(self, media_agent_name, mountpath_id):
        """
            returns the id of the device controller for given media agent and mountpath id
            args:
                media_agent_name: the name of the media agent machine
                mountpath_id: id of the mountpath which is shared by the media agent
        """
        query = f"""select dc.devicecontrollerid
                    from mmdevicecontroller dc with (nolock),
                         mmmountpathtostoragedevice mpst with (nolock),
                         app_client ac with (nolock)
                    where dc.deviceid = mpst.deviceid
                          and dc.clientid = ac.id
                          and mpst.mountpathid = {mountpath_id}
                          and ac.name = '{media_agent_name}'
                """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def get_device_id(self, mountpath_id):
        """
            returns the device id for the given mountpath id
            args:
                mountpath_id: id of the mountpath
        """
        query = f"""select mpsd.deviceid
                    from mmmountpathtostoragedevice mpsd with (nolock)
                    where mpsd.mountpathid = {mountpath_id}
                 """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def get_media_agent_id(self, media_agent_name):
        """
            returns the id of the media agent for the given media agent name
            args:
                media_agent_name: the name of the media agent machine
        """
        query = f"select id from app_client with (nolock) where name = '{media_agent_name}'"
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        return int(self.csdb.fetch_one_row()[0])

    def validate_max_writers_on_device_controller(self, media_agent_name):
        """
            validates if max writers are set on device controller
            args:
                media_agent_name: the name of the media agent machine
        """
        query = f"""select dpl.maxdrivestoswitch
                    from mmdrivepool dpl with (nolock),
                         mmdatapath dp with (nolock),
                         archgroupcopy agc with (nolock),
                         archgroup ag with (nolock),
                         app_client ac with (nolock)
                    where dpl.drivepoolid = dp.drivepoolid
                          and dpl.clientid = ac.id
                          and dp.copyid = agc.id
                          and agc.archgroupid = ag.id
                          and ag.name = '{self.cloud_storage_pool_name}'
                          and ac.name = '{media_agent_name}'
                  """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        maxdrivestoswitch = int(self.csdb.fetch_one_row()[0])
        if maxdrivestoswitch == -1:
            self.log.info(f"[{media_agent_name}] has max writers set")
        else:
            msg = f"[{media_agent_name}] doesn't have max writers set as default"
            self.warning_list.append(msg)
            self.log.error(msg)

    def validate_device_controller_read_only_access(self, device_controller_id):
        """
            Validates if the device controller has read-only access to the mountpath
            args:
                device_controller_id: id of the device controller
        """
        can_read_write = self.is_device_controller_read_write(device_controller_id)
        if can_read_write:
            raise Exception(f"The device controller {device_controller_id} has read-write access."
                            f" Expected read only access.")
        self.log.info(f"The device controller {device_controller_id} has read-only access")

    def validate_device_controller_read_write_access(self, device_controller_id):
        """
            Validates if the device controller has read-write access to the mountpath
            args:
                device_controller_id: id of the device controller
        """
        can_read_write = self.is_device_controller_read_write(device_controller_id)
        if not can_read_write:
            raise Exception(f"The device controller {device_controller_id} doesn't have read-write access.")
        self.log.info(f"The device controller {device_controller_id} has read-write access")

    def validate_device_controller_credentials(self, device_controller_id, expected_credential_name):
        """
            validates if the credentials used are same as expected credentials on device controller

            args:
                device_controller_id - id of the device controller

            returns: none
        """
        query = f"""select c.credentialName
                    from APP_Credentials c with (nolock),
                         APP_CredentialAssoc ca with (nolock),
                         MMDeviceController dc with (nolock)
                    where c.credentialId = ca.credentialId
                          and ca.assocId = dc.CredentialAssocId
                          and dc.DeviceControllerId = {device_controller_id}
                """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cred_name = str(self.csdb.fetch_one_row()[0])

        if cred_name != expected_credential_name:
            msg = (f"Validating credential failed for devicecontroller {device_controller_id}. "
                   f"[Expected]: {expected_credential_name} "
                   f"[Used]: {cred_name}")
            raise Exception(msg)

        self.log.info(f"Credential name used : {cred_name}")

    def validate_ma_used_for_backup_job(self, job, expected_media_agent):
        """
            validates if the given MA was used for the backup job
            args:
                job (Job Object) - job object of the backup job
                expected_media_agent (str) - media agent expected to be used for the backup job
        """
        job_details = job._get_job_details()
        for attempt in range(len(job_details['jobDetail']['attemptsInfo'])):
            phase = job_details['jobDetail']['attemptsInfo'][attempt]['phaseName']
            status = job_details['jobDetail']['attemptsInfo'][attempt]['status']
            if ('Backup' in phase) and status == 'Completed':
                media_agent_used = job_details['jobDetail']['attemptsInfo'][attempt]['mediaAgent']['mediaAgentName']

        if (media_agent_used != expected_media_agent):
            raise Exception(f"For backup job, media agent used is different from expected media agent. "
                            f"Used: {media_agent_used}. Expected: {expected_media_agent}")
        self.log.info(f"For backup job media agent used is : {media_agent_used}")

    def validate_ma_used_for_restore_job(self, job, expected_media_agent):
        """
            validates if the given MA was used for the restore job
            args:
                job (Job object) - job object of the restore job
                expected_media_agent (str) - media agent expected to be used for the restore job
        """
        job_details = job._get_job_details()
        media_agent_used = job_details['jobDetail']['generalInfo']['mediaAgent']['mediaAgentName']
        if (media_agent_used != expected_media_agent):
            raise Exception(f"For restore job, media agent used is different from expected media agent. "
                            f"Used: {media_agent_used}. Expected: {expected_media_agent}")
        self.log.info(f"For restore job media agent used is : {media_agent_used}")

    def is_device_controller_read_write(self, device_controller_id):
        """
            Tells if the devicecontroller has read/write access or not

            args:
                device_controller_id - id of the device controller

            returns: none
        """
        query = f"""select DeviceAccessType 
                    from MMDeviceController with (nolock)
                    where devicecontrollerid = {device_controller_id}
                 """
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        device_access_type = int(self.csdb.fetch_one_row()[0])
        can_read_write = (device_access_type & 6 == 6)
        return can_read_write

    def restore_to_path_on_client(self, subclient_obj, restore_dest_path):
        """
            restores to the given destination path on the client machine

            args:
                sublient_obj - object of the subclient entity

                restore_dest_path - restore path on the client machine

            returns: (int) - restore job object
        """

        restore_job = self.common_util.subclient_restore_out_of_place(restore_dest_path, [self.content_path],
                                                                      subclient=subclient_obj)

        # comparing content data with restored data
        self.log.info("Comparing source content and restore destination content")
        if self.client_machine.compare_folders(self.client_machine, self.content_path,
                                               self.client_machine.join_path(restore_dest_path, 'Testdata')):
            msg = f"Restored data is different from content data. RestoreLocation on client: {restore_dest_path}"
            raise Exception(msg)
        self.log.info("Restored data is same as content data")
        return restore_job