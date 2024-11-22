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

import time
import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesHelper
from Kubernetes.KubernetesHelper import KubernetesHelper
from AutomationUtils import constants, machine

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA intellisnap backup and Restore test case
        This test case does the following
        1) Create Virtual Kubernetes client
        2) create Application/ Subclient.
        3) Enable Intellisnap on subclient
        4) Connect to VSA Host setup testbed
         (Create namespace , pvc (independent of storage controller type) and pod for backup and restore
              &cleanup if already exists) and deploying test pods
        5) List all pods created
        6) upload data to pod
        7) RUn SnapBackup(FULL) --> check backup is launched and successfully backed up all items
        8) Run Browse and validate the pods backedup or not.
        9) Run Restore  from snap copy and wait until job complates( Fails on failures / CWE)
        10) Connect to host and validate pods and status
        11) Validate data on pod
        12) Verify the pods before backup(Step5) to (Step 10) and compare data by checksum and metadata Report on failures.
        13) RUn Backupcopy (FULL) --> check backup is launched and successfully backed up all items
        14) Run Browse and validate the pods backedup or not.
        15) Run Restore  from Backup copy (copy precedence 2) and wait until job completes( Fails on failures / CWE)
        16) Connect to host and validate pods and status
        17) Validate data on pod
        18) Verify the pods before backup(Step5) to (Step 16) and compare data by checksum and metadata Report on failures.
        19) add more data and move some data and deltes files on pod
        20) upload it to pod
        21) List all pods created (INCLUDES ALL pods in namespace)
        22) RUn SnapBackup(INCR) --> check backup is launched and successfully backed up all items
        23) Run Browse and validate the pods backedup or not.
        24) Run Restore  from snap copy and wait until job complates( Fails on failures / CWE)
        25) Connect to host and validate pods and status
        26) Validate data on pod
        27) Verify the pods before backup(Step21) to (Step 25) and compare data by checksum and metadata Report on failures.
        28) RUn Backupcopy (INCR) --> check backup is launched and successfully backed up all items
        29) Run Browse and validate the pods backedup or not.
        30) Run Restore  from Backup copy (copy precedence 2) and wait until job completes( Fails on failures / CWE)
        31) Connect to host and validate pods and status
        32) Validate data on pod
        32) Verify the pods before backup(Step21) to (Step 31) status along with checksum and metadata comparision Fail on Failures

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA KUBERNETES SNAP VALIDATION"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.utils_path = VirtualServerUtils.UTILS_PATH
        self.pod_create = "poddeployment.yml"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.namespace = ''
        self.restore_namespace = ''
        self.master_machine = None
        self.planid = ''
        self.controller = None
        self.result_string = ''
        self.status = ''
        self.tcinputs = {}
        self.kubehelper = KubernetesHelper(TestCase)

    def run(self):
        """Main function for test case execution"""
        try:
            self.tcinputs.update({"SubclientName": "automation-59618"})
            self.tcinputs.update({"DestinationClient": "k8sauto-59618"})
            self.tcinputs.update({"Namespace": "automation-59618"})
            self.tcinputs.update({"RestoreNamespace": "restoretest-59618"})
            self.namespace = 'automation-59618'
            self.restore_namespace = 'restoretest-59618'
            if 'VSAClient' in self.tcinputs:
                self.controller = self.commcell.clients.get(self.tcinputs['VSAClient'])
            self.log.info(" Checking client with name {0} already exists"
                          .format(self.tcinputs['ClientName']))
            if self.commcell.clients.has_client(self.tcinputs.get('ClientName')):
                self.log.info("Create client object for: %s", self.tcinputs['ClientName'])
                self._client = self.commcell.clients.get(self.tcinputs['ClientName'])

            pod_deployment_path = os.path.join(self.utils_path, self.pod_create)
            self.master_machine = machine.Machine(self.tcinputs.get('MasterNode'),
                                                  username=self.tcinputs.get('Username'),
                                                  password=self.tcinputs.get('Password'))
            VirtualServerUtils.decorative_log("Creating Class Objects")

            path = "/tmp/automation_{0}".format(self.id)
            VirtualServerUtils.decorative_log("Done Creating ")
            self.kubehelper.populate_tc_inputs(self)

            VirtualServerUtils.decorative_log("setting Kuberenetes Test Environment")
            self.kubehelper.create_name_space()
            self.kubehelper.create_pvc_yaml(pod_deployment_path, self.tcinputs['StorageType'])
            self.kubehelper.populate_data(pod_deployment_path)
            self.kubehelper.create_pod_yaml(pod_deployment_path)
            self.kubehelper.populate_data(pod_deployment_path)
            pods = self.kubehelper.get_pods(self.namespace)
            test_pod = pods[0]
            time.sleep(60)
            self.kubehelper.upload_pod_data(test_pod, path, self.id)
            list_before_backup = self.kubehelper.get_pods_services(self.namespace)
            self.log.info("Listing pods services and replication controllers before backup "
                          "in namespace %s", str(list_before_backup))
            if len(list_before_backup) == 0:
                Exception("Failed to get namespace entities or failed to create")
            if self.backupset.subclients.has_subclient(str(self.tcinputs.get('SubclientName'))):
                self.backupset.subclients.delete(str(self.tcinputs.get('SubclientName')))
            self.backupset.application_groups.create_application_group(content=self.namespace,
                                                                       plan_name=
                                                                       str(self.tcinputs.get('PlanName')),
                                                                       subclient_name=
                                                                       str(self.tcinputs.get('SubclientName')))
            self.log.info("Application Group Created  %s", str(self.tcinputs.get('SubclientName')))
            self.backupset = self._instance.backupsets.get(
                self.tcinputs['BackupsetName'])
            self.log.info("Creating subclient object for: %s",
                          self.tcinputs['SubclientName'])
            self.subclient = self._backupset.subclients.get(
                self.tcinputs['SubclientName'])
            self.vendor = 'Kubernetes CSI Snap'
            self.kubehelper.source_vm_object_creation(self)
            if not self.subclient.is_intelli_snap_enabled:
                self.log.info(
                    "Intelli snap is not enabled at subclient level, enabling it.")
                self.subclient.enable_intelli_snap(self.vendor)
            self._log.info("Intelli Snap for subclient is enabled.")
            VirtualServerUtils.decorative_log("Snap Full Backup")
            self.kubehelper.source_vm_object_creation(self)
            self.kubehelper.backup('FULL')
            self.log.info("Running Restore From snap copy")
            self.kubehelper.restore_out_of_place(
                self.client.client_name,
                self.tcinputs['StorageType'],
                self.restore_namespace)
            list_pods_services_rst = self.kubehelper.get_pods_services(self.restore_namespace)

            self.log.info("list of pods post restore {0} on namespace {1} "
                          .format(list_pods_services_rst, self.restore_namespace))
            self.log.info("Running Validation")

            src_pod_path = self.kubehelper.download_pod_data(test_pod, self.namespace, self.id)
            rst_pod_path = self.kubehelper.download_pod_data(test_pod, self.restore_namespace, self.id)

            result, diff_output = self.master_machine.compare_meta_data(
                src_pod_path,
                rst_pod_path
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Meta data comparison failed")

            result, diff_output = self.master_machine.compare_checksum(
                src_pod_path, rst_pod_path
            )
            if result:
                self.log.info("Checksum comparison successful")
            else:
                self.log.error("Checksum comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Checksum comparison failed")
            VirtualServerUtils.decorative_log("Running Backup copy for Full Job")
            try:
                VirtualServerUtils.decorative_log("checking If any jobs to backup copied before triggering snap job")
                storage_policy_object = self.commcell.storage_policies.get(str(self.tcinputs.get('PlanName')))
                checkbackupcopyjob = storage_policy_object.run_backup_copy()
                VirtualServerUtils.decorative_log("--backup copy job triggered successfully--")
            except Exception as err:
                self.log.exception("--Triggering backupcopy job failed--" + str(checkbackupcopyjob))
                raise Exception
            if not checkbackupcopyjob.wait_for_completion():
                raise Exception("Failed to run job with error: "+str(checkbackupcopyjob.delay_reason))
            VirtualServerUtils.decorative_log("Back up copy job completed successfully")

            self.log.info("Running Restore From Backup copy")
            self.kubehelper.restore_out_of_place(
                self.client.client_name,
                self.tcinputs['StorageType'],
                self.restore_namespace,
                copy_precedence=1
            )
            list_pods_services_rst = self.kubehelper.get_pods_services(self.restore_namespace)

            self.log.info("list of pods post restore {0} on namespace {1} "
                          .format(list_pods_services_rst, self.restore_namespace))
            self.log.info("Running Validation")

            # bkp_pod_path = "/tmp/automation_restore_{0}_{1}".format(self.id, self.namespace)
            src_pod_path = self.kubehelper.download_pod_data(test_pod, self.namespace, self.id)
            rst_pod_path = self.kubehelper.download_pod_data(test_pod, self.restore_namespace, self.id)

            result, diff_output = self.master_machine.compare_meta_data(
                src_pod_path,
                rst_pod_path
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Meta data comparison failed")

            result, diff_output = self.master_machine.compare_checksum(
                src_pod_path, rst_pod_path
            )
            if result:
                self.log.info("Checksum comparison successful")
            else:
                self.log.error("Checksum comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Checksum comparison failed")



            VirtualServerUtils.decorative_log(" FULL BACKUP AND RESTORE VALIDATION DONE")

            VirtualServerUtils.decorative_log(" INCREMENTAL Backup and MOVE FOLDER CASES ")
            self.kubehelper.upload_pod_data(test_pod, path, self.id, job_type='INCR')
            list_before_backup = self.kubehelper.get_pods_services(self.namespace)

            self.log.info("Listing pods services and replication controllers before backup "
                          "in namespace %s", str(list_before_backup))
            if len(list_before_backup) == 0:
                Exception("Failed to get namespace entities or failed to create")
            src_path = path + '/FULL'
            dest_path = path + '/MOVED'
            self.kubehelper.move_pod_content(test_pod, src_path, dest_path)
            self.kubehelper.delete_and_recreate_namespace()
            self.log.info("Running Snap Incremental Backup")
            self.kubehelper.backup('INCREMENTAL')
            self.kubehelper.delete_and_recreate_namespace()
            self.log.info("Running Restore")
            self.kubehelper.restore_out_of_place(
                                                  self.client.client_name,
                                                  self.tcinputs['StorageType'],
                                                  self.restore_namespace)
            list_pods_services_rst = self.kubehelper.get_pods_services(self.restore_namespace)
            self.log.info("list of pods post restore {0} on namespace {1} "
                          .format(list_pods_services_rst, self.restore_namespace))
            self.log.info("Running Validation")
            # bkp_pod_path = "/tmp/automation_restore_{0}_{1}".format(self.id, self.namespace)
            src_pod_path = self.kubehelper.download_pod_data(test_pod, self.namespace, self.id)
            rst_pod_path = self.kubehelper.download_pod_data(test_pod, self.restore_namespace, self.id)

            moved_src_rst_path = rst_pod_path + '/FULL'
            moved_rst_path = rst_pod_path + '/MOVED/FULL'
            if self.master_machine.check_directory_exists(moved_src_rst_path):
                self.log.info("Directory not marked as deleted {0} cleaning it ".format(str(moved_src_rst_path)))
                raise Exception
            else:
                self.log.info("Directory  marked as deleted {0} cleaning it ".format(str(moved_src_rst_path)))

            if self.master_machine.check_directory_exists(moved_rst_path):
                if len(self.master_machine.get_items_list(moved_rst_path)) > 1:
                    self.log.info("Directory {0} is not empty".format(str(moved_rst_path)))
                    self.log.info("Directory {0} moved and backed up ".format(str(moved_rst_path)))
                else:
                    self.log.info("Directory {0} is empty failing testcase".format(str(moved_rst_path)))
                    raise Exception
            else:
                self.log.info("Directory {0} not moved or not backed up ".format(str(moved_rst_path)))
                raise Exception

            result, diff_output = self.master_machine.compare_meta_data(
                src_pod_path,
                rst_pod_path
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Meta data comparison failed")

            result, diff_output = self.master_machine.compare_checksum(
                src_pod_path, rst_pod_path
            )
            if result:
                self.log.info("Checksum comparison successful")
            else:
                self.log.error("Checksum comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Checksum comparison failed")

            VirtualServerUtils.decorative_log("Running Backup copy for INCREMENTAL Job")
            try:
                VirtualServerUtils.decorative_log("checking If any jobs to backup copied before triggering snap job")
                storage_policy_object = self.commcell.storage_policies.get(str(self.tcinputs.get('PlanName')))
                checkbackupcopyjob = storage_policy_object.run_backup_copy()
                VirtualServerUtils.decorative_log("--backup copy job triggered successfully--")
            except Exception as err:
                self.log.exception("--Triggering backupcopy job failed--" + str(checkbackupcopyjob))
                raise Exception
            if not checkbackupcopyjob.wait_for_completion():
                raise Exception("Failed to run job with error: "+str(checkbackupcopyjob.delay_reason))
            VirtualServerUtils.decorative_log("Back up copy job completed successfully")
            self.log.info("Running Restore From Incremental Backup copy")
            self.kubehelper.restore_out_of_place(
                self.client.client_name,
                self.tcinputs['StorageType'],
                self.restore_namespace,
                copy_precedence=1
            )
            list_pods_services_rst = self.kubehelper.get_pods_services(self.restore_namespace)

            self.log.info("list of pods post restore {0} on namespace {1} "
                          .format(list_pods_services_rst, self.restore_namespace))
            self.log.info("Running Validation")

            # bkp_pod_path = "/tmp/automation_restore_{0}_{1}".format(self.id, self.namespace)
            src_pod_path = self.kubehelper.download_pod_data(test_pod, self.namespace, self.id)
            rst_pod_path = self.kubehelper.download_pod_data(test_pod, self.restore_namespace, self.id)

            result, diff_output = self.master_machine.compare_meta_data(
                src_pod_path,
                rst_pod_path
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Meta data comparison failed")

            result, diff_output = self.master_machine.compare_checksum(
                src_pod_path, rst_pod_path
            )
            if result:
                self.log.info("Checksum comparison successful")
            else:
                self.log.error("Checksum comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Checksum comparison failed")

            VirtualServerUtils.decorative_log(" INCREMENTAL 2 Backup")
            self.kubehelper.upload_pod_data(test_pod, path, self.id, job_type='INCR')
            list_before_backup = self.kubehelper.get_pods_services(self.namespace)

            self.log.info("Listing pods services and replication controllers before backup "
                          "in namespace %s", str(list_before_backup))
            if len(list_before_backup) == 0:
                Exception("Failed to get namespace entities or failed to create")
            self.kubehelper.backup('INCREMENTAL')
            self.kubehelper.delete_and_recreate_namespace()
            self.log.info("Running Restore")
            self.kubehelper.restore_out_of_place(
                self.client.client_name,
                self.tcinputs['StorageType'],
                self.restore_namespace)
            list_pods_services_rst = self.kubehelper.get_pods_services(self.restore_namespace)
            self.log.info("list of pods post restore {0} on namespace {1} "
                          .format(list_pods_services_rst, self.restore_namespace))
            self.log.info("Running Validation")
            src_pod_path = self.kubehelper.download_pod_data(test_pod, self.namespace, self.id)
            rst_pod_path = self.kubehelper.download_pod_data(test_pod, self.restore_namespace, self.id)

            result, diff_output = self.master_machine.compare_meta_data(
                src_pod_path,
                rst_pod_path
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Meta data comparison failed")
            result, diff_output = self.master_machine.compare_checksum(
                src_pod_path, rst_pod_path
            )
            if result:
                self.log.info("Checksum comparison successful")
            else:
                self.log.error("Checksum comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Checksum comparison failed")
            VirtualServerUtils.decorative_log("Running Backup copy for INCREMENTAL 2 Job")
            try:
                VirtualServerUtils.decorative_log("checking If any jobs to backup copied before triggering snap job")
                storage_policy_object = self.commcell.storage_policies.get(str(self.tcinputs.get('PlanName')))
                checkbackupcopyjob = storage_policy_object.run_backup_copy()
                VirtualServerUtils.decorative_log("--backup copy job triggered successfully--")
            except Exception as err:
                self.log.exception("--Triggering backupcopy job failed--" + str(checkbackupcopyjob))
                raise Exception
            if not checkbackupcopyjob.wait_for_completion():
                raise Exception("Failed to run job with error: "+str(checkbackupcopyjob.delay_reason))
            VirtualServerUtils.decorative_log("Back up copy job completed successfully")
            self.log.info("Running Restore From Incremental Backup copy")
            self.kubehelper.restore_out_of_place(
                self.client.client_name,
                self.tcinputs['StorageType'],
                self.restore_namespace,
                copy_precedence=1
            )
            list_pods_services_rst = self.kubehelper.get_pods_services(self.restore_namespace)
            self.log.info("list of pods post restore {0} on namespace {1} "
                          .format(list_pods_services_rst, self.restore_namespace))
            self.log.info("Running Validation")
            src_pod_path = self.kubehelper.download_pod_data(test_pod, self.namespace, self.id)
            rst_pod_path = self.kubehelper.download_pod_data(test_pod, self.restore_namespace, self.id)
            result, diff_output = self.master_machine.compare_meta_data(
                src_pod_path,
                rst_pod_path
            )
            if result:
                self.log.info("Meta data comparison successful")
            else:
                self.log.error("Meta data comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Meta data comparison failed")

            result, diff_output = self.master_machine.compare_checksum(
                src_pod_path, rst_pod_path
            )
            if result:
                self.log.info("Checksum comparison successful")
            else:
                self.log.error("Checksum comparison failed")
                self.log.info("Diff output: \n%s", diff_output)
                raise Exception("Checksum comparison failed")
            VirtualServerUtils.decorative_log(" INCR BACKUP AND RESTORE VALIDATION DONE")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.log.info("Cleaning up testcase entitites")
                if self.master_machine.check_directory_exists(src_pod_path):
                    self.log.info("Directory Exists {0} cleaning it ".format(str(src_pod_path)))
                    self.master_machine.remove_directory(src_pod_path)
                if self.master_machine.check_directory_exists(rst_pod_path):
                    self.log.info("Directory Exists {0} cleaning it ".format(str(rst_pod_path)))
                    self.master_machine.remove_directory(rst_pod_path)
                self.log.info("TEST CASE COMPLETED SUCESSFULLY")

            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
