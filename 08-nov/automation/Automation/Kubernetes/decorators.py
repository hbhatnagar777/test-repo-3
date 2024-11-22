# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Decorator file containing decorators for Kubernetes methods

DebugSkip:
    __init__()          :   Initializes decorator class

    __call__()          :   Wrapper method

"""

from functools import wraps
from AutomationUtils import logger, config

automation_config = config.get_config().Kubernetes


class DebugSkip:
    """Class for decorating Kubernetes functions to skip cleanup for debugging"""

    def __init__(self):
        """
        Constructor function for the class

        Args:
        """
        self.__debug_flag = automation_config.DEBUG_MODE
        self.log = logger.get_log()

    def __call__(self, func):
        """
        Wrapper method that skips cleanup of resources if debug mode is set

        Returns:
            function: The wrapped function
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.__debug_flag:
                return func(*args, **kwargs)
            self.log.info(f"Debug mode is active. Skipping cleanup being performed by method [{func.__name__}]")
        return wrapper

