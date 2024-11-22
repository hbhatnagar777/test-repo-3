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

import random
import string

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing SMTAPE Incremental and Differential backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "SMTAPE Incremental and Differential backup"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "FilerRestoreLocation": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def _run_smtape_backup(self, backup_type, snap_name):
        """Initiates smtap snap backup job and validates whether the job ran as smtape"""
        self._log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self.subclient.backup(backup_type, snap_name=snap_name)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )
        self._log.info("Successfully finished %s backup job", backup_type)

        self._nas_helper.validate_if_smtape_backup(str(job.job_id))

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self._log = logger.get_log()
        self.commserver_name = self.commcell.commserv_name
        self._nas_helper = NASHelper()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing %s testcase", self.id)

            # Read inputs for restore out of place
            if 'FilerRestoreLocation' in self.tcinputs:
                restore_location = str(self.tcinputs['FilerRestoreLocation'])
            else:
                raise Exception("FilerRestoreLocation is not specified. Please specify it.")

            if not self.backupset.is_image_backupset:
                self._log.info("Backupset is not image backupset. Will make it image backupset.")
                self.backupset.set_image_backupset()

            self._log.info("Backupset is image backupset")

            self._log.info("Get NAS Client object")
            nas_client = self._nas_helper.get_nas_client(self.client, self.agent)

            self._log.info("Connect to cifs share on NAS client")
            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            self._log.info(
                "Will run below test case on: %s subclient", str(self.tcinputs['SubclientName'])
            )

            # check the data readers count
            self._log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            self._log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                self._log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            random_string = "".join([random.choice(string.ascii_letters) for _ in range(4)])

            self._log.info("Read volume name from subclient content")
            volume = str(self.subclient.content[0]).split("/")[2]
            self._log.info("Volume name from subclient content: " + volume)

            self._log.info("Create backup volume %s object", volume)
            backup_volume = nas_client.get_volume(volume)

            full_snap_name = "Snap_FULL_" + random_string
            self._log.info(
                "Creating %s snap for %s volume", full_snap_name, backup_volume.name
            )

            backup_volume.create_snap(full_snap_name)

            self._log.info(
                "Successfully created snap: %s for volume: %s", full_snap_name, backup_volume.name
            )

            if not backup_volume.has_snap(full_snap_name):
                raise Exception(
                    "Snap {0} not found in list for volume: {1}".format(
                        full_snap_name, backup_volume.name
                    )
                )

            self._run_smtape_backup("FULL", full_snap_name)

            volume_path, _ = nas_client.get_path_from_content(self.subclient.content[0])
            self._nas_helper.copy_test_data(nas_client, volume_path)

            # Create Snapshot
            inc_snap_name = "Snap_INC_" + random_string
            self._log.info(
                "Creating %s snap for %s volume", inc_snap_name, backup_volume.name
            )

            backup_volume.create_snap(inc_snap_name)

            self._log.info(
                "Successfully created snap: %s for volume: %s", inc_snap_name, backup_volume.name
            )

            if not backup_volume.has_snap(inc_snap_name):
                raise Exception(
                    "Snap {0} not found in list for volume: {1}".format(
                        inc_snap_name, backup_volume.name
                    )
                )

            self._run_smtape_backup("INCREMENTAL", inc_snap_name)

            restore_location = restore_location.lstrip("/vol/")
            self._log.info("Creating restore volume %s object", restore_location)
            restore_volume = nas_client.get_volume(restore_location)

            # Set destination filer to restricted state
            self._log.info("Restrict restore volume")
            restore_volume.restrict()

            self._log.info("*" * 10 + " Run out of place restore " + "*" * 10)
            # run restore out of place job
            restore_location = "/vol/" + restore_location
            job = self.subclient.restore_out_of_place(
                self.client.client_name, restore_location, self.subclient.content)

            self._log.info("Started restore out of place job with job id: " + job.job_id)

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: {0}".format(
                        job.delay_reason
                    )
                )

            self._log.info("Successfully finished restore out of place job")

            self._log.info("Validate Restored content")
            diff = []
            volume_path, source_volume = nas_client.get_path_from_content(
                self.subclient.content[0]
            )
            volume_path, destination_volume = nas_client.get_path_from_content(restore_location)
            diff = nas_client.compare_volumes(
                source_volume, destination_volume,
                ignore_files=self._nas_helper.ignore_files_list)

            if diff != []:
                raise Exception(
                    "Restore out of place validation failed. Different files list: {0}".format(
                        str(diff)
                    )
                )

            self._log.info("Successfully validated restored content")

            # Check if SMTape restore job
            self._nas_helper.validate_if_smtape_restore(str(job.job_id))

            # Check volume status
            self._nas_helper.validate_volume_status(restore_volume, 'ONLINE')

            volume_path, _ = nas_client.get_path_from_content(self.subclient.content[0])
            self._nas_helper.copy_test_data(nas_client, volume_path)

            # Create Snapshot
            diff_snap_name = "Snap_DIFF_" + random_string
            self._log.info(
                "Creating %s snap for %s volume", diff_snap_name, backup_volume.name
            )

            backup_volume.create_snap(diff_snap_name)

            self._log.info(
                "Successfully created snap: %s for volume: %s", diff_snap_name, backup_volume.name
            )

            if not backup_volume.has_snap(diff_snap_name):
                raise Exception(
                    "Snap {0} not found in list for volume: {1}".format(
                        diff_snap_name, backup_volume.name
                    )
                )

            self._run_smtape_backup("DIFFERENTIAL", diff_snap_name)

            try:
                self._log.info("Deleting differential snap")
                backup_volume.delete_snap(diff_snap_name)

                self._log.info("Deleting incremental snap")
                backup_volume.delete_snap(inc_snap_name)

                self._log.info("Deleting full snap")
                backup_volume.delete_snap(full_snap_name)
            except Exception as exp:
                self._log.warning("Failed to delete snap with error: %s", str(exp))

        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
