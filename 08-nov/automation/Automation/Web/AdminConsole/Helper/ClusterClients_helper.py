# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be used to run
basic operations on identity servers page.

Class:

    ClusterMain:

        __init__()                  --Initializes the cluster server helper module

        get_cluster_properties()	    --Returns details about the nodes, agents and job directory

        run_backup()				    --Runs backup jobs for a cluster client and validate

        run_restore()				    --Runs restore jobs for a cluster client and validate

        open_cluster_client()	        --Searches for given client and opens it

        add_clusterclient()             --Adds Cluster client

        edit_clustergroup()				--Edits Cluster client

        deconfigure_cluster()			--Deconfigure Clusterclient

        delete_cluster()			    --Delete Clusterclient

        get_list_of_servers()		    --Lists the servers present in servers page

        hard_delete_GxClusPlugin()		--Hard delete GxCluster plugin on the client machine

        verify_plugin()				    --Verify if plugin is reconfigured or not

        validate_agents()               --Validates Agents list

        validate_nodes()                --Validates Nodes list

        validate_job_directory()        --Validates job directory

"""
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.server_details import ServerDetails
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.exceptions import CVWebAutomationException


class ClusterMain:
    """
            Helper for Cluster client page
    """

    def __init__(self, admin_console):
        """
        Initializes Cluster helper module
            Args:

                admin_console   (object) -- _Navigator class object

            Returns : None
        """
        self.__adminconsole = admin_console
        self.__driver = admin_console.driver
        self.server = Servers(self.__adminconsole)
        self.server_details = ServerDetails(self.__adminconsole)
        self.__table = Table(admin_console)
        self.__panel = PanelInfo(admin_console, 'Cluster group')
        self.file_server = FileServers(self.__adminconsole)
        self.__jobs = Jobs(self.__adminconsole)
        self.navigator_obj = self.__adminconsole.navigator
        self.log = logger.get_log()

    def switch_to_configuration_tab(self):
        """  Selects the configuration tab """
        self.log.info("Switching to configuration tab")
        self.server.select_configuration_tab()

    def switch_to_overview_tab(self):
        """ Selects the overview tab """
        self.log.info("Switching to overview tab")
        self.server.select_overview_tab()

    def run_backup(self, client_name, backup_level):
        """ Run a backup job """
        self.log.info("Running a backup job for the default sublient")
        job_id = self.file_server.backup_subclient(client_name, backup_level)
        backup_job_details = self.__jobs.job_completion(job_id=job_id)
        if backup_job_details['Status'] == 'Completed':
            return True
        return False

    def run_restore(self, client_name):
        """ Run a restore job """
        self.log.info("Running a restore job")
        job_id = self.file_server.restore_subclient(client_name)
        restore_job_details = self.__jobs.job_completion(job_id=job_id)
        if restore_job_details['Status'] == 'Completed':
            return True
        return False

    def open_cluster_client(self, client_name):
        """
            Searches for a given clinet and opens it

            Args:

                client_name    (str)   --   cluster client name

            Returns:     None
        """
        self.log.info("Opening Cluster Client")
        self.server.select_client(client_name)

    def add_clusterclient(self, name, host, os_type, plan, job_dir, nodes, agents, force_sync=None):
        """
            Adds Cluster client
        """
        self.server.add_cluster_client(name, host, os_type, plan, job_dir, nodes, agents, force_sync)

    def edit_clustergroup(self, nodes=None, agents=None, job_dir=None, force_sync=None, add=None, delete=None):
        """ Edits Cluster client """
        self.server_details.edit_cluster_group(
            nodes=nodes,
            agents=agents,
            job_dir=job_dir,
            force_sync=force_sync,
            add=add,
            delete=delete)

    def deconfigure_cluster(self, nodes):
        """ Deconfigure cluster nodes"""
        self.server_details.deconfigure_cluster_client(nodes=nodes)

    def delete_cluster(self, client_name):
        """ Deleting a cluster client """
        self.server.delete_cluster_client(client_name)

    def get_list_of_servers(self):
        """ Gets the list of server details """
        return self.__table.get_column_data('Name')

    def hard_delete_GxClusPlugin(self, hostname, username, pwd):
        """ Hard delete GxCluster plugin on the client machine"""
        machine = Machine(machine_name=hostname, username=username, password=pwd)
        output = machine.execute_command('sc.exe delete "GxClusPlugIn (Mega1) (Instance001)"')
        if output.exception:
            raise CVWebAutomationException("operation Failed")
        else:
            return output.output

    def verify_plugin(self, hostname, username, pwd):
        """ Verify if plugin is reconfigured or not """
        machine = Machine(machine_name=hostname, username=username, password=pwd)
        self.log.info(" Executing query to get details of given service ")
        output = machine.execute_command('Get-Service -Name "GxClusPlugIn*"')
        if output.exception:
            raise CVWebAutomationException(output.exception)
        else:
            return output.output

    def validate_agents(self, cluster_groups, input_agents):
        """
        Validates the given input agents with the values in UI

        Args:
            cluster_groups (dict)   :   cluster details present in 'Cluster group' panel
            input_agents   (list)   :   input agents to validate

        Returns :   Boolean
        """
        agents = ' , '.join(input_agents)
        if set(cluster_groups['Agents']) == set(agents):
            return True
        return False

    def validate_nodes(self, cluster_groups, input_nodes):
        """
        Validates the given input nodes with the values in UI

        Args:
            cluster_groups (dict)   :   cluster details present in 'Cluster group' panel
            input_nodes   (list)   :   input nodes to validate

        Returns :   Boolean
        """
        cluster_nodes = cluster_groups['Nodes'].split(' , ')
        if any(item in input_nodes for item in cluster_nodes):
            return True
        return False

    def validate_job_dir(self, cluster_groups, input_job_dir):
        """
        Validates the given input job dir with the values in UI

        Args:
            cluster_groups (dict)   :   cluster details present in 'Cluster group' panel
            input_job_dir  (str)    :   input job directory value to validate

        Returns :   Boolean
         """
        job_dir = input_job_dir + 'JobResults'
        if job_dir == cluster_groups['Job storage cache']:
            return True
        return False

    def get_cluster_properties(self, cluster_name):
        """
        Gets Cluster client properties

        cluster_name (str)      :   Name of the cluster

        Returns:
            a dictionary with the details present in cluster groups tile
        """
        self.navigator_obj.navigate_to_servers()
        self.open_cluster_client(cluster_name)
        self.switch_to_configuration_tab()
        self.log.info("Getting the details of cluster group")
        cluster_groups = self.__panel.get_details()
        return cluster_groups