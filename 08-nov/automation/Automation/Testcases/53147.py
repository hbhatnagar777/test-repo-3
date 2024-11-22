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
    """Class for executing Basic acceptance Test of VSA backup and Restore testcase
    for paravirtualzed scsi controller with hotadd"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2: PavaVirtualized SCSI controllers with hotadd backups"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.ind_status = True
        self.failure_msg = ''

    def validate_transport_mode(self, job_obj):
        self.log.info("Checking if the {} ran via hotadd mode".format(job_obj.job_type))
        for vm in job_obj.details['jobDetail']['clientStatusInfo']['vmStatus']:
            if vm['TransportMode'] != 'hotadd':
                self.ind_status = False
                raise Exception('VM: {} was not run with hotadd mode'.format(vm))
            if job_obj.job_type in ('VM Admin Job(Snap Backup)', 'VM Admin Job(Backup)'):
                _job_type = 'Backup'
            else:
                _job_type = job_obj.job_type
            if not self.tc_utils.sub_client_obj.verify_direct_hottadd(vm['Agent'], job_obj.job_id, _job_type):
                self.ind_status = False
                raise Exception('VM: {} was not run with direct hotadd mode'.format(vm))
        self.log.info("Verified: the {} ran via hotadd mode".format(job_obj.job_type))

    def validate_paravirtual_scsi_controller(self, vm):
        self.log.info("Checking for ParaVirtualized SCSI controller in the vm".format(vm.vm_name))
        if not vm.find_scsi_controller('ParaVirtualSCSIController'):
            self.ind_status = False
            raise Exception('VM: {} doesnt have ParaVirtualized scsi controller'.format(vm))
        else:
            self.log.info("Verified: ParaVirtualized SCSI controller in present the vm".format(vm.vm_name))

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)
            if not self.tc_utils.sub_client_obj.auto_vsaclient.isIndexingV2:
                self.ind_status = False
                self.failure_msg = 'This testcase is for indexing v2. The client passed is indexing v1'
                raise Exception(self.failure_msg)

            self.log.info("Checking for ParaVirtualized SCSI controller in the backup vms")
            for vm in self.tc_utils.sub_client_obj.hvobj.VMs:
                self.validate_paravirtual_scsi_controller(self.tc_utils.sub_client_obj.hvobj.VMs[vm])

            self.tc_utils.run_backup(self, msg='Streaming First Full Backup')
            job1_id = self.tc_utils.sub_client_obj.current_job
            job1_path = self.tc_utils.sub_client_obj.testdata_path
            job1_timestamp = self.tc_utils.sub_client_obj.timestamp
            self.validate_transport_mode(self.tc_utils.sub_client_obj.backup_job)

            self.tc_utils.run_backup(self, msg='Streaming Incremental Backup',
                                     backup_type="INCREMENTAL",
                                     cleanup_testdata_before_backup=False)
            self.validate_transport_mode(self.tc_utils.sub_client_obj.backup_job)

            self.tc_utils.run_virtual_machine_restore(self, msg="Restore from the latest job",
                                                      power_on_after_restore=True,
                                                      unconditional_overwrite=True
                                                      )
            self.validate_transport_mode(self.tc_utils.vm_restore_options.restore_job)
            for vm in self.tc_utils.sub_client_obj.hvobj.VMs:
                if vm.startswith('del'):
                    self.validate_paravirtual_scsi_controller(self.tc_utils.sub_client_obj.hvobj.VMs[vm])

            self.tc_utils.run_virtual_machine_restore(self, msg="PIT FULL VM out of Place restore from 1st Backup",
                                                      restore_backup_job=job1_id
                                                      )
            self.validate_transport_mode(self.tc_utils.vm_restore_options.restore_job)
            for vm in self.tc_utils.sub_client_obj.hvobj.VMs:
                if vm.startswith('del'):
                    self.validate_paravirtual_scsi_controller(self.tc_utils.sub_client_obj.hvobj.VMs[vm])

        except Exception as exp:
            self.ind_status = False
            self.failure_msg += '<br>' + str(exp) + '<br>'

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.testdata_path = job1_path
                self.tc_utils.sub_client_obj.timestamp = job1_timestamp
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
