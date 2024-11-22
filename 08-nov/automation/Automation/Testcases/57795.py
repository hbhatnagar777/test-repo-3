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

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - Openstack: Attach Volume to Existing Instance : Across Project"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing the testcase {0}".format(self.id))
            self.log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            self.hvobj = auto_backupset.auto_vsainstance.hvobj
            self.hvobj.destination_project_name = self.tcinputs.get('destination_project_name', None)
            self.hvobj.Source_Security_Grp = self.tcinputs.get('Source_Security_Grp', None)
            self.hvobj.DestinationZone = self.tcinputs.get('DestinationZone', None)

            #-------- Backup for the subclient -------------
            try:
                self.log.info(
                    "-" * 25 + " Backup " + "-" * 25)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            # -------- Attach volume to existing instance restore for the subclient -------------
            try:
                self.log.info(
                    "-" * 25 + " Attach volume to existing instance - across project " + "-" * 25)
                attach_volume_restore_options = OptionsHelper.AttachDiskRestoreOptions(auto_subclient, self)
                self.hvobj.OpenStackHandler.projectName = self.hvobj.destination_project_name
                attach_volume_restore_options.dest_servers = self.hvobj.OpenStackHandler.get_instance_list()
                attach_volume_restore_options.dest_vm = list(attach_volume_restore_options.dest_servers.keys())[0]
                attach_volume_restore_options.dest_vm_guid = list(attach_volume_restore_options.dest_servers.values())[0]
                auto_subclient.attach_volume_restore(attach_volume_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.log.info(
                "-" * 25 + " Cleanup of test data " + "-" * 25)
            if auto_subclient and backup_options:
                self.hvobj.OpenStackHandler.projectName = self.tcinputs.get('project_name', None)
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
               self.result_string = self.test_individual_failure_message
               self.status = constants.FAILED
