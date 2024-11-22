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

    _get_mountpath_id() --  To get first mountpath id on specified library

    _get_librarytype_id() -- Get librarytype id of specified library

    _validate_storage_type() -- Check if storage type of provided library is accurate

    _validate_storage_deletion() -- Verify provided library is deleted

    _cleanup()      --  To perform cleanup operation before setting the environment and after testcase completion

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample Input:
"62569": {
            "ClientName": "Name of Client Machine",
            "AgentName": "File System",
            "MediaAgent1": "Name of MA machine1",
            "MediaAgent2": "Name of MA machine2"
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.mediaagentconstants import DEVICE_ACCESS_TYPES
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Admin Console - Basic Disk Storage creation and deletion Case"
        self.browser = None
        self.admin_console = None
        self.plan_helper = None
        self.storage_helper = None
        self.mmhelper = None
        self.common_util = None
        self.plan_name = None
        self.ma1_machine = None
        self.ma2_machine = None
        self.nondedupe_storage_name = None
        self.nondedupe_backup_location = None
        self.nondedupe_backup_location2 = None
        self.dedupe_backup_location = None
        self.dedupe_storage_name = None
        self.ddb_location = None
        self.content_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent1": None,
            "MediaAgent2": None
        }

    def _get_mountpath_id(self, library_name):
        """
        Get a first Mountpath id from Library Name
            Args:
                library_name (str)  --  Library Name

            Returns:
                First Mountpath id for the given Library name
        """

        query = """ SELECT	MM.MountPathId
                    FROM	MMMountPath MM
                    JOIN    MMLibrary ML
                            ON  ML.LibraryId = MM.LibraryId
                    WHERE	ML.AliasName = '{0}'
                    ORDER BY    MM.MountPathId DESC""".format(library_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return cur[0]
        self.log.error("No entries present")
        raise Exception("Invalid Library Name.")

    def _get_librarytype_id(self, library_name):
        """
        Get library type id
        :param library_name (str): name of the library to check
        :return: Librarytype id of provided library
        """

        query = """ SELECT  ML.LibraryTypeId
                    FROM    MMLibrary ML
                    WHERE   ML.ALiasName = '{0}' """.format(library_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: LibraryTypeId is %s", cur[0])
        if cur[0] != '':
            return cur[0]
        self.log.error("No entries present")
        raise Exception("Invalid Library Name.")

    def _get_library_id(self, storage_pool_name):
        """
        Get Library id associated to provided storage pool name
        :param storage_pool_name (str): name of storage pool to check
        :return: Library id associated to storage pool
        """
        query = """ SELECT DISTINCT MP.LibraryId
                            FROM MMDrivePool DRP WITH (NOLOCK), MMDataPath DAP WITH (NOLOCK),
                            MMMasterPool MP WITH (NOLOCK), archGroup AG WITH (NOLOCK)
                            WHERE DAP.CopyId = AG.defaultCopy
                            AND DAP.DrivePoolId = DRP.DrivePoolId
                            AND DRP.MasterPoolId = MP.MasterPoolId
                            AND AG.name = '{0}' """.format(storage_pool_name)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        if cur[0] != '':
            return cur[0]
        self.log.error("Drive pool library does not exist")
        raise Exception("Invalid storage pool name")

    def _validate_storage_type(self, library_name):
        """
        Validate Library Type id is accurate
        :param library_name (str): name of the library to check
        """
        libtype_id = self._get_librarytype_id(library_name)
        if libtype_id != '3':
            self.log.error("Library type set is not accurate")
            raise Exception("Inaccurate Library Type id")
        else:
            self.log.info("Validated storage type as Magnetic Storage")

    def _validate_storage_deletion(self, library_id):
        """
        Check MMLibrary for provided library id and verify entry is removed
        :param library_name (str): name of the library to check
        """
        query = """ SELECT  ML.AliasName
                            FROM    MMLibrary ML
                            WHERE   ML.Libraryid = {0} """.format(library_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        if cur[0] != '':
            self.log.error("Library %s entry was not removed from MMLibrary post deletion", cur[0])
            raise Exception("Entry present, Library did not delete successfully")
        else:
            self.log.info("Validated Library deletion successfully")

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
            self.log.info('Check for nondedupe storage %s', self.nondedupe_storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.nondedupe_storage_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s ', self.nondedupe_storage_name)
                self.commcell.storage_pools.delete(self.nondedupe_storage_name)

            self.log.info('Check for dedupe storage %s', self.dedupe_storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.dedupe_storage_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s ', self.dedupe_storage_name)
                self.commcell.storage_pools.delete(self.dedupe_storage_name)

            self.commcell.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.init_tc()
        self.plan_helper = PlanMain(self.admin_console)
        self.storage_helper = StorageMain(self.admin_console)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        options_selector = OptionsSelector(self.commcell)
        time_stamp = options_selector.get_custom_str()
        self.ma1_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.ma2_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent2'])
        self.nondedupe_storage_name = '%s_NonDedupe_Disk' % str(self.id)
        self.dedupe_storage_name = '%s_Dedupe_Disk' % str(self.id)

        # To select drive with space available in MA1 machine
        self.log.info('Selecting drive in the MA1 machine based on space available')
        ma1_drive = options_selector.get_drive(self.ma1_machine, size=30 * 1024)
        if ma1_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma1_drive)
        self.nondedupe_backup_location = self.ma1_machine.join_path(ma1_drive, 'Automation', str(self.id), 'MP')

        # To select drive with space available in MA2 machine
        self.log.info('Selecting drive in the MA2 machine based on space available')
        ma2_drive = options_selector.get_drive(self.ma2_machine, size=30 * 1024)
        if ma2_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma2_drive)
        self.dedupe_backup_location = self.ma2_machine.join_path(ma2_drive, 'Automation', str(self.id), 'MP')
        self.nondedupe_backup_location2 = self.ma2_machine.join_path(ma2_drive, 'Automation', str(self.id), 'MP_ND')
        self.ddb_location = self.ma2_machine.join_path(ma2_drive, 'Automation', str(self.id), 'DDB_%s' % time_stamp)

    @test_step
    def create_storage(self):
        """Create a new disk storages and validate"""

        ma1_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        self.log.info("Adding a new disk for primary nondedupe storage: %s", self.nondedupe_storage_name)
        self.storage_helper.add_disk_storage(
            self.nondedupe_storage_name,
            ma1_name,
            self.nondedupe_backup_location)
        self.log.info('successfully created disk storage: %s', self.nondedupe_storage_name)
        self.log.info('Validating Storage Type: %s', self.nondedupe_storage_name)
        self._validate_storage_type(self.nondedupe_storage_name)

        ma2_name = self.commcell.clients.get(self.tcinputs['MediaAgent2']).display_name
        self.log.info("Adding a new disk for secondary dedupe storage: %s", self.dedupe_storage_name)
        self.storage_helper.add_disk_storage(
            self.dedupe_storage_name,
            ma2_name,
            self.dedupe_backup_location,
            deduplication_db_location=self.ddb_location)
        self.log.info('successfully created disk storage: %s', self.dedupe_storage_name)
        self.log.info('Validating Storage Type: %s', self.dedupe_storage_name)
        self._validate_storage_type(self.dedupe_storage_name)

    @test_step
    def check_mp_share(self):
        """ Add Mountpath with another MA and check sharing of Mountpath with other MA uses Dataserver IP"""

        # Get first mountpathId on the new primary nondedupe disk storage
        ma1_mountpath_id = self._get_mountpath_id(self.nondedupe_storage_name)

        # To add backup location to primary non-dedupe disk storage
        ma2_name = self.commcell.clients.get(self.tcinputs['MediaAgent2']).display_name
        self.storage_helper.add_disk_backup_location(self.nondedupe_storage_name,
                                                     ma2_name,
                                                     self.nondedupe_backup_location2)

        # Get second mountpathId on the new primary nondedupe disk storage
        ma2_mountpath_id = self._get_mountpath_id(self.nondedupe_storage_name)

        # To validate whether MA2 access MA1’s mountpath by using dataserver IP and also vice-versa
        ma2_access_type = self.mmhelper.get_device_access_type(ma1_mountpath_id, self.tcinputs['MediaAgent2'])
        ma1_access_type = self.mmhelper.get_device_access_type(ma2_mountpath_id, self.tcinputs['MediaAgent1'])

        if (ma1_access_type & DEVICE_ACCESS_TYPES['DATASERVER_IP'] and
                ma2_access_type & DEVICE_ACCESS_TYPES['DATASERVER_IP']):
            self.log.info("Validation for mountpath access type was successful")
        else:
            self.log.error("Validation for mountpath access type has failed")
            raise Exception("Validation for mountpath access type has failed")

    @test_step
    def delete_storage(self):
        """Delete storage and validate deletion"""
        try:
            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.nondedupe_storage_name)
            lib_id1 = self._get_library_id(self.nondedupe_storage_name)
            if self.nondedupe_storage_name in self.storage_helper.list_disk_storage():
                self.log.info('Deleting Nondedupe storage %s', self.nondedupe_storage_name)
                self.storage_helper.delete_disk_storage(self.nondedupe_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.nondedupe_storage_name)
            self.commcell.refresh()
            self._validate_storage_deletion(lib_id1)

            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.dedupe_storage_name)
            lib_id2 = self._get_library_id(self.dedupe_storage_name)
            if self.dedupe_storage_name in self.storage_helper.list_disk_storage():
                self.log.info('Deleting Dedupe storage %s', self.dedupe_storage_name)
                self.storage_helper.delete_disk_storage(self.dedupe_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.dedupe_storage_name)
            self.commcell.refresh()
            self._validate_storage_deletion(lib_id2)
        except Exception as exp:
            raise CVTestStepFailure(f'Deletion of Storage failed with error : {exp}')


    def run(self):
        """Main function for test case execution"""

        try:
            self.cleanup()
            self.create_storage()
            self.check_mp_share()
            self.delete_storage()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
