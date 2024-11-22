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

    setup()         -- sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  cleans up the element created during test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware CI test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of VMware Content Indexing Search in AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.ADMINCONSOLE
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None

    def setup(self):
        """
        Sets up the variables required for running the test case
        """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating the login object")
        login_obj = LoginMain(self.browser.driver, self.csdb)
        login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                        self.inputJSONnode['commcell']['commcellPassword']
                        )
        self.log.info("Login completed successfully. Creating object for VSA")

        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser.driver,
                                                 self.commcell, self.csdb)

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']

            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.ci_enabled = True
            self.vsa_obj.backup()

            for vm_name in self.vsa_obj.vms:
                self.vsa_obj.virtual_machines_obj.navigate_to_virtual_machines()
                self.vsa_obj.virtual_machines_obj.open_vm(vm_name)
                self.vsa_obj.vm_details_obj.vm_search_content("xls")
                self.vsa_obj.vsa_search_obj.validate_file_types("xls")

                self.vsa_obj.vsa_search_obj.search_for_content("xls", "Matrix", file_type='Office')
                self.vsa_obj.vsa_search_obj.validate_contains("Matrix")

                self.vsa_obj.vsa_search_obj.search_for_content(contains="ContentIndexing",
                                                               include_folders=True)
                self.vsa_obj.vsa_search_obj.validate_folders()
                self.vsa_obj.vsa_search_obj.select_data_type("Folder")
                self.vsa_obj.vsa_search_obj.validate_contains("ContentIndexing", name=False,
                                                              folder=True)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.browser.close()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
