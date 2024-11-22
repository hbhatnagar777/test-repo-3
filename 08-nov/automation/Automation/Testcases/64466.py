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

    tear_down()     --  tear down function of this test case

"""
import random
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Server.JobManager import jobmanager_helper
from Server.Plans import planshelper
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing AssociatedEntities REST API for a plan"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "plans-Associated entities"
        self.plan_name = None
        self.agent_obj = None
        self.client_name = None
        self.plan_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.plan_helper = planshelper.PlansHelper(self.inputJSONnode['commcell']["webconsoleHostname"],
                                                   self.inputJSONnode['commcell']['commcellUsername'],
                                                   self.inputJSONnode['commcell']['commcellPassword'], self.commcell)

        # choose a random client
        self.commcell.clients.refresh()
        self.client_name = random.choice(list(self.commcell.clients.file_server_clients.keys()))
        self.log.info(f"client to be used for the testcase: {self.client_name}")

        self.agent_obj = self.commcell.clients.get(self.client_name).agents.get('File System')

        # create a test plan
        plan_name = f"assoc_entity_test_plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        storage = self.plan_helper.get_storage_pool()
        self.plan_name = self.plan_helper.create_base_plan(plan_name=plan_name,
                                                           subtype='Server',
                                                           storage_pool=storage).plan_name
        # create a test backupset
        self.backupset = \
            self.agent_obj.backupsets.add(f"test_assoc_backupset_{datetime.now().strftime('%Y%m%d%H%M%S')}")

    def cleanup(self):
        """Method to dissociate and delete subclients to the plan and delete all the test entities"""
        self.agent_obj.backupsets.refresh()
        jobmanager_helper.JobManager(commcell=self.commcell).kill_active_jobs(self.client_name)
        try:
            backup_sets = self.agent_obj.backupsets.all_backupsets
            for keys in backup_sets.keys():
                if self.agent_obj.backupsets.get(keys).plan and \
                        "assoc_entity_test_plan_" in self.agent_obj.backupsets.get(keys).plan.plan_name:
                    self.plan_helper.dissociate_entity(self.client_name, keys)
                if not self.agent_obj.backupsets.get(keys).plan and 'test_assoc_backupset_' in keys:
                    self.agent_obj.backupsets.delete(keys)
            self.plan_helper.cleanup_plans("assoc_entity_test_plan_")
            self.log.info("Clean Up successful")
        except Exception as exp:
            self.log.info(f"cleanUp failed for backupset: {self.backupset.name}. Reason: {str(exp)}")

    def run(self):
        """Main function for test case execution"""
        try:
            # create subclients and associate to plan
            self.plan_helper.validate_plans_assoc_entity_count(plan_name=self.plan_name,
                                                               client_name=self.client_name,
                                                               backup_set=self.backupset.name,
                                                               operation="association")

            # dissociate random number of subclients to plan
            self.plan_helper.validate_plans_assoc_entity_count(plan_name=self.plan_name,
                                                               client_name=self.client_name,
                                                               backup_set=self.backupset.name,
                                                               operation="dissociation")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
