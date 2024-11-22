# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Chargeback report RptStorageUsage, RptCapacityUsage table validation

Input: no input is required

"""

from datetime import date, timedelta

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.API.customreports import CustomReportsAPI

from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure)
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    RPT_STORAGE_USAGE = 'RptStorageUsage'
    RPT_CAPACITY_USAGE = 'RptCapacityUsage'

    DAILY_TYPE = 1
    WEEKLY_TYPE = 3
    MONTHLY_TYPE = 2

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Chargeback report RptStorageUsage, RptCapacityUsage table validation"
        self.utils = None

    def init_tc(self):
        """Initial configuration for connecting to DB"""
        try:
            self.utils = TestCaseUtils(self, self.inputJSONnode["commcell"]["commcellUsername"],
                                       self.inputJSONnode["commcell"]["commcellPassword"])
        except Exception as _exception:
            raise CVTestCaseInitFailure("Exception in db connection with host [%s] with exception:"
                                        " [%s]" % (self.commcell.webconsole_hostname, _exception))

    def get_startdt_data(self, interval_type, table_name):
        """
        Get startDT column data from database
        Args:
            interval_type (int): select TYPE from declaration DAILY_TYPE, WEEKLY_TYPE, MONTHLY_TYPE
            table_name (str): Table name from declaration RPT_STORAGE_USAGE,RPT_CAPACITY_USAGE
        Returns (list) : query result in list
        """
        query = "select Top 1 startDT from %s where type = %s order by startDT desc" % \
                (table_name, interval_type)
        self.log.info("Executing the query: [%s]", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info("Query result:%s", rows[0][0])
        return rows[0][0]

    def get_startdt_string(self, interval_type):
        """
        Get expected date based on 'type',

        Args:
            interval_type (int): type should be selected from DAILY_TYPE, WEEKLY_TYPE
        MONTHLY_TYPE from declaration

        Returns (String): returns expected string  depending on type
        """
        #  if today is '2020-03-06 00:00:00.0', this should return '2020-03-05 00:00:00.0'
        if interval_type == int(1):  # return previous day date
            return str(date.today() - timedelta(1)) + " 00:00:00.0"

        #  if today is '2020-03-06 00:00:00.0', this should return '2020-02-01 00:00:00.0'
        if interval_type == int(2):  # return previous month date
            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(
                days=last_day_of_prev_month.day)
            return str(start_day_of_prev_month) + " 00:00:00.0"

        #  if today is '2020-03-06 00:00:00.0', this should return '2020-02-24 00:00:00.0'
        if interval_type == int(3):  # return previous week date
            today = date.today()
            return str(today - timedelta(days=today.weekday(), weeks=1)) + " 00:00:00.0"
        raise CVTestStepFailure("Invalid interval type is sent, Please select type from "
                                "DAILY_TYPE, WEEKLY_TYPE, MONTHLY_TYPE")

    @test_step
    def verify_repetative_data(self):
        """Verify daily weekly monthly data is populated in RptStorageUsage and RptCapacityUsage
         table"""
        for each_table in [self.RPT_STORAGE_USAGE, self.RPT_CAPACITY_USAGE]:
            for each_type in [self.DAILY_TYPE, self.WEEKLY_TYPE, self.MONTHLY_TYPE]:
                self.log.info("Verifying data for table [%s] with [%s] type ", each_table,
                              each_type)
                # Read table startdt from table
                data = self.get_startdt_data(each_type, each_table)

                # form the string according to type
                expected_startdt = self.get_startdt_string(each_type)
                self.log.info("Expected startdt string %s", expected_startdt)

                # Verify expected startdt is equal to table's startdt
                if expected_startdt != data:
                    raise CVTestStepFailure("expected [%s] startDT in table [%s] with [%s] type,"
                                            " but [%s] exists" %
                                            (expected_startdt, each_table, each_type, data))
                self.log.info("Verified data for [%s] table with [%s] type", each_table,
                              each_type)

    def delete_data_from_table(self, table, startdt, interval_type):
        """Delete previous data from table based on type"""
        query = "delete from %s where startDT='%s' and type = '%s' " % (table, startdt,
                                                                        interval_type)
        self.log.info("Executing the query: [%s]", query)
        self.utils.cs_db.execute(query)

    def execute_stored_procedure(self):
        """Execute the stored procedure [RptSaveStorageUsage] to re generate the data in table"""
        query = "exec RptSaveStorageUsage 0"
        self.log.info("Executing the query: [%s]", query)
        self.utils.cs_db.execute(query)

    @test_step
    def verify_stored_procedure(self):
        """Verify stored procedure is working fine"""
        # check for both the tables 'RptStorageUsage', 'RptCapacityUsage'
        for each_table in [self.RPT_STORAGE_USAGE, self.RPT_CAPACITY_USAGE]:

            #  form the string according to type,
            #  ex: if today is 2020-03-06 00:00:00.000, below should return
            #  2020-03-05 00:00:00.000 with type=1
            #  ex: if today is 2020-03-06 00:00:00.000, below should return
            #  2020-03-24 00:00:00.000 with type=3
            for each_type in [self.DAILY_TYPE, self.WEEKLY_TYPE, self.MONTHLY_TYPE]:
                expected_startdt = self.get_startdt_string(each_type)

                #  delete daily/weekly/monthly type data
                # self.delete_data_from_table(each_table, expected_startdt, each_type)

                #  execute the stored procedure to re generate data and to
                #  make sure sp is working fine
                self.execute_stored_procedure()

                #  Read the both tables, get only startDT column content only 1 string for
                #  each type
                found_startdt = self.get_startdt_data(each_type, each_table)

                #  verify expected startdt string comparing with startdt data of table for
                #  'daily type'
                if expected_startdt != found_startdt:
                    raise CVTestStepFailure("Expected startdt [%s] but found [%s]" %
                                            (expected_startdt, found_startdt))
                self.log.info("Verified data for [%s] type for [%s] table", each_type, each_table)

    def run(self):
        try:
            self.init_tc()
            self.verify_repetative_data()
            self.verify_stored_procedure()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.execute_stored_procedure()
