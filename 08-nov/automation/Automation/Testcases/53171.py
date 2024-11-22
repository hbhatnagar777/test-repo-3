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

import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing live mount from snap backup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWARE Live Mount - from Snap Backup (copy precedence 0)"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = backup_options = None
            self.log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log(msg="Initialize helper objects")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            VirtualServerUtils.decorative_log(msg="Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            _adv = {"create_backup_copy_immediately": True}
            backup_options.advance_options = _adv
            backup_options.backup_method = "SNAP"
            auto_subclient.backup(backup_options)

            from cvpysdk.virtualmachinepolicies import VirtualMachinePolicies
            vmpolicy_name = self.tcinputs['VMPolicyName'].lower()
            vmpolicies = VirtualMachinePolicies(auto_commcell.commcell)
            vmpolicy = vmpolicies.get(vm_policy_name=vmpolicy_name)
            self.log.info('Fetching Media Agent specified from Virtual Machine Policy')
            media_agent_name = vmpolicy.properties()['mediaAgent']['clientName']

            VirtualServerUtils.decorative_log(msg="Starting Live Mount Automation")

            # checking if required reg key exists on MA and adding/updating it in case it doesn't
            VirtualServerUtils.decorative_log(msg="Checking Media Agent for reg key "
                                                  "'VmExpiryCheckThreadWaitTimeMinutes'")
            from AutomationUtils.machine import Machine
            self.log.info("Creating Machine object for Media Agent.")
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
                    self.log.info("Trying to update reg key value data on Media Agent.")
                    update_success = media_agent_machine.update_registry(reg_key, value, '2',
                                                                         'DWord')
                    if not update_success:
                        self.log.info("Unable to update reg key on Media Agent.")
                        raise Exception
                    else:
                        self.log.info("Successfully updated reg key value on Media Agent.")
                else:
                    self.log.info("Required reg key value data already set.")
            # else creating new reg key value
            else:
                self.log.info("Trying to create reg key on Media Agent.")
                create_success = media_agent_machine.create_registry(reg_key, value, '2', 'DWord')
                if not create_success:
                    self.log.info("Unable to create reg key on Media Agent.")
                    raise Exception
                else:
                    self.log.info("Reg key value successfully created on Media Agent.")

            VirtualServerUtils.decorative_log(msg="Initialize helper objects for Live Mount "
                                                  "Validation")
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
            self.log.info("Creating HypervisorHelper object for source and mount.")
            source_hvobj = auto_instance.hvobj
            hvobj = auto_virtualization_instance.hvobj

            copy_precedence = 0     # for default

            # start live mount job for each vm in subclient
            for each_vm in auto_subclient.vm_list:
                VirtualServerUtils.decorative_log(msg="Initiating Live Mount Job for" + each_vm)

                # setting copy precedence to 1 for snap
                live_mount_options = {'copyPrecedence': copy_precedence}
                # live_mount_options needs to be a dict for multiple vm's in subclient
                live_mount_job = vmpolicy.live_mount(client_vm_name=each_vm,
                                                     live_mount_options=live_mount_options)

                self.log.info(
                    "Live mount Job for client: %(vm)s for vm policy: %(policy)s with Job ID: "
                    "%(jobid)s started.", {'vm': each_vm, 'policy': vmpolicy_name,
                                           'jobid': live_mount_job.job_id})

                # waiting for job to finish
                self.log.info("Waiting for Live Mount Job to finish.")
                # if job does not complete successfully, raise exception
                if not live_mount_job.wait_for_completion():
                    self.log.error(
                        "Live Mount Job with Job ID: %(jobid)s failed for VM %(vm)s with "
                        "Job Status: %(status)s.", {'jobid': live_mount_job.job_id, 'vm': each_vm,
                                                    'status': live_mount_job.status})
                    raise Exception
                # if job is successful, perform live mount validation after job is finished
                self.log.info(
                    "Success - Live mount for client: %(vm)s for vm policy: %(policy)s "
                    "with Job ID: %(jobid)s.", {'vm': each_vm, 'policy': vmpolicy_name,
                                                'jobid': live_mount_job.job_id})

                # Livemount validation for each_vm after job is successful
                VirtualServerUtils.decorative_log(msg="Starting Live Mount validation now")
                auto_client.live_mount_validation(vmpolicy=vmpolicy,
                                                  hvobj=hvobj,
                                                  live_mount_job=live_mount_job,
                                                  source_vm_name=each_vm,
                                                  mounted_network_name=None,
                                                  source_hvobj=source_hvobj)
        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
