# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""

This module provides the function or operations that can be used to run
basic operations and tests on the active jobs page, job history page and job details page


---------------------------------------------------------------------------------------------

jobs_columns()                              --  This function returns the column specifications of jobs grids


JobsHelper : This class provides methods for jobs page related tests

__init__()                                  --  Initialize object of JobsHelper class associated

================================= SETUP UTILS ==============================================

start_blackout_window()                     --  sets up a full blackout window to block any job changes during test

delete_blackout_window()                    --  deletes the created blackout window

setup_multiple_jobs()                       --  sets up multiple jobs for testing

get_job_subclient()                         --  gets the subclient sdk object of given job

get_later_job()                             --  gets the latest job of the same subclient as given job

random_job()                                --  gets a random job from jobhistory to test on

renew_job()                                 --  renews existing self.job and returns a resubmitted job in new state

setup_job()                                 --  sets up a job to test on depending on init options

clean_up()                                  --  cleans up any changes made by this helper

================================= VALIDATION UTILS (Class Methods) ============================

group_api_jobs_by_column()                  --  groups the given jobs data based on given column

================================= VALIDATION SETUPS ===========================================

setup_active_jobs()                         --  Sets up active jobs page

setup_jobs_history()                        --  Sets up job history page

validate_api_ui_sync()                      --  Validates jobs and their status sync between API resp and UI view

================================= TEST STEPS =====================================

run_and_validate()                          --  Runs job and validates if it appears in table

suspend_and_validate()                      --  Suspends job and validates if it has suspended

resume_and_validate()                       --  Resumes job and validates if it has resumed status

kill_and_validate()                         --  Kills job and validates if it shows killed status

resubmit_and_validate()                     --  Resubmits job and validates if toast appears

validate_redirects()                        --  Validates the redirect links for a job

multi_run_and_validate()                    --  Starts multiple jobs and validates all appear in table

multi_validate_api_ui_sync()                --  validates sync of jobs and their status between UI and API

get_best_criteria_test()                    --  calculates the best multi job control criteria to test

multi_actions_validate()                    --  performs multi job control action and validates the result

----------------------------------------------------------------------------------------------------

JobDetailsHelper : This class provides methods for jobs details page related tests

__init__()                                 --  Initialize object of JobDetailsHelper class

================================= VALIDATION UTILS (Class Methods) ============================

compare_job_overview_data()     --  compares job overview data from UI with API

================================= TEST STEPS ====================================================

setup_job_details()             --  sets up job details page

validate_tabs()                 --  validates the tabs in job details page

validate_overview()             --  validates overview tab

validate_jd_redirects()         --  validates the redirect links from job details page

validate_resume()               --  validates resume from job details page

validate_suspend()              --  validates suspend from job details page

validate_kill()                 --  validates kill from job details page

validate_resubmit()             --  validate resubmit from job details page

"""
import functools
import itertools
import json
import os
import random
import re
import time
import traceback
from collections import defaultdict
from threading import Thread
from typing import Union, Callable

from dateutil.parser import parse
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException

from AutomationUtils import logger
from AutomationUtils.commonutils import parse_size, parse_duration, process_text
from AutomationUtils.database_helper import CommServDatabase
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Helper.rtable_helper import RTableHelper
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs, JOB_ID_LABEL, CLIENT_LABEL
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.Components.panel import MultiJobPanel
from Web.AdminConsole.Components.table import Rfilter
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure, CVWebAutomationException
from Web.Common.page_object import TestStep
from cvpysdk.commcell import Commcell
from cvpysdk.constants import AdvancedJobDetailType
from cvpysdk.job import Job
from cvpysdk.subclient import Subclient


# jobs table column specifications (referred from JobsGrid.js#L280)
def jobs_columns(t: dict = None, is_job_history: bool = False) -> dict:
    """
    returns the jobs table's complete columns specifications

    Args:
        t   (dict)              -   the adminconsole.props locale dict
        is_job_history  (bool)  -   set True to get column specs of job history table

    Returns:
        specs   (dict)          -   column specifications dict for jobs grids
    """
    if t is None:
        t = defaultdict(lambda k: k)
    specs = {
        t["Job\\ ID"]: {
            'cell_value': RTableHelper.ParsingCriteria.apply_typecast(int),
            'api_value_key': lambda api_row: api_row['jobSummary']['jobId'],
            'match_key': RTableHelper.MatchingCriteria.numeric,
            'is_primary_key': True,
        },
        t["Operation"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('localizedOperationName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["Status"]: {
            'api_value_key': lambda api_row: api_row['jobSummary']['localizedStatus'],
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["label.jobDescription"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('jobDescription'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["label.job.destinationServer"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('destinationClient', {}).get('displayName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["agentType"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('appTypeName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["Instance"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('instanceName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
            'filter_criteria': Rfilter.contains
        },
        t["Backup\\ Set"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('backupsetName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
            'filter_criteria': Rfilter.contains
        },
        t["SubClient"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('subclientName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
            'filter_criteria': Rfilter.contains
        },
        t["Backup\\ Type"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('localizedBackupLevelName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["label.planUsed"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('planName') or t["label.NA"],
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["label.storagePool"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('storagePolicy', {}).get('storagePolicyName')
                                             or t["label.NA"],
            'match_key': RTableHelper.MatchingCriteria.raw_string,
        },
        t["label.column.company"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('companyName'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
            'filter_criteria': Rfilter.contains
        },
        # t["Client\\ Group"]: {}  # THIS IS A PROBLEMATIC COLUMN, HARD TO PARSE VALUES, AVOIDING FOR NOW
        t["label.size"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('sizeOfApplication'),
            'match_key': RTableHelper.MatchingCriteria.size_str_vs_bytes,
            'sort_key': RTableHelper.SortingCriteria.size_type,
            'is_filterable': False,  # TODO: ADD SIZE TYPE FILTERS SUPPORT
            'is_searchable': not is_job_history
        },
        t["label.totalNumberOfFiles"]: {
            'cell_value': RTableHelper.ParsingCriteria.apply_typecast(int),
            'api_value_key': lambda api_row: api_row['jobSummary'].get('totalNumOfFiles') or 0,
            'match_key': RTableHelper.MatchingCriteria.numeric,
            'is_searchable': not is_job_history
        },
        t["label.start"]: {
            'api_value_key': lambda api_row: api_row['jobSummary']['jobStartTime'],
            'match_key': RTableHelper.MatchingCriteria.date_str_vs_timestamp_mdy,
            'sort_key': RTableHelper.SortingCriteria.datetime_mdy,
            'is_filterable': False,  # TODO: ADD DATE TIME FILTERS SUPPORT
            'is_searchable': not is_job_history
        },
        t["label.elapsed"]: {
            'api_value_key': lambda api_row: api_row['jobSummary']['jobElapsedTime'],
            'match_key': RTableHelper.MatchingCriteria.duration_str_vs_seconds,
            'sort_key': RTableHelper.SortingCriteria.duration_type,
            'is_filterable': False,  # TODO: ADD DURATION TYPE FILTERS SUPPORT
            'is_searchable': not is_job_history
        },
        t["label.errorDescription"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('pendingReason'),
            'match_key': RTableHelper.MatchingCriteria.raw_string,
            'filter_criteria': Rfilter.contains,
            'search_value_key': lambda error_desc: max(re.split(r'<.*?>', error_desc), key=len).strip(),
            'filter_value_key': lambda error_desc: max(re.split(r'<.*?>', error_desc), key=len).strip()
            # to avoid tags <> in search keyword, search maximum substring outside around the tags
        },
        # t["label.errorCode"]: {}  # ANOTHER PROBLEMATIC COLUMN, NEED TO CHECK HOW ERROR CODE IS POPULATED
        t["label.backupCopyStatusColumn"]: {
            'api_value_key': lambda api_row: str(
                api_row['jobSummary'].get('snapToTapeStatus') or t["label.NA"]),
            'sort_key': RTableHelper.SortingCriteria.with_nulls(
                [t["label.NA"]], RTableHelper.SortingCriteria.numeric),
            'filter_criteria': Rfilter.contains
        },
        t["label.backupCopyJobID"]: {
            'api_value_key': lambda api_row: str(
                api_row['jobSummary'].get('snapBkpCopyJobID') or t["label.NA"]),
            'sort_key': RTableHelper.SortingCriteria.with_nulls(
                [t["label.NA"]], RTableHelper.SortingCriteria.numeric),
        },
        t["Started\\ By"]: {
            'api_value_key': lambda api_row: api_row['jobSummary'].get('userName', {}).get('userName') or t["label.NA"],
            'match_key': RTableHelper.MatchingCriteria.raw_string,
            'filter_criteria': Rfilter.contains
        }

    }
    if not is_job_history:
        specs |= {
            f'{t["Current\\ Throughput"]} (GB/hr)': {
                'api_value_key': lambda api_row: str(
                    round(api_row['jobSummary'].get('currentThroughput'), 2) or t["label.N_SLASH_A"]),
                'sort_key': RTableHelper.SortingCriteria.with_nulls(
                    [t["label.N_SLASH_A"]], RTableHelper.SortingCriteria.numeric),
            },
            t["label.lastUpdate"]: {
                'api_value_key': lambda api_row: api_row['jobSummary'].get('lastUpdateTime') or 0,
                'match_key': lambda ui, api: (
                    RTableHelper.MatchingCriteria.date_str_vs_timestamp_mdy(ui, api) if ui else api <= 0),
                'sort_key': RTableHelper.SortingCriteria.with_nulls(
                    [''], RTableHelper.SortingCriteria.datetime_dmy),
                'is_filterable': False,  # TODO: ADD DATE TIME FILTERS SUPPORT
            },
            t["Progress"]: {
                'api_value_key': lambda api_row: api_row['jobSummary'].get('percentComplete'),
                'match_key': RTableHelper.MatchingCriteria.percentage_str_vs_int,
                'sort_key': RTableHelper.SortingCriteria.percentage_str,
                'is_filterable': False,
                'search_value_key': lambda ui: ui.rstrip("%")
            },
            t["label.column.phase"]: {
                'api_value_key': lambda api_row: api_row['jobSummary'].get('currentPhaseName'),
                'match_key': RTableHelper.MatchingCriteria.raw_string,
                'filter_criteria': Rfilter.contains
            },
            t["Media\\ Agent"]: {
                'api_value_key': lambda api_row: api_row['jobSummary'].get('mediaAgent', {}).get('mediaAgentName'),
                'match_key': RTableHelper.MatchingCriteria.raw_string,
                'filter_criteria': Rfilter.contains
            }
        }
    if is_job_history:
        specs |= {
            t["label.end"]: {
                'api_value_key': lambda api_row: api_row['jobSummary']['jobEndTime'],
                'match_key': RTableHelper.MatchingCriteria.date_str_vs_timestamp_mdy,
                'sort_key': RTableHelper.SortingCriteria.datetime_mdy,
                'is_filterable': False,  # TODO: ADD DATE TIME FILTERS SUPPORT
                'is_searchable': False
            },
            t["label.retainUntil"]: {
                'api_value_key': lambda api_row: api_row['jobSummary'].get('retainUntil') or 0,
                'match_key': lambda ui, api: (
                    RTableHelper.MatchingCriteria.date_str_vs_timestamp_mdy(ui, api) if api > 0 else (
                        t["label.infinite"] if api == -1 else t["label.NA"]
                    )
                ),
                'sort_key': RTableHelper.SortingCriteria.with_nulls(  # Need to check how ui sorts infinite retention
                    [t["label.NA"]], RTableHelper.SortingCriteria.datetime_mdy),
                'is_filterable': False,  # TODO: ADD DATE TIME FILTERS SUPPORT
                'is_searchable': False
            }
        }
    return specs


class JobsHelper:
    """
    Helper class of Jobs related tests from UI
    """
    test_step = TestStep()
    blackout_window = 'jobs_testcase_in_progress'

    redirects = {
        'Job link': r"/jobs/%s",
        'Restore': None,
        'View logs': r"/jobs/%s/logs",
        'View failed items': r"/viewFailedItems/%s",
        'Send logs': r'/sendLogs/jobs/%s',
        'View job details': r'/jobs/%s',
    }

    def __init__(self, admin_console: AdminConsole = None, commcell: Commcell = None, **options) -> None:
        """
        Initializes the JobsHelper class

        Args:
            admin_console (AdminConsole)    -   instance of AdminConsole class
            commcell (Commcell)             -   Commcell sdk object
            options:
                job_id (int/str)                -   id of job to test, will be killed and resubmitted if required
                                                    default: suitable job will be picked from job history
                app_id  (int/str)               -   app id of a subclient to use for running backup jobs to test on
                                                    default: None
                ui_delay    (int/str)           -   acceptable seconds time lag between API response and UI update
                                                    default: 30 seconds
                job_ids     (list)              -   ids of multiple diverse jobs to get
                                                    multiple active jobs in suspended state
                                                    default: None, will fail multi job tests if not given
                use_csv     (bool)              -   Will use csv export to read jobs table if True
                                                    (greatly reduces automation running time)
                                                    default: True
                job_filters (str)               -   Types of job to use for testing, (if job id not given)
                                                    default: None
                automation_lag  (int)           -   minimum duration of job to pick for test (if job id not given)
                                                    (usually depends on automation performance on controller)
                                                    default: 120 seconds
                size_threshold  (int)           -   minimum size of job to pick for test (if job id not given)
                                                    default: 500 MB
                leave_suspended (bool)          -   Will leave jobs in suspended state and avoid kill during cleanup
                                                    default: False

        Returns:
            None
        """
        self._worklow = None
        self._admin_console = admin_console
        self._commcell = commcell
        self._job_helper = JobManager(commcell=commcell)
        self.csdb = CommServDatabase(commcell)
        self.clean_csv = []
        self.clean_jobs = []
        if admin_console:
            self._navigator = admin_console.navigator
            self._jobs_page = Jobs(admin_console)
            self._job_details = JobDetails(admin_console)
            self.active_jobs_table_helper = RTableHelper(
                admin_console, column_specifications=jobs_columns(admin_console.props)
            )
            self.job_history_table_helper = RTableHelper(
                admin_console, column_specifications=jobs_columns(admin_console.props, True)
            )
        self.log = logger.get_log()
        self.__init_params__(options)

    def __init_params__(self, options: dict) -> None:
        """
        Initializes all test params from options given

        Args:
            options (dict)  -   dict with all optional parameters

        Returns:
            None
        """
        self.time_lag = int(options.get('ui_delay') or 30)
        self.automation_delay = int(options.get('automation_lag') or 120)
        self.size_threshold = int(options.get('size_threshold') or 500)
        self.use_csv = (str(options.get('use_csv')).lower()) != 'false'
        self.leave_suspended = (str(options.get('use_csv')).lower()) == 'true'
        self.job_filters = options.get('job_filters') or None

        self.job = None
        self.jobs = []
        job_id = options.get('job_id') or None
        job_ids = []
        if input_job_ids := options.get('job_ids'):
            job_ids += input_job_ids.split(',')
        if app_id := options.get('app_id'):
            job_id = self._get_job_from_appid(int(app_id))
        if app_ids := options.get('app_ids'):
            job_ids += [self._get_job_from_appid(int(app_id)) for app_id in app_ids.split(",")]
        if job_id:
            self.job = self._commcell.job_controller.get(int(job_id))
        if job_ids:
            self.jobs = [self._commcell.job_controller.get(int(jobid)) for jobid in job_ids]
        self.log.info(f">>> initialized jobs helper with options: {json.dumps(options, indent=4)}")
        self.log.info(f">>> total input jobs: {job_ids or job_id}")

    # =============================== SETUP UTILS ============================================
    def start_blackout_window(self):
        """
        Creates a full blackout window to block all new jobs temporarily
        """
        self.delete_blackout_window()
        self._commcell.operation_window.create_operation_window(
            'jobs_testcase_in_progress',
            start_time=0, end_time=86340,
            operations=['ALL'],
            day_of_week=['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
            do_not_submit_job=True
        )

    def delete_blackout_window(self):
        """
        Deletes the jobs blocker blackout window
        """
        try:
            self._commcell.operation_window.delete_operation_window(name=self.blackout_window)
        except:
            pass

    def _get_job_from_appid(self, app_id: int):
        """
        Gets the latest job for given app ID, that isn't aged hopefully
        """
        if not app_id:
            return None
        active_job_query = f"""select jobId from JMBkpJobInfo where applicationId={app_id}"""
        history_job_query = f"""select max(jobId) as latest from JMBkpStats where appId={app_id}"""
        self.csdb.execute(active_job_query)
        try:
            return int(self.csdb.rows[0][0])
        except:
            self.log.info(f"No active jobs for app id {app_id}")
            self.csdb.execute(history_job_query)
            try:
                return int(self.csdb.rows[0][0])
            except:
                self.log.info(f"No jobs in history either for app id {app_id}")
                self.log.info("Attempting new full backup")
                subclient = self._get_subclient_from_appid(app_id)
                backup_job = subclient.backup(
                    "Full",
                    advanced_options={
                        'impersonate_gui': True
                    },
                    common_backup_options={
                        'start_in_suspended_state': True
                    }
                )
                self.clean_jobs.append(backup_job)
                return int(backup_job.job_id)

    def _get_subclient_from_appid(self, app_id: int) -> Subclient:
        """Gets subclient SDK object from appID"""
        self.csdb.execute(
            f"select clientId, appTypeId, instance, backupSet, subclientName from APP_Application where id={app_id}")
        entity_ids = self.csdb.rows[0]
        cl = self._commcell.clients.get(
            [clname for clname, cldata in self._commcell.clients.all_clients.items()
             if int(cldata.get('id', -1)) == int(entity_ids[0])][0]
        )
        ag = cl.agents.get(
            [agn for agn, agid in cl.agents.all_agents.items() if int(agid) == int(entity_ids[1])][0])
        ist = ag.instances.get(
            [istn for istn, istid in ag.instances.all_instances.items() if int(istid) == int(entity_ids[2])][0])
        bst = ist.backupsets.get(
            [bstn for bstn, bstdat in ist.backupsets.all_backupsets.items()
             if int(bstdat.get('id', -1)) == int(entity_ids[3])][0]
        )
        return bst.subclients.get(entity_ids[4])

    def setup_multiple_jobs(self, pause: bool = True, new: bool = False) -> list[int]:
        """
        Sets up multiple jobs using job ids given

        Returns:
            pause      (bool)  -   whether to pause after job started
            new        (bool)  -   sets up new job if True
            
        Raises:
            CVTestCaseInitFailure   -   if job ids not given or multiple jobs also not present
        """
        setup_jobs = []
        if self.jobs:
            temp_store_job = self.job
            self.log.info(f">> Setting up Multiple Jobs via jobs: {self.jobs}")

            for mjob in self.jobs:
                self.log.info(f"> setting up job using: {mjob}")
                try:
                    self.job = mjob
                    setup_jobs.append(
                        self.setup_job(pause, new)
                    )
                except Exception as exp:
                    self.log.error(f">>! Could not set up from {mjob}: {str(exp)}")
                    continue
            self.job = temp_store_job

        self.active_jobs_for_test = {
            jobid: jobdata for jobid, jobdata in
            self._commcell.job_controller.active_jobs(
                lookup_time=0, job_summary='full', hide_admin_jobs=False, limit=10 ** 5).items()
            if jobdata.get('status', '').lower() == 'suspended'
        }
        self.log.info(f">> Multiple Jobs setup and ready for testing: {self.active_jobs_for_test}")
        if len(self.active_jobs_for_test) < 3:
            # TODO: SETUP RANDOM JOBS BY PROBING
            raise CVTestCaseInitFailure(
                "Not enough active suspended jobs for testing! Try providing app_ids or job_ids to setup"
            )
        return setup_jobs

    def get_job_subclient(self, job: Job) -> Subclient | None:
        """
        Gets the subclient SDK object from job

        Args:
            job (Job)   -   the Job sdk object to get subclient for

        Returns:
            subclient   (Subclient) -   the subclient sdk object that job was for
            None    -   if subclient not applicable for job
        """
        try:
            return self._commcell.clients.get(job.client_name) \
                .agents.get(job.agent_name) \
                .backupsets.get(job.backupset_name) \
                .subclients.get(job.subclient_name)
        except Exception as exp:
            self.log.error("Error while fetching job subclient")
            self.log.error(str(exp))

    def get_later_job(self, old_job: Job) -> Job | None:
        """
        Gets the latest job of same subclient of given job

        Args:
            old_job (Job)   -   the Job sdk object to get updated job for

        Returns:
            latest_job  (Job)   -   the latest job of the same subclient of given job
            None    -   if subclient not applicable

        """
        general_details = old_job.details.get('jobDetail', {}).get('generalInfo', {})
        try:
            subclient_id = int(general_details['subclient']['subclientId'])
            entity_dict = {
                "subclientId": subclient_id
            }
        except KeyError:
            self.log.error(f'got job details: {general_details}')
            self.log.error("job does not have subclient id, cannot find latest job")
            return

        later_jobs = self._commcell.job_controller.all_jobs(
            client_name=old_job.client_name,
            lookup_time=24 * 7,
            entity=entity_dict
        )
        latest_jobid = 0
        for job in later_jobs:
            if later_jobs[job]['subclient_id'] == subclient_id:
                if int(job) > latest_jobid and int(job) > int(old_job.job_id):
                    latest_jobid = int(job)
        if not latest_jobid:
            self.log.error("job does not have later jobs within 7 days, cannot find latest job.")
        else:
            self.log.info(f"found later job {latest_jobid}. reusing it.")
            return self._commcell.job_controller.get(latest_jobid)

    def random_job(self) -> Job:
        """
        Finds suitable job from history and returns job after resubmitting

        Returns:
            suitable_job    (Job)   -   job sdk object of random job test

        Raises:
            CVTestCaseInitFailure   -   if failed to find suitable job for testing
        """
        suitable_jobs = []
        jobs_history = self._commcell.job_controller.finished_jobs(lookup_time=24 * 30 * 12 * 3, limit=3000,
                                                                   job_summary='full', hide_admin_jobs=True,
                                                                   job_filter=self.job_filters)
        for job in jobs_history:
            job_data = jobs_history[job]
            if job_data.get("status", "none").lower() in ['committed', 'completed'] \
                    and job_data.get("jobElapsedTime", 0) >= self.automation_delay \
                    and job_data.get('sizeOfApplication', 0) >= self.size_threshold * (2 ** 20) \
                    and self.get_job_subclient(self._commcell.job_controller.get(job)) \
                    and job not in suitable_jobs:
                suitable_jobs.append(job)
        suitable_jobs.sort(reverse=True)
        self.log.info(f"Found suitable jobs: {suitable_jobs}")
        # using long past history to find big enough subclients/long enough jobs

        errors = []
        done_jobs = []
        for job in suitable_jobs:
            if job in done_jobs:
                continue
            done_jobs.append(job)
            suited_job = self._commcell.job_controller.get(job)
            latest_job = self.get_later_job(suited_job)
            if latest_job:
                suited_job = latest_job
                done_jobs.append(int(latest_job.job_id))
            # now we may loop through, attempting resubmits
            try:
                resubmitted_job = suited_job.resubmit()
                self.clean_jobs.append(resubmitted_job)
                return resubmitted_job
            except Exception as exp:
                error_msg = str(exp).lower()
                match = re.search(r"job\s*\[?(\d*)]?", error_msg)
                if 'another' in error_msg and match.group(1):
                    self.log.info(f"Found another job {match.group(1)} while resubmitting")
                    return self._commcell.job_controller.get(int(match.group(1)))
                else:
                    errors.append(f"Failed to resubmit job -> {suited_job.job_id}")
                    errors.append(error_msg)

        for error in errors:
            self.log.error(error)
        raise CVTestCaseInitFailure("Could not Setup random job to test on!")

    def renew_job(self, pause: bool) -> bool:
        """
        Renews job by resubmitting or starting new

        Args:
            pause   (bool)  -   tries to start in suspended state if True

        Returns:
            True    -   on successfully renewing
            False   -   if no renewing but redirected to existing running job
        """
        self.log.info(f"Resubmitting job -> {self.job.job_id}")
        try:
            self.job = self.job.resubmit(start_suspended=pause)
            self.clean_jobs.append(self.job)
            # to catch already running jobs of non-subclient jobs
        except Exception as exp:
            error_msg = str(exp).lower()
            match = re.search(r'job\s*\[?(\d*)]?', error_msg)
            if 'another' in error_msg and match.group(1):
                self.log.info(f"Found another job {match.group(1)} while resubmitting")
                self.job = self._commcell.job_controller.get(int(match.group(1)))
                return False
                # recurse with this new job id
            else:
                self.log.error(f"Cannot resubmit job because -> {error_msg}")
                self.log.info("Attempting subclient backup of same job")
                job_subclient = self.get_job_subclient(self.job)
                if not job_subclient:
                    self.log.error("Cannot get job subclient. Nothing more to try")
                    raise CVTestCaseInitFailure("Failed to setup job")
                else:
                    self.job = job_subclient.backup(
                        "Full",
                        advanced_options={
                            'impersonate_gui': True
                        },
                        common_backup_options={
                            'start_in_suspended_state': pause
                        }
                    )
                    self.clean_jobs.append(self.job)
                    return True

    def setup_job(self, pause: bool = None, new: bool = False) -> int:
        """
        Sets up job to test on by reusing from suspended jobs or by resubmitting completed job

        Args:
            pause      (bool)  -   keeps in suspended state if True
            new        (bool)  -   sets up new job if True

        Returns:
            job_id     (int)   -   id of the job to test on

        Raises:
            CVTestCaseInitFailure   -   if unable to setup job
        """
        if self.job is None:
            self.job = self.random_job()

        self.log.info(f"Reusing existing job {self.job.job_id}")
        if self.job.is_finished:
            latest_job = self.get_later_job(self.job)
            if latest_job:
                self.job = latest_job
                return self.setup_job(pause, new)
                # recurse with this new job id
            if not self.renew_job(pause):
                # self.job is only pointed to already running job, need to recurse it again
                return self.setup_job(pause, new)
            else:
                # if renewing happened, job is already newly started and paused, no need to recurse
                self.log.info(f"Job {self.job.job_id} is ready for testing")
                return self.job.job_id

        elif self.job.summary.get('percentComplete', 0) >= 50 or new:
            self.log.info(f"Killing and resubmitting as job "
                          f"{'must be new' if new else 'has progressed too far'}")
            self.job.kill()
            self._job_helper.job = self.job
            self._job_helper.wait_for_job_progress(99)
            self.renew_job(pause)

        if pause:
            self.job.pause(True)
        elif pause is not None and self.job.status.lower() == 'suspended':
            self.job.resume(True)

        self.log.info(f"Job {self.job.job_id} is ready for testing")
        return self.job.job_id

    def clean_up(self) -> None:
        """
        Method to clean up any changes made by this helper
        """
        self.log.info("Deleting parsed CSVs")
        for csv_file in self.clean_csv:
            os.remove(csv_file)
        self.log.info("CSV cleaned, cleaning Jobs")
        if not self.clean_jobs:
            self.log.info("No jobs started, No cleanup required!")
            return
        for job in self.clean_jobs:
            if self.leave_suspended and job.status.lower() == 'suspended':
                self.log.info(f"Job {job.job_id} left suspended for debugging/reuse purpose")
                continue
            if not job.is_finished:
                try:
                    job.kill()
                    self.log.info(f"Job {job.job_id} kill initiated...")
                except Exception as exp:
                    self.log.info(f'Job {job.job_id} failed cleanup due to {str(exp)}')
            else:
                self.log.info(f"Job {job.job_id} completed, not cleaning up..")

    # =============================== VALIDATION UTILS =======================================
    @staticmethod
    def group_api_jobs_by_column(api_jobs: dict, column: str) -> dict:
        """
        Sorts the api jobs summary by UI column and returns sorted dict (Ascending)

        Args:
            api_jobs    (dict)      -   the api jobs summary json
            column  (str)           -   label prop name of column in UI to group using

        Returns:
            grouped_api_jobs (OrderedDict)   -   dictionary with key as that column value and value as list of job ids
        """
        match_criteria = jobs_columns()[column]['match_key']
        grouped_jobs = {}
        for job_id, job_data in api_jobs.items():
            job_attrib_value = match_criteria(job_data)
            if job_attrib_value and str(job_attrib_value).lower() not in ["not applicable", "n/a", "null", "nil",
                                                                          "none"]:
                if isinstance(job_attrib_value, list):
                    for each_attrib in job_attrib_value:
                        grouped_jobs[each_attrib] = grouped_jobs.get(each_attrib, []) + [int(job_id)]
                else:
                    grouped_jobs[job_attrib_value] = grouped_jobs.get(job_attrib_value, []) + [int(job_id)]
        return grouped_jobs

    # =============================== VALIDATION SETUPS ================================

    def setup_active_jobs(self, sort: bool = True, view: str = None) -> None:
        """
        Navigates to active jobs page, if not already there

        Args:
            sort    (bool)  -   sorts the job ID column if True
            view    (str)   -   the view to select
        """
        if "/activeJobs" not in self._admin_console.current_url():
            self._navigator.navigate_to_jobs()
            if sort:
                self._jobs_page.sort_by_column(JOB_ID_LABEL, ascending=False, data=False)
                # stop rows re-arranging during operation
        if view:
            self._jobs_page.select_view(view)

    def setup_jobs_history(self, view: str = None) -> None:
        """
        Navigates to jobs history, if not already there

        Args:
            view    (str)   -   the view to select
        """
        if "/jobs" not in self._admin_console.current_url():
            self.setup_active_jobs(sort=False)
            self._jobs_page.access_job_history()
        if view:
            self._jobs_page.select_view(view)

    # @test_step
    # def validate_jh_views(self, strict: bool = True, admin_jobs: bool = True) -> None:
    #     """
    #     Selects each default view and verifies the jobs visible are correct
    #
    #     Args:
    #         strict  (bool)      -   Ensures same number of jobs are shown API and UI
    #                                 False only ensures UI does not show incorrect jobs
    #         admin_jobs  (bool)  -   Tests using show admin jobs also if True
    #
    #     Raises:
    #         CVTestStepFailure   -   if failed to validate any system created view
    #     """
    #
    #     def is_failed_job(job_data: dict) -> bool:
    #         """
    #         util for determining failed jobs
    #         """
    #         statuses = JobsHelper.str_ui_props(job_data)['Status']
    #         return ("Completed w/ one or more errors" in statuses
    #                 or "Failed to Start" in statuses)
    #
    #     self._jobs_page.show_admin_jobs(admin_jobs)
    #
    #     view_lookup_times = {
    #         "Last 24 hours": 24,
    #         "Failed in last 24 hours": 24,
    #         "Yesterday": 48,
    #         "Last week": 24 * 7,
    #         "Last month": 24 * 30,
    #         "Last 3 months": 24 * 30 * 3,
    #         "Last 12 months": 24 * 30 * 12
    #     }
    #     errors = []
    #     for view in view_lookup_times:
    #         self._jobs_page.select_view(view)
    #
    #         expected_jobs = self._commcell.job_controller.finished_jobs(
    #             lookup_time=view_lookup_times[view], job_summary='full', limit=10 ** 5,
    #             hide_admin_jobs=not admin_jobs
    #         )
    #         if view == 'Yesterday':
    #             expected_jobs = {
    #                 job: data for job, data in expected_jobs.items()
    #                 if job not in self._commcell.job_controller.finished_jobs(lookup_time=24, limit=10 ** 5)
    #             }
    #
    #         if "Failed" in view:
    #             expected_jobs = {
    #                 job: data for job, data in expected_jobs.items()
    #                 if is_failed_job(data)
    #             }
    #
    #         visible_jobs = self.jobs_table_from_csv()
    #
    #         validation_errors = JobsHelper.compare_jobs_lists(visible_jobs, expected_jobs)
    #         errors.extend(validation_errors)
    #
    #         if strict and len(visible_jobs) != len(expected_jobs):
    #             errors.append(f"View {view} Failed: UI_count={len(visible_jobs)} but API count={len(expected_jobs)}")
    #
    #         if not validation_errors:
    #             self.log.info("View %s : Verified", view)
    #         else:
    #             self.log.error(f"View {view} failed")
    #
    #     self._jobs_page.select_view()
    #
    #     if errors:
    #         for error in errors:
    #             self.log.error(error)
    #         raise CVTestStepFailure(f"Jobs History default view failed to validate")
    #     else:
    #         self.log.info("Jobs History default view validated successfully!")

    # ----------- single job validations -------------

    def validate_api_ui_sync(self, job_id: Union[int, str], status: list, ui_delay: int = None, result: dict = None):
        if not ui_delay:
            ui_delay = self.time_lag
        jm = JobManager(_job=int(job_id), commcell=self._commcell)
        try:
            jm.wait_for_state(status, retry_interval=2)
            self._jobs_page.wait_jobs_status([job_id], [jm.job.status.title()], ui_delay)
        except Exception as exp:
            if not result:
                raise exp
            else:
                self.log.error(f"Failure while verifying for job->{job_id}: {exp}")
                result[job_id] = str(exp)
                return
        self.log.info(f"{status[0]} job verified from active jobs for job->{job_id}")

    @test_step
    def run_and_validate(self, ui_delay: int = None, reload: bool = False) -> int:
        """
        Runs a backup job and validates if it appears in table

        Args:
            ui_delay (int)   -   acceptable delay between time of job initiation and appearance in table
            reload  (bool)   -   reloads jobs grid before waiting for job if True

        Returns:
            job_id  (int)   -   Id of job started
        """
        if not ui_delay:
            ui_delay = self.time_lag
        self.setup_active_jobs()
        self._jobs_page.select_view('All')
        job_id = self.setup_job(pause=False, new=True)
        if reload:
            self._jobs_page.reload_jobs()
        self._jobs_page.wait_for_jobs([job_id], ui_delay)
        self.log.info("Jobs updation validated")
        return job_id

    @test_step
    def suspend_and_validate(self, job_id: Union[int, str] = None, ui_delay: int = None) -> None:
        """
        Suspends a backup job and validates if it's status updates in table

        Args:
            job_id  (int/str)   -   id of job to suspend and validate
            ui_delay (int)   -   acceptable delay between job state change and update in status column
        """
        if not job_id:
            job_id = self.setup_job(pause=False)
        self._jobs_page.suspend_job(str(job_id), "Indefinitely")
        self.validate_api_ui_sync(job_id, ["suspended", "committed", "completed"], ui_delay)

    @test_step
    def resume_and_validate(self, job_id: Union[int, str] = None, ui_delay: int = None) -> None:
        """
        Resumes a backup job and validates if it's status updates in table

        Args:
            job_id  (int/str)   -   id of job to suspend and validate
            ui_delay (int)   -   acceptable delay between time of job initiation and appearance in table
        """
        if not job_id:
            job_id = self.setup_job(pause=True)
        self._jobs_page.resume_job(str(job_id))
        self.validate_api_ui_sync(job_id, ["queued", "waiting", "running", "completed"], ui_delay)

    @test_step
    def kill_and_validate(self, job_id: Union[int, str] = None, ui_delay: int = None) -> None:
        """
        Kills a backup job and validates if it's status updates in table

        Args:
            job_id  (int/str)   -   id of job to suspend and validate
            ui_delay (int)   -   acceptable delay between time of job initiation and appearance in table
        """
        if not job_id:
            job_id = self.setup_job(pause=True)
        self._jobs_page.kill_job(str(job_id))
        self.validate_api_ui_sync(job_id, ["killed", "committed", "completed"], ui_delay)

    @test_step
    def resubmit_and_validate(self, job_id: Union[int, str] = None, ui_delay: int = None) -> None:
        """
        Resubmits a backup job and validates if it updates in table

        Args:
            job_id  (int/str)   -   id of completed job to resubmit and validate
            ui_delay    (int)   -   acceptable delay between resubmit and job appearance
        """
        active_jobs = "activeJobs" in self._admin_console.current_url()
        if not ui_delay:
            ui_delay = self.time_lag
        if not job_id:
            job_id = self.setup_job()
            self.job.kill(True)
            if not active_jobs:
                self.setup_jobs_history()

        new_job = self._jobs_page.resubmit_job(str(job_id))
        # TODO: add validation for case when same client job is already running
        self._job_helper.job = self._commcell.job_controller.get(int(new_job))
        self._job_helper.wait_for_state(["queued", "waiting", "running", "completed"], retry_interval=2)

        if not active_jobs:
            self.setup_active_jobs()
        self._jobs_page.wait_for_jobs([job_id], ui_delay)
        self.log.info(f"Resubmit job verified for job -> {job_id} from "
                      f"{'active jobs' if active_jobs else 'job history'}")
        try:
            self._job_helper.job.kill(True)
            self.log.info("Job killed successfully")
        except:
            self.log.error("Error during kill resubmitted job")

    def validate_redirection(self, action: Callable, **expectations):
        """
        Validates redirection after performing an action

        Args:
            action  (Callable)      -   a function to call to trigger the redirection
            expectations:
                wait_time   (int)           -   wait time expected for redirection
                new_tabs    (int)           -   number of new tabs expected for redirection
                url_patterns (list)         -   list of url regex matches to check for each new tab or same tab
                validation (Callable)       -   a validation function to call post-redirection
                wait_for_load   (bool)      -   if True, waits for completion before checking urls and validations
        """
        new_tabs = expectations.get('new_tabs') or 0
        url_regexes = expectations.get('url_patterns')[:] or []
        main_handle = self._admin_console.driver.current_window_handle
        initial_handles = self._admin_console.driver.window_handles
        self._admin_console.browser.wait_redirection(action, expectations.get('wait_time', 5), new_tabs)
        new_handles = [
            handle for handle in self._admin_console.driver.window_handles
            if handle not in initial_handles
        ]
        if not new_handles:
            new_handles = [main_handle]
        # TODO: HANDLE REDIRECT SPECIFICATION BETTER
        errors = []
        for handle in new_handles:
            self._admin_console.driver.switch_to.window(handle)
            if expectations.get('wait_for_load'):
                self._admin_console.wait_for_completion()
            opened_url = self._admin_console.current_url()

            if expectations.get('url_patterns'):
                matched_regex = [regex for regex in url_regexes if re.search(regex, opened_url)]
                if not matched_regex:
                    errors.append(f'For tab with url: {opened_url}, failed to match regex from {url_regexes}')
                    if handle != main_handle:
                        self._admin_console.driver.close()
                    break
                self.log.info(f'matched url: {opened_url} with regex: {matched_regex[0]}')
                url_regexes.remove(matched_regex[0])

            if validate := expectations.get('validation'):
                try:
                    validate()
                except Exception as exp:
                    errors.append(f'For tab with url: {opened_url}, validation failed, got exception: {exp}')
                    errors.append(traceback.format_exc())
                    if handle != main_handle:
                        self._admin_console.driver.close()
                    break

            self.log.info(f'validation passed for tab with url: {opened_url}')
            if handle != main_handle:
                self._admin_console.driver.close()

        self._admin_console.driver.switch_to.window(main_handle)
        return errors

    @test_step
    def validate_redirects(self, job_id: Union[int, str] = None, exclusions: str = 'all') -> None:
        """
        Validates all the redirect actions such as view logs, job details etc

        Args:
            job_id  (str/int)   -   the job to test redirects for
            exclusions  (str)   -   redirects to ignore on failure (ex. its greyed out)
                                    comma seperated str with redirect names (see JobsHelper.redirects)
                                    'all' will never report failure on greyed out redirects

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        active = 'active' in self._admin_console.current_url()
        actions = {
            'Job link': self._jobs_page.access_job,
            'View logs': self._jobs_page.view_logs,
            'Send logs': self._jobs_page.send_logs,
            'View job details': self._jobs_page.view_job_details,
        }
        if not active:
            actions |= {
                'Restore': self._jobs_page.job_restore,
                'View failed items': self._jobs_page.view_failed_items
            }
        new_tabs = {
            'View logs': 1
        }
        if job_id:
            job_id = str(job_id)
        else:
            job_id = self._jobs_page.get_job_ids()[0]

        errors = []
        for action in actions:
            self.log.info(f"verifying {action} on job {job_id}")
            redirect_href = JobsHelper.redirects[action]
            if redirect_href:
                redirect_href = redirect_href % job_id
            try:
                errors += self.validate_redirection(
                    lambda: actions[action](job_id),
                    wait_time=8,
                    new_tabs=new_tabs.get(action, 0),
                    url_patterns=[redirect_href],
                    wait_for_load=True
                )
                self.log.info(f"{action} redirect verified!")

                if active:
                    self.setup_active_jobs(sort=False)
                else:
                    self.setup_jobs_history()
                self._admin_console.wait_for_completion()

            except CVWebAutomationException as exp:
                if "item is disabled" in str(exp).lower():
                    if action not in exclusions and 'all' not in exclusions:
                        raise CVTestStepFailure(f"Redirect {action} is disabled!")
                    else:
                        self.log.error(f"Redirect {action} is greyed out, skipping it")
                        self._admin_console.click_menu_backdrop()  # collapse menu
                        continue
                else:
                    raise exp

        if not errors:
            self.log.info(f"All Redirects validated successfully")
        else:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure("Redirects validation failed")

    # ----------- multiple job validations -------------

    @test_step
    def multi_run_and_validate(self, ui_delay: int = None, reload: bool = False):
        """tests all jobs"""
        if not ui_delay:
            ui_delay = self.time_lag
        self.setup_active_jobs()
        self._jobs_page.select_view('All')
        job_ids = self.setup_multiple_jobs()
        if reload:
            self._jobs_page.reload_jobs()
        self._jobs_page.wait_for_jobs([job_ids], ui_delay)
        self.log.info("Jobs Table Updation validated for Multiple Jobs")
        return job_ids

    def multi_validate_api_ui_sync(self, exec_fn: Callable, job_ids: list, status: list, ui_delay: int = None) -> None:
        """
        Validates if given jobs status updates in table

        Args:
            exec_fn (function)  -  the function object to execute, just before waiting for job status
            job_ids  (list)   -   ids of job expected to show the particular status
            status   (str)    -   expected status from those job ids
            ui_delay (int)   -   acceptable delay between job state change and update in status column
        """
        self.log.info(f">>> Validating status={status} for jobs={job_ids} after {exec_fn}")
        results = {}
        validator_threads = [
            Thread(target=functools.partial(self.validate_api_ui_sync, job_id, status, ui_delay, results))
            for job_id in job_ids
        ]
        exec_fn()
        for validator in validator_threads:
            validator.start()
        for validator in validator_threads:
            validator.join()
        if results:
            for job_id, tcfail_reason in results.items():
                self.log.error(f"{job_id} Failed to Validate:->{tcfail_reason}")
            raise CVTestStepFailure(f"Multi Job Validation Failed for Jobs: {results.keys()}!")
        self.log.info(">>> Status matched for those job ids, now verifying others are unaffected")
        # self.validate_jobs_table(exclude_jobs=job_ids)

    def get_best_criteria_test(self, criteria):
        """
        Gets or processes criteria and figures best way to test it
        """
        if process_text(criteria) in MultiJobPanel.SelectionType.ALL.value.lower():
            self.log.info('Preparing multi job validation for criteria ALL JOBS')
            expected_jobs = [int(job) for job in self.active_jobs_for_test]
            return expected_jobs, {
                'selection': MultiJobPanel.SelectionType.ALL
            }
        elif process_text(criteria) in MultiJobPanel.SelectionType.JOB_TYPE.value.lower():
            self.log.info('Preparing multi job validation for criteria PARTICULAR JOB TYPE')
            available_job_types = JobsHelper.group_api_jobs_by_column(self.active_jobs_for_test, 'Operation')
            self.log.info(f'got available job types: {available_job_types}')
            remaining_jobs = (set(self.active_jobs_for_test.keys())
                              - set(itertools.chain.from_iterable(available_job_types.values())))
            if (not remaining_jobs) and len(available_job_types) < 2:
                raise CVTestCaseInitFailure(f"Need at least two different Job Types to properly validate")
            client_name = min(available_job_types, key=lambda k: len(available_job_types[k]))
            self.log.info(f'job type: {client_name} will be used')
            return available_job_types[client_name], {
                'selection': MultiJobPanel.SelectionType.JOB_TYPE,
                'entity_name': client_name
            }
        elif process_text(criteria) in MultiJobPanel.SelectionType.SELECTED.value.lower():
            self.log.info('Preparing multi job validation for criteria SELECTED JOBS')
            random_jobs = list(random.sample(list(self.active_jobs_for_test), 2))
            self.log.info(f'Using 2 random jobs for selection: {random_jobs}')
            return random_jobs, {
                'selection': MultiJobPanel.SelectionType.SELECTED,
                'selected_jobs': random_jobs
            }
        elif process_text(criteria) in MultiJobPanel.SelectionType.CLIENT.value.lower():
            self.log.info('Preparing multi job validation for criteria CLIENT JOBS')
            available_clients_jobs = JobsHelper.group_api_jobs_by_column(self.active_jobs_for_test, 'Server')
            self.log.info(f'got available clients: {available_clients_jobs}')
            remaining_jobs = (set(self.active_jobs_for_test.keys())
                              - set(itertools.chain.from_iterable(available_clients_jobs.values())))
            if (not remaining_jobs) and len(available_clients_jobs) < 2:
                raise CVTestCaseInitFailure(f"Need at least two different Client Jobs to properly validate")
            client_name = min(available_clients_jobs, key=lambda k: len(available_clients_jobs[k]))
            self.log.info(f'Client: {client_name} will be used')
            return available_clients_jobs[client_name], {
                'selection': MultiJobPanel.SelectionType.CLIENT,
                'entity_name': client_name
            }
        elif process_text(criteria) in MultiJobPanel.SelectionType.AGENT_ONLY.value.lower():
            self.log.info('Preparing multi job validation for criteria AGENT JOBS')
            available_clients_jobs = JobsHelper.group_api_jobs_by_column(self.active_jobs_for_test, 'Server')
            self.log.info(f'got available clients: {available_clients_jobs}')
            for client_name in available_clients_jobs:
                subset_jobs = {
                    jobid: jobdata for jobid, jobdata in self.active_jobs_for_test.items()
                    if jobid in available_clients_jobs[client_name]
                }
                available_agents = JobsHelper.group_api_jobs_by_column(subset_jobs, 'Agent type')
                self.log.info(f'Agents for Client {client_name}: {available_agents}')
                null_agent_jobs = (set(subset_jobs.keys())
                                   - set(itertools.chain.from_iterable(available_agents.values())))
                if (not null_agent_jobs) and len(available_agents) < 2:
                    self.log.error(f"Need at least two different Agent Jobs (under same client) to properly validate")
                else:
                    agent_for_use = min(available_agents, key=lambda k: len(available_agents[k]))
                    self.log.info(f'Client: {client_name} and Agent: {agent_for_use} will be used')
                    return available_agents[agent_for_use], {
                        'selection': MultiJobPanel.SelectionType.AGENT_ONLY,
                        'entity_name': client_name,
                        'agent_name': agent_for_use
                    }
            raise CVTestCaseInitFailure(f"Need jobs with atleast 2 agents and common client to properly validate")
        elif process_text(criteria) in MultiJobPanel.SelectionType.CLIENT_GROUP.value.lower():
            available_clgroup_jobs = JobsHelper.group_api_jobs_by_column(self.active_jobs_for_test, 'Server group')
            self.log.info(f"Got cl group jobs: {available_clgroup_jobs}")
            for client_group in available_clgroup_jobs:
                remaining_jobs = (set(self.active_jobs_for_test.keys())
                                  - set(available_clgroup_jobs[client_group]))
                if not remaining_jobs:
                    self.log.error(
                        f"Cannot use {client_group}'s jobs as no other jobs would remain for inaction validation")
                else:
                    self.log.info(f"Will use {client_group}'s jobs for test")
                    return available_clgroup_jobs[client_group], {
                        'selection': MultiJobPanel.SelectionType.CLIENT_GROUP,
                        'entity_name': client_group
                    }
            raise CVTestCaseInitFailure(f"Need other jobs than the expected ones to validate they are not affected")

    @test_step
    def multi_actions_validate(self, criteria: str, ui_delay: int = None) -> None:
        """
        Resumes, Suspends, Kills to validate Multi Job Control for given Criteria
        """
        if not ui_delay:
            ui_delay = self.time_lag

        try:
            expected_jobs, exec_params = self.get_best_criteria_test(criteria)
        except CVTestCaseInitFailure:
            self.setup_multiple_jobs()
            expected_jobs, exec_params = self.get_best_criteria_test(criteria)

        multi_job_resumer = lambda: self._jobs_page.multi_job_control(operation="resume", **exec_params)
        multi_job_suspender = lambda: self._jobs_page.multi_job_control(operation="suspend", **exec_params)
        multi_job_killer = lambda: self._jobs_page.multi_job_control(operation="kill", **exec_params)

        # self.validate_jobs_table()

        self.multi_validate_api_ui_sync(
            multi_job_resumer, expected_jobs, ["running", "waiting", "queued", "pending", "completed"], ui_delay
        )

        expected_jobs = self.setup_multiple_jobs(expected_jobs, False)
        self._jobs_page.wait_for_jobs([expected_jobs], ui_delay)
        self.multi_validate_api_ui_sync(
            multi_job_suspender, expected_jobs, ["suspended", "committed", "completed"], ui_delay
        )

        expected_jobs = self.setup_multiple_jobs(expected_jobs)
        self._jobs_page.wait_for_jobs([expected_jobs], ui_delay)
        self.multi_validate_api_ui_sync(
            multi_job_killer, expected_jobs, ["killed", "committed", "completed"], ui_delay
        )


class JobDetailsHelper(JobsHelper):
    """
    Helper class for job details page tests
    """

    test_step = TestStep()
    # =============================== JOB DETAILS VALIDATION UTILS ================================

    str_jd_props = lambda api_data: {
        'Type': [api_data.get("operationType")],
        'Backup type': [api_data.get("backupType")],
        'Status': [api_data.get("state")],
        'Current phase': [api_data.get("currentPhase")],
        'Encryption enabled': [api_data.get("encrypted")],
        'System state': [api_data.get("systemState")],
        'Agent': [api_data.get("subclient", {}).get("appName")],
        'Media agent': [api_data.get("mediaAgent", {}).get("mediaAgentName")],
        'Backup set': [api_data.get("subclient", {}).get("backupsetName")],
        'Source client computer': [
            api_data.get("subclient", {}).get("clientName"),
            api_data.get("subclient", {}).get("displayName")
        ],
        'Instance': [api_data.get("subclient", {}).get("instanceName")],
        'Subclient': [api_data.get("subclient", {}).get("subclientName")],
        'No of objects backed up': [
            api_data.get("numOfObjects"),
            api_data.get("numOfFilesTransferred")
        ],
        'No of objects qualified for backup': [api_data.get("totalNumOfFiles")],
        'Failures': [api_data.get("failures")]
    }
    time_jd_props = lambda api_data: {
        'Start time': [int(api_data.get("startTime", 0))],
        'End time': [int(api_data.get("endTime", 0))],
        'Last update time': [int(api_data.get("lastJobUpdateTime", 0))]
    }
    size_jd_props = lambda api_data: {
        'Data transferred on network': [api_data.get("dataXferedNetwork", 0)],  # in Bytes
        'Size of application': [api_data.get("sizeOfApplication", 0)],  # in Bytes
        'Estimated media size': [api_data.get("estMediaSize", 0)],  # in Bytes
        'Average throughput': [api_data.get("averageThroughput", 0)],  # in GB/hr
        'Current throughput': [api_data.get("currentAttemptThroughput", 0)]  # in GB/hr
    }
    misc_jd_props = lambda api_data: {
        'Savings percentage': [int(api_data.get("savingsPercent", 0))],  # without %
        'Progress': [int(api_data.get("percentComplete", 0))],  # without %
        'Job started by': [api_data.get("jobStartedBy"), api_data.get("jobStartedFrom")],
        'Elapsed time': [
            int(api_data.get("elapsedTime", 0)),
            int(api_data.get("lastJobUpdateTime", 0)) - int(api_data.get("startTime", 0))
        ],
        'Duration': [int(api_data.get("endTime", 0)) - int(api_data.get("startTime", 0))],
        'Scanned objects': [api_data.get("scannedFolders", 0), api_data.get("scannedFiles", 0)],
    }
    all_jd_props = lambda api_job: {
        **JobDetailsHelper.str_jd_props(api_job),
        **JobDetailsHelper.time_jd_props(api_job),
        **JobDetailsHelper.size_jd_props(api_job),
        **JobDetailsHelper.misc_jd_props(api_job)
    }

    @staticmethod
    def compare_job_overview_data(ui_job: dict, api_job: dict) -> list[str]:
        """
        Compares the job data points in panel with same job's data from API

        Args:
            ui_job  (dict)  -   the job's data points from all panels
            api_job (dict)  -   the json returned by API call for job summary

        Returns:
            errors  (list)   -   list with info on what data points mismatched
        """
        str_data_map = JobDetailsHelper.str_jd_props(api_job)
        time_data_map = JobDetailsHelper.time_jd_props(api_job)
        size_data_map = JobDetailsHelper.size_jd_props(api_job)
        misc_data_map = JobDetailsHelper.misc_jd_props(api_job)

        def validate_job_point(point_name: str) -> str:
            """
            Util to validate single data point and get error string if any
            """
            ui_value = process_text(ui_job[point_name])
            api_values = ['column data not assigned from API']

            # Handing null/empty data points
            nulls = ['notapplicable', 'nil', 'null', 'notavailable', 'n/a', 'None', 'none', '0']
            if ui_value in nulls:
                api_values = JobDetailsHelper.all_jd_props(api_job)[point_name]
                for api_value in api_values:
                    if process_text(api_value) in nulls:
                        return ""

            if point_name in str_data_map:
                api_values = [process_text(value) for value in str_data_map[point_name] if value is not None]

            elif point_name in time_data_map:
                api_values = [float(value) for value in time_data_map[point_name] if value is not None]
                if ui_value:
                    ui_value = parse(ui_job[point_name]).timestamp()
                else:
                    ui_value = 0.0
                if not api_values:
                    api_values = [0.0]

            elif point_name in size_data_map:
                divisor = 1
                ui_size = ui_job[point_name]
                if 'throughput' in point_name:
                    ui_size = ui_size.rstrip('/hr')
                    size_data_map[point_name][0] = float(size_data_map[point_name][0]) * 2 ** 30
                ui_value = parse_size(ui_size)
                if 'kb' in ui_size.lower():
                    divisor = 2 ** 10
                elif 'mb' in ui_size.lower():
                    divisor = 2 ** 20
                elif 'gb' in ui_size.lower():
                    divisor = 2 ** 30
                elif 'tb' in ui_size.lower():
                    divisor = 2 ** 40
                ui_value = round(ui_value / divisor, 2)
                api_values = [round(int(api_value) / divisor, 2) for api_value in size_data_map[point_name]]

            elif point_name in misc_data_map:
                if point_name in ['Elapsed time', 'Duration']:
                    ui_value = parse_duration(ui_job[point_name])
                    api_values = [int(misc_data_map[point_name][0])]

                elif point_name in ['Savings percentage', 'Progress']:
                    api_values = [str(misc_data_map[point_name][0]) + "%"]

                elif point_name in ['Job started by', 'Scanned objects']:
                    for api_val in misc_data_map[point_name]:
                        if str(api_val) and str(api_val).lower() not in ui_value:
                            return f"failed to match {point_name} - " \
                                   f"UI: {ui_job[point_name]} -> {ui_value} " \
                                   f"| API: {api_val} <- {misc_data_map[point_name]}"
                    return ""

            # Ignore if we don't know to validate the data point
            else:
                return ""

            # Final check
            if ui_value not in api_values:
                return f"failed to match {point_name} - UI: {ui_job[point_name]} -> {ui_value} | API: {api_values}"

        errors = []
        for data_point in ui_job:
            try:
                error_str = validate_job_point(data_point)
            except Exception as exp:
                print(f"couldnt validate {data_point}")
                raise exp
            if error_str:
                errors.append(error_str)
        return errors

    # ===================================== JOB DETAILS TESTS ========================================

    @test_step
    def setup_job_details(self, job_id: Union[int, str] = None) -> None:
        """
        Sets up the job details page for given job

        Args:
            job_id  (int/str)   -   id of job
        """
        if not job_id:
            job_id = self.job.job_id
        if self.redirects['Job link'] % str(job_id) not in self._admin_console.current_url():
            if self._commcell.job_controller.get(job_id).is_finished:
                self.setup_jobs_history()
            else:
                self.setup_active_jobs(sort=False)
                self._jobs_page.wait_for_jobs([job_id], self.time_lag)
            self._jobs_page.access_job(str(job_id), True)
            self._admin_console.wait_for_completion()

    @test_step
    def validate_tabs(self, exclusions: str = '') -> None:
        """
        Validates all tabs in job details 'overview','events',etc

        Args:
            exclusions  (str)   -   tabs to ignore if missing elements
                                    overview/attempts/events...
                                    redirects/retention/all
                                    however, any incorrect data will be caught
        """
        tabs_validations = {
            'overview': self.validate_overview,
            # 'attempts': self.validate_attempts,
            # 'events': self.validate_events,
            # 'retention': self.validate_retention,
            'redirects': self.validate_jd_redirects
        }
        for tab in tabs_validations:
            if tab in exclusions:
                self.log.info(f"Skipping test for -> {tab}")
                continue
            tabs_validations[tab]()
        self.log.info("All Job Details Tabs/Redirects Validated")

    @test_step
    def validate_overview(self, exclusions: str = 'all') -> None:
        """
        Validates the panels in overview tab of job details

        Args:
            exclusions  (str)   -   panels to exclude failure if missing
                                    'all' will not enforce visibility of any panel
                                    but will still fail on incorrect details

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self._job_details.access_overview()
        job_id = int(self._admin_console.current_url().split('/')[-1])

        flat_api = {}
        flat_data = {}

        api_job = self._commcell.job_controller.get(job_id).details['jobDetail']
        if 'attemptsInfo' in api_job:
            del api_job['attemptsInfo']
        else:
            self.log.error(f"no attempts Info found in details. only -> {list(api_job.keys())}")
        for info_type in api_job:
            flat_api.update(api_job[info_type])

        panels_data = {
            'General': self._job_details.get_general_details(),
            'Progress': self._job_details.get_progress_details(),
            'Associations': self._job_details.get_association_details(),
            'Item status': self._job_details.get_item_status()
            # TODO: add error summary panel validation
        }
        for panel in panels_data:
            if not panels_data[panel]:
                if panel in exclusions or 'all' in exclusions:
                    self.log.error(f"panel {panel} missing, skipping")
                else:
                    raise CVTestStepFailure(f"panel {panel} is missing!")
            else:
                flat_data.update(panels_data[panel])

        errors = JobDetailsHelper.compare_job_overview_data(flat_data, flat_api)
        if errors:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure("Job Details Overview validation Failed!")
        else:
            self.log.info("Job Details Overview validated!")

    # @test_step
    # def validate_attempts(self, exclusions: str = '') -> None:
    #     """
    #     Validates job attempts table in job details page
    #
    #     Args:
    #         exclusions  (str)   -   comma seperated list of column names to exclude from validation
    #
    #     Raises:
    #         CVTestStepFailure   -   if failed to validate
    #     """
    #     job_id = int(self._admin_console.current_url().split('/')[-1])
    #     self._job_details.access_attempts()
    #     count, ui_data = self.collect_jd_table_data(exclusions)
    #
    #     api_data = self._commcell.job_controller.get(job_id).attempts
    #     errors = JobDetailsHelper.compare_attempts_lists(ui_data, api_data)
    #     if count != len(api_data):
    #         errors.append("Attempts UI count does not match API's count")
    #     if errors:
    #         for error in errors:
    #             self.log.error(error)
    #         raise CVTestStepFailure("Attempts validation failed!")
    #     else:
    #         self.log.info("Attempts validated successfully!")
    #
    # @test_step
    # def validate_events(self, exclusions: str = '') -> None:
    #     """
    #     Validates job events table in job details page
    #
    #     Args:
    #         exclusions  (str)   -   comma seperated list of column names to exclude from validation
    #
    #     Raises:
    #         CVTestStepFailure   -   if failed to validate
    #     """
    #     job_id = self._admin_console.current_url().split('/')[-1]
    #     self._job_details.access_events()
    #     count, ui_data = self.collect_jd_table_data(exclusions, key='Event ID')
    #     api_data = self._commcell.event_viewer.events({
    #         'jobId': job_id
    #     }, True)
    #     errors = JobDetailsHelper.compare_events_lists(ui_data, api_data)
    #     if errors:
    #         for error in errors:
    #             self.log.error(error)
    #         raise CVTestStepFailure("Events validation failed!")
    #     else:
    #         self.log.info("Events validated successfully!")
    #
    # @test_step
    # def validate_retention(self) -> None:
    #     """
    #     Validates job retention table in job details page
    #
    #     Raises:
    #         CVTestStepFailure   -   if failed to validate
    #     """
    #     job_id = int(self._admin_console.current_url().split('/')[-1])
    #     self._job_details.access_retention()
    #     count, ui_data = self.collect_jd_table_data()
    #     api_data = self._commcell.job_controller.get(job_id).advanced_job_details(
    #         AdvancedJobDetailType.RETENTION_INFO
    #     )
    #     api_data = [
    #         copy_data for sp_data in
    #         api_data.get('jobRetention', {}).get('storagePolicyRetentionInfoList', [])
    #         for copy_data in sp_data.get('copyRetentionInfoList', [])
    #     ]
    #     api_count = len(api_data)
    #     errors = JobDetailsHelper.compare_retention_lists(ui_data, api_data)
    #     if api_count != count:
    #         errors.append(f"Retention rows count mismatch from API! UI: {count} vs API: {api_count}")
    #     if errors:
    #         for error in errors:
    #             self.log.error(error)
    #         raise CVTestStepFailure("Retention validation failed!")
    #     else:
    #         self.log.info("Job Retention data validated successfully!")

    @test_step
    def validate_jd_redirects(self, exclusions: str = 'all') -> None:
        """
        Validates all the redirect actions such as view logs, job details etc

        Args:
            exclusions  (str)   -   redirects to ignore on failure (ex. its greyed out)
                                    comma seperated str with redirect names (see JobsHelper.redirects)
                                    'all' will never report failure on greyed out redirects

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        job_id = self._admin_console.current_url().split('/')[-1]

        actions = {
            # 'Restore': self._job_details.restore,
            'View logs': self._job_details.view_logs,
            # 'View failed items': self._job_details.view_failed_items,
            'Send logs': self._job_details.send_logs,
        }
        new_tabs = {
            'View logs': True
        }

        errors = []
        for action in actions:
            self.log.info(f"verifying {action} on job {job_id} from job details page")
            redirect_href = JobsHelper.redirects[action]
            if redirect_href:
                redirect_href = redirect_href % job_id
            try:
                errors += self.validate_redirection(
                    actions[action],
                    wait_time=8,
                    new_tabs=new_tabs.get(action, 0),
                    url_patterns=[redirect_href],
                    wait_for_load=True
                )
                self.log.info(f"{action} redirect verified!")
                self.setup_job_details(job_id)
                self._admin_console.wait_for_completion()

            except CVWebAutomationException as exp:
                if "item is disabled" in str(exp).lower():
                    if action not in exclusions and 'all' not in exclusions:
                        raise CVTestStepFailure(f"Redirect {action} is disabled!")
                    else:
                        self.log.error(f"Redirect {action} is greyed out, skipping it")
                        self._admin_console.click_menu_backdrop()  # collapse menu
                        continue
                else:
                    raise exp

        if not errors:
            self.log.info(f"All Redirects validated successfully")
        else:
            for error in errors:
                self.log.error(error)
            raise CVTestStepFailure("Redirects validation failed")

    @test_step
    def validate_resume(self, ui_delay: int = None) -> None:
        """
        Perform resume from current job details page and verifies job is running

        Args:
            ui_delay (int)   -   acceptable time delay between job's api status and ui status
        """
        job_id = self._admin_console.current_url().split('/')[-1]
        self._job_helper.job = self._commcell.job_controller.get(int(job_id))
        if not ui_delay:
            ui_delay = self.time_lag

        self._job_details.resume()
        self._job_helper.wait_for_state(["queued", "waiting", "running", "completed"], retry_interval=2)
        self._job_details.wait_label_text("Status", [self._job_helper.job.status.title()], ui_delay)
        self.log.info("Resume Validated Successfully!")

    @test_step
    def validate_suspend(self, ui_delay: int = None) -> None:
        """
        Perform Suspend from current job details page and verifies job is suspended

        Args:
            ui_delay (int)   -   acceptable time delay between job's api status and ui status
        """
        job_id = self._admin_console.current_url().split('/')[-1]
        self._job_helper.job = self._commcell.job_controller.get(int(job_id))
        if not ui_delay:
            ui_delay = self.time_lag

        self._job_details.suspend('Indefinitely')
        self._job_helper.wait_for_state(["suspended", "committed", "completed"], retry_interval=2)
        self._job_details.wait_label_text("Status", [self._job_helper.job.status.title()], ui_delay)
        self.log.info("Suspend Validated Successfully!")

    @test_step
    def validate_kill(self, ui_delay: int = None) -> None:
        """
        Perform Kill from current job details page and verifies job is killed

        Args:
            ui_delay (int)   -   acceptable time delay between job's api status and ui status
        """
        job_id = self._admin_console.current_url().split('/')[-1]
        self._job_helper.job = self._commcell.job_controller.get(int(job_id))
        if not ui_delay:
            ui_delay = self.time_lag

        self._job_details.kill()
        self._job_helper.wait_for_state(["killed", "committed", "completed"], retry_interval=2)
        self._job_details.wait_label_text("Status", [self._job_helper.job.status.title()], ui_delay)
        self.log.info("Kill Validated Successfully!")

    @test_step
    def validate_resubmit(self) -> None:
        """
        Resubmits from current job details page and verifies the toast and job initiation
        """
        new_job = self._job_details.resubmit()
        try:
            self.job = self._commcell.job_controller.get(int(new_job))
            self._job_helper.job = self.job
            self._job_helper.wait_for_state(["queued", "waiting", "pending", "running", "completed"], retry_interval=2)
        except Exception as exp:
            self.log.error("Failed to find resubmitted job!")
            raise exp
        self.log.info("Resubmit job verified from job details")
        try:
            self._job_helper.job.kill(True)
            self.log.info("Job killed successfully")
        except:
            self.log.error("Error during kill resubmitted job")
