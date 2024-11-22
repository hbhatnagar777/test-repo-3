# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import oci
import time
import json
from AutomationUtils.config import get_config
from AutomationUtils.logger import get_log

_CONFIG_DATA = get_config()

"""Helper file for performing OCI operations

OCIHelper 

OCIHelper: Helper class for the common oci related operations

OCI:
    __init__()                    --  Initializes objects of the OCIHelper

    create_stack()                --  Creates an OCI stack

    run_apply_job_for_stack()     --  Runs the apply job for the stack

    run_destroy_job_for_stack()   --  Runs the destroy job for the stack

    get_stack_apply_job_output()  -- Gets resources details of the apply job

    oci_user_details()            -- Gets user details for the given username

    upload_api_key()              -- Uploads api key for oci user

    delete_stack()                -- Deletes the stack

    get_node_power_state()        -- Gets the power state of the db node

    set_db_state()                -- Sets the state for all nodes in db
"""


class OCIHelper:
    """Helper class for the oci related operations"""

    def __init__(self):
        """Initialize instance of the OCIHelper class"""
        self.oci_config = {
            "user": _CONFIG_DATA.OCI.oci_user_id,
            "key_file": _CONFIG_DATA.OCI.oci_private_key_path,
            "fingerprint": _CONFIG_DATA.OCI.oci_fingerprint,
            "tenancy": _CONFIG_DATA.OCI.oci_tenancy_id,
            "region": _CONFIG_DATA.OCI.oci_region,
            "pass_phrase": _CONFIG_DATA.OCI.oci_private_key_password
        }
        self.identity_client = oci.identity.IdentityClient(self.oci_config)
        self.database_client = oci.database.DatabaseClient(self.oci_config)
        self.user = self.identity_client.get_user(self.oci_config["user"]).data
        self.root_compartment_id = self.user.compartment_id
        self.log = get_log()
        self.resource_manager = oci.resource_manager.ResourceManagerClient(self.oci_config)
        self.compartments_list = None
        self.core_client = oci.core.ComputeClient(self.oci_config)

    def create_stack(self, stack_creation_data):
        """Creates the stack by uploading the custom terraform config
           Args:
               stack_creation_data  (dict)      : Dict containing details of the stack
           Returns:
               stack_info           (dict)      : Dict containing stack_info
        """
        zipfiledetails = oci.resource_manager.models.CreateZipUploadConfigSourceDetails()
        zipfiledetails.config_source_type = 'ZIP_UPLOAD'
        zipfiledetails.zip_file_base64_encoded = stack_creation_data['encoded_file']

        createStackDetails = oci.resource_manager.models.CreateStackDetails()
        createStackDetails.display_name = stack_creation_data['display_name']
        createStackDetails.description = stack_creation_data['description']
        createStackDetails.config_source = zipfiledetails
        createStackDetails.terraform_version = '1.0.x'
        createStackDetails.compartment_id = stack_creation_data['compartment_id']
        createStackDetails.variables = stack_creation_data['variables']
        stack_info = self.resource_manager.create_stack(create_stack_details=createStackDetails)
        stack_info = stack_info.data
        time_passed = 0
        while stack_info.lifecycle_state not in [stack_info.LIFECYCLE_STATE_ACTIVE]:
            if time_passed > 180:
                raise Exception("stack creation taking too long, please check on the OCI console")
            time.sleep(20)
            time_passed = time_passed + 20
            stack_info = self.get_stack_details(stack_id=stack_info.id)
        return stack_info

    def run_apply_job_for_stack(self, stack_id):
        """
        run apply job for the oci stack
        Args:
            stack_id             (int)    :   stack id
        Returns:
            apply_job_info       (dict)   :   Info of the applied job
            stack_resource_info  (dict)   :   Info of the created stack
        """
        apply_job_operation_details = oci.resource_manager.models.CreateApplyJobOperationDetails()
        apply_job_operation_details.operation = 'APPLY'
        apply_job_operation_details.execution_plan_strategy = 'AUTO_APPROVED'
        job_details = oci.resource_manager.models.CreateJobDetails()
        job_details.stack_id = stack_id
        job_details.job_operation_details = apply_job_operation_details

        apply_job_info = self.resource_manager.create_job(job_details)
        apply_job_info = apply_job_info.data
        time.sleep(30)
        time_passed = 30
        while apply_job_info.lifecycle_state not in [apply_job_info.LIFECYCLE_STATE_SUCCEEDED]:
            if time_passed > 720:
                raise Exception("apply job info failed , please check the OCI console for details ")
            time.sleep(60)
            time_passed = time_passed + 60
            apply_job_info = self.resource_manager.get_job(job_id=apply_job_info.id).data
        stack_resources_info = self.resource_manager.list_stack_associated_resources(stack_id).data
        return apply_job_info, stack_resources_info

    def run_destroy_job_on_stack(self, stack_id):
        """
        run apply job for the oci stack
        Args:
              stack_id  (int)   :  stack id
        Returns:
              destroy_job_info  (dict) : Info of the destroy job
        """
        destroy_job_operation_details = oci.resource_manager.models.CreateDestroyJobOperationDetails()
        destroy_job_operation_details.operation = 'DESTROY'
        destroy_job_operation_details.execution_plan_strategy = 'AUTO_APPROVED'
        job_details = oci.resource_manager.models.CreateJobDetails()
        job_details.stack_id = stack_id
        job_details.job_operation_details = destroy_job_operation_details

        destroy_job_info = self.resource_manager.create_job(job_details)
        destroy_job_info = destroy_job_info.data
        time.sleep(30)
        time_passed = 30
        while destroy_job_info.lifecycle_state not in [destroy_job_info.LIFECYCLE_STATE_SUCCEEDED]:
            if time_passed > 720:
                raise Exception("apply job info failed , please check the OCI console for details ")
            time.sleep(60)
            time_passed = time_passed + 60
            destroy_job_info = self.resource_manager.get_job(job_id=destroy_job_info.id).data
        return destroy_job_info

    def get_stack_apply_job_output(self, apply_job_id):
        """
        output of resource job on the stack
        Args:
            apply_job_id: (str) ocid of the apply job

        Returns:
            output object of the job
        """
        apply_job_state = self.resource_manager.get_job_tf_state(apply_job_id)
        state_json = json.loads(apply_job_state.data.content.decode('utf-8'))
        return state_json

    def oci_user_details(self, username):
        """
        user details of the oci user
        Args:
            username: (str) name of the user

        Returns:
            userdetails obj of oci
        """
        oci_user_details = self.identity_client.list_users(compartment_id=_CONFIG_DATA.OCI.oci_tenancy_id,
                                                           name=username).data[0]
        return oci_user_details

    def upload_api_key(self, oci_user, public_key_path):
        """
        upload a api key to the user on oci
        Args:
            oci_user: (obj) oci user object
            public_key_path: (str) file path of the public key

        Returns:
            (obj) api key data of oci
        """

        with open(public_key_path, 'rb') as f:
            public_key = f.read().strip()
        key_details = oci.identity.models.CreateApiKeyDetails(key=public_key.decode())
        key_response = self.identity_client.upload_api_key(oci_user.id, key_details)
        api_key_data = key_response.data
        return api_key_data

    def delete_stack(self, stack_id):
        """
        method to delete the stack
        Args:
            stack_id: (str) ocid of the stack

        Returns:
            None
        """
        self.resource_manager.delete_stack(stack_id=stack_id)

    def get_node_power_state(self, node_id):
        """
        get the power state of the db node

        Args:
            node_id (str) : id of the db node
        """
        response = self.database_client.get_db_node(node_id)
        node_info = response.data
        return node_info.lifecycle_state

    def set_db_state(self, action):
        """
        performs action on all nodes of the db

        Args:
            action (str) : action for the node
        """
        final_state = {"start": "AVAILABLE", "stop": "STOPPED"}.get(action)
        for node_id in _CONFIG_DATA.OCI.node_ids:
            self.database_client.db_node_action(db_node_id=node_id, action=action)
            time_left = 900
            while time_left:
                self.log.info(f"Waiting to set db state to {final_state}")
                time.sleep(180)
                time_left -= 180
                current_state = self.get_node_power_state(node_id)
                if current_state == final_state:
                    self.log.info(f"Node with id {node_id} is set to {final_state}")
                    break
                if not time_left:
                    self.log.warning(f"Node with id {node_id} is not set to {final_state}")
    
    def get_instance(self, instance_ocid):
        """
        Returns the Instance object for OCI Instance

        Args:
            instance_ocid (str) : OCID of the Instance
        """

        response = self.core_client.get_instance(instance_ocid)
        return response.data
    
    def get_instance_state(self, instance_ocid):
        """
        Returns the instance state

        Args:
            instance_ocid (str) : OCID of the Instance
        """

        instance_obj = self.get_instance(instance_ocid)
        return instance_obj.lifecycle_state

    def set_instance_state(self, instance_ocid, state):
        """
        Sets the instance state

        Args:
            instance_oci (str): OCID of the instance
            state (str) : Action to perform. Values can be start / stop
        """

        action = {"start": "START", "stop": "SOFTSTOP"}.get(state)
        
        self.core_client.instance_action(instance_ocid, action)

        self.log.info(f"Sleeping for 3 minutes for the instance to {state}")
        time.sleep(180)

        if state == "start" and self.get_instance_state(instance_ocid).lower() == "running":
            self.log.info("Instance successfully started")
        
        if state == "stop" and self.get_instance_state(instance_ocid).lower() == "stopped":
            self.log.info("Instance successfully stopped")
