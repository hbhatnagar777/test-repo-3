# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing Index Server related operations in Metallic Ring

    IndexServerRingHelper:

        __init__()                      --  Initializes Index Server Helper

        start_task                      --  Starts the index server ring automation task

        create_index_server             --  Creates a new index server with the given name

        associate_plan                  --  Associates plan to index server for backup of index data

"""

from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs
from MetallicRing.Utils.ring_utils import RingUtils

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class IndexServerRingHelper(BaseRingHelper):
    """ helper class for performing Index Server related operations in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.index_servers = self.commcell.index_servers

    def start_task(self):
        """Starts the index server ring automation task"""
        try:
            index_servers = _CONFIG.index_servers
            self.log.info("Starting index server task")
            ring_id = RingUtils.get_ring_string(_CONFIG.id)
            for index, index_server in enumerate(index_servers):
                index_str = f"0{index + 1}" if len(str(index)) <= 1 else index + 1
                role = index_server.roles[0]
                role_dn_str = cs.role_name_dict.get(role, f"{role.replace(' ', '')}_is")
                is_client_name = f"{role_dn_str}{index_str}{ring_id}{index_server.region}"
                self.create_index_server(is_client_name,
                                         index_server.nodes, index_server.roles, index_server.index_directory)
                self.associate_plan(is_client_name, cs.CLOUD_SERVER_PLAN_NAME)
            self.log.info("All index server tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute index server helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_index_server(self, index_server_name, nodes, roles, directory):
        """ Creates a new index server with the given nodes and the role
                Args:
                    index_server_name(str)      --  Name of the index server to be created
                    nodes(list)                 --  List of nodes to be used by the index server
                    roles(list)                 --  List of roles to be supported by the index server
                    directory(list)             --  list of index locations for the index server
                                                    nodes respectively
                                For example:
                                        [<path_1>] - same index location for all the nodes
                                        [<path_1>, <path_2>, <path_3>] - different index
                                location for index server with 3 nodes
                Returns:
                    None:

                Raises:
                    Exception:
                        If index server with given name exists

        """
        if not self.index_servers.has(index_server_name):
            self.index_servers.create(index_server_name, nodes, directory, roles)
            self.log.info(f"Index server with name [{index_server_name}] created successfully")
        else:
            self.log.info(f"Index server with name [{index_server_name}] already exists")

    def associate_plan(self, index_server_name, plan_name):
        """ Associates plan to index server for backup of index data
                Args:
                    index_server_name(str)      --  Name of the index server
                    plan_name(str)    --  Name of the storage policy/plan to be associated
                Returns:
                    None:
                Raises:
                    Exception:
                        If index server with given name doesn't exists
                        if plan with given name doesn't exists

        """
        if not self.index_servers.has(index_server_name):
            raise Exception(f"Index server with given name [{index_server_name}] doesn't exist")
        if not self.commcell.plans.has_plan(plan_name):
            raise Exception(f"Storage policy with given name [{index_server_name}] doesn't exist")
        self.index_servers.get(index_server_name).change_plan(plan_name)
        self.log.info(f"Associated index server [{index_server_name}] with plan [{plan_name}]")
