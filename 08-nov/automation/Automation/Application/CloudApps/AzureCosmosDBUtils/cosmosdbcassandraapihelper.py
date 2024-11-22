# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing CosmosDB Cassandra API instance operations


CockroachDBHelper:
    __init__()                        --   Initializes cockroachdb helper object

    add_instance()                    --   Add new instance for cockroachdb instance

    run_backup()                      --   Run backup on the cockroachdb instance

    run_restore()                      --  Run restore job

    add_credential()                   --  add credential for s3 bucket staging path

    add_client()                       --  Add cloud account

"""

from AutomationUtils import logger
from cvpysdk.client import Clients
from cvpysdk.agent import Agent
from cvpysdk.backupset import Backupset
from cvpysdk.credential_manager import Credentials


class CosmosDBCassandraAPIHelper():
    """Helper class to perform CosmosDB Cassandra API Instanceoperations"""

    def __init__(self, testcase):
        """Initialize instance of the CosmosDBCassandraAPIHelper class."""
        self.testcase = testcase
        self.log = logger.get_log()
        self.__commcell = testcase.commcell
        self._clients_object = Clients(testcase.commcell)
        self._cvpysdk_object = testcase.commcell._cvpysdk_object
        self._credentials_object = Credentials(self.__commcell)
        self.instance_name = testcase.instance_name
        self.cloudaccount = testcase.cloudaccount
        self.cloudaccount_name = testcase.cloudaccountname
        self.region = testcase.tcinputs.get("Region")
        self.cloudaccount_password = testcase.tcinputs.get(
            "CloudAccountPasword")
        self.access_nodes = testcase.tcinputs.get("AccessNodes").split(",")
        self.plan_name = testcase.tcinputs.get("Plan")
        self.instance_name = "CASSANDRA_API_" + testcase.id
        self.subscription_id = testcase.tcinputs.get("SubscriptionId")
        self.credential_name = "credential_" + testcase.id
        self.tenant_id = testcase.tcinputs.get("TenantID")
        self.application_id = testcase.tcinputs.get("ApplicationID")
        self.application_secret = testcase.tcinputs.get("ApplicationSecret")
        self.restore_no_of_stream = testcase.tcinputs.get("RestoreNoOfStream", 2)
        self.backupsetname = testcase.tcinputs.get("BackupSetName", "defaultBackupSet")
        self.subclientname = testcase.tcinputs.get("SubclientName", "default")
        self.agentname = "Cloud Apps"
        self.keyspace = testcase.keyspace
        self.tablename = testcase.tablename
        self.tablename2 = testcase.tablename2
        self.pathlist = testcase.pathlist
        account_dict = {}
        account_dict["cosmosdb_account"] = True
        account_dict["cloudaccount"] = self.cloudaccount
        account_dict["cloudaccount_name"] = self.cloudaccount_name
        account_dict["access_nodes"] = self.access_nodes
        account_dict["plan_name"] = self.plan_name
        account_dict["subscription_id"] = self.subscription_id
        account_dict["credential_name"] = self.credential_name
        account_dict["tenant_id"] = self.tenant_id
        account_dict["application_id"] = self.application_id
        account_dict["application_secret"] = self.application_secret
        account_dict["password"] = self.application_secret
        account_dict["cloudinstancetype"] = "AZURE_COSMOS_DB_CASSANDRA_API"
        self.account_dict = account_dict

    def add_credential(self):
        """add credential"""
        if not self._credentials_object.has_credential(self.credential_name):
            self._credentials_object.add_azure_cosmosdb_creds(
                credential_name=self.credential_name,
                tenant_id=self.tenant_id,
                application_id=self.application_id,
                application_secret=self.application_secret)

        self._credentials_object.refresh()
        if self._credentials_object.has_credential(self.credential_name):
            self.credential_id = self._credentials_object.get(
                self.credential_name).credential_id
            self.account_dict["credential_id"] = int(self.credential_id)
            self.log.info(
                "Successfully added credential %s",
                self.credential_name)
        else:
            raise Exception("failed to add credential")

    def add_client(self):
        """add cloud account"""
        self._client_object = self.__commcell.clients.add_azure_cosmosdb_client(
            client_name=self.cloudaccount_name,
            access_nodes=self.access_nodes,
            credential_name=self.credential_name,
            azure_options=self.account_dict)
        self._agent_object = Agent(
            client_object=self._client_object,
            agent_name=self.agentname)

    def add_instance(self):
        """Add cosmosdb cassandra api instance
            need several steps to add new instance:
                add credential,
                add cloud account (client),
                add instance,
                update default subclient properties
        """

        # delete existing instance
        if self.__commcell.clients.has_client(self.cloudaccount_name):
            self.log.info(
                "client %s exist, delete it and create new",
                self.cloudaccount_name)
            self.__commcell.clients.delete(self.cloudaccount_name)
        else:
            self.log.info(
                "no client with name %s,  create new",
                self.cloudaccount_name)

        # add credential
        self.add_credential()

        # add cloud account
        self.add_client()

        # add instance
        self.account_dict["clientid"] = self._client_object.client_id
        self._agent_object.instances.add_cosmosdb_instance(self.instance_name, **(self.account_dict))

        self._instance_object = self._agent_object.instances.get(
            self.instance_name)
        self.log.info(
            "Successfully created new instance with instance id %s",
            self._instance_object.instance_id)
        self._backupset_object = Backupset(
            instance_object=self._instance_object,
            backupset_name=self.backupsetname)
        self._subclient_object = self._backupset_object.subclients.get(
            self.subclientname)

        # update default sublient properties
        cloud_app_subclient_prop = {
            "cloudAppsSubClientProp": {
                "cloudBigQuerySubclient": {
                },
                "cloudBigtableSubclient": {
                },
                "cloudSpannerSubclient": {
                },
                "dynamoDBSubclient": {
                },
                "instanceType": 44,
                "rdsSubclient": {
                },
                "tableStorageSubclient": {
                }
            },
            "cloudDbContent": {
                "children": [
                    {
                        "allOrAnyChildren": True,
                        "displayName": self.cloudaccount,
                        "name": self.cloudaccount,
                        "negation": False,
                        "path": self.region,
                        "type": "StorageAccount"
                    }
                ]
            },
            "cloudDbFilter": {
            },
            "commonProperties": {
                "numberOfBackupStreams": 2
            }
        }
        self._subclient_object.update_properties(cloud_app_subclient_prop)

    def run_backup(self, backup_level="INCREMENTAL", wait_to_complete=True):
        """Initiates backup job with specified options
            on the current testcase subclient object
            and waits for completion.

            Args:
                backup_level            (str)   --  level of backup
                (Full/Incremental)

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

    def run_restore(self, srckeyspacename, destkeyspacename):
        """Restores database and verify the restored data
        Args:
            srckeyspacename        (str)    --    source database name
            destkeyspacename       (str)    --    destination database name
            tablename        str)     --    table name
        """

        restore_dict = {}
        restore_dict["no_of_streams"] = self.restore_no_of_stream
        restore_dict["destination_instance"] = self.instance_name
        restore_dict["destination_instance_id"] = self._instance_object.instance_id
        restore_dict["paths"] = ["/" + self.cloudaccount + "/" + self.keyspace]
        restore_dict["cloudinstancetype"] = "AZURE_COSMOS_DB_CASSANDRA_API"
        restore_dict["backupsetname"] = self.backupsetname
        restore_dict["unconditional_overwrite"] = True
        restore_dict["in_place"] = True
        restore_dict["sourcedatabase"] = srckeyspacename
        restore_dict["destinatinodatabase"] = destkeyspacename
        restore_dict["srcstorageaccount"] = self.cloudaccount
        restore_dict["deststorageaccount"] = self.cloudaccount

        job_object = self._instance_object.restore(
            restore_options=restore_dict)
        self.log.info(
            "wait for restore job %s to complete",
            job_object._job_id)
        job_object.wait_for_completion(return_timeout=5)

    def delete_instance(self):
        """delete test instances"""
        if self.__commcell.clients.has_client(self.cloudaccount_name):
            self.__commcell.clients.delete(self.cloudaccount_name)
