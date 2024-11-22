# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------



""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper
class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental,Differential
        This test case does the following
        Step 1 : Create backupset for this testcase if it doesn't exist.
                Delete the backupset if exists
        Step 2 :, For each of the allowed scan type
                    do the following on the backupset
        Step 3 : Create subclient for each scan type
        Step 4 : Add full data for the current run.
        Step 5 : Run a full backup for the subclient
                 and verify it completes without failures.
        Step 6 : Run a restore of the full backup data
                 and verify correct data is restored.
        Step 7 : Run a find operation for the full job
                 and verify the returned results.
        Step 8 : Run an incremental and synthfull       
        Step 9 : Add new data for the incremental -
                 we are going to rename set of files in sc.
                 This is to verify if trueup ran and picked up items
        Step 10 :Verify if trueup ran a picked item
                 by calling ValidateTrueup for fshelper
                 Make sure the renamed items are picked by
                 getting trueup from validate helper
        Step 11 :Run an OOP restore and verify the incremental job
        Step 12 :Add new content and run an incremental job
                Ask validatetrueup if trueup ran for this job
        Step 13 :Run a synthfull job
        Step 14 :Call rename function again and ran an incremental job.
                we are going to call rename to rename set of files in the
                 subclient content.
        Step 15 :This is to verify if trueup ran and picked up items,
                ask the Validatetrueup for 38 and logs for -tjc
        Step 16 :Run an OOP restore and verify the incremental job

        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection"\
            " - Synthetic Full - Trueup"
        #self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.acls = None
        self.unicode = None
        self.xattr = None
        self.long_path = None
        self.problematic = None
        self.should_wait = None
        self.is_client_big_data_apps = None
        self.is_client_network_share = None
        self.master_node = None
        self.data_access_nodes = None
        self.no_of_streams = None
        self.instance_name = None
        self.tmp_path = None
        self.slash_format = None
        self.runid = None
        self.subclient_name = None
        self.slash_format = None
        self.only_dc = None

    def run(self):
        """Main function for test case execution"""
        log = self.log
        

        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)
            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy
            log.info("The test data path is %s", test_path)
            log.info("Step1,Create backup set,"
                     " If backup set already exists delete and recreate")
            backupset_name = "backupset_{0}".format(self.id)
            helper.create_backupset(backupset_name, delete=True)
            log.info("Step2, Executing steps for all the allowed scan type")
            for scan_type in ScanType:
                #Skip change journal scan for Unix
                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.CHANGEJOURNAL.value):
                        continue
                if (self.applicable_os == 'WINDOWS'
                        and
                        scan_type.value == ScanType.CHANGEJOURNAL.value):
                    if self.only_dc:
                        self.log.info("ONLY DC is Selected so skipped CJ ")
                        continue
                # Skip DC if verify_dc is not provided
                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.OPTIMIZED.value):
                    if not self.verify_dc:
                        continue

                if (scan_type.value == ScanType.RECURSIVE.value):
                    if (self.only_dc):
                            self.log.info("ONLY DC is selected skipping recursive")
                            continue

                log.info("**STARTING RUN FOR %s SCAN**", scan_type.name)
                log.info(" Step2.1,Create sub client for the scan type "
                         "%s if it doesn't exists", scan_type.name)
                subclient_name = "subclient_{0}_{1}".format(
                    self.id, scan_type.name.lower())
                log.info("Scan type being used is %s", scan_type)
                subclient_content=[]
                subclient_content.append("{0}{1}{2}".format(test_path,
                                         slash_format,
                                         subclient_name))
                log.info(subclient_content)
                tmp_path = "{0}{1}cvauto_tmp{1}{2}{1}{3}".format(
                                test_path,
                                slash_format, self.subclient_name
                                , str(self.runid))
                log.info("tmp_path is %s", tmp_path)
                run_path = "{0}{1}{2}".format(subclient_content[0]
                                       , self.slash_format
                                       , str(self.runid))
                full_data_path = "{0}{1}full".format(run_path, slash_format)
                log.info("Full data path %s ", full_data_path)
                helper.create_subclient(name=subclient_name,
                                        storage_policy=storage_policy,
                                        content=subclient_content,
                                        scan_type=scan_type)
                log.info("Step2.3,  Add full data for the current run.")
                log.info("Adding data under path: %s", full_data_path)
                self.client_machine.generate_test_data(
                    full_data_path,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr
                    )
                log.info("scantype used is %s", str(scan_type))
                job_full = helper.run_backup_verify(scan_type, "Full")[0]
                log.info("validate Trueup function called.")
                retval = helper.validate_trueup(job_full)
                if retval:
                    log.info("True up Ran for Full Job. Failing the case.")
                    raise Exception("Failing test case")
                log.info("True up did not run for Full job as expected.")
                
                if self.applicable_os == 'WINDOWS':
                    self.client_machine.modify_test_data(full_data_path,
                                                     acls=True,rename=True)
                else:
                    self.client_machine.modify_test_data(full_data_path,
                                                     rename=True) 
                    
                
                
                incr_job1 = helper.run_backup_verify(
                    scan_type, "Incremental")[0]
                retval = helper.validate_trueup(incr_job1)
                if retval:
                    raise Exception("Trueup ran in incremental after FULL")
                log.info("Trueup didnt run as expected")
                incr_job2 = helper.run_backup_verify(
                    scan_type, "Incremental", scan_marking=True)[0]
                retval = helper.validate_trueup(incr_job2)
                if retval:
                    raise Exception("Trueup ran for second incremental")
                log.info("Trueup didnt run as expected for scan marking")
                synthfull1 = helper.run_backup_verify(scan_type, "Synthetic_full")[0]
                retval = helper.validate_trueup(synthfull1)
                if retval:
                    raise Exception("Trueup ran for  synthfull")
                log.info("Trueup didnt run as expected for synthfull")
                log.info("Step2.4,  Run an incremental job for the subclient"
                         " and verify it completes without failures.")
                job_incr3 = helper.run_backup_verify(
                    scan_type, "Incremental")[0]
                    
                    
                if self.applicable_os == 'WINDOWS':
                    log.info("Search for -tjc in DC and CJ and recursive")
                    search_term = "Next phase parameters: \[ -CLN"
                    self.log.info(search_term)
                    log_line = self.helper.get_logs_for_job_from_file(
                    job_incr3.job_id, "Filescan.log", search_term)
                    log.info(log_line)  
                    if log_line.find('-TJ') == -1:
                            raise Exception("Trueup should not pick for DC/CJ/Recursive")
                            log.info("Trueup didnt pick any items")
                    retval = helper.validate_trueup(job_incr3)
                    if retval:
                        self.log.info("Trueup ran here")
                    else:
                            raise Exception("Trueup needs to run but didn't")
                
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    cleanup=True,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams
                    )
                    
                full_incr_path1 = "{0}cre".format(full_data_path)
                full_incr_path2 = "{0}cre2".format(full_data_path)
                self.client_machine.create_directory(full_incr_path1)
                self.client_machine.create_directory(full_incr_path2)
                self.client_machine.generate_test_data(
                    full_incr_path1,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr
                    )
                self.client_machine.generate_test_data(
                    full_incr_path2,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr
                    )
                job_incr4 = helper.run_backup_verify(
                    scan_type, "Incremental", scan_marking=False)[0]
                retval = helper.validate_trueup(job_incr4)
                if retval:
                    raise Exception("Trueup ran when not needed")
                log.info("Trueup didnt run as expected")
                log.info("Folder creation is successful")
                log.info("Renaming is going to happen here for the folders")
                full_incr_path_to_rename = "{0}123".format(full_incr_path1)
                self.client_machine.rename_file_or_folder(
                    full_incr_path1, full_incr_path_to_rename)
                log.info("path to rename is %s", full_incr_path_to_rename)
                self.client_machine.rename_file_or_folder(
                    full_incr_path2, full_incr_path1)
                log.info("full_incr_path1 is %s", full_incr_path1)
                self.client_machine.rename_file_or_folder(
                    full_incr_path_to_rename, full_incr_path2)
                log.info("full_incr_path2 is %s", full_incr_path2)
                log.info("Rename folder 1 to 2 and 2 to 1 is successful")
                log.info("Step2.6, Run a synthfull job")
                synthfull2 = helper.run_backup_verify(scan_type, "Synthetic_full")[0]
                retval = helper.validate_trueup(synthfull2)
                if retval:
                    raise Exception("Trueup ran for synthfull")
                log.info("Trueup didnt run as expected for synthfull")
                log.info("Step2.7,  Run an incremental job for the subclient"
                         " and verify it completes without failures.")
                log.info("Step2.7, Run the incremental after synthfull job")
                job_incr5 = helper.run_backup_verify(
                    scan_type, "Incremental")[0]              
                retval = helper.validate_trueup(job_incr5)
                if retval:
                    self.log.info("Trueup ran successfully ")
                else:
                    raise Exception("Trueup did not run as expected") 
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    cleanup=True,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams
                    )

                self.client_machine.remove_directory(tmp_path)
                self.client_machine.remove_directory(run_path)
                log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
