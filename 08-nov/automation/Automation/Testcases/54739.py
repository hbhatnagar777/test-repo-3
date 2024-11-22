# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the workflow "Disaster recovery backup" runs a DR backup job and the
backup job completes successfully without errors and with valid data.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    open_admin_console()        --  Starts the browser and opens admin console

    navigate_to_sql_instance()  --  Navigates to the SQL instance page

    start_migration()           --  Opening migration form and filling inputs

    initialize_azure_vm_object()--  Creates the azure VM object

    validate_vm()               --  Validates if the VM is created as expected. Things verified
    are vm size, vm username

    validate_db_restored()      --  Validates if all the DBs are restored in the VM

    tear_down()                --  Runs a backup job and adds the job to Indexing validation

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import commonutils
from AutomationUtils import constants

from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Databases.db_instances import DBInstances, SQLInstance

from VirtualServer.VSAUtils import VirtualServerHelper
from VirtualServer.VSAUtils.VMHelper import AzureVM

from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """This automation verifies that "Migrate to cloud" feature works for "SQL to Azure" from
    admin console"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Migrate DB to cloud - SQL DB to Azure cloud'

        self.tcinputs = {
            'dbs_migrate': [],
            'sql_instance': None,
            'recovery_target': None,
            'vm_template': None,
            'vm_size': None,
            'proxy_client': None
        }

        self.admin_console = None
        self.hypervisor = None
        self.vm_name = None
        self.azure_client = None
        self.dbs_migrate = None
        self.instance = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:

            self.vm_name = 'dbmig' + commonutils.get_random_string(length=4, lowercase=False)
            self.log.info('Azure VM which will be created for the run [{0}]'.format(self.vm_name))

            self.dbs_migrate = self.tcinputs.get('dbs_migrate', [])
            self.log.info('DBs to be migrated are {0}'.format(self.dbs_migrate))

            if self.dbs_migrate is []:
                raise Exception('No databases are configured for migration')

        except Exception as exp:
            self.log.exception(exp)
            raise Exception(exp)

    @test_step
    def open_admin_console(self):
        """Starts the browser and opens admin console"""

        browser_factory = BrowserFactory()
        browser = browser_factory.create_browser_object()
        browser.open()

        self.admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword']
        )

    @test_step
    def navigate_to_sql_instance(self):
        """Navigating to SQL instances list page"""

        self.admin_console.navigator.navigate_to_db_instances()
        instances = DBInstances(self.admin_console)
        db_type = DBInstances.Types.MSSQL
        instances.select_instance(db_type, self.tcinputs.get('sql_instance'))

    @test_step
    def start_migration(self):
        """Opening migration form and filling inputs"""

        sql_instance = SQLInstance(self.admin_console)
        vm_password = self.tcinputs.get('vm_password', '######')

        form = sql_instance.configure_migrate_to_cloud(SQLInstance.MigrationVendor.AZURE)
        form.set_vm_name(self.vm_name)
        form.set_username(self.vm_name)
        form.set_password(vm_password)
        form.set_confirm_password(vm_password)
        form.set_recovery_target(self.tcinputs.get('recovery_target'))
        form.set_template(self.tcinputs.get('vm_template'))
        form.set_size(self.tcinputs.get('vm_size'))
        form.set_proxy(self.tcinputs.get('proxy_client'))
        form.submit()

        job_id = self.admin_console.get_jobid_from_popup()

        job_obj = JobManager(job_id, self.commcell)
        job_obj.wait_for_state(expected_state=['completed'], retry_interval=30, time_limit=120)

        self.log.info('***** SQL DB to Azure migration job completed successfully *****')

    def initialize_azure_vm_object(self):
        """Creating azure VM object"""

        self.log.info('***** Refreshing clients object *****')
        self.commcell.clients.refresh()

        self.log.info('Creating hypervisor object for [{0}]'.format(self.client.client_name))

        auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(
            auto_client, self.agent, self.instance
        )

        self.hypervisor = auto_instance.hvobj

        self.log.info('Creating Azure VM object')
        self.azure_client = AzureVM(self.hypervisor, self.vm_name)

    @test_step
    def validate_vm(self):
        """Validates if the VM is created as expected. Things verified are vm size, vm username"""

        self.log.info('********** Validation 1: VM information **********')

        try:
            input_vm_size = self.tcinputs.get('vm_size').lower()
            result_vm_size = self.azure_client.vm_size.lower()

            if result_vm_size not in input_vm_size:
                raise Exception('VM size is incorrect. Got value [{0}]'.format(result_vm_size))

            result_vm_username = (
                self.azure_client.vm_info['properties']['osProfile']['adminUsername'])

            if result_vm_username != self.vm_name:
                raise Exception('VM username is incorrect. Got value [{0}]'.format(
                    result_vm_username))

            self.log.info('VM validation passed')

        except Exception as e:
            self.log.error('VM validation failed [{0}]'.format(e))
            raise Exception(e)

    @test_step
    def validate_db_restored(self):
        """Validates if all the DBs are restored in the VM"""

        self.log.info('********** Validation 2: DB restored **********')

        try:

            migrated_dbs = self.azure_client.machine.execute_command(
                """[reflection.assembly]::LoadWithPartialName("Microsoft.SqlServer.Smo") > $nul;
                $srv = New-Object "Microsoft.SqlServer.Management.SMO.Server"; 
                $srv.Databases | select Name""")

            migrated_dbs = migrated_dbs.output

            self.log.info('Migrated DBs [{0}]'.format(migrated_dbs))

            for db in self.dbs_migrate:
                if db not in migrated_dbs:
                    raise Exception('Database [{0}] is not migrated'.format(db))

            self.log.info('DB validation passed')

        except Exception as e:
            self.log.error('Database validation VM failed [{0}]'.format(e))
            raise Exception(e)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.open_admin_console()

            self.navigate_to_sql_instance()

            self.start_migration()

            self.initialize_azure_vm_object()

            self.validate_vm()

            self.validate_db_restored()

            self.log.info('********** Migration completed successfully **********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of test case"""

        Browser.close_silently(self.admin_console.browser)

        if self.status == constants.FAILED:
            self.log.info('Leaving the client and VM as it is for checking as testcase failed')
            return

        try:

            if self.commcell.clients.has_client(self.vm_name):
                self.log.info('Deleting the new client created')
                self.commcell.clients.delete(self.vm_name)

            if isinstance(self.azure_client, AzureVM):
                self.log.info('Deleting the new VM created')
                self.azure_client.clean_up()

        except Exception as e:
            self.log.error('Failed to cleanup azure VM [{0}]'.format(e))
