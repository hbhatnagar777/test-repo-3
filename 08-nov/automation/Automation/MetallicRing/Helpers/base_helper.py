# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Base Helper class for metallic ring helpers classes

    BaseRingHelper:

        __init__()                      --  Initializes Base Ring Helper

"""

from AutomationUtils import logger
from AutomationUtils.config import get_config
from MetallicRing.Utils import Constants as cs
from Server.regions_helper import RegionsHelper

_CONFIG = get_config(json_path=cs.METALLIC_CONFIG_FILE_PATH)


class BaseRingHelper:
    """ Base Helper class for metallic ring helpers classes """

    def __init__(self, ring_commcell):
        """Initialized the base ring helper"""
        self.commcell = ring_commcell
        self.ring = _CONFIG.Metallic.ring
        self.log = logger.get_log()
        self.status = cs.FAILED
        self.is_linux_cs = False
        self.message = None
        if self.commcell is not None:
            self.region_helper = RegionsHelper(self.commcell)
            self.users = self.commcell.users
            self.is_linux_cs = self.commcell.is_linux_commserv
        if self.is_linux_cs is None:
            self.is_linux_cs = True

