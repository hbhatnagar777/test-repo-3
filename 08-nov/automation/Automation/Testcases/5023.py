# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    run_backup()                --  method to run backup of the subclient

    run_restore()               --  method to run restore

    tear_down()                 --  tear down method for testcase

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "5023":
                        {
                          "ClientName":"client",
                          "AgentName":"oracle",
                          "InstanceName":"instance"
                        }
            }

"""

import re
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """ Test case class used to run a given test """

    def __init__(self):
        """ Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "Backup - With Skip Offline option"
        self.tablespace_name = 'CV_5023'
        self.tcinputs = {
            'ClientName': None,
            'AgentName': None,
            'InstanceName': None
        }
        self.subclient = None
        self.oracle_helper_object = None
        self.jobid = None

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.oracle_helper_object = OracleHelper(self.commcell, self.client, self.instance)
        self.oracle_helper_object.db_connect(OracleHelper.CONN_SYSDBA)
        self.oracle_helper_object.check_instance_status()

    def run_backup(self):
        """ Runs a backup job on the subclient created """
        job = self.subclient.backup()
        self.jobid = re.findall(r'\d+', str(job))[0]
        self.log.info(f"Backup Job {self.jobid} has started")
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup job with error: {0}".format(
                    job.delay_reason))
        self.log.info("Backup completed successfully")

    def run_restore(self):
        """ Method to run restore """
        recover_scn = self.oracle_helper_object.get_current_scn()
        options = {
            "resetLogs": 1,
            "switchDatabaseMode": True,
            "noCatalog": True,
            "recover": True,
            "recoverFrom": 2,
            "restoreData": True,
            "restoreFrom": 1,
            "restoreControlFile": True,
            "restoreSPFile": False,
            "restoreStream": 2,
            "recoverSCN": f"{recover_scn}"
        }
        job = self.subclient.restore(destination_client=self.client.client_name,
                                     oracle_options=options)
        self.jobid = re.findall(r'\d+', str(job))[0]
        self.log.info(f"Restore Job {self.jobid} has started")
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(
                    job.delay_reason))
        self.log.info("Restore completed successfully")

    def tear_down(self):
        """ Tear down method for testcase """
        self.log.info("Deleting Automation Created tablespaces and tables")
        if self.oracle_helper_object:
            self.oracle_helper_object.oracle_data_cleanup(tables=["CV_TABLE_01"], tablespace=self.tablespace_name,
                                                          user=f"{self.tablespace_name}_user")
        self.log.info("Deleting Automation Created subclient")
        if self.instance.subclients.has_subclient(self.tablespace_name):
            self.instance.subclients.delete(self.tablespace_name)

    def run(self):
        """ Main function for test case execution """
        try:
            self.log.info("Creating new subclient")
            storage_policy = self.instance.subclients.get('default').storage_policy
            self.subclient = self.oracle_helper_object.create_subclient(subclient_name=self.tablespace_name,
                                                                        storage_policy=storage_policy, data_stream=2,
                                                                        data=True, log=True)

            self.log.info("Generating Sample Data for test")
            self.oracle_helper_object.create_sample_data(
                self.tablespace_name, 1, 1)
            self.oracle_helper_object.db_execute('alter system switch logfile')
            self.log.info("Test Data Generated successfully")

            self.run_backup()

            self.log.info("Setting the datafile to offline")
            datafile = '{0}{1}{2}.dbf'.format(self.oracle_helper_object.db_fetch_dbf_location(),
                                              self.tablespace_name, 1)
            self.oracle_helper_object.db_execute(f"alter database datafile '{datafile}' offline")

            self.subclient.skip_offline = True
            self.log.info("Backup with Skip Offline option")
            self.run_backup()

            self.log.info("Checking if any warning is shown in RMAN log file after "
                          "performing backup with skip offline option")
            rman_log = self.oracle_helper_object.fetch_rman_log(self.jobid, self.client, 'backup').splitlines()
            search_term = (f"RMAN-06060: warning: skipping datafile compromises tablespace "
                           f"{self.tablespace_name} recoverability")
            for log_line in rman_log:
                if search_term in log_line:
                    self.log.info("The offline datafiles are not backed up and "
                                  "the following message is shown in RMAN log file:")
                    self.log.info(f"RMAN-06060: warning: skipping datafile compromises tablespace "
                                  f"{self.tablespace_name} recoverability")
                    break

            self.run_restore()

            self.subclient.skip_offline = False
            self.log.info("Backup without Skip Offline option")
            self.run_backup()

        except Exception as exp:
            self.log.error("Testcase failed with exception : %s", exp)
