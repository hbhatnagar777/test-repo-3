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
from Server.Security.userhelper import UserHelper


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
        self.name = "Installation with the different client name, same hostname – without install capabilities on" \
                    " the existing client"
        self.config_json = None
        self.client_1 = None
        self.client_2 = None
        self.sim_caller = None
        self.client_hostname = None
        self.username_1 = None
        self.username_2 = None
        self.password_enc = None
        self.password = None
        self.options_selector = None
        self.user_helper = None
        self.email_id_1 = None
        self.email_id_2 = None
        self.entity_dict = None
        self.default = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.client_1 = self.config_json.Install.windows_client.client_name_1
        self.client_2 = self.config_json.Install.windows_client.client_name_2
        self.client_hostname = self.config_json.Install.windows_client.machine_host_1
        self.username_1 = self.config_json.Install.user_details.user1
        self.username_2 = self.config_json.Install.user_details.user2
        self.password = self.config_json.Install.windows_client.machine_password
        self.password_enc = self.config_json.Install.windows_client.machine_password_enc
        self.email_id_1 = self.config_json.Install.user_details.email_id_1
        self.email_id_2 = self.config_json.Install.user_details.email_id_2
        self.sim_caller = SimCallHelper(self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
        self._log = logger.get_log()
        self.user_helper = UserHelper(self.commcell)
        self.entity_dict = {
            'assoc1': {
                'clientName': [self.commcell.commserv_hostname.split('.')[0]],
                'role': ['Master']
            }
        }

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
            self.validate_client_name(self.client_1)

            # Create a new user
            try:
                self.user_helper.create_user(
                    self.username_1,
                    self.email_id_1,
                    self.default,
                    self.default,
                    self.password,
                    ['master'])
            except:
                self.log.info("User already exists")

            self._log.info(
                "Registering client {0} with hostname {1} to CS by user {2}".format(self.client_1,
                                                                                    self.client_hostname,
                                                                                    self.username_1))
            # Register a new client with main user
            self.sim_caller.install_new_client(
                self.client_1,
                self.client_hostname,
                self.username_1,
                self.password_enc)
            self._log.info(
                "Registered client {0} with hostname {1} to CS".format(self.client_1, self.client_hostname))

            # Create a new user without install capabilities on the previous client
            self.user_helper.create_user(
                self.username_2,
                self.email_id_2,
                self.default,
                self.default,
                self.password,
                self.default,
                self.entity_dict
            )

            self._log.info("Install different client with same hostname when user doesn't have install capabilities "
                           "on already existing instance")
            self._log.info(
                "Reinstalling client {0} with hostname {1} to CS by different user {2}".format(self.client_2,
                                                                                               self.client_hostname,
                                                                                               self.username_2))
            # Registering client with new user
            self.sim_caller.install_new_client(
                self.client_2,
                self.client_hostname,
                self.username_2,
                self.password_enc)
            self._log.info(
                "Reinstalled client {0} with hostname:{1} to CS".format(self.client_2, self.client_hostname))

            # Deleting users from commcell
            self.user_helper.delete_user(self.username_1, self.default, 'master')
            self.user_helper.delete_user(self.username_2, self.default, 'master')

            # Retiring clients from commcell
            self.options_selector.delete_client(self.client_1)
            self.options_selector.delete_client(self.client_2)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.commcell.users.has_user(self.username_1):
                self.user_helper.delete_user(self.username_1, self.default, 'master')
            if self.commcell.users.has_user(self.username_2):
                self.user_helper.delete_user(self.username_2, self.default, 'master')
            if self.commcell.clients.has_client(self.client_1):
                self.options_selector.delete_client(self.client_1)
            if self.commcell.clients.has_client(self.client_2):
                self.options_selector.delete_client(self.client_2)

        except Exception as exp:
            self.log.error('Failed to execute teardown with error: %s', exp)
