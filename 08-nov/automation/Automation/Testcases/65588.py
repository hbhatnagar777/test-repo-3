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

    seal_frequency_validation() -- check seal frequency is set as per retention on pool and minimum storage stay days

    min_seal_frequency_validation() -- check min seal frequency is set as 7 days if retention is set as less than 7 days

    max_seal_frequency_validation() -- check max seal frequency set as 365 days if retention set as more than 365 days

    hot_seal_frequency_validation() -- check seal frequency is set as per retention on hot tier storage pool

    cool_seal_frequency_validation() -- check seal frequency is set as per retention on cool tier storage pool

    archive_seal_frequency_validation() -- check seal frequency is set as per retention on archive tier storage pool

Sample Input:

    "65588": {
            "AgentName": "File System",
            "MediaAgentName": "MediaAgent1",
            "ClientName": "Client1",
            "CloudMountPath": "Container1",
            "SavedCredential": "SavedCredential1",
            "CloudHotUserName": "cloudhotuser1",
            "CloudCoolUserName": "cloudcooluser2",
            "CloudArchiveUserName": "cloudarchiveuser3",
            "CloudVendorName": "Vendor1"
            "AgentName": "File System"
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
        self.name = "[SDK] Acceptance WORM config for DDB sealing frequency"
        self.mmhelper = None
        self.ma_machine = None
        self.hot_policy_case1 = None
        self.hot_policy_case2 = None
        self.cool_policy = None
        self.archive_policy = None
        self.hot_pool_case1 = None
        self.hot_pool_case2 = None
        self.cool_pool = None
        self.archive_pool = None
        self.partition_path = None
        self.cloud_lib_obj = None
        self.mount_path = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgentName": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.hot_pool_case1 = '%s_hot_pool1-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                        self.tcinputs['ClientName'])
        self.hot_pool_case2 = '%s_hot_pool2-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                        self.tcinputs['ClientName'])
        self.cool_pool = '%s_cool_pool-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                  self.tcinputs['ClientName'])
        self.archive_pool = '%s_archive_pool-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                             self.tcinputs['ClientName'])

        self.hot_policy_case1 = '%s_hot_policy1-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                              self.tcinputs['ClientName'])
        self.hot_policy_case2 = '%s_hot_policy2-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                              self.tcinputs['ClientName'])
        self.cool_policy = '%s_cool_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                      self.tcinputs['ClientName'])
        self.archive_policy = '%s_archive_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
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
        self._cleanup(self.hot_policy_case1, self.hot_pool_case1)
        self._cleanup(self.hot_policy_case2, self.hot_pool_case2)
        self._cleanup(self.cool_policy, self.cool_pool)
        self._cleanup(self.archive_policy, self.archive_pool)

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
            self._cleanup(self.hot_policy_case1, self.hot_pool_case1)
            self._cleanup(self.hot_policy_case2, self.hot_pool_case2)
            self._cleanup(self.cool_policy, self.cool_pool)
            self._cleanup(self.archive_policy, self.archive_pool)
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment."
                "Please check for failure reason and manually clean up the environment..."
            )

    def seal_frequency_validation(self, cloud_pool, retention_days, min_stay_days):
        """
        check seal frequency is set as per retention on pool and minimum storage stay days

        Args:
            cloud_pool (object) : cloud storage pool object
            retention_days (int) : retention days set on pool
            min_stay_days (int) : minimum days storage tier expect data be stored, if no such requirement then pass 0
        """

        if retention_days < 7:
            expected_seal_frequency = 7
        elif retention_days > 365:
            expected_seal_frequency = 365
        else:
            expected_seal_frequency = retention_days

        if min_stay_days > 0 and (retention_days + expected_seal_frequency) < min_stay_days:
            expected_seal_frequency = min_stay_days - retention_days

        configured_seal_frequency = self.mmhelper.get_copy_store_seal_frequency(cloud_pool)['days']
        if configured_seal_frequency == expected_seal_frequency:
            self.log.info("Seal frequency [%s days] was set as expected" % configured_seal_frequency)
        else:
            self.log.error("Seal frequency [%s days] was not set as expected [%s days]" % (configured_seal_frequency,
                                                                                           expected_seal_frequency))
            raise Exception("Seal frequency [%s days] was not set as expected [%s days]" % (configured_seal_frequency,
                                                                                            expected_seal_frequency))

    def min_seal_frequency_validation(self, cloud_pool):
        """ check min seal frequency is set as 7 days if retention is set as less than 7 days"""

        # Set retention on the pool primary copy as 1Day, 1Cycle
        self.log.info("Setting retention on pool copy as 1 day")
        retention = (1, 1, -1)
        pool_copy = cloud_pool.get_copy()
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy set as 1 day")
        self.seal_frequency_validation(pool_copy, 1, 0)

        # Update retention to the value of 7 days (increase in retention should be allowed)
        self.log.info("Increasing retention on pool copy as 7 days")
        retention = (7, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 7:
            self.log.info("Retention on pool copy set as expected to 7 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 7 days")
        self.seal_frequency_validation(pool_copy, 7, 0)

        # Try lowering the retention, it should get an error that it is not allowed (reduce to 5D)
        self.log.info("Reducing retention on pool copy to 5 days from 7 days")
        retention = (5, 1, -1)
        try:
            pool_copy.copy_retention = retention
            self.log.error("Retention on pool copy got reduced to 5 days from 7 days which is not allowed")
            raise Exception("Retention on pool copy got reduced to 5 days from 7 days which is not allowed")
        except Exception as exp:
            if "Reducing the basic or extended retention of a worm storage policy copy is not allowed" in str(exp):
                self.log.info("Retention on pool copy was not allowed to reduce as expected with error: %s", exp)
            else:
                raise exp

        # Increase retention to the value of 8 days, seal frequency should get updated to 8 days.
        self.log.info("Increasing retention on pool copy to 8 days from 7 days")
        retention = (8, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 8:
            self.log.info("Retention on pool copy set as expected to 8 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 8 days")
        self.seal_frequency_validation(pool_copy, 8, 0)

    def max_seal_frequency_validation(self, cloud_pool):
        """ check max seal frequency is set as 365 days if retention is set as more than 365 days"""
        # Set retention on the pool as 364Days
        self.log.info("Setting retention on pool copy as 364 days")
        retention = (364, 1, -1)
        pool_copy = cloud_pool.get_copy()
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy set as 364 days")
        self.seal_frequency_validation(pool_copy, 364, 0)

        # Update retention to the value of 365 days (increase in retention should be allowed)
        self.log.info("Increasing retention on pool copy to 365 days from 364 days")
        retention = (365, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 365:
            self.log.info("Retention on pool copy set as expected to 365 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 365 days")
        self.seal_frequency_validation(pool_copy, 365, 0)

        # Update retention to the value of 366days (increase in retention should be allowed)
        self.log.info("Increasing retention on pool copy to 366 days from 365 days")
        retention = (366, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 366:
            self.log.info("Retention on pool copy set as expected to 366 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 366 days")
        self.seal_frequency_validation(pool_copy, 366, 0)

        # Try lowering the retention, it should get an error that it is not allowed (reduce to 365D)
        self.log.info("Reducing retention on pool copy to 365 days from 366 days")
        retention = (365, 1, -1)
        try:
            pool_copy.copy_retention = retention
            self.log.error("Retention on pool copy got reduced to 365 days from 366 days which is not allowed")
            raise Exception("Retention on pool copy got reduced to 365 days from 366 days which is not allowed")
        except Exception as exp:
            if "Reducing the basic or extended retention of a worm storage policy copy is not allowed" in str(exp):
                self.log.info("Retention on pool copy was not allowed to reduce as expected with error: %s", exp)
            else:
                raise exp
        # Increase retention to the value of 3650 days, seal frequency should stay 365 days.
        self.log.info("Increasing retention on pool copy to 3650 days from 365 days")
        # Updating retention should not return overflow error.
        retention = (3650, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 3650:
            self.log.info("Retention on pool copy set as expected to 3650 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 3650 days")
        self.seal_frequency_validation(pool_copy, 3650, 0)

    def hot_seal_frequency_validation(self, cloud_pool):
        """ check seal frequency is set as per retention on pool"""
        # Set retention on the pool as 7Days
        self.log.info("Setting retention on pool copy as 7 days")
        retention = (7, 1, -1)
        pool_copy = cloud_pool.get_copy()
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy set as 7 days")
        self.seal_frequency_validation(pool_copy, 7, 0)

        # Update retention to the value of 30 days (increase in retention should be allowed)
        self.log.info("Increasing retention on pool copy to 30 days from 7 days")
        retention = (30, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 30:
            self.log.info("Retention on pool copy set as expected to 30 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 30 days")
        self.seal_frequency_validation(pool_copy, 30, 0)

        # Update retention to the value of 180 days (increase in retention should be allowed)
        self.log.info("Increasing retention on pool copy to 180 days from 30 days")
        retention = (180, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 180:
            self.log.info("Retention on pool copy set as expected to 180 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 180 days")
        self.seal_frequency_validation(pool_copy, 180, 0)

    def cool_seal_frequency_validation(self, cloud_pool):
        """ check seal frequency is set as per retention on cool tier storage pool"""

        # Set retention on the pool as 1Days
        self.log.info("Setting retention on pool copy as 1 day")
        retention = (1, 1, -1)
        pool_copy = cloud_pool.get_copy()
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy set as 1 day")
        self.seal_frequency_validation(pool_copy, 1, 30)

        # Set retention to 7 days then seal frequency should be 23 days
        self.log.info("Increasing retention on pool copy to 7 days from 1 day")
        retention = (7, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 7:
            self.log.info("Retention on pool copy set as expected to 7 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 7 days")
        self.seal_frequency_validation(pool_copy, 7, 30)

        # Increase retention to 15 days seal frequency should be 15 days
        self.log.info("Increasing retention on pool copy to 15 days from 7 days")
        retention = (15, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 15:
            self.log.info("Retention on pool copy set as expected to 15 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 15 days")
        self.seal_frequency_validation(pool_copy, 15, 30)

        # Increase retention to 16 days seal frequency should be 14 days
        self.log.info("Increasing retention on pool copy to 16 days from 15 days")
        retention = (16, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 16:
            self.log.info("Retention on pool copy set as expected to 16 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 16 days")
        self.seal_frequency_validation(pool_copy, 16, 30)

        # Increase retention to 30 days seal frequency should be 30 days
        self.log.info("Increasing retention on pool copy to 30 days from 16 days")
        retention = (30, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 30:
            self.log.info("Retention on pool copy set as expected to 30 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 30 days")
        self.seal_frequency_validation(pool_copy, 30, 30)

        # Increase retention to 366 days and seal frequency should cap at 365 days.
        self.log.info("Increasing retention on pool copy to 366 days from 30 days")
        retention = (366, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 366:
            self.log.info("Retention on pool copy set as expected to 366 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 366 days")
        self.seal_frequency_validation(pool_copy, 366, 30)

    def archive_seal_frequency_validation(self, cloud_pool):
        """ check seal frequency is set as per retention on archive tier storage pool"""
        # Set retention on the pool as 1Days
        self.log.info("Setting retention on pool copy as 1 day")
        retention = (1, 1, -1)
        pool_copy = cloud_pool.get_copy()
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy set as 1 day")
        self.seal_frequency_validation(pool_copy, 1, 180)

        # Set retention to 7 days then seal frequency should be 173 days.
        self.log.info("Increasing retention on pool copy to 7 days from 1 day")
        retention = (7, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 7:
            self.log.info("Retention on pool copy set as expected to 7 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 7 days")
        self.seal_frequency_validation(pool_copy, 7, 180)

        # Increase retention to 30 days seal frequency should be 150 days.
        self.log.info("Increasing retention on pool copy to 30 days from 7 days")
        retention = (30, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 30:
            self.log.info("Retention on pool copy set as expected to 30 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 30 days")
        self.seal_frequency_validation(pool_copy, 30, 180)

        # Increase retention to 90 days seal frequency should be 90 days.
        self.log.info("Increasing retention on pool copy to 90 days from 30 days")
        retention = (90, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 90:
            self.log.info("Retention on pool copy set as expected to 90 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 90 days")
        self.seal_frequency_validation(pool_copy, 90, 180)

        # Increase retention to 91 days and seal frequency should be 91 days.
        self.log.info("Increasing retention on pool copy to 91 days from 90 days")
        retention = (91, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 91:
            self.log.info("Retention on pool copy set as expected to 91 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 91 days")
        self.seal_frequency_validation(pool_copy, 91, 180)

        # Increase retention to 366 days and seal frequency should cap at 365 days.
        self.log.info("Increasing retention on pool copy to 366 days from 91 days")
        retention = (366, 1, -1)
        pool_copy.copy_retention = retention
        self.log.info("Retention on pool copy can be increased")
        if pool_copy.copy_retention['days'] == 366:
            self.log.info("Retention on pool copy set as expected to 366 days")
        else:
            raise Exception("Retention on pool copy not set as expected to 366 days")
        self.seal_frequency_validation(pool_copy, 366, 180)

    def run(self):
        """Main test case logic"""
        try:
            # case1(a) - Hot tier pool min and max seal frequency validation
            self.log.info("Case1(a) - Hot tier pool min and max seal frequency validation if retention is set as "
                          "less than 7 Day and more than 365 Days")
            # Creating cloud storage pool
            hot_pool_obj_case1, hot_lib_obj_case1 = self.mmhelper.configure_storage_pool(self.hot_pool_case1,
                                                                                        self.tcinputs["CloudMountPath"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.partition_path,
                                                                                        username=self.tcinputs[
                                                                                            "CloudHotUserName"],
                                                                                        credential_name=self.tcinputs[
                                                                                            "SavedCredential"],
                                                                                        cloud_vendor_name=self.tcinputs[
                                                                                            "CloudVendorName"])

            # Validate storage class is set as Hot for the storage pool
            if int(hot_pool_obj_case1.storage_pool_properties["storagePoolDetails"]["cloudStorageClassNumber"]) == 1:
                self.log.info("Storage class is set as Hot for the storage pool [%s]" % self.hot_pool_case1)
            else:
                raise Exception("Storage class is not set as Hot for the storage pool [%s]" % self.hot_pool_case1)

            # Create a dependent storage policy associated to the pool
            self.mmhelper.configure_storage_policy(self.hot_policy_case1, storage_pool_name=self.hot_pool_case1)

            # Enable WORM on cloud storage pool
            self.mmhelper.enable_worm_storage_lock(hot_pool_obj_case1, 1)

            # Validate min seal frequency of 7 days if retention is less than 7 days
            self.min_seal_frequency_validation(hot_pool_obj_case1)

            # Validate max seal frequency is set as per retention on pool
            self.max_seal_frequency_validation(hot_pool_obj_case1)

            # case1(b) - Hot tier pool seal frequency validation with random retention
            self.log.info("Case1(b) - Hot tier pool seal frequency validation with random retention")

            # Creating cloud storage pool
            hot_pool_obj_case2, hot_lib_obj_case2 = self.mmhelper.configure_storage_pool(self.hot_pool_case2,
                                                                                        self.tcinputs["CloudMountPath"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.tcinputs["MediaAgentName"],
                                                                                        self.partition_path,
                                                                                        username=self.tcinputs[
                                                                                            "CloudHotUserName"],
                                                                                        credential_name=self.tcinputs[
                                                                                            "SavedCredential"],
                                                                                        cloud_vendor_name=self.tcinputs[
                                                                                            "CloudVendorName"])

            # Validate storage class is set as Hot for the storage pool
            if int(hot_pool_obj_case1.storage_pool_properties["storagePoolDetails"]["cloudStorageClassNumber"]) == 1:
                self.log.info("Storage class is set as Hot for the storage pool [%s]" % self.hot_pool_case2)
            else:
                raise Exception("Storage class is not set as Hot for the storage pool [%s]" % self.hot_pool_case2)

            # Create a dependent storage policy associated to the pool
            self.mmhelper.configure_storage_policy(self.hot_policy_case2, storage_pool_name=self.hot_pool_case2)

            # Enable WORM on cloud storage pool
            self.mmhelper.enable_worm_storage_lock(hot_pool_obj_case2, 1)

            # Validate seal frequency is set as per retention on pool
            self.hot_seal_frequency_validation(hot_pool_obj_case2)

            # case2 - Cool tier pool seal frequency validation
            self.log.info("Case2 - Cool tier pool seal frequency validation")
            # Creating cloud storage pool
            cool_pool_obj, cool_lib_obj = self.mmhelper.configure_storage_pool(self.cool_pool,
                                                                              self.tcinputs["CloudMountPath"],
                                                                              self.tcinputs["MediaAgentName"],
                                                                              self.tcinputs["MediaAgentName"],
                                                                              self.partition_path,
                                                                              username=self.tcinputs["CloudCoolUserName"],
                                                                              credential_name=self.tcinputs["SavedCredential"],
                                                                              cloud_vendor_name=self.tcinputs["CloudVendorName"])
            # Validate storage class is set as Cool for the storage pool
            if int(cool_pool_obj.storage_pool_properties["storagePoolDetails"]["cloudStorageClassNumber"]) == 2:
                self.log.info("Storage class is set as Cool for the storage pool [%s]" % self.cool_pool)
            else:
                raise Exception("Storage class is not set as Cool for the storage pool [%s]" % self.cool_pool)

            # Create a dependent storage policy associated to the pool
            self.mmhelper.configure_storage_policy(self.cool_policy, storage_pool_name=self.cool_pool)

            # Enable WORM on cloud storage pool
            self.mmhelper.enable_worm_storage_lock(cool_pool_obj, 1)

            # Validate seal frequency is set as per retention on pool
            self.cool_seal_frequency_validation(cool_pool_obj)

            # case3 - Archive tier pool seal frequency validation
            self.log.info("Case3 - Archive tier pool seal frequency validation")
            # Creating cloud storage pool
            archive_pool_obj, archive_lib_obj = self.mmhelper.configure_storage_pool(self.archive_pool,
                                                                                    self.tcinputs["CloudMountPath"],
                                                                                    self.tcinputs["MediaAgentName"],
                                                                                    self.tcinputs["MediaAgentName"],
                                                                                    self.partition_path,
                                                                                    username=self.tcinputs["CloudArchiveUserName"],
                                                                                    credential_name=self.tcinputs["SavedCredential"],
                                                                                    cloud_vendor_name=self.tcinputs["CloudVendorName"])
            # Validate storage class is set as Archive for the storage pool
            if int(archive_pool_obj.storage_pool_properties["storagePoolDetails"]["cloudStorageClassNumber"]) in (3, 19):
                self.log.info("Storage class is set as Archive for the storage pool [%s]" % self.archive_pool)
            else:
                raise Exception("Storage class is not set as Archive for the storage pool [%s]" % self.archive_pool)

            # Create a dependent storage policy associated to the pool
            self.mmhelper.configure_storage_policy(self.archive_policy, storage_pool_name=self.archive_pool)
            # Enable WORM on cloud storage pool
            self.mmhelper.enable_worm_storage_lock(archive_pool_obj, 1)
            # Validate seal frequency is set as per retention on pool
            self.archive_seal_frequency_validation(archive_pool_obj)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
