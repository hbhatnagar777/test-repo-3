
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


Test Case Input JSON:

            "59488": {
					"ClientName": "ssrv11console",
					"AgentName": "File System",
					"LibraryControllerMA": "ssrv11console",
					"DriveControllerMA" : "universe",
					"TapeLibrary":"CommVault API2"
				}


Configuration Note :

The tape library should be as following
    Library Controllers : MA1, MA2
    Drive Controller : MA1 or MA2 ( Any one MA)


"""

from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
import time, threading
import json
from cvpysdk.exception import SDKException


class TestCase(CVTestCase):
    """Class for executing tape library configuration test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Tape Library config and de-config case - Library hosted with more than one MA"

        self.ma_helper = None
        self.storage_policy = None
        self.backup_set = None
        self.sub_client = None
        self.path_prefix = None
        self.client = None
        self.library_name = None
        self.scratch_pool = None
        self.client_machine = None
        self.client_drive = None
        self.client_path = None
        self.client_content = None
        self.is_client_directory_created = None
        self.is_case_failed = None
        self.subclient = None
        self.MediaAgents_obj = {}
        self.MediaAgents = None
        self.LibraryControllerMA = None
        self.DriveControllerMA = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")

        utility = OptionsSelector(self.commcell)
        self.ma_helper = MMHelper(self)

        self.storage_policy = "TestCase_"+str(self.id) +"_SP"
        self.backup_set = "TestCase_"+str(self.id) +"_BS"
        self.sub_client = "TestCase_" + str(self.id) + "_SC"
        self.path_prefix = "TestCase_" + str(self.id) + "_" + str(time.time())

        self.client = self.tcinputs['ClientName']
        self.library_name = self.tcinputs['TapeLibrary']
        self.scratch_pool= "Default Scratch"
        self.DriveControllerMA = self.tcinputs['DriveControllerMA']
        self.LibraryControllerMA = self.tcinputs['LibraryControllerMA']
        self.DriveControllerMA_obj = self.commcell.media_agents.get(self.DriveControllerMA)
        self.LibraryControllerMA_obj= self.commcell.media_agents.get(self.LibraryControllerMA)
         
        """
        if len(self.MediaAgents) != 2:
            raise Exception("Two MediaAgents are expected for library controller.")
        """
        
        self.log.info("Creating client machine object")
        self.client_machine = Machine(self.client, self.commcell)
        self.log.info("Successfully created the machine object")

        self.log.info("Getting client drive")
        self.client_drive = utility.get_drive(self.client_machine, 1000)
        self.client_path = self.client_drive + self.path_prefix + self.client_machine.os_sep
        self.client_content = self.client_path + "subclient_content"
        self.log.info("Client content path %s", self.client_content)
        self.is_client_directory_created = False
        self.is_case_failed = False


    def cleanup(self):
        self.log.info("Starting cleanup")

        if self._agent.backupsets.has_backupset(self.backup_set):
                self.log.info("BackupSet [%s] exists, deleting that", self.backup_set)
                self._agent.backupsets.delete(self.backup_set)
                self.log.info("Backup set deleted successfully")

        if self.commcell.storage_policies.has_policy(self.storage_policy):
                self.log.info("Storage policy [%s] exists, deleting that", self.storage_policy)
                self.commcell.storage_policies.delete(self.storage_policy)
                self.log.info("Storage policy deleted successfully")

    def wait_for_job_complete(self, timeout=60*60):
        """
                Waits for the job to complete and try to delete the library when the job is in backup phase

                Args:
                    Time out -- (int) -- Time-out for the job

                Exception:
                    If the job is not completed within time out
                    If the library deleted successfully. Because, the library is reserved and should be failed to delete
        """
        start_time = time.time()
        self.log.info("Waiting for the job [%s] to complete.", self.job_obj.job_id)
        job_details = self.job_obj.details

        library_delete_tried = False
        self.DELETE_LIBRARY_SERVICE = self.commcell._services['LIBRARY']
        pay_load = {
            "isDeconfigLibrary": 1,
            "library": {
                "opType": 2,
                "libraryName": self.tape_lib_obj._name
            }
        }

        while job_details["jobDetail"]["progressInfo"]["state"] != "Completed":

            job_details = self.job_obj.details

            if not library_delete_tried:
                if job_details["jobDetail"]["progressInfo"]["currentPhase"] == "Backup" and job_details["jobDetail"]["progressInfo"]["state"] =="Running" :
                    self.log.info("Job is in backup phase and running state, trying to delete the library")
                    library_delete_tried = True
                    time.sleep(5)
                    flag, response = self.commcell._cvpysdk_object.make_request('POST', self.DELETE_LIBRARY_SERVICE , pay_load, 1)
                    #self.commcell.tape_libraries.delete(self.tape_lib_obj._name)

                    if not flag:
                        self.log.info("Library deletion failed, which is expected as its reserved.")
                        self.log.info("Verifying the DB entries")
                        self.verify_mmlibrary_table(False)
                        self.verify_MMDrivePool_table(False)
                        self.verify_MMMasterPool_table(False)
                        self.verify_MMDrives_table(False)
                    else:
                        self.log.error("Library deletion successful which is NOT expected. It should have failed")
                        raise Exception("Library deletion successful which is NOT expected. It should have failed")
                self.log.info("Job Phase : {0}".format(job_details["jobDetail"]["progressInfo"]["currentPhase"]))
            self.log.info("Job status : %s", job_details["jobDetail"]["progressInfo"]["state"])

            if job_details["jobDetail"]["progressInfo"]["state"] not in ["Completed", "Waiting", "Running", "Pending"]:
                raise Exception("Job is NOT completed successfully")

            if time.time() > (start_time+timeout):
                raise Exception('Job is NOT completed within expected time')
            time.sleep(5)

        self.log.info("Job [%s] completed successfully", self.job_obj.job_id)

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        if not self.is_case_failed:
            self.log.info("Test case completed. Deleting SC, BS, SP")
            self.cleanup()
        else:
            self.log.info("Test case failed, not deleting SC, BS, SP")

        if self.is_client_directory_created:
            self.log.info("Client directory created, deleting that")
            self.ma_helper.remove_content(self.client_path, self.client_machine)

    def configure_tape_library(self):
        """ Method to configure tape library"""
        self.log.info("Detecting and configuring tape library")
        ma_list_to_pass=[]
        ma_list_to_pass.append(int(self.LibraryControllerMA_obj.media_agent_id))
        ma_list_to_pass.append(int(self.DriveControllerMA_obj.media_agent_id))

        self.tape_lib_obj = self.commcell.tape_libraries.configure_tape_library(self.library_name, ma_list_to_pass)
        self.log.info("Library configured successfully. Tape Library Name : [%s]", self.tape_lib_obj._name)

    def verify_MMLibraryController_table(self, controller_id, after_delete=True ):
        """
            Verifies the entries on MMLibraryController table

            Args:
                controller_id -- (int) -- Controller ID of the library
                after_delete --(Boolean) -- If yes, the entries should not be there

            Exception:
                if after_delete=True and found DB entry
                if after_delete=False and not found DB entries
        """

        self.log.info("Verifying MMLibraryController table for controller [%s]", controller_id)

        query = "select count(*) from mmlibrarycontroller WITH (NOLOCK) where LibraryId = {0} and clientid= {1}".format(self.tape_lib_obj._library_id, controller_id)
        self.log.info(query)
        self.csdb.execute(query)
        count = self.csdb.fetch_one_row()[0]
        self.log.info("{0} entries found on table MMLibrary".format(count))

        if after_delete:
            if int(count) != 0:
                raise Exception("Entries found on MMLibrary, which is not expected")
            self.log.info("MMLibraryController table verified successfully")
        else:
            if int(count) != 1:
                raise Exception("Entries not found on MMLibrary, which is not expected")
            self.log.info("MMLibraryController table verified successfully")

    def verify_mmlibrary_table(self,after_delete=True):
        """
            Verifies the entries on MMLibrary table

            Args:
                after_delete --(Boolean) -- If yes, the entries should not be there

            Exception:
                if after_delete=True and found DB entry
                if after_delete=False and not found DB entries
        """
        self.log.info("verifying MMLibrary table")
        query = "select count(*) from mmlibrary WITH (NOLOCK) where aliasname='" \
                ""+self.tape_lib_obj._name+"' and LibraryLicenseType =-1"
        self.log.info("Verifying the mmlibrary table for library [%s]", self.tape_lib_obj._name)

        self.csdb.execute(query)
        count=self.csdb.fetch_one_row()[0]
        self.log.info("{0} entries found on table MMLibrary".format(count))

        if after_delete:
            if int(count) != 0 :
                raise Exception("Entries found on MMLibrary, which is not expected")
            self.log.info("MMLibrary table verified successfully")
        else:
            if int(count) <1:
                raise Exception("Entries not found on MMLibrary, which is not expected")

        self.log.info("MMLibrary table verified successfully")

    def verify_MMDrivePool_table(self, after_delete=True):
            """
            Verifies the entries on MMDrivePool table

            Args:
                after_delete --(Boolean) -- If yes, the entries should not be there

            Exception:
                if after_delete=True and found DB entry
                if after_delete=False and not found DB entries
            """

            self.log.info("Verifying MMDrivePool table")
            print (self.drive_pools[self.DriveControllerMA_obj.media_agent_id])
            query ="select count(*) from MMDrivePool WITH (NOLOCK) where DrivePoolName='"+self.drive_pools[self.DriveControllerMA_obj.media_agent_id]+"'"

            self.log.info("Executing the following query")
            self.log.info(query)

            self.csdb.execute(query)
            count = self.csdb.fetch_one_row()[0]
            self.log.info("{0} entries found on table MMDrivePool for DrivePoolName [{1}]".format(count,self.drive_pools[self.DriveControllerMA_obj.media_agent_id]))

            if after_delete:
                if int(count) != 0:
                    raise Exception("Entries found on MMDrivePool, which is not expected")

            else:
                if int(count) !=1:
                    raise Exception("Entries not found on MMDrivePool, which is not expected")

            self.log.info("MMDrivePool table verified successfully")

    def verify_MMMasterPool_table(self, after_delete=True):
        """
            Verifies the entries on MMMasterPool table

            Args:
                controller_id -- (int) -- Controller ID of the library
                after_delete --(Boolean) -- If yes, the entries should not be there

            Exception:
                if after_delete=True and found DB entry
                if after_delete=False and not found DB entries
        """

        self.log.info("Verifying MMMasterPool table")

        for mp in self.master_pools.values():
            query ="select count(*) from MMMasterPool WITH (NOLOCK) where MasterPoolName='{0}'".format(mp)
            self.log.info("Executing the following query")
            self.log.info(query)
            self.csdb.execute(query)
            count = self.csdb.fetch_one_row()[0]
            self.log.info("{0} entries found on table MMMasterPool for MasterPoolName [{1}]".format(count, mp))

            if after_delete:
                if int(count) != 0:
                    raise Exception("Entries found MMMasterPool, which is not expected")
            else :
                if int(count) !=1:
                    raise Exception("Entries NOT found MMMasterPool, which is not expected")

            self.log.info("MMMasterPool table verified")


    def unload_all_drives(self):
        """
        Unload the drives of the tape
        """
        drive_list = self.tape_lib_obj.get_drive_list()

        for drive in drive_list:
            self.ma_helper.unload_drive(self.tape_lib_obj._name, drive)

 
    def verify_MMDrives_table(self, after_delete = True):
        """
            Verifies the entries on MMdrives table

            Args:
                after_delete --(Boolean) -- If yes, the entries should not be there

            Exception:
                if after_delete=True and found DB entry
                if after_delete=False and not found DB entries
        """

        self.log.info("Verifying MMDrive table")

        for master_pool_id, master_pool_name in self.master_pools.items():
            self.log.info("Verifying drives for master pool [{0}]".format(master_pool_name))
            query = "select count(*) from mmdrive WITH (NOLOCK) where masterpoolid={0}".format(master_pool_id)
            self.log.info("Executing the following query")
            self.log.info(query)
            count = self.csdb.fetch_one_row()[0]
            self.log.info("Entries found on table MMDrive for MasterPoolID [{0}]".format(master_pool_id))

            if after_delete:
                if int(count) !=0:
                    raise SDKException("Entries found on MMDrive, which is not expected")
            else:
                if int(count) <1:
                    raise SDKException("Entries NOT found on MMDrive, which is not expected")

            self.log.info("MMDrive table verified successfully")

    def run(self):
        """Run method of this test case"""
        try:

        
            self.configure_tape_library()
            
            """
            self.drive_pools = self.tape_lib_obj.get_drive_pool(self.csdb)
            self.master_pools = self.tape_lib_obj.get_master_pool(self.csdb)
            """
            
            self.drive_pools = self.ma_helper.get_drive_pool(self.csdb, self.tape_lib_obj._name)
            self.master_pools = self.ma_helper.get_master_pool(self.csdb, self.tape_lib_obj._name)

            # Cleanup
            self.cleanup()

            # Starting the DB verification to check if everything configured properly
            self.verify_mmlibrary_table(False)
            self.verify_MMDrivePool_table(False)
            self.verify_MMMasterPool_table(False)
            self.verify_MMDrives_table(False)
            self.verify_MMLibraryController_table(self.DriveControllerMA_obj.media_agent_id, False)
            self.verify_MMLibraryController_table(self.LibraryControllerMA_obj.media_agent_id, False)

            # Generating sub client content
            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.client_content, 1)
            self.is_client_directory_created = True
            self.log.info("Content generation completed")

            #while (i < len(self.MediaAgents)):

            #self.log.info("Startin the loop for DrivePool [%s]", self.drive_pools[self.MediaAgents_obj[self.MediaAgents[i]].media_agent_id)
            #Creating SP
            self.log.info("Creating storage policy with drive pool [%s]", self.drive_pools[self.DriveControllerMA_obj.media_agent_id])
            self.commcell.storage_policies.add_tape_sp(self.storage_policy, self.tape_lib_obj._name, self.DriveControllerMA,self.drive_pools[self.DriveControllerMA_obj.media_agent_id] , self.scratch_pool)
            self.log.info("Storage Policy [%s] created successfully",self.storage_policy)
            self.storage_policy_obj=self.commcell.storage_policies.get(self.storage_policy)

            #Creating backup set
            self.log.info("Creating BackupSet [%s]", self.backup_set)
            self.backup_set_obj = self._agent.backupsets.add(self.backup_set)
            self.log.info("Backup set created successfully")


            # Creating sub client
            self.log.info("Creating SubClient[%s]",self.sub_client)
            self.subclient = self.backup_set_obj.subclients.add(self.sub_client, self.storage_policy)
            self.log.info("SubClient created successfully")
            self.log.info("Adding content to subclient")
            self.subclient.content = [self.client_content]


            # Starting backup
            self.log.info("Starting backup")
            self.job_obj = self.subclient.backup("FULL")
            self.log.info("Waiting for the BACKUP job to complete. Job ID {0}".format(self.job_obj._job_id))
            self.wait_for_job_complete()

            self.log.info("Unloading the medias from drives")
            self.unload_all_drives()
            
            self.log.info("Deleting the library")
            self.commcell.tape_libraries.delete(self.tape_lib_obj._name)
            self.log.info("Library deleted successfully")

            # Starting the DB verification to check if everything cleaned properly
            self.verify_mmlibrary_table()
            self.verify_MMDrivePool_table()
            self.verify_MMMasterPool_table()
            self.verify_MMDrives_table()
            self.verify_MMLibraryController_table(self.DriveControllerMA_obj.media_agent_id)
            self.verify_MMLibraryController_table(self.LibraryControllerMA_obj.media_agent_id)

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.is_case_failed = True
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED