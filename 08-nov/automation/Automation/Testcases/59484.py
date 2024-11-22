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


class TestCase(CVTestCase):
    """Class for executing the test case of Office365- SharePoint Online Data protection:
    Manual Discovery Advanced Case: Edit, delete and modify site title and URL """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online Data protection: Manual Discovery Advanced Case: Edit, delete " \
                    "and modify site title and URL "
        self.sp_client_object = None
        self.subsites_metadata = {}

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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def create_initial_sites(self):
        """Creates subsites in a given site based on given input json
        """
        try:
            self.log.info("Cleaning up all subsites if exists")
            subsite_end_url_list = ["subsite_1", "subsite_2", "subsite_2_rename", "subsite_3", "subsite_3_rename"]
            self.sp_client_object.delete_subsites(subsite_end_url_list)
            subsite_list = []
            for i in range(2, 4):
                title = "Test Subsite - " + str(i)
                url_end = "subsite_" + str(i)
                subsite_list.append({
                    "Title": title,
                    "Url End": url_end
                })
            self.subsites_metadata = self.sp_client_object.create_subsites(subsite_list)
            if not self.subsites_metadata:
                self.log.exception("Initial test subsites are not created.Please check if the provided app credentials "
                                   "are correct or if app experiencing any throttling")
        except Exception as exception:
            self.log.exception("Exception while creating subsite on SharePoint Site: %s", str(exception))
            raise exception

    def make_site_level_changes(self):
        """Makes site level changes - Add/Edit/Delete
        """
        try:
            self.log.info("Creating a sub site")
            title = "Test Subsite - 1"
            url_end = "subsite_1"
            self.subsites_metadata.update(self.sp_client_object.create_subsites([{
                    "Title": title,
                    "Url End": url_end
                }]))

            self.log.info("Edit site level properties of a subsite")
            subsite_url = "/" + "/".join(self.sp_client_object.site_url.split("/")[3:]) + "/subsite_2"
            self.subsites_metadata[subsite_url]['Old Url End'] = self.subsites_metadata.get(subsite_url).get('Url End')
            self.subsites_metadata[subsite_url]['Url End'] = self.subsites_metadata.get(subsite_url).get('Url End') + "_rename"
            self.subsites_metadata[subsite_url]['Title'] = self.subsites_metadata.get(subsite_url).get('Title') + " - Rename"
            prop_dict = {
                'ServerRelativeUrl': self.subsites_metadata[subsite_url].get('Url End'),
                'Title': self.subsites_metadata[subsite_url].get('Title')
            }
            self.sp_client_object.update_subsite_level_properties(prop_dict, self.subsites_metadata[subsite_url].
                                                                  get('Old Url End'))
            self.log.info(f"New properties of subsite are\n URL: {self.sp_client_object.site_url}/"
                          f"{self.subsites_metadata[subsite_url].get('Url End')}\n Title: "
                          f"{self.subsites_metadata[subsite_url].get('Title')}")
            self.subsites_metadata[subsite_url]["Operation"] = "EDITED"

            self.log.info("Deleting the subsite")
            subsite_url = "/" + "/".join(self.sp_client_object.site_url.split("/")[3:]) + "/subsite_3"
            self.sp_client_object.delete_subsite("subsite_3")
            self.subsites_metadata[subsite_url]["Operation"] = "DELETED"
        except Exception as exception:
            self.log.exception("Exception while making site level changes: %s", str(exception))
            raise exception

    def validate_site_level_changes(self):
        """Validates site level changes made earlier"""
        try:
            for subsite in self.subsites_metadata:
                add_properties = {
                    'Associated Flags Value': "4",
                    'Office 365 Plan Id': self.sp_client_object.office_365_plan[0][1]
                }
                self.subsites_metadata[subsite].update(add_properties)
                self.sp_client_object.validate_subsite_properties(self.subsites_metadata[subsite])
        except Exception as exception:
            self.log.exception("Exception while validating site level changes: %s", str(exception))
            raise exception

    def clean_up_sites(self):
        """Cleans up the sites created for testcase"""
        try:
            for subsite in self.subsites_metadata:
                if self.subsites_metadata[subsite].get("Operation") != "DELETED":
                    self.sp_client_object.delete_subsite(self.subsites_metadata[subsite].get('Url End'))
                    self.subsites_metadata[subsite]["Operation"] = "DELETED"
        except Exception as exception:
            self.log.exception(f"Exception while deleting sites: %s", str(exception))
            raise exception

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.create_initial_sites()
        self.sp_client_object.cvoperations.add_share_point_pseudo_client()
        self.log.info("Pseudo Client has been created successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(self.sp_client_object.office_365_plan[0][1])
            self.make_site_level_changes()
            self.log.info("Site level changes are made successfully")
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.validate_site_level_changes()
            self.log.info("Site level changes are validated successfully")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.clean_up_sites()
            self.log.info("All test sites are deleted successfully")
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client\
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
