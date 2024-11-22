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
from AutomationUtils import logger

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.EdgeDrive.edgedrive import EdgeDrivePage

from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    FILE_NAME = "test50490"
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Edge Drive - Restore to client and network Path"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.edge = None
        self.upload_path = None
        self.file_folder_name = None
        self.log = logger.get_log()

        self.tcinputs = {
            'edgeUser': None,
            'edgeUserPasswd': None,
            'edgeClientName': None,
            'RestoreClientName': None,
            'NetworkPath': None,
            'UNCClientName': None,
            'UNCUserName': None,
            'UNCPassword': None,
            'RestoreNW_link_path': None
        }

    def init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.webconsole.login(self.tcinputs['edgeUser'],
                                  self.tcinputs['edgeUserPasswd'])
            self.edge = EdgeDrivePage(self.webconsole)
            self.edge.goto_drive()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def test_step_1(self):
        """restore file to commcell client and network path without overwrite option selected"""
        try:
            self.edge.restore_to_commcell_client(self.commcell,
                                                 self.file_folder_name,
                                                 self.tcinputs['edgeClientName'],
                                                 self.tcinputs['RestoreClientName'])

            self.edge.restore_to_network_path(self.commcell,
                                              self.file_folder_name,
                                              self.tcinputs['edgeClientName'],
                                              self.tcinputs['RestoreClientName'],
                                              self.tcinputs['NetworkPath'],
                                              self.tcinputs['UNCUserName'],
                                              self.tcinputs['UNCPassword'],
                                              self.tcinputs['RestoreNW_link_path'])
        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def test_step_2(self):
        """restore file to commcell client and network path with overwrite option"""
        try:
            self.edge.restore_to_commcell_client(self.commcell,
                                                 self.file_folder_name,
                                                 self.tcinputs['edgeClientName'],
                                                 self.tcinputs['RestoreClientName'],
                                                 overwrite=True)

            self.edge.restore_to_network_path(self.commcell,
                                              self.file_folder_name,
                                              self.tcinputs['edgeClientName'],
                                              self.tcinputs['RestoreClientName'],
                                              self.tcinputs['NetworkPath'],
                                              self.tcinputs['UNCUserName'],
                                              self.tcinputs['UNCPassword'],
                                              self.tcinputs['RestoreNW_link_path'],
                                              overwrite=True)

        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    @test_step
    def test_step_3(self):
        """restore file to commcell client and network path without overwrite option
           and destination path exists"""
        try:
            # overwrite data on restore commcell client
            restore_client_obj = Machine(self.tcinputs['RestoreClientName'], self.commcell)
            restored_file = restore_client_obj.join_path(restore_client_obj.tmp_dir, self.file_folder_name)
            restore_client_obj.create_file(restored_file, content=self.name)

            self.edge.restore_to_commcell_client(self.commcell,
                                                 self.file_folder_name,
                                                 self.tcinputs['edgeClientName'],
                                                 self.tcinputs['RestoreClientName'],
                                                 restore_path=restore_client_obj.tmp_dir,
                                                 clear_destination_path=False)

            # overwrite data on restore network client
            restore_client_obj = Machine(self.tcinputs['UNCClientName'],
                                         username=self.tcinputs['UNCUserName'],
                                         password=self.tcinputs['UNCPassword'])

            restored_file = restore_client_obj.join_path(self.tcinputs['RestoreNW_link_path'],
                                                         self.file_folder_name)

            restore_client_obj.create_file(restored_file, content=self.name)
            self.edge.restore_to_network_path(self.commcell,
                                              self.file_folder_name,
                                              self.tcinputs['edgeClientName'],
                                              self.tcinputs['RestoreClientName'],
                                              self.tcinputs['NetworkPath'],
                                              self.tcinputs['UserName'],
                                              self.tcinputs['Password'],
                                              self.tcinputs['RestoreNW_link_path'],
                                              clear_destination_path=False)

            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

        except Exception as _exception:
            raise CVTestStepFailure(_exception)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.file_folder_name = TestCase.FILE_NAME

            self.upload_path = self.edge.create_edge_test_data("file", self.file_folder_name)
            self.log.info("edge drive upload path: %s" % self.upload_path)

            self.edge.upload_to_edge([self.upload_path], self.commcell, self.tcinputs['edgeClientName'])

            self.test_step_1()
            self.test_step_2()
            self.test_step_3()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function"""
        try:
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
