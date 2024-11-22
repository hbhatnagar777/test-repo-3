# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper to perform Azure config related operations

    AzureConfigHelper:
        __init__()                      --  Initializes the Azure configuration helper
        perform_git_push_tasks          --  Performs all git tasks such as adding, committing,
                                            pushing and creating PR in azure devops
        perform_clone_task              --  Performs git clone task
        perform_checkout_task           --  Performs git checkout task
        perform_update_task             --  Performs git update task
        update_orbit_config             --  Updates orbit config file
        update_ring_biz_config          --  Creates the ring biz config files from the template that is passed
        update_ring_core_config         --  Creates the ring core config files from the template that is passed
        update_ring_global_param_config --  Creates the ring global param config files from the template that is passed
        set_key_vault_access_policies   --  Sets the required keyvault access policies for the function apps
        update_lead_n_legal_value       --  Updates the lead and legal values in the config files
        wait_for_pr_complete            --  Wait for PR request to complete
        check_if_pr_complete            --  Check if PR is complete
        switch_directory                --  Switches directory to the given path
        delete_orbit_config_values      --  Deletes orbit config file
        delete_ring_biz_config          --  Deletes the ring biz config files from the template that is passed
        delete_ring_core_config         --  Deletes the ring core config files from the template that is passed
        delete_ring_gp_config           --  Deletes the ring core config files from the template that is passed

"""
import json
import os
import shutil
import datetime
import time

from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicHub.Helpers.azure_pipeline_helper import AzurePipelineHelper
from MetallicHub.Helpers.azure_resource_helper import AzureResourceHelper
from MetallicHub.Utils.common_utils import CommonUtils
from MetallicHub.Utils.git_utils import GitUtils
from MetallicHub.Utils import Constants as cs
from MetallicHub.Utils.keyvault_utils import KeyVaultUtils
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Helpers.email_helper import EmailHelper
from MetallicRing.Utils.ring_utils import RingUtils

_CONFIG = get_config(json_path=cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub


class AzureConfigHelper(BaseRingHelper):
    """contains helper class to perform azure config related operations"""

    def __init__(self, ring_commcell, config=_CONFIG.azure_credentials):
        """
        Initializes the Azure configuration helper
        Args:
            ring_commcell(object)       --  Instance of commcell class
            config(dict)                --  Dictionary containing azure credential information
        """
        super().__init__(ring_commcell)
        self.log.info("Initializing Azure Resource Helper")
        self.commcell = ring_commcell
        self.ring_name = self.ring.name
        self.ring_commcell_config = self.ring.commserv
        self.rid = self.ring.id
        self.rid_str = RingUtils.get_ring_string(self.ring.id)
        self.config_clone_path = cs.HUB_CONFIG_CLONE_PATH % self.ring_name
        self.pr_complete_check_path = cs.HUB_CHECK_PR_COMPLETE_PATH % self.ring_name
        self.branch_name = f"automation_config_{self.ring_name}_branch"
        self.lead_legal_branch_name = f"automation_config_{self.ring_name}_lead_legal_branch"
        self.pat = config.AZ_PAT
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET
        self.subscription_id = config.SUBSCRIPTION_ID
        self.tenant_id = config.TENANT_ID
        self.access_key = config.ACCESS_KEY
        self.keyvault_name = config.KEY_VAULT_NAME
        os.environ["AZURE_DEVOPS_EXT_PAT"] = self.pat
        self.git_util = GitUtils(cs.HUB_CONFIG_REPO % self.pat, self.branch_name, cs.HUB_CONFIG_REPO_NAME)
        self.common_utils = CommonUtils(cs.RESOURCE_GROUP_NAME, self.subscription_id)
        self.keyvault_utils = KeyVaultUtils(self.keyvault_name)
        self.local_machine = Machine()
        self.retry_attempt = 0
        self.log.info("Azure config helper initialized. All Environmental variables set")

    def perform_git_push_tasks(self, clone_path=None, branch_name=None):
        """
        Performs all git tasks such as adding, committing, pushing and creating PR in azure devops
        Args:
            clone_path(str)         --  path to clone the repo
            branch_name(str)        --  name of the azure branch
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            if clone_path is None:
                clone_path = self.config_clone_path
            if branch_name is None:
                branch_name = self.branch_name
            self.log.info(f"Request received to push data from source branch [{branch_name}] - "
                          f"clone path - [{clone_path}]")
            self.log.info("Changing cwd")
            self.switch_directory(cs.HUB_CONFIG_REPO_NAME, clone_path)
            self.log.info("cwd changed. Going to add content")
            self.git_util.git_add()
            self.log.info("Git add successful. Going to commit changes")
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            self.git_util.git_commit(cs.GIT_COMMIT_HUB_CONFIG_MESSAGE % timestamp)
            self.log.info(f"Git commit successful - [{cs.GIT_COMMIT_HUB_CONFIG_MESSAGE % timestamp}]. "
                          f"pushing branch")
            self.git_util.git_push(branch_name)
            self.log.info(f"Pushed branch. Creating pull request for repo - [[{cs.HUB_CONFIG_REPO_NAME}] ")
            self.git_util.create_pr(cs.HUB_CONFIG_REPO_NAME, branch_name)
            self.log.info(f"Pull request created successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def perform_clone_task(self, clone_path=None):
        """
        Performs git clone task
        Args:
            clone_path(str)         --  Local Path in the system to clone the git repo
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            if clone_path is not None:
                self.config_clone_path = clone_path
            self.log.info(f"Request received to clone repo. [{cs.HUB_CONFIG_REPO_NAME}]")
            if not os.path.exists(self.config_clone_path):
                self.log.info(f"clone path doesn't exist. Creating new one. [{self.config_clone_path}]")
                os.makedirs(self.config_clone_path)
                self.log.info(f"Created the required directories")
            os.chdir(self.config_clone_path)
            self.log.info(f"CWD directory set")
            if os.path.exists(cs.HUB_CONFIG_REPO_NAME):
                self.log.info(f"Repository already exists in the current directory. Moving it")
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                shutil.move(cs.HUB_CONFIG_REPO_NAME, f"{cs.HUB_CONFIG_REPO_NAME}_{timestamp}")
                self.log.info(f"Move successful")
            self.log.info("Cloning the repo")
            self.git_util.git_clone()
            self.log.info("Clone successful")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def perform_checkout_task(self):
        """
        Performs git checkout task
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info(f"Request received to perform checkout. Switching directory - "
                          f"[{cs.HUB_ORBIT_CONFIG_FILE_PATH}]")
            self.switch_directory(cs.HUB_ORBIT_CONFIG_FILE_PATH)
            self.log.info("Switch cwd successful. Proceeding to checkout")
            self.git_util.git_checkout()
            self.log.info("Git checkout successful")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure Config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def perform_update_task(self):
        """
        Performs git update task
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to update config file. Going to update biz config files")
            self.update_ring_biz_config()
            self.log.info("Updated biz. Going to update global param config file")
            self.update_ring_global_param_config()
            self.log.info("Updated GP. Going to update Core config file")
            self.update_ring_core_config()
            self.log.info("Updated core. Going to update orbit config file")
            self.update_orbit_config()
            self.log.info("Updated Orbit config file")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute azure config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def update_orbit_config(self):
        """
        Updates orbit config file
        """
        self.log.info(f"Request received to update orbit config. Switching cwd - [{cs.HUB_ORBIT_CONFIG_FILE_PATH}]")
        self.switch_directory(cs.HUB_ORBIT_CONFIG_FILE_PATH)
        filename = cs.HUB_ORBIT_CONFIG_JSON_FILE
        self.log.info(f"CWD changed. Orbit config file name - [{filename}]")
        # Read the content of the JSON file
        self.log.info("Reading file contents")
        with open(filename, 'r') as file:
            data = json.load(file)
            self.log.info("File read successfully")
        # Write the updated data back to the file
        for content in data:
            if content.get(cs.ORBIT_FILE_LABEL_CONSTANT) is None:
                for sub_content in content.get(cs.ORBIT_FILE_DATA_CONSTANT):
                    if sub_content.get(cs.ORBIT_FILE_KEY_CONSTANT) == cs.ORBIT_FILE_ALLOWED_DOMAINS:
                        allowed_domain = sub_content.get(cs.ORBIT_FILE_VALUE_CONSTANT, None)
                        if allowed_domain is None:
                            sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] = \
                                f"{cs.ORBIT_FILE_ALLOWED_DOMAINS_VALUE%self.ring_name.lower()}"
                        else:
                            sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] += \
                                f",{cs.ORBIT_FILE_ALLOWED_DOMAINS_VALUE % self.ring_name.lower()}"
            elif content.get(cs.ORBIT_FILE_LABEL_CONSTANT) == cs.ORBIT_FILE_LABEL_MULTI_COMMCELL:
                base_url_dict = {cs.ORBIT_FILE_KEY_CONSTANT: cs.ORBIT_FILE_BASE_URL_KEY % self.ring_name.upper(),
                      cs.ORBIT_FILE_VALUE_CONSTANT: cs.ORBIT_FILE_BASE_URL_VALUE % self.ring_name.lower()}
                function_app_name = cs.ORBIT_FILE_CORE_FUNCTION_APP_NAME % self.ring_name.lower()
                function_default_app_key = self.common_utils.get_function_app_app_key(function_app_name)
                core_function = {cs.ORBIT_FILE_KEY_CONSTANT:
                                     cs.ORBIT_FILE_CORE_FUNCTION_APP_KEY % self.ring_name.upper(),
                                 cs.ORBIT_FILE_VALUE_CONSTANT:
                                     cs.ORBIT_FILE_CORE_FUNCTION_APP_VALUE % (function_app_name,
                                                                              function_default_app_key)}
                if content.get(cs.ORBIT_FILE_DATA_CONSTANT, None) is None:
                    content[cs.ORBIT_FILE_DATA_CONSTANT] = [base_url_dict, core_function]
                else:
                    sub_contents = content[cs.ORBIT_FILE_DATA_CONSTANT]
                    for sub_content in sub_contents:
                        if sub_content.get(cs.ORBIT_FILE_KEY_CONSTANT) == cs.ORBIT_FILE_COMMCELL_NAME_KEY:
                            commcell_name = sub_content.get(cs.ORBIT_FILE_VALUE_CONSTANT, None)
                            if commcell_name is None:
                                sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] = \
                                    f"{self.ring_name.upper()}"
                            else:
                                sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] += \
                                    f",{self.ring_name.upper()}"
                    sub_contents.append(base_url_dict)
                    sub_contents.append(core_function)
        self.log.info(f"Content updated successfully - [{data}]. Writing to file")
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        self.log.info(f"Write to file - [{filename}] successful")

    def delete_orbit_config_values(self):
        """
        Deletes orbit config data related to the ring
        """
        self.log.info(f"Request received to delete orbit config for ring [{self.ring_name}]. "
                      f"Switching cwd - [{cs.HUB_ORBIT_CONFIG_FILE_PATH}]")
        self.switch_directory(cs.HUB_ORBIT_CONFIG_FILE_PATH)
        filename = cs.HUB_ORBIT_CONFIG_JSON_FILE
        self.log.info(f"CWD changed. Orbit config file name - [{filename}]")
        # Read the content of the JSON file
        self.log.info("Reading file contents")
        with open(filename, 'r') as file:
            data = json.load(file)
            self.log.info("File read successfully")
        # Write the updated data back to the file
        for content in data:
            if content.get(cs.ORBIT_FILE_LABEL_CONSTANT) is None:
                for sub_content in content.get(cs.ORBIT_FILE_DATA_CONSTANT):
                    if sub_content.get(cs.ORBIT_FILE_KEY_CONSTANT) == cs.ORBIT_FILE_ALLOWED_DOMAINS:
                        allowed_domain = sub_content.get(cs.ORBIT_FILE_VALUE_CONSTANT, None)
                        if allowed_domain is not None:
                            sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] = str.replace(sub_content[cs.ORBIT_FILE_VALUE_CONSTANT],
                                        f"{cs.ORBIT_FILE_ALLOWED_DOMAINS_VALUE%self.ring_name.lower()}", "")
                            sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] = str.replace(sub_content[cs.ORBIT_FILE_VALUE_CONSTANT],
                                        ",,", ",")
            elif content.get(cs.ORBIT_FILE_LABEL_CONSTANT) == cs.ORBIT_FILE_LABEL_MULTI_COMMCELL:
                base_url_dict = cs.ORBIT_FILE_BASE_URL_KEY % self.ring_name.upper()
                core_function = cs.ORBIT_FILE_CORE_FUNCTION_APP_KEY % self.ring_name.upper()
                val_to_remove = {base_url_dict, core_function}
                if content.get(cs.ORBIT_FILE_DATA_CONSTANT, None) is not None:
                    sub_contents = content[cs.ORBIT_FILE_DATA_CONSTANT]
                    for sub_content in sub_contents:
                        if sub_content.get(cs.ORBIT_FILE_KEY_CONSTANT) == cs.ORBIT_FILE_COMMCELL_NAME_KEY:
                            commcell_name = sub_content.get(cs.ORBIT_FILE_VALUE_CONSTANT, None)
                            if commcell_name is not None:
                                sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] = str.replace(sub_content[cs.ORBIT_FILE_VALUE_CONSTANT],
                                            f"{self.ring_name.upper()}", "")
                                sub_content[cs.ORBIT_FILE_VALUE_CONSTANT] = str.replace(sub_content[cs.ORBIT_FILE_VALUE_CONSTANT],
                                            ",,", ",")
                    content[cs.ORBIT_FILE_DATA_CONSTANT] = [sub_content for sub_content in sub_contents if sub_content.get(cs.ORBIT_FILE_KEY_CONSTANT) not in val_to_remove]
        self.log.info(f"Content delete successfully - [{data}]. Writing to file")
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        self.log.info(f"Write to file - [{filename}] successful")

    def update_ring_biz_config(self):
        """
        Creates the ring biz config files from the template that is passed
        """
        self.log.info(f"Request received to update ring biz config. Switching directory - {cs.HUB_RING_BIZ_FILE_PATH}")
        self.switch_directory(cs.HUB_RING_BIZ_FILE_PATH)
        self.log.info("CWD changed. Copying template file for modification")
        filename = cs.HUB_RING_BIZ_JSON_FILE % self.ring_name.lower()
        shutil.copyfile(cs.HUB_RING_BIZ_TEMPLATE_JSON_FILE, filename)
        self.log.info(f"File copy successful. [{cs.HUB_RING_BIZ_TEMPLATE_JSON_FILE}] to [{filename}]. updating file")
        with open(filename, 'r') as file:
            content = file.read()
            content = content.replace(cs.REPLACE_STR_RNAME, self.ring_name.lower())
            content = content.replace(cs.REPLACE_STR_RID, self.rid_str)
            content = content.replace(cs.REPLACE_STR_COMMCELL_HOSTNAME, self.ring.commserv.hostname)
        self.log.info("Content updated successfully. Writing to file")
        with open(filename, 'w') as file:
            # Write the modified content back to the file
            file.write(content)
        self.log.info("File updated")

    def delete_ring_biz_config(self):
        """
        Deletes the ring biz config files
        """
        self.log.info(f"Request received to delete ring biz config. Switching directory - {cs.HUB_RING_BIZ_FILE_PATH}")
        self.switch_directory(cs.HUB_RING_BIZ_FILE_PATH)
        self.log.info("CWD changed. Copying template file for modification")
        filename = cs.HUB_RING_BIZ_JSON_FILE % self.ring_name.lower()
        if os.path.isfile(filename):
            os.remove(filename)
        self.log.info("File deleted")

    def update_ring_core_config(self):
        """
        Creates the ring core config files from the template that is passed
        """
        self.log.info(f"Request received to update ring core config. Changing cwd - [{cs.HUB_RING_CORE_FILE_PATH}]")
        self.switch_directory(cs.HUB_RING_CORE_FILE_PATH)
        ma_name = cs.MEDIA_AGENT_NAME
        self.log.info(f"Getting Media Agent Object - [{ma_name}]")
        if not self.commcell.media_agents.has_media_agent(ma_name):
            raise Exception(f"Media agent with given name [{ma_name}] doesn't exist in this commcell")
        ma_obj = self.commcell.media_agents.get(ma_name)
        self.log.info("MA object obtained")
        storage_access_key = self.common_utils.\
            get_storage_account_access_key(cs.STORAGE_ACCOUNT_NAME % self.ring_name.lower())
        storage_secret_value = cs.STORAGE_ACCOUNT_SECRET_VALUE % (self.ring_name.lower(), storage_access_key)
        secret_name = cs.STORAGE_ACCOUNT_SECRET_NAME % self.ring_name.lower()
        self.log.info(f"Creating secret with storage access key - [{storage_access_key}]")
        self.keyvault_utils.create_secret(secret_name, storage_secret_value)
        self.log.info("Secret created successfully")
        secret_url = self.keyvault_utils.get_secret_url(secret_name)
        self.log.info(f"secret URL - {secret_url}")
        filename = cs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
        shutil.copyfile(cs.HUB_RING_CORE_TEMPLATE_JSON_FILE, filename)
        self.log.info(f"Updating core config files - [{filename}]")
        with open(filename, 'r') as file:
            content = file.read()
            content = content.replace(cs.REPLACE_STR_RNAME, self.ring_name.lower())
            content = content.replace(cs.REPLACE_STR_RID, self.rid_str)
            content = content.replace(cs.REPLACE_STR_MEDIA_AGENT_ID, ma_obj.media_agent_id)
            content = content.replace(cs.REPLACE_STR_MEDIA_AGENT_NAME, ma_name)
            content = content.replace(cs.REPLACE_STR_STORAGE_SECRET_URL, secret_url)
            content = content.replace(cs.REPLACE_STR_COMMCELL_HOSTNAME, self.ring.commserv.hostname)
        self.log.info("updated the content. Write to file")
        with open(filename, 'w') as file:
            # Write the modified content back to the file
            file.write(content)
        self.log.info("Content written to file")

    def delete_ring_core_config(self):
        """
        Deletes the ring core config files
        """
        self.log.info(f"Request received to delete ring core config. Switching directory - {cs.HUB_RING_CORE_FILE_PATH}")
        self.switch_directory(cs.HUB_RING_CORE_FILE_PATH)
        self.log.info("CWD changed. Copying template file for modification")
        filename = cs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
        if os.path.isfile(filename):
            os.remove(filename)
        self.log.info("File deleted")

    def update_ring_global_param_config(self):
        """
        Creates the ring global param config files from the template that is passed
        """
        self.log.info(f"Request received to update ring global param config. "
                      f"Changing cwd - [{cs.HUB_RING_GLOBAL_PARAM_FILE_PATH}]")
        self.switch_directory(cs.HUB_RING_GLOBAL_PARAM_FILE_PATH)
        filename = cs.HUB_RING_GP_JSON_FILE % self.ring_name.lower()
        shutil.copyfile(cs.HUB_RING_GP_TEMPLATE_JSON_FILE, filename)
        self.log.info(f"Filename - [{filename}]. Reading and updating content")
        with open(filename, 'r') as file:
            content = file.read()
            content = content.replace(cs.REPLACE_STR_RNAME, self.ring_name.lower())
            content = content.replace(cs.REPLACE_STR_RID, self.rid_str)
        with open(filename, 'w') as file:
            # Write the modified content back to the file
            file.write(content)
        self.log.info("Updated file contents successfully")

    def delete_ring_gp_config(self):
        """
        Deletes the ring core config files
        """
        self.log.info(f"Request received to delete ring global param config. Switching directory - "
                      f"{cs.HUB_RING_GLOBAL_PARAM_FILE_PATH}")
        self.switch_directory(cs.HUB_RING_GLOBAL_PARAM_FILE_PATH)
        self.log.info("CWD changed. Copying template file for modification")
        filename = cs.HUB_RING_GP_JSON_FILE % self.ring_name.lower()
        if os.path.isfile(filename):
            os.remove(filename)
        self.log.info("File deleted")

    def set_key_vault_access_policies(self):
        """
        Sets the required keyvault access policies for the function apps
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Updating access policies")
            core_func_app = cs.CORE_FUNCTION_APP_NAME % self.ring_name.lower()
            biz_func_app = cs.BIZ_FUNCTION_APP_NAME % self.ring_name.lower()
            core_func_app_stage = f"{core_func_app}/slots/staging"
            biz_func_app_stage = f"{biz_func_app}/slots/staging"
            self.log.info("Obtaining function app IDs")
            core_func_app_id = self.common_utils.get_func_app_object_id(core_func_app)
            core_func_app_stage_id = self.common_utils.get_func_app_object_id(core_func_app_stage)
            biz_func_app_id = self.common_utils.get_func_app_object_id(biz_func_app)
            biz_func_app_stage_id = self.common_utils.get_func_app_object_id(biz_func_app_stage)
            self.log.info("All app IDs obtained successfully. Setting access policies")
            self.keyvault_utils.set_access_policy(core_func_app_id, self.subscription_id)
            self.keyvault_utils.set_access_policy(core_func_app_stage_id, self.subscription_id)
            self.keyvault_utils.set_access_policy(biz_func_app_id, self.subscription_id)
            self.keyvault_utils.set_access_policy(biz_func_app_stage_id, self.subscription_id)
            self.log.info("Access policies set")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def update_lead_n_legal_value(self):
        """
        Updates the lead and legal values in the config files
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Request received to update lead and legal values. Obtaining lead code")
            biz_app = cs.BIZ_FUNCTION_APP_NAME % self.ring_name.lower()
            filename = cs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
            try:
                lead_code = self.common_utils.get_function_code(cs.LEAD_CREATION_FUCN_NAME,
                                                                biz_app)
            except Exception as exp:
                # TODO: Remove this code once a fix from microsoft is delivered for updating backend health
                arh = AzureResourceHelper(self.ring_name, self.rid_str, None)
                arh.readd_backend_pool_target()
                aph = AzurePipelineHelper(self.ring_name, self.rid_str)
                aph.run_pipeline_api()
                lead_code = self.common_utils.get_function_code(cs.LEAD_CREATION_FUCN_NAME,
                                                                biz_app)
            self.log.info("Lead code obtained")
            lead_legal_clone_path = os.path.join(self.config_clone_path, cs.LEAD_LEGAL_CLONE_DIR)
            if not os.path.exists(lead_legal_clone_path):
                os.makedirs(lead_legal_clone_path)
            else:
                os.chdir(self.config_clone_path)
                shutil.rmtree(cs.LEAD_LEGAL_CLONE_DIR, ignore_errors=True)
            os.chdir(lead_legal_clone_path)
            self.log.info(f"Updaing lead and legal cwd - [{lead_legal_clone_path}]. Starting clone opertion")
            self.git_util.git_clone()
            self.log.info("Clone complete. Performing git checkout")
            self.switch_directory(cs.HUB_RING_CORE_FILE_PATH, clone_path=lead_legal_clone_path)
            self.git_util.git_checkout(self.lead_legal_branch_name)
            self.log.info("Git checkout successful. updating file contents")
            with open(filename, 'r') as file:
                content = file.read()
                content = content.replace(cs.REPLACE_STR_LEAD_CREATION, lead_code)
                # content = content.replace(cs.REPLACE_STR_LEGAL_UPDATE, legal_code)
            with open(filename, 'w') as file:
                # Write the modified content back to the file
                file.write(content)
            self.log.info("File content updated successfully. Performing git push tasks")
            self.perform_git_push_tasks(lead_legal_clone_path, self.lead_legal_branch_name)
            self.log.info("Git push complete")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def wait_for_pr_complete(self, pr_type=cs.CheckPRType.NEW):
        """
        Wait for PR request to complete
        Returns:
            status(str)             --  Passed/Failed based on the result of operation
            message(str)            --  Error message if there is an exception else None
        """
        status = cs.FAILED
        message = None
        try:
            pr_status = False
            self.log.info("Waiting for PR completion")
            email = EmailHelper(self.ring_name, self.ring_commcell_config.hostname)
            while not pr_status:
                pr_status = self.check_if_pr_complete(pr_type)
                if not pr_status:
                    self.log.info("PR status not complete. Sleeping for 5 mins")
                    email.send_pr_mail()
                    time.sleep(10 * 60)
                else:
                    self.log.info("PR complete. We are ready to start the pipeline")
            self.log.info("PR complete")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Azure config helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def check_if_pr_complete(self, pr_type=cs.CheckPRType.NEW):
        """
        Checks if PR is complete
        Returns:
            Bool    --  True if PR is complete
                        False if PR is not complete
        """
        pr_status = False
        self.log.info(f"Request received to check if PR task is complete. PR_TYPE - [{pr_type}]")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        clone_path = os.path.join(self.pr_complete_check_path, timestamp)
        if not os.path.exists(clone_path):
            os.makedirs(clone_path)
        os.chdir(clone_path)
        self.git_util.git_clone()
        self.switch_directory(cs.HUB_RING_CORE_FILE_PATH, clone_path)
        if pr_type == cs.CheckPRType.NEW:
            self.log.info("This is new PR request")
            filename = cs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
            if os.path.exists(filename):
                pr_status = True
        elif pr_type == cs.CheckPRType.UPDATE:
            self.log.info("This PR request post the update of lead value")
            filename = cs.HUB_RING_CORE_JSON_FILE % self.ring_name.lower()
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    content = file.read()
                    if cs.REPLACE_STR_LEAD_CREATION in content and cs.REPLACE_STR_LEGAL_UPDATE in content:
                        pr_status = False
                    else:
                        pr_status = True
            else:
                pr_status = False
        os.chdir(self.pr_complete_check_path)
        shutil.rmtree(timestamp, ignore_errors=True)
        self.log.info(f"PR task status {pr_status}")
        return pr_status

    def switch_directory(self, path, clone_path=None):
        """
        Switches directory to the given path
        Args:
            path(str)           --  path to be switched to
            clone_path(str)     --  clone path to be switched to
        """
        if clone_path is None:
            clone_path = self.config_clone_path
        self.log.info(f"Switching to directory - [{path}]. Root - [{clone_path}]")
        os.chdir(clone_path)
        os.chdir(path)


