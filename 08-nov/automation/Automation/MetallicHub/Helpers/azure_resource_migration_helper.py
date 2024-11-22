# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# Support for Migration of Azure Resources from dedicated RG to Common RG for SaaS Rings
# 1. Destroy all azure resources in the ring's resource group using terraform destroy command
# 1.1 Delete resource group if not deleted
# 1.2 Delete DNS records
# 2. Recreate them by updating the following terraform files,
# 	main.tf (Terraform file) to reuse existing,
# 		1. Resource Group
# 		2. App Service Plan
# 	terraform.tfvars.json (Variable file) with the name of RG and ASP to be reused,
# 	backend.tf,
#  	    1. update the terraform required_version = "= 1.8.2" if not updated already
#       2. update the azure rm version to "3.105.0"
# 3. Connect function apps to VNET if not connected
# 3.1 Recreate DNS records
# 4. Set Key vault Access policy
# 5. Update the following config files value,
# 	a. RingConfig-> Core -> CacheStorageAccount
# 	c. OrbitConfig-> AppConfig -> commcell:{ring_name}:corefunction
# 5.1 Update the variable group with new resource group name
# 5.2 Manually update the stage task to use the reordered task group for old rings
# 6. Run the pipeline
# 7. Update the following config files value,
# 	b. RingConfig-> Core -> api:endpoint:leadcreation
# 8. ReRun the pipeline
# 9. Test tenant creation is working


"""
Helper class for performing Azure/SaaS resource migration related operations

    AzureResourceMigrationHelper:

        start_task                      --  Starts the Migration task
        destroy_azure_resources         --  Destroys and deletes the azure terraform created resources and appgateway resources
        delete_resource_group           --  Destroys azure resource group
        recreate_terraform_resources    --  Recreates the terraform resources
        set_key_vault_access            --  Sets key vault access policies
        update_config_files             --  Updates the config files
        update_config_lead_files        --  Updates the lead value in core config file
        init_config_helper              --  Initializes config helper
        update_pipeline_variables       --  Updates the pipeline variables
        run_pipeline                    --  Starts the azure pipeline
        update_orbit_config             --  Updates orbit config file
        update_ring_core_storage_acc_config --  Updates the ring core config files from the template that is passed
        update_ring_core_lead_config    --  Updates the ring core config files from the template that is passed
        remove_lock_file                --  Removes the terraform lock file
        update_backend_file_content     --  Updates the contents of backend terraform file
        update_terraform_vars_file_content  --  Updates the contents of terraform_vars json file
        update_main_tf_file_content     --  Updates the contents of main terraform file
        create_company             --  Creates a new company post migration

"""
import json
import os
import random
import shutil

from AutomationUtils import logger
from AutomationUtils.config import get_config
from cvpysdk.commcell import Commcell
from MetallicHub.Helpers.azure_config_helper import AzureConfigHelper
from MetallicHub.Helpers.azure_resource_helper import AzureResourceHelper
from MetallicHub.Helpers.azure_pipeline_helper import AzurePipelineHelper
from MetallicHub.Utils import Constants as hcs
from MetallicHub.Utils.git_utils import GitUtils
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper
from MetallicRing.Helpers.workflow_helper import WorkflowRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils


class AzureResourceMigrationHelper:
    def __init__(self, ring_id):
        self.log = logger.get_log()
        self.ring_id_int = int(ring_id)
        self.ring_id = RingUtils.get_ring_string(ring_id)
        self.ring_name = RingUtils.get_ring_name(ring_id)
        self.sqlite_helper = SQLiteDBQueryHelper()
        self.resource_helper = None
        self.azure_pipeline_helper = None
        self.lh_helper = None
        self.config = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH)
        self.metrics_config = self.config.Metallic.metrics_commcell
        self.cs_client_name = self.ring_name
        self.backend_file = "backend.tf"
        self.terraform_var_file = "terraform.tfvars.json"
        self.main_file = "main.tf"
        self.config_helper = None

    def start_task(self):
        """
        Starts the cleanup task
        """
        self.destroy_azure_resources()
        self.delete_resource_group()
        self.recreate_terraform_resources()
        self.set_key_vault_access()
        self.update_config_files()
        self.update_pipeline_variables()
        self.run_pipeline()
        self.update_config_lead_files()
        self.run_pipeline()
        self.create_company()

    def destroy_azure_resources(self):
        """
        Destroys and deletes the azure terraform created resources and appgateway resources
        """
        self.resource_helper = AzureResourceHelper(self.ring_name, self.ring_id, None)
        self.resource_helper.perform_clone_task()
        self.resource_helper.perform_checkout_task()
        self.resource_helper.set_terraform_dir()
        self.update_backend_file_content()
        self.remove_lock_file()
        self.resource_helper.terraform_init(os.getcwd())
        self.resource_helper.terraform_plan(os.getcwd())
        self.resource_helper.terraform_destroy(os.getcwd())
        self.resource_helper.delete_dns_records()

    def delete_resource_group(self):
        """
        Destroys azure resource group
        """
        rg_name = "rg01-%s-c1us02" % self.ring_id
        self.resource_helper = AzureResourceHelper(self.ring_name, self.ring_id, None)
        self.resource_helper.delete_resource_group(rg_name)

    def recreate_terraform_resources(self):
        """
        Recreates the terraform resources
        """
        self.resource_helper = AzureResourceHelper(self.ring_name, self.ring_id, None)
        self.resource_helper.perform_clone_task()
        self.resource_helper.git_util.git_init()
        self.resource_helper.perform_checkout_task()
        self.resource_helper.set_terraform_dir()
        self.update_backend_file_content()
        self.update_terraform_vars_file_content()
        self.update_main_tf_file_content()
        self.remove_lock_file()
        self.resource_helper.terraform_init(os.getcwd())
        self.resource_helper.terraform_validate(os.getcwd())
        self.resource_helper.terraform_plan(os.getcwd())
        self.resource_helper.terraform_apply(os.getcwd())
        self.resource_helper.create_dns_records()
        self.log.info("Terraform resources are recreated in new RG. "
                      "Vnet integration on functions is complete as part of terraform_apply")
        self.resource_helper.perform_git_push_tasks(add_all=False)
        self.log.info("Terraform config pushed to git repo")

    def set_key_vault_access(self):
        """
        Sets key vault access policies
        """
        self.init_config_helper()
        self.config_helper.set_key_vault_access_policies()

    def update_config_files(self):
        """
        Updates the config files
        """
        self.init_config_helper()
        self.config_helper.perform_clone_task()
        self.config_helper.perform_checkout_task()
        self.update_orbit_config()
        self.update_ring_core_storage_acc_config()
        self.config_helper.perform_git_push_tasks()

    def update_config_lead_files(self):
        """
        Updates the lead value in core config file
        """
        self.init_config_helper()
        self.update_ring_core_lead_config()
        self.config_helper.perform_git_push_tasks()

    def init_config_helper(self):
        """
        Initializes config helper
        """
        self.config_helper = AzureConfigHelper(None)
        self.config_helper.ring_name = self.ring_name
        self.config_helper.rid_str = self.ring_id
        self.config_helper.config_clone_path = hcs.HUB_CONFIG_CLONE_PATH % self.ring_name
        self.config_helper.pr_complete_check_path = hcs.HUB_CHECK_PR_COMPLETE_PATH % self.ring_name
        self.config_helper.branch_name = f"automation_config_{self.ring_name}_branch"
        self.config_helper.lead_legal_branch_name = f"automation_config_{self.ring_name}_lead_legal_branch"
        self.config_helper.git_util = GitUtils(hcs.HUB_CONFIG_REPO % self.config_helper.pat,
                                               self.config_helper.branch_name, hcs.HUB_CONFIG_REPO_NAME)

    def update_pipeline_variables(self):
        """
        Updates the pipeline variables
        """
        self.azure_pipeline_helper = AzurePipelineHelper(self.ring_name, self.ring_id)
        self.azure_pipeline_helper.update_pipeline_variables()

    def run_pipeline(self):
        """
        Starts the azure pipeline
        """
        self.azure_pipeline_helper = AzurePipelineHelper(self.ring_name, self.ring_id)
        self.azure_pipeline_helper.write_pipeline_definition_to_file()
        self.azure_pipeline_helper.run_pipeline_api()
        self.log.info("Pipeline run completed successfully")

    def update_orbit_config(self):
        """
        Updates orbit config file
        """
        self.log.info(f"Request received to update orbit config. Switching cwd - [{hcs.HUB_ORBIT_CONFIG_FILE_PATH}]")
        self.config_helper.switch_directory(hcs.HUB_ORBIT_CONFIG_FILE_PATH)
        filename = hcs.HUB_ORBIT_CONFIG_JSON_FILE
        self.log.info(f"CWD changed. Orbit config file name - [{filename}]")
        # Read the content of the JSON file
        self.log.info("Reading file contents")
        with open(filename, 'r') as file:
            data = json.load(file)
            self.log.info("File read successfully")
        # Write the updated data back to the file
        for content in data:
            if content.get(hcs.ORBIT_FILE_LABEL_CONSTANT) == hcs.ORBIT_FILE_LABEL_MULTI_COMMCELL:
                function_app_name = hcs.ORBIT_FILE_CORE_FUNCTION_APP_NAME % self.ring_name.lower()
                function_default_app_key = self.config_helper.common_utils.get_function_app_app_key(function_app_name)
                sub_contents = content[hcs.ORBIT_FILE_DATA_CONSTANT]
                for sub_content in sub_contents:
                    if sub_content.get(hcs.ORBIT_FILE_KEY_CONSTANT) == \
                            hcs.ORBIT_FILE_CORE_FUNCTION_APP_KEY % self.ring_name.upper():
                        sub_content[hcs.ORBIT_FILE_VALUE_CONSTANT] = hcs.ORBIT_FILE_CORE_FUNCTION_APP_VALUE % \
                                                                     (function_app_name, function_default_app_key)
        self.log.info(f"Content updated successfully - [{data}]. Writing to file")
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        self.log.info(f"Write to file - [{filename}] successful")

    def update_ring_core_storage_acc_config(self):
        """
        Updates the ring core config files from the template that is passed
        """
        self.log.info(f"Request received to update ring core config. Changing cwd - [{hcs.HUB_RING_CORE_FILE_PATH}]")
        self.config_helper.switch_directory(hcs.HUB_RING_CORE_FILE_PATH)
        storage_access_key = self.config_helper.common_utils.\
            get_storage_account_access_key(hcs.STORAGE_ACCOUNT_NAME % self.ring_name.lower())
        storage_secret_value = hcs.STORAGE_ACCOUNT_SECRET_VALUE % (self.ring_name.lower(), storage_access_key)
        secret_name = hcs.STORAGE_ACCOUNT_SECRET_NAME % self.ring_name.lower()
        self.log.info(f"Creating secret with storage access key - [{storage_access_key}]")
        self.config_helper.keyvault_utils.create_secret(secret_name, storage_secret_value)
        self.log.info("Secret created successfully")
        secret_url = self.config_helper.keyvault_utils.get_secret_url(secret_name)
        self.log.info(f"secret URL - {secret_url}")
        filename = hcs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
        self.log.info(f"Updating core config files - [{filename}]")
        with open(filename, 'r') as file:
            data = json.load(file)
            self.log.info("File read successfully")
        # Write the updated data back to the file
        for content in data:
            if content.get(hcs.RING_CORE_FILE_NAME_CONSTANT) == hcs.RING_CORE_FILE_CACHE_SA_NAME:
                content[hcs.RING_CORE_FILE_VALUE_CONSTANT] = \
                    f"@Microsoft.KeyVault(SecretUri={secret_url})"
        self.log.info(f"Content updated successfully - [{data}]. Writing to file")
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        self.log.info("Content written to file")

    def update_ring_core_lead_config(self):
        """
        Updates the ring core config files from the template that is passed
        """
        self.log.info(f"Request received to update ring core config. Changing cwd - [{hcs.HUB_RING_CORE_FILE_PATH}]")
        self.config_helper.switch_directory(hcs.HUB_RING_CORE_FILE_PATH)
        biz_app = hcs.BIZ_FUNCTION_APP_NAME % self.ring_name.lower()
        lead_code = self.config_helper.common_utils.get_function_code(hcs.LEAD_CREATION_FUCN_NAME, biz_app)
        self.log.info(f"Lead code obtained - {lead_code}")
        filename = hcs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
        self.log.info(f"Updating core config files - [{filename}]")
        with open(filename, 'r') as file:
            data = json.load(file)
            self.log.info("File read successfully")
        # Write the updated data back to the file
        for content in data:
            lead_key = "api:endpoint:leadcreation"
            if content.get(hcs.RING_CORE_FILE_NAME_CONSTANT) == lead_key:
                content[hcs.RING_CORE_FILE_VALUE_CONSTANT] = \
                    f"https://{biz_app}.azurewebsites.net/api/lead?code={lead_code}"
        self.log.info(f"Content updated successfully - [{data}]. Writing to file")
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        self.log.info("Content written to file")

    def remove_lock_file(self):
        """
        Removes the terraform lock file
        """
        lock_file_name = ".terraform.lock.hcl"
        self.log.info("Removing terraform lock file")
        os.remove(lock_file_name)
        self.log.info("Lock file removed")

    def update_backend_file_content(self):
        """
        Updates the contents of backend terraform file
        """
        self.log.info(f"Request received to backend terraform file content")
        with open(self.backend_file, 'r') as file:
            content = file.read()
            tf_old_ver = "= 0.14.7"
            tf_new_ver = "= 1.8.2"
            az_rm_old_version = ">= 3.0.0"
            az_rm_old_version_2 = "2.91.0"
            az_rm_new_version = "= 3.105.0"
            content = content.replace(tf_old_ver, tf_new_ver)
            content = content.replace(az_rm_old_version, az_rm_new_version)
            content = content.replace(az_rm_old_version_2, az_rm_new_version)
        with open(self.backend_file, 'w') as file:
            # Write the modified content back to the file
            file.write(content)
        self.log.info(f"updated file content - [{content}]")

    def update_terraform_vars_file_content(self):
        """
        Updates the contents of terraform_vars json file
        """
        self.log.info(f"Request received to terraform_vars json content")
        with open(self.terraform_var_file, 'r') as file:
            content = file.read()
            rg_old_name = f"rg01-{self.ring_id}-c1us02"
            rg_new_name = "Dev-Ring-M050-Function-Group"
            asp_old_name = f"asp01-{self.ring_id}-c1us02\""
            asp_new_name = "Dev-Ring-M050-ASP-EP1-02\""
            content = content.replace(rg_old_name, rg_new_name)
            content = content.replace(asp_old_name, asp_new_name)
        with open(self.terraform_var_file, 'w') as file:
            # Write the modified content back to the file
            file.write(content)
        self.log.info(f"updated file content - [{content}]")

    def update_main_tf_file_content(self):
        """
        Updates the contents of main terraform file
        """
        self.log.info(f"Request received to  main terraform file content")
        source_file = '../../automation_template/main_c1us02/main.tf'
        destination_file = 'main.tf'
        # Replace the file in the destination
        shutil.copy2(source_file, destination_file)
        self.log.info(f"Copied file from source to destination")

    def create_company(self):
        """
        Creates a new company post migration
        """
        company = f"RGMig-{cs.CMP_NAME}{self.ring_name.upper()}"
        first_name = cs.CMP_USER_NAME
        commcell_name = self.ring_name.upper()

        metrics_commcell = Commcell(self.metrics_config.hostname, self.metrics_config.username,
                                    self.metrics_config.password)
        wf_helper = WorkflowRingHelper(metrics_commcell)
        workflow_inputs = {"firstname": first_name, "lastname": "Admin01",
                           "company_name": company,
                           "phone": f"{random.randint(1000000000, 9999999999)}",
                           "commcell": f"{commcell_name}"}
        workflow_inputs["email"] = f"{workflow_inputs['firstname']}@{company}.com"
        workflow_name = "Metallic Trials On-boarding v2"
        self.log.info(f"Starting workflow [{workflow_name}] with inputs - [{workflow_inputs}]")
        wf_helper.execute_trials_v2_workflow(workflow_name, workflow_inputs)
        self.log.info("Workflow execution complete")
