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

from Application.Office365.solr_helper import CVSolr
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing the test case of Office365- SharePoint Online- Validate all items on SharePoint Site
    and Index Server
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
        self.name = "Office365- SharePoint Online- Validate all items on SharePoint Site and Index Server"
        self.sp_client_object = None
        self.sites_source_paths = None
        self.index_paths = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [(self.tcinputs.get('Office365Plan'),
                                                      int(self.sp_client_object.cvoperations.get_plan_obj
                                                          (self.tcinputs.get('Office365Plan')).plan_id))]
            self.sp_client_object.site_url_list = self.tcinputs.get("SiteUrlList", "")
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def associate_sites(self):
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])

    def get_site_all_items(self):
        """Gets all the items metadata of tc input given sites
        """
        self.sites_source_paths = {}
        self.log.info("SharePoint Sites Stats")
        for site_url in self.sp_client_object.site_url_list:
            self.sp_client_object.site_url = site_url
            lists_dict = self.sp_client_object.get_site_all_items_metadata()
            source_paths = self.sp_client_object.process_source_paths(lists_dict)
            self.sites_source_paths[site_url] = source_paths
            self.log.info(f"Number of Unique Items: {len(source_paths)}")
            all_items_count = 0
            for path, items in source_paths.items():
                all_items_count = all_items_count + items.get('VersionCount')
            self.log.info(f"Number of Items Including Versions: {all_items_count}")

    def validate_items_on_index(self):
        """Validates items from SharePoint site and items present on index for tc input given sites
        """
        solr = CVSolr(self.sp_client_object)
        filters = ["SPTitle", "Url", "Version", "IdxMetaData"]
        index_paths = solr.get_all_items_metadata(filters, self.sp_client_object.site_url_list)
        failed_items_dict = {}
        for site, site_source_paths in self.sites_source_paths.items():
            is_site_validated = solr.validate_all_items(site_source_paths, index_paths[site])
            failed_items_dict[site] = is_site_validated
            if is_site_validated:
                self.log.info(f"All the items are validated for {site}")
            else:
                self.log.exception(f"All the items are not validated for {site}")
        if all(failed_items_dict.values()):
            self.log.info("All sites are validated")
        else:
            self.log.info("All sites are not validated")
            raise Exception("All sites are not validated")

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()
            self.associate_sites()
            self.get_site_all_items()
            self.sp_client_object.cvoperations.run_backup()
            self.validate_items_on_index()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client\
                (self.sp_client_object.pseudo_client_name)
