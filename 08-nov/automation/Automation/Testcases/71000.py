# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""AGP OCI Cloud Storage - CVOEM
The purpose of this testcase is to verify the functionality of the AGP OCI storage from Command Center

Pre-requisite -> License 100050 (OCI-Infrequent) should be applied and active to run this TC
*** This testcase is for MSP users only ***

Sample Input JSON:

        "71000": {
            "MediaAgentName": Name of the media agent (str),
            "ClientName": Name of the client (str),
            "location": Name of the region fo AGP-OCI storage (same as UI),
            "AgentName": Type of agent (str) (eg-"File System"),
            "ddb_path": DDB location on MA (mandatory for Unix MA)
        }

Steps:
    1) Create a Disk Storage Pool.
    2) Create a Dedup AGP OCI Cloud Storage. (Need 10050 license)
    3) Create a Plan with primary Storage as Disk Storage Pool. and secondary Storage as Dedup AGP OCI Cloud Storage.
    4) Run backup to primary storage
    5) Run Auxiliary Copy to AGP OCI Cloud Storage.
    6) Run Restore from secondary copy

TestCase: Class for executing this test case
TestCase:
    __init__()                  --  initialize TestCase class

    init_tc()                   --  initial configuration for the test case

    setup()                     --  setup function of this test case

    validate_storage_status()  -- Validates whether the storage is visible on CC or not

    configure_storages()       -- Create and validate storages required in the TC

    generate_backup_data()     -- Generates backup data on client

    configure_plan()           -- Create,associate and validate plan as per TC

    check_license()            -- Checks whether the specified license is active or not

    run_backup()               -- Run full backup on SC

    run_restore_from_sec_copy() -- Runs restore from secondary copy on plan

    run_aux_copy_job()          -- Run aux copy job to AGP storage (secondary backup destination)

    run()                       --  run function of this test case

    tear_down()                 --  tear down function of this test case

    disable_lock_on_entities()  -- Disables lock on storage pool and plan

    cleanup()                   -- Cleans up entities and data created in TC

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Helper.PlanHelper import PlanMain


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here """

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()

        self.name = "AGP OCI Cloud Storage CVOEM - CC"
        self.tcinputs = {
            "MediaAgentName": None,
            "ClientName": None,
            "location": None,
            "AgentName": None
        }
        self.storage_class = "Infrequent access"
        self.storage_type = "Oracle Cloud Infrastructure Object Storage"
        self.license_code = 100050
        self.backup_data_in_MB = 200
        self.num_of_files = 20

        self.common_utils = None
        self.browser = None
        self.admin_console = None
        self.mm_helper = None
        self.storage_helper = None
        self.plan_helper = None

        self.client_name = None
        self.media_agent_name = None
        self.ma_machine = None
        self.client_machine = None

        self.plan_name = None
        self.agp_storage_name = None
        self.disk_storage_name = None
        self.backup_set_name = None
        self.backup_set_obj = None
        self.subClient_name = None
        self.subclient_obj = None
        self.sec_copy_name = None

        self.content_path = None
        self.disk_backup_location = None
        self.restored_location = None
        self.path = None
        self.dedup_provided = False
        self.ddb_location = None

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
        self.media_agent_name = self.tcinputs['MediaAgentName']
        self.client_name = self.tcinputs["ClientName"]
        self.common_utils = CommonUtils(self)
        self.mm_helper = MMHelper(self)
        self.storage_helper = StorageMain(self.admin_console)
        self.plan_helper = PlanMain(self.admin_console)
        options_selector = OptionsSelector(self.commcell)

        self.ma_machine = options_selector.get_machine_object(self.media_agent_name)
        self.client_machine = options_selector.get_machine_object(self.client_name)
        self.disk_storage_name = f"Disk-{self.id}"
        self.agp_storage_name = f"Agp-{self.id}"
        self.plan_name = f"Plan-{self.id}"
        self.backup_set_name = f"BS-{self.id}"
        self.subClient_name = f"SC-{self.id}"
        self.sec_copy_name = f"sec-{self.agp_storage_name}"

        self.log.info('Selecting drive in the MA machine')
        ma_drive = options_selector.get_drive(self.ma_machine)
        if ma_drive is None:
            Browser.close_silently(self.browser)
            raise Exception("No free space for hosting mount paths")
        self.log.info('selected drive: %s', ma_drive)
        self.path = self.ma_machine.join_path(ma_drive, "Automation")
        self.disk_backup_location = self.ma_machine.join_path(self.path, self.id, "backup_loc")
        self.log.info('Backup location for dedupe disk: %s', self.disk_backup_location)

        self.log.info('Selecting drive in the client machine')
        client_drive = options_selector.get_drive(self.client_machine)
        if client_drive is None:
            Browser.close_silently(self.browser)
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)
        self.path = self.client_machine.join_path(client_drive, "Automation")
        self.content_path = self.client_machine.join_path(self.path, self.id, "backup_data")
        self.restored_location = self.client_machine.join_path(self.path, self.id, "restored_loc")
        self.log.info('Content path on client machine: %s', self.content_path)

        if self.tcinputs.get("ddb_path"):
            self.dedup_provided = True

        if "unix" in self.ma_machine.os_info.lower():
            if self.dedup_provided:
                self.log.info('Unix/Linux MA provided, assigning user defined dedup locations')
                self.ddb_location = self.tcinputs["ddb_path"]

            else:
                self.log.error(
                    f"LVM enabled dedup path must be an input for Unix MA {self.media_agent_name}")
                Browser.close_silently(self.browser)
                raise Exception(
                    f"Please provide LVM enabled dedup path as input for Unix MA {self.media_agent_name}")
        else:
            if self.dedup_provided:
                self.log.info('Windows MA provided, assigning user defined dedup location')
                self.ddb_location = self.tcinputs["ddb_path"]

            else:
                self.log.info('Windows MA provided, creating dedup locations')
                self.path = self.ma_machine.join_path(ma_drive, f"Automation_DDB")
                self.ddb_location = self.ma_machine.join_path(self.path, self.id, "DDB")

        self.log.info('selected ddb location for testCase: %s', self.ddb_location)

    def validate_storage_status(self, action, storage_name):
        """Validates whether the storage is visible on CC or not

            Args:
                action -  Create/Delete

                storage_name - name of the storage whose creation/deletion needs to be validated
        """

        if action.lower() == "create":
            expected_status = True
        elif action.lower() == "delete":
            expected_status = False
        else:
            raise Exception(f"Provide correct action - Create/Delete, you provided {action}")

        exist = self.storage_helper.has_air_gap_protect_storage(storage_name)

        if exist == expected_status:
            self.log.info(f"Validated action {action} on Air Gap Protect storage {storage_name} on CC")
        else:
            raise Exception(f'FAILED validating action {action} on Air Gap Protect storage {storage_name} on CC')

    def configure_storages(self):
        """ Create and validate storages required in the TC"""

        # Creating AGP storage early to save time, as it requires time to fully configure
        # Create a dedupe AGP OCI cloud storage
        self.log.info(f"Creating {self.storage_type} - {self.storage_class} dedupe AGP storage")
        self.storage_helper.add_air_gap_protect_storage(air_gap_protect_storage_name=self.agp_storage_name,
                                                        media_agent=self.media_agent_name,
                                                        region=self.tcinputs["location"],
                                                        storage_type=self.storage_type,
                                                        storage_class=self.storage_class,
                                                        deduplication_db_location=self.ddb_location)
        self.log.info(f"Successfully created {self.storage_type} - {self.storage_class} dedupe AGP storage")
        self.validate_storage_status(action='Create', storage_name=self.agp_storage_name)

        # Create a dedupe disk storage pool
        self.log.info(f"Creating dedupe disk storage using MA {self.media_agent_name}")
        self.storage_helper.add_disk_storage(disk_storage_name=self.disk_storage_name,
                                             media_agent=self.media_agent_name,
                                             backup_location=self.disk_backup_location,
                                             deduplication_db_location=self.ddb_location)
        self.log.info(f"Successfully created dedupe disk storage using MA {self.media_agent_name}")

    def generate_backup_data(self):
        """Generates backup data on client"""

        one_file_size = (self.backup_data_in_MB // self.num_of_files)
        self.log.info(
            f"Generating {self.num_of_files} files of size {one_file_size} MB at {self.content_path} on client {self.client_name}")
        if self.client_machine.generate_test_data(file_path=self.content_path, dirs=1,
                                                  file_size=one_file_size * 1024,  # converting data to KBs
                                                  files=self.num_of_files):
            self.log.info(f"Successfully generated data at {self.content_path} on client {self.client_name}")
        else:
            self.log.error(f"Unable to generate data at {self.content_path} on client {self.client_name}")
            raise Exception(f"Unable to Generate Data at {self.content_path} on client {self.client_name}")

    def configure_plan(self):
        """Create,associate and validate plan as per TC"""

        self.log.info("Adding a new plan: %s", self.plan_name)

        self.plan_helper.plan_name = {'server_plan': self.plan_name}
        self.plan_helper.storage = {'pri_storage': self.disk_storage_name, 'pri_ret_period': '1', 'ret_unit': 'Day(s)',
                                    'sec_storage': self.agp_storage_name, 'sec_ret_period': '1'}
        self.plan_helper.sec_copy_name = self.sec_copy_name
        self.plan_helper.retention = None
        self.plan_helper.rpo_hours = None
        self.plan_helper.backup_data = None
        self.plan_helper.allow_override = None
        self.plan_helper.allowed_features = None
        self.plan_helper.backup_data = None
        self.plan_helper.backup_day = None
        self.plan_helper.backup_duration = None
        self.plan_helper.snapshot_options = None
        self.plan_helper.database_options = None

        self.plan_helper.add_plan()
        self.log.info('successfully created plan: %s', self.plan_name)

    def check_license(self):
        """Checks whether the specified license is active or not"""

        self.log.info(f"Checking whether license {self.license_code} is added on CS or not")

        query = """ select 1 from LicUsage where LicType = {0}
                        and OpType = 'Install' """.format(self.license_code)

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info("RESULT: %s", cur)
        if cur[0] and int(cur[0]) == 1:
            self.log.info("License is added on CS")
        else:
            raise Exception(f"Exiting testcase, as license {self.license_code} specified is not active on testcase")

    def run_backup(self):
        """ Run full backup on SC"""

        self.log.info(f"Running backup job on subclient {self.subClient_name}")
        self.common_utils.subclient_backup(subclient=self.subclient_obj, backup_type='Full')
        self.log.info(f"Backup job completed on subclient {self.subClient_name}")

    def run_restore_from_sec_copy(self):
        """ Runs restore from secondary copy on plan"""

        self.log.info(f"Running Restore job on plan {self.plan_name} from sec copy {self.sec_copy_name}")
        job_obj = self.common_utils.subclient_restore_out_of_place(client=self.client_name,
                                                                   destination_path=self.restored_location,
                                                                   paths=[self.content_path],
                                                                   subclient=self.subclient_obj,
                                                                   copy_precedence=2)
        self.log.info("Restore job: %s completed successfully", job_obj.job_id)

    def run_aux_copy_job(self):
        """Run aux copy job to AGP storage (secondary backup destination)"""

        self.log.info(f"Running auxiliary copy job via CC on plan {self.plan_name}")
        try:
            job_id = self.plan_helper.run_auxiliary_copy_job(plan_name=self.plan_name, copy_name=self.sec_copy_name)
        except Exception as exp:
            raise Exception(f'Triggering on-demand Aux via CC on plan {self.plan_name} failed with error : {exp}')

        self.log.info(f"Successfully triggered auxiliary copy job via command center with job id: {job_id}")

        # Waiting for Aux copy job to complete
        self.log.info(f"Waiting for Aux copy job [{job_id}] to complete")
        self.mm_helper.wait_for_job_completion(job_obj=job_id)
        self.log.info(f"Successfully Completed Aux copy job [{job_id}]")

    def run(self):
        """run function of this test case"""

        try:
            self.cleanup()

            self.check_license()
            self.configure_storages()
            self.generate_backup_data()

            # Waiting for AGP storage to come online
            self.storage_helper.air_gap_protect_wait_for_online_status(air_gap_protect_storage=self.agp_storage_name,
                                                                       wait_time=3, total_attempts=10)
            self.configure_plan()
            # Removing auto copy schedule on plan
            self.log.info(f"Removing autocopy schedule for Copy [{self.sec_copy_name}] on Plan [{self.plan_name}]")
            self.mm_helper.remove_autocopy_schedule(storage_policy_name=self.plan_name, copy_name=self.sec_copy_name)
            self.log.info(
                f"Successfully removed autocopy schedule for Copy [{self.sec_copy_name}] on Plan [{self.plan_name}]")

            # Configuring backup set
            self.log.info("Configuring Backup set [%s]", self.backup_set_name)
            self.backup_set_obj = self.mm_helper.configure_backupset(self.backup_set_name)
            self.log.info("Successfully configured Backup set [%s]", self.backup_set_name)

            # Configuring subclient
            self.log.info("Configuring subclient [%s]", self.subClient_name)
            self.subclient_obj = self.mm_helper.configure_subclient(self.backup_set_name, self.subClient_name,
                                                                    self.plan_name, self.content_path)
            self.log.info("Successfully configured subclient [%s]", self.subClient_name)

            self.run_backup()
            self.run_aux_copy_job()
            self.run_restore_from_sec_copy()

        except Exception as exp:
            self.cleanup(failed=True)  # Clean folders even in failure case
            handle_testcase_exception(self, exp)

        else:
            self.cleanup()

    def tear_down(self):
        """Tear down function of this test case"""

        try:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

        except Exception as exp:
            self.log.error('Failed to tear down test case with error: %s', exp)

    def disable_lock_on_entities(self):
        """Disables lock on storage pool and plan"""

        copy_id = self.mm_helper.get_copy_id(sp_name=self.plan_name, copy_name=self.sec_copy_name)
        if copy_id:
            self.log.info(
                f"Disabling lock on Copy [{self.sec_copy_name}] copyId: [{copy_id}] of Plan [{self.plan_name}]")
            self.mm_helper.disable_compliance_lock(copy_id=copy_id)

        copy_id = self.mm_helper.get_copy_id(sp_name=self.agp_storage_name, copy_name='Primary')
        if copy_id:
            self.log.info(f"Disabling lock on copyId: [{copy_id}] of Storage Pool [{self.agp_storage_name}]")
            self.mm_helper.disable_compliance_lock(copy_id=copy_id)

    def cleanup(self, failed=False):
        """
        Cleans up entities and data created in TC

        Args:
             failed - True, to clean some entities even in failure case (default - False)

        """

        try:
            self.log.info("****************************** Cleanup Started ******************************")

            if not failed:
                self.disable_lock_on_entities()

                self.log.info('Check for backupset %s', self.backup_set_name)
                if self.agent.backupsets.has_backupset(self.backup_set_name):
                    self.log.info('Deletes backupset %s', self.backup_set_name)
                    self.agent.backupsets.delete(self.backup_set_name)

                self.commcell.refresh()  # Refreshing to get the updated entity list on CommCell

                self.log.info('Check for plan %s', self.plan_name)
                if self.commcell.plans.has_plan(self.plan_name):
                    self.log.info('Deleting plan %s', self.plan_name)
                    self.commcell.plans.delete(self.plan_name)

                self.log.info('Check for storage %s', self.disk_storage_name)
                if self.commcell.storage_pools.has_storage_pool(self.disk_storage_name):
                    self.log.info('Deleting disk storage %s ', self.disk_storage_name)
                    self.commcell.storage_pools.delete(self.disk_storage_name)

                if self.storage_helper.has_air_gap_protect_storage(self.agp_storage_name):
                    self.log.info(f"Deleting AGP storage {self.agp_storage_name}")
                    self.storage_helper.delete_air_gap_protect_storage(self.agp_storage_name)
                    self.validate_storage_status(action='DELETE', storage_name=self.agp_storage_name)

            self.log.info('Check for content path %s', self.content_path)
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info('Removed directory...' + self.content_path)

            self.log.info('Check for restore path %s', self.restored_location)
            if self.client_machine.check_directory_exists(self.restored_location):
                self.client_machine.remove_directory(self.restored_location)
                self.log.info('Removed directory...' + self.restored_location)

            self.log.info("****************************** Cleanup Completed ******************************")

        except Exception as exp:
            self.log.error(f'Error in Cleanup Reason: {exp}')
            raise Exception("CLEANUP FAILED: Please clean up entities manually")
