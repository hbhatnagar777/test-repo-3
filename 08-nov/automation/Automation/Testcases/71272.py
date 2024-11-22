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
import time,random

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants as cv_constants
from Web.Common.exceptions import CVTestStepFailure
from Database.MongoDBUtils.mongodbhelper import MongoDBHelper, MongoAgentHelper


class TestCase(CVTestCase):
    """
    Class for executing basic test case for creating a new MongoDB client
    amd performing Backup and full cluster restore.
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.status = None
        self.result_string = None
        self.data_object = None
        self.client_obj = None
        self.master_obj = None
        self.name = "MongoDB acceptance"
        self.show_to_user = False
        self.mongodb_object = None
        self.tcinputs = {
            'MasterNode': None,
            'MasterHostName': None,
            'OsUser': None,
            'Password': None,
            'Port': None,
            'Plan': None,
            'BinPath': None,
            'ReplicaSetName': None,
            'PrimaryHost': None,
            'DB_user': None,
            'DB_password': None,
            "ClientName": None
        }
        self.wait_time = 60

    def run(self):
        """
        Steps :
        Creates a new MongoDB Pseudo Client on CS
        Run Discover Operation on New Instance
        Populates FULL Test Data
        Runs Full Snap Backup
        Delete FULL testdata
        Runs In-place Cluster Restore.
        Run validation that cluster databases and collections.
        Populates INCREMENTAL Test Data
        Runs INCEMENTAL OP LOGS backup
        Delete ICNR testdata
        Runs In-place Cluster Restore
        Run validation that cluster databases and collections.
        """
        try:
            self.log.info("Creating MongoDB Object")
            self.mongohelper = MongoAgentHelper(self)
            self.random_str = str(random.randint(0, 10000))
            full_database= "database_full_%s" %(self.random_str)
            incr_database = "database_incr_%s" % (self.random_str)
            self.log.info("MongoDB Object Creation Successful")
            self.log.info("Adding new MongoDB client")

            self.client_obj = self.commcell.clients.get(self.tcinputs['ClientName'])
            self.log.info("Running Discover on the client")
            instance_id = int(self.client_obj.client_id)
            self.client_obj.enable_backup()
            time.sleep(20)
            try:
                self.mongohelper.discover_mongodb_nodes(instance_id)
                self.log.info("Ran Discover on new Instance")
                self.log.info("Generating Sample Data on the cluster")
                self.data_object = MongoDBHelper(self,
                                                 masterhostname=self.mongohelper.master_hostname,
                                                 port=self.tcinputs.get("Port"))
                full_data = self.data_object.generate_test_data(database_prefix=full_database,num_dbs=1,num_col=4,num_docs=10)
            except Exception as e:
                raise CVTestStepFailure(e)
            self.log.info("Running Full Snap Backup")
            try:
                snap_job,backup_job = self.mongohelper.run_mongodb_snap_backup(self.client_obj)
                self.log.info("Backup Job Successful ")
                self.data_object.delete_test_data(prefix=full_database)
                self.log.info("********************deleted database %s ************", str(full_database))
                self.client_obj.disable_backup()
            except Exception as e:
                raise CVTestStepFailure(e)
            req_agent = self.client_obj.agents.get("big data apps")
            self.log.info("Running in place Cluster restore")
            self.mongohelper.run_full_cluster_restore()
            self.log.info("Restore completed ")
            self.log.info("Running validation on cluster")
            self.mongohelper.verify_cluster_restore(full_data)

            self.data_object = MongoDBHelper(self,
                                             masterhostname=self.mongohelper.master_hostname,
                                             port=self.tcinputs.get("Port"))
            self.client_obj.enable_backup()
            snap_job, backup_job = self.mongohelper.run_mongodb_snap_backup(self.client_obj)
            self.log.info(" FULL Backup Job post restore  Successful ")
            incr_data = self.data_object.generate_test_data(database_prefix=incr_database, num_dbs=1, num_col=4,
                                                                 num_docs=10)
            self.log.info("***** Waiting for 10 mins for Incremental to finish ********")
            time.sleep(500)
            jobs = self.mongohelper.get_client_jobs(self.tcinputs['ClientName'])
            latest_job = int(next(iter(jobs)))
            if latest_job > backup_job:
                self.log.info("incremental oplogs backup kicked as per schedule %s ", latest_job)
                first_element = next(iter(jobs.items()))
                status = first_element[1]['STATUS']
                if status == 'Completed':
                    self.log.info("job %s launched is completed ", status)
                else:
                    self.log.info("job %s launched is failed ", status)
                    raise Exception(" incremental backup launched in schedule but failed ")
            else:
                self.log.info("incremental oplogs backup failed to run ")
                raise Exception(" incremental backup didnt launch  ")
            self.log.info("********************deleted database %s ************", str(incr_database))
            self.data_object.delete_test_data(prefix=incr_database)
            self.log.info("Running Restore from incremental backup")
            self.client_obj.disable_backup()
            time.sleep(30)
            restore_job_id = self.mongohelper.run_full_cluster_restore()
            time.sleep(60)
            self.mongohelper.verify_cluster_restore(full_data)
            self.mongohelper.verify_cluster_restore(incr_data)
            search_term ="Replaying the oplog dumps"
            log_lines = self.mongohelper.get_logs_for_job_from_file( job_id=restore_job_id,
                log_file_name="CVMongoDBUtil.log", search_term=search_term)
            self.log.info("Log Lines returned are %s", str(log_lines))
            if not log_lines:  # This will be True if str_value is empty
                self.log.info("Log Lines returned are %s", str(log_lines))
                raise Exception("Replaying incremental jobs not done %s", str(restore_job_id) )

            else:
                self.log.info("Log Lines returned are %s", str(log_lines))
                self.log.info("Replaying incremental jobs %s done ", str(restore_job_id))
            self.data_object = MongoDBHelper(self,
                                             masterhostname=self.mongohelper.master_hostname,
                                             port=self.tcinputs.get("Port"))
            self.data_object.delete_test_data(prefix='database_')
            self.status = cv_constants.PASSED


        except Exception as ex:
            self.log.error("Exception in the test case")
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
        finally:
            self.client_obj.disable_backup()
