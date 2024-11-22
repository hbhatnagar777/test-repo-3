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
        self.name = "Virtual Server - VMWare V2 - Streaming-Snap Synth Full Scenarios for multiple subclients " \
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

            VirtualServerUtils.decorative_log("Incremental Snap Backup without backup copy - Subclient 2")
            backup_options2 = OptionsHelper.BackupOptions(auto_subclient2)
            backup_options2.advance_options = {"create_backup_copy_immediately": False}
            backup_options2.backup_method = "SNAP"
            backup_options2.backup_type = "INCREMENTAL"
            auto_subclient2.backup(backup_options2)

            VirtualServerUtils.decorative_log("SynthFull for Streaming Backup - Subclient 1")
            backup_options.backup_type = "SYNTHETIC_FULL"
            backup_options.incr_level = ""
            auto_subclient.backup(backup_options)

            # synth full should fail on subclient 2 as it's not backup copied
            VirtualServerUtils.decorative_log("SynthFull for Snap Backup (without backup copy) - Subclient 2")
            backup_options2.backup_method = "SNAP"
            backup_options2.backup_type = "SYNTHETIC_FULL"
            backup_options2.incr_level = ""
            try:
                auto_subclient2.backup(backup_options2)
                # if we proceed past this point in try, testcase fails
                exp = "Synth full seems to have completed on subclient 2 which shouldn't happen without backup copy"
                self.log.error('Failed with error: ' + str(exp))
                self.ind_status = False
                self.failure_msg = str(exp)
            except Exception as exp:
                self.log.info("Synth full failed AS EXPECTED because subclient is not backup copied")
                self.log.info('Synth full Failed with error: {0}'.format(exp))


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
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED