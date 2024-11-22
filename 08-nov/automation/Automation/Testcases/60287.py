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
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "TEST_SharePoint"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating SharePoint client object.')
        self.sp_client_object = SharePointOnline(self)
        self.sp_client_object.initialize_sp_v1_client_attributes()

        # SharePoint Site details
        self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
        self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
        self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
        self.log.info('SharePoint client object created.')

        self.testdata = TestData(self.sp_client_object)
        self.restore_obj = Restore(self.sp_client_object)
        if self.sp_client_object.site_url_list:
            site_url_list = self.sp_client_object.site_url_list
        else:
            site_url_list = [self.sp_client_object.site_url]
        self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, list=True,
                                                       versions=True)

    def run(self):
        """Run function of this test case"""
        try:

            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.validate_client_creation()
            self.sp_client_object.cvoperations.browse_for_sp_sites(paths=["\\MB"])
            self.sp_client_object.cvoperations.associate_content_for_backup(content=self.tcinputs.get("Content", []))
            self.sp_client_object.cvoperations.run_backup()
            self.testdata.modify_backup_content(folder=True, list=True)
            self.sp_client_object.cvoperations.run_backup()
            self.testdata.modify_content_before_restore(folder=True, list=True)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=[self.sp_client_object.site_url])
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "overwrite": True,
                "showDeletedItems": True},
                folder=True, list=True)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.testdata.delete_disk_files()
            self.testdata.delete_backup_site_structure(folder=True, list=True)
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client(
                self.sp_client_object.pseudo_client_name)
