# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.EdgeDrive.edgedrive import EdgeDrivePage

from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    FILE_NAME = "file50750.txt"
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Edge Drive - Public Share- Edit Access"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.profile = None
        self.edge = None
        self.client_machine_obj = None
        self.path_to_file = None
        self.public_link = None
        self.tcinputs = {
            'edgeUser': None,
            'edgeUserPasswd': None,
            'edgeBkpClientName': None,
        }

    def create_test_file(self, file_content):
        """create test file on machine"""
        if self.client_machine_obj.check_file_exists(self.path_to_file):
            self.log.debug("deleting test file %s" % self.path_to_file)
            self.client_machine_obj.delete_file(self.path_to_file)
        self.client_machine_obj.create_file(self.path_to_file, content=file_content)

    def login_and_goto_drive(self):
        """login to webconsole and navigate to edge drive"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.webconsole.login(self.tcinputs['edgeUser'],
                              self.tcinputs['edgeUserPasswd'])
        self.edge = EdgeDrivePage(self.webconsole)
        self.edge.goto_drive()

    @test_step
    def test_step_1(self):
        """create a public share with edit access"""
        try:
            self.login_and_goto_drive()
            self.create_test_file(file_content=self.name)
            self.edge.upload_to_edge([self.path_to_file], self.commcell, self.tcinputs['edgeBkpClientName'])

            self.public_link = self.edge.create_public_link(TestCase.FILE_NAME, share_access_type="edit")

            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def test_step_2(self):
        """download public link and upload new version of the file"""
        try:
            self.edge.download_public_link(self.public_link, TestCase.FILE_NAME)
            self.edge.validate_restore_job(self.commcell, self.tcinputs["edgeBkpClientName"])
            self.edge.wait_for_file_download(TestCase.FILE_NAME)

            self.create_test_file(file_content="new version of the file")
            self.edge.upload_new_version_public_share(self.public_link, self.path_to_file)
            self.edge.validate_backup_job_for_upload(self.commcell, self.tcinputs["edgeBkpClientName"])
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def test_step_3(self):
        """download new version of the file"""
        try:
            self.login_and_goto_drive()
            self.edge.download_file_folder(TestCase.FILE_NAME)
            self.edge.validate_restore_job(self.commcell, self.tcinputs["edgeBkpClientName"])
            downloaded_file = self.client_machine_obj.join_path(self.browser.get_downloads_dir(), TestCase.FILE_NAME)
            if not self.client_machine_obj.compare_checksum(downloaded_file, self.path_to_file):
                self.log.error("downloaded file is not reflecting new version of the file uploaded")
            else:
                self.log.error("Successfully downloaded new version of the file")

            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    def run(self):
        """Main function for test case execution"""
        try:
            self.utils = TestCaseUtils(self)
            self.client_machine_obj = Machine()
            self.path_to_file = self.client_machine_obj.join_path(self.client_machine_obj.tmp_dir,
                                                                  TestCase.FILE_NAME)
            self.test_step_1()
            self.test_step_2()
            self.test_step_3()
        except Exception as err:
            self.utils.handle_testcase_exception(err)

    def tear_down(self):
        """Tear down function"""
        try:
            self.login_and_goto_drive()
            self.edge.delete_file(TestCase.FILE_NAME)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

