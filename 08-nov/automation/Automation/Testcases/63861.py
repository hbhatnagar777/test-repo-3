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

    setup()         --  setup function of this test case

    create_cloud_storage()  -- To create a new cloud storage

    validate_storage_creation() -- Validates if the cloud storage is created

    run()           --  run function of this test case

User has the following permissions :
        Media Agent Management on MA entity. But Disabled the parameter
            [Control Panel > Media Management, and on the Service Configuration tab, set Provide user with Media Agent
             management rights additional capabilities for libraries, data paths, and storage policies to 0]
        View on CommCell Entity Regarding the user access
        Execute and edit on Workflow Entity

Sample Input:
"63861": {
                        "AgentName": "File System",
                        "ClientName": "client_name",
                        "CloudContainer1": "cloud_container_1",
                        "CloudServerName": "cloud_server_name",
                        "CloudServerType": "cloud_server_type",
                        "MediaAgent1": "media_agent_1",
                        "SavedCredential": "saved_credential",
                        }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "CC-Cloud Storage BYOS - Using Access Key Auth- User with not enough access"
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.client_machine = None
        self.ma1_machine = None
        self.content_path = None
        self.storage_name = None
        self.backup_location = None
        self.mp1_id = None
        self.ddb_location = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent1": None,
            "CloudContainer1": None,
            "CloudServerName": None,
            "CloudServerType": None,
            "SavedCredential": None,
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

    def cleanup(self):
        """ To perform cleanup operation """

        try:
            self.log.info('Check for storage %s', self.storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.storage_name):
                # To delete cloud storage if exists
                self.log.info('Deletes storage %s', self.storage_name)
                self.storage_helper.delete_cloud_storage(self.storage_name)
            self.commcell.storage_pools.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.init_tc()
        self.storage_helper = StorageMain(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.storage_name = '%s_Cloud' % str(self.id)

        # To select drive with space available in MA1 machine
        self.log.info('Selecting drive in the MA machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=30 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)
        self.ddb_location = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

    @test_step
    def create_cloud_storage(self):
        """ To create a new cloud storage"""
        self.log.info("Adding a new cloud storage: %s", self.storage_name)
        ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        self.storage_helper.add_cloud_storage(self.storage_name, ma_name,
                                              self.tcinputs['CloudServerType'],
                                              self.tcinputs['CloudServerName'],
                                              self.tcinputs['CloudContainer1'],
                                              storage_class=self.tcinputs.get('CloudStorageClass'),
                                              saved_credential_name=self.tcinputs['SavedCredential'],
                                              deduplication_db_location=self.ddb_location,
                                              region=self.tcinputs['CloudRegion'],
                                              auth_type='Access key and Account name')
        self.log.info('Adding of cloud storage: %s attempted', self.storage_name)

    @test_step
    def validate_storage_creation(self):
        """Validates if the cloud storage is created or not"""

        storage_list = self.storage_helper.list_cloud_storage()
        if self.storage_name in storage_list:
            self.cleanup()
            raise Exception('Cloud storage is created without enough permissions')
        else:
            self.log.info('Cloud storage is not created as expected')

    def run(self):
        try:
            self.cleanup()
            self.create_cloud_storage()
            self.validate_storage_creation()
        except Exception as exp:
            if "doesn't have [Create Storage Policy] permission" in str(exp):
                self.log.info('Adding of cloud storage denied as expected')
                self.validate_storage_creation()
            else:
                handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
