import time

from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.cventities import CVActionsToolbar
from Web.AdminConsole.Components.core import SearchFilter
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import DropDown, ModalPanel, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import RCalendarView, TreeView
from Web.AdminConsole.Components.alert import Alert
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Hub.constants import GoogleWorkspaceAppTypes


class GoogleWorkspaceApps:

    def __init__(self, admin_console, app_type):
        """Init function for the metallic hub"""
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.app_type = app_type
        self.search_filter = SearchFilter(admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__dropdown = DropDown(self.__admin_console)
        self.__jobs = Jobs(self.__admin_console)
        self._alert = Alert(self.__admin_console)
        self.__modal_dialog = ModalDialog(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__rpanelInfo_obj = RPanelInfo(self.__admin_console)
        self.__Browse_obj = Browse(self.__admin_console, is_new_o365_browse=True)
        self.__RCalendarView_obj = RCalendarView(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__navigator = self.__admin_console.navigator
        self.__cvactions_toolbar = CVActionsToolbar(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__treeview = TreeView(self.__admin_console)

    @WebAction()
    def __select_agent(self):
        """Select the agent from the wizard"""
        title = self.__wizard.get_wizard_title()
        if title == "Configure Google Workspace app":
            if self.app_type == GoogleWorkspaceAppTypes.gdrive:
                agent_type = "Google Drive"
            else:
                agent_type = "Gmail"
            self.__wizard.select_radio_card(agent_type)
            self.__wizard.click_next()
            self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_region(self, region: str) -> None:
        """Helper method to select region while creating Google Workspace App
            Args:
                region(str) -- region if required
        """
        self.__wizard.select_drop_down_values(id='storageRegion', values=[region])
        self.__admin_console.wait_for_completion()

    def __create_custom_app(self, super_admin: str = None,
                            credential_name: str = None) -> None:
        """Creates custom app
            app_id   (str)          -- App id
            app_secret (str)        -- App secret
            dir_id(str)             -- Directory ID
            super_admin(str)       -- Global admin username (Default: None)
            global_pass(str)        -- Global admin password (Default: None)
            tenant_site_url(str)    -- Tenant URL for sharepoint app (Default: None)

        """
        self.__wizard.fill_text_in_field(id="googleAdminSMTP", text=super_admin)
        self.__wizard.select_drop_down_values(id='credentials', values=[credential_name])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __check_for_errors(self):
        """Checks for any errors while creating app"""
        error_xpaths = [
            "//div[contains(@class,'MuiAlert-standardError')]"
        ]

        for xpath in error_xpaths:
            if self.__admin_console.check_if_entity_exists('xpath', xpath):
                if self.__driver.find_element(By.XPATH, xpath).text:
                    raise CVWebAutomationException(
                        'Error while creating the app: %s' %
                        self.__driver.find_element(By.XPATH, xpath).text
                    )

    @WebAction(delay=2)
    def __click_sign_in_with_google(self):
        """Clicks Sign in with Google"""
        sign_in_with_google_xpath = "//*[name()='svg' and @id='sign-in-with-google-onboarding-icon']"
        self.__driver.find_element(By.XPATH, sign_in_with_google_xpath).click()
        self.__check_for_errors()

    @WebAction(delay=3)
    def __click_here_link(self):
        """Clicks on here hyperlink"""
        self.__admin_console.select_hyperlink("here")

    @WebAction(delay=3)
    def __switch_to_window(self, window):
        """Switch to specified window

                Args:
                    window (WebElement)  -- Window element to switch to
        """
        self.__driver.switch_to.window(window)

    @WebAction(delay=2)
    def __click_next(self):
        """Clicks Next Button"""
        next_btn_xpath = "//button/span[text()='Next']"
        self.__driver.find_element(By.XPATH, next_btn_xpath).click()

    @WebAction(delay=2)
    def __enter_email(self, email):
        """Enter email in email type input

                Args:
                    email (str)  --  Microsoft Global Admin email
        """
        self.__admin_console.fill_form_by_id('identifierId', email)
        self.__click_next()

    @WebAction(delay=2)
    def __enter_password(self, password):
        """Enter password into password type input

                Args:
                    password (str)  --  Global Admin password
        """
        self.__admin_console.fill_form_by_name('Passwd', password)
        self.__click_next()

    @PageService()
    def __sign_in_to_google(self, super_admin, password):
        """Method to sigin to google"""
        if len(self.__driver.window_handles) == 1:
            self.__click_here_link()

        admin_console_window = self.__driver.window_handles[0]
        google_signin_window = self.__driver.window_handles[1]

        self.__switch_to_window(google_signin_window)
        self.__enter_email(super_admin)
        self.__enter_password(password)

        self.__switch_to_window(admin_console_window)
        self.__admin_console.wait_for_completion()

        attempts = 3
        while attempts:
            success_xpath = "//div[contains(@class,'MuiAlert-standardSuccess')]"
            if self.__admin_console.check_if_entity_exists("xpath", success_xpath):
                break
            attempts -= 1
            time.sleep(5)
        self.__admin_console.click_button("Close")

    @WebAction(delay=1)
    def __click_confirm_requirements_box(self):
        """Click on requirements checkbox"""
        xpath = "//input[@id='appInstallationConfirmation']"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __get_app_name(self):
        """Gets app name for current client"""
        xpath = "//div[@class='tile-row-value-display']"
        elem = self.__driver.find_elements(By.XPATH, xpath)[0]
        return elem.text

    @PageService()
    def access_googleworkspace_app(self, app_name):
        """Accesses the Google Workspace app from the Google Workspace landing page

                Args:
                    app_name (str) : Name of the Google Workspace app to access

        """
        self.__admin_console.access_tab('Apps')
        self.__rtable.access_link(app_name)

    def __create_googleworkspace_app(self, name, super_admin, password, credential_name, is_express_config, region):
        """Creates GoogleWorkspace App

            Args:
                name(str)                   :  Name to be given to the app
                super_admin(str)            :  Global admin email id (Default: None)
                password(str)               :  Password for global admin (Default: None)
                is_express_config(boolean)  :  Time out for app creation
                region(str)                 :  Storage Region
        """
        self.__select_agent()
        self.__select_region(region)
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.fill_text_in_field(id='appNameField', text=name)
        if is_express_config:
            self.__click_sign_in_with_google()
            self.__sign_in_to_google(super_admin, password)
        else:
            self.__wizard.select_card("Custom configuration (Advanced)")
            self.__create_custom_app(super_admin, credential_name)
        self.__click_confirm_requirements_box()
        self.__wizard.click_button(name='Create')
        self.__admin_console.wait_for_completion()
        self.app_name = self.__get_app_name()
        self.log.info(f"Client Created Successfully with Name : {self.app_name}")
        self.__admin_console.click_button('Close')
        self.__admin_console.wait_for_completion()
        time.sleep(5)  # Wait for Discovery process to launch in access node

    @PageService()
    def create_googleworkspace_app(self, name, super_admin=None, password=None, credential_name=None,
                                   is_express_config=True,
                                   region="us-east1"):
        """
        Creates Google Workspace App
        """

        if is_express_config and not (super_admin and password):
            raise Exception("Global Admin and password are required")
        if self.__admin_console.check_if_entity_exists("xpath", "//div[@class='dashboard-tabs-container']"):
            self.__admin_console.access_tab("Apps")
            self.__rtable.access_toolbar_menu("Add google workspace app")
            self.__admin_console.wait_for_completion()
        self.__create_googleworkspace_app(name, super_admin, password, credential_name, is_express_config, region)

    @PageService()
    def __wait_while_discovery_in_progress(self, time_out=600, poll_interval=60):
        """Waits for cache to get populated

            Args:
                time_out (int): Time out
                poll_interval (int): Regular interval for check
        """
        attempts = time_out // poll_interval
        search_text = "//*[contains(text(),'cache last updated on')]"
        while not self.__admin_console.check_if_entity_exists(By.XPATH, search_text):
            if attempts == 0:
                raise CVWebAutomationException("Discovery exceeded Stipulated time. Testcase terminated.")
            self.log.info("Please wait while the discovery is in progress")
            time.sleep(20)
            self.__rtable.reload_data()
            attempts -= 1

    @PageService()
    def add_content(self, users, plan=None):
        """Adds users to the Google Workspace APp

            Args:
                users (list)    : List of users to be added to the client
                plan (str)     : Name of plan to be selected
                                    //Default: None
        """
        self.__admin_console.access_tab('Content')
        self.__rtable.access_toolbar_menu('Add')
        self.__wizard.select_card("Add content to backup")
        self.__wizard.click_button(id="Submit")
        if self.app_type == GoogleWorkspaceAppTypes.gdrive:
            self.__wizard.select_card("Users")
        else:
            self.__wizard.select_card("Mailboxes")
        self.__wizard.click_button(id="Next")
        self.__wait_while_discovery_in_progress()
        self.__rtable.select_rows(users, search_for=True)
        self.log.info(f'Users added: {users}')
        self.__wizard.click_button(id="Next")
        self.__wizard.select_drop_down_values(id="cloudAppsPlansDropdown",
                                              values=[plan])
        self.log.info(f'Selected Google Workspace Plan: {plan}')
        self.__wizard.click_button(id="Next")
        self.__wizard.click_button(id="Submit")
        self.__admin_console.wait_for_completion()

    @WebAction(delay=2)
    def __click_app_restore(self):
        """Clicks the restore button on the app page"""
        self.__driver.find_element(By.XPATH, "//button[@id='APP_LEVEL_RESTORE']").click()
        self.__admin_console.wait_for_completion()

    @WebAction(delay=2)
    def __click_backup(self):
        """Clicks the backup button on the app page"""
        self.__driver.find_element(By.ID, "BACKUP").click()

    @WebAction(delay=2)
    def __select_all_entities(self):
        """Selects all pages across the table"""
        self.__rtable.select_all_rows()

    @WebAction(delay=2)
    def __job_details(self, job_id=None):
        """Waits for job completion and gets the job details"""
        try:
            job_id = self._alert.get_jobid_from_popup(wait_time=5)
        except CVWebAutomationException:
            self.__driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
            self.__admin_console.click_button("View jobs")
            self.__jobs.access_active_jobs()
            job_id = self.__jobs.get_job_ids()[0]
        job_details = self.__jobs.job_completion(job_id=job_id)
        job_details['Job Id'] = job_id
        self.log.info('job details: %s', job_details)
        if job_details[self.__admin_console.props['Status']] not in ["Completed"]:
            raise CVWebAutomationException('Job did not complete successfully')
        return job_details

    @PageService()
    def run_backup(self):
        """Runs backup by selecting all the associated users to the app"""
        if self.app_type == GoogleWorkspaceAppTypes.gdrive:
            self.__admin_console.access_tab('Users')
        else:
            self.__admin_console.access_tab('Mailboxes')
        self.__select_all_entities()
        self.__click_backup()
        self.__rmodal_dialog.click_submit()
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def get_rows_from_browse(self):
        """
        navigates to browse and return rows count
        """
        self.__click_app_restore()
        time.sleep(15)
        self.__admin_console.wait_for_completion()
        return int(self.__rtable.get_total_rows_count())

    @PageService()
    def browse_destination_details(self, name):
        """Browses and selects the out-of-place destination
        """
        self.__wizard.click_icon_button_by_title('Browse')
        self.__rtable.search_for(name)
        self.__admin_console.wait_for_completion()
        self.__rtable.select_rows([name])
        self.__rmodal_dialog.click_submit()

    @WebAction()
    def __select_folder_destination(self, path):
        """
        select_folder_destination
        """
        self.__driver.find_element(
            By.XPATH, f"//li[contains(@class,'k-treeview-item')]//span[contains(text(),'{path}')]").click()

    @PageService()
    def browse_destination_path(self, path):
        """Browses and selects the out-of-place destination
        """
        self.__wizard.click_icon_button_by_title('Browse')
        self.__select_folder_destination(path)
        self.__rmodal_dialog.click_submit()

    @PageService()
    def _enter_details_in_restore_panel(self,
                                        destination,
                                        file_location_details=None,
                                        oop_details=None,
                                        restore_option=None):
        """
        Enters the details in the Restore Options panel

        Args:
            destination --  Specifies the destination
            file_server --  Name of server where files have to be restored
            dest_path   --  Path to which the files have to be restored
            user_name   --  User to which files have to be restored
            restore_option  --  Specifies what to fo if file already exists

        """
        if destination == 'Restore to Disk':
            self.__wizard.select_card("File location")
            self.__wizard.select_drop_down_values(id="fileServersDropdown", values=[file_location_details["server"]])
            self.browse_destination_path(file_location_details["path"])
        elif destination == 'Restore to original location':
            self.__wizard.select_drop_down_values(id="agentDestinationDropdown", values=["Restore the data to its "
                                                                                         "original location"])
        elif destination == 'Restore to a Google Drive account':
            self.__wizard.select_drop_down_values(id="agentDestinationDropdown",
                                                  values=["Restore the data to another"
                                                          "location"])
            self.__wizard.select_drop_down_values(id="googleDriveDestinationDropdown",
                                                  values=[oop_details["type"]])
            self.browse_destination_details(oop_details["name"])
            self.browse_destination_path(oop_details["path"])

        self.__wizard.click_next()
        if restore_option:
            if restore_option == 'UNCONDITIONALLY_OVERWRITE':
                self.__wizard.select_radio_button(id="OVERWRITE")
            elif restore_option == 'RESTORE_AS_COPY':
                self.__wizard.select_radio_button(id="RESTORE_AS_COPY")
            else:
                self.__wizard.select_radio_button(id="SKIP")

    @WebAction(delay=2)
    def _click_restore(self, recovery_point=False):
        """Clicks the browse button on the app page"""
        self.__rtable.access_toolbar_menu("Restore")
        if recovery_point:
            xpath = '//li[@id="batch-action-menu_BROWSE_RECOVERY_POINT"]//a[@id="BROWSE_RECOVERY_POINT"]'
            self.__driver.find_element(By.XPATH, xpath).click()
        else:
            self.__driver.find_element(By.XPATH, "//li[@id='RESTORE_ENTIRE_CONTENT']").click()

    @PageService()
    def run_restore(self,
                    destination,
                    content=None,
                    file_location_details=None,
                    oop_details=None,
                    restore_option=None):
        """
        Runs the restore by selecting all users associated to the app

        Args:
            destination (str):  Specifies the destination
                                Acceptable values: to_disk, in_place, out_of_place
            users (list):       List of users to be selected for Restore
            restore_option:     Whether to Skip, Restore as copy or Overwrite for In-place restore

            file_location_details = {"server":"proxy,"path":"C:\new"}
            oop_details ={"type":"User","name":"brian neuhaus","path":"folder_name"}
            oop_details ={"type":"SharedDrive","name":"ADdrive","path":"folder_name"}


        Returns:
            job_details (dict): Details of the restore job

        """
        if self.app_type == GoogleWorkspaceAppTypes.gdrive:
            self.__admin_console.access_tab('Users')
        else:
            self.__admin_console.access_tab('Mailboxes')
        if content:
            self.__rtable.select_rows(content, search_for=True,partial_selection=True)
        else:
            self.__rtable.select_all_rows()
        self._click_restore()
        self.__admin_console.wait_for_completion()
        self._enter_details_in_restore_panel(
            destination=destination,
            file_location_details=file_location_details,
            oop_details=oop_details,
            restore_option=restore_option)
        self.__wizard.click_next()
        self.__wizard.click_submit()
        self.__admin_console.wait_for_completion()
        job_id = self.__wizard.get_job_id()
        job_details = self.__job_details(job_id=job_id)
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def get_retention_period(self):
        """Returns retention period of the Google Workspace  plan"""
        retention_panel = RPanelInfo(self.__admin_console, title='Retention')
        retention_details = retention_panel.get_details()
        return retention_details.get(self.__admin_console.props['label.retentionPeriod'],
                                     retention_details.get(self.__admin_console.props['label.retentionDays']))

    @PageService()
    def get_converted_retention_period(self, retention_period):
        """Converts the retention period to no of days format and returns it

             Args:
                    retention_period(str) : retention period
                    // Example: '5-years', 'infinite'

        """
        self.log.info(f'Given retention period : {retention_period}')
        retention_dict = {
            '5-years': '1825 days',
            '7-years': '2555 days',
            'infinite': 'Infinite',
            'enterprise': '1095 days',
            'standard': '365 days'
        }
        # Need to implement this conversion completely. For now taking static values
        converted_retention_period = retention_dict[retention_period]
        self.log.info(f'Converted retention period : {converted_retention_period}')
        return converted_retention_period

    @PageService()
    def get_plans_list(self):
        """Gets the list of available plans"""
        try:
            plans = self.__rtable.get_column_data(self.__admin_console.props['tableHeader.planName'])
        except ValueError:
            plans = self.__rtable.get_column_data('Profile name')
        self.log.info("plans: %s" % plans)
        for plan in plans:
            if 'google-workspace-plan' in plan:
                self.gw_plan = plan
                break
        return plans

    @PageService()
    def verify_retention_of_gw_plans(self, tenant_name, plans):
        """Verifies retention for Google Workspace plans

            Args:
                    tenant_name(str) : name of the tenant/company

                    plans(list)      : list of plans

        """
        tenant_name = tenant_name.lower()
        for plan in plans:
            if 'google-workspace-plan' in plan:
                expected_retention = self.get_converted_retention_period(
                    plan.split(tenant_name)[-1].split('google-workspace-plan')[0].split('-')[1])
                self.__rtable.access_link(plan)
                actual_retention = self.get_retention_period()
                if expected_retention != actual_retention:
                    raise Exception(f'Retention is not set correctly for {plan}'
                                    f'Expected Value: {expected_retention}, Actual Value: {actual_retention}')
                else:
                    self.log.info(f'Retention is set correctly for {plan}')

    @PageService()
    def verify_google_usage_report(self):
        """Verifies usage report for Google Workspace tenant"""
        self.__admin_console.select_hyperlink(link_text="Google Workspace - Enterprise")

