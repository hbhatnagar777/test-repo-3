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
    __init__()             --  initialize TestCase class

    run()                  --  run function of this test case
"""

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        File System Data Protection - Synthetic Full
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
        Step2, For all the allowed scan type
                do the following on the backupset
            Step2.1,  Create subclient for the scan type if it doesn't exist.
            Step2.2,  Add new data for the incremental
            Step2.3,  Run an incremental backup for the subclient
                    and verify it completes without failures.
            Step2.4,  Perform all modifications on the existing data.
            Step2.5,  Run a Synthetic Full backup with incremental before
                    for the subclient and verify it completes without failures.
            Step2.6,  Run a restore of the latest data
                    and verify correct data is restored.
            Step2.7,  Run a find operation for the latest data
                    and verify the returned results.
            Step2.8,  Add new data for the incremental
            Step2.9,  Run an incremental backup and
                    verify it completes without failures.
            Step2.10, Perform all modifications on the existing data.
            Step2.11, Run a Synthetic Full backup with incremental after
                    for the subclient and verify it completes without failures.
            Step2.12, Run a restore of the latest data
                    and verify correct data is restored.
            Step2.13, Run a find operation for the latest data
                    and verify the returned results.
            Step2.14, Add new data for the incremental
            Step2.15, Run an incremental backup and
                    verify it completes without failures.
            Step2.16, Run a Synthetic Full backup
                    and verify it completes without failures.
            Step2.17, Run a restore of the complete subclient data
                    and verify correct data is restored.
            Step2.18, Run a find operation for the entire subclient
                    and verify the returned results.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System Data Protection"\
            " - Synthetic Full"
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

            log.info("""File System Data Protection - Synthetic Full
        This test case does the following
        Step1, Create backupset for this testcase if it doesn't exist.
        Step2, For all the allowed scan type
                do the following on the backupset
            Step2.1,  Create subclient for the scan type if it doesn't exist.
            Step2.2,  Add new data for the incremental
            Step2.3,  Run an incremental backup for the subclient
                    and verify it completes without failures.
            Step2.4,  Perform all modifications on the existing data.
            Step2.5,  Run a Synthetic Full backup with incremental before
                    for the subclient and verify it completes without failures.
            Step2.6,  Run a restore of the latest data
                    and verify correct data is restored.
            Step2.7,  Run a find operation for the latest data
                    and verify the returned results.
            Step2.8,  Add new data for the incremental
            Step2.9,  Run an incremental backup and
                    verify it completes without failures.
            Step2.10, Perform all modifications on the existing data.
            Step2.11, Run a Synthetic Full backup with incremental after
                    for the subclient and verify it completes without failures.
            Step2.12, Run a restore of the latest data
                    and verify correct data is restored.
            Step2.13, Run a find operation for the latest data
                    and verify the returned results.
            Step2.14, Add new data for the incremental
            Step2.15, Run an incremental backup and
                    verify it completes without failures.
            Step2.16, Run a Synthetic Full backup
                    and verify it completes without failures.
            Step2.17, Run a restore of the complete subclient data
                    and verify correct data is restored.
            Step2.18, Run a find operation for the entire subclient
                    and verify the returned results.
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

                # Skip DC if verify_dc is not provided
                if (self.applicable_os != 'WINDOWS'
                        and
                        scan_type.value == ScanType.OPTIMIZED.value):
                    if not self.verify_dc:
                        continue

                # Skip Classic scan if specified in inputs
                is_recursive = scan_type.value == ScanType.RECURSIVE.value
                if (self.skip_classic and is_recursive):
                    continue

                # Check if We need to wait for I/O to get flushed
                self.should_wait = True
                if is_recursive:
                    if self.applicable_os == 'UNIX':
                        if 'darwin' not in machine.os_flavour.lower() and not self.is_client_big_data_apps:
                            self.should_wait = False

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

                tmp_path = (test_path
                            + slash_format
                            + 'cvauto_tmp'
                            + slash_format
                            + subclient_name
                            + slash_format
                            + str(self.runid))

                run_path = (subclient_content[0]
                            + slash_format
                            + str(self.runid))

                helper.create_subclient(name=subclient_name,
                                        storage_policy=storage_policy,
                                        content=subclient_content,
                                        scan_type=scan_type,
                                        data_access_nodes=self.data_access_nodes,
                                        delete=self.cleanup_run)

                log.info("Step2.2,  Add new data for the incremental")
                incr_synth_data_path = run_path + slash_format + "incr_bsynth"
                helper.add_new_data_incr(
                    incr_synth_data_path,
                    slash_format,
                    scan_type)

                log.info("Step2.3,  Run an incremental job for the subclient"
                         " and verify it completes without failures.")
                helper.run_backup_verify(scan_type)

                log.info("Step2.4,  Perform modifications"
                         " on the existing data.")
                helper.mod_data_incr(scan_type)

                log.info("Step2.5,  Run a Synthetic Full backup"
                         " with incremental before"
                         " and verify it completes without failures.")
                job_synth = helper.run_backup_verify(
                    scan_type,
                    backup_level="Synthetic_full",
                    incremental_backup=True
                )[1]

                log.info("Step2.6,  Run a restore of the"
                         " latest data"
                         " and verify correct data is restored.")

                log.info(
                    "Verifying time based browse/restore for the synthfull."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    job=job_synth,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)
                log.info(
                    "Verifying latest browse/restore for the synthfull."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                log.info(
                    "Step2.7,  Run a find operation for the latest data"
                    " and verify the returned results.")
                helper.run_find_verify(subclient_content[0], job_synth)

                log.info("Step2.8,  Add new data for the incremental")
                incr_synth_data_path = run_path + slash_format + "incr_asynth"
                helper.add_new_data_incr(
                    incr_synth_data_path,
                    slash_format,
                    scan_type)

                log.info("Step2.9,  Run an incremental backup "
                         "for the subclient"
                         " and verify it completes without failures.")
                helper.run_backup_verify(scan_type)

                log.info(
                    "Step2.10, Perform all modifications "
                    "on the existing data.")
                helper.mod_data_incr(scan_type)

                log.info("Step2.11, Run a Syntehtic Full backup"
                         " with incremental after for the subclient"
                         " and verify it completes without failures.")
                helper.run_backup_verify(
                    scan_type,
                    backup_level="Synthetic_full",
                    incremental_backup=True,
                    incremental_level='AFTER_SYNTH'
                )

                log.info("Step2.12, Run a restore of the"
                         " latest data"
                         " and verify correct data is restored.")

                log.info(
                    "Verifying latest browse/restore for the synthfull."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                log.info(
                    "Step2.13, Run a find operation for the latest data"
                    " and verify the returned results.")
                helper.run_find_verify(subclient_content[0])

                log.info("Step2.14, Add new data for the incremental")
                final_incr_path = run_path + slash_format + "last_incr"
                machine.generate_test_data(
                    final_incr_path,
                    acls=self.acls,
                    unicode=self.unicode,
                    xattr=self.xattr,
                    long_path=self.long_path,
                    problematic=self.problematic)

                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)

                log.info("Step2.15, Run an incremental backup "
                         "for the subclient"
                         " and verify it completes without failures.")
                helper.run_backup_verify(scan_type)

                log.info("Step2.16, Run a Syntehtic Full backup "
                         "for the subclient"
                         " and verify it completes without failures.")
                job_synth = helper.run_backup_verify(
                    scan_type,
                    backup_level="Synthetic_full"
                )[0]

                log.info(
                    "Step2.17, Run a restore of the complete subclient data"
                    " and verify correct data is restored."
                )
                log.info(
                    "Verifying time based browse/restore for the synthfull."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    job=job_synth,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)
                log.info(
                    "Verifying latest browse/restore for the synthfull."
                )
                helper.run_restore_verify(
                    slash_format,
                    subclient_content[0],
                    tmp_path,
                    subclient_name,
                    cleanup=True,
                    is_client_big_data_apps=self.is_client_big_data_apps,
                    destination_instance=self.instance_name,
                    no_of_streams=self.no_of_streams,
                    restore_nodes=restore_nodes)

                log.info(
                    "Step2.18, Run a find operation for the entire subclient"
                    " and verify the returned results.")
                helper.run_find_verify(subclient_content[0])

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

                # IBMi IFS supports only recursive scan.
                # Separate test case for 'Optimized scan'/'Scanless backup'
                if machine.os_flavour == 'OS400':
                    break

                # OpenVMS supports only recursive scan like IBMi.
                # Before completing the test case the OpenVMS test_path
                # must be unmounted from the proxy mount location.
                if machine.os_flavour == 'OpenVMS':
                    helper.unmount_openvms_testpath(test_path)
                    break

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
