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
from Web.Common.exceptions import CVTestStepFailure
from Application.Sharepoint import sharepointconstants as const
from AutomationUtils.windows_machine import WindowsMachine
import time


class TestCase(CVTestCase):
    """Class for executing the test case of  Office365- SharePoint Online Pseudo Client creation"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online- Pseudo Client Creation- General"
        self.sp_client_object = None

    def wait_for_discovery_to_complete(self):
        """ Method to wait for the completion of auto discovery
        """
        try:
            self.sp_client_object.cvoperations.wait_for_process_to_complete(
                machine_name=self.tcinputs.get('MachineName'),
                process_name=const.MANUAL_DISCOVERY_PROCESS_NAME,
                time_out=5400,
                poll_interval=60,
                cvf_file=True)
        except Exception as exception:
            self.log.error("An error occurred while waiting for auto discovery to complete")
            raise exception

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
        self.log.info("Starting test run")

    def run(self):
        """Run function of this test case"""
        try:
            cloud_regions = (
                '', 'Default (Global Service)',
                'Germany',
                'China',
                'U.S. Government GCC',
                'U.S. Government GCC High'
            )

            for i in range(1, 6):
                self.log.info('Creating SharePoint client object for {cloudRegion} region'.format(
                        cloudRegion=cloud_regions[i]))
                self.sp_client_object = SharePointOnline(self)
                self.sp_client_object.initialize_sp_v2_client_attributes()
                self.sp_client_object.graph_client_id = self.tcinputs.get("GraphClientId", "")
                self.sp_client_object.graph_client_secret = self.tcinputs.get("GraphClientSecret", "")
                self.sp_client_object.graph_tenant_id = self.tcinputs.get("GraphTenantId", "")
                self.log.info('SharePoint client object created.')

                self.sp_client_object.cvoperations.add_share_point_pseudo_client(cloud_region=i)
                self.log.info(
                    "Pseudo Client has been created successfully for {cloudRegion} region".format(
                        cloudRegion=cloud_regions[i]))
                self.sp_client_object.cvoperations.validate_client_creation()
                self.log.info("Pseudo Client validation is done successfully")
                self.sp_client_object.cvoperations.validate_additional_service_accounts()
                self.log.info("Validated users created successfully")
                self.wait_for_discovery_to_complete()
                self.validate_content_under_add_web_apps()
                self.log.info("Discovery contents verified")
                self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                    (self.sp_client_object.pseudo_client_name)
                self.log.info("Pseudo Client has been deleted successfully")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
