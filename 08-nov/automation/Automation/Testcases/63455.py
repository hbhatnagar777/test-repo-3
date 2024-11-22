from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer, AmazonAdminConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of
       Amazon : Verify backup and restore of VPC, subnets, security groups, NICs"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AMAZON  : Amazon VPC backup and restore of entities in same account"
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        """ Setup of basic entities required for testcase"""
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AmazonAdminConsole(self.instance, self.browser, self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        self.vsa_obj.auto_vsa_subclient = VirtualServerUtils.subclient_initialize(self)

    def run(self):
        """AWS VPC regression testcases"""
        try:
            decorative_log("Running a backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
            try:
                decorative_log("Starting cross region restore")
                self.vsa_obj.availability_zone = self.tcinputs['AvailabilityZone']
                self.vsa_obj.aws_vpc_recovery_validation = True
                self.vsa_obj.restore_source_network = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

        finally:
            self.browser.close()

    def cleanup(self, vpc_list):
        """ Perform cleanup of restored network entities"""
        try:
            decorative_log("Starting cleanup of network entities")
            for vpc in vpc_list:
                network = self.vsa_obj.hvobj.get_vpc_entities(vpc, vpc_list[vpc], self.vsa_obj.restore_job_id)
                self.vsa_obj.hvobj.terminate_network(network, vpc_list[vpc])
            decorative_log("Deletion of network entities successful")
        except Exception as _exception:
            self.log.info("Exception in cleaning network entities")
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tear down after test case execution"""
        decorative_log("Tear Down Started")
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
            vpc_list = {}
            vm_list = self.vsa_obj.auto_vsa_subclient.vm_list
            restore_prefix = self.vsa_obj.vm_restore_prefix
            for vm in vm_list:
                restore_vm = str(restore_prefix) + str(vm)
                region = self.vsa_obj.hvobj.get_instance_region(restore_vm)
                vpc_id = self.vsa_obj.hvobj.get_vpcid(restore_vm, region)
                if vpc_id in vpc_list:
                    continue
                vpc_list[vpc_id] = region
            self.vsa_obj.post_restore_clean_up(source_vm=True, status=self.status)
            self.cleanup(vpc_list)
