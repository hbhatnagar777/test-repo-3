# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case
(Pave / Repave Attach disk to new azure vm for AWS restore)

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer

from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):

    """Class for executing Pave / Repave Attach disk restore to new azure vm for AWS restore"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the class and variables are set to None"""
        super(TestCase, self).__init__()
        self.name = "Pave / Repave Attach disk to new Azure VM for Aws restore"
        self.browser = None
        self.admin_console = None
        self.vsa_obj = None
        self.utils = None
        self.vsa_obj_azure = None


    def login(self):
        """Logs in to the admin console and initialises it"""
        decorative_log("Initializing browser objects")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, machine=(
            self.inputJSONnode['commcell']['webconsoleHostname']))

        self.admin_console.goto_adminconsole()
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])


    def logout(self):
        """Silent logout"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the various variables and initiates the admin console"""
        try:
            self.utils = TestCaseUtils(self)
            self.login()
            decorative_log("Creating an object for virtual Server helper")
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser, self.commcell, self.csdb)

            vsa_obj_inputs = {
                'restore_as':self.tcinputs['RestoreAs'],
                'hypervisor': self.tcinputs['ClientName'],
                'instance': self.tcinputs['InstanceName'],
                'subclient': self.tcinputs['SubclientName'],
                'storage_account': self.tcinputs['StorageAccount'],
                'resource_group': self.tcinputs['ResourceGroup'],
                'destination_region': self.tcinputs.get('DestinationRegion', None),
                'security_group' : self.tcinputs['SecurityGroup'],
                'azure_user_name' : self.tcinputs['AzureUserName'],
                'azure_password' : self.tcinputs['AzurePassword'],
                'availability_zone': self.tcinputs.get('AvailabilityZone', "Auto"),
                'image_option' : self.tcinputs.get('ImageOption', None),
                'visibility_type': self.tcinputs.get('VisibilityType', None),
                'publisher_type': self.tcinputs.get('PublisherType', None),
                'offer_type': self.tcinputs.get('OfferType', None),
                'plan_type': self.tcinputs.get('PlanType', None),
                'version': self.tcinputs.get('Version', None),
                'private_image':self.tcinputs.get('PrivateImage', None),
                'subclient_obj': self.subclient,
                'restore_client': self.tcinputs["Destination_Virtualization_client"],
                'testcase_obj': self,
                'auto_vsa_subclient': VirtualServerUtils.subclient_initialize(self)
            }

            VirtualServerUtils.set_inputs(vsa_obj_inputs, self.vsa_obj)

        except Exception as exp:
            raise CVTestCaseInitFailure(f"Could not initialise the test case {self.id} "
                                        f"due to following error:\n{str(exp)}")

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Running a backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
            try:
                decorative_log("Starting Attach disk restore to a new Azure vm for AWS restore")
                self.vsa_obj_azure = VirtualServerUtils.create_adminconsole_object(self, is_destination_client=True)
                self.vsa_obj.attach_disk_restore_AWS_to_Azure("New instance", self.vsa_obj_azure)

            except Exception as ex:
                self.utils.handle_testcase_exception(ex)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            self.logout()

    def tear_down(self):
        """Tear down after test case execution"""
        decorative_log("Tear Down Started")
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
