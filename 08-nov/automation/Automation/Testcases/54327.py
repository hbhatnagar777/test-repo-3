# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  Setup function for the test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

import os
import shutil
from Application.CloudStorage import google_storage_helper
from Application.CloudStorage.azure_helper import AzureHelper
from Application.CloudStorage.s3_helper import S3Helper
from Application.CloudStorage.cloud_storage_helper import CloudStorageHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Google Cloud Acceptance Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Google Cloud Restore Validation Test Case"
        self.google_helper = None
        self.cloud_storage_helper = None
        self.tcinputs = {
            "key_file_path":None,
            "bucket_name":None,
            "azure_client_name":None,
            "azure_instance_name":None,
            "s3_access_key":None,
            "s3_secret_key":None
        }
        self.subclient_name = "TEST_54327"
        self.google_helper = None
        self.cloud_storage_helper = None
        self.azure_helper = None
        self.s3_helper = None
        self.azure_session = None
        self.s3_session = None
        self.automation_directory = constants.AUTOMATION_DIRECTORY

    def setup(self):
        """Setup function of this test case"""
        self.google_helper = google_storage_helper.GoogleObjectStorage(self)
        self.cloud_storage_helper = CloudStorageHelper(self)
        self.azure_helper = AzureHelper(self)
        self.s3_helper = S3Helper(self)
        self.content = []
        self.azure_client = self.commcell.clients.get(self.tcinputs["azure_client_name"])
        self.azure_agent = self.azure_client.agents.get('cloud apps')
        self.azure_instance = self.azure_agent.instances.get(self.tcinputs["azure_instance_name"])
        azure_account_name = self.azure_instance.account_name
        azure_access_key = self.azure_instance.access_key
        self.azure_session = self.azure_helper.create_session_azure(azure_account_name,
                                                                    azure_access_key)
        self.s3_access_key = self.tcinputs["s3_access_key"]
        self.s3_secret_key = self.tcinputs["s3_secret_key"]
        self.s3_session = self.s3_helper.create_session_s3(self.s3_access_key,
                                                           self.s3_secret_key,
                                                           'ap-south-1')
        self.controller_object = self.google_helper.controller_object
        self.original_data_path = self.controller_object.join_path(self.google_helper.common_dir_path,
                                                                   'original_contents')


    def restore_validation(self, restored_contents):
        """
        To validate restore by comparing the actual data restored with original data

        Args:

            restored_contents       (str)   --      path representing restored directory

        Raises
            Exception
                if validation fails
        """
        if restored_contents.lower() == "azure_contents":
            restored_data_path = self.controller_object.join_path(self.automation_directory,
                                                                  restored_contents)
        else:
            restored_data_path = self.controller_object.join_path(self.google_helper.common_dir_path,
                                                                  restored_contents)
        self.log.info(self.original_data_path)
        self.log.info(restored_data_path)

        restore_status = self.controller_object.compare_folders(self.controller_object,
                                                                self.original_data_path,
                                                                restored_data_path)
        if restore_status is False:
            raise Exception("Restore to Given destination Failed During Validation")


    def run(self):
        """Main function for test case execution"""

        try:
            self.bucket_name = self.tcinputs["bucket_name"]
            self.log.info("bucket name :%s", self.bucket_name)

            # check if given bucket exists in cloud
            self.log.info("check if given bucket exists in cloud")
            bucket_status = self.google_helper.check_if_bucket_exists(self.bucket_name)
            if bucket_status is False:
                raise Exception("Not a valid cloud content")

            content_string = "/{0}".format(self.bucket_name)
            self.content.append(content_string)

            # create subclient with this bucket
            self.subclient = self.google_helper.create_google_subclient(self.subclient_name, self.content)


            # upload data to google bucket
            self.google_helper.populate_data(self.bucket_name, "incremental_data")

            # run full backup on this content
            self.log.info("Starting Full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Full")
            self.log.info("Full Backup completed successfully")


            # downloading the cloud contents to local
            self.log.info("Download original bucket data before restore")
            self.google_helper.download_google_bucket(self.bucket_name, "original_contents")
            self.log.info("successfully downloaded subclient "
                          "contents to local file system before restore")

            # perform cross cloud restore to azure blob
            self.log.info("Restore to Azure Cloud using configured instance")
            self.cloud_storage_helper.cross_cloud_restore_with_configured_instance(self.subclient,
                                                                                   self.azure_client.client_name,
                                                                                   self.azure_instance.instance_name,
                                                                                   "/")
            # download azure container after restore
            self.log.info("Downloading Azure Contents")
            self.azure_helper.download_contents_azure(self.azure_session,
                                                      self.subclient.content,
                                                      'azure_contents',
                                                      False)

            # Azure Restore Validation
            self.restore_validation('azure_contents')
            self.log.info("Restore to Azure Cloud Succeeded")

            proxy_name = self.instance.access_node
            proxy_credentials = {
                'amazon_s3': {
                    's3_host_url': 's3.amazonaws.com',
                    's3_access_key': self.s3_access_key,
                    's3_secret_key': self.s3_secret_key
                }
            }

            # perform cross cloud restore to S3 using proxy
            self.log.info("Restore to S3 cloud using  Proxy")
            # self.s3_helper.delete_container_s3(self.s3_session, self.bucket_name)
            self.cloud_storage_helper.cloud_apps_restore(subclient=self.subclient,
                                                         restore_type='out_of_place',
                                                         proxy_based=True,
                                                         destination_client_name=proxy_name,
                                                         destination_path="/",
                                                         proxy_based_credentials=proxy_credentials
                                                         )

            # download S3  bucket after restore
            self.log.info("Downloading S3 contents")
            current_path = os.getcwd()
            os.chdir(self.google_helper.common_dir_path)
            self.s3_helper.download_container_s3(self.s3_session, self.bucket_name)
            os.chdir(current_path)

            # S3 restore validation
            self.restore_validation(self.bucket_name)

            self.log.info("Restore to S3 Cloud using Proxy Succeeded")

            # Restore to Local File System
            self.log.info("File System Restore")

            self.cloud_storage_helper.restore_to_file_system(self.subclient,
                                                             self.commcell.commserv_name,
                                                             self.original_data_path)

            self.log.info("Restore to Local File System Succeeded")

            self.result_string = "Run of test case 54327 has completed successfully"

        except Exception as exp:
            self.log.error('Test Case Execution Failed with error: "%s"', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """tear down method of this testcase"""
        self.google_helper.google_helper_cleanup()
        self.instance.subclients.delete(self.subclient.subclient_name)
        # delete the additional data populated
        self.google_helper.delete_folder_in_cloud(self.bucket_name, "incremental_data/")
        # delete S3 bucket
        self.s3_helper.delete_container_s3(self.s3_session, self.bucket_name)
        # Delete Azure container
        self.azure_helper.delete_container_azure(self.azure_session,
                                                 self.bucket_name)
        azure_local_path = self.controller_object.join_path(self.automation_directory, "azure_contents")
        self.controller_object.remove_directory(azure_local_path)

