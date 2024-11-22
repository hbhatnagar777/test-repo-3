# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module is a helper class that provides the functions or operations that
can be used to run basic operations on Media Agent page in Command Center

Class MediaAgentHelper:
    move_ddb_path() -- method to perform DDB move operation for provided path

    create_ddb_disk() -- method to create DDB disk for provided path

    get_num_partitions_for_path() -- Get the number of partitions from DDB partition table for provided path

    fill_ma_details_and_submit() -- This fills the given MA details in the given Add/Install MA dialog and then submits it

    install_media_agent() -- This installs MediaAgent on the given clients and returns the job id of the installation job

    retire_media_agents() -- This method retires all the media agents with given names

    add_ma_role() -- Function will navigate to servers page and then add MA role to the given server.
"""

import time
from Web.AdminConsole.AdminConsolePages.media_agents import MediaAgents
from Web.AdminConsole.Infrastructure.MediaAgentDetails import MediaAgentDetails
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from AutomationUtils import logger

class MediaAgentHelper:
    """ Admin console helper for Media Agent related pages """

    def __init__(self, admin_console):
        """
        Helper for media agent related files

        Args:
            admin_console   (AdminConsole)    --  AdminConsole class object
        """
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__mediaAgent = MediaAgents(self.__admin_console)
        self.__mediaAgentDetails = MediaAgentDetails(self.__admin_console)
        self.__servers = Servers(self.__admin_console)
        self.log = logger.get_log()

    def move_ddb_path(self,
                      source_ma,
                      destination_ma,
                      source_path,
                      dest_path):
        """
        Method to perform DDB move operation for provided path

        Args:
            source_ma (str)      :   source media agent
            destination_ma(str)  :   destination media agent
            source_path (str)    :   source path to move
            dest_path (str)      :   destination path to move to

        """
        self.__navigator.navigate_to_media_agents()
        self.__mediaAgent.access_media_agent(source_ma)
        self.__mediaAgentDetails.move_ddb(dest_ma=destination_ma,
                                          source_path=source_path,
                                          dest_path=dest_path)
        self.log.info("Successfully submitted move DDB job")


    def create_ddb_disk(self,
                        source_ma,
                        source_path):
        """
        Method to create DDB Disk for provided path
        Args:
            source_ma (str)      :   source media agent
            source_path (str)    :   source path to move
        """
        self.__navigator.navigate_to_media_agents()
        self.__mediaAgent.access_media_agent(source_ma)
        self.__mediaAgentDetails.create_ddb_disk(source_path=source_path)
        self.log.info("Successfully created ddb disk")


    def get_num_partitions_for_path(self, ma, path):
        """
        Method to get number of partitions for provided path

        Args:
            ma (str)      :   source media agent
            path (str)     :   source path to move

        Return:
            num_partitions : the number of partitions on the given path
        """
        self.__navigator.navigate_to_media_agents()
        self.__mediaAgent.access_media_agent(ma)
        self.log.info(f"Getting number of partitions in path: {path} ")
        num_partitions = self.__mediaAgentDetails.get_num_partitions_for_path(path)
        return num_partitions
    
    def fill_ma_details_and_submit(self,r_modal_dialog,hostnames,os_type,username = None,password = None,saved_credential_name = None,**kwargs):
        """
        This fills the given MA details in the given Add/Install MA dialog and then submits it

        This works on any page where Add/Install MA Dialog is opened

        Args:
            r_modal_dialog (RModalDialog)  --  RModalDialog object of the Add/Install MA Dialog

            hostnames (list(str))  --  hostnames of the media agent machine

            username (str | None)       --  username of the media agent machine , default is None

            password (str | None)       --  password of the media agent machine , default is None

            os_type (str)        --  os type of the media agent machine , values can be "windows","linux","unix"

            saved_credential_name (str | None) --  saved credential name , default is None

            Available kwargs Options:

                software_cache (str) --  software cache client name , default is None

                port_number (int)    --  port number , default is 22

                install_location (str)    --  installation location

                reboot_if_required (bool) --  reboot if required , default is False

        Returns: 
            job id of the installation job
        """

        return self.__mediaAgent._fill_ma_details_and_submit(r_modal_dialog,hostnames,os_type,username,password,saved_credential_name,**kwargs)
    
    def install_media_agent(self,hostnames,os_type,username = None,password = None,saved_credential_name = None,**kwargs):
        """
        This installs MediaAgent on the given clients and returns the job id of the installation job

        Navigates to Media Agent Page and opens the Add MA dialog then fills the MA details and submits it 

        Args:
            hostnames (list(str))  --  hostnames of the media agent machine

            username (str | None)       --  username of the media agent machine , default is None

            password (str | None)       --  password of the media agent machine , default is None

            os_type (str)        --  os type of the media agent machine , values can be "windows","linux","unix"

            saved_credential_name (str | None) --  saved credential name , default is None

            Available kwargs Options:

                software_cache (str) --  software cache client name , default is None

                port_number (int)    --  port number , default is 22

                install_location (str)    --  installation location

                reboot_if_required (bool) --  reboot if required , default is False

        Returns: 
            job id of the installation job
        """

        self.__navigator.navigate_to_media_agents()
        self.log.info("Starting Media Agent Installation on given clients")
        job_id = self.__mediaAgent.install_media_agent(hostnames,os_type,username,password,saved_credential_name,**kwargs)
        self.log.info(f"Started Media Agent Installation job, job id : [{job_id}]")
        return job_id
    
    def _close_popup_if_present(self):
        """Close popup if present"""

        # admin_console.close_popup() closes popup if present, but sometimes during fadeoff it's click can be intercepted
        # popup can fade off and click can be intercepted so it is in try block
        try:
            self.__admin_console.close_popup()
        except Exception as e:
            self.log.info(e)
    
    def retire_media_agents(self,ma_names):
        """
        This method retires all the media agents with given names

        Args:
            ma_names (list(str))  :  list of media agent names to retire

        Raises:

            Exception:  if media agent does not exist
        """

        self.__navigator.navigate_to_media_agents()

        # in case when you were already on a particular page and then navigating to that page again won't reload the data, so we explicitly reload the data
        self.__mediaAgent.reload_data()
        self.log.info("reloaded the table data")

        for ma_name in ma_names:
            if not self.__mediaAgent.is_media_agent_exists(ma_name):
                raise Exception(f"Media Agent [{ma_name}] does not exist")
            
            self.log.info(f"Retiring media agent [{ma_name}]")
            self.__mediaAgent.retire_media_agent(ma_name)
            self.log.info(f"Successfully retired media agent [{ma_name}]")
            # we close the popup so that it does not intercept the search in is_media_agent_exists()
            self._close_popup_if_present()

    def add_ma_role(self,server_names,wait_time_for_table_reload=0):
        """
        Function will navigate to servers page and then add MA role to the given server.

        Args:
            server_names (list(str))          --  Name of the server to which MA role needs to be added

            wait_time_for_table_reload (int) --  Time to wait before refreshing the table if 0 then won't refresh, default is 0
        """

        self.__navigator.navigate_to_servers()

        # we might need to reload the data so that it reflects the latest data otherwise causes issues
        # the issue is caused when server is still marked as infrastructure even though MA role was already removed. 
        if wait_time_for_table_reload > 0:
            self.log.info(f"Waiting for {wait_time_for_table_reload} seconds to reload the table")
            time.sleep(wait_time_for_table_reload)
            self.__servers.reload_data()
            self.log.info("reloaded the table data")

            for server_name in server_names:            
                self.log.info(f"Adding MA role to [{server_name}]")
                self.__servers.add_ma_role(server_name)
                self.log.info(f"Successfully added MA role to [{server_name}]")
                # we close the popup so that it does not intercept the search in is_client_exists()
                self._close_popup_if_present()