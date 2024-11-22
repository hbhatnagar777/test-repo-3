""""
Main file for executing this test case
TestCase is the only class definied in this file
TestCase: Class for executing this test case

TestCase:
    __init__()  --  Initialize test case class object

    run()       --  Main function for test case execution
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.unixsnaphelper import UnixSnapHelper

class TestCase(CVTestCase):
    """Unix snap for IRISDB"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Snap Backup - LVM testing scenario - Striped LV for Snap'
        self.tcinputs = {
            "SubclientContent": None,
            "ScanType": None,
            "MediaAgentName": None,
            "RestoreLocation": None,
            "DiskLibLocation": None,
            "SnapEngine": None,
            "IsIris": None,
            "IrisSourcePath": None,
            "BackupsetName": None,
            "SubclientName": None
            }
        self.instant_clone_options = {}

    def run(self):
        """Main function for test case execution"""
        log = self.log

        try:
            log.info("Started executing %s test case", format(self.id))
            snap_helper = UnixSnapHelper(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper.iris_template(is_single_iris_instance=True, instant_clone_options=self.instant_clone_options)
            self.status = constants.PASSED
        except Exception as excp:
            log.error('Failed with error: [%s]', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            snap_helper.cleanup()
        