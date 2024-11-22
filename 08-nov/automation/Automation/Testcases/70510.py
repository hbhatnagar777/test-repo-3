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
from VirtualServer.VSAUtils import VirtualServerUtils, VsaTestCaseUtils, OptionsHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware extent restart validation and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware extent restart validation when proxy services are down for streaming job"
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
            index_server_name = self.tc_utils.sub_client_obj.get_index_name()
            # Running backup job
            try:
                VirtualServerUtils.decorative_log("FULL  Backup")
                self.tc_utils.backup_options = OptionsHelper.BackupOptions(
                    self.tc_utils.sub_client_obj)
                self.tc_utils.backup_options.backup_type = "FULL"
                self.tc_utils.sub_client_obj.vsa_discovery(self.tc_utils.backup_options, dict())
                VirtualServerUtils.decorative_log("Starting Backup Job")
                _backup_job = self.subclient.backup(self.tc_utils.backup_options.backup_type,
                                                    self.tc_utils.backup_options.run_incr_before_synth,
                                                    self.tc_utils.backup_options.incr_level,
                                                    self.tc_utils.backup_options.collect_metadata,
                                                    self.tc_utils.backup_options.advance_options)
                VirtualServerUtils.decorative_log("Back Up Job ID = {}".format(_backup_job.job_id))
            except Exception as err:
                self.log.error("Backup job Failed to start")
                raise Exception
            # validate restart extents
            self.tc_utils.sub_client_obj.validate_restart_extents(self.tcinputs.get('username'),
                                                                  self.tcinputs.get('password'),
                                                                  operation='stop',
                                                                  clientname=proxy_list[0],
                                                                  streaming_job=_backup_job.job_id)
            if not _backup_job.wait_for_completion():
                raise Exception("Failed to run the job with error: "
                                +str(_backup_job.delay_reason))
            # Full VM restore
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=False,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      browse_from_backup_copy=True
                                                      )
            self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
        except Exception as exp:
            self.log.error('Failed with error [{}]'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED