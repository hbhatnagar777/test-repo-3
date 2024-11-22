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
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing the test case of Office365- SharePoint Online- Incremental Backup on a Persistent Client
    """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online- Incremental Backup on a Persistent Client"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None
        self.machine_obj = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365Plan')).plan_id))]
            self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
            self.testdata = TestData(self.sp_client_object)
            self.restore_obj = Restore(self.sp_client_object)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.validate_pseudo_client_present()
            self.log.info("Presence of Pseudo Client has been verified successfully")
            self.sp_client_object.cvoperations.browse_for_sp_sites()

            associated_sites, _ = self.sp_client_object.cvoperations.check_sites_under_add_webs(discovery_type=6)
            if self.sp_client_object.site_url not in associated_sites:
                self.log.info('Previously associated site missing: %s', self.sp_client_object.site_url)
                raise Exception(f'Client {self.sp_client_object.site_url} is missing from association')
            if self.sp_client_object.office_365_plan[0][0] != associated_sites[self.sp_client_object.site_url]['planName']:
                self.log.info('Previously associated site had different plan: %s',
                              self.sp_client_object.office_365_plan[0][1])
                raise Exception(f'Client {self.sp_client_object.site_url} is associated with a different plan than expected')

            self.log.info(f'Presence of previously associated site: {self.sp_client_object.site_url} has been '
                          f'verified successfully with plan {self.sp_client_object.office_365_plan[0][0]}')

            if self.sp_client_object.site_url_list:
                site_url_list = self.sp_client_object.site_url_list
            else:
                site_url_list = [self.sp_client_object.site_url]
            self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, list=True, versions=False)

            job = self.sp_client_object.cvoperations.run_backup(deleted_objects_count=2)
            if job.num_of_files_transferred == 0:
                raise Exception(f'Incremental backup with job id {job.job_id} did not backup any data')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.testdata.delete_disk_files()
