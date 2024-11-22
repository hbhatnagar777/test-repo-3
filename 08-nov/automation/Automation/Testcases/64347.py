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
from VirtualServer.VSAUtils import VirtualServerUtils, VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware extent restart validation and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware extent restart validation when job gets suspend and resume"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''
        self.tcinputs = {}
    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            _ = self.tc_utils.initialize(self)
            if self.tc_utils.sub_client_obj.subclient.subclient_proxy is not None:
                proxy_list = self.subclient.subclient_proxy
            else:
                proxy_list = self.tc_utils.sub_client_obj.auto_vsainstance.proxy_list
            index_server_name = self.tc_utils.sub_client_obj.get_index_name()
            # check services are up on all proxies and media agent machines
            for each_proxy in proxy_list:
                machine_names = [each_proxy, index_server_name]
                for each_server in machine_names:
                    self.tc_utils.sub_client_obj.start_service(
                        each_server, None, None, self.commcell)
            # checking if any jobs to be backup copied
            self.tc_utils.sub_client_obj.auto_commcell.run_backup_copy(
                self.tc_utils.sub_client_obj.storage_policy)
            # Running snap job
            VirtualServerUtils.decorative_log("Starting Snap Job")
            self.tc_utils.run_backup(self,
                                      advance_options={
                                          'create_backup_copy_immediately': False,
                                          'backup_copy_type': 'USING_LATEST_CYLE'},
                                      backup_method='SNAP')
            # Running backup copy job to validate restart extents
            self.tc_utils.sub_client_obj.validate_restart_extents(operation='suspend')
            # Full VM restore
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=False,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      browse_from_backup_copy=True
                                                      )
        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.failure_msg = str(exp)
            self.ind_status = False
        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
