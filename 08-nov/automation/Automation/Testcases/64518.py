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

from AutomationUtils.cvtestcase import CVTestCase, constants
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Agent less restore case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AHV - Automation SMB restore VM which has multiple Nics and first IP not reachable to proxy"
        self.ind_status = True
        self.tcinputs = {"sourcevm": None,
                         "destvm": None,
                         "Indextype": None}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)
            try:
                VirtualServerUtils.decorative_log("Agentless file restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.smbrestore = True
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.agentless_file_restore(file_restore_options,
                                                      "SMBRESTORE", self.tcinputs.get('sourcevm'),
                                                       self.tcinputs.get('destvm'),
                                                       self.tcinputs.get('Indextype'))
                self.result_string = str('Using CVWinGuestAPI interface. So SMB approach used')
            except Exception as exp:
                self.log.error('Failed with error: ' + str(exp))
                raise exp
        finally:
            try:
                if auto_subclient and backup_options:
                    auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
