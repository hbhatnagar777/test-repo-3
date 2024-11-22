# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Ring Routing: Remote Links from Router [UI]

This test verifies the remote links from router on any company in registered commcell for
    Edit icon
    Dashboard icon
    Company link
    Configure
    Entities summary
    Entities link

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed


TestCase Inputs (Optional):
    {
        -------------- entity options (defaults are randomly set) ---------------
        avoid_enabling_reseller (bool)  --  avoids enabling reseller if given
        avoid_cleanup   (bool)          --  skips cleanup if given
        company  (str)                  --  existing reseller company name to test on
        child    (str)                  --  child organization name to test on
        default_password    (str)       --  default password for all created users
        service_commcells   (list)      --  list of service commcells to test on
        idp_commcell        (str)       --  specific idp commcell to use
        workload_commcells   (list)     --  specific workload commcells to use
        child_idp_commcell  (str)       --  specific idp commcell for child
        child_workload_commcells (list) --  specific workloads for child commcell (to extend)

        -------------- credentials (defaults are from multicommcellconstants.RingRoutingConfig) ---------------
    }
"""
import json
import traceback

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.ring_routing_helper import RingRoutingHelperUI


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.error_tracking = {}
        self.exclusions = None
        self.child = None
        self.rr_helper = None
        self.reseller = None
        self.name = "Ring Routing: Remote Links from Router [UI]"
        self.tcinputs = {}

    def setup(self):
        self.reseller = self.tcinputs.get('reseller')
        self.exclusions = self.tcinputs.get('exclusions', '')
        self.rr_helper = RingRoutingHelperUI(
            self.commcell, **self.tcinputs | {
                'router_password': self._inputJSONnode['commcell']['commcellPassword']
            }
        )

    def run(self):
        if not self.reseller:
            self.rr_helper.setup_reseller(
                company_name=self.tcinputs.get('company_name'),
                company_alias=self.tcinputs.get('company_alias')
            )
        personas = {
            # todo: add non admin msp operator
            'MSP as Operator': self.rr_helper.use_msp_admin
        }

        try:
            for persona in personas:
                if persona in self.exclusions:
                    self.log.info(f"****** SKIPPING TEST FOR {persona} ******")
                    self.error_tracking[persona] = 'SKIPPED'
                    continue

                self.log.info(f"****** VALIDATING TEST FOR {persona} ******")

                persona_rrhelper = personas[persona]()  # GETTING PERSONA LOGIN

                # THE TESTS
                try:
                    # persona_rrhelper.validate_companies_list()
                    persona_rrhelper.validate_entities_summary()
                    persona_rrhelper.verify_redirects(
                        exclusions=eval(self.tcinputs.get('redirect_exclusions', 'None'))
                    )
                    persona_rrhelper.validate_switchers_slo()
                    self.log.info(f"****** VALIDATION SUCCESSFUL FOR {persona} ******")
                    self.error_tracking[persona] = 'PASSED'
                except Exception as exp:
                    self.status = constants.FAILED
                    trace = traceback.format_exc()
                    self.log.info("Caught Exception!")
                    self.log.error(str(exp))
                    self.log.error(trace)
                    self.error_tracking[persona] = [str(exp), trace]
                    persona_rrhelper.clean_browser()
                    continue
        finally:
            self.rr_helper.clean_up()

        self.log.info("--------------------- TESTCASE SUMMARY ---------------------")
        for persona, errors in self.error_tracking.items():
            self.log.info("----------------- * * * * * -------------------")
            if errors == 'PASSED':
                self.log.info(f"------------- PASSED FOR {persona} ------------")
            elif errors == 'SKIPPED':
                self.log.info(f"-------------- SKIPPED TEST FOR {persona} ------------")
            else:
                self.log.info(f"------------ FAILURE FOR {persona} ------------")
                self.log.error(errors[0])
                self.log.error(errors[1])
        self.result_string = json.dumps(self.error_tracking, indent=4)
