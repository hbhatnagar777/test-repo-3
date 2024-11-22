# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" helper class for managing Smart Folders in Metallic Ring

    SmartFolderRingHelper:

        __init__()                              --  Initializes client group folder Ring Helper

        start_task                              --  Starts the smart folder configuration task

        create_smart_folder                     --  Creates a smart folder in the commcell

        delete_folder                           --  Deletes a smart client group folder in the commcell
"""

from AutomationUtils.config import get_config
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.SMART_FOLDER_CONFIG_FILE_PATH)
_RING_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class SmartFolderHelper(BaseRingHelper):
    """ helper class for managing Client Groups in Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)

    def start_task(self):
        """
        Starts the smart folder configuration task
        """
        try:
            self.log.info("Starting smart folder helper task")
            smart_folders = _CONFIG.smart_folders
            manual_folders = _CONFIG.manual_smart_folder
            for smart_folder in smart_folders:
                self.log.info(f"Creating smart folder - [{smart_folder.folder_name}]")
                self.create_smart_folder(smart_folder.folder_name, smart_folder.filter_type, smart_folder.filter_value)
            for manual_folder in manual_folders:
                self.log.info(f"Creating folder with name - [{manual_folder.folder_name}]")
                self.create_manual_folder(manual_folder.folder_name, manual_folder.filter_value)
            self.log.info("Smart folder tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute Smart folder helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def create_smart_folder(self, folder_name, filter_type, value):
        """ Creates a smart client group folder in the commcell
                Args:
                    folder_name(str)    --  Name of the client group to be created
                    filter_type(int)    --  Dict of smart client rule list
                    value(str)          --  Scope of the client group
                Returns:
                    None:
        """
        self.log.info(f"Request received to create smart folder - [{folder_name}]"
                      f"Filter Type - [{filter_type}] and filter valure - [{value}]")
        q_cmd = "qoperation execute"
        smart_folder_xml = cs.SMART_FOLDER_XML % (folder_name, filter_type, value)
        self.commcell.execute_qcommand_v2(q_cmd, smart_folder_xml)
        self.log.info(f"Smart folder [{folder_name}] created")

    def create_manual_folder(self, folder_name, client_groups):
        """ Creates a smart client group folder in the commcell
                Args:
                    folder_name(str)    --  Name of the client group to be created
                    client_groups(list) --  List of client group names
                Returns:
                    None:
        """
        self.log.info(f"Request received to create smart folder - [{folder_name}]"
                      f"filter values - [{client_groups}]")
        q_cmd = "qoperation execute"
        associations = []
        for client_group in client_groups:
            associations.append(f"<associations _type_='28' clientGroupName='{client_group}'/>")
        smart_folder_xml = cs.MANUAL_FOLDER_XML % (folder_name, associations)
        self.commcell.execute_qcommand_v2(q_cmd, smart_folder_xml)
        self.log.info(f"Smart folder [{folder_name}] created")

    def delete_folder(self, folder_name):
        """ Deletes a smart client group folder in the commcell
                Args:
                    folder_name(str)    --  Name of the folder to be deleted
                Returns:
                    None:
        """
        self.log.info(f"Request received to delete folder - [{folder_name}]")
        q_cmd = "qoperation execute"
        smart_folder_xml = cs.DELETE_FOLDER_XML % folder_name
        self.commcell.execute_qcommand(q_cmd, smart_folder_xml)
        self.log.info(f"Smart folder [{folder_name}] deleted")
