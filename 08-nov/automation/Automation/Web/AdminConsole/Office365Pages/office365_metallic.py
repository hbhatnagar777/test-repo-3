from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This file consists of only one class Office365Metallic
"""


import time

from selenium.common.exceptions import StaleElementReferenceException
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException


class MetallicJobs(Jobs):
    """Class for Job Operations in Metallic for Office 365 Apps Jobs"""

    def __init__(self, admin_console):
        """Constructor for Office365Metallic class"""
        super(MetallicJobs, self).__init__(admin_console)
        self._admin_console = admin_console
        self._driver = self._admin_console.driver

    @WebAction(delay=2)
    def __click_view_job_details(self):
        """Clicks on view job details"""
        self._admin_console.select_hyperlink(self._admin_console.props['label.viewJobDetails'])

    @WebAction(delay=2)
    def __get_job_status(self):
        """Read job status"""
        try:
            return self._driver.find_element(By.XPATH, 
                "//span[contains(text(),'Status')]/following-sibling::span"
            ).text
        except StaleElementReferenceException:
            pass

    @WebAction(delay=2)
    def __get_job_progress(self):
        """Read job progress"""
        if self._admin_console.check_if_entity_exists(
                "xpath", "//span[contains(text(),'Progress')]/following-sibling::span"):
            return self._driver.find_element(By.XPATH, 
                "//span[contains(text(),'Progress')]/following-sibling::span"
            ).text
        return ""

    @PageService()
    def resume_job(self):
        """Resumes the job"""
        self._admin_console.select_hyperlink(self._admin_console.props['Resume'])

    @PageService()
    def kill_job(self):
        """Kills the job"""
        self._admin_console.select_hyperlink(self._admin_console.props['Kill'])

    @PageService()
    def wait_for_job_completion(self, job_id, retry=5):
        """
        Waits for the job to complete

        Args:
            job_id (str):   Id of the job to wait for
            retry (int):    Number of times the job has to be resumed, if it goes into pending state

        """
        job_id = str(job_id)
        self._admin_console.navigator.navigate_to_jobs()
        if self.if_job_exists(job_id):
            self.access_job_by_id(job_id)
        else:
            self.access_job_history()
            self.show_admin_jobs()
            if not self.if_job_exists(job_id):
                raise CVWebAutomationException(
                    f"Job {job_id} is not present in Active Jobs or Job History")
            self.access_job_by_id(job_id)
        self.__click_view_job_details()
        while True:
            time.sleep(60)
            self._driver.refresh()
            self._admin_console.wait_for_completion()
            status = self.__get_job_status()
            if status == "Running" or status == 'Waiting':
                progress = self.__get_job_progress()
                if progress == '100%':
                    retry = 0
                    while retry < 18:
                        time.sleep(10)
                        self._driver.refresh()
                        self._admin_console.wait_for_completion()
                        status = self.__get_job_status()
                        if status == "Running" or status == 'Waiting':
                            retry += 1
                            continue
                        else:
                            break
                    else:
                        raise CVWebAutomationException(f"Job Status is not getting updated correctly. "
                                                       f"Job progress says 100 % but status still shows as "
                                                       f"'{status}' even after 3 minutes of wait")
                else:
                    self.log.info("Waiting for Job %s to complete.", str(job_id))
                    time.sleep(10)
                    continue

            if status == 'Pending':
                if retry > 0:
                    self.log.info('Job in Pending state. Resuming job..')
                    self.resume_job(job_id)
                    retry = retry - 1
                    continue
                else:
                    self.log.info(f'Job in Pending state for the {retry + 1}th time. Killing job..')
                    self.kill_job(job_id)
                    time.sleep(30)
                    continue
            elif status in ["Failed", "Killed", "Failed to Start"]:
                raise CVWebAutomationException(f'Job failed to complete successfully with Status: {status}')
            else:
                self.log.info(f'Job completed with status: {status}')
                break

    @PageService()
    def get_job_details(self):
        """
        Gets the job details

        Returns:
            (dict): Dictionary containing job details

        """
        summary_panel = PanelInfo(self._admin_console, title='Job summary')
        summary = summary_panel.get_details()
        details_panel = PanelInfo(self._admin_console, title='Job details')
        details = details_panel.get_details()
        return {**summary, **details}


class Office365Metallic(Office365Apps):
    """Class for all Office 365 Apps page"""

    def __init__(self, tcinputs, admin_console):
        """Constructor for Office365Metallic class"""
        super(Office365Metallic, self).__init__(tcinputs, admin_console)
        self.metallic_jobs = MetallicJobs(self._admin_console)
        self.__table = Table(self._admin_console)
        self.backedup_mails = None
        self.restored_mails = None

    @WebAction(delay=2)
    def _click_add_onedrive_user(self):
        """Clicks on Add User button of office365 client"""
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        self._driver.find_element(By.XPATH, "//a[@id='ID_USER']").click()
        self._driver.find_element(By.XPATH, 
            f"//a[@id='ADD_CONTENT']/span[normalize-space()="
            f"'{self._admin_console.props['action.label.addUsers']}']"
        ).click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_add_sharepoint_site(self):
        """Clicks on Add button of office365 SharePoint client"""
        self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        self._driver.find_element(By.XPATH, "//a[@id='ADD']/span[1]").click()
        self._driver.find_element(By.XPATH, 
            f"//a[@id='ADD_SUBCLIENT']/span[normalize-space()="
            f"'{self._admin_console.props['action.addSubclient']}']"
        ).click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _get_mb_refresh_error_msg(self):
        """Gets the Mailbox refresh error message for Metallic"""
        mailbox_refresh_error_xpath = "//p[@class='serverMessage error']"
        return self._driver.find_element(By.XPATH, mailbox_refresh_error_xpath).text

    @WebAction(delay=2)
    def _enter_subclient_name(self, subclient_name):
        """Enters the subclient name of Office 365 OneDrive client"""
        input_element = self._driver.find_element(By.ID, 'subclientName')
        input_element.clear()
        input_element.send_keys(subclient_name)

    @WebAction(delay=2)
    def _click_add_user_checkbox(self, username):
        """Clicks the checkbox to add the users"""
        self._driver.find_element(By.XPATH, 
            f"//*[contains(text()[2], '{username}')]/"
            f"ancestor::tr/td[contains(@id,'checkbox')]"
        ).click()

    @WebAction(delay=2)
    def _click_backup(self):
        """Clicks the backup button on the app page"""
        self.__table.access_toolbar_menu(menu_id='archive')

    @WebAction(delay=2)
    def _get_app_name(self):
        """Gets the app name from the app page. Useful for Metallic app"""
        app_type = self.tcinputs['office_app_type']
        if app_type == Office365Apps.AppType.share_point_online:
            app_name_xpath = "//h1[@data-ng-bind='O365ClientDetailsCtrl.clientName']"
        else:
            app_name_xpath = "//div[@id='cv-changename']//h1"
        return self._driver.find_element(By.XPATH, app_name_xpath).text

    @WebAction(delay=2)
    def _expand_restore_options(self):
        """Expands restore options"""
        self._driver.find_element(By.XPATH, 
            f"//span[normalize-space()='{self._admin_console.props['header.messagelevel.options']}'"
            f" or normalize-space()='{self._admin_console.props['header.filelevel.options']}']"
        ).click()

    @WebAction(delay=2)
    def _click_overwrite_radio_button(self):
        """Clicks the radio button for unconditionally overwrite"""
        self._driver.find_element(By.XPATH, 
            '//input[@type="radio" and @value="UNCONDITIONALLY_OVERWRITE"]'
        ).click()

    @PageService()
    def get_all_office365_apps(self):
        """
        List of all App Names
        """
        return self.__table.get_column_data(self._admin_console.props['label.appName'])

    @PageService()
    def create_metallic_office365_app(self, time_out=600, poll_interval=10):
        """
        Creates O365 App

        Args:

            time_out (int): Time out for app creation

            poll_interval (int): Regular interval for app creating check
        """

        # General Required details
        app_type = self.tcinputs['office_app_type']
        name = self.tcinputs['Name']

        if name in set(self.get_all_office365_apps()):
            raise CVWebAutomationException("App name already exists")

        self._create_app(app_type)

        if (app_type == Office365Apps.AppType.exchange_online or
                app_type == Office365Apps.AppType.one_drive_for_business):
            # Required details for Exchange Online
            global_admin = self.tcinputs['GlobalAdmin']
            password = self.tcinputs['Password']

            self._admin_console.fill_form_by_id('appName', name)

            if self.tcinputs['Region']:
                self._dropdown.select_drop_down_values(
                    values=[self.tcinputs['Region']],
                    drop_down_id='createOffice365App_isteven-multi-select_#1167')
            self._admin_console.fill_form_by_id('globalUserName', global_admin)
            self._admin_console.fill_form_by_id('globalPassword', password)

            self._click_create_azure_ad_app()

            attempts = time_out // poll_interval
            while True:
                if attempts == 0:
                    raise CVWebAutomationException('App creation exceeded stipulated time.'
                                                   'Test case terminated.')
                self._LOG.info("App creation is in progress..")

                self._admin_console.wait_for_completion()
                self._check_for_errors()

                # Check authorize app available

                if self._admin_console.check_if_entity_exists(
                        "link", self._admin_console.props['action.authorize.app']):
                    break

                time.sleep(poll_interval)
                attempts -= 1
            self._verify_modern_authentication()
            self._authorize_permissions(global_admin, password)
        elif app_type == Office365Apps.AppType.share_point_online:
            # Required details for SharePoint Online V1
            sharepoint_admin = self.tcinputs['SharePointAdmin']
            password = self.tcinputs['Password']
            tenant_admin_site_url = self.tcinputs['TenantAdminSiteURL']
            self._admin_console.fill_form_by_id('appName', name)
            self._admin_console.fill_form_by_id('adminSiteURL', tenant_admin_site_url)
            self._admin_console.fill_form_by_id('username', sharepoint_admin)
            self._admin_console.fill_form_by_id('password', password)
            app_name_prefix_xpath = "//span[@data-ng-bind='addOffice365.office365AppPrefix']"
            self.tcinputs['Name'] = self._driver.find_element(By.XPATH, app_name_prefix_xpath).text + name
        self._admin_console.submit_form()
        self._admin_console.wait_for_completion()
        time.sleep(5)

    @PageService()
    def delete_office365_app(self, app_name):
        """Deletes the office365 app
                Args:
                    app_name (str)  --  Name of the office365 app to delete

        """
        steps = ['Disable', 'Delete']
        for i in range(2):
            self.__table.access_action_item(app_name, steps[i])
            self._modal_dialog.click_submit()

    @PageService()
    def get_plans_list(self):
        """Gets the list of available plans"""
        plans = self.__table.get_column_data('Plan name')
        self._LOG.info("plans: %s" % plans)
        for plan in plans:
            if 'O365Plan' in plan:
                self.tcinputs['ExchangePlan'] = plan

    @PageService()
    def get_app_name(self):
        """Fetches the name of the created app. This is useful for metallic app"""
        return self._get_app_name()

    @PageService()
    def add_user(self):
        """Adds user to the office365 app"""
        while True:
            self._open_add_user_panel()
            self._admin_console.wait_for_completion()
            mailbox_refresh_error_xpath = "//p[@class='serverMessage error']"
            if self._admin_console.check_if_entity_exists('link', self._admin_console.props['action.refresh']):
                while self._admin_console.check_if_entity_exists(
                        'link', self._admin_console.props['action.refresh']):
                    time.sleep(60)
                    self._admin_console.select_hyperlink(self._admin_console.props['action.refresh'])
                break
            elif self._admin_console.check_if_entity_exists('xpath', mailbox_refresh_error_xpath):
                error_message = self._get_mb_refresh_error_msg()
                if error_message == "The mailbox list is getting refreshed. Please check back in few minutes.":
                    self._modal_dialog.click_cancel()
                    self._admin_console.wait_for_completion()
                    time.sleep(60)
                    continue
            else:
                break
        self._dropdown.select_drop_down_values(values=[self.tcinputs['ExchangePlan']],
                                               drop_down_id='exchangePlan_isteven-multi-select_#2')
        for user in self.users:
            search_element = self._driver.find_element(By.ID, 'searchInput')
            if search_element.is_displayed():
                self._admin_console.fill_form_by_id(element_id='searchInput', value=user)
            self.__table.select_rows([user.split("@")[0]])
        self._admin_console.submit_form()

    @PageService()
    def add_onedrive_users(self):
        """Adds user to the office365 app"""
        self._click_add_onedrive_user()
        self._dropdown.select_drop_down_values(values=['## New user group ##'],
                                               index=0)
        self._enter_subclient_name(self.tcinputs['OneDriveSubclientName'])
        for user in self.users:
            search_element = self._driver.find_element(By.ID, 'searchInput')
            if search_element.is_displayed():
                self._admin_console.fill_form_by_id(element_id='searchInput', value=user)
            self._click_add_user_checkbox(user.split("@")[0])
        self._admin_console.submit_form()

    @PageService()
    def add_sharepoint_sites(self):
        """Adds sites to the office365 app"""
        self._click_add_sharepoint_site()
        self._enter_subclient_name(self.tcinputs['OneDriveSubclientName'])
        self._driver.find_element(By.XPATH, "//a[@id='addAction']").click()
        self._admin_console.wait_for_completion()
        site_url = self.tcinputs['SiteURL']
        site_xpath = "//span[@class='path-title ng-binding' and text()='" + site_url + "']"
        self._driver.find_element(By.XPATH, site_xpath).click()
        self._admin_console.submit_form()
        self._admin_console.submit_form()

    @PageService()
    def wait_for_onedrive_bkpjob(self):
        """Waits for the OneDrive Automatic backup job to launch"""
        self.__table.apply_filter_over_column(
            column_name='Subclient',
            filter_term=self.tcinputs['OneDriveSubclientName'])
        if int(self.__table.get_total_rows_count()) == 0:
            self.__table.clear_column_filter(column_name='Subclient')
            row_count = int(self.__table.get_total_rows_count())
            while int(self.__table.get_total_rows_count()) <= row_count:
                time.sleep(10)
                self._driver.refresh()
                self._admin_console.wait_for_completion()
            self.__table.apply_filter_over_column(
                column_name='Subclient',
                filter_term=self.tcinputs['OneDriveSubclientName'])

    @PageService()
    def kill_automatically_launched_job(self):
        """Kills the job which is launched automatically"""
        self.view_jobs()
        self.open_active_jobs_tab()
        while int(self.__table.get_total_rows_count()) == 0:
            time.sleep(10)
            self._driver.refresh()
            self._admin_console.wait_for_completion()
        app_type = self.tcinputs['office_app_type']
        if app_type == self.AppType.one_drive_for_business or app_type == self.AppType.share_point_online:
            self.wait_for_onedrive_bkpjob()
        job_id = str(self.__table.get_column_data('Job Id')[0])
        self._jobs.kill_job(job_id)
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _job_details(self, job_id):
        """Waits for job completion and gets the job details"""
        self.metallic_jobs.wait_for_job_completion(job_id)
        job_details = self.metallic_jobs.get_job_details()
        self._LOG.info('job details: %s', job_details)
        if job_details[self._admin_console.props['Status']] not in [
                "Committed", "Completed", 'Completed w/ one or more errors']:
            raise CVWebAutomationException('Job did not complete successfully')
        return job_details

    @PageService()
    def run_backup(self):
        """Runs backup by selecting all the associated users to the app"""
        app_type = self.tcinputs['office_app_type']
        if app_type == self.AppType.exchange_online:
            self._select_all_users()
            self._click_backup()
            self._modal_dialog.click_submit()
        elif (app_type == self.AppType.one_drive_for_business
              or app_type == self.AppType.share_point_online):
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            self.__table.access_action_item(
                entity_name=self.tcinputs['OneDriveSubclientName'],
                action_item='Back up',
                partial_selection=True)
            backup_details = PanelInfo(self._admin_console)
            backup_details.submit()
        job_id = self._admin_console.get_jobid_from_popup()
        job_details = self._job_details(job_id)
        self._LOG.info('job details: %s', job_details)
        self.backedup_mails = int(job_details['Number of files transferred'])

    @PageService()
    def run_restore(self, mailbox=True):
        """Runs the restore by selecting all users associated to the app

                Args:
                    mailbox  (Boolean)  --  Whether to restore mailbox or messages
        """
        app_type = self.tcinputs['office_app_type']
        if app_type == self.AppType.exchange_online:
            self._select_all_users()
        elif (app_type == self.AppType.one_drive_for_business
              or app_type == self.AppType.share_point_online):
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            self.__table.access_action_item(
                entity_name=self.tcinputs['OneDriveSubclientName'],
                action_item='Restore',
                partial_selection=True)
            self._click_selectall_browse()
        self._click_restore(mailbox)
        self._admin_console.wait_for_completion()
        self._expand_restore_options()
        self._click_overwrite_radio_button()
        self._admin_console.submit_form(wait=False)
        job_id = self._admin_console.get_jobid_from_popup()
        job_details = self._job_details(job_id)
        self._LOG.info('job details: %s', job_details)
        self.restored_mails = int(job_details['Number of files transferred'])
