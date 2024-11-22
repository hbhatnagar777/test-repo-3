# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup function of this test case

    run()                                       --  run function of this test case

    tear_down()                                 --  tear down function of this test case

    index_server_setup()                        --  delete and recreate the index server with required roles

    create_data_source_import_data()            --  Creates the open data source and imports some random data

    run_backup()                                --  run solr backup

    index_server_restore                        --  do out of -place restore of index server to destination client
                                                                                        for data analytics role

    validate_data_with_src()                    --  validate size between browse core data and source index server core
                                                                                                data matches or not

    validate_backup()                           --  validates whether solr backup happened on correct cores

    validate_restored_data()                    --  validate size between browse core data and restored core
                                                                                                data matches or not

"""

import calendar
import time

from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.index_server_helper import IndexServerHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Validate out-of-place restore of data analytics role from solr backup"
        self.tcinputs = {
            "IndexServerName": None,
            "StoragePolicyCopy": None,
            "StoragePolicy": None,
            "RestoreClient": None,
            "IndexServerClientName": None
        }
        self.index_server_obj = None
        self.timestamp = None
        self.data_source_name = "SolrBackup_"
        self.data_source_obj = None
        self.data_source_column = ['Id', 'Date', 'Name']
        self.data_source_column_type = ['int', 'date', 'string']
        self.index_server_roles = [index_constants.ROLE_DATA_ANALYTICS, index_constants.ROLE_EXCHANGE_INDEX]
        self.total_crawlcount = 0
        self.ds_helper = None
        self.backup_job_id = None
        self.dest_client = None
        self.dest_client_obj = None
        self.dest_path = None
        self.index_server_helper = None
        self.option_selector_obj = None
        self.controller_machine_obj = None

    def index_server_setup(self):
        """delete and recreate the index server with required roles"""
        if self.commcell.index_servers.has(self.tcinputs['IndexServerName']):
            self.log.info("Deleting the index server : %s", self.tcinputs['IndexServerName'])
            self.commcell.index_servers.delete(self.tcinputs['IndexServerName'])

        index_dir = f"{self.option_selector_obj.get_drive(machine=self.controller_machine_obj)}" \
                    f"AnalyticsIndex{self.timestamp}"
        self.log.info("Going to create index server with index dir as : %s", index_dir)
        self.commcell.index_servers.create(index_server_name=self.tcinputs['IndexServerName'],
                                           index_server_node_names=[self.tcinputs['IndexServerClientName']],
                                           index_directory=index_dir,
                                           index_server_roles=self.index_server_roles)
        self.log.info("Created index server : %s", self.tcinputs['IndexServerName'])

    def create_data_source_import_data(self):
        """Creates the open data source and imports some random data"""
        self.log.info("Going to create open data source : %s", self.data_source_name)
        self.data_source_obj = self.ds_helper.create_open_data_source(
            data_source_name=self.data_source_name,
            index_server_name=self.tcinputs['IndexServerName'])
        self.log.info("Going to do update schema on data source")
        self.ds_helper.update_data_source_schema(data_source_name=self.data_source_name,
                                                 field_name=self.data_source_column,
                                                 field_type=self.data_source_column_type,
                                                 schema_field=dynamic_constants.SCHEMA_FIELDS)
        self.log.info("Calling Import data")
        self.total_crawlcount = self.ds_helper.import_random_data(data_source_name=self.data_source_name,
                                                                  field_name=self.data_source_column,
                                                                  field_type=self.data_source_column_type, rows=5)
        self.log.info("Calling hard commit for this data source on index server")
        self.index_server_obj.hard_commit(core_name=self.data_source_obj.computed_core_name)

    def run_backup(self):
        """run solr backup"""
        self.log.info("Make sure default subclient has all roles in backup content")
        self.index_server_helper.subclient_obj.configure_backup(storage_policy=self.tcinputs['StoragePolicy'],
                                                                role_content=[index_constants.ROLE_DATA_ANALYTICS])
        self.backup_job_id = self.index_server_helper.run_full_backup()

    def index_server_restore(self):
        """do out of -place restore of index server to destination client for data analytics role"""
        role_to_restore = [index_constants.ROLE_DATA_ANALYTICS]
        self.log.info("Going to do out of-place restore of index server for role : %s", role_to_restore)
        job_obj = self.index_server_helper.subclient_obj.do_restore_out_of_place(dest_client=self.dest_client,
                                                                                 dest_path=self.dest_path,
                                                                                 roles=role_to_restore)
        msg = f"Destination client: {self.dest_client} Detination path : {self.dest_path}"
        self.log.info(msg)
        self.index_server_helper.monitor_restore_job(job_obj=job_obj)

    def validate_data_with_src(self):
        """validate size between browse core data and source index server core data matches or not"""

        self.log.info("Going to cross verify data size vs browse size for DA role")
        is_success = self.index_server_helper.validate_backup_size_with_src(
            role_name=index_constants.ROLE_DATA_ANALYTICS, job_id=int(self.backup_job_id))
        if not is_success:
            raise Exception("Source Core size and browse core size mismatched for DA role. Please check logs")

    def validate_backup(self):
        """validates whether solr backup happened on correct cores"""
        folder_list, data_from_index_server = self.index_server_helper.subclient_obj.get_file_details_from_backup(
            include_files=False,
            job_id=int(self.backup_job_id))
        self.log.info("Browse response from index server : %s", data_from_index_server)
        for folder in folder_list:
            self.log.info("Validating folder : %s", folder)
            if not (folder.startswith(f"\\{index_constants.ROLE_DATA_ANALYTICS}") or
                    folder.startswith(f"\\{index_constants.ROLE_SYSTEM_DEFAULT}")):
                msg = "Unknown folder found in solr backup without role name. Folder : %s", folder
                raise Exception(msg)
        self.log.info("Backup validation for index server cores finished")

    def validate_restored_data(self):
        """validate size between browse core data and restored core data matches or not"""
        self.log.info("Going to validate restored data on client : %s", self.dest_client)
        is_success = self.index_server_helper.validate_restore_data_with_browse(
            role_name=index_constants.ROLE_DATA_ANALYTICS,
            client_name=self.dest_client,
            restore_path=self.dest_path,
            backup_job_id=int(
                self.backup_job_id))

        if not is_success:
            raise Exception("Restored Data Core size and browse core size mismatched. Please check logs")

    def setup(self):
        """Setup function of this test case"""
        self.timestamp = calendar.timegm(time.gmtime())
        self.option_selector_obj = OptionsSelector(self.commcell)
        self.controller_machine_obj = Machine(commcell_object=self.commcell)
        self.data_source_name = f"{self.data_source_name}{self.timestamp}"
        self.dest_client = self.tcinputs['RestoreClient']
        self.dest_client_obj = Machine(commcell_object=self.commcell,
                                       machine_name=self.dest_client)
        self.dest_path = f"{self.option_selector_obj.get_drive(machine=self.dest_client_obj)}" \
                         f"RestoreTest_IndexServer_{self.timestamp}"
        self.ds_helper = DataSourceHelper(self.commcell)
        self.index_server_setup()
        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServerName'])
        self.log.info("Index server helper initialized")
        self.index_server_helper.init_subclient()
        self.index_server_obj = self.index_server_helper.index_server_obj
        self.create_data_source_import_data()

    def run(self):
        """Run function of this test case"""
        try:
            self.run_backup()
            self.validate_backup()
            self.validate_data_with_src()
            self.index_server_restore()
            self.validate_restored_data()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("Going to delete open data source : %s", self.data_source_name)
            self.commcell.datacube.datasources.delete(self.data_source_name)
            self.log.info("Deleted the open data source :  %s", self.data_source_name)
            self.log.info("Going to delete the full backup job : %s", self.backup_job_id)
            storage_copy_obj = self.commcell.storage_policies.get(self.tcinputs['StoragePolicy']) \
                .get_copy(self.tcinputs['StoragePolicyCopy'])
            storage_copy_obj.delete_job(self.backup_job_id)
            self.log.info("Deleted the Full backup job")
            self.log.info("Going to delete the restored data on client : %s", self.dest_client)
            self.dest_client_obj.remove_directory(self.dest_path)
            self.log.info("Deleted the restored dir : %s", self.dest_path)
            self.log.info("Deleting index server: %s" % self.tcinputs['IndexServerName'])
            self.commcell.index_servers.delete(self.tcinputs['IndexServerName'])
            self.log.info("Index server deleted")
