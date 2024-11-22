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
    """Class for executing the test case of Office365- SharePoint V2 - Site level Restore
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
        self.name = "Office365- SharePoint Online- Site level Restore"
        self.sp_client_object = None
        self.testdata = None
        self.share_point_data_flag = False
        self.restore_obj = None
        self.site_collection_data = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')

            timestamp = f"_{int(time.time())}"
            self.site_collection_data = {
                url + timestamp: {
                    "is_group": bool(i)
                } for i, url in enumerate(self.tcinputs.get("SiteUrlList")[:2])
            }

            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365Plan')).plan_id))]
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
            self.testdata = TestData(self.sp_client_object)
            self.restore_obj = Restore(self.sp_client_object)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def get_subsites_list(self):
        """Returns the list of subsites title and end url"""
        subsite_title_list = []
        for i, data in enumerate(self.site_collection_data.values()):
            subsite_title_list.append([])
            for metadata in data["subsites_metadata"].values():
                subsite_title_list[i].append((metadata['Title'], metadata['Url End']))
        return subsite_title_list

    def validate_subsites_titles(self):
        """Validates properties of subsites"""
        try:
            subsite_title_list = self.get_subsites_list()
            for i, site_collection in enumerate(self.site_collection_data):
                self.sp_client_object.site_url = site_collection
                for subsite_title, subsite_end_url in subsite_title_list[i]:
                    site_properties = self.sp_client_object.get_site_properties(subsite_end_url,
                                                                                additional_uri="Title")
                    self.log.info(f"Restored title for {subsite_end_url} is {site_properties.get('Title', '')}")
                    if site_properties.get("Title", "") == subsite_title:
                        self.log.info(f"{subsite_end_url} has title {subsite_title} as expected")
                    else:
                        self.log.exception(f"{subsite_end_url} is not restored properly")
                        raise Exception(f"{subsite_end_url} is not restored properly")
        except Exception as exception:
            self.log.exception("Exception while validating subsite properties: %s", str(exception))
            raise exception

    def create_collection(self, site_collection_url, is_group):
        """Creates a site collection, populates it with subsites and populates all the webs with test data

            Args:

                site_collection_url (str)       :   Site Collection URL

                is_group            (bool)      :   Whether to create a group site
        """
        self.log.info(f"Creating {site_collection_url}, group site: {is_group}")
        self.sp_client_object.create_sp_site_collection(site_collection_url, is_group)

        self.log.info("Populating site collection")
        data = self.site_collection_data[site_collection_url]

        self.sp_client_object.site_url = site_collection_url
        data["url_list"], data["subsites_metadata"] = self.testdata.create_test_subsites()
        data["subsite_end_url_list"] = self.testdata.get_subsites_end_url_list(data["url_list"][1:])

        self.testdata.create_site_structure_for_backup(data["url_list"], folder=True, list=True, versions=False)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        for site, data in self.site_collection_data.items():
            self.create_collection(site, is_group=data["is_group"])

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.sp_client_object.cvoperations.run_manual_discovery(True)

            for site in self.site_collection_data:
                self.sp_client_object.site_url = site
                self.sp_client_object.cvoperations.browse_for_sp_sites()
                self.sp_client_object.cvoperations.associate_content_for_backup(
                    self.sp_client_object.office_365_plan[0][1])
            self.sp_client_object.cvoperations.run_manual_discovery(True)

            self.sp_client_object.cvoperations.run_backup()

            subsite_browse_list = []
            for site, data in self.site_collection_data.items():
                for end_url in data["subsite_end_url_list"]:
                    subsite_browse_list.append(site + "\\Subsites\\" + end_url)

            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=subsite_browse_list)

            for site, data in self.site_collection_data.items():
                self.sp_client_object.delete_sp_site_collection(site, data["is_group"])

            self.restore_obj.restore_and_validate_sharepoint_content(restore_args={
                "paths": ["MB\\" + url for url in self.site_collection_data],
                }, sites_to_validate=list(self.site_collection_data),
                folder=True, list=True, v2_restore=True)

            self.validate_subsites_titles()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

            for site, data in self.site_collection_data.items():
                try:
                    self.sp_client_object.delete_sp_site_collection(site, data["is_group"])
                except Exception as e:
                    self.log.error(f"Error occurred while cleaning up site collection {site}: {e}. "
                                   "The testcase failed, so this error must be ignored")

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            for site_url, data in self.site_collection_data.items():
                self.sp_client_object.site_url = site_url
                self.sp_client_object.delete_subsites(data["subsite_end_url_list"])
            self.log.info("Cleaned up all test sub sites")

            self.testdata.delete_backup_site_structure(list(self.site_collection_data), folder=True, list=True)

            self.testdata.delete_disk_files()
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client(
                self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
