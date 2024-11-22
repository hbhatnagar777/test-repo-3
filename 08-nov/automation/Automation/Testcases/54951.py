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
from VirtualServer.SNAPUtils.vsa_snap_templates import VSASNAPTemplates
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware Full Snap backup and Restore test case
    Windows proxy, Windows MA, Windows backup vm without metadata collection"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA V1 VMWARE Full Snap Backup and Restore Cases for DataCore"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""

        try:
            vsa_snap_templates = VSASNAPTemplates(self.commcell, self.tcinput)
            return_values = vsa_snap_templates.vsasnap_template_v1(self)
            auto_subclient, backup_options, vm_restore_options, self.test_individual_status, self.test_individual_failure_message = return_values

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                if not self.test_individual_status:
                    self.result_string = self.test_individual_failure_message
                    self.status = constants.FAILED
                else:
                    auto_subclient.cleanup_testdata(backup_options)

                auto_subclient.post_restore_clean_up(vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
                pass
