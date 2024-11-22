# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""" Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                    -- initialize TestCase class
    tear_down()                   -- tear down method for test case
    run()                         -- run function of this test case
    create_sweep_schedule()       -- Create schedule with sweep interval of one hour
    create_source_ifx_helper_obj()      -- Creates informix helper object for source instance
    create_destination_ifx_helper_obj() -- Creates informix helper object for destination instance
    run_backup()                  -- Submit backup and return backup job id
    restore_and_validate()        -- Submit restore and validate data restored
    get_client_list()             -- Gets list of client IDs for which entries need to be
    deleted from APP_clientAccessControl table

Input Example:
    "testCases":
        {
            "63433":
                    {
                        "ClientName": "client_name",
                        "AgentName": "informix",
                        "InstanceName": "instance_name",
                        "BackupsetName": "default",
                        "SubclientName": "default",5
                        "UserName":"username",
                        "SourceInformixServiceName": "port_number",
                        "SourceInformixDBPassword": "password",
                        "DestinationClientName": "dest_client_name",
                        "DestinationInstanceName": "dest_instance_name",
                        "DestinationInformixServiceName": "port_number",
                        "DestinationInformixDBPassword": "password",
                        "TestDataSize": [2, 10, 100]
                    }
        }
Put password value as empty for linux clients.
Provide DomainName also in UserName for windows clients.
Provide port to which informix server listens using ipv4 address in InformixServiceName
TestDataSize should be list in order: [database_count, tables_count, row_count]
"""
from time import sleep
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.InformixUtils.informixhelper import InformixHelper
from Database import dbhelper

class TestCase(CVTestCase):
    """Class for executing Informix cross machine restore from command line after deleting access control entries"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Informix cross machine restore from command line after deleting access control entries"
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.INFORMIX
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            'UserName': None,
            'SourceInformixServiceName': None,
            'SourceInformixDBPassword': None,
            'TestDataSize': [],
            'DestinationClientName': None,
            'DestinationInstanceName': None,
            'DestinationInformixServiceName': None,
            'DestinationInformixDBPassword': None
        }
        self.dbhelper_object = None
        self.base_directory = None
        self.source_informix_helper_obj = None
        self.destination_informix_helper_obj = None

    def tear_down(self):
        """ tear down method for test case"""
        self.log.info("Deleting Automation Created databases")
        if self.source_informix_helper_obj:
            self.source_informix_helper_obj.delete_test_data()
        if self.destination_informix_helper_obj:
            self.destination_informix_helper_obj.delete_test_data()
        if self.commcell.schedule_policies.has_policy('ifx_idx_automation_sweep'):
            self.log.info("Deleting the automation created sweep schedule policy")
            self.commcell.schedule_policies.delete('ifx_idx_automation_sweep')

    def create_sweep_schedule(self):
        """Creates schedule with log backup to disk cache enabled and
        associates to the informix source instance """
        if self.commcell.schedule_policies.has_policy('ifx_idx_automation_sweep'):
            self.log.info("Deleting the existing sweep schedule policy")
            self.commcell.schedule_policies.delete('ifx_idx_automation_sweep')
        self.source_informix_helper_obj.create_sweep_schedule_policy(
            'ifx_idx_automation_sweep', sweep_time=1)
        self.log.info("Sweep schedule policy is associated to instance")

    def create_source_ifx_helper_obj(self):
        """Creates object of informix helper class for source instance
        and does test data generation"""
        source_agent = self.client.agents.get('informix')
        source_instance = source_agent.instances.get(self.tcinputs['InstanceName'])
        self.source_informix_helper_obj = InformixHelper(
            self.commcell,
            source_instance,
            'default',
            self.client.client_hostname,
            self.tcinputs['InstanceName'],
            source_instance.informix_user,
            self.tcinputs['SourceInformixDBPassword'],
            self.tcinputs['SourceInformixServiceName']
        )
        self.log.info("Populate the informix server with "
                      "test data size=%s", self.tcinputs['TestDataSize'])
        self.source_informix_helper_obj.populate_data(scale=self.tcinputs['TestDataSize'])

    def create_destination_ifx_helper_obj(self):
        """Creates object of informix helper class for destination instance
        Returns:
            ifx_info_list (list) -- list of informix server details as:
            [source_server_number,
            destination_server_number,
            dest_onconfig_path,
            dest_oncfg_path,
            dest_ixbar_path,
            source_onconfig_path]  """
        self.destination_informix_helper_obj = InformixHelper(
            self.commcell,
            self.destination_instance,
            'default',
            self.destination_client.client_hostname,
            self.tcinputs["DestinationInstanceName"],
            self.destination_instance.informix_user,
            self.tcinputs['DestinationInformixDBPassword'],
            self.tcinputs['DestinationInformixServiceName']
        )
        self.base_directory = self.destination_informix_helper_obj.base_directory
        self.log.info("Creating a dbspace in Destination client")
        self.destination_informix_helper_obj.create_dbspace()
        self.log.info("getting required information for cross machine restore")
        ifx_info_list = self.destination_informix_helper_obj.cross_machine_operations(
            self.destination_informix_helper_obj)
        self.log.info("Informix information list:%s", ifx_info_list)
        return ifx_info_list

    def run_backup(self):
        """Adds more rows to tab1, collect metadata, submit full backup,
        wait for completion and returns the metadata and backup jobid
        Returns:
            metadata_backup (str)--  metadata collected during backup
            job_id (str) -- backup job id
        """
        self.source_informix_helper_obj.insert_rows(
            "tab1",
            database="auto1",
            scale=2)
        self.log.info("Collect metadata from server")
        metadata_backup = self.source_informix_helper_obj.collect_meta_data()
        self.log.info("Setting the backup mode of subclient to Entire Instance")
        self.subclient.backup_mode = "Entire_Instance"
        self.dbhelper_object.run_backup(self.subclient, "FULL")
        return metadata_backup

    def restore_and_validate(self, metadata_backup):
        """ Submit restore and validate data restored
        Args:
            metadata_backup (str)--  metadata collected during backup
        Raises:
            Exception: If validation fail for restored data
        """
        ifx_info_list = self.create_destination_ifx_helper_obj()
        self.log.info("Starting config file restore")
        self.source_informix_helper_obj.cross_config_only_restore(
            self.destination_informix_helper_obj,
            ifx_info_list[2])
        self.log.info("Starting entire instance physical restore Job")
        self.destination_informix_helper_obj.cl_physical_restore(
            self.destination_client.client_name,
            self.destination_client.instance,
            base_directory=self.base_directory)
        self.log.info("Starting entire instance logical restore Job")
        self.destination_informix_helper_obj.cl_log_only_restore(
            self.destination_client.client_name,
            self.destination_client.instance,
            base_directory=self.base_directory)
        self.log.info("Making server online and validating data")
        self.destination_informix_helper_obj.bring_server_online()
        self.log.info("Informix server is now online")
        self.log.info("Deleting copied ixbar file from destination")
        destination_machine_object = machine.Machine(self.destination_client)
        destination_machine_object.delete_file(ifx_info_list[4])
        self.log.info("Metadata collected during backup=%s", metadata_backup)
        self.destination_informix_helper_obj.reconnect()
        metadata_restore = self.destination_informix_helper_obj.collect_meta_data()
        self.log.info("Metadata collected after restore=%s", metadata_restore)
        if metadata_backup == metadata_restore:
            self.log.info("Restored data is validated")
        else:
            raise Exception("Data validation failed")

    def get_client_list(self):
        """ Method to get the list of client IDs for which
        access control table entries are deleted
        Returns:
            client_list(list) -- list of IDs of clients """
        client_list = [int(self.client.client_id), int(self.destination_client.client_id)]
        ma_names = self.dbhelper_object.get_ma_names(self.subclient.storage_policy)
        for ma in ma_names:
            client_list.append(int(self.commcell.clients.get(ma).client_id))
        self.log.info("ClientIDs for which entries are deleted:{0}".format(client_list))
        return client_list

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)
            self.create_source_ifx_helper_obj()
            self.destination_client = self.commcell.clients.get(self.tcinputs["DestinationClientName"])
            destination_agent = self.destination_client.agents.get('informix')
            self.destination_instance = destination_agent.instances.get(
                self.tcinputs["DestinationInstanceName"])
            self.dbhelper_object = dbhelper.DbHelper(self.commcell)
            metadata_backup = self.run_backup()
            client_list = self.get_client_list()
            self.dbhelper_object.delete_client_access_control(
                client1=self.client, client_list=client_list)
            self.restore_and_validate(metadata_backup)
            self.log.info("Regular cross machine restore completed")
            self.create_sweep_schedule()
            sleep(20)
            if not self.source_informix_helper_obj.is_log_backup_to_disk_enabled():
                raise Exception("Log backup to disk feature is not enabled")
            metadata_backup = self.run_backup()
            self.dbhelper_object.delete_client_access_control(
                client1=self.client, client_list=client_list)
            self.restore_and_validate(metadata_backup)
            self.log.info("Cross machine restore with logs in cache completed")
            self.source_informix_helper_obj.run_sweep_job_using_regkey()
            self.dbhelper_object.delete_client_access_control(
                client1=self.client, client_list=client_list)
            self.restore_and_validate(metadata_backup)
            self.log.info("Cross machine restore with swept logs completed")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
