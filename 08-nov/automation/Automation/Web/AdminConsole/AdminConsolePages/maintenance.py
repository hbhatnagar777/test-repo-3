# -*- coding: utf-8 -*-s

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Maintenance page on the AdminConsole

MaintenanceTiles:

    access_tile()                       --  Method to access tile displayed on maintenance page

    access_tile_settings()              --  Method to access tile settings

    run_job_for_tile()                  --  Method to run job for given tile

    run_job_for_tile_entity()           --  Method to run job for some entity inside tile

Maintenance:

    access_http_proxy()                  --  loads http proxy tile from maintenance page

    access_dr_backup()                   --  loads DR backup tile from maintenance page

    access_internet_options()            --  loads download software tile from maintenance page

    access_download_software()           --  loads Internet options tile from maintenance page

    access_install_update_schedules()    --  loads Install update schedule tile from
                                             maintenance page

    edit_download_schedule()            --   Edits the system created download schedule.

    add_schedule()                      --   Adds new download schedule

    add_install_schedule()              --   Creates a new installation schedule on the given
                                             clients/client group.

    run_install_updates()               --   runs install updates job for the given clients/client groups

    run_copy_software()                 --  Runs copy software job with configured settings

    run_download_software()             --   Runs  download software job with configured settings.

    disable_http_proxy()                --   Disables http proxy

    set_internet_options()              --   Configures internet gateway from maintenance page.

    enable_http_proxy()                 --   set up http proxy on commcell.

DRBackupDaily:

    access_dr_backup()                  --  loads DR backup tile from maintenance page.

    edit()                              --  Method to edit the DR backup settings.

    access_dr_backup_destinations()     --  Method to access DR backup destinations.

"""
from datetime import datetime

from AutomationUtils import logger
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.core import TreeView, Toggle
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Components.panel import DropDown, PanelInfo, RDropDown
from Web.AdminConsole.Components.browse import CVAdvancedTree
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Helper import adminconsoleconstants as acdefines
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.Common.exceptions import CVWebAutomationException


class MaintenanceTiles:
    """ Maintenance Tile class """

    def __init__(self, admin_console):
        """ Initialize the backup object

        Args:
            admin_console: instance of AdminConsoleBase

        """
        self._driver = admin_console.driver
        self._admin_console_base = admin_console
        self.drop_down = DropDown(admin_console)

    @WebAction()
    def access_tile(self, tile_header):
        """ Method to access tile displayed on maintenance page """
        self._admin_console_base.access_tile(tile_header)

    @WebAction()
    def access_tile_settings(self, tile_header):
        """ Method to access tile settings """
        tile_setting_icon = self._driver.find_element(By.XPATH, 
            f"//cv-tile-component[@data-title='{tile_header}']"
            f"//div[contains(@class,'page-details-box-links')]//div[contains(text(),'Edit')]")
        tile_setting_icon.click()

    @WebAction()
    def run_job_for_tile(self, tile_header):
        """ Method to run job for given tile """
        self._admin_console_base.click_button_using_text(tile_header)

    @WebAction()
    def schedule_job_for_tile(self, tile_header):
        """ Method to run job for given tile """
        tile_run_icon = self._driver.find_element(By.XPATH, 
            f"//cv-tile-component[@data-title='{tile_header}']"
            f"//div[contains(@class,'page-details-box-links')]//div[contains(text(),'{self._admin_console_base.props['label.schedule']}')]")
        tile_run_icon.click()

    @WebAction()
    def run_job_for_tile_entity(self, tile_header, entity_label):
        """ Method to run job for some entity inside tile """
        entity_run_icon = self._driver.find_element(By.XPATH, 
            f"//cv-tile-component[@data-title='{tile_header}']"
            f"//a[contains(text(),'{entity_label}')]/ancestor::li//div[contains(text(),'Run')]"
        )
        entity_run_icon.click()


class _HttpProxy:
    """Class for http proxy panel use Maintenance object access_http_proxy to get this object"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: instance of AdminConsoleBase
        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self.http_panel = PanelInfo(self._admin_console, 'HTTP proxy')

    @PageService()
    def enable_http_proxy(
            self,
            proxy_server,
            proxy_port
    ):
        """
        Enables http proxy

        Args:
            proxy_server    (str)  :  Host name or IP address of the proxy server.

            proxy_port      (int)  :  port no on which proxy server listens to.

        """
        key = self._admin_console.props['label.proxyServer']
        proxy_toggle = self.http_panel.get_toggle_element(key)
        if self.http_panel.is_toggle_enabled(proxy_toggle):
            self.http_panel.edit_tile_entity(key)
            self._admin_console.wait_for_completion()
        else:
            self.http_panel.enable_toggle(key)
            self._admin_console.wait_for_completion()
        self._admin_console.fill_form_by_id("proxyServer", proxy_server)
        self._admin_console.fill_form_by_id("proxyPort", proxy_port)
        self._admin_console.submit_form()

    @PageService()
    def disable_http_proxy(self):
        """ Disables http proxy"""
        self._admin_console.disable_toggle(index=0)  # use id once id added to toggle-control tag

    @PageService()
    def enable_authentication(self, proxy_user_name, proxy_password):
        """
        Enables http proxy authentication
        Args:
            proxy_user_name (str): Proxy user name
            proxy_password  (str): Proxy password
        """
        key = self._admin_console.props['label.availableAuthentication']
        user_authentication_toggle = self.http_panel.get_toggle_element(key)
        if self.http_panel.is_toggle_enabled(user_authentication_toggle):
            self.http_panel.edit_tile_entity(key)
            self._admin_console.wait_for_completion()
        else:
            self.http_panel.enable_toggle(key)
            self._admin_console.wait_for_completion()
        self._admin_console.fill_form_by_id("userName", proxy_user_name)
        self._admin_console.fill_form_by_id("password", proxy_password)
        self._admin_console.fill_form_by_id("confirmPassword", proxy_password)
        self._admin_console.submit_form()

    @PageService()
    def disable_authentication(self):
        """ Disables http proxy authentication"""
        self._admin_console.disable_toggle(index=1)  # use id once id added to toggle-control tag


class Maintenance:
    """
    This class provides the function or operations that can be performed on the
    maintenance page on the AdminConsole
    """

    def __init__(self, admin_console):
        """
        Method to initiate Maintenance class
        Args:
            admin_console: instance of AdminConsoleBase
        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self.admin_page = self._admin_console.navigator
        self.__maintenance_tile = MaintenanceTiles(self._admin_console)
        self.company = Companies(self._admin_console)
        self._cv_advanced_tree = CVAdvancedTree(admin_console)
        self._rtable = Rtable(self._admin_console)
        self._admin_console.load_properties(self)

    @WebAction()
    def _add_one_time_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit one time schedule using the given options
        Usage:
            * sample dict for schedule options

                schedule_options:
                {
                    'year': '2017',
                    'month': 'december',
                    'date': '31',
                    'hours': '09',
                    'mins': '19',
                    'session': 'AM'
                }
        """
        self.__maintenance_tile.drop_down.select_drop_down_values(0, [self._admin_console.props['option.oneTime']])
        if schedule_options:
            self._admin_console.date_picker(schedule_options)

    @WebAction()
    def _add_automatic_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit automatic schedule using the given options

        Args:
            schedule_options (dict)     -- automatic schedule options to be selected

        Usage:
            * sample dict for schedule options

                schedule_options:
                {
                    'frequency': 'Automatic'
                    'min_job_interval_hrs': '24',
                    'min_job_interval_mins': '30',
                    'max_job_interval_hrs': '72',
                    'max_job_interval_mins': '45',
                    'min_sync_interval_hrs': '1',
                    'min_sync_interval_mins': '30',
                    'ignore_operation_window': True,
                    'only_wired': True,
                    'min_bandwidth': True,
                    'bandwidth': '128',
                    'use_specific_network': True,
                    'specific_network_ip_address': '0.0.0.0',
                    'specific_network': '24',
                    'start_on_ac': True,
                    'stop_task': True,
                    'prevent_sleep': True,
                    'cpu_utilization_below': True,
                    'cpu_below_threshold': '10',
                    'start_only_files_bkp': True
                }

        **Note** For Automatic there is NO default value

        """
        self.__maintenance_tile.drop_down.select_drop_down_values(0, [self._admin_console.props['option.automatic']])
        # To fill the Min job interval
        if schedule_options.get('min_job_interval_hrs') and schedule_options.get(
                'min_job_interval_mins'):
            self._admin_console.fill_form_by_id("minBackupIntervalHours",
                                                schedule_options['min_job_interval_hrs'])
            self._admin_console.fill_form_by_id("minBackupIntervalMinutes",
                                                schedule_options['min_job_interval_mins'])

        # To fill the Max job interval
        if schedule_options.get('max_job_interval_hrs') and schedule_options.get(
                'max_job_interval_mins'):
            self._admin_console.fill_form_by_id("maxBackupIntervalHours",
                                                schedule_options['max_job_interval_hrs'])
            self._admin_console.fill_form_by_id("maxBackupIntervalMinutes",
                                                schedule_options['max_job_interval_mins'])

        if schedule_options.get('min_sync_interval_hrs') and \
                schedule_options.get('min_sync_interval_mins'):
            self._admin_console.fill_form_by_id("minSyncIntervalHours",
                                                schedule_options['min_sync_interval_hrs'])
            self._admin_console.fill_form_by_id("minSyncIntervalMinutes",
                                                schedule_options['min_sync_interval_mins'])

            if schedule_options.get('ignore_operation_window'):
                self._admin_console.checkbox_select("ignoreAtMaxInterval")

        # To fill the Network Management
        # To select the wired network checkbox
        if schedule_options.get('only_wired'):
            self._admin_console.checkbox_select("onlyWiredWork")

        # To select the min network bandwidth checkbox
        if schedule_options.get('min_bandwidth'):
            self._admin_console.checkbox_select("minBandwidth")
            if schedule_options.get('bandwidth'):
                self._admin_console.fill_form_by_id("bandwidth", schedule_options['bandwidth'])
            else:
                raise Exception('Bandwidth argument missing for Automatic schedule')

        # To select the specific network checkbox
        if schedule_options.get('use_specific_network'):
            self._admin_console.checkbox_select("specificNetwork")
            if schedule_options.get('specific_network_ip_address') and \
                    schedule_options.get('specific_network'):
                self._admin_console.fill_form_by_name("specificNetworkIpAddress",
                                                      schedule_options['specific_network_ip_address'])
                self._driver.find_element(By.XPATH, 
                    "//input[@id='specificNetwork'and @type='number']").send_keys(
                        schedule_options['specific_network'])
            else:
                raise Exception("Specific network arguments missing in automatic schedule")

        # Power Management
        # To select A/C power checkbox
        if schedule_options.get('start_on_ac'):
            self._admin_console.checkbox_select("startOnAC")

        # To select the stop task checkbox
        if schedule_options.get('stop_task'):
            self._admin_console.checkbox_select("StopTask")

        # To select the prevent sleep checkbox
        if schedule_options.get('prevent_sleep'):
            self._admin_console.checkbox_select("preventSleep")

        # Resource Utilization
        if schedule_options.get('cpu_utilization_below'):
            self._admin_console.checkbox_select("cpuBelowThresholdEnabled")
            if schedule_options.get('cpu_below_threshold'):
                self._admin_console.fill_form_by_id("cpuBelowThreshold", schedule_options['cpu_below_threshold'])
            else:
                raise Exception('CPU threshold missing in automatic schedule')

        # File Management
        if schedule_options.get('start_only_files_bkp'):
            self._admin_console.checkbox_select("startOnlyFileBackUp")

    @WebAction()
    def _add_daily_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit daily schedule using the given options

        Args:
            schedule_options (dict)     -- daily schedule options to be selected
        Usage:
                    {
                        'frequency': 'Daily',
                        'hours': '09',
                        'mins': '15',
                        'session': 'AM',
                        'repeatMonth': '1',
                        'exceptions': True,
                        'day_exceptions': True,
                        'week_exceptions': True,
                        'exception_days': ['monday','friday'],
                        'exception_weeks': ['First', 'Last'],
                        'repeat': True,
                        'repeat_hrs': '8',
                        'repeat_mins': '25',
                        'until_hrs': '11',
                        'until_mins': '59',
                        'until_sess': 'PM'
                    }
        """
        self.__maintenance_tile.drop_down.select_drop_down_values(0, [self._admin_console.props['option.daily']])
        if schedule_options.get('repeatDay'):
            self._admin_console.fill_form_by_id("dayFrequency", schedule_options.get('repeatDay'))

    @WebAction()
    def _add_weekly_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit weekly schedule using the given options

        Args:
            schedule_options (dict)     -- weekly schedule options to be selected
        Usage:
                    {
                        'frequency': 'Weekly',
                        'hours': '09',
                        'mins': '15',
                        'session': 'AM',
                        'days': ['Monday', 'Friday', 'Sunday'],
                        'repeatDay': '1',
                        'exceptions': True,
                        'day_exceptions': True,
                        'week_exceptions': True,
                        'exception_days': ['monday','friday'],
                        'exception_weeks': ['First', 'Last'],
                        'repeat': True,
                        'repeat_hrs': '8',
                        'repeat_mins': '25',
                        'until_hrs': '11',
                        'until_mins': '59',
                        'until_sess': 'PM'
                    }


        """

        self.__maintenance_tile.drop_down.select_drop_down_values(0, [self._admin_console.props['option.weekly']])
        if schedule_options.get('days'):
            self.__maintenance_tile.drop_down.select_drop_down_values(1, schedule_options['days'])
        if schedule_options.get('repeatWeek'):
            self._admin_console.fill_form_by_id("weekFrequency", schedule_options.get('repeatWeek'))

    @WebAction()
    def _add_monthly_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit monthly schedule using the given options

        Args:
            schedule_options (dict)     -- monthly schedule options to be selected
        Usage:
             schedule_options =         {
                        'frequency': 'Monthly',
                        'hours': '09',
                        'mins': '15',
                        'session': 'AM',
                        'day_of_month': '25',
                        'custom_week': 'Second',
                        'custom_day': 'Weekend Day',
                        'repeatMonth': '1',
                        'exceptions': True,
                        'day_exceptions': True,
                        'week_exceptions': True,
                        'exception_days': ['Monday','Friday'],
                        'exception_weeks': ['First', 'Last'],
                        'repeat': True,
                        'repeat_hrs': '8',
                        'repeat_mins': '25',
                        'until_hrs': '11',
                        'until_mins': '59',
                        'until_sess': 'PM'
                    }

        """
        self.__maintenance_tile.drop_down.select_drop_down_values(0, [self._admin_console.props['option.monthly']])

        if schedule_options.get('day_of_month'):
            self._admin_console.fill_form_by_id("dayOfMonth", schedule_options['day_of_month'])
        elif schedule_options.get('custom_week') and schedule_options.get('custom_day'):
            self._admin_console.select_radio("monthly_relative")
            self.__maintenance_tile.drop_down.select_drop_down_values(1, schedule_options['custom_week'])

            self.__maintenance_tile.drop_down.select_drop_down_values(2, schedule_options['custom_day'])
        else:
            raise Exception('Arguments missing for Monthly schedule')

        if schedule_options.get('repeatMonth'):
            self._admin_console.fill_form_by_id("monthRelativeFrequency", schedule_options.get('repeatMonth'))

    @WebAction()
    def _add_continuous_schedule(
            self,
            schedule_options=None
    ):
        """
        To add or edit continuous schedule using the given options

        Usage:

                schedule_options:
                {
                    'continuous_interval': '30'
                }

        **Note** There are NO default values for continuous schedule
        """
        self.__maintenance_tile.drop_down.select_drop_down_values(0, self._admin_console.props['option.continous'])
        if schedule_options.get('continuous_interval'):
            self._admin_console.fill_form_by_id("intervalBetweenTwoJobs", schedule_options['continuous_interval'])
        else:
            raise Exception('Job interval missing for continuous schedule')

    @WebAction()
    def _schedule_repeat(self, schedule_options):
        """
        To edit schedule repeat using the given options
        Usage:
            * sample dict for schedule options

                schedule_options:
                {
                    'exceptions': True,
                    'day_exceptions': False
                    'week_exceptions': True,
                    'exception_days': ['monday','friday'],
                    'exception_weeks': ['First', 'Last'],
                    'repeat': True,
                    'repeat_hrs': '8',
                    'repeat_mins': '25',
                    'until_hrs': '11',
                    'until_mins': '59',
                    'until_sess': 'PM',
                }
        """
        if schedule_options.get('repeat'):
            self._admin_console.checkbox_select("repeat")

        # To fill the repeat hours and mins
        if schedule_options.get('repeat_hrs') and schedule_options.get('repeat_mins'):
            self._admin_console.fill_form_by_id("repeatHours", schedule_options['repeat_hrs'])
            self._admin_console.fill_form_by_id("repeatMinutes", schedule_options['repeat_mins'])

        # To fill the time to stop the schedule
        if schedule_options.get('until_hrs') and schedule_options.get('until_mins'):
            self._driver.find_element(By.XPATH, 
                "//*[@id='repeatTime']/table/tbody/tr[2]/td[1]/input").clear()
            self._driver.find_element(By.XPATH, 
                "//*[@id='repeatTime']/table/tbody/tr[2]/td[1]/input").send_keys(
                    schedule_options['until_hrs'])
            self._driver.find_element(By.XPATH, 
                "//*[@id='repeatTime']/table/tbody/tr[2]/td[3]/input").clear()
            self._driver.find_element(By.XPATH, 
                "//*[@id='repeatTime']/table/tbody/tr[2]/td[3]/input"
            ).send_keys(schedule_options['until_mins'])

            # To change session AM or PM in repeat
            if schedule_options.get('until_sess'):
                sess = self._driver.find_element(By.XPATH, 
                    "//*[@id='repeatTime']/table/tbody/tr[2]/td[6]/button")
                if not schedule_options.get('until_sess') == sess.text:
                    sess.click()

        # To fill the Exceptions in Repeat schedule
        if schedule_options.get('exceptions'):
            self._admin_console.select_hyperlink("Exceptions")

            if schedule_options.get('day_exceptions'):
                self._admin_console.select_radio("dayInMonth")
                if schedule_options.get('exception_days'):
                    self.__maintenance_tile.drop_down.select_drop_down_values(0,
                                                                              schedule_options['exception_days'])
                if self._admin_console.check_if_entity_exists('xpath', "//form/div[2]/div/button["
                                                              "contains(text(),'Add')]"):
                    self._driver.find_element(By.XPATH, "//form/div[2]/div/button["
                                                       "contains(text(),'Add')]"
                                                       ).click()
                    self._admin_console.wait_for_completion()

            if schedule_options.get('week_exceptions'):
                self._admin_console.select_radio("weekInMonth")

                if schedule_options.get('exception_weeks'):
                    self.__maintenance_tile.drop_down.select_drop_down_values(0,
                                                                              schedule_options['exception_weeks'])
                if schedule_options.get('exception_days'):
                    self.__maintenance_tile.drop_down.select_drop_down_values(1,
                                                                              schedule_options['exception_days'])

                if self._admin_console.check_if_entity_exists('xpath', "//form/div[2]/div/button["
                                                              "contains(text(),'Add')]"):
                    self._driver.find_element(By.XPATH, "//form/div[2]/div/button["
                                                       "contains(text(),'Add')]"
                                                       ).click()
                    self._admin_console.wait_for_completion()

            self._admin_console.submit_form()

    @PageService()
    def access_http_proxy(self):
        """Loads http proxy tile and returns the HttpProxy class object"""
        self.__maintenance_tile.access_tile('HTTP proxy')
        self._admin_console.wait_for_completion()
        return _HttpProxy(self._admin_console)

    @PageService()
    def access_dr_backup(self):
        """ loads DR backup tile from maintenance page """
        self.__maintenance_tile.access_tile('tileMenuSelection_drBackupDaily')
        self._admin_console.wait_for_completion()

    @PageService()
    def access_internet_options(self):
        """ loads Internet Options tile from maintenance page """
        self.__maintenance_tile.access_tile('Internet options')
        self._admin_console.wait_for_completion()

    @PageService()
    def access_download_software(self):
        """ loads Download software tile from maintenance page """
        self.__maintenance_tile.access_tile("tileMenuSelection_downloadOrCopySoftware")
        self._admin_console.wait_for_completion()

    @PageService()
    def access_install_update_schedules(self):
        """ loads Install update schedule tile from maintenance page """
        self.__maintenance_tile.access_tile('Install update schedules')
        self._admin_console.wait_for_completion()

    @PageService()
    def access_web_domains(self):
        """Access Web domains"""
        self.__maintenance_tile.access_tile('Web Domains')
        self._admin_console.wait_for_completion()

    @PageService()
    def set_internet_options(self, internet_option, gateway_client=None):
        """
        Configures internet gateway from maintenence page.

        Args:
            internet_option (Enum) -- InternetOptions defined in adminconsoleconstants
                                        (Ex:InternetOptions.USE_CLIENT)

            gateway_client  (str) -- name of the client , if InternetOptions.USE_CLIENT
            option is selected
        """
        self.__maintenance_tile.access_tile_settings("Internet options")
        self._admin_console.wait_for_completion()
        self._admin_console.select_radio(internet_option.value)
        if acdefines.InternetOptions.USE_CLIENT.value == internet_option.value:
            if isinstance(gateway_client, str):
                self._admin_console.select_value_from_dropdown("gatewayClient", gateway_client)
            else:
                raise Exception("Invalid Input parameter :gateway_client")
        self._admin_console.submit_form()

    @property
    def current_service_pack(self):
        """

        Returns: Current service pack property from donwload tile.

        """
        return self._admin_console.label_getvalue("Current service pack")

    @property
    def internet_gateway(self):
        """

        Returns: Internet gateway property from donwload tile.

        """
        return self._admin_console.label_getvalue("Internet gateway")

    @PageService()
    def _copy_software(self, media_path, auth=False, username=None, password=None, sync_remote_cache=False,
                       clients_to_sync="All", notify_via_mail=False):
        """
        Fills download software page with configured settings.

        Args:
            media_path (str)  -- path to copy media from

            auth (bool) -- set to True if authentication is required. Default is False

            username (str) -- username if authentication is required

            password (str) -- password if authentication is required

            sync_remote_cache   (bool) --   to sync remote cache

            clients_to_sync (list)  -- list of clients to be synced

            notify_via_mail (bool)  --  Notify job status to users via email

        Returns:
            jobid of the copy software job

        Raises:
            Exception if inputs are invalid

        """
        copy_software_wizard = Wizard(adminconsole=self._admin_console, title='Download or copy software')
        copy_software_wizard.select_radio_button(id='downloadUsingCopy')
        copy_software_wizard.fill_text_in_field("updateCachePath", media_path)
        if auth:
            if not username and not password:
                raise Exception("Auth is True but no credentials provided")
            copy_software_wizard.enable_toggle('impersonateUser')
            copy_software_wizard.fill_text_in_field("username", username)
            copy_software_wizard.fill_text_in_field("password", password)
            copy_software_wizard.fill_text_in_field("confirmPassword", password)
        copy_software_wizard.click_next()

        if notify_via_mail:
            copy_software_wizard.checkbox.check(id='notifyUser')
        else:
            copy_software_wizard.checkbox.uncheck(id='notifyUser')

        if sync_remote_cache:
            copy_software_wizard.checkbox.check(id='selectAllCheckbox')
            tree_view = TreeView(self._admin_console)
            if clients_to_sync == 'All':
                tree_view.select_all()
            else:
                tree_view.select_items([clients_to_sync])
        else:
            copy_software_wizard.checkbox.uncheck(id='selectAllCheckbox')

        copy_software_wizard.click_button('Run')

        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def _download_software(self, download_option=None, sp_version=None, os_to_download=None,
                           sync_remote_cache=False, clients_to_sync="All", notify_via_mail=False):
        """
        Fills download software page with configured settings.

        Args:
            download_option (str) -- download option to be chosen

            sp_version  (str)     -- sp version to download (EX: 'SP12')

            os_to_download  (list) --  List of os to be downloaded

            sync_remote_cache   (bool) --   to sync remote cache

            clients_to_sync (list)  -- list of clients to be synced

            notify_via_mail (bool)  --  Notify job status to users via email

        Returns:
            jobid of the download software job

        Raises:
            Exception

                if inputs are invalid

        """
        download_software_wizard = Wizard(adminconsole=self._admin_console, title='Download or copy software')
        download_software_wizard.select_radio_button(id='downloadUsingInternet')
        if download_option:
            # To select the download option
            download_software_wizard.select_radio_button(id=download_option)
        if acdefines.DownloadOptions.GIVEN_SP_AND_HF.value == download_option:
            download_software_wizard.enable_toggle(toggle_id='includeEarlyRelease')
            if isinstance(sp_version, str):
                download_software_wizard.select_drop_down_values(id='selectedHotfixPack', values=[sp_version.upper()])
            else:
                raise Exception("Invalid Input parameter :sp_version")

        if os_to_download:
            win_os = []
            unix_os = []

            for os in os_to_download:
                if 'Windows' in os:
                    win_os.append(os)
                else:
                    unix_os.append(os)

            if win_os:
                download_software_wizard.checkbox.check(id='isWindows')
                download_software_wizard.select_drop_down_values(id='selectedWindowsPackages', values=win_os)
            else:
                download_software_wizard.checkbox.uncheck(id='isWindows')

            if unix_os:
                download_software_wizard.checkbox.check(id='isUnix')
                download_software_wizard.select_drop_down_values(id='selectedUnixPackages', values=unix_os)
            else:
                download_software_wizard.checkbox.uncheck(id='isUnix')

            download_software_wizard.click_next()

            if notify_via_mail:
                download_software_wizard.checkbox.check(id='notifyUser')
            else:
                download_software_wizard.checkbox.uncheck(id='notifyUser')

            if sync_remote_cache:
                download_software_wizard.checkbox.check(id='selectAllCheckbox')
                tree_view = TreeView(self._admin_console)
                if clients_to_sync == 'All':
                    tree_view.select_all()
                else:
                    tree_view.select_items([clients_to_sync])
            else:
                download_software_wizard.checkbox.uncheck(id='selectAllCheckbox')

        download_software_wizard.click_button('Run')

        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def run_copy_software(self, media_path, auth=False, username=None, password=None,
                          sync_remote_cache=False, clients_to_sync="All"):
        """
        Runs copy software job with configured settings
        Args:
            media_path (str)  -- path to copy media from
            auth (bool) -- set to True if authentication is required. Default is False
            username (str) -- username if authentication is required
            password (str) -- password if authentication is required
            sync_remote_cache   (bool) --   to sync remote cache
            clients_to_sync (list)  -- list of clients to be synced
        Returns:
            str -- jobid of the copy software job
        Raises:
            Exception if job fails, fails to start or inputs are invalid
        """
        self.access_download_software()
        page_container = PageContainer(self._admin_console)
        page_container.click_button(value='Download')
        job_id = self._copy_software(media_path=media_path, auth=auth, username=username, password=password,
                                     sync_remote_cache=sync_remote_cache, clients_to_sync=clients_to_sync)
        return job_id

    @PageService()
    def add_install_schedule(self, schedule_name, schedule_options, clients=None, client_groups=None):
        """
        Creates a new install schedule for the given client/client groups

        Args:
            schedule_name   (str)   -- name of the schedule to be created.

            schedule_options(dict) -- schedule options to create a schedule

            clients         (list) -- list of clients

            client_groups   (list) -- list of client group names.

        """
        self.access_install_update_schedules()
        self._driver.find_element(By.ID, 'internetProxy_button_#6092').click()
        self._admin_console.fill_form_by_id("name", schedule_name)

        if (clients is None) and (client_groups is None):
            raise Exception("Both client and client group is not provided")
        self._driver.find_element(By.XPATH, '//a[@class="accordion-toggle"]').click()
        if clients:
            self._cv_advanced_tree.select_elements(self._admin_console.props['label.nav.activeServers'], clients)
        if client_groups:
            self._cv_advanced_tree.select_elements(self._admin_console.props['label.nav.serverGroups'], client_groups)

        frequency = schedule_options.get('frequency')
        if not frequency:
            raise Exception('Missing argument: Frequency for schedule')

        self.add_schedule(schedule_options=schedule_options)
        self._admin_console.submit_form()

    @PageService()
    def run_install_updates(self, clients=None, client_groups=None):
        """
        run install updates job for the given client/client groups

        Args:
            clients         (list) -- list of clients

            client_groups   (list) -- list of client group names.

        """
        self._admin_console.refresh_page()
        self.access_install_update_schedules()
        self._driver.find_element(By.ID, 'internetProxy_button_#0958').click()

        if (clients is None) and (client_groups is None):
            raise Exception("Both client and client group is not provided")
        self._driver.find_element(By.XPATH, f"//input[@id='searchTree']").click()
        if clients:
            self._cv_advanced_tree.select_elements(self._admin_console.props['label.nav.activeServers'], clients)
        if client_groups:
            self._cv_advanced_tree.select_elements(self._admin_console.props['label.nav.serverGroups'],
                                                   client_groups)
        self._admin_console.submit_form()
        return self._admin_console.get_jobid_from_popup()

    @PageService()
    def run_download_software(self, download_option=None, sp_version=None, os_to_download=None,
                              sync_remote_cache=False, clients_to_sync="All"):
        """
        Runs download software job with configured settings.

        Args:
            download_option (str) -- download option to be chosen

            sp_version  (str)   -- sp version to download
                                    (Example: 'SP12')

            os_to_download  (list) --  List of os to be downloaded

            sync_remote_cache   (bool) --   to sync remote cache

            clients_to_sync (list)  -- list of clients to be synced


        Returns:
            (str)       --  Job id of the download job triggered

        Raises:
            Exception

                if inputs are invalid

                if job fails

                if job failed to start

        Usage:

            * Enum DownloadOptions defined in adminconsoleconstants can be used for providing
              input to download_option

                >>> DownloadOptions.LATEST_HF_FOR_INSTALLED_SP.value

            * Enum DownloadOSID defined in adminconsoleconstants can be used for providing input
              to os_to_download

                >>> [DownloadOSID.WINDOWS_32.value, acd.DownloadOSID.UNIX_AIX32.value]

            * If no arguments are given, by default Latest hotfixes for the installed service pack
              is chosen as the
              download_option and WindowsX64 is chosen as the os_to_download

        """
        self.access_download_software()
        page_container = PageContainer(self._admin_console)
        page_container.click_button(value='Download')
        job_id = self._download_software(download_option=download_option, sp_version=sp_version,
                                         os_to_download=os_to_download, sync_remote_cache=sync_remote_cache,
                                         clients_to_sync=clients_to_sync)
        return job_id

    @PageService()
    def add_schedule(
            self,
            schedule_name=None,
            schedule_options=None
    ):
        """
        To add or edit a schedule using the given options

        Args:
            schedule_name    (str)   -- name of the schedule to be created

            schedule_options (dict)  -- schedule options to create or edit a schedule
        """
        if schedule_name:
            self._admin_console.fill_form_by_id("name", schedule_name)
        frequency = schedule_options.get('frequency')
        if not frequency:
            raise Exception('Missing argument: Frequeny for schedule')
        else:
            frequency = frequency.lower()
        try:
            getattr(self, '_add_' + frequency + '_schedule')(schedule_options)

        except Exception as exp:
            raise Exception(str(exp))

        if frequency in ['Daily', 'Weekly', 'Monthly']:
            # To fill the Time for schedule
            if schedule_options.get('hours') and schedule_options.get('mins'):
                self._driver.find_element(By.XPATH, 
                    "//table/tbody/tr[2]/td[1]/input").clear()
                self._driver.find_element(By.XPATH, 
                    "//table/tbody/tr[2]/td[1]/input").send_keys(schedule_options['hours'])
                self._driver.find_element(By.XPATH, 
                    "//table/tbody/tr[2]/td[3]/input").clear()
                self._driver.find_element(By.XPATH, 
                    "//table/tbody/tr[2]/td[3]/input").send_keys(schedule_options['mins'])

                # To change session to AM or PM
                if schedule_options.get('session'):
                    sess = self._driver.find_element(By.XPATH, 
                        "//table/tbody/tr[2]/td[6]/button")
                    if not sess.text == schedule_options['session']:
                        sess.click()

        self._schedule_repeat(schedule_options)
        self._admin_console.submit_form()

    @PageService()
    def edit_download_schedule(
            self,
            download_option=None,
            sp_version=None,
            os_to_download=None,
            schedule_name=None,
            schedule_options=None):
        """
        Edits the download software schedule with configured settings.

        Args:
            download_option (str)   -- download option to be chosen

            sp_version  (str)       -- sp version to download
                                        (Example: 'SP12')

            os_to_download  (list)  --  List of os to be downloaded

            schedule_name   (str)   -- name for the schedule

            schedule_options (dict) -- schedule options to be selected

        Usage:

            * Enum DownloadOptions defined in adminconsoleconstants can be used for providing
              input to download_option

                >>> DownloadOptions.LATEST_HF_FOR_INSTALLED_SP.value

            * Enum DownloadOSID defined in adminconsoleconstants can be used for providing
              input to os_to_download

                >>> [DownloadOSID.WINDOWS_32.value, acd.DownloadOSID.UNIX_AIX32.value]

            * If no arguments are given, by default Latest hotfixes for the installed service
              pack is chosen as the download_option and WindowsX64 is chosen as the os_to_download

        """

        self.access_download_software()
        page_container = PageContainer(self._admin_console)
        page_container.select_tab(tab_id='schedules')
        self._rtable.access_link('System Created Download Software')

        download_software_wizard = Wizard(
            adminconsole=self._admin_console, title='Download or copy schedule  - System Created Download Software')
        download_software_wizard.select_radio_button(id='downloadUsingInternet')
        if download_option:
            # To select the download option
            download_software_wizard.select_radio_button(id=download_option)
        if acdefines.DownloadOptions.GIVEN_SP_AND_HF.value == download_option:
            download_software_wizard.enable_toggle(toggle_id='includeEarlyRelease')
            if isinstance(sp_version, str):
                download_software_wizard.select_drop_down_values(id='selectedHotfixPack', values=[sp_version.upper()])
            else:
                raise Exception("Invalid Input parameter :sp_version")

        if os_to_download:
            win_os = []
            unix_os = []

            for os in os_to_download:
                if 'Windows' in os:
                    win_os.append(os)
                else:
                    unix_os.append(os)

            if win_os:
                download_software_wizard.checkbox.check(id='isWindows')
                download_software_wizard.select_drop_down_values(id='selectedWindowsPackages', values=win_os)
            else:
                download_software_wizard.checkbox.uncheck(id='isWindows')

            if unix_os:
                download_software_wizard.checkbox.check(id='isUnix')
                download_software_wizard.select_drop_down_values(id='selectedUnixPackages', values=unix_os)
            else:
                download_software_wizard.checkbox.uncheck(id='isUnix')

            download_software_wizard.click_next()

        if schedule_options:
            self.add_schedule(schedule_name, schedule_options)
        self._admin_console.submit_form()


class DRBackupDaily:
    """
    This class provides the function or operations that can be performed on the
    maintenance page on the AdminConsole
    """

    def __init__(self, admin_console):
        """
        Method to initiate DR Backup Daily class
        Args:
            admin_console: instance of AdminConsoleBase
        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self._admin_console.load_properties(self)
        self._jobs = Jobs(admin_console)
        self._toggle = Toggle(admin_console)
        self._dropdown = RDropDown(admin_console)
        self.__dialog = RModalDialog(self._admin_console)
        self._log = logger.get_log()
        self.__maintenance = Maintenance(self._admin_console)
        self._admin_console.navigator.navigate_to_maintenance()
        self.__maintenance.access_dr_backup()

    @WebAction()
    def __set_time(self, element_id, input_time):
        """
        This function is used to set the time in the input field

        Args:
            element_id (str): The id of the parent of input field
            input_time (str): The time to be set in the input field in the format 'hh:mm aa' ["12:00 PM"]
        """
        xpath = f"//*[contains(@id,'{element_id}')]//*[contains(@placeholder,'hh:mm aa')]"
        self.__dialog.fill_input_by_xpath(text=input_time, element_xpath=xpath)

    @PageService()
    def access_dr_backup(self):
        """ navigate to DR backup page from maintenance page """
        self.__maintenance.access_dr_backup()

    @PageService()
    def access_dr_backup_destinations(self):
        """Opens DR backup destinations page."""
        self._log.info('Navigating to Backup Destinations page..')
        if '/drbackup' not in self._admin_console.driver.current_url:
            self._admin_console.navigator.navigate_to_maintenance()
            self.access_dr_backup()
        self._admin_console.access_tab(self._admin_console.props['label.plan.storageAndRetention'])

    @PageService()
    def edit(self, export_settings=None, schedule_settings=None):
        """
        This function is used to edit the DR backup settings

        Args:
            export_settings (dict): The settings to be updated in the export settings of DR backup (Daily) dialog.
                                    i.e:
                                        Number of DR backups to retain, Backup Metadata Destination,
                                        Upload Metadata to Commvault Cloud or Cloud Library
            schedule_settings (dict): The settings to be updated in the schedule settings of DR backup (Daily) dialog.
                                    i.e:
                                        Daily Start Time, Repeat Schedule

        Example:
            export_settings = {
                "retain":2,
                "network_share": {
                    "path": "\\\\path\\to\\share",
                    "username": "user",
                    "password": "password"
                },
                "local_drive": "C:\\path\\to\\drive",
                "metallic": {
                    "turn_on": True
                },
                "cloud_library": {
                    "turn_on": True,
                    "cloud_library_name": "cloud_library_name"
                }
            }

            schedule_settings = {
                "daily_start_time": "12:00 PM",
                "repeat_schedule": {
                    "enable": True,
                    "repeat_every": "08:00",
                    "until": "11:59 PM"
                }
            }

            Raises:
                CVWebAutomationException : if invalid time format is provided

        """
        self._admin_console.click_button(self._admin_console.props['action.edit'])

        if export_settings:
            if export_settings.get('retain', None):
                self.__dialog.fill_text_in_field('numberofMetadata',
                                                 export_settings['retain'])

            if export_settings.get('network_share', None):
                self.__dialog.select_radio_by_value('network')
                self.__dialog.fill_text_in_field('backupMetadataNetworkPath',
                                                 export_settings["network_share"]['path'])
                self.__dialog.fill_text_in_field('userName',
                                                 export_settings["network_share"]['username'])
                self.__dialog.fill_text_in_field('password',
                                                 export_settings["network_share"]['password'])
                self.__dialog.fill_text_in_field('confirmPassword',
                                                 export_settings["network_share"]['password'])

            if export_settings.get('local_drive', None):
                self.__dialog.select_radio_by_value('local')
                self.__dialog.fill_text_in_field('backupMetadataLocalPath',
                                                 export_settings['local_drive'])

            if export_settings.get('metallic', None):
                if export_settings['metallic']['turn_on']:
                    self._toggle.enable(id="uploadMetadataToCloud")
                else:
                    self._toggle.disable(id="uploadMetadataToCloud")

            if export_settings.get('cloud_library'):
                if export_settings['cloud_library']['turn_on']:
                    self._toggle.enable(id="uploadMetadataToCloudLibrary")
                    cloud_library_name = export_settings['cloud_library']['cloud_library_name']
                    self._dropdown.select_drop_down_values(values=[cloud_library_name], drop_down_id="cloudLibrary")
                else:
                    self._toggle.disable(id="uploadMetadataToCloudLibrary")

        if schedule_settings:
            if schedule_settings.get('daily_start_time', None):
                start_time = schedule_settings['daily_start_time']
                try:
                    datetime.strptime(start_time, '%I:%M %p')  # Check if the time is in correct format
                    self.__set_time("dailyStartTime", start_time)
                except Exception as exp:
                    raise CVWebAutomationException(f"Invalid time format: {exp}")

            if schedule_settings.get('repeat_schedule', None):
                if schedule_settings['repeat_schedule']['enable']:
                    self._toggle.enable(id="repeatSchedule")
                    if schedule_settings.get('repeat_schedule', {}).get('repeat_every', None):
                        repeat_every = schedule_settings['repeat_schedule']['repeat_every']
                        try:
                            datetime.strptime(repeat_every, '%H:%M')  # Check if the time is in correct format
                            self.__dialog.fill_text_in_field("repeatEveryHour", repeat_every[:2])
                            self.__dialog.fill_text_in_field("repeatEveryHourMinute", repeat_every[3:])
                        except Exception as exp:
                            raise CVWebAutomationException(f"Invalid time format: {exp}")

                    if schedule_settings.get('repeat_schedule', {}).get('until', None):
                        until = schedule_settings['repeat_schedule']['until']
                        try:
                            datetime.strptime(until, '%I:%M %p')  # Check if the time is in correct format
                            self.__set_time("repeatEveryUntil", until)
                        except Exception as exp:
                            raise CVWebAutomationException(f"Invalid time format: {exp}")

                else:
                    self._toggle.disable(id="repeatSchedule")

        self._admin_console.click_button(self._admin_console.props['label.save'])
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()
