# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import os
import random
import filecmp
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Application.Sharepoint import sharepointconstants
from Application.Sharepoint.sharepointhelper import SharepointHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Backup, Browse and Restore - WebApp - Non RBS--Same Configuration"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SHAREPOINT
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

        self.sphelper = None
        self.spmachine = None
        self.subclient = None

        self.tcinputs = {
            "SQLClientName": None,
            "SQLInstanceName": None,
            "StoragePolicyName": None,
            "SharepointFarmAdmin": None,
            "SharepointFarmPass": None
        }

    def run(self):
        """Main function for test case execution"""
        log = self.log
        clientname = self.client.client_name
        spfarmuser = self.tcinputs["SharepointFarmAdmin"]
        spfarmpass = self.tcinputs["SharepointFarmPass"]
        sqlclient = self.tcinputs["SQLClientName"]
        sqlinstance = self.tcinputs["SQLInstanceName"]
        storagepolicy = self.tcinputs["StoragePolicyName"]

        self.sphelper = SharepointHelper(self, clientname, sqlclient, sqlinstance, spfarmuser, spfarmpass)
        self.spmachine = Machine(self.sphelper.spautomation.spclient)

        try:
            spdump_file1 = sharepointconstants.METADATA_BEFORE_FULL
            spdump_file2 = sharepointconstants.METADATA_AFTER_RESTORE

            log.info("Started executing {0} testcase".format(self.id))
            self.sphelper.sharepoint_setup(storagepolicy)

            self.subclient = self.sphelper.subclient

            # generate metadata info file
            self.sphelper.spvalidate.create_meta_data(
                os.path.join(self.sphelper.tcdir, spdump_file1),
                self.sphelper.webapp
            )

            # run a Full backup
            self.sphelper.sharepoint_backup("Full")

            # run an in-place restore
            self.sphelper.sharepoint_restore(self.subclient.content)

            # generate metadata info file after restore
            self.sphelper.spvalidate.create_meta_data(
                os.path.join(self.sphelper.tcdir, spdump_file2),
                self.sphelper.webapp
            )

            # check if some files still exist after restore
            if not self.sphelper.spvalidate.check_file(
                    self.sphelper.spsetup_list[0]["web_application"],
                    self.sphelper.library_name,
                    self.sphelper.site_title,
                    os.path.basename(random.choice(self.sphelper.upload_file_list))
            ):
                raise Exception("Failed to validate file in library.")

            # validate metadata info files
            if not filecmp.cmp(
                    os.path.join(self.sphelper.tcdir, spdump_file1),
                    os.path.join(self.sphelper.tcdir, spdump_file2)):

                raise Exception("Sharepoint metadata files from backup and restore do not match!")

            log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        # delete webapp
        self.sphelper.spinit.delete_web_application()
        # delete directory
        if not self.spmachine.remove_directory(self.sphelper.tcdir):
            self.log.error("Unable to delete temporary testcase folder: [{0}]".format(self.sphelper.tcdir))
        # delete subclient
        self.backupset.subclients.delete(self.subclient.subclient_name)
