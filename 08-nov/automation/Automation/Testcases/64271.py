# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this tesc case
"""
import time
from AutomationUtils.cvtestcase import CVTestCase, constants
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VirtualServerHelper as VirtualServerhelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Nutanix failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Nutanix failover file level restore validation by turning down services on MA after backup copy job completed"
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
            # check services are up on all the proxies and media agents
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
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            # Running backup copy job
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            # stop MA servcies
            auto_subclient.stop_service(finalma[0], 'GxCVD(Instance001)')
            VirtualServerUtils.decorative_log("wait for 30 min's for RFC server switch to happen")
            time.sleep(600)
            try:
                VirtualServerUtils.decorative_log(
                    "-" * 25 + " Files restores " + "-" * 25)
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.browse_from_backup_copy = True
                fs_restore_options.is_ma_specified = True
                fs_restore_options.browse_ma = finalma[0]
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(fs_restore_options, discovered_client=vm)
            except Exception as exp:
                self.log.error("Restore job Failed")
                raise Exception
            # start MA services
            auto_subclient.start_service(finalma,
                                         self.tcinputs.get('username'),
                                         self.tcinputs.get('password'))
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
        except Exception as exp:
            self.log.error('Failed with error [{}]'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
