# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for managing Azure Application Gateway in Metallic Ring

    AzureAppGatewayHelper:

        __init__()                              --  Initializes Azure Application Gateway Helper

        run_command                             --  Runs a given az command

        enable_vnet_integration                 --  Enables VNET on a given function app

        is_vnet_integration_enabled             --  Checks if VNET integration is enabled

        create_app_service_plan                 --  Creates a app service plan

        create_app_service                      --  Creates a App Service in the Azure subscription

        create_backend_pool                     --  Creates backend pool

        get_app_service_address                 --  Gets the address of the app service

        get_static_web_prim_endpoints           --  Gets the static web primary endpoint for storage containers

        get_static_web_sec_endpoints            --  Gets the static web secondary endpoint for storage containers

        add_backend_pool_with_target            --  Adds backend pool with target app service

        remove_backend_pool_with_target         --  Removes target of a backend pools

        add_backend_pool_with_address           --  Adds backend pool with target address

        add_backend_settings                    --  Adds a new backend settings

        add_health_probe                        --  Adds health probe to application gateway

        create_listener                         --  Creates listener in the application gateway

        create_rules                            --  Creates rules in the application gateway

        update_rules                            --  Updates rules in the application gateway

        create_url_path_map                     --  Create URL Path Map in application gateway

        create_path_map_rule                    --  Create path map rules in application gateway

        delete_path_map                         --  Deletes path map in application gateway

        get_function_app_ip_addr                --  Gets the IP address of a given function app

        create_az_dns_record                    --  Create DNS records in application gateway

        update_url_path_map                     --  Updates URL Path Map in application gateway

        delete_path_map_rule                    --  Deletes path map in application gateway

        delete_backend_pool                     --  Deletes a backend pool with given name

        delete_backend_settings                 --  Deletes a new backend settings

        delete_health_probe                     --  Deletes health probe on application gateway

        delete_listener                         --  Deletes listener in the application gateway

        delete_rules                            --  Delete rules in the application gateway

        delete_az_dns_record                    --  Delete DNS records in application gateway
"""

import subprocess
import json
from urllib.parse import urlparse

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from MetallicHub.Utils import Constants as cs
from MetallicRing.Utils import Constants as r_cs
from MetallicRing.Core.sqlite_db_helper import SQLiteDBQueryHelper

_CONFIG = get_config(json_path=cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub


class AzureAppGatewayHelper:
    """ contains helper class for Azure application gateway related operations"""

    def __init__(self, rid, config=_CONFIG.azure_credentials):
        """
        Initializes Azure Application Gateway Helper
        Args:
            rid(str)        --  Ring ID to be used
            config(dict)    --  Azure credentials information
        """
        self.log = logger.get_log()
        self.log.info("Initiazlizing Azure app gateway helper")
        self.subscription_id = config.SUBSCRIPTION_ID
        self.tenant_id = config.TENANT_ID
        self.orbit_resource_group = config.ORBIT_RESOURCE_GROUP
        self.resource_group = cs.RESOURCE_GROUP_NAME
        self.subnet = cs.VN_SUBNET_NAME
        self.organization = config.ORGANIZATION
        self.vnet = config.VNET_NAME
        self.app_gateway = config.APP_GATEWAY_NAME
        self.vnet_rg = config.VNET_RESOURCE_GROUP
        self.local_machine = Machine()
        login_cmd = f"az login --service-principal --username {config.CLIENT_ID} " \
                    f"--password {config.CLIENT_SECRET} " \
                    f"--tenant {config.TENANT_ID}"
        self.run_command(login_cmd)
        self.log.info("Azure app gateway helper initialized")

    def run_command(self, command, output_type=r_cs.CMD_FORMATTED_OP):
        """
        Runs a given az command
        Args:
            command(str)        --  Command to be executed
            output_type(str)    --  Type of output to be returned
        Raises:
            Exception when command fails to return expected results
        Returns:
            Command output either formatted or raw output
        """
        self.log.info(f"Request received to run the following command - [{command}]")
        command_op = self.local_machine.execute_command(command)
        if command_op.exception_message:
            if not cs.BLOWFISH_WARNING_MSG in command_op.exception_message:
                raise Exception(command_op.exception_code,
                                command_op.exception_message)
        elif command_op.exception:
            raise Exception(command_op.exception_code, command_op.exception)
        self.log.info(f"Formatted op - [{command_op.formatted_output}]."
                      f"output - [{command_op.output}]")
        if output_type == r_cs.CMD_FORMATTED_OP:
            return command_op.formatted_output
        else:
            return command_op.output

    def enable_vnet_integration(self, function_app_name, is_staging=False):
        """
        Enables VNET on a given function app
        Args:
            function_app_name(str)      --  Name of the function App
            is_staging(bool)            --  Flag to represent if it's staging slot
        Raises:
            Exception,
                When enabling VNET fails
        """
        self.log.info(f"Request received to enable vnet on app - [{function_app_name}]")
        staging = ""
        slot = ""
        if is_staging:
            staging = "-s staging"
            slot = "/slots/staging"
            self.log.info("This is a staging app")
        if not self.is_vnet_integration_enabled(function_app_name, is_staging):
            self.log.info("Vnet integration is disabled. Enabling it")
            cmd = f"az functionapp vnet-integration add -g '{self.resource_group}' -n '{function_app_name}' " \
                  f"--vnet '/subscriptions/{self.subscription_id}/resourceGroups/{self.vnet_rg}/providers/" \
                  f"Microsoft.Network/virtualNetworks/{self.vnet}' " \
                  f"--subnet '{self.subnet}' --subscription {self.subscription_id} {staging}"
            self.run_command(cmd)
            if not self.is_vnet_integration_enabled(function_app_name, is_staging):
                raise Exception("Failed to enable VNET on function app")
            self.log.info("Vnet integration is enabled. Disabling Route all option")
            cmd = f"az resource update --resource-group {self.resource_group} --name {function_app_name}{slot} " \
                  "--resource-type 'Microsoft.Web/sites' --set properties.vnetRouteAllEnabled=false  " \
                  f"--subscription {self.subscription_id}"
            self.run_command(cmd)
            self.log.info(f"Disabled route all option for the function app - [{function_app_name}]")
        self.log.info(f"Vnet for function app - [{function_app_name}] is enabled")

    def is_vnet_integration_enabled(self, function_app_name, is_staging=False):
        """
        Checks if VNET integration is enabled
        Args:
            function_app_name(str)      --  Name of the function app
            is_staging(bool)            --  Flag to represent if it's staging slot
        Returns:
            Boolean, true/false based on the VNET integration on the function app
        """
        self.log.info("Checking if VNET integration is turned off")
        staging = ""
        if is_staging:
            staging = "-s staging"
            self.log.info("This is a staging app")
        output = self.run_command(f"az functionapp vnet-integration list --resource-group {self.resource_group} "
                                  f"--subscription {self.subscription_id} "
                                  f"--name {function_app_name} {staging}")
        list_op = json.loads(output)
        self.log.info(f"Output of the following command is: [{output}]")
        for item in list_op:
            if item.get('id', None) is not None:
                self.log.info("VNET integration is enabled for this function app")
                return True
        self.log.info("VNET integration is disabled for this function app")
        return False

    def create_app_service_plan(self, app_service_plan, sku, is_linux=True):
        """
        Creates a app service plan
        Args:
            app_service_plan(str)       --  Name of the app service plan
            sku(str)                    --  SKU for the app service plan
            is_linux(bool)              --  True if linux else false
        """
        self.log.info(f"Request received to create app service plan - [{app_service_plan}]")
        self.run_command(
            f"az appservice plan create --name '{app_service_plan}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}'"
            f" --sku '{sku}' --is-linux '{is_linux}'")
        self.log.info("Service plan created successfully")

    def create_app_service(self, app_service, app_service_plan, runtime):
        """
        Creates a app service with the given app service plan
        Args:
            app_service(str)        --  Name of the app service
            app_service_plan(str)   --  Name of the plan to be used
            runtime(str)            --  Runtime for the app service
        """
        self.log.info(f"Request received to create App service - [{app_service}] under plan [{app_service_plan}]")
        self.run_command(
            f"az webapp create --name '{app_service}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}' "
            f"--plan '{app_service_plan}' --runtime '{runtime}' --deployment-local-git")
        self.log.info("Service created successfully")

    def create_backend_pool(self, backend_pool):
        """
        Creates a backend pool with given name
        Args:
            backend_pool(str)       --  Name of the backend pool
        """
        self.log.info(f"Request received to create backend pool - [{backend_pool}]")
        self.run_command(
            f"az network application-gateway address-pool create --name '{backend_pool}' "
            f"--gateway-name '{self.app_gateway}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}'")
        self.log.info("Backend pool created successfully")

    def delete_backend_pool(self, backend_pool):
        """
        Deletes a backend pool with given name
        Args:
            backend_pool(str)       --  Name of the backend pool
        """
        self.log.info(f"Request received to delete backend pool - [{backend_pool}]")
        self.run_command(
            f"az network application-gateway address-pool delete --name '{backend_pool}' "
            f"--gateway-name '{self.app_gateway}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}'")
        self.log.info("Backend pool delete successfully")

    def get_app_service_address(self, app_service):
        """
        Gets the address of the app service
        Args:
            app_service(str)        --  Name of the app service
        """
        self.log.info(f"Request received to get app service address - [{app_service}]")
        app_service_address = self.run_command(
            f"az webapp show --name '{app_service}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.resource_group}' "
            f"--query defaultHostName --output tsv")
        self.log.info(f"App service address - [{app_service_address}]")
        return app_service_address

    def get_static_web_prim_endpoints(self, storage_container):
        """
        Gets the static web primary endpoint for storage containers
        Args:
            storage_container(str)      --  name of the storage container
        """
        self.log.info(f"Request to get static web primary endpoint for storage container - [{storage_container}]")
        primary_endpoint = self.run_command(
            f"az storage account show -n '{storage_container}' -g '{self.resource_group}' "
            f"--subscription '{self.subscription_id}' --query 'primaryEndpoints.web' --output tsv")
        self.log.info(f"Primary endpoint - [{primary_endpoint}]")
        return primary_endpoint

    def get_static_web_sec_endpoints(self, storage_container):
        """
        Gets the static web secondary endpoint for storage containers
        Args:
            storage_container(str)      --  name of the storage container
        """
        self.log.info(f"Request to get static web secondary endpoint for storage container - [{storage_container}]")
        secondary_endpoint = self.run_command(
            f"az storage account show -n '{storage_container}' -g '{self.resource_group}' "
            f"--subscription '{self.subscription_id}' --query 'secondaryEndpoints.web' --output tsv")
        self.log.info(f"Secondary endpoint - [{storage_container}]")
        return secondary_endpoint

    def add_backend_pool_with_target(self, backend_pool, app_service):
        """
        Adds backend pool with target app service
        Args:
            backend_pool(str)           --  name of the backend pool
            app_service(str)            --  name of the app service
        """
        self.log.info(f"Request received to add backend ppol - [{backend_pool}] with target [{app_service}]")
        app_service_address = self.get_app_service_address(app_service)
        self.run_command(
            f"az network application-gateway address-pool update --name '{backend_pool}' "
            f"--gateway-name '{self.app_gateway}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}' --servers '{app_service_address}'")
        self.log.info("Backend pool created successfully")

    def remove_backend_pool_with_target(self, backend_pool, index=0):
        """
        Removes target of a backend pools
        Args:
            backend_pool(str)           --  name of the backend pool
            index(int)                  --  index of the target to be removed
        """
        self.log.info(f"Request received to remove backend pool - [{backend_pool}] with target index [{index}]")
        self.run_command(
            f"az network application-gateway address-pool update --name '{backend_pool}' "
            f"--gateway-name '{self.app_gateway}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}' --remove backendAddresses {index}")
        self.log.info("Backend pool created successfully")

    def add_backend_pool_with_address(self, backend_pool, address):
        """
        Adds a new backend pool with address type as target
        Args:
            backend_pool(str)       --  name with the backend pool
            address(str)            --  address of the backend pool
        """
        self.log.info(f"Request received to add backend pool - [{backend_pool}] with target [{address}]")
        self.run_command(
            f"az network application-gateway address-pool update --name '{backend_pool}' "
            f"--gateway-name '{self.app_gateway}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}' --servers '{address}'")
        self.log.info("Backend pool created successfully")

    def add_backend_pool_web_address(self, storage_container, backend_pool):
        """
        Adds a new backend pool with web address of a storage container
        Args:
            storage_container(str)          --  Name of the storage container
            backend_pool(str)               --  Name of the backend pool
        """
        self.log.info(f"Request received to update address pool - [{storage_container}]."
                      f"Backend pool [{backend_pool}]")
        prim_endpoint_url = self.get_static_web_prim_endpoints(storage_container)
        prim_endpoint = urlparse(prim_endpoint_url).netloc
        sec_endpoint_url = self.get_static_web_sec_endpoints(storage_container)
        sec_endpoint = urlparse(sec_endpoint_url).netloc
        self.run_command(
            f"az network application-gateway address-pool update --name '{backend_pool}' "
            f"--gateway-name '{self.app_gateway}' --subscription '{self.subscription_id}' "
            f"--resource-group '{self.orbit_resource_group}' --servers '{prim_endpoint}' '{sec_endpoint}'")
        self.log.info("Updated backend pool web address")

    def add_backend_settings(self, bs_name, port, cookie_based_affinity,
                             path=None, affinity_name=None, request_timeout=300, enable_probe=0, probe_name=None,
                             override_hostname=1):
        """
        Adds a new backend settings
        Args:
            bs_name(str)                --  name of the backend settings
            port(int)                   --  port to be used for backend settings
            cookie_based_affinity(str)  --  Enabled/Disabled to either enable/disable cookie based affinity
            path(str)                   --  path to be used for the backend settings
            affinity_name(str)          --  name of the affinity cookie
            request_timeout(int)        --  timeout seconds for backend settings
            enable_probe(int)           --  0 - disable probe,
                                            1 - enable probe
            probe_name(str)             --  Name of the probe to be used
            override_hostname(int)      --  0 - not to override
                                            1 - override the hostname
        """
        self.log.info(f"Request received to add backend settings - [{bs_name}]")
        cmd = f"az network application-gateway http-settings create --gateway-name {self.app_gateway} " \
              f"--name {bs_name} --port {port} --resource-group {self.orbit_resource_group} " \
              f"--connection-draining-timeout 300 " \
              f"--cookie-based-affinity {cookie_based_affinity} " \
              f"--enable-probe {enable_probe} " \
              f"--host-name-from-backend-pool {override_hostname} " \
              f"--protocol Https --timeout {request_timeout} " \
              f"--subscription {self.subscription_id}"
        if path is not None:
            cmd += f" --path {path}"
        if probe_name is not None:
            cmd += f" --probe {probe_name}"
        if affinity_name is not None:
            cmd += f" --affinity-cookie-name {affinity_name}"
        self.run_command(cmd)
        self.log.info("Backend setting added")

    def delete_backend_settings(self, bs_name):
        """
        Deletes a new backend settings
        Args:
            bs_name(str)                --  name of the backend settings
        """
        self.log.info(f"Request received to delete backend settings - [{bs_name}]")
        cmd = f"az network application-gateway http-settings delete --gateway-name {self.app_gateway} " \
              f"--name {bs_name} --resource-group {self.orbit_resource_group} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Backend setting deleted")

    def add_health_probe(self, name, host, path=None):
        """
        Adds health probe on application gateway
        Args:
            name(str)               --  name of the health probe
            host(str)               --  name of the host
            path(str)               --  URL path for the health probe
        """
        self.log.info(f"Request received to add health probe - [{name}]")
        cmd = f"az network application-gateway probe create --gateway-name {self.app_gateway} " \
              f"--name {name} " \
              f"--resource-group {self.orbit_resource_group} " \
              "--from-http-settings false " \
              f"--host {host} --interval 30 --match-status-codes 200 " \
              f"--protocol Https --threshold 3 --timeout 30 --subscription {self.subscription_id}"
        if path is not None:
            cmd += f" --path {path}"
        self.run_command(cmd)
        self.log.info("Health probe created successfully")

    def delete_health_probe(self, name):
        """
        deletes health probe on application gateway
        Args:
            name(str)               --  name of the health probe
        """
        self.log.info(f"Request received to delete health probe - [{name}]")
        cmd = f"az network application-gateway probe delete --gateway-name {self.app_gateway} " \
              f"--name {name} " \
              f"--resource-group {self.orbit_resource_group} --subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Health probe deleted successfully")

    def create_listener(self, name, host_name, ssl_cert=cs.AG_HP_SSL_CERT_NAME):
        """
        Creates listener in the application gateway
        Args:
            name(str)               --  name of the listener
            host_name(str)          --  name of the host
            ssl_cert(str)           --  name of the ssl certificate
        """
        self.log.info(f"Request received to create listener - [{name}]")
        cmd = f"az network application-gateway http-listener create --frontend-port " \
              f"{cs.AG_LISTENER_FRONTEND_443_PORT_NAME} " \
              f"--gateway-name {self.app_gateway} --name {name} --resource-group {self.orbit_resource_group} " \
              f"--frontend-ip {cs.AG_LISTENER_FRONTEND_PRIVATE_IP_NAME} --host-name {host_name} " \
              f"--ssl-cert {ssl_cert} --subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Listener created successfully")

    def delete_listener(self, name):
        """
        Deletes listener in the application gateway
        Args:
            name(str)               --  name of the listener
        """
        self.log.info(f"Request received to delete listener - [{name}]")
        cmd = f"az network application-gateway http-listener delete " \
              f"--gateway-name {self.app_gateway} --name {name} --resource-group {self.orbit_resource_group} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Listener deleted successfully")

    def create_rules(self, name, path_map_name, listener_name, backend_pool, backend_settings):
        """
        Creates rules in the application gateway
        Args:
            name(str)               --  name of the rule to be created
            path_map_name(str)      --  name of the path map
            listener_name(str)      --  name of the listener
            backend_pool(str)       --  name of the backend pool
            backend_settings(str)   --  name of the backend settings
        """
        self.log.info(f"Request received to create rule - [{name}]")
        sql_helper = SQLiteDBQueryHelper()
        result = sql_helper.execute_query(cs.GET_PRIORITY_QUERY)
        priority = result.rows[0][0]
        cmd = f"az network application-gateway rule create --gateway-name {self.app_gateway} " \
              f"--name {name} --resource-group {self.orbit_resource_group} --http-listener {listener_name} " \
              f"--priority {priority} --rule-type PathBasedRouting --subscription {self.subscription_id} " \
              f"--address-pool {backend_pool} --http-settings {backend_settings} " \
              f"--url-path-map {path_map_name}"
        self.run_command(cmd)
        sql_helper.execute_query(cs.UPDATE_PRIORITY_QUERY)
        self.log.info(f"Rule created with priority - [{priority}]")

    def delete_rules(self, name):
        """
        Delete rules in the application gateway
        Args:
            name(str)               --  name of the rule to be created
        """
        self.log.info(f"Request received to delete rule - [{name}]")
        cmd = f"az network application-gateway rule delete --gateway-name {self.app_gateway} " \
              f"--name {name} --resource-group {self.orbit_resource_group} --subscription {self.subscription_id} "
        self.run_command(cmd)
        self.log.info(f"Rule deleted")

    def update_rules(self, name, path_map_name, listener_name, backend_pool, backend_settings):
        """
        Updates rules in the application gateway
        Args:
            name(str)               --  name of the rule to be created
            path_map_name(str)      --  name of the path map
            listener_name(str)      --  name of the listener
            backend_pool(str)       --  name of the backend pool
            backend_settings(str)   --  name of the backend settings
        """
        cmd = f"az network application-gateway rule update --gateway-name {self.app_gateway} " \
              f"--name {name} --resource-group {self.orbit_resource_group} --http-listener {listener_name} " \
              f"--rule-type PathBasedRouting --subscription {self.subscription_id} " \
              f"--address-pool {backend_pool} --http-settings {backend_settings} " \
              f"--url-path-map {path_map_name}"
        self.run_command(cmd)
        self.log.info(f"Rule updated with priority")

    def create_url_path_map(self, path_name, path_rule_name, backend_pool, backend_settings, paths):
        """
        Create URL Path Map in application gateway
        Args:
            path_name(str)          --  name of the url path map
            path_rule_name(str)     --  name of the url path rule
            backend_pool(str)       --  name of the backend pool
            backend_settings(str)   --  name of the backend settings
            paths(list)             --  list of paths for the url path map
        """
        self.log.info(f"Request received to create URL path map - [{path_name}], [{[path_rule_name]}]")
        path_str = ""
        for path in paths:
            path_str += f" {path}"
        self.log.info(f"Paths - [{path_str}]")
        cmd = f"az network application-gateway url-path-map create -g {self.orbit_resource_group} " \
              f"--gateway-name {self.app_gateway} -n {path_name} --rule-name {path_rule_name} --paths  {path_str} " \
              f"--address-pool {backend_pool} --default-address-pool {backend_pool} " \
              f"--http-settings {backend_settings} --default-http-settings {backend_settings} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Created URL path map")

    def update_url_path_map(self, path_name, backend_pool, backend_settings):
        """
        Updates URL Path Map in application gateway
        Args:
            path_name(str)          --  name of the url path map
            backend_pool(str)       --  name of the backend pool
            backend_settings(str)   --  name of the backend settings
        """
        self.log.info(f"Request received to create URL path map - [{path_name}]]")
        cmd = f"az network application-gateway url-path-map update -g {self.orbit_resource_group} " \
              f"--gateway-name {self.app_gateway} -n {path_name} --default-address-pool {backend_pool} " \
              f"--default-http-settings {backend_settings} --subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Updated URL path map")

    def create_path_map_rule(self, path_rule_name, path_map_name, backend_pool, backend_settings, paths):
        """
        Create path map rules in application gateway
        Args:
            path_rule_name(str)         --  Name of the path rule
            path_map_name(str)          --  Name of the path map
            backend_pool(str)           --  Name of the backend pool
            backend_settings(str)       --  Name of the backend settings
            paths(list)                 --  List of paths to be added to path map rules
        """
        self.log.info(f"Request received to create path map rule - [{path_rule_name}], "
                      f"path map name -[{path_map_name}], paths - [{paths}]")
        path_str = ""
        for path in paths:
            path_str += f" {path}"
        cmd = f"az network application-gateway url-path-map rule create --gateway-name {self.app_gateway} " \
              f"--resource-group {self.orbit_resource_group} --name {path_rule_name} --path-map-name {path_map_name} " \
              f"--paths {path_str} --address-pool {backend_pool} --http-settings {backend_settings} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Path map rule created successfully")

    def delete_path_map(self, name):
        """
        Deletes path map in application gateway
        Args:
            name(str)       --  Name of the path map
        """
        self.log.info(f"Deleting path map - [{name}]")
        cmd = f"az network application-gateway url-path-map delete --resource-group {self.orbit_resource_group} " \
              f"--gateway-name {self.app_gateway} --name {name} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Deleted path map successfully")

    def delete_path_map_rule(self, path_map_name, name):
        """
        Deletes path map in application gateway
        Args:
            path_map_name(str)  --  Name of the path map where the rule is present
            name(str)           --  Name of the path map rules
        """
        self.log.info(f"Deleting path map rule - [{name}]")
        cmd = f"az network application-gateway url-path-map rule delete --resource-group {self.orbit_resource_group} " \
              f"--gateway-name {self.app_gateway} --path-map-name {path_map_name} --name {name} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("Deleted path map successfully")

    def get_function_app_ip_addr(self, name):
        """
        Gets the IP address of a given function app
        Args:
            name(str)       --  Name of the function app
        """
        self.log.info("Request received to creation function app IP address")
        cmd = f"az network nic list -g {self.resource_group} --subscription {self.subscription_id}"
        output = self.run_command(cmd, output_type="normal")
        network_info = json.loads(output)
        for private_ip in network_info:
            for ip_config in private_ip.get("ipConfigurations"):
                inbound_ip = ip_config.get("privateIPAddress", None)
                private_line = ip_config.get("privateLinkConnectionProperties", None)
                if private_line is not None:
                    fqdns = private_line.get("fqdns", None)
                    if fqdns is not None:
                        if name in fqdns[0]:
                            self.log.info(f"IP address obtained is [{inbound_ip}]")
                            return inbound_ip
        raise Exception(f"No inbound IP address found for the given function app name - [{name}]")

    def create_az_dns_record(self, name, ip_address, resource_group, zone_name):
        """
        Create DNS records in application gateway
        Args:
            name(str)           --  Name of the dns record
            ip_address(str)     --  IP Address for the DNS record
            resource_group(str) --  Resource group where the dns record has to be created
            zone_name(str)      --  Zone where the dns record has to be created
        """
        self.log.info(f"Request received to create dns records - [{name}], [{ip_address}]")
        cmd = "az network private-dns record-set a add-record " \
              f"--resource-group '{resource_group}' --zone-name {zone_name} " \
              f"--record-set-name {name} --ipv4-address {ip_address} " \
              f"--subscription {self.subscription_id}"
        self.run_command(cmd)
        self.log.info("DNS record created successfully")

    def delete_az_dns_record(self, name, resource_group, zone_name):
        """
        Delete DNS records in application gateway
        Args:
            name(str)           --  Name of the dns record
            resource_group(str) --  Resource group where the dns record has to be created
            zone_name(str)      --  Zone where the dns record has to be created
        """
        self.log.info(f"Request received to delete dns records - [{name}]")
        cmd = "az network private-dns record-set a delete " \
              f"--resource-group '{resource_group}' --zone-name {zone_name} " \
              f"--name {name} --subscription {self.subscription_id} --yes"
        self.run_command(cmd)
        self.log.info("DNS record deleted successfully")
