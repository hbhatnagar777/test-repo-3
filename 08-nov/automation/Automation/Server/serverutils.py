# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file containing generic utilities for Server Team not tied to Commserve operations """

import os

from AutomationUtils import constants
from AutomationUtils.config import get_config


def get_logmonitoring_config():
    """Gets the log monitoring configuration"""
    return get_config(
        json_path=os.path.join(
            constants.AUTOMATION_DIRECTORY,
            "Server",
            "logmonitoring_config.json"
        )
    )
