# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for validating tppm for webserver/index server

    WebServerTPPM()

         __init__()                              --  Initialize the WebServerTPPM object

        get_cs_sql_port()                        --  Returns the port number of sql running on CS

        is_sql_port_open()                       --  Checks whether webserver client is able to ping CS sql port or not

        validate_firewall_entry()                --  Validates whether tppm entry got added in firewalltppm table or not

        validate_tppm_in_log()                   --  Validates whether dynamic tppm kicked in or not by checking dm2web log

        cs_sql_operations()                      --  Kills or brings up sql service on CS

        cs_firewall_setup()                      --  Make sure cs firewall services are up & running
"""
import time

from AutomationUtils import database_helper, logger
from AutomationUtils.database_helper import get_csdb, CommServDatabase
from AutomationUtils.machine import Machine
from dynamicindex.utils import constants as dynamic_constants


class WebServerTPPM():
    """Helper class for webserver dynamic tppm validation"""

    def __init__(self, commcell, client_name, cs_machine_user=None, cs_machine_password=None):
        """
        Initialize the WebServerTPPM object

            Args:

                commcell                -   Instance of commcell class

                client_name             -   Name of webserver client

                cs_machine_user         -   Username for accessing cs machine

                cs_machine_password     --  Password for accessing CS machine
        """
        self.commcell = commcell
        self.client_obj = self.commcell.clients.get(client_name)
        self.machine_obj = Machine(machine_name=client_name, commcell_object=commcell)
        self._sql_port_prop = 'cvSQLServerPort'
        database_helper.set_csdb(CommServDatabase(self.commcell))
        self._csdb = get_csdb()
        self.log = logger.get_log()
        self.cs_client_obj = self.commcell.clients.get(self.commcell.commserv_hostname)
        self.cs_machine_obj = Machine(machine_name=self.commcell.commserv_hostname, commcell_object=self.commcell)
        self.cs_machine_obj_cred = None
        if cs_machine_password and cs_machine_user:
            self.cs_machine_obj_cred = Machine(machine_name=self.commcell.commserv_hostname, username=cs_machine_user,
                                               password=cs_machine_password)

    def validate_tppm_in_log(self):
        """Validates whether dynamic tppm kicked in or not by checking dm2web log

            Args:

                None

            Raises:

                Exception:

                    if failed to find related logs
        """
        pattern = f'Opening tunneling to CSDB port: [{self.get_cs_sql_port()}]'
        self.log.info(f"Pattern formed for checking dm2web.log -> {pattern}")
        log_lines = self.machine_obj.get_logs_for_job_from_file(
            log_file_name=dynamic_constants.DM2_WEB_LOG_FILE, search_term=pattern)
        if not log_lines:
            raise Exception('Unable to find tppm related log lines in dm2web')
        self.log.info(f"Expected log lines found in dm2web.log - {log_lines}")

    def get_cs_sql_port(self):
        """Returns the port number of sql running on CS

                Args:

                    None

                Returns:

                    str - sql port number

                Raises:

                    Exception:

                        if failed to find sql port client property

        """
        _query = f"select attrval from app_clientprop(nolock) where componentNameId=2 and attrname='{self._sql_port_prop}' and modified=0"
        self._csdb.execute(_query)
        port = str(self._csdb.fetch_one_row()[0])
        if not port:
            raise Exception("Failed to find sql port number in client properties")
        self.log.info(f"CS Sql is running with port no - {port}")
        return port

    def validate_firewall_entry(self):
        """Validates whether tppm entry got added in firewalltppm table or not for webserver client

            Args:

                None

            Returns:

                bool  -- whether tppm entry exists or not
        """
        port = self.get_cs_sql_port()
        _query = f"select count(*) as tppm from APP_FirewallTPPM(nolock) where toPortNumber = {port} and fromEntityId={self.client_obj.client_id} and fromEntityType=3 and tppmType=9"
        self._csdb.execute(_query)
        exists = int(self._csdb.fetch_one_row()[0])
        if not exists:
            self.log.info("Failed to find sql port number tppm entry")
            return False
        return True

    def is_sql_port_open(self):
        """Checks whether client is able to ping CS sql port or not

            Args:

                None

            Returns:

                bool    --  Specifies whether CS sql port is accessible from webserver or not
        """
        port = self.get_cs_sql_port()
        return self.machine_obj.run_cvping(destination=self.commcell.commserv_hostname, port=port)

    def cs_sql_operations(self, start=False):
        """Kills or brings up CS sql related service

            Args:

                start           (bool)      --  Flag denoting sql service to be up or down (Default - False)

            Returns:

                None
        """
        self.log.info(f"CS sql operation requested for start - {start}")
        if self.cs_machine_obj.os_info.lower() == 'windows':
            if not start:
                self.cs_machine_obj.kill_process(process_name="sql*")
                self.log.info("All Sql related process is killed")
            else:
                if not self.cs_machine_obj_cred:
                    raise Exception(
                        "Machine object has to be initialised with credentials. Please pass CS Machine username/Password")
                sql_services = ['MSSQL$COMMVAULT', 'SQLAgent$COMMVAULT', 'SQLBrowser', 'SQLTELEMETRY$COMMVAULT']
                for _service in sql_services:
                    self.cs_machine_obj_cred.execute_command(command=f'Start-Service -Name "{_service}"')
                    self.log.info(f"Service [{_service}] started on CS")
                    time.sleep(10)
                time.sleep(120)
            return
        raise Exception("Not implemented for Unix as dynamic port for sql is not supported")

    def cs_firewall_setup(self):
        """Make sure cs firewall services are up & running

            Args:
                None

            Returns:
                None
        """
        if self.cs_machine_obj.os_info.lower() == 'windows':
            self.cs_client_obj.start_service(service_name="BFE")
            self.log.info("BFE service is started")
            time.sleep(60)
            self.cs_client_obj.start_service(service_name="MpsSvc")
            self.log.info("MpsSvc service is started")
            return
        raise Exception("Not implemented for Unix")
