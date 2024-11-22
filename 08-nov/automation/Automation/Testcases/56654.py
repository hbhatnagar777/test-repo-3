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
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case calls SnapHelper Class to execute 
                            and Validate Below Operations.
                            Snap Backup, backup Copy, Restores, 
                            with RFC metadata validation.
"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snaptemplates import SNAPTemplate
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.SNAPUtils.snaphelper import SNAPHelper


class TestCase(CVTestCase):
    """ Class for executing FS Snap RFC validation, It performs the below operations
        1.Run full snap job.
            Delete RFC metadata files from indexserver.
            Try to restore from Snap backup, and perform data validation from source and target.
            Run Backup copy and Validate RFC files restored from media for full snap job
            Performed Restore operations Priamry snap and Backup copy
        2. Repeat above with couple of more Incremental jobs.
        3. Delete RFC files for whole cycle and run Backup copy.
        4. Validate metadata files updloaded for all snap jobs at RFC locaiton.
        4. Delete RFC files for all jobs again and Run synthetic Full.
        5. Run restore from synthetic full and validate data.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None,
            "IndexMediaAgent": None,
           }
        self.name = "Automation - RFC validation for Snap -WinFS"

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        
        try:
            log.info("Started executing {0} testcase".format(self.id))
            fshelper = FSHelper(self)
            fshelper.populate_tc_inputs(self, False)
            self.tcinputs['fshelper'] = fshelper
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(self.commcell, 
                            self.client, self.agent, self.tcinputs, self.snapconstants)
            
            """ Pre-clenup and initial test setup """         
            self.snaphelper.add_array()
            self.snaphelper.pre_cleanup()
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
    
            """ Step 1: Run full snap Job, delete metadata files from RFC.
                        Perfrom Restore operation. Run backup copy and check 
                        metadata files are restored at RFC """
            
            self.log.info("*" * 20 + "Running First FULL Snap Backup job" + "*" * 20)
            self.snapconstants.skip_catalog = True
            self.snaphelper.update_test_data(mode='add')
            full1_job = self.snaphelper.snap_backup()
            full1_jobid = full1_job.job_id
            
            full_srclist = ['cjinfotot.cvf', 'filtertot.cvf', str(full1_jobid)+'_']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
                                     "path post validation")
            
            fshelper.testcase.subclient = self.snaphelper.snapconstants.subclient
            self.helper.validate_rfc_files(full1_jobid, full_srclist, delete_rfc=True)
       
            """ Compare Source and Destination and check files restored."""
        
            self.log.info("*" * 20 + "Running OutPlace Restore from Snap Backup job" + "*" * 20)
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            self.snaphelper.snap_outplace(1)
            self.snaphelper.outplace_validation(self.snapconstants.snap_outplace_restore_location,
                                                self.snaphelper.client_machine)
            
            """ Run backup copy and validate metadata files for full job restore correctly at RFC """
            
            self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            self.snaphelper.backup_copy()
            self.log.info("Verify RFC metadata files are restored for previous snap jobs")
            self.helper.validate_rfc_files(full1_jobid, full_srclist)
            
            """Perform restore and validate Source and destination data """
            
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(full1_job.job_id, 2, full1_job.start_time, full1_job.end_time)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            
            """Step 2: Delete RFC files, run Incremental Snap backup and backup copy.
                Verify RFC metadata restore for previous snap job after backup copy""" 
            
            self.log.info("*" * 20 + "Validate and Delete RFC metadata files for Full job" + "*" * 20)
            self.helper.validate_rfc_files(full1_jobid, full_srclist, delete_rfc=True)
            
            self.log.info("*" * 20 + "Change/add the date before Incremental Job" + "*" * 20)
            self.snapconstants.source_path = [self.snapconstants.test_data_path[0]]
            self.snaphelper.update_test_data(mode='edit')
            
            self.log.info("*" * 20 + "Running FIRST INCREMENTAL Snap Backup job and Restore from snap copy" + "*" * 20)
            self.snapconstants.backup_level = 'INCREMENTAL'
            inc1_job = self.snaphelper.snap_backup()
            
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.update_test_data(mode='copy')
            self.snaphelper.snap_inplace(1)
            self.snaphelper.inplace_validation(inc1_job.job_id,
                                               self.snapconstants.snap_copy_name,
                                               self.snapconstants.test_data_path)
            
            self.log.info("*" * 20 + "Validate and Delete RFC metadata files for INCR job" + "*" * 20)
            incr1_jobid = inc1_job.job_id
            
            incr1_srclist = ['cjInfoInc.cvf', 'FilterInc.cvf', str(incr1_jobid)+'_']
            self.helper.validate_rfc_files(incr1_jobid, incr1_srclist, delete_rfc=True)
            
            self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            self.snaphelper.backup_copy()
            
            self.log.info("*" * 10 + "Verify RFC metadata files are restored for full1 and inc1 snap jobs" + "*" *10)
            self.helper.validate_rfc_files(full1_jobid, full_srclist)
            self.helper.validate_rfc_files(incr1_jobid, incr1_srclist)
            
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy of INCR job" + "*" * 20)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(inc1_job.job_id, 2, inc1_job.start_time, inc1_job.end_time)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            
            """Step 3: Run 2nd Incremental Snap backup and backup copy.
                Validate RFC metadata uploaded""" 
            
            self.snapconstants.backup_level = 'INCREMENTAL'
            inc2_job = self.snaphelper.snap_backup()
            
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.update_test_data(mode='copy')
            self.snaphelper.snap_inplace(1)
            self.snaphelper.inplace_validation(inc2_job.job_id,
                                               self.snapconstants.snap_copy_name,
                                               self.snapconstants.test_data_path)
            
            self.log.info("*" * 10 + "Validate RFC metadata files for INCR job" + "*" * 10)
            incr2_jobid = inc2_job.job_id
            incr2_srclist = ['cjInfoInc.cvf', 'FilterInc.cvf', str(incr2_jobid)+'_']
            self.helper.validate_rfc_files(incr2_jobid, incr2_srclist)
            self.snaphelper.backup_copy()
            
            """ Run out of place restore from Backup copy """
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(inc2_job.job_id, 2, inc2_job.start_time, inc2_job.end_time)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            
            """Step 4: Delete RFC metadata for full cycle and Run Synthetic full
                    Perform restore operation and validate Data"""
            
            self.log.info("*" * 20 + "Delete RFC files and run synthtic full" + "*" * 20)
            self.helper.validate_rfc_files(full1_jobid, full_srclist, delete_rfc=True)
            self.helper.validate_rfc_files(incr1_jobid, incr1_srclist,delete_rfc=True)
            self.helper.validate_rfc_files(incr2_jobid, incr2_srclist, delete_rfc=True)
            
            self.snapconstants.backup_level = 'Synthetic_full'
            synth_job = self.snaphelper.snap_backup()
            
            self.log.info("*" * 20 + "Perform out of place restore from synth full" + "*" * 20)       
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(synth_job.job_id, 2, synth_job.start_time, synth_job.end_time)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            
            """Step 5 : Run Incremental, check RFC uploaded for previous cycle and new 
                        INC job. browse and restore and validate incremetnal data.
            """
            
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snaphelper.update_test_data(mode='add')
            inc3_job = self.snaphelper.snap_backup()
            
            self.log.info("*" * 10 + "Validate RFC metadata files for INCR job" + "*" * 10)
            incr3_jobid = inc3_job.job_id
            incr3_srclist = ['cjInfoInc.cvf', 'FilterInc.cvf', str(incr3_jobid)+'_']
            self.helper.validate_rfc_files(incr3_jobid, incr3_srclist)
            
            """ Run backup copy and validate RFC uploaded for previous inc data"""
            self.snaphelper.backup_copy()
            self.helper.validate_rfc_files(incr2_jobid, incr2_srclist)
            
            """ out of place restore from backup copy """
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(inc3_job.job_id, 2, inc3_job.start_time, inc3_job.end_time)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            
            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED
            
            
            
        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
