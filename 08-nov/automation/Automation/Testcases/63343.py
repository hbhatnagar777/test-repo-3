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

    new_content()       -- generates data of specified size in given directory

    deallocate_resources()      -- deallocates all the resources created for testcase environment

    allocate_resources()        -- allocates all the necessary resources for testcase environment

    previous_run_cleanup()      -- for deleting the left over backupset and storage policy from the previous run

    run_backup()        -- for running a backup job of given type

    run_auxcopy()       -- for running auxcopy job

    run_dv2()           -- for running DDB data verification job

    run_defrag()       -- for running defrag job

    verify_MA_clientGroup_selection()       -- validate that media agent selections were honored for given job


    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case



Prerequisites: None

Note regarding sql credentials :

    In order to ensure security,
    sql credentials have to be passed to the TC via config.json file under CoreUtils/Templates

    populate the following fields in config file as required,
    "SQL": {
        "Username": "<SQL_SERVER_USERNAME>",
        "Password": "<SQL_SERVER_PASSWORD>"
    }

    At the time of execution the creds will be automatically fetched by TC.

Input JSON:

"63343": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName1": "<Name of MediaAgent>",
        "MediaAgentName2": "<Name of MediaAgent>",
        "MediaAgentName3": "<Name of MediaAgent>",
        "MediaAgentName4": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "dedup_path1": "<path where dedup store to be created>" (optional argument),
        "dedup_path2": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:
1. setup test environment
2. create a subclient and run backups to it
3. run the following jobs with user defined MA/Client group selections :
    dv2
    auxcopy
    defrag
4. validate that user selection was honored for each job
5. deallocate resources


"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils import config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "Verify MA selection for DV2, Defrag, and Auxcopy when multiple reader media agents and client groups have been selected."
        self.tcinputs = {
            "MediaAgentName1": None,
            "MediaAgentName2": None,
            "MediaAgentName3": None,
            "MediaAgentName4": None
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.storage_pool_name = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.sidb_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.sql_password = None
        self.media_agent = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_pool = None
        self.library = None
        self.gdsp_name = None
        self.gdsp = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy = None
        self.tertiary_copy = None
        self.is_user_defined_storpool = False
        self.is_user_defined_dedup1 = False
        self.is_user_defined_dedup2 = False

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("dedup_path1"):
            self.is_user_defined_dedup1 = True
        if self.tcinputs.get("dedup_path2"):
            self.is_user_defined_dedup2 = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent1 = self.tcinputs["MediaAgentName1"]
        self.media_agent2 = self.tcinputs["MediaAgentName2"]
        self.media_agent3 = self.tcinputs["MediaAgentName3"]
        self.media_agent4 = self.tcinputs["MediaAgentName4"]
        self.client_group_name = str(self.id) + "_ClientGroup"
        suffix = f"{str(self.media_agent1)}_{str(self.client.client_name)}"
        self.storage_policy_name = f"{str(self.id)}_SP{suffix}"
        self.backupset_name = f"{str(self.id)}_BS{suffix}"
        self.subclient_name = f"{str(self.id)}_SC{suffix}"
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_obj1 = self.commcell.media_agents.get(self.media_agent1)
        self.media_agent_obj2 = self.commcell.media_agents.get(self.media_agent2)
        self.media_agent_obj3 = self.commcell.media_agents.get(self.media_agent3)
        self.media_agent_obj4 = self.commcell.media_agents.get(self.media_agent4)
        self.media_agent_machine1 = Machine(self.media_agent1, self.commcell)
        self.media_agent_machine2 = Machine(self.media_agent2, self.commcell)
        self.media_agent_machine3 = Machine(self.media_agent3, self.commcell)
        self.media_agent_machine4 = Machine(self.media_agent4, self.commcell)

        if not self.is_user_defined_dedup1 and "unix" in self.media_agent_machine1.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_dedup2 and "unix" in self.media_agent_machine2.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        drive_path_client = self.opt_selector.get_drive(
            self.client_machine)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")

        if self.is_user_defined_storpool:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.gdsp = self.commcell.storage_policies.get(self.storage_pool.global_policy_name)

        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent1 = self.opt_selector.get_drive(
            self.media_agent_machine1)
        self.testcase_path_media_agent1 = "%s%s" % (drive_path_media_agent1, self.id)

        drive_path_media_agent2 = self.opt_selector.get_drive(
            self.media_agent_machine2)
        self.testcase_path_media_agent2 = "%s%s" % (drive_path_media_agent2, self.id)

        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine1.join_path(
            self.testcase_path_media_agent1, "mount_path")

        if self.is_user_defined_dedup1:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path1 = self.tcinputs["dedup_path1"]
        else:
            self.dedup_store_path1 = self.media_agent_machine1.join_path(
                self.testcase_path_media_agent1, "dedup_store_path", "1")

        if self.is_user_defined_dedup2:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path2 = self.tcinputs["dedup_path2"]
        else:
            self.dedup_store_path2 = self.media_agent_machine2.join_path(
                self.testcase_path_media_agent1, "dedup_store_path", "2")

        # sql connections
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

    def new_content(self, machine, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                machine         (object)    machine object for client on which we are creating content
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        returns None
        """
        if machine.check_directory_exists(dir_path):
            machine.remove_directory(dir_path)
        machine.create_directory(dir_path)
        self.opt_selector.create_uncompressable_data(client=machine,
                                                     size=dir_size,
                                                     path=dir_path)

    def deallocate_resources(self):
        """removes all resources allocated by the Testcase"""
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("storage policy deleted")
        else:
            self.log.info("storage policy does not exist.")

        if not self.is_user_defined_storpool:
            # here the storage pool is automatically created by gdsp and therefore has the same name as gdsp.
            if self.commcell.storage_policies.has_policy(self.gdsp_name):
                self.commcell.storage_policies.delete(self.gdsp_name)
                self.log.info("gdsp deleted")
            else:
                self.log.info("gdsp does not exist.")
            if self.commcell.storage_policies.has_policy(self.gdsp_name + '2'):
                self.commcell.storage_policies.delete(self.gdsp_name + '2')
                self.log.info("gdsp 2 deleted")
            else:
                self.log.info("gdsp 2 does not exist.")

        self.log.info("clean up successful")

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.error("previous run clean up ERROR")
            raise Exception("ERROR:%s", exp)

    def allocate_resources(self):
        """creates all necessary resources for testcase to run"""
        # create new client group for TC
        if self.commcell.client_groups.has_clientgroup(self.client_group_name):
            self.commcell.client_groups.delete(self.client_group_name)
            self.log.info("deleting existing client group %s..", self.client_group_name)
        self.commcell.client_groups.add(self.client_group_name)
        self.log.info("creating new client group %s..", self.client_group_name)
        self.client_group = self.commcell.client_groups.get(self.client_group_name)
        self.client_group.add_clients(self.commcell.commserv_name)
        self.log.info("adding CS machine %s to client group", self.commcell.commserv_name)

        # create dedupe store paths
        if not self.media_agent_machine1.check_directory_exists(self.dedup_store_path1):
            self.media_agent_machine1.create_directory(self.dedup_store_path1)
            self.log.info("store path 1 created")
        else:
            self.log.info("store path 1 directory already exists")

        if not self.media_agent_machine1.check_directory_exists(self.dedup_store_path2):
            self.media_agent_machine1.create_directory(self.dedup_store_path2)
            self.log.info("store path 2 created")
        else:
            self.log.info("store path 2 directory already exists")

        # create library if not provided
        if not self.is_user_defined_storpool:
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.media_agent1, self.mount_path)

        # create gdsp if not provided
        if not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent1,
                ddb_path=self.dedup_store_path1,
                ddb_media_agent=self.media_agent1)
            self.gdsp2 = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name + '2',
                library_name=self.library_name,
                media_agent_name=self.media_agent1,
                ddb_path=self.dedup_store_path2,
                ddb_media_agent=self.media_agent1)
        # create dependent storage policy
        self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.library_name,
                                                                 media_agent=self.media_agent1,
                                                                 global_policy_name=self.gdsp_name,
                                                                 dedup_media_agent=self.media_agent1,
                                                                 dedup_path=self.dedup_store_path1)

        # create backupset and subclient
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name,
                                                             self.agent)
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name,
                                                            self.subclient_name,
                                                            self.storage_policy_name,
                                                            self.content_path,
                                                            self.agent)

        # create primary copy object for storage policy
        self.primary_copy = self.storage_policy.get_copy(copy_name="primary")

        # create secondary copy for storage policy
        self.secondary_copy = self.mm_helper.configure_secondary_copy(
            sec_copy_name=self.storage_policy_name + "_secondary",
            storage_policy_name=self.storage_policy_name,
            ma_name=self.media_agent1,
            global_policy_name=self.gdsp2.storage_policy_name)

        # Remove Association with System Created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.storage_policy_name + "_secondary")

        # set multiple readers for subclient
        self.subclient.data_readers = 10
        self.subclient.allow_multiple_readers = True

        # set enc on primary copy BlowFish 128
        self.gdsp.get_copy("Primary_Global").set_encryption_properties(re_encryption=True, encryption_type="BlowFish",
                                                                       encryption_length=128)
        # set re-encrypt on secondary as GOST 256
        self.gdsp2.get_copy("Primary_Global").set_encryption_properties(re_encryption=True, encryption_type="GOST",
                                                                        encryption_length=256)

        # sharing mountpath - add in support for HS config later
        self.library.share_mount_path(self.media_agent2, self.mount_path, access_type=22, mount_path=self.mount_path)
        self.library.share_mount_path(self.media_agent3, self.mount_path, access_type=22, mount_path=self.mount_path)
        self.library.share_mount_path(self.media_agent4, self.mount_path, access_type=22, mount_path=self.mount_path)

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        job = self.subclient.backup(backup_level=job_type)
        self.log.info("starting backup %s job with job id - %s", job_type, job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

    def run_dv2(self):
        """
        Triggers a dv2 job with given media agent selections

        Returns Job object
        """
        request_xml = f"""<TMMsg_CreateTaskReq>                            
                          <processinginstructioninfo/>                            
                          <taskInfo>
                            <task>
                              <taskFlags>
                                <disabled>false</disabled>
                              </taskFlags>
                              <policyType>DATA_PROTECTION</policyType>
                              <taskType>IMMEDIATE</taskType>
                              <initiatedFrom>COMMANDLINE</initiatedFrom>
                              <alert>
                                <alertName></alertName>
                              </alert>
                            </task>
                            <associations>
                              <subclientName></subclientName>
                              <backupsetName></backupsetName>
                              <instanceName></instanceName>
                              <appName></appName>
                              <clientName></clientName>
                              <copyName>Primary_Global</copyName>
                              <storagePolicyName>{self.gdsp_name}</storagePolicyName>
                              <sidbStoreName>{self.store_name}</sidbStoreName>
                            </associations>
                            <subTasks>
                              <subTask>
                                <subTaskType>ADMIN</subTaskType>
                                <operationType>ARCHIVE_CHECK</operationType>
                              </subTask>
                              <options>
                                <backupOpts>
                                  <backupLevel>INCREMENTAL</backupLevel>
                                  <mediaOpt>
                                    <auxcopyJobOption>
                                      <useMaximumStreams>true</useMaximumStreams>
                                      <maxNumberOfStreams>0</maxNumberOfStreams>
                                      <allCopies>true</allCopies>
                                      <useScallableResourceManagement>true</useScallableResourceManagement>
                                      <totalJobsToProcess>1000</totalJobsToProcess>
                                      <jobsTimeRange>
                                        <fromTimeValue>1970-01-01 05:30:00</fromTimeValue>
                                        <toTimeValue>2038-01-19 08:44:07</toTimeValue>
                                        <TimeZoneName>(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi</TimeZoneName>
                                      </jobsTimeRange>
                                      <mediaAgents>
                                        <mediaAgentName>{self.media_agent2}</mediaAgentName>
                                      </mediaAgents>
                                      <mediaAgents>
                                        <mediaAgentName>{self.media_agent3}</mediaAgentName>
                                      </mediaAgents>
                                      <clientGroups>
                                        <clientGroupName>{self.client_group_name}</clientGroupName>
                                      </clientGroups>
                                    </auxcopyJobOption>
                                  </mediaOpt>
                                  <vsaBackupOptions/>
                                </backupOpts>
                                <restoreOptions>
                                  <virtualServerRstOption>
                                    <diskLevelVMRestoreOption>
                                      <esxServerName></esxServerName>
                                    </diskLevelVMRestoreOption>
                                    <isBlockLevelReplication>false</isBlockLevelReplication>
                                  </virtualServerRstOption>
                                </restoreOptions>
                                <adminOpts>
                                  <archiveCheckOption>
                                    <ddbVerificationLevel>DDB_AND_DATA_VERIFICATION</ddbVerificationLevel>
                                    <backupLevel>FULL</backupLevel>
                                  </archiveCheckOption>
                                  <contentIndexingOption>
                                    <subClientBasedAnalytics>false</subClientBasedAnalytics>
                                  </contentIndexingOption>
                                </adminOpts>
                                <commonOpts>
                                  <startUpOpts>
                                    <startInSuspendedState>false</startInSuspendedState>
                                    <priority>166</priority>
                                    <useDefaultPriority>true</useDefaultPriority>
                                    <startWhenActivityIsLow>false</startWhenActivityIsLow>
                                  </startUpOpts>
                                  <jobDescription></jobDescription>
                                </commonOpts>
                              </options>
                              <subTaskOperation>OVERWRITE</subTaskOperation>
                            </subTasks>
                          </taskInfo>                            
                        </TMMsg_CreateTaskReq>"""
        job_id = self.commcell._qoperation_execute(request_xml)['jobIds'][0]
        return self.commcell.job_controller.get(job_id)

    def run_auxcopy(self):
        """
                Triggers an auxcopy job with given media agent selections

                Returns Job object
        """
        request_xml = f"""<TMMsg_CreateTaskReq>
                          <processinginstructioninfo/>
                          <taskInfo>
                            <task>
                              <taskFlags>
                                <disabled>false</disabled>
                                <isEdgeDrive>false</isEdgeDrive>
                              </taskFlags>
                              <policyType>DATA_PROTECTION</policyType>
                              <taskType>IMMEDIATE</taskType>
                              <initiatedFrom>COMMANDLINE</initiatedFrom>
                              <alert>
                                <alertName></alertName>
                              </alert>
                            </task>
                            <associations>
                              <subclientName></subclientName>
                              <backupsetName></backupsetName>
                              <instanceName></instanceName>
                              <appName></appName>
                              <clientName></clientName>
                              <copyName>{self.secondary_copy.copy_name}</copyName>
                              <storagePolicyName>{self.storage_policy_name}</storagePolicyName>
                            </associations>
                            <subTasks>
                              <subTask>
                                <subTaskType>ADMIN</subTaskType>
                                <operationType>AUX_COPY</operationType>
                              </subTask>
                              <options>
                                <backupOpts>
                                  <mediaOpt>
                                    <markMediaFullOnSuccess>false</markMediaFullOnSuccess>
                                    <startNewMedia>false</startNewMedia>
                                    <auxcopyJobOption>
                                      <useMostRecentBackupForAuxcopy>false</useMostRecentBackupForAuxcopy>
                                      <useMaximumStreams>true</useMaximumStreams>
                                      <maxNumberOfStreams>0</maxNumberOfStreams>
                                      <allCopies>false</allCopies>
                                      <waitForAllParallelCopyResources>false</waitForAllParallelCopyResources>
                                      <useScallableResourceManagement>true</useScallableResourceManagement>
                                      <ignoreDataVerificationFailedJobs>false</ignoreDataVerificationFailedJobs>
                                      <totalJobsToProcess>1000</totalJobsToProcess>
                                      <jobsTimeRange>
                                        <fromTimeValue>1969-12-31 19:00:00</fromTimeValue>
                                        <toTimeValue>2038-01-18 22:14:07</toTimeValue>
                                        <TimeZoneName>(UTC-05:00) Eastern Time (US &amp; Canada)</TimeZoneName>
                                      </jobsTimeRange>
                                      <mediaAgents>
                                        <mediaAgentName>{self.media_agent2}</mediaAgentName>
                                      </mediaAgents>
                                      <mediaAgents>
                                        <mediaAgentName>{self.media_agent3}</mediaAgentName>
                                      </mediaAgents>
                                      <clientGroups>
                                        <clientGroupName>{self.client_group_name}</clientGroupName>
                                      </clientGroups>
                                    </auxcopyJobOption>
                                  </mediaOpt>
                                  <vaultTrackerOpt>
                                    <excludeMediaNotCopied>false</excludeMediaNotCopied>
                                    <exportMediaAfterJobFinishes>false</exportMediaAfterJobFinishes>
                                    <mediaStatus>
                                      <all>false</all>
                                      <active>false</active>
                                      <full>true</full>
                                      <overwriteProtected>true</overwriteProtected>
                                      <bad>true</bad>
                                    </mediaStatus>
                                    <exportLocation>
                                      <locationName>Not Available</locationName>
                                    </exportLocation>
                                    <trackTransit>false</trackTransit>
                                    <inTransitLocation>
                                      <locationName>Not Available</locationName>
                                    </inTransitLocation>
                                    <useVirtualMailSlots>false</useVirtualMailSlots>
                                    <filterMediaByRetention>false</filterMediaByRetention>
                                    <mediaWithExtendedRetentionJobs>false</mediaWithExtendedRetentionJobs>
                                  </vaultTrackerOpt>
                                  <vsaBackupOptions/>
                                </backupOpts>
                                <restoreOptions>
                                  <virtualServerRstOption>
                                    <diskLevelVMRestoreOption>
                                      <esxServerName></esxServerName>
                                    </diskLevelVMRestoreOption>
                                    <isBlockLevelReplication>false</isBlockLevelReplication>
                                  </virtualServerRstOption>
                                </restoreOptions>
                                <adminOpts>
                                  <archiveCheckOption/>
                                  <contentIndexingOption>
                                    <subClientBasedAnalytics>false</subClientBasedAnalytics>
                                  </contentIndexingOption>
                                </adminOpts>
                                <commonOpts>
                                  <startUpOpts>
                                    <startInSuspendedState>false</startInSuspendedState>
                                    <priority>266</priority>
                                    <useDefaultPriority>true</useDefaultPriority>
                                    <startWhenActivityIsLow>false</startWhenActivityIsLow>
                                  </startUpOpts>
                                  <jobRetryOpts>
                                    <runningTime>
                                      <enableTotalRunningTime>false</enableTotalRunningTime>
                                      <totalRunningTime>01:00:00</totalRunningTime>
                                    </runningTime>
                                    <killRunningJobWhenTotalRunningTimeExpires>false</killRunningJobWhenTotalRunningTimeExpires>
                                    <enableNumberOfRetries>false</enableNumberOfRetries>
                                    <numberOfRetries>0</numberOfRetries>
                                  </jobRetryOpts>
                                  <jobDescription></jobDescription>
                                </commonOpts>
                              </options>
                              <subTaskOperation>OVERWRITE</subTaskOperation>
                            </subTasks>
                          </taskInfo>
                        </TMMsg_CreateTaskReq>"""
        job_id = self.commcell._qoperation_execute(request_xml)['jobIds'][0]
        return self.commcell.job_controller.get(job_id)

    def run_defrag(self):
        """
            Triggers a defrag job with given media agent selections

            Returns Job object
        """
        request_xml = f"""<TMMsg_CreateTaskReq>
                                  <processinginstructioninfo/>
                                  <taskInfo>
                                    <task>
                                      <taskFlags>
                                        <disabled>false</disabled>
                                      </taskFlags>
                                      <policyType>DATA_PROTECTION</policyType>
                                      <taskType>IMMEDIATE</taskType>
                                      <initiatedFrom>COMMANDLINE</initiatedFrom>
                                      <alert>
                                        <alertName></alertName>
                                      </alert>
                                    </task>
                                    <associations>
                                      <subclientName></subclientName>
                                      <backupsetName></backupsetName>
                                      <instanceName></instanceName>
                                      <appName></appName>
                                      <clientName></clientName>
                                      <copyName>Primary_Global</copyName>
                                      <storagePolicyName>{self.gdsp_name}</storagePolicyName>
                                      <sidbStoreName>{self.store_name}</sidbStoreName>
                                    </associations>
                                    <subTasks>
                                      <subTask>
                                        <subTaskType>ADMIN</subTaskType>
                                        <operationType>ARCHIVE_CHECK</operationType>
                                      </subTask>
                                      <options>
                                        <backupOpts>
                                          <backupLevel>INCREMENTAL</backupLevel>
                                          <mediaOpt>
                                            <auxcopyJobOption>
                                              <useMaximumStreams>true</useMaximumStreams>
                                              <maxNumberOfStreams>0</maxNumberOfStreams>
                                              <allCopies>true</allCopies>
                                              <mediaAgent/>
                                              <useScallableResourceManagement>true</useScallableResourceManagement>
                                              <totalJobsToProcess>1000</totalJobsToProcess>
                                              <jobsTimeRange>
                                                <fromTimeValue>1970-01-01 05:30:00</fromTimeValue>
                                                <toTimeValue>2038-01-19 08:44:07</toTimeValue>
                                                <TimeZoneName>(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi</TimeZoneName>
                                              </jobsTimeRange>
                                              <mediaAgents>
                                                <mediaAgentName>{self.media_agent2}</mediaAgentName>
                                              </mediaAgents>
                                              <mediaAgents>
                                                <mediaAgentName>{self.media_agent3}</mediaAgentName>
                                              </mediaAgents>
                                              <clientGroups>
                                                <clientGroupName>{self.client_group_name}</clientGroupName>
                                              </clientGroups>
                                            </auxcopyJobOption>
                                          </mediaOpt>
                                          <vsaBackupOptions/>
                                        </backupOpts>
                                        <restoreOptions>
                                          <virtualServerRstOption>
                                            <diskLevelVMRestoreOption>
                                              <esxServerName></esxServerName>
                                            </diskLevelVMRestoreOption>
                                            <isBlockLevelReplication>false</isBlockLevelReplication>
                                          </virtualServerRstOption>
                                        </restoreOptions>
                                        <adminOpts>
                                          <archiveCheckOption>
                                            <ddbVerificationLevel>DDB_DEFRAGMENTATION</ddbVerificationLevel>
                                            <backupLevel>FULL</backupLevel>
                                            <defragmentationPercentage>20</defragmentationPercentage>
                                            <ocl>true</ocl>
                                            <fullOCL>false</fullOCL>
                                            <runDefrag>true</runDefrag>
                                          </archiveCheckOption>
                                          <contentIndexingOption>
                                            <subClientBasedAnalytics>false</subClientBasedAnalytics>
                                          </contentIndexingOption>
                                        </adminOpts>
                                        <commonOpts>
                                          <startUpOpts>
                                            <startInSuspendedState>false</startInSuspendedState>
                                            <priority>166</priority>
                                            <useDefaultPriority>true</useDefaultPriority>
                                            <startWhenActivityIsLow>false</startWhenActivityIsLow>
                                          </startUpOpts>
                                          <jobDescription></jobDescription>
                                        </commonOpts>
                                      </options>
                                      <subTaskOperation>OVERWRITE</subTaskOperation>
                                    </subTasks>
                                  </taskInfo>   
                                </TMMsg_CreateTaskReq>"""
        job_id = self.commcell._qoperation_execute(request_xml)['jobIds'][0]
        return self.commcell.job_controller.get(job_id)

    def verify_MA_clientGroup_selection(self, iter, job_type, job_id, media_agents=[], clientgroups=[]):
        """
        Verifies that media agent/client group selection was honored for the auxcopy/dv2/defrag job

            Args:
                iter        (int)       if 1, then check for CS in reader MAs used, if 2, then check for MA4 in reader MAs used
                job_type    (str)       type of job being validated ["auxcopy"/"dv2"/"defrag"]
                job_id      (str/int)    id of the auxcopy/dv2/defrag job to be verified
                media_agents        (list)      list of media agents that had been selected for the job
                clientgroups        (list)      list of client groups that had been selected for the job

            Returns Boolean
        """
        query = ""
        if job_type == "dv2":
            query = f"""select name from app_client where id in 
                    (select distinct srcMAId from archchunktoverify2history where adminjobid = {job_id})"""
        elif job_type == "auxcopy":
            query = f"""select name from app_client where id in 
                    (select distinct srcMAId from archchunktoreplicatehistory where adminjobid = {job_id})"""
        elif job_type == "defrag":
            query = f"""select name from app_client where id in 
                                (select distinct clientid from RMReservations where jobid in ({job_id}))"""
        else:
            raise Exception("invalid job_type provided!")
        self.log.info("reader mediaagent(s) input by user for %s job are : %s", job_type,
                      str(media_agents + clientgroups))
        self.log.info("running query : %s", query)
        self.csdb.execute(query)
        MA_list = [row[0] for row in self.csdb.rows]
        self.log.info("reader mediaagent(s) used by %s job are : %s", job_type, str(MA_list))
        if set(MA_list).issubset(set(media_agents + clientgroups)) and len(MA_list) > 1:
            if iter == 1:
                if self.commcell.commserv_name not in MA_list:
                    return True
                else:
                    self.log.error("CS machine %s was used as reader MA! not expected!", self.commcell.commserv_name)
                    return False
            elif iter == 2:
                if self.media_agent4 in MA_list:
                    return True
                else:
                    self.log.error("MA4 %s was not used as reader MA! not expected!", self.media_agent4)
                    return False
        else:
            return False

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # add data to subclient content
            self.log.info("adding content to subclient..")
            self.new_content(machine=self.client_machine,
                             dir_path=self.client_machine.join_path(self.content_path, "new"),
                             dir_size=8)
            job = self.run_backup("Full")

            # getting engine details
            self.dedupe_engine = self.commcell.deduplication_engines.get(self.gdsp_name, "Primary_Global")
            self.store = self.dedupe_engine.get(self.dedupe_engine.all_stores[0][0])
            self.store_name = self.store.store_name
            self.substore = self.store.get(self.store.all_substores[0][0])

            validation_failure_count = 0
            job_failures = []

            for iter in range(1, 3):
                if iter == 1:
                    self.log.info("*" * 30)
                    self.log.info(
                        "ITERATION #1 :: Client group contains CS client only / We should not pick it(not part of MP sharing)")

                elif iter == 2:
                    self.log.info("*" * 30)
                    self.log.info(
                        "ITERATION #2 :: Client group contains CS client + MA4 / We should pick MA4")
                    self.client_group.add_clients(self.media_agent4)
                    self.log.info("adding MA4 %s to client group %s..", self.media_agent4, self.client_group_name)

                # adding new content and running a full backup iteratively
                for index in range(1, 3):
                    # add data to subclient content
                    self.log.info("adding content to subclient..")
                    self.new_content(machine=self.client_machine,
                                     dir_path=self.client_machine.join_path(self.content_path, str(iter), "new",
                                                                            str(index)),
                                     dir_size=8)
                    job = self.run_backup("Full")
                    # run full backup
                    self.new_content(machine=self.client_machine,
                                     dir_path=self.client_machine.join_path(self.content_path, str(iter), "new",
                                                                            str(index), "incremental_data"),
                                     dir_size=2)
                    job = self.run_backup("Incremental")

                for job_type in ["dv2", "auxcopy", "defrag"]:
                    try:
                        if job_type == "dv2":
                            job = self.run_dv2()
                        elif job_type == "auxcopy":
                            job = self.run_auxcopy()
                        elif job_type == "defrag":
                            job = self.run_defrag()
                        self.log.info(
                            "starting %s job #%d - ID %s with the following mediaagent "
                            "%s, %s and client group %s selected as reader mediagent(s)",
                            job_type, iter, job.job_id, self.media_agent2, self.media_agent3, self.client_group_name)

                        if not job.wait_for_completion():
                            raise Exception(
                                f"Failed to run {job_type} job #{iter} with error: {job.delay_reason}"
                            )
                        self.log.info("%s job %d: %s completed successfully", job_type, iter, job.job_id)

                        if self.verify_MA_clientGroup_selection(iter, job_type, job.job_id,
                                                                media_agents=[self.media_agent2, self.media_agent3],
                                                                clientgroups=self.client_group.associated_clients):

                            self.log.info("MA/client group selection was honoured for %s job #%d!", job_type, iter)

                        else:
                            self.log.error("MA/client group selection was not honoured for %s job #%d!", job_type, iter)
                    except Exception as exp:
                        validation_failure_count += 1
                        job_failures.append(f"{job_type} job #{iter} failed ::: " + str(exp))
                        self.log.error("ran into errors while running %s job #%d!", job_type, iter)

            if validation_failure_count == 0:
                self.log.info("All Validations Completed.. Testcase executed successfully..")
            elif validation_failure_count > 0:
                self.log.error("all jobs did not complete successfully!!")
                raise Exception(str(job_failures))
            else:
                self.log.error("All validations were not successful!!")
                raise Exception("MA/client group selection validations failed!!")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # removing initialized resources
        try:
            self.log.info("cleaning up resources post execution..")
            self.deallocate_resources()
        except:
            self.log.warning("Cleanup Failed, please check setup ..")
