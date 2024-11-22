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
    """Class for executing the test case of SharePoint V2 - Basic Acceptance Test for Moving Job Results Directory
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
        self.name = "Office365- SharePoint V2 - Basic Acceptance Test for Moving Job Results Directory"
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
            self.log.info('SharePoint client object created.')
            self.testdata = TestData(self.sp_client_object)
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
        self.source_machine = Machine(self.sp_client_object.job_results_directory.get('Machine'), self.commcell)
        self.sp_client_object.job_results_directory['Path'] = self.create_directory_and_get_share_directory(
            self.source_machine, self.sp_client_object.job_results_directory.get('FolderName'))

    def create_directory_and_get_share_directory(self, machine_obj, folder_name):
        """Creates a directory and returns share directory path with full control to everyone"""
        directory = "C:\\{0}".format(folder_name)
        job_result_directory = directory + "\\JobResults"
        self.log.info("Creating local directory and sharing it with full control")
        machine_obj.create_directory(directory_name=directory, force_create=True)
        machine_obj.create_directory(directory_name=job_result_directory, force_create=True)
        try:
            machine_obj.share_directory(share_name=folder_name, directory=directory)
        except Exception:
            # sometimes sharing of above created directory is failing with unknown reason, but when checked after
            # above method call, the directory is shared
            pass
        return "\\\\{0}\\{1}\\JobResults".format(machine_obj.machine_name, folder_name)

    def change_jr_directory(self):
        """Changes JR directory of the client"""
        job_results_dir = self.sp_client_object.cvoperations.get_job_results_dir()
        self.log.info(
            'Initial Job Result Directory is: {}'.format(job_results_dir))
        new_shared_path_details = self.tcinputs.get('NewSharedJRDirectoryDetails', {})
        destination_machine = Machine(new_shared_path_details.get('Machine'), self.commcell)
        destination_jr_dir = self.create_directory_and_get_share_directory(destination_machine,
                                                                           new_shared_path_details.get('FolderName'))
        self.sp_client_object.cvoperations.client.change_o365_client_job_results_directory(
            new_directory_path=destination_jr_dir,
            username=new_shared_path_details.get('Username', None),
            password=new_shared_path_details.get('Password', None))
        self.log.info('Job Result Directory changed successfully')
        self.sp_client_object.cvoperations.wait_for_process_to_complete(
            machine_name=new_shared_path_details.get('Machine'),
            time_out=900,
            process_name=sharepointconstants.MOV_DIR_PROCESS_NAME)
        # self.sp_client_object.machine_name = new_shared_path_details.get('Machine')
        # self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
        self.sp_client_object.cvoperations.client.refresh()
        self.log.info('Refreshed the client object')
        new_job_results_dir = self.sp_client_object.cvoperations.get_job_results_dir()
        self.log.info(
            'New Job Result Directory is: {}'.format(new_job_results_dir))
        if not new_job_results_dir.startswith(destination_jr_dir):
            raise Exception("Job Results Directory is not moved to correct destination")
        diff = self.source_machine.compare_folders(
            destination_machine=destination_machine,
            source_path=job_results_dir,
            destination_path=new_job_results_dir)
        if diff:
            self.log.error('The difference of files after moving jr directory', diff)

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])
            full_bkp_job = self.sp_client_object.cvoperations.run_backup()
            self.change_jr_directory()
            deleted_objects_count = self.testdata.modify_backup_content(folder=True, list=True)
            incremental_bkp_job = self.sp_client_object.cvoperations.run_backup(deleted_objects_count=deleted_objects_count)
            if int(incremental_bkp_job.summary['totalNumOfFiles']) >= int(full_bkp_job.summary['totalNumOfFiles']):
                raise Exception("Total number of files in incremental job are more than full job which is not expected")
            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=[self.sp_client_object.site_url])
            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "showDeletedItems": True},
                folder=True, list=True, v2_restore=True)
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.testdata.delete_disk_files()
            self.testdata.delete_backup_site_structure(folder=True, list=True)
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client\
                (self.sp_client_object.pseudo_client_name)
