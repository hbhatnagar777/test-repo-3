# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Cassandra operations


CassandraHelper:
    __init__()                 --  initializes cassandra helper object

    add_instance()             --  creates new instance for cassandra big data apps

    run_backup()               --  Run backup on the cassandra instnace

    run_restore()              --  Initiates restore of data and validate the restored data

    delete_instance()          --  Delete test instance
"""
from AutomationUtils import logger
from cvpysdk.client import Clients
from cvpysdk.agent import Agent
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient


class CassandraHelper(object):
    """Helper class to perform cassandra operations using restapi"""

    def __init__(self, testcase):
        """Initialize instance of the CassandraHelper class."""
        self.testcase = testcase
        self.log = logger.get_log()
        self.__commcell = testcase.commcell
        self._clients_object = Clients(testcase.commcell)
        self._cvpysdk_object = testcase.commcell._cvpysdk_object
        self._services = testcase.commcell._services
        self.cql_host = testcase.tcinputs.get("cql_host")
        self.plan_name = testcase.tcinputs.get("plan")
        self.cql_username = testcase.cql_username
        self.cql_password = testcase.cql_password
        self.cql_port = testcase.tcinputs.get("cql_port")
        self.cassandra_server_name = testcase.cassandra_server_name
        self.gatewaynode = testcase.tcinputs.get("gateway_node")
        self.config_file_path = testcase.tcinputs.get("config_file_path")
        self.backupsetname = testcase.tcinputs.get("BackupSetName", "defaultBackupSet")
        self.subclientname = testcase.tcinputs.get("SubclientName", "default")
        self.agentname = "Big Data Apps"
        self.jmx_port = testcase.tcinputs.get("jmx_port")
        self.jmx_port_int = int(self.jmx_port)
        self.cql_port_int = int(self.cql_port)
        self.jmx_username = testcase.jmx_username
        self.jmx_password = testcase.jmx_password
        self.keystore = testcase.ssl_keystore
        self.keystorepwd = testcase.ssl_keystorepwd
        self.truststore = testcase.ssl_truststore
        self.truststorepwd = testcase.ssl_truststorepwd
        self.staging_path = testcase.tcinputs.get("staging_path")
        self.datapath = testcase.tcinputs.get("datapath")
        self.javapath = testcase.tcinputs.get("javapath")

    def add_instance(self):
        """Creates cassandra instance.

            Raises:
                Exception - Any error occured during Instance creation
        """
        try:
            if self.__commcell.clients.has_client(self.cassandra_server_name):
                self.log.info(
                    "client %s exist, delete it and create new instance",
                    self.cassandra_server_name)
                self.__commcell.clients.delete(self.cassandra_server_name)
        except BaseException:
            self.log.info("no client with name %s", self.cassandra_server_name)

        self._client_object = self.__commcell.clients.add_cassandra_client(
            new_client_name=self.cassandra_server_name,
            gatewaynode=self.gatewaynode,
            cql_port=self.cql_port,
            cql_username=self.cql_username,
            cql_password=self.cql_password,
            jmx_port=self.jmx_port,
            config_file_path=self.config_file_path,
            plan_name=self.plan_name)

        self._agent_object = Agent(
            client_object=self._client_object,
            agent_name=self.agentname)
        self._instance_object = self._agent_object.instances.get(
            self.cassandra_server_name)
        self._backupset_object = Backupset(
            instance_object=self._instance_object,
            backupset_name=self.backupsetname)
        self._subclient_object = Subclient(
            backupset_object=self._backupset_object,
            subclient_name=self.subclientname)

    def run_backup(self, backup_level="INCREMENTAL",
                   wait_to_complete=True):
        """Initiates backup job with specified options
            on the current testcase subclient object
            and waits for completion.

        Args:
            backup_level            (str)   --  level of backup (Full/Incremental)

            wait_to_complete        (bool)  --  Specifies whether to wait until job finishes.

        Raises:
            Exception - Any error occurred while running backup or
            backup didn't complete successfully.

        """

        self.log.info("Starting %s Backup ", backup_level)
        job = self._subclient_object.backup()

        if job.backup_level is None:
            job_type = job.job_type
        else:
            job_type = job.backup_level

        if wait_to_complete:
            self.log.info(
                "Waiting for completion of %s backup with Job ID: %s", job_type, str(
                    job.job_id))
            job.wait_for_completion()

    def run_restore(self, keyspacename, wait_to_complete=True):
        """Restores keyspace

        Args
            keyspacename (str)     -- keyspace name

            wait_to_complete (bool)  - wait for job to completed if True

        """
        restore_dict = {}
        restore_dict["no_of_streams"] = 2
        restore_dict["multinode_restore"] = True
        restore_dict["destination_instance"] = self.cassandra_server_name
        restore_dict["destination_instance_id"] = self._instance_object.instance_id
        restore_dict["paths"] = ["/" + keyspacename]
        restore_dict["cassandra_restore"] = True
        restore_dict["outofPlaceRestore"] = True
        restore_dict["runStageFreeRestore"] = False
        restore_dict["recover"] = True
        restore_dict["replaceDeadNode"] = False
        restore_dict["stagingLocation"] = self.staging_path
        restore_dict["useSSTableLoader"] = True
        restore_dict["runLogRestore"] = False
        restore_dict["nodeMap"] = []
        restore_dict["dockerNodeMap"] = []
        restore_dict["DBRestore"] = True
        restore_dict["truncateTables"] = True
        restore_dict["destination_appTypeId"] = 64
        restore_dict["backupset_name"] = self.backupsetname
        restore_dict["_type_"] = 5
        restore_dict["subclient_id"] = -1

        restore_json = self._instance_object._restore_bigdataapps_option_json(
            value=restore_dict)
        job_object = self._instance_object._process_restore_response(
            restore_json)
        self.log.info(
            "wait for restore job %s to complete",
            job_object._job_id)
        if wait_to_complete:
            job_object.wait_for_completion(return_timeout=5)

    def delete_instance(self):
        """delete test instance"""
        if self.__commcell.clients.has_client(self.cassandra_server_name):
            self.__commcell.clients.delete(self.cassandra_server_name)
