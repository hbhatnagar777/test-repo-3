# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: CleanRoom: Trigger Recovery Job for eligible VMs

TestCase: Class for executing this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from cvpysdk.cleanroom.recovery_groups import RecoveryGroups
from Server.control_plane_recovery_helper import ControlPlaneRecoveryhelper
from cvpysdk.commcell import Commcell
from AutomationUtils import config


class TestCase(CVTestCase):
    """This class is used to automate triggering Recovery job"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.cs_recovery = None
        self.name = "CleanRoom: Trigger Recovery Job for eligible VMs"
        self.tcinputs = {
            "group_name": None,
            "commserve_guid": None
        }
        self.csrecovery_helper = None
        self.utils = None
        self.group_name = None
        self.recovery_groups = None
        self.config_json = config.get_config()

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.csrecovery_helper = ControlPlaneRecoveryhelper(self.commcell, self.tcinputs['commserve_guid'])
            self.utils = TestCaseUtils(self)
            self.group_name = self.tcinputs['group_name']
        except Exception as exp:
            raise CVTestCaseInitFailure('Failed to initialise testcase') from exp

    @test_step
    def perform_recovery(self, commcell_obj):
        """Perform Recovery job for eligible vms"""
        self.recovery_groups = RecoveryGroups(commcell_obj)
        if self.recovery_groups.has_recovery_group(self.group_name):
            recovery_group = self.recovery_groups.get(self.group_name)
            self.log.info(f"Recovery Group: {self.group_name} found")

            job_id = recovery_group.recover_all()
            recovery_job = commcell_obj.job_controller.get(job_id)
            self.log.info(f"Recovery Job {job_id} triggered for Recovery group {self.group_name} for eligible entities")
            recovery_job.wait_for_completion()

            self.utils.assert_comparison(recovery_job.status, 'Completed')
            self.log.info(f"Recovery job completed")
        else:
            raise Exception(f"Given commcell does not have {self.group_name} recovery group")

    def run(self):
        """Runs the testcase in order"""
        try:
            reqid = self.csrecovery_helper.start_recovery_of_latest_backupset()
            self.log.info(f"request id : {reqid}")
            details = self.csrecovery_helper.wait_until_vm_is_recovered(reqid)
            staged_commcell_obj = Commcell(
                details['commandcenter_url'].split("/")[2],
                details['username'],
                details['password'],
                verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE
            )
            self.perform_recovery(staged_commcell_obj)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
