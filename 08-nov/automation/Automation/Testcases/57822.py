# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper
from datetime import datetime


class TestCase(CVTestCase):
    """Class for executing
        IBMi Restore of single object from a large library
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a library T57822 with 1,000 objects
        Step3: Run a full backup for the subclient and verify if it completes without failures.
        Step4: Check Full backup logs to backup command
        Step5: run OOP restore of first object of the libraries and verify and note down the duration.
        Step6: run OOP restore whole libraries and verify and note down the duration.
        step7: verify if restore of first object job has completed much earlier than restore of whole library job.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Restore of single object from a large library"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destlib = None
        self.sc_name = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE

            self.log.info("*** STARTING RUN FOR SC: {0} with {1} SCAN **".format(self.sc_name, self.scan_type.name))
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.log.info("Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "Subclient_{0}".format(self.id)
            srclib = "T{0}".format(self.id)
            self.destlib = "RST{0}".format(self.id)
            content = [self.client_machine.lib_to_path(srclib)]
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=content,
                                         scan_type=self.scan_type,
                                         delete=True)

            self.log.info("Step2: On client, create a library {0} with 1,000 objects".format(srclib))

            self.client_machine.populate_lib_with_data(library_name=srclib, tc_id=self.id, count=500, prefix="A")
            #first object name will be A578221
            self.client_machine.create_sourcepf(library=srclib, object_name='ZZZZZZZZZZ')
            # Last object name will be ZZZZZZZZZZ
            self.client_machine.create_savf(lib=srclib, size=50000)

            self.log.info("Step3: Run a full backup for the subclient *ALLUSR "
                          "and verify if it completes without failures.")
            full_job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: Check Full backup logs to backup command.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=full_job.job_id,
                                        expectedvalue='[SAVLIB]:[LIB({0}'.format(srclib))

            self.log.info("Step5: run OOP restore of first object of the "
                          "libraries and verify and note down the duration.")
            obj_to_restore = ["{0}{1}A{2}1.FILE".format(self.client_machine.lib_to_path(srclib),
                                                        self.slash_format,
                                                        self.id)]

            self.log.info("Object to restore is {}".format(obj_to_restore))
            self.log.info("destination library is {0}".format(self.client_machine.lib_to_path(self.destlib)))

            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            restore_job = self.helper.restore_out_of_place(
                destination_path=self.client_machine.lib_to_path(self.destlib),
                paths=obj_to_restore)

            diff1 = datetime.utcfromtimestamp(restore_job.summary['jobEndTime']) - \
                    datetime.utcfromtimestamp(restore_job.summary['jobStartTime'])
            self.log.info("Time taken for restore of first object is {0}".format(str(diff1)))

            self.client_machine.object_existence(library_name=self.destlib,
                                                 object_name="A{0}1".format(self.id),
                                                 obj_type='*FILE')

            self.log.info("Step6: run OOP restore of whole library and verify and note down the duration.")
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            restore_job = self.helper.restore_out_of_place(
                destination_path=self.client_machine.lib_to_path(self.destlib),
                paths=[self.client_machine.lib_to_path(srclib)])

            diff2 = datetime.utcfromtimestamp(restore_job.summary['jobEndTime']) - \
                    datetime.utcfromtimestamp(restore_job.summary['jobStartTime'])

            self.log.info("Time taken for restore of last object is {0}".format(str(diff2)))

            self.log.info("Perform cleanup of generated data libraries on client machine")

            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            self.client_machine.manage_library(operation='delete', object_name=srclib)

            if diff1 < diff2:
                self.log.info("Restore duration of single object from library is discarding rest of data.")
            else:
                raise Exception("First object restore has taken more duration than last object of the library")
            self.log.info("**%s SCAN RUN OF *ALLUSR COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED