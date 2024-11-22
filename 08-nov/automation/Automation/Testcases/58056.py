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
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA  backup
    and Restore test case - v2 Indexing"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE V2 Indexing Streaming : Remote File Cache Pruning cases"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = backup_options = None
            self.log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            proxy_list = self.subclient.subclient_proxy
            Indexservername = auto_subclient.get_index_name()
            finalma = auto_subclient.get_final_ma()
            #check services are up on all proxies and media agents
            machinenames =[proxy_list[1],proxy_list[0],Indexservername,finalma[0]]
            for eachname in machinenames:
                auto_subclient.start_service(eachname, self.tcinputs.get('username'), self.tcinputs.get('password'))

            VirtualServerUtils.decorative_log("FULL Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            if backup_options.collect_metadata:
                raise Exception("Metadata collection is enabled")
            auto_subclient.backup(backup_options)

            _Parent_jobid = auto_subclient.backup_job.job_id
            self.log.info("Parent JobID : %s ", _Parent_jobid)

            """ Validate and Delete metadata files from RFC """
            VirtualServerUtils.decorative_log("Validate and Delete the metadata files from RFC")
            full_srclist = ['vmcollect_'+str(_Parent_jobid)+'.cvf']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
		                        "path post validation")
            auto_subclient.validate_rfc_files(Indexservername, _Parent_jobid, full_srclist, delete_rfc=True)
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " FULL VM out of Place restores " + "-" * 25)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            VirtualServerUtils.decorative_log("INCREMENTAL Backup")
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)

            _Parent_jobid = auto_subclient.backup_job.job_id

            """ Validate and Delete metadata files from RFC """
            VirtualServerUtils.decorative_log("Validate and Delete metadata files from RFC ")
            full_srclist = ['vmcollect_'+str(_Parent_jobid)+'.cvf']
            self.log.info("Validate RFC Cache paths for backup job created & delete RFC "
                          "path post validation")
            auto_subclient.validate_rfc_files(Indexservername, _Parent_jobid, full_srclist, delete_rfc=True)

            try:
                VirtualServerUtils.decorative_log("Files restores - v2 Indexing")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.browse_ma = Indexservername
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(file_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " FULL VM out of Place restores " + "-" * 25)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s ', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
