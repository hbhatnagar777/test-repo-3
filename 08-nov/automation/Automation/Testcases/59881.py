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
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.DRHelper import ReplicationMain


class TestCase(CVTestCase):
    """Class for performing suspend and resume replication jobs"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Failback operation with data added to destination VM, and with extra disks, NIC"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.navigator = None
        self.table = None
        self.timestamp = None
        self.tc_hvobj = None
        self.auto_subclient = None
        self.replication_group_name = None

    def setup(self):
        """Setup function for test case execution"""
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.close_popup()

        self.navigator = self.admin_console.navigator
        self.table = Table(self.admin_console)
        self.timestamp = str(int(time.time()))
        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        self.replication_helper = ReplicationMain(self.auto_subclient, self.browser)
        self.replication_group_name = self.tcinputs['ReplicationGroupName']

    def run(self):
        """Main function for test case execution"""
        try:
            # checking if failover operation is done or not
            self.navigator.navigate_to_replication_groups()
            self.table.access_link(self.replication_group_name)
            sync_status = self.table.get_column_data(self.admin_console.props['header.failoverStatus'])
            for status in sync_status:
                if status.lower() not in ["failover complete", "failback failed"]:
                    self.replication_helper.do_unplanned_failover(self.replication_group_name)

            # adding a data disk and an NIC to the destination vm
            self.replication_helper.get_details_for_validation(self.replication_group_name)
            self.tc_hvobj = self.auto_subclient.auto_vsainstance._create_hypervisor_object()
            for vm_name in self.replication_helper.destination_vms:
                if vm_name not in self.tc_hvobj.VMs:
                    self.tc_hvobj.VMs = vm_name
                vm = self.tc_hvobj.VMs[vm_name]
                uri = vm.vm_info['properties']['storageProfile']['osDisk']['vhd']['uri']
                storage_account = uri.split('//')[1].partition('.')[0]
                disk_name = vm.vm_name + self.timestamp
                vm.add_data_disk(disk_name=disk_name, storage_account=storage_account, disk_size=8)
                vm.add_nic(self.tcinputs['NIC'])

            # perform failback operation
            self.replication_helper.do_failback(self.replication_group_name)

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

        finally:
            # removing the data disk and the extra NIC
            for vm_name in self.replication_helper.destination_vms:
                vm = self.tc_hvobj.VMs[vm_name]
                vm.detach_data_disk(vm.vm_name + self.timestamp)
                vm.remove_nic(self.tcinputs['NIC'])

    def tear_down(self):
        """Teardown function for this test case execution"""
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
