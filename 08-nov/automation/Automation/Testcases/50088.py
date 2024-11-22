# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    _run_backup()       --  initiates backup job

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing Wild Card content for Subclient Content and Filter"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Wild Card content for Subclient Content and Filter"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "SubclientContent": None,
            "SubclientFilter": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def _run_backup(self, backup_type):
        """Initiates backup job and waits for completion"""
        self._log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self.subclient.backup(backup_type)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        return job

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()
        self._nas_helper = NASHelper()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing %s testcase", self.id)

            options_selector = OptionsSelector(self.commcell)

            if 'SubclientContent' in self.tcinputs:
                subclient_content = self.tcinputs['SubclientContent']

                # Check if subclient content is list
                if not isinstance(subclient_content, list):
                    subclient_content = subclient_content.split(",")

                # set subclient content
                self._log.info("*" * 10 + " Set Subclient Content " + "*" * 10)
                self._log.info("Subclient content to set: " + str(subclient_content))
                self.subclient.content = subclient_content

            else:
                self._log.info("Reading subclient content from object")
                subclient_content = self.subclient.content

            if 'SubclientFilter' in self.tcinputs:
                subclient_filter = self.tcinputs['SubclientFilter']

                # Check if subclient filter is list
                if not isinstance(subclient_filter, list):
                    subclient_filter = subclient_filter.split(",")

                # set subclient filter
                self._log.info("*" * 10 + " Set Subclient Filter " + "*" * 10)
                self._log.info("Subclient Filter to set: " + str(subclient_filter))
                self.subclient.filter_content = subclient_filter

            else:
                self._log.info("Reading subclient filter content from object")
                subclient_filter = self.subclient.filter_content

            new_filter_content = []
            for filter_content in subclient_filter:
                new_filter_content.append(str(filter_content).split("/")[-1])

            self._log.info("Found last part of subclient filter: " + str(new_filter_content))

            # Mark the subclient volumes as restricted
            self._log.info("Get NAS client object")
            nas_client = self._nas_helper.get_nas_client(self.client, self.agent)
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            subclient_content_from_pattern = []
            volumes_from_pattern = []
            for content in subclient_content:
                volumes_from_pattern += nas_client.get_volumes_by_pattern(str(content))
            for volume in volumes_from_pattern:
                subclient_content_from_pattern.append("/vol/"+str(volume))
            self._log.info(
                "Subclient Content Formed from Pattern: " + str(
                    subclient_content_from_pattern
                )
            )

            self._log.info("Will run below test case on: %s subclient", self.subclient)

            # check the data readers count
            self._log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self._log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                self._log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            # run full backup
            self._run_backup("FULL")

            for i in range(len(subclient_content_from_pattern)):
                volume_path, _ = nas_client.get_path_from_content(subclient_content_from_pattern[i])
                self._nas_helper.copy_test_data(nas_client, volume_path)

            self._run_backup("INCREMENTAL")

            for i in range(len(subclient_content_from_pattern)):
                volume_path, _ = nas_client.get_path_from_content(subclient_content_from_pattern[i])
                self._nas_helper.copy_test_data(nas_client, volume_path)

            self._run_backup("DIFFERENTIAL")

            # Get the subclient content to backup
            restore_content = subclient_content_from_pattern
            self._log.info("Restore content: " + str(restore_content))
            size = nas_client.get_content_size(subclient_content_from_pattern)

            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            self._log.info("*" * 10 + " Run out of place restore " + "*" * 10)

            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name, windows_restore_location, restore_content
            )
            self._log.info("Started Restore out of place with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + job.delay_reason
                )

            self._log.info("Successfully finished restore out of place")

            self._nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, windows_restore_location, restore_content
            )

            self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            # run restore in place job
            job = self.subclient.restore_in_place(restore_content)

            self._log.info("Started restore in place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: " + job.delay_reason
                )

            self._log.info("Successfully finished restore in place job")

            self._nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location, restore_content
            )

        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
