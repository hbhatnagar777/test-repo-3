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

    This code implements selective copy hourly full for:
    a) last full  wait until
    Expected JSON:
        "MediaAgentName": "MA1",
		"ClientName" : "client1",
		"AgentName":"File System",
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
        self.name = "Selective Copy Acceptance Cases for Hourly & Last Full Wait Until Configuration With Accrued Jobs"
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

    def run_bkp_jobs(self):
        """ runs a few jobs on last sub-client and creates backup job schedule
            for first 2 subclients.
        """
        # Run this for a little time over 2 hours
        self.schedules_list = []
        size = len(self.subclient_list)
        for i in range(size - 1):
            interval = 8 + i * 6
            schedname = "continuous sched for " + self.subclient_list[i].subclient_name
            sched_pattern = {
                'freq_type': 'continuous',
                'job_interval': interval,
                'schedule_name': schedname}
            common_utils = CommonUtils(self.commcell)
            sched_obj = common_utils.subclient_backup(
                subclient=self.subclient_list[i],
                backup_type='full',
                wait=False,
                schedule_pattern=sched_pattern)
            self.schedules_list.append(sched_obj)

        today_start = datetime.datetime.now()  # today()
        # Run on the last subclient
        self.run_jobs('full', 8, -1)

        today_end = datetime.datetime.now()
        timediff = today_end - today_start

        # let us let backup schedule run for at least 180 mins
        if timediff.seconds < 180 * 60:
            self.log.info("Will sleep for %d seconds to let scheduled jobs run for 120 min",
                          ((180 * 60) - timediff.seconds))
            time.sleep((180 * 60) - timediff.seconds)

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
                            has_schedule -- do the passed appids have a job schedule
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
            daystartsonsecs = (int(row[3]) % 60) * 60
            self.log.info("The DayStartsOn option is set with %s seconds", daystartsonsecs)
            break

        # Note: Query is adjusted to IST time zone
        # Here we are checking for jobs that have run during the last period.
        # For example if we invoked the call at say  2019-12-16 18:03:00 then we are looking for
        # jobs that have a start time of 2019-12-16 18:00:00 as they qualify for the period.
        # We do this as we are computing what jobs must be picked based on their rank and other
        # criteria and if the period has not ended then we might mark a job as
        # should be picked incorrectly.
        # Ideally we should sync this with JM thread that does the job picking.
        # For now, this will do.s

        # since the job selection can happen between 1-60 mins after the period ended I guess we
        # need to wait that extra time. That will slow down this test case. Since we are letting
        # jobs run for 3 hours, let us look back for jobs for the first 2 hours.

        today = datetime.datetime.now()
        last_hour = today - datetime.timedelta(hours=1, minutes=today.minute, seconds=today.second)

        sqlquery = str("""
                        select  Q.*,
                        (case when convert(date,Q.jobSelTime) = '1970-01-01' and Q.jobPickedState = 0 and Q.QualifiesByTime = 1 and Q.QualifiesByFreq = 1 and Q.jobRankByHr = 1
                                then DATEDIFF(minute, Q.jobRunTime, '{3}')
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
                                            dbo.GetDateTime(dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate,0)),2),102))
                                            + datepart(hour, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate,0)),2)) * 3600  ) as jobRunDate,
                                            JMB.bkpLevel,
                                            dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(JMB.servStartDate,0)),2) jobRunTime,
                                            RANK() OVER (PARTITION BY JMB.appId,
                                                dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {4},0)),2),102))
                                                    + datepart(hour, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {4},0)),2)) * 3600
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
                       """ and JMB.servStartDate < dbo.GetUnixTime(convert(date,'{3}')) + (3600 * (DATEPART(hour,'{3}'))) - (330 * 60) - {4}
                                join JMJobDataStats JDS with(nolock)
                                    on JMB.jobId = JDS.jobId AND JDS.commCellId = JMB.commCellId AND JDS.archGrpCopyId = (CASE
                                        WHEN AGC.sourceCopyId = 0 THEN AG.defaultCopy ELSE AGC.sourceCopyId END)
                                        AND JDS.disabled = 0
                                where	AG.name = '{1}') SRCDATA
                        on JMDS.jobId = SRCDATA.jobId and JMDS.commCellId = SRCDATA.commCellId and JMDS.appId = SRCDATA.appId
                            where	(JMDS.jobId is not null or SRCDATA.jobId is not null)
                       """).format(copy_obj.copy_id, self.sp_name, queryresultorder, last_hour, daystartsonsecs)

        if for_appids:
            sqlquery += ' and JMDS.appId in (' + ''.join(str(appId) +
                                                         ',' for appId in for_appids)[:-1] + ')'
        sqlquery += ' ) Q'
        self.log.info("Looking for jobs until the last ended hour from %s", str(last_hour))
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

    def hourly_last_full_wait_until_basic(self):
        """START OF BASIC CASE
            Steps:
            1. Create selective copies - last full wait
            2. Run multiple hourly full jobs (via schedules and manual) for multiple sub-clients.
            3. Last full wait we must pick the last full of the hour regardless of whether it was run via
               schedule or manually.
        """

        # Creating Secondary Copy
        # Last Full : Select most recent job if there are no more full backup
        # schedules in the current time period

        sp_obj = self.commcell.storage_policies.get(self.sp_name)
        copy_name_fw1 = str(self.id) + '_selcopyLastFullWait1'
        self.log.info("Adding a new selective copy: %s", copy_name_fw1)
        today = date.today()
        sp_obj.create_selective_copy(
            copy_name_fw1,
            self.disk_library_dest,
            self.tcinputs['MediaAgentName'],
            'hourly',
            'LastFullWait',
            str(today))
        self.log.info("Selective Copy %s has created.", copy_name_fw1)
        self.log.info(
            "Removing association with System Created Autocopy schedule on above created copy")
        if self.commcell.schedule_policies.has_policy('System Created Autocopy schedule'):
            auxcopy_schedule_policy = self.commcell.schedule_policies.get(
                'System Created Autocopy schedule')
            association = [{'storagePolicyName': self.sp_name, 'copyName': copy_name_fw1}]
            auxcopy_schedule_policy.update_associations(association, 'exclude')

        copy_obj_lfw = sp_obj.get_copy(copy_name_fw1)

        self.run_bkp_jobs()
        self.log.info("Checking picked job status on copy %s", copy_name_fw1)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj_lfw)
        if bverdict:
            self.log.info("Last full wait for sub-clients with and without schedule passed")
            self.result_string = "Last full wait for sub-clients with and without " \
                                 "schedule passed <br>"
        else:
            raise Exception("Basic Test Case Unexpected jobs: [{0}] ".format(verdictstr))

    def hourly_last_full_wait_until_accrued(self):
        """ START OF BASIC CASE 2
            Steps:
            1. Selective copy is created after we have accrued a few eligible jobs
               from multiple sub-clients.
            2. Post copy creation ensure we picked the right set of jobs.
            3. Run new jobs and verify we picked right jobs on selective copy.

            From basic case 1 we already have some jobs accrued. So let us just create a
            new copy and verify if we picked right set of jobs.
        """
        sp_obj = self.commcell.storage_policies.get(self.sp_name)
        copy_name_fw = str(self.id) + '_selcopyLastFullWait2'
        self.log.info("Adding a new selective copy: %s", copy_name_fw)
        today = date.today()
        sp_obj.create_selective_copy(
            copy_name_fw,
            self.disk_library_dest,
            self.tcinputs['MediaAgentName'],
            'hourly',
            'LastFullWait',
            str(today))
        self.log.info("Selective Copy %s has created.", copy_name_fw)
        self.log.info(
            "Removing association with System Created Autocopy schedule on above created copy")
        if self.commcell.schedule_policies.has_policy('System Created Autocopy schedule'):
            auxcopy_schedule_policy = self.commcell.schedule_policies.get(
                'System Created Autocopy schedule')
            association = [{'storagePolicyName': self.sp_name, 'copyName': copy_name_fw}]
            auxcopy_schedule_policy.update_associations(association, 'exclude')

        copy_obj_lfw = sp_obj.get_copy(copy_name_fw)
        self.log.info("Checking picked job status on copy %s", copy_name_fw)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj_lfw)
        if bverdict:
            self.log.info("Accrued Jobs For LastFullWait Case Passed")
            self.result_string += "Accrued Jobs For LastFull wait Case Passed <br>"
        else:
            raise Exception("Accrued Jobs Case For LastFull wait Unexpected jobs: [{0}]"
                            .format(verdictstr))

        # Run some new jobs and check if we have picked them right.
        self.log.info("Running new jobs to %s", self.sp_name)
        # self.create_jobs_for_basic_case()
        self.run_bkp_jobs()

        self.log.info("Checking picked job status on copy %s", copy_name_fw)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj_lfw)
        if bverdict:
            self.log.info("Accrued Jobs Case on LastFullWait: Passed for newly run jobs")
            self.result_string += "Accrued Jobs Case on LastFullWait: Passed for newly " \
                                  "run jobs <br>"
        else:
            raise Exception("Accrued Jobs Case on LastFullWait: Newly run jobs Unexpected "
                            "jobs:[{0}]".format(verdictstr))

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

            self.create_bkpset_subclients()
            self.generate_bk_data()
            self.hourly_last_full_wait_until_basic()
            self.hourly_last_full_wait_until_accrued()
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