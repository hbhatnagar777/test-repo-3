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
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore


class TestCase(CVTestCase):
    """Class for executing the test case of SharePoint V2 - Checking if Staging is Deleted Successfully
        after Backup/Restore/CI Completion
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
        self.name = "Office365- SharePoint Online - Check Staging Deletion after Backup/Restore/CI"
        self.sp_client_object = None
        self.restore_obj = None
        self.testdata = None
        self.source_machine = None

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
            self.testdata = TestData(self.sp_client_object)
            self.log.info('SharePoint client object created.')
            self.restore_obj = Restore(self.sp_client_object)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        if self.sp_client_object.site_url_list:
            site_url_list = self.sp_client_object.site_url_list
        else:
            site_url_list = [self.sp_client_object.site_url]
        self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, list=True)

    def check_staging_successfully_deleted(self, job_id, backup=True):
        """Changes JR directory of the client"""
        staging_path_details = self.tcinputs.get('StagingPathDetails', {})
        if backup:
            staging_dir = staging_path_details.get('Path') + '\\' + job_id + '\\' + 'SP-Backup'
        else:
            staging_dir = staging_path_details.get('Path') + '\\' + job_id + '\\' + 'SP-Restore'
        self.log.info(
            'Staging Directory is: {}'.format(staging_dir))
        staging_machine = Machine(staging_path_details.get('Machine'), self.commcell)
        staging_size = staging_machine.get_folder_size(staging_dir)
        if staging_size > 0:
            return False
        else:
            return True

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])

            # Backup Job
            backup_job = self.sp_client_object.cvoperations.run_backup()
            if self.check_staging_successfully_deleted(backup_job.job_id):
                self.log.info('Staging is deleted after backup completes')
            else:
                raise Exception("Staging not deleted after backup completes")

            # Content Indexing Job
            ci_job = self.sp_client_object.cvoperations.get_latest_ci_job()
            ci_job.wait_for_completion()
            if self.check_staging_successfully_deleted(ci_job.job_id, backup=False):
                self.log.info('Staging is deleted after Content Indexing completes')
            else:
                raise Exception("Staging not deleted after Content Indexing completes")

            # Restore Job
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=[self.sp_client_object.site_url])
            restore_job = self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "showDeletedItems": True},
                folder=True, list=True, v2_restore=True)
            if self.check_staging_successfully_deleted(restore_job.job_id, backup=False):
                self.log.info('Staging is deleted after restore completes')
            else:
                raise Exception("Staging not deleted after restore completes")

            self.log.info('Staging Deletion Testcase Verified Successfully')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")