# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    Setup()                 --  setup function of this test case

    Run()                   --  run function of this test case

    Tear_down()             --  tear down function of this test case

"""

import json, requests
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils import config, constants
import xml.etree.ElementTree as ET


class TestCase(CVTestCase):
    """Testcase: REST API Validation for Master and Service Commcells"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "REST API Validation for Master and Service Commcells"
        self.organization_helper = None
        self.config_json = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        if not self.commcell:
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.cs_password)

    def run(self):
        """Run function of this test case"""

        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'}

            # Case 1: Authcode of Master Commcell
            self.log.info("**** Case 1: Authcode of Master Commcell ****")
            url = self.config_json.Install.api.mastercsurl
            payload = json.dumps({"authcode": self.commcell.enable_auth_code()})
            response = self.commcell._cvpysdk_object.make_request(
                method="POST",
                url=url,
                headers=headers,
                payload=payload)
            gateways = response[1].json()['gatewayInfo']

            response_list = []
            for i in range(len(gateways)):
                response_list.append(str(gateways[i].get('hostname')) + ":" + str(gateways[i].get('port')))
            self.log.info(f"Gateways returned from API Call are {response_list}")
            config_list = [self.config_json.Install.mastercs.gateway]

            for gateway in config_list:
                if gateway not in response_list:
                    self.status = constants.FAILED

            # Case 2: Authcode to Tenant admin of Master Commcell
            self.log.info("**** Case 2: Tenant admin of Master Commcell ****")
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
            url = self.config_json.Install.api.mastercsurl
            payload = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                          <App_GetGatewayInfoReq>
                          <userAccount password="{self.config_json.Install.mastercs.tenants.Auto_Tenant1.users.password1_enc}"
                          userName="{self.config_json.Install.mastercs.tenants.Auto_Tenant1.users.email1}"/>
                          </App_GetGatewayInfoReq>"""
            response = requests.request("POST",
                                        url,
                                        headers=headers,
                                        data=payload)
            response_list = []
            root = ET.fromstring(response.content)
            for child in root:
                if child.tag == "gatewayInfo":
                    hostname = child.attrib['hostname']
                    port = child.attrib['port']
                    response_list.append(str(hostname) + ":" + str(port))

            self.log.info(f"Gateways returned from API Call are {response_list}")
            config_list = [self.config_json.Install.mastercs.tenants.Auto_Tenant1.gateways.gatewaywin,
                           self.config_json.Install.mastercs.tenants.Auto_Tenant1.gateways.gatewayunix,
                           self.config_json.Install.mastercs.gateway]

            for gateway in config_list:
                if gateway not in response_list:
                    self.status = constants.FAILED

            # Case 3: Authcode of Service Commcell
            self.log.info("**** Case 3: Authcode of Service Commcell ****")
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'}
            self.commcell = Commcell(
                webconsole_hostname=self.config_json.Install.service_commserve_client.machine_host,
                commcell_username=DEFAULT_COMMSERV_USER,
                commcell_password=self.config_json.Install.service_commserve_client.cs_password)
            url = self.config_json.Install.api.servicecsurl
            payload = json.dumps({"authcode": self.commcell.enable_auth_code()})
            response = self.commcell._cvpysdk_object.make_request(
                method="POST",
                url=url,
                headers=headers,
                payload=payload)
            gateways = response[1].json()['gatewayInfo']

            response_list = []
            for i in range(len(gateways)):
                response_list.append(str(gateways[i].get('hostname')) + ":" + str(gateways[i].get('port')))
            self.log.info(f"Gateways returned from API Call are {response_list}")
            config_list = [self.config_json.Install.servicecs.gateway]

            for gateway in config_list:
                if gateway not in response_list:
                    self.status = constants.FAILED

            # Case 4: Tenant admin of Service Commcell
            self.log.info("**** Case 4: Tenant admin of Service Commcell ****")
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'}
            url = self.config_json.Install.api.servicecsurl
            payload = f"""<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                      <App_GetGatewayInfoReq>
                      <userAccount password="{self.config_json.Install.servicecs.tenants.Firewalltest.users.password1_enc}"
                      userName="{self.config_json.Install.servicecs.tenants.Firewalltest.users.email1}"/>
                      </App_GetGatewayInfoReq>"""
            response = requests.request("POST",
                                        url,
                                        headers=headers,
                                        data=payload)
            response_list = []
            root = ET.fromstring(response.content)
            for child in root:
                if child.tag == "gatewayInfo":
                    hostname = child.attrib['hostname']
                    port = child.attrib['port']
                    response_list.append(str(hostname) + ":" + str(port))

            self.log.info(f"Gateways returned from API Call are {response_list}")
            config_list = []

            for gateway in config_list:
                if gateway not in response_list:
                    self.status = constants.FAILED

        except Exception as exp:
            self.log.error(f"Failed with an error: {exp}")
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):

        """Tear down function of this test case"""
