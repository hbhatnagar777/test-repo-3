# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

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
    """Class for executing Basic acceptance Test of VSA backup and Restore with IP customization"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'v2: VSA VMWARE Full Backup and IP customization and Hostname verification on Linux VM'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION,
                                                          tcinputs={
                                                              "source_ip": None,
                                                              "destination_ip": None,
                                                              "dest_computer_name": None
                                                          })

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            if not self.tc_utils.sub_client_obj.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1'
                raise Exception(self.failure_msg)
            self.log.info("--__Validating that backup vm are linux__--")
            self.tc_utils.sub_client_obj.validate_inputs('', '', 'linux', True)
            self.log.info("--__Validating that FREL is set__--")
            if not self.tc_utils.sub_client_obj.auto_vsainstance.fbr_ma:
                self.ind_status = False
                self.failure_msg += '<br> FBR not set at the instance <br>'
                raise Exception("FBR not set at the instance")
            self.tc_utils.run_backup(self, msg='Streaming Full Backup')
            self.tc_utils.run_virtual_machine_restore(self,
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True,
                                                      source_subnet=self.tcinputs.get(
                                                          'source_subnet',
                                                          None),
                                                      destination_subnet=self.tcinputs.get(
                                                          'destination_subnet',
                                                          None),
                                                      source_gateway=self.tcinputs.get(
                                                          'source_gateway',
                                                          None),
                                                      destination_gateway=self.tcinputs.get(
                                                          'destination_gateway',
                                                          None)
                                                      )
            try:
                self.log.info("Validating IP and hostname are properly set")
                for vm in self.tc_utils.sub_client_obj.vm_list:
                    vm = 'del' + vm
                    self.tc_utils.sub_client_obj.validate_ip_hostname(vm, ip=self.tcinputs['destination_ip'],
                                                                      host_name=self.tcinputs['dest_computer_name'])
            except Exception as err:
                self.ind_status = False
                self.failure_msg += '<br>' + str(err) + '<br>'
                raise Exception("Issue in validating IP and hostname of the restored vm")
        except Exception:
            pass

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
