# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Decorator file containing decorators for Salesforce methods

SalesforceAPICall is the only class defined in this file

SalesforceAPICall: Decorator for methods making an API call to Salesforce

SalesforceAPICall:
    __init__()          :   Initializes decorator class

    __call__()          :   Wrapper method

    Properties:

        *sf_connector      :   The SalesforceConnector object for which this decorator will be used

"""
import datetime
from functools import wraps
from requests.exceptions import ConnectionError
from AutomationUtils import logger
from .constants import SALESFORCE_PARAMS


class SalesforceAPICall:
    """Class for handling timeout of Salesforce API connection"""

    def __init__(self, timeout_delta=datetime.timedelta(hours=2)):
        """
        Constructor function for the class

        Args:
            timeout_delta (datetime.timedelta): timedelta for how long to wait before redoing login to Salesforce
                                                (Default 2h)
        """
        self.__timeout_delta = timeout_delta
        self.__timestamp = None
        self.__sf_connector = None
        self.__exp = None
        self.log = logger.get_log()

    @property
    def sf_connector(self):
        """
        Get sf_connector

        Returns:
            SalesforceConnector:
        """
        return self.__sf_connector

    @sf_connector.setter
    def sf_connector(self, sf_connector):
        """
        Sets sf_connector

        Returns:
            None
        """
        self.__sf_connector = sf_connector
        self.__timestamp = datetime.datetime.now()
        self.__sf_connector.reconnect()

    def __call__(self, out_of_place=False, max_retries=5):
        """
        Wrapper method that checks if Salesforce connection has timed out and attempts to reconnect before calling func

        Args:
            out_of_place (bool): Whether to allow out of place execution on a different Salesforce organization or not
            max_retries (int): Number of times to retry in case of Timeout

        Returns:
            function: The wrapped function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if out_of_place and any(param in kwargs for param in SALESFORCE_PARAMS):
                    self.sf_connector.reconnect(**kwargs)
                elif (current_time := datetime.datetime.now()) > self.__timestamp + self.__timeout_delta:
                    self.log.info(f"Salesforce API timeout. Last API call was at {self.__timestamp}.")
                    self.log.info("Attempting to reconnect to Salesforce.")
                    self.__sf_connector.reconnect()
                    self.__timestamp = current_time
                try:
                    for i in range(max_retries):
                        try:
                            return_val = func(*args, **kwargs)
                            break
                        except ConnectionError as exp:
                            self.__exp = exp
                            self.log.error(f"{exp}")
                            self.log.info(f"Tried {i + 1} times out of {max_retries}. Retrying....")
                    else:
                        raise Exception(f"Salesforce timeout error. Tried {max_retries} times and failed.") \
                            from self.__exp
                finally:
                    if out_of_place and any(param in kwargs for param in SALESFORCE_PARAMS):
                        self.sf_connector.reconnect()
                        self.__timestamp = datetime.datetime.now()
                return return_val
            return wrapper
        return decorator
