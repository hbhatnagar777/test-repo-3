""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    create_company_using_workflow()  -- create a new company

    change_company_admin_password()  -- change company password

    start_company_trial()     -- start trial for the company

    enable_o365_plan_ci()      -- enable content indexing for O365 plan

    activate_compliance()     -- add compliance role to user group

    add_exchange_client()     -- add new exchange client

    perform_backup()         -- performs backup

    validate_content_indexing()  -- validate ci job

    create_export_set()         -- create an ExportSet

    search_and_export_items()   -- search and export random items to ExportSet

    validate_download_items()   -- validate the downloaded files from export

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import sys
import random
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox import constants as exchange_apps_constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils.config import get_config
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper, CVSolr
from cvpysdk.commcell import Commcell
from cvpysdk.activateapps.constants import ComplianceConstants
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from dynamicindex.activate_sdk_helper import ActivateSDKHelper
from dynamicindex.activate_tenant_helper import ActivateTenantHelper
from dynamicindex.utils import constants as d_cs
from dynamicindex.utils.constants import set_step_complete, is_step_complete, CITestSteps as sc
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from MetallicRing.Helpers.subscription_helper import SaaSSubscriptionHelper
from MetallicRing.Helpers.workflow_helper import WorkflowRingHelper
from MetallicRing.Utils import Constants as cs
from Web.Common.page_object import TestStep
from time import sleep


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("Basic Acceptance - CVPysdk -Tenant creation, Backup, Content Indexing "
                     "and Export-Compliance Search - Exchange")
        self.plan_name = None
        self.server_plan = None
        self.export_set_name = None
        self.export_name = None
        self.firstname = None
        self.metrics_config = None
        self.company = None
        self.index_server_name = None
        self.msp_password = None
        self.azure_app_details = None
        self.metrics_commcell = None
        self.activate_helper = None
        self.compliance_search = None
        self.export_sets = None
        self.users = None
        self.admin_commcell = None
        self.workflow_helper = None
        self.tenant_helper = None
        self.client_name = None
        self.tenant_commcell = None
        self.is_ci_failed = False
        self.rehydrator = None
        self.wait_time = cs.WaitTime.TWO_MIN.value * 60
        self.retry_attempt = 0
        self.max_attempt = 45
        self.tcinputs = {
            "Users": None,
            "IndexServer": None,
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            self.firstname = f"{self.id}"
            self.rehydrator = Rehydrator(self.id)
            self.test_progress = self.rehydrator.bucket(d_cs.BUCKET_TEST_PROGRESS)
            self.test_progress.get(default=0)
            self.tenant_name = self.rehydrator.bucket("tenant_name")
            config = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH)
            self.metrics_config = config.Metallic.metrics_commcell
            self.metrics_commcell = Commcell(self.metrics_config.hostname, self.metrics_config.username,
                                             self.metrics_config.password)
            self.workflow_helper = WorkflowRingHelper(self.metrics_commcell)
            self.azure_app_details = config.Metallic.exchange_azure_key_details
            self.admin_commcell = self.commcell
            self.msp_password = self.inputJSONnode['commcell']['commcellPassword']
            self.client_name = f"{self.company}_Exchange_Client"
            self.users = self.tcinputs["Users"]
            self.tcinputs["ProxyServers"] = [""]
            self.index_server_name = self.tcinputs["IndexServer"]
            self.export_count = 1
            self.query = "*"
            self.export_name = "Export_%s" % self.id
            self.export_set_name = "ExportSet_%s" % self.id
            self.tenant_helper = ActivateTenantHelper(self.commcell)
        except Exception:
            self.status = constants.FAILED
            raise Exception("init tc failed")

    @TestStep()
    def create_company_using_workflow(self):
        """Testcase step for creating a new company"""
        self.company = d_cs.EXCHANGE_TENANT.format(str(int(time.time())))
        workflow_inputs = dict(
            firstname=self.firstname,
            lastname=self.id,
            company_name=self.company,
            phone=f"{random.randint(1000000000, 9999999999)}",
            commcell=self.commcell.commserv_name
        )
        workflow_inputs["email"] = f"{self.firstname}@{self.company}.com"
        workflow_name = "Metallic Trials On-boarding v2"
        self.log.info(f"Starting workflow [{workflow_name}] with inputs - [{workflow_inputs}]")
        if self.commcell.organizations.has_organization(self.company):
            self.log.info("------Company already created----------")
        self.workflow_helper.execute_trials_v2_workflow(workflow_name, workflow_inputs)
        while not self.commcell.organizations.has_organization(self.company):
            self.commcell.organizations.refresh()
            self.log.info(f"Tenant is still not created [{self.company}]. Sleeping for couple of minutes")
            self.retry_attempt += 1
            sleep(self.wait_time)
            if self.retry_attempt >= self.max_attempt:
                raise Exception("Tenant creation from trials v2 workflow failed."
                                " Please check logs for more info")
        self.log.info(f"Tenant [{self.company}] created successfully. Changing company user password")
        self.tenant_name.set(self.company)

    @TestStep()
    def change_company_admin_password(self):
        """Testcase step to change company password"""
        self.log.info("Changing company user password")
        user_name = f'{self.company}\\{self.firstname}'
        self.tenant_helper = ActivateTenantHelper(self.commcell)
        self.tenant_helper.change_company_user_password(user_name, self.msp_password,
                                                        self.msp_password)
        self.log.info("Company user password changed.")

    @TestStep()
    def start_company_trial(self):
        """Testcase step to start trial for company"""
        self.tenant_commcell = Commcell(self.commcell.webconsole_hostname,
                                        f'{self.company}\\{self.firstname}',
                                        self.msp_password)
        self.subscription_helper = SaaSSubscriptionHelper(self.tenant_commcell)
        lh_base_url = self.commcell.get_gxglobalparam_value("MetallicLightHouseBaseUrl")
        if not self.is_test_step_complete(sc.START_TRIAL):
            self.log.info("-----------Starting trial for newly added company-------------")
            self.subscription_helper.start_o365_trial(lh_base_url)
            self.set_test_step_complete(sc.START_TRIAL)
        else:
            self.log.info(f"{sc.START_TRIAL.name} step complete. Not starting it")

        self.plan_name = self.subscription_helper.get_o365_enterprise_plan()
        self.server_plan = self.subscription_helper.get_server_plan()
        self.log.info(f"Trial started for {self.company}")

    @TestStep()
    def add_exchange_client(self):
        """Testcase step to add exchange client"""
        self.client_name = f"{self.company}_client"
        self.log.info(f"Adding exchange client {self.client_name}")
        self.tenant_commcell.clients.add_exchange_client(
            client_name=self.client_name,
            server_plan=self.server_plan,
            azure_app_key_secret=self.azure_app_details.azure_app_key_secret,
            azure_tenant_name=self.azure_app_details.azure_tenant_name,
            azure_app_key_id=self.azure_app_details.azure_app_key_id,
            environment_type=4,
            index_server='',
            clients_list='',
            recall_service_url='',
            job_result_dir='',
            exchange_servers=[],
            service_accounts={}
        )
        self.log.info("Exchange client added")

    @TestStep()
    def enable_o365_plan_ci(self):
        """Testcase step to enable CI for O365 plan"""
        self.log.info("Enabling content indexing for O365 plan")
        self.plans = self.commcell.plans
        self.plan = self.plans.get(self.plan_name)
        ci_status = self.plan.content_indexing
        if not ci_status:
            self.plan.content_indexing = True
        self.log.info(f"Content Indexing enabled for plan {self.plan_name}")

    @TestStep()
    def activate_compliance(self):
        """Testcase step to add compliance to user group"""
        self.log.info("Adding Complinace role for the tenant")
        self.tenant_helper.add_compliance_user_group(user_group_name=f"{self.id}_User_Group", company_name=self.company,
                                                     users_list=[f'{self.company}\\{self.firstname}'])
        self.log.info(f"Compliance search role added for {self.company}")

    @TestStep()
    def perform_backup(self):
        """Testcase step to perform backup"""
        self.log.info("Starting to perform backup")
        self.log.info("Starting Backup Now")
        # Running backup job as tenant admin
        self.commcell = self.tenant_commcell
        self.job = self.subclient.backup()
        self.log.info('Backup job started; job ID: %s', self.job.job_id)
        if not self.job.wait_for_completion():
            self.log.exception("Pending Reason %s", self.job.pending_reason)
            raise Exception('%s job not completed successfully.', self.job.job_type)
        self.log.info('%s job completed successfully.', self.job.job_type)
        self.log.info(f"Backup completed for {self.client_name}")

        self.log.info("Checking playback items")
        # Querying SOLR with admin commcell object
        self.commcell = self.admin_commcell
        solr = SolrHelper(self.online_exmblclient)
        solr.check_all_items_played_successfully(self.job.job_id)

    @TestStep()
    def validate_content_indexing(self):
        """Testcase step to get and validate CI job"""
        try:
            self.log.info("Getting automatic triggered CI job")
            self.online_exmblclient.cvoperations.get_automatic_ci_job()
            self.log.info("Validating CI Job")
            cvSolr = CVSolr(self.online_exmblclient)
            is_content_indexed = cvSolr.is_content_indexed(self.job.num_of_files_transferred)
            if is_content_indexed:
                self.log.info("Content indexing completed for the client")
            else:
                self.is_ci_failed = True
                raise Exception(f"Content indexed failed for the client {self.client_name}")
        except Exception as ex:
            self.is_ci_failed = True
            self.status = constants.FAILED
            raise ex

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
            search_text=self.query, page_size=50, app_type=ComplianceConstants.AppTypes.EXCHANGE)
        self.log.info(f"Total of {len(self.search_items)} items were found for the query")
        self.search_items = self.export_set.select(
            result_items=self.search_items, no_of_files=self.export_count)
        self.log.info(f"Randomly selected {self.export_count} items from the total search result")
        self.log.info(f"Now exporting the search result items to export {self.export_name}")
        restore_job_id = self.export_set.export_items_to_set(
            export_name=self.export_name, export_items=self.search_items,
            export_type=ComplianceConstants.ExportTypes.PST)
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
            export_type=ComplianceConstants.ExportTypes.PST)
        self.log.info("Downloaded files validated")

    def initialize_sdk_objects(self):
        self.log.info("Initializing required objects for testcase")
        self._client = self.tenant_commcell.clients.get(self.client_name)
        self._agent = self._client.agents.get(exchange_apps_constants.EXCHANGE_AGENT)
        self._instance = self._agent.instances.get(exchange_apps_constants.EXCHANGE_INSTANCE)
        self._backupset = self._instance.backupsets.get(exchange_apps_constants.EXCHANGE_BACKUPSET)
        self._subclient = self._backupset.subclients.get(exchange_apps_constants.EXCHANGE_SUBCLIENT)
        self.tcinputs['SubclientName'] = exchange_apps_constants.EXCHANGE_SUBCLIENT
        self.tcinputs['BackupsetName'] = exchange_apps_constants.EXCHANGE_BACKUPSET

        self.online_exmblclient = ExchangeMailbox(self)
        self.online_exmblclient.client_name = self.client_name
        self.online_exmblclient.cvoperations.client_name = self.client_name
        self.export_sets = self.tenant_commcell.export_sets
        self.compliance_search = self.tenant_commcell.activate.compliance_search()
        self.activate_helper = ActivateSDKHelper(self.tenant_commcell)

    def is_test_step_complete(self, step_enum):
        """
        checks if a test step is complete
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        Returns:
            bool                        --  Returns true if step is complete else false
        """
        return is_step_complete(self.test_progress, step_enum.value)

    def set_test_step_complete(self, step_enum):
        """
        Sets the progress with a give test step value
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        """
        set_step_complete(self.test_progress, step_enum.value)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Starting testcase run")
            if not self.is_test_step_complete(sc.CREATE_COMPANY):
                self.create_company_using_workflow()
                self.set_test_step_complete(sc.CREATE_COMPANY)
            else:
                self.log.info(f"{sc.CREATE_COMPANY.name} step complete. Not starting it")
                self.company = self.tenant_name.get()

            if not self.is_test_step_complete(sc.CHANGE_PASSWORD):
                self.change_company_admin_password()
                self.set_test_step_complete(sc.CHANGE_PASSWORD)
            else:
                self.log.info(f"{sc.CHANGE_PASSWORD.name} step complete. Not starting it")

            self.start_company_trial()

            if not self.is_test_step_complete(sc.ADD_COMPLIANCE_ROLE):
                self.activate_compliance()
                self.set_test_step_complete(sc.ADD_COMPLIANCE_ROLE)
            else:
                self.log.info(f"{sc.ADD_COMPLIANCE_ROLE.name} step complete. Not starting it")
            if not self.is_test_step_complete(sc.ENABLE_CI):
                self.enable_o365_plan_ci()
                self.set_test_step_complete(sc.ENABLE_CI)
            else:
                self.log.info(f"{sc.ENABLE_CI.name} step complete. Not starting it")
            if not self.is_test_step_complete(sc.CREATE_CLIENT):
                self.add_exchange_client()
                self.set_test_step_complete(sc.CREATE_CLIENT)
            else:
                self.log.info(f"{sc.CREATE_CLIENT.name} step complete. Not starting it")
                self.client_name = f"{self.company}_client"

            self.initialize_sdk_objects()

            if not self.is_test_step_complete(sc.ADD_USER):
                self.log.info("Adding mailbox to the client")
                subclient_content = {
                    'mailboxNames': self.users,
                    'plan_name': self.plan_name
                }
                self.subclient.set_user_assocaition(
                    subclient_content, use_policies=False)
                self.log.info("Mailbox added successfully")
                self.set_test_step_complete(sc.ADD_USER)
            else:
                self.log.info(f"{sc.ADD_USER.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.PERFORM_BACKUP):
                self.perform_backup()
                self.set_test_step_complete(sc.PERFORM_BACKUP)
            else:
                self.log.info(f"{sc.PERFORM_BACKUP.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.CONTENT_INDEXING):
                self.validate_content_indexing()
                self.set_test_step_complete(sc.CONTENT_INDEXING)
            else:
                self.log.info(f"{sc.CONTENT_INDEXING.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.CREATE_EXPORT_SET):
                self.create_export_set()
                self.set_test_step_complete(sc.CREATE_EXPORT_SET)
            else:
                self.log.info(f"{sc.CREATE_EXPORT_SET.name} step complete. Not starting it")
                self.export_set = self.export_sets.get(self.export_set_name)

            self.search_and_export_items()
            self.validate_download_items()
            self.log.info("Testcase execution finished")

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s',
                           type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED

    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.log.info("---------Deleting automatic added tenant--------------")
        self.tenant_helper = ActivateTenantHelper(self.admin_commcell)
        self.tenant_helper.delete_company(self.company)
        self.log.info(f"{self.company} deleted successfully")

    def tear_down(self):
        """Tear Down Function for the Test Case"""
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
                self.rehydrator.cleanup()
                self.log.info("Test case execution completed successfully")
            elif self.is_ci_failed:
                self.perform_cleanup()
                self.rehydrator.cleanup()
            else:
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.log.exception(
                "Exception while performing cleanup %s" %
                str(exp))
            raise exp
