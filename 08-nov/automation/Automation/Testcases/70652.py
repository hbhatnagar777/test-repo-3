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

    setup()         --  setup function of this test case

    tear_down()     --  tear down function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory,Browser
from Web.Common.page_object import handle_testcase_exception
import collections

class TestCase(CVTestCase):
    """Class for executing VMWare Cross VCenter Tag Validation Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMWare - Cross VCenter - Tag Validation - Automation"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None

    def setup(self):
        """Setup function for test case execution"""
        decorative_log("Initializing browser Objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login Object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance,
                                                 self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.restore_client = self.tcinputs['DestinationClientName']
        self.destination_hvobj, _ = self.vsa_obj._create_hypervisor_object(self.vsa_obj.restore_client)
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.auto_vsa_subclient = subclient_initialize(self)
        self.vsa_obj.testcase_obj = self

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Performing Full Backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.vsa_discovery()
            self.vsa_obj.run_discovery = False
            for vm_name in self.vsa_obj.hvobj.VMs:
                self.vsa_obj.hvobj.VMs[vm_name].get_vm_tags()
            self.tags_that_need_to_be_present = collections.defaultdict(dict)
            self.validate_source_vm_tags()
            self.vsa_obj.backup()
            self.vsa_obj.unconditional_overwrite = True
            self.source_vm_list = list(self.vsa_obj.hvobj.VMs.keys())
            #Deleting source VMs to prevent same MAC address issue
            for vm_name in self.source_vm_list:
                self.vsa_obj.hvobj.VMs[vm_name].delete_vm()

            try:
                decorative_log('Case 1: Performing Full VM OOP Restore to {} Hypervisor'.format(self.tcinputs['DestinationClientName']))
                self.vsa_obj.full_vm_restore()
                for vm_name in self.source_vm_list:
                    should_tag_be_present = lambda category,tag: category in self.tags_that_need_to_be_present[vm_name] and tag in self.tags_that_need_to_be_present[vm_name][category]
                    restore_vm_name = self.vsa_obj.vm_restore_prefix + vm_name
                    self.log.info("----- Validating tags fpr VM {} and its restored VM {} -----".format(vm_name,restore_vm_name))
                    self.vsa_obj.restore_destination_client.VMs[restore_vm_name].get_vm_tags()
                    for category in self.vsa_obj.hvobj.VMs[vm_name].tags:
                        for tag in self.vsa_obj.hvobj.VMs[vm_name].tags[category]:
                            if should_tag_be_present(category,tag):
                                if category not in self.vsa_obj.restore_destination_client.VMs[restore_vm_name].tags or tag not in self.vsa_obj.restore_destination_client.VMs[restore_vm_name].tags[category]:
                                    raise Exception("Tag {}:{} not present on VM {} when it is supposed be present".format(tag,category,restore_vm_name))
                                self.log.info("Tag {}:{} present on VM {} as tag:category pair is present in the Vcenter".format(tag,category,restore_vm_name))
                            else:
                                if category in self.vsa_obj.restore_destination_client.VMs[restore_vm_name].tags and tag in self.vsa_obj.restore_destination_client.VMs[restore_vm_name].tags[category]:
                                    raise Exception("Tag {}:{} present on VM {} when shouldn't be present".format(tag,category,restore_vm_name))
                                self.log.info("Tag {}:{} not present on VM {} as tag:category pair is not present in the Vcenter".format(tag,category,restore_vm_name))
                    self.log.info("Successfully validated tags for VM {} and its restored VM {}".format(vm_name,restore_vm_name))
            except Exception as exp:
                self.log.exception('Failure in Case 1 : {}'.format(exp))
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
    
    def validate_source_vm_tags(self):
        """
        Ensures that the source VMs have the tags in the following format:
        {
            Tag1 (Present in destination VCenter): Category1 (Present in destination VCenter),
            Tag1 (Present in destination VCenter): Category2 (Not Present in destination VCenter),
            Tag2 (Not Present in destination VCenter): Category3 (Not Present in destination VCenter),
            Tag3 (Present in destination VCenter): Category4 (Not Present in destination VCenter)
            Tag4 (Present in destination VCenter): Category5 (Present in destination VCenter)
        }
        """
        required_tag_format = "Tag1 (Present in destination VCenter): Category1 (Present in destination VCenter), " \
                              "Tag1 (Present in destination VCenter): Category2 (Not Present in destination VCenter), " \
                              "Tag2 (Not Present in destination VCenter): Category3 (Not Present in destination VCenter), " \
                              "Tag3 (Present in destination VCenter): Category4 (Not Present in destination VCenter), " \
                              "Tag4 (Present in destination VCenter): Category5 (Present in destination VCenter)"
        for vm_name in self.vsa_obj.hvobj.VMs:
            validation_map = {"Two Same Tag Names but only one category present in destination VCenter": False,
                                "Tag and Category not present in destination VCenter": False,
                                "Tag and Category present in destination VCenter": False,
                                "Tag present but Category not present in destination VCenter": False}
            tags = self.vsa_obj.hvobj.VMs[vm_name].tags
            tag_category_map = {}
            double_tag = None
            for category in tags:
                for tag in tags[category]:
                    if tag in tag_category_map:
                        double_tag = tag
                        tag_status1, category_status1 = self.destination_hvobj.get_tag_and_category_id(tag,category)
                        tag_status2, category_status2 = self.destination_hvobj.get_tag_and_category_id(tag,tag_category_map[tag])
                        valid = ((tag_status1 and category_status1) and (not tag_status2 and not category_status2)) or \
                                ((not tag_status1 and not category_status1) and (tag_status2 and category_status2))
                        if not valid:
                            raise Exception("Tags are not in the required format for VM {}. Required Format: {}. Validation Map: {}".format(vm_name,required_tag_format,validation_map))
                        validation_map["Two Same Tag Names but only one category present in destination VCenter"] = True
                        if category not in self.tags_that_need_to_be_present[vm_name]:
                            self.tags_that_need_to_be_present[vm_name][category] = []
                        if tag_status1 and category_status1:
                            self.tags_that_need_to_be_present[vm_name][category].append(tag)
                        else:
                            self.tags_that_need_to_be_present[vm_name][tag_category_map[tag]].append(tag)
                        break
                if validation_map["Two Same Tag Names but only one category present in destination VCenter"]:
                    break
                tag_category_map[tag] = category
            for category in tags:
                for tag in tags[category]:
                    if tag == double_tag:
                        continue
                    tag_status1, category_status1 = self.destination_hvobj.get_tag_and_category_id(tag,category)
                    tag_status2, category_status2 = self.destination_hvobj.get_tag_and_category_id(tag)
                    if tag_status1 and category_status1:
                        validation_map["Tag and Category present in destination VCenter"] = True
                        if category not in self.tags_that_need_to_be_present[vm_name]:
                            self.tags_that_need_to_be_present[vm_name][category] = []
                        self.tags_that_need_to_be_present[vm_name][category].append(tag)
                    elif tag_status2 and category_status2:
                        validation_map["Tag present but Category not present in destination VCenter"] = True
                    else:
                        validation_map["Tag and Category not present in destination VCenter"] = True
            if not all(validation_map.values()):
                raise Exception("Tags are not in the required format for VM {}. Required Format: {}. Validation Map: {}".format(vm_name,required_tag_format,validation_map))
            self.log.info("Tags on the source VM are in the required format for the VM {}".format(vm_name))

    def tear_down(self):
        try:
            for vm_name in self.source_vm_list:
                restore_vm_name = self.vsa_obj.vm_restore_prefix + vm_name
                self.vsa_obj.restore_destination_client.VMs[restore_vm_name].delete_vm()
            self.vsa_obj.full_vm_in_place = True
            self.vsa_obj.validation_skip_all = True
            self.vsa_obj.full_vm_restore()

        except Exception as exp:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed : {}".format(exp))

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)