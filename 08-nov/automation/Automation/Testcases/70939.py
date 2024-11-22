
""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    execute_query()  --  Executes SQL Queries

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

Input Example:
"testcases":    {     "70939": {   "ClientName": "",
                            "SubclientName": "",
                            "BackupsetName": "",
                            "AgentName": "Virtual Server",
                            "InstanceName": "",
                            "snap_engine": "",
                            "destination_datastore": "",
                            "destination_host": "",
                            "offline_backupcopy": "",
                            "VcenterName": "",
                            "VcenterUserName": ""
                         }
                }
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
from AutomationUtils.database_helper import get_csdb
from cvpysdk.job import Job
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Live VM Recovery from Secondary Snap copy using v2 client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of VMware Live Recovery from Secondary Snap copy"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.plan_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "destination_host": None,
            "destination_datastore": None
        }
        self.child_job = """select childjobid from jmjobdatalink where parentjobId={a}"""
        self._csdb = get_csdb()
        self.secondary_snap_copy_name = """select name from archGroupCopy where archgroupid=(select id from archGroup
                 where name ='{a}') and isSnapCopy=1 and name!= 'Primary snap' and copy=3"""
        self.primary_snap_name = """select name from archGroupCopy where archgroupid = (select id from archGroup
         where name ='{b}') and isSnapCopy = 1 and copy=1"""
        self.vsa_sc_obj = None

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
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)
        self.vsa_sc_obj = VsaSubclientDetails(self.admin_console)

    def execute_query(self, query, my_options=None, fetch_rows='all'):
        """ Executes SQL Queries
            Args:
                query           (str)   -- sql query to execute

                my_options      (dict)  -- options in the query
                default: None

                fetch_rows      (str)   -- By default return all rows, if not return one row
            Return:
                    str : first column of the sql output

        """
        if my_options is None:
            self._csdb.execute(query)
        elif isinstance(my_options, dict):
            self._csdb.execute(query.format(**my_options))

        if fetch_rows != 'all':
            return self._csdb.fetch_one_row()[0]
        return self._csdb.fetch_all_rows()

    def run(self):
        """Main function for test case execution"""

        try:
            decorative_log("*" * 10 + "Created VSA object successfully. Now starting a Snap backup" + "*" * 10)
            self.vsa_obj.generate_testdata = True
            self.vsa_obj.skip_testdata = False
            self.vsa_obj.backup_method = "Regular"
            decorative_log("*" * 10 + " VSA Snap Backup " + "*" * 10)
            if "skip_pre_backup_config" in self.tcinputs.keys():
                self.vsa_obj.run_pre_backup_config_checks = not self.tcinputs['skip_pre_backup_config']
            backup_jobid = self.vsa_obj.backup()
            parent_jobid = self.vsa_obj.backup_job
            self.admin_console.refresh_page()

            # Run Auxiliary copy Job
            self.vsa_obj.run_auxiliary_copy(self.vsa_obj.storage_policy.storage_policy_name)

            # Restoring the VM using Live Recovery
            decorative_log("*" * 10 + " Live Recovery " + "*" * 10)
            if self.tcinputs.get('RedirectDatastore'):
                self.vsa_obj.redirect_datastore = self.tcinputs['RedirectDatastore']
            if self.tcinputs.get('Datastore'):
                self.vsa_obj.datastore = self.tcinputs['Datastore']
            if self.tcinputs.get('Replication Target'):
                self.vsa_obj.restore_client = self.tcinputs['Replication Target']
            if self.tcinputs.get('DelayMigration'):
                self.vsa_obj.delay_migration = self.tcinputs['DelayMigration']
            try:
                decorative_log("*" * 10 + "Restoring the VM out-of-place from Secondary snap copy" + "*" * 10)
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.live_recovery = True
                self.vsa_obj.secondary_snap_restore = True
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore(vm_level=True)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                decorative_log("*" * 10 + "Running Backup Copy from Secondary snap copy " + "*" * 10)
                sec_copy_name = self.execute_query(self.secondary_snap_copy_name,
                                                   {'a': self.vsa_obj.storage_policy.storage_policy_name})[0][0]
                self.vsa_obj.change_source_for_backupcopy(self.vsa_obj.storage_policy.storage_policy_name, sec_copy_name)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            bkpcpy_job = self.vsa_obj.backup_copy()
            job_details = self.vsa_obj.get_job_status(bkpcpy_job)
#
            try:
                decorative_log("*" * 10 + "In-place Full VM Restore from Secondary snap copy" + "*" * 10)
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.live_recovery = False
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.secondary_snap_restore = True
                self.vsa_obj.full_vm_restore(vm_level=True)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            self.admin_console.refresh_page()
            try:
                Pri_copy_name = self.execute_query(self.primary_snap_name,
                                                   {'b': self.vsa_obj.storage_policy.storage_policy_name})[0][0]
                self.vsa_obj.change_source_for_backupcopy(self.vsa_obj.storage_policy.storage_policy_name, Pri_copy_name)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            self.vsa_obj.delete_snap_array(parent_jobid)
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
                self.vsa_obj.post_restore_clean_up(status=self.test_individual_status)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.browser.close_silently(self.browser)