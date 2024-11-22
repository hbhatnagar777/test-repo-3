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

    _cleanup()      --  To perform cleanup operation before setting the environment and after testcase completion

    create_disk_storage()   --      Creates a new disk storage

    validate_storage_creation()     -- Validates if the disk is crated or not

    setup()         --  setup function of this test case

    run()           --  run function of this test case

User has the following permissions :
        Media Agent Management on MA entity. But Disabled the parameter
            [Control Panel > Media Management, and on the Service Configuration tab, set Provide user with Media Agent
             management rights additional capabilities for libraries, data paths, and storage policies to 0]
        View on CommCell Entity Regarding the user access
        Execute and edit on Workflow Entity

Sample Input:
"63862": {
                    "AgentName": "File System",
                    "ClientName": "client_name",
                    "MediaAgent1": "media_agent_1"
                }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.mp1_id = None
        self.mmhelper = None
        self.name = "CC - Disk Storage-with user having not enough permission"
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.client_machine = None
        self.ma1_machine = None
        self.storage_name = None
        self.backup_location = None
        self.ddb_location = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent1": None
        }

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
            self.log.info('Check for storage %s', self.storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s ', self.storage_name)
                self.storage_helper.delete_disk_storage(self.storage_name)
            self.commcell.storage_pools.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    @test_step
    def create_disk_storage(self):
        """Creates a new disk storage"""
        self.log.info("Adding a new disk storage: %s", self.storage_name)
        ma1_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        self.storage_helper.add_disk_storage(
            self.storage_name,
            ma1_name,
            self.backup_location,
            deduplication_db_location=self.ddb_location)
        self.log.info('Adding of disk storage: %s attempted', self.storage_name)

    @test_step
    def validate_storage_creation(self):
        """Validates if the disk is being created or not"""

        storage_list = self.storage_helper.list_disk_storage()

        if self.storage_name in storage_list:
            self.cleanup()
            raise Exception('Disk storage is created without enough permissions')
        else:
            self.log.info('Disk storage is not created as expected')

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.init_tc()
        self.storage_helper = StorageMain(self.admin_console)
        self.mmhelper = MMHelper(self)
        options_selector = OptionsSelector(self.commcell)
        self.ma1_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.storage_name = '%s_Dedupe_Disk' % str(self.id)

        # To select drive with space available in MA1 machine
        self.log.info('Selecting drive in the MA1 machine based on space available')
        ma1_drive = options_selector.get_drive(self.ma1_machine, size=30 * 1024)
        if ma1_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma1_drive)
        self.backup_location = self.ma1_machine.join_path(ma1_drive, 'Automation', str(self.id), 'MP')
        self.ddb_location = self.ma1_machine.join_path(ma1_drive, 'Automation', str(self.id), 'DDB')

    def run(self):
        """Main function for test case execution"""

        try:
            self.cleanup()
            self.create_disk_storage()
            self.validate_storage_creation()
        except Exception as exp:
            if "doesn't have [Create Storage Policy] permission" in str(exp):
                self.log.info('Adding of cloud storage denied as expected')
                self.validate_storage_creation()
            else:
                handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
