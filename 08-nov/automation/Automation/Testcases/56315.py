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
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils

class TestCase(CVTestCase):
    """Class for executing basic testcase for Backup and restore for VMware Cloud director in admin Console"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of VMware Cloud director Different types of full VM OOP restores"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "SourceVDC": None
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
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.org_vdc = self.tcinputs['SourceVDC']
        self.log.info("Created VSA object successfully.")

    def run(self):
        """Main function for testcase execution"""
        try:
            decorative_log("Performing Full VM backup ")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
            try:
                decorative_log("Performing full vm restore to same vDC and same vApp")
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            try:
                decorative_log("Performing full vm restore to same vDC and different vApp")
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.destination_vapp = self.tcinputs['DestinationVapp']
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            try:
                decorative_log("Performing full vm restore to same vDC and new vApp")
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.new_vapp = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            try:
                decorative_log("Performing full vm restore to different vDC and existing vApp")
                self.vsa_obj.destination_vapp = self.tcinputs['DestinationVDCVapp']
                self.vsa_obj.org_vdc = self.tcinputs['DestinationVDC']
                self.vsa_obj.new_vapp = False
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            try:
                decorative_log("Performing full vm restore to different vDC and new vApp")
                self.vsa_obj.new_vapp = True
                self.vsa_obj.destination_vapp = self.tcinputs['DestinationVDCVapp']
                self.vsa_obj.org_vdc = self.tcinputs['DestinationVDC']
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        self.browser.close()
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
        if not self.test_individual_status:
            self.result_string = self.test_individual_failure_message
            self.status = constants.FAILED