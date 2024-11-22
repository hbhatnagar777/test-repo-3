# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""helper class for Media Agent related operations in a Metallic Ring

    MediaAgentRingHelper:

        __init__()                              --  Initializes Media Agent Ring Helper

        start_task                              --  Starts the media agent helper task for ring configuration

        update_mm_config                        --  Updates the media agent configuration settings in the table

"""
from AutomationUtils.config import get_config
from MetallicRing.Core.db_helper import DBQueryHelper
from MetallicRing.Helpers.base_helper import BaseRingHelper
from MetallicRing.Utils import Constants as cs

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring


class MediaAgentRingHelper(BaseRingHelper):
    """ helper class for Media Agent related operations in a Metallic Ring"""

    def __init__(self, ring_commcell):
        super().__init__(ring_commcell)
        self.db_helper = DBQueryHelper(ring_commcell)

    def start_task(self):
        """
        Starts the media agent helper task for ring configuration
        """
        try:
            self.log.info("Starting media agent task")
            self.update_mm_config()
            self.log.info("All media agent tasks completed. Status - Passed")
            self.status = cs.PASSED
        except Exception as exp:
            self.message = f"Failed to execute media agent helper. Exception - [{exp}]"
            self.log.info(self.message)
        return self.status, self.message

    def update_mm_config(self):
        """
        Updates the media agent configuration settings in the table
        Raises:
            Exception when response is not success
        """
        self.log.info("setting the MMCONFIG_INFINI_STORE_MAX_PATITIONS_ON_MA value in mmconfigs table")
        mm_config = _CONFIG.mm_configs[0]
        qscript = f"-sn setConfigParam -si {mm_config.param} -si {mm_config.value} " \
                  f"-si {_CONFIG.mm_configs_auth_code} -si {mm_config.min} -si {mm_config.max}"
        response = self.commcell._qoperation_execscript(qscript)
        self.log.info(f"Update MM config table. Response - [{response}]")
        error = response.get('CVGui_GenericResp', {}).get('@errorCode', 0)
        if error != 0:
            raise Exception("Failed to set MM Config")
