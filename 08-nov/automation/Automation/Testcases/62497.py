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

"""
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VsaTestCaseUtils, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants
from cvpysdk.backupsets.vsbackupset import VSBackupset
from cvpysdk.subclients.vssubclient import VirtualServerSubclient

class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - VMWare V2 - Streaming Synth Full Scenarios for multiple subclients " \
                    "backing up same VM"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None,
            "BackupsetName2": None,
            "SubclientName2": None
        }
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            self.backupset = VSBackupset(self.instance, self.tcinputs["BackupsetName2"])
            self.subclient = VirtualServerSubclient(self.backupset, self.tcinputs["SubclientName2"])
            auto_subclient2 = VirtualServerUtils.subclient_initialize(self)

            # need to have one prior FUll job present on these subclients as we are directly running incremental
            # if not, testcase will fail as job type validation will fail.
            VirtualServerUtils.decorative_log("Incremental Streaming Backup - Subclient 1")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)

            VirtualServerUtils.decorative_log("Incremental Streaming Backup - Subclient 2")
            backup_options2 = OptionsHelper.BackupOptions(auto_subclient2)
            backup_options2.backup_type = "INCREMENTAL"
            auto_subclient2.backup(backup_options2)

            VirtualServerUtils.decorative_log("SynthFull Streaming Backup - Subclient 1")
            backup_options.backup_type = "SYNTHETIC_FULL"
            backup_options.incr_level = ""
            auto_subclient.backup(backup_options)

            # if synth full runs successfully for subclient 2 now, it means it wasn't triggered for this subclient
            # automatically when we ran synth full for subclient 1
            VirtualServerUtils.decorative_log("SynthFull Streaming Backup - Subclient 2")
            backup_options2.backup_type = "SYNTHETIC_FULL"
            backup_options2.incr_level = ""
            auto_subclient2.backup(backup_options2)


        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.ind_status = False
            self.failure_msg = str(exp)

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
                auto_subclient2.cleanup_testdata(backup_options2)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
