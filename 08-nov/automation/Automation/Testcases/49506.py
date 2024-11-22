# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Webconsole : Laptop - Privacy feature"""

import time
from cvpysdk.exception import SDKException
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.summary import Summary
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
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
        self.name = "Webconsole : Laptop - Privacy feature"
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
        self.subclient = None
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.computers = None
        self.machine = None
        self.backups = None
        self.ida_utils = None
        self.utils = TestCaseUtils(self)
        self.laptop_utils = None
        self.ida_utils = None
        self.windows_filename = None
        self.webconsole_username = None
        self.webconsole_password = None
        self.download_directory = None
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
    def verify_privacy_feature(self, clients_found):
        """
        Verify Laptop Privacy feature
        """
        self._log.info("""
                ==============================================================================
                Prerequisite 1: From Control Panel->Sytem->Security-> 'Allow users to enable data privacy' option
                should be enabled for the client.

                Prerequisite 2: Make sure admin should not be the owner for that client

                Steps 1: enable "Prevent administrators from viewing or downloading your data." option from webconsole

                Steps 2: Verify Admin Should be able to run all backup jobs from gui

                Steps 3: Verify Admin Should not be able browse and restore data from gui
                ==============================================================================
                """)
        local_time = int(time.time())
        for each_client in clients_found:
            if each_client == self.tcinputs["Windows_client_name"]:
                client_name = self.tcinputs["Windows_client_name"]
                file_name = 'backupfile_'+str(local_time)+".txt"
                file_path = self.tcinputs["windows_test_Path"] + '\\' + file_name
                client_path = self.tcinputs["windows_test_Path"]
                self.os_info = "WINDOWS"
                self.cleanup_dict.setdefault(client_name, file_path)

            else:
                client_name = self.tcinputs["Mac_client_name"]
                file_name = 'backupmacfile_'+str(local_time)+".txt"
                file_path = self.tcinputs["Mac_test_Path"] + '/' + file_name
                client_path = self.tcinputs["Mac_test_Path"]
                self.os_info = "UNIX"
                self.cleanup_dict.setdefault(client_name, file_path)

            self.machine = Machine(client_name, self.commcell)
            self.laptop_utils.create_file(self.machine, client_path, file_path)
            self.computers.get_client_prop(client_name=each_client, goto_link=True)  # get the client properties
            self.backups.enable_privacy_feature(self.webconsole_password)  # Trigger the backup
            # Run full job
            laptop_config = get_config().Laptop
            client_data = laptop_config._asdict()['UserCentricClient']._asdict()
            client = client_data[self.os_info].ClientName
            if client:
                new_client = client
            else:
                new_client = client_name

            if self.tcinputs['Cloud_direct']:
                #-------Run incremental and synth full together and verify
                self.log.info("verify synthfull backup on cloud client [{0}]".format(client_name))
                self.cloud_object.run_sythfull_with_incremenatlfrom_webconsole(client_name, self.webconsole, self.machine)

            else:
                job_obj = self.laptop_utils.run_backup_job(self.ida_utils, new_client)
                if not job_obj:
                    raise CVTestStepFailure("Admin unable to run the backup job for client: {0}".format(new_client))
                self._log.info("Successfully ! Admin able to run backup job for locked client")
                # Run Synth full job

                self.laptop_utils.run_backup_job(self.ida_utils, new_client, 'Synthetic_full')
                if not job_obj:
                    raise CVTestStepFailure("Admin unable to run Synthetic full job for client: {0}".format(new_client))
                self._log.info("Successfully ! Admin able to run Synthetic full job for locked client")

            client_obj = self.commcell.clients.get(new_client)
            agent_obj = client_obj.agents.get('File System')
            backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
            subclient_obj = backupset_obj.subclients.get('default')
            self._log.info("verifying whether admin is able to browse data of locked client")
            try:
                properties = subclient_obj.browse(path='\\')
                if properties:
                    raise CVTestStepFailure(" 'Admin' able to browse data for locked client : {0}"
                                            .format(new_client))
            except SDKException as exp:
                self._log.info('Success! As expected: Browse failed with error: %s', str(exp))

            self._log.info("verifying whether admin able to restore data of locked client")
            try:
                job_obj = subclient_obj.restore_in_place(subclient_obj.content)
                if job_obj:
                    raise CVTestStepFailure("'Admin' able to restore data for locked client : {0}"
                                            .format(new_client))
            except SDKException as exp:
                self._log.info('Success! As expected: Failed with error: %s', str(exp))

        self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

    def run(self):
        try:
            self.init_tc(self.webconsole_username, self.webconsole_password)
            self.navigator.go_to_computers()
            console_clients = self.computers.get_clients_list()
            self.clients_found = self.laptop_utils.check_clients_exists(self.clients, console_clients)
            self.verify_privacy_feature(self.clients_found)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                for client_name in self.clients_found:
                    try:
                        self.computers.get_client_prop(client_name, goto_link=True)  # get the client properties
                        self.backups.disable_privacy_feature(self.webconsole_password)  # Trigger the backup
                    except Exception as err:
                        self.log.info("Failed to disable the privacy feature: {0}".format(err))
                    self.laptop_utils.cleanup_testdata(client_name, self.cleanup_dict[client_name])
            except Exception as err:
                self.log.info("Failed to delete test data{0}".format(err))
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
