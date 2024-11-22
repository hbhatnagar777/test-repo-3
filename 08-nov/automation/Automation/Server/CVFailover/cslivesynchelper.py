# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file to perform the CSlivesync operation

LiveSync is the only class defined in this file

LiveSync:
    __init__()                 --  Initialize the LiveSync Object 
    _set_values                --  Set the OS related values
    get_commands               --  Return the specific command to perform failover
    execute_command            --  Execute the given command on the client through CVD
    production_failover        --  Perform production failover
    production_failback        --  Perform production failback
    test_failover              --  Perform test failover
    test_failback              --  Perform test failback
    production_maintenance     --  Perform maintenance failover
    maintenance_failback       --  Perform maintenance failback
    reset_config               --  Perform the reset config command on the client

"""
import os
from AutomationUtils.machine import Machine


class LiveSync:
    """ Livesync Helper class to perform Failovers and other Livesync operations"""
    def __init__(self, testcase, node_name, machine_hostname=None, machine_username=None, machine_passwod=None):
        self.node_name = node_name
        self.testcase = testcase
        self.log = testcase.log
        self.client_obj = testcase.commcell.clients.get(node_name)
        self.log_directory = self.client_obj.log_directory
        self.cmd = None
        self.machine = None
        if not machine_hostname:
            machine_hostname = self.client_obj.client_hostname
        
        if machine_hostname and machine_username and machine_passwod:
            self.machine = Machine(
                machine_name=machine_hostname,                   
                username=machine_username,
                password=machine_passwod
            )
        else:
            self.machine = Machine(self.client_obj)
        self.get_gxadmin_path = None
        self._set_values()
        self.flags = ["-silent", "-skipConfirmation", "-forceUnplannedFailover"]

    def __str__(self):
        return f"CSLiveSync Object for {self.node_name}."

    def _set_values(self):
        """
	    Method to set gxadmin path and other tokens required for Livesync operations based on os flavour.
	    """
        if 'windows' in self.client_obj.os_info.lower():
            self.get_gxadmin_path = self.client_obj.install_directory + "\\Base\\GxAdmin.exe"
            self.cmd = {
                "failover": """ -console -failover -execute -type "failover_type" -destNode dest_node""",

                "get_node_info": """ -console -failover -getnodeinfo -nodeName node_name""",

                "resetconfig": """ -console -resetconfig -nodeName node_name""",

                "getoperationstatus": """ -console -failover -getoperationstatus -silent"""
            }
        elif 'unix' in self.client_obj.os_info.lower():
            self.get_gxadmin_path = f"{self.client_obj.install_directory}/Base/CvFailover"
            self.cmd = {
                "failover": " -OpType Failover -FailoverType failover_type -FailoverSubType failover_subtype -TargetNode dest_node ",
                "get_node_info": """ -OpType GetFailoverConfig""",
                "resetconfig": """ -OpType ReSetFailoverConfig""",
                "reset_failover_operation": """ -OpType ReSetFailoverConfig"""
            }

    def get_commands(self, op_type):
        """
        Dictionary for all the commands:
            Key: Name of command
            Value: command

        Keyword arguments for commands
            failover           : 'failover_type' & 'dest_node'
            get_node_info      : 'node_name'
            resetconfig        : 'node_name'
            getoperationstatus : None

        Value is list of commands 0th index is for windows, 1st index for Linux
        """
        try:
            return f'''"{self.get_gxadmin_path}"''' + self.cmd[op_type]
        except Exception as e:
            raise Exception(str(e))

    def execute_command(self, command, wait_for_completion=False):
        """ Execute the given command """
        self.log.info(f"\nExecuting {command} on {self.node_name}")
        if self.machine:
            output = self.machine.execute_command(command)
            output = (output.exit_code, output.output, output.exception)
        else:
            output = self.client_obj.execute_command(command, wait_for_completion=wait_for_completion)
        self.log.info(f"Output: {output}")
        return output

    def production_failover(self, dest_node, wait_for_completion=False):
        """
        Peforms production failover on the given node name

        Args:
            dest_node            (str)  -- Destination node name
            wait_for_completion  (bool) -- Wait util the command get executed
        """
        cmd = self.get_commands("failover")
        cmd = cmd.replace("failover_type", "Production")
        cmd = cmd.replace("dest_node", dest_node)

        if "unix" in self.client_obj.os_info.lower():
            cmd = cmd.replace("failover_subtype", "Planned")
        else:
            cmd += " -forceUnplannedFailover"
        self.log.info(f"Executing {cmd}")
        return self.execute_command(cmd, wait_for_completion)

    def unplanned_production_failover(self, dest_node, wait_for_completion=False):
        """
        Peforms unplanned production failover on the given node name

        Args:
            dest_node            (str)  -- Destination node name
            wait_for_completion  (bool) -- Wait util the command get executed
        """
        cmd = self.get_commands("failover")
        cmd = cmd.replace("failover_type", "Production Failback")
        cmd = cmd.replace("dest_node", dest_node)

        if "unix" in self.client_obj.os_info.lower():
            cmd = cmd.replace("failover_subtype", "Unplanned")

        self.log.info(f"Executing {cmd}")
        return self.execute_command(cmd, wait_for_completion)

    def test_failover(self, dest_node, wait_for_completion=False):
        """
        Peforms test failover on the given node name

        Args:
            dest_node            (str)  -- Destination node name
            wait_for_completion  (bool) -- Wait util the command get executed
        """
        cmd = self.get_commands("failover")
        cmd = cmd.replace("failover_type", "Test")
        cmd = cmd.replace("dest_node", dest_node)

        if "unix" in self.client_obj.os_info.lower():
            cmd = cmd.replace("failover_subtype", "Planned")

        self.log.info(f"Executing {cmd}")
        return self.execute_command(cmd, wait_for_completion)

    def test_failback(self, dest_node, wait_for_completion=False):
        """
        Peforms test failback on the given node name

        Args:
            dest_node            (str)  -- Destination node name
            wait_for_completion  (bool) -- Wait util the command get executed
        """
        cmd = self.get_commands("failover")
        cmd = cmd.replace("dest_node", dest_node)

        if "unix" in self.client_obj.os_info.lower():
            cmd = cmd.replace("failover_type", "TestFailback")
            cmd = cmd.replace("failover_subtype", "Planned")
        else:
            cmd = cmd.replace("failover_type", "Test Failback")

        self.log.info(f"Executing {cmd}")
        return self.execute_command(cmd, wait_for_completion)

    def production_maintenance(self, dest_node, wait_for_completion=False):
        """
        Peforms Production Maintenance on the given node name

        Args:
            dest_node            (str)  -- Destination node name
            wait_for_completion  (bool) -- Wait util the command get executed
        """
        cmd = self.get_commands("failover")
        cmd = cmd.replace("dest_node", dest_node)

        if "unix" in self.client_obj.os_info.lower():
            cmd = cmd.replace("failover_type", "ProductionMaintenance")
            cmd = cmd.replace("failover_subtype", "Planned")
        else:
            cmd = cmd.replace("failover_type", "Production Maintenance")

        self.log.info(f"Executing {cmd}")
        self.execute_command(cmd, wait_for_completion)

    def maintenance_failback(self, dest_node, wait_for_completion=False):
        """
        Peforms Maintenance Failback on the given node name

        Args:
            dest_node            (str)  -- Destination node name
            wait_for_completion  (bool) -- Wait util the command get executed
        """
        cmd = self.get_commands("failover")
        cmd = cmd.replace("dest_node", dest_node)

        if "unix" in self.client_obj.os_info.lower():
            cmd = cmd.replace("failover_type", "MaintenanceFailback")
            cmd = cmd.replace("failover_subtype", "Planned")
        else:
            cmd = cmd.replace("failover_type", "Maintenance Failback")

        self.log.info(f"Executing {cmd}")
        return self.execute_command(cmd, wait_for_completion)

    def reset_config(self):
        """Performs the reset config command on the node object
        """
        cmd = self.get_commands("resetconfig")
        self.log.info(f"Executing {cmd}")
        self.execute_command(cmd)
         
    def get_node_info(self, node_name=None):
        """
        Get the node info
        :param node_name: Default is self.node_name:
        :return List [Active/Standby, Status]:
        """
        if not node_name:
            node_name = self.node_name
        cmd = self.get_commands("get_node_info")
        cmd = cmd.replace("node_name", node_name)
        op = self.execute_command(cmd, True)
        if op[0] == 1:
            return "Failed to execute command"
        op = op[1].split("\n")
        for each_line in op:
            if node_name in each_line:
                status = " ".join(each_line.split()[1:3])
                break
        return status

    def latest_failover_details(self):
        """This functions parse the log fies, fetch the details
        of latest failover.

        Return (Dict):
        {
            "startDate": None,
            "startTime": None,
            "startDetail": None,

            "endDate": None,
            "endTime": None,
            "endDetail": None
        }
        """
        try:
            if self.machine:
                path = self.machine.join_path(self.log_directory, "CommServeLiveSync.log")
                summary = self.machine.read_file(path)
            else:
                summary = self.machine.get_log_file("CommServeLiveSync.log")
            started = "#######  STARTED"
            idx = summary.rfind(started)
            data = summary[idx - 120: idx + 200]
            pattern = data.split('\n')[1]
            ps = pattern.split()
            idx = ps.index("STARTED")
            start_date, start_time = ps[2], ps[3]
            start_detail = " ".join(ps[idx:-1])

            ended = "##############   "
            idx = summary.rfind(ended)
            data = summary[idx - 120:idx + 200]
            pattern = data.split('\n')[1]
            ps = pattern.split()
            idx = ps.index("##############")
            end_date, end_time = ps[2], ps[3]
            end_detail = " ".join(ps[idx + 1:-1])

            return {
                "startDate": start_date,
                "startTime": start_time,
                "startDetail": start_detail,

                "endDate": end_date,
                "endTime": end_time,
                "endDetail": end_detail
            }

        except Exception as e:
            raise Exception(f"Error while fetching details.\nException: {str(e)}")

