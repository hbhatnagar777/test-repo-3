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
from VirtualServer.VSAUtils.VirtualServerConstants import VMBackupType


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware V2 VM settings validation from Command center"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "VMBackupType": None
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

    def run(self):
        """Main function for test case execution"""

        """
        JSON Input VM Backup Type Format:
        "VMBackupType": "<VM_BACKUP_TYPE>"
        VM_BACKUP_TYPE = APP_CONSISTENT or CRASH_CONSISTENT or INHERITED  
        Ex : "VMBackupType": "APP_CONSISTENT"
        """
        try:
            vm_backup_type = self.tcinputs['VMBackupType']
            applicable_vm_backup_types = [backup_type.name for backup_type in VMBackupType]

            if vm_backup_type not in applicable_vm_backup_types:
                raise Exception('Please provide valid VM Backup Type in the input JSON')

            # 1. Inherit Backup Type from the VM group
            vm_setting_options = {
                'vm_backup_type': VMBackupType.INHERITED.name
            }

            self.vsa_obj.vm_setting_options = vm_setting_options
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            # 2. Override Backup Type at the VM level
            vm_setting_options = {
                'vm_backup_type': vm_backup_type
            }

            self.vsa_obj.vm_setting_options = vm_setting_options
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.run_discovery = False
            self.vsa_obj.backup()

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
