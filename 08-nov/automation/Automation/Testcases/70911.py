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

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Application.Sharepoint.sharepoint_online import SharePointOnline
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore
from Web.Common.exceptions import CVTestCaseInitFailure
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing the test case of Office365: SharePoint Online - Restore backup cycle dependency validation
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
        self.name = "Office365: SharePoint Online - Restore backup cycle dependency validation"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None

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
            self.log.info('SharePoint client object created.')
            self.testdata = TestData(self.sp_client_object)
            self.restore_obj = Restore(self.sp_client_object)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.testdata.create_site_structure_for_backup(site_url_list=self.sp_client_object.site_url_list, folder=True,
                                                       list=False, versions=False)

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()

            for site in self.sp_client_object.site_url_list:
                self.sp_client_object.site_url = site
                self.sp_client_object.cvoperations.browse_for_sp_sites()
                self.sp_client_object.cvoperations.associate_content_for_backup(
                    self.sp_client_object.office_365_plan[0][1])

            self.sp_client_object.cvoperations.run_backup()

            self.testdata.update_files()
            self.sp_client_object.cvoperations.run_backup()

            self.testdata.update_files()
            self.testdata.edit_folder_name()
            self.sp_client_object.cvoperations.run_backup()

            self.testdata.update_files()
            self.testdata.edit_library_description()
            self.sp_client_object.cvoperations.run_backup()

            self.testdata.update_files()
            self.testdata.edit_site_description()
            self.sp_client_object.cvoperations.run_backup()

            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=self.sp_client_object.site_url_list)
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                    "overwrite": True, "latest_version": False},
                file=True, v2_restore=True, validate_restore_vectors=True, file_versions=5)
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client(self.sp_client_object.pseudo_client_name)
        self.testdata.delete_backup_site_structure(folder=True, site_url_list=self.sp_client_object.site_url_list)
