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
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware enduser restores"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware to OCI conversion using Linux proxy"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
        "Destination_Virtualization_client": None
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

        decorative_log("Creating an object for Virtual Server helper for VMWare")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.testcase_obj = self
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.restore_client = self.tcinputs["Destination_Virtualization_client"]


    def run(self):
        """Main function for test case execution"""

        try:
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                decorative_log("Initialize helper objects for OCI")
                if 'Destination_Virtualization_client' in self.tcinputs:
                    self.log.info("Create client object for: %s", self.tcinputs['Destination_Virtualization_client'])
                    oci_client = self.commcell.clients.get(self.tcinputs['Destination_Virtualization_client'])
                self.log.info("Create agent object for: %s",'Virtual Server') 
                oci_agent = oci_client.agents.get('Virtual Server')
                self.log.info("Create instance object for: %s", 'Oracle Cloud Infrastructure') 
                oci_instance = oci_agent.instances.get('Oracle Cloud Infrastructure')
                self.log.info("Creating subclient object for: %s", 'default')
                oci_subclient = oci_instance.subclients.get('default') 

                decorative_log("Creating an object for Virtual Server helper for OCI")
                self.vsa_obj_oci = AdminConsoleVirtualServer(oci_instance, self.browser,
                                                         self.commcell, self.csdb)
                self.vsa_obj_oci.subclient_obj = oci_subclient
                self.vsa_obj_oci.testcase_obj = self
                self.vsa_obj_oci.hypervisor = self.tcinputs['Destination_Virtualization_client']
                self.vsa_obj_oci.instance = oci_instance.name
                self.vsa_obj_oci.subclient = oci_subclient.name 
                self.vsa_obj_oci.auto_vsa_subclient.validate_inputs(proxy_os="linux",update_qa=self.update_qa)
                self.vsa_obj_oci.unconditional_overwrite = True
                self.vsa_obj_oci.conversion_restore = True
                self.vsa_obj_oci.staging_bucket = self.tcinputs["staging_bucket"]
                # self.vsa_obj_oci.oci_shape = self.tcinputs["shape"] #Put this set cross region parameters function
                self.vsa_obj.full_vm_conversion_restore(self.vsa_obj_oci)
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
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status=self.status)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)