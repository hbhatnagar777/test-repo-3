# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
"""
"63667":{
            "AgentName":"",
            "ClientName":"",
            "BackupsetName":"",
            "PlanName":"",
            "StoragePolicyName":"",
            "RestoreMachine":"",
            "RestorePath":"",
            "RestorePathForCrossMachine":"",
            "ImpersonateUser": "", - only for windows network share
            "ImpersonatePassword": "", - only for windows network share
            "DataAccessNodes": ["client-1", "client-2"], - only for network share
        }
"""

import time, uuid, calendar
import datetime
from datetime import date
from AutomationUtils.config import get_config
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers as RFileServers
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Overview
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import SubclientOverview
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from cvpysdk.constants import AppIDAType
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.AdminConsole.Hub.constants import HubServices, FileObjectTypes
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
from base64 import b64decode


class TestCase(CVTestCase):
    """ Class for executing this test case

    Verify restore from calender for both from subclient and backupset level.

    """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = (
            "Verify restore from calender for both from subclient and backupset level"
        )
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.machine = None
        self.dest_machine = None
        self.fs_sub_client = None
        self.fs_helper = None
        self.os_name = None
        self.delimiter = None
        self.config = get_config()
        self.base_path = None
        self.UNC_base_path = None
        self.temp_mount_path = None
        self.is_cifs_agent = None
        self.dest_path = None
        self.restore_path = ''
        self.impersonate_user = None
        self.impersonate_password = None
        self.jobs = None
        self.appTypeId = None
        self.sub_client_name = None
        self.restore_path = None
        self.cross_machine_restore_path = None
        self.agent_overview = None
        self.content = []
        self.fs_utils = None
        self.isMetallic = False
        self.UNC_content = []
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "PlanName": None,
            "RestoreMachine": None,
            "RestorePath": None,
            "RestorePathForCrossMachine": None
        }

    def wait_for_calendar_to_load(self):
        for _ in range(6):
            self.log.info("Waiting for calendar to load")
            if self.admin_console.is_element_present("//div[@id='teer-calendar']"):
                return
            time.sleep(10)
        raise Exception("Calendar element is not loaded")

    def navigate_to_client_page(self):
        """ Navigates to the input client page """
        self.navigator.navigate_to_file_servers()
        self.admin_console.access_tab("File servers")

        self.rfile_server.access_server(self.client.display_name)

        if self.is_client_network_share:

            if self.is_cifs_agent:
                self.fs_utils.access_protocol("CIFS")
            else:
                self.fs_utils.access_protocol("NFS")

        self.refresh()

        self.wait_for_calendar_to_load()

    def navigate_to_subclients_tab(self):
        """Navigates to the subclients tab"""

        self.admin_console.access_tab("Subclients")

    def refresh(self, wait_time=180):
        """ Refreshes the current page """
        self.log.info("%s Refreshes browser %s", "*" * 8, "*" * 8)
        self.admin_console.refresh_page()

    def wait_for_job_completion(self, job_id):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
        """
        self.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.commcell.job_controller.get(job_id)
        return job_obj.wait_for_completion()

    def delete_content(self):
        """Deletes subclient content"""

        machine = self.machine

        if self.is_client_network_share:
            machine = self.client_machine

        if machine.check_directory_exists(self.content[0]):
            machine.remove_directory(self.content[0])

        self.log.info("Deleted folder %s", self.content[0])

    @test_step
    def define_content_and_path(self):
        """ Define the subclient content, exclusions and exceptions """
        self.os_name = self.client._properties['client']['osInfo']['Type'].lower()
        self.content = []
        self.UNC_content = []
        self.UNC_base_path = ""
        if self.os_name == "windows":
            self.delimiter = "\\"
            path = self.client.job_results_directory + self.delimiter + 'Test63367'
            # setting appTypeId for DB query
            self.appTypeId = AppIDAType.WINDOWS_FILE_SYSTEM.value
        elif self.os_name == "unix":
            self.delimiter = "/"
            path = '/opt/Test63367'
            # setting appTypeId for DB query
            self.appTypeId = AppIDAType.LINUX_FILE_SYSTEM.value
        else:
            # The client is a NAS client
            if "windows" in self.client_machine.os_info.lower():
                self.os_name = "windows"
                self.is_cifs_agent = True
                self.delimiter = self.client_machine.os_sep
                self.temp_mount_path = "Z:"
                self.fs_helper.mount_cifs_share_on_drive(
                    self.client_machine,
                    self.test_path,
                    self.impersonate_user,
                    self.impersonate_password,
                    self.temp_mount_path
                )
            else:
                self.is_cifs_agent = False
                self.os_name = "unix"
                self.delimiter = self.client_machine.os_sep
                self.temp_mount_path = self.client_machine.join_path('/', f"_{self.id}")
                server, share = self.test_path.split(":")

                if self.client_machine.check_directory_exists(self.temp_mount_path):
                    if self.client_machine.is_path_mounted(self.temp_mount_path):
                        self.client_machine.unmount_path(self.temp_mount_path)

                self.client_machine.create_directory(self.temp_mount_path, force_create=True)
                self.client_machine.mount_nfs_share(self.temp_mount_path, server, share)

            self.UNC_base_path = self.client_machine.join_path(
                self.test_path, f"{self.id}"
            )

            self.base_path = self.client_machine.join_path(
                self.temp_mount_path, f"{self.id}"
            )

            path = self.base_path

        hex_val = uuid.uuid4().hex

        path = path + hex_val
        self.fs_helper.generate_testdata(['.html', '.py'], path, 6)
        self.content.append(path)
        self.UNC_content.append(self.UNC_base_path + hex_val)

    @test_step
    def add_subclient(self):
        """ Creates new subclient
                Raises:
                    Exception:
                        -- if fails to add entity
        """
        self.navigate_to_subclients_tab()
        self.delete_sub_client()
        # toggle_own_content should be true only when plan has predefined contents
        if not self.is_client_network_share:
            self.fs_sub_client.add_subclient(
                subclient_name=self.sub_client_name,
                plan_name=self.tcinputs['PlanName'],
                backupset_name=self.tcinputs['BackupsetName'],
                contentpaths=self.content,
                define_own_content=True,
                remove_plan_content=True
            )
        else:
            impersonate_user = None

            if self.is_cifs_agent:
                impersonate_user = {
                    "username": self.impersonate_user,
                    "password": self.impersonate_password
                }

            self.fs_sub_client.add_subclient(subclient_name=self.sub_client_name,
                                             backupset_name=self.tcinputs['BackupsetName'],
                                             plan_name=self.tcinputs['PlanName'],
                                             contentpaths=self.UNC_content,
                                             define_own_content=True,
                                             is_nas_subclient=True,
                                             impersonate_user=impersonate_user)

        self.log.info("%s Subclient created successfully %s", "*" * 8, "*" * 8)
        self.backupset.subclients.refresh()
        self.subclient = self.backupset.subclients.get(self.sub_client_name)

    def backup_job(self, backup_type):
        """ Function to run a backup job
            Args:
                backup_type (BackupType) : Type of backup (FULL, INCR, DIFFERENTIAL, SYN_FULL)
            Raises:
                Exception :
                 -- if fails to run the backup
        """
        self.log.info(
            "%s Starts Backup job %s for subclient %s", backup_type, "*" * 8, "*" * 8
        )
        self.navigate_to_client_page()
        self.navigate_to_subclients_tab()
        job = self.fs_sub_client.backup_subclient(
            subclient_name=self.sub_client_name,
            backupset_name=self.tcinputs['BackupsetName'],
            backup_type=backup_type
        )
        self.wait_for_job_completion(job)
        return job

    def kill_if_any_running_job(self):
        """Kills any active job running for the subclient"""
        self.log.info(
            "Killing any active backup jobs for subclient %s", self.sub_client_name
        )

        # Skips the query to DB if the case is run for metallic
        if not self.isMetallic and (not self.is_client_network_share):
            # Getting running job details from csdb as its faster and efficient
            query = f"select * from APP_Application WITH(NOLOCK) where subclientName = '{self.sub_client_name}' and appTypeId = {self.appTypeId}"
            # CSDB is already initialised in cvtestcase.py
            self.csdb.execute(query)
            query_result = self.csdb.fetch_one_row()
            self.log.info(query_result)
            if len(query_result) > 1:
                # If the following subclient exists
                subclient_id = query_result[0]
                query = f"select * from JMBkpJobInfo WITH(NOLOCK) where applicationId = {subclient_id}"
                self.csdb.execute(query)
                query_result = self.csdb.fetch_one_row()

                if len(query_result) > 1:
                    # If there is running job for the subclient
                    self.log.info(query_result)
                    job_id = query_result[0]
                    self.log.info("Killing Job with JOB ID : %s", job_id)
                    self.navigator.navigate_to_jobs()
                    self.admin_console.access_tab('Active jobs')
                    # Need a try and catch to kill jobs as jobs may have completed before it is able to kill
                    try:
                        self.jobs.kill_job(job_id, wait=100)
                    except Exception as E:
                        self.log.info(
                            "Error occured at killing the job as job may have finished before kill happens"
                        )
                        return
                else:
                    self.log.info("No running jobs for the subclient")
        else:
            self.log.info("Running metallic testcase or the client is network share. Skipping querying the db")

    @test_step
    def configure_calender_for_restore(self, job_id: int) -> dict:
        """
        Configures the calender for the given job_id that is used to browse from calenders

        Args:
            job_id (int):

        Returns:
            dict: Calendar dictionary
        """

        job_obj: object = self.commcell.job_controller.get(job_id)
        job_start_time: str = job_obj._start_time

        # Sample Job Start Time : '2023-03-29 11:15:11'
        date, time = job_start_time.split(" ")

        # Converting date from string to int
        year, month, day = map(lambda x: int(x), date.split("-"))
        hour, minute, seconds = map(lambda x: int(x), time.split(":"))

        # get the controller datetime with timezone information
        # We use the controller datetime as the time in UI changes based on where we access the Command center from
        dt = datetime.datetime.now(datetime.timezone.utc)

        # get the timezone offset for the local machine compared to UTC
        # We use UTC as "job_obj._start_time" return timestamp in UTC time zone
        local_offset = dt.astimezone().utcoffset()

        # create a datetime object with a extracted timestamp and timezone
        dt = datetime.datetime(
            year, month, day, hour, minute, seconds, tzinfo=datetime.timezone.utc
        )

        # convert the datetime object to controller time zone
        new_tz = datetime.timezone(local_offset)
        dt = dt.astimezone(new_tz)

        # Extracing data from datetime object
        calender = {}
        calender["year"] = str(dt.year)
        calender["date"] = str(dt.day)
        calender["month"] = calendar.month_name[dt.month]
        calender["hours"] = dt.hour
        calender["minutes"] = dt.minute

        return calender

    def restore_cross_machine_from_subclient(self, calender, search_pattern=None):
        """ Restores cross machine from subclient calender
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info(
            "%s Starts cross machine restore from subclient %s", "*" * 8, "*" * 8
        )
        res_path = self.tcinputs['RestorePathForCrossMachine']
        dest_obj = self.commcell.clients.get(self.tcinputs['RestoreMachine'])
        display_name = dest_obj.display_name
        if self.dest_machine.check_directory_exists(res_path):
            self.dest_machine.remove_directory(res_path)
        self.dest_machine.create_directory(directory_name=res_path)
        if self.is_client_network_share:
            if self.is_cifs_agent:
                search_pattern = search_pattern[2:]
                search_pattern = "UNC-NT_" + search_pattern
            else:
                search_pattern = search_pattern.replace(":", "")

        self.navigate_to_client_page()
        self.navigate_to_subclients_tab()
        self.fs_sub_client.access_subclient(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name
        )

        self.wait_for_calendar_to_load()

        if not self.is_client_network_share:
            job_id = self.fs_sub_client_details.restore_from_calender(
                calender,
                dest_client=display_name,
                search_pattern=search_pattern,
                rest_path=res_path
            )
        else:
            # To restore from NAS to Regular FS, we still get the impersonation prompt. Adding nfs and nas as True
            job_id = self.fs_sub_client_details.restore_from_calender(
                calender,
                dest_client=display_name,
                search_pattern=search_pattern,
                rest_path=res_path,
                cifs=self.is_cifs_agent,
                nfs=not self.is_cifs_agent
            )
        self.wait_for_job_completion(job_id)
        return res_path

    def restore_cross_machine_from_backupset(self, calender, search_pattern=None):
        """ Restores cross machine from backupset calender
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info(
            "%s Starts cross machine restore from subclient %s", "*" * 8, "*" * 8
        )
        res_path = self.tcinputs['RestorePathForCrossMachine']
        dest_obj = self.commcell.clients.get(self.tcinputs['RestoreMachine'])
        display_name = dest_obj.display_name
        if self.dest_machine.check_directory_exists(res_path):
            self.dest_machine.remove_directory(res_path)
        self.dest_machine.create_directory(directory_name=res_path)
        if self.is_client_network_share:
            if self.is_cifs_agent:
                search_pattern = search_pattern[2:]
                search_pattern = "UNC-NT_" + search_pattern
            else:
                search_pattern = search_pattern.replace(":", "")

        self.navigate_to_client_page()

        if not self.is_client_network_share:
            job_id = self.agent_overview.restore_from_calender(
                calender,
                backupset_name=self.tcinputs['BackupsetName'],
                search_pattern=search_pattern,
                rest_path=res_path,
                dest_client=display_name
            )
        else:
            job_id = self.agent_overview.restore_from_calender(
                calender,
                backupset_name=self.tcinputs['BackupsetName'],
                dest_client=display_name,
                search_pattern=search_pattern,
                rest_path=res_path,
                cifs=self.is_cifs_agent,
                nfs=not self.is_cifs_agent
            )

        self.wait_for_job_completion(job_id)
        return res_path

    def restore_out_of_place_from_subclient(self, calender, search_pattern=None):
        """Restores the subclient from subclient level calender
        Raises:
            Exception :
                -- if fails to run the restore operation
         """
        self.log.info(
            "%s Starts out_of_place restore for subclient %s", "*" * 8, "*" * 8
        )
        self.restore_path = self.tcinputs['RestorePath']

        if not self.is_client_network_share:
            if self.machine.check_directory_exists(self.restore_path):
                self.machine.remove_directory(self.restore_path)
            self.machine.create_directory(self.restore_path, False)
        else:
            mounted_rest_path = self.restore_path.replace(self.test_path, self.temp_mount_path)
            self.client_machine.create_directory(mounted_rest_path, force_create=True)

        self.navigate_to_client_page()
        self.navigate_to_subclients_tab()
        self.fs_sub_client.access_subclient(
            backupset_name=self.tcinputs['BackupsetName'],
            subclient_name=self.sub_client_name
        )

        self.wait_for_calendar_to_load()

        if not self.is_client_network_share:
            job_id = self.fs_sub_client_details.restore_from_calender(
                calender,
                search_pattern=search_pattern,
                rest_path=self.restore_path
            )
        else:
            impersonate_user = None

            if self.is_cifs_agent:
                impersonate_user = {
                    "username": self.impersonate_user,
                    "password": self.impersonate_password
                }

                search_pattern = search_pattern[2:]
                search_pattern = "UNC-NT_" + search_pattern
            else:
                search_pattern = search_pattern.replace(":", "")

            job_id = self.fs_sub_client_details.restore_from_calender(calender,
                                                                      search_pattern=search_pattern,
                                                                      rest_path=self.restore_path,
                                                                      dest_client=self.data_access_nodes[0],
                                                                      impersonate_user=impersonate_user,
                                                                      cifs=self.is_cifs_agent,
                                                                      nfs=not self.is_cifs_agent
                                                                      )

        self.wait_for_job_completion(job_id)

    def restore_out_of_place_from_backupset(self, calender, search_pattern=None):
        """ Restores the subclient
                Raises:
                    Exception :
                     -- if fails to run the restore operation
         """
        self.log.info(
            "%s Starts out_of_place restore for subclient %s", "*" * 8, "*" * 8
        )
        self.restore_path = self.tcinputs['RestorePath']

        if not self.is_client_network_share:
            if self.machine.check_directory_exists(self.restore_path):
                self.machine.remove_directory(self.restore_path)
            self.machine.create_directory(self.restore_path, False)
        else:
            mounted_rest_path = self.restore_path.replace(self.test_path, self.temp_mount_path)
            self.client_machine.create_directory(mounted_rest_path, force_create=True)

        self.navigate_to_client_page()

        if not self.is_client_network_share:
            job_id = self.agent_overview.restore_from_calender(
                calender,
                backupset_name=self.tcinputs['BackupsetName'],
                search_pattern=search_pattern,
                rest_path=self.restore_path
            )
        else:
            impersonate_user = None

            if self.is_cifs_agent:
                impersonate_user = {
                    "username": self.impersonate_user,
                    "password": self.impersonate_password
                }

                search_pattern = search_pattern[2:]
                search_pattern = "UNC-NT_" + search_pattern
            else:
                search_pattern = search_pattern.replace(":", "")

            job_id = self.agent_overview.restore_from_calender(calender,
                                                               backupset_name=self.tcinputs['BackupsetName'],
                                                               search_pattern=search_pattern,
                                                               rest_path=self.restore_path,
                                                               dest_client=self.data_access_nodes[0],
                                                               impersonate_user=impersonate_user,
                                                               cifs=self.is_cifs_agent,
                                                               nfs=not self.is_cifs_agent
                                                               )

        self.wait_for_job_completion(job_id)

    @test_step
    def restore_from_backupsetlevel_calender_and_verify(
            self, job_id, search_pattern=None
    ):
        """
        Restore from backupset level calender and verify OOP and Cross Machine Restore
        """
        calender = self.configure_calender_for_restore(job_id)

        # Verify OOP Restore
        self.log.info("%s Perform OOP restore and verify %s", "*" * 8, "*" * 8)
        self.restore_out_of_place_from_backupset(
            calender, search_pattern=search_pattern
        )
        # using cross machine as helper for inplace has issues

        if not self.is_client_network_share:
            self.fs_helper.validate_cross_machine_restore(self.content, self.restore_path)
        else:
            dest_client = self.commcell.clients.get(self.data_access_nodes[0])

            local_rest_path = self.restore_path.replace(self.test_path, self.temp_mount_path)

            self.fs_helper.validate_cross_machine_restore(self.content, local_rest_path, dest_client)

        self.log.info("%s Verified OOP restore %s", "*" * 8, "*" * 8)

        # Verify Cross machine restore
        restore_path = self.restore_cross_machine_from_backupset(
            calender, search_pattern
        )

        rest_client = self.commcell.clients.get(self.tcinputs["RestoreMachine"])

        self.fs_helper.validate_cross_machine_restore(self.content, restore_path, rest_client)

        self.log.info("%s Verified Cross machine restore %s", "*" * 8, "*" * 8)

    @test_step
    def restore_from_subclientlevel_calender(self, job_id, search_pattern=None):
        """
        Restore form subclientlevel calender
        """
        calender = self.configure_calender_for_restore(job_id)

        # Verify OOP Restore
        self.log.info("%s Perform OOP restore and verify %s", "*" * 8, "*" * 8)
        self.restore_out_of_place_from_subclient(
            calender, search_pattern=search_pattern
        )

        if not self.is_client_network_share:
            self.fs_helper.validate_cross_machine_restore(self.content, self.restore_path)
        else:
            dest_client = self.commcell.clients.get(self.data_access_nodes[0])

            local_rest_path = self.restore_path.replace(self.test_path, self.temp_mount_path)

            self.fs_helper.validate_cross_machine_restore(self.content, local_rest_path, dest_client)

        self.log.info("%s Verified OOP restore %s", "*" * 8, "*" * 8)

        # Verify Cross machine restore
        restore_path = self.restore_cross_machine_from_subclient(
            calender, search_pattern
        )
        rest_client = self.commcell.clients.get(self.tcinputs["RestoreMachine"])

        self.fs_helper.validate_cross_machine_restore(
            self.content, restore_path, rest_client
        )
        self.log.info("%s Verified Cross machine restore %s", "*" * 8, "*" * 8)

    @test_step
    def check_rpo_restore_from_backupset(self):
        """ Runs full and incr backup with restore from calender at backupset level"""
        self.kill_if_any_running_job()
        self.backup_job(Backup.BackupType.FULL)
        self.refresh()
        self.log.info("%s Full job Completed %s", "*" * 8, "*" * 8)
        incr_path = self.content[0] + self.delimiter + "Incr"
        self.fs_helper.generate_testdata([".txt", ".xml"], incr_path, 6)
        incr_job_id = self.backup_job(Backup.BackupType.INCR)
        self.log.info("%s Incr job Completed %s", "*" * 8, "*" * 8)

        if not self.is_client_network_share:
            self.restore_from_backupsetlevel_calender_and_verify(
                incr_job_id, self.content[0]
            )
        else:
            self.restore_from_backupsetlevel_calender_and_verify(
                incr_job_id, self.UNC_content[0]
            )

    @test_step
    def check_rpo_restore_from_subclientdetails(self):
        """ Runs full and incr backup with restore from calender from subclientdetails page"""
        self.kill_if_any_running_job()
        self.backup_job(Backup.BackupType.FULL)
        self.refresh()
        incr_path = self.content[0] + self.delimiter + "Incr"
        self.fs_helper.generate_testdata(['.txt', '.xml'], incr_path, 6)
        incr_job_id = self.backup_job(Backup.BackupType.INCR)
        self.log.info("%s Incr job Completed %s", "*" * 8, "*" * 8)

        if not self.is_client_network_share:
            self.restore_from_subclientlevel_calender(incr_job_id, self.content[0])
        else:
            self.restore_from_subclientlevel_calender(incr_job_id, self.UNC_content[0])

    @test_step
    def delete_sub_client(self):
        """ Verifies whether subclient exists or not and then deletes the subclient """
        if self.fs_sub_client.is_subclient_exists(self.sub_client_name, self.tcinputs['BackupsetName']):
            # Check if any job is being run for subclient as delete will fail otherwise

            self.kill_if_any_running_job()
            self.navigate_to_client_page()
            self.navigate_to_subclients_tab()
            self.log.info("%s Deletes subclient %s", "*" * 8, "*" * 8)
            self.fs_sub_client.delete_subclient(self.sub_client_name, self.tcinputs['BackupsetName'])
            self.admin_console.wait_for_completion()

    def setup(self):
        """ Pre-requisites for this testcase """

        self.fs_helper = FSHelper(self)
        self.fs_helper.populate_tc_inputs(self, mandatory=False)
        self.isMetallic = self.tcinputs.get("IsMetallic", "false").lower() == "true"

        self.impersonate_user = self.tcinputs.get("ImpersonateUser")
        self.impersonate_password = self.tcinputs.get("ImpersonatePassword", None)
        if self.impersonate_password:
            self.impersonate_password = str(b64decode(self.tcinputs.get("ImpersonatePassword")), 'utf-8')

        self.browser = BrowserFactory().create_browser_object()
        self.log.info("%s Opening the browser %s", "*" * 8, "*" * 8)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname
                                          )

        # Updated login method to use paramters from config.json
        # Added this so that cases can be handled from autocenter
        self.admin_console.login(username=self.config.ADMIN_USERNAME,
                                 password=self.config.ADMIN_PASSWORD)

        self.hub_dashboard = Dashboard(
            self.admin_console,
            HubServices.file_system,
            app_type=FileObjectTypes.file_server
        )
        try:
            self.admin_console.click_button("OK, got it")
        except BaseException:
            self.log.info("No Popup seen")
        if self.isMetallic:
            self.hub_dashboard.choose_service_from_dashboard()
            self.hub_dashboard.click_new_configuration()
            self.log.info("\n\n%s RUNNING TESTCASE FOR METALLIC %s\n", "-" * 5, "-" * 5)
        else:
            self.log.info("\n\n%s RUNNING TESTCASE FOR COMMAND CENTER %s\n", "-" * 5, "-" * 5)

        self.table = Rtable(self.admin_console)
        self.fs_sub_client = Subclient(self.admin_console)
        self.fs_sub_client_details = SubclientOverview(self.admin_console)
        self.fs_utils = FileServersUtils(self.admin_console)
        self.agent_overview = Overview(self.admin_console)

        if not self.is_client_network_share:
            self.machine = Machine(self.client)

        dest_client = self.commcell.clients.get(self.tcinputs['RestoreMachine'])
        self.dest_machine = Machine(dest_client, self.commcell)
        self.jobs = Jobs(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.job_details = JobDetails(self.admin_console)
        self.rfile_server = RFileServers(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.define_content_and_path()
            self.navigate_to_client_page()
            self.sub_client_name = "Test_" + self.id
            self.add_subclient()
            self.check_rpo_restore_from_backupset()
            self.navigate_to_client_page()
            self.delete_sub_client()
            self.delete_content()
            self.sub_client_name = "Test_" + self.id
            self.define_content_and_path()
            self.navigate_to_client_page()
            self.add_subclient()
            self.check_rpo_restore_from_subclientdetails()
            self.delete_sub_client()

        except Exception as excp:
            handle_testcase_exception(self, excp)

    def tear_down(self):
        if self.cleanup_run:
            self.log.info("Performing cleanup")
            self.delete_content()
            self.delete_sub_client()

            if self.is_cifs_agent:
                if self.fs_helper.is_drive_mounted(self.client_machine, self.temp_mount_path):
                    self.fs_helper.unmount_network_drive(self.client_machine, self.temp_mount_path)
            else:
                if self.client_machine.is_path_mounted(self.temp_mount_path):
                    self.client_machine.unmount_path(self.temp_mount_path)
                if self.client_machine.check_directory_exists(self.temp_mount_path):
                    self.client_machine.remove_directory(self.temp_mount_path)

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
