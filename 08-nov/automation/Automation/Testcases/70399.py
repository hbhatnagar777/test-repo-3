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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Application.AD.ms_azuread import AzureAd, CvAzureAd
from Application.AD.adpowershell_helper import AADPowerShell
from Application.AD.exceptions import ADException
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Azure AD Group Relationship Point In Time Restore acceptance Test:
    Validation for Azure AD Group Relationship Point In Time Restore
    """
    TestStep = TestStep()
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure AD Restore relationship verification"
        self.utils = TestCaseUtils(self)
        self.commcell_object = None
        self.client = None
        self.subclient_name = None
        self.azure_username = None
        self.azure_password = None
        self.first_groupid = None
        self.second_groupid = None
        self.third_groupid = None
        self.user_id = None
        self.display_name = None
        self.azure_power_helper = None
        self.add_ins = None
        self.cv_azure_ad = None

    @TestStep
    def do_backup(self, backup_level="Incremental"):
        """
        Function to trigger incremental backup and return backup end time
        param backup_level: the level of backup to perform
        """
        backup_obj = self._subclient.backup(backup_level=backup_level)
        backup_obj.wait_for_completion()
        job_end_time = int(backup_obj._summary['jobEndTime'])
        self.log.info(" Backup Done Returning end Time")
        return job_end_time

    @TestStep
    def get_user_info(self):
        """
        get the user attributes from ms-aad
        :return: User
        """
        self.log.info(f"Getting user info {self.display_name}")
        sleep(20)
        user = self.aad_ins.user(**{"displayName": self.display_name})
        return user

    @TestStep
    def perform_restore(self, azure_ad_obj, to_time):
        """
        Performs restore for a selected object at selected time
        param to_time: restores from a backup_job_time
        param azure_ad_obj: user info object
        return: restore job object

        """
        self.log.info("Performing restore")
        self.cv_azure_ad.cv_obj_restore(browsetime=to_time, obj_=azure_ad_obj)
        self.log.info("Restore completed")

    @TestStep
    def verification_after_first_restore(self, result_report):
        """
        Function to verify Azure Group Relationship restored
        param result_report: report containing the object
                             ids of group associated with
                             the azure user
        """
        self.log.info(f"Second group association: {self.second_groupid in result_report}")
        self.log.info(f"First group association: {self.first_groupid in result_report}")
        if self.second_groupid in result_report and self.first_groupid in result_report:
            self.log.info("Got expected result in Restore ")
        else:
            self.log.info("Did not get expected result after first Restore")
            raise ADException(exception_module="azuread", exception_id=607)

    @TestStep
    def verification_after_second_restore(self, result_report):
        """
        Function to verify Azure Group Relationship restored
        param result_report: report containing the object
                             ids of group associated with
                             the azure user
        """
        self.log.info(f"Third group association: {self.third_groupid in result_report}")
        self.log.info(f"Second group association: {self.second_groupid in result_report}")
        self.log.info(f"First group association: {self.first_groupid in result_report}")

        if (self.first_groupid in result_report and self.second_groupid not in result_report and
                self.third_groupid not in result_report):
            self.log.info("Got expected result in Restore ")
        else:
            self.log.info("Did not get expected result after Second Restore")
            raise ADException(exception_module="azuread", exception_id=607)

    def setup(self):
        self.client = self.tcinputs['ClientName']
        self.azure_username=self.tcinputs['azure_username']
        self.azure_password=self.tcinputs['azure_password']
        self.first_groupid=self.tcinputs['FirstGroupID']
        self.second_groupid = self.tcinputs['SecondGroupID']
        self.third_groupid = self.tcinputs['ThirdGroupID']
        self.user_id = self.tcinputs['user_id']
        self.display_name = self.tcinputs['display_name']
        aad_credential = [self.tcinputs['ClientId'],
                          self.tcinputs['ClientPass'],
                          self.tcinputs['TenantName']]
        self.aad_ins = AzureAd(*aad_credential, self.log)
        self.cv_azure_ad = CvAzureAd(self.aad_ins, self._subclient)
        self.azure_power_helper = AADPowerShell(self.log, self.azure_username, self.azure_password)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Beginning The Run functions")
            self.do_backup()
            first_aad_obj = self.get_user_info()
            self.log.info(f"First Azure AD object : {first_aad_obj}")
            self.azure_power_helper.user_ps_operation(group_object_id=self.first_groupid,
                                                      user_id=self.user_id, op_type="ADD_TO_GROUP")
            self.azure_power_helper.user_ps_operation(group_object_id=self.second_groupid,
                                                      user_id=self.user_id, op_type="ADD_TO_GROUP")
            first_backup_job = self.do_backup()

            self.azure_power_helper.user_ps_operation(group_object_id="",
                                                      user_id=self.user_id, op_type="DELETE_USER")

            self.perform_restore(first_aad_obj,first_backup_job)

            members_after_first_restore=self.azure_power_helper.user_ps_operation(group_object_id="",
                                                                      user_id=self.user_id,
                                                                      op_type="RETURN_MEMBER_GROUPS")
            self.log.info(members_after_first_restore)
            self.verification_after_first_restore(members_after_first_restore)

            self.azure_power_helper.user_ps_operation(group_object_id=self.second_groupid,
                                                     user_id=self.user_id, op_type="REMOVE_FROM_GROUP")

            second_backup_job = self.do_backup()
            second_aad_obj = self.get_user_info()
            self.log.info(f"Second Azure AD object : {second_aad_obj}")

            self.azure_power_helper.user_ps_operation(group_object_id=self.third_groupid,
                                                      user_id=self.user_id, op_type="ADD_TO_GROUP")
            self.azure_power_helper.user_ps_operation(group_object_id=self.first_groupid,
                                                      user_id=self.user_id, op_type="REMOVE_FROM_GROUP")
            self.azure_power_helper.user_ps_operation(group_object_id=self.second_groupid,
                                                      user_id=self.user_id, op_type="REMOVE_FROM_GROUP")

            self.perform_restore(second_aad_obj,second_backup_job)

            members_after_second_restore = self.azure_power_helper.user_ps_operation(group_object_id="",
                                                                         user_id=self.user_id,
                                                                         op_type="RETURN_MEMBER_GROUPS")
            self.verification_after_second_restore(members_after_second_restore)
            self.log.info("Azure Group Relationship Restore Verified Successful")

        except ADException as exp:
            raise ADException('azuread', '607')

    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("Teardown function of this test case started")
        try:
            self.azure_power_helper.user_ps_operation(group_object_id=self.first_groupid,
                                                      user_id=self.user_id, op_type="REMOVE_FROM_GROUP")
            self.azure_power_helper.user_ps_operation(group_object_id=self.second_groupid,
                                                      user_id=self.user_id, op_type="REMOVE_FROM_GROUP")
            self.azure_power_helper.user_ps_operation(group_object_id=self.third_groupid,
                                                      user_id=self.user_id, op_type="REMOVE_FROM_GROUP")
        finally:
            self.log.info("Tear down function completed")
