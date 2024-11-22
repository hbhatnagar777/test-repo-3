# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    create_default_plan()   --  Creates a Default Plan

    create_non_default_plan()   --  Creates a Non-Default Plan

    validate_plan() --  Validates Plan Created through command centre

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.AdminConsolePages.Plans import Plans


class TestCase(CVTestCase):
    """ Command center: Testcase for creating and validating default and non-default archival plans """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Testcase for creating and validating default and non-default archival plans"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.plan = None
        self.table = None
        self.tcinputs = {
            "AgentName": None,
            "PrimaryStorageForPlan": None
        }

    @test_step
    def create_default_plan(self):
        """ Creates a Default plan """

        self.navigator.navigate_to_plan()
        plan_names = self.table.get_column_data('Plan name')
        plan_name = self.tcinputs.get('DefaultPlanName', 'Default Archive Plan')
        if plan_name in plan_names:
            self.plan.delete_plan(plan_name)
            self.admin_console.wait_for_completion()

        storage = {
            'pri_storage': self.tcinputs.get('PrimaryStorageForPlan'),
            'pri_ret_period': None,
            'ret_unit': None
        }
        self.plan.create_archive_plan(plan_name=plan_name, storage=storage)
        self.commcell.refresh()

    @test_step
    def create_non_default_plan(self):
        """ Creates a Non-Default Plan """

        self.navigator.navigate_to_plan()
        plan_names = self.table.get_column_data('Plan name')
        plan_name = self.tcinputs.get('NonDefaultPlanName', 'Non Default Archive Plan')
        if plan_name in plan_names:
            self.plan.delete_plan(plan_name)
            self.admin_console.wait_for_completion()

        storage = {
            'pri_storage': self.tcinputs.get('PrimaryStorageForPlan'),
            'pri_ret_period': self.tcinputs.get('PrimaryRetentionPeriod', '6'),
            'ret_unit': self.tcinputs.get('PrimaryRetentionUnit', 'Month(s)')
        }

        rpo = {
            'archive_frequency': self.tcinputs.get('ArchiveFrequency', 8),
            'archive_frequency_unit': self.tcinputs.get('ArchiveFrequencyUnit', 'Hour(s)'),
        }

        archive_day = dict.fromkeys(['1', '3', '4', '5', '6', '7'], 1)

        archive_duration = dict.fromkeys(['2', '3', '4', '5'], 1)

        archiving_rules = {
            'last_modified': self.tcinputs.get('LastModifiedTime', None),
            'last_modified_unit': self.tcinputs.get('LastModifiedUnit', None),
            'last_accessed': self.tcinputs.get('LastAccessedTime', 1),
            'last_accessed_unit': self.tcinputs.get('LastAccessedUnit', 'days'),
            'file_size': self.tcinputs.get('FileSize', 10),
            'file_size_unit': self.tcinputs.get('FileSizeUnit', 'KB'),
        }
        self.plan.create_archive_plan(plan_name=plan_name, storage=storage, rpo=rpo, archive_duration=archive_duration,
                                      archive_day=archive_day, archiving_rules=archiving_rules)
        self.commcell.refresh()

    def validate_plan(self, plan_properties, min_file_size, access_time, modified_time, max_file_size,
                      archiver_retention, backup_cycles, backup_days, archiver_days, start_time, rpo):
        """ Validates Plan Created through command centre """

        file_size_greater_than = \
            plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy']['subClientList'][0][
                'fsSubClientProp']['diskCleanupRules']['fileSizeGreaterThan']
        if file_size_greater_than == min_file_size:
            self.log.info("file_size_greater_than = {}".format(file_size_greater_than))
        else:
            raise CVTestStepFailure(
                "Validate Default Plan failed as file_size_greater_than = {}".format(file_size_greater_than))

        file_access_time_older_than = \
            plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy']['subClientList'][0][
                'fsSubClientProp']['diskCleanupRules']['fileAccessTimeOlderThan']
        if file_access_time_older_than != access_time:
            raise CVTestStepFailure(
                "Validate Default Plan failed as file_access_time_older_than = {}".format(file_access_time_older_than))
        else:
            self.log.info("file_access_time_older_than = {}".format(file_access_time_older_than))

        file_modified_time_older_than = \
            plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy']['subClientList'][0][
                'fsSubClientProp']['diskCleanupRules']['fileModifiedTimeOlderThan']
        if file_modified_time_older_than != modified_time:
            raise CVTestStepFailure(
                "Validate Default Plan failed as file_modified_time_older_than = {}".format(
                    file_modified_time_older_than))
        else:
            self.log.info("file_modified_time_older_than = {}".format(file_modified_time_older_than))

        maximum_file_size = \
            plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy']['subClientList'][0][
                'fsSubClientProp']['diskCleanupRules']['maximumFileSize']
        if maximum_file_size != max_file_size:
            raise CVTestStepFailure(
                "Validate Default Plan failed as maximum_file_size = {}".format(
                    maximum_file_size))
        else:
            self.log.info("maximum_file_size = {}".format(maximum_file_size))

        subclient_archiver_retention = \
            plan_properties['laptop']['content']['backupContent'][0]['subClientPolicy']['subClientList'][0][
                'fsSubClientProp']['extendRetentionForNDays']
        if subclient_archiver_retention != archiver_retention:
            raise CVTestStepFailure(
                "Validate Default Plan failed as subclient_archiver_retention = {}".format(
                    subclient_archiver_retention))
        else:
            self.log.info("subclient_archiver_retention = {}".format(subclient_archiver_retention))

        retain_backup_data_for_cycles = plan_properties['storage']['copy'][0]['retentionRules'][
            'retainBackupDataForCycles']
        if retain_backup_data_for_cycles != backup_cycles:
            raise CVTestStepFailure(
                "Validate Default Plan failed as retain_backup_data_for_cycles = {}".format(
                    retain_backup_data_for_cycles))
        else:
            self.log.info("retain_backup_data_for_cycles = {}".format(retain_backup_data_for_cycles))

        retain_archiver_data_for_days = plan_properties['storage']['copy'][0]['retentionRules'][
            'retainArchiverDataForDays']
        if retain_archiver_data_for_days != archiver_days:
            raise CVTestStepFailure(
                "Validate Default Plan failed as retain_archiver_data_for_days = {}".format(
                    retain_archiver_data_for_days))
        else:
            self.log.info("retain_archiver_data_for_days = {}".format(retain_archiver_data_for_days))

        retain_backup_data_for_days = plan_properties['storage']['copy'][0]['retentionRules'][
            'retainBackupDataForDays']
        if retain_backup_data_for_days != backup_days:
            raise CVTestStepFailure(
                "Validate Default Plan failed as retain_backup_data_for_days = {}".format(
                    retain_backup_data_for_days))
        else:
            self.log.info("retain_backup_data_for_days = {}".format(retain_backup_data_for_days))

        active_start_time = plan_properties['schedule']['subTasks'][0]['pattern']['active_start_time']
        if active_start_time != start_time:
            raise CVTestStepFailure(
                "Validate Default Plan failed as active_start_time = {}".format(
                    active_start_time))
        else:
            self.log.info("active_start_time = {}".format(active_start_time))

        rpo_in_minutes = plan_properties['summary']['rpoInMinutes']
        if rpo_in_minutes != rpo:
            raise CVTestStepFailure(
                "Validate Default Plan failed as rpo_in_minutes = {}".format(
                    rpo_in_minutes))
        else:
            self.log.info("rpo_in_minutes = {}".format(rpo_in_minutes))

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.table = Table(self.admin_console)
        self.plan = Plans(self.admin_console)
        self.navigator = self.admin_console.navigator

    def run(self):
        """Main function for test case execution"""

        _desc = """
        1)	Create an archive plan with default settings.
        2)	Create a storage policy with retention infinite retention.
        3)	Verify that subclient policy with job based retention set to 0 days and size rule set to 1 MB.
        4)	Verify that subclient policy, with Modified time rule set to 91 days. 
        5)	Verify that remaining all the rules are set to 0.
        6)	Schedule policy with RPO set at the plan level. 
        7)	Create  an archive plan with Access time rule set to x day, storage policy set to y day retention, file size z and RPO settings.
        8)	Verify that subclient policy with Access time rule set to x days.
        9)	Verify that  storage policy with retention Y days 1 cycle is created.
        10)	Verify that the File size in the subclient policy is set to z.
        11)	Verify that remaining all the rules are set to 0.
        12)	Schedule policy with RPO set at the plan level.
        """
        try:
            self.create_default_plan()

            plan = self.commcell.plans.get(self.tcinputs.get('DefaultPlanName', 'Default Archive Plan'))

            self.validate_plan(plan._plan_properties, min_file_size=1024, access_time=0, modified_time=91,
                               max_file_size=0,
                               archiver_retention=0, backup_cycles=-1, backup_days=-1, archiver_days=-1,
                               start_time=75600, rpo=1440)
            self.log.info("Default Plan creation succeeded.")

            self.create_non_default_plan()

            plan = self.commcell.plans.get(self.tcinputs.get('NonDefaultPlanName', 'Non Default Archive Plan'))

            self.validate_plan(plan._plan_properties, min_file_size=10, access_time=1, modified_time=0, max_file_size=0,
                               archiver_retention=0, backup_cycles=1, backup_days=182, archiver_days=-1,
                               start_time=0, rpo=480)
            self.log.info("Non Default Plan creation succeeded.")

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
