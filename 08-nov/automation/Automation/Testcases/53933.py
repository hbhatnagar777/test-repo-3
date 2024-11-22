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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from time import sleep, mktime
from datetime import datetime
from Install import installer_utils
from AutomationUtils import logger, constants, database_helper, windows_machine, options_selector
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        File IO monitoring for laptops.
        This test case does the following
        Scenario 1 - check if non-moniker contents are not monitored in laptop.
        Scenario 2 - check if moniker contents are monitored in laptop.
        """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "File IO monitoring for laptops"
        self.hostname = None
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.test_path2 = None
        self.helper = None
        self.client_machine = None
        self.utility = options_selector.OptionsSelector(self.commcell)


    def execute_sqlite_query(self):
        """ Function to connect to SQLite DB."""
        log = logger.get_log()
        try:
            query = "select total from FileIOInfo order by Time desc Limit 1"
            sql_db = database_helper.SQLite("C:\\Users\\Administrator\\Documents\\FolderWatcher.db")
            execute_db = sql_db.getConnectionObject()
            cur = execute_db.cursor()
            cur.execute(query)
            total = cur.fetchone()[0]
            execute_db.close()
            return total
        except Exception as err:
            log.error("Failed during SQLite DB query. %s", err)

    def comp_mtime(self, mtime, cur_time, folderwatcher_path=None, modify_path=None):
        """Compares folderwatcher mtime with current
        time fetched before test data creation.
        Args:
            mtime    (int)    --    Modified time of folderwatcher.db file or reg key value.
            cur_time    (int)    --    Current time on client machine.
            folderwatcher_path      (string)   --    path where FolderWatcher.db file is present.
            modify_path    (string)    --    path to modify temp file.

        Returns:
            True if folderwatcher mtime is greater than cur_time.
            True if reg key time (mtime) is greater than cur_time.
            False if reg key update or folderwatcher update takes more than 20 mins.

        Raises:
            Exception:
                If a valid timestamp is not passed.
                If valid path is not passed.
        """
        log = logger.get_log()
        timeout = 0
        try:
            while mtime < cur_time:
                if timeout > 1200:
                    log.error("Timed out waiting for mtime value to be updated.")
                    return False
                else:
                    log.info("mtime is less than current time captured after test data creation."
                             "Sleeping for 5 mins.")
                    sleep(300)
                    timeout += 300
                    if modify_path is not None:
                        log.info("Modifying one file in path %s", modify_path)
                        self.client_machine.modify_test_data(
                            modify_path, False, True)
                        mtime = self.get_folderwatcher_mtime(folderwatcher_path)
                    else:
                        mtime = int(self.utility.check_reg_key(
                            self.client_machine, "EventManager", "FileIOLastUpdateTime", fail=False))
                        if not mtime:
                            mtime = 0
            log.info("mtime updated successfully : %s", mtime)
            return True
        except Exception as err:
            log.error("Exception during mtime comparison - %s", err)

    def get_folderwatcher_mtime(self, folderwatcher_path):
        """Function returns mtime of folderwatcher .db file.
        Args:
            folderwatcher_path      (string)   --    path where FolderWatcher.db file is present.

        Returns:
            Modified time stamp on folderwatcher.db file on client machine.

        Raises:
            Exception:
                If valid path is not passed.
        """

        folderwatcher_mtime = self.client_machine.get_file_property(
            folderwatcher_path, False, "LastWriteTime").strip()
        folderwatcher_mtime = datetime.strptime(
            folderwatcher_mtime, "%A, %B %d, %Y %H:%M:%S")
        folderwatcher_mtime = int(mktime(
            folderwatcher_mtime.timetuple()))
        return folderwatcher_mtime

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        win = windows_machine.WindowsMachine()

        try:
            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            nonmoniker_test_path = self.test_path
            moniker_test_path = self.test_path2

            log.info("""File System File Activity Anomaly Detection -
        This test case does the following
        Scenario 1 - check if non-moniker contents are not monitored in laptop.
        Scenario 2 - check if moniker contents are monitored in laptop.""")

            log.info("Checking if OS type is Windows")

            if self.applicable_os != 'WINDOWS':
                raise Exception("OS type is not valid for this test case")
            else:
                log.info("OS Type Windows detected. Proceeding with Monitoring validation.")
            log.info("Fetching Base path from reg key.")
            if self.client_machine.check_registry_exists(r"Base", "dBASEHOME"):
                regkey_base_path = self.client_machine.get_registry_value(r"Base", "dBASEHOME")
            else:
                raise Exception("Base Reg key not found.")
            folderwatcher_path = "{0}\\FolderWatcher.db" \
                .format(regkey_base_path)
            folderwatcher_mtime_before = self.get_folderwatcher_mtime(folderwatcher_path)

            log.info("FolderWatcher DB file mtime before test data creation: %s ", folderwatcher_mtime_before)
            net_path = folderwatcher_path.replace(":", "$")
            net_path = "\\\{0}\\{1}".format(self.hostname, net_path)
            log.info("Net path %s", net_path)

            log.info("Scenario 1: Verify if Non-moniker "
                     "content is not monitored.")

            log.info("Copying folderwatcher for DB query.")

            win.copy_file_to_local(
                net_path, "C:\\Users\\Administrator\\Documents\\FolderWatcher.db")

            total_before = self.execute_sqlite_query()
            log.info("Deleting db File.")

            win.delete_file("C:\\Users\\Administrator\\Documents\\FolderWatcher.db")
            log.info("Count before test data creation in DB %s", total_before)
            log.info("Creating Test Data in Non-moniker path.")
            self.client_machine.generate_test_data(
                nonmoniker_test_path, 1, 100000)
            current_time = int(installer_utils.get_current_time())
            log.info("Current time :%s", current_time)
            log.info("Test Data creation completed. Fetching mtime of folderwatcher.db file.")
            folderwatcher_mtime_after = self.get_folderwatcher_mtime(folderwatcher_path)
            log.info("FolderWatcher DB file mtime after test data creation: %s ", folderwatcher_mtime_after)
            log.info("Creating Directory.")
            self.client_machine.create_directory("{0}_new".format(moniker_test_path))
            log.info("Creating one file in path %s", "{0}_new".format(moniker_test_path))
            self.client_machine.create_file("{0}_new\\File.txt".format(moniker_test_path),"Sample")
            # FoderWatcher mtime comparison
            log.info("Verifying if folderwatcher db is updated.")

            if not self.comp_mtime(folderwatcher_mtime_after,
                                   current_time, folderwatcher_path, "{0}_new".format(moniker_test_path)):
                raise Exception("Timeout. Folder watcher DB"
                                " is not getting updated.")
            log.info("Folderwatcher db updated. Verifying if reg key is updated.")
            # RegKey mtime comparison
            regkey_timestamp = int(self.utility.check_reg_key(self.client_machine, "EventManager", "FileIOLastUpdateTime", fail=False))
            if not regkey_timestamp:
                regkey_timestamp = 0

            log.info("Reg Key FileIOLastUpdateTime value: %s ",
                     regkey_timestamp)
            if not self.comp_mtime(regkey_timestamp, current_time):
                raise Exception("Anomaly Algorithm is not running as Expected.")

            log.info("FileIOLastUpdateTime Reg key is updated.")

            log.info("Checking if creates are captured  in DB.")
            log.info("Copying folderwatcher for DB query.")

            win.copy_file_to_local(
                net_path, "C:\\Users\\Administrator\\Documents\\FolderWatcher.db")
            total_after = self.execute_sqlite_query()
            log.info("Deleting DB file from local.")

            win.delete_file("C:\\Users\\Administrator\\Documents\\FolderWatcher.db")

            log.info("Total items captured %s", total_after)

            if total_after - total_before >= 100000:
                raise Exception("Non-moniker content is being monitored.")
            log.info("Scenario to verify if Non-moniker content is being monitored passed.")

            log.info("Scenario 2 - Verify if Moniker contents are monitored.")

            folderwatcher_mtime_before = self.get_folderwatcher_mtime(folderwatcher_path)

            log.info("FolderWatcher DB file mtime before test data creation: %s", folderwatcher_mtime_before)

            log.info("Copying folderwatcher for DB query.")

            win.copy_file_to_local(
                net_path, "C:\\Users\\Administrator\\Documents\\FolderWatcher.db")

            total_before = self.execute_sqlite_query()

            log.info("Deleting DB file from local.")

            win.delete_file("C:\\Users\\Administrator\\Documents\\FolderWatcher.db")
            log.info("Count before test data creation in DB %s", total_before)
            log.info("Creating Test Data in Moniker path.")
            self.client_machine.generate_test_data(
                moniker_test_path, 1, 100000)
            current_time = int(installer_utils.get_current_time())
            log.info("Current time :%s", current_time)
            log.info("Test Data creation completed. "
                     "Fetching mtime of folderwatcher.db file.")
            folderwatcher_mtime_after = self.get_folderwatcher_mtime(folderwatcher_path)
            log.info("FolderWatcher DB file mtime after testdata creation: %s", folderwatcher_mtime_after)
            log.info("Verifying if folderwatcher db is updated.")
            # FoderWatcher mtime comparison
            if not self.comp_mtime(folderwatcher_mtime_after,
                                   current_time, folderwatcher_path, "{0}_new".format(moniker_test_path)):
                raise Exception("Timeout. Folder watcher DB is not getting updated.")
            log.info("Folderwatcher db updated. Verifying if reg key is updated.")
            # RegKey mtime comparison
            regkey_timestamp = int(self.utility.check_reg_key(self.client_machine, "EventManager", "FileIOLastUpdateTime", fail=False))
            if not regkey_timestamp:
                regkey_timestamp = 0
            log.info("Reg Key FileIOLastUpdateTime value: %s", regkey_timestamp)
            if not self.comp_mtime(regkey_timestamp, current_time):
                raise Exception("Anomaly Algorithm is not running as Expected.")
            log.info("FileIOLastUpdateTime Reg key is updated.")
            log.info("Checking if creates are captured  in DB.")
            log.info("Copying folderwatcher for DB query.")
            win.copy_file_to_local(
                net_path, "C:\\Users\\Administrator\\Documents\\FolderWatcher.db")
            total_after = self.execute_sqlite_query()
            log.info("Deleting DB file from local.")
            win.delete_file("C:\\Users\\Administrator\\Documents\\FolderWatcher.db")
            log.info("Total items captured%s", total_after)

            if total_after-total_before >= 100000:
                log.info("Scenario to verify if moniker content is being monitored passed.")
            else:
                raise Exception("Moniker content is not being monitored.")


            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.client_machine.remove_directory(nonmoniker_test_path)
            self.client_machine.remove_directory(moniker_test_path)
            self.client_machine.remove_directory("{0}_new".format(moniker_test_path))