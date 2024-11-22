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
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants
from cvpysdk.client import Client, Clients




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test vmware retire"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware retire validation for Hypervisor with backups"
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
            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerhelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerhelper.AutoVSAVSInstance(auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerhelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerhelper.AutoVSASubclient(auto_backupset, self.subclient)

        #checking Hypervisor configure status on DB ,if de-configure reconfigure Hypervisor
            try:
                VirtualServerUtils.decorative_log(
                    'check Hypervisor status on DB and if de-configure, configure the Hypervisor')
                name = self.tcinputs.get('ClientName')
                client = Client(self.commcell, name, client_id=None)
                query = "SELECT status from APP_CLIENT where Name = '"+name+"'"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
                if output == [['2']]:
                    client.reconfigure_client()
                    query = "SELECT status from APP_CLIENT where Name = '"+name+"'"
                    if output == [['0']]:
                        VirtualServerUtils.decorative_log('Hypervisor configured successfully')
            except Exception as exp:
                raise Exception('--Hypervisor not getting configured---')
            VirtualServerUtils.decorative_log("-" * 25 + " Backup " + "-" * 25)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "Incremental"
            auto_subclient.backup(backup_options)

            #Retire Hypervisor
            try:
                VirtualServerUtils.decorative_log('Retire the client')
                self.commcell.clients.refresh()
                client.retire()
                VirtualServerUtils.decorative_log('Retire client operation ran successfully')
            except Exception as exp:
                self.log.error('---Failed to retire Hypervisor----')
            #Validating if Hypervisor got deleted from GUI
            try:
                VirtualServerUtils.decorative_log('Validating if Hypervisor got deleted from GUI')
                self.commcell.clients.refresh()
                if self.commcell.clients.has_client(client.client_name):
                    VirtualServerUtils.decorative_log(
                        'Hypervisor has been not deleted which is expected since it has backups associated to it')
            except Exception as exp:
                self.log.error('----Hypervisor deleted even backups associated to it----')
                raise Exception
            #Validating DB
            try:
                VirtualServerUtils.decorative_log('checking if Hypervisor deleted status on DB')
                query = "SELECT ID from APP_CLIENT where Name = '"+name+"'"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
                if output != [['']]:
                    VirtualServerUtils.decorative_log('Hypervisor entry found on DB')
            except Exception as exp:
                self.log.error('---Hypervisor deleted as no entry found on DB ---')
                raise Exception

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

            #reconfigure client
            try:
                VirtualServerUtils.decorative_log('Reconfiguring the client')
                self.commcell.clients.refresh()
                client.reconfigure_client()
                VirtualServerUtils.decorative_log('Reconfigure client successfully')
            except Exception as exp:
                self.log.error('---Reconfiguring client failed----')
                raise Exception

            #Validating if Hypervisor got reconfigure state
            try:
                VirtualServerUtils.decorative_log('Checking DB for Hypervisor status')
                query = "SELECT status from APP_CLIENT where Name = '"+name+"'"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
                if output == [['0']]:
                    VirtualServerUtils.decorative_log(
                        'Hypervisor status set to 0 in DB which is expected for configured Hypervisor') 
            except Exception as exp:
                self.log.error(
                    '--Hypervisor status set to 2 in DB which mean Hypervisor in de-configured state---')
                VirtualServerUtils.decorative_log('All validations succeeded')
                raise Exception
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

      