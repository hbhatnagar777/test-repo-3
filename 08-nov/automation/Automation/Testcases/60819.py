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
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of  v2-Snap - CTRee+ SOLR - Synthfull Backups with restores."""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2-Snap - CTRee+ SOLR - Synthfull Backups with restores."
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {}

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
        self.vsa_obj = VirtualServerUtils.create_adminconsole_object(self)
        self.vsa_obj.ci_enabled = True
        self.vsa_obj.verify_ci = True
        if self.vsa_obj.instance.lower() == hypervisor_type.AZURE_V2.value.lower():
            self.vsa_obj.pre_backup_config_checks = \
                {**self.vsa_obj.pre_backup_config_checks,
                 **{
                    "min_proxy_os": {"count": 2, "os_list": ["unix", "windows"], "validate": True},
                    'multiple_disk_encryption': {"validate": False},
                    'vm_encryption_info': {'validate': False}
                 }}

    def test_cycle(self):
        self.vsa_obj.backup()
        self.vsa_obj.ctree_file_search_restore()
        self.vsa_obj.solr_file_search_restore()

    def run(self):

        """Main function for test case execution"""

        try:
            if not self.vsa_obj.is_indexing_v2:
                self.log.info("Please provide an Indexing V2 client for this testcase")
                self.log.error(f"Client {self.tcinputs['ClientName']} is not an Indexing V2 client")
                raise Exception(f"Client {self.tcinputs['ClientName']} is not an Indexing V2 client")
            else:
                self.vsa_obj.backup_type = "SYNTH"
                self.vsa_obj.backup_method = "SNAP"
                self.test_cycle()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_versions_file = True
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.log.error(f"Error in tear_down: {exp}")
