# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this metallic CRUD test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import collections
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.AdminConsole.Hub.constants import HubServices
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.Hub.dashboard import Dashboard
from Web.Common.page_object import handle_testcase_exception
import json
from AutomationUtils import config
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Class for executing VMGroups CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic AWS VMGroups CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vm_group_name = "TC_CRUD_vmgroup"
        self.vmgroup_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.dashboard = None
        self.config = config.get_config()
        self.utils = TestCaseUtils(self)

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['username'],
                                 self.tcinputs['password'])
        self.dashboard = Dashboard(self.admin_console, service=HubServices.vm_kubernetes)
        try:
            content = json.loads(self.tcinputs['BackupContent'])
        except Exception:
            content = list(self.tcinputs['BackupContent'])
        self.log.info(type(content))
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vmgroup_obj = VMGroups(self.admin_console)
        self.cs_creds = {}
        self.commcell = Commcell(self.commcell.webconsole_hostname, self.tcinputs['username'],
                                 self.tcinputs['password'])
        self.cs_creds['commcell'] = self.commcell
        self.cs_creds['user'] = 'cvautoexec'
        self.cs_creds['password'] = self.config.Metallic.workflow_password
        self.vsa_metallic_helper = VSAMetallicHelper.getInstance(self.admin_console, self.tcinputs, self.cs_creds)
        self.vsa_metallic_helper.metallic_options.BYOS = True
        self.vsa_metallic_helper.metallic_options.existing_hypervisor = True

    def run(self):
        try:
            decorative_log("Adding vmgroup with rules on instance name,tag name, tag value")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_metallic_helper.configure_metallic_vm_group()
            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.tcinputs['SubclientName'] = self.tcinputs['vm_group_name']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.reinitialize_testcase_info()
            self.subclient = self.backupset.subclients.get(self.vsa_obj.subclient)
            self.cs_creds['commcell'] = self.commcell.webconsole_hostname
            self.vsa_obj.auto_vsa_subclient = subclient_initialize(self, **{'is_metallic': True,
                                                                            "metallic_ring_info": self.cs_creds,
                                                                            "region": 'us-east-2'})
            decorative_log("Validating the VM group content with rules")
            vms_in_content = []
            content = {}
            content = json.loads(self.tcinputs['BackupContent'])
            for _value in content['Content']:
                for _browse_type, _values in _value.items():
                    for _region_name, _vms in _values.items():
                        for _vm in _vms:
                            vms_in_content.append(_vm)
            self.log.info(vms_in_content)
            self.log.info(type(vms_in_content))

            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vmgroup_name": self.vm_group_name,
                                                          "hypervisor_name": self.tcinputs['ClientName'],
                                                          "plan": self.tcinputs['Plan'],
                                                          "vm_group_content": vms_in_content})
            '''
            decorative_log("Adding vmgroup with instance search")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.set_vm_group_content(vendor=hypervisor_type.AMAZON_AWS.value,
                                                  vm_content=json.loads(self.tcinputs['BackupContent_with_ID']),
                                                  remove_existing_content=True,
                                                  vm_group=self.vm_group_name)
            decorative_log("Validating===================")
            self.log.info(type(self.tcinputs['BackupContent_with_ID']))
            decorative_log("Validating vmgroup with instance search")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vm_group_content": vms_in_content})
            '''
            decorative_log("rules based content update")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.set_vm_group_content(vendor=hypervisor_type.AMAZON_AWS.value,
                                                  vm_content=json.loads(self.tcinputs['ContentRule']),
                                                  remove_existing_content=True,
                                                  vm_group=self.vm_group_name)
            decorative_log("Validating rules based content")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vm_group_content": vms_in_content})

            decorative_log("Adding vmgroup with region and zone browse")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.set_vm_group_content(vendor=hypervisor_type.AMAZON_AWS.value,
                                                  vm_content=json.loads(self.tcinputs['BackupContent']),
                                                  remove_existing_content=True,
                                                  vm_group=self.vm_group_name)
            decorative_log("Validating vmgroup with region and zone browse")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vm_group_content": vms_in_content})

            # Delete the vmgroup
            decorative_log("Deleting vmgroup")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)

            # Validate whether vmgroup deleted or not.
            decorative_log("checking for deleted vmgroup")
            self.admin_console.navigator.navigate_to_vm_groups()
            if not self.vmgroup_obj.has_vm_group(self.vm_group_name):
                self.log.info("VM group doesnt exist")
                pass
            else:
                self.log.error("VM group not deleted")
                raise Exception
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if self.vsa_metallic_helper:
                self.vsa_metallic_helper.resetInstance()
            self.admin_console.navigator.navigate_to_vm_groups()
            if self.vmgroup_obj.has_vm_group(self.vm_group_name):
                self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)
            Browser.close_silently(self.browser)