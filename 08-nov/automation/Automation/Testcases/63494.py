# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager
from Laptop.laptoputils import LaptopUtils
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.browse import RBrowse



class TestCase(CVTestCase):
    """[Laptop] [AdminConsole][EdgeMode]- ACL Browse with User created folder has explicit group deny"""
    
    test_step = TestStep()
    
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- ACL Browse with User created folder has explicit group deny"
        self.browser = None
        self.admin_console = None
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
        self.client_name = None 
        self.computers = None
        self.edgeHelper_obj = None
        self.edgemain_obj = None
        self.rtable = None
        self.rbrowse = None

    def init_tc(self, login_username, login_password):
        """ Login to with given user """
        try:
          
            self.server_obj.log_step(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(login_username, login_password)
            self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
            self.edgeHelper_obj.client_name = self.client_name
            self.edgemain_obj = EdgeMain(self.admin_console)
            self.rtable = Rtable(self.admin_console)
            self.rbrowse = RBrowse(self.admin_console)
            self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception
    
    @test_step
    def verify_browse_for_denyeduser(self, browse_folder_path, folder_to_verify, folder_path):
        """verify browse result for denyed user"""
        denyed_user = self.user_inputs['Denyeduser_name']
        self.log.info(" Verifying the browse result from webconsole for the owner [{0}] *****".format(denyed_user))
        self.edgemain_obj.navigate_to_client_restore_page(self.client_name)
        self.log.info("Client path is : {0}".format(browse_folder_path))
        self.rbrowse.navigate_path(browse_folder_path, use_tree=False)
        browse_res= self.rtable.get_table_data()
        if folder_to_verify in browse_res['Name']:
            exp = "User [{0}] able to browse the data even does not have permissions on [{1}]"\
                .format(denyed_user, folder_path)
            self.log.exception(exp)
            raise Exception(exp)
                
        self.log.info("As Expected! User [{0}] Unable to browse the data [{1}]".format(denyed_user, folder_path))

    
    def run(self):

        try:
            self.server_obj = ServerTestCases(self)
            self.tcinputs.update(EdgeHelper.set_testcase_inputs(self, acl=True))

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
            self.user_inputs = laptop_config._asdict()['ACL']._asdict()
            allowed_group = self.user_inputs['Allowed_group']
            denyed_group = self.user_inputs['Denyed_group']
            folder_to_verify = 'TC_'+str(self.id)
            sub_folder = 'TC_'+str(self.id)+'_01'

            if self.tcinputs['os_type']=="Windows":
                self._log.info(""" *-------- ACL browse verification started on Windows client ---------*""")
                self.root_folder = 'C:\\' + folder_to_verify
                folder_path = 'C:\\' + folder_to_verify +'\\'+sub_folder
                browse_folder_path = "C:"
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, folder_path)
                self.client_name = self.tcinputs['Client_name']
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = folder_path
                self.laptop_obj.os_info = self.tcinputs['os_type']
                self.utility.create_test_data(self.machine_obj, folder_path)
                self.log.info("Add group to folder with ALLOW permissions")
                self.laptop_obj.add_usergroup_permissions(allowed_group, self.root_folder)
                self.log.info("Add group to folder with DENY permission")
                self.laptop_obj.deny_usergroup_permissions(denyed_group, self.root_folder)

            else:
                self._log.info(""" *-------- ACL browse verification started on MAC client-------* """)

                self.root_folder = '/Users/' + folder_to_verify
                folder_path = '/Users/' + folder_to_verify +'/'+sub_folder
                browse_folder_path = '/Users'
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, folder_path)
                self.client_name = self.tcinputs['Client_name']
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

            self.init_tc(self.user_inputs['Denyeduser_name'], self.user_inputs['Denyeduser_password'])
            self.subclient_obj.content += [self.root_folder]

            #-----------------Changes for cloud laptop -------------#
            if self.tcinputs['Cloud_direct'] is True:
                # Run incr backup job
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(self.client_name))
                self.edgeHelper_obj.trigger_v2_laptop_backup(self.client_name, self.tcinputs['os_type'])

            else:
                _jobs = self.job_manager.get_filtered_jobs(
                    self.client_obj.client_name,
                    time_limit=5,
                    retry_interval=5,
                    backup_level='Incremental',
                    current_state='Running'
                )
                self._log.info("Backup job completed successfully")

            self._log.info("----Verifying the browse result with Denyed user----")
            self.verify_browse_for_denyeduser(browse_folder_path, folder_to_verify, folder_path)
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            self.utility.remove_directory(self.machine_obj, self.root_folder)
            self.subclient_obj.content = ['\%Pictures%']
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)


