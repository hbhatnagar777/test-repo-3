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

    configure_sc()          --  Configure predefined SC and another SC with content

    restore_verify()        --  Initiates restore for content Configured in non-pre-defined SC  and Verify if it fails.

    cleanup()               --  Cleanup the data on client machine

    run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Verify if pre-defined subclient backup is filtering content from other subclients
        Validate for *ALLUSR, *LINK, *ALLDLO and *HST
        for non-VTL, test with Optimized scan and regular scan do as following.
            Configure SC with some user libraries.
            Backup *ALLUSR and verify if content is not backedup.
            Perform LFS cleanup.
            Configure SC with some user directory.
            Backup *LINK and verify if content is not backedup.
            Perform IFS  cleanup.
            Configure SC with some user folder.
            Backup *ALLDLO and verify if content is not backedup.
            Perform QDLS cleanup.
            Configure SC with some QHST files as content.
            Backup *HST log and verify if content is not backedup.
            Perform HST files cleanup.
        for VTL and Parallel VTL, test with regular scan do as following.
            Configure SC with some user libraries.
            Backup *ALLUSR and verify if content is not backedup.
            Perform LFS cleanup.
            Configure SC with some user directory.
            Backup *LINK and verify if content is not backedup.
            Perform IFS  cleanup.
            Configure SC with some user folder.
            Backup *ALLDLO and verify if content is not backedup.
            Perform QDLS cleanup.
            Configure SC with some QHST files as content.
            Backup *HST log and verify if content is not backedup.
            Perform HST files cleanup.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify if pre-defined subclient backup is filtering content from other subclients"
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
        self.subclient_name = None
        self.client_machine = None
        self.destlib = None
        self.sc_name = None
        self.job = None
        self.scan_type = None
        self.IBMiMode = None
        self.src_path = None

    def configure_sc(self, scan_type, content_type):
        """
               Configure predefined and another subclient with content

               Args:
                   scan_type              (str)           -- Scan Type
                   content_type      (str)            -- Type of content
                   (LFS/IFS/QDLS/QHST)
               """
        self.log.info("Configuring subclient for %s", content_type)
        if self.IBMiMode == "NON-VTL":
            data_readers = 5
            allow_multiple_readers = True
        else:
            data_readers = 1
            allow_multiple_readers = False
        self.src_path = []
        if content_type == "LFS":
            self.subclient_name = "Filter_LFS_{0}".format(self.id)
            usr_lib = ["AUT{0}".format(self.id), "A#C{0}".format(self.id), "A#C{0}1".format(self.id)]
            for each in usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=2)
            self.src_path.append(self.client_machine.lib_to_path(usr_lib[0]))
            self.src_path.append("/QSYS.LIB/{0}*.LIB".format(usr_lib[1]))

            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=self.src_path,
                                         scan_type=scan_type,
                                         delete=False)
            self.sc_name = "*ALLUSR"
            self.log.info("Performance libraries and locked libraries are added as filters to *ALLUSR")
            filters = ["/QSYS.LIB/QPFR*.LIB", "/QSYS.LIB/QUSRD*.LIB"]
            self.log.info("Save file data is ignored to reduce the backup duration")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.sc_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=scan_type,
                                                  filter_content=filters,
                                                  data_readers=data_readers,
                                                  savfdta=False,
                                                  allow_multiple_readers=allow_multiple_readers,
                                                  delete=False)

        elif content_type == "IFS":
            self.src_path = ["/AUT{0}".format(self.id), "/AUT{0}1".format(self.id)]
            self.subclient_name = "Filter_IFS_{0}".format(self.id)
            for each in self.src_path:
                self.client_machine.populate_ifs_data(directory_name=each,
                                                      tc_id=self.id,
                                                      count=10,
                                                      prefix="F",
                                                      delete=True)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=self.src_path,
                                         scan_type=scan_type,
                                         delete=True)

            self.subclient_name = "*LINK"
            filters = ["/QSR", "/QIBM", "/tmp", "/QFileSvr.400", "/QOpenSys", "/var/commvault"]
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=scan_type,
                                                  filter_content=filters,
                                                  data_readers=data_readers,
                                                  allow_multiple_readers=allow_multiple_readers,
                                                  delete=False)
            self.log.info("adding filters to *LINK subclient to avoid failures from system directories %s", filters)

        elif content_type == "QDLS":
            usr_flr = ["A{0}".format(self.id), "A{0}1".format(self.id)]
            for each in usr_flr:
                self.client_machine.manage_folder(operation='delete', folder_name=each)
                self.client_machine.populate_QDLS_data(folder_name=each, tc_id=self.id, count=5)
                self.src_path.append("/QDLS/{0}".format(each))
            self.subclient_name = "Filter_QDLS_{0}".format(self.id)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=self.src_path,
                                         scan_type=scan_type,
                                         delete=True)

            self.subclient_name = "*ALLDLO"
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=scan_type,
                                                  data_readers=data_readers,
                                                  allow_multiple_readers=allow_multiple_readers,
                                                  delete=False)

        elif content_type == "QHST":
            hstobj = ["QHST{0}".format(self.id), "QHST{0}1".format(self.id)]

            for each in hstobj:
                self.client_machine.delete_file_object(library="QSYS", object_name="{0}".format(each))
                self.src_path.append("{0}{1}{2}.FILE".format(self.test_path, self.slash_format, each))
                self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(each))

            self.subclient_name = "Filter_QHST_{0}".format(self.id)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=self.src_path,
                                         scan_type=scan_type,
                                         delete=True)
            self.subclient_name = "*HST log"
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=scan_type,
                                                  data_readers=data_readers,
                                                  allow_multiple_readers=allow_multiple_readers,
                                                  delete=False)

    def restore_verify(self):
        """
                Initiates restore for content Configured in non-pre-defined SC  and Verify if it fails.
        """
        self.log.info("Starting restore {0} and verify if job fails ".format(self.src_path))
        restore_options = {'wait_to_complete': False}
        self.job = self.helper.restore_in_place(paths=self.src_path,
                                                **restore_options)
        self.log.info("Verify if restore job ss failed")
        self.job.wait_for_completion()
        self.log.info("Restore job#{0} has reported as {1}".format(self.job.job_id, self.job.status.lower))
        if not self.job.status.lower() == "failed":
            raise Exception("Restore Job status is not failed, job has status: {0}".format(self.job.status))

    def cleanup(self, content_type):
        """
        Cleanup the data on client machine

           Args:
               content_type      (str)            -- Type of content
               (LFS/IFS/QDLS/QHST)
        """
        self.log.info("Cleanup the {0} on client machine.")
        if content_type == "LFS":
            usr_lib = ["AUT{0}".format(self.id), "AUT{0}1".format(self.id)]
            for each in usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)
        elif content_type == "IFS":
            self.src_path = ["/AUT{0}".format(self.id), "/AUT{0}1".format(self.id)]
            for each in self.src_path:
                self.client_machine.remove_directory(directory_name=each)
        elif content_type == "QDLS":
            usr_flr = ["A{0}".format(self.id), "A{0}1".format(self.id)]
            for each in usr_flr:
                self.client_machine.manage_folder(operation='delete', folder_name=each)
        elif content_type == "QHST":
            hstobj = ["QHST{0}".format(self.id), "QHST{0}1".format(self.id)]
            for each in hstobj:
                self.client_machine.delete_file_object(library="QSYS", object_name="{0}".format(each))

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
                self.log.info("mode is %s", self.IBMiMode)
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=True)
            self.scan_type = [ScanType.RECURSIVE]
            if self.IBMiMode == "NON-VTL":
                self.scan_type.append(ScanType.OPTIMIZED)
            fs_type=["LFS", "IFS", "QDLS", "QHST"]
            self.log.info("*** STARTING VALIDATION OF PRE-DEFINED SC IS FILTERING CONTENT FROM OTHER SC CONTENT "
                          "WITH {0}***".format(self.IBMiMode))
            for each in self.scan_type:
                for each_type in fs_type:
                    if each is ScanType.OPTIMIZED and each_type is "QDLS":
                        self.log.info("SKIPPING: QDLS cannot be saved using optimized scan.")
                    else:
                        self.log.info("Starting {0} run for {1}".format(each.name, each_type))
                        self.configure_sc(scan_type=each, content_type=each_type)
                        self.job = self.helper.run_backup(backup_level="Full")[0]
                        self.restore_verify()
                        self.cleanup(content_type=each_type)
                        self.log.info("{0} has properly filtered the other SC content.".format(each_type))
            self.log.info("*ALLUSR, *LINK, *ALLDLO, *HST log subclients are filtering content from custom subclients")
            self.log.info("**OTHER SC CONTENT IS FILTERED FROM PRE-DEFINED SC VALIDATION COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
