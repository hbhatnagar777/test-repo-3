# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# Support for cleanup of Ring SaaS Infra
# 1. Delete Terraform resources - Complete
# 2. Delete App Gateway settings - Complete
#         delete_backend_pool
#         delete_health_probe
#         delete_backend_settings
#         delete_listeners
#         delete_rules
#         delete_dns_records
#         Cleanup subnets
# 3. Delete config files - Complete
# 4. Delete orbit config values - Complete
# 4. Delete terraform files - Complete
# 5. Delete Variables - Complete
# 6. Delete CORS value for orbit function - Complete
# 7. Cleanup sqlite db values - Complete
# 8. Delete the stages in Release definition - Complete
# 9. Remove the Lighthouse entry for this ring - Complete
# 10. Delete Service Commcell Registrations - Complete

"""helper class for performing Azure/SaaS resource cleanup related operations

    AzureResourceCleanupHelper:

        start_task                      --  Starts the cleanup task
        destroy_azure_resources         --  Destroys and deletes the azure terraform created resources and appgateway resources
        delete_config_files             --  Deletes/Updates the config file of both terraform and ring
        delete_azure_pipeline_configs   --  Deletes the azure pipeline configs and updates the release definition
        unregister_service_commcell     --  Unregisters the service commcell
        cleanup_db_entries              --  Cleans up the sqlite db entries created for tracking ring configuration
        delete_lh_config                --  Deletes the Light house configuration
        _get_commcell_name              --  Gets the cs client name for the ring

"""

import os
import shutil

from AutomationUtils import logger
from AutomationUtils.config import get_config
from cvpysdk.commcell import Commcell
from MetallicHub.Helpers.azure_resource_helper import AzureResourceHelper
from MetallicHub.Helpers.azure_config_helper import AzureConfigHelper
from MetallicHub.Helpers.azure_pipeline_helper import AzurePipelineHelper
from MetallicHub.Helpers.light_house_helper import LightHouseHelper
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper
from MetallicRing.DBQueries import Constants as db_cs
from MetallicRing.Helpers.metrics_helper import MetricsRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils
from MetallicHub.Utils import Constants as h_cs

_CONFIG = get_config(json_path=h_cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub.azure_credentials


class AzureResourceCleanupHelper:
    def __init__(self, ring_id):
        self.log = logger.get_log()
        self.ring_id_int = int(ring_id)
        self.ring_id = RingUtils.get_ring_string(ring_id)
        self.ring_name = RingUtils.get_ring_name(ring_id)
        self.sqlite_helper = SQLiteDBQueryHelper()
        self.resource_helper = None
        self.config_helper = None
        self.azure_pipeline_helper = None
        self.lh_helper = None
        self.config = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH)
        self.metrics_config = self.config.Metallic.metrics_commcell
        self.cs_client_name = self.ring_name

    def start_task(self):
        """
        Starts the cleanup task
        """
        self.destroy_azure_resources()
        self.delete_lh_config()
        self.delete_config_files()
        self.delete_azure_pipeline_configs()
        self.unregister_service_commcell()
        self.cleanup_db_entries()

    def delete_lh_config(self):
        """
        Deletes the Light house configuration
        """
        self.lh_helper = LightHouseHelper(self.ring_name)
        self.lh_helper.delete_lh_config()

    def destroy_azure_resources(self):
        """
        Destroys and deletes the azure terraform created resources and appgateway resources
        """
        self.resource_helper = AzureResourceHelper(self.ring_name, self.ring_id, None)
        self.resource_helper.perform_clone_task()
        self.resource_helper.perform_checkout_task()
        self.resource_helper.set_terraform_dir()
        self.resource_helper.terraform_init(os.getcwd())
        self.resource_helper.terraform_destroy(os.getcwd())
        self.resource_helper.delete_dns_records()
        self.resource_helper.delete_rules()
        self.resource_helper.delete_listeners()
        self.resource_helper.delete_backend_settings()
        self.resource_helper.delete_health_probe()
        self.resource_helper.delete_backend_pool()

    def delete_config_files(self):
        """
        Deletes/Updates the config file of both terraform and ring
        """
        # Delete terraform related directories
        self.resource_helper = AzureResourceHelper(self.ring_name, self.ring_id, None)
        self.resource_helper.perform_clone_task()
        self.resource_helper.perform_checkout_task()
        self.resource_helper.set_root_dir()
        dir_name = self.ring_name.lower()
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        self.resource_helper.perform_git_push_tasks()

        # # Delete Config Related Directories'
        self.config_helper = AzureConfigHelper(None)
        self.config_helper.ring_name = self.ring_name
        self.config_helper.rid_str = self.ring_id
        self.config_helper.perform_clone_task()
        self.config_helper.perform_checkout_task()
        self.config_helper.delete_ring_gp_config()
        self.config_helper.delete_ring_biz_config()
        self.config_helper.delete_ring_core_config()
        self.config_helper.delete_orbit_config_values()
        self.config_helper.perform_git_push_tasks()

    def delete_azure_pipeline_configs(self):
        """
        Deletes the azure pipeline configs and updates the release definition
        """
        self.azure_pipeline_helper = AzurePipelineHelper(self.ring_name, self.ring_id)
        self.azure_pipeline_helper.delete_pipeline_variables([h_cs.VARIABLE_CC_NAME_NAME,
                                                              h_cs.VARIABLE_CC_ENDPOINT_NAME,
                                                              h_cs.VARIABLE_CC_RESOURCE_GROUP_NAME])
        self.azure_pipeline_helper.delete_pipeline_variables([h_cs.VARIABLE_DEV_CC_NAME_NAME,
                                                              h_cs.VARIABLE_DEV_CC_ENDPOINT_NAME,
                                                              h_cs.VARIABLE_DEV_CC_RESOURCE_GROUP_NAME])
        self.azure_pipeline_helper.remove_orbit_app_CORS_allowed_domain()
        self.azure_pipeline_helper.delete_definition_from_file(pipeline=_CONFIG.PIPELINE)
        self.azure_pipeline_helper.delete_definition_from_file(pipeline=_CONFIG.PIPELINE_PHASE_TWO)
        self.azure_pipeline_helper.update_pipeline_definition()

    def unregister_service_commcell(self):
        """
        Unregisters the service commcell
        """
        metrics_commcell = Commcell(self.metrics_config.hostname, self.metrics_config.username,
                 self.metrics_config.password)
        metrics_commcell_helper = MetricsRingHelper(metrics_commcell)
        metrics_commcell_helper.unregister_remote_commcell(self.cs_client_name)

    def cleanup_db_entries(self):
        """
        Cleans up the sqlite db entries created for tracking ring configuration
        """
        self.log.info("Cleanup started for clearing DB entries")
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_CONFIG_MAP % self.ring_name)
        self.sqlite_helper.execute_query(db_cs.CLEANUP_SUBNET_INFO % self.ring_name)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_CS % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_MA % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_WC % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_WS % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_IS % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_NWP % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_EMAIL % self.ring_name)
        self.sqlite_helper.execute_query(db_cs.CLEANUP_AVAILABLE_RING_STATUS % self.ring_id_int)
        self.sqlite_helper.execute_query(db_cs.DELETE_METALLIC_RING_INFO % self.ring_id_int)
        self.log.info("Sqlite DB entries are cleaned up")

    def _get_commcell_name(self):
        """
        Gets the cs client name for the ring
        """
        self.log.info("Executing query to get cs client name from sqlite DB")
        result = self.sqlite_helper.execute_query(db_cs.GET_COMMCELL_CLIENT % self.ring_id_int)
        if len(result.rows) == 0:
            cs_name = self.ring_name
        else:
            cs_name = result.rows[0][0]
        self.log.info(f"CS Name obtainer - [{cs_name}]")
        return cs_name
