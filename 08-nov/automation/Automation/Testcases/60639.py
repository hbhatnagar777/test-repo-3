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
        self.name = "VSA VMWARE Full Backup and Full VM Job Based Restore for Tags/Category with RestAPI"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            try:
                self.log.info("Tags/Category discovery should be done via rest api")
                self.tc_utils.sub_client_obj.validate_vcenter(6.5)
                self.tc_utils.sub_client_obj.validate_content(["Tag", "TagCategory"])
            except Exception as ex:
                self.ind_status = False
                self.failure_msg = str(ex)
                self.log.exception('Failed in validating Vcenter or content {}'.format(self.failure_msg))

            self.tc_utils.run_backup(self, msg='Streaming First Full Backup')
            job1_id = self.tc_utils.sub_client_obj.current_job
            job1_path = self.tc_utils.sub_client_obj.testdata_path
            job1_timestamp = self.tc_utils.sub_client_obj.timestamp

            self.tc_utils.run_backup(self, msg='Streaming Incremental Backup',
                                     backup_type="INCREMENTAL",
                                     cleanup_testdata_before_backup=False)

            self.tc_utils.run_virtual_machine_restore(self, msg="PIT FULL VM out of Place restore from 1st Backup",
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      restore_backup_job=job1_id
                                                      )
            self.tc_utils.sub_client_obj.validate_tags()

        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.testdata_path = job1_path
                self.tc_utils.sub_client_obj.timestamp = job1_timestamp
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
