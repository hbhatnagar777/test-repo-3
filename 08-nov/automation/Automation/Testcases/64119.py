
"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --   setup function will create setup objects related to web adminconsole

    run()           --   run function of this test case calls Snaptemplate Class to execute
                            and Validate Below Operations.
                            cleanup,create entities,revert,multi snap mount, multi snap unmount, multi snap delete
    tear_down()     --  tear down function will cleanup

Inputs:

    ClientName          --      name of the client for backup

    StoragePoolName     --      backup location for disk storage

    SnapEngine          --      snap engine to set at subclient

    SubclientContent    --      Data to be backed up

    ArrayName           --     Name of Array
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.snaptemplate import SnapTemplate
from Web.AdminConsole.Components.panel import Backup


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.source_test_data = None
        self.browser = None
        self.admin_console = None
        self.snap_template = None
        self.tcinputs = {
            "ClientName": None,
            "StoragePoolName": None,
            "SnapEngine": None,
            "SubclientContent": None,
            "ArrayName": None
        }
        self.name = """CC Automation : Positive Case: For Multiple Mount, Multiple Unmount, Multiple Delete, Revert Operations
                    (subclient content should be multiple volumes coming from same array)"""

    def setup(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.snap_template = SnapTemplate(self, self.admin_console)
        self.array_name = self.tcinputs['ArrayName']


    def run(self):
        """Main function for test case execution"""

        try:
            if len(self.tcinputs["SubclientContent"].split(",")) <= 1:
                raise Exception("Subclient Content should be multiple paths of different volumes of same array")
            self.snap_template.cleanup()
            self.snap_template.create_entities()
            self.source_test_data = self.snap_template.add_test_data()
            full_jobid = self.snap_template.verify_backup(Backup.BackupType.FULL)
            self.snap_template.revert_snap(full_jobid)
            self.snap_template.mount_snap(job_id=full_jobid, copy_name=self.snap_template.snap_primary)
            self.snap_template.unmount_snap(job_id=full_jobid, copy_name=self.snap_template.snap_primary)
            self.snap_template.reconcile_snapshots(self.array_name)
            self.snap_template.delete_snap(job_id=full_jobid, copy_name=self.snap_template.snap_primary)
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To cleanup entities created during TC"""
        try:
            self.snap_template.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
