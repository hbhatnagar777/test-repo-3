# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    only one class is defined in this file
    MediaAgentAnomaly: Class to control and manage media agent
                        anomalies on the Commvault environment.

    The instance of this class can be used to induce various negative
    scenarios of the media agent associated with instance.

    1. killing sidb2 process
    2. taking down communications service
    3. taking down media mount manager service
    4. disabling media agent
    5. marking media agent offline for maintenance
    6. disabling library

     MediaAgentAnomaly
     =================

     __init__(arguments)    - initialises the object of MediaAgentAnomaly class with
                              keyword arguments supplied.

    kill_sidb_media_agent()     -- kills the sidb2 process on the MA associated with instance object

    kill_communications_media_agent()      -- kills the communication service of MA
                                                associated with instance object

    kill_media_mount_manager()     -- kills the media mount manager service on the MA
                                        associated with instance object

    enable_media_agent()   -- enables / disables the media agent associated with instance object

    offline_for_maintenance()  -- marks/unmarks for maintenance media agent
                                                    associated with instance object

    library_enable()     -- enables / disables the library on the MA

"""


from cvpysdk.storage import MediaAgent
from .client_anomaly import ClientAnomaly



class MediaAgentAnomaly(ClientAnomaly):
    """Class to handle anomalies specific to media agents machines"""

    def __init__(self, **anomaly_options):
        """Initializes the client anomaly class

            Args:
                anomaly_options  (dict)  - key value pairs for the required anomaly options

                commcell_object - object - of the commcell associated with the MA
                machine         - str    - name of the media agent

                machine_user        - str    - user name of media agent machine
                machine_password    - str    - password of the media agent machine

                        * username, password may be needed if changes done in
                        future which make ONLY media agent installed machine
                        not be part of clients of commcell.

        """
        super(MediaAgentAnomaly, self).__init__(**anomaly_options)
        self.media_agent_object = self._commcell_object.media_agents.get(self.machine_object.machine_name)
        self.cvpysdk_object = self._commcell_object._cvpysdk_object
        self.qoperation_execscript = self._commcell_object._qoperation_execscript
    # return or raise exception

    # killing processes

    def kill_sidb_media_agent(self):
        """kill the sidb2.exe process running on media agent"""
        if self._machine_object.is_process_running("sidb2"):
            result = self._machine_object.kill_process("sidb2")
        else:
            result = "sidb2 process is not running on {0}".format(
                self._machine_object.machine_name)
        return result

    def kill_communications_media_agent(self):
        """kills the cvd.exe process on media agent """
        # cvd. exe runs on all three cs.client,MA
        # deal with MA here, _machine_object is the MA object associated with current
        # instance of media_agent_anomaly
        if self._machine_object.is_process_running("cvd"):
            result = self._machine_object.kill_process("cvd")
        else:
            result = "cvd process is not running on MA {0}".format(
                self._machine_object.machine_name)
        return result

    def kill_media_mount_manager(self):
        """kills the CVMountd.exe process on media agent"""
        if self._machine_object.is_process_running("CVMountd"):
            result = self._machine_object.kill_process("CVMountd")
        else:
            result = "cvd process is not running on MA {0}".format(
                self._machine_object.machine_name)
        return result
    # offline scenarios

    def enable_media_agent(self, enable=True):
        """
        disable the media agent by change in media agent properties.
            Arguments
            enable          (bool)
                            True        - Enable the media agent
                            False       - Disable the media agent
            Returns
            "string depicting no error"     if success

            "exception"                     if failure
        """
        return self.media_agent_object.set_state(enable)

    def offline_for_maintenance(self, mark=False):
        """
        mark the media agent offline for maintenance
            Arguments
                mark        (bool)
                                        True    - mark the media agent for maintenance
                                        False   - UNMARK the media agent for maintenance

            Returns
            "string depicting no error"     if success

            "exception"                     if failure

        """
        return self.media_agent_object.mark_for_maintenance(mark)

    # server side POST request handling of q script execution not working;
    # escalated with server team
    # library disable may not at the moment

    def library_enable(self, library_name, enable):
        """to enable or disable a library (for all types of libraries)
            Arguments
                library         (str)       name of the library to be enabled/disabled

                enable          (bool)
                                True    -   it will enable the library

                                False   -   it will disable the library

            Returns
                "json object result of q command execution"
        """
        if not isinstance(library_name, str) or type(enable) != bool:
            raise Exception("input arguments format type incorrect, please check")

        if enable:
            command = "-sn setLibraryProperty -si {0} -si enablelibrary -si 1".format(
                library_name)
        else:
            command = "-sn setLibraryProperty -si {0} -si enablelibrary -si 0".format(
                library_name)
        result = self.qoperation_execscript(command)
        return result
