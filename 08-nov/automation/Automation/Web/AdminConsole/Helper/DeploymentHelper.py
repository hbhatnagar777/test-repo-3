# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to deployment in AdminConsole
DeploymentHelper : This class provides methods for deployment related operations

DeploymentHelper
================

    __init__(TestCase obj)          --  Initialize object of TestCase class associated

    convert_package_name_to_id      --  To convert list of package id's into package names

    get_package_names               --  To get the names of the packages given as input

    navigate_to_server_page         --  To navigate to the servers page of the admin console

    navigate_to_fileserver_page     -- To navigate to file servers page

    check_job_status                --  To check the status of the job in admin console jobs page

    action_add_software             --  To invoke add software method in the servers page

    action_update_software          --  To invoke update software method in the servers page

    action_uninstall_software       --  To invoke uninstall software method in the servers page

    retire_server                   --  To invoke retire server method in the servers page

    delete_server                   --  To invoke delete server method in the servers page

    add_server_new_windows_or_unix_server   --  To invoke add server method for new windows or
                                                unix server in the servers page

    run_copy_software               --  Runs copy software job with configured settings

    run_download_software           --  To run download software job with configured settings

"""
from selenium.common.exceptions import NoSuchElementException
from AutomationUtils import constants
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.maintenance import Maintenance
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.FileServerPages.file_servers import FileServers


class DeploymentHelper:
    """Admin console helper for deployment operations"""

    def __init__(self, testcase, admin_console):
        """
        Helper for deployment related files

        Args:
            testcase    (object)    -- object of TestCase class

        """
        self.admin_console = admin_console
        self.driver = admin_console.driver
        self.__navigator = self.admin_console.navigator
        self.log = testcase.log
        self.csdb = testcase.csdb
        self.commcell = testcase.commcell
        self.job = Jobs(self.admin_console)
        self.job_details = JobDetails(self.admin_console)
        self.tcinputs = testcase.tcinputs
        self.status = testcase.status
        self.server = None
        self.maintenance = None
        self._table = Table(self.admin_console)
        self.fileserver = None

    def convert_package_id_to_name(self):
        """ To convert list of package id's into package names

            Returns:
                (list)      -- list of package names

            Raises:
                Exception

                if Invalid package ID is given

                if failed to connect to the DB

        """
        package_names = []
        packages = self.tcinputs.get('Packages')
        packages = packages.split(',')
        try:
            for package in packages:
                package = package.strip()
                query = f"select Name from simPackage where id = {int(package)}"
                self.csdb.execute(query)
                cur = self.csdb.fetch_one_row()
                package_names.append(cur[0][0])
        except Exception:
            self.log.info("Invalid package ID given")
            raise Exception("Invalid package ID given")
        return package_names

    def get_package_names(self):
        """ To get the names of the packages given as input

            Returns:
                (list)      -- list of package names

                None        -- If no input packages

        """
        packages = self.tcinputs.get('Packages')
        package_names = []
        if packages:
            packages = packages.split(',')
            for package in packages:
                package_names.append(package.strip().upper())

        return package_names

    def navigate_to_server_page(self):
        """ To navigate to the servers page of the admin console
        """
        if not self.server:
            self.server = Servers(self.admin_console)

        self.__navigator.navigate_to_servers()
        self.admin_console.wait_for_completion()

    def navigate_to_fileserver_page(self):
        """
        To navigate to file servers page
        """
        if not self.fileserver:
            self.fileserver = FileServers(self.admin_console)
        self.__navigator.navigate_to_file_servers()
        self.admin_console.select_file_servers_tab()
        self.admin_console.wait_for_completion()

    def navigate_to_maintenance_page(self):
        """ To navigate to the servers page of the admin console
        """
        if not self.maintenance:
            self.maintenance = Maintenance(self.admin_console)

        self.__navigator.navigate_to_maintenance()
        self.admin_console.wait_for_completion()

    def check_job_status(self, jobid):
        """ To check the status of the job in admin console jobs page

            Args:
                jobid   (str)   --  job id of the triggered job

            Raises:
                Exception

                    if Job failed

        """
        base_url = self.driver.current_url.split("commandcenter")[0]
        self.driver.get(f'{base_url}commandcenter/#/jobs/{jobid}')
        self.admin_console.wait_for_completion(wait_time=450)

        job_details = self.job_details.job_completion()

        if "Completed" in job_details.get('Status'):
            self.status = constants.PASSED
            self.log.info("Job Completed successfully")
        else:
            raise Exception(job_details.get('Job pending reason'))

    def get_client_name_from_hostname(self, hostname):
        """
        To get the client name from the host name

        Args:
            hostname    (str)   --  Full hostname of the machine

        Returns:
            (str)   --  Client name which matches the hostname

        Raises:
            Exception

            if hostname is invalid
        """
        self.commcell.refresh()
        client = self.commcell.clients.get(hostname)

        return client.client_name

    def action_add_software(
            self,
            client_name=None,
            select_all_packages=False,
            packages=None,
            reboot=True):
        """
        To invoke add software method in the servers page

        Args:
            client_name     (str)           -- client to add software on

            select_all_packages  (bool)     -- selects all the packages if set True
                                                default: False

            packages        (list)          -- list of packages to be installed

            reboot          (bool)          -- set to True if reboot required
                                            default: False

        Returns:
            None

        Raises:
            Exception

                if given input is invalid

                if there is no add software option for the client

                if Job failed

        """
        self.navigate_to_fileserver_page()
        jobid = self.fileserver.action_add_software(
            client_name=client_name,
            select_all_packages=select_all_packages,
            packages=packages,
            reboot=reboot
        )
        self.log.info("Job %s is started for adding software", jobid)
        self.check_job_status(jobid)
        self.log.info("Successfully installed the selected packages on client %s",
                      self.tcinputs.get('DeploymentClientName'))

    def action_update_software(self, client_name=None, reboot=False):
        """
        To invoke update software method in the servers page

        Args:
            client_name     (str) -- client to update software on

            reboot      (bool)    -- set to True if reboot required
                                        default: False

        Returns:
            None

        Raises:
            Exception

                if given input is invalid

                if there is no update software option for the client

                if Job failed

        """
        self.navigate_to_server_page()
        jobid = self.server.action_update_software(
            client_name=client_name,
            reboot=reboot
        )
        self.log.info("Job %s is started for update software", jobid)

        # To Check the Job status
        self.check_job_status(jobid)
        self.log.info("Successfully updated the client %s",
                      self.tcinputs.get('DeploymentClientName'))

    def action_uninstall_software(self, client_name=None, packages=None):
        """
        To invoke uninstall software method in the servers page

        Args:
            client_name     (str)       -- client to uninstall software on

            select_all_packages (bool)   -- selects all the packages if set True
                                                default: False

            packages        (list)      -- list of packages to be uninstalled

        Returns:
            None

        Raises:
            Exception

                if given input is invalid

                if there is no uninstall software option for the client

                if Job failed

        """
        self.navigate_to_server_page()
        jobid = self.server.action_uninstall_software(client_name, select_from_all_server=True)
        self.log.info("Job %s is started for uninstall software", jobid)

        # To Check the Job status
        self.check_job_status(jobid)
        self.log.info("Successfully uninstalled the selected packages on the client %s",
                      self.tcinputs.get('DeploymentClientName'))

    def retire_server(self, server_name):
        """
        To invoke retire server method in the servers page

        Args:
            server_name     (str)       -- server to retire
        """
        self.navigate_to_fileserver_page()
        try:
            jobid = self.fileserver.retire_server(server_name)
        except NoSuchElementException:
            self.log.info("%s server does not have retire action to perform", server_name)
            return
        self.log.info("Job %s is started for retire server", jobid)
        self.check_job_status(jobid)
        self.log.info("Successfully retired the server %s", server_name)
        self.navigate_to_fileserver_page()
        name = self._table.get_column_data('Name')
        if server_name in name:
            self.log.error("Client Still Exists. Retire Operation failed")

    def delete_server(self, server_name):
        """
        To invoke delete server method in the servers page

        Args:
            server_name     (str)       -- server to delete
        """
        self.navigate_to_server_page()
        try:
            self.server.delete_server(server_name)
        except NoSuchElementException:
            self.log.info("%s server does not have delete action to perform", server_name)
            return
        self.log.info("Successfully delete the server %s", server_name)

    def add_server_new_windows_or_unix_server(
            self,
            hostname=None,
            username=None,
            password=None,
            os_type='windows',
            packages=None,
            select_all_packages=False,
            plan=None,
            unix_group=None,
            log_path=None,
            reboot=False,
            install_path=None,
            remote_cache=None):
        """
        To invoke add server method for new windows or unix server in the servers page

         Args:

            hostname   (list)  -- list of servers to install packages on

            username    (str)   -- username of the server machine

            password    (str)   -- password of the server machine

            os_type     (str)   -- os type of the server machine
                                    default: windows

            packages    (list)  -- packages to be installed on the machine

            select_all_packages (bool) -- set to True to install all the packages
                                            default: False

            plan        (str)   -- plan to run install

            unix_group  (str)   -- unix group for UNIX machine

            log_path    (str)   -- path to store the DB2 logs

            reboot      (bool)  -- set to True to reboot if required
                                    default: False

            install_path (str)  -- Installing client on specified path ( Optional )

            remote_cache (str)  -- Client name of remote cache machine ( Optional )

        Returns:
            None

        Raises:
            Exception

                if given inputs are not valid

                if there is no add server option

                if Job failed

        """
        self.navigate_to_server_page()
        jobid = self.server.add_server_new_windows_or_unix_server(
            hostname=hostname,
            username=username,
            password=password,
            os_type=os_type,
            packages=packages,
            select_all_packages=select_all_packages,
            plan=plan,
            unix_group=unix_group,
            reboot=reboot,
            install_path=install_path,
            remote_cache=remote_cache
        )
        self.log.info("Job %s is started for adding new server", jobid)

        self.check_job_status(jobid)
        self.log.info("Successfully created new clients on the machine(s) %s", hostname)

    def run_copy_software(self, media_path, auth=False, username=None, password=None,
                          sync_remote_cache=False, clients_to_sync="All"):
        """
        Runs copy software job with configured settings.
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

        self.navigate_to_maintenance_page()

        jobid = self.maintenance.run_copy_software(
            media_path=media_path,
            auth=auth,
            username=username,
            password=password,
            sync_remote_cache=sync_remote_cache,
            clients_to_sync=clients_to_sync
        )
        self.log.info("Copy Software job %s has started", jobid)

        # To Check the Job status
        self.check_job_status(jobid)
        self.log.info("Successfully completed copying media to cache")

    def run_download_software(self, download_option=None, sp_version=None, os_to_download=None,
                              sync_remote_cache=False, clients_to_sync="All"):
        """
        Runs download software job with configured settings.

        Args:
            download_option (str) -- download option to be chosen

            sp_version  (str)   -- sp version to download
                                    Example: 'SP12'

            os_to_download  (list) --  List of os to be downloaded

            sync_remote_cache   (bool) --   to sync remote cache

            clients_to_sync (list)  -- list of clients to be synced

        Returns:
            (str)       --  Job id of the download job triggered

        Raises:
            Exception

                if inputs are invalid

                if job fails

                ìf job failed to start

        Usage:

            * Enum DownloadOptions defined in adminconsoleconstants can be used for providing
              input to download_option

                >>> DownloadOptions.LATEST_HF_FOR_INSTALLED_SP.value

            * Enum DownloadOSID defined in adminconsoleconstants can be used for providing input
              to os_to_download

                >>> [DownloadOSID.WINDOWS_32.value, acd.DownloadOSID.UNIX_AIX32.value]

            * If no arguments are given, by default Latest hotfixes for the installed service
              pack is chosen as the download_option and WindowsX64 is chosen as the os_to_download

        """
        # To navigate to the maintenance page
        self.navigate_to_maintenance_page()

        jobid = self.maintenance.run_download_software(
            download_option=download_option,
            sp_version=sp_version,
            os_to_download=os_to_download,
            sync_remote_cache=sync_remote_cache,
            clients_to_sync=clients_to_sync
        )
        self.log.info("Job %s is started for Download job", jobid)

        # To Check the Job status
        self.check_job_status(jobid)
        self.log.info("Successfully completed downloading software using %s option",
                      download_option)

    def edit_download_schedule(
            self,
            download_option=None,
            sp_version=None,
            os_to_download=None,
            schedule_name=None,
            schedule_options=None
    ):
        """
        Edits the download software schedule with configured settings.

        Args:
            download_option (str)   -- download option to be chosen

            sp_version  (str)       -- sp version to download
                                        Example: 'SP12'

            os_to_download  (list)  -- list of os to be downloaded

            schedule_name   (str)   -- name for the schedule

            schedule_options (dict) -- schedule options to be selected

        Returns:
            None

        Raises:
            Exception

                if inputs are invalid

        Usage:

            * Enum DownloadOptions defined in adminconsoleconstants can be used for providing
              input to download_option

                >>> DownloadOptions.LATEST_HF_FOR_INSTALLED_SP.value

            * Enum DownloadOSID defined in adminconsoleconstants can be used for providing
              input to os_to_download

                >>> [DownloadOSID.WINDOWS_32.value, acd.DownloadOSID.UNIX_AIX32.value]

            * If no arguments are given, by default Latest hotfixes for the installed service
              pack is chosen as the download_option and WindowsX64 is chosen as the os_to_download

            * Sample dict for one time schedule

                    {
                        'frequency': 'One time',
                        'servers': ['server1','server2'],
                        'backup_level': 'Full',
                        'year': '2017',
                        'month': 'december',
                        'date': '31',
                        'hours': '09',
                        'mins': '19',
                        'session': 'AM'
                    }

            * Sample dict for automatic schedule

                    {
                        'frequency': 'Automatic',
                        'servers': ['server1','server2'],
                        'backup_level': 'Full',
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

            * Sample dict for daily schedule

                    {
                        'frequency': 'Daily',
                        'servers': ['server1','server2'],
                        'backup_level': 'Full',
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

            * Sample dict for weekly schedule

                    {
                        'frequency': 'Weekly',
                        'servers': ['server1','server2'],
                        'backup_level': 'Full',
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

            * Sample dict for monthly schedule

                    {
                        'frequency': 'Monthly',
                        'servers': ['server1','server2'],
                        'backup_level': 'Full',
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
                        'exception_days': ['monday','friday'],
                        'exception_weeks': ['First', 'Last'],
                        'repeat': True,
                        'repeat_hrs': '8',
                        'repeat_mins': '25',
                        'until_hrs': '11',
                        'until_mins': '59',
                        'until_sess': 'PM'
                    }

            * Sample dict for continuous schedule

                    {
                    'frequency': 'Continuous',
                    'servers': ['server1','server2'],
                    'backup_level': 'Full',
                    'continuous_interval': '30'
                    }

        """
        # To navigate to the maintenance page
        self.navigate_to_maintenance_page()

        # To edit the download schedule
        self.maintenance.edit_download_schedule(
            download_option=download_option,
            sp_version=sp_version,
            os_to_download=os_to_download,
            schedule_name=schedule_name,
            schedule_options=schedule_options
        )
