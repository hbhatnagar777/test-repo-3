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
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case

    tear_down()                 --  Tear down function for this testcase

    run()                       --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """Class for executing MySQL Enterprise Backup and Out of Place Restores Commcell Console"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "MySQL Enterprise Backup and Out of Place Restores Commcell Console"
        self.mysql_helper = None
        self.dbhelper_object = None
        self.tcinputs = {
            "meb_binary_path": None,
            "DestinationClientName": None,
            "DestinationInstanceName": None
        }
        self.meb_existing_flag = None
        self.destination_mysql_helper = None
        self.no_locking_flag = None
        self.destination_mysql_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.mysql_helper = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username)
        self.dbhelper_object = DbHelper(self.commcell)

    def tear_down(self):
        """Tear down function for this testcase"""
        # Disabling No Locking and MySQL Enterprise Backup functionality on MySQL Instance
        # Property if it was disabled before start of automation
        if not self.no_locking_flag:
            self.log.info("Disabled no lock checkbox on %s as it was disabled before the "
                          "start of the test case execution", self.instance.name)
            self.instance.no_lock_status = False

        if not self.meb_existing_flag:
            self.log.info("Disabled MySQL Enterprise Backup option on MySQL Instance %s since it "
                          "was disabled before start of test case execution",
                          self.instance.name)
            self.instance.mysql_enterprise_backup_binary_path = ''

        if self.mysql_helper:
            self.log.info("Deleting Automation Created Tables in Source MySQL Server")
            self.mysql_helper.cleanup_test_data(database_prefix='automation_cv')
        if self.destination_mysql_helper:
            self.log.info("Deleting Automation Created Tables in Destination MySQL Server")
            self.destination_mysql_helper.cleanup_test_data(
                database_prefix='automation_cv')

    def run(self):
        """Run function for test case execution"""

        try:
            destination_client = self.commcell.clients.get(
                self.tcinputs['DestinationClientName'])
            destination_instance = destination_client.agents.get(
                'MySQL').instances.get(self.tcinputs['DestinationInstanceName'])
            destination_subclient = destination_instance.backupsets.get(
                'defaultdummybackupset').subclients.get(self.tcinputs['SubclientName'])

            if 'windows' in self.client.os_info.lower():
                raise Exception("Kindly provide unix/linux source client as input")

            if 'windows' in destination_client.os_info.lower():
                raise Exception("Kindly provide unix/linux destination client as input")

            if not self.subclient.is_default_subclient:
                raise Exception("Kindly provide default subclient as input")

            self.meb_existing_flag = self.mysql_helper.verify_meb_properties_on_instance(
                source_instance=self.instance, destination_instance=destination_instance,
                source_meb_bin_path=self.tcinputs.get("meb_binary_path"))

            self.destination_mysql_helper = MYSQLHelper(self.commcell, destination_subclient,
                                                        destination_instance,
                                                        destination_client.client_hostname,
                                                        destination_instance.mysql_username)

            # Executing MEB backups with No Lock enabled in MySQL Instance
            backup_db_list, db_size_after_inc2_bkp, inc_backup_2, meb_backup_sbt_image = \
                self.mysql_helper.run_meb_backup_flow()

            # Out of Place MEB restore
            self.log.info("Running Cross Machine MEB Restore from Increment Backup 2")
            restore_job = self.mysql_helper.run_meb_restore_flow(
                dest_client_name=destination_client.name,
                dest_instance_name=destination_instance.name,
                from_time=inc_backup_2.start_timestamp, to_time=inc_backup_2.end_timestamp,
                browse_jobid=int(inc_backup_2.job_id),
                temporary_staging=destination_instance.log_data_directory)

            self.destination_mysql_helper.validate_meb_data_and_image(
                db_size_after_inc2_bkp, backup_db_list, restore_job.job_id, meb_backup_sbt_image)

            # Check No Locking status in MySQL Instance for MySQL Enterprise backup
            self.no_locking_flag = self.instance.no_lock_status
            self.log.info("No Locking status before execution of test case is %s",
                          self.no_locking_flag)

            if not self.no_locking_flag:
                self.instance.no_lock_status = True

            # Executing MEB backups with No Lock enabled in MySQL Instance
            backup_db_list, db_size_after_inc2_bkp, inc_backup_2, meb_backup_sbt_image = \
                self.mysql_helper.run_meb_backup_flow(check_no_lock_flag=True)

            # Out of Place MEB restore
            self.log.info("Running Cross Machine MEB Restore from Increment Backup 2")
            restore_job = self.mysql_helper.run_meb_restore_flow(
                dest_client_name=destination_client.name,
                dest_instance_name=destination_instance.name,
                from_time=inc_backup_2.start_timestamp, to_time=inc_backup_2.end_timestamp,
                browse_jobid=int(inc_backup_2.job_id),
                temporary_staging=destination_instance.log_data_directory)

            self.destination_mysql_helper.validate_meb_data_and_image(db_size_after_inc2_bkp,
                                                                      backup_db_list,
                                                                      restore_job.job_id,
                                                                      meb_backup_sbt_image)
        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
