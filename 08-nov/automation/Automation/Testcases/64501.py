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
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils.HypervisorHelpers import VmwareHelper
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from AutomationUtils import cvhelper


class TestCase(CVTestCase):
    """Class for executing Basic Verification Test of AllowEmptySubclient regkey"""

    def __init__(self):
        """Initialize the test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - Verify the VM-Hypervisor's subclient association is cleared if the VM list " \
                    "is empty and AllowEmptySubclient set"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "InstanceName": None,
            "BackupsetName": None,
            "SubclientName": None,  # snap enabled with content set as tag rule
            "vcenter_server": None,
            "vcenter_user": None,
            "vcenter_pass": None,
            "tag_name": None,
            "tag_category_name": None,
            "vm_name": None,
            "backup_proxy": None
        }
        self.ind_status = True
        self.failure_msg = ''

    def run(self):
        """Main function for test case execution"""

        try:
            # Step 1
            # create tag and category on vmware setup for vm if not already existing

            hv_obj = VmwareHelper.VmwareHelper([self.tcinputs["vcenter_server"]],
                                               self.tcinputs["vcenter_user"],
                                               self.tcinputs["vcenter_pass"],
                                               hypervisor_type.VIRTUAL_CENTER.value.lower(),
                                               self.commcell)
            hv_obj.VMs = self.tcinputs["vm_name"]

            self.log.info("Creating tag if not already present")
            hv_obj.create_tag(self.tcinputs["tag_name"], self.tcinputs["tag_category_name"])

            # assign tag and tag category to the vm
            self.log.info("Assigning tag to VM")
            hv_obj.VMs[self.tcinputs["vm_name"]].assign_tag(self.tcinputs["tag_name"],
                                                            self.tcinputs["tag_category_name"])

            # Set regkey on backup proxy
            self.log.info("Setting regkey AllowEmptySubclient on the backup proxy")
            proxy_obj = Machine(self.tcinputs['backup_proxy'], self.commcell)
            if proxy_obj.check_registry_exists('VirtualServer', 'AllowEmptySubclient'):
                proxy_obj.update_registry('VirtualServer', 'AllowEmptySubclient', 1, 'DWord')
            else:
                proxy_obj.create_registry('VirtualServer', 'AllowEmptySubclient', 1, 'DWord')

            # Backup the VMs using tag rule
            VirtualServerUtils.decorative_log("Full Snap Backup with backup copy")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.advance_options = {"create_backup_copy_immediately": True}
            backup_options.backup_method = "SNAP"
            backup_options.backup_type = "FULL"
            auto_subclient.backup(backup_options)

            # Remove tag assignment to the VM, so it is no longer part of tag content set in subclient
            self.log.info("Removing tag assignment")
            hv_obj.VMs[self.tcinputs["vm_name"]].remove_tag(self.tcinputs["tag_name"],
                                                            self.tcinputs["tag_category_name"])

            # Run backup again. Snap backup should complete successfully, without any child job created.
            # Backup copy workflow job should complete w/o launching backup copy job.
            try:
                VirtualServerUtils.decorative_log("Incremental Snap Backup with backup copy")
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.advance_options = {"create_backup_copy_immediately": True}
                backup_options.backup_method = "SNAP"
                backup_options.backup_type = 'INCREMENTAL'
                auto_subclient.backup(backup_options, override_child_bc_type="NoChildJob")
            except Exception as exp:
                # as backup copy job is not launched, there will be exception here
                if "'vmStatus'" in str(exp):
                    self.log.info("EXPECTED Exception when in getting job status and archive file id. "
                                  "PROCEEDING AHEAD...")
                else:
                    raise Exception(str(exp))

            # Make sure VSA discover subclient Id should be removed.
            self.log.info("Checking vsa discover subclient id property")
            query = '''select id from app_application where id in
            (select attrval from app_clientprop where componentNameId in
            (select id from app_client where name like '%''' + self.tcinputs['vm_name'] \
                    + '''%') and attrName = 'VSA Discover subclient id')
            '''
            result = cvhelper.execute_query(self.commcell, "COMMSERV", query)
            if str(self.subclient.subclient_id) in str(result):
                raise Exception("VSA Discover subclient ID was not removed for VM after removing "
                                "tag assignment and running backup")
            else:
                self.log.info("VSA Discover subclient ID was removed for VM as expected")

            # Step 2
            # Disable regkey on backup proxy
            self.log.info("Disabling regkey")
            proxy_obj.update_registry('VirtualServer', 'AllowEmptySubclient', 0, 'DWord')

            # Reassign the tag to VM
            self.log.info("Re-assigning tag to VM")
            hv_obj.VMs[self.tcinputs["vm_name"]].assign_tag(self.tcinputs["tag_name"],
                                                            self.tcinputs["tag_category_name"])

            # Backup the VMs using tags rule so VSA discover subclient id is set again
            VirtualServerUtils.decorative_log("Incremental Snap Backup with backup copy")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.advance_options = {"create_backup_copy_immediately": True}
            backup_options.backup_method = "SNAP"
            backup_options.backup_type = 'INCREMENTAL'
            auto_subclient.backup(backup_options)

            # Remove tag assignment to the VM, so it is no longer part of tag content set in subclient
            self.log.info("Removing tag assignment")
            hv_obj.VMs[self.tcinputs["vm_name"]].remove_tag(self.tcinputs["tag_name"],
                                                            self.tcinputs["tag_category_name"])

            # Run backup again. Snap backup should fail in discovery phase
            try:
                VirtualServerUtils.decorative_log("Incremental Snap Backup with backup copy")
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.advance_options = {"create_backup_copy_immediately": False}
                backup_options.backup_method = "SNAP"
                backup_options.backup_type = 'FULL'
                auto_subclient.backup(backup_options)
            except Exception as exp:
                if "No virtual machines were discovered" in str(exp):
                    self.log.info(str(exp) + "\nSnap backup and backup copy failed as EXPECTED")
                else:
                    raise Exception(str(exp))

            # Make sure VSA discover subclient Id was not removed
            self.log.info("Checking vsa discover subclient id property")
            result = cvhelper.execute_query(self.commcell, "COMMSERV", query)
            if self.subclient.subclient_id not in str(result):
                raise Exception("VSA Discover subclient ID was removed for VM ")
            else:
                self.log.info("VSA Discover subclient ID was not removed for VM as expected")

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.ind_status = False
            self.failure_msg = str(exp)

        finally:
            try:
                self.log.info("Deleting tag")
                hv_obj.delete_tag(self.tcinputs["tag_name"], self.tcinputs["tag_category_name"])
                auto_subclient.cleanup_testdata(backup_options)
            except Exception:
                self.log.warning("Testcase cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
