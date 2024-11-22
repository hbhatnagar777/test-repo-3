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

    download_ova()          --  downloads the OVA from the commvault store

    ova_deploy_validate()   --  deploys the OVA in the given vcenter

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Reports.storeutils import StoreUtils
from VirtualServer.Deployment.deployment_helper import DeploymentHelper


class TestCase(CVTestCase):
    """Class for executing Commvault OVA from store test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Store: VMware OVA download and deployment"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.VMPROVISIONING
        self.browser = None
        self.driver = None
        self.download_directory = None
        self.store: StoreApp = None
        self.webconsole: WebConsole = None
        self.utils = StoreUtils(self)
        self.config = StoreUtils.get_store_config()
        self.tcinputs = {
            "servicePack": None,
            "vCenter": None,
            "vCenterUsername": None,
            "vCenterPassword": None,
            "esx": None,
            "datastore": None,
            "network": None
        }

    def init_tc(self):
        """
        Initializes the testcase related paramters and opens the browser
        """
        try:
            self.download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory is %s", self.download_directory)

            self.log.info("Initializing browser objects")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.download_directory)
            self.browser.open()

            self.driver = self.browser.driver
            self.driver.get("http://######")

            self.webconsole = WebConsole(self.browser, "######")
            self.store = StoreApp(self.webconsole)
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    @test_step
    def download_ova(self):
        """
        Downloads the ova from the store
        """
        package_name = f"VMWare Image of CommVault Software [v11] " \
                       f"with [SP{self.tcinputs['servicePack']}]"
        self.store.download_package(package_name, "Media Kits",
                                    sub_category="Virtual Appliance",
                                    escape_package_name=True)
        self.utils.wait_for_file_to_download("ova", 10800, 600)

    @test_step
    def ova_deploy_validate(self):
        """
        Deploys the OVA in the given vcenter
        """
        obj = DeploymentHelper(self)
        obj.deploy_vmware_ova()
        obj.validate_vm()

    def run(self):
        """
        Executes the testcase
        """
        try:
            self.init_tc()
            self.download_ova()
            self.ova_deploy_validate()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            Browser.close_silently(self.browser)
