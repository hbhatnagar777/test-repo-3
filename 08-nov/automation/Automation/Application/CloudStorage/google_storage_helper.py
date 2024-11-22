# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Main Class for performing Google Cloud storage operations

    This File has one class : GoogleObjectStorage

    GoogleObjectStorage: Helper to perform operations/manipulations on google cloud object storage

    __init__()                              --  initializes googleobjectstorage object

    google_helper_cleanup()                 --  Removes temp directories created
                                                during google cloud object initialization

    google_connect()                        --  Establishes connection to google object storage
                                                and return google storage  object

    file_generator()                        --  Method to generate files with
                                                random string content

    list_buckets()                          --  Lists all buckets available in given google cloud

    check_if_bucket_exist()                 --  To check if given bucket exists or not

    create_google_subclient()               --  Creates subclient with given content under
                                                given google instance

    create_bucket()                         --  To create bucket in google object storage

    get_bucket()                            --  Returns bucket object with given name if it exists

    delete_bucket()                         --  Delete given google Bucket

    list_objects()                          --  To list all blobs inside given bucket

    download_single_item()                  --  To download object from given bucket

    upload_single_item()                    --  To upload single item to given bucket

    delete_blob()                           --  To delete blob from cloud bucket

    delete_folder_in_cloud()                --  To delete a subfolder inside the google bucket

    get_blob_size()                         --  Returns size of given blob in cloud

    populate_data()                         --  populate basic set of data in google cloud

    download_google_bucket()                --  Download entire google bucket

    upload_folder_to_cloud()                --  Upload folder to given google bucket

    get_google_secret_key()                 --  Returns google instance secret key for given instance

    upload_files_to_bucket()                --  To upload files directly under google bucket

    google_restore_overwrite_validation()   --  To perform in-place restore with overwrite
                                                to google and validating the same

    fetch_file_metadata()                    -- To fetch file object meta data from Google Cloud Storage

"""
import mimetypes
import os
import random
import string
from datetime import datetime
from os.path import isfile, join
import shutil
import threading
import google.cloud
from google.cloud import storage

from AutomationUtils import machine
from AutomationUtils import cvhelper
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from Application.CloudApps import exception
from dynamicindex.utils import constants as cs

CONFIG = get_config().DynamicIndex.Activate.GCP


class GoogleObjectStorage:
    """Class for performing admin level operation for Google Cloud Storage"""

    def __init__(self, testcase_object, ignore_tc_props=False):
        """
        Initializes the GoogleObjectStorage object.

            Args:

                    testcase_object  (Object)  --  instance of Test case class

            Returns:

                    object  --  instance of Google Object Storage class
        """
        self.testcase_object = testcase_object
        self.tc_inputs = testcase_object.tcinputs
        self.commcell = testcase_object.commcell
        self.log = testcase_object.log
        if not ignore_tc_props:
            self.instance = testcase_object.instance
            self.client = testcase_object.client
            self.agent = testcase_object.agent
            self.cloud_storage_helper = testcase_object.cloud_storage_helper
        if "key_file_path" in self.tc_inputs:
            self.key_file_path = self.tc_inputs["key_file_path"]
        else:
            self.key_file_path = CONFIG.KeyFilePath
        self.google_storage = None
        self.controller_object = machine.Machine()
        self.thread_id = str(threading.get_ident())
        self.temp_folder_name = """GoogleTemp_{0}""".format(self.thread_id)
        self.common_dir_path = self.controller_object.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.controller_object.create_directory(self.common_dir_path,
                                                force_create=True)
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.csdb = testcase_object.csdb
        self.google_connect()

    def google_helper_cleanup(self):
        """
        To remove temp directories created
        during google helper object initialization
        """
        self.controller_object.remove_directory(self.common_dir_path)

    def google_connect(self):
        """
        Establishes connection to google object storage
        and return google storage  object

        Raises
            Exception
                if it fails to create google storage connection
                due to missing entries in json file

        """
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.key_file_path
            self.google_storage = storage.Client()
        except Exception as google_exception:
            self.log.exception(
                "Error occurred while creating google storage object")
            raise exception.CVCloudException(
                'CloudConnector', '101', str(google_exception))

    def file_generator(self, local_directory_path, count=10):
        """
        Method to generate files with random string content

        Args:
            local_directory_path    (str)       --  path to local directory for file generation

            count                   (int)       --  number of files to be generated
                                                    default : 10

        """
        for file in range(count):
            filename = self.controller_object.join_path(
                local_directory_path, "{0}_testfile.txt".format(file + 1))
            with open(filename, "w") as fp:
                content_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(1000000))
                fp.write(content_string)
                content_string = None

    def list_buckets(self, prefix=None):
        """
        Lists all available buckets in given google object storage

        Args:

            prefix  (str)   --  filter results to buckets whose
                                names begin with this prefix
                                default : None

        Returns:

            (list)  -    returns list of available buckets

        Raises
            Exception
                if its fails to fetch the list of buckets

        """
        try:
            self.log.info("List Bucket Method")
            bucket_list = []
            for bucket in self.google_storage.list_buckets(prefix):
                bucket_list.append(bucket.name)
            return bucket_list
        except Exception as google_exception:
            raise Exception(
                "Error occurred while fetching the google bucket list")

    def check_if_bucket_exists(self, bucket_name):
        """
        To check if given bucket exists or not

        Args:

            bucket_name     (str)   --  name of the bucket to be checked

        Returns:

            (bool)      -       returns true if bucket exists else false

        """
        self.log.info("Check if given %s bucket exists", bucket_name)
        check_if_exists = self.google_storage.lookup_bucket(bucket_name)
        if check_if_exists is None:
            return False
        else:
            return True

    def create_google_subclient(self, subclient_name, content):
        """
        Creates subclient with given content under given sybase instance

        Args:
            subclient_name  (str)  -- name of subclient to be created

            content         (list) -- list of buckets for content

        Returns:
            (obj)   -   subclient object created

        """
        # get storage policy of default subclient
        self.log.info("fetching SP")
        self.log.info(self.instance.instance_name)
        default_subclient = self.instance.subclients.get("default")
        self.log.info("got subclient object")
        storage_policy = default_subclient.storage_policy
        self.log.info("fetched SP")
        if self.instance.subclients.has_subclient(subclient_name):
            self.log.info(
                "subclient with name:%s already exists.deleting",
                subclient_name)
            self.instance.subclients.delete(subclient_name)

        # create subclient with this bucket
        self.log.info("creating subclient object")
        subclient = self.instance.subclients.add(
            subclient_name, storage_policy)
        subclient.content = content
        return subclient

    def create_bucket(self, bucket_name):
        """
        To create bucket in google object storage

        Args:

            bucket_name     (str)   --  name of the bucket to be created

        Raises
            Exception
                if it fails to create bucket

                if bucket with same name exists

        """
        check_if_exists = self.google_storage.lookup_bucket(bucket_name)
        if not check_if_exists:
            self.log.info(
                "Bucket with given name doesn't exists . so creating the bucket")
            bucket = self.google_storage.create_bucket(bucket_name)
            self.log.info("Bucket %s created", bucket.name)

        else:
            self.log.info(
                'The bucket matching the name provided exists already')
            raise Exception("Bucket with same name already exists in cloud")

    def get_bucket(self, bucket_name):
        """
        Returns bucket object with given name if it exists

        Args:

            bucket_name     (str)       --      name of bucket to be fetched

        Returns:

            (object)    -   object of google bucket class

        Raises
            Exception
                if bucket is not found

        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            return bucket
        except google.cloud.exceptions.NotFound:
            self.log.info("Given bucket does not exist!")

    def delete_bucket(self, bucket_name):
        """
        To delete given bucket

        Args:

            bucket_name     (str)   --      name of the bucket to be deleted

        Raises
            Exception
                if deletion of bucket fails

        """
        try:
            bucket = self.get_bucket(bucket_name)
            bucket.delete(force=True)
            if self.check_if_bucket_exists(bucket_name):
                raise Exception('Failed to delete bucket. its exists in cloud')
            self.log.info("Bucket deleted successfully")
        except Exception as google_exception:
            self.log.exception(
                "Error occurred during bucket deletion: {0}".format(google_exception))

    def list_objects(self, bucket_name):
        """
        To list all blobs inside given bucket

        Args:

            bucket_name     (str)   --  name of bucket whose objects to be listed

        Returns:

            (list)      -       list of objects inside given bucket

        Raises
            Exception
                if it fails to list the blobs/objects

        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            blobs = bucket.list_blobs()
            objects = []
            for blob in blobs:
                objects.append(blob.name)
            return objects
        except Exception as google_exception:
            raise Exception(
                "issue in listing the blobs of given bucket: %s",
                str(google_exception))

    def download_single_object(
            self,
            bucket_name,
            source_blob,
            destination_file):
        """
        To download object from given bucket

        Args:

            bucket_name         (str)   --  name of bucket in cloud

            source_blob         (str)   --  name of object to be downloaded

            destination_file    (str)   --  destination file name in which object will be downloaded

        Raises
            Exception
                if it fails to download the object/blob
        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            blob = bucket.blob(source_blob)
            blob.download_to_filename(destination_file)
            self.log.info(
                'Blob %s downloaded to %s',
                source_blob,
                destination_file)
        except Exception as google_exception:
            raise Exception(
                "Failed to download the object : %s",
                google_exception)

    def upload_single_item(
            self,
            bucket_name,
            source_file_name,
            destination_blob_name):
        """
        To upload given file bucket

        Args:
                bucket_name              (str)   --     name of bucket in cloud

                source_file_name         (str)   --     name of file to be uploaded with full path

                destination_blob         (str)   --     destination blob name which
                                                        will uploaded in cloud

        Raises
            Exception
                if it fails to upload the object/blob
        """

        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)
            self.log.info(
                'File %s uploaded as blob %s.',
                destination_blob_name,
                source_file_name)
        except Exception as google_exception:
            raise Exception(
                "Failed to upload the object : %s",
                google_exception)

    def delete_blob(self, bucket_name, blob_name):
        """
        To delete blob from cloud bucket

        Args:
            bucket_name         (str)       --      name of cloud bucket in
                                                    which object to be deleted exists

            blob_name           (str)       --      name of blob/object to be deleted from cloud

        Raises
            Exception
                if deletion of object fails

        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
        except Exception as delete_exception:
            raise Exception(
                "Deletion of cloud blob failed due to : %s",
                delete_exception)

    def delete_folder_in_cloud(self, bucket_name, subfolder_prefix):
        """
        To delete a subfolder inside the google bucket

        Args:
            bucket_name         (str)       --      name of the bucket inside which
                                                    subfolder to be deleted resides

            subfolder_prefix    (str)       --      prefix of subfolder to be deleted

        Raises:
            Exception
                if it fails during deletion
        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            for blob in bucket.list_blobs(prefix=subfolder_prefix):
                blob.delete()
        except Exception as delete_exception:
            raise Exception(
                "Deletion of cloud blob failed due to : %s",
                delete_exception)

    def get_blob_size(self, bucket_name, blob_name):
        """
        Returns size of given blob in cloud

        Args:
            bucket_name         (str)       --      name of bucket in cloud

            blob_name           (str)       --      name of blob whose size to be fetched

        Returns:
            (int)   -   size of blob in cloud bucket

        Raises
            Exception
                if it fails to fetch the blob size

        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            blob = bucket.get_blob(blob_name)
            blob_size = blob.size
            return blob_size
        except Exception as google_exception:
            raise Exception(
                "Error occurred while fetching blob size : %s",
                google_exception)

    def populate_data(self, bucket_name, local_directory_name):
        """
        Method to populate data to cloud for testing

        Args:
            bucket_name             (str)       --      name of bucket in cloud

            local_directory         (str)       --      local directory containing source files

            local_directory_path    (str)       --      path of local directory to be uploaded

        """
        local_directory_path = self.controller_object.join_path(self.common_dir_path,
                                                                local_directory_name)
        if not os.path.exists(local_directory_path):
            os.mkdir(local_directory_path)

        # generate files to upload to cloud
        self.file_generator(local_directory_path=local_directory_path, count=10)

        # Create bucket
        check_status = self.check_if_bucket_exists(bucket_name)
        self.log.info(check_status)
        if not check_status:
            self.log.info("bucket not existing")
            self.create_bucket(bucket_name)

        # Upload test files to created bucket
        self.upload_folder_to_cloud(
            bucket_name,
            local_directory_name,
            local_directory_path)

        if not os.path.exists(local_directory_path):
            os.mkdir(local_directory_path)

    def download_google_bucket(self, bucket_name, base_folder_name):
        """Downloads bucket from Google cloud
            Args:
                    bucket_name         (str)       --      name of bucket in cloud

                    base_folder_name    (str)       --      name of folder to which
                                                            bucket has to be downloaded

            Raises :
                Exception :
                    if it fails to download container

        """
        bucket = self.google_storage.get_bucket(bucket_or_name=bucket_name)
        local_path = self.controller_object.join_path(
            self.common_dir_path, base_folder_name)
        current_path = os.getcwd()
        os.mkdir(local_path)
        os.chdir(local_path)
        try:
            for blob in bucket.list_blobs():
                filename = blob.name
                self.log.info("blob name :%s", filename)
                local_filename = self.controller_object.join_path(
                    local_path, filename)
                # local_filename = "{0}{1}{2}".format(
                #     local_path, self.controller_object.os_sep, filename)
                if "/" in "{}".format(blob.name):
                    self.log.info("Folder object in cloud")
                    head, tail = os.path.split("{}".format(blob.name))
                    test_path = self.controller_object.join_path(
                        os.getcwd(), head)
                    self.log.info("test_path : {0}\n".format(test_path))
                    if not os.path.isdir(test_path):
                        if tail == "":
                            self.log.info(
                                "it is directory object.creating new directory")
                            os.mkdir(test_path)
                        else:
                            self.log.info(
                                "creating directory and then downloading  the item")
                            os.makedirs(test_path)
                            local_file = self.controller_object.join_path(
                                test_path, tail)
                            # local_file = "{0}{1}{2}".format(test_path, self.controller_object.os_sep, tail)
                            self.download_single_object(
                                bucket_name, filename, local_file)
                    else:
                        self.log.info("parent directory exists already")
                        os.makedirs(test_path, exist_ok=True)
                        new_path = self.controller_object.join_path(
                            test_path, tail)
                        self.download_single_object(
                            bucket_name, filename, new_path)
                else:
                    self.log.info("single object download")
                    try:
                        self.download_single_object(
                            bucket_name, filename, local_filename)
                    except Exception as error:
                        raise Exception("The specified container does not exist on the cloud {0}".format(error))
        except Exception as google_exception:
            raise Exception(
                "Failed to download container due to :%s",
                google_exception)
        finally:
            os.chdir(current_path)

    def upload_folder_to_cloud(
            self,
            bucket_name,
            local_folder_name,
            local_folder_path):
        """
        To upload a folder to google cloud

        Args:
            bucket_name         (str)       --      name of bucket in cloud

            local_folder_name   (str)       --      name of local directory

            local_folder_path   (str)       --      path of local directory to be uploaded

        Raises
            Exception
                if it fails during upload operation to cloud

        """
        try:
            bucket = self.google_storage.get_bucket(bucket_name)
            # dummy file creation to create sub folder in cloud
            dummy_file = self.controller_object.join_path(
                local_folder_path, "dummy.txt")
            file_pointer = open(dummy_file, "w")
            file_pointer.close()
            if os.path.isdir(local_folder_path):
                self.log.info("local folder exists . Uploading it to cloud")
                destination_folder = "{0}/".format(local_folder_name)
                #  destination_folder = "{0}".format(local_folder_name, self.controller_object.os_sep)
                blob = bucket.blob(destination_folder)
                blob.upload_from_filename(dummy_file)
                self.log.info("Folder created successfully")
                os.remove(dummy_file)
                self.log.info("Lets upload the items of local folder")
                for filename in os.listdir(local_folder_path):
                    source_file_name = self.controller_object.join_path(
                        local_folder_path, filename)
                    destination_blob_name = "{0}{1}".format(
                        destination_folder, filename)
                    self.upload_single_item(
                        bucket_name, source_file_name, destination_blob_name)
        except Exception as google_exception:
            raise Exception(
                "Failed to upload the object : %s",
                google_exception)

    def get_google_secret_key(self):
        """
        Returns google instance secret key for given instance

        Returns:
            (str)       --      returns google instance secret key

        Raises:
            Exception
                if failed to get secret key from csdb

        """
        query2 = (
            "select attrVal from app_instanceprop where(componentnameid={0} "
            "and attrName in ('Google Cloud Cloud Password'))".format(
                self.instance.instance_id))
        self.csdb.execute(query2)
        cur = self.csdb.fetch_one_row()
        if cur:
            google_secret_key = cur[0]
        else:
            raise Exception(
                "Failed to get the sybase user password"
                "for given instance from commserve database")
        google_secret_key = cvhelper.format_string(
            self.commcell, google_secret_key)
        return google_secret_key

    def upload_files_to_bucket(self, bucket_name):
        """
        To upload files directly under google bucket

        Args:

            bucket_name     (str)       --      name of bucket in google

        Returns:

        """
        local_path = self.controller_object.join_path(
            self.common_dir_path, "single_files")
        self.controller_object.create_directory(local_path, force_create=True)
        # generate files to upload to cloud
        self.file_generator(local_directory_path=local_path, count=10)

        # self.file_generator(local_directory_path=local_path, count=10)
        for filename in os.listdir(local_path):
            source_file_name = self.controller_object.join_path(
                local_path, filename)
            self.upload_single_item(
                bucket_name,
                source_file_name,
                filename)

    def google_restore_overwrite_validation(self,
                                            subclient,
                                            bucket_name,
                                            original_data_path,
                                            overwrite=False):
        """
        To perform in-place restore with overwrite to google and validating the same

        Args:
            subclient           (object)    --      object of subclient class

            bucket_name         (str)       --      name of bucket in google cloud

            original_data_path  (str)       --      path where originals contents are downloaded

            overwrite           (bool)      --      unconditional overwrite files during restore
                                                    default: False
        Returns:

            (bool)      -       returns True if restore validation succeeds

        Raises:
            Exception
                if restore validation fails

        """
        self.log.info("original path : {0}".format(original_data_path))

        if not overwrite:
            overwrite_option = "overwrite only if file in media is newer"
        else:
            overwrite_option = "unconditional overwrite"

        # now mark one file for overwrite testing
        file_list = [f for f in os.listdir(original_data_path) if isfile(join(original_data_path, f))]
        self.log.info(file_list)
        version_1 = file_list[0]
        self.log.info("version_1: {0}".format(version_1))

        # make changes to version_1 file and save it as version_2
        versions_dir = self.controller_object.join_path(self.common_dir_path,
                                                        "versions_dir")
        os.mkdir(versions_dir)
        version_1_path = self.controller_object.join_path(original_data_path, version_1)
        version_2_path = self.controller_object.join_path(versions_dir, version_1)
        self.log.info("version1 path : {0}".format(version_1_path))
        self.log.info("version2 path : {0}".format(versions_dir))
        self.controller_object.copy_from_local(version_1_path, versions_dir)

        # add new contents to version_2 file
        new_line = OptionsSelector.get_custom_str()
        self.log.info(new_line)
        with open(version_2_path, 'a') as file_2:
            file_2.write(new_line * 6)
            file_2.write("\n")

        # now upload version_2 file to cloud
        self.upload_single_item(
            bucket_name,
            version_2_path,
            version_1)

        # in-place restore to google cloud without overwrite option
        self.log.info("restore to google %s", overwrite_option)
        self.cloud_storage_helper.cloud_apps_restore(subclient=subclient,
                                                     restore_type="in_place",
                                                     overwrite=overwrite)

        # download that modified file and compare with version_1 and version_2
        restored_file = self.controller_object.join_path(
            self.common_dir_path, "restored_file.txt")
        self.download_single_object(bucket_name,
                                    version_1,
                                    restored_file)
        self.log.info("successfully downloaded subclient"
                      " contents to local file system after restore")

        # validate restore
        version_1_result = self.controller_object.compare_files(self.controller_object,
                                                                version_1_path,
                                                                restored_file)

        version_2_result = self.controller_object.compare_files(self.controller_object,
                                                                version_2_path,
                                                                restored_file)
        if overwrite:
            self.log.info(
                "overwrite details before validation : %s",
                overwrite)
            validation_result = (version_1_result) and (version_2_result == False)
        else:
            self.log.info(
                "overwrite details before validation : %s",
                overwrite)
            validation_result = (version_1_result == False) and (version_2_result == True)

        if not validation_result:
            raise Exception(
                "File restored with {0} failed in validation".format(overwrite_option))
        else:
            self.log.info("File restored and passed validation")
            shutil.rmtree(versions_dir)
            self.log.info("Version directory is removed successfully")
            return True

    def fetch_file_metadata(self, bucket_name):
        """
        Fetches the properties meta data for all file objects in Google Cloud Storage

        Args:
            bucket_name (str)        : Name of the container to fetch the data from

        Returns:
            list                        : List of dict of the metadata retrieved from the cloud

            Example - [{'PATH': 'GCP\\10364200796756\\PIIFiles\\476_1644340532752\\512\\Lindsey good
            1621204276-3251\\Chester McCormick window 3259.txt', 'PARENT_DIR':
            '10364200796756\\PIIFiles\\476_1644340532752\\512\\Lindsey good 1621204276-3251', 'NAME': 'Chester
            McCormick window 3259.txt', 'FILE_SIZE': 28286, 'MIME_TYPE': 'text/plain', 'MODIFIED_TIME': 'February 08,
            2022 12:16:51 PM', 'CREATED_TIME': 'February 08, 2022 12:16:51 PM', 'ACCESS_TIME': 'February 08,
            2022 12:16:51 PM', 'FILE_OWNER': 'dummy_user', 'PARENT_DIR_PERMISSION': '', 'FILE_PERMISSION': '',
            'FILE_PERMISSION_READABLE': '', 'IS_DIR': 0}, {...}]

        """
        bucket = self.google_storage.lookup_bucket(bucket_name)
        assert isinstance(bucket, storage.Bucket), "Bucket Not Found"
        meta_data = []
        for obj in bucket.list_blobs():
            temp_dict = {}
            obj.reload(projection='full')
            file_path = obj.name.lstrip('/').replace('/', '\\')
            temp_dict[cs.FSO_METADATA_FIELD_PATH] = file_path
            file_string_split = file_path.rsplit('\\', 1)
            temp_dict[cs.FSO_METADATA_FIELD_PARENT_DIR] = file_string_split[0]
            temp_dict[cs.FSO_METADATA_FIELD_NAME] = file_string_split[1]
            temp_dict[cs.FSO_METADATA_FIELD_FILE_SIZE] = obj.size
            mime_type, encoding = mimetypes.guess_type(temp_dict[cs.FSO_METADATA_FIELD_NAME])
            if not mime_type:
                mime_type = 'application/octet-stream'
            temp_dict[cs.FSO_METADATA_FIELD_MIME_TYPE] = mime_type
            created_time_str = datetime.strftime(obj.time_created.astimezone(), "%B %d, %Y %r")
            temp_dict[cs.FSO_METADATA_FIELD_CREATED_TIME] = created_time_str
            temp_dict[cs.FSO_METADATA_FIELD_MODIFIED_TIME] = created_time_str
            temp_dict[cs.FSO_METADATA_FIELD_ACCESS_TIME] = created_time_str
            temp_dict[cs.FSO_METADATA_FIELD_FILE_OWNER] = obj.owner
            temp_dict[cs.FSO_METADATA_FIELD_PARENT_DIR_PERMISSION] = ""
            temp_dict[cs.FSO_METADATA_FIELD_FILE_PERMISSION] = ""
            temp_dict[cs.FSO_METADATA_FIELD_FILE_PERMISSION_READABLE] = ""
            temp_dict[cs.FSO_METADATA_FIELD_IS_DIR] = 0
            temp_dict[cs.FSO_METADATA_FIELD_FILE_TYPE] = file_string_split[1].rsplit('.')[-1]
            meta_data.append(temp_dict)
        return meta_data
