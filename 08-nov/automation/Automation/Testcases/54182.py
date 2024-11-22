# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Webconsole : Erase File Data"""

import time
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.summary import Summary
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from Web.WebConsole.Laptop.Computers.browse import Browse
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.config import get_config
from Laptop.CloudLaptop import cloudlaptophelper

class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Webconsole : Erase File Data"
        self.product = self.products_list.LAPTOP
        self.show_to_user = True
        self.tcinputs = {
            "webconsole_username": None,
            "webconsole_password": None,
            "Windows_client_name": None,
            "windows_test_Path": None,
            "Mac_client_name": None,
            "Mac_test_Path": None,
            "Cloud_direct": None
        }
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.computers = None
        self.backups = None
        self.browse = None
        self.utils = TestCaseUtils(self)
        self.laptop_utils = None
        self.ida_utils = None
        self.windows_filename = None
        self.webconsole_username = None
        self.webconsole_password = None
        self.download_directory = None
        self.machine = None
        self.clients = []
        self.clients_found = []
        self.cleanup_dict = {}
        self.os_info = None
        self.cloud_object = None

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
        self.ida_utils = CommonUtils(self)
        self.cloud_object = cloudlaptophelper.CloudLaptopHelper(self)


    @test_step
    def _verify_browse_results(self, client_name, client_path, folder_name):
        """
        Verify browse results after folder erased.
        """
        self.computers.get_client_restore_link(client_name, goto_link=True)
        self.log.info("Client restore path is : {0}".format(client_path))
        self.browse.navigate_to_restore_page(client_path)

        browse_res = self.browse.read_browse_results()
        file_found = 0
        for each_item in browse_res:
            if folder_name == each_item['FolderName']:
                file_found = 1
                raise CVTestStepFailure("Backed up folder: {0} found in browse result even after erased"
                                        .format(folder_name))
        if file_found == 0:
            self.log.info("Backed up folder: '{0}' is not found in browse result after erased".format(folder_name))

    @test_step
    def _verify_backup_running(self, backup_text):
        """
        Verify if any backup is running on client machine.
        """
        for _i in range(1, 6):
            if not self.backups.is_backup_running():
                return 0
            self.log.info(" '{0}' backup job running.Will wait about 5 minutes to let job finish".format(backup_text))
            OptionsSelector(self._commcell).sleep_time(120, "Waiting for Backup job to finish")
        raise CVTestStepFailure("Backup did not finish in 10 minutes. Exiting")

    @test_step
    def _verify_erase_folder(self, client_name, client_path, folder_name):
        """
        Delete/Erase the folder from webconsole.
        """
        self.computers.get_client_restore_link(client_name, goto_link=True)
        self.log.info("Client restore path is : {0}".format(client_path))
        self.browse.navigate_to_restore_page(client_path)
        self.webconsole.clear_all_notifications()
        self.browse.refresh_browse_data()
        self.browse.select_required_folder(folder_name)
        self.browse.click_on_delete()
        err_msgs = self.webconsole.get_all_error_notifications()
        if err_msgs:
            raise CVTestStepFailure("Erase folder failed with error message: {0} ".format(err_msgs[0]))
        self._verify_browse_results(client_name, client_path, folder_name)
        # Run the incremental backup and verify browse result to make sure file erased and not picked for backup again
        self.computers.get_client_prop(client_name, goto_link=True)  # get the client properties

        if self.tcinputs['Cloud_direct']:
            #-------Run incremental and synth full together and verify
            self.log.info("verify synthfull backup on cloud client [{0}]".format(client_name))
            self.cloud_object.run_sythfull_with_incremenatlfrom_webconsole(client_name, self.webconsole, self.machine)

        else:
            self._verify_backup_running('previous')
            self.backups.click_on_backup_button()
            self._verify_backup_running('Current')
            self._verify_browse_results(client_name, client_path, folder_name)
            # Run Synth full job
            laptop_config = get_config().Laptop
            client_data = laptop_config._asdict()['UserCentricClient']._asdict()
            client = client_data[self.os_info].ClientName
            if client:
                new_client = client
            else:
                new_client = client_name
            self.laptop_utils.run_backup_job(self.ida_utils, new_client, 'Synthetic_full')
        self._verify_browse_results(client_name, client_path, folder_name)

    @test_step
    def backup_and_erase_folder_data(self, clients_found):
        """
        Run backup and erase folder from webconsole.
        """
        local_time = int(time.time())
        for each_client in clients_found:
            if each_client == self.tcinputs["Windows_client_name"]:
                client_name = self.tcinputs["Windows_client_name"]
                file_name = 'Erasefile_'+str(local_time)+".txt"
                folder_path = self.tcinputs["windows_test_Path"] + '\\' + 'Erase_TC_54182'
                folder_file_name = folder_path + '\\' + file_name
                client_path = self.tcinputs["windows_test_Path"]
                self.os_info = "WINDOWS"
                self.cleanup_dict.setdefault(client_name, folder_path)

            else:
                client_name = self.tcinputs["Mac_client_name"]
                file_name = 'Erasemacfile_'+str(local_time)+".txt"
                folder_path = self.tcinputs["Mac_test_Path"] + '/' + 'Erase_TC_54182'
                folder_file_name = folder_path + '/' + file_name
                client_path = self.tcinputs["Mac_test_Path"]
                self.os_info = "UNIX"
                self.cleanup_dict.setdefault(client_name, folder_path)

            folder_name = 'Erase_TC_54182'
            # create machine object
            self.machine = Machine(client_name, self.commcell)
            # create test data
            self.laptop_utils.create_file(self.machine, folder_path, folder_file_name)
            self.computers.get_client_prop(client_name=each_client, goto_link=True)  # get the client properties
            #-----------------Changes for cloud laptop -------------#
            if self.tcinputs['Cloud_direct']:
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
                self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole, self.machine)
            else:
                self._verify_backup_running('previous')
                self.backups.click_on_backup_button()  # Trigger the backup
                self._verify_backup_running('Current')
            self._verify_erase_folder(client_name, client_path, folder_name)
        self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

    def run(self):
        try:
            self.init_tc(self.webconsole_username, self.webconsole_password)
            self.navigator.go_to_computers()
            console_clients = self.computers.get_clients_list()
            self.clients_found = self.laptop_utils.check_clients_exists(self.clients, console_clients)
            self.backup_and_erase_folder_data(self.clients_found)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                for client_name in self.clients_found:
                    self.laptop_utils.remove_directory(client_name, self.cleanup_dict[client_name])
            except Exception as err:
                self.log.info("Failed to delete test data{0}".format(err))
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
