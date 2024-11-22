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

    tear_down()     --  tear down function of this test case
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants
from Server.MultiCommcell.multicommcellhelper import MultiCommcellHelper
from Server.MultiCommcell import multicommcellconstants
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing multicommcell Test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       —  name of this test case

                applicable_os   (str)       —  applicable os for this test case
                    Ex: self.os_list.WINDOWS

                product         (str)       —  applicable product for this test case
                    Ex: self.products_list.FILESYSTEM

                features        (str)       —  qcconstants feature_list item
                    Ex: self.features_list.DATAPROTECTION

                tcinputs   (dict)      —  dict of test case inputs with input name as dict key
                                            and value as input type
                        Ex: {
                             "MY_INPUT_NAME": "MY_INPUT_TYPE"
        """
        super(TestCase, self).__init__()
        self.name = "Multicommcell - Compatibility and job validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.IDENTITYMANAGEMENT
        self.tcinputs = {
            "SPCommserver": None,
            "SPadminUser": None,
            "SPadminUserPwd": None,
            "v10client": None
        }
        self.sp_user_commcell = None
        self.idp_user_commcell = None
        self.multicommcell_helper = None

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()
        self.tcinputs["IDPCommserver"] = self.inputJSONnode['commcell']['webconsoleHostname']
        self.tcinputs["IDPadminUser"] = self.inputJSONnode['commcell']['commcellUsername']
        self.tcinputs["IDPadminUserPwd"] = self.inputJSONnode['commcell']['commcellPassword']
        self.multicommcell_helper = MultiCommcellHelper(self.tcinputs)
        self.server = ServerTestCases(self)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing %s testcase", self.id)

            test_users = {
                'SPUser': {
                    'userName': multicommcellconstants.USERNAME,
                    'password': multicommcellconstants.PASSWORD
                },
                'IDPUser': {
                    'userName': multicommcellconstants.USERNAME,
                    'password': multicommcellconstants.PASSWORD
                }
            }
            display_name = 'Auto_IDP_Commcell_app_{0}'.format(time.time())
            (self.idp_user_commcell,
                self.sp_user_commcell) = self.multicommcell_helper.saml_config(
                display_name,
                user_dict=test_users
            )

            self._log.info("\tSetting up initial configuration")
            if self.idp_user_commcell:
                self._log.info("Initial configuration is done")
            else:
                self._log.error("Initial configuration failed")
                raise Exception(
                    "Initial configuration failed"
                )

            self.multicommcell_helper.job_validate(
                'FULL',
                self.sp_user_commcell,
                self.tcinputs["v10client"]
            )

        except Exception as exp:
            self.server.fail(exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self._log.info("\tIn FINAL BLOCK")
        self.multicommcell_helper.cleanup_certificates()
