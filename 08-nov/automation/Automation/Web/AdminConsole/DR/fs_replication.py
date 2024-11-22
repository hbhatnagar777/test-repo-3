# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module is used for configure a File system Replication Group
"""
from time import sleep
from Web.AdminConsole.Components.panel import DropDown, ModalPanel
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.DR.recovery_targets import RecoveryPointStore
from Web.Common.page_object import WebAction, PageService
from Web.Common.exceptions import CVWebAutomationException


class ConfigureBLR:
    """Class for configuring a block level replication(BLR)"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self.__admin_console = admin_console
        self.__drop_down = DropDown(admin_console)
        self.__table = Table(admin_console)
        self.__dialog = ModalDialog(admin_console)
        self.__modal_panel = ModalPanel(admin_console)
        self.__rpstore = RecoveryPointStore(admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @PageService()
    def __select_volume(self, source_volume, destination_volume):
        """
        Selects the volume pairs from the source and destination clients respectively
        Args:
            source_volume       (str): source replication volume
            destination_volume  (str): destination replication volume
        """
        self.__admin_console.select_hyperlink(self.__label["label.addVolume"])
        self.__table.select_rows([source_volume])
        self.__modal_panel.submit()

        self.__admin_console.select_hyperlink(self.__label['label.browse'])
        self.__table.select_rows([destination_volume])
        self.__modal_panel.submit()

        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def _set_clients(self, source_client, destination_client):
        """
        Set the clients which are marked as source and destination for the replication group
        Args:
            source_client       (str): Name of the source client
            destination_client  (str): Name of the destination client
        """
        self.__drop_down.select_drop_down_values(
            values=[source_client],
            drop_down_id="liveSyncIOConfigurePairsModal_isteven-multi-select_#0707")
        self.__drop_down.select_drop_down_values(
            values=[destination_client],
            drop_down_id="liveSyncIOConfigurePairsModal_isteven-multi-select_#7456")

    @PageService()
    def select_volumes(self, source_volumes, destination_volumes):
        """
        A service to add multiple volume pairs for replication, following the order pair from both lists
        Args:
            source_volumes       (list): List of string values of each source volume
            destination_volumes  (list): List of string values of each destination volume
        """
        if not source_volumes or len(source_volumes) != len(destination_volumes):
            raise CVWebAutomationException('There are incorrect number of source volumes and destination volumes.'
                                           'They must be equal in number')
        for source, destination in zip(source_volumes, destination_volumes):
            self.__select_volume(source, destination)

    @PageService()
    def remove_volume(self, source_volume, destination_volume):
        """Removes the volumes row from the replication pair"""
        self.__table.apply_filter_over_column(self.__label['label.sourceVolume'], source_volume)
        self.__table.apply_filter_over_column(self.__label['label.destinationVolume'], destination_volume)

        self.__table.access_action_item(source_volume, self.__label['label.remove'])

        self.__table.clear_column_filter(self.__label['label.sourceVolume'])
        self.__table.clear_column_filter(self.__label['label.destinationVolume'])

    @PageService()
    def add_block_level_replication(self, source_client, destination_client,
                                    source_volumes, destination_volumes, recovery_type,
                                    rpstore_args=None, interval_args=None, retention_args=None):
        """
        Adds and configures the block level replication pair to the admin console
        Args:
            source_client        (str): Name of the source client
            destination_client   (str): Name of the destination client
            source_volumes      (list): List of volumes on source client
            destination_volumes (list): List of volumes on destination client
            recovery_type        (int): Recovery Type to opt for, 0 for latest recovery, 1 for point in time recoverys
            rpstore_args        (dict): Dictionary of the recovery point store options
                - name            (str): name of the recovery point store
                - media_agent     (str): name of the media agent on which the store will reside on, only for new store
                - max_size        (int): the maximum size of the recovery point store in GB, only for new store
                - path            (str): the path at which the store will be present
                - path_type       (str): the path type as 'Local path' or 'Network path'
                - path_username   (str): the path access username, only for network path
                - path_password   (str): the path access password, only for network path
                - peak_interval  (dict): the intervals at which recovery point store is marked at peak
                                            Must be a dict of keys as days, and values as list of date time ids(0-23)
            interval_args      (dict): Dictionary of recovery point intervals
                - ccrp            (str): Crash consistent recovery points interval '<time> <unit>'
                                            unit -> ('seconds', 'minutes', 'days', 'hours')
                - acrp            (str): Application Consistent recovery points interval '<time> <unit>'
                                            unit -> ('seconds', 'minutes', 'days', 'hours')
            retention_args      (dict): Dictionary of recovery point retention
                - retention            (str): Duration for which a recovery point is retained for
                - merge               (bool): Whether to merge recovery points
                - merge_delay          (str): Merge recovery points older than this interval
                - max_rp_interval      (str): Recovery point max retention interval
                - max_rp_offline       (str): After what time to switch to latest recovery if RPstore is offline
                - off_peak_only       (bool): Whether to prune and merge only on non-peak time
        """
        self._set_clients(source_client, destination_client)
        self.select_volumes(source_volumes, destination_volumes)

        self.__rpstore.select_recovery_type(recovery_type)
        if recovery_type == 1:
            if rpstore_args and rpstore_args.get("media_agent", None) and rpstore_args.get("path", None):
                self.__rpstore.create_recovery_store(**rpstore_args)
            else:
                self.__rpstore.select_store(rpstore_args.get("name"))
            if interval_args:
                self.__rpstore.configure_intervals(**interval_args)
            if retention_args:
                self.__rpstore.configure_retention(**retention_args)

        self.__modal_panel.submit()


class ReplicaCopy:
    """This class is used to configure a replica copy for the Block Level Replication Pair, when the pair is in sync"""
    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole base object
        """
        self.__admin_console = admin_console
        self.__table = Table(admin_console)
        self.__modal_panel = ModalPanel(admin_console)
        self.__dialog = ModalDialog(admin_console)

        self.__admin_console.load_properties(self, unique=True)
        self.__label = self.__admin_console.props[self.__class__.__name__]

    @WebAction()
    def __get_all_recovery_points(self):
        """
        Selects the latest possible recovery point for replica copy.
        The times values are of the format 'number:<timestamp>' which are needed to be converted to integers
        Returns: list of integer timestamps that can be used to comparisons and other functions
        """
        elements = self.__admin_console.driver.find_elements(By.XPATH, "//select[@id='crashConsistentRPTDetailDate"
                                                                      "']//option")
        return [int(element.get_attribute("value").split(":")[-1]) for element in elements]

    @PageService()
    def select_volume(self, volume_name):
        """Selects the volume to create replica copy at"""
        self.__admin_console.select_hyperlink(self.__label['label.browse'])
        self.__admin_console.wait_for_completion()
        self.__table.select_rows([volume_name])
        self.__modal_panel.submit()
        self.__dialog.click_submit()

    @PageService()
    def select_recovery_point(self, recovery_type, rptime=None, get_closest=False):
        """Selects the recovery point on the basis of time sent by user
        Args:
            recovery_type (int): 0 for oldest point in time, 1 for recovery point time
            rptime        (int): epoch timestamp of recovery point
            get_closest  (bool): whether to select closest next timestamp or not
        """
        if recovery_type == 0:
            self.__admin_console.select_value_from_dropdown("recoveryType", "Oldest point in time")
        else:
            self.__admin_console.select_value_from_dropdown("recoveryType", "Recovery point time")
            self.__admin_console.wait_for_completion()
            rptimes = self.__get_all_recovery_points()
            if not rptime:
                rptime = rptimes[-1]
            elif rptime not in rptimes:
                if get_closest:
                    rptime = self.get_closest_rptime(rptime)
                else:
                    raise CVWebAutomationException("The timestamp does not exist in the recovery points")
            self.__admin_console.select_value_from_dropdown(
                "crashConsistentRPTDetailDate", "number:{}".format(rptime), attribute=True)

    @PageService()
    def get_closest_rptime(self, timestamp):
        """Returns the closest timestamp to the rptime provided after the rptime.
         Must be done when the dropdown for rpstore timestamp selection is available
        Args:
            timestamp  (int): timestamp to choose the option near
        Returns: str of value 'number:<timestamp>'
        """
        rptimes = self.__get_all_recovery_points()
        for rptime in rptimes:
            if rptime >= timestamp:
                return rptime

        raise CVWebAutomationException("No future recovery point times found")

    @PageService()
    def submit_replica_job(self, volume_name, recovery_type, rptime=None, get_closest=False):
        """
        Configures the replica copy page and submits it
        Args:
            volume_name     (str): Name of the destination volume
            recovery_type   (int): 0 for oldest point in time, 1 for recovery point time
            rptime          (int): The recovery point time of copy(epoch timestamp)
            get_closest  (bool): whether to select closest next timestamp or not
        """
        self.select_volume(volume_name)
        self.select_recovery_point(recovery_type, rptime, get_closest)
        sleep(10)
        self.__modal_panel.submit(wait_for_load=False)
        return self.__admin_console.get_jobid_from_popup()
