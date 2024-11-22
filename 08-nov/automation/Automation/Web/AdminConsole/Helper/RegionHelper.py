# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on Regions or Region details page.

Class:

    RegionMain()

Functions:

    add_new_region()                :   Method to create a new region

    validate_region_locations()     :   Method to validate the locations shown under a particular region

    modify_region_location()        :   Method to modify the region locations

    delete_created_region()         :   Method to delete the region created in the test case

class:

    AssociatedRegion()

Functions:

    set_workload_region()           :   Method to set workload region to entities

    get_workload_region()           :   Method to get the assigned workload region for an entity

    set_backup_region()             :   Method to assign backup destination region to an entity

    get_backup_region()             :   Method to get the assigned Backup destination region for an entity

    validate_backup_region()        :   method to validate backup destination region assigned to the client is same
                                        as that of region assigned to that elastic-plan

    regions_lookup()                :   looks up for regions listed in various places in CC
"""
import random

from Web.AdminConsole.AdminConsolePages.regions import Regions
from Web.AdminConsole.FileServerPages import file_servers, fsagent
from Web.AdminConsole.AdminConsolePages import server_group_details, Commcell, Companies, CompanyDetails, Servers
from Web.AdminConsole.AdminConsolePages import server_groups, Plans, PlanDetails
from Web.AdminConsole.VSAPages import virtual_machines, vm_details, hypervisors, hypervisor_details
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException
from Web.AdminConsole.Components import panel
import time


class RegionMain(object):
    """
        Helper for region/region details page
    """

    def __init__(self, admin_console):
        """
            Initializes the RegionMain helper module

            Args:
                admin_console  (object)   --  Admin Console class object
        """
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__region = Regions(self.__admin_console)
        self.log = admin_console.log

        self.__region_name = 'newRegionTest'
        self.__region_type = 'Custom'
        self.__region_locations = ['Kanpur', 'Lucknow']
        self.__edit_region_locations = {
            'Add': ['Chennai'],
            'Remove': ['Lucknow'],
        }

    @property
    def region_name(self):
        """ Get Region name"""
        return self.__region_name

    @region_name.setter
    def region_name(self, value):
        """ Set Region name"""
        self.__region_name = value

    @property
    def region_type(self):
        """ Get Region name"""
        return self.__region_type

    @region_type.setter
    def region_type(self, value):
        """ Set Region name"""
        self.__region_type = value

    @property
    def region_locations(self):
        """ Get Region locations"""
        return self.__region_locations

    @region_locations.setter
    def region_locations(self, value):
        """ Set Region locations"""
        self.__region_locations = value

    @property
    def edit_region_locations(self):
        """ Get region edit locations"""
        return self.__edit_region_locations

    @edit_region_locations.setter
    def edit_region_locations(self, value):
        """ Set Region edit locations"""
        self.__edit_region_locations = value

    def add_new_region(self):
        """
        Function to add new region
        """
        self.__navigator.navigate_to_regions()
        self.__region.add_region(self.region_name, self.region_type, self.region_locations)

    def create_gcm(self, service_commcell=None):
        """Helper method to create gcm region from cloud console
        Args:
            service_commcell (list): list of service commcell names for GCM (Not applicable for Regions, we have it
                                        here to keep the method signatures same)
        """

        random_string = str(time.time()).split('.')[0]
        self.region_name = f"GCMRegion{random_string}"
        self.add_new_region()
        return self.region_name

    def validate_region_locations(self):
        """
        Function to validate the locations under a given region
        """
        self.__navigator.navigate_to_regions()
        location_list = self.__region.get_region_locations(self.region_name)
        self.log.info(f"Got locations: {location_list}")
        self.log.info(f"Expected: {self.region_locations}")
        for location in self.region_locations:
            match = False
            for ui_location in location_list:
                if location.lower() in ui_location.lower():
                    self.log.info('Location {} matched successfully'.format(location))
                    match = True
                    break
            if not match:
                exp = 'Error in finding location' + ' ' + location
                self.log.exception(exp)
                raise CVTestStepFailure(exp)

    def modify_region_location(self):
        """
        Function to modify region locations
        """
        self.__navigator.navigate_to_regions()
        self.__region.edit_region_locations(self.region_name, self.edit_region_locations)
        add_locations = self.edit_region_locations['Add']
        remove_locations = self.edit_region_locations['Remove']
        self.region_locations.extend(add_locations)
        for location in remove_locations:
            self.region_locations.remove(location)

    def delete_created_region(self):
        """
        Function to modify region locations
        """
        self.__navigator.navigate_to_regions()
        self.__region.delete_region(self.region_name)


class AssociatedRegion(object):
    """
    Helper for actions related to regions associated to various client entities
    """

    def __init__(self, admin_console):
        """
            Initializes the AssociatedRegion helper module

        """

        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__FS = file_servers.FileServers(self.__admin_console)
        self.__FS_details = fsagent.FsAgent(self.__admin_console)
        self.__client_group_details = server_group_details.ServerGroupConfiguration(self.__admin_console)
        self.__vm = virtual_machines.VirtualMachines(self.__admin_console)
        self.__vm_details = vm_details.VMDetails(self.__admin_console)
        self.__hypervisor = hypervisors.Hypervisors(self.__admin_console)
        self.__hypervisor_details = hypervisor_details.HypervisorDetails(self.__admin_console)
        self.__Commcell = Commcell.Commcell(self.__admin_console)
        self.__company = Companies.Companies(self.__admin_console)
        self.__company_details = CompanyDetails.CompanyDetails(self.__admin_console)
        self.__rdropdown = panel.RDropDown(self.__admin_console)
        self.__rpanel_info = panel.RPanelInfo(self.__admin_console)
        self.__servers = Servers.Servers(self.__admin_console)
        self.__server_group = server_groups.ServerGroups(self.__admin_console)
        self.__plan = Plans.Plans(self.__admin_console)
        self.log = admin_console.log
        self.__props = self.__admin_console.props
        self.__plan_details = PlanDetails.PlanDetails(self.__admin_console)

    def set_workload_region(self, entity_type, region, entity_name=None):
        """
        Method to set workload region to entities
        args:
            entity_type(str): type of entity
                    valid parameter: CLIENT, VM, HYPERVISOR, COMMCELL, CLIENTGROUP

            region(str): name of the region to be assigned to the entitiy

            entity_name(str): name of the entity
                note: no entity name should be passed for COMMCELL entity type
        """
        self.log.info("====================================================================================")
        self.log.info("assigning workload region to %s = %s" % (entity_type, entity_name))

        if entity_type.upper() == "CLIENT":
            self.__navigator.navigate_to_file_servers()
            self.__FS.access_server(entity_name)
            self.__FS_details.set_workload_region(region)

        elif entity_type.upper() == "VM":
            self.__navigator.navigate_to_virtual_machines()
            self.__vm.open_vm(entity_name)
            self.__vm_details.set_workload_region(region)

        elif entity_type.upper() == "HYPERVISOR":
            self.__navigator.navigate_to_hypervisors()
            self.__hypervisor.select_hypervisor(entity_name)
            self.__hypervisor_details.set_workload_region(region)

        elif entity_type.upper() == "COMMCELL":
            self.__navigator.navigate_to_commcell()
            self.__Commcell.set_workload_region(region)

        elif entity_type.upper() == "CLIENTGROUP":
            self.__navigator.navigate_to_server_groups()
            self.__client_group_details.access_configuration_tab(entity_name)
            self.__client_group_details.set_workload_region(region)

        elif entity_type.upper() == "COMPANY":
            self.__navigator.navigate_to_company()
            self.__company.access_company(entity_name)
            general_settings = {"Workload region": [region]}
            self.__company_details.edit_general_settings(general_settings)
        else:
            raise CVTestStepFailure("Invalid entity type, please check the helper docstring for valid parameters")
        self.log.info("successfully assigned workload region %s to %s" % (region, entity_type))

    def get_workload_region(self, entity_type, entity_name=None):
        """
        Method to get the assigned workload region for an entity
        args:
            entity_type(str): type of entity
                    valid parameter: CLIENT, VM, HYPERVISOR, COMMCELL, CLIENTGROUP

            entity_name(str): name of the entity
                note: no entity name should be passed for COMMCELL entity type
        """
        self.log.info("====================================================================================")
        self.log.info("Getting workload region assigned to %s = %s" % (entity_type, entity_name))

        if entity_type.upper() == "CLIENT":
            self.__navigator.navigate_to_file_servers()
            self.__FS.access_server(entity_name)
            region = self.__FS_details.get_region("WORKLOAD")

        elif entity_type.upper() == "CLIENTGROUP":
            self.__navigator.navigate_to_server_groups()
            region = self.__client_group_details.get_workload_region(entity_name)

        elif entity_type.upper() == "VM":
            self.__navigator.navigate_to_virtual_machines()
            self.__vm.open_vm(entity_name)
            region = self.__vm_details.vm_summary()["Workload region"]

        elif entity_type.upper() == "HYPERVISOR":
            self.__navigator.navigate_to_hypervisors()
            self.__hypervisor.select_hypervisor(entity_name)
            region = self.__hypervisor_details.get_region()

        elif entity_type.upper() == "COMMCELL":
            self.__navigator.navigate_to_commcell()
            region = self.__Commcell.get_general_details()['Workload region']

        elif entity_type.upper() == "COMPANY":
            self.__navigator.navigate_to_company()
            self.__company.access_company(entity_name)
            region = self.__company_details.get_general_settings()['Workload region']

        else:
            raise CVTestStepFailure("Invalid entity type, please check the helper docstring for valid parameters")
        self.log.info("workload region assigned to %s is %s" % (entity_type, region))
        return region

    def set_backup_region(self, entity_type, entity_name, plan):
        """
        Method to assign backup destination region to an entity
        args:
            entity_type(str): type of entity
                    valid parameter: CLIENT, VM

            entity_name(str): name of the entity

            plan(str): name of the plan to be assigned to the entity
                note: for elastic plans, make sure region is assigned to the plan,
                    and for non-elastic plans, no region should be assigned to the plan
        """
        self.log.info("====================================================================================")
        self.log.info("assigning Backup destination region to %s = %s" % (entity_type, entity_name))

        if entity_type.upper() == "CLIENT":
            self.__navigator.navigate_to_file_servers()
            self.__FS.access_server(entity_name)
            self.__FS_details.set_plan(plan)

        elif entity_type.upper() == "VM":
            self.__navigator.navigate_to_virtual_machines()
            self.__vm.open_vm(entity_name)
            self.__vm_details.set_plan(plan)

        else:
            raise CVTestStepFailure("Invalid entity type, please check the helper docstring for valid parameters")

        self.log.info("successfully assigned plan %s to %s" % (plan, entity_type))

    def get_backup_region(self, entity_type, entity_name):
        """
        Method to get the assigned Backup destination region for an entity
        args:
            entity_type(str): type of entity
                    valid parameter: CLIENT, VM

            entity_name(str): name of the entity
        """
        self.log.info("====================================================================================")
        self.log.info("Getting Backup destination region assigned to %s = %s" % (entity_type, entity_name))

        if entity_type.upper() == "CLIENT":
            self.__navigator.navigate_to_file_servers()
            self.__FS.access_server(entity_name)
            region = self.__FS_details.get_region("BACKUP")

        elif entity_type.upper() == "VM":
            self.__navigator.navigate_to_virtual_machines()
            self.__vm.open_vm(entity_name)
            if "Backup destination region" in self.__vm_details.vm_summary():
                region = self.__vm_details.vm_summary()['Backup destination region']
            else:
                self.log.info("=========No Backup destination region assigned to VM==================")
                region = False

        else:
            raise CVTestStepFailure("Invalid entity type, please check the helper docstring for valid parameters")

        self.log.info("Backup destination region assigned to %s is %s" % (entity_type, region))
        return region

    def validate_backup_region(self, entity_type, entity_name, plan):
        """
        method to validate backup destination region assigned to the client is same as that of region assigned
        to that elastic-plan
        args:
            entity_type(str): type of entity
                    valid parameter: CLIENT, VM
            entity_name(str): name of the entity
            plan(str): name of the plan to be assigned to the entity
        """
        self.log.info("====================================================================================")
        self.log.info("validating Backup destination region assigned to %s = %s" % (entity_type, entity_name))

        region = self.get_backup_region(entity_type=entity_type, entity_name=entity_name)
        self.__navigator.navigate_to_plan()
        self.__plan.select_plan(plan=plan)

        if region in self.__plan_details.get_backup_destination_regions():
            self.log.info("BackupDestination region assigned to %s is correct!!" % entity_name)
        else:
            raise CVTestStepFailure("BackupDestination region assigned to %s is not correct!!" % entity_name)

    def regions_lookup(self, entity_type: str, region: str, entity_name: str = None) -> list:
        """
        Method to look up regions listed in various places in the CC.

        Args:
            entity_type (str)   : The type of entity ('COMPANY', 'SERVER', 'CLIENTGROUP', 'FILESERVER', or 'PLAN').
            region (str)        : The region name to search for within the regions dropdown.
            entity_name (str)   : The name of the entity. If not provided, a random entity will be chosen.

        Returns:
            list: A list of regions found in the dropdowns.
        """
        self.log.info(f"Starting regions lookup for entity_type: {entity_type}")

        entity_type = entity_type.upper()
        navigate_actions = {
            "COMPANY": self.__navigator.navigate_to_company,
            "SERVER": self.__navigator.navigate_to_servers,
            "CLIENTGROUP": self.__navigator.navigate_to_server_groups,
            "FILESERVER": lambda: (
                self.__navigator.navigate_to_file_servers(),
                self.__admin_console.access_tab(self.__props['label.nav.servers'])),
            "PLAN": self.__navigator.navigate_to_plan
        }

        access_actions = {
            "COMPANY": self.__company.access_company,
            "SERVER": self.__servers.select_client,
            "CLIENTGROUP": self.__client_group_details.access_configuration_tab,
            "FILESERVER": self.__FS.access_server,
            "PLAN": self.__plan.select_plan
        }

        get_entity_list = {
            "COMPANY": self.__company.get_active_companies,
            "SERVER": self.__servers.get_all_servers,
            "CLIENTGROUP": self.__server_group.get_all_servers_groups,
            "FILESERVER": self.__FS.get_all_file_servers
        }

        if entity_type not in navigate_actions:
            raise ValueError("Invalid entity type")

        navigate_actions[entity_type]()

        if entity_type == "PLAN":
            if not entity_name:
                raise CVTestStepFailure('Entity name not passed')
            access_actions[entity_type](entity_name)
            self.__admin_console.access_tab(self.__props['label.plan.storageAndRetention'])
            self.__admin_console.click_button_using_text(self.__props['label.plan.addRegion'])
            regions_list = self.__rdropdown.get_values_of_drop_down(drop_down_label='Region', search=region)
            if not regions_list:
                raise CVWebAutomationException(
                    f'{region} not listed in the regions dropdown for entity type {entity_type}')
            self.__admin_console.click_button_using_text(self.__props['action.cancel'])
        else:
            if not entity_name:
                entity_name = random.choice(get_entity_list[entity_type]())
            access_actions[entity_type](entity_name)
            self.__rpanel_info.edit_tile_entity((self.__props['label.workloadRegion']))
            regions_list = self.__rdropdown.get_values_of_drop_down(drop_down_id='regionDropdown_', search=region)
            if not regions_list:
                raise CVWebAutomationException(
                    f'{region} not listed in the regions dropdown for entity type {entity_type}')

        return regions_list
