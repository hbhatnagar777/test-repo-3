import os
from datetime import datetime
import ibm_boto3
import oss2
from AutomationUtils import logger
from AutomationUtils import constants
from AutomationUtils.machine import Machine


class IbmHelper(object):
    """Helper class to perform ibm object storage operations"""

    def __init__(self, access_key, secret_key, endpoint):
        """Initializes azure helper object
        Args:

            access_key (str)      --        access key to the ibm storage resource

            secret_key(str)       --       secret key to the ibm storage resource

            endpoint(str)        --        endpoint on which ibm storage resides
        """
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = logger.get_log()
        self.machine = Machine()
        self.time_stamp = str(int(datetime.timestamp(datetime.now())))
        self.temp_folder_name = f"IbmTemp_{self.time_stamp}"
        self.common_dir_path = self.machine.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.machine.create_directory(self.common_dir_path,
                                      force_create=True)
        try:
            self.client = ibm_boto3.client('s3', aws_access_key_id=access_key,
                                           aws_secret_access_key=secret_key,
                                           endpoint_url=endpoint)
            self.log.info("session created successfully!")
        except Exception as exp:
            self.log.info(exp)
            raise exp

    def download_bucket(self, bucket_name, dir_name):
        """downloads the bucket contents
            Args:
                bucket_name(str) -- name of the bucket to download.

                dir_name(str)  -- directory to which bucket is downloaded.
        """
        response = self.client.list_objects(Bucket=bucket_name)
        objects = response["Contents"]
        local_path = self.machine.join_path(
            self.common_dir_path, dir_name)
        os.mkdir(local_path)
        os.chdir(local_path)
        try:
            for obj in objects:
                if "/" in obj["Key"]:
                    self.create_dir_download(obj["Key"], bucket_name)
                else:
                    with open(obj["Key"], 'wb') as data:
                        self.client.download_fileobj(bucket_name, obj["Key"], data)
        except Exception as exp:
            self.log.info(exp)
            raise exp
        finally:
            os.chdir(self.automation_directory)

    def create_dir_download(self, key, bucket_name):
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

                with open(self.machine.join_path(os.getcwd(), head, tail), 'wb') as data:
                    self.client.download_fileobj(bucket_name, key, data)

            except Exception as error:
                self.log.error(error)
                raise error

    def delete_bucket(self, bucket_name):
        """
        deletes alibaba bucket
        Args:
            bucket_name(str) -- name of the bucket to delete.
        """
        try:
            response = self.client.list_objects(Bucket=bucket_name)
            objects = response["Contents"]
            for obj in objects:
                self.client.delete_object(Bucket=bucket_name, Key=obj["Key"])
            self.client.delete_bucket(Bucket=bucket_name)
            self.log.info("Bucket deleted")
        except Exception as exp:
            self.log.info(exp)
            raise exp

    def cleanup(self):
        """
        To remove temp directories created
        during ibm helper object initialization
        """
        self.machine.remove_directory(self.common_dir_path)
