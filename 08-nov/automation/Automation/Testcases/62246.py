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
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants
from cvpysdk.client import Client


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware Full Snap backup and Restore test case with
    crash consistent option"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA VMWARE Full Snap Backup, Backup Copy and Restore Cases with Crash Consistent'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:

            _ = self.tc_utils.initialize(self)

            self.tc_utils.sub_client_obj.get_proxies()
            _proxies = list(self.tc_utils.sub_client_obj.proxy_obj.keys())
            self.tc_utils.log.info("Checking if the Proxy is not Commserve")
            if self.tc_utils.sub_client_obj.auto_commcell.commserv_name in _proxies:
                raise Exception("We can't use CS as proxy here")
            self.tc_utils.log.info("Verfied. Commserve is not a proxy for this testcase")
            self.tc_utils.log.info(
                "Setting the key nEnableSnapCrashConsistent on All proxies and restarting the services on them")
            for _proxy in _proxies:
                self.tc_utils.sub_client_obj.add_registry_key('nEnableSnapCrashConsistent', _proxy)
                _proxy_client = Client(
                    commcell_object=self.tc_utils.sub_client_obj.auto_commcell.commcell, client_name=_proxy)
                _proxy_client.restart_services()
                self.tc_utils.log.info(
                    "Successful: key nEnableSnapCrashConsistent set and services restarted")
            self.tc_utils.run_backup(self,
                                     advance_options={
                                         'create_backup_copy_immediately': True,
                                         'backup_copy_type': 'USING_LATEST_CYLE'},
                                     backup_method='SNAP')
            _logs_lines_found = 0
            for _proxy in _proxies:
                if self.tc_utils.sub_client_obj.verify_crash_consistent_backup(
                        self.tc_utils.sub_client_obj.backup_job.job_id, _proxy):
                    _logs_lines_found += 1
                if self.tc_utils.sub_client_obj.verify_crash_consistent_backup(
                        self.tc_utils.sub_client_obj.backupcopy_job_id, _proxy, False):
                    _logs_lines_found += 1
            if _logs_lines_found != 2:
                self.ind_status = False
                self.log.error("Backup jobs didn't go via crash consistent way."
                               "Snap backup job: {}"
                               "Backup copy job: {}".format(self.tc_utils.sub_client_obj.backup_job.job_id,
                                                            self.tc_utils.sub_client_obj.backupcopy_job_id))
                raise Exception('Backups were not crash consistent')
            self.tc_utils.log.info("****Backups went crash consistent way****")
            self.tc_utils.run_guest_file_restore(self,
                                                 child_level=True,
                                                 browse_from_snap=True)

            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      browse_from_snap=True
                                                      )
            self.tc_utils.run_virtual_machine_restore(self,
                                                      in_place_overwrite=False,
                                                      unconditional_overwrite=True,
                                                      browse_from_snap=False,
                                                      browse_from_backup_copy=True
                                                      )

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.log.info(
                    "Deleting the key nEnableSnapCrashConsistent on All proxies and restarting the services on them")
                for _proxy in _proxies:
                    self.tc_utils.sub_client_obj.delete_registry_key('nEnableSnapCrashConsistent', _proxy)
                    _proxy_client = Client(
                        commcell_object=self.tc_utils.sub_client_obj.auto_commcell.commcell, client_name=_proxy)
                    _proxy_client.restart_services()
                    self.tc_utils.log.info(
                        "Deleted the key nEnableSnapCrashConsistent on All proxies and restarted the services on them")
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
