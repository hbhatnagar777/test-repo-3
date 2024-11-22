# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""[SDK] Compliance Lock auto enable on DR Copy

Steps:
    1. Create new DR policy
    2. Validate if compliance lock got enabled by default on primary DR copy (CVA_WORM_COPY_FLAG -> 16777216)
    3. Create a secondary copy on DR policy
    4. Validate if compliance lock is not enabled by default on secondary DR copy
    5. Set compliance lock on secondary copy
    6. Try disabling the compliance lock on primary DR copy it should fail
    7. Set config param to allow disabling compliance lock(https://engweb.commvault.com/additionalsetting/13251)
    8. Try disabling the compliance lock on primary DR copy it should disable
    9. Try disabling the compliance lock on secondary DR copy it should fail
    10. Restart the MM service and validate if compliance lock is not reenabled on primary DR copy
    11. Remove the config param
    12. Restart the MM service and validate if compliance lock is reenabled on primary DR copy


TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case


User should have the following permissions:
        CommCell level Administrative Management


Sample Input:
"65637": {
    "MediaAgentName": "MediaAgentName"
}
"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper

from cvpysdk.exception import SDKException


class TestCase(CVTestCase):
    """This test case verifies the Compliance Lock auto enable on DR Copy"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name        (str)       --  name of this test case

                tcinputs    (dict)      --  test case inputs with input name as dict key
                                            and value as input type
        """
        super(TestCase, self).__init__()

        self.name = '[SDK] Compliance Lock auto enable on DR Copy'
        self.tcinputs = {
            'MediaAgentName': None
        }

        self.storage_policy_name = None
        self.library_name = None
        self.mount_path = None
        self.global_param = None

        self.mm_helper: MMHelper = None
        self.total_attempts = None   # MAX retries after mm service restarts

        self.disk_library = None
        self.dr_policy = None
        self.primary_copy = None
        self.sec_copy = None

    def setup(self):
        """Setup function of this test case"""

        self.storage_policy_name = '%s_policy-ma(%s)' % (str(self.id), self.tcinputs.get('MediaAgentName'))
        self.library_name = '%s_disk_library-ma(%s)' % (str(self.id), self.tcinputs.get('MediaAgentName'))

        options_selector = OptionsSelector(self.commcell)
        ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])
        ma_drive = options_selector.get_drive(ma_machine)
        self.mount_path = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')

        self.global_param = {
            'category': 'CommServDB.GxGlobalParam',
            'key_name': 'AllowUnsetComplianceLockOnDRCopy'
        }

        self.mm_helper = MMHelper(self)
        self.total_attempts = 5

    def run(self):
        """Run function of this test case"""

        try:
            self._cleanup()
            self.log.debug('Using mount path: %s' % self.mount_path)
            self.disk_library = self.mm_helper.configure_disk_library(mount_path=self.mount_path)

            # 1. Create new DR policy
            self.dr_policy = self.mm_helper.configure_storage_policy(dr_sp=True)
            self.primary_copy = self.dr_policy.get_copy('Primary')

            # 2. Validate if compliance lock got enabled by default on primary DR copy (CVA_WORM_COPY_FLAG -> 16777216)
            if not self.primary_copy.is_compliance_lock_enabled:
                raise Exception('Complaince lock did not get enabled by default on primary DR copy.')
            self.log.info('Complaince lock got enabled by default on primary DR copy.')

            # 3. Create a secondary copy on DR policy
            self.sec_copy = self.mm_helper.configure_secondary_copy('Secondary')

            # 4. Validate if compliance lock is not enabled by default on secondary DR copy
            if self.sec_copy.is_compliance_lock_enabled:
                raise Exception('Complaince lock is enabled by default on secondary DR copy.')
            self.log.info('Complaince lock is not enabled by default on secondary DR copy.')

            # 5. Set compliance lock on secondary copy
            self.sec_copy.enable_compliance_lock()
            self.log.info('Set compliance lock on secondary.')

            # 6. Try disabling the compliance lock on primary DR copy it should fail
            try:
                self.primary_copy.disable_compliance_lock()
                raise Exception('Disabling the compliance lock on primary DR copy did not fail.')
            except SDKException as exp:
                if 'Response was not success' in exp.exception_message:
                    self.log.info('Disabling the compliance lock on primary DR copy failed.')
                else:
                    raise exp

            # 7. Set config param to allow disabling compliance lock
            self.commcell.add_additional_setting(**self.global_param, data_type='BOOLEAN', value='true')
            self.log.info('Set config param to allow disabling compliance lock.')

            # 8. Try disabling the compliance lock on primary DR copy it should disable
            self.primary_copy.disable_compliance_lock()
            self.log.info('Disabled the compliance lock on primary DR copy.')

            # 9. Try disabling the compliance lock on secondary DR copy it should fail
            try:
                self.sec_copy.disable_compliance_lock()
                raise Exception('Disabling the compliance lock on secondary DR copy did not fail.')
            except SDKException as exp:
                if 'Response was not success' in exp.exception_message:
                    self.log.info('Disabling the compliance lock on secondary DR copy failed.')
                else:
                    raise exp

            # 10. Restart the MM service and validate if compliance lock is not reenabled on primary DR copy
            self.mm_helper.restart_mm_service()
            for attempt in range(1, self.total_attempts + 1):
                self.log.info('Validating compliance lock: attempt [%s/%s]' % (attempt, self.total_attempts))
                self.log.info('... Waiting for 5 minutes')
                time.sleep(60 * 5)
                self.primary_copy.refresh()
                if not self.primary_copy.is_compliance_lock_enabled:
                    self.log.info('Complaince lock is not reenabled on primary DR copy.')
                    break
            else:
                raise Exception('Complaince lock is reenabled on primary DR copy.')

            # 11. Remove the config param
            self.commcell.delete_additional_setting(**self.global_param)
            self.log.info('Removed the config param.')

            # 12. Restart the MM service and validate if compliance lock is reenabled on primary DR copy
            self.mm_helper.restart_mm_service()
            for attempt in range(1, self.total_attempts + 1):
                self.log.info('Validating compliance lock: attempt [%s/%s]' % (attempt, self.total_attempts))
                self.log.info('... Waiting for 5 minutes')
                time.sleep(60 * 5)
                self.primary_copy.refresh()
                if self.primary_copy.is_compliance_lock_enabled:
                    self.log.info('Complaince lock is reenabled on primary DR copy.')
                    break
            else:
                raise Exception('Complaince lock is not reenabled on primary DR copy.')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self._cleanup()
        except Exception as exp:
            self.log.error('Failed to tear down test case with error: %s', exp)

    def _cleanup(self):
        """Delete existing entities before/after running testcase"""

        self.log.info('Check storge policy: %s' % self.storage_policy_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.log.info('Deleting storage policy ...')
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info('Storage policy deleted.')

        self.log.info('Check disk library: %s' % self.library_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info('Deleting disk library ...')
            self.commcell.disk_libraries.delete(self.library_name)
            self.log.info('Disk library deleted.')

        global_param_name = self.global_param['key_name']
        self.log.info('Check global param: %s', global_param_name)
        if self.commcell.get_gxglobalparam_value(global_param_name):
            self.log.info('Deleting global param ...')
            self.commcell.delete_additional_setting(**self.global_param)
            self.log.info('Global param deleted.')
