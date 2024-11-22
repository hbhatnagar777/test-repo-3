# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Chargeback report RptStorageUsage, RptCapacityUsage table validation

Input: no input is required

"""

from Reports.reportsutils import get_startdt_string

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure)
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    RPT_STORAGE_USAGE = 'RptStorageUsage'
    RPT_DEDUP_RATIOS = 'RptDedupRatios'

    RPT_CAPACITY_USAGE = 'RptCapacityUsage'

    DAILY_TYPE = 1
    MONTHLY_TYPE = 2
    WEEKLY_TYPE = 3

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Chargeback report RptDedupRatios table validation"
        self.utils = None
        self.db_connection = None

    def init_tc(self):
        """Initial configuration for connecting to DB"""
        try:
            self.utils = TestCaseUtils(
                self, self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
        except Exception as _exception:
            raise CVTestCaseInitFailure(
                f"Exception in db connection with host [{self.commcell.commserv_name}] "
                f"with exception:[{_exception}]"
            )

    def get_startdt_data(self, value_type, copy_id):
        """
        Get startDT column data from database
        Args:
            value_type (int): select TYPE from declaration DAILY_TYPE, WEEKLY_TYPE, MONTHLY_TYPE
            copy_id (str): Table name from declaration RPT_STORAGE_USAGE,RPT_CAPACITY_USAGE
        Returns (list) : query result in list
        """
        query = (
                "SELECT Top 1 startDT FROM RptDedupRatios with (nolock) "
                f"WHERE type = {value_type} and copyId = {copy_id} ORDER BY "
                "startDT desc"
        )
        self.log.info("Executing the query: [%s]", query)

        self.csdb.execute(query)
        '''self.csdb.execute(query)'''
        rows = self.csdb.fetch_all_rows()
        self.log.info("Query result:%s", rows[0][0])
        return rows[0][0]

    @staticmethod
    def get_column(matrix, i):
        return [row[i] for row in matrix]

    def get_copyid_list(self):

        query = """select  distinct archGrpCopyId as Copyid from JMJobDataStats  
        where archGrpCopyId in (
            SELECT top 8 AGC.id AS CopyID FROM    archGroupCopy AGC
            INNER JOIN archGroup AG ON AGC.archGroupId = AG.id
            WHERE    AG.type = 1 AND AGC.type IN (1,2) AND AGC.IsActive = 1 
            and AGC.SIDBStoreId > 0 AND AGC.dedupeFlags&268435456 = 0) 
        and sizeOnMedia > 0 and copiedTime >= DATEDIFF(SECOND, '19700101', GETUTCDATE()) - 3888000 
"""
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        copy_id_list = self.get_column(rows, 0)
        return copy_id_list

    @test_step
    def verify_data_entry(self):
        """Verify daily weekly monthly data is populated in RptStorageUsage and RptCapacityUsage
         table"""
        final_copy_id = self.get_copyid_list()

        self.log.info("List of IDs to be verified: " + str(final_copy_id))
        for each_id in final_copy_id:

            self.log.info(each_id)
            for each_type in [self.DAILY_TYPE, self.WEEKLY_TYPE, self.MONTHLY_TYPE]:

                self.log.info("Verifying data for id" + str(each_id))
                # Read table startdt from table
                data = self.get_startdt_data(each_type, each_id)

                # form the string according to type
                if each_type == 4:
                    expected_startdt = get_startdt_string(each_type)[0]
                else:
                    expected_startdt = get_startdt_string(each_type)

                self.log.info("Expected start date %s", expected_startdt)

                # Verify expected startdt is equal to table's startdt
                if expected_startdt != data:
                    raise CVTestStepFailure("expected [%s] startDT in table [%s] with [%s] type,"
                                            " but [%s] exists" %
                                            (expected_startdt, "RptDedupRatios", each_type, data))
                self.log.info("Verified data for [%s] id with [%s] type", each_id,
                              each_type)

    @test_step
    def verify_between_tables(self):
        """Compare data between RptDedupRatios and RptStorage Usage"""
        top_five_id = self.get_copyid_list()

        for each_id in top_five_id:
            for each_type in [self.DAILY_TYPE, self.WEEKLY_TYPE, self.MONTHLY_TYPE]:
                self.log.info("Verifying data for id [%s] with [%s] type ", each_id,
                              each_type)
                dedupe_ratio_query = (
                    "SELECT Top 1 dedupRatio FROM RptDedupRatios with (nolock) "
                    f"WHERE type = {each_type} and copyId = {each_id} ORDER BY startDT desc"
                )
                self.csdb.execute(dedupe_ratio_query)
                rows = self.csdb.fetch_all_rows()
                dedup_ratio = round(float(rows[0][0]),2)
                rpt_storage_usage_query = (
                    "SELECT Top 1 dedupRatio FROM RptStorageUsage with (nolock) "
                    f"WHERE type = {each_type} and copyId = {each_id} ORDER BY startDT desc"
                )
                self.csdb.execute(rpt_storage_usage_query)
                rows = self.csdb.fetch_all_rows()
                dedup_storage = round(float(rows[0][0]),2)
                if dedup_ratio != dedup_storage:
                    self.log.error(
                        f"For copy id {each_id} and type {each_type}, Dedup Storage value is "
                        f"[{dedup_storage}] Dedup Ratio value is [{dedup_ratio}]"
                    )
                    raise CVTestStepFailure(
                        "Dedupe ratio in RptDedupRatios and RptStorageUsage tables "
                        f"do not match at copy id {each_id} and type {each_type}"
                    )

    @test_step
    def verify_dedupe_ratios(self):
        """Verify that the dedup ratios are not greater than 1"""
        for each_table in [self.RPT_STORAGE_USAGE, self.RPT_DEDUP_RATIOS]:
            query = f"""
            SELECT dedupRatio, copyId FROM {each_table} with (nolock)
            WHERE type !=0  and copyid in (
                SELECT top 10 AGC.id AS copyId from archgroupcopy AGC 
                INNER JOIN archGroup AG ON AGC.archGroupID=AG.id 
                where ag.type=1 and AGC.type in (1,2) AND AGC.IsActive=1 and AGC.SIDBStoreId > 0
                )
                and startDT > GETDate() -10
            order by copyId desc
            """
            self.log.info("Executing the query: [%s]", query)
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            id_list = self.get_column(rows, 1)
            dedup_list = self.get_column(rows, 0)
            count = 0
            self.log.info(dedup_list)
            for i in dedup_list:

                if float(i) > 1.00001:
                    raise CVTestStepFailure(f"Dedup > 1 at id: {id_list[count]}")
                count += 1

    def execute_stored_procedure(self):
        """Execute the stored procedure [RptSaveStorageUsage] to re generate the data in table"""
        query = "Exec RptSaveDedupRatios 0"
        self.log.info("Executing the query: [%s]", query)
        self.utils.cre_api.execute_sql(query)

    def run(self):
        try:
            self.init_tc()
            self.verify_data_entry()
            self.verify_between_tables()
            self.verify_dedupe_ratios()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.execute_stored_procedure()
