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

    """Class for executing Basic acceptance Test of Vmware To AWS restores"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware to AWS conversion from backupcopy in Hotadd transport mode"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.vsa_obj_aws = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {"Destination_Virtualization_client": None}

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
        self.vsa_obj.restore_client = self.tcinputs["Destination_Virtualization_client"]

    def run(self):

        """Main function for test case execution"""


        try:
            self.vsa_obj.source_client = self.tcinputs["InstanceName"]
            try:
                if self.vsa_obj.source_client == "VMWare":
                    auto_vsa_subclient = VirtualServerUtils.subclient_initialize(self)
                    try:
                        if auto_vsa_subclient.subclient.is_intelli_snap_enabled:
                            self.vsa_obj.backup_type = "FULL"
                            self.vsa_obj.backup_method = "SNAP"
                            self.vsa_obj.backup()
                            try:
                                self.vsa_obj_aws = VirtualServerUtils.create_adminconsole_object(self, is_destination_client = True)
                                self.vsa_obj_aws.source = "Primary"
                                self.vsa_obj_aws.transport_mode = "Commvault HotAdd"
                                self.utils.copy_config_options(self.vsa_obj_aws, "RestoreOptions")
                                self.vsa_obj.full_vm_conversion_restore(self.vsa_obj_aws)
                            except Exception as exp:
                                self.test_individual_status = False
                                self.test_individual_failure_message = str(exp)

                    except Exception as exp:
                        raise  Exception("Intelli Snap is not configured on the subclient, Please enable Snap Configuration and try again", exp)

            except Exception as exp:
                raise Exception("Source Client is not VMWare, Please check the source client vendor and try again", exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
            self.status = constants.FAILED

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            status = False
            if self.status == constants.PASSED:
                status = True
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
            if self.vsa_obj_aws:
                self.vsa_obj_aws.post_conversion_clean_up(status=status)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)