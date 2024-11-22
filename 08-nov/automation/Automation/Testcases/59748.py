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
from Application.Sharepoint import sharepointconstants
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore


class TestCase(CVTestCase):
    """Class for executing the test case of
    Office365- SharePoint Online - Exclude/Remove sites - Basic Case
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
        self.name = "Office365- SharePoint Online - Exclude/Remove sites - Basic Case"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None
        self.deleted_items = 0

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365Plan')).plan_id))]
            self.sp_client_object.site_url_list = self.tcinputs.get("SiteUrlList", [])
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.testdata = TestData(self.sp_client_object)
            self.restore_obj = Restore(self.sp_client_object)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def delete_backup_content(self):
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.testdata.delete_backup_content(folder=True, list=True)

    def modify_backup_content(self):
        self.deleted_items = 0
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.deleted_items += self.testdata.modify_backup_content(folder=True, list=True)

    def modify_content_before_restore(self):
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.testdata.modify_content_before_restore(folder=True, list=True)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        if self.sp_client_object.site_url_list:
            site_url_list = self.sp_client_object.site_url_list
        else:
            site_url_list = [self.sp_client_object.site_url]
        self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, list=True,
                                                       versions=False)

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.sp_client_object.cvoperations.associates_sites_for_backup(
                sites_list=self.sp_client_object.site_url_list,
                office_365_plan_id=self.sp_client_object.office_365_plan[0][1])
            self.sp_client_object.cvoperations.exclude_sites_from_backup([self.sp_client_object.site_url_list[0]])
            job_id_1 = self.sp_client_object.cvoperations.run_backup()
            self.sp_client_object.cvoperations.validate_num_webs_in_backup(job_id_1, 2)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=self.sp_client_object.site_url_list[1:],
                exclude_browse_paths=[self.sp_client_object.site_url_list[0]])
            # self.modify_backup_content()
            self.sp_client_object.cvoperations.include_sites_in_backup([self.sp_client_object.site_url_list[0]])
            self.sp_client_object.cvoperations.exclude_sites_from_backup([self.sp_client_object.site_url_list[1]])
            self.sp_client_object.cvoperations.remove_sites_from_backup_content([self.sp_client_object.site_url_list[2]])
            job_id_2 = self.sp_client_object.cvoperations.run_backup(deleted_objects_count=self.deleted_items)
            self.sp_client_object.cvoperations.validate_num_webs_in_backup(job_id_2, 1)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=self.sp_client_object.site_url_list)
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            # backup_metadata_index_list = [-1, -2, -2]

            for i in range(len(self.sp_client_object.site_url_list)):
                self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
                self.restore_obj.restore_and_validate_sharepoint_content(restore_args={"showDeletedItems": True},
                                                                         folder=True, list=True,
                                                                         v2_restore=True)
            self.sp_client_object.cvoperations.remove_sites_from_backup_content(self.sp_client_object.site_url_list)
            sites, no_of_records = self.sp_client_object.cvoperations.subclient.browse_for_content(discovery_type=6)
            if no_of_records != 0 and len(sites) != 0:
                raise Exception("No. of associated sites is not equal to 0")
            self.log.info("No. of associated sites is 0 as expected")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.testdata.delete_backup_site_structure(folder=True, list=True)
            self.testdata.delete_disk_files()
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client\
                (self.sp_client_object.pseudo_client_name)
