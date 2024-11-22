# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file that does all operations on AliCloud

Classes:

AliHelper - Ali Cloud class that provides elastic compute service to automation


AliHelper:

build_request_string()	    --	Builds the request string to be used with the API requests

execute_action()		    --	Computes RPC URL based on Ali Cloud standard.

get_regions()			    --	Returns all the regions available.

get_all_vms_in_hypervisor()	--	gets all vms from all regions in ali cloud.

compute_free_resources()    --  computes the region, network and security groups based on proxy

"""

from datetime import datetime
import uuid
from urllib.parse import quote, urlencode
import hmac
import base64
import hashlib
import json
import requests
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor


class AliCloudHelper(Hypervisor):
    """
    Ali Cloud class that provides elastic compute service to automation
    """

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes
    # This requirement is coming from base class.

    def __init__(self,
                 server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine
                 ):
        """

        Args:

            server_host_name  (str) -- Url of Ali Cloud.defaults to public url

            host_machine (str)  -- the client of CS where we will execute all the powershell cmd

            user_name (str)  -- Access key of the user

            password (str)  -- Secret key corresponding to the access key.

            instance_type (str)  -- Will be defaulted to ALI , when object is created for
                                        hypervisor class.

            commcell (Object) -- commcell object created using python SDK.

        """
        # pylint: disable=too-many-instance-attributes
        # pylint: disable=unused-argument
        # We inherit all this from base class , it might be required for ali cloud ,but will be
        # required for other hypervisors. Cant do much.
        super(AliCloudHelper, self).__init__(server_host_name, user_name, password,
                                             instance_type, commcell, host_machine)
        self.ali_url = "https://ecs.aliyuncs.com/?"
        self.access_key = user_name
        self.secret_key = password
        self.secret_key += "&"
        self.ali_common_param = {
            "AccessKeyId": self.access_key,
            "Format": "JSON",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "Version": "2014-05-26"
        }
        self.region_ids = []
        self.vm_list = []
        self.vm_region_map = {}
        self.vm_details = {}

    @staticmethod
    def build_request_string(table):
        """
        Builds a request string from the request params

        Args:
            table   (dict): the params to be sent with the request

        Returns:
            res (str):   encoded string of all the request params

        """
        items = sorted(iter(table.items()), key=lambda d: d[0])

        res = urlencode(items)
        res = res.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')

        return res

    def execute_action(self, action, additional_param=None):
        """
        Computes RPC URL based on Ali Cloud standard.
        Args:

            action (str) -- Name of the Action to be performed.

            additional_param  (dict)   -- Key value pair of additional inputs to the action
            specified.

        Returns:

            Response from the RPC call if status is 200.

        Raises:

            When RPC call failed. Dumps response in the exception message.


        """

        # pylint: disable=too-many-locals
        # url encoding and signature calculation involves multiple steps and we need locals.
        retry = 0
        while retry < 3:

            if additional_param is None:
                additional_param = {}

            now = datetime.utcnow()
            utc = now.isoformat(timespec='seconds') + 'Z'
            api = self.ali_url

            import copy
            # Have dict per execute call
            # Hence multiple request can be made simultaneously
            params = copy.deepcopy(self.ali_common_param)
            params['Action'] = action
            params['SignatureNonce'] = str(uuid.uuid1())
            params['Timestamp'] = utc
            params.update(additional_param)

            encoded_params = self.build_request_string(params)
            string_to_sign = f"GET&%2F&{quote(encoded_params)}"

            # Generate signature
            digest = hmac.new(
                bytes(self.secret_key, 'UTF-8'),
                bytes(string_to_sign, 'UTF-8'),
                hashlib.sha1
            ).digest()
            sign = base64.standard_b64encode(digest)
            signature = str(sign, "UTF-8")
            params['Signature'] = signature

            url = api + self.build_request_string(params)

            response = requests.get(url)
            if response.status_code != 200:
                retry += 1
                continue
            elif response.status_code == 200 and response.content:
                return json.loads(response.content)

        raise Exception("Ali Cloud REST call failed, Response [{}] and message [{}] ".format(
            str(response),
            str(response.content)))

    def get_regions(self):
        """
        Returns all the regions available.

        Returns:
            region_list   (list)    -- List of regions in ali cloud
        """
        regions = self.execute_action("DescribeRegions")
        for region in regions["Regions"]["Region"]:
            self.region_ids.append(region["RegionId"])

    def get_all_vms_in_hypervisor(self, region_id=None):
        """

        gets all vms from all regions in ali cloud.

        Args:
            region_id   (str / list):   regions whose instances are to be obtained

        Returns:
            list of all instances in the regions

        """
        if region_id:
            if isinstance(region_id, str):
                regions = [region_id]
            elif isinstance(region_id, list):
                regions = region_id
        else:
            self.get_regions()
            regions = self.region_ids

        for region in regions:
            stop = True
            pageNumber = 1
            try:
                while stop:
                    get_vms = {
                        "RegionId": region,
                        "PageNumber": pageNumber
                    }
                    instances = self.execute_action("DescribeInstances", get_vms)
                    for instance in instances["Instances"]["Instance"]:
                        instance_name = instance["InstanceName"]
                        self.vm_region_map[instance_name.lower()] = region
                        self.vm_details[instance_name.lower()] = instance
                    if instances['PageNumber']*instances['PageSize'] >= instances['TotalCount']:
                        stop = False
                    pageNumber = pageNumber + 1
            except Exception as err:
                pass
        return self.vm_region_map.keys()

    def power_on_instance(self, region, instance_id):
        """
        power on the instance
        Args:
            region: (str) id of the region of the instance to be obtained
            instance_id: (str) id of the instance in alibaba cloud
        """
        start_instance = {
            "RegionId": region,
            "InstanceId": instance_id
        }
        self.execute_action("StartInstance", start_instance)

    def power_off_instance(self, region, instance_id):
        """
        power on the instance
        Args:
            region: (str) id of the region of the instance to be obtained
            instance_id: (str) id of the instance in alibaba cloud
        """
        stop_instance = {
            "RegionId": region,
            "InstanceId": instance_id
        }
        self.execute_action("StopInstance", stop_instance)

    def power_on_proxies(self, proxy_ips):
        """
        power on the instances with ips given as input
        Args:
            proxy_ips: (list) ips of the proxies to be powered on

        """
        if not self.vm_details:
            self.get_all_vms_in_hypervisor()
        for instance in self.vm_details:
            if self.vm_details[instance]['VpcAttributes']['PrivateIpAddress']['IpAddress'][0] in proxy_ips.values():
                self.power_on_instance(self.vm_region_map[instance], self.vm_details[instance]["InstanceId"])

    def power_off_proxies(self, proxy_ips):
        """
        power on the instances with ips given as input
        Args:
            proxy_ips: (list) ips of the proxies to be powered off

        """
        try:
            if not self.vm_details:
                self.get_all_vms_in_hypervisor()
            for instance in self.vm_details:
                if self.vm_details[instance]['VpcAttributes']['PrivateIpAddress']['IpAddress'][0] in proxy_ips.values():
                    self.power_off_instance(self.vm_region_map[instance], self.vm_details[instance]["InstanceId"])
        except Exception as exp:
            self.log.exception(exp)

    def compute_free_resources(self, proxy):
        """
        Compute the free resources of the endpoint depending on proxy and source instance

        Args:

            proxy   (str):   name of the proxy whose region has to be found out

        Returns:

            zone    (str):   the zone to restore the VMs to

            vpc     (str):   the vpc the restored VMs should be associated with

            security_groups (str):   the security group to be associated to

        Raises:
            Exception:
                if there is an error in computing the resources of the endpoint.

        """
        try:
            proxy = proxy.lower()
            if proxy not in self.vm_region_map.keys():
                self.get_regions()
                self.get_all_vms_in_hypervisor()
            region = self.vm_region_map[proxy]

            get_network = {'RegionId': region, 'PageSize': 50}
            proxy_details = self.vm_details[proxy]
            networks = self.execute_action("DescribeNetworkInterfaces", get_network)
            for network in networks['NetworkInterfaceSets']['NetworkInterfaceSet']:
                if network['InstanceId'] == proxy_details['InstanceId']:
                    security_groups = network['SecurityGroupIds']['SecurityGroupId']
                    vpc = network['VSwitchId']
                    zone = network['ZoneId']
                    break

            return zone, vpc, security_groups
        except Exception as err:
            self.log.exception("An exception %s occurred in computing free resources"
                               " for restore", err)
            raise Exception(err)
