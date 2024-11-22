# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initializes test case class object

    setup()                 --  Setup function for this testcase

    run()                   --  Main function for this testcase

    tear_down()             --  tear down method for this testcase

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
        rdp creds for any commcell:
                '<cs_name_lowercase>_rdp_username'
                '<cs_name_lowercase>_rdp_password'
        db creds for any commcell:
                '<cs_name_lowercase>_db_username'
                '<cs_name_lowercase>_db_password'
    }

"""
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.ring_routing_helper import RingRoutingHelperAPI


class TestCase(CVTestCase):
    """Class for executing Ring Routing: Remote Operations on Child Company [API]"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.reseller = None
        self.name = "Ring Routing: Remote Operations on Child Company [API]"
        self.rr_helper = None
        self.tcinputs = {}

    def setup(self):
        """setup function for this testcase"""
        self.reseller = self.tcinputs.get("company")
        self.rr_helper = RingRoutingHelperAPI(
            self.commcell, **self.tcinputs | {
                'router_password': self._inputJSONnode['commcell']['commcellPassword']
            }
        )

    def run(self):
        """Main function for test case execution"""
        try:
            if not self.reseller:
                self.rr_helper.setup_reseller(
                    company_name=self.tcinputs.get('company_name'),
                    company_alias=self.tcinputs.get('company_alias')
                )
            self.log.info("------------------------------------------")
            self.log.info("CASE1: CHILD CREATED ON DIFFERENT COMMCELL")
            self.rr_helper.create_child_company()
            self.rr_helper.setup_child_operators(test=True)
            self.rr_helper.setup_child_tags()
            self.rr_helper.deactivate_child()
            self.rr_helper.activate_child()
            self.rr_helper.extend_child()
            self.rr_helper.delete_child()
            self.log.info("------------------------------------------")
            self.log.info("CASE2: CHILD CREATED ON SAME COMMCELL")
            self.rr_helper.child_idp_hostname = self.rr_helper.reseller_idp_hostname
            self.rr_helper.create_child_company()
            self.rr_helper.extend_child()
            self.rr_helper.delete_child()

        finally:
            self.rr_helper.clean_up()
