# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Class to control and manage the anomalies on the Commvault environment.

CVAnomalyManagement:
    Factory class to return the anomaly handlers.
"""

from .anomalies.client_anomaly import ClientAnomaly
from .anomalies.media_agent_anomaly import MediaAgentAnomaly
from .anomalies.indexing_anomaly import IndexingAnomaly


class CVAnomalyManagement(object):
    """A singleton class to get the handlers of different types of
        anomalies that has to be managed on the Commvault.

        Since this is a singleton class, all the instances would return the same
        instance.

        Usage:
            media_agent_anomaly = CVAnomalyManagement().get_anomaly_handler(
                'media_agent'
            )

            client_anomaly = CVAnomalyManagement().get_anomaly_handler(
                'client'
            )

            IndexingAnomaly = CVAnomalyManagement().get_anomaly_handler(
                'media_agent'
            )

    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Returns the instance of CVAnomalyManagement
        """
        if not isinstance(cls._instance, cls):
            cls._instance = super(CVAnomalyManagement, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self):
        """Initializes the anomaly management"""
        self._anomaly_types = {
            'media_agent': MediaAgentAnomaly,
            'client': ClientAnomaly,
            'indexing': IndexingAnomaly
        }

    def get_anomaly_handler(self, anomaly_type, **kwargs):
        """Creates the anomaly object and returns the anomaly handler

            Args:
                anomaly_type    (str)   - type of the anomaly handler to build

                kwargs          (dict)  - arguments that are to be passed to the anomaly handler

            Raises:
                Exception:
                    if provided anomaly type is not string

                    if invalid anomaly type name is provided

                    if anomaly type is not yet supported
        """
        if not isinstance(anomaly_type, str):
            raise Exception("Anomaly type should be an string.")

        anomaly_type = anomaly_type.lower()

        # check if provided anomaly type is valid
        if anomaly_type not in self._anomaly_types:
            raise Exception(f"Invalid anomaly type {anomaly_type} or not yet supported.")

        return self._anomaly_types.get(anomaly_type)(**kwargs)
