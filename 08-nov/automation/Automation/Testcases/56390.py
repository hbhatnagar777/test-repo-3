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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample Input:
"56390": {
    "ClientName": "Name of Client Machine",
    "AgentName": "File System",
    "MediaAgent": "Name of MA machine",
    "CloudServerType": "Type of Cloud Server",
    "CloudServerName": "Name of Cloud Server",
    "CloudContainer": "ContainerName",
    "CloudRegion": "cloud region",
    "CloudAuthType" : "example: Access key and Account name"
}

NOTE:
    Test case requires a saved credential named 56390_Credential for configuring cloud storages
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Admin Console - Basic Cloud Configuration Case"
        self.browser = None
        self.admin_console = None
        self.plan_helper = None
        self.storage_helper = None
        self.plan_name = None
        self.fs_helper = None
        self.mmhelper = None
        self.common_util = None
        self.client_machine = None
        self.ma_machine = None
        self.nondedupe_storage_name = None
        self.dedupe_storage_name = None
        self.ddb_location = None
        self.content_path = None
        self.restore_dest_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgent": None,
            "CloudServerType": None,
            "CloudServerName": None,
            "CloudContainer": None,
            "CloudAuthType": None
        }
        self.cleanup_status = False

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
        """ To perform cleanup operation """

        try:
            self.log.info('Check for backupset %s', self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                # To delete backupset if exists
                self.log.info('Deletes backupset %s', self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            self.log.info('Check for plan %s', self.plan_name)
            if self.commcell.plans.has_plan(self.plan_name):
                # To delete plan if exists
                self.log.info('Deletes plan %s', self.plan_name)
                self.commcell.plans.delete(self.plan_name)

            self.log.info('Check for storage %s', self.nondedupe_storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.nondedupe_storage_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s', self.nondedupe_storage_name)
                self.commcell.storage_pools.delete(self.nondedupe_storage_name)

            self.log.info('Check for storage %s', self.dedupe_storage_name)
            if self.commcell.storage_pools.has_storage_pool(self.dedupe_storage_name):
                # To delete disk storage if exists
                self.log.info('Deletes storage %s', self.dedupe_storage_name)
                self.commcell.storage_pools.delete(self.dedupe_storage_name)

            self.commcell.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    @test_step
    def create_entities(self):
        """ To create cloud storage, plan, backupset, subclient"""

        # To create a new cloud storage
        self.log.info("Adding a new cloud for primary nondedupe storage: %s", self.nondedupe_storage_name)
        ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent']).display_name
        self.storage_helper.add_cloud_storage(self.nondedupe_storage_name, ma_name,
                                              self.tcinputs['CloudServerType'],
                                              self.tcinputs['CloudServerName'],
                                              self.tcinputs['CloudContainer'],
                                              storage_class=self.tcinputs.get('CloudStorageClass'),
                                              saved_credential_name=str(self.id)+'_Credential',
                                              region=self.tcinputs['CloudRegion'],
                                              auth_type=self.tcinputs['CloudAuthType'])
        self.log.info('successfully created cloud storage: %s', self.nondedupe_storage_name)

        self.log.info("Adding a new cloud for secondary dedupe storage: %s", self.dedupe_storage_name)
        self.storage_helper.add_cloud_storage(self.dedupe_storage_name, ma_name,
                                              self.tcinputs['CloudServerType'],
                                              self.tcinputs['CloudServerName'],
                                              self.tcinputs['CloudContainer'],
                                              storage_class=self.tcinputs.get('CloudStorageClass'),
                                              saved_credential_name=str(self.id) + '_Credential',
                                              deduplication_db_location=self.ddb_location,
                                              region=self.tcinputs['CloudRegion'],
                                              auth_type=self.tcinputs['CloudAuthType'])
        self.log.info('successfully created cloud storage: %s', self.dedupe_storage_name)

        # To create a new plan
        self.log.info("Adding a new plan: %s", self.plan_name)
        self.plan_helper.add_plan()
        self.log.info("successfully created plan: %s", self.plan_name)

        # To add backupset
        self.mmhelper.configure_backupset(self.backupset_name, self.agent)

        # To add subclient
        self.commcell.refresh()
        self.subclient = self.mmhelper.configure_subclient(self.backupset_name, self.subclient_name,
                                                           self.plan_name, self.content_path, self.agent)

    @test_step
    def run_backup_restore(self):
        """To run backup and restore jobs"""

        job_types_sequence_list = ['full', 'incremental', 'incremental', 'synthetic_full', 'incremental',
                                   'synthetic_full']
        for sequence_index in range(0, 6):
            # Create unique content
            if job_types_sequence_list[sequence_index] != 'synthetic_full':
                self.log.info("Generating Data at %s", self.content_path)
                if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10):
                    self.log.error("unable to Generate Data at %s", self.content_path)
                    raise Exception("unable to Generate Data at {0}".format(self.content_path))
                self.log.info("Generated Data at %s", self.content_path)
            # Perform Backup
            self.common_util.subclient_backup(self.subclient, job_types_sequence_list[sequence_index])

        # Perform Restore
        restore_job = self.subclient.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path])
        self.log.info("restore job [%s] has started.", restore_job.job_id)
        if not restore_job.wait_for_completion():
            self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                            restore_job.delay_reason))
        self.log.info("restore job [%s] has completed.", restore_job.job_id)

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.init_tc()
        self.plan_helper = PlanMain(self.admin_console, commcell=self.commcell)
        self.storage_helper = StorageMain(self.admin_console)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        options_selector = OptionsSelector(self.commcell)
        time_stamp = options_selector.get_custom_str()
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])
        self.nondedupe_storage_name = '%sNonDedupeCloud' % str(self.id)
        self.dedupe_storage_name = '%sDedupeCloud' % str(self.id)
        self.plan_name = '%sPlan' % str(self.id)
        self.plan_helper.plan_name = {"server_plan": self.plan_name}
        self.plan_helper.sec_copy_name = 'Secondary'
        self.plan_helper.storage = {'pri_storage': self.nondedupe_storage_name, 'pri_ret_period': '10',
                                    'sec_storage': self.dedupe_storage_name, 'sec_ret_period': '15',
                                    'ret_unit': 'Day(s)'}
        self.plan_helper.backup_data = None
        self.plan_helper.backup_day = None
        self.plan_helper.backup_duration = None
        self.plan_helper.rpo_hours = None
        self.plan_helper.allow_override = None
        self.plan_helper.database_options = None

        self.backupset_name = '%s_Backupset' % str(self.id)
        self.subclient_name = '%s_SC' % str(self.id)

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=30 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine .remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)

        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Restoredata')
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)
        self.client_machine.create_directory(self.restore_dest_path)

        # To select drive with space available in MA2 machine
        self.log.info('Selecting drive in the MA machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=30 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.ddb_location = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB_%s' % time_stamp)

    def run(self):
        """Main function for test case execution"""
        try:
            self.cleanup()
            self.create_entities()
            self.run_backup_restore()
        except Exception as exp:
            handle_testcase_exception(self, exp)
            self.cleanup_status = True
        else:
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            self.cleanup()

    def tear_down(self):
        """Tear Down Function of this Case"""
        try:
            if self.cleanup_status:
                self.log.info("This is Tear Down method")
                if self.client_machine.check_directory_exists(self.content_path):
                    self.client_machine.remove_directory(self.content_path)
                if self.client_machine.check_directory_exists(self.restore_dest_path):
                    self.client_machine.remove_directory(self.restore_dest_path)
                self.cleanup()

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")

        finally:
            Browser.close_silently(self.browser)
