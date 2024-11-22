# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Security.userhelper import UserHelper
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.EdgeDrive.edgedrive import EdgeDrivePage

from Web.Common.page_object import TestStep

import time

class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    FILE_NAME = "file50748.txt"
    password = '######'
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Edge Drive - Private Share Test- Edit Access"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.edge = None
        self.user1 = None
        self.path_to_file = None
        self.client_machine_obj = None
        self.user_helper = None
        self.tcinputs = {
            'edgeUser': None,
            'edgeUserPasswd': None,
            'UserEmailId': None,
            'edgeBkpClientName': None,
        }

    def create_test_file(self, file_content):
        """ create test file on machine
        Args:
            file_content (str)          -- Content of the file to write

        Returns:
            None
        """
        if self.client_machine_obj.check_file_exists(self.path_to_file):
            self.log.debug("deleting test file %s" % self.path_to_file)
            self.client_machine_obj.delete_file(self.path_to_file)
        self.client_machine_obj.create_file(self.path_to_file, content=file_content)

    def init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.utils = TestCaseUtils(self)
            self.client_machine_obj = Machine()
            self.path_to_file = self.client_machine_obj.join_path(self.client_machine_obj.tmp_dir,
                                                                  TestCase.FILE_NAME)
            self.browser = BrowserFactory().create_browser_object()
            
            # create galaxy user and associate it to edge drive user
            self.user_helper = UserHelper(self.commcell)
            self.user1 = '{0}_Automation_User1'.format(self.id)
            if not self.commcell.users.has_user(user_name=self.user1):
                self.log.info("creating galaxy user %s" % self.user1)
                self.user_helper.create_user(user_name=self.user1,
                                             full_name=self.user1,
                                             password=TestCase.password,
                                             email=self.tcinputs['UserEmailId'])
            else:
                self.log.warning("user %s already exists" % self.user1)

            user_association = {
                'assoc1':
                    {
                        'userName': [self.user1],
                        'role': ['View']
                    }
            }
            self.user_helper.modify_security_associations(user_association,
                                                          self.tcinputs['edgeUser'])

            # create test file
            self.create_test_file(file_content=self.name)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def test_step_1_2(self):
        """create a private share and check if it is present in shared by me link"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.webconsole.login(self.tcinputs['edgeUser'],
                                  self.tcinputs['edgeUserPasswd'])
            self.edge = EdgeDrivePage(self.webconsole)
            self.edge.goto_drive()
            self.edge.upload_to_edge([self.path_to_file], self.commcell, self.tcinputs['edgeBkpClientName'])

            self.edge.create_private_share(TestCase.FILE_NAME, self.user1, edit_user_priv=True)
            self.log.info("private share created successfully")
            files = self.edge.files_in_share_folder_link("shared_by_me")
            if TestCase.FILE_NAME.split(".")[0] not in files:
                raise CVTestStepFailure("file %s not present in share by Me link" % TestCase.FILE_NAME)

            self.log.info("file %s present in share by Me link" % TestCase.FILE_NAME)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def test_step_3(self):
        """Verify download of private share file and with edit access can upload new version of the file"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.webconsole.login(self.user1,
                                  TestCase.password)
            self.edge = EdgeDrivePage(self.webconsole)
            self.webconsole.goto_mydata()

            files = self.edge.files_in_share_folder_link("shared_with_me", download_file=TestCase.FILE_NAME)
            if TestCase.FILE_NAME.split(".")[0] not in files:
                raise CVTestStepFailure("file %s not present in share with Me link" % TestCase.FILE_NAME)

            self.log.info("file %s present in shared with Me link for user %s" % (TestCase.FILE_NAME, self.user1))
            self.edge.wait_for_file_download(TestCase.FILE_NAME, self.browser.get_downloads_dir())

            # verify if we can upload new version as it is edit private link
            self.create_test_file(file_content="uploading new version")
            self.edge.upload_new_version_private_share(TestCase.FILE_NAME, self.path_to_file)
            self.edge.validate_backup_job_for_upload(self.commcell, self.tcinputs["edgeBkpClientName"])

            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def test_step_4(self):
        """check if owner of the share can see the latest version of file and can delete private share link"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.webconsole.login(self.tcinputs['edgeUser'],
                                  self.tcinputs['edgeUserPasswd'])
            self.edge = EdgeDrivePage(self.webconsole)
            self.edge.goto_drive()

            self.edge.download_file_folder(TestCase.FILE_NAME)
            self.edge.validate_restore_job(self.commcell, self.tcinputs["edgeBkpClientName"])
            downloaded_file = self.client_machine_obj.join_path(self.browser.get_downloads_dir(), TestCase.FILE_NAME)
            if not self.client_machine_obj.compare_checksum(downloaded_file, self.path_to_file):
                self.log.error("downloaded file is not reflecting new version of the file uploaded")
            else:
                self.log.info("Successfully downloaded new version of the file")

            self.edge.delete_private_share(TestCase.FILE_NAME)
            self.log.info("Private share is deleted successfully by user %s" % self.user1)
            files = self.edge.files_in_share_folder_link("shared_by_me")
            if TestCase.FILE_NAME in files:
                raise CVTestStepFailure("file %s still present in shared by Me link" % TestCase.FILE_NAME)
            self.log.info("file %s is removed in shared by Me link" % TestCase.FILE_NAME)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.test_step_1_2()
            self.test_step_3()
            self.test_step_4()
        except Exception as err:
            self.utils.handle_testcase_exception(err)

    def tear_down(self):
        """Tear down function"""
        try:
            self.user_helper.delete_user(self.user1, self.inputJSONnode['commcell']['commcellUsername'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.webconsole.login(self.tcinputs['edgeUser'],
                                  self.tcinputs['edgeUserPasswd'])
            self.edge = EdgeDrivePage(self.webconsole)
            self.edge.goto_drive()
            self.edge.delete_file(TestCase.FILE_NAME)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

