# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Class to control and manage media agent anomalies on the Commvault environment.

IndexingAnomaly:
    Anomaly handler class to inject or validate the anomalies on the commvault media agent.

IndexingAnomaly
=============

    __init__()                  --  initializes the client anomaly class

    kill_index_server()         --  Kills the IndexServer process running on media agent
    kill_fsindexedrestore()     --  Kills the FsIndexedRestore process running on media agent
    kill_synthfull()            --  Kills the synthfull process running on media agent
    kill_cvd()                  --  Kills the cvd process running on media agent
    kill_start_synthfull()      --  Kills the StartSynthfull process running on CS
    kill_cvjobreplicatorods()   --  Kills the CVJobReplicatorODS process on media agent
    kill_cvsynthfullods()       --  Kills the CVSynthFullODS process on media agent
    kill_archive_index()        --  Kills the archive index process on media agent
    delete_cvidxdb_temp()        -- Deletes the temp folder under cvidxdb folder
                                    from index cache on media agent

"""

from .media_agent_anomaly import MediaAgentAnomaly
from Indexing.helpers import IndexingHelpers
from AutomationUtils.machine import Machine


class IndexingAnomaly(MediaAgentAnomaly):
    """Class to handle anomalies specific to medai agents machines"""

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
        super(IndexingAnomaly, self).__init__(**anomaly_options)
        self.indexing_help = IndexingHelpers(self.commcell_object)

    def kill_index_server(self):
        """Kills the IndexServer process running on MA"""

        process_name = 'cvods' if self.machine_object.os_info == 'WINDOWS' else ' CVODS'
        return self.kill_process(process_name)

    def kill_fsindexedrestore(self):
        """Kills the FsIndexedRestore process running on MA"""

        return self.kill_process('FsIndexedRestore')

    def kill_synthfull(self):
        """Kills the synthfull process running on MA"""

        process_name = 'synthfull' if self.machine_object.os_info == 'WINDOWS' else ' SynthFull'
        return self.kill_process(process_name)

    def kill_cvd(self):
        """Kills the cvd process running on MA"""

        return self.kill_process('cvd')

    def kill_start_synthfull(self):
        """Kills the StartSynthfull process running on CS"""

        return self.commserve_machine.kill_process('IndexingService')

    def kill_cvjobreplicatorods(self):
        """Kills the CVJobReplicatorODS process on media agent"""

        process_name = 'cvods' if self.machine_object.os_info == 'WINDOWS' else ' CVODS'
        return self.kill_process(process_name)

    def kill_cvsynthfullods(self):
        """Kills the CVSynthFullODS process on media agent"""

        process_name = 'cvods' if self.machine_object.os_info == 'WINDOWS' else ' CVODS'
        return self.kill_process(process_name)

    def kill_archive_index(self):
        """Kills the archive index process on media agent"""

        process_name = 'cvods' if self.machine_object.os_info == 'WINDOWS' else ' CVODS'
        return self.kill_process(process_name)

    def delete_cvidxdb_temp(self):
        """Deletes the temp folder under cvidxdb folder
           from index cache on media agent

        Returns:
            True    -   if directory was removed successfully

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to remove the directory

        """

        index_cache = self.indexing_help.get_index_cache(self.client_object)
        self.log.info("Index cache is : {0} ".format(index_cache))
        machine_obj = Machine(self.client_object)
        temp_path = f"{index_cache}{machine_obj.os_sep}" \
                         f"CvIdxDB{machine_obj.os_sep}Temp"
        self.log.info("Temp folder path is: {0} ".format(temp_path))
        self.log.info("Removing temp path ")
        retcode = machine_obj.remove_directory(temp_path)
        self.log.info("Temp path removed successfully ")
        return retcode
