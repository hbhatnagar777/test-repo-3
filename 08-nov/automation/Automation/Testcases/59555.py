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
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore


class TestCase(CVTestCase):
    """Class for executing the test case of Office365- SharePoint Online- Restore Options
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
        self.name = "Office365- SharePoint Online- Restore Options"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None
        self.oop_restore_site = None

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
            self.oop_restore_site = self.tcinputs.get("OOPRestoreSite", "")
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def validate_disk_restore_native_files(self):
        self.log.info("Starting disk restore of type native files")
        paths = self.restore_obj.get_path_for_restore(folder=True, list=True)
        self.sp_client_object.cvoperations.disk_restore(paths=paths,
                                                        destination_client=self.tcinputs['DiskRestoreClient'],
                                                        destination_path=self.tcinputs['DiskRestorePath'],
                                                        overwrite=True,
                                                        disk_restore_type=1)
        self.log.info("Comparing restore to disk as native files")
        restore_items = ["Shared Documents", self.testdata.json_value.List.TITLE]
        self.restore_obj.compare_restore_disk_native_files(
            restore_items,
            self.tcinputs['DiskRestoreClient'],
            self.tcinputs['DiskRestorePath'],
            num_of_backups=2)
        self.log.info("Restore to disk as native files is validated")

    def validate_disk_restore_original_files(self):
        self.log.info("Starting disk restore of type original files")
        paths = self.restore_obj.get_path_for_restore(folder=True, v2_restore=True)
        self.sp_client_object.cvoperations.disk_restore(paths=paths,
                                                        destination_client=self.tcinputs['DiskRestoreClient'],
                                                        destination_path=self.tcinputs['DiskRestorePath'],
                                                        overwrite=True,
                                                        disk_restore_type=2)

        self.log.info("Comparing restore to disk as original files")
        destination_machine_obj = Machine(self.tcinputs["DiskRestoreClient"], self.commcell)
        site_metadata = self.testdata.testdata_metadata.get(self.sp_client_object.site_url, {})
        site_path = self.sp_client_object.site_url.split("//")[1].replace("/", "_")
        root_path = destination_machine_obj.join_path(self.tcinputs['DiskRestorePath'], site_path, "Contents")

        self.restore_obj.compare_restore_disk_original_files(machine_obj=destination_machine_obj,
                                                             testdata_metadata=(site_metadata.get("Folder") or [{}])[0],
                                                             parent_dir=root_path)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        if self.sp_client_object.site_url_list:
            site_url_list = self.sp_client_object.site_url_list
        else:
            site_url_list = [self.sp_client_object.site_url]
        self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, list=True,
                                                       special_data_folder=True, versions=False)

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(self.sp_client_object.office_365_plan[0][1])
            job_1_obj = self.sp_client_object.cvoperations.run_backup()
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=[self.sp_client_object.site_url])
            self.log.info("Validating Restore to disk as original files")
            self.validate_disk_restore_original_files()
            self.log.info("Restore to disk as original files is validated")
            deleted_objects_count = self.testdata.modify_backup_content(folder=True, list=True)
            self.sp_client_object.cvoperations.run_backup(deleted_objects_count=deleted_objects_count)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=[self.sp_client_object.site_url])
            self.testdata.modify_backup_content(folder=True, list=True)
            self.log.info("Validating Skip Restore Option")
            self.restore_obj.restore_and_validate_sharepoint_content(folder=True, list=True, v2_restore=True)
            self.log.info("Skip Restore Option is validated")
            self.log.info("Validating Unconditional Overwrite Option")
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={"overwrite": True}, folder=True,
                                                                     backup_metadata_index=-2, list=True, v2_restore=True)
            self.log.info("Unconditional Overwrite Restore Option is validated")
            self.sp_client_object.site_url = self.oop_restore_site[0]
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.sp_client_object.site_url = self.tcinputs['SiteUrl']
            self.log.info("Validating OOP Restore Option")
            restore_args = {
                "destination_site": self.oop_restore_site[0],
                "destination_site_title": self.oop_restore_site[1]
            }
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args=restore_args, folder=True, list=True,
                                                                     backup_metadata_index=-2, v2_restore=True)
            self.log.info("OOP Restore Option is validated")
            self.log.info("Validating Point in Time restore")
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "showDeletedItems": True,
                "to_time": job_1_obj.end_timestamp},
                folder=True, list=True,
                backup_metadata_index=-3, v2_restore=True)
            self.log.info("Point in time restore is validated")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.testdata.delete_disk_files()
            self.testdata.delete_backup_site_structure(folder=True, list=True, site_url_list=[
                self.sp_client_object.site_url,
                self.oop_restore_site[0]])
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                (self.sp_client_object.pseudo_client_name)
