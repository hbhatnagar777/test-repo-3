# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
This test case will verify CV S3 feature using BotoS3 covering upload, download ,List and search, delete
Validates below steps via automation.

1) Connect to CVS3 bucket
2)Upload data to bucket
3) Validate each file uploaded
4) Search and find files in CVS3
5) Download the files from CVS3
6) Compare file uploaded and Downloaded are Same (no corruption)
7) Delete the files uploaded in CVS3

Prerequisites: awscli /s3  package need to installed.
Testcase body
                        {
							"AccessKey": "",
							"SecretKey": "",
							"Endpoint": "",
							"BucketName": "",
							"ClientName": "",
							"TestPath": "E:",
							"AgentName": "File System",
							"StoragePolicyName": ""
						}

optinal  : "FileCount"--> no of files in string
          "FIleSize" --> Always in MB in string

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    s3_client_setup() -- Setup S3 with secret and Access and Bucket info

    creategbfile()   -- Create large file , size in MB

    upload_file()    --  UPload file to S3 bucket.

    check_file_exists() -- Check file exisits in S3 bucket.

    download_file()     -- Download file from S3 bucket

    get_logs_on_search_term() -- Search from Logs and print based on Search term.

    calculate_file_hash() --- Calculate hash of file provided.

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from datetime import datetime
import boto3, os, datetime, hashlib
import filecmp
import time, random
import random, string
from botocore.exceptions import ClientError


class TestCase(CVTestCase):
    """Testcase for CVS3 validation """

    def __init__(self, ):
        super(TestCase, self).__init__()
        self.name = "CV S3 Acceptance case with AWS CLI"
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = False
        self.tcinputs = {
            "AccessKey": None,
            "SecretKey": None,
            "Endpoint": None,
            "BucketName": None,
            "ClientName": None,
            "TestPath": None

        }
        self.helper = FSHelper(TestCase)
        self.random_str = str(random.randint(0, 10000))
        self.total_time = 0
        self.source_paths = []
        self.file_names = []

    def s3_client_setup(self):
        self.s3_client = boto3.client(service_name='s3',
                                      aws_access_key_id=self.tcinputs['AccessKey'],
                                      aws_secret_access_key=self.tcinputs['SecretKey'],
                                      endpoint_url=self.tcinputs['Endpoint'])
        self.log.info(self.s3_client)

    def creategbfile(self, filename, size_mb):
        file_name = filename
        file_size = size_mb * 1024 * 1024  # 1 GB in bytes
        chunk_size = 1024 * 1024  # 1 MB
        self.log.info("File is created  with size %s MB ", size_mb)
        self.log.info("File is created and added to list:  %s ", filename)

        def generate_random_text(size):
            return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation + ' \n', k=size))

        with open(file_name, 'w') as f:
            for _ in range(file_size // chunk_size):
                f.write(generate_random_text(chunk_size))
        print(f"{file_name} has been created with random text content.")

    def upload_file(self, filename, key):
        try:
            self.s3_client.upload_file(filename, self.s3_bucket, key)
            self.log.info("File %s uploaded to S3 bucket %s as %s" % (filename, self.s3_bucket, key))
        except FileNotFoundError:
            self.log.info("The file %s was not found.", filename)
        except ClientError as e:
            self.log.info(f"Failed to upload file: %s", str(e))
            raise Exception("Upload  failed for file %s", filename)

        self.file_names.append(filename)
        self.log.info(self.file_names)

    def check_file_exists(self, bucket_name, object_key):
        """ Check FIle exisits in S3 bucket"""
        try:
            self.s3_client.head_object(Bucket=bucket_name, Key=object_key)
            self.log.info("File %s exists in bucket", object_key)
        except ClientError as e:
            # If a 404 error is thrown, the object does not exist

            if e.response['Error']['Code'] == '404':
                self.log.info("File %s  doesnt exists in bucket retrying it.", object_key)
                response = self.s3_client.list_objects(Bucket=bucket_name)
                if 'Contents' in response:
                    # Extract the list of object keys from the response
                    response_keys = [obj['Key'] for obj in response['Contents']]
                    # Check if the specified key exists in the list of keys
                    if object_key in response_keys:
                        self.log.info("File %s exists in bucket", object_key)
                    else:
                        self.log.info("File %s doesnt exists in bucket", object_key)
                        raise Exception("File doesnt exist : %s", object_key)
                else:
                    self.log.info("File %s doesnt exists in bucket or empty ", object_key)
                    raise Exception("File doesnt exist : %s", object_key)
            else:
                # Handle other possible errors
                print(f"Error occurred: {e}")
                raise Exception("File doesnt exist : %s", object_key)

    def download_file(self, key, filename):
        """ Method to Download file from CVS3/ S3 interface"""
        try:
            # Download the file from S3
            self.s3_client.download_file(self.s3_bucket, key, filename)
            self.log.info("File %s downloaded from S3 bucket %s to  %s" % (key , self.s3_bucket, filename))
        except FileNotFoundError:
            self.log.info("The path %s was not found.", filename)
        except Exception as e:
            self.log.info(f"Failed to Download  file: %s", str(e))
            raise Exception("Download failed for file %s " % (key))

    def get_logs_on_search_term(self):
        """ Method to get logs for Performance Counters"""
        search_term = "LoggerTask - S3 PERF:"
        self.log.info("search term :%s", search_term)
        log_lines = self.helper.get_logs_for_job_from_file(
            log_file_name="CVDotNetContainer.log", search_term=search_term)
        trimsize = 6000
        trim_logs = log_lines[len(log_lines) - trimsize:]
        self.log.info(trim_logs)

    def calculate_file_hash(self, file_path, hash_algorithm='md5'):
        hash_func = hashlib.new(hash_algorithm)
        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def run(self):
        """Follows the following steps:
            Validate below steps via automation.
            1) Connect to CVS3 bucket
            2)Upload data to bucket
            3) Validate each file uploaded
            4) Search and find files in CVS3
            5) Download the files from CVS3
            6) Compare file uploaded and Downloaded are Same (no corruption)
            7) Delete the files uploaded in CVS3
        """

        self.log.info("Setting up S3client using BotoS3API")
        try:
            FSHelper.populate_tc_inputs(self)
            self.s3_bucket = self.tcinputs['BucketName']
            self.testpath = self.tcinputs['TestPath']
            slash_format = self.slash_format
            if self.testpath.endswith(slash_format):
                test_path = str(self.testpath).rstrip(slash_format)
            self.s3_client_setup()
            print(self.s3_client)
            if self.tcinputs.get('FileCount', False):
                self.num_files = int(self.tcinputs['FileCount'])
            else:
                self.num_files = 20

            for i in range(0, self.num_files):
                # Function to generate random data
                filename = 'random' + self.random_str + '_data' + str(i) + '.txt'
                upload_file_path = ("%s%s%s%s" % (self.testpath, slash_format, slash_format, filename))
                file_uploaded = os.path.basename(filename)
                if self.tcinputs.get('FileSize', False):
                    random_file_size = int(self.tcinputs['FileSize'])
                else:
                    random_file_size = random.randint(10, 100)
                self.creategbfile(upload_file_path, random_file_size)
                self.log.info(upload_file_path)
                self.log.info("File Uploaded to Cloud as %s: ", file_uploaded)
                now1 = datetime.datetime.now()
                self.log.info("Time of Upload %s: ", now1)
                self.upload_file(upload_file_path, file_uploaded)
                now2 = datetime.datetime.now()
                self.log.info("Time Ended after completion Upload %s: ", now2)
                # returns a timedelta object
                c = now2 - now1
                self.log.info("Time Difference %s: ", c)
                minutes = c.total_seconds() / 60
                self.log.info('Total difference in : %s ', minutes)
                self.log.info('Total difference in minutes for download file : %s ', minutes)
                # file_names = file_names.append(filename)
                self.total_time = self.total_time + int(minutes)

            self.log.info("Files uploaded are : %s", self.file_names)

            self.get_logs_on_search_term()
            time.sleep(300)

            for file in self.file_names:
                file_uploaded = os.path.basename(file)
                self.check_file_exists(self.s3_bucket, file_uploaded)

            for file in self.file_names:
                file_uploaded = os.path.basename(file)
                file_uploaded_without_extension = os.path.splitext(file_uploaded)[0]
                filename_down = str(file_uploaded_without_extension) + 'download.txt'
                download_file_path = ("%s%s%s%s" % (self.testpath, slash_format, slash_format, filename_down))
                now1 = datetime.datetime.now()
                self.log.info("Time of Download %s: ", now1)
                file_uploaded = os.path.basename(file)
                self.download_file(file_uploaded, download_file_path)
                now2 = datetime.datetime.now()
                self.log.info("Time of Download  %s: ", now2)
                # returns a timedelta object
                c = now2 - now1
                self.log.info("Time Difference %s: ", c)
                minutes = c.total_seconds() / 60
                self.log.info('Total difference in : %s ', minutes)
                self.log.info('Total difference in minutes for download file : % ', minutes)
                self.total_time = self.total_time + int(minutes)
                local_file_hash = self.calculate_file_hash(file)
                downloaded_file_hash = self.calculate_file_hash(download_file_path)
                if local_file_hash == downloaded_file_hash:
                    self.log.info("Files %s %s are identical" % (file, download_file_path))
                else:
                    self.log.info("Files %s %s are not  identical" % (file, download_file_path))
                    raise Exception("Files %s %s  are not same " % (file, download_file_path))

            self.get_logs_on_search_term()
            for file in self.file_names:
                file_uploaded = os.path.basename(file)
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=file_uploaded)
                self.log.info("Deleted File: %s ", file_uploaded)

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)
