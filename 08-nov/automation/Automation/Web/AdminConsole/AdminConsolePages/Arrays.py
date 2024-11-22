# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the Arrays Page on the AdminConsole.
Below are the class defined along with the functions.


    Arrays() :  -- To add snap arrays along with editing snap configurations

                    add_arrays()            -- Creates an array if a snap plan already exists

                    action_delete_array()   -- Deletes the array with the given name

                    action_list_snaps()     --  Lists the snaps on the array with the given name

                    array_list()            -- Lists all the arrays

                    delete_snaps()          -- Deletes the snap with given jobid for an array

                    delete_all_snapshots()  -- Delete all snapshots for an array

                    reconcile_snapshots()   -- Reconcile snapshots of the array


    General() -- Includes all the General information required to add array like : Array Vendor, Array Name,Control Host,
                 Username and Password.

                    add_general()   -- To add generic details to add the array


    ArrayAccessNodes() -- This class includes array controllers to be selected for pruning purpose

                    add_array_accessnodes()  -- To add array controllers for the array

    Snap_config()   -- This class includes adding/editing snap configuration of the array

                    add_snapconfig()  -- To add snap configuration for the array


    Engine()  -- Includes the method to add array for each engine.

                    add_engine()  -- To add the Snap engine



"""

from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.table import Table, Rtable
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.panel import ModalPanel, DropDown, RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from AutomationUtils import logger
from Web.AdminConsole.Components.wizard import Wizard
from AutomationUtils.database_helper import get_csdb


class Arrays():
    """ Class for the Arrays page """

    def __init__(self, admin_console):
        """Method to initiate Arrays Class
                Args:
                        admin_console   (Object) :   Admin Console Class object"""

        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__drop_down = DropDown(self.__admin_console)
        self.__rdrop_down = RDropDown(self.__admin_console)
        self.__navigator = admin_console.navigator
        self.log = logger.get_log()
        self.dialog = ModalDialog(self.__admin_console)
        self.rmodal_dialog = RModalDialog(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__wizard = Wizard(self.__admin_console)
        self._csdb = get_csdb()
        self.get_recon_job = """ SELECT  MAX(jobid) FROM JMJobStats where optype = 90 and jobCategory =3 and jobDescription like 
                                           'Snap Reconciliation Completed Successfully' """

    @PageService()
    def action_delete_array(self, array_name):
        """
        Deletes the array with the given name
       Args :
            array_name   (str)   --  the name of the array to be deleted
        """

        self.__rtable.access_action_item(array_name, "Delete")
        self.rmodal_dialog.click_submit()
        self.__admin_console.get_notification(wait_time=60)

    @PageService()
    def action_list_snaps(self, array_name):
        """
        Lists the snaps on the array with the given name

        Args :
            array_name   (str)   --  the name of the array whose snaps are to listed
        """
        self.__admin_console.refresh_page()
        self.__rtable.access_action_item(array_name, self.__admin_console.props['action.listSnaps'])

    @PageService()
    def delete_snaps(self, job_id):
        """
        Deletes the single snap or multiple snaps with the given jobids in the List for an array
        Args :
            job_id (string): single jobid or (list) multiple jobids
        returns:
            del_jobid: job id for delete operation
        """
        if type(job_id) == str or type(job_id) == int:
            self.__rtable.access_action_item(job_id, self.__admin_console.props['action.delete'])
        else:
            for jobid in job_id:
                self.__rtable.apply_filter_over_column(column_name="Job ID", filter_term=jobid)
                self.__rtable.select_all_rows()
                self.__rtable.clear_column_filter(column_name="Job ID", filter_term=jobid)
            self.__rtable.access_toolbar_menu("Delete")
        self.rmodal_dialog.click_submit(wait=False)
        del_jobid = self.__admin_console.get_jobid_from_popup()
        return del_jobid

    def array_list(self):
        """
        Lists all the arrays.
        :return array_info  (dict)  --  dict of all arrays, contains name, username and snap vendor.
        """
        self.log.info("Listing all the arrays")
        array_info = []
        array_table = self.__driver.find_element(By.ID, 'snapArrayTable')
        rows = array_table.find_elements(By.XPATH, ".//tr")[1:]
        for row in rows:
            name = row.find_element(By.XPATH, ".//td[1]").text
            user_name = row.find_element(By.XPATH, ".//td[2]").text
            snap_vendor = row.find_element(By.XPATH, ".//td[3]").text
            array_info.append({'name': name, 'user_name':user_name, 'snap_vendor': snap_vendor})
        self.log.info(array_info)
        return array_info

    def delete_all_snapshots(self):
        """
        Delete all  the snaps on the array
        """
        self.log.info("Deleting snaps for the given array")
        if self.__rtable.get_total_rows_count():
            self.__driver.find_element(By.XPATH, "//th//*[contains(@class,'k-checkbox')]").click()
            self.__admin_console.click_button_using_text("Delete")
            self.__r_modal_dialog = RModalDialog(self.__admin_console)
            self.__r_modal_dialog.click_button_on_dialog("Delete")
            job_id = self.__admin_console.get_jobid_from_popup()
            return job_id
        else:
            self.log.info(f"List Snapshots: {self.__rtable.get_total_rows_count()}")
            return False

    @PageService()
    def mount_snap(self, job_id, client_name, mount_path):
        """
           Mounts the snap with the given jobid if jobid is single jobid else multiple jobids in the list for an array
        Args :
            job_id:  (str):single jobid or (list):multiple jobids
            client_name (string)    -- client name
            mount_path (string)   -- mount path
        """
        if type(job_id) == str or type(job_id) == int:
            self.__rtable.access_action_item(job_id, self.__admin_console.props['action.mount'])
        else:
            for jobid in job_id:
                self.__rtable.apply_filter_over_column(column_name="Job ID", filter_term=jobid)
                self.__rtable.select_all_rows()
                self.__rtable.clear_column_filter(column_name="Job ID", filter_term=jobid)
            self.__rtable.access_toolbar_menu("Mount")
        self.__rdrop_down.select_drop_down_values(values=[client_name], drop_down_id='availableMediaAgents')
        self.__admin_console.fill_form_by_id("destPath", mount_path)
        self.rmodal_dialog.click_submit(wait=False)
        self.__admin_console.click_button_using_text('Yes')
        mount_jobid = self.__admin_console.get_jobid_from_popup()
        return mount_jobid

    @PageService()
    def unmount_snap(self, job_id, plan_name, copy_name):
        """
        Unmounts the snap with the given jobid if jobid is single jobid else multiple jobids in the list for an array
        Args :
            job_id's   (string)    -- list of job id
            plan_name  (string)    -- plan name
            copy_name  (string)    -- copy name

      Note: If subclient content has different volumes locations then same jobid is created for different volumes snaps,
            if multiple snaps exists then all jobs with same jobid will be selected and unmounted

        """
        if type(job_id) == str or type(job_id) == int:
            self.__rtable.search_for(job_id)
            if plan_name and copy_name:
                sp_copy = "{}/{}".format(plan_name, copy_name)
            else:
                sp_copy = ""
            self.__rtable.apply_filter_over_column(column_name="Plan/Copy", filter_term=sp_copy)
            if self.__rtable.get_total_rows_count(job_id) == 1:
                self.__rtable.access_action_item(job_id, self.__admin_console.props['action.unmount'])
                self.rmodal_dialog.click_submit(wait=False)
            else:
                self.__rtable.select_all_rows()
                self.__rtable.access_toolbar_menu("Unmount")
                self.rmodal_dialog.click_submit(wait=False)
        else:
            for jobid in job_id:
                self.__rtable.search_for(jobid)
                if plan_name and copy_name:
                    sp_copy = "{}/{}".format(plan_name, copy_name)
                else:
                    sp_copy = ""
                self.__rtable.apply_filter_over_column(column_name="Plan/Copy", filter_term=sp_copy)
                self.__rtable.select_all_rows()
                self.__rtable.clear_column_filter(column_name="Plan/Copy", filter_term=sp_copy)
            self.__rtable.access_toolbar_menu("Unmount")
            self.rmodal_dialog.click_submit(wait=False)
        unmount_jobid = self.__admin_console.get_jobid_from_popup()
        return unmount_jobid

    def execute_query(self, query, my_options=None, fetch_rows='all'):
        """ Executes SQL Queries
            Args:
                query           (str)   -- sql query to execute

                my_options      (dict)  -- options in the query
                default: None

                fetch_rows      (str)   -- By default return all rows, if not return one row
            Return:
                    str : first column of the sql output

        """
        if my_options is None:
            self._csdb.execute(query)
        elif isinstance(my_options, dict):
            self._csdb.execute(query.format(**my_options))

        if fetch_rows != 'all':
            return self._csdb.fetch_one_row()[0]
        return self._csdb.fetch_all_rows()

    @PageService()
    def reconcile_snapshots(self, array_name):
        """
        Reconcile snapshots at array level
        Args :
                array_name  (str)  -- name of the array
        """

        self.__rtable.access_action_item(array_name, "Reconcile snapshots")
        recon_jobid = self.execute_query(self.get_recon_job)
        recon_jobid = recon_jobid[0][0]
        self.log.info("Running Reconcilation Operation is with Job ID:{0}".format(recon_jobid))
        self.__admin_console.wait_for_completion()
        return recon_jobid


class _General():
    """
    Class for adding general details of Arrays
    """

    def __init__(self, admin_console):
        """
        Method to initate General Class
        """
        self._admin_console = admin_console
        self._rtable = Rtable(self._admin_console)
        self._drop_down = DropDown(self._admin_console)
        self._rdropdown = RDropDown(self._admin_console)
        self._rpanel = RPanelInfo(self._admin_console)
        self._wizard = Wizard(self._admin_console)

    @PageService()
    def add_general(self,
                    array_vendor,
                    array_name,
                    username,
                    password,
                    control_host=None,
                    credentials=False):
        """

        Args:
            snap_vendor:   (str)            -- Name of the snap vendor
            array_name:    (str)            -- Name of the array
            control_host:  (str)            -- Name of the control host
            user_name:     (str)            -- username of the array
            password:      (str)            -- password of the array
            credentials :  (str)            -- saved Credentials of the array


        """
        self._rtable.access_toolbar_menu('Add')
        self._rdropdown.select_drop_down_values(values=[array_vendor], drop_down_id="snapVendor")
        self._admin_console.fill_form_by_id("arrayName", array_name)
        if self._admin_console.check_if_entity_exists("id", "arrayHost"):
            self._admin_console.fill_form_by_id("arrayHost", control_host)

        if credentials is not None:
            self._wizard.enable_toggle(label="Use saved credentials")
            self._rdropdown.select_drop_down_values(values=[credentials], drop_down_id="savedCredential")

        else:
            self._admin_console.fill_form_by_id("userName", username)
            self._admin_console.fill_form_by_id("password", password)


class _ArrayAccessNodes():
    """
    Class for adding Array access nodes for the array
    """

    def __init__(self, admin_console):
        """
        Method to initate General Class
        """
        self._admin_console = admin_console
        self._rdropdown = RDropDown(self._admin_console)

    @PageService()
    def add_array_accessnodes(self, controllers):
        """
        Args:
            controllers:  (list)        -- list the array controllers
        """
        if controllers:
            self._rdropdown.select_drop_down_values(values=[controllers], drop_down_id='availableMediaAgents')
            self._admin_console.wait_for_completion()

class _Snap_config():

    def __init__(self, admin_console,csdb):

        """
        Args:
            admin_console:  (obj)        -- browser object

            csdb: (obj)                  -- database object
        """

        self.csdb = csdb
        self._admin_console = admin_console
        self.log = logger.get_log()
        self.get_master_config_id = """SELECT config.id FROM SMMasterConfigs AS config
                                                    INNER JOIN SMVendor AS vendor ON config.VendorId = vendor.id		
                                                    WHERE config.Name LIKE '{a}' AND vendor.Name LIKE '{b}'"""
        self.get_type_input = """SELECT Type from SMMasterConfigs WHERE id = {a}"""
        self.snap_config = """ SELECT Name from SMMasterConfigs WHERE id = {a}"""
        self.rmodaldialog = RModalDialog(self._admin_console)

    @PageService()
    def add_snapconfig(self, snap_configs, array_vendor):
        """

        Args:
            snap_configs:  (str)        -- Snap configs to be updated
            array_vendor:  (str)        -- array vendor name

        """

        import json
        if snap_configs and type(snap_configs) is not dict:
            snap_configs = json.loads(snap_configs)
        if snap_configs:
            config_data = {}
            self.log.info(f"snap config {snap_configs}, array_vendor {array_vendor}")
            for config, value in snap_configs.items():
                self.csdb.execute(self.get_master_config_id.format(
                    **{'a': config, 'b': array_vendor}))
                master_config_id = self.csdb.fetch_one_row()[0]
                self.log.info(f"Config ID: {master_config_id}, value: {value}")
                config_data[master_config_id] = value

                self.csdb.execute(self.snap_config.format(**{'a': master_config_id}))
                toggle_config = self.csdb.fetch_one_row()[0]
                self.csdb.execute(self.get_type_input.format(**{'a': master_config_id}))
                type_1 = self.csdb.fetch_one_row()[0]

                if str(type_1) == '1':
                    if value == "True":
                        self.rmodaldialog.enable_toggle(master_config_id)
                    else:
                        self.rmodaldialog.disable_toggle(master_config_id)

                if type_1 != '1':
                    if self._admin_console.check_if_entity_exists("id", master_config_id):
                        self._admin_console.fill_form_by_id(master_config_id, value)
                        self._admin_console.wait_for_completion()

        else:
            config_data = None



class Engine(_General, _ArrayAccessNodes , _Snap_config):

    def __init__(self, admin_console , csdb):

        super().__init__(admin_console)

        from AutomationUtils.database_helper import get_csdb

        self._csdb = get_csdb()
        self._admin_console = admin_console
        self.log = logger.get_log()
        self.csdb = csdb
        self.get_master_config_id = """SELECT config.id FROM SMMasterConfigs AS config
                                                                   INNER JOIN SMVendor AS vendor ON config.VendorId = vendor.id		
                                                                   WHERE config.Name LIKE '{a}' AND vendor.Name LIKE '{b}'"""
        self.get_type_input = """SELECT Type from SMMasterConfigs WHERE id = {a}"""
        self.snap_config = """ SELECT Name from SMMasterConfigs WHERE id = {a}"""
        self.rmodaldialog = RModalDialog(self._admin_console)

    @PageService()
    def add_engine(self, array_vendor,
                   array_name,
                   username,
                   password,
                   control_host,
                   controllers,
                   credential_name=None,
                   snap_config=None):
       """

       Args:
           array_vendor: select the array vendor
           array_name:   (str)   --     name of the array
           username:     (str)   --     username of the array
           password:     (str)   --     password of the array
           control_host: (int)   --     control host of the array
           controllers:  (str)   --     name of the array controller
           snap_config:  (str)   --     Edit the snap configuration of the array
           credential_name : (str) -- Name of the Credential of Storage Array Account


       """
       self.add_general(array_vendor, array_name, username, password, control_host, credential_name)
       self._admin_console.button_next()
       if controllers:
           self.add_array_accessnodes(controllers)
           self._admin_console.click_button('Next')
           self._admin_console.wait_for_completion()
       if snap_config:
           self.add_snapconfig(snap_config, array_vendor)
       self._admin_console.click_button("Submit")
       self._admin_console.wait_for_completion()

