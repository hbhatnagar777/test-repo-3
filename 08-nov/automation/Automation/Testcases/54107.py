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

from cvpysdk.commcell import Commcell
from cvpysdk.subclient import Subclients

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
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.idautils import CommonUtils
from Server.Workflow import workflowconstants as WC
from Server.Security.userhelper import UserHelper
from Server.Security.userconstants import USERGROUP
from Server.JobManager.jobmanager_helper import JobManager

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):
    """Class for executing Software store workflow DeleteStoragePolicyAutorization """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate DeleteStoragePolicyAutorization workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.store = None
        self.storeutils = StoreUtils(self)
        self.workflow_store_name = "DeleteStoragePolicyAuthorization"
        self.workflow = "DeleteStoragePolicyAuthorization"
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
            user = self.id + '_' + OptionsSelector.get_custom_str()
            password = _STORE_CONFIG.Workflow.ComplexPasswords.CommonPassword
            user_helper = UserHelper(self.commcell)
            workflow_helper = WorkflowHelper(self, workflow_name, deploy=False)
            entities = CVEntities(self)
            idautils = CommonUtils(self)
            job_manager = JobManager(commcell=self.commcell)

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                1. Create non admin user with admin privledges and corresponding commcell object
                2. Validate if the business logic workflows DeleteStoragePolicyAuthorization and
                    GetAndProcessAuthorization are deployed
                3. Create a new storage policy
                4. Try deleting the stirage policy from non admin user. It should be blocked
                5. Approve the workflow user interaction request to kill the job
                6. Get workflow job id for the business logic workflow and wait for it to complete.
                7. Validate if job is killed
            """, 200)
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Create non admin user and corresponding commcell object
                Validate if the BL workflows DeleteStoragePolicyAuthorization and GetAndProcessAuthorization are
                    deployed.
                Create a new storagepolicy
            """)
            user_helper.create_user(user_name=user, full_name=user, email='test@commvault.com',
                                    password=password, local_usergroups=[USERGROUP.MASTER])
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            workflow_helper.is_deployed(workflow_name)
            workflow_helper.is_deployed(dependent_workflow)
            sp_props = entities.create(['storagepolicy','subclient'])
            subclient_object = sp_props['subclient']['object']
            backup_job = idautils.subclient_backup(subclient_object)
            subclients = Subclients(self.backupset)
            subclients.delete(subclient_object.name)
            sp_name = sp_props['storagepolicy']['name']
            user_sp = user_commcell.storage_policies
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Try deleting the storage policy from non admin user. It should be blocked
            """)
            try:
                self.log.info(
                    "Attempting to delete storage policy. Should be blocked by workflow [{0}]".format(workflow_name)
                )
                error_msg = user_sp.delete(sp_name)
                if 'An email has been sent to the administrator' not in error_msg:
                    raise Exception("Deleting storage policy succeeded. "
                                    "Expected to be blocked from business logic workflow")
            except Exception as excp:
                if 'An email has been sent to the administrator' in str(excp):
                    self.log.info("Error as expected: [{0}]".format(str(excp)))
                    self.log.info("Delete storagepolicy successfully blocked through business logic workflow.")
                else:
                    self.log.error(str(excp))
                    raise Exception("Delete storagepolicy validation failed")

                assert user_sp.has_policy(sp_name), "StoragePolicy deleted unexpectedly. Test Failed"
            # ---------------------------------------------------------------------------------------------------------

            # ---------------------------------------------------------------------------------------------------------
            workflow_helper.test.log_step("""
                Approve the workflow user interaction request to delete storagepolicy
                Get workflow job id for the business logic workflow and wait for it to complete.
                Validate if storage policy is deleted
            """)
            workflow_helper.process_user_requests(user, input_xml=WC.WORKFLOW_DEFAULT_USER_INPUTS % user)
            user_sp.refresh()
            assert not user_sp.has_policy(sp_name), "StoragePolicy *not deleted post user approval"
            self.log.info("StoragePolicy [{0}] deleted via BL workflow's [Approve] action".format(sp_name))
            # ---------------------------------------------------------------------------------------------------------

        except Exception as excp:
            self.storeutils.handle_testcase_exception(excp)
            workflow_helper.test.fail(excp)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            WorkflowHelper(self, workflow_name, deploy=False).delete([dependent_workflow, workflow_name])
            UserHelper(self.commcell).delete_user(user_name=user, new_user='admin')
            entities.cleanup()
