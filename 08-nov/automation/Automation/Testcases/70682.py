# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  Initial configuration for the test case

    is_ibmi_vtl_plan_exist()        -- check if IBMi VTL Plan exists

    navigate_to_file_server_tab     -- Navigates to file server tab of Protect--> File Servers

    navigate_to_client_subclient_tab -- Navigates to the subclient page for IBMi clients

    create_ibmi_client()            --  Create new IBMi client machine.

    validate_plan_with_client()     --  Validate if IBMi client got the VTL plan assigned or not

    validate_plan_with_subclient()  -- Validate if IBMi autocreated subclient got the VTL plan assigned or not

    retire()                        --  Retire the IBMi client

    create_user_defined_backupset()	--  Create a new backupset

    create_user_defined_subclient() --  Create a new IBMi Subclient with VTL Plan assigned

    verify_client_existence()       --  Check if IBMi client entity present

    assign_plan_to_ibmi_client()    --  Assign the VTL Plan to IBMi client

    create_user_defined_backupset() --  Create a new IBMi backupset

    generate_strong_password()      --  generate random and strong password

    run()                           --  run function of this test case

Input Example:

    "testCases":
            {
                "70682":
                        {
                            "PlanName":"Test-Auto",
                            "ClientName": "Existing-client",
                            "AccessNode": ["proxy1", "proxy2"],
                            "HostName": "IBMi-host-name",
                            "TestPath": "/QSYS.LIB"
                        }
            }

"""

import random
import string

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_Subclient_details import SubclientOverview
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient, Overview
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Assign and validate IBMi VTL plan with IBMi client, backupSet and subclient."
        self.browser = None
        self.admin_console = None
        self.client_obj = None
        self.display_name = None
        self.navigator = None
        self.new_client_name = None
        self.subclient_name = None
        self.helper = None
        self.browser = None
        self.hostname = None
        self.username = None
        self.password = None
        self.RfsSubclient = None
        self.backupset_name = None
        self.Rfile_servers = None
        self.plan_name = None
        self.plans_page = None
        self.subclient_details_overview = None
        self.vtl_plan = None
        self.overview = None
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PlanName": None,
            "TestPath": None,
            "HostName": None,
            "VTLLibrary": None,
            "VTLPlanName": None
        }

    def setup(self):
        """ Initial configuration for the test case. """

        try:
            # Initialize test case inputs
            self.log.info("***TESTCASE: %s***", self.name)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.Rfile_servers = FileServers(self.admin_console)
            self.RfsSubclient = Subclient(self.admin_console)
            self.plans_page = Plans(self.admin_console)
            self.subclient_details_overview = SubclientOverview(self.admin_console)
            # self.page = PageContainer(self.admin_console)
            self.overview = Overview(self.admin_console)
            self.backupset_name = "non-default"
            self.new_client_name = "IBMi-TC_{0}".format(self.id)
            self.vtl_plan = self.tcinputs['VTLPlanName']
            self.subclient_name = "SC_{0}".format(self.id)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def is_ibmi_vtl_plan_exist(self):
        """check if IBMi VTL Plan exists"""
        self.navigator.navigate_to_plan()
        all_vtl_plans = self.plans_page.list_plans(plan_type="IBM i VTL")
        return self.vtl_plan in all_vtl_plans

    def navigate_to_client_subclient_tab(self):
        """Navigates to the subclient page for IBMi clients"""
        self.Rfile_servers.navigate_to_file_server_tab()
        self.Rfile_servers.access_server(self.new_client_name)
        self.admin_console.access_tab("Subclients")

    @test_step
    def create_ibmi_client(self, withplan):
        """
        Create new IBMi client with or without VTL plan assigned
        Args:
            withplan(bool)      : assign a VTL plan during IBMi client creation
        """
        self.Rfile_servers.navigate_to_file_server_tab()
        notification = self.Rfile_servers.add_ibmi_client(server_name=self.new_client_name,
                                                          file_server_host_name=self.new_client_name,
                                                          username=self.tcinputs['UserName'],
                                                          password=self.generate_strong_password(),
                                                          access_node=self.tcinputs['AccessNode'],
                                                          plan=self.vtl_plan if withplan else None
                                                          )
        if 'created successfully' not in notification:
            raise CVTestStepFailure(notification)
        self.admin_console.refresh_page()

    @test_step
    def validate_plan_with_client(self, withplan):
        """
        Validate if IBMi client got the VTL plan assigned or not
        Args:
            withplan(bool)      : assign a VTL plan during IBMi client creation
        """
        self.Rfile_servers.navigate_to_file_server_tab()
        self.Rfile_servers.access_server(self.new_client_name)

        protection_panel = RPanelInfo(self.admin_console, title="Protection summary")
        assigned_plan = protection_panel.get_details()['Plan']
        if withplan:
            if assigned_plan != self.vtl_plan:
                raise Exception("IBMi client doesn't got IBM i VTL Plan assigned")
        else:
            if assigned_plan != "Not assigned":
                raise Exception("IBMi client got Plan assigned which is not specified during client creation")

    @test_step
    def validate_plan_with_subclient(self,
                                     withplan,
                                     backupset_name='defaultBackupSet',
                                     all_subclients=True):
        """
        Validate if IBMi autocreated subclient got the VTL plan assigned or not
        Args:
            withplan(bool)      : assign a VTL plan during IBMi client creation
            backupset_name(str) : BackupSet name
            all_subclients(bool): verify all auto-crated subclients
        """
        if all_subclients:
            subclient_names = ['*SECDTA', '*CFG', '*IBM', '*ALLDLO', '*ALLUSR', '*LINK', '*HST log']
            if backupset_name == "defaultBackupSet":
                subclient_names.append('DR Subclient')
        else:
            subclient_names = [self.subclient_name]
        self.navigate_to_client_subclient_tab()
        for each in subclient_names:
            assigned_plan = self.RfsSubclient.get_ibmi_subclient_plan_details(backupset_name=backupset_name,
                                                                              subclient_name=each)
            if withplan:
                if self.vtl_plan not in assigned_plan:
                    raise Exception("IBMi subclient {0} doesn't got IBM i VTL Plan assigned. it has {1}".format(
                        each, assigned_plan))
            else:
                if assigned_plan != 'Not assigned':
                    raise Exception("IBMi subclient {0} has plan {1} assigned.".format(each, assigned_plan))
            self.admin_console.select_hyperlink(self.new_client_name)
            self.admin_console.access_tab("Subclients")

    def retire(self):
        """ Retire the IBMi client"""
        self.Rfile_servers.navigate_to_file_server_tab()
        notification = self.Rfile_servers.retire_ibmi_client(server_name=self.new_client_name)
        if 'retired successfully' not in notification:
            raise CVTestStepFailure(notification)
        self.admin_console.refresh_page()

    @test_step
    def create_user_defined_backupset(self):
        """ Create a new backupset with VTL plan assined
        """
        self.navigate_to_client_subclient_tab()
        if not self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name):
            self.RfsSubclient.add_ibmi_backupset(backupset_name=self.backupset_name,
                                                 plan_name=self.tcinputs['PlanName'])
            self.admin_console.refresh_page()

    @test_step
    def create_user_defined_subclient(self):
        """ Create a new IBMi Subclient with VTL Plan assigned """
        # self.navigate_to_subclient_tab()
        self.RfsSubclient.add_ibmi_subclient(subclient_name=self.subclient_name,
                                             backupset_name=self.backupset_name,
                                             plan_name=self.vtl_plan,
                                             content_paths=["/tmp123"]
                                             )
        self.admin_console.refresh_page()

    def verify_client_existence(self):
        """Check if IBMi client entity present"""
        self.Rfile_servers.navigate_to_file_server_tab()
        return self.Rfile_servers.is_client_exists(server_name=self.new_client_name)

    @test_step
    def assign_plan_to_ibmi_client(self):
        """ Assign the VTL Plan to IBMi client
        """
        self.Rfile_servers.navigate_to_file_server_tab()
        self.Rfile_servers.access_server(self.new_client_name)
        self.log.info("Update the VTL plan to client on overview page")
        self.overview.modify_ibmi_plan_from_protection_summary(plan_name=self.vtl_plan)
        self.admin_console.refresh_page()

    @test_step
    def create_user_defined_backupset(self):
        """ Create a new IBMi backupset
        """
        self.navigate_to_client_subclient_tab()
        if not self.RfsSubclient.is_backupset_exists(backupset_name=self.backupset_name):
            self.RfsSubclient.add_ibmi_backupset(backupset_name=self.backupset_name,
                                                 plan_name=self.vtl_plan)
            self.admin_console.refresh_page()

    def generate_strong_password(self):
        """ generate random and strong password
            :return: return random password
        """
        password = ''.join(random.choice(string.ascii_uppercase +
                                         string.digits +
                                         string.ascii_lowercase +
                                         string.punctuation) for _ in range(10))
        return password

    def run(self):
        try:
            if not self.is_ibmi_vtl_plan_exist():
                raise CVTestStepFailure("IBMi VTL Plan '{0}' does not exists".format(self.vtl_plan))
            if self.verify_client_existence():
                self.retire()
            self.log.info("- - - * - * - * - * # CREATE IBMi CLIENT WITH VTL PLAN - * - * - * - * - * - * - * ")
            self.create_ibmi_client(withplan=True)
            self.log.info("- * - * - * - * - * # CREATE BACKUPSET WITH VTL PLAN - * - * - * - * - * - * - * # ")
            self.create_user_defined_backupset()
            self.log.info("- * - * - * # VALIDATE IF VTL PLAN IS ASSIGNED TO CLIENT - * - * - * - * - * - * # ")
            self.validate_plan_with_client(withplan=True)
            self.log.info("- * # VALIDATE IF VTL PLAN IS ASSIGNED ALL SUBCLIENTS OF DEFAULTBACKUPSET - * - * #")
            self.validate_plan_with_subclient(withplan=True)
            self.log.info("- * # VALIDATE IF VTL PLAN IS ASSIGNED ALL SUBCLIENTS OF USER-DEFINED BACKUPSET - * - * ")
            self.validate_plan_with_subclient(withplan=True, backupset_name=self.backupset_name)
            self.log.info("- * # CREATE IBMi CUSTOM CONTENT SUBCLIENT WITH VTL PLAN ASSIGNED - * - * - * - * ")
            self.create_user_defined_subclient()
            self.log.info("- * # VALIDATE IF VTL PLAN IS ASSIGNED SUBCLIENT OF USER-DEFINED BACKUPSET - * - * ")
            self.validate_plan_with_subclient(withplan=True, backupset_name=self.backupset_name, all_subclients=False)
            self.retire()
            self.log.info("- * - * - * - * - * # CREATE IBMi CLIENT WITHOUT VTL PLAN - * - * - * - * - * - * # ")
            self.create_ibmi_client(False)
            self.log.info("- * - * - * # VALIDATE IF NO PLAN IS ASSIGNED TO CLIENT - * - * - * - * - * - * # ")
            self.validate_plan_with_client(False)
            self.log.info("- * # VALIDATE IF VTL NO PLAN IS ASSIGNED ALL SUBCLIENTS OF DEFAULTBACKUPSET - * - * #")
            self.validate_plan_with_subclient(withplan=False)
            self.log.info("- * # ASSIGN VTL PLAN TO IBMi CLIENT AND VALIDATE IF ALL SUBCLIENTS OF DEFAULTBACKUPSET "
                          " GOT PLAN ASSIGNED- * - * #")
            self.assign_plan_to_ibmi_client()
            self.log.info("- * - * - * # VALIDATE IF VTL PLAN IS ASSIGNED TO CLIENT - * - * - * - * - * - * # ")
            self.validate_plan_with_client(withplan=True)
            self.log.info("- * # VALIDATE IF VTL PLAN IS ASSIGNED ALL SUBCLIENTS OF DEFAULTBACKUPSET - * - * -")
            self.validate_plan_with_subclient(withplan=True)
            self.retire()

        except Exception as exception:
            handle_testcase_exception(self, exception)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
