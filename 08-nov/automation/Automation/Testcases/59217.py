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

    Daily First Fulls case

    Expected JSON:
        "MediaAgentName": "MA1",
		"ClientName" : "client1",
		"AgentName":"File System"
		"SqlSAPassword": "",
        "UnconditionalCleanup": True  # This is an optional parameter. If users do not wish to perform cleanup for failures, set it to False. Default is True

"""

import time
from datetime import date
import datetime
from cvpysdk.backupset import Backupsets
from cvpysdk.subclient import Subclients
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.database_helper import MSSQL


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Daily First Full Configuration"
        self.tcinputs = {
            "MediaAgentName": None
        }

        self.mediaagent = None
        self.disk_library_src = None
        self.disk_library_dest = None
        self.mountpath_src = None
        self.mountpath_dest = None
        self.disk_lib_obj = None
        self.sp_name = None
        self.sp_obj = None
        self.client_machine = None

        self.backupset_name = None
        self.bkupsets = None
        self.subclients = None
        self.subclient_list = []
        self.numOfSubclients = 3
        self.client_drive = None
        self.ma_drive = None
        self.backupset = None
        self.content_list = []
        self.schedules_list = []
        
        self.unconditional_cleanup = None

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        # timestamp_suffix = options_selector.get_custom_str().lower()
        # time_secs = datetime.datetime.now().timestamp()
        # self.id += str(time_secs)
        self.disk_library_src = str(self.id) + "_disklib_src"
        self.disk_library_dest = str(self.id) + "_disklib_dest"
        self.sp_name = str(self.id) + "_sp_auto"
        self.mediaagent = Machine(self.tcinputs['MediaAgentName'], self.commcell)

        self.unconditional_cleanup = self.tcinputs.get('UnconditionalCleanup', True)
        
        # To select drive with space available on media agent machine
        self.log.info('Selecting drive on the MediaAgent machine based on space available')
        self.ma_drive = options_selector.get_drive(self.mediaagent, size=50 * 1024)

        if self.ma_drive is None:
            raise Exception("No free space for hosting mount paths")
        self.log.info('selected drive: %s', self.ma_drive)

        self.mountpath_src = self.mediaagent.join_path(
            self.ma_drive, 'Automation', str(self.id), 'MPSRC')
        self.mountpath_dest = self.mediaagent.join_path(
            self.ma_drive, 'Automation', str(self.id), 'MPDST')
        self.backupset_name = str(self.id) + "_bs_"
        self.client_machine = Machine(self.client)

        # To select drive with space available on client machine
        self.log.info('Selecting drive on the client machine based on space available')
        self.client_drive = options_selector.get_drive(self.client_machine, size=20 * 1024)
        if self.client_drive is None:
            raise Exception("No free space for hosting sub-client content")
        self.log.info('selected drive: %s', self.client_drive)
        # Change the number of content by adding to the range below
        for i in range(self.numOfSubclients):
            content_path = self.client_machine.join_path(
                self.client_drive, 'Automation', str(self.id), 'Testdata' + str(i + 1))
            self.content_list.append(content_path)

        self.bkupsets = Backupsets(self.agent)

    def create_bkpset_subclients(self):
        """fuction to create bkpset and sub-clients """
        subclient_name = ""
        self.log.info("Adding a new backupset: %s", self.backupset_name)
        self.backupset = self.bkupsets.add(self.backupset_name)
        self.log.info("Backupset Configuration Done.")
        # create subclients
        self.subclients = Subclients(self.backupset)

        self.log.info("Creating Subclients")
        for i in range(self.numOfSubclients):
            subclient_name = str(self.id) + "_SC_" + str(i + 1)
            self.log.info("Adding a new subclient: %s", subclient_name)
            sc_obj = self.subclients.add(subclient_name, self.sp_name)
            sc_obj.content = [self.content_list[i]]
            self.subclient_list.append(sc_obj)
            self.log.info("Subclient %s Configuration Done.", subclient_name)

    def generate_bk_data(self):
        """Generate subclient data """
        for content_path in self.content_list:
            self.log.info("Generating data at %s", content_path)
            if not self.client_machine.generate_test_data(
                    content_path, dirs=1, file_size=(20 * 1024), files=2):
                raise Exception("Unable to generate Data at {0}".format(content_path))
            self.log.info("Generated data at %s", content_path)

    def active_sleep(self, secs_to_sleep):
        """ sleeps in small quantas
            (Since we are sleeping for long without any activity, post waking we are receiving
            errors like auth failed, machine not reachable etc.)
            Args:
                secs_to_sleep : total time in seconds to sleep
        """
        # let us sleep short duration and ping CS for some info.
        # pinging csdb didn't help let me
        quant_sleep = 2*60
        t_slept = 0
        simple_query = """ select  name,maxStreams, type, flags
                    from	archGroup with(nolock)
                    where	name = '{0}'""".format(self.sp_name)

        while t_slept < secs_to_sleep:
            if secs_to_sleep - t_slept < quant_sleep:
                quant_sleep = secs_to_sleep - t_slept

            time.sleep(quant_sleep)
            self.csdb.execute(simple_query)
            result_set = self.csdb.fetch_all_rows()
            if result_set == [['']]:
                self.log.info("Strange, query returned nothing about this storage policy")
            t_slept += quant_sleep

            if t_slept >= 360 and t_slept % 360 == 0:
                self.log.info("Slept %d sec. Remaining time %d sec", t_slept, secs_to_sleep - t_slept)

    def run_bkp_jobs(self):
        """ runs a few jobs on last sub-client and creates backup job schedule
            for first 2 subclients.
        """
        self.schedules_list = []
        size = len(self.subclient_list)

        today = datetime.datetime.now()
        start_date = today.date().strftime("%m/%d/%Y")
        st_tmp = today.hour * 60 + today.minute + 5
        # start_time = (today + datetime.timedelta(minutes=5)).strftime("%m/%d/%Y %H:%M")
        start_time = str(int(st_tmp / 60)) + ':' + str(st_tmp % 60)
        rm_hr = 23 - today.hour
        rm_min = 59 - today.minute
        st_tmp = int((rm_hr * 60 + rm_min) / 2)
        repeat_every = str(int(st_tmp / 60)) + ':' + str(st_tmp % 60)
        # print(start_date, start_time, repeat_every)

        for i in range(0, size - 1):
            # interval = 8 + i * 6
            schedname = "Daily schedule for " + self.subclient_list[i].subclient_name
            sched_pattern = {
                'freq_type': 'Daily',
                'active_start_date': str(start_date),
                'active_start_time': str(start_time),
                'repeat_every': repeat_every,
                'repeat_end': '23:59',
                'schedule_name': schedname
            }
            common_utils = CommonUtils(self.commcell)
            sched_obj = common_utils.subclient_backup(
                subclient=self.subclient_list[i],
                backup_type='full',
                wait=False,
                schedule_pattern=sched_pattern)
            self.schedules_list.append(sched_obj)

        today_start = datetime.datetime.now()  # today()

        # Run on the last subclient
        self.run_jobs('full', 4, -1)

        today_end = datetime.datetime.now()
        timediff = today_end - today_start

        # let us let backup schedule run for at least 60 mins
        if timediff.seconds < 60 * 60:
            self.log.info("Will sleep for %d seconds to let scheduled jobs run for 60 min",
                          ((60 * 60) - timediff.seconds))
            self.active_sleep((60 * 60) - timediff.seconds)
            # time.sleep((60 * 60) - timediff.seconds)

        self.log.info("Cleaning up backup job schedules")
        for sch_obj in self.schedules_list:
            scheduler_helper_obj = ScheduleCreationHelper(self)
            scheduler_helper_obj.cleanup_schedules(sch_obj)

    def _run_backup(self, subclient_obj, jobType, return_list):
        """ runs a backup job on given VSA sub-client
            Args:
                subclient_obj - subclient on which we wish to run the job
                jobType - type of job ex. FULL
                return_list - list to append launched job details
        """
        try:
            job = subclient_obj.backup(jobType)
            if job:
                return_list.append(job)
        except BaseException:
            raise Exception("Basic backup jobs: [{0}] ")

    def run_jobs(self, jobType, numOfJobsToRun, numOfsubClientsToRunOn=0):
        """ runs numOfJobsToRun jobs on given subclients from sc_list
            Args:
                jobType - type of job to run
                numOfJobsToRun - number of jobs to run on each of the provided subclients
                numOfsubClientsToRunOn - number of sub-clients on which we want to run jobs.
        """
        running_job_list = []
        startSubclient = 0
        if numOfsubClientsToRunOn < 0:
            startSubclient = len(self.subclient_list) + numOfsubClientsToRunOn
            numOfsubClientsToRunOn = len(self.subclient_list)

        if not numOfsubClientsToRunOn:
            numOfsubClientsToRunOn = len(self.subclient_list)
        # for i in range(numOfJobsToRun):
        i = 0
        while i < numOfJobsToRun:
            for j in range(startSubclient, numOfsubClientsToRunOn):
                self._run_backup(self.subclient_list[j], jobType, running_job_list)
            while True:
                jobs_completed = True
                tmp_str = ''
                for job in running_job_list:
                    if job.is_finished is False:
                        jobs_completed = False
                    tmp_str += str(job.job_id) + ":" + job.status + " "
                self.log.info("Job Status %s", tmp_str)
                if jobs_completed is False:
                    time.sleep(30)
                    self.log.info("Rechecking job status")
                else:
                    self.log.info("All jobs completed running")
                    time.sleep(10)
                    break
            i += 1

    def check_job_status_on_copy(self, copy_obj, for_appids=None, isupdatecopy=None, today=None):
        """
                    checks the job picked status on selective copy
                        Args:
                            copy_obj -- selective copy object
                            for_appids -- list og appids whose job status we wish to check
                            isupdatecopy -- for future use
                            today  -- for future use
        """
        updateQuery = ""
        if isupdatecopy:
            updateQuery = str(
                " and JMB.servStartDate >= dbo.GetUnixTime(convert(date,'{0}')) + "
                "(3600 * (DATEPART(hour,'{0}'))) - (330 * 60)").format(today)
        copyflagsquery = """ select  AGC.id, AGC.archGroupId, AGC.flags & 4096, ASCC.dayNumber
                                    from	archGroupCopy AGC, archSelectiveCopy ASCC
                                    where	AGC.Id = ASCC.copyId
                                            and	AGC.Id = {0}
                                 """.format(copy_obj.copy_id)
        self.log.info("Getting copy's %s flags", copy_obj.copy_id)

        self.csdb.execute(copyflagsquery)
        resultset = self.csdb.fetch_all_rows()
        archgroupid = 0
        daystartsonsecs = 0
        if resultset == [['']]:
            self.log.info("Failed to get copy flags from CSDB. Query %s", copyflagsquery)
            raise Exception("Failed to get copy flags from CSDB")

        for row in resultset:
            if int(row[0]) != int(copy_obj.copy_id):
                self.log.info(
                    "Strange. Result did not have expected copy details. Got %s. Query %s",
                    row[0],
                    copyflagsquery)
                raise Exception("Unexpected result")
            if int(row[1]) > 0:
                archgroupid = int(row[1])
                self.log.info("Copy %s 's storage policy id is %s", copy_obj.copy_id, row[1])
            if int(row[2]) > 0:
                self.log.info("Copy %s has Last Full Flag set %s", copy_obj.copy_id, row[2])
            if int(row[3]) > 0:
                # daynumber is set in minutes. convert it into seconds
                daystartsonsecs = int(row[3]) * 60
                self.log.info("The DayStartsOn option is set with %s seconds", daystartsonsecs)
            else:
                self.log.info("The DayStartsOn option is not set")

            break

        if not archgroupid:
            self.log.info(
                "Storage Policy Id return is 0, which should never happen. Query %s",
                copyflagsquery)
            raise Exception("Unexpected result")
        # for daily, the rank over will be date and day adjusted to daystarts on.
        sqlquery = str(""" select  distinct SRCDATA.jobId,SRCDATA.appId, SRCDATA.jobRunTime,
                            dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(jobSelectionTime,0)),2) as jobSelTime,
                            SRCDATA.jobRankByHr,
                            (case when SRCDATA.servStartDate >= SRCDATA.copyStartTime THEN 1 ELSE 0 end) QualifiesByTime,
                            (case when SRCDATA.jobRankByHr = 1 then 1 else 0 end) QualifiesByFreq,
                            (case  when (JMDS.jobId is not null and JMDS.disabled = 0) then 1 else 0 end ) as jobPickedState
                            from	JMJobDataStats JMDS with(nolock)
                            join	archGroupCopy AGC with(nolock)
                                on	JMDS.archGrpCopyId = AGC.id and AGC.id = {0}
                            right outer join
                                (select  AG.name,AP.Id as appId,JMB.jobId,AP.subclientName,JMB.servStartDate,JMB.commCellId,
                                    dbo.GetDateTime(dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {2},0)),2),102))
                                    + datepart(day, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {2},0)),2)) * 3600  ) as jobRunDate,
                                    JMB.bkpLevel,
                                    dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(JMB.servStartDate,0)),2) jobRunTime,
                                    RANK() OVER (PARTITION BY JMB.appId,
                                        dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {2},0)),2),102))
                                            + datepart(day, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {2},0)),2)) * 3600
                                        ORDER BY JDS.jobId ) as jobRankByHr,
                                        AGC.startTime as copyStartTime
                                    from	archGroup AG with(nolock)
                                    join	archGroupCopy AGC with(nolock)
										on AG.Id = AGC.archGroupId and AGC.id = {0}
                                    left outer join	APP_Application AP with(nolock)
                                        on	AG.id = AP.dataArchGrpID
                                    left outer join	JMBkpStats JMB with(nolock)
                                        on JMB.appId = AP.id and JMB.commCellId = 2 and JMB.totalUncompBytes > 0 """
                       + updateQuery + """
                                    join JMJobDataStats JDS with(nolock)
                                        on JMB.jobId = JDS.jobId AND JDS.commCellId = JMB.commCellId AND JDS.archGrpCopyId = (CASE
                                            WHEN AGC.sourceCopyId = 0 THEN AG.defaultCopy ELSE AGC.sourceCopyId END)
                                            AND JDS.disabled = 0
                                    where	AG.name = '{1}') SRCDATA
                                    on JMDS.jobId = SRCDATA.jobId and JMDS.commCellId = SRCDATA.commCellId and JMDS.appId = SRCDATA.appId
                                    where	(JMDS.jobId is not null or SRCDATA.jobId is not null)
                                        """).format(copy_obj.copy_id, self.sp_name, daystartsonsecs)
        # CommcellId join, case when tertiary copy is present, ensure source - sec
        # copy has valid jobs
        if for_appids:
            sqlquery += ' and JMDS.appId in (' + ''.join(str(appId) +
                                                         ',' for appId in for_appids)[:-1] + ')'

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        is_result_expected = True
        anomaly_result = ''

        print(sqlquery)

        # result set: jobId, appId, jobRunTime, jobSelTime, jobRankByHr,
        # QualifiesByTime, QualifiesByFreq, jobPickedState
        if resultset != [['']]:
            job_state = ''
            job_picked_verdict = ''
            for row in resultset:
                print(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])
                self.log.info(
                    "JOBID %s APPID %s JobRunTime %s SelectionTime %s "
                    "JobRankByHr %s QualifiesByTime %s QualifiesByFreq %s JobPickedState %s",
                    row[0], row[1], row[2], row[3],
                    row[4], row[5], row[6], row[7])

                if int(row[7]) == 1:
                    job_state = 'Picked'
                    if int(row[5]) == 1 and int(row[6]) == 1:
                        job_picked_verdict = "EXPECTED"
                    elif int(row[5]) == 0 or int(row[6]) == 0:
                        job_picked_verdict = "UNEXPECTED. Picked JobId=" + row[0] + (
                            ' Not qualified by time' if int(row[5]) == 0 else 'Not qualified by rank')
                        anomaly_result += job_picked_verdict + "\n"
                        is_result_expected = False
                else:
                    job_state = 'Not Picked'
                    if int(row[5]) == 0 or int(row[6]) == 0:
                        job_picked_verdict = "EXPECTED"
                    elif int(row[5]) == 1 and int(row[6]) == 1:
                        job_picked_verdict = "UNEXPECTED. Not Picked JobId=" + \
                            row[0] + ' Qualifies by time and rank.'
                        anomaly_result += job_picked_verdict + "\n"
                        is_result_expected = False
                print("Listing Values", job_state, row[0], row[1], row[2], job_picked_verdict)
                self.log.info(
                    "%s Job[%s] AppId[%s] RunTime[%s]: %s ",
                    job_state,
                    row[0],
                    row[1],
                    row[2],
                    job_picked_verdict)

        self.log.info("Returning from check_job_status_on_copy")
        return is_result_expected, anomaly_result, resultset

    def _cleanup(self):
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete bkupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.bkupsets.has_backupset(self.backupset_name):
                self.bkupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting storagepolicy: %s if exists", self.sp_name)
            if self.commcell.storage_policies.has_policy(self.sp_name):
                self.commcell.storage_policies.delete(self.sp_name)
                self.log.info("Deleted Dedupe storagepolicy: %s", self.sp_name)

            # Delete Library
            self.log.info("Deleting library: %s if exists", self.disk_library_src)
            if self.commcell.disk_libraries.has_library(self.disk_library_src):
                self.commcell.disk_libraries.delete(self.disk_library_src)
                self.log.info("Deleted library: %s", self.disk_library_src)

            # Delete Library
            self.log.info("Deleting library: %s if exists", self.disk_library_dest)
            if self.commcell.disk_libraries.has_library(self.disk_library_dest):
                self.commcell.disk_libraries.delete(self.disk_library_dest)
                self.log.info("Deleted library: %s", self.disk_library_dest)

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging(storage_policy_name=self.sp_name,
                                                          is_granular=True, include_all_clients=True)
            self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.",
                    data_aging_job.job_id,
                    data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(
                        data_aging_job.job_id,
                        data_aging_job.delay_reason))
            self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)
            
            for contentpath in self.content_list:
                if self.client_machine.check_directory_exists(contentpath):
                    self.client_machine.remove_directory(contentpath)

        except Exception as exp:
            self.log.warning("Error encountered during cleanup : %s", str(exp))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def update_job_run_times(self, days):
        """
        updates the job run times of each sub-client.
        Args:
            days: spreads all jobs over past number of "days"

        """
        sqlinstancename = self.commcell.commserv_hostname() + r"\Commvault"
        sapasswd = self.tcinputs['SqlSAPassword']

        mssql_obj = MSSQL(sqlinstancename, "sa", sapasswd, "CommServ")
        if not mssql_obj:
            raise Exception("Failed to get connection to CSDB")
        # spread_days = 3
        for sc in self.subclient_list:
            if int(sc.subclient_id) > 0:
                jobruntimeupdate = """
                                    declare @tmpDays int = {0}
                                    declare @tmpAppId int = {1}
                                    declare @tmpVar int = 1
                                    while @tmpVar <= @tmpDays
                                    begin
                                        update JMBkpStats set
                                                servStartDate = servStartDate - ((@tmpDays - @tmpVar + 1) * 24*60*60),
                                                servEndDate = servEndDate - ((@tmpDays - @tmpVar + 1) * 24*60*60)
                                        from
                                        (select ntile(@tmpDays) over (order by jobId) jobGrp, jobId, commCellId
                                         from	JMBkpStats
                                         where	appId = @tmpAppId and bkpLevel = 1 and status = 1 ) JQ
                                         where	JMBkpStats.jobId = JQ.JobId and JMBkpStats.commCellId = JQ.commCellId
                                         and JQ.jobGrp = @tmpVar and JMBkpStats.appId = @tmpAppId
                                        set @tmpVar = @tmpVar + 1
                                    end
                                    """.format(days, sc.subclient_id)
                self.log.info("Job run time update query: %s", jobruntimeupdate)
                mssql_obj.execute(jobruntimeupdate)

    def daily_first_full_basic(self):
        """START OF BASIC CASE
            Steps:
            1. Run multiple backup jobs and update their run times such that they are spread
               over 3 days.
            2. Create daily first full selective copy with backups on or after set to today - 3 days.
            3. Verify that we have picked the right jobs from the accrued set.
            4. Note that none of the job have start date of today/now due to #1.
            5. Run jobs via schedule and manually on sub-clients and verify that we picked right ones.
        """
        # Creating Selective Copy
        go_back_no_days = 3
        sp_obj = self.commcell.storage_policies.get(self.sp_name)

        # run jobs on all sub-clients.
        self.run_jobs('full', 6)
        # update job run times
        for i in range(3):
            try:
                self.update_job_run_times(go_back_no_days)
                break
            except Exception as exp:
                self.log.warning("Caught exception while updating run times: %s. "
                                 "Will sleep and retry. Attempt :%d", str(exp), i)
                time.sleep(30)

        copy1_name = str(self.id) + '_daily_full_selcopy'
        self.log.info("Adding a new selective copy: %s", copy1_name)
        today = date.today() - datetime.timedelta(days=go_back_no_days)
        sp_obj.create_selective_copy(copy1_name, self.disk_library_dest,
                                     self.tcinputs['MediaAgentName'], 'daily',
                                     'first', str(today))

        self.log.info("Selective Copy %s has created.", copy1_name)
        self.log.info(
            "Removing association with System Created Autocopy schedule on above created copy")
        if self.commcell.schedule_policies.has_policy('System Created Autocopy schedule'):
            self.log.info("Found AutoCopy Schedule")
            auxcopy_schedule_policy = self.commcell.schedule_policies.get(
                'System Created Autocopy schedule')
            association = [{'storagePolicyName': self.sp_name, 'copyName': copy1_name}]
            auxcopy_schedule_policy.update_associations(association, 'exclude')

        copy_obj = sp_obj.get_copy(copy1_name)

        self.log.info("Checking picked job status on copy %s", copy1_name)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj)
        if bverdict:
            self.log.info("Daily First Full For Accrued Jobs Passed")
            self.result_string = "Daily First Full For Accrued Jobs Passed<br>"
        else:
            self.result_string = "Daily first full Unexpected jobs: [{0}] ".format(verdictstr)
            raise Exception("Daily first full Unexpected jobs: [{0}] ".format(verdictstr))

        # now run new jobs via schedule and manually.
        self.run_bkp_jobs()

        self.log.info("Checking picked job status for newly run jobs on copy %s", copy1_name)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj)
        if bverdict:
            self.log.info("Daily First Full For Newly Run Jobs Passed")
            self.result_string = "Daily First Full For Newly Run Jobs Passed"
        else:
            self.result_string = "Daily first new full Unexpected jobs: [{0}] ".format(verdictstr)
            raise Exception("Daily first new full Unexpected jobs: [{0}] ".format(verdictstr))

    def run(self):
        """Run function of this test case"""
        try:
            self._cleanup()
            self.log.info("Running %s case", self.id)
            self.log.info(
                "Creating Library %s on %s ",
                self.disk_library_src,
                self.tcinputs['MediaAgentName'])

            disk_lib_obj = self.commcell.disk_libraries.add(
                self.disk_library_src, self.tcinputs['MediaAgentName'], self.mountpath_src)
            if disk_lib_obj:
                self.log.info("Created source disk library")

            self.log.info(
                "Creating Library %s on %s ",
                self.disk_library_dest,
                self.tcinputs['MediaAgentName'])
            disk_lib_obj = self.commcell.disk_libraries.add(
                self.disk_library_dest, self.tcinputs['MediaAgentName'], self.mountpath_dest)
            if disk_lib_obj:
                self.log.info("Created dest disk library")

            if not self.commcell.storage_policies.has_policy(self.sp_name):
                self.log.info("Creating StoragePolicy %s", self.sp_name)
                sp_obj = self.commcell.storage_policies.add(self.sp_name, self.disk_library_src,
                                                            self.tcinputs['MediaAgentName'])
            else:
                sp_obj = self.commcell.storage_policies.get(self.sp_name)
            if sp_obj:
                self.log.info("Successfully created storage policy")
            else:
                self.log.info("Failed to create storage policy")
                return

            self.create_bkpset_subclients()
            self.generate_bk_data()
            self.daily_first_full_basic()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string += str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED or self.unconditional_cleanup:
            self.log.info("Test case PASSED or Unconditional cleanup set to True, starting cleanup")
            self._cleanup()
        else:
            self.log.info("Not cleaning up")