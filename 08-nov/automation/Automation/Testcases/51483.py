# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Test Case to check basic acceptance of IntelliSnap operations

steps:
Creates a plan, add-edit arrays, associate server and creates subclient
run snapbackup and restore operations
disassociate array, delete array, delete subclient and delete plan

Pre-requisite:
Storage pool should be configured

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import time
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from Web.AdminConsole.Helper.fs_helper import FSHelper
from Web.AdminConsole.Helper.array_helper import ArrayHelper
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.AdminConsolePages.StoragePools import StoragePools


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of IntelliSnap FS backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Snap FS in Admin Console"
        self.product = self.products_list.CTE
        self.feature = self.features_list.SNAPBACKUP
        self.tcinputs = {
            'MediaAgent': None,
            'StoragePath': None,
            'StoragePoolName': None,
            'PlanName': None,
            'ArrayVendor': None,
            'ArrayName': None,
            'ArrayUser': None,
            'ArrayPassword': None,
            'ControlHost': None,
            'NewSubclientName': None,
            'SubclientContent': None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            driver = browser.driver

            self.log.info("Creating the login object")
            login_obj = LoginMain(driver, self.csdb)

            login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                            self.inputJSONnode['commcell']['commcellPassword']
                           )
            self.log.info("Login completed successfully. Will continue with snap plan creation")

            # Creating a new storage pool
            pool_obj = StoragePools(driver)
            pool_obj.navigate_to_storage_pools()
            partition_settings = {}
            partition_settings[self.tcinputs['MediaAgent']] = [
                self.tcinputs['StoragePath'] + "\\" + str(
                    int(time.time()))]

            ma_machine = Machine(self.tcinputs['MediaAgent'], self.commcell)
            if ma_machine.check_directory_exists(self.tcinputs['StoragePath']):
                ma_machine.remove_directory(self.tcinputs['StoragePath'])
            pool_obj.add_disk_cloud_storage_pool(self.tcinputs['StoragePoolName'],
                                                 "New storage",
                                                 media=self.tcinputs['MediaAgent'],
                                                 path_type="Local path",
                                                 path=self.tcinputs['StoragePath'],
                                                 partition_settings=partition_settings)

            # Creating a new Plan
            plan_obj = PlanMain(driver)
            plan_obj.plan_name = {'server_plan': self.tcinputs['PlanName']}
            plan_obj.storage_name = self.tcinputs['StoragePoolName']
            plan_obj.backup_day = dict.fromkeys(['1', '2', '3', '4', '5', '6'], 1)
            plan_obj.backup_duration = dict.fromkeys(['2', '3', '4', '5', '6', '7', '8', '9',
                                                      '10', '11', '12', '13', '14', '15', '16',
                                                      '17', '18', '19', '20', '21', '22', '23',
                                                      '24', '25'], 1)
            plan_obj.add_plan()

            # Creating a new array
            array_obj = ArrayHelper(driver, self.csdb)
            array_obj.array_vendor = self.tcinputs['ArrayVendor']
            array_obj.array_name = self.tcinputs['ArrayName']
            array_obj.array_user = self.tcinputs['ArrayUser']
            array_obj.array_password = self.tcinputs['ArrayPassword']
            array_obj.control_host = self.tcinputs['ControlHost']
            array_obj.client_name = self.tcinputs['ClientName']
            array_obj.array_controllers = self.tcinputs['ClientName']
            array_obj.add_array()

            # Create FS subclient and run backup
            fs_obj = FSHelper(driver, self.csdb)
            fs_obj.client_name = self.tcinputs['ClientName']
            fs_obj.subclient_name = self.tcinputs['NewSubclientName']
            fs_obj.subclient_content = self.tcinputs['SubclientContent']
            fs_obj.plan_name = self.tcinputs['PlanName']
            fs_obj.snap_engine = self.tcinputs['ArrayVendor'] + " Snap"
            fs_obj.create_fs_subclient()
            fs_obj.enable_snap()

            #Run Backup And Restore
            fs_obj.fsbackup_now()
            fs_obj.fs_restore_all_inplace()

            array_obj.verify_snap()

            # Cleanup and Delete Test
            array_obj.delete_all_snap()
            fs_obj.delete_subclient()
            array_obj.delete_array()
            plan_obj.delete_plans()
            pool_obj.navigate_to_storage_pools()
            pool_obj.action_delete(self.tcinputs['StoragePoolName'])

            browser.close()

        except Exception as exp:
            Browser.close_silently(browser)
            handle_testcase_exception(self, exp)
