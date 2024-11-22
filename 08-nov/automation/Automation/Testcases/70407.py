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
    __init__()                                   -- Initializes TestCase class

    plan_validation()                            -- Verifies that a plan exists for a threat scan client

    run()                                        -- Run function for this testcase
"""
import dynamicindex.utils.constants as cs
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import TestStep, handle_testcase_exception
from cvpysdk.index_server import IndexServer
from Web.AdminConsole.Helper.ThreatAnalysisHelper import ThreatAnalysisHelper


class TestCase(CVTestCase):
    """Class for executing threat scan plan validation"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate threat scan plan"
        self.tcinputs = {
            "IndexServerName": None
        }
        # Testcase constants
        self.test_case_error = None
        

    @test_step
    def plan_validation(self):
        """
        Verifies that there's a plan associated with a threat scan IS
        """
        self.log.info(self.commcell)
        ts_helper = ThreatAnalysisHelper(commcell=self.commcell, csdb=self.csdb)
        index_server_obj = IndexServer(self.commcell, self.tcinputs['IndexServerName'])
        ts_plan_prefix = cs.THREAT_SCAN_PLAN_PREFIX
        
        is_pseudo_client_id = index_server_obj.properties.get("indexServerClientId")
        ts_plan = f'{ts_plan_prefix}{is_pseudo_client_id}'
        ts_plan_exists = ts_helper.is_plan_associated(self.tcinputs['IndexServerName'], ts_plan)
        if not ts_plan_exists:
            raise CVWebAutomationException('[DB] Plan not found in database')
        else:
            self.log.info(f"Plan found")
        self.log.info("Test step passed")
    
    def run(self):
        try:
            self.plan_validation()
            if self.test_case_error is not None:
                raise Exception(self.test_case_error)
        except Exception as err:
            handle_testcase_exception(self, err)
