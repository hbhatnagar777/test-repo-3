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
import datetime
import time

from Install.installer_constants import DEFAULT_COMMSERV_USER
from Web.AdminConsole.Hub.constants import HubServices, ADTypes
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Application.AD import adpowershell_helper
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Automation.Web.AdminConsole.AD.ad import ADPage , ADClientsPage
from Install import installer_utils
from Install.install_helper import InstallHelper
from AutomationUtils import config, constants
from cvpysdk.commcell import Commcell
from Metallic.hubutils import HubManagement
from Automation.AutomationUtils import machine


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Tenant Onboarding case for Active Directory
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Tenant Onboarding case for Active Directory"
        self.windows_helper = None
        self.machine_name = None
        self.windows_machine = None
        self.install_helper = None
        self.ad_page = None
        self.__driver = None
        self.driver = None
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.hub_dashboard = None
        self.service_catalogue = None
        self.app_type = None
        self.users = None
        self.inc_user = None
        self.app_name = None
        self.installinputs = None
        self.custompkg_directory = None
        self.download_dir = None
        self.adps = None
        self.utils = TestCaseUtils(self)

    def create_tenant(self):
        """Creates tenant to be used in test case"""
        self.hub_utils = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_name = datetime.datetime.now().strftime('ad-Auto-%d-%b-%H-%M')
        current_timestamp = str(int(time.time()))
        self.tenant_user_name = self.hub_utils.create_tenant(
            company_name=self.tenant_name,
            email=f'cvautouser-{current_timestamp}@ad{current_timestamp}.com')

    def setup(self):
        self.create_tenant()    # add the part that will generate tenenet
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=self.tcinputs['commcell_username'],
                                     commcell_password=self.config_json.Install.cs_password)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tenant_user_name,
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.ad
        self.app_type = ADTypes.ad
        self.service_catalogue = ServiceCatalogue(self.admin_console, self.service, self.app_type)
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_service_catalogue()
        self.service_catalogue.start_AD_trial()
        self.driver = self.browser.driver
        self.__driver = self.admin_console.driver
        self.ad_page = ADPage(self.admin_console, self.commcell)
        self.adclientspage = ADClientsPage(self.admin_console)
        # create the custom package dir
        self.download_dir = self.browser.get_downloads_dir()

        self.ad_ps_helper = adpowershell_helper.ADPowerShell(self.ad_page, self.tcinputs['remote_client_ip'],
                                                             ad_username=self.tcinputs['remote_username'],
                                                             ad_password=self.tcinputs['remote_userpassword'])
        self.ad_ps_helper.os_remote_ops("C:\\MetallicDDB", "DELETE_DIR")

        self.utils.reset_temp_dir()
        self.custompkg_directory = self.utils.get_temp_dir()

        self.installinputs = {"commcell": self.commcell,
                              "os_type": "windows",
                              "registering_user": self.tenant_user_name,
                              "registering_user_password": self.tcinputs['registering_user_password'],
                              "remote_clientname": self.tcinputs['remote_clientname'],
                              "remote_username": self.tcinputs['remote_username'],
                              "remote_userpassword": self.tcinputs['remote_userpassword'],
                              "full_package_path": self.download_dir + "\\BackupGateway64.exe"
                              }
        # required for uninstall
        self.install_helper = InstallHelper(self.commcell, tc_object=self)
        self.windows_machine = self.install_helper.get_machine_objects(type_of_machines=1)[0]
        self.machine_name = self.windows_machine.get_hostname()
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)

    def run(self):
        """Main function for test case execution"""
        try:
            self.ad_page.navigate_to_ad_app_on_prem()
            authcode = self.ad_page.extract_authcode()
            self.installinputs["authCode"] = authcode
            self.ad_page.interactive_install_machine(self.installinputs)
            self.ad_page.select_backup_gateway()
            # change package name
            self.installinputs["full_package_path"] = self.download_dir + "\\WindowsSeed64.exe"
            self.ad_page.perform_install_package(hostname=self.installinputs["remote_clientname"],
                                                 installinputs=self.installinputs)
            self.ad_page.create_backup_target(disk_storage_name=self.tenant_name,
                                              storage_loc="C:\\" + self.tenant_name + "_dir")
            self.ad_page.conf_cloud_storage()
            self.ad_page.create_plan(plan_name=self.tenant_name + "plan")

            self.ad_page.conf_service_account(username=self.installinputs["registering_user"],
                                              password=self.installinputs["registering_user_password"])
            self.ad_page.handle_summery_page()
            
            self.log.info(f"Navigating to active directory")
            
            self.navigator.navigate_to_activedirectory()
            self.log.info(f"Backing up the GPO for the subclient {self.subclient}")
            self.adclientspage.select_client(self.client)
            self.admin_console.wait_for_completion()
            self.ad_page.backup(backuptype="Inc")
            self.log.info(f"Incremental Backup is completed")


        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tear Down the function of this test case"""
        self.log.info("tear down function")
        if self.status == constants.FAILED:
            installer_utils.collect_logs_after_install(self, self.windows_machine)
        if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
            self.windows_helper.uninstall_client(delete_client=True)
        Browser.close_silently(self.browser)
        self.hub_utils.deactivate_tenant(self.tenant_name)
        self.hub_utils.delete_tenant(self.tenant_name)
