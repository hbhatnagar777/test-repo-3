# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  Initializes test case class object

    setup()                         --  Setup function for this testcase

    teardown()                      --  Tear down method for testcase(Cleans up testdata)

    create_objects()                --  Method to create client/instance/MySQL helper objects for all cloud clients

    set_mysql_helper_object()       --  Method to create MySQL helper Object

    generate_test_data()            --  Method to generate test data for backup and restore

    backup()                        --  Method to run full backup for subclient

    restore()                       --  Method to run out-of-place restore for subclient

    get_metadata()                  --   Method to collect metadata

    validate_metadata()             --  Method to validate metadata

    delete_subclient()              --  Method to delete subclient

    create_subclient()              --  Method to create subclient

    delete_client_access_control_rows()     --  Method to delete APP_clientAccessControl table entries from CSDB

    gcp_to_other_clouds()           --  GCP Backup to other cloud Restores

    ali_to_other_clouds()           --  Alibaba Backup to other cloud Restores

    amazon_to_other_clouds()        --  Amazon Backup to other cloud Restores

    azure_to_other_clouds()         --  Azure Backup to other cloud Restores

    run()                           --  Main function for test case execution
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper
from Database.dbhelper import DbHelper
from deepdiff import DeepDiff


class TestCase(CVTestCase):
    """ Testcase to perform Cross cloud restores from GUI for PAAS MySQL
        Example:
        "62306" : {
          "google_clientName": "",
          "ali_clientName": "",
          "amazon_clientName": "",
          "azure_clientName": "",
          "google_instanceName": "",
          "ali_instanceName": "",
          "amazon_instanceName": "",
          "azure_instanceName": "",
          "storage_policy": ""
          "testdata":[1,1,10]
        }
    """

    def __init__(self):
        """ Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "Cross cloud restores for PAAS MySQL from GUI"
        self.database_list = []
        self.db_prefix = f"automation{str(int(time.time()))}"
        self.db_helper = None
        self.google_client_obj = None
        self.google_instance_obj = None
        self.google_mysql_helper_obj = None
        self.ali_client_obj = None
        self.ali_instance_obj = None
        self.ali_mysql_helper_obj = None
        self.amazon_client_obj = None
        self.amazon_instance_obj = None
        self.amazon_mysql_helper_obj = None
        self.azure_client_obj = None
        self.azure_instance_obj = None
        self.azure_mysql_helper_obj = None
        self.subclients_object = None
        self.tcinput = {
            "google_clientName": None,
            "ali_clientName": None,
            "amazon_clientName": None,
            "azure_clientName": None,
            "google_instanceName": None,
            "ali_instanceName": None,
            "amazon_instanceName": None,
            "azure_instanceName": None,
            "storage_policy": None
        }

    def setup(self):
        """ setup function for this testcase """
        self.db_helper = DbHelper(self._commcell)
        self.create_objects()

    def tear_down(self):
        """Tear down function for this testcase"""
        self.log.info("Deleting Automation Created databases from all cloud instances.")
        if self.google_mysql_helper_obj:
            self.google_mysql_helper_obj.cleanup_test_data(database_prefix='automation')
            self.log.info("Automation Created databases deleted from GCP MySQL instance.")
        if self.ali_mysql_helper_obj:
            self.ali_mysql_helper_obj.cleanup_test_data(database_prefix='automation')
            self.log.info("Automation Created databases deleted from Alibaba MySQL instance.")
        if self.amazon_mysql_helper_obj:
            self.amazon_mysql_helper_obj.cleanup_test_data(database_prefix='automation')
            self.log.info("Automation Created databases deleted from Amazon MySQL instance.")
        if self.azure_mysql_helper_obj:
            self.azure_mysql_helper_obj.cleanup_test_data(database_prefix='automation')
            self.log.info("Automation Created databases deleted from Azure MySQL instance.")
        self.log.info("Deleted Automation Created databases from all cloud instances.")

    def create_objects(self):
        """ Method to create client/instance/MySQL helper objects for all cloud clients """
        # Google
        self.google_client_obj = self._commcell.clients.get(self.tcinputs['google_clientName'])
        self.google_instance_obj = \
            self.google_client_obj.agents.get('MySQL').instances.get(self.tcinputs['google_instanceName'])
        self.google_mysql_helper_obj = self.set_mysql_helper_object(self.google_instance_obj)

        # Alibaba
        self.ali_client_obj = self._commcell.clients.get(self.tcinputs['ali_clientName'])
        self.ali_instance_obj = \
            self.ali_client_obj.agents.get('MySQL').instances.get(self.tcinputs['ali_instanceName'])
        self.ali_mysql_helper_obj = self.set_mysql_helper_object(self.ali_instance_obj)

        # Amazon
        self.amazon_client_obj = self._commcell.clients.get(self.tcinputs['amazon_clientName'])
        self.amazon_instance_obj = \
            self.amazon_client_obj.agents.get('MySQL').instances.get(self.tcinputs['amazon_instanceName'])
        self.amazon_mysql_helper_obj = self.set_mysql_helper_object(self.amazon_instance_obj)

        # Azure
        self.azure_client_obj = self._commcell.clients.get(self.tcinputs['azure_clientName'])
        self.azure_instance_obj = \
            self.azure_client_obj.agents.get('MySQL').instances.get(self.tcinputs['azure_instanceName'])
        self.azure_mysql_helper_obj = self.set_mysql_helper_object(self.azure_instance_obj)
        self.log.info("Created client/instance/MySQL objects for all clouds.")

    def set_mysql_helper_object(self, instance):
        """ Generating MySQL helper object
        Args:
            instance (obj)  --  instance object
        Returns:
            MySQL helper object
        """
        self.log.info("Creating MySQL Helper Object")
        mysql_helper_object = MYSQLHelper(
            commcell=self.commcell,
            subclient=instance.subclients.get('default'),
            instance=instance,
            user=instance.mysql_username,
            port=instance.port)
        self.log.info("Created MySQL Helper Object")
        return mysql_helper_object

    def generate_test_data(self, mysql_helper_object):
        """ Method to generate test data for backup and restore
        Args:
            mysql_helper_object    (obj)   --  MySQL helper object
        """
        data = self.tcinputs.get('testdata', [2, 2, 10])
        num_of_databases = data[0]
        num_of_tables = data[1]
        num_of_rows = data[2]
        self.log.info("Generating Test Data")
        self.database_list = mysql_helper_object.generate_test_data(
            database_prefix=self.db_prefix,
            num_of_databases=num_of_databases,
            num_of_tables=num_of_tables,
            num_of_rows=num_of_rows,
            cross_cloud=True)
        self.log.info("Successfully generated Test Data {0}.".format(self.database_list))

    def backup(self, instance):
        """ perform backup operation
        Args:
            instance           (obj)   --  instance object
        """
        self.log.info("Running Full Backup.")
        self.db_helper.run_backup(instance.subclients.get('automation_sc'), 'FULL')
        self.log.info("Full backup compeleted successfully.")

    def restore(self, instance_obj, dest_client, dest_instance):
        """ Method to run out-of-place restore for subclient
        Args:
            instance_obj (obj)   --  mysql helper object
            dest_client         (obj)   --  destination client object
            dest_instance       (obj)   --  destination instance object
        """
        self.log.info("Database list to restore --- %s", self.database_list)
        database_list = ["//" + db for db in self.database_list]
        job = instance_obj.restore_in_place(path=database_list,
                                            dest_client_name=dest_client,
                                            dest_instance_name=dest_instance)
        self.log.info("####Started Restore with Job ID: %s####", job.job_id)
        if not job.wait_for_completion():
            raise Exception("Failed to run restore job with error:{0}".format(job.delay_reason))
        self.log.info("Database restore completed successfully.")

    def get_metadata(self, mysql_helper_object):
        """ Method to collect metadata
        Args:
            mysql_helper_object    (obj)   --  mysql helper object
        Returns:
            dict of metadata generated for database
        """
        return mysql_helper_object.get_database_information(self.database_list)

    def validate_metadata(self, before_backup, after_restore):
        """ Method to validate metadata
        Args:
            before_backup   (dict)  --  metadata collected before bacjup of db on src
            after_restore   (dict)  --  metadata collecetd after restore of db to dest
        """
        # Note: generated test data will have uppercase names
        # but few clouds(alibaba) doesn't create DBs with name having uppercase chars
        result = DeepDiff(str(before_backup), str(after_restore), ignore_string_case=True)
        if not result:
            self.log.info("MySQL Backup and Restore Successful!")
        else:
            raise Exception("MySQL Backup and Restore Failed!")

    def delete_subclient(self):
        """ Method to delete subclient """
        if self.subclients_object:
            if self.subclients_object.has_subclient('automation_sc'):
                self.subclients_object.delete('automation_sc')
                self.log.info("deleted subclient automation_sc")
        self.log.info("automation_sc subclient deleted.")

    def create_subclient(self, instance_obj):
        """ Method to create subclient
        Args:
            instance_obj   (obj)   --  backupset_object
        """
        self.subclients_object = instance_obj.subclients
        self.delete_subclient()
        self._subclient = self.subclients_object.add_mysql_subclient(subclient_name='automation_sc',
                                                                     storage_policy=self.tcinputs['storage_policy'],
                                                                     contents=self.database_list)
        self.log.info("created subclient automation_sc.")
        self._commcell.refresh()

    def delete_client_access_control_rows(self, src, dest):
        """ Method to delete APP_clientAccessControl table entries from CSDB
        Args:
            src     (str)   -- source client name
            dest    (dest)  --  destination client name
        """
        client_list = []
        src_object = self._commcell.clients.get(src)
        dest_object = self._commcell.clients.get(dest)
        client_list.append(int(src_object.client_id))
        client_list.append(int(dest_object.client_id))
        proxies_of_src = self.db_helper.get_proxy_names(src_object)
        for proxy in proxies_of_src:
            client_list.append(int(self._commcell.clients.get(proxy).client_id))
        proxies_of_dest = self.db_helper.get_proxy_names(dest_object)
        for proxy in proxies_of_dest:
            client_list.append(int(self._commcell.clients.get(proxy).client_id))
            self.log.info("client list to delete associations are {0}".format(client_list))
        # delete entries
        self.log.info("clients list for which access control entries are deleted is {0}".format(client_list))
        self.db_helper.delete_client_access_control(client1=self.google_client_obj, client_list=client_list)
        self.log.info("Deleted associations from table.")

    def gcp_to_other_clouds(self):
        """ GCP Backup to other cloud Restores"""
        self.tear_down()
        self.generate_test_data(mysql_helper_object=self.google_mysql_helper_obj)
        self.create_subclient(instance_obj=self.google_instance_obj)
        before_backup = self.get_metadata(mysql_helper_object=self.google_mysql_helper_obj)
        self.log.info("Source(GCP) MySQL instance metadata before backup - {0}".format(before_backup))
        self.backup(self.google_instance_obj)

        # to Alibaba
        self.delete_client_access_control_rows(src=self.tcinputs['google_clientName'],
                                               dest=self.tcinputs['ali_clientName'])
        self.restore(dest_client=self.tcinputs['ali_clientName'],
                     dest_instance=self.tcinputs['ali_instanceName'],
                     instance_obj=self.google_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.ali_mysql_helper_obj)
        self.log.info("Destination(Alibaba) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("GCP to Alibaba Verified")

        # to Amazon
        self.delete_client_access_control_rows(src=self.tcinputs['google_clientName'],
                                               dest=self.tcinputs['amazon_clientName'])
        self.restore(dest_client=self.tcinputs['amazon_clientName'],
                     dest_instance=self.tcinputs['amazon_instanceName'],
                     instance_obj=self.google_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.amazon_mysql_helper_obj)
        self.log.info("Destination(Amazon) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("GCP to Amazon verified")

        # to Azure
        self.delete_client_access_control_rows(src=self.tcinputs['google_clientName'],
                                               dest=self.tcinputs['azure_clientName'])
        self.restore(dest_client=self.tcinputs['azure_clientName'],
                     dest_instance=self.tcinputs['azure_instanceName'],
                     instance_obj=self.google_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.azure_mysql_helper_obj)
        self.log.info("Destination(Azure) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("GCP to Azure verified")
        self.delete_subclient()
        self.tear_down()

        self.log.info("############### GCP to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def ali_to_other_clouds(self):
        """ Ali Backup to other cloud Restores"""
        self.generate_test_data(mysql_helper_object=self.ali_mysql_helper_obj)
        self.create_subclient(instance_obj=self.ali_instance_obj)
        before_backup = self.get_metadata(mysql_helper_object=self.ali_mysql_helper_obj)
        self.log.info("Source(Alibaba) MySQL instance metadata before backup - {0}".format(before_backup))
        self.backup(self.ali_instance_obj)

        # to GCP
        self.delete_client_access_control_rows(src=self.tcinputs['ali_clientName'],
                                               dest=self.tcinputs['google_clientName'])
        self.restore(dest_client=self.tcinputs['google_clientName'],
                     dest_instance=self.tcinputs['google_instanceName'],
                     instance_obj=self.ali_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.google_mysql_helper_obj)
        self.log.info("Destination(GCP) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Alibaba to GCP Verified")

        # to Amazon
        self.delete_client_access_control_rows(src=self.tcinputs['ali_clientName'],
                                               dest=self.tcinputs['amazon_clientName'])
        self.restore(dest_client=self.tcinputs['amazon_clientName'],
                     dest_instance=self.tcinputs['amazon_instanceName'],
                     instance_obj=self.ali_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.amazon_mysql_helper_obj)
        self.log.info("Destination(Amazon) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Alibaba to Amazon verified")

        # to Azure
        self.delete_client_access_control_rows(src=self.tcinputs['ali_clientName'],
                                               dest=self.tcinputs['azure_clientName'])
        self.restore(dest_client=self.tcinputs['azure_clientName'],
                     dest_instance=self.tcinputs['azure_instanceName'],
                     instance_obj=self.ali_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.azure_mysql_helper_obj)
        self.log.info("Destination(Azure) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Alibaba to Azure verified")
        self.delete_subclient()
        self.tear_down()

        self.log.info("############### Alibaba to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def amazon_to_other_clouds(self):
        """ Amazon Backup to other cloud Restores"""
        self.generate_test_data(mysql_helper_object=self.amazon_mysql_helper_obj)
        self.create_subclient(instance_obj=self.amazon_instance_obj)
        before_backup = self.get_metadata(mysql_helper_object=self.amazon_mysql_helper_obj)
        self.log.info("Source(Amazon) MySQL instance metadata before backup - {0}".format(before_backup))
        self.backup(self.amazon_instance_obj)

        # to GCP
        self.delete_client_access_control_rows(src=self.tcinputs['amazon_clientName'],
                                               dest=self.tcinputs['google_clientName'])
        self.restore(dest_client=self.tcinputs['google_clientName'],
                     dest_instance=self.tcinputs['google_instanceName'],
                     instance_obj=self.amazon_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.google_mysql_helper_obj)
        self.log.info("Destination(GCP) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Amazon to GCP Verified")

        # to Alibaba
        self.delete_client_access_control_rows(src=self.tcinputs['amazon_clientName'],
                                               dest=self.tcinputs['ali_clientName'])
        self.restore(dest_client=self.tcinputs['ali_clientName'],
                     dest_instance=self.tcinputs['ali_instanceName'],
                     instance_obj=self.amazon_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.ali_mysql_helper_obj)
        self.log.info("Destination(Alibaba) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Amazon to Alibaba verified")

        # to Azure
        self.delete_client_access_control_rows(src=self.tcinputs['amazon_clientName'],
                                               dest=self.tcinputs['azure_clientName'])
        self.restore(dest_client=self.tcinputs['azure_clientName'],
                     dest_instance=self.tcinputs['azure_instanceName'],
                     instance_obj=self.amazon_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.azure_mysql_helper_obj)
        self.log.info("Destination(Azure) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Amazon to Azure verified")
        self.delete_subclient()
        self.tear_down()

        self.log.info("############### Amazon to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def azure_to_other_clouds(self):
        """ Azure Backup to other cloud Restores"""
        self.generate_test_data(mysql_helper_object=self.azure_mysql_helper_obj)
        self.create_subclient(instance_obj=self.azure_instance_obj)
        before_backup = self.get_metadata(mysql_helper_object=self.azure_mysql_helper_obj)
        self.log.info("Source(Azure) MySQL instance metadata before backup - {0}".format(before_backup))
        self.backup(self.azure_instance_obj)

        # to GCP
        self.delete_client_access_control_rows(src=self.tcinputs['azure_clientName'],
                                               dest=self.tcinputs['google_clientName'])
        self.restore(dest_client=self.tcinputs['google_clientName'],
                     dest_instance=self.tcinputs['google_instanceName'],
                     instance_obj=self.azure_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.google_mysql_helper_obj)
        self.log.info("Destination(GCP) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Azure to GCP Verified")

        # to Alibaba
        self.delete_client_access_control_rows(src=self.tcinputs['azure_clientName'],
                                               dest=self.tcinputs['ali_clientName'])
        self.restore(dest_client=self.tcinputs['ali_clientName'],
                     dest_instance=self.tcinputs['ali_instanceName'],
                     instance_obj=self.azure_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.ali_mysql_helper_obj)
        self.log.info("Destination(Alibaba) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Azure to Alibaba verified")

        # to Amazon
        self.delete_client_access_control_rows(src=self.tcinputs['azure_clientName'],
                                               dest=self.tcinputs['amazon_clientName'])
        self.restore(dest_client=self.tcinputs['amazon_clientName'],
                     dest_instance=self.tcinputs['amazon_instanceName'],
                     instance_obj=self.azure_instance_obj)
        after_restore = self.get_metadata(mysql_helper_object=self.amazon_mysql_helper_obj)
        self.log.info("Destination(Amazon) MySQL instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore)
        self.log.info("Azure to Amazon verified")
        self.delete_subclient()

        self.log.info("############### Azure to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def run(self):
        """Main function for test case execution"""
        try:
            # create client objects - all cloud clients
            # generate data on source
            # collect source metadata - get db_list filter required and generate db_info
            # create subclient & backup source
            # delete entries from app_clientAccessControl
            # restore to destination
            # get metadata from destination on filtered tables(geneated testdata only)
            # validate metadata (based on src and dest cloud)
            #   different if azure because -- azure has other tables/views generated by default
            # Repeat above for all clouds
            # delete subclient on src
            # tear_down on src & all destinaion
            # Use same version of MySQL instances in all clouds

            self.gcp_to_other_clouds()
            self.ali_to_other_clouds()
            self.amazon_to_other_clouds()
            self.azure_to_other_clouds()

            self.log.info("%%%%%%%%%%%%%%%%% TESTCASE EXECUTION COMPLETED %%%%%%%%%%%%%%%%%%")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
