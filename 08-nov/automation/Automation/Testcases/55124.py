# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Running a backup and restore on from File Server page for verifying MongoDB caching

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.file_servers_helper import FileServersMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Verify backup and restore for a freshly installed File Server"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.fs_helper_obj = None
        self.tcinputs = {
            "client_name": None,
            "client_hostname": None,
            "backupset_name": None,
            "subclient_name": None,
            "subclient_content": None,
            "plan": None
        }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.fs_helper_obj = FileServersMain(self.admin_console, self.commcell, self.csdb)

    def run(self):

        try:

            self.fs_helper_obj.client_name = self.tcinputs['client_name']
            self.fs_helper_obj.client_hostname = self.tcinputs['client_hostname']
            self.fs_helper_obj.subclient_content = self.tcinputs['subclient_content']
            self.fs_helper_obj.client_plan = self.tcinputs['plan']

            file_no = 0
            content_creation_attempts = 3
            while content_creation_attempts > 0:
                try:
                    self.fs_helper_obj.create_subclient_content(f"file{file_no}", file_size=51200000)
                    break
                except Exception as exp:
                    self.log.info(exp)
                    time.sleep(180)
                    content_creation_attempts -= 1
                    if content_creation_attempts != 0:
                        pass

            self.fs_helper_obj.file_server_backup_subclient(backup_level="Full")
            self.fs_helper_obj.validate_file_server_details(flag=1)
            self.fs_helper_obj.restore_file_server()

            backup_jobs = 2
            while backup_jobs > 0:
                file_no += 1
                filename = f"file{file_no}"
                self.fs_helper_obj.create_subclient_content(file_name=filename, file_size=10240000)
                self.fs_helper_obj.file_server_backup_subclient(backup_level="incremental")
                self.fs_helper_obj.validate_file_server_details(flag=1)
                backup_jobs -= 1

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.fs_helper_obj.release_license()
            self.fs_helper_obj.delete_client()

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
