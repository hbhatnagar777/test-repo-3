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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing On Demand Backupset test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "OnDemand Backupset - all Basic NDMP functions"
        self.product = self.products_list.NDMP
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "SubclientContent": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None
        }

    def run(self):
        """Execution method for this test case"""
        log = logger.get_log()

        try:

            log.info("Started executing %s testcase", self.id)
            inputs = self.tcinputs

            log.info("Check if %s is on demand backupset", (str(inputs['BackupsetName'])))
            if not self.backupset.is_on_demand_backupset:
                raise Exception(
                    "{0} backupset is not on demand backupset.".format(
                        str(inputs['BackupsetName'])
                    )
                )
            log.info("%s is on demand backupset", (str(inputs['BackupsetName'])))

            log.info("*" * 10 + " Initialize helper objects " + "*" * 10)

            nas_helper = NASHelper()

            options_selector = OptionsSelector(self.commcell)

            if 'SubclientContent' in inputs:
                subclient_content = inputs['SubclientContent']
            else:
                raise Exception("SubclientContent is not specified. Please specify it.")

            if not isinstance(subclient_content, list):
                subclient_content = str(subclient_content).split(",")

            log.info("Get CommServ Machine class object")
            commserv_object = Machine(self.commcell.commserv_name, self.commcell)
            log.info("Successfully got commserv object")

            log.info("Get CommServ SDK object")
            commserv = self.commcell.clients.get(self.commcell.commserv_name)

            install_directory = commserv.install_directory
            log.info("Install Directory: %s", install_directory)

            on_demand_file = install_directory + "\\OnDemandInput\\contents.txt"

            on_demand_content = "`r`n".join(subclient_content)
            log.info("On Demand Content: %s", on_demand_content)

            log.info("Create Directive file on CommServ machine")
            commserv_object.create_file(on_demand_file, on_demand_content)

            log.info("Successfully create directive file on commserv")
            log.info("On Demand Input File Path: %s", on_demand_file)

            log.info("Create NAS Client object")
            nas_client = nas_helper.get_nas_client(self.client)

            nas_client.connect_to_cifs_share(
                str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
            )

            log.info("Will run below test case on: %s subclient", self.subclient)

            # check the data readers count
            log.info("*" * 10 + " Make Subclient Data readers to 3 " + "*" * 10)
            log.info("Number of data readers: " + str(self.subclient.data_readers))
            if self.subclient.data_readers != 3:
                log.info("Setting the data readers count to 3")
                self.subclient.data_readers = 3

            # run full backup
            log.info("*" * 10 + " Starting Subclient FULL Backup " + "*" * 10)
            job = self.subclient.backup("FULL", on_demand_input=on_demand_file)
            log.info("Started subclient FULL backup with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Full backup job with error: {0}".format(
                        job.delay_reason
                    )
                )

            log.info("Successfully finished subclient full backup")

            size = nas_client.get_content_size(subclient_content)

            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            log.info("*" * 10 + " Run out of place restore " + "*" * 10)

            # run restore out of place job
            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name, windows_restore_location, subclient_content)

            log.info("Started Restore out of place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + str(job.delay_reason))

            nas_helper.validate_windows_restored_content(
                nas_client, windows_restore_client, windows_restore_location, subclient_content
            )

            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            # run restore in place job
            job = self.subclient.restore_in_place([subclient_content[0]])

            log.info("Started restore in place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception("Failed to run restore in place job with error: " +
                                str(job.delay_reason))

            log.info("Successfully finished restore in place job")
            nas_helper.validate_filer_restored_content(
                nas_client, windows_restore_client, windows_restore_location,
                [subclient_content[0]])

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
