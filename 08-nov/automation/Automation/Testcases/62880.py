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
import os
from AutomationUtils.cvtestcase import CVTestCase, logger, constants
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerConstants



class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Nutanix AHV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Nutanix AHV disk filter snap test case"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONNUTANIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.test_individual_status = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:
            log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            #Getting container details from VM
            vmobj =  auto_subclient.hvobj.VMs[auto_subclient.vm_list[0]]
            guestvminfo = vmobj.get_vm_info(auto_subclient.vm_list[0])
            diskfilter = ([guestvminfo['config']['vmDisks'][1]['id']])
            #Setting container filter
            self.subclient.vm_diskfilter = [{
                  'filter': diskfilter[0],
                  'vmGuid': '',
                  'type':'Virtual Device Node'
             }]
            VirtualServerUtils.decorative_log("triggering Backup")
            try:
                subclient_obj = CommonUtils(self.commcell).get_subclient(
                    self.tcinputs.get('ClientName'), self.tcinputs.get('AgentName'),
                    self.tcinputs.get('BackupsetName'), self.tcinputs.get('SubclientName'))
                job_obj = subclient_obj.backup("FULL")
                if job_obj.wait_for_completion():
                    self._log.error("Backup job {0} completed".format(job_obj.job_id))
                    raise Exception
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            #Validating failure reason
            res = job_obj.get_events()
            if VirtualServerConstants.JM_Failure_Reason['DiskFilter'] not in res[2]['description']:
                self.log.error(
                        '---Job didnt fail with expected reason --'+str(job_obj.job_id))
                raise Exception
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED