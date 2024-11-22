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

class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA - VMware - Verify Job is converted to Full when subclient switched from Snap to Streaming" \
                    " and vice versa"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None #initially subclient should have intellisnap enabled
        }
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)

            VirtualServerUtils.decorative_log("Full Snap Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.advance_options = {"create_backup_copy_immediately": False}
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options)

            auto_subclient.toggle_intellisnap() #switch from snap to streaming
            VirtualServerUtils.decorative_log("Try Incremental backup on now switched streaming subclient")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options, override_child_bc_type="FULL") #child job should get converted to full

            auto_subclient.toggle_intellisnap() #switch back to snap
            VirtualServerUtils.decorative_log("Try Incremental Backup on now switched snap subclient")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.advance_options = {"create_backup_copy_immediately": False}
            backup_options.backup_type = "INCREMENTAL"
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options, override_child_bc_type="FULL") #child job should get converted to full


        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.ind_status = False
            self.failure_msg = str(exp)

        finally:
            try:
                auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
