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
    """Class for executing Basic acceptance Test of Tags for VMware with RestAPI approach"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2: VSA VMWARE Full Backup and Full VM Restore for Tags with RestAPI"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            if not self.tc_utils.sub_client_obj.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1'
                raise Exception(self.failure_msg)
            try:
                self.log.info("Tags discovery should be done via rest api")
                self.tc_utils.sub_client_obj.validate_vcenter(6.5)
                self.tc_utils.sub_client_obj.validate_content("Tag")
            except Exception as ex:
                self.ind_status = False
                self.failure_msg = str(ex)
                self.log.exception('Failed in validating Vcenter or content {}'.format(self.failure_msg))

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
