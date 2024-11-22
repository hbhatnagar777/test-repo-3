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
        -------------- testcase options (defaults are present)  -----------------
        timeout (int)                   --  seconds to keep waiting for RR Sync
        company_alias   (str)           --  alias name to set for creating reseller
        company_name    (str)           --  company name to set for creating reseller
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
import random

from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.ring_routing_helper import RingRoutingHelperAPI


class TestCase(CVTestCase):
    """Class for executing Ring Routing: All Properties Sync Of Extended Child [API]"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.timeout = 60 * 5
        self.child = None
        self.reseller = None
        self.name = "Ring Routing: All Properties Sync Of Extended Child [API]"
        self.rr_helper = None
        self.tcinputs = {}

    def setup(self):
        """setup function for this testcase"""
        self.reseller = self.tcinputs.get("company")
        self.child = self.tcinputs.get("child")
        if "timeout" in self.tcinputs:
            self.timeout = int(self.tcinputs["timeout"])
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
            if not self.child:
                self.rr_helper.create_child_company()
                self.rr_helper.extend_child()
            if not self.rr_helper.child_workloads_hostnames:
                self.rr_helper.extend_child()

            level_transfer_init_params = {
                'company': self.rr_helper._child_name,
                'default_password': self.rr_helper._default_password,
                'router_password': self._inputJSONnode['commcell']['commcellPassword'],
            }
            msp_lvl_helper = RingRoutingHelperAPI(self.commcell, **level_transfer_init_params)
            reseller_lvl_helper = RingRoutingHelperAPI(
                self.rr_helper.reseller_idp_as_reseller,
                **(level_transfer_init_params | {
                    'router_password': self.rr_helper._default_password
                })
            )
            # TODO: ADD GENERIC N LEVELS LOGIC
            helper_levels = {
                'msp': msp_lvl_helper,
                'father': reseller_lvl_helper
            }

            for level, helper in helper_levels.items():
                success = False
                try:
                    self.log.info(f"---------------------TESTING CHILD FROM LEVEL: {level}-------------------------")
                    random_coinflip = random.choice([True, False])
                    helper.modify_dlp(as_reseller=random_coinflip)
                    helper.modify_autodiscovery(as_reseller=(not random_coinflip))
                    helper.setup_theme(as_reseller=random_coinflip)
                    helper.verify_sync_continous(timeout=self.timeout)
                    helper.setup_theme(as_reseller=(not random_coinflip))
                    for x in [True, False]:
                        for y in [True, False]:
                            helper.setup_company_user(
                                as_reseller=x, workloads=y, tenant_admin=True, add_contact=True
                            )
                    roles = [
                        helper.setup_role(workloads=x, as_reseller=y)
                        # ONLY USING RESELLER CREATED ROLES TO AVOID ROLE PERMISSION CONFLICT CASES
                        for x in [True, False] for y in [True, False]
                    ]
                    for role in roles:
                        helper.setup_msp_user(workloads=True, role=role.role_name, tenant_operator=True)
                        helper.setup_msp_user(workloads=False, role=role.role_name, tenant_operator=True)
                    helper.setup_tags(as_reseller=True)
                    helper.setup_tags(as_reseller=False)
                    helper.verify_sync_continous(timeout=self.timeout)
                    success = True
                finally:
                    helper.clean_up()
                    self.log.info(f"------------SYNC TEST "
                                  f"{'SUCCESSFULL' if success else 'FAILED'} FROM LEVEL {level}---------------------")
        finally:
            self.rr_helper.clean_up()
