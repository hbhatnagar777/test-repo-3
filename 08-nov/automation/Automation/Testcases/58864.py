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

    Hourly & First Full Configuration For VSA IDA: Sub-client disassoc case

    Expected JSON:
        "MediaAgentName": "",
        "ClientName" : "",
        "AgentName":"Virtual Server",
        "VMNames": "vm1,vm2,vm3,vm4"


"""
# import threading

import time
from datetime import date
import datetime
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
from AutomationUtils.idautils import CommonUtils
from cvpysdk.constants import VSAObjects


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
        self.name = "Selective Copy for Hourly & First Full Configuration for VSA IDA & With " \
                    "Sub-Client Disassociation"
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
        self.src_ddb = None
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

    def setup(self):
        """Setup function of this test case"""
        options_selector = OptionsSelector(self.commcell)
        # timestamp_suffix = options_selector.get_custom_str().lower()
        time_secs = datetime.datetime.now().timestamp()
        # self.id += str(time_secs)
        self.disk_library_src = str(self.id) + "_disklib_src"
        self.disk_library_dest = str(self.id) + "_disklib_dest"
        self.sp_name = str(self.id) + "_sp_auto"
        self.mediaagent = Machine(self.tcinputs['MediaAgentName'], self.commcell)

        # To select drive with space available on media agent machine
        self.log.info('Selecting drive on the MediaAgent machine based on space available')
        self.ma_drive = options_selector.get_drive(self.mediaagent, size=100*1024)

        if self.ma_drive is None:
            raise Exception("No free space for hosting mount paths")
        self.log.info('selected drive: %s', self.ma_drive)

        self.mountpath_src = self.mediaagent.join_path(
            self.ma_drive, 'Automation', str(self.id), 'MPSRC')
        self.mountpath_dest = self.mediaagent.join_path(
            self.ma_drive, 'Automation', str(self.id), 'MPDST')
        self.src_ddb = self.mediaagent.join_path(
            self.ma_drive, 'Automation', str(self.id), 'ddb_path_'+str(time_secs))
        self.backupset_name = str(self.id) + "_bs_"
        # self.client_machine = Machine(self.client)

        # Setup VMs as content paths
        for i in range(self.numOfSubclients):
            content_path = \
                {
                    'type': VSAObjects.VMName,
                    'name': self.tcinputs['VMNames'].split(',')[i],
                    'display_name': self.tcinputs['VMNames'].split(',')[i],
                }
            self.content_list.append(content_path)
        self.bkupsets = self.agent.backupsets
        self.log.info("Got backup sets")

    def create_bkpset_subclients(self):
        """fuction to create bkpset and sub-clients """
        self.log.info("Adding a new backupset: %s", self.backupset_name)
        self.agent.backupsets.add(self.backupset_name)
        # self.backupset = self.bkupsets.add(self.backupset_name)
        self.backupset = self.agent.backupsets.get(self.backupset_name)

        self.log.info("Backupset Configuration Done.")

        self.log.info("Creating Subclients")
        for i in range(self.numOfSubclients):
            subclient_name = str(self.id) + "_SC_" + str(i + 1)
            self.log.info("Adding a new subclient: %s", subclient_name)
            self.backupset.subclients.add(subclient_name, self.sp_name)
            sc_obj = self.backupset.subclients.get(subclient_name)
            print("Added sub-client")
            print(self.content_list[i])
            sc_obj.content = [self.content_list[i]]
            self.subclient_list.append(sc_obj)
            self.log.info("Subclient %s Configuration Done.", subclient_name)

    def run_bkp_jobs(self):
        """ runs a a few jobs on last sub-client and creates backup job schedule
            for first 2 subclients.
        """
        self.schedules_list = []
        size = len(self.subclient_list)
        # if size > 1:
        #     size -= 1
        # for first 2 subclients only
        for i in range(0, size - 1):
            interval = 8 + i * 6
            schedname = "continuous schedule for " + self.subclient_list[i].subclient_name
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

        # let us let backup schedule run for at least 90 mins
        if timediff.seconds < 90 * 60:
            self.log.info("Will sleep for %d seconds to let scheduled jobs run for 90 min",
                          ((90 * 60) - timediff.seconds))
            time.sleep((90 * 60) - timediff.seconds)

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
                    time.sleep(10)
                    self.log.info("Rechecking job status")
                else:
                    self.log.info("All jobs completed running")
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
                daystartsonsecs = (int(row[3]) % 60) * 60
                self.log.info("The DayStartsOn option is set with %s seconds", daystartsonsecs)
            else:
                self.log.info("The DayStartsOn option is not set")

            break

        if not archgroupid:
            self.log.info(
                "Storage Policy Id return is 0, which should never happen. Query %s",
                copyflagsquery)
            raise Exception("Unexpected result")

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
                                    dbo.GetDateTime(dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate,0)),2),102))
                                    + datepart(hour, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate,0)),2)) * 3600  ) as jobRunDate,
                                    JMB.bkpLevel,
                                    dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(JMB.servStartDate,0)),2) jobRunTime,
                                    RANK() OVER (PARTITION BY JMB.appId,
                                        dbo.GetUnixTime(convert(date, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {2},0)),2),102))
                                            + datepart(hour, dbo.UTCToClientLocalTime(dbo.GetDateTime(isnull(servStartDate - {2},0)),2)) * 3600
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

    def create_new_subclient(self):
        content_path = \
            {
                'type': VSAObjects.VMName,
                'name': self.tcinputs['VMNames'].split(',')[-1],
                'display_name': self.tcinputs['VMNames'].split(',')[-1],
            }
        self.content_list.append(content_path)
        subclient_name = str(self.id) + "_SC_" + str(self.numOfSubclients+1)
        self.log.info("Adding a new subclient: %s", subclient_name)
        self.backupset.subclients.add(subclient_name, self.sp_name)
        sc_obj = self.backupset.subclients.get(subclient_name)
        sc_obj.content = [self.content_list[-1]]
        self.subclient_list.append(sc_obj)
        self.log.info("Subclient %s Configuration Done.", subclient_name)
        return sc_obj

    def _cleanup(self):
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete bkupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.bkupsets.has_backupset(self.backupset_name):
                self.bkupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            if self.commcell.storage_policies.has_policy(self.sp_name):
                # re-associate subclients to Not Assigned state
                request_xml = '''<App_ReassociateStoragePolicyReq>
                                    <forceNextBkpToFull>1</forceNextBkpToFull>
                                    <runSyntheticFullForTurbo/>
                                    <currentStoragePolicy>
                                        <storagePolicyName>{0}</storagePolicyName>
                                    </currentStoragePolicy>
                                    <newStoragePolicy>
                                        <storagePolicyName>CV_DEFAULT</storagePolicyName>
                                    </newStoragePolicy>
                                </App_ReassociateStoragePolicyReq>
                                '''.format(self.sp_name)
                self.commcell.qoperation_execute(request_xml)
                self.log.info("Deleting storage policy  %s", self.sp_name)
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

            if self.mediaagent.check_directory_exists(self.mountpath_src):
                self.mediaagent.remove_directory(self.mountpath_src)

            if self.mediaagent.check_directory_exists(self.mountpath_dest):
                self.mediaagent.remove_directory(self.mountpath_dest)

            if self.mediaagent.check_directory_exists(self.src_ddb):
                self.mediaagent.remove_directory(self.src_ddb)
        except Exception as exp:
            self.log.warning("Error encountered during cleanup : %s", str(exp))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def hourly_first_full_basic(self):
        """START OF BASIC CASE
            Steps:
            Create a selective copy.
            Run multiple hourly full jobs (via schedules and manual) for multiple sub-clients.
            Verify we always pick the first hourly full for each subclient.
            Repeat this over a few hours.
        """
        # Creating Selective Copy
        sp_obj = self.commcell.storage_policies.get(self.sp_name)
        copy1_name = str(self.id) + '_selcopy'
        self.log.info("Adding a new selective copy: %s", copy1_name)
        today = date.today()
        sp_obj.create_selective_copy(
            copy1_name,
            self.disk_library_dest,
            self.tcinputs['MediaAgentName'],
            'hourly',
            'first',
            str(today))
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
        self.run_bkp_jobs()
        self.log.info("Checking picked job status on copy %s", copy1_name)
        bverdict, verdictstr, query_results = self.check_job_status_on_copy(copy_obj)
        if bverdict:
            self.log.info("Basic Test Case passed")
            # self.result_string = "Basic Test Case passed"
        else:
            self.result_string = "Basic Test Case Unexpected jobs: [{0}] ".format(verdictstr)
            raise Exception("Basic Test Case Unexpected jobs: [{0}] ".format(verdictstr))

    def hourly_first_full_sc_disassoc(self):
        """ START OF BASIC CASE 3
            Steps:
                1. Create a new sub-client and dis-associate it from selective copy.
                2. Dis-associate an existing sub-client from selective copy.
                2. Run backup jobs on new subclient & old sub-clients
                3. Verify that we pick jobs only from associated sub-clients.

                I will reuse the first selective copy that we created for this purpose.
        """
        copy1_name = str(self.id) + '_selcopy'
        sp_obj = self.commcell.storage_policies.get(self.sp_name)
        copy_obj = sp_obj.get_copy(copy1_name)
        sc4_obj = self.create_new_subclient()

        self.log.info(
            "Dis-associating subclient %s from selective copy : %s",
            sc4_obj.subclient_name,
            copy1_name)

        # [-si 'a=Agent'] [-si 'i=instanceName'] [-si 'b=backupsetName']  [-si 's=subClientName']
        # qoperation  execscript
        cmd = r"-sn QS_modifySubclientAssociationsForCopy -si 'e={7}' -si 'sp={0}' " \
              r"-si 'c={1}' -si 'cl={2}' -si 'a={3}' -si 'i={4}' -si 'b={5}' -si 's={6}'".format(
                  self.sp_name, copy1_name, self.tcinputs['ClientName'], self.tcinputs['AgentName'],
                  "VMware", self.backupset_name, sc4_obj.subclient_name, "exclude")

        #request_url = self.commcell._services['QCOMMAND'] + '/' + cmd
        request_url = self.commcell._services['EXECUTE_QSCRIPT'] % cmd
        self.log.info("We shall POST this request url :: %s", request_url)
        bPostRes, post_response = self.commcell._cvpysdk_object.make_request("POST", request_url)
        if not bPostRes:
            self.log.info("POST Failed")
            raise Exception("POST Command to dis-associate sub-client failed")
        self.log.info(
            "Successfully disassociated subclient %s from selective copy : %s",
            sc4_obj.subclient_name,
            copy1_name)

        # Let us get the latest jobId on this copy that was picked as we are reusing the copy.
        # When a sub-client is dis-associated from a copy and if it has jobs in to-be-copied state we disable
        # those jobs for auxCopy. These will NOT be re-enabled even after re-association.
        # Any job that we run after this for this sub-client should not be picked.
        sc3_obj = self.subclient_list[2]
        sqlquery = """
                        select  top 1 JMDS.jobId
                        from	JMJobDataStats JMDS with(nolock), APP_Application AP with(nolock), 
                                APP_Client C with(nolock)
                        where	JMDS.archGrpCopyId = {0} and JMDS.appId = AP.Id and AP.clientId = C.id
                                and JMDS.archGrpId = AP.dataArchGrpID
                                and AP.appTypeId = 106 and AP.subclientName = 'default'
                                and C.name = '{1}'
                                and JMDS.status in (100,101,102,103) and disabled = 0
                        order by JMDS.jobId desc
                        """.format(copy_obj.copy_id, self.tcinputs['VMNames'].split(',')[2])

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        self.highestJobId = 0
        if resultset != [['']]:
            for row in resultset:
                self.highestJobId = int(row[0])

        self.log.info(
            "Highest JobId on subclient %s [%s]", sc3_obj.subclient_name, str(
                self.highestJobId))
        self.log.info(
            "Dis-associating subclient %s from selective copy : %s",
            sc3_obj.subclient_name,
            copy1_name)

        cmd = r"-sn QS_modifySubclientAssociationsForCopy -si 'e={7}' -si 'sp={0}' " \
              r"-si 'c={1}' -si 'cl={2}' -si 'a={3}' -si 'i={4}' -si 'b={5}' -si 's={6}'".format(
            self.sp_name, copy1_name, self.tcinputs['ClientName'], self.tcinputs['AgentName'],
            "VMware", self.backupset_name, sc3_obj.subclient_name, "exclude")

        # request_url = self.commcell._services['QCOMMAND'] + '/' + cmd
        request_url = self.commcell._services['EXECUTE_QSCRIPT'] % cmd
        self.log.info("We shall POST this request url :: %s", request_url)
        bPostRes, post_response = self.commcell._cvpysdk_object.make_request('POST', request_url)
        if not bPostRes:
            self.log.info("POST Failed")
            raise Exception("POST Command to dis-associate sub-client failed")

        self.log.info(
            "Successfully disassociated sub-client %s from selective copy : %s",
            sc3_obj.subclient_name,
            copy1_name)

        # Give it 10 sec for jobs to get marked do not copy.

        time.sleep(10)
        # Check that all to-be-copied are marked disabled
        sqlquery = """ 
                    select  count(*)
                    from	JMJobDataStats JMDS with(nolock), APP_Application AP with(nolock), 
                            APP_Client C with(nolock)
                    where	JMDS.archGrpCopyId = {0} and JMDS.appId = AP.Id and AP.clientId = C.id
                            and JMDS.archGrpId = AP.dataArchGrpID
                            and AP.appTypeId = 106 and AP.subclientName = 'default'
                            and C.name = '{1}'
                            and JMDS.status in (101,102,103) and disabled = 0
                    """.format(copy_obj.copy_id, self.tcinputs['VMNames'].split(',')[2])

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        if resultset != [['']]:
            for row in resultset:
                if int(row[0]) > 0:
                    self.log.info("Jobs not marked disabled on copy %s", str(copy_obj.copy_id))
                    raise Exception("Jobs not marked disabled on copy")

        # for existing subclients there could be jobs already run for the current period. If so then we
        # should wait until the next period begins

        today = datetime.datetime.now()
        seconds_to_next_hour = (59 - today.minute) * 60 + (60 - today.second)

        if seconds_to_next_hour > 0:
            self.log.info(
                "Sleeping for %s seconds until the next hour begins",
                str(seconds_to_next_hour))
            time.sleep(seconds_to_next_hour)

        self.log.info("Running jobs on disassociated sub-clients")
        # run fulls on sub-clients 3 & 4
        self.run_jobs('full', 2, -2)

        # without a group by I wil get a zero count
        sqlquery = """ select  count(*)
                    from	JMJobDataStats JMDS with(nolock), APP_Application AP with(nolock), 
                            APP_Client C with(nolock)
                    where	JMDS.archGrpCopyId = {0} and JMDS.appId = AP.Id and AP.clientId = C.id
                            and JMDS.archGrpId = AP.dataArchGrpID
                            and AP.appTypeId = 106 and AP.subclientName = 'default'
                            and C.name = '{1}'
                            and JMDS.status in (101,102,103) and disabled = 0
                    """.format(copy_obj.copy_id, self.tcinputs['VMNames'].split(',')[2])

        self.log.info("Checking picked job status on copy %s for sub-client %s", copy1_name,
                      sc3_obj.subclient_name)

        self.log.info("Query : %s", sqlquery)

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        if resultset != [['']]:
            for row in resultset:
                if int(row[0]) > 0:
                    self.log.info("Jobs got picked post sub-client %s dis-association on copy %s",
                                  sc3_obj.subclient_name, str(copy_obj.copy_id))
                    self.log.info(
                        "SubClient disassociation case failed for %s",
                        sc3_obj.subclient_name)
                    raise Exception("Jobs were picked on dis-associated sub-client")

        self.log.info("SubClient disassociation case passed for %s", sc3_obj.subclient_name)
        self.result_string += "SubClient Dis-Association For An Existing Sub-Client Case Passed<br>"

        sqlquery = """ select  count(*)
                    from	JMJobDataStats JMDS with(nolock), APP_Application AP with(nolock), 
                            APP_Client C with(nolock)
                    where	JMDS.archGrpCopyId = {0} and JMDS.appId = AP.Id and AP.clientId = C.id
                            and JMDS.archGrpId = AP.dataArchGrpID
                            and AP.appTypeId = 106 and AP.subclientName = 'default'
                            and C.name = '{1}'
                            and JMDS.status in (101,102,103) and disabled = 0
                   """.format(copy_obj.copy_id, self.tcinputs['VMNames'].split(',')[3])

        self.log.info("Checking picked job status on copy %s for sub-client %s", copy1_name,
                      sc4_obj.subclient_name)
        self.log.info("Query : %s", sqlquery)

        self.csdb.execute(sqlquery)
        resultset = self.csdb.fetch_all_rows()

        if resultset != [['']]:
            for row in resultset:
                if int(row[0]) > 0:
                    self.log.info("Jobs got picked post sub-client %s dis-association on copy %s",
                                  sc4_obj.subclient_name, str(copy_obj.copy_id))
                    self.log.info(
                        "SubClient disassociation case failed for %s",
                        sc4_obj.subclient_name)
                    raise Exception("Jobs were picked on dis-associated sub-client")

        self.log.info("SubClient disassociation case passed for %s", sc4_obj.subclient_name)
        self.result_string += "SubClient Dis-Association For A New Sub-Client Case Passed<br>"

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
                                                            self.tcinputs['MediaAgentName'], self.src_ddb)
            else:
                sp_obj = self.commcell.storage_policies.get(self.sp_name)
            if sp_obj:
                self.log.info("Successfully created storage policy")
            else:
                self.log.info("Failed to create storage policy")
                return

            self.create_bkpset_subclients()
            self.hourly_first_full_basic()
            self.hourly_first_full_sc_disassoc()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string += str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self._cleanup()
        else:
            self.log.info("Not cleaning up as we encountered error")