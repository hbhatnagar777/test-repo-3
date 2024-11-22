# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    _filesystem_license_usage() --  To get file system license status of the given server

    _ddb_subclient_validation() --  To validate if 'DDBBackup' subclient is present for the given server

    _get_storage_dedupe_flags() --  To get default dedupe flags set on SIDB store of given disk storage

    _get_storage_flags_not_set()--  To know which all flags are not set that should be set by default on a storage

    _get_storage_flags_set()    --  To know which all flags are set that should not be set by default on a storage

    setup()         --  setup function of this test case

    run()           --  run function of this test case

Inputs:

    hostname        --      server hostname to install MediaAgent packages on

    username        --      username of the server machine i.e domain\\username

    password        --      password of the server machine

    OS type         --      server OS type ('Windows' or 'Unix and Linux')

    packages        --      packages to install on the server (eg: "Media Agent,File System")

    backup location --      backup location for disk storage

    DDB location    --      deduplication database location for disk storage
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.DeploymentHelper import DeploymentHelper
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.AdminConsolePages.media_agents import MediaAgents


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """
            Initializing the TestCase class object

            Testcase json example:
                    "54617": {
                        "ServerHostName": "MachineName",
                        "ServerUsername": "domain\\user",
                        "ServerPassword": "password",
                        "ServerOSType": "windows",
                        "Packages":	"Media Agent,File System",
                        "BackupLocation": "E:\\Test\\MP",
                        "DDBLocation": "E:\\Test\\DDB"
                    }
        """

        super(TestCase, self).__init__()
        self.name = "Admin Console - Install Server and validate 'DDBBackup' subclient creation and " \
                    "default dedupe flags on creating a disk storage"
        self.browser = None
        self.admin_console = None
        self.deployment_helper = None
        self.storage_helper = None
        self.media_agents = None
        self.server_display_name = None
        self.disk_storage_name = None
        self.ddb_location = None
        self.mm_helper = None
        self.tcinputs = {
            "ServerHostName": None,
            "ServerUsername": None,
            "ServerPassword": None,
            "ServerOSType": None,
            "Packages": None,
            "BackupLocation": None,
            "DDBLocation": None
        }

    def _filesystem_license_usage(self, hostname):
        """
        To get file system license status of the given server
            Args:
             hostname (str) --  Hostname of the server

            Returns:
                True    -   if license is in use
                False   -   if license is not in use
        """

        query = f"""SELECT	count(1)
                    FROM	LicUsage LU
                    JOIN	APP_Client Cli
                        ON	LU.CId = Cli.id
                    WHERE	LU.AppType = 33	
                    AND     LU.LicType = 1
                    AND     Cli.net_hostname = '{hostname}'"""
        self.csdb.execute(query)
        if self.csdb.fetch_one_row()[0] == '0':
            return False
        return True

    def _ddb_subclient_validation(self, server_name):
        """
        To validate if 'DDBBackup' subclient is present for the given server
            Args:
             server_name (str) --  Name of the server

            Returns:
                True    -   if subclient present
                False   -   if subclient not present
        """

        query = f"""SELECT	count(1)
                    FROM	APP_Application APP
                    JOIN	APP_Client Cli
                        ON	APP.clientId = Cli.id
                    WHERE	APP.subclientName = 'DDBBackup'
                    AND     Cli.net_hostname = '{server_name}'"""
        self.csdb.execute(query)
        if self.csdb.fetch_one_row()[0] == '0':
            return False
        return True

    def _get_storage_dedupe_flags(self, disk_storage_name):
        """
        To get default dedupe flags set on SIDB store of given disk storage
            Args:
             disk_storage_name (str) --  Name of the disk storage

            Returns:
                list    --  contains storage dedupe flags, extended flags
        """

        query = f"""SELECT	DDB.flags, DDB.ExtendedFlags
                    FROM	IdxSIDBStore DDB
                    JOIN	archGroupCopy AGC
                        ON	DDB.SIDBStoreId = AGC.SIDBStoreId
                    JOIN	archGroup AG
                            ON	AGC.archGroupId = AG.id
                    WHERE	AG.name = '{disk_storage_name}'"""
        self.csdb.execute(query)

        return self.csdb.fetch_one_row()

    def _get_storage_flags_not_set(self, dedupe_flag, extended_flag):
        """
        To know which all flags are not set that should be set by default on a storage
            Args:
             dedupe flag (int) --  storage dedupe flag

             extended_flag (int) -- storage extended flag

            Returns:
                None
        """

        if dedupe_flag & 2 == 0:
            self.log.error('SW_COMPRESSION flag is not set')
        if dedupe_flag & 16 == 0:
            self.log.error('GLOBAL_DEDUPE flag is not set')
        if dedupe_flag & 65536 == 0:
            self.log.error('STORE_DEDUPFACTOR_ENABLED flag is not set')
        if dedupe_flag & 131072 == 0:
            self.log.error('SECONDARY_FOLLOW_SOURCE_DEDUP_BLOCK flag is not set')
        if dedupe_flag & 1048576 == 0:
            self.log.error('SILO_PREPARED flag is not set')
        if dedupe_flag & 8388608 == 0:
            self.log.error('ENABLE_DDB_VALIDATION flag is not set')
        if dedupe_flag & 536870912 == 0:
            self.log.error('PRUNING_ENABLED flag is not set')
        if extended_flag & 2 == 0:
            self.log.error('DEFAULT Extended flag is not set')
        if extended_flag & 4 == 0:
            self.log.error('MARK_AND_SWEEP_ENABLED Extended flag is not set')
        if extended_flag & 8 == 0:
            self.log.error('ZEROREF_LOGGING_ENABLED Extended flag is not set')

    def _get_storage_flags_set(self, dedupe_flag, extended_flag):
        """
        To know which all dedupe flags are set that should not be set by default on a storage
            Args:
             dedupe flag (int) --  storage dedupe flag

             extended_flag (int) -- storage extended flag

            Returns:
                None
        """

        if dedupe_flag & 1 != 0:
            self.log.error('MULTI_TAG_HEADER flag is set')
        if dedupe_flag & 4 != 0:
            self.log.error('NONTRANS_DB flag is set')
        if dedupe_flag & 8 != 0:
            self.log.error('NO_SECONDARY_TABLE flag is set')
        if dedupe_flag & 32 != 0:
            self.log.error('SINGLE_THREAD_DB flag is set')
        if dedupe_flag & 64 != 0:
            self.log.error('SIDB_SUSPENDED flag is set')
        if dedupe_flag & 128 != 0:
            self.log.error('RECYCLABLE flag is set')
        if dedupe_flag & 256 != 0:
            self.log.error('SILO_AGED flag is set')
        if dedupe_flag & 512 != 0:
            self.log.error('DDB_COPYOP_INPROGRESS flag is set')
        if dedupe_flag & 1024 != 0:
            self.log.error('DDB_MOVEOP_INPROGRESS flag is set')
        if dedupe_flag & 2048 != 0:
            self.log.error('DDB_ARCHIVE_STATUS flag is set')
        if dedupe_flag & 4096 != 0:
            self.log.error('SIDB_ENGINE_RUNNING flag is set')
        if dedupe_flag & 8192 != 0:
            self.log.error('MEMDB_DDB flag is set')
        if dedupe_flag & 16384 != 0:
            self.log.error('OPTIMIZE_DB flag is set')
        if dedupe_flag & 32768 != 0:
            self.log.error('STORE_SEALED flag is set')
        if dedupe_flag & 2097152 != 0:
            self.log.error('SILO_ENABLED flag is set')
        if dedupe_flag & 4194304 != 0:
            self.log.error('DDB_VALIDATION_FAILED flag is set')
        if dedupe_flag & 16777216 != 0:
            self.log.error('DDB_UNDER_MAINTENANCE flag is set')
        if dedupe_flag & 33554432 != 0:
            self.log.error('DDB_NEEDS_AUTO_RESYNC flag is set')
        if dedupe_flag & 67108864 != 0:
            self.log.error('DDB_VERIFICATION_INPROGRESS flag is set')
        if dedupe_flag & 134217728 != 0:
            self.log.error('TIMESTAMP_MISMATCH flag is set')
        if dedupe_flag & 268435456 != 0:
            self.log.error('DDB_VERIFICATION_INPROGRESS_ALLOW_BACKUPS flag is set')
        if dedupe_flag & 1073741824 != 0:
            self.log.error('DDB_RESYNC_IN_PROGRESS flag is set')
        if dedupe_flag & 214748368 != 0:
            self.log.error('DDB_PRUNING_IN_PROGRESS flag is set')
        if extended_flag & 1 != 0:
            self.log.error('IDX_SIDBSTORE_EX_FLAGS_FULL extended flag is set')

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def cleanup(self):
        """To perform cleanup operation"""

        try:
            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.disk_storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.disk_storage_name):
                self.log.info('Deletes storage %s', self.disk_storage_name)
                self.storage_helper.delete_disk_storage(self.disk_storage_name)
                # Delete Library
                if self.commcell.disk_libraries.has_library(self.disk_storage_name):
                    self.commcell.disk_libraries.delete(self.disk_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.disk_storage_name)

            # To retire server if exists
            self.log.info('Check for server with hostname %s', self.tcinputs['ServerHostName'])
            if self.commcell.clients.has_client(self.tcinputs['ServerHostName']):
                self.server_display_name = self.commcell.clients.get(self.tcinputs['ServerHostName']).display_name
                server_name = self.commcell.clients.get(self.tcinputs['ServerHostName']).client_name

                # To delete media agent if exists
                if self.commcell.media_agents.has_media_agent(server_name):
                    self.log.info('Deleting MediaAgent for %s', server_name)
                    self.admin_console.navigator.navigate_to_media_agents()
                    self.media_agents.delete_media_agent(self.server_display_name)
                    self.log.info('Deleting MediaAgent successful for %s', server_name)
                    self.commcell.refresh()

                self.log.info('Retiring server %s', server_name)
                self.deployment_helper.retire_server(self.server_display_name)
                self.log.info('Retire server %s successful', server_name)
                self.commcell.refresh()

                if self.commcell.clients.has_client(self.tcinputs['ServerHostName']):
                    self.log.info('Deleting server %s', server_name)
                    self.deployment_helper.delete_server(self.server_display_name)
                    self.log.info('Deleted server successful for %s', server_name)
                    self.commcell.refresh()
            else:
                self.log.info('No server exists with hostname %s', self.tcinputs['ServerHostName'])
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    # changed here
    # we are expecting only one hostname
    # but used for hostname as well since sub function wants list
    def _pamper_input(self, given_input):
        """convert the given input to a list
            input is expected to comma separated
            Returns:
                    list
        """
        list_input = given_input.split(",")
        return list_input

    @test_step
    def install_client(self):
        """Add a new server"""

        self.deployment_helper.add_server_new_windows_or_unix_server(
            hostname=self._pamper_input(self.tcinputs.get('ServerHostName')),
            username=self.tcinputs['ServerUsername'],
            password=self.tcinputs['ServerPassword'],
            os_type=self.tcinputs['ServerOSType'],
            packages=self._pamper_input(self.tcinputs.get('Packages'))
        )
        self.server_display_name = self.commcell.clients.get(self.tcinputs['ServerHostName']).display_name

    @test_step
    def create_storage(self):
        """To create a new disk storage"""

        self.storage_helper.add_disk_storage(
            self.disk_storage_name,
            self.server_display_name,
            self.tcinputs['BackupLocation'],
            deduplication_db_location=self.ddb_location)

    @test_step
    def check_ransomware_protection(self):
        """ Validates if ransomware protection is enabled on the MA"""

        self.log.info("Validate if ransomware protection is enabled on the newly installed MA")
        # Post discussion decided to expect the client Name to be same as client ServerHostName
        clnt_id = self.commcell.clients.get(self.tcinputs['ServerHostName']).client_id
        if self.mm_helper.ransomware_protection_status(clnt_id):
            self.log.info('Ransomware protection is enabled on the MA')
        else:
            self.log.error("Ransomware protection is not working on the MA")
            raise CVTestStepFailure('ransomware protection is not'
                                    ' enabled on the newly installed MA')

    @test_step
    def check_fs_configure_state(self):
        """ Validates File System Configure state based on the installed packages"""

        if 'File System' in str(self.tcinputs['Packages']):
            # To validate if file system iDA is in configured state
            self.log.info("Validate if file system iDA is in configured state")
            if self._filesystem_license_usage(self.tcinputs["ServerHostName"]):
                self.log.info('File System iDA is in configured state')
            else:
                raise CVTestStepFailure(f'File System iDA is in de-configured state when file system '
                                        'package is installed')
        elif 'File System' not in str(self.tcinputs['Packages']) and 'Media Agent' in str(self.tcinputs['Packages']):
            # To validate if file system iDA is in de-configured state
            self.log.info("Validate if File System iDA is in de-configured state")
            if self._filesystem_license_usage(self.tcinputs["ServerHostName"]):
                raise CVTestStepFailure(f'File System iDA is in configured state when only Media Agent '
                                        'package is installed')
            self.log.info('File System iDA is in de-configured state')

    @test_step
    def check_ddb_subclient(self):
        """To validate if system created a 'DDBBackup' subclient when disk storage is created"""

        if self._ddb_subclient_validation(self.tcinputs["ServerHostName"]):
            self.log.info('System Successfully created DDBBackup subclient for %s', self.server_display_name)
        else:
            raise CVTestStepFailure(f"There is no subclient named DDBBackup for {self.server_display_name}")

    @test_step
    def check_dedupe_flags(self):
        """To validate if default dedupe flags are set or not on storage created"""

        dedupe_flag, extended_flag = map(int, self._get_storage_dedupe_flags(self.disk_storage_name))
        if dedupe_flag == 546504722 and extended_flag == 14:
            self.log.info('All the default dedupe flags are seton disk storage: %s', self.disk_storage_name)
            self.log.info("Validation for default dedupe flags on disk storage: %s was successful",
                          self.disk_storage_name)
        else:
            self._get_storage_flags_not_set(dedupe_flag, extended_flag)
            self._get_storage_flags_set(dedupe_flag, extended_flag)
            raise CVTestStepFailure(f'The default dedupe flags are incorrectly set on disk storage: '
                                    f'{self.disk_storage_name}')

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.init_tc()
        self.deployment_helper = DeploymentHelper(self, self.admin_console)
        self.storage_helper = StorageMain(self.admin_console)
        self.media_agents = MediaAgents(self.admin_console)
        time_stamp = OptionsSelector(self.commcell).get_custom_str()
        self.disk_storage_name = str(self.id) + '_Disk_' + time_stamp
        self.ddb_location = self.tcinputs['DDBLocation'] + time_stamp
        self.mm_helper = mahelper.MMHelper(self)

    def run(self):
        """Main function for test case execution"""

        try:
            self.cleanup()
            self.install_client()
            self.create_storage()
            self.check_ransomware_protection()
            self.check_fs_configure_state()
            self.check_ddb_subclient()
            self.check_dedupe_flags()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        else:
            self.cleanup()
        finally:
            Browser.close_silently(self.browser)
