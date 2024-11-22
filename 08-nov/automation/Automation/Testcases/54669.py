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


"""
import time
from AutomationUtils.database_helper import MSSQL
from AutomationUtils import constants
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
        self.name = "DDB_Full_Scenarios"
        self.tcinputs = {
            "MediaAgentName": None,
            "sqlpassword": None,
            "sqluser": None,
            "MountPath" : None
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
        self.result_string = ""
        self.storage_policy_list = []
        self.copy_name = 'Primary'
        self.MM_THREAD_SLEEP_TIME = 480
        self.dbhandle = None
        self.db_server = ""

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.machineobj = Machine(self.client)
        self.client_system_drive = optionobj.get_drive(self.machineobj)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)

        timestamp_suffix = OptionsSelector.get_custom_str()
        self.dedup_path = self.machineobj.join_path(self.client_system_drive,
                                                    "DDBs\\tc_54669_{0}".format(timestamp_suffix))
        self.storage_policy_name = "%s_%s" % ("tc_54669_sp", timestamp_suffix)
        self.library_name = "lib_%s_%s" % (self.name, timestamp_suffix)
        self.backupset_name = "bkpset_tc_54669_%s" % timestamp_suffix
        self.content_path = self.machineobj.join_path(self.client_system_drive, "content_104014")
        self.backupset = "defaultBackupSet"
        self.subclient = "default"

        if Machine(self.commcell.commserv_name, self.commcell).os_info.lower() != 'unix':
            self.db_server = self.commcell.commserv_name + r'\commvault'
        else:
            self.db_server = self.commcell.commserv_name
        self.dbhandle =  MSSQL(self.db_server,
                               self.tcinputs['sqluser'],
                               self.tcinputs['sqlpassword'],
                               "commserv", as_dict=False)

    def run(self):
        """Run function of this test case"""
        try:

            # Local Variable initialization
            dedup_obj = DedupeHelper(self)
            mmhelper_obj = MMHelper(self)
            sqluser = self.tcinputs['sqluser']
            sqlpassword = self.tcinputs['sqlpassword']
            mountpath = self.tcinputs['MountPath']
            subclient_name_prefix = "subclient_tc_104014"
            storage_policy_prefix = self.storage_policy_name
            status = True
            result_string = ""
            sqlobj = MSSQL(self.db_server, sqluser, sqlpassword, "commserv")
            self.log.info("----------Configuring TC environment-----------")
            self.log.info("---Create new Library---")
            # Create new library
            mmhelper_obj.configure_disk_library(self.library_name, self.mediaagentname, mountpath)
            # STEP : Set MM Interval thread to 5 mins
            self.log.info("----------Setting MM Maintenance Check Interval to 5 mins-----------")
            query = "update MMConfigs set nmin=5, value=5 where name = 'MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES'"
            self.log.info("QUERY: %s", query)
            sqlobj.execute(query)


            # Configure backup set and subclients
            self.log.info("---Configuring backup set---")
            self.backupset_obj = MMHelper.configure_backupset(self)

            self.storage_policy_name = "%s_%s" % (storage_policy_prefix, "_qi_time_threshold")
            if self.test_qi_time_threshold(mmhelper_obj, dedup_obj, sqlobj, subclient_name_prefix):
                self.log.info("======Horizontal Scaling of DDBs - QI TIME THRESHOLD ==> PASS")
                result_string = "QI TIME THRESHOLD ==> PASS"
            else:
                self.log.info("======Horizontal Scaling of DDBs - QI TIME THRESHOLD ==> FAIL")
                status = False
                result_string = "QI TIME THRESHOLD ==> FAIL"

            self.storage_policy_name = "%s_%s" % (storage_policy_prefix, "_free_space_threshold")
            if self.test_free_space_threshold(mmhelper_obj, sqlobj, subclient_name_prefix):
                self.log.info("======Horizontal Scaling of DDBs - FREE DISKSPACE THRESHOLD ==> PASS")
                result_string = "%s\n%s" % (result_string, "DISK SPACE THRESHOLD ==> PASS")
            else:
                self.log.info("======Horizontal Scaling of DDBs - FREE DISKSPACE THRESHOLD ==> FAIL")
                status = False
                result_string = "%s\n%s" % (result_string, "DISK SPACE THRESHOLD ==> FAIL")

            self.log.info("---Configuring Dedup Storage Policy---")
            self.storage_policy_name = "%s_%s" % (storage_policy_prefix, "_subclient_primarycount_threshold")
            self.dedup_path = "%s_%s" % (self.dedup_path, "_subclient_primarycount_threshold")
            self.log.info("Creating new storage policy - %s", self.storage_policy_name)
            self.commcell.storage_policies.add(
                self.storage_policy_name, self.library_name, self.mediaagentname, self.dedup_path)
            self.log.info("---Successfully configured storage policy - %s", self.storage_policy_name)
            self.storage_policy_list.append(self.storage_policy_name)

            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)
            self.machineobj.create_directory(self.content_path)


            if self.test_subclient_threshold(mmhelper_obj, sqlobj, subclient_name_prefix):
                self.log.info("======Horizontal Scaling of DDBs - Subclient Number Threshold ==> PASS")
                result_string = "%s\n%s" % (result_string, "SUBCLIENT NUMBER THRESHOLD ==> PASS")

            else:
                self.log.info("======Horizontal Scaling of DDBs - Subclient Number Threshold ==> FAIL")
                status = False
                result_string = "%s\n%s" % (result_string, "SUBCLIENT NUMBER THRESHOLD ==> FAIL")

            if self.test_primary_threshold(mmhelper_obj, sqlobj, subclient_name_prefix):
                self.log.info("======Horizontal Scaling of DDBs - Primary Count Threshold ==> PASS")
                result_string = "%s\n%s" % (result_string, "PRIMARY COUNT THRESHOLD ==> PASS")
            else:
                self.log.info("======Horizontal Scaling of DDBs - Primary Count Threshold ==> FAIL")
                status = False
                result_string = "%s\n%s" % (result_string, "PRIMARY COUNT THRESHOLD ==> FAIL")

            self.log.info("------------Disabling the subclient threshold--------------")
            query = "update MMConfigs set value=0 where name = 'MMCONFIG_INFINI_STORE_NUMBER_OF_SUBCLIENTS'"
            self.log.info("QUERY: %s", query)
            sqlobj.execute(query)


            if not status:
                self.log.error("DDB Full Scenario test case failed.")
                raise Exception("One or more DDB Full Scenarios failed verification.")

            self.log.info("DDB Full Senario test case completed successfully.")
            self.log.info("\n********************************\n%s\n********************************\n", result_string)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.log.error("\n********************************\n%s\n********************************\n", result_string)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")
        self.log.info("cleaning up the test environment ...")

        try:
            self.log.info("----------Setting number of subclients threshold back to 0------------")
            mmhelper_obj_new = MMHelper(self)

            query = "update MMConfigs set value=0 where name = 'MMCONFIG_INFINI_STORE_NUMBER_OF_SUBCLIENTS'"
            self.log.info("QUERY: %s", query)
            mmhelper_obj_new.execute_update_query(query, self.tcinputs['sqlpassword'], self.tcinputs['sqluser'])

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            for policy in self.storage_policy_list:
                if self.commcell.storage_policies.has_policy(policy):
                    self.log.info("Deleting storage policy  %s", policy)
                    self.commcell.storage_policies.delete(policy)

            self.log.info("Deleting library %s", self.library_name)
            self.commcell.disk_libraries.delete(self.library_name)
            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)
        except Exception as ex:
            self.log.warning(f"Failed to clean up test environment - {ex}")

    def test_primary_threshold(self, mmhelper_obj, sqlobj, subclient_name_prefix):
        """
        Test Primary count threshold for DDB full scenario
        Args:
        mmhelper_obj (obj) -- mmhelper object
        sqlobj (obj)    -- SQL connection object

        Return:
        True if test succeeds, False otherwise
        """
        current_content_dir = self.machineobj.join_path(self.content_path, 'primary')
        if self.machineobj.check_directory_exists(current_content_dir):
            self.machineobj.remove_directory(current_content_dir)
        self.machineobj.create_directory(current_content_dir)
        self.log.info("----------Content directory %s created----------", current_content_dir)
        self.log.info("---Configuring subclient %s_primary---", subclient_name_prefix)
        subclient_obj = MMHelper.configure_subclient(self, subclient_name="%s%s" % (subclient_name_prefix, 'primary'),
                                                     content_path=current_content_dir)
        subclient_obj.data_readers = 1
        self.log.info("---Creating uncompressable unique data---")
        mmhelper_obj.create_uncompressable_data(self.client.client_name, current_content_dir, 0.1, 0)
        self.run_backup_job(subclient_obj)

        status = True
        self.log.info("===================PRIMARY COUNT THRESHOLD=================")
        copy_id = mmhelper_obj.get_copy_id(str(self.storage_policy_name), str(self.copy_name))
        current_ddbs = self.get_all_ddbs_for_copy(copy_id, 1001)
        self.log.info(
            "Before starting the primary threshold test, number of SIDBs associated with this storage policy "
            " --> %s",
            len(current_ddbs))
        engine_id = current_ddbs[-1][0]

        self.log.info("Sleeping 60 seconds for IdxSIDBUsageHistory update to happen")
        time.sleep(60)

        # STEP : Modify the idxsidbusagehistory table to make primarycount for last job as 800 millions
        self.log.info("Setting primary entry count for sidbstore to 800 million plus")
        query = "update idxsidbusagehistory set PrimaryEntries = 800000000 where sidbstoreid = %s" % engine_id
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        # Sleep for 5 minutes so that couple of MM threads complete exeuction
        self.log.info("Executing stored proc to simulate MM thread invocations & sleeping for 60 seconds")
        query = "exec CommServ.dbo.archUpdateStoreLimitFlagOnStoragePolicy"
        self.log.info("QUERY: %s", query)
        self.dbhandle.execute_stored_procedure(query, None)

        time.sleep(60)

        # Now check if a new DDB has got created
        after_test_ddbs = self.get_all_ddbs_for_copy(copy_id, 1001)
        # As we are using same storage policy used by Subclient threshold , we expect it to have 3 DDBs now
        if len(after_test_ddbs) == len(current_ddbs) + 1:
            self.log.info("New DDB got created for Storage Policy copy as expected")
            third_ddb = int(after_test_ddbs[-1][0])
            if not self.is_ddb_full(third_ddb):
                self.log.info("Successfully verified that new DDB engine id %s is not FULL", third_ddb)
                # Set status to True/False based on whether DDB full reason turned out to be 4 as expected
                status = self.validate_ddb_full_reason(engine_id, 4)
            else:
                self.log.error("New DDB engine id %s is marked as FULL instead of ACTIVE", third_ddb)
                status = False
        else:
            self.log.error("There are still only 2 DDBs of type FS associated with this storage policy copy")
            status = False

        self.log.info("Cleaning up storage policy.")
        self.backupset_obj.refresh()
        self.agent.backupsets.delete(self.backupset_name)
        self.commcell.storage_policies.delete(self.storage_policy_name)

        return status

    def test_subclient_threshold(self, mmhelper_obj, sqlobj, subclient_name_prefix):
        """
        Test number of subclient threshold for DDB full scenario
        Args:
        mmhelper_obj (obj) -- mmhelper object
        sqlobj (obj)    -- SQL connection object
        subclient_name_prefix (str) -- subclient name prefix for subclient creation

        Return:
        True if test succeeds, False otherwise
        """
        self.log.info("===================SUBCLIENT THRESHOLD=================")
        status = True
        self.log.info("----------Setting number of subclients threshold to 4-----------")
        query = "update MMConfigs set value=4 where name = 'MMCONFIG_INFINI_STORE_NUMBER_OF_SUBCLIENTS'"
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)


        self.log.info("===================SUBCLIENT THRESHOLD=================")
        # STEP : Create 3 subclients and wait for MM thread to kick off after 2 mins

        for i in range(1, 6):
            current_content_dir = self.machineobj.join_path(self.content_path, str(i))
            if self.machineobj.check_directory_exists(current_content_dir):
                self.machineobj.remove_directory(current_content_dir)
            self.machineobj.create_directory(current_content_dir)
            self.log.info("----------Content directory %s created----------", current_content_dir)
            self.log.info("---Configuring subclient %s---", i)
            subclient_obj = MMHelper.configure_subclient(self, subclient_name="%s%s" % (subclient_name_prefix, i),
                                                         content_path=current_content_dir)
            subclient_obj.data_readers = 1
            self.log.info("---Creating uncompressable unique data---")
            mmhelper_obj.create_uncompressable_data(self.client.client_name, current_content_dir, 0.1, 0)
            self.run_backup_job(subclient_obj)
            if i == 1:
                copy_id = mmhelper_obj.get_copy_id(str(self.storage_policy_name), str(self.copy_name))
                engine_id = self.get_all_ddbs_for_copy(copy_id, 1001)[0][0]

            # STEP : Check subclient to DDB association and that it is getting associated to correct DDB
            assoc_engine_id = self.get_subclient_ddb_association(subclient_obj.subclient_id, copy_id)
            if i <= 4:
                if engine_id != assoc_engine_id:
                    self.log.error(
                        "Subclient associated with wrong DDB. Expected-> %s Actual-> %s",
                        engine_id, assoc_engine_id)
                    status = False
                else:
                    self.log.info("Subclient %s associated to correct DDB %s",
                                  subclient_obj.subclient_name, engine_id)
            else:
                current_ddbs = self.get_all_ddbs_for_copy(copy_id, 1001)
                if len(current_ddbs) == 1:
                    self.log.error("There is still only 1 DDB of type FS associated with this storage policy copy")
                    status = False
                else:
                    self.log.info("This storage policy copy now has %s DDBs of type FS "
                                  "associated with it", len(current_ddbs))

                if self.is_ddb_full(engine_id):
                    self.log.info("Successfully verified that old DDB engine id %s is marked FULL", engine_id)
                    if not self.validate_ddb_full_reason(engine_id, 8):
                        status = False
                else:
                    self.log.error("Old DDB engine id %s is not marked as FULL", engine_id)
                    status = False

                if not self.is_ddb_full(assoc_engine_id):
                    self.log.info(
                        "Successfully verified that new DDB engine id %s is not marked FULL", assoc_engine_id)
                else:
                    self.log.error("New DDB engine id %s is marked as FULL instead of ACTIVE", assoc_engine_id)
                    status = False

        return status

    def test_free_space_threshold(self, mmhelper_obj, sqlobj, subclient_name_prefix):
        """
        Test Disk Free Space threshold for DDB full scenario
        Args:
        mmhelper_obj (obj) -- mmhelper object
        sqlobj (obj)    -- SQL connection object
        subclient_name_prefix (str) -- subclient name prefix for subclient creation

        Return:
        True if test succeeds, False otherwise
        """
        self.log.info("===================FREE SPACE THRESHOLD=================")
        return_flag = True
        self.log.info("---Configuring new Dedup Storage Policy for free space threshold verification---")
        self.log.info("Creating new storage policy - %s", self.storage_policy_name)
        self.dedup_path = "%s_%s" % (self.dedup_path, "_free_space_threshold")
        self.commcell.storage_policies.add(
            self.storage_policy_name, self.library_name, self.mediaagentname, self.dedup_path)
        self.log.info("---Successfully configured storage policy - %s", self.storage_policy_name)
        self.storage_policy_list.append(self.storage_policy_name)

        self.log.info("---Setting free disk space threshold to 50%---")
        query = "update MMConfigs set value=50 where name = 'MMCONFIG_INFINI_STORE_FREE_SPACE_PERC'"
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        self.log.info("Create a new subclient and run a backup")
        subclient_obj = self.create_subclient_run_backup(7, subclient_name_prefix, mmhelper_obj)

        copy_id = mmhelper_obj.get_copy_id(str(self.storage_policy_name), str(self.copy_name))
        engine_id = self.get_all_ddbs_for_copy(copy_id, 1001)[0][0]
        self.log.info("DDB Engine ID created at the time of copy creation - %s", engine_id)

        self.log.info("Sleeping 60 seconds for IdxSIDBUsageHistory update to happen")
        time.sleep(60)
        # Set SIDB substore's idxcache values to breach the free space threshold
        query = "update idxcache set totalcapacitymb=20480, FreeDiskSpaceMB=8192 where IdxCacheId= " \
                "(select idxcacheid from idxsidbsubstore where sidbstoreid=%s)" % engine_id
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        self.log.info("Setting primary entry count for sidbstore to 200 million plus")
        query = "update idxsidbusagehistory set PrimaryEntries = 200000000 where sidbstoreid = %s" % engine_id
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        self.log.info("Executing stored proc to simulate MM thread invocations & sleeping for 60 seconds")
        query = "exec CommServ.dbo.archUpdateStoreLimitFlagOnStoragePolicy"
        self.log.info("QUERY: %s", query)
        self.dbhandle.execute_stored_procedure(query, None)
        time.sleep(60)

        # Now check if a new DDB has got created
        current_ddbs = self.get_all_ddbs_for_copy(copy_id, 1001)
        if len(current_ddbs) == 2:
            self.log.info("Second DDB got created for Storage Policy copy as expected")
            # Now check if 2nd DDB got marked as FULL
            if self.is_ddb_full(engine_id):
                self.log.info("Successfully verified that old DDB engine id %s is marked FULL", engine_id)
                # Check DDB FULL Reason
                if not self.validate_ddb_full_reason(engine_id, 2):
                    return_flag = False
            else:
                self.log.error("Old DDB engine id %s is not marked as FULL", engine_id)
                return_flag = False

            new_engine_id = current_ddbs[1][0]
            if not self.is_ddb_full(new_engine_id):
                self.log.info("Successfully verified that new DDB engine id %s is not FULL", new_engine_id)
            else:
                self.log.error("New DDB engine id %s is marked as FULL instead of ACTIVE", new_engine_id)
                return_flag = False
        else:
            self.log.error("There is still only 1 DDB of type FS associated with this storage policy copy")
            return_flag = False

        #If test has succeeded, we can clean up the SP. This will reduce number of partition on node
        #Remember - Number of partitions > 30 on an MA will stop creating new DDBs even when FULL conditions are met
        self.log.info("Cleaning up storage policy.")
        self.backupset_obj.refresh()
        self.backupset_obj.subclients.delete(subclient_obj.subclient_name)
        self.commcell.storage_policies.delete(self.storage_policy_name)
        return return_flag

    def test_qi_time_threshold(self, mmhelper_obj, dedup_obj, sqlobj, subclient_name_prefix):
        """
        Test QI time threshold for DDB full scenario
        Args:
        mmhelper_obj (obj) -- mmhelper object
        dedup_obj (obj) -- Dedup Object
        sqlobj (obj)    -- SQL connection object
        subclient_name_prefix (str) -- subclient name prefix for subclient creation

        Return:
        True if test succeeds, False otherwise
        """
        self.log.info("===================QI TIME THRESHOLD=================")
        return_flag = True
        self.log.info("---Configuring new Dedup Storage Policy for QI time threshold verification---")
        self.log.info("Creating new storage policy - %s", self.storage_policy_name)
        self.dedup_path = "%s_%s" % (self.dedup_path, "_qi_time_threshold")
        sp_obj = self.commcell.storage_policies.add(
            self.storage_policy_name, self.library_name, self.mediaagentname, self.dedup_path)
        self.log.info("---Successfully configured storage policy - %s", self.storage_policy_name)
        self.storage_policy_list.append(self.storage_policy_name)
        sp_obj = self.commcell.storage_policies.get(self.storage_policy_name)



        self.log.info("Create a new subclient and run a backup")
        subclient_obj = self.create_subclient_run_backup(11, subclient_name_prefix, mmhelper_obj)

        copy_id = mmhelper_obj.get_copy_id(str(self.storage_policy_name), str(self.copy_name))
        engine_id = self.get_all_ddbs_for_copy(copy_id, 1001)[0][0]
        substore_id = dedup_obj.get_sidb_ids(sp_obj.storage_policy_id, self.copy_name)[1]
        self.log.info("DDB Engine ID created at the time of copy creation - %s", engine_id)

        # Set DDB Disk space update interval to 5 mins. This is to ensure that if DDB becomes full, it is
        # solely based on QI Time and no disk space is involved.

        self.log.info("Updating DDB Disk Space Update Threshold to 5 minutes")
        query = "update MMCONFIGS set nmin=5, value=5 where name='MMS2_CONFIG_MM_LOW_SPACE_ALERT_INTERVAL_MINUTES'"
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        self.log.info("Sleeping for DDB disk space update to happen")
        time.sleep(self.MM_THREAD_SLEEP_TIME)
        # Set SIDB store's CreatedTime to 2 month old time
        query = "select CreatedTime from idxsidbstore where sidbstoreid=%s" % engine_id
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        created_time = int(self.csdb.fetch_one_row()[0])
        self.log.info("Original CreatedTime for SIDB store %s is %s", engine_id, created_time)
        backdated_created_time = created_time - (86400 * 60)
        self.log.info("2 month old CreatedTime for SIDB store %s is %s", engine_id, backdated_created_time)
        query = "update idxsidbstore set createdtime = %s where sidbstoreid=%s" % (backdated_created_time, engine_id)
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        # Set SIDB substore's idxcache values to dummy values which don't violate disk space constraints
        query = "update idxcache set totalcapacitymb=204800, FreeDiskSpaceMB=181920 where IdxCacheId= " \
                "(select idxcacheid from idxsidbsubstore where sidbstoreid=%s)" % engine_id
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        # Now insert 30 rows with QI Time > 1000 so that median value for last 30 days comes to be > 1000
        self.log.info("Setting QI time count for last 30 days to be greater than 1000 microseconds")


        query = """declare @i int = 0
                declare @modifiedtime int = %s
                while @i < 50
                begin
                insert into IdxSIDBUsageHistory values
                (%s,%s,2,2,@modifiedtime,200000000,1500000,1100,100,0,0,0,40000000,0,'',0,393,151366,0)
                set @i = @i + 1
                set @modifiedtime = @modifiedtime - 86400
                end
                """ % (created_time, engine_id, substore_id)


        # TODO: Add a check that if PrimaryCount is less than 200 million, new store will not get created
        self.log.info("QUERY: %s", query)
        sqlobj.execute(query)

        for i in range(0, 3):
            # Need to do this in every loop as new rows keep getting added to this table
            self.log.info("Setting primary entry count for sidbstore to 200 million plus")
            query = "update idxsidbusagehistory set PrimaryEntries = 200000000 where sidbstoreid = %s" % engine_id
            self.log.info("QUERY: %s", query)
            sqlobj.execute(query)
            self.log.info("Executing stored proc to simulate MM thread invocations & sleeping for 60 seconds")
            query = "exec CommServ.dbo.archUpdateStoreLimitFlagOnStoragePolicy"
            self.log.info("QUERY: %s", query)
            self.dbhandle.execute_stored_procedure(query, None)
            time.sleep(60)

            # Now check if a new DDB has got created
            current_ddbs = self.get_all_ddbs_for_copy(copy_id, 1001)
            if len(current_ddbs) == 2:
                self.log.info("Second DDB got created for Storage Policy copy as expected")
                return_flag = True
                # Now check if 2nd DDB got marked as FULL
                if self.is_ddb_full(engine_id):
                    self.log.info("Successfully verified that old DDB engine id %s is marked FULL", engine_id)
                    # Check DDB FULL Reason
                    return_flag = self.validate_ddb_full_reason(engine_id, 1)

                new_engine_id = int(current_ddbs[-1][0])
                if not self.is_ddb_full(new_engine_id):
                    self.log.info("Successfully verified that new DDB engine id %s is not FULL", new_engine_id)
                else:
                    self.log.error("New DDB engine id %s is marked as FULL instead of ACTIVE", new_engine_id)
                    return_flag = False
                break
            else:
                self.log.error("There is still only 1 DDB of type FS associated with this storage policy copy")
                return_flag = False

        if not return_flag:
            self.log.error("No new DDB creation happened, hence returning failure.")

        self.log.info("Cleaning up storage policy.")
        self.backupset_obj.refresh()
        self.backupset_obj.subclients.delete(subclient_obj.subclient_name)
        self.commcell.storage_policies.delete(self.storage_policy_name)
        return return_flag

    def validate_ddb_full_reason(self, engine_id, expected_reason):
        """
        Validates if DDB Full Reason matches with the user provided Full Reason
        Args:
        engine_id (int) -- DDB Engine ID
        expected_reason (int) -- Expected FULL reason

        Return:
        True if expected reason is same as DDB full reason in CSDB, False otherwise
        """
        query = "select FULLREASON from idxsidbstore where sidbstoreid=%s" % engine_id
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        full_reason = int(self.csdb.fetch_one_row()[0])
        self.log.info(full_reason)
        if full_reason == expected_reason:
            self.log.info("Successfully verified that DDB FULL REASON = %s", expected_reason)
            return True

        self.log.error("Failed to verify DDB FULL REASON. Expected = %s Actual = %s", expected_reason, full_reason)
        return False

    def get_subclient_ddb_association(self, appid, copy_id):
        """
        Get DDB associated with a subclient for a given storage policy copy
        Args:
        appid (int) -- Subclient ID
        copy_id (int) -- Storage policy copy id

        Return:
        DDB Engine ID associated with the subclient
        """
        query = "select sidbstoreid from archsubclientcopyddbmap where appid = %s and copyid = %s" % (appid, copy_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        sidb_id = self.csdb.fetch_one_row()[0]
        self.log.info(sidb_id)
        return sidb_id

    def get_all_ddbs_for_copy(self, copy_id, apptypegroupid, only_active=False):
        """
        Get all DDB engines associated to a storage policy copy
        Args:
        copy_id (int) -- Storage policy copy id
        apptypegroupid (int) -- AppTypeGroupID ( FS=1001 DB=1002 VSA=1003)
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
        #When DDB is FULL, flag 1 is set on store. So a FULL DDB will always have ODD number as flag.
        if flags:
            return True

        return False

    def run_backup_job(self, subclient_obj, backuptype="Incremental"):
        """
        Run a backup job on subclient
        Args:
        subclient_obj (object) -- object of subclient class
        backuptype (str) -- Backup type , Incremental by default.

        """

        fulljobobj = subclient_obj.backup(backuptype)
        self.log.info("Successfully initiated a backup job on subclient with jobid - %s", fulljobobj.job_id)
        if not fulljobobj.wait_for_completion():
            raise Exception("Backup job %s did not complete in given timeout" % fulljobobj.job_id)

        self.log.info("Successfully completed a backup job on subclient with jobid - %s", fulljobobj.job_id)

    def create_subclient_run_backup(self, subclient_number, subclient_name_prefix, mmhelper_obj):
        """
        Create a subclient and run backup on the subclient
        Args:
        subclient_number (int) -- subclient name suffix
        subclient_name_prefix (str) -- subclient name prefix
        mmhelper_obj (obj)  -- mmhelper object

        Return:
        Returns content subclient object
        """
        current_content_dir = self.machineobj.join_path(self.content_path, str(subclient_number))
        if self.machineobj.check_directory_exists(current_content_dir):
            self.machineobj.remove_directory(current_content_dir)
        self.machineobj.create_directory(current_content_dir)
        self.log.info("----------Content directory %s created----------", current_content_dir)
        self.log.info("---Configuring subclient %s---", subclient_number)
        subclient_obj = MMHelper.configure_subclient(
            self, subclient_name="%s%s" %
            (subclient_name_prefix, subclient_number), content_path=current_content_dir)
        subclient_obj.data_readers = 1
        mmhelper_obj.create_uncompressable_data(self.client.client_name, current_content_dir, 0.1, 0)
        self.run_backup_job(subclient_obj)
        return subclient_obj
