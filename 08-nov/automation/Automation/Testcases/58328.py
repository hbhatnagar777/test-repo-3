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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    simulate_mm_thread() -- Simulates MM Thread invocation by running stored proc
                            archUpdateStoreLimitFlagOnStoragePolicy

    get_all_ddbs_for_copy() -- Get all DDB engines associated to a storage policy copy

    get_num_subclient_associated_to_ddb()   --  Get number of subclients associated with a DDB

    is_ddb_full()   --  Check if DDB is marked FULL

    create_subclient_with_data() -- Create a subclient and run backup on the subclient

    update_archfilecopydedup()  --  Update ArchFileCopyDedup table for a give subclient_id with
                                    primary & secondary count provided

    STEPS:
    1. Create storage policy
    2. Create backup set and 30 subclients
    3. Create small amount of unique data for each subclient [ 50 MB ]
    4. Run backups on 30 subclients
    5. When backups are complete modify archfilecopydedup table such that
        a. subclient1 to subclient10 has 1 to 10  million primary and secondary reccords each
        b. subclient11 to subclient30 has 50 million records each
    6. verify subclient to ddb association in archsubclientcopyddbmap shows
        30 subclients against DDB
    7. Modify IdxSIDBUsageHistory to have a number > sum of all primary entries cooked in ste 5
    8. Run stored procedure archUpdateStoreLimitFlagOnStoragePolicy to mark DDB full
    9. Verify that new DDB has got created and it has 0 subclients
    10. Modify IdxSIDBStore table to change FullTime of FULL DDB to FullTime - 7 days
    11. Run stored procedure archUpdateStoreLimitFlagOnStoragePolicy again
    12. verify subclient to ddb association in archsubclientcopyddbmap now shows 27
    subclients against DDB
    13. verify that archsubclientcopyddbmaphistory table in HistoryDB shows 3 new rows
    for this FULL DDB
    14. Run backups on these 3 subclients
    15. Again verify that 3 subclients show ddb association in archsubclientcopyddbmap with new DDB
    16. Also verify that old DDB has 27 subclients intact in archsubclientcopyddbmap table
    17. Check sidbstoreid against volumes created by these 3 subclients is new DDBs sidbstoreid
    18. Clean up the test case.

    Input Example : 
    "58328": {
                "MediaAgentName": "ma name",
		"AgentName" : "File System",
		"ClientName": "client name"

	    }
"""
from AutomationUtils.database_helper import MSSQL
from AutomationUtils import constants, cvhelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "AutoBalance_Full_DDBs"
        self.tcinputs = {
            "MediaAgentName": None
        }

        # Local variables
        self.clientname = None
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
        self.result_string = ""
        self.mountpath = ""
        self.subclients_list = []
        self.copy_name = 'Primary'
        self.dedupe_helper_obj = None
        self.mmhelper_obj = None
        self.ma_library_drive = None
        self.dbhandle = None
        self.subclient_name = None

    def setup(self):
        """Setup function of this test case"""


        optionobj = OptionsSelector(self.commcell)
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.machineobj = Machine(self.client)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)

        self.client_system_drive = optionobj.get_drive(self.machineobj)
        self.ma_library_drive = optionobj.get_drive(self.ma_machineobj)

        timestamp_suffix = OptionsSelector.get_custom_str()
        self.dedup_path = self.ma_machineobj.join_path(self.ma_library_drive,
                                                    "DDBs\\%s%s"%(self.id, timestamp_suffix))
        self.mountpath = self.ma_machineobj.join_path(self.ma_library_drive,
                                                      self.id)

        cs_machine_obj = Machine(self.commcell.commserv_client)
        encrypted_pass = cs_machine_obj.get_registry_value("Database", "pAccess")
        sql_password = cvhelper.format_string(
            self._commcell, encrypted_pass).split("_cv")[1]

        db_server = ""
        if Machine(self.commcell.commserv_name, self.commcell).os_info.lower() != 'unix':
            db_server = self.commcell.commserv_name + r'\commvault'
        else:
            db_server = self.commcell.commserv_name
        self.dbhandle = MSSQL(db_server,
                              "sqladmin_cv", sql_password,
                              "commserv", as_dict=False)

        self.storage_policy_name = "%s_%s" % ("tc_%s_sp"%self.id, timestamp_suffix)
        self.library_name = "lib_%s" % (self.name)
        self.backupset_name = "bkpset_tc_%s_%s" % (self.id, timestamp_suffix)
        self.content_path = self.machineobj.join_path(self.client_system_drive, "content_%s"%self.id)
        self.subclient_name = "autobalance_sc"
        self.dedupe_helper_obj = DedupeHelper(self)
        self.mmhelper_obj = MMHelper(self)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Configuring the Disk Library")
            self.mmhelper_obj.configure_disk_library(self.library_name, self.mediaagentname, self.mountpath)

            # Delete Storage Policy if exists
            self.log.info("Configuring the Storage Policy")
            self.dedupe_helper_obj.configure_dedupe_storage_policy(self.storage_policy_name,
                                                                   self.library_name,
                                                                   self.mediaagentname, self.dedup_path)
            # Delete Backupset if exists

            self.log.info("Configuring the Backupset")
            self.mmhelper_obj.configure_backupset(self.backupset_name)

            # Create 30 subclients
            for num in range(0, 30):
                self.subclients_list.append(self.create_subclient_with_data(num))

            # Run backup for all subclients
            backup_jobs = []
            self.log.info("Launching backup jobs for each of the subclients")
            for num in range(0, 30):
                backup_jobs.append(self.subclients_list[num].backup("Full"))

            # wait for backup job completion on all subclients
            for num in range(0, 30):
                if not backup_jobs[num].wait_for_completion():
                    raise Exception("Backup job %s did not complete in given timeout" % backup_jobs[num].job_id)
                self.log.info("Successfully completed a backup job on subclient with jobid - %s",
                              backup_jobs[num].job_id)

            # Check ArchSubclientCopyDDBMap for 30 entries
            copy_id = self.mmhelper_obj.get_copy_id(self.storage_policy_name, self.copy_name)
            engine_id = int(self.get_all_ddbs_for_copy(copy_id, 1001, True)[0][0])

            orig_assoc_subcs = self.get_num_subclient_associated_to_ddb(engine_id)
            self.log.info("Number of subclients associated to DDB : %s = %s", engine_id, orig_assoc_subcs)

            # Update ArchFileCopyDedup
            # For first 10 subclients, update 1 to 10 million as primary & secondary count
            self.log.info("Updating ArchFileCopyDedup to load primary IDs for SIDB Store")
            for num in range(1, 11):
                update_value = num * 1000000
                self.log.info("Setting PrimaryObjects & SecondaryObjects for subclient %s%s",
                              self.subclient_name, num - 1)
                self.update_archfilecopydedup(self.subclients_list[num - 1].subclient_id,
                                              engine_id, update_value, update_value)

            # For remaining 20 subclients, update 50 million as primary & secondary count
            for num in range(10, 30):
                self.log.info("Setting PrimaryObjects & SecondaryObjects for subclient %s%s",
                              self.subclient_name, num)
                self.update_archfilecopydedup(self.subclients_list[num].subclient_id,
                                              engine_id, 50000000, 50000000)

            # Update IdxSIDBUsageHistory
            self.log.info("Setting primary entry count for sidbstore to 1200 million plus")
            query = "update idxsidbusagehistory set PrimaryEntries = 1200000000 " \
                    "where sidbstoreid = %s" % engine_id
            self.log.info("QUERY: %s", query)
            self.dbhandle.execute(query)

            # Execute the stored procedure to mark DDB Full
            self.simulate_mm_thread()

            # Make sure that DDB has got marked FULL
            if self.is_ddb_full(engine_id):
                self.log.info("===Successfully verified that old DDB engine id %s is marked FULL===", engine_id)
            else:
                self.log.error("===DDB %s is not marked as FULL, failing the testcase===", engine_id)
                Exception("DDB %s is not marked as FULL, failing the testcase" % engine_id)

            # Get new Active Engine Id
            new_engine_id = int(self.get_all_ddbs_for_copy(copy_id, 1001, True)[0][0])
            self.log.info("New DDB Engine ID created by Horizontal Scaling of DDBs => %s", new_engine_id)

            # Make sure that there are no DDB
            if self.get_num_subclient_associated_to_ddb(new_engine_id) != 0:
                self.log.error("===New DDB %s shows subclient association which is not exepected. "
                               "Please check if SIDB Store ID is correct.===", new_engine_id)

            # Modify Full DDB FullTime
            self.log.info("Updating FullTime for DDB to current FullTime - 7 days")
            query = "update idxsidbstore set FullTime = FullTime - (86400*7) where sidbstoreid = %s" % engine_id
            self.log.info("QUERY: %s", query)
            self.dbhandle.execute(query)

            # Invoke MM Thread again
            self.simulate_mm_thread()

            # Now check how many entries are present in archsubclientcopyddbmap
            num_subcs_full_ddb = self.get_num_subclient_associated_to_ddb(engine_id)
            self.log.info("Validation 1 : Number of subclients against FULL DDB should go down by 10%")
            if num_subcs_full_ddb < 30:
                self.log.info("=== %s rows deleted from ArchSubclientCopyDDBMap table for SIDBStoreID %s ===",
                              30 - num_subcs_full_ddb, engine_id)
            else:
                self.log.error("=== No rows deleted from ArchSubclientCOpyDDBMap table for SIDBStoreID %s ===",
                               engine_id)
                self.status = constants.FAILED

            self.log.info("Validation 2 : Number of subclients in ArchSubclientCopyDDBMapHistory should be 3")

            query = "select * from HistoryDB.dbo.ArchSubclientCopyDDBMapHistory where sidbstoreid=%s" % engine_id
            self.log.info(query)
            self.csdb.execute(query)
            deleted_subclients = self.csdb.fetch_all_rows()
            self.log.info(deleted_subclients)
            self.log.info("Number of deleted subclients recorded in ArchSubclientCopyDDBMapHistory = %s",
                          len(deleted_subclients))
            self.log.info("Deleted Subclients List ===> %s", str(deleted_subclients))
            if len(deleted_subclients) == 3:
                self.log.info("=== Successfully verified that 10% of subclients have got deleted from "
                              "ArchSubclientCopyDDBMap and HistoryDB has recorded the same ===")
            else:
                self.log.error("=== Failed to verify that 10% of subclients have got deleted from "
                               "ArchSubclientCopyDDBMap and HistoryDB has recorded the same ===")
                self.status = False

            #Start backup on the subclients which were moved from FULL DDB
            deleted_subclient_ids = [int(subc[0]) for subc in deleted_subclients]
            for subc in self.subclients_list:
                if int(subc.subclient_id) in deleted_subclient_ids:
                    self.log.info("Start a full backup job on subclient - %s  id - %s",
                                  subc.subclient_name, subc.subclient_id)
                    full_bkp = subc.backup("Full")
                    if not full_bkp.wait_for_completion():
                        raise Exception("Backup job %s did not complete in given timeout" % full_bkp.job_id)
                    self.log.info("Successfully completed a backup job on subclient with jobid - %s",
                                  full_bkp.job_id)

            #Now check number of subclinets associated with new DDB - It should be 3
            num_subc_new_ddb = self.get_num_subclient_associated_to_ddb(new_engine_id)
            self.log.info("Validation => Check if new jobs on deleted subclients backup using new DDB store")
            if num_subc_new_ddb == len(deleted_subclients):
                self.log.info("===Successfully verified that deleted subclients are correctly associated "
                              "to new DDB===")
            else:
                self.log.error("Deleted subclients are not associated to new DDB")
                self.status = False

            #Validate if deleted subclients are part of ArchSubclientCopyDDBMap with new store
            query = "Select * from archsubclientcopyddbmap where appid in (%s)"%','.join(
                [str(x) for x in deleted_subclient_ids])
            self.log.info("QUERY: %s", query)
            self.csdb.execute(query)
            new_association_rows = self.csdb.fetch_all_rows()
            self.log.info(new_association_rows)
            if len(new_association_rows) != len(deleted_subclient_ids):
                self.log.error("===Same subclient has more than 1 DDBs associated which is not expected===")
                self.log.error("%s", str(new_association_rows))
                self.status = constants.FAILED

            for association in new_association_rows:
                if int(association[-1]) == new_engine_id:
                    self.log.info("===Successfully verified that deleted subclient ID %s used DDB store %s "
                                  "for backup===",
                                  association[0], association[-1])
                    self.log.info("%s", str(association))
                else:
                    self.log.error("===ERROR : Failed to verify that deleted subclient ID %s used DDB store %s for "
                                   "backup. Expected DDB store %s : Actual DDB store %s===",
                                   association[0], new_engine_id, new_engine_id, association[-1])
                    self.status = constants.FAILED

            if not self.status:
                raise Exception("Test case Execution failed as at least one verification step failed. "
                                "Please check logs for more details.")
            self.log.info("Testcase execution completed successfully.")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        try:
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy  %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)
                if self.machineobj.check_directory_exists(self.dedup_path):
                    self.log.info("Deleting DDB path - %s", self.dedup_path)
                    self.machineobj.remove_directory(self.dedup_path)

            try:
                self.log.info("Deleting library %s", self.library_name)
                self.commcell.disk_libraries.delete(self.library_name)
                if self.machineobj.check_directory_exists(self.content_path):
                    self.machineobj.remove_directory(self.content_path)
                if self.machineobj.check_directory_exists(self.mountpath):
                    self.log.info("Deleting library path - %s", self.mountpath)
                    self.machineobj.remove_directory(self.mountpath)
            except Exception as ex:
                self.log.error("Library Deletion during cleanup Failed with error %s", str(ex))
        except Exception as ex:
            self.log.warning(f"Failure in test environment cleanup - {ex}")

    def simulate_mm_thread(self):
        """
        Simulates MM Thread invocation by running stored proc archUpdateStoreLimitFlagOnStoragePolicy
        """
        self.log.info("Executing stored proc to simulate MM thread invocations & sleeping for 30 seconds")
        query = "exec CommServ.dbo.archUpdateStoreLimitFlagOnStoragePolicy"
        self.log.info("QUERY: %s", query)
        self.dbhandle.execute_stored_procedure(query, None)

    def get_num_subclient_associated_to_ddb(self, engine_id):
        """
        Get number of subclients associated with a DDB
        Args:
        engine_id (int) -- DDB Engine ID

        Return: Number of subclients associated with DDB
        """
        query = "select count(*) from archsubclientcopyddbmap where sidbstoreid = %s" % (engine_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        mapping = int(self.csdb.fetch_one_row()[0])
        self.log.info(mapping)
        return mapping

    def get_all_ddbs_for_copy(self, copy_id, apptypegroupid=0, only_active=False):
        """
        Get all DDB engines associated to a storage policy copy
        Args:
        copy_id (int) -- Storage policy copy id
        apptypegroupid (int) -- AppTypeGroupID ( FS=1001 DB=1002 VSA=1003).
        only_active (bool)  -- True for returning only active DDBs, by default set to False

        Return:
        List of all the DDBs associated with given copy based on whether user wants only active DDBs or all DDBs
        """

        if only_active:
            self.log.info("filtering out the FULL DDBs associated with copy")
            query = "select sidbstoreid from idxsidbstore where sidbstoreid in " \
                "(select sidbstoreid from archcopysidbstore where copyid=%s and flags  & 1 <> 1)" \
                " and apptypegroupid=%s" % (copy_id, apptypegroupid)
        else:
            self.log.info("fetching all the DDBs associated with copy")
            query = "select sidbstoreid from idxsidbstore where sidbstoreid in " \
                    "(select sidbstoreid from archcopysidbstore where copyid=%s)" \
                    " and apptypegroupid=%s" % (copy_id, apptypegroupid)

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info(rows)
        return rows

    def is_ddb_full(self, engineid):
        """
        Check if DDB is marked FULL
        Args:
        engineid (int) -- SIDB Store ID

        Return:
        True if DDB is FULL, false otherwise.
        """
        query = "select flags&1 from archcopysidbstore where sidbstoreid=%s" % engineid
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        flags = int(self.csdb.fetch_one_row()[0])
        self.log.info(flags)
        # When DDB is FULL, flag 1 is set on store. So a FULL DDB will always have ODD number as flag.
        if flags:
            return True

        return False

    def create_subclient_with_data(self, subclient_number):
        """
        Create a subclient and run backup on the subclient
        Args:
        subclient_number (int) -- subclient name suffix

        Return:
        Returns subclient object
        """
        current_content_dir = self.machineobj.join_path(self.content_path, str(subclient_number))
        if self.machineobj.check_directory_exists(current_content_dir):
            self.machineobj.remove_directory(current_content_dir)
        self.machineobj.create_directory(current_content_dir)
        self.log.info("----------Content directory %s created----------", current_content_dir)
        self.log.info("---Configuring subclient %s%s---", self.subclient_name, subclient_number)
        subclient_obj = MMHelper.configure_subclient(
            self, subclient_name="%s%s" %
            (self.subclient_name, subclient_number), content_path=current_content_dir)
        subclient_obj.data_readers = 1
        self.mmhelper_obj.create_uncompressable_data(self.client.client_name, current_content_dir, 0.1, 0)
        self.log.info("---Successfully configured subclient %s%s", self.subclient_name, subclient_number)
        return subclient_obj

    def update_archfilecopydedup(self, subclient_id, engine_id, primary_count, secondary_count):
        """
        Update ArchFileCopyDedup table for a give subclient_id with primary & secondary count provided
        Args:
        subclient_id (int) -- subclient id
        engine_id (int) -- SIDBEngine ID
        primary_count (int) -- primary count to set in PrimaryObjects column
        secondary_count (int) -- secondary count to set in SecondaryObjects column

        Return :
        True if update succeeds, False otherwise
        """

        self.log.info("Fetching ArchFileId for given subclient")
        query = "select id from archfile where id in (" \
                "select archfileid from archchunkmapping where jobid = (" \
                "select top 1 jobid from jmbkpstats where appid = %s order by servstartdate desc) " \
                "and filetype=1)" % subclient_id
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        archfile_id = int(self.csdb.fetch_one_row()[0])
        self.log.info("Modifying PrimaryObjects & SecondaryObjects for following Sublient - AF Pair: %s-%s",
                      subclient_id, archfile_id)

        query = "update ArchFileCopyDedup set PrimaryObjects = %s, SecondaryObjects = %s " \
                "where archfileid = %s and sidbstoreid=%s" % (primary_count, secondary_count,
                                                              archfile_id, engine_id)
        self.log.info("QUERY: %s", query)
        self.dbhandle.execute(query)
        return True
