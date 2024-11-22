# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main Module for setting input variables and creating objects of all other modules.
This module is imported in any test case.
You need to create an object of this module in the test case.

Splunk: Class for initializing input variables and other module objects.

Splunk
======

    __init__()                          --  initialize object of Splunk class

    populate_tc_inputs()                --  populates test case inputs in splunk object

    validate_bigdata_app_list()         --  validates if the client exists in Big Data Apps List

    validate_client_parameters()        --  validates if the client parameters such as
    master uri, master_node,user_name and plan are set as required

    make_request()                      --  common module to make splunk related REST API calls

    fetch_bucket_details_of_index       --  Retrieves bucket details of the given index

    retrieve_warm_and_cold_buckets_information  --  Seperates the warm buckets and cold buckets names
    and eventcount using the fetched bucket details

    verify_rolled_buckets               --  Verifies if the buckets are rolled according to the max_warm_DB_count
    parameter

    verify_buckets_deletion             --  Verifies if the given bucket is deleted from the list of buckets

    splunk_bundle_push()                --   pushes the latest Splunk bundle to slave nodes

    splunk_nodes_health_check()         --  checks if all the slaves are up

    splunk_rolling_restart()            --  initiates a rolling restart over the Splunk cluster
    and waits until all the slave nodes restart

    add_data_to_index                   --  Adds data to existing Splunk index

    delete_bucket                       --  Deletes a bucket

    roll_buckets                        --  Rolls the warm buckets to cold buckets.

    add_splunk_index()                  --  creates a new splunk index

    edit_splunk_index()                 --  edits the events associated with the index_obj

    delete_index()                      --  deletes Splunk index by changing indexes.conf
    on master node and performing bundle push and rolling restart

    cleanup_index()                     --  cleans up the created index for the test-case
    as a part of cleanup job

    make_after_restore_configuration()  --  writes appropriate content into indexes.conf file
    of master node after successful restore job

"""

from __future__ import unicode_literals
import time
import calendar
from http import HTTPStatus
import requests
import xmltodict
import splunklib.client as splunk_client
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.machine import Machine
from Database.SplunkApplication.operations import CvOperation
from xml.dom import minidom
import json


class Splunk():
    """Class for initializing input variables"""

    def __init__(self, tc_object):
        """
            Initializes the input variables,logging and creates object from other modules.

            Args:
                tc_object   --  instance of testcase class

            Returns:
                object  --  instance of splunk class object
        """
        self.tc_object = tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.csdb = self.tc_object.csdb
        self.tcinputs = tc_object.tcinputs
        self.commcell = tc_object.commcell
        self.cvpysdk_object = self.commcell._cvpysdk_object
        self.new_client_name = ""
        self.master_node = ""
        self.master_uri = ""
        self.user_name = ""
        self.password = ""
        self.plan = ""
        self.populate_tc_inputs(tc_object)
        self.cvoperations = CvOperation(self)

    def populate_tc_inputs(self, tc_object):
        """
        Initializes all the test case inputs after validation

        Args:
            tc_object (obj)    --    Object of testcase

        Raises:
            Exception:
                if a valid CVTestCase object is not passed.

                if CVTestCase object doesn't have agent initialized
        """
        if not isinstance(tc_object, CVTestCase):
            raise Exception("Valid test case object must be passed as argument")
        self.new_client_name = tc_object.tcinputs.get("NewClientName")
        self.master_node = tc_object.tcinputs.get("MasterNode")
        self.master_uri = tc_object.tcinputs.get("MasterUri")
        self.user_name = tc_object.tcinputs.get("UserName")
        self.password = tc_object.tcinputs.get("Password")
        self.plan = tc_object.tcinputs.get("Plan")
        self.log = tc_object.log

    def validate_bigdata_app_list(self, client_obj):
        """
        Validates if the client exists in Big Data Apps List

        Args:
            client_obj              (Object)    --      splunk client object

        Returns:
            instance ID
        """
        agent_obj = client_obj.agents
        req_agent = agent_obj.get("big data apps")
        instance_obj = req_agent.instances
        all_instances = instance_obj.all_instances

        if self.new_client_name.lower() in all_instances.keys():
            instance_id = all_instances[self.new_client_name.lower()]
            return instance_id

        raise Exception("Failed to find required client in big data entities")

    def validate_client_parameters(self, instance_id, client_object):
        """
        Validates if the client parameters such as master uri, master_node,user_name
        and plan are set as required.

        Args:
           instance_id    (int)  --  instance ID of an instance associated with an agent

           client_object  (obj)  --  client object of the newly created splunk client

        """
        instance_id = int(instance_id)
        agent_obj = client_object.agents
        req_agent = agent_obj.get("big data apps")
        instance_obj = req_agent.instances
        req_instance = instance_obj.get(instance_id)
        instance_prop = req_instance.properties
        master_uri = instance_prop["distributedClusterInstance"]["clusterConfig"] \
            ["splunkConfig"]["url"]
        master_node = instance_prop["distributedClusterInstance"]["clusterConfig"] \
            ["splunkConfig"]["primaryNode"]["entity"]["clientName"]
        user_name = instance_prop["distributedClusterInstance"]["clusterConfig"] \
                     ["splunkConfig"]["splunkUser"]["userName"]

        if(master_uri != self.master_uri or \
                master_node != self.master_node or \
                user_name != self.user_name):
            raise Exception("Client Parameter Validation Failed")

        backupset_obj = req_agent.backupsets
        req_backupset = backupset_obj.get("defaultbackupset")
        subclients_obj = req_backupset.subclients
        req_subclient = subclients_obj.get("default")
        subclient_prop = req_subclient.properties
        if subclient_prop["planEntity"]["planName"] != self.plan:
            raise Exception("Client Parameter Validation Failed")

    def make_request(self, url, method):
        """
        Common module to make splunk related REST API calls

        Args:
            url             (str)   -- url of the REST API

            method          (str)   --  method type of the request

        Returns:
            returned_resp   (obj)   --  response object associated with the request
        """

        if method == "POST":
            returned_resp = requests.post(
                url, auth=(self.user_name, self.password), verify=False
            )

        elif method == "GET":
            returned_resp = requests.get(
                url, auth=(self.user_name, self.password), verify=False
            )

        else:
            raise Exception("Request Method Not supported")

        if returned_resp.status_code == HTTPStatus.UNAUTHORIZED:
            raise Exception("Unauthorized Splunk Request")

        if returned_resp.status_code == HTTPStatus.OK and returned_resp.ok:
            return returned_resp

        raise Exception("Splunk Request Failed")

    def fetch_bucket_details_of_index(self,index_name=None):
        '''
        Retrieves bucket details of the given index

        Args:
            index_name       (str)   --  Splunk index object

        Returns:
            bucket_details   (dict)   --  a dictionary of bucket details of the corresponding index
        '''

        self.log.info("Retrieving bucket details")
        #Initiate the search
        search_query='| dbinspect index=' + index_name
        self.log.info("The search query is %s",search_query)
        returned_response = requests.post(
            self.master_uri + "/services/search/jobs",
            data={'search': search_query},
            auth=(self.user_name, self.password),
            verify=False)
        time.sleep(5)
        if returned_response.status_code != 201:
            raise Exception("Search request not successful")
        self.log.info("Search request is sent")
        time.sleep(10)
        #Retriving the search id of the search
        sid=minidom.parseString(returned_response.content).getElementsByTagName('sid')[0].childNodes[0].nodeValue
        if sid is None:
            raise Exception("Couldn't retrieve the search id")
        self.log.info("The search id of the search is %s",sid)
        #Checking the status of search
        self.log.info("Checking the status of the search" )
        wait_time = 0
        dispatched_state = 0
        job_status = None
        while(not(dispatched_state) and wait_time < 120):
            returned_response = self.make_request(
                self.master_uri + "/services/search/jobs/" + str(sid),
                "GET"
            )
            time.sleep(5)
            keys = minidom.parseString(returned_response.content).getElementsByTagName('s:key')
            for n in keys:
                if n.getAttribute('name') == 'dispatchState':
                    job_status = n.childNodes[0].nodeValue
                    if(job_status == 'DONE'):
                        dispatched_state=1
                    else:
                        wait_time += 10
                        self.log.info("Waiting for the search job to complete")
        if(job_status != 'DONE'):
            raise Exception("Search not successful")
        self.log.info("Search job is done")
        #Retrieve the result of the search
        returned_response = self.make_request(
            self.master_uri + "/services/search/jobs/" + str(sid) + '/results?output_mode=json&count=0',
            "GET"
        )
        time.sleep(5)
        if returned_response.status_code != 200:
            raise Exception("Retrieving bucket details failed")
        bucket_details = json.dumps(returned_response.json())
        self.log.info("Retrieved the bucket details of the index")
        return bucket_details

    def retrieve_warm_and_cold_buckets_information(self, bucket_details=None):
        '''
        Extracts one set(either originating or replicating) of warm buckets and cold buckets names and eventcount using the fetched bucket details.

        Args:
            bucket_details                      (dict)  --   dictionary of bucket details of the corresponding index
        Returns:
            warm_and_cold_buckets_names (list),               --   list of warm and cold buckets,
            eventcount_of_warm_and_cold_buckets (list)             list of eventcount of warm and cold buckets


        '''
        if bucket_details is None:
            raise Exception("Bucket information is None")
        warm_buckets = []
        cold_buckets = []
        warm_buckets_eventcount = []
        cold_buckets_eventcount = []
        type_of_buckets=[]
        for bucket in bucket_details["results"]:
            if ("db_" in bucket["path"]):
                type_of_buckets.append("db")
            elif ("rb_" in bucket["path"]):
                type_of_buckets.append("rb")
        if(len(set(type_of_buckets))==2):
            for bucket in bucket_details["results"]:
                if("db_" in bucket["path"]):
                    if bucket['state'] == 'warm':
                        warm_buckets.append(bucket["bucketId"])
                        warm_buckets_eventcount.append(int(bucket['eventCount']))
                    elif bucket['state'] == 'cold':
                        cold_buckets.append(bucket["bucketId"])
                        cold_buckets_eventcount.append(int(bucket['eventCount']))
        else:
            for bucket in bucket_details["results"]:
                if bucket['state'] == 'warm':
                    warm_buckets.append(bucket["bucketId"])
                    warm_buckets_eventcount.append(int(bucket['eventCount']))
                elif bucket['state'] == 'cold':
                    cold_buckets.append(bucket["bucketId"])
                    cold_buckets_eventcount.append(int(bucket['eventCount']))
        self.log.info("Retrieved warm and cold bucket details")
        return [warm_buckets, cold_buckets],[warm_buckets_eventcount, cold_buckets_eventcount]

    def verify_rolled_buckets(self, warm_buckets, max_warm_DB_count=None):
        """
                Verifies if the buckets are rolled according to the max_warm_DB_count parameter

            Args:
                warm_buckets (list)   --   a list of warm buckets
            Returns:
                Nothing
        """
        self.log.info("Verifying rolling of buckets")
        num_of_warm_buckets = len(warm_buckets)
        if (num_of_warm_buckets != max_warm_DB_count):
            raise Exception("Rolling not successful")
        self.log.info("Rolling successful")

    def verify_buckets_deletion(self, buckets, bucket_name):
        """
            Verifies if the given bucket is deleted from the list of buckets

                Args:
                    buckets (list)     --   a list of buckets
                    bucket_name(str)  --   name of the deleted bucket
                Returns:
                    Nothing
        """
        self.log.info("Verifying bucket deletion")
        if (bucket_name in buckets):
            raise Exception("Deletion not successful")
        self.log.info("Deletion successful")

    def splunk_bundle_push(self):
        """
        Pushes the latest Splunk bundle to slave nodes

        Args:
            Nothing

        """

        self.log.info("Starting Splunk Bundle Push")
        returned_response = self.make_request(
            self.master_uri+"/services/cluster/master/control/default/apply",
            "POST"
        )
        if returned_response.status_code != 200:
            raise Exception("Splunk Bundle Push Failed")

        time.sleep(60)
        self.log.info("Splunk Bundle Push Successful")

    def splunk_nodes_health_check(self):
        """
        Checks if all the slave nodes are up.

        Args:
            Nothing

        Exception:
            Raises exception if slave nodes do not come up within 300 secs
        """
        health_uri = self.master_uri + "/services/cluster/master/health"

        self.log.info("Waiting For All Slave Nodes To Be Up")

        returned_response = self.make_request(health_uri, "GET")
        if returned_response.status_code != 200:
            raise Exception("Failed To Check Splunk Health")

        all_peers_up = False
        total_time_elapsed = 0

        up_result_count = 0

        while (not all_peers_up and total_time_elapsed <= 500):
            returned_response = self.make_request(health_uri, "GET")
            parse_data = xmltodict.parse(returned_response.text)
            key_value_list = parse_data["feed"]["entry"]["content"]["s:dict"]["s:key"]
            for i in range(len(key_value_list)):
                req_dict = dict(parse_data["feed"]["entry"]["content"]["s:dict"]["s:key"][i])
                if (req_dict["@name"] == "all_peers_are_up" and req_dict["#text"] == "1"):
                    up_result_count = up_result_count + 1
                    if up_result_count >= 3:
                        all_peers_up = True
                        break

            if not all_peers_up:
                self.log.info("Some Nodes Are Down/Restarting")
                time.sleep(15)
                total_time_elapsed = total_time_elapsed + 15

        if not all_peers_up:
            raise Exception("Failed To Restart Slave Nodes")

        self.log.info("All Slave Nodes Are Up")

    def splunk_rolling_restart(self):
        """
        Initiates a rolling restart over the Splunk cluster and
        waits until all the slave nodes restart

        Args:
             Nothing

        """

        self.log.info("Starting Rolling Restart")
        returned_response = self.make_request(
            self.master_uri+"/services/cluster/master/control/control/restart",
            "POST"
        )

        if returned_response.status_code != 200:
            raise Exception("Splunk Rolling Restart Failed")

        time.sleep(15)
        self.splunk_nodes_health_check()

    def add_data_to_index(self, index_name=None, num_of_buckets=None):
        """
        Adds data to existing Splunk index

        Args:
            index_name     (str)   --  Splunk index name
            num_of_buckets (int)   --  Number of buckets to add to the index

        Returns:
            Splunk index object
        """
        self.log.info("Starting to add data to %s",index_name)
        slave_username = self.tcinputs.get("Slave1SplunkUsername")
        slave_password = self.tcinputs.get("Slave1SplunkPassword")
        slave_ip = self.tcinputs.get("Slave1Ip")
        slave_port = self.tcinputs.get("Slave1Port")
        self.log.info("Populating Index %s", index_name)
        for bucket in range(num_of_buckets):
            service = splunk_client.connect(
                host=slave_ip, port=slave_port,
                username=slave_username, password=slave_password
            )
            index_obj = service.indexes[index_name]
            for event in range(100):
                index_obj.submit("This event from automation" + str(event), sourcetype="custom", host="remote_host")
            self.splunk_rolling_restart()
            time.sleep(5)
        self.log.info("Populating Index %s Completed Successfully", index_name)
        service = splunk_client.connect(
            host=slave_ip, port=slave_port,
            username=slave_username, password=slave_password
        )
        time.sleep(20)
        index_obj = service.indexes[index_name]
        return index_obj


    def delete_bucket(self, bucket_name=None):
        '''
            Deletes a bucket

            Args:
                bucket_name (str)   --  the name of the bucket to be deleted
            Returns:
                Nothing
        '''

        returned_response = self.make_request(
            self.master_uri + "/services/cluster/master/buckets/" + bucket_name + "/remove_all",
            "POST",
        )
        if returned_response.status_code != 200:
            raise Exception("Bucket Deletion Failed")
        time.sleep(10)
        self.splunk_rolling_restart()
        self.splunk_nodes_health_check()

    def roll_buckets(self, max_warm_DB_count=2):
        '''
        Rolls the warm buckets to cold buckets. By default, only two warm buckets remain.

        Args:
            max_warm_DB_count (int)  --  the number of warm buckets to remain

        Returns:
            Nothing
        '''
        self.log.info("Start of Appending max_warm_DB_count")
        splunk_home_path = self.tcinputs.get("SplunkHomePath")
        master_name = self.tcinputs.get("MasterNode")
        machine_obj = Machine(machine_name=master_name, commcell_object=self.commcell)
        if machine_obj.os_info.lower() == "windows":
            windows_machine_obj = WindowsMachine(machine_name=master_name,
                                                 commcell_object=self.commcell)
            file_path = splunk_home_path + "\\etc\\master-apps\\_cluster\\local\\indexes.conf"
            windows_machine_obj.append_to_file(file_path, 'maxWarmDBCount = ' + str(max_warm_DB_count) + '\r\n')

        else:
            unix_machine_obj = UnixMachine(machine_name=master_name,
                                           commcell_object=self.commcell)
            file_path = splunk_home_path + "/etc/master-apps/_cluster/local/indexes.conf"
            unix_machine_obj.append_to_file(file_path, 'maxWarmDBCount = ' + str(max_warm_DB_count))
        self.splunk_bundle_push()
        self.splunk_nodes_health_check()
        self.splunk_rolling_restart()
        self.splunk_nodes_health_check()
        self.log.info("Appending max_warm_DB_count is successful")

    def add_splunk_index(self):
        """
        Creates new Splunk index

        Args:
            Nothing

        Returns:
              Splunk index object
        """
        self.log.info("Starting To Add New Splunk Index")
        time_stamp = str(calendar.timegm(time.gmtime()))
        index_name = "testindex_" + time_stamp
        slave_username = self.tcinputs.get("Slave1SplunkUsername")
        slave_password = self.tcinputs.get("Slave1SplunkPassword")
        slave_ip = self.tcinputs.get("Slave1Ip")
        slave_port = self.tcinputs.get("Slave1Port")
        master_name = self.tcinputs.get("MasterNode")
        machine_obj = Machine(machine_name=master_name, commcell_object=self.commcell)
        splunk_home_path = self.tcinputs.get("SplunkHomePath")

        if machine_obj.os_info.lower() == "windows":
            windows_machine_obj = WindowsMachine(machine_name=master_name,
                                                 commcell_object=self.commcell)
            file_path = splunk_home_path + "\\etc\\master-apps\\_cluster\\local\\indexes.conf"
            index_stanza = "[" + index_name + "]\r\n"
            index_stanza = index_stanza + "coldPath = C:\\SplunkIndex\\" + index_name + "\\colddb\r\n"
            index_stanza = index_stanza + "homePath = C:\\SplunkIndex\\" + index_name + "\\db\r\n"
            index_stanza = index_stanza + "thawedPath = C:\\SplunkIndex\\" + index_name + "\\thaweddb\r\n"
            index_stanza = index_stanza + "repFactor = auto\r\n"
            windows_machine_obj.append_to_file(file_path, index_stanza)

        else:
            unix_machine_obj = UnixMachine(machine_name=master_name,
                                           commcell_object=self.commcell)
            file_path = splunk_home_path + "/etc/master-apps/_cluster/local/indexes.conf"
            index_stanza_dict = {
                "index_stanza1": "[" + index_name + "]",
                "index_stanza2": "homePath = \\$" + "SPLUNK_DB/" + index_name + "/db",
                "index_stanza3": "coldPath = \\$" + "SPLUNK_DB/" + index_name + "/colddb",
                "index_stanza4": "thawedPath = \\$" + "SPLUNK_DB/" + index_name + "/thaweddb",
                "index_stanza5": "repFactor = auto"
            }
            for path in index_stanza_dict:
                unix_machine_obj.append_to_file(file_path, index_stanza_dict[path])

        self.splunk_bundle_push()
        time.sleep(15)
        self.splunk_nodes_health_check()
        self.splunk_rolling_restart()
        self.log.info("New Index Added Successfully With Name %s", index_name)
        self.log.info("Populating Index %s", index_name)
        service = splunk_client.connect(
            host=slave_ip, port=slave_port,
            username=slave_username, password=slave_password
        )
        index_obj = service.indexes[index_name]

        for event in range(100):
            index_obj.submit("This event from automation" + \
                             str(event), sourcetype="custom", host="remote_host")

        time.sleep(30)
        self.log.info("Populating Index %s Completed Successfully", index_name)
        eventcount = 0
        wait_time = 0
        eventcount_retrieved = False
        while (not(eventcount_retrieved) and wait_time < 120):
            try:
                index_obj = service.indexes[index_name]
                eventcount = index_obj["totalEventCount"]
                if (int(eventcount) == 100):
                    eventcount_retrieved = True
                else:
                    wait_time += 10
                    time.sleep(10)
            except KeyError:
                wait_time += 10
                time.sleep(10)
        if(int(eventcount) != 100):
            raise Exception("Eventcount retrieval not successful")
        return index_obj

    def edit_splunk_index(self, index_name):
        """
        Edits the events associated with the index_obj

        Args:
            index_name   (obj)   --  Splunk index object

        """
        self.log.info("Starting To Edit Splunk Index")
        slave_username = self.tcinputs.get("Slave1SplunkUsername")
        slave_password = self.tcinputs.get("Slave1SplunkPassword")
        slave_ip = self.tcinputs.get("Slave1Ip")
        slave_port = self.tcinputs.get("Slave1Port")
        service = splunk_client.connect(host=slave_ip, port=slave_port,
                                        username=slave_username, password=slave_password)
        index_obj = service.indexes[index_name]
        self.log.info("Adding New Events To The Index")
        for event in range(10):
            index_obj.submit(("This is a modified event" +
                             str(event)).encode(), sourcetype="custom", host="remote_host")
        time.sleep(180)
        self.log.info("Successfully Completed Editing Splunk Index")

    def delete_index(self):
        """
        Deletes Splunk index by changing indexes.conf on master node
        and performing bundle push and rolling restart

        Args:
            Nothing

        """

        self.log.info("Starting Index Deletion")
        master_name = self.tcinputs.get("MasterNode")
        machine_obj = Machine(machine_name=master_name, commcell_object=self.commcell)
        splunk_home_path = self.tcinputs.get("SplunkHomePath")

        if machine_obj.os_info.lower() == "windows":
            windows_machine_obj = WindowsMachine(machine_name=master_name,
                                                 commcell_object=self.commcell)
            file_path = splunk_home_path + "\\etc\\master-apps\\_cluster\\local\\indexes.conf"
            windows_machine_obj.append_to_file(file_path, "\ndeleted=true")

        else:
            unix_machine_obj = UnixMachine(machine_name=master_name,
                                           commcell_object=self.commcell)
            file_path = splunk_home_path + "/etc/master-apps/_cluster/local/indexes.conf"
            unix_machine_obj.append_to_file(file_path, "deleted=true")

        self.splunk_bundle_push()
        time.sleep(15)
        self.splunk_nodes_health_check()
        self.splunk_rolling_restart()
        self.log.info("Index Deletion Successful")

    def cleanup_index(self, index_name, max_warm_DB_count=None):
        """
         Cleans up the created index for the testcase as a part of cleanup job

         Args:
             index_name     (str)   --  Name associated with the index which
             we want to cleanup
             max_warm_DB_count (int)   --  Should be given when index contains max_warm_DB_count parameter
        """
        self.log.info("Starting Index Cleanup")
        master_name = self.tcinputs.get("MasterNode")
        machine_obj = Machine(machine_name=master_name, commcell_object=self.commcell)
        splunk_home_path = self.tcinputs.get("SplunkHomePath")

        if machine_obj.os_info.lower() == "windows":
            windows_machine_obj = WindowsMachine(machine_name=master_name,
                                                 commcell_object=self.commcell)
            file_path = splunk_home_path + "\\etc\\master-apps\\_cluster\\local\\indexes.conf"
            index_stanza = "[" + index_name + "]\r\n"
            index_stanza = index_stanza + "coldPath = C:\\SplunkIndex\\" + index_name + "\\colddb\r\n"
            index_stanza = index_stanza + "homePath = C:\\SplunkIndex\\" + index_name + "\\db\r\n"
            index_stanza = index_stanza + "thawedPath = C:\\SplunkIndex\\" + index_name + "\\thaweddb\r\n"
            index_stanza = index_stanza + "repFactor = auto\r\n"
            if (max_warm_DB_count != None):
                index_stanza = index_stanza + "maxWarmDBCount = " + str(max_warm_DB_count) + "\r\n"
            index_stanza = index_stanza + "deleted = true\r\n"
            windows_machine_obj.append_to_file(file_path, index_stanza)

        else:
            unix_machine_obj = UnixMachine(machine_name=master_name,
                                           commcell_object=self.commcell)
            file_path = splunk_home_path + "/etc/master-apps/_cluster/local/indexes.conf"
            if (max_warm_DB_count != None):
                index_stanza_dict = {
                    "index_stanza1": "[" + index_name + "]",
                    "index_stanza2": "homePath = \\$" + "SPLUNK_DB/" + index_name + "/db",
                    "index_stanza3": "coldPath = \\$" + "SPLUNK_DB/" + index_name + "/colddb",
                    "index_stanza4": "thawedPath = \\$" + "SPLUNK_DB/" + index_name + "/thaweddb",
                    "index_stanza5": "repFactor = auto",
                    "index_stanza6": "maxWarmDBCount = " + str(max_warm_DB_count),
                    "index_stanza7": "deleted = true"
                }
            else:
                index_stanza_dict = {
                    "index_stanza1": "[" + index_name + "]",
                    "index_stanza2": "homePath = \\$" + "SPLUNK_DB/" + index_name + "/db",
                    "index_stanza3": "coldPath = \\$" + "SPLUNK_DB/" + index_name + "/colddb",
                    "index_stanza4": "thawedPath = \\$" + "SPLUNK_DB/" + index_name + "/thaweddb",
                    "index_stanza5": "repFactor = auto",
                    "index_stanza7": "deleted = true"
                }
            for path in index_stanza_dict:
                unix_machine_obj.append_to_file(file_path, index_stanza_dict[path])

        self.splunk_bundle_push()
        time.sleep(15)
        self.splunk_nodes_health_check()
        self.splunk_rolling_restart()
        self.log.info("Index Cleanup Successful")


    def make_after_restore_configuration(self):
        """
        Writes appropriate content into indexes.conf file of master node
        after successful restore job

        Args:
            Nothing
        """

        self.log.info("Starting After Restore Configuration")
        master_name = self.tcinputs.get("MasterNode")
        machine_obj = Machine(machine_name=master_name, commcell_object=self.commcell)
        splunk_home_path = self.tcinputs.get("SplunkHomePath")

        if machine_obj.os_info.lower() == "windows":
            windows_machine_obj = WindowsMachine(machine_name=master_name,
                                                 commcell_object=self.commcell)
            file_path = splunk_home_path + "\\etc\\master-apps\\_cluster\\local\\indexes.conf"
            windows_machine_obj.append_to_file(file_path, "\r\ndeleted=false")

        else:
            unix_machine_obj = UnixMachine(machine_name=master_name,
                                           commcell_object=self.commcell)
            file_path = splunk_home_path + "/etc/master-apps/_cluster/local/indexes.conf"
            unix_machine_obj.append_to_file(file_path, "\r\n")
            unix_machine_obj.append_to_file(file_path, "deleted=false")

        self.splunk_bundle_push()
        time.sleep(60)
        self.splunk_nodes_health_check()
        self.splunk_rolling_restart()
        time.sleep(30)
        self.log.info("After Restore Configuration Successful")
