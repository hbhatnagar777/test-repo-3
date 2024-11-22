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

from Application.AD import CVADHelper
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Application.AD.exceptions import ADException
from Web.Common.page_object import TestStep





class TestCase(CVTestCase):
    """
    Class for executing  AD Point In Time Restore acceptance Test:
    Validation for AD Point In Time Restore
    """
    TestStep = TestStep()
    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "AD"
        self.utils = TestCaseUtils(self)
        self.domain = None
        self.user_name = None
        self.surname=None
        self.title=None
        self.mobile=None
        self.attribute = None
        self.host_machine = None
        self.ad_point_in_time_restore= None
        self.job_end_time1=None
        self.job_end_time2=None
        self.report_before_alter=None
        self.report_after_alter=None
        self.server=None
        self.host_machine=None
        self.ad_point_in_time_restore=None
        self.client_name=None
        self.client_display_name=None
        self.subclient_name=None
        self.computer_name=None
        self.restore_path=None

    @TestStep
    def generate_report(self):
        """
        Function to get surname, title and mobile phone of a user.
        """
        surname=self.ad_point_in_time_restore.user_ps_operation(username=self.user_name,
                                                                op_type="RETURN_PROPERTY",
                                                                computer_name=self.computer_name,
                                                                attribute_value="",
                                                                attribute="Surname")
        title=self.ad_point_in_time_restore.user_ps_operation(username=self.user_name,
                                                              op_type="RETURN_PROPERTY",
                                                              computer_name=self.computer_name,
                                                              attribute_value="",
                                                              attribute="Title")
        mobile=self.ad_point_in_time_restore.user_ps_operation(username=self.user_name,
                                                               op_type="RETURN_PROPERTY",
                                                               computer_name=self.computer_name,
                                                               attribute_value="",
                                                               attribute="MobilePhone")
        report=surname+title+mobile
        return report

    @TestStep
    def gen_restore_path(self):
        """
        Function to generate restore Path returns restore Path
        """
        self.log.info("Function to generate restore path")
        restore_path=""
        domain_split=self.domain.split('.')
        domain_split_rev=domain_split[::-1]
        for i in domain_split_rev:
            restore_path+=",DC="
            restore_path+=i

        restore_path+=",CN=Users,CN="
        restore_path+=self.user_name
        return restore_path

    @TestStep
    def verify_point_in_time_restore(self):
        """
        Function to verify point in time restore
        """
        try:
            if self.report_before_alter==self.report_after_alter :
                self.log.info("AD Point In Time Restore Verified Successfully")
            else:
                raise ADException("ad", 17,
                                  "AD Point In Time Restore Failed")
        except ADException as excp:
            raise ADException('ad', '17',
                              "AD Point In Time Restore Failed") from excp

    def setup(self):

        self.domain = self.tcinputs['Domain']
        ad_user = self.tcinputs['ServerUsername']
        ad_pass = self.tcinputs['ServerPassword']
        self.user_name = self.tcinputs['UserName']
        self.surname=self.tcinputs['Surname']
        self.title=self.tcinputs['Title']
        self.mobile=self.tcinputs['Mobile']
        self.server = self.tcinputs['ServerName']
        self.host_machine = machine.Machine(self.server, self.commcell)
        self.ad_point_in_time_restore = CVADHelper.CVADHelper( self.log,self.commcell,self.server,
                                                           ad_username=ad_user, ad_password=ad_pass)
        self.client_name = self.tcinputs['ClientName']
        self.client_display_name=self.tcinputs['ClientDisplayName']
        self.computer_name=self.tcinputs['CompName']
        self.subclient_name=self.tcinputs['SubclientName']

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Beginning The Run functions")
            self.log.info("Triggering First Backup")
            self.job_end_time1=self.ad_point_in_time_restore.do_backup(subclient_obj=self._subclient)
            self.log.info("Execution of Power shell script to "
                          "return properties of user Before Alter")
            self.report_before_alter = self.generate_report()
            self.log.info("Making Changes Through Power Shell")
            self.ad_point_in_time_restore.user_ps_operation(username=self.user_name,
                                                            op_type="MODIFY_USER",
                                                            computer_name=self.computer_name,
                                                            attribute_value=self.surname,
                                                            attribute="Surname")
            self.ad_point_in_time_restore.user_ps_operation(username=self.user_name,
                                                            op_type="MODIFY_USER",
                                                            computer_name=self.computer_name,
                                                            attribute_value=self.title,
                                                            attribute="Title")
            self.ad_point_in_time_restore.user_ps_operation(username=self.user_name,
                                                            op_type="MODIFY_USER",
                                                            computer_name=self.computer_name,
                                                            attribute_value=self.mobile,
                                                            attribute="MobilePhone")
            self.log.info("Triggering Second Backup")
            self.job_end_time2 = self.ad_point_in_time_restore.do_backup(subclient_obj=self._subclient)
            self.log.info("Doing Point In Time Restore")
            self.restore_path=self.gen_restore_path()
            self._subclient.restore_job(display_name=self.client_display_name,
                                        client_name=self.client_name,
                                        subclient_name=self.subclient_name,
                                        to_time=self.job_end_time1,
                                        restore_path=self.restore_path)
            self.log.info("Execution of Power shell script to "
                          "return properties of user After Point In Time Restore")
            self.report_after_alter=self.generate_report()
            self.log.info("Verifying point in time restore")
            self.verify_point_in_time_restore()

        except ADException as exp:
            raise ADException('ad', '17',
                              "AD Point in Time Restore met "
                              "with Exception in run function") from exp

    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("Teardown function of this test case started")
