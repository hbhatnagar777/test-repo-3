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
    __init__()              --  initialize TestCase class

    run()                   --  run function of this test case

    init_tc()               --  initializes the testcase related parameters

"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.AdminConsole.Setup.registration import Registration
from Web.AdminConsole.Setup.login import LoginPage
from Web.AdminConsole.Setup.core_setup import Setup
from Web.AdminConsole.Helper.getting_started_helper import GettingStartedMain


class TestCase(CVTestCase):
    """Class for registering and completed core setup of a new commcell"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AdminConsole: Commvault Product Registration and Setup"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.ADMINCONSOLE
        self.browser = None
        self.driver = None
        self.utils = None
        self.registration = None
        self.login = None
        self.tcinputs = {
            "URL": None,
            "Email": None,
            "Password": None,
            "ServerHostname": None,
            "ServerUsername": None,
            "ServerPassword": None,
            "VirtualMachines": None
        }

    def init_tc(self):
        """
        Initializes the testcase related parameters and opens the browser
        """
        try:
            self.log.info("Initializing browser objects")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.driver = self.browser.driver
            self.driver.get(self.tcinputs['URL'])
            self.utils = StoreUtils(self)

        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    @test_step
    def register_product(self):
        """
        Register the user with the product
        """
        self.registration = Registration(self.driver)
        self.registration.register_existing_account(self.tcinputs["Email"],
                                                    self.tcinputs["Password"])

    @test_step
    def core_setup(self):
        """
        Completes the core setup in a new machine
        Returns:

        """
        self.login = LoginPage(self.driver)
        self.login.login(self.tcinputs['Email'], self.tcinputs['Password'])

        # To complete core setup
        setup = Setup(self.driver)

        # To get started with the configuration
        setup.select_get_started()
        self.log.info('Successfully selected "Getting Started button"')

        # To configure Email
        setup.configure_email(sender_name='CommvaultExpress')
        self.log.info('Successfully configured Email')

        # To add storage pool
        setup.add_storage_pool(
            pool_name='CommvaultExpressPool',
            path=r'C:\CommvaultExpressLibrary',
            partition_path=r'C:\CommvaultExpressLibrary\SIDB')
        self.log.info('Successfully added storage pool')

        # To create server backup plan
        # Using default Admin console values for backup
        setup.create_server_backup_plan()
        self.log.info('Successfully created server backup plan')

        if not setup.core_setup_status():
            raise Exception("Core setup configuration failed. Please check the logs.")

    @test_step
    def vsa_setup(self):
        """
        Complete Virtualization Getting Started
        """
        getting_started = GettingStartedMain(self.driver, self.commcell, self.csdb)
        getting_started.solution = "Virtualization"
        getting_started.vsa_hypervisor_name = self.tcinputs['ServerHostname']
        getting_started.vsa_hostname = self.tcinputs['ServerHostname']
        getting_started.vsa_username = self.tcinputs['ServerUsername']
        getting_started.vsa_password = self.tcinputs['ServerPassword']
        getting_started.vm_group_name = "TestOVA"
        getting_started.virtual_machine_list = self.tcinputs['VirtualMachines'].split(",")

        getting_started.complete_vsa_setup()

    def run(self):
        """
        Executes the testcase
        """
        try:
            self.init_tc()
            self.register_product()
            self.core_setup()
            self.vsa_setup()
            self.login.logout()
        except Exception as exp:
            if self.login:
                self.login.logout()
            self.utils.handle_testcase_exception(exp)
        finally:
            Browser.close_silently(self.browser)
