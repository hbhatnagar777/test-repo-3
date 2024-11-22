# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, cvhelper
from Server.Plans.migrationhelper import MigrationHelper
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.serverhelper import ServerTestCases
from Web.API.webconsole import Apps as AppsAPI
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       —  name of this test case

                product         (str)       —  applicable product for this
                                                test case
                    Ex: self.products_list.FILESYSTEM

                features        (str)       —  qcconstants feature_list item
                    Ex: self.features_list.DATAPROTECTION

                tcinputs        (dict)      —  dict of test case inputs with
                                                input name as dict key
                                                and value as input type
                        Ex: {
                                "MY_INPUT_NAME": "MY_INPUT_TYPE"
                            }
        """
        super(TestCase, self).__init__()
        self.name = "[Commserver] Policy to plan conversion validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.PLANS
        self.commcell_obj = None
        self.migration_validation = None

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()
        self.commcell_obj = self._commcell
        self.tcinputs["MSPCommCell"] = self.inputJSONnode[
            'commcell']['webconsoleHostname']
        self.tcinputs["MSPadminUser"] = self.inputJSONnode[
            'commcell']['commcellUsername']
        self.tcinputs["MSPadminUserPwd"] = self.inputJSONnode[
            'commcell']['commcellPassword']
        cs_machine_obj = Machine()
        encrypted_pass = cs_machine_obj.get_registry_value(
                r"Database", "pAccess")
        password = cvhelper.format_string(
                self._commcell, encrypted_pass).split("_cv")[1]
        self.migration_validation = MigrationHelper(
            self.commcell_obj,
            password
        )
        self.server = ServerTestCases(self)
        self.workflow_helper = WorkflowHelper(
            self, "Policy to Plan - Create Base Plan", deploy=False, commcell=self.commcell_obj
        )
        self.applications = AppsAPI(
            self.commcell_obj.webconsole_hostname,
            username=self.tcinputs["MSPadminUser"],
            password=self.tcinputs["MSPadminUserPwd"]
        )

    def run(self):
        """Run function of this test case"""
        self._log.info("Started executing {0} testcase".format(self.id))

        # Check if step 1 has been run
        if not self.migration_validation.step1_complete():
            # Import the app
            self.applications.import_app_from_path('.\\Server\\Plans\\Policy to Plan Conversion.cvapp.zip')

            # Collect the info of the subclients that will potentially be affected by the WF (subclientId, 
            # storagePolicy, schedPolicies)
            self.migration_validation.retrieve_eligible_subclients()

            # Execute step 1
            self.workflow_helper.execute()

            # Validate sub.storage_policy.before == sub.storage_policy.after
            self.migration_validation.validate_after_step1()
        else:
            self.migration_validation.validate_after_step1()

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn Final Block")
