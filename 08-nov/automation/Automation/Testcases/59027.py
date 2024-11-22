# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.browse import Browse
from Web.WebConsole.Laptop.Computers.summary import Summary
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Laptop.laptoputils import LaptopUtils
from Laptop.CloudLaptop import cloudlaptophelper


class TestCase(CVTestCase):
    """[Laptop] [Webconsole FS] - ACL Browse with User Created Folder under Desktop / Documents"""
    test_step = TestStep()
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Webconsole FS] - ACL Browse with User Created Folder under Desktop / Documents"
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.server_obj = None
        self.idautils = None
        self.utility = None
        self.navigator = None
        self.machine_obj = None
        self.client_obj = None
        self.laptop_obj = None
        self.user_inputs = None
        self.root_folder = None
        self.subclient_obj = None
        self.source_dir = None
        self.folder_path = None
        self.computers = None
        self.subclient_content = None
        self.cloud_object = None
        self.computers = None
        self.tcinputs = {
            "Windows_client_name": None,
            "Mac_client_name": None,
            "Cloud_direct": None

        }


    def init_tc(self, login_username, login_password):
        """ Login to with given user """
        try:
            self.server_obj.log_step(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(login_username, login_password)
            self.webconsole.goto_mydata()
            self.navigator = Navigator(self.webconsole)
            self.computers = Summary(self.webconsole)
            _client_details = ClientDetails(self.webconsole)
            browse_obj = Browse(self.webconsole)
            self.laptop_obj.browser_obj = browse_obj
            self.laptop_obj.computers_obj = self.computers

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):

        try:
            self.server_obj = ServerTestCases(self)
            #-------------------------------------------------------------------------------------
            # 1. Take same domain users in both mac and windows
            # 2. For Windows verifying browse result both with allowed user and denyed user As per OS behaviour
            # 3. MAC always deny other users to access system created folders of other users
            self.server_obj.log_step("""
                1. Create Folder/File under system created folder of the USER
                            ex: /users/testuser_12/Desktop/TC_59027
                                /users/testuser_12/Documents/TC_5907
                2. Add above path as content, Above folder should be backedup
                3. loginto webconsole as owner of folder and should be able to see above created folder with enduser access
                     Note:Makesure broswe disabled and enduser access enabled on that client
                4. Loginto webconsole as other user [testuser_13] and should not be able to see the data

            """, 200)

            #-------------------------------------------------------------------------------------
            self.laptop_obj = LaptopUtils(self)
            self.utility = OptionsSelector(self._commcell)
            self.idautils = CommonUtils(self)
            self.cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            laptop_config = get_config().Laptop
            self.user_inputs = laptop_config._asdict()['WebConsole']._asdict()
            folder_owner = self.user_inputs['Folderowner_name'].split('\\')[1]

            if not self.tcinputs["Windows_client_name"] == 'None':
                self._log.info(""" *-------- ACL browse verification started on Windows client ---------*""")
                self.folder_path = f"C:\\Users\\{folder_owner}\\Documents\\TC_59027"
                browse_folder_path = f"C:\\Users"
                folder_to_verify = folder_owner
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Windows_client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Windows_client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, self.folder_path)
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = self.folder_path
                self.laptop_obj.os_info = 'windows'
                self.utility.create_test_data(self.machine_obj, self.folder_path)

            else:
                self._log.info(""" *-------- ACL browse verification started on MAC client--------* """)
                self.folder_path = f'/Users/{folder_owner}/Documents/TC_59027'
                browse_folder_path = f'/Users/{folder_owner}'
                folder_to_verify = 'Documents'
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Mac_client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Mac_client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, self.folder_path)
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = self.folder_path
                osc_options = '-testuser root -testgroup admin'
                self.utility.create_test_data(self.machine_obj, self.folder_path, options=osc_options)
                self.log.info("Changing the folder owner with logged in user")
                self.machine_obj.change_folder_owner(folder_owner, self.folder_path)

            if not self.tcinputs['Cloud_direct']:
                # Run incr backup job
                _job_obj = self.idautils.subclient_backup(self.subclient_obj)

            self._log.info("----- Verifying the browse result for the owner-----")
            self.init_tc(self.user_inputs['Folderowner_name'], self.user_inputs['Folderowner_password'])
            #-----------------Changes for cloud laptop -------------#
            if self.tcinputs['Cloud_direct']:
                # Run incr backup job
                client_name = self.client_obj.machine_name
                self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
                self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole, self.machine_obj)

            self.laptop_obj.verify_browse_result(folder_owner)
            self.webconsole.logout_silently(self.webconsole)
            self.browser.close_silently(self.browser)
            if self.laptop_obj.os_info == "windows":
                self._log.info("----Verifying the browse result for Windows allowed user----")
                self.init_tc(self.user_inputs['Seconduser_name'], self.user_inputs['Seconduser_password'])
                self.laptop_obj.verify_browse_result(self.user_inputs['Seconduser_name'])
                self.webconsole.logout_silently(self.webconsole)
                self.browser.close_silently(self.browser)
            self._log.info("----Verifying the browse result with Denyed user----")
            self.init_tc(self.user_inputs['Denyeduser_name'], self.user_inputs['Denyeduser_password'])
            self.laptop_obj.verify_browse_for_denyeduser(self.user_inputs['Denyeduser_name'], browse_folder_path, folder_to_verify)
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            self.utility.remove_directory(self.machine_obj, self.folder_path)
            self.webconsole.logout_silently(self.webconsole)
            self.browser.close_silently(self.browser)


