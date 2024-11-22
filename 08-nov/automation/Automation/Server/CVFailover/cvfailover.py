# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Main file for performing cvfailover operations.

CSLiveSync: Class for all CS Live Sync Operations
    __init__() -- Initializes the CSLiveSync class instance

    _get_failover_command() -- Returns failover command

    failover() -- Performs Failover or Failback operation

    get_failover_status() -- Returns Failover status

"""


from cvpysdk.exception import SDKException


class CSLiveSync:
    """Class for all CS Live Sync Operations"""

    PRODUCTION = "Production"
    PRODUCTION_MAINTENANCE = "ProductionMaintenance"
    MAINTENANCE_FAILBACK = "MaintenanceFailback"
    TEST = "Test"
    TEST_FAILBACK = "TestFailback"

    PLANNED = "Planned"
    UNPLANNED = "UnPlanned"
    FORCE_UNPLANNED = "ForceUnPlanned"

    def __init__(self, commcell_object, failover_client_name):
        """
        Initializes the CSLiveSync class instance

        Args:
            commcell_object (object) --  Instance of the Commcell class
            failover_client_name (str) --  Name of the SQL failover instance client name

        Returns:
                object - instance of the CSLiveSync class
        """
        self.cs_obj = commcell_object
        self.failover_client_name = failover_client_name
        self.failover_client_obj = self.cs_obj.clients.get(failover_client_name)

    @property
    def path(self):
        """Returns failover command"""
        if 'windows' in self.failover_client_obj.os_info.lower():
            return f'"{self.failover_client_obj.install_directory}\\Base\\CvFailover.exe"'
        elif 'unix' in self.failover_client_obj.os_info.lower():
            return f'{self.failover_client_obj.install_directory}/Base/CvFailover'
        else:
            raise SDKException('Client', '109')

    def failover(self, failovertype, failoversubtype, targetnode):
        """
        Performs Failover  operation

        Args:
            failovertype (str) --  Failover type
                Valid Values are:
                    Production
                    ProductionMaintenance
                    MaintenanceFailback
                    Test
                    TestFailback

            failoversubtype (str)   -- Failover Sub type
                Valid values are:
                    Planned
                    UnPlanned
                    ForceUnPlanned

            targetnode (str)    -- Target Node Name

        Returns:
                True/False based on the result
        """
        cmd = self.path + f" -OpType Failover -FailoverType {failovertype} -FailoverSubType {failoversubtype} -TargetNode {targetnode}"
        return self.failover_client_obj.execute_command(cmd, wait_for_completion=False)

    def get_failover_config(self):
        """
        Shows failover configuration status - active, passive node information.
        """
        cmd = self.path + "-OpType GetFailoverConfig"
        return self.failover_client_obj.execute_command(cmd, wait_for_completion=False)

    def reset_failover_operation(self):
        """
        Shows failover configuration status - active, passive node information.
        """
        cmd = self.path + "-OpType ReSetFailoverOperation"
        return self.failover_client_obj.execute_command(cmd, wait_for_completion=False)

    def reset_failover_config(self):
        """
        Shows failover configuration status - active, passive node information.
        """
        cmd = self.path + "-OpType ReSetFailoverConfig"
        return self.failover_client_obj.execute_command(cmd, wait_for_completion=False)

    def get_recent_failover_log(self):
        """
        Returns the log for latest failover operation
        """

    def check_phases(self, output):
        """
        Check each steps and return the list of failed steps.
        """
        failed_tasks = []
        output = output.split("\n")
        for each_line in output:
            if "Failed" in each_line:
                failed_tasks.append(each_line)

        if "Successfully completed" in output[-1]:
            return "PASSED", failed_tasks
        return "FAILED", failed_tasks
