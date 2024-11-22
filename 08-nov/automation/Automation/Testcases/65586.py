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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  teardown function of this test case

    _cleanup()      --  cleanup the entities created

    dedupe_worm_validation() -- validate WORM lock configuration on dedupe pool

Design Steps:
    Case1:
        1. Create a storage pool with deduplication enabled
        2. Enable H/w worm, set retention of 1 day.
        3. Check DB for the worm copy flag, storage is marked with bucket lock flag, micro pruning is disabled and seal frequency is set as per retention on pool ( in this case it should be 7 days).
        4. Create first copy associated to the pool.
        5. Ensure copy creation is successful, worm copy flag is set and override retention is not set on the copy.
    Case2:
        1. Create a storage pool with deduplication enabled
        2. Associate a copy to it and set retention value of 30 days and 2 cycles.
        3. Enable H/w worm on the pool and set retention as 1 days and 1 cycle.
        4. Check DB for the worm copy flag, storage is marked with bucket lock flag, micro pruning is disabled and seal frequency is set as per retention on pool (7 days in this case).
        5. Ensure copy is marked with worm copy flag and override retention is not set on the copy, also the retention value should be updated to pool retention i.e. 1D and 1C.

Sample Input:
    "65586": {
            "AgentName": "File System",
            "MediaAgentName": "MediaAgent1",
            "ClientName": "Client1",
            "CloudMountPath": "Container1",
            "SavedCredential": "SavedCredential1",
            "CloudUserName": "clouduser1",
            "CloudVendorName": "Vendor1"
            }
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
        self.name = "[SDK] Acceptance WORM bucket lock config only"
        self.mmhelper = None
        self.ma_machine = None
        self.policy_case1 = None
        self.partition_path = None
        self.cloud_lib_obj = None
        self.mount_path = None
        self.dedupe_pool_case1 = None
        self.dedupe_pool_case2 = None
        self.policy_case2 = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.dedupe_pool_case1 = '%s_dedupe_pool1-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                        self.tcinputs['ClientName'])
        self.dedupe_pool_case2 = '%s_dedupe_pool2-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                        self.tcinputs['ClientName'])

        self.policy_case1 = '%s_policy1-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                              self.tcinputs['ClientName'])
        self.policy_case2 = '%s_policy2-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                              self.tcinputs['ClientName'])

        options_selector = OptionsSelector(self.commcell)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        # DDB partition path
        if self.tcinputs.get("PartitionPath") is not None:
            self.partition_path = self.tcinputs['PartitionPath']
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")
            # To select drive with space available in Media agent machine
            self.log.info('Selecting drive in the Media agent machine based on space available')
            ma_drive = options_selector.get_drive(self.ma_machine, size=25 * 1024)
            if ma_drive is None:
                raise Exception("No free space for hosting ddb")
            self.log.info('selected drive: %s', ma_drive)
            self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

        self.mmhelper = MMHelper(self)
        self._cleanup(self.policy_case1, self.dedupe_pool_case1)
        self._cleanup(self.policy_case2, self.dedupe_pool_case2)

    def _cleanup(self, policy, pool):
        """cleanup the entities created"""
        try:
            # Delete storage policy
            if self.commcell.storage_policies.has_policy(policy):
                self.log.info(f"Deleting Storage Policy: {policy}")
                self.commcell.storage_policies.delete(policy)
                self.log.info(f"Deleted Storage Policy: {policy}")

            # Delete cloud storage pool
            if self.commcell.storage_pools.has_storage_pool(pool):
                self.log.info(f"Deleting Storage Pool: {pool}")
                self.commcell.storage_pools.delete(pool)
                self.log.info(f"Deleted Storage Pool: {pool}")

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup(self.policy_case1, self.dedupe_pool_case1)
            self._cleanup(self.policy_case2, self.dedupe_pool_case2)
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )

    def dedupe_worm_validation(self, cloud_pool, cloud_lib, sp_obj):
        """ validate WORM lock configuration on dedupe pool"""

        cloud_pool_name = cloud_pool.storage_pool_name
        cloud_library_name = cloud_lib.library_name
        sp_name = sp_obj.storage_policy_name

        # check if storage WORM lock is enabled
        if cloud_pool.is_worm_storage_lock_enabled:
            self.log.info("WORM lock is enabled on cloud storage pool - [%s]", cloud_pool_name)
        else:
            raise Exception("WORM lock is not enabled on cloud storage pool - [%s]", cloud_pool_name)

        # Check if bucket level WORM lock is enabled on cloud storage pool
        if cloud_pool.is_bucket_level_worm_lock_enabled:
            self.log.info("Bucket level WORM lock is enabled on cloud storage pool - [%s]", cloud_pool_name)
        else:
            raise Exception("Bucket level WORM lock is not enabled on cloud storage pool - [%s]", cloud_pool_name)

        # check if compliance lock is enabled
        if cloud_pool.is_compliance_lock_enabled:
            self.log.info("Compliance lock is enabled on cloud storage pool - [%s]", cloud_pool_name)
        else:
            raise Exception("Compliance lock is not enabled on cloud storage pool - [%s]", cloud_pool_name)

        # check seal frequency is set as per retention on pool
        seal_frequency = 7
        if self.mmhelper.get_copy_store_seal_frequency(cloud_pool.get_copy())['days'] == seal_frequency:
            self.log.info("Seal frequency is set as per retention on pool - [%s]", cloud_pool_name)
        else:
            raise Exception("Seal frequency is not set as per retention on pool - [%s]", cloud_pool_name)

        # check if micro pruning is disabled on pool
        if cloud_lib.advanced_library_properties['MountPathList'][0]['mountPathSummary']['attribute'] & 32 == 32:
            raise Exception("Micro pruning is enabled on cloud library - [%s]", cloud_library_name)
        else:
            self.log.info("Micro pruning is disabled on cloud library - [%s]", cloud_library_name)

        primary_copy_obj = sp_obj.get_copy("Primary")

        # check if compliance lock is enabled on dependent storage policy copy
        if primary_copy_obj.is_compliance_lock_enabled:
            self.log.info("Compliance lock is enabled on dependent [Primary] copy of storage policy [%s]", sp_name)
        else:
            raise Exception("Compliance lock is not enabled on dependent [Primary] copy of storage policy [%s]", sp_name)

        # check override retention of pool is not enabled on dependent storage policy copy
        if primary_copy_obj.override_pool_retention:
            raise Exception("Override retention of pool is enabled on dependent [Primary] copy of storage policy [%s]", sp_name)
        else:
            self.log.info("Override retention of pool is not enabled on dependent [Primary] copy of storage policy [%s]", sp_name)

    def run(self):
        """Main test case logic"""
        try:
            # case1 - Dependent storage policy creation after enabling WORM lock on cloud storage pool
            self.log.info("Case1: Dependent storage policy creation after enabling WORM lock on cloud storage pool")
            # Creating cloud storage pool
            dedupe_pool_obj_case1, lib_obj_case1 = self.mmhelper.configure_storage_pool(self.dedupe_pool_case1,
                                                                                        self.tcinputs["CloudMountPath"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.partition_path,
                                                                                        username=self.tcinputs[
                                                                                            "CloudUserName"],
                                                                                        credential_name=self.tcinputs[
                                                                                            "SavedCredential"],
                                                                                        cloud_vendor_name=self.tcinputs[
                                                                                            "CloudVendorName"])
            # Enable WORM on cloud storage pool
            self.mmhelper.enable_worm_storage_lock(dedupe_pool_obj_case1, 1)

            # Create a dependent storage policy associated to the pool
            sp_obj_case1 = self.mmhelper.configure_storage_policy(self.policy_case1,
                                                                  storage_pool_name=self.dedupe_pool_case1)

            # Validate WORM lock configuration
            self.dedupe_worm_validation(dedupe_pool_obj_case1, lib_obj_case1, sp_obj_case1)

            # case2 - Dependent storage policy creation before enabling WORM lock on cloud storage pool
            self.log.info("Case2: Dependent storage policy creation before enabling WORM lock on cloud storage pool")
            # Creating cloud storage pool
            dedupe_pool_obj_case2, lib_obj_case2 = self.mmhelper.configure_storage_pool(self.dedupe_pool_case2,
                                                                                        self.tcinputs["CloudMountPath"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.partition_path,
                                                                                        username=self.tcinputs[
                                                                                            "CloudUserName"],
                                                                                        credential_name=self.tcinputs[
                                                                                            "SavedCredential"],
                                                                                        cloud_vendor_name=self.tcinputs[
                                                                                            "CloudVendorName"])
            # Create a dependent storage policy associated to the pool
            sp_obj_case2 = self.mmhelper.configure_storage_policy(self.policy_case2,
                                                                  storage_pool_name=self.dedupe_pool_case2)

            # Set Retention on primary copy to 30 Days, 2 Cycle
            self.log.info("Setting retention on primary copy to 30 Days, 2 Cycle")
            primary_copy_obj_case2 = sp_obj_case2.get_copy("Primary")
            retention = (30, 2, -1)
            primary_copy_obj_case2.copy_retention = retention

            # Validate retention on primary copy set as expected to 30 Days, 2 Cycle
            primary_retention = primary_copy_obj_case2.copy_retention
            if primary_retention['days'] == 30 and primary_retention['cycles'] == 2:
                self.log.info("Retention on primary copy set as expected to 30 Days, 2 Cycle")
            else:
                raise Exception("Retention on primary copy not set as expected to 30 Days, 2 Cycle")

            # Enable WORM on cloud storage pool
            self.mmhelper.enable_worm_storage_lock(dedupe_pool_obj_case2, 1)

            # Refresh pool copy object
            primary_copy_obj_case2.refresh()

            # Validate retention on primary copy reset to pool copy retention after enabling WORM lock
            primary_retention = primary_copy_obj_case2.copy_retention
            if primary_retention['days'] == 1 and primary_retention['cycles'] == 1:
                self.log.info("Retention on primary copy set as expected to 1 Days, 1 Cycle")
            else:
                raise Exception("Retention on primary copy not set as expected to 1 Days, 1 Cycle")

            # Validate WORM lock configuration
            self.dedupe_worm_validation(dedupe_pool_obj_case2, lib_obj_case2, sp_obj_case2)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
