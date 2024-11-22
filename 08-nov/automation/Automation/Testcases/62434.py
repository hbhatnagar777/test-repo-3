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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of CTRee+ SOLR -
    Full and Incr Backups with restores for windows VM with Linux Proxy."""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "CTRee+ SOLR - Full and Incr Backups with restores for windows VM with Linux Proxy."
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
        self.vsa_obj.test_file_versions = True

    def test_cycle(self):
        self.vsa_obj.backup()
        if self.vsa_obj.is_indexing_v2:
            self.vsa_obj.ctree_file_search_restore()
        else:
            self.log.info("Skipping Ctree search and restore as this is a V1 client")
        self.vsa_obj.solr_file_search_restore()
        self.vsa_obj.ci_validate_deleted_items()
        self.vsa_obj.ci_validate_file_versions()

    def run(self):

        """Main function for test case execution"""

        try:
            try:
                self.vsa_obj.backup_type = "FULL"
                self.test_cycle()
                self.vsa_obj.cleanup_testdata()

                self.vsa_obj.previous_backup_timestamp = self.vsa_obj.timestamp
                self.vsa_obj.backup_type = "Incr"
                self.test_cycle()

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_versions_file = True
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
