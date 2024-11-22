import time
from base64 import b64encode
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import CommitCondition, FSHelper
from AutomationUtils import logger, constants
import traceback


class TestCase(CVTestCase):
    """
    Class for executing CIFS Network share client backup and restore cases.
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Network Share Client NFS Acceptance Case"
        self.impersonate_user = None
        self.impersonate_password = None
        self.username = None
        self.password = None
        self.data_access_nodes = None
        self.restore_location = None
        self.client_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.mount_drive_letter = None
        self.no_of_streams = None
        self.only_incr = None
        self.tcinputs = {
            "ClientName": None,
            "SubclientName": None,
            "BackupsetName": None,
            "DataAccessNodes": None,
            "TestPath": None,
            "RestoreLocation": None,
            "MountDriveLetter": None
        }

    def setup(self):
        """Setup function for test case execution"""

        self.log.info("Executing NetworkShareClient CIFS Testcase")
        try:
            self.helper = FSHelper(self)
        except Exception as exp:
            self.log.info(traceback.print_exc())
        self.data_access_nodes = self.tcinputs['DataAccessNodes']
        self.restore_location = self.tcinputs['RestoreLocation']
        self.client_name = self.tcinputs['ClientName']
        self.subclient_name = self.tcinputs['SubclientName']
        self.backupset_name = self.tcinputs['BackupsetName']
        self.temp_mount_path = self.tcinputs['MountDriveLetter']
        self.client_machine = Machine(self.data_access_nodes[0], self.commcell)

    def run(self):
        """Run function for test case execution"""

        try:
            self.client = self.commcell.clients.get(self.client_name)
            self.agent = self.client.agents.get('Linux file system')
            self.backupset = self.agent.backupsets.get(self.backupset_name)
            self.subclient = self.backupset.subclients.get(self.subclient_name)
            self.log.info("Tests Running on Pre Configured Network share client: " +self.client_name)
            self.log.info("Tests Running on NFS subclient client: " + self.subclient_name)
            sccontent_leaf = self.subclient.content[0].split("/")[-1]
            self.helper.populate_tc_inputs(self, mandatory=False)
            rest_path = self.client_machine.join_path(self.test_path,
                                                      f'{self.id}_tmp_restore')
            self.server, self.share = self.test_path.split(":")
            self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)
            self.client_machine.clear_folder_content(self.temp_mount_path)
            self.client_machine.unmount_path(self.temp_mount_path)
            self.helper.generate_data_on_share(self.client_machine, self.test_path, self.temp_mount_path)

            self.subclient.data_readers = self.no_of_streams
            self.log.info("*** streams enabled on Subclient***"+str(self.no_of_streams))
            self.subclient.allow_multiple_readers = self.no_of_streams > 1
            self.log.info ("****Enabled Multi readers on Subclient****")

            #Full Backup
            self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)
            job = self.helper.run_backup_verify(backup_level="Full")
            #Generate Data for incremental
            self.helper.generate_data_on_share(self.client_machine, self.test_path, self.temp_mount_path, for_incr=True)

            self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)

            job = self.helper.run_backup_verify(backup_level="Incremental")

            #Creating new folder for out of place restore
            self.client_machine.create_directory(directory_name=self.restore_location, force_create=True)
            self.client_machine.create_directory(directory_name=self.restore_location+"/r1", force_create=True)

            #Out of place restore and checksum verification
            job = self.helper.restore_out_of_place(paths=self.subclient.content,
                                                 destination_path=self.restore_location+"/r1",
                                                 client=self.data_access_nodes[0],
                                                 proxy_client=self.data_access_nodes[0],
                                                 wait_to_complete= False)
            # time.sleep(100)
            job_status = job.wait_for_completion()
            # if not job.status.lower() == "completed" :
            if "completed" in job.status.lower():
                self.log.info("Job is successful and completed")
            else:
                raise Exception(
                    "Job status is not Completed, job has status: {0}".format(
                        job.status))

            self.compare_data_nfs(path1=self.temp_mount_path, path2=self.restore_location+"/r1/"+sccontent_leaf)
            if self.only_incr:
                return

            #Synthetic Full Backup job
            synthfulljob = self.helper.run_backup_verify(backup_level="Synthetic_Full")

            #Deleting some files
            self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)
            for i in range(1, 11):
                dir_path = self.client_machine.join_path(self.temp_mount_path, str(self.id), "full", "dir1", "regular", "regularfile"+str(i))
                self.log.info("Deleting " + dir_path)
                self.client_machine.delete_file(dir_path)
            # self.client_machine.unmount_path(self.temp_mount_path)
            self.helper.run_backup_verify(backup_level="Incremental")
            #Out of place restore and checksum verification

            self.client_machine.create_directory(directory_name=self.restore_location+"/r2", force_create=True)
            job = self.helper.restore_out_of_place(paths=self.subclient.content,
                                             destination_path=self.restore_location+"/r2",
                                             client=self.data_access_nodes[0],
                                            proxy_client=self.data_access_nodes[0],
                                             wait_to_complete=False)
            job_status = job.wait_for_completion()
            if "completed" in job.status.lower():
                self.log.info("Job is successful and completed")
            else:
                raise Exception(
                    "Job status is not Completed, job has status: {0}".format(
                        job.status))
            # self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)
            self.compare_data_nfs(path1=self.temp_mount_path, path2=self.restore_location+"/r2/"+sccontent_leaf)

            if self.client_machine.is_path_mounted(self.temp_mount_path):
                self.client_machine.unmount_path(self.temp_mount_path)
            self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)
            self.client_machine.clear_folder_content(self.temp_mount_path)
            #In place restore and checksum verification with first out of place restore data.
            job = self.helper.restore_in_place(paths=self.subclient.content,
                                               proxy_client=self.data_access_nodes[0],
                                               wait_to_complete=False)
            job_status = job.wait_for_completion()
            if "completed" in job.status.lower():
                self.log.info("Job is successful and completed")
            else:
                raise Exception(
                    "Job status is not Completed, job has status: {0}".format(
                        job.status))
            self.compare_data_nfs(path1=self.temp_mount_path, path2=self.restore_location+"/r2/"+sccontent_leaf)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED


        except Exception as exp:
            self.log.info(traceback.print_exc())
            if self.client_machine.is_path_mounted(self.temp_mount_path):
                self.client_machine.unmount_path(self.temp_mount_path)
            self.client_machine.clear_folder_content(self.restore_location)
            self.status = 'FAILED'
            self.log.error('Failed to execute test case with error: %s', str(exp))

    def tear_down(self):
        """Tear Down function for the test case"""
        try:
            if self.client_machine:
                self.client_machine.disconnect()


        except Exception as exp:
            self.log.error('Failed to execute teardown with error: %s', str(exp))

    def verify_backup_logs(self,job, incremental=False, inc_after_synthfull=False):
        logs = self.client_machine.get_logs_for_job_from_file(job_id=job[0].job_id,
                                                              log_file_name="FileScan.log",
                                                              search_term="CumulativeScanModeAndReason=CLASSIC+UNC")
        if logs:
            self.log.info("CumulativeScanModeAndReason=CLASSIC+UNC was found in FileScan.log")
        else:
            self.log.info("CumulativeScanModeAndReason=CLASSIC+UNC was not found in FileScan.log")
            raise Exception("CumulativeScanModeAndReason=CLASSIC+UNC was not found in FileScan.log")
        if incremental:
            logs = self.client_machine.get_logs_for_job_from_file(job_id=job[0].job_id,
                                                                  log_file_name="FileScan.log",
                                                                  search_term="BackupType=[2 (Incremental)]")
            if logs:
                self.log.info("BackupType=[2 (Incremental)] was found in FileScan.log")
            else:
                self.log.info("BackupType=[2 (Incremental)] was not found in FileScan.log")
                raise Exception("BackupType=[2 (Incremental)] was not found in FileScan.log")
        if inc_after_synthfull:
            logs = self.client_machine.get_logs_for_job_from_file(job_id=job[0].job_id,
                                                                  log_file_name="FileScan.log",
                                                                  search_term="Sending browse request to generate TrueUp DirChange")
            if logs:
                self.log.info("Sending browse request to generate TrueUp DirChange was found in FileScan.log")
            else:
                self.log.info("Sending browse request to generate TrueUp DirChange was not found in FileScan.log")
                raise Exception("Sending browse request to generate TrueUp DirChange was not found in FileScan.log")

    def compare_data_nfs(self, path2, path1):
        """Compares the checksum of two data-paths
            Arguments:
                path1   : path of first data source

                path2   : path of 2nd data source

            Raises Exception if checksum do not matches
        """
        self.log.info("First Path is .. %s", str(path1))
        self.log.info("Second Path is .. %s", str(path2))
        # self.helper.mount_cifs_share_on_drive(self.client_machine, self.subclient.content[0], self.impersonate_user,
        #                                       self.impersonate_password, drive_letter=self.mount_drive_letter)
        if self.client_machine.is_path_mounted(self.temp_mount_path):
            self.client_machine.unmount_path(self.temp_mount_path)
        self.client_machine.mount_nfs_share(self.temp_mount_path, self.server, self.share)
        result = self.client_machine.compare_checksum(path1, path2)
        self.client_machine.unmount_path(self.temp_mount_path)
        if not result[0]:
            self.log.info("Data at two paths does not match")
            raise Exception("Data at two paths does not match")
        else:
            self.log.info("***Content matched comparision succesful***")

