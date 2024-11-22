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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Backup and restore content in content file with SWA(*SYNCLIB)
        Step1, configure BackupSet and Subclient with ContentFile content
        Step2: On client, create a library and objects.
        Step3: On client, create the content file and add content to content file.
        Step3: Run a full backup for the subclient.
        Step4: verify the full backup logs and validate all advanced options.
        Step5: re-create the SC with new values for additional options.
        Step6: Run a full backup for the subclient.
        Step7: verify the full backup logs and validate all advanced options.
        Step8: Perform OOP restore and verify.
        Step9: Cleanup libraries and content file from client disk.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Backup and restore content in content file with SWA(*SYNCLIB)"
        # Other attributes which will be initialized in FSHelper.populate_tc_inputs
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.scan_type = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE

            self.log.info("*** STARTING RUN FOR SC ADDITIONAL OPTIONS validation WITH <ContentFIle> ***")
            self.log.info("Step1, configure BackupSet and Subclient with ContentFile content")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "ContentFile_{0}".format(self.id)
            srclib = "TC{0}".format(self.id)
            destlib = "RST{0}".format(self.id)
            content_file = "/tmp/{0}".format(srclib)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=["<ContentFile>{0}".format(content_file)],
                                         scan_type=self.scan_type,
                                         delete=True)
            self.log.info("update the subclient additional options and set SWA(*SYNCLIB.)")
            sc_options = {'savact': '*SYNCLIB',
                          'savactwait': 345,
                          'savactmsgq': 'QSYS/QSYSOPR',
                          'txtlibSyncCheckPoint': 'SNDMSG MSG("AUTOMATION SYNCLIB TC#{0}") TOUSR(*SYSOPR)'.format(
                              self.id),
                          'dtacpr': '*NO',
                          'updhst': False,
                          'accpth': '*SYSVAL',
                          'tgtrls': self.client_machine.get_ibmi_version(),
                          'pvtaut': False,
                          'qdta': False,
                          'splfdta': False,
                          'savfdta': False
                          }
            self.helper.set_ibmi_sc_options(**sc_options)
            self.log.info("Step2: On client, create a library {0} and objects.".format(srclib))
            self.client_machine.populate_lib_with_data(library_name=srclib, tc_id=self.id, count=5, prefix="A")
            object_name = ['SRCPF1', "SRCPF2", "SRCOF3"]
            for each in object_name:
                self.client_machine.create_sourcepf(library=srclib, object_name=each)

            self.log.info("Step3: On client, create the content file and add content to content file.")
            self.client_machine.run_ibmi_command(command="echo '##' >{0}".format(content_file))
            self.client_machine.run_ibmi_command(command="echo 'SAVLIB LIB({0}) OMITOBJ(({0}/{1} *FILE) "
                                                 "({0}/{2} *FILE) ({0}/{3} *FILE))' >>{4}".format(srclib,
                                                                                                  object_name[0],
                                                                                                  object_name[1],
                                                                                                  object_name[2],
                                                                                                  content_file)
                                                 )
            self.client_machine.run_ibmi_command(command="echo 'SAVOBJ LIB({0}) OBJ({1} {2} {3}) "
                                                         "OBJTYPE(*FILE)' >>{4}".format(srclib,
                                                                                        object_name[0],
                                                                                        object_name[1],
                                                                                        object_name[2],
                                                                                        content_file)
                                                 )

            self.log.info("Step3: Run a full backup for the subclient.")
            job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options)
            self.log.info("Step5: re-create the SC with new values for additional options.")
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=["<ContentFile>{0}".format(content_file)],
                                         scan_type=self.scan_type,
                                         delete=True)
            sc_options1 = {'savact': '*SYNCLIB',
                           'savactwait': 123,
                           'dtacpr': '*LOW',
                           'updhst': True,
                           'accpth': '*YES',
                           'tgtrls': self.client_machine.get_ibmi_version("*SUPPORTED"),
                           'pvtaut': True,
                           'qdta': True,
                           'splfdta': True,
                           'savfdta': True
                           }
            self.helper.set_ibmi_sc_options(**sc_options1)
            self.log.info("Step6: Run a full backup for the subclient.")
            job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step7: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options1)

            self.log.info("Step8: Perform OOP restore and verify.")
            self.helper.run_restore_verify(slash_format=self.slash_format,
                                           data_path=self.client_machine.lib_to_path(srclib),
                                           tmp_path=self.client_machine.lib_to_path(destlib),
                                           data_path_leaf="")

            self.log.info("Step9: Cleanup libraries and content file from client disk")
            self.client_machine.manage_library(operation='delete', object_name=srclib)
            self.client_machine.manage_library(operation='delete', object_name=destlib)
            self.client_machine.run_ibmi_command(command="rm {0}".format(content_file))

            self.log.info("**CONTENT FILE BACKUP AND RESTORE COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
