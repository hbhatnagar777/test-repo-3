# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing basic testcase for attach disk restore from FULL VMware Cloud director backups through Admin Console"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "VMware Cloud director Full Backup and Attach Disk Restore"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "VcloudVdc": None
        }


    def setup(self):
        decorative_log("Initalising Browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.destination_vm_path = self.tcinputs['DestinationVM']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        self.vsa_obj.org_vdc = self.tcinputs['VcloudVdc']
        self.log.info("Created VSA object successfully.")

    def run(self):
        """Main function for testcase execution"""
        try:
            decorative_log("Starting Backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
            try:
                decorative_log("Performing attach disk restore")
                self.vsa_obj.attach_disk_restore(disk_storage_policy = self.tcinputs['StoragePolicy'])
            except Exception as exp:
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            self.vsa_obj.cleanup_testdata()
            self.vsa_obj.post_restore_clean_up(status= self.status, disk_restore=True)
        except Exception:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed")