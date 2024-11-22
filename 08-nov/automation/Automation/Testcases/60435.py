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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from VirtualServer.VSAUtils import VirtualServerUtils
from cvpysdk.client import Client
from Web.Common.cvbrowser import (BrowserFactory)
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.webconsole import WebConsole
from Server.Workflow.workflowhelper import WorkflowHelper
import time

class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA - VMware V1 to V2 migration"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DATAPROTECTION
        self.commcell_obj = None
        self.migration_validation = None
        self.workflow = "VSA V1 to V2 migration"
        self.test_individual_status = True
        self.tcinputs = {"Clients to migrate": ""}

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()
        self.commcell_obj = self._commcell
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                              self.inputJSONnode['commcell']['commcellPassword'])
        self.webconsole.wait_till_load_complete()
        self.webconsole.goto_forms()
        self.forms = Forms(self.webconsole)

    def run(self):
        """Main function for test case execution"""

        log = logger.get_log()

        try:
            list_of_clients = self.tcinputs['Clients to migrate']
            _list_of_clients = list(list_of_clients.split(","))
            for clients in range(len(_list_of_clients)):
                workflow_helper = WorkflowHelper(self, self.workflow, deploy=False)
                self.forms.open_workflow(self.workflow)
                # First window
                self.forms.set_textbox_value(label="Specify email addresses of any other users to be reported:",
                                         value=[self.inputJSONnode['email']['receiver']])
                self.forms.click_action_button("OK")
                # Second window
                time.sleep(10)
                self.forms._open_search_results("Clients to migrate")
                time.sleep(10)
                self.forms._search_submit_dropdown(value=_list_of_clients[clients])
                self.forms.click_action_button("OK")
                # third window
                self.forms.click_action_button("Continue")
                workflow_helper.workflow_job_status(self.workflow)

                try:
                    # validate V2 client is created
                    auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
                    _client_name = _list_of_clients[clients] + '_V2'
                    _is_v2 = auto_commcell.check_v2_indexing(client=_client_name)
                    if _is_v2:
                        VirtualServerUtils.decorative_log("V2 client has been created")

                except Exception as exp:
                    self.log.error('Client created is not V2' + str(exp))
                    raise Exception
            VirtualServerUtils.decorative_log("All clients have been migrated")
            VirtualServerUtils.decorative_log("Cleaning up migrated clients for next run")

            for clients in range(len(_list_of_clients)):
                try:
                    #Retire the V2 client
                    _client_name = _list_of_clients[clients] + "_V2"
                    VirtualServerUtils.decorative_log('Retire the client')
                    self.commcell.clients.refresh()
                    client = Client(self.commcell, _client_name, client_id=None)
                    self.commcell.clients.refresh()
                    client.retire()
                    VirtualServerUtils.decorative_log('Retire client operation ran successfully')

                except Exception as exp:
                    self.log.error('Failed to retire'+ str(exp))
                    raise Exception

                try:
                    #Validate client has been retired
                    VirtualServerUtils.decorative_log('Validate if Client is deleted')
                    self.commcell.clients.refresh()
                    if not self.commcell.clients.has_client(client.client_name):
                        VirtualServerUtils.decorative_log('Client has been deleted')

                except Exception as exp:
                    self.log.error('Client is not deleted' + str(exp))
                    raise Exception

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if not self.test_individual_status:
                self.result_string = str(exp)
                self.status = constants.FAILED
