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

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled



class TestCase(CVTestCase):

    """Class for executing Blocklevel  RFC validation
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
            Step2, For each of the allowed scan type
                    do the following on the backupset
                Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                    do the following on the backupset
                        Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                            blocklevel and metadata collection options.
                            Step3.2, Add full data for the current run.
                            Step3.3, Run a full backup for the subclient
                                and verify it completes without failures.
                            Step3.4, Validate RFC cache and delete RFC cache
                            Step3.5, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.6, Run a File level Restore
                                and verify correct data is restored.
                            Step3.7, Validate RFC cache
                            Step3.8, Add new data for the incremental
                            Step3.9, Run an incremental backup for the subclient
                                and verify it completes without failures.
                            Step3.10, Validate RFC cache and delete RFC cache
                            Step3.11, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.12, Run a File level Restore
                                and verify correct data is restored.
                            Step3.13, Validate RFC cache
                            Step3.14, Run an synthfull for the subclient and
                                verify it completes without failures
                            Step3.15, Validate RFC cache and delete RFC cache
                            Step3.16, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.17, Run a File level Restore
                                and verify correct data is restored.
                            Step3.18, Validate RFC cache

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Windows Blocklevel  Data Protection"\
            " - Full,Incremental,Synthetic Full"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "RestorePath": None,
            "StoragePolicyName": None,
            "IndexMediaAgent":None
        }
        self.client_name = ""
        self.client_machine = None
        self.runid = ""
        self.slash_format = ""
        self.test_path = ""
        self.test_path2 = ""
        self.restore_path = ""
        self.storage_policy = None
        self.verify_dc = None
        self.wait_time = 30
        self.status = None
        self.result_string = None
        self.helper = FSHelper(TestCase)


    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs

            FSHelper.populate_tc_inputs(self)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            log.info(""" Blocklevel  RFC Validation
                    This test case does the following
                    Step1, Create backupset for this testcase if it doesn't exist.
                        Step2, For each of the allowed scan type
                                do the following on the backupset
                            Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                                do the following on the backupset
                       Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                            blocklevel and metadata collection options.
                            Step3.2, Add full data for the current run.
                            Step3.3, Run a full backup for the subclient
                                and verify it completes without failures.
                            Step3.4, Validate RFC cache and delete RFC cache
                            Step3.5, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.6, Run a File level Restore
                                and verify correct data is restored.
                            Step3.7, Validate RFC cache
                            Step3.8, Add new data for the incremental
                            Step3.9, Run an incremental backup for the subclient
                                and verify it completes without failures.
                            Step3.10, Validate RFC cache and delete RFC cache
                            Step3.11, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.12, Run a File level Restore
                                and verify correct data is restored.
                            Step3.13, Validate RFC cache
                            Step3.14, Run an synthfull for the subclient and
                                verify it completes without failures
                            Step3.15, Validate RFC cache and delete RFC cache
                            Step3.16, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.17, Run a File level Restore
                                and verify correct data is restored.
                            Step3.18, Validate RFC cache""")

            log.info("Step1, Create backupset for "
                     "this testcase if it doesn't exist")
            backupset_name = "backupset_" + self.id
            helper.create_backupset(backupset_name)

            log.info("Step2, For each of the allowed scan type Create all operations")

            for scan_type in ScanType:
                log.info(
                    "Step3, For each of the allowed index_type"
                    "Meta data colection Enabled/Not do operatons")
                for index_type in IndexEnabled:
                    if scan_type.name == 'CHANGEJOURNAL':
                        continue
                    elif scan_type.name == 'OPTIMIZED':
                        log.info(
                            "skipping optimised Scan")
                        continue

                    else:
                        # Assigning mountpoint as content based on Scan and Index type
                        if scan_type.name == 'RECURSIVE' and index_type.name == 'INDEX':
                            test_path = self.test_path2
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)
                        elif scan_type.name == 'RECURSIVE' and index_type.name == 'NOINDEX':
                            test_path = self.test_path
                            helper = self.helper
                            if test_path.endswith(slash_format):
                                test_path = str(test_path).rstrip(slash_format)

                        log.info("Running operations on Scan Type: %s", str(scan_type))
                        log.info("Running operations on Index Type: %s", str(index_type))


                        # SKip chain journal scan for Unix
                        if (self.applicable_os != 'WINDOWS'
                                and
                                scan_type.value == ScanType.CHANGEJOURNAL.value):
                            continue

                        # Skip DC if verify_dc is not provided
                        if (self.applicable_os != 'WINDOWS'
                                and scan_type.value == ScanType.OPTIMIZED.value):
                            if not self.verify_dc:
                                continue

                        log.info("Step3.1,  Create subclient for the scan type %s "
                                 "Index type if it doesn't exist.", scan_type.name)

                        subclient_name = ("subclient_%s_%s_%s" %\
                                         (self.id, scan_type.name.lower(), index_type.name.lower()))

                        subclient_content = []
                        subclient_content.append(test_path)
                        restore_path = self.restore_path
                        slash_format = self.slash_format
                        helper = self.helper
                        if restore_path.endswith(slash_format):
                            restore_path = str(restore_path).rstrip(slash_format)

                        tmp_path = ("%s%scvauto_tmp%s%s%s%s" %\
                                   (restore_path, slash_format, slash_format, subclient_name,\
                                    slash_format, str(self.runid)))

                        synthfull_tmp_path = ("%s%scvauto_tmp%s%s%s%s" % \
                                              (restore_path, slash_format, slash_format,\
                                               subclient_name, slash_format, str(self.runid)))

                        synthfull_run_path = ("%s%s%s" %(subclient_content[0], \
                                                        slash_format, str(self.runid)))
                        synthfull_datapath = synthfull_run_path

                        run_path = ("%s%s%s" %(subclient_content[0], slash_format, str(self.runid)))

                        vlr_source = ("%s%s%s" %(str(test_path), slash_format, str(self.runid)))
                        vlr_destination = ("%s%s%s" %(str(restore_path), slash_format,\
                                                      str(self.runid)))
                        full_data_path = ("%s%sfull" %(run_path, slash_format))
                        log.info("Step3.1,  Create subclient for the scan type if it doesn't exist")
                        # Create Subclient if doesnt exist
                        helper.create_subclient(
                            name=subclient_name,
                            storage_policy=storage_policy,
                            content=subclient_content,
                            scan_type=scan_type
                            )
                        # Update Subclient with blocklevel value if not set
                        log.info("Enabling BlockLevel Option")
                        helper.update_subclient(content=subclient_content,
                                                block_level_backup=1)
                        # Update Subclient with Meta data value if not set
                        if index_type.name == "INDEX":
                            log.info("Enabling Metadata collection")
                            helper.update_subclient(content=subclient_content,
                                                    createFileLevelIndex=True)
                        log.info("Step3.2, Add full data for the current run")
                        log.info("Adding data under path: %s", full_data_path)
                        self.client_machine.generate_test_data(
                            full_data_path
                        )
                        #wait for for journals to get flushed
                        if not scan_type.value == ScanType.RECURSIVE.value:
                            log.info("Waiting for journals to get flushed")
                            sleep(self.wait_time)
                        log.info(
                            "Step3.3,Run a full backup for the subclient"
                            "and verify it completes without failures")

                        job_full = helper.run_backup_verify(scan_type, "Full")[0]
                        srclist = ['blockdeviceconfig.cvf.7z', 'cumulativev2.bmp.7z',
                                   'rfc_collect_xml_', 'statefile_xml_']

                        jobid = job_full.job_id
                        full_srclist = srclist.copy()
                        full_srclist.extend(['cjinfotot.cvf', 'filtertot.cvf', str(jobid)+'_', 'bcd.xml', 'subclientproperties.cvf'])
                        log.info("Step 3.4, Validate RFC Cache paths for backup job created & delete RFC "
                                 "path post validation")

                        helper.validate_rfc_files(jobid, full_srclist, delete_rfc=True)
                        # Compare Source and Destination and check files restored.
                        log.info("Step3.5, Run a File level Restore"
                                 "and verify correct data is restored.")
                        helper.run_restore_verify(
                            slash_format,
                            full_data_path,
                            tmp_path, "full", job_full, proxy_client=self.client_name)
                        log.info("Step 3.6, Validate RFC Cache paths got recreated by Index Restore ")
                        helper.validate_rfc_files(jobid, full_srclist)
                        log.info("Step3.7, Add new data for the incremental")
                        incr_diff_data_path = run_path + slash_format + "incr_diff"
                        self.client_machine.generate_test_data(
                            incr_diff_data_path, dirs=5, files=20, file_size=50
                        )
                        log.info("Step3.8, Run an incremental backup for the subclient"
                                 "and verify it completes without failures.")
                        job_incr1 = helper.run_backup_verify(
                            scan_type, "Incremental")[0]
                        log.info("Step3.9, Run a Volume level Restore"
                                 "and verify correct data is restored.")
                        jobid = job_incr1.job_id
                        incr_srclist = srclist.copy()
                        incr_srclist.extend(['cjInfoInc.cvf', 'FilterInc.cvf', str(jobid)+'_', 'bcd.xml', 'subclientproperties.cvf'])
                        log.info("Step 3.10, Validate RFC Cache paths for backup job created & delete RFC "
                                 "path post validation")
                        helper.validate_rfc_files(jobid, incr_srclist, delete_rfc=True)
                        log.info(
                            "Step3.11, Run a File level Restore"
                            "and verify correct data is restore."
                        )
                        helper.run_restore_verify(
                            slash_format,
                            incr_diff_data_path,
                            tmp_path, "incr_diff", job_incr1, proxy_client=self.client_name)
                        log.info("Step 3.12, Validate RFC Cache paths got recreated by Index Restore ")
                        helper.validate_rfc_files(jobid, incr_srclist)
                        log.info("Step3.13, Run an synthfull for the subclient and"
                                 "verify it completes without failures.")
                        job_synth = helper.run_backup_verify(scan_type, "Synthetic_full")
                        jobid = job_synth[0].job_id
                        log.info("Step 3.14, Validate RFC Cache paths for backup job created & delete RFC "
                                 "path post validation")
                        helper.validate_rfc_files(jobid, srclist, delete_rfc=True)
                        log.info("Step3.15, Run a Volume level Restore"
                                 "and verify correct data is restored.")
                        helper.volume_level_restore(vlr_source, vlr_destination, \
                                                    client_name=self.client_name)
                        # Compare Source and Destination and check files restored.
                        log.info("Step3.16, Run a File level Restore"
                                 "and verify correct data is restored.")
                        helper.run_restore_verify(
                            slash_format,
                            synthfull_datapath,
                            synthfull_tmp_path, str(self.runid), proxy_client=self.client_name)
                        log.info("Step 3.17, Validate RFC Cache paths got recreated by Index Restore ")
                        helper.validate_rfc_files(jobid, srclist)
                        log.info("<<<<<<< Cycle 1 completed >>>>>>")
                        log.info("** %s SCAN TYPE USED", scan_type.name)
                        log.info("** %s INDEXTYPE USED", index_type.name)
                        log.info("RUN COMPLETED SUCCESFULLY")
            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
