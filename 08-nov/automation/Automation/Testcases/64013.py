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
import time

from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
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
        self.name = "Office365- SharePoint Online - Advanced Delete Data Verification"
        self.sp_client_object = None
        self.restore_obj = None
        self.testdata = None
        self.source_machine = None
        self.files_delete = None
        self.search_and_delete = None
        self.folder_delete = None
        self.deleted_folder_delete = None

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
            self.files_delete = self.tcinputs.get('FilesDelete')
            self.search_and_delete = self.tcinputs.get('SearchAndDelete')
            self.folder_delete = self.tcinputs.get('FolderDelete')
            self.deleted_folder_delete = self.tcinputs.get('DeletedFolderDelete')

            # Initialize proper Url paths from Relative Url Paths
            for index in range(len(self.files_delete)):
                self.files_delete[index] = self.sp_client_object.site_url + "\\Contents\\Shared Documents\\" + \
                                           self.files_delete[index]
            for index in range(len(self.search_and_delete)):
                self.search_and_delete[index] = self.sp_client_object.site_url + "\\Contents\\Shared Documents\\" + \
                                                self.search_and_delete[index]
            for index in range(len(self.folder_delete["ToDelete"])):
                self.folder_delete["ToDelete"][index] = self.sp_client_object.site_url + \
                                                        "\\Contents\\Shared Documents\\" + \
                                                        self.folder_delete["ToDelete"][index]
            for index in range(len(self.folder_delete["Exist"])):
                self.folder_delete["Exist"][index] = self.sp_client_object.site_url + \
                                                     "\\Contents\\Shared Documents\\" + \
                                                     self.folder_delete["Exist"][index]
            for index in range(len(self.folder_delete["NotExist"])):
                self.folder_delete["NotExist"][index] = self.sp_client_object.site_url + \
                                                        "\\Contents\\Shared Documents\\" + \
                                                        self.folder_delete["NotExist"][index]
            for index in range(len(self.deleted_folder_delete["ToDelete"])):
                self.deleted_folder_delete["ToDelete"][index] = self.sp_client_object.site_url + \
                                                                "\\Contents\\Shared Documents\\" + \
                                                                self.deleted_folder_delete["ToDelete"][index]
            for index in range(len(self.deleted_folder_delete["NotExist"])):
                self.deleted_folder_delete["NotExist"][index] = self.sp_client_object.site_url + \
                                                                "\\Contents\\Shared Documents\\" + \
                                                                self.deleted_folder_delete["NotExist"][index]
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        if self.sp_client_object.site_url_list:
            site_url_list = self.sp_client_object.site_url_list
        else:
            site_url_list = [self.sp_client_object.site_url]
        self.testdata.create_site_structure_for_backup(site_url_list=site_url_list, folder=True, versions=False)

    def check_if_present_on_sharepoint_site(self, item, is_present):
        item = "/" + item.replace("\\", "/").replace("/Contents", "").split("/", 3)[-1]
        if item.endswith(".txt"):
            item = item.rsplit('/', 1)
            res = self.sp_client_object.get_sp_file_metadata(item[1], item[0])
        else:
            res = self.sp_client_object.get_sp_folder_metadata(item)
            if res:
                res = True
        if res != is_present:
            if is_present:
                self.log.error(f"{item} is expected to be present but is NOT")
                raise Exception(f"{item} is expected to be present but is NOT")
            else:
                self.log.error(f"{item} is expected to not be present but is PRESENT")
                raise Exception(f"{item} is expected to not be present but is PRESENT")

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])

            # Backup Job and set base Solr URL
            self.sp_client_object.cvoperations.run_backup()
            self.restore_obj.solr_obj.set_cvsolr_base_url()

            # Check data present in browse
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=self.files_delete + self.search_and_delete + self.folder_delete["ToDelete"] + self.deleted_folder_delete["ToDelete"])

            # Delete at file/item level
            file_guids = []
            for path in self.files_delete:
                file_guids.append(self.restore_obj.extract_guid("MB\\" + path))
            self.sp_client_object.cvoperations.delete_sharepoint_backup_data(file_guids)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                exclude_browse_paths=self.files_delete)
            self.log.info("Delete item at file/item level is verified SUCCESSFULLY")

            # Search and delete all (BULK JOB)
            site_guid = [self.restore_obj.extract_guid("MB\\" + self.sp_client_object.site_url, search_and_delete_all=True)]
            job1 = self.sp_client_object.cvoperations.delete_sharepoint_backup_data(site_guid,
                                                                                          search_string="Weird",
                                                                                          search_and_delete_all=True)
            self.log.info(f"Index Delete job with id {job1.job_id} launched ")
            time.sleep(10)
            if job1.status.lower():
                self.restore_obj.browse_restore_content_and_verify_browse_response(
                    exclude_browse_paths=self.search_and_delete)
                self.log.info("Index Delete Job completed successfully")
            else:
                raise Exception("Search and delete all data FAILED")
            self.log.info("Search and delete all is verified SUCCESSFULLY")

            # delete at folder level (one folder and file) which is present in source site (BULK JOB)
            folder_and_file_guids = []
            for path in self.folder_delete["ToDelete"]:
                folder_and_file_guids.append(self.restore_obj.extract_guid("MB\\" + path))
            job2 = self.sp_client_object.cvoperations.delete_sharepoint_backup_data(folder_and_file_guids,
                                                                                          folder_delete=True)
            self.log.info(f"Index Delete job with id {job2.job_id} launched ")
            time.sleep(10)
            if job2.status.lower() == 'completed':
                self.restore_obj.browse_restore_content_and_verify_browse_response(
                    browse_paths = self.folder_delete["Exist"],
                    exclude_browse_paths=self.folder_delete["NotExist"])
                self.log.info("Index Delete Job completed successfully")
            else:
                raise Exception("Delete item at folder level which is present in source site FAILED")
            self.log.info("Delete item at folder level which is present in source site is verified SUCCESSFULLY")

            # delete at folder level which does NOT exist on source site (BULK JOB)
            folder_path = self.deleted_folder_delete["ToDelete"][0]
            delete_from_sp_path = '/' + folder_path.replace("\\", "/").split("/", 3)[3].replace("/Contents", "")
            self.sp_client_object.delete_sp_file_or_folder(delete_from_sp_path)
            self.log.info(f"Deleted the existing folder {delete_from_sp_path}")
            self.sp_client_object.cvoperations.run_backup(deleted_objects_count=1)
            folder_path = self.deleted_folder_delete["ToDelete"][0]
            folder_guid = [self.restore_obj.extract_guid("MB\\" + folder_path)]
            job3 = self.sp_client_object.cvoperations.delete_sharepoint_backup_data(folder_guid,
                                                                                          folder_delete=True)
            self.log.info(f"Index Delete job with id {job3.job_id} launched ")
            time.sleep(10)
            if job3.status.lower() == 'completed':
                self.restore_obj.browse_restore_content_and_verify_browse_response(
                    exclude_browse_paths=self.folder_delete["NotExist"])
                self.log.info("Index Delete Job completed successfully")
            else:
                raise Exception("Delete item at folder level which is NOT present in source site FAILED")
            self.log.info("Delete item at folder level which is NOT present in source site is verified SUCCESSFULLY")

            # CHECK ITEM_STATE of DELETED ITEMS
            should_be_deleted = self.files_delete + self.search_and_delete + self.folder_delete["NotExist"] + \
                                self.deleted_folder_delete["NotExist"]
            for deleted_item in should_be_deleted:
                state = self.restore_obj.extract_state_of_item("MB\\" + deleted_item)
                if state == "False,3334" or state == "False,3335":
                    self.log.info(f"state of {deleted_item} is verified on index")
                else:
                    raise Exception(f"State of {deleted_item} is not marked as deleted and/or is still visible")

            # CHECK ITEM_STATE of PRESENT ITEMS
            should_be_present = self.folder_delete["Exist"]
            for present_item in should_be_present:
                state = self.restore_obj.extract_state_of_item("MB\\" + present_item)
                if state == "True,1":
                    self.log.info(f"state of {present_item} is verified on index")
                else:
                    raise Exception(f"State of {present_item} is not marked as present and/or is not visible")

            # Restore Job
            self.testdata.delete_backup_site_structure(folder=True, force=True)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=[self.sp_client_object.site_url])
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "paths": ["MB\\" + self.sp_client_object.site_url],
                "showDeletedItems": True},
                v2_restore=True)
            for item in should_be_present:
                self.check_if_present_on_sharepoint_site(item, True)
            for item in should_be_deleted:
                self.check_if_present_on_sharepoint_site(item, False)

            self.log.info('Advanced Delete Data Testcase Verified Successfully')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
