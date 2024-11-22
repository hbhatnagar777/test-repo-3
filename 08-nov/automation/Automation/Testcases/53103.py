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

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import logger, constants
from cvpysdk.job import Job
from cvpysdk.policies.storage_policies import StoragePolicies


class TestCase(CVTestCase):
    """Class for executing live mount"""

    def __init__(self):
        """Initializes test case class object"""
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMware Live Mount Case - Point In Time"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.LIVEMOUNT

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase.".format(self.id))
            log.info("-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            VirtualServerUtils.decorative_log("Primary Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            auto_subclient.backup(backup_options)

            backup_job = Job(self.commcell, auto_subclient.backup_job.job_id)
            point_in_time_value = {
                'timeValue': backup_job.end_time, #time_value,
                'TimeZoneName': '(UTC) Coordinated Universal Time'}

            VirtualServerUtils.decorative_log("Initialize helper objects for Live Mount Validation")
            from cvpysdk.virtualmachinepolicies import VirtualMachinePolicies
            vmpolicy_name = self.tcinputs['VMPolicyName'].lower()
            vmpolicies = VirtualMachinePolicies(auto_commcell.commcell)
            vmpolicy = vmpolicies.get(vm_policy_name=vmpolicy_name)
            virtualization_client_name = (
                vmpolicy.properties()['dataCenter']['instanceEntity']['clientName'])
            virtualization_client = auto_commcell.commcell.clients.get(
                virtualization_client_name)
            virtualization_agent = virtualization_client.agents.get('Virtual Server')
            instance_keys = next(iter(virtualization_agent.instances._instances))
            source_instance = virtualization_agent.instances.get(instance_keys)
            auto_virtualization_client = VirtualServerHelper.AutoVSAVSClient(
                auto_commcell, virtualization_client)
            auto_virtualization_instance = VirtualServerHelper.AutoVSAVSInstance(
                auto_client=auto_virtualization_client,
                agent=virtualization_agent,
                instance=source_instance)

            # creating HypervisorHelper object
            log.info("Creating HypervisorHelper object for source and mount.")
            source_hvobj = auto_instance.hvobj
            hvobj = auto_virtualization_instance.hvobj

            # start live mount job for each vm in subclient
            for each_vm in auto_subclient.vm_list:
                log.info("-" * 25 + " Initiating Live Mount Job for " + each_vm + "-" * 25)

                live_mount_options = {
                    'pointInTime': point_in_time_value
                }
                # live_mount_options needs to be a dict for multiple vm's in subclient
                live_mount_job = vmpolicy.live_mount(client_vm_name=each_vm,
                                                     live_mount_options=live_mount_options)

                log.info(
                    "Live mount Job for client: {0} for vm policy: {1} with Job ID: {2} started."
                        .format(each_vm, vmpolicy_name, live_mount_job.job_id))

                # waiting for job to finish
                log.info("Waiting for Live Mount Job to finish.")
                # if job does not complete successfully, raise exception
                if not live_mount_job.wait_for_completion():
                    log.error("Live Mount Job with Job ID: {0} failed for VM {1} "
                              "with Job Status: {1}.".format(live_mount_job.job_id,
                                                             each_vm,
                                                             live_mount_job.status))
                    raise Exception

                # if job is successful, perform live mount validation after job is finished
                log.info(
                    "Success - Live mount for client: {0} for vm policy: {1} "
                    "with Job ID: {2}.".format(each_vm,  # self.client.client_name,
                                               vmpolicy_name,
                                               live_mount_job.job_id))

                # Livemount validation for each_vm after job is successful
                log.info("-" * 25 + " Starting Live Mount validation now " + "-" * 25)
                auto_client.live_mount_validation(vmpolicy=vmpolicy,
                                                  hvobj=hvobj,
                                                  live_mount_job=live_mount_job,
                                                  source_vm_name=each_vm,
                                                  mounted_network_name=None,
                                                  source_hvobj=source_hvobj)

        except Exception as exp:
            log.warning('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)