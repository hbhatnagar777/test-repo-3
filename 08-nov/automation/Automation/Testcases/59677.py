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
    Office365- SharePoint V2 - Finalize Phase - Advance Case - Web commit after job kill"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online - Finalize Phase - Advance Case - Web commit after job kill"
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
        self.site_url_list, _ = self.testdata.create_test_subsites()
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
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            # restricting streams count for kill case
            num_webs_to_be_processed_to_kill_job = 1
            self.sp_client_object.cvoperations.subclient.data_readers = num_webs_to_be_processed_to_kill_job
            job = self.sp_client_object.cvoperations.run_backup(wait_for_job_to_complete=False)
            self.sp_client_object.cvoperations.wait_time(60, f"Waiting for backup to start")
            self.sp_client_object.cvoperations.monitor_job_advance_details(job, num_webs_to_be_processed_to_kill_job)
            self.sp_client_object.cvoperations.kill_job(job)
            if job.status != 'Committed':
                self.log.exception(f"Job status is reported as {job.status} but not Committed")
                raise Exception(f"Job status is reported as {job.status} but not Committed")
            self.sp_client_object.cvoperations.check_playback_completion(job.job_id)
            committed_webs = self.sp_client_object.cvoperations.get_committed_webs_list(job_id=job.job_id)
            uncommitted_webs = [site for site in self.site_url_list if site not in committed_webs]
            self.sp_client_object.cvoperations.validate_backup_reference_time(uncommitted_webs)
            committed_webs = self.testdata.get_subsites_end_url_list(committed_webs)
            uncommitted_webs = self.testdata.get_subsites_end_url_list(uncommitted_webs)
            self.restore_obj.validate_browse_for_restore(include_subsite_end_url_list=committed_webs)
            self.sp_client_object.cvoperations.run_backup()
            self.sp_client_object.cvoperations.validate_backup_reference_time()
            self.restore_obj.validate_browse_for_restore(
                include_subsite_end_url_list=committed_webs + uncommitted_webs)
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.sp_client_object.delete_subsites(subsite_end_url_list=self.subsite_end_url_list)
            self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
            paths = [
                "MB\\" + self.sp_client_object.site_url + "\\Contents",
                "MB\\" + self.sp_client_object.site_url + "\\Subsites\\" + self.subsite_end_url_list[0],
            ]
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "paths":  paths,
            }, folder=True, list=True,
                sites_to_validate=self.site_url_list[:-1], v2_restore=True)
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
