# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         -- initialize the Test case required objects

    run()           --  Oracle Acceptance Testcase iwth basic backup and restore functions

"""
import os
import time
from datetime import datetime, timedelta

from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils import database_helper
from AutomationUtils.config import ConfigReader
from AutomationUtils.constants import SnapShotEngineNames
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing basic acceptance of SNAP Recovery points """

    def __init__(self):
        """Initializes test case class objects"""
        super(TestCase, self).__init__()
        self.sqldump_file1 = "before_backup_full.txt"
        self.sqldump_file2 = "after_restore.txt"
        self.name = "Basic Acceptance - SNAP Recovery Points"

        self.tcinputs = {
            "SQLServerUser": None,
            "SQLServerPassword": None,
            "LibraryName": None,
            "MediaAgentName": None,

            # eg: "NETAPP"
            "SnapEngineName": None,

            # eg: "F:\\databases"  no"\\" at the end after the directory name
            "DirectoryPathOnLUN": None

        }
        self.agent_name = None
        self.sqlhelper = None
        self.client_name = None

        # csdb sa account
        config = ConfigReader().get_config()
        self.commserv_sql_user = config.SQL.CS_Username
        self.commserv_sql_password = config.SQL.CS_Password
        self.commserv_sql_instance_name = config.SQL.CS_InstanceName

        # client sql server login
        self.client_sql_user = None
        self.client_sql_password = None
        self.client_sql_instance_name = None

        self.dbs = None
        self.snap_engine_name = None
        self.db_path = None
        self.media_agent = None
        self.library_name = None

    def setup(self):
        """
        initializing the db connections, creates a database, populates the tables,
        creates a subclient with given plan name

        sql_server (MSSQL obj) --  "MSSQL helper obj for sql server operations"

         db   (dict)       --  "dict from json file with required db details"

        return:
            NONE
        """

        self.client_sql_user = self.tcinputs["SQLServerUser"]
        self.client_sql_password = self.tcinputs["SQLServerPassword"]
        self.client_sql_instance_name = self.instance.instance_name

        self.client_name = self.client.client_name
        self.agent_name = self.agent.agent_name

        self.media_agent = self.tcinputs["MediaAgentName"]
        self.library_name = self.tcinputs["LibraryName"]

        self.db_path = self.tcinputs["DirectoryPathOnLUN"]

        self.snap_engine_name = self.tcinputs["SnapEngineName"]
        self.sqlhelper = SQLHelper(self,
                                   self.client_name,
                                   self.client_sql_instance_name,
                                   self.client_sql_user,
                                   self.client_sql_password)

    def run(self):
        """Main function of this test case execution

            returns:
                    None
        """

        try:
            # creating a subclient and databases
            self.log.info("creating a db and subclient using sqlhelper")
            self.sqlhelper.sql_setup(noof_dbs=1,
                                     noof_tables_ffg=1,
                                     noof_files_ffg=1,
                                     media_agent=self.media_agent,
                                     library_name=self.library_name,
                                     snap_setup=True,
                                     db_path=self.db_path
                                     )

            self.dbs = self.sqlhelper.dbname + "1"
            self.sqlhelper.dbinit.set_database_autoclose_property(self.dbs, "OFF")
            self.sqlhelper.dbinit.change_recovery_model(self.dbs[:-1], 1, "FULL")

            """Enabling Intelli-Snap for the created subclient"""
            self.subclient = self.sqlhelper.subclient
            self.log.info('Enabling Snap backup on subclient')

            if not SnapShotEngineNames(self.snap_engine_name):
                self.log.info("Snap Engine Name [{0}] is invalid. Please enter correct Snap Engine Name"
                              .format(self.snap_engine_name))

            self.subclient.enable_intelli_snap(self.snap_engine_name)

            job_id = self.sqlhelper.sql_backup("Full")

            # check backup level for Full
            backup_level = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if backup_level != "Full":
                raise Exception("Wrong backup level of the database detected in the job")
            self.log.info("Backup level confirmed: %s", backup_level)

            randomization = 100

            # get table shuffled list
            return_string, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                randomization,
                self.sqlhelper.noof_dbs,
                self.sqlhelper.noof_ffg_db,
                self.sqlhelper.noof_tables_ffg
            )

            # modify database before TL
            if not self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3):
                raise Exception("Database modification failed.")

            # run a TL backup
            job_id = self.sqlhelper.sql_backup('transaction_log')

            # check backup level for TL1
            backup_level = self.sqlhelper.dbvalidate.get_sql_backup_type(job_id, multidb=False)
            if str(backup_level) != "Transaction Log":
                raise Exception("Wrong backup level of the database detected in the job")
            self.log.info("Backup level confirmed: %s", str(backup_level))

            # write the database to file for comparison before DIFF
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, self.sqldump_file1),
                    self.dbs[:-1], list1, list2, list3, 'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # browsing instance for granular level restore of db
            if self.dbs in self.instance.browse()[0]:
                self.log.info("%s is added to granular level restore successfully", self.dbs)
            else:
                raise Exception("failed to add database to"
                                " granular restore at instance level")

            # creating recovery point
            self.log.info("creating the recovery Point")
            job, recovery_point_id, restored_dbname = self.instance.create_recovery_point(self.dbs, snap=True)
            if not job.wait_for_completion():
                raise Exception("Job {0} has failed".format(job.job_id))
            self.log.info("created recovery point with jobid= %s and mountPath=%s", job.job_id, restored_dbname)

            # set auto close off for the recovery point
            self.sqlhelper.dbinit.set_database_autoclose_property(restored_dbname, "OFF")

            # changing expiration time to 4 min
            exp_time = 4
            csdb_con = database_helper.MSSQL(self.commserv_sql_instance_name, self.commserv_sql_user,
                                             self.commserv_sql_password, "CommServ", use_pyodbc=True)

            future = datetime.now() + timedelta(minutes=exp_time)
            expire_time = int(datetime.timestamp(future))

            self.sqlhelper.set_recovery_point_expire_time(recovery_point_id, csdb_con, expire_time)
            self.log.info("expire time set to %d min", exp_time)
            csdb_con.close()

            # checking if the recovery point is accessible
            if not self.sqlhelper.dbinit.check_database(restored_dbname):
                raise Exception("recovery point database {0} is not accessible".format(restored_dbname))

            # checking if recovery point is added to list of recovery points
            if not self.sqlhelper.recovery_point_exists(restored_dbname):
                raise Exception("failed to add database to list of recovery points")
            self.log.info("recovery point added to the list")

            # fetching do not backup subclient contents
            do_not_backup = self.sqlhelper.do_not_backup_subclient
            do_not_backup.refresh()
            if restored_dbname not in do_not_backup.content:
                raise Exception("Recovery point Database is not added to Do Not Backup SubClient")
            self.log.info("Recovery point added to do not backup sub client")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, self.sqldump_file2),
                    restored_dbname, list1, list2, list3, 'INCREMENTAL', use_same_db_name=True):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            self.log.info("%s Validating content %s", "*" * 10, "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(
                    os.path.join(self.sqlhelper.tcdir, self.sqldump_file1),
                    os.path.join(self.sqlhelper.tcdir, self.sqldump_file2)):
                raise Exception("Failed to compare both files.")
            self.log.info("Transactional Backup data is verified successfully")

            # wait for expiration time to end
            wait_time = (exp_time + 6) * 60
            self.log.info("sleep for %d seconds.. waiting for recovery point to expire", wait_time)
            time.sleep(wait_time)

            # checking if the database is removed
            if self.sqlhelper.dbinit.check_database(restored_dbname):
                raise Exception("recovery point database {0} is not removed".format(restored_dbname))
            self.log.info("recovery point database is removed")

            # checking if the db is removed from list of recovery points
            if self.sqlhelper.recovery_point_exists(restored_dbname):
                raise Exception("failed to remove database to list of recovery points")
            self.log.info("recovery point is removed from list of recovery points")

            # checking if it added to Do Not Backup Sub Client
            do_not_backup.refresh()
            if restored_dbname in do_not_backup.content:
                raise Exception("Recovery point Database {0} is not removed"
                                " from Do Not Backup SubClient".format(restored_dbname))
            self.log.info("database removed from Do Not Backup subclient")

            self.log.info("%s TestCase %s successfully completed! %s", "*" * 10, self.id, "*" * 10)
        finally:
            # executing teardown of sqlhelper
            self.sqlhelper.sql_teardown()
