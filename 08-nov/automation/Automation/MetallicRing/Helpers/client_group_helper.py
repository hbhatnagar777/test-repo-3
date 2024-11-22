# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" helper class for managing Client Groups in Metallic Ring

    ClientGroupRingHelper:

        __init__()                              --  Initializes client group Ring Helper

        start_task                              --  Starts the client group configuration task

        create_smart_client_group               --  Creates a smart client group in the commcell

"""

from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.CLIENT_GROUP_CONFIG_FILE_PATH)
_AD_SETTING_CONFIG = get_config(json_path=cs.ADDITIONAL_SETTING_CONFIG_FILE_PATH)
_RING_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class ClientGroupRingHelper(BaseRingHelper):
    """ helper class for managing Client Groups in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.client_groups = self.commcell.client_groups

    def start_task(self):
        """
        Starts the client group configuration task
        """
        try:
            self.log.info("Starting client group helper task")
            if self.ring.provision_type == cs.RingProvisionType.CUSTOM.value:
                self.create_custom_client_groups()
            else:
                self.create_smart_client_groups()
            if not self.client_groups.has_clientgroup(cs.CG_UNIVERSAL_INSTALLER_NAME):
                self.log.info("Creating universal install client group")
                self.client_groups.add(cs.CG_UNIVERSAL_INSTALLER_NAME)
            if not self.client_groups.has_clientgroup(cs.CG_CLEANROOM_AZURE_US):
                self.log.info("Creating cleanroom azure client group")
                self.client_groups.add(cs.CG_CLEANROOM_AZURE_US)
            self.log.info("All client group tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute client group helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_smart_rule(self, cg_filter):
        rule_list = None
        if hasattr(cg_filter, "filter_value"):
            if hasattr(cg_filter, "value"):
                self.log.info("Client group has filter value and value set")
                rule_list = self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                 filter_condition=cg_filter.filter_condition,
                                                                 filter_value=cg_filter.filter_value,
                                                                 value=cg_filter.value)
                self.log.info("Smart rule request created and added to rules list")
            else:
                self.log.info("Client group has no value set")
                if cg_filter.filter_rule == cs.CG_ASSOC_CG_KEY:
                    self.log.info(f"Filter rule is [{cs.CG_ASSOC_CG_KEY}]")
                    cg_obj = self.client_groups.get(cg_filter.filter_value)
                    rule_list = self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                     filter_condition=cg_filter.filter_condition,
                                                                     filter_value=cg_filter.filter_value,
                                                                     value=cg_obj.clientgroup_id)
                    self.log.info("Smart rule request created and added to rules list")
                elif cg_filter.filter_rule == cs.CG_HOSTNAME_KEY:
                    self.log.info(f"Filter rule is [{cs.CG_HOSTNAME_KEY}]")
                    filter_value = cg_filter.filter_value
                    if cg_filter.filter_value == cs.CG_FILTER_VALUE_DOMAIN:
                        filter_value = _RING_CONFIG.domain.name
                    rule_list = self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                     filter_condition=cg_filter.filter_condition,
                                                                     filter_value=filter_value,
                                                                     value=filter_value)
                else:
                    filter_value = cg_filter.filter_value
                    if cg_filter.filter_value == cs.CG_VALUE_RING:
                        filter_value = str(_RING_CONFIG.id)
                        if len(filter_value) <= 2:
                            filter_value = f"0{filter_value}"
                    rule_list = self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                                     filter_condition=cg_filter.filter_condition,
                                                                     filter_value=filter_value,
                                                                     value=filter_value)
                    self.log.info("Smart rule request created and added to rules list")
        else:
            self.log.info("Client group has no filter value or value set")
            rule_list = self.client_groups.create_smart_rule(filter_rule=cg_filter.filter_rule,
                                                             filter_condition=cg_filter.filter_condition)
            self.log.info("Smart rule request created and added to rules list")
        return rule_list

    def get_scope_region_value(self, client_group):
        scope_value = client_group.scope_value
        self.log.info("Setting the client group scope")
        if client_group.scope_value == cs.CG_SCOPE_COMMCELL:
            scope_value = _RING_CONFIG.commserv.client_name
        elif client_group.scope_value == cs.CG_SCOPE_USER:
            scope_value = _RING_CONFIG.commserv.new_username
        region = None
        if hasattr(client_group, "region"):
            region = client_group.region
        return region, scope_value

    def create_smart_client_groups(self):
        client_groups = _CONFIG.client_groups
        for client_group in client_groups:
            self.log.info(f"Creating client group with name - [{client_group.client_group_name}]")
            if not self.client_groups.has_clientgroup(client_group.client_group_name):
                rule_list = []
                for cg_filter in client_group.filters:
                    rule_list.append(self.create_smart_rule(cg_filter))
                sclient_groups_list = self.client_groups.merge_smart_rules(rule_list,
                                                                           op_value=client_group.criteria)
                region, scope_value = self.get_scope_region_value(client_group)
                self.create_smart_client_group(client_group.client_group_name, sclient_groups_list,
                                               client_group.client_scope, scope_value, region=region)
                self.log.info("Created smart client group successfully")

    def create_custom_client_groups(self):
        client_groups = _CONFIG.client_groups
        for client_group in client_groups:
            self.log.info(f"Creating client group with name - [{client_group.client_group_name}]")
            if not self.client_groups.has_clientgroup(client_group.client_group_name):
                rule_list = []
                for cg_filter in client_group.filters:
                    if client_group.client_group_name == cs.CustomClientGroups.INFRA_PROXIES.value and \
                            (cg_filter.filter_rule == cs.CG_DISPLAY_NAME_KEY or
                             cg_filter.filter_rule == cs.CG_OS_TYPE_KEY or
                             cg_filter.filter_rule == cs.CG_HOSTNAME_KEY or
                             cg_filter.filter_rule == cs.CG_CLIENT_PROXY):
                        if cg_filter.filter_rule == cs.CG_DISPLAY_NAME_KEY and \
                                cg_filter.filter_value == cs.CG_VALUE_RING:
                            self.log.info(f"Ring ID filter is needed for this group [{client_group.client_group_name}]."
                                          " Not skipping it")
                        else:
                            self.log.info(
                                f"Skipping this filter as it is a custom client group [{client_group.client_group_name}] "
                                f"create request. Filter - [{cg_filter.filter_rule}]")
                            continue
                    elif client_group.client_group_name \
                            in (cs.CustomClientGroups.CS.value, cs.CustomClientGroups.MA_ALL.value,
                                cs.CustomClientGroups.MA_WIN.value, cs.CustomClientGroups.MA_UNIX.value,
                                cs.CustomClientGroups.MA_UNIX_TENANT.value, cs.CustomClientGroups.WEC.value,
                                cs.CustomClientGroups.WES.value, cs.CustomClientGroups.AZURE_MA_US_EAST_2.value) \
                            and (cg_filter.filter_rule == cs.CG_DISPLAY_NAME_KEY or
                                 cg_filter.filter_rule == cs.CG_OS_TYPE_KEY or
                                 cg_filter.filter_rule == cs.CG_HOSTNAME_KEY):
                        if client_group.client_group_name in (cs.CustomClientGroups.MA_WIN.value,
                                                              cs.CustomClientGroups.MA_UNIX.value,
                                                              cs.CustomClientGroups.MA_UNIX_TENANT.value) and \
                                (cg_filter.filter_rule == cs.CG_OS_TYPE_KEY):
                            self.log.info(f"OS Type filter is needed for this group [{client_group.client_group_name}]."
                                          " Not skipping it")
                        else:
                            self.log.info(f"Skipping this filter as it is a custom client group [{client_group.client_group_name}] "
                                          f"create request. Filter - [{cg_filter.filter_rule}]")
                            continue
                    rule_list.append(self.create_smart_rule(cg_filter))
                sclient_groups_list = self.client_groups.merge_smart_rules(rule_list,
                                                                           op_value=client_group.criteria)
                region, scope_value = self.get_scope_region_value(client_group)
                self.create_smart_client_group(client_group.client_group_name, sclient_groups_list,
                                               client_group.client_scope, scope_value, region=region)
                self.log.info("Created smart client group successfully")

    def create_smart_client_group(self, client_group_name, sclient_groups_list, client_scope, scope_value, **kwargs):
        """ Creates a smart client group in the commcell
                Args:
                    client_group_name(str)          --  Name of the client group to be created
                    sclient_groups_list(dict)       --  Dict of smart client rule list
                    client_scope(str)               --  Scope of the client group
                    scope_value(str)                --  Value for client scope
                    kwargs(dict)                    --Key value pairs for supported arguments
                    Supported argument values:
                        region(str)                 --  Name of the region
                Returns:
                    None:

                Raises:
                    Exception:
                        If client group with given name exist

        """

        if self.client_groups.has_clientgroup(client_group_name):
            raise Exception(f"Client group with name {client_group_name} already exists")
        self.log.info(f"Smart client group request: \n cg name [{client_group_name}]"
                      f"\n scg_rule [{sclient_groups_list}]\n client scope: [{client_scope}]"
                      f"\n scope value: [{scope_value}]")
        client_group_obj = self.client_groups.add(client_group_name, clientgroup_description=client_group_name,
                                                  scg_rule=sclient_groups_list,
                                                  client_scope=client_scope,
                                                  client_scope_value=scope_value)
        self.log.info("Client group created")
        region = kwargs.get("region", None)
        if region is not None:
            self.region_helper.edit_region_of_entity(entity_type=cs.ENTITY_TYPE_CG_STR, entity_name=client_group_name,
                                                     entity_region_type=cs.REGION_TYPE_WORKLOAD, region_name=region)
        if client_group_name == cs.WC_CLIENT_GROUP_NAME:
            self.log.info("This is webconsole Client group. Proceeding with creating additional settings at CG level")
            wc_add_setting = _AD_SETTING_CONFIG.wc_client_group
            for add_setting in wc_add_setting:
                if add_setting.key_name == cs.ADD_SETTING_CUSTOM_HOME:
                    custom_home_value = cs.ADD_SETTING_CUSTOM_HOME_VALUE % _RING_CONFIG.custom_webconsole_url
                    client_group_obj.add_additional_setting(category=add_setting.category,
                                                            key_name=add_setting.key_name,
                                                            data_type=add_setting.data_type,
                                                            value=custom_home_value)
                else:
                    client_group_obj.add_additional_setting(category=add_setting.category,
                                                            key_name=add_setting.key_name,
                                                            data_type=add_setting.data_type,
                                                            value=add_setting.value)
                self.log.info(f"Additional settings with name [{add_setting.key_name}] created successfully")

        elif client_group_name == cs.WS_CLIENT_GROUP_NAME:
            self.log.info("This is Web Server Client group. Proceeding with creating additional settings at CG level")
            ws_add_setting = _AD_SETTING_CONFIG.ws_client_group
            for add_setting in ws_add_setting:
                client_group_obj.add_additional_setting(category=add_setting.category,
                                                        key_name=add_setting.key_name,
                                                        data_type=add_setting.data_type,
                                                        value=add_setting.value)
                self.log.info(f"Additional settings with name [{add_setting.key_name}] created successfully")

        elif client_group_name.endswith(cs.MAS_WIN_CLIENT_GROUP_NAME):
            self.log.info("This is Media Agent Windows Client group. "
                          "Proceeding with creating additional settings at CG level")
            mas_add_setting = _AD_SETTING_CONFIG.mas_clients
            ddb_path = _RING_CONFIG.media_agents[0].ddb_path
            for add_setting in mas_add_setting:
                client_group_obj.add_additional_setting(category=add_setting.category,
                                                        key_name=add_setting.key_name,
                                                        data_type=add_setting.data_type,
                                                        value=ddb_path)
                self.log.info(f"Additional settings with name [{add_setting.key_name}] created successfully")

        elif client_group_name.endswith(cs.MAS_UNIX_CLIENT_GROUP_NAME):
            self.log.info("This is Media Agent Unix Client group. "
                          "Proceeding with creating additional settings at CG level")
            mas_add_setting = _AD_SETTING_CONFIG.mas_clients
            ddb_path = _RING_CONFIG.media_agents[0].ddb_path_unix
            for add_setting in mas_add_setting:
                client_group_obj.add_additional_setting(category=add_setting.category,
                                                        key_name=add_setting.key_name,
                                                        data_type=add_setting.data_type,
                                                        value=ddb_path)
                self.log.info(f"Additional settings with name [{add_setting.key_name}] created successfully")
