import os
from datetime import datetime
import oss2
from AutomationUtils import logger
from AutomationUtils import constants
from AutomationUtils.machine import Machine


class Alibaba(object):
    """Helper class to perform azure blob storage operations"""

    def __init__(self, access_key, secret_key):
        """Initializes azure helper object
        Args:

            access_key (str)      --        access key to the alibaba storage resource

            secret_key(str)       --       secret key to the alibaba storage resource

        """
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = logger.get_log()
        self.machine = Machine()
        self.time_stamp = str(int(datetime.timestamp(datetime.now())))
        self.temp_folder_name = f"AlibabaTemp_{self.time_stamp}"
        self.common_dir_path = self.machine.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.machine.create_directory(self.common_dir_path,
                                      force_create=True)
        try:
            self.session = oss2.Auth(access_key, secret_key)
            self.log.info("session created successfully!")
        except Exception as exp:
            self.log.info(exp)
            raise exp

    def download_bucket(self, bucket_name, endpoint, dir_name):
        """downloads the bucket contents
            Args:
                bucket_name(str) -- name of the bucket to download.

                endpoint(str) --  the location where buckets are residing.

                dir_name(str)  -- directory to which bucket is downloaded.
        """
        bucket = oss2.Bucket(self.session, endpoint, bucket_name)
        local_path = self.machine.join_path(
            self.common_dir_path, dir_name)
        os.mkdir(local_path)
        os.chdir(local_path)
        try:
            for obj in oss2.ObjectIteratorV2(bucket):
                if "/" in f"{obj.key}":
                    self.create_dir_download(obj.key, bucket)
                else:
                    bucket.get_object_to_file(obj.key, obj.key)
        except Exception as exp:
            self.log.info(exp)
            raise exp
        finally:
            os.chdir(self.automation_directory)

    def create_dir_download(self, key, bucket_obj):
        """creates directory if required to download
            Args:
                key(str) -- object name of objet in alibaba object storage.

                bucket_obj(object) -- Bucket object of oss2 package.
        """
        if str(key)[-1] == "/":
            self.machine.create_directory(self.machine.join_path(os.getcwd(), key))
        else:
            head, tail = os.path.split(f"{key}")
            try:
                if not self.machine.check_directory_exists(self.machine.join_path(os.getcwd(), head)):
                    self.machine.create_directory(self.machine.join_path(os.getcwd(), head))

                bucket_obj.get_object_to_file(key, self.machine.join_path(os.getcwd(), head, tail))
            except Exception as error:
                self.log.error(error)
                raise error

    def download_file(self, key, bucket_obj, path):
        """downloads file to given path
            Args:
                key(str) -- object name of objet in alibaba object storage.

                bucket_obj(object) -- Bucket object of oss2 package.

                path(str) -- path to which file will be downloaded.
        """
        try:
            obj_stream = bucket_obj.get_object()
            head, tail = os.path.split(f"{key}")
            download_path = os.path.join(path, tail)
            bucket_obj.get_object_to_file(key, download_path)
        except Exception as error:
            self.log.error(error)
            raise error

    def delete_bucket(self, bucket_name, endpoint):
        """
        deletes alibaba bucket
        Args:
            bucket_name(str) -- name of the bucket to delete.

             endpoint(str) --  the location where buckets are residing.
        """
        try:
            # Delete the bucket.
            bucket = oss2.Bucket(self.session, endpoint, bucket_name)
            for obj in oss2.ObjectIteratorV2(bucket):
                if str(obj.key)[-1] != "/":
                    bucket.delete_object(obj.key)
                else:
                    for sobj in oss2.ObjectIterator(bucket, prefix=obj.key):
                        bucket.delete_object(sobj.key)
                    bucket.delete_object(obj.key)
            bucket.delete_bucket()
        except oss2.exceptions.BucketNotEmpty:
            self.log.info('bucket is not empty.')
        except oss2.exceptions.NoSuchBucket:
            self.log.info('bucket does not exist')

    def empty_bucket(self, bucket_name, endpoint):
        """
        empties alibaba bucket
        Args:
            bucket_name(str) -- name of the bucket to delete.

             endpoint(str) --  the location where buckets are residing.
        """
        try:
            # Empty the bucket.
            bucket = oss2.Bucket(self.session, endpoint, bucket_name)
            for obj in oss2.ObjectIteratorV2(bucket):
                if str(obj.key)[-1] != "/":
                    bucket.delete_object(obj.key)
                else:
                    for sobj in oss2.ObjectIterator(bucket, prefix=obj.key):
                        bucket.delete_object(sobj.key)
                    bucket.delete_object(obj.key)
        except oss2.exceptions.BucketNotEmpty:
            self.log.info('bucket is not empty.')
        except oss2.exceptions.NoSuchBucket:
            self.log.info('bucket does not exist')

    def cleanup(self):
        """
        To remove temp directories created
        during alibaba helper object initialization
        """
        self.machine.remove_directory(self.common_dir_path)
