from selenium.webdriver.common.by import By
"""
This module provides the function or operations that can be used to run
basic operations on getting started page.

To initialize the class variables, pass the instance object to the appropriate
definition of AdminConsoleInfo

Call the required definition using the instance object, with no arguments to
be passed, only the flags needs to be passed into the method call while calling
the member function.

Class:

   GettingStartedMain() -> getting_started() -> object()

        __init__()

"""
from AutomationUtils import logger
from AutomationUtils import constants
from Web.AdminConsole.Helper.LoadModule import load_module
from Web.AdminConsole.Setup.vsa_getting_started import Virtualization
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.Servers import Servers


class GettingStartedMain:
    """
        Helper for getting started page
    """

    def __init__(self, driver=None, commcell=None, csdb=None, admin_console=None):
        """
            Initializes the getting started helper module
            :param
                driver -- the web driver object
                commcell -- comcell object
                csdb -- csdb object
                admin_console -- admin consol object
        """
        self.driver = driver
        self.csdb = csdb
        self.commcell = commcell
        self.admin_console = admin_console
        if not driver:
            raise Exception('Driver is not provided')
        setup_path = '\\Web\\AdminConsole\\Setup'

        self.getting_started_module = load_module(
            'getting_started',
            constants.AUTOMATION_DIRECTORY + setup_path)
        self.fs_gettting_started_module = load_module(
            'file_servers_getting_started',
            constants.AUTOMATION_DIRECTORY + setup_path)
        self.setup_module = load_module(
            'core_setup',
            constants.AUTOMATION_DIRECTORY + setup_path)

        self.setup_obj = self.setup_module.Setup(self.driver)
        self.getting_started = self.getting_started_module.GettingStarted(self.driver)
        self.fs_getting_started = self.fs_gettting_started_module.FileServers(self.driver)
        self.log = logger.get_log()
        self._solution = None
        self._fs_hostname_list = None
        self._fs_host_username = None
        self._fs_host_password = None
        self._fs_plan_name = None
        self._fs_backup_now = False
        self._pool_name = None
        self._media_agent = None
        self._mount_path = None
        self._partition_path = None
        self._reboot_required = False
        self.vsa_getting_started = None
        self.server_obj = None
        self._vsa_hostname = None
        self._vsa_hypervisor_name = None
        self._vsa_username = None
        self._vsa_password = None
        self._vm_group_name = None
        self._virtual_machine_list = None
        self._vsa_client = None
        self.company_obj = None
        self._storage = {'pri_storage':  None,
                         'pri_ret_period': '30'}

    @property
    def solution(self):
        """ Gets the solution selected"""
        return self._solution

    @solution.setter
    def solution(self, value):
        """ Sets the solution selected"""
        self._solution = value

    @property
    def pool_name(self):
        """ Gets the pool name"""
        return self._pool_name

    @pool_name.setter
    def pool_name(self, value):
        """ Sets the pool name"""
        self._pool_name = value

    @property
    def media_agent(self):
        """ Gets the media agent"""
        return self._media_agent

    @media_agent.setter
    def media_agent(self, value):
        """ Sets the media agent"""
        self._media_agent = value

    @property
    def mount_path(self):
        """ Gets the mount_path"""
        return self._mount_path

    @mount_path.setter
    def mount_path(self, value):
        """ Sets the mount_path selected"""
        self._mount_path = value

    @property
    def partition_path(self):
        """ Gets the partition_path"""
        return self._partition_path

    @partition_path.setter
    def partition_path(self, value):
        """ Sets the partition_path selected"""
        self._partition_path = value

    @property
    def fs_hostname_list(self):
        """ Gets the list of host names"""
        return self._fs_hostname_list

    @fs_hostname_list.setter
    def fs_hostname_list(self, value):
        """ Sets the list of host names"""
        self._fs_hostname_list = value

    @property
    def fs_host_username(self):
        """ Gets the username for the host where FS package is to be installed"""
        return self._fs_host_username

    @fs_host_username.setter
    def fs_host_username(self, value):
        """ Sets the username for the host where FS package is to be installed"""
        self._fs_host_username = value

    @property
    def fs_host_password(self):
        """ Gets the password for the host where FS package is to be installed"""
        return self._fs_host_password

    @fs_host_password.setter
    def fs_host_password(self, value):
        """ Sets the password for the host where FS package is to be installed"""
        self._fs_host_password = value

    @property
    def fs_plan_name(self):
        """ Gets the plan name"""
        return self._fs_plan_name

    @fs_plan_name.setter
    def fs_plan_name(self, value):
        """ Sets the fs plan name"""
        self._fs_plan_name = value

    @property
    def fs_backup_now(self):
        """ Gets the fs_backup_now """
        return self._fs_backup_now

    @fs_backup_now.setter
    def fs_backup_now(self, value):
        """ Sets the fs_backup_now selected"""
        self._fs_backup_now = value

    @property
    def reboot_required(self):
        """ Gets the reboot_required """
        return self._reboot_required

    @reboot_required.setter
    def reboot_required(self, value):
        """ Sets the fs_backup_now selected"""
        self._reboot_required = value

    @property
    def vsa_hostname(self):
        """ Gets the _vsa_hostname"""
        return self._vsa_hostname

    @vsa_hostname.setter
    def vsa_hostname(self, value):
        """ Sets the _vsa_hostname"""
        self._vsa_hostname = value

    @property
    def vsa_hypervisor_name(self):
        """ Gets the vsa_hypervisor_name"""
        return self._vsa_hypervisor_name

    @vsa_hypervisor_name.setter
    def vsa_hypervisor_name(self, value):
        """ Sets the _vsa_hypervisor_name"""
        self._vsa_hypervisor_name = value

    @property
    def vsa_username(self):
        """ Gets the vsa_username"""
        return self._vsa_username

    @vsa_username.setter
    def vsa_username(self, value):
        """ Sets the vsa_username"""
        self._vsa_username = value

    @property
    def vsa_password(self):
        """ Gets the vsa_password"""
        return self._vsa_password

    @vsa_password.setter
    def vsa_password(self, value):
        """ Sets the _vsa_password"""
        self._vsa_password = value

    @property
    def vm_group_name(self):
        """ Gets the _vm_group_name"""
        return self._vm_group_name

    @vm_group_name.setter
    def vm_group_name(self, value):
        """ Sets the _vm_group_name"""
        self._vm_group_name = value

    @property
    def virtual_machine_list(self):
        """ Gets the virtual_machine_list"""
        return self._virtual_machine_list

    @virtual_machine_list.setter
    def virtual_machine_list(self, value):
        """ Sets the_virtual_machine_list"""
        self._virtual_machine_list = value

    @property
    def storage(self):
        """ Gets the storage"""
        return self._storage

    @storage.setter
    def storage(self, value):
        """ Sets the storage"""
        self._storage = value

    @property
    def vsa_client(self):
        """ Gets the _vsa_client"""
        return self._vsa_client

    @vsa_client.setter
    def vsa_client(self, value):
        """ Sets the vsa_client"""
        self._vsa_client = value

    def edit_security_of_servers(self, associations):
        """
        Edits the security tile in servers page
        Returns:None

        """
        try:
            if not self.server_obj:
                self.server_obj = Servers(self.admin_console)
            self.server_obj.navigate_to_servers()
            self.server_obj.select_client(self.vsa_client)
            self.server_obj.add_security_associations(associations)
        except Exception as exp:
            self.log.info("%s", str(exp))
            if str(exp) == self.server_obj.props['error.duplicateAssociation']:
                return
            raise Exception(str(exp))

    def edit_infrastructure_tye_of_company(self, general_settings, company_name):
        """
        Edits the infrastructure type of a company
        Returns:None

        """
        if not self.company_obj:
            self.company_obj = CompanyDetails(self.admin_console)
        self.company_obj.navigate_to_companies()
        self.company_obj.select_hyperlink(company_name)
        # self.company_obj.companies.edit_general_settings(general_settings)--implement later

    def complete_fs_setup(self):
        """
        Completes the FS setup solution
        Returns:None

        """
        if self.__go_to_solutions_setup():
            step1 = self.fs_getting_started.props['label.createServerBackupPlan']
            self.log.info("STEP1:%s", step1)
            if not self.__check_if_step_is_completed(step1):
                self.fs_getting_started.add_file_server_plan(self.fs_plan_name,
                                                             self.storage)
            step2 = self.fs_getting_started.props['label.addFsServer']
            self.log.info("STEP2:%s", step2)
            go_to_next_step = self.__check_if_step_is_completed(step2)
            self.fs_getting_started.add_file_server(self.fs_hostname_list,
                                                        self.fs_host_username,
                                                        self.fs_host_password,
                                                        self.fs_plan_name,
                                                        self.reboot_required,
                                                        go_to_next_step)

            step3 = self.fs_getting_started.props['label.setupComplete']
            self.log.info("STEP3:%s", step3)
            if self.fs_backup_now:
                self.fs_getting_started.fs_setup_complete()

            self.__mark_setup_complete()
            self.log.info("setup completed, validating the completion")
            self.getting_started.navigate_to_getting_started()
            if self.getting_started.get_setup_completion_state(self.solution):
                self.log.info("FS setup completed successfully")

    def complete_vsa_setup(self):
        """
        Completes the FS setup solution
        Returns:None

        """
        if not self.vsa_getting_started:
            self.vsa_getting_started = Virtualization(self.driver)
        if self.__go_to_solutions_setup():
            step1 = self.vsa_getting_started.props['label.createServerBackupPlan']
            self.log.info("STEP1:%s", step1)
            if not self.__check_if_step_is_completed(step1):
                self.fs_getting_started.add_file_server_plan(self.fs_plan_name,
                                                             self.storage
                                                             )
            step2 = self.vsa_getting_started.props['label.addHypervisor']
            self.log.info("STEP2:%s", step2)
            if not self.__check_if_step_is_completed(step2):
                self.vsa_getting_started.add_hypervisor(self.vsa_hostname,
                                                        self.vsa_hypervisor_name,
                                                        self.vsa_username,
                                                        self.vsa_password)
            step3 = self.vsa_getting_started.props['action.showAddVMGroup']
            self.log.info("STEP3:%s", step3)
            if not self.__check_if_step_is_completed(step3):
                self.vsa_getting_started.add_vm_group(self.vm_group_name,
                                                      self.virtual_machine_list)

            step4 = self.vsa_getting_started.props['label.setupComplete']
            self.log.info("STEP3:%s", step4)
            if self.fs_backup_now:
                self.fs_getting_started.fs_setup_complete()


            self.__mark_setup_complete()

            self.log.info("setup completed, validating the completion")
            self.getting_started.navigate_to_getting_started()
            if self.getting_started.get_setup_completion_state(self.solution):
                self.log.info("VSA setup completed successfully")

    def __go_to_solutions_setup(self):
        """
        traverses from getting started to solutions page
        Returns:True if complete solution is clicked

        """
        self.log.info("Navigating to getting started")
        self.getting_started.navigate_to_getting_started()
        if self.getting_started.click_get_started():
            self.getting_started.wait_for_completion()
            self.__do_storage_configurations()
        if not self.getting_started.get_setup_completion_state(self.solution):
            self.getting_started.configure_wizard_for_solution(self.solution)
            return True
        self.log.info("solution is already completed")
        return False

    def __do_storage_configurations(self):
        """
        add a MA
        add storage pool
        Returns:None

        """
        step1 = "Add MediaAgent"
        self.log.info("STEP1:%s", step1)
        if not self.__check_if_step_is_completed(step1):
            self.__click_download_package_link()
            self.setup_obj.click_button("Continue")
        step2 = "Add storage pool"
        self.log.info("STEP1:%s", step2)
        if not self.__check_if_step_is_completed(step2):
            self.setup_obj.add_storage_pool(self.pool_name,
                                            media_agent=self.media_agent,
                                            path=self.mount_path,
                                            partition_path=self.partition_path)
            self.log.info('Successfully created Disk storage pool')

    def __click_download_package_link(self):
        """
        clicks the download link
        Returns:None

        """
        if self.setup_obj.check_if_entity_exists(
                'xpath', '//a[@data-ng-bind="ovaPackageDownloadLocation"]'):
            self.driver.find_element(By.XPATH, 
                "//a[@data-ng-bind='ovaPackageDownloadLocation']").click()
            self.getting_started.wait_for_completion()
        else:
            raise Exception("No link to download the package")

    def __check_if_step_is_completed(self, step):
        """
        Returns true if the step is completed for the solution in getting started or false
        otherwise

        Args:
            step        (str)   -- name of the step to be verified

        """
        ul_element = self.driver.find_element(By.XPATH, "//ul[@class='steps group']")
        li_elements = ul_element.find_elements(By.XPATH, "./li")
        for li_elem in li_elements:
            step_name = li_elem.find_element(By.XPATH, "./span").text
            if step_name == step:
                li_class = li_elem.get_attribute('class')
                if li_class in ('ng-scope done clickable', 'ng-scope current done'):
                    self.log.info("Step is completed :%s", step)
                    return True
                if li_class in ('ng-scope current warn', 'ng-scope current', 'ng-scope clickable'):
                    self.log.info("Step is not completed :%s", step)
                    return False
                raise Exception("state of the step could not be found")
        raise Exception("Step could not be found in this solution")

    def __mark_setup_complete(self):
        """
        Clicks the mark setup complete option in solution page
        Returns: None

        """
        try:
           self.fs_getting_started.select_hyperlink(
               self.fs_getting_started.props['setup.setupCompleted'])
        except Exception as exp:
            self.log.info(str(exp))
            try:
                self.fs_getting_started.select_hyperlink(
                    self.fs_getting_started.props['label.markAsComplete'])
            except Exception as exp:
                raise Exception(str(exp))
