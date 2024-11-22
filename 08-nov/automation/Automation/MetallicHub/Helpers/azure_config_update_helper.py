# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper to perform Azure config related operations

    switch_directory                --  Switches directory to the given path

    update_network_gateway_rules    --  Updates the network gateway rules

    update_ring_gp_json             --  Updates ring global param json file

    delete_ring_gp_json             --  Deletes a value in key value pair for a given json file

    delete_blob_ring_gp_json        --  Deletes a blob based on the kv pair passed for a given json file

    update_azure_config_files       --  Updates azure core ring json file

"""

import json
import os

from MetallicHub.Helpers.azure_config_helper import AzureConfigHelper
from MetallicHub.Helpers.azure_application_gateway_helper import AzureAppGatewayHelper
from MetallicHub.Utils import Constants as cs
from cvpysdk.commcell import Commcell


def switch_directory(path, ring_name, clone_path=None):
    """
    Switches directory to the given path
    Args:
        ring_name           -- name of the ring
        path(str)           --  path to be switched to
        clone_path(str)     --  clone path to be switched to
    """
    if clone_path is None:
        clone_path = cs.HUB_CONFIG_CLONE_PATH % ring_name
    print(f"Switching to directory - [{path}]. Root - [{clone_path}]")
    os.chdir(clone_path)
    os.chdir(path)


def update_network_gateway_rules():
    """
    Updates the network gateway rules
    """
    cc = Commcell("newyork.idx.commvault.com", "admin", "Builder!12")
    agh = AzureAppGatewayHelper(cc)
    ring_name_ips = ['051', '052', '053', '055', '056', '057', '058', '059', '060', '061', '062',
                     '066', '067', '069']
    for ring_name_ip in ring_name_ips:
        rule_bt = cs.AG_BP_WEB % ring_name_ip
        rule_bs = cs.AG_BS_WEB % ring_name_ip
        ag_wec_bs = cs.AG_BS_WEC % ring_name_ip
        ag_wec_bp = cs.AG_BP_WEC % ring_name_ip
        web_rule = cs.PB_WEB_RULE_NAME % ring_name_ip
        app_rule_web_val = ["/maintenance.html,/assets/brand/*"]
        app_gateway_rule_name = cs.AG_RULE_NAME % ring_name_ip
        agh.update_url_path_map(app_gateway_rule_name, ag_wec_bp, ag_wec_bs)
        # agh.delete_path_map_rule(app_gateway_rule_name, web_rule)
        agh.create_path_map_rule(web_rule, app_gateway_rule_name, rule_bt, rule_bs, app_rule_web_val)


def update_ring_gp_json(clone_name, filename, key_value_pair):
    """
    Updates ring global param json file
    Args:
        ring_name - name of the ring
        filename - name of the file to be modified
        key_value_pair - Dictionary having key and value
    """
    print(f"Request received to update global param config. Switching cwd - [{cs.HUB_RING_GLOBAL_PARAM_FILE_PATH}]")
    switch_directory(cs.HUB_RING_GLOBAL_PARAM_FILE_PATH, clone_name)
    print(f"CWD changed. update global param file name - [{filename}]")
    # Read the content of the JSON file
    print("Reading file contents")
    with open(filename, 'r') as file:
        data = json.load(file)
        print("File read successfully")
    # Write the updated data back to the file
    for content in data:
        if key_value_pair.get(content.get("name"), None) is not None:
            kval = key_value_pair.get(content.get("name"))
            ct_dict = content.get(cs.ORBIT_FILE_VALUE_CONSTANT, None)
            # if ct_dict == ",serviceCatalogV2":
            #     content[cs.ORBIT_FILE_VALUE_CONSTANT] = "serviceCatalogV2"
            if ct_dict is None or ct_dict == "":
                content[cs.ORBIT_FILE_VALUE_CONSTANT] = \
                    f"{kval}"
            else:
                content[cs.ORBIT_FILE_VALUE_CONSTANT] += \
                    f",{kval}"
    print(f"Content updated successfully - [{data}]. Writing to file")
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Write to file - [{filename}] successful")


def delete_ring_gp_json(clone_name, filename, key_value_pair):
    """
    Deletes a value in key value pair for a given json file
    Args:
        ring_name - name of the ring
        filename - name of the file to be modified
        key_value_pair - Dictionary having key and value
    """
    print(f"Request received to update global param config. Switching cwd - [{cs.HUB_RING_GLOBAL_PARAM_FILE_PATH}]")
    switch_directory(cs.HUB_RING_GLOBAL_PARAM_FILE_PATH, clone_name)
    print(f"CWD changed. update global param file name - [{filename}]")
    # Read the content of the JSON file
    print("Reading file contents")
    with open(filename, 'r') as file:
        data = json.load(file)
        print("File read successfully")
    # Write the updated data back to the file
    for content in data:
        if key_value_pair.get(content.get("name"), None) is not None:
            del_kval = key_value_pair.get(content.get("name"))
            cur_kval = content.get(cs.ORBIT_FILE_VALUE_CONSTANT, None)
            if not cur_kval is None and cur_kval != "":
                content_str = content[cs.ORBIT_FILE_VALUE_CONSTANT]
                content[cs.ORBIT_FILE_VALUE_CONSTANT] = str.replace(content_str, del_kval, "")
    print(f"Content updated successfully - [{data}]. Writing to file")
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Write to file - [{filename}] successful")


def delete_blob_ring_gp_json(clone_name, filename, key_value_pair):
    """
    Deletes a blob based on the kv pair passed for a given json file
    Args:
        ring_name - name of the ring
        filename - name of the file to be modified
        key_value_pair - Array of key values
    """
    print(f"Request received to update global param config. Switching cwd - [{cs.HUB_RING_GLOBAL_PARAM_FILE_PATH}]")
    switch_directory(cs.HUB_RING_GLOBAL_PARAM_FILE_PATH, clone_name)
    print(f"CWD changed. update global param file name - [{filename}]")
    # Read the content of the JSON file
    print("Reading file contents")
    with open(filename, 'r') as file:
        data = json.load(file)
        print("File read successfully")
    # Write the updated data back to the file
    for index, content in enumerate(data):
        for val in key_value_pair:
            if content is not None and val == content.get("name", None):
                data[index] = None
    data = [item for item in data if item is not None]
    print(f"Content updated successfully - [{data}]. Writing to file")
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Write to file - [{filename}] successful")


def update_azure_config_files():
    """
    Updates azure core ring json file
    """
    ring_name_ips = ['m051', 'm052', 'm053', 'm054', 'm055', 'm056', 'm057', 'm058', 'm059', 'm060', 'm061', 'm062', 'm063',
                     'm066', 'm067', 'm068', 'm069', 'm070', 'm071', 'm072', 'm073', 'm074', 'm075', 'm076', 'm077', 'm078']
    test_clone_append = "clone10"
    clone_path = cs.HUB_CONFIG_CLONE_PATH % test_clone_append
    ach = AzureConfigHelper(None)
    ach.perform_clone_task(clone_path)
    ach.perform_checkout_task()

    # kv_pair = {"Restricted Nav Items For Restricted Admin": "vsaOverview,kubernetesOverview,dbOverview",
    #            "Restricted Nav Items For Tenant Admin": "vsaOverview,kubernetesOverview,dbOverview",
    #            "Restricted Nav Items For Tenant User": "vsaOverview,kubernetesOverview,dbOverview"}
    kv_pair = {"Restricted Nav Items For Restricted Admin", "Restricted Nav Items For Tenant Admin",
               "Restricted Nav Items For Tenant User",  "Metallic-Auth-Service-Url", "AzureMultiTenantMIClientId",
               "AzureMultiTenantUrl", "Metallic Service Account", "supportedVendors", "supportedFSVendors",
               "supportedCloudStorageVendors", "Restricted Nav Items For MSP Admin",
               "Restricted Nav Items For MSP User"}

    for ring_name_ip in ring_name_ips:
        file = cs.HUB_RING_CORE_JSON_FILE % ring_name_ip.lower()
        delete_complete_blob_ring_core_json(test_clone_append, file, None)

    file = "cv_hub_automation_template.json"
    update_ring_gp_json(test_clone_append, file, kv_pair)


def delete_complete_blob_ring_core_json(clone_name, filename):
    """
    Deletes a blob of data based on a keyvalue pair for a given json file
    Args:
        ring_name - name of the ring
        filename - name of the file to be modified
    """
    print(f"Request received to update global param config. Switching cwd - [{cs.HUB_RING_CORE_FILE_PATH}]")
    switch_directory(cs.HUB_RING_CORE_FILE_PATH, clone_name)
    print(f"CWD changed. update global param file name - [{filename}]")
    # Read the content of the JSON file
    print("Reading file contents")
    if not os.path.exists(filename):
        print(f"{filename} doesn't exist")
        return
    with open(filename, 'r') as file:
        data = json.load(file)
        print("File read successfully")
    # Write the updated data back to the file
    filtered_data = [item for item in data if not item.get('name', '').startswith('package:')]
    print(f"Content updated successfully - [{data}]. Writing to file")
    with open(filename, 'w') as file:
        json.dump(filtered_data, file, indent=4)
    print(f"Write to file - [{filename}] successful")
