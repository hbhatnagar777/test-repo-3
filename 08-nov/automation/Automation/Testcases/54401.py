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

** Note** Requires trials.txt file for testcase execution if not case is skipped

PowerCli should be installed on the controller machine

"""

import json

from cvpysdk.commcell import Commcell

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from CVTrials.trial_helper import TrialHelper
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.Setup.login import LoginPage
from AutomationUtils.database_helper import CommServDatabase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Commvault Express Trial - VSA backup and restore from Admin console"
        self.browser = None
        self.driver = None
        self.helper = None
        self.trial_file = None
        self.contents = None
        self.test_individual_status = True
        self.test_individual_failure_message = ""

        self.machine = Machine()

    def setup(self):
        """Initializes pre-requisites for this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.helper = TrialHelper(self)

    def run(self):
        """Main function for test case execution"""
        try:
            try:
                self.trial_file = self.machine.join_path(constants.CVTRIALS_DIRECTORY, 'trials.txt')
                self.contents = json.loads(self.machine.read_file(self.trial_file))
                assert self.contents['status'] == 'passed'
            except Exception as err:
                self.log.error(err)
                self.status = constants.SKIPPED
                return

            # To login to admin console
            login = LoginPage(self.driver)

            # To navigate to admin console page
            login.navigate(self.contents.get('URL'))

            login.login(
                self.contents.get('Commvault ID'),
                self.contents.get('Password')
            )

            # To initialize basic SDK objects
            commcell = Commcell(
                self.contents.get('Commcell'),
                self.contents.get('Commvault ID'),
                self.contents.get('Password')
            )
            client = commcell.clients.get(self.contents['Client'])
            agent = client.agents.get(self.contents['Agent'])
            instance = agent.instances.get(self.contents['Instance'])
            backupset = instance.backupsets.get(self.contents['Backupset'])
            subclient = backupset.subclients.get(self.contents['Subclient'])
            csdb = CommServDatabase(commcell)
            self.log.info('Successfully created basic SDK objects for this case')

            # To create Basic VSA objects
            vsa_obj = AdminConsoleVirtualServer(instance, self.driver, commcell, csdb)
            vsa_obj.hypervisor = self.contents['Client']
            vsa_obj.instance = self.contents['Instance']
            vsa_obj.subclient = self.contents['Subclient']
            vsa_obj.subclient_obj = subclient

            self.log.info("Created VSA object successfully. Now starting a backup")
            vsa_obj.backup_type = "FULL"
            vsa_obj.backup()

            try:
                # Restoring test data to the source VM in a different path
                decorative_log("Restoring data to source VM to different path")
                vsa_obj.guest_files_restore(in_place=False)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

            try:
                # Restoring the VM to the same ESX host
                decorative_log("Restoring data to same ESX host")
                vsa_obj.unconditional_overwrite = True
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.browser.close_silently(self.browser)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
