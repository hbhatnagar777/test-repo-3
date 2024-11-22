# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Test case for creating and validation of basic operations for Continuous replication pair
Sample json
        "tenant_username": <username>,
        "tenant_password": <password>,
        "view_name": "AutomationView",
        "source_vm": "Source Vm Name",
        "ClientName" : "Client Name"
        "rpstorename": "RpStore name",
        "datastore": "datastore name",
        "resource_pool": "resourcepool name",
        "recovery_target": "Recovery target name",
        "Destination_host": "Destination esx host name",
        "source_vm_network": "Source Vm network"
        "destination_network": "Destination VM network"
"""
from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, wait_for_condition
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore


class TestCase(CVTestCase):
    """Class for executing Command Center replication operations"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Adminconsole--> Continuous replication Monitor page basic operations validation"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "source_vm": None,
            "recovery_target": None,
            "rpstorename": None,
            "Destination_host": None,
            "resource_pool": None,
            "datastore": None
        }
        self.utils = None
        self.browser = None
        self.admin_console = None
        self.replication_monitor = None
        self.replication_group = None
        self.source_vm = None
        self.datastore = None
        self.target_details = None
        self.source_hypervisor = None
        self.recovery_target = None
        self.destination_vm = None
        self.replication_details = None
        self.rpstorename = None
        self.Destination_host = None
        self.resource_pool = None
        self.source_vm_network = None
        self.destination_network = None
        self.rpstore = None
        self.ccrp_1 = "5 minutes"
        self.acrp_1 = "1 hours"
        self.retention_options = {
            "retention": "7 days",
            "merge": True,
            "merge_delay": "2 days",
            "max_rp_interval": "6 hours",
            "max_rp_offline": "15 minutes",
            "off_peak_only": False
        }

    def setup(self):
        """Sets up the variables for the test case"""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            self.login()
            self.admin_console.wait_for_completion()

            self.replication_monitor = ContinuousReplicationMonitor(self.admin_console)
            self.source_vm = self.tcinputs['source_vm']
            self.source_hypervisor = self.tcinputs["ClientName"]
            self.recovery_target = self.tcinputs["recovery_target"]
            self.rpstorename = self.tcinputs["rpstorename"]
            self.Destination_host = self.tcinputs["Destination_host"]
            self.datastore = self.tcinputs["datastore"]
            self.resource_pool = self.tcinputs["resource_pool"]
            self.source_vm_network = self.tcinputs["source_vm_network"]
            self.destination_network = self.tcinputs["destination_network"]
            self.target_details = self.commcell.recovery_targets.get(self.recovery_target)

        except Exception as exp:
            raise CVTestCaseInitFailure(f"Failed to initialize testcase due to {str(exp)}")

    def login(self):
        """Logs in to command center"""
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.goto_adminconsole()
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])
        self.replication_group = ReplicationGroup(self.admin_console)
        self.rpstore = RecoveryPointStore(self.admin_console)
        self.replication_details = ReplicationDetails(self.admin_console)
        self.continuous_monitor = ContinuousReplicationMonitor(self.admin_console)


    @property
    def group_name(self):
        """Returns the replication group name"""
        return ReplicationHelper.group_name(self.id)

    @test_step
    def delete_pair(self):
        """Deletes the pair and information if it exists"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.select_destination_option_grid()
        if self.replication_monitor.has_replication_group(self.tcinputs['source_vm'],
                                                          self.tcinputs['destination_vm']):
            if self.replication_monitor.check_view(self.tcinputs['view_name']):
                self.replication_monitor.delete_view(self.tcinputs['view_name'])
            self.replication_monitor.create_view(self.tcinputs['view_name'],
                                                 {'Source': self.tcinputs['source_vm'],
                                                  'Destination': self.tcinputs['destination_vm']})
            self.replication_monitor.select_view(self.tcinputs['view_name'])
            self.replication_monitor.delete_pair()
            self.replication_monitor.delete_view(self.tcinputs['view_name'])
            sleep(300)

    @test_step
    def configure_replication_group(self):
        """Create a continuous replication group"""

        self.admin_console.navigator.navigate_to_replication_groups()
        vmware_configure = self.replication_group.configure_vmware()
        vmware_configure.content.set_name(self.group_name)
        vmware_configure.content.select_vm_from_browse_tree(self.source_hypervisor,
                                                            {"VMs and templates": [self.source_vm]})
        vmware_configure.next()
        vmware_configure.target.select_recovery_target(self.recovery_target)
        vmware_configure.target.select_continuous_replication_type()
        vmware_configure.next()
        self.rpstore.select_recovery_type(1)
        self.rpstore.select_store(self.rpstorename)
        self.rpstore.configure_intervals(self.ccrp_1, self.acrp_1)
        self.rpstore.configure_retention(self.retention_options["retention"],
                                         self.retention_options["merge"],
                                         self.retention_options["merge_delay"],
                                         self.retention_options["max_rp_interval"],
                                         self.retention_options["max_rp_offline"],
                                         self.retention_options["off_peak_only"])
        vmware_configure.next()
        override_options = vmware_configure.override_options.override_vms(self.source_vm)
        override_options.set_destination_host(self.Destination_host)
        override_options.select_datastore(self.datastore)
        override_options.select_resource_pool(self.resource_pool)
        edit_network = override_options.edit_network()
        edit_network.select_source_network(self.source_vm_network)
        edit_network.select_destination_network(self.destination_network)
        edit_network.save()
        self.admin_console.click_button('Save')
        self.vm_noedit_details = vmware_configure.override_options.get_vmware_details(
            self.source_vm
        )
        self.vm_noedit_details[2] = self.vm_noedit_details[2].split(" ")[0]
        self.utils.assert_comparison(self.target_details.destination_host, self.vm_noedit_details[1])
        self.utils.assert_includes(self.target_details.datastore, self.vm_noedit_details[2])
        self.utils.assert_comparison(self.target_details.resource_pool, self.vm_noedit_details[3])
        vmware_configure.next()
        sleep(5)
        vmware_configure.finish()

    @test_step
    def verify_blr_creation(self):
        """Verifies the creating of a Continuous pair in the replication monitor's continuous tab"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.select_destination_option_grid()
        if not self.replication_monitor.has_replication_group(
                self.tcinputs['source_vm'],
                self.tcinputs['destination_vm']):
            raise CVTestStepFailure("The BLR pair was not created or found")

        self.replication_monitor.create_view(self.tcinputs['view_name'],
                                             {'Source': self.tcinputs['source_vm'],
                                              'Destination': self.tcinputs['destination_vm']})

    def get_destination_vm(self):
        if self.target_details.vm_prefix:
            self.destination_vm = f'{self.target_details.vm_prefix}{self.source_vm}'
        elif self.target_details.vm_suffix:
            self.destination_vm = f'{self.source_vm}{self.target_details.vm_suffix}'

    def select_destination_option_grid(self):
        """select destination from actions grid on monitor page"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.continuous_monitor.select_grid_option("Destination")

    @test_step
    def verify_pair_status(self):
        """Waits for sometime for pair to add new content and then check its status"""

        self.replication_monitor.select_view(self.tcinputs['view_name'])
        self.check_pair_status('Replicating')

    @test_step
    def verify_resync(self):
        """Performs a re-sync operation and verifies the status"""

        self.replication_monitor.resync()
        sleep(60)
        self.check_pair_status('Replicating')

    @wait_for_condition(timeout=900)
    def wait_for_sync_status(self, expected):
        """Waits for the sync status to meet expected value"""
        return (self.replication_monitor.sync_status(self.tcinputs['source_vm'],
                                                     self.tcinputs['destination_vm']) == expected)

    def check_pair_status(self, expected):
        """Checks the sync status of the BLR pair with the expected value"""
        self.wait_for_sync_status(expected)

    @test_step
    def verify_suspend(self):
        """Performs a suspend and verifies the state"""
        self.replication_monitor.suspend()
        sleep(60)
        self.check_pair_status('Suspended')

    @test_step
    def verify_resume(self):
        """Performs a resume operation"""
        self.replication_monitor.Undo_failover()
        self.check_pair_status('Replicating')

    @test_step
    def verify_stop(self):
        """Performs a stop operation"""
        self.replication_monitor.stop()
        self.check_pair_status('Stopped')

    @test_step
    def verify_start(self):
        """Performs a start operation"""
        self.replication_monitor.start()
        self.check_pair_status('Replicating')

    def change_recovery_type(self, after_edit=False):
        """Changes the recovery type of replication group in the configuration tab"""
        self.admin_console.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.replication_details.access_configuration_tab()
        self.replication_details.configuration.edit_recovery_options()
        if after_edit:
            self.rpstore.select_recovery_type(0)
        else:
            self.rpstore.select_recovery_type(1)
            self.rpstore.select_store(self.rpstorename)
            self.rpstore.configure_intervals(self.ccrp_2, self.acrp_2)
            self.rpstore.configure_retention(self.retention_options["retention"],
                                             self.retention_options["merge"],
                                             self.retention_options["merge_delay"],
                                             self.retention_options["max_rp_interval"],
                                             self.retention_options["max_rp_offline"],
                                             self.retention_options["off_peak_only"])
        self.admin_console.click_button('Save')
        sleep(300)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def run(self):
        try:
            self.delete_pair()
            self.configure_replication_group()
            self.verify_blr_creation()
            self.get_destination_vm()
            self.select_destination_option_grid()
            self.verify_pair_status()
            self.verify_resync()
            self.verify_suspend()
            self.select_destination_option_grid()
            self.verify_resume()
            self.verify_stop()
            self.verify_start()

            self.change_recovery_type(after_edit=True)
            self.logout()
            sleep(600)
            self.login()
            self.select_destination_option_grid()
            self.verify_pair_status()
            self.verify_resync()
            self.verify_suspend()
            self.verify_resume()
            self.verify_stop()
            self.verify_start()
            self.delete_pair()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
