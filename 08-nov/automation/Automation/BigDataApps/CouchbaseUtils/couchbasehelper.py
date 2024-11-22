# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for couchbase cluster related operations.

Classes defined in this file:

    CouchbaseHelper:         Class for connecting to couchbase host and performing bucket operations.

        __init__()                 --  Constructor for connecting to couchbase host and running bucket operations

        check_bucket_exists()      --  checks if a bucket already exists in couchbase db

        load_sample_bucket()       --  loads a sample bucket into couchbase db

        create_test_bucket()       --  creates test bucket before running incremental backups

        add_items_to_test_bucket() --  adds documents to an existing bucket

        fetch_value_for_docid()    --  gets the document value based on the document id

        change_value_for_docid()   --  changes the document value based on the document id

        delete_sample_bucket()     --  deletes the sample bucket from couchbase db

        get_number_of_documents()  --  returns the number of documents present under the bucket


    Couchbase:               Class for creating/deleting instances and running backup/restore
                                 for couchbase instance Under Big data, It also has the methods to
                                 connect/disconnect to couchbase cluster, generate/delete test data
                                 and validate restored data

        __init__()                  --  constructor for creating couchbase object

        get_first_access_node_ip()  --  Returns ip address of access node

        add_couchbase_client()      --  create couchbase client

        add_credential()            --  creates a new credential

        get_client_details()        --  fetches the details of the couchbase client

        run_backup()                --  run backup job and verify if backup job completes

        run_restore()               --  run restore job and verify if restore job completes

        connect_to_db()             --  initiate connection to couchbase access node

        generate_test_data()        --  generates test data

        create_bucket()             --  creates test bucket before running incremental backups

        add_items_to_bucket()       --  adds new documents to the existing bucket

        get_value_for_docid()       --  gets the document value based on the document id

        update_value_for_docid()    --  updates the document value based on the document id

        get_number_of_docs()        --  gets number of documents under the bucket

        delete_buckets()            --  deletes buckets

        validate_restored_data()    --  verifies expected data are restored to couchbase cluster db

        validate_doc_value()        --  verifies value of the document after restore

        delete_couchbase_client()   --  deletes the couchbase client

"""

import time
import json
import requests
from AutomationUtils import logger
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.management.logic.buckets_logic import CreateBucketSettings
from cvpysdk.agent import Agent
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient
from cvpysdk.credential_manager import Credentials


class CouchbaseHelper():
    """Class for performing commvault operations"""

    def __init__(self, data_access_nodes, access_node_ip, user_name, password, port):
        """
        Constructor for connecting to cluster and running bucket operations
        Args:
                data_access_nodes (list)        -- access node names

                access_node_ip (str)     -- access node ip

                user_name (str)           -- couchbase admin username

                password (str)           -- couchbase admin password

                port(str)                -- port to connect to cluster

            Returns:
                object  -   connection object to the couchbase cluster

            Raises:
                Exception:
                    if failed to connect to the database

        """
        self.data_access_nodes = data_access_nodes
        self.access_node_ip = access_node_ip
        self.user_name = user_name
        self.password = password
        self.port = int(port)
        self.log = logger.get_log()

    def check_bucket_exists(self, port, bucket_names, access_node_ip, user_name, password):
        """
        checks if a specified bucket exists or not
        Args:
                port (str)              -- port number
                bucket_names(list)      -- names of the sample buckets
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster

            Returns:
                true/false  -   True / false based on the response

            Raises:
                Exception:
                    if failed to check for bucket's existence
        """
        try:
            for i in range(len(bucket_names)):
                response = requests.get('http://' + access_node_ip + ':' + port +
                                        '/pools/default/buckets/'+bucket_names[i],
                                        auth=(user_name, password))
            if response == "<Response [200]>":
                return True
            else:
                return False
        except Exception:
            raise Exception("unable to fetch bucket details")

    def load_sample_bucket(self, port, bucket_names, access_node_ip, user_name, password):
        """
        loads sample couchbase bucket
        Args:
                port (str)              -- port number
                bucket_names(list)      -- names of the sample buckets
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster

            Raises:
                Exception:
                    if failed to load sample bucket
        """
        try:
            for i in range(len(bucket_names)):
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
                check = self.check_bucket_exists(port, bucket_names[i], access_node_ip, user_name, password)
                if check == "<Response [200]>":
                    self.log.info("bucket already exists")
                else:
                    data = "[\"" + bucket_names[i] + "\"]"
                    requests.post('http://' + access_node_ip + ':' + port +
                                  '/sampleBuckets/install', headers=headers, data=data,
                                  auth=(user_name, password))
                    time.sleep(30)
                    self.log.info("sample bucket created")
        except Exception:
            raise Exception("unable to load sample bucket")

    def create_test_bucket(self, access_node_ip, user_name, password, test_bucket_name):
        """
        creates test buckets for running incremental backups
        Args:
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created

            Raises:
                Exception:
                    if failed to create test bucket
        """
        try:
            auth = PasswordAuthenticator(user_name, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            bucket = cluster.buckets()
            bucket.create_bucket(CreateBucketSettings(name=test_bucket_name, bucket_type="couchbase", ram_quota_mb=100))
            time.sleep(30)
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            for i in range(10):
                collection.upsert("test" + str(i), {
                    "place": "place" + str(i),
                    "name": "name" + str(i),
                })
        except Exception:
            raise Exception("unable to create test bucket")

    def add_items_to_test_bucket(self, access_node_ip, user_name, password, test_bucket_name):
        """
        adds items to existing buckets
        Args:
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created

            Raises:
                Exception:
                    if fails to add items
        """
        try:
            auth = PasswordAuthenticator(user_name, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            for i in range(10):
                collection.upsert("testinc" + str(i), {
                    "place": "place" + str(i),
                    "name": "name" + str(i),
                })
        except Exception:
            raise Exception("unable to create test bucket")

    def fetch_value_for_docid(self, access_node_ip, user_name, password, test_bucket_name, doc_id):
        """
        gets value for an existing document id
        Args:
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created
                doc_id(str)             -- id of a document

            Raises:
                Exception:
                    if fails to get value
        """
        try:
            auth = PasswordAuthenticator(user_name, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            return collection.get(doc_id).value
        except Exception:
            raise Exception("unable to get value for the key")

    def change_value_for_docid(self, access_node_ip, user_name, password, test_bucket_name, doc_id):
        """
        updates value for an existing document id
        Args:
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created
                doc_id(str)             -- id of a document

            Raises:
                Exception:
                    if fails to update value
        """
        try:
            auth = PasswordAuthenticator(user_name, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            content = {"place": "place_updated", "name": "name_updated"}
            collection.upsert(doc_id, content)
        except Exception:
            raise Exception("unable to get value for the key")

    def get_number_of_documents(self, port, bucket_names, access_node_ip, user_name, password):
        """
                gets number of documents present under sample couchbase bucket
                Args:
                        port (str)              -- port number
                        bucket_names(list)      -- names of the sample buckets
                        access_node_ip(str)     -- Ip address of the access node
                        user_name (str)         -- username to connect to cluster
                        password (str)          -- password to connect to cluster

                    Returns:
                        count  -- list containing number of documents present under each sample bucket

                    Raises:
                        Exception:
                            if failed to get number of documents under sample bucket
        """
        try:
            count = []
            for i in range(len(bucket_names)):
                response = requests.get('http://' + access_node_ip + ':' + port +
                                        '/pools/default/buckets/'+bucket_names[i],
                                        auth=(user_name, password))
                num_docs = response.json()
                self.log.info("returning number of documents under the sample bucket")
                test = (num_docs['basicStats']['itemCount'])
                count.append(test)
            return count

        except Exception:
            raise Exception("unable to get number of documents")

    def delete_sample_buckets(self, port, bucket_names, access_node_ip, user_name, password):
        """
        deletes sample couchbase bucket
        Args:
                port (str)              -- port number
                bucket_names(list)      -- names of the sample buckets
                access_node_ip(str)     -- Ip address of the access node
                user_name (str)         -- username to connect to cluster
                password (str)          -- password to connect to cluster

            Raises:
                Exception:
                    if failed to delete sample bucket
        """
        try:
            for i in range(len(bucket_names)):
                requests.delete('http://' + access_node_ip + ':' + port +
                                '/pools/default/buckets/'+bucket_names[i],
                                auth=(user_name, password))
                self.log.info("sample bucket "+bucket_names[i]+" deleted")
        except Exception:
            raise Exception("Unable to delete sample bucket")


class Couchbase:

    def __init__(self, testcase):
        """Constructor for creating the couchbase object"""

        self.__commcell = testcase.commcell
        self.__couchbase = None
        self._credentials_object = Credentials(self.__commcell)
        self.instance_name = "COUCHBASE_" + testcase.id
        self.credential_name = "credential_" + testcase.id
        self.data_access_nodes = testcase.tcinputs.get("data_access_nodes")
        self.access_node_ip = self.get_first_access_node_ip(self.data_access_nodes)
        self.port = testcase.tcinputs.get("port")
        self.user_name = testcase.tcinputs.get("user_name")
        self.password = testcase.tcinputs.get("password")
        self.staging_type = testcase.tcinputs.get("staging_type")
        self.bucket_names = testcase.bucket_names
        self.service_host = testcase.tcinputs.get("service_host")
        self.staging_path = testcase.tcinputs.get("staging_path")
        self.plan_name = testcase.tcinputs.get("plan_name")
        self.aws_access_key = testcase.aws_access_key
        self.aws_secret_key = testcase.aws_secret_key
        self.restore_no_of_stream = testcase.tcinputs.get("RestoreNoOfStream", 2)
        self.agentname = "Big Data Apps"
        self.backupsetname = testcase.tcinputs.get("BackupSetName", "defaultBackupSet")
        self.subclientname = testcase.tcinputs.get("SubclientName", "default")
        self.log = logger.get_log()

    def get_first_access_node_ip(self, data_access_nodes):
        """Returns ip address of the couchbase access node
        Args:
                dataAccessNodes (list)      --      data access nodes list
        """
        cl_machine = self.__commcell.clients.get(data_access_nodes[0])
        hostname = str(cl_machine.client_hostname)
        return hostname

    def add_couchbase_client(self):
        """
        Adds new couchbase client by calling comcell object of cvpysdk

         Args:
             Nothing

        Returns:
            client  --  client object of the newly created couchbase client

        """
        self.add_credential()
        if self.__commcell.clients.has_client(self.instance_name):
            self.log.info('Client exists. Deleting it and creating')
            self.__commcell.clients.delete(self.instance_name)

        self.client = self.__commcell.clients.add_couchbase_client(
            self.instance_name, self.data_access_nodes, self.user_name, self.password, self.port, self.staging_type,
            self.staging_path, self.credential_name, self.service_host, self.plan_name
        )
        return self.client


    def add_credential(self):
        """adds new credential"""
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

    def get_client_details(self, client_object,
                           backupset_name="defaultbackupset",
                           subclient_name="default"):
        """
        Returns a dictionary containing client_obj, instance_obj,
        backupset_obj and agent_obj

        Args:
            client_object   (object)    --  couchbase client object

            backupset_name  (str)       --  name of the backupset entity
                default: defaultbackupset

            subclient_name  (str)       --  name of the subclient entity
                default: default

        Returns:
             client_details (dict)      --  dictionary containing client_obj, instance_obj,
             backupset_obj and agent_obj

        """

        req_agent = client_object.agents.get("big data apps")
        req_instance = req_agent.instances.get(client_object.client_name)
        req_backupset = req_agent.backupsets.get(backupset_name)
        req_subclient = req_backupset.subclients.get(subclient_name)
        req_subclient_id = req_subclient.subclient_id

        client_details = {
            "client": client_object,
            "agent": req_agent,
            "instance": req_instance,
            "backupset": req_backupset,
            "subclient": req_subclient,
            "subclient_id": req_subclient_id
        }

        return client_details

    def run_backup(self, client_object, client_details, subclient_details=None, backup_type="Full"):
        """
            Runs backup on the specified couchbase client object. Runs a Full backup by default

            Args:
                 client_object  (obj)       --  couchbase client object

                 subclient_details (obj)    --  Contains subclient_object
                                                Ex: Subclient class instance for Subclient: "default" of Backupset:
                                                "defaultbackupset"}

                 backup_type(str)           --  Type of backup - Full/Incremental

            Return:
                  tuple: A tuple containing two elements:
                  - str: The job ID of the backup job.
        """

        self.log.info("Starting Backup Job")
        if subclient_details is None:
            req_agent = client_object.agents.get(self.agentname)
            req_backupset = req_agent.backupsets.get(self.backupsetname)
            req_subclient = req_backupset.subclients.get(self.subclientname)
        else:
            req_subclient = subclient_details
        job_obj = req_subclient.backup(backup_type)
        self.log.info("Waiting For Completion Of Backup Job With Job ID: %s",
                      str(job_obj.job_id))
        if not job_obj.wait_for_completion():
            raise Exception(
                "Failed To Run Backup {0} With Error {1}".format(
                    str(job_obj.job_id), job_obj.delay_reason
                )
            )

        if not job_obj.status.lower() == "completed":
            raise Exception(
                "Job {0} is not completed and has job status: {1}".format(
                    str(job_obj.job_id), job_obj.status
                )
            )
        self.log.info(
            "Successfully Finished Backup Job %s", str(job_obj.job_id)
        )

    def run_restore(self, overwrite=False, wait_to_complete=True, instance_level_restore = True):
            """Restores database and verify the restored data
            Args:
                overwrite             (bool)    --    Specifies whether data should be overwritten or not during restore
                wait_to_complete      (bool)    --    Specifies whether to wait until restore job finishes.
                instance_level_restore(bool)    --    Specifies whether the restore is from instance or subclient level
            """
            self._agent_object = Agent(
                client_object=self.client,
                agent_name=self.agentname)
            self._instance_object = self._agent_object.instances.get(
                self.instance_name)
            client_details = self.get_client_details(self.client)

            restore_dict = {}
            restore_dict["no_of_streams"] = self.restore_no_of_stream
            restore_dict["multinode_restore"] = True
            restore_dict["overwrite"] = overwrite
            restore_dict["destination_instance"] = self.instance_name
            restore_dict["destination_instance_id"] = self._instance_object.instance_id
            restore_dict["destination_client_id"] = self.client.client_id
            restore_dict["destination_client_name"] = self.client.client_name
            restore_dict["client_type"] = 29
            restore_dict["destination_appTypeId"] = 64
            restore_dict["backupset_name"] = "DefaultBackupSet"

            if instance_level_restore:
                restore_dict["subclient_id"] = -1
                restore_dict["_type_"] = 5
            else:
                restore_dict["subclient_id"] = client_details.req_subclient_id
                restore_dict["_type_"] = 7

            restore_content = []
            db_paths = []
            for i in self.bucket_names:
                restore_content.append({"srcEntityName": '/'+i, "destEntityName": i})
                db_paths.append('/'+i)
            restore_dict["restore_items"] = restore_content
            restore_dict["paths"] = db_paths
            restore_dict["accessnodes"] = self.data_access_nodes

            job_object = self._instance_object.restore(
                restore_options=restore_dict)
            self.log.info(
                "wait for restore job %s to complete",
                job_object._job_id)
            job_object.wait_for_completion(return_timeout=30)

    def connect_to_db(self):
        """initiate connection to couchbase access node"""
        self.__couchbase = CouchbaseHelper(self.data_access_nodes,
                                           self.access_node_ip,
                                           self.user_name,
                                           self.password,
                                           self.port)

    def generate_test_data(self):
        """generates test data"""
        self.__couchbase.load_sample_bucket(self.port, self.bucket_names,
                                            self.access_node_ip, self.user_name, self.password)

    def create_bucket(self, test_bucket_name):
        """creates buckets for incr backup"""
        self.__couchbase.create_test_bucket(self.access_node_ip, self.user_name, self.password, test_bucket_name)

    def add_items_to_bucket(self, test_bucket_name):
        """add items to already existing bucket"""
        self.__couchbase.add_items_to_test_bucket(self.access_node_ip, self.user_name, self.password,
                                                  test_bucket_name)

    def get_value_for_docid(self, test_bucket_name, doc_id):
        """gets value of a document based on the id"""
        self.__couchbase.fetch_value_for_docid(self.access_node_ip, self.user_name, self.password,
                                               test_bucket_name, doc_id)

    def update_value_for_docid(self, test_bucket_name, doc_id):
        """updates value of a document based on the id"""
        self.__couchbase.change_value_for_docid(self.access_node_ip, self.user_name, self.password, test_bucket_name,
                                                doc_id)

    def get_number_of_docs(self, buckets):
        """gets number of documents under the bucket"""
        num_of_docs = self.__couchbase.get_number_of_documents(self.port, buckets,
                                                               self.access_node_ip, self.user_name, self.password)
        return num_of_docs

    def delete_buckets(self, buckets):
        """deletes bucket"""
        self.__couchbase.delete_sample_buckets(self.port, buckets,
                                               self.access_node_ip, self.user_name, self.password)

    def validate_restored_data(self, items, buckets):
        """validates restore data"""
        restored_items = self.__couchbase.get_number_of_documents(self.port, buckets,
                                                                  self.access_node_ip, self.user_name, self.password)
        if restored_items == items:
            self.log.info("restored data matches original data")
        else:
            self.log.info("restored data does not match with original data")

    def validate_doc_value(self, value_for_docid, bucket_name, doc_id):
        """validates document value after restore"""
        value_after_restore = self.__couchbase.fetch_value_for_docid(self.access_node_ip, self.user_name, self.password,
                                                                     bucket_name, doc_id)
        if value_after_restore == value_for_docid:
            self.log.info("document value after restore matches value before restore")
        else:
            self.log.info("document value after restore doesn't match value before restore")

    def delete_couchbase_client(self):
        """deletes the client"""
        if self.__commcell.clients.has_client(self.instance_name):
            self.log.info('Client exists. Deleting it')
            self.__commcell.clients.delete(self.instance_name)
        else :
            self.log.info('client does not exist')