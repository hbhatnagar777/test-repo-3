# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Command Center - Basic Disk Configuration Case (Precert)


Steps:
    0.  Previous run cleanup
    1.  Create a Non-dedupe disk storage pool (with mediaagent as MA1 and storage path is local to MA1)
    2.  Create a Dedupe disk storage pool (with mediaagent as MA2)
    3.  Create a Plan with primary storage as Dedupe disk storage pool (created in step2)
        and secondary storage as Non-dedupe storage pool (created in step1).
    4.  Add a mountpath to the a Non-dedupe disk storage pool (with mediaagent as MA2)
    5.  Validate that MA2 should be auto shared to MP1 created in step 1 as DataServer IP and viceversa.
    6.  Run a Full backup
    7.  Run an Auxiliary Copy job from Command Center
    8.  Run Restore from Command Center using secondary copy
    *.  Cleanup

TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class

    _get_mountpath_id() --  To get first mountpath id on specified library

    _cleanup()      --  To perform cleanup operation before setting the environment and after testcase completion

    setup()         --  setup function of this test case

    run_full_backup()    --  To run a Full backup job

    run__aux_via_cc()       --  To run auxiliary copy job via command center

    run_restore_from_cc()   --  To perform restore from command center

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


User should have the following permissions:
    [Execute Workflow] permission on [Execute Query] workflow



Sample Input:
"71167": {
    "ClientName": "Name of Client Machine",
    "AgentName": "File System",
    "MediaAgent1": "Name of MA machine1",
    "MediaAgent2": "Name of MA machine2"
}


NOTE:
    1. Media Agent 2 will be used to configure DDB partitions and hence needs to be a Windows MA
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
from Web.AdminConsole.FSPages.RFsPages.FS_Common_Helper import FileServersUtils
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from cvpysdk.job import JobController
from datetime import datetime
from dateutil import tz


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Command Center - Basic Disk Configuration Case (Precert)"
        self.browser = None
        self.admin_console = None
        self.storage_helper = None
        self.mmhelper = None
        self.common_util = None
        self.plan_name = None
        self.client_machine = None
        self.ma1_machine = None
        self.ma2_machine = None
        self.nondedupe_storage_name = None
        self.nondedupe_backup_location = None
        self.nondedupe_backup_location2 = None
        self.dedupe_backup_location = None
        self.dedupe_storage_name = None
        self.ddb_location = None
        self.content_path = None
        self.restore_dest_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent1": None,
            "MediaAgent2": None
        }
        self.cleanup_status = False
        self.plan_helper = None
        self.fs_utils = None
        self.file_server = None
        self.storage_policy = None
        self.jobs = None
        self.navigator = None
        self.jobs_list = []

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
        if cur[0] != ['']:
            return cur[0]
        self.log.error("No entries present")
        raise Exception("Invalid Library Name.")

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
                self.log.info('Deletes storage %s ', self.nondedupe_storage_name)
                self.commcell.storage_pools.delete(self.nondedupe_storage_name)

            self.log.info('Check for storage %s', self.dedupe_storage_name)
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
        self.plan_helper = PlanMain(self.admin_console, csdb=self.csdb, commcell=self.commcell)
        self.navigator = self.admin_console.navigator
        self.storage_helper = StorageMain(self.admin_console)
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        options_selector = OptionsSelector(self.commcell)
        time_stamp = options_selector.get_custom_str()
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.ma1_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent1'])
        self.ma2_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent2'])
        self.nondedupe_storage_name = '%sNonDedupeDisk' % str(self.id)
        self.dedupe_storage_name = '%sDedupeDisk' % str(self.id)
        self.plan_name = '%sPlan' % str(self.id)
        self.plan_helper.plan_name = {"server_plan": self.plan_name}
        self.plan_helper.sec_copy_name = 'Secondary'
        self.plan_helper.storage = {'pri_storage': self.nondedupe_storage_name,
                                    'pri_ret_period': '30',
                                    'sec_storage': self.dedupe_storage_name,
                                    'sec_ret_period': '45',
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
        
        self.fs_utils = FileServersUtils(self.admin_console)
        self.file_server = FileServers(self.admin_console)

    @test_step
    def create_storage(self):
        """To create a new disk storage"""

        ma1_name = self.commcell.clients.get(self.tcinputs['MediaAgent1']).display_name
        self.log.info("Adding a new disk for primary nondedupe storage: %s", self.nondedupe_storage_name)
        self.storage_helper.add_disk_storage(
            self.nondedupe_storage_name,
            ma1_name,
            self.nondedupe_backup_location)
        self.log.info('successfully created disk storage: %s', self.nondedupe_storage_name)

        ma2_name = self.commcell.clients.get(self.tcinputs['MediaAgent2']).display_name
        self.log.info("Adding a new disk for secondary dedupe storage: %s", self.dedupe_storage_name)
        self.storage_helper.add_disk_storage(
            self.dedupe_storage_name,
            ma2_name,
            self.dedupe_backup_location,
            deduplication_db_location=[self.ddb_location + "_1"])
        self.log.info('successfully created disk storage: %s', self.dedupe_storage_name)

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
            self.log.error("Validation for mountpath access type was failed")
            raise Exception("Validation for mountpath access type was failed")

    @test_step
    def create_backup_entities(self):
        """To create required entities for backup"""

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
        
        # Remove association from system created autocopy schedule to trigger on demand auxcopy at a later point
        self.log.info(
            "Removing association with System Created Autocopy schedule on above created copy")
        self.mmhelper.remove_autocopy_schedule(self.plan_name, self.plan_helper.sec_copy_name)

    @test_step
    def run_full_backup(self):
        """ To run a Full backup job"""

        job_types_sequence_list = ['full']
        for sequence_index in range(0, len(job_types_sequence_list)):
            # Create unique content
            if job_types_sequence_list[sequence_index] != 'synthetic_full':
                self.log.info("Generating Data at %s", self.content_path)
                if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10):
                    self.log.error("unable to Generate Data at %s", self.content_path)
                    raise Exception("unable to Generate Data at {0}".format(self.content_path))
                self.log.info("Generated Data at %s", self.content_path)
            # Perform Backup
            self.jobs_list.append(self.common_util.subclient_backup(self.subclient,
                                                                    job_types_sequence_list[sequence_index]))

    @test_step
    def run_restore_from_cc(self):
        """
        Perform restore from command center by changing source to secondary copy
        """
        self.file_server.navigate_to_file_server_tab()

        self.file_server.access_server(self.client.display_name)

        # start_time = self.jobs_list[4].start_time
        start_time = self.jobs_list[-1].start_time

        date_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

        # covert time from utc to local machine time
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        date_time = date_time.replace(tzinfo=from_zone)
        date_time = date_time.astimezone(to_zone)
        
        restore_time = {'year':     date_time.year,
                        'month':    date_time.strftime("%B"),
                        'date':     date_time.day,
                        'hours':    date_time.hour,
                        'minutes':  date_time.minute
                        }
        
        self.fs_utils.restore_from_calender(calendar=restore_time,
                                            backuspet_name=self.backupset_name,
                                            measure_time=False)
        
        restore_job_id = self.fs_utils.restore(dest_client=self.client.display_name,
                                               destination_path=self.restore_dest_path,
                                               restore_aux_copy=True,
                                               storage_copy_name=self.plan_helper.sec_copy_name)
        
        restore_job = JobController(self.commcell).get(restore_job_id)
        
        if not restore_job.wait_for_completion():
            self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                            restore_job.delay_reason))
        self.log.info("restore job [%s] has completed.", restore_job.job_id)
        
    @test_step
    def run_aux_via_cc(self):
        """
        Method to perform on demand aux via CC -> plan -> backup destinations page
        """

        self.log.info("Running auxiliary copy job via command center")
        try:
            job_id = self.plan_helper.run_auxiliary_copy_job(self.plan_name, self.plan_helper.sec_copy_name)
        except Exception as exp:
            raise CVTestStepFailure(f'Triggering on-demand Aux via CC failed with error : {exp}')

        self.log.info(f"Successfully triggered auxiliary copy job via command center with job id: {job_id}")
        
        # Wait for Aux copy job to complete
        self.log.info("Waiting for Aux copy job to complete")
        self.jobs = Jobs(self.admin_console)
        job_details = self.jobs.job_completion(job_id=job_id, skip_job_details=False)
        
        if job_details['Status'] == 'Completed':
            self.log.info(f"Auxiliary copy job {job_id} completed successfully")
        else:
            self.log.error(f"Auxiliary copy job {job_id} failed with status {job_details['status']}")

    def run(self):
        """Main function for test case execution"""

        try:
            self.cleanup()
            self.create_storage()
            self.check_mp_share()
            self.create_backup_entities()
            self.run_full_backup()
            self.run_aux_via_cc()
            self.run_restore_from_cc()
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
