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
    """Class for executing Google Cloud Overwrite Restore Validation Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Google Cloud Overwrite Restore Validation Test Case"
        self.google_helper = None
        self.cloud_storage_helper = None
        self.tcinputs = {
            "key_file_path":None
        }
        self.subclient_name = "TEST_54428"
        self.bucket_name = None
        self.controller_object = None
        self.content = None
        self.original_data_path = None

    def setup(self):
        """Setup function of this test case"""
        self.bucket_name = "bucket_54428"
        self.cloud_storage_helper = CloudStorageHelper(self)
        self.google_helper = google_storage_helper.GoogleObjectStorage(self)
        self.content = []
        self.controller_object = self.google_helper.controller_object
        self.original_data_path = self.controller_object.join_path(self.google_helper.common_dir_path,
                                                                   'original_contents')

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("bucket name :%s", self.bucket_name)
            # create bucket in cloud
            self.google_helper.create_bucket(self.bucket_name)


            # # upload data to google bucket
            # self.google_helper.populate_data(self.bucket_name, "full_data")

            # upload files to bucket directly
            self.google_helper.upload_files_to_bucket(self.bucket_name)

            content_string = "/{0}".format(self.bucket_name)
            self.content.append(content_string)

            # create subclient with this bucket
            self.subclient = self.google_helper.create_google_subclient(self.subclient_name,
                                                                        self.content)

            # run full backup on this content
            self.log.info("Starting Full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Full")

            # downloading the cloud contents to local
            self.log.info("Download original bucket data before restore")
            self.google_helper.download_google_bucket(self.bucket_name, "original_contents")
            self.log.info("successfully downloaded subclient "
                          "contents to local file system before restore")

            no_overwrite = self.google_helper.google_restore_overwrite_validation(self.subclient,
                                                                                  self.bucket_name,
                                                                                  self.original_data_path,
                                                                                  overwrite=False)

            unconditional_overwrite = self.google_helper.google_restore_overwrite_validation(self.subclient,
                                                                                             self.bucket_name,
                                                                                             self.original_data_path,
                                                                                             overwrite=True)

            self.log.info("Overwrite only if file in media"
                          " is newer result : %s", no_overwrite)
            self.log.info("Overwrite Validation Result : %s", unconditional_overwrite)


            validate_result = no_overwrite and unconditional_overwrite
            if validate_result is False:
                raise Exception("Restore Validation Failed")
            self.log.info("Restore Validation Succeeded")
            self.log.info("Google Cloud Overwrite Restore "
                          "Validation Test Case Passed")
            self.result_string = "Run of test case 54428 has completed successfully"

        except Exception as exp:
            self.log.error('Test Case Execution Failed with error: "%s"', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """tear down method of this testcase"""
        self.google_helper.google_helper_cleanup()
        self.instance.subclients.delete(self.subclient.subclient_name)
        # delete the data populated
        self.google_helper.delete_bucket(self.bucket_name)
