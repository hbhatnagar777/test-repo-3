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


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Tags for VMware with PowerCLI approach"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Full Backup and Full VM Restore for Tags with PowerCLI"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            self.tc_utils.sub_client_obj.validate_inputs("windows")
            self.log.info("Tags discovery should be done via Powercli."
                          " Proxy should have Powercli installed")
            self.tc_utils.sub_client_obj.validate_vcenter(6.0)
            self.tc_utils.sub_client_obj.validate_content("Tag")

            self.tc_utils.run_backup(self, msg='Streaming Full Backup')
            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True
                                                      )
            self.tc_utils.sub_client_obj.validate_tags()

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED