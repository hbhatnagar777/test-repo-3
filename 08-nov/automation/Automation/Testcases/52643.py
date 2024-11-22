# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Test case to check the basic acceptance of SNMP in Admin console.

It verifies
1. Creation of SNMP configuration based on different criteria's passed as arguments
2. Validates if the SNMP configuration is created successfully.
3. Editing of SNMP configuration created in above steps.
4. Deletion of SNMP configuration created, edited & verified in above steps.
"""

import ast
import random

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.SNMPConfigurationHelper import SNMPConfigurationMain

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ Basic Acceptance test for SNMP Configuration """

    def __init__(self):
        """ Initializing the Test case file """

        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for SNMP configuration in AdminConsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.snmp_configuration_obj = None
        self.admin_console = None
        self.tcinputs = {}

    def run(self):
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)

            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.snmp_configuration_obj = SNMPConfigurationMain(self.admin_console)

            random_enc_algos = ",".join(random.sample(SNMPConfigurationMain.encryption_algorithms, 2))
            random_privacy_algos = ",".join(random.sample(SNMPConfigurationMain.privacy_algorithms, 2))
            encryption_algorithm_list = self.tcinputs.get(
                'encryption_value_combo_list', random_enc_algos).split(",")
            privacy_algorithm_list = self.tcinputs.get(
                'privacy_value_combo_list', random_privacy_algos).split(",")

            self.snmp_configuration_obj.config_name = self.tcinputs.get('config_name', 'Test_SNMP_Config')
            self.snmp_configuration_obj.encryption_algorithm = encryption_algorithm_list[0]
            self.snmp_configuration_obj.privacy_algorithm = privacy_algorithm_list[0]

            self.snmp_configuration_obj.create_configuration()
            self.log.info("SNMP configuration created successfully")

            self.snmp_configuration_obj.validate_snmp_configuration()
            self.log.info("Initial validation completed successfuly")

            self.snmp_configuration_obj.config_name = self.tcinputs.get('new_config_name', 'Test_SNMP_Config_New')
            self.snmp_configuration_obj.username = "Tester B"
            self.snmp_configuration_obj.password = "########"
            self.snmp_configuration_obj.encryption_algorithm = [encryption_algorithm_list[1]]
            self.snmp_configuration_obj.privacy_algorithm = [privacy_algorithm_list[1]]

            self.snmp_configuration_obj.modify_configuration()
            self.log.info("SNMP configuration edited successfully")

            self.snmp_configuration_obj.validate_snmp_configuration()
            self.log.info("Validation after editing completed successfully")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.snmp_configuration_obj.del_configuration()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
