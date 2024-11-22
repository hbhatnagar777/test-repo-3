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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.page_object import handle_testcase_exception
from VirtualServer.VSAUtils.VirtualServerUtils import set_inputs, decorative_log
from VirtualServer.VSAUtils.AutoScaleUtils import AutoScaleNodeConfiguration

import time


class TestCase(CVTestCase):
    """Class for executing Azure On demand access node - Create a Windows Access node using Command Center"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "Azure On demand access node - Create a Windows Access node using Command Center"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.vsa_obj = None
        self.browser = None
        self.auto_scale_node_config = None

        self.proxy_name = None
        self.prov_hypervisor = None
        self.entry_points = None
        self.access_node_cleaned = {}
        self.image_request_id = None

    def login(self):
        """ Logs in to the Command Center """
        try:
            decorative_log("Initialize browser objects")

            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open(maximize=True)

            admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Login completed successfully")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.login()
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            vsa_obj_inputs = {
                'hypervisor': self.tcinputs['ClientName'],
                'instance': self.tcinputs['InstanceName'],
                'subclient': self.tcinputs['SubclientName'],
                'resource_group': self.tcinputs.get('ResourceGroup', None),
                'region': self.tcinputs.get('Region', None),
                'security_group': self.tcinputs.get('SecurityGroup', None),
                'vm_size': self.tcinputs.get('VMSize', None),
                '_create_public_ip': self.tcinputs.get('CreatePublicIP', None),
                'server_group': self.tcinputs.get('ServerGroup', None),
                'resource_pool': self.tcinputs.get('ResourcePool', None),
                'testcase_obj': self,
                'subclient_obj': self.subclient,
                'validation_skip_all': True,
                'validation': False
            }

            set_inputs(vsa_obj_inputs, self.vsa_obj)
            self.log.info("Created VSA object successfully.")

            self.vsa_obj.hvobj = self.vsa_obj._create_hypervisor_object()[0]
            self.auto_scale_node_config = AutoScaleNodeConfiguration(self.vsa_obj)
            self.auto_scale_node_config.node_os = self.tcinputs.get("ProxyOperatingSystem", 'Windows')
            self.proxy_name = self.tcinputs.get('ProxyName')
            self.prov_hypervisor = self.tcinputs.get('ProvisioningHypervisor', None)
            self.entry_points = [entry.strip() for entry in self.tcinputs.get("EntryPoints", 'Hypervisor').split(',')]
            self.access_node_cleaned = {entry_point: False for entry_point in self.entry_points}
            self.image_request_id = self.tcinputs.get("RequestId", None)
            self.auto_scale_node_config.image_type = self.tcinputs.get("CustomImageType", "Public")
            self.auto_scale_node_config.image_name = self.tcinputs.get("CustomImage", None)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def deploy_vm(self, image_version):
        """
            Deploys Azure VMs from Gallery image to make Private image from that and returns VM object
            
            Args:
                image_version (str) : SP version of image to be used for deploying VM

        """
        try:
            vm_props = {
                "vm_name": f"AzureWindowsNode-{image_version.split('.')[1]}",
                "resourceGroup": self.vsa_obj.resource_group,
                "location": self.vsa_obj.region,
                "vm_os": self.auto_scale_node_config.node_os.lower(),
                "tags": dict(self.tcinputs.get('Tags', {})),
                "nic_props": {
                    "nic_name": f"AzureWindowsNode-{image_version.split('.')[1]}",
                    "subnet_id": self.tcinputs.get("SubNetId"),
                    "resourceGroup": self.vsa_obj.resource_group
                },
                "image_id": self.auto_scale_node_config.gallery_image
            }
            try:
                self.log.info(f"Deploying VM {vm_props['vm_name']} "
                              f"from image {self.auto_scale_node_config.gallery_image}")
                vm_name = self.vsa_obj.hvobj.create_vm_from_image(vm_props)

                self.log.info(f"VM {vm_name} created successfully, creating & returning VM object")

                return self.vsa_obj.hvobj.to_vm_object(vm_name)

            except Exception as exp:
                raise Exception(f"Failed to deploy VM with gallery image with error: {exp}")

        except Exception as exp:
            raise Exception(f"Failed to deploy VM with gallery image with error: {exp}")

    def create_managed_image_from_gallery(self):
        try:
            image_version = self.auto_scale_node_config.get_image_details_from_db(self.image_request_id)
            gallery_path = self.tcinputs.get("GalleryPath")
            self.auto_scale_node_config.gallery_image = f"{gallery_path}/{image_version}"

            self.vsa_obj.hvobj.replicate_gallery_image(self.auto_scale_node_config.gallery_image, self.vsa_obj.region)

            vm_obj = self.deploy_vm(image_version)

            self.auto_scale_node_config.create_managed_image(vm_obj)

        except Exception as exp:
            raise Exception(f"Failed to create Managed image from Gallery Image with error {exp}")

    def set_vm_provisioning_options(self):
        """
            Builds VM provisioning option to be sent for editing VM Provisioning setting of the Hypervisor
        """
        try:
            vm_provisioning_options = {
                "custom image os": self.auto_scale_node_config.node_os,
                "custom image": self.auto_scale_node_config.image_path
            }

            self.vsa_obj.hypervisor_ac_obj.select_hypervisor(self.prov_hypervisor)
            self.vsa_obj.hypervisor_details_obj.configure_vm_provisioning(vm_provisioning_options,
                                                                                reset=False)

            return vm_provisioning_options

        except Exception as exp:
            raise Exception(f"Failed to build VM Provisioning options with error: {exp}")

    def run(self):
        """"Main function for testcase execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            if self.image_request_id:
                self.create_managed_image_from_gallery()

            self.set_vm_provisioning_options()

            for entry_point in self.entry_points:
                decorative_log("Creating access node from {} Level".format(entry_point))
                proxy_name = "{}-{}".format(self.proxy_name,
                                            ''.join([s[0] for s in entry_point.split()]))
                self.vsa_obj.create_access_node(prov_hypervisor=self.prov_hypervisor,
                                                proxy_name=proxy_name, proxy_os=self.auto_scale_node_config.node_os,
                                                entry_point=entry_point,
                                                region=self.vsa_obj.region)

                decorative_log("Backup using newly added Access Node")
                self.vsa_obj.backup_type = "FULL"
                self.vsa_obj.backup()

                self.access_node_cleaned[entry_point] = self.vsa_obj.cleanup_access_node(proxy_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            try:
                self.browser.close()
                if self.vsa_obj:
                    if self.auto_scale_node_config.image_name:
                        self.log.info("Cleaning up temp VM and deployed managed Image")
                        temp_vm_obj = self.vsa_obj.one_click_node_obj = self.vsa_obj.hvobj.to_vm_object(self.auto_scale_node_config.image_name)
                        temp_vm_obj.clean_up()
                        
                    for entry_point in self.entry_points:
                        if not self.access_node_cleaned[entry_point]:
                            decorative_log("Cleaning up access node from {} Level".format(entry_point))
                            proxy_name = "{}-{}".format(self.proxy_name,
                                                        ''.join([s[0] for s in entry_point.split()]))
                            try:
                                if not self.vsa_obj.one_click_node_obj:
                                    self.vsa_obj.one_click_node_obj = self.vsa_obj.hvobj.to_vm_object(proxy_name)

                                self.vsa_obj.cleanup_access_node(proxy_name)

                            except Exception as exp:
                                self.log.error("Failed to Delete Access node with error: {}".format(str(exp)))
                                continue
                    self.vsa_obj.cleanup_testdata()

            except Exception as err:
                self.log.warning("Testcase and/or Deployed VM cleanup was not completed: %s", err)
                pass

            if not self.test_individual_status:
                if self.image_request_id:
                    self.auto_scale_node_config.update_image_status_db(self.image_request_id, "Failed")
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
            else:
                self.result_string = f"Verified Image: {self.image_version}"
                if self.image_request_id:
                    self.auto_scale_node_config.update_image_status_db(self.image_request_id, "Certified")
