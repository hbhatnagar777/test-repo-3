# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module implements the methods that fill in the various restore
options for databases. Each class represents the options available per database

DynamoDBRestorePanel:

    adjust_write_capacity()         --      Sets temporary write capacity for restore

    enable_overwrite()              --      Enables the overwrite destination tables toggle

    set_streams()                   --      Sets the number of streams for restore

    same_account_same_region()      --      Submits a restore with same cloud account as source
    and restores tables to same regions as source

    cross_account_same_region()     --      Submits a cross account restore to the given destination
    account and tables are restored to same region as source

RedshiftRestorePanel:

    same_account_same_region()      --      Submits a restore with same cloud account as source
    and restores snapshots to same regions as source

DocumentDBRestorePanel:

    same_account_same_region()      --      Submits a restore with same cloud account as source
    and restores snapshots to same regions as source

PostgreSQLRestorePanel
    in_place_restore()              --      Submits a in place restore of postgreSQL database

    out_of_place_restore()          --      Submits a out of place restore of postgreSQL database

OracleRestorePanel
    _redirect_tablespace            --      Enters redirect path for datafile restore for
     corresponding tablespace

    _redirect                       --      Enters redirect restore options

    _recover                        --      Enter recover to options

    in_place_restore()              --      Submits a in place restore of Oracle database

    out_of_place_restore()          --      Submits an out of place restore of Oracle database

DB2RestorePanel
    in_place_restore()              --      Submits a in place restore of db2 database

    out_of_place_restore()          --      Submits an out of place restore of DB2 database

    _redirect                       --      Enters redirect restore options


MySQLRestorePanel
    in_place_restore()              --      Submits a in place restore of MySQL database

    out_of_place_restore()          --      Submits out of place restore of MySQL database

RDSRestorePanel:
    restore()                       --      Submits RDS restore without setting any advanced options

SybaseResorePanel
    mark_email()                    --      Marks notify by email option

    mark_recover_databases()        --      Marks recover databases option

    _click_device()                 --      Clicks on device in redirect options

    _construct_redirect_dict()      --      Constructs redirect options dict

    in_place_restore()              --      Submits an in place restore of Sybase database

    out_of_place_restore()          --      Submits an out of place restore of Sybase database

InformixRestorePanel
    informix_restore()              --      To perform inplace and out of place restore for Informix
    __get_value()                   --      Gets element value from restore options using element id

CosmosDBSQLRestorePanel:

    disable_write_throughput()      --      Disables the adjust throughput toggle

    select_overwrite()              --      Enables overwrites destination containers option

    in_place_restore()              --      Submits restore to same cloud account

CosmosDBCASSANDRARestorePanel:

    disable_write_throughput()      --      Disables the adjust throughput toggle

    select_overwrite()              --      Enables overwrites destination containers option

    in_place_restore()              --      Submits restore to same cloud account

    out_of_place_restore()          --      Submits out of place restore

SQLRestorePanel:

    in_place_restore()              --      Submits in place restore job for SQL Server

    restore()                       --      Submits a restore of a SQL database with options

SAPHANARestorePanel:

    in_place_restore()              --      Submits a in place restore of SAP Hana database

    out_of_place_restore()          --      Submits a out of place restore of SAP Hana database

SpannerRestorePanel:

    in_place_restore()              --      Submits in place restore job for Spanner database

SAPOracleRestorePanel
    
    in_place_restore()              --      Submits a in place restore of SAP Oracle database

    outof_place_restore()           --      Submits a database copy restore for SAP Oracle database
    

"""
import time
from datetime import datetime
from Web.AdminConsole.Components.core import CalendarView
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException

from Web.Common.page_object import (
    PageService,
    WebAction
)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RDropDown, RModalPanel
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.table import Rtable
from selenium.common.exceptions import ElementNotInteractableException
from AutomationUtils import logger


class DynamoDBRestorePanel(RModalDialog):
    """Class to represent the restore panel for DynamoDB"""

    def __init__(self, admin_console):
        super(DynamoDBRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def adjust_write_capacity(self, write_capacity):
        """Sets temporary write capacity for restore
        Args:
            write_capacity   (int):  The value to be set as write capacity

        """
        self.enable_toggle(toggle_element_id='adjustWriteCapacity')
        write_capacity = str(write_capacity)
        self.fill_text_in_field('units', write_capacity)

    @PageService()
    def enable_overwrite(self):
        """Enables the overwrite destination tables toggle"""
        self.enable_toggle(toggle_element_id='overwrite')

    @PageService()
    def set_streams(self, number_of_streams):
        """Sets the number of streams for restore

        Args:
            number_of_streams   (int):  Number of streams to be set

        """
        self.__admin_console.fill_form_by_id('numberOfStreams',
                                             number_of_streams)

    @PageService()
    def same_account_same_region(self, overwrite=True, adjust_write_capacity=0, notify=False):
        """Submits a restore with same cloud account as source
        and restores tables to same regions as source

        Args:
            overwrite (Boolean): True to overwrite tables
                                False to not overwrite

            adjust_write_capacity (int):  The value to be set as write capacity

            notify          (bool) : to enable notification by enable
        """
        if overwrite:
            self.enable_overwrite()
        if adjust_write_capacity != 0:
            self.adjust_write_capacity(adjust_write_capacity)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid

    @PageService()
    def cross_account_same_region(self, dest_account, overwrite=True, notify=False):
        """Submits a cross account restore to the given destination
        account and tables are restored to same region as source

        Args:
            dest_account (str):  The name of destination cloud account
            overwrite (Boolean): True to overwrite tables
                                False to not overwrite
            notify  (bool): to enable notification by enable

        """
        self._dropdown.select_drop_down_values(
            values=[dest_account], drop_down_id='destinationServer')
        if overwrite:
            self.enable_overwrite()
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class RedshiftRestorePanel(RModalDialog):
    """Class to represent the restore panel for Redshift"""

    def __init__(self, admin_console):
        super(RedshiftRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = RModalDialog(self.__admin_console)

    @PageService()
    def same_account_same_region(self, cluster_identifier, notify=False):
        """Submits a restore with same cloud account as source
        and restores snapshots to same regions as source

        Args:
            cluster_identifier(str) --  Name of the cluster to be created

            notify            (bool) -- to enable notification by enable

        """
        self.__admin_console.fill_form_by_id('dbIdentifier', cluster_identifier)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class DocumentDBRestorePanel(RModalDialog):
    """Class to represent the restore panel for DocDB"""

    def __init__(self, admin_console):
        super(DocumentDBRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = RModalDialog(self.__admin_console)

    @PageService()
    def same_account_same_region(self, cluster_identifier, number_of_instance=1, notify=False):
        """Submits a restore with same cloud account as source
        and restores snapshots to same regions as source

        Args:
            cluster_identifier(str) --  Name of the cluster to be created

            number_of_instance(str) --  Number of instances to be created

            notify            (bool) -- to enable notification by enable

        """
        self.__admin_console.fill_form_by_id('dbIdentifier', cluster_identifier)
        self.__admin_console.fill_form_by_id('numberOfInstances', number_of_instance)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class PostgreSQLRestorePanel(RModalDialog):
    """Class to represent the restore panel for PostgreSQl DB"""

    def __init__(self, admin_console):
        super(PostgreSQLRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def in_place_restore(self, fsbased_restore=False, revert=False, proxy_client=None, notify=False,
                         numberofstreams=None, staging_path=None, global_objects=False, cluster_restore=False,
                         cleanup_directories=False, restore_to_entire_cluster=True, restore_to_client_name=None,
                         redirect_values=None):
        """Submits a in place restore of postgreSQL database

        Args:

            fsbased_restore (bool): Boolean value to specify if the restore is being
                                    performed on fsbasedbackupset
            revert          (bool): Boolean value to select revert option for restore
            proxy_client    (str) : Name of the proxy client or access node to mount snap
            notify          (bool)  : to enable notification by enable
            numberofstreams (int) : Number of data streams
            staging_path    (str) : to set the staging path
            global_objects  (bool): Boolean value to select global objects option for restore
            cluster_restore (bool) : Bool value to select if cluster restore or not
            cleanup_directories (bool) : Bool value to select cleanup directories or not in cluster restores
            restore_to_entire_cluster (bool) : Bool value to specify type of cluster restore
            restore_to_client_name (str) : Client ID to which restore will happen in case of single node restore
            redirect_values (dict) : {(client name, client id):(original directory, redirect directory)}

        Returns:
            restore job id on succesful restore submission

        """
        self.select_radio_by_id("inPlaceRestore")
        if revert:
            self.select_checkbox("hardwareRevert")
        if proxy_client:
            self.select_dropdown_values(values=[proxy_client],
                                        drop_down_id='proxyClient')
        if numberofstreams:
            self.fill_text_in_field(element_id="numberOfStreams", text=numberofstreams)
        if staging_path:
            self.click_button_on_dialog(aria_label='Browse')
            self.browse_path(staging_path)
        if global_objects:
            self.select_checkbox('stageGlobalObjects')
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()

        if cluster_restore:
            self.click_button_on_dialog(text="Cluster restore options")
            if cleanup_directories:
                self.select_checkbox('cleanUpPgDirs')
            if not restore_to_entire_cluster:
                self.deselect_checkbox('fullClusterRestore')
                self.select_checkbox(checkbox_label=f'{restore_to_client_name}')
            if redirect_values:
                for node, directory in redirect_values.items():
                    self.click_element(f"//*[text()='{node[0]}']")
                    self.select_checkbox(checkbox_id=f"redirect_{node[1]}")
                    self.click_button_on_dialog("Find and replace")
                    redirect_dialog = RModalDialog(self.__admin_console, title="Find and replace")
                    redirect_dialog.fill_text_in_field(element_id="findWhatString", text=directory[0])
                    redirect_dialog.fill_text_in_field(element_id="replaceWithString", text=directory[1])
                    redirect_dialog.click_submit()
                    redirect_dialog_2 = RModalDialog(self.__admin_console, title="Find and replace")
                    redirect_dialog_2.click_yes_button()
                    self.click_element(f"//*[text()='{node[0]}']")
            self.click_save_button()

        self.click_submit()
        if fsbased_restore:
            self.click_yes_button()
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def out_of_place_restore(self, destination_client, destination_instance, fsbased_restore=False, notify=False):
        """Submits a out of place restore of postgreSQL database

        Args:

            destination_client      (str): Destination client name

            destination_instance    (str): Destination instance name

            fsbased_restore      (bool): Boolean value to specify if
            the restore is being performed on fsbasedbackupset

            notify              (bool)  : to enable notification by enable

        Returns:
            restore job id on succesful restore submission

        """
        self.select_radio_by_id('outOfPlaceRestore')
        self._dropdown.select_drop_down_values(
            values=[destination_client], drop_down_id='destinationServer')
        self._dropdown.select_drop_down_values(
            values=[destination_instance], drop_down_id='destinationInstance')
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        if fsbased_restore:
            self.click_yes_button()
        return self.__admin_console.get_jobid_from_popup()


class OracleRestorePanel(RModalDialog):
    """Class to represent the restore panel for Oracle database"""

    def __init__(self, admin_console):
        super(OracleRestorePanel, self).__init__(admin_console)
        self.log = logger.get_log()
        self.__admin_console = admin_console

    @WebAction()
    def _redirect_tablespace(self, tablespace, redirect_paths):
        """Method to fill target path for specific tablespace for redirect restore
            Args:
                tablespace      (str):  Name of tablespace to redirect
                redirect_paths  (list): Redirect paths for datafiles of tablespace
        """
        self.__admin_console.expand_accordion(tablespace)
        xpath = f"//span[contains(text(), '{tablespace}')]/ancestor::div[@role='tab']" \
                f"/following-sibling::div/descendant-or-self::input"
        elems = self.__admin_console.driver.find_elements(By.XPATH, xpath)
        for elem, path in zip(elems, redirect_paths):
            elem.clear()
            elem.send_keys(path)

    @WebAction()
    def _redirect(self, redirect_all_path=None, redirect_datafiles=None,
                  redirect_redo=None, redirect_temp=None):
        """Method to enter redirect options

        Args:
            redirect_all_path   (str)   : Redirect all Path
                default: None
            redirect_datafiles  (dict)  : Dict mapping tablespaces with redirect path of datafiles
                default: None
            redirect_redo       (dict)  : Redo logs redirect path
                default: None
            redirect_temp       (str)   : Temp logs redirect path
                default: None

        """
        redirect_options_modal = RModalDialog(self.__admin_console, title='Redirect path options')
        self.click_redirect_options()
        if redirect_all_path:
            self.select_radio_by_value('ALL')
            redirect_options_modal.fill_text_in_field('redirectAllCB', redirect_all_path)
        if redirect_datafiles:
            self.select_radio_by_value('INDIVIDUAL')
            for tablespace in redirect_datafiles:
                self._redirect_tablespace(tablespace.upper(), redirect_datafiles[tablespace])
        if redirect_redo:
            redirect_options_modal.enable_toggle(label='Online redo logs')
            redirect_options_modal.fill_text_in_field('numberOfGroups', redirect_redo['nGroups'])
            redirect_options_modal.fill_text_in_field('redoInGroups', redirect_redo['nFiles'])
            redirect_options_modal.fill_text_in_field('redoSize', redirect_redo['redoSize'])
            for Log_vol_path in range(redirect_redo['nFiles']):
                redirect_options_modal.fill_text_in_field(f"redoLogFilePath_{Log_vol_path}",
                                                          redirect_redo['LVol'][Log_vol_path])
        if redirect_temp:
            redirect_options_modal.enable_toggle(label='Redirect temporary tablespaces')
            redirect_options_modal.fill_text_in_field('redoLogsPath', redirect_temp)
        self.click_save_button()

    @WebAction()
    def _recover(self, recover_to=None):
        """Method to enter recover options

        Args:
            recover_to          (str/int):"most recent backup"/"current time"/SCN number/
            Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
        """
        if recover_to:
            recover_to_map = {"most recent backup": "Most recent backup", "current time": "Current time"}
            if isinstance(recover_to, int):
                self.select_dropdown_values(values=['SCN'],
                                            drop_down_id='recoverToType')
                self.fill_text_in_field('scnInput', recover_to)
            elif recover_to.lower() in recover_to_map:
                self.select_dropdown_values(values=[recover_to_map[recover_to.lower()]],
                                            drop_down_id='recoverToType')
            else:
                self.select_dropdown_values(values=['Point in time'],
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
    def in_place_restore(self, redirect_all_path=None, redirect_datafiles=None,
                         redirect_redo=None, recover_to=None, staging_path=None, table_options=None,
                         revert=False, notify=False, auxiliary_path=None):
        """
        submits inplace restore for Oracle database

        Args:
            redirect_all_path   (str)   : Redirect all Path
                default: None

            redirect_datafiles  (dict)  : Dict mapping tablespaces with redirect path of datafiles
                default: None

            redirect_redo       (str)   : Redo logs redirect path
                default: None

            recover_to          (str/int):"most recent backup"/"current time"/SCN number
                                            /Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
                default: None
            staging_path        (str)   : The path on which the auxiliary instance is created
                default: None

            table_options:      (str)   : Advanced options for table-level restores
                default: None
                Accepted Values: Import/Dump

            auxiliary_path:     (str)   : The path to the auxiliary instance location
                default: None

            revert              (bool)  : to enable hardware revert for the snap restore

            notify              (bool)  : to enable notification by enable

        Returns:
             restore job id on successful restore submission
        """
        self.select_radio_by_id("inPlaceRestore")
        if redirect_all_path or redirect_datafiles or redirect_redo:
            self._redirect(redirect_all_path, redirect_datafiles, redirect_redo)
        self._recover(recover_to)
        if auxiliary_path:
            self.fill_text_in_field("axuPath", auxiliary_path)
        if staging_path:
            self.fill_text_in_field("stagingPath", staging_path)
        if table_options:
            self.select_radio_by_id(f"oracleTableOption{table_options}Radio")
        if revert:
            self.expand_accordion(label="Advanced options")
            self.select_checkbox("hardwareRevert")
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()

        if not table_options:
            self.click_yes_button()

        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid

    @PageService()
    def out_of_place_restore(self, destination_client, destination_instance,
                             redirect_all_path=None, redirect_datafiles=None,
                             redirect_redo=None, rman_duplicate=False,
                             duplicate_standby=False, recover_to=None,
                             pdb_clone=False, staging_path=None,
                             redirect_all_pdb_path=None, redirect_all_pdb_name=None, redirect_individual_pdb=None,
                             source_wallet_password=None, dest_wallet_password=None,
                             table_options="", auxiliary_instance=None, user_created_auxiliary=False, pfile=None,
                             redirect_path=None,
                             notify=False, redirect_temp=None):
        """
        submits out of place restore for Oracle database

        Args:
            destination_client  (str)   :   Destination client to restore data to
            destination_instance(str)   :   Destination instance to restore data to
            redirect_all_path   (str)   :   Redirect all Path
                default: None
            redirect_datafiles  (dict)  :   Dict mapping tablespaces with redirect path of datafiles
                default: None
            redirect_redo       (dict)  :   Dict containing Number of log Volumes, Path etc
                default: None
            rman_duplicate      (bool)  :   True if RMAN duplicate option must be enabled
                default: False
            duplicate_standby   (bool)  :   True if duplicate for standby option is to be enabled
                default: False
            recover_to          (str/int):  "most recent backup"/"current time"/SCN number/
            Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
                default: None
            pdb_clone           (bool)   :   True if pdb clone option must be enabled
                default: False
            staging_path        (str)    :   Provide staging path
                default: None
            redirect_all_pdb_path (str)  :   Provide path to redirect all pdbs
                default: None
            redirect_all_pdb_name (list) :   List of new names of the pdbs to be cloned, order of names to be taken
            from command center.
                default: None
            redirect_individual_pdb (dict):  The key will be the old pdb name, while the value will be a list of new pdb
            name and the datafile path for the new pdb
            Example - {"Oldpdbname1":["newpdbname1","newpdbpath1"],"Oldpdbname2":["newpdbname2","newpdbpath2"]}
                default: None
            source_wallet_password  (str)   : Source wallet password
                default: None
            dest_wallet_password    (str)   : Destination wallet password
                default: None
            table_options:      (str)   : Advanced options for table-level restores
                default: Empty String
                Accepted Values: Import/Dump
            auxiliary_instance(str)   :   Auxiliary instance to restore data
            user_created_auxiliary  (bool):  Provide name of the user-specified auxiliary instance
                default: False
            pfile:              (str)   : Path to the pfile of the auxiliary instance
                default: None
            redirect_path       (str)   : Path to redirect the datafiles
                default: None
            notify              (bool)  : to enable notification by enable
            redirect_temp       (str)   : to redirect temp tablespace

        Returns:
             restore job id on successful restore submission
        """
        self.select_radio_by_id('outOfPlaceRestore')
        if rman_duplicate:
            self.select_dropdown_values(values=['RMAN duplicate'],
                                        drop_down_id='restoreType')
            if duplicate_standby:
                self.select_checkbox(checkbox_id="duplicateStandby")
        self.select_dropdown_values(values=[destination_client],
                                    drop_down_id='destinationServer',
                                    partial_selection=True)
        self.select_dropdown_values(values=[destination_instance],
                                    drop_down_id='destinationInstance')
        if pdb_clone:
            self.select_dropdown_values(values=['PDB Clone'],
                                        drop_down_id='restoreType')
            self.click_button_on_dialog(text=self.__admin_console.props['label.pdbCloneOptions'])
            self.fill_text_in_field("stagingPath", staging_path)
            if redirect_all_pdb_path:
                self.fill_text_in_field("redirectAllCDB", redirect_all_pdb_path)
                for names in range(len(redirect_all_pdb_name)):
                    cur_pdb_id = f"clonePDBName_{names}"
                    self.fill_text_in_field(cur_pdb_id, redirect_all_pdb_name[names])
            elif redirect_individual_pdb:
                self.__admin_console.select_radio(id="individualTSCB")
                iterator = 0
                for oldpdb, newpdb in redirect_individual_pdb.items():
                    self.log.info("Redirect %s to %s as name %s", oldpdb, newpdb[0], newpdb[1])
                    cur_pdb_id = f"clonePDBName_{iterator}"
                    cur_datafile_id = f"pdbDataFilePath_{iterator}"
                    self.fill_text_in_field(cur_pdb_id, newpdb[0])
                    self.fill_text_in_field(cur_datafile_id, newpdb[1])
                    iterator += 1
            self.click_save_button()
        if source_wallet_password:
            self.fill_text_in_field("sourceWallet", source_wallet_password)
            self.fill_text_in_field("destinationWallet", dest_wallet_password)
        if redirect_all_path or redirect_datafiles or redirect_redo:
            self._redirect(redirect_all_path, redirect_datafiles, redirect_redo)
        if staging_path and not pdb_clone:
            self.fill_text_in_field("stagingPath", staging_path)
        if redirect_path and not pdb_clone:
            self.fill_text_in_field("rdsRedirect", redirect_path)
        if table_options:
            self.select_radio_by_id(f"oracleTableOption{table_options}Radio")
        if user_created_auxiliary:
            self.deselect_checkbox(checkbox_id='auxilariyIns')
            self.select_dropdown_values(index=2, values=[auxiliary_instance])
            if pfile:
                self.fill_text_in_field("pFile", pfile)
        self._recover(recover_to)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        try:
            self.click_button_on_dialog(id='Save')
        except ElementNotInteractableException:
            self.log.info("Dialog not Present")
        finally:
            if self.check_if_button_exists("Yes"):
                self.click_yes_button()
            _jobid = self.__admin_console.get_jobid_from_popup()
            return _jobid


class DB2RestorePanel(RModalDialog):
    """Class to represent the restore panel for DB2 database"""

    def __init__(self, admin_console):
        super(DB2RestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console

    @WebAction()
    def _redirect(self, redirect_all_tablespace_path=None, redirect_tablespace_path=None,
                  redirect_storage_group_path=None):
        """Method to enter redirect options

        Args:
            redirect_all_tablespace_path    (str)   : Redirect all tablespace path
                default: None
            redirect_tablespace_path        (dict)  : Dictionary with tablespace name and path
                default: None
            redirect_storage_group_path     (dict)   : Redirects storage group name and path
                default: None
        """
        self.click_redirect_options()
        if redirect_all_tablespace_path:
            self.enable_disable_toggle(id="redirectTableSpaces", enable=True)
            self.__admin_console.fill_form_by_name('redirectAllCB', redirect_all_tablespace_path)
        if redirect_tablespace_path:
            self.enable_disable_toggle(id="redirectTableSpaces", enable=True)
            if isinstance(redirect_tablespace_path, dict):
                self.__admin_console.select_radio(id="individualTSCB", value="INDIVIDUAL")
                for tablespace_name, redirect_path in redirect_tablespace_path.items():
                    xpath = "//button[@aria-label='Collapse all']"
                    self.__admin_console.click_by_xpath(xpath)
                    self.click_button_on_dialog(id="edit-mapping")
                    xpath = f"//input[contains(@id, '{tablespace_name}')]"
                    self.__admin_console.fill_form_by_xpath(xpath, redirect_path)
                    self.click_button_on_dialog(id="save-mapping")
                    self.__admin_console.wait_for_completion()
            else:
                raise CVWebAutomationException("Invalid argument passed for redirect_tablespace_path.")

        if redirect_storage_group_path:
            self.expand_accordion("Storage groups")
            if isinstance(redirect_storage_group_path, dict):
                for storage_group_name, redirect_path in redirect_storage_group_path.items():
                    xpath = f"//*[@aria-label='{storage_group_name}']//ancestor::tr//button"
                    elem = self.__admin_console.driver.find_element(By.XPATH, xpath)
                    self.__admin_console.scroll_into_view_using_web_element(elem)
                    elem.click()

                    parent_id = 'dataFilesGrid_' + storage_group_name

                    self.click_button_on_dialog(id="edit-mapping")
                    self.__admin_console.wait_for_completion()

                    self.__admin_console.fill_form_by_xpath(f"//div[contains(@id, '{parent_id}')]//input",
                                                            redirect_path)
                    self.__admin_console.wait_for_completion()

                    self.click_button_on_dialog(id="save-mapping")
                    self.__admin_console.wait_for_completion()

                    elem = self.__admin_console.driver.find_element(By.XPATH, xpath)
                    elem.click()
            else:
                raise CVWebAutomationException("Invalid argument passed for redirect_storage_group_path.")

        self.__admin_console.wait_for_completion()
        self.click_save_button()

    @PageService()
    def in_place_restore(self, endlogs=False, recover=False, notify=False, deselect_roll_forward=False, redirect=False,
                         redirect_all_tablespace_path=None, redirect_tablespace_path=None, redirect_sto_grp_path=None):
        """
        Submits inplace restore for DB2 database
        Args:
            endlogs               (bool)             -- To roll-forward database till end of logs
                - default: True

            recover               (bool)             -- To perform recover operation or not
                - default: False

            notify                (bool)             -- to enable notification by enable


            deselect_roll_forward (bool)             -- to disable roll forward during restore
                - default : False

            redirect              (bool)             -- To redirect tablespaces to new path

            redirect_all_tablespace_path    (str)   : Redirect all tablespace path
                - default: None
            redirect_tablespace_path        (dict)  : Dictionary with tablespace name and path
                default: None
            redirect_sto_grp_path           (dict)  : Redirects storage group name and path
                default: None
        Returns:
             restore job id on successful restore submission
        """
        self.select_radio_by_id("inPlaceRestore")
        if recover:
            self.select_checkbox("recoverDatabase")

        if deselect_roll_forward:
            self.deselect_checkbox("rollFWSelect")

        if redirect:
            self._redirect(redirect_all_tablespace_path=redirect_all_tablespace_path,
                           redirect_tablespace_path=redirect_tablespace_path,
                           redirect_storage_group_path=redirect_sto_grp_path)

        if endlogs:
            self.select_dropdown_values(values=['To end of the logs'],
                                        drop_down_id='rollFwdToType')
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()

        self.click_submit()
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def out_of_place_restore(self, destination_client, destination_instance, destination_db, target_db_path,
                             rollforward=True, endlogs=False, redirect=False,
                             redirect_all_tablespace_path=None, redirect_tablespace_path=None,
                             redirect_sto_grp_path=None, notify=False):
        """
        submits out of place restore for DB2 database

        Args:
            destination_client              (str)   : Destination client to restore data to
            destination_instance            (str)   : Destination instance to restore data to
            destination_db                  (str)   : Destination database to restore data to
            target_db_path                  (str)   : Destination path to restore database to
            rollforward                     (bool)  : Rollforward database or not
                - default: True
            endlogs                         (bool)  : Rollforward to end of logs or not
                - default: True
            redirect                        (bool)  : Redirect or not
                - default: False
            redirect_all_tablespace_path    (str)   : Redirect all tablespace path
                - default: None
            redirect_tablespace_path        (dict)  : Dictionary with tablespace name and path
                default: None
            redirect_sto_grp_path           (dict)  : Redirects storage group name and path
                default: None
            notify                          (bool)  : to enable notification by enable

        Returns:
             restore job id on successful restore submission
        """
        self.select_radio_by_id("outOfPlaceRestore")
        self.select_dropdown_values(values=[destination_client], drop_down_id='destinationServer',
                                    partial_selection=True)
        self.select_dropdown_values(values=[destination_instance], drop_down_id='destinationInstance')
        self.fill_text_in_field('tgtDatabaseName', destination_db)
        self.fill_text_in_field('tgtDatabasePath', target_db_path)
        if rollforward:
            self.select_checkbox("rollFWSelect")
            if endlogs:
                self.select_dropdown_values(values=['To end of the logs'],
                                            drop_down_id='rollFwdToType')
        else:
            self.deselect_checkbox("rollFWSelect")
        if redirect:
            self._redirect(redirect_all_tablespace_path=redirect_all_tablespace_path,
                           redirect_tablespace_path=redirect_tablespace_path,
                           redirect_storage_group_path=redirect_sto_grp_path)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class MySQLRestorePanel(RModalDialog):
    """Class to represent the restore panel for MySQL"""

    def __init__(self, admin_console):
        super(MySQLRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def in_place_restore(self, data_restore=True, log_restore=True,
                         staging_location=None, notify_job_completion=False, is_cloud_db=False):
        """Submits Restore in place job

        Args:
            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            staging_location  (str): Location of data agent job details.
                                    Default value is already filled
                default: None
            notify_job_completion (Boolean): Notify on job completion by email
                default: False
            is_cloud_db (Boolean): Checks whether the sql instance is cloudDB or not
                default: False

        Returns:
            job id  (int): job id of restore job

        """
        self.select_radio_by_id("inPlaceRestore")
        if not is_cloud_db:
            if not data_restore:
                self.deselect_checkbox("data")
            else:
                self.select_checkbox("data")
            if not log_restore:
                self.deselect_checkbox("log")
            else:
                self.select_checkbox("log")
            if staging_location:
                self.fill_text_in_field("StagingLocation-label", staging_location)

        if notify_job_completion:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid

    @PageService()
    def out_of_place_restore(self, destination_client, destination_instance, data_restore=True, log_restore=True,
                             staging_location=None, notify_job_completion=False, is_cloud_db=False,
                             destination_folder=None, cross_instance_restore=True):
        """Submits out of place restore of MySQL database

        Args:

            destination_client      (str): Destination client name

            destination_instance    (str): Destination instance name

            data_restore (Boolean):  Checks data restore option
                default: True
            log_restore (Boolean):  Checks log restore option
                default: True
            staging_location  (str): Location of data agent job details.
                                    Default value is already filled
                default: None
            notify_job_completion (Boolean): Notify on job completion by email
                default: False
            is_cloud_db (Boolean): Checks whether the sql instance is cloudDB or not
                default: False
            cross_instance_restore (Boolean): Checks whether the restore type is cross machine
                default: True
            destination_folder (str): Restore location

        Returns:
            restore job id on successful restore submission

        """
        self.select_radio_by_id('outOfPlaceRestore')
        if not is_cloud_db:
            if cross_instance_restore:
                self._dropdown.select_drop_down_values(
                    values=['Cross instance restore'], drop_down_id='restoreType')
                self._dropdown.select_drop_down_values(
                    values=[destination_client], drop_down_id='destinationServer')
                self._dropdown.select_drop_down_values(
                    values=[destination_instance], drop_down_id='destinationInstance')
                if staging_location:
                    self.click_button_on_dialog(aria_label='Browse')
                    self.browse_path(staging_location)
            else:
                self._dropdown.select_drop_down_values(
                    values=['Restore to disk'], drop_down_id='restoreType')
                self._dropdown.select_drop_down_values(
                    values=[destination_client], drop_down_id='destinationServer')
                self.fill_text_in_field('destinationFolder', destination_folder)
                if destination_folder:
                    self.click_button_on_dialog(aria_label='Browse')
                    self.browse_path(destination_folder)
            if not data_restore:
                self.deselect_checkbox("data")
            else:
                self.select_checkbox("data")
            if not log_restore:
                self.deselect_checkbox("log")
            else:
                self.select_checkbox("log")
        if notify_job_completion:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class RDSRestorePanel(RModalDialog):
    """Class to represent the restore panel for Amazon RDS database"""

    def __init__(self, admin_console):
        super(RDSRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = ModalDialog(self.__admin_console)

    @PageService()
    def restore(self, database_identifier, notify=False):
        """Submits basic restore of RDS without any advanced options
        Args:
            database_identifier (str)   -- The identifier to be set during restore

            notify              (bool)  -- to enable notification by enable

        """
        self.fill_text_in_field('dbIdentifier', database_identifier)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class SybaseRestorePanel(RModalDialog):
    """Class to represent the restore panel for Sybase"""

    def __init__(self, admin_console):
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = ModalDialog(self.__admin_console)
        self._panel_dropdown = DropDown(self.__admin_console)
        self.redirect_options_dict = None

    @WebAction()
    def mark_recover_databases(self, select=True):
        """
        Marks recover databases option if enabled
        Args:
            select  (bool)  :   True if recover databases should be enabled
                default:    True
        """
        if select:
            self._admin_console.checkbox_select("recoverDatabases")
        else:
            self.__admin_console.checkbox_deselect("recoverDatabases")

    @WebAction()
    def _click_device(self, database_name, device_name):
        """
        Clicks on device of a particular database in redirect restore
        Args:
            database_name   (str)   :   Name of the database of the device
            device_name     (str)   :   Name of the device to be selected
                    default: True
        """
        xpath = f"//b[contains(text(),'{database_name}')]/../following-sibling::" \
                f"ul/li/a[normalize-space()='{device_name}']"
        self.__admin_console.driver.find_element(By.XPATH, xpath).click()

    def _construct_redirect_dict(self, database_names, prefix, path):
        """
        Generates redirect options dictionary
        Args:
            database_names  (list)  :   Names of the source databases
            prefix          (str)   :   Prefix for dict values
            path            (str)   :   Physical path to redirect to
        """
        self.redirect_options_dict = {}
        for database_name in database_names:
            self.redirect_options_dict[database_name] = {
                f"data_{database_name}": {
                    "target_db": f"{prefix}{database_name}",
                    "device_name": f"{prefix}data_{database_name}",
                    "physical_path": f"{path}{prefix}data_{database_name}.dat"
                },
                f"log_{database_name}": {
                    "target_db": f"{prefix}{database_name}",
                    "device_name": f"{prefix}log_{database_name}",
                    "physical_path": f"{path}{prefix}log_{database_name}.dat"
                }
            }

    @PageService()
    def in_place_restore(self, notify_job_completion=False, recover_databases=True,
                         redirect_options=None, database_names=None, path=None):
        """
        Submits Restore in place job for Sybase
            Args:
                notify_job_completion: True if user to be notified by mail on job completion
                    default: False
                recover_databases: True if recover databases is to be enabled
                    default: True
                redirect_options: Dictionary containing redirect options for each device
                                    in the format
                                    {database1:
                                        device1:{
                                            target_db:"target db",
                                            device_name:"device_name",
                                            physical_path:"physical/path/",
                                            device_size:123456
                                        }
                                    }
                database_names(list):  Names of the databases in case databases need to be
                                    redirected during restore for redirect_options dict
                                     construction in house
                path                :   Path to redirect database to including separator
            Returns:
                job id  (int): job id of restore job
        """
        self.select_radio_by_id("inPlaceRestore")
        self.mark_recover_databases(select=recover_databases)
        if redirect_options or database_names:
            self.__admin_console.expand_accordion(
                self.__admin_console.props['header.redirectOptions'])
            if database_names:
                self._construct_redirect_dict(database_names, "inplace_", path)
                redirect_options = self.redirect_options_dict
            else:
                self.redirect_options_dict = redirect_options
            for database, devices in redirect_options.items():
                for device, properties in devices.items():
                    self._click_device(database, device)
                    if properties.get("target_db"):
                        self.__admin_console.fill_form_by_name('databaseName',
                                                               properties['target_db'])
                    if properties.get("device_name"):
                        self.__admin_console.fill_form_by_name('logName',
                                                               properties['device_name'])
                    if properties.get('physical_path'):
                        self.__admin_console.fill_form_by_name('physicalPath',
                                                               properties['physical_path'])
                    if properties.get("device_size"):
                        self.__admin_console.fill_form_by_name('deviceSize',
                                                               properties['device_size'])
        if notify_job_completion:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid

    @PageService()
    def out_of_place_restore(self, destination_client, destination_instance,
                             notify_job_completion=False, recover_databases=True,
                             redirect_options=None, database_names=None, path=None):
        """
        Submits Restore in place job for Sybase
            Args:
                destination_client: Destination client to restore data to
                destination_instance: Destination instance to restore data to
                notify_job_completion: True if user to be notified by mail on job completion
                    default: False
                recover_databases: True if recover databases is to be enabled
                    default: True
                redirect_options: Dictionary containing redirect options for each device
                                    in the format
                                    {database1:
                                        device1:{
                                            target_db:"target db",
                                            device_name:"device_name",
                                            physical_path:"physical/path/",
                                            device_size:123456
                                        }
                                    }
                database_names(list):  Names of the databases in case databases need to be
                                    redirected during restore for redirect_options dict
                                     construction in house
                path                :   Path to redirect database to including separator
            Returns:
                job id  (int): job id of restore job
        """
        self.access_tab("Out of place")
        self._panel_dropdown.select_drop_down_values(values=[destination_client],
                                                     drop_down_id='destinationclient',
                                                     partial_selection=True)
        self._panel_dropdown.select_drop_down_values(values=[destination_instance],
                                                     drop_down_id='destinationDatabase')
        self.mark_recover_databases(select=recover_databases)
        if redirect_options or database_names:
            self.__admin_console.expand_accordion(
                self.__admin_console.props['header.redirectOptions'])
            if database_names:
                self._construct_redirect_dict(database_names, "outofplace_", path)
                redirect_options = self.redirect_options_dict
            else:
                self.redirect_options_dict = redirect_options
            for database, devices in redirect_options.items():
                for device, properties in devices.items():
                    self._click_device(database, device)
                    if properties.get("target_db"):
                        self.__admin_console.fill_form_by_name('databaseName',
                                                               properties['target_db'])
                    if properties.get("device_name"):
                        self.__admin_console.fill_form_by_name('logName',
                                                               properties['device_name'])
                    if properties.get('physical_path'):
                        self.__admin_console.fill_form_by_name('physicalPath',
                                                               properties['physical_path'])
                    if properties.get("device_size"):
                        self.__admin_console.fill_form_by_name('deviceSize',
                                                               properties['device_size'])
        if notify_job_completion:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class InformixRestorePanel(RModalDialog):
    """Class to represent the restore panel for Informix database"""

    def __init__(self, admin_console):
        super(InformixRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.props = self.__admin_console.props

    @WebAction()
    def __get_value(self, elem_id):
        """
        Get element value by id for any element from restore options
        Returns:
            Value of the element from command center restore options
        """
        return self.__admin_console.driver.find_element(
            By.XPATH, "//div[@class='date-input-wrapper']/span/input").get_attribute("value")

    @PageService()
    def informix_restore(self, restore_type=None, destination_client=None,
                         destination_instance=None, physical=True, logical=True,
                         config_files=False, restore_time=None, tolog=0, notify=False):
        """
        Submits inplace or out of place restore job for Informix
            Args:
                restore_type        (str) -- Restore mode with no space between words.Default = None
                    Accepted values       = 'Entireinstance' or 'Wholesystem'
                destination_client  (str) -- Name of destination client,
                                             required for out of place restore only
                destination_instance(str) -- Name of destination instance,
                                             required for out of place restore only
                physical            (bool)-- True to perform physical restore. Default = True
                logical             (bool)-- True to perform logical restore. Default = True
                config_files        (bool)-- True to perform config files restore. Default = False
                restore_time        (str) -- Actual to-time to perform point-in-time restore
                tolog               (int) -- Last log number to be restored for point-in-log restore
                notify              (bool)-- to enable notification by enable
            Returns:
                job id  (int): job id of restore job
        """
        if destination_client and destination_instance is not None:
            self.select_radio_by_id('outOfPlaceRestore')
            self.select_dropdown_values(
                values=[destination_client], drop_down_id='destinationServer')
            self.select_dropdown_values(
                values=[destination_instance], drop_down_id='destinationInstance')
        else:
            self.select_radio_by_id("inPlaceRestore")
        restoretypes = {
            'entireinstance': 'label.entireInstance',
            'wholesystem': 'label.wholeSystem'
        }
        if restore_type is not None:
            self.select_dropdown_values(
                values=[self.props[restoretypes[restore_type.lower()]]],
                drop_down_id='informixRestoreMode')
        if not physical:
            self.deselect_checkbox("physical")
            if not logical:
                if not config_files:
                    raise Exception("Select the restore content correctly")
        if not logical:
            self.deselect_checkbox("logical")
        if config_files:
            self.select_checkbox("restoreConfigFile")
        if tolog > 0:
            self.select_dropdown_values(values=['Up to logical log'], drop_down_id='recoverToType')
            self.fill_text_in_field('logicalLogNumber', tolog)
        elif restore_time is not None:
            self.select_dropdown_values(values=['Point in time'], drop_down_id='recoverToType')
            pit_now = self.__get_value("dateTimeValue")
            pit_now = datetime.strptime(pit_now, '%Y-%m-%d %H:%M:%S %p').strftime("%m/%d/%Y %H:%M %p")
            if pit_now != restore_time:
                if int(pit_now.split(":")[-1].split(" ")[0]) - int(restore_time.split(":")[-1].split(" ")[0]) > 1:
                    raise CVWebAutomationException("PIT %(p)s and browse-restore time %(r)s "
                                                   "differ" % {'p': pit_now, 'r': restore_time})
        else:
            self.select_dropdown_values(values=['Most recent backup'], drop_down_id='recoverToType')
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit(False)
        return self.__admin_console.get_jobid_from_popup()


class CosmosDBSQLRestorePanel(ModalPanel):
    """Class to represent restore panel for CosmosDB SQL API"""

    def __init__(self, admin_console):
        super(CosmosDBSQLRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = RModalDialog(self.__admin_console)

    @PageService()
    def disable_write_throughput(self):
        """Disables the adjust write throughput toggle"""
        self.__dialog.disable_toggle(toggle_element_id="throughput")

    @PageService()
    def select_overwrite(self):
        """Enables overwrites destination containers option"""
        self.__dialog.enable_toggle(toggle_element_id="overwrite")

    @PageService()
    def in_place_restore(self, adjust_throughput=0, streams=2, overwrite=True, notify=False):
        """Submits restore to same cloud account and restores containers with same name
        Args:
            adjust_throughput  (int)  --  The value to be set as adjust throughput

            streams     (str)   --  The number of streams for restore

            overwrite   (bool)  --  True to enable overwrite containers
                                    False to not overwrite containers

            notify  (bool) - to enable notification by enable
        Returns:
            int     --  The jobid of the restore
        """
        if adjust_throughput != 0:
            self.__admin_console.fill_form_by_id('throughput', adjust_throughput)
        else:
            self.disable_write_throughput()
        if streams != 2:
            self.__admin_console.fill_form_by_id('noOfStreams', streams)
        if overwrite:
            self.select_overwrite()
        if notify:
            self._enable_notify_via_email()
        else:
            self._disable_notify_via_email()
        self.__dialog.click_submit()
        if overwrite:
            self.__dialog.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class CosmosDBCASSANDRARestorePanel(RModalPanel):
    """Class to represent restore panel for CosmosDB Cassandra API"""

    def __init__(self, admin_console):
        super(CosmosDBCASSANDRARestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console
        self.__dialog = RModalDialog(admin_console)
        self.__dropdown = RDropDown(admin_console)

    @PageService()
    def redirect_all_tables(self):
        """redirect all tables"""
        self.__dialog.enable_toggle(toggle_element_id="setDestCosmosDbAccount")

    @PageService()
    def disable_write_throughput(self):
        """Disables the adjust write throughput toggle"""
        self.__dialog.disable_toggle(toggle_element_id="throughput")

    @PageService()
    def select_overwrite(self):
        """Enables overwrites destination containers option"""
        self.__dialog.enable_toggle(toggle_element_id="overwrite")

    @PageService()
    def in_place_restore(self, adjust_throughput=0, overwrite=True):
        """Submits restore to same cloud account and restores containers with same name
        Args:
            adjust_throughput  (int)  --  The value to be set as adjust throughput
            overwrite   (bool)  --  True to enable overwrite containers
                                    False to not overwrite containers
        Returns:
            int     --  The jobid of the restore
        """
        if adjust_throughput != 0:
            self.__dialog.fill_input_by_xpath(
                text=adjust_throughput, element_id="throughputField")
        else:
            self.disable_write_throughput()

        if overwrite:
            self.select_overwrite()

        self.__dialog.click_submit()
        self.__dialog.click_yes_button()

        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid

    @PageService()
    def out_of_place_restore(
            self,
            adjust_throughput=0,
            overwrite=True,
            dest_account=None,
            dest_keyspace=None,
            dest_table=None):
        """Submits restore to same cloud account and restores containers with same name
        Args:
            adjust_throughput  (int)  --  The value to be set as adjust throughput
            overwrite   (bool)  --  True to enable overwrite containers
                                    False to not overwrite containers
            dest_account (str)  --  Destinatino account name
            dest_keyspace (str) --  Destination keyspace name
            dest_table    (str) --  Destination table name
        Returns:
            int     --  The jobid of the restore
        """
        if dest_account:
            self.__dropdown.select_drop_down_values(
                values=[dest_account], drop_down_id='destinationServer')
        if adjust_throughput != 0:
            self.__dialog.fill_input_by_xpath(
                text=adjust_throughput, element_id="throughputField")
        else:
            self.disable_write_throughput()
        if overwrite:
            self.select_overwrite()

        # get destination input Id for first keyspace/table row
        input_id = Rtable(
            admin_console=self.__admin_console,
            id="restoreContent").get_column_data(
            column_name="Source")[0]
        if dest_keyspace is not None:
            if dest_table is not None:
                destpath = dest_keyspace + "/" + dest_table
                self.__dialog.fill_input_by_xpath(
                    text=destpath, element_id=input_id)
            else:
                self.__dialog.fill_input_by_xpath(
                    text=dest_keyspace, element_id=input_id)

        self.__dialog.click_submit()
        self.__dialog.click_yes_button()
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid


class SQLRestorePanel(RModalDialog):
    """ Class to represent the restore panels for SQL Server"""

    def __init__(self, admin_console):
        super(SQLRestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def in_place_restore(self, notify=False):
        """ Submits restore in place job for SQL Server

            Args:
                notify  (bool) - to enable notification by enable

            Returns:
                job id (str)   -   job id of restore job
        """
        self.select_radio_by_id("inPlaceRestore")
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()

        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def restore(self, destination_instance, notify=False, **kwargs):
        """ Submits a restore for SQL Server cloud DB

            Args:
                destination_instance (str/Optional) -- Destination to restore SQL DB to. Default is the source instance

                notify  (bool) - to enable notification by enable

            Keyword Args:
                access_node (str)   --      Name of the access node for restore staging purposes

                staging_path (str)  --      Folder path on access node to stage database for restore

                destination_database_name (str) --  Name to restore database as

            Returns:
                job id (str)   -   job id of restore job
        """
        self.access_tab("Restore")
        self._dropdown.select_drop_down_values(drop_down_id='destinationInstance', values=[destination_instance])

        if 'access_node' in kwargs:
            access_node = kwargs.get('access_node')
            self._dropdown.select_drop_down_values(drop_down_id='proxyClient', values=[access_node])
        if 'staging_path' in kwargs:
            staging_path = kwargs.get('staging_path')
            self.__admin_console.fill_form_by_id("stagingPath", staging_path)
        if 'destination_database_name' in kwargs:
            destination_database_name = kwargs.get('destination_database_name')
            self.__admin_console.fill_form_by_id("destinationDatabase", destination_database_name)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()

        return self.__admin_console.get_jobid_from_popup()


class SAPHANARestorePanel(RModalDialog):
    """Class to represent the restore panel for SAP HANA"""

    def __init__(self, admin_console):
        super(SAPHANARestorePanel, self).__init__(admin_console)
        self.__admin_console = admin_console

    @PageService()
    def __set_point_in_time(self, point_in_time=None):
        """Sets Point in Time for Restore

        Args:
            point_in_time  (str)   -- Point in Time (Apr 30, 2024, 6:12:04 PM)
                default: None
        """
        self.select_dropdown_values(values=["Point in time"], drop_down_id="recoverToType")
        calendar = CalendarView(self.__admin_console)
        self.click_button_on_dialog(aria_label='Open calendar')
        time_obj = datetime.strptime(point_in_time, "%b %d, %Y, %I:%M:%S %p")
        year, month, day, hour, minute, second = (int(i) if i.isnumeric() else i.lower() for i in
                                                  time_obj.strftime("%Y %B %d %H %M %S").split())
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
    def __set_advanced_options(self, advanced_options=None):
        """Sets Advanced Options for Restore

        Args:
            advanced_options (dict)     --  advanced option
                { "copyPrecedence" : str, "mediaAgent" : str, InitializeLogArea : bool}
                default: None
        """
        self.click_element(xpath="//div[@id='advancedOptions']")
        if "copyPrecedence" in advanced_options:
            self.select_dropdown_values("copyPrecedence", [advanced_options["copyPrecedence"]])
        if "mediaAgent" in advanced_options:
            self.select_dropdown_values("mediaAgent", [advanced_options["mediaAgent"]])
        if "InitializeLogArea" in advanced_options and advanced_options["InitializeLogArea"]:
            self.select_checkbox(checkbox_id='InitializeLogArea', checkbox_label='Initialize log area')
        if "proxyClient" in advanced_options:
            self.select_dropdown_values("proxyClient", [advanced_options["proxyClient"]])
        if "hardwareRevert" in advanced_options and advanced_options["hardwareRevert"]:
            self.enable_toggle("hardwareRevert")

    @PageService()
    def in_place_restore(self, no_of_streams=2, destination_database=None, backup_prefix=None, internal_backup_id=None, point_in_time=None,
                         advanced_options=None, notify=False):
        """Submits a in place restore of SAP Hana database

        Args:

            no_of_streams       (int)   --  Number of restore streams to be used
                default: 2

            destination_database(str)   --  Name of destination database for restore
                default: None

            backup_prefix       (str)   --  Backups prefix string
                default: None

            internal_backup_id  (str)   --  Internal backup ID
                default: None

            point_in_time       (str)   --  Point in Time (Apr 30, 2024, 6:12:04 PM)
                default: None

            advanced_options (dict)     --  advanced option
                { "copyPrecedence" : str, "mediaAgent" : str, InitializeLogArea : bool
                    "proxyClient" : str, "hardwareRevert" : bool
                }
                default: None

            notify              (bool)  -- to enable notification by enable

        Returns:
            restore job id on succesful restore submission

        """
        self.select_radio_by_id('inPlaceRestore')
        if no_of_streams != 2:
            self.__admin_console.fill_form_by_id("noOfStreams", no_of_streams)
        if destination_database:
            self.select_dropdown_values(values=[destination_database], drop_down_id="destinationDatabase")
        if backup_prefix:
            self.select_dropdown_values(values=["Using backup prefix"], drop_down_id="recoverToType")
            self.__admin_console.fill_form_by_id("backupPrefixValue", backup_prefix)
        elif internal_backup_id:
            self.select_dropdown_values(values=["Using internal backup id"], drop_down_id="recoverToType")
            self.__admin_console.fill_form_by_id("backupIdValue", internal_backup_id)
        elif point_in_time:
            self.__set_point_in_time(point_in_time)
        else:
            self.select_dropdown_values(values=["Most recent state"], drop_down_id="recoverToType")
        if advanced_options:
            self.__set_advanced_options(advanced_options)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        return self.__admin_console.get_jobid_from_popup()

    @PageService()
    def out_of_place_restore(self, destination_client, destination_instance, destination_database,
                             data_directory=None, no_of_streams=2, backup_prefix=None,
                             internal_backup_id=None, point_in_time=None, advanced_options=None, notify=False):
        """Submits an out of place restore of SAP Hana database

                Args:
                    destination_client  (str)   --  Name of destination client for restore

                    destination_instance(str)   --  Name of destination instance for restore

                    destination_database(str)   --  Name of destination database for restore

                    data_directory      (str)   --  Data directory for restore
                        default: None

                    no_of_streams       (int)   --  Number of restore streams to be used
                        default: 2

                    backup_prefix       (str)   --  Backups prefix string
                        default: None

                    internal_backup_id  (str)   --  Internal backup ID
                        default: None

                    point_in_time       (str)   --  Point in Time (Apr 30, 2024, 6:12:04 PM)
                        default: None

                    advanced_options (dict)     --  advanced option
                        { "copyPrecedence" : str, "mediaAgent" : str, InitializeLogArea : bool
                            "proxyClient" : str, "hardwareRevert" : bool}
                        default: None

                    notify              (bool)  -- to enable notification by enable
                        default: False

                Returns:
                    restore job id on succesful restore submission

                """
        self.__admin_console.select_radio('outOfPlaceRestore')
        self.select_dropdown_values("destinationServer", [destination_client])
        self.select_dropdown_values("destinationInstance", [destination_instance])
        self.select_dropdown_values("databaseId", [destination_database])

        if data_directory:
            self.__admin_console.fill_form_by_id("dataDir", data_directory)
        if no_of_streams != 2:
            self.__admin_console.fill_form_by_id("noOfStreams", no_of_streams)
        if backup_prefix:
            self.select_dropdown_values(values=["Using backup prefix"], drop_down_id="recoverToType")
            self.__admin_console.fill_form_by_id("backupPrefixValue", backup_prefix)
        elif internal_backup_id:
            self.select_dropdown_values(values=["Using internal backup id"], drop_down_id="recoverToType")
            self.__admin_console.fill_form_by_id("backupIdValue", internal_backup_id)
        elif point_in_time:
            self.__set_point_in_time(point_in_time)
        if advanced_options:
            self.__set_advanced_options(advanced_options)
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        return self.__admin_console.get_jobid_from_popup()


class SpannerRestorePanel(RModalDialog):
    """ Class to represent the restore panels for SQL Server"""

    def __init__(self, admin_console):
        super(SpannerRestorePanel, self).__init__(admin_console)
        self._admin_console = admin_console

    @PageService()
    def in_place_restore(self, notify=False):
        """ Submits restore in place job for SQL Server

            Args:
                notify  (bool) : to enable notification by enable

            Returns:
                job id (str)   -   job id of restore job
        """
        self.select_radio_by_id("inPlaceRestore")
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()

        return self._admin_console.get_jobid_from_popup()
    
class SAPOracleRestorePanel(RModalDialog):
    """Class to represent the restore panel for SAP Oracle database"""

    def __init__(self, admin_console):
        super(SAPOracleRestorePanel, self).__init__(admin_console)
        self.log = logger.get_log()
        self.__admin_console = admin_console

    @WebAction()
    def _mark_open_db(self, open_db=True):
        """
        Marks recover databases option if enabled
        Args:
            select  (bool)  :   True if recover databases should be enabled
                default:    True
        """
        if open_db:
            self.select_checkbox(checkbox_label="Open DB")
        else:
            self.deselect_checkbox(checkbox_label="Open DB")
    
    
    @WebAction()
    def _recover(self, recover_to):
        """Method to enter recover options

        Args:
            recover_to          (str/int):"most recent state"/"current time"/
            Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
        """
        if recover_to:
            recover_to_map = {"most recent state": "Most recent state", "current time": "Current time"}
            if recover_to.lower() in recover_to_map:
                self.select_dropdown_values(values=[recover_to_map[recover_to.lower()]],
                                            drop_down_id='recoverToType')
            else:
                self.select_dropdown_values(values=['Point in time'],
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
    def in_place_restore(self, recover_to, no_of_streams=2, open_db=True, notify=False):
        """
        submits inplace restore for SAP Oracle database

        Args:
            

            recover_to          (str/int):"most recent state"/"current time"/SCN number
                                            /Point in time in format "%m/%d/%Y %H:%M:%S" (eg. 12/31/2020 23:59:59)
                default: None
            open_db             (bool)  : to open database after restore

            notify              (bool)  : to enable notification by enable

        Returns:
             restore job id on successful restore submission
        """
        self.select_radio_by_id("inPlaceRestore")
        if no_of_streams != 2:
            self.__admin_console.fill_form_by_id("noOfStreams", no_of_streams)

        self.deselect_checkbox("controlfile") 
        self._recover(recover_to)
        self._mark_open_db(open_db)
        
        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_submit()
        self.click_yes_button()
        
        _jobid = self.__admin_console.get_jobid_from_popup()
        return _jobid

    @PageService()
    def outof_place_restore(self, destination_client, destination_instance,
                            recover_to, database_copy=True,
                            restore_to_disk=False, job_id=None,
                            destination_folder=None, no_of_streams=2,
                            open_db=True, notify=False):
        """
        submits out of place restore for SAP Oracle instance

            Args:
            destination_client  (str)   :   Destination client to restore data to
            destination_instance(str)   :   Destination instance to restore data to

            database_copy      (bool)  :   True if Database copy option must be enabled
                default: True
            restore_to_disk    bool)  :   True if Restore to disk option must be enabled
                default: False
            job_id             (int)  :   pass the backup jobid for restore to disk
                default: None
            destination_folder (str)  :   Path on the destination client where restore to disk job
                default: None                       need to be run

        Returns:
            restore job id on successful restore submission
        """
        self.select_radio_by_id("outOfPlaceRestore")
        if no_of_streams != 2:
            self.__admin_console.fill_form_by_id("noOfStreams", no_of_streams)
        self._recover(recover_to)
        self._mark_open_db(open_db)
        if database_copy:
            self.select_dropdown_values(values=['Database copy'],
                                        drop_down_id='restoreType')
            self.select_dropdown_values(values=[destination_client],
                                        drop_down_id='destinationServer',
                                        partial_selection=True)
            self.select_dropdown_values(values=[destination_instance],
                                        drop_down_id='destinationInstance')
        else:
            self.select_drop_down_values(
                values=['Restore to disk'], drop_down_id='restoreType')
            self._dropdown.select_drop_down_values(
                values=[destination_client], drop_down_id='destinationServer')
            self._dropdown.select_drop_down_values(
                values=[job_id], drop_down_id='Select job9(s)')
            self.fill_text_in_field('destinationFolder', destination_folder)
            if destination_folder:
                self.click_button_on_dialog(aria_label='Browse')
                self.browse_path(destination_folder)

        if notify:
            self.enable_notify_via_email()
        else:
            self.disable_notify_via_email()
        self.click_button_on_dialog(id='Save')
        if self.check_if_button_exists("Yes"):
            self.click_yes_button()
        try:
            self.click_button_on_dialog(id='Save')
        except ElementNotInteractableException:
            self.log.info("Dialog not Present")
        finally:
            _jobid = self.__admin_console.get_jobid_from_popup()
            return _jobid
