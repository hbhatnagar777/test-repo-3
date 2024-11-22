# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
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

import os
#from Automation import AutomationUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants, qcconstants, database_helper, cvhelper
from AutomationUtils.machine import Machine
from SAPOracleUtils.saporaclehelper import SAPOraclehelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of SAPOracle
    backup and Restore test case using util_file device"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of SAPOracle Backup and Restore using util_file device"
        self.product = self.products_list.SAPORACLE
        self.feature = self.features_list.DATAPROTECTION

    def _run_backup(self, subclient, backup_type):
        """Starts backup job"""
        log = logger.get_log()
        log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = subclient.backup(backup_type)
        log.info("Started {0} backup with Job ID: {1}".format(backup_type, str(job.job_id)))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )
        log.info("Successfully finished {0} backup job".format(backup_type))

        return job

    def run(self):
        """executes basic acceptance test case for SAP for Oracle"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))
            commcell = self.commcell
            inputs = self.tcinputs
            log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            log.info("*" * 10 + " Create SDK objects " + "*" * 10)
            client = commcell.clients.get(str(inputs['ClientName']))
            log.info("Successfully got {0} client object".format(str(inputs['ClientName'])))
            saporacle_clientid = client._get_client_id()
            agent = client.agents.get('sap for oracle')
            log.info("Successfully got SAP Oracle agent object")
            instance = agent.instances.get(str(inputs['InstanceName']))
            log.info("Successfully got {0} instance object".format(str(inputs['InstanceName'])))
            subclient = instance.subclients.get(str(inputs['SubclientName']))
            log.info("Successfully got {0} subclient object".format(str(inputs['SubclientName'])))
            log.info("initializing SAPOraclehelper")
            self._saporacle_db_user = instance.saporacle_db_user
            log.info("sap oracle db user name is "+self._saporacle_db_user)
            self._saporacle_db_connectstring = instance.saporacle_db_connectstring
            log.info("sap oracle db connect string  is "+self._saporacle_db_connectstring)
            self._saporacle_instanceid = instance.saporacle_instanceid
            log.info("sap oracle instance id is  "+str(self._saporacle_instanceid))
            self._saporacle_instancename = instance.instance_name
            log.info("sap oracle instance name is  "+str(self._saporacle_instancename))
            self._saporacle_db_connectpassword = SAPOraclehelper.get_saporacle_db_connectpassword\
            (self, str(self._saporacle_instanceid))
            #log.info("sap oracle db connect password  is "+self._saporacle_db_connectpassword)
            log.info("Create Machine class object")
            client_machine = Machine(client.client_name, commcell)
            log.info("Create Machine class object"+str(client_machine))
            tblSpaceG = "TSP51418"
            tblNameG = "T51418"

            log.info("Will run below test case on: {0} subclient".\
                     format(str(inputs['SubclientName'])))
            log.info("Checking database state")
            status = SAPOraclehelper.GetDatabaseState(self, self._saporacle_db_user, \
                                                      self._saporacle_db_connectpassword, \
                                                      self._saporacle_db_connectstring)
            if status != "OPEN":
                log.error("database is not in open state")
            else:
                log.info("database is in open statue")

            log.info("getting datafilepath")
            self.DBFile = SAPOraclehelper.getdatafile(self, self._saporacle_db_user, \
                                                      self._saporacle_db_connectpassword, \
                                                      self._saporacle_db_connectstring, tblSpaceG)
            log.info("Datafile location is "+str(self.DBFile))
            log.info("Creating test tables in the database")
            retcode = SAPOraclehelper.create_test_tables(self, self._saporacle_db_user, \
                                                         self._saporacle_db_connectpassword, \
                                                         self._saporacle_db_connectstring, \
                                                         self.DBFile, tblSpaceG, tblNameG, True)
            if retcode == 0:
                log.info("test data creation is sucessful")

            job = self._run_backup(subclient, "FULL")
            log.info(job)
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: "\
                                + str(job.delay_reason))
            log.info("Successfully ran full backup")
            log.info("cleaning up test data before restore ")
            status = SAPOraclehelper.cleanup_test_data(self, self._saporacle_db_user, \
                                                       self._saporacle_db_connectpassword, \
                                                       self._saporacle_db_connectstring, tblSpaceG)
            if status == 0:
                log.info("tablespace spaces are cleaned up sucessgully")
            log.info("###Submitting Restore job starts here###")
            job = instance.restore_in_place()
            log.info("Started Current time restore to same client job with Job ID: "\
                     + str(job.job_id))
            if not job.wait_for_completion():
                raise Exception("Failed to run current time restore job with error: "\
                                + str(job.delay_reason))
            log.info("Successfully finished Current time restore to same client")
            log.info("restore tablespace and table validation starts here")
            status = SAPOraclehelper.test_tables_validation(self, self._saporacle_db_user,\
                                                            self._saporacle_db_connectpassword, \
                                                            self._saporacle_db_connectstring,\
                                                            tblSpaceG, tblNameG)
            if status == 0:
                log.info("tablespace/tables are restored sucessgully")
            log.info("validating the tablespace restore or not")
            status = SAPOraclehelper.cleanup_test_data(self, self._saporacle_db_user, \
                                                       self._saporacle_db_connectpassword,\
                                                       self._saporacle_db_connectstring,\
                                                       tblSpaceG)
            if status == 0:
                log.info("tablespace spaces are cleaned up sucessgully")
            else:
                log.info("there is some issue with tablespace cleanup created by \
                automation.please cleanup manually")

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
