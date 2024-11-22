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
from random import choice
from AutomationUtils.cvtestcase import CVTestCase
from Server.MultiCommcell.ring_routing_helper import RingRoutingHelperAPI


class TestCase(CVTestCase):
    """Class for executing Ring Routing: Company Properties Sync [Themes, DLP, Autodiscovery]"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.timeout = 60 * 5
        self.reseller = None
        self.reseller_login = None
        self.name = "Ring Routing: All Properties Sync Of Reseller [API]"
        self.rr_helper = None
        self.tcinputs = {}

    def setup(self):
        """setup function for this testcase"""
        self.reseller = self.tcinputs.get("company")
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
            random_coinflip = choice([True, False])
            # SETTING DLP, AUTODISCOVERY
            self.rr_helper.modify_dlp(as_reseller=random_coinflip)
            self.rr_helper.modify_autodiscovery(as_reseller=(not random_coinflip))

            # SETTING THEME FROM MSP AND RESELLER LEVELS
            self.rr_helper.setup_theme(as_reseller=random_coinflip)
            self.rr_helper.verify_sync_continous(timeout=self.timeout)
            self.rr_helper.setup_theme(as_reseller=(not random_coinflip))

            # PREPARING CONTACTS
            for x in [True, False]:
                for y in [True, False]:
                    self.rr_helper.setup_company_user(
                        as_reseller=x, workloads=y, tenant_admin=True, add_contact=True
                    )

            # PREPARING ROLES AND OPERATORS
            roles = [
                self.rr_helper.setup_role(workloads=x, as_reseller=y)
                # ONLY USING RESELLER CREATED ROLES TO AVOID ROLE PERMISSION CONFLICT CASES
                for x in [True, False] for y in [True, False]
            ]

            for role in roles:
                self.rr_helper.setup_msp_user(workloads=True, role=role.role_name, tenant_operator=True)
                self.rr_helper.setup_msp_user(workloads=False, role=role.role_name, tenant_operator=True)

            # PREPARING TAGS
            self.rr_helper.setup_tags(as_reseller=True)
            self.rr_helper.setup_tags(as_reseller=False)

            # SYNC VERIFICATIONS
            self.rr_helper.verify_sync_continous(timeout=self.timeout)

        finally:
            self.rr_helper.clean_up()
