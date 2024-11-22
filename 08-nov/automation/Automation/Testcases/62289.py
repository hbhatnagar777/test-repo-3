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

    create_objects()                --  Method to create client/instance/postgres helper objects for all cloud clients

    set_postgres_helper_object()    --  Method to create Postgres helper Object

    generate_test_data()            --  Method to generate test data for backup and restore

    backup()                        --  Method to run full backup for subclient

    restore()                       --  Method to run out-of-place restore for subclient

    get_metadata()                  --   Method to collect metadata

    validate_metadata()             --  Method to validate metadata

    validate_azure_metadata()       --  Method to validate metadata when src/dest is azure

    delete_subclient()              --  Method to delete subclient

    create_subclient()              --  Method to create subclient

    delete_client_Access_control_rows()     --  Method to delete APP_clientAccessControl table entries from CSDB

    gcp_to_other_clouds()           --  GCP Backup to other cloud Restores

    ali_to_other_clouds()           --  Alibaba Backup to other cloud Restores

    amazon_to_other_clouds()        --  Amazon Backup to other cloud Restores

    azure_to_other_clouds()         --  Azure Backup to other cloud Restores

    run()                           --  Main function for test case execution
"""
from AutomationUtils import constants, database_helper
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper
from Database.dbhelper import DbHelper


class TestCase(CVTestCase):
    """ Testcase to perform Cross cloud Table level restores from GUI for PAAS PostgreSQL
        Example:
        "62289" : {
          "google_clientName": "",
          "ali_clientName": "",
          "amazon_clientName": "",
          "azure_clientName": "",
          "google_instanceName": "",
          "ali_instanceName": "",
          "amazon_instanceName": "",
          "azure_instanceName": "",
          "storage_policy": ""
        }
    """

    def __init__(self):
        """ Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "Cross cloud Table level restores for PAAS PostgreSQL from GUI"
        self.db_list = []
        self.subclients_object = None
        self.db_helper = None
        self.google_client_obj = None
        self.google_instance_obj = None
        self.google_pg_helper_obj = None
        self.google_psql_db_object = None
        self.ali_client_obj = None
        self.ali_instance_obj = None
        self.ali_pg_helper_obj = None
        self.ali_psql_db_object = None
        self.amazon_client_obj = None
        self.amazon_instance_obj = None
        self.amazon_pg_helper_obj = None
        self.amazon_psql_db_object = None
        self.azure_client_obj = None
        self.azure_instance_obj = None
        self.azure_pg_helper_obj = None
        self.azure_psql_db_object = None
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
        """ Tear down method for testcase(Cleans up testdata) """
        self.log.info("Deleting Automation Created databases from all cloud instances.")
        self.log.info("Database list to be deleted --- %s", self.db_list)
        if self.google_pg_helper_obj:
            self.google_pg_helper_obj.cleanup_tc_db(
                self.google_pg_helper_obj.postgres_server_url,
                self.google_pg_helper_obj.postgres_port,
                self.google_pg_helper_obj.postgres_db_user_name,
                self.google_pg_helper_obj.postgres_password,
                "cloud_automation")
            self.log.info("Automation Created databases deleted from GCP Postgres instance.")
        if self.ali_pg_helper_obj:
            self.ali_pg_helper_obj.cleanup_tc_db(
                self.ali_pg_helper_obj.postgres_server_url,
                self.ali_pg_helper_obj.postgres_port,
                self.ali_pg_helper_obj.postgres_db_user_name,
                self.ali_pg_helper_obj.postgres_password,
                "cloud_automation")
            self.log.info("Automation Created databases deleted from Alibaba Postgres instance.")
        if self.amazon_pg_helper_obj:
            self.amazon_pg_helper_obj.cleanup_tc_db(
                self.amazon_pg_helper_obj.postgres_server_url,
                self.amazon_pg_helper_obj.postgres_port,
                self.amazon_pg_helper_obj.postgres_db_user_name,
                self.amazon_pg_helper_obj.postgres_password,
                "cloud_automation")
            self.log.info("Automation Created databases deleted from Amazon Postgres instance.")
        if self.azure_pg_helper_obj:
            self.azure_pg_helper_obj.cleanup_tc_db(
                self.azure_pg_helper_obj.postgres_server_url,
                self.azure_pg_helper_obj.postgres_port,
                self.azure_pg_helper_obj.postgres_db_user_name,
                self.azure_pg_helper_obj.postgres_password,
                "cloud_automation")
            self.log.info("Automation Created databases deleted from Azure Postgres instance.")
        self.log.info("Deleted Automation Created databases from all cloud instances.")

    def create_objects(self):
        """ Method to create client/instance/postgres helper objects for all cloud clients """
        # Google
        self.google_client_obj = self._commcell.clients.get(self.tcinputs['google_clientName'])
        self.google_instance_obj = \
            self.google_client_obj.agents.get('PostgreSQL').instances.get(self.tcinputs['google_instanceName'])
        self.google_pg_helper_obj, self.google_psql_db_object = \
            self.set_postgres_helper_object(self.google_client_obj, self.google_instance_obj)

        # Alibaba
        self.ali_client_obj = self._commcell.clients.get(self.tcinputs['ali_clientName'])
        self.ali_instance_obj = \
            self.ali_client_obj.agents.get('PostgreSQL').instances.get(self.tcinputs['ali_instanceName'])
        self.ali_pg_helper_obj, self.ali_psql_db_object = \
            self.set_postgres_helper_object(self.ali_client_obj, self.ali_instance_obj)

        # Amazon
        self.amazon_client_obj = self._commcell.clients.get(self.tcinputs['amazon_clientName'])
        self.amazon_instance_obj = \
            self.amazon_client_obj.agents.get('PostgreSQL').instances.get(self.tcinputs['amazon_instanceName'])
        self.amazon_pg_helper_obj, self.amazon_psql_db_object = \
            self.set_postgres_helper_object(self.amazon_client_obj, self.amazon_instance_obj)

        # Azure
        self.azure_client_obj = self._commcell.clients.get(self.tcinputs['azure_clientName'])
        self.azure_instance_obj = \
            self.azure_client_obj.agents.get('PostgreSQL').instances.get(self.tcinputs['azure_instanceName'])
        self.azure_pg_helper_obj, self.azure_psql_db_object = \
            self.set_postgres_helper_object(self.azure_client_obj, self.azure_instance_obj)
        self.log.info("Created client/instance/postgres objects for all clouds.")

    def set_postgres_helper_object(self, client, instance):
        """ Method to create Postgres helper Object
        Args:
            client  (obj)   --  client object
            instance (obj)  --  instance object
        Returns:
            postgres helper object and postgres database object
        """
        self.log.info("Creating PostgreSQL Helper Object")
        postgres_helper_object = pgsqlhelper.PostgresHelper(
            commcell=self.commcell,
            client=client,
            instance=instance)
        pgsql_db_object = database_helper.PostgreSQL(
            postgres_helper_object.postgres_server_url,
            postgres_helper_object.postgres_port,
            postgres_helper_object.postgres_db_user_name,
            postgres_helper_object.postgres_password,
            "postgres")
        postgres_helper_object.pgsql_db_object = pgsql_db_object
        self.log.info("Created PostgreSQL Helper Object")
        return postgres_helper_object, pgsql_db_object

    def generate_test_data(self, pg_helper_object, pg_db_object):
        """ Method to generate test data for backup and restore
        Args:
            pg_helper_object    (obj)   --  postgres helper object
            pg_db_object        (obj)   --  postgres database object
        """
        postgres_data = [1, 1, 10]
        num_of_databases = postgres_data[0]
        num_of_tables = postgres_data[1]
        num_of_rows = postgres_data[2]
        db_prefix = "cloud_automation"
        self.log.info("Generating Test Data")
        pg_helper_object.generate_test_data(
            pg_helper_object.postgres_server_url,
            num_of_databases=num_of_databases,
            num_of_tables=num_of_tables,
            num_of_rows=num_of_rows,
            port=pg_helper_object.postgres_port,
            user_name=pg_helper_object.postgres_db_user_name,
            password=pg_helper_object.postgres_password,
            delete_if_already_exist=True,
            database_prefix=db_prefix)
        self.log.info("Successfully generated Test Data.")
        self.db_list = [db for db in pg_db_object.get_db_list() if db.startswith(db_prefix)]
        self.log.info('db list is {0}'.format(self.db_list))

    def backup(self, subclient, pg_helper_object):
        """ Method to run full backup for subclient
        Args:
            subclient           (obj)   --  subclient object
            pg_helper_object    (obj)   --  postgres helper object
        """
        pg_helper_object.run_backup(subclient, "FULL")
        self.log.info("Backup Job ran successfully")

    def restore(self, subclient, dest_client, dest_instance, pg_helper_object):
        """ Method to run out-of-place restore for subclient
        Args:
            subclient           (obj)   --  subclient object
            dest_client         (obj)   --  destination client object
            dest_instance       (obj)   --  destination instance object
            pg_helper_object    (obj)   --  postgres helper object
        """
        pg_helper_object.run_restore(paths=[
            "/cloud_automation_testdb_0/public/testtab_0/",
            "/cloud_automation_testdb_0/public/test_view_0/",
            "/cloud_automation_testdb_0/public/test_function_0/"],
            subclient=subclient,
            is_dump_based=True,
            destination_client=dest_client,
            destination_instance=dest_instance,
            table_level_restore=True)
        self.log.info("Restore job ran successfully")

    def get_metadata(self, pg_helper_object, pg_db_object):
        """ Method to collect metadata
        Args:
            pg_helper_object    (obj)   --  postgres helper object
            pg_db_object        (obj)   --  postgres database object
        Returns:
            dict of metadata generated for database
        """
        self.db_list = [db for db in pg_db_object.get_db_list() if db.startswith('cloud_automation_testdb_0')]
        return pg_helper_object.generate_db_info(
            db_list=self.db_list,
            hostname=pg_helper_object.postgres_server_url,
            port=pg_helper_object.postgres_port,
            user_name=pg_helper_object.postgres_db_user_name,
            password=pg_helper_object.postgres_password)

    def validate_metadata(self, before_backup, after_restore, pg_helper_object):
        """ Method to validate metadata
        Args:
            before_backup   (dict)  --  metadata collected before bacjup of db on src
            after_restore   (dict)  --  metadata collecetd after restore of db to dest
            pg_helper_object    (obj)   --  postgres helper object
        """
        result = pg_helper_object.validate_db_info(
            before_backup,
            after_restore)
        if result:
            self.log.info("PostgreSQL Backup and Restore Successful!")
        else:
            raise Exception("PostgreSQL Backup and Restore Failed!")

    def validate_azure_metadata(self, before_backup, after_restore, is_source=False):
        """ Method to validate metadata when src/dest is azure
        Args:
            before_backup   (dict)  --  metadata collected before bacjup of db on src
            after_restore   (dict)  --  metadata collecetd after restore of db to dest
            is_source       (bool)  --  True if source/destination is Azure
        """
        before_backup = before_backup['cloud_automation_testdb_0']
        after_restore = after_restore['cloud_automation_testdb_0']
        for index in range(0, max(len(before_backup), len(after_restore))):
            src = set(tuple(before_backup[index]))
            dest = set(tuple(after_restore[index]))
            if is_source:
                if len(dest.difference(src)) != 0:
                    raise Exception("Database Validation Failed for Azure as source!")
            else:
                if len(src.difference(dest)) != 0:
                    raise Exception("Database Validation Failed for Azure as destination!")
        self.log.info("Database Validation Successful for Azure.")

    def delete_subclient(self):
        """ Method to delete subclient """
        if self.subclients_object:
            if self.subclients_object.has_subclient('automation_sc'):
                self.subclients_object.delete('automation_sc')
                self.log.info("deleted subclient automation_sc")
        self.log.info("automation_sc subclient deleted.")

    def create_subclient(self, backupset_obj):
        """ Method to create subclient
        Args:
            backupset_obj   (obj)   --  backupset_object
        """
        self.subclients_object = backupset_obj.subclients
        self.delete_subclient()
        self._subclient = self.subclients_object.add_postgresql_subclient(subclient_name='automation_sc',
                                                                          storage_policy=self.tcinputs[
                                                                              'storage_policy'],
                                                                          contents=self.db_list)
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
        self.generate_test_data(pg_db_object=self.google_psql_db_object,
                                pg_helper_object=self.google_pg_helper_obj)
        self.create_subclient(backupset_obj=self.google_instance_obj.backupsets.get('DumpBasedBackupSet'))
        before_backup = self.get_metadata(pg_db_object=self.google_psql_db_object,
                                          pg_helper_object=self.google_pg_helper_obj)
        self.log.info("Source(GCP) postgres instance metadata before backup - {0}".format(before_backup))
        self.backup(self._subclient, pg_helper_object=self.google_pg_helper_obj)

        # to ALIBABA
        self.delete_client_access_control_rows(src=self.tcinputs['google_clientName'],
                                               dest=self.tcinputs['ali_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['ali_clientName'],
                     dest_instance=self.tcinputs['ali_instanceName'], pg_helper_object=self.google_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.ali_psql_db_object,
                                          pg_helper_object=self.ali_pg_helper_obj)
        self.log.info("Destination(Alibaba) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore, pg_helper_object=self.ali_pg_helper_obj)

        # to AMAZON
        self.delete_client_access_control_rows(src=self.tcinputs['google_clientName'],
                                               dest=self.tcinputs['amazon_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['amazon_clientName'],
                     dest_instance=self.tcinputs['amazon_instanceName'], pg_helper_object=self.google_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.amazon_psql_db_object,
                                          pg_helper_object=self.amazon_pg_helper_obj)
        self.log.info("Destination(Amazon) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore, pg_helper_object=self.amazon_pg_helper_obj)

        # TO AZURE
        self.delete_client_access_control_rows(src=self.tcinputs['google_clientName'],
                                               dest=self.tcinputs['azure_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['azure_clientName'],
                     dest_instance=self.tcinputs['azure_instanceName'], pg_helper_object=self.google_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.azure_psql_db_object,
                                          pg_helper_object=self.azure_pg_helper_obj)
        self.log.info("Destination(Azure) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_azure_metadata(before_backup, after_restore)
        self.delete_subclient()
        self.tear_down()

        self.log.info("############### GCP to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def ali_to_other_clouds(self):
        """ Ali Backup to other cloud Restores"""
        self.generate_test_data(pg_db_object=self.ali_psql_db_object,
                                pg_helper_object=self.ali_pg_helper_obj)
        self.create_subclient(backupset_obj=self.ali_instance_obj.backupsets.get('DumpBasedBackupSet'))
        before_backup = self.get_metadata(pg_db_object=self.ali_psql_db_object,
                                          pg_helper_object=self.ali_pg_helper_obj)
        self.log.info("Source(Alibaba) postgres instance metadata before backup - {0}".format(before_backup))
        self.backup(self._subclient, pg_helper_object=self.ali_pg_helper_obj)

        # to GCP
        self.delete_client_access_control_rows(src=self.tcinputs['ali_clientName'],
                                               dest=self.tcinputs['google_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['google_clientName'],
                     dest_instance=self.tcinputs['google_instanceName'], pg_helper_object=self.ali_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.google_psql_db_object,
                                          pg_helper_object=self.google_pg_helper_obj)
        self.log.info("Destination(GCP) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore, pg_helper_object=self.google_pg_helper_obj)

        # to AMAZON
        self.delete_client_access_control_rows(src=self.tcinputs['ali_clientName'],
                                               dest=self.tcinputs['amazon_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['amazon_clientName'],
                     dest_instance=self.tcinputs['amazon_instanceName'], pg_helper_object=self.ali_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.amazon_psql_db_object,
                                          pg_helper_object=self.amazon_pg_helper_obj)
        self.log.info("Destination(Amazon) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore, pg_helper_object=self.amazon_pg_helper_obj)

        # TO AZURE
        self.delete_client_access_control_rows(src=self.tcinputs['ali_clientName'],
                                               dest=self.tcinputs['azure_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['azure_clientName'],
                     dest_instance=self.tcinputs['azure_instanceName'], pg_helper_object=self.ali_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.azure_psql_db_object,
                                          pg_helper_object=self.azure_pg_helper_obj)
        self.log.info("Destination(Azure) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_azure_metadata(before_backup, after_restore)
        self.delete_subclient()
        self.tear_down()

        self.log.info("############### ALIBABA to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def amazon_to_other_clouds(self):
        """ Amazon Backup to other cloud Restores"""
        self.generate_test_data(pg_db_object=self.amazon_psql_db_object,
                                pg_helper_object=self.amazon_pg_helper_obj)
        self.create_subclient(backupset_obj=self.amazon_instance_obj.backupsets.get('DumpBasedBackupSet'))
        before_backup = self.get_metadata(pg_db_object=self.amazon_psql_db_object,
                                          pg_helper_object=self.amazon_pg_helper_obj)
        self.log.info("Source(Amazon) postgres instance metadata before backup - {0}".format(before_backup))
        self.backup(self._subclient, pg_helper_object=self.amazon_pg_helper_obj)

        # to GCP
        self.delete_client_access_control_rows(src=self.tcinputs['amazon_clientName'],
                                               dest=self.tcinputs['google_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['google_clientName'],
                     dest_instance=self.tcinputs['google_instanceName'], pg_helper_object=self.amazon_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.google_psql_db_object,
                                          pg_helper_object=self.google_pg_helper_obj)
        self.log.info("Destination(GCP) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore, pg_helper_object=self.google_pg_helper_obj)

        # to ALIBABA
        self.delete_client_access_control_rows(src=self.tcinputs['amazon_clientName'],
                                               dest=self.tcinputs['ali_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['ali_clientName'],
                     dest_instance=self.tcinputs['ali_instanceName'], pg_helper_object=self.amazon_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.ali_psql_db_object,
                                          pg_helper_object=self.ali_pg_helper_obj)
        self.log.info("Destination(Alibaba) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_metadata(before_backup, after_restore, pg_helper_object=self.ali_pg_helper_obj)

        # TO AZURE
        self.delete_client_access_control_rows(src=self.tcinputs['amazon_clientName'],
                                               dest=self.tcinputs['azure_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['azure_clientName'],
                     dest_instance=self.tcinputs['azure_instanceName'], pg_helper_object=self.amazon_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.azure_psql_db_object,
                                          pg_helper_object=self.azure_pg_helper_obj)
        self.log.info("Destination(Azure) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_azure_metadata(before_backup, after_restore)
        self.delete_subclient()
        self.tear_down()

        self.log.info("########### AMAZON to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

    def azure_to_other_clouds(self):
        """ Azure Backup to other cloud Restores"""
        self.generate_test_data(pg_db_object=self.azure_psql_db_object,
                                pg_helper_object=self.azure_pg_helper_obj)
        self.create_subclient(backupset_obj=self.azure_instance_obj.backupsets.get('DumpBasedBackupSet'))
        before_backup = self.get_metadata(pg_db_object=self.azure_psql_db_object,
                                          pg_helper_object=self.azure_pg_helper_obj)
        self.log.info("Source(Azure) postgres instance metadata before backup - {0}".format(before_backup))
        self.backup(self._subclient, pg_helper_object=self.azure_pg_helper_obj)

        # to GCP
        self.delete_client_access_control_rows(src=self.tcinputs['azure_clientName'],
                                               dest=self.tcinputs['google_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['google_clientName'],
                     dest_instance=self.tcinputs['google_instanceName'], pg_helper_object=self.azure_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.google_psql_db_object,
                                          pg_helper_object=self.google_pg_helper_obj)
        self.log.info("Destination(GCP) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_azure_metadata(before_backup, after_restore, is_source=True)

        # to ALIBABA
        self.delete_client_access_control_rows(src=self.tcinputs['azure_clientName'],
                                               dest=self.tcinputs['ali_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['ali_clientName'],
                     dest_instance=self.tcinputs['ali_instanceName'], pg_helper_object=self.azure_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.ali_psql_db_object,
                                          pg_helper_object=self.ali_pg_helper_obj)
        self.log.info("Destination(Alibaba) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_azure_metadata(before_backup, after_restore, is_source=True)

        # TO AMAZON
        self.delete_client_access_control_rows(src=self.tcinputs['azure_clientName'],
                                               dest=self.tcinputs['amazon_clientName'])
        self.restore(subclient=self._subclient, dest_client=self.tcinputs['amazon_clientName'],
                     dest_instance=self.tcinputs['amazon_instanceName'], pg_helper_object=self.azure_pg_helper_obj)
        after_restore = self.get_metadata(pg_db_object=self.amazon_psql_db_object,
                                          pg_helper_object=self.amazon_pg_helper_obj)
        self.log.info("Destination(Amazon) postgres instance metadata after restore - {0}".format(after_restore))
        self.validate_azure_metadata(before_backup, after_restore, is_source=True)
        self.delete_subclient()

        self.log.info("############# AZURE to CROSS CLOUD EXECUTED SUCCESSFULLY ############")

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
            # Use same version of postgres instances in all clouds

            self.gcp_to_other_clouds()
            self.ali_to_other_clouds()
            self.amazon_to_other_clouds()
            self.azure_to_other_clouds()

            self.log.info("%%%%%%%%%%%%%%%%% TESTCASE EXECUTION COMPLETED %%%%%%%%%%%%%%%%%%")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
