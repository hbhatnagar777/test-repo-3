""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from VirtualServer.VSAUtils import  OptionsHelper, VirtualServerUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Live VM Recovery using v2 client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of VMware Live Recovery from Snap backups"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.tpath = None
        self.tstamp = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {

        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient

    def run(self):
        """Main function for test case execution"""

        try:

            auto_subclient = VirtualServerUtils.subclient_initialize( self )
            VirtualServerUtils.decorative_log( "Backup" )
            backup_options = OptionsHelper.BackupOptions( auto_subclient )
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            if backup_options.collect_metadata:
                raise Exception( "Metadata collection is enabled" )
            auto_subclient.backup( backup_options )

            self.tpath= auto_subclient.testdata_path
            self.tstamp=auto_subclient.timestamp
            self.vsa_obj.testdata_path=self.tpath
            self.vsa_obj.timestamp = self.tstamp
            self.vsa_obj.generate_testdata = False
            self.vsa_obj.skip_testdata = True

            self.vsa_obj.vsa_discovery()


            decorative_log("Verifying that File Indexing job runs and completes successfully")
            # Restoring the VM using Live Recovery

            decorative_log("*" * 10 + " Live Recovery " + "*" * 10)

            self.vsa_obj.unconditional_overwrite = True
            self.vsa_obj.live_recovery = True

            if self.tcinputs.get('RedirectDatastore'):
                self.vsa_obj.redirect_datastore = self.tcinputs['RedirectDatastore']
            if self.tcinputs.get('DelayMigration'):
                self.vsa_obj.delay_migration = self.tcinputs['DelayMigration']
            if self.tcinputs.get('Datastore'):
                self.vsa_obj.datastore = self.tcinputs['Datastore']
                self.vsa_obj.recovery_target = True

            try:
                decorative_log("*" * 10 + "Restoring the VM out-of-place" + "*" * 10)
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
                
            try:
                decorative_log("*" * 10 + "Restoring the VM In-place" + "*" * 10)
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.browser.close_silently(self.browser)
