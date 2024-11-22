# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on Amazon """

import boto3
import botocore
import datetime
import time
import json
from botocore.exceptions import ClientError
from dateutil.tz import tzlocal
from collections import defaultdict
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils.VirtualServerUtils import get_details_from_config_file
from AutomationUtils.pyping import ping


class AmazonHelper(Hypervisor):
    """
        Main class for performing all operations on AWS
        """

    def __init__(self, server_host_name,
                 user_name,
                 password,
                 instance_type,
                 commcell,
                 host_machine,
                 **kwargs):

        super(AmazonHelper, self).__init__(server_host_name, user_name, password,
                                           instance_type, commcell, host_machine,
                                           **kwargs)
        if kwargs.get('region') is None:
            self.aws_region = 'us-east-1'  # default region
        else:
            self.aws_region = kwargs.get('region')
        self.kwargs = kwargs
        self.cross_account = False
        if kwargs.get('is_metallic', None):
            self.cross_account = True
        if kwargs.get('BYOS') == False:
            self.cross_account = False
        if kwargs.get('is_tenant') == True:
            self.cross_account = True

        # only admin account case
        if kwargs.get('admin_password') is None and not self.cross_account:
            if isinstance(password, tuple) and all(password):
                self.log.info("Using secret key and access key authentication")
                self._aws_access_key = password[0]
                self._aws_secret_key = password[1]
            else:
                self.log.info(
                    "Hypervisor using STS/IAM Auth so Automation will read Secret and access key from config file")
                keys = get_details_from_config_file('aws_login_creds', 'keys')
                self._aws_access_key = keys.split(":")[0]
                self._aws_secret_key = keys.split(":")[1]

            self._aws_admin_access_key = self._aws_access_key
            self._aws_admin_secret_key = self._aws_secret_key
            self._aws_tenant_access_key = self._aws_access_key
            self._aws_tenant_secret_key = self._aws_secret_key

        # admin and tenant both account configuration
        else:
            admin_password = kwargs.get('admin_password', None)
            if isinstance(admin_password, tuple) and all(admin_password) and isinstance(password, tuple) and all(
                    password):
                self._aws_admin_access_key = admin_password[0]
                self._aws_admin_secret_key = admin_password[1]

                self._aws_tenant_access_key = password[0]
                self._aws_tenant_secret_key = password[1]

                self._aws_access_key = self._aws_tenant_access_key
                self._aws_secret_key = self._aws_tenant_secret_key
            else:
                self.log.info(
                    "Hypervisor using STS/IAM Auth so Automation will read Secret and access key from config file")
                keys = get_details_from_config_file('aws_login_creds', 'keys')
                self._aws_access_key = keys.split(":")[0]
                self._aws_secret_key = keys.split(":")[1]
                try:
                    keys = get_details_from_config_file('aws_tenant_login_creds', 'keys')
                    self._aws_tenant_access_key = keys.split(":")[0]
                    self._aws_tenant_secret_key = keys.split(":")[1]
                except Exception:
                    self._aws_tenant_access_key = self._aws_access_key
                    self._aws_tenant_secret_key = self._aws_secret_key
                self._aws_admin_access_key = self._aws_access_key
                self._aws_admin_secret_key = self._aws_secret_key

        self.connection = None
        self.admin_connection = None
        self.tenant_connection = None
        self.proxy_instances = []
        self.aws_session()
        self._cloud_formation_obj = None
        self._iam_obj = None

    def aws_session(self):
        """Create the session with aws """

        try:
            self.tenant_connection = boto3.Session(aws_access_key_id=self._aws_tenant_access_key,
                                                   aws_secret_access_key=self._aws_tenant_secret_key,
                                                   region_name=self.aws_region)
            self.admin_connection = boto3.Session(aws_access_key_id=self._aws_admin_access_key,
                                                  aws_secret_access_key=self._aws_admin_secret_key,
                                                  region_name=self.aws_region)
            self.connection = self.admin_connection
            if self.cross_account or self.kwargs.get('is_tenant', None):
                self.connection = self.tenant_connection
            self.log.info("Connection successful for AWS")
        except ClientError as err:
            self.log.exception("Unexpected error: %s" % err)
            raise err

    def switch_to_admin_access(self):
        """
          uses admin connection to perform operations in the helper function
        Returns:
            None
        """
        self.connection = self.admin_connection

    def switch_to_tenant_access(self):
        """
        uses tenant connection to perform operations in the helper function
        Returns:
            None
        """
        self.connection = self.tenant_connection

    @property
    def cloud_formation_obj(self):
        """
        get the cloud formation object of aws
        Returns:
            cloud formation obj
        """
        self._cloud_formation_obj = self.connection.resource('cloudformation')
        return self._cloud_formation_obj

    @property
    def iam_obj(self):
        """
        get the IAM object of aws
        Returns:
            IAM resource obj
        """
        # if not self._iam_obj:
        self._iam_obj = self.connection.resource('iam')
        return self._iam_obj

    def power_on_proxies(self, proxy_ips):
        """
        power on the proxies

        Returns: None
        Raises:
            Exception:
                Not able to get instances in the the AWS
        """

        try:
            _resource = self.admin_connection.resource('ec2')
            for instance in _resource.instances.all():
                power_state = instance.state['Code']
                if instance.state['Code'] != 48 and instance.tags:
                    if instance.private_ip_address in proxy_ips.values():
                        if power_state in (0, 32, 64):
                            time.sleep(120)
                            instance.start()
                        elif power_state == 80:
                            instance.start()
                        self.proxy_instances.append(instance)
                        # proxy_ips.remove(instance.private_ip_address)
        except Exception as err:
            self.log.exception("An exception occurred while powering on proxies")
            self.log.exception(err)

    def power_off_proxies(self, proxy_ips):
        """
        power off the proxies

        """

        try:
            _resource = self.admin_connection.resource('ec2')
            for instance in _resource.instances.all():
                if instance.private_ip_address in proxy_ips.values():
                    power_state = instance.state['Code']
                    if instance.state['Code'] != 48:
                        if power_state != 80:
                            instance.stop()
                            time.sleep(180)
                    else:
                        self.log.error("Power Off failed. Instance has been terminated already")

        except Exception as err:
            self.log.exception("An exception occurred while powering off proxies")
            self.log.exception(err)

    def get_vmname_by_ip(self, ip):
        """
        Find instance by its IP
        Args:
            ip: ip address of the machine

        Returns:
            instance of the machine
        """
        try:

            _region_list = self.connection.get_available_regions('ec2')
            # Sorting in reverse so that region "us-east-1" comes first, which is commonly used for VM's
            _region_list.sort(reverse=True)
            self.log.info(f"Regions:\n{_region_list}")
            instances = []

            for region in _region_list:
                try:
                    _resource = self.connection.resource('ec2', region)
                    self.log.info(f"Attempting to search instance - {ip} across region {region}")
                    instances = _resource.instances.filter(Filters=[
                        {
                            'Name': 'private-ip-address',
                            'Values': [ip]
                        },
                    ],
                        DryRun=False
                    )

                    for instance in instances:
                        if instance.state['Code'] != 48:
                            for dicts in instance.tags:
                                if dicts['Key'] == 'Name':
                                    return dicts['Value']
                except Exception as err:
                    self.log.exception("Failed to Get basic info of the instance")
                    raise Exception(err)
        except Exception as err:
            self.log.exception("Failed to Get basic info of the instance")
            raise Exception(err)

    def assumed_role_session(self, role_arn):
        """
        Login via assume role
        Args:
            role_arn                    (string):  assume role

        Returns:
            aws session

        Raises:
            Exception:
                Not able to get login via assume role

        """
        try:

            base_session = boto3.session.Session()._session
            fetcher = botocore.credentials.AssumeRoleCredentialFetcher(
                client_creator=base_session.create_client,
                source_credentials=base_session.get_credentials(),
                role_arn=role_arn
            )
            creds = botocore.credentials.DeferredRefreshableCredentials(
                method='assume-role',
                refresh_using=fetcher.fetch_credentials,
                time_fetcher=lambda: datetime.datetime.now(tzlocal())
            )
            botocore_session = botocore.session.Session()
            botocore_session._credentials = creds
            return boto3.Session(botocore_session=botocore_session, region_name=self.aws_region)
        except Exception as err:
            self.log.exception("Exception during login via assume role: {}".format(err))
            raise err

    def get_all_vms_in_hypervisor(self):
        """
        Get all the ec2 instances in aws

        Returns:
            _all_vm_list    (str):  List of instances in the the AWS

        Raises:
            Exception:
                Not able to get instances in the the AWS
        """
        try:
            _resource = self.connection.resource('ec2')
            _all_vm_list = []
            for instance in _resource.instances.all():
                if instance.state.get('Code', 0) != 48 and instance.tags:
                    for tag in instance.tags:
                        if tag.get('Key') == 'Name':
                            _all_vm_list.append(tag['Value'])
            return _all_vm_list
        except Exception as err:
            self.log.exception("An exception occurred while getting all VMs from AWS")
            raise Exception(err)

    def compute_free_resources(self, proxy_vm):
        """
        If proxy is not in  AWS, only then bucket is needed
        Finds nearest bucket to proxy for restore

        Args:
            proxy_vm    (str)   -   AWS proxy vm

        Returns:
            bucket_id   (str)   -   bucket id

        Raises:
            Exception:
                if it fails to retreive bucket for non aws proxy

        """
        # TODO: this is only for non AWS proxy
        pass

    def check_vms_exist(self, vm_list):
        """

        Check each VM in vm_list exists in Hypervisor VMs Dict

        Args:
            vm_list (list): List of VMs to check

        Returns:
            True (bool): If All VMs are present

            False (bool): If any VM is absent

        """
        if isinstance(vm_list, str):
            vm_list = [vm_list]
        present_vms = self.get_all_vms_in_hypervisor()
        present_vms = set(present_vms)
        if (set(vm_list) & set(present_vms)) == set(vm_list):
            return True
        return False

    def get_instance_region(self, vm_name):
        """

        Retrieves the region that the instance is present in.

        Args:
            vm_name (str): AWS instance name

        Returns:
            region (str): Region that the instance is present in.

        Raises:
            Exception:
                If the instance is not found in either of the regions => The instance does not exist

        """
        self.log.info(
            f"Attempting to search instance - {vm_name} across all regions")
        _region_list = self.connection.get_available_regions('ec2')
        instances = list()

        for region in _region_list:
            try:
                _resource = self.connection.resource('ec2', region)
                instances = list(
                    _resource.instances.filter(
                        Filters=[
                            {
                                'Name': 'tag:Name',
                                'Values': [vm_name]
                            },
                        ],
                        DryRun=False))
            except Exception as excp:
                if excp.response['Error']['Code'] == 'AuthFailure':
                    # Region Disabled <-> Most probable cause
                    continue
                else:
                    raise Exception("Exception: " + str(excp))

            if len(instances):
                self.log.info(
                    f"Instance - {vm_name} found in region - {region}")
                return region

        raise Exception(f"Instance - {vm_name} does not exist")

    def check_resource_exists(self, region='us-east-1', **kwargs):
        """

        Checks if resources exist

        Args:
            region (str) : Region of the resources
            kwargs: (Current Support)
                1. volumes : list of volume ID(s) (list)
                2. network_interfaces : Network interface ID(s) (list)

        Returns:
            resource_status (dict) : Contains the status of the resource
                1. True (if exists)
                2. False (does not exist)

        """
        _resource = self.connection.resource('ec2', region)
        supported_resources = {
            'volumes': 'volume-id',
            'network_interfaces': 'network-interface-id'
        }

        resource_object_list = defaultdict(list)
        resource_status = defaultdict(dict)

        for resource_name in supported_resources.keys():
            resource_object = eval('_resource.' + resource_name)
            resource_object_list[resource_name] = [res.id for res in resource_object.filter(
                Filters=[{'Name': supported_resources.get(resource_name), 'Values': kwargs.get(resource_name)}])]

        for resource_name in supported_resources:
            [resource_status[resource_name].__setitem__(resource_id, resource_id in resource_object_list.get(
                resource_name)) for resource_id in kwargs.get(resource_name)]

        return resource_status

    def get_proxy_location(self, proxy_ip):
        """
        Gets the region of the vm which has the ip specified

        Args :
            proxy_ip(str): ip / host name of the proxy

        Returns:
            status, region :  True, region of the vm if vm is found
                              else False, None

        """
        _prev_state_aws_connection = self.connection
        self.switch_to_admin_access()
        try:
            if not proxy_ip.replace('.', '').isnumeric():
                proxy_ip = ping(proxy_ip).destination_ip
            vm_id = self.get_vmname_by_ip(proxy_ip)
            if vm_id:
                region = self.get_instance_region(vm_id)
                if region is not None:
                    return True, region
            return False, None
        except Exception as err:
            raise Exception("Exception in proxy/VM location restored VM location:{0}".format(err))
        finally:
            self.connection = _prev_state_aws_connection

    def create_stack(self, stack_inputs, delete_previous_existing=False):
        """
        create stack on aws with the stack inputs provided
        Args:
            stack_inputs: dict() containing the inputs for stack creation
            delete_previous_existing : (bool) delete the previous existing stack and create new one

        Returns:
            stack_ouput
        """
        if delete_previous_existing:
            self.log.info("checking for previous existing stack and deleting it")
            if stack_inputs['StackName'] in self.list_stacks():
                self.delete_stack(stackName=stack_inputs['StackName'])
        try:
            self.log.info(f"creating the stack : {stack_inputs['StackName']}")
            self.cloud_formation_obj.create_stack(StackName=stack_inputs['StackName'],
                                                  TemplateURL=stack_inputs['TemplateURL'],
                                                  Capabilities=stack_inputs['Capabilities'],
                                                  Parameters=stack_inputs['parameters'])
        except self.cloud_formation_obj.meta.client.exceptions.AlreadyExistsException:
            self.log.info("stack already exists")
            return None
        except Exception as exp:
            self.log.exception(exp)
            raise Exception
        self.__wait_for_stack_state(stack_inputs['StackName'])
        self.log.info(f"created the stack : {stack_inputs['StackName']} successfully")
        return self.get_stack_details(stack_inputs['StackName'])

    def get_stack_details(self, stack_name):
        """
        get the stack details
        Args:
            stack_name: (str) name

        Returns: stack output

        """
        stack_details = self.cloud_formation_obj.Stack(stack_name)
        return stack_details.outputs

    def list_stacks(self, stackStatusFilter=['CREATE_COMPLETE']):
        """
        get all the stacks in the account
        stackStatusFilter : (list) filter the stacks based on the status of state provided
        """
        stack_list = []
        stack_list_response = self.cloud_formation_obj.meta.client.list_stacks(StackStatusFilter=stackStatusFilter)
        stack_list_details = stack_list_response['StackSummaries']
        for stack in stack_list_details:
            stack_list.append(stack['StackName'])
        return stack_list

    def delete_stack(self, stackName):
        """
        delete the stack on the aws cloud
        Args:
            stackName: (str) name of the stack

        Returns:

        """
        try:
            self.cloud_formation_obj.meta.client.delete_stack(StackName=stackName)
            self.__wait_for_stack_state(stackName, state=['DELETE_COMPLETE'])
            self.log.info("stack got deleted successfully : %s", stackName)
        except Exception as exp:
            self.log.warning("failed to delete the stack with below exception")
            self.log.info(exp)
            raise Exception(exp)

    def __wait_for_stack_state(self, stack_name, state=['CREATE_COMPLETE', 'ROLLBACK_COMPLETE']):
        stack_state_reached = False
        self.log.info(f'waiting for stack : {stack_name} to be in state : {state}')
        while not stack_state_reached:
            self.log.info("sleeping for 30 sec")
            time.sleep(30)
            try:
                stack_status = self.cloud_formation_obj.Stack(stack_name).stack_status
            except:
                if 'DELETE_COMPLETE' in state:
                    stack_status = 'DELETE_COMPLETE'
            self.log.info(f'current status of the stack : {stack_status}')
            if stack_status in state:
                stack_state_reached = True
                self.log.info(f'stack reached the required state')

    def get_role(self, name):
        """
        method to get role details of iam role
        Args:
            name: (str) name of the role

        Returns:
            Iam role (aws obj)
        """
        return self.iam_obj.Role(name)

    def get_role_trust_policy(self, name):
        """
        method to get trust policy of AWS role
        Args:
            name: (str) name of the role

        Returns:
            trust policy (dict)
        """
        role = self._iam_obj.Role(name)
        return role.assume_role_policy_document

    def update_trust_policy(self, name, policy_document):
        """
        method to update the trust policy of aws role
        Args:
            name: (str) name of the role
            policy_document: (str) policy of the role

        Returns:
            None
        """
        assume_role_policy = self._iam_obj.AssumeRolePolicy(name)
        assume_role_policy.update(PolicyDocument=policy_document)

    def add_arn_to_role(self, role_name, role_arn):
        """
        method to add given arn to the policy document of the role
        Args:
            role_name: (str) name of the role
            role_arn: (str) arn of the role to be added

        Returns:
            (dict) updated trust policy
        """
        role_trust_policy = self.get_role_trust_policy(role_name)
        if not role_arn:
            return
        if role_trust_policy['Statement'][0]['Principal'].get('AWS', None):
            current_aws_policy = role_trust_policy['Statement'][0]['Principal']['AWS']
            if isinstance(current_aws_policy, str):
                if current_aws_policy == role_arn:
                    return
                else:
                    updated_policy = [current_aws_policy, role_arn]
            else:
                if role_arn in current_aws_policy:
                    return
                updated_policy = current_aws_policy
                updated_policy.append(role_arn)
            role_trust_policy['Statement'][0]['Principal']['AWS'] = updated_policy
        else:
            role_trust_policy['Statement'][0]['Principal']['AWS'] = role_arn
        self.update_trust_policy(role_name, json.dumps(role_trust_policy))

    def get_vpcid(self, vm_name, region):
        """
        method to fetch the vpc id for the given instance
        Args:
            vm_name: (str) name of the instance
            region: (str) region of the instance

        Returns:
            vpc_id (str)
        """
        try:
            client = self.connection.client('ec2', region)
            ec2_response = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [vm_name]}])[
                'Reservations']
            if len(ec2_response) == 0:
                raise Exception("Instance not found or doesn't exist")
            return ec2_response[len(ec2_response) - 1]['Instances'][0]['VpcId']
        except Exception as exp:
            raise Exception("Failed to fetch the VPC id for the instance as" + str(exp))

    def get_vpc_options(self, vpc_id, region):
        """
        method to fetch the vpc options for the given vpc
        options fetched are: tags, CidrBlock, tenancy, isDefault, dhcp_id, Ipv6CidrBlockAssociationSet
        attributes fetched are: EnableDnsSupport, EnableDnsHostnames, EnableNetworkAddressUsageMetrics
        Args:
            vpc_id: (str) id of the vpc to be searched for
            region: (str) region of the vpc

        Returns:
            vpc_options (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            vpc_response = client.describe_vpcs(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Vpcs'][0]
            tags = {tag['Key']: tag['Value'] for tag in vpc_response.get('Tags', []) if
                    tag['Key'] not in ['CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_']}
            vpc_options = {'CidrBlock': vpc_response['CidrBlock'], 'tenancy': vpc_response['InstanceTenancy'],
                           'isDefault': vpc_response["IsDefault"], 'tags': tags,
                           'dhcp_id': vpc_response['DhcpOptionsId'],
                           'Ipv6CidrBlockAssociationSet': vpc_response.get('Ipv6CidrBlockAssociationSet', []),
                           'enableDnsSupport': client.describe_vpc_attribute(Attribute='enableDnsSupport',
                               VpcId=vpc_id)['EnableDnsSupport']['Value'],
                           'enableDnsHostnames': client.describe_vpc_attribute(Attribute='enableDnsHostnames',
                               VpcId=vpc_id)['EnableDnsHostnames']['Value'],
                           'enableNetworkAddressUsageMetrics': client.describe_vpc_attribute(
                               Attribute='enableNetworkAddressUsageMetrics',
                               VpcId=vpc_id)['EnableNetworkAddressUsageMetrics']['Value']}
            return vpc_options
        except Exception:
            raise Exception("Failed to fetch vpc options")

    def get_subnet_options(self, subnet_id, region):
        """
        method to fetch the subnet options for the given subnet id
        options fetched are: tags, CidrBlock, MapPublicIpOnLaunch, AssignIpv6AddressOnLaunch,
                            'PrivateDnsNameOptionsOnLaunch', EnableDns64
        Args:
            subnet_id: (str) id of the subnet to be searched for
            region: (str) region of the subnet

        Returns:
            subnet_options (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            subnet_response = client.describe_subnets(Filters=[{'Name': 'subnet-id',
                                                                'Values': [subnet_id]}])['Subnets'][0]
            tags = {tag['Key']: tag['Value'] for tag in subnet_response.get('Tags', []) if
                    tag['Key'] not in ['CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_']}
            subnet_options = {'CidrBlock': subnet_response['CidrBlock'],
                              'MapPublicIpOnLaunch': subnet_response['MapPublicIpOnLaunch'],
                              'AssignIpv6AddressOnCreation': subnet_response["AssignIpv6AddressOnCreation"],
                              'Ipv6CidrBlockAssociationSet': subnet_response['Ipv6CidrBlockAssociationSet'],
                              'PrivateDnsNameOptionsOnLaunch': subnet_response['PrivateDnsNameOptionsOnLaunch'],
                              'EnableDns64': subnet_response['EnableDns64'], 'tags': tags,
                              'NetworkAcls': self.get_network_acls(subnet_id, region)}
            return subnet_options
        except Exception:
            raise Exception("Failed to get Subnet options")

    def get_group_options(self, group_ids, region):
        """
        method to fetch the security group options for the given security groups
        options fetched are: tags, IpPermissions, IpPermissionsEgress
        Args:
            group_ids: list(str) ids of the security groups to be searched for
            region: (str) region of the security groups

        Returns:
            group_options list(dict) sorted by group names
        """
        try:
            client = self.connection.client('ec2', region)
            group_options = []
            group_response = client.describe_security_groups(Filters=[{'Name': 'group-id',
                                                                       'Values': group_ids}])["SecurityGroups"]
            for group in group_response:
                tags = {tag['Key']: tag['Value'] for tag in group.get('Tags', []) if
                        tag['Key'] not in ['CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_']}
                for permissions_type in ['IpPermissions', 'IpPermissionsEgress']:
                    for permission in group[permissions_type]:
                        if permission['IpProtocol'] == '-1':
                            permission['FromPort'] = permission['ToPort'] = None
                        del permission['PrefixListIds']
                group_options.append({'tags': tags, 'description': group['Description'], 'GroupName': group['GroupName'],
                  'IpPermissions': sorted(list(group['IpPermissions']), key=lambda x: (x['IpProtocol'],
                                        x['FromPort'] if x['FromPort'] is not None else -1)),
                 'IpPermissionsEgress': sorted(group['IpPermissionsEgress'], key=lambda x: (x['IpProtocol'],
                                        x['FromPort'] if x['FromPort'] is not None else -1))})
            return sorted(group_options, key=lambda x: x['GroupName'])
        except Exception:
            raise Exception("Failed to get Security group options")

    def get_dhcp_options(self, dhcp_id, region):
        """
        method to fetch the dhcp options for the given dhcp id
        options fetched are: tags, dhcp configurations
        Args:
            dhcp_id: (str) id of the dhcp to be searched for
            region: (str) region of the dhcp
        Returns:
            dhcp_options (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            dhcp_response = client.describe_dhcp_options(DhcpOptionsIds=[dhcp_id])["DhcpOptions"][0]
            tags = {tag['Key']: tag['Value'] for tag in dhcp_response.get('Tags', []) if
                    tag['Key'] not in ['CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_']}
            dhcp_options = {'tags': tags}
            for configuration in dhcp_response['DhcpConfigurations']:
                key = configuration["Key"]
                values = configuration['Values']
                if len(values) > 1:
                    dhcp_options[key] = [val["Value"].strip() for val in values]
                else:
                    dhcp_options[key] = values[0]["Value"].strip()
            return dhcp_options
        except Exception:
            raise Exception("Failed to get DHCP options")

    def get_nic_options(self, nic_ids, region):
        """
        method to fetch the nic options for the given list of nic ids
        options fetched are: tags, security groups names and ids, description, sourceDestCheck,
                             ipv6Addresses, interfaceType,
        Args:
            nic_ids: (str) ids of the nics to be searched for
            region: (str) region of the nics

        Returns:
            nic_options list(dict) sorted by description and security group names
        """
        try:
            client = self.connection.client('ec2', region)
            nic_response = client.describe_network_interfaces(Filters=[{'Name': 'network-interface-id',
                                                                        'Values': nic_ids}])['NetworkInterfaces']
            nic_options = []
            for nic in nic_response:
                groups = sorted([sg['GroupName'] for sg in nic['Groups']])
                ids = [sg['GroupId'] for sg in nic['Groups']]
                tags = {tag['Key']: tag['Value'] for tag in nic.get('TagSet', [])
                        if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
                nic_options.append({'Description': nic['Description'], 'SourceDestCheck': nic['SourceDestCheck'],
                                    'Ipv6Addresses': nic['Ipv6Addresses'], 'InterfaceType': nic['InterfaceType'],
                                    'SecurityGroups': groups, 'tags': tags, 'ids': ids})
            return sorted(nic_options, key=lambda x: (x['Description'], x['SecurityGroups']))
        except Exception:
            raise Exception("Failed to get NIC options")

    def get_network_acls(self, subnet_id, region):
        """
        method to fetch the network acl options for the given subnet id
        options fetched are: tags, entries, isDefault
        Args:
            subnet_id: (str) id of the subnet to be searched for
            region:    (str) region of the subnet
        Returns:
            network_acl (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            network_acl = client.describe_network_acls(Filters=[{'Name': 'association.subnet-id',
                                                                 'Values': [subnet_id]}])['NetworkAcls']
            for i in network_acl:
                del i['Associations'], i['NetworkAclId'], i['VpcId'], i['OwnerId']
                i['Tags'] = {tag['Key']: tag['Value'] for tag in i.get('Tags', [])
                             if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
            return network_acl
        except Exception as exp:
            self.log.info("Failed to fetch network acl information : " + str(exp))

    def get_internet_gateways(self, vpc_id, region):
        """
        method to fetch the internet gateway options for the given vpc id
        options fetched are: tags
        Args:
            vpc_id:    (str) id of the vpc to be searched for
            region:    (str) region of the vpc
        Returns:
            internet_gateway (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            internet_gateway = client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                           'Values': [vpc_id]}])['InternetGateways']
            for i in internet_gateway:
                del i['Attachments'], i['InternetGatewayId'], i['OwnerId']
                i['Tags'] = {tag['Key']: tag['Value'] for tag in i.get('Tags', [])
                             if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
            return internet_gateway
        except Exception as exp:
            self.log.info("Failed to fetch internet gateway details" + str(exp))

    def get_egress_only_internet_gateways(self, vpc_id, region):
        """
        method to fetch the egress only internet gateway options for the given vpc id
        options fetched are: tags
        Args:
            vpc_id:    (str) id of the vpc to be searched for
            region:    (str) region of the vpc
        Returns:
            egress_gateways list(dict)
        """
        try:
            client = self.connection.client('ec2', region)
            egress_gateway_response = client.describe_egress_only_internet_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                    'Values': [vpc_id]}])['EgressOnlyInternetGateways']
            egress_gateways = []
            for gateway in egress_gateway_response:
                if any(attachment.get('VpcId') == vpc_id for attachment in gateway.get('Attachments', [])):
                    del gateway['Attachments'], gateway['EgressOnlyInternetGatewayId']
                    gateway['Tags'] = {tag['Key']: tag['Value'] for tag in gateway.get('Tags', [])
                                    if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
                    egress_gateways.append(gateway)
            return egress_gateways
        except Exception as exp:
            self.log.info("Exception in fetching egress gateway details"+str(exp))

    def get_nat_gateways(self, vpc_id, region):
        """
        method to fetch the nat gateway options for the given vpc id
        options fetched are: tags, name, subnet name, connectivity type
        Args:
            vpc_id:    (str) id of the vpc to be searched for
            region:    (str) region of the vpc
        Returns:
            nat_gateway (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            nat_gateway = client.describe_nat_gateways(Filter=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
            for i in nat_gateway:
                del i['NatGatewayId'], i['CreateTime'], i['NatGatewayAddresses'], i['SubnetId'], i['VpcId']
                i['Tags'] = {tag['Key']: tag['Value'] for tag in i.get('Tags', [])
                             if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
            return nat_gateway
        except Exception as exp:
            self.log.info("Failed to get nat gateway details" + str(exp))

    def get_vpn_gateways(self, vpc_id, region):
        """
        method to fetch the virtual private network gateway options for the given vpc id
        options fetched are: tags, state, type, amazon ASN
        Args:
            vpc_id:    (str) id of the vpc to be searched for
            region:    (str) region of the vpc
        Returns:
            vpn_gateway (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            vpn_gateway = client.describe_vpn_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])[
                'VpnGateways']
            for i in vpn_gateway:
                del i['VpcAttachments'], i['VpnGatewayId']
                i['Tags'] = {tag['Key']: tag['Value'] for tag in i.get('Tags', [])
                             if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
            return vpn_gateway
        except Exception as exp:
            self.log.info("Exception in vpn gateways: " + str(exp))

    def get_transit_gateway_vpc_attachments(self, vpc_id, region):
        """
        method to fetch the transit gateway and transit gateway attachment options for the given vpc id
        options fetched for transit gateway are: tags, state, options, description
        options fetched for transit gateway attachments are: tags, state, options
        Args:
            vpc_id:    (str) id of the vpc to be searched for
            region:    (str) region of the vpc
        Returns:
            transit_gateway_attachments (dict)
            transit_gateways (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            transit_gateway_attachments = client.describe_transit_gateway_vpc_attachments(
                                      Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['TransitGatewayVpcAttachments']
            transit_gateways = []
            for attachment in transit_gateway_attachments:
                transit_gateway_id = attachment['TransitGatewayId']
                response = client.describe_transit_gateways(TransitGatewayIds=[transit_gateway_id])['TransitGateways']
                for tgw in response:
                    del tgw['TransitGatewayId'], tgw['CreationTime'], tgw['OwnerId'], tgw['TransitGatewayArn']
                    del tgw['Options']['AssociationDefaultRouteTableId'], tgw['Options']['PropagationDefaultRouteTableId']
                    tgw['Description'] = tgw.get('Description', '')
                    tgw['Tags'] = {tag['Key']: tag['Value'] for tag in attachment.get('Tags', [])
                                   if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
                    transit_gateways.append(tgw)

            for attachment in transit_gateway_attachments:
                del attachment['TransitGatewayAttachmentId'], attachment['TransitGatewayId'], attachment['VpcId'], \
                    attachment['VpcOwnerId'], attachment['SubnetIds'], attachment['CreationTime']
                attachment['Tags'] = {tag['Key']: tag['Value'] for tag in attachment.get('Tags', [])
                                      if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
            return transit_gateway_attachments, transit_gateways
        except Exception as exp:
            self.log.info("Failed to get transit gateway details: " + str(exp))

    def verify_prefix_lists(self, source_region, dest_region, job_id):
        """
        method to verify the restored prefix lists by searching for them using the restore_job_id in GX_BACKUP and
        fetching the source prefix list through CV_SourceId as route tables are not restored in sp36
        options fetched are: tags
        Args:
            source_region:   (str) region of the source instance
            dest_region:    (str) region of the restored instance
            job_id:         (str) restore job id
        Returns:
            (bool)     :True, if the validation is successful
        """
        try:
            source_client = self.connection.client('ec2', source_region)
            dest_client = self.connection.client('ec2', dest_region)
            source_prefix_list_ids, dest_prefix_lists, source_prefix_lists = [], {}, {}
            dest_prefix_list_response = dest_client.describe_managed_prefix_lists()['PrefixLists']
            for prefix_list in dest_prefix_list_response:
                for tag in prefix_list['Tags']:
                    if tag['Key'] == '_GX_BACKUP_' and job_id in tag['Value']:
                        source_id = next((t['Value'] for t in prefix_list['Tags'] if t['Key'] == 'CV_SourceId'), None)
                        if source_id is not None:
                            source_prefix_list_ids.append(source_id)
                        del prefix_list['PrefixListId'], prefix_list['PrefixListArn']
                        prefix_list['Tags'] = {tag['Key']: tag['Value'] for tag in prefix_list.get('Tags', [])
                            if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
                        dest_prefix_lists.update(prefix_list)
            if not source_prefix_list_ids and not dest_prefix_lists:
                return True
            source_prefix_list_response = \
                source_client.describe_managed_prefix_lists(PrefixListIds=source_prefix_list_ids)['PrefixLists']
            for prefix_list in source_prefix_list_response:
                del prefix_list['PrefixListId'], prefix_list['PrefixListArn']
                prefix_list['Tags'] = {tag['Key']: tag['Value'] for tag in prefix_list.get('Tags', [])
                                    if tag['Key'] not in {'CV_VMRestoreInProgressCount', 'CV_SourceId', '_GX_BACKUP_'}}
                source_prefix_lists.update(prefix_list)
            return source_prefix_lists == dest_prefix_lists
        except Exception as exp:
            self.log.info("Failed to get prefix list details" + str(exp))

    def collect_vpc_network_configuration(self, vm, region):
        """
        method to validate the network entities existing under given vpc
        entities fetched are: nics, security groups, subnets, dhcp options, internet gateways, egress only gateways,
                              nat gateways, vpn gateways, transit gateways, transit gateway attachments
        Args:
            vm:     (str) name of the instance
            region: (str) region of the instance
        Returns:
            aws_resources (dict)
        """
        try:
            aws_resources = {"Vpc": self.get_vpc_options(vm.vpc, region),
                             "Subnet": self.get_subnet_options(vm.subnet, region),
                             "Nic": self.get_nic_options(vm.nic, region),
                             'InternetGateways': self.get_internet_gateways(vm.vpc, region),
                             'EgressOnlyInternetGateways': self.get_egress_only_internet_gateways(vm.vpc, region),
                             'NATGateways': self.get_nat_gateways(vm.vpc, region),
                             'VPNGateways': self.get_vpn_gateways(vm.vpc, region), }
            group_ids = {group_id for nic in aws_resources['Nic'] for group_id in nic.pop('ids', [])}
            group_ids.update(vm.security_groups)
            transit_gateway_attachments, transit_gateway = self.get_transit_gateway_vpc_attachments(vm.vpc, region)
            aws_resources.update({'SecurityGroups': self.get_group_options(list(group_ids), region),
                                  'Dhcp': self.get_dhcp_options(aws_resources['Vpc'].pop('dhcp_id'), region),
                                  'TransitGatewayAttachments': transit_gateway_attachments,
                                  'TransitGateway': transit_gateway})
            return aws_resources
        except Exception as exp:
            raise Exception("Failed to get network details of the vm: " + str(exp))

    def get_vpc_entities(self, vpc_id, region, job_id):
        """
        method to fetch the network entities existing under given vpc
        entities fetched are: nics, security groups, subnets, dhcp options id, internet gateways, egress only gateways,
                              nat gateways, vpn gateways, transit gateways, transit gateway attachments, network acls
        Args:
            vpc_id: (str) id of the vpc
            region: (str) region of the vpc
            job_id: (str) restore job id
        Returns:
            network (dict)
        """
        try:
            client = self.connection.client('ec2', region)
            nic_response = client.describe_network_interfaces(Filters=[{'Name': 'vpc-id',
                                                                        'Values': [vpc_id]}])['NetworkInterfaces']
            subnet_response = client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            group_response = client.describe_security_groups(Filters=[{'Name': 'vpc-id',
                                                                    'Values': [vpc_id]}])["SecurityGroups"]
            network_acl_response = client.describe_network_acls(Filters=[{'Name': 'vpc-id',
                                                                    'Values': [vpc_id]}])['NetworkAcls']
            internet_gateway_response = client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                    'Values': [vpc_id]}])['InternetGateways']
            egress_gateway_response = client.describe_egress_only_internet_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                    'Values': [vpc_id]}])['EgressOnlyInternetGateways']
            nat_gateway_response = client.describe_nat_gateways(Filter=[{'Name': 'vpc-id',
                                                                    'Values': [vpc_id]}])['NatGateways']
            vpn_gateway_response = client.describe_vpn_gateways(Filters=[{'Name': 'attachment.vpc-id',
                                                                    'Values': [vpc_id]}])['VpnGateways']
            transit_attachments_response = client.describe_transit_gateway_vpc_attachments(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['TransitGatewayVpcAttachments']
            prefix_list_response = client.describe_managed_prefix_lists()['PrefixLists']
            dhcp_id = client.describe_vpcs(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Vpcs'][0]['DhcpOptionsId']

            nics, egress_gateways = [nic['NetworkInterfaceId'] for nic in nic_response], []
            groups = [group['GroupId'] for group in group_response if group['GroupName'] != 'default']
            subnets = [subnet['SubnetId'] for subnet in subnet_response]
            network_acls = [network_acl['NetworkAclId'] for network_acl in network_acl_response]
            internet_gateways = [ig['InternetGatewayId'] for ig in internet_gateway_response]
            nat_gateways = [nat_gateway['NatGatewayId'] for nat_gateway in nat_gateway_response]
            vpn_gateways = [vpn_gateway['VpnGatewayId'] for vpn_gateway in vpn_gateway_response]
            transit_gateway_attachments = [tg['TransitGatewayAttachmentId'] for tg in transit_attachments_response]
            transit_gateways = [tg['TransitGatewayId'] for tg in transit_attachments_response]
            for gateway in egress_gateway_response:
                if any(attachment.get('VpcId') == vpc_id for attachment in gateway.get('Attachments', [])):
                    egress_gateways.append(gateway['EgressOnlyInternetGatewayId'])
            prefix_list_ids = [prefix_list['PrefixListId'] for prefix_list in prefix_list_response
                if any(tag['Key'] == '_GX_BACKUP_' and job_id in tag['Value'] for tag in prefix_list.get('Tags', []))]
            network = {'nics': nics, 'groups': groups, 'subnets': subnets, 'dhcp': dhcp_id, 'vpc': vpc_id,
                       'networkacls': network_acls, 'natgateways': nat_gateways, 'vpngateways': vpn_gateways,
                       'internetgateways': internet_gateways, 'egressonlyinternetgateways': egress_gateways,
                       'transitgatewayattachments': transit_gateway_attachments,
                       'transitgateways': transit_gateways, 'prefix-lists': prefix_list_ids}
            return network
        except Exception as exp:
            raise Exception("Failed to get vpc network entities : " + str(exp))

    def terminate_network(self, network, region):
        """
        terminates entire vpc network in order
        Args:
            network: (dict) network entities to be terminated
            region: (str) region of the vpc
        """
        try:
            client = self.connection.client('ec2', region)
            self.log.info("Terminating NAT Gateways")
            for nat_gw in network.get('natgateways', []):
                try:
                    client.delete_nat_gateway(NatGatewayId=nat_gw)
                except Exception as e:
                    print(f"Error terminating NAT Gateway {nat_gw}: {e}")
            self.log.info("Terminating Network interfaces")
            for nic in network.get('nics'):
                try:
                    client.delete_network_interface(NetworkInterfaceId=nic)
                except Exception:
                    pass # might be trying to delete default nics which will be deleted later with entity only so ignore
            self.log.info("Terminating security groups")
            for group in network.get('groups'):
                client.delete_security_group(GroupId=group)
            self.log.info("Terminating Transit Gateway Attachments")
            for attachment in network.get('transitgatewayattachments', []):
                try:
                    client.delete_transit_gateway_vpc_attachment(TransitGatewayAttachmentId=attachment)
                except Exception as e:
                    print(f"Error terminating Transit Gateway Attachment {attachment}: {e}")
            time.sleep(50)
            self.log.info("Terminating Transit Gateways")
            for tgw in network.get('transitgateways', []):
                try:
                    client.delete_transit_gateway(TransitGatewayId=tgw)
                except Exception as exp:
                    print(f"Error terminating Transit Gateway {tgw}: {exp}")
            time.sleep(70)
            self.log.info("Terminating subnets")
            for subnet in network.get('subnets'):
                client.delete_subnet(SubnetId=subnet)
            self.log.info("Terminating Network ACLs")
            for acl in network.get('networkacls', []):
                try:
                    client.delete_network_acl(NetworkAclId=acl)
                except Exception:
                    pass  # might be trying to delete default acl which will be deleted later with entity only so ignore
            self.log.info("Terminating Internet Gateways")
            for igw in network.get('internetgateways', []):
                try:
                    client.detach_internet_gateway(InternetGatewayId=igw, VpcId=network['vpc'])
                    time.sleep(20)
                    client.delete_internet_gateway(InternetGatewayId=igw)
                except Exception as exp:
                    self.log.info(f"Error terminating Internet Gateway {igw}: {exp}")
            self.log.info("Terminating Egress-Only Internet Gateways")
            for egress_gw in network.get('egressonlyinternetgateways', []):
                try:
                    client.delete_egress_only_internet_gateway(EgressOnlyInternetGatewayId=egress_gw)
                except Exception as exp:
                    self.log.info(f"Error terminating Egress-Only Internet Gateway {egress_gw}: {exp}")
            self.log.info("Terminating VPN Gateways")
            for vpn_gw in network.get('vpngateways', []):
                try:
                    client.detach_vpn_gateway(VpcId=network['vpc'], VpnGatewayId=vpn_gw)
                    time.sleep(70)
                    client.delete_vpn_gateway(VpnGatewayId=vpn_gw)
                except Exception as exp:
                    self.log.info(f"Error terminating VPN Gateway {vpn_gw}: {exp}")
            time.sleep(30)
            self.log.info("Terminating VPC")
            client.delete_vpc(VpcId=network.get('vpc'))
            time.sleep(50)
            self.log.info("Terminating DHCP options")
            client.delete_dhcp_options(DhcpOptionsId=network.get('dhcp'))
            self.log.info("Terminating Prefix lists")
            for prefix_list in network.get('prefix-lists'):
                try:
                    client.delete_managed_prefix_list(PrefixListId=prefix_list)
                except Exception:
                    pass  # might be trying to delete default aws lists which needn't be deleted so ignore
        except Exception as exp:
            raise Exception("Exception occurred while terminating network entities:" + str(exp))

        def get_volume_details(self, volume_id):
            """
            Method to fetch the all details of the volume

            Args:
                volume_id: (str) id of the Volume

            Returns:
                Volume dictionary
            """

            try:
                client = self.connection.client('ec2')
                volume_response = client.describe_volumes(VolumeIds=[volume_id])
                return volume_response

            except Exception as exp:
                raise Exception("Exception occured while getting the volume details " + str(exp))