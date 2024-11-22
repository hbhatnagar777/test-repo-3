from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.Common.cvbrowser import BrowserFactory, Browser
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.vm_details import VMDetails
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    def __init__(self):
        """
        Initializes test case class object
         Class for executing VMgroups CRUD case
        """
        super().__init__()
        self.name = "VSA OCI VMgroups CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vm_group_name = "OCI_CRUD_TEST_VMGROUP"
        self.vmgroup_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.tcinputs = {
            "Plan": None,
            "BackupContent": None,
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
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vmgroup_obj = VMGroups(self.admin_console)
        self.vmgroup_details_obj = VMDetails(self.admin_console)

    def run(self):
        try:
            decorative_log("Case 1: Creating VM group %s for hypervisor %s" % (self.vm_group_name, self.tcinputs['ClientName']))
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.add_vm_group(vm_group_name=self.vm_group_name,
                                          vm_content=self.tcinputs['BackupContent'],
                                          hypervisor_name=self.tcinputs['ClientName'],
                                          plan=self.tcinputs['Plan'],
                                          vendor=HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value)

            decorative_log("Validating the newly created VM group %s" % self.vm_group_name)
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vmgroup_name": self.vm_group_name,
                                                          "hypervisor_name": self.tcinputs['ClientName'],
                                                          "plan": self.tcinputs['Plan'],
                                                          "vm_group_content": self.tcinputs['BackupContent']})

            #Update the vm group details
            decorative_log("Case 2: Updating the details of the VM Group %s" % self.vm_group_name)
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.select_vm_group(self.vm_group_name)
            self.vmgroup_details_obj.edit_vm_details(
                vendor=HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE.value,
                proxy_list=self.tcinputs['Updated_proxy_list'],
                tag_name=self.tcinputs['Updated_tag_name'],
                number_of_readers=self.tcinputs['Updated_number_of_readers']
            )
            # Validate the VMGroup
            decorative_log("Validating the updated VM group details")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                             validate_input={
                                                 "tag_name": self.tcinputs['Updated_tag_name'],
                                                 "number_of_readers":self.tcinputs['Updated_number_of_readers'],
                                                 "proxy_list": self.tcinputs['Updated_proxy_list'],
                                             })

            # Delete the vm group
            decorative_log("Case 3: Deleteing the VM group")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)

            # Validate whether hypervisor deleted or not.
            decorative_log("Validating whether VM group got deleted or not.")
            self.admin_console.navigator.navigate_to_vm_groups()
            if not self.vmgroup_obj.has_vm_group(self.vm_group_name):
                self.log.info("VM group doesn't exist")
            else:
                self.log.error("VM group not deleted")
                raise Exception
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
