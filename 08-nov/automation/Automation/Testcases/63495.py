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
from Laptop.laptoputils import LaptopUtils
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.browse import RBrowse

class TestCase(CVTestCase):
    """[Laptop] [AdminConsole][EdgeMode]- ACL Browse with User Created Folder under Desktop / Documents"""
    test_step = TestStep()
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- ACL Browse with User Created Folder under Desktop / Documents"
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
        self.folder_path = None
        self.os_type = None

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
    def verify_browse_result(self, current_user):
        """verify browse result for the given user """
        self.log.info("****** Verifying the browse result from webconsole for the given user [{0}] *****".format(current_user))
        self.edgemain_obj.navigate_to_client_restore_page(self.client_name)
        self.log.info("Client path is : {0}".format(self.folder_path))
        self.rbrowse.navigate_path(self.folder_path, use_tree=False)
        browse_res= self.rtable.get_table_data()
        name_res = browse_res['Name']
        for each_folder in name_res:
            if each_folder !='':
                self.log.info("***** User [{0}] able to browse the data [{1}] *****".format(current_user, self.folder_path))
                break
        else:
            exp = "User [{0}] Unable to browse the data from [{1}]"\
                .format(current_user, self.folder_path)
            self.log.exception(exp)
            raise Exception(exp)

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
            # 2. For Windows verifying browse result both with allowed user and denyed user As per OS behavior
            # 3. MAC always deny other users to access system created folders of other users
            self.server_obj.log_step("""
                1. Create Folder/File under system created folder of the USER
                            ex: /users/testuser_12/Desktop/TC_63495
                                /users/testuser_12/Documents/TC_63495
                2. Add above path as content, Above folder should be backedup
                3. loginto webconsole as owner of folder and should be able to see above created folder with enduser access
                     Note:Makesure broswe disabled and enduser access enabled on that client
                4. Loginto webconsole as other user [testuser_13] and should not be able to see the data

            """, 200)

            #-------------------------------------------------------------------------------------
            self.laptop_obj = LaptopUtils(self)
            self.utility = OptionsSelector(self._commcell)
            self.idautils = CommonUtils(self)
            laptop_config = get_config().Laptop
            self.user_inputs = laptop_config._asdict()['ACL']._asdict()
            folder_owner = self.user_inputs['Folderowner_name'].split('\\')[1]
            folder_name = 'TC_'+str(self.id)
            if self.tcinputs['os_type']=="Windows":
                self._log.info(""" *-------- ACL browse verification started on Windows client ---------*""")
                local_folder_path = f"C:\\Users\\{folder_owner}\\Documents"
                self.folder_path = local_folder_path + '\\' + folder_name
                browse_folder_path = f"C:\\Users"
                folder_to_verify = folder_owner
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, self.folder_path)
                self.client_name = self.tcinputs['Client_name']
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = self.folder_path
                self.laptop_obj.os_info =  self.tcinputs['os_type']
                self.utility.create_test_data(self.machine_obj, self.folder_path)

            else:
                self._log.info(""" *-------- ACL browse verification started on MAC client--------* """)
                local_folder_path = f'/Users/{folder_owner}/Documents'
                self.folder_path = local_folder_path + '/'+ folder_name
                browse_folder_path = f'/Users/{folder_owner}'
                folder_to_verify = 'Documents'
                self.machine_obj = self.utility.get_machine_object(self.tcinputs['Client_name'])
                self.client_obj = self.commcell.clients.get(self.tcinputs['Client_name'])
                self.subclient_obj = CommonUtils(self.commcell).get_subclient(self.client_obj.client_name)
                self.source_dir = self.utility.create_directory(self.machine_obj, self.folder_path)
                self.client_name = self.tcinputs['Client_name']
                self.laptop_obj.client_object = self.client_obj
                self.laptop_obj.machine_object = self.machine_obj
                self.laptop_obj.subclient_object = self.subclient_obj
                self.laptop_obj.folder_path = self.folder_path
                osc_options = '-testuser root -testgroup admin'
                self.utility.create_test_data(self.machine_obj, self.folder_path, options=osc_options)
                self.log.info("Changing the folder owner with logged in user")
                self.machine_obj.change_folder_owner(folder_owner, self.folder_path)

            self._log.info("----- Verifying the browse result for the owner-----")
            self.init_tc(self.user_inputs['Folderowner_name'], self.user_inputs['Folderowner_password'])

            #-----------------Changes for cloud laptop -------------#
            if self.tcinputs['Cloud_direct'] is True:
                # Run incr backup job
                client_name = self.client_obj.machine_name
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
                self.edgeHelper_obj.trigger_v2_laptop_backup(self.client_name, self.tcinputs['os_type'])

            else:
                # Run incr backup job
                _job_obj = self.idautils.subclient_backup(self.subclient_obj)

            self.verify_browse_result(folder_owner)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            if self.tcinputs['os_type']=='Windows':
                self._log.info("----Verifying the browse result for Windows allowed user----")
                self.init_tc(self.user_inputs['Seconduser_name'], self.user_inputs['Seconduser_password'])
                self.verify_browse_result(self.user_inputs['Seconduser_name'])
                AdminConsole.logout_silently(self.admin_console)
                Browser.close_silently(self.browser)
            self._log.info("----Verifying the browse result with Denyed user----")
            self.init_tc(self.user_inputs['Denyeduser_name'], self.user_inputs['Denyeduser_password'])
            self.verify_browse_for_denyeduser(browse_folder_path, folder_to_verify, self.folder_path)
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            self.utility.remove_directory(self.machine_obj, self.folder_path)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)


