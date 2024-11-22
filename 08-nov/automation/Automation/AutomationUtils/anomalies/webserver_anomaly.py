# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Class to control and manage Webserver anomalies on the Commvault environment.
"""

from .client_anomaly import ClientAnomaly


class WebserverAnomaly(ClientAnomaly):
    """Class to handle anomalies specific to the Webserver machines"""

    def __init__(self, **anomaly_options):
        """Initializes the client anomaly class

            Args:
                commcell_object (object) --     The Commcell object to which the Webserver client belongs to.
                client_name     (str)    --     Webserver client name.
        """
        super(WebserverAnomaly, self).__init__(**anomaly_options)

    def stop_tomcat(self):
        """Stops the tomcat process running and belonging to the Webserver"""
        return self.client_object.stop_service("GxTomcatInstance001")

    def stop_iis(self):
        """Stops IIS service on the Webserver"""
        command = "net stop was /y"
        self.client_object.execute_command(command)

    def start_iis(self):
        """Starts IIS service on the Webserver"""
        command = "net start W3SVC"
        self.client_object.execute_command(command)

    def start_tomcat(self):
        """Starts the tomcat process on the Webserver"""
        return self.client_object.start_service("GxTomcatInstance001")
