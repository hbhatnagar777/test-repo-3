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
    __init__()              --  initialize TestCase class

    setup()                 --  setup function of this test case

    validate_client_name()  --  validate client in commcell

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""

from AutomationUtils import logger, constants, config
from AutomationUtils.cvtestcase import CVTestCase
from Install.sim_call_helper import SimCallHelper
from AutomationUtils.options_selector import OptionsSelector
from Server.Security.securityhelper import OrganizationHelper
from Server.organizationhelper import OrganizationHelper as OH

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "Installation with the same client name and same hostname - using Authcode"
        self.config_json = None
        self.client = None
        self.sim_caller = None
        self.client_hostname = None
        self.company_1 = None
        self.company_2 = None
        self.c_name_1 = None
        self.c_name_2 = None
        self.email_1 = None
        self.email_2 = None
        self.c_domain_1 = None
        self.c_domain_2 = None
        self.username = None
        self.user = None
        self.password = None
        self.authcode_1 = None
        self.authcode_2 = None
        self.options_selector = None
        self.security_helper = None
        self.default = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.client = self.config_json.Install.windows_client.client_name_1
        self.client_hostname = self.config_json.Install.windows_client.machine_host_1
        self.username = self.config_json.Install.user_details.user1
        self.password = self.config_json.Install.windows_client.machine_password_enc
        self.company_1 = self.config_json.Install.comp_details.comp1
        self.company_2 = self.config_json.Install.comp_details.comp2
        self.c_name_1 = self.config_json.Install.comp_details.cname1
        self.c_name_2 = self.config_json.Install.comp_details.cname2
        self.c_domain_1 = self.config_json.Install.comp_details.cdomain1
        self.c_domain_2 = self.config_json.Install.comp_details.cdomain2
        self.email_1 = self.config_json.Install.comp_details.email1
        self.email_2 = self.config_json.Install.comp_details.email2
        self.sim_caller = SimCallHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self._log = logger.get_log()
        self.company_creator = OH(self.commcell)
        self.company_creator.create(self.company_1)
        self.security_helper = OrganizationHelper(self.commcell, self.company_1)

    def validate_client_name(self, client_name):
        """
            Validate client name

            client_name       (str)       -- Name of the client to be validated

                default : None
        """
        if self.commcell.clients.has_client(client_name):
            raise Exception(f'Client {client_name} already exists in Commcell')

    def run(self):
        """Run function of this test case"""
        try:
            # Validate client name
            self.validate_client_name(self.client)

            # Generate authcode for the company
            self.authcode_1 = self.security_helper.modify_auth_code('enable')

            self._log.info(
                "Registering client {0} with hostname {1} to CS".format(self.client, self.client_hostname))
            # Register a new client with new company user
            self.sim_caller.install_new_client(
                self.client,
                self.client_hostname,
                self.username,
                self.password,
                self.authcode_1)
            self._log.info(
                "Registered client {0} with hostname {1} to CS".format(self.client, self.client_hostname))

            self._log.info("Reinstall client with same hostname when the user have install capabilities")
            self._log.info(
                "Reinstalling client {0} with hostname {1} to CS".format(self.client, self.client_hostname))
            # Register a new client with new company user
            self.sim_caller.install_new_client(
                self.client,
                self.client_hostname,
                self.username,
                self.password,
                self.authcode_1)
            self._log.info(
                "Reinstalled client {0} with hostname:{1} to CS".format(self.client, self.client_hostname))

            # Create a new company without install capabilities on the previous client
            self.company_creator.create(self.company_2)
            self.security_helper = OrganizationHelper(self.commcell, self.company_2)

            # Generate authcode for the company
            self.authcode_2 = self.security_helper.modify_auth_code('enable')

            self._log.info("Reinstall client with same hostname when the user doesn't have install capabilities")
            self._log.info(
                "Reinstalling client {0} with hostname {1} to CS".format(self.client, self.client_hostname))

            # Registering client with new company user
            self.sim_caller.install_new_client(
                self.client,
                self.client_hostname,
                self.username,
                self.password,
                self.authcode_2)
            self._log.info(
                "Reinstalled client {0} with hostname:{1} to CS".format(self.client, self.client_hostname))

            # Retiring clients from commcell
            self.options_selector.delete_client(self.client + '___1')
            if self.commcell.clients.has_client(self.client):
                self.options_selector.delete_client(self.client)

            # Deleting companies from commcell
            self.commcell.organizations.delete(self.company_1)
            self.commcell.organizations.delete(self.company_2)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:

            if self.commcell.clients.has_client(self.client + '___1'):
                self.options_selector.delete_client(self.client + '___1')
            if self.commcell.clients.has_client(self.client):
                self.options_selector.delete_client(self.client)
            if self.commcell.organizations.has_organization(self.company_1):
                self.commcell.organizations.delete(self.company_1)
            if self.commcell.organizations.has_organization(self.company_2):
                self.commcell.organizations.delete(self.company_2)

        except Exception as exp:
            self.log.error('Failed to execute teardown with error: %s', exp)
