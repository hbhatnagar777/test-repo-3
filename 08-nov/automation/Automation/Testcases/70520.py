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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import os

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.drbackup_helper import DRValidateHelper
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object """
        super(TestCase, self).__init__()
        self.download_path = None
        self.name = "validate DR Backup run, Restore and Download functionality."
        self.browser = None
        self.admin_console = None
        self.drbackup_helper = None
        # tcinputs : list of database name eg.:["AppStudioDB", "CVCloud", "HistoryDB", "CacheDB", "UsageHistoryDB"]
        self.tcinputs = {
            "download_filenames": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.log.info("executing testcase")
        self.browser = BrowserFactory().create_browser_object()
        self.download_path = os.path.join(constants.TEMP_DIR, str(self.id), "Downloads")
        self.log.info("Setting browser download path to : " + self.download_path)
        self.browser.set_downloads_dir(self.download_path)
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.drbackup_helper = DRValidateHelper(
            admin_console=self.admin_console,
            commcell=self.commcell,
            client_name=self.commcell.commserv_client
        )

    def run(self):
        """Run function of this test case"""
        try:
            self.drbackup_helper.validate(test_list={'validate_run_DRBackup': {'job_types': ['full', 'Differential']},
                                                     'validate_dbbackup_restore': {},
                                                     'validate_drbackup_download': {
                                                         "download_path": self.download_path,
                                                         "download_filenames": self.tcinputs['download_filenames']
                                                     }})

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.browser.close()
        # remove temp directory
        if os.path.exists(self.download_path):
            # Iterate over all the files in the directory
            for filename in os.listdir(self.download_path):
                file_path = os.path.join(self.download_path, filename)
                # Check if it's a file and not a directory
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        self.log.info(f"Removed file {file_path}")
                    except Exception as exp:
                        self.log.error(f"Failed to remove file {file_path} due to {str(exp)}")