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

        setup()                 --  Initial configuration for the test case

        configure_sc()          --  Configure predefined SC and another SC with content

        generate_client_data()  --  Generate Incremental data on client machine.

        restore_verify()        --  Initiates OOP restore for content and verify the Advanced restore options

        verify_client_logs()    --  Verify client logs if correct paramemter are used

        cleanup()               --  Cleanup the data on client machine

        run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for executing
            IBMi - Optimized scan backup validation for SYNCLIB with library level and object level filters
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Optimized scan backup validation for SYNCLIB with library level and object level filters"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.tcinputs = {
            "IBMiMode": None,
            "whichPython": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.destlib = None
        self.job = None
        self.IBMiMode = None
        self.usr_lib = None
        self.subclient_name = None
        self.backupset_name = None
        self.filters = None

    def setup(self):
        """ Initial configuration for the test case. """

        try:
            # Initialize test case inputs
            self.log.info("***TESTCASE: %s***", self.name)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.backupset_name = "backupset_{0}".format(self.id)
            self.subclient_name = "subclient_{0}".format(self.id)
            self.destlib = "AUTR{0}".format(self.id)
            self.usr_lib = ["ZKAO0{0}".format(self.id),
                            "ZKAO1{0}".format(self.id),
                            "ZKAO2{0}".format(self.id),
                            "ZKAE{0}".format(self.id)]
            self.filters = ["ZKAX1", "ZKAX2", "LUCK"]

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def configure_sc(self):
        """
               Configure subclient with content, filters and enable optimized scan.
        """
        self.log.info("Configuring SYNCLIB subclient with Library & object level filters")
        self.helper.create_backupset(name=self.backupset_name)
        sc_filters = [self.client_machine.lib_to_path(self.usr_lib[2])]
        for each in self.filters:
            for each_lib in self.usr_lib:
                sc_filters.append("{0}/{1}.FILE".format(self.client_machine.lib_to_path(each_lib), each))

        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=["/QSYS.LIB/ZKAO*.LIB",
                                              self.client_machine.lib_to_path(self.usr_lib[3])],
                                     filter_content=sc_filters,
                                     scan_type=ScanType.OPTIMIZED,
                                     data_readers=2,
                                     allow_multiple_readers=True,
                                     delete=True)
        self.helper.enable_synclib()

    def generate_client_data(self, run_count=0):
        """ Generate data on IBMi client machine """
        if run_count == 0:
            for each in self.usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=2)
                for each_obj in self.filters:
                    self.client_machine.create_sourcepf(library=each, object_name=each_obj)
        elif run_count == 1:
            for each in self.usr_lib:
                self.client_machine.create_sourcepf(library=each, object_name="INCF")

    def run_backup_and_verify(self, run_count=0):
        """ Generate data on IBMi client machine """
        if run_count == 0:
            self.job = self.helper.run_backup(backup_level="Full")[0]
        elif run_count == 1:
            self.job = self.helper.run_backup(backup_level="Incremental")[0]
        self.verify_client_logs(run_count)

    def restore_verify(self):
        """
            Initiates OOP restore for content and verify the restored data and objects reporting ...
        """
        self.log.info("Run OOP restore of libraries and verify.")

        for each in self.usr_lib:
            if each is not self.usr_lib[2]:
                self.log.info(
                    "run OOP restore of library [{0}] to library [{1}] and verify.".format(each, self.destlib))
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                # Delete filtered objects from source libraries
                for each_object in self.filters:
                    self.client_machine.delete_file_object(library=each, object_name=each_object)

                self.job = self.helper.restore_out_of_place(
                    destination_path=self.client_machine.lib_to_path("{0}".format(self.destlib)),
                    paths=[self.client_machine.lib_to_path("{0}".format(each))],
                    restore_ACL=False,
                    preserve_level=0)

                self.log.info("Deleting the filtered objects from source libraries...")
                for each_obj in self.filters:
                    if self.client_machine.is_object_exists(library_name=self.destlib,
                                                            object_name=each_obj,
                                                            obj_type='*FILE'):
                        raise Exception(
                            "Filtered object {0}/{1} not supposed to be restored.".format(each, each_obj))
                self.helper.compare_ibmi_data(
                    source_path="{0}/*".format(self.client_machine.lib_to_path("{0}".format(each))),
                    destination_path="{0}/*".format(self.client_machine.lib_to_path("{0}".format(self.destlib))))
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                self.log.info("Verifying client logs if correct command is used for restore.")
                self.verify_client_logs(run_count=self.usr_lib.index(each)+2)

    def verify_client_logs(self, run_count=0):
        """
        Verify client logs if correct parameter are used
        """
        if run_count == 0:
            self.log.info("Check Full backup logs to validate backup command.")
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='[LIB({0}'.format(self.usr_lib[0])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='[LIB({0}'.format(self.usr_lib[1])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='[LIB({0}'.format(self.usr_lib[3])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='OMITOBJ(*USRSPC)'
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVACT(*SYNCLIB)'
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='CMDUSRSPC('
                                        )
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::ExpandWCContent',
                                        jobid=self.job.job_id,
                                        expectedvalue="Skipping filtered content [/QSYS.LIB/{0}".
                                        format(self.usr_lib[2])
                                        )
        elif run_count == 1:
            self.log.info("Check incremental backup logs to validate backup command.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::ExpandWCContent',
                                        jobid=self.job.job_id,
                                        expectedvalue="Skipping filtered content [/QSYS.LIB/{0}".
                                        format(self.usr_lib[2])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='[LIB({0}'.format(self.usr_lib[0])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='[LIB({0}'.format(self.usr_lib[1])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='[LIB({0}'.format(self.usr_lib[3])
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='OMITOBJ(*USRSPC)'
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVACT(*SYNCLIB)'
                                        )
            self.helper.verify_from_log('cvbkpdrv*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue='CMDUSRSPC('
                                        )
        else:
            self.log.info("Verify client restore logs if command RSTLIB is used for full backup restore.")
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="Restore type=4 [RSTLIB] CMD"
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="SAVLIB({0}".format(self.usr_lib[run_count - 2])
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="RSTLIB({0}".format(self.destlib)
                                        )
            self.log.info("Verify client restore logs if command RSTOBJ is used for inc backup restore.")
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="Restore type=2 [RSTOBJ] CMD"
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="SAVLIB({0}".format(self.usr_lib[run_count - 2])
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="RSTLIB({0}".format(self.destlib)
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=self.job.job_id,
                                        expectedvalue="OBJ(*ALL)"
                                        )

    def cleanup(self):
        """
            Cleanup the data on client machine
        """
        for each in self.usr_lib:
            self.client_machine.manage_library(operation='delete', object_name=each)
        self.client_machine.manage_library(operation='delete', object_name=self.destlib)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)
            self.configure_sc()
            self.generate_client_data(run_count=0)
            self.run_backup_and_verify(run_count=0)
            self.generate_client_data(run_count=1)
            self.run_backup_and_verify(run_count=1)
            self.restore_verify()
            self.cleanup()
            self.log.info("**IBMi: VALIDATION OF FILTERS WITH SYNCLIB BACKUP HAS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
