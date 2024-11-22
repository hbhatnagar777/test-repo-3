# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  initialize TestCase class

    run()                   --  run function of this test case

    
"""

import os, time, requests
#from Automation import AutomationUtils

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants, qcconstants, database_helper, cvhelper, commonutils
from AutomationUtils.machine import Machine
from Database.SAPOracleUtils.saporaclehelper import SAPOraclehelper
from AutomationUtils.machine import Machine
#from AutomationUtils.interruption import Interruption
from AutomationUtils import constants
from cvpysdk.job import Job

class TestCase(CVTestCase):
    """Class for executing backup restartability
    Test of SAPOracle backup and Restore test case using rman_util device"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "executes suspend/resume/pending and client process kill cases\
        during backup for SAP for Oracle iDa using rman_util device"
        self.product = self.products_list.SAPORACLE
        self.feature = self.features_list.DATAPROTECTION
        self.saporacle_helper = None
        self.tcinputs = {
                "SCName":52615}

    

    def run(self):
        """executes suspend/resume/pending and client process kill cases\
        during backup for SAP for Oracle iDa using rman_util device"""
        try:
            self.log = logger.get_log()
            self.log.info("Started executing testcase: {0} self.id ".format(self.id))
            inputs = self.tcinputs
            self.log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            self.log.info("*" * 10 + " Create SDK objects " + "*" * 10)
            self.client = self.commcell.clients.get(str(inputs['ClientName']))
            self.log.info("Successfully got {0} client object".format(str(inputs['ClientName'])))
            self._ostype = self.client._properties['client']['osInfo']['Type']
            self.log.info("Successfully got os type "+self._ostype)
            self.saporacle_clientid = self.client._get_client_id()
            self.saporacle_helper = SAPOraclehelper(self.commcell, self.instance)
            self._saporacle_db_connectpassword = self.saporacle_helper.\
            getsaporacle_db_connectpassword()
            self.saporacle_helper.db_connect()
            self.log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            self.log.info("*" * 10 + " Create SDK objects " + "*" * 10)
            self._spname = self.instance.log_sp
            self.log.info("log storage policy name is  "+str(self._spname))
            self._simpanainstance = self.client.instance
            self.log.info("simpana instance we got from client is "+ str(self._simpanainstance))
            self.machine = Machine(machine_name=self.client.client_name, commcell_object=self.commcell)
            self.log.info(self.machine)
            self.create_tmpdir = self.machine.tmp_dir
            self.log.info("temp dir path is: {0} ".format(self.create_tmpdir))
            self.pathname = self.machine.join_path(
                    self.create_tmpdir, "failSAPDataBackupB4Intimate")
            self.log.info(self.pathname)
            self.pathname1 = self.machine.join_path(
                    self.create_tmpdir, "failSAPDataConfigBackupB4Intimate")
            self.log.info(self.pathname1)
            self.pathname2 = self.machine.join_path(
                    self.create_tmpdir, "failSAPLogBackupB4Intimate")
            self.log.info(self.pathname2)
            self.pathname3 = self.machine.join_path(
                    self.create_tmpdir, "failSAPLogConfigBackupB4Intimate")
            self.log.info(self.pathname3)
            tblspaceg = "TSP52615"
            tblnameg = "T52615"


            self.log.info("Will run below test case on: {0} subclient"\
                     .format(str(inputs['SCName'])))
            self.log.info("Checking database state")
            status = self.saporacle_helper.getdatabasestate()
            if status != "OPEN":
                self.log.error("database is not in open state")
            else:
                self.log.info("database is in open statue")
            self.log.info("getting datafilepath")
            self.dbfile = self.saporacle_helper.getdatafile(tblspaceg)
            self.log.info("Datafile location is: {0}  dbfile ".\
                          format(str(self.dbfile)))


            self.log.info("Creating test tables in the database")
            retcode = self.saporacle_helper.create_test_tables(self.dbfile,\
                                                               tblspaceg, tblnameg, True)
            if retcode == 0:
                self.log.info("test data creation is sucessful")
            self.log.info("##check  subclient specified exists in GUI##")
            subclient = self.instance.subclients.has_subclient(format(str(inputs['SCName'])))
            self.log.info(subclient)
            if subclient == True:
                self.log.info("Successfully got {0} subclient object ")
                subclient = self.instance.subclients.get(str(inputs['SCName']))
            else:
                self.log.info("Subclient doesn't exist..so creating new \
                subclient named: {0} SCName ".format(str(inputs['SCName'])))
                subclient = self.instance.subclients.add(format(str(inputs['SCName'])),\
                                                    str(self._spname))
                self.log.info("Successfully created  subclient with rman_util device")
                self.log.info(subclient)
            
            self.log.info("Running 1st full job with out anyrestart")
            job = self.saporacle_helper.run_backup(subclient, "FULL")
            self.log.info(job)
            jobid = job.job_id
            self.log.info(str(jobid))
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: "\
                                + str(job.delay_reason))
            self.log.info("Successfully ran full backup")
            
           
            self.log.info("##getting dabasebackup size from CS db##")
            appsize = self.saporacle_helper.getjobbackupsize(jobid)
            if appsize != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize ".\
                              format(str(appsize)))
            self.log.info("##getting application size from CS db##")
            self.jobobject = Job(self.commcell, jobid)
            sizeofapp = self.jobobject.size_of_application
            self.log.info(sizeofapp)
            self._sizeofapp = float(sizeofapp/1024/1024)
            self.log.info(self._sizeofapp)
            if self._sizeofapp != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize ".\
                              format(str(self._sizeofapp)))
            self.log.info("running second full backup by suspend and resume job")
            
            job = self.saporacle_helper.run_restart_backup(subclient, "FULL")
            self.log.info(job)
            jobid1 = job.job_id
            self.log.info(jobid1)
            self.log.info("checking cs db for data archivefiles validation")
            recode = self.saporacle_helper.getarchfileisvalid(str(jobid1), '1')
            if recode == '0':
                self.log.info("archivefiles are invalidated sucessfully in Cs db for restarted job")
            else:
                self.log.error("There is some issue with data archive files invalidation")
            recode = self.saporacle_helper.getarchfileisvalid(str(jobid1), '4')
            if recode != '0':
                self.log.info("archivefiles are not validated for log backup phase\
                in Cs db for restarted job")
            else:
                self.log.error("There is some issue with log archive files invalidation")
            self.log.info("##getting application size from CS db for the restarted backup job##")
            appsize1 = self.saporacle_helper.getjobdatabasephasebackupsize(jobid1)
            if appsize1 != 0:
                self.log.info("Appsize we got from cs db is "+str(appsize1))
            self.log.info("comapre the application size backup b/w \
            single attempt and restarted job")
            if str(appsize) != str(appsize1):
                self.log.error("There is some issue with application\
                size for restarted backup jobs")
            self.log.info("##getting application size from CS db##")
            self.jobobject = Job(self.commcell, jobid)
            sizeofapp1 = self.jobobject.size_of_application
            self.log.info(sizeofapp1)
            self._sizeofapp1 = float(sizeofapp1/1024/1024)
            self.log.info(self._sizeofapp1)
            if self._sizeofapp1 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize ".\
                              format(str(self._sizeofapp1)))
            self.log.info("comapre the total application size backup b/w \
            single attempt and restarted job")
            if str(self._sizeofapp1) > str(self._sizeofapp):
                self.log.error("There is some issue with total application\
                size for restarted backup jobs")
            self.log.info("cleaning up test data before restore ")
            
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")

            self.log.info("##running 1st inplace restore job###")
            job = self.instance.restore_in_place()
            self.log.info("Started Current time restore to same client job with Job ID: "\
                     + str(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run current time restore job with \
                error: {0} delay_reason".format(str(job.delay_reason)))

            self.log.info("Successfully finished Current time restore to same client")
            self.log.info("restore tablespace and table validation starts here")
            status = self.saporacle_helper.test_tables_validation(tblspaceg, tblnameg)
            if status == 0:
                self.log.info("tablespace/tables are restored sucessgully")
            
            self.log.info("###Case#2 Make SAp Oracle backup job goes to pending\
            at different phases")
            retCode = self.machine.create_file(self.pathname, '')
            if retCode == True:
                self.log.info("hook File failSAPDataBackupB4Intimate is \
                creatinged sucessfully on client")
            retCode = self.machine.create_file(self.pathname1, '')
            if retCode == True:
                self.log.info("hook File failSAPDataConfigBackupB4Intimate is\
                creatinged sucessfully on client")
            retCode = self.machine.create_file(self.pathname2, '')
            if retCode == True:
                self.log.info("hook File failSAPLogBackupB4Intimate is \
                creatinged sucessfully on client")
            retCode = self.machine.create_file(self.pathname3, '')
            if retCode == True:
                self.log.info("hook File failSAPLogConfigBackupB4Intimate is \
                creatinged sucessfully on client")

            self.log.info("Creates archive logs after restlogs")
            status = self.saporacle_helper.switchlogfile('10')
            if status == 0:
                self.log.info("logs are created sucessgully")
            
            self.log.info("running third full backup by kepping sap oracle hooks\
            which will hlp make job go to pending state")
            job = self.saporacle_helper.run_pending_backup(subclient, "FULL", self.machine,\
                                                           self.pathname, self.pathname1,\
                                                           self.pathname2, self.pathname3)
            self.log.info(job)

            jobid2 = job.job_id
            self.log.info(jobid2)

            self.log.info("##getting application size from CS db for the restarted backup job##")
            appsize2 = self.saporacle_helper.getjobdatabasephasebackupsize(jobid2)
            if appsize2 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize2 ".\
                              format(str(appsize2)))
            self.log.info("comapre the application size backup\
            b/w single attempt and restarted job")
            if str(appsize) != str(appsize2):
                self.log.error("There is some issue with application\
                size for restarted backup jobs")
            self.log.info("##getting total application size from CS db##")
            self.jobobject = Job(self.commcell, jobid)
            sizeofapp2 = self.jobobject.size_of_application
            self.log.info(sizeofapp2)
            self._sizeofapp2 = float(sizeofapp2/1024/1024)
            self.log.info(self._sizeofapp2)
            if self._sizeofapp2 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize ".\
                              format(str(self._sizeofapp2)))
            self.log.info("comapre the total application size backup b/w \
            single attempt and restarted job")
            if str(self._sizeofapp2) > str(self._sizeofapp):
                self.log.error("There is some issue with total application\
                size for restarted backup jobs")
            
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup\
                 created by automation.please cleanup manually")
            self.log.info("running 2nd inplace restore job")
            job = self.instance.restore_in_place()
            self.log.info("Started Current time restore to same client job with \
            Job ID: {0} job_id ".format(str(job.job_id)))

            if not job.wait_for_completion():
                raise Exception("Failed to run current time restore job with \
                error: {0} delay_reason ".format(str(job.delay_reason)))

            self.log.info("Successfully finished Current time restore to same client")
            self.log.info("restore tablespace and table validation starts here")
            status = self.saporacle_helper.test_tables_validation(tblspaceg, tblnameg)
            if status == 0:
                self.log.info("tablespace/tables are restored sucessgully")
            self.log.info("Creates archive logs after restlogs")
            status = self.saporacle_helper.switchlogfile('10')
            if status == 0:
                self.log.info("logs are created sucessgully")
            
            self.log.info("running 4th full backup by stopping client services\
            after backup job is submitted")
            job = self.saporacle_helper.run_client_service_restart_backup(subclient, "FULL")
            self.log.info(job)

            jobid3 = job.job_id
            self.log.info(jobid3)
            
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup\
                 created by automation.please cleanup manually")
            self.log.info("running 3rd inplace restore job")
            job = self.instance.restore_in_place()
            self.log.info("Started Current time restore to same client job with Job ID: "\
                     + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception("Failed to run current time restore job with error: "\
                        + str(job.delay_reason))

            self.log.info("Successfully finished Current time restore to same client")
            self.log.info("restore tablespace and table validation starts here")
            status = self.saporacle_helper.test_tables_validation(tblspaceg, tblnameg)
            if status == 0:
                self.log.info("tablespace/tables are restored sucessgully")
            
            appsize3 = self.saporacle_helper.getjobdatabasephasebackupsize(jobid3)
            if appsize3 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize3 ".format(str(appsize3)))
            self.log.info("comapre the application size backup \
            b/w single attempt and restarted job")
            if str(appsize) != str(appsize3):
                self.log.error("There is some issue with application\
                size for restarted backup jobs")
            self.log.info("##getting total application size from CS db##")
            self.jobobject = Job(self.commcell, jobid)
            sizeofapp3 = self.jobobject.size_of_application
            self.log.info(sizeofapp3)
            self._sizeofapp3 = float(sizeofapp3/1024/1024)
            self.log.info(self._sizeofapp3)
            if self._sizeofapp3 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize ".\
                              format(str(self._sizeofapp3)))
            self.log.info("comapre the total application size backup b/w \
            single attempt and restarted job")
            if str(self._sizeofapp3) > str(self._sizeofapp):
                self.log.error("There is some issue with total application\
                size for restarted backup jobs")
            self.log.info("Running 5th step..killing ClSapAgent process while backup job is running")

            self.log.info("Creates archive logs after restlogs")
            status = self.saporacle_helper.switchlogfile('12')
            if status == 0:
                self.log.info("logs are created sucessgully")
            job = self.saporacle_helper.run_kill_process_backup(subclient, "FULL", self.machine)
            self.log.info(job)

            jobid4 = job.job_id
            self.log.info(jobid4)
            
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup\
                 created by automation.please cleanup manually")
            self.log.info("running 4th inplace restore job")
            job = self.instance.restore_in_place()
            self.log.info("Started Current time restore to same client job with Job ID: "\
                     + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception("Failed to run current time restore job with error: "\
                        + str(job.delay_reason))

            self.log.info("Successfully finished Current time restore to same client")
            self.log.info("restore tablespace and table validation starts here")
            status = self.saporacle_helper.test_tables_validation(tblspaceg, tblnameg)
            if status == 0:
                self.log.info("tablespace/tables are restored sucessgully")
            
            appsize4 = self.saporacle_helper.getjobdatabasephasebackupsize(jobid4)
            if appsize4 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize3 ".format(str(appsize4)))
            self.log.info("comapre the application size backup \
            b/w single attempt and restarted job")
            if str(appsize) != str(appsize4):
                self.log.error("There is some issue with application\
                size for restarted backup jobs")
            self.log.info("##getting total application size from CS db##")
            self.jobobject = Job(self.commcell, jobid)
            sizeofapp4 = self.jobobject.size_of_application
            self.log.info(sizeofapp4)
            self._sizeofapp4 = float(sizeofapp4/1024/1024)
            self.log.info(self._sizeofapp4)
            if self._sizeofapp4 != 0:
                self.log.info("Appsize we got from cs db is: {0} appsize ".\
                              format(str(self._sizeofapp4)))
            self.log.info("comapre the total application size backup b/w \
            single attempt and restarted job")
            if str(self._sizeofapp4) > str(self._sizeofapp):
                self.log.error("There is some issue with total application\
                size for restarted backup jobs")
            
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup\
                 created by automation.please cleanup manually")

        except Exception as exp:
            self.log.error('Failed with error: {0} exp '.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED
