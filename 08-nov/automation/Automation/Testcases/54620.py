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

    _get_storage_dedupe_flags() --  To get default dedupe flags set on SIDB store of given disk storage

    _get_storage_flags_not_set()--  To know which all flags are not set that should be set by default on a storage

    _get_storage_flags_set()    --  To know which all dedupe flag are set that should not be set by default on a storage

    _get_copy_dedupe_flag()     --  To get default dedupe flags set on archGroupCopy table of given plan and copy

    _get_copy_flags_not_set()   --  To know which all dedupe flags are not set that should be set by default on a copy

    _get_copy_flags_set()       --  To know which all dedupe flags are set that should not be set by default on a copy

    _get_retention_period()     --  To get retention set on copy from archAgingRule table for given plan and copy

    _get_extended_retention_period() -- Get extended retention days from archAgingRuleExtended table for given copy

    _get_extended_retention_rule() -- Get extended retention rule from archAgingRuleExtended table for given copy

    _get_full_cycles()          -- Get full cycles from ArchAgingRule table for given plan and copy

    _validate_retention()       -- Validate retention period on copy

    _validate_extended_retention_rules() -- Validate extended retention periods on copy

    _validate_auxcopy_association() --  To validate if  Auxiliary Copy schedule is associated to plan secondary copy

    setup()         --  setup function of this test case

    run()           --  run function of this test case

Sample Input:
"54620": {
    "ClientName": "Name of Client Machine",
    "AgentName": "File System",
    "MediaAgent": "Name of MA machine",
    *** OPTIONAL ***
    "TenantUserPassword": "Password to be used while configuring Tenant User"
}

NOTE:
    1. Tenant User Password must be:
        minimum 12 characters long
        having 2 upper case alphabets
        having 2 lower case alphabets
        having 2 numerals
        having 2 special symbols
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.Helper.StorageHelper import StorageMain
from enum import IntEnum
from Server.organizationhelper import OrganizationHelper

import random


class ExtendedRules(IntEnum):
    EXTENDED_NORULE = 0,
    EXTENDED_ALLFULL = 2,
    EXTENDED_WEEK = 4,
    EXTENDED_MONTH = 8,
    EXTENDED_QUARTER = 16,
    EXTENDED_HALFYEAR = 32,
    EXTENDED_YEAR = 64,
    EXTENDED_HOUR = 262144,
    EXTENDED_DAY = 524288


class CipherList(IntEnum):
    BlowFish = 2,
    AES = 3,
    Serpent = 4,
    TwoFish = 5,
    DES3 = 6,
    GOST = 8


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = f"Admin Console: Validate default dedupe flags, retention rule, extended retention" \
                    f" schedule policy set on plan creation, retention on plans without override option enabled," \
                    f" deletion of copy - With Company Creation & Multi-region plans"
        self.browser = None
        self.admin_console = None
        self.plan_helper = None
        self.storage_helper = None
        self.primary_storage_name = None
        self.secondary_storage_name = None
        self.tertiary_storage_name = None
        self.quat_storage_name = None
        self.primary_backup_location = None
        self.secondary_backup_location = None
        self.tertiary_backup_location = None
        self.quat_backup_location = None
        self.primary_ddb_location = None
        self.secondary_ddb_location = None
        self.plan_name = None
        self.tcinputs = {
            "MediaAgent": None
        }
        self.extended_rules = None
        self.cipher_list = None
        self.cleanup_status = False
        self.tenant_admin = None
        self.company_name = None
        self.company_contact = None
        self.company_alias = None
        self.company_email = None
        self.company_user = None
        self.company_user_password = None
        self.company_creator_password = None
        self.region1 = '-(US) East US'   # Region name used as suffix for Storage Policy
        self.region2 = '-(US) West US'   # Region name used as suffix for Storage Policy

    def _get_storage_dedupe_flags(self, disk_storage_name):
        """
        To get default dedupe flags set on SIDB store of given disk storage
            Args:
             disk_storage_name (str) --  Name of the disk storage

            Returns:
                list    --  contains storage dedupeflags, extended flags
        """

        query = f"""SELECT	DDB.flags, DDB.ExtendedFlags
                    FROM	IdxSIDBStore DDB
                    JOIN	archGroupCopy AGC
                            ON	DDB.SIDBStoreId = AGC.SIDBStoreId
                    JOIN	archGroup AG
                            ON	AGC.archGroupId = AG.id
                    WHERE	AG.name = '{disk_storage_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)

        return self.csdb.fetch_one_row()

    def _get_storage_flags_not_set(self, dedupe_flag, extended_flag):
        """
        To know which all flags are not set that should be set by default on a storage
            Args:
             dedupe flag (int) --  storage dedupe flag

             extended_flag (int) -- storage extended flag

            Returns:
                None
        """

        if dedupe_flag & 2 == 0:
            self.log.error('SW_COMPRESSION flag is not set')
        if dedupe_flag & 16 == 0:
            self.log.error('GLOBAL_DEDUPE flag is not set')
        if dedupe_flag & 65536 == 0:
            self.log.error('STORE_DEDUPFACTOR_ENABLED flag is not set')
        if dedupe_flag & 131072 == 0:
            self.log.error('SECONDARY_FOLLOW_SOURCE_DEDUP_BLOCK flag is not set')
        if dedupe_flag & 1048576 == 0:
            self.log.error('SILO_PREPARED flag is not set')
        if dedupe_flag & 8388608 == 0:
            self.log.error('ENABLE_DDB_VALIDATION flag is not set')
        if dedupe_flag & 536870912 == 0:
            self.log.error('PRUNING_ENABLED flag is not set')
        if extended_flag & 2 == 0:
            self.log.error('DEFAULT Extended flag is not set')
        if extended_flag & 4 == 0:
            self.log.error('MARK_AND_SWEEP_ENABLED Extended flag is not set')
        if extended_flag & 8 == 0:
            self.log.error('ZEROREF_LOGGING_ENABLED Extended flag is not set')

    def _get_storage_flags_set(self, dedupe_flag, extended_flag):
        """
        To know which all dedupe flags are set that should not be set by default on a storage
            Args:
             dedupe flag (int) --  storage dedupe flag

             extended_flag (int) -- storage extended flag

            Returns:
                None
        """

        if dedupe_flag & 1 != 0:
            self.log.error('MULTI_TAG_HEADER flag is set')
        if dedupe_flag & 4 != 0:
            self.log.error('NONTRANS_DB flag is set')
        if dedupe_flag & 8 != 0:
            self.log.error('NO_SECONDARY_TABLE flag is set')
        if dedupe_flag & 32 != 0:
            self.log.error('SINGLE_THREAD_DB flag is set')
        if dedupe_flag & 64 != 0:
            self.log.error('SIDB_SUSPENDED flag is set')
        if dedupe_flag & 128 != 0:
            self.log.error('RECYCLABLE flag is set')
        if dedupe_flag & 256 != 0:
            self.log.error('SILO_AGED flag is set')
        if dedupe_flag & 512 != 0:
            self.log.error('DDB_COPYOP_INPROGRESS flag is set')
        if dedupe_flag & 1024 != 0:
            self.log.error('DDB_MOVEOP_INPROGRESS flag is set')
        if dedupe_flag & 2048 != 0:
            self.log.error('DDB_ARCHIVE_STATUS flag is set')
        if dedupe_flag & 4096 != 0:
            self.log.error('SIDB_ENGINE_RUNNING flag is set')
        if dedupe_flag & 8192 != 0:
            self.log.error('MEMDB_DDB flag is set')
        if dedupe_flag & 16384 != 0:
            self.log.error('OPTIMIZE_DB flag is set')
        if dedupe_flag & 32768 != 0:
            self.log.error('STORE_SEALED flag is set')
        if dedupe_flag & 2097152 != 0:
            self.log.error('SILO_ENABLED flag is set')
        if dedupe_flag & 4194304 != 0:
            self.log.error('DDB_VALIDATION_FAILED flag is set')
        if dedupe_flag & 16777216 != 0:
            self.log.error('DDB_UNDER_MAINTENANCE flag is set')
        if dedupe_flag & 33554432 != 0:
            self.log.error('DDB_NEEDS_AUTO_RESYNC flag is set')
        if dedupe_flag & 67108864 != 0:
            self.log.error('DDB_VERIFICATION_INPROGRESS flag is set')
        if dedupe_flag & 134217728 != 0:
            self.log.error('TIMESTAMP_MISMATCH flag is set')
        if dedupe_flag & 268435456 != 0:
            self.log.error('DDB_VERIFICATION_INPROGRESS_ALLOW_BACKUPS flag is set')
        if dedupe_flag & 1073741824 != 0:
            self.log.error('DDB_RESYNC_IN_PROGRESS flag is set')
        if dedupe_flag & 214748368 != 0:
            self.log.error('DDB_PRUNING_IN_PROGRESS flag is set')
        if extended_flag & 1 != 0:
            self.log.error('IDX_SIDBSTORE_EX_FLAGS_FULL extended flag is set')

    def _get_copy_dedupe_flag(self, plan_name, copy_name):
        """
        To get default dedupe flags set on archGroupCopy table of given plan and copy
            Args:
             plan_name (str) --  Name of the plan
             copy_name (str) -- Name of the copy

            Returns:
                int    --  given copy related dedupe flags
        """

        query = f"""SELECT AGC.dedupeFlags
                    FROM   archGroupCopy AGC
                    JOIN   archGroup AG
                           ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)

        return int(self.csdb.fetch_one_row()[0])

    def _get_copy_flags_not_set(self, dedupe_flag, copy_name):
        """
        To know which all dedupe flags are not set that should be set by default on a copy
            Args:
                dedupe_flag (int) : flags set on the given copy
                copy_name   (str) : name of the copy
            Returns:
                None
        """
        if dedupe_flag & 8 == 0:
            self.log.error('CVA_SIDB_RESILIENCY_ENABLED_FLAG flag is not set')
        if dedupe_flag & 262144 == 0:
            self.log.error('SIDB_STORE_ENABLED_FLAG flag is not set')
        if dedupe_flag & 524288 == 0 and copy_name == 'Primary':
            self.log.error('CLIENT_SIDE_DEDUP_FLAG flag is not set')
        if dedupe_flag & 8388608 == 0:
            self.log.error('USE_READLESS_MODE_DEDUP_FLAG flag is not set')
        if dedupe_flag & 33554432 == 0:
            self.log.error('RECONSTRUCT_SIDB_FROM_SNAPSHOT_FLAG flag is not set')
        if dedupe_flag & 67108864 == 0:
            self.log.error('AUTO_RECONSTRUCT_DEDUP_STORE_FLAG flag is not set')
        if dedupe_flag & 134217728 == 0:
            self.log.error('USE_GLOBAL_DEDUP_STORE_FLAG flag is not set')

    def _get_copy_flags_set(self, dedupe_flag, copy_name):
        """
        To know which all dedupe flags are set that should not be set by default on a copy
            Args:
                dedupe_flag (int) : flags set on the given copy
                copy_name   (str) : name of the copy
            Returns:
                None
        """

        if dedupe_flag & 2 != 0:
            self.log.error('ENABLE_SIGNATURE_BACKWARD_REF_FLAG flag is set')
        if dedupe_flag & 4 != 0:
            self.log.error('OPTIMIZE_HIGH_LATENCY_NETWORK_FLAG flag is set')
        if dedupe_flag & 131072 != 0:
            self.log.error('ENABLE_SIDB_ARCHIVE_FLAG flag is set')
        if dedupe_flag & 524288 == 0 and copy_name == 'Secondary':
            self.log.error('CLIENT_SIDE_DEDUP_FLAG flag  not set')
        if dedupe_flag & 1048576 != 0:
            self.log.error('DEDUP_INACTIVE_FLAG flag is set')
        if dedupe_flag & 2097152 != 0:
            self.log.error('BACKUP_SILO_ENABLED_FLAG flag is set')
        if dedupe_flag & 4194304 != 0:
            self.log.error('KEEP_ACTIVE_SILO_IN_CACHE_FLAG flag is set')
        if dedupe_flag & 16777216 != 0:
            self.log.error('ENABLE_SILO_DISK_SPACE_MANAGEMENT_FLAG flag is set')
        if dedupe_flag & 268435456 != 0:
            self.log.error('HOST_GLOBAL_DEDUP_STORE_FLAG flag is set')
        if dedupe_flag & 536870912 != 0:
            self.log.error('CLIENT_CACHE_DB_DIRTY_FLAG flag is set')
        if dedupe_flag & 1073741824 != 0:
            self.log.error('DASH_SOURCE_SIDE_DISK_CACHE_FLAG flag is set')

    def _get_retention_period(self, plan_name, copy_name):
        """
        To get retention set on copy from archAgingRule table for given plan and copy
        Args:
             plan_name (str) --  Name of the plan
             copy_name (str) -- Name of the copy

        Returns:
            int    --  retention days set on the copy
        """

        query = f"""SELECT	AGR.retentionDays
                    FROM	archAgingRule AGR
                    JOIN	archGroupCopy AGC
                            ON     AGR.copyId = AGC.id
                    JOIN	archGroup AG
                            ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return int(cur[0])
        raise Exception("Unable to fetch retention period")

    def _get_extended_retention_period(self, plan_name, copy_name):
        """
        To get extended retention days from archAgingRuleExtended table for given plan and copy
        Args:
            plan_name (str) --  Name of the plan
            copy_name (str) -- Name of the copy

        Returns:
            list    --  extended retention days list set on the copy
        """

        query = f"""SELECT	AGE.retentionDays
                    FROM	archAgingRuleExtended AGE
                    JOIN	archGroupCopy AGC
                            ON     AGE.copyId = AGC.id
                    JOIN	archGroup AG
                            ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        period_list = self.csdb.fetch_all_rows()
        if period_list:
            flat_period_list = [int(item) for sublist in period_list for item in sublist]
            return flat_period_list
        raise Exception("Unable to fetch extended retention days")

    def _get_extended_retention_rule(self, plan_name, copy_name):
        """
        To get extended retention rules from archAgingRuleExtended table for given plan and copy
        Args:
            plan_name (str) --  Name of the plan
            copy_name (str) -- Name of the copy

        Returns:
            list    --  extended retention rules list set on the copy
        """

        query = f"""SELECT	AGE.retentionRule
                    FROM	archAgingRuleExtended AGE
                    JOIN	archGroupCopy AGC
                            ON     AGE.copyId = AGC.id
                    JOIN	archGroup AG
                            ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        retention_rule_list = self.csdb.fetch_all_rows()
        if retention_rule_list:
            flat_rule_list = [int(item) for sublist in retention_rule_list for item in sublist]
            return flat_rule_list
        raise Exception("Unable to fetch extended retention rules")

    def _convert_ret_to_days(self, ret_periods, ret_units):
        """
        To convert retention period to days
        """
        ret_days = []
        for i, val in enumerate(ret_units):
            if val == 'Day(s)':
                ret_days.append(ret_periods[i])
            elif val == 'Week(s)':
                ret_days.append(ret_periods[i] * 7)
            elif val == 'Month(s)':
                days = 30
                months = ret_periods[i] - 1
                if months % 2 != 0:
                    days += ((months // 2) + 1) * 30
                else:
                    days += (months // 2) * 30
                days += (months // 2) * 31
                ret_days.append(days)
            else:
                ret_days.append(ret_periods[i] * 365)

        return ret_days

    def _get_full_cycles(self, plan_name, copy_name):
        """
        To get full cycles on copy from archAgingRule table for given plan and copy
        Args:
             plan_name (str) --  Name of the plan
             copy_name (str) -- Name of the copy

        Returns:
            int    --  full cycles set on the copy
        """
        query = f"""SELECT	AGR.fullCycles
                    FROM	archAgingRule AGR
                    JOIN	archGroupCopy AGC
                            ON     AGR.copyId = AGC.id
                    JOIN	archGroup AG
                            ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return int(cur[0])
        raise Exception("Unable to fetch fullCycles for the copy")

    def _validate_auxcopy_association(self, plan_name):
        """
        To validate if System Created Autocopy schedule(Auxiliary Copy) is associated to plan secondary copy
        Args:
             plan_name (str) --  Name of the plan

        Returns:
            True  --    if schedule is associated
            False --    if schedule is not associated
        """

        query = f"""SELECT	COUNT(1)
                    FROM	TM_AssocEntity AE
                    JOIN	archGroupCopy AGC
                            ON     AE.copyId = AGC.id
                    JOIN	archGroup AG
                            ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = 'Secondary'
                    AND		AE.taskId=9"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)

        if self.csdb.fetch_one_row()[0] == '0':
            return False
        return True

    def _check_override_flag(self, plan_name, copy_name):
        """
        To check if override flag is set or unset
        Args:
             plan_name (str) --  Name of the plan
             copy_name (str) --  Name of the copy

        Returns:
            True  --    if flag is set
            False --    if flag is not set
        """
        query = f"""SELECT extendedFlags &2048
                    FROM archGroupCopy AGC
                    JOIN	archGroup AG
                    ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{plan_name}'
                    AND     AGC.name = '{copy_name}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)

        if self.csdb.fetch_one_row()[0] == '2048':
            return True
        return False

    def verify_override_setting(self, plan_name, copy_name, expected_setting):
        """
        To verify override flag is set/unset as expected for a copy
        Args:
             plan_name (str) --  Name of the plan
             copy_name (str) --  Name of the copy
             expected_setting (bool) -- Whether override flag is expected to be set or unset
        """
        self.log.info(f'Verifying if override flag is set correctly for {plan_name}' \
                      f' and copy {copy_name}')

        if self._check_override_flag(plan_name, copy_name) == expected_setting:
            self.log.info(f'Override flag set correctly on copy {copy_name}')
        else:
            raise CVTestStepFailure(f'Override flag not set correctly on copy {copy_name}')

    def _validate_retention(self, plan_name, copy_name, ret_days):
        """
        Validate retention period on copy
        Args:
            plan_name (str) : Name of plan
            copy_name (str) : Name of copy policy
            ret_days (int) : Number of retention days set
        """
        retention_days = self._get_retention_period(plan_name, copy_name)
        full_cycles = self._get_full_cycles(plan_name, copy_name)
        if retention_days == ret_days:
            self.log.info(f'Retention days is correctly set on dependent {copy_name} copy')
        else:
            raise CVTestStepFailure(f'Retention days was not correctly set on dependent {copy_name} copy')

        if full_cycles == 1:
            self.log.info(f'Full Cycles is correctly set on dependent {copy_name} copy')
        else:
            raise CVTestStepFailure(f'Full Cycles was not correctly set on dependent {copy_name} copy')

    def _validate_extended_retention_rules(self,
                                           plan_name,
                                           copy_name,
                                           ret_periods,
                                           ret_units,
                                           ret_freqs):
        """
        Validate extended retention rules on copy
        Args:
            plan_name (str) : Name of plan
            copy_name (str) : Name of copy policy
            ret_periods (list of int) : Number of retention days set for each extended retention rule
            ret_units (list of string) : Units for extended retention rules
            ret_freqs (list of string) : Retention frequency used for each extended retention rule
        """
        retention_days_list = self._get_extended_retention_period(plan_name, copy_name)
        ret_period_in_days = self._convert_ret_to_days(ret_periods, ret_units)
        for i in range(len(retention_days_list)):
            if retention_days_list[i] == ret_period_in_days[i]:
                self.log.info(f'Extended retention days is set on dependent {copy_name} copy')
            else:
                raise CVTestStepFailure(f'Retention days was not correctly set on dependent {copy_name} copy')

        extended_rule_list = self._get_extended_retention_rule(plan_name, copy_name)
        self._check_retention_rules(extended_rule_list, ret_freqs)

    def validate_encryption_settings(self, pool, cipher, key_length):
        """
        Validate encryption settings on storage pool
        Args:
            pool (str)      :   Name of storage pool
            cipher (str)    :   Type of cipher used
            key_length (int):   key length of the cipher
        """
        query = f"""SELECT	AGC.encType, AGC.encKeyLen
                    FROM	archGroupCopy AGC
                    JOIN	archGroup AG
                    ON     AGC.archGroupId = AG.id
                    WHERE	AG.name = '{pool}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)

        enc_type, enc_keyLength = map(int, self.csdb.fetch_one_row())

        if cipher == '3-DES':
            if self.cipher_list(enc_type).name != 'DES3' and enc_keyLength != key_length:
                raise CVTestStepFailure(f'Encryption cipher not set correctly set for {pool}')
        elif cipher != self.cipher_list(enc_type).name and enc_keyLength != key_length:
            raise CVTestStepFailure(f'Encryption cipher not set correctly set for {pool}')

        self.log.info(f'Encryption settings sucessfully validated on pool: {pool}')

    def _check_retention_rules(self, extended_rules, ret_freqs):
        """
        To verify retention rules on copy
        """
        for i in range(len(extended_rules)):
            if ret_freqs[i] == 'All Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_ALLFULL:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            elif ret_freqs[i] == 'Hourly Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_HOUR:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            elif ret_freqs[i] == 'Daily Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_DAY:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            elif ret_freqs[i] == 'Weekly Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_WEEK:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            elif ret_freqs[i] == 'Monthly Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_MONTH:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            elif ret_freqs[i] == 'Quarterly Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_QUARTER:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            elif ret_freqs[i] == 'Half Yearly Fulls':
                if extended_rules[i] != self.extended_rules.EXTENDED_HALFYEAR:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
            else:
                if extended_rules[i] != self.extended_rules.EXTENDED_YEAR:
                    raise CVTestStepFailure(f'Extended Retention Rule not correctly set for {ret_freqs[i]}')
        self.log.info(f'Extended Retention Rules successfully set on copy')

    def init_tc(self):
        """Initial configuration for the test case"""

        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.company_user.name, self.company_user_password)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def cleanup(self):
        """To perform cleanup operation"""

        try:
            # To delete plan if exists
            self.log.info('Check for plan %s', self.plan_name)
            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info('Deletes plan %s', self.plan_name)
                self.plan_helper.validate_listing_plan_deletion(self.plan_name)
                self.log.info('Deleted plan %s', self.plan_name)
            else:
                self.log.info('No plan exists with name %s', self.plan_name)

            available_disk_storages = self.storage_helper.list_disk_storage()

            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.primary_storage_name)
            if self.primary_storage_name in available_disk_storages:
                self.log.info('Deletes storage %s', self.primary_storage_name)
                self.storage_helper.delete_disk_storage(self.primary_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.primary_storage_name)

            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.secondary_storage_name)
            if self.secondary_storage_name in available_disk_storages:
                self.log.info('Deletes storage %s', self.secondary_storage_name)
                self.storage_helper.delete_disk_storage(self.secondary_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.secondary_storage_name)

            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.tertiary_storage_name)
            if self.tertiary_storage_name in available_disk_storages:
                self.log.info('Deletes storage %s', self.tertiary_storage_name)
                self.storage_helper.delete_disk_storage(self.tertiary_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.tertiary_storage_name)

            # To delete disk storage if exists
            self.log.info('Check for storage %s', self.quat_storage_name)
            if self.quat_storage_name in available_disk_storages:
                self.log.info('Deletes storage %s', self.quat_storage_name)
                self.storage_helper.delete_disk_storage(self.quat_storage_name)
            else:
                self.log.info('No storage exists with name %s', self.quat_storage_name)

            self.commcell.refresh()
        except Exception as exp:
            raise CVTestStepFailure(f'Cleanup operation failed with error : {exp}')

    @test_step
    def create_entities(self):
        """To create required entities for test case"""

        ma_name = self.commcell.clients.get(self.tcinputs['MediaAgent']).display_name

        # To create a new disk storage
        self.log.info("Adding a new disk for primary storage: %s", self.primary_storage_name)
        self.storage_helper.add_disk_storage(
            self.primary_storage_name,
            ma_name,
            self.primary_backup_location,
            deduplication_db_location=self.primary_ddb_location)

        self.log.info("Adding a new disk for secondary storage: %s", self.secondary_storage_name)
        self.storage_helper.add_disk_storage(
            self.secondary_storage_name,
            ma_name,
            self.secondary_backup_location,
            deduplication_db_location=self.secondary_ddb_location)

        self.log.info("Adding a new disk for tertiary storage: %s", self.tertiary_storage_name)
        self.storage_helper.add_disk_storage(
            self.tertiary_storage_name,
            ma_name,
            self.tertiary_backup_location)

        self.log.info("Adding a new disk for quaternary storage: %s", self.quat_storage_name)
        self.storage_helper.add_disk_storage(
            self.quat_storage_name,
            ma_name,
            self.quat_backup_location)

        # To create a new plan
        self.log.info("Adding a new plan: %s", self.plan_name)
        self.plan_helper.add_plan()
        self.log.info("successfully created plan: %s", self.plan_name)
        # Validate retention periods set on the copies
        self.log.info("Validating retention on Primary copy")
        self._validate_retention(self.plan_name + self.region1, 'Primary', 10)
        self.log.info("Validating retention on Secondary copy")
        self._validate_retention(self.plan_name + self.region1, 'Secondary', 12)
        # Verify override flag setting on copies
        self.log.info("Verifying override retention flag on copies")
        self.verify_override_setting(self.plan_name + self.region1, 'Primary', True)
        self.verify_override_setting(self.plan_name + self.region1, 'Secondary', True)

    @test_step
    def check_dedupe_flags(self):
        """ To validate all default dedupe flags on storage and plan"""

        # To validate if default dedupe flags are set or not on the primary disk storage.
        self.log.info("Validate if default dedupe flags are set or not on primary disk storage: %s",
                      self.primary_storage_name)
        dedupe_flag, extended_flag = map(int, self._get_storage_dedupe_flags(self.primary_storage_name))
        if dedupe_flag == 546504722 and extended_flag == 14:
            self.log.info('All the default dedupe flags are set on primary disk storage')
            self.log.info("Validation for default dedupe flags on primary disk storage: %s was successful",
                          self.primary_storage_name)
        else:
            self._get_storage_flags_not_set(dedupe_flag, extended_flag)
            self._get_storage_flags_set(dedupe_flag, extended_flag)
            raise CVTestStepFailure('The default dedupe flags are incorrectly set on  primary disk storage')

        # To validate if default dedupe flags are set or not on the secondary disk storage.
        self.log.info("Validate if default dedupe flags are set or not on secondary disk storage: %s",
                      self.secondary_storage_name)
        dedupe_flag, extended_flag = map(int, self._get_storage_dedupe_flags(self.secondary_storage_name))
        if dedupe_flag == 546504722 and extended_flag == 14:
            self.log.info('All the default dedupe flags are set on secondary disk storage')
            self.log.info("Validation for default dedupe flags on secondary disk storage: %s was successful",
                          self.secondary_storage_name)
        else:
            self._get_storage_flags_not_set(dedupe_flag, extended_flag)
            self._get_storage_flags_set(dedupe_flag, extended_flag)
            raise CVTestStepFailure('The default dedupe flags are incorrectly set on secondary disk storage')

        # To validate if default dedupe flags are set or not on dependent primary copy.
        self.log.info("Validate if default dedupe flags are set or not on dependent primary copy of %s",
                      self.plan_name)
        dedupe_flag = self._get_copy_dedupe_flag(self.plan_name + self.region1, 'Primary')
        if dedupe_flag == 244056072:
            self.log.info('All the default dedupe flags are set on dependent primary copy')
            self.log.info("Validation for default dedupe flags on dependent primary copy of %s was successful",
                          self.plan_name + self.region1)
        else:
            self._get_copy_flags_not_set(dedupe_flag, 'Primary')
            self._get_copy_flags_set(dedupe_flag, 'Primary')
            raise CVTestStepFailure('The default dedupe flags are incorrectly set on dependent primary copy')

        # To validate if default dedupe flags are set or not on dependent secondary copy.
        self.log.info("Validate if default dedupe flags are set or not on dependent secondary copy of %s",
                      self.plan_name)
        dedupe_flag = self._get_copy_dedupe_flag(self.plan_name + self.region1, 'Secondary')
        if dedupe_flag == 243531784:
            self.log.info('All the default dedupe flags are set on dependent secondary copy')
            self.log.info("Validation for default dedupe flags on dependent secondary copy of %s was successful",
                          self.plan_name + self.region1)
        else:
            self._get_copy_flags_not_set(dedupe_flag, 'Secondary')
            self._get_copy_flags_set(dedupe_flag, 'Secondary')
            raise CVTestStepFailure('The default dedupe flags are incorrectly set on dependent secondary copy')

    # Modify retention period and validate
    @test_step
    def modify_retention(self):
        """
        To modify retention on copies and validate the same
        """
        self.plan_helper.modify_retention_on_copy(plan_name=self.plan_name,
                                                  copy_name='Primary',
                                                  ret_days=25,
                                                  ret_unit='Day(s)',
                                                  region=self.plan_helper.regions[0])
        self._validate_retention(self.plan_name + self.region1, 'Primary', 25)
        self.plan_helper.modify_retention_on_copy(plan_name=self.plan_name,
                                                  copy_name='Secondary',
                                                  ret_days=32,
                                                  ret_unit='Day(s)',
                                                  region=self.plan_helper.regions[0])
        self._validate_retention(self.plan_name + self.region1, 'Secondary', 32)

    # Modify extended retention rules and validate
    @test_step
    def modify_extended_retention_rules(self):
        """
        To modify extended retention rules for a copy and validate the same
        """
        ret_periods_1 = [60, 15, 5]
        ret_units_1 = ['Day(s)', 'Week(s)', 'Month(s)']
        ret_freqs_1 = ['Monthly Fulls', 'Quarterly Fulls', 'Yearly Fulls']
        self.plan_helper.modify_extended_retention_on_copy(self.plan_name,
                                                           'Primary',
                                                           3,
                                                           ret_periods_1,
                                                           ret_units_1,
                                                           ret_freqs_1,
                                                           self.plan_helper.regions[0]
                                                           )

        self._validate_extended_retention_rules(self.plan_name + self.region1,
                                                'Primary',
                                                ret_periods_1,
                                                ret_units_1,
                                                ret_freqs_1)
        ret_periods_2 = [70, 8, 2]
        ret_units_2 = ['Day(s)', 'Month(s)', 'Year(s)']
        ret_freqs_2 = ['Weekly Fulls', 'Monthly Fulls', 'Yearly Fulls']
        self.plan_helper.modify_extended_retention_on_copy(self.plan_name,
                                                           'Secondary',
                                                           3,
                                                           ret_periods_2,
                                                           ret_units_2,
                                                           ret_freqs_2,
                                                           self.plan_helper.regions[0]
                                                           )
        self._validate_extended_retention_rules(self.plan_name + self.region1,
                                                'Secondary',
                                                ret_periods_2,
                                                ret_units_2,
                                                ret_freqs_2)

    @test_step
    def check_auxcopy_schedule(self):
        """To validate System Created Autocopy schedule(Auxiliary Copy) is associated to plan secondary copy"""

        if self._validate_auxcopy_association(self.plan_name + self.region1):
            self.log.info("System Created Autocopy schedule(Auxiliary Copy) is associated to dependent"
                          " secondary copy of %s was successful", self.plan_name)
        else:
            raise CVTestStepFailure('System Created Autocopy schedule(Auxiliary Copy) is not associated to plan '
                                    'secondary copy')

    @test_step
    def delete_copy(self):
        """ To delete a copy of a plan """

        self.log.info("Deleting copy")
        try:
            self.plan_helper.delete_copy_and_validate(self.plan_name, 'Secondary', self.plan_helper.regions[0])
        except Exception as exp:
            raise CVTestStepFailure(f'Delete copy operation failed with error : {exp}')

        self.log.info("Successfully Deleted Copy")

    @test_step
    def encrypt_disk_storage_and_validate(self):
        """
        To enable encryption on storage pool and validate encryption
        """
        ciphers_dict = {'3-DES': [192],
                        'BlowFish': [128, 256],
                        'AES': [128, 256],
                        'GOST': [256],
                        'Serpent': [128, 256],
                        'TwoFish': [128, 256]
                        }
        cipher, keylength_list = random.choice(list(ciphers_dict.items()))
        key_length = random.choice(keylength_list)
        self.storage_helper.encrypt_disk_storage(self.primary_storage_name, cipher, key_length)
        self.validate_encryption_settings(self.primary_storage_name, cipher, key_length)

    def setup(self):
        """Initializes pre-requisites for this test case"""

        # Generate the company name and alias
        ran = random.randint(1, 100)
        self.company_email = f"TestAutomation{ran}@commvault.com"
        self.company_name = 'TestAutomationCompany1'
        self.company_contact = self.company_name + "_Contact"
        self.company_alias = self.company_name
        # Create Company and company user
        self.log.info("Deleting Company")
        if self.commcell.organizations.has_organization(self.company_name):
            self.commcell.organizations.delete(self.company_name)
        self.commcell.users.refresh()
        self.log.info("Creating Company")
        self.company_creator_password = self.inputJSONnode['commcell']['commcellPassword']
        self.company_user_password = str(self.tcinputs.get('TenantUserPassword', self.company_creator_password))
        # Create Organization
        self.organization_helper = OrganizationHelper(self.commcell)
        self.organization_helper.create(name=self.company_name,
                                        email=self.company_email,
                                        contact_name=self.company_contact,
                                        company_alias=self.company_alias)
        # Set company properties to show storage option in navigation pane
        company_properties = {"general": {"infrastructureType": "RENTED_AND_OWN_STORAGE"}}
        self.organization_helper.edit_company_properties(company_properties)
        # Associate clients to Company User
        self.commcell.refresh()
        self.company_user = self.commcell.users.get(self.company_alias + "\\" + self.company_email.split("@")[0])
        self.company_user.update_user_password(new_password=self.company_user_password,
                                          logged_in_user_password=self.company_creator_password)

        self.log.info("Associate clients and media agents to company")
        self.company_clients = {"assoc1": {"clientName": [self.tcinputs['ClientName']],
                                           "mediaAgentName": [self.tcinputs['MediaAgent']],
                                           "role": ["Tenant Admin"]}}
        self.company_user.update_security_associations(entity_dictionary=self.company_clients,
                                                       request_type="UPDATE")
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")
        self.init_tc()
        self.plan_helper = PlanMain(self.admin_console, csdb=self.csdb, commcell=self.commcell)
        self.storage_helper = StorageMain(self.admin_console)
        options_selector = OptionsSelector(self.commcell)
        time_stamp = options_selector.get_custom_str()
        self.primary_storage_name = str(self.id) + 'PrimaryDisk'
        self.secondary_storage_name = str(self.id) + 'SecondaryDisk'
        self.tertiary_storage_name = str(self.id) + 'TertiaryDisk'
        self.quat_storage_name = str(self.id) + 'QuatDisk'
        ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])
        self.plan_helper.storage = {'pri_storage': self.primary_storage_name, 'pri_ret_period': '10',
                                    'sec_storage': self.secondary_storage_name, 'sec_ret_period': '15',
                                    'ter_storage': self.tertiary_storage_name, 'ter_ret_period': '12',
                                    'quat_storage': self.quat_storage_name, 'quat_ret_period': '17',
                                    'ret_unit': 'Day(s)'}
        self.plan_name = "%s_Plan" % str(self.id)
        self.plan_helper.plan_name = {"server_plan": self.plan_name}
        self.plan_helper.sec_copy_name = 'Secondary'
        self.plan_helper.backup_data = None
        self.plan_helper.backup_day = None
        self.plan_helper.backup_duration = None
        self.plan_helper.rpo_hours = None
        self.plan_helper.allow_override = None
        self.plan_helper.database_options = None
        self.plan_helper.selective = 'Weekly Fulls'
        self.plan_helper.regions = ['eastus', 'westus']     # Region name as displayed on Command Center
        self.plan_helper.modify_retention = True
        self.plan_helper.specify_date = True
        self.extended_rules = ExtendedRules
        self.cipher_list = CipherList

        # To select drive with space available in MA machine
        self.log.info('Selecting drive in the MA machine based on space available')
        ma_drive = options_selector.get_drive(ma_machine, size=5 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)
        self.primary_backup_location = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP_Primary')
        self.secondary_backup_location = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP_Secondary')
        self.tertiary_backup_location = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP_Tertiary')
        self.quat_backup_location = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP_Quat')
        self.primary_ddb_location = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB_Primary_%s' %
                                                         time_stamp)
        self.secondary_ddb_location = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB_Secondary_%s'
                                                           % time_stamp)

    def run(self):
        """Main function for test case execution"""

        try:
            self.cleanup()
            self.create_entities()
            self.modify_retention()
            self.modify_extended_retention_rules()
            self.check_dedupe_flags()
            self.check_auxcopy_schedule()
            self.delete_copy()
            self.encrypt_disk_storage_and_validate()
        except Exception as exp:
            handle_testcase_exception(self, exp)
            self.cleanup_status = True
        else:
            self.cleanup()
        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear Down Function of this Case"""
        try:
            self.log.info("This is Tear Down method")
            self.log.info("Deleting Company")
            if self.commcell.organizations.has_organization(self.company_name):
                self.commcell.organizations.delete(self.company_name)
            self.commcell.users.refresh()
            if self.commcell.users.has_user(self.company_user.name):
                self.log.error("Error: User exists after company deletion")
                raise Exception("Company user exists after company deletion")
            if self.cleanup_status:
                self.log.info('Check for plan %s', self.plan_name)
                if self.commcell.plans.has_plan(self.plan_name):
                    self.log.error(f"Error: Plan {self.plan_name} exists after company deletion")
                    raise Exception("Plan exists after company deletion")
            self.log.info("Deleting storage pools")
            if self.commcell.storage_pools.has_storage_pool(self.primary_storage_name):
                self.log.error(f"Error: Storage {self.primary_storage_name} exists after company deletion")
                raise Exception("Company user exists after company deletion")
            if self.commcell.storage_pools.has_storage_pool(self.secondary_storage_name):
                self.log.error(f"Error: Storage {self.secondary_storage_name} exists after company deletion")
                raise Exception("Storage exists after company deletion")
            if self.commcell.storage_pools.has_storage_pool(self.tertiary_storage_name):
                self.log.error(f"Error: Storage {self.tertiary_storage_name} exists after company deletion")
                raise Exception("Storage exists after company deletion")
            if self.commcell.storage_pools.has_storage_pool(self.quat_storage_name):
                self.log.error(f"Error: Storage {self.quat_storage_name} exists after company deletion")
                raise Exception("Storage exists after company deletion")
            self.log.info("All storage pools have been deleted")
            self.log.info("Cleaned up all entities")

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")

