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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Remote File Cache
        This test case does the following
                Step2.1, Create sub client for the scan type if it doesn't exist.
                Step2.2, Add full data for the current run.
                Step2.3, Run a full backup for the sub client
                            and verify it completes without failures.
                Step2.4, Go to job results on the client and delete CJinfoTot.
                Step2.5, Add new data for the incremental
                Step2.7, Run an incremental backup for the subclient
                            and verify it completes without failures.
                Step2.8, Run a restore of the incremental backup data
                            and verify correct data is restored.
                Step2.9, Run a find operation for the incremental job
                            and verify the returned results.
                Step2.10, Delete the CJinfo file from the incremental.
                Step2.11, Run a synthfull job
                Step2.12, Run an incremental job and make sure it is scan marking
                        complete
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection"\
            " - Remote File Cache"
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.should_wait = None
        self.is_client_big_data_apps = None
        self.is_client_network_share = None
        self.master_node = None
        self.data_access_nodes = None
        self.no_of_streams = None
        self.instance_name = None
        self.cleanup_run = None
        self.backupset_name = None
        self.jobID = None

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            machine = self.client_machine
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy
            self.log.info("RFC for file system")
            if self.is_client_big_data_apps:
                self.log.info("Step1, Create Instance for "
                         "this testcase if it doesn't exist")
                instance_name = "Instance_" + self.id
                helper.create_instance(instance_name, delete=self.cleanup_run)
                self.instance_name = instance_name
            else:
                self.log.info("Step1, Create backupset for "
                         "this testcase if it doesn't exist")
                self.backupset_name  = "backupset_" + self.id
                helper.create_backupset(self.backupset_name, delete=self.cleanup_run)
            self.log.info("Step2, Executing steps for all DC scan")
            scan_type = ScanType.OPTIMIZED
            self.log.info("**STARTING RUN FOR " + scan_type.name + " SCAN**")
            self.log.info("Step2.1,  Create subclient for the scan type "
                     + scan_type.name + " if it doesn't exist.")
            subclient_name = ("subclient_"
                              + self.id
                              + "_"
                              + scan_type.name.lower())
            subclient_content = []
            subclient_content.append(test_path
                                     + slash_format
                                     + subclient_name)
            
            tmp_path = (
                test_path
                + slash_format
                + 'cvauto_tmp'
                + slash_format
                + subclient_name
                + slash_format
                + str(self.runid)
            )
            run_path = (subclient_content[0]
                        + slash_format
                        + str(self.runid))
            full_data_path = run_path + slash_format + "full"
            
            helper.create_subclient(name=subclient_name,
                storage_policy=storage_policy,
                content=subclient_content,
                scan_type=scan_type,
                data_readers = self.no_of_streams,
                allow_multiple_readers = self.no_of_streams > 1,
                data_access_nodes=self.data_access_nodes,
                delete=self.cleanup_run)
            self.log.info("Step2.2,  Add full data for the current run.")
            self.log.info("Adding data under path:" + full_data_path)
            machine.generate_test_data(
                full_data_path,
                acls=self.acls,
                unicode=self.unicode,
                xattr=self.xattr,
                files=5,
                file_size=20,
                long_path=self.long_path,
                problematic=self.problematic
            )
                        
            self.log.info("Step2.3,  Run a full backup for the subclient "
                     "and verify it completes without failures.")
            job_full = helper.run_backup_verify(scan_type, "Full")[0]
            self.log.info("Getting subclient job results")
            cjInfoPath = list(helper.subclient_job_results_directory.values())[0] + self.slash_format+'CjinfoTot.cvf'
            self.log.info(cjInfoPath)
            machine.delete_file(cjInfoPath)
            self.log.info("File has been deleted")
            helper.run_restore_verify(
                    slash_format,
                    full_data_path,
                    tmp_path, "full", job_full,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams)
            self.log.info("Step2.4,  Run a find operation for the full job"
                     " and verify the returned results.")
            self.log.info("Subclient Content is",subclient_content[0])

            self.log.info("Step2.6,  Add new data for the incremental")
            incr_diff_data_path = run_path + slash_format + "incr_diff"
            helper.add_new_data_incr(
                incr_diff_data_path,
                slash_format,
                dirs=1,
                files=5,
                file_size=20,
                levels=1,
                hlinks=False,
                slinks=False,
                sparse=False,
                sparse_hole_size=False)
        
            self.log.info("Incremental path is",incr_diff_data_path)

            self.log.info("Step2.7,  Run an incremental job for the subclient"
                     " and verify it completes without failures.")
            job_incr1 = helper.run_backup_verify(
                scan_type, "Incremental")[0]
                
            self.log.info("Deleting RFC from index cache as well")
            source_list=['CJinfoInc.cvf']
            self.helper.validate_rfc_files(job_incr1.job_id,source_list,delete_rfc=True) 
            self.log.info("Deletion for RFC from index done")  
            self.log.info("Executing code for checking CJinfo download")
            search_term = "Change Journal info file was downloaded; Checking again"
            log_line = self.helper.get_logs_for_job_from_file(job_incr1.job_id, "Filescan.log", search_term)
            self.log.info("Incremental job id is",job_incr1.job_id)
            if log_line:
                    self.log.info("Change Journal info file was downloaded; Checking again")
            else:
                raise Exception("Test case failed because CJinfo was not downloaded")

            self.log.info(
                "Step2.8,  Run a restore of the incremental backup data"
                " and verify correct data is restored."
            )
            helper.run_restore_verify(
                slash_format,
                incr_diff_data_path,
                tmp_path, "incr_diff", job_incr1,
                destination_instance=self.instance_name)

            self.log.info("Getting subclient job results")            
            cjInfoPath = list(helper.subclient_job_results_directory.values())[0] + self.slash_format + 'CjinfoInc.cvf'
            self.log.info(cjInfoPath)
            machine.delete_file(cjInfoPath)
            self.log.info("File has been deleted")
            
            self.log.info("Step2.9, Run a synthfull job")
            helper.run_backup_verify(scan_type, "Synthetic_full")
            
            incr2=helper.run_backup_verify(scan_type, "Incremental",scan_marking=True)[0]
            
            if incr2:
                self.log.info(
                "Step2.10,  Scan marking job completed successfully"
            )
            else:
                raise Exception("Test case failed because we expect scan marking job")
            
            
            machine.remove_directory(tmp_path)

        # delete backupset/instance if clean up is specified
            if self.cleanup_run:
                if self.is_client_big_data_apps:
                    self.agent.instances.delete(self.instance_name)
                else:
                    self.instance.backupsets.delete(self.backupset_name)
                    self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
