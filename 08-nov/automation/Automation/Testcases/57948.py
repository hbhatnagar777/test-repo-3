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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os
import re
import time
import datetime
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Application.SQL import sqlconstants
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SQL Dump and Sweep - Basic Acceptance"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MSSQL
        self.feature = self.features_list.DATARECOVERY
        self.show_to_user = False

        self.tcinputs = {
            "MediaAgentName": None,
            "LibraryName": None,
            "SQLServerUser": None,
            "SQLServerPassword": None
        }

        self.sqlhelper = None
        self.sqlmachine = None
        self.ma_machine = None

    def run(self):
        """Main function for test case execution"""
        log = self.log
        clientname = self.client.client_name
        instancename = self.instance.instance_name
        media_agent = self.tcinputs["MediaAgentName"]
        library_name = self.tcinputs["LibraryName"]
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]

        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass, _media_agent=media_agent)
        self.sqlmachine = Machine(self.client)

        try:
            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            self.sqlhelper.sql_setup(noof_dbs=1, media_agent=media_agent, library_name=library_name)
            self.subclient = self.sqlhelper.subclient

            # run a full backup
            self.sqlhelper.sql_backup('Full')

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg)
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # modify dbs
            self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3)

            # write the database to file for comparison before turning on dump/sweep schedule

            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")
            # create automatic schedule for dump and sweep
            max_interval_minutes = 2
            self.sqlhelper.create_sql_automatic_schedule(
                self.subclient,
                use_dump_sweep=True
            )

            # wait some time for dump to happen.. should fall in line with max_interval_mins
            self.log.info("Sleeping for {0} minutes for dumps to happen".format(max_interval_minutes + 3))
            time.sleep((max_interval_minutes + 3) * 60)

            # check if dump path exists yet
            if not self.sqlhelper.sql_subclient_dump_path_exists(
                    self.sqlhelper.sql_subclient_dump_path(self.subclient)
            ):
                raise Exception(
                    "SQL Dump and Sweep file path [{0}] hasn't been populated. "
                    "Verify there are no issues with the media agent [{1}]".format(
                        self.sqlhelper.sql_subclient_dump_path(self.subclient),
                        media_agent
                    )
                )

            # build dict with original database names and new names
            db1_restore = self.sqlhelper.dbname + str(1)
            db1_restore_list = [db1_restore]

            database_name_list = []

            database_name_dict = {
                'database_names': {
                    sqlconstants.DATABASE_ORIG_NAME: db1_restore,
                    sqlconstants.DATABASE_NEW_NAME: db1_restore
                }
            }
            database_name_list.append(database_name_dict)

            # get the file path list for restore
            restore_path_list = self.sqlhelper.get_file_list_restore(database_name_list,
                                                                     restore_path=self.sqlhelper.tcdir,
                                                                     filerename=True)
            # kill db connections and restore db1 using job_id_log1
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore to same instance - new file names & new path" + "*" * 10)
            restore1_job_id = self.sqlhelper.sql_restore(
                db1_restore_list,
                restore_path=restore_path_list,
                return_job_id=True
            )

            # check log file for restores from disk job_id
            restore1_loglines = self.sqlmachine.get_logs_for_job_from_file(
                str(restore1_job_id),
                sqlconstants.SQL_RESTORE_LOG,
                search_term="Info--: Starting"
            )
            log.info("SQL RESTORE QUERY LOG SNIPPET for JOB [{0}]:\n{1}".format(restore1_job_id, restore1_loglines))

            if not re.search('Starting SDT CSLess log restore of db \\[(\\w+)\\]', restore1_loglines):
                raise Exception("SQL Restore was not from dump location")

            # verify database is online after restore
            if not self.sqlhelper.dbvalidate.is_db_online(db1_restore, useexistingdb=False):
                raise Exception("Databases are not online on source instance.")

            # verify db is utilizing new location
            dbpath1 = self.sqlhelper.dbvalidate.db_path(db1_restore)[1]
            if not any(self.sqlhelper.tcdir in s for s in dbpath1):
                raise Exception("Restored database was not restored to its new location.")

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                        os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

            # set to time to sweep after calculating time difference between MA and client
            ma_tz = self.commcell.clients.get(media_agent).timezone
            ma_tz_val = ma_tz[4:10]
            client_tz = self.client.timezone
            client_tz_val = client_tz[4:10]
            
            log.info("Client Timezone [{0}] and Media Agent Timezone [{1}]".format(client_tz, ma_tz))

            tfmt = '%H:%M'
            tzdelta = datetime.datetime.strptime(ma_tz_val[1:], tfmt) - datetime.datetime.strptime(
                client_tz_val[1:],
                tfmt
            )
            start_in_mins = 3

            sweep_start_time = (datetime.datetime.now() + datetime.timedelta(minutes=start_in_mins)).strftime(tfmt)

            # sweep time will change if MA and Client aren't in same timezone
            if ma_tz_val > client_tz_val:
                sweep_start_time = (datetime.datetime.now() + datetime.timedelta(minutes=start_in_mins) - tzdelta)\
                    .strftime(tfmt)
            elif client_tz_val > ma_tz_val:
                sweep_start_time = (datetime.datetime.now() + datetime.timedelta(minutes=start_in_mins) + tzdelta)\
                    .strftime(tfmt)

            self.sqlhelper.set_sweep_start_time(sweep_start_time)

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100, self.sqlhelper.noof_dbs, self.sqlhelper.noof_ffg_db, self.sqlhelper.noof_tables_ffg)
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # modify dbs again
            self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3, p=2)

            log.info("Sleeping {0} minutes to wait for SQL sweep job happen.".format(start_in_mins + 3))
            time.sleep((start_in_mins + 3) * 60)

            # modify dbs again
            self.sqlhelper.modifydatabase.modify_db_for_inc(self.sqlhelper.dbname, list1, list2, list3, p=3)

            log.info("Sleeping {0} minutes to wait for additional log dump to happen.".format(start_in_mins))
            time.sleep(start_in_mins * 60)

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # kill db connections and restore db1, here we should see hybrid restore (archFile and dump folder)
            self.sqlhelper.dbinit.kill_db_connections(self.sqlhelper.dbname, self.sqlhelper.noof_dbs, True)

            self.log.info("*" * 10 + " Run Restore to same instance - new file names & new path" + "*" * 10)
            restore2_job_id = self.sqlhelper.sql_restore(
                db1_restore_list,
                restore_path=restore_path_list,
                return_job_id=True
            )

            # verify database is online after restore
            if not self.sqlhelper.dbvalidate.is_db_online(db1_restore, useexistingdb=False):
                raise Exception("Databases are not online on source instance.")

            # verify db is utilizing new location
            dbpath1 = self.sqlhelper.dbvalidate.db_path(db1_restore)[1]
            if not any(self.sqlhelper.tcdir in s for s in dbpath1):
                raise Exception("Restored database was not restored to its new location.")

            # check log file for restores from disk job_id
            restore2_loglines = self.sqlmachine.get_logs_for_job_from_file(
                str(restore2_job_id),
                sqlconstants.SQL_RESTORE_LOG,
                search_term="-Info--: Starting"
            )
            log.info("SQL RESTORE QUERY LOG SNIPPET for JOB [{0}]:\n{1}".format(restore2_job_id, restore2_loglines))

            if not (
                    re.search('Starting log restore of db \\[(\\w+)\\]', restore2_loglines)
                    and re.search('Starting SDT CSLess log restore of db \\[(\\w+)\\]', restore2_loglines)
            ):
                raise Exception(
                    "SQL Restore was not of hybrid type. Expecting restore from archive file and dump location"
                )

            # write the restored database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                    self.sqlhelper.dbname,
                    list1,
                    list2,
                    list3,
                    'INCREMENTAL'
            ):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            log.info("*" * 10 + " Validating content " + "*" * 10)
            if not self.sqlhelper.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                        os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        self.sqlhelper.sql_teardown(cleanup_dumpsweep=True)
