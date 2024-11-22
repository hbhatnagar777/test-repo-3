# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Helper file for performing DevOps operations.

This file consists of a class named: DevOpsHelper, which establishes connection with required
helpers and performs devops common operations.

The instance of this class can be used to perform various common operations related to DevOps app,
like,

    #.  Creating required helper objects based on tc inputs
    #.  Methods for validation of job restartability and staging paths
    #.  Methods for data aging and LSR VOI validation

DevOpsHelper
=============

    __init__()                               --   Initialize instance of the DevOpsHelper class.

    __setup_helpers()                        --   Creates required helper objects based on tcinputs

    __validate_staging()                     --   Validates if correct staging path is used by the access node(s) or not for a given job

    __check_job_restartability()             --   Method for validating restartability by suspending or resuming a job

    __switch_to_webconsole()                 --   Switches to webconsole

    __do_private_metrics_upload()            --   Runs a private metrics upload operation

    __verify_entry_in_voi_table()            --   Verifies if entry is present in VOI table for LSR in CC level or SCPU in WC level

    __get_license_summary_data()             --   Getting VOI license usage and verifies entries are present in LSR admin console report

    __get_webconsole_license_summary_data()  --   Getting VOI license usage and verifies entries are present in LSR WW and SCPU web console report

    wait_for_job_completion()                --   Wait till job gets completed and performs other operations based on args

    modify_plan_retention()                  --   Modifies plan retention based on given args

    move_job_and_validate_data_aging()       --   Moves job and validates data aging

    get_voi_count()                          --   Compares VOI count in LSR and LSR WW report
"""
import json
import time
import datetime

from Application.DevOps.AzureDevOpsUtils.azuredevops_helper import AzureDevOpsHelper
from Application.DevOps.GitHubUtils.github_helper import GitHubHelper
from MediaAgents.MAUtils.mahelper import MMHelper

from AutomationUtils import logger
from AutomationUtils import database_helper
from AutomationUtils.machine import Machine
from AutomationUtils.database_helper import CommServDatabase

from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.AdminConsole.Reports.Custom import viewer


class DevOpsHelper:
    """Class which establishes connection with required helpers and performs devops common operations."""

    def __init__(self, commcell, tcinputs, app_type, admin_console=None):
        """
        Initialize instance of the DevOpsHelper class.
        Args:
            commcell        (obj)     -- commcell object
            tcinputs        (dict)    -- tcinputs
            admin_console   (obj)     -- admin_console object
        """
        self.id = None
        self.commcell = commcell
        self.tcinputs = tcinputs
        self.app_type = app_type
        self.log = logger.get_log()
        self.admin_console = admin_console
        self.web_console = None
        self.report_viewer = None
        self.azhelper = None
        self.githelper = None
        self.mmhelper = None
        self.csdb = None
        self._agent = None
        self.__storage_policy = None
        self.__copy = None
        nodes = self.tcinputs['access_nodes']
        testdata = self.tcinputs.get('test_data', {})
        self.access_nodes = json.loads(nodes) if isinstance(nodes, str) else nodes
        self.test_data = json.loads(testdata) if isinstance(testdata, str) else testdata
        self.access_nodes = self.tcinputs.get("des_server", self.access_nodes)
        if "staging_path" in self.tcinputs:
            self.tcinputs["staging_path"] += f"_{int(time.time())}"
        if isinstance(self.access_nodes, str):
            self.access_nodes = [self.access_nodes]
        self.__setup_helpers()

    def __setup_helpers(self):
        """Creates required helper objects based on tcinputs"""
        if self.app_type == 'azure':
            self.azhelper = AzureDevOpsHelper(self.commcell,
                                              self.tcinputs['azure_organization_name'],
                                              self.tcinputs['azure_access_token'],
                                              self.access_nodes,
                                              git_bin=self.tcinputs.get('git_bin'))
        if self.app_type == 'git':
            access_node = None
            if self.azhelper is not None:
                access_node = [self.azhelper.client_machine.machine_name]
            self.githelper = GitHubHelper(self.commcell,
                                          self.tcinputs['git_organization_name'],
                                          self.tcinputs['git_access_token'],
                                          access_node or self.access_nodes,
                                          git_bin=self.tcinputs.get('git_bin'),
                                          base_url=self.tcinputs.get('git_host_url'))
        if "MediaAgentName" in self.tcinputs:
            database_helper.set_csdb(CommServDatabase(self.commcell))
            self.csdb = database_helper.get_csdb()
            self.mmhelper = MMHelper(self)
            plan = self.commcell.plans.get(self.tcinputs['plan'])
            self.__storage_policy = self.commcell.storage_policies.get(plan.storage_policy.storage_policy_name)
        if self.admin_console is not None:
            self.report_viewer = viewer.CustomReportViewer(self.admin_console)

    def __validate_staging(self, job_obj):
        """
        Validates if correct staging path is used by the access node(s) or not for a given job
        Args:
            job_obj             (obj)       --  job object
        Raises:
            Exception:
                If staging path is not used by access node(s).
        """
        staging_path = self.tcinputs.get('staging_path')
        for client in self.tcinputs.get('access_nodes'):
            client_machine = Machine(client, self.commcell)
            staging_files = client_machine.get_folders_in_path(staging_path)
            job_type = job_obj.job_type
            base_folder = ""
            if job_type == "Backup":
                sc_id = job_obj.summary.get('subclient')
                base_folder = client_machine.join_path(staging_path,
                                                       f"{job_type}_{sc_id}")
            elif job_type == "Restore":
                instance_id = f"{job_obj.summary.get('destinationClient').get('clientId')}"
                job_id = f"{job_obj.job_id}"
                base_folder = client_machine.join_path(staging_path,
                                                       f"Git{job_type}_"
                                                       f"{instance_id}_{job_id}")
            if base_folder in staging_files:
                self.log.info(f"Staging verified successfully in {client}")
            else:
                self.log.info(f"staging verification failed for {client}")
                raise Exception(f"staging verification failed for {client}")

    def __check_job_restartability(self, job_obj, validate_staging=False):
        """
        Method for validating restartability by suspending or resuming a job
        Args:
            job_obj             (obj)       --  job object
            validate_staging    (bool)      --  verifies staging if True
        Raises:
            Exception:
                If failed to suspend or resume the job.
                If staging path is not used by access node(s).
        """
        try:
            sleep_time = 30
            while job_obj.status.upper() == 'WAITING':
                time.sleep(sleep_time)
            if job_obj.status.upper() == 'PENDING':
                self.log.info("Job is in pending state. Skipping restartability verification")
                return
            if job_obj.is_finished:
                self.log.info("Job is already finished. Cannot verify restartability")
                return
            time.sleep(20)
            ignore_restartability_phases = [None, 'Post Operation']
            if validate_staging:
                ignore_restartability_phases.append('Archive Index')
                sleep_time = 45
            phase_restart_count = 0
            while job_obj.phase not in ignore_restartability_phases:
                current_phase = job_obj.phase
                phase_restart_count += 1
                self.log.info(f"Phase:{current_phase} and restart count:{phase_restart_count}")
                # suspending the job
                self.log.info(f"Suspending Job {job_obj.job_id} in {current_phase} phase")
                job_obj.pause(wait_for_job_to_pause=True)
                self.log.info("Job Suspended Successfully")
                time.sleep(sleep_time)
                # staging validation by checking if staging related directories are created
                if validate_staging:
                    self.__validate_staging(job_obj)
                # resuming job
                if job_obj.is_finished:
                    self.log.info("Job is already finished. Cannot resume a finished job")
                    return
                self.log.info(f"Resuming Job {job_obj.job_id} in {current_phase} phase")
                job_obj.resume(wait_for_job_to_resume=True)
                self.log.info("Job Resumed Successfully")
                while current_phase == job_obj.phase:
                    if phase_restart_count == 3:
                        time.sleep(2*sleep_time)
                    else:
                        time.sleep(sleep_time)
                        if current_phase != job_obj.phase:
                            phase_restart_count = 0
                        break
                else:
                    phase_restart_count = 0
        except Exception as exp:
            self.log.exception(f"Exception occurred in getting the job status: {str(exp)}")
            raise exp

    def __switch_to_webconsole(self):
        """Switches to webconsole"""
        if self.web_console is None:
            self.web_console = WebConsole(self.admin_console.browser,
                                          self.commcell.webconsole_hostname)
        self.web_console.goto_webconsole()
        if self.web_console.is_login_page():
            self.web_console.login(username=self.admin_console.username,
                                   password=self.admin_console.password,
                                   stay_logged_in=True)
            self.web_console.wait_till_load_complete()

    def __do_private_metrics_upload(self):
        """Runs a private metrics upload operation"""
        from cvpysdk.metricsreport import PrivateMetrics
        self.log.info("Initiating Private metrics upload now and waiting for completion")
        private_metrics = PrivateMetrics(self.commcell)
        private_metrics.update_url(self.commcell.webconsole_hostname)
        private_metrics.enable_all_services()
        private_metrics.enable_chargeback(daily=True, weekly=True, monthly=True)
        self.log.info(f"Last upload time:{datetime.datetime.fromtimestamp(int(private_metrics.lastuploadtime)).strftime('%Y-%m-%d %H:%M:%S')}")
        self.log.info(f"Upload start time:{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        private_metrics.upload_now()
        private_metrics.wait_for_uploadnow_completion()
        private_metrics.refresh()
        self.log.info(f"Upload end time:{datetime.datetime.fromtimestamp(int(private_metrics.lastuploadtime)).strftime('%Y-%m-%d %H:%M:%S')}")
        self.log.info("Upload completed")

    def __verify_entry_in_voi_table(self, expected_entries):
        """
        Verifies if entry is present in VOI table for LSR in CC level or SCPU in WC level
        Args:
            expected_entries    (dict)    --  {client_id:[repos_list]}
        Raises:
            Exception:
                If expected entries are not present in VOI table
        """
        data_table = viewer.DataTable("")
        self.report_viewer.associate_component(data_table)
        data_table.enable_all_columns()
        for client_id in expected_entries:
            repo_list = expected_entries[client_id]
            self.log.info(f"Verifying if entries for repo_list: {repo_list} are present in VOI "
                          f"table for client: {client_id}")
            if "worldwide" in self.admin_console.driver.current_url.lower():
                data_table.set_filter('Client ID', client_id)
            else:
                data_table.set_filter('ID', client_id)
            table_data = data_table.get_table_data()
            self.log.info(table_data)
            if "worldwide" in self.admin_console.driver.current_url.lower():
                if sorted(table_data['Client']) != sorted(repo_list):
                    raise Exception(f"Entry validation failed. \n Expected data: {repo_list}"
                                    f" \n Data present: {table_data} \n local:{locals()}")
            else:
                if sorted(table_data['Name']) != sorted(repo_list):
                    raise Exception(f"Entry validation failed. \n Expected data: {repo_list}"
                                    f" \n Data present: {table_data} \n local:{locals()}")
            self.log.info(f"Successfully Verified entries for repo_list: {repo_list} are present in "
                          f"VOI table for client: {client_id}")

    def __get_license_summary_data(self, verify_entry=False):
        """
        Getting VOI license usage and verifies entries are present in LSR admin console report
        Args:
            verify_entry    dict    --  Expected entries to be present in VOI table
                default - False (skips entry verification)
        Returns:
            purchased and used license count from LSR in admin console
        Raises:
            Exception:
                If entry verification failed or admin_console object is not initialized
        """
        if self.admin_console is None:
            raise Exception("Initiate helper object with admin_console argument")
        self.admin_console.goto_adminconsole()
        self.admin_console.navigator.navigate_to_reports()
        ManageReport(self.admin_console).access_report('License summary')
        self.admin_console.select_hyperlink('Recalculate')
        time.sleep(30)
        self.admin_console.wait_for_completion()
        data_table = viewer.DataTable("Virtual Operating Instances")
        self.report_viewer.associate_component(data_table)
        data = data_table.get_table_data()
        index = data['License'].index('Virtual Operating Instances')
        if verify_entry and isinstance(verify_entry, dict):
            self.admin_console.select_hyperlink('Virtual Operating Instances')
            self.admin_console.select_hyperlink('Refresh')
            self.__verify_entry_in_voi_table(verify_entry)
        else:
            self.log.info("Skipping VOI entry verification")
        return int(data['Available Total (instances)'][index]), int(data['Used (instances)'][index])

    def __get_webconsole_license_summary_data(self, verify_entry=False, verify_scpu_entry=True):
        """
        Getting VOI license usage and verifies entries are present in LSR WW and SCPU web console report
        Returns:
            purchased and used license count from LSR in web console
        Raises:
            Exception:
                If entry verification failed in LSR WW and SCPU Webconsole report
        """
        self.__switch_to_webconsole()
        try:
            self.web_console.goto_commcell_dashboard()
        except Exception:
            self.log.info("dashboard not present, using url")
            dashboard_ww = f"{self.admin_console.driver.current_url.split('/applications/')[0]}" \
                           f"/reports/index.jsp?page=Dashboard"
            self.admin_console.driver.get(dashboard_ww)
            self.admin_console.wait_for_completion()
        web_nav = Navigator(self.web_console)
        web_nav.goto_worldwide_commcells()
        self.admin_console.select_hyperlink(self.commcell.commserv_name)
        lsr_worldwide_xpath = '//*[@id="CurrentCapacityUsage"]/div/a'
        self.admin_console.click_by_xpath(lsr_worldwide_xpath)
        time.sleep(15)
        self.log.info(f"Before Refresh Last Updated Time:{self.admin_console.label_getvalue('Last')}")
        self.admin_console.click_by_id('refreshButton')
        time.sleep(15)
        self.log.info(f"After Refresh Last Updated Time:{self.admin_console.label_getvalue('Last')}")
        data_table = viewer.DataTable("Virtual Operating Instances")
        self.report_viewer.associate_component(data_table)
        data = data_table.get_table_data()
        index = data['License'].index('Virtual Operating Instances')
        commcell_id = self.admin_console.driver.current_url.split('input.CommCell=')[-1].split('&')[0]
        if verify_entry and isinstance(verify_entry, dict):
            lsr_ww = f"{self.admin_console.driver.current_url.split('?')[0]}" \
                     f"?reportId=License%20Summary%20Worldwide" \
                     f"&pageName=Page19&input.CommCell={commcell_id}"
            self.admin_console.driver.get(lsr_ww)
            self.admin_console.wait_for_completion()
            self.admin_console.click_by_id('refreshButton')
            self.__verify_entry_in_voi_table(verify_entry)
        else:
            self.log.info("Skipping VOI entry verification")
        if verify_scpu_entry and isinstance(verify_scpu_entry, dict):
            sc_peak_usage = f"{self.admin_console.driver.current_url.split('?')[0]}" \
                            f"?reportId=Subclient%20Peak%20Usage%20Worldwide" \
                            f"&pageName=Page18&input.CommCell={commcell_id}" \
                            f"&input.month={'-'.join(str(datetime.date.today()).split('-')[:-1] + ['01'])}"
            self.admin_console.driver.get(sc_peak_usage)
            self.admin_console.wait_for_completion()
            self.admin_console.click_by_id('refreshButton')
            self.__verify_entry_in_voi_table(verify_scpu_entry)
        return int(data['Available Total (instances)'][index]), int(data['Used (instances)'][index])

    def wait_for_job_completion(self, job_id, check_restartability=False, validate_staging=False,
                                verify_jpr=False, is_cwe=False):
        """
        Wait till job gets completed and performs other operations
        Args:
            job_id                      (int)       -- Job id
            check_restartability        (bool)      -- Checks job restartability
            validate_staging            (bool)      -- Validates staging directory
            verify_jpr                  (bool/str)  -- matches given JPR and continues accordingly
            is_cwe                      (bool)      -- verifies if job should be CWE or not
        Raises:
            Exception:
                If job is failed to complete
        Returns:
            job_obj for the job
        """
        job_obj = self.commcell.job_controller.get(job_id)
        if check_restartability or validate_staging:
            self.__check_job_restartability(job_obj, validate_staging)
        self.log.info(f"Wait for {job_obj.job_type} job: {job_id} to complete")
        if job_obj.wait_for_completion():
            self.log.info("[%s] job completed with job id:[%s]", job_obj.job_type, job_id)
            job_status = job_obj.status.lower()
            if job_status == 'completed':
                self.log.info("Job completed without any errors, continuing tc.")
            elif is_cwe:
                if job_status == 'completed w/ one or more errors':
                    self.log.info("Job is expected to complete with errors, continuing tc.")
                else:
                    self.log.info(f"Job should be CWE, but job is {job_obj.status}")
            else:
                raise Exception("Please refer job and check if it is the expected status, "
                                "job should've completed without any errors")
        else:
            err_str = "[%s] job id for [%s] failed with JPR: [%s]" % (job_id, job_obj.job_type,
                                                                      job_obj.pending_reason)
            if verify_jpr and verify_jpr in job_obj.pending_reason:
                self.log.info(f"Job is expected to fail with {verify_jpr}, continuing with tc.")
            else:
                if verify_jpr:
                    self.log.info(f"Job failed with diff JPR: {job_obj.pending_reason}, expected JPR: {verify_jpr}")
                raise Exception(err_str)
        return job_obj

    def modify_plan_retention(self, copy_props=None, cycles=None, managed_disk_space=None):
        """
        Modifies plan retention
        Args:
            copy_props          (dict)     -- copy retention and managed disk space properties
                default - {"Primary": {"retention": (1, 0, -1), "managed_disk_space": False}}
            cycles              (int)      -- can be specified to edit only no of cycles in copy props
            managed_disk_space  (bool)     -- can be specified to edit only managed disk space in copy props
        Returns:
            old properties of the copy
        """
        if copy_props is None:
            copy_props = {"Primary": {"retention": (1, 0 if cycles is None else int(cycles), -1),
                                      "managed_disk_space": managed_disk_space or False}}
        else:
            copy_name = next(iter(copy_props))
            copy_retention = copy_props.get(copy_name)["retention"]
            copy_props.get(copy_name)["retention"] = (copy_retention['days'], copy_retention['cycles'], copy_retention['archiveDays'])
        copy_name = next(iter(copy_props))
        self.__copy = self.__storage_policy.get_copy(copy_name)
        old_copy_props = {copy_name: {"retention": self.__copy.copy_retention,
                                      "managed_disk_space": self.__copy.copy_retention_managed_disk_space}}
        self.__copy.copy_retention = copy_props.get(copy_name).get('retention', (1, 0, -1))
        self.__copy.copy_retention_managed_disk_space = copy_props.get(copy_name).get('managed_disk_space', False)
        return old_copy_props

    def move_job_and_validate_data_aging(self, job_id, is_aged=True, run_aging=True,
                                         move_job=True, copy_name=None):
        """
        Moves job and validates data aging
        Args:
            job_id              (int)      -- Job id
            is_aged             (bool)     -- this specifies if job is expected to age
            run_aging           (bool)     -- this specifies if data aging job should be triggered
            move_job            (bool)     -- this specifies if job needs to be moved back by 1 day
            copy_name           (str)      -- name of the copy on which data aging needs to run
        Raises:
            Exception:
                If job is not aged/unaged as expected based on is_aged property
        """
        if move_job:
            self.mmhelper.move_job_start_time(int(job_id), 1)
        if self.__copy is None:
            self.__copy = self.__storage_policy.get_copy(copy_name or "Primary")
        if run_aging:
            da_job = self.commcell.run_data_aging(copy_name=self.__copy.copy_id,
                                                  storage_policy_name=self.__storage_policy.storage_policy_name,
                                                  is_granular=True,
                                                  include_all_clients=True)
            self.wait_for_job_completion(da_job.job_id)
        if job_id is not None:
            retcode = self.mmhelper.validate_job_prune(int(job_id), self.__copy.copy_id)
            if bool(is_aged) == bool(retcode):
                if is_aged:
                    age_msg = "successfully aged"
                else:
                    age_msg = "not aged as expected"
                self.log.info(f"Backup job: {job_id} is {age_msg}")
            else:
                if is_aged:
                    age_excp = f"expected to age"
                else:
                    age_excp = f"not expected to age"
                raise Exception(f"Backup job: {job_id} is {age_excp}")

    def get_voi_count(self, verify_entry=None, verify_scpu_entry=None):
        """
        Compares VOI count in LSR and LSR WW report
        Args:
            verify_entry       (dict)    --  verifies if given entries present in LSR and LSR WW VOI reports
                default - False (skips entry verification)
                dict format - {client_id:[repos_list]}
            verify_scpu_entry  (dict)    --  verifies if given entries present in SCPU VOI reports
                default - False (skips entry verification)
                dict format - {client_id:[repos_list]}
        Returns:
            used and purchased VOI count if matched in both LSR and LSR WW reports
        Raises:
            Exception:
                If count match failed in LSR and LSR WW report
                If entry verfication failed in LSR, LSR WW and SCPU reports
        """
        cc_data = self.__get_license_summary_data(verify_entry)
        self.__do_private_metrics_upload()
        wc_data = self.__get_webconsole_license_summary_data(verify_entry, verify_scpu_entry)
        if cc_data != wc_data:
            raise Exception(f"World LSR and Local LSR data are not same.\nWorld:"
                            f"{wc_data}\nLocal:{cc_data}")
        return cc_data
