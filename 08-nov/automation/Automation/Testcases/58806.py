# -*- coding: utf-8 -*-

    # --------------------------------------------------------------------------
    # See LICENSE.txt in the project root for
    # license information.
    # --------------------------------------------------------------------------

""""Main file for executing this test case

    TestCase is the only class defined in this file.

    TestCase: Class for executing this test case

    TestCase:
        __init__()      --  Initializes test case class object

        setup()         --  Setup function for this testcase

        teardown()      --  Cleans up testdata

        run()           --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.config_cloud_db import ConfigCloudDb
from Database.dbhelper import DbHelper

class TestCase(CVTestCase):
    """
        Class for executing Basic acceptance test of MySQL cloud paas backup and Restore test case
        Example for testcase inputs:
        "58806": {
                        "client_name": "client name",
                        "agent_name": "MySQL",
                        "instance_name": "mysqlservername [location]",
                        "access_node": "proxyvm",
                        "cloud_type": "Alicloud",
                        "cloud_options": {
                            "accessKey": "accesskey",
                            "secretkey": "secretkey"
                        },
                        "database_options":{
                            "storage_policy": "storage policy",
                            "port": "servername:port",
                            "mysql_user_name": "mysql user",
                            "mysql_password": "password",
                            "version": "mysql version",
                            "install_dir": "/opt/commvault/CVCloudAddOns/MySQL/5.7/bin"
                    }
                    }
        Example if client/agent/instance already exists
        "58806": {
                        "ClientName": "cloud client name",
                        "AgentName": "MySQL",
                        "InstanceName": "mysqlservername [location]",
                        "SubclientName": "default",
                }
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "Basic Acceptance Test of Alibaba cloud Paas MySQL backup and restore"
        self.mysql_helper_object = None
        self.mysql_db_object = None
        self.dbhelper_object = None
        self.config_cloud_db_object = None
        self.tcinputs = {"client_name": None,
                         "agent_name": None,
                         "instance_name": None,
                         "access_node": None,
                         "cloud_type": "Alicloud",
                         "cloud_options": {
                             "accessKey": None,
                            "secretkey": None
                         },
                         "database_options":{
                             "storage_policy": None,
                             "port": None,
                             "mysql_user_name": None,
                             "mysql_password": None,
                             "version": None,
                             "install_dir": None
                             }
                        }

    def setup(self):
        """setup function for this testcase"""
        if self._client is None:
            self.config_cloud_db_object = ConfigCloudDb(self.commcell, self.tcinputs)
        elif self._instance is None:
            self.config_cloud_db_object = ConfigCloudDb(self.commcell, self.tcinputs,
                                                        self.client)
        else:
            self.config_cloud_db_object = ConfigCloudDb(self.commcell, self.tcinputs,
                                                        self.client, self.instance)

        self.mysql_helper_object = MYSQLHelper(self.commcell,
                                               self.config_cloud_db_object.instance.subclients.get('default'),
                                               self.config_cloud_db_object.instance,
                                               self.config_cloud_db_object.access_node,
                                               self.config_cloud_db_object.instance.mysql_username,
                                               self.config_cloud_db_object.database_options.get("port"))

        self.dbhelper_object = DbHelper(self.commcell)
        self.mysql_helper_object.basic_setup_on_mysql_server()

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.debug("Deleting Automation Created databases")
        self.mysql_helper_object.cleanup_test_data("automation")

    def run(self):
        """Main function for test case execution"""
        try:

            subclient = self.config_cloud_db_object.instance.subclients.get('default')
            self.log.debug("Read subclient content")
            self.log.debug("Subclient Content: {0}".format(subclient.content))

            self.log.debug("genearting testdata for Full Backup")
            self.full_tables_dict = self.mysql_helper_object.generate_test_data()
            self.log.debug("#########Running backup #########")
            self.log.info(
                "Check Basic Setting of mysql server before stating the test cases")

            full_job = self.dbhelper_object.run_backup(subclient, "FULL")
            self.log.debug("Full job is {0}".format(full_job))
            db_size = self.mysql_helper_object.get_database_information(
                subclient.content)
            self.log.debug(db_size)
            self.log.debug("Deleting Automation Created databases before Restore")
            self.mysql_helper_object.cleanup_test_data("automation")

            self.log.debug("#####Running In Place Data Restore and validation#####")

            restore_job = self.mysql_helper_object.run_data_restore_and_validation(
                database_info=db_size)
            self.log.debug(restore_job)


        except Exception as excp:
            self.log.error('Failed with error: {0}'.format(excp))
            self.result_string = excp
            self.status = constants.FAILED
