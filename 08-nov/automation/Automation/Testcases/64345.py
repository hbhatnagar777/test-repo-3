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


class TestCase(CVTestCase):
    """Class for executing AWS On demand access node - Create a Windows Access node using Command Center"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "AWS On demand access node - Create a Windows MA/FREL using Command Center"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.vsa_obj = None
        self.browser = None

        self.proxy_name = None
        self.prov_hypervisor = None
        self.proxy_os = None
        self.entry_points = None
        self.access_node_cleaned = {}
        self.custom_image_options = {}

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
                'testcase_obj': self,
                'subclient_obj': self.subclient,
                'validation_skip_all': True,
                'validation': False
            }

            self.vm_provisioning_options = {
                'server_group': self.tcinputs.get('ServerGroup', None),
                'iam_role': self.tcinputs.get('IAMRole', None),
                'vm_size': self.tcinputs.get('VMSize', None),
                'create_public_ip': self.tcinputs.get('CreatePublicIP', None),
                'availability_zone': self.tcinputs.get('AvailabilityZone', None),
                'proxy_os': self.tcinputs.get('ProxyOperatingSystem'),
                'custom_image': self.tcinputs.get("CustomImage", None),
                'VPC': self.tcinputs.get("VPC", None),
                'security_group': self.tcinputs.get("SecurityGroup", None),
                'subnet': self.tcinputs.get("Subnet", None),
                'advanced_settings': self.tcinputs.get("AdvancedSettings", None),
            }

            self.proxy_name = self.tcinputs.get('ProxyName'),
            self.proxy_os = self.tcinputs.get("ProxyOperatingSystem", 'Unix')
            self.prov_hypervisor = self.tcinputs.get('ProvisioningHypervisor', None)
            self.region = self.tcinputs.get('AvailabilityZone',None)[:-1]
            set_inputs(vsa_obj_inputs, self.vsa_obj)
            self.log.info("Created VSA object successfully.")

            self.entry_points = [entry.strip() for entry in self.tcinputs.get("EntryPoints", 'Hypervisor').split(',')]
            self.access_node_cleaned = {entry_point: False for entry_point in self.entry_points}

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def run(self):
        """"Main function for testcase execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            self.vsa_obj.hypervisor_ac_obj.select_hypervisor(self.prov_hypervisor)
            decorative_log("Setting VM Provisioning settingson Hypervisor - {}".format(self.prov_hypervisor))
            self.vsa_obj.hypervisor_details_obj.configure_aws_vm_provisioning(self.vm_provisioning_options,
                                                                                reset=True)
            for entry_point in self.entry_points:
                decorative_log("Creating access node from {} Level".format(entry_point))
                self.vsa_obj.create_access_node(prov_hypervisor=self.prov_hypervisor,
                                                proxy_name=self.proxy_name, proxy_os=self.proxy_os,
                                                entry_point=entry_point, region=self.region)

                decorative_log("Backup using newly added Access Node")
                self.vsa_obj.backup_type = "INCR"
                self.vsa_obj.backup()

                self.access_node_cleaned[entry_point] = self.vsa_obj.cleanup_access_node(proxy_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            try:
                self.browser.close()
                if self.vsa_obj:
                    for entry_point in self.entry_points:
                        if not self.access_node_cleaned[entry_point]:
                            decorative_log("Creating access node from {} Level".format(entry_point))
                            proxy_name = "{}-{}".format(self.proxy_name,
                                                        ''.join([s[0] for s in entry_point.split()]))
                            try:
                                if not self.vsa_obj.one_click_node_obj:
                                    self.vsa_obj.hvobj = self.vsa_obj._create_hypervisor_object()[0]
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
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
