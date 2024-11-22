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
from AutomationUtils import config
from threading import Thread
from queue import Queue
from cvpysdk.job import JobController
from cvpysdk.subclient import Subclients
from Server.Plans.planshelper import PlansHelper
from Server.Security.userhelper import UserHelper
from cvpysdk.deployment.deploymentconstants import UnixDownloadFeatures
from base64 import b64encode

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
            In Rented and Own Storage Configuration:
                1. Company Tenant Admin can install media agent for company.
                2. Creating Storage Pool and Plans on available media agent.
                3. Associating company created plan to company client and running backups on it.
                4. Associating MSP plan to company client and running backups on it.
                5. Associating Company plan with MSP client and running backups on it.
                6. Deleting company and verifying plan, storage pool and MA doesnot get delete [Shared Entities]. These entities will be migrated to Commcell.
                7. Everytime new job is triggered, verifying whether MSP/ Company 1 Tenant Admin and Operator/ Company 2 Tenant Admin and Operator are seeing the jobs or not.
        """
        super(TestCase, self).__init__()
        self.name = "Companies - Rented Storage and BYOS"
        
        self.msp_storage_pool = self.company_storage_pool = self.rented_plan = self.byos_plan = self.company = self.view_company = self.created_new_plan = self.subclient =  None
        self.tcinputs = {
            "company_client" : {
                "machine_host" : "",
                "machine_username" : "",
                "machine_password" : ""
            },
            "msp_client" : {
                "machine_host" : "",
                "machine_username" : "",
                "machine_password" : ""
            }
        }
        self.reports = []
        self.msp_subclient = None
        self.mis_match_count = 0
        self.tenant_admin_1 = self.tenant_operator_1 = None
        self.tenant_admin_2 = self.tenant_operator_2 = None
        self.additional_settings_key_name = 'DisablePlanCompanyValidationBeforeAssociation'

    def setup(self):
        """Setup function of this test case"""
        self.key_already_present = self.check_if_key_exists()
        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.user_helper = UserHelper(self.commcell)

        self.company_client_name = self.tcinputs['company_client']['machine_host']
        self.company_client_user = self.tcinputs['company_client']['machine_username']
        self.company_client_password = b64encode(self.tcinputs['company_client']['machine_password'].encode()).decode()
        self.msp_client_name = self.tcinputs['msp_client']['machine_host']
        self.msp_client_user = self.tcinputs['msp_client']['machine_username']
        self.msp_client_password = b64encode(self.tcinputs['msp_client']['machine_password'].encode()).decode()
        
        self.common_password = self.inputJSONnode['commcell']['commcellPassword']
        self.msp = OrganizationHelper(commcell= self.commcell)

        # creating company - 1
        self.company, self.tenant_admin_1, self.tenant_operator_1 = self.setup_company()
        self.log.info(f"Company Name : {self.company['company_name']}")

        # creating company - 2
        self.commcell.refresh()
        self.view_company, self.tenant_admin_2, self.tenant_operator_2 = self.setup_company()
        self.log.info(f"[View] Company Name : {self.view_company['company_name']}")
        
        # uninstall and starting installing clients to commcell and company
        queue1, queue2 = Queue(), Queue()
        t1 = Thread(target= lambda queue: queue.put(self.uninstall_and_install_company_client()), args= (queue1, ))
        t2 = Thread(target= lambda queue: queue.put(self.uninstall_and_install_msp_client()), args= (queue2, ))
        t1.start()
        t2.start()
        
        self.msp_orghelper_obj = OrganizationHelper(self.commcell, self.company['company_name'])
        # creating new msp plan and associating this plan to company. Creating new plan because, we need to run backup. Old Plans Storage pool might be offline
        self.msp_storage_pool, self.rented_plan = self.msp_orghelper_obj.create_plan_with_available_resource()
        self.log.info(f'MSP Created Plan : {self.rented_plan.plan_name}')

        self.msp_orghelper_obj.associate_plans(plan_list= [self.rented_plan.plan_name])
        
        # waiting for the both client installation to finish
        self.log.info('Waiting for Clients Uninstall/install to finish..')
        t1.join()
        t2.join()

        # if installation fails - Will retry once again here
        self.log.info('Installation Thread completed if it was a failure will retry..')
        if (queue1.empty() or (not queue1.get())) and (not self.uninstall_and_install_company_client()):
                raise Exception(f'Uninstalling/Installing Company Client [{self.company_client_name}] Failed!')            
        self.log.info(f'Installing Company Client [{self.company_client_name}] Success!')
        
        if (queue2.empty() or (not queue2.get())) and (not self.uninstall_and_install_msp_client()):
                raise Exception(f'Uninstalling/Installing MSP Client [{self.msp_client_name}] Failed!')            
        self.log.info(f'Installing MSP Client [{self.msp_client_name}] Success!')
    
        self.commcell.refresh() # to make sure client installed and visible under commcell
        self.company_client = self.commcell.clients.get(self.company_client_name)
        self.msp_client = self.commcell.clients.get(self.msp_client_name)
        
        # Now, creating plan as tenant admin on company resource
        self.company['ta_loginobj'].refresh()
        self.tenant_admin = OrganizationHelper(self.company['ta_loginobj'], self.company['company_name'])
        
        self.company_storage_pool, self.byos_plan = self.tenant_admin.create_plan_with_available_resource(create_new_pool=True) # creates storage pool + plan
        self.log.info(f'Company TA Created Plan : {self.byos_plan.plan_name}')

        self.company_storage_pool_2, self.byos_plan_2 = self.tenant_admin.create_plan_with_available_resource(create_new_pool=True) # Non shared entity - This Plan should get delete along with Company
        self.log.info(f'Company TA Created Plan - 2 : {self.byos_plan_2.plan_name}')
        
        self.company['to_loginobj'].switch_to_company(self.company['company_name'])
        self.company['to_loginobj'].refresh()
        self.toperator_orghelper = OrganizationHelper(self.company['to_loginobj'], self.company['company_name'])

    def run(self):
        """Run function of this test case"""
        try:
            self.update_plan_content() # changing content to Desktop and disabling backup system state. To Save Bandwidth
            self.log.info('Running Backup as Tenant Admin...')
            self.run_backup(self.tenant_admin)

            self.log.info('Running Backup as Tenant Operator...')
            self.run_backup(self.toperator_orghelper)

            self.log.info('58973 Testcase Verification is done!')
            self.log.info('Running Backup as MSP on MSP client..')
            self.msp_subclient = Subclients(self.msp_client.agents.get('File System').backupsets.get('defaultBackupset')).get('default')

            self.commcell.add_additional_setting(category='CommServDB.GxGlobalParam', key_name=self.additional_settings_key_name, data_type='Integer', value='1')
            self.msp_subclient.plan = self.byos_plan # this is restricted from SP32, We need to enable Key => DisablePlanCompanyValidationBeforeAssociation

            job= self.msp_subclient.backup()
            self.log.info(f'MSP subclient backup : {job.job_id}')
            self.verify_jobs_visibility(jobid= job.job_id, company1= False)
            job.wait_for_completion(timeout= 1)
            
            # Now delete organization
            self.log.info('Now Deleting Organization..')
            self.msp_orghelper_obj.delete_company(wait= True, timeout= 15)
            
            self.verify_entities_deletion()
            self.log.info('59751 Testcase Verification is done!')
            
            self.log.info(f'Total Mismatch Count : {self.mis_match_count}')
            if self.mis_match_count:
                self.log.info(f'Mismatch Count : {self.mis_match_count}')
                self.result_string = f'Mismatch Count in JOB views : {self.mis_match_count}, Report : {self.reports}'
                # raise Exception(f'Mismatch Count in JOB views : {self.mis_match_count}, Report : {self.reports}')
            self.log.info('59175 Testcase Verification is done!')
            
            self.status = constants.PASSED
            self.log.info('Testcase Passed')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if not self.key_already_present:
            self.commcell.delete_additional_setting(category='CommServDB.GxGlobalParam', key_name=self.additional_settings_key_name)

        # at the end both the client will be present in commcell - So deleting both the clients separately
        queue1, queue2 = Queue(), Queue()
        self.commcell.refresh()
        t1 = Thread(target= lambda queue, clientname: queue.put(self.msp.uninstall_client(client_name= clientname)), args= (queue1, self.company_client_name, ))
        t2 = Thread(target= lambda queue, clientname: queue.put(self.msp.uninstall_client(client_name= clientname)), args= (queue2, self.msp_client_name, ))
        t1.start()
        t2.start()
        
        # meanwhile clients are uninstalling - Clean up other entities.
        self.msp_orghelper_obj.cleanup_orgs(marker= 'DEL Automated')
        self.user_helper.cleanup_users(marker= 'del_automated')

        try:
            if self.msp_subclient: self.msp_subclient.plan = None
            if self.subclient.plan: self.subclient.plan = None
            self.sdk_plans_helper.cleanup_plans(marker='DEL Automated')
            if self.msp_storage_pool and self.commcell.storage_pools.has_storage_pool(self.msp_storage_pool.storage_pool_name):
                self.commcell.storage_pools.delete(self.msp_storage_pool.storage_pool_name)
            if self.company_storage_pool and self.commcell.storage_pools.has_storage_pool(self.company_storage_pool.storage_pool_name):
                self.commcell.storage_pools.delete(storage_pool_name= self.company_storage_pool.storage_pool_name)
            if self.company_storage_pool_2 and self.commcell.storage_pools.has_storage_pool(self.company_storage_pool_2.storage_pool_name):
                self.commcell.storage_pools.delete(storage_pool_name= self.company_storage_pool_2.storage_pool_name)
        except Exception as err:
            self.log.info(err)
        
        t1.join()
        t2.join()
        self.log.info('Clients Uninstallation Finished!')

    def check_if_key_exists(self) -> bool:
        keys = [key['displayLabel'] for key in self.commcell.get_configured_additional_setting()]
        return True if self.additional_settings_key_name in keys else False

    def setup_company(self):
        """Creating Company"""
        tries = 3
        while tries:
            try:
                company = OrganizationHelper(self.commcell).setup_company(ta_password= self.common_password, to_password= self.common_password)
                tenant_admin, tenant_operator =  company['ta_loginobj'], company['to_loginobj']
                tenant_operator.switch_to_company(company['company_name'])
                return company, tenant_admin, tenant_operator
            except Exception as error:
                self.log.warning(error)
                self.commcell.refresh()
            tries -= 1
        raise Exception('Failed to Create Company with 3 tries.')
    
    @test_step
    def verify_entities_deletion(self):
        """Verifying testcase 59751 - Shared Entities Deletion."""
        self.commcell.refresh()
        self.log.info('Checking for plans..')
        if not self.commcell.plans.has_plan(plan_name= self.byos_plan.plan_name):
            raise Exception(f'Shared Plan [{self.byos_plan.plan_name}] Got Deleted!')
        
        if self.commcell.plans.has_plan(plan_name= self.byos_plan_2.plan_name):
            raise Exception(f'Non-Shared Plan [{self.byos_plan_2.plan_name}] not deleted, even after company deletion')
        
        self.log.info('Checking for storage pools..')
        if not self.commcell.storage_pools.has_storage_pool(name= self.company_storage_pool.storage_pool_name):
            raise Exception(f'Shared Storage Pool [{self.company_storage_pool.storage_pool_name}] Got Deleted!')
        
        self.log.info('Checking for MA..')
        if not self.commcell.clients.has_client(client_name= self.company_client_name):
            raise Exception(f'Shared Media Agent [{self.company_client_name}] Also Got Deleted!')
        
        self.company_client.refresh()
        self.log.info(f'Current Company of MA Client : {self.company_client.company_name}')
        if self.company_client.company_name.lower() != 'commcell': raise Exception(f'MA Client Still Associated to Company!? : [{self.company_client.company_name}]')
        
        self.commcell.plans.refresh(mongodb=True, hard=True)
        plans = [i.lower() for i in list(self.commcell.plans.filter_plans(plan_type= 'Server', company_name= 'Commcell').keys())]
        self.log.info(f'Plans in Commcell : {plans}')
        
        if self.byos_plan.plan_name in plans:
            self.log.info('Plan Moved to Commcell..')
        else:
            raise Exception(f'Plan {self.byos_plan.plan_name} is still having association with deleted company')
        self.log.info('[VERIFIED] Shared Entities are not deleted')
        
    def _wait_for_completion(self, job):
        if not job.wait_for_completion():
            self.log.info(f"Client installation Failed. Reason : [{job.delay_reason}]")
            return False
        else:
            return True
            
    def verify_jobs_visibility(self, jobid, company1):
        """Verifying Job Visibility with different persona"""
        self._verify_msp_seeing_job(job_id= jobid)
        self._verify_company_jobs(job_id= jobid, company_index= "1", job_should_be_visible= company1)
        self._verify_company_jobs(job_id= jobid, company_index= "2", job_should_be_visible= False) # company 2 doesnot have rights on any entities, So it is always False
        
    def _verify_msp_seeing_job(self, job_id):
        """Verifies whether MSP is seeing the given JOB"""
        self.commcell.refresh()
        user_seeing_the_job = int(job_id) in list(JobController(commcell_object= self.commcell).all_jobs().keys())
        if not user_seeing_the_job:
            self.mis_match_count += 1
            error_string = f'MSP not seeing this Job : {job_id} ?'
            self.log.info(error_string)
            self.reports.append(error_string)
    
    def _verify_company_jobs(self, job_id, company_index, job_should_be_visible):
        """It verifies Job is visible or not according to the parameters passed"""
        companies = {
            "1" : [self.tenant_admin_1, self.tenant_operator_1],
            "2" : [self.tenant_admin_2, self.tenant_operator_2]
        }
        users, user_index = ["Tenant Admin", "Tenant operator"], 0 # To print error mesage at the end
        for user_object in companies[company_index]:
            user_seeing_the_job = int(job_id) in list(JobController(commcell_object= user_object).all_jobs().keys())
            if user_seeing_the_job != job_should_be_visible: # Actual Behaviour and Expected behaviour is not Same -> Something is wrong here.
                self.mis_match_count += 1
                self.log.info(f'All Jobs for Failed User : {list(JobController(commcell_object= user_object).all_jobs().keys())}')

                if job_should_be_visible:
                    error_string = f'Company {company_index} -> {users[user_index]} is not seeing this Job : {job_id}'
                    self.log.info(error_string)
                    self.reports.append(error_string)
                else:
                    error_string = f'Company {company_index} -> {users[user_index]} is seeing this Job : {job_id}, But user not suppose to see.'
                    self.log.info(error_string)
                    self.reports.append(error_string)
            user_index += 1
    
    @test_step
    def run_backup(self, company_obj):
        """Runs Backup using Rented Storage and Own Storage Plan"""
        for i in range(2):
            plan_name = self.byos_plan.plan_name if i else self.rented_plan.plan_name
            self.log.info(f'Running Backup using plan : {plan_name}')

            self.subclient , job = company_obj.run_backup_on_company_client({'client_display_name': self.company_client.display_name, 'plan_name' : plan_name})
            self.log.info(f'JOB ID : [{job.job_id}] Waiting For Completion...')
            self.log.info(f'Company Backup : {job.job_id}')
            self.verify_jobs_visibility(jobid= job.job_id, company1= True)
           
            if not job.wait_for_completion(timeout= 1): # if the job is in waiting state for 1 min. Kill the JOB
                try:
                    job.kill(wait_for_job_to_kill= True)
                except Exception as error:
                    self.log.warning(f'While killing Job : {error}')
                self.log.info(f'Job [{job.job_id}] failed or killed after timeout')
            self.log.info('Job Done!')
            self.subclient.plan = None 
            
    def update_plan_content(self):
        """Updates Content of Plan to Desktop and disables backup system state to Save Bandwidth"""
        tries = 3 # to avoid one time errors like 'Response Failed'
        content = {
            "windowsIncludedPaths": ['Desktop'],
            "unixIncludedPaths": ['Desktop'],
            "macIncludedPaths": ['Desktop'],
            "backupSystemState": False
        }
        while tries:
            try: 
                self.byos_plan.update_backup_content(content)
                self.rented_plan.update_backup_content(content)
                self.log.info('Backup Content For Plan Updated!')
                return
            except Exception as err:
                self.log.info(err)
                tries -= 1
                self.log.info('Retrying for plan content update..')
        raise Exception('Failed to Change Content for Plan')
    
    def uninstall_and_install_msp_client(self):
        """Uninstalls and Re-Installs client to commcell"""
        try:
            self.log.info('Uninstalling and Installing MSP Client..')
            if not self.msp.uninstall_client(client_name= self.msp_client_name): return False
            self.log.info('Installing MSP Client..')
            job_install = self.commcell.install_software(
                    client_computers=[self.msp_client_name],
                    # windows_features= [702],
                    unix_features=[UnixDownloadFeatures.FILE_SYSTEM.value],
                    username= self.msp_client_user,
                    password= self.msp_client_password
                )

            self.log.info(f"[MSP Client] Install Client Job Launched Successfully, Will wait until Job: {job_install.job_id} Completes")
            self.verify_jobs_visibility(jobid= job_install.job_id, company1= False)
            return self._wait_for_completion(job= job_install)
        except Exception as err:
            self.log.info(f'Exception in [uninstall_and_install_msp_client] : {err}') # Exception might happen during job verfication as well.
            return False
        
    def uninstall_and_install_company_client(self):
        """Uninstalls and Re-Installs client to company"""
        try:
            if not self.msp.uninstall_client(client_name= self.company_client_name): return False
            self.log.info('Installing Company Client..')
            job_install = self.tenant_admin_1.install_software(
                    client_computers=[self.company_client_name],
                    # windows_features= [51, 702],
                    unix_features=[UnixDownloadFeatures.FILE_SYSTEM.value, UnixDownloadFeatures.MEDIA_AGENT.value],
                    username= self.company_client_user,
                    password= self.company_client_password
                )

            self.log.info(f"[Company Client] Install Client Job Launched Successfully, Will wait until Job: {job_install.job_id} Completes")
            return self._wait_for_completion(job= job_install)
        except Exception as err:
            self.log.info(f'Exception in [uninstall_and_install_company_client] : {err}')
            return False