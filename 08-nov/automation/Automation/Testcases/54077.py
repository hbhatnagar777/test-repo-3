# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Web Console - verify Add/Remove contents for Laptop Clients"""

import time
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.browse import Browse
from Web.WebConsole.Laptop.Computers.summary import Summary
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.options_selector import OptionsSelector
from Laptop.CloudLaptop import cloudlaptophelper
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Web Console - verify Add/Remove contents for Laptop Clients"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = True
        self.tcinputs = {
            "webconsole_username": None,
            "webconsole_password": None,
            "Windows_client_name": None,
            "windows_test_Path": None,
            "Mac_client_name": None,
            "Mac_test_Path": None,
            "Documents_path":None,
            "Cloud_direct": None
        }
        self.utils = TestCaseUtils(self)
        self.laptop_utils = None
        self.webconsole = None
        self.browser = None
        self.backups = None
        self.browse = None
        self.computers = None
        self.navigator = None
        self.webconsole_username = None
        self.webconsole_password = None
        self.cloud_object = None
        self.common_utils = None
        self.clients = []
        self.clients_found = []
        self.cleanup_dir = {}
        self.cleanup_file = {}
        self.exclude_file_path = None

    def init_tc(self, user_name, password):
        """
        Initial configuration for the test case
        """
        try:
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(user_name, password)
            self.webconsole.goto_mydata()
            self.navigator = Navigator(self.webconsole)
            self.computers = Summary(self.webconsole)
            self.backups = ClientDetails(self.webconsole)
            self.browse = Browse(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes objects required for this testcase"""
        self.clients.append(self.tcinputs["Windows_client_name"])
        self.clients.append(self.tcinputs["Mac_client_name"])
        self.webconsole_username = (self.tcinputs["webconsole_username"])
        self.webconsole_password = (self.tcinputs["webconsole_password"])
        self.laptop_utils = LaptopUtils(self)
        self.common_utils = CommonUtils(self)
        self.cloud_object = cloudlaptophelper.CloudLaptopHelper(self)

    @test_step
    def _verify_backup_running(self, backup_text):
        """
        Verify if any backup is running on client machine.
        """
        for _i in range(1, 6):
            if not self.backups.is_backup_running():
                return 0
            self.log.info(" [{0}] backup job running.Will wait about 5 minutes to let job finish".format(backup_text))
            OptionsSelector(self._commcell).sleep_time(120, "Waiting for Backup job to finish")
        raise CVTestStepFailure("Backup did not finish in 10 minutes. Exiting")

    @test_step
    def _verify_browse_results(self, each_client, client_path, file_name, exclude=0):
        """
        Verify browse results on given machine.
        """
        self.computers.get_client_restore_link(client_name=each_client, goto_link=True)
        self.log.info("Client restore path is : {0}".format(client_path))
        self.browse.navigate_to_restore_page(client_path)
        browse_res = self.browse.read_browse_results()
        if not exclude:
            file_found = 0
            for each_item in browse_res:
                if file_name == each_item['FileName']:
                    self.log.info("Backed up file: '{0}' is found in the web console".format(file_name))
                    file_found = 1
            if file_found == 0:
                raise CVTestStepFailure("Backed up file: {0} is not found in the web console" .format(file_name))
        else:
            file_found = 0
            for each_item in browse_res:
                if file_name == each_item['FileName']:
                    file_found = 1
                    raise CVTestStepFailure("Exclude backup content functionality failed as" +
                                            "file [{0}] backed up even excluded from backup" .format(file_name))

            if file_found == 0:
                self.log.info("Backed up file: {0} is not found in the web console" .format(file_name))

    @test_step
    def _verify_add_content_functionality(self, client_name, documents_path, file_name, documents_file_path, name):
        """ verify add documents as content and run the backup"""

        self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
        self._verify_backup_running('previous')
        self.backups.add_browse_content(name)
        self.laptop_utils.create_file(client_name, documents_path, documents_file_path)
        OptionsSelector(self._commcell).sleep_time(180, "CCSDB wait time to update the filter")
        #-----------------Changes for cloud laptop -------------#
        if self.tcinputs['Cloud_direct']:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
            self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole)
        else:
            self._verify_backup_running('previous')
            self.backups.click_on_backup_button()
            self._verify_backup_running('Current')
        self._verify_browse_results(client_name, documents_path, file_name)
        self.log.info("*" * 10 + " Add documents as content functionality verification completed successfully" +
                      "for client : [{0}] " .format(client_name) + "*" * 10)

    @test_step
    def _verify_exclude_content_functionality(self, client_name, exclude_path, file_name, file_path):
        """ verify exclude content and run the backup"""
        self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
        self._verify_backup_running('previous')
        self.backups.exclude_custon_content(file_path)
        self.laptop_utils.create_file(client_name, exclude_path, file_path)
        OptionsSelector(self._commcell).sleep_time(180, "CCSDB wait time to update the content")
        #-----------------Changes for cloud laptop -------------#
        if self.tcinputs['Cloud_direct']:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
            self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole)
        else:
            self._verify_backup_running('previous')
            self.backups.click_on_backup_button()
            self._verify_backup_running('Current')
        self._verify_browse_results(client_name, exclude_path, file_name, exclude=1)
        self.log.info("*" * 10 + " Exclude content functionality verification completed successfully" +
                      "for client : [{0}] " .format(client_name) + "*" * 10)

    @test_step
    def _verify_remove_contnent_functionality(self, client_name, name="Documents"):
        """ Remove documents from content and verify"""
        self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
        #-----------------Changes for cloud laptop -------------#
        if self.tcinputs['Cloud_direct']:
            subclient_object = self.common_utils.get_subclient(client_name)
            self.cloud_object.check_if_any_job_running(client_name, subclient_object)
        else:
            self._verify_backup_running('previous')
        self.backups.remove_include_files(name)
        OptionsSelector(self._commcell).sleep_time(5, "waiting for remove content to be reflected in GUI")
        content_list = self.laptop_utils.get_subclient_content_from_gui(client_name)
        for _contnent in content_list:
            if name in _contnent:
                raise CVTestStepFailure("content is not removed from the gui")
        self.log.info("*" * 10 + " Remove content functionality verification completed successfully" +
                      "for client : [{0}] " .format(client_name) + "*" * 10)

    @test_step
    def verify_backup_content_operations(self, clients_found):
        """
        verify add, exclude , remove contnet functionality
        """
        local_time = int(time.time())
        documents_path = self.tcinputs["Documents_path"]
        for each_client in clients_found:
            if each_client == self.tcinputs["Windows_client_name"]:
                client_name = self.tcinputs["Windows_client_name"]
                exclude_path = self.tcinputs["windows_test_Path"]
                file_name = 'backupfile_'+str(local_time)+".txt"
                documents_file_path = documents_path + '\\' + file_name
                self.exclude_file_path = exclude_path + '\\' + file_name
                self.cleanup_dir.setdefault(client_name, documents_path)
                self.cleanup_file.setdefault(client_name, self.exclude_file_path)

            else:
                client_name = self.tcinputs["Mac_client_name"]
                exclude_path = self.tcinputs["Mac_test_Path"]
                file_name = 'backupmacfile_'+str(local_time)+".txt"
                documents_file_path = documents_path + '/' + file_name
                self.exclude_file_path = exclude_path + '/' + file_name
                self.cleanup_dir.setdefault(client_name, documents_path)
                self.cleanup_file.setdefault(client_name, self.exclude_file_path)

            self.log.info("*" * 10 + "Add,exclude,remove content functionality verification started on client: '{0}' "
                          .format(client_name) + "*" * 10)
            self._verify_add_content_functionality(
                client_name, documents_path, file_name, documents_file_path, "Documents"
            )
            self._verify_exclude_content_functionality(client_name, exclude_path, file_name, self.exclude_file_path)
            self._verify_remove_contnent_functionality(client_name, "Documents")
        self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

    def run(self):
        try:
            self.init_tc(self.webconsole_username, self.webconsole_password)
            self.navigator.go_to_computers()
            console_clients = self.computers.get_clients_list()
            self.clients_found = self.laptop_utils.check_clients_exists(self.clients, console_clients)
            self.verify_backup_content_operations(self.clients_found)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                for client_name in self.clients_found:
                    self.computers.get_client_prop(client_name=client_name, goto_link=True)
                    self.backups.remove_exclude_files(self.exclude_file_path)
                    self.backups.remove_include_files("Documents")
                    self.laptop_utils.remove_directory(client_name, self.cleanup_dir[client_name])
                    self.laptop_utils.cleanup_testdata(client_name, self.cleanup_file[client_name])
            except Exception as err:
                self.log.info("Cleanup failed with error {0}".format(err))
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
