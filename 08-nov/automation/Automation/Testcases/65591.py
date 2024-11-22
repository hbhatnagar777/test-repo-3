# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Acceptance of Compliance Lock using air_gap_protect storage - Java

Pre-requisite- Air Gap Protect License should be already applied and active on CS.
***Primary copy can be created only using "HOT", for this testcase to run, "HOT" License Type should be used ***

TestCase: Class for executing this test case

    __init__()      -- Initializes test case class object

    setup()         -- Setup function of this test case

    delete_policy_pool() -- Deletes pool and policy

    cleanup() -- cleanup Function of this Case

    tear_down() -- Tear Down Function of this Case

    worm_settings_disabled() -- Checks if worm settings are disabled or not

    check_policy_settings() -- Checks for compliance lock and override retention flag set on policy

    check_retention_settings() -- Checks if retention rules are applied as expected

    run() -- run function of this Testcase

Sample Input JSON:
        "65591": {
            "ClientName": name of client (str),
            "MediaAgent": name of Media Agent (str),
            "region_name": location (str) (same as displayed over UI),
            "storage_type": name of the cloud vendor (str, eg - "Microsoft Azure storage") (same as UI)
            "storage_class": storage class (str, eg - "Hot","Cool") (same as UI)

Steps:
    A. Case1:
        i.   Create a non-dedupe air_gap_protect storage
        ii.  Try to enable H/w WORM lock, we should get an error and no setting should be enabled i.e. micro pruning is
             ON, retention not set on pool.
        iii.    A. For SP<32 Enable compliance lock on pool, it should be successful
                B. For SP>=32 Validate compliance lock is enabled by default
        iv.  Pool should not ask for retention and no setting should be enabled i.e. micro pruning is ON, retention not
             set on pool.
        v.   Associate a copy to the air_gap_protect pool
            1. Copy should have WORM copy flag set
            2. Retention override flag should be set
            3. Retention is considered from dependent copy, say set retention as 1d
            4. Try increasing retention to 7 days, it should be successful
            5. Try reducing basic retention from 7 to 5 Days, it should return error
            6. Try increasing retention to 10 d it should be successful as well.
            6. Try setting extended retention (12 d), it should be successful
            7. Try reducing extended retention (10 d) it should return error
            9. Try increasing extended retention (15 d) it should be successful.

    B. Case2:
        i.    Create a dedupe air_gap_protect storage pool
        ii.   Associate a copy to the air_gap_protect pool
        iii.  Try to enable H/w WORM lock, we should get an error and no setting should be enabled i.e. micro pruning is
              ON, seal frequency  not set, retention not set on pool.
        iv.     A. For SP<32 Enable compliance lock on pool, it should be successful
                B. For SP>=32 Validate compliance lock is enabled by default.
        v.    Pool should not ask for retention and no setting should be enabled i.e. micro pruning is ON, seal
              frequency  not set, retention not set on pool.
        vi.   Create another storage plan using disk storage for primary copy
        vii.  Associate a secondary copy on new SP to air_gap_protect pool and see compliance lock is ON, retention pass as 1D
        viii. On the secondary copy associated to the air_gap_protect pool
            1. Retention override flag should be set
            2. Retention is considered from dependent copy, say set retention as 1d
            3. Try increasing retention to 7 days, it should be successful
            4. Try reducing basic retention from 7 to 5 Days, it should return error
            5. Try increasing retention to 10 d it should be successful as well.
            6. Try setting extended retention (12 d), it should be successful
            7. Try reducing extended retention (10 d) it should return error
            8. Try increasing extended retention (15 d) it should be successful.


"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()

        self.name = "Acceptance of Compliance Lock using air_gap_protect storage - Java"
        self.mm_helper = None
        self.ma_machine = None
        self.tcinputs = {
            "ClientName": None,
            "MediaAgent": None,
            "region_name": None,
            "storage_type": None,
            "storage_class": None
        }
        self.cs_version = None
        self.cs_oem_id = None
        self.partition_path = None

        self.dedupe_storage = None
        self.dedupe_storage_sec = None
        self.non_dedupe_storage = None
        self.dedupe_disk_storage = None

        self.disk_storage_policy = None
        self.dedupe_policy = None
        self.non_dedupe_policy = None
        self.secondary_air_gap_protect_copy = None

        self.disk_mountPath = None
        self.disk_ddb = None

    def setup(self):
        """Setup function of this test case"""

        self.cs_oem_id = int(self.commcell.commserv_oem_id)
        # check whether CS is a commvault OEM or not
        if self.cs_oem_id != 1:
            raise Exception("Failing testcase as CS provided is not a commvault OEM")

        self.cs_version = int(self.commcell.commserv_version)
        self.mm_helper = MMHelper(self)
        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgent'])
        ma_drive = options_selector.get_drive(self.ma_machine)

        if ma_drive is None:
            raise Exception("No free space on media agent")
        self.log.info('selected drive: %s', ma_drive)
        self.disk_mountPath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'Disk_backup_loc')
        self.disk_ddb = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'Disk_DDB')

        if self.tcinputs.get("PartitionPath") is not None:
            self.partition_path = self.tcinputs['PartitionPath']
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("Please provide LVM enabled DDB partition as input for Unix MA!..")
            self.log.info('Selecting drive in the Media agent machine based on space available')
            self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'air_gap_protect_DDB')
        self.log.info('selected ddb location : %s', self.partition_path)

        self.dedupe_storage = f"air_gap_protect-dedupe-{self.id}"
        self.dedupe_storage_sec = f"air_gap_protect-dedupe-sec-{self.id}"
        self.dedupe_policy = f"air_gap_protect-dedupe-policy-{self.id}"
        self.secondary_air_gap_protect_copy = f"air_gap_protect-secondary-{self.id}"
        self.non_dedupe_storage = f"air_gap_protect-non-dedupe-{self.id}"
        self.non_dedupe_policy = f"air_gap_protect-non-dedupe-policy-{self.id}"
        self.dedupe_disk_storage = f"disk-dedupe-{self.id}"
        self.disk_storage_policy = f"disk-dedupe-policy-{self.id}"

    def delete_policy_pool(self, policy=None, pool=None):
        """Deletes pool/policy

            Args:
                policy - name of the policy to be deleted

                pool - name of the pool to be deleted
        """

        if policy and self.commcell.storage_policies.has_policy(policy):
            self.log.info(f"Deleting Storage Policy: {policy}")
            self.commcell.storage_policies.delete(policy)
            self.log.info(f"Deleted Storage Policy: {policy}")

        if pool and self.commcell.storage_pools.has_storage_pool(pool):
            self.log.info(f"Deleting Storage Pool: {pool}")
            self.commcell.storage_pools.delete(pool)
            self.log.info(f"Deleted Storage Pool: {pool}")

    def cleanup(self):
        """cleanup Function of this Case"""

        try:
            self.log.info("*****CLEANUP STARTED*****")

            if self.commcell.storage_policies.has_policy(self.disk_storage_policy):
                sp_obj = self.commcell.storage_policies.get(self.disk_storage_policy)
                if sp_obj.has_copy(self.secondary_air_gap_protect_copy):
                    self.log.info(f"Deleting secondary storage policy copy: {self.secondary_air_gap_protect_copy}")
                    sp_obj.delete_secondary_copy(self.secondary_air_gap_protect_copy)
                    self.log.info(f"Deleted secondary storage policy copy: {self.secondary_air_gap_protect_copy}")

            self.delete_policy_pool(policy=self.disk_storage_policy, pool=self.dedupe_disk_storage)
            self.delete_policy_pool(pool=self.dedupe_storage_sec)
            self.delete_policy_pool(policy=self.dedupe_policy, pool=self.dedupe_storage)
            self.delete_policy_pool(policy=self.non_dedupe_policy, pool=self.non_dedupe_storage)

            self.log.info("*****CLEANUP COMPLETED*****")

        except Exception as exp:
            self.log.error(f"Error during cleanup: {exp}")
            raise Exception(f"Error during cleanup: {exp}")

    def tear_down(self):
        """Tear Down Function of this Case"""

        if self.status != constants.FAILED:
            self.cleanup()
            self.log.info(f"RESULT of this testcase: {self.status}")
        else:
            self.log.error("Required manually cleanup of created entities")

    def worm_settings_disabled(self, lib, pool, dedup=True):
        """Checks if worm settings are disabled or not

            Args:
                lib - library object to check worm settings on

                pool - pool object to check worm settings on

                dedup - True , in case the provided pool is dedupe

            Returns - True if all worm settings are disabled

        """

        if dedup:
            # check no seal frequency is set on dedupe pool
            primary_copy_obj = pool.get_copy()
            if self.mm_helper.get_copy_store_seal_frequency(primary_copy_obj)['days'] == 0:
                self.log.info("No seal frequency is set on dedupe pool")
            else:
                self.log.info("Seal frequency is set on dedupe pool")
                return False

        # check micro pruning is on or not
        if lib.advanced_library_properties['MountPathList'][0]['mountPathSummary']['attribute'] & 32 == 32:
            self.log.info("Micro pruning is enabled")
        else:
            self.log.info("Micro pruning is disabled")
            return False

        # check retention on pool
        if pool.storage_pool_properties['storagePoolDetails']['copyInfo']['retentionRules']['retainBackupDataForDays'] == -1:
            self.log.info("Retention not set on pool")
        else:
            self.log.info("Retention set on pool")
            return False

        return True

    def check_policy_settings(self, policy_obj, copy_name):
        """Checks for compliance lock and override retention flag set on policy

            Args:
                policy_obj - policy object to check settings on

                copy_name - name of the policy copy to check settings on (Primary/Copy-2)

        """

        policy_obj.refresh()
        primary_copy_obj = policy_obj.get_copy(copy_name)
        if primary_copy_obj.is_compliance_lock_enabled:
            self.log.info("Compliance lock is enabled on policy")
        else:
            raise Exception("Compliance lock is not enabled on policy")

        if primary_copy_obj.override_pool_retention:
            self.log.info("Override retention of pool is enabled on policy")
        else:
            raise Exception("Override retention of pool is not enabled on policy")

    def check_retention_settings(self, policy_obj, copy_name):
        """Checks if retention rules are applied as expected

            Args:
                policy_obj - policy object to check settings on

                copy_name - name of the policy copy to check settings on (Primary/Copy-2)

        """

        copy_obj = policy_obj.get_copy(copy_name)
        copy_obj.copy_retention = (1, 1, -1)
        self.log.info("Retention on dependent copy set to 1 day")

        # checked on pool, it was -1
        # Try increasing retention to 7 days, it should be successful
        copy_obj.copy_retention = (7, 1, -1)
        self.log.info("Retention on dependent copy increased to 7 days")

        # Try reducing basic retention from 7 to 5 Days, it should return error
        try:
            copy_obj.copy_retention = (5, 1, -1)
            self.log.error("Retention on dependent copy was reduced")
            raise Exception("Retention on dependent copy should not be reduced")
        except Exception as exp:
            self.log.info("As expected, Retention on dependent copy cannot be reduced : %s", exp)

        # Try increasing retention to 10 days, it should be successful
        copy_obj.copy_retention = (10, 1, -1)
        self.log.info("Retention on dependent copy increased to 10 days")

        # Try setting extended retention (12 d), it should be successful
        copy_obj.extended_retention_rules = [1, True, "EXTENDED_ALLFULL", 12, 0]
        self.log.info("Extended retention on dependent copy set to 12 days")

        # Try reducing extended retention (10 d) it should return error
        try:
            copy_obj.extended_retention_rules = [1, True, "EXTENDED_ALLFULL", 10, 0]
            self.log.error("Retention on dependent copy was reduced")
            raise Exception("Retention on dependent copy should not be reduced")
        except Exception as exp:
            self.log.info("As expected, Extended Retention on dependent copy cannot be reduced : %s", exp)

        # Try setting extended retention (15 d), it should be successful
        copy_obj.extended_retention_rules = [1, True, "EXTENDED_ALLFULL", 15, 0]
        self.log.info("Extended retention on dependent copy set to 15 days")

    def run(self):
        """run function of this Testcase"""

        try:
            self.cleanup()

            # Creating air gap storages early - allows time for it to come online
            # Create a non dedupe air_gap_protect storage pool
            non_dedupe_pool_obj, non_dedupe_lib_obj = self.mm_helper.configure_air_gap_protect_pool(
                storage_pool_name=self.non_dedupe_storage, media_agent=self.tcinputs["MediaAgent"],
                storage_type=self.tcinputs["storage_type"], storage_class=self.tcinputs["storage_class"],
                region_name=self.tcinputs["region_name"])

            # Create a dedupe air_gap_protect storage pool
            dedupe_pool_obj, dedupe_lib_obj = self.mm_helper.configure_air_gap_protect_pool(
                storage_pool_name=self.dedupe_storage, media_agent=self.tcinputs["MediaAgent"],
                storage_type=self.tcinputs["storage_type"], storage_class=self.tcinputs["storage_class"],
                region_name=self.tcinputs["region_name"], ddb_ma=self.tcinputs["MediaAgent"],
                ddb_path=self.partition_path)

            dedupe_pool_obj_sec, dedupe_lib_obj_sec = self.mm_helper.configure_air_gap_protect_pool(
                storage_pool_name=self.dedupe_storage_sec, media_agent=self.tcinputs["MediaAgent"],
                storage_type=self.tcinputs["storage_type"], storage_class=self.tcinputs["storage_class"],
                region_name=self.tcinputs["region_name"], ddb_ma=self.tcinputs["MediaAgent"],
                ddb_path=self.partition_path)

            self.log.info("************Case 1 execution starts*************")

            # Checking if the AGP storage is online or not
            self.log.info(f"Checking if the AGP storage {self.non_dedupe_storage} is online or not")
            self.mm_helper.wait_for_online_status_air_gap_protect(non_dedupe_pool_obj)

            successful_attempt = False
            # Try to enable H/w WORM lock, we should get an error
            try:
                self.mm_helper.enable_worm_storage_lock(non_dedupe_pool_obj, 1)
                successful_attempt = True
            except Exception as ex:
                self.log.info(f"Expected error - {ex}")

            if successful_attempt:
                raise Exception(f"Enabling worm lock should throw an error (air_gap_protect) {self.non_dedupe_storage}")

            if not self.worm_settings_disabled(dedup=False, lib=non_dedupe_lib_obj, pool=non_dedupe_pool_obj):
                raise Exception(f"Raising error because no worm setting should be enabled")
            else:
                self.log.info("As expected, no worm setting is enabled")

            if self.cs_version < 32:
                self.log.info(f"Enabling compliance lock as CS version < 32, {self.cs_version}")
                non_dedupe_pool_obj.enable_compliance_lock()

            if non_dedupe_pool_obj.is_compliance_lock_enabled:
                self.log.info(f"Compliance lock is enabled on {self.non_dedupe_storage}")
            else:
                error = f"Compliance lock is not enabled on {self.non_dedupe_storage}"
                self.log.error(error)
                raise Exception(error)

            if not self.worm_settings_disabled(dedup=False, lib=non_dedupe_lib_obj, pool=non_dedupe_pool_obj):
                raise Exception(f"Raising error because no worm setting should be enabled")
            else:
                self.log.info("As expected, no worm setting is enabled")

            # Associate a copy to the air_gap_protect non dedupe pool
            non_dedupe_policy_obj = self.mm_helper.configure_storage_policy(storage_policy_name=self.non_dedupe_policy,
                                                                            storage_pool_name=self.non_dedupe_storage,
                                                                            retention_period=1)

            self.check_policy_settings(non_dedupe_policy_obj, copy_name='Primary')
            self.check_retention_settings(policy_obj=non_dedupe_policy_obj,
                                          copy_name='Primary')

            self.log.info("************Case 1 execution completed*************")

            self.log.info("************Case 2 execution starts*************")

            # Checking if the AGP storage is online or not
            self.log.info(f"Checking if the AGP storage {self.dedupe_storage} is online or not")
            self.mm_helper.wait_for_online_status_air_gap_protect(dedupe_pool_obj)

            # Associate a copy to the air_gap_protect pool
            dedupe_policy_obj = self.mm_helper.configure_storage_policy(storage_policy_name=self.dedupe_policy,
                                                                        storage_pool_name=self.dedupe_storage)
            successful_attempt = False
            # Try to enable H/w WORM lock, we should get an error
            try:
                self.mm_helper.enable_worm_storage_lock(dedupe_pool_obj, 1)
                successful_attempt = True
            except Exception as ex:
                self.log.info(f"Expected error - {ex}")

            if successful_attempt:
                raise Exception(f"Enabling worm lock should throw an error (air_gap_protect) {self.dedupe_storage}")

            if not self.worm_settings_disabled(dedup=True, lib=dedupe_lib_obj, pool=dedupe_pool_obj):
                raise Exception(f"Raising error because no worm setting should be enabled")
            else:
                self.log.info("As expected, no worm setting is enabled")

            if self.cs_version < 32:
                self.log.info(f"Enabling compliance lock as CS version < 32, {self.cs_version}")
                dedupe_pool_obj.enable_compliance_lock()

            if dedupe_pool_obj.is_compliance_lock_enabled:
                self.log.info(f"Compliance lock is enabled on {self.dedupe_storage}")
            else:
                error = f"Compliance lock is not enabled on {self.dedupe_storage}"
                self.log.error(error)
                raise Exception(error)

            if not self.worm_settings_disabled(dedup=True, lib=dedupe_lib_obj, pool=dedupe_pool_obj):
                raise Exception(f"Raising error because no worm setting should be enabled")
            else:
                self.log.info("As expected, no worm setting is enabled")

            self.log.info("*****Creating dedupe disk storage*****")
            dedupe_disk_obj, disk_lib_obj = self.mm_helper.configure_storage_pool(
                storage_pool_name=self.dedupe_disk_storage, media_agent=self.tcinputs["MediaAgent"],
                mount_path=self.disk_mountPath, ddb_ma=self.tcinputs["MediaAgent"],
                ddb_path=self.disk_ddb)

            # Create another storage plan using disk storage for primary copy
            disk_policy_obj = self.mm_helper.configure_storage_policy(storage_policy_name=self.disk_storage_policy,
                                                                      storage_pool_name=self.dedupe_disk_storage,
                                                                      retention_period=1)

            # Checking if the AGP storage is online or not
            self.log.info(f"Checking if the AGP storage {self.dedupe_storage_sec} is online or not")
            self.mm_helper.wait_for_online_status_air_gap_protect(dedupe_pool_obj_sec)

            # Associate a secondary copy on new SP to air_gap_protect pool
            air_gap_protect_sec_policy_obj = self.mm_helper.configure_secondary_copy(
                sec_copy_name=self.secondary_air_gap_protect_copy,
                storage_policy_name=self.disk_storage_policy,
                global_policy_name=self.dedupe_storage_sec,
                retention_period=1)

            self.check_policy_settings(disk_policy_obj, self.secondary_air_gap_protect_copy)
            self.check_retention_settings(policy_obj=disk_policy_obj,
                                          copy_name=self.secondary_air_gap_protect_copy)

            self.log.info("************Case 2 execution completed*************")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
