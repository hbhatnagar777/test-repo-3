# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Live Sync IO: Pair Configurations : With Prune and Merge changes during off-peak time only

Sample input: "56718": { "group_name":"Replication group name", "unc_path":"Enter the shared UNC path to which
VMRpstore db file is to be copied from destination proxy i.e \\\\AUTO_CONTROLLER\\vmrpstoredb_share",
"username":"Enter remote machine username where RP store resides", "Enter remote machine password where RP store resides"
,"local_share_path":"Enter local machine shared path i.e "E:\\vmrpstoredb_share" } """

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, wait_for_condition
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from AutomationUtils.machine import Machine
from Web.AdminConsole.DR.rp_store import RpstoreOperations,RPStores
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
from time import sleep
from cvpysdk.drorchestration.blr_pairs import BLRPair
import re
from datetime import date,datetime
import calendar
from AutomationUtils import database_helper
from DROrchestration.test_failover import TestFailover
from Web.AdminConsole.DR.group_details import ReplicationDetails


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)

        self.vm_guid = None
        self.rpstore_mountpath = None
        self.name = "Live Sync IO: Pair Configurations : With Prune and Merge changes during off-peak time only"
        self.rpstat_details1 = None
        self.rpstat_details2 = None
        self.tcinputs = {
            "group_name": None,
            "unc_path": None,
            "username": None,
            "password": None,
            "local_share_path": None
        }
        self.replication_group = None
        self.source_vm = None
        self.destination_vm = None
        self.group_name = None

        self.rpstorename = None
        self.test_failover = None
        self.controller = Machine()
        self.testboot_options = {
            "test_vm_name": "Automation56719_TestVm",
            "expiration_time": "0:2",
            "recovery_type": "Recovery point time",
            "recovery_point": ""
        }
        self.retention_options = {
            "retention": "7 days",
            "merge": True,
            "merge_delay": "4 minutes",
            "max_rp_interval": "6 minutes",
            "max_rp_offline": "15 minutes",
            "off_peak_only": True
        }

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.group_name = self.tcinputs["group_name"]
        self.test_failover = TestFailover(self.commcell, self.group_name)
        self.source_vm = [*self.test_failover.group.vm_pairs][1]
        self.rpstorename = \
            self.test_failover.group.vm_pairs.get(self.source_vm).pair_properties['blrRecoveryOpts']['granularV2'][
                'rpStoreName']
        self.destination_vm = self.test_failover.group.vm_pairs.get(self.source_vm).destination_vm

    def login(self):
        """Logs in to admin console"""
        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.replication_group = ReplicationGroup(self.admin_console)
            self.rpstore_options = RecoveryPointStore(self.admin_console)
            self.replication_details = ReplicationDetails(self.admin_console)
            self.rpstore = RpstoreOperations(self.admin_console)
            self.rpstore_tab = RPStores(self.admin_console)
            self.blr_pair = BLRPair(self.commcell, self.source_vm, self.destination_vm)
            self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)
            self.unc_path = self.tcinputs['unc_path']
            self.username = self.tcinputs['username']
            self.password = self.tcinputs['password']
            self.local_share_path = self.tcinputs['local_share_path']

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def select_destination_option_grid(self):
        """select destination from actions grid on monitor page"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_grid_option("Destination")

    def check_pair_status(self, expected):
        """Checks the sync status of the BLR pair with the expected value"""
        self.wait_for_sync_status(expected)

    @wait_for_condition(timeout=3500)
    def wait_for_sync_status(self, expected):
        """Waits for the sync status to meet expected value"""
        return (self.continuous_monitor.sync_status(self.source_vm,
                                                    self.destination_vm) == expected)

    @test_step
    def change_recovery_type(self, operation):
        """Changes the recovery type of replication group in the configuration tab"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.replication_details.access_configuration_tab()
        self.replication_details.configuration.edit_recovery_options()

        self.rpstore_options.select_recovery_type(1)
        self.rpstore_options.select_store(self.rpstorename)
        self.rpstore_options.configure_intervals("3 minutes", "5 minutes")
        if operation == "pruning":
            self.retention_options["retention"] = "3 minutes"
        self.rpstore_options.configure_retention(self.retention_options["retention"],
                                                 self.retention_options["merge"],
                                                 self.retention_options["merge_delay"],
                                                 self.retention_options["max_rp_interval"],
                                                 self.retention_options["max_rp_offline"],
                                                 self.retention_options["off_peak_only"])
        self.admin_console.click_button('Save')

    @test_step
    def write_temp_data(self):
        """Writes data to the virtual machine and performs prevalidation for testfailover operation
        """
        self.test_failover.pre_validation()

    @test_step
    def perform_stop(self):
        """Perform stop operation on the pair"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.stop(self.source_vm, self.destination_vm)
        self.select_destination_option_grid()
        self.check_pair_status('Stopped')

    @test_step
    def perform_start(self):
        """Perform start operation on the pair"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.start(self.source_vm, self.destination_vm)
        sleep(200)
        self.select_destination_option_grid()
        self.check_pair_status('Replicating')

    @test_step
    def get_vm_guid(self):
        """Get destination vm guid"""
        self.vm_guid = self.blr_pair.destination['guid']

    @test_step
    def get_mountpath(self):
        """Get RP store mount path"""
        self.rpstore_mountpath = self.commcell.blr_pairs.get_rpstore_mountpath(self.rpstorename)

    @test_step
    def clear_intervals(self, rpstore_name):
        """Clears the intervals set on a rpstore"""
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.goto_rpstore(rpstore_name)
        self.rpstore.edit_general_details()
        self.rpstore.clear_intervals()

    @test_step
    def edit_and_verify_storage(self, name, rp_interval):
        """Change the edit storage options and verify disabled field """
        rp_interval = {calendar.day_name[date.today().weekday()]: [datetime.now().hour]}
        self.admin_console.navigator.navigate_to_rpstore()
        self.rpstore.goto_rpstore(self.rpstorename)
        self.rpstore.edit_general_details()
        self.rpstore.edit_storage(name, "60", rp_interval)
        self.rpstore.edit_general_details()
        self.admin_console.click_button('Save')

    def execute_sqlite_query(self, local_rpstoredb_path, operation_type):
        """ Function to connect to SQLite DB."""
        try:
            query = "select * from RecoveryPoints"
            sql_db = database_helper.SQLite(local_rpstoredb_path)
            execute_db = sql_db.connection
            cur = execute_db.cursor()
            cur.execute(query)
            if operation_type == "before_merge":
                self.initial_merge_rps = cur.fetchall()
            else:
                self.after_merge_rps = cur.fetchall()
            execute_db.close()

        except Exception as err:
            pass

    @test_step
    def read_rpstoredb(self, operation):
        """Read RP store db file"""
        self.destination_proxy = self.test_failover.destination_auto_instance.proxy_list[0]
        self.destination_proxy_obj = Machine(self.destination_proxy, self.commcell)
        remote_rpstoredb_path = self.destination_proxy_obj.join_path(self.rpstore_mountpath, self.vm_guid)
        self.destination_proxy_obj.copy_folder_to_network_share(remote_rpstoredb_path,
                                                                self.unc_path, self.username,
                                                                self.password)
        local_rpstoredb_path = self.destination_proxy_obj.join_path(self.local_share_path, self.vm_guid, "VmRpStore.Db")
        self.execute_sqlite_query(local_rpstoredb_path, operation)

    @test_step
    def verify_merge(self):
        """Verifies merge operation"""
        for before_merge_rp in self.initial_merge_rps:
            for after_merge_rp in self.after_merge_rps:
                if after_merge_rp[0] == before_merge_rp[0]:
                    self._log.info("RP found with ID %s", str(after_merge_rp[0]))
                    if after_merge_rp[1] > 0:
                        self._log.info("- RP with ID %s got merged successfully new level value is %s",
                                       str(after_merge_rp[0]),
                                       str(after_merge_rp[1]))
                        break
                    else:
                        raise CVTestStepFailure(
                            "Failed!!Merge operation failed RP with ID %s has level 0 and not merged yet",
                            str(after_merge_rp[0]))
        self._log.info("Successfully verified merge operation")

    @test_step
    def get_rp_stats(self, operation):
        """Get list of RP store points for point in time boot operations"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        if operation == "before_prune":
            self.rpstat_details1 = self.rpstore.get_all_rp_stats(self.source_vm, self.destination_vm)
        else:
            self.rpstat_details2 = self.rpstore.get_all_rp_stats(self.source_vm, self.destination_vm)

    @test_step
    def perform_test_failover(self, testboot_options):
        """Perform test boot on the destination VM"""

        self.admin_console.navigator.navigate_to_continuous_replication()
        test_boot_job_id = self.continuous_monitor.continuous_test_bootvm(testboot_options,self.source_vm, self.destination_vm)
        job_obj = self.commcell.job_controller.get(test_boot_job_id)
        # self.logout()
        self.log.info('Waiting for Job [%s] to complete', test_boot_job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
        self.test_failover.job_phase_validation(test_boot_job_id)

    @test_step
    def attach_network(self, test_vm_name):
        """Attaches NIC card to test boot VM"""
        self.test_failover._destination_auto_instance.hvobj.VMs = test_vm_name
        self.testfailover_vm = self.test_failover._destination_auto_instance.hvobj.VMs[test_vm_name]
        self.testfailover_vm.attach_network_adapter()
        sleep(150)
        self.testfailover_vm.update_vm_info(force_update=True)
        self.testfailover_vm.update_vm_info(prop="All")

    @test_step
    def test_diff(self):
        """Verifies the integrity of the test data on test booted VM"""
        self.test_failover.update_testfailovervm_details(self.testboot_options['test_vm_name'])
        self.test_failover.post_validation()

    @test_step
    def delete_testboot_vm(self):
        """Delete the current test boot VM"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.pair_details = self.continuous_monitor.access_pair_details(self.source_vm)
        self.pair_details.continuous_delete_testboot(self.testboot_options['test_vm_name'])

    @test_step
    def verify_pruning(self, prune_start_time):
        """Verifies if pruning gets completed"""

        self.get_rp_stats("after_prune")
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.destination_proxy = self.test_failover.destination_auto_instance.proxy_list[0]
        self.destination_proxy_obj = Machine(self.destination_proxy, self.commcell)

        ##verify if the ldest before prune rp present in th RP list

        if self.rpstat_details1[0] in self.rpstat_details2:
            raise CVTestStepFailure("Failed!! Some of the Oldest RP's not pruned")
        else:
            self.log.info("Successfully verified before prune oldest RP got pruned successfully")

        self.log.info("Verifying pruning operation from logs")

        result = self.destination_proxy_obj.get_log_file("BlrSvc.log", all_versions=False)
        pattern = "\d+/\d+\s+\d+:\d+:\d+\s+\d+\s+\["+self.source_vm+"\]\s+[BlrTail]+::[pruneUntil]+\(\)\s+-\s+[Streaming complete]+"
        latest_pruned_log = re.findall(pattern, result)[-1]
        current_log_date = re.findall('\d+/\d+\s+\d+:\d+:\d+', latest_pruned_log)[0]
        current_log_date = re.sub("\d+/\d+", current_log_date.split()[0]+"/"+str(prune_start_time.year)[2:4], current_log_date)
        prune_log_date = datetime.strptime(current_log_date, '%m/%d/%y %H:%M:%S')

        if prune_start_time > prune_log_date:
            raise CVTestStepFailure("Failed!! Some of the Oldest RP's not pruned")
        else:
            self.log.info("Successfully verified from logs pruning ran successfully")

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def run(self):
        """Runs the testcase in order"""
        try:

            self.login()
            self.clear_intervals(self.rpstorename)
            self.edit_and_verify_storage(self.rpstorename)
            self.change_recovery_type("merging")

            ### perform start and stop to delete all previous RP's on the pair
            self.perform_stop()
            self.perform_start()
            self.write_temp_data()
            self.get_vm_guid()
            self.get_mountpath()
            sleep(400)
            self.read_rpstoredb("before_merge")

            ## sleep to allow the old RP's to merge
            sleep(400)

            self.read_rpstoredb("after_merge")
            self.verify_merge()

            ### Perform test boot using Oldest point in time
            ### Wait for 5 mins for initial RP to get created
            self.admin_console.refresh_page()
            self.testboot_options['recovery_type'] = "Oldest point in time"
            self.perform_test_failover(self.testboot_options)
            sleep(150)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()
            self.delete_testboot_vm()
            self.write_temp_data()
            sleep(150)
            self.get_rp_stats("before_prune")
            self.change_recovery_type("pruning")
            time_t = datetime.now()
            ###Verify pruning gets completed sleep for
            sleep(250)
            self.verify_pruning(time_t)

            self.clear_intervals(self.rpstorename)
            self.write_temp_data()
            sleep(350)
            self.admin_console.refresh_page()
            self.testboot_options['recovery_type'] = "Latest recovery point"
            self.perform_test_failover(self.testboot_options)
            sleep(150)
            self.attach_network(self.testboot_options['test_vm_name'])
            self.test_diff()
            self.delete_testboot_vm()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
