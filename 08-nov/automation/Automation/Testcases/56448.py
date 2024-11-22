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

"""
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing the test case of -------------"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online- Pseudo Client - Manual Discovery "
        self.sp_client_object = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.graph_client_id = self.tcinputs.get("GraphClientId", "")
            self.sp_client_object.graph_client_secret = self.tcinputs.get("GraphClientSecret", "")
            self.sp_client_object.graph_tenant_id = self.tcinputs.get("GraphTenantId", "")
            self.log.info('SharePoint client object created.')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def validate_content_under_add_web_apps(self):
        """Checks whether content is available under web apps"""
        # Discovery_type=7,  (for all Web/Sites) Associated or Non-Associated Content
        discovery_type = 7
        site_dict = self.sp_client_object.cvoperations.check_sites_under_add_webs(discovery_type)
        if site_dict:
            self.log.info("Content available under add web apps")
        else:
            raise CVTestStepFailure("Content is not available under add web apps")

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.sp_client_object.cvoperations.add_share_point_pseudo_client()
        self.log.info("Pseudo Client has been created successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Triggered manual discovery successfully")
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.log.info("Manual Discovery is done successfully")
            self.sp_client_object.validate_site_collections()
            self.log.info("Validated site collections successfully")
            self.validate_content_under_add_web_apps()
            self.log.info("Content checked successfully")
            self.sp_client_object.cvoperations.validate_additional_service_accounts()
            self.log.info("Validated users created successfully")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
