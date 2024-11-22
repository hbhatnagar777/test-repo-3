# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 54157

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    init_tc()       --  Setup function for this testcase

    start_step1()   --  Check the status of workflow in Store

    start_step2()   --  Install the workflow from Store

    start_step3()   --  Validates the change of status once workflow installed

    run()           --  Main funtion for testcase execution

"""
#Test Suite Imports
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.config import get_config
from AutomationUtils.constants import CONFIG_FILE_PATH
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from AutomationUtils.idautils import CommonUtils

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Software store workflow Limit Restore Operation"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - Validate Limit Restore Operation workflow"
        self.browser = None
        self.webconsole = None
        self.srore = None
        self.workflow = "Limit Restore Operation"
        self.tcinputs = {
            'UserWithRestorePrivilege': None,
            'Password': None
        }

    def init_tc(self):
        """Setup function for this testcase"""
        try:
            self.storeutils = StoreUtils(self)
            username = _STORE_CONFIG.Cloud.username
            password = _STORE_CONFIG.Cloud.password
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update creds under {}".format(CONFIG_FILE_PATH))
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                _STORE_CONFIG.ADMIN_USERNAME,
                _STORE_CONFIG.ADMIN_PASSWORD
            )
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(
                username=username,
                password=password
            )

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def start_step1(self):
        """Install status should be shown for workflow
        when it is not installed"""
        pkg_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if pkg_status != "Install":
            raise CVTestStepFailure(
                f"[{self.workflow}] does "
                f"not have [Install] status, found [{pkg_status}]"
            )

    @test_step
    def start_step2(self):
        """Installing workflow Limit Restore Operation"""
        self.store.install_workflow(
            self.workflow, refresh=True
        )

    @test_step
    def start_step3(self):
        """Open status should be shown"""
        pkg_status = self.store.get_package_status(
            self.workflow,
            category="Workflows"
        )
        if pkg_status != "Open":
            raise CVTestStepFailure(
                f"[{self.workflow}] does"
                f"not have [Open] status after installation,"
                f"found status [{pkg_status}]"
            )

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self.commcell.refresh()
            workflow_helper = WorkflowHelper(self, self.workflow, deploy=False)
            # Class Initializations
            utility = OptionsSelector(self.commcell)
            user = self.tcinputs['UserWithRestorePrivilege']
            password = self.tcinputs['Password']
            job_manager = JobManager(commcell=self.commcell)
            entities = CVEntities(self)
            idautils = CommonUtils(self)
            client = self.client.client_name
            user_commcell = Commcell(self.commcell.commserv_name, user, password)
            entity_inputs = (['subclient'])
            entity_props_1 = entities.create(entity_inputs)
            subclient_object_1 = entity_props_1['subclient']['object']
            subclient_name_1 = entity_props_1['subclient']['name']
            self.log.info("Initiating backup job for subclient %s", subclient_name_1)
            backup_job_1 = idautils.subclient_backup(subclient_object_1, wait=False)
            job_manager.job = backup_job_1
            job_manager.wait_for_state()
            entity_props_2 = entities.create(entity_inputs)
            subclient_object_2 = entity_props_2['subclient']['object']
            subclient_name_2 = entity_props_2['subclient']['name']
            self.log.info("Initiating backup job for subclient %s", subclient_name_2)
            backup_job_2 = idautils.subclient_backup(subclient_object_2, wait=False)
            job_manager.job = backup_job_2
            job_manager.wait_for_state()
            workflow_helper.is_deployed(self.workflow)
            config_xml = """<RestrictUserGroup/><RestoreRequestLimit>1</RestoreRequestLimit>"""
            workflow_helper.modify_workflow_configuration(config_xml)
            try:
                machine_object = utility.get_machine_object(client)
                tmp_path = utility.create_directory(machine_object)
                destpath = machine_object.os_sep.join([tmp_path, "restore"])
                paths_1 = subclient_object_1.content
                paths_2 = subclient_object_2.content
                user_idautils = CommonUtils(user_commcell)
                instances = user_commcell.clients.get(client).agents.get(self.tcinputs['AgentName']).instances
                subclients = instances.get(
                    self.tcinputs['InstanceName']
                ).backupsets.get(self.tcinputs['BackupsetName']).subclients
                user_subc_object_1 = subclients.get(subclient_name_1)
                user_subc_object_2 = subclients.get(subclient_name_2)
                self.log.info("Initiating first Restore job")
                restore_job = user_idautils.subclient_restore_out_of_place(destpath, paths_1, client,
                                                                           user_subc_object_1, wait=False)
                job_manager.job = restore_job
                self.log.info("Initiating Second Restore job")
                user_idautils.subclient_restore_out_of_place(destpath, paths_2, client, user_subc_object_2)
                job_manager.wait_for_state()
                raise Exception(
                    'Restore request is processed successfully. Expected to restrict from business logic workflow')
            except Exception as excp:
                excp_msg = 'Currently 1 restore request is processing for User[{}]. Restore Limit is 1'.format(user)
                if excp_msg in str(excp):
                    self.log.info("Restore Request is restricted as expected from business logic workflow")
                else:
                    self.log.error(str(excp))
                    raise Exception("Validation of Limit restore Operation BL workflow failed with error {}".format(str(excp)))

        except Exception as excp:
            raise Exception("Exception {0}".format(str(excp)))
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            workflow_helper.delete(self.workflow)
            entities.cleanup()
