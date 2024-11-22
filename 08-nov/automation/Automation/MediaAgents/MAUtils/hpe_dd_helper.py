# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""This file contains classes named HPEHelper which consists of
 methods required for MM testcase assistance creating HPE Store libraries, etc.

 -- DDBoost API changes are to be added to the same file.

Class HPEHelper:
    configure_hpe_library()                     --  configure a new hpe catalyst library.
    create_secondary_copy()                     --  create a secondary non dedupe storage policy copy for HPE GDSP. ** For HPE we dont support deduplication.
"""
from AutomationUtils import logger
from MediaAgents import mediaagentconstants

class HPEHelper:
    def __init__(self, test_case_obj):
        self.tcinputs = test_case_obj.tcinputs
        self.commcell = test_case_obj.commcell
        self._log = logger.get_log()

    def configure_hpe_library(self, library_name, media_agent, store_name, host, username, password='', server_type='hpe store'):
        """
        Adds a new HPE Catalyst Library to the Commcell.

            Args:
                library_name (str)        --  name of the new HPE library to add

                media_agent  (str/object) --  name or instance of media agent to add the library to

                store_name   (str)        --  cloud bucket/store to be used.

                username     (str)        --  username to access mountpath

                password     (str)        --  password to access the mount path

                server_type   (str)       --  provide cloud library server type

            Returns:
                object - instance of the disk library class, if created successfully
        """
        server_type_dict = mediaagentconstants.CLOUD_SERVER_TYPES
        if not server_type.lower() in server_type_dict:
            raise Exception('Invalid server type specified')
        server_type = server_type_dict[server_type.lower()]
        self._log.info("check library: %s", library_name)
        if not self.commcell.disk_libraries.has_library(library_name):
            self._log.info("adding Library...")
            username = f"{host}//{username}"
            cloud_library = self.commcell.disk_libraries.add(library_name, media_agent, store_name, username, password,
                                                             server_type)
            self._log.info("Library Config done.")
            return cloud_library
        cloud_library = self.commcell.disk_libraries.get(library_name)
        self._log.info("Library exists!")
        return cloud_library

    def create_secondary_copy(self, copy_name, storage_policy_name, media_agent_name, storage_pool_name):
        """
        Creates a non-dedupe secondary storage policy copy.
        ** For HPE we dont support deduplication

            Args:
                copy_name (str)                  --  name of the storage policy copy.
                storage_policy_name (str)        --  storage policy name.
                global_pool_name (str)           --  global policy name.

            Returns:
                (object)                         -- storage policy copy object
        """
        storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        if not storage_policy.has_copy(copy_name):
            self._log.info(f"Adding a new synchronous secondary copy: {copy_name}")
            storage_policy.create_secondary_copy(
                copy_name=copy_name,
                media_agent_name=media_agent_name,
                global_policy=storage_pool_name
            )
            self._log.info("Secondary Copy has been created")
            storage_policy.refresh()
        else:   
            self._log.info("Storage PolicyCopy Exists!")
        return storage_policy.get_copy(copy_name)
