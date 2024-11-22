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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants
from AutomationUtils.machine import Machine
from Database.SAPOracleUtils.saporaclehelper import SAPOraclehelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance
    Test of SAPOracle backup and Restore test case using rman_util device"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of SAPOracle Backup and\
        Restore using rman_util device"
        self.product = self.products_list.SAPORACLE
        self.feature = self.features_list.DATAPROTECTION
        self.saporacle_helper = None
        self.tcinputs = {
                "SCName":51463}

    def _run_backup(self, subclient, backup_type):
        """Starts backup job
        Args:

             subclient(str)     -- Specify the subclient object name where backups
                                             needs to be run
            backup_type(str)    --  specify the backup type needs to be run
                                   ex:FULL or INCREMENTAL
        Raises:
                Exception:

                    if failed to run backup
        """
        self.log.info("*" * 10 + " Starting Subclient {0} Backup "\
                 .format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        self.log.info("Started {0} backup_type backup with Job ID: {1} job_id ".\
                 format(backup_type, str(job.job_id)))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}"\
                               .format(backup_type, job.delay_reason))
        self.log.info("Successfully finished {0} backup_type backup job ".format(backup_type))
        return job

    def run(self):
        """executes basic acceptance test case for SAP for Oracle"""

        try:
            self.log = logger.get_log()
            self.log.info("Started executing testcase: {0} id ".format(self.id))
            inputs = self.tcinputs
            self.log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            self.log.info("*" * 10 + " Create SDK objects " + "*" * 10)
            client = self.commcell.clients.get(str(inputs['ClientName']))
            self.log.info("Successfully got {0} client object".format(str(inputs['ClientName'])))
            self.saporacle_clientid = client._get_client_id()
            self.saporacle_helper = SAPOraclehelper(self.commcell, self.instance)
            self._saporacle_db_connectpassword = self.saporacle_helper.\
            getsaporacle_db_connectpassword()
            self.saporacle_helper.db_connect()
            self.log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            self.log.info("*" * 10 + " Create SDK objects " + "*" * 10)
            self._spname = self.instance.log_sp
            self.log.info("log storage policy name is: {0} _spname ".format(str(self._spname)))
            tblspaceg = "TSP51463"
            tblnameg = "T51463"
            tblnameg1 = "T514631"
            tblspaceg1 = "TSP514631"


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
            self.log.info("Datafile location is: {0} dbfile ".format(str(self.dbfile)))


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
                subclient named: {0}  SCName ".\
                                 format(str(inputs['SCName'])))
                subclient = self.instance.subclients.add(format(str(inputs['SCName'])),\
                                                    str(self._spname))
                self.log.info("Successfully created  subclient with rman_util device")
                self.log.info(subclient)
            job = self._run_backup(subclient, "FULL")
            self.log.info(job)
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: {0} delay_reason ".\
                                format(str(job.delay_reason)))
            self.log.info("Successfully ran full backup")

            self.dbfile = self.saporacle_helper.getdatafile(tblspaceg1)
            self.log.info("Datafile location is: {0} dbfile ".format(str(self.dbfile)))
            self.log.info("adding one tablespace and table before incremental backup")
            retcode = retcode = self.saporacle_helper.create_test_tables(self.dbfile,\
                                                         tblspaceg1, tblnameg1, True)
            if retcode == 0:
                self.log.info("test data creation is sucessful")
            job = self._run_backup(subclient, "INCREMENTAL")
            self.log.info(job)
            if not job.wait_for_completion():
                raise Exception("Failed to run INCREMENTAL backup job with error: "\
                                + str(job.delay_reason))
            self.log.info("Successfully ran INCREMENTAL backup")
            self.log.info("cleaning up test data before restore ")
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            status = self.saporacle_helper.droptablespace(tblspaceg1)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
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
            status = self.saporacle_helper.test_tables_validation(tblspaceg1, tblnameg1)
            if status == 0:
                self.log.info("tablespace/tables are restored sucessgully")
            self.log.info("validating the tablespace restore or not")
            status = self.saporacle_helper.droptablespace(tblspaceg)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup\
                 created by automation.please cleanup manually")
            status = self.saporacle_helper.droptablespace(tblspaceg1)
            if status == 0:
                self.log.info("tablespace spaces are cleaned up sucessgully")
            else:
                self.log.info("there is some issue with tablespace cleanup\
                created by automation.please cleanup manually")

        except Exception as exp:
            self.log.error('Failed with error: {0} exp ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
