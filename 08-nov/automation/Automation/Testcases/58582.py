# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    _run_backup()   --  initiates the backup job for the specified subclient

    run()           --  run function of this test case


    Input Example:

    "testCases": {

				"58582": {
					"ClientName": "mm-scalema-02",
					"AgentName": "File System",
					"MediaAgentToDelete": "madeleteauto",
					"MediaAgent2": "ssrup1"
				}
            }

"""
import time
import threading
from cvpysdk.job import Job
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils.options_selector import OptionsSelector
from Install.install_helper import WindowsInstallHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test case of MediaAgent delete"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MediaAgent delete basic case"

        self.storage_policy = None
        self.ma1 = None
        self.ma2 = None
        self.library_path1 = None
        self.ddb_path1 = None
        self.ddb_path2 = None
        self.ma1_machine_obj = None
        self.ma2_machine_obj = None
        self.client_machine_obj = None
        self.ma1_drive = None
        self.ma2_drive = None
        self.client_drive = None
        self.ma1_path = None
        self.ma2_path = None
        self.client_path = None
        self.dhlpr = None
        self.ma_helper = None
        self.ma1_obj = None
        self.ma2_obj = None
        self.sp_obj = None
        self.backup_set_obj = None
        self.job_obj = None
        self.library1 = "MA_Delete_Library_1_58582"
        self.copy1 = "AuxCopy1"
        self.client = None
        self.client_content = None
        self.backup_set = "MA_Delete_BS_58582"
        self.subclient = "MA_Delete_SC_58582"

        self.ma1_directory_created = None
        self.ma2_directory_created = None
        self.client_directory_created = None

        self.is_case_failed = None

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentToDelete": None,
            "MediaAgent2": None}

    def setup(self):
        """Setup function of this test case"""
        self.log.info("This is MediaAgent delete basic case")
        self.log.info("Starting test case setup")
        self.storage_policy = "MA_Delete_SP_58582"
        self.ma1 = self.tcinputs['MediaAgentToDelete']
        self.ma2 = self.tcinputs['MediaAgent2']
        self.client = self.tcinputs['ClientName']

        utility = OptionsSelector(self.commcell)

        self.ma1_machine_obj = Machine(self.ma1, self.commcell)
        self.ma2_machine_obj = Machine(self.ma2, self.commcell)
        self.client_machine_obj = Machine(self.client, self.commcell)

        self.ma1_drive = utility.get_drive(self.ma1_machine_obj, 5000)
        self.ma2_drive = utility.get_drive(self.ma2_machine_obj, 5000)
        self.client_drive = utility.get_drive(self.client_machine_obj, 2000)

        self.ma1_path = self.ma1_drive + "MA_Delete_" + str(self.id) + "_" + str(
            time.time()) + self.ma1_machine_obj.os_sep
        self.ma2_path = self.ma2_drive + "MA_Delete_" + str(self.id) + "_" + str(
            time.time()) + self.ma2_machine_obj.os_sep
        self.client_path = self.client_drive + "MA_Delete_" + str(self.id) + "_" + str(
            time.time()) + self.client_machine_obj.os_sep

        self.ddb_path1 = self.ma1_path + "DDB" + self.ma1_machine_obj.os_sep
        self.log.info("ddb_path1 : %s", self.ddb_path1)
        self.ddb_path2 = self.ma2_path + "DDB" + self.ma2_machine_obj.os_sep
        self.log.info("ddb_path2 : %s", self.ddb_path2)
        self.library_path1 = self.ma1_path + "MP"
        self.log.info("library_path1 : %s", self.library_path1)
        self.client_content = self.client_path + "SubClient_Content"
        self.log.info("client_content : %s", self.client_content)

        self.dhlpr = DedupeHelper(self)
        self.ma_helper = MMHelper(self)

        self.log.info("Successfully completed test case setup")


    def create_disk_library(self, library_name, mount_path, ma_obj):
        """
        Delete (if exists) and recreate the library

        Args:
            library_name -- (str) -- Name of the library to be created
            mount_path -- (str) -- Directory of the library
            ma_obj -- (Object of MediaAgent class) -- MediaAgent Object where the Mount Path will be created


        """

        self.log.info("Library : %s", library_name)
        self.log.info("MA : %s", ma_obj._media_agent_name)
        self.log.info("Creating library")
        self.commcell.disk_libraries.add(library_name, ma_obj._media_agent_name, mount_path)
        self.log.info("Library creation successful")

    def create_multi_partition_dedupe_copy(self, destination_ma_name,
                                           ddb_ma1_name, ddb_path):
        """
        Create 2 partitioned (on same MediaAgent) DDB aux copy

        Args:
            destination_ma_name -- (str) -- DataPath MediaAgent for aux copy
            ddb_ma1_name -- (str) -- MediaAgent for both the partitione
            ddb_path -- (str) -- DDB path (Directory)



        """
        self.log.info("Creating secondary copy")

        self.log.info("Creating aux copy. Copy Name : %s", self.copy1)
        self.dhlpr.configure_dedupe_secondary_copy(self.sp_obj, self.copy1, self.library1, destination_ma_name, ddb_path+str(time.time()), ddb_ma1_name)
        sidb_store_ids = self.dhlpr.get_sidb_ids(self.sp_obj.storage_policy_id, self.copy1)
        sp_copy_obj = self.sp_obj.get_copy(str(self.copy1))
        self.log.info("Copy created with 1 DDB partition")
        self.log.info("Adding 1 more partition on MA %s", ddb_ma1_name)
        self.log.info("SIDB Store ID %s", str(sidb_store_ids))
        self.sp_obj.add_ddb_partition(str(sp_copy_obj.get_copy_id()), str(sidb_store_ids[0]),
                                      str(ddb_path + str(time.time())), str(ddb_ma1_name))
        self.log.info("Secondary copy created successfully")

        self.log.info("Removing the association with system created schedule policy and this secondary copy")
        self.ma_helper.remove_autocopy_schedule(self.storage_policy, self.copy1)
        self.log.info("Successfully removed the association")

    def verify_mmhost_table(self, ma_id):
        """
        Verify that host details deleted from MMHost table

        Args:
            ma_id -- (str) -- MediaAgent ID


        """
        query = """select count(*) from mmhost where ClientId={0}""".format(ma_id)
        self.csdb.execute(query)
        count = self.csdb.fetch_one_row()[0]

        if int(count) != 0:
            self.is_case_failed = True
            raise Exception('Validation Failed :: MMHost table is not cleaned-up')
        self.log.error("MMHost table cleaned-up for the deleted MediaAgent.")

    def verify_partition_host(self, copy_name, expected_host_id):
        """
        Verify the DDB host IDs after MA delete

        Args:
            copy_name -- (str) -- Storage Policy Copy Name
            expected_host_id -- (str) -- Expected host ID for all the DDB partitions

        Exception:
                If validation failed
        """
        query = """
                        select p.ClientId 
   	                    from archGroup grp, archGroupCopy cp, IdxSIDBStore s, IdxSIDBSubStore ss, IdxAccessPath p 
    	                where grp.id = cp.archGroupId 
                        and cp.SIDBStoreId = s.SIDBStoreId 
	                    and s.SIDBStoreId = ss.SIDBStoreId 
	                    and ss.IdxAccessPathId = p.IdxAccessPathId 
	                    and cp.name = '{0}' 
	                    and grp.name = '{1}'     
                """.format(copy_name, self.storage_policy)

        self.csdb.execute(query)
        host_list = self.csdb.fetch_all_rows()
        for host in host_list:
            if int(host[0]) != int(expected_host_id):
                self.is_case_failed = True
                raise Exception("Expected DDB partition Host ID [{0}] but found host id [{1}] for copy [{2}]".format(expected_host_id, host[0], copy_name))
            self.log.info("Validation Passed::Expected DDB partition Host ID [%s] and Host ID in DB [%s] for Copy [%s]", expected_host_id, host[0], copy_name)


    def get_uninstall_job_object(self, ma_host_id):
        """
        Return job object of the uninstall job

        Args:
            ma_host_id -- (str) -- MA host ID to fetch the uninstall job ID
        Return:
                Job object of uninstall job
        """

        query = """
                    select us.jobId
                    from JMQinetixUpdateStatus US 
                    inner join JMAdminJobInfoTable JS on us.jobId = js.jobId 
                    and js.opType = 68 
                    and us.clientId = {0}""".format(ma_host_id)

        self.csdb.execute(query)
        job_id = self.csdb.fetch_one_row()[0]
        return Job(self.commcell, job_id)

    def check_media_agent_package(self, media_agent_name):
        """
        Check if MediaAgent package installed. If not, install that

        Args:
            media_agent_name -- (str) -- MediaAgent name

        """
        self.log.info("Checking if MediaAgent package is installed on [%s]", media_agent_name)
        if self.commcell.media_agents.has_media_agent(media_agent_name):
            self.log.info("MediaAgent package installed on [%s]", media_agent_name)
        else:
            self.log.info(
                "MediaAgent package is not installed. Installing MediaAgent package on client [%s]", media_agent_name)
            machine = Machine(media_agent_name, self.commcell)
            windows_install_helper = WindowsInstallHelper(self.commcell, machine)
            job_obj = windows_install_helper.install_software([media_agent_name], ['MEDIA_AGENT'])
            self.log.info("Waiting for the install job to complete. Job ID %s", job_obj._job_id)
            job_obj.wait_for_completion()
            time.sleep(15)
            self.commcell.media_agents.refresh()
            self.log.info("MediaAgent package is installed")

    def cleanup(self):
        """Cleanup the existing entities"""

        self.log.info("Deleting BackupSet if exists")
        if self._agent.backupsets.has_backupset(self.backup_set):
            self.log.info("BackupSet[%s] exists, deleting that", self.backup_set)
            self._agent.backupsets.delete(self.backup_set)

        self.log.info("Deleting Storage Policy if exists")
        if self.commcell.storage_policies.has_policy(self.storage_policy):
            self.log.info("Storage Policy[%s] exists, deleting that", self.storage_policy)
            self.commcell.storage_policies.delete(self.storage_policy)

        self.log.info("Deleting library if exists")
        if self.commcell.disk_libraries.has_library(self.library1):
            self.log.info("Library[%s] exists, deleting that", self.library1)
            self.commcell.disk_libraries.delete(self.library1)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        if self.is_case_failed != True:
            self.log.info("Test case completed, deleting BS, SP, Library")
            self.cleanup()
        else:
            self.log.info("Test case failed, NOT deleting SC, BS, SP, Library")

        if self.client_directory_created == True:
            self.log.info("Deleting the SubClient content directory")
            self.ma_helper.remove_content(self.client_path, self.client_machine_obj)

        if self.ma1_directory_created == True:
            self.log.info("Deleting %s on %s", self.ma1_path, self.ma1)
            self.ma_helper.remove_content(self.ma1_path, self.ma1_machine_obj)

        if self.ma2_directory_created == True:
            self.log.info("Deleting %s on %s", self.ma2_path, self.ma2)
            self.ma_helper.remove_content(self.ma2_path, self.ma2_machine_obj)

    def run(self):
        """Main test case logic"""
        try:


            # Will check if MA package is installed simultaneously.
            thread1 = threading.Thread(target=self.check_media_agent_package, args=(self.ma1,))
            thread2 = threading.Thread(target=self.check_media_agent_package, args=(self.ma2,))

            thread1.start()
            thread2.start()

            thread1.join()
            thread2.join()

            self.log.info("Creating MediaAgent objects")
            self.ma1_obj = self.commcell.media_agents.get(self.ma1)
            self.ma2_obj = self.commcell.media_agents.get(self.ma2)
            self.log.info("Created objects for all MediaAgents")

            self.log.info("Cleanup old entities if exists")
            self.cleanup()

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.client_content, 0.4)
            self.client_directory_created = True

            self.create_disk_library(self.library1, self.library_path1, self.ma1_obj)
            self.ma1_directory_created = True

            self.log.info("Creating Storage Policy [%s]", self.storage_policy)
            self.commcell.storage_policies.add(self.storage_policy, self.library1, self.ma1, self.ddb_path1+str(time.time()), self.ma1)
            self.sp_obj = self.commcell.storage_policies.get(self.storage_policy)
            self.log.info("SP created with 1 partition,adding 1 more partition on MA [%s]", self.ma2)
            sidb_store_ids = self.dhlpr.get_sidb_ids(self.sp_obj.storage_policy_id, "Primary")
            sp_copy_obj = self.sp_obj.get_copy("Primary")
            self.log.info("SIDB Store ID %s", str(sidb_store_ids))
            self.sp_obj.add_ddb_partition(str(sp_copy_obj.get_copy_id()), str(sidb_store_ids[0]),
                                          self.ddb_path2 + str(time.time()), str(self.ma2))
            self.ma2_directory_created = True

            self.log.info("Storage Policy with 2 partitions created successfully")

            self.create_multi_partition_dedupe_copy(self.ma1, self.ma1, self.ddb_path1)

            self.log.info("Creating BackupSet")
            self.backup_set_obj = self._agent.backupsets.add(self.backup_set)

            self.subclient = self.ma_helper.configure_subclient(self.backup_set, self.subclient, self.storage_policy, self.client_content)

            # Starting backup
            self.log.info("Will run 2 backup jobs")
            for j in range(2):
                self.log.info("Starting backup job")
                self.job_obj = self.subclient.backup("FULL")
                self.log.info("Waiting for the job to complete. Job ID %s", self.job_obj._job_id)
                if self.job_obj.wait_for_completion():
                    self.log.info("Job completed")
                else:
                    self.is_case_failed = True
                    self.log.info("Job failed, failing the case")
                    raise Exception('Job is not completed')

            self.log.info("Starting aux copy job")
            self.job_obj = self.sp_obj.run_aux_copy(self.copy1, use_scale=True, all_copies=False)
            self.log.info("Waiting for the aux copy job to complete. Job ID %s", self.job_obj._job_id)
            if self.job_obj.wait_for_completion():
                self.log.info("Job completed")
            else:
                self.is_case_failed = True
                self.log.info("Job failed, failing the case")
                raise Exception('Job is not completed')

            ma_id = self.ma1_obj._media_agent_id

            self.log.info("Deleting MediaAgent [%s]", self.ma1)
            self.commcell.media_agents.delete(self.ma1)
            self.log.info("MediaAgent deleted successfully")

            # MMHOst table entry should be deleted. Verifying that
            self.log.info("MMHost table entry should be deleted. Verifying that")
            self.verify_mmhost_table(ma_id)

            # All DDB partitions of Primary copy should be moved to MA2
            self.log.info("Verifying DDB host entries for Primary copy")
            self.verify_partition_host("Primary", self.ma2_obj._media_agent_id)

            # All DDB partitions of Aux copy copy should have dummy host ID
            self.log.info("Verifying DDB host entries for Aux copy")
            self.verify_partition_host(self.copy1, "1")

            job_obj = self.get_uninstall_job_object(self.ma1_obj._media_agent_id)
            self.log.info("Waiting for uninstall job to complete. Job ID : %s", str(job_obj._job_id))
            job_obj.wait_for_completion()
            self.log.info("Uninstall job completed")

            # It might take upto 2 mins to sync with CS after completing the uninstall else cleanup will fail
            time.sleep(120)

            self.log.info("Test case completed successfully")

        except Exception as excp:
            self.is_case_failed = True
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
