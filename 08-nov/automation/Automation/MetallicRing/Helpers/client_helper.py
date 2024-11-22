# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for managing Clients in Metallic Ring

    ClientRingHelper:

        __init__()                              --  Initializes client ring Helper

        start_task                              --  Starts the client configuration task

        add_additional_settings                 --  sets additional settings in the client

"""

from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_AD_SETTING_CONFIG = get_config(json_path=cs.ADDITIONAL_SETTING_CONFIG_FILE_PATH)


class ClientRingHelper(BaseRingHelper):
    """ helper class for managing Clients in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.clients = self.commcell.clients
        self.client_groups = self.commcell.client_groups

    def start_task(self):
        """
        Starts the client configuration task
        """
        try:
            self.log.info("Starting client tasks")
            if not self.commcell.client_groups.has_clientgroup(cs.INFRA_CLIENT_GROUP_NAME):
                raise Exception(f"Client group with given name [{cs.INFRA_CLIENT_GROUP_NAME}] doesn't exist")
            client_group_obj = self.commcell.client_groups.get(cs.INFRA_CLIENT_GROUP_NAME)
            all_clients_add_setting = _AD_SETTING_CONFIG.all_clients
            for add_setting in all_clients_add_setting:
                client_group_obj.add_additional_setting(category=add_setting.category,
                                                        key_name=add_setting.key_name,
                                                        data_type=add_setting.data_type,
                                                        value=add_setting.value)
            mas = _CONFIG.media_agents
            for media_agent in mas:
                if media_agent.region == cs.REGION_EASTUS2_CODE:
                    self.region_helper.edit_region_of_entity(entity_type=cs.ENTITY_TYPE_CLIENT_STR,
                                                             entity_name=media_agent.client_name,
                                                             entity_region_type=cs.REGION_TYPE_WORKLOAD,
                                                             region_name=cs.REGION_EASTUS2)
                    self.log.info(f"Media Agent's [{media_agent.client_name}] region set to [{cs.REGION_EASTUS2}]")
            self.log.info("All client tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute client helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def add_additional_settings(self, client_name, additional_setting_dict):
        """ Adds additional settings on the given client name
                Args:
                    client_name(str)                --  Name of the client
                    additional_setting_dict(dict)  --  Additional setting to be set on the client
                        Example     --  {"category":"EventManager",
                                        "key_name":"Test",
                                        "data_type":"Boolean",
                                        "value":"Test"}
                Returns:
                    None:

                Raises:
                    Exception:
                        If client group with given name exist

        """
        self.log.info(f"Request received to create additional setting on the following client - [{client_name}]")
        if not self.clients.has_client(client_name):
            raise Exception(f"Client with name {client_name} does not exists")
        client = self.clients.get(client_name)
        client.add_additional_setting(category=additional_setting_dict["category"],
                                      key_name=additional_setting_dict["key_name"],
                                      data_type=additional_setting_dict["data_type"],
                                      value=additional_setting_dict["value"])
        self.log.info(f"Additional settings with name {additional_setting_dict['key_name']} created successfully")
