from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, machine
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer, AmazonAdminConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Amazon VPC Backup Copy: File level backup and restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AMAZON : Verify file level backup and restore to windows and linux access nodes from backup copy"
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.machines = []
        self.restore_directory = None

    def setup(self):
        """Perform setup for testcase"""
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
        self.restore_directory = "testcase_config_files"

    def instance_file_restore(self):
        """Restore instance configuration files to access nodes"""
        try:
            for access_node in ['windows', 'linux']:
                destination_name = self.tcinputs[access_node + '_proxy']
                destination_machine = machine.Machine(destination_name, self.commcell)
                destination_machine.create_directory(self.restore_directory)
                destination_path = "C:\\" + self.restore_directory if access_node == "windows" \
                                                                   else "/" + self.restore_directory
                self.machines.append(destination_machine)
                self.vsa_obj.instance_configuration_file_restore(destination_name, destination_machine, destination_path)
        except Exception as _exception:
            raise Exception("Exception occurred while trying to restore instance configuration files")

    def run(self):
        """Amazon VPC Backup Copy: File level backup and restore"""
        try:
            decorative_log("Running a full snap backup with backup copy")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup_method = "SNAP"
            self.vsa_obj.backup()

            try:
                self.instance_file_restore()
            except Exception as _exception:
                self.utils.handle_testcase_exception(_exception)

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

        finally:
            self.browser.close()

    def cleanup(self):
        """ Cleaning up restored config files"""
        decorative_log("Starting cleanup of restored instance configuration files")
        try:
            for access_node in self.machines:
                os_info = access_node.os_info.lower()
                destination_path = "C:\\" + self.restore_directory if 'windows' in os_info \
                                                                   else '/' + self.restore_directory
                files = access_node.get_files_in_path(destination_path)
                for file in files:
                    access_node.delete_file(file)
                access_node.remove_directory(self.restore_directory)
            self.admin_console.log.info("Deletion of files successful")
        except Exception:
            raise Exception("Exception in cleaning up of instance configuration files")

    def tear_down(self):
        """Tear down after testcase execution"""
        decorative_log("Tear Down Started")
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
            self.cleanup()
