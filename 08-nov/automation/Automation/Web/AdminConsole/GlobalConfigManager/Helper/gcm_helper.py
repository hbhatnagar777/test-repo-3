# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module acts as a base class for other gcm entities helper. Common helper methods can be defined here which is
applicable for all the entities.

Class:
GCMHelper -> ABC

GCMHelper:
    __init__()                          --      Initialize instance of the GCMHelper class

    validate_create_propagation()       --      Creates and validates if entity is created service commcells

    get_entity_status()                 --      Gets the service commcell propagation status for the entity created

    get_activity()                      --      Go to commcell acvities and fetch all the activities done of cloud console

    validate_commcell_activity()        --      Validate if the operations done on cloud commcells are tracked in commmcell activity view

    ** Static Methods:

        track_activity                  --      Helper method to track operations done on cloud console

        get_service_commcells_object    --      Helper method to create and return service commcell objects from input

    ** Class variable:

        activity                        --      Variable to keep track of all the operations on cloud console

"""
import time
from abc import ABC, abstractmethod

from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVWebAutomationException
from cvpysdk.commcell import Commcell


class GCMHelper(ABC):
    """Helper class to automate generic methods related tasks on cloud console

        Use this as a base class for the other GCM entities helper class.
    """

    # Static variable to track activities across all the entity type operations
    activity = []

    def __init__(self, admin_console: AdminConsole) -> None:

        """Initializes GCMHelper class"""
        self.admin_console = admin_console
        self.table = Rtable(self.admin_console)
        self.admin_console.load_properties(self)
        self.log = self.admin_console.log

    @staticmethod
    def track_activity(operation: str) -> None:
        """Helper method to track operations done on cloud console

        Args:
            operation (str): Operation name as seen in Commcell's view activity
        """
        GCMHelper.activity.append(operation)

    @abstractmethod
    def validate_create_propagation(self,
                                    ui_helper_object: object,
                                    backend_objs: list[object],
                                    service_commcells: list[dict] = None) -> None:
        """Helper method to check if entities created from cloud console are propagated selected service commcells
        Args:
            ui_helper_object:      Instance of a UI helper class of an entity
                Example: GCMUserGroup or roles_helper

            backend_objs:    Cvpysdk instance of entity object for propagation is being checked
                Example: UserGroups or Roles

            service_commcells (list[dict]): list of service commcells information
                Eg: [
                    {
                        "name"        : "serviceC1",
                        "webconsoleEP": "<FQDN of webconsole>",
                        "username"    : admin
                        "password"    : your_secret_password1
                    },
                    {
                        "name"        : "serviceC2",
                        "webconsoleEP": "<FQDN of webconsole>",
                        "username"    : admin
                        "password"    : your_secret_password2
                    }
                ]

        """
        service_commcells_name = None
        if service_commcells:
            service_commcells_name = [i['name'] for i in service_commcells]

        entity_name = ui_helper_object.create_gcm(service_commcells_name)
        self.track_activity(ui_helper_object.CREATE_OPERATION)

        entity_status = self.get_entity_status()

        retry_counter = 5
        while entity_status['In progress'] and retry_counter != 0:
            time.sleep(10)
            self.table.reload_data()
            entity_status = self.get_entity_status()
            retry_counter -= 1

        if failed_commcells := entity_status['Failed']:
            raise Exception(
                f"Propogation failed to following commcells (checked from cloud console): {failed_commcells}")

        propagation_failed_commcell = []

        if not service_commcells:
            self.log.info("Cannot Validate for entity propagation as no service commcells information is provided")
            return

        for backend_obj in backend_objs:
            try:
                backend_obj.refresh()
                backend_obj.get(entity_name.lower())
            except Exception:
                propagation_failed_commcell.append(backend_obj._commcell_object.commserv_name)

        if propagation_failed_commcell:
            raise Exception(f"Entity {entity_name.lower()} not propagated(created) on service commcells: {propagation_failed_commcell}")

    @abstractmethod
    def get_entity_status(self) -> dict:
        """Method to get entity status after creation

        Returns:
            dict: {
                    "Successful":  [commcell5, commcell7],
                    "In progress": [commcell1, commcell2],
                    "Failed":      [commcell3, commcell4]
                }
        """
        time.sleep(10)
        self.admin_console.access_tab('Service CommCells')

        self.table.reload_data()

        table_data = self.table.get_rows_data()[1].values()

        failed_commcells = []
        inprogress_commcells = []
        synced_commcell = []
        status = {}
        for item in table_data:
            status_label = item.get(self.admin_console.props['issueReports.title.status'])

            if status_label == self.admin_console.props['label.status.inSync']:
                synced_commcell.append(item['CommCell'])
            elif status_label == self.admin_console.props['label.status.outOfSync']:
                failed_commcells.append(item['CommCell'])
            elif status_label == self.admin_console.props['label.status.inProgress']:
                inprogress_commcells.append(item['CommCell'])

        status['In progress'] = inprogress_commcells
        status['Failed'] = failed_commcells
        status['Successful'] = synced_commcell

        return status

    def get_activity(self) -> list:
        """Method to get activities on cloud console

        Returns:
            list - activities performed on cloud console
                Example: [Create server plan, Create tag]
        """
        self.admin_console.access_activity()
        self.table.apply_sort_over_column(self.admin_console.props['tableHeader.Time'], False)
        activities = self.table.get_column_data("Operation")
        return activities

    def validate_commcell_activity(self):
        """Validate if actions done on cloud console shows up on activity page

            Note: This method can be called from any child object. Do track activity using self.track_activity if you
            are adding any new operation in individual entity helper file, such that it can be picked up in this method.

            Raises:
                CVWebAutomationException if actions listed and performed are not in line

        """
        activity_list = self.activity

        activities = self.get_activity()
        no_of_activities = len(activity_list)

        required_activities = activities[:no_of_activities]
        required_activities.reverse()
        if activity_list != required_activities:
            self.log.info(f"Actions Performed: {activity_list}\n Actions listed: {required_activities}")
            raise CVWebAutomationException(f"Action performed and actions listed in View Activity screen are different"
                                           f"\nActions Performed: {activity_list}\n Actions listed: {required_activities}")

    @staticmethod
    def get_service_commcells_object(service_commcells: list[dict]) -> list[Commcell]:
        """Method to create and return service commcells object from input

        Args:
            service_commcells (list[dict]): list of service commcells information
                Eg: [
                    {
                        "name"        : "serviceC1",
                        "webconsoleEP": "<FQDN of webconsole>",
                        "username"    : admin
                        "password"    : your_secret_password1
                    },
                    {
                        "name"        : "serviceC2",
                        "webconsoleEP": "<FQDN of webconsole>",
                        "username"    : admin
                        "password"    : your_secret_password2
                    }
                ]

            Returns:
                list of service commcell objects
        """
        if not service_commcells:
            return []

        service_commcells_list = []

        for commcell_info in service_commcells:
            commcell = Commcell(webconsole_hostname=commcell_info['webconsoleEP'],
                                commcell_username=commcell_info['username'],
                                commcell_password=commcell_info['password'],
                                verify_ssl=False)
            service_commcells_list.append(commcell)

        return service_commcells_list
