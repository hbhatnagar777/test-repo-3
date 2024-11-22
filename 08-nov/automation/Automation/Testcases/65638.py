# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    create_storage() -- Creates a backup location with two mountpaths on separate media agents

    validate_storage_pool_created() -- Validates whether storage pool created is listed

    validate_storage_pool_locations() -- Validates whether both mountpaths added to the library are listed

    validate_location_access() -- Validates whether both media agents can access both paths

    validate_mountpaths_db() -- Database validation for whether both mountpaths created

    validate_mountpath_location_db() -- Database validation for whether both mountpaths exist on separate media agents

    validate_num_of_lib_in_pool_db() -- Database validation for whether only one library got created as a part of pool creation

    validate_access_through_network_db() -- Validate whether both media agents can access mountpath through network

    validate_attributes_writers_db() -- Database validation for default attributes and max concurrent writers

    negative_validation() -- Validates whether created mount path and library getting deleted in case of failure

    get_invalid_path() -- To obtain drive that does not exist on MA2


    sample input :
    "65638": {
                  "MediaAgent1": "sample_agent_1",
                  "MediaAgent2": "sample_agent_2",
              }
"""

import string
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.dedupehelper = None
        self.__props = None
        self.name = "Disk Storage creation with multiple backup location"
        self.tcinputs = {
            "MediaAgent1": None,
            "MediaAgent2": None
        }
        self.storage_name = None
        self.path1 = None
        self.path2 = None
        self.invalid_path = None
        self.browser = None
        self.navigator = None
        self.disk_storage = None
        self.admin_console = None
        self.mmhelper = None
        self.storage_helper = None
        self.table = None
        self.dropdown = None
        self.option_selector = None
        self.ma1_machine = None
        self.ma2_machine = None
        self.cs_os = None
        self.options_selector = None
        self.unique_storage_name = None

    @test_step
    def create_storage(self, storage_name, backup_location_details):
        """
        Creates a backup location with two mountpaths on separate media agents

        Args :

            storage_name(str) : Name of the disk storage to be created

            backup_location_details (list): List of dictionaries containing backup location details to add multiple backup
                                            locations.
        """
        try:
            self.storage_helper.add_disk_storage_with_multiple_locations(storage_name,
                                                                         backup_location_details)
        except Exception:
            raise Exception("Unable to create a disk storage")

    @test_step
    def validate_storage_pool_created(self, storage_name):
        """Validates whether storage pool created is listed"""
        disk_storages = self.storage_helper.list_disk_storage()
        if storage_name in disk_storages:
            self.log.info("Storage pool is created")
        else:
            raise Exception("Storage pool is not created")

    @test_step
    def validate_storage_pool_locations(self):
        """Validates whether both mountpaths added to the library are listed"""
        storage_locations = self.storage_helper.list_disk_backup_locations(self.storage_name)
        ma_path_1 = f"[{self.tcinputs['MediaAgent1']}] {self.path1}"
        ma_path_2 = f"[{self.tcinputs['MediaAgent2']}] {self.path2}"
        if len(storage_locations) == 2 and ma_path_1 in storage_locations and ma_path_2 in storage_locations:
            self.log.info("Both locations added")
        else:
            raise Exception("Both locations not added")

    @test_step
    def validate_location_access(self):
        """Validates whether both media agents can access both paths"""
        media_agents_path1 = self.storage_helper.list_disk_media_agent(self.storage_name,
                                                                       self.path1)
        if (len(media_agents_path1) == 2 and
                self.tcinputs["MediaAgent1"] in media_agents_path1 and
                self.tcinputs["MediaAgent2"] in media_agents_path1):
            self.log.info("Both media agents have access to path1")
        else:
            raise Exception("Both media agents have access to path1")

        media_agents_path2 = self.storage_helper.list_disk_media_agent(self.storage_name,
                                                                       self.path2)
        if (len(media_agents_path2) == 2 and
                self.tcinputs["MediaAgent1"] in media_agents_path2 and
                self.tcinputs["MediaAgent2"] in media_agents_path2):
            self.log.info("Both media agents have access to path2")
        else:
            raise Exception("Both media agents have access to path2")

    @test_step
    def validate_mountpaths_db(self, global_storage_policy_id):
        """Database validation for whether both mountpaths created"""
        query = """SELECT COUNT(DISTINCT MP.MountPathId) FROM MMMountPath MP
                   JOIN MMDrivePool DP ON MP.MasterPoolId = DP.MasterPoolId
                   JOIN MMDataPath dta_pth ON dta_pth.DrivePoolId = DP.DrivePoolId
                   JOIN archGroupCopy agc ON agc.id = dta_pth.CopyId
                   WHERE agc.archGroupId = '{0}'""".format(global_storage_policy_id)
        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row(False)
        self.log.info("Query result : %s", query_result)
        if query_result[0] == '2':
            self.log.info("library has two mountpaths")
        else:
            raise Exception("Two mountpaths not added to database")

    @test_step
    def validate_mountpath_location_db(self, global_storage_policy_id):
        """Database validation for whether both mountpaths exist on separate media agents"""
        query = """SELECT COUNT(DISTINCT device.DeviceId)  FROM MMMountPath as MP
                   JOIN MMMountPathToStorageDevice MPSD ON MP.MountPathId = MPSD.MountPathId
                   JOIN MMDevice device ON device.DeviceId = MPSD.DeviceId
                   JOIN MMDrivePool as DP ON MP.MasterPoolId = DP.MasterPoolId
                   JOIN MMDataPath dta_pth ON dta_pth.DrivePoolId = DP.DrivePoolId
                   JOIN archGroupCopy agc ON agc.id = dta_pth.CopyId
                   WHERE agc.archGroupId = '{0}'""".format(global_storage_policy_id)
        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row(False)
        self.log.info("Query result : %s", query_result)
        if query_result[0] == '2':
            self.log.info("Mountpath present on two separate media agents")
        else:
            raise Exception("Two mountpaths not on separate media agents")

    @test_step
    def validate_num_of_lib_in_pool_db(self, global_storage_policy_id):
        """Database validation for whether only one library got created as a part of pool creation"""
        query = """SELECT COUNT(DISTINCT lib.LibraryID) FROM MMLibrary lib
                   JOIN MMMasterPool MP ON MP.LibraryId = lib.LibraryId
                   JOIN MMDrivePool DP ON DP.MasterPoolId = MP.MasterPoolId
                   JOIN MMDataPath dta_pth ON dta_pth.DrivePoolId = DP.DrivePoolId
                   JOIN archGroupCopy agc ON dta_pth.CopyId = agc.id
                   WHERE agc.archGroupId = '{0}'""".format(global_storage_policy_id)
        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row(False)
        self.log.info("Query result : %s", query_result)
        if query_result[0] == '1':
            self.log.info("Only one library got created as part of pool creation")
        else:
            raise Exception("More than one library got created as part of pool creation")

    @test_step
    def validate_attributes_writers_db(self, global_storage_policy_id):
        """Database validation for default attributes and max concurrent writers"""
        query = """SELECT COUNT(DISTINCT MP.MountPathId) FROM MMMountPath MP
                   JOIN MMDrivePool DP ON MP.MasterPoolId = DP.MasterPoolId
                   JOIN MMDataPath dta_pth ON dta_pth.DrivePoolId = DP.DrivePoolId
                   JOIN archGroupCopy agc ON agc.id = dta_pth.CopyId
                   WHERE agc.archGroupId = '{0}' AND MP.Attribute = '1160'
                   AND MP.MaxConcurrentWriters = '1000'""".format(global_storage_policy_id)
        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row(True)
        self.log.info("Query result : %s", query_result)

        if query_result[0] == '2':
            self.log.info("Attributes and writers set correctly")
        else:
            self.log.info("Attributes and writers not correctly set")

    @test_step
    def validate_access_through_network_db(self, global_storage_policy):
        """Validate whether both media agents can access mountpath through network"""
        query = """SELECT	DISTINCT MP.MountPathId,AC.displayName, MDC.DeviceAccessType
                    FROM	MMDeviceController MDC , MMMountPathToStorageDevice MPSD , 
                            MMMountPath MP , APP_Client AC , MMDrivePool DP, MMDataPath dta_pth, archGroupCopy agc
                    WHERE	MDC.DeviceId = MPSD.DeviceId
                            AND	MPSD.MountPathId = MP.MountPathId
                            AND MDC.ClientId = AC.id
					        AND DP.MasterPoolId = MP.MasterPoolId
							AND DP.DrivePoolId = dta_pth.DrivePoolId
							AND agc.id = dta_pth.CopyId
							AND agc.archGroupId = '{0}'
                    ORDER BY MDC.DeviceAccessType""".format(global_storage_policy)
        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_all_rows(True)
        self.log.info("Query result : %s", query_result)
        if len(query_result) != 4:
            raise Exception("Not auto shared")

        if query_result[2]['DeviceAccessType'] != '20' or query_result[3]['DeviceAccessType'] != '20':
            raise Exception("Not Auto shared")

        self.log.info("Both media agents have access to both paths")

    @test_step
    def negative_validation(self):
        """Validates whether created mount path and library are getting deleted in case of failure"""
        try:
            backup_location_details = [{'media_agent': self.tcinputs["MediaAgent1"],
                                        'backup_location': self.path1},
                                       {'media_agent': self.tcinputs["MediaAgent2"],
                                        'backup_location': self.invalid_path}]

            self.create_storage(self.unique_storage_name, backup_location_details)
            raise Exception("Disk storage added with invalid path")
        except Exception:
            self.log.info("as expected storage was not created ")

        # Validate whether storage pool created in UI
        try:
            self.validate_storage_pool_created(self.unique_storage_name)
            raise Exception("Storage pool created with invalid path")
        except Exception:
            self.log.info("Storage pool not created as excepted")

        self.validate_database_negative_case()
        self.validate_log_file()

    def validate_log_file(self):
        """Log file validation for whether created mountpath is getting deleted"""
        if self.commcell.commserv_client.os_info.lower().count('unix'):
            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 "AppMgrService.log",
                                                 """.*Adding\sMount Path \[[^\]]*\]\sfor\sDisk Library \[{0}\]\.\.\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                self.log.info("Mountpath for valid backup location not created")
            else:
                self.log.info("Mountpath creation for valid location started")

            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 "AppMgrService.log",
                                                 """.*Adding\sMount Path \[[^\]]*\]\sfor Disk Library \[{0}\] succeeded\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                self.log.info("Mountpath creation for valid backup location not succesfull")
            else:
                self.log.info("Mountpath for valid location created")

            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 "AppMgrService.log",
                                                 """.*Deleting\sMount Path \[[^\]]*\] from Disk Library \[{0}\]\.\.\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                raise Exception("Mountpath for valid backup location not deleted")
            else:
                self.log.info("Mountpath deletion started")

            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 "AppMgrService.log",
                                                 """.*Deleting\sMount Path \[[^\]]*\] from Disk Library \[{0}\] succeeded\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                raise Exception("Mountpath for valid backup location not deleted")
            else:
                self.log.info("Mountpath deletion succesfull")

        else:
            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 'CS_CVMMInst.log',
                                                 """.*Adding\sMount Path \[[^\]]*\]\sfor\sDisk Library \[{0}\]\.\.\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                self.log.info("Mountpath for valid backup location not created")
            else:
                self.log.info("Mountpath creation for valid location started")

            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 'CS_CVMMInst.log',
                                                 """.*Adding\sMount Path \[[^\]]*\]\sfor Disk Library \[{0}\] succeeded\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                self.log.info("Mountpath creation for valid backup location not succesfull")
            else:
                self.log.info("Mountpath for valid location created")

            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 'CS_CVMMInst.log',
                                                 """.*Deleting\sMount Path \[[^\]]*\] from Disk Library \[{0}\]\.\.\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                raise Exception("Mountpath for valid backup location not deleted")
            else:
                self.log.info("Mountpath deletion started")

            result = self.dedupehelper.parse_log(self.commcell.commserv_client.client_name,
                                                 'CS_CVMMInst.log',
                                                 """.*Deleting\sMount Path \[[^\]]*\] from Disk Library \[{0}\] succeeded\.""".format(
                                                     self.unique_storage_name),
                                                 jobid=None,
                                                 escape_regex=False,
                                                 single_file=True,
                                                 only_first_match=True
                                                 )
            self.log.info(result)
            if result[0] is None:
                raise Exception("Mountpath for valid backup location not deleted")
            else:
                self.log.info("Mountpath deletion succesfull")

    def validate_database_negative_case(self):
        """Validates that no library exists in database"""
        query = """ SELECT COUNT(DISTINCT LibraryId) FROM MMLibrary
                    WHERE AliasName = '{0}'""".format(self.unique_storage_name)
        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row(False)
        self.log.info("Query result : %s", query_result)

        if query_result[0] == '0':
            self.log.info("Library not created as expected")
        else:
            raise Exception("Library created with invalid path")

    def get_invalid_path(self):
        """To obtain drive that does not exist on MA2"""
        drives_dict = self.ma2_machine.get_storage_details()
        available_drives = set()
        for drive in drives_dict:
            if isinstance(drives_dict[drive], dict):
                available_drives.add(drive)

        for letter in string.ascii_uppercase:
            if letter not in available_drives:
                return letter + ":\\"

        raise Exception("Unable to find invalid drive")

    def get_global_storage_policy_id(self, storage_name):
        query = """SELECT ag.id from archGroup ag 
                   where ag.name = '{0}'""".format(storage_name)

        self.log.info("Query : %s", query)
        self.csdb.execute(query)
        query_result = self.csdb.fetch_one_row(False)
        self.log.info("Query result : %s", query_result)
        return query_result[0]

    @test_step
    def cleanup(self):
        """To perform cleanup operation"""
        try:
            self.log.info('Check for storage %s', self.storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s ', self.storage_name)
                self.storage_helper.delete_disk_storage(self.storage_name)
            self.commcell.storage_pools.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

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

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.init_tc()
        self.options_selector = OptionsSelector(self.commcell)
        self.storage_name = '%s_Disk_Storage' % str(self.id)
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.storage_helper = StorageMain(self.admin_console)
        self.ma1_machine = self.options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.ma2_machine = self.options_selector.get_machine_object(self.tcinputs['MediaAgent2'])
        ma1_drive = self.options_selector.get_drive(self.ma1_machine, size=30 * 1024)
        ma2_drive = self.options_selector.get_drive(self.ma2_machine, size=30 * 1024)
        if ma1_drive is None or ma2_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.path1 = self.ma1_machine.join_path(ma1_drive, 'Automation', str(self.id), 'MP1')
        self.path2 = self.ma2_machine.join_path(ma2_drive, 'Automation', str(self.id), 'MP2')
        self.invalid_path = self.get_invalid_path()
        self.unique_storage_name = self.storage_name + self.options_selector.get_custom_str()

    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.negative_validation()
            self.create_storage(self.storage_name,
                                [{'media_agent': self.tcinputs['MediaAgent1'], 'backup_location': self.path1},
                                 {'media_agent': self.tcinputs['MediaAgent2'], 'backup_location': self.path2}])
            global_storage_policy_id = self.get_global_storage_policy_id(self.storage_name)
            self.validate_storage_pool_created(self.storage_name)
            self.validate_storage_pool_locations()
            self.validate_location_access()
            self.validate_num_of_lib_in_pool_db(global_storage_policy_id)
            self.validate_mountpaths_db(global_storage_policy_id)
            self.validate_mountpath_location_db(global_storage_policy_id)
            self.validate_attributes_writers_db(global_storage_policy_id)
            self.validate_access_through_network_db(global_storage_policy_id)
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.cleanup()
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
