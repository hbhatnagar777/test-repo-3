# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase, constants
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VirtualServerHelper as VirtualServerhelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Nutanix failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Nutanix failover validation for services down on MA server before backup copy job starts"
        self.tcinputs = {"username": None,
                         "password": None}

    def run(self):
        """Main function for test case execution"""

        try:
            VirtualServerUtils.decorative_log(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            proxy_list = self.subclient.subclient_proxy
            Indexservername = auto_subclient.get_index_name()
            finalma = auto_subclient.get_final_ma()
            # check services are up on all the proxies and media agent machines
            machinenames = [proxy_list[1], proxy_list[0], Indexservername, finalma[0]]
            for eachname in machinenames:
                auto_subclient.start_service(eachname,
                                             self.tcinputs.get('username'),
                                             self.tcinputs.get('password'))
            # checking if any jobs to be backup copied
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            # Running snap job
            VirtualServerUtils.decorative_log("Starting Snap Job")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)
            # stop MA servcies
            auto_subclient.stop_service(finalma[0], 'GxCVD(Instance001)')
            # Running backup copy job
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            # start MA services
            auto_subclient.start_service(finalma[0],
                                         self.tcinputs.get('username'),
                                         self.tcinputs.get('password'))
            try:
                VirtualServerUtils.decorative_log("FULL VM out of Place restores - v2 Indexing")
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                vm_restore_options.browse_from_backup_copy = True
                auto_subclient.virtual_machine_restore(vm_restore_options)
            except Exception as exp:
                self.log.error("Restore job Failed")
                raise Exception
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
        except Exception as exp:
            self.log.error('Failed with error [{}]'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED