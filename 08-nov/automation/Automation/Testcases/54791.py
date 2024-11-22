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

    create_sql_subclient()  --  Create a new Database and a SQL DB subclient to back up this content

    create_vsa_subclient()  --  Create a VSA subclient

    create_fs_subclient()   --  Create a File System IDA subclient

    validate_subclient_ddb_mapping()    --  Validate whether a subclient has correctly got
                                            mapped to DDB in a given copy

"""
import time
from cvpysdk.constants import VSAObjects
from AutomationUtils import constants, config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from Application.SQL.sqlhelper import SQLHelper
from Application.SQL import sqlconstants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Subclient to DDB Mapping for different IDAs"
        self.tcinputs = {
            "MediaAgentName": None,
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
        self.result_string = ""
        self.dedup_obj = None
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

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.backup_vm_name = self.tcinputs['HyperVBackupVM']
        self.machineobj = Machine(self.client)
        self.client_system_drive = optionobj.get_drive(self.machineobj)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        self.ma_ddb_drive = optionobj.get_drive(self.ma_machineobj)
        timestamp_suffix = OptionsSelector.get_custom_str()
        self.dbname = "54791_%s" % timestamp_suffix
        self.dedup_path = self.ma_machineobj.join_path(
            self.ma_ddb_drive, "DDBs\\tc_54791_{0}".format(timestamp_suffix))
        self.storage_policy_name = "%s_%s" % ("tc_54791_sp", timestamp_suffix)
        self.library_name = "lib_%s_%s" % ("tc_54791_sp", timestamp_suffix)
        self.backupset_name = "bkpset_tc_54791_%s" % timestamp_suffix
        self.vsa_backupset_name = "vsa_bkpset_tc_54791_%s" % timestamp_suffix
        self.sql_backupset_name = "defaultBackupSet"
        self.fs_subclient_name = "fs_subc_tc_54791_%s" % timestamp_suffix
        self.vsa_subclient_name = "default"
        self.sql_subclient_name = "sql_subc_tc_54791_%s" % timestamp_suffix
        self.content_path = self.machineobj.join_path(self.client_system_drive, "content_54791")
        self.backupset = "defaultBackupSet"
        self.subclient = "default"
        self.tcstatus = True
        self.tcresult = ""

    def run(self):
        """Run function of this test case"""
        try:

            # Local Variable initialization
            CONSTANTS = config.get_config()
            self.dedup_obj = DedupeHelper(self)
            self.mmhelper_obj = MMHelper(self)
            self.sqluser = CONSTANTS.SQL_USER
            self.sqlpassword = CONSTANTS.SQL_PASSWORD
            mountpath = self.tcinputs['MountPath']

            vsa_client = self.tcinputs["HyperVClientName"]
            vsa_agent = self.tcinputs['HyperVAgentName']

            sql_client = self.tcinputs["DatabaseClientName"]
            sql_agent = self.tcinputs["DatabaseAgentname"]

            self.vsaclient = self.commcell.clients.get(vsa_client)
            self.vsaagent = self.vsaclient.agents.get(vsa_agent)
            instancekeys = next(iter(self.vsaagent.instances.all_instances))
            self.vsainstance = self.vsaagent.instances.get(instancekeys)

            self.sqlclient = self.commcell.clients.get(sql_client)
            self.sqlagent = self.sqlclient.agents.get(sql_agent)
            sqlinstance_keys = next(iter(self.sqlagent.instances.all_instances))
            self.sqlinstance = self.sqlagent.instances.get(sqlinstance_keys)


            self.log.info("----------Configuring TC environment-----------")
            self.log.info("---Create new Library---")

            # Create new library
            self.mmhelper_obj.configure_disk_library(
                self.library_name, self.mediaagentname, mountpath)
            self.log.info("---Configuring backup set---")

            self.log.info("---Configuring new Dedup Storage Policy for subclient "
                          "to ddb association verification---")
            self.log.info("Creating new storage policy - %s", self.storage_policy_name)
            sp_obj = self.commcell.storage_policies.add(
                self.storage_policy_name, self.library_name, self.mediaagentname, self.dedup_path)
            self.log.info(
                "---Successfully configured storage policy - %s",
                self.storage_policy_name)
            sp_id = self.commcell.storage_policies.get(self.storage_policy_name).storage_policy_id
            copy_id = self.mmhelper_obj.get_copy_id(self.storage_policy_name, 'Primary')
            copy = sp_obj.get_copy('Primary')
            self.log.info("setting copy retention: 1 day, 0 cycle")
            copy.copy_retention = (1, 0, 1)
            #Form 118685 : Now only 1 DDB gets created at the beginning and then as new datatypes start
            #using this store, horizontal scaling starts and 1 new DDB for each datatype gets added

            #STEP 0 : Verify only 1 DDB gets created
            self.log.info("Validate that there is 1 DDB after Storage Policy creation.")
            self.validate_dedup_store_creation(1, False)

            #STEP 2 : Create a FileSystem subclient and verify DDB association

            fs_subclient = self.create_fs_subclient()
            fulljob_obj = fs_subclient.backup("Full")
            if not fulljob_obj.wait_for_completion():
                raise Exception("Backup job %s did not complete due to - %s" %(
                    fulljob_obj.job_id, fulljob_obj.delay_reson))
            self.log.info(
                "Successfully completed the FS backup job on subclient with jobid - %s",
                fulljob_obj.job_id)

            self.log.info("Validate that there is only 1 DDB after FS backups.")
            self.validate_dedup_store_creation(1, False)

            expected_ddb = self.dedup_obj.get_sidb_ids(sp_id, 'Primary')
            if self.validate_subclient_ddb_mapping(self.storage_policy_name, 'Primary',
                                                   self.fs_subclient_name, expected_ddb[0],
                                                   self.backupset_name, self.client.client_name):
                self.log.info("***Validate FS Subclient Mapping to FS DDB ==> PASS***")
                self.tcresult = "%s\n%s" % (self.tcresult,
                                       "***Validate FS Subclient Mapping to FS DDB ==> PASS***")
            else:
                self.log.error("***Validate FS Subclient Mapping to FS DDB ==> FAIL***")
                self.tcresult = "%s\n%s" % (self.tcresult,
                                       "***Validate FS Subclient Mapping to FS DDB ==> FAIL***")
                self.tcstatus = False

            #STEP 3 : Create a DB subclient and verify DDB association

            sql_subclient = self.create_sql_subclient()
            fulljob_obj = sql_subclient.backup("Full")

            self.log.info(
                "Successfully initiated a backup job on SQL subclient with jobid - %s",
                fulljob_obj.job_id)
            if not fulljob_obj.wait_for_completion():
                raise Exception(
                    "Backup job %s did not complete due to - %s" %(
                        fulljob_obj.job_id, fulljob_obj.delay_reson))

            self.log.info(
                "Successfully completed the SQL backup job on subclient with jobid - %s",
                fulljob_obj.job_id)

            self.log.info("Validate that there are 2 DDBs after Database backups.")
            self.validate_dedup_store_creation(2, False)

            expected_ddb = self.dedup_obj.get_db_sidb_ids(copy_id)
            if self.validate_subclient_ddb_mapping(self.storage_policy_name, 'Primary',
                                                   self.sql_subclient_name, expected_ddb[0],
                                                   self.sql_backupset_name,
                                                   self.sqlclient.client_name):
                self.log.info("***Validate SQL Subclient Mapping to SQL DDB ==> PASS***")
                self.tcresult = "%s\n%s" % (self.tcresult,
                                       "***Validate SQL Subclient Mapping to SQL DDB ==> PASS***")

            else:
                self.log.error("***Validate SQL Subclient Mapping to SQL  DDB ==> FAIL***")
                self.tcresult = "%s\n%s" % (self.tcresult,
                                       "***Validate SQL Subclient Mapping to SQL  DDB ==> FAIL***")
                self.tcstatus = False

            #STEP 4 : Create a HyperV subclient and verify DDB association

            vsa_subclient = self.create_vsa_subclient()
            fulljob_obj = vsa_subclient.backup("Full")

            self.log.info(
                "Successfully initiated a backup job on VSA subclient with jobid - %s",
                fulljob_obj.job_id)
            if not fulljob_obj.wait_for_completion():
                raise Exception(
                    "Backup job %s did not complete due to - %s" %(
                        fulljob_obj.job_id, fulljob_obj.delay_reson))

            self.log.info(
                "Successfully completed the VSA backup job on subclient with jobid - %s",
                fulljob_obj.job_id)

            self.log.info("Validate that there are 3 DDBs after Database backups.")
            self.validate_dedup_store_creation(3, True)

            expected_ddb = self.dedup_obj.get_vm_sidb_ids(copy_id)
            if self.validate_subclient_ddb_mapping(self.storage_policy_name, 'Primary',
                                                   self.vsa_subclient_name, expected_ddb[0],
                                                   self.vsa_backupset_name,
                                                   self.vsaclient.client_name):
                self.log.info("***Validate VSA Subclient Mapping to VSA DDB ==> PASS***")
                self.tcresult = "%s\n%s" % (self.tcresult,
                                       "***Validate VSA Subclient Mapping to VSA DDB ==> PASS***")

            else:
                self.log.error("***Validate VSA Subclient Mapping to VSA  DDB ==> FAIL***")
                self.tcresult = "%s\n%s" % (self.tcresult,
                                       "***Validate VSA Subclient Mapping to VSA  DDB ==> FAIL***")
                self.tcstatus = False



            self.log.info(self.tcresult)
            if self.tcstatus:
                self.log.info("Subclient to DDB association test case completed successfully.")
            else:
                raise Exception(
                    "Failed to validate subclient to DDB mapping for Storage Policy Copy.Exiting.")


        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
        try:
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
                            "Assigning HyperV subclient to following storage policy - %s",
                            policy_name)
                        hyperv_subc_obj.storage_policy = policy_name
                        self.log.info("Sleeping for 1 minute before refreshing commcell")
                        time.sleep(60)
                        break
                    else:
                        self.log.info(f"Skipping Storage Policy {policy_name} as it is a glolbal dedup storage policy")

            self.log.info("Cleaning up SQL subclient")
            if not self.sqlhelper.dbinit.drop_databases(self.dbname):
                self.log.error("Unable to drop the dataBase")

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

            if self.machineobj.check_directory_exists(self.content_path):
                self.machineobj.remove_directory(self.content_path)
        except Exception as ex:
            self.log.error(f"Storage Policy deletion failed during cleanup - {ex}")

    def create_sql_subclient(self):
        """
        Create a new Database and a SQL DB subclient to back up this content

        Return : SQL DB subclient object
        """
        self.log.info("Creating new Database")

        self.sqlhelper = SQLHelper(
            self,
            self.sqlclient,
            self.sqlinstance.instance_name,
            self.sqluser,
            self.sqlpassword)

        noofdbs = 1
        nooffilegroupsforeachdb = 3
        nooffilesforeachfilegroup = 3
        nooftablesforeachfilegroup = 5
        noofrowsforeachtable = 6

        if self.sqlhelper.dbinit.check_database(self.dbname):
            if not self.sqlhelper.dbinit.drop_databases(self.dbname):
                raise Exception("Unable to drop the database")

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

        sql_subclient_obj = self.sqlinstance.subclients.add(
            self.sql_subclient_name, self.storage_policy_name, 'DATABASE')

        request_json = sqlconstants.SQL_SUBCLIENT_PROP_DICT
        self.dbname = self.dbname + "1"
        sql_subclient_obj.content = [self.dbname]
        sql_subclient_obj.log_backup_storage_policy = self.storage_policy_name
        subclient_prop = ["_mssql_subclient_prop", request_json]
        sql_subclient_obj.mssql_subclient_prop = subclient_prop

        request_json = sqlconstants.SQL_SUBCLIENT_STORAGE_DICT
        sql_subclient_obj.mssql_subclient_prop = [
            "_commonProperties['storageDevice']", request_json]

        return sql_subclient_obj

    def create_vsa_subclient(self):
        """
        Create a VSA subclient

        Return : VSA subclient object
        """

        # Configure backupset
        self.log.info("adding VSA Backupset...")
        self.vsa_backupset_name = "defaultBackupSet"
        vsa_backupset_obj = self.vsaagent.backupsets.get(self.vsa_backupset_name)
        self.log.info("Backupset config done.")

        #querying default subclient as custom subclient support is not present for VSA
        sckeys = next(iter(vsa_backupset_obj.subclients.all_subclients))

        hyperv_subc_obj = vsa_backupset_obj.subclients.get(sckeys)
        hyperv_subc_obj.storage_policy = self.storage_policy_name
        hyperv_subc_obj.content = [
            {
                'type': VSAObjects.VMName,
                'name': self.backup_vm_name,
                'display_name': self.backup_vm_name,
            }
        ]
        return hyperv_subc_obj

    def create_fs_subclient(self):
        """
        Create a File System IDA subclient

        Return: Subclient object after creation of subclient
        """
        self.backupset_obj = MMHelper.configure_backupset(self)
        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
        self.machineobj.create_directory(self.content_path)
        self.log.info("----------Content directory %s created----------", self.content_path)
        self.log.info("---Configuring subclient %s---", self.fs_subclient_name)
        fs_subc_obj = MMHelper.configure_subclient(self, subclient_name=self.fs_subclient_name)
        fs_subc_obj.data_readers = 1

        self.log.info("---Creating uncompressable unique data---")
        self.content_path = self.client_system_drive + self.machineobj.os_sep + "content_54791"
        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
        self.machineobj.create_directory(self.content_path)
        self.mmhelper_obj.create_uncompressable_data(
            self.client.client_name, self.content_path, 0.1, 0)
        return fs_subc_obj

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

    def validate_dedup_store_creation(self, expected_stores, check_details):
        """
        Validate whether expected number of dedup stores are getting created

        Args:
            expected_stores (int)       -- expected stores
            check_details   (boolean)   -- perform AppTypeGroupID validation

        Return: Boolean True or False based on whether validation succeeded or not
        """
        if self.validate_dedup_stores_for_copy(self.storage_policy_name, 'Primary', expected_stores, check_details):
            self.log.info("***Validate %s DDB creation for Storage Policy copy ==> PASS***", expected_stores)
            self.tcresult = "%s\n%s" % (
                self.tcresult, "***Validate %s DDB creation for Storage Policy copy ==> PASS***"%expected_stores)
        else:
            self.log.error("***Validate %s DDB creation for Storage Policy copy ==> FAIL***", expected_stores)
            self.tcresult = "%s\n%s" % (
                self.tcresult, "***Validate % DDB creation for Storage Policy copy ==> FAIL***"%expected_stores)
            self.tcstatus = False

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
        if expected_stores != 3:
            self.log.info("Skipping apptypegroupid check as this is first check after SP creation.")
            return True

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
