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
from Server.JobManager.jobmanager_helper import JobManager
from Laptop.laptoputils import LaptopUtils
from Laptop.CloudLaptop import cloudlaptophelper



class TestCase(CVTestCase):
    """[Laptop] [Webconsole FS] - ACL Browse with User created folder has explicit group deny"""
    test_step = TestStep()
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [Webconsole FS] - ACL Browse with User created folder has explicit group deny"
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)
        self.server_obj = None
        self.idautils = None
        self.utility = None
        self.machine_obj = None
        self.client_obj = None
        self.navigator = None
        self.job_manager = None
        self.laptop_obj = None
        self.user_inputs = None
        self.root_folder = None
        self.subclient_obj = None
        self.source_dir = None
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
            # 2. create custom domain groups for both allowed and denyed users in Active directory
            # chmod 770 foldername # to remove permssions explicity to the user
            self.server_obj.log_step("""
                1. Create Folder like below with some files in child directory
                            ex: /USER/MAC_TEST/ACL_TEST
                2. Create 2 groups in Active directory With user
                     For ex: Group_allow , Group_deny in testlab domain and  testlab\testuser_13 is added to both groups
                3.Add both groups to folder one with allow and another with deny
                     Deny will take the precendence and user will not be able to see the data
                4. Add above path as content, Above folder should be backedup
                5. loginto webconsole as  testlab\testuser_13 and user should not be able to see the folder
                     Note:Makesure broswe disabled and enduser access enabled on that client

            """, 200)

            #-------------------------------------------------------------------------------------
            self.laptop_obj = LaptopUtils(self)
            self.utility = OptionsSelector(self._commcell)
            self.job_manager = JobManager(commcell=self._commcell)
            self.idautils = CommonUtils(self)
            laptop_config = get_config().Laptop
            self.user_inputs = laptop_config._asdict()['WebConsole']._asdict()
            allowed_group = self.user_inputs['Allowed_group']
            denyed_group = self.user_inputs['Denyed_group']
            folder_to_verify = 'TC_59028'

            if not self.tcinputs["Windows_client_name"] == 'None':
                self._log.info(""" *-------- ACL browse verification started on Windows client ---------*""")
                self.root_folder = f"C:\\TC_59028"
                folder_path = f"C:\\TC_59028\\TC_59028_01"
                folder_to_verify = 'TC_59028'
                browse_folder_path = "C:"
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Windows_client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Windows_client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, folder_path)
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = folder_path
                self.laptop_obj.os_info = 'windows'
                self.utility.create_test_data(self.machine_obj, folder_path)
                self.log.info("Add group to folder with ALLOW permissions")
                self.laptop_obj.add_usergroup_permissions(allowed_group, self.root_folder)
                self.log.info("Add group to folder with DENY permission")
                self.laptop_obj.deny_usergroup_permissions(denyed_group, self.root_folder)

            else:
                self._log.info(""" *-------- ACL browse verification started on MAC client--------* """)

                self.root_folder = f"/Users/TC_59028"
                folder_path = '/Users/TC_59028/TC_59028_01'
                browse_folder_path = '/Users'
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Mac_client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Mac_client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, folder_path)
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = folder_path
                osc_options = '-testuser root -testgroup admin'
                self.utility.create_test_data(self.machine_obj, folder_path, options=osc_options)
                self.log.info("Add group to folder with ALLOW permissions")
                self.laptop_obj.add_usergroup_permissions(allowed_group, self.root_folder)
                self.log.info("Add group to folder with DENY permission")
                self.laptop_obj.deny_usergroup_permissions(denyed_group, self.root_folder)

            #----------- Verify Auto trigger backup-------#
            self.subclient_obj.content += [self.root_folder]

            if not self.tcinputs['Cloud_direct']:
                _jobs = self.job_manager.get_filtered_jobs(
                    self.client_obj.client_name,
                    time_limit=5,
                    retry_interval=5,
                    backup_level='Incremental',
                    current_state='Running'
                )
                self._log.info("Backup job completed successfully")

            self._log.info("----Verifying the browse result with Denyed user----")
            self.init_tc(self.user_inputs['Denyeduser_name'], self.user_inputs['Denyeduser_password'])
            #-----------------Changes for cloud laptop -------------#
            if self.tcinputs['Cloud_direct']:
                # Run incr backup job
                client_name = self.client_obj.machine_name
                self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
                self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole, self.machine_obj)

            self.laptop_obj.verify_browse_for_denyeduser(self.user_inputs['Denyeduser_name'], browse_folder_path, folder_to_verify)
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            self.utility.remove_directory(self.machine_obj, self.root_folder)
            self.subclient_obj.content = ['\%Pictures%']
            self.webconsole.logout_silently(self.webconsole)
            self.browser.close_silently(self.browser)


