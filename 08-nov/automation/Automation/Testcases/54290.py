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


from Application.CloudStorage import google_storage_helper
from Application.CloudStorage.cloud_storage_helper import CloudStorageHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Google Cloud Acceptance Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Google Cloud Acceptance Test Case"
        self.google_helper = None
        self.cloud_storage_helper = None
        self.tcinputs = {
            "key_file_path":None,
            "bucket_name":None
        }
        self.subclient_name = "TEST_54290"


    def setup(self):
        """Setup function of this test case"""
        self.google_helper = google_storage_helper.GoogleObjectStorage(self)
        self.cloud_storage_helper = CloudStorageHelper(self)
        self.content = []


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

            # run full backup on this content
            self.log.info("Starting Full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Full")
            self.log.info("Full Backup completed successfully")

            # upload data to google bucket
            self.google_helper.populate_data(self.bucket_name, "incremental_data")

            # run incremental backup job
            self.log.info("Starting Incremental backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Incremental")
            self.log.info("Incremental Backup completed successfully")

            # run synthetic full job
            self.log.info("Starting Synthetic Full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Synthetic_Full")
            self.log.info("Synthetic Full Backup completed successfully")


            # downloading the cloud contents to local
            self.log.info("Download original bucket data before restore")
            self.google_helper.download_google_bucket(self.bucket_name, "original_contents")
            self.log.info("successfully downloaded subclient "
                          "contents to local file system before restore")

            # delete the cloud bucket
            self.google_helper.delete_bucket(self.bucket_name)

            # in-place restore to google cloud
            self.cloud_storage_helper.cloud_apps_restore(self.subclient,
                                                         restore_type="in_place")

            # validate if bucket available in cloud
            bucket_status = self.google_helper.check_if_bucket_exists(self.bucket_name)
            if bucket_status is False:
                raise Exception("Restore validation failed as bucket not available in cloud")

            # download data to local after restore
            self.log.info("Download restored bucket data after restore")
            self.google_helper.download_google_bucket(self.bucket_name, "restored_contents")
            self.log.info("successfully downloaded subclient"
                          " contents to local file system after restore")

            # validate restore
            original_data_path = self.google_helper.controller_object.join_path(self.google_helper.common_dir_path,
                                                                                'original_contents')
            restored_data_path = self.google_helper.controller_object.join_path(self.google_helper.common_dir_path,
                                                                                'restored_contents')
            self.log.info("original path : %s", original_data_path)
            self.log.info("restored path : %s", restored_data_path)

            validate_result = self.google_helper.controller_object.compare_folders(self.google_helper.controller_object,
                                                                                   original_data_path,
                                                                                   restored_data_path)
            if validate_result is False:
                raise Exception("Restore Validation Failed")
            self.log.info("Restore Validation Succeeded")
            self.log.info("Google Cloud Acceptance Test Case Passed")
            self.result_string = "Run of test case 54290 has completed successfully"

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
