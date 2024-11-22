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
    """Class for executing Basic acceptance Test of Amazon V2 backup and Restore test case with
    v2 Synthfull backup for Tennant Account HOTADD"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AMAZON : V2: Synthfull backup (Tennant Account) and File level restore and Full VM restore"
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

            self.tc_utils.run_backup(self, msg='v2 Synthfull backup',
                                     advance_options={"create_backup_copy_immediately": True},
                                     backup_method='SNAP',
                                     backup_type='SYNTHETIC_FULL')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            unconditional_overwrite=True,
                                            msg='FULL VM out of place restore from parent')

            self.tc_utils.run_attach_disk_restore(self,
                                                  msg='Attach Disk restore from parent')

            self.tc_utils.run_guest_file_restore(self,
                                                 child_level=True,
                                                 msg='Guest Files restores from Child')

            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            child_level=True,
                                            msg='FULL VM out of Place restores from Child')

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   True, self.tcinputs.get('DeleteRestoredVM', True))
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
