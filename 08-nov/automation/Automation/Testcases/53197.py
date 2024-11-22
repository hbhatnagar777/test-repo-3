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

    run()           --  run function of this test case

"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger
from AutomationUtils import constants

from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Oracle Cloud backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Oracle Cloud Incr Backup and Restore in AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONORACLECLOUD
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.tcinputs = {
            "RestorePath": None
        }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase" % self.id)

            log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            driver = browser.driver

            log.info("Creating the login object")
            login_obj = LoginMain(driver, self.csdb)

            login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                            self.inputJSONnode['commcell']['commcellPassword']
                           )

            log.info("Login completed successfully. Creating object for VSA")

            vsa_obj = AdminConsoleVirtualServer(self.instance, driver,
                                                self.commcell, self.csdb)
            vsa_obj.hypervisor = self.tcinputs['ClientName']
            vsa_obj.instance = self.tcinputs['InstanceName']
            vsa_obj.subclient = self.tcinputs['SubclientName']

            log.info("Created VSA object successfully. Now starting a backup")
            vsa_obj.backup_type = "INCR"
            vsa_obj.backup()

            vsa_obj.restore_path = self.tcinputs['RestorePath']
            vsa_obj.file_level_restore()

            # Restoring the instance
            vsa_obj.full_vm_restore()

            browser.close()

        except Exception as exp:
            browser.close()
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if vsa_obj:
                vsa_obj.cleanup_testdata()
