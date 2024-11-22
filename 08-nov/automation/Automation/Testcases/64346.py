# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Testcase to verify create access node operation using VM provisioning flow from CC

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import datetime
import pytz

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerUtils, VsaTestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.AdminConsolePages.media_agents import MediaAgents
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails


class TestCase(CVTestCase):
    """Class for executing AWS On demand access node - Create a Windows Access node using Command Center"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "AWS On demand access node - Create a Windows MA/FREL using Command Center"
        self.product = self.products_list.VIRTUALIZATIONAMAZON
        self.feature = self.features_list.ADMINCONSOLE
        self.vsa_obj = None
        self.hvobj = None
        self.vm_provisioning_options = None
        self.admin_console = None
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.proxy_name = None
        self.prov_hypervisor = None
        self.proxy_os = None
        self.entry_points = None
        self.testcase_start_timestamp = None
        self.storage_name = None
        self.plan_name = None
        self.plan = None
        self.ind_status = True
        self.failure_msg = ""
        self.tc_utils = None
        self.access_node_cleaned = {}
        self.custom_image_options = {}

    def setup(self):
        """Sets up the Testcase"""
        try:
            decorative_log("Initializing browser objects")
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            decorative_log("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            utc_now = datetime.datetime.now(datetime.timezone.utc)
            ist = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
            self.testcase_start_timestamp = ist.strftime('%Y-%m-%d %H:%M:%S')

            decorative_log("Creating an object for Virtual Server helper")

            self.vm_provisioning_options = {
                'server_group': self.tcinputs.get('ServerGroup', None),
                'iam_role': self.tcinputs.get('IAMRole', None),
                'vm_size': self.tcinputs.get('VMSize', None),
                'create_public_ip': self.tcinputs.get('CreatePublicIP', None),
                'default_vpc': self.tcinputs.get('DefaultVPC', None),
                'system_default_settings': self.tcinputs.get('SetAsSystemDefaultSetting', None),
                'availability_zone': self.tcinputs.get('AvailabilityZone', None),
                'proxy_os': self.tcinputs.get('ProxyOperatingSystem'),
                'custom_image': self.tcinputs.get("CustomImage", None),
                'AccessNodeSettings': self.tcinputs.get("AccessNodeSettings", None),
                'NetworkGateway': self.tcinputs.get("NetworkGateway", None),
                'AutoScaleMaxNoOfVMs': self.tcinputs.get("AutoScaleMaxNoOfVMs", None),
                'AutoScaleNodeOS': self.tcinputs.get("AutoScaleNodeOS", None),
                'AZSpecificInfo': self.tcinputs.get("AZSpecificInfo", []),
                'HypervisorName': self.tcinputs.get("InstanceName", None)
            }

            self.proxy_name = self.tcinputs.get('ProxyName')
            self.proxy_os = self.tcinputs.get("ProxyOperatingSystem", 'Unix')
            self.proxy_os = self.tcinputs.get("ProxyOperatingSystem", 'Unix')
            self.storage_name = f"{self.tcinputs['CloudServerName']}_{self.testcase_start_timestamp}"
            self.plan_name = f"{self.tcinputs['StoragePlanName']}_{self.testcase_start_timestamp}"
            self.prov_hypervisor = self.tcinputs.get('ProvisioningHypervisor', None)
            decorative_log("Creating an object for Virtual Server helper")
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.vsa_obj.region = self.tcinputs.get('AvailabilityZone', None)[:-1]
            self.vsa_obj.zone = self.tcinputs['AvailabilityZone']
            self.vsa_obj.subclient_obj = self.subclient
            self.vsa_obj.testcase_obj = self
            self.vmgroup_obj = VMGroups(self.admin_console)
            self.vsa_sc_obj = VsaSubclientDetails(self.admin_console)
            self.media_agent = MediaAgents(self.admin_console)

            self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                              self.products_list.VIRTUALIZATIONAMAZON,
                                                              self.features_list.DATAPROTECTION)

            self.log.info("Created VSA object successfully.")

            self.entry_points = [entry.strip() for entry in self.tcinputs.get("EntryPoints", 'Hypervisor').split(',')]
            self.access_node_cleaned = {entry_point: False for entry_point in self.entry_points}

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def run(self):
        """"Main function for testcase execution"""
        try:
            _ = self.tc_utils.initialize(self)

            self.log.info("Started executing %s testcase", self.id)
            self.vsa_obj.hypervisor_ac_obj.select_hypervisor(self.prov_hypervisor)
            decorative_log("Setting VM Provisioning settings on Hypervisor - {}".format(self.prov_hypervisor))
            self.vsa_obj.hypervisor_details_obj.configure_vm_provisioning(options=self.vm_provisioning_options,
                                                                          reset=True)
            decorative_log("VM Provisioning settings has been set on Hypervisor - {}".format(self.prov_hypervisor))

            for entry_point in self.entry_points:
                decorative_log("Creating access node from {} Level".format(entry_point))
                self.vsa_obj.create_access_node(prov_hypervisor=self.prov_hypervisor,
                                                proxy_name=self.proxy_name, proxy_os=self.proxy_os,
                                                vm_size=self.vm_provisioning_options['vm_size'],
                                                entry_point=entry_point, region=self.vsa_obj.region,
                                                hypervisor_display_name=self.vm_provisioning_options['HypervisorName'])
                decorative_log("Successfully created access node:".format(self.proxy_name))

                try:
                    decorative_log("Creating Storage using the Access Node: {} ".format(self.proxy_name))
                    self.commcell.refresh()
                    self.commcell.storage_pools.add(
                        storage_pool_name=self.storage_name,
                        mountpath=self.tcinputs['CloudContainer'],
                        media_agent=self.proxy_name,
                        ddb_ma=self.proxy_name,
                        dedup_path=self.tcinputs['DDBLocation'],
                        credential_name=self.tcinputs['SavedCredentials'],
                        cloud_server_type=2,
                        region_id=50,
                        username=f"{self.tcinputs['CloudServerHost']}@2//__CVCRED____EXTERNALID__|-|IAM",
                        password="OTg3NjU0MzIx",
                    )
                    self.log.info("Successfully created Storage: %s", self.storage_name)
                except Exception as exp:
                    self.log.error("Failed to Create Storage: %s", self.storage_name)
                    self.utils.handle_testcase_exception(exp)

                try:
                    decorative_log("Adding a new plan: {}".format(self.proxy_name))
                    self.commcell.refresh()
                    self.plan = self.commcell.plans.add(plan_name=self.plan_name, plan_sub_type="Server",
                                            storage_pool_name=self.storage_name)
                    self.log.info("Successfully created plan: %s", self.plan_name)
                except Exception as exp:
                    self.log.error("Failed to Create plan: %s", self.plan_name)
                    self.utils.handle_testcase_exception(exp)

                try:
                    self.log.info('Disabling the schedule policy')
                    self.plan.schedule_policies['data'].disable()
                except Exception as exp:
                    self.log.error("Failed to Disable Schedule policy for the plan: {}".format(self.plan_name))
                    self.utils.handle_testcase_exception(exp)

                # Update VMG to Newly Created Plan
                try:
                    self.log.info("Updating VM Group with Newly created plan: %s", self.plan_name)
                    self.admin_console.navigator.navigate_to_vm_groups()
                    self.vmgroup_obj.select_vm_group(self.tcinputs['SubclientName'])
                    self.vsa_sc_obj.update_storage_plan(plan_name=self.plan_name)
                except Exception as exp:
                    self.log.error("Failed to update VM Group with Newly created plan: %s", self.plan_name)
                    self.utils.handle_testcase_exception(exp)

                decorative_log("Backup using newly added Access Node")
                self.reinitialize_testcase_info()
                _ = self.tc_utils.initialize(self)

                self.tc_utils.run_backup(self)

                decorative_log("Performing Full VM Restore")
                self.tc_utils.run_virtual_machine_restore(self, proxy_client=self.proxy_name)

                decorative_log("Performing File Level Restore")
                self.tc_utils.run_guest_file_restore(self, child_level=True, proxy_client=self.proxy_name,
                                                     skip_block_level_validation=True,
                                                     destination_client=self.proxy_name)

                try:
                    self.log.info("Changing VM Group's plan from %s to %s", self.plan_name,
                                  self.tcinputs['ExistingStoragePlanName'])
                    self.admin_console.navigator.navigate_to_vm_groups()
                    self.vmgroup_obj.select_vm_group(self.tcinputs['SubclientName'])
                    self.vsa_sc_obj.update_storage_plan(plan_name=self.tcinputs['ExistingStoragePlanName'])
                except Exception as exp:
                    self.log.warning("Failed to update VM Group's plan")


                try:
                    decorative_log("Deleting Plan for Cleanup")
                    self.log.info('Check for plan %s', self.plan_name)
                    self.commcell.refresh()
                    if self.commcell.plans.has_plan(self.plan_name):
                        self.log.info('Deletes plan %s', self.plan_name)
                        self.commcell.plans.delete(self.plan_name)
                except Exception as exp:
                    self.log.warning("Failed to delete plan: %s", self.plan_name)

                try:
                    decorative_log("Deleting Storage for Cleanup")
                    self.log.info('Check for storage %s', self.storage_name)
                    self.commcell.refresh()
                    if self.commcell.storage_pools.has_storage_pool(self.storage_name):
                        self.log.info('Deletes storage %s', self.storage_name)
                        self.commcell.storage_pools.delete(self.storage_name)
                except Exception as exp:
                    self.log.warning("Failed to delete storage: %s", self.storage_name)

                try:
                    decorative_log("Clean Up Access Node")
                    self.admin_console.navigator.navigate_to_media_agents()
                    self.media_agent.retire_media_agent(media_agent=self.proxy_name)
                    self.commcell.refresh()
                    if self.commcell.clients.has_client(self.proxy_name):
                        self.access_node_cleaned[entry_point] = self.vsa_obj.cleanup_access_node(self.proxy_name)
                except Exception as exp:
                    self.log.warning("Failed to Clean Up Access Node: %s", self.proxy_name)

                decorative_log("Delete VM Client")
                for vm_name in self.vsa_obj.hvobj.VMs.keys():
                    if self.commcell.clients.has_client(vm_name):
                        try:
                            self.commcell.clients.delete(vm_name)
                            self.log.info("Successfully deleted VM client: %s", vm_name)
                        except Exception as exp:
                            self.log.warning("Failed to delete VM client: %s, Error: %s", vm_name, str(exp))

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.browser.close()
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED

    def tear_down(self):
        decorative_log("Tear Down Started")
        try:
            self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
            self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                               True, self.tcinputs.get('DeleteRestoredVM', True))
            self.result_string = f'Validation for AMI : {self.tcinputs.get("AccessNodeSettings", {}).get("CustomImage", "No Custom Image Found")}'
        except Exception:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed")
