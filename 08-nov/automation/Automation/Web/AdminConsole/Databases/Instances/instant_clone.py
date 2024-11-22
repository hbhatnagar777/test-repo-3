# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module implements the methods that fill in the various instant clone
options for databases. Each class represents the options available per database

InstantClone
    recover                 -- Enter recover to-time options
    retention               -- Enter retention period option
    delete_clone_if_exists  -- Checks if clone exists and call select_clone_delete
    delete_clone            -- Method that submits delete operation
    extend_clone            -- Method that submits retention extend request
    get_clone_details       -- Gets details of the clone job
    refresh                 -- Refreshes content of instant clones page
    select_clone_delete     -- Selects the clone jobs to delete
    select_clone_extend     -- Selects the clone job to extend
    verify_expiry_time      -- Verifies that expiry time is set correctly

OracleInstantClone
    instant_clone  			--  Submits instant clone job for Oracle database

PostgreSQLInstantClone
    instant_clone  			--  Submits instant clone job for PostgreSQL server

MSSQLInstantClone
    _recover                --      Enter recover to options
    instant_clone           --      Submits instant clone job for MSSQL database

MySQLInstantClone
    instant_clone  			--  Fills instant clone job for MySQL server
    get_bin_username        --  Fetch the prefilled username and binary dir (for instance restore)
"""
from time import sleep
from datetime import datetime
from enum import Enum
from Web.Common.page_object import (
    PageService,
    WebAction
)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import CalendarView


class InstantClone(RModalDialog):
    """This class provides the function or operations to perform clone restore
    from instant clones tab"""

    class InstantClonePanelTypes(Enum):
        """Enum to represent classes for implementing clone restore panel"""
        ORACLE = "OracleInstantClone"
        POSTGRES = "PostgreSQLInstantClone"

    def __init__(self, admin_console):
        """Class constructor
            Args:
                admin_console (obj) --  The admin console class object
        """
        super(InstantClone, self).__init__(admin_console)
        self._admin_console = admin_console
        self._rtable = Rtable(self._admin_console)
        self._panel_dropdown = RDropDown(self._admin_console)
        self._dialog = RModalDialog(admin_console)
        self._calendar = CalendarView(self._admin_console)
        self.props = self._admin_console.props

    @PageService()
    def recover(self, recover_to=None):
        """Method to enter point in time recover options
        Args:
            recover_to (str): Most recent backup/Point in time in format
                "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
        """
        if recover_to:
            if recover_to == "Most recent backup":
                self._panel_dropdown.select_drop_down_values(values=[recover_to],
                                                             drop_down_id='recoverToType')
            else:
                self._panel_dropdown.select_drop_down_values(values=['Point in time'],
                                                             drop_down_id='recoverToType')
                calendar = CalendarView(self._admin_console)
                month_abbr = {
                    "01": "january",
                    "02": "february",
                    "03": "march",
                    "04": "april",
                    "05": "may",
                    "06": "june",
                    "07": "july",
                    "08": "august",
                    "09": "september",
                    "10": "october",
                    "11": "november",
                    "12": "december"
                }
                self.click_button_on_dialog(aria_label='Open calendar')
                year = int(recover_to.split(' ')[0].split('/')[2])
                month = month_abbr[recover_to.split(' ')[0].split('/')[0]]
                day = int(recover_to.split(' ')[0].split('/')[1])
                second = int((recover_to.split(' ')[1]).split(':')[2])
                minute = int((recover_to.split(' ')[1]).split(':')[1])
                hour = int((recover_to.split(' ')[1]).split(':')[0])
                date_time_dict = {
                    'year': year,
                    'month': month,
                    'day': day,
                    'hour': hour,
                    'minute': minute,
                    'second': second
                }
                calendar.set_date_and_time(date_time_dict=date_time_dict)

    @PageService()
    def retention(self, retention=None):
        """Method to enter clone retention options
        Args:
            retention     (dict): {"days": 7, "hours": 0}
            default: None
            """
        if retention:
            if "days" in retention:
                self._admin_console.fill_form_by_name('cloneReservationDays', retention["days"])
            else:
                self._admin_console.fill_form_by_name('cloneReservationDays', 0)
            if "hours" in retention:
                self._admin_console.fill_form_by_name('cloneReservationHours', retention["hours"])
            else:
                self._admin_console.fill_form_by_name('cloneReservationHours', 0)

    @PageService()
    def refresh(self):
        """Method to refresh contents of instant clones page"""
        self._rtable.reload_data()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_clone_details(self, clone_jobid):
        """Method to get clone job details based on job id of clone operation
        Args:
            clone_jobid (int): job id of clone to extend retention
        Returns:
            Details of clone as listed in table from instant clones page
        """
        self._rtable.search_for(clone_jobid)
        return self._rtable.get_table_data()

    @PageService()
    def select_clone_extend(self, clone_jobid, new_retention=None):
        """Method to select jobs for extending retention and calculate new expiry time
        Args:
            clone_jobid   (int) : job id of clone for which retention need to be extended
            new_retention (dict): {"days": 7, "hours": 0}  Default: None
        """
        self._rtable.select_rows([clone_jobid])
        if new_retention:
            job_details = self.get_clone_details(clone_jobid)
            expiry_time = int(datetime.strptime(
                job_details['Expiration date'][0], '%b %d, %I:%M %p').replace(
                year=datetime.now().year).timestamp())
            if "days" in new_retention:
                expiry_time += (new_retention["days"] * 24 * 60 * 60)
            if "hours" in new_retention:
                expiry_time += (new_retention["hours"] * 60 * 60)
            expiry_time_map = {
                'year': int(datetime.fromtimestamp(expiry_time).strftime("%Y")),
                'month': datetime.fromtimestamp(expiry_time).strftime("%B"),
                'day': int(datetime.fromtimestamp(expiry_time).strftime("%d")),
                'hour': int(datetime.fromtimestamp(expiry_time).strftime("%I")),
                'minute': int(datetime.fromtimestamp(expiry_time).strftime("%M")),
                'session': datetime.fromtimestamp(expiry_time).strftime("%p")
            }
        self._rtable.select_rows([clone_jobid])
        self.extend_clone(expiry_time=expiry_time_map)
        time_set = datetime.fromtimestamp(expiry_time).strftime('%b %d, %I:%M %p')
        return time_set

    @PageService()
    def extend_clone(self, expiry_time):
        """Method to update extension time  and save it
        Args:
            expiry_time (dict): current expiry time of clone in syntax '03/01/2022 19:54:00'
        """
        self._admin_console.click_button('Extend')
        self._dialog.click_button_on_dialog(aria_label='Open calendar')
        self._calendar.set_date_and_time(expiry_time)
        self._dialog.click_button_on_dialog(id='Save')
        self._admin_console.wait_for_completion()
        self.refresh()

    @PageService()
    def verify_expiry_time(self, clone_jobid, expiry_time):
        """Method to verify retention set is same as argument value
        Args:
            clone_jobid (int): job id of clone for which retention need to be extended
            expiry_time (str): expected expiry time of clone
                               in syntax '03/01/2022 19:54:00'
        Raises:
            CVWebAutomationException:
                If expiry time set in command center is not expiry_time value
        """
        job_details = self.get_clone_details(clone_jobid)
        current_expiry_time = int(datetime.strptime(
            job_details['Expiration date'][0], '%b %d, %I:%M %p').replace(
            year=datetime.now().year).timestamp())
        expiry_time = int(datetime.strptime(expiry_time, '%b %d, %I:%M %p').replace(
            year=datetime.now().year).timestamp())
        if expiry_time - current_expiry_time > 60:
            raise CVWebAutomationException("Expiry time is not set correctly")

    @PageService()
    def delete_clone_if_exists(self, instance_name):
        """Method to select clones to delete for an instance
        Args:
            instance_name (str): Name of the instance for which clones should be cleaned up
        """
        if self._rtable.is_entity_present_in_column(self.props['label.sourceInst'], instance_name):
            self._rtable.search_for(instance_name)
            self.select_clone_delete(instance_name)

    @PageService()
    def select_clone_delete(self, instance_name=None, clone_jobid=0):
        """Method to select clones to delete based on instance name or clone jobid
        Args:
            instance_name (str): Name of the instance for which clones should be cleaned up
            clone_jobid ( int) : Job id of the clone operation
        """
        if instance_name is not None:
            self._rtable.select_rows([instance_name])
            self.delete_clone(instance_name=instance_name)
        else:
            self._rtable.select_rows([clone_jobid])
            self.delete_clone(clone_jobid=clone_jobid)

    @PageService()
    def delete_clone(self, instance_name=None, clone_jobid=0):
        """Method to delete clone instance(s) already selected to delete
        Args:
            instance_name (str): Name of the instance for which clones are selected to delete
            clone_jobid   (int): Job ID of the clone instance already selected to delete
        Raises:
            CVWebAutomationException : If clone instance is not deleted
        """
        self._admin_console.click_button('Delete')
        self.type_text_and_delete('DELETE')
        self._admin_console.wait_for_completion()
        sleep(120)
        self.refresh()
        if instance_name is not None:
            if self._rtable.is_entity_present_in_column(
                    self.props['label.sourceInst'], instance_name):
                raise CVWebAutomationException(
                    "Clone instance for {} is not deleted".format(instance_name))
        else:
            if self._rtable.is_entity_present_in_column(
                    self.props['label.cloneJobId'], str(clone_jobid)):
                raise CVWebAutomationException(
                    "Clone job for {:d} is not deleted".format(clone_jobid))


class OracleInstantClone(InstantClone):
    """Class to represent the clone restore panel for Oracle database"""

    def __init__(self, admin_console):
        """Class constructor
            Args:
                admin_console (obj) --  The admin console class object
        """
        super(OracleInstantClone, self).__init__(admin_console)

    @PageService()
    def instant_clone(self, destination_client, instance_name, oracle_home=None, access_node=None,
                      recover_to=None, pfile=None, staging_path=None, global_area_size=None,
                      redo_log_size=None, clone_retention=None, copy_name=None, overwrite=False,
                      post_clone_commands=None):
        """Method to perform instant clone of instance
            Args:
                destination_client  (str):  Destination client for clone
                instance_name       (str):  Name of clone instance
                oracle_home         (str):  Oracle Home for new instance
                access_node         (str):  Access node client
                    default: None
                recover_to          (str):  Enter point in time in format
                                            "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
                    default: None
                pfile               (str):  PFile path
                    default: None
                staging_path        (str):  Staging path
                    default: None
                global_area_size    (int):  PGA+SGA size in MB
                    default: None
                redo_log_size       (int):  REDO log size in MB
                    default: None
                clone_retention     (dict): {"days": 7, "hours": 0}
                    default: None
                copy_name           (str):  Name of storage policy copy to clone from
                    default: None
                overwrite           (bool): Overwrite if already exists
                    default: False
                post_clone_commands (str):  Post clone commands file path
                    default: None

            Returns:
                 Instant clone job id
        """
        self._panel_dropdown.select_drop_down_values(values=[destination_client],
                                                     drop_down_id='destinationServer')
        self._admin_console.fill_form_by_name('destinationInstanceName', instance_name)
        if oracle_home:
            self._admin_console.fill_form_by_name('oracleHome', oracle_home)
        if access_node:
            self._panel_dropdown.select_drop_down_values(values=[access_node],
                                                         drop_down_id='accessNode')
        if recover_to:
            self.recover(recover_to)
        self.expand_accordion(self.props['label.cloneOptions'])
        self.retention(clone_retention)
        if overwrite:
            self.enable_toggle(toggle_element_id='overrideExists')
        else:
            self.disable_toggle(toggle_element_id='overrideExists')
        if copy_name:
            self._panel_dropdown.select_drop_down_values(values=[copy_name],
                                                         drop_down_id='copyPrecedence',
                                                         partial_selection=True)
        if staging_path:
            self._admin_console.fill_form_by_name('stagingPath', staging_path)
        if pfile:
            self._admin_console.fill_form_by_name('oraPfile', pfile)
        if global_area_size:
            self._admin_console.fill_form_by_name('pgaSgaSize', global_area_size)
        if redo_log_size:
            self._admin_console.fill_form_by_name('redoLogSize', redo_log_size)
        self._admin_console.expand_accordion(self.props['label.postCloneOper'])
        if post_clone_commands:
            self._admin_console.fill_form_by_name('commondFilePath', post_clone_commands)
        self.click_submit()
        _jobid = self._admin_console.get_jobid_from_popup()
        return _jobid


class PostgreSQLInstantClone(InstantClone):
    """Class to represent the clone restore panel for PostgreSQL instance"""

    def __init__(self, admin_console):
        """Class constructor
        Args:
            admin_console (obj) --  The admin console class object
        """
        super(PostgreSQLInstantClone, self).__init__(admin_console)

    @PageService()
    def instant_clone(self, destination_client, destination_instance, **kwargs):
        """Method for instant clone of instance
            Args:
                destination_client   (str):  Destination client for clone
                destination_instance (str):  Name of clone instance
                \\*\\*kwargs          (dict):  Other arguments
                Available kwargs Options:
                    :binary_dir           (str):  Binary directory path for new instance
                    :library_dir          (str):  Library directory path for new instance
                    :recover_to           (str):  "most recent backup"/
                    Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
                                                default: None
                    :custom              (bool): True if destination instance does not exist
                                                default : False
                    :username            (str):  OS user to start new postgres instance
                                                default: postgres
                    :clone_directory     (str):  Staging path for snap and logs
                                                default: /tmp
                    :clone_retention     (dict): {"days": 7, "hours": 0}
                                                default: None
                    :overwrite           (bool): Overwrite if already exists
                                                default: False
                    :post_clone_commands (str):  Post clone commands file path
                                                default: None
                    :port                (int): Port for new postgres instance
                                                default: 5442
            Returns:
                 Instant clone job id
        """
        self._dialog.select_dropdown_values(
            drop_down_id='destinationServer', values=[destination_client])
        self._dialog.select_dropdown_values(
            drop_down_id='destinationInstance', values=[destination_instance])
        if kwargs.get('recover_to', None):
            self.recover(kwargs.get('recover_to'))
        self._dialog.expand_accordion(self.props['label.destOptions'])
        self._dialog.fill_text_in_field(
            'cloneDir', kwargs.get('clone_directory', "/tmp"))
        self._dialog.fill_text_in_field("portTitle", kwargs.get('port', 5442))
        if kwargs.get('custom', False):
            self._dialog.fill_text_in_field(
                'binaryDirectoryTitleLb', kwargs.get('binary_dir', None))
            self._dialog.fill_text_in_field(
                'libDirectoryTitleLb', kwargs.get('library_dir', None))
            self._dialog.fill_text_in_field(
                "hanaDBUsernameTitle", kwargs.get('username', "postgres"))
        self._dialog.expand_accordion(self.props['label.cloneOptions'])
        self.retention(kwargs.get('clone_retention', None))
        if kwargs.get('overwrite', False):
            self._dialog.enable_toggle(toggle_element_id='overrideExists')
        if kwargs.get('post_clone_commands', None):
            self._dialog.expand_accordion(self.props['label.advancedOptions'])
            self._dialog.fill_text_in_field('cmdFilePath', kwargs.get('post_clone_commands'))
        self._dialog.click_submit(wait=False)
        _jobid = self._admin_console.get_jobid_from_popup()
        return _jobid


class MSSQLInstantClone(ModalPanel):
    """Class to represent the restore panel for MS SQL database"""

    def __init__(self, admin_console):
        super(MSSQLInstantClone, self).__init__(admin_console)
        self.__admin_console = admin_console
        self._panel_dropdown = DropDown(self.__admin_console)
        self.props = self.__admin_console.props

    @WebAction()
    def _recover(self, recover_to=None):
        """Method to enter recover options

        Args:
            recover_to          (str):  "most recent backup"/
                Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
        """
        if recover_to:
            self.__admin_console.expand_accordion(
                self.__admin_console.props['label.recoverOptions'])
            if recover_to.lower() == "most recent backup":
                self.__admin_console.select_radio("mostRecent")
            else:
                self.__admin_console.select_radio("pitDate")
                self.__admin_console.fill_form_by_name('dateTimeValue', recover_to)

    @PageService()
    def instant_clone(self, database_type, source_server, source_instance, source_database,
                      destination_client, instance_name, recover_to=None, access_node=None):

        """Method for instant clone of instance

            Args:
                database_type       (str) : the type of database like MSSQL
                source_server       (str) : Source server for Clone
                source_instance     (str)  : Name of clone instance
                source_database     (str) : Name of the source database
                destination_client  (str) :  Destination client for clone
                recover_to          (str)  : recover the database to
                access_node         (str)   : name of the access node

            Returns:
                 Instant clone job id
        """
        agent_prop_map = {"Oracle": "agentType.oracle",
                          "Oracle RAC": "agentType.oracleRac",
                          "SAP HANA": "agentType.sapHana",
                          "PostgreSQL": "agentType.postgreSQL",
                          "DB2": "agentType.DB2",
                          "MySQL": "agentType.MySQL",
                          "Sybase": "agentType.Sybase",
                          "Informix": "agentType.Informix",
                          "SQL Server": "agentType.SQLServer"}
        self.dbtype = database_type.value
        self.__admin_console.access_menu(self.props['label.instantClone'])
        self.__admin_console.access_sub_menu(self.props[agent_prop_map[self.dbtype]])
        self._panel_dropdown.select_drop_down_values(values=[source_server],
                                                     drop_down_id='sourceClient')
        self._panel_dropdown.select_drop_down_values(values=[source_instance],
                                                     drop_down_id='sourceInstance')
        self._panel_dropdown.select_drop_down_values(values=[source_database],
                                                     drop_down_id='sourceDatabase')
        self._panel_dropdown.select_drop_down_values(values=[destination_client],
                                                     drop_down_id='destinationClient')
        self._panel_dropdown.select_drop_down_values(values=[instance_name],
                                                     drop_down_id='destinationInstance')

        if access_node:
            self._panel_dropdown.select_drop_down_values(values=[access_node],
                                                         drop_down_id='accessNode')
        self._recover(recover_to)
        self.__admin_console.submit_form()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class MySQLInstantClone(InstantClone):
    """Class to represent the clone panel for MySQL instance"""

    def __init__(self, admin_console):
        """Class constructor
        Args:
            admin_console (obj) --  The admin console class object
        """
        super(MySQLInstantClone, self).__init__(admin_console)

    @PageService()
    def instant_clone(self, destination_client, destination_instance, **kwargs):
        """Method for instant clone of instance
            Args:
                destination_client   (str):  Destination client for clone
                destination_instance (str):  Name of clone instance
                Available kwargs Options:
                    :binary_dir           (str):  Binary directory path for new instance
                    :recover_to           (str):  "most recent backup"/
                    Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
                                                default: None
                    :custom              (bool): True if destination instance does not exist
                                                default : False
                    :username            (str):  OS user to start new mysql instance
                                                default: root
                    :clone_directory     (str):  Staging path for snap and logs
                                                default: /tmp
                    :clone_retention     (dict): {"days": 7, "hours": 0}
                                                default: None
                    :overwrite           (bool): Overwrite if already exists
                                                default: False
                    :post_clone_commands (str):  Post clone commands file path
                                                default: None
                    :port                (int): Port for new mysql instance
                                                default: 3305

                Returns:
                    list: [job_id, bin_username]
                    where:
                        job_id (str) : job id of clone job
                        bin_username (list) : list of binary dir and username (in case of instance restore otherwise
                                                                                empty list)
        """
        self._dialog.select_dropdown_values(
            drop_down_id='destinationServer', values=[destination_client])
        self._dialog.select_dropdown_values(
            drop_down_id='destinationInstance', values=[destination_instance])
        if kwargs.get('recover_to', None):
            self.recover(kwargs.get('recover_to'))
        self._dialog.expand_accordion(self.props['label.destOptions'])
        self._dialog.fill_text_in_field(
            'cloneDir', kwargs.get('clone_directory', "/tmp"))
        self._dialog.fill_text_in_field("portTitle", kwargs.get('port', 3305))
        if kwargs.get('custom', False):
            self._dialog.fill_text_in_field(
                'binaryDirectoryTitleLb', kwargs.get('binary_dir', None))
            self._dialog.fill_text_in_field(
                "hanaDBUsernameTitle", kwargs.get('username', "root"))
        self._dialog.expand_accordion(self.props['label.cloneOptions'])
        if kwargs.get('overwrite', False):
            self._dialog.enable_toggle(toggle_element_id='overrideExists')
        if kwargs.get('post_clone_commands', None):
            self._dialog.expand_accordion(self.props['label.advancedOptions'])
            self._dialog.fill_text_in_field('cmdFilePath', kwargs.get('post_clone_commands'))
        bin_username = []
        if not kwargs.get('custom'):
            bin_username = self.get_bin_username()
        self._dialog.click_submit(wait=False)
        _jobid = self._admin_console.get_jobid_from_popup()
        return [_jobid, bin_username]

    def get_bin_username(self):
        """
        Fetches the binary dir and username from the clone modal
        Returns:
            list: [binary_dir, username]
        """
        bin_file = self._dialog.get_input_details('binaryDirectoryTitleLb')
        username = self._dialog.get_input_details('hanaDBUsernameTitle')
        return [bin_file, username]

