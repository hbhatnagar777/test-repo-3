# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Base class for all the anomalies on the Commvault environment.

CVAnomaly:
    Base Anomaly handler class to inject or validate the anomalies.

CVAnomaly
=========

    __init__()                  --  initializes the client anomaly class

    kill_process()              --  kills the services on the client

CVAnomaly Attributes
--------------------

    **machine_object**           --  returns the machine class object
    **commcell_object**           --  returns the commcell object
    **commserv**            --  returns the commserv client object
    **commserve_machine**           --  returns the commserv machine object

"""

from AutomationUtils import logger
from ..machine import Machine


class CVAnomaly:
    """Base class to for all the anomalies on the Commvault environment."""

    def __init__(self, **anomaly_options):
        """Initializes the base class for anomaly

            Args:
                anomaly_options  (dict)  - key value pairs for the required anomaly options
                    commcell_object     (object)        - cvpysdk commcell class object

                    machine             (str/object)    - client machine name or machine class instance
                                                            or cvpysdk client class object

                    machine_user        (str)           - username for the client to connect to

                    machine_password    (str)           - password for the above specified user
        """
        self._anomaly_options = anomaly_options
        self._commcell_object = anomaly_options.get('commcell_object')
        self._machine_object = None
        self._commserv = None
        self._commserv_machine = None
        self._log = logger.get_log()

    @property
    def log(self):
        """Returns the logger object"""
        return self._log

    @property
    def commcell_object(self):
        """Returns the commcell object"""
        return self._commcell_object

    @property
    def machine_object(self):
        """Returns the machine class instance"""
        if self._machine_object is None:
            if isinstance(self._anomaly_options.get('machine'), Machine):
                self._machine_object = self._anomaly_options.get('machine')
            else:
                self._machine_object = Machine(
                    self._anomaly_options.get('machine'), self._commcell_object,
                    self._anomaly_options.get('machine_user'), self._anomaly_options.get('machine_password')
                )

        return self._machine_object

    @property
    def commserv(self):
        """Returns the commserv client object"""
        if self._commserv is None:
            cs_name = self._commcell_object.commserv_name
            self._commserv = self._commcell_object.clients.get(cs_name)

        return self._commserv

    @property
    def commserve_machine(self):
        """Returns the commserv machine object"""
        if self._commserv_machine is None:
            self._commserv_machine = Machine(self.commserv)

        return self._commserv_machine

    def kill_process(self, process_name=None, process_id=None):
        """Kills the process running on the machine.

            Args:
                process_name    (str)   - kills the provided process name

                process_id      (int)   - kills the provided process id
        """
        return self.machine_object.kill_process(process_name, process_id)
