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

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

import time

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing SMTAPE Full backup test case"""

    def __init__(self):
        """Initializes the TestCase object"""
        super(TestCase, self).__init__()
        self.name = "SMTAPE Full Backup"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.tcinputs = {
            "FilerRestoreLocation": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def setup(self):
        """Initializes pre-requisiets for this test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing %s testcase", self.id)

            self._log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            nas_helper = NASHelper()

            # Check if backupset is image backupset else set it as image backupset
            if not self.backupset.is_image_backupset:
                self._log.info("Backupset is not image backupset. Will make it image backupset.")
                self.backupset.set_image_backupset()

            self._log.info("Backupset is image backupset")

            restore_location = str(self.tcinputs['FilerRestoreLocation'])

            self._log.info("Get NAS Client object")
            nas_client = nas_helper.get_nas_client(self.client, self.agent)

            self._log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            self._log.info("Will run below test case on: %s subclient", self.subclient)

            # check the data readers count
            self._log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self._log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                self._log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            # run full backup
            self._log.info("*" * 10 + " Starting Subclient FULL Backup " + "*" * 10)
            job = self.subclient.backup("FULL")
            self._log.info("Started subclient FULL backup with job id: " + str(job.job_id))
            time.sleep(10)
            if not job.wait_for_completion():
                raise Exception("Failed to run full backup job with error: " + job.delay_reason)

            time.sleep(10)

            # Validate if SMTape backup job was ran
            nas_helper.validate_if_smtape_backup(str(job.job_id))

            # Mark the subclient volumes as restricted
            self._log.info("Read volume name from subclient content")
            volume = self.subclient.content[0].split("/")[2]
            self._log.info("Volume name from subclient content is: " + volume)

            self._log.info("Creating backup volume %s object", volume)
            backup_volume = nas_client.get_volume(volume)

            restore_location = restore_location.lstrip("/vol/")
            self._log.info("Get Restore volume %s object", restore_location)
            restore_volume = nas_client.get_volume(restore_location)

            # Set destination filer to restricted state
            self._log.info("Restrict restore volume")
            restore_volume.restrict()

            self._log.info("*" * 10 + " Run out of place restore " + "*" * 10)
            # run restore out of place job
            restore_location = "/vol/" + restore_location
            job = self.subclient.restore_out_of_place(
                self.client.client_name, restore_location, self.subclient.content
            )

            self._log.info("Started restore out of place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + job.delay_reason
                )

            self._log.info("Successfully finished restore out of place job")

            self._log.info("Validate Restored content")
            diff = []
            _, source_volume = nas_client.get_path_from_content(self.subclient.content[0])
            _, destination_volume = nas_client.get_path_from_content(restore_location)
            diff = nas_client.compare_volumes(
                source_volume, destination_volume, ignore_files=nas_helper.ignore_files_list
            )

            if diff != []:
                raise Exception(
                    "Restore out of place validation failed. Different files list: {0}".format(
                        str(diff)
                    )
                )

            self._log.info("Successfully validated restored content")

            # Check if SMTape restore job
            nas_helper.validate_if_smtape_restore(str(job.job_id))

            # Check volume status
            nas_helper.validate_volume_status(backup_volume, 'ONLINE')

        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
