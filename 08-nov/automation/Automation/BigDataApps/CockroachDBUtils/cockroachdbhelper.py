# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing cockroachDB operations


CockroachDBHelper:
    __init__()                        --  initializes cockroachdb helper object

    add_instance()                    --  add new instance for cockroachdb instance

    run_backup()                      --  Run backup on the cockroachdb instance

    run_restore()                     --  Run restore job

    add_credential()                   -- add credential for s3 bucket staging path

"""

from AutomationUtils import logger
from cvpysdk.client import Clients
from cvpysdk.agent import Agent
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient
from cvpysdk.credential_manager import Credentials


class CockroachDBHelper(object):
    """Helper class to perform cockroachDB operations"""

    def __init__(self, testcase):
        """Initialize instance of the CockroachDBHelper class."""
        self.testcase = testcase
        self.log = logger.get_log()
        self.__commcell = testcase.commcell
        self._clients_object = Clients(testcase.commcell)
        self._cvpysdk_object = testcase.commcell._cvpysdk_object
        self._credentials_object = Credentials(self.__commcell)
        self.credential_name = testcase.credential_name
        self.cockroachdb_name = testcase.cockroachdb_name
        self.access_nodes = testcase.tcinputs.get("access_nodes").split(",")
        self.cockroachdb_host = testcase.tcinputs.get("cockroachdb_host")
        self.plan_name = testcase.tcinputs.get("plan")
        self.backupsetname = testcase.tcinputs.get("BackupSetName", "defaultBackupSet")
        self.subclientname = testcase.tcinputs.get("SubclientName", "default")
        self.agentname = "Big Data Apps"
        self.db_username = testcase.db_username
        self.db_password = testcase.db_password
        self.cockroachdb__port = testcase.tcinputs.get("cockroachdb_port")
        self.use_iamrole = testcase.tcinputs.get("use_iamrole")
        self.use_ssl = testcase.tcinputs.get("use_ssl")
        self.s3_service_host = testcase.tcinputs.get("s3_service_host")
        self.s3_staging_path = testcase.tcinputs.get("s3_staging_path")
        self.aws_access_key = testcase.aws_access_key
        self.aws_secret_key = testcase.aws_secret_key
        self.sslrootcert = testcase.sslrootcert
        self.sslcert = testcase.sslcert
        self.sslkey = testcase.sslkey
        self.dbname = testcase.dbname
        self.destdbname = testcase.destdbname

    def add_credential(self):
        """add credential"""
        if not self._credentials_object.has_credential(self.credential_name):
            self._credentials_object.add_aws_s3_creds(
                credential_name=self.credential_name,
                access_key_id=self.aws_access_key,
                secret_access_key=self.aws_secret_key)
        self._credentials_object.refresh()
        if self._credentials_object.has_credential(self.credential_name):
            self.log.info("credential is created successfully")
        else:
            raise Exception("failed to add credential")

    def add_instance(self):
        """Creates cockroachDB instance.
            Raises:
                Exception - Any error occur during Instance creation

        """
        if self.__commcell.clients.has_client(self.cockroachdb_name):
            self.log.info(
                "client %s exist, delete it and create new",
                self.cockroachdb_name)
            self.__commcell.clients.delete(self.cockroachdb_name)
        else:
            self.log.info(
                "no client with name %s,  create new",
                self.cockroachdb_name)

        self.add_credential()

        self._client_object = self.__commcell.clients.add_cockroachdb_client(
            new_client_name=self.cockroachdb_name,
            s3_credential_name=self.credential_name,
            cockroachdb_host=self.cockroachdb_host,
            cockroachdb_port=self.cockroachdb__port,
            db_username=self.db_username,
            db_password=self.db_password,
            sslcert=self.sslcert,
            sslkey=self.sslkey,
            sslrootcert=self.sslrootcert,
            s3_service_host=self.s3_service_host,
            s3_staging_path=self.s3_staging_path,
            accessnodes=self.access_nodes,
            plan_name=self.plan_name)

        self._agent_object = Agent(
            client_object=self._client_object,
            agent_name=self.agentname)
        self._instance_object = self._agent_object.instances.get(
            self.cockroachdb_name)
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
                Exception - Any error occurred while running backup

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

    def run_restore(self, srcdbname, destdbname, wait_to_complete=True):
        """Restores database and verify the restored data
        Args:
            srcdbname        (str)    --    source database name
            destdbname       (str)    --    destination database name
            wait_to_complete  (bool)  --  Specifies whether to wait until restore job finishes.
        """

        restore_dict = {}
        restore_dict["no_of_streams"] = 2
        restore_dict["multinode_restore"] = True
        restore_dict["destination_instance"] = self.cockroachdb_name
        restore_dict["destination_instance_id"] = self._instance_object.instance_id
        restore_dict["paths"] = ["/"]
        restore_dict["cockroachdb_restore"] = True
        restore_dict["destination_client_id"] = self._client_object.client_id
        restore_dict["destination_client_name"] = self._client_object.client_name
        restore_dict["overwrite"] = True
        restore_dict["client_type"] = 29

        restore_dict["destination_appTypeId"] = 64
        restore_dict["backupset_name"] = self.backupsetname
        restore_dict["_type_"] = 5
        restore_dict["subclient_id"] = -1
        restore_dict["fromtable"] = srcdbname
        restore_dict["totable"] = destdbname
        restore_dict["accessnodes"] = self.access_nodes

        restore_json = self._instance_object._restore_bigdataapps_option_json(
            value=restore_dict)
        self.log.info(restore_json)
        job_object = self._instance_object._process_restore_response(
            restore_json)
        if wait_to_complete:
            self.log.info(
                "wait for restore job %s to complete",
                job_object._job_id)
            job_object.wait_for_completion(return_timeout=5)

    def delete_instance(self):
        """delete test instances"""
        if self.__commcell.clients.has_client(self.cockroachdb_name):
            self.__commcell.clients.delete(self.cockroachdb_name)
