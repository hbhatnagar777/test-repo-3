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
        self.name = "Google Cloud Instance Creation Test Case"
        self.google_helper = None
        self.cloud_storage_helper = None
        self.tcinputs = {
            "key_file_path":None,
            "storage_policy":None,
            "access_node":None,
            "google_access_key":None,
            "google_secret_key":None

        }
        self.subclient_name = "TEST_54380"
        self.instance_properties = None
        self.bucket_name = "bucket_54380"


    def setup(self):
        """Setup function of this test case"""

        self.instance_properties = {
            'instance_name': 'test_instance_54380',
            'description': 'instance for google',
            'storage_policy': self.tcinputs['storage_policy'],
            'number_of_streams': 3,
            'access_node': self.tcinputs['access_node'],
            'cloudapps_type': 'google_cloud',
            'host_url': 'storage.googleapis.com',
            'access_key': self.tcinputs['google_access_key'],
            'secret_key': self.tcinputs['google_secret_key']

        }
        # create google Instance
        self.instance = self.agent.instances.add_cloud_storage_instance(self.instance_properties)
        self.google_helper = google_storage_helper.GoogleObjectStorage(self)
        self.cloud_storage_helper = CloudStorageHelper(self)
        self.content = []


    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("bucket name :%s", self.bucket_name)

            # upload data to google bucket
            self.google_helper.populate_data(self.bucket_name, "incremental_data")


            content_string = "/{0}".format(self.bucket_name)
            self.content.append(content_string)

            # create subclient with this bucket
            self.subclient = self.google_helper.create_google_subclient(self.subclient_name, self.content)

            # run full backup on this content
            self.log.info("Starting Full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Full")
            self.log.info("Full Backup completed successfully")


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
            self.log.info("Google Cloud Instance Test Case Passed")
            self.result_string = "Run of test case 54380 has completed successfully"

        except Exception as exp:
            self.log.error('Test Case Execution Failed with error: "%s"', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """tear down method of this testcase"""
        # delete google instance
        self.agent = self.client.agents.get('cloud apps')
        self.agent.instances.delete('test_instance_54380')
        self.google_helper.google_helper_cleanup()
        # delete the data populated
        self.google_helper.delete_bucket(self.bucket_name)
