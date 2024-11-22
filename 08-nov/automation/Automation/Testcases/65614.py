from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.adminconsole import AdminConsole
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    def __init__(self):
        """
        Initializes test case class object
        Class for executing Hypervisors CRUD case
        """
        super().__init__()
        self.name = "VSA OCI Hypervisors CRUD case"
        self.browser = None
        self.admin_console = None
        self.hypervisor_details_obj=None
        self.client_name = "OCI CRUD Auto HYP"
        self.vsa_obj = None
        self.tcinputs={
            "VM_Content": None
        }

    def setup(self):
        """
        Method to setup test variables
        """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.admin_console.navigator.navigate_to_virtualization()



    def run(self):
        try:
            self.hypervisor_ac_obj = Hypervisors(self.admin_console)
            self.hypervisor_details_obj = HypervisorDetails(self.admin_console)
            self.hypervisor_ac_obj.select_add_hypervisor()
            self.hypervisor_ac_obj.add_hypervisor(vendor=hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value,
                                                  server_name=self.client_name,
                                                  credential=self.tcinputs['Credential'],
                                                  regions=self.tcinputs['Regions'],
                                                  proxy_list=self.tcinputs['Proxy_List'],
                                                  vm_group_name=self.tcinputs['VM_Group_Name'],
                                                  vm_content=self.tcinputs['VM_Content'],
                                                  plan=self.tcinputs['Plan']
                                                  )

            self.tcinputs['ClientName'] = self.client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            decorative_log("Validating hypervisor %s that was created" % self.client_name)
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={
                                                 "vendor": hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value,
                                                 "server_name": self.client_name,
                                                 "credential": self.tcinputs['Credential'],
                                                 "regions": self.tcinputs['Regions'],
                                                 "proxy_list": self.tcinputs['Proxy_List'],
                                                 "vm_group_name": self.tcinputs['VM_Group_Name'],
                                                 "vm_content": self.tcinputs['VM_Content'],
                                                 "plan": self.tcinputs['Plan']})

            decorative_log("Updating Credential,FREL,Proxy,Tag_Name of the hypervisor")
            self.hypervisor_ac_obj.select_hypervisor(self.client_name)
            self.hypervisor_details_obj.edit_hypervisor_details(
                vendor=hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value,
                credential=self.tcinputs['Updated_Credential'],
                frel=self.tcinputs['Updated_FREL'],
                proxy_list=self.tcinputs['Updated_Proxy_List'],
                tag_name=self.tcinputs['Updated_Tag_Name']
                )
            # Validate the hypervisor
            self.tcinputs['ClientName'] = self.client_name
            self.reinitialize_testcase_info()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            decorative_log("Validating admin hypervisor")
            self.vsa_obj.validate_hypervisor(self.client_name,
                                             validate_input={
                                                 "vendor": hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value,
                                                 "credential": self.tcinputs['Updated_Credential'],
                                                 "proxy_list": self.tcinputs['Updated_Proxy_List'],
                                                 "frel": self.tcinputs['Updated_FREL'],
                                                 "tag_name": self.tcinputs['Updated_Tag_Name'],
                                                 })

            decorative_log("Deleting hypervisor %s" % self.client_name)
            self.admin_console.navigator.navigate_to_hypervisors()
            self.hypervisor_ac_obj.retire_hypervisor(self.client_name)

            decorative_log("Checking for deleted hypervisor")
            self.admin_console.navigator.navigate_to_hypervisors()
            if not self.hypervisor_ac_obj.is_hypervisor_exists(self.client_name):
                self.log.info("Hypervisor doesn't exist")
                pass
            else:
                self.log.error("Hypervisor not deleted")
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
