# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" This case aims to validate creation of disk storage, for smoke test via CC

TestCase: Class for executing this test case

    __init__()      --  Initializes test case class objects

    init_tc()       -- Initial configuration for the test case

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    create_disk_storage() -- creates a new disk storage

    validate_disk_storage_deletion() -- validates the deletion of disk storage

    validate_disk_storage_creation() -- validates the creation of disk storage

    cleanup()       -- Cleans Up the Entities created in the TC

Sample Input JSON:
    {
      "ClientName": Name of the Client (str),
      "MediaAgent": Name of the mediaAgent (str),
      "disk_dedup_path" : Disk Ddb location for unix MA
                        (required - if the MA provided is Unix/Linux, else optional)

      *****In case of Unix/Linux MA, provide LVM enabled dedup paths*****
    }

Steps:
    1) Add new deduplication enabled disk storage via CC UI.
    2) Add new non-dedupe disk storage via CC
    3) Delete both storages

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'MM Smoke Test - CC - Disk Storage Creation'
        self.mm_helper = None
        self.disk_storage_name1 = None
        self.disk_storage_name2 = None
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.client_machine = None
        self.ma_machine = None
        self.path = None
        self.disk_ddb_location1 = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent": None
        }
        self.res_string = ""
        self.dedup_provided = False
        self.disk_backup_location1 = None
        self.disk_backup_location2 = None

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
        """Setup function of this test case"""

        self.init_tc()
        self.disk_storage_name1 = f"Disk1-{self.id}1"
        self.disk_storage_name2 = f"Disk2-{self.id}2"
        self.mm_helper = MMHelper(self)
        self.storage_helper = StorageMain(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])

        self.log.info('Selecting drive in the MA machine')
        ma_drive = options_selector.get_drive(self.ma_machine)
        if ma_drive is None:
            Browser.close_silently(self.browser)
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)
        self.path = self.ma_machine.join_path(ma_drive, f"Smoke_Test_{self.id}")
        self.disk_backup_location1 = self.ma_machine.join_path(self.path, 'Disk_backup_loc1')
        self.disk_backup_location2 = self.ma_machine.join_path(self.path, 'Disk_backup_loc2')
        self.log.info('Backup location for dedupe disk: %s', self.disk_backup_location1)
        self.log.info('Backup location for non-dedupe disk: %s', self.disk_backup_location2)

        if self.tcinputs.get('disk_dedup_path'):
            self.dedup_provided = True

        if "unix" in self.ma_machine.os_info.lower():
            if self.dedup_provided:
                self.log.info('Unix/Linux MA provided, assigning user defined dedup locations')
                self.disk_ddb_location1 = self.tcinputs['disk_dedup_path']
            else:
                self.log.error(
                    f"LVM enabled dedup path must be an input for Unix MA {self.tcinputs['MediaAgent']}")
                Browser.close_silently(self.browser)
                raise Exception(
                    f"Please provide LVM enabled dedup path as input for Unix MA {self.tcinputs['MediaAgent']}")
        else:
            if self.dedup_provided:
                self.log.info('Windows MA provided, assigning user defined dedup location')
                self.disk_ddb_location1 = self.tcinputs['disk_dedup_path']
            else:
                self.log.info('Windows MA provided, creating dedup locations')
                self.disk_ddb_location1 = self.ma_machine.join_path(self.path, 'Disk_DDB1')

        self.log.info('Ddb location for Disk: %s', self.disk_ddb_location1)

    def cleanup(self):
        """Cleans Up the Entities created in the TC"""

        try:
            self.log.info("****************************** Cleanup Started ******************************")

            if self.storage_helper.has_disk_storage(self.disk_storage_name1):
                self.log.info(f"Deleting disk storage {self.disk_storage_name1}")
                self.storage_helper.delete_disk_storage(self.disk_storage_name1)
                self.validate_disk_storage_deletion(name=self.disk_storage_name1)

            if self.storage_helper.has_disk_storage(self.disk_storage_name2):
                self.log.info(f"Deleting disk storage {self.disk_storage_name2}")
                self.storage_helper.delete_disk_storage(self.disk_storage_name2)
                self.validate_disk_storage_deletion(name=self.disk_storage_name2)
            self.log.info('****************************** Cleanup Completed ******************************')

        except Exception as exe:
            self.res_string += f'Error in Cleanup Reason: {exe} \n'
            self.status = constants.FAILED
            self.log.error(f'Error in Cleanup Reason: {exe}')

    def create_disk_storage(self, storage_name, backup_location, dedup_location=None):
        """Creates a new disk storage

            Args:
                storage_name: name of the storage

                backup_location: backup location for the storage

                dedup_location: ddb path (required for dedupe storage only)

        """

        try:
            self.log.info(f'Creating disk storage {storage_name}')
            ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent']).display_name
            self.storage_helper.add_disk_storage(disk_storage_name=storage_name,
                                                 media_agent=ma_name,
                                                 backup_location=backup_location,
                                                 deduplication_db_location=dedup_location)
            self.validate_disk_storage_creation(name=storage_name)

        except Exception as exp:
            self.res_string += f'Error in creating disk storage: {exp} \n'
            self.status = constants.FAILED

    def validate_disk_storage_deletion(self, name):
        """Validates if storage is deleted or not

            Args:
                name - name of the storage whose deletion needs to be validated

        """

        try:
            exist = self.storage_helper.has_disk_storage(name)
            if not exist:
                self.log.info(f'Disk storage {name} does not exist on CC')
            else:
                raise Exception(f'Disk storage {name} is not deleted, visible on CC')

        except Exception as exp:
            self.res_string += f'Error in validating deletion of disk storage: {exp} \n'
            self.status = constants.FAILED

    def validate_disk_storage_creation(self, name):
        """Validates if storage is created or not

            Args:
                name - name of the storage whose creation needs to be validated

        """

        try:
            exist = self.storage_helper.has_disk_storage(name)
            if exist:
                self.log.info(f'Created disk storage {name} is being shown on web page')
            else:
                raise Exception(f'Created disk storage {name} is not displayed on web page')

        except Exception as exp:
            self.res_string += f'Error in validating creation of disk storage: {exp} \n'
            self.status = constants.FAILED

    def run(self):
        """Run Function of this case"""

        try:
            self.cleanup()
            self.log.info("****Creating dedupe disk storage****")
            self.create_disk_storage(self.disk_storage_name1, self.disk_backup_location1, self.disk_ddb_location1)
            self.log.info("****Creating non dedupe disk storage****")
            self.create_disk_storage(self.disk_storage_name2, self.disk_backup_location2)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            if not self.res_string:
                self.res_string = 'Success'
            self.log.info(f'Result of this TestCase: {self.res_string}')
            Browser.close_silently(self.browser)
