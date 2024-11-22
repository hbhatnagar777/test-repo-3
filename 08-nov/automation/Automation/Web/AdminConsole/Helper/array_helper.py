# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This module provides the function or operations related to Storage in AdminConsole
ArrayHelper : This class provides methods for Array related operations

ArrayHelper
===========

__init__(admin_console obj, csdb obj)  --  initialize object of ArrayHelper class associated

add_array()                     --      add array using admin console

associate_array()               --      associate storage array with a client

list_snap()                     --      list all snaps of a storage array

delete_all_snap()               --      deletes all snaps of a storage array

disassociate_array()            --      disassociate storage array from a client

delete_array()                  --      deletes storage array from admin console


"""

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.Arrays import Arrays , Engine
from Web.AdminConsole.AdminConsolePages.ArrayDetails import ArrayDetails




class ArrayHelper():
    """ Helper for handling function calls for Array operations from ArrayDetails."""

    def __init__(self, admin_console, csdb=None):

        """Initialize object for ArrayHelper class.

            Args:
                admin_console:  (obj)   --  browser object

                csdb :   (obj)   -- database object
            Returns:
                object - instance of ArrayHelper class

        """

        self.csdb = csdb
        self.log = logger.get_log()
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__navigator = admin_console.navigator
        self._array_obj = Arrays(self.__admin_console)
        self._engine_obj = Engine(self.__admin_console, csdb)
        self._arraydetails_obj = ArrayDetails(self.__admin_console)
        self._array_vendor = None
        self._array_name = None
        self._controllers = None
        self._client_name = None
        self._array_control_host = None
        self._snap_config = None
        self._region = None
        self._credential_name = None

    @property
    def array_vendor(self):


        """Returns the Array vendor

                Returns:    _array_vendor    (str)   --  array vendor name

        """
        return self._array_vendor

    @array_vendor.setter
    def array_vendor(self, value):
        """Sets the array vendor
            Args :

               value :    (str)   --  array vendor name

        """
        self._array_vendor = value

    @property
    def array_name(self):
        """Returns the Array name
                Returns :     _array_name    (str)   --  array name

        """
        return self._array_name

    @array_name.setter
    def array_name(self, value):
        """Sets the array name
           Args:
                value :  (str)   --  array name

        """
        self._array_name = value


    @property
    def client_name(self):
        """Returns the client name
                Returns:    _client_name    (str)   --  client name

        """
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        """Sets the client name
        Args :
                value:   (str)   --  client name

        """
        self._client_name = value

    @property
    def array_controllers(self):
        """Returns the array controllers

                Returns:    _array_controllers    (list)   --  list of all array controllers

        """
        return self._array_controllers

    @array_controllers.setter
    def array_controllers(self, value):
        """Sets the array controller
        Args :
                value :   (str / list)   --  controllers of the array

        """
        if isinstance(value, str):
            self._array_controllers = [value]
        elif isinstance(value, list):
            self._array_controllers = value
        else:
            raise Exception("Please pass the correct instance of the array controller.")

    @property
    def control_host(self):
        return self._array_control_host

    @control_host.setter
    def control_host(self, value):
        """
        Sets the array control host value
        Args:
            value: name of the control host

        Returns:
            None

        """
        self._array_control_host = value

    @property
    def snap_config(self):
        """Returns the Array name
                Returns :    _array_name    (str)   --  array name

        """
        return self._snap_config

    @snap_config.setter
    def snap_config(self, value):
        """Sets the array name
                value:    (str)   --  array name

        """
        self._snap_config = value

    @property
    def region(self):
        """Returns the Region name
                Returns :    _region   (str)   --  region name

        """
        return self._region

    @region.setter
    def region(self, value):
        """Sets the region
                value:    (str)   --  region

        """
        self._region = value



    def add_engine(self):
        """Creates Storage Array"""

        # Add Array
        self._engine_obj.add_engine(
            self.array_vendor,
            self.array_name,
            self.array_user,
            self.array_password,
            self.control_host,
            self.controllers,
            self.credential_name,
            self.snap_config)

    def edit_snap_configuration(self):

        """Edits snap configuration"""

        self._arraydetails_obj.edit_snap_configuration(
            self.array_vendor,
            self.array_name,
            self.snap_config
        )

    def edit_general(self):

        """Edits the General properties of array"""

        self._arraydetails_obj.edit_general(self.array_name, self.region)

    def edit_array_access_node(self):

        """Edits the array controllers of the array"""

        self.__navigator.navigate_to_arrays()
        self._arraydetails_obj.edit_array_access_node(self.array_name, self.controllers)

    def clear_all_access_nodes(self):
        self.__navigator.navigate_to_arrays()
        self._arraydetails_obj.clear_access_node(self.array_name)

    def associate_array(self):

        """Associate Storage Array and server"""
        self.array_obj.navigate_to_arrays()
        # Select Array
        self.array_obj.select_array(self._array_name)
        # Associate server with Added array
        self.array_obj.associate_existing_server([self._client_name])

    def list_snap(self):
        """
        Lists all the snaps of the array

        Returns:
            None

        """
        self.log.info("Listing Snaps")
        self.__navigator.navigate_to_arrays()
        self._array_obj.action_list_snaps(self._array_name)

    def verify_snap(self):
        """List Snaps of a storage array"""
        # List snaps of the array
        self.list_snap()
        self.__table.search_for(self.client_name)
        if not self.array_obj.check_if_entity_exists("xpath",
                                                     "//div[@class='ui-grid-contents-wrapper']"
                                                     "/div[3]/div[2]/div/div[1]"):
            raise Exception("A snap was not present for this client")

    def delete_all_snap(self):
        """Delete All snaps for the Array"""
        # List snaps of the array
        self.list_snap()
        self.log.info("Deleting Snaps")
        job_id = self.array_obj.delete_all_snapshots()
        job_details = self.job_obj.job_completion(job_id)
        if job_details['Status'] not in ["Completed"]:
            raise Exception("Snaps in array could not be deleted. Please check logs.")

    def delete_snap_by_job(self, jobID):
        """ Delete snaps in the array with given jobID
                Args:
                    jobID-> job id of the snap that needs to be deleted

                Returns:
                    del_jobID -> jobID of the delete snap job
        """
        self.list_snap()
        self.log.info("Deleting snap of Job: {0}".format(jobID))
        del_jobID = self._array_obj.delete_snaps(jobID)
        
        return del_jobID

    def disassociate_array(self):
        """Disassociate Storage array from the server"""
        self.array_obj.navigate_to_arrays()
        # Select Array
        self.array_obj.select_array(self._array_name)
        self.array_obj.action_disassociate_server(self._client_name)

    def action_delete_array(self):
        """Delete Storage Array"""
        # Select Array to delete

        self._array_obj.action_delete_array(self.array_name)
        _query = "select ControlHostId  from SMControlHost where SMArrayId='{0}'".format(
            self._array_name)
        self.csdb.execute(_query)
        _results = self.csdb.fetch_one_row()
        _control_hostid = _results[0].strip()
        if _control_hostid:
            raise Exception("Array could not be Deleted from DB")
        else:
            self.log.info("Array Deleted Successfully from DB")

    def disable_pruning(self):
        """disable pruning on all MAs"""
        self.__navigator.navigate_to_arrays()
        self._arraydetails_obj.disable_pruning(self.array_name)

