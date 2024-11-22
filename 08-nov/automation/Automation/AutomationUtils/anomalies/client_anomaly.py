# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Class to control and manage client anomalies on the Commvault environment.

ClientAnomaly:
    Anomaly handler class to inject or validate the anomalies on the commvault client.

ClientAnomaly
=============

    __init__()                  --  initializes the client anomaly class

    restart_cv_services()       --  restarts the commvault services on this client

ClientAnomaly Attributes
------------------------

    **client_object**           --  returns the cvpsdk client class object

	**machine_object**           --  returns the machine class object
"""


from .cvanomaly import CVAnomaly
from ..machine import Machine

from cvpysdk.client import Client


class ClientAnomaly(CVAnomaly):
    """Class to handle anomalies specific to client machines"""

    def __init__(self, **anomaly_options):
        """Initializes the client anomaly class

            Args:
                anomaly_options  (dict)  - key value pairs for the required anomaly options
                    commcell_object     (object)        - cvpysdk commcell class object

                    machine             (str/object)    - client machine name or machine class instance
                                                            or cvpysdk client class object

                    machine_user        (str)           - username for the client to connect to

                    machine_password    (str)           - password for the above specified user
        """
        super(ClientAnomaly, self).__init__(**anomaly_options)
        self._client_object = anomaly_options.get('client_object')

    @property
    def client_object(self):
        """Returns the cvpysdk Client class object"""
        if not self._client_object:
            if self._anomaly_options.get('client_name'):
                self._client_object = self._commcell_object.clients.get(self._anomaly_options.get('client_name'))
            else:
                raise Exception("Client object is not initialized.")

        return self._client_object

    @property
    def machine_object(self):
        """Returns the machine class instance"""
        if self._machine_object is None:
            client_object = None
            try:
                client_object = self.client_object
            except Exception:
                pass # will proceed and check if user has provided machine details
            
            if isinstance(client_object, Client):
                self._machine_object = Machine(self.client_object)
            else:
                super(ClientAnomaly, self).machine_object
            
        return self._machine_object

    def restart_cv_services(self):
        """Restarts the commvault services"""
        return self.client_object.restart_services()
