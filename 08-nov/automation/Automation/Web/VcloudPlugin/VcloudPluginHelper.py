"""
Classes:
    VcloudPluginHelper -> This class contains all the helper functions related to the vCloud Plugin

    Functions:

    __init__()                              -- initialise an instance of the VcloudPluginHelper class
    _navigate_to_vcloud()                   -- navigate to the vcloud login page
    _select_tab()                           -- Select a Tab from plugin
    _navigate_to_plugin()                   -- Login to the VCD page and access the Commvault plugin
    _login()                                -- Login to vcloud portal using username and password
    _configure_plugin()                     -- Configure plugin by navigating to the configuration tab, modifying the configuration, filling the credentials,
        then choosing a hypervisor
    setup()                                 -- Navigate to plugin and configure it
    backup()                                -- Filters vm list by name, vapp, vdc and submits a backup job and tracks it to completion
    restore()                               -- Filters vm list by name, vapp, vdc and submits a restore job and tracks it to completion
    _navigate_to_tenant_portal()            -- Waits for provider page to load, then navigates to tenant portal
    _navigate_in_virtual_machine_tab()      -- Navigate within virtual machines tab
    _filter_by_vm_name()                    -- Filter list of VMs by name
    _filter_by_vapp()                       -- Filter list of VMs by vapp
    _filter_by_vdc()                        -- FIlter list of VMs by vdc
    _select_first_vm()                      -- Select the first VM from the list of VMs
    _submit_backup()                        -- Submit backup job for the selected vm
    _get_job_id()                           -- Wait for alert to show up and, get job id from the alert
    _submit_restore()                       -- Submit inplace Restore with unconditional override for the selected VM
    _guest_files_restore()                  -- Click on the guest files restore button
    _navigate_in_sidebar()                  -- Navigate to a tab on the sidebar
    _modify_config()                        -- Click on the modify configurations button
    _fill_config_credentials()              -- Fill the configuration credentials such as Commvault End Point, Username, and Password
    _hypervisor_form()                      -- Selects the hypervisor for configuration
    backup_and_restore()                    -- Loop over all VMs and back them up and restore them
    end_user_login()                        -- Login to plugin as end user, and enter credentials on cc
    vcloud_login()                          -- Use the vcloud api to start a session
    vcloud_request_get()                    -- Send a get request
    vcloud_request_post()                   -- Send a post request
    vcloud_request_put()                    -- Send a put request
    vcloud_request_delete()                 -- Send a delete request
    upload_plugin()                         -- Delete plugin if it exists and upload plugin
    enable_advanced_view()                  -- Enable Advanced view on plugin
"""

import base64
import json
import os
from time import sleep

import requests
from selenium.webdriver.common.keys import Keys

from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import PageService, WebAction

from selenium.webdriver.common.by import By
from Server.JobManager.jobmanager_helper import JobManager
from cvpysdk.job import Job
from cvpysdk.commcell import Commcell


class VcloudPluginHelper(AdminConsole):
    """
    Helper for vcloud plugin automation
    """

    def __init__(self, browser=None, commcell_setup=None, vcloud_setup=None, commcell=None):
        """
        vCloudPluginHelper class initialisation

        Args:
            browser: Browser object
            commcell_setup: Contains commcell credentials from input.json
            vcloud_setup: Contains vcloud_setup details from input.json
            commcell: Contains the commcell object
        """
        super(VcloudPluginHelper, self).__init__(browser, commcell_setup['commcellUsername'])
        self.driver = browser.driver
        self.username = vcloud_setup['username']
        self.password = vcloud_setup['password']
        self.url = vcloud_setup['url']
        self.org = vcloud_setup['org']
        self.tenant = vcloud_setup['tenant']
        self.vms = vcloud_setup['vms']
        self.hypervisor = vcloud_setup['hypervisor']
        self.commcell = commcell
        self.job_obj = None
        self.commcell_setup = commcell_setup
        self.session = None
        self.path = vcloud_setup['plugin_path']

    @PageService()
    def _navigate_to_vcloud(self, org=None):
        """
        To navigate to the vcloud director login page

        Args:
            org     (str)   -   Name of the organisation in the VCD we want to navigate to. If None goes to provider
                                page.
        """
        try:
            login_url = 'https://' + self.url
            if org:
                login_url += '/tenant/' + self.org
            else:
                login_url += '/' + 'provider'
            self.navigate(login_url)
            self.log.info('Successfully navigated to the vcloud portal')
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @PageService()
    def _select_tab(self, title):
        """
        Select a tab from the plugin

        Args:
            title   (str)   -       Title of the vCloud Plugin Tab
        """
        try:
            tab_header = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{title}')]"
                                                            "/parent::*[contains(@class, 'nav-link')]").click()
            tab_header.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _navigate_to_plugin(self, org=None):
        """
        Login to the VCD page and access the Commvault plugin

        Args:
            org (str) - the short name of the organisation you want to log into
        """
        try:
            self._login(org)
            self.wait_for_element_based_on_xpath(
                "//*[contains(text(), 'More') and contains(@class, 'dropdown-toggle')]", 500)
            if not org:
                self._navigate_to_tenant_portal()
            self.wait_for_element_based_on_xpath(
                "//*[contains(text(), 'More') and contains(@class, 'dropdown-toggle')]", 500)
            self.driver.find_element(By.XPATH,
                                     "//*[contains(text(), 'More') and contains(@class, 'dropdown-toggle')]").click()
            self.wait_for_completion()
            self.driver.find_element(By.XPATH,
                                     "//*[contains(text(), 'Commvault Data Protection') and contains(@role, 'menuitem')]") \
                .click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _login(self, org = None):
        """
        Login to vcloud portal using username and password

        Args:
            org (str) - the short name of the organisation you want to log into
        """
        try:
            self._navigate_to_vcloud(org)
            self.wait_for_element_based_on_xpath("//input[@id='usernameInput']", 10)
            username = self.driver.find_element(By.XPATH, "//input[@id='usernameInput']")
            password = self.driver.find_element(By.XPATH, "//input[@id='passwordInput']")

            username.clear()
            username.send_keys(self.username, Keys.ENTER)

            password.clear()
            password.send_keys(self.password, Keys.ENTER)
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @PageService()
    def setup(self):
        """
        Navigates to plugin and configures it
        """
        try:
            self._navigate_to_plugin()
            self._navigate_in_sidebar("Configuration")
            self._modify_config()
            self._fill_config_credentials()
            self._hypervisor_form()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @PageService()
    def backup(self, vm):
        """
        This function contains the backup automation logic

        Args:
            vm (object) - Contains details of VM about to be backed up.
        """
        try:
            self._navigate_in_sidebar("Virtual Machines")
            sleep(5)
            self._filter_by_vm_name(vm_name=vm['vm_name'])
            self._filter_by_vapp(vapp=vm['vapp'])
            self._filter_by_vdc(vdc=vm['vdc'])
            self._select_first_vm()
            self._submit_backup()

            job_id = self._get_job_id()
            if job_id == -1:
                self.log.error("Job already exists")

            self.job_obj = Job(self.commcell, job_id)
            if self.job_obj.wait_for_completion():
                self.log.info("Job Completed")
            else:
                self.log.error("Job Failed")
                raise Exception("Backup Job Failed")

        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @PageService()
    def restore(self, vm, oop=False, standalone=True):
        """
        This function contains the restore automation logic

        Args:
            vm (object) - Contains details of VM about to be backed up.
            oop (bool) - True if we want to do an out of place restore
            standalone (bool) - True if we want to do a standalone restore
        """
        try:
            self._navigate_in_sidebar("Virtual Machines")
            sleep(5)
            self._filter_by_vm_name(vm_name=vm['vm_name'])
            self._filter_by_vapp(vapp=vm['vapp'])
            self._filter_by_vdc(vdc=vm['vdc'])
            self._select_first_vm()
            self._submit_restore()
            job_id = self._get_job_id()
            if job_id == -1:
                return
            self.job_obj = Job(self.commcell, job_id)
            if self.job_obj.wait_for_completion():
                self.log.info("Job Completed")
            else:
                self.log.error("Job Failed")
                raise Exception("Restore Job Failed")

            #submit oop restore
            if not oop:
                return
            self._select_first_vm()
            self._submit_restore(oop, standalone, vapp_dest=vm['destinationVapp'])
            job_id = self._get_job_id()
            if job_id == -1:
                return
            self.job_obj = Job(self.commcell, job_id)
            if self.job_obj.wait_for_completion():
                self.log.info("Job Completed")
            else:
                self.log.error("Job Failed")
                raise Exception("OOP Restore Job Failed")

        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @PageService()
    def _navigate_to_tenant_portal(self):
        """
        Waits for provider page to load, then navigates to tenant portal
        """
        try:
            self.wait_for_element_based_on_xpath("//span[@class='title']", 100)
            tenant_url = 'https://' + self.url + '/tenant/' + self.tenant
            self.log.info('Navigating to ' + tenant_url)
            self.navigate(tenant_url)
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _navigate_in_virtual_machine_tab(self, tab="protected"):
        """
        Navigate to tab specified in 'tab' arg

        Args:
            tab (string) - holds the name of the tab we want to navigate to in the virtual machines tab. Possible values
            are "protected", "unprotected", "active jobs"
        """
        try:
            self.wait_for_element_based_on_xpath("//button[@id='"+tab+"Button']", 100)
            protected_tab = self.driver.find_element(By.XPATH, "//button[@id='"+tab+"Button']")
            protected_tab.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _filter_by_vm_name(self, vm_name):
        """
        Filter list of VMs by name

        Args:
            vm_name     (str)   -   Name of the VM you want to filter by
        """
        try:
            filter_icon = self.driver.find_element(By.XPATH,
                                                   "//clr-icon[@shape='vm']/../.."
                                                   "//button[contains(@class, 'datagrid-filter-toggle')]")
            filter_icon.click()
            self.wait_for_completion()
            search_bar = self.driver.find_element(By.XPATH, "//input[@name='search']")
            search_bar.clear()
            search_bar.send_keys(vm_name, Keys.ENTER)
            self.wait_for_completion()
            close_icon = self.driver.find_element(By.XPATH, "//button[contains(@class, 'clr-smart-close-button')]")
            close_icon.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _filter_by_vapp(self, vapp):
        """
        Filter list of VMs by vapp

        Args:
            vapp     (str)   -   Name of the vapp you want to filter by
        """
        try:
            filter_icon = self.driver.find_element(By.XPATH,
                                                   "//clr-icon[@shape='vmw-app']/../"
                                                   "..//button[contains(@class, 'datagrid-filter-toggle')]")
            filter_icon.click()
            self.wait_for_completion()
            self.log.info('XPATH for Vapp is ' + f"//input[@id='{vapp}']")
            vapp_selection = self.driver.find_element(By.XPATH, f"//label[@for='{vapp}']")
            vapp_input = self.driver.find_element(By.XPATH, f"//input[@id='{vapp}']")
            if not vapp_input.is_selected():
                vapp_selection.click()

            self.wait_for_completion()
            close_icon = self.driver.find_element(By.XPATH, "//button[contains(@class, 'clr-smart-close-button')]")
            close_icon.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _filter_by_vdc(self, vdc):
        """
        Filter list of VMs by vdc

        Args:
            vdc     (str)   -   Name of the vdc you want to filter by
        """
        try:
            filter_icon = self.driver.find_element(By.XPATH,
                                                   "//clr-icon[@shape='data-cluster']/../"
                                                   "..//button[contains(@class, 'datagrid-filter-toggle')]")
            filter_icon.click()
            self.wait_for_completion()
            self.log.info('XPATH for VDC is ' + f"//input[@id='{vdc}']")
            vdc_selection = self.driver.find_element(By.XPATH, f"//label[@for='{vdc}']")
            vdc_input = self.driver.find_element(By.XPATH, f"//input[@id='{vdc}']")

            if not vdc_input.is_selected():
                vdc_selection.click()

            self.wait_for_completion()
            close_icon = self.driver.find_element(By.XPATH, "//button[contains(@class, 'clr-smart-close-button')]")
            close_icon.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _select_first_vm(self):
        """
        Select the first VM from the list of VMs
        """
        try:
            self.wait_for_element_based_on_xpath("(//div[@class='datagrid-table']//label[@class='clr-control-label ng-star-inserted'])[1]", 100)
            sleep(5)
            input_radio = self.driver.find_element(By.XPATH,
                                                   "(//div[@class='datagrid-table']//label[@class='clr-control-label ng-star-inserted'])[1]")
            input_radio.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _submit_backup(self):
        """
        Submit backup job for the selected VM
        """
        try:
            backup_button = self.driver.find_element(By.XPATH, "//button/clr-icon[@shape='backup']")
            backup_button.click()
            self.wait_for_completion()
            sleep(5)
            backup_confirm = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Back up')]")
            backup_confirm.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _get_job_id(self):
        """
        Wait for alert to show up and, get job id from the alert
        """
        try:
            self.wait_for_element_based_on_xpath("//div[@class='alert-items']//span", 100)
            alert_element = self.driver.find_element(By.XPATH, "//div[@class='alert-items']//span")
            alert_text = alert_element.text
            self.log.info(alert_text)
            job_id_list = alert_text.split("Job Id: ")
            if len(job_id_list) == 0:
                self.log.info('Another job is running')
                # fail if another job is running
                return -1
            else:
                job_id = job_id_list[1].split(".")[0]
                self.log.info(job_id)
                close_alert = self.driver.find_element(By.XPATH, "//button[@aria-label='Close alert']")
                close_alert.click()
                return job_id
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _submit_restore(self, oop=False, standalone=True, vapp_dest=""):
        """
        Submit inplace Restore with option to restore inplace or outofplace or as a standalone vm

        Args:
            vm (object) - Contains details of VM about to be backed up.
            oop (bool) - True if we want an out of place restore
            standalone (bool) - True if we want to do a standalone restore
            vapp_dest (str) - Name of the destination vapp if we are doing an oop restore
        """
        try:
            restore_button = self.driver.find_element(By.XPATH, "//button/clr-icon[@shape='backup-restore']")
            restore_button.click()
            self.wait_for_completion()
            sleep(5)
            if oop:
                oop_button = self.driver.find_element(By.XPATH, "//label[@for='outOfPlace']")
                oop_button.click()
                if not standalone:
                    vapp_dropdown = self.driver.find_element(By.XPATH, "//form//clr-icon[@shape='caret down']")
                    vapp_dropdown.click()
                    selected_vapp = self.driver.find_element(By.XPATH,
                                                             "//button[@title='" + vapp_dest + "']")
                    selected_vapp.click()
                else:
                    stand_alone = self.driver.find_element(By.XPATH, "//label[@for='standAloneVMRestore']")
                    stand_alone.click()
                self.wait_for_completion()
            else:
                inplace_button = self.driver.find_element(By.XPATH, "//label[@for='inPlace']")
                inplace_button.click()

            unconditional_override = self.driver.find_element(By.XPATH, "//label[@for='unConditionalVMOverride']")
            unconditional_override.click()
            self.wait_for_completion()
            restore_confirm = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Restore')]")
            restore_confirm.click()
            self.wait_for_completion()

        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _guest_files_restore(self):
        """
        Click on the guest files restore button
        """
        try:
            file_restore_button = self.driver.find_element(By.XPATH, "//button/clr-icon[@shape='file-group']")
            file_restore_button.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _navigate_in_sidebar(self, tab=""):
        """
        Navigate to chosen tab in the sidebar

        Args:
            tab:  Can take the following values ["Dashboard", "Virtual Machines", "Configuration", "Advanced View"]
        """
        try:
            self.wait_for_element_based_on_xpath("//span[contains(text(), '"+tab+"')]", 300)
            self.wait_for_completion()
            sleep(15)
            selected_tab = self.driver.find_element(By.XPATH, "//span[contains(text(), '"+tab+"')]")
            selected_tab.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _modify_config(self):
        """"
        Click on the modify configurations button
        """
        try:
            self.wait_for_element_based_on_xpath("//button[contains(text(), 'Modify')]", 10)
            modify_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Modify')]")
            modify_button.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _fill_config_credentials(self):
        """
        Fill the configuration credentials such as Commvault End Point, Username, and Password
        """
        try:
            self.wait_for_element_based_on_xpath("//input[@id='cvEndPoint']", 10)
            cv_end_point = self.driver.find_element(By.XPATH, "//input[@id='cvEndPoint']")
            cv_end_point.clear()
            cv_end_point.send_keys("https://" + self.commcell_setup['webconsoleHostname'], Keys.ENTER)
            self.wait_for_completion()

            self.wait_for_element_based_on_xpath("//input[@id='username']", 10)
            username_input = self.driver.find_element(By.XPATH, "//input[@id='username']")
            username_input.clear()
            username_input.send_keys(self.commcell_setup['commcellUsername'], Keys.ENTER)
            self.wait_for_completion()

            password_input = self.driver.find_element(By.XPATH, "//input[@id='password']")
            password_input.clear()
            password_input.send_keys(self.commcell_setup['commcellPassword'], Keys.ENTER)
            self.wait_for_completion()

            next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
            next_button.click()

        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @WebAction()
    def _hypervisor_form(self):
        """
        Selects the hypervisor for configuration
        """
        try:
            self.wait_for_element_based_on_xpath("//label[contains(text(), 'Hypervisor')]/..//clr-icon[@shape='caret down']", 120)
            dropdown_icon = self.driver.find_element(By.XPATH,
                                                     "//label[contains(text(), 'Hypervisor')]/..//clr-icon[@shape='caret down']")
            dropdown_icon.click()
            self.wait_for_element_based_on_xpath("//clr-dropdown-menu//button[contains(text(), '" + self.hypervisor + "')]", 120)
            sleep(5)
            dropdown_option = self.driver.find_element(By.XPATH,
                                                       "//clr-dropdown-menu//button[contains(text(), '" + self.hypervisor + "')]")
            dropdown_option.click()
            self.wait_for_completion()
            next_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
            next_button.click()
            self.wait_for_completion()
            self.wait_for_element_based_on_xpath("//span[contains(text(), 'Complete')]", 300)
            complete_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Complete')]")
            complete_button.click()
            self.wait_for_completion()
            self.wait_for_element_based_on_xpath("//span[contains(text(), 'OK')]", 300)
            ok_button = self.driver.find_element(By.XPATH, "//span[contains(text(), 'OK')]")
            ok_button.click()
            self.wait_for_completion()

        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)

    @PageService()
    def backup_and_restore(self, end_user=False, oop=False, standalone=True):
        """
            Backup vm then restore it

            Args:
            end_user (bool) - True if we have logged in as an end_user
            oop (bool) - True if we want an out of place restore
            standalone (bool) - True if we want to do a standalone restore
        """

        for vm in self.vms:
            try:
                if not end_user:
                    self.backup(vm)
                self.restore(vm, oop, standalone)
            except Exception as ex:
                self.log.error(ex)
                raise Exception(ex)
        self.log.info("All VMs completed")


    @WebAction()
    def end_user_login(self):
        """
            Login to plugin as end user, and enter credentials on cc
        """
        try:
            self._navigate_to_plugin(self.tenant)
            self.wait_for_element_based_on_xpath("//input[@id='password']", 100)
            password = self.driver.find_element(By.XPATH, "//input[@id='password']")
            password.clear()
            password.send_keys("")
            login_button = self.driver.find_element(By.XPATH, "//a[@id = 'loginbtn']")
            login_button.click()
            self.wait_for_element_based_on_xpath("//input[@id='username']", 100)
            username = self.driver.find_element(By.XPATH, "//input[@id='username']")
            username.clear()
            username.send_keys(self.commcell_setup['commcellUsername'])
            password.send_keys(self.commcell_setup['commcellPassword'])
            login_button.click()
            self.wait_for_completion()
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)


    @PageService()
    def vcloud_login(self, vcloud_url, username, password):
        """
            Login to vCloud and start a session

            Args:
                vcloud_url (str) - url of the vcloud you want to run this testcase on
                username (str) - the username of the user you want to login as
                password (str) - the password of the user you want to login as
        """
        Accept = 'application/*+json;version=36.0,application/json;version=36.0'
        Pair = f'{username}:{password}'
        EncodedPair = base64.b64encode(Pair.encode('utf-8')).decode()
        Authorization = f'Basic {str(EncodedPair)}'
        apiheaders = {'Authorization': Authorization, 'Accept': Accept}
        vcloud_url = vcloud_url + 'api/sessions'
        res = requests.post(
            vcloud_url,
            headers=apiheaders,
            verify=False)
        if res.ok:
            s = requests.Session()
            s.verify = False
            s.headers.update(
                {'Accept': Accept, 'x-vcloud-authorization': res.headers['x-vcloud-authorization']})
            return s
        else:
            print(f'vCloud login failed, {vcloud_url}, {username}')
            print(f'Response: {res.status_code}\n{res.text}\n')


    @PageService()
    def vcloud_request_get(self, url):
        """
        Send get request to vcloud

        Args:
            url (str) - The url to which you want to send a get request
        """
        self.log.info('Get request: '+url)
        res = self.session.get(url)
        return res

    @PageService()
    def vcloud_request_post(self, url, body):
        """
        Send  post request to vcloud

        Args:
            url (str) - The url to which you want to send a post request
            body (str) - The body of the post request
        """
        if len(body) == 0:
            res = self.session.post(url)
        else:
            res = self.session.post(url, json=body)
        return res

    @PageService()
    def vcloud_request_put(self, url, path):
        """
        Send put request to vcloud

        Args:
            url (str) - The url to which you want to send a put request
            body (str) - The body of the put request
        """
        res = self.session.put(url, data=open(path, 'rb'))
        res = self.session.get(url)
        return res

    @PageService()
    def vcloud_request_delete(self, url):
        """
        Send delete request ot vcloud

        Args:
            url (str) - The url to which you want to send a post request
        """
        res = self.session.delete(url)
        return res

    @PageService()
    def upload_plugin(self):
        """
        Delete plugin if it exists and upload plugin
        """
        try:
            vcloud_url = 'https://' + self.url + '/'
            self.session = self.vcloud_login(vcloud_url, self.username+'@system', self.password)
            if self.session == None:
                raise Exception('Could not log into vcloud')

            logged_in = True

            plugin_url = vcloud_url + 'cloudapi/extensions/ui/'
            allPlugin = json.loads(self.vcloud_request_get(plugin_url).text)
            for plugin in allPlugin:
                if "Commvault" in plugin["pluginName"]:
                    url = plugin_url + plugin["id"]
                    self.log.info("deleting" + url)
                    self.vcloud_request_delete(url)
            body = {"pluginName": "Commvault Data Protection",
                    "description": "A self-service portal to perform commvault data protection operation on vCD environment.",
                    "enabled": "true", "license": "Copyright (C) Commvault 2020-2021.  All rights reserved.",
                    "link": "https://ma.commvault.com/Support", "vendor": "Commvault", "version": "10.3.2",
                    "tenant_scoped": "true", "provider_scoped": "true"}
            res = self.vcloud_request_post(plugin_url, body)
            plugin_details = json.loads(res.text)
            plugin_id = plugin_details["id"]
            url = plugin_url + plugin_id + '/tenants/publishAll'
            self.vcloud_request_post(url, "")
            url = plugin_url + plugin_id + '/plugin'

            file_size = os.path.getsize(self.path)
            body = {"fileName":"commvaultvcdplugin10.x.zip","size":file_size}
            res = self.vcloud_request_post(url, body)
            url = res.links["upload:default"]["url"]
            res = self.vcloud_request_put(url, self.path)
        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)


    @WebAction()
    def enable_advanced_view(self):
        """
        Enable Advanced view on plugin
        """
        try:
            self._navigate_in_sidebar("Configuration")
            sleep(10)
            advView = self.driver.find_element(By.XPATH, "//input[@name='Advanced View']")
            wrapper = self.driver.find_element(By.XPATH, "//input[@name='Advanced View']/..")
            if not advView.is_selected():
                wrapper.click()

        except Exception as ex:
            self.log.error(ex)
            raise Exception(ex)
