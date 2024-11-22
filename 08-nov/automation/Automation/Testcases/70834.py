""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    enable_o365_plan_ci()      -- enable content indexing for O365 plan

    perform_backup()         -- performs backup

    validate_content_indexing()  -- validate ci job

    create_export_set()         -- create an ExportSet

    search_and_export_items()   -- search and export random items to ExportSet

    validate_download_items()   -- validate the downloaded files from export

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import shutil
from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.solr_helper import SolrHelper
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.teams_constants import TeamsConstants
from cvpysdk.activateapps.constants import ComplianceConstants
from cvpysdk.commcell import Commcell
from dynamicindex.activate_sdk_helper import ActivateSDKHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.utils.constants import DOWNLOAD_FOLDER_PATH
from Web.Common.page_object import TestStep

const = TeamsConstants()


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = ("Basic Acceptance-CVPysdk-Tenant creation,Backup,Content Indexing and Export-Compliance "
                     "Search-Teams")
        self.no_of_objects = None
        self.client_name = None
        self.company_username = None
        self.plan_name = None
        self.index_server_name = None
        self.teams = None
        self.export_name = None
        self.export_set_name = None
        self.tenant_commcell = None
        self.admin_commcell = None
        self.export_sets = None
        self.compliance_search = None
        self.activate_helper = None
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.query = None
        self.export_count = None
        self.solrhelper_obj = None
        self.page_size = 50
        self.tcinputs = {
            "ClientName": None,
            "teams": None,
            "O365_plan": None,
            "TenantUserName": None,
            "TenantPassword": None,
            "IndexServer": None
        }

    def setup(self):
        """Setup function of this test case."""
        try:
            self.client_name = self.tcinputs["ClientName"]
            self.company_username = self.tcinputs["TenantUserName"]
            self.plan_name = self.tcinputs["O365_plan"]
            self.no_of_objects = 0
            self.index_server_name = self.tcinputs["IndexServer"]
            self.teams = self.tcinputs['teams']
            self.export_count = 1
            self.query = "*"
            self.export_name = "Export_%s" % self.id
            self.export_set_name = "ExportSet_%s" % self.id
            self.tenant_commcell = Commcell(self.commcell.webconsole_hostname,
                                            self.tcinputs["TenantUserName"],
                                            self.tcinputs["TenantPassword"])
            self.admin_commcell = self.commcell
            self.export_sets = self.tenant_commcell.export_sets
            self.compliance_search = self.tenant_commcell.activate.compliance_search()
            self.activate_helper = ActivateSDKHelper(self.tenant_commcell)
        except Exception:
            raise Exception("init tc failed")



    @TestStep()
    def enable_o365_plan_ci(self):
        """Testcase step to enable CI for O365 plan"""
        self.log.info("Enabling content indexing for O365 plan")
        self.plans = self.commcell.plans
        self.plan = self.plans.get(self.plan_name)
        ci_status = self.plan.content_indexing
        if not ci_status:
            self.plan.content_indexing = True

    def init_tc(self):
        """Initializing testcase objects"""
        self.log.info("Initializing client object")
        self.client = self.tenant_commcell.clients.get(self.client_name)
        self.log.info("Initializing teams helper object")
        self.helper = TeamsHelper(self.client, self)
        self.log.info("Adding teams to the client")
        self.helper.set_content(self.teams, self.plan_name)
        self.log.info(f"Teams {self.teams} added with O365 plan {self.plan_name}")
        try:
            self.ci_job_before_backup = self.helper.get_latest_ci_job()
        except:
            self.ci_job_before_backup = 0

    @TestStep()
    def perform_backup(self):
        """Testcase step to perform backup"""
        self.log.info("Ready to perform backup")
        self.backup_job = self.helper.backup(self.teams)
        self.log.info(f"Backup job {self.backup_job.job_id} completed successfully")

        self.log.info("Checking if playback succeeded")
        self.helper._commcell_object = self.admin_commcell
        self.solrhelper_obj = SolrHelper(self.helper)

        teams_objects = self.solrhelper_obj.create_url_and_get_response(
            {'JobId': self.backup_job.job_id, 'DocumentType': '4'}, op_params={})
        no_of_teams_objects = int(self.solrhelper_obj.get_count_from_json(teams_objects.content))

        files = self.solrhelper_obj.create_url_and_get_response(
            {'JobId': self.backup_job.job_id, 'DocumentType': '1'}, op_params={})
        no_of_files = int(self.solrhelper_obj.get_count_from_json(files.content))

        self.no_of_objects = no_of_teams_objects - (self.backup_job.num_of_files_transferred - no_of_files)

        if not self.solrhelper_obj._check_all_items_played_successfully(self.backup_job.job_id):
            raise Exception(f"Playback failed for Job ID {self.backup_job.job_id}")
        else:
            self.log.info(f"Playback successful for Job ID {self.backup_job.job_id}")
        self.log.info("backup completed")

    @TestStep()
    def validate_content_indexing(self):
        """Testcase step to validate content indexing"""
        self.log.info("Waiting for CI jobs to be completed")
        ci_job_after_backup = self.helper.get_latest_ci_job()
        if self.ci_job_before_backup != ci_job_after_backup:
            self.log.info('%s job completed successfully.', ci_job_after_backup)
        else:
            self.log.info("No CI job run after the backup")
        solr_results = self.solrhelper_obj.create_url_and_get_response(
            {'JobId': self.backup_job.job_id, 'DocumentType': '1', 'ContentIndexingStatus': '1'}, op_params={})
        count = int(self.solrhelper_obj.get_count_from_json(solr_results.content))
        self.log.info(f"Number of items content indexed {count}")

    @TestStep()
    def create_export_set(self):
        """Testcase step to create an ExportSet"""
        self.log.info(f"Trying to create a new ExportSet {self.export_set_name}")
        if self.export_sets.has(self.export_set_name):
            self.log.info(f"ExportSet {self.export_set_name} exists already, deleting and retrying")
            self.export_sets.delete(self.export_set_name)
            self.log.info(f"ExportSet {self.export_set_name} deleted")
        self.log.info(f"Now creating a new ExportSet {self.export_set_name}")
        self.export_set = self.export_sets.add(self.export_set_name)
        self.log.info(f"ExportSet {self.export_set_name} created successfully")

    @TestStep()
    def search_and_export_items(self):
        """Testcase step to search and export random items to ExportSet"""
        self.log.info("Running Compliance search with the query now")
        self.search_items = self.compliance_search.do_compliance_search(
            search_text=self.query, page_size=self.page_size, app_type=ComplianceConstants.AppTypes.TEAMS)
        self.log.info(f"Total of {len(self.search_items)} items were found for the query")
        self.search_items = self.export_set.select(
            result_items=self.search_items, no_of_files=self.export_count)
        self.log.info(f"Randomly selected {self.export_count} items from the total search result")
        self.log.info(f"Now exporting the search result items to export {self.export_name}")
        restore_job_id = self.export_set.export_items_to_set(
            export_name=self.export_name, export_items=self.search_items
        )
        self.log.info(f"Search result items exported to export {self.export_name} successfully")
        if restore_job_id != 0:
            self.log.info(f"Waiting for job {restore_job_id} to get complete")
            if not CrawlJobHelper.monitor_job(
                    commcell_object=self.commcell,
                    job=int(restore_job_id)):
                self.log.error("Restore job failed to complete")
                raise Exception(f"Restore job {restore_job_id} failed to complete")
            self.log.info(f"Restore job {restore_job_id} completed successfully")

    @TestStep()
    def validate_download_items(self):
        """Testcase step to validate the downloaded files from export"""
        self.activate_helper.download_validate_compliance_export(
            export_name=self.export_name,
            export_set_name=self.export_set_name,
            exported_files=self.search_items,
            app_type=ComplianceConstants.AppTypes.TEAMS)

    def cleanup(self):
        """Testcase step to delete the export and ExportSet"""
        self.log.info("Now trying to delete the Export")
        self.export_set.delete(self.export_name)
        self.log.info(f"Export {self.export_name} deleted successfully")
        self.log.info(f"Deleting the ExportSet {self.export_set_name}")
        self.export_sets.delete(self.export_set_name)
        self.log.info(f"ExportSet {self.export_set_name} deleted")
        self.log.info("Deleting the export download files")
        shutil.rmtree(DOWNLOAD_FOLDER_PATH % self.export_name)
        self.log.info("Export download folder deleted successfully")

    def run(self):
        """Main function for test case execution."""
        try:
            self.enable_o365_plan_ci()
            self.init_tc()
            self.perform_backup()
            self.validate_content_indexing()
            self.create_export_set()
            self.search_and_export_items()
            self.validate_download_items()
        except Exception as ex:
            self.log.exception(ex)

    def tear_down(self):
        """Tear down function for test case"""
        try:
            self.cleanup()
        except Exception as exp:
            self.log.exception(exp)
            self.log.info("Test case execution failed")



