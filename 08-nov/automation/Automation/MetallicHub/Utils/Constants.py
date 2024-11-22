# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import enum
import os

from AutomationUtils.config import get_config
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
external_domain_suffix = _CONFIG.domain.name
wc_hostname = _CONFIG.web_consoles[0].hostname
ma_clientname = _CONFIG.media_agents[0].client_name

METALLIC_HUB_CONFIG_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicHub", "Configuration", "azure_portal_config.json"
)

_HUB_CONFIG = get_config(json_path=METALLIC_HUB_CONFIG_FILE_PATH).Hub

METALLIC_HUB_STAGE_BLOB_FILE_PATH = os.path.join(
    AUTOMATION_DIRECTORY, "MetallicHub", "Configuration", "PipelineConfig", "pipeline_stage_blob.json"
)

# Hub devops clone directories

C_DIR = "C:\\Automation_Clone_Path"

HUB_TERRAFORM_CLONE_PATH = os.path.join(C_DIR, "AutoTF", "%s")

HUB_CONFIG_CLONE_PATH = os.path.join(C_DIR, "AutoConfig", "%s")

HUB_RELEASE_PIPELINE_PATH = os.path.join(C_DIR, "AutoReleasePipe", "%s")

HUB_CHECK_PR_COMPLETE_PATH = os.path.join(C_DIR, "AutoConfigPRPath", "%s")

HUB_TF_CHECK_PR_COMPLETE_PATH = os.path.join(C_DIR, "AutoTFPRPath", "%s")

HUB_TERRAFORM_REPO_NAME = "non-prod-terraform-live"

HUB_CONFIG_REPO_NAME = "OnPremDevConfigs"

# Hub terraform config directory

HUB_TERRAFORM_CONFIG_FILE_PATH = os.path.join("non-prod-terraform-live", "environment",
                                              "dev", "cloud_provider", "azure", "core-dev")

# Hub Orbit config directory

HUB_ORBIT_CONFIG_FILE_PATH = os.path.join("OnPremDevConfigs", "OrbitConfigs", "AppConfig")

# Hub ring config directory

HUB_RING_BIZ_FILE_PATH = os.path.join("OnPremDevConfigs", "RingConfigs", "Biz")

HUB_RING_CORE_FILE_PATH = os.path.join("OnPremDevConfigs", "RingConfigs", "Core")

HUB_RING_GLOBAL_PARAM_FILE_PATH = os.path.join("OnPremDevConfigs", "RingConfigs", "GlobalParam")

# Hub repo directories

HUB_NON_PROD_REPO = "https://%s@dev.azure.com/turinnbi/ProjectTurin/_git/non-prod-terraform-live"

HUB_CONFIG_REPO = "https://%s@dev.azure.com/turinnbi/ProjectTurin/_git/OnPremDevConfigs"

HUB_TERRAFORM_TEMPLATE_DIR = "automation_template"

HUB_TERRAFORM_CORE_DIR = "main_c1us02"

HUB_TERRAFORM_BACKEND_FILE = "backend.tf"

HUB_TERRAFORM_TFVARS_FILE = "terraform.tfvars.json"

HUB_ORBIT_CONFIG_JSON_FILE = "m050c1us02.json"

HUB_PIPELINE_RELEASE_JSON_FILE = "%sc1us02.json"

HUB_RING_CORE_JSON_FILE = "%sc1us02.json"
HUB_RING_BIZ_JSON_FILE = "%sc1us02.json"
HUB_RING_GP_JSON_FILE = "%sc1us02.json"

HUB_RING_CORE_TEMPLATE_JSON_FILE = "cv_hub_automation_template.json"
HUB_RING_BIZ_TEMPLATE_JSON_FILE = "cv_hub_automation_template.json"
HUB_RING_GP_TEMPLATE_JSON_FILE = "cv_hub_automation_template.json"

REPLACE_STR_RNAME = "{ring_name}"

REPLACE_STR_RID = "{ring_id}"

REPLACE_STR_SUBNET = "{subnet_info}"

REPLACE_STR_STORAGE_SECRET_URL = "{storage_secret_url}"

REPLACE_STR_MEDIA_AGENT_ID = "{media_agent_id}"
REPLACE_STR_MEDIA_AGENT_NAME = "{media_agent_name}"

REPLACE_STR_COMMCELL_HOSTNAME = "{commcell_hostname}"

REPLACE_STR_LEAD_CREATION = "{lead_creation_code}"
LEAD_CREATION_FUCN_NAME = "lead"

REPLACE_STR_LEGAL_UPDATE = "{legal_update_code}"
LEGAL_UPDATE_FUNC_NAME = "legal"

LEAD_LEGAL_CLONE_DIR = "lead_legal"

MAX_RETRY_LIMIT = 6

RESOURCE_GROUP_NAME = _HUB_CONFIG.azure_credentials.RING_RESOURCE_GROUP

MEDIA_AGENT_NAME = ma_clientname

STORAGE_ACCOUNT_NAME = "hub%sc1us02cache"

STORAGE_ACCOUNT_SECRET_NAME = "hub%sc1us02cache-conn-string"

STORAGE_ACCOUNT_SECRET_VALUE = "DefaultEndpointsProtocol=https;AccountName=hub%sc1us02cache;AccountKey=%s;" \
                               "EndpointSuffix=core.windows.net"

SECRET_NOT_FOUND_EXCEPTION = "(SecretNotFound)"

ORBIT_FILE_LABEL_CONSTANT = "label"
ORBIT_FILE_KEY_CONSTANT = "key"
ORBIT_FILE_VALUE_CONSTANT = "value"
ORBIT_FILE_DATA_CONSTANT = "data"

RING_CORE_FILE_NAME_CONSTANT = "name"
RING_CORE_FILE_VALUE_CONSTANT = "value"
RING_CORE_FILE_CACHE_SA_NAME = "CacheStorageAccount"

ORBIT_FILE_ALLOWED_DOMAINS = "portal:alloweddomains"
ORBIT_FILE_ALLOWED_DOMAINS_VALUE = f"https://%s.{external_domain_suffix}"

ORBIT_FILE_BASE_URL_KEY = "commcell:%s:base:url"
ORBIT_FILE_BASE_URL_VALUE = f"https://%s.{external_domain_suffix}"

ORBIT_FILE_CORE_FUNCTION_APP_NAME = "hub%sc1us02core"
ORBIT_FILE_CORE_FUNCTION_APP_KEY = "commcell:%s:corefunction"
ORBIT_FILE_CORE_FUNCTION_APP_VALUE = "%s,%s"

ORBIT_FILE_COMMCELL_NAME_KEY = "commcell:name"

ORBIT_FILE_LABEL_MULTI_COMMCELL = "MultiCommcell"

PIPELINE_FILE_ENVIRONMENTS = "environments"
PIPELINE_FILE_RANK = "rank"
PIPELINE_STAGE_NAME = "name"

GIT_COMMIT_HUB_CONFIG_MESSAGE = "CV Hub Automation - Orbit Ring Config Changes %s"
GIT_COMMIT_HUB_TERRAFORM_MESSAGE = "CV Hub Automation - Terraform Config Changes %s"
GIT_NOTHING_TO_COMMIT_MSG = "nothing to commit"
GIT_ACTIVE_PULL_REQUEST_EXISTS = "An active pull request for the source and target branch already exists"
GIT_DEVOPS_WARNING_MSG = "WARNING: The command requires the extension azure-devops"

VARIABLE_CC_ENDPOINT_NAME = "%s_CC_ENDPOINT"
VARIABLE_CC_RESOURCE_GROUP_NAME = "%s_RESOURCE_GROUP_NAME"
VARIABLE_CC_NAME_NAME = "%s_CC_NAME"

VARIABLE_DEV_CC_ENDPOINT_NAME = "%s_DEV_CC_ENDPOINT"
VARIABLE_DEV_CC_RESOURCE_GROUP_NAME = "%s_DEV_RESOURCE_GROUP_NAME"
VARIABLE_DEV_CC_NAME_NAME = "%s_DEV_CC_NAME"

VARIABLE_CC_ENDPOINT_VALUE = f"%s.{external_domain_suffix}"
VARIABLE_CC_RESOURCE_GROUP_VALUE = _HUB_CONFIG.azure_credentials.RING_RESOURCE_GROUP
VARIABLE_CC_NAME_VALUE = "%sc1us02"

CORS_ALLOWED_DOMAIN_ORBIT_APP_VALUE = f"https://%s.{external_domain_suffix}"
CORS_ALLOWED_ORIGINS_KEY = "allowedOrigins"

# App Gateway backend pool
AG_BP_CORE = "pagw02-%s-c1us02-hub-core-beap"
AG_BP_BIZ = "pagw02-%s-c1us02-hub-biz-beap"
AG_BP_WEB = "pagw02-%s-c1us02-hub-web-beap"
AG_BP_WEC = "pagw02-%s-c1us02-wec-beap"

# App Gateway App service name
AG_AS_CORE = "hub%sc1us02core"
AG_AS_BIZ = "hub%sc1us02biz"

AG_WC_APP = wc_hostname

# Appgateway Backend Settings
AG_BS_WEB = "pagw02-%s-c1us02-hub-web-be-htst-https"
AG_BS_BIZ = "pagw02-%s-c1us02-hub-biz-be-htst-https"
AG_BS_CORE = "pagw02-%s-c1us02-hub-core-be-htst-https"
AG_BS_WEC = "pagw02-%s-c1us02-wec-be-htst-https"

# Application Gateway Health Probe settings
AG_HP_WC_ENDPOINT = "/commandcenter/api"
AG_HP_SSL_CERT_NAME = "testlab-certificate"

AG_ORBIT_WC_PROBE = "pagw02-050-c1us02-wec-probe"
AG_ORBIT_WEB_PROBE = "pagw02-050-c1us02-hub-web-probe"
AG_ORBIT_API_PROBE = "pagw02-050-c1us02-hub-api-probe"
AG_RING_WC_PROBE = "pagw02-%s-c1us02-wec-probe"

PB_WEB_RULE_NAME = "pagw02-%s-c1us02-hub-web-path-rule"
PB_BIZ_RULE_NAME = "pagw02-%s-c1us02-hub-biz-path-rule"
PB_CORE_RULE_NAME = "pagw02-%s-c1us02-hub-core-path-rule"
PB_WEC_RULE_NAME = "pagw02-%s-c1us02-wec-path-rule"

PB_WEB_PATH = ["/maintenance.html,/asset/brand/*"]
PB_BIZ_PATH = ["/api/biz*"]
PB_CORE_PATH = ["/api/core*"]
PB_WEC_PATH = ["/adminconsole*", "/webconsole*", "/compliancesearch*", "/commandcenter*", "/console*"]

AG_RING_WC_HOST_VALUE = f"%s.{external_domain_suffix}"

AG_LISTENER_NAME = "pagw02-%s-c1us02-listener-https"
AG_LISTENER_FRONTEND_443_PORT_NAME = "pagw02-050-c1us02-feport-443"
AG_LISTENER_FRONTEND_PRIVATE_IP_NAME = "pagw02-050-c1us02-feip-config"

AG_RULE_PRIORITY_VALUE = 80
AG_RULE_NAME = "pagw02-%s-c1us02-rqrt-https"

VN_SUBNET_NAME = "asp01-080-c1us02-delegation"

STORAGE_CONTAINER_NAME = "hub%sc1us02web"

BLOWFISH_WARNING_MSG = "CryptographyDeprecationWarning: Blowfish has been deprecated"

CORE_FUNCTION_APP_NAME = "hub%sc1us02core"
BIZ_FUNCTION_APP_NAME = "hub%sc1us02biz"
FUNCTION_APP_DOMAIN = "https://%s.azurewebsites.net/"
DNS_A_REC_BIZ = "hub%sc1us02biz"
DNS_A_REC_CORE = "hub%sc1us02core"
DNS_A_REC_BIZ_SCM = "hub%sc1us02biz.scm"
DNS_A_REC_CORE_SCM = "hub%sc1us02core.scm"

PASSED = "Passed"
FAILED = "FAILED"
STARTED = "STARTED"
RESUMED = "RESUMED"

GET_PRIORITY_QUERY = "SELECT priority FROM MetallicHubRulePriority;"
UPDATE_PRIORITY_QUERY = "UPDATE MetallicHubRulePriority SET priority = priority+1;"

REMOTE_BRANCH_NAME = "origin"


class FunctionAppKeyType(enum.Enum):
    """Enum for representing the Azure Function App key types"""
    DEFAULT = 1
    MASTER = 2


class CheckPRType(enum.Enum):
    """Enum for representing the type of Azure PR type"""
    NEW = 1
    UPDATE = 2


class ReqType(enum.Enum):
    """Enum for representing the type of API requests"""
    GET = 1
    POST = 2
    DELETE = 3


lh_auth_req = {
    'username': "",
    'password': ""
}

lh_add_ring_info_req = [
    {
        "name": "%s Access URL",
        "configKey": "commvault.%s.access.url",
        "configValue": f"https://%s.{external_domain_suffix}/commandcenter/api",
        "configValueType": "text",
        "configCategory": "commvault.core.ring"
    },
    {
        "name": "%s Access Username",
        "configKey": "commvault.%s.access.username",
        "configValue": "",
        "configValueType": "text",
        "configCategory": "commvault.core.ring"
    },
    {
        "name": "%s Access Password",
        "configKey": "commvault.%s.access.password",
        "configValue": "",
        "configValueType": "password_aes256",
        "configCategory": "commvault.core.ring"
    }
]

lh_search_field = "/search?filter=searchTerm:commvault.%s.access"
