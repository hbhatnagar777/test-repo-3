# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the Index Server page on the AdminConsole

Class:

    IndexServer()

Functions:
    __init__()                              --  Method to initiate IndexServer class
    verify_roles()                          --  verify if the input roles are matching index server roles
    check_node_dropdown_empty()             --  checks if the Index Server Node dropdown is empty or not
    validate_backup_plan_dropdown()         --  Validate if all the backup plans in the dropdown are Server Backup plan
    verify_backup_plan()                    --  verify if the backup plan is assigned or not.
    verify_node_data()                      --  verifies if the node data is matching with the input
    is_index_server_exists()                --  Check if index server exists
    create_index_server()                   --  Create an index server
    delete_index_server()                   --  Deletes an Index Server
    validate_index_server_overview()        --  Validates Index Server Overview
    backup_index_server()                   --  Performs the backup of the index server
    edit_index_server_node()                --  Edit an index server node
    edit_backup_plan()                      --  Adds / Modify a backup plan to an index server
    edit_index_server_roles()               --  edit roles for the index server
    add_node()                              --  Add a new node on an existing index server
    balance_load()                          --  Balance load between two or more nodes
"""
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.core import Checkbox
from Web.AdminConsole.Components.cventities import CVMainBarAction
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RModalPanel, RDropDown, RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.page_object import (WebAction, PageService)
from dynamicindex.index_server_helper import IndexServerHelper
from dynamicindex.utils.constants import AUTO_SCALE_INDEX_MOVE, AUTO_SCALE_INDEX_PREPARE
from dynamicindex.utils.constants import INCREMENTAL, MIN_JVM, MAX_JVM
from dynamicindex.utils.constants import SERVER_BACKUP_PLAN_TYPE, NO_DATA_AVAILABLE, ENGLISH, CONTINUE


class IndexServer:
    """ Class for the Index Servers page """

    def __init__(self, admin_console):
        """
        Method to initiate IndexServer class

        Args:
            admin_console   (Object) :  admin console object
        """
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.__rtable = Rtable(self.__admin_console)
        self.__plans_obj = Plans(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__modal_dialog = RModalDialog(self.__admin_console)
        self.__drop_down = RDropDown(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__panel_info_obj = RPanelInfo(self.__admin_console, "General")
        self.__job_obj = Jobs(self.__admin_console)
        self.__cv_entitites_obj = CVMainBarAction(self.__admin_console)
        self.__checkbox = Checkbox(self.__admin_console)
        self.java_memory = "javaMemory"
        self.port_no = "portNo"

    @WebAction()
    def verify_roles(self, input_roles):
        """
        verify if the input roles are matching index server roles

        Args:
            input_roles (list): list of the roles
        Raises:
            Exception:
                if Roles do not match
        """
        self.__panel_info_obj.open_hyperlink_on_tile('Show all')
        panel_details = self.__panel_info_obj.get_details()
        index_server_roles = panel_details['Roles'].split('\n')
        index_server_roles[-1] = index_server_roles[-1][:-4]
        if sorted(index_server_roles) != sorted(input_roles):
            self.log.info(f'Roles Mismatch. Expected Roles: {input_roles} & Actual Roles: {index_server_roles}')
            raise Exception("Index Server Roles are not Same")
        self.log.info('Roles Validated')

    @PageService()
    def check_node_dropdown_empty(self, drop_down_id):
        """
        checks if the Index Server Node dropdown is empty or not

        Args:
            drop_down_id   (str):  ID of the Dropdown element
        Returns:
            True: if dropdown is empty
            False: if dropdown is not empty
        """
        available_nodes = self.__drop_down.get_values_of_drop_down(drop_down_id=drop_down_id)
        if len(available_nodes) == 0 or NO_DATA_AVAILABLE in available_nodes:
            return True
        return False

    def validate_backup_plan_dropdown(self, index_server_name, commcell_obj):
        """
        Validates if all the backup plans in the dropdown are Server Backup plan

        Args:
            index_server_name        (str):  Name of the index server
            commcell_obj (commcell object):  Commcell Object
        """
        self.__admin_console.navigator.navigate_to_index_servers()
        self.__rtable.access_toolbar_menu(self.__admin_console.props['label.add'])
        self.__admin_console.wait_for_completion()
        self.log.info("Entering index server name")
        self.__admin_console.fill_form_by_name("indexServerName", index_server_name)
        self.__wizard.click_next()
        backup_plans = self.__wizard.get_all_plans()
        plans_obj = commcell_obj.plans
        for plan in backup_plans:
            if plan.lower() in plans_obj.all_plans:
                plan_obj = plans_obj.get(plan.lower())
                self.log.info(f'Checking if {plan} is a valid Server Backup Plan')
                if plan_obj.plan_type != SERVER_BACKUP_PLAN_TYPE:
                    raise Exception(f'{plan} is not a valid Server Backup Plan')

    @PageService()
    def verify_backup_plan(self, index_server_name, backup_plan):
        """
        verify if the backup plan is assigned or not. if assigned it is matching with input or not

        Args:
            index_server_name (str): name of index server
            backup_plan (str): backup plan which is expected to be assigned
        Raises:
            Exception:
                if backup plan is not assigned
                if wrong backup plan is assigned
        """
        self.__admin_console.navigator.navigate_to_index_servers()
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.log.info('Validating Backup plan')
        panel_details = self.__panel_info_obj.get_details()
        backup_plan_details = panel_details['Server backup plan'].split("\n")
        if backup_plan_details[0] == 'Not assigned':
            raise Exception('Backup Plan not Assigned')
        if backup_plan_details[0] != backup_plan:
            raise Exception(f'Backup Plan Mismatch. Expected = {backup_plan} & Actual = {backup_plan_details[0]}')
        self.log.info('Backup Plan validated')

    @PageService()
    def verify_node_data(self, index_server_table_data, node_name, node_directory=None, memory=None, port_number=None,
                         commcell_object=None):
        """
        verifies if the node data is matching with the input

        Args:
            index_server_table_data (dict): Data on the index server page table
            node_name               (str):  name of index server node
            node_directory          (list):  directory of node
            memory                  (list):  allocated memory
            port_number             (list):  port number of node
            commcell_object         (obj):  commcell object

        Raises:
            Exception:
                if Node Names do not match
                if Index Directory do not match
                if Memory Allocated do not match
                if Port Number do no match
        """
        index = index_server_table_data['Name'].index(node_name)
        if index_server_table_data['Name'][index] != node_name:
            raise Exception("Node Names are not Matching")
        if node_directory is not None and index < len(node_directory) and index_server_table_data['Index directory'][index] != node_directory[index]:
            raise Exception("Node Directory is not matching")
        if memory is not None and index < len(memory) and int(index_server_table_data['Allocated memory (MB)'][index]) != memory[index]:
            raise Exception("Memory Allocated is not Equal")
        if port_number is not None and index < len(port_number) is not None and int(index_server_table_data['Port'][index]) != port_number[index]:
            raise Exception("Port Number is not Same")
        if commcell_object is not None:
            machine_object = Machine(node_name, commcell_object)
            memory_registry = round(int(machine_object.get_registry_value('Analytics', 'analyticsMaxJvm')) / 1024)
            memory_ui = round(int(index_server_table_data['Allocated memory (MB)'][index]) / 1024)
            memory_machine = int(machine_object.get_hardware_info()['RAM'][: -2])
            if memory_ui != memory_registry:
                raise Exception("Overview memory doesn't matches the registry value")
            if memory_machine < MIN_JVM * 2 and memory_ui != MIN_JVM:
                raise Exception(f"JVM is {memory_ui} whereas machine memory is {memory_machine}")
            elif memory_machine > MAX_JVM * 2 and memory_ui != MAX_JVM:
                raise Exception(f"JVM is {memory_ui} whereas machine memory is {memory_machine}")
            else:
                if round(memory_machine / 2) != memory_ui:
                    raise Exception("Overview memory doesn't matches the machine RAM value")
        self.log.info("Successfully validated the node data with the input data!")

    @PageService()
    def is_index_server_exists(self, index_server_name):
        """
        Check if index server exists

        Args:
            index_server_name           (str):   Name of index server
        Returns:
            True                                if index server exist
            False                               if index server do not exist
        """
        return self.__rtable.is_entity_present_in_column('Name', index_server_name)

    @PageService()
    def create_index_server(
            self, index_server_name, index_directory, index_server_node_names, solutions=None,
            index_server_roles=None, backup_plan=None, port_number=None, memory=None, language=ENGLISH):
        """
        Create an index server

        Args:
            index_server_name           (str):   Name of index server
            index_directory             (list):   Index Directory
            index_server_node_names     (list):  Nodes on which index server needs to be created
            solutions                   (list):  Solutions on which index Server will work
            index_server_roles          (list):  Roles of index Server
            backup_plan                 (str):   Backup Plan for index Server
            port_number                 (list):   Port Number for the node
            memory                      (list):   Memory allocated to index server on a node
            language                    (str):   Index Server language

        Raises:
            Exception:
                if input types do not match
        """
        if not isinstance(index_server_name, str) or not isinstance(index_server_node_names, list):
            raise Exception('Invalid input data type')
        self.log.info(f"Creating an Index Server with name: {index_server_name}")
        self.__rtable.access_toolbar_menu(self.__admin_console.props['label.add'])
        self.__admin_console.wait_for_completion()
        self.log.info("Entering index server name")
        self.__admin_console.fill_form_by_name("indexServerName", index_server_name)
        self.__drop_down.select_drop_down_values(drop_down_id="indexServerLanguage", values=[language],
                                                 case_insensitive_selection=True)
        self.__wizard.click_next()
        self.__admin_console.check_for_react_errors()
        error_msg = self.__admin_console.get_error_message()
        if error_msg:
            raise Exception(error_msg)
        if backup_plan is None:
            self.__wizard.click_next()
            self.__wizard.click_button(CONTINUE)
        else:
            try:
                self.__wizard.select_plan(backup_plan)
            except NoSuchElementException:
                raise Exception(f'{backup_plan} does not exist')
            self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        error_msg = self.__admin_console.check_for_react_errors()
        if error_msg:
            raise Exception(error_msg)
        self.log.info("Selecting Solutions from Dropdown")
        self.__drop_down.select_drop_down_values(drop_down_id="indexServerApplications", values=solutions,
                                                 case_insensitive_selection=True)
        if index_server_roles:
            self.log.info("Selecting Roles from Dropdown")
            self.__drop_down.select_drop_down_values(drop_down_id="indexServerRoles", values=index_server_roles,
                                                     case_insensitive_selection=True)
        self.__wizard.click_next()
        error_msg = self.__admin_console.check_for_react_errors()
        if error_msg:
            raise Exception(error_msg)
        self.log.info('Checking if Nodes Dropdown is Empty')
        if self.check_node_dropdown_empty("indexServerNodes"):
            raise Exception('No Nodes Available')
        self.log.info("Selecting Nodes from dropdown")
        index = 0
        for node in index_server_node_names:
            self.__drop_down.select_drop_down_values(drop_down_id="indexServerNodes", values=[node],
                                                     case_insensitive_selection=True)
            self.__admin_console.fill_form_by_id('indexDirectory', index_directory[index])
            if memory:
                edit_memory_button_xpath = "//button[contains(@class, 'MuiIconButton-root') and @title='Edit']"
                self.__admin_console.click_by_xpath(edit_memory_button_xpath)
                self.__admin_console.fill_form_by_id(self.java_memory, memory[index])
            if port_number:
                self.__admin_console.fill_form_by_id(self.port_no, port_number[index])
            self.__admin_console.click_button_using_text('Add')
            try:
                self.__admin_console.check_for_react_errors()
            except Exception as error_msg:
                self.__modal_dialog.click_cancel()
                raise Exception(error_msg)
            index += 1
        self.__wizard.click_next()
        self.__wizard.click_submit()
        self.__admin_console.wait_for_completion()
        error_msg = self.__admin_console.check_for_react_errors()
        if error_msg:
            raise Exception(error_msg)
        self.log.info("Index Server Created")

    @PageService()
    def delete_index_server(self, index_server_name, force_delete=False):
        """
        Deletes an Index Server

        Args:
            index_server_name (str): Name of the index server to be deleted
            force_delete      (bool): to delete index server even if it is has associated entities
        Raises:
            Exception:
                if failed to delete the index server
        """
        self.__rtable.access_action_item(index_server_name, 'Delete')
        self.__admin_console.fill_form_by_id('confirmText', 'Delete')
        self.__admin_console.click_button_using_text('Delete')
        notification = self.__admin_console.get_notification(wait_time=120)
        if force_delete and notification != (index_server_name + ' is now deleted'):
            self.log.info(notification)
            associated_entities = notification[notification.index('[') + 1: notification.index(']')].split(',')
            self.log.info('Removing the associated entities')
            self.__admin_console.navigator.navigate_to_governance_apps()
            self.__admin_console.navigator.navigate_to_plan()
            for plan_name in associated_entities:
                self.__plans_obj.action_delete_plan(plan_name)
            self.__admin_console.navigator.navigate_to_index_servers()
            self.delete_index_server(index_server_name)
        if self.__rtable.is_entity_present_in_column('Name', index_server_name):
            raise Exception("Index Server is not Deleted Properly")

    @PageService()
    def validate_index_server_overview(self, index_server_name, index_server_node, node_directory,
                                       port_number=None, input_roles=None, memory=None, commcell_object=None):
        """
        Validates Index Server Overview

        Args:
            index_server_name       (str):  Name of the index server to overview
            input_roles             (list): list of all roles associated to index server
            index_server_node       (list): list of all index server nodes
            node_directory          (list):  directory of node
            memory                  (list):  allocated memory
            port_number             (list):  port number of node
            commcell_object         (obj):   commcell object
        """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        if input_roles is not None:
            self.log.info("Validating Roles")
            self.verify_roles(input_roles)
        self.select_nodes_tab()

        for node in index_server_node:
            self.__rtable.expand_row(row_text=node)
            index_server_table_data = self.__rtable.get_table_data()
            index_node_name = index_server_table_data['Name'][0]
            index_server_detail = index_server_table_data['Name'][1].split('\n')

            index_server_data = {index_server_detail[i]: [index_server_detail[i + 1]] for i in
                                 range(0, len(index_server_detail), 2)}
            index_server_data.update({"Name": [index_node_name]})

            self.verify_node_data(index_server_data, node, node_directory, memory, port_number, commcell_object)

        self.log.info("Successfully validated Index Server Overview!")

    def select_nodes_tab(self):
        """
        Select Review tab in FSO review page
        """
        self.__admin_console.driver.find_element(By.XPATH,
                                                 "//a[contains(@id,'NODES')]").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def backup_index_server(self, index_server_name, backup_type=INCREMENTAL):
        """Performs the backup of the index server

        Args:
            index_server_name   (str):  Name of index server
            backup_type         (str):  The type of backup for ex-> Full, Incremental, SynthFull
                                        default - Incremental

        Returns:
            job id  (int):  Job id of the Backup job.
            """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.__cv_entitites_obj.access_action_item('Backup')
        self.__modal_panel.select_radio_button_and_type(backup_type, False, "")
        self.__modal_panel.submit()
        notification = self.__admin_console.get_notification()
        job_id = notification.split('\n')[0].split()[-1]
        self.__job_obj.job_completion(job_id)
        return int(job_id)

    @PageService()
    def edit_index_server_node(self, index_server_name, node, memory=None, port=None):
        """
        Edit an index server node

        Args:
            index_server_name   (str):  Name of index server
            node                (str):  Node to be edited
            memory              (int):  JVM memory for index server node
            port                (int):  Port Number to modify
        """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.select_nodes_tab()
        self.__rtable.access_action_item(node, "Edit")
        self.__admin_console.wait_for_completion()
        node_name = self.__driver.find_element(By.NAME, 'indexServerName')
        index_directory = self.__driver.find_element(By.NAME, 'indexDirectory')
        if node_name.is_enabled():
            raise Exception('Node name should be Non editable')
        if index_directory.is_enabled():
            raise Exception('Index Directory should be Non editable')
        if memory:
            self.__admin_console.fill_form_by_name(self.java_memory, memory)
        if port:
            self.__admin_console.fill_form_by_name(self.port_no, port)
        self.__admin_console.click_button_using_text('Save')
        self.__admin_console.wait_for_completion()
        try:
            self.__admin_console.check_for_react_errors()
        except Exception as error_msg:
            self.log.info(error_msg)
            self.__admin_console.click_button_using_text('Cancel')
            raise Exception(error_msg)
        index_server_table_data = self.__rtable.get_table_data()
        self.verify_node_data(index_server_table_data, node, memory=memory, port_number=port)

    @PageService()
    def edit_backup_plan(self, index_server_name, new_backup_plan):
        """
        Adds / Modify a backup plan to an index server

        Args:
            index_server_name   (str):  Name of index server
            new_backup_plan     (str):  Backup plan to be added
        """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.__panel_info_obj.edit_tile_entity('Server backup plan')
        self.__admin_console.wait_for_completion()
        self.__drop_down.select_drop_down_values(drop_down_id='plan', values=[new_backup_plan])
        self.__admin_console.click_button_using_text('Submit')

    @PageService()
    def edit_index_server_roles(self, index_server_name, roles):
        """
        edit roles for the index server

        Args:
            index_server_name   (str):  Name of index server
            roles               (list):  New List of Roles
        """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.__panel_info_obj.edit_tile_entity('Roles')
        self.__drop_down.select_drop_down_values(drop_down_id="indexServerRoles", values=roles,
                                                 case_insensitive_selection=True)
        self.__admin_console.click_button_using_text('Submit')
        self.log.info("Validating Roles")
        self.verify_roles(roles)

    @PageService()
    def add_node(self, index_server_name, node, index_directory, port_number=None, memory=None, load_balancing=False):
        """
        Add a new node on an existing index server

        Args:
            index_server_name           (str):   Name of index server
            index_directory             (str):   Index Directory
            node                        (str):   Node to be added
            port_number                 (int):   Port Number for the node
            memory                      (int):   Memory allocated to index server on a node
            load_balancing              (bool):  to allow load balancing or not
        """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.__admin_console.click_button_using_text('Add')
        try:
            self.log.info("Choosing Node from Drop Down")
            self.__drop_down.select_drop_down_values(drop_down_id="indexServerNodes", values=[node],
                                                     case_insensitive_selection=True)
            self.__admin_console.fill_form_by_id('indexDirectory', index_directory)
            if memory:
                edit_memory_button_xpath = "//button[contains(@class, 'MuiIconButton-root') and @title='Edit']"
                self.__admin_console.click_by_xpath(edit_memory_button_xpath)
                self.__admin_console.fill_form_by_id(self.java_memory, memory)
            if port_number:
                self.__admin_console.fill_form_by_id(self.port_no, port_number)
            # Disabling Load Balancing if load_balancing is False (it is enabled by default)
            if not load_balancing:
                self.__checkbox.uncheck(id='loadBalance')
            self.log.info("Submitting Form")
            self.__admin_console.submit_form()
            self.__admin_console.wait_for_completion()
        except Exception:
            raise Exception("Node addition unsuccessful")

    @PageService()
    def balance_load(self, index_server_name, commcell_obj, destination=None):
        """
        Balance load between two or more nodes

        Args:
              index_server_name     (str):  Name of index server
              commcell_obj          (object):   Commcell Object
              destination           (str):  Destination of load balancing
        Returns:
            job id  (int):  Job id of the AutoScale Index Move job.
        """
        self.__rtable.access_action_item(index_server_name, 'Overview')
        self.__admin_console.click_button_using_text('Load balance')
        if destination:
            self.__drop_down.select_drop_down_values(0, [destination])
        self.__admin_console.submit_form()
        index_server_helper = IndexServerHelper(commcell_obj, index_server_name)
        index_server_helper.verify_job_completion(commcell_obj, AUTO_SCALE_INDEX_PREPARE)
        time.sleep(15)
        self.log.info("Sleeping for 15 Seconds")
        index_server_helper.verify_job_completion(commcell_obj, AUTO_SCALE_INDEX_MOVE)
        self.log.info('Load Balancing operation completed')

    def get_no_node_error_msg(self):
        return self.__admin_console.driver.find_element(
            By.XPATH, f"//p[contains(text(), 'Add at least one node')]").text
