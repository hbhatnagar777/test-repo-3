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

    Daily Last Full, Most Recent

    Expected JSON:
        "MediaAgentName": "MA1",
		"ClientName" : "client1",
		"AgentName":"File System"
		"SqlSAPassword": "",
        "UnconditionalCleanup": True  # This is an optional parameter. If users do not wish to perform cleanup for failures, set it to False. Default is True

"""

import time
import datetime
from datetime import date
from cvpysdk.backupset import Backupsets
from cvpysdk.subclient import Subclients
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import constants
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
        self.name = "Daily Last Full Most Recent Configuration"
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
        
        self.unconditional_cleanup = None

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
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
        self.backupset_name = str(self.id) + "_bs_"  # + timestamp_suffix
        self.client_machine = Machine(self.client)

        # To select drive with space available on client machine
        self.log.info('Selecting drive on the client machine based on space available')
        self.client_drive = options_selector.get_drive(self.client_machine, size=20 * 1024)
        if self.client_drive is None:
            raise Exception("No free space for hosting sub-client content")
        self.log.info('selected drive: %s', self.client_drive)
        # Change the number of content by adding to the range below
        for i in range(self.numOfSubclients):
            self.content_path = self.client_machine.join_path(
                self.client_drive, 'Automation', str(self.id), 'Testdata' + str(i + 1))
            self.content_list.append(self.content_path)

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
        """ Generate subclient data """
        for content_path in self.content_list:
            self.log.info("Generating data at %s", content_path)
            if not self.client_machine.generate_test_data(
                    content_path, dirs=1, file_size=(20 * 1024), files=2):
                raise Exception("Unable to generate Data at {0}".format(content_path))
            self.log.info("Generated data at %s", content_path)

    def get_completed_jobs_list(self, appid):
        """
            gets completed jobs list for given sub-client
            Args:
                appid -- sub-clientid

        """
        # storage_policy_id
        jobs_list = []
        get_jobs_query = """
                        select appId, jobId
                        from	JMBkpStats JMB with(nolock), archGroup AG with(nolock)
                        where	JMB.dataArchGrpId = AG.Id and appId = {0}
                        and CommcellId = 2 and AG.name = '{1}'
                        order by appId, jobId""".format(appid, self.sp_name)
        self.log.info("get_jobs_query:  %s", get_jobs_query)
        self.csdb.execute(get_jobs_query)
        result_set = self.csdb.fetch_all_rows()
        if result_set != [['']]:
            for row in result_set:
                jobs_list.append(int(row[1]))
        return jobs_list

    def have_jobs_run_beyond_dso(self, copy_obj):
        """
        checks if jobs have run beyond the day starts on set on copy.
        Args:
            copy_obj: selective copy object

        """
        """ for some reason the query though not having update statement is being construed as one.
            so need to run this via MSSQL
        """
        self.log.info("Executing query to check if jobs ran beyond day starts on")
        check_for_jobs_query = """
                                declare @tmpCrossedCopyDSTime int = 0
                                declare @tmpDiffTimeSecs int = 0 
                                declare @tmpJobsRunning int = 0 
                                declare @now_dt datetime = GETDATE()
                                declare @tmpDayStartOnMin int 
                                select @tmpDayStartOnMin = dayNumber
                                from	archSelectiveCopy 
                                where	copyId = {0}
                                if (datepart(hour, @now_dt) * 60 + datepart(minute, @now_dt) < @tmpDayStartOnMin)
                                begin
                                    set @tmpCrossedCopyDSTime = 0
                                    set @tmpDiffTimeSecs = (@tmpDayStartOnMin - (datepart(hour, @now_dt) * 60 
                                                            + datepart(minute, @now_dt))) * 60 
                                end
                                else
                                begin
                                    set @tmpCrossedCopyDSTime = 1 
                                    set @tmpDiffTimeSecs = (datepart(hour, @now_dt) * 60 
                                                            + datepart(minute, @now_dt) - @tmpDayStartOnMin) * 60
                                    -- we are past the copy's start time. so look for any running jobs that 
                                    -- may have started before copy's start time.
                                    if exists (
                                            select *
                                            from	JMJobInfo JI, JMBkpJobInfo JMBI
                                            where	JI.jobId = JMBI.jobId and JMBI.dataPolicy = {1}
                                                    and ( datepart(hour, dbo.UTCToClientLocalTime(dbo.GetDateTime(JI.jobStartTime),2)) * 60 +
                                                        datepart(minute, dbo.UTCToClientLocalTime(dbo.GetDateTime(JI.jobStartTime),2)) ) <= @tmpDayStartOnMin 
                                        )
                                        set @tmpJobsRunning = 1	
                                end
                                select @tmpCrossedCopyDSTime as flg1, @tmpDiffTimeSecs as flg2,  @tmpJobsRunning as flg3
                                """.format(copy_obj.copy_id, self.sp_obj.storage_policy_id)

        self.log.info("Query to check for jobs : %s", check_for_jobs_query)

        sqlinstancename = self.commcell.commserv_hostname + r"\Commvault"
        sapasswd = self.tcinputs['SqlSAPassword']

        mssql_obj = MSSQL(sqlinstancename, "sa", sapasswd, "CommServ")
        if not mssql_obj:
            raise Exception("Failed to get connection to CSDB")

        result_set = mssql_obj.execute(check_for_jobs_query)
        if result_set == [['']]:
            raise Exception("Empty result set")
        return int(result_set.rows[0][0]), int(result_set.rows[0][1]), int(result_set.rows[0][2])
        # return int(result_set.rows[0]['flg1']), int(result_set.rows[0]['flg2']), int(result_set.rows[0]['flg3'])

    def run_bkp_jobs(self, copy_obj, rel_sched_st_time_min, repeat_every_min, copy_day_starts_min):
        """ runs a few jobs on last sub-client and creates backup job schedule
            for first 2 subclients.
        """
        # Run this for a little time over 2 hours
        self.schedules_list = []
        size = len(self.subclient_list)
        jobs_list_dict = dict()

        # get the number of jobs for the 2 sub_clients for which we are creating the bkp-sched.
        for i in range(0, size - 1):
            jobs_list_dict[self.subclient_list[i].subclient_id] = \
                self.get_completed_jobs_list(self.subclient_list[i].subclient_id)
            self.log.info("Num of jobs for sub client %s: %d",
                          self.subclient_list[i].subclient_id,
                          len(jobs_list_dict[self.subclient_list[i].subclient_id]))

        today = datetime.datetime.now()
        start_date = today.date().strftime("%m/%d/%Y")
        st_tmp = today.hour * 60 + today.minute + rel_sched_st_time_min
        start_time = str(int(st_tmp / 60)) + ':' + str(st_tmp % 60)
        repeat_every = "00:{}".format(repeat_every_min)  # 15 minutes

        for i in range(0, size - 1):
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
        # we have about repeat_every_min + repeat_every_min/2 min to spend.
        # Run a few jobs on last subclient
        self.run_jobs('full', 3, -1)

        # Wait till we have 2 jobs completed via schedule but hopefully not reached copy's
        # day end time. Cannot avoid waiting more if the job that started before the day ends
        # is still running.
        # todo: write a case where the last full job extends beyond copy's day end time and
        #       of course has started before the copy's day end time.

        # let us sleep until expected time of 2nd sched job which is
        # rel_sched_st_time_min + repeat_every_min

        today_now = datetime.datetime.now()
        td = today_now - today_start

        self.log.info("rel_sched_st_time_min: %d repeat_every_min: %d td.seconds: %d",
                      rel_sched_st_time_min, repeat_every_min, td.seconds)
        if (rel_sched_st_time_min + repeat_every_min)*60 - td.seconds > 0:
            self.log.info("Will sleep for %d sec and check on completed jobs",
                          (rel_sched_st_time_min + repeat_every_min) * 60 - td.seconds)
            time.sleep((rel_sched_st_time_min + repeat_every_min) * 60 - td.seconds)

        while True:
            b_flag = True
            for i in range(0, size - 1):
                sc_id = self.subclient_list[i].subclient_id
                if len(self.get_completed_jobs_list(sc_id)) - len(jobs_list_dict[sc_id]) < 2:
                    b_flag = False
            if b_flag is True:
                tn = datetime.datetime.now()
                self.log.info("Found all jobs to have completed. Time to copy's day start %d min",
                              copy_day_starts_min - ((tn.hour * 60) + tn.minute))
                break

            tm_crossed_dso_time, tm_diff_secs, tm_jobs_running = self.have_jobs_run_beyond_dso(copy_obj)
            if tm_crossed_dso_time == 0:
                self.log.info("We still have not crossed the copy's day starts on time."
                              "Behind by %d sec", tm_diff_secs)
            elif tm_jobs_running == 1:
                self.log.info("We reached/crossed copy's day starts on time. "
                              "But there are jobs from last time period still running.")
            else:
                self.log.info("Found all jobs to have completed. Passed copy's day end by %d sec",
                              tm_diff_secs)
                break

            self.log.info("Will sleep for 600 seconds to let scheduled jobs to complete")
            time.sleep(600)

        for i in range(0, size - 1):
            sc_id = self.subclient_list[i].subclient_id
            self.log.info("New jobs added by schedule on subclient %s: %d", sc_id,
                          len(self.get_completed_jobs_list(sc_id)) - len(jobs_list_dict[sc_id]))

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
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            raise Exception("Basic backup jobs exception: " + str(exp))

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

    def check_job_status_on_copy(
            self,
            copy_obj,
            for_appids=None,
            has_schedule=None,
            isupdatecopy=None,
            updated_time=None):
        """
                            checks the job picked status on selective copy
                                Args:
                                    copy_obj -- selective copy object
                                    for_appids -- list og appids whose job status we wish to check
                                    isupdatecopy -- for future use
                                    updated_time  -- for future use
        """
        updateQuery = ""
        if isupdatecopy and updated_time:
            updateQuery = str(
                " and JMB.servStartDate >= dbo.GetUnixTime(convert(date,'{0}')) + (3600 * "
                "(DATEPART(hour,'{0}'))) - (330 * 60)").format(updated_time)
        copyflagsquery = """ select  AGC.id, AGC.flags & 8192, AGC.flags & 4096, ASCC.dayNumber
                            from	archGroupCopy AGC, archSelectiveCopy ASCC
                            where	AGC.Id = ASCC.copyId
                                    and	AGC.Id = {0}
                         """.format(copy_obj.copy_id)

        self.log.info("Getting copy's %s flags", copy_obj.copy_id)
        self.csdb.execute(copyflagsquery)
        resultset = self.csdb.fetch_all_rows()
        queryresultorder = ""
        daystartsonsecs = 0

        # For both last full and last full wait, for sub-clients with schedules we must always
        # pick the last full of the time period. Meaning query must be ordered by desc.
        # For sub-clients with no schedule :
        #   on last full copy we should pick first full of the time period.
        #   on last full wait copy we should pick last full of the time period as
        # selection happens at after the end of the period.

        if resultset == [['']]:
            self.log.info("Failed to get copy flags from CSDB. Query %s", copyflagsquery)
            raise Exception("Failed to get copy flags from CSDB")
        for row in resultset:
            if int(row[0]) != int(copy_obj.copy_id):
                self.log.info(
                    "Strange. Result did not have expected copy details. Got %s. Query %s",
                    row[0], copyflagsquery)
                raise Exception("Unexpected result")
            if int(row[1]) > 0:
                self.log.info("Copy %s has Last Full Wait Flag set %s", copy_obj.copy_id, row[1])
                queryresultorder = "desc"
            else:
                self.log.info("Copy %s has NO Last Full Wait Flag set %s",
                              copy_obj.copy_id, row[1])
                if has_schedule and has_schedule is True:
                    queryresultorder = "desc"
                else:
                    self.log.info("has_schedule flag is either not set or false")
            daystartsonsecs = int(row[3]) * 60
            self.log.info("The DayStartsOn option is set with %s seconds", daystartsonsecs)
            break

        # Note: Query is adjusted to IST time zone
        # Here we are checking for jobs that have run during the last period.

        # today is the time when the copy's "day" ends. this is passed to the query to check for
        # jobs that have a start time less than this. Meaning we are looking to jobs for the period
        # that just ended.

        #today = datetime.datetime.now()

        now = datetime.datetime.now()
        today = datetime.datetime(year=now.year, month=now.month, day=now.day) + \
                datetime.timedelta(seconds=(daystartsonsecs - 60))

        sqlquery = str("""
                        select  Q.*,
                        (case when convert(date,Q.jobSelTime) = '1970-01-01' and Q.jobPickedState = 0 and Q.QualifiesByTime = 1 and Q.QualifiesByFreq = 1 and Q.jobRankByHr = 1
                                then DATEDIFF(minute, Q.jobRunTime, GETDATE())
                              when 	convert(date,Q.jobSelTime) = '1970-01-01' and Q.jobPickedState = 0 and (Q.QualifiesByTime = 0 or Q.QualifiesByFreq = 0 or Q.jobRankByHr = 0)
                                then -999999
                                else DATEDIFF(minute, Q.jobRunTime, jobSelTime) end) as MinutesAfterJobRunTime
                        from	(select  distinct SRCDATA.jobId,SRCDATA.appId, SRCDATA.jobRunTime,
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
                                            dbo.GetDateTime(dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {4},0)),2),102))
                                            + datepart(day, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {4},0)),2)) * 3600  ) as jobRunDate,
                                            JMB.bkpLevel,
                                            dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(JMB.servStartDate,0)),2) jobRunTime,
                                            RANK() OVER (PARTITION BY JMB.appId,
                                                dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {4},0)),2),102))
                                                    + datepart(day, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {4},0)),2)) * 3600
                                                ORDER BY JDS.jobId {2} ) as jobRankByHr,
                                                AGC.startTime as copyStartTime
                                            from	archGroup AG with(nolock)
                                            join	archGroupCopy AGC with(nolock)
                                                on AG.Id = AGC.archGroupId and AGC.id = {0}
                                            left outer join	APP_Application AP with(nolock)
                                                on	AG.id = AP.dataArchGrpID
                                            left outer join	JMBkpStats JMB with(nolock)
                                                on JMB.appId = AP.id and JMB.commCellId = 2 and JMB.totalUncompBytes > 0 """
                       + updateQuery +
                       """ and JMB.servStartDate < dbo.GetUnixTime('{3}') - (330 * 60)
                                        join JMJobDataStats JDS with(nolock)
                                            on JMB.jobId = JDS.jobId AND JDS.commCellId = JMB.commCellId AND JDS.archGrpCopyId = (CASE
                                                WHEN AGC.sourceCopyId = 0 THEN AG.defaultCopy ELSE AGC.sourceCopyId END)
                                                AND JDS.disabled = 0
                                        where	AG.name = '{1}') SRCDATA
                                on JMDS.jobId = SRCDATA.jobId and JMDS.commCellId = SRCDATA.commCellId and JMDS.appId = SRCDATA.appId
                            where	(JMDS.jobId is not null or SRCDATA.jobId is not null)
                       """).format(copy_obj.copy_id, self.sp_name, queryresultorder, today, daystartsonsecs)

        if for_appids:
            sqlquery += ' and JMDS.appId in (' + ''.join(str(appId) +
                                                         ',' for appId in for_appids)[:-1] + ')'

        sqlquery += ' ) Q'

        self.log.info("%s", sqlquery)

        self.log.info("Looking for jobs until the last ended hour from %s", str(today))

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        is_result_expected = True
        anomaly_result = ''

        # result set: jobId	appId jobRunTime jobSelTime	jobRankByHr	QualifiesByTime	QualifiesByFreq
        # jobPickedState MinutesAfterJobRunTime
        if resultset != [['']]:
            job_state = ''
            job_picked_verdict = ''
            for row in resultset:
                self.log.info(
                    "JOBID %s APPID %s JobRunTime %s SelectionTime %s JobRankByHr %s "
                    "QualifiesByTime %s QualifiesByFreq %s JobPickedState %s "
                    "MinutesAfterJobRunTime %s",
                    row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                if int(row[7]) == 1:
                    job_state = 'Picked'
                    if int(row[5]) == 1 and int(row[6]) == 1:
                        job_picked_verdict = "EXPECTED"
                        if int(row[8]) > 60:
                            job_picked_verdict += " Picked Late"
                    elif int(row[5]) == 0 or int(row[6]) == 0:
                        job_picked_verdict = "UNEXPECTED. Picked JobId=" + row[0] \
                                            + (' Not qualified by time'
                                               if int(row[5]) == 0 else 'Not qualified by rank')
                        anomaly_result += job_picked_verdict + "\n"
                        is_result_expected = False
                else:
                    job_state = 'Not Picked'
                    if int(row[5]) == 0 or int(row[6]) == 0:
                        job_picked_verdict = "EXPECTED"
                    elif int(row[5]) == 1 and int(row[6]) == 1:
                        job_picked_verdict = "UNEXPECTED. Not Picked JobId=" + \
                            row[0] + ' Qualifies by time and rank.'
                        if int(row[8]) > 60:
                            job_picked_verdict += "Selection has not happened for " + \
                                row[8] + "minutes"
                        anomaly_result += job_picked_verdict + "\n"
                        is_result_expected = False
                self.log.info("%s Job[%s] AppId[%s] RunTime[%s]: %s ", job_state, row[0], row[1],
                              row[2], job_picked_verdict)

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
        sqlinstancename = self.commcell.commserv_hostname + r"\Commvault"
        sapasswd = self.tcinputs['SqlSAPassword']

        self.log.info("Instance %s Password: %s", sqlinstancename, sapasswd)
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


    def daily_last_full_most_recent_basic(self):
        """START OF BASIC CASE
        Steps:
        1. Run backup jobs on 3 sub-clients.
        2. Update their run times spread over 3 days.
        3. Create daily full sel copy with day starts on set
        4. Verify we correctly picked jobs from existing lot.
        5. Create and run jobs via schedule.
        """

        # Creating Selective Copy
        go_back_no_days = 3
        sp_obj = self.commcell.storage_policies.get(self.sp_name)

        # run jobs on all sub-clients.
        self.log.info("Running jobs on all sub-clients")
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

        self.log.info("Updated job run times")

        sp_obj = self.commcell.storage_policies.get(self.sp_name)
        copy_name_lf1 = str(self.id) + '_DailyLastFull'
        self.log.info("Adding a new selective copy: %s", copy_name_lf1)
        today = date.today() - datetime.timedelta(days=go_back_no_days)

        # day start on logic is, from current time allow 2 jobs to run and complete
        # and just have enough time left for day to start so that we can check for
        # picked jobs before the day ends as this is last full + most recent

        # day starts on = current time + relative min to job sched st time (5 min) +
        #                 1.5 * repeat_every

        now = datetime.datetime.now()
        st_tmp = now.hour * 60 + now.minute
        repeat_every_min = 16
        # exp_job_run_time_min = 2 * 10
        rel_sched_st_time_min = 5
        st_tmp += rel_sched_st_time_min + repeat_every_min + int(repeat_every_min/2)
        ds_hr = int(st_tmp / 60)
        ds_min = st_tmp % 60
        ds_ampm = 'AM'
        if ds_hr > 11:
            ds_ampm = "PM"
            if ds_hr > 12:
                ds_hr -= 12

        self.log.info("Current time:%s. Setting copy's day starts on to %s", str(now),
                      str(ds_hr) + ':' + str(ds_min) + ' ' + ds_ampm)

        daystartson = {"hours": str(ds_hr), "minutes": str(ds_min), "seconds": "0", "ampm": ds_ampm}

        sp_obj.create_selective_copy(copy_name_lf1, self.disk_library_dest,
                                     self.tcinputs['MediaAgentName'], 'daily', 'LastFull',
                                     str(today), daystartson)
        self.log.info("Selective Copy %s created.", copy_name_lf1)
        self.log.info(
            "Removing association with System Created Autocopy schedule on above created copy")
        if self.commcell.schedule_policies.has_policy('System Created Autocopy schedule'):
            auxcopy_schedule_policy = self.commcell.schedule_policies.get(
                'System Created Autocopy schedule')
            association = [{'storagePolicyName': self.sp_name, 'copyName': copy_name_lf1}]
            auxcopy_schedule_policy.update_associations(association, 'exclude')

        copy_obj_lf = sp_obj.get_copy(copy_name_lf1)
        self.log.info("Checking picked job status on copy %s for all sub-clients", copy_name_lf1)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(
            copy_obj_lf, None, True)
        if bverdict:
            self.log.info("Daily Last full selection passed.")
            self.result_string = "Daily Last full passed. <br>"
        else:
            raise Exception("Daily Last Full Unexpected jobs:[{0}]"
                            .format(verdictstr))

        for_appids = []
        tmpappid = self.subclient_list[-1].subclient_id
        for_appids.append(tmpappid)

        sqlquery = """ select  top 1 jobId
                                        from	JMJobDataStats
                                        where	archGrpCopyId = {0} and appId = {1}
                                                and status in (100,101,102,103)
                                        order by jobId desc
                                    """.format(copy_obj_lf.copy_id, str(tmpappid))

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        highestJobId = 0
        if resultset != [['']]:
            for row in resultset:
                highestJobId = int(row[0])

        self.log.info("Highest JobId on subclient %s that has no backup schedule [%s]",
                      self.subclient_list[-1].subclient_name, str(highestJobId))

        # run new back up jobs.
        self.run_bkp_jobs(copy_obj_lf, rel_sched_st_time_min, repeat_every_min, st_tmp)

        # For LastFull on sub-clients without sched, in the last iteration we picked last full
        # jobs but now for the newly run jobs we should be picking first full.
        self.log.info("Checking picked job status on copy %s and subclient %s", copy_name_lf1,
                      self.subclient_list[-1].subclient_name)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj_lf, for_appids)

        bverdict = True
        if query_results != [['']]:
            for row in query_results:
                if int(row[0]) > highestJobId and int(row[7]) == 0 and \
                        int(row[4]) == 1 and int(row[5]) == 1 and int(row[6]) == 1:
                    self.log.info("Did not expect job %s to be picked on subclient %s",
                                  row[0], self.subclient_list[-1].subclient_name)
                    bverdict = False

        if bverdict:
            self.log.info("Daily LastFull: Passed for newly run jobs on sub-client "
                          "without schedule")
            self.result_string += "Daily LastFull: Newly Run Jobs on sub-client " \
                                  "without schedule Case Passed  <br>"
        else:
            raise Exception("Daily : Newly run jobs on sub-client without "
                            "schedule unexpected jobs: [{0}] ".format(verdictstr))

        # check for job status on copy for scs with schedule
        self.log.info("Checking picked job status on copy %s for sub-clients that have schedule",
                      copy_name_lf1)

        for_appids.clear()
        for_appids.append(self.subclient_list[0].subclient_id)
        for_appids.append(self.subclient_list[1].subclient_id)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(
            copy_obj_lf, for_appids, True)
        if bverdict:
            self.log.info("Daily Last full selection for sub-clients with schedule passed.")
            self.result_string += "Daily Last full selection for sub-clients with schedule passed.<br>"
        else:
            raise Exception("Daily Last Full For Sub-Clients With Schedule Unexpected jobs:[{0}]"
                            .format(verdictstr))

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

            self.log.info("Creating StoragePolicy %s", self.sp_name)
            sp_obj = self.commcell.storage_policies.add(
                self.sp_name, self.disk_library_src, self.tcinputs['MediaAgentName'])
            # sp_obj = self.commcell.storage_policies.get(self.sp_name)
            if sp_obj:
                self.log.info("Successfully created storage policy")
            else:
                self.log.info("Failed to create storage policy")
                return
            self.sp_obj = sp_obj
            self.create_bkpset_subclients()
            self.generate_bk_data()
            self.daily_last_full_most_recent_basic()
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
