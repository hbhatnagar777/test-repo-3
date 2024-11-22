# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for performing metrics related operations in Metallic Ring

    MetricsRingHelper:

        __init__()                              --  Initializes Metrics Ring Helper

        start_task                              --  Starts the metrics/master commcell helper
                                                    tasks for ring related operations

        register_remote_commcell                --  Registers a remote commcell to the metrics server

        unregister_remote_commcell              --  Un-Registers a registered service commcell from the metrics server

"""

from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class MetricsRingHelper(BaseRingHelper):
    """ helper class for performing metrics related operations in Metallic Ring"""

    def __init__(self, metrics_commcell):
        super().__init__(metrics_commcell)

    def start_task(self):
        """
        Starts the metrics/master commcell helper task for registering the ring commcell
        """
        try:
            self.log.info("Started Metrics helper task")
            commserv = _CONFIG.commserv
            if not self.commcell.is_commcell_registered(_CONFIG.name):
                if self.ring.container_provision is True:
                    cs_clientname = commserv.client_name
                    cs_gateway_name = commserv.hostname.replace(cs_clientname, f"{cs_clientname}gateway")
                    self.register_remote_commcell(cs_gateway_name, commserv.new_username, commserv.new_password)
                else:
                    self.register_remote_commcell(commserv.hostname, commserv.new_username, commserv.new_password)
            else:
                self.log.info("Commcell is already registerd to metrics commcell")
            self.log.info("All Metrics tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute metrics helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def register_remote_commcell(self, commcell_name, user_name, password, registered_for_routing=True):
        """
        Registers a remote commcell to the metrics server
        Args:
            commcell_name(str)              -   name of the commcell to be registered
            user_name(str)                  -   username of the commcell
            password(str)                   -   password of the commcell
            registered_for_routing(bool)    -   routing option
        """
        self.log.info(f"Attempting to register Commcell [{commcell_name}] to master commcell "
                      f"[{self.commcell.commserv_name}]")
        self.commcell.register_commcell(commcell_name, registered_for_routing, user_name, password)
        self.log.info(f"Commcell [{commcell_name}] is registered to master commcell "
                      f"[{self.commcell.commserv_name}]")

    def unregister_remote_commcell(self, commcell_name):
        """
        Un-Registers a registered service commcell from the master commcell
        Args:
            commcell_name(str)              -   name of the commcell to be unregistered
        """
        self.log.info(f"Attempting to unregister Commcell [{commcell_name}] to master commcell "
                      f"[{self.commcell.commserv_name}]")
        self.commcell.unregister_commcell(commcell_name, force=True)
        self.log.info(f"Commcell [{commcell_name}] is unregistered from the master commcell "
                      f"[{self.commcell.commserv_name}]")
