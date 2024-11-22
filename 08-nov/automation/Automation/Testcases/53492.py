# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2016 Commvault Systems, Inc.
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
import os

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import logger, constants
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware Live VM Recovery test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of VMware Live Recovery from Streaming backups"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.tcinputs = {
            "RedirectDatastore": None,
            "DelayMigration": None
        }

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            vsa_obj = None
            log.info("Started executing %s testcase", self.id)

            self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
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
            vsa_obj.backup_type = "FULL"
            vsa_obj.backup()

            # Restoring the VM using Live Recovery
            self.log.info("*" * 10 + " Live Recovery " + "*" * 10)
            vsa_obj.unconditional_overwrite = True
            vsa_obj.live_recovery = True
            vsa_obj.redirect_datastore = self.tcinputs['RedirectDatastore']
            vsa_obj.delay_migration = self.tcinputs['DelayMigration']
            vsa_obj.full_vm_restore()

        except Exception as exp:
            log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            browser.close()
            if vsa_obj:
                vsa_obj.cleanup_testdata()
