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
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing the test case of
    Office365- SharePoint V2 - Restartability - Suspend and Resume Case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online - Restartability - Suspend and Resume Case"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None
        self.site_url_list = []
        self.subsite_end_url_list = []

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
        self.site_url_list, _ = self.testdata.create_test_subsites(num_of_sites=4)
        self.subsite_end_url_list = self.testdata.get_subsites_end_url_list(self.site_url_list[1:])
        self.testdata.create_site_structure_for_backup(site_url_list=self.site_url_list,
                                                       folder=True, list=True,
                                                       large_files_size=5242880, versions=False)
        self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])
            total_webs = len(self.site_url_list)
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.sp_client_object.cvoperations.suspend_resume_job(total_webs, 2)
            self.sp_client_object.cvoperations.validate_backup_reference_time()
            subsite_browse_list = []
            for site in self.subsite_end_url_list:
                subsite_browse_list.append(self.sp_client_object.site_url + "\\Subsites\\" + site)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=subsite_browse_list)
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.sp_client_object.delete_subsites(subsite_end_url_list=self.subsite_end_url_list)
            self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
            paths = [
                "MB\\" + self.sp_client_object.site_url + "\\Contents",
                "MB\\" + subsite_browse_list[1],
                "MB\\" + subsite_browse_list[3]
            ]
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "paths": paths,
            }, folder=True, list=True, v2_restore=True)
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
            self.sp_client_object.delete_subsites(self.subsite_end_url_list)
            self.log.info("Cleaned up all test sub sites")
            self.testdata.delete_backup_site_structure(folder=True, list=True)
            self.testdata.delete_disk_files()
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client\
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
