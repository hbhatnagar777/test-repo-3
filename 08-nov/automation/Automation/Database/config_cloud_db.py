# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module for communicating with cvpysdk for all commvault related operations.

ConfigCloudDb class is defined in this file.

ConfigCloudDb: Performs Commvault related operations using cvpysdk

ConfigCloudDb:
    __init__()                                  --  initializes configclouddb object

    client()                                    --  fetches client object

    agent()                                     --  fetches agent object

    instance()                                  --  fetches instance object

    add_cloud_client()                          --  adds cloud client if it is not exist

    add_database_instance()                     --  adds database instance if it is not exist

    add_database_agent()                        --  adds database agent if it is not exist

"""

from AutomationUtils import logger
import json


class ConfigCloudDb:
    """Class for performing Commvault operations"""

    def __init__(self, commcell, tc_inputs, client_obj=None, instance_obj=None):
        """Initializes the ConfigCloudDb object.

            Args:
                commcell     (object)  --  commcell object
                tc_inputs    (dict)    --  testcase inputs
                client_obj   (object)  --  client object
                instance_obj (object)  --  instance object
        """
        self.tc_inputs = tc_inputs
        self.commcell = commcell
        self.log = logger.get_log()
        self.client_name = self.tc_inputs.get('ClientName',
                                              self.tc_inputs.get('client_name', 'Cloud_Database_Client_Automation'))
        self.instance_name = self.tc_inputs.get('InstanceName', self.tc_inputs.get('instance_name', ''))
        self.agent_name = self.tc_inputs.get('AgentName', self.tc_inputs.get('agent_name', ''))
        self.access_node = self.tc_inputs.get("access_node", "")
        self.port = self.tc_inputs.get("port", "")
        self.storage_policy = self.tc_inputs.get('storage_policy', '')
        self.database_options = self.tc_inputs.get('database_options', {})
        if not isinstance(self.database_options, dict):
            self.database_options = json.loads(self.database_options)
        self.cloud_type = self.tc_inputs.get('cloud_type', 'Azure')
        self.cloud_options = self.tc_inputs.get('cloud_options', {})
        if not isinstance(self.cloud_options, dict):
            self.cloud_options = json.loads(self.cloud_options)
        self._client = None
        self._agent = None
        self._instance = None
        if client_obj is None:
            self.add_cloud_client()
            self.add_database_agent()
            self.add_database_instance()
        else:
            self._client = client_obj
        if instance_obj is None:
            self.add_database_agent()
            self.add_database_instance()
        else:
            self._instance = instance_obj

    @property
    def instance(self):
        """Returns instance object."""
        if self._instance is None:
            self._instance = self.agent.instances.get(self.instance_name)
        return self._instance

    @property
    def client(self):
        """Returns client object."""
        if self._client is None:
            self._client = self.commcell.clients.get(self.client_name)
        return self._client

    @property
    def agent(self):
        """Returns agent object."""
        if self._agent is None:
            self._agent = self.client.agents.get(self.agent_name)
        return self._agent

    def add_cloud_client(self):
        """
        Add cloud client to commcell
        """
        try:

            if self.commcell.clients.has_client(self.client_name):
                self.log.info('Cloud client %s already exists.', self.client_name)
                self._client = self.commcell.clients.get(self.client_name)
            else:
                self.log.info('Creating cloud client %s ', self.client_name)
                if self.cloud_type == "Azure":
                    self._client = self.commcell.clients.add_azure_client(self.client_name, self.access_node,
                                                                          self.cloud_options)
                elif self.cloud_type == "Amazon":
                    self._client = self.commcell.clients.add_amazon_client(self.client_name, self.access_node,
                                                                           self.cloud_options)
                elif self.cloud_type == "Google":
                    self._client = self.commcell.clients.add_google_client(self.client_name, self.access_node,
                                                                           self.cloud_options)
                elif self.cloud_type == "Alicloud":
                    self._client = self.commcell.clients.add_alicloud_client(self.client_name, self.access_node,
                                                                             self.cloud_options)
                else:
                    raise Exception("{0} is not supported yet.".format(self.cloud_type))

                self.log.info('Created cloud client %s ', self.client_name)

        except Exception as excp:
            self.log.exception("An error occurred while creating cloud client")
            raise excp

    def add_database_instance(self):
        """
        Add database instance to cloud client
        """
        try:
            if self.agent.instances.has_instance(self.instance_name):
                self.log.info('Database instance %s already exists under cloud client %s.',
                              self.instance_name, self.client_name)
                self._instance = self.agent.instances.get(self.instance_name)
            else:
                self.log.info('Creating database instance %s under cloud client %s',
                              self.instance_name, self.client_name)
                if self.agent_name == "PostgreSQL":
                    self._instance = self.agent.instances.add_postgresql_instance(self.instance_name,
                                                                                  self.database_options)
                elif self.agent_name == "MySQL":
                    self._instance = self.agent.instances.add_mysql_instance(self.instance_name,
                                                                             self.database_options)
                else:
                    raise Exception("{0} is not supported yet.".format(self.agent_name))

                self.log.info('Created database instance %s under cloud client %s',
                              self.instance_name, self.client_name)
        except Exception as excp:
            self.log.exception("An error occurred while creating database instance")
            raise excp

    def add_database_agent(self):
        """
        Add database agent to cloud client
        """
        try:

            if self.client.agents.has_agent(self.agent_name):
                self.log.info('Agent %s already exists under cloud client %s.', self.agent_name, self.client_name)
                self._agent = self.client.agents.get(self.agent_name)
            else:
                self.log.info('Creating agent %s under cloud client %s', self.agent_name, self.client_name)
                if self.agent_name == "PostgreSQL":
                    self._agent = self.client.agents.add_database_agent(self.agent_name,
                                                                        self.access_node,
                                                                        version=self.database_options.get("version"))
                elif self.agent_name == "MySQL":
                    self._agent = self.client.agents.add_database_agent(self.agent_name,
                                                                        self.access_node,
                                                                        install_dir=self.database_options.get("install_dir"),
                                                                        version=self.database_options.get("version"))
                else:
                    raise Exception("{0} is not supported yet.".format(self.agent_name))
                self.log.info('Created agent %s under cloud client %s', self.agent_name, self.client_name)
        except Exception as excp:
            self.log.exception("An error occurred while creating database agent")
            raise excp
