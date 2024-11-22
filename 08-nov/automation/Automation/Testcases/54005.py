# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=broad-except

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
        Hadoop Data Protection - Full,Incremental,Differential,Synthfull
        This test case does the following
        Step1,  Create instance for this testcase if it doesn't exist.
        Step2,  Create subclient for this testcase if it doesn't exist.
        Step3,  Add full data for the current run.
        Step4,  Run a full backup for the subclient and verify it completes without failures.
        Step5,  Run a restore of the full backup data and verify correct data is restored.
        Step6,  Run a find operation for the full job and verify the returned results.
        Step7,  Add new data for the incremental
        Step8,  Run an incremental backup for the subclient and verify it completes without failures.
        Step9,  Run a restore of the incremental backup data and verify correct data is restored.
        Step10, Run a find operation for the incremental job and verify the returned results.
        Step11, Perform all modifications on the existing data.
        Step12, Run an incremental backup for the subclient and verify it completes without failures.
        Step13, Run a restore of the incremental backup data and verify correct data is restored.
        Step14, Run a find operation for the incremental job and verify the returned results.
        Step15, Add new data for the differential
        Step16, Run a differential backup for the subclient and verify it completes without failures.
        Step17, Run a restore of the differential backup data and verify correct data is restored.
        Step18, Run a find operation for the differential job and verify the returned results.
        Step19, Add new data for the incremental
        Step20, Run a synthfull job
        Step21, Run an incremental backup after synthfull for the subclient and verify it completes without failures.
        Step22, Run a restore of the incremental backup data and verify correct data is restored.
        Step23, Run a find operation for the incremental job and verify the returned results.
        Step24, Perform all modifications on the existing data.
        Step25, Run a synthfull job
        Step26, Run an incremental backup after synthfull for the subclient and verify it completes without failures.
        Step27, Run a restore of the incremental backup data and verify correct data is restored.
        Step28, Run a find operation for the incremental job and verify the returned results.
        Step29, Run a restore of the complete subclient data and verify correct data is restored.
        Step30, Run a find operation for the entire subclient and verify the returned results.
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Hadoop Data Protection - Full,Incremental,Differential,Synthfull"
        self.tcinputs = {"TestPath": None}
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = ''
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.acls = None
        self.unicode = None
        self.xattr = None
        self.long_path = None
        self.should_wait = None
        self.is_client_big_data_apps = None
        self.master_node = None
        self.data_access_nodes = None
        self.no_of_streams = None
        self.instance_name = None
        self.backupset_name = None
        self.runid = 0
        self.cleanup_run = None
        self.run_path = None
        self.tmp_path = None
        self.backup_job = None
        self.scan_type = ScanType.RECURSIVE

    def setup(self):
        """Setup function of this test case"""
        # Initialize test case inputs
        FSHelper.populate_tc_inputs(self, mandatory=False)
        self.should_wait = False
        test_path = self.test_path
        slash_format = self.slash_format
        if test_path.endswith(slash_format):
            test_path = str(test_path).rstrip(slash_format)

        self.log.info("""Hadoop Data Protection - Full,Incremental,Differential,Synthfull
        This test case does the following
        Step1,  Create instance for this testcase if it doesn't exist.
        Step2,  Create subclient for this testcase if it doesn't exist.
        Step3,  Add full data for the current run.
        Step4,  Run a full backup for the subclient and verify it completes without failures.
        Step5,  Run a restore of the full backup data and verify correct data is restored.
        Step6,  Run a find operation for the full job and verify the returned results.
        Step7,  Add new data for the incremental
        Step8,  Run an incremental backup for the subclient and verify it completes without failures.
        Step9,  Run a restore of the incremental backup data and verify correct data is restored.
        Step10, Run a find operation for the incremental job and verify the returned results.
        Step11, Perform all modifications on the existing data.
        Step12, Run an incremental backup for the subclient and verify it completes without failures.
        Step13, Run a restore of the incremental backup data and verify correct data is restored.
        Step14, Run a find operation for the incremental job and verify the returned results.
        Step15, Add new data for the differential
        Step16, Run a differential backup for the subclient and verify it completes without failures.
        Step17, Run a restore of the differential backup data and verify correct data is restored.
        Step18, Run a find operation for the differential job and verify the returned results.
        Step19, Add new data for the incremental
        Step20, Run a synthfull job
        Step21, Run an incremental backup after synthfull for the subclient and verify it completes without failures.
        Step22, Run a restore of the incremental backup data and verify correct data is restored.
        Step23, Run a find operation for the incremental job and verify the returned results.
        Step24, Perform all modifications on the existing data.
        Step25, Run a synthfull job
        Step26, Run an incremental backup after synthfull for the subclient and verify it completes without failures.
        Step27, Run a restore of the incremental backup data and verify correct data is restored.
        Step28, Run a find operation for the incremental job and verify the returned results.
        Step29, Run a restore of the complete subclient data and verify correct data is restored.
        Step30, Run a find operation for the entire subclient and verify the returned results.
        """)

        self.log.info("Create Instance for this testcase if it doesn't exist")
        self.instance_name = f"Instance_{self.id}_recursive"
        self.helper.create_instance(self.instance_name, delete=self.cleanup_run)

        self.log.info("Create subclient for this testcase if it doesn't exist.")
        subclient_name = f"subclient_{self.id}"
        subclient_content = ["{0}{1}{2}".format(test_path, slash_format, subclient_name)]
        self.tmp_path = "".join([test_path, slash_format, 'cvauto_tmp', slash_format, subclient_name, slash_format,
                                 str(self.runid)])
        self.run_path = "".join([subclient_content[0], slash_format, str(self.runid)])
        self.create_subclient_and_gen_data(subclient_content, "{0}{1}full".format(self.run_path, slash_format))

    def create_subclient_and_gen_data(self, subclient_content, full_data_path):
        """Creates subclient and generates data in given path"""
        self.helper.create_subclient(
            name="subclient_{0}".format(self.id),
            storage_policy=self.storage_policy,
            content=subclient_content,
            data_readers=self.no_of_streams,
            allow_multiple_readers=self.no_of_streams > 1,
            data_access_nodes=self.data_access_nodes,
            scan_type=self.scan_type,
            delete=self.cleanup_run
        )

        self.log.info("Add full data for the current run.")
        self.client_machine.generate_test_data(
            full_data_path,
            acls=self.acls,
            unicode=self.unicode,
            xattr=self.xattr,
            long_path=self.long_path,
            file_size=self.tcinputs.get('file_size', 21),
            sparse=self.tcinputs.get('sparse')
        )

    def run_backup_and_validate(self, backup_level):
        """Runs backup for subclient with given backup level and verifies postops functionality in case of optimized scan"""
        self.log.info(f"Run {backup_level} backup for the subclient and verify it completes without failures.")
        self.client_machine.run_kdestroy()
        self.backup_job = self.helper.run_backup_verify(scan_type=self.scan_type,
                                                        backup_level=backup_level)[0]

    def run_restore_and_validate(self, data_path, data_path_leaf, verify_job=True, verify_latest=False, cleanup=False):
        """Runs restore, verifies restored data and validates extent level data"""
        self.client_machine.run_kdestroy()
        backup_job_type = self.backup_job.backup_level.lower()
        if backup_job_type == "full" or cleanup:
            find_content = self.helper.testcase.subclient.content[0]
            backup_job = None
        else:
            find_content = data_path
            backup_job = self.backup_job
        if verify_job:
            self.log.info(f"Run a restore of the {backup_job_type} backup data and verify correct data is restored.")
            self.helper.run_restore_verify(
                self.slash_format,
                data_path,
                self.tmp_path, data_path_leaf, self.backup_job,
                is_client_big_data_apps=self.is_client_big_data_apps,
                destination_instance=self.instance_name,
                no_of_streams=self.no_of_streams,
                restore_nodes=self.data_access_nodes)
        if verify_latest:
            self.log.info(f"Run a latest restore of the backup data and verify correct data is restored.")
            self.helper.run_restore_verify(
                self.slash_format,
                data_path,
                self.tmp_path,
                data_path_leaf,
                cleanup=cleanup,
                is_client_big_data_apps=self.is_client_big_data_apps,
                destination_instance=self.instance_name,
                no_of_streams=self.no_of_streams,
                restore_nodes=self.data_access_nodes)
        self.log.info(f"Run a find and verify collect operation for the {backup_job_type} job and verify the returned results.")
        self.helper.run_find_verify(find_content, backup_job)
        if not cleanup:
            collect_validate = self.helper.verify_collect_extent_acl(find_content, backup_job_type,
                                                                     fetch_eligible_files=True,
                                                                     validate_no_of_extents=True)
            if not collect_validate:
                raise Exception("Collect validation failed")

    def backup_and_restore(self, backup_level, data_path, data_path_leaf, verify_latest=False):
        """Runs backup and validates restore"""
        self.run_backup_and_validate(backup_level=backup_level)
        self.run_restore_and_validate(data_path, data_path_leaf, verify_latest=verify_latest)

    def run_incremental_and_differential(self):
        """Run incremental, differential backups and validates data"""
        self.log.info("Add new data and verify data protection")
        incr_diff_data_path = "".join([self.run_path, self.slash_format, "incr_diff"])
        self.helper.add_new_data_incr(incr_diff_data_path, self.slash_format, dirs=1, files=1,
                                      file_size=self.tcinputs.get('file_size', 137), sparse=self.tcinputs.get('sparse'))
        self.backup_and_restore("Incremental", incr_diff_data_path, "incr_diff", verify_latest=True)

        self.log.info("Perform all modifications on the existing data and verify data protection")
        self.helper.mod_data_incr()
        self.backup_and_restore("Incremental", incr_diff_data_path, "incr_diff", verify_latest=True)

        self.log.info("Add new data for the differential")
        self.client_machine.generate_test_data(
            "".join([incr_diff_data_path, self.slash_format, "differential"]),
            acls=self.acls,
            unicode=self.unicode,
            xattr=self.xattr,
            long_path=self.long_path,
            file_size=self.tcinputs.get('file_size', 21),
            sparse=self.tcinputs.get('sparse')
        )
        self.backup_and_restore("Differential", incr_diff_data_path, "incr_diff")

    def run_synth_full(self, modify_data=False, verify_latest=False):
        """Runs synthetic full backups and validates restore"""
        incr_diff_data_path = "".join([self.run_path, self.slash_format, "incr_diff_synth"])
        if modify_data:
            self.log.info("Perform all modifications on the existing data.")
            self.helper.mod_data_incr()
        else:
            self.log.info("Add new data for the incremental")
            self.helper.add_new_data_incr(incr_diff_data_path, self.slash_format, dirs=1, files=1,
                                          file_size=self.tcinputs.get('file_size', 137), sparse=self.tcinputs.get('sparse'))
        self.run_backup_and_validate(backup_level="Synthetic_full")
        self.log.info("Run an incremental backup after synthfull for the subclient")
        self.backup_and_restore("Incremental", incr_diff_data_path, "incr_diff_synth", verify_latest)

    def run(self):
        """Main function for test case execution"""
        try:
            self.backup_and_restore("Full", "{0}{1}full".format(self.run_path, self.slash_format), "full")
            self.run_incremental_and_differential()
            self.run_synth_full(modify_data=False, verify_latest=False)
            self.run_synth_full(modify_data=True, verify_latest=True)
            self.log.info("Run a restore of the complete subclient data and verify correct data is restored.")
            self.run_restore_and_validate(self.helper.testcase.subclient.content[0], f"subclient_{self.id}",
                                          verify_job=False, verify_latest=True, cleanup=True)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.cleanup_run:
            self.client_machine.remove_directory(self.helper.testcase.subclient.content[0])
        self.client_machine.remove_directory(self.tmp_path)
        self.client_machine.run_kdestroy()
        # delete backupset/instance if clean up is specified
        if self.cleanup_run:
            if self.is_client_big_data_apps:
                self.agent.instances.delete(self.instance_name)
            else:
                self.instance.backupsets.delete(self.backupset_name)
