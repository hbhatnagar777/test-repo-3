# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup method for test case

    get_active_mysql_servers()  --  method to fetch the number of MySQL servers running on the client machine

    get_all_instances()         --  method to get the list of MySQL instance names for a client

    delete_instances()          --  method to delete all the instances present for a MySQL client

    validate_auto_discovered_instances() -- method to validate the auto discovered instances

    cleanup()                   --  method to cleanup all testcase created changes

    run()                       --  run function of this test case

    Input Example:

    "testCases":
            {
                "51295": {
                    "ClientName": "mysql",
                    "AgentName": "MySQL"
                }
            }
"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import MySQLInstanceDetails
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Components.dialog import RModalDialog
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ Class for executing testcase to Auto discovery of MySQL instances on Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Auto discovery of MySQL instances'
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.database_instances = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None
        }
        self.page_container = None
        self.dialog = None
        self.table = None
        self.machine = None
        self.instance_list = None
        self.auto_discover = False

    def setup(self):
        """ Method to setup test variables """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.database_instances = DBInstances(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.dialog = RModalDialog(self.admin_console)
        self.table = Rtable(self.admin_console)
        self.machine = Machine(self.client)

    @test_step
    def get_active_mysql_servers(self):
        """ method to fetch the number of MySQL servers running on the client machine
        Returns:
            NumberOfInstances (int) : number of MySQL servers running on the client
        """
        self.log.info("Get the number of MySQL servers running on client")
        if "UNIX" in self.machine.os_info:
            instances = self.machine.execute_command("ps -eo user,pid,command | grep -e mysqld -e mariadbd | "
                                                     "awk '{n=split($3,a,\" --\"); print $1,$2,a[1]}'")
            NumberOfInstances = len([line for line in instances.formatted_output if 'mysqld' in line[2]])
        else:
            instances = self.machine.execute_command('tasklist /svc | findstr "mysqld.exe mariadbd.exe"')
            NumberOfInstances = len([line for line in instances.formatted_output.splitlines() if 'N/A' not in line])
        return NumberOfInstances

    @test_step
    def get_all_instances(self):
        """ method to get the list of MySQL instance names for a client
        Returns:
            instance_list  (List) : List of instance name
        """
        self.navigator.navigate_to_db_instances()
        self.table.reload_data()
        self.table.search_for(keyword=self.client.client_name)
        instance_list = self.table.get_column_data(column_name='Name')
        return instance_list

    @test_step
    def delete_instances(self, instance_list):
        """ method to delete all the instances present for a MySQL client
        Args:
            instance_list (List) : List of instance name
        """
        self.navigator.navigate_to_db_instances()
        for instance in instance_list:
            self.admin_console.refresh_page()
            if self.database_instances.is_instance_exists(DBInstances.Types.MYSQL, instance,
                                                          self.tcinputs['ClientName']):
                self.database_instances.select_instance(
                    DBInstances.Types.MYSQL, instance, self.tcinputs['ClientName'])
                MySQLInstanceDetails(self.admin_console).delete_instance()
                self.log.info(f"### Instance {instance} is deleted ###")
            else:
                raise CVTestStepFailure(f"### Failed to delete the instance {instance}  ###")

    @test_step
    def auto_discover_instances(self):
        """ method to auto discover MySQL instances """
        self.admin_console.refresh_page()
        self.page_container.access_page_action_from_dropdown('Discover instances')
        self.dialog.select_dropdown_values(values=[self.tcinputs['AgentName']], drop_down_id='ddDbEngine')
        self.dialog.select_dropdown_values(values=[self.tcinputs['ClientName']], drop_down_id='serverDropdown')
        self.dialog.enable_toggle(toggle_element_id='toggleEADiscovery')
        self.dialog.click_button_on_dialog(id='btnDiscoverNow')
        self.admin_console.wait_for_completion()
        self.auto_discover = True

    @test_step
    def validate_auto_discovered_instances(self, NumberOfInstances, instance_list_after_autodiscovery):
        """
        method to validate the auto discovered instances
        Args:
            NumberOfInstances (int) : Number of instances to be auto discovered
            instance_list_after_autodiscovery (List) : List of instances after auto discovery
        """
        self.log.info("Check for MySQL instances if they were auto discovered")
        if NumberOfInstances == len(instance_list_after_autodiscovery):
            for instance in instance_list_after_autodiscovery:
                self.log.info(f"Instance {instance} is auto-discovered. Validation Successful ###")
        else:
            raise CVTestStepFailure(f"The Number of auto-discovered instances {len(instance_list_after_autodiscovery)}"
                                    f" does not match the expected number {NumberOfInstances}")

    @test_step
    def cleanup(self):
        """ Removes testcase created changes """
        if self.auto_discover:
            instances = self.get_all_instances()
            instances_to_delete = []
            for instance in instances:
                if instance not in self.instance_list:
                    instances_to_delete.append(instance)
            if instances_to_delete:
                self.log.info("Deleting auto discovered instances")
                self.delete_instances(instances_to_delete)

    def run(self):
        """ Main function for test case execution """
        try:
            NumberOfInstances = self.get_active_mysql_servers()
            self.instance_list = self.get_all_instances()
            self.delete_instances(self.instance_list)
            self.auto_discover_instances()
            instance_list_after_autodiscovery = self.get_all_instances()
            self.validate_auto_discovered_instances(NumberOfInstances,
                                                    instance_list_after_autodiscovery)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.cleanup()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)
