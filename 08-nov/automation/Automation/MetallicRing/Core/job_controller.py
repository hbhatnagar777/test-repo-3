# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Controller class for orchestrating the tasks in Metallic Ring

    JobController:

        __init__()                              --  Initializes Job Controller class object

        __is_user_task_complete                 --  Checks if user task is complete

        start_task                              --  Starts the Tasks involved in configuring the ring

        start_hub_post_config_validator_task    --  Starts the hub post config helper task

        start_hub_pipeline_helper_task          --  Starts the hub pipeline helper task

        start_hub_config_helper_task            --  Starts and updates the status hub configuration helper task

        start_hub_resource_helper_task          --  Starts and updates the result of hub resource helper task

        start_vm_helper_task                    --  Starts and updates the result of vm provisioning helper task

        start_helper_task                       --  Starts and updates the result of individual task based on the task type passed

        insert_config                           --  Inserts the task information into sqlite database

        update_config                           --  Updates the task information into sqlite database

        read_config                             --  Reads the configuration from metallic config file and
                                                    sets it for the ring tasks to complete

        set_ring_details                        --  Sets the information about the ring

        set_infra_details                       --  Sets the information about the infrastructure clients

        set_client_details                      --  Sets the client details needed for the ring automation
"""

from time import sleep

from AutomationUtils import logger
from AutomationUtils.config import get_config
from MetallicHub.Helpers.azure_config_helper import AzureConfigHelper
from MetallicHub.Helpers.azure_resource_helper import AzureResourceHelper
from MetallicHub.Helpers.azure_pipeline_helper import AzurePipelineHelper
from MetallicHub.Helpers.light_house_helper import LightHouseHelper
from MetallicHub.Helpers.post_config_validator import PostConfigRingHelper
from MetallicHub.Utils.Constants import CheckPRType
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper
from MetallicRing.DBQueries import Constants as db_cs
from MetallicRing.Helpers.alerts_helper import AlertRingHelper
from MetallicRing.Helpers.admin_helper import AdminRingMaintenanceHelper, AdminRingSystemHelper, \
    CustomAdminRingSystemHelper, CustomAdminRingMaintenanceHelper
from MetallicRing.Helpers.client_group_helper import ClientGroupRingHelper
from MetallicRing.Helpers.client_helper import ClientRingHelper
from MetallicRing.Helpers.commserv_helper import CommservRingHelper
from MetallicRing.Helpers.container_helper import ContainerRingHelper
from MetallicRing.Helpers.email_helper import EmailHelper
from MetallicRing.Helpers.index_server_helper import IndexServerRingHelper
from MetallicRing.Helpers.media_agent_helper import MediaAgentRingHelper
from MetallicRing.Helpers.metrics_helper import MetricsRingHelper
from MetallicRing.Helpers.network_helper import NetworkRingHelper
from MetallicRing.Helpers.report_helper import ReportsRingHelper
from MetallicRing.Helpers.roles_helper import RolesRingHelper
from MetallicRing.Helpers.smart_folder_helper import SmartFolderHelper
from MetallicRing.Helpers.snap_controller import RingSnapController
from MetallicRing.Helpers.storage_helper import StorageRingHelper, CustomStorageRingHelper
from MetallicRing.Helpers.user_helper import UserRingHelper
from MetallicRing.Helpers.user_group_helper import UserGroupRingHelper
from MetallicRing.Helpers.vm_provisioning import VMProvisioningHelper
from MetallicRing.Helpers.workflow_helper import WorkflowRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils
from cvpysdk.commcell import Commcell


class JobController:
    """Controller class for orchestrating the tasks in Metallic Ring"""

    def __init__(self):
        try:
            self.log = logger.get_log()
            self.config = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH)
            self.ring_id = None
            self.ring = self.config.Metallic.ring
            self.metrics_config = self.config.Metallic.metrics_commcell
            self.ring_id = self.ring.id
            self.ring_name = self.ring.name
            self.current_task = db_cs.VM_SNAP_TASK
            self.ring_commcell_config = self.ring.commserv
            self.ring_webconsole_config = self.ring.web_consoles[0]
            self.email = EmailHelper(self.ring_name, self.ring_commcell_config.hostname)
            self.db_obj = SQLiteDBQueryHelper()
            is_cs_installed = self.__is_vm_task_complete(db_cs.VM_INSTALL_SW_TASK_CS)
            self.vm_helper = None
            self.container_helper = None
            if self.ring.vm_provision:
                self.vm_helper = VMProvisioningHelper(is_cs_installed)
            elif self.ring.container_provision:
                # Container related task
                self.container_helper = ContainerRingHelper()
            else:
                if not self.__is_user_task_complete():
                    self.log.info(f"Initializing commcell with user - [{self.ring_commcell_config.username}]")
                    self.ring_commcell = Commcell(self.ring_webconsole_config.hostname,
                                                  self.ring_commcell_config.username, self.ring_commcell_config.password)
                else:
                    self.log.info(f"Initializing commcell with user - [{self.ring_commcell_config.new_username}]")
                    self.ring_commcell = Commcell(self.ring_webconsole_config.hostname,
                                                  self.ring_commcell_config.new_username,
                                                  self.ring_commcell_config.new_password)
            self.log.info(f"Initializing metrics commcell with user - [{self.metrics_config.username}]")
            self.metrics_commcell = Commcell(self.metrics_config.hostname, self.metrics_config.username,
                                             self.metrics_config.password)
            self.log.info("All commcells initialized successfully")
        except Exception as exp:
            error_desc = f"Exception occurred while configuring the metallic ring. {exp}"
            self.db_obj.execute_query(db_cs.UPDATE_RING_INFO_STATUS % (db_cs.RING_TASK_FAILED, self.ring_name.lower()))
            self.db_obj.execute_query(db_cs.UPDATE_AVAILABLE_RING_STATUS % (db_cs.RING_TASK_FAILED,
                                                                            self.ring.unique_id,
                                                                            self.ring_name.lower()))
            self.log.info(error_desc)
            raise

    def __is_user_task_complete(self):
        """
        Checks if user task is complete
        Returns:
            bool    -   True, if user task is complete
                        False, if user task is not complete
        """
        self.log.info("Checking if user task is complete")
        query = db_cs.SELECT_RING_CONFIG_QUERY % (self.ring_name, db_cs.USER_TASK)
        result = self.db_obj.execute_query(query)
        self.log.info(f"Query to check user task completion executed successfully [{result}]")
        if len(result.rows) != 0:
            state = result.rows[0][1]
            if state == db_cs.STATE_COMPLETE:
                self.log.info("user task is already complete")
                return True
        self.log.info("user task is not complete")
        return False

    def __is_vm_task_complete(self, task_type):
        """
        Checks if user task is complete
        Returns:
            bool    -   True, if user task is complete
                        False, if user task is not complete
        """
        self.log.info("Checking if user task is complete")
        query = db_cs.SELECT_RING_CONFIG_QUERY % (self.ring_name, task_type)
        result = self.db_obj.execute_query(query)
        self.log.info(f"Query to check user task completion executed successfully [{result}]")
        if len(result.rows) != 0:
            state = result.rows[0][1]
            if state == db_cs.STATE_COMPLETE:
                self.log.info("user task is already complete")
                return True
        self.log.info("user task is not complete")
        return False

    def start_task(self):
        """
        Starts the Tasks involved in configuring the ring
        """
        should_provision_containers = self.ring.container_provision
        try:
            self.log.info("Starting the rings tasks. Reading the config file")
            self.log.info("Starting VM creation task")
            self.start_vm_helper_task(db_cs.VM_CREATE_TASK)
            self.log.info("VM creation complete. Starting with VM configuration task")
            self.start_vm_helper_task(db_cs.VM_CONFIG_TASK)
            self.log.info("VM configuration task complete. Starting with CS install SW task")
            self.start_vm_helper_task(db_cs.VM_INSTALL_SW_TASK_CS)
            self.log.info("Software install on CS complete. Starting with MA SW install task")
            self.start_vm_helper_task(db_cs.VM_INSTALL_SW_TASK_MA)
            self.log.info("SW install task in MA complete. Starting with WS SW install task")
            self.start_vm_helper_task(db_cs.VM_INSTALL_SW_TASK_WS)
            self.log.info("SW install task in WS complete. Starting with WC SW install task")
            self.start_vm_helper_task(db_cs.VM_INSTALL_SW_TASK_WC)
            self.log.info("SW install task in WC complete. Starting with NWP SW install task")
            self.start_vm_helper_task(db_cs.VM_INSTALL_SW_TASK_NP)
            self.log.info("SW install task in NWP complete. Initializing Ring commcell")
            should_provision_vm = self.ring.vm_provision
            if should_provision_containers:
                self.start_helper_task(self.container_helper, db_cs.CONTAINER_TASK)
            if should_provision_vm or should_provision_containers:
                self.ring_commcell = Commcell(self.ring_webconsole_config.hostname,
                                              self.ring_commcell_config.username, self.ring_commcell_config.password)
            self.read_config()
            self.log.info("Checking readiness before starting the automation rung")
            self.start_helper_task(RingSnapController(), db_cs.VM_SNAP_TASK)
            self.start_helper_task(UserRingHelper(self.ring_commcell), db_cs.USER_TASK)
            self.start_helper_task(UserGroupRingHelper(self.ring_commcell), db_cs.USER_GROUP_TASK)
            self.start_helper_task(RolesRingHelper(self.ring_commcell), db_cs.ROLES_TASK)
            if self.ring.provision_type == cs.RingProvisionType.CUSTOM.value:
                self.start_helper_task(CustomAdminRingMaintenanceHelper(self.ring_commcell), db_cs.ADMIN_MAINTENANCE_TASK)
                self.start_helper_task(CustomAdminRingSystemHelper(self.ring_commcell), db_cs.ADMIN_SYSTEM_TASK)
                self.start_helper_task(CustomStorageRingHelper(self.ring_commcell), db_cs.STORAGE_TASK)
            else:
                self.start_helper_task(AdminRingMaintenanceHelper(self.ring_commcell), db_cs.ADMIN_MAINTENANCE_TASK)
                self.start_helper_task(AdminRingSystemHelper(self.ring_commcell), db_cs.ADMIN_SYSTEM_TASK)
                self.start_helper_task(StorageRingHelper(self.ring_commcell), db_cs.STORAGE_TASK)
            self.start_helper_task(MediaAgentRingHelper(self.ring_commcell), db_cs.MEDIA_AGENT_TASK)
            self.start_helper_task(IndexServerRingHelper(self.ring_commcell), db_cs.INDEX_SERVER_TASK)
            self.start_helper_task(ClientGroupRingHelper(self.ring_commcell), db_cs.CLIENT_GROUP_TASK)
            self.start_helper_task(ClientRingHelper(self.ring_commcell), db_cs.CLIENT_TASK)
            self.start_helper_task(NetworkRingHelper(self.ring_commcell), db_cs.NETWORK_TASK)
            self.start_helper_task(CommservRingHelper(self.ring_commcell), db_cs.COMMCELL_TASK)
            self.start_helper_task(WorkflowRingHelper(self.ring_commcell), db_cs.WORKFLOW_TASK)
            self.start_helper_task(ReportsRingHelper(self.ring_commcell, self.ring_commcell_config.new_username,
                                                     self.ring_commcell_config.new_password), db_cs.REPORT_TASK)
            self.start_helper_task(MetricsRingHelper(self.metrics_commcell), db_cs.METRIC_SERVER_TASK)
            self.start_helper_task(AlertRingHelper(self.ring_commcell), db_cs.ALERT_TASK)
            self.start_helper_task(SmartFolderHelper(self.ring_commcell), db_cs.SMART_FOLDER_TASK)
            self.start_helper_task(LightHouseHelper(), db_cs.LIGHT_HOUSE_TASK)
            self.log.info("Ring tasks complete")
            should_perform_hub_task = self.ring.hub_config
            if should_perform_hub_task:
                self.log.info("Hub Task is set. Starting hub tasks.")
                self.start_hub_task()
                self.db_obj.execute_query(db_cs.UPDATE_RING_INFO_STATUS % (db_cs.RING_TASK_COMPLETE,
                                                                           self.ring_name.lower()))
            else:
                self.db_obj.execute_query(db_cs.UPDATE_RING_INFO_STATUS % (db_cs.RING_TASK_COMPLETE_HUB_PENDING,
                                                                           self.ring_name.lower()))
            self.db_obj.execute_query(db_cs.UPDATE_AVAILABLE_RING_STATUS % (db_cs.RING_TASK_COMPLETE,
                                                                            self.ring.unique_id,
                                                                            self.ring_name.lower()))
            self.email.send_next_steps_mail()
        except Exception as exp:
            error_desc = f"Exception occurred while configuring the metallic ring. {exp}"
            self.db_obj.execute_query(db_cs.UPDATE_RING_INFO_STATUS % (db_cs.RING_TASK_FAILED, self.ring_name.lower()))
            self.db_obj.execute_query(db_cs.UPDATE_AVAILABLE_RING_STATUS % (db_cs.RING_TASK_FAILED,
                                                                            self.ring.unique_id,
                                                                            self.ring_name.lower()))
            self.log.info(error_desc)
        finally:
            self.log.info("Ring task execution finished. Sending email")
            self.email.send_status_mail()
            self.log.info("Email sent")

    def start_hub_task(self):
        """
        Starts the hub tasks.
            1. Resource creation task
            2. Config files creation/update task
            3. Pipeline tasks
        """
        self.log.info("Request received to start hub configuration task. \n starting terraform repo clone task")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_CLONE_TASK)
        self.log.info("Clone task complete. starting checkout task")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_CHECKOUT_TASK)
        self.log.info("Checkout task complete. starting terraform config update task")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_UPDATE_TASK)
        self.log.info("Update task complete. starting push configuration task")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_PUSH_TASK)
        self.log.info("All configs pushed. Waiting for PR to complete")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_WAIT_FOR_PR_COMPLETE_TASK)
        self.log.info("PR complete. starting azure resource deployment task")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_DEPLOY_TASK)
        self.log.info("Resource creation task complete. Pushing the latest changes to repo")
        self.start_hub_resource_helper_task(db_cs.HUB_TERRAFORM_PUSH_TASK_STAGE_2)
        self.log.info("All changes pushed. Starting backend pool creation  task")
        self.start_hub_resource_helper_task(db_cs.HUB_RESOURCE_CREATE_BP_TASK)
        self.log.info("BP creation complete. starting health probe creation task")
        self.start_hub_resource_helper_task(db_cs.HUB_RESOURCE_CREATE_HP_TASK)
        self.log.info("HP creation complete. starting backend setting creation task")
        self.start_hub_resource_helper_task(db_cs.HUB_RESOURCE_CREATE_BS_TASK)
        self.log.info("Backend settings creation complete. starting listener creation task")
        self.start_hub_resource_helper_task(db_cs.HUB_RESOURCE_CREATE_LISTENER_TASK)
        self.log.info("Listener creation complete. starting create rules creation task")
        self.start_hub_resource_helper_task(db_cs.HUB_RESOURCE_CREATE_RULES_TASK)
        self.log.info("Rules creation complete. starting DNS record creation task")
        self.start_hub_resource_helper_task(db_cs.HUB_RESOURCE_CREATE_DNS_REC_TASK)
        self.log.info("DNS record creation complete. \n\n\n starting hub config files task")

        self.log.info("starting Cloning task for the config files")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_CLONE_TASK)
        self.log.info("Clone task complete. starting checkout task")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_CHECKOUT_TASK)
        self.log.info("Checkout task complete. starting config update task")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_UPDATE_TASK)
        self.log.info("Updating config files task complete. starting set access policies task")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_SET_ACCESS_POLICIES_TASK)
        self.log.info("Set access policies task complete. starting pushing of config files task ro repo")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_PUSH_TASKS)
        self.log.info("Config files pushed to Git. Starting wait for PR task")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_WAIT_FOR_PR_COMPLETE_STAGE_I)
        self.log.info("PR task complete. starting Pipeline task")

        self.log.info("Starting CORS allowed domain task complete. starting checkout task")
        self.start_hub_pipeline_helper_task(db_cs.HUB_PIPELINE_SET_CORS_ALLOWED_DOMAIN_TASK)
        self.log.info("CORS allowed domain task complete. starting create pipeline variables task")
        self.start_hub_pipeline_helper_task(db_cs.HUB_PIPELINE_CREATE_VARIABLES_TASK)
        self.log.info("Variables creation task complete. starting to update file definition for pipeline stage")
        self.start_hub_pipeline_helper_task(db_cs.HUB_PIPELINE_UPDATE_FILE_DEFINITION_TASK)
        self.log.info("File definition updated and writted to file. starting update definition to devops task")
        self.start_hub_pipeline_helper_task(db_cs.HUB_PIPELINE_UPDATE_RELEASE_DEFINITION_TASK)
        self.log.info("Update pipeline def to azure devops task complete. starting run pipeline task")
        self.start_hub_pipeline_helper_task(db_cs.HUB_PIPELINE_RUN_PIPELINE_TASK_STAGE_1)
        self.log.info("Request received to update lead and legal value")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_UPDATE_LEAD_AND_LEGAL)
        self.log.info("Update lead and legal complete. Wait for PR completion")
        self.start_hub_config_helper_task(db_cs.HUB_CONFIG_WAIT_FOR_PR_COMPLETE_STAGE_II)
        self.log.info("PR complete. Runing the second stage pipeline")
        self.start_hub_pipeline_helper_task(db_cs.HUB_PIPELINE_RUN_PIPELINE_TASK_STAGE_2)
        self.log.info("2nd stage pipeline run complete. \n\n Sleeping for 2 hours to complete running the pipeline. ")

        self.start_hub_post_config_validator_task(db_cs.HUB_POST_CONFIG_VALIDATOR)
        self.log.info("Hub task complete.")

    def start_hub_post_config_validator_task(self, task_type):
        """
        Starts the hub post config helper task
        """
        self.current_task = task_type
        self.log.info(f"starting the helper task [{self.current_task}]. Checking for status of the task")
        task_status = self.insert_config(task_type)
        self.log.info(f"Is task status complete: [{task_status}]")
        if task_status:
            self.log.info("Task already completed. Not starting it")
            return
        self.log.info("Task status is not complete. Calling the helper to start the task")
        status = cs.FAILED
        message = None
        post_config_helper = PostConfigRingHelper(self.metrics_commcell)
        if task_type == db_cs.HUB_POST_CONFIG_VALIDATOR:
            status, message = post_config_helper.start_task()
        self.log.info(f"Status of helper task is [{status}]. Updating the status in db")
        self.update_config(task_type, status, message)
        self.log.info("updated status successfully")

    def start_hub_pipeline_helper_task(self, task_type):
        """
        Starts the hub pipeline helper task
        """
        self.current_task = task_type
        self.log.info(f"starting the helper task [{self.current_task}]. Checking for status of the task")
        task_status = self.insert_config(task_type)
        self.log.info(f"Is task status complete: [{task_status}]")
        if task_status:
            self.log.info("Task already completed. Not starting it")
            return
        self.log.info("Task status is not complete. Calling the helper to start the task")
        status = cs.FAILED
        message = None
        pipeline_helper = AzurePipelineHelper(self.ring_name, RingUtils.get_ring_string(self.ring_id))
        if task_type == db_cs.HUB_PIPELINE_SET_CORS_ALLOWED_DOMAIN_TASK:
            status, message = pipeline_helper.set_orbit_app_CORS_allowed_domain()
        elif task_type == db_cs.HUB_PIPELINE_CREATE_VARIABLES_TASK:
            status, message = pipeline_helper.create_pipeline_variables()
        elif task_type == db_cs.HUB_PIPELINE_UPDATE_FILE_DEFINITION_TASK:
            status, message = pipeline_helper.update_definition_to_file()
        elif task_type == db_cs.HUB_PIPELINE_UPDATE_RELEASE_DEFINITION_TASK:
            status, message = pipeline_helper.update_pipeline_definition()
        elif task_type in (db_cs.HUB_PIPELINE_RUN_PIPELINE_TASK_STAGE_1, db_cs.HUB_PIPELINE_RUN_PIPELINE_TASK_STAGE_2):
            status, message = pipeline_helper.run_pipeline_api()
        self.log.info(f"Status of helper task is [{status}]. Updating the status in db")
        self.update_config(task_type, status, message)
        self.log.info("updated status successfully")

    def start_hub_config_helper_task(self, task_type):
        """
        Starts and updates the status hub configuration helper task
        """
        self.current_task = task_type
        self.log.info(f"starting the helper task [{self.current_task}]. Checking for status of the task")
        task_status = self.insert_config(task_type)
        self.log.info(f"Is task status complete: [{task_status}]")
        if task_status:
            self.log.info("Task already completed. Not starting it")
            return
        self.log.info("Task status is not complete. Calling the helper to start the task")
        status = cs.FAILED
        message = None
        config_helper = AzureConfigHelper(self.ring_commcell)
        if task_type == db_cs.HUB_CONFIG_CLONE_TASK:
            status, message = config_helper.perform_clone_task()
        elif task_type == db_cs.HUB_CONFIG_CHECKOUT_TASK:
            status, message = config_helper.perform_checkout_task()
        elif task_type == db_cs.HUB_CONFIG_UPDATE_TASK:
            status, message = config_helper.perform_update_task()
        elif task_type == db_cs.HUB_CONFIG_SET_ACCESS_POLICIES_TASK:
            status, message = config_helper.set_key_vault_access_policies()
        elif task_type == db_cs.HUB_CONFIG_PUSH_TASKS:
            status, message = config_helper.perform_git_push_tasks()
        elif task_type == db_cs.HUB_CONFIG_UPDATE_LEAD_AND_LEGAL:
            status, message = config_helper.update_lead_n_legal_value()
        elif task_type == db_cs.HUB_CONFIG_WAIT_FOR_PR_COMPLETE_STAGE_I:
            status, message = config_helper.wait_for_pr_complete()
        elif task_type == db_cs.HUB_CONFIG_WAIT_FOR_PR_COMPLETE_STAGE_II:
            status, message = config_helper.wait_for_pr_complete(pr_type=CheckPRType.UPDATE)
        self.log.info(f"Status of helper task is [{status}]. Updating the status in db")
        self.update_config(task_type, status, message)
        self.log.info("updated status successfully")

    def start_hub_resource_helper_task(self, task_type):
        """
        Starts and updates the result of hub resource helper task
        """
        self.current_task = task_type
        self.log.info(f"starting the helper task [{self.current_task}]. Checking for status of the task")
        task_status = self.insert_config(task_type)
        self.log.info(f"Is task status complete: [{task_status}]")
        if task_status:
            self.log.info("Task already completed. Not starting it")
            return
        self.log.info("Task status is not complete. Calling the helper to start the task")
        status = cs.FAILED
        message = None
        resource_helper = AzureResourceHelper(self.ring_name, RingUtils.get_ring_string(self.ring_id),
                                              self.ring.hub_info.subnet_info)
        if task_type == db_cs.HUB_TERRAFORM_CLONE_TASK:
            status, message = resource_helper.perform_clone_task()
        elif task_type == db_cs.HUB_TERRAFORM_CHECKOUT_TASK:
            status, message = resource_helper.perform_checkout_task()
        elif task_type == db_cs.HUB_TERRAFORM_UPDATE_TASK:
            status, message = resource_helper.perform_update_task()
        elif task_type == db_cs.HUB_TERRAFORM_PUSH_TASK:
            status, message = resource_helper.perform_git_push_tasks()
        elif task_type == db_cs.HUB_TERRAFORM_WAIT_FOR_PR_COMPLETE_TASK:
            status, message = resource_helper.wait_for_pr_complete()
        elif task_type == db_cs.HUB_TERRAFORM_DEPLOY_TASK:
            status, message = resource_helper.create_resources_with_terraform()
        elif task_type == db_cs.HUB_TERRAFORM_PUSH_TASK_STAGE_2:
            status, message = resource_helper.perform_git_push_tasks(add_all=False)
        elif task_type == db_cs.HUB_RESOURCE_CREATE_BP_TASK:
            status, message = resource_helper.create_backend_pool()
        elif task_type == db_cs.HUB_RESOURCE_CREATE_HP_TASK:
            status, message = resource_helper.create_health_probe()
        elif task_type == db_cs.HUB_RESOURCE_CREATE_BS_TASK:
            status, message = resource_helper.create_backend_settings()
        elif task_type == db_cs.HUB_RESOURCE_CREATE_LISTENER_TASK:
            status, message = resource_helper.create_listeners()
        elif task_type == db_cs.HUB_RESOURCE_CREATE_RULES_TASK:
            status, message = resource_helper.create_rules()
        elif task_type == db_cs.HUB_RESOURCE_CREATE_DNS_REC_TASK:
            status, message = resource_helper.create_dns_records()
        self.log.info(f"Status of helper task is [{status}]. Updating the status in db")
        self.update_config(task_type, status, message)
        self.log.info("updated status successfully")

    def start_vm_helper_task(self, task_type):
        """
        Starts and updates the result of vm provisioning helper task
        """
        self.current_task = task_type
        should_provision_vm = self.ring.vm_provision
        message = None
        task_status = self.insert_config(task_type)
        if should_provision_vm:
            self.log.info(f"starting the helper task [{self.current_task}]. Checking for status of the task")
            self.log.info(f"Is task status complete: [{task_status}]")
            if task_status:
                self.log.info("Task already completed. Not starting it")
                return
            self.log.info("Task status is not complete. Calling the helper to start the task")
            status = cs.FAILED
            if task_type == db_cs.VM_CREATE_TASK:
                status, message = self.vm_helper.create_terraform_vms()
            elif task_type == db_cs.VM_CONFIG_TASK:
                status, message = self.vm_helper.configure_VMs()
            elif task_type == db_cs.VM_INSTALL_SW_TASK_CS:
                status, message = self.vm_helper.install_CS_software()
            elif task_type == db_cs.VM_INSTALL_SW_TASK_MA:
                status, message = self.vm_helper.install_MA_software()
            elif task_type == db_cs.VM_INSTALL_SW_TASK_WS:
                status, message = self.vm_helper.install_WS_software()
            elif task_type == db_cs.VM_INSTALL_SW_TASK_WC:
                status, message = self.vm_helper.install_WC_software()
            elif task_type == db_cs.VM_INSTALL_SW_TASK_NP:
                status, message = self.vm_helper.install_NP_software()
        else:
            status = cs.PASSED
        self.log.info(f"Status of helper task is [{status}]. Updating the status in db")
        self.update_config(task_type, status, message)
        self.log.info("updated status successfully")

    def start_helper_task(self, helper_object, task_type):
        """
        Starts and updates the result of individual task based on the task type passed
        Args:
            helper_object(object)       -   object of the helper for which the task has to start
            task_type(int)                   -   Type of task invoked
        """
        self.current_task = task_type
        self.log.info(f"starting the helper task [{self.current_task}]. Checking for status of the task")
        task_status = self.insert_config(task_type)
        self.log.info(f"Is task status complete: [{task_status}]")
        if task_status:
            self.log.info("Task already completed. Not starting it")
            return
        self.log.info("Task status is not complete. Calling the helper to start the task")
        status, message = helper_object.start_task()
        self.log.info(f"Status of helper task is [{status}]. Updating the status in db")
        self.update_config(task_type, status, message)
        self.log.info("updated status successfully")

    def insert_config(self, task_type):
        """
        Inserts the task information into sqlite database
        Args:
            task_type(int)     -   Type of task
        """
        self.log.info(f"Adding new config information into sqlite DB for task type [{task_type}]")
        query = db_cs.SELECT_RING_CONFIG_QUERY % (self.ring_name.lower(), task_type)
        self.log.info(f"Query used for selection - [{query}]")
        result = self.db_obj.execute_query(query)
        self.log.info(f"Result of query execution - [{result}]")
        if len(result.rows) != 0:
            state = result.rows[0][1]
            if state == db_cs.STATE_COMPLETE:
                self.log.info("Task already completed. Returning task status as complete")
                return True
            self.log.info("Task not complete. Updating the status to resumed")
            self.update_config(task_type, cs.RESUMED, "")
            self.log.info("Status in DB updated successfully")
        else:
            self.log.info("Task is new. Inserting the information into DB")
            query = db_cs.INSERT_RING_CONFIG_QUERY % (db_cs.STATE_STARTED, '%s', self.ring_name.lower(), task_type)
            self.log.info(f"Query used - [{query}]")
            self.db_obj.execute_query(query)
            self.log.info(f"Status of the task [{task_type}] inserted successfully. Stating the task")
        return False

    def update_config(self, task_type, status, message=None):
        """
        Updates the task information into sqlite database
        Args:
            task_type(int)      -   Type of task
            status(str)         -   Status of the task
            message(str)        -   Reason for failure or success
        """
        query = None
        self.log.info(f"updating the status of task [{task_type}] to [{status}]")
        if status == cs.FAILED:
            if message is not None:
                message = message.replace("'", "''")
                self.log.info(f"Task failed with error [{message}]")
            query = db_cs.UPDATE_RING_CONFIG_QUERY % (db_cs.STATE_FAILED, '%s', message, self.ring_name.lower(), task_type)
            self.log.info(f"Query used for updating ring config. query [{query}]")
            if task_type in (db_cs.ALERT_TASK, db_cs.WORKFLOW_TASK, db_cs.REPORT_TASK):
                self.log.info("Optional tasks failed. We are continuing with other tasks")
            else:
                self.log.info(f"Task [{task_type}] failed to execute. Please check the failure reason and try again")
                self.log.info(f"query for updating the status to failed: [{query}]")
                self.db_obj.execute_query(query)
                self.log.info("DB updated successfully")
                raise Exception(
                    f"Failed to complete the following task [{task_type}]. Please check the failure message"
                    " and try again")
        elif status == cs.PASSED:
            query = db_cs.UPDATE_RING_CONFIG_QUERY % (db_cs.STATE_COMPLETE, '%s', "", self.ring_name.lower(), task_type)
        elif status == cs.STARTED:
            query = db_cs.UPDATE_RERUN_RING_CONFIG_QUERY % (db_cs.STATE_STARTED, '%s', self.ring_name.lower(), task_type)
        elif status == cs.RESUMED:
            query = db_cs.UPDATE_RING_CONFIG_QUERY % (db_cs.STATE_STARTED, '%s', "", self.ring_name.lower(), task_type)
        self.log.info(f"query for updating the status - [{query}]")
        self.db_obj.execute_query(query)
        self.log.info("Task status updated successfully")

    def read_config(self):
        """
        Reads the configuration from metallic config file and sets it for the ring tasks to complete
        Raises:
            Exception
                When media agent client is not present in the commcell
        """
        self.log.info("Reading Metallic configuration file needed for starting the ring automation")
        self.set_ring_details()
        self.log.info("Ring details set successfully. Reading CS client details")
        self.set_infra_details(cs.Infra.CS.name, self.ring_commcell.commcell_id,
                               self.ring.commserv.client_name)
        self.log.info("CS client details read successfully")
        media_agents = self.ring.media_agents
        self.log.info("Reading Media agents information from config")
        for media_agent in media_agents:
            client_name = media_agent.client_name
            if not self.ring_commcell.media_agents.has_media_agent(client_name):
                raise Exception(f"Media agent client [{client_name}] is not present in the commcell")
            media_agent = self.ring_commcell.media_agents.get(client_name)
            self.log.info("Setting media agents information in DB")
            self.set_infra_details(cs.Infra.MA.name, media_agent.media_agent_id, media_agent.media_agent_name)
            self.log.info("Information set in DB successfully")
        self.log.info("Setting Webserver information in DB")
        self.set_client_details(self.ring.web_servers, cs.Infra.WS.name)
        self.log.info("Set Webserver information in DB. Setting web console information in DB")
        self.set_client_details(self.ring.web_consoles, cs.Infra.WC.name)
        self.log.info("Set Web console information in DB. Setting index server information in DB")
        self.set_client_details(self.ring.index_servers, cs.Infra.IS.name)
        self.log.info("Set index server information in DB. Setting network proxy information in DB")
        self.set_client_details(self.ring.network_proxies, cs.Infra.NWP.name)
        self.log.info("Set network proxy console information in DB")

    def set_ring_details(self):
        """
        Sets the information about the ring
        """
        self.log.info("Checking if ring information is present in DB")
        query = db_cs.SELECT_RING_QUERY % (self.ring_id, self.ring_name.lower())
        self.log.info(f"Query to fetch ring information - [{query}]")
        result = self.db_obj.execute_query(query)
        self.log.info(f"Result - [{result}]")
        if len(result.rows) == 0:
            self.log.info("No entry is presnt in DB. Inserting the details for the ring")
            self.db_obj.execute_query(db_cs.INSERT_RING_QUERY % (self.ring_id, self.ring_name.lower()))
            self.log.info("Ring details are set in DB")
        else:
            self.db_obj.execute_query(db_cs.UPDATE_RING_INFO_STATUS % (db_cs.RING_TASK_RUNNING, self.ring_name.lower()))
            self.log.info("Ring details are already present in DB. Proceeding without creating a new entry")

    def set_infra_details(self, infra_type, client_id, client_name):
        """
        Sets the information about the infrastructure clients
        Args:
            infra_type(str)         -   represents the infrastructure type
            client_id(int)          -   id of the client in the commcell
            client_name(str)        -   name of the client in the commcell

        """
        self.log.info(f"Setting infra details for client [{client_name}]. Infra type [{infra_type}]")
        query = db_cs.SELECT_RING_INFRA_QUERY % (infra_type, self.ring_id, client_id)
        self.log.info(f"query to check if infra entry is already present - [{query}]")
        result = self.db_obj.execute_query(query)
        self.log.info(f"query result - [{result}]")
        if len(result.rows) == 0:
            self.log.info("Data is not present in DB. Proceeding to add the entry to DB")
            self.db_obj.execute_query(db_cs.INSERT_RING_INFRA_QUERY % (infra_type, client_id,
                                                                       client_name, '%s',
                                                                       self.ring_id))
            self.log.info("DB entry added successfully")
        else:
            self.log.info(f"Infra [{infra_type}][{client_name}] details are already present in DB. "
                          f"Proceeding without creating a new entry")

    def set_client_details(self, client_list, infra_type):
        """
        Sets the client details needed for the ring automation
        Args:
            client_list(list)       -   List of client names
            infra_type(str)         -   Type of infrastructure client

        Raises:
            Exception:
                When Index server client node is not present in the commcell
                When client with a given name is not present in the commcell
        """
        self.log.info(f"setting the following clients' details - [{client_list}] for infra type [{infra_type}]")
        clients = self.ring_commcell.clients
        for client in client_list:
            if infra_type == cs.Infra.IS.name:
                for node in client.nodes:
                    if not clients.has_client(node):
                        raise Exception(
                            f"Index server Client Node with name [{node}] is not present in the commcell")
                    client_obj = clients.get(node)
                    self.log.info("Checking if client entry is already present in DB")
                    query = db_cs.SELECT_RING_IS_QUERY % (infra_type, self.ring_id,
                                                          client_obj.client_id, client.client_name)
                    self.log.info(f"Query used - [{query}]")
                    result = self.db_obj.execute_query(query)
                    self.log.info(f"Result of the query - [{query}]")
                    if len(result.rows) == 0:
                        self.log.info("Information is not present in DB. Inserting the data")
                        self.db_obj.execute_query(
                            db_cs.INSERT_RING_IS_QUERY % (infra_type, client.client_name,
                                                          client_obj.client_id, client_obj.client_name,
                                                          '%s', self.ring_id))
                        self.log.info(f"Client [{node}] information inserted successfully")
                    else:
                        self.log.info(f"Client [{node}] information is already present in DB")
            else:
                if not clients.has_client(client.client_name):
                    if infra_type == cs.Infra.NWP.name and self.ring.provision_type == cs.RingProvisionType.CUSTOM.value:
                        self.log.info("Skipping setting details for network proxy as this is custom infra")
                        continue
                    raise Exception(f"Client with name [{client.client_name}] is not present in the commcell")
                client_obj = clients.get(client.client_name)
                self.log.info("Checking if entry is already present in DB")
                query = db_cs.SELECT_RING_INFRA_QUERY % (infra_type, self.ring_id, client_obj.client_id)
                self.log.info(f"Query used - [{query}]")
                result = self.db_obj.execute_query(query)
                self.log.info(f"Result of the query - [{query}]")
                if len(result.rows) == 0:
                    self.log.info("Information is not present in DB. Inserting the data")
                    self.db_obj.execute_query(
                        db_cs.INSERT_RING_INFRA_QUERY % (
                            infra_type, client_obj.client_id, client_obj.client_name, '%s', self.ring_id))
                    self.log.info(f"Client [{client.client_name}] information inserted successfully")
                else:
                    self.log.info(f"Client [{client.client_name}] information is already present in DB")
