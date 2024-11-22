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
import datetime
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.database_helper import get_csdb
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled


class TestCase(CVTestCase):
    """Class for executing MultiStream Blocklevel  Data Protection- Full,Incremental,Synthfull
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
            Step2, For each of the allowed scan type
                    do the following on the backupset
                Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                    do the following on the backupset
                        Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                            blocklevel and metadat collection options.
                            Step3.2, Add full data for the current run.
                            Step3.3, Run a full backup for the subclient
                                and verify it completes without failures.
                            Step3.4, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.5, Run a File level Restore
                                and verify correct data is restored.
                            Step3.6, Add new data for the incremental
                            Step3.7, Run an incremental backup for the subclient
                                and verify it completes without failures.
                            Step3.8, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.9, Run a File level Restore
                                and verify correct data is restored.
                            Step3.10, Run an synthfull for the subclient and
                                verify it completes without failures
                            Step3.11, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.12, Run a File level Restore
                                and verify correct data is restored.
                            Step3.13,Add new data for the incremental
                            Step3.14, Run an incremental backup after
                                synthfull 1 for the subclient and
                                verify it completes without failures.
                            Step3.15, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.16, Run a File level Restore
                                and verify correct data is restored.
                            Step3.17, Run a synthfull 2  job
                            Step3.18, Run a Volume level Restore
                                and verify correct data is restored.
                            Step3.19, Run a File level Restore
                                and verify correct data is restored.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MultiStream Blocklevel  Data Protection" \
                    " - Full,Incremental,Synthetic Full"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "RestorePath": None,
            "StoragePolicyName": None
        }
        self.client_name = ""
        self.client_machine = None
        self.runid = ""
        self.slash_format = ""
        self.test_path = ""
        self.test_path2 = ""
        self.test_path3 = ""
        self.restore_path = ""
        self.storage_policy = None
        self.verify_dc = None
        self.csdb = get_csdb()
        self.wait_time = 30
        self.verify_dc = None
        self.only_dc = None
        self.skip_classic = None
        self.no_of_streams = None
        self.helper = FSHelper(TestCase)


    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs
            self.tcinputs['VerifyDC'] = True
            self.tcinputs['SkipClassic'] = True
            self.tcinputs['OnlyDC'] = True
            self.tcinputs['FolderTimeStamp'] = False
            self.tcinputs['NoOfStreams'] = 4
            # hard link restores doesn't preserve links for multi-stream restores
            self.tcinputs['SkipLink'] = True
            FSHelper.populate_tc_inputs(self)
            self.common_utils_obj = CommonUtils(self)
            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            log.info(""" MultiStream Blocklevel  Data Protection - Full,Incrmental,Synthfull
                    This test case does the followingi
                    Step1, Create backupset for this testcase if it doesn't exist.
                        Step2, For each of the allowed scan type
                                do the following on the backupset
                            Step3, For each of the allowed index_type (Meta data colection Enabled/Not)
                                do the following on the backupset
                                    Step3.1,  Create subclient for the scan type if it doesn't exist and enable
                                        blocklevel and metadat collection options.
                                        Enable MultiStreams with backup 
                                        Step3.2, Add full data for the current run.
                                        Step3.3, Run a full backup for the subclient
                                            and verify it completes without failures.
                                        Step3.4, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.5, Run a File level Restore
                                            and verify correct data is restored using proxy.
                                        Step3.6, Add new data for the incremental
                                        Step3.7, Run an incremental backup for the subclient
                                            and verify it completes without failures.
                                        Step3.8, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.9, Run a File level Restore
                                            and verify correct data is restored using proxy.
                                        Step3.10, Run an synthfull for the subclient and
                                            verify it completes without failures
                                        Step3.11, Run a Volume level Restore
                                            and verify correct data is restored.
                                        Step3.12, Run a File level Restore
                                            and verify correct data is restored using proxy.
                                        Step 3.13, check Multi Stream Sysnthfull Run or not
                                        """)

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
                            "Skipping as  OPtimised scan as ran with Recursive scan"
                        )
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
                        if (self.applicable_os != 'WINDOWS'
                                and
                                scan_type.value == ScanType.CHANGEJOURNAL.value):
                            continue
                        # Skip DC if verify_dc is not provided
                        if scan_type.value == ScanType.OPTIMIZED.value:
                            if not self.verify_dc:
                                continue
                        log.info("Step3.1,  Create subclient for the scan type %s "
                                 "Index type if it doesn't exist.", scan_type.name)

                        subclient_name = ("subclient_%s_%s_%s" % \
                                          (self.id, scan_type.name.lower(), index_type.name.lower()))

                        subclient_content = []
                        subclient_content.append(test_path)
                        restore_path = self.restore_path
                        slash_format = self.slash_format
                        helper = self.helper
                        if restore_path.endswith(slash_format):
                            restore_path = str(restore_path).rstrip(slash_format)

                        tmp_path = ("%s%scvauto_tmp%s%s%s%s" % \
                                    (restore_path, slash_format, slash_format, subclient_name, \
                                     slash_format, str(self.runid)))

                        synthfull_tmp_path = ("%s%scvauto_tmp%s%s%s%s" % \
                                              (restore_path, slash_format, slash_format, \
                                               subclient_name, slash_format, str(self.runid)))

                        synthfull_run_path = ("%s%s%s" % (subclient_content[0], \
                                                          slash_format, str(self.runid)))
                        synthfull_datapath = synthfull_run_path

                        run_path = ("%s%s%s" % (subclient_content[0], slash_format, str(self.runid)))

                        vlr_source = ("%s%s" % (str(test_path), slash_format))
                        vlr_destination = ("%s%s" % (str(restore_path), slash_format))
                        full_data_path = ("%s%sfull" % (run_path, slash_format))

                        log.info("Step3.1,  Create subclient for the scan type if it doesn't exist")
                        log.info("Running on Existing subclient forever cycle")
                        # Create Subclient if doesnt exist

                        helper.create_subclient(
                            name=subclient_name,
                            storage_policy=storage_policy,
                            content=subclient_content,
                            scan_type=scan_type,
                            data_readers=self.no_of_streams,
                            allow_multiple_readers=self.no_of_streams > 1
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

                        helper.update_subclient(content=subclient_content,
                                                data_readers=4,
                                                allow_multiple_readers=True)

                        log.info("Step3.2, Add full data for the current run")

                        log.info("Adding data under path: %s", full_data_path)
                        self.client_machine.generate_test_data(
                            full_data_path, dirs=3, files=50, file_size=50
                        )
                        # wait for for journals to get flushed
                        if not scan_type.value == ScanType.RECURSIVE.value:
                            log.info("Waiting for journals to get flushed")
                            sleep(self.wait_time)

                        log.info(
                            "Step3.3,Run a full backup for the subclient"
                            "and verify it completes without failures")

                        job_full = helper.run_backup_verify(scan_type, "Full")[0]
                        log.info(
                            "Step3.4, Run a Volume level Restore"
                            "and verify correct data is restored.")
                        helper.volume_level_restore(vlr_source, vlr_destination,
                                                    client_name=self.client_name,
                                                    no_of_streams=self.no_of_streams,
                                                    cleanup=False)
                        # Compare Source and Destination and check files restored.
                        log.info("Step3.5, Run a File level Restore"
                                 "and verify correct data is restored using proxy")

                        helper.run_restore_verify(
                            slash_format,
                            full_data_path,
                            tmp_path, "full",
                            proxy_client=self.client_name,
                            no_of_streams=self.no_of_streams)

                        log.info("Step3.6, Add new data for the incremental")
                        incr_diff1_data_path = run_path + slash_format + "incr_diff1" + slash_format
                        incr_diff_data_path_bigdata = incr_diff1_data_path + str(
                            datetime.datetime.now().strftime("%y-%m-%d-%H-%M") + "_1")
                        self.client_machine.generate_test_data(
                            incr_diff_data_path_bigdata, dirs=3, files=20, file_size=50
                        )

                        log.info("Step3.7, Run an incremental backup for the subclient"
                                 "and verify it completes without failures.")
                        job_incr1 = helper.run_backup_verify(
                            scan_type, "Incremental")[0]
                        log.info("Step3.8, Run a Volume level Restore"
                                 "and verify correct data is restored.")
                        helper.volume_level_restore(vlr_source, vlr_destination,
                                                    client_name=self.client_name,
                                                    no_of_streams=self.no_of_streams,
                                                    cleanup=False)
                        # Compare Source and Destination and check files restored.

                        log.info(
                            "Step3.9, Run a File level Restore"
                            "and verify correct data is restore."
                        )
                        incr_diff1_data_path = run_path + slash_format + "incr_diff1"
                        helper.run_restore_verify(
                            slash_format,
                            incr_diff1_data_path,
                            tmp_path, "incr_diff1",
                            job_incr1,
                            proxy_client=self.client_name,
                            no_of_streams=self.no_of_streams)

                        log.info("Step3.10, Run an synthfull for the subclient and"
                                 "verify it completes without failures.")
                        # helper.run_backup_verify(scan_type, "Synthetic_full")

                        multi_stream_sfull = self.common_utils_obj.subclient_backup(
                            self.subclient,
                            backup_type="Synthetic_full",
                            wait=False,
                            advanced_options={
                                'use_multi_stream': True,
                                'use_maximum_streams': False,
                                'max_number_of_streams': 2
                            }
                        )

                        log.info(multi_stream_sfull)
                        self.log.info(
                            "Waiting for completion of %s backup with Job ID: %s", multi_stream_sfull.job_type, str(
                                multi_stream_sfull.job_id))

                        if not multi_stream_sfull.wait_for_completion():
                            raise Exception(
                                "Failed to run {0} backup {1} with error: {2}".format(
                                    multi_stream_sfull.job_type, str(multi_stream_sfull.job_id),
                                    multi_stream_sfull.delay_reason
                                )
                            )

                        if not multi_stream_sfull.status.lower() == "completed":
                            raise Exception(
                                "{0} job {1}status is not Completed, job has status: {2}".format(
                                    multi_stream_sfull.job_type, str(
                                        multi_stream_sfull.job_id), multi_stream_sfull.status))

                        self.log.info("Successfully finished %s job %s", multi_stream_sfull.job_type,
                                      str(multi_stream_sfull.job_id))

                        query = "select numStreams from JMBkpStats where jobId  = '{}'" \
                            .format(multi_stream_sfull.job_id)
                        self.csdb.execute(query)
                        _results1 = self.csdb.fetch_all_rows()
                        streams_ran = int(_results1[0][0])
                        if streams_ran > 2:
                            self.log.info("Job Ran as MultiStream backup with streams {}".format(streams_ran))
                        else:
                            self.log.info("Synthfull ob Failed to as MultiStream backup streams ran  {}"
                                          .format(streams_ran))
                            raise Exception(
                                "Synthfull ob Failed to as MultiStream backup with streams {}"
                                .format(streams_ran)
                            )

                        log.info("Step3.11, Run a Volume level Restore"
                                 "and verify correct data is restored.")
                        helper.volume_level_restore(vlr_source, vlr_destination,
                                                    client_name=self.client_name,
                                                    no_of_streams=self.no_of_streams,
                                                    cleanup=False
                                                    )
                        # Compare Source and Destination and check files restored.

                        log.info("Step3.12, Run a File level Restore"
                                 "and verify correct data is restored using proxy")
                        helper.run_restore_verify(
                            slash_format,
                            synthfull_datapath,
                            synthfull_tmp_path,
                            str(self.runid),
                            proxy_client=self.client_name,
                            no_of_streams=self.no_of_streams
                        )

                        log.info("<<<<<<< Cycle 1 completed >>>>>>")
                        log.info("** %s SCAN TYPE USED", scan_type.name)
                        log.info("** %s INDEXTYPE USED", index_type.name)
                        log.info("RUN COMPLETED SUCCESFULLY")

                        self.client_machine.remove_directory(tmp_path)
            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
