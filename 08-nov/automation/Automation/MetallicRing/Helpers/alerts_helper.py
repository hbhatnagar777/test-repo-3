# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for managing Alerts in Metallic Ring

    AlertRingHelper:

        __init__()                              --  Initializes Alert Ring Helper

        start_task                              --  Starts the alert ring helper task

        create_alert                            --  Creates alert in the ring commcell

        enable_alert                            --  Enables alert in the ring commcell

        disable_alert                           --  Disables alert in the ring commcell

"""
import copy
from AutomationUtils import constants as alert_cs
from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.ALERT_CONFIG_FILE_PATH)
_COMMSERV_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring.commserv


class AlertRingHelper(BaseRingHelper):
    """ contains helper class for managing alerts in the ring commcell"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.alerts = self.commcell.alerts

    def start_task(self):
        """Starts the alert helper task for ring configuration"""
        try:
            self.log.info("Starting alert task")
            alerts = _CONFIG.alerts
            if not _CONFIG.is_alert_json:
                for alert in alerts:
                    self.log.info(f"Request received to create alert [{alert.alert_name}]")
                    alert_type = alert_cs.ALERT_CATEGORY_TYPE.get(alert.category, {}).get(alert.type, 0)
                    if alert_type == 0:
                        self.log.info(f"Alert with name [{alert.alert_name}] creation failed since the alert type is "
                                      "missing")
                        continue
                    alert_req = copy.deepcopy(cs.ALERT_CREATE_REQUEST)
                    self.log.info(f"Forming alert request - [{alert.alert_name}]")
                    alert_req["alert_type"] = alert_type
                    alert_req["alert_name"] = alert.alert_name
                    alert_req["users"] = [_COMMSERV_CONFIG.new_username]
                    if alert.monitoring_nodes == cs.ALERT_ENTITY_TYPE_MA:
                        mas = []
                        for media_agent in self.commcell.media_agents.all_media_agents:
                            mas.append(media_agent)
                        entities = {
                            "media_agents": mas
                        }
                    elif alert.monitoring_nodes == cs.ALERT_ENTITY_TYPE_ALL:
                        entities = {
                            "entity_type_names": ["ALL_CLIENT_GROUPS_ENTITY", "ALL_CLIENTS"]
                        }
                    else:
                        entities = {
                            "client_groups": alert.monitoring_nodes
                        }
                    alert_req["entities"] = entities
                    alert_req["nonGalaxyList"]["nonGalaxyUserList"][0]["nonGalaxyUser"] = \
                        _COMMSERV_CONFIG.alert_notification_email
                    for criteria in alert.alert_criteria:
                        if cs.ALERT_CRITERIA.get(criteria, 0) != 0:
                            alert_req["criteria"] = cs.ALERT_CRITERIA.get(criteria, 0)
                            alert_req["alert_name"] = f"{alert.alert_name} - {criteria}"
                            self.log.info(f"Alert request - [{alert_req}]")
                            self.create_alert(alert_req["alert_name"], alert_req)
                            self.log.info(f"Alert - [{alert.alert_name}] created successfully")
            else:
                for alert in alerts:
                    self.log.info(f"Alert request JSON- [{alert}]")
                    self.create_alert(alert.alert_name, alert)
                    self.log.info(f"Alert - [{alert.alert_name}] created successfully")
            self.log.info("All alert tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute alert helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_alert(self, alert_name, alert_dict):
        """
        Creates an alert with given name and definition
        Args:
            alert_name      -   Name of the alert
            alert_dict      -   Alert definition to be used for creation
        """
        self.log.info(f"Request received to created alert - [{alert_name}]")
        if not self.commcell.alerts.has_alert(alert_name):
            self.alerts.create_alert(alert_dict)
            self.log.info(f"Alert [{alert_name}] created")
        else:
            self.log.info(f"Alert [{alert_name}] already exists")

    def enable_alert(self, alert_name):
        """
        Enables the alert with a given name
        Args:
            alert_name      -   Name of the alert ot be enabled

        Return:
            bool    -   True if alert is enabled
                        False if alert is not enabled
        """
        self.log.info(f"Enabling alert with name - [{alert_name}]")
        if self.commcell.alerts.has_alert(alert_name):
            alert = self.commcell.alerts.get(alert_name)
            alert.enable()
            self.log.info(f"Enabled alert with name - [{alert_name}]")
            return True
        self.log.info(f"Alert with name - [{alert_name}] is not present in the Commcell")
        return False

    def disable_alert(self, alert_name):
        """
        Disables the alert with a given name
        Args:
            alert_name      -   Name of the alert ot be disabled

        Return:
            bool    -   True if alert is disabled
                        False if alert is not disabled
        """
        self.log.info(f"Disabling alert with name - [{alert_name}]")
        if self.commcell.alerts.has_alert(alert_name):
            alert = self.commcell.alerts.get(alert_name)
            alert.disable()
            self.log.info(f"Disabled alert with name - [{alert_name}]")
            return True
        self.log.info(f"Alert with name - [{alert_name}] does not exist")
        return False
