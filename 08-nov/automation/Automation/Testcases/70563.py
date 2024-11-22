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
import time

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
        Populates Test Data
        Runs Full Snap Backup
        Runs In-place Cluster Restore.
        # Incremental Backup is through oplog schedule , can't trigger through API.
        """
        try:
            self.log.info("Creating MongoDB Object")
            self.mongohelper = MongoAgentHelper(self)

            self.log.info("MongoDB Object Creation Successful")
            self.log.info("Adding new MongoDB client")
            # skipping steps as we have workflow enabled to authenticate Unistall or install of client.
            # self.client_obj = self.mongohelper.add_mongodb_pseudo_client()
            # if self.client_obj is None:
            #     raise Exception("New Client Creation Failed")
            # self.log.info("Addition of New MongoDB Pseudo Client Successful")
            # self.client_obj = self.mongohelper.add_mongodb_pseudo_client()

            self.client_obj = self.commcell.clients.get(self.tcinputs['ClientName'])
            self.log.info("Running Discover on the client")
            instance_id = int(self.client_obj.client_id)

            try:
                self.mongohelper.discover_mongodb_nodes(instance_id)
                self.log.info("Ran Discover on new Instance")
                self.log.info("Generating Sample Data on the cluster")
                self.data_object = MongoDBHelper(self,
                                                 masterhostname=self.mongohelper.master_hostname,
                                                 port=self.tcinputs.get("Port"))
                self.data_object.generate_test_data()
            except Exception as e:
                raise CVTestStepFailure(e)
            self.log.info("Running Full Snap Backup")
            try:
                self.mongohelper.run_mongodb_snap_backup(self.client_obj)
                self.log.info("Backup Job Successful ")
            except Exception as e:
                raise CVTestStepFailure(e)
            req_agent = self.client_obj.agents.get("big data apps")
            self.log.info("Running in place Cluster restore")
            self.mongohelper.run_full_cluster_restore()
            self.log.info("Restore completed ")
            self.status = cv_constants.PASSED


        except Exception as ex:
            self.log.error("Exception in the test case")
            self.log.error(
                'Error %s on line %s. Error %s', type(ex).__name__,
                sys.exc_info()[-1].tb_lineno, ex
            )
            self.result_string = str(ex)
            self.status = cv_constants.FAILED
