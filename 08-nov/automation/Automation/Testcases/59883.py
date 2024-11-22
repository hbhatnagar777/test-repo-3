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
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.DRHelper import ReplicationMain


class TestCase(CVTestCase):
    """Class for performing failover and failback operation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure - DR - Failover and failback operations when both source and destination vms are powered on"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.replication_helper = None
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
        self.auto_subclient = VirtualServerUtils.subclient_initialize(self)
        self.replication_helper = ReplicationMain(self.auto_subclient, self.browser)
        self.replication_group_name = self.tcinputs['ReplicationGroupName']

    def power_on_vms(self):
        """ Function to power on the source and destination vms """
        for vm_name in self.replication_helper.source_vms:
            if vm_name not in self.tc_hvobj.VMs:
                self.tc_hvobj.VMs = vm_name
            self.tc_hvobj.VMs[vm_name].power_on()

        for vm_name in self.replication_helper.destination_vms:
            if vm_name not in self.tc_hvobj.VMs:
                self.tc_hvobj.VMs = vm_name
            self.tc_hvobj.VMs[vm_name].power_on()
        time.sleep(30)

    def run(self):
        """Main function for test case execution"""
        try:
            self.replication_helper.get_details_for_validation(self.replication_group_name)
            self.tc_hvobj = self.auto_subclient.auto_vsainstance._create_hypervisor_object()
            self.power_on_vms()

            # performing the unplanned failover operation
            self.replication_helper.do_unplanned_failover(self.replication_group_name)

            # performing the failback operation
            self.power_on_vms()
            self.replication_helper.do_failback(self.replication_group_name)

        except Exception as exp:
            decorative_log("Testcase Failed")
            raise exp

    def tear_down(self):
        """Teardown function for this test case execution"""
        self.browser.close()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED
