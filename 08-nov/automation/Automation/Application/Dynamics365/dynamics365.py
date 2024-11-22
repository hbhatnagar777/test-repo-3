# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Module for Dynamics 365 Automation
        Test cases making use of Dynamics 365 Helper files (Web and SDK Automation test cases)
        need to invoke them through this class' data members.

    CVDynamics365 is the only class defined in this file.

    CVDynamics365: Class for Dynamics 365 Automation

    CVDynamics365:

        populate_tc_inputs()                --  Populate necessary/ required parameters
                                                based on the Test case input values

        client                              --  CVPySDK.client object denoting the Dynamics 365 Client

        agent                               --  CVPySDK.agent object denoting the Dynamics 365 agent
                                                corresponding to the Dynamics 365 client

        backupset                           --  CVPySDK.backupset object for the backup set
                                                corresponding to the Dynamics 365 client

        subclient                           --  CVPySDK.subclient object for the sub client
                                                corresponding to the Dynamics 365 client

        instance                            --  CVPySDK.instance object for the instance corresponding
                                                to the Dynamics 365 client

        d365api_helper                      --  Instance of D365APIHelper to work with Dynamics 365 Web API's

        restore                             --  Instance of CVD365Restore for restore validations

        solr_helper                         --  Instance of D365SolrHelper for working with
                                                Dynamics 365 client based CVSolr index server

        d365_operations                     --  Instance of CVD365Operations

        csdb_operations                     --  Instance of CSDB operations
"""

from . import constants
from .csdb_helper import Dynamics365CSDBHelper
from .operations import CVD365Operations
from .pyd365_helper import D365APIHelper
from .restore_options import CVD365Restore
from .solr_helper import D365SolrHelper
from AutomationUtils.cvtestcase import CVTestCase


class CVDynamics365:

    def __init__(self, tc_object):
        """Initializes the input variables,logging and creates object from other modules.

                Args:
                    tc_object   --  instance of testcase class

                Returns:
                    object  --  instance of CVDynamics365 class"""
        self.tc_object = tc_object
        self.commcell = self.tc_object.commcell
        self.log = self.tc_object.log
        self.log.info('Logger initialized for CVDynamics365')
        self.app_name = self.__class__.__name__
        self._tables = None
        self._client = None
        self._backupset = None
        self._subclient = None
        self._instance = None
        self._agent = None
        self.csdb = self.tc_object.csdb
        self.d365_online_user: str = str()
        self.d365_online_password: str = str()
        self._restore: CVD365Restore = None
        self._pyd365: D365APIHelper = None
        self._solr_helper: D365SolrHelper = None
        self._d365_operations: CVD365Operations = None
        self._cs_db_operations: Dynamics365CSDBHelper = None
        self.d365tables: list = list()
        self.d365instances: list = list()
        self.client_name: str = str()
        self.access_nodes: list = list()
        self.access_node: str = str()
        self.index_server: str = str()
        self.job_results_directory: str = str()
        self.d365plan: str = str()
        self.azure_app_id: str = str()
        self.azure_app_secret: str = str()
        self.azure_tenant_id: str = str()
        self.tc_inputs: dict = dict()
        self.server_plan: str = str()
        self.cloud_region: int = int()
        self.populate_tc_inputs(tc_object)

    def __repr__(self):
        """Representation string for the instance of CVDynamics365 class."""

        return 'CVDynamics365 class instance'

    def populate_tc_inputs(self, tc_object: CVTestCase):
        """Initializes all the test case inputs after validation

        Args:
            tc_object (obj)    --    Object of CVTestCase
        Returns:
            None
        Raises:
            Exception:
                if a valid CVTestCase object is not passed.
                if CVTestCase object doesn't have agent initialized"""

        self.tc_inputs = tc_object.tcinputs
        self.client_name = tc_object.tcinputs.get("Dynamics_Client_Name", constants.CLIENT_NAME % tc_object.id)
        self.commcell = tc_object.commcell

        # proxies, index-server, shared job result directory
        # For Dynamics 365 Automation cases

        if isinstance(tc_object.tcinputs.get('AccessNode'), list):
            self.access_nodes = tc_object.tcinputs.get('AccessNode')
            self.access_node = self.access_nodes[0]
        else:
            self.access_node = tc_object.tcinputs.get('AccessNode')

        self.index_server = tc_object.tcinputs.get('IndexServer')
        self.job_results_directory = tc_object.tcinputs.get('JobResultDirectory', "")

        self.server_plan = tc_object.tcinputs.get('ServerPlan', "")

        self.d365plan = tc_object.tcinputs.get('Dynamics365Plan')

        self.azure_app_id = tc_object.tcinputs.get('application_id', "")
        self.azure_app_secret = tc_object.tcinputs.get('application_key_value', "")
        self.azure_tenant_id = tc_object.tcinputs.get('azure_directory_id', "")

        self.d365_online_user = tc_object.tcinputs.get("TokenAdminUser", tc_object.tcinputs.get("GlobalAdmin"))
        self.d365_online_password = tc_object.tcinputs.get("TokenAdminPassword", tc_object.tcinputs.get("Password"))

        if 'cloud_region' in self.tc_inputs:
            self.cloud_region = self.tc_inputs.get('cloud_region')
        else:
            self.cloud_region = 1

        # self.d365instances = tc_object.tcinputs.get("D365_Instance", [])
        #
        # self.d365tables = list()
        # for table, instance in tc_object.tcinputs.get("Tables", []):
        #     self.d365tables.append((table, instance))

        _tables = tc_object.tcinputs.get("D365-Tables", str()).split(",")
        _environments = tc_object.tcinputs.get("D365-Environments", str()).split(",")
        for table, instance in zip(_tables, _environments):
            self.d365tables.append((table, instance))

        self.d365instances = tc_object.tcinputs.get('D365_Instance', str()).split(",")

    @property
    def client(self):
        """Returns the client object"""
        if self._client is None:
            if not self.client_name or not self.commcell.clients.has_client(self.client_name):
                raise Exception("Client does not exist. Check the client name")
            self._client = self.tc_object.commcell.clients.get(self.client_name)
        return self._client

    @property
    def agent(self):
        """Returns the agent object"""
        if self._agent is None:
            _agent_name = list(self.client.agents.all_agents)[0]
            self._agent = self.client.agents.get(_agent_name)
        return self._agent

    @property
    def backupset(self):
        """Returns the backupset object"""
        if self._backupset is None:
            _backup_set_name = list(self.instance.backupsets.all_backupsets)[0]  # single backup set for Dynamics
            self._backupset = self.instance.backupsets.get(_backup_set_name)
        return self._backupset

    @property
    def instance(self):
        """Returns the instance object"""
        if self._instance is None:
            _instance_name = list(self.agent.instances.all_instances)[0]  # single instance for Dynamics
            self._instance = self.agent.instances.get(_instance_name)
        return self._instance

    @property
    def subclient(self):
        """Returns the sub-client object"""
        if self._subclient is None:
            _sub_client_name = list(self.backupset.subclients.all_subclients)[0]  # Single sub client for Dynamics
            self._subclient = self.backupset.subclients.get(_sub_client_name)
        return self._subclient

    @property
    def d365api_helper(self):
        """Returns the D365 API Helper object"""
        self._pyd365 = D365APIHelper(self) if self._pyd365 is None else self._pyd365
        return self._pyd365

    @property
    def restore(self):
        """Returns the CVDynamicsRestore object"""
        self._restore = CVD365Restore(self) if self._restore is None else self._restore
        return self._restore

    @property
    def solr_helper(self):
        """Returns the Solr helper object for Dynamics 365"""
        self._solr_helper = D365SolrHelper(self) if self._solr_helper is None else self._solr_helper
        return self._solr_helper

    @property
    def d365_operations(self):
        """
            Returns the CV Dynamics 365 Operations object
        """
        self._d365_operations = CVD365Operations(self) if self._d365_operations is None else self._d365_operations
        return self._d365_operations

    @property
    def csdb_operations(self):
        """
            Returns the Dynamics 365 CS-DB Helper Object
        """
        self._cs_db_operations = Dynamics365CSDBHelper(self) \
            if self._cs_db_operations is None else self._cs_db_operations
        return self._cs_db_operations
