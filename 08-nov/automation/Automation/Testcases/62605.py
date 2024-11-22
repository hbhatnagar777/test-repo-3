# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
import sys
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants as cv_constants
from Database.SplunkApplication.splunk import Splunk
import json

class TestCase(CVTestCase):
    """
    Class for executing basic test case for creating new splunk client and performing
    backup and recovery and verifying the same.
    """

    def __init__(self):
        """
        init method of the test-case class which defines test-case arguments
        """
        super(TestCase, self).__init__()
        self.name = "Splunk iDA,Incremental Backup and Restore from snap copy"
        self.show_to_user = False
        self.splunk_object = None
        self.tcinputs = {
            "NewClientName": None,
            "MasterNode": None,
            "MasterUri": None,
            "UserName": None,
            "Password": None,
            "SplunkHomePath": None,
            "Plan": None,
            "Nodes": None,     #list of slave nodes:[slave1, slave2]
            "Slave1Ip": None,
            "Slave1Port": None,
            "Slave1SplunkUsername": None,
            "Slave1SplunkPassword": None
        }

    def run(self):
        """
        Run function of this test case
        """
        try:
            self.log.info("Creating Splunk Object")
            self.splunk_object = Splunk(self)
            self.log.info("Splunk Object Creation Successful")
            self.log.info("Starting Splunk Client Creation")
            client_obj = self.splunk_object.cvoperations.add_splunk_client()
            if client_obj is None:
                raise Exception("New Splunk Client Creation Failed")
            self.log.info("Splunk Client Creation Successful")
            index_obj1 = self.splunk_object.add_splunk_index()
            index_name1 = index_obj1["name"]
            self.splunk_object.splunk_rolling_restart()
            index_obj1 = self.splunk_object.add_data_to_index(index_name=index_name1, num_of_buckets=4)
            self.log.info("Starting Backup Job")
            nodes = self.tcinputs.get("Nodes")
            self.splunk_object.cvoperations.update_client_nodes(client_obj, nodes)
            index_list = [index_name1]
            self.splunk_object.cvoperations.update_client_content(client_obj, index_list)
            client_details = self.splunk_object.cvoperations.get_client_details(
                client_obj, backupset_name="defaultbackupset", subclient_name="default")
            self.splunk_object.cvoperations.run_backup(client_obj, subclient_details=client_details["subclient"])
            self.log.info("Backup job Successful")
            # Adding more data to index
            index_obj1 = self.splunk_object.add_data_to_index(index_name=index_name1, num_of_buckets=1)
            # Rolling a few buckets in the index from warm to cold
            self.splunk_object.roll_buckets(max_warm_DB_count=2)
            # Fetching bucket details of the index
            bucket_details = json.loads(self.splunk_object.fetch_bucket_details_of_index(index_name=index_name1))
            self.log.info("The bucket information is %s", bucket_details)
            buckets, eventcount = self.splunk_object.retrieve_warm_and_cold_buckets_information(bucket_details)
            warm_buckets = buckets[0]
            cold_buckets = buckets[1]
            self.splunk_object.verify_rolled_buckets(warm_buckets, max_warm_DB_count=2)
            sorted_warm_buckets = sorted(warm_buckets)
            sorted_cold_buckets = sorted(cold_buckets)
            # Delete one warm and one cold buckets of the index
            deleted_warm_bucket = sorted_warm_buckets[0]
            deleted_cold_bucket = sorted_cold_buckets[0]
            self.splunk_object.delete_bucket(deleted_warm_bucket)
            self.splunk_object.delete_bucket(deleted_cold_bucket)
            if (len(eventcount) == 2):
                deleted_warm_bucket_eventcount = eventcount[0][warm_buckets.index(deleted_warm_bucket)]
                deleted_cold_bucket_eventcount = eventcount[1][cold_buckets.index(deleted_cold_bucket)]
            else:
                raise Exception("Eventcount not retrieved properly")
            bucket_details = json.loads(self.splunk_object.fetch_bucket_details_of_index(index_name=index_name1))
            buckets, eventcount = self.splunk_object.retrieve_warm_and_cold_buckets_information(bucket_details)
            warm_buckets = buckets[0]
            cold_buckets = buckets[1]
            warm_buckets_eventcount = eventcount[0]
            cold_buckets_eventcount = eventcount[1]
            self.splunk_object.verify_buckets_deletion(warm_buckets, deleted_warm_bucket)
            self.splunk_object.verify_buckets_deletion(cold_buckets, deleted_cold_bucket)
            final_index1_eventcount = 0
            # Checking sequence of deletion of buckets
            bucket_numbers=[]
            for i in warm_buckets:
                bucket_numbers.append(int(i.split('~')[1]))
            for i in cold_buckets:
                bucket_numbers.append(int(i.split('~')[1]))
            least_bucket_number=min(bucket_numbers)
            if((int(deleted_warm_bucket.split('~')[1]) == least_bucket_number or
                int(deleted_cold_bucket.split('~')[1] == least_bucket_number)) and
                (abs(int(deleted_warm_bucket.split('~')[1]) - int(deleted_cold_bucket.split('~')[1])) == 1)):
                final_index1_eventcount += (sum(warm_buckets_eventcount) + sum(cold_buckets_eventcount))
            else:
                final_index1_eventcount += (sum(warm_buckets_eventcount) + sum(cold_buckets_eventcount))
                if (int(deleted_warm_bucket.split('~')[1]) != least_bucket_number):
                    final_index1_eventcount += deleted_warm_bucket_eventcount
                    warm_buckets.append(deleted_warm_bucket)
                elif (int(deleted_cold_bucket.split('~')[1]) != least_bucket_number):
                    final_index1_eventcount += deleted_cold_bucket_eventcount
                    cold_buckets.append(deleted_cold_bucket)
            # Adding a new index
            index_obj2 = self.splunk_object.add_splunk_index()
            index_name2 = index_obj2["name"]
            total_eventcount2 = index_obj2["totalEventCount"]
            self.splunk_object.splunk_rolling_restart()
            index_list = [index_name1,index_name2]
            self.splunk_object.cvoperations.update_client_content(client_obj, index_list)
            self.splunk_object.cvoperations.run_backup(client_obj, subclient_details=client_details["subclient"],backup_type="Incremental")
            #deleting the two indexes
            self.splunk_object.delete_index()
            self.splunk_object.delete_index()
            self.splunk_object.cvoperations.run_restore(client_obj, index_list,
                                                        subclient_details=client_details["subclient"], copy_precedence = 1)
            self.splunk_object.make_after_restore_configuration()
            """self.splunk_object.cvoperations.verify_incr_restore(
                final_index1_eventcount, index_name1, warm_buckets, cold_buckets)"""
            self.splunk_object.cvoperations.verify_restore(total_eventcount2, index_name2)
            self.log.info("Starting Cleanup Job")
            self.splunk_object.cvoperations.cleanup(client_obj)
            self.splunk_object.cleanup_index(index_name1, max_warm_DB_count=2)
            self.splunk_object.cleanup_index(index_name2)
            self.log.info("Cleanup Job Successful")
            self.log.info("Test CASE SUCCESSFUL")

        except Exception as ex:
            self.log.error("Exception in the test case")
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
