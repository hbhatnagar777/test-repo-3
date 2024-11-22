# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file that does all operations on OCI for metallic object storage
OCIMetallicHelper: Class for deploying stacks in OCI

OCIOSSHelper: Helper class for OCI Object Storage related operations

OCIMetallicHelper:

    create_stack()              --  Method for creating a stack in oracle cloud.

    run_destroy_job_on_stack()  -- Destroys the resources created by the stack.

    delete_stack()              --  Method for deleting a stack

    run_apply_job_for_stack()   -- Runs an Apply job on the stack to create the resources needed

    get_stack_apply_job_output()  -- Gets the outputs of the job for the stack

    oci_user_details()          --   Gets the user details of the oci user

    upload_api_key()             --  uploads the public key to the user so that an API key gets generated

    get_job_details()           --  Returns the job details with the provided job id

    get_stack_details()         --  Returns the stack details with the provided stack id

    execute_oci_gateway_stack() -- function to set up and execute oci stack for gateway creation

    configure_oci_role()        -- method to collect the stack information to execute on oci

    destroy_and_delete_stack()  -- Deletes all the resources created by stack

    cleanup()                      -- Cleanups the created IAM and Backup gateway stacks

OCIOSSHelper:

    list_compartments()           --  Returns the compartments list under the given compartment

    list_buckets()                --  Returns the buckets under the given compartment

    list_objects()                --  List of objects along with metadata in a given bucket will be returned

    get_objects_metadata()         --  Returns each object metadata under the given bucket.

    get_bucket_metadata()         --  Returns the metadata of the given bucket

    download_bucket()             -- downloads the given bucket to the given directory in temp folder.

    create_dir_download()         --  creates directory if required to download

    list_object_versions()        --  List of object versions along with metadata in a given bucket will be returned

    abort_uncommitted_multipart_uploads()  --  aborts uncommitted uploads in the given tenant.

    delete_bucket()               --  deletes the given bucket

    oci_cleanup()                  --   To remove temp directories created during oci helper object initialization

"""

import os
import oci
from AutomationUtils import config, logger, constants
import time
from urllib.parse import urlparse, parse_qs
from oci.object_storage.object_storage_client import ObjectStorageClient
from AutomationUtils.machine import Machine


class OCIOSSHelper:
    def __init__(self, user_name):
        """Helper class for OCI Object Storage related operations"""
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.machine = Machine()
        self.time_stamp = time.time()
        self.temp_folder_name = f"OCITemp_{self.time_stamp}"
        self.common_dir_path = self.machine.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.machine.create_directory(self.common_dir_path,
                                      force_create=True)
        self.oci_dict = user_name
        self.vm_details_dict = dict()
        self.oci = oci
        self.config = config.get_config()
        self.log = logger.get_log()
        self.oci_config = {
            "user": self.oci_dict['oci_user_id'],
            "key_file": self.oci_dict['oci_private_file_name'],
            "fingerprint": self.oci_dict['oci_finger_print'],
            "tenancy": self.oci_dict['oci_tenancy_id'],
            "region": self.oci_dict['oci_region_name'],
            "pass_phrase": self.oci_dict.get('oci_private_key_password', '')
        }
        try:
            config_validator = self.oci.config.validate_config(self.oci_config)
            if config_validator not in (None, "None"):
                self.log.error("Provided configurations are not valid please cross check.")
                raise Exception
            self.osc = ObjectStorageClient(self.oci_config)
            self.identity = self.oci.identity.IdentityClient(self.oci_config)
            self.user = self.identity.get_user(self.oci_config["user"]).data
            self.root_compartment_id = self.user.compartment_id
            self.resource_manager = oci.resource_manager.ResourceManagerClient(self.oci_config)
            self.composite_resource_manager = oci.resource_manager.ResourceManagerClientCompositeOperations(
                self.oci_config)
            self.identity_client = oci.identity.IdentityClient(self.oci_config)
        except Exception as exp:
            self.log.info("Error occurred during initializing oci helper objects")
            self.log.info(exp)
            raise exp

    def list_compartments(self, compartment_id=None):
        """Returns the compartments list under the given compartment
            Args:
                compartment_id(str) -- parent compartment id under which all the sub compartments are needed.
            Returns:
                list -- compartments list under given compartment id.
        """
        try:
            response = self.identity.list_compartments(compartment_id=compartment_id, compartment_id_in_subtree=True)
            compartments_list = response.data
            while response.next_page:
                response = self.identity.list_compartments(compartment_id=compartment_id,
                                                           page=response.next_page,
                                                           compartment_id_in_subtree=True)
                compartments_list.extend(response.data)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return compartments_list

    def list_buckets(self, compartment_id):
        """Returns the buckets under the given compartment
            Args:
                compartment_id(str) -- compartment id for getting the buckets in the given compartment.
            Returns:
                list -- buckets list in the given compartment.
        """
        try:
            response = self.osc.list_buckets(self.config.ObjectStorage.oci.namespace, compartment_id)
            buckets_list = response.data
            while response.next_page:
                self.osc.list_buckets(self.config.ObjectStorage.oci.namespace, compartment_id,
                                      page=response.next_page)
                buckets_list.extend(response.data)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return buckets_list

    def get_bucket_metadata(self, bucket_name):
        """Returns the metadata of the given bucket
            Args:
                bucket_name(str) -- name of the bucket for which bucket metadata need to be returned.
            Returns:
                dict -- A dictionary of the metadata for a given bucket will be returned.
        """
        try:
            response = self.osc.get_bucket(self.config.ObjectStorage.oci.namespace, bucket_name,
                                           fields=['approximateCount', 'approximateSize', 'autoTiering'])
            bucket_metadata = response.data.__dict__
            # removing the data that gets changed based on time and other constraints not based on the backed up data
            del bucket_metadata["_time_created"]
            del bucket_metadata["_etag"]
            del bucket_metadata["attribute_map"]
            del bucket_metadata["swagger_types"]
            del bucket_metadata["_approximate_size"]
            del bucket_metadata["_approximate_count"]
            del bucket_metadata["_id"]
            del bucket_metadata["_created_by"]
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return bucket_metadata

    def list_objects(self, bucket_name, prefix=None):
        """
        List of objects along with metadata in a given bucket will be returned
        Args:
            bucket_name(str) -- buckets in which objects list need to be retrived.
            prefix(str) -- prefix filtering with given string.
        Returns:
            list -- objects list
        """
        try:
            response = self.osc.list_objects(self.config.ObjectStorage.oci.namespace, bucket_name,
                                             fields='name',
                                             prefix=prefix)
            response = response.data.__dict__
            objects_list = response['_objects']
            while response.get('_next_start_with'):
                response = self.osc.list_objects(self.config.ObjectStorage.oci.namespace, bucket_name,
                                                 fields='name',
                                                 prefix=prefix, start=response['_next_start_with']).data.__dict__
                objects_list.extend(response['_objects'])
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return objects_list

    def get_objects_metadata(self, bucket_name, prefix=None):
        """
        Returns each object metadata under the given bucket.
        Args:
            bucket_name(str) -- buckets in which objects metadata need to be retrieved.
            prefix(str) -- prefix filtering with given string.
        Returns:
            dict -- objects metadata mapped to their names

        """
        objects_list = self.list_objects(bucket_name, prefix=prefix)
        objects_metadata = {}
        for current_object in objects_list:
            response = self.osc.head_object(self.config.ObjectStorage.oci.namespace, bucket_name, current_object.name)
            response = dict(response.headers)
            del response['last-modified']
            del response['etag']
            del response['version-id']
            del response['date']
            del response['opc-request-id']
            del response['x-api-id']
            objects_metadata[current_object.name] = response
        return objects_metadata

    def download_bucket(self, bucket_name, dir_name):
        """
        downloads the given bucket to the given directory in temp folder.
        Args:
            bucket_name(str) -- bucket name of the bucket that need to be downloaded.
            dir_name(str) -- directory in which this bucket need to be downloaded.
        """
        objects_list = self.list_objects(bucket_name)
        local_path = self.machine.join_path(
            self.common_dir_path, dir_name)
        os.mkdir(local_path)
        os.chdir(local_path)
        try:
            for current_object in objects_list:
                if "/" in current_object.name:
                    self.create_dir_download(bucket_name, current_object.name)
                else:
                    try:
                        data = self.osc.get_object(self.config.ObjectStorage.oci.namespace, bucket_name,
                                                   current_object).data
                        with open(current_object.name, 'wb') as file:
                            for chunk in data.raw.stream(1024 * 1024, decode_content=False):
                                file.write(chunk)
                    except Exception as exp:
                        self.log.error(exp)
                        raise exp
        except Exception as exp:
            self.log.error(exp)
            raise exp
        finally:
            os.chdir(self.automation_directory)

    def create_dir_download(self, bucket_name, key):
        """creates directory if required to download
            Args:
                key(str) -- object name of object in ibm object storage.

                bucket_name(str) -- name of the bucket to be downloaded.
        """
        if str(key)[-1] == "/":
            self.machine.create_directory(self.machine.join_path(os.getcwd(), key))
        else:
            head, tail = os.path.split(f"{key}")
            try:
                if not self.machine.check_directory_exists(self.machine.join_path(os.getcwd(), head)):
                    self.machine.create_directory(self.machine.join_path(os.getcwd(), head))
                data = self.osc.get_object(self.config.ObjectStorage.oci.namespace, bucket_name, key).data
                with open(self.machine.join_path(os.getcwd(), head, tail), 'wb') as file:
                    for chunk in data.raw.stream(1024 * 1024, decode_content=False):
                        file.write(chunk)
            except Exception as error:
                self.log.error(error)
                raise error

    def list_object_versions(self, bucket_name, prefix=None):
        """
        List of object versions along with metadata in a given bucket will be returned
        Args:
            bucket_name(str) -- buckets in which object versions list need to be retrived.
            prefix(str) -- prefix filtering with given string.
        Returns:
            list -- object versions list
        """
        try:
            response = self.osc.list_object_versions(self.config.ObjectStorage.oci.namespace, bucket_name,
                                                     fields='name',
                                                     prefix=prefix)
            object_versions_list = response.data.__dict__['_items']
            while response.next_page:
                response = self.osc.list_object_versions(self.config.ObjectStorage.oci.namespace, bucket_name,
                                                         fields='name',
                                                         prefix=prefix, page=response.next_page)
                object_versions_list.extend(response.data.__dict__['_items'])
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return object_versions_list

    def abort_uncommitted_multipart_uploads(self, bucket_name):
        """
        aborts uncommitted uploads in the given tenant.
        """
        try:
            response = self.osc.list_multipart_uploads(self.config.ObjectStorage.oci.namespace,
                                                       bucket_name)
            list_uncommited_multipart_uploads = response.data
            while response.next_page:
                response = self.osc.list_multipart_uploads(self.config.ObjectStorage.oci.namespace,
                                                           bucket_name, page=response.next_page)
                list_uncommited_multipart_uploads.extend(response.data)
            for upload in list_uncommited_multipart_uploads:
                self.osc.abort_multipart_upload(self.config.ObjectStorage.oci.namespace, bucket_name, upload.object,
                                                upload.upload_id)
        except Exception as exp:
            self.log.error(exp)
            raise exp

    def delete_bucket(self, bucket_name):
        """deletes the given bucket"""
        try:
            objects_list_versions = self.list_object_versions(bucket_name)
            for object_version in objects_list_versions:
                self.osc.delete_object(self.config.ObjectStorage.oci.namespace, bucket_name, object_version.name,
                                       version_id=object_version.version_id)
            self.abort_uncommitted_multipart_uploads(bucket_name)
            self.osc.delete_bucket(self.config.ObjectStorage.oci.namespace, bucket_name)
        except Exception as exp:
            self.log.error(exp)
            raise exp

    def oci_cleanup(self):
        """
        To remove temp directories created
        during oci helper object initialization
        """
        self.machine.remove_directory(self.common_dir_path)


class OCIMetallicHelper(OCIOSSHelper):

    def __init__(self, user_name):
        """Initializes the class
            Args:
                user_name(dict) -- user details to authenticate with oracle cloud.
        """
        super(OCIMetallicHelper, self).__init__(user_name=user_name)
        self._bkp_gw_stack_id = None
        self._iam_stack_id = None
        self.user_details = None
        self.api_key_data = None

    def create_stack(self, stack_creation_data):
        """Method for creating a stack in oracle cloud.
            Args:
                stack_creation_data (dict) -- the data required for creating a stack in cloud.
            Returns:
                dict -- infromation regarding the created stack.
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
        try:
            stack_info = self.resource_manager.create_stack(create_stack_details=createStackDetails)
            stack_info = stack_info.data
            time.sleep(15)
            time_passed = 15
            while stack_info.lifecycle_state not in [stack_info.LIFECYCLE_STATE_ACTIVE]:
                if time_passed > 120:
                    raise Exception("stack creation taking too long, please check on the OCI console")
                time.sleep(20)
                time_passed = time_passed + 20
                stack_info = self.get_stack_details(stack_id=stack_info.id)
        except Exception as exp:
            self.log.error("An error occurred during stack creation")
            self.log.error(exp)
            raise exp
        return stack_info

    def run_destroy_job_on_stack(self, stack_id):
        """Destroys the resources created by the stack.
            Args:
                stack_id(str) -- id of the stack whose resources need to be deleted.
            Returns:
                dict -- destroy job information.
        """
        destroy_job_operation_details = oci.resource_manager.models.CreateDestroyJobOperationDetails()
        destroy_job_operation_details.operation = 'DESTROY'
        destroy_job_operation_details.execution_plan_strategy = 'AUTO_APPROVED'

        destroy_job_details = oci.resource_manager.models.CreateJobDetails()
        destroy_job_details.stack_id = stack_id
        destroy_job_details.job_operation_details = destroy_job_operation_details
        try:
            destroy_job_info = self.resource_manager.create_job(destroy_job_details)
            destroy_job_info = destroy_job_info.data
            time.sleep(30)
            time_passed = 30
            while destroy_job_info.lifecycle_state not in [destroy_job_info.LIFECYCLE_STATE_SUCCEEDED]:
                if time_passed > 300:
                    raise Exception("plan job info failed , please check the OCI console for details ")
                time.sleep(60)
                time_passed = time_passed + 60
                destroy_job_info = self.get_job_details(destroy_job_info.id)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return destroy_job_info

    def delete_stack(self, stack_id):
        """Method for deleting a stack
            Args:
                stack_id(str) -- id of the stack which we need to delete.
            Returns:
                object -- response data of the stack delete operation
        """
        try:
            response = self.resource_manager.delete_stack(stack_id)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return response.data

    def run_apply_job_for_stack(self, stack_id):
        """Runs an Apply job on the stack to create the resources needed
            Args:
                stack_id(str) -- id of the stack on which apply job need to be run.
            Returns:
                dict -- apply job response.
        """
        apply_job_operation_details = oci.resource_manager.models.CreateApplyJobOperationDetails()
        apply_job_operation_details.operation = 'APPLY'
        apply_job_operation_details.execution_plan_strategy = 'AUTO_APPROVED'
        job_details = oci.resource_manager.models.CreateJobDetails()
        job_details.stack_id = stack_id
        job_details.job_operation_details = apply_job_operation_details
        try:
            apply_job_info = self.resource_manager.create_job(job_details)
            apply_job_info = apply_job_info.data
            time.sleep(30)
            time_passed = 30
            while apply_job_info.lifecycle_state not in [apply_job_info.LIFECYCLE_STATE_SUCCEEDED]:
                if time_passed > 600:
                    raise Exception("apply job info failed , please check the OCI console for details ")
                time.sleep(60)
                time_passed = time_passed + 60
                apply_job_info = self.get_job_details(apply_job_info.id)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return apply_job_info

    def get_stack_apply_job_output(self, apply_job_id):
        """
        Gets the outputs of the job for the stack
        Args:
            apply_job_id(str) -- job id of the apply job.
        Returns:
            json string -- apply job outputs.
        """
        import json
        try:
            apply_job_state = self.resource_manager.get_job_tf_state(apply_job_id)
            state_json = json.loads(apply_job_state.data.content.decode('utf-8'))
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return state_json

    def oci_user_details(self, username_details):
        """
        Gets the user details of the oci user
        Args:
            username_details(dict) -- details of a user.
        Returns:
            dict -- returns the api key and user id details
        """
        try:
            oci_user_details = self.identity_client.list_users(compartment_id=self.config.ObjectStorage.oci.tenancy,
                                                               name=username_details).data[0]
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return oci_user_details

    def upload_api_key(self, oci_user, public_key_path):
        """
        uploads the public key to the user so that an API key gets generated
        Args:
            oci_user(dict) -- oci user details
            public_key_path(dict) -- path to public key to create a new API key.
        Returns:

        """
        try:
            with open(public_key_path, 'rb') as f:
                public_key = f.read().strip()
            key_details = oci.identity.models.CreateApiKeyDetails(key=public_key.decode())
            key_response = self.identity_client.upload_api_key(oci_user.id, key_details)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        api_key_data = key_response.data
        return api_key_data

    def get_job_details(self, job_id):
        """Returns the job details with the provided job id
            Args:
                job_id(str) -- id of the job for which we need the job details
            Returns:
                dict -- job details
        """
        try:
            job_response = self.resource_manager.get_job(job_id=job_id)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return job_response.data

    def get_stack_details(self, stack_id):
        """Returns the stack details with the provided stack id
        Args:
            stack_id(str) -- id of the stack for which we need the details
        Returns:
            dict -- job details
        """
        try:
            stack_details_response = self.resource_manager.get_stack(stack_id=stack_id)
        except Exception as exp:
            self.log.error(exp)
            raise exp
        return stack_details_response.data

    def execute_oci_gateway_stack(self, stack_url):
        """
        function to set up and execute oci stack for gateway creation
        Args:
            stack_url: backup gateway deployment url.

        Returns:
            dict -- outputs of the deployment job.
        """
        stack_params = parse_qs(urlparse(stack_url).query)
        zipUrl = stack_params['zipUrl'][0]
        import base64, requests
        encoded_file = base64.b64encode(requests.get(zipUrl).content).decode('ascii')
        stack_creation_data = dict()
        stack_creation_data['encoded_file'] = encoded_file
        stack_creation_data['display_name'] = 'metallic automation backup gateway stack ashburn'
        stack_creation_data['description'] = "backupgateway for oci automation for metallic onboarding test"
        stack_creation_data['compartment_id'] = self.config.ObjectStorage.oci.compartment
        variables = dict()
        variables["tenancy_ocid"] = self.config.ObjectStorage.oci.tenancy
        variables["compartment_ocid"] = self.config.ObjectStorage.oci.compartment
        variables["region"] = stack_params['region'][0]
        variables["data_size"] = '25TB'
        variables["authcode"] = eval(stack_params["zipUrlVariables"][0])['authcode']
        variables["instance_compartment_ocid"] = self.config.ObjectStorage.oci.compartment
        variables["nsg_compartment_ocid"] = self.config.ObjectStorage.oci.compartment
        variables["availability_domain"] = self.config.ObjectStorage.oci.availability_domain
        variables["vcn_ocid"] = self.config.ObjectStorage.oci.vcn
        variables["subnet_ocid"] = self.config.ObjectStorage.oci.subnet
        if "LinuxBackupGateway.zip" in zipUrl:
            variables["ssh_public_key"] = self.config.ObjectStorage.oci.bkpgw_public_key
        else:
            variables["ssh_public_key"] = ''
        stack_creation_data['variables'] = variables
        stack_info = self.create_stack(stack_creation_data)
        self._bkp_gw_stack_id = stack_info.id
        apply_job = self.run_apply_job_for_stack(stack_id=self._bkp_gw_stack_id)
        job_output = self.get_stack_apply_job_output(apply_job.id)
        self.log.info("OCI Backup created.")
        return job_output

    def configure_oci_role(self, stack_url):
        """
        method to collect the stack information to execute on oci
        :return:
        stack ino
        """
        public_key_path = self.config.ObjectStorage.oci.public_key_path
        stack_params = parse_qs(urlparse(stack_url).query)
        zipUrl = stack_params['zipUrl'][0]
        stack_params['region'] = zipUrl.split('.')[1]
        import base64, requests
        encoded_file = base64.b64encode(requests.get(zipUrl).content).decode('ascii')
        stack_creation_data = dict()
        stack_creation_data['encoded_file'] = encoded_file
        stack_creation_data['display_name'] = 'metallication automation Role'
        stack_creation_data['description'] = "role with the permissions required"
        stack_creation_data['compartment_id'] = self.config.ObjectStorage.oci.compartment
        variables = dict()
        variables['tenancy_ocid'] = self.config.ObjectStorage.oci.tenancy
        variables['region'] = stack_params['region']
        variables['user_email'] = "abc2@abc.com"
        variables['policy_compartment_ocid'] = self.config.ObjectStorage.oci.compartment
        stack_creation_data['variables'] = variables
        stack_info = self.create_stack(stack_creation_data=stack_creation_data)
        self._iam_stack_id = stack_info.id
        apply_job = self.run_apply_job_for_stack(stack_id=stack_info.id)
        job_output = self.get_stack_apply_job_output(apply_job.id)
        user_details = job_output['outputs']['metallic_user']['value']
        self.log.info(f"OCI stack resources for IAM got created.")
        self.user_details = self.oci_user_details(username_details=user_details)
        self.log.info(f"Fetching user details {user_details}")
        self.api_key_data = self.upload_api_key(self.user_details, public_key_path=public_key_path)
        self.log.info(f"API Key for authentication with oracle cloud got created.")
        return self.api_key_data

    def destroy_and_delete_stack(self, stack_id):
        """Deletes all the resources created by stack"""
        self.run_destroy_job_on_stack(stack_id)
        self.delete_stack(stack_id)

    def cleanup(self):
        """Cleanups the created IAM and Backup gateway stacks"""
        if self._iam_stack_id:
            self.destroy_and_delete_stack(self._iam_stack_id)
            self.log.info("Cleaned up the user groups, user account and policy created during execution")
        if self._bkp_gw_stack_id:
            self.destroy_and_delete_stack(self._bkp_gw_stack_id)
            self.log.info("Cleaned up the backup gateway created during execution")


