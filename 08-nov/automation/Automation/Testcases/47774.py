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
    """Class for executing VSA VMWARE Parallel File level Browse of the same VM with diff jobs"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "V2: VSA VMWARE Parallel File level Browse of the same VM from different job"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = self.tc_utils.initialize(self)
            if not auto_subclient.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1 '
                raise Exception(self.failure_msg)
            # currently the testcase works best with one vm as a content.
            # support for having multiple vms will be added
            if len(auto_subclient.vm_list) != 1:
                self.ind_status = False
                self.failure_msg = 'multiple vm present.support for having multiple vms will be added later'
                raise Exception(self.failure_msg)
            for vm in auto_subclient.vm_list:
                if auto_subclient.hvobj.VMs[vm].guest_os.lower() != 'windows':
                    self.log.info('{} is not windows vm, skipping dynamic disk check'.format(vm))
                    continue
                if not auto_subclient.windows_dynamic_disks_check(vm):
                    self.ind_status = False
                    self.failure_msg = 'There are no dynamic disks in vm: {}'.format(vm)
                    raise Exception(self.failure_msg)
            self.log.info("All vms have dynamic disks")
            _backup_jobs = self.tc_utils.run_multiple_backups(self, ['FULL', 'INCREMENTAL',
                                                                     'INCREMENTAL'])
            self.tc_utils.run_multiple_guest_files_restores(self, _backup_jobs,
                                                            run_type='parallel')
        except Exception:
            pass

        finally:
            try:
                for backup_options in _backup_jobs['backup_option']:
                    auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testdata cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED

