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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.constants import FAILED
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from dynamicindex.Datacube.data_source_helper import DataSourceHelper
from dynamicindex.Datacube.crawl_job_helper import CrawlJobHelper
from cvpysdk.datacube.constants import IndexServerConstants


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
        self.name = "Validation the role update operation on standalone index server"
        self.tcinputs = {
            "IndexServerNodeName": None,
            "AccessNodeClientName": None,
            "UserName": None,
            "Password": None,
            "IncludedirectoriesPath": None
        }
        self.index_server_name = None
        self.index_directory = None
        self.da_role_version = None
        self.da_role_id = None
        self.roles_reg_key_path = "HKLM:\\SOFTWARE\\CommVault Systems\\Galaxy\\%s\\Analytics"
        self.roles_reg_value = "analyticsInstalledRoles"
        self.data_source_helper = None
        self.crawl_job_helper = None
        self.data_source_name = None

    def setup(self):
        self.index_server_name = "IndexServer_%s" % self.id
        self.data_source_helper = DataSourceHelper(self.commcell)
        self.crawl_job_helper = CrawlJobHelper(self)
        option_selector = OptionsSelector(self.commcell)
        self.data_source_name = option_selector.get_custom_str("data_source")
        self.roles_reg_key_path = self.roles_reg_key_path % (self.commcell.clients.get(
            self.tcinputs['IndexServerNodeName']).instance)
        index_node_machine_obj = Machine(self.tcinputs['IndexServerNodeName'], self.commcell)
        self.index_directory = "%sindex_directory_%s" % (option_selector.get_drive(
            index_node_machine_obj), self.id)
        for role_data in self.commcell.index_servers.roles_data:
            if role_data['roleName'] == IndexServerConstants.ROLE_DATA_ANALYTICS:
                self.da_role_version = role_data['roleVersion']
                self.da_role_id = str(role_data['roleId'])
        if self.commcell.index_servers.has(self.index_server_name):
            self.log.info("Deleting and recreating the index server")
            self.commcell.index_servers.delete(self.index_server_name)
        index_node_machine_obj.remove_directory(self.index_directory, 0)
        self.log.info("Creating an Index server")
        self.commcell.index_servers.create(self.index_server_name, [self.tcinputs['IndexServerNodeName']],
                                           self.index_directory, [IndexServerConstants.ROLE_EXCHANGE_INDEX])
        self.log.info("Index server created with Exchange Index role")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Modifying index server by adding a new role")
            index_server_obj = self.commcell.index_servers.get(self.index_server_name)
            index_server_obj.update_role([{
                "roleName": IndexServerConstants.ROLE_DATA_ANALYTICS,
                "operationType": 1
            }])
            self.log.info("Checking registry on index server node for installed roles")
            index_node_machine_obj = Machine(self.tcinputs['IndexServerNodeName'], self.commcell)
            installed_roles_id = index_node_machine_obj.get_registry_value(
                win_key=self.roles_reg_key_path,
                value=self.roles_reg_value)
            if self.da_role_id not in installed_roles_id.split(","):
                raise Exception("Data analytics not installed on the index server node")
            self.log.info("Index node registry is successfully updated with installed roles")
            if self.da_role_version not in index_server_obj.roles:
                raise Exception("Failed to add a role to index server")
            self.log.info("Data analytics role added to the index server")
            self.log.info("Testing for Data analytics role")
            data_source_properties = {
                "includedirectoriespath": self.tcinputs['IncludedirectoriesPath'],
                "username": self.tcinputs['UserName'],
                "password": self.tcinputs['Password'],
                "accessnodeclientid": self.commcell.clients.get(
                    self.tcinputs['AccessNodeClientName']).client_id
            }
            data_source_properties = self.data_source_helper.\
                form_file_data_source_properties(data_source_properties)
            self.data_source_helper.create_file_data_source(
                self.data_source_name, self.index_server_name,
                data_source_properties
            )
            self.crawl_job_helper.monitor_crawl_job(self.data_source_name)
            self.crawl_job_helper.validate_crawl_files_count(
                self.data_source_name, self.tcinputs['IncludedirectoriesPath'],
                self.tcinputs['AccessNodeClientName'], self.index_server_name
            )
            self.log.info("Modifying index server by removing a role")
            index_server_obj.update_role([{
                "roleName": IndexServerConstants.ROLE_DATA_ANALYTICS,
                "operationType": 2
            }])
            if self.da_role_version in index_server_obj.roles:
                raise Exception("Failed to delete a role from index server")
            self.log.info("Data analytics role removed from the index server")

        except Exception as err:
            self.log.error('Test case failed.')
            self.log.exception(err)
            self.status = FAILED
            raise Exception("Test case failed.")

    def tear_down(self):
        if self.status != FAILED:
            self.log.info("Deleting index server")
            self.commcell.index_servers.delete(self.index_server_name)
            self.log.info("Index server deleted")
            Machine(self.tcinputs['IndexServerNodeName'], self.commcell).remove_directory(
                self.index_directory, 0
            )
