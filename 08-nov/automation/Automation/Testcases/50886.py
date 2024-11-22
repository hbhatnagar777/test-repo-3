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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from Server.Security.userhelper import UserHelper
from Server.Workflow.workflowhelper import WorkflowHelper


class TestCase(CVTestCase):

    """Class for validating Workflow-all variable Types"""
    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Workflow-all variable Types"
        self.workflow_name = "WF_INPUTVARIABLES"
        self.wf_helper = None
        self.custom_name = None
        self.option_selector = None
        self.user_obj = None
        self.cv_entities = None
        self.media_agent = None
        self.entities = None

    def setup(self):
        """Setup function of this test case"""
        self.wf_helper = WorkflowHelper(self, wf_name=self.workflow_name)
        self.option_selector = OptionsSelector(self.commcell)
        self.cv_entities = CVEntities(self.commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.custom_name = self.option_selector.get_custom_str()
            self.user_obj = UserHelper(self.commcell)
            self.user_obj.create_user(user_name=self.custom_name,
                                      email="{0}@cv.com".format(self.custom_name),
                                      password=self.custom_name)
            self.media_agent = self.option_selector.get_ma()
            self.log.info("Creating storage policy")
            self.entities = self.cv_entities.create({
                'disklibrary': {},
                'storagepolicy':
                    {
                        'name': "{0}test".format(self.custom_name),
                        'dedup_path': None,
                        'incremental_sp': None,
                        'retention_period': 3,
                        'force': True,
                    },
            })
            self.wf_helper.execute(workflow_json_input={
                "xml": "<head><body>test</body></head>",
                "string": self.custom_name,
                "integer": 12345,
                "client": self.commcell.commserv_client.client_name,
                "client_group": "Laptop Clients",
                "library": self.entities["disklibrary"]["name"],
                "media_agent": self.media_agent,
                "storage_policy": self.entities["storagepolicy"]["name"],
                "user": self.custom_name,
                "user_group": "master",
                "workflow": self.workflow_name,
                "commserv": self.commcell.commserv_name
            })

        except Exception as exp:
            self.wf_helper.test.fail(exp)

        finally:
            self.wf_helper.delete(self.workflow_name)
            if self.commcell.users.has_user(self.custom_name):
                self.user_obj.delete_user(self.custom_name, new_user="admin")
            self.cv_entities.cleanup()
