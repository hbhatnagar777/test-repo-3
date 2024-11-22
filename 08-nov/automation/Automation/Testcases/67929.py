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

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Full,Incremental,Differential
                This test case does the following
                Step1, Create backupset/Instance for this testcase if it doesn't exist.
                Step2, For all the allowed scan type do the following on the backupset/Instance
                    Step2.1,  Create subclient for the scan type if it doesn't exist.
                    Step2.2,  Add full data for the current run.
                    Step2.3,  Run a full backup for the subclient
                            and verify it completes without failures.
                    Step2.4,  Run a restore of the full backup data
                            and verify correct data is restored.
                    Step2.5,  Add new data for the incremental
                    Step2.6,  Run an incremental backup for the subclient
                            and verify it completes without failures.
                    Step2.7,  Run a restore of the incremental backup data
                            and verify correct data is restored.
                    Step2.9, Perform all modifications on the existing data.
                    Step2.10, Run an incremental backup for the subclient
                            and verify it completes without failures.
                    Step2.11, Run a restore of the incremental backup data
                            and verify correct data is restored..
                    Step2.12, Add new data for the differential
                    Step2.13, Run a differential backup for the subclient
                            and verify it completes without failures.
                    Step2.14, Run a restore of the differential backup data
                            and verify correct data is restored.
                    Step2.15, Add new data for the incremental
                    Step2.16, Run a synthfull job
                    Step2.17, Run the incremental after synthfull job
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection" \
                    " - Full,Incremental,Synth full"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.only_full = None
        self.only_incr = None
        self.only_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.acls = None
        self.unicode = None
        self.xattr = None
        self.long_path = None
        self.problematic = None
        self.WAIT_TIME = None
        self.RETAIN_DAYS = None
        self.should_wait = None
        self.is_client_big_data_apps = None
        self.is_client_network_share = None
        self.master_node = None
        self.data_access_nodes = None
        self.no_of_streams = None
        self.instance_name = None
        self.cleanup_run = None
        self.backupset_name = None
        self.username = None
        self.password = None

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self, mandatory=False)

            if "cv_fs_automation_{0}".format(self.id) not in self.test_path:
                self.test_path = "{0}{1}{2}".format(
                    self.test_path.rstrip(self.slash_format), self.slash_format, self.id)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            machine = self.client_machine
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            log.info("""File System Data Protection - Full,Incremental,Differential
        This test case does the following
        Step1, Create backupset/Instance for this testcase if it doesn't exist.
        Step2, For all the allowed scan type do the following on the backupset/Instance
            Step2.1,  Create subclient for the scan type if it doesn't exist.
            Step2.2,  Add full data for the current run.
            Step2.3,  Run a full backup for the subclient
                    and verify it completes without failures.
            Step2.4,  Run a restore of the full backup data
                    and verify correct data is restored.
            Step2.5,  Add new data for the incremental
            Step2.6,  Run an incremental backup for the subclient
                    and verify it completes without failures.
            Step2.7,  Run a restore of the incremental backup data
                    and verify correct data is restored.
            Step2.8, Perform all modifications on the existing data.
            Step2.9, Run an incremental backup for the subclient
                    and verify it completes without failures.
            Step2.10, Run a restore of the incremental backup data
                    and verify correct data is restored..
            Step2.11, Add new data for the differential
            Step2.12, Run a differential backup for the subclient
                    and verify it completes without failures.
            Step2.13, Run a restore of the differential backup data
                    and verify correct data is restored.
            Step2.14, Add new data for the incremental
            Step2.15, Run a synthfull job
            Step2.16, Run the incremental after synthfull job
                        """)

            if self.is_client_big_data_apps:
                log.info("Step1, Create Instance for "
                         "this testcase if it doesn't exist")
                instance_name = "Instance_" + self.id
                helper.create_instance(instance_name, delete=self.cleanup_run)
                self.instance_name = instance_name
            else:
                log.info("Step1, Create backupset for "
                         "this testcase if it doesn't exist")
                backupset_name = "backupset_" + self.id
                helper.create_backupset(backupset_name, delete=self.cleanup_run)
                self.backupset_name = backupset_name

            restore_nodes = self.data_access_nodes

            log.info("Step2, Executing steps for all the allowed scan type")
            for scan_type in ScanType:
                # SKip chain journal scan for Unix
                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.CHANGEJOURNAL.value):
                    continue
                if(self.applicable_os == 'WINDOWS'
                    and scan_type.value == ScanType.CHANGEJOURNAL.value and self.only_dc == True):
                    continue

                # Skip DC if verify_dc is not provided
                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.OPTIMIZED.value):
                    if not self.verify_dc:
                        continue

                # Skip Classic scan if specified in inputs
                is_recursive = scan_type.value == ScanType.RECURSIVE.value
                if (self.applicable_os == 'WINDOWS' and is_recursive and self.only_dc):
                    continue

                if (self.skip_classic and is_recursive):
                    continue

                # Check if We need to wait for I/O to get flushed
                self.should_wait = True
                if is_recursive:
                    if self.applicable_os == 'UNIX':
                        if 'darwin' not in machine.os_flavour.lower() and not self.is_client_big_data_apps:
                            self.should_wait = False

                # Skip Optimized and Change Journal Scan methods if client is a Network Share Client.
                if self.is_client_network_share and scan_type.value in (
                ScanType.OPTIMIZED.value, ScanType.CHANGEJOURNAL.value):
                    self.log.info(f"For Network Share Client, skipping run for {scan_type.name} scan method")
                    continue

                log.info("**STARTING RUN FOR " + scan_type.name + " SCAN**")
                log.info("Step2.1,  Create subclient for the scan type "
                         + scan_type.name + " if it doesn't exist.")
                subclient_name = ("subclient_"
                                  + self.id
                                  + "_"
                                  + scan_type.name.lower())
                subclient_content = []
                subclient_content.append(test_path
                                         + slash_format
                                         + subclient_name)
                log.info("Checking subclient content %s exists", subclient_content[0])
                if machine.check_directory_exists(subclient_content[0]):
                    log.info("Removing subclient content %s", subclient_content[0])
                    machine.remove_directory(subclient_content[0])

                restore_path = ("{0}{1}cvauto_tmp{2}{3}".format(
                    test_path, slash_format, slash_format, subclient_name))

                log.info("Cleaning restored content %s if exists", restore_path)
                if machine.check_directory_exists(restore_path):
                    log.info("Removing restored content %s", restore_path)
                    machine.remove_directory(restore_path)

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
                                        data_readers=self.no_of_streams,
                                        allow_multiple_readers=self.no_of_streams > 1,
                                        data_access_nodes=self.data_access_nodes,
                                        delete=self.cleanup_run)

                log.info("Step2.2,  Add full data for the current run.")

                log.info("Adding data under path:" + full_data_path)
                machine.generate_test_data(
                    full_data_path,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr,
                    long_path=self.long_path,
                    problematic=self.problematic,
                    username=self.username,
                    password=self.password
                )

                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)

                log.info("Step2.3,  Run a full backup for the subclient "
                         "and verify it completes without failures.")
                job_full = helper.run_backup_verify(scan_type, "Full")[0]

                log.info("Step2.4,  Run a restore of the full backup data"
                         " and verify correct data is restored.")

                helper.run_restore_verify(
                    slash_format,
                    full_data_path,
                    tmp_path, "full", job_full,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                if self.only_full == True:
                    continue

                log.info("Step2.5,  Add new data for the incremental")
                incr_diff_data_path = run_path + slash_format + "incr_diff"
                helper.add_new_data_incr(
                    incr_diff_data_path,
                    slash_format,
                    scan_type,
                    username=self.username,
                    password=self.password
                )
                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)

                log.info("Step2.6,  Run an incremental job for the subclient"
                         " and verify it completes without failures.")
                job_incr1 = helper.run_backup_verify(
                    scan_type, "Incremental")[0]

                log.info(
                    "Step2.7,  Run a restore of the incremental backup data"
                    " and verify correct data is restored."
                )
                helper.run_restore_verify(
                    slash_format,
                    incr_diff_data_path,
                    tmp_path, "incr_diff", job_incr1,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)
                if self.only_incr:
                    continue

                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)

                log.info("Step2.8, Perform modifications"
                         " on the existing data.")
                helper.mod_data_incr(scan_type)

                log.info("Step2.9, Run incremental backup for the subclient"
                         " and verify it completes without failures.")
                job_incr2 = helper.run_backup_verify(
                    scan_type, "Incremental")[0]

                log.info("Step2.10, Run a restore of the"
                         " incremental backup data"
                         " and verify correct data is restored.")

                log.info(
                    "Verifying time based browse/restore for the incremental."
                )

                helper.run_restore_verify(
                    slash_format,
                    incr_diff_data_path,
                    tmp_path,
                    "incr_diff",
                    job_incr2,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                log.info(
                    "Verifying latest browse/restore for the incremental."
                )

                helper.run_restore_verify(
                    slash_format,
                    incr_diff_data_path,
                    tmp_path,
                    "incr_diff",
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                log.info("Step2.11, Add new data for the differential")
                incr_new_diff_path = (incr_diff_data_path
                                      + slash_format
                                      + "differential")
                machine.generate_test_data(
                    incr_new_diff_path,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr,
                    long_path=self.long_path,
                    problematic=self.problematic,
                    username=self.username,
                    password=self.password
                )

                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(600)

                log.info("Step2.12, Run a differential backup "
                         "for the subclient"
                         " and verify it completes without failures.")
                job_diff = helper.run_backup_verify(
                    scan_type, "Differential")[0]

                log.info(
                    "Step2.13, Run a restore of the differential backup data"
                    " and verify correct data is restored."
                )
                helper.run_restore_verify(
                    slash_format,
                    incr_diff_data_path,
                    tmp_path,
                    "incr_diff",
                    job_diff,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                log.info("Step2.14, Add new data for the incremental")
                incr_diff_data_path = (run_path
                                       + slash_format
                                       + "incr_diff_synth")
                helper.add_new_data_incr(
                    incr_diff_data_path,
                    slash_format,
                    scan_type,
                    username=self.username,
                    password=self.password
                )

                log.info("Step2.15, Run a synthfull job")
                helper.run_backup_verify(scan_type, "Synthetic_full")

                log.info("Step2.16, Run the incremental after synthfull job")
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

                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)


                if self.cleanup_run:
                    machine.remove_directory(subclient_content[0])
                else:
                    machine.remove_directory(
                        subclient_content[0],
                        self.RETAIN_DAYS
                    )
                log.info("**"
                         + scan_type.name
                         + " SCAN RUN COMPLETED SUCESSFULLY**")

                machine.remove_directory(tmp_path)

            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            if self.cleanup_run:
                log.info("Cleaning up all the entities created")
                try:
                    machine.remove_directory(self.test_path)
                except Exception as excp:
                    log.error('Cleanup failed with error: %s', str(excp))

                try:
                    if self.is_client_big_data_apps:
                        log.info('Deleting instance: %s', self.instance_name)
                        self.agent.instances.delete(self.instance_name)
                    else:
                        log.info('Deleting backupset: %s', self.backupset_name)
                        self.instance.backupsets.delete(self.backupset_name)
                except Exception as excp:
                    log.error('Cleanup failed with error: %s', str(excp))
