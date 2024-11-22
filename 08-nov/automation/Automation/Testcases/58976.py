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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Server.organizationhelper import OrganizationHelper
from cvpysdk.subclient import Subclients
import random
from threading import Thread
from AutomationUtils import config
from queue import Queue
class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        This testcase verifies:
            1. Deactivating company with disabling backup/restore/login and verifying.
            2. Deactivitng all the properties and verifying.
            3. Delete Company without deactivating company [Negative Case]
            4. Delete company after deactivation
        """
        super(TestCase, self).__init__()
        self.name = "Companies - deactivate_company and Delete company"
                
        self.tcinputs = {}

        self.msp_plan = None
        self.client = None
        self.subclient = None
        """
        Either pass Client Details via Input Json or Config.json [config_json.Install.windows_client]
        tcinputs = {
            'machine_host' : '',
            'machine_username' : '',
            'machine_password' : '' # base 64 encoded password
        }
        """

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.common_password = self.inputJSONnode['commcell']['commcellPassword']
        self.msp_orghelper = OrganizationHelper(commcell= self.commcell)

        if self.tcinputs.get('file_server'):
             self.using_existing_client = True
             self.client_name = self.tcinputs['file_server']
             self.client = self.commcell.clients.get(self.client_name)
             self.log.info(f'Using provided existing client on CS => {self.client_name}')
        else:
            self.using_existing_client = False
            self.client_name = self.tcinputs['machine_host']
            self.machine_username = self.tcinputs['machine_username']
            self.machine_password = self.tcinputs['machine_password']
            self.msp_orghelper.uninstall_client(self.client_name)
            self.log.info(f'Installing new client on CS => {self.client_name}')
        
        # create new plan with available resource
        self.msp_spool, self.msp_plan = self.msp_orghelper.create_plan_with_available_resource()
        self.log.info(f'Created Plan : {self.msp_plan.plan_name}')

        # update content to Desktop to reduce backup size
        content = {
            "windowsIncludedPaths": ['Desktop'],
            "unixIncludedPaths": ['Desktop'],
            "macIncludedPaths": ['Desktop'],
            "backupSystemState": False
        }
        self.msp_plan.update_backup_content(content)

        self.infos = OrganizationHelper(self.commcell).setup_company(ta_password= self.common_password, plans= [self.msp_plan.plan_name])
        self.log.info(f"Company Name : {self.infos['company_name']}")
        
        self.msp_orghelper_obj = OrganizationHelper(self.commcell, self.infos['company_name'])
        self.ta_login_obj = self.infos['ta_loginobj']
        self.ta_orghelper_obj = OrganizationHelper(commcell= self.infos['ta_loginobj'], company= self.infos['company_name'])
                
        self.ta_login_obj.refresh()
        
        # move the client to the company
        if self.using_existing_client:
            Subclients(self.client.agents.get('File System').backupsets.get('defaultBackupSet')).get('default').plan = None
            self.client.change_company_for_client(self.infos['company_name'])
        else:
            for _ in range(2):
                if self.ta_orghelper_obj.install_client(self.client_name, self.machine_username, self.machine_password):
                    self.log.info('Client Installation Finished!')
                    self.client = self.commcell.clients.get(self.client_name)
                    break
            else:
                raise Exception('Client Install Failed even with two tries!')

        self.commcell.refresh()
        self.subclient = Subclients(self.client.agents.get('File System').backupsets.get('defaultBackupSet')).get('default')

    def run(self):
        """Run function of this test case"""
        try:
            self.ta_login_obj.refresh()
            subclient_obj = Subclients(self.ta_login_obj.clients.get(self.client_name).agents.get('File System').backupsets.get('defaultBackupSet')).get('default')
            plan_obj = self.ta_login_obj.plans.get(self.msp_plan.plan_name)

            # have one backup job to try restore
            self.log.info('Running backup as tenant admin without disabling any activity...')
            subclient_obj.plan = self.msp_plan.plan_name
            subclient_obj.backup().wait_for_completion(timeout=5)

            self.log.info("Disable only backup..")
            self.msp_orghelper_obj.deactivate_company(disable_backup= True ,disable_restore= False, disable_login= False)
            self.ta_orghelper_obj.verify_disabled_backup(subclient_obj, plan_obj)

            self.log.info("Disable only restore..")
            self.msp_orghelper_obj.deactivate_company(disable_backup= False ,disable_restore= True, disable_login= False)
            self.ta_orghelper_obj.verify_disabled_restore(subclient_obj)

            self.log.info("Disable only login..")
            self.msp_orghelper_obj.deactivate_company(disable_backup= False ,disable_restore= False, disable_login= True)
            self.ta_orghelper_obj.verify_disabled_login(self.infos['ta_name'], self.common_password)
            
            self.log.info("Disable all options..")
            self.msp_orghelper_obj.activate_company()
            self.msp_orghelper_obj.deactivate_company()
            # As even login is disabled, So Now trying as MSP. Above as Tenant Admin it is already Verified.
            self.msp_orghelper_obj.verify_disabled_backup(self.subclient, self.msp_plan)
            self.msp_orghelper_obj.verify_disabled_restore(self.subclient)
            self.msp_orghelper_obj.verify_disabled_login(self.infos['ta_name'], self.common_password)

            if self.using_existing_client:
                self.client.change_company_for_client('Commcell')

            self.log.info('Delete without Deactivating company..')
            self.msp_orghelper_obj.activate_company()
            try:
                self.commcell.organizations.delete(self.infos['company_name'], False)
            except Exception as err:
                self.log.info(f'[Negative Case] : {err}')
            else:
                raise Exception('Company got deleted without prior deactivation!!!')

            self.log.info('Delete after Deactivating company..')
            self.msp_orghelper_obj.deactivate_company()
            self.msp_orghelper_obj.delete_company(wait= True, timeout= 10)

            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.using_existing_client:
            self.client.change_company_for_client('Commcell')
        
        if self.subclient: self.subclient.plan = None
        if self.infos and self.commcell.organizations.has_organization(self.infos['company_name']):
            self.msp_orghelper_obj.delete_company(wait= True) # timeout = 15 min 
        
        if self.commcell.plans.has_plan(self.msp_plan.plan_name):
            self.commcell.plans.delete(self.msp_plan.plan_name)
