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
from cvpysdk.policy import Policies
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing live mount"""

    def __init__(self):
        """Initializes test case class object"""
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMware Live Mount from Aux Copy using V2"
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

            subclient_storage_policy = Policies(self.commcell).storage_policies.get(
                self.subclient.storage_policy)

            aux_copy_name = None
            for copy_name in subclient_storage_policy.copies:
                if copy_name.lower() == subclient_storage_policy.aux_copies[0]:
                    aux_copy_name = copy_name
                    break

            from cvpysdk.virtualmachinepolicies import VirtualMachinePolicies
            vmpolicy_name = self.tcinputs['VMPolicyName'].lower()
            vmpolicies = VirtualMachinePolicies(auto_commcell.commcell)
            vmpolicy = vmpolicies.get(vm_policy_name=vmpolicy_name)

            VirtualServerUtils.decorative_log("Aux Copy Backup")
            _auxcopy_job = subclient_storage_policy.run_aux_copy(aux_copy_name)

            if not _auxcopy_job.wait_for_completion():
                raise Exception(
                    "Failed to run backup with error: " +
                    str(_auxcopy_job.delay_reason)
                )
            _auxcopy_job_id = _auxcopy_job.job_id
            log.info("Aux Copy Job {0} completed successfully".format(_auxcopy_job_id))
            log.info("Aux Copy Job got complete")

            VirtualServerUtils.decorative_log("Starting Live Mount Automation")

            # checking if required reg key exists on MA and adding/updating it in case it doesn't
            log.info("-" * 15 + " Checking Media Agent for reg key "
                                "'VmExpiryCheckThreadWaitTimeMinutes'" + "-" * 15)
            media_agent_name = vmpolicy.properties()['mediaAgent']['clientName']
            from AutomationUtils.machine import Machine
            log.info("Creating Machine object for Media Agent.")
            media_agent_machine = Machine(machine_name=media_agent_name,
                                          commcell_object=auto_commcell.commcell)
            reg_key = 'EventManager'
            value = 'VmExpiryCheckThreadWaitTimeMinutes'
            # if reg key exists
            if media_agent_machine.check_registry_exists(reg_key, value):
                data = media_agent_machine.get_registry_value(reg_key, value)
                # checking if the data is as desired
                if data != '2':
                    # updating if not
                    log.info("Trying to update reg key value data on Media Agent.")
                    update_success = media_agent_machine.update_registry(reg_key, value, '2',
                                                                         'DWord')
                    if not update_success:
                        log.info("Unable to update reg key on Media Agent.")
                        raise Exception
                    else:
                        log.info("Successfully updated reg key value on Media Agent.")
                else:
                    log.info("Required reg key value data already set.")
            # else creating new reg key value
            else:
                log.info("Trying to create reg key on Media Agent.")
                create_success = media_agent_machine.create_registry(reg_key, value, '2', 'DWord')
                if not create_success:
                    log.info("Unable to create reg key on Media Agent.")
                    raise Exception
                else:
                    log.info("Reg key value successfully created on Media Agent.")

            VirtualServerUtils.decorative_log("Initialize helper objects for Live Mount Validation")
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
            hvobj = auto_virtualization_instance.hvobj
            source_hvobj = auto_instance.hvobj

            copy_precedence = subclient_storage_policy.copies[aux_copy_name]['copyPrecedence']

            # start live mount job for each vm in subclient
            for each_vm in auto_subclient.vm_list:
                log.info("-" * 25 + " Initiating Live Mount Job for " + each_vm + "-" * 25)

                # setting copy precedence to 3 for aux copy
                live_mount_options = {'copyPrecedence': copy_precedence}
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
                    log.error(
                        "Live Mount Job with Job ID: {0} failed for VM {1} with Job Status: {1}.".
                        format(live_mount_job.job_id, each_vm, live_mount_job.status))
                    raise Exception

                # if job is successful, perform live mount validation after job is finished
                log.info(
                    "Success - Live mount for client: {0} for vm policy: {1} with Job ID: {2}.".
                    format(each_vm, vmpolicy_name, live_mount_job.job_id))

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
