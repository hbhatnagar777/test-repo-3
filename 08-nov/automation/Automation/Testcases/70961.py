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
    __init__()                           --  initialize TestCase class

    setup()                               --  setup method for test case

    tear_down()                           --  tear down method for testcase

    get_db_status()                       --  method to get database status

    get_data_file_create_test_data()      --  method to get datafile location and create test data

    run_third_party_brbackup_job()        --  method to run third party cmd backup
                                            and gets the detail file

    run_third_party_brarchive_job()       --  method run third party brarchive jobs

    get_log_number()                      --  method to get log sequence number

    db_shut_down()                        --  method to shutdown database

    run_third_party_brrestore_data()      --  method to run cmd brrestore of data

    run_third_party_brrestore_log()       --  method to run cmd brrestore of logs

    run()                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "70961":
                        {
                          "ClientHostName": "saporatest.commvault.com",
                          "AgentName":"sap for oracle",
                          "ClientName":"saporatest",
                          "InstanceName":"DSP"
                        }
            }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Database.SAPOracleUtils.saporaclehelper import SAPOracleHelper
from Web.Common.page_object import TestStep
import Web.Common.exceptions as cvexceptions


class TestCase(CVTestCase):
    """Class for executing Basic third party commandline jobs
    for SAP Oracle using util_file_online device"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Basic Acceptance Test of SAPOracle Backup and Restore from cmd using util_file_online device"
        self.product = self.products_list.SAPORACLE
        self.feature = self.features_list.DATAPROTECTION
        self.saporacle_helper = None
        self.tcinputs = {
            'ClientHostName': None,
            'AgentName': None,
            'ClientName': None,
            'InstanceName': None}
        self.client = None
        self.saporacle_clientid = None
        self.saporacle_helper = None
        self.saporacle_db_user = None
        self.saporacle_db_connectstring = None
        self.saporacle_db_connectpassword = None
        self.machine = None
        self.saporacle_osapp_user = None
        self.saporacle_sapsecurestore = None
        self.tblspaceg = "TSP70956"
        self.tblnameg = "T70956"

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
        self.log.info("*" * 10 + " Create SDK objects " + "*" * 10)
        self.client = self.commcell.clients.get(str(self.tcinputs['ClientName']))
        self.log.info("Successfully got {0} client object".format(str(self.tcinputs['ClientName'])))
        self.saporacle_clientid = self.client._get_client_id()
        self.saporacle_helper = SAPOracleHelper(self.commcell, self.client, self.instance)
        self.saporacle_db_user = self.instance.saporacle_db_user
        self.saporacle_db_connectstring = self.instance.saporacle_db_connectstring
        self.saporacle_db_connectpassword = self.saporacle_helper. \
            get_saporacle_db_connect_password()
        self.saporacle_helper.db_connect()
        self.machine = Machine(machine_name=self.client.client_name, commcell_object=self.commcell)
        self.saporacle_osapp_user = self.instance.os_user
        self.saporacle_sapsecurestore = self.instance.saporacle_sapsecurestore

    @test_step
    def get_db_status(self):
        """ method to database information

                    Returns:
                       status of database

                    Raises:
                        Exception:
                            if unable to get  database status

        """
        status = self.saporacle_helper.get_database_state()
        if status != "OPEN":
            raise cvexceptions.CVTestStepFailure("database is not in open state")
        else:
            self.log.info("database is in open statue")

    @test_step
    def get_data_file_create_test_data(self):
        """ method to get datafile information and create test data

                    Returns:
                            string  -- gives datafile path and create test data

                    Raises:
                            Exception:
                                if unable to get datafile path and create test data

        """
        self.db_file = self.saporacle_helper.get_datafile(self.tblspaceg)
        self.log.info("Datafile location is: {0} delay_reason db_file ". \
                      format(str(self.db_file)))
        self.log.info("Creating test tables in the database")
        retcode = self.saporacle_helper.create_test_tables(self.db_file,
                                                           self.tblspaceg, self.tblnameg, True)
        if retcode == 0:
            self.log.info("test data creation is sucessful")
        return self.db_file

    @test_step
    def run_third_party_brbackup_job(self):
        """ method to run database brbackup from command line

                Returns:
                            string  returns detailfile name

                Raises:
                            Exception:
                                    if unable to run brbackup job

        """

        self.log.info("##Running Third party commandline brbackup job##")
        if self.machine.os_info == 'UNIX':
            brbackup_cmd = r"su - " + self.saporacle_osapp_user + ' -c "brbackup -d \
                                        util_file_online -t online -m full -c force -u /'
            self.log.info(" Command we are running is " + brbackup_cmd)
            if self.saporacle_sapsecurestore == 1:
                brbackup_cmd = f"{brbackup_cmd}/"
                self.log.info(" Command we are running is " + brbackup_cmd)
        else:
            brbackup_cmd = '"brbackup -d util_file_online -t online -m full -c force -u /'
            self.log.info(" Command we are running is " + brbackup_cmd)
            if self.saporacle_sapsecurestore == 1:
                brbackup_cmd = f"{brbackup_cmd}/"
                self.log.info(" Command we are running is " + brbackup_cmd)

        detail_file = self.saporacle_helper.thirdparty_cmd_backup_job(brbackup_cmd, "initauto.utl",
                                                                " BRRESTORE completed successfully")
        if detail_file == None:
            raise cvexceptions.CVTestStepFailure("Failed to run Thirdparty commandline brbackup backup job ")
        else:
            self.log.info("Successfully ran Thirdparty commandline brbackup backup job")

    @test_step
    def run_third_party_brarchive_job(self):
        """ method to run brarchive from command line

                    Returns:
                            returns return code

                    Raises:
                            Exception:
                                    if unable to get  database status

        """

        self.log.info("##Running Third party commandline brarchive job##")
        if self.machine.os_info == 'UNIX':
            brarchive_cmd = r"su - " + self.saporacle_osapp_user + ' -c "brarchive -d \
                                            util_file_online -sd -c force -u /'
            self.log.info(" Command we are running is " + brarchive_cmd)
            if self.saporacle_sapsecurestore == 1:
                brarchive_cmd = f"{brarchive_cmd}/"
                self.log.info(" Command we are running is " + brarchive_cmd)
        else:
            brarchive_cmd = '"brarchive -d util_file_online -sd -c force -u /'
            self.log.info(" Command we are running is " + brarchive_cmd)
            if self.saporacle_sapsecurestore == 1:
                brarchive_cmd = f"{brarchive_cmd}/"
                self.log.info(" Command we are running is " + brarchive_cmd)

        detail_file = self.saporacle_helper.thirdparty_cmd_backup_job(brarchive_cmd, "initauto.utl",
                                                           " BRARCHIVE completed successfully")
        if detail_file == None:
            raise cvexceptions.CVTestStepFailure("Failed to run Thirdparty commandline brarchive job ")
        else:
            self.log.info("Successfully ran Thirdparty commandline brarchive job")

    @test_step
    def get_log_number(self):
        """ method to get log range information

                    Returns:
                            returns log sequence number

                    Raises:
                            Exception:
                            if unable to get  database status

        """
        self.end_lsn = self.saporacle_helper.get_archive_lsn()
        if self.end_lsn != 0:
            self.log.info("End LSN we got is " + str(self.end_lsn))
            return self.end_lsn
        else:
            self.log.error("Failed to get end Log sequence number")

    @test_step
    def db_shut_down(self):
        """ method to shutdown database

                    Returns:
                        returns return code

                    Raises:
                        Exception:
                                if unable to shutdown database

        """
        self.log.info("##DB shutdown #")
        if self.machine.os_info == 'UNIX':
            self.log.info("Os type we got is " +self.machine.os_info)
            self.db_cmd = r"su - " + self.saporacle_osapp_user + ' -c "sqlplus ' + \
                          self.saporacle_db_user + '/' + self.saporacle_db_connectpassword + \
                          '@' + self.saporacle_db_connectstring + ' as sysdba '
        else:
            self.log.info("Os type we got is " +self.machine.os_info)
            self.db_cmd = '"sqlplus ' + self.saporacle_db_user + \
                          '/' + self.saporacle_db_connectpassword + '@' + \
                          self.saporacle_db_connectstring + ' as sysdba '
        self.saporacle_helper.db_shutdown(self.db_cmd, "dbshutdown.sql")

    @test_step
    def run_third_party_brrestore_data(self):
        """ method to run db restore of data from cmd

                            Returns:
                                 returns return code

                            Raises:
                                Exception:
                                    if unable to get  database status

        """

        self.log.info("##Running Third party commandline brrestore of data job##")
        if self.machine.os_info == 'UNIX':
            brrestore_cmd = r"su - " + self.saporacle_osapp_user + ' -c "brrestore -d \
                              util_file_online -b last -m all -c force -u /'
            self.log.info(" Command we are running is " + brrestore_cmd)
            if self.saporacle_sapsecurestore == 1:
                brrestore_cmd = f"{brrestore_cmd}/"
                self.log.info(" Command we are running is " + brrestore_cmd)
        else:
            brrestore_cmd = '"brrestore -d util_file_online -b last -m all -c force -u /'
            self.log.info(" Command we are running is " + brrestore_cmd)
            if self.saporacle_sapsecurestore == 1:
                brrestore_cmd = f"{brrestore_cmd}/"
                self.log.info(" Command we are running is " + brrestore_cmd)

        detail_file = self.saporacle_helper.thirdparty_cmd_backup_job(brrestore_cmd, "initauto.utl",
                                                           " BRRESTORE completed successfully")
        if detail_file == None:
            raise cvexceptions.CVTestStepFailure("Failed to run Thirdparty commandline brrestore of data job ")
        else:
            self.log.info("Successfully ran Thirdparty commandline brrestore of data job")

    @test_step
    def run_third_party_brrestore_log(self):
        """ method to run db restore of log from cmd

                            Returns:
                                 returns return code

                            Raises:
                                Exception:
                                    if unable to get  database status

        """

        self.log.info("##Running Third party commandline brrestore of logs job##")
        if self.machine.os_info == 'UNIX':
            brrestore_logcmd = r"su - " + self.saporacle_osapp_user + ' -c "brrestore -d \
                              util_file_online -a ' + self.end_lsn + ' -c force -u /'
            self.log.info(" Command we are running is " + brrestore_logcmd)
            if self.saporacle_sapsecurestore == 1:
                brrestore_logcmd = f"{brrestore_logcmd}/"
                self.log.info(" Command we are running is " + brrestore_logcmd)
        else:
            brrestore_logcmd = '"brrestore -d  util_file_online -a ' + self.end_lsn + ' -c force -u /'
            self.log.info(" Command we are running is " + brrestore_logcmd)
            if self.saporacle_sapsecurestore == 1:
                brrestore_logcmd = f"{brrestore_logcmd}/"
                self.log.info(" Command we are running is " + brrestore_logcmd)

        detail_file = self.saporacle_helper.thirdparty_cmd_backup_job(brrestore_logcmd, "initauto.utl",
                                                           " BRRESTORE completed successfully")
        if detail_file == None:
            raise cvexceptions.CVTestStepFailure("Failed to run Thirdparty commandline brrestore of logs ")
        else:
            self.log.info("Successfully ran Thirdparty commandline brrestore of logs")

    def run(self):
        """executes basic Third party commandline backup and inlace restore
         for SAP for Oracle using util_file_online device"""

        try:
            self.get_db_status()
            self.get_data_file_create_test_data()
            self.run_third_party_brbackup_job()
            self.run_third_party_brarchive_job()
            self.get_log_number()
            self.db_shut_down()
            self.saporacle_helper.rename_datafile(self.db_file)
            self.saporacle_helper.db_mount(self.db_cmd, "dbmount.sql")
            self.run_third_party_brrestore_data()
            self.run_third_party_brrestore_log()
            self.saporacle_helper.db_recover_open(self.db_cmd, "recoveropen.sql")
            self.saporacle_helper.test_tables_validation(self.tblspaceg, self.tblnameg)

        except Exception:
            raise cvexceptions.CVWebAutomationException('Test case failed')

    def tear_down(self):
        """Tear Down function of this test case"""
        self.log.info("Deleting Automation Created databases")
        if self.saporacle_helper:
            self.saporacle_helper.drop_tablespace(self.tblspaceg)
