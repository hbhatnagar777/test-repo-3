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

    run()           --  run function of this test case
"""

# Test Suite imports
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (Browser, BrowserFactory)
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.Common.page_object import TestStep
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.idautils import CommonUtils
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.Workflow import workflowconstants as WC
from Server.Security.userhelper import UserHelper
from Server.JobManager.jobmanager_helper import JobManager

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Software store workflow Modify Active Job Authorization"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Modify Active Job Authorization workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = True
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow_store_name = "Modify Active Job Authorization"
        self.workflow = "Modify Active Job Authorization"
        self.dependent_workflow_store_name = "GetAndProcessAuthorization"
        self.dependent_workflow = "GetAndProcessAuthorization"

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(
                username=_STORE_CONFIG.Cloud.username,
                password=_STORE_CONFIG.Cloud.password
            )

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def start_step1(self):
        """Install status should be shown for workflow
        when it is not installed"""
        for workflow in [self.dependent_workflow_store_name, self.workflow_store_name]:
            pkg_status = self.store.get_package_status(workflow, category="Workflows")
            if pkg_status != "Install":
                raise CVTestStepFailure(
                    f"[{workflow}] does "
                    f"not have [Install] status, found [{pkg_status}]"
                )

    @test_step
    def start_step2(self):
        """After installing workflow, status should be Open"""
        for workflow in [self.dependent_workflow_store_name, self.workflow_store_name]:
            self.store.install_workflow(
                workflow, refresh=True
            )

    def run(self):
        """Main function for test case execution"""

        try:
            workflow_name = self.workflow
            dependent_workflow = self.dependent_workflow
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.commcell.workflows.refresh()

            # Class Initializations
            workflow_helper = WorkflowHelper(self, workflow_name, deploy=False)
            job_manager = JobManager(commcell=self.commcell)
            entities = CVEntities(self)
            idautils = CommonUtils(self)
            flag = False
            # ---------------------------------------------------------------------------------------------------------

            workflow_helper.test.log_step("""
                1. Create non admin user with admin privileges and corresponding commcell object
                2. Validate if the business logic workflows Modify Active Job Authorization and
                    GetAndProcessAuthorization are deployed
                3. Create a new subclient and start a backup job, and then suspend the job.
                4. Try killing the backup job from non admin user. It should be blocked
                5. Approve the workflow user interaction request to kill the job
                6. Get workflow job id for the business logic workflow and wait for it to complete.
                7. Validate if job is killed
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object
                Validate if the BL workflows Modify Active Job Authorization and
                    GetAndProcessAuthorization are deployed.
                Create a new subclient and start a backup job, and then suspend the job.
            """)
            response = workflow_helper.bl_workflows_setup([workflow_name, dependent_workflow], usergroup='View All')
            user_commcell = response[1]
            user = response[0]
            entity_inputs = (['backupset','subclient'])
            entity_props = entities.create(entity_inputs)
            subclient_object = entity_props['subclient']['object']
            backup_job = idautils.subclient_backup(subclient_object, wait=False)
            job_manager.job = backup_job
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Try killing the job from non admin user. It should be blocked by BL Workflow.
            """)
            try:
                self.log.info("Attempting to kill the job. Should be blocked by workflow [{0}]".format(workflow_name))
                user_job_object = user_commcell.job_controller.get(backup_job.job_id)
                user_job_object.kill()
                raise Exception("Killing job succeeded. Expected to be blocked from business logic workflow")
            except Exception as excp:
                if 'An email has been sent to the administrator' in str(excp):
                    self.log.info("Error as expected: [{0}]".format(str(excp)))
                    self.log.info("Kill job successfully blocked through business logic workflow.")
                else:
                    self.log.error(str(excp))
                    raise Exception("Job validation failed")
                job_status = backup_job.status
                assert job_status.lower() != 'killed', "Job Killed unexpectedly. Test Failed"
                assert job_status.lower() != 'kill pending', "Job Killed unexpectedly. Test Failed"
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Approve the workflow user interaction request to kill the job
                Get workflow job id for the business logic workflow and wait for it to complete.
                Validate if job is killed
            """)

            workflow_helper.process_user_requests(user, input_xml=WC.WORKFLOW_DEFAULT_USER_INPUTS % user)
            job_manager.wait_for_state(['completed', 'killed', 'committed'])
            self.log.info("Job [{0}] request completed via BL workflow's [Approve] action".format(backup_job.job_id))
            # ---------------------------------------------------------------------------------------------------------
            flag = True

        except Exception as excp:
            self.storeutils.handle_testcase_exception(excp)
            workflow_helper.test.fail(excp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            WorkflowHelper(self, workflow_name, deploy=False).delete([workflow_name, dependent_workflow])
            UserHelper(self.commcell).delete_user(user_name=user, new_user='admin')
            entities.cleanup()
            if not flag:
                job_manager.wait_for_state(['completed', 'killed', 'committed'])
