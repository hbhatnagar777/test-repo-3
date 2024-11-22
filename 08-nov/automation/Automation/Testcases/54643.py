# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object
    setup()         --  Setup function for this testcase
    tear_down()     --  Tear down function to delete automation generated data
    run()           --  Main function for test case executions
    bakcup_job      --  run azure ad backup job
    compare_result  --  compare the azure ad object with browse result
    full_backup     --  azure ad full backup/browse/restore testing
    inc_backup      --  azure ad inc bakcup/browse/restore testing
    change_backup   --  azure ad object change backup/browse/restore testing

"""
from time import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.AD.ms_azuread import AzureAd, CvAzureAd
from Application.AD.exceptions import ADException
from Web.Common.page_object import TestStep

class TestCase(CVTestCase):
    """ class to run agent basic testing for Azure ad agent"""

    test_step = TestStep()

    def __init__(self):
        """ initial class
        Properties to be initialized:
        name            (str)        -- name of this test case
        applicable_os   (str)    -- applicable os for this test case
        product         (str)    -- applicable product for AD
        """
        super().__init__()
        self.name = "Azure AD agent basic backup/restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.ACTIVEDIRECTORY
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "ClientName" : None,
            "AgentName" : "Azure AD",
            }
        self.aad_ins = None
#       we can pick any objects type from ["user", "group", "reg_app", "ent_app"]
        self.aad_types = ['user']
        self.subclient = None
        self.aad_ins = None
        self.cv_aad_ins = None
        self.status = None
        self.result_string = None

    def backup_job(self, backuplevel="Inc"):
        """
        run backup job
        Args:
            backuplevel     (str)       backup level, picked form "Inc" and "Full", default is Inc
        Return:
            job_            (obj)       job object
        """
        self.log.info(f"Start the {backuplevel} backup job")
        if backuplevel == "full":
            job_ = self.subclient.backup(backup_level="Full")
        else:
            job_ = self.subclient.backup()
        self.log.debug(f"backup job {job_.job_id} started")
        jobresult = job_.wait_for_completion()
        if not jobresult:
            raise ADException("testcase", self._id,
                              f"full backup job result is {job_.summary['pendingReason']}.")
        self.log.debug(f"backup job {job_.job_id} completed. job result is {jobresult}")
        return job_

    def compare_result(self,compare_result):
        """
        compare the azure ad object with browse result
        Args:
            compare_result  (dict)      compare result between azure directory and browse
            objs_           (list)      azure ad objects to compare
        Return:

        """
        for type_ in self.aad_types:
            result = compare_result[type_]
            if result:
                self.log.debug(f"{type_} object  was restored successuflly")
            else:
                self.log.info(f"{type_} delete and restore doesn't find match result")
                raise ADException("testcase", self._id,
                                  "compare result after full is not correct")

    @test_step
    def full_backup(self):
        """
        azure ad full backup/browse/restore testing
        Args:
        Return:
        """
        aad_objs_batch0 = self.aad_ins.group_objs_create(types=self.aad_types,
                                                         prestring=f"auto_init_{self.id}")
        self.log.info("Start an full backup job")
        b_f_job  = self.backup_job(backuplevel="Full")
        self.cv_aad_ins.cv_obj_browse_check(aad_objs_batch0, b_f_job)
        compare_result = self.cv_aad_ins.cv_obj_delete_restore(aad_objs_batch0)
        self.log.info(f"here is the compare result {compare_result}")
        self.compare_result(compare_result)

    @test_step
    def inc_backup(self):
        """
        azure ad inc bakcup/browse/restore testing
        Args:
        Return:
        """
        timestamp = int(time())
        aad_objs_batch1 = self.aad_ins.group_objs_create(types=self.aad_types,
                                                         prestring=f"auto_inc_{self.id}_{timestamp}")
        self.log.info("Start an incrmeantal backup job ")
        b_in_job = self.backup_job()
        self.cv_aad_ins.cv_obj_browse_check(aad_objs_batch1, b_in_job)
        compare_result = self.cv_aad_ins.cv_obj_delete_restore(aad_objs_batch1, harddelete=True)
        self.log.debug(f"Here is the compare result after hard delete {compare_result}")
        self.compare_result(compare_result)

    @test_step
    def change_backup(self, advanced=False):
        """
        azure ad object change backup/browse/restore testing
        """
        timestamp = int(time())
        aad_objs_batch2 = self.aad_ins.group_objs_create(types=self.aad_types,
                                                         prestring=f"auto_change_{self.id}_{timestamp}")
        self.log.info("Start an incremental backup job before make attribute change")
        attributes = self.cv_aad_ins.cv_obj_change(aad_objs_batch2, value="basic")
        b_change_base_job = self.backup_job()
        self.cv_aad_ins.cv_obj_browse_check(aad_objs_batch2, b_change_base_job)
        attributes = self.cv_aad_ins.cv_obj_change(aad_objs_batch2, attributes=attributes)
        self.log.info("Start another incremental backup job after make attribute change")
        if advanced: #   there is a browse issue which will failed hte changed test case. will skip 2nd inc job
            b_change_change_job = self.backup_job()
            self.cv_aad_ins.cv_obj_browse_check(aad_objs_batch2, b_change_change_job)
        compare_result = self.cv_aad_ins.cv_obj_change_restore(aad_objs_batch2,
                                                                b_change_base_job,
                                                                attributes=attributes)
        self.log.debug(f"Here is the compare result after attribute change {compare_result}")
        self.compare_result(compare_result)

    def setup(self):
        """ prepare the setup environment"""
        aad_credential = [self.tcinputs['ClientId'],
                          self.tcinputs['ClientPass'],
                          self.tcinputs['TenantName']]
        if "types" in self.tcinputs:
            self.aad_types = self.tcinputs['types']
            self.log.info(f"will use obj types in answer file {self.aad_types}")
        self.aad_ins = AzureAd(*aad_credential, self.log)
        self.subclient = self._backupset.subclients.get("default")
        self.cv_aad_ins = CvAzureAd(self.aad_ins, self.subclient)
        self.log.info(f"get default subclient instance with id {self.subclient.subclient_id}")
        self.clean_up(phase="all")

    def run(self):
        """ run test case steps"""
        try:
            self.full_backup()
            self.inc_backup()
            self.change_backup()
            self.status = constants.PASSED
            self.log.info("Test case completed without issue")
        except ADException as exp:
            self.status = constants.FAILED
            self.log.exception(f"There is excpetion happened, here is the detail {exp.report}")
            self.result_string = exp.report
        except Exception as exp:
            self.status = constants.FAILED
            self.log.exception(f"There is not AD excpetion happened, here is the detail {exp}")

    def tear_down(self):
        """tear down when the case is completed, include error handle"""
        # check existing aad objects
        if self.status == constants.PASSED:
            self.clean_up(phase="all")

    def clean_up(self, phase):
        """clean up all object created in the script"""
        # remove all static objects
        if phase == "all":
            for type_ in self.aad_types:
                operation_ins = getattr(self.aad_ins, type_)
                for phase_ in ['init', "full", "change", "inc"]:
                    try:
                        operation_ins(operation="delete", **{"displayname": f"*auto_{phase_}"})
                    except:
                        self.log.debug(f"failed to clean {type_} objects auto_{phase_}. please manually clean up it")
        else:
            for type_ in self.aad_types:
                operation_ins = getattr(self.aad_ins, type_)
                operation_ins(operation="delete", **{"displayname": f"*auto_{phase_}"})