# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Testcase to verify system performance data is populated in history db and visible in infrastructure resource
utilization report"""

from datetime import (
    datetime,
    timedelta
)

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils

from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Validate system performance data upload"
        self.utils = None
        self.ma = None
        self.tcinputs = {
            "MA_Name": None
        }

    @test_step
    def verify_client_update_time(self):
        """Verifies time info"""
        query = f"""SELECT C.displayname client,m.clientid,max(m.creationdate) time
                    from HistoryDB..MMPerformanceHistory m
                    inner join CommServ..APP_Client c on c.id=m.clientId
                    where clientid in (2,{self.ma.client_id})
                    Group by  C.displayname,m.clientid
                    """
        db_data = self.utils.cre_api.execute_sql(
            sql=query, database_name="CommServ", as_json=True)
        ma_time = list(map(lambda time_: datetime.strptime(time_, "%b %d, %Y, %I:%M:%S %p"), db_data["time"]))
        current_time = datetime.now()
        error = list()
        for index, time in enumerate(ma_time):
            seconds = (current_time - time).total_seconds()
            if seconds > 86400:
                error.append(f"client: {db_data['Client'][index]} was last updated"
                             f" {str(timedelta(seconds=seconds))} ago")

        if error:
            raise CVTestStepFailure("\n".join(error))

    def setup(self):
        self.ma = self.commcell.clients.get(self.tcinputs['MA_Name'])
        self.utils = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                       password=self.inputJSONnode['commcell']['commcellPassword'])

    def run(self):
        try:
            self.verify_client_update_time()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
