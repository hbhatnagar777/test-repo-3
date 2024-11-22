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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware V2 VM Disk Filters validation from Command center"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "VMDiskFilters": None
        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)

    @test_step
    def clear_include_vm_group_disk_filters_flag(self):
        """
            Clears the Subclient attribute [Include VM Group Disk Filters] for all the VMs from the DB

            Raises:
                Exception:
                    If failed to execute the query
        """
        for _vm in self.vsa_obj.auto_vsa_subclient.vm_list:
            self.vsa_obj.auto_vsa_subclient.delete_subclient_attribute("Include VM Group Disk Filters", _vm)

    def run(self):
        """Main function for test case execution"""

        """
        JSON Input VM Disk Filters Format:
        "VMDiskFilters": "<List of vmdk names for each VM>"
        Ex : "VMDiskFilters": [AutoVM1.vmdk,AutoVM1_1.vmdk,AutoVM2.vmdk,AutoVM2_1.vmdk..]
        """
        try:

            if not isinstance(self.tcinputs['VMDiskFilters'], list):
                raise Exception("Please provide list as an input for ['VMDiskFilters'] in the JSON")

            vm_disk_filters = self.tcinputs['VMDiskFilters']
            is_input_valid = all(disk_filter.endswith('.vmdk') for disk_filter in vm_disk_filters)

            if not is_input_valid:
                raise Exception('JSON input list for VM Disk Filters is not valid')

            # 1. Inherit Disk Filters from the VM group
            vm_disk_filter_options = {
                'filters': None
            }

            self.vsa_obj.vm_disk_filter_options = vm_disk_filter_options
            self.vsa_obj.backup_type = "INCR"
            # Cleanup any existing flag for [Include VM Group Disk Filters] before starting the configuration
            self.clear_include_vm_group_disk_filters_flag()
            self.vsa_obj.backup()
            self.vsa_obj.auto_vsa_subclient.validate_disk_filtering()

            # 2. Include VM group disk filters along with VM level filters
            vm_disk_filter_options = {
                'filters': vm_disk_filters,
                'include_vm_group_disk_filters': True
            }

            self.vsa_obj.vm_disk_filter_options = vm_disk_filter_options
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.run_discovery = False
            self.vsa_obj.backup()
            self.vsa_obj.auto_vsa_subclient.validate_disk_filtering()

            # 3. Override Disk Filters at the VM level
            vm_disk_filter_options = {
                'filters': vm_disk_filters,
                'include_vm_group_disk_filters': False
            }

            self.vsa_obj.vm_disk_filter_options = vm_disk_filter_options
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.run_discovery = False
            self.vsa_obj.backup()
            self.vsa_obj.auto_vsa_subclient.validate_disk_filtering()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status=self.test_individual_status)

        except Exception as exp:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed : {}".format(exp))

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
