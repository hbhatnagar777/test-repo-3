from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods to manage content on the subclient.

Classes:

    ManageContent() ---> _Navigator() ---> AdminConsoleBase() ---> Object()

    ManageContent() -- This class provides methods to manage content on a subclient like add vm and
                        remove content
    Functions:

    add_vm()          -- Adds VMs to the collection content
    remove_content()  -- Removes content from the collection content
    edit_rule()       -- Edits the rule
    add_rule()        -- Add collection content based on rules
    preview()         --  Preview collection content
    filters()         -- Adds VM filters to the subclient content
    disk_filters()    --  Adds disk filters to the subclient content

"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from time import sleep
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails
from Web.AdminConsole.VSAPages.hypervisor_details import HypervisorDetails
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from collections import OrderedDict
from Web.Common.page_object import WebAction
from Web.AdminConsole.Components.core import TreeView
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException
)

from Web.AdminConsole.Components.core import Toggle, TreeView
from Web.AdminConsole.Components.table import Rtable

class ManageContent:
    """
    This class provides methods to manage content on a subclient like add vm and remove content
    """

    def __init__(self, admin_console):
        """
        Init method to create objects of classes used in the file.

        Args:
            driver      (object)   :  the browser object
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self, unique=True)
        self.__driver = admin_console.driver
        self.vsa_sc_obj = VsaSubclientDetails(admin_console)
        self.hypdet_obj = HypervisorDetails(admin_console)
        self.__model_panel_obj = ModalPanel(admin_console)
        self.__panel_dropdown_obj = DropDown(admin_console)
        self.__rpanel_dropdown_obj = RDropDown(admin_console)
        self.__rmodal_dialog_object = RModalDialog(admin_console)
        self.__treeview_obj = TreeView(self.__admin_console)
        self.__rpanelinfo_obj = RPanelInfo(self.__admin_console)

    @WebAction()
    def add_vm(self, vm_content):
        """
        Adds VMs to the collection content

        Args:
            vm_content      (dict)  --  the content to be added to the subclient
            Sample value:   {'datastore':[ds1,ds2],
                                 'host':[h1,h2],
                                 'tags':[tag1,category1],
                                 'vms':[vm1,vm2]
                                }
        """
        self.__driver.find_element(By.LINK_TEXT, "Add virtual machines").click()
        self.__admin_console.wait_for_completion()

        self.hypdet_obj.select_vm_from_browse_tree(vm_content)
        self.__driver.find_element(By.XPATH,
            "//form/cv-browse-collection-content/following-sibling::div/button[2]").click()
        self.__admin_console.wait_for_completion()
        self.__model_panel_obj.submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @WebAction()
    def remove_content(self, content_list, vm_filter=False, disk_filter=False):
        """
        Removes content from the collection content

        Args:
            content_list (list): List of content to remove
            vm_filter (bool)   : if or not filter vm
            disk_filter (bool) : if or not filter disk
        """
        self.__admin_console.log.info("Removing VMs and filters from the collection content")
        self.vsa_sc_obj.manage_content()
        items = []
        if vm_filter is True:
            self.__driver.find_element(By.XPATH, 
                "//form[@name='addCollectionForm']/cv-tabset-component/ul/li[2]/a").click()
        elif disk_filter is True:
            self.__driver.find_element(By.XPATH, 
                "//form[@name='addCollectionForm']/cv-tabset-component/ul/li[3]/a").click()
        for content in content_list:
            if self.__admin_console.cv_table_next_button_exists():
                if self.__driver.find_element(By.XPATH, 
                        "//button[@ng-click='paginationApi.seek(1)']").is_enabled():
                    self.__admin_console.cv_table_click_first_button()
                    self.__admin_console.wait_for_completion()
            while True:
                if self.__admin_console.check_if_entity_exists("xpath", "//span[@title='" + content + "']"):
                    self.__driver.find_element(By.XPATH, 
                        "//span[@title='" + content + "']/../../div[3]/div/a/span").click()
                    if self.__admin_console.check_if_entity_exists("link", "Remove"):
                        self.__driver.find_element(By.XPATH, 
                            "//span[@title='" + content + "']/../../div[3]/div/ul//a[ \
                            contains(text(),'Remove')]").click()
                        break
                elif disk_filter:
                    if self.__admin_console.check_if_entity_exists("xpath", "//span[contains(text(), '" +
                                                                            content + "')]"):
                        self.__driver.find_element(By.XPATH, "//span[contains(text(),'" +
                                                            content + "')]/../../div[3]/div/a"
                                                                      "/span").click()
                        if self.__admin_console.check_if_entity_exists("link", "Remove"):
                            self.__driver.find_element(By.XPATH, 
                                "//span[contains(text(),'" +
                                content + "')]/../../div[3]/div/ul//a[contains(text(),"
                                          "'Remove')]").click()
                            break
                else:
                    if self.__admin_console.cv_table_next_button_exists():
                        if self.__driver.find_element(By.XPATH, 
                                "//button[@ng-disabled='cantPageForward()']").is_enabled():
                            self.__driver.find_element(By.XPATH, 
                                "//button[@ng-disabled='cantPageForward()']/div").click()
                            self.__admin_console.wait_for_completion()
                            continue
                        else:
                            items.append(content)
                            break
                    else:
                        items.append(content)
                        break
        if items != []:
            raise Exception("There is no content with the name " + str(items))
        self.__driver.find_element(By.XPATH, 
            "//form[@name='addCollectionForm']/div/button[3]").click()
        self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//div/div[2]/span[@class='serverMessage error']"):
            raise Exception(self.__driver.find_element(By.XPATH, 
                "//div/div[2]/span[@class='serverMessage error']").text)
        else:
            content = []
            ret = self.vsa_sc_obj.content_info()
            for vms in content_list:
                if vms in set(ret[0]):
                    content.append(vms)
            if content != []:
                raise Exception("The VMs " + str(content) + " could not be deleted.")

    @WebAction()
    def edit_rule(self, content_type, rule_name, rule_type, rule_expressions, new_rule_name):
        """
        Edits the rule

        Args:
            content_type (str)    : the type of content
            rule_name (str)       : name of the rule
            rule_type (str)       : select rule for
                Ex: Virtual machine name/pattern, Datastore, Guest DNS Hostname, Guest OS, Host,
                    Notes, Power state, Template
            rule_expressions (str): condition which matches with the rule type
                Ex: Equals, Contains, Ends with, Starts with
            new_rule_name (str)   : new name of the rule
        """
        self.__admin_console.log.info("Editing the rule")
        self.vsa_sc_obj.manage_content()
        if content_type == "Filters":
            self.__driver.find_element(By.XPATH, 
                "//form[@name='addCollectionForm']/cv-tabset-component/ul/li[2]/a").click()
        elif content_type == "Disk Filters":
            self.__driver.find_element(By.XPATH, 
                "//form[@name='addCollectionForm']/cv-tabset-component/ul/li[3]/a").click()
        while True:
            if self.__admin_console.check_if_entity_exists(
                    "xpath", "//span[@title='" + rule_name + "']"):
                self.__driver.find_element(By.XPATH, 
                    "//span[@title='" + rule_name + "']/../../div[3]/div/a/span").click()
                if self.__admin_console.check_if_entity_exists("link", "Edit rule"):
                    self.__driver.find_element(By.XPATH, 
                        "//span[@title='" + rule_name + "']/../../div[3]/div/ul//a[contains("
                                                        "text(),'Edit rule')]").click()
                    self.__admin_console.wait_for_completion()
                    Select(self.__driver.find_element(By.XPATH, 
                        "//form/label[1]/select")).select_by_visible_text(rule_type)
                    Select(self.__driver.find_element(By.XPATH, 
                        "//form/label[2]/select")).select_by_visible_text(rule_expressions)
                    if rule_type in ["Power state", "Template"]:
                        Select(self.__driver.find_element(By.XPATH, 
                            "//form/label[3]/select")).select_by_visible_text(new_rule_name)
                    else:
                        self.__admin_console.fill_form_by_id("ruleString", new_rule_name)

                    self.__driver.find_element(By.XPATH, 
                        "//form[@name='addRuleForm']/div/button[2]").click()
                    self.__admin_console.wait_for_completion()
                    break
            else:
                if self.__admin_console.cv_table_next_button_exists():
                    if self.__driver.find_element(By.XPATH, 
                            "//button[@ng-disabled='cantPageForward()']").is_enabled():
                        self.__driver.find_element(By.XPATH, 
                            "//button[@ng-disabled='cantPageForward()']/div").click()
                        self.__admin_console.wait_for_completion()
                        continue
                    else:
                        raise Exception("There is no rule with the name " +
                                        rule_name + " in the collection content")
                else:
                    raise Exception("There is no rule with the name " +
                                    rule_name + " in the collection content")
        self.__driver.find_element(By.XPATH, 
            "//form[@name='addCollectionForm']/div/button[3]").click()
        self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//div/div[2]/span[@class='serverMessage error']"):
            raise Exception(self.__driver.find_element(By.XPATH, 
                "//div/div[2]/span[@class='serverMessage error']").text)
        else:
            ret = self.vsa_sc_obj.content_info()
            if not any(new_rule_name in x for x in ret[0]):
                raise Exception("The rule " + new_rule_name + " could not be modified.")

    @WebAction()
    def add_rule(self, rule_type, rule_expressions, rule_name, index=0):
        """
        Add subclient content based on rules

        args:
            rule_type           (str)   --  select rule for
                Ex: Virtual machine name/pattern, Datastore, Guest DNS Hostname, Guest OS, Host,
                    Notes, Power state, Template
            rule_expressions    (str)   --  condition which matches with the rule type
                Ex: Equals, Contains, Ends with, Starts with
            rule_name           (str)   --  the name of the rule
            count   (int)       --rule count (no of rules added)
        """
        self.__admin_console.log.info("Creating a rule- %s of type- %s for discovery of content", rule_expressions,
                                      rule_type)
        if index > 0:
            self.__admin_console.click_by_id("matchAll")
        self.__rpanel_dropdown_obj.select_drop_down_values(drop_down_id=f'rules[{index}].ruleType', values=[rule_type])
        self.__rpanel_dropdown_obj.select_drop_down_values(drop_down_id=f'rules[{index}].operator',
                                                           values=[rule_expressions])

        if rule_type in ["Power state", "Template"]:
            self.__rpanel_dropdown_obj.select_drop_down_values(drop_down_id=f'rules[{index}].ruleName',
                                                               values=[rule_name])
        elif rule_type in ["Region"]:
            self.__driver.find_element(By.XPATH, f'//div[input[@id="rules[{index}].ruleName"]]/parent::*/parent::div/following-sibling::div/button').click()
            add_content_modal = RModalDialog(self.__admin_console, title='Add content')
            region_treeview = TreeView(self.__admin_console)
            region_treeview.select_items([rule_name])
            add_content_modal.click_save_button()

        else:
            self.__admin_console.fill_form_by_id(element_id=f'rules[{index}].ruleName', value=rule_name)

    @WebAction()
    def preview(self, preview_dict=None):
        """
        Preview collection content

        Args:
            preview_dict (dict): dict of VMs in the content

        Returns:
                Returns a dict of VMs in the content
        """
        if not preview_dict:
            preview_dict = {}
        preview_modal = RModalDialog(self.__admin_console, title='Preview')
        self.__admin_console.log.info("Preview of collection content")
        self.__admin_console.click_button(self.__admin_console.props['ManageContent']['label.preview'])
        self.__admin_console.wait_for_completion()

        tries = 0
        while True:
            element_list = self.__driver.find_elements(By.XPATH, 
                '//*[@id="preview-vmgroups"]//table/tbody/tr')

            if not element_list:
                if tries > 5:
                    # If Preview fails after 3 tries, then throw Exception
                    raise WebDriverException("VM group content preview failed")
                else:
                    tries += 1
                    sleep(30)
                    continue
            try:
                for elem in element_list:
                    key = elem.find_element(By.XPATH, "td[1]").text
                    val = elem.find_element(By.XPATH, "td[2]").text
                    preview_dict[key] = val
            except StaleElementReferenceException:
                element_list = self.__driver.find_elements(By.XPATH, '//*[@id="preview-vmgroups"]//table/tbody/tr')
                for elem in element_list:
                    key = elem.find_element(By.XPATH, "td[1]").text
                    val = elem.find_element(By.XPATH, "td[2]").text
                    preview_dict[key] = val
            break
        preview_modal.click_cancel()
        self.__admin_console.wait_for_completion()
        self.__admin_console.log.info(preview_dict)
        self.__admin_console.cancel_form()
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form()
        return preview_dict

    @WebAction()
    def filters(self, filter_dict):
        """
        Adds VM filters to the subclient content
        Args:
            filter_dict   (dict)  --  the dictionary containing the filter for subclient content
                Ex: {'vm': {'datastore':[ds1,ds2],
                                 'host':[h1,h2],
                                 'tags':[tag1,category1],
                                 'vms':[vm1,vm2]
                                },
                     'rule': [rule1,rule2]}
                        rule1 Ex:    Datastore:Equals:datastore1
        """
        self.__admin_console.log.info("Adding filters to the subclient content")
        self.vsa_sc_obj.manage_content()
        manage_content_dialog = RModalDialog(self.__admin_console, title="Manage content")
        manage_content_dialog.enable_toggle(label="Define filters")
        vm_filter_table = Rtable(self.__admin_console, title="Filters")

        if "content" in filter_dict.keys():
            for key, values in filter_dict["content"].items():
                vm_filter_table.access_menu_from_dropdown("Content", "Add")
                filter_vm_dialog = RModalDialog(self.__admin_console, title="Add content")
                filter_vm_dialog.select_dropdown_values(drop_down_id="vmBrowseView", values=[key])
                treeview = TreeView(self.__admin_console)
                treeview.select_items(values)
                filter_vm_dialog.click_save_button()

        if "rules" in filter_dict.keys():
            rules_dict_list = filter_dict['rules']
            for rule_dict in rules_dict_list:
                vm_filter_table.access_menu_from_dropdown("Rule", "Add")
                filter_rule_dialog = RModalDialog(self.__admin_console, title="Add rule")
                for index, rule in enumerate(rule_dict["rule"]):
                    rule_type, rule_expression, rule_name = rule.split(":")
                    self.add_rule(rule_type, rule_expression, rule_name, index)
                    if index+1 != len(rule_dict["rule"]):
                        filter_rule_dialog.click_add()
                if rule_dict["match_rule"] == "any":
                    filter_rule_dialog.select_radio_by_id("matchAny")
                filter_rule_dialog.click_save_button()

        manage_content_dialog.click_save_button()
        self.__admin_console.wait_for_completion()


    @WebAction()
    def disk_filters(self, disk_filters_obj=None):
        """
        Adds disk filters to the subclient content

        Args:
            disk_filters_obj    (str)   --      { 'Rules': [<Rule>], 'Content': [<Disks to select>] }

            Rules should be of the format:
            {
                "filter_type": <str>,
                "filters": [
                    [ <label>, <input type>, <value>]
                ]
            }

            Content should be of the format:
            {
                "<VM Name>": [<Name of the disks>]
            }
        """
        self.__admin_console.log.info("Adding disk filters to the subclient content")
        self.vsa_sc_obj.manage_content()

        disk_filter_toggle = Toggle(self.__admin_console)
        disk_filter_table = Rtable(self.__admin_console, title="Disk Filters")

        disk_filter_toggle.enable(label="Define disk filters")

        rules, content = [], {}

        if "Rules" in disk_filters_obj.keys():
            rules = disk_filters_obj["Rules"]

        if "Content" in disk_filters_obj.keys():
            content = disk_filters_obj["Content"]

        for rule in rules:
            # Process individual rule here
            disk_filter_table.access_menu_from_dropdown("Rule", "Add")

            # Set disk filter type
            self.__rpanel_dropdown_obj.select_drop_down_values(values=[rule['filter_type']],
                                                               drop_down_label="Disk filter type")

            for label, input_type, value in rule["props"]:
                if input_type == 'text':
                    self.__rpanelinfo_obj.fill_input(label, value)
                if input_type == 'dropdown':
                    self.__rpanel_dropdown_obj.select_drop_down_values(values=[value], drop_down_label=label)

            self.__rpanelinfo_obj.click_button("Ok")

        disk_treeview = TreeView(self.__admin_console)

        # Process explicitly defined disks
        self.__rpanelinfo_obj.click_button("Browse")

        for vm, disks in content.items():
            disk_treeview.expand_node(vm)
            disk_treeview.select_items(disks, partial_selection=True)

        self.__rpanelinfo_obj.click_button("Ok")

        self.__rpanelinfo_obj.click_button("Save")