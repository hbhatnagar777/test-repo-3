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

    validate_append_company_name_to_client_name()   -- To validate if pre install workflow appends
    commany name to the client name

    validate_append_custom_string_to_client_name()  -- To validate if pre install workflow appends custom string
    to the client name

    validate_append_username_to_client_name()       -- To validate if pre install workflow appends username to the
    client name

    validate_append_company_name_to_client_name_and_hostname()  -- To validate if pre install workflow appends commany
    name to the client name and hostname

    validate_pre_install_workflow()                 -- To validate pre-install business logic workflow

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector

from Install.sim_call_helper import SimCallHelper

from Server.Workflow.workflowhelper import WorkflowHelper

from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import (CVTestCaseInitFailure, CVTestStepFailure)
from Web.WebConsole.webconsole import WebConsole

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for validating pre install business logic workflow"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW- Pre install business logic validation"
        self.workflow = None
        self.sim_call = None
        self.machine = None
        self.options = None
        self.browser = None
        self.webconsole = None
        self.store = None
        self.organization = None
        self.organization_name = None
        self.temp_dir = None
        self.workflow_name = "PreInstallBusinessLogicWorkflow"

    def setup(self):
        """Initializes pre-requisites for this test case"""

        # To create a machine class object for controller machine
        self.log.info("Create Machine class object for controller machine")
        self.machine = Machine()
        self.log.info('Successfully created machine class object')

        # To create a options selector class object
        self.options = OptionsSelector(self.commcell)

        # To set the temp directory
        self.temp_dir = self.machine.join_path(constants.TEMP_DIR, 'preinstall')
        self.log.info('Temp file storage location "%s"', self.temp_dir)

        # To initiate the WorkFlowHelper class
        self.workflow = WorkflowHelper(self, 'PreInstallBusinessLogicWorkflow', deploy=False)
        self.log.info('Workflow helper object created successfully')

        # To delete the workflow if exists
        self.workflow.delete('PreInstallBusinessLogicWorkflow')

        # To initialize SimCallHelper class
        self.sim_call = SimCallHelper(self.commcell)
        self.log.info('Simcall Helper object created successfully')

        # To create temp directory in Automation folder if not present
        if not self.machine.check_directory_exists(self.temp_dir):
            self.machine.create_directory(self.temp_dir)
            self.log.info('Successfully created temporary directory for Automation')

        # To generate a random organization name
        self.organization_name = self.options.get_custom_str('company')

        # To add a new organization
        self.log.info('Adding new organization: %s', self.organization_name)
        self.organization = self.commcell.organizations.add(
            self.organization_name,
            f'{self.organization_name}@commvault.com',
            f'{self.organization_name}_install',
            f'{self.organization_name}_commvault'
        )
        self.log.info('Successfully added new organization "%s"', self.organization_name)

        # To enable auth code generation for the created organization
        self.organization.enable_auth_code()
        self.log.info('Successfully enabled auth code generation for the organization "%s"',
                      self.organization_name)

    def init_tc(self):
        """
        To initialize browser and open store

        """
        try:
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
                username=_STORE_CONFIG.Cloud.username,
                password=_STORE_CONFIG.Cloud.password
            )

        except Exception as excp:
            raise CVTestCaseInitFailure(excp) from excp

    @test_step
    def start_step1(self):
        """Install status should be shown for workflow when it is not installed"""
        package_status = self.store.get_package_status(self.workflow_name, category="Workflows")
        if package_status != "Install":
            raise CVTestStepFailure(
                f"[{self.workflow}] does "
                f"not have [Install] status, found [{package_status}]"
            )

    @test_step
    def start_step2(self):
        """After installing workflow, status should be Open"""
        self.store.install_workflow(
            self.workflow_name, refresh=True
        )

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.commcell.workflows.refresh()

            # Pre install case to append company name to client name
            self.validate_append_company_name_to_client_name()

            # Pre install case to append custom string to client name
            self.validate_append_custom_string_to_client_name()

            # Pre install case to append username to client name
            self.validate_append_username_to_client_name()

            # Pre install case to append company name to client name and hostname
            self.validate_append_company_name_to_client_name_and_hostname()

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def validate_append_company_name_to_client_name(self):
        """
        To validate if pre install workflow appends commany name to the client name

        """
        config_xml = """
                    <Append>1</Append>
                    <Append_custom_string>false</Append_custom_string>
                    <Custom_string></Custom_string>
                    <Append_username_to_client>false</Append_username_to_client>
                    """

        # To set configuration to the workflow
        self.workflow.modify_workflow_configuration(config_xml)

        # To create a new client
        client_name, client_hostname = self.sim_call.install_new_client(
            auth_code=self.organization.auth_code)

        # To get client name and hostname based on configuration
        client_name, client_hostname = self.workflow.get_client_name_and_hostname_based_on_configuration(
            client_name=client_name,
            client_hostname=client_hostname,
            config_xml=config_xml,
            organization_name=self.organization.domain_name)

        # To validate pre install workflow
        self.validate_pre_install_workflow(
            client_name=client_name,
            client_hostname=client_hostname
        )

        # To delete the created client
        self.options.delete_client(client_name)

        self.log.info('Preinstall workflow to append commany name to client name is successfull')

    def validate_append_custom_string_to_client_name(self):
        """
        To validate if pre install workflow appends custom string to the client name

        """
        config_xml = """
                    <Append>0</Append>
                    <Append_custom_string>true</Append_custom_string>
                    <Custom_string>CV</Custom_string>
                    <Append_username_to_client>false</Append_username_to_client>
                    """

        # To set configuration to the workflow
        self.workflow.modify_workflow_configuration(config_xml)

        # To create a new client
        client_name, client_hostname = self.sim_call.install_new_client()

        # To get client name and hostname based on configuration
        client_name, client_hostname = self.workflow.get_client_name_and_hostname_based_on_configuration(
            client_name=client_name,
            client_hostname=client_hostname,
            config_xml=config_xml)

        # To validate pre install workflow
        self.validate_pre_install_workflow(
            client_name=client_name,
            client_hostname=client_hostname
        )

        # To delete the created client
        self.options.delete_client(client_name)

        self.log.info('Preinstall workflow to append custom string to client name is successfull')

    def validate_append_username_to_client_name(self):
        """
        To validate if pre install workflow appends username to the client name

        """
        config_xml = """
                    <Append>0</Append>
                    <Append_custom_string>false</Append_custom_string>
                    <Custom_string></Custom_string>
                    <Append_username_to_client>true</Append_username_to_client>
                    """

        # To set configuration to the workflow
        self.workflow.modify_workflow_configuration(config_xml)

        # To create a new client
        client_name, client_hostname = self.sim_call.install_new_client()

        # To get client name and hostname based on configuration
        client_name, client_hostname = self.workflow.get_client_name_and_hostname_based_on_configuration(
            client_name=client_name,
            client_hostname=client_hostname,
            config_xml=config_xml)

        # To validate pre install workflow
        self.validate_pre_install_workflow(
            client_name=client_name,
            client_hostname=client_hostname
        )

        # To delete the created client
        self.options.delete_client(client_name)

        self.log.info('Preinstall workflow to append username to client name is successfull')

    def validate_append_company_name_to_client_name_and_hostname(self):
        """
        To validate if pre install workflow appends commany name to the client name and hostname

        """
        config_xml = """
                    <Append>2</Append>
                    <Append_custom_string>false</Append_custom_string>
                    <Custom_string></Custom_string>
                    <Append_username_to_client>false</Append_username_to_client>
                    """

        # To set configuration to the workflow
        self.workflow.modify_workflow_configuration(config_xml)

        # To create a new client
        client_name, client_hostname = self.sim_call.install_new_client(
            auth_code=self.organization.auth_code)

        # To get client name and hostname based on configuration
        client_name, client_hostname = self.workflow.get_client_name_and_hostname_based_on_configuration(
            client_name=client_name,
            client_hostname=client_hostname,
            config_xml=config_xml,
            organization_name=self.organization.domain_name)

        # To validate pre install workflow
        self.validate_pre_install_workflow(
            client_name=client_name,
            client_hostname=client_hostname
        )

        # To delete the created client
        self.options.delete_client(client_name)

        self.log.info('Preinstall workflow to append commany'
                      ' name to client name and client hostname is successfull')

    def validate_pre_install_workflow(
            self,
            client_name=None,
            client_hostname=None):
        """
        To validate pre-install business logic workflow

        Args:
            client_name     (str)   -- Name of the client

            client_hostname (str)   -- Hostname of the client installed

        """
        self.log.info('validating the pre install workflow')

        self.commcell.clients.refresh()

        if not self.commcell.clients.has_client(client_name):
            self.log.error('No client exists with the name "%s"', client_name)
            raise Exception(f'Workflow validation failed, no client exists with name {client_name}')

        if client_hostname and not self.commcell.clients.has_client(client_hostname):
            self.log.error('No client exists with the hostname "%s"', client_hostname)
            raise Exception(f'Workflow validation failed, no client exists with hostname {client_hostname}')

        self.log.info('Pre install workflow validation is successfull')

    def tear_down(self):
        """To clean-up the test case environment created"""
        # To close the browser
        self.browser.close()

        # To delete the workflow
        self.workflow.delete('PreInstallBusinessLogicWorkflow')

        # To delete the created organization
        self.commcell.organizations.delete(self.organization_name)
        self.log.info('Successfully deleted the created organization "%s"', self.organization_name)

        # To delete the created temp directory
        self.machine.remove_directory(self.temp_dir)
        self.log.info('successfully deleted the temp directory')
