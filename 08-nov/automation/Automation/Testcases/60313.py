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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    create_resources()  --  Create all the required commvault entities like subclient, storage policy etc.

    run_backups_on_subclient)   --  Run multiple  backups on given type of IDA subclient based on user demand.

    add_secondary_copy()        --  Add a secondary copy to storage policy

    run_aux_copy_with_induced_error()   --  Run auxcopy after inducing error by setting destinatin ddb
                                            store value to 0

    dump_archchunktoreplicate() --  Log the output of ArchChunkToReplicate table for given Auxcopy Job ID.

    dump_archjobstreamstatus()  --  Log the output of ArchJobStreamStatus table for given Auxcopy Job ID.

    verify_auxcopy_job_failure()    --  verify Auxcopy job failure reason

    suspend_resume_auxcopy()    --  suspend and resume the Auxcopy job

    verify_auxcopy_job_successful_run() -- Verify successful completion of auxcopy job

    cleanup_resources()     --   Cleanup the commvault entities created by this test case

    verify_subc_association_auxcopy()   --  Verify subclient to DDB association for secondary copy

    create_sql_subclient()  --  Create a new Database and a SQL DB subclient to back up this content

    create_vsa_subclient()  --  Create a VSA subclient

    create_fs_subclient()   --  Create a File System IDA subclient

    validate_subclient_ddb_mapping()    --  Validate whether a subclient has correctly got
                                            mapped to DDB in a given copy

    validate_dedup_stores_for_copy()    -- Validate whether 3 DDBs are created for given storage policy copy with
                                        correct apptypegroupid

"""
import time
from cvpysdk.constants import VSAObjects
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from Application.SQL.sqlhelper import SQLHelper
from Application.SQL import sqlconstants
from AutomationUtils import config


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Auxcopy should go to WAITING state when DestSIDBStoreID in ArchChunkToReplicate is 0 " \
                    "for some chunks"
        self.tcinputs = {
            "MediaAgentName": None,
            "SecondaryCopyMediaAgent": None,
            "DatabaseClientName": None,
            "DatabaseAgentname": None,
            "HyperVBackupVM": None,
            "HyperVClientName": None,
            "HyperVAgentName": None
        }

        # Local variables
        self.backupset_obj = None
        self.mediaagentname = ""
        self.machineobj = None
        self.ma_machineobj = None
        self.dedup_path = None
        self.storage_policy_name = None
        self.library_name = None
        self.backupset_name = None
        self.content_path = None
        self.client_system_drive = None
        self.deduphelper_obj = None
        self.mmhelper_obj = None
        self.sqlobj = None
        self.sqlhelper = None
        self.vsaclient = None
        self.vsaagent = None
        self.vsainstance = None
        self.backup_vm_name = None
        self.sqlclient = None
        self.sqlagent = None
        self.sqlinstance = None
        self.vsa_backupset_name = None
        self.sql_backupset_name = None
        self.fs_subclient_name = None
        self.vsa_subclient_name = None
        self.sqluser = None
        self.sqlpassword = None
        self.sql_subclient_name = None
        self.dbname = None
        self.ma_ddb_drive = None
        self.copy_ddb_mapping_dict = {}
        self.mountpath = None
        self.library_name_2 = None
        self.storage_policy = None
        self.auxcopy_job = None
        self.fs_subc_obj = None
        self.sql_subclient_obj = None
        self.hyperv_subc_obj = None
        self.csdb_sql_user = None
        self.csdb_sql_password = None
        self.copy_name = None
        self.aux_copy_job = None
        self.secondary_copy_obj = None
        self.secondary_mountpath = None
        self.secondary_dedup_path = None
        self.ma_sec_ddb_drive = None
        self.ma_sec_machineobj = None

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        self.mediaagentname = self.tcinputs["MediaAgentName"]

        self.backup_vm_name = self.tcinputs['HyperVBackupVM']
        self.machineobj = Machine(self.client)
        self.client_system_drive = optionobj.get_drive(self.machineobj)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        self.ma_sec_machineobj = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        self.ma_ddb_drive = optionobj.get_drive(self.ma_machineobj, 50)
        self.ma_sec_ddb_drive = optionobj.get_drive(self.ma_sec_machineobj, 50)
        if not self.ma_ddb_drive:
            self.log.error("Not enough space [50G] available to create disk library for primary copy")
            raise Exception("Not enough space [50G] available to create disk library. "
                            "Pre-requisite error for primary copy.")
        if not self.ma_sec_ddb_drive:
            self.log.error("Not enough space [50G] available to create disk library for secondary copy")
            raise Exception("Not enough space [50G] available to create disk library. "
                            "Pre-requisite error for secondary copy.")

        self.mountpath = self.ma_machineobj.join_path(self.ma_ddb_drive, self.id, "MP1")
        self.secondary_mountpath = self.ma_sec_machineobj.join_path(self.ma_sec_ddb_drive, self.id, "SEC_MP1")
        timestamp_suffix = optionobj.get_custom_str()
        self.dbname = f"{self.id}_{timestamp_suffix}"
        self.dedup_path = self.ma_machineobj.join_path(self.ma_ddb_drive, "DDBs", f"{self.id}",
                                                       f"tc_{self.id}_{timestamp_suffix}")
        self.secondary_dedup_path = self.ma_sec_machineobj.join_path(self.ma_sec_ddb_drive, "DDBs", f"{self.id}",
                                                       f"tc_{self.id}_{timestamp_suffix}")
        self.storage_policy_name = f"SP_{self.id}"
        self.library_name = f"LIB_{self.id}"
        self.library_name_2 = f"LIB_SECONDARY_{self.id}"
        self.backupset_name = f"FS_BKPSET_{self.id}"
        self.vsa_backupset_name = "defaultBackupSet"
        self.sql_backupset_name = "defaultBackupSet"
        self.fs_subclient_name = f"FS_SUBC_{self.id}"
        self.vsa_subclient_name = "default"
        self.sql_subclient_name = f"SQL_SUBC_{self.id}"
        self.content_path = self.machineobj.join_path(self.client_system_drive, f"content_{self.id}")
        self.backupset = "defaultBackupSet"
        self.subclient = "default"
        self.copy_name = "Secondary_Copy"
        self.csdb_sql_user = config.get_config().SQL.Username
        self.csdb_sql_password = config.get_config().SQL.Password

        self.deduphelper_obj = DedupeHelper(self)
        self.mmhelper_obj = MMHelper(self)
        self.sqluser = self.tcinputs["sqluser"]
        self.sqlpassword =self.tcinputs["sqlpassword"]


        vsa_client = self.tcinputs["HyperVClientName"]
        vsa_agent = self.tcinputs['HyperVAgentName']

        sql_client = self.tcinputs["DatabaseClientName"]
        sql_agent = self.tcinputs["DatabaseAgentname"]

        self.log.info("Creating requird objects for SQL subclient creation")
        self.sqlclient = self.commcell.clients.get(sql_client)
        self.sqlagent = self.sqlclient.agents.get(sql_agent)
        sqlinstance_keys = next(iter(self.sqlagent.instances.all_instances))
        self.sqlinstance = self.sqlagent.instances.get(sqlinstance_keys)

        self.log.info("Creating requird objects for VSA subclient creation")
        self.vsaclient = self.commcell.clients.get(vsa_client)
        self.vsaagent = self.vsaclient.agents.get(vsa_agent)
        instancekeys = next(iter(self.vsaagent.instances.all_instances))
        self.vsainstance = self.vsaagent.instances.get(instancekeys)

        self.sqlhelper = SQLHelper(
            self,
            self.sqlclient,
            self.sqlinstance.instance_name,
            self.sqluser,
            self.sqlpassword)

    def create_resources(self):
        """
        Create all the required commvault entities like subclient, storage policy etc.
        """

        self.log.info("----------Configuring TC environment-----------")
        self.log.info("---Create new Library---")

        # Create new library

        self.mmhelper_obj.configure_disk_library(self.library_name, self.mediaagentname, self.mountpath)
        self.mmhelper_obj.configure_disk_library(self.library_name_2, self.tcinputs['SecondaryCopyMediaAgent'],
                                                 self.secondary_mountpath)

        self.log.info("---Configuring backup set---")

        self.log.info("Creating new storage policy - %s", self.storage_policy_name)
        self.storage_policy =self.deduphelper_obj.configure_dedupe_storage_policy(self.storage_policy_name,
                                                                                    self.library_name,
                                                                                    self.mediaagentname,
                                                                                    self.dedup_path)
        self.log.info("---Successfully configured storage policy - %s", self.storage_policy_name)
        copy = self.storage_policy.get_copy('Primary')
        self.log.info("setting copy retention: 1 day, 0 cycle")
        copy.copy_retention = (1, 0, 1)

        self.create_fs_subclient()
        self.create_sql_subclient()
        self.create_vsa_subclient()

    def run_backups_on_subclient(self, subclient_ida_type, backup_count=1):
        """
        Run multiple  backups on given type of IDA subclient based on user demand.

        Args:
            subclient_ida_type (str)    --  IDA type of the subclient [ fs or database or vsa ]
            backup_count(int)           -- How many consecutive backups to run
        """
        subc_obj = None
        if subclient_ida_type.lower() == "fs":
            subc_obj = self.fs_subc_obj
        if subclient_ida_type.lower() == "database":
            subc_obj = self.sql_subclient_obj
        if subclient_ida_type.lower() == "vsa":
            subc_obj = self.hyperv_subc_obj

        for iteration in range(0, backup_count):
            self.log.info("Launching %s IDA Backup No. - [%s]", subclient_ida_type, iteration+1)
            fulljob_obj = subc_obj.backup("Full")
            self.log.info("Successfully initiated a backup job on %s IDA subclient with jobid - %s",
                          subclient_ida_type, fulljob_obj.job_id)
            if not fulljob_obj.wait_for_completion():
                raise Exception(f"Backup job [{fulljob_obj.job_id}] did not complete - [{fulljob_obj.delay_reson}]")

            self.log.info("Successfully completed the %s IDA subclient backup job with jobid - %s",
                          subclient_ida_type, fulljob_obj.job_id)


    def add_secondary_copy(self):
        """
        Add a secondary copy to storage policy
        """
        if self.storage_policy.has_copy(self.copy_name):
            self.log.info("Secondary copy already exists. Deleting secondary copy.")
            self.storage_policy.delete_secondary_copy(self.copy_name)
        self.log.info("Adding secondary dedup copy")
        self.secondary_copy_obj = self.deduphelper_obj.configure_dedupe_secondary_copy(
            self.storage_policy, self.copy_name, self.library_name_2, self.tcinputs['SecondaryCopyMediaAgent'],
            self.secondary_dedup_path, self.tcinputs['SecondaryCopyMediaAgent'])
        self.log.info("Removing Auto-copy schedule")
        self.mmhelper_obj.remove_autocopy_schedule(self.storage_policy_name, self.copy_name)


    def run_aux_copy_with_induced_error(self):
        """
        Run auxcopy after inducing error by setting destinatin ddb store value to 0
        """
        self.log.info("Running AuxCopy job")
        self.aux_copy_job = self.storage_policy.run_aux_copy(use_scale=True, streams=1)
        self.log.info("Launched AuxCopy job - [%s]", self.aux_copy_job.job_id)

        self.log.info("Waiting for AuxCopy job to enter Running state")
        count = 10
        while count > 0 and self.aux_copy_job.status.lower() != 'running':
            self.log.info("Attempt [%s] : Job Status is not Running - current Status - [%s]", count,
                          self.aux_copy_job.status)
            time.sleep(5)
            count = count-1
        self.log.info("Job Status is Running.")

        for attempt in (1,4):
            self.log.info("Attempt [%s] : Manipulating DestSIDBStoreId in ArchChunkToReplicate", attempt)
            self.dump_archchunktoreplicate()
            populated_rows = self.dump_archjobstreamstatus()

            if populated_rows:
                self.log.info("Setting DestSIDBStoreID = 0 for jobs from DDBs other than picked DDB")
                query = f"update archchunktoreplicate set destSIDBStoreId = 0 where destSIDBStoreId <> " \
                        f"(select destsidbstoreid from archjobstreamstatus where jobid = {self.aux_copy_job.job_id}" \
                        f" and DestStreamNum <> 0)"
                self.log.info("QUERY ==> %s", query)
                self.mmhelper_obj.execute_update_query(query, self.csdb_sql_password, self.csdb_sql_user)
                self.log.info("Successfully executed update query to modify DestSIDBStoreId")
                self.dump_archchunktoreplicate()
                self.dump_archjobstreamstatus()
                break
            else:
                self.log.warning("ArchJobStreamStatus table is not yet populated. Trying after 10 seconds")
                time.sleep(10)

    def dump_archchunktoreplicate(self):
        """
        Log the output of ArchChunkToReplicate table for given Auxcopy Job ID.
        """
        self.log.info("Dumping information about ArchChunkToReplicate")
        query = f"select DestSIDBStoreId, * from ArchChunkToReplicate where adminjobid={self.aux_copy_job.job_id}"
        self.log.info("QUERY ==> %s", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info("==" * 30)
        self.log.info(rows)
        self.log.info("==" * 30)
        return len(rows)

    def dump_archjobstreamstatus(self):
        """
        Log the output of ArchJobStreamStatus table for given Auxcopy Job ID.
        """
        self.log.info("Dumping information about ArchJobStreamStatus")
        query = f"select DestSIDBStoreId, * from ArchJobStreamStatus where jobid={self.aux_copy_job.job_id}"
        self.log.info("QUERY ==> %s", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info("==" * 30)
        self.log.info(rows)
        self.log.info("==" * 30)
        return len(rows)

    def verify_auxcopy_job_failure(self, job_no):
        """
        verify Auxcopy job failure reason

        Args:

        job_no (int)    --  Auxcopy job number during flow of TC - 1 or 2 etc.
        """
        count = 20
        failure_reason=""
        jpr=""
        while count > 0 and self.aux_copy_job.status.lower() != 'waiting':
            self.log.info("Attempt [%s]: Waiting for Auxcopy job status to become WAITING", count)
            time.sleep(60)
            count-=1
        if count == 0:
            self.log.error("Auxcopy job is not in WAITING state even after timeout of 10 minutes.")
            raise Exception(f"Auxcopy job {self.aux_copy_job.job_id} did not enter WAITING state - Returning Failure")
        else:
            self.log.info("AuxCopy Job is in WAITING state. Verifying Failure Reason and JPR after few minutes")
            for itr in range(1,10):
                self.log.info("Checking status after 3 minutes - Attempt [%s]", itr)
                time.sleep(180)
                failure_reason = self.aux_copy_job.details['jobDetail']['progressInfo']['dataCopiedInfo'][0]['failureReason']
                jpr =self.aux_copy_job.delay_reason
                self.log.info("In AuxCopy Job Attempt [%s] : \n JPR = [%s] \n Failure Reason = [%s]", job_no, jpr,
                              failure_reason)

                if not jpr and not failure_reason:
                    self.log.info("Failure Reason/JPR is not yet populated. Checking again after some time.")
                else:
                    self.log.info("Failure Reason/JPR is populated and not empty.")
                    break
        if not jpr and not failure_reason:
            self.log.error("JPR or failure reason is not populated. Failing the test case.")
            raise Exception("JPR or failure reason is not populated. Mostly the job completed successfully without going"
                            " to WAITING state. Failing this case.")
        if jpr.count('Unable to associate subclient to DDB Advice: Check data access node(s) set '
                                  'on client'):
            self.log.info("Successfully verified the jpr / failure reason for Aux Copy Job [%s]",
                          self.aux_copy_job.job_id)
        else:
            self.log.warning("Failed to verify the jpr of Aux Copy Job [%s]", self.aux_copy_job.job_id)
            self.log.info("Verifying if JPR is related to Resource Allocation")
            if jpr.count('Unable to allocate resources. Please check the Progress tab for more details'):
                self.log.info("JPR is set to Resource Allocation Error. Checking Progress tab string.")
                if failure_reason.count('Unable to associate subclient to DDB Advice: Check data access node(s) set '
                                  'on client'):
                    self.log.info("Successfully verified the failure reason for Aux Copy Job [%s]",
                          self.aux_copy_job.job_id)
            else:
                raise Exception(f"Verification of JPR / Failure Reason failed for AuxCopy Job {self.aux_copy_job.job_id}")
        if job_no == 2:
            self.log.info("Killing Auxcopy Job - [%s]", self.aux_copy_job.job_id)
            self.aux_copy_job.kill(True)
            if self.aux_copy_job.status.lower() == 'killed':
                self.log.info("Successfully killed the Aux Copy job")
            time.sleep(120)

    def suspend_resume_auxcopy(self):
        """
        suspend and resume the Auxcopy job
        """
        self.log.info("Suspending Auxcopy job")
        self.aux_copy_job.pause(wait_for_job_to_pause=True)
        self.log.info("SUspended Auxcopy job")
        self.log.info("Will Resume the suspended job after 1 minutes")
        time.sleep(60)
        self.log.info("Resume Auxcopy job")
        self.aux_copy_job.resume()
        self.log.info("Resumed Auxcopy job, will wait for 2 mins")
        time.sleep(120)

    def verify_auxcopy_job_successful_run(self):
        """
        Verify the successful completion of auxcopy job
        """
        self.log.info("Submitting another Auxcopy job")
        self.aux_copy_job = self.storage_policy.run_aux_copy(use_scale=True)
        self.log.info("Launched AuxCopy job - [%s]", self.aux_copy_job.job_id)
        if self.aux_copy_job.wait_for_completion():
            self.log.info('AuxCopy Job [%s] Completed successfully.', self.aux_copy_job.job_id)
        else:
            raise Exception('AuxCopy Job [%s[ Failed.' % self.aux_copy_job.job_id)

    def verify_subc_association_auxcopy(self):
        """
        Verify subclient to DDB association for secondary copy
        """
        errors_list = []
        self.log.info("Populating DDBs for Primary & Secondary Copy")
        self.validate_dedup_stores_for_copy(self.storage_policy_name, "Primary", 3)
        self.validate_dedup_stores_for_copy(self.storage_policy_name, self.copy_name, 3)

        self.log.info("Verifying that FS Subclient is assigned to FS store on Secondary Copy")
        if self.validate_subclient_ddb_mapping(self.storage_policy_name, self.copy_name,
                                               self.fs_subc_obj.subclient_name,
                                               self.copy_ddb_mapping_dict[f"{self.copy_name}_Files"],
                                               self.backupset_name, self.client.client_name):
            self.log.info("Successfully Verified that FS subclient is mapped to FS DDB [%s] on Secondary Copy",
                          self.copy_ddb_mapping_dict[f"{self.copy_name}_Files"])
        else:
            self.log.error("Verification for FS subclient DDB Mapping on Secondary copy failed")
            errors_list.append("FS Subclient DDB Mapping Verification Failed")

        self.log.info("Verifying that SQL Subclient is assigned to Databases store on Secondary Copy")
        if self.validate_subclient_ddb_mapping(self.storage_policy_name, self.copy_name, self.sql_subclient_name,
                                            self.copy_ddb_mapping_dict[f"{self.copy_name}_Databases"],
                                            self.sql_backupset_name, self.sqlclient.client_name):
            self.log.info("Successfully Verified that SQL subclient is mapped to Databases DDB [%s] on Secondary Copy",
                          self.copy_ddb_mapping_dict[f"{self.copy_name}_Databases"])
        else:
            self.log.error("Verification for SQL subclient DDB Mapping on Secondary copy failed")
            errors_list.append("SQL Subclient DDB Mapping Verification Failed")


        self.log.info("Verifying that HyperV Subclient is assigned to VSA store on Secondary Copy")
        if self.validate_subclient_ddb_mapping(self.storage_policy_name, self.copy_name, 
                                                self.vsa_subclient_name,
                                               self.copy_ddb_mapping_dict[f"{self.copy_name}_VMs"],
                                               self.vsa_backupset_name, self.vsaclient.client_name):
            self.log.info("Successfully Verified VSA subclient is mapped to VSA DDB [%s] on Secondary Copy",
                          self.copy_ddb_mapping_dict[f"{self.copy_name}_VMs"])
        else:
            self.log.info("Checking with Client Name = VM Name = [%s]", self.backup_vm_name)
            if self.validate_subclient_ddb_mapping(self.storage_policy_name, self.copy_name,
                                                   self.vsa_subclient_name,
                                                   self.copy_ddb_mapping_dict[f"{self.copy_name}_VMs"],
                                                   self.vsa_backupset_name, self.backup_vm_name):
                self.log.info("Successfully Verified VSA subclient is mapped to VSA DDB [%s] on Secondary Copy",
                              self.copy_ddb_mapping_dict[f"{self.copy_name}_VMs"])
            else:
                self.log.error("Verification for HyperV subclient DDB Mapping on Secondary copy failed with both "
                               "client name - [%s] and [%s]", self.vsaclient.client_name, self.backup_vm_name)
                errors_list.append("HyperV Subclient DDB Mapping Verification Failed")


        if not errors_list:
            self.log.info("All subclients have got correctly assigned to their respective DDB types")
        else:
            raise Exception(str(errors_list))

    def cleanup_resources(self):
        """
        Cleanup the commvault entities created by this test case
        """
        self.log.info("Cleaning up resources")
        try:
            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)

            self.log.info("Cleaning up FileSystem subclient")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            self.log.info("Cleaning up VSA subclient")
            self.log.info("Restting Storage Policy for VSA subclient %s", self.vsa_backupset_name)
            vsa_backupset_obj = self.vsaagent.backupsets.get("defaultBackupSet")
            sckeys = next(iter(vsa_backupset_obj.subclients.all_subclients))
            hyperv_subc_obj = vsa_backupset_obj.subclients.get(sckeys)
            for (policy_name, id) in self.commcell.storage_policies.all_storage_policies.items():
                if policy_name != self.storage_policy_name:
                    sp_obj = self.commcell.storage_policies.get(policy_name)
                    if int(sp_obj.storage_policy_properties["copy"][0]["dedupeFlags"].get("hostGlobalDedupStore",
                                                                                          0)) != 1:
                        self.log.info(
                            "Assigning HyperV subclient [%s] to following storage policy - %s",
                            hyperv_subc_obj.subclient_name, policy_name)
                        hyperv_subc_obj.storage_policy = policy_name
                        self.log.info("Sleeping for 1 minute before refreshing commcell")
                        time.sleep(60)
                        break
                    else:
                        self.log.info(f"Skipping Storage Policy {policy_name} as it is a glolbal dedup storage policy")

            self.log.info("Cleaning up SQL subclient")
            if self.sqlhelper.dbinit.check_database(self.dbname):
                if not self.sqlhelper.dbinit.drop_databases(self.dbname):
                    raise Exception("Unable to drop the database")
            self.log.info("Cleaned up SQL Database %s", self.dbname)

            if self.sqlinstance.subclients.has_subclient(self.sql_subclient_name):
                self.log.info("Deleting SQL subclient %s", self.sql_subclient_name)
                self.sqlinstance.subclients.delete(self.sql_subclient_name)

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.refresh()
                self.commcell.storage_policies.delete(self.storage_policy_name)

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("Deleting library %s", self.library_name)
                self.commcell.disk_libraries.delete(self.library_name)

            if self.commcell.disk_libraries.has_library(self.library_name_2):
                self.log.info("Deleting library %s", self.library_name_2)
                self.commcell.disk_libraries.delete(self.library_name_2)

        except Exception as ex:
            self.log.error("Storage Policy deletion failed during cleanup. Please check further - [%s]", str(ex))


    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup_resources()
            self.create_resources()
            self.add_secondary_copy()
            self.run_backups_on_subclient("fs", 2)
            self.run_backups_on_subclient("database", 2)
            self.run_backups_on_subclient("vsa", 1)
            self.run_aux_copy_with_induced_error()
            self.verify_auxcopy_job_failure(1)
            self.suspend_resume_auxcopy()
            self.verify_auxcopy_job_failure(2)
            self.verify_auxcopy_job_successful_run()
            self.verify_subc_association_auxcopy()


            self.log.info("Test case completed successfully.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
        try:
            self.cleanup_resources()
        except:
            self.log.error("Cleanup of resources failed. Please check further.")

    def create_sql_subclient(self):
        """
        Create a new Database and a SQL DB subclient to back up this content

        """
        self.log.info("Creating new Database")
        noofdbs = 1
        nooffilegroupsforeachdb = 3
        nooffilesforeachfilegroup = 3
        nooftablesforeachfilegroup = 5
        noofrowsforeachtable = 6

        # create databases on SOURCE INSTANCE
        self.log.info("Creating database [%s]", self.dbname)
        if not self.sqlhelper.dbinit.db_new_create(
                self.dbname,
                noofdbs,
                nooffilegroupsforeachdb,
                nooffilesforeachfilegroup,
                nooftablesforeachfilegroup,
                noofrowsforeachtable):
            raise Exception("Failed to create databases.")

        self.log.info("Adding SQL subclient %s", self.sql_subclient_name)

        # perform database check if exists, if so, drop it first. SOURCE INSTANCE
        try:
            self.sql_subclient_obj = self.sqlinstance.subclients.get(self.sql_subclient_name)
            self.log.info("Existing SQL subclient found, assigning storage policy.")
            self.sql_subclient_obj.storage_policy = self.storage_policy_name
        except:
            self.sql_subclient_obj = self.sqlinstance.subclients.add(
                self.sql_subclient_name, self.storage_policy_name, 'DATABASE')

        request_json = sqlconstants.SQL_SUBCLIENT_PROP_DICT
        self.dbname = self.dbname + "1"
        self.sql_subclient_obj.content = [self.dbname]
        self.sql_subclient_obj.log_backup_storage_policy = self.storage_policy_name
        subclient_prop = ["_mssql_subclient_prop", request_json]
        self.sql_subclient_obj.mssql_subclient_prop = subclient_prop

        request_json = sqlconstants.SQL_SUBCLIENT_STORAGE_DICT
        self.sql_subclient_obj.mssql_subclient_prop = [
            "_commonProperties['storageDevice']", request_json]

    def create_vsa_subclient(self):
        """
        Create a VSA subclient

        """

        # Configure backupset
        self.log.info("Fetching existing Default VSA Backupset...")
        vsa_backupset_obj = self.vsaagent.backupsets.get(self.vsa_backupset_name)
        self.log.info("Fetching VSA DefaultBackupset done.")

        #querying default subclient as custom subclient support is not present for VSA
        sckeys = next(iter(vsa_backupset_obj.subclients.all_subclients))

        self.hyperv_subc_obj = vsa_backupset_obj.subclients.get(sckeys)
        self.hyperv_subc_obj.storage_policy = self.storage_policy_name
        self.hyperv_subc_obj.content = [
            {
                'type': VSAObjects.VMName,
                'name': self.backup_vm_name,
                'display_name': self.backup_vm_name,
            }
        ]

    def create_fs_subclient(self):
        """
        Create a File System IDA subclient

        """
        self.backupset_obj = MMHelper.configure_backupset(self)
        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
        self.machineobj.create_directory(self.content_path)
        self.log.info("----------Content directory %s created----------", self.content_path)
        self.log.info("---Configuring subclient %s---", self.fs_subclient_name)
        self.fs_subc_obj = MMHelper.configure_subclient(self, subclient_name=self.fs_subclient_name)
        self.fs_subc_obj.data_readers = 1

        self.log.info("---Creating uncompressable unique data---")
        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
        self.machineobj.create_directory(self.content_path)
        self.mmhelper_obj.create_uncompressable_data(self.client.client_name, self.content_path, 2, 1)

    def validate_subclient_ddb_mapping(
            self,
            spname,
            copyname,
            subclient_name,
            expected_ddb,
            backupeset_name,
            client_name):
        """
        Validate whether a subclient has correctly got mapped to DDB in a given copy

        Args:
        spname (str)            -- Storage Policy Name
        copyname (str)          -- Copy name
        subclient_name (str)    -- subclient name
        expected_ddb (int)      -- Expected SIDB store id in subclient - ddb mapping
        backupset_name (str)    -- Backup set name
        client_name (str)       -- Client name

        Return: True if FS subclient is correctly associated to expected DDB id, False otherwise
        """
        query = """select sidbstoreid from archsubclientcopyddbmap where
        appid  = (select id from app_application where subclientname='%s' and
        clientid = ( select id from app_client where name = '%s') and
        backupset in ( select id from app_backupsetname where name = '%s')) and
        copyid = (select id from archgroupcopy where archGroupId =
        (select id from archgroup where name = '%s') and name = '%s')
        """ % (subclient_name, client_name, backupeset_name, spname, copyname)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        actual_ddbs_list = self.csdb.fetch_all_rows()
        self.log.info(actual_ddbs_list)
        if len(actual_ddbs_list) != 1:
            self.log.error(
                "Subclient DDB Association - Expected : 1 Actual : %s",
                len(actual_ddbs_list))
            return False
        actual_ddb = actual_ddbs_list[0][0]
        if actual_ddb == expected_ddb:
            self.log.info("Success : subclient name = %s storage policy = %s and copy = %s "
                          " Expected mapped ddb => %s Actual mapped ddb => %s",
                          subclient_name, spname, copyname, expected_ddb, actual_ddb)
            return True

        self.log.error("Failure : subclient name = %s storage policy = %s and copy = %s"
                       " Expected mapped ddb => %s Actual mapped ddb => %s",
                       subclient_name, spname, copyname, expected_ddb, actual_ddb)
        return False


    def validate_dedup_stores_for_copy(self, spname, copyname, expected_stores, check_details=True):
        """
        Validate whether 3 DDBs are created for given storage policy copy with correct
        apptypegroupid and populate a dictionary with copy id , ddb type and engine id
        information

        Args:
        spname (str)            -- Storage Policy Name
        copyname (str)          -- Copy name
        expected_stores (int)   -- How many stores are expected for a copy
        check_details (Boolean) -- Flag to tell if AppTypeGroupID for DDB is to be checked

        Return: True if expected stores with correct apptypegroupid get created for copy, False otherwise
        """

        result = True
        query = """select S.apptypegroupid,S.sidbstoreid,S.SIDBStoreName
        from idxsidbstore S, archcopysidbstore A where 
        (A.copyid = ( select id from archgroupcopy where archGroupId = 
        (select id from archgroup where name = '%s') and name = '%s')) and
        A.sidbstoreid = S.sidbstoreid""" % (spname, copyname)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        dedup_store_list = self.csdb.fetch_all_rows()
        self.log.info(dedup_store_list)
        # validation 1 : Check if we have 3 stores
        total_ddbs = len(dedup_store_list)
        if total_ddbs != expected_stores:
            self.log.error(
                "Copy to DDB Association -> Expected DDBs : %s Actual DDBs : %s", expected_stores,
                total_ddbs)
            raise Exception("Copy to DDB association verification failed - "
                            "Expected DDBs : %s Actual DDBs : %s" % (expected_stores, total_ddbs))

        self.log.info(
            "***Successfully validated that %s DDBs are associated to storage policy copy***", expected_stores)

        #for total DDBs = 1, we do not want to check apptypegroupid
        #if expected_stores != 3:
        #    self.log.info("Skipping apptypegroupid check as this is first check after SP creation.")
        #    return True

        # validation 2 : Check if apptypegroupid for each type of DDB is correct
        for groupid, engineid, storename in dedup_store_list:
            self.log.info(
                "AppTypeGroupID => %s EngineID => %s StoreName => %s",
                groupid,
                engineid,
                storename)
            # 1001 for Files DDB
            if storename.count('_Files_') == 1:
                if int(groupid) == 1001:
                    self.log.info("DDB with _Files_ has AppTypeGroupId = 1001 as expected")
                    self.copy_ddb_mapping_dict["%s_%s" % (copyname, 'Files')] = engineid
                else:
                    self.log.error(
                        "DDB with _Files_ doesn't have correct AppTypeGroupId. Expected : 1001 "
                        " Actual : %s", groupid)
                    result = False
            # 1002 for Databases DDB
            elif storename.count('_Databases_') == 1:
                if int(groupid) == 1002:
                    self.log.info("DDB with _Databases_ has AppTypeGroupId = 1002 as expected")
                    self.copy_ddb_mapping_dict["%s_%s" % (copyname, 'Databases')] = engineid
                else:
                    self.log.error(
                        "DDB with _Databases_ doesn't have correct AppTypeGroupId. Expected : 1002 "
                        " Actual : %s", groupid)
                    result = False

            # 1003 for VMs DDB
            elif storename.count('_VMs_') == 1:
                if int(groupid) == 1003:
                    self.log.info("DDB with _VMs_ has AppTypeGroupId = 1003 as expected")
                    self.copy_ddb_mapping_dict["%s_%s" % (copyname, 'VMs')] = engineid
                else:
                    self.log.error(
                        "DDB with _VMs_ doesn't have correct AppTypeGroupId. Expected : 1003 "
                        " Actual : %s", groupid)
                    result = False
        return result
