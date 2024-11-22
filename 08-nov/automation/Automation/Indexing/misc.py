# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Miscellaneous indexing related helper functions and classes goes in this file"""

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.database_helper import CommServDatabase

from cvpysdk.commcell import Commcell


class MetallicConfig:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, commcell):
        """Initializes the object"""

        self.log = logger.get_log()

        config = get_config()
        self.is_metallic = False
        self.is_configured = False
        self.admin_username = None
        self.admin_password = None
        self.commcell = commcell
        self.metallic_admin_cc = None
        self.csdb = None

        if hasattr(config, 'Indexing') and hasattr(config.Indexing, 'is_metallic'):
            self.is_metallic = config.Indexing.is_metallic
            self.admin_username = config.Indexing.metallic.admin_username
            self.admin_password = config.Indexing.metallic.admin_password

        if self.is_metallic and self.admin_username and self.admin_password:
            self.log.info('Creating metallic admin commcell object')
            self.metallic_admin_cc = Commcell(
                webconsole_hostname=self.commcell.webconsole_hostname,
                commcell_username=self.admin_username,
                commcell_password=self.admin_password
            )
            self.log.info('Creating metallic database object')
            self.csdb = CommServDatabase(self.metallic_admin_cc)

            self.is_configured = True
