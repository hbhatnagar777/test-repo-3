# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Amazon S3 operations

S3Helper is the only class defined in this file.

S3Helper: Helper class to perform operations on Amazon S3

S3Helper :
    __init__()                           --   initializes Amazon S3 helper object

    create_session_s3()                  --   creates a new session with Amazon S3 cloud
    with the provided credentials

    create_container_s3()                --   creates a bucket in Amazon S3 cloud

    delete_container_s3()                --   deletes the specified bucket from Amazon S3 cloud

    upload_file_s3()                     --   uploads the specified file to Amazon S3 cloud

    create_dir_download_file_s3()        --   checks if the folder exists locally. If not,
    creates a directory and downloads a file to it

    delete_contents_s3()                 --   deletes all the contents under the specified
    paths from Amazon S3 cloud

    download_container_s3()              --   downloads a specified container with all
    it's contents from the Amazon S3 cloud

    download_contents_s3()               --   downloads all the contents under the
    specified paths from the Amazon S3 cloud

    recur()                              --   recursively traverses through the subfolders
    and downloads the objects

    delete_file_s3()                     --   deletes a specified file from Amazon S3 cloud

    fetch_file_metadata()                --   To fetch object meta data from AWS S3 Storage

    search_bucket_by_prefix()            --   Fetches the first instance of a Bucket name that starts with given prefix

    get_bucket_and_objects_acls()       --    gets the bucket and objects acls

    get_objects_user_defined_metadata() --    gets the user defined metadata for objects

    get_objects_metadata()              --    gets the all http headers defined for objects

    get_bucket_and_objects_tags()       --    gets the tags defined for objects and bucket

    download_s3_bucket()                 --   Downloads S3 bucket to the given path

S3MetallicHelper:

    __init()                        -- init method for s3 metallic helper class

    create_stack()                  --  Method to create stack for backup in aws

    delete_stack()                  --  deletes the cloud formation stack

    wait_for_stack_creation()       --  Waits for stack to get created

    wait_for_stack_deletion()       --  Waits for stack to get deleted

    get_stack()                     --  Gets the stack output value

"""
import mimetypes
import os
import socket
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from AutomationUtils import logger, config
import boto3
import botocore
from boto3.session import Session
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from dynamicindex.utils import constants as cs


class S3Helper(object):
    """Helper class to perform operations on Amazon S3"""

    def __init__(self, testcase_object):
        """Initializes Amazon S3 helper object"""
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = testcase_object.log
        self.machine = Machine(socket.gethostname())
        self.s3_client = None

    def create_session_s3(self, access_key, secret_access_key, region):
        """creates a session with S3 cloud
        Args :
            access_key         (str)    --  Access key for connecting to Amazon S3 account

            secret_access_key  (str)    --  Secret access key for connecting to Amazon S3 account

            region             (str)    --  Region where the S3 buckets are residing

        Returns :
            (obj)                       --  Amazon S3 session object

        """
        session = Session(aws_access_key_id=access_key, aws_secret_access_key=secret_access_key,
                          region_name=region)
        self.s3_client = session.client(service_name='s3')
        s3_session = session.resource("s3")
        return s3_session

    def create_container_s3(self, session, bucket_name):
        """creates a container to S3 cloud
        Args :
            session        (obj)     --       Amazon S3 session object

            bucket_name    (str)     --       name of the new bucket which has to be created

        Returns :
            None

        Raises :
            Exception :
                if the bucket name is invalid or the bucket with specified name already exists

        """
        try:
            response = session.create_bucket(Bucket=bucket_name)
            self.log.info(response)
        except Exception as error:
            self.log.error(
                "The bucket name is invalid or the bucket with specified name already exists")
            self.log.error(error)
            raise error

    def empty_container_s3(self, session, bucket_name):
        """empties a container from S3 cloud
        Args :
            session        (obj)     --       Amazon S3 session object

            bucket_name    (str)     --       name of the bucket which has to be deleted

        Returns :
            None

        Raises :
            Exception :
                If the specified bucket does not exist

        """
        bucket = session.Bucket(bucket_name)
        try:
            for key in bucket.objects.all():
                key.delete()
        except Exception as error:
            self.log.error("The specified bucket doesn't exist")
            self.log.error(error)
            raise error


    def delete_container_s3(self, session, bucket_name):
        """deletes a container from S3 cloud
        Args :
            session        (obj)     --       Amazon S3 session object

            bucket_name    (str)     --       name of the bucket which has to be deleted

        Returns :
            None

        Raises :
            Exception :
                If the specified bucket does not exist

        """
        bucket = session.Bucket(bucket_name)
        try:
            self.empty_container_s3(session, bucket_name)
            bucket.delete()
        except Exception as error:
            self.log.error("The specified bucket doesn't exist")
            self.log.error(error)
            raise error

    def upload_file_s3(self, session, file_path, bucket_name, file_name):
        """uploads a file to S3 cloud
        Args :
            session        (obj)     --       Amazon S3 session object

            file_path      (str)     --       path to the file on the local machine

            bucket_name    (str)     --       name of the bucket

            file_name      (str)     --       name of the file to be created on the cloud

        Returns :
            None

        Raises :
            Exception :
                If the specified bucket or the file on the local machine doesn't exist

        """
        try:
            response = session.meta.client.upload_file(file_path, bucket_name, file_name)
            self.log.info(response)
        except Exception as error:
            self.log.error("The specified bucket or the file on the local machine doesn't exist")
            self.log.error(error)
            raise error

    def create_dir_download_file_s3(self, container_name, obj_key, session):
        """checks if folder exists locally. If not, creates a directory and downloads a file to it
        Args :
            container_name (str)     --       name of the container

            obj_key        (str)     --       name of the s3 object

            session        (obj)     --       s3 session object

        Returns :
            None

        Raises :
            Exception:
                if the specified content does not exist on the cloud

        """
        if str(obj_key)[-1] == "/":
            self.machine.create_directory(self.machine.join_path(os.getcwd(), obj_key[:-1]))
        else:
            head, tail = os.path.split("{}".format(obj_key))
            try:
                if self.machine.check_directory_exists(self.machine.join_path(os.getcwd(), head)):
                    # download the files to this directory
                    session.meta.client.download_file(container_name, obj_key,
                                                      self.machine.join_path(os.getcwd(), head, tail))
                else:
                    # create the directory and download the file to it
                    self.machine.create_directory(self.machine.join_path(os.getcwd(), head))
                    session.meta.client.download_file(container_name, obj_key,
                                                      self.machine.join_path(os.getcwd(), head, tail))
            except Exception as error:
                self.log.error("The specified container does not exist on the cloud")
                self.log.error(error)
                raise error

    def delete_contents_s3(self, session, content):
        """deletes the specified contents from S3 cloud
        Args :
            session        (obj)     --       Amazon S3 session object

            content        (list)    --       Part of the subclient content which has to be
            deleted from the cloud

        Returns :
            None

        Raises :
            Exception :
                if the specified content does not exist on the cloud

        """
        for item in content:
            windows_path = Path(item)
            bucket_name = Path(item).parts[1]
            if (len(windows_path.parts)) == 2:
                self.delete_container_s3(session, bucket_name)
                continue
            last = os.path.basename(item)
            bucket = session.Bucket(bucket_name)
            path_to_file = ("/".join(item.strip("/").split('/')[1:]))
            generator = bucket.objects.all()
            obj_list = []
            for i in generator:
                obj_list.append(i.key)
            if last in obj_list:
                obj = session.Object(bucket_name, path_to_file)
                obj.delete()
            else:
                generator = bucket.objects.filter(Prefix=path_to_file)
                for j in generator:
                    obj = session.Object(bucket_name, j.key)
                    obj.delete()

    def download_container_s3(self, session, container_name):
        """downloads a container from S3 cloud
        Args :
            session        (obj)   --   Amazon S3 session object

            container_name (str)   --   Name of the amazon s3 bucket which has to be downloaded

        Returns :
            None

        Raises :
            Exception :
                If the specified container does not exist on the cloud

        """
        bucket = session.Bucket(container_name)
        generator = bucket.objects.all()
        os.mkdir(container_name)
        try:
            os.chdir(container_name)
            # code below lists all the blobs in the container and downloads them one after another
            for obj in generator:
                # check if the path contains a folder structure, create the folder structure
                if "/" in "{}".format(obj.key):
                    # extract the folder path and check if that folder exists locally,
                    # and if not create it
                    self.create_dir_download_file_s3(container_name, obj.key, session)
                else:
                    try:
                        session.meta.client.download_file(container_name, obj.key, obj.key)
                    except Exception as error:
                        self.log.error("The specified container does not exist on the cloud")
                        self.log.error(error)
                        raise error
        finally:
            os.chdir(self.automation_directory)

    def download_contents_s3(self, session, content, dir_name, oop_flag):
        """downloads the specified contents from S3 cloud
        Args :
            session       (obj)      --      Amazon S3 session object

            content       (list)     --      Part of the subclient content which has to
            be downloaded from the cloud

            dir_name      (str)      --      Name of the folder where the specified
            contents are to be downloaded

            oop_flag      (bool)     --      Flag to determine if it's an inplace restore
            or an out of place restore

        Returns :
            None

        Raises :
            Exception :
                If the specified content does not exist on the cloud

        """
        if oop_flag is True:
            container_name = content.replace("/", "")
            self.download_container_s3(session, container_name)
            os.chdir(self.automation_directory)
        else:
            os.mkdir(dir_name)
            for item in content:
                try:
                    os.chdir(dir_name)
                    container_name = Path(item).parts[1]
                    path_to_file = ("/".join(item.strip("/").split('/')[1:]))
                    bucket = session.Bucket(container_name)
                    generator = bucket.objects.all()
                    obj_list = []
                    for j in generator:
                        obj_list.append(j.key)
                    if path_to_file == "":
                        self.download_container_s3(session, container_name)
                        os.chdir(self.automation_directory)
                    elif path_to_file in obj_list:
                        if os.path.exists(container_name) is False:
                            os.mkdir(container_name)
                        os.chdir(container_name)
                        self.create_dir_download_file_s3(container_name, path_to_file,
                                                         session)
                    else:
                        generator_folder = bucket.objects.filter(Prefix=path_to_file)
                        if os.path.exists(container_name) is False:
                            os.mkdir(container_name)
                        os.chdir(container_name)
                        # code below lists all the blobs in the container and
                        # downloads them one after another
                        for obj in generator_folder:
                            # check if the path contains a folder structure,
                            # create the folder structure
                            if "/" in "{}".format(obj.key):
                                # extract the folder path and check if that folder exists locally,
                                # and if not create it
                                head, tail = os.path.split("{}".format(obj.key))
                                if tail:
                                    self.create_dir_download_file_s3(container_name, obj.key,
                                                                     session)
                                else:
                                    self.recur(session, container_name, obj.key)
                            else:
                                try:
                                    session.meta.client.download_file(container_name, obj.key,
                                                                      obj.key)
                                except Exception as error:
                                    self.log.error(
                                        "The specified content does not exist on the cloud")
                                    self.log.error(error)
                                    raise error
                finally:
                    os.chdir(self.automation_directory)

    def recur(self, session, container_name, objct):
        """recursively traverses through the subfolders and downloads the objects
        Args :
            session        (obj)       --     S3 session object

            container_name (str)       --     name of the S3 container

            objct          (str)       --     name of the object

        Returns :
            None

        Raises :
            Exception :
                If the specified container or object does not exist on the cloud

        """
        bucket = session.Bucket(container_name)
        generator_folder = bucket.objects.filter(Prefix=objct)
        for i in generator_folder:
            head, tail = os.path.split("{}".format(i.key))
            if tail:
                self.create_dir_download_file_s3(container_name, i.key, session)
            else:
                self.recur(session, container_name, i.key)

    def delete_file_s3(self, session, bucket_name, filetobedeleted):
        """deletes a file from S3 cloud
        Args :
            session            (obj)       --        Amazon S3 session object

            bucket_name        (str)       --        Name of the bucket

            filetobedeleted    (str)       --        Name of the file to be deleted

        Returns :
            None

        Raises :
            Exception :
                If the specified bucket or the file does not exist on the cloud

        """
        try:
            response = session.meta.client.delete_object(Bucket=bucket_name, Key=filetobedeleted)
            self.log.info(response)
        except Exception as error:
            self.log.error("The specified bucket or the file does not exist on the cloud")
            self.log.error(error)
            raise error

    def fetch_file_metadata(self, session, bucket_name_prefix):
        """
        Fetches the properties meta data for all the file objects in the S3 Bucket

        Args:
            session (Object)            :   Container client object

            bucket_name_prefix (str)    :   Bucket name prefix string

        Returns:
            list                        :   Returns a list of metadata retrieved from the cloud

            Example - [{'PATH': 'AWS\\10364200796756\\PIIFiles\\476_1644340532752\\512\\Lindsey good
            1621204276-3251\\Chester McCormick window 3259.txt', 'PARENT_DIR':
            '10364200796756\\PIIFiles\\476_1644340532752\\512\\Lindsey good 1621204276-3251', 'NAME': 'Chester
            McCormick window 3259.txt', 'FILE_SIZE': 28286, 'MIME_TYPE': 'text/plain', 'MODIFIED_TIME': 'February 08,
            2022 12:16:51 PM', 'CREATED_TIME': 'February 08, 2022 12:16:51 PM', 'ACCESS_TIME': 'February 08,
            2022 12:16:51 PM', 'FILE_OWNER': 'dummy_user', 'PARENT_DIR_PERMISSION': '', 'FILE_PERMISSION': '',
            'FILE_PERMISSION_READABLE': '', 'IS_DIR': 0}, {...}]

        """
        bucket_name = self.search_bucket_by_prefix(session, bucket_name_prefix)
        if not bucket_name:
            raise Exception(
                f"AWS bucket not found. No Bucket exists with prefix {bucket_name_prefix}")

        all_buckets = session.buckets.all()
        assert bucket_name in list(b.name for b in all_buckets) != "", f"Bucket {bucket_name} does not exist"
        meta_data = list()
        bucket = session.Bucket(bucket_name)
        for obj in bucket.objects.all():
            temp_dict = {}
            temp_dict[cs.FSO_METADATA_FIELD_PATH] = file_path = obj.key.lstrip('/').replace('/', '\\')
            file_string_split = file_path.rsplit('\\', 1)
            temp_dict[cs.FSO_METADATA_FIELD_PARENT_DIR] = file_string_split[0]
            temp_dict[cs.FSO_METADATA_FIELD_NAME] = file_string_split[1]
            temp_dict[cs.FSO_METADATA_FIELD_FILE_SIZE] = obj.size
            mime_type, encoding = mimetypes.guess_type(temp_dict[cs.FSO_METADATA_FIELD_NAME])
            if not mime_type:
                mime_type = 'application/octet-stream'
            temp_dict[cs.FSO_METADATA_FIELD_MIME_TYPE] = mime_type
            modified_time_str = datetime.strftime(obj.last_modified.astimezone(), "%B %d, %Y %r")
            temp_dict[cs.FSO_METADATA_FIELD_MODIFIED_TIME] = modified_time_str
            temp_dict[cs.FSO_METADATA_FIELD_CREATED_TIME] = modified_time_str
            temp_dict[cs.FSO_METADATA_FIELD_ACCESS_TIME] = modified_time_str
            temp_dict[cs.FSO_METADATA_FIELD_FILE_OWNER] = obj.Acl().owner['DisplayName']
            temp_dict[cs.FSO_METADATA_FIELD_PARENT_DIR_PERMISSION] = ""
            temp_dict[cs.FSO_METADATA_FIELD_FILE_PERMISSION] = ""
            temp_dict[cs.FSO_METADATA_FIELD_FILE_PERMISSION_READABLE] = ""
            temp_dict[cs.FSO_METADATA_FIELD_IS_DIR] = 0
            temp_dict[cs.FSO_METADATA_FIELD_FILE_TYPE] = file_string_split[1].rsplit('.')[-1]
            meta_data.append(temp_dict)
        return meta_data

    def search_bucket_by_prefix(self, session, bucket_name_prefix):
        """
        Gets the first Bucket Name that matches bucket_name_prefix from AWS S3 storage
        Args:
            session             (obj)       :   AWS session object
            bucket_name_prefix  (str)       :   Prefix string to match bucket names
        Returns:
            str                             :   Returns the bucket name as string
        """
        all_buckets = session.buckets.all()
        for b in all_buckets:
            if b.name.startswith(bucket_name_prefix):
                try:
                    session.meta.client.head_bucket(Bucket=b.name)
                    return b.name
                except Exception:
                    self.log.info(f"Skipping stale bucket : {b.name}")
        return None

    def get_bucket_and_objects_acls(self, session, bucket_name):
        """gets the bucket and objects acls
                Args :
                    session        (obj)     --       Amazon S3 session object

                    bucket_name    (str)     --       name of the new bucket which has to be created

                Returns :
                    dict : returns a dictionary where key is the object or bucket name and value is the list of acls.
        """
        acls = {}
        bucket = session.Bucket(bucket_name)
        for obj in bucket.objects.all():
            acls[obj.key] = obj.Acl().grants
        acls[bucket.name] = bucket.Acl().grants
        return acls

    def get_objects_user_defined_metadata(self, session, bucket_name):
        """gets the user defined metadata for objects
                Args :
                    session        (obj)     --       Amazon S3 session object

                    bucket_name    (str)     --       name of the new bucket which has to be created

                Returns :
                    dict : returns a dictionary where key is the object or bucket name and value is the list of acls.
                """
        metadata = {}
        bucket = session.Bucket(bucket_name)
        for obj in bucket.objects.all():
            metadata[obj.key] = obj.get()['Metadata']
        return metadata

    def get_objects_metadata(self, session, bucket_name):
        """gets the all http headers defined for objects
                Args :
                    session        (obj)     --       Amazon S3 session object

                    bucket_name    (str)     --       name of the new bucket which has to be created

                Returns :
                    dict : returns a dictionary where key is the object or bucket name and value is the list of acls.
                """
        metadata = {}
        bucket = session.Bucket(bucket_name)
        for obj in bucket.objects.all():
            meta = obj.get()['ResponseMetadata']['HTTPHeaders']
            del meta['x-amz-id-2']
            del meta['x-amz-request-id']
            del meta['date']
            del meta['last-modified']
            metadata[obj.key] = meta
        return metadata

    def get_bucket_and_objects_tags(self, session, bucket_name):
        """gets the tags defined for objects and bucket
                Args :
                    session        (obj)     --       Amazon S3 session object

                    bucket_name    (str)     --       name of the new bucket which has to be created

                Returns :
                    dict : returns a dictionary where key is the object or bucket name and value is the list of acls.
        """
        tags = {}
        bucket = session.Bucket(bucket_name)
        try:
            for obj in bucket.objects.all():
                tags[obj.key] = self.s3_client.get_object_tagging(Bucket=bucket_name, Key=obj.key)['TagSet']
            tags[bucket.name] = self.s3_client.get_bucket_tagging(Bucket=bucket_name)
            tags[bucket.name] = tags[bucket.name]['TagSet']
        except botocore.exceptions.ClientError as exp:
            self.log.info(f"while getting tags for {bucket_name} bucket following error occurred {exp}")
        finally:
            return tags

    def download_s3_bucket(self, s3_session, bucket_name, path):
        """ Downloads S3 bucket to the given path
            Args:
                path(str) -- download location of s3 bucket

                s3_session(obj)  --       Amazon S3 session object

                bucket_name(str) -- name of the bucket which needs to be downloaded
        """
        current_path = os.getcwd()
        head, tail = os.path.split(path)
        os.chdir(head)
        os.mkdir(tail)
        os.chdir(path)
        self.download_container_s3(s3_session, bucket_name)
        os.chdir(current_path)
        self.log.info("Downloaded S3 bucket")


class S3MetallicHelper:

    def __init__(self, region):
        """init method for s3 metallic helper"""
        try:
            self.aws_connection = boto3.Session(region_name=region)
            self.config = config.get_config()
            self.cloud_formation_obj = self.aws_connection.client(
                'cloudformation', region_name=region,
                aws_access_key_id=self.config.aws_access_creds.access_key,
                aws_secret_access_key=self.config.aws_access_creds.secret_key)
            self.resources = boto3.resource('cloudformation',
                                            region_name=region,
                                            aws_access_key_id=self.config.aws_access_creds.access_key,
                                            aws_secret_access_key=self.config.aws_access_creds.secret_key)
            self.log = logger.get_log()
            self.log.info("Connection successful for AWS")
        except Exception as error:
            self.log.exception("Unexpected error: %s" % error)
            raise error

    def create_stack(self, stack_name, stack_url, params=None, capabilities=None):
        """Method to create stack for backup in aws
        Args:
            stack_name(str) -- name of the stack

            stack_url(str)  -- stack url for template to create stack

            params(dict)    -- parameters for creating stack

            capabilities(dict)  --option for IAM stack creation
        """
        stack_params = parse_qs(urlparse(stack_url).fragment)
        template_url = stack_params["/stacks/quickcreate?templateURL"][0]
        try:
            if params:
                authcode = stack_params["param_AuthCode"][0]
                params.append({"ParameterKey": "AuthCode", "ParameterValue": authcode})
                backup_gateway_package = stack_params["param_BackupGatewayPackage"][0]
                params.append({"ParameterKey": "BackupGatewayPackage",
                               "ParameterValue": backup_gateway_package})
                auth_type = stack_params["param_Authentication"][0]
                params.append({"ParameterKey": "Authentication",
                               "ParameterValue": auth_type})
                self.cloud_formation_obj.create_stack(StackName=stack_name,
                                                      TemplateURL=template_url,
                                                      Parameters=params)
            else:
                self.cloud_formation_obj.create_stack(StackName=stack_name,
                                                      TemplateURL=template_url,
                                                      Capabilities=capabilities)
            self.wait_for_stack_creation(stack_name)
        except self.cloud_formation_obj.exceptions.AlreadyExistsException:
            self.log.info(f'Stack already exist. Using this existing stack {stack_name}')
            pass
        except Exception as exp:
            self.log.exception(exp)
            raise Exception
        return self.get_stack(stack_name)

    def delete_stack(self, stack_name):
        """deletes the cloud formation stack
            Args:
                stack_name(str)-Name of the cloud formation stack.
        """
        self.cloud_formation_obj.delete_stack(StackName=stack_name)
        self.log.info("stack delete started")
        self.wait_for_stack_deletion(stack_name)
        self.log.info(f"{stack_name} deleted successfully")

    def wait_for_stack_creation(self, stack_name):
        """Waits for stack to get created
            Args:
                stack_name(str) -- Name of the cloud formation stack.
        """
        waiter = self.cloud_formation_obj.get_waiter('stack_create_complete')
        self.log.info("waiting for stack to get created")
        waiter.wait(StackName=stack_name)

    def wait_for_stack_deletion(self, stack_name):
        """Waits for stack to get deleted
            Args:
                stack_name(str)-Name of the cloud formation stack.
        """
        waiter = self.cloud_formation_obj.get_waiter('stack_delete_complete')
        self.log.info("waiting for stack to get deleted")
        waiter.wait(StackName=stack_name)

    def get_stack(self, stackName):
        """Gets the stack output value
           Args:
               stackName(str)-- Name of the cloud formation stack.

            Returns:
                string -- output of the cloud formation stack
        """
        stack = self.resources.Stack(stackName)
        return stack
