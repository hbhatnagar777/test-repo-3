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
    
    init_tc()       --  initializes this test case

    run()           --  run function of this test case
"""

from datetime import datetime
from cvpysdk.job import Job
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from Reports.storeutils import StoreUtils
from Server.Workflow.workflowhelper import WorkflowHelper
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Store.storeapp import StoreApp
from Web.Common.cvbrowser import (Browser, BrowserFactory)
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of SQL Server backup and restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - [SoftwareStore] - " \
                    "Validate Update Log Storage Policy on SQL Agents by Client Group workflow"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.WORKFLOW
        self.feature = self.features_list.WORKFLOW
        self.show_to_user = False
        self.browser = None
        self.webconsole = None
        self.store = None
        self.store_config = None
        self.storeutils = StoreUtils(self)
        self.workflow_name = "Update Log Storage Policy on SQL Agents by Client Group"

        self.sqlhelper = None
        self.sqlmachine = None
        self.workflow = None
        self.tcinputs = {
            "SQLServerUser": None,
            "SQLServerPassword": None
        }

        self.entities = None
        self.client_group = None
        self.client_group_list = []
        self.client_groups_map = None
        self.storagepolicy = None
        self.storagepolicy_new = None

    def init_tc(self):
        """Initializes this test case."""
        try:
            self.store_config = config.get_config().Cloud
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword']
            )
            self.webconsole.wait_till_load_complete()
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store(
                username=self.store_config.username,
                password=self.store_config.password
            )

            # get workflow package status
            pkg_status = self.store.get_package_status(
                self.workflow_name,
                category="Workflows"
            )
            if pkg_status == "Install":
                # install workflow package
                self.store.install_workflow(
                    self.workflow_name, refresh=True
                )
            else:
                self.log.info(
                    f"[{0}] does not have [Install] status, found [{1}]. Attempting to open."
                        .format(self.workflow_name, pkg_status)
                )

        except Exception as excp:
            raise CVTestCaseInitFailure(excp) from excp

    def run(self):
        """Main function for test case execution"""
        log = self.log

        clientname = self.client.client_name
        instancename = self.instance.instance_name
        sqluser = self.tcinputs["SQLServerUser"]
        sqlpass = self.tcinputs["SQLServerPassword"]

        self.entities = CVEntities(self)

        time1 = (datetime.now()).strftime("%H:%M:%S")
        sptime = time1.replace(":", "")
        storage_temp_name = "SQLSP_{0}_{1}".format(self.id, sptime)
        self.client_group = "SQL_CCG_{0}".format(time1)

        self.sqlmachine = Machine(clientname)
        self.sqlhelper = SQLHelper(self, clientname, instancename, sqluser, sqlpass)

        try:
            log.info("Started executing {0} testcase".format(self.id))

            self.init_tc()
            self.commcell.workflows.refresh()
            self.workflow = WorkflowHelper(self, self.workflow_name, deploy=False)

            self.sqlhelper.sql_setup(noof_dbs=1)
            self.subclient = self.sqlhelper.subclient

            self.storagepolicy = self.instance.subclients.get(
                self.instance.subclients.default_subclient
            ).storage_policy

            library_name = self.commcell.storage_policies.get(
                self.instance.subclients.get(self.instance.subclients.default_subclient).storage_policy
            ).library_name
            media_agent = self.commcell.disk_libraries.get(library_name).media_agents_associated[0]

            if not self.commcell.storage_policies.has_policy(storage_temp_name):
                self.commcell.storage_policies.add(storage_temp_name, library_name, media_agent, number_of_streams=10)
            self.storagepolicy_new = self.commcell.storage_policies.get(storage_temp_name).name

            # create client group and assign client to it
            self.client_group_list.append(self.client_group)
            self.client_groups_map = self.entities.create_client_groups(self.client_group_list)
            client_group_obj = self.client_groups_map[self.client_group]['object']
            self.entities.update_clientgroup(client_group_obj, clients_to_add=clientname)

            # run a full backup
            self.sqlhelper.sql_backup('Full')

            # run a TL backup - record log storage policy used
            job_id = self.sqlhelper.sql_backup('transaction_log')

            job = Job(self.commcell, job_id)

            if self.storagepolicy != job.details['jobDetail']['generalInfo']['storagePolicy']['storagePolicyName']:
                raise Exception("Storage policy used is not matching expected result.")

            # Start workflow execution
            self.workflow.execute(
                {
                    'clientGroup': self.client_group,
                    'storagePolicy': self.storagepolicy_new
                }
            )

            # run a TL backup - record log storage policy used. Should match what WF modified.
            job_id = self.sqlhelper.sql_backup('transaction_log')

            job = Job(self.commcell, job_id)

            if self.storagepolicy_new != job.details['jobDetail']['generalInfo']['storagePolicy']['storagePolicyName']:
                raise Exception("Storage policy used is not matching expected result.")

            log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as excp:
            log.error('Failed with error: {0}').format(excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function"""

        # Start workflow execution to revert storage policy
        self.workflow.execute(
            {
                'clientGroup': self.client_group,
                'storagePolicy': self.storagepolicy
            }
        )

        # delete workflow
        self.workflow.delete(self.workflow_name)
        # delete client group
        self.entities.delete_client_groups(self.client_groups_map)
        # delete databases, subclients, storage policies
        self.sqlhelper.sql_teardown()
