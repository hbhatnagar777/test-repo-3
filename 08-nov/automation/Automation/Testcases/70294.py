""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

Input Example:
"testcases":    {     "70294": {
                         "ClientName": "",
                         "SubclientName": "",
                         "Replication Target": "",
                         "BackupsetName": "",
                         "AgentName": "Virtual Server",
                         "InstanceName": "",
                         "Host": "",
                         "MediaAgent": "",
                         "Datastore": "",
                         "SnapAutomationOutput": "",
                         "Network": "VM Network",
                         "Destination network": "Original network",
                         "VMName" : ""
                         }
                }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.VirtualServerHelper import VMwareAdminConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.virtual_machines import VirtualMachines
from Web.AdminConsole.VSAPages.vm_details import VMDetails
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails
from Web.AdminConsole.VSAPages.hypervisors import Hypervisors
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.Components.table import Rtable
import time


class TestCase(CVTestCase):
    """Class for executing List Snapshots at different levels in Command center for Virtual Server agent """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "List Snapshots at different levels in Command center for Virtual Server agent"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tpath = None
        self.tstamp = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "AgentName": None,
            "BackupsetName": None,
            "ClientName": None,
            "Datastore":  None,
            "Destination network":  None,
            "Host":  None,
            "InstanceName":  None,
            "MediaAgent":  None,
            "Network":  None,
            "SnapAutomationOutput":  None,
            "SubclientName":  None,
            "VMName":  None
        }
        self.vmware_obj = None
        self.navigator = None
        self.vms = None
        self.vm = None
        self.vmgs = None
        self.vmg = None
        self.hyps = None
        self.hyp = None
        self.rtable = None
        self.child_job = """select childjobid from jmjobdatalink where parentjobId={a}"""

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)

        decorative_log("Creating an object for Virtual Server helper")
        self.vmware_obj = VMwareAdminConsole(self.instance, self.browser,
                                             self.commcell, self.csdb)
        self.vmware_obj.testcase_obj = self
        self.vmware_obj.hypervisor = self.tcinputs['ClientName']
        self.vmware_obj.instance = self.tcinputs['InstanceName']
        self.vmware_obj.subclient = self.tcinputs['SubclientName']
        self.vmware_obj.subclient_obj = self.subclient
        self.navigator = self.admin_console.navigator
        self.vms = VirtualMachines(self.admin_console)
        self.vm = VMDetails(self.admin_console)
        self.vmgs = VMGroups(self.admin_console)
        self.vmg = VsaSubclientDetails(self.admin_console)
        self.hyps = Hypervisors(self.admin_console)
        self.hyp = HypervisorDetails(self.admin_console)
        self.rtable = Rtable(self.admin_console)

    def list_snapshots_vms_level(self, vmname, jobid):
        """
         list of Snapshots from action item of a particular vm at vms level
         Virtualization ->Virtual machines -> VM Actions button -> List snapshots
         args:
             vmname : name of the vm
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots from action item of a particular vm at vms level" + "*" * 20)
        self.navigator.navigate_to_virtual_machines()
        self.rtable.search_for(vmname)
        self.vms.action_list_snapshots(vmname)
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_vm_level(self, vmname, jobid):
        """
         list of Snapshots from action item of a particular vm at vmdetails or vmlevel
         Virtualization ->Virtual machines -> Click on VM details -> Actions -> List Snapshots
         args:
             vmname : name of the vm
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots from action item of a particular vm at vmdetails or vmlevel"
                      + "*" * 20)
        self.navigator.navigate_to_virtual_machines()
        self.rtable.search_for(vmname)
        self.vms.open_vm(vmname)
        self.vm.action_list_snapshots()
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_vmgs_level(self, vmgroup, jobid):
        """
         list of Snapshots from action item of a particular vmgroup at vmgroups level
         Virtualization ->VM groups -> Select VM group -> VM group action button -> List Snapshots
         args:
             vmgroup : name of the vmgroup
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots from action item of a particular vmgroup at vmgroups level"
                      + "*" * 20)
        self.navigator.navigate_to_vm_groups()
        self.rtable.search_for(vmgroup)
        self.vmgs.action_list_snapshots(vmgroup)
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_vmg_level(self, vmgroup, jobid):
        """
         list of Snapshots from action item of a particular vmgroup at vmgroup details level
         Virtualization ->VM groups -> Select VM group -> Click on VM group details -> Actions -> List Snapshots
         args:
             vmgroup : name of the vmgroup
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots from action item of a particular vmgroup at vmgroup details level"
                      + "*" * 20)
        self.navigator.navigate_to_vm_groups()
        self.rtable.search_for(vmgroup)
        self.vmgs.select_vm_group(vmgroup)
        self.vmg.action_list_snapshots()
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_hyp_vms_level(self, hyp, vmname, jobid):
        """
         list of Snapshots from action item of a particular vm at Hypervisor level
         Virtualization -> Hypervisors -> Select Hypervisor -> Virtual Machine -> VM action button -> List Snapshots
         args:
             hyp: name of the Hypervisor
             vmname : name of the vm
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots from action item of a particular vm at Hypervisor level" + "*" * 20)
        self.hyps.select_hypervisor(hyp)
        self.hyp.select_vm_tab()
        self.rtable.search_for(vmname)
        self.hyp.action_list_snapshots(entity=vmname)
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_hyp_vm_level(self, hyp, vmname, jobid):
        """
         list of Snapshots of a particular vm details page from Hypervisor level
         Virtualization -> Hypervisors -> Select Hypervisor -> Virtual Machine -> Click on VM details -> Actions
          -> List Snapshots
         args:
             hyp: name of the Hypervisor
             vmname : name of the vm
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots of a particular vm details page from Hypervisor level" + "*" * 20)
        self.hyps.select_hypervisor(hyp)
        self.hyp.select_vm_tab()
        self.rtable.search_for(vmname)
        self.vms.open_vm(vmname)
        self.vm.action_list_snapshots()
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_hyps_vmgs_level(self, hyp, vmgroup, jobid):
        """
         list of Snapshots from action item of a particular vmgroup at Hypervisors level
         Virtualization ->VM groups -> Select Hypervisor -> VM groups -> VM group action button -> List Snapshots
         args:
             hyp: name of the Hypervisor
             vmgroup : name of the vmgroup
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots from action item of a particular vmgroup at Hypervisors level"
                      + "*" * 20)
        self.hyps.select_hypervisor(hyp)
        self.hyp.select_vmgroup_tab()
        self.rtable.search_for(vmgroup)
        self.hyp.action_list_snapshots(entity=vmgroup)
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def list_snapshots_hyp_vmg_level(self, hyp, vmgroup, jobid):
        """
         list of Snapshots of a particular vmgroup details page from Hypervisor level
         Virtualization -> Hypervisors -> Select Hypervisor -> VM groups -> Click on VM group details -> Actions
          -> List Snapshots
         args:
             hyp: name of the Hypervisor
             vmgroup : name of the vmgroup
             jobid : jobid of snap which needs to checked
        """
        self.log.info("*" * 20 + "list of Snapshots of a particular vmgroup details page from Hypervisor level" +
                      "*" * 20)
        self.hyps.select_hypervisor(hyp)
        self.hyp.select_vmgroup_tab()
        self.rtable.search_for(vmgroup)
        self.vmgs.select_vm_group(vmgroup)
        self.vmg.action_list_snapshots()
        self.rtable.search_for(jobid)
        if self.rtable.get_total_rows_count(jobid) < 1:
            raise Exception("No snap jobs available, check manually")

    def run(self):
        """Main function for test case execution"""

        try:
            self.vmware_obj.generate_testdata = True
            self.vmware_obj.skip_testdata = False
            self.vmware_obj.backup_method = "Regular"
            vmname = self.tcinputs['VMName']
            vmgroup = self.tcinputs['SubclientName']
            hypervisor = self.tcinputs['ClientName']
            decorative_log("*" * 10 + " VSA Snap Backup " + "*" * 10)
            if "skip_pre_backup_config" in self.tcinputs.keys():
                self.vmware_obj.run_pre_backup_config_checks = not self.tcinputs['skip_pre_backup_config']
            self.vmware_obj.backup()
            parent_jobid = self.vmware_obj.backup_job
            child_jobid = self.vmware_obj.execute_query(self.child_job, {'a': parent_jobid})
            child_jobid = child_jobid[0][0]
            self.vmware_obj.mount_snap(parent_jobid)
            self.vmware_obj.unmount_snap(parent_jobid)
            self.list_snapshots_vms_level(vmname=vmname, jobid=child_jobid)
            self.list_snapshots_vm_level(vmname=vmname, jobid=child_jobid)
            self.list_snapshots_vmgs_level(vmgroup=vmgroup, jobid=parent_jobid)
            self.list_snapshots_vmg_level(vmgroup=vmgroup, jobid=parent_jobid)
            self.list_snapshots_hyp_vms_level(hyp=hypervisor, vmname=vmname, jobid=child_jobid)
            self.list_snapshots_hyp_vm_level(hyp=hypervisor, vmname=vmname, jobid=child_jobid)
            self.list_snapshots_hyps_vmgs_level(hyp=hypervisor, vmgroup=vmgroup, jobid=parent_jobid)
            self.list_snapshots_hyp_vmg_level(hyp=hypervisor, vmgroup=vmgroup, jobid=parent_jobid)
            self.vmware_obj.delete_snap_array(parent_jobid)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        try:
            if self.vmware_obj:
                self.vmware_obj.cleanup_testdata()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        self.browser.close_silently(self.browser)
