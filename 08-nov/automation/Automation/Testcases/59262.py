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
import os
import time
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware failover and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware failover file level restore validation by turning down services on MA/Index server after backup copy job completed"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.test_individual_failure_message = ''
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            log.info(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            proxy_list = self.subclient.subclient_proxy
            Indexservername = auto_subclient.get_index_name()
            finalma = auto_subclient.get_final_ma()
            #check services are up on all the proxies and media agents
            machinenames =[proxy_list[1],proxy_list[0],Indexservername,finalma[0]]
            for eachname in machinenames:
                auto_subclient.start_service(eachname,
                                             self.tcinputs.get('username'),
                                             self.tcinputs.get('password'))
            #checking if any jobs to be backup copied
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            #Running snap job
            VirtualServerUtils.decorative_log("Starting Snap Job")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            #Running backup copy job
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            #stop MA servcies
            auto_subclient.stop_service(finalma[0], 'GxCVD(Instance001)')
            VirtualServerUtils.decorative_log("wait for 30 min's for RFC server switch to happen")
            time.sleep(600)
            try:
                self.log.info(
                    "-" * 25 + " Files restores " + "-" * 25)
                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.browse_from_backup_copy = True
                fs_restore_options.is_ma_specified = True
                fs_restore_options.browse_ma = Indexservername
                for vm in auto_subclient.vm_list:
                    auto_subclient.guest_file_restore(fs_restore_options, discovered_client=vm)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            #start MA services
            auto_subclient.start_service(finalma[0],
                                         self.tcinputs.get('username'),
                                         self.tcinputs.get('password'))
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED