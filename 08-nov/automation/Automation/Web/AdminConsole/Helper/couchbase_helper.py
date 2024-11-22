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

        add_items_to_test_bucket   --  adds documents to an existing bucket

        fetch_value_for_docid      --  gets the document value based on the document id

        change_value_for_docid     --  changes the document value based on the document id

        delete_sample_bucket()     --  deletes the sample bucket from couchbase db

        get_number_of_documents()  --  returns the number of documents present under the bucket


    Couchbase:               Class for creating/deleting instances and running backup/restore
                                 for couchbase instance Under Big data, It also has the methods to
                                 connect/disconnect to couchbase cluster, generate/delete test data
                                 and validate restored data

        __init__()                  --  constructor for creating couchbase object

        get_access_node_ip()        --  Returns ip address of access node

        create_couchbase_instance() --  create couchbase pseudo client

        __check_job_restartability  --  Method for validating restartability by suspending or resuming a job

        wait_for_job_completion     --  Method to wait till job completes

        verify_backup()             --  run backup job and verify if backup job completes

        verify_restore()            --  run restore job and verify if restore job completes

        delete_couchbase_instance() --  delete couchbase instance and pseudo client

        generate_test_data()        --  generates test data

        create_bucket()             --  creates test bucket before running incremental backups

        add_items_to_bucket()       --  adds new documents to the existing bucket

        get_value_for_docid()       --  gets the document value based on the document id

        update_value_for_docid()    --  updates the document value based on the document id

        validate_restored_data()    --  verifies expected data are restored to couchbase cluster db

        validate_doc_value()        --  verifies value of the document after restore

"""
import requests
import time

from Web.Common.page_object import TestStep
from Web.AdminConsole.Bigdata.instances import Instances, CouchbaseServer
from Web.AdminConsole.Bigdata.details import Overview, CouchbaseOperations
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils import logger
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.management.logic.buckets_logic import CreateBucketSettings


class CouchbaseHelper():
    """
        Helper class for Couchbase cluster related operations
    """

    def __init__(self, access_nodes, access_node_ip, username, password, port):
        """
        Constructor for connecting to cluster and running bucket operations
        Args:
                access_nodes (list)        -- access node names

                access_node_ip (str)     -- access node ip

                username (str)           -- couchbase admin username

                password (str)           -- couchbase admin password

                port(str)                -- port to connect to cluster

            Returns:
                object  -   connection object to the couchbase cluster

            Raises:
                Exception:
                    if failed to connect to the database

        """
        self.access_nodes = access_nodes
        self.access_node_ip = access_node_ip
        self.username = username
        self.password = password
        self.port = int(port)
        self.log = logger.get_log()

    def check_bucket_exists(self, port, bucket_names, access_node_ip, username, password):
        """
        checks if a specified bucket exists or not
        Args:
                port (str)              -- port number
                bucket_names(list)      -- names of the sample buckets
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
                password (str)          -- password to connect to cluster

            Returns:
                response  -   response returned by the API

            Raises:
                Exception:
                    if failed to check for bucket's existence
        """
        try:
            for i in range(len(bucket_names)):
                response = requests.get('http://' + access_node_ip + ':' + port +
                                        '/pools/default/buckets/'+bucket_names[i],
                                        auth=(username, password))
            self.log.info("returning response regarding bucket's existence")
            return response

        except Exception:
            raise Exception("unable to fetch bucket details")

    def load_sample_bucket(self, port, bucket_names, access_node_ip, username, password):
        """
        loads sample couchbase bucket
        Args:
                port (str)              -- port number
                bucket_names(list)      -- names of the sample buckets
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
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
                check = self.check_bucket_exists(port, bucket_names[i], access_node_ip, username, password)
                if check == "<Response [200]>":
                    self.log.info("bucket already exists")
                else:
                    data = "[\""+bucket_names[i]+"\"]"
                    requests.post('http://' + access_node_ip + ':' + port +
                                  '/sampleBuckets/install', headers=headers, data=data,
                                  auth=(username, password))
                    time.sleep(60)
                    self.log.info("sample bucket created")
        except Exception:
            raise Exception("unable to load sample bucket")

    def create_test_bucket(self, access_node_ip, username, password, test_bucket_name):
        """
        creates test buckets for running incremental backups
        Args:
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created

            Raises:
                Exception:
                    if failed to create test bucket
        """
        try:
            auth = PasswordAuthenticator(username, password)
            cluster = Cluster.connect('couchbase://'+access_node_ip, ClusterOptions(auth))
            bucket = cluster.buckets()
            bucket.create_bucket(CreateBucketSettings(name=test_bucket_name, bucket_type="couchbase", ram_quota_mb=100))
            time.sleep(60)
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            for i in range(10):
                collection.upsert("test"+str(i), {
                    "place": "place"+str(i),
                    "name": "name"+str(i),
                })
            time.sleep(60)
        except Exception:
            raise Exception("unable to create test bucket")

    def add_items_to_test_bucket(self, access_node_ip, username, password, test_bucket_name):
        """
        adds items to existing buckets
        Args:
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created

            Raises:
                Exception:
                    if fails to add items
        """
        try:
            auth = PasswordAuthenticator(username, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            for i in range(10):
                collection.upsert("testinc" + str(i), {
                    "place": "place" + str(i),
                    "name": "name" + str(i),
                })
            time.sleep(60)
        except Exception:
            raise Exception("unable to create test bucket")

    def fetch_value_for_docid(self, access_node_ip, username, password, test_bucket_name, doc_id):
        """
        gets value for an existing document id
        Args:
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created
                doc_id(str)             -- id of a document

            Raises:
                Exception:
                    if fails to get value
        """
        try:
            auth = PasswordAuthenticator(username, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            return collection.get(doc_id).value
        except Exception:
            raise Exception("unable to get value for the key")

    def change_value_for_docid(self, access_node_ip, username, password, test_bucket_name, doc_id):
        """
        updates value for an existing document id
        Args:
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
                password (str)          -- password to connect to cluster
                test_bucket_name(str)   -- test bucket name to be created
                doc_id(str)             -- id of a document

            Raises:
                Exception:
                    if fails to update value
        """
        try:
            auth = PasswordAuthenticator(username, password)
            cluster = Cluster.connect('couchbase://' + access_node_ip, ClusterOptions(auth))
            cb = cluster.bucket(test_bucket_name)
            collection = cb.default_collection()
            content = {"place": "place_updated", "name": "name_updated"}
            collection.upsert(doc_id, content)
        except Exception:
            raise Exception("unable to get value for the key")

    def get_number_of_documents(self, port, bucket_names, access_node_ip, username, password):
        """
                gets number of documents present under sample couchbase bucket
                Args:
                        port (str)              -- port number
                        bucket_names(list)      -- names of the sample buckets
                        access_node_ip(str)     -- Ip address of the access node
                        username (str)          -- username to connect to cluster
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
                                        auth=(username, password))
                num_docs = response.json()
                self.log.info("returning number of documents under the sample bucket")
                test = (num_docs['basicStats']['itemCount'])
                count.append(test)
            return count

        except Exception:
            raise Exception("unable to get number of documents")

    def delete_sample_buckets(self, port, bucket_names, access_node_ip, username, password):
        """
        deletes sample couchbase bucket
        Args:
                port (str)              -- port number
                bucket_names(list)      -- names of the sample buckets
                access_node_ip(str)     -- Ip address of the access node
                username (str)          -- username to connect to cluster
                password (str)          -- password to connect to cluster

            Raises:
                Exception:
                    if failed to delete sample bucket
        """
        try:
            for i in range(len(bucket_names)):
                requests.delete('http://' + access_node_ip + ':' + port +
                                '/pools/default/buckets/'+bucket_names[i],
                                auth=(username, password))
                self.log.info("sample bucket "+bucket_names[i]+" deleted")
        except Exception:
            raise Exception("Unable to delete sample bucket")


class Couchbase:
    """
    class has the functions to operate Couchbase instances Under Big data Apps
    """
    test_step = TestStep()

    def __init__(self, admin_console, testcase):
        """Constructor for creating the couchbase object"""
        self._admin_console = admin_console
        self.__instances = Instances(admin_console)
        self.__overview = Overview(self._admin_console)
        self.__couchbaseoperations = CouchbaseOperations(self._admin_console)
        self.__commcell = testcase.commcell
        self.__couchbase = None
        self.couchbase_server_name = testcase.couchbase_server_name
        self.access_nodes = testcase.tcinputs.get("access_nodes")
        self.access_node_ip = self.get_access_node_ip(self.access_nodes)
        self.port = testcase.tcinputs.get("port")
        self.username = testcase.tcinputs.get("username")
        self.password = testcase.tcinputs.get("password")
        self.staging_type = testcase.tcinputs.get("staging_type")
        self.bucket_names = testcase.bucket_names
        self.credentials = testcase.tcinputs.get("credentials")
        self.service_host = testcase.tcinputs.get("service_host")
        self.staging_path = testcase.tcinputs.get("staging_path")
        self.plan_name = testcase.tcinputs.get("plan")
        self.destination_instance = testcase.tcinputs.get("destination_instance")

    def get_access_node_ip(self, access_nodes):
        """Returns ip address of access node"""
        cl_machine = self.__commcell.clients.get(access_nodes[0])
        hostname = str(cl_machine.client_hostname)
        return hostname

    @test_step
    def create_couchbase_instance(self):
        """create couchbase instance """
        self._admin_console.navigator.navigate_to_big_data()
        if self.__instances.is_instance_exists(self.couchbase_server_name):
            self.delete_couchbase_instance()
        _couchbase_server = self.__instances.add_couchbase_server()
        _couchbase_server.add_couchbase_parameters(self.couchbase_server_name, self.access_nodes,
                                                   self.port, self.username, self.password,
                                                   self.staging_type, self.credentials, self.service_host,
                                                   self.staging_path, self.plan_name)
        _couchbase_server.save()
        self._admin_console.navigator.navigate_to_big_data()
        if not self.__instances.is_instance_exists(self.couchbase_server_name):
            raise CVTestStepFailure(
                "[%s] Couchbase server is not getting created " %
                self.couchbase_server_name)
        self._admin_console.log.info("Successfully Created [%s] couchbase server instance",
                                     self.couchbase_server_name)

    def __check_job_restartability(self, job_obj):
        """
        Method for validating restartability by suspending or resuming a job
        Args:
            job_obj             (obj)       --  job object
        Raises:
            Exception:
                If failed to suspend or resume the job.
        """
        try:
            while job_obj.status.upper() == 'WAITING':
                time.sleep(15)
            if job_obj.status.upper() == 'PENDING':
                self._admin_console.log.info("Job is in pending state. Skipping restartability verification")
                return
            if job_obj.is_finished:
                self._admin_console.log.info("Job is already finished. Cannot verify restartability")
                return
            time.sleep(20)
            ignore_restartability_phases = [None, 'Post Operation']
            phase_restart_count = 0
            while job_obj.phase not in ignore_restartability_phases:
                current_phase = job_obj.phase
                phase_restart_count += 1
                self._admin_console.log.info(f"Phase:{current_phase} and restart count:{phase_restart_count}")
                # suspending the job
                self._admin_console.log.info(f"Suspending Job {job_obj.job_id} in {current_phase} phase")
                job_obj.pause(wait_for_job_to_pause=True)
                self._admin_console.log.info("Job Suspended Successfully")
                time.sleep(15)
                # resuming job
                if job_obj.is_finished:
                    self._admin_console.log.info("Job is already finished. Cannot resume a finished job")
                    return
                self._admin_console.log.info(f"Resuming Job {job_obj.job_id} in {current_phase} phase")
                job_obj.resume(wait_for_job_to_resume=True)
                self._admin_console.log.info("Job Resumed Successfully")
                while current_phase == job_obj.phase:
                    if phase_restart_count == 3:
                        time.sleep(30)
                    else:
                        time.sleep(15)
                        if current_phase != job_obj.phase:
                            phase_restart_count = 0
                        break
                else:
                    phase_restart_count = 0
        except Exception as exp:
            self._admin_console.log.exception(f"Exception occurred in getting the job status: {str(exp)}")
            raise exp

    def wait_for_job_completion(self, job_id, check_restartability):
        """ Function to wait till job completes
                Args:
                    job_id (str): Entity which checks the job completion status
                    Check_restartability (str) : checks job restartability
        """
        self._admin_console.log.info("%s Waits for job completion %s", "*" * 8, "*" * 8)
        job_obj = self.__commcell.job_controller.get(job_id)
        if check_restartability:
            self.__check_job_restartability(job_obj)
        self._admin_console.log.info(f"Wait for {job_obj.job_type} job: {job_id} to complete")
        if job_obj.wait_for_completion():
            self._admin_console.log.info("[%s] job completed with job id: \
                          [ % s]", job_obj.job_type, job_id)
        else:
            err_str = "[%s] job id for [%s] failed with JPR: [%s]" % (job_id, job_obj.job_type,
                                                                      job_obj.pending_reason)
            raise Exception(err_str)

        return job_obj.wait_for_completion(timeout=60)


    @test_step
    def verify_backup(self, backup_type, check_restartability = False):
        """Initiate the backup and verify backup job is completed"""
        # Initiate backup job
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.couchbase_server_name)
        _job_id = self.__couchbaseoperations.backup(backup_type)
        self.wait_for_job_completion(_job_id, check_restartability)

    @test_step
    def verify_restore(self, outofplace=False, overwrite=False, check_restartability = False):
        """Initiate restore and verify restore job is completed"""
        # Initiate restore job
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.access_instance(self.couchbase_server_name)
        self.__couchbaseoperations.access_restore()
        _restore = self.__couchbaseoperations.restore_all()
        if outofplace:
            _restore.select_destination_instance(self.destination_instance)
            _restore.set_destination_bucket_names()
        if overwrite:
            _restore.select_overwrite_option()

        self.__couchbaseoperations.submit_restore()
        # Wait for restore job to complete
        _job_id = self._admin_console.get_jobid_from_popup(wait_time=10)
        self.wait_for_job_completion(_job_id, check_restartability)
        self._admin_console.log.info("Restore completed successfully")

    @test_step
    def delete_couchbase_instance(self):
        """Delete couchbase instance and verify instance is deleted"""
        self._admin_console.navigator.navigate_to_big_data()
        self.__instances.delete_instance_name(self.couchbase_server_name)
        if self.__instances.is_instance_exists(self.couchbase_server_name):
            raise CVTestStepFailure(
                "[%s] Couchbase server is not getting deleted" %
                self.couchbase_server_name)
        self._admin_console.log.info(
            "Deleted [%s] instance successfully",
            self.couchbase_server_name)

    @test_step
    def connect_to_db(self):
        """initiate connection to couchbase access node"""
        self.__couchbase = CouchbaseHelper(self.access_nodes,
                                           self.access_node_ip,
                                           self.username,
                                           self.password,
                                           self.port)

    @test_step
    def generate_test_data(self):
        """generates test data"""
        self.__couchbase.load_sample_bucket(self.port, self.bucket_names,
                                            self.access_node_ip, self.username, self.password)

    @test_step
    def create_bucket(self, test_bucket_name):
        """creates buckets for incr backup"""
        self.__couchbase.create_test_bucket(self.access_node_ip, self.username, self.password, test_bucket_name)

    @test_step
    def add_items_to_bucket(self, test_bucket_name):
        """add items to already existing bucket"""
        self.__couchbase.add_items_to_test_bucket(self.access_node_ip, self.username, self.password,
                                                test_bucket_name)

    @test_step
    def get_value_for_docid(self, test_bucket_name, doc_id):
        """gets value of a document based on the id"""
        self.__couchbase.fetch_value_for_docid(self.access_node_ip, self.username, self.password,
                                             test_bucket_name, doc_id)

    @test_step
    def update_value_for_docid(self, test_bucket_name, doc_id):
        """updates value of a document based on the id"""
        self.__couchbase.change_value_for_docid(self.access_node_ip, self.username, self.password, test_bucket_name, doc_id)

    @test_step
    def get_number_of_docs(self, buckets):
        """gets number of documents under the bucket"""
        num_of_docs = self.__couchbase.get_number_of_documents(self.port, buckets,
                                                               self.access_node_ip, self.username, self.password)
        return num_of_docs

    @test_step
    def delete_buckets(self, buckets):
        """deletes bucket"""
        self.__couchbase.delete_sample_buckets(self.port, buckets,
                                               self.access_node_ip, self.username, self.password)

    @test_step
    def validate_restored_data(self, items, buckets):
        """validates restore data"""
        restored_items = self.__couchbase.get_number_of_documents(self.port, buckets,
                                                                  self.access_node_ip, self.username, self.password)
        if restored_items == items:
            self._admin_console.log.info("restored data matches original data")
        else:
            self._admin_console.log.info("restored data does not match with original data")

    @test_step
    def validate_doc_value(self, value_for_docid, bucket_name, doc_id):
        """validates document value after restore"""
        value_after_restore = self.__couchbase.fetch_value_for_docid(self.access_node_ip, self.username, self.password,
                                                                     bucket_name, doc_id)
        if value_after_restore == value_for_docid:
            self._admin_console.log.info("document value after restore matches value before restore")
        else:
            self._admin_console.log.info("document value after restore doesn't match value before restore")
