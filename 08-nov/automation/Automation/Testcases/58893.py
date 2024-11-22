# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Validate Front End Backup Size in Daily/weekly/monthly Chargeback.

    Input Example:

    "testCases": {

        "58893": {
            "ClientName": "metrics2_2",
            "AgentName" : "file system",
            "BackupsetName": "defaultbackupset",
            "SubclientName": "sc1"
}
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Reports.reportsutils import get_startdt_string
import math
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.Common.page_object import TestStep
from cvpysdk.metricsreport import PrivateMetrics
from Reports.metricsutils import MetricsServer


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()

        self.name = (
            "Chargeback: validation of Capacity usage in cs and metrics"
            " for FS Clients and VSA Agents")
        self.utils = None
        self.metrics_server = None
        self.tcinputs = {
            "ClientName": None,
            "SubclientName": None,
            "BackupsetName": None
        }

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        private_metrics_name = PrivateMetrics(self.commcell).private_metrics_server_name
        self.metrics_server = MetricsServer(private_metrics_name)

    def init_tc(self):
        """Initial configuration for connecting to DB"""
        try:
            self.utils = TestCaseUtils(self, self.inputJSONnode["commcell"]["commcellUsername"],
                                       self.inputJSONnode["commcell"]["commcellPassword"])

        except Exception as _exception:
            raise CVTestCaseInitFailure(
                "Testcase init failure on host [%s] with exception:[%s]" % (
                    self.commcell.webconsole_hostname, _exception)
            )

    @staticmethod
    def get_column(matrix, i):
        return [row[i] for row in matrix]

    @test_step
    def get_subclient_id(self):
        """Get subclient id using the client name and subclient name"""

        query = f"""
        SELECT ID FROM app_application 
        WHERE clientId = (
            select id from app_client where name like '{self.tcinputs["ClientName"]}')
        and subclientname like '{self.tcinputs["SubclientName"]}'"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return rows[0][0]

    @test_step
    def yesterday_subclient_front_end_size(self):
        """Get the value of yesterday's front end size"""
        app_id = self.get_subclient_id()
        yesterday_dates = get_startdt_string(1)
        query = f"""
        SELECT TOP 1 frontEndSize FROM RptCapacityUsage 
        WHERE startDT = '{yesterday_dates}' and appId = '{app_id}' 
        order by startDt desc """
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return rows[0][0]

    @test_step
    def yesterday_subclient_backup_size(self):
        """Get the value of yesterday's backup size"""
        app_id = self.get_subclient_id()
        query = f"""
        SELECT B.totalUnCompBytes FROM  JMBkpStats B WITH(NOLOCK) 
        INNER JOIN (SELECT appId, MAX(jobId)
                    AS lastFullJobId FROM  JMBkpStats WITH(NOLOCK) WHERE status IN (1,3,14) AND 
                    bkpLevel IN (1, 64,128,1024, 16384, 32768) AND commCellId = 2 GROUP BY appId) T
        ON B.jobId = T.lastFullJobId AND 
        B.commCellId = 2 and B.appId = {app_id}"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        return rows[0][0]

    @test_step
    def verify_subclient_frontend_size(self):
        """Compare front end size and latest back up size"""
        latest_front_end_size = self.yesterday_subclient_front_end_size()
        latest_backup_size = self.yesterday_subclient_backup_size()
        if latest_front_end_size != latest_backup_size:
            raise CVTestStepFailure(
                f"Yesterday's front end size of [{latest_front_end_size}] does not match the "
                f"latest backup size of {latest_backup_size}"
                )
        else:
            self.log.info("Front End Size info has been validated")

    @test_step
    def verify_subclient_weekly(self):
        """Weekly value is the largest of all the daily values"""
        app_id = self.get_subclient_id()
        self.log.info("Getting the weekly front end size")
        recent_week = get_startdt_string(3)
        query = f"""
        SELECT TOP 1 frontEndSize FROM RptCapacityUsage 
        WHERE type=3 and appId = '{app_id}' and startDT = '{recent_week}' 
        order by startDt desc"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        weekly_front_end_size = rows[0][0]
        last_completed_week = get_startdt_string(4)
        self.log.info("Getting the largest daily front end size")
        query = """
        SELECT TOP 1 frontendSize FROM RptCapacityUsage 
        WHERE type = 1 and appId = %s and startDT BETWEEN {ts '%s'} AND {ts '%s'} 
        order by frontendSize desc""" % (app_id, last_completed_week[1], last_completed_week[0])

        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        largest_daily_front_end_size = rows[0][0]
        self.log.info(f"Weekly Front End Size [{weekly_front_end_size}]")
        self.log.info(
            f"Largest daily front end size over the last week [{largest_daily_front_end_size}]")
        if weekly_front_end_size < largest_daily_front_end_size:
            raise CVTestStepFailure("weekly value is not the largest of the daily values")
        else:
            self.log.info("Weekly data matches that of the daily values")

    def get_vm_info(self):
        """Get the id of the VM with the largest guest size"""

        query = '''CREATE TABLE #LastFullVSAJob (jobId INT, appId INT)
    INSERT	INTO #LastFullVSAJob
    SELECT	MAX(jobId), appId
    FROM	JMBkpStats WITH(NOLOCK)
    WHERE	appType = 106 AND status IN (1,14) AND bkpLevel IN (1, 64, 128, 1024, 16384, 32768)
    and servenddate <= dbo.GetUnixTimeBig(dateadd(day,datediff(day,1,GETDATE()),0))
    and agedtime = 0 and mediadeletedtime = 0
    GROUP BY appId

    SELECT	TOP 1 T.VMClientId, T.jobId AS LastFullJob,
            CAST(GuestSize/1024/1024/1024 AS DECIMAL(20,2)) AS GuestSizeGB
    FROM	APP_Client CL WITH(NOLOCK)
            INNER JOIN (
                SELECT	VM.VMClientId, VM.jobId, LJ.appId AS vsaAppId, CAST(VM.attrVal AS FLOAT) AS GuestSize,
                        ROW_NUMBER() OVER (PARTITION BY VM.VMClientId ORDER BY VM.jobId DESC) AS RowId
                FROM	APP_VMProp VM WITH(NOLOCK)
                        INNER JOIN #LastFullVSAJob LJ ON VM.jobId = LJ.jobId
                WHERE	VM.attrName = 'vmGuestSize'
            ) T ON CL.id = T.VMClientId
            INNER JOIN APP_Application A WITH(NOLOCK) ON T.vsaAppId = A.id
            INNER JOIN APP_Client C ON A.clientId = C.id
            INNER JOIN APP_InstanceName INS ON A.instance = INS.id
            INNER JOIN APP_BackupsetName BS ON A.backupset = BS.id
    WHERE	T.RowId = 1
    ORDER BY LastFullJob desc
    DROP TABLE #LastFullVSAJob
    '''
        rows = self.utils.cre_api.execute_sql(query)
        return [rows[0][0], rows[0][2]]

    @test_step
    def yesterday_vm_backup_size(self):
        """Get the largest front end size from yesterday for that VM"""
        vm_id = self.get_vm_info()[0]
        query = f"""
        SELECT TOP 1 frontendSize FROM RptCapacityUsage WHERE vmClientId = {vm_id} 
        order by startDt desc"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        backup_size_gb = int(rows[0][0]) // 1073741824
        return backup_size_gb

    @test_step
    def verify_vm_frontend_size(self):
        """Compare guest size and latest front end size"""
        vm_id, guest_size = self.get_vm_info()
        largest_guest_size = math.floor(int(guest_size))
        latest_backup_size = self.yesterday_vm_backup_size()
        self.log.info("Largest guest size is: " + str(largest_guest_size))
        self.log.info("Latest backup size is: " + str(latest_backup_size))
        if largest_guest_size != latest_backup_size:
            raise CVTestStepFailure(
                f"Largest guest size [{largest_guest_size}] does not match the "
                f"latest backup size of [{latest_backup_size}] VM id: {vm_id}"
            )
        else:
            self.log.info("Latest backup size is equal to the largest guest size")

    @test_step
    def verify_vm_weekly(self):
        """verify weekly data for VMs"""
        vm_id = self.get_vm_info()[0]
        query = f"""
        SELECT TOP 1 frontEndSize FROM RptCapacityUsage WHERE type=3 and vmClientId = '{vm_id}'
        order by startDt desc"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        weekly_front_end_size = rows[0][0]
        last_completed_week = get_startdt_string(4)
        self.log.info("Getting DAILY data")
        query = f"""SELECT TOP 1 frontendSize FROM RptCapacityUsage
        WHERE type = 1 and vmClientId = {vm_id} and startDT = '{last_completed_week[0]}'
        order by frontendSize desc"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        largest_daily_front_end_size = rows[0][0]
        self.log.info("The latest weekly value is")
        self.log.info(weekly_front_end_size)
        self.log.info("The largest daily value in that week is")
        self.log.info(largest_daily_front_end_size)
        if weekly_front_end_size != largest_daily_front_end_size:
            self.log.error("weekly value is not the largest of the daily values")
        else:
            self.log.info("Weekly data matches that of the daily values")

    @test_step
    def compare_with_metrics(self):
        """Compare values in RptCapacity Usage and ChargebackUsageDetails"""
        query = """
        select top 5 appID from RptCapacityUsage where type=2 and startDT = (SELECT MAX(startDT)
        FROM RptStorageUsage WITH (NOLOCK) WHERE type = 2 ) 
        and vmClientId =0 and frontendSize > 5242880 and jobType =0
        """
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        top_five_id = self.get_column(rows, 0)
        self.log.info(f'comparison is done with appid {top_five_id}')
        capacity_daily_list = []
        capacity_weekly_list = []
        capacity_monthly_list = []
        survey_daily_list = []
        survey_weekly_list = []
        survey_monthly_list = []

        for topId in top_five_id:
            for valueType in [1, 2, 3]:
                query = f"""
                SELECT TOP 1 frontEndSize FROM RptCapacityUsage 
                WHERE appId = {topId} and type = {valueType} and jobType=0
                order by startDT desc"""
                self.log.info("Executing the query: [%s]", query)
                self.csdb.execute(query)
                rows = self.csdb.fetch_all_rows()
                if rows[0][0] == "":
                    rows[0][0] = "0"
                if valueType == 1:
                    capacity_daily_list.append(rows[0][0])
                elif valueType == 2:
                    capacity_monthly_list.append(rows[0][0])
                elif valueType == 3:
                    capacity_weekly_list.append(rows[0][0])

        self.log.info(f"Getting Commserve unique id of commcell {self.commcell.commserv_name}")
        query = f"""
        SELECT ID FROM cf_Commcellidnamemap where commservname = '{self.commcell.commserv_name}'
        """
        metrics_cre_api = self.metrics_server.metrics_server_api
        response = metrics_cre_api.execute_sql(query, database_name="CVCloud")
        cc_id = response[0][0]
        for topId in top_five_id:
            # 4 is daily, 1 is monthly, 2 is weekly
            for instance_type in [4, 1, 2]:

                query = f"""
                Select TOP 1 frontEndSize FROM ChargebackUsageDetails 
                WHERE appId = {topId} and type = {instance_type} and CommservUniqueId = {cc_id}
                and FrontEndSizeType=0 
                order by StartDate desc
                """
                self.log.info("Executing the query: [%s]", query)
                response = metrics_cre_api.execute_sql(query, database_name="UsageHistoryDB")
                if response:
                    if instance_type == 4:
                        survey_daily_list.append(str(response[0][0]))
                    elif instance_type == 1:
                        survey_monthly_list.append(str(response[0][0]))
                    elif instance_type == 2:
                        survey_weekly_list.append(str(response[0][0]))

        if capacity_daily_list != survey_daily_list:
            self.log.info(f'RptCapacityUsage daily data {capacity_daily_list}')
            self.log.info(f'ChargebackUsageDetails daily data {survey_daily_list}')
            raise CVTestStepFailure(
                "RptCapacityUsage and ChargebackUsageDetails list do not match for daily data")
        else:
            self.log.info("Values in both tables are accurate for daily data")

        if capacity_monthly_list != survey_monthly_list:
            self.log.info(f'RptCapacityUsage monthly data {capacity_monthly_list}')
            self.log.info(f'ChargebackUsageDetails monthly data {survey_monthly_list}')
            raise CVTestStepFailure(
                "RPT Capacity and the ChargebackUsageDetails list do not match for monthly data")
        else:
            self.log.info("Values in both tables are accurate for monthly data")
        if capacity_weekly_list != survey_weekly_list:
            self.log.info(f'RptCapacityUsage weekly data {capacity_weekly_list}')
            self.log.info(f'ChargebackUsageDetails weekly data {survey_weekly_list}')
            raise CVTestStepFailure(
                "RPT Capacity and the ChargebackUsageDetails list do not match for weekly data")
        else:
            self.log.info("Values in both tables are accurate for weekly data")

    def run(self):
        try:
            self.init_tc()
            self.verify_subclient_frontend_size()
            self.verify_vm_frontend_size()
            self.verify_vm_weekly()
            self.compare_with_metrics()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
