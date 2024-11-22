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

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils, VsaTestCaseUtils
from AutomationUtils import logger


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware backup performance test """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware backup performance test"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self,
                                     backup_type='INCREMENTAL',
                                     msg='Streaming Incremental Backup')
            self.tc_utils.sub_client_obj.validate_backup_pref_time(
                self.tc_utils.sub_client_obj.backup_job.job_id, self.subclient.subclient_proxy[0])
        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
