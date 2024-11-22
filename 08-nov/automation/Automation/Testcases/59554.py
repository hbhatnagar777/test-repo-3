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

Input Guide:

    Provide 3 fresh site collection URLs in SiteUrlList and
    3 Office 365 plans in Office365PlanList with the following properties:

        First plan with all versions backup (not considered for version retention)
        Second plan with latest version backup and 30 days version retention period
        Third plan with latest version backup and 60 days version retention period

"""

import json
from datetime import datetime
from Application.Sharepoint.sharepoint_online import SharePointOnline
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Application.Sharepoint.data_generation import TestData
from Application.Sharepoint.restore_options import Restore
from Application.CloudApps.csdb_helper import CSDBHelper
from Application.Office365.solr_helper import CVSolr
from AutomationUtils.database_helper import MSSQL


class TestCase(CVTestCase):
    """Class for executing the test case of Office365- SharePoint Online-
    All Versions and Latest Versions Backup and Restore
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
        self.name = "Office365- SharePoint Online- All Versions and Latest Versions Backup and Restore"
        self.sp_client_object = None
        self.testdata = None
        self.restore_obj = None
        self.csdb_helper = None
        self.client_id = None
        self.version_retention_sites = None
        self.solr_helper = None
        self.db_helper = None

    def init_tc(self):
        """ Initialization function for the test case. """
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.initialize_sp_v2_client_attributes()
            self.sp_client_object.office_365_plan = [
                (plan, int(self.sp_client_object.cvoperations.get_plan_obj(plan).plan_id))
                for plan in self.tcinputs.get('Office365PlanList')
            ]
            self.sp_client_object.site_url_list = self.tcinputs.get("SiteUrlList", [])
            self.sp_client_object.api_client_id = self.tcinputs.get("ClientId", "")
            self.sp_client_object.api_client_secret = self.tcinputs.get("ClientSecret", "")
            self.log.info('SharePoint client object created.')
            self.testdata = TestData(self.sp_client_object)
            self.restore_obj = Restore(self.sp_client_object)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def associate_sites(self):
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[i][1])

    def run_and_validate_restore(self):
        self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
        for i in range(len(self.sp_client_object.site_url_list)):
            self.sp_client_object.site_url = self.sp_client_object.site_url_list[i]
            self.restore_obj.restore_and_validate_sharepoint_content(
                restore_args={
                    "latest_version": bool(i)
                }, folder=True, list=True, v2_restore=True)

    def setup(self):
        """Setup function of this test case"""
        self.init_tc()
        self.csdb_helper = CSDBHelper(self)
        self.db_helper = MSSQL(self.tcinputs["SqlInstanceName"],
                               self.tcinputs["SqlUsername"],
                               self.tcinputs["SqlPassword"],
                               "CommServ")
        self.testdata.create_site_structure_for_backup(site_url_list=self.sp_client_object.site_url_list, folder=True,
                                                       list=True, versions=True)

    def enable_version_retention(self):
        """Enables version retention feature using QScript"""
        self.log.info("Enabling version retention feature for the client")

        try:
            commcell_number = self.csdb_helper.get_commcell_number()
            authcode = self.csdb_helper.get_authcode_setclientproperty(self.client_id, commcell_number)

            qscript = (f"-sn QS_SetClientProperty.sql -si '{self.tcinputs['PseudoClientName']}' "
                       f"-si 'EnableVersionRetention' -si 'true' -si '{authcode}'")
            self.log.info(f"Executing qscript: {qscript}")
            response = self.commcell._qoperation_execscript(qscript)
            self.log.info(f"QScript output: {response}")
            if not response:
                raise Exception(f"Failed to execute qscript for enabling version retention")

            self.log.info(f"Version retention feature enabled for client id [{self.client_id}]")
        except Exception as exp:
            self.log.error(f"Enabling version retention feature failed with error: {exp}")
            raise exp

    def modify_data_for_version_retention(self):
        """Adds versions to version retention sites to validate retention"""
        self.log.info("Modifying data and backing up the versions")

        try:
            for site in self.version_retention_sites:
                self.sp_client_object.site_url = site
                self.testdata.modify_backup_content(folder=True, list=True)
            job = self.sp_client_object.cvoperations.run_backup(wait_for_job_to_complete=False)
            self.sp_client_object.cvoperations.check_job_status(job)
            self.log.info(f"Backed up modified versions successfully")
        except Exception as exp:
            self.log.error(f"Failed to modify data for version retention with error: {exp}")
            raise exp

    def get_all_items_index_data(self, site_url):
        """Gets the folder and list items index from a SharePoint site

            Args:

                site_url    (str)       :   URL of the site collection
        """
        self.log.info(f"Getting all the backed up items data from index")

        try:
            index_data = {
                self.testdata.json_value.Folder.NAME: {},
                self.testdata.json_value.List.TITLE: {}
            }
            newline = "\n"

            for file in self.testdata.json_value.Folder.FILES:
                file_url = (f"\\\\MB\\\\{site_url}\\\\Contents\\\\{self.testdata.library_name}\\\\"
                            f"{self.testdata.json_value.Folder.NAME}\\\\{file.Name}")

                self.solr_helper.set_cvsolr_base_url()
                response = self.solr_helper.create_url_and_get_response(
                    {'Url': f'"{file_url}"'}, ["contentid", "BackupStartTime", "IsVisible", "Url", "Version"])
                docs = json.loads(response.content).get("response", {}).get("docs", [])

                index_data[self.testdata.json_value.Folder.NAME][file.Name] = docs
                self.log.info(f"Docs for [{file.Name}] in [{self.testdata.json_value.Folder.NAME}]:\n"
                              f"{newline.join(json.dumps(doc) for doc in docs)}")

            for i in range(len(self.testdata.json_value.List.LIST_ITEMS)):
                item_id = f"{i + 1}_.000"
                item_url = f"\\\\MB\\\\{site_url}\\\\Contents\\\\{self.testdata.json_value.List.TITLE}\\\\{item_id}"

                self.solr_helper.set_cvsolr_base_url()
                response = self.solr_helper.create_url_and_get_response(
                    {'Url': f'"{item_url}"'}, ["contentid", "BackupStartTime", "IsVisible", "Url", "Version"])
                docs = json.loads(response.content).get("response", {}).get("docs", [])

                index_data[self.testdata.json_value.List.TITLE][item_id] = docs
                self.log.info(f"Docs for [{item_id}] in [{self.testdata.json_value.List.TITLE}]:\n"
                              f"{newline.join(json.dumps(doc) for doc in docs)}")

            return index_data
        except Exception as exp:
            self.log.error(f"Failed to get index data with error: {exp}")
            raise exp

    def delete_version_retention_lock(self):
        """Deletes the row in CSDB that prevents version retention from running frequently"""
        query = ("DELETE FROM App_ClientProp WHERE attrName like '%LastVersionRetentionTime%' and "
                 f"componentNameId = {self.client_id}")

        self.log.info(f"Executing the CSDB query for client id [{self.client_id}]")
        self.log.info(f"CSDB Query: {query}")

        try:
            self.db_helper.execute(query)
            self.log.info("Query executed successfully")
        except Exception as exp:
            self.log.error(f"Failed to execute query with error: {exp}")
            raise exp

    def run_retention_rules(self, days_to_subtract):
        """Runs retention rules after subtracting days from BackupStartTime

            Args:

                days_to_subtract    (int)       :   Number of days to subtract from BackupStartTime field
        """
        self.log.info(f"Running retention rules after modifying BackupStartTime field")

        try:
            for site in self.version_retention_sites:
                index_data = self.get_all_items_index_data(site)
                for items in index_data.values():
                    for docs in items.values():
                        for doc in docs:
                            new_time = self.solr_helper.subtract_retention_time(doc["BackupStartTime"], days_to_subtract)
                            self.solr_helper.update_field(doc["contentid"], "BackupStartTime", new_time)

            self.delete_version_retention_lock()
            self.sp_client_object.cvoperations.process_index_retention_rules(
                self.solr_helper.index_details.get('indexServerClientId'))
            self.log.info("Modified field and ran retention rules successfully")
        except Exception as exp:
            self.log.error(f"Failed to modify field and run retention rules with error: {exp}")
            raise exp

    def incremental_retry(func):
        def inner(self, *args, **kwargs):
            retry_count = 0
            while True:
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as exception:
                    retry_count = retry_count + 1
                    if retry_count > 3:
                        raise exception
                    self.log.error(f"Exception: {exception}, Retrying")
                    self.sp_client_object.cvoperations.wait_time(60 * retry_count)
        return inner

    @incremental_retry
    def validate_is_visible_field(self, site_url, latest_only=False):
        """Validates the IsVisible field for the SharePoint site

            Args:

                site_url    (str)       :   URL of the site collection

                latest_only (bool)      :   Whether only the latest version for each item should be visible
        """

        def sort_function(d):
            return datetime.strptime(d["BackupStartTime"], '%Y-%m-%dT%H:%M:%SZ'), d["Version"]

        index_data = self.get_all_items_index_data(site_url)
        for collection, items in index_data.items():
            for name, docs in items.items():
                for doc in sorted(docs, key=sort_function)[1:-1]:
                    if latest_only and doc["IsVisible"]:
                        self.log.error(f"IsVisible for the Solr doc [{doc}] is TRUE")
                        raise Exception(f"IsVisible for the Solr doc [{doc}] is TRUE")
                    if not latest_only and not doc["IsVisible"]:
                        self.log.error(f"IsVisible for the Solr doc [{doc}] is FALSE")
                        raise Exception(f"IsVisible for the Solr doc [{doc}] is FALSE")

                latest_doc = max(docs, key=sort_function)
                if not latest_doc["IsVisible"]:
                    self.log.error(f"IsVisible for the Solr doc [{latest_doc}] is FALSE")
                    raise Exception(f"IsVisible for the Solr doc [{latest_doc}] is FALSE")

        self.log.info(f"{'Latest' if latest_only else 'All'} versions in [{site_url}] have IsVisible set to TRUE")

    def validate_version_retention(self):
        """Validates version retention for the SharePoint site"""
        self.log.info(f"Validating version retention for {self.version_retention_sites}")

        self.run_retention_rules(45)
        self.validate_is_visible_field(self.version_retention_sites[0], latest_only=True)
        self.validate_is_visible_field(self.version_retention_sites[1], latest_only=False)

        self.run_retention_rules(90)
        self.validate_is_visible_field(self.version_retention_sites[0], latest_only=True)
        self.validate_is_visible_field(self.version_retention_sites[1], latest_only=True)

        self.log.info(f"Validated version retention successfully")

    def run(self):
        """Run function of this test case"""
        try:
            self.sp_client_object.cvoperations.add_share_point_pseudo_client()

            self.client_id = self.sp_client_object.cvoperations.client.client_id
            if not self.tcinputs.get("FeatureEnabled", True):
                self.enable_version_retention()

            self.associate_sites()
            self.sp_client_object.cvoperations.run_backup()

            self.restore_obj.browse_restore_content_and_verify_browse_response(
                browse_paths=self.sp_client_object.site_url_list)
            self.run_and_validate_restore()

            self.solr_helper = CVSolr(self.sp_client_object)
            self.version_retention_sites = self.sp_client_object.site_url_list[1:]

            self.testdata.delete_backup_site_structure(folder=True, list=True, force=True)
            self.testdata.create_site_structure_for_backup(
                site_url_list=self.sp_client_object.site_url_list, folder=True, list=True, versions=False)
            job = self.sp_client_object.cvoperations.run_backup(wait_for_job_to_complete=False)
            self.sp_client_object.cvoperations.check_job_status(job)

            self.modify_data_for_version_retention()
            self.modify_data_for_version_retention()
            self.validate_version_retention()
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.testdata.delete_disk_files()
            self.testdata.delete_backup_site_structure(folder=True, list=True)
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client(
                self.sp_client_object.pseudo_client_name)
