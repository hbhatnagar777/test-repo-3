# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Acceptance of Compliance Lock using MRR storage - CC

Steps:
    A. Case1:
        i.   Create a non-dedupe MRR storage
        ii.  Try to enable H/w WORM lock, we should get an error and no setting should be enabled i.e. micro pruning is
             ON, retention not set on pool.
        iii.    A. For SP<32 Enable compliance lock on pool, it should be successful
                B. For SP>=32 Validate compliance lock is enabled by default
        iv.  Pool should not ask for retention and no setting should be enabled i.e. micro pruning is ON, retention not
             set on pool.
        v.   Associate a copy to the MRR pool
            1. Copy should have WORM copy flag set
            2. Retention override flag should be set
            3. Retention is considered from dependent copy, say set retention as 1d
            4. Try increasing retention to 7 days, it should be successful
            5. Try reducing basic retention from 7 to 5 Days, it should return error
            6. Try increasing retention to 10 d it should be successful as well.
            6. Try setting extended retention (12 d), it should be successful, only one rule out of 3 will be fine
            7. Try reducing extended retention (10 d) it should return error
            9. Try increasing extended retention (15 d) it should be successful.

    B. Case2:
        i.    Create a dedupe MRR storage pool
        ii.   Associate a copy to the MRR pool
        iii.  Try to enable H/w WORM lock, we should get an error and no setting should be enabled i.e. micro pruning is
              ON, seal frequency  not set, retention not set on pool.
        iv.     A. Enable compliance lock on pool, it should be successful and applied on dependent copy as well.
                B. For SP>=32 Validate compliance lock is enabled by default and applied on dependent copy as well.
        v.    Pool should not ask for retention and no setting should be enabled i.e. micro pruning is ON, seal
              frequency  not set, retention not set on pool.
        vi.   Create another storage plan using disk storage for primary copy
        vii.  Associate a secondary copy on new SP to MRR pool and see compliance lock is ON, retention pass as 1D
        viii. On the secondary copy associated to the MRR pool
            1. Retention override flag should be set
            2. Retention is considered from dependent copy, say set retention as 1d
            3. Try increasing retention to 7 days, it should be successful
            4. Try reducing basic retention from 7 to 5 Days, it should return error
            5. Try increasing retention to 10 d it should be successful as well.
            6. Try setting extended retention (12 d), it should be successful, only one rule out of 3 will be fine
            7. Try reducing extended retention (10 d) it should return error
            8. Try increasing extended retention (15 d) it should be successful.

TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


User should have the following permissions:
        [Execute Workflow] permission on [Execute Query] workflow


Sample Input:
"65592": {
    "MediaAgentName": "MediaAgentName",
    "StorageType": Cloud vendor type, same as UI (eg- Microsoft Azure Storage)
    "StorageClass": Storage class associated with the storage, same as UI (eg - Hot)
    "Region": "Air Gap Protect storage region / location" , same as UI
}
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep, handle_testcase_exception

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from Web.AdminConsole.Helper.PlanHelper import PlanMain


class TestCase(CVTestCase):
    """This is to validate MRR + WORM and also compliance-specific configuration."""

    test_step = TestStep()

    # Modify Service Pack number if compliance lock is expected to be enabled by default after creation
    COMPLIANCE_LOCK_AUTO_ENABLED_SP = 32    # >= 32

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name        (str)       --  name of this test case

                tcinputs    (dict)      --  test case inputs with input name as dict key
                                            and value as input type
        """
        super(TestCase, self).__init__()

        self.name = 'Acceptance of Compliance Lock using MRR storage - CC'
        self.tcinputs = {
            'MediaAgentName': None,
            'StorageType': None,
            'StorageClass': None,
            'Region': None
        }

        self.browser = None
        self.admin_console: AdminConsole = None
        self.storage_helper: StorageMain = None
        self.plan_helper: PlanMain = None

        self.media_agent = None
        self.air_gap_region = None
        self.cs_version = None

        self.mrr_storage_name_1 = None
        self.mrr_storage_name_2 = None

        self.disk_storage_name = None
        self.mount_path = None
        self.ddb_path = None

        self.plan_name_1 = None
        self.plan_name_2A = None
        self.plan_name_2B = None

    def _init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )

            self.storage_helper = StorageMain(self.admin_console)
            self.plan_helper = PlanMain(self.admin_console)
        except Exception as exp:
            raise CVTestCaseInitFailure(exp) from exp

    def _init_props(self):
        """Initializes parameters and names required for testcase"""
        self.media_agent = self.tcinputs['MediaAgentName']
        self.air_gap_region = self.tcinputs['Region']
        self.storage_class = self.tcinputs["StorageClass"]
        self.storage_type = self.tcinputs["StorageType"]
        self.cs_version = int(self.commcell.commserv_version)

        options_selector = OptionsSelector(self.commcell)
        ma_machine = options_selector.get_machine_object(self.media_agent)
        ma_drive = options_selector.get_drive(ma_machine)

        self.mrr_storage_name_1 = '%s_mrr-ma_%s-1' % (str(self.id), self.media_agent)
        self.mrr_storage_name_2 = '%s_mrr-ma_%s-2' % (str(self.id), self.media_agent)

        self.disk_storage_name = '%s_disk-ma_%s' % (str(self.id), self.media_agent)
        self.mount_path = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')
        self.ddb_path = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')       # Unix?

        self.plan_name_1 = '%s_plan-ma_%s-1' % (str(self.id), self.media_agent)
        self.plan_name_2A = '%s_plan-ma_%s-2A' % (str(self.id), self.media_agent)
        self.plan_name_2B = '%s_plan-ma_%s-2B' % (str(self.id), self.media_agent)

    def setup(self):
        """Setup function of this test case"""
        self._init_tc()
        self._init_props()

    @test_step
    def _cleanup(self):
        """Delete entities before/after running testcase"""
        try:
            plans_list = self.plan_helper.list_plans()
            if self.plan_name_1 in plans_list:
                self.plan_helper.plan_name = {'server_plan': self.plan_name_1}
                self.plan_helper.delete_plans()
            if self.plan_name_2A in plans_list:
                self.plan_helper.plan_name = {'server_plan': self.plan_name_2A}
                self.plan_helper.delete_plans()
            if self.plan_name_2B in plans_list:
                self.plan_helper.plan_name = {'server_plan': self.plan_name_2B}
                self.plan_helper.delete_plans()

            disk_storage_list = self.storage_helper.list_disk_storage()
            if self.disk_storage_name in disk_storage_list:
                self.storage_helper.delete_disk_storage(self.disk_storage_name)

            mrr_storage_list = self.storage_helper.list_air_gap_protect_storage()
            if self.mrr_storage_name_1 in mrr_storage_list:
                self.storage_helper.delete_air_gap_protect_storage(self.mrr_storage_name_1)
            if self.mrr_storage_name_2 in mrr_storage_list:
                self.storage_helper.delete_air_gap_protect_storage(self.mrr_storage_name_2)
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    @test_step
    def _case_1(self):
        """Runs the steps for case 1"""
        try:
            self._wait_for_online_status(self.mrr_storage_name_1)   # MRR Storage config is async
            self._validate_pool_settings(self.mrr_storage_name_1, is_dedupe=False)

            # Compliance lock enabled by default on SP36 and onwards
            if self.cs_version < self.COMPLIANCE_LOCK_AUTO_ENABLED_SP:
                self.storage_helper.air_gap_protect_compliance_lock(self.mrr_storage_name_1)
            self._validate_compliance_lock_on_air_gap_protect_storage(self.mrr_storage_name_1)
            self._validate_pool_settings(self.mrr_storage_name_1, is_dedupe=False)

            self._associate_plan(self.plan_name_1, self.mrr_storage_name_1)
            # Validating compliance lock on Plan Copy through UI not supported before SP36
            if self.cs_version >= 36:
                self._validate_compliance_lock_on_plan_copy(self.plan_name_1, 'Primary')    # Gets values from UI
            self._check_copy_flags(self.plan_name_1, 'Primary')

            self._execute_retention_modification_steps(self.plan_name_1, 'Primary')
        except Exception as exp:
            raise CVTestStepFailure(f'Case 1 failed with error : {exp}')

    @test_step
    def _case_2(self):
        """Runs the steps for case 2"""
        try:
            self._wait_for_online_status(self.mrr_storage_name_2)   # MRR Storage config is async
            self._associate_plan(self.plan_name_2A, self.mrr_storage_name_2)
            self._validate_pool_settings(self.mrr_storage_name_2, is_dedupe=True)

            # Compliance lock enabled by default on SP36 and onwards
            if self.cs_version < self.COMPLIANCE_LOCK_AUTO_ENABLED_SP:
                self.storage_helper.air_gap_protect_compliance_lock(self.mrr_storage_name_2)
            self._validate_compliance_lock_on_air_gap_protect_storage(self.mrr_storage_name_2)
            # Validating compliance lock on Plan Copy through UI not supported before SP36
            if self.cs_version >= 36:
                self._validate_compliance_lock_on_plan_copy(self.plan_name_2A, 'Primary')
            self._validate_pool_settings(self.mrr_storage_name_2, is_dedupe=True)

            self.storage_helper.add_disk_storage(self.disk_storage_name, self.media_agent, self.mount_path)
            self._associate_plan(self.plan_name_2B, self.disk_storage_name, self.mrr_storage_name_2)
            # Validating compliance lock on Plan Copy through UI not supported before SP36
            if self.cs_version >= 36:
                self._validate_compliance_lock_on_plan_copy(self.plan_name_2B, 'Secondary')
            self._check_copy_flags(self.plan_name_2B, 'Secondary')

            self._execute_retention_modification_steps(self.plan_name_2B, 'Secondary')
        except Exception as exp:
            raise CVTestStepFailure(f'Case 2 failed with error : {exp}')

    def run(self):
        """Run function of this test case"""

        try:
            self._cleanup()

            # MRR Storage config is async, start configuration before cases start to save time
            self.storage_helper.add_air_gap_protect_storage(self.mrr_storage_name_1, self.media_agent,
                                                            self.air_gap_region, storage_type=self.storage_type,
                                                            storage_class=self.storage_class)
            self.storage_helper.add_air_gap_protect_storage(self.mrr_storage_name_2, self.media_agent,
                                                            self.air_gap_region, storage_type=self.storage_type,
                                                            storage_class=self.storage_class,
                                                            deduplication_db_location=self.ddb_path)

            self._case_1()
            self._case_2()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        else:
            self._cleanup()     # Clean up entities after testcase only if there are no errors

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            AdminConsole.logout_silently(self.admin_console)
            self.browser.close()
        except Exception as exp:
            self.log.error('Failed to tear down test case with error: %s', exp)

    @test_step
    def _wait_for_online_status(self, air_gap_protect_storage, wait_time=3, total_attempts=10):
        """Waits until Air Gap Protect storage is fully configured; i.e.; Status changes to 'Online'

            Args:
                air_gap_protect_storage (str)   - Name of air gap protect storage
                wait_time               (int)   - Number of minutes to wait before next attempt

                total_attempts          (int)   - Total number of attempts before raising error

            Raises:
                CVTestStepFailure   - If timed out
        """

        try:
            self.storage_helper.air_gap_protect_wait_for_online_status(air_gap_protect_storage, wait_time,
                                                                       total_attempts)
        except Exception as exp:
            if 'Failed to validate status' not in str(exp):
                raise exp   # Something else went wrong
            raise CVTestStepFailure('Failed to configure Air Gap Protect storage [%s]' % air_gap_protect_storage) from exp

    @test_step
    def _validate_pool_settings(self, air_gap_protect_storage, is_dedupe=False):
        """Validates  micro pruning is ON, seal frequency  not set, retention not set on pool.

            Args:
                air_gap_protect_storage     (str)   - Name of air gap protect storage

            Raises:
                CVTestStepFailure   - If pool settings not as expected
        """
        # Retention not set on pool
        self._validate_basic_retention(air_gap_protect_storage, 'Primary', -1)  # Pool is global storage policy

        # Get Library name from Pool name
        query = f"""SELECT  ML.AliasName
                    FROM    MMLibrary ML WITH (NOLOCK)
                    INNER JOIN      MMMasterPool MP WITH (NOLOCK)
                            ON      MP.LibraryId = ML.LibraryId
                    INNER JOIN      MMDrivePool DP WITH (NOLOCK)
                            ON      DP.MasterPoolId = MP.MasterPoolId
                    INNER JOIN      MMDataPath MDP WITH (NOLOCK)
                            ON      MDP.DrivePoolId = DP.DrivePoolId
                    INNER JOIN      archGroupCopy AGC WITH (NOLOCK)
                            ON      MDP.CopyId = AGC.id
                    INNER JOIN      archGroup AG WITH (NOLOCK)
                            ON      AGC.archGroupId = AG.id
                    WHERE AG.name = '{air_gap_protect_storage}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info('RESULT: %s', result)

        library_alias_name = result[0]

        # Micro pruning is ON
        query = f"""SELECT  MP.Attribute
                    FROM    MMMountPath MP WITH (NOLOCK)
                    INNER JOIN      MMLibrary ML WITH (NOLOCK)
                            ON      MP.LibraryId = ML.LibraryId
                    WHERE   ML.AliasName = '{library_alias_name}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info('RESULT: %s', result)

        attribute = int(result[0])
        is_micro_pruning_on = ((attribute & 32) == 32)
        if not is_micro_pruning_on:
            raise CVTestStepFailure('Micro pruning found disabled on %s pool' % air_gap_protect_storage)
        self.log.info('Micro pruning is enabled on %s pool' % air_gap_protect_storage)

        # seal frequency not set
        if is_dedupe:
            query = f"""SELECT  AT.numPeriod
                        FROM    archTask AT WITH (NOLOCK)
                        INNER JOIN      archGroupCopy AGC WITH (NOLOCK)
                                ON      AT.id = AGC.sealStoreTaskId
                        INNER JOIN      archGroup AG WITH (NOLOCK)
                                ON      AGC.archGroupId = AG.id
                        WHERE   AG.name = '{air_gap_protect_storage}'"""
        else:
            query = f"""SELECT  AGC.SIDBStoreId
                        FROM    archGroupCopy AGC WITH (NOLOCK)
                        INNER JOIN      archGroup AG WITH (NOLOCK)
                                ON      AGC.archGroupId = AG.id
                        WHERE   AG.name = '{air_gap_protect_storage}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info('RESULT: %s', result)

        seal_freq_param = int(result[0])    # archTask.numPeriod (dedupe) or archGroupCopy.SIDBStoreId (non dedupe)
        if seal_freq_param != 0:
            self.log.error('Seal frequency found to be set on %s pool (not expected)' % air_gap_protect_storage)
        self.log.info('Seal frequency not set on %s pool (expected)' % air_gap_protect_storage)

    @test_step
    def _validate_compliance_lock_on_air_gap_protect_storage(self, air_gap_protect_storage):
        """Checks if compliance lock is enabled on Air Gap Protect storage

            Args:
                air_gap_protect_storage     (str)   - Name of air gap protect storage

            Raises:
                CVTestStepFailure   - If compliance lock is not enabled
        """
        self.log.info('Validating compliance lock on air gap protect storage [%s]' % air_gap_protect_storage)
        if not self.storage_helper.air_gap_protect_is_compliance_lock_enabled(air_gap_protect_storage):
            raise CVTestStepFailure('Compliance lock not enabled on air gap storage [%s]' % air_gap_protect_storage)
        self.log.info('Compliance lock is enabled on air gap protect storage [%s]' % air_gap_protect_storage)

    @test_step
    def _validate_compliance_lock_on_plan_copy(self, plan, copy):
        """Checks if compliance lock is enabled on given copy of plan using state of toggle on Command center

            Args:
                plan          (str)   - Plan name
                copy          (str)   - Copy name

            Raises:
                CVTestStepFailure   - If compliance lock is not enabled
        """
        self.log.info('Validating compliance lock on copy [%s] of plan [%s]' % (copy, plan))
        if not self.plan_helper.is_compliance_lock_enabled(plan, copy):
            raise CVTestStepFailure('Compliance lock not enabled on copy [%s] of plan [%s]' % (copy, plan))
        self.log.info('Compliance lock is enabled on copy [%s] of plan [%s]' % (copy, plan))

    @test_step
    def _associate_plan(self, plan, pri_storage, sec_storage=None):
        """Configures a new plan and associates copy to given storage

            Args:
                plan        (str)   - Plan name
                pri_storage (str)   - Storage name to be used for primary copy
                sec_storage (str)   - Storage name to be used for secondary copy
        """
        self.plan_helper.plan_name = {'server_plan': plan}
        self.plan_helper.storage = {'pri_storage': pri_storage, 'pri_ret_period': '1', 'ret_unit': 'Day(s)'}
        if sec_storage is not None:
            self.plan_helper.storage.update({'sec_storage': sec_storage, 'sec_ret_period': '1'})
            self.plan_helper.sec_copy_name = 'Secondary'

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

    @test_step
    def _execute_retention_modification_steps(self, plan, copy):
        """Executes retention modifications as mentioned in test case steps

            Args:
                plan    (str)   - Plan name
                copy    (str)   - Copy name
        """
        self.log.info('Executing retention modification steps for plan %s and copy %s' % (plan, copy))

        # Retention is considered from dependent copy, say set retention as 1d
        self._validate_basic_retention(plan, copy, 1)

        # Try increasing retention to 7 days, it should be successful
        self._set_and_validate_basic_retention(plan, copy, 7)

        # Try reducing basic retention from 7 to 5 Days, it should return error
        self._set_and_validate_basic_retention(plan, copy, 5)

        # Try increasing retention to 10 d it should be successful as well.
        self._set_and_validate_basic_retention(plan, copy, 10)

        # Try setting extended retention, it should be successful
        self._set_and_validate_extended_retention(plan, copy, 12)

        # Try reducing extended retention it should return error
        self._set_and_validate_extended_retention(plan, copy, 10)

        # Try increasing extended retention it should be successful.
        self._set_and_validate_extended_retention(plan, copy, 15)

    @test_step
    def _set_and_validate_basic_retention(self, plan, copy, new_ret_days):
        """To set retention on copy for given plan and copy

            Args:
                plan          (str)   - Plan name
                copy          (str)   - Copy name
                new_ret_days  (int)   - New retention period (in days)
        """
        old_ret_days = self._get_basic_retention_period(plan, copy)
        change = 'Increasing' if old_ret_days < new_ret_days else 'Reducing'

        self.log.info('%s retention from %s days to %s days' % (change, old_ret_days, new_ret_days))
        self.plan_helper.modify_retention_on_copy(plan, copy, new_ret_days, 'Day(s)')
        if change == 'Increasing':
            self.log.info('... %s retention should be successful' % change)
            self.log.info('... validating changes')
            self._validate_basic_retention(plan, copy, new_ret_days)
        else:
            self.log.info('... %s retention should not be allowed' % change)
            self.log.info('... validating no changes are made')
            self._validate_basic_retention(plan, copy, old_ret_days)

            # Close dialog, it was not closed by plan helper
            self.admin_console.click_button(self.admin_console.props['action.cancel'])

    @test_step
    def _set_and_validate_extended_retention(self, plan, copy, new_ret_days):
        """To set extended retention on copy for given plan and copy

            Args:
                plan          (str)   - Plan name
                copy          (str)   - Copy name
                new_ret_days  (int)   - New retention period (in days)
        """
        try:
            old_ret_days = self._get_extended_retention_period(plan, copy)  # Returns list of int
        except Exception as exp:
            if str(exp) == 'Unable to fetch extended retention days':
                old_ret_days = [0]  # Setting extended retention for the first time
            else:
                self.log.error(exp)
                raise exp
        change = 'Increasing' if old_ret_days[0] < new_ret_days else 'Reducing'

        self.log.info('%s extended retention from %s days to %s days' % (change, old_ret_days[0], new_ret_days))
        self.plan_helper.modify_extended_retention_on_copy(plan, copy, 1,
                                                           [new_ret_days], ['Day(s)'], ['Monthly Fulls'])
        if change == 'Increasing':
            self.log.info('... %s extended retention should be successful' % change)
            self.log.info('... validating changes')
            self._validate_extended_retention(plan, copy, [new_ret_days])
        else:
            self.log.info('... %s extended retention should not be allowed' % change)
            self.log.info('... validating no changes are made')
            self._validate_extended_retention(plan, copy, old_ret_days)

            # Close dialog, it was not closed by plan helper
            self.admin_console.click_button(self.admin_console.props['action.cancel'])

    def _get_basic_retention_period(self, plan, copy):
        """To get retention set on copy from archAgingRule table for given plan/pool and copy

            Args:
                plan    (str)   - Plan name / Pool name
                copy    (str)   - Copy name

            Returns:
                int             -  retention days set on the copy

            Raises:
                Exception   - If unable to fetch retention period
        """

        query = f"""SELECT  AAR.retentionDays
                    FROM    archAgingRule AAR WITH (NOLOCK)
                    INNER JOIN      archGroupCopy AGC WITH (NOLOCK)
                            ON      AAR.copyId = AGC.id
                    INNER JOIN      archGroup AG WITH (NOLOCK)
                            ON      AGC.archGroupId = AG.id
                    WHERE   AG.name = '{plan}'
                    AND     AGC.name = '{copy}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        results = self.csdb.fetch_one_row()
        self.log.info('RESULT: %s', results[0])
        if results[0] != '':
            return int(results[0])
        raise Exception('Unable to fetch retention period')

    def _get_extended_retention_period(self, plan, copy):
        """To get extended retention days from archAgingRuleExtended table for given plan/pool and copy

            Args:
                plan    (str)   - Plan name / pool
                copy    (str)   - Copy name

            Returns:
                list            - extended retention days list set on the copy

            Raises:
                Exception   - If unable to fetch extended retention period
        """

        query = f"""SELECT  AARE.retentionDays
                    FROM    archAgingRuleExtended AARE WITH (NOLOCK)
                    INNER JOIN      archGroupCopy AGC WITH (NOLOCK)
                            ON      AARE.copyId = AGC.id
                    INNER JOIN      archGroup AG WITH (NOLOCK)
                            ON      AGC.archGroupId = AG.id
                    WHERE   AG.name = '{plan}'
                    AND     AGC.name = '{copy}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        results = self.csdb.fetch_all_rows()
        self.log.info('RESULT: %s', str(results))
        if results and results[0] != '' and results[0][0] != '':
            ret_days = [int(row[0]) for row in results]
            return ret_days
        raise Exception('Unable to fetch extended retention days')

    @test_step
    def _validate_basic_retention(self, plan, copy, ret_days):
        """Validate retention period on copy

            Args:
                plan    (str)   - Plan name / Pool name
                copy    (str)   - Copy name
                ret_days (int)  - Number of retention days set

            Raises:
                CVTestStepFailure   - If retention period not as expected
        """
        retention_days = self._get_basic_retention_period(plan, copy)
        self.log.info('Retention set: %s, expected: %s' % (retention_days, ret_days))
        if retention_days == ret_days:
            self.log.info('Retention days is correctly set on copy [%s] of plan/pool [%s]' % (copy, plan))
        else:
            raise CVTestStepFailure('Retention days was not correctly set on copy [%s] of plan/pool [%s]' % (copy, plan))

    @test_step
    def _validate_extended_retention(self, plan, copy, ret_days):
        """Validate extended retention on copy

            Args:
                plan    (str)           - Plan name / Pool name
                copy    (str)           - Copy name
                ret_days (list of int)  - Number of retention days set for each extended retention rule

            Raises:
                CVTestStepFailure   - If extended retention period not as expected
        """
        retention_days_list = self._get_extended_retention_period(plan, copy)
        for i in range(len(retention_days_list)):
            self.log.info('Extended retention [%s] set: %s, expected: %s' % (i, retention_days_list[i], ret_days[i]))
            if retention_days_list[i] == ret_days[i]:
                self.log.info('Extended retention is correctly set on copy [%s] of plan/pool [%s]' % (copy, plan))
            else:
                raise CVTestStepFailure('Extended retention not correctly set on copy [%s] of plan/pool [%s]' % (copy, plan))

    def _check_copy_flags(self, plan, copy):
        """To check if retention override flag and compliance lock (wormCopy) flag are set

            Args:
                plan    (str)           - Plan name
                copy    (str)           - Copy name

            Raises:
                CVTestStepFailure   - If flags not properly set
        """
        self.log.info('Checking retention override and compliance lock flags on copy [%s] of plan [%s]' % (copy, plan))

        query = f"""SELECT  AGC.flags, AGC.extendedFlags
                    FROM    archGroupCopy AGC WITH (NOLOCK)
                    INNER JOIN      archGroup AG WITH (NOLOCK)
                            ON      AGC.archGroupId = AG.id
                    WHERE   AG.name = '{plan}'
                    AND     AGC.name = '{copy}'"""
        self.log.info('QUERY: %s', query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info('RESULT: %s', result)

        flags, extended_flags = map(int, result)

        over_ride_gacp_retention = ((extended_flags & 2048) == 2048)    # overRideGACPRetention
        cva_worm_copy_flag = ((flags & 16777216) == 16777216)           # CVA_WORM_COPY_FLAG

        if not over_ride_gacp_retention:
            raise CVTestStepFailure('Retention override flag not set on copy [%s] of plan [%s]' % (copy, plan))
        self.log.info('Retention override flag set on copy [%s] of plan [%s]' % (copy, plan))

        if not cva_worm_copy_flag:
            raise CVTestStepFailure('Compliance lock not set on copy [%s] of plan [%s]' % (copy, plan))
        self.log.info('Compliance lock  set on copy [%s] of plan [%s]' % (copy, plan))
