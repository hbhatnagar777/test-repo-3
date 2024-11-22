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
from VirtualServer.VSAUtils import VsaTestCaseUtils, OptionsHelper
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Amazon V2 backup and Restore
    test case with Full backup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AMAZON V2: Full backup and Attach disks as new instance"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONAMAZON,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            self.tc_utils.run_backup(self, msg='Streaming Full Backup')
            self.tc_utils.run_attach_disk_restore(self,
                                                  msg='Attach Disk restore from parent',
                                                  new_instance=True,
                                                  key_pair=self.tcinputs['KeyPair'],
                                                  ami_linux=self.tcinputs.get('AmiId_linux', None),
                                                  ami_win=self.tcinputs.get('AmiId_win', None))
        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                for vm in self.tc_utils.sub_client_obj.hvobj.VMs:
                    if not vm.startswith('del'):
                        self.tc_utils.sub_client_obj.hvobj.VMs[vm].power_off()

            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
