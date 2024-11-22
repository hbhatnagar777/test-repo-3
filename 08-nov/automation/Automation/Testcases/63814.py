# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils.windows_machine import WindowsMachine
from Web.Common.page_object import handle_testcase_exception
from Install.sim_call_helper import SimCallHelper
from Install.installer_constants import REMOTE_FILE_COPY_LOC
from Laptop.laptophelper import LaptopHelper
from Web.AdminConsole.Helper.UserHelper import UserMain
from Web.AdminConsole.AdminConsolePages.UserGroupDetails import UserGroupDetails
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Components.table import Rtable
import random
import re

class TestCase(CVTestCase):
    """Testcase : Activating multiple laptop clients to a company"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Parallel Registration of Multiple Clients"
        self.log = None
        self.sim_caller = None
        self.no_of_clients = None
        self.local_machine = None
        self.xml_file_path = None
        self.cs_machine = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.list_of_activation_users = None
        self.user_obj = None
        self.user_group_details = None

    def setup(self):
        """Setup function of this test case"""
        self.sim_caller = SimCallHelper(self.commcell)
        self.log = logger.get_log()
        self.xml_file_path = REMOTE_FILE_COPY_LOC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.local_machine = Machine()
        common_inputs = ["Activation_User2", "Activation_User3", "Activation_User4", "Activation_User5", "No_of_Clients", "Activation_Password1", "domain_name", "user_group"]
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company3', common_inputs))
        self.cs_machine = WindowsMachine(self.tcinputs['Machine_host_name'], commcell_object=self.commcell)
        self.no_of_clients = self.tcinputs.get('No_of_Clients') if self.tcinputs.get('No_of_Clients') else 10
        self.list_of_activation_users = [self.tcinputs['Activation_User'], self.tcinputs['Activation_User2'], self.tcinputs['Activation_User3'], self.tcinputs['Activation_User4'],
                                    self.tcinputs['Activation_User5']]

    def generate_xmls(self):
        """ To generate the XMLs for the SIM call operation for all the clients """
        self.xml_file_path = self.local_machine.join_path(self.xml_file_path, "request_xmls")
        if not self.local_machine.check_directory_exists(self.xml_file_path):
            self.local_machine.create_directory(self.xml_file_path)
            self.log.info('Successfully created directory for SimRequests')
        self.local_machine.clear_folder_content(self.xml_file_path)
        self.log.info('Successfully cleared the SIMRequests directory of previous requests and responses')
        self.log.info(f'Begin generating [{int(self.no_of_clients)}] XMLs for SIM requests')
        for i in range(int(self.no_of_clients)):
            try:
                sim_request = f"SimReq{i + 1}"
                xml_path = self.local_machine.join_path(self.xml_file_path, f"{sim_request}.xml")
                self.log.info(f'Generating SIM request: [{sim_request}]')
                self.sim_caller.generate_xml(path=xml_path,
                                             commserv_hostname=self.tcinputs["Machine_host_name"],
                                             client_name=sim_request + "client",
                                             client_hostname=sim_request + "hostname",
                                             username=random.choice(self.list_of_activation_users),
                                             password=self.tcinputs['Activation_Password'],
                                             domainName=self.tcinputs['domain_name'])
            except:
                self.log.info('Error while generating the request XMLs. Exiting...')
                raise
            else:
                self.log.info(f'Successfully generated [{sim_request}] at path: [{xml_path}]')
        self.log.info(f'Successfully generated [{int(self.no_of_clients)}] XMLs for SIM requests')

    def execute_sim_calls(self, i):
        """ To execute the SIM call """
        sim_request = f"SimReq{i + 1}"
        xml_path = self.local_machine.join_path(self.xml_file_path, f"{sim_request}.xml")
        xml_output_path = self.local_machine.join_path(self.xml_file_path, f"{sim_request}_output.xml")
        try:
            self.log.info(f'Executing SIM call for [{sim_request}]')
            self.sim_caller.execute_sim_call(xml_path, xml_output_path)
        except:
            self.log.info(f'Error while executing the SIM call for [{sim_request}]. Response saved: [{xml_output_path}]')
            return
        else:
            self.log.info(f'Successfully executed SIM call for [{sim_request}], response in: [{xml_output_path}]')

    def time_analyzer(self):
        """
        Extracts registration and configuration times from CS CvInstallMgr.log file for all clients and compares them
        with preconfigured time values for each
            Raises:
                Exception: Configuration times more than the threshold
                Exception: Registration time more than the threshold
        """
        N = self.no_of_clients
        self.log.info('Attempting retrieval of registration time durations from CS logs')
        try:
            raw_log_config_times = self.cs_machine.get_logs_for_job_from_file(job_id=None, log_file_name="CvInstallMgr.log",
                                                                         search_term="Successfully configured client")
            raw_log_registration_times = self.cs_machine.get_logs_for_job_from_file(job_id=None, log_file_name=
                "CvInstallMgr.log", search_term="Client registration completed in")
        except:
            self.log.info('Error while retrieving the time durations from CS logs')
            return
        self.log.info('Successfully retrieved time durations, logging them now...')
        filter_log_config_times = raw_log_config_times.split('\r\n')[-N - 1:-1]
        filter_log_registration_times = raw_log_registration_times.split('\r\n')[-N - 1:-1]
        config_times_regex = re.compile(r'taken \[(.*)\] seconds')
        config_times = [int(config_times_regex.search(line).group(1)) for line in filter_log_config_times]
        registration_times_regex = re.compile(r'completed in \[(.*)\] seconds')
        registration_times = [int(registration_times_regex.search(line).group(1)) for line in
                              filter_log_registration_times]
        for i in range(N):
            self.log.info(f"Configuration time for client {i + 1} = {config_times[i]} seconds")
            self.log.info(f"Registration time for client {i + 1} = {registration_times[i]} seconds")
        config_time_check = all(t <= int(self.tcinputs['configuration_threshold']) for t in config_times)
        if not config_time_check:
            raise Exception("Configuration taking more time than threshold")
        registration_time_check = all(t <= int(self.tcinputs['registration_threshold']) for t in registration_times)
        if not registration_time_check:
            raise Exception("Registration taking more time than threshold")

    def run(self):
        """Run function of this test case"""
        try:
            self.admin_console.login(self.tcinputs["Tenant_admin"],
                                 self.tcinputs["Tenant_password"],
                                 stay_logged_in=True)
            self.user_obj = UserMain(self.admin_console,self.commcell)
            self.user_group_details = UserGroupDetails(self.admin_console)
            user_group_name = self.tcinputs["user_group"]
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_user_groups()
            Rtable(self.admin_console).access_link(user_group_name)
            user_list = self.user_group_details.list_users()
            self.navigator.navigate_to_users()
            for user in user_list:
                Users(self.admin_console).delete_user(user)
            for user in self.list_of_activation_users:
                self.user_obj.user_name = user
                self.user_obj.full_name = user
                self.user_obj.email = user + '@' + self.tcinputs['domain_name'] + '.com'
                self.user_obj.password = self.tcinputs["Activation_Password1"]
                self.user_obj.user_groups = [self.tcinputs['user_group']]
                self.user_obj.add_new_local_user()
                self.log.info("User Creation completed")
            self.log.info("Generating XMLs for Simcalls")
            self.generate_xmls()
            self.log.info(f'Setting CvInstallMgr.log file size to 15 MB on Path EventManager')
            self.cs_machine.set_logging_filesize_limit('CVINSTALLMGR', 15)
            self.log.info("Executing Simcalls")
            for i in range(int(self.no_of_clients)):
                self.execute_sim_calls(i)
            self.time_analyzer()
        except Exception as excp:
            handle_testcase_exception(self, excp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info(f'Setting CvInstallMgr.log file size to default on Path EventManager')
        self.cs_machine.set_logging_filesize_limit('CVINSTALLMGR')
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)