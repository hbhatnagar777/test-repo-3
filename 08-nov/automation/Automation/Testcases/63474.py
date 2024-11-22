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
from VirtualServer.VSAUtils import VsaTestCaseUtils, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Amazon V2 backup and Full VM Restore, Attach Disk Restore test case with
    Incremental v2 Snap backup and backup copy for Tennant Account HOTADD"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AMAZON : V2: Incremental Snap and backup copy (Tennant Account) and Attach Disk" \
                    "restore and Full VM restore"
        self.ind_status = True
        self.is_tenant = True
        self.failure_msg = " "
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONAMAZON,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            VirtualServerUtils.decorative_log("Checking if client given in input is tenant")
            if self.subclient.instance_proxy is None:
                self.log.info("No proxies set at client instance, hence it is a tenant client")
            else:
                self.ind_status = False
                self.failure_msg = "Please input a tenant client"
                raise Exception("Please input a tenant client")

            self.tc_utils.run_backup(self, msg='Full v2 Incremental Snap Backup and Backup Copy',
                                     advance_options={"create_backup_copy_immediately": True},
                                     backup_method='SNAP',
                                     backup_type='INCREMENTAL')

            VirtualServerUtils.decorative_log("Checking if backup used Hotadd tranport mode or not")
            _tranport_mode = self.tc_utils.sub_client_obj.auto_commcell.find_job_transport_mode(
                self.tc_utils.sub_client_obj.backupcopy_job_id)
            if _tranport_mode == 'Commvault HotAdd':
                self.log.info("Backup used Hotadd transport mode")
            else:
                self.ind_status = False
                self.failure_msg = "Backup was not run via hotadd mode"
                raise Exception("Backup was not run via {} mode. it should be via hotadd mode".format(_tranport_mode))

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            browse_from_backup_copy=False,
                                            browse_from_snap=True,
                                            child_level=True,
                                            unconditional_overwrite=True,
                                            msg='FULL VM out of Place restores from Child from snap')

            self.tc_utils.run_attach_disk_restore(self,
                                                  browse_from_snap=True,
                                                  child_level=True,
                                                  msg='Attach Disk restore from child from snap copy')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            browse_from_snap=False,
                                            browse_from_backup_copy=True,
                                            child_level=True,
                                            unconditional_overwrite=True,
                                            msg='FULL VM out of Place restores from Child from Backup Copy')

            self.tc_utils.run_attach_disk_restore(self,
                                                  browse_from_snap=False,
                                                  child_level=True,
                                                  browse_from_backup_copy=True,
                                                  msg='Attach Disk restore from child from Backup Copy')

        except Exception:
            pass

        finally:
            VirtualServerUtils.decorative_log("Test Data Clean Up Started")
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   True, self.tcinputs.get('DeleteRestoredVM', True))
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
