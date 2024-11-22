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
    """Class for executing the test case of Office365- SharePoint Online- Auto Association -
    Advance - O365 Plan Retention Conflicts Case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Office365- SharePoint Online- Auto Association - Advance - O365 Plan Retention Conflicts Case"
        self.sp_client_object = None
        self.subsite_metadata = {}
        self.group_names = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365PlanList')[0],
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365PlanList')[0]).plan_id)),
                                                     (self.tcinputs.get('Office365PlanList')[1],
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365PlanList')[1]).plan_id)),
                                                     (self.tcinputs.get('Office365PlanList')[2],
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365PlanList')[2]).plan_id))
                                                     ]
            self.sp_client_object.graph_client_id = self.tcinputs.get("GraphClientId", "")
            self.sp_client_object.graph_client_secret = self.tcinputs.get("GraphClientSecret", "")
            self.sp_client_object.graph_tenant_id = self.tcinputs.get("GraphTenantId", "")
            self.sp_client_object.site_url = self.tcinputs.get("SiteUrl", "")
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def create_initial_subsite(self):
        """Creates subsites in a given site based on given input json
        """
        try:
            subsite_url = "/" + "/".join(self.sp_client_object.site_url.split("/")[3:]) + "/subsite_1"
            self.subsite_metadata = self.sp_client_object.create_subsites([{
                'Title':  "Test Subsite - 1",
                'Url End': "subsite_1"
            }]).get(subsite_url)
        except Exception as exception:
            self.log.exception("Exception while creating subsite on SharePoint Site: %s", str(exception))
            raise exception

    def validate_o365_plan_for_common_site(self, configured_plan_name):
        """Validates o365 plan for site which is common in two groups

            Args:

                configured_plan_name (str)      --    o365 plan with which the site is associated

        """
        try:
            site_dict, no_of_records = self.sp_client_object.cvoperations.check_sites_under_add_webs(discovery_type=6)
            if site_dict:
                if self.sp_client_object.site_url in site_dict.keys():
                    plan_name = site_dict[self.sp_client_object.site_url].get('planName', '')
                    self.log.info(f"Input Plan Name : {configured_plan_name}")
                    self.log.info(f"{self.sp_client_object.site_url} has {plan_name} o365 plan")
                    if configured_plan_name == plan_name:
                        self.log.info(f"Correct o365 plan is selected for {self.sp_client_object.site_url} site")
                    else:
                        self.log.exception(f"Correct o365 plan is not selected for {self.sp_client_object.site_url}")
                        raise Exception(f"Correct o365 plan is not selected for {self.sp_client_object.site_url} site")
        except Exception as exception:
            self.log.exception("Exception while validating o365 for common site: %s", str(exception))
            raise exception

    def update_auto_association_properties_and_validate_retention_conflict(self, group_name, configure_o365_plan,
                                                                           validate_o365_plan):
        """Updates auto association properties and validates rentention conflicts

            Args:

                group_name (str)                --    name of the auto association group

                configure_o365_plan (tuple)     --    office 365 plan to be configured
                                                      Example: (plan_name, plan_id) -> ("plan1", "1")

                validate_o365_plan (tuple)      --    office 365 plan to be validated
                                                      Example: (plan_name, plan_id) -> ("plan1", "1")

        """
        try:
            self.sp_client_object.cvoperations.configure_group_for_backup(group_name,
                                                                          configure_o365_plan[1])
            self.sp_client_object.cvoperations.update_auto_association_group_properties(
                association_group_name=group_name, account_status=0,
                office_365_plan_id=configure_o365_plan[1])
            self.validate_o365_plan_for_common_site(validate_o365_plan[0])
            add_properties = {
                'Associated Flags Value': "0",
                'Office 365 Plan Id': validate_o365_plan[1]
            }
            self.subsite_metadata.update(add_properties)
            self.sp_client_object.validate_subsite_properties(self.subsite_metadata)
        except Exception as exception:
            self.log.exception("Exception while updating auto association properties "
                               "and validating rentention conflicts: %s", str(exception))
            raise exception

    def validate_o365_plan_retention_conflicts(self):
        """Validates o365 plan conflicts for retention
        """
        try:
            self.update_auto_association_properties_and_validate_retention_conflict\
                ("All Teams Sites", self.sp_client_object.office_365_plan[1],
                 self.sp_client_object.office_365_plan[1])

            self.update_auto_association_properties_and_validate_retention_conflict\
                ("All Web Sites", self.sp_client_object.office_365_plan[0],
                 self.sp_client_object.office_365_plan[1])

            self.update_auto_association_properties_and_validate_retention_conflict\
                ("All Teams Sites", self.sp_client_object.office_365_plan[2],
                 self.sp_client_object.office_365_plan[0])
        except Exception as exception:
            self.log.exception("Exception while validating plan conflicts: %s", str(exception))
            raise exception

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.create_initial_subsite()
        self.sp_client_object.cvoperations.add_share_point_pseudo_client()
        self.log.info("Pseudo Client has been created successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)
            self.validate_o365_plan_retention_conflicts()
            self.sp_client_object.delete_subsites(["subsite_1"])
            self.log.info("All test sites are deleted successfully")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client \
                (self.sp_client_object.pseudo_client_name)
            self.log.info("Pseudo Client has been deleted successfully")
