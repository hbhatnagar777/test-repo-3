from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on File servers page.

FileServersMain : This class provides methods for file servers related operations

 __init__()                             --  Initialize object of TestCase class associated

 set_server_details()                   --  To setup the server details which were used to perform the actions

 navigate_to_file_servers_page()        --  To navigate to file servers page of the admin console

 navigate_to_backup_sets_page()         --  To navigate to backup sets page of the admin console

 navigate_to_subclients_page()          --  To navigate to subclients page of the admin console

 file_server_action_check_readiness()   --  To run check readiness operation on the given client

 file_server_action_backup_subclient()  --  To start a backup operation for a subclient

 file_server_action_restore()           --  To restore the given client data

 add_backup_set()                       --  To invoke add backup set operation in backup sets page

 backup_set_action_add_subclient()      --  To invoke add subclient operation in backup sets page

 backup_set_action_backup_subclient()   --  To invoke backup operation from the backup sets page

 backup_set_action_restore()            --  To invoke restore operation in backup sets page

 backup_set_action_delete_subclient()   --  To delete the given subclient

 backup_set_action_delete_backup_set()  --  To invoke delete action in backup sets page

 add_subclient()                        --  To invoke add subclient operation in subclients page

 subclient_action_backup_subclient()    --  To invoke backup operation from subclients page

 subclient_action_restore()             --  To invoke restore operation from subclients page

 subclient_action_delete_subclient()    --  To invoke delete operation from subclients page

 open_backup_sets_page()                --  To open backup sets page

 open_subclients_page()                 --  To open the subclients page

"""

from AutomationUtils.windows_machine import WindowsMachine
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.view_logs import ViewLogs, ViewLogsPanel
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.FSPages.fs_agent import FSSubClient
from Web.AdminConsole.FSPages.fs_backupset import FsBackupset
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)


class FileServersMain:
    """Admin console helper for file server operations"""

    def __init__(self, admin_console, commcell, csdb=None):
        """
        Helper for file server related files

        Args:
            admin_console    (object)    -- admin_console object of TestCase class
            commcell        (object)    --  commcell object of TestCase

        """

        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.commcell = commcell
        self._csdb = csdb

        self._client_name = None
        self._backupset_name = None
        self._subclient_name = None
        self._subclient_content = None

        self._client_hostname = None
        self._client_username = None
        self._client_password = None
        self._client_os_type = "Windows"
        self._client_reboot_required = False
        self._client_plan_assoc = None

        self.file_servers = FileServers(self.__admin_console)
        # self.backup_sets = BackupSets(self.__driver)
        # self.subclients = Subclients(self.__driver)
        self.fs_backup_set = FsBackupset(self.__admin_console)

        self.__jobs = Jobs(self.__admin_console)
        self.__table = Rtable(self.__admin_console)
        self.view_logs = ViewLogs(self.__admin_console)
        self.view_logs_panel = ViewLogsPanel(self.__admin_console)
        if self.commcell and (clients := list(self.commcell.clients.all_clients.keys())):
            self.clients_obj = self.commcell.clients.get(clients[0])

    @property
    def client_name(self):
        """ Returns the client name """
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        """ Sets the client name """
        self._client_name = value

    @property
    def backupset_name(self):
        """ Returns the backupset name """
        return self._backupset_name

    @backupset_name.setter
    def backupset_name(self, value):
        """ Sets the backupset name """
        self._backupset_name = value

    @property
    def subclient_name(self):
        """ Returns the subclient_name """
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """ Sets the subclient_name """
        self._subclient_name = value

    @property
    def subclient_content(self):
        """ Returns the subclient_name """
        return self._subclient_content

    @subclient_content.setter
    def subclient_content(self, value):
        """ Sets the subclient_name """
        self._subclient_content = value

    @property
    def client_hostname(self):
        """Returns client hostname"""
        return self._client_hostname

    @client_hostname.setter
    def client_hostname(self, value):
        self._client_hostname = value

    @property
    def client_username(self):
        """Returns client username"""
        return self._client_username

    @client_username.setter
    def client_username(self, value):
        """Sets the client username"""
        self._client_username = value

    @property
    def client_password(self):
        """Returns client password"""
        return self._client_password

    @client_password.setter
    def client_password(self, value):
        """Sets the client password"""
        self._client_password = value

    @property
    def client_os_type(self):
        """Returns the client os type"""
        return self._client_os_type

    @client_os_type.setter
    def client_os_type(self, value):
        """Sets the client os type"""
        self._client_os_type = value

    @property
    def client_reboot_required(self):
        """Returns boolean state for the client reboot toggle"""
        return self._client_reboot_required

    @client_reboot_required.setter
    def client_reboot_required(self, value):
        """Sets the value for client reboot toggle"""
        self._client_reboot_required = value

    @property
    def client_plan(self):
        """Returns the plan to be associated with the client"""
        return self._client_plan_assoc

    @client_plan.setter
    def client_plan(self, value):
        """Sets the plan to be associated with the client"""
        self._client_plan_assoc = value

    def wait_for_job_completion(self, jobid):
        """Waits for Backup or Restore Job to complete"""
        job_obj = self.commcell.job_controller.get(jobid)
        return job_obj.wait_for_completion()

    def set_server_details(
            self,
            client_name=None,
            backupset_name=None,
            subclient_name=None):
        """ To set server details"""
        self.client_name = client_name
        self.backupset_name = backupset_name
        self.subclient_name = subclient_name

    def navigate_to_file_servers_page(self):
        """ To navigate to file servers page of the admin console """
        self.__navigator.navigate_to_file_servers()

    def file_server_check_readiness(self):
        """To run check readiness operation on the given client in file servers page"""
        self.navigate_to_file_servers_page()
        self.file_servers.run_check_readiness(self.client_name)

    def create_subclient_content(self, file_name, file_size):
        """Method to add data to subclient content directory"""

        client = WindowsMachine(machine_name=self.client_hostname,
                                commcell_object=self.commcell,
                                username=self.client_username,
                                password=self.client_password)
        client.create_file(file_path=f"{self.subclient_content}\\{file_name}",
                           content="abcdefghijkl",
                           file_size=file_size)

    def file_server_backup_subclient(self, backup_level="Full"):
        """
        Method to invoke backup operation in file servers page

        Args:
            backup_level   (str)   -- type of backup

        Returns :
             None

        Raises:
            Exception :

             -- if fails to run the backup

        """

        self.navigate_to_file_servers_page()
        backup_job_id = self.file_servers.backup_subclient(
            client_name=self.client_name,
            backup_level=backup_level,
            backupset_name=self.backupset_name,
            subclient_name=self.subclient_name)

        self._backup_job_details = self.__jobs.job_completion(
            job_id=backup_job_id)

        if self._backup_job_details['Status'] == 'Completed':
            self.log.info("Client backup job ran successfully")

        else:
            raise Exception("Client backup job did not complete successfully")

    def validate_file_server_details(self, flag):
        """Method to validate file server details
        Args:
            flag    (int): Set to 0 to validate file server details post install,
                           set to 1 to validate post backup
        """

        self.navigate_to_file_servers_page()
        client_details = self.__return_file_server_details()
        expected_details = dict()

        app_size_query = "select sum(cast (attrval as bigint))/(1024.0 * 1024.0) from " \
                         "APP_BackupSetProp where attrName = 'Application Size' and " \
                         "componentNameId in (select backupSet from APP_Application where " \
                         "clientId = (select id from app_client where " \
                         f"displayName = '{self.client_hostname}'))"

        if flag == 0:
            expected_details['Name'] = self.client_hostname
            expected_details['Last backup time'] = "Never backed up"
            expected_details['Application size'] = "0 B"
            if self.client_plan:
                expected_details['Plan'] = self.client_plan
                expected_details['Status'] = "To be protected"
            else:
                expected_details['Plan'] = "Not assigned"
                expected_details['Status'] = "Excluded"

        elif flag == 1:
            self._csdb.execute(app_size_query)
            app_size_query_res = self._csdb.fetch_one_row()[0]
            self.__admin_console.log.info(
                f"app size query result {app_size_query_res}")
            converted_job_start_time = self.__convert_date_job_format_to_fs_page_format(
                self._backup_job_details['Start time'])
            expected_details['Last backup time'] = converted_job_start_time
            expected_details['Application size'] = f"{round(float(app_size_query_res), 2)} MB"
            expected_details['Status'] = "Met"

        else:
            raise Exception("Provided flag value is invalid")

        for key, value in expected_details.items():

            if value != client_details[key][0]:
                raise Exception(f"Expected value for {key} is {value}, "
                                f"displayed value is {client_details[key][0]}")
            else:
                self.log.info(
                    f"Expected value for {key} matches displayed value")

    def __convert_date_job_format_to_fs_page_format(self, job_date_str):
        """Method to convert date from job details format to the format as shown on FS page"""

        split1 = job_date_str.split(",")
        datestr = split1[0]
        timesplit = split1[1][6:].split(":")
        final_timestr = f"{timesplit[0]}:{timesplit[1]} {timesplit[2][-2:]}"

        return datestr + ", " + final_timestr

    def __return_file_server_details(self):
        """Verify last backup time, application size, associated plan and status
           of the file server"""

        self.navigate_to_file_servers_page()
        self.__table.apply_filter_over_column("Name", self.client_name)
        self.__admin_console.wait_for_completion()
        fs_details = self.__table.get_table_data()
        return fs_details

    def restore_file_server(self, restore_file=None):
        """
        To invoke restore operation in file servers page

        Args:
            restore_file (str)      --  Data to be restored

        Returns:
            None

        Raises:
            Exception:

                -- if fails to run the restore operation

        """
        self.navigate_to_file_servers_page()
        if self.backupset_name:
            restore_job_id = self.file_servers.restore_subclient(
                client_name=self.client_name,
                backupset_name=self.backupset_name,
                subclient_name=self.subclient_name)
            self.__admin_console.wait_for_completion()
        else:
            restore_job_id = self.file_servers.restore_subclient(
                client_name=self.client_name,
                subclient_name=self.subclient_name)
            self.__admin_console.wait_for_completion()

        job_details = self.wait_for_job_completion(restore_job_id)
        if job_details:
            self.log.info("Subclient was restored successfully")
        else:
            raise Exception("Restore did not complete successfully")

    '''
    ----------------------- Outdated Code --------------------------
    
    def navigate_to_backup_sets_page(self):
        """To navigate to file server backup sets page in admin console"""
        self.__navigator.navigate_to_file_servers()
        self.open_backup_sets_page()

    def navigate_to_subclients_page(self):
        """To navigate to file server subclients page in admin console"""
        self.__navigator.navigate_to_file_servers()
        self.open_subclients_page()

    def add_backup_set(
            self,
            backup_set_content=None,
            storage_policy=None,
            schedule_policies=None):
        """
        To invoke add backup set operation from backup sets page

        Args:
            backup_set_content (str)      --   backup set content

            storage_policy(str)           -- storage policy for the default subclient

            schedule_policies(list)       -- List of schedule policies to be associated

        Returns:
            None

        Raises:
            Exception:

                -- if fails to run the add backup set operation

        """

        self.__navigator.navigate_to_file_servers()
        self.__table.access_link(self.client_name)
        self.backup_sets.add_backup_set(backupset_name=self.backupset_name,
                                        backup_set_content=backup_set_content,
                                        storage_policy=storage_policy,
                                        schedule_policies=schedule_policies)

    def backup_set_action_add_subclient(
            self, subclient_content=None, plan_name=None):
        """
           To invoke add subclient operation in backup sets page

               Return:

                   subclient_content (str)  : Subclient content

                   plan_name (str)         : Name of the plan

               Raises:
                   Exception:
                    ---if failed to add the subclient

        """
        self.navigate_to_backup_sets_page()
        self.backup_sets.add_subclient(
            self.subclient_name,
            subclient_content,
            plan_name,
            self.backupset_name)

    def backup_set_action_backup_subclient(self):
        """
        To invoke backup operation from the backup sets page

        Return:

            job id  (int) : Job id of the backup job

        Raises:
            Exception:
             ---if failed to run the backup operation

        """
        self.navigate_to_backup_sets_page()
        self.backup_sets.select_backup_set(
            self.client_name, self.backupset_name)

        job_id = self.fs_backup_set.perform_fs_subclient_backup(
            self.subclient_name)
        job = self.commcell.job_controller.get(job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: " + job.delay_reason
            )
        self.log.info("Backup job was completed successfully")

    def backup_set_action_restore(self, restore_file=None):
        """

        To invoke restore operation in backup sets page

        Args:

            restore_file (str)  : file to be restored

        Return:
                job id  (int) : Job id of the restore job

        Raises:
                Exception:
                    --- if failed to run the restore operation

        """
        self.navigate_to_backup_sets_page()

        restore_job_id = self.backup_sets.restore_client(
            self.backupset_name, restore_file)
        restore_job = self.commcell.job_controller.get(restore_job_id)

        if not restore_job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: " +
                restore_job.delay_reason)
        self.log.info(" Restore job was completed successfully")

    def backup_set_action_delete_subclient(self):
        """
        To delete the given subclient

        Return:
                None
        Raises:
                Exception:
                    --- if failed to run the delete operation

        """
        self.navigate_to_backup_sets_page()
        self.log.info("Deleting the subclient")
        self.backup_sets.select_backup_set(
            self.client_name, self.backupset_name)
        self.fs_backup_set.delete_fs_subclient(self.subclient_name)
        self.log.info("subclient was deleted successfully")

    def backup_set_action_delete_backup_set(self):
        """
        To invoke delete backup set operation in backup sets page

        Returns:
            None
        Raises:
            Exception:

            ---if failed to delete the backup set

        """
        self.navigate_to_backup_sets_page()
        self.log.info("Deleting the backup set")
        self.backup_sets.delete_backup_set(self.backupset_name)
        self.log.info("Backup set was deleted successfully")

    def add_subclient(
            self,
            subclient_name,
            plan_name=None,
            subclient_content=None,
            storage_policy=None,
            schedule_policies=None):
        """
        To invoke add subclient operation in subclients page

        Args:

            subclient_name (str)    : Name of the subclient

            subclient_content (str) : Data to be backed up

            plan_name (str)         : Name of the plan

            storage_policy (str)    : Name of the storage policy

            schedule_policies (list): List of schedule policies to be associated

        Returns:
            None

        Raises:
            Exception:
                -- if failed to add subclient

        """
        self.navigate_to_subclients_page()
        self.log.info("Creating subclient in the given backup set")
        self.subclients.add_subclient(
            subclient_name,
            subclient_content,
            plan_name,
            self.backupset_name,
            storage_policy,
            schedule_policies)
        self.log.info("Subclient was created successfully.")

    def subclient_action_backup_subclient(self, backup_level=None):
        """
        To invoke backup operation in subclients page

        Args:
            backup_level   (str)   -- type of backup

        Returns :
             job id (int) : backup job id

        Raises:
            Exception :

             -- if fails to run the backup

        """
        self.navigate_to_subclients_page()
        job_id = self.subclients.backup_subclient(
            self.client_name, self.subclient_name, backup_level)
        return self.commcell.job_controller.get(job_id)

    def subclient_action_restore(self, restore_file=None):
        """

        To invoke restore operation in subclients page

        Args:

            restore_file (str)  : file to be restored

        Return:
                job id  (int) : Job id of the restore job

        Raises:
                Exception:
                    --- if failed to run the restore operation

        """
        self.navigate_to_subclients_page()
        self.log.info("Invoking restore job operation from subclients page")

        restore_job_id = self.subclients.restore_client(
            self.client_name, self.subclient_name, restore_file)
        return self.commcell.job_controller.get(restore_job_id)

    def subclient_action_delete_subclient(self):
        """
        To delete the given subclient in subclients page

        Returns:
                None
        Raises:
                Exception:
                    --- if failed to run the delete operation

        """
        self.navigate_to_subclients_page()
        self.log.info("Deleting the subclient")
        self.subclients.delete_subclient(self.client_name, self.subclient_name)
        self.log.info("subclient was deleted successfully")

    def open_backup_sets_page(self):
        """ To open backup sets page"""
        self.__driver.find_element(By.XPATH, 
            '//span[text()="Backup sets"]').click()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def open_subclients_page(self):
        """ To open subclients listing page"""
        self.__driver.find_element(By.XPATH, 
            '//span[text()="Subclients"]').click()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
    '''

    def view_live_logs(self, client_name, log_name):
        """View live logs for the give server"""
        self.__navigator.navigate_to_file_servers()
        self.file_servers.view_live_logs(client_name)
        self.view_logs_panel.access_log(log_name)
        self.view_logs.change_to_log_window()

    def install_new_fs_client(self):
        """Method to install a new client"""
        self.navigate_to_file_servers_page()
        job_id = self.file_servers.install_windows_unix_client(self.client_hostname,
                                                               self.client_username,
                                                               self.client_password,
                                                               self.client_os_type,
                                                               self.client_reboot_required,
                                                               self.client_plan)
        job_details = self.wait_for_job_completion(job_id)
        if job_details:
            self.log.info("Client installation completed successfully")
        else:
            raise Exception(
                "Client installation did not complete successfully")

    def validate_type_filter(self):
        """Method to verify correct results are shown when using fs page filter type"""
        self.navigate_to_file_servers_page()

        fs_dict = self.get_file_server_page_list()
        self.log.info(str(fs_dict))
        self.__table.set_pagination('min')
        if fs_dict['Windows']:
            self.file_servers.filter_file_server_by_type("Windows")
            windows_fs_list = self.__table.get_column_data("Name")
            for server in windows_fs_list:
                if server not in fs_dict["Windows"]:
                    raise Exception(
                        f"{server} is displayed under windows, it should not")
            self.log.info("Windows type servers verified")

        if fs_dict['Unix']:
            self.file_servers.filter_file_server_by_type("Unix")
            unix_fs_list = self.__table.get_column_data("Name")
            for server in unix_fs_list:
                if server not in fs_dict["Unix"]:
                    raise Exception(
                        f"{server} is displayed under unix, it should not")
            self.log.info("Unix type servers verified")

        if fs_dict['NAS']:
            self.file_servers.filter_file_server_by_type("NAS")
            nas_fs_list = self.__table.get_column_data("Name")
            for server in nas_fs_list:
                if server not in fs_dict["NAS"]:
                    raise Exception(
                        f"{server} is displayed under NAS, it should not")
            self.log.info("NAS type servers verified")

    def get_file_server_page_list(self):
        """Method to get file servers list via API call"""

        windows_list = self.clients_obj.filter_clients_return_displaynames(
            filter_by="OS",
            os_type="Windows",
            url_params={"Hiddenclients": "true",
                        "includeIdaSummary": "true",
                        "propertylevel": "10"})

        unix_list = self.clients_obj.filter_clients_return_displaynames(
            filter_by="OS",
            os_type="Linux",
            url_params={"Hiddenclients": "true",
                        "includeIdaSummary": "true",
                        "propertylevel": "10"})

        nas_list = self.clients_obj.filter_clients_return_displaynames(
            filter_by="OS",
            os_type="NDMP",
            url_params={"Hiddenclients": "true",
                        "includeIdaSummary": "true",
                        "propertylevel": "10"})

        return {"Windows": windows_list, "Unix": unix_list, "NAS": nas_list}

    def validate_pagination(self):
        """Method to verify if pagination works as intended"""

        self.navigate_to_file_servers_page()
        options = self.__table.get_pagination_options()
        total_rows = None
        for option in options:

            self.__table.set_pagination(option)
            self.__admin_console.wait_for_completion()
            rows_displayed = len(self.__table.get_column_data("Name"))

            if int(option) == rows_displayed:
                self.log.info(
                    f"Pagination option {option} shows {rows_displayed} rows")
            else:
                if int(option) > rows_displayed:
                    if total_rows is None:
                        total_rows = rows_displayed
                    if total_rows != rows_displayed:
                        raise Exception(
                            "Number of rows displayed neither match pagination option nor total file servers")
                    else:
                        self.log.info(
                            f"Pagination {option} shows {rows_displayed} rows which is total servers {total_rows}")
                else:
                    raise Exception(
                        f"Number of rows displayed is more than pagination option {option}")

    def sort_table_and_return_column(self, column_name, order):
        """Method to sort table over column and return list of column values"""

        self.navigate_to_file_servers_page()
        self.__table.apply_sort_over_column(column_name, order)
        return self.__table.get_column_data(column_name)

    def release_license(self):
        """Method to release license of client"""

        self.navigate_to_file_servers_page()
        self.__table.access_link(self.client_hostname)
        self.__admin_console.access_menu("Release license")
        self.__admin_console.click_button("Yes")

    def delete_client(self):
        """Method to delete client from File servers listing page"""

        self.navigate_to_file_servers_page()
        self.__table.access_action_item(self.client_hostname, "Delete")
        self.__admin_console.click_button("Yes")

    def listing_page_search(self, server_name):
        """Validate if a file server is listed"""
        self.__navigator.navigate_to_file_servers()
        if self.file_servers.is_client_exists(server_name):
            self.log.info(
                'listing page search validation completed for the File server')
        else:
            raise CVWebAutomationException(
                'file server not listed in listing page')

    def edit_Client_name(self, old_name, new_name):
        """Method to edit file server name"""
        self.__navigator.navigate_to_file_servers()
        self.file_servers.access_server(old_name)
        self.__admin_console.wait_for_completion()
        self.file_servers.change_server_name(new_name)

    @PageService()
    def associate_plan_to_file_server(self, plan_name: str, file_server_name: str) -> bool:
        """Method to associate plan to file server and validate if association got successfull

        Args:
            plan_name (str) : Plan name

            file_server_name (str)  : File server client name
        """
        try:
            self.file_servers.manage_plan(file_server_name, plan_name)
        except Exception as err:
            self.log.info(f'Plan association via UI Failed : {err}')
            return False
        backupset = self.commcell.clients.get(file_server_name).agents.get(
            'File System').backupsets.get('defaultBackupSet')
        return backupset.plan.plan_name.lower() == plan_name.lower() if backupset.plan else False
