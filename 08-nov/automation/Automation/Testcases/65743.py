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

from cvpysdk.commcell import Commcell
from AutomationUtils import machine, constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.AD import CVADHelper
from Reports.utils import TestCaseUtils
from Application.AD.exceptions import ADException
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """
    Class for executing Basic AD Compare acceptance Test:
    Validation for AD Compare
    """
    TestStep = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "AD Compare domain validation"
        self.app_type = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.domain = None
        self.attribute = None
        self.subclient = None
        self.host_machine = None
        self.ad_comphelper = None
        self.server = None
        self.user_name1 = None
        self.display_name1 = None
        self.display_name2 = None
        self.display_name3 = None
        self.user_name2 = None
        self.user_name3 = None
        self.commcell_object = None
        self.server = None
        self.host_machine = None
        self.ad_comphelper = None
        self.client = None
        self.description = None
        self.computer_name = None
        self.display_name = None
        self.comparison_name = None
        self.agent = None
        self.instance = None
        self.backupset = None
        self.client_obj = None
        self.agent_obj = None
        self.inst_obj = None
        self.backupset_obj = None
        self.backupset_id = None
        self.subclient_obj = None
        self.job_end_time1 = None
        self.job_end_time2 = None
        self.results = None
        self.next_run_attribute = None
        self.live_comparison_name = None
        self.results_live = None

    @TestStep
    def validate_results_live(self, results):
        """
        function to validate AD compare report between Live data and second backup
        param results(dict): AD compare report
        """
        self.log.info("Validating Results Generated in Live Report")

        try:

            total_hits = results['adComparisonBrowseResp']['TotalHits']
            if total_hits >= 3:
                self.log.info("ADCompare between live data and first backup successful")
            else:
                raise ADException('ad', '007',
                                  "ADCompare Unsuccessful Did not get the "
                                  "expected Response in the Results Total Hits did not match")

        except ADException as exp:
            raise ADException('ad', '007',
                              exception_message="Invalid Compare Report") from exp

    @TestStep
    def validate_results(self, results, username1, username2, username3):
        """
        function to validate AD compare report between first and second backup
        param results(dict): AD compare report
        username1(str): Name of new user
        username2(str):Name of modified user
        username3(str):Name of deleted user

        """
        self.log.info("Validating Results Generated in Report")

        try:

            total_hits = results['adComparisonBrowseResp']['TotalHits']
            # Validating if total hits 3
            self.log.info("Checking if 3 hits found")
            self.log.info(f"Creating dictionary to validate results")
            modified_dict = {"CN=Users,CN=" + username1: 0, username3: 1, username2: 2}
            result_dict = {}
            for i in range(total_hits):
                result_dict[results['adComparisonBrowseResp']["compareItem"][i]["DisplayName"]] = \
                    results['adComparisonBrowseResp']["compareItem"][i]["ItemChangeType"]

            if set(modified_dict.items()).issubset(set(result_dict.items())):
                self.log.info("AD Compare between First and Second backup "
                              "verified successfully")

            # if total_hits==3:
            #     #Extracting DisplayName and ItemChangeType for further validation
            #     compare_item=results['adComparisonBrowseResp']['compareItem']
            #     first_change_type=compare_item[0]['ItemChangeType']
            #     first_display_name=compare_item[0]['DisplayName']
            #     self.log.info(f"{first_display_name}")
            #     second_change_type = compare_item[1]['ItemChangeType']
            #     second_display_name = compare_item[1]['DisplayName']
            #     self.log.info(f"{second_display_name}")
            #     third_change_type = compare_item[2]['ItemChangeType']
            #     third_display_name = compare_item[2]['DisplayName']
            #     self.log.info(f"{third_display_name}")
            # elif total_hits==4:
            #     compare_item = results['adComparisonBrowseResp']['compareItem']
            #     first_change_type = compare_item[1]['ItemChangeType']
            #     first_display_name = compare_item[1]['DisplayName']
            #     self.log.info(f"{first_display_name}")
            #     second_change_type = compare_item[2]['ItemChangeType']
            #     second_display_name = compare_item[2]['DisplayName']
            #     self.log.info(f"{second_display_name}")
            #     third_change_type = compare_item[3]['ItemChangeType']
            #     third_display_name = compare_item[3]['DisplayName']
            #     self.log.info(f"{third_display_name}")

            # self.log.info("3 Hits found matching ItemChangeType with Username "
            #               "now( 0 for New User "
            #               "1 for delete and 2 for set description)")
            # check_dict={first_change_type:first_display_name,
            #             second_change_type:second_display_name,
            #             third_change_type:third_display_name}
            #
            # self.log.info(f"{check_dict}")
            # #Checking if the ItemChangeType matches with the expected username
            # if(check_dict[1].find(username3)!=-1 and check_dict[2].find(username2)!=-1 and
            #         check_dict[0].find(username1)!=-1):

            else:
                raise ADException('ad', '007', "ADCompare "
                                               "Unsuccessful Did not get the"
                                               " expected Response in the "
                                               "Results Total Hits not three")

        except ADException as exp:
            raise ADException('ad', '007',
                              exception_message="Invalid Compare Report") from exp

    def setup(self):

        self.domain = self.tcinputs['Domain']
        webconsole_hostname = self.inputJSONnode['commcell']['webconsoleHostname']
        username = self.inputJSONnode['commcell']['commcellUsername']
        password = self.inputJSONnode['commcell']['commcellPassword']
        ad_user = self.tcinputs['ServerUsername']
        ad_pass = self.tcinputs['ServerPassword']
        self.user_name1 = self.tcinputs['AddUserName']
        self.user_name2 = self.tcinputs['ModifyUserName']
        self.user_name3 = self.tcinputs['DeleteUserName']
        self.display_name1 = self.tcinputs['AddDisplayName']
        self.display_name2 = self.tcinputs['ModifyDisplayName']
        self.display_name3 = self.tcinputs['DeleteDisplayName']
        self.subclient = self.tcinputs['subclient']
        self.commcell_object = Commcell(webconsole_hostname=webconsole_hostname,
                                        commcell_username=username, commcell_password=password)
        self.server = self.tcinputs['ServerName']

        self.ad_comphelper = CVADHelper.CVADHelper(self.log, self.server,
                                                   ad_username=ad_user,
                                                   ad_password=ad_pass)

        self.client = self.tcinputs['ClientName']
        self.description = self.tcinputs['Description']
        self.computer_name = self.tcinputs['ComputerName']

        self.display_name = self.tcinputs['ClientDisplayName']
        self.comparison_name = self.tcinputs['ComparisonName']
        self.next_run_attribute = self.tcinputs['NextRunAttribute']
        self.live_comparison_name = self.tcinputs['LiveComparisonName']
        self.agent = "active directory"
        self.instance = "defaultInstanceName"
        self.backupset = "defaultBackupSet"

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Beginning The Run functions")

            self.client_obj = self.commcell_object.clients.get(self.client)
            self.agent_obj = self.client_obj.agents.get(self.agent)
            self.inst_obj = self.agent_obj.instances.get(self.instance)
            self.backupset_obj = self.inst_obj.backupsets.get(self.backupset)
            self.subclient_obj = self.backupset_obj.subclients.get(self.subclient)

            # Triggering first backup and fetching job end time
            self.log.info("Triggering first Backup")
            self.job_end_time1 = self.ad_comphelper.do_backup(subclient_obj=self.subclient_obj)

            self.log.info("Calling function to make changes Through Power Shell script")
            # Creating New user
            self.log.info("Creating New user")
            self.ad_comphelper.user_ps_operation(username=self.user_name1,
                                                 principalname=self.display_name1,
                                                 op_type="NEW_USER",
                                                 computer_name=self.computer_name,
                                                 attribute_value="",
                                                 attribute="Description")
            # Modifying existing user
            self.log.info("Setting Description of Existing User")
            self.ad_comphelper.user_ps_operation(username=self.user_name2,
                                                 principalname=self.display_name2,
                                                 op_type="MODIFY_USER",
                                                 computer_name=self.computer_name,
                                                 attribute_value=self.description,
                                                 attribute="Description")
            # Deleting existing user
            self.log.info("Deleting User")
            self.ad_comphelper.user_ps_operation(username=self.user_name3,
                                                 principalname=self.display_name3,
                                                 op_type="DELETE_USER",
                                                 computer_name=self.computer_name,
                                                 attribute_value="",
                                                 attribute="Description")
            self.log.info("Finished Making changes through Power Shell")

            # Triggering second backup and fetching job end time
            self.log.info("Triggering Second Backup")
            self.job_end_time2 = self.ad_comphelper.do_backup(subclient_obj=self.subclient_obj)

            # Calling Function to launch compare job and generate results
            self.log.info("Calling Function to launch compare job and generate results")
            self.results = self.ad_comphelper.generate_compare_result(
                subclient_obj=self.subclient_obj,
                left_set_time=self.job_end_time1,
                right_set_time=self.job_end_time2,
                display_name=self.display_name,
                client_name=self.client,
                comparison_name=self.comparison_name,
                domain=self.domain)
            self.log.info("Compare Report generated")
            self.log.info(f"Report is {self.results}")

            # Calling function to validate compare report
            self.validate_results(self.results, self.user_name1, self.display_name2, self.display_name3)

            self.log.info("Live data Comparison")
            self.results_live = self.ad_comphelper.generate_compare_result(
                subclient_obj=self.subclient_obj,
                left_set_time=self.job_end_time1,
                right_set_time=0,
                display_name=self.display_name,
                client_name=self.client,
                comparison_name=self.live_comparison_name,
                domain=self.domain, op_type=2)
            self.log.info("Live Compare Report generated")

            self.validate_results_live(self.results_live)

        except ADException as exp:
            raise ADException('ad', '007',
                              exception_message="Exception in run function") from exp

    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("Teardown function of this test case started")
        if self.status == constants.PASSED:
            # Recreating deleted user
            self.log.info("Recreating deleted user")
            self.ad_comphelper.user_ps_operation(username=self.user_name3, principalname=self.display_name3,op_type="NEW_USER",
                                                 computer_name=self.computer_name, attribute_value="",
                                                 attribute="Description")
            self.ad_comphelper.user_ps_operation(username=self.user_name1,
                                                 principalname=self.display_name1,
                                                 op_type="DELETE_USER",
                                                 computer_name=self.computer_name,
                                                 attribute_value="",
                                                 attribute="Description")

            self.log.info("Setting Description of Existing User")
            self.ad_comphelper.user_ps_operation(username=self.user_name2,
                                                 principalname=self.display_name2,
                                                 op_type="MODIFY_USER",
                                                 computer_name=self.computer_name,
                                                 attribute_value=self.next_run_attribute,
                                                 attribute="Description")
            self.log.info("Testcase : PASSED")

        else:
            self.log.info("Testcase : FAILED")

        self.log.info("Tear down funtion executed.")
