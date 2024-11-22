# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""

Validator Class for Access Token Functionalities

AccessTokenValidator():
    validate_expiry_time()               : validates the access token after expiry time
    validate_scope()                     : validates the scope of access token
"""

import datetime
import json
import time
import selenium.common.exceptions
from cvpysdk.exception import SDKException
from Web.AdminConsole.AdminConsolePages.UserDetails import AccessToken
from cvpysdk import services
from cvpysdk.client import Clients
from cvpysdk.operation_window import OperationWindow
from cvpysdk.commcell import Commcell
from AutomationUtils import config

class AccessTokenValidator():
    """
    AccessTokenValidator class to perform access token validations
    """
    def __init__(self, commcell, admin_console_obj, username):
        """
        Initialize the instance of the AccessTokenValidator class
        Args:
            commcell           (Commcell object)         -- object of the Commcell class
            admin_console_obj  (AdminConsole object)     -- object of the AdminConsole class
            username           (str)                     -- Name of the user that is logged into

        """
        self.admin_console_obj = admin_console_obj
        self.log = self.admin_console_obj.log
        self.commcell = commcell
        self.username = username
        self.hostname = self.commcell.webconsole_hostname
        self.client = self.commcell.commserv_client
        self.access_token_obj = AccessToken(self.admin_console_obj, self.username)
        self.services = services.get_services("http://" + self.hostname + "/webconsole/api/")
        self.config_json = config.get_config()


    def _wait_until_expiry_time(self, expirytime, token_name):
        """
        Args:
            expirytime   <dict> ex: {"hour":12, "minute":12, "session":"AM"}
            token_name   <str>  Name of the token to be waited for
        Returns:
            None
        """
        cur_time = datetime.datetime.now()
        exp_time = datetime.time(expirytime['hour'], expirytime['minute'])
        timediff = abs((cur_time - datetime.datetime.combine(datetime.date.today(), exp_time)).total_seconds()) // 60

        if timediff>7:
            cur_time = cur_time + datetime.timedelta(minutes=5)
            am_pm = "AM" if "AM" in datetime.datetime.strftime(cur_time, "%Y-%m-%d %I:%M:%S %p") else "PM"
            timedict = {'hour': int(cur_time.strftime("%I")), 'minute': cur_time.minute, "session": am_pm}
            self.log.info("editing time from {} to {}".format(expirytime, timedict))
            self.access_token_obj.edit_token(current_token_name=token_name, field="time", value=timedict)

            '''
            If the token is started at 23:58 and we add five minutes time delta to it,
            the date might also change. So here we are cosidering the date after the timedelta
            and editing the token to that date.
            '''
            mapper = {
                1: "january",
                2: "february",
                3: "march",
                4: "april",
                5: "may",
                6: "june",
                7: "july",
                8: "august",
                9: "september",
                10: "october",
                11: "november",
                12: "december"
            }
            datedict = {'year': cur_time.year,'month': mapper[cur_time.month],'day': cur_time.day}
            self.access_token_obj.edit_token(current_token_name=token_name, field="date", value=datedict)
        else:
            self.log.info("waiting for %s minutes"%timediff)
            time.sleep((timediff*60)+60)
        self.log.info("Waiting for token to expire")
        time.sleep(360)
        self.log.info("token expired")

    def validate_expiry_time(self):
        """validates the access token operations by sending requests with valid token and expired token
                Raises:
                    Raises exception if the token is expired/access is denied
                    ex:
                        SDKException('Response', '102', response_string)
                        cvpysdk.exception.SDKException: Response received is empty
                        {
                        "errorMessage":"Access denied","errorCode":5
                        }
        """
        token, token_name, expirytime = self.access_token_obj.create_token()
        self.log.info("access token = %s" % token)
        self.commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                 authtoken="Bearer "+str(token), verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
        self.client = self.commcell.commserv_client
        operation_window_obj = OperationWindow(self.client)
        self.log.info("Creating an operation window using POST request")
        ruleid = operation_window_obj.create_operation_window(name=token_name).rule_id
        self.log.info("Created an operation window with rule id %s" % ruleid)

        self.log.info("Getting all Operation windows using GET request")
        windows = operation_window_obj.list_operation_window()
        self.log.info("Operation window created %s"% windows)

        self.log.info("Deleting the operation window using DELETE request")
        operation_window_obj.delete_operation_window(ruleid)
        self.log.info("Deleted operation window")

        self._wait_until_expiry_time(expirytime, token_name)

        self.log.info("Creating an operation window using POST request")
        try:
            ruleid = operation_window_obj.create_operation_window(name="opwindow1").rule_id
            self.log.info("Created an operation window with rule id %s" % ruleid)
        except SDKException as exp:
            if exp.exception_id == "106":
                self.log.info("Token expired exception")
                self.log.info("Working as expected")
            else:
                raise SDKException(exp.exception_module, exp.exception_id)
        else:
            raise Exception("Request is processed even with expired token. Something went wrong.")

        self.log.info("Getting all Operation windows using GET request")
        try:
            windows = operation_window_obj.list_operation_window()
            self.log.info("Operation window created %s" % windows)
        except SDKException as exp:
            if exp.exception_id == "106":
                self.log.info("Token expired exception")
                self.log.info("Working as expected")
            else:
                raise SDKException(exp.exception_module, exp.exception_id)
        else:
            raise Exception("Request is processed even with expired token. Something went wrong.")

        self.log.info("Deleting the operation window using DELETE request")
        try:
            operation_window_obj.delete_operation_window(ruleid)
            self.log.info("Deleted operation window")
        except SDKException as exp:
            if exp.exception_id == "106":
                self.log.info("Token expired exception")
                self.log.info("Working as expected")
            else:
                raise SDKException(exp.exception_module, exp.exception_id)
        else:
            raise Exception("Request is processed even with expired token. Something went wrong.")
        self.log.info("Successfully validated the access token operations")

    def validate_scope(self):
        """validates the access token operations by sending requests with to in-scope and out-scope of endpoints
                Args:
                    None
                Returns:
                    None
                Raises:
                    Raises exception if the token is expired/access is denied.
                    Ex:
                        SDKException('Response', '102', response_string)
                        cvpysdk.exception.SDKException: Response received is empty
                        {
                        "errorMessage":"Access denied","errorCode":5
                        }
        """
        token, token_name, expirytime = self.access_token_obj.create_token(
            scope=['/Client', '/OperationWindow', '/Qcommand', "/VSAClientAndClientGroupList", "/WhoAmI", "/CommServ"])
        self.log.info("Created access token with custom scope /client and /operationwindow")
        self.log.info("access token = %s" % token)
        self.commcell = Commcell(webconsole_hostname=self.commcell.webconsole_hostname,
                                 authtoken="Bearer "+str(token), verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
        self.client = self.commcell.commserv_client
        operation_window_obj = OperationWindow(self.client)
        self.log.info("Creating an operation window using POST request to /OperationWindow")
        ruleid = operation_window_obj.create_operation_window(name="opwindow1").rule_id
        self.log.info("Created an operation window with rule id %s" % ruleid)

        self.log.info("Getting all Operation windows using GET request to /OperationWindow")
        windows = operation_window_obj.list_operation_window()
        self.log.info("Operation window created %s" % windows)

        self.log.info("Deleting the operation window using DELETE request to /OperationWindow")
        operation_window_obj.delete_operation_window(ruleid)
        self.log.info("Deleted operation window")

        self.log.info("Sending a GET reqest to /client")
        clients_obj = Clients(self.commcell)
        clients = clients_obj._get_clients()
        self.log.info("Clients of this commcell are : %s" % clients)

        self.log.info("Editing scope of the access token only to /operationwindow")
        self.access_token_obj.edit_token(token_name, "scope", ["/OperationWindow", "/Qcommand", "/WhoAmI", "/CommServ"])

        self.log.info("Creating an operation window using POST request to /OperationWindow")
        ruleid = operation_window_obj.create_operation_window(name="opwindow1").rule_id
        self.log.info("Created an operation window with rule id %s" % ruleid)

        self.log.info("Getting all Operation windows using GET request to /OperationWindow")
        windows = operation_window_obj.list_operation_window()
        self.log.info("Operation window created %s" % windows)

        self.log.info("Deleting the operation window using DELETE request to /OperationWindow")
        operation_window_obj.delete_operation_window(ruleid)
        self.log.info("Deleted operation window")

        self.log.info("Sending a GET reqest to /client")
        try:
            clients = clients_obj._get_clients()
            self.log.info("Clients of this commcell are : %s" % clients)
        except SDKException as exp:
            if exp.exception_id == "106":
                self.log.info("Token expired exception")
                self.log.info("Working as expected")
            else:
                raise SDKException(exp.exception_module, exp.exception_id)
        else:
            raise Exception("Request is processed even with out of scope API. Something went wrong.")

        try:
            self.access_token_obj.revoke_token(token_name)
        except selenium.common.exceptions.NoSuchElementException:
            pass

        self.log.info("Token access revoked")
        self.log.info("Successfully validated the scope operations of access token")
