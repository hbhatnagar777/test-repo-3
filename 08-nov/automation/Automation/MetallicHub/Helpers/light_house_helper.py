# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""helper class for performing Light house related operations

    LightHouseHelper:

        __init__()                              --  Initializes lighthouse Helper

        start_task                              --  Starts the LightHouse Helper task

        lh_get_auth_token                       --  Gets the auth token required to authenticate with Light house portal

        lh_add_ring_info                        --  Adds the ring information in the lighthouse portal

        make_request                            --  Makes HTTP POST request to given URL

        delete_lh_config                        --  Deletes the given Light house configs for a given ring

        get_lh_config_ids                       --  Gets the list Light house config ID based on the ring ID

        delete_lh_keys                          --  Deletes the lighthouse entry config for the config passed

"""
import base64
import copy
import requests

from AutomationUtils import logger
from AutomationUtils.config import get_config
from MetallicHub.Utils import Constants as cs
from MetallicRing.Utils import Constants as r_cs
from MetallicRing.Utils.ring_utils import RingUtils

_CONFIG = get_config(json_path=r_cs.METALLIC_CONFIG_FILE_PATH).Metallic.ring
_LH_HUB_CONFIG = get_config(json_path=cs.METALLIC_HUB_CONFIG_FILE_PATH).Hub.lh_config


class LightHouseHelper:
    def __init__(self, ring_name=None):
        self.log = logger.get_log()
        if ring_name is None:
            self.ring_name = RingUtils.get_ring_name(_CONFIG.id)
        else:
            self.ring_name = ring_name

    def start_task(self):
        """
        Starts the LightHouse Helper task
        """
        status = cs.FAILED
        message = None
        try:
            self.log.info("Starting light house helper task")
            auth_token = f"Bearer {self.lh_get_auth_token()}"
            self.lh_add_ring_info(self.ring_name, auth_token)
            self.log.info("Light house helper task successfully")
            status = cs.PASSED
        except Exception as exp:
            message = f"Failed to execute Light house helper. Exception - [{exp}]"
            self.log.info(message)
        return status, message

    def lh_get_auth_token(self, url=_LH_HUB_CONFIG.AUTH_URL, username=_LH_HUB_CONFIG.AUTH_UNAME,
                          password=_LH_HUB_CONFIG.AUTH_PWD):
        """
        Gets the auth token required to authenticate with Lighthouse portal
        Args:
            url(str)            --  URL to get Auth token
            username(str)       --  Username required to authenticate
            password(str)       --  Password required to authenticate
        Returns:
            str                 --  string containing bearer authentication token
        """
        self.log.info(f"Request received to get Auth token for LH with user [{username}]")
        auth_req = copy.deepcopy(cs.lh_auth_req)
        auth_req['username'] = username
        auth_req['password'] = password
        response = self.make_request(url, auth_req)
        auth = response.get('data', {}).get("authToken", None)
        self.log.info("Light house Authentication Response received")
        return auth

    def lh_add_ring_info(self, ring_name, auth_token, url=_LH_HUB_CONFIG.RING_INFO_URL,
                         ring_access_uname=f"{_CONFIG.hub_user.domain}\\{_CONFIG.hub_user.username}",
                         ring_access_pwd=_CONFIG.hub_user.password):
        """
        Adds the ring information in the lighthouse portal
        Args:
            ring_name(str)              --  Name of the ring
            auth_token(str)             --  Bearer token used for auth
            url(str)                    --  URL for adding ring info to light house
            ring_access_uname(str)      --  Master Username to authenticate with the ring
            ring_access_pwd(str)        --  Master username's password
        Returns:
            None
        """
        self.log.info(f"Request received to add the ring info to light house URL - [{url}], "
                      f"username - [{ring_access_uname}]")
        add_ring_info_req = copy.deepcopy(cs.lh_add_ring_info_req)
        ring_name = str.upper(ring_name)
        for config in add_ring_info_req:
            config["name"] = config["name"] % ring_name
            config["configKey"] = config["configKey"] % ring_name
            if config["name"] == f"{ring_name} Access Username":
                config["configValue"] = ring_access_uname
            elif config["name"] == f"{ring_name} Access Password":
                config["configValue"] = base64.b64encode(ring_access_pwd.encode('utf-8')).decode('utf-8')
            elif config["name"] == f"{ring_name} Access URL":
                config["configValue"] = config["configValue"] % ring_name
        self.make_request(url, add_ring_info_req, auth_token)

    def delete_lh_config(self):
        """
        Deletes the given Light house configs for a given ring
        """
        self.log.info("Deleting Lighthouse configs")
        auth_token = f"Bearer {self.lh_get_auth_token()}"
        ids = self.get_lh_config_ids(auth_token)
        self.log.info(f"List of Ids returned for ring name [{self.ring_name}] is {ids}")
        for key in ids:
            self.delete_lh_keys(auth_token, key)
        self.log.info("Light house config deleted successfully")

    def get_lh_config_ids(self, auth, url=_LH_HUB_CONFIG.RING_INFO_URL):
        """
        Gets the list Light house config ID based on the ring ID
        Returns:
             List(str) -- List of lighthouse config IDs
        """
        url = f"{url}{cs.lh_search_field % self.ring_name}"
        response = self.make_request(url, data=None, auth=auth, method=cs.ReqType.GET)
        data = response.get("data", None)
        if data is not None and len(data) == 3:
            return [item['id'] for item in data]
        self.log.info(f"Invalid response data. [{response}]")
        raise Exception(f"Invalid response data. [{response}]")

    def delete_lh_keys(self, auth, key, url=_LH_HUB_CONFIG.RING_INFO_URL):
        """
        Deletes the lighthouse entry config for the config passed
        """
        self.log.info(f"Request received to delete key [{key}] for Ring [{self.ring_name}]")
        url = f"{url}/{key}"
        self.make_request(url, data=None, auth=auth, method=cs.ReqType.DELETE)
        self.log.info(f"Deleted LH key successfully")

    def make_request(self, url, data, auth=None, method=cs.ReqType.POST):
        """
        Makes HTTP request to given URL
        Args:
             url(str)           --  Request URL
             data(str)          --  Request body
             auth(str)          --  Bearer Auth token
             method(enumerate)  --  Method of HTTP request
        Returns:
            dict            --  Dictionary containing the response data
        Raises:
            Exception
                When response is not successful
        """
        self.log.info(f"Sending request to URL [{url}] with data [{data}]")
        headers = {'Content-Type': 'application/json'}
        if auth is not None:
            headers['Authorization'] = auth
        if method == cs.ReqType.POST:
            response = requests.post(url, json=data, headers=headers)
        elif method == cs.ReqType.DELETE:
            response = requests.delete(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        if response.status_code in (200, 201):
            self.log.info("Response successful")
        else:
            self.log.info(f"Response failed. {response.status_code}")
            raise Exception(f"Response Failed. Status: {response.status_code}. Error: {response.content}")
        self.log.info(f"Response received - [{response}]")
        return response.json()
