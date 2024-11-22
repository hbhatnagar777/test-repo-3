# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

Example JSON input for running this test case:
"5305": {
            "ClientName" : Client name,
            "InstanceName": Instnace Name,
            "database_name": DB Name,
            "db2_username": DB username,
            "db2_user_password": DB Password,
            "plan": Plan Name,
            "credential_name": DB2 creds name
        }

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  setup the parameters and common object necessary

    run()                                       --  run function of this test case

    prerequisite_setup_test_case()              --  setup prerequisite for the test case
    
    navigate_to_database()                      --  navigate to db page
    
    backup()                                    --  function to perform backup operation
    
    restore()                                   --  perform restore operation

    tear_down()                                 --  Tear down method to cleanup the entities

    cleanup()                                   --  Deletes the subclient
"""

from AutomationUtils.cvtestcase import CVTestCase
from Database.DB2Utils.db2helper import DB2
from Database.dbhelper import DbHelper
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import Db2InstanceDetails
from Web.AdminConsole.Databases.backupset import DB2Backupset
from Web.AdminConsole.Databases.subclient import DB2Subclient
from Web.Common.exceptions import CVTestCaseInitFailure, CVWebAutomationException
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.page_container import PageContainer


class TestCase(CVTestCase):
    """ Class for executing this test case """

    test_step = TestStep()

    def __init__(self):
        """Initial configs for test case"""
        super(TestCase, self).__init__()
        self.name = "Restore from multiple Offline DB Backup Images using multiple streams combinations"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.db_instance = None
        self.db_instance_details = None
        self.db_backupset = None
        self.db_subclient = None
        self.dbhelper = None
        self.page_container = None
        self.db2_helper = None
        self.dbtype = None
        self.tcinputs = {
            "InstanceName": None,
            "database_name": None,
            "plan": None,
            "db2_username": None,
            "db2_user_password": None,
            "credential_name": None,
        }
        self.jobs = dict()
        self.job = None
        self.job_num = 0
        self.tblcount = None
        self.tablespace_list = None

    def setup(self):
        """ Must needed setups for test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.db_instance = DBInstances(admin_console=self.admin_console)
            self.db_instance_details = Db2InstanceDetails(admin_console=self.admin_console)
            self.db_backupset = DB2Backupset(admin_console=self.admin_console)
            self.db_subclient = DB2Subclient(admin_console=self.admin_console)
            self.page_container = PageContainer(self.admin_console)
            self.dbtype = DBInstances.Types.DB2
            self.dbhelper = DbHelper(self.commcell)
            self.job = Jobs(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """ Main method to run test case. """

        try:
            self.prerequisite_setup_test_case()
            self.navigate_to_database()
            instance = self.client.agents.get('db2').instances.get(self.tcinputs['InstanceName'])
            backupset = instance.backupsets.get(self.tcinputs["database_name"])
            self.db2_helper = DB2(commcell=self.commcell,
                                  client=self.client,
                                  instance=instance,
                                  backupset=backupset)
            self.db_backupset.add_db2_subclient(subclient_name="test_subc", plan=self.tcinputs["plan"],
                                                data_backup=True, backup_logs=True, type_backup='offline')
            self.backup("full")
            self.backup("incremental")
            self.backup("differential")
            self.restore("full")
            self.restore("incremental")
            self.restore("differential")
        except Exception:
            raise CVWebAutomationException
        finally:
            self.cleanup()

    @test_step
    def prerequisite_setup_test_case(self):
        """ Prerequisite setup for test case """
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["InstanceName"],
                                         client_name=self.tcinputs["ClientName"])
                
        self.db_instance_details.get_instance_details()
        if "windows" in self.client.os_info.lower():
            self.tcinputs["db2_username"] = self.client.display_name + "\\" + self.tcinputs["db2_username"]

        self.db_instance_details.db2_edit_instance_properties(username=self.tcinputs["db2_username"],
                                                              password=self.tcinputs["db2_user_password"],
                                                              plan=self.tcinputs["plan"],
                                                              credential_name=self.tcinputs["credential_name"])
    
    @test_step
    def navigate_to_database(self):
        """ Function to navigate to database page. """
        self.navigator.navigate_to_db_instances()
        self.db_instance.select_instance(database_type=self.dbtype,
                                         instance_name=self.tcinputs["InstanceName"],
                                         client_name=self.tcinputs["ClientName"])
        self.db_instance_details.click_on_entity(entity_name=self.tcinputs["database_name"])
        self.page_container.select_entities_tab()

    @test_step
    def backup(self, backup_type):
        """
        Data population and Backup function
        Args:
            backup_type (str) : backup type to be taken
        """
        self.tblcount, self.tablespace_list = self.db2_helper.add_data_to_database(tablespace_name=f"Test_db2_{backup_type[0:3]}",
                                                                                   table_name=f"Test_db2_{backup_type[0:3]}", 
                                                                                   database_name=self.tcinputs["database_name"])
        self.navigate_to_database()
        self.jobs[f'backup_{backup_type}'] = self.db_backupset.db2_backup(subclient_name="test_subc",
                                                                           backup_type=backup_type)
        self.dbhelper.wait_for_job_completion(self.jobs[f'backup_{backup_type}'])
        self.db2_helper.drop_tablespace(f"Test_db2_{backup_type[0:3]}".upper())

    @test_step
    def restore(self, backup_type):
        """ 
        Restore and validation fucntion
        Args:
            backup_type (str) : backup type to be restored
        """
        job_id = self.jobs[f"backup_{backup_type}"]
        self.navigate_to_database()
        self.db_backupset.list_backup_history()
        self.job.job_restore(job_id)
        restore_job = self.db_backupset.restore_folders(database_type=self.dbtype, all_files=True)
        self.jobs['restore'] = restore_job.in_place_restore(endlogs=True)
        self.dbhelper.wait_for_job_completion(self.jobs['restore'])
        self.db2_helper.restore_validation(table_space=f"Test_db2_{backup_type[0:3]}", table_name=f"Test_db2_{backup_type[0:3]}")

    @test_step
    def cleanup(self):
        """ Cleanup method for test case. """
        self.navigate_to_database()
        self.db_instance_details.delete_entity("test_subc")

    def tear_down(self):
        """ Logout from all the objects and close the browser. """
        self.admin_console.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
