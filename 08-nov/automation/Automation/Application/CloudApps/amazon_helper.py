# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Amazon operations

AmazonCLIHelper, AmazonEC2Helper, AmazonRDSCLIHelper, AmazonRedshiftCLIHelper, AmazonDynamoDBCLIHelper and
AmazonCloudDatabaseHelper are the classes defined in this file.

AmazonCLIHelper   :   Helper class for common AWS CLI Operations

AmazonEC2Helper   :   Helper class for common AWS CLI Operations

AmazonCloudFormationHelper    :    Helper class for common AWS cloudformation operations

AmazonRDSCLIHelper  :   Helper class derived from AmazonCLIHelper to perform Amazon RDS related CLI operations.

AmazonRedshiftCLIHelper : Helper class derived from AmazonCLIHelper to Amazon Redshift related CLI operations

AmazonDocumentDBDCLIHelper  :   Helper class derived from AmazonCLIHelper to Amazon DocumentDB related CLI operations

AmazonDynamoDBDCLIHelper : Helper class derived from AmazonCLIHelper to Amazon DynamoDB related CLI operations

AmazonCloudDatabaseHelper : Helper class used to perform commvault related operations for the testcases related
                            to Amazon RDS/Redshift/DocumentDB

AmazonCLIHelper:

    __init__()         -- Initializes AmazonCLIHelper instance with secret and access keys

    get_client()       -- Returns aws client for requested resource and region.

    empty_cluster_dict()    -- Returns a dictionary with all available regions as key and empty sets as values.

    ec2_state   --  Returns the state of ec2 instance

    start_ec2_instance()    --  Method to start ec2 instance

    stop_ec2_instance()     --  Method to stop ec2 instance

    convert_region_codes_to_names()   --  Method to get region name using region code

    Attributes
    ==========

    regions     --- List of available regions determined from ec2 resource.

AmazonEC2Helper:

    __init__()              :  Initializes AmazonCLIHelper instance with secret and access keys

    get_public_ip()         :  Method to fetch public ip of EC2

    get_private_ip()        :  Method to fetch the private ip of EC2

    get_instance_id()       :  Method to get the instance id of the vm

    get_security_group_id() :  Method to get the security group id of EC2 instance

    add_inbound_rule()      :  Add given IP into inbound rule

    remove_inbound_rule()   :  Remove given IP from inbound rule

AmazonCloudFormationHelper:

    __init__()                  :  Initialize instance of the AmazonCloudFormationHelper class

    get_cloudformation_client   :  Returns aws cloudformation client for the requst region

    check_if_stack_exist        :  Returns true if stack exist

    delete_stack                :  delete the stack

    create_stack                :  create stack

    check_stack_status          :  check the stack status, if in progress, wait for the stack to be deleted 
                                   or created

AmazonRDSCLIHelper:

    __init__            -- initializes AmazonRDSCLIHelper class with secret and access keys


    get_rds_client()    -- Returns aws rds client for the requested region

    discover_all_clusters() -- Returns a dictionary with all regions as key and discovered rds instances in
                                that region as values

    discover_all_region_clusters() -- Discover all amazon rds instances and clusters in the specified region
                                        and update clusters_dict passed



    discover_region_clusters()  -- Returns a dictionary with specified region as key and all discovered instances
                                in that region

    start_rds_instance()    --  Method to start the mentioned RDS instance

    stop_rds_instance()     --  Method to stop the mentioned RDS instance

    start_rds_cluster()     --  Method to start the mentioned cluster

    stop_rds_cluster()      --  Method to stop the mentioned cluster

    discover_cluster()      -- Returns dictionary with instance specified region as key and instance name as value if
                                found in that region


    discover_cluster_rule() --  Returns a dictionary with all available regions as key and all discovered instances
                                that match/does not match the given regex based on whether negation is true or not.


    get_clusters()          -- Returns dictionary of discovered RDS instances based on content passed.

    delete_cluster()        --  Deletes the given rds instance in that region

    delete_aurora_cluster   --  Deletes the aurora engine type cluster.

    is_instance_present()   --  Checks if the given rds instance present

    check_instance_state() --  Checks whether given rds instance is running or not

    is_cluster_present()    --  Checks if the given rds cluster present

    is_snapshot_present()   --  checks whether if the given rds instance snapshot is present in the given region

    is_cluster_snapshot_present()   --  checks whether if the given rds cluster snapshot is present in the given region

    delete_snapshot()       --  Deletes the RDS snapshot with the given snapshot identifier


AmazonRedshiftCLIHelper:

    __init__            -- initializes AmazonRedshiftCLIHelper class with secret and access keys

    get_redshift_client()   -- Returns aws redshift client for requested region

    create_redshift_cluster()   --  Creates a new redshift cluster with the specified parameters

    discover_all_clusters() -- Returns a dictionary with all regions as key and discovered redshift clusters in
                                that region as values

    discover_region_clusters()  -- Returns a dictionary with specified region as key and all discovered clusters
                                in that region

    discover_cluster()      -- Returns dictionary with cluster specified region as key and cluster as value if found
                                in that region


    discover_cluster_rule() --  Returns a dictionary with all available regions as key and all discovered clusters
                                that match/does not match the given regex based on whether negation is true or not.

    discover_cluster_tag()  --  Returns a dictionary with all available regions as key and all discovered clusters
                                as values with matching tag name and value.

    get_clusters()          -- Returns dictionary of discovered clusters based on content passed.

    delete_cluster()        --  Deletes the given redshift cluster in that region

    get_all_manual_snapshots()      -- returns the list of all manual snapshots present in the region specified

    delete_all_manual_snapshots()   -- Method to delete all manual snapshots in the given region

    delete_snapshot()               --  Method to delete a snapshot in the given region

    is_cluster_present()    --  checks if the cluster with given name present in the given region

    is_snapshot_present()   --  checks whether if the given redshift cluster snapshot is present in the given region


AmazonDocumentDBCLIHelper:

    __init__            -- initializes AmazonDocumentDBCLIHelper class with secret and access keys

    get_docdb_client()   -- Returns aws docdb client for requested region

    create_docdb_cluster()  --  Creates the DocumentDB cluster

    create_docdb_instance() --  Creates the DocumentDB instance under given cluster


    discover_all_clusters() -- Returns a dictionary with all regions as key and discovered redshift clusters in
                                that region as values

    discover_region_clusters()  -- Returns a dictionary with specified region as key and all discovered clusters
                                in that region

    discover_cluster()      -- Returns dictionary with cluster specified region as key and cluster as value if found
                                in that region

    discover_cluster_rule() --  Returns a dictionary with all available regions as key and all discovered clusters
                                that match/does not match the given regex based on whether negation is true or not.

    get_clusters()          -- Returns dictionary of discovered clusters based on content passed.

    get_cluster_instances() --  Returns set of discovered instances for the given cluster

    get_manual_snapshot_of_cluster()   --  Return the name of manual snapshot of given cluster

    delete_instance()       --  Deletes given aws docdb cluster instance in that region

    delete_cluster()        --  Deletes the given redshift cluster in that region

    delete_snapshot()       --  Deletes the given snapshot

    get_all_manual_snapshots()      -- returns the list of all manual snapshots present in the region specified

    delete_all_manual_snapshots()   -- Method to delete all manual snapshots in the given region

    start_docdb_cluster()   --  This starts the DocumentDB cluster if it is in stopped state

    stop_docdb_cluster()    --  Function to stop the DocumentDB cluster if it is available state

    is_cluster_present()    --  This checks if the cluster is available

    is_snapshot_present()   --  checks whether if the given redshift cluster snapshot is present in the given region

    delete_docdb_snapshots_of_cluster() --  This will delete all manual snapshots of given cluster

AmazonDynamoDBDCLIHelper:

    __init__            -- initializes AmazonDynamoDBCLIHelper class with secret and access keys

    initialize_client()   -- Initializes the aws boto3 client with resource type as dynamodb on given region

    get_table_object()    --  Creates the dynamodb table object for given table

    create_dynamodb_table()   --  Method to create a dynamodb table with the given name and partition key

    populate_dynamodb_table()   --  Method to populate given dynamodb with sample items

    validate_dynamodb_table()   --  Method to validate the data of the given table after restore

    run_dynamodb_backup()       --  Runs backup of the test case subclient and checks if job ran successfully

    delete_dynamodb_table()     --  Method to delete the given dynamodb table

    get_table_arn()             --  Method to return the Amazon resource number-ARN of the given table

    get_table_id()              --  Method to return the ID of the given dynamodb table

    get_read_capacity()         --  Method to return the read throughput/capacity of the given table

    get_write_capacity()        --  Method to return the write throughput/capacity of the table

    detect_change_in_capacity() --  Method to find if table's read/write capacity was changed to
                                    expected value during backup and restore

    tag_resource()              --  Method to associate AWS tags for the given list of table_names/resources

    get_number_of_decreases()   --  Method to get the number of times table's capacity was decreased

AmazonCloudDatabaseHelper:

    __init__()          --  Initializes AmazonCloudDatabaseHelper object

    populate_tc_inputs()    --  Populates common test case inputs by parsing the json tcinputs

    process_browse_response()   --  Process the browse response received and return the list of snapshots

    run_backup()             -- Runs a snapshot backup of the testcase subclient

    browse()                --  Browse the testcase's subclient backup job and return the snapshot list

    run_backup_verify()       -- Runs a snapshot backup of the testcase subclient and verifies if the snapshot
                                is present in the amazon through cli helper.

    run_restore()           -- Runs a restore job of the selected snapshot to the destination with specified restore
                                options

    run_restore_verify()    -- Runs a restore job of a random snapshot selected from the browse job with specified
                            restore options and verify if the cluster/instance is successfully restored. If cleanup
                            is specified then delete the restored cluster/instance.

    Attributes
    ==========

    cli_helper      --  Based on the testcase instance name, we get the corresponding AmazonCLIHelper class


"""

import re
import time
from datetime import datetime
from time import sleep
import pprint
import boto3
import json
from botocore.exceptions import ClientError
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase


class AmazonCLIHelper:
    """Helper class to perform Amazon operations using python boto3 CLI """

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonCLIHelper class.

            Args:

                access_key : Access key used to connect to Amazon Web Services

                secret_key : Secret Key used to connect to Amazon Web Services

        """
        self.log = logger.get_log()
        self.access_key = access_key
        self.secret_key = secret_key
        self._clients = {}

    @property
    def regions(self):
        """ Retrieves possible AWS region endpoints from ec2 client.

            Returns:
                list    --  list of all possible AWS Region endpoints.

        """
        client = boto3.client(
            'ec2',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='us-east-1')
        regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
        return regions

    def empty_cluster_dict(self):
        """ Gives a empty region cluster dict with possible regions as keys

            Args:
                None

            Returns:
                dict - dictionary with all possible regions as keys and values as empty set.
        """
        empty_clusters = {}
        for region in self.regions:
            empty_clusters[region] = set()
        return empty_clusters

    def get_client(self, region='us-east-1', service='ec2'):
        """ Returns aws client for the desired service region

            Args:

            region  -- AWS region endpoint for which we need aws service client
                default: us-east-1

            service --  AWS service we need the client for ex: ec2, redshift, rds default:
                default : ec2

            Returns:

                object  --  AWS client object

        """
        try:

            if self._clients.get(service):
                if self._clients.get(service).get(region):
                    return self._clients[service][region]
            else:
                self._clients[service] = {}

            self._clients[service][region] = boto3.client(
                service,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=region)

            return self._clients[service][region]

        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def ec2_state(self, instance_name, region='us-east-1'):
        """method to return ec2 instance state

            Args:

            instance_name   --  Name of the ec2 instance

            region          -- AWS region where ec2 client resides
                default: us-east-1

            Returns:

                string  --  State of EC2 instance
                    Possible values: ["Running", "Stopped", "Pending", "shutting-down", "terminated"]

        """
        ec2_client = self.get_client(region=region)
        return ec2_client.describe_instances(
            Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])['Reservations'][0]['Instances'][0]['State'][
            'Name']

    def start_ec2_instance(self, instance_name, region='us-east-1', wait_for_complete=True):
        """method to start ec2 instance

            Args:

            instance_name   --  Name of the ec2 instance

            region          -- AWS region where ec2 client resides
                default: us-east-1

            wait_for_complete   --  flag to determine if we need to
            wait for operation to complete
                default: True

        """
        if "running" not in self.ec2_state(instance_name, region).lower():
            ec2_client = self.get_client(region=region)
            instance_id = ec2_client.describe_instances(
                Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])['Reservations'][0][
                'Instances'][0]['InstanceId']
            ec2_client.start_instances(InstanceIds=[instance_id])
            if wait_for_complete:
                waiter = ec2_client.get_waiter('instance_running')
                waiter.wait(InstanceIds=[instance_id])

    def stop_ec2_instance(self, instance_name, region='us-east-1', wait_for_complete=True):
        """method to stop ec2 instance

            Args:

            instance_name   --  Name of the ec2 instance

            region          -- AWS region where ec2 client resides
                default: us-east-1

            wait_for_complete   --  flag to determine if we need to
            wait for operation to complete
                default: True

        """
        if "stopped" not in self.ec2_state(instance_name, region).lower():
            ec2_client = self.get_client(region=region)
            instance_id = ec2_client.describe_instances(
                Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])['Reservations'][0][
                'Instances'][0]['InstanceId']
            ec2_client.stop_instances(InstanceIds=[instance_id])
            if wait_for_complete:
                waiter = ec2_client.get_waiter('instance_stopped')
                waiter.wait(InstanceIds=[instance_id])

    def convert_region_codes_to_names(self, region_code):
        """Functions to convert the region code to name

            Args:
                region_code (str)    : region code of AWS
        """
        region_dict = {
            "us-east-2": "US East (Ohio)",
            "us-east-1": "US East (N. Virginia)",
            "us-west-1": "US West (N. California)",
            "us-west-2": "US West (Oregon)",
            "af-south-1": "Africa (Cape Town)",
            "ap-east-1": "Asia Pacific (Hong Kong)",
            "ap-south-2": "Asia Pacific (Hyderabad)",
            "ap-southeast-3": "Asia Pacific (Jakarta)",
            "ap-southeast-4": "Asia Pacific (Melbourne)",
            "ap-south-1": "Asia Pacific (Mumbai)",
            "ap-northeast-3": "Asia Pacific (Osaka)",
            "ap-northeast-2": "Asia Pacific (Seoul)",
            "ap-southeast-1": "Asia Pacific (Singapore)",
            "ap-southeast-2": "Asia Pacific (Sydney)",
            "ap-northeast-1": "Asia Pacific (Tokyo)",
            "ca-central-1": "Canada (Central)",
            "eu-central-1": "Europe (Frankfurt)",
            "eu-west-1": "Europe (Ireland)",
            "eu-west-2": "Europe (London)",
            "eu-south-1": "Europe (Milan)",
            "eu-west-3": "Europe (Paris)",
            "eu-south-2": "Europe (Spain)",
            "eu-north-1": "Europe (Stockholm)",
            "eu-central-2": "Europe (Zurich)",
            "me-south-1": "Middle East (Bahrain)",
            "me-central-1": "Middle East (UAE)",
            "sa-east-1": "South America (São Paulo)",
            "us-gov-east-1": "AWS GovCloud (US-East)",
            "us-gov-west-1": "AWS GovCloud (US-West)"
        }
        return region_dict[region_code]


class AmazonEC2Helper(AmazonCLIHelper):
    """
    Amazon helper class for EC2 machines
    """

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonEC2Helper class.

            Args:

                access_key : Access key used to connect to Amazon Web Services

                secret_key : Secret Key used to connect to Amazon Web Services

        """
        super().__init__(access_key, secret_key)

    def get_public_ip(self, instance_name=None, instance_id=None, region='us-east-1'):
        """method to fetch public IP of ec2 instance

            Args:

            instance_name(str)      :  Name of the ec2 instance
            instance_id             :  Id of the EC2 instance

            region                  : AWS region where ec2 client resides
                default: us-east-1
                """
        ec2_client = self.get_client(region=region)
        if instance_name:
            self.log.info(f"Getting IP for {instance_name} in {region}")
            return ec2_client.describe_instances(
                Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])['Reservations'][0]['Instances'][0][
                'PublicIpAddress']
        else:
            self.log.info(f"Getting IP for {instance_id} in {region}")
            return ec2_client.describe_instances(
                InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['PublicIpAddress']

    def get_private_ip(self, instance_name=None, instance_id=None, region='us-east-1'):
        """method to fetch private IP of ec2 instance

            Args:

            instance_name   :  Name of the ec2 instance
            instance_id     :  Id of the EC2 instance

            region          : AWS region where ec2 client resides
                default: us-east-1
                """
        ec2_client = self.get_client(region=region)
        if instance_name:
            self.log.info(f"Getting IP for {instance_name} in {region}")
            return ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])[
                'Reservations'][0]['Instances'][0]['PrivateIpAddress']
        else:
            self.log.info(f"Getting IP for {instance_id} in {region}")
            return ec2_client.describe_instances(
                InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['PrivateIpAddress']

    def get_private_dns_name(
            self,
            instance_name=None,
            instance_id=None,
            region='us-east-1'):
        """method to fetch private dns name of ec2 instance

            Args:

            instance_name   :  Name of the ec2 instance
            instance_id     :  Id of the EC2 instance

            region          : AWS region where ec2 client resides
                default: us-east-1
                """
        ec2_client = self.get_client(region=region)
        if instance_name:
            self.log.info(f"Getting IP for {instance_name} in {region}")
            return ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])[
                'Reservations'][0]['Instances'][0]['PrivateDnsName']
        else:
            self.log.info(f"Getting IP for {instance_id} in {region}")
            return ec2_client.describe_instances(
                InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['PrivateDnsName']

    def get_instance_id(self, instance_name, region='us-east-1'):
        """method to fetch instance id of ec2 instance using instance name

            Args:

            instance_name   :  Name of the ec2 instance

            region          : AWS region where ec2 client resides
                default: us-east-1
                        """
        self.log.info("Fetching instance ID")
        ec2_client = self.get_client(region=region)
        return ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [
            instance_name]}])['Reservations'][0]['Instances'][0]['InstanceId']

    def get_instance_id_with_state(
            self,
            instance_name,
            region='us-east-1',
            instance_state='running'):
        """method to fetch instance id of ec2 instance using instance name and ec2 instance state

            Args:

            instance_name   :  Name of the ec2 instance

            region          : AWS region where ec2 client resides
                default: us-east-1

            instance_state  :  state of the ec instance, eg: running, stopped
                        """
        self.log.info("Fetching instance ID")
        ec2_client = self.get_client(region=region)
        return ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}, {
            'Name': 'instance-state-name', 'Values': [instance_state]}])['Reservations'][0]['Instances'][0]['InstanceId']

    def get_security_group_id(self, instance_name, region='us-east-1'):
        """method to fetch security of group id of ec2 instance

            Args:

            instance_name   :  Name of the ec2 instance

            region          : AWS region where ec2 client resides
                default: us-east-1
                        """
        self.log.info("Fetching Security Groupid")
        ec2_client = self.get_client(region=region)
        instance_id = self.get_instance_id(instance_name, region)
        return ec2_client.describe_instances(
            InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['SecurityGroups'][0]['GroupId']

    def add_inbound_rule(self, instance_name, region, inbound_ip, inbound_port=22, protocol="tcp"):
        """method to add new IP as inbound rule to ec2 instance

            Args:

            instance_name       :  Name of the ec2 instance

            region              : AWS region where ec2 client resides
                default: us-east-1

            inbound_ip(str)     : IP to be added to inbound rule
            inbound_port        :  port number
            protocol            :  Type of custom protocol


                        """
        self.log.info("Adding Inbound rules")
        ec2_client = self.get_client(region=region)
        security_group_id = self.get_security_group_id(instance_name, region)
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': protocol,
                    'FromPort': inbound_port,
                    'ToPort': inbound_port,
                    'IpRanges': [{'CidrIp': inbound_ip + '/32'}]
                }
            ]
        )

    def remove_inbound_rule(self, instance_name, region, inbound_ip, inbound_port=22, protocol="tcp"):
        """method to remove an IP as inbound rule to ec2 instance

            Args:

            instance_name       :   Name of the ec2 instance

            region              :   AWS region where ec2 client resides
                default: us-east-1

            inbound_ip(str)     :   IP to be added to inbound rule
            inbound_port        :   port number
            prorocol            :   Type of xustom protocol


            """
        ec2_client = self.get_client(region=region)
        security_group_id = self.get_security_group_id(instance_name, region)
        ec2_client.revoke_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': protocol,
                    'FromPort': inbound_port,
                    'ToPort': inbound_port,
                    'IpRanges': [{'CidrIp': inbound_ip + '/32'}]
                }
            ]
        )


class AmazonCloudFormationHelper(AmazonCLIHelper):
    """
    Amazon helper class for cloudformation client
    """

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonCloudFormationHelper class.

            Args:

                access_key : Access key used to connect to Amazon Web Services

                secret_key : Secret Key used to connect to Amazon Web Services

        """
        super().__init__(access_key, secret_key)

    def get_cloudformation_client(self, region):
        """ Returns aws rds client for the desired service region

            Args:

                region -- region for which we need rds client for

            Returns:

                object -- aws cloudformation client object
        """
        return boto3.client(
            'cloudformation',
            region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key)

    def check_if_stack_exist(self, stack_name, region_name):
        """method to check whether stack name exist

            Args:

            stack_name		:  name of the stack

            region_name     :  Name of the region
        """
        self.log.info("check if stack name %s exist", stack_name)
        cfn_client = self.get_cloudformation_client(region=region_name)
        # -- Check if this stack name already exists
        stack_list = cfn_client.describe_stacks()["Stacks"]
        stack_exists = False
        for stack_cf in stack_list:
            if stack_name.strip() == stack_cf["StackName"].strip():
                self.log.info("Stack " + stack_name + " already exists.")
                stack_exists = True
        return stack_exists

    def delete_stack(self, stack_name, region_name):
        """"delete existing stack
            Args:

            stack_name		:  name of the stack

            region_name     :  Name of the region
		"""
        self.log.info("delete stack  %s", stack_name)
        cfn_client = self.get_cloudformation_client(region=region_name)
        cfn_client.delete_stack(StackName=stack_name)
        ss_status = self.check_stack_status(stack_name, region_name)
        if ss_status == "STACK_DELETED":
            self.log.info("stack %s is deleted", stack_name)

    def create_stack(
            self,
            stack_name,
            template_url,
            parameters,
            region_name,
            disablerollback=True):
        """ create stack using input parameters and urls
            Args:

            stack_name		:  name of the stack

            template_url    :  template url

            parameters      :  input parameters

            region_name     :  Name of the region
		"""
        self.log.info("create stack %s", stack_name)
        cfn_client = self.get_cloudformation_client(region=region_name)
        result_ss = cfn_client.create_stack(
            StackName=stack_name,
            DisableRollback=disablerollback,
            TemplateURL=template_url,
            Parameters=parameters,
            Capabilities=["CAPABILITY_NAMED_IAM"])
        self.log.info("output from API call: %s", result_ss)

        status_cur_ss = self.check_stack_status(stack_name, region_name)
        if status_cur_ss == "CREATE_COMPLETE":
            print("Stack " + stack_name + " created successfully.")
        else:
            raise exception("Unexpected error: %s", stack_name)

    def check_stack_status(self, stack_name, region_name):
        """method to check the stack status

            Args:

            stack_name		:  name of the stack

            region_name     :  Name of the region
            """
        cfn_client = self.get_cloudformation_client(region=region_name)
        stacks = cfn_client.describe_stacks(StackName=stack_name)["Stacks"]
        stack_val = stacks[0]
        status_cur_ss = stack_val["StackStatus"]
        self.log.info(
            "Current status of stack " +
            stack_val["StackName"] +
            ": " +
            status_cur_ss)
        for ln_loop in range(1, 9999):
            if "IN_PROGRESS" in status_cur_ss:	
                self.log.info(
                    "\rWaiting for status update %s...",
                    str(ln_loop))
                time.sleep(20)  # pause 20 seconds
                try:
                    stacks_ss = cfn_client.describe_stacks(
                        StackName=stack_name)["Stacks"]
                except BaseException:
                    self.log.info(
                        "Stack " +
                        stack_val["StackName"] +
                        " no longer exists")
                    status_cur_ss = "STACK_DELETED"
                    break

                stack_ss_val = stacks_ss[0]
                if stack_ss_val["StackStatus"] != status_cur_ss:
                    status_cur_ss = stack_ss_val["StackStatus"]
                    self.log.info(
                        "Updated status of stack " +
                        stack_ss_val["StackName"] +
                        ": " +
                        status_cur_ss)
                    break
            else:
                break
        return status_cur_ss


class AmazonRDSCLIHelper(AmazonCLIHelper):
    """ Helper class derived from AmazonCLIHelper class to perform Amazon RDS operations using python boto3 CLI
        Does not support discovery and backup of aurora clusters.
    """

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonRDSCLIHelper class.

            Args:

            access_key : Access Key used to connect to the Amazon Web Services
                default: None

            secret_key : Secret Key used to connect to the Amazon Web Services
                default: None

        """
        super().__init__(access_key, secret_key)
        self.clusters_dict = {}

    def get_rds_client(self, region):
        """ Returns aws rds client for the desired service region

                Args:

                    region -- region for which we need rds client for

                Returns:

                    object -- aws rds client object
        """
        return self.get_client(region, 'rds')

    def discover_all_clusters(self, availability=True, clusters_dict=None):
        """ Discover all amazon rds instances across all regions and update instances_dict passed

            Args:

                availability -- discover only available rds instances

                clusters_dict -- Discover all instances and update the passed cluster dictionary

            Returns:

                dict    --  dictionary of region : instances based on rds cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.info("Discovering rds instances across all regions")
            for region in self.regions:
                rds_client = self.get_rds_client(region)
                response = rds_client.describe_db_instances()
                instances = response['DBInstances']
                for instance in instances:
                    if 'docdb' not in instance['Engine'] and 'aurora' not in instance['Engine']:
                        self.log.info(
                            "Found Instance [%s] Region [%s] Status [%s]",
                            instance['DBInstanceIdentifier'],
                            region,
                            instance['DBInstanceStatus'])
                    if availability:
                        if instance['DBInstanceStatus'].lower() == "available":
                            clusters_dict[region].add(instance['DBInstanceIdentifier'])
                    else:
                        clusters_dict[region].add(instance['DBInstanceIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_region_clusters(self, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover all amazon rds instances in the specified region and update clusters_dict passed

                Args:

                region      -- discover rds instances in the specified region
                    default - us-east-1

                availability -- discover only available rds instances
                    default - True

                clusters_dict -- Discover all instances and update the passed cluster dictionary
                    default - None
            Returns:

                dict    --  dictionary of region : instances based on rds instance availability

        """
        try:
            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            rds_client = self.get_rds_client(region)
            response = rds_client.describe_db_instances()
            instances = response['DBInstances']
            for instance in instances:
                if 'docdb' not in instance['Engine'] and 'aurora' not in instance['Engine']:
                    self.log.info(
                        "Found Instance [%s] Region [%s] Status [%s]",
                        instance['DBInstanceIdentifier'],
                        region,
                        instance['DBInstanceStatus'])
                if availability:
                    if instance['DBInstanceStatus'].lower() == "available":
                        clusters_dict[region].add(instance['DBInstanceIdentifier'])
                else:
                    clusters_dict[region].add(instance['DBInstanceIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_all_region_clusters(self, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover all amazon rds instances and clusters in the specified region and update clusters_dict passed

                Args:

                region      -- discover rds instances in the specified region
                    default - us-east-1

                availability -- discover only available rds instances
                    default - True

                clusters_dict -- Discover all instances and update the passed cluster dictionary
                    default - None
            Returns:

                dict    --  dictionary of region : instances based on rds instance availability

        """
        try:
            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            rds_client = self.get_rds_client(region)
            response = rds_client.describe_db_instances()
            instances = response['DBInstances']
            for instance in instances:
                self.log.info(
                    "Found Instance [%s] Region [%s] Status [%s]",
                    instance['DBInstanceIdentifier'],
                    region,
                    instance['DBInstanceStatus'])
                if availability:
                    if instance['DBInstanceStatus'].lower() == "available":
                        clusters_dict[region].add(instance['DBInstanceIdentifier'])
                else:
                    clusters_dict[region].add(instance['DBInstanceIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def start_rds_instance(self, region, instance_identifier, wait_time_for_completion=15):
        """
        starts the RDS instance in AWS
        Args:
            region                      (str)   :   Region where the RDS instance Hosted
            instance_identifier          (str)   :   Name of the instance
            wait_time_for_completion    (int)   :   Minutes to wait to start the instance

        Raises:
            Exception: If RDS instance is not found
        """
        try:
            rds_client = self.get_rds_client(region)
            response = rds_client.start_db_instance(
                DBInstanceIdentifier=instance_identifier
            )
            if response.get("DBInstance", {}).get("DBInstanceIdentifier", "") == instance_identifier:
                while True:
                    is_started = True
                    wait_response = rds_client.describe_db_instances()
                    wait_instances = wait_response.get("DBInstances", {})
                    for wait_instance in wait_instances:
                        if wait_instance.get("DBInstanceIdentifier", "") == instance_identifier and 'available' not in \
                                wait_instance.get("DBInstanceStatus", "").lower():
                            self.log.info(f"Waiting for instance {instance_identifier} to be started.")
                            is_started = False
                            break
                    if is_started:
                        self.log.info(f"instance {instance_identifier} is started successfully")
                        break
                    if wait_time_for_completion <= 0:
                        self.log.info(
                            "Exiting from start instance method as the wait time is over, please track the instance status manually")
                        break
                    wait_time_for_completion -= 1
                    time.sleep(60)

        except ClientError as err:
            self.log.debug(f"instance {instance_identifier} not found in region {region}")
            raise err

    def stop_rds_instance(self, region, instance_identifier, wait_time_for_completion=15):
        """

                stops the Instance of rds
                Args:
                    region                      (str)   :   Region where the RDS instance Hosted
                    instance_identifier          (str)   :   Name of the instance
                    wait_time_for_completion    (int)   :   Minutes to wait to stop the instance

                Raises:
                    Exception: If RDS instance is not found
                """
        try:
            rds_client = self.get_rds_client(region)
            response = rds_client.stop_db_instance(
                DBInstanceIdentifier=instance_identifier
            )
            if response.get("DBInstance", {}).get("DBInstanceIdentifier", "") == instance_identifier:
                while True:
                    is_started = True
                    wait_response = rds_client.describe_db_instances()
                    wait_instances = wait_response.get("DBInstances", {})
                    for wait_instance in wait_instances:
                        if wait_instance.get("DBInstanceIdentifier", "") == instance_identifier and 'stopped' not in \
                                wait_instance.get("DBInstanceStatus", "").lower():
                            self.log.info(f"Waiting for instance {instance_identifier} to be stopped.")
                            is_started = False
                            break
                    if is_started:
                        self.log.info(f"Instance {instance_identifier} is stopped successfully")
                        break
                    if wait_time_for_completion <= 0:
                        self.log.info(
                            "Exiting from stop instance method as the wait time is over, please track the instance status manually")
                        break
                    wait_time_for_completion -= 1
                    time.sleep(60)
        except ClientError as err:
            self.log.debug(f"Instance {instance_identifier} not found in region {region}")
            raise err

    def start_rds_cluster(self, region, cluster_identifier, wait_time_for_completion=15):
        """
        Starts the rds cluster
        Args:
            region                      (str)   :   Region where the RDS cluster Hosted
            cluster_identifier          (str)   :   Name of the cluster
            wait_time_for_completion    (int)   :   Minutes to wait to start the cluster

        Raises:
            Exception: If RDS cluster is not found

        """
        try:
            rds_client = self.get_rds_client(region)
            response = rds_client.start_db_cluster(
                DBClusterIdentifier=cluster_identifier
            )
            if response['DBCluster']['DBClusterIdentifier'] == cluster_identifier:
                while True:
                    is_started = True
                    wait_response = rds_client.describe_db_clusters()
                    wait_clusters = wait_response['DBClusters']
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBClusterIdentifier'] == cluster_identifier and 'available' not in \
                                wait_cluster['Status'].lower():
                            self.log.info(f"Waiting for cluster {cluster_identifier} to be started.")
                            is_started = False
                            break
                    if is_started:
                        self.log.info(f"Cluster {cluster_identifier} is started successfully")
                        break
                    if wait_time_for_completion <= 0:
                        self.log.info(
                            "Exiting from start cluster method as the wait time is over, please track the cluster status manually")
                        break
                    wait_time_for_completion -= 1
                    time.sleep(60)
        except ClientError as err:
            self.log.debug(f"Cluster {cluster_identifier} not found in region {region}")
            raise err

    def stop_rds_cluster(self, region, cluster_identifier, wait_time_for_completion=15):
        """

        stops the cluster of rds
        Args:
            region                      (str)   :   Region where the RDS cluster Hosted
            cluster_identifier          (str)   :   Name of the cluster
            wait_time_for_completion    (int)   :   Minutes to wait to stop the cluster

        Raises:
            Exception: If RDS cluster is not found
        """
        try:
            rds_client = self.get_rds_client(region)
            response = rds_client.stop_db_cluster(
                DBClusterIdentifier=cluster_identifier
            )
            if response['DBCluster']['DBClusterIdentifier'] == cluster_identifier:
                while True:
                    is_started = True
                    wait_response = rds_client.describe_db_clusters()
                    wait_clusters = wait_response['DBClusters']
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBClusterIdentifier'] == cluster_identifier and 'stopped' not in \
                                wait_cluster['Status'].lower():
                            self.log.info(f"Waiting for cluster {cluster_identifier} to be stopped.")
                            is_started = False
                            break
                    if is_started:
                        self.log.info(f"Cluster {cluster_identifier} is stopped successfully")
                        break
                    if wait_time_for_completion <= 0:
                        self.log.info(
                            "Exiting from stop cluster method as the wait time is over, please track the cluster status manually")
                        break
                    wait_time_for_completion -= 1
                    time.sleep(60)
        except ClientError as err:
            self.log.debug(f"Cluster {cluster_identifier} not found in region {region}")
            raise err

    def discover_cluster(self, name, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover specified rds instance in the specified region and update clusters_dict passed

                Args:

                name        --  Name of the rds instance

                region      -- discover rds instances in the specified region
                    default: us-east-1

                availability -- discover only available rds instances
                    default: True

                clusters_dict -- Discover all instances and update the passed cluster dictionary
                    default: None

            Returns:

                dict    --  dictionary of region : instances based on rds instances availability

        """
        try:
            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            rds_client = self.get_rds_client(region)
            response = rds_client.describe_db_instances()
            instances = response['DBInstances']
            for instance in instances:
                if 'docdb' not in instance['Engine'] and 'aurora' not in instance['Engine']:
                    self.log.info(
                        "Found Instance [%s] Region [%s] Status [%s]",
                        instance['DBInstanceIdentifier'],
                        region,
                        instance['DBInstanceStatus'])
                if availability:
                    if instance['DBInstanceStatus'].lower() == "available" or \
                            instance['DBInstanceStatus'].lower() == "backing-up":
                        clusters_dict[region].add(instance['DBInstanceIdentifier'])
                else:
                    clusters_dict[region].add(instance['DBInstanceIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_cluster_rule(self, regex, negation=False, availability=True, clusters_dict=None):
        """ Discover rds instances that match the specified regex expression.

                Args:

                regex        -- discover all instances that has name that matches the regex.

                negation     -- discover all instances that doesn't match the regex pattern
                    default: True

                availability -- discover only available rds instances
                    default: True

                clusters_dict -- Discover all instances and update the passed cluster dictionary
                    default: None

            Returns:

                dict    --  dictionary of region : instances based on rds instances availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            for region in self.regions:
                rds_client = self.get_rds_client(region)
                response = rds_client.describe_db_instances()
                instances = response['DBInstances']
                for instance in instances:
                    if 'docdb' not in instance['Engine'] and 'aurora' not in instance['Engine']:
                        instance_name = instance['DBInstanceIdentifier']
                        if re.search(regex, instance_name) ^ negation:
                            self.log.info(
                                "Found Instance [%s] Region [%s] Status [%s]",
                                instance['DBInstanceIdentifier'],
                                region,
                                instance['DBInstanceStatus'])
                            if availability:
                                if instance['DBInstanceStatus'].lower() == "available":
                                    clusters_dict[region].add(instance['DBInstanceIdentifier'])
                            else:
                                clusters_dict[region].add(instance['DBInstanceIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def get_clusters(self, content=None, availability=True):
        """ Returns aws rds instances based on the content passed

                Args:

                content  -- list of dynamic cloud entity content which we can set on the subclient content
                    default: None

                availability -- discover only available rds instances
                    default: True

                    Example:

                            -- content to select all rds instances across all available regions
                            [
                                {
                                    'type': 'root'
                                }
                            ]

                            -- content to select based on region, cluster name, tag rule, regex expressions
                            [
                                {
                                    'type': 'instance',
                                    'name': 'rds-instance-1',
                                    'path': 'us-east-2'
                                },
                                {
                                    'type': 'region',
                                    'name': 'us-east-1'
                                },
                                {
                                    'type' : 'instanceRule',
                                    'name' : '*instance*' (regex expression to select or filter instances),
                                    'negation' : true or false
                                }
                            ]

            Returns:

                dict(region:set)  --  dict of rds instance objects per region that matches availability status.

        """
        try:
            self.clusters_dict = self.empty_cluster_dict()
            self.log.info("Discovering RDS instances based on the content passed : %s", content)
            for item in content:

                if item['type'] == 'root':
                    self.discover_all_clusters(availability, self.clusters_dict)
                    return self.clusters_dict

                if item['type'] == 'region':
                    region = item['name']
                    self.discover_region_clusters(region, True, self.clusters_dict)

                if item['type'] == 'instance':
                    region = item['path']
                    name = item['name']
                    self.discover_cluster(name, region, True, self.clusters_dict)

                if item['type'] == 'instanceRule':
                    name = item['name']
                    negation = item['negation']
                    self.discover_cluster_rule(name, negation, True, self.clusters_dict)

            return self.clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def delete_cluster(self, cluster, region):
        """ Delete the rds instance in the given region

                Args:

                    cluster   --  name of rds instance

                    region    --  region in which the instance exists

                Returns:

                    None    -- If deletion is successful.

                    Exception   -- If the deletion is unsuccessful
        """
        try:
            self.log.info("Checking if RDS instance [%s] exists", cluster)
            cluster_dict = self.discover_cluster(cluster, region, False)
            if cluster not in cluster_dict[region]:
                self.log.info("RDS Instance %s not found in AWS. Deletion is successful.", cluster)
            else:
                rds_client = self.get_rds_client(region)
                is_available = False
                while True:
                    wait_response = rds_client.describe_db_instances(DBInstanceIdentifier=cluster)
                    wait_instances = wait_response['DBInstances']
                    for wait_instance in wait_instances:
                        if 'docdb' not in wait_instance['Engine'] and 'aurora' not in wait_instance['Engine']:
                            if wait_instance['DBInstanceIdentifier'] == cluster and \
                                    wait_instance['DBInstanceStatus'].lower() == 'available':
                                self.log.info("Instance [%s] to be in available state.", cluster)
                                is_available = True
                                break
                            else:
                                self.log.info(
                                    "Waiting for instance [%s][%s] to be in available state.", cluster,
                                    wait_instance['DBInstanceStatus'])
                                break
                    if is_available:
                        break
                    time.sleep(60)

                response = rds_client.delete_db_instance(
                    DBInstanceIdentifier=cluster,
                    SkipFinalSnapshot=True)
                if response['DBInstance']['DBInstanceIdentifier'] == cluster:
                    while True:
                        wait_response = rds_client.describe_db_instances()
                        wait_clusters = wait_response['DBInstances']
                        is_deleted = True
                        for wait_cluster in wait_clusters:
                            if wait_cluster['DBInstanceIdentifier'] == cluster:
                                self.log.info("Waiting for instance %s to be deleted.", cluster)
                                is_deleted = False
                                break
                        if is_deleted:
                            self.log.info("Instance %s is deleted successfully", cluster)
                            break
                        time.sleep(60)
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def delete_aurora_cluster(self, cluster, region):
        """
        Deletes aurora instance and cluster

        Args:
            cluster (str)   : Name of the cluster that need to be deleted
            region  (str)   : Region code where the cluster is hosted
        """
        try:
            self.log.info(f"Checking if RDS instance {cluster} exists")
            cluster_dict = self.discover_cluster(cluster, region, False)
            rds_client = self.get_rds_client(region)
            if cluster not in cluster_dict[region]:
                self.log.info("RDS Instance %s not found in AWS. Deletion is successful.", cluster)
            else:
                is_available = False
                try:
                    self.start_rds_instance(region, cluster)
                except ClientError as err:
                    self.log.error(err)
                while True:
                    wait_response = rds_client.describe_db_instances(DBInstanceIdentifier=cluster)
                    wait_instances = wait_response['DBInstances']
                    for wait_instance in wait_instances:
                        if wait_instance['DBInstanceIdentifier'] == cluster and \
                                wait_instance['DBInstanceStatus'].lower() == 'available':
                            self.log.info(f"Instance {cluster} to be in available state.")
                            is_available = True
                            break
                        else:
                            self.log.info(
                                f"Waiting for instance {cluster}-{wait_instance['DBInstanceStatus']} to be in available state.")
                            break
                    if is_available:
                        break
                    time.sleep(60)

                response = rds_client.delete_db_instance(
                    DBInstanceIdentifier=cluster,
                    SkipFinalSnapshot=True)
                if response['DBInstance']['DBInstanceIdentifier'] == cluster:
                    for _ in range(15):
                        wait_response = rds_client.describe_db_instances()
                        wait_clusters = wait_response['DBInstances']
                        is_deleted = True
                        for wait_cluster in wait_clusters:
                            if wait_cluster['DBInstanceIdentifier'] == cluster:
                                self.log.info(f"Waiting for instance {cluster} to be deleted.")
                                is_deleted = False
                                break
                        if is_deleted:
                            self.log.info(f"Instance {cluster} is deleted successfully")
                            break
                        time.sleep(60)
            rds_clusters = rds_client.describe_db_clusters(DBClusterIdentifier=cluster)
            set_db_clusters = set()
            for resp_cluster in rds_clusters['DBClusters']:
                set_db_clusters.add(resp_cluster['DBClusterIdentifier'])
            if cluster not in set_db_clusters:
                self.log.info(f"RDS Instance {cluster} not found in AWS. Deletion is successful.")
            else:
                is_available = False
                try:
                    self.start_rds_cluster(region, cluster)
                except ClientError as err:
                    self.log.error(err)
                while True:
                    wait_response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster)
                    wait_clusters = wait_response['DBClusters']
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBClusterIdentifier'] == cluster and \
                                wait_cluster['Status'].lower() == 'available':
                            self.log.info(f"Instance {cluster} to be in available state.")
                            is_available = True
                            break
                        else:
                            self.log.info(
                                f"Waiting for instance {cluster} {wait_cluster['Status']} to be in available state.")
                            break
                    if is_available:
                        break
                    time.sleep(60)

                response = rds_client.delete_db_cluster(
                    DBClusterIdentifier=cluster,
                    SkipFinalSnapshot=True)
                if response['DBCluster']['DBClusterIdentifier'] == cluster:
                    while True:
                        wait_response = rds_client.describe_db_clusters()
                        wait_clusters = wait_response['DBClusters']
                        is_deleted = True
                        for wait_cluster in wait_clusters:
                            if wait_cluster['DBClusterIdentifier'] == cluster:
                                self.log.info(f"Waiting for cluster {cluster} to be deleted.")
                                is_deleted = False
                                break
                        if is_deleted:
                            self.log.info(f"Instance {cluster} is deleted successfully")
                            break
                        time.sleep(60)
        except ClientError as err:
            self.log.exception(f"Unexpected error: {err}")
            raise err

    def is_instance_present(self, region, instance_name, availability=True):
        """ checks if the instance with given name present in the given region

                    Args:

                        region          --  region in which the instance is present

                        instance_name    --  name of RDS instance

                        availability    --  if True return only available instance
                                            else return if instance exists
                                    default: True


                    Returns:

                        bool -- Is instance in available state or present(based on input)

                    Raises:
                        Exception: If boto3 could not fetch details


                """
        try:
            rds_client = self.get_rds_client(region)
            instances = rds_client.describe_db_instances()['DBInstances']
            for instance in instances:
                if instance['DBInstanceIdentifier'] == instance_name:
                    if availability:
                        if instance['DBInstanceStatus'].lower() == 'available':
                            self.log.info(
                                f"instance {instance_name} {region} is found on Amazon in available state")
                            return True
                    else:
                        self.log.info(
                            f"instance {instance_name} {region} is found on Amazon in {instance['DBInstanceStatus']} state")
                        return True
            return False
        except ClientError as err:
            self.log.exception(f"Unexpected error: {err}")
            raise err

    def check_instance_state(self, region, instance_name):
        """ checks if the instance with given name is currently running or not.
        Should be used after checking if the instance is present or not

                            Args:
                                region          --  region in which the instance is present
                                instance_name    --  name of RDS instance

                            Returns:
                                bool -- Is instance in available state or stopped

                            Raises:
                                Exception: If boto3 could not fetch details

                        """
        try:
            rds_client = self.get_rds_client(region)
            instances = rds_client.describe_db_instances()['DBInstances']
            for instance in instances:
                if instance['DBInstanceIdentifier'] == instance_name:

                    if instance['DBInstanceStatus'].lower() == 'available':
                        self.log.info(
                            f"instance {instance_name} {region} is found on Amazon in available state")
                        return True
                    else:
                        self.log.info(
                            f"instance {instance_name} {region} is found on Amazon in {instance['DBInstanceStatus']} state")
                        return False

        except ClientError as err:
            self.log.exception(f"Unexpected error: {err}")
            raise err

    def is_cluster_present(self, region, cluster_name, availability=True):
        """ checks if the cluster with given name present in the given region

            Args:

                region          --  region in which the cluster is present

                cluster_name    --  name of RDS cluster

                availability    --  if True return only available cluster
                                    else return if cluster exists

        """
        try:
            rds_client = self.get_rds_client(region)
            clusters = rds_client.describe_db_clusters()['DBClusters']
            for cluster in clusters:
                if cluster['DBClusterIdentifier'] == cluster_name:
                    if availability:
                        if cluster['Status'].lower() == 'available':
                            self.log.info(
                                f"Cluster {cluster_name} {region} is found on Amazon in available state")
                            return True
                    else:
                        self.log.info(
                            f"Cluster {cluster_name} {region} is found on Amazon in {cluster['Status']} state")
                        return True
            return False
        except ClientError as err:
            self.log.debug(f"Cluster {cluster_name} not found in region {region}")
            raise err

    def is_snapshot_present(self, name, region, availability=True):
        """ Check if aws rds instance snapshot exists in a given region

                Args:

                    name   --  name of rds instance snapshot

                    region          --  region in which the snapshot is present

                    availability    --  if True return only available snapshots
                                        else return if snapshot exists

                Returns:

                    bool    --  True if snapshot exists (and available) and False if snapshot
                    doesn't exist

                    Exception -- if it is not part of AWS CLI botocore exception
        """
        try:
            rds_client = self.get_rds_client(region)
            response = rds_client.describe_db_snapshots(DBSnapshotIdentifier=name)
            snapshots = response['DBSnapshots']
            for snapshot in snapshots:
                if snapshot['DBSnapshotIdentifier'] == name:
                    if availability:
                        if snapshot['Status'].lower() == 'available':
                            self.log.info("Snapshot [%s][%s] is found on Amazon in available state", name, region)
                            return True
                    else:
                        self.log.info(
                            "Snapshot [%s][%s] is found on Amazon in %s state",
                            name,
                            region,
                            snapshot['Status'])
                        return True
            return False
        except ClientError:
            self.log.debug("Snapshot %s not found in region %s", name, region)
            return False
        except Exception as err:
            self.log.exception("Unknown exception %s", err)
            raise err

    def is_cluster_snapshot_present(self, name, region, availability=True):
        """ Check if aws rds cluster snapshot exists in a given region

                Args:

                    name   --  name of rds instance snapshot

                    region          --  region in which the snapshot is present

                    availability    --  if True return only available snapshots
                                        else return if snapshot exists

                Returns:

                    bool    --  True if snapshot exists (and available) and False if snapshot
                    doesn't exist

                    Exception -- if it is not part of AWS CLI botocore exception
        """
        try:
            rds_client = self.get_rds_client(region)
            response = rds_client.describe_db_cluster_snapshots()
            snapshots = response['DBClusterSnapshots']
            for snapshot in snapshots:
                if snapshot['DBClusterSnapshotIdentifier'] == name:
                    if availability:
                        if snapshot['Status'].lower() == 'available':
                            self.log.info("Snapshot [%s][%s] is found on Amazon in available state", name, region)
                            return True
                    else:
                        self.log.info(
                            "Snapshot [%s][%s] is found on Amazon in %s state",
                            name,
                            region,
                            snapshot['Status'])
                        return True
            return False
        except ClientError:
            self.log.debug("Snapshot %s not found in region %s", name, region)
            return False
        except Exception as err:
            self.log.exception("Unknown exception %s", err)
            raise err

    def delete_snapshot(self, snapshot_identifier, region, is_cluster_snapshot=False):
        """Deletes the RDS snapshot with the given snapshot identifier
        Args:
            snapshot_identifier (str)   -- The snapshot ID of snapshot

            region  (str)   -- Name of the region

            is_cluster_snapshot  (bool)   --  Type of snapshot
                default: False

        Returns:
            None

        Raises:
            Exception - if incorrect snapshot identifier was passed
                        if snapshot could not be deleted on AWS

        """
        try:
            rds_client = self.get_rds_client(region)
            if not is_cluster_snapshot:
                rds_client.delete_db_snapshot(DBSnapshotIdentifier=snapshot_identifier)
            else:
                rds_client.delete_db_cluster_snapshot(DBClusterSnapshotIdentifier=snapshot_identifier)
            self.log.info("Snapshot [%s]: deleted successfully", snapshot_identifier)
        except ClientError as err:
            self.log.exception("Snapshot with identifier [%s] "
                               "could not be deleted", snapshot_identifier)
            raise err


class AmazonRedshiftCLIHelper(AmazonCLIHelper):
    """ Helper class derived from AmazonCLIHelper class to perform Amazon Redshift operations using python boto3 CLI"""

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonRedshiftCLIHelper class.

            Args:

            access_key : Access Key used to connect to the Amazon Web Services

            secret_key : Secret Key used to connect to the Amazon Web Services

        """
        super().__init__(access_key, secret_key)
        self.clusters_dict = {}

    def get_redshift_client(self, region):
        """ Returns aws redshift client for the desired service region

                Args:

                    region -- region for which we need redshift client for

                Returns:

                    object -- aws redshift client object
        """
        return self.get_client(region, 'redshift')

    def create_redshift_cluster(
            self, region, cluster_identifier, node_type, master_username, master_password,
            cluster_type='multi-node', number_of_nodes=2, wait_time_for_creation=15):
        """ Creates a new redshift cluster with the specified parameters

            Args:

                region(str)             -- region in which cluster needs to be created

                cluster_identifier(str) -- A unique identifier for the cluster.
                    You use this identifier to refer to the cluster for any subsequent
                    cluster operations such as deleting or modifying.
                    The identifier also appears in the Amazon Redshift console.

                node_type(str)          --  The node type to be provisioned for the cluster.

                    Valid Values:
                        ds2.xlarge | ds2.8xlarge | dc1.large | dc1.8xlarge | dc2.large
                        | dc2.8xlarge | ra3.4xlarge | ra3.16xlarge

                master_username(str)    --  The user name associated with the
                    master user account for the cluster that is being created

                master_password(str)    --  The password associated with the master
                    user account for the cluster that is being created

                cluster_type(str)       --  The type of the cluster. When cluster
                    type is specified as

                    single-node : the number_of_nodes parameter is not required.
                    multi-node  : the number_of_nodes parameter is required.

                    Valid Values: multi-node | single-node

                    default: 'multi-node'

                number_of_nodes(int)    --  The number of compute nodes in the cluster.
                    This parameter is required when the cluster_type parameter is
                    specified as multi-node .

                    default: 2

                wait_time_for_creation(int) --  Maximum number of MINUTES method needs
                to wait for cluster creation before exiting from wait.
                Provide the value as 0 to immediately exit from method
                without waiting for the creation.

                    default: 15

        """
        try:
            if "single-node" in cluster_type:
                number_of_nodes = 1
            redshift_client = self.get_redshift_client(region)
            response = redshift_client.create_cluster(
                ClusterIdentifier=cluster_identifier,
                NodeType=node_type,
                MasterUsername=master_username,
                MasterUserPassword=master_password,
                ClusterType=cluster_type,
                NumberOfNodes=number_of_nodes)
            if response['Cluster']['ClusterIdentifier'] == cluster_identifier:
                while True:
                    wait_response = redshift_client.describe_clusters()
                    wait_clusters = wait_response['Clusters']
                    is_created = True
                    for wait_cluster in wait_clusters:
                        if wait_cluster['ClusterIdentifier'] == cluster_identifier and 'available' not in wait_cluster[
                            'ClusterStatus'].lower():
                            self.log.info("Waiting for cluster %s to be created.", cluster_identifier)
                            is_created = False
                            break
                    if is_created:
                        self.log.info("Cluster %s is created successfully", cluster_identifier)
                        break
                    if wait_time_for_creation <= 0:
                        self.log.info(
                            "Exiting from create cluster method as the wait time is over, please track the cluster status manually")
                        break
                    wait_time_for_creation -= 1
                    time.sleep(60)

        except ClientError as err:
            self.log.exception("Exception during redshift cluster creation:%s", err)
            raise err

    def discover_all_clusters(self, availability=True, clusters_dict=None):
        """ Discover all amazon redshift clusters across all regions and update clusters_dict passed

            Args:

                availability -- discover only available redshift clusters

                clusters_dict -- Discover all clusters and update the passed cluster dictionary

            Returns:

                dict    --  dictionary of region : clusters based on redshift cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.info("Discovering redshift clusters across all regions")
            for region in self.regions:
                redshift_client = self.get_redshift_client(region)
                response = redshift_client.describe_clusters()
                clusters = response['Clusters']
                for cluster in clusters:
                    self.log.info(
                        "Found Cluster [%s] Region [%s] Status [%s]",
                        cluster['ClusterIdentifier'],
                        region,
                        cluster['ClusterStatus'])
                    if availability:
                        if cluster['ClusterStatus'].lower() == "available":
                            clusters_dict[region].add(cluster['ClusterIdentifier'])
                    else:
                        clusters_dict[region].add(cluster['ClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_region_clusters(self, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover all amazon redshift clusters in the specified region and update clusters_dict passed

            Args:

                availability -- discover only available redshift clusters

                clusters_dict -- Discover all clusters and update the passed cluster dictionary

                region      -- discover redshift clusters in the specified region

            Returns:

                dict    --  dictionary of region : clusters based on redshift cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Discovering redshift clusters in Region [%s]", region)
            redshift_client = self.get_redshift_client(region)
            response = redshift_client.describe_clusters()
            clusters = response['Clusters']
            for cluster in clusters:
                self.log.debug(
                    "Found Cluster [%s] Region [%s] Status [%s]",
                    cluster['ClusterIdentifier'],
                    region,
                    cluster['ClusterStatus'])
                if availability:
                    if cluster['ClusterStatus'].lower() == "available":
                        clusters_dict[region].add(cluster['ClusterIdentifier'])
                else:
                    clusters_dict[region].add(cluster['ClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_cluster(self, name, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover specified redshift cluster in the specified region and update clusters_dict passed

            Args:

                name        --  Name of the redshift cluster

                region      -- discover redshift clusters in the specified region

                availability -- discover only available redshift clusters

                clusters_dict -- Discover all clusters and update the passed cluster dictionary

            Returns:

                dict    --  dictionary of region : clusters based on redshift cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Discovering cluster with Name [%s] Region [%s]", name, region)
            redshift_client = self.get_redshift_client(region)
            response = redshift_client.describe_clusters(ClusterIdentifier=name)
            clusters = response['Clusters']
            for cluster in clusters:
                self.log.debug(
                    "Found Cluster [%s] Region [%s] Status [%s]",
                    cluster['ClusterIdentifier'],
                    region,
                    cluster['ClusterStatus'])
                if availability:
                    if cluster['ClusterStatus'].lower() == "available":
                        clusters_dict[region].add(cluster['ClusterIdentifier'])
                else:
                    clusters_dict[region].add(cluster['ClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_cluster_rule(self, regex, negation=False, availability=True, clusters_dict=None):
        """ Discover redshift clusters that match the specified regex expression.

            Args:

                regex        -- discover all clusters that has name that matches the regex.

                negation     -- discover all clusters that doesn't match the regex pattern

                availability -- discover only available redshift clusters

                clusters_dict -- Discover all clusters and update the passed cluster dictionary

            Returns:

                dict    --  dictionary of region : clusters based on redshift cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Discovering Clusters with Pattern [%s] Negation [%s]", regex, str(negation))
            for region in self.regions:
                redshift_client = self.get_redshift_client(region)
                response = redshift_client.describe_clusters()
                clusters = response['Clusters']
                for cluster in clusters:
                    cluster_name = cluster['ClusterIdentifier']
                    if re.search(regex, cluster_name) ^ negation:
                        self.log.debug(
                            "Found Cluster [%s] Region [%s] Status [%s]",
                            cluster['ClusterIdentifier'],
                            region,
                            cluster['ClusterStatus'])
                        if availability:
                            if cluster['ClusterStatus'].lower() == "available":
                                self.clusters_dict[region].add(cluster['ClusterIdentifier'])
                        else:
                            self.clusters_dict[region].add(cluster['ClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_cluster_tag(self, tag_name, tag_value, availability=True, clusters_dict=None):
        """ Discover redshift clusters that match the specified regex expression.

            Args:

                tag_name        -- discover all clusters that matches the given tag_name

                tag_value     -- discover all clusters that matches the given tag_value

                availability -- discover only available redshift clusters

                clusters_dict -- Discover all clusters and update the passed cluster dictionary

            Returns:

                dict    --  dictionary of region : clusters based on redshift cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Searching for clusters with Tag [%s] and Value [%s]", tag_name, tag_value)
            for region in self.regions:
                redshift_client = self.get_redshift_client(region)
                response = redshift_client.describe_clusters()
                clusters = response['Clusters']
                for cluster in clusters:
                    tags = cluster['Tags']
                    for tag in tags:
                        if tag['Key'] == tag_name and tag['Value'] == tag_value:
                            self.log.debug(
                                "Found Cluster [%s] Region [%s] Status [%s]",
                                cluster['ClusterIdentifier'],
                                region,
                                cluster['ClusterStatus'])
                            if availability:
                                if cluster['ClusterStatus'].lower() == "available":
                                    clusters_dict[region].add(cluster['ClusterIdentifier'])
                            else:
                                clusters_dict[region].add(cluster['ClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def get_clusters(self, content=None, availability=True):
        """ Returns aws redshift clusters based on the content passed

            Args:

                content  -- list of dynamic cloud entity content which we can set on the subclient content

                availability -- discover only available redshift clusters

                    Example:

                            -- content to select all redshift clusters across all available regions
                            [
                                {
                                    'type': 'root'
                                }
                            ]

                            -- content to select based on region, cluster name, tag rule, regex expressions
                            [
                                {
                                    'type': 'cluster',
                                    'name': 'redshift-cluster-1',
                                    'path': 'us-east-2'
                                },
                                {
                                    'type': 'region',
                                    'name': 'us-east-1'
                                },
                                {
                                    'type' : 'clusterRule',
                                    'name' : '*cluster*' (regex expression to select or filter clusters),
                                    'negation' : true or false
                                },
                                {
                                    'type' : 'tag',
                                    'name' : 'tagname',
                                    'value': 'tagvalue'
                                }
                            ]

            Returns:

                dict(region:set)  --  dict of redshift cluster objects per region that matches availability status.

        """
        try:
            self.clusters_dict = self.empty_cluster_dict()
            self.log.info("Discovering Redshift clusters based on the content passed : %s", content)
            for item in content:

                if item['type'] == 'root':
                    self.discover_all_clusters(availability, self.clusters_dict)
                    return self.clusters_dict

                if item['type'] == 'region':
                    region = item['name']
                    self.discover_region_clusters(region, True, self.clusters_dict)

                if item['type'] == 'cluster':
                    region = item['path']
                    name = item['name']
                    self.discover_cluster(name, region, True, self.clusters_dict)

                if item['type'] == 'clusterRule':
                    name = item['name']
                    negation = item['negation']
                    self.discover_cluster_rule(name, negation, True, self.clusters_dict)

                if item['type'] == 'tag':
                    name = item['name']
                    value = item['value']
                    self.discover_cluster_tag(name, value, True, self.clusters_dict)

            return self.clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def delete_cluster(self, cluster, region):
        """ Delete the cluster in the given region

                Args:

                    cluster   --  name of redshift cluster

                    region    --  region in which the cluster exists

                Returns:

                    None    -- If deletion is successful.

                    Exception   -- If the deletion is unsuccessful
        """
        try:
            self.log.info("Checking if cluster [%s] exists", cluster)
            cluster_dict = self.discover_cluster(cluster, region, False)
            if cluster not in cluster_dict[region]:
                self.log.info("Cluster %s not found in AWS. Deletion is successful.", cluster)
            else:
                redshift_client = self.get_redshift_client(region)
                response = redshift_client.delete_cluster(
                    ClusterIdentifier=cluster,
                    SkipFinalClusterSnapshot=True)
                if response['Cluster']['ClusterIdentifier'] == cluster:
                    while True:
                        wait_response = redshift_client.describe_clusters()
                        wait_clusters = wait_response['Clusters']
                        is_deleted = True
                        for wait_cluster in wait_clusters:
                            if wait_cluster['ClusterIdentifier'] == cluster:
                                self.log.info("Waiting for cluster %s to be deleted.", cluster)
                                is_deleted = False
                                break

                        if is_deleted:
                            self.log.info("Cluster %s is deleted successfully", cluster)
                            break
                        time.sleep(60)
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def get_all_manual_snapshots(self, region):
        """ returns the list of all manual snapshots present in the region specified

            Args:

                region(str)  --  region in which the snapshot list is requested

            Returns:

                list containing manual snapshot identifiers

        """
        try:
            redshift_client = self.get_redshift_client(region)
            snapshots = redshift_client.describe_cluster_snapshots()['Snapshots']
            snapshot_identifier_list = list()
            for snapshot in snapshots:
                if 'manual' in snapshot['SnapshotType'].lower():
                    snapshot_identifier_list.append(snapshot['SnapshotIdentifier'])
            return snapshot_identifier_list
        except ClientError as err:
            self.log.exception("Unable to get the manual snapshots")
            raise err

    def delete_all_manual_snapshots(self, region):
        """ Method to delete all manual snapshots in the given region

            Args:

                region(str) --  region in which the snapshot is present

        """
        try:
            manual_snapshots = self.get_all_manual_snapshots(region)
            for snapshot in manual_snapshots:
                self.delete_snapshot(region, snapshot)
        except ClientError as err:
            self.log.exception(
                "Unable to delete all manual snapshots in:%s", region)
            raise err

    def delete_snapshot(self, region, snapshot_identifier):
        """ Method to delete a snapshot in the given region

            Args:

                region(str)              --  region in which the snapshot is present

                snapshot_identifier(str) -- snapshot identefier

        """
        try:
            redshift_client = self.get_redshift_client(region)
            redshift_client.delete_cluster_snapshot(
                SnapshotIdentifier=snapshot_identifier)
            if self.is_snapshot_present(snapshot_identifier, region):
                raise Exception("Snapshot couldn't be deleted")
        except ClientError as err:
            self.log.exception("Unable to delete the manual snapshot")
            raise err

    def is_cluster_present(self, region, cluster_name, availability=True):
        """ checks if the cluster with given name present in the given region

            Args:

                region          --  region in which the cluster is present

                cluster_name    --  name of redshift cluster

                availability    --  if True return only available cluster
                                    else return if cluster exists
                            default: True

        """
        try:
            redshift_client = self.get_redshift_client(region)
            clusters = redshift_client.describe_clusters()['Clusters']
            for cluster in clusters:
                if cluster['ClusterIdentifier'] == cluster_name:
                    if availability:
                        if cluster['ClusterAvailabilityStatus'].lower() == 'available':
                            self.log.info(
                                "Cluster [%s][%s] is found on Amazon in available state",
                                cluster_name, region)
                            return True
                    else:
                        self.log.info(
                            "Cluster [%s][%s] is found on Amazon in %s state",
                            cluster_name, region, cluster['ClusterAvailabilityStatus'])
                        return True
            return False
        except ClientError as err:
            self.log.debug("Cluster %s not found in region %s", cluster_name, region)
            raise err

    def is_snapshot_present(self, name, region, availability=True):
        """ Check if aws redshift cluster snapshot exists in a given region

                Args:

                    name   --  name of redshift cluster snapshot

                    region          --  region in which the snapshot is present

                    availability    --  if True return only available snapshots
                                        else return if snapshot exists

                Returns:

                    bool    --  True if snapshot exists (and available) and False if snapshot
                    doesn't exist

                    Exception -- if it is not part of AWS CLI botocore exception
        """
        try:
            redshift_client = self.get_redshift_client(region)
            response = redshift_client.describe_cluster_snapshots(SnapshotIdentifier=name)
            snapshots = response['Snapshots']
            for snapshot in snapshots:
                if snapshot['SnapshotIdentifier'] == name:
                    if availability:
                        if snapshot['Status'].lower() == 'available':
                            self.log.info("Snapshot [%s][%s] is found on Amazon in available state", name, region)
                            return True
                    else:
                        self.log.info(
                            "Snapshot [%s][%s] is found on Amazon in %s state",
                            name,
                            region,
                            snapshot['Status'])
                        return True
            return False
        except ClientError:
            self.log.debug("Snapshot %s not found in region %s", name, region)
            return False
        except Exception as err:
            self.log.exception("Unknown exception %s", err)
            raise err


class AmazonDocumentDBCLIHelper(AmazonCLIHelper):
    """Helper class derived from AmazonCLIHelper class to perform Amazon DocDB operations using python boto3 CLI"""

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonDocumentDBCLIHelper class.

            Args:

            access_key : Access Key used to connect to the Amazon Web Services
                default: None

            secret_key : Secret Key used to connect to the Amazon Web Services
                default: None

        """
        super().__init__(access_key, secret_key)
        self.clusters_dict = {}

    def get_docdb_client(self, region):
        """ Returns aws docdb client for the desired service region

                Args:

                    region -- region for which we need docdb client for

                Returns:

                    object -- aws docdb client object
        """
        return self.get_client(region, 'docdb')

    def create_docdb_cluster(self, region, cluster_identifier, master_username, master_userpassword,
                             wait_time_for_creation=10):
        """
        Creates the DocumentDB cluster

        Args:
            region                  (str)   :   region where DocumentDB to be hosted
            cluster_identifier      (str)   :   name of the cluster to be created
            master_username         (str)   :   username for the cluster that gets created
            master_userpassword     (str)   :   password for the cluster that gets created
            wait_time_for_creation  (int)   :   number of minutes to wait for cluster creation
        """
        try:
            docdb_client = self.get_docdb_client(region=region)
            response = docdb_client.create_db_cluster(
                DBClusterIdentifier=cluster_identifier,
                Engine="docdb",
                MasterUsername=master_username,
                MasterUserPassword=master_userpassword

            )
            if response['DBCluster']['DBClusterIdentifier'] == cluster_identifier:
                while True:
                    wait_response = docdb_client.describe_db_clusters()
                    wait_clusters = wait_response['DBClusters']
                    is_created = True
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBClusterIdentifier'] == cluster_identifier and 'available' not in \
                                wait_cluster['Status'].lower():
                            self.log.info("Waiting for cluster %s to be created.", cluster_identifier)
                            is_created = False
                            break
                    if is_created:
                        self.log.info("Cluster %s is created successfully", cluster_identifier)
                        break
                    if wait_time_for_creation <= 0:
                        self.log.info(
                            "Exiting from create cluster method as the wait time is over, please track the cluster status manually")
                        break
                    wait_time_for_creation -= 1
                    time.sleep(60)

        except ClientError as err:
            self.log.exception("Exception during DocumentDB cluster creation:%s", err)
            raise err

    def create_docdb_instance(self, region, instance_identifier, instance_class, cluster_identifier,
                              wait_time_for_creation=15):
        """
        Creates an instance under given DocumentDB cluster
        Args:
            region                  (str)   :   Region where cluster is hosted
            instance_identifier     (str)   :   Name of the instance that getting created
            instance_class          (str)   :   Type of instance that getting created like system requirements
                                                eg: db.r5.large, db.r5.xlarge, db.t4g.medium, etc...
            cluster_identifier      (str)   :   Name of the existing cluster under which instance is getting created
            wait_time_for_creation  (int)   :   Number of minutes to wait to create the instance
        """
        try:
            docdb_client = self.get_docdb_client(region=region)
            response = docdb_client.create_db_instance(
                DBInstanceIdentifier=instance_identifier,
                DBInstanceClass=instance_class,
                Engine="docdb",
                DBClusterIdentifier=cluster_identifier
            )
            if response['DBInstance']['DBInstanceIdentifier'] == instance_identifier and \
                    response['DBInstance']['DBClusterIdentifier'] == cluster_identifier:
                while True:
                    wait_response = docdb_client.describe_db_instances()
                    wait_clusters = wait_response['DBInstances']
                    is_created = True
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBInstanceIdentifier'] == instance_identifier and 'available' not in \
                                wait_cluster['DBInstanceStatus'].lower():
                            self.log.info(f"Waiting for instance {instance_identifier} to be created.")
                            is_created = False
                            break
                    if is_created:
                        self.log.info(f"Instance {instance_identifier} is created successfully")
                        break
                    if wait_time_for_creation <= 0:
                        self.log.info(
                            "Exiting from create instance method as the wait time is over, please track the instance status manually")
                        break
                    wait_time_for_creation -= 1
                    time.sleep(60)

        except ClientError as err:
            self.log.exception(f"Exception during DocumentDB instance creation:{err}")
            raise err

    def discover_all_clusters(self, availability=True, clusters_dict=None):
        """ Discover all amazon docdb clusters across all regions and update clusters_dict passed

                Args:

                availability -- discover only available docdb clusters
                    default: True

                clusters_dict -- Discover all clusters and update the passed cluster dictionary
                    default: None

            Returns:

                dict    --  dictionary of region : clusters based on docdb cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.info("Discovering docdb clusters across all regions")
            for region in self.regions:
                docdb_client = self.get_docdb_client(region)
                response = docdb_client.describe_db_clusters()
                clusters = response['DBClusters']
                for cluster in clusters:
                    self.log.info(
                        "Found Cluster [%s] Region [%s] Status [%s]",
                        cluster['DBClusterIdentifier'],
                        region,
                        cluster['Status'])
                    if availability:
                        if cluster['Status'].lower() == "available":
                            clusters_dict[region].add(cluster['DBClusterIdentifier'])
                    else:
                        clusters_dict[region].add(cluster['DBClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_region_clusters(self, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover all amazon docdb clusters in the specified region and update clusters_dict passed

                Args:

                region      -- discover docdb clusters in the specified region
                    default: us-east-1

                availability -- discover only available docdb clusters
                    default: True

                clusters_dict -- Discover all clusters and update the passed cluster dictionary
                    default: None

            Returns:

                dict    --  dictionary of region : clusters based on docdb cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Discovering docdb clusters in Region [%s]", region)
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.describe_db_clusters()
            clusters = response['DBClusters']
            for cluster in clusters:
                self.log.debug(
                    "Found Cluster [%s] Region [%s] Status [%s]",
                    cluster['DBClusterIdentifier'],
                    region,
                    cluster['Status'])
                if availability:
                    if cluster['Status'].lower() == "available":
                        clusters_dict[region].add(cluster['DBClusterIdentifier'])
                else:
                    clusters_dict[region].add(cluster['DBClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_cluster(self, name, region='us-east-1', availability=True, clusters_dict=None):
        """ Discover specified docdb cluster in the specified region and update clusters_dict passed

                Args:

                name        --  Name of the docdb cluster

                region      -- discover docdb clusters in the specified region
                    default: us-east-1

                availability -- discover only available docdb clusters
                    default: True

                clusters_dict -- Discover all clusters and update the passed cluster dictionary
                    default: None

            Returns:

                dict    --  dictionary of region : clusters based on docdb cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Discovering cluster with Name [%s] Region [%s]", name, region)
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.describe_db_clusters(DBClusterIdentifier=name)
            clusters = response['DBClusters']
            for cluster in clusters:
                self.log.debug(
                    "Found Cluster [%s] Region [%s] Status [%s]",
                    cluster['DBClusterIdentifier'],
                    region,
                    cluster['Status'])
                if availability:
                    if cluster['Status'].lower() == "available":
                        clusters_dict[region].add(cluster['DBClusterIdentifier'])
                else:
                    clusters_dict[region].add(cluster['DBClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def discover_cluster_rule(self, regex, negation=False, availability=True, clusters_dict=None):
        """ Discover docdb clusters that match the specified regex expression.

                Args:

                regex        -- discover all clusters that has name that matches the regex.

                negation     -- discover all clusters that doesn't match the regex pattern
                    default: False

                availability -- discover only available docdb clusters
                    default: True

                clusters_dict -- Discover all clusters and update the passed cluster dictionary
                    default: None

            Returns:

                dict    --  dictionary of region : clusters based on docdb cluster availability

        """
        try:

            if clusters_dict is None:
                clusters_dict = self.empty_cluster_dict()

            self.log.debug("Discovering Clusters with Pattern [%s] Negation [%s]", regex, str(negation))
            for region in self.regions:
                docdb_client = self.get_docdb_client(region)
                response = docdb_client.describe_db_clusters()
                clusters = response['DBClusters']
                for cluster in clusters:
                    cluster_name = cluster['DBClusterIdentifier']
                    if re.search(regex, cluster_name) ^ negation:
                        self.log.debug(
                            "Found Cluster [%s] Region [%s] Status [%s]",
                            cluster['DBClusterIdentifier'],
                            region,
                            cluster['Status'])
                        if availability:
                            if cluster['Status'].lower() == "available":
                                self.clusters_dict[region].add(cluster['DBClusterIdentifier'])
                        else:
                            self.clusters_dict[region].add(cluster['DBClusterIdentifier'])
            return clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def get_clusters(self, content=None, availability=True):
        """ Returns aws docdb clusters based on the content passed

                Args:

                content  -- list of dynamic cloud entity content which we can set on the subclient content
                    default: None

                availability -- discover only available docdb clusters
                    default: True

                    Example:

                            -- content to select all docdb clusters across all available regions
                            [
                                {
                                    'type': 'root'
                                }
                            ]

                            -- content to select based on region, cluster name, tag rule, regex expressions
                            [
                                {
                                    'type': 'cluster',
                                    'name': 'docdb-cluster-1',
                                    'path': 'us-east-2'
                                },
                                {
                                    'type': 'region',
                                    'name': 'us-east-1'
                                },
                                {
                                    'type' : 'clusterRule',
                                    'name' : '*cluster*' (regex expression to select or filter clusters),
                                    'negation' : true or false
                                }
                            ]

            Returns:

                dict(region:set)  --  dict of docdb cluster objects per region that matches availability status.

        """
        try:
            self.clusters_dict = self.empty_cluster_dict()
            self.log.info("Discovering DocumentDB clusters based on the content passed : %s", content)
            for item in content:

                if item['type'] == 'root':
                    self.discover_all_clusters(availability, self.clusters_dict)
                    return self.clusters_dict

                if item['type'] == 'region':
                    region = item['name']
                    self.discover_region_clusters(region, True, self.clusters_dict)

                if item['type'] == 'cluster':
                    region = item['path']
                    name = item['name']
                    self.discover_cluster(name, region, True, self.clusters_dict)

                if item['type'] == 'clusterRule':
                    name = item['name']
                    negation = item['negation']
                    self.discover_cluster_rule(name, negation, True, self.clusters_dict)

            return self.clusters_dict
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def get_cluster_instances(self, cluster, region):
        """ Returns aws docdb clusters based on the content passed

            Args:

                cluster - Name of the cluster to list instances

                region  - Region in which the cluster resides

            Returns

                set(instances)  - Set of instances belonging to the docdb cluster

        """
        cluster_instances = set()
        try:
            self.log.debug("Discovering instances for cluster with Name [%s] Region [%s]", cluster, region)
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.describe_db_clusters(DBClusterIdentifier=cluster)
            clusters = response['DBClusters']
            for cluster_object in clusters:
                if cluster_object['DBClusterIdentifier'] == cluster:
                    self.log.debug(
                        "Found Cluster [%s] Region [%s] Status [%s]",
                        cluster_object['DBClusterIdentifier'],
                        region,
                        cluster_object['Status'])
                    instances = cluster_object['DBClusterMembers']
                    for instance in instances:
                        self.log.debug(
                            "Found Cluster Instance [%s]",
                            instance['DBInstanceIdentifier'])
                        cluster_instances.add(instance['DBInstanceIdentifier'])
                    break
            return cluster_instances
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def get_manual_snapshot_of_cluster(self, region, cluster_identifier):
        """
            Fetches all the manual snapshots of the given cluster
            Args:
                region              (str)   :   Region where the cluster is hosted
                cluster_identifier  (str)   :   Name of the cluster

            Returns:
                (str)   Name of the manual cluster snapshot
        """
        try:
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.describe_db_cluster_snapshots(DBClusterIdentifier=cluster_identifier)
            snapshots = response['DBClusterSnapshots']
            for snapshot in snapshots:
                if 'manual' in snapshot['SnapshotType'].lower():
                    return snapshot['DBClusterSnapshotIdentifier']
            return None
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def delete_instance(self, instance, region):
        """ Delete the docdb instance passed

            instance    -- Name of the docdb instance to delete

            region      -- Region in which the instance is present

            Returns:

                None    -- If the deletion is successful

                Exception -- If the deletion is unsuccessful
        """
        try:
            self.log.info("Deleting instance [%s]", instance)
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.delete_db_instance(DBInstanceIdentifier=instance)
            if response['DBInstance']['DBInstanceIdentifier'] == instance:
                while True:
                    wait_response = docdb_client.describe_db_instances()
                    wait_instances = wait_response['DBInstances']
                    is_deleted = True
                    for wait_instance in wait_instances:
                        if wait_instance['DBInstanceIdentifier'] == instance:
                            self.log.info("Waiting for instance %s to be deleted.", instance)
                            is_deleted = False
                            break

                    if is_deleted:
                        self.log.info("Instance %s deleted successfully", instance)
                        break
                    time.sleep(60)
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def delete_cluster(self, cluster, region):
        """ Delete the cluster in the given region

                Args:

                    cluster   --  name of docdb cluster

                    region    --  region in which the cluster exists

                Returns:

                    None    -- If deletion is successful.

                    Exception   -- If the deletion is unsuccessful
        """
        try:
            self.log.info("Checking if cluster [%s] exists", cluster)
            cluster_dict = self.discover_cluster(cluster, region, False)
            if cluster not in cluster_dict[region]:
                self.log.info("Cluster %s not found in AWS. Deletion is successful.", cluster)
            else:
                docdb_client = self.get_docdb_client(region)
                # Delete all instances of the cluster
                db_instances = self.get_cluster_instances(cluster, region)
                for db_instance in db_instances:
                    self.delete_instance(db_instance, region)
                # Delete the cluster
                response = docdb_client.delete_db_cluster(
                    DBClusterIdentifier=cluster,
                    SkipFinalSnapshot=True)
                if response['DBCluster']['DBClusterIdentifier'] == cluster:
                    while True:
                        wait_response = docdb_client.describe_db_clusters()
                        wait_clusters = wait_response['DBClusters']
                        is_deleted = True
                        for wait_cluster in wait_clusters:
                            if wait_cluster['DBClusterIdentifier'] == cluster:
                                self.log.info("Waiting for cluster %s to be deleted.", cluster)
                                is_deleted = False
                                break

                        if is_deleted:
                            self.log.info("Cluster %s is deleted successfully", cluster)
                            break
                        time.sleep(60)
        except ClientError as err:
            self.log.exception("Unexpected error: %s", err)
            raise err

    def delete_snapshot(self, region, snapshot_identifier):
        """
        Deletes the given DocumentDB snapshot
        Args:
            region              (str)   :   Region where the snapshot present
            snapshot_identifier (str)   :   Name of the snapshot to be deleted
        """
        try:
            docdb_client = self.get_docdb_client(region)
            docdb_client.delete_db_cluster_snapshot(
                DBClusterSnapshotIdentifier=snapshot_identifier
            )
            if self.is_snapshot_present(snapshot_identifier, region):
                raise Exception(f"{snapshot_identifier} snapshot couldn't got deleted")
        except ClientError as err:
            self.log.exception("Unable to delete the snapshot")
            raise err

    def get_all_manual_snapshots(self, region):
        """ returns the list of all manual snapshots present in the region specified

            Args:

                region(str)  --  region in which the snapshot list is requested

            Returns:

                list containing manual snapshot identifiers

        """
        try:
            docdb_client = self.get_docdb_client(region)
            snapshots = docdb_client.describe_db_cluster_snapshots()['DBClusterSnapshots']
            snapshot_identifier_list = list()
            for snapshot in snapshots:
                if 'manual' in snapshot['SnapshotType'].lower():
                    snapshot_identifier_list.append(snapshot['DBClusterSnapshotIdentifier'])
            return snapshot_identifier_list
        except ClientError as err:
            self.log.exception("Unable to get the manual snapshots")
            raise err

    def delete_all_manual_snapshots(self, region):
        """ Method to delete all manual snapshots in the given region

            Args:

                region(str) --  region in which the snapshot is present

        """
        try:
            manual_snapshots = self.get_all_manual_snapshots(region)
            for snapshot in manual_snapshots:
                self.delete_snapshot(region, snapshot)
        except ClientError as err:
            self.log.exception(
                "Unable to delete all manual snapshots in:%s", region)
            raise err

    def start_docdb_cluster(self, region, cluster_identifier, wait_time_for_completion=15):
        """
        Starts the DocumentDB cluster
        Args:
            region                      (str)   :   Region where the DocumentDB cluster Hosted
            cluster_identifier          (str)   :   Name of the cluster
            wait_time_for_completion    (int)   :   Minutes to wait to start the cluster
        """
        try:
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.start_db_cluster(
                DBClusterIdentifier='string'
            )
            if response['DBCluster']['DBClusterIdentifier'] == cluster_identifier:
                while True:
                    is_started = True
                    wait_response = docdb_client.describe_db_clusters()
                    wait_clusters = wait_response['DBClusters']
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBClusterIdentifier'] == cluster_identifier and 'available' not in \
                                wait_cluster['Status'].lower():
                            self.log.info(f"Waiting for cluster {cluster_identifier} to be started.")
                            is_started = False
                            break
                    if is_started:
                        self.log.info(f"Cluster {cluster_identifier} is started successfully")
                        break
                    if wait_time_for_completion <= 0:
                        self.log.info(
                            "Exiting from create cluster method as the wait time is over, please track the cluster status manually")
                        break
                    wait_time_for_completion -= 1
                    time.sleep(60)
        except ClientError as err:
            self.log.debug("Cluster %s not found in region %s", cluster_identifier, region)
            raise err

    def stop_docdb_cluster(self, region, cluster_identifier, wait_time_for_completion=15):
        """
        This will stop the DocumentDB cluster
        Args:
            region                      (str)   :   Region where the DocumentDB cluster Hosted
            cluster_identifier          (str)   :   Name of the cluster
            wait_time_for_completion    (int)   :   Minutes to wait to stop the cluster
        """
        try:
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.stop_db_cluster(
                DBClusterIdentifier=cluster_identifier
            )
            if response['DBCluster']['DBClusterIdentifier'] == cluster_identifier:
                while True:
                    is_stopped = True
                    wait_response = docdb_client.describe_db_clusters()
                    wait_clusters = wait_response['DBClusters']
                    for wait_cluster in wait_clusters:
                        if wait_cluster['DBClusterIdentifier'] == cluster_identifier and 'stopped' not in \
                                wait_cluster['Status'].lower():
                            self.log.info("Waiting for cluster {cluster_identifier} to be started.")
                            is_stopped = False
                            break
                    if is_stopped:
                        self.log.info("Cluster {cluster_identifier} is started successfully")
                        break
                    if wait_time_for_completion <= 0:
                        self.log.info(
                            "Exiting from create cluster method as the wait time is over, please track the cluster status manually")
                        break
                    wait_time_for_completion -= 1
                    time.sleep(60)
        except ClientError as err:
            self.log.debug("Cluster %s not found in region %s", cluster_identifier, region)
            raise err

    def is_cluster_present(self, region, cluster_identifier, availability=False, turn_on=False,
                           wait_time_for_completion=15):
        """
        Check's if the given DocumentDB cluster is present Will do turn on

        Args:
            region                      (str)   :   Region where the DocumentDB cluster Hosted
            cluster_identifier          (str)   :   Name of the cluster
            availability                (bool)  :   Check's is the cluster in available state
            turn_on                     (bool)  :   Will start the cluster if it is stopped state
            wait_time_for_completion    (int)   :   Number of mimutes to wait to start the cluster

        """
        try:
            docdb_client = self.get_docdb_client(region)
            clusters = docdb_client.describe_db_clusters()['DBClusters']
            for cluster in clusters:
                if cluster['DBClusterIdentifier'] == cluster_identifier:
                    if cluster['Status'].lower() == 'stopped' and turn_on:
                        self.log.info(f"starting the {cluster_identifier} cluster")
                        self.start_docdb_cluster(region, cluster_identifier, wait_time_for_completion)
                        return True
                    if availability:
                        if cluster['Status'].lower() == 'available':
                            self.log.info(
                                f"Cluster {cluster_identifier} {region} is found on Amazon in available state")
                            return True
                    else:
                        self.log.info(
                            f"Cluster {cluster_identifier} {region} is found on Amazon in {cluster['Status']} state")
                        return True
            return False
        except ClientError as err:
            self.log.debug("Cluster %s not found in region %s", cluster_identifier, region)
            raise err

    def is_snapshot_present(self, name, region, availability=True):
        """ Check if aws docdb cluster snapshot exists in a given region

                    Args:

                    name   --  name of docdb cluster snapshot

                    region          --  region in which the snapshot is present

                    availability    --  if True return only available snapshots
                                        else return if snapshot exists
                        default: True
                Returns:

                    bool    --  True if snapshot exists (and available) and False if snapshot
                    doesn't exist

                    Exception -- if it is not part of AWS CLI botocore exception
        """
        try:
            docdb_client = self.get_docdb_client(region)
            response = docdb_client.describe_db_cluster_snapshots(DBClusterSnapshotIdentifier=name)
            snapshots = response['DBClusterSnapshots']
            for snapshot in snapshots:
                if snapshot['DBClusterSnapshotIdentifier'] == name:
                    if availability:
                        if snapshot['Status'].lower() == 'available':
                            self.log.info("Snapshot [%s][%s] is found on Amazon in available state", name, region)
                            return True
                    else:
                        self.log.info(
                            "Snapshot [%s][%s] is found on Amazon in %s state",
                            name,
                            region,
                            snapshot['Status'])
                        return True
            return False
        except ClientError:
            self.log.debug("Snapshot %s not found in region %s", name, region)
            return False
        except Exception as err:
            self.log.exception("Unknown exception %s", err)
            raise err

    def delete_docdb_snapshots_of_cluster(self, region, cluster_identifier):
        """
        delete manual snapshots of a particular cluster
        Args:
            region                      (str)   :   Region where the DocumentDB cluster Hosted
            cluster_identifier          (str)   :   Name of the cluster
        """
        docdb_client = self.get_docdb_client(region=region)
        response = docdb_client.describe_db_cluster_snapshots(
            DBClusterIdentifier=cluster_identifier,
            SnapshotType="manual"
        )
        for snapshot in response['DBClusterSnapshots']:
            self.delete_snapshot(region, snapshot['DBClusterSnapshotIdentifier'])


class AmazonCloudDatabaseHelper:
    """Helper class to perform Amazon Cloud Database related operations"""

    def __init__(self, testcase):
        """Initialize instance of the AmazonCloudDatabaseHelper class."""
        self.log = testcase.log
        self.testcase = testcase
        self._cli_helper = None

    @property
    def cli_helper(self):
        """Initializes corresponding Amazon CLI helper based on the instance type"""
        if self._cli_helper is None:
            if self.testcase.instance_name.lower() == "rds":
                self._cli_helper = AmazonRDSCLIHelper(self.testcase.access_key, self.testcase.secret_key)
            if self.testcase.instance_name.lower() == "redshift":
                self._cli_helper = AmazonRedshiftCLIHelper(self.testcase.access_key, self.testcase.secret_key)
            if self.testcase.instance_name.lower() == "documentdb":
                self._cli_helper = AmazonDocumentDBCLIHelper(self.testcase.access_key, self.testcase.secret_key)
        return self._cli_helper

    @staticmethod
    def populate_tc_inputs(testcase):
        """Initializes all the common test case inputs after validation

                Args:

                testcase    (obj)    --    Object of CVTestCase

                Returns:
                    None

                Raises:
                    Exception:
                        if a valid CVTestCase object is not passed.
                        if CVTestCase object doesn't have agent initialized
        """
        if not isinstance(testcase, CVTestCase):
            raise Exception(
                "Valid test case object must be passed as argument"
            )

        testcase.client_name = testcase.tcinputs.get('ClientName', None)
        testcase.instance_name = testcase.tcinputs.get('InstanceName', None)
        testcase.storage_policy = testcase.tcinputs.get('StoragePolicy', None)
        testcase.access_key = testcase.tcinputs.get('AccessKey', None)
        testcase.secret_key = testcase.tcinputs.get('SecretKey', None)
        testcase.access_node = testcase.tcinputs.get('AccessNode', None)
        testcase.agent = testcase.client.agents.get("Cloud Apps")

        if testcase.tcinputs.get('Content'):
            testcase.content = testcase.tcinputs.get('Content')
            if not isinstance(testcase.content, list):
                raise Exception(
                    'Content should be a list type'
                )

    @staticmethod
    def process_browse_response(browse_resp):
        """ Process browse response from BrowseRDSBackups request with start and endtime

            Args:

            browse_resp    --  Response received from the browse request

                Ex:

                    [
                        {
                            "copyId": 13,
                            "commcellId": 2,
                            "createTime": 1571087011,
                            "dbName": "redshift-cluster",
                            "dbType": "Redshift",
                            "archFileId": 1132,
                            "snapShotName": "redshift-cluster-us-east-2-20191014t210331z",
                            "status": 0,
                            "rdsAttributes": {
                                "dbSubnetGroup": "default",
                                "availabilityZone": "us-east-2a,us-east-2b,us-east-2c"
                            }
                        }
                    ]

            Returns:

                dict    -   List of snapshots as key and their avaiability and source cluster name as
                values

                Ex:
                    {
                        'redshift-cluster-us-east-2-20191014t210331z': {
                            'region': 'us-east-2'
                            'source': 'redshift-cluster'
                        }
                    }
        """
        if not isinstance(browse_resp, list):
            raise Exception(
                'Incorrect browse response received {0}'.format(browse_resp)
            )

        snapshots = {}
        for snap in browse_resp:
            snapshots[snap['snapShotName']] = {
                'region': snap['rdsAttributes']['availabilityZone'].split(',')[0][:-1],
                'source': snap['dbName']
            }

        return snapshots

    def run_backup(self, level='full'):
        """ Runs backup of the test case subclient and checks if job ran successfully

                Args:
                    level   -- Backup level (Only fulls will be supported)
                                default - 'full'

                Returns:

                    job     -- object of job if the job ran successfully

                Raises:
                    Exception:
                        --  if job fails

        """
        self.log.info("Starting %s backup for subclient: %s", level, str(self.testcase.subclient_name))
        job = self.testcase.subclient.backup(backup_level=level)

        self.log.info("Waiting for completion of %s backup job : %s", level, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup {1} with error: {2}".format(
                    level, str(job.job_id), job.delay_reason
                )
            )

        if not job.status.lower() == "completed":
            raise Exception(
                "{0} job {1} status is not Completed, job has status: {2}".format(
                    level, str(job.job_id), job.status))

        self.log.info("Successfully finished %s job %s", level, str(job.job_id))
        return job

    def browse(self, job=None):
        """ Returns the list of snapshot from browse request based on the job start and endtime

                Args:

                job   --    Backup job for which we send browse request and get back list of snapshots
                            If the job is not specified then start and endtime are set to 0 and current time
                            respectively

                Returns:

                    dict    --  List of snapshots as key and their avaiability and source cluster name as
                values

                Raises:

                    Exception:
                        --  if browse fails

        """

        job_start_time = 0
        job_end_time = int(time.time())
        if job is not None:
            job_start_time = job.summary['jobStartTime']
            job_end_time = job.summary['jobEndTime']

        browse_req = {
            "start_time": job_start_time,
            "end_time": job_end_time
        }

        self.log.info("Sending Browse request from %s to %s", str(datetime.utcfromtimestamp(job_start_time)),
                      str(datetime.utcfromtimestamp(job_end_time)))
        browse_resp = self.testcase.subclient.browse(browse_req)
        snapshots = self.process_browse_response(browse_resp)
        return snapshots

    def run_backup_verify(self):
        """ Runs Full backup of the test case subclient and checks if job ran successfully
            Verifies if the all clusters of the subclient content is successfully snapped

                Args:
                    None

                Returns:

                    job     -- object of job if the job ran successfully and the verification
                                is successful

                Raises:

                    Exception:

                        --  if job fails.
                        --  all clusters are not snapped successfully

        """
        clusters = self.cli_helper.get_clusters(self.testcase.content)
        self.log.info("Discovered available clusters in Amazon based on content are : \n%s", pprint.pformat(clusters))
        job = self.run_backup()
        snapshots = self.browse(job)
        snapshot_clusters = self.cli_helper.empty_cluster_dict()
        for snapshot in snapshots:
            if not self.cli_helper.is_snapshot_present(snapshot, snapshots[snapshot]['region']):
                raise Exception(
                    "Snapshot {0} is not found on Amazon in available state".format(snapshot)
                )
            snapshot_clusters[snapshots[snapshot]['region']].add(snapshots[snapshot]['source'])

        self.log.info("Clusters Discovered based on Content : \n%s", pprint.pformat(clusters))
        self.log.info("Cluster that has snapshots from Browse Request : \n%s", pprint.pformat(snapshot_clusters))
        if dict(snapshot_clusters) != dict(clusters):
            raise Exception(
                "Not all available clusters are successfully snapped. Run backup Verify failed"
            )
        self.log.info("All available clusters are snapped successfully.")
        return job

    def run_restore(self, snapshot, destination, options):
        """ Runs restore of the subclient with given snapshot, destination and restore options

                Args:
                    snapshot    -- Snapshot we want to restore

                    destination -- Destination instance/cluster name

                    options     -- restore options

                Returns:

                    job     -- object of job if the job ran successfully

                Raises:
                    Exception:
                        --  if job fails

        """

        self.log.info("Restoring snapshot [%s] to [%s] with options \n[%s]", snapshot, destination,
                      pprint.pformat(options))
        job = self.testcase.subclient.restore(destination, snapshot, options)

        self.log.info("Started restore job with job id: %s", str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(
                    job.delay_reason))

        if not job.status.lower() == "completed":
            raise Exception(
                "Job status is not Completed, job has status: {0}".format(
                    job.status))

        self.log.info("Successfully finished restore job %s", str(job.job_id))
        return job

    def run_restore_verify(self, job, options=None, cleanup=True):
        """ Runs restore from the given job by selecting a random snapshot with given restore options
            Verifies if the restore is successful and the restored cluster/instance is in available state
            If cleanup is enabled, then we will delete the restored cluster/instance

                Args:

                    job         -- job which we want to restore from

                    options     -- restore options

                    cleanup     -- True if we want to delete the restored cluster
                                    default - True

                Returns:

                    job     -- object of job if the job ran successfully

                Raises:
                    Exception:
                        --  if job fails

        """
        snapshots = self.browse(job)
        snapshot = list(snapshots.keys())[0]
        region = snapshots[snapshot]['region']
        source = snapshots[snapshot]['source']
        if options is None:
            options = {}

        if not self.cli_helper.is_snapshot_present(snapshot, region):
            raise Exception('Snapshot {0} is not in available state for the restore'.format(snapshot))

        destination = source + "-restore"
        self.log.info(
            "Restoring a random snapshot from the job. Source [%s] Destination [%s] Snapshot [%s] Options [%s]",
            source,
            destination,
            snapshot,
            pprint.pformat(options))

        job = self.run_restore(snapshot, destination, options)

        cluster_list = self.cli_helper.discover_cluster(destination, region)
        if destination not in cluster_list[region]:
            raise Exception(
                "Cluster {0} not found in available state in Amazon. Restore is unsuccessful".format(destination)
            )
        self.log.info("Destination [%s] has been successfully restored from snapshot", destination)

        if cleanup:
            self.log.info("Deleting the restored cluster [%s]", destination)
            self.cli_helper.delete_cluster(destination, region)

        return job


class AmazonDynamoDBCLIHelper(AmazonCLIHelper):
    """Helper class derived from AmazonCLIHelper class to perform Amazon DynamoDB
        operations using python boto3 CLI"""

    def __init__(self, access_key=None, secret_key=None):
        """ Initialize instance of the AmazonDynamoDBCLIHelper class.

            Args:

            access_key : Access Key used to connect to the Amazon Web Services

            secret_key : Secret Key used to connect to the Amazon Web Services

        """
        self.client = None
        self.boto_client = None
        super().__init__(access_key, secret_key)
        self.tables_dict = {}

    def initialize_client(self, region='us-east-1'):
        """Initializes the aws boto3 client with resource type as dynamodb on given region

        Args:
                region: (str)   -- The name of the region where the boto3 client needs to be initiazed

        Returns:
            None

        Raises:
            Exception:
                if the boto3 client couldn't be initialized with resource type as DynamoDB
        """

        try:
            self.client = boto3.resource('dynamodb', region_name=region,
                                         aws_access_key_id=self.access_key,
                                         aws_secret_access_key=self.secret_key
                                         )
            self.boto_client = boto3.client('dynamodb', region_name=region,
                                            aws_access_key_id=self.access_key,
                                            aws_secret_access_key=self.secret_key
                                            )
        except ClientError as err:
            self.log.exception("Unexpected error:%s", err)

    def get_table_object(self, table_name):
        """Creates the dynamodb table object for given table for performing table operations
        using boto3 modules
        If table object was already created, the existing object is returned

        Args:
                table_name: (str)   --  The name of the table for which table object
                                        needs to be created

        Returns:
            object  --  The table object for the given table

        Raises:
            Exception:
                If table object could not be created or if invalid table name is passed

        """
        if not self.tables_dict.get(table_name):
            self.tables_dict[table_name] = self.client.Table(table_name)

        return self.tables_dict.get(table_name)

    def create_dynamodb_table(self, table_name, partition_key):
        """Method to create a dynamodb table with the given name and partition key

        Args:
                table_name: (str)   --  The name of the table that needs to be created

                partition_key(str)  --  The partition key with which table needs to be created

        Returns:
                None

        Raises:
            Exception:
                If table could not be created due to exception on AWS/DynamoDB
        """
        try:
            if table_name in self.boto_client.list_tables()['TableNames']:
                self.log.info("Table exists, dropping it and re-creating")
                self.delete_dynamodb_table(table_name)
            table_obj = self.client.create_table(TableName=table_name, KeySchema=[
                {'AttributeName': partition_key, 'KeyType': 'HASH'}
            ], AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'N'}
            ], ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1},
                                                 StreamSpecification={'StreamEnabled': True,
                                                                      'StreamViewType': 'NEW_IMAGE'})
            self.log.info("Waiting for 30 seconds for the table to get created")
            sleep(30)
            if table_obj.table_status.upper() == 'CREATING':
                self.log.info("Table created successfully")
            else:
                raise Exception("Could not create table")
        except ClientError as err:
            self.log.exception("Create table failed with error: %s", err)
            raise err

    def populate_dynamodb_table(self, table_name, partition_key, num_items):
        """Method to populate given dynamodb with sample items

         Args:
                table_name: (str)   --  The name of the table that needs to be populated
                                        with sample data

                partition_key(str)  --  The partition key for the given table

                num_items(int)      --  The number of items that need to be populated

        Returns:
                None

        Raises:
            Exception:
                If table could not be populated
                If invalid table name was passed
        """
        try:
            table_obj = self.get_table_object(table_name)
            for i in range(1, num_items + 1):
                table_obj.put_item(
                    Item={
                        partition_key: i,
                        'title': 'CV AUTOMATION TESTCASE'
                    }
                )
        except ClientError as err:
            self.log.exception("Unable to populate table: %s", err)
            raise err

    def validate_dynamodb_table(self, table_name, partition_key, expected_item_count):
        """Method to validate the data of the given table after restore

        Args:
                table_name: (str)   --  The name of the table that needs to be validated


                partition_key(str)  --  The partition key for the given table

                expected_item_count(int)      --  The expected count of items in the table

        Returns:
                None
        Raises:
            Exception:
                If expected items were not found
                If expected count of items did not match with the restored table
                If invalid table name was passed
                If table couldn't be read due to exception on AWS/DynamoDB
        """
        try:
            self.log.info("Running validation to check if expected items are found")
            table_obj = self.get_table_object(table_name)
            for i in range(1, expected_item_count + 1):
                response = table_obj.get_item(Key={partition_key: i})
                title = response['Item']['title']
                if title != 'CV AUTOMATION TESTCASE':
                    raise Exception(
                        "Validation failed, did not find the expected items in the table")
            self.log.info("Validation passed, found expected items on dynamodb table")
        except Exception as err:
            self.log.exception("Unknown exception %s", err)
            raise err

    def run_dynamodb_backup(self, subclient_obj, level):
        """Runs backup of the test case subclient and checks if job ran successfully

         Args:
                subclient_obj   --  The subclient object of the subclient
                                    which needs to be backed up

                level   -- Backup level ('full' or 'incremental')

        Returns:
                job     -- object of job if the job ran successfully

        Raises:
                Exception:
                        --  if job fails
        """
        self.log.info("Starting %s backup for subclient: %s", level,
                      str(subclient_obj.subclient_name))
        job = subclient_obj.backup(backup_level=level)

        self.log.info("Waiting for completion of %s backup job : %s", level, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup {1} with error: {2}".format(
                    level, str(job.job_id), job.delay_reason
                )
            )
        if not job.status.lower() == "completed":
            raise Exception(
                "{0} job {1} status is not Completed, job has status: {2}".format(
                    level, str(job.job_id), job.status))

        self.log.info("Successfully finished %s job %s", level, str(job.job_id))
        return job

    def delete_dynamodb_table(self, table_name):
        """Method to delete the given dynamodb table
        Args:
                table_name: (str)   --  The name of the table that needs to be validated

        Returns:
            None
        Raises:
            Exception:
                    If table could not be deleted
                    If invalid table name is passed
        """
        try:
            self.get_table_object(table_name).delete()
            self.log.info("Waiting for 30 seconds for the table to get deleted")
            sleep(30)
        except Exception as err:
            self.log.exception("Unable to delete table: %s", err)
            raise err

    def get_table_arn(self, table_name):
        """Method to return the Amazon resource number-ARN of the given table
                   Args:
                            table_name: (str)   --  The name of the table

                   Returns:
                            str  --  Amazon resource number-ARN of table

                   Raises:
                       Exception:
                       if given table is not found
                """
        try:
            return self.get_table_object(table_name).table_arn
        except Exception as err:
            self.log.exception("Unable to get table ARN: %s", err)
            raise err

    def get_table_id(self, table_name):
        """Method to return the ID of the given dynamodb table
                    Args:
                        table_name: (str)   --  The name of the table

                    Returns:
                        str  --  The ID of table

                    Raises:
                        Exception:
                            if given table is not found
        """
        try:
            return self.boto_client.describe_table(
                TableName=table_name)['Table']['TableId']
        except Exception as err:
            self.log.exception("Unable to get table ID %s", err)
            raise err

    def get_read_capacity(self, table_name):
        """Method to return the read throughput/capacity of the given table
                   Args:
                            table_name: (str)   --  The name of the table

                   Returns:
                            int  --  The read capacity of table

                   Raises:
                       Exception:
                       if given table is not found
                """
        try:
            return self.boto_client.describe_table(
                TableName=table_name)['Table']['ProvisionedThroughput']['ReadCapacityUnits']
        except Exception as err:
            self.log.exception("Unable to get the read capacity: %s", err)
            raise err

    def get_write_capacity(self, table_name):
        """Method to return the write throughput/capacity of the table
                   Args:
                            table_name: (str)   --  The name of the table

                   Returns:
                            int  --  The write capacity of table

                   Raises:
                       Exception:
                       if given table is not found
                """
        try:
            return self.boto_client.describe_table(
                TableName=table_name)['Table']['ProvisionedThroughput']['WriteCapacityUnits']
        except Exception as err:
            self.log.exception("Unable to get the write capacity: %s", err)
            raise err

    def detect_change_in_capacity(self, table_name, changed, parameter='read'):
        """Method to find if table's read/write capacity was changed to expected value
            during backup and restore
                Args:
                    table_name: (str)   --  The name of the table

                    changed: (int)      --  The temp throughput set at subclient/restore job

                    parameter: (str)    --  property to detect capacity change during backup or restore

                         Acceptable values: read / write

                         default: read

                Returns:
                    Boolean--   'True' if capacity was changed to expected value

                Raises:
                    Exception:
                        if given table is not found
                        if parameter other than 'read' or 'write' was passed
                        if no change in throughput is detected
                        Timed-out while waiting to change the throughput
                        """
        parameter_map = {
            'read': self.get_read_capacity,
            'write': self.get_write_capacity
        }
        table_parameter = parameter_map.get(parameter.lower())
        count = 0
        if table_parameter:
            while count < 60:
                current_capacity = table_parameter(table_name)
                if current_capacity == changed:
                    self.log.info("Found expected change in capacity")
                    return True
                else:
                    self.log.info("Waiting for table's capacity to be changed")
                    sleep(2)
                    count += 1
        else:
            self.log.info("Did not detect change in throughput, timed out while waiting")
            self.log.info("Or table with given name doesnt exist")
            raise Exception(
                "Invalid parameter passed or given table doesn't exist or no change in throughput")

    def tag_resource(self, resource_names, tag_name, value):
        """Method to associate AWS tags for the given list of table_names/resources
                Args:
                    resource_names: (list)--  List of names of tables that need to be
                                                            associated with given tag

                    tag_name: (str)       --  The name of the tag

                    value: (str)          --  value of the tag

                Returns:
                        None
                Raises:
                        Exception:
                                if given table is not found
                                if given resource is not in active state
                                """
        try:
            for resource in resource_names:
                self.boto_client.tag_resource(
                    ResourceArn=self.get_table_arn(resource),
                    Tags=[{'Key': tag_name, 'Value': value}, ])
        except Exception as err:
            self.log.exception("Resource could not be tagged: %s", err)
            raise err

    def get_number_of_decreases(self, table_name):
        """Method to get the number of times table's capacity was decreased
         for the given table
                Args:
                    table_name: (str)   --  Name of table

                Returns:
                    int   --  The number of times table's capacity was decreased

                Exception:
                    if given table is not found
                    if given resource is not in active state

        """
        try:
            var = self.boto_client.describe_table(
                TableName=table_name)['Table']['ProvisionedThroughput']['NumberOfDecreasesToday']
            return self.boto_client.describe_table(
                TableName=table_name)['Table']['ProvisionedThroughput']['NumberOfDecreasesToday']
        except Exception as err:
            self.log.exception("Unable to get the write capacity:%s", err)
            raise err
