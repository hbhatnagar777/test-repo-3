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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VirtualServerHelper
from AutomationUtils import logger, constants
from cvpysdk.client import Client, Clients




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "V2 Hypervisor - Delete API validation for the VM in de-configure state and without packages"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)

            log.info(
                "-------------------Initialize helper objects------------------------------------")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)
            #Delete Vm through delete API with no force deletion
            VirtualServerUtils.decorative_log('Delete Vm through delete API with no force deletion')
            self.commcell.clients.refresh()
            time.sleep(30)
            client = Clients(self.commcell)
            for eachvm in auto_subclient.vm_list:
                res = Client(self.commcell, eachvm)
                res.retire()
                client.delete(eachvm, forceDelete=False)
            #Validating if VM got deleted
            for eachvm in auto_subclient.vm_list:
                auto_commcell.statuscheck(1, 2,status = 'deleted', clientname = [eachvm])
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.status = constants.FAILED