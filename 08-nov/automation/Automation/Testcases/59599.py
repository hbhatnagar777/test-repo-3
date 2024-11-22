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


class TestCase(CVTestCase):
    """Class for executing the test case of Office365- SharePoint Online - Auto Association - Basic case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online - Auto Association - Basic case"
        self.sp_client_object = None
        self.subsites_metadata = {}
        self.group_names = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365Plan')).plan_id))]
            self.sp_client_object.graph_client_id = self.tcinputs.get("GraphClientId", "")
            self.sp_client_object.graph_client_secret = self.tcinputs.get("GraphClientSecret", "")
            self.sp_client_object.graph_tenant_id = self.tcinputs.get("GraphTenantId", "")
            self.sp_client_object.site_url_list = self.tcinputs.get("SiteUrlList", "")
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def clean_up_sites(self):
        """Cleans up the test sites used in test case"""
        try:
            for site in self.sp_client_object.site_url_list:
                self.sp_client_object.site_url = site
                if self.sp_client_object.get_site_properties("subsite_1"):
                    self.log.info("site is present in SharePoint site")
                    self.sp_client_object.delete_subsite("subsite_1")
        except Exception as exception:
            self.log.exception(f"Exception while deleting sites: %s", str(exception))
            raise exception

    def create_subsite(self, web_template):
        """Creates a subsite
        """
        try:
            self.log.info("Creating a sub site")
            title = "Test Subsite - 1"
            url_end = "subsite_1"
            response = self.sp_client_object.create_subsite(title, url_end, web_template)
            self.subsites_metadata[response.get('ServerRelativeUrl')] = {
                'Url End': response.get('ServerRelativeUrl').split("/")[-1],
                'Title': response.get('Title', ""),
                'Operation': "ADDED",
                'Associated Flags Value': "0",
                'Office 365 Plan Id': self.sp_client_object.office_365_plan[0][1]
            }
            return response.get('ServerRelativeUrl')
        except Exception as exception:
            self.log.exception("Exception while making site level changes: %s", str(exception))
            raise exception

    def validate_group_association(self, group_name, site_url, web_template, total_num_of_sites):
        """Validates auto association group"""
        try:
            self.sp_client_object.cvoperations.configure_group_for_backup(group_name,
                                                                          self.sp_client_object.office_365_plan[0][1])
            self.sp_client_object.cvoperations.update_auto_association_group_properties(
                association_group_name=group_name,
                account_status=0,
                office_365_plan_id=self.sp_client_object.office_365_plan[0][1])
            site_dict, no_of_records = self.sp_client_object.cvoperations.check_sites_under_add_webs(discovery_type=6)
            self.log.info(f"Total number of sites from api= {total_num_of_sites}")
            self.log.info(f"Total number of sites associated under {group_name} group = {no_of_records}")
            if no_of_records < total_num_of_sites or no_of_records - total_num_of_sites > 10 or no_of_records == 0:
                raise Exception(f"All sites are not associated with {group_name} group")
            else:
                total_num_of_sites = no_of_records
                self.log.info(f"All sites are associated with {group_name} group")
            self.sp_client_object.site_url = site_url
            subsite = self.create_subsite(web_template)
            time.sleep(10)
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.sp_client_object.validate_subsite_properties(self.subsites_metadata[subsite])
            site_dict, no_of_records = self.sp_client_object.cvoperations.check_sites_under_add_webs(discovery_type=6)
            self.log.info(f"Total number of sites from api= {total_num_of_sites}")
            self.log.info(f"Total number of sites associated under group = {no_of_records}")
            if no_of_records > total_num_of_sites:
                # ideally (no_of_records - total_num_of_sites) should be equal to 1, but due to simultaneous use of
                # this tenant we'll go with ">"
                self.log.info(f"The total associated sites count is as expected for {group_name} "
                              f"group after new subsite discovery")
            else:
                raise Exception(f"The total associated sites count is not as expected for {group_name} "
                                f"group after new subsite discovery")
            self.sp_client_object.cvoperations.update_auto_association_group_properties(
                association_group_name=group_name, account_status=1)
            site_dict, no_of_records = self.sp_client_object.cvoperations.check_sites_under_add_webs(discovery_type=6)
            self.log.info(f"No of associated sites after disassociating the group: {no_of_records}")
            if int(no_of_records or 0) != 0:
                raise Exception(f"All sites are not dis-associated for {group_name} group")
        except Exception as exception:
            self.log.exception("Exception while validating all webs group: %s", str(exception))
            raise exception

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.clean_up_sites()
        self.sp_client_object.cvoperations.add_share_point_pseudo_client()
        self.log.info("Pseudo Client has been created successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            total_num_of_sites = self.sp_client_object.get_group_based_sites_count()
            self.group_names = ["All Web Sites", "All Teams Sites", "All Project Online Sites"]
            web_templates = ['GROUP', 'STS', 'STS']
            for index in range(len(self.sp_client_object.site_url_list)):
                self.validate_group_association(self.group_names[index], self.sp_client_object.site_url_list[index],
                                                web_templates[index], total_num_of_sites[self.group_names[index]])
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.clean_up_sites()
            self.log.info("All test sites are deleted successfully")
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
