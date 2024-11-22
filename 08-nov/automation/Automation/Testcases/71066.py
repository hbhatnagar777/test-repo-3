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
import time

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.credential_manager import Credentials
from AutomationUtils import config
from Install.install_helper import InstallHelper
from Install.bootstrapper_helper import BootstrapperHelper
from Install.installer_constants import DEFAULT_COMMSERV_USER
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing hypervisors CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA HyperV hypervisors CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.client_name = "Auto_02_c"
        self.vm_group_name = "Auto_02"
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.credential_obj = None
        self.config_json = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {

        }

    def setup(self):
        self.log.info("Initializing browser objects")
        self.config_json = config.get_config()
        self.windows_machine = Machine(
            machine_name=self.config_json.Install.vsa_client.machine_host,
            username=self.config_json.Install.vsa_client.machine_username,
            password=self.config_json.Install.vsa_client.machine_password)
        self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                 commcell_username=DEFAULT_COMMSERV_USER,
                                 commcell_password=self.config_json.Install.cs_password)
        self.windows_helper = InstallHelper(self.commcell, self.windows_machine)
        self.machine_name = self.windows_machine.machine_name
        self.silent_install_dict = {
            "csClientName": self.commcell.commserv_name,
            "csHostname": self.commcell.commserv_hostname,
            "authCode": self.commcell.enable_auth_code(),
            "instance": "Instance001"
        }
        self.media_path = BootstrapperHelper("SP" + str(self.commcell.commserv_version),
                                             self.windows_machine).bootstrapper_download_url()

    def login(self):
        """ Logs in to admin console """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.config_json.Install.commserve_client.machine_host)
        self.admin_console.login(
            username=DEFAULT_COMMSERV_USER,
            password=self.config_json.Install.cs_password,
            stay_logged_in=True
            )
        self.hypervisor_details_obj = HypervisorDetails(self.admin_console)

        self.credential_obj = Credentials(self.commcell)
        self.storage_helper = StorageMain(self.admin_console)
        self.plan = Plans(self.admin_console)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def install_vsa(self):
        """ To install VSA agent on client"""
        # Installing VSA on windows client
        try:
            if self.windows_machine.check_registry_exists("Session", "nCVDPORT"):
                self.windows_helper.uninstall_client(delete_client=False)

            self.log.info("Determining Media Path for Installation")
            _service_pack = "SP" + str(self.commcell.commserv_version)
            self.log.info(f"Service Pack used for Installation: {_service_pack}")
            self.log.info(f"Installing fresh windows client on {self.machine_name}")
            self.windows_helper.silent_install(
                client_name=self.config_json.Install.vsa_client.client_name,
                tcinputs=self.silent_install_dict, feature_release=_service_pack,
                packages=['FILE_SYSTEM', 'MEDIA_AGENT', 'VIRTUAL_SERVER'])
            self.log.info("Refreshing Client List on the CS")
            self.commcell.refresh()

            self.log.info("Initiating Check Readiness from the CS")
            if self.commcell.clients.has_client(self.machine_name):
                self.client_obj = self.commcell.clients.get(self.machine_name)
                if self.client_obj.is_ready:
                    self.log.info("Check Readiness of Client is successful")
            else:
                self.log.error("Client failed Registration to the CS")
                raise Exception(f"Client: {self.machine_name} failed registering to the CS, Please check client logs")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def create_storage(self):
        """ To create a storage"""
        self.storage_helper.add_disk_storage(self.config_json.Hypervisor.storage,
                                             self.config_json.Install.commserve_client.client_name,
                                             self.config_json.Hypervisor.location)

    def create_plan(self):
        """To create a plan"""
        self.admin_console.navigator.navigate_to_plan()
        self.plan.create_server_plan(self.config_json.Hypervisor.plan,
                                     {'pri_storage': self.config_json.Hypervisor.storage})

    def create_hypervisor(self):
        """ TO create a hypervisor"""
        self.admin_console = AdminConsole(self.browser, self.config_json.Install.commserve_client.machine_host)
        try:
            # Creating Hyper-V client
            decorative_log("Creating Hyper-V Client")
            self.admin_console.load_properties(self)
            self.hypervisor_ac_obj = Hypervisors(self.admin_console)
            self.hypervisor_ac_obj.add_hypervisor(vendor=hypervisor_type.MS_VIRTUAL_SERVER.value,
                                                  server_name=self.client_name,
                                                  vs_username=self.config_json.Hypervisor.vs_username,
                                                  vs_password=self.config_json.Hypervisor.vs_password,
                                                  proxy_list=self.config_json.Hypervisor.access_node,
                                                  credential=self.config_json.Hypervisor.display_name,
                                                  vm_group_name=self.vm_group_name,
                                                  vm_content=self.config_json.Hypervisor.vm_content,
                                                  plan=self.config_json.Hypervisor.plan,
                                                  host_name=self.config_json.Hypervisor.host_name
                                                  )
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def validate_hypervisor(self):
        # Validate the hypervisor creation
        self.tcinputs['ClientName'] = self.client_name
        self.tcinputs['InstanceName'] = self.config_json.Hypervisor.InstanceName
        self.tcinputs['AgentName'] = self.config_json.Hypervisor.AgentName
        self.tcinputs['BackupsetName'] = self.config_json.Hypervisor.BackupsetName
        self.reinitialize_testcase_info()
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        decorative_log("Validating Hyper-V client created with the inputs")
        self.vsa_obj.validate_hypervisor(self.client_name,
                                         validate_input={"vendor": hypervisor_type.MS_VIRTUAL_SERVER.value,
                                                         "server_name": self.client_name,
                                                         "proxy_list": self.config_json.Hypervisor.access_node,
                                                         "credential": self.config_json.Hypervisor.display_name,
                                                         "vm_group_name": self.vm_group_name,
                                                         "vm_content": self.config_json.Hypervisor.vm_content,
                                                         "plan": self.config_json.Hypervisor.plan,
                                                         "username": self.config_json.Hypervisor.vs_username,
                                                         "hostname": self.config_json.Hypervisor.host_name})

    def uninstall_vsa(self):
        """
        To uninstall VSA on the machine
        """
        self.windows_helper.uninstall_client(delete_client=False)

    def run(self):
        """Run function of this test case"""
        self.login()
        self.install_vsa()
        self.create_storage()
        self.create_plan()
        self.create_hypervisor()
        self.validate_hypervisor()
        self.uninstall_vsa()
        self.logout()