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
    __init__() 											--  Initialize TestCase class

    run()													--  run function of this test case

    verify_whether_all_phases_ran()	-- function validates whether job ran Scan, Backup, ArchiveIndex phase or no.

    add_data_to_path()							-- function to create Data for Backup
"""

from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper

class TestCase(CVTestCase):
    """
    1. Create backupset for this testcase if it doesn't exist.
    2. For all the allowed scan type do the following on the backupset
        2.1  Create subclient for the scan type if it doesn't exist.
             SubClient as   Subclientcontentfolder\file?.doc
                            Subclientcontentfolder\*.txt
                            SubclientcontentFolder\*.log
        2.2  Add full data for the current run.                 
        2.3  Run a full backup for the subclient and verify it completes without failures   --> should run all phases
        2.4  Without changing any data run a Incremental Job      --> Scan Marking Job
        2.5  Remove one entry(file?.doc) from subclient content
        2.6  Run an incremental backup for the subclient and verify it completes without failures.  --> Should run all phases
        2.7  Remove txt file from disk
        2.8  Run an incremental backup for the subclient and verify it completes without failures.  --> should run all phases
        2.9  Run a synthfull job
        2.10  Run an incremental backup after synthfull for the subclient and verify it completes without failures. -->Scan Marking Job
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File System BAckup Scan Marking job where deleted aboject are involved"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.verify_dc = None
        self.skip_classic = None
        self.client_machine = None
        self.acls = None
        self.unicode = None
        self.xattr = None
        self.long_path = None
        self.problematic = None
        self.WAIT_TIME = None
        self.RETAIN_DAYS = None
        self.should_wait = None

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            test_path = self.test_path
            slash_format = self.slash_format
            helper = self.helper
            machine = self.client_machine
            if test_path.endswith(slash_format):
                test_path = str(test_path).rstrip(slash_format)
            storage_policy = self.storage_policy

            log.info("""File System Data Protection - Full,Incremental,Differential
                        This test case does the following
                        1. Create backupset for this testcase if it doesn't exist.
        
                        2. For all the allowed scan type do the following on the backupset
                            2.1  Create subclient for the scan type if it doesn't exist.
                                SubClient as    Subclientcontentfolder\file?.doc
                                Subclientcontentfolder \*.txt
                                SubclientcontentFolder\*.log 
                        2.2  Add full data for the current run.
                        2.3  Run a full backup for the subclient and verify it completes without failures    
                        2.4  Without changing any data run a Incremental Job
                        2.5  Remove one entry(file?.doc) from subclient content
                        2.6  Run an incremental backup for the subclient and verify it completes without failures.
                        2.7  Remove txt file from disk
                        2.8  Run an incremental backup for the subclient and verify it completes without failures.
                        2.9  Run a synthfull job
                        2.10  Run an incremental backup after synthfull and verify it completes without failures.
                        """)

            log.info("Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            helper.create_backupset(backupset_name)

            log.info("Executing steps for all the allowed scan type")
            for scan_type in ScanType:
                # Skip Change Journal for UUnx
                if (self.applicable_os != 'WINDOWS' and scan_type.value == ScanType.CHANGEJOURNAL.value):
                    continue
                # Skip DC if verify_dc is not provided
                if (self.applicable_os != 'WINDOWS' and scan_type.value == ScanType.OPTIMIZED.value):
                    if not self.verify_dc:
                        continue

                # Skip Classic scan if specified in inputs
                is_recursive = scan_type.value == ScanType.RECURSIVE.value
                if (self.skip_classic and is_recursive):
                    continue
    
                # Check if We need to wait for I/O to get flushed
                self.should_wait = True
                if is_recursive:
                    if self.applicable_os == 'UNIX':
                        if 'darwin' not in machine.os_flavour.lower():
                            self.should_wait = False
    
                log.info("**** Check With SubClient Content Without Filters****")
                log.info("**STARTING RUN FOR {0} SCAN**".format(scan_type.name))
                log.info("Create subclient for the scan type {0} if it doesn't exist.".format(scan_type.name))

                subclient_name = ("subclient_{0}_{1}".format(self.id, scan_type.name.lower()))
                subclient_content = []
                subclient_content.append("{0}{1}{2}{3}*.txt".format(test_path, slash_format, subclient_name, slash_format))
                subclient_content.append("{0}{1}{2}{3}file?.doc".format(test_path, slash_format, subclient_name, slash_format))
                subclient_content.append("{0}{1}{2}{3}*.log".format(test_path, slash_format, subclient_name, slash_format))

                subclient_content_path = "{0}{1}{2}".format(test_path, slash_format, subclient_name)

                full_data_path =  subclient_content_path

                helper.create_subclient(name=subclient_name,
                                        storage_policy=storage_policy,
                                        content=subclient_content,
                                        scan_type=scan_type,
                                        delete=True)

                log.info("Add full data for the current run.")

                log.info("Adding data under path: {0}".format(full_data_path))
                list_of_source_files = self.add_data_to_path( full_data_path )
    
                # wait for for journals to get flushed
                if self.should_wait:
                    log.info("Waiting for journals to get flushed")
                    sleep(self.WAIT_TIME)
    
                log.info(" Run a full backup for the subclient "
                            "and verify it completes without failures.")
                helper.run_backup_verify(scan_type, "Full")[0]

                log.info("Without changing any data run a Incremental Job")
                job_incr1 = helper.run_backup_verify(scan_type, "Incremental", scan_marking=True)

                log.info("Job[" + job_incr1[0].job_id + "] ran as Scan Marking Job")
                subclient_content1 = []
                subclient_content1.append("{0}{1}{2}{3}*.txt".format(test_path, slash_format, subclient_name, slash_format))
                subclient_content1.append("{0}{1}{2}{3}*.log".format(test_path, slash_format, subclient_name, slash_format))
    
                helper.update_subclient(content=subclient_content1,
                                            scan_type=scan_type)

                job_incr2 = helper.run_backup_verify(scan_type, "Incremental")
                if self.verify_whether_all_phases_ran(job_incr2[0].job_id):
                    log.info("Job[" + job_incr1[0].job_id + "] ran with all phases")
                    deleted_file = list_of_source_files[0]
                    machine.delete_file(deleted_file)
                    list_of_source_files.remove(deleted_file)
    
                    job_incr3 = helper.run_backup_verify(scan_type, "Incremental")
                    if self.verify_whether_all_phases_ran(job_incr3[0].job_id):
                        log.info("Job[" + job_incr1[0].job_id + "] ran with all phases")
                        log.info("Run a synthfull job")
                        helper.run_backup_verify(scan_type, "Synthetic_full")
                        log.info("Run an incremental backup after synthfull and verify it completes without failures.")
                        job_incr3 = helper.run_backup_verify(scan_type, "Incremental",scan_marking='True')
                        log.info("Incremental backup after Synthull ran as Scan Marking Job")
                    else:
                        raise Exception("Job[" + job_incr3[0].job_id + "] did not ran with all phases")
                else:
                    raise Exception("Job[" + job_incr2[0].job_id + "] did not ran with all phases")

            machine.remove_directory(test_path)
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: {0}'.format(str(excp)))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def add_data_to_path(self, full_data_path):
        """"Add files to the folder path and return the list of files added to be Backed-up
				Args :
					full_data_path		(str)			--  Folder path to create the files

				Return:
					list of files to be Backed-up

        """
        machine = self.client_machine
        slash_format = self.slash_format
        list_of_files = []
        machine.create_directory(full_data_path)
        for i in range (1,5):
            file_name = "{0}{1}{2}.txt".format(full_data_path, slash_format, str(i))
            list_of_files.append(file_name)
            machine.create_file(file_name, '')
        for i in range (1,5):
            file_name = "{0}{1}{2}.log".format(full_data_path, slash_format, str(i))
            list_of_files.append(file_name)
            machine.create_file(file_name, '')
        for i in range (1,5):
            file_name = "{0}{1}file{2}.doc".format(full_data_path, slash_format, str(i))
            list_of_files.append(file_name)
            machine.create_file(file_name, '')
        for i in range (1,5):
            file_name = "{0}{1}{2}.pdf".format(full_data_path, slash_format, str(i))
            machine.create_file(file_name, '')

        return list_of_files

    def verify_whether_all_phases_ran(self,  job_id):
        """"Verifies whether the job ran all three phases i.e., Scan Backup ArchiveIndex
        Args :
            job_id 	(int)	 		-- to verify the given job ran all phases

        Return:
            True        -- if ran all phases
                       
            False       -- if didnt ran all phases

        """
        # query to get the numbre of phases ran
        str_query = (" select count(distinct(phase)) from JMBkpAtmptStats with"
                     " (NOLOCK) where status=1 and jobID={0}".format(job_id) )
        self.csdb.execute(str_query)
        cur = self.csdb.fetch_one_row()
        # if count is one it means only one phase was ran else multiple phases were ran
        if cur[0] == '3':
            # query to get which phase was ran
            str_query = ("select distinct(phase) as phases from JMBkpAtmptStats with (NOLOCK)"
                         " where status=1 and jobID={0} order by phases ASC".format(job_id))
            self.csdb.execute(str_query)
            cur = self.csdb.fetch_all_rows()
            if cur[0][0] == '4' and cur[1][0] == '7' and cur[2][0] =='11' :
                return True

        return False

