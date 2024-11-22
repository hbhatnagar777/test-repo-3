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
from Application.Office365.solr_helper import CVSolr
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore


class TestCase(CVTestCase):
    """Class for executing the test case of
    Office365- SharePoint Online - O365 Plan - Retention – Basic Case
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
        self.name = "Office365- SharePoint Online - O365 Plan - Retention – Basic Case"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None
        self.deleted_objects_count = 0

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(plan, int(self.sp_client_object.cvoperations.get_plan_obj(plan).plan_id))
                                                     for plan in self.tcinputs.get('Office365PlanList')]
            self.sp_client_object.site_url_list = self.tcinputs.get("SiteUrlList", [])
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
            self.testdata = TestData(self.sp_client_object)
            self.restore_obj = Restore(self.sp_client_object)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def associate_sites(self):
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[i][1])

    def delete_backup_content(self):
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.deleted_objects_count += self.testdata.delete_backup_content(delete_folder=True, delete_list=True)

    def get_browse_paths(self):
        browse_paths = []
        for site in self.sp_client_object.site_url_list:
            browse_paths.extend([site + "\\Contents\\Shared Documents\\59747 - Test Automation Folder",
                                 site + "\\Contents\\Shared Documents\\59747 - Test Automation Folder\\"
                                        "59747 - Test Automation File 1.txt",
                                 site + "\\Contents\\59747 Test Automation List",
                                 site + "\\Contents\\59747 Test Automation List\\1_.000"])
        return browse_paths

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        if self.sp_client_object.site_url_list:
            site_url_list = self.sp_client_object.site_url_list
        else:
            site_url_list = [self.sp_client_object.site_url]
        self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, list=True)

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.associate_sites()
            self.sp_client_object.cvoperations.run_backup()
            self.delete_backup_content()
            self.sp_client_object.cvoperations.run_backup(deleted_objects_count=self.deleted_objects_count)
            self.deleted_objects_count = 0
            browse_paths = self.get_browse_paths()
            self.restore_obj.browse_restore_content_and_verify_browse_response(exclude_browse_paths=browse_paths)
            self.restore_obj.browse_restore_content_and_verify_browse_response(browse_paths=browse_paths, browse_args={
                'show_deleted': True
            })
            solr = CVSolr(self.sp_client_object)
            site_dict_with_o365_plan_retention = {}
            for site, plan in zip(self.sp_client_object.site_url_list, self.sp_client_object.office_365_plan):
                plan_obj = self.sp_client_object.cvoperations.get_plan_obj(plan[0])
                retention_period = plan_obj._properties['office365Info']['o365CloudOffice']['caRetention']['detail']\
                    ['cloudAppPolicy']['retentionPolicy']['numOfDaysForMediaPruning']
                site_dict_with_o365_plan_retention[site] = retention_period
            self.log.info(f"Sites along with their retention period: {site_dict_with_o365_plan_retention}")
            solr.validate_retention(site_dict_with_o365_plan_retention)
            browse_paths_partition_index = len(browse_paths)//len(self.sp_client_object.site_url_list)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=browse_paths[browse_paths_partition_index:],
                exclude_browse_paths=browse_paths[:browse_paths_partition_index],
                browse_args={'show_deleted': True})
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
